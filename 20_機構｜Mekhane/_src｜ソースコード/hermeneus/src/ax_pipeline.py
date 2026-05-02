# PROOF: [L2/インフラ] <- hermeneus/src/ax_pipeline.py /ax 完全自動化パイプライン
"""
Hermēneus AX Pipeline — Peras の Peras

/ax = lim(T · M · K · D · O · C) × X

6つの Series Peras を L3 深度で順次実行し、結果を統合する。
Phase 1: 6 Peras 独立評価 (Sequential)
Phase 2: 6 Limits の統合・対比分析
Phase 3: X-series (15 K₆ エッジ) 張力分析
Phase 4: 最終統合レポート生成

Usage:
    pipeline = AxPipeline(model="auto")
    result = await pipeline.run(context="分析対象テキスト")
    print(result.report)

Origin: 2026-02-22 /ax 完全自動化 (アプローチ B)
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# =============================================================================
# Types
# =============================================================================

# Shared definitions — peras_pipeline.py が Single Source of Truth
from hermeneus.src.peras_pipeline import PERAS_SERIES, PerasResult

# X-series 15 K₆ エッジ — 事前定義付き
# tension_type: 張力の質的カテゴリ
#   contradiction  = 矛盾型: 一方が他方を否定する
#   complement     = 補完型: 異なる側面を照らす
#   scale_mismatch = スケール型: 粒度・抽象度が異なる
#   temporal_gap   = 時間型: 過去/現在/未来の視点衝突
#   value_conflict = 価値型: 望ましさの評価基準が衝突
X_SERIES_EDGES = [
    # --- Tel (Why) のエッジ ---
    {"edge": ("Tel", "Met"), "type": "contradiction",  "hint": "理想 (Why) と現実的手法 (How) の衝突"},
    {"edge": ("Tel", "Kri"), "type": "scale_mismatch", "hint": "目的の壮大さと確信度の限界"},
    {"edge": ("Tel", "Dia"), "type": "scale_mismatch", "hint": "Why の抽象度と Where の具体度"},
    {"edge": ("Tel", "Ore"), "type": "value_conflict",  "hint": "目的の方向性と価値傾向の整合"},
    {"edge": ("Tel", "Chr"), "type": "temporal_gap",    "hint": "理想の時間軸と現実の時制"},
    # --- Met (How) のエッジ ---
    {"edge": ("Met", "Kri"), "type": "complement",     "hint": "手法の選択と確信度の裏付け"},
    {"edge": ("Met", "Dia"), "type": "complement",     "hint": "方法論の粒度とスケールの対応"},
    {"edge": ("Met", "Ore"), "type": "value_conflict", "hint": "効率 (How) と望ましさ (Which) の衝突"},
    {"edge": ("Met", "Chr"), "type": "temporal_gap",   "hint": "手順の順序と時間的制約"},
    # --- Kri (How much) のエッジ ---
    {"edge": ("Kri", "Dia"), "type": "complement",     "hint": "確信度の深さとスケールの広さ"},
    {"edge": ("Kri", "Ore"), "type": "contradiction",  "hint": "冷静な確信と情動的傾向の対立"},
    {"edge": ("Kri", "Chr"), "type": "temporal_gap",   "hint": "現時点の確信度と時間経過での変化"},
    # --- Dia (Where) のエッジ ---
    {"edge": ("Dia", "Ore"), "type": "complement",     "hint": "空間的配置と価値的方向性"},
    {"edge": ("Dia", "Chr"), "type": "complement",     "hint": "空間の構造と時間の流れ"},
    # --- Ore-Chr ---
    {"edge": ("Ore", "Chr"), "type": "value_conflict", "hint": "今の欲求と長期的展望の衝突"},
]

# PerasResult は peras_pipeline.py から import 済み


@dataclass
class EdgeTension:
    """X-series edge tension between two Series"""
    edge: tuple             # e.g., ("Tel", "Met")
    tension_type: str       # "contradiction", "complement", "scale_mismatch", "temporal_gap", "value_conflict"
    tension_level: str      # "low", "medium", "high", "critical"
    tension_score: float    # 0.0 - 1.0
    description: str = ""   # LLM-generated tension description
    expected_type: str = "" # Pre-defined expected type from X_SERIES_EDGES
    pre_score: float = 0.0  # Embedding-based pre-calculated tension score


@dataclass
class AxResult:
    """Complete /ax execution result"""
    context: str
    peras_results: List[PerasResult] = field(default_factory=list)
    edge_tensions: List[EdgeTension] = field(default_factory=list)
    synthesis: str = ""             # Phase 2: 6 Limits comparison
    tension_analysis: str = ""      # Phase 3: X-series analysis
    report: str = ""                # Phase 4: Final integrated report
    success: bool = False
    total_duration_ms: float = 0.0
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    model: str = ""

    def summary(self) -> str:
        """Human-readable summary"""
        lines = [
            "=" * 60,
            "📐 /ax — Peras の Peras 実行結果",
            "=" * 60,
            f"コンテキスト: {self.context[:80]}...",
            f"成功: {'✅' if self.success else '❌'}",
            f"実行時間: {self.total_duration_ms:.0f}ms",
            "",
            "--- Series 別結果 ---",
        ]
        for pr in self.peras_results:
            status = "✅" if pr.success else "❌"
            lines.append(
                f"  {status} /{pr.series_id}+ ({pr.series_name}): "
                f"conf={pr.confidence:.0%} ({pr.duration_ms:.0f}ms)"
            )

        if self.edge_tensions:
            lines.append("")
            lines.append("--- X-series 張力 Top 3 ---")
            sorted_edges = sorted(
                self.edge_tensions, key=lambda e: e.tension_score, reverse=True
            )[:3]
            for et in sorted_edges:
                type_match = "✓" if et.tension_type == et.expected_type else "≠"
                lines.append(
                    f"  ⚡ {et.edge[0]}-{et.edge[1]} [{et.tension_type}{type_match}]: "
                    f"{et.tension_level} (score: {et.tension_score:.2f}, pre: {et.pre_score:.2f}) — {et.description[:60]}"
                )

        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)


# =============================================================================
# Tension Pre-Scorer (TF-IDF — no external model dependency)
# =============================================================================

class TensionPreScorer:
    """テキスト類似度に基づく張力の pre-score 計算

    Strategy:
      1. BGE-M3 Embedder.pairwise_novelty (default — semantic)
      2. TF-IDF + cosine similarity (fallback — stdlib only)

    pre_score = novelty (0.0=identical, 1.0=orthogonal)
    類似テキスト = 低張力, 異なるテキスト = 高張力
    """

    def compute(self, code_to_output: Dict[str, str]) -> Dict[tuple, float]:
        """6 Peras 出力間の新規性 (テキスト距離) から張力 (0.0-1.0) を算出"""
        if not code_to_output or len(code_to_output) < 2:
            return {}

        codes = list(code_to_output.keys())
        texts = [code_to_output[c] for c in codes]

        # 1. Vertex AI (API, no CPU overhead)
        try:
            from mekhane.anamnesis.vertex_embedder import VertexEmbedder
            from mekhane.anamnesis.constants import EMBED_MODEL
            embedder = VertexEmbedder(model_name=EMBED_MODEL, dimension=3072)
            all_novelties = embedder.pairwise_novelty(
                [t[:2000] for t in texts], labels=codes,
            )
            scores = {}
            for edge_def in X_SERIES_EDGES:
                a, b = edge_def["edge"]
                tension = all_novelties.get((a, b), all_novelties.get((b, a), 0.0))
                scores[(a, b)] = tension
            return scores
        except Exception:  # noqa: BLE001
            pass

        # 2. BGE-M3 (local CPU fallback)
        try:
            from mekhane.anamnesis.index import Embedder
            embedder = Embedder()
            all_novelties = embedder.pairwise_novelty(
                [t[:2000] for t in texts], labels=codes,
            )
            scores = {}
            for edge_def in X_SERIES_EDGES:
                a, b = edge_def["edge"]
                tension = all_novelties.get((a, b), all_novelties.get((b, a), 0.0))
                scores[(a, b)] = tension
            return scores
        except (ImportError, RuntimeError):
            pass

        # 3. TF-IDF (stdlib only, last resort)
        return self._compute_tfidf(codes, texts)

    def _compute_tfidf(self, codes: List[str], texts: List[str]) -> Dict[tuple, float]:
        """TF-IDF fallback for environments without BGE-M3."""
        vectors = self._tfidf_vectorize(texts)
        vec_map = {c: v for c, v in zip(codes, vectors)}

        scores = {}
        for edge_def in X_SERIES_EDGES:
            a, b = edge_def["edge"]
            if a in vec_map and b in vec_map:
                sim = self._cosine_sim(vec_map[a], vec_map[b])
                tension = max(0.0, min(1.0, 1.0 - sim))
                scores[(a, b)] = round(tension, 3)
        return scores

    @staticmethod
    def _tfidf_vectorize(texts: List[str]) -> List[Dict[str, float]]:
        """TF-IDF vectorization using only stdlib

        Tokenization strategy:
          - Word-level: whitespace split (English/mixed)
          - Character n-gram (bigram+trigram): always applied (Japanese-safe)

        Returns sparse vectors as dicts: {token: tfidf_score}
        """
        import math
        import re
        from collections import Counter

        def tokenize(text: str) -> List[str]:
            text = text.lower()
            tokens = []

            # Word-level tokens (space-separated)
            words = re.findall(r'[a-z]{3,}', text)
            tokens.extend(words)

            # Character bigrams and trigrams (language-agnostic, works for CJK)
            # Strip whitespace/punctuation for n-gram generation
            clean = re.sub(r'[\s\.,;:!?\-\(\)\[\]\{\}\"\']+', '', text)
            for n in (2, 3):
                for i in range(len(clean) - n + 1):
                    tokens.append(clean[i:i + n])

            return tokens

        tokenized = [tokenize(t) for t in texts]

        # Document frequency
        n_docs = len(texts)
        df: Dict[str, int] = {}
        for words in tokenized:
            for w in set(words):
                df[w] = df.get(w, 0) + 1

        # TF-IDF vectors
        vectors = []
        for words in tokenized:
            tf = Counter(words)
            total = len(words) if words else 1
            vec: Dict[str, float] = {}
            for word, count in tf.items():
                idf = math.log((n_docs + 1) / (df.get(word, 0) + 1)) + 1
                vec[word] = (count / total) * idf
            vectors.append(vec)

        return vectors

    @staticmethod
    def _cosine_sim(a: Dict[str, float], b: Dict[str, float]) -> float:
        """Cosine similarity between two sparse vectors (dicts)"""
        import math

        # Dot product
        common_keys = set(a.keys()) & set(b.keys())
        dot = sum(a[k] * b[k] for k in common_keys)

        # Magnitudes
        mag_a = math.sqrt(sum(v * v for v in a.values())) if a else 0
        mag_b = math.sqrt(sum(v * v for v in b.values())) if b else 0

        if mag_a == 0 or mag_b == 0:
            return 0.0

        return dot / (mag_a * mag_b)


# =============================================================================
# AX Pipeline
# =============================================================================

class AxPipeline:
    """Peras の Peras — /ax 完全自動化パイプライン

    6つの Series Peras を L3 深度で実行し、結果を統合する。
    各 Peras は WorkflowExecutor 経由で LLM を呼び出す。
    """

    def __init__(
        self,
        model: str = "auto",
        verify: bool = True,
        audit: bool = True,
    ):
        self.model = model
        self.verify = verify
        self.audit = audit

    async def run(
        self,
        context: str,
        model: Optional[str] = None,
    ) -> AxResult:
        """Execute the full /ax pipeline

        Args:
            context: Analysis target text
            model: LLM model override

        Returns:
            AxResult with all phases completed
        """
        start_time = time.time()
        model = model or self.model

        result = AxResult(
            context=context,
            model=model,
        )

        try:
            # Phase 1: 6 Peras Sequential Execution (L3)
            result.peras_results = await self._phase1_peras(context, model)

            # Phase 2: Synthesis — 6 Limits の対比分析
            result.synthesis = await self._phase2_synthesis(
                context, result.peras_results, model
            )

            # Phase 3: X-series 張力分析
            result.edge_tensions, result.tension_analysis = (
                await self._phase3_x_series(
                    context, result.peras_results, model
                )
            )

            # Phase 4: 最終統合レポート
            result.report = await self._phase4_report(
                context, result, model
            )

            result.success = all(pr.success for pr in result.peras_results)

        except Exception as e:  # noqa: BLE001
            result.success = False
            result.report = f"[Error] /ax pipeline failed: {e}"

        result.total_duration_ms = (time.time() - start_time) * 1000
        result.completed_at = datetime.now()
        return result

    # ─── Phase 1: 6 Peras Sequential ────────────────────────────

    async def _phase1_peras(
        self,
        context: str,
        model: str,
    ) -> List[PerasResult]:
        """Phase 1: Execute each Peras WF at L3 depth

        Runs T → M → K → D → O → C sequentially.
        Each Peras is a PerasPipeline with 3 internal phases:
          Phase 1: 4定理の個別推論
          Phase 2: Limit 收束 (C0→C1→C2→C3)
          Phase 3: 構造化出力
        """
        from hermeneus.src.peras_pipeline import PerasPipeline

        results = []
        accumulated_context = context

        for series in PERAS_SERIES:
            peras = PerasPipeline(
                series_id=series["id"],
                model=model,
                depth="+",  # /ax always runs at L3
            )

            pr = await peras.run(
                context=accumulated_context,
                model=model,
            )

            # Context accumulation: each Peras builds on previous
            if pr.output:
                accumulated_context = (
                    f"{accumulated_context}\n\n"
                    f"--- {series['name']} Limit ---\n"
                    f"{pr.output[:500]}"
                )

            results.append(pr)

        return results

    # ─── Phase 2: Synthesis ─────────────────────────────────────

    async def _phase2_synthesis(
        self,
        context: str,
        peras_results: List[PerasResult],
        model: str,
    ) -> str:
        """Phase 2: Synthesize the 6 Limits — 4回逐次 LLM 呼び出し

        S1 Synopsis  → 6つの結論を俯瞰し全体像を把握
        S2 Tension   → 矛盾/緊張点を特定
        S3 Synthesis → 対立を統合しメタ結論を生成
        S4 Kalon     → 偏り検証 + 最終判定
        """
        from hermeneus.src.runtime import LMQLExecutor, ExecutionConfig

        config = ExecutionConfig(model=model, timeout=60, max_retries=1)
        llm = LMQLExecutor(config)

        # Build 6 Series の結論テキスト
        limits_text = ""
        for pr in peras_results:
            if pr.success and pr.output:
                limits_text += (
                    f"\n## {pr.series_name} (/{pr.series_id}) "
                    f"[conf: {pr.confidence:.0%}]\n"
                    f"{pr.output[:600]}\n"
                )

        base_ctx = f"対象: {context[:300]}\n\n6 Series の分析結果:\n{limits_text}"

        try:
            # ── S1: Synopsis (全体俯瞰) ──
            s1_prompt = f"""{base_ctx}

## 指示: S1 Synopsis (全体俯瞰)
6つの Series の分析結果を俯瞰し、全体像を1段落で要約してください。
各 Series がどのような視点から何を主張しているかを簡潔にまとめてください。

3行以内で回答してください。"""

            s1_result = await llm.generate_text_async(s1_prompt)
            s1_text = s1_result.output.strip() if s1_result.output else ""

            # ── S2: Tension Detection (対立・緊張の特定) ──
            s2_prompt = f"""{base_ctx}

全体像: {s1_text}

## 指示: S2 Tension Detection (対立・緊張の特定)
6つの Series の結論の中で、矛盾している点や緊張関係にある点を特定してください。
どの Series 間に対立があるかを明示してください。

3行以内で回答してください。"""

            s2_result = await llm.generate_text_async(s2_prompt)
            s2_text = s2_result.output.strip() if s2_result.output else ""

            # ── S3: Synthesis (統合) ──
            s3_prompt = f"""全体像: {s1_text}

対立・緊張: {s2_text}

6 Series の確信度: {', '.join(f'{pr.series_name}={pr.confidence:.0%}' for pr in peras_results if pr.success)}

## 指示: S3 Synthesis (メタ結論の生成)
全体像 (S1) と対立点 (S2) を踏まえて、6つの結論を1つのメタ結論に統合してください。
- 収束点を核にし、対立点を包含する上位概念を見つけてください
- 各 Series の確信度を考慮してください

3行以内で回答してください。"""

            s3_result = await llm.generate_text_async(s3_prompt)
            s3_text = s3_result.output.strip() if s3_result.output else ""

            # ── S4: Kalon (普遍性検証 + 最終出力整形) ──
            s4_prompt = f"""メタ結論: {s3_text}

全体像: {s1_text}
対立点: {s2_text}

## 指示: S4 Kalon (普遍性検証)
メタ結論が特定の Series に偏っていないか検証し、最終的な統合分析を完成させてください。

以下の形式で回答してください:

| 項目 | 内容 |
|:-----|:-----|
| 収束点 | (6つの分析が一致している点) |
| 発散点 | (矛盾または緊張がある点) |
| 盲点 | (いずれの分析でもカバーされていない領域) |
| V[6 Limits] | 低 / 中 / 高 (分散度とその理由) |
| メタ結論 | (S3 の結論を偏り検証後に確定) |"""

            s4_result = await llm.generate_text_async(s4_prompt)
            s4_text = s4_result.output.strip() if s4_result.output else ""

            # 4ステップの結果を統合して返す
            return (
                f"## S1 全体俯瞰\n{s1_text}\n\n"
                f"## S2 対立・緊張\n{s2_text}\n\n"
                f"## S3 メタ結論\n{s3_text}\n\n"
                f"## S4 Kalon 検証\n{s4_text}"
            )

        except Exception as e:  # noqa: BLE001
            return f"[Synthesis Error] {e}"

    # ─── Phase 3: X-series Tension Analysis ─────────────────────

    async def _phase3_x_series(
        self,
        context: str,
        peras_results: List[PerasResult],
        model: str,
    ) -> tuple:
        """Phase 3: Analyze tensions across the 15 K₆ edges

        For each of the 15 edges, evaluate the tension between
        the two connected Series based on their Peras results.
        """
        from hermeneus.src.runtime import LMQLExecutor, ExecutionConfig

        # Build a map of series_code -> output for quick lookup
        code_to_output = {}
        for pr in peras_results:
            if pr.success:
                code_to_output[pr.series_code] = pr.output[:400]

        # Phase 2.5: Compute pre-scores using Embedding
        scorer = TensionPreScorer()
        pre_scores = scorer.compute(code_to_output)

        # Build edges description with pre-defined tension types & pre-score
        edges_desc = ""
        for i, edge_def in enumerate(X_SERIES_EDGES, 1):
            a, b = edge_def["edge"]
            expected_type = edge_def["type"]
            hint = edge_def["hint"]
            a_text = code_to_output.get(a, "(未実行)")[:150]
            b_text = code_to_output.get(b, "(未実行)")[:150]
            pre_score = pre_scores.get((a, b), 0.0)
            
            edges_desc += (
                f"\n### Edge {i}: {a} — {b}\n"
                f"**期待される張力タイプ**: {expected_type} ({hint})\n"
                f"**事前計算スコア (Embedding類似度反転)**: {pre_score:.2f} (参考値: 0.0=低張力, 1.0=高張力)\n"
                f"**{a}**: {a_text}\n"
                f"**{b}**: {b_text}\n"
            )

        tension_prompt = f"""あなたは Hegemonikón 体系の X-series 分析者です。

以下の 15 エッジ (K₆ 完全グラフ) について、2つの Series の結論間の「張力 (tension)」を評価してください。

**張力タイプ** (質的評価):
- **contradiction**: 一方が他方を否定する矛盾型
- **complement**: 異なる側面を照らす補完型
- **scale_mismatch**: 粒度・抽象度が異なるスケール型
- **temporal_gap**: 過去/現在/未来の視点衝突
- **value_conflict**: 望ましさの評価基準の衝突

**張力スコア** (量的評価):
- **low (0.0-0.3)**: 整合的。矛盾なし。
- **medium (0.3-0.6)**: 補完的だが視点の違いが顕著。
- **high (0.6-0.8)**: 緊張がある。一方を優先すると他方が犠牲に。
- **critical (0.8-1.0)**: 根本的矛盾。両立不可能。

各エッジには「期待される張力タイプ」がガイドとして記載されています。
実際の分析結果に基づいて、異なるタイプを選んでも構いません。

## 分析対象
{context[:200]}

## 15 エッジ
{edges_desc}

## 出力形式 (必ずこの形式で)
各エッジについて 1 行ずつ:
EDGE|A-B|TYPE|LEVEL|SCORE|DESCRIPTION

例:
EDGE|Tel-Met|contradiction|high|0.72|目的の理想と方法の現実制約が衝突
"""

        try:
            config = ExecutionConfig(model=model)
            llm = LMQLExecutor(config)
            result = await llm.execute_async(tension_prompt, context="")
            output_text = result.output if hasattr(result, "output") else str(result)

            # Parse tension results
            edge_tensions = self._parse_tension_output(output_text, pre_scores)

            return edge_tensions, output_text

        except Exception as e:  # noqa: BLE001
            return [], f"[X-series Error] {e}"

    def _parse_tension_output(self, text: str, pre_scores: Dict[tuple, float]) -> List[EdgeTension]:
        """Parse LLM tension output into EdgeTension objects

        Expected format: EDGE|A-B|TYPE|LEVEL|SCORE|DESCRIPTION
        """
        # Build lookup for expected types
        expected_types = {}
        for edge_def in X_SERIES_EDGES:
            a, b = edge_def["edge"]
            expected_types[f"{a}-{b}"] = edge_def["type"]
            expected_types[f"{b}-{a}"] = edge_def["type"]  # bidirectional

        tensions = []
        for line in text.split("\n"):
            line = line.strip()
            if not line.startswith("EDGE|"):
                continue
            parts = line.split("|")
            if len(parts) < 6:
                continue
            try:
                edge_str = parts[1]  # "Tel-Met"
                codes = edge_str.split("-")
                if len(codes) != 2:
                    continue
                edge_key = f"{codes[0].strip()}-{codes[1].strip()}"
                tensions.append(EdgeTension(
                    edge=(codes[0].strip(), codes[1].strip()),
                    tension_type=parts[2].strip(),
                    tension_level=parts[3].strip(),
                    tension_score=float(parts[4].strip()),
                    description=parts[5].strip() if len(parts) > 5 else "",
                    expected_type=expected_types.get(edge_key, ""),
                    pre_score=pre_scores.get((codes[0].strip(), codes[1].strip()), 0.0),
                ))
            except (ValueError, IndexError):
                continue
        return tensions

    # ─── Phase 4: Final Report ──────────────────────────────────

    async def _phase4_report(
        self,
        context: str,
        ax_result: "AxResult",
        model: str,
    ) -> str:
        """Phase 4: Generate the final integrated report

        Combines all phases into a single, actionable report.
        """
        from hermeneus.src.runtime import LMQLExecutor, ExecutionConfig

        # Build report input
        peras_summary = ""
        for pr in ax_result.peras_results:
            status = "✅" if pr.success else "❌"
            peras_summary += (
                f"- {status} **{pr.series_name}** (/{pr.series_id}+): "
                f"{pr.output[:200] if pr.output else '(失敗)'}...\n"
            )

        top_tensions = ""
        if ax_result.edge_tensions:
            sorted_t = sorted(
                ax_result.edge_tensions,
                key=lambda e: e.tension_score,
                reverse=True,
            )[:5]
            for et in sorted_t:
                top_tensions += (
                    f"- ⚡ **{et.edge[0]}—{et.edge[1]}**: "
                    f"{et.tension_level} ({et.tension_score:.2f}) — "
                    f"{et.description}\n"
                )

        report_prompt = f"""あなたは Hegemonikón 統合レポート生成者です。

以下の全分析結果を統合し、最終レポートを生成してください。

## 対象
{context[:300]}

## Phase 1: 6 Series 分析結果
{peras_summary}

## Phase 2: 統合分析
{ax_result.synthesis[:600] if ax_result.synthesis else '(未実行)'}

## Phase 3: X-series 張力 (Top 5)
{top_tensions if top_tensions else '(未実行)'}

## レポート形式

# /ax 統合レポート

## 1. 核心 (What is the essence?)
(1-2文で核心を述べる)

## 2. 6 次元の収束
(6 Series がどこで合意したか)

## 3. 張力マップ
(最も重要な緊張関係とその意味)

## 4. 盲点と未知
(どの視座からも見えなかったもの)

## 5. 推奨アクション
(次に取るべき具体的行動)

## 6. 確信度
(統合判断の確信度と根拠)
"""

        try:
            config = ExecutionConfig(model=model)
            llm = LMQLExecutor(config)
            result = await llm.execute_async(report_prompt, context="")
            return result.output if hasattr(result, "output") else str(result)
        except Exception as e:  # noqa: BLE001
            return f"[Report Error] {e}"


# =============================================================================
# Convenience Functions
# =============================================================================

async def run_ax(
    context: str,
    model: str = "auto",
    verify: bool = True,
    audit: bool = True,
) -> AxResult:
    """Run /ax pipeline (async convenience function)

    Example:
        >>> result = await run_ax("HGK体系の方向性について")
        >>> print(result.report)
    """
    pipeline = AxPipeline(model=model, verify=verify, audit=audit)
    return await pipeline.run(context=context, model=model)


def run_ax_sync(
    context: str,
    model: str = "auto",
    verify: bool = True,
    audit: bool = True,
) -> AxResult:
    """Run /ax pipeline (sync convenience function)"""
    return asyncio.run(run_ax(context, model, verify, audit))
