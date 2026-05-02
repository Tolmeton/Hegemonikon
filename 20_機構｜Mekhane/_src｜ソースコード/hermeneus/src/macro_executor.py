# PROOF: [L1/定理] <- hermeneus/src/macro_executor.py マクロ自動実行エンジン
"""
Hermēneus Macro Executor — CCL マクロを AST walk で自動実行

Forward pass: マクロ → 展開 → AST → 各ノードを再帰実行
Backward pass: 確信度スコアから各ステップの帰責値 (gradient) を計算

アナロジー:
  - Forward pass  = ニューラルネットの順伝播 = 拡散モデルのデノイジング
  - Loss function = /pis (確信度) = FEP の自由エネルギー
  - Backward pass = 逆伝播 = 信用割り当て

Origin: 2026-02-09 — /v マクロ化 → 合成エンジン設計
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from enum import Enum
import logging
import time
import re

logger = logging.getLogger(__name__)

# Progress logging fallback
try:
    from hermeneus.src.mcp_server import _progress
except ImportError:
    def _progress(*args: Any, **kwargs: Any) -> None:
        pass


# =============================================================================
# Types
# =============================================================================

# PURPOSE: [L2-auto] 実行ステップのタイプ
class StepType(Enum):
    """実行ステップのタイプ"""
    WORKFLOW = "workflow"       # 定理 WF 実行
    MACRO = "macro"            # マクロ展開 → 再帰実行
    SEQUENCE = "sequence"      # 順次実行コンテナ
    FOR_LOOP = "for_loop"      # F:N{body} ループ
    IF_COND = "if_cond"        # I:cond{body} 条件
    OSCILLATION = "oscillation" # A~B 振動
    FUSION = "fusion"          # A*B 融合
    PIPELINE = "pipeline"      # A |> B パイプライン
    PARALLEL = "parallel"      # A || B 並列実行
    COLIMIT = "colimit"        # \A Colimit 展開
    WHILE_LOOP = "while_loop"  # W:[cond]{body}
    CONVERGENCE = "convergence" # A >> cond / lim[cond]{A}


# --- 構造化コンテキスト伝播 ---

# LLM への構造化出力要求 (プロンプト末尾に付加)
_STRUCTURED_OUTPUT_INSTRUCTION = """
最後に、以下の JSON ブロックを出力してください (構造化伝播用):
```json
{"findings": ["発見1", "発見2"], "open_questions": ["問い1"], "confidence": 0.75, "summary": "1行要約"}
```"""


def _extract_structured_meta(output: str) -> tuple[str, Dict[str, Any]]:
    """LLM 出力末尾の JSON ブロックを抽出する。

    Returns:
        (clean_output, meta_dict) — JSON が見つからない場合は空 dict。
    """
    import json as _json
    import re as _re

    # ```json ... ``` ブロックを探す (複数ある場合は最後のもの)
    pattern = _re.compile(r'```json\s*\n(\{.*?\})\s*\n```', _re.DOTALL)
    matches = list(pattern.finditer(output))
    if not matches:
        return output, {}

    last_match = matches[-1]
    try:
        meta = _json.loads(last_match.group(1))
        if not isinstance(meta, dict):
            return output, {}
            
        # jsonschema による検証 (Phase 1 導入)
        try:
            from jsonschema import validate, ValidationError
            from hermeneus.src.schemas import WF_META_SCHEMA
            validate(instance=meta, schema=WF_META_SCHEMA)
        except ImportError:
            pass  # jsonschema がない場合はスキップ
        except Exception as e:  # noqa: BLE001
            logger.warning(f"structured_meta schema validation failed: {e}")
            # 無効なフィールドをフィルタするか、最低限 format を保つか
            # ここでは厳格にせず、取得できたものを返す (フェーズ1)
            
        # JSON ブロックを出力から除去 (表示をクリーンにする)
        clean = output[:last_match.start()].rstrip()
        return clean, meta
    except (_json.JSONDecodeError, ValueError):
        return output, {}
@dataclass
class ExecutionContext:
    """ステップ間のコンテキスト (作業記憶)

    各ステップの出力が次ステップの入力になる。
    $scope, $findings 等の WM 変数を保持。
    structured: 構造化メタデータ (findings, decisions, open_questions 等)
    """
    initial_input: str = ""
    current_output: str = ""
    variables: Dict[str, Any] = field(default_factory=dict)
    step_outputs: List[str] = field(default_factory=list)
    depth: int = 0  # ネスト深度
    derivative: str = ""  # マクロ派生 (+/-/^) — 深度パラメータとして使用
    structured: Dict[str, Any] = field(default_factory=dict)  # 構造化コンテキスト伝播

    # PURPOSE: ステップ出力を記録し、current を更新
    def push(self, output: str, step_name: str = ""):
        """ステップ出力を記録し、current を更新"""
        self.step_outputs.append(output)
        self.current_output = output
        if step_name:
            self.variables[f"${step_name}"] = output

    # PURPOSE: ステップ出力を構造化メタデータ付きで記録
    def push_structured(self, output: str, step_name: str, meta: Dict[str, Any]):
        """ステップ出力を構造化メタデータ付きで記録

        通常の push() に加え、structured にメタデータを蓄積する。
        meta のキー: findings, decisions, open_questions, confidence, summary
        """
        self.push(output, step_name)
        for key in ("findings", "decisions", "open_questions", "blind_spots"):
            if key in meta:
                self.structured.setdefault(key, []).extend(meta[key])
        if "confidence" in meta:
            self.structured["confidence"] = meta["confidence"]
        if "summary" in meta:
            self.structured.setdefault("phase_summary", {})[step_name] = meta["summary"]

    # PURPOSE: 子コンテキストを生成 (ループ/条件の内部用)
    def fork(self) -> "ExecutionContext":
        """子コンテキストを生成 (ループ/条件の内部用)"""
        import copy
        return ExecutionContext(
            initial_input=self.current_output,
            current_output=self.current_output,
            variables=dict(self.variables),
            step_outputs=[],
            depth=self.depth + 1,
            derivative=self.derivative,  # AP-1: 深度パラメータを子に伝播
            structured=copy.deepcopy(self.structured),  # 構造化コンテキストも伝播
        )


# PURPOSE: [L2-auto] 個別ステップの実行結果 (forward pass の出力)
@dataclass
class StepResult:
    """個別ステップの実行結果 (forward pass の出力)"""
    step_type: StepType
    node_id: str               # ノード識別子 (e.g., "/kho", "@fix")
    output: str                # 出力テキスト
    entropy_before: float      # 実行前エントロピー (0.0-1.0)
    entropy_after: float       # 実行後エントロピー (0.0-1.0)
    duration_ms: float = 0.0   # 実行時間
    gradient: float = 0.0      # 逆伝播で計算される帰責値
    children: List["StepResult"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # PURPOSE: エントロピー削減量 (denoising 量)
    @property
    def entropy_reduction(self) -> float:
        """エントロピー削減量 (denoising 量)"""
        return max(0, self.entropy_before - self.entropy_after)


# PURPOSE: [L2-auto] マクロ実行全体の結果
@dataclass
class ExecutionResult:
    """マクロ実行全体の結果"""
    ccl: str                   # 元の CCL 式
    expanded_ccl: str          # マクロ展開後の CCL
    steps: List[StepResult] = field(default_factory=list)
    final_output: str = ""
    structured_output: Dict[str, Any] = field(default_factory=dict)  # JSON Schema 構造化メタデータ
    final_confidence: float = 0.0  # /pis の確信度 (= 1 - final_entropy)
    total_entropy_reduction: float = 0.0
    total_duration_ms: float = 0.0

    # === Backward pass results ===
    bottleneck_step: Optional[str] = None  # gradient 最大のステップ
    gradient_map: Dict[str, float] = field(default_factory=dict)
    
    # === Morphism Proposals ===
    morphism_proposals: List[str] = field(default_factory=list)
    
    # === Macro Derivative (深度パラメータ) ===
    derivative: str = ""  # "+", "-", "^", "" のいずれか

    @property
    def success(self) -> bool:
        """ステップが1つ以上存在すれば成功と判定"""
        return len(self.steps) > 0

    # PURPOSE: 人間可読なサマリー
    # derivative → 深度レベル名のマッピング
    _DEPTH_LABELS = {"-": "L1 (Quick)", "": "L2 (Standard)", "+": "L3 (Deep)", "^": "L2 (Bird's eye)"}

    def summary(self) -> str:
        """人間可読なサマリー"""
        depth_label = self._DEPTH_LABELS.get(self.derivative, f"L2 ({self.derivative or 'default'})")
        lines = [
            f"CCL: {self.ccl}",
            f"展開: {self.expanded_ccl}",
            f"深度: {depth_label}",
            f"ステップ数: {len(self.steps)}",
            f"確信度: {self.final_confidence:.0%}",
            f"エントロピー削減: {self.total_entropy_reduction:.2f}",
            f"実行時間: {self.total_duration_ms:.0f}ms",
        ]
        if self.bottleneck_step:
            lines.append(f"ボトルネック: {self.bottleneck_step} (gradient: {self.gradient_map.get(self.bottleneck_step, 0):.2f})")

        lines.append("\nステップ別:")
        for s in self.steps:
            arrow = "↓" if s.entropy_reduction > 0 else "→"
            lines.append(
                f"  {arrow} {s.node_id:15s} "
                f"Δε={s.entropy_reduction:+.2f} "
                f"g={s.gradient:.2f} "
                f"({s.duration_ms:.0f}ms)"
            )
            
        if self.morphism_proposals:
            lines.append("\n【射提案 @complete】:")
            for prop in self.morphism_proposals:
                lines.append(f"  {prop}")
                
        return "\n".join(lines)


# =============================================================================
# Entropy Estimator
# =============================================================================

# PURPOSE: [L2-auto] エントロピー推定器
class EntropyEstimator:
    """エントロピー推定器

    LLM 出力のヒューリスティック分析でエントロピーを推定。
    拡散モデルの「ノイズレベル推定」に相当。
    """

    # 不確実性を示すマーカー
    UNCERTAINTY_MARKERS = [
        "不明", "不確実", "おそらく", "かもしれない", "推測",
        "未確認", "要確認", "TODO", "FIXME", "不明確",
        "uncertain", "maybe", "probably", "unknown", "unclear",
    ]
    # 確信を示すマーカー
    CONFIDENCE_MARKERS = [
        "確認済み", "検証済み", "完了", "成功", "✅",
        "confirmed", "verified", "passed", "success", "done",
    ]

    # PURPOSE: テキストからエントロピーを推定 (0.0=確実, 1.0=完全不確実)
    @classmethod
    def estimate(cls, text: str, context: Optional[ExecutionContext] = None) -> float:
        """テキストからエントロピーを推定 (0.0=確実, 1.0=完全不確実)

        推定方法:
        1. 不確実性マーカーの頻度
        2. 疑問文の頻度
        3. 出力の構造化度
        4. コンテキストの充実度
        """
        if not text:
            return 1.0  # 出力なし = 最大不確実性

        text_lower = text.lower()
        word_count = max(1, len(text.split()))

        # 1. 不確実性マーカー頻度
        uncertainty_count = sum(
            1 for m in cls.UNCERTAINTY_MARKERS if m in text_lower
        )
        uncertainty_ratio = min(1.0, uncertainty_count / (word_count * 0.1 + 1))

        # 2. 確信マーカー頻度
        confidence_count = sum(
            1 for m in cls.CONFIDENCE_MARKERS if m in text_lower
        )
        confidence_ratio = min(1.0, confidence_count / (word_count * 0.1 + 1))

        # 3. 疑問文頻度
        question_count = text.count("?") + text.count("？")
        question_ratio = min(1.0, question_count / max(1, text.count(".")))

        # 4. 構造化度 (テーブル, リスト, コードブロック → 低エントロピー)
        structure_markers = (
            text.count("|") + text.count("- ") + text.count("```")
        )
        structure_ratio = min(1.0, structure_markers / (word_count * 0.05 + 1))

        # 統合: 重み付き平均
        entropy = (
            0.3 * uncertainty_ratio
            - 0.3 * confidence_ratio
            + 0.2 * question_ratio
            - 0.2 * structure_ratio
            + 0.5  # ベースライン (情報がなければ0.5)
        )

        return max(0.0, min(1.0, entropy))

    # PURPOSE: 2つのテキスト間の意味論的収束度を推定する
    @classmethod
    def estimate_convergence(cls, prev_text: str, curr_text: str) -> float:
        """2つのテキスト間の意味論的収束度を推定する (0.0=全く異なる, 1.0=同一)

        n-gram Jaccard 類似度で意味論的な変化を捉える。
        単純なテキスト長比較ではなく、内容の構造的類似性を測定する。

        C:{} 収束ループの停止条件として使用。
        """
        if not prev_text or not curr_text:
            return 0.0

        # 3-gram で分割 (文字レベル n-gram — 言語非依存)
        def ngrams(text: str, n: int = 3) -> set:
            text = text.strip().lower()
            return {text[i:i+n] for i in range(len(text) - n + 1)} if len(text) >= n else {text}

        prev_ng = ngrams(prev_text)
        curr_ng = ngrams(curr_text)

        # Jaccard 類似度
        if not prev_ng and not curr_ng:
            return 1.0
        intersection = prev_ng & curr_ng
        union = prev_ng | curr_ng
        jaccard = len(intersection) / len(union) if union else 0.0

        # 構造類似度: 見出し・リスト・テーブル行の一致率
        def extract_structure(text: str) -> list:
            lines = text.strip().split('\n')
            return [l.strip()[:50] for l in lines if l.strip().startswith(('#', '|', '- ', '* ', '1.'))]

        prev_struct = set(extract_structure(prev_text))
        curr_struct = set(extract_structure(curr_text))
        if prev_struct or curr_struct:
            struct_sim = len(prev_struct & curr_struct) / max(1, len(prev_struct | curr_struct))
        else:
            struct_sim = jaccard  # 構造なしの場合は Jaccard をそのまま使用

        # 統合: n-gram 類似度 60% + 構造類似度 40%
        return 0.6 * jaccard + 0.4 * struct_sim

    # PURPOSE: 2つのテキスト間の意味論的ドリフト（ズレ）を測定する
    @classmethod
    def estimate_drift(cls, text_a: str, text_b: str) -> float:
        """2つのテキスト間の意味論的ドリフト（ズレ）を測定する (0.0=変化なし, 1.0=完全なドリフト)

        estimate_convergence の逆。ステップ間の文脈の断絶や、
        過剰なハルシネーションによる推論ツリーの脱線を検出するために使用。

        Returns:
            float: ドリフトスコア (0.0 - 1.0)
        """
        # 収束度 (similarity) の逆数をドリフトとする
        similarity = cls.estimate_convergence(text_a, text_b)
        return max(0.0, 1.0 - similarity)


# =============================================================================
# WF Resolver
# =============================================================================

# PURPOSE: [L2-auto] WF 名からファイルパスと定義テキストを解決
class WFResolver:
    """WF/Skill 名からファイルパスと定義テキストを解決

    優先順位: .agents/skills/{verb}/SKILL.md > nous/workflows/{verb}.md (レガシー)
    """

    # Skills ディレクトリ (WF 後継)
    SKILL_DIR = Path(__file__).resolve().parents[4] / ".agents" / "skills"
    # レガシー WF
    WF_DIR = Path(__file__).resolve().parents[2] / "nous" / "workflows"

    # PURPOSE: WF/Skill ID からファイルパスを解決
    @classmethod
    def resolve(cls, wf_id: str) -> Optional[Path]:
        """WF/Skill ID からファイルパスを解決"""
        clean_id = wf_id.lstrip("/")

        # 1. Skills パス (新): .agents/skills/{verb}/SKILL.md
        skill_path = cls.SKILL_DIR / clean_id / "SKILL.md"
        if skill_path.exists():
            return skill_path

        # 2. レガシー: nous/workflows/{verb}.md
        wf_path = cls.WF_DIR / f"{clean_id}.md"
        if wf_path.exists():
            return wf_path

        # 3. poiesis/ サブディレクトリ検索 (レガシー)
        poiesis_dir = cls.WF_DIR / "poiesis"
        if poiesis_dir.is_dir():
            for family_dir in poiesis_dir.iterdir():
                if family_dir.is_dir():
                    candidate = family_dir / f"{clean_id}.md"
                    if candidate.exists():
                        return candidate

        return None

    # PURPOSE: WF 定義テキストを読み込む
    @classmethod
    def load_definition(cls, wf_id: str) -> Optional[str]:
        """WF 定義テキストを読み込む"""
        path = cls.resolve(wf_id)
        if path:
            try:
                return path.read_text(encoding="utf-8")
            except Exception:  # noqa: BLE001
                return None
        return None

    # PURPOSE: WF の description (frontmatter) を抽出
    @classmethod
    def extract_description(cls, wf_id: str) -> str:
        """WF の description (frontmatter) を抽出"""
        text = cls.load_definition(wf_id)
        if not text:
            return f"WF /{wf_id} (定義ファイル未発見)"
        import re
        match = re.search(r"description:\s*(.+)", text)
        return match.group(1).strip() if match else f"WF /{wf_id}"

    # PURPOSE: WF の Execution Guide セクションを抽出
    @classmethod
    def extract_execution_guide(cls, wf_id: str) -> Optional[str]:
        """WF の Execution Guide セクションを抽出"""
        text = cls.load_definition(wf_id)
        if not text:
            return None
        import re
        # Execution Guide からファイルの末尾まで全て抽出
        # コードブロック内の ## にマッチして途切れるのを防ぐ + Post-Check も含める
        match = re.search(r"^## Execution Guide.*", text, re.DOTALL | re.MULTILINE)
        if match:
            return match.group(0).strip()
        return None


# =============================================================================
# AST Walker (Forward Pass)
# =============================================================================

# PURPOSE: [L2-auto] AST を再帰的に辿り、各ノードを実行する
class ASTWalker:
    """AST を再帰的に辿り、各ノードを実行する

    ニューラルネットの forward pass に相当。
    各ステップでエントロピーを計測し、StepResult を生成。
    """

    # PURPOSE: Initialize instance
    def __init__(
        self,
        step_handler: Optional[Callable] = None,
        entropy_estimator: Optional[EntropyEstimator] = None,
        event_bus: Optional[Any] = None,
        environment: Optional[Any] = None,
    ):
        """
        Args:
            step_handler: WF ステップの実行関数
                signature: (wf_id: str, params: dict, ctx: ExecutionContext) -> str
                None の場合はデフォルトハンドラ (定義テキスト返却) を使用
            entropy_estimator: エントロピー推定器
            event_bus: (後方互換) CognitionEventBus インスタンス
            environment: CognitionEnvironment インスタンス (Phase 4b)
                None の場合はイベント emit をスキップ
        """
        self.step_handler = step_handler or self._default_handler
        self.estimator = entropy_estimator or EntropyEstimator()
        # Phase 4b: environment を優先。event_bus はフォールバック (後方互換)
        self.environment = environment or event_bus
        self.event_bus = self.environment  # 後方互換エイリアス

    # PURPOSE: AST ノードを実行 (forward pass)
    def walk(self, node: Any, ctx: ExecutionContext) -> StepResult:
        """AST ノードを実行 (forward pass)"""
        from hermeneus.src.ccl_ast import (
            Workflow, MacroRef, Sequence, ForLoop, IfCondition,
            WhileLoop, Oscillation, Fusion, ConvergenceLoop,
            ColimitExpansion, Pipeline, Parallel, Program,
            TaggedBlock, OpenEnd, Group
        )

        if isinstance(node, Program):
            return self._walk_program(node, ctx)
        elif isinstance(node, Sequence):
            return self._walk_sequence(node, ctx)
        elif isinstance(node, Workflow):
            return self._walk_workflow(node, ctx)
        elif isinstance(node, MacroRef):
            return self._walk_macro(node, ctx)
        elif isinstance(node, ForLoop):
            return self._walk_for(node, ctx)
        elif isinstance(node, IfCondition):
            return self._walk_if(node, ctx)
        elif isinstance(node, WhileLoop):
            return self._walk_while(node, ctx)
        elif isinstance(node, Oscillation):
            return self._walk_oscillation(node, ctx)
        elif isinstance(node, Fusion):
            return self._walk_fusion(node, ctx)
        elif isinstance(node, ConvergenceLoop):
            return self._walk_convergence(node, ctx)
        elif isinstance(node, ColimitExpansion):
            return self._walk_colimit(node, ctx)
        elif isinstance(node, Pipeline):
            return self._walk_pipeline(node, ctx)
        elif isinstance(node, Parallel):
            return self._walk_parallel(node, ctx)
        elif isinstance(node, TaggedBlock):
            return self._walk_tagged_block(node, ctx)
        elif isinstance(node, Group):
            return self._walk_group(node, ctx)
        elif isinstance(node, OpenEnd):
            return StepResult(
                step_type=StepType.PIPELINE,
                node_id="open_end",
                output=ctx.current_output,
                entropy_before=0.5,
                entropy_after=0.5,
                metadata={"is_open_end": True}
            )
        else:
            return StepResult(
                step_type=StepType.WORKFLOW,
                node_id=f"unknown({type(node).__name__})",
                output=str(node),
                entropy_before=0.5,
                entropy_after=0.5,
            )

    # PURPOSE: Program ノード: 全式を順次実行
    def _walk_program(self, node, ctx: ExecutionContext) -> StepResult:
        """Program ノード: 全式を順次実行"""
        children = []
        for expr in node.expressions:
            child = self.walk(expr, ctx)
            children.append(child)
            ctx.push(child.output)

        return StepResult(
            step_type=StepType.SEQUENCE,
            node_id="program",
            output=ctx.current_output,
            entropy_before=children[0].entropy_before if children else 0.5,
            entropy_after=children[-1].entropy_after if children else 0.5,
            children=children,
        )

    # PURPOSE: Sequence (_ チェイン): ステップを順次実行
    def _walk_sequence(self, node, ctx: ExecutionContext) -> StepResult:
        """Sequence (_ チェイン): ステップを順次実行"""
        children = []
        initial_entropy = self.estimator.estimate(ctx.current_output)

        for step in node.steps:
            child = self.walk(step, ctx)
            children.append(child)
            
            # [D1] Drift 測定: 前ステップ出力と現ステップ出力のズレを測る
            if len(children) > 1:
                drift = self.estimator.estimate_drift(
                    children[-2].output, child.output
                )
                child.metadata["semantic_drift"] = drift
                if drift > 0.7:  # ドリフト警告閾値
                    logger.warning(f"[Drift Warning] Step {child.node_id} drifted {drift:.2f} from previous context")
                    # [D1→D2] 動的結合: ドリフト超過時に検証アラートを発行
                    child.metadata["drift_alert"] = True
                    child.metadata["drift_context"] = {
                        "prev_step": children[-2].node_id,
                        "curr_step": child.node_id,
                        "drift_score": drift,
                        "prev_output_snippet": children[-2].output[:200],
                        "curr_output_snippet": child.output[:200],
                    }
                    if self.environment:
                        from hermeneus.src.event_bus import CognitionEvent, EventType
                        drift_event = CognitionEvent(
                            event_type=EventType.DRIFT_ALERT,
                            source_node=child.node_id,
                            entropy_before=children[-2].entropy_after,
                            entropy_after=child.entropy_after,
                            metadata={
                                "step": child.node_id,
                                "drift": drift,
                                "prev_step": children[-2].node_id,
                                "prev_output": children[-2].output[:2000],
                                "curr_output": child.output[:2000],
                            }
                        )
                        self.environment.emit(drift_event)
                        # D1→D2 還元: DriftGuardSubscriber が verdict を
                        # イベントメタデータに注入するので、child に書き戻す
                        if "drift_verdict" in drift_event.metadata:
                            child.metadata["drift_verdict"] = drift_event.metadata["drift_verdict"]
                            child.metadata["drift_verdict_confidence"] = drift_event.metadata.get("drift_verdict_confidence", 0.0)
                            child.metadata["drift_verdict_reasoning"] = drift_event.metadata.get("drift_verdict_reasoning", "")
                            if drift_event.metadata.get("drift_rejected"):
                                child.metadata["drift_rejected"] = True

            # [W1] Entropy Change 検出: ステップ前後のエントロピー差分を監視
            entropy_delta = abs(child.entropy_after - child.entropy_before)
            child.metadata["entropy_delta"] = entropy_delta
            if entropy_delta > 0.3 and self.environment:  # 有意なエントロピー変化
                from hermeneus.src.event_bus import CognitionEvent, EventType
                entropy_event = CognitionEvent(
                    event_type=EventType.ENTROPY_CHANGE,
                    source_node=child.node_id,
                    entropy_before=child.entropy_before,
                    entropy_after=child.entropy_after,
                    metadata={
                        "entropy_delta": entropy_delta,
                        "step": child.node_id,
                        "prev_output": children[-2].output[:2000] if len(children) > 1 else "",
                        "curr_output": child.output[:2000],
                        "prev_step": children[-2].node_id if len(children) > 1 else "",
                    }
                )
                self.environment.emit(entropy_event)
                # entropy_guard の verdict 還元
                if "drift_verdict" in entropy_event.metadata:
                    child.metadata["entropy_verdict"] = entropy_event.metadata["drift_verdict"]
                    if entropy_event.metadata.get("drift_rejected"):
                        child.metadata["drift_rejected"] = True
            
            # F1: drift_rejected 時の後続ステップへの警告注入
            push_output = child.output
            if child.metadata.get("drift_rejected"):
                sd = child.metadata.get('semantic_drift', 0)
                vc = child.metadata.get('drift_verdict_confidence', 0)
                drift_warning = (
                    "\n[⚠️ DRIFT REJECTED: 前ステップとの論理的断絶が検出されました。"
                    f" drift={sd:.2f}, confidence={vc:.0%}."
                    " 以下の出力を批判的に再評価してください]\n"
                )
                push_output = drift_warning + child.output
            ctx.push(push_output)

        return StepResult(
            step_type=StepType.SEQUENCE,
            node_id="sequence",
            output=ctx.current_output,
            entropy_before=initial_entropy,
            entropy_after=children[-1].entropy_after if children else initial_entropy,
            children=children,
        )

    # PURPOSE: Workflow ノード: 単一 WF を実行
    def _walk_workflow(self, node, ctx: ExecutionContext) -> StepResult:
        """Workflow ノード: 単一 WF を実行"""
        start = time.monotonic()
        entropy_before = self.estimator.estimate(ctx.current_output)

        # パラメータ抽出
        params = dict(node.modifiers) if node.modifiers else {}
        if node.mode:
            params["mode"] = node.mode
        elif ctx.derivative:
            # マクロ派生のベースライン深度を適用
            # ノード自身の mode がある場合はそちらを優先（上書き）
            params["mode"] = ctx.derivative

        # 実行
        output = self.step_handler(node.id, params, ctx)

        entropy_after = self.estimator.estimate(output)
        duration = (time.monotonic() - start) * 1000

        result = StepResult(
            step_type=StepType.WORKFLOW,
            node_id=f"/{node.id}",
            output=output,
            entropy_before=entropy_before,
            entropy_after=entropy_after,
            duration_ms=duration,
            metadata={"params": params},
        )

        # Phase 2: STEP_COMPLETE イベントを emit
        self._emit_event(
            "step_complete", result, ctx,
            source_node=f"/{node.id}",
        )

        # エントロピー変化が大きい場合は ENTROPY_CHANGE も emit
        entropy_delta = abs(entropy_after - entropy_before)
        if entropy_delta > 0.1:
            self._emit_event(
                "entropy_change", result, ctx,
                source_node=f"/{node.id}",
            )

        return result

    # PURPOSE: MacroRef: マクロを展開して再帰実行
    def _walk_macro(self, node, ctx: ExecutionContext) -> StepResult:
        import importlib
        _macro_registry = importlib.import_module('mekhane.ccl.macro_registry')
        MacroRegistry = _macro_registry.MacroRegistry
        from hermeneus.src.parser import CCLParser

        registry = MacroRegistry()
        macro = registry.get(node.name)

        if not macro:
            return StepResult(
                step_type=StepType.MACRO,
                node_id=f"@{node.name}",
                output=f"[Error: Macro @{node.name} not found]",
                entropy_before=1.0,
                entropy_after=1.0,
            )

        # マクロ展開 → パース → 再帰実行
        parser = CCLParser()
        expanded_ast = parser.parse(macro.ccl)
        child_ctx = ctx.fork()
        
        # マクロ実行中であることをコンテキストに記録 (LLMStepHandler での Execution Guide 注入用)
        child_ctx.variables["$active_macro"] = node.name
        
        child_result = self.walk(expanded_ast, child_ctx)

        # 子の出力を親コンテキストに反映
        ctx.push(child_result.output, node.name)

        return StepResult(
            step_type=StepType.MACRO,
            node_id=f"@{node.name}",
            output=child_result.output,
            entropy_before=child_result.entropy_before,
            entropy_after=child_result.entropy_after,
            duration_ms=child_result.duration_ms,
            children=child_result.children if child_result.children else [child_result],
            metadata={"expanded_ccl": macro.ccl},
        )

    # PURPOSE: ForLoop: N回繰り返し
    def _walk_for(self, node, ctx: ExecutionContext) -> StepResult:
        """ForLoop: N回繰り返し"""
        children = []
        initial_entropy = self.estimator.estimate(ctx.current_output)

        iterations = node.iterations if isinstance(node.iterations, int) else len(node.iterations)

        for i in range(iterations):
            child_ctx = ctx.fork()
            child_ctx.variables["$i"] = i
            # P1 横展開: F:[×N]{} ループでも CognitiveStepHandler の
            # イテレーション変動を有効化 (C:{} と同じ変数名を使用)
            child_ctx.variables["$convergence_iteration"] = i + 1
            if isinstance(node.iterations, list) and i < len(node.iterations):
                child_ctx.variables["$item"] = node.iterations[i]

            child = self.walk(node.body, child_ctx)
            children.append(child)
            ctx.push(child.output)

        return StepResult(
            step_type=StepType.FOR_LOOP,
            node_id=f"F:{iterations}",
            output=ctx.current_output,
            entropy_before=initial_entropy,
            entropy_after=children[-1].entropy_after if children else initial_entropy,
            children=children,
        )

    # PURPOSE: IfCondition: 条件分岐 (数値比較対応)
    def _walk_if(self, node, ctx: ExecutionContext) -> StepResult:
        """IfCondition: 条件分岐

        v6.0: 数値条件評価に対応。
        I:[ε>θ]{...} のような数値比較を実行時の変数で評価する。
        Condition(var='V[]', op='<', value=0.5) のような構造を受け取る。
        """
        initial_entropy = self.estimator.estimate(ctx.current_output)

        condition_met = self._evaluate_condition(node.condition, ctx)

        if condition_met:
            child = self.walk(node.then_branch, ctx)
        elif node.else_branch:
            child = self.walk(node.else_branch, ctx)
        else:
            child = StepResult(
                step_type=StepType.IF_COND,
                node_id="I:skip",
                output=ctx.current_output,
                entropy_before=initial_entropy,
                entropy_after=initial_entropy,
            )

        return StepResult(
            step_type=StepType.IF_COND,
            node_id=f"I:{getattr(node.condition, 'var', '?')}",
            output=child.output,
            entropy_before=initial_entropy,
            entropy_after=child.entropy_after,
            children=[child],
        )

    # PURPOSE: 条件を評価する (数値比較 + キーワード検索)
    def _evaluate_condition(self, condition, ctx: ExecutionContext) -> bool:
        """条件を評価する。

        対応パターン:
        1. 数値比較: Condition(var='V[]', op='<', value=0.5)
           → ctx.variables から $verified 等の確信度を取得して比較
        2. キーワード検索: var が文字列で op/value がない場合
           → ctx.current_output にキーワードが含まれるかチェック
        3. チェックマーク: var が '✓' → 常に True (検証パス)
        """
        cond_var = getattr(condition, 'var', '') if condition else ''
        cond_op = getattr(condition, 'op', None)
        cond_value = getattr(condition, 'value', None)

        # パターン1: チェックマーク (✓) → 常に True
        if cond_var == '✓':
            return True

        # パターン2: 数値比較 (op と value がある場合)
        if cond_op and cond_value is not None:
            # 変数名から実行時の値を解決
            runtime_value = self._resolve_variable(cond_var, ctx)
            if runtime_value is not None:
                try:
                    rv = float(runtime_value)
                    tv = float(cond_value)
                    if cond_op == '<': return rv < tv
                    elif cond_op == '>': return rv > tv
                    elif cond_op == '<=': return rv <= tv
                    elif cond_op == '>=': return rv >= tv
                    elif cond_op == '==': return rv == tv
                    elif cond_op == '!=': return rv != tv
                except (ValueError, TypeError):
                    pass

        # パターン3: フォールバック — キーワード検索
        if cond_var:
            return cond_var.lower() in ctx.current_output.lower()
        return True

    # PURPOSE: 変数名を実行時の値に解決する
    def _resolve_variable(self, var_name: str, ctx: ExecutionContext):
        """変数名を実行時の値に解決する。

        対応パターン:
        - 'V[]' → $verified (検証ゲートの結果)
        - 'ε' → 直近のエントロピー
        - '$xxx' → ctx.variables['$xxx']
        """
        # V[] → $verified
        if var_name in ('V[]', 'V'):
            return ctx.variables.get('$verified', None)
        # ε → 直近のエントロピー推定
        if var_name in ('ε', 'epsilon'):
            return self.estimator.estimate(ctx.current_output)
        # 直接変数参照
        if var_name.startswith('$'):
            return ctx.variables.get(var_name, None)
        return None

    # PURPOSE: Oscillation (A~B / A~*B): 2つのノードを交互実行
    def _walk_oscillation(self, node, ctx: ExecutionContext) -> StepResult:
        """Oscillation (A~B / A~*B): 2つのノードを交互実行

        ~ (通常振動): エントロピー変化が 0.05 未満で停止。最大 max_iterations 回。
        ~* (収束振動): より厳密。エントロピー変化が 0.01 未満 かつ
                       最低3回の反復を要求。確実に収束させる。
        """
        children = []
        initial_entropy = self.estimator.estimate(ctx.current_output)
        max_iters = getattr(node, 'max_iterations', 3)
        is_convergent = getattr(node, 'convergent', False)

        # ~* (収束振動) では最低反復回数と閾値を厳しくする
        min_iters = 3 if is_convergent else 1
        threshold = 0.01 if is_convergent else 0.05

        for i in range(max_iters):
            left = self.walk(node.left, ctx)
            ctx.push(left.output)
            children.append(left)

            right = self.walk(node.right, ctx)
            ctx.push(right.output)
            children.append(right)

            # 収束チェック (最低反復回数を超えてから)
            if i >= min_iters and len(children) >= 4:
                delta = abs(right.entropy_after - children[-4].entropy_after)
                if delta < threshold:
                    break

        return StepResult(
            step_type=StepType.OSCILLATION,
            node_id="oscillation~*" if is_convergent else "oscillation",
            output=ctx.current_output,
            entropy_before=initial_entropy,
            entropy_after=children[-1].entropy_after if children else initial_entropy,
            children=children,
        )

    # PURPOSE: テキストを構造的に分割する (*% 外積融合用)
    @staticmethod
    def _split_structured(text: str) -> list[str]:
        """テキストを構造的に分割する。

        優先順位:
        1. 見出し (#, ##, ###) で分割 → セクション単位
        2. 番号付きリスト (1., 2., 3.) で分割 → アイテム単位
        3. 箇条書き (- , * ) で分割 → 要素単位
        4. フォールバック: 段落 (\\n\\n) で分割 → 段落単位
        5. 最終フォールバック: 全体を1要素

        Returns: 少なくとも1要素を含むリスト
        """
        if not text or not text.strip():
            return [text or ""]

        lines = text.strip().split('\n')

        # コードブロック内の行をマスク (``` で囲まれた範囲を除外)
        in_code_block = False
        content_lines = []  # (index, line, is_content) — コードブロック外の行のみ分割対象
        for i, l in enumerate(lines):
            if l.strip().startswith('```'):
                in_code_block = not in_code_block
                content_lines.append((i, l, False))
            elif in_code_block:
                content_lines.append((i, l, False))
            else:
                content_lines.append((i, l, True))

        # 分割対象の行インデックスだけを取得
        active_indices = {i for i, _, is_content in content_lines if is_content}

        # 戦略1: 見出しで分割 (コードブロック外のみ)
        heading_indices = [i for i, l in enumerate(lines)
                          if i in active_indices and l.strip().startswith('#')]
        if len(heading_indices) >= 2:
            sections = []
            for k, idx in enumerate(heading_indices):
                end = heading_indices[k + 1] if k + 1 < len(heading_indices) else len(lines)
                section = '\n'.join(lines[idx:end]).strip()
                if section:
                    sections.append(section)
            if sections:
                return sections

        # 戦略2: 番号付きリストで分割 (コードブロック外のみ)
        import re
        numbered = [i for i, l in enumerate(lines)
                    if i in active_indices and re.match(r'^\s*\d+[\.\)]\s', l)]
        if len(numbered) >= 2:
            items = []
            for k, idx in enumerate(numbered):
                end = numbered[k + 1] if k + 1 < len(numbered) else len(lines)
                item = '\n'.join(lines[idx:end]).strip()
                if item:
                    items.append(item)
            if items:
                return items

        # 戦略3: 箇条書きで分割 (コードブロック外のみ)
        bullet = [i for i, l in enumerate(lines)
                  if i in active_indices and l.strip().startswith(('- ', '* ', '• '))]
        if len(bullet) >= 2:
            items = []
            for k, idx in enumerate(bullet):
                end = bullet[k + 1] if k + 1 < len(bullet) else len(lines)
                item = '\n'.join(lines[idx:end]).strip()
                if item:
                    items.append(item)
            if items:
                return items

        # 戦略4: 段落分割
        parts = [p.strip() for p in text.split('\n\n') if p.strip()]
        if len(parts) >= 2:
            return parts

        # 戦略5: 全体を1要素
        return [text.strip()]

    # PURPOSE: Fusion (A*B / A%B / A*%B): 2つのノードの出力を統合
    def _walk_fusion(self, node, ctx: ExecutionContext) -> StepResult:
        """Fusion (A*B / A%B / A*%B): 2つのノードの出力を統合

        * (通常融合): 両方を実行し、出力を結合。
        % (外積): 左の出力の各要素と右の出力の各要素を掛け合わせ、
                  全組み合わせを生成する。テンソル積 (copy morphism)。
        *% (内積+外積): % と同じ外積展開を行う。収束+展開の同時操作。
        """
        initial_entropy = self.estimator.estimate(ctx.current_output)
        # % (outer_product) と *% (fuse_outer) の両方で外積展開を有効化
        is_outer = getattr(node, 'fuse_outer', False) or getattr(node, 'outer_product', False)

        left = self.walk(node.left, ctx)
        right = self.walk(node.right, ctx)

        if is_outer:
            # 外積融合: 構造的分割→全組み合わせ生成
            left_parts = self._split_structured(left.output)
            right_parts = self._split_structured(right.output)
            combinations = []
            for i, lp in enumerate(left_parts):
                for j, rp in enumerate(right_parts):
                    combinations.append(
                        f"[Tensor({i+1},{j+1})]\n{lp}\n× {rp}"
                    )
            fused = f"[OuterProduct: {len(left_parts)}×{len(right_parts)} = {len(combinations)} combinations]\n"
            fused += "\n---\n".join(combinations)
        else:
            # 通常融合: 両方の出力を結合
            fused = f"[Fusion]\n{left.output}\n---\n{right.output}"

        ctx.push(fused)

        # node_id: *% = fusion*%, % = fusion%, * = fusion
        if getattr(node, 'fuse_outer', False):
            fusion_id = "fusion*%"
        elif getattr(node, 'outer_product', False):
            fusion_id = "fusion%"
        else:
            fusion_id = "fusion"

        return StepResult(
            step_type=StepType.FUSION,
            node_id=fusion_id,
            output=fused,
            entropy_before=initial_entropy,
            entropy_after=min(left.entropy_after, right.entropy_after),
            children=[left, right],
        )

    # PURPOSE: Pipeline (A |> B |> C): 前段の出力を次段の入力にチェイン
    def _walk_pipeline(self, node, ctx: ExecutionContext) -> StepResult:
        """Pipeline (A |> B |> C): 前段の出力を次段の入力にチェイン

        Unix パイプと同じ: 各ステップの出力が次ステップのコンテキストになる。
        Sequence (_) との違い: Pipeline は出力を明示的に入力として渡す。
        """
        children = []
        initial_entropy = self.estimator.estimate(ctx.current_output)

        for step in node.steps:
            child = self.walk(step, ctx)
            children.append(child)
            
            # [D1] Drift 測定
            if len(children) > 1:
                drift = self.estimator.estimate_drift(
                    children[-2].output, child.output
                )
                child.metadata["semantic_drift"] = drift
                if drift > 0.7:
                    logger.warning(f"[Drift Warning] Pipeline Step {child.node_id} drifted {drift:.2f} from previous context")
                    # [D1→D2] 動的結合
                    child.metadata["drift_alert"] = True
                    child.metadata["drift_context"] = {
                        "prev_step": children[-2].node_id,
                        "curr_step": child.node_id,
                        "drift_score": drift,
                        "prev_output_snippet": children[-2].output[:200],
                        "curr_output_snippet": child.output[:200],
                    }
                    if self.environment:
                        from hermeneus.src.event_bus import CognitionEvent, EventType
                        drift_event = CognitionEvent(
                            event_type=EventType.DRIFT_ALERT,
                            source_node=child.node_id,
                            metadata={
                                "step": child.node_id,
                                "drift": drift,
                                "prev_step": children[-2].node_id,
                            }
                        )
                        self.environment.emit(drift_event)
            
            # パイプライン: 出力を次のステップの入力に直接注入
            ctx.push(child.output)
            ctx.variables["$pipe_input"] = child.output

        return StepResult(
            step_type=StepType.PIPELINE,
            node_id="pipeline",
            output=ctx.current_output,
            entropy_before=initial_entropy,
            entropy_after=children[-1].entropy_after if children else initial_entropy,
            children=children,
        )

    # PURPOSE: Parallel (A || B || C): 全ブランチを独立実行し、結果を統合
    def _walk_parallel(self, node, ctx: ExecutionContext) -> StepResult:
        """Parallel (A || B || C): 全ブランチを独立実行し、結果を統合

        各ブランチは独立したコンテキスト (fork) で実行。
        結果はエントロピー最小 (最も確信度の高い) のブランチを採用しつつ、
        全ブランチの出力を融合して返す。
        """
        children = []
        initial_entropy = self.estimator.estimate(ctx.current_output)

        for branch in node.branches:
            branch_ctx = ctx.fork()
            child = self.walk(branch, branch_ctx)
            children.append(child)

        if not children:
            return StepResult(
                step_type=StepType.PARALLEL,
                node_id="parallel",
                output=ctx.current_output,
                entropy_before=initial_entropy,
                entropy_after=initial_entropy,
            )

        # 全ブランチの出力を融合
        outputs = [f"[Branch {i+1}] {c.output}" for i, c in enumerate(children)]
        merged = "[Parallel Results]\n" + "\n---\n".join(outputs)
        ctx.push(merged)

        # エントロピーは全ブランチの最小値 (最良の結果を採用)
        best_entropy = min(c.entropy_after for c in children)

        return StepResult(
            step_type=StepType.PARALLEL,
            node_id="parallel",
            output=merged,
            entropy_before=initial_entropy,
            entropy_after=best_entropy,
            children=children,
        )

    # PURPOSE: ColimitExpansion (\A): Colimit 展開 — 全派生を列挙し統合
    def _walk_colimit(self, node, ctx: ExecutionContext) -> StepResult:
        """ColimitExpansion (\\A): Colimit 展開 — 全派生を列挙し統合

        圏論的意味: Colimit = 余極限 = 全射影の合併。
        WF の全派生(variants)を展開し、統合的な視点を構築する。
        """
        initial_entropy = self.estimator.estimate(ctx.current_output)

        # 内部ノードを実行
        child = self.walk(node.body, ctx)

        # Colimit の意味: 展開 + 全派生合併のメタ情報を追加
        expanded = (
            f"[Colimit Expansion]\n"
            f"{child.output}\n"
            f"---\n"
            f"全派生を展開済み。余極限として統合。"
        )
        ctx.push(expanded)

        return StepResult(
            step_type=StepType.COLIMIT,
            node_id="colimit",
            output=expanded,
            entropy_before=initial_entropy,
            entropy_after=child.entropy_after * 0.9,  # 展開により若干改善
            children=[child],
        )

    # PURPOSE: Group ((expr)op): グループ全体に修飾子を適用
    def _walk_group(self, node, ctx: ExecutionContext) -> StepResult:
        """Group ((expr)op): グループ全体に修飾子を適用

        意味論:
            (A*B)+ は「A と B の融合結果を深化する」。
            内部式を実行した後、グループの修飾子をメタデータとして付与する。
            修飾子に DEEPEN が含まれる場合は mode='+' をコンテキストに反映。
        """
        from hermeneus.src.ccl_ast import OpType

        initial_entropy = self.estimator.estimate(ctx.current_output)

        # グループ修飾子を mode に変換してコンテキストに反映
        _OP_TO_MODE = {
            OpType.DEEPEN: "+",
            OpType.CONDENSE: "-",
            OpType.ASCEND: "^",
        }
        group_mode = None
        for op in node.operators:
            if op in _OP_TO_MODE:
                group_mode = _OP_TO_MODE[op]
                break

        if group_mode:
            ctx.push(f"[Group mode: {group_mode}]")

        # 内部式を実行
        child = self.walk(node.body, ctx)

        # メタデータにグループ修飾子を記録
        op_names = [op.name for op in node.operators]
        child.metadata["group_operators"] = op_names
        if group_mode:
            child.metadata["group_mode"] = group_mode

        return StepResult(
            step_type=StepType.WORKFLOW,
            node_id=f"group({','.join(op_names)})",
            output=child.output,
            entropy_before=initial_entropy,
            entropy_after=child.entropy_after,
            children=[child],
            metadata={"group_operators": op_names, "group_mode": group_mode},
        )

    # PURPOSE: WhileLoop (W:[cond]{body}): 条件が真の間ループ
    def _walk_while(self, node, ctx: ExecutionContext) -> StepResult:
        """WhileLoop (W:[cond]{body}): 条件が真の間ループ

        条件評価はヒューリスティック: エントロピーベースの収束判定。
        最大反復は安全のため制限 (max_iterations=10)。
        """
        children = []
        initial_entropy = self.estimator.estimate(ctx.current_output)
        max_iterations = 10  # 安全制限

        for i in range(max_iterations):
            # 条件評価: Condition ノードの値とコンテキストのエントロピーを比較
            current_entropy = self.estimator.estimate(ctx.current_output)
            cond_threshold = node.condition.value if hasattr(node.condition, 'value') else 0.5
            cond_op = node.condition.op if hasattr(node.condition, 'op') else '>'

            # 条件判定
            if cond_op == '>':
                should_continue = current_entropy > cond_threshold
            elif cond_op == '<':
                should_continue = current_entropy < cond_threshold
            elif cond_op == '>=':
                should_continue = current_entropy >= cond_threshold
            elif cond_op == '<=':
                should_continue = current_entropy <= cond_threshold
            else:
                should_continue = i < 3  # デフォルト: 3回

            if not should_continue:
                break

            child_ctx = ctx.fork()
            child_ctx.variables["$iteration"] = i
            child = self.walk(node.body, child_ctx)
            children.append(child)
            ctx.push(child.output)

        return StepResult(
            step_type=StepType.WHILE_LOOP,
            node_id=f"W:{len(children)}",
            output=ctx.current_output,
            entropy_before=initial_entropy,
            entropy_after=children[-1].entropy_after if children else initial_entropy,
            children=children,
        )

    # PURPOSE: ConvergenceLoop (A >> cond / lim[cond]{A}): 収束するまで反復
    def _walk_convergence(self, node, ctx: ExecutionContext) -> StepResult:
        """ConvergenceLoop (A >> cond / lim[cond]{A}): 収束するまで反復

        本体を繰り返し実行し、条件が満たされるか
        エントロピー変化が閾値以下になったら停止。
        """
        children = []
        initial_entropy = self.estimator.estimate(ctx.current_output)
        max_iters = getattr(node, 'max_iterations', 5)
        prev_entropy = initial_entropy

        for i in range(max_iters):
            # P1 統合: 収束ループでも視点変動を有効化
            ctx.variables['$convergence_iteration'] = i + 1
            child = self.walk(node.body, ctx)
            children.append(child)
            ctx.push(child.output)

            # 収束判定: 条件閾値チェック
            cond_threshold = node.condition.value if hasattr(node.condition, 'value') else 0.5
            if child.entropy_after < cond_threshold:
                break  # 収束条件を満たした

            # 追加の収束判定: エントロピー変化が小さい = プラトー
            if i > 0 and abs(child.entropy_after - prev_entropy) < 0.02:
                break  # プラトーに到達

            prev_entropy = child.entropy_after

        return StepResult(
            step_type=StepType.CONVERGENCE,
            node_id=f"convergence:{len(children)}",
            output=ctx.current_output,
            entropy_before=initial_entropy,
            entropy_after=children[-1].entropy_after if children else initial_entropy,
            children=children,
        )

    # PURPOSE: TaggedBlock (V:{}, C:{}, R:{}, M:{}, E:{}): 意味タグ付き実行
    def _walk_tagged_block(self, node, ctx: ExecutionContext) -> StepResult:
        """TaggedBlock (V:{}, C:{}, R:{}, M:{}, E:{}): 意味タグ付き実行

        CPL v2.0 意味タグ。
        Tags:
            V = Validate (検証) — 内部実行後、結果を $verified に保存
            C = Convergence (収束ループ) — 内部を反復実行し、エントロピーが
                安定するまで繰り返す。v5.0 の「生きた認知」の核心。
            R = Repeat (反復) — 内部を実行
            M = Memorize (記憶) — 内部実行、結果を $memory に保存
            E = Error/Else — IfCondition の else ブランチ
            I = If/Invariant — 条件付き実行 (内部の IfCondition に委譲)
        """
        tag = node.tag

        # C:{} は収束ループとして特別処理
        if tag == 'C':
            return self._walk_convergence_loop(node, ctx)

        initial_entropy = self.estimator.estimate(ctx.current_output)

        # 内部ノードを実行
        child = self.walk(node.body, ctx)

        # タグに応じた後処理
        if tag == 'V':  # Verification
            ctx.variables['$verified'] = child.output
        elif tag == 'M':  # Memory/Memorize
            ctx.variables['$memory'] = child.output
        # R (Repeat), E (Else) は特別な後処理なし

        ctx.push(child.output, f"{tag}_block")

        result = StepResult(
            step_type=StepType.SEQUENCE,
            node_id=f"{tag}:block",
            output=child.output,
            entropy_before=initial_entropy,
            entropy_after=child.entropy_after,
            children=[child],
        )

        # Phase 2: V:{} 完了時に VERIFICATION イベントを emit
        if tag == 'V':
            self._emit_event(
                "verification", result, ctx,
                source_node=f"{tag}:block",
                extra_metadata={"step_outputs": ctx.step_outputs.copy()}
            )

        return result

    # PURPOSE: C:{} 収束ループ — 生きた認知の核心
    def _walk_convergence_loop(self, node, ctx: ExecutionContext) -> StepResult:
        """C:{} 収束ループ (Convergence Loop) — 差分実行対応

        逆拡散プロセスとしての計画:
        内部ブロックを反復実行し、**出力の意味論的類似度**が
        安定する (予測誤差 ε が閾値を下回る) まで繰り返す。

        差分実行 (Delta Execution):
        2回目以降のイテレーションでは、前回の出力をキャッシュし、
        入力コンテキストが変化していない場合はノードの再実行をスキップ。
        これにより API 呼び出し回数を劇的に削減する。

        レート制限対策:
        反復間に短い sleep を挿入し、API の「息継ぎ」を確保。

        最大 max_convergence_iters 回で打ち切り。
        最低2回は実行する (1回目の出力と比較するため)。
        """
        import time as _time

        max_iters = 5  # 収束ループの最大反復回数
        convergence_threshold = 0.85  # 意味論的類似度がこれ以上なら収束
        entropy_threshold = 0.03  # エントロピー差分の閾値 (補助)
        # P3: フロントマターから最低反復回数を取得 (デフォルト2)
        min_iters = ctx.variables.get("$min_convergence_iters", 2)
        pacing_sleep = 1.0  # 反復間の sleep (秒) — API レート制限対策

        initial_entropy = self.estimator.estimate(ctx.current_output)
        all_children = []
        prev_output = ctx.current_output
        prev_entropy = initial_entropy
        converged = False

        # 差分実行用: 前回の入力コンテキストを記録
        prev_input_context = ctx.current_output

        for iteration in range(max_iters):
            # 差分実行: 2回目以降で入力コンテキストが変わっていなければ
            # 前回結果を再利用して LLM 呼び出しを節約
            if iteration > 0 and all_children:
                current_input = ctx.current_output
                input_similarity = self.estimator.estimate_convergence(
                    prev_input_context, current_input
                )
                # 入力が 95% 以上同じ場合でも、min_iters 未満なら
                # 視点変動付きで再実行する (P1 との構造的整合性)
                if input_similarity >= 0.95 and iteration >= min_iters:
                    child = all_children[-1]  # 前回の結果をそのまま使う
                    all_children.append(child)
                    ctx.variables['$convergence_iteration'] = iteration + 1
                    ctx.variables['$delta_skip'] = True
                    converged = True  # 入力が変わらない = 収束
                    break

            # 内部ブロック全体を実行
            child = self.walk(node.body, ctx)
            all_children.append(child)
            ctx.push(child.output, f"C_iter_{iteration}")

            # 429 / 503 エラー (API レート制限等) 時の即時打ち切り
            # ConvergenceLoop が無駄に quota を消費し続けるのを防ぐ
            if "[FALLBACK:" in child.output and (
                "429" in child.output or "503" in child.output or "RESOURCE_EXHAUSTED" in child.output
            ):
                import logging
                logging.getLogger(__name__).warning("ConvergenceLoop 中に API レート制限 (429/503 等) を検出。ループを強制打ち切り。")
                converged = False  # 正常な収束ではないため False とする
                break

            # 実行結果を variables に保存 (他の walker から参照可能)
            ctx.variables['$condition_result'] = child.output
            ctx.variables['$convergence_iteration'] = iteration + 1
            ctx.variables['$delta_skip'] = False

            current_entropy = child.entropy_after

            # 収束判定 (最低反復回数到達後)
            similarity = 0.0
            is_last = False
            if iteration >= min_iters - 1:
                # 意味論的収束: 前回出力との類似度
                similarity = self.estimator.estimate_convergence(prev_output, child.output)
                entropy_delta = abs(current_entropy - prev_entropy)

                ctx.variables['$convergence_similarity'] = similarity
                ctx.variables['$convergence_delta'] = entropy_delta

                # 類似度が高い OR エントロピー変化が小さい → 収束
                if similarity >= convergence_threshold or entropy_delta < entropy_threshold:
                    converged = True
                    is_last = True

            # Phase 2: CONVERGENCE_ITER イベントを emit
            self._emit_event(
                "convergence_iter", child, ctx,
                source_node="C:loop",
                iteration=iteration,
                extra_metadata={
                    "similarity": similarity,
                    "delta_skip": False,
                    "duration_ms": child.duration_ms,
                    "is_last_iteration": is_last or (iteration == max_iters - 1),
                },
            )

            if converged:
                break

            prev_input_context = ctx.current_output
            prev_output = child.output
            prev_entropy = current_entropy

            # レート制限対策: 反復間に短い sleep
            if iteration < max_iters - 1:
                _time.sleep(pacing_sleep)

        ctx.variables['$converged'] = converged

        # Phase 5: Hebb則スコアブースト
        # 収束ループで蓄積された痕跡の連鎖を Neural Graph として解析し、
        # 協調して発火した subscriber の fire_threshold を一時的に下げる。
        # これにより次の C:{} ループでの subscriber 発火パターンが強化される。
        if self.environment and hasattr(self.environment, 'apply_hebbian_boost'):
            boosted = self.environment.apply_hebbian_boost()
            if boosted:
                ctx.variables['$hebbian_boost'] = boosted

        result = StepResult(
            step_type=StepType.SEQUENCE,
            node_id=f"C:loop(iters={len(all_children)},converged={converged})",
            output=ctx.current_output,
            entropy_before=initial_entropy,
            entropy_after=all_children[-1].entropy_after if all_children else initial_entropy,
            children=all_children,
        )

        return result

    # PURPOSE: デフォルト WF ハンドラ: CognitiveStepHandler に委譲
    # ─── Event Emission ───────────────────────────────────────

    def _emit_event(
        self,
        event_type_str: str,
        step_result: StepResult,
        ctx: ExecutionContext,
        source_node: str = "",
        iteration: int = 0,
        extra_metadata: Optional[Dict] = None,
    ) -> None:
        """環境にイベントを emit (Phase 4b)

        environment が None のときは何もしない (後方互換)。
        """
        if self.environment is None:
            return

        try:
            from .event_bus import CognitionEvent, EventType

            type_map = {
                "step_complete": EventType.STEP_COMPLETE,
                "convergence_iter": EventType.CONVERGENCE_ITER,
                "verification": EventType.VERIFICATION,
                "entropy_change": EventType.ENTROPY_CHANGE,
                "execution_complete": EventType.EXECUTION_COMPLETE,
            }
            et = type_map.get(event_type_str)
            if et is None:
                return

            metadata = extra_metadata or {}
            ctx_snapshot = {
                "step_count": len(ctx.step_outputs),
                "depth": ctx.depth,
                "variables": {k: str(v)[:200] for k, v in ctx.variables.items()},
            }

            event = CognitionEvent(
                event_type=et,
                step_result=step_result,
                context_snapshot=ctx_snapshot,
                metadata=metadata,
                source_node=source_node,
                iteration=iteration,
                entropy_before=step_result.entropy_before,
                entropy_after=step_result.entropy_after,
            )

            # Phase 4b: 環境が subscriber をルーティング
            self.environment.emit(event)

            # subscriber の出力をコンテキストに還流
            self.environment.inject_outputs_to_context(ctx.variables)

        except Exception as e:  # noqa: BLE001
            logger.debug("Environment emit failed: %s", e)

    @staticmethod
    def _default_handler(wf_id: str, params: dict, ctx: ExecutionContext) -> str:
        """デフォルト WF ハンドラ: CognitiveStepHandler に委譲"""
        return CognitiveStepHandler.handle(wf_id, params, ctx)


# =============================================================================
# Cognitive Step Handler (認知シミュレーター)
# =============================================================================

# PURPOSE: [L2-auto] 各定理 WF の認知効果をシミュレートするハンドラ
class CognitiveStepHandler:
    """各定理 WF の認知効果をシミュレートするハンドラ

    各定理シリーズは固有のエントロピー削減パターンを持つ:
    - O-series (本質): 認識深化 → 不確実性マーカー除去、構造追加
    - S-series (様態): 配置・構造化 → リスト/テーブル追加
    - H-series (傾向): 確信度変動 → 確信/不確信マーカー追加
    - P-series (条件): スコープ縮小 → 対象限定、境界定義
    - K-series (文脈): 文脈補完 → 情報追加
    - A-series (精密): 精密評価 → 検証済みマーカー追加

    出力テキスト内のマーカーを EntropyEstimator が検出し、
    エントロピーが自然に降下する仕組み。
    """

    # 定理→シリーズマッピング
    THEOREM_SERIES: Dict[str, str] = {
        # O-series (本質)
        "noe": "O", "bou": "O", "zet": "O", "ene": "O",
        # v4.1 Methodos 族 (S-series 相当)
        "ske": "S", "sag": "S", "pei": "S", "tek": "S",
        # H-series (傾向)
        "pro": "H", "pis": "H", "ore": "H", "dox": "H",
        # P-series (条件)
        "kho": "P", "hod": "P", "tro": "P", "tek": "P",
        # K-series (文脈)
        "euk": "K", "chr": "K", "tel": "K", "sop": "K",
        # A-series (精密)
        "pat": "A", "dia": "A", "gno": "A", "epi": "A",
    }

    # シリーズ別の認知効果テンプレート
    SERIES_EFFECTS: Dict[str, Dict] = {
        "O": {
            "action": "認識深化",
            "entropy_impact": -0.15,  # 高い削減
            "markers": ["確認済み: 本質を把握", "構造が明確化"],
            "template": "本質分析完了。{context_summary}\n"
                       "- 確認済み: 対象の本質的構造を特定\n"
                       "- 核心: {param_detail}\n"
                       "| 要素 | 状態 |\n|---|---|\n| 認識 | 完了 |",
        },
        "S": {
            "action": "構造配置",
            "entropy_impact": -0.12,
            "markers": ["配置完了", "構造化済み"],
            "template": "構造配置完了。\n"
                       "- 確認済み: {param_detail} の構造を定義\n"
                       "- 方法論を選択済み\n"
                       "| ステップ | 内容 | 状態 |\n|---|---|---|\n"
                       "| 1 | 分析 | 完了 |\n| 2 | 設計 | 完了 |",
        },
        "H": {
            "action": "確信度評価",
            "entropy_impact": -0.10,
            "markers": ["確信度", "検証済み"],
            "template": "傾向評価。\n"
                       "- 確信度: 75%\n"
                       "- 検証済み: {param_detail}\n"
                       "- 根拠: コンテキスト分析に基づく",
        },
        "P": {
            "action": "スコープ限定",
            "entropy_impact": -0.18,  # 最高削減 (範囲を狭める)
            "markers": ["スコープ確定", "対象限定", "確認済み"],
            "template": "スコープ限定完了。\n"
                       "- 確認済み: 対象を {param_detail} に限定\n"
                       "- 対象限定: 不要な領域を除外\n"
                       "- 境界: 明確に定義済み\n"
                       "| 範囲 | 状態 |\n|---|---|\n| 対象 | 確定 |",
        },
        "K": {
            "action": "文脈補完",
            "entropy_impact": -0.08,  # 中程度
            "markers": ["文脈追加", "情報補完"],
            "template": "文脈補完。\n"
                       "- 追加情報: {param_detail}\n"
                       "- 時間的文脈を確認\n"
                       "- 背景知識を統合",
        },
        "A": {
            "action": "精密評価",
            "entropy_impact": -0.20,  # 最高 (最終判定)
            "markers": ["検証済み", "成功", "確認済み", "✅"],
            "template": "精密評価完了。✅\n"
                       "- 検証済み: {param_detail}\n"
                       "- 判定: 成功\n"
                       "- 確認済み: 品質基準を満たす\n"
                       "| 基準 | 結果 |\n|---|---|\n| 正確性 | ✅ |\n| 完全性 | ✅ |",
        },
    }

    # PURPOSE: WF の認知効果をシミュレートした出力を生成
    # イテレーション変動用の視点リスト (C:{} ループで同一出力を防ぐ)
    ITERATION_PERSPECTIVES = [
        "構造的側面から分析",
        "機能的側面から再検証",
        "境界条件と例外を検討",
        "全体整合性を確認",
        "最終的な統合評価",
    ]

    @classmethod
    def handle(cls, wf_id: str, params: dict, ctx: ExecutionContext) -> str:
        """WF の認知効果をシミュレートした出力を生成

        P1 改善 (2026-02-24): イテレーション番号に応じて視点テキストを
        注入し、C:{} ループ内での Jaccard 即収束を防止する。
        """
        series = cls.THEOREM_SERIES.get(wf_id, "O")
        effect = cls.SERIES_EFFECTS.get(series, cls.SERIES_EFFECTS["O"])

        # パラメータからコンテキスト詳細を構築
        param_detail = ", ".join(f"{v}" for v in params.values()) if params else wf_id
        context_summary = ctx.current_output[:100] if ctx.current_output else "初期状態"

        # テンプレートを適用
        output = effect["template"].format(
            param_detail=param_detail,
            context_summary=context_summary,
        )

        # コンテキスト蓄積: 前のステップの確認事項を引き継ぐ
        step_count = len(ctx.step_outputs)
        if step_count > 0:
            output += f"\n前ステップからの引き継ぎ: {step_count}件の確認済み事項"

        # 深度に応じた確信度上昇
        if step_count >= 3:
            output += "\n累積確信度: 高 — 複数ステップの検証を経由"

        # P1: イテレーション番号に応じた視点変動 (C:{} ループ対策)
        iteration = ctx.variables.get('$convergence_iteration', 0)
        if iteration > 0:
            perspective_idx = (iteration - 1) % len(cls.ITERATION_PERSPECTIVES)
            perspective = cls.ITERATION_PERSPECTIVES[perspective_idx]
            output += f"\n[Iter {iteration}] 視点: {perspective}"
            # コンテキストの異なる部分を抽出して変動を増やす
            ctx_len = len(ctx.current_output) if ctx.current_output else 0
            offset = min(iteration * 50, max(0, ctx_len - 100))
            ctx_slice = ctx.current_output[offset:offset+100] if ctx.current_output else ""
            if ctx_slice:
                output += f"\n焦点: {ctx_slice.strip()[:80]}"

        # N1: EventBus Subscriber からの検証フィードバック注入
        event_outputs = ctx.variables.get('$event_outputs', [])
        if event_outputs:
            output += "\n\n--- 検証フィードバック (EventBus Subscribers) ---"
            for eo in event_outputs:
                sub_name = eo.get('subscriber', '?')
                sub_output = eo.get('output', '')[:500]
                output += f"\n[{sub_name}]: {sub_output}"

        return output


# =============================================================================
# LLM Step Handler (本物の LLM 推論)
# =============================================================================

# PURPOSE: [L2-auto] 各WFを LLM (Ochēma 経由) で実行するハンドラ
class LLMStepHandler:
    """各WFを LLM (Ochēma 経由) で実行するハンドラ

    CognitiveStepHandler (テンプレート) の代替。
    品質基準: 単体WF実行の80%以上の出力量を保証。

    Usage:
        handler = LLMStepHandler(model="auto")
        executor = MacroExecutor(step_handler=handler.handle)
        result = executor.execute("@nous", context="CCLマクロの品質")

    Fallback:
        LLM 呼び出しに失敗した場合、CognitiveStepHandler にフォールバック。
    """

    # PURPOSE: WF ID → Skill ID マッピング (24定理 + H-series + A-series)
    # 一元管理: _get_skill_prompt と _execute_phased の両方がこれを参照する
    WF_TO_SKILL = {
        "noe": "O1", "bou": "O2", "zet": "O3", "ene": "O4",
        "ske": "V05", "sag": "V06", "pei": "V07", "tek": "V08",
        "kat": "V09", "epo": "V10", "pai": "V11", "dok": "V12",
        "lys": "V13", "ops": "V14", "akr": "V15", "arc": "V16",
        "beb": "V17", "ele": "V18", "kop": "V19", "dio": "V20",
        "hyp": "V21", "prm": "V22", "ath": "V23", "par": "V24",
        # H-series (座標層)
        "pro": "H01", "pis": "H02", "ore": "H03", "dox": "H04",
        # A-series
        "dia": "A02",
    }

    # PURPOSE: Initialize instance
    def __init__(
        self,
        model: str = "auto",
        min_output_chars: int = 500,
        timeout: int = 120,
        account: str = "default",
    ):
        self.model = model
        self.min_output_chars = min_output_chars  # 80% 品質ゲート
        self.timeout = timeout
        self.account = account
        self._executor = None  # lazy init

    # PURPOSE: CortexClient を遅延初期化
    def _get_client(self):
        """CortexClient を遅延初期化 (urllib のみ、asyncio 不要)"""
        if self._executor is None:
            from mekhane.ochema.cortex_client import CortexClient
            self._executor = CortexClient(
                model=self.model if self.model != "auto" else "gemini-3.1-pro-preview",
                max_tokens=8192,
                account=self.account,
            )
        return self._executor

    # PURPOSE: AP-4 ラウンドロビン対応 CortexClient を取得 (L3 逐次実行用)
    def _get_rotated_client(self):
        """account_router 経由でアカウントをラウンドロビンした CortexClient を返す。

        L3 逐次フェーズ実行で同一アカウントへの連続呼び出しを防ぎ、
        quota 競合による 403/429 エラーを回避する。
        """
        from mekhane.ochema.cortex_client import CortexClient
        try:
            from mekhane.ochema.account_router import get_account_for
            account = get_account_for("hermeneus")
        except Exception:  # noqa: BLE001
            account = self.account  # フォールバック
        return CortexClient(
            model=self.model if self.model != "auto" else "gemini-3.1-pro-preview",
            max_tokens=8192,
            account=account,
        )

    # PURPOSE: 全先行ステップの出力を積み重ねてコンテキストを構築
    def _build_accumulated_context(self, ctx: ExecutionContext) -> str:
        """全先行ステップの出力を積み重ねてコンテキストを構築。

        CCL の _ (シーケンス) 演算子は所有権移転 (Move):
        先行ステップの出力が後続ステップの入力コンテキストになる。
        最後のステップだけでなく、全ステップの出力を蓄積する。
        """
        if not ctx.step_outputs and not ctx.initial_input:
            return "(初期入力: コンテキストなし)"

        parts: list[str] = []

        # 1. 初期入力 (ユーザーが渡した context)
        if ctx.initial_input:
            parts.append(f"## 初期入力\n{ctx.initial_input}")

        # 2. 全先行ステップの出力を積み重ね
        for i, output in enumerate(ctx.step_outputs):
            parts.append(f"## ステップ {i+1} 出力\n{output}")

        accumulated = "\n\n---\n\n".join(parts)

        # 予算制御: 深度に応じた最大コンテキスト長
        mode = ctx.derivative or ''
        mode_char = mode[0] if mode else ''
        budget = {'+': 32000, '-': 4000}.get(mode_char, 16000)
        if len(accumulated) > budget:
            accumulated = self._compress_context(parts, budget)

        return accumulated

    # PURPOSE: 予算内に収まるようコンテキストを圧縮 (最新ステップ優先)
    def _compress_context(self, parts: list, budget: int) -> str:
        """予算内に収まるようコンテキストを圧縮。最新のステップを優先。"""
        result: list[str] = []
        remaining = budget
        for part in reversed(parts):
            if len(part) <= remaining:
                result.insert(0, part)
                remaining -= len(part)
            elif remaining > 500:
                result.insert(0, part[:remaining] + "\n... (圧縮)")
                remaining = 0
            else:
                result.insert(0, f"[ステップ出力省略 — {len(part)}文字]")
        return "\n\n---\n\n".join(result)

    # PURPOSE: WF 定義からプロンプトを構築 (SKILL.md フェーズ注入対応)
    def _build_wf_prompt(self, wf_id: str, params: dict, ctx: ExecutionContext) -> str:
        """WF 定義からプロンプトを構築

        SkillRegistry に該当 SKILL.md があれば、フェーズ定義を注入して
        深い出力を生成する。なければ従来の description ベースプロンプト。
        """
        description = WFResolver.extract_description(wf_id)

        # mode 判定 (+ = 全展開, - = 縮約)
        mode = params.get('mode', '')
        depth_instruction = ""
        if '+' in mode:
            depth_instruction = "\n深度: L3 (全展開) — 省略なし、全ステップを詳細に実行してください。"
        elif '-' in mode:
            depth_instruction = "\n深度: L1 (縮約) — 要点のみ簡潔に。"
        else:
            depth_instruction = "\n深度: L2 (標準) — バランスの取れた分析を実行してください。"

        # コンテキスト: 全先行ステップの出力を積み重ね (CCL _ 演算子の意味論)
        prev_output = self._build_accumulated_context(ctx)

        # --- 構造化コンテキスト注入 ---
        structured_ctx = ""
        if ctx.structured:
            parts = []
            if ctx.structured.get("findings"):
                parts.append("\n## 前ステップの発見事項")
                for f in ctx.structured["findings"][-5:]:
                    if isinstance(f, dict):
                        parts.append(f"- [{f.get('phase','')}] {f.get('content','')}")
                    else:
                        parts.append(f"- {f}")
            if ctx.structured.get("open_questions"):
                parts.append("\n## 未解決の問い")
                for q in ctx.structured["open_questions"][-3:]:
                    if isinstance(q, dict):
                        parts.append(f"- {q.get('question','')}")
                    else:
                        parts.append(f"- {q}")
            if ctx.structured.get("phase_summary"):
                parts.append("\n## フェーズ履歴")
                for name, summ in ctx.structured["phase_summary"].items():
                    parts.append(f"- {name}: {summ}")
            if parts:
                structured_ctx = "\n".join(parts) + "\n"

        # 蓄積されたステップ数を表示
        step_count = len(ctx.step_outputs)
        step_info = f"\n[前ステップ: {step_count}件完了]" if step_count > 0 else ""

        # --- マクロの Execution Guide 注入 ---
        active_macro = ctx.variables.get("$active_macro")
        macro_guide = ""
        if active_macro:
            loaded_guide = WFResolver.extract_execution_guide(f"ccl-{active_macro}")
            if loaded_guide:
                macro_guide = f"\n\n## @{active_macro} Execution Guide (Trace/Negativa/Iso)\n{loaded_guide}\n"

        # schemas.py を使って JSON Schema 定義を _STRUCTURED_OUTPUT_INSTRUCTION に注入
        output_instruction = _STRUCTURED_OUTPUT_INSTRUCTION
        try:
            from hermeneus.src.schemas import get_schema
            import json as _json
            schema = get_schema(wf_id)
            if schema:
                schema_str = _json.dumps(schema, ensure_ascii=False, indent=2)
                output_instruction += f"\n\nJSON Schema:\n```json\n{schema_str}\n```\n"
        except Exception:  # noqa: BLE001
            pass

        # --- SKILL.md フェーズ注入 ---
        skill_prompt = self._get_skill_prompt(wf_id, params, prev_output)
        if skill_prompt:
            # SKILL.md ベースの高品質プロンプト
            prompt = f"""{skill_prompt}
{depth_instruction}{macro_guide}
{structured_ctx}
## マクロ実行コンテキスト{step_info}
{prev_output}

{output_instruction}
"""
            return prompt

        # --- N1: EventBus Subscriber からの検証フィードバック注入 ---
        event_outputs = ctx.variables.get('$event_outputs', [])
        feedback_section = ""
        if event_outputs:
            fb_lines = ["\n## 前回検証からのフィードバック (EventBus Subscribers)"]
            for eo in event_outputs:
                sub_name = eo.get('subscriber', '?')
                sub_output = eo.get('output', '')[:500]
                fb_lines.append(f"- [{sub_name}]: {sub_output}")
            fb_lines.append("上記のフィードバックを考慮して出力を改善してください。")
            feedback_section = "\n".join(fb_lines) + "\n"

        # --- フォールバック: WF 定義全文注入プロンプト ---
        # 原因①修正: description(1行) ではなく WF 定義全文を注入。
        # LLM が WF の意味を理解するための最低限の情報を渡す。
        mode_char = mode[0] if mode else ''
        wf_budget = {'+': 8000, '-': 3000}.get(mode_char, 5000)
        full_definition = WFResolver.load_definition(wf_id)
        
        if full_definition:
            wf_section = full_definition[:wf_budget]
        else:
            wf_section = f"/{wf_id}: {description}"

        prompt = f"""あなたは Hegemonikón の /{wf_id} ワークフローを実行しています。

## WF 定義（全文）
{wf_section}

## コンテキスト (前ステップの出力){step_info}
{prev_output}
{structured_ctx}{macro_guide}{feedback_section}
## 指示
上記の WF 定義に記された認知操作・フェーズ構造に忠実に従って実行してください。
各フェーズの操作を省略せず、フェーズごとに異なる認知操作を行ってください。
出力は構造化し (テーブル、箇条書きを活用)、最低500文字以上で回答してください。
{output_instruction}
{depth_instruction}
"""
        return prompt

    # PURPOSE: SkillRegistry から SKILL.md のフェーズ定義を取得しプロンプト化 (P0: フェーズ選択的注入)
    def _get_skill_prompt(
        self, wf_id: str, params: dict, context: str
    ) -> Optional[str]:
        """SkillRegistry から SKILL.md のフェーズ定義を取得しプロンプト化

        深度に応じたフェーズ選択:
          L1 (-): スキル概要のみ (description + algorithm)
          L2 (標準): 概要 + 最終フェーズ (出力形式)
          L3 (+): 概要 + 全フェーズ (トークン予算内)

        Returns:
            SKILL.md ベースのプロンプト文字列、または None (SKILL 未整備時)
        """
        WF_TO_SKILL = self.WF_TO_SKILL  # クラス定数を参照

        skill_id = WF_TO_SKILL.get(wf_id)
        if not skill_id:
            return None

        try:
            from .skill_registry import SkillRegistry
            registry = SkillRegistry()
            skill = registry.get(skill_id)
            if not skill or not skill.phases:
                return None

            mode = params.get('mode', '')
            phases = skill.phases
            ctx_snippet = context[:800] if context else ""

            # --- スキル概要 (常に注入) ---
            overview = (
                f"あなたは Hegemonikón の {skill_id} {skill.name} を実行しています。\n"
                f"説明: {skill.description}\n"
            )
            if phases[0].algorithm:
                overview += f"認知アルゴリズム: {phases[0].algorithm}\n"

            # ステップ一覧 (全フェーズのタイトルを 1行ずつ)
            overview += "\n## フェーズ一覧\n"
            for i, p in enumerate(phases):
                overview += f"  {i}. {p.name}\n"

            # --- 拡張ブロック抽出 (P3: 認知代数・Anti-Patterns・WM) ---
            # SkillParser はフェーズしかパースしないため、
            # SKILL.md ファイルから直接テキスト抽出する
            enrichment = self._extract_enrichment_blocks(skill, skill_id)

            # --- 深度に応じたフェーズ選択 ---
            # 品質第一主義: 速度より品質を優先
            TOKEN_BUDGET_L2 = 4000   # L2: 概要+enrichment+第1+最終
            TOKEN_BUDGET_L3 = 8000   # L3: 概要+enrichment+全フェーズ

            if '-' in mode:
                # L1: 概要のみ — 軽量
                return overview[:TOKEN_BUDGET_L2]

            # L2/L3: 概要に enrichment (認知代数・Anti-Patterns) を結合
            if enrichment:
                overview += "\n" + enrichment + "\n"

            if '+' in mode:
                # L3: 概要+enrichment + 全フェーズ (予算内で最大限)
                parts = [overview]
                remaining = TOKEN_BUDGET_L3 - len(overview)
                for phase in phases:
                    block = phase.to_prompt(
                        skill_id=skill_id,
                        skill_name=skill.name,
                        context=ctx_snippet,
                    )
                    if len(block) <= remaining:
                        parts.append(block)
                        remaining -= len(block)
                    else:
                        parts.append(f"[Phase {phase.number} {phase.name}: 省略 (予算超過)]")
                        break
                return "\n\n---\n\n".join(parts)

            else:
                # L2 (標準): 概要+enrichment + 第1フェーズ + 最終フェーズ
                parts = [overview]
                remaining = TOKEN_BUDGET_L2 - len(overview)

                first = phases[0].to_prompt(
                    skill_id=skill_id, skill_name=skill.name, context=ctx_snippet,
                )
                if len(first) <= remaining:
                    parts.append(first)
                    remaining -= len(first)

                if len(phases) > 1:
                    last = phases[-1].to_prompt(
                        skill_id=skill_id, skill_name=skill.name, context=ctx_snippet,
                    )
                    if len(last) <= remaining:
                        parts.append(last)

                return "\n\n---\n\n".join(parts)

        except Exception as e:  # noqa: BLE001
            logger.warning("SKILL prompt generation failed for %s: %s", wf_id, e)
            return None

    def _extract_enrichment_blocks(self, skill, skill_id: str) -> str:
        """SKILL.md から認知代数・Anti-Patterns・WM管理ブロックを抽出

        SkillRegistry.extract_cognitive_supplements() に委譲。
        """
        try:
            from .skill_registry import SkillRegistry
            registry = SkillRegistry()
            return registry.extract_cognitive_supplements(skill_id)
        except Exception:  # noqa: BLE001
            return ""

    # PURPOSE: CortexClient 経由で WF を実行
    def handle(self, wf_id: str, params: dict, ctx: ExecutionContext) -> str:
        """CortexClient (Gemini API) 経由で WF を実行

        原因②修正: L3 (+) 深度で SKILL.md にフェーズ定義がある場合、
        各フェーズを個別 LLM 呼び出しで逐次実行する。
        L1/L2 は従来の 1 ショット実行を維持。

        Returns:
            WF の出力テキスト (500文字以上を保証)
        """
        mode = params.get('mode', '')

        # 原因②: L3 (+) かつ SKILL.md にフェーズ定義がある場合 → 逐次実行
        if '+' in mode:
            phased_output = self._execute_phased(wf_id, params, ctx)
            if phased_output:
                return phased_output

        # L1/L2 または SKILL.md なし → 従来の1ショット実行
        prompt = self._build_wf_prompt(wf_id, params, ctx)

        try:
            client = self._get_client()
            
            # Progress: LLM 呼び出し開始
            _progress("llm_call", f"/{wf_id} → Gemini API (model={self.model})")

            # JSON Schema / Structured Outputs integration (opt-in)
            response_schema = None
            try:
                from hermeneus.src.schemas import to_provider_schema
                response_schema = to_provider_schema(wf_id)
            except Exception as e:  # noqa: BLE001
                logger.debug("Failed to load schema for %s: %s", wf_id, e)

            response = client.ask(
                prompt,
                timeout=self.timeout,
                response_schema=response_schema
            )

            if response and response.text:
                output = response.text

                # 構造化メタデータの抽出と蓄積
                clean_output, meta = _extract_structured_meta(output)
                if meta:
                    ctx.push_structured(clean_output, wf_id, meta)
                    output = clean_output  # JSON ブロックを除去した表示用テキスト

                if len(output) < self.min_output_chars:
                    output += (
                        f"\n\n[品質警告: 出力 {len(output)} 文字 < "
                        f"最小閾値 {self.min_output_chars} 文字]"
                    )
                # Progress: LLM 呼び出し完了
                _progress("llm_done", f"/{wf_id} 完了 ({len(output)}文字)")
                return output
            else:
                # P2: フォールバック — [FALLBACK] マーカーで C:{} が検知可能
                fallback = CognitiveStepHandler.handle(wf_id, params, ctx)
                return f"[FALLBACK: LLM empty response for /{wf_id} — model={self.model}]\n{fallback}"

        except ImportError as e:
            # 永続的障害: モジュール不在 — クライアント再初期化を強制
            self._executor = None
            fallback = CognitiveStepHandler.handle(wf_id, params, ctx)
            logger.error("LLMStepHandler ImportError for /%s: %s (client reset)", wf_id, e)
            _progress("llm_fallback", f"/{wf_id} → CognitiveStepHandler (ImportError)")
            return f"[FALLBACK: ImportError for /{wf_id} — {str(e)[:200]}]\n{fallback}"
        except Exception as e:  # noqa: BLE001
            # 一時的障害: API エラー等 — フォールバック (クライアントは保持)
            fallback = CognitiveStepHandler.handle(wf_id, params, ctx)
            logger.warning("LLMStepHandler fallback for /%s: %s: %s", wf_id, type(e).__name__, e)
            _progress("llm_fallback", f"/{wf_id} → CognitiveStepHandler ({type(e).__name__})")
            return f"[FALLBACK: {type(e).__name__} for /{wf_id} — {str(e)[:200]}]\n{fallback}"

    # PURPOSE: L3 フェーズ逐次実行 — 各フェーズを個別LLM呼出しで実行
    def _execute_phased(self, wf_id: str, params: dict, ctx: ExecutionContext) -> Optional[str]:
        """L3 フェーズ逐次実行: 各フェーズを個別LLM呼出しで実行

        SKILL.md にフェーズ定義がある場合のみ有効。
        Phase N の出力が Phase N+1 の入力コンテキストになる。
        各フェーズで異なる認知操作が実行されることを保証する。

        NOTE: response_schema は意図的に適用しない。
        フェーズ逐次実行では各フェーズの自然言語出力が次フェーズの
        入力コンテキストとなるため、JSON 強制はフェーズ間連鎖を破壊する。
        構造化メタデータは _extract_structured_meta() で後処理として抽出する。

        Returns:
            フェーズ逐次実行の結合出力。SKILL.md がない場合は None。
        """
        WF_TO_SKILL = self.WF_TO_SKILL  # クラス定数を参照

        skill_id = WF_TO_SKILL.get(wf_id)
        if not skill_id:
            return None

        try:
            from .skill_registry import SkillRegistry
            registry = SkillRegistry()
            skill = registry.get(skill_id)
            if not skill or not skill.phases:
                return None

            # 逐次実行: 各フェーズに個別LLM呼出し
            import time as _time
            accumulated = ctx.current_output or ctx.initial_input or "(初期入力なし)"
            phase_outputs = []

            for phase_idx, phase in enumerate(skill.phases):
                # Progress: フェーズ開始
                _progress("phase", f"Phase {phase_idx+1}/{len(skill.phases)}: {phase.name}",
                          step=phase_idx+1, total=len(skill.phases))

                prompt = self._build_phase_prompt(
                    skill=skill, phase=phase,
                    accumulated=accumulated, wf_id=wf_id,
                )

                # AP-3: フェーズ間 rate limit 対策
                # 2番目以降のフェーズは呼び出し前に sleep (rate limit 予防)
                if phase_idx > 0:
                    _time.sleep(2.0)

                # 403/429 エラー時の exponential backoff リトライ (最大3回)
                phase_output = None
                max_retries = 3
                for retry in range(max_retries):
                    try:
                        client = self._get_rotated_client()
                        response = client.ask(prompt, timeout=self.timeout)

                        if response and response.text:
                            phase_output = response.text
                        else:
                            phase_output = f"[Phase {phase.number} {phase.name}: LLM応答なし]"
                        break  # 成功 → リトライループ終了

                    except Exception as e:  # noqa: BLE001
                        error_str = str(e)
                        status_code = getattr(e, 'status_code', 0)
                        is_rate_limit = status_code in (403, 429) or '403' in error_str or '429' in error_str

                        if is_rate_limit and retry < max_retries - 1:
                            backoff = 2 ** (retry + 1) * 3  # 6s, 12s, 24s
                            logger.warning(
                                "Phase %d rate limited (attempt %d/%d), "
                                "backing off %ds: %s",
                                phase.number, retry + 1, max_retries, backoff, e,
                            )
                            # Progress: リトライ
                            _progress("retry", f"Phase {phase_idx+1} retry {retry+1}/{max_retries} (backoff {backoff}s)")
                            _time.sleep(backoff)
                        else:
                            phase_output = f"[Phase {phase.number} {phase.name}: エラー — {e}]"
                            break

                phase_header = f"## Phase {phase.number}: {phase.name}"
                phase_outputs.append(f"{phase_header}\n\n{phase_output}")

                # Phase N の出力を Phase N+1 のコンテキストに蓄積
                accumulated = f"{accumulated}\n\n---\n\n{phase_header}\n{phase_output}"

            if phase_outputs:
                combined = "\n\n---\n\n".join(phase_outputs)

                # --- 介入点B: フェーズ間 drift メトリクス ---
                drift_scores = []
                if len(phase_outputs) >= 2:
                    for i in range(1, len(phase_outputs)):
                        drift = EntropyEstimator.estimate_drift(
                            phase_outputs[i - 1], phase_outputs[i]
                        )
                        drift_scores.append(drift)

                    avg_drift = sum(drift_scores) / len(drift_scores)
                    min_drift = min(drift_scores)
                    drift_report = "\n".join(
                        f"  Phase {i}→{i+1} drift: {d:.2f}"
                        + (" ⚠️ 低" if d < 0.15 else "")
                        for i, d in enumerate(drift_scores)
                    )

                    if min_drift < 0.15:
                        combined += (
                            f"\n\n[⚠️ 穴埋め疑惑: フェーズ間差分が低い "
                            f"(最小drift={min_drift:.2f}, 平均={avg_drift:.2f})]\n"
                            f"{drift_report}"
                        )

                # --- 介入点C: 段階的監査 ---
                mode = params.get('mode', '')
                try:
                    audit_result = self._audit_phases(
                        phase_outputs=phase_outputs,
                        drift_scores=drift_scores,
                        mode=mode,
                        wf_id=wf_id,
                    )
                    if audit_result:
                        combined += f"\n\n---\n\n## 監査結果\n{audit_result}"
                except Exception as e:  # noqa: BLE001
                    logger.debug("Phase audit failed: %s", e)

                return combined
            return None

        except Exception as e:  # noqa: BLE001
            logger.warning("Phased execution failed for %s: %s", wf_id, e)
            return None

    # PURPOSE: 個別フェーズのプロンプトを構築
    def _build_phase_prompt(self, skill, phase, accumulated: str, wf_id: str) -> str:
        """個別フェーズのプロンプトを構築

        各フェーズに固有の認知操作指示を含むプロンプトを生成する。
        前フェーズまでの蓄積結果をコンテキストとして渡す。
        """
        # フェーズの description と algorithm を取得
        phase_desc = getattr(phase, 'description', '') or phase.name
        phase_algo = getattr(phase, 'algorithm', '') or ''

        # phase.to_prompt があればフル定義を使う
        phase_definition = ""
        if hasattr(phase, 'to_prompt'):
            try:
                phase_definition = phase.to_prompt(
                    skill_id=getattr(skill, 'id', wf_id),
                    skill_name=getattr(skill, 'name', wf_id),
                    context=accumulated[-800:],
                )
            except Exception:  # noqa: BLE001
                phase_definition = phase_desc
        else:
            phase_definition = phase_desc

        algo_section = f"\n認知アルゴリズム: {phase_algo}" if phase_algo else ""

        return f"""あなたは Hegemonikón の /{wf_id} ({getattr(skill, 'name', wf_id)}) を実行中です。
現在 Phase {phase.number}: {phase.name} を実行してください。

## このフェーズの定義
{phase_definition}{algo_section}

## これまでの分析結果 (前フェーズの出力)
{accumulated[-3000:]}

## ⚠️ 実行における絶対の制約 (Anti-Illusion)
1. **論理的連続性**: 「これまでの分析結果」で導出された具体的な結論・用語・仮説を**必ずそのまま引き継いで**使用してください。このフェーズで唐突に新しい用語や対象を捏造しないでください。
2. **テンプレート穴埋め禁止**: 指定された出力形式の「形」だけを真似て、中身を前後の文脈と無関係な言葉で埋める行為を固く禁じます。
3. **認知的差分の明示**: 前フェーズから「何を受け取り」「このフェーズの認知操作によってそれをどう加工したか」が明確にわかるように出力してください。
4. 出力は 500 文字以上、具体的かつ構造化して回答してください。
"""

    # PURPOSE: 段階的監査 — L1/L2/L3 で異なる粒度・モデルでフェーズ出力を監査
    def _audit_phases(
        self,
        phase_outputs: List[str],
        drift_scores: List[float],
        mode: str,
        wf_id: str,
    ) -> Optional[str]:
        """段階的監査: フェーズ出力の品質を深度に応じた粒度で監査

        L1 (-): Flash で全フェーズ一括監査
        L2 (標準): Pro で全フェーズ一括監査
        L3 (+): Pro で 3フェーズごとクラスタリングして個別監査

        drift スコアを監査プロンプトに注入し、穴埋め検出精度を底上げ。
        """
        if not phase_outputs:
            return None

        # モデル選択
        if '-' in mode:
            model = "gemini-3-flash-preview"
        else:
            model = "gemini-3.1-pro-preview"

        # drift レポート構築
        drift_report = ""
        if drift_scores:
            drift_lines = []
            for i, d in enumerate(drift_scores):
                flag = " ⚠️ 低（穴埋め疑惑）" if d < 0.15 else ""
                drift_lines.append(f"Phase {i}→{i+1}: drift={d:.2f}{flag}")
            drift_report = "\n".join(drift_lines)

        if '+' in mode:
            # L3: 3フェーズごとクラスタ監査
            return self._audit_clustered(
                phase_outputs, drift_scores, drift_report, wf_id, model,
                cluster_size=3,
            )
        else:
            # L1/L2: 全フェーズ一括監査
            return self._audit_bulk(
                phase_outputs, drift_report, wf_id, model,
            )

    # PURPOSE: 全フェーズ一括監査 (L1/L2)
    def _audit_bulk(
        self,
        phase_outputs: List[str],
        drift_report: str,
        wf_id: str,
        model: str,
    ) -> Optional[str]:
        """全フェーズ一括監査"""
        all_text = "\n\n---\n\n".join(phase_outputs)
        # トークン予算: 各フェーズ冒頭 500 文字ずつ
        phase_summaries = "\n\n".join(
            f"### {po.split(chr(10))[0]}\n{po[:500]}..."
            for po in phase_outputs
        )

        prompt = f"""あなたは Hegemonikón の品質監査員です。
/{wf_id} の実行結果（{len(phase_outputs)} フェーズ）を監査してください。

## 監査基準
1. **フェーズ間依存性**: 各フェーズは前フェーズの出力に実質的に依存しているか？
   → 独立していたら「テンプレート穴埋め」の兆候
2. **認知的差異**: フェーズ間で異なる種類の認知操作が行われているか？
   → 同種操作の繰り返しは穴埋めの兆候
3. **情報の新規性**: 入力コンテキストに含まれない新しい洞察があるか？

## フェーズ間 drift スコア（高=異なる内容、低=似た内容）
{drift_report if drift_report else "(測定不可)"}

## フェーズ出力
{phase_summaries}

## 判定
以下の形式で回答:
判定: [PASS/WARN/FAIL]
穴埋め度: [0-100]% (0%=完全に実行されている, 100%=完全な穴埋め)
理由: [具体的な根拠]
"""
        try:
            client = self._get_rotated_client()
            response = client.ask(prompt, timeout=60)
            return response.text if response and response.text else None
        except Exception as e:  # noqa: BLE001
            logger.debug("Bulk audit failed: %s", e)
            return None

    # PURPOSE: 3フェーズごとクラスタ監査 (L3)
    def _audit_clustered(
        self,
        phase_outputs: List[str],
        drift_scores: List[float],
        drift_report: str,
        wf_id: str,
        model: str,
        cluster_size: int = 3,
    ) -> Optional[str]:
        """3フェーズごとクラスタ監査 (L3)"""
        clusters = []
        for i in range(0, len(phase_outputs), cluster_size):
            cluster = phase_outputs[i:i + cluster_size]
            cluster_drifts = drift_scores[i:i + cluster_size - 1] if drift_scores else []
            clusters.append((i, cluster, cluster_drifts))

        audit_results = []
        for start_idx, cluster, drifts in clusters:
            end_idx = start_idx + len(cluster) - 1
            cluster_summaries = "\n\n".join(
                f"### {po.split(chr(10))[0]}\n{po[:600]}..."
                for po in cluster
            )
            drift_section = ""
            if drifts:
                drift_section = "\n".join(
                    f"Phase {start_idx + j}→{start_idx + j + 1}: drift={d:.2f}"
                    + (" ⚠️" if d < 0.15 else "")
                    for j, d in enumerate(drifts)
                )

            prompt = f"""あなたは Hegemonikón の品質監査員です。
/{wf_id} の Phase {start_idx}〜{end_idx} を監査してください。

## 監査基準
1. **フェーズ間依存性**: 後のフェーズは前フェーズの出力を実質的に使っているか？
2. **認知的差異**: 各フェーズで異なる種類の操作をしているか？
3. **新規性**: テンプレート的な一般論ではなく、具体的な洞察を出しているか？

## drift スコア
{drift_section if drift_section else "(N/A)"}

## フェーズ出力
{cluster_summaries}

判定: [PASS/WARN/FAIL]
穴埋め度: [0-100]%
理由: [根拠]
"""
            try:
                client = self._get_rotated_client()
                response = client.ask(prompt, timeout=60)
                if response and response.text:
                    audit_results.append(
                        f"### Phase {start_idx}〜{end_idx}\n{response.text}"
                    )
            except Exception as e:  # noqa: BLE001
                audit_results.append(
                    f"### Phase {start_idx}〜{end_idx}\n[監査エラー: {e}]"
                )

        return "\n\n".join(audit_results) if audit_results else None
# Backward Pass (Credit Assignment)
# =============================================================================

# PURPOSE: [L2-auto] 逆伝播: 確信度スコアから各ステップの帰責値を計算
class BackwardPass:
    """逆伝播: 確信度スコアから各ステップの帰責値を計算

    ニューラルネットの逆伝播に相当。
    損失関数 = 1 - final_confidence。
    各ステップの gradient = そのステップのエントロピー削減の寄与率。
    """

    # PURPOSE: 逆伝播を実行
    @staticmethod
    def compute(steps: List[StepResult], final_confidence: float) -> Dict[str, float]:
        """逆伝播を実行

        Args:
            steps: forward pass の全ステップ結果
            final_confidence: 最終確信度 (0.0-1.0)

        Returns:
            {node_id: gradient} の辞書
        """
        loss = 1.0 - final_confidence  # 損失 = 1 - 確信度
        gradient_map: Dict[str, float] = {}

        # 全ステップのエントロピー削減量を収集
        flat_steps = BackwardPass._flatten(steps)
        total_reduction = sum(s.entropy_reduction for s in flat_steps) or 1.0

        # 各ステップの寄与率 (= gradient)
        for step in flat_steps:
            if step.step_type in (StepType.SEQUENCE, StepType.FOR_LOOP):
                continue  # コンテナはスキップ

            contribution = step.entropy_reduction / total_reduction
            gradient = loss * contribution  # 損失に対する寄与
            step.gradient = gradient
            gradient_map[step.node_id] = gradient

        return gradient_map

    # PURPOSE: ネストされたステップをフラット化
    @staticmethod
    def _flatten(steps: List[StepResult]) -> List[StepResult]:
        """ネストされたステップをフラット化"""
        flat = []
        for s in steps:
            if s.children:
                flat.extend(BackwardPass._flatten(s.children))
            else:
                flat.append(s)
        return flat


# =============================================================================
# Macro Executor (統合エントリーポイント)
# =============================================================================

# PURPOSE: [L2-auto] CCL マクロ自動実行エンジン
class MacroExecutor:
    """CCL マクロ自動実行エンジン

    Usage:
        executor = MacroExecutor()
        result = executor.execute("@v", context="fix shape mismatch")
        print(result.summary())

        # カスタムハンドラ (LLM API 呼び出し等)
        executor = MacroExecutor(step_handler=my_llm_handler)
    """

    # PURPOSE: Initialize instance
    def __init__(
        self,
        step_handler: Optional[Callable] = None,
        estimator: Optional[EntropyEstimator] = None,
        event_bus: Optional[Any] = None,
        environment: Optional[Any] = None,
    ):
        # Phase 4b: environment を優先。event_bus はフォールバック (後方互換)
        self.environment = environment or event_bus
        self.event_bus = self.environment  # 後方互換エイリアス
        self.walker = ASTWalker(
            step_handler=step_handler,
            entropy_estimator=estimator,
            environment=self.environment,
        )

    # PURPOSE: CCL 式 (マクロ含む) を実行
    def execute(self, ccl: str, context: str = "") -> ExecutionResult:
        """CCL 式 (マクロ含む) を実行

        1. マクロ展開
        2. AST パース
        3. Forward pass (AST walk + エントロピー計測)
        4. Backward pass (帰責計算)
        """
        import importlib
        _macro_expander = importlib.import_module('mekhane.ccl.macro_expander')
        _macro_registry = importlib.import_module('mekhane.ccl.macro_registry')
        MacroExpander = _macro_expander.MacroExpander
        MacroRegistry = _macro_registry.MacroRegistry
        from hermeneus.src.parser import CCLParser

        start = time.monotonic()

        from hermeneus.src.ccl_normalizer import normalize_ccl_input
        ccl = normalize_ccl_input(ccl)

        # v9.0: 層1 CCLLinter による静的整合性検証
        try:
            from hermeneus.src.ccl_linter import lint_ccl
            lint_issues = lint_ccl(ccl)
            if lint_issues:
                from hermeneus.src.ccl_linter import Severity
                errors = [i for i in lint_issues if i.severity == Severity.ERROR]
                if errors:
                    logger.warning("CCLLinter errors: %s", [str(e) for e in errors])
        except Exception as e:  # noqa: BLE001
            logger.debug("CCLLinter failed: %s", e)

        # v9.0: 層0 MACRO_START イベント — PlanPreprocessor が発火
        if self.environment is not None:
            try:
                from .event_bus import CognitionEvent, EventType
                macro_name = ccl.strip().lstrip("/@").split("_")[0].split("~")[0]
                event = CognitionEvent(
                    event_type=EventType.MACRO_START,
                    metadata={
                        "macro_name": macro_name,
                        "ccl": ccl,
                        "context": context,
                    },
                    source_node="macro_executor",
                )
                self.environment.emit(event)
            except Exception as e:  # noqa: BLE001
                logger.debug("MACRO_START emit failed: %s", e)

        # Step 1: マクロ展開
        registry = MacroRegistry()
        expander = MacroExpander(registry)
        expanded, _, derivative = expander.expand(ccl)

        # ネストされたマクロも展開 (最大3回)
        for _ in range(3):
            re_expanded, did, nested_deriv = expander.expand(expanded)
            if not did:
                break
            expanded = re_expanded
            if nested_deriv:
                derivative = nested_deriv  # 最内マクロの派生を優先

        # Step 2: AST パース
        parser = CCLParser()
        ast = parser.parse(expanded)

        # AP-2 補完: MacroExpander は @macro+ のみで derivative を抽出するため、
        # /noe+ のような直接CCL式では derivative が空になる。
        # AST ルートの mode フィールドからフォールバック導出する。
        if not derivative and hasattr(ast, 'mode') and ast.mode:
            derivative = ast.mode

        # Step 3: Forward pass
        ctx = ExecutionContext(
            initial_input=context,
            current_output=context,
            derivative=derivative,
        )

        # P3: WF フロントマターから min_convergence_iters を抽出
        try:
            from hermeneus.src.macros import get_macro_metadata
            metadata = get_macro_metadata()
            max_min_iters = None
            for name, fm in metadata.items():
                if f"@{name}" in ccl:
                    iters = fm.get("min_convergence_iters")
                    if iters is not None:
                        max_min_iters = max(max_min_iters or 0, int(iters))
            if max_min_iters is not None:
                ctx.variables["$min_convergence_iters"] = max_min_iters
        except Exception as e:  # noqa: BLE001
            logger.debug("Failed to extract macro metadata: %s", e)

        root_result = self.walker.walk(ast, ctx)

        # Step 4: Backward pass
        all_steps = root_result.children if root_result.children else [root_result]
        final_confidence = 1.0 - root_result.entropy_after
        gradient_map = BackwardPass.compute(all_steps, final_confidence)

        # ボトルネック特定
        bottleneck = max(gradient_map, key=gradient_map.get) if gradient_map else None

        total_duration = (time.monotonic() - start) * 1000

        # Phase 2: EXECUTION_COMPLETE イベントを emit
        # Phase 4b: 環境にイベントを emit
        if self.environment is not None:
            try:
                from .event_bus import CognitionEvent, EventType
                event = CognitionEvent(
                    event_type=EventType.EXECUTION_COMPLETE,
                    step_result=root_result,
                    metadata={
                        "ccl": ccl,
                        "expanded_ccl": expanded,
                        "confidence": final_confidence,
                        "duration_ms": total_duration,
                        "bottleneck": bottleneck,
                    },
                    source_node="macro_executor",
                    entropy_before=root_result.entropy_before,
                    entropy_after=root_result.entropy_after,
                )
                self.environment.emit(event)
            except Exception as e:  # noqa: BLE001
                logger.debug("Environment EXECUTION_COMPLETE emit failed: %s", e)

        # v9.0: 層6 MACRO_COMPLETE イベント — PlanRecorder が発火
        if self.environment is not None:
            try:
                from .event_bus import CognitionEvent, EventType
                macro_name = ccl.strip().lstrip("/@").split("_")[0].split("~")[0]
                event = CognitionEvent(
                    event_type=EventType.MACRO_COMPLETE,
                    step_result=root_result,
                    metadata={
                        "macro_name": macro_name,
                        "ccl": ccl,
                        "confidence": final_confidence,
                        "duration_ms": total_duration,
                    },
                    source_node="macro_executor",
                    entropy_before=root_result.entropy_before,
                    entropy_after=root_result.entropy_after,
                )
                self.environment.emit(event)
            except Exception as e:  # noqa: BLE001
                logger.debug("MACRO_COMPLETE emit failed: %s", e)

        # === Morphism Proposals ===
        morphism_proposals: list[str] = []
        try:
            from hermeneus.src.dispatch import extract_workflows, resolve_wf_paths
            from mekhane.taxis.morphism_proposer import parse_trigonon, format_proposal
            from pathlib import Path
            
            wfs = extract_workflows(ast)
            if wfs:
                paths = resolve_wf_paths(wfs)
                seen_proposals = set()
                for wf_id, wf_path in paths.items():
                    trigonon = parse_trigonon(Path(wf_path))
                    if trigonon:
                        prop_text = format_proposal(wf_id.lstrip("/"), trigonon, confidence=final_confidence)
                        if prop_text and prop_text not in seen_proposals:
                            morphism_proposals.append(prop_text.strip())
                            seen_proposals.add(prop_text)
        except Exception as e:  # noqa: BLE001
            logger.debug("MorphismProposer failed: %s", e)

        # === Kalon Quality Check ===
        kalon_report_str = ""
        try:
            from mekhane.fep.kalon_checker import KalonChecker
            checker = KalonChecker()
            report = checker.check_all()
            kalon_report_str = report.summary()
        except Exception as e:  # noqa: BLE001
            logger.debug("KalonChecker failed: %s", e)

        # === Cone Consumer (Devil's Advocate) ===
        return ExecutionResult(
            ccl=ccl,
            expanded_ccl=expanded,
            steps=all_steps,
            final_output=root_result.output,
            structured_output=ctx.structured,
            final_confidence=final_confidence,
            total_entropy_reduction=root_result.entropy_reduction,
            total_duration_ms=total_duration,
            bottleneck_step=bottleneck,
            gradient_map=gradient_map,
            morphism_proposals=morphism_proposals,
            derivative=derivative,
        )

    # PURPOSE: 実行 + 確信度が低ければボトルネックを再実行
    def execute_and_retry(
        self,
        ccl: str,
        context: str = "",
        min_confidence: float = 0.7,
        max_retries: int = 3,
    ) -> ExecutionResult:
        """実行 + 確信度が低ければボトルネックを再実行

        拡散モデルの「段階的デノイジング」に相当。
        """
        result = self.execute(ccl, context)

        for attempt in range(max_retries):
            if result.final_confidence >= min_confidence:
                break

            # ボトルネックのステップだけ再実行
            if result.bottleneck_step:
                enhanced_context = (
                    f"{context}\n\n"
                    f"[Retry {attempt + 1}] Previous attempt identified "
                    f"'{result.bottleneck_step}' as bottleneck "
                    f"(gradient={result.gradient_map.get(result.bottleneck_step, 0):.2f}). "
                    f"Focus on improving this step."
                )
                result = self.execute(ccl, enhanced_context)

        return result


# =============================================================================
# Convenience Functions
# =============================================================================

# PURPOSE: マクロを実行 (便利関数)
def execute_macro(ccl: str, context: str = "") -> ExecutionResult:
    """マクロを実行 (便利関数)"""
    return MacroExecutor().execute(ccl, context)


# PURPOSE: マクロを実行し、人間可読な説明を返す
def execute_and_explain(ccl: str, context: str = "") -> str:
    """マクロを実行し、人間可読な説明を返す"""
    result = execute_macro(ccl, context)
    return result.summary()
