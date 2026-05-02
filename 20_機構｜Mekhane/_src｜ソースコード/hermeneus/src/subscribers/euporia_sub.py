from __future__ import annotations
# PROOF: [L2/Phase2] <- hermeneus/src/subscribers/euporia_sub.py
"""
EuporiaSubscriber — 行為可能性増大チェック (Euporía Principle)

定理³ Euporía: 全ての認知操作は行為可能性を増やさなければならない。
WF 実行完了時に出力テキストから affordance パターンをスキャンし、
深度に応じた閾値で品質チェックを行う。

6射影スコアリング (euporia.md §2b):
  Value (pragmatic/epistemic), Function (探索/活用),
  Precision (確信度校正), Temporality (時間的区別),
  Scale (スケール横断), Valence (正負両面)

ドメイン重点座標 (euporia.md §7.5 — C1' 修正: 3D+Hóros):
  Cognition→Function,Precision / Description→Value,Precision
  Hóros(横断)→Precision,Valence / Linkage→Scale,Temporality,Valence

発火条件: EXECUTION_COMPLETE イベント時。
影響: affordance 不足なら警告テキストを返す。

参照: axiom_hierarchy.md §定理³ Euporía
      euporia.md §7 Q1-Q2
"""

import logging
import re
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from mekhane.anamnesis.embedder_mixin import EmbedderMixin

from ..activation import BaseSubscriber, ActivationPolicy
from ..event_bus import CognitionEvent, EventType

logger = logging.getLogger(__name__)


# =============================================================================
# Affordance パターン定義
# =============================================================================

# PURPOSE: 行為可能性 (pragmatic) のパターン — 「次に何ができるか」
PRAGMATIC_PATTERNS = re.compile(
    r'(?:'
    r'→次|→\s*次|🕳️|📍'                    # HGK 標準出力マーカー
    r'|次のステップ|次の一手|次にやるべき'       # 日本語の「次」表現
    r'|アクション|実行可能|着手'                # 行動語彙
    r'|next\s*(?:step|action)|TODO|FIXME'     # 英語マーカー
    r'|- \[ \]'                               # タスクリスト (未完了)
    r'|提案[:：]\s*\S'                         # 提案の後に内容がある
    r'|→\s*\S'                                # → の後に具体的内容
    # ── v0.5: Pragmatic Gemini 自然言語表現拡張 ──
    r'|する必要があります|おすすめします|推奨します'
    r'|ご[確検]討ください|解決策[:：]|対策[:：]'
    r'|具体的な手順|ステップ\d'
    r')',
    re.IGNORECASE | re.MULTILINE,
)

# PURPOSE: 認識可能性 (epistemic) のパターン — 「何がわかったか」
EPISTEMIC_PATTERNS = re.compile(
    r'(?:'
    r'発見|判明|わかった|明らかに'              # 日本語の認識語彙
    r'|\[DISCOVERY\]|\[FACT\]|\[DECISION\]'   # HGK 意味タグ
    r'|insight|finding|learned|discovered'      # 英語マーカー
    r'|新たに|初めて|意外'                      # 新規性シグナル
    r'|\[主観\]'                                # N-7 主観表出 (認知的発見)
    r'|仮説[:：]\s*\S'                         # 仮説の提示
    # ── v0.4: Handoff AY スキャン偽陰性修正 (E=9/20 → 改善) ──
    # ── v0.5: Epistemic 完了形制約緩和 ──
    r'|[確検]証[し済]|調査[し済]|分析[し済]'     # 結果動詞・名詞 (「結」除外: 分析結果 偽陽性防止)
    r'|特定[し済]|修正[し済]|対応[し済]|解決[し済]' # 成果動詞・名詞
    r'|実施[し済]|修復[し済]'                    # 対応動詞・名詞
    r'|原因[はが]|問題[はが]'                    # 原因/問題特定 (助詞で文脈を絞る)
    r'|結果[:：]\s*\S|結果,\s*\S'              # 「結果: ...」形式
    r'|✅\s*.+済'                               # チェックマーク + 済
    r'|クローズ|CLOSE|resolved'                  # 完了シグナル
    # ── v0.6: Handoff E 合格率改善 (30% → 70%) ──
    r'|完了[。！\s\n]|全完了'                     # 完了マーカー
    r'|passed|PASSED'                             # テスト結果
    r'|確認済|動作確認'                            # 確認結果
    r'|成果[:：\s]'                               # 成果セクション
    r'|設計判断'                                  # 判断記録
    r'|撤廃|削除[し済]|統合[し済]'                 # 除去/統合の完了
    r')',
    re.IGNORECASE | re.MULTILINE,
)

# PURPOSE: Function 射影 — 探索/活用の区別 (euporia.md §2b #3a-2)
FUNCTION_PATTERNS = re.compile(
    r'(?:'
    r'探索|活用|Explore|Exploit'                # 直接的区別
    r'|/ske|/sag|/pei|/tek'                     # WF 参照
    r'|不確実|確実|仮説空間|収束'               # 状態記述
    r')',
    re.IGNORECASE | re.MULTILINE,
)

# PURPOSE: Precision 射影 — 確信度校正 (euporia.md §2b #3a-3)
PRECISION_PATTERNS = re.compile(
    r'(?:'
    r'\[確信\]|\[推定\]|\[仮説\]'              # N-3 確信度ラベル
    r'|SOURCE|TAINT'                            # N-10 精度ラベル
    r'|精度|校正|calibrat'                      # 精度語彙
    r'|confidence|precision'                    # 英語マーカー
    r')',
    re.IGNORECASE | re.MULTILINE,
)

# PURPOSE: Temporality 射影 — 時間的区別 (euporia.md §2b #3a-4)
TEMPORALITY_PATTERNS = re.compile(
    r'(?:'
    r'過去|未来|変遷|推移|時系列'               # 日本語の時間語彙
    r'|Past|Future|VFE|EFE'                     # FEP 用語
    r'|prior|posterior|変化'                    # 統計/変化
    r'|以前|今後|これまで|これから'              # 時間参照
    r')',
    re.IGNORECASE | re.MULTILINE,
)

# PURPOSE: Scale 射影 — スケール横断 (euporia.md §2b #3a-5)
SCALE_PATTERNS = re.compile(
    r'(?:'
    r'局所|全体|Micro|Macro'                    # スケール語彙
    r'|体系|個別|統合|横断'                     # 構造語彙
    r'|影響範囲|波及|上位|下位'                 # 範囲語彙
    r')',
    re.IGNORECASE | re.MULTILINE,
)

# PURPOSE: Valence 射影 — 正負の両面評価 (euporia.md §2b #3a-6)
VALENCE_PATTERNS = re.compile(
    r'(?:'
    r'反証|支持|賛否|反対'                      # 評価語彙
    r'|リスク|利点|欠点|懸念'                   # リスク/メリット
    r'|trade.?off|一方で|ただし|しかし'          # 対比接続
    r'|AY⁺|AY⁻'                                # AY 正負記号
    # ── v0.4: Valence 偽陰性修正 ──
    r'|課題|注意点|制約|制限'                    # 制約/課題語彙
    r'|未解決|残[タ件量]|未[テ対]'               # 未完了シグナル
    r'|改善|劣化|品質'                          # 品質評価
    r'|⚠|⚠️|❌|✗'                               # アイコンマーカー
    r')',
    re.IGNORECASE | re.MULTILINE,
)

# PURPOSE: 6射影パターンの名前→コンパイル済み正規表現のマップ
PROJECTION_PATTERNS: Dict[str, "re.Pattern[str]"] = {
    "Value_P": PRAGMATIC_PATTERNS,    # Value = pragmatic + epistemic
    "Value_E": EPISTEMIC_PATTERNS,
    "Function": FUNCTION_PATTERNS,
    "Precision": PRECISION_PATTERNS,
    "Temporality": TEMPORALITY_PATTERNS,
    "Scale": SCALE_PATTERNS,
    "Valence": VALENCE_PATTERNS,
}


# =============================================================================
# AY スコアリング (U3: embedding ベース定量化)
# =============================================================================

# PURPOSE: AY 測定結果を格納する構造体
class AYResult(NamedTuple):
    """Affordance Yield 測定結果

    ay_score: 統合 AY スコア [0, 1] — α·micro + (1-α)·macro
    ay_micro: 正規表現ベースの6射影充足率 [0, 1]
    ay_macro: embedding 距離ベースの意味的変化量 [0, 1]
    projections: 6射影の個別カウント (Layer 1 の詳細)
    depth: 使用された深度
    """
    ay_score: float
    ay_micro: float
    ay_macro: float
    projections: Dict[str, int]
    depth: str


# PURPOSE: 深度に応じた α (micro/macro の重み) スケジュール
# α が高い = micro (正規表現) を重視、α が低い = macro (embedding) を重視
DEFAULT_ALPHA_SCHEDULE: Dict[str, float] = {
    "L0": 1.0,   # embedding 不要 (skip)
    "L1": 0.8,   # 正規表現重視
    "L2": 0.5,   # 均等
    "L3": 0.3,   # embedding 重視
}


# PURPOSE: AY の定量化ロジック (euporia.md §2.7 E4-4 Stage 1)
class AYScorer:
    """Affordance Yield のスコアリング

    2層構造:
      Layer 1 (micro): 正規表現パターンによる6射影の充足率
      Layer 2 (macro): embedding cosine 距離による意味的変化量

    AY = α · micro + (1-α) · macro
      α は深度に依存: L1→0.8 (正規表現重視) / L3→0.3 (embedding 重視)

    参照: euporia.md §2.7 E4-4, §2b 6射影
    """

    def __init__(
        self,
        alpha_schedule: Optional[Dict[str, float]] = None,
    ):
        self.alpha_schedule = alpha_schedule or DEFAULT_ALPHA_SCHEDULE

    def compute_micro(
        self, output: str, depth: str,
        projections: Optional[Dict[str, int]] = None,
    ) -> float:
        """Layer 1: 正規表現ベースの6射影充足率 [0, 1]

        各射影のカウントを深度閾値で正規化し、加重平均を取る。
        閾値を超えたカウントは 1.0 にクリップ (超過は加点しない)。

        Args:
            projections: 事前計算済みの射影カウント (省略時は内部で計算)
        """
        if not output:
            return 0.0

        # 6射影のカウント (事前計算済みがあれば再利用)
        if projections is None:
            projections = {
                name: len(pattern.findall(output))
                for name, pattern in PROJECTION_PATTERNS.items()
            }

        # 深度閾値 (pragmatic_min, epistemic_min)
        prag_min, epis_min = DEPTH_THRESHOLDS.get(depth, DEPTH_THRESHOLDS["L2"])

        # 各射影の充足率を計算
        # Value = (pragmatic 充足 + epistemic 充足) / 2
        # 他の射影 = 出現有無 (0 or 1)
        scores: list[float] = []

        # Value_P (pragmatic)
        if prag_min > 0:
            scores.append(min(projections["Value_P"] / prag_min, 1.0))
        else:
            scores.append(1.0 if projections["Value_P"] > 0 else 0.5)

        # Value_E (epistemic)
        if epis_min > 0:
            scores.append(min(projections["Value_E"] / epis_min, 1.0))
        else:
            scores.append(1.0 if projections["Value_E"] > 0 else 0.5)

        # Function, Precision, Temporality, Scale, Valence
        # L1 では出現有無のみ (0 or 1)、L2+ では min(count/2, 1.0)
        secondary_target = 2 if depth in ("L2", "L3") else 1
        for key in ["Function", "Precision", "Temporality", "Scale", "Valence"]:
            count = projections[key]
            scores.append(min(count / secondary_target, 1.0) if secondary_target > 0 else 0.0)

        # 加重平均 (Value は2エントリにわたるため均等配分で計 7 要素)
        return sum(scores) / len(scores) if scores else 0.0

    def compute_macro(
        self,
        input_context: str,
        output: str,
        embedder: Optional["EmbedderMixin"] = None,
    ) -> float:
        """Layer 2: embedding cosine 距離による意味的変化量 [0, 1]

        AY_macro = 1 - cosine_similarity(embed(input), embed(output))
        → 状態変化が大きいほどスコアが高い。

        embedder が None の場合は 0.0 を返す (後方互換)。
        """
        if embedder is None:
            return 0.0
        if not input_context or not output:
            return 0.0

        try:
            distance = embedder.novelty(input_context, output)
            return max(0.0, min(distance, 1.0))
        except Exception as e:  # noqa: BLE001
            logger.warning("AYScorer.compute_macro failed: %s", e)
            return 0.0

    def compute(
        self,
        output: str,
        depth: str,
        input_context: str = "",
        embedder: Optional["EmbedderMixin"] = None,
        projections: Optional[Dict[str, int]] = None,
    ) -> AYResult:
        """統合 AY スコアを計算

        AY = α · micro + (1-α) · macro

        Args:
            projections: 事前計算済みの射影カウント (省略時は内部で計算)
        """
        # 射影カウント (事前計算済みがあれば再利用)
        if projections is None:
            projections = {
                name: len(pattern.findall(output))
                for name, pattern in PROJECTION_PATTERNS.items()
            }

        # Layer 1: micro (射影を共有して二重計算を回避)
        ay_micro = self.compute_micro(output, depth, projections=projections)

        # Layer 2: macro
        ay_macro = self.compute_macro(input_context, output, embedder)

        # α (深度依存の重み)
        alpha = self.alpha_schedule.get(depth, 0.5)

        # embedder がない場合は micro のみ (α=1.0 相当)
        if embedder is None or not input_context:
            ay_score = ay_micro
        else:
            ay_score = alpha * ay_micro + (1.0 - alpha) * ay_macro

        return AYResult(
            ay_score=round(ay_score, 4),
            ay_micro=round(ay_micro, 4),
            ay_macro=round(ay_macro, 4),
            projections=projections,
            depth=depth,
        )


# =============================================================================
# Presheaf 計数 (U4: E4-4 Stage 2)
# =============================================================================

# PURPOSE: Presheaf (前層) 計数結果を格納する構造体
class PresheafResult(NamedTuple):
    """Presheaf 計数結果

    reachable_wf_count: 到達可能な WF 数 (Drift < threshold)
    presheaf_score: Σ(1 - drift) — 行為可能性の総和
    wf_details: 各 WF の drift 計算結果の詳細
    """
    reachable_wf_count: int
    presheaf_score: float
    wf_details: List[Dict[str, object]]


# PURPOSE: 36動詞の ID リスト (entity-map 準拠 v5.4)
POIESIS_36: List[str] = [
    # Telos (目的) = Flow × Value
    "noe", "bou", "zet", "ene", "the", "ant",
    # Methodos (方法) = Flow × Function
    "ske", "sag", "pei", "tek", "ere", "agn",
    # Krisis (判断) = Flow × Precision
    "epo", "kat", "dok", "pai", "sap", "ski",
    # Diástasis (拡張) = Flow × Scale
    "lys", "ops", "akr", "ark", "prs", "per",
    # Orexis (欲求) = Flow × Valence
    "ele", "beb", "dio", "kop", "apo", "exe",
    # Chronos (時間) = Flow × Temporality
    "hyp", "prm", "ath", "par", "his", "prg",
]


# PURPOSE: E4-4 Stage 2 の presheaf (前層) スコアリング
class PresheafScorer:
    """状態 B から到達可能な WF を全36動詞で走査し presheaf_score を算出する。

    presheaf_score = Σ (1 - Drift(B, wf_def)) for wf in reachable_wfs
    到達可能: Drift(B, wf_def) < drift_threshold

    数学的意味: Hom(B, -) の「太さ」= B からの射の本数 × 各射の品質。
    参照: euporia.md §4 E4-4 Stage 2, kalon.md §2 Corollary 2.1
    """

    # PURPOSE: Presheaf 計数器の初期化
    def __init__(self, drift_threshold: float = 0.8):
        self.drift_threshold = drift_threshold

    def compute(
        self,
        output: str,
        source_wf_id: str = "",
    ) -> PresheafResult:
        """全36動詞に対して drift を計算し presheaf_score を返す。

        Args:
            output: WF 実行結果のテキスト (= 現在の状態 B)
            source_wf_id: 実行元の WF ID (自己遷移を除外するため)

        Returns:
            PresheafResult
        """
        from hermeneus.src.macro_executor import WFResolver, EntropyEstimator

        if not output:
            return PresheafResult(
                reachable_wf_count=0,
                presheaf_score=0.0,
                wf_details=[],
            )

        # 実行元 WF を除外用に正規化
        source_clean = source_wf_id.lstrip("/").rstrip("+-^")

        details: List[Dict[str, object]] = []
        presheaf_sum = 0.0
        reachable_count = 0

        for wf_id in POIESIS_36:
            # 自己遷移は除外
            if wf_id == source_clean:
                continue

            # WF 定義テキストを取得
            wf_def = WFResolver.load_definition(wf_id)
            if wf_def is None:
                details.append({
                    "wf_id": wf_id,
                    "drift": 1.0,
                    "reachable": False,
                    "reason": "定義ファイル未発見",
                })
                continue

            # drift を計算 (n-gram Jaccard ベース — 計算コスト: 数μs)
            drift = EntropyEstimator.estimate_drift(output, wf_def)

            reachable = drift < self.drift_threshold
            if reachable:
                reachable_count += 1
                presheaf_sum += 1.0 - drift

            details.append({
                "wf_id": wf_id,
                "drift": round(drift, 4),
                "reachable": reachable,
            })

        return PresheafResult(
            reachable_wf_count=reachable_count,
            presheaf_score=round(presheaf_sum, 4),
            wf_details=details,
        )


# =============================================================================
# 深度別閾値
# =============================================================================

# PURPOSE: 深度に応じた affordance 要件
DEPTH_THRESHOLDS: Dict[str, Tuple[int, int]] = {
    # (pragmatic_min, epistemic_min)
    "L0": (0, 0),   # 明示不要
    "L1": (1, 0),   # pragmatic ≥ 1
    "L2": (2, 1),   # pragmatic ≥ 2 + epistemic ≥ 1
    "L3": (3, 2),   # pragmatic ≥ 3 + epistemic ≥ 2
}


# =============================================================================
# ドメイン推定 + 重点座標 (euporia.md §7.5 — C1' 3D+Hóros)
# =============================================================================

# PURPOSE: source_node からドメインを推定するためのパターンマップ
DOMAIN_NODE_MAP: Dict[str, List[str]] = {
    "Description": ["@typos", "@prompt", "typos"],
    "Hóros": ["@proof", "/fit", "/ele", "proof", "dendron"],  # C1': Constraint → Hóros (横断)
    "Linkage": ["@index", "/eat", "@read", "@chew", "index", "gnosis"],
    # Cognition はデフォルト — 36動詞の大半が該当
}

# PURPOSE: ドメインごとの重点座標 (euporia.md §7.5 表 — C1' 修正版)
# 重点座標の検出パターンが L2+ で 0 件の場合に警告を発する
DOMAIN_EMPHASIS: Dict[str, List[str]] = {
    "Cognition": ["Function", "Precision"],
    "Description": ["Value_P", "Precision"],         # Value_P = pragmatic (記述の実用価値)
    "Hóros": ["Precision", "Valence"],               # C1': Constraint → Hóros (横断)
    "Linkage": ["Scale", "Temporality", "Valence"],  # /ele E5 修正: Valence 追加
}


# =============================================================================
# EuporiaSubscriber
# =============================================================================

# PURPOSE: WF 出力の行為可能性をチェックする subscriber
class EuporiaSubscriber(BaseSubscriber):
    """WF 完了時に出力の行為可能性 (Euporía) をスキャンする subscriber

    定理³ Euporía: 全ての認知操作は行為可能性を増やさなければならない。
    EFE(B) > EFE(A) — 出力 B は入力 A より多くの affordance を持つべき。

    責務境界 (vs KalonGateSubscriber):
        - KalonGate: VERIFICATION で発火。Trace/Negativa の構造的完全性。
        - Euporia: EXECUTION_COMPLETE で発火。行為可能性の増大 (pragmatic/epistemic)。
    """

    def __init__(
        self,
        fire_threshold: float = 0.3,
        default_depth: str = "L2",
        embedder: Optional["EmbedderMixin"] = None,
        alpha_schedule: Optional[Dict[str, float]] = None,
    ):
        super().__init__(
            name="euporia",
            policy=ActivationPolicy(
                event_types={EventType.EXECUTION_COMPLETE},
            ),
            fire_threshold=fire_threshold,
        )
        self.default_depth = default_depth
        self.embedder = embedder
        self.ay_scorer = AYScorer(alpha_schedule=alpha_schedule)
        self.presheaf_scorer = PresheafScorer()
        
        # テストや外部参照用に保持するローカルの Trace リスト
        from hermeneus.src.stigmergy import Trace
        self.stigmergy_traces: List[Trace] = []

    def leave_trace(self, event: CognitionEvent, payload: Dict[str, Any], intensity: Optional[float] = None) -> None:
        """Trace を残す (ローカルリストにも保存)"""
        from hermeneus.src.stigmergy import Trace
        trace = Trace(
            subscriber_name=self.name,
            event_id=event.event_id,
            intensity=intensity if intensity is not None else 0.5,
            payload=payload,
        )
        self.stigmergy_traces.append(trace)
        # 環境 (StigmergyContext) に登録されている場合はそちらにも残す
        super().leave_trace(event, payload, intensity)

    # PURPOSE: スコア計算 — 出力長 + 6射影カバレッジ + AY micro
    def score(self, event: CognitionEvent) -> float:
        """出力の長さと6射影カバレッジに基づくスコア

        スコア構成:
          base (0.2) + length_bonus (最大0.3) + coverage_bonus (最大0.3) + ay_bonus (最大0.2)
          = 最大 1.0
        """
        result = event.step_result
        if result is None:
            return 0.0
        output = result.output if hasattr(result, 'output') else ""
        if not output:
            return 0.0
        length = len(output)
        # 長さボーナス: 2500文字で 0.3
        length_bonus = min(length / 2500, 0.3)
        # 射影カバレッジボーナス: 6射影中検出された射影の割合 × 0.3
        projections = self._compute_projections(output)
        # Value は Value_P + Value_E のいずれかで 1 カウント
        covered = 0
        if projections.get("Value_P", 0) > 0 or projections.get("Value_E", 0) > 0:
            covered += 1
        for key in ["Function", "Precision", "Temporality", "Scale", "Valence"]:
            if projections.get(key, 0) > 0:
                covered += 1
        coverage_bonus = (covered / 6) * 0.3
        # AY micro ボーナス (射影を共有して二重計算を回避)
        depth = self._extract_depth(event)
        ay_micro = self.ay_scorer.compute_micro(output, depth, projections=projections)
        ay_bonus = ay_micro * 0.2
        return min(0.2 + length_bonus + coverage_bonus + ay_bonus, 1.0)

    # PURPOSE: メインハンドラ — affordance パターンをスキャンし警告を返す
    def handle(self, event: CognitionEvent) -> Optional[str]:
        """出力の行為可能性をスキャンする

        2層チェック:
          Layer 1: Value 射影 (pragmatic/epistemic) — 全深度で適用
          Layer 2: ドメイン重点座標 — L2+ で適用
        """
        result = event.step_result
        if result is None:
            return None

        output = result.output if hasattr(result, 'output') else ""
        if not output or len(output) < 50:
            # 50文字未満は L0 操作とみなしスキップ
            return None

        # 深度を決定 (メタデータから取得、なければデフォルト)
        depth = self._extract_depth(event)

        # 閾値を取得
        prag_min, epis_min = DEPTH_THRESHOLDS.get(depth, DEPTH_THRESHOLDS["L2"])

        # L0 はチェック不要
        if depth == "L0":
            return None

        # --- 射影カウント (1回だけ計算し全ステップで共有) ---
        projections = self._compute_projections(output)
        pragmatic_count = projections["Value_P"]
        epistemic_count = projections["Value_E"]

        # --- Layer 1: Value 射影 (pragmatic/epistemic) ---
        warnings: List[str] = []

        if pragmatic_count < prag_min:
            warnings.append(
                f"- [Euporía] Pragmatic 不足: 行為可能性が {pragmatic_count} 件 "
                f"(要件: ≥{prag_min})。「→次に何ができるか」を明示してください。"
            )

        if epistemic_count < epis_min:
            warnings.append(
                f"- [Euporía] Epistemic 不足: 認識的発見が {epistemic_count} 件 "
                f"(要件: ≥{epis_min})。「何がわかったか」を明示してください。"
            )

        # --- Layer 2: ドメイン重点座標チェック (L2+ のみ) ---
        domain = self._extract_domain(event)
        emphasis_keys = DOMAIN_EMPHASIS.get(domain, [])

        emphasis_warnings: List[str] = []
        if depth in ("L2", "L3") and emphasis_keys:
            for key in emphasis_keys:
                count = projections.get(key, 0)
                if count == 0:
                    # 射影名を読みやすく変換
                    display_name = key.replace("Value_P", "Value(Pragmatic)").replace("Value_E", "Value(Epistemic)")
                    emphasis_warnings.append(
                        f"- [Euporía] {display_name} 射影不足 "
                        f"(ドメイン '{domain}' の重点座標)。"
                    )

        all_warnings = warnings + emphasis_warnings

        # --- AY スコアリング (U3 — 射影を共有して二重計算を回避) ---
        input_context = ""
        if event.metadata:
            input_context = event.metadata.get("input_context", "")
        ay_result = self.ay_scorer.compute(
            output=output,
            depth=depth,
            input_context=input_context,
            embedder=self.embedder,
            projections=projections,
        )

        # --- Presheaf 計数 (U4: E4-4 Stage 2) ---
        presheaf_result = self.presheaf_scorer.compute(
            output=output,
            source_wf_id=event.source_node,
        )

        # --- Trace payload 構築 (DRY: 共通部分を一度だけ構築) ---
        trace_payload: Dict[str, Any] = {
            "pragmatic": pragmatic_count,
            "epistemic": epistemic_count,
            "projections": projections,
            "domain": domain,
            "depth": depth,
            "ay_score": ay_result.ay_score,
            "ay_micro": ay_result.ay_micro,
            "ay_macro": ay_result.ay_macro,
            "presheaf_score": presheaf_result.presheaf_score,
            "reachable_wf_count": presheaf_result.reachable_wf_count,
        }

        if not all_warnings:
            # affordance 十分 — Stigmergy Trace を残して成功を記録
            trace_payload["status"] = "pass"
            self.leave_trace(event=event, payload=trace_payload, intensity=0.3)
            return None

        # 警告を構築
        lines = [
            f"【Euporía 品質ゲート警告 (Depth: {depth}, Domain: {domain})】",
            "出力に行為可能性 (affordance) の明示が不足しています。",
            f"定理³: 全ての認知操作は行為可能性を増やさなければならない。",
            f"",
            f"📊 検出: pragmatic={pragmatic_count}, epistemic={epistemic_count}",
            f"📏 要件: pragmatic≥{prag_min}, epistemic≥{epis_min}",
            f"📈 AY スコア: {ay_result.ay_score:.3f} (micro={ay_result.ay_micro:.3f}, macro={ay_result.ay_macro:.3f})",
        ]
        lines.extend(all_warnings)
        lines.append(
            "→ 「次に何ができるか」(pragmatic) と「何がわかったか」(epistemic) を出力に含めてください。"
        )

        advice = "\n".join(lines)
        logger.info(
            "Euporia: affordance deficit detected (%d warnings, depth=%s, domain=%s, ay=%.3f)",
            len(all_warnings), depth, domain, ay_result.ay_score,
        )

        # Stigmergy Trace を残す
        trace_payload["warnings"] = len(all_warnings)
        trace_payload["status"] = "warn"
        self.leave_trace(event=event, payload=trace_payload, intensity=0.8)

        return advice

    # PURPOSE: イベントメタデータから深度を抽出
    def _extract_depth(self, event: CognitionEvent) -> str:
        """CCL の修飾子やメタデータから深度を推定する"""
        # メタデータに明示されている場合
        if event.metadata:
            depth = event.metadata.get("depth", "")
            if depth in DEPTH_THRESHOLDS:
                return depth

        # source_node から推定: + → L3, - → L1, 無印 → L2
        node = event.source_node
        if node.endswith("+"):
            return "L3"
        elif node.endswith("-"):
            return "L1"

        return self.default_depth

    # PURPOSE: source_node からドメインを推定 (euporia.md §7.5 — C1' 3D+Hóros)
    def _extract_domain(self, event: CognitionEvent) -> str:
        """WF ノード ID からドメインを推定する

        Returns:
            "Cognition" | "Description" | "Constraint" | "Linkage"
        """
        # メタデータに明示されている場合
        if event.metadata:
            domain = event.metadata.get("domain", "")
            if domain in DOMAIN_EMPHASIS:
                return domain

        # source_node のパターンマッチ
        node = event.source_node.lower()
        for domain_name, patterns in DOMAIN_NODE_MAP.items():
            for pattern in patterns:
                if pattern.lower() in node:
                    return domain_name

        return "Cognition"  # デフォルト: 36動詞の大半は Cognition

    # PURPOSE: 出力テキストから6射影のパターン出現数を計算
    def _compute_projections(self, output: str) -> Dict[str, int]:
        """6射影 (7パターン) の出現回数を返す

        Returns:
            {"Value_P": n, "Value_E": n, "Function": n, ...}
        """
        return {
            name: len(pattern.findall(output))
            for name, pattern in PROJECTION_PATTERNS.items()
        }
