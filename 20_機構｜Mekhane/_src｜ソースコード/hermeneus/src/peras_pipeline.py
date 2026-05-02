# PROOF: [L2/インフラ] <- hermeneus/src/peras_pipeline.py 汎用 Series Hub 実行器
"""
Hermēneus Peras Pipeline — 汎用 Series Hub 実行器

個々の Series Hub WF (/t, /m, /k, /d, /o, /c) を
「4定理の個別推論 → Limit 収束 → 構造化出力」の
3フェーズで自動実行する。

AxPipeline が6つの PerasPipeline を呼び出す設計。

Phase 1: 4定理の個別 LLM 推論 (verb evaluation)
Phase 2: Limit 演算 (C0→C1→C2→C3 PW加重融合)
Phase 3: 構造化出力の生成

Usage:
    pipeline = PerasPipeline(series_id="t", model="gemini-3-flash-preview")
    result = await pipeline.run(context="分析対象テキスト")
    print(result.output)

Origin: 2026-02-22 PerasPipeline 実装 (Hub WF 自動実行)
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# =============================================================================
# Shared Types (ax_pipeline.py からも参照される)
# =============================================================================

# 6 Series の定義 (v4.1 準拠)
PERAS_SERIES = [
    {"id": "t", "name": "Telos",     "code": "Tel", "question": "Why",      "verbs": ["noe", "bou", "zet", "ene"]},
    {"id": "m", "name": "Methodos",  "code": "Met", "question": "How",      "verbs": ["ske", "sag", "pei", "tek"]},
    {"id": "k", "name": "Krisis",    "code": "Kri", "question": "How much", "verbs": ["kat", "epo", "pai", "dok"]},
    {"id": "d", "name": "Diástasis", "code": "Dia", "question": "Where",    "verbs": ["lys", "ops", "akr", "arc"]},
    {"id": "o", "name": "Orexis",    "code": "Ore", "question": "Which",    "verbs": ["beb", "ele", "kop", "dio"]},
    {"id": "c", "name": "Chronos",   "code": "Chr", "question": "When",     "verbs": ["hyp", "prm", "ath", "par"]},
]


@dataclass
class PerasResult:
    """Individual Peras evaluation result"""
    series_id: str          # e.g., "t"
    series_name: str        # e.g., "Telos"
    series_code: str        # e.g., "Tel"
    ccl_executed: str       # e.g., "/t+"
    output: str             # LLM output
    success: bool = True
    confidence: float = 0.0
    duration_ms: float = 0.0
    error: Optional[str] = None


# =============================================================================
# Types
# =============================================================================

# Series 座標のマッピング (v4.1 公理体系準拠)
SERIES_COORDINATES = {
    "t": {"axis": "Value",       "poles": ("Epistemic", "Pragmatic"), "question": "何を / なぜ"},
    "m": {"axis": "Function",    "poles": ("Explore", "Exploit"),     "question": "どのように"},
    "k": {"axis": "Precision",   "poles": ("Confidence", "Uncertainty"), "question": "どれくらい確実に"},
    "d": {"axis": "Scale",       "poles": ("Micro", "Macro"),         "question": "どの粒度・範囲で"},
    "o": {"axis": "Valence",     "poles": ("Positive", "Negative"),   "question": "どちらへ向かうか"},
    "c": {"axis": "Temporality", "poles": ("Past", "Future"),         "question": "いつ"},
}


@dataclass
class VerbResult:
    """Individual verb (theorem) evaluation result"""
    verb_id: str            # e.g., "noe"
    verb_name: str          # e.g., "Noēsis"
    verb_number: int        # e.g., 1 (V01)
    output: str             # LLM output
    success: bool = True
    duration_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class LimitResult:
    """Limit convergence result from Phase 2"""
    c0_pw: str = ""         # Precision Weighting
    c1_contrast: str = ""   # 4射の対比
    c2_fusion: str = ""     # PW加重融合
    c3_kalon: str = ""      # 普遍性検証
    conclusion: str = ""    # 最終1文結論
    confidence: float = 0.0
    coordinate_value: str = ""  # 座標判定 (例: "Explore寄り")


# =============================================================================
# Verb Definitions (v4.1 準拠)
# =============================================================================

# 各 Series の4定理の名前と説明
VERB_DEFINITIONS = {
    "t": [
        {"id": "noe", "name": "Noēsis",    "num": 1,  "role": "深い認識・直観。対象の本質を捉える"},
        {"id": "bou", "name": "Boulēsis",   "num": 2,  "role": "意志・目的。何を望むかを明確化する"},
        {"id": "zet", "name": "Zētēsis",    "num": 3,  "role": "探求。何を問うべきかを発見する"},
        {"id": "ene", "name": "Energeia",   "num": 4,  "role": "行為。意志を現実に具現化する"},
    ],
    "m": [
        {"id": "ske", "name": "Skepsis",    "num": 5,  "role": "仮説空間を拡げ、前提を破壊する"},
        {"id": "sag", "name": "Synagōgē",   "num": 6,  "role": "仮説空間を絞り込み、最適構造を統合する"},
        {"id": "pei", "name": "Peira",      "num": 7,  "role": "未知領域で情報を集め、仮説を実験で検証する"},
        {"id": "tek", "name": "Tekhnē",     "num": 8,  "role": "既知の手法を使って確実に成果を出す"},
    ],
    "k": [
        {"id": "kat", "name": "Katalēpsis",  "num": 9,  "role": "信念を固定しコミットする"},
        {"id": "epo", "name": "Epochē",      "num": 10, "role": "判断を開いて複数可能性を保持する"},
        {"id": "pai", "name": "Proairesis",   "num": 11, "role": "確信を持って資源を投入する"},
        {"id": "dok", "name": "Dokimasia",    "num": 12, "role": "小さく一歩を打って反応を見る"},
    ],
    "d": [
        {"id": "lys", "name": "Analysis",         "num": 13, "role": "局所的に深く推論する"},
        {"id": "ops", "name": "Synopsis",          "num": 14, "role": "広域的に全体を推論する"},
        {"id": "akr", "name": "Orexis",          "num": 15, "role": "局所的に正確に行動する"},
        {"id": "arc", "name": "Architektonikē",    "num": 16, "role": "広域的に一斉に行動する"},
    ],
    "o": [
        {"id": "beb", "name": "Bebaiōsis",   "num": 17, "role": "信念を強化・承認する"},
        {"id": "ele", "name": "Elenchos",    "num": 18, "role": "信念を問い直し問題を検知する"},
        {"id": "kop", "name": "Prokopē",     "num": 19, "role": "成功方向をさらに前進させる"},
        {"id": "dio", "name": "Diorthōsis",  "num": 20, "role": "問題を修正し方向を変える"},
    ],
    "c": [
        {"id": "hyp", "name": "Hypomnēsis",     "num": 21, "role": "過去の信念状態にアクセスする"},
        {"id": "prm", "name": "Promētheia",      "num": 22, "role": "未来の状態を推論・予測する"},
        {"id": "ath", "name": "Anatheōrēsis",    "num": 23, "role": "過去の行動を評価し教訓を抽出する"},
        {"id": "par", "name": "Proparaskeuē",    "num": 24, "role": "未来を形成するための先制行動をとる"},
    ],
}


# =============================================================================
# SKILL.md Core Extraction
# =============================================================================

# 定理 ID → SKILL.md ディレクトリのマッピング
_VERB_SKILL_DIRS = {
    # Telos
    "noe": "telos/v01-noesis",
    "bou": "telos/v02-boulesis",
    "zet": "telos/v03-zetesis",
    "ene": "telos/v04-energeia",
    # Methodos
    "ske": "methodos/v05-skepsis",
    "sag": "methodos/v06-synagoge",
    "pei": "methodos/v07-peira",
    "tek": "methodos/v08-tekhne",
    # Krisis
    "kat": "krisis/v09-katalepsis",
    "epo": "krisis/v10-epoche",
    "pai": "krisis/v11-proairesis",
    "dok": "krisis/v12-dokimasia",
    # Diástasis
    "lys": "diastasis/v13-analysis",
    "ops": "diastasis/v14-synopsis",
    "akr": "diastasis/v15-akribeia",
    "arc": "diastasis/v16-architektonike",
    # Orexis
    "beb": "orexis/v17-bebaiosis",
    "ele": "orexis/v18-elenchos",
    "kop": "orexis/v19-prokope",
    "dio": "orexis/v20-diorthosis",
    # Chronos
    "hyp": "chronos/v21-hypomnesis",
    "prm": "chronos/v22-prometheia",
    "ath": "chronos/v23-anatheoresis",
    "par": "chronos/v24-proparaskeue",
}

# Skills ルートディレクトリ
_SKILLS_ROOT = Path(__file__).parent.parent.parent / "nous" / "skills"


def _extract_skill_core(
    verb_id: str,
    verb_num: int,
    verb_name: str,
    max_chars: int = 3000,
) -> str:
    """SKILL.md からプロンプト注入用のコアセクションを抽出

    抽出対象:
    - Processing Logic: 思考プロセスの概要 (パイプライン固有)
    - PHASE ヘッダー: 各フェーズの1行要約 (パイプライン固有)
    - When to Use の Trigger: 発動条件 (パイプライン固有)
    - 認知代数 / Anti-Patterns / WM管理: SkillRegistry に委譲

    Args:
        verb_id: 定理 ID (e.g., "noe")
        verb_num: 定理番号 (e.g., 1)
        verb_name: 定理名 (e.g., "Noēsis")
        max_chars: 抽出最大文字数
    """
    skill_dir = _VERB_SKILL_DIRS.get(verb_id)
    if not skill_dir:
        return ""

    skill_path = _SKILLS_ROOT / skill_dir / "SKILL.md"
    if not skill_path.exists():
        return ""

    try:
        content = skill_path.read_text(encoding="utf-8")
        lines = content.split("\n")
    except Exception:  # noqa: BLE001
        return ""

    sections = []

    # 1. Processing Logic セクションを抽出 (冒頭5行)
    pl_text = _extract_section(lines, "## Processing Logic", max_lines=5)
    if pl_text:
        sections.append(f"### 思考プロセス\n{pl_text}")

    # 2. 全 PHASE ヘッダーを1行ずつ抽出
    phase_lines = []
    for line in lines:
        if line.startswith("## PHASE"):
            phase_lines.append(f"- {line.replace('## ', '')}")
    if phase_lines:
        sections.append(f"### フェーズ構成\n" + "\n".join(phase_lines))

    # 3. When to Use → Trigger セクション (冒頭5行)
    trigger_text = _extract_section(lines, "### ✓ Trigger", max_lines=5)
    if trigger_text:
        sections.append(f"### 発動条件\n{trigger_text}")

    # 4. 認知代数・Anti-Patterns・WM管理: SkillRegistry に委譲
    try:
        from .skill_registry import get_default_skill_registry
        registry = get_default_skill_registry()
        supplements = registry.extract_cognitive_supplements(verb_id)
        if supplements:
            sections.append(supplements)
    except Exception:  # noqa: BLE001
        pass

    result = "\n\n".join(sections)
    return result[:max_chars] if result else ""


def _extract_section(
    lines: List[str],
    header: str,
    max_lines: int = 5,
) -> str:
    """Markdown のセクションヘッダー以降の max_lines 行を抽出"""
    found = False
    collected = []
    for line in lines:
        if found:
            # 次のセクションヘッダーで終了
            if line.startswith("##"):
                break
            if line.strip():
                collected.append(line)
            if len(collected) >= max_lines:
                break
        elif line.startswith(header):
            found = True
    return "\n".join(collected)
# =============================================================================

class PerasPipeline:
    """汎用 Series Hub 実行器

    個々の Series Hub WF (/t, /m, /k, /d, /o, /c) を
    3フェーズで自動実行する:

    Phase 1: 4定理の個別 LLM 推論
    Phase 2: Limit 演算 (C0→C1→C2→C3)
    Phase 3: 構造化出力の生成
    """

    def __init__(
        self,
        series_id: str,
        model: str = "auto",
        depth: str = "+",  # "+", "", "-"
    ):
        # Resolve series definition
        self.series_id = series_id
        series_def = next(
            (s for s in PERAS_SERIES if s["id"] == series_id), None
        )
        if not series_def:
            raise ValueError(f"Unknown series_id: {series_id}. Valid: t,m,k,d,o,c")

        self.series_name = series_def["name"]
        self.series_code = series_def["code"]
        self.question = series_def["question"]
        self.verbs = VERB_DEFINITIONS.get(series_id, [])
        self.coordinate = SERIES_COORDINATES.get(series_id, {})
        self.model = model
        self.depth = depth

    async def run(
        self,
        context: str,
        model: Optional[str] = None,
    ) -> PerasResult:
        """Execute the full Peras pipeline for this Series

        Args:
            context: Analysis target text
            model: LLM model override

        Returns:
            PerasResult with structured output
        """
        start_time = time.time()
        model = model or self.model

        try:
            # Phase 1: 4定理の個別推論
            verb_results = await self._phase1_verbs(context, model)

            # Phase 2: Limit 収束
            limit_result = await self._phase2_limit(
                context, verb_results, model
            )

            # Phase 3: 構造化出力
            formatted_output = self._phase3_format(
                verb_results, limit_result
            )

            return PerasResult(
                series_id=self.series_id,
                series_name=self.series_name,
                series_code=self.series_code,
                ccl_executed=f"/{self.series_id}{self.depth}",
                output=formatted_output,
                success=True,
                confidence=limit_result.confidence,
                duration_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:  # noqa: BLE001
            return PerasResult(
                series_id=self.series_id,
                series_name=self.series_name,
                series_code=self.series_code,
                ccl_executed=f"/{self.series_id}{self.depth}",
                output="",
                success=False,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )

    # ─── Phase 1: 4定理の個別推論 ──────────────────────────────

    async def _phase1_verbs(
        self,
        context: str,
        model: str,
    ) -> List[VerbResult]:
        """Phase 1: Execute each of the 4 verbs individually

        Each verb gets a focused prompt based on its role.
        Context accumulates across verbs (sequential).
        """
        from hermeneus.src.runtime import LMQLExecutor, ExecutionConfig

        config = ExecutionConfig(model=model, timeout=60, max_retries=1)
        llm = LMQLExecutor(config)

        results = []
        accumulated_context = context

        for verb in self.verbs:
            start = time.time()

            prompt = self._build_verb_prompt(
                verb, accumulated_context, prior_results=results
            )

            try:
                result = await llm.generate_text_async(prompt)

                vr = VerbResult(
                    verb_id=verb["id"],
                    verb_name=verb["name"],
                    verb_number=verb["num"],
                    output=result.output if result.output else "",
                    success=result.status.value == "success",
                    duration_ms=(time.time() - start) * 1000,
                )

                # Context accumulation
                if vr.output:
                    accumulated_context = (
                        f"{accumulated_context}\n\n"
                        f"--- V{verb['num']:02d} {verb['name']} ---\n"
                        f"{vr.output[:500]}"
                    )

            except Exception as e:  # noqa: BLE001
                vr = VerbResult(
                    verb_id=verb["id"],
                    verb_name=verb["name"],
                    verb_number=verb["num"],
                    output="",
                    success=False,
                    error=str(e),
                    duration_ms=(time.time() - start) * 1000,
                )

            results.append(vr)

        return results

    def _build_verb_prompt(
        self,
        verb: Dict,
        context: str,
        prior_results: Optional[List[VerbResult]] = None,
    ) -> str:
        """Build a deep prompt for a single verb, enriched with SKILL.md core

        If depth='+' and prior_results are provided, inject prior verb analyses
        as structured context (verb dialogue).
        """
        axis = self.coordinate.get("axis", "")
        poles = self.coordinate.get("poles", ("", ""))
        q = self.coordinate.get("question", "")

        # SKILL.md からコアセクションを抽出
        skill_core = _extract_skill_core(verb["id"], verb["num"], verb["name"])

        # コアセクションがある場合はプロンプトに注入
        skill_section = ""
        if skill_core:
            skill_section = f"""
## 認知的ガイダンス (SKILL.md より抽出)

{skill_core}
"""

        # depth='+' 時のみ先行定理の分析結果を注入
        prior_section = ""
        if self.depth == "+" and prior_results:
            successful = [vr for vr in prior_results if vr.success and vr.output]
            if successful:
                prior_lines = []
                for vr in successful:
                    # 各先行定理の結論を3行以内で要約
                    summary = vr.output[:300].strip()
                    prior_lines.append(
                        f"- **V{vr.verb_number:02d} {vr.verb_name}**: {summary}"
                    )
                prior_section = (
                    "\n## 先行定理の分析結果\n"
                    "以下の定理が既に分析を完了しています。"
                    "これらの視点を踏まえた上で、あなた独自の視点から分析してください。\n\n"
                    + "\n".join(prior_lines)
                    + "\n"
                )

        return f"""あなたは Hegemonikón 体系の V{verb['num']:02d} {verb['name']} 定理です。

## あなたの役割
{verb['role']}

## 座標系
- 族: {self.series_name} ({self.series_code})
- 座標軸: {axis} ({poles[0]} ↔ {poles[1]})
- 問い: {q}
{skill_section}{prior_section}
## 分析対象
{context[:800]}

## 指示
上記の対象について、あなたの定理の視点から分析してください。
- あなたの役割に忠実に、{verb['role']}
- 認知的ガイダンスに示された思考プロセスに従ってください
- 結論を3行以内で述べてください
- 座標軸 ({poles[0]} ↔ {poles[1]}) のどちら寄りか判定してください

## 出力形式
**V{verb['num']:02d} {verb['name']} の分析**:
(3行以内の分析結果)

**座標判定**: {poles[0]}寄り / {poles[1]}寄り / 均等
"""

    # ─── Phase 2: Limit 収束 ───────────────────────────────────

    async def _phase2_limit(
        self,
        context: str,
        verb_results: List[VerbResult],
        model: str,
    ) -> LimitResult:
        """Phase 2: Limit convergence (C0→C1→C2→C3)

        4回の逐次 LLM 呼び出しで収束演算を実行。
        各ステップが前ステップの結果を入力として受け取る。
        """
        from hermeneus.src.runtime import LMQLExecutor, ExecutionConfig

        config = ExecutionConfig(model=model, timeout=60, max_retries=1)
        llm = LMQLExecutor(config)

        # Build verb summaries
        verb_summaries = ""
        for vr in verb_results:
            if vr.success and vr.output:
                verb_summaries += (
                    f"\n### V{vr.verb_number:02d} {vr.verb_name}\n"
                    f"{vr.output[:600]}\n"
                )

        axis = self.coordinate.get("axis", "")
        poles = self.coordinate.get("poles", ("", ""))

        base_context = f"""対象: {context[:300]}
族: {self.series_name} / 座標軸: {axis} ({poles[0]} ↔ {poles[1]})

4定理の分析結果:
{verb_summaries}"""

        result = LimitResult()

        try:
            # ── C0: Precision Weighting ──
            c0_prompt = f"""{base_context}

## 指示: C0 Precision Weighting
4つの定理の分析結果を読み、各定理にどれだけの重みを置くべきか判定してください。
座標軸 {axis} ({poles[0]} ↔ {poles[1]}) の観点から、各定理の貢献度を0-1の割合で示してください。

1行で回答してください。例: V01: 0.3, V02: 0.2, V03: 0.3, V04: 0.2"""

            c0_result = await llm.generate_text_async(c0_prompt)
            c0_text = c0_result.output.strip() if c0_result.output else ""
            result.c0_pw = c0_text

            # ── C1: 4射の対比 ──
            c1_prompt = f"""{base_context}

重み配分: {c0_text}

## 指示: C1 対比分析
4つの定理の結論のうち、一致している点と相違している点を明示してください。

2行以内で回答してください。"""

            c1_result = await llm.generate_text_async(c1_prompt)
            c1_text = c1_result.output.strip() if c1_result.output else ""
            result.c1_contrast = c1_text

            # ── C2: PW加重融合 ──
            c2_prompt = f"""{base_context}

重み配分: {c0_text}
対比結果: {c1_text}

## 指示: C2 加重融合
C0の重みに基づいて、4つの結論を1つに融合してください。
一致点を核にし、相違点を重み付けで統合してください。

3行以内で回答してください。"""

            c2_result = await llm.generate_text_async(c2_prompt)
            c2_text = c2_result.output.strip() if c2_result.output else ""
            result.c2_fusion = c2_text

            # ── C3: Kalon 普遍性検証 + 最終判定 ──
            c3_prompt = f"""融合結論: {c2_text}

元の4定理: {verb_summaries[:800]}

## 指示: C3 Kalon 普遍性検証
融合結果が特定の定理に偏っていないか検証し、最終結論を確定してください。

以下の形式で回答してください:
KALON: (偏り検証の結果を1行で)
CONCLUSION: (最終結論を1文で)
CONFIDENCE: (0-100の数値のみ)
COORDINATE: ({poles[0]}寄り / {poles[1]}寄り / 均等)"""

            c3_result = await llm.generate_text_async(c3_prompt)
            c3_text = c3_result.output.strip() if c3_result.output else ""

            # Parse structured C3 output using the shared parser
            result = self._parse_limit_output(c3_text)
            
            # Fill in free-form responses from earlier sequential steps
            result.c0_pw = c0_text
            result.c1_contrast = c1_text
            result.c2_fusion = c2_text

            # Fallback if CONCLUSION not found
            if not result.conclusion:
                result.conclusion = c2_text[:200] if c2_text else c3_text[:200]
                result.confidence = max(result.confidence, 0.5)

            # Fallback for c3_kalon
            if not result.c3_kalon and c3_text:
                result.c3_kalon = c3_text[:200]

        except Exception as e:  # noqa: BLE001
            result = LimitResult()
            result.conclusion = f"[Limit Error] {e}"
            result.confidence = 0.0

        return result

    def _parse_limit_output(self, text: str) -> LimitResult:
        """Parse structured Limit output (or C3 final output) into LimitResult"""
        result = LimitResult()

        for line in text.split("\n"):
            line = line.strip()
            # Support both plain labels and Markdown bold format
            clean = line.lstrip("- *").rstrip("*")
            if clean.startswith("C0_PW:") or clean.startswith("C0 PW:"):
                result.c0_pw = clean.split(":", 1)[1].strip()
            elif clean.startswith("C1_CONTRAST:") or clean.startswith("C1 対比:"):
                result.c1_contrast = clean.split(":", 1)[1].strip()
            elif clean.startswith("C2_FUSION:") or clean.startswith("C2 融合:"):
                result.c2_fusion = clean.split(":", 1)[1].strip()
            elif clean.startswith("C3_KALON:") or clean.startswith("C3 Kalon:") or clean.startswith("KALON:"):
                result.c3_kalon = clean.split(":", 1)[1].strip()
            elif clean.startswith("CONCLUSION:"):
                result.conclusion = clean[len("CONCLUSION:"):].strip()
            elif clean.startswith("CONFIDENCE:"):
                try:
                    result.confidence = float(
                        clean[len("CONFIDENCE:"):].strip().rstrip("%")
                    ) / 100.0
                except ValueError:
                    result.confidence = 0.5
            elif clean.startswith("COORDINATE:"):
                result.coordinate_value = clean[len("COORDINATE:"):].strip()

        # If structured parsing failed, use full text as conclusion
        if not result.conclusion and text:
            result.conclusion = text[:200]
            result.confidence = 0.5

        return result

    # ─── Phase 3: 構造化出力 ───────────────────────────────────

    def _phase3_format(
        self,
        verb_results: List[VerbResult],
        limit_result: LimitResult,
    ) -> str:
        """Phase 3: Format the final structured output"""
        lines = [
            f"## /{self.series_id} Peras 結果 ({self.series_name})",
            "",
            f"**Limit 結論**: {limit_result.conclusion}",
            f"**確信度**: {limit_result.confidence:.0%}",
            f"**座標判定**: {limit_result.coordinate_value}",
            "",
            "### Limit 演算",
            f"- **C0 PW**: {limit_result.c0_pw}",
            f"- **C1 対比**: {limit_result.c1_contrast}",
            f"- **C2 融合**: {limit_result.c2_fusion}",
            f"- **C3 Kalon**: {limit_result.c3_kalon}",
            "",
            "### 4定理の寄与",
        ]

        for vr in verb_results:
            status = "✅" if vr.success else "❌"
            summary = vr.output[:100].replace("\n", " ") if vr.output else "(失敗)"
            lines.append(
                f"- {status} V{vr.verb_number:02d} {vr.verb_name}: "
                f"{summary}..."
            )

        return "\n".join(lines)


# =============================================================================
# Convenience Functions
# =============================================================================

async def run_peras(
    series_id: str,
    context: str,
    model: str = "auto",
    depth: str = "+",
) -> PerasResult:
    """Run a single Peras pipeline (async convenience function)

    Example:
        >>> result = await run_peras("t", "プロジェクトの方向性")
        >>> print(result.output)
    """
    pipeline = PerasPipeline(series_id=series_id, model=model, depth=depth)
    return await pipeline.run(context=context, model=model)


def run_peras_sync(
    series_id: str,
    context: str,
    model: str = "auto",
    depth: str = "+",
) -> PerasResult:
    """Run a single Peras pipeline (sync convenience function)"""
    return asyncio.run(run_peras(series_id, context, model, depth))
