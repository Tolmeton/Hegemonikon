from __future__ import annotations
# PROOF: mekhane/periskope/quality_metrics.py
# PURPOSE: periskope モジュールの quality_metrics
"""
Search quality metrics for Periskopē.

Provides quantitative assessment of search result quality:
- NDCG@10: Pipeline sort health (are results ordered by relevance?)
- Source Entropy: Shannon Diversity Index (source diversity)
- Coverage Score: Query concept coverage in results
- Score Spread: LLM discrimination power (can it tell good from bad?)
- Coherence Score: Linkage Coherence Invariance (result semantic consistency)

These metrics enable data-driven search improvement by measuring
what "good search" means quantitatively.
"""


import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mekhane.periskope.models import SearchResult


# PURPOSE: [L2-auto] QualityMetrics のクラス定義
@dataclass
class QualityMetrics:
    """Search quality metrics for a single research session."""

    FORMAT_BENCHMARK = "benchmark"  # Format specifier for f"{m:benchmark}"

    ndcg_at_10: float       # 0.0-1.0 (1.0 = pipeline sort is healthy)
    source_entropy: float   # 0.0-log₂(N) (higher = more diverse)
    max_entropy: float      # log₂(N) for normalization
    coverage_score: float   # 0.0-1.0 (1.0 = all query terms covered)
    score_spread: float = 0.0  # 0.0-1.0 (higher = LLM discriminates well)
    coherence_score: float = 0.0  # 0.0-1.0 (Linkage Coherence Invariance coh(c))
    diversity_weight: float = 0.3  # 0.0=precision, 1.0=diversity

    # PURPOSE: [L2-auto] source_entropy_normalized の関数定義
    @property
    def source_entropy_normalized(self) -> float:
        """Normalized entropy (0.0-1.0)."""
        if self.max_entropy == 0:
            return 0.0
        return min(1.0, self.source_entropy / self.max_entropy)

    # PURPOSE: [L2-auto] overall_score の関数定義
    @property
    def overall_score(self) -> float:
        """Weighted overall quality score (0.0-1.0).

        Weights:
          NDCG      = 0.10 (pipeline health — low = bug, not quality indicator)
          Entropy   = 0.10 (source diversity)
          Coverage  = 0.30 (query concept coverage — most important)
          Spread    = 0.30 (LLM discrimination — only meaningful with reranker)
          Coherence = 0.20 (Linkage Coherence Invariance — semantic consistency)
        """
        return (
            0.10 * self.ndcg_at_10
            + 0.10 * self.source_entropy_normalized
            + 0.30 * self.coverage_score
            + 0.30 * self.score_spread
            + 0.20 * self.coherence_score
        )

    def __format__(self, format_spec: str) -> str:
        """Format matching rules via format specifiers."""
        if format_spec == self.FORMAT_BENCHMARK:
            return (
                f"{self.ndcg_at_10:.2f} | {self.source_entropy_normalized:.2f} | "
                f"{self.coverage_score:.2f} | **{self.overall_score:.2f}**"
            )
        return super().__format__(format_spec)

    # PURPOSE: [L2-auto] summary の関数定義
    def summary(self) -> str:
        """One-line summary."""
        return (
            f"Quality: {self.overall_score:.0%} "
            f"(NDCG={self.ndcg_at_10:.2f}, "
            f"Entropy={self.source_entropy_normalized:.2f}, "
            f"Coverage={self.coverage_score:.2f}, "
            f"Spread={self.score_spread:.2f}, "
            f"Coherence={self.coherence_score:.2f})"
        )

    # PURPOSE: [L2-auto] markdown_section の関数定義
    def markdown_section(self) -> str:
        """Markdown section for ResearchReport."""
        emoji = "🟢" if self.overall_score >= 0.7 else "🟡" if self.overall_score >= 0.4 else "🔴"
        lines = [
            "## Search Quality Metrics",
            "",
            f"> {emoji} Overall: **{self.overall_score:.0%}**",
            "",
            "| Metric | Score | Meaning |",
            "|:-------|------:|:--------|",
            f"| NDCG@10 | {self.ndcg_at_10:.2f} | Pipeline sort health (low = ordering bug) |",
            f"| Source Entropy | {self.source_entropy_normalized:.2f} | Source diversity (balanced across engines?) |",
            f"| Coverage | {self.coverage_score:.2f} | Query concept coverage (all terms found?) |",
            f"| Score Spread | {self.score_spread:.2f} | LLM discrimination (can it tell good from bad?) |",
            f"| Coherence | {self.coherence_score:.2f} | Linkage coh(c) — semantic consistency (≥0.7 = good) |",
            "",
        ]

        # Coherence Invariance ゲート: coh(c) < τ_coherence の場合に警告
        # #6修正: insert(-1) は最後から2番目に挿入するため、append で末尾追加に変更
        if self.coherence_score < 0.7 and self.coherence_score > 0.0:
            lines.append("")
            lines.append("> ⚠️ **Coherence below threshold** (τ=0.7): "
                         f"coh(c)={self.coherence_score:.2f}. "
                         "Results may lack semantic consistency.")

        return "\n".join(lines)


# PURPOSE: [L2-auto] compute_quality_metrics の関数定義
def compute_quality_metrics(
    query: str,
    results: list[SearchResult],
    source_counts: dict[str, int],
    k: int = 10,
    pre_rerank_results: list[SearchResult] | None = None,
    diversity_weight: float = 0.3,
) -> QualityMetrics:
    """Compute all quality metrics for a search session.

    Args:
        query: Original search query.
        results: Search results (post-rerank, post-filter).
        source_counts: Source name → result count mapping.
        k: Cutoff for NDCG (default: 10).
        pre_rerank_results: Results BEFORE reranking (for meaningful NDCG).
            If provided, NDCG measures how much reranking improved order.
            If None, falls back to self-comparison (always 1.0).
        diversity_weight: Balance between precision and diversity (0.0-1.0).

    Returns:
        QualityMetrics with all three scores.
    """
    return QualityMetrics(
        ndcg_at_10=_ndcg(
            results, k,
            pre_rerank_results=pre_rerank_results,
            source_count=sum(1 for c in source_counts.values() if c > 0),
        ),
        source_entropy=_source_entropy(source_counts),
        max_entropy=_max_entropy(source_counts),
        coverage_score=_coverage(query, results),
        score_spread=_score_spread(results),
        coherence_score=_coherence_score(results),
        diversity_weight=diversity_weight,
    )


# PURPOSE: [L2-auto] _ndcg の関数定義
def _ndcg(
    results: list[SearchResult],
    k: int = 10,
    pre_rerank_results: list[SearchResult] | None = None,
    source_count: int = 0,
) -> float:
    """Normalized Discounted Cumulative Gain at k.

    Measures the quality of result ordering.

    When pre_rerank_results is provided:
      DCG = uses pre-rerank relevance scores (original order)
      IDCG = uses ideal (sorted by post-rerank relevance desc)
      NDCG < 1.0 means reranking improved the order.

    Without pre_rerank_results: post-rerank self-comparison (always 1.0).

    NDCG = DCG / IDCG
    DCG = Σ (rel_i / log₂(i+1))  for i = 1..k
    """
    if not results:
        return 0.0

    # Ideal relevances: post-rerank scores sorted desc (the best possible order)
    ideal_relevances = sorted(
        [r.relevance for r in results[:k]], reverse=True,
    )

    if pre_rerank_results:
        # Create a lookup for true relevance (ground truth = post-rerank LLM scores)
        # We match by (title, url) because SearchResult doesn't have a unique ID,
        # and LLMReranker creates new dataclass instances rather than mutating in-place.
        true_relevance_map = {}
        for r in results:
            key = (r.title, r.url)
            true_relevance_map[key] = r.relevance

        # DCG from pre-rerank order: how good was the original ordering?
        pre_top_k = pre_rerank_results[:k]
        actual_relevances = []
        for r in pre_top_k:
            key = (r.title, r.url)
            # If item was filtered out in Phase 1.75 (score < 0.25), it's missing from `results`.
            # We assign 0.0 for dropped items to penalize the original ranking.
            actual_relevances.append(true_relevance_map.get(key, 0.0))
    else:
        # Fallback: post-rerank (self-comparison, always 1.0)
        actual_relevances = [r.relevance for r in results[:k]]

    # DCG of actual order
    dcg = sum(
        rel / math.log2(i + 2)  # i+2 because i is 0-indexed
        for i, rel in enumerate(actual_relevances)
    )

    # IDCG: best possible order
    idcg = sum(
        rel / math.log2(i + 2)
        for i, rel in enumerate(ideal_relevances)
    )

    if idcg == 0:
        return 0.0

    ndcg = min(1.0, dcg / idcg)

    # H3: Single-source discount — self-comparison NDCG=1.0 is uninformative
    if source_count <= 1 and pre_rerank_results is None:
        ndcg = min(ndcg, 0.5)

    return ndcg


# PURPOSE: Score spread — LLM discrimination power (判別力)
def _score_spread(results: list[SearchResult], k: int = 10) -> float:
    """Score spread of top-k results.

    Measures how well the scoring system discriminates between results.
    High spread (→ 1.0) = clear separation between good and bad results.
    Low spread (→ 0.0) = all results scored similarly (no discrimination).

    Uses standard deviation normalized to [0.0, 1.0].
    For scores in [0, 1], max stdev ≈ 0.5 (all 0s and 1s equally).
    """
    if len(results) < 2:
        return 0.0

    scores = [r.relevance for r in results[:k]]
    n = len(scores)
    if n < 2:
        return 0.0

    mean = sum(scores) / n
    variance = sum((s - mean) ** 2 for s in scores) / n
    stdev = variance ** 0.5

    # Normalize: max possible stdev for [0,1] scores is 0.5
    # Scale so that stdev=0.3 → spread=1.0 (practical max for search results)
    spread = min(1.0, stdev / 0.3)
    return spread


# PURPOSE: [L2-auto] _source_entropy の関数定義
def _source_entropy(source_counts: dict[str, int]) -> float:
    """Shannon Entropy of source distribution.

    H = -Σ p_i · log₂(p_i)

    High entropy = results come from many sources (good).
    Low entropy = dominated by one source (bad).
    """
    total = sum(source_counts.values())
    if total == 0:
        return 0.0

    entropy = 0.0
    for count in source_counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    return entropy


# PURPOSE: [L2-auto] _max_entropy の関数定義
def _max_entropy(source_counts: dict[str, int]) -> float:
    """Maximum possible entropy for normalization.

    H_max = log₂(N) where N = number of active sources.
    """
    active_sources = sum(1 for c in source_counts.values() if c > 0)
    if active_sources <= 1:
        return 0.0
    return math.log2(active_sources)


# PURPOSE: [L2-auto] _coverage の関数定義
def _coverage(query: str, results: list[SearchResult]) -> float:
    """Query concept coverage score.

    Measures what fraction of query terms appear in the search results.
    Strips common stopwords and short tokens.
    """
    # Extract meaningful query terms (>= 2 chars, skip stopwords)
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "and", "or", "not", "in", "on", "at", "to", "for", "of", "with",
        "by", "from", "up", "about", "into", "through", "during",
        "の", "は", "が", "を", "に", "で", "と", "も", "や", "か",
        "する", "した", "ある", "いる", "なる", "れる", "られる",
    }

    query_terms = set()
    for word in re.findall(r'\w+', query.lower()):
        if len(word) >= 2 and word not in stopwords:
            query_terms.add(word)

    if not query_terms:
        return 1.0  # No terms to check

    # Check which terms appear in result content (2-level matching)
    all_content = " ".join(
        f"{r.title} {r.content} {r.snippet}".lower()
        for r in results
    )

    # Extract all words from content for substring matching
    content_words = set(re.findall(r'\w+', all_content))

    covered = 0
    for term in query_terms:
        # L1: Exact substring match in full content (handles multi-word)
        if term in all_content:
            covered += 1
            continue

        # L2: Partial match — term is contained in a content word
        # e.g., "mechanism" matches "mechanisms", "key" matches "keyword"
        if any(term in cw or cw in term for cw in content_words if len(cw) >= 3):
            covered += 0.5  # Partial matches count as half

    return covered / len(query_terms)


# PURPOSE: F6 Linkage Coherence Invariance — 検索結果の意味的一貫性
def _coherence_score(results: list[SearchResult]) -> float:
    """検索結果の意味的一貫性 (Coherence Invariance) を推定。

    Linkage 理論の coh(c) = 内部冗長性の逆数。
    高い coherence = 結果が良くまとまった一貫したセット。
    低い coherence = 結果がバラバラで一貫性がない。

    τ_coherence = 0.7 を品質ゲートとして使用。

    TF-IDF コサイン類似度で計算。API 呼出し不要。
    sklearn 未インストール時は 0.0 (計算不可) を返す。
    """
    if len(results) < 3:
        return 0.0  # 結果が少なすぎて判定不可

    texts = [
        f"{r.title} {r.content or ''} {r.snippet or ''}"
        for r in results[:20]  # 計算コスト制限
    ]
    # 空テキストをフィルタ
    texts = [t for t in texts if len(t.strip()) > 10]
    if len(texts) < 3:
        return 0.0

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(max_features=500, stop_words="english")
        tfidf = vectorizer.fit_transform(texts)
        sim_matrix = cosine_similarity(tfidf)
        n = sim_matrix.shape[0]
        # 対角を除いた平均類似度
        total = float(sim_matrix.sum()) - n
        coherence = total / (n * (n - 1)) if n > 1 else 0.0
        return max(0.0, min(1.0, coherence))
    except (ValueError, ImportError):
        return 0.0  # sklearn 未インストール時は計算不可


# Default metrics log path
_METRICS_LOG = Path(__file__).parent / "metrics.jsonl"


# PURPOSE: [L2-auto] log_metrics の関数定義
def log_metrics(
    query: str,
    metrics: QualityMetrics,
    source_counts: dict[str, int],
    elapsed: float = 0.0,
    path: Path | None = None,
) -> Path:
    """Append quality metrics to JSONL log file.

    Args:
        query: Original search query.
        metrics: Computed quality metrics.
        source_counts: Source distribution.
        elapsed: Research elapsed time in seconds.
        path: Output JSONL path (default: periskope/metrics.jsonl).

    Returns:
        Path to the log file.
    """
    log_path = path or _METRICS_LOG
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "ndcg_at_10": round(metrics.ndcg_at_10, 4),
        "source_entropy": round(metrics.source_entropy, 4),
        "source_entropy_norm": round(metrics.source_entropy_normalized, 4),
        "coverage_score": round(metrics.coverage_score, 4),
        "coherence_score": round(metrics.coherence_score, 4),
        "score_spread": round(metrics.score_spread, 4),
        "overall_score": round(metrics.overall_score, 4),
        "source_counts": source_counts,
        "elapsed_seconds": round(elapsed, 2),
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return log_path
