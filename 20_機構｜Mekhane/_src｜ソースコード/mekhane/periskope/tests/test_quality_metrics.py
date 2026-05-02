# PROOF: mekhane/periskope/tests/test_quality_metrics.py
# PURPOSE: periskope モジュールの quality_metrics に対するテスト
"""
Tests for search quality metrics.
"""

import math

import pytest
from mekhane.periskope.quality_metrics import (
    QualityMetrics,
    compute_quality_metrics,
    _ndcg,
    _source_entropy,
    _max_entropy,
    _coverage,
)
from mekhane.periskope.models import SearchResult, SearchSource


# ── NDCG Tests ──

def test_ndcg_perfect_ranking():
    """Results already sorted by relevance desc → NDCG = 1.0."""
    results = [
        SearchResult(source=SearchSource.SEARXNG, title="A", relevance=1.0),
        SearchResult(source=SearchSource.SEARXNG, title="B", relevance=0.8),
        SearchResult(source=SearchSource.SEARXNG, title="C", relevance=0.5),
    ]
    assert _ndcg(results, source_count=3) == pytest.approx(1.0)


def test_ndcg_with_pre_rerank():
    """NDCG uses post-rerank relevance as true labels for pre-rerank order."""
    # Final scored results (Ground truth)
    post_results = [
        SearchResult(source=SearchSource.SEARXNG, title="A", url="url1", relevance=0.9),
        SearchResult(source=SearchSource.SEARXNG, title="B", url="url2", relevance=0.5),
        SearchResult(source=SearchSource.SEARXNG, title="C", url="url3", relevance=0.1),
    ]
    # Original order (Pre-rerank): B -> C -> A
    pre_results = [
        SearchResult(source=SearchSource.SEARXNG, title="B", url="url2", relevance=1.0),
        SearchResult(source=SearchSource.SEARXNG, title="C", url="url3", relevance=1.0),
        SearchResult(source=SearchSource.SEARXNG, title="A", url="url1", relevance=1.0),
    ]
    
    # IDCG is calculated from [0.9, 0.5, 0.1]
    # DCG is calculated from [0.5, 0.1, 0.9]
    # This should be < 1.0 because the original order was sub-optimal.
    ndcg_score = _ndcg(post_results, k=3, pre_rerank_results=pre_results, source_count=3)
    assert ndcg_score < 1.0
    assert ndcg_score > 0.0


def test_ndcg_single_source_discount():
    """H3: Single-source self-comparison → capped at 0.5."""
    results = [
        SearchResult(source=SearchSource.SEARXNG, title="A", relevance=1.0),
        SearchResult(source=SearchSource.SEARXNG, title="B", relevance=0.8),
    ]
    # source_count=1, no pre_rerank → H3 discount applied
    assert _ndcg(results, source_count=1) == pytest.approx(0.5)
    # source_count=0 (default) also triggers H3
    assert _ndcg(results) == pytest.approx(0.5)


def test_ndcg_reverse_ranking():
    """Worst ranking → NDCG < 1.0."""
    results = [
        SearchResult(source=SearchSource.SEARXNG, title="A", relevance=0.1),
        SearchResult(source=SearchSource.SEARXNG, title="B", relevance=0.5),
        SearchResult(source=SearchSource.SEARXNG, title="C", relevance=1.0),
    ]
    assert _ndcg(results) < 1.0


def test_ndcg_empty():
    """No results → NDCG = 0.0."""
    assert _ndcg([]) == 0.0


def test_ndcg_single_result():
    """Single result → NDCG = 1.0."""
    results = [SearchResult(source=SearchSource.SEARXNG, title="A", relevance=0.7)]
    assert _ndcg(results, source_count=2) == pytest.approx(1.0)


# ── Source Entropy Tests ──

def test_entropy_single_source():
    """Single source → entropy = 0."""
    assert _source_entropy({"searxng": 10}) == 0.0


def test_entropy_uniform_distribution():
    """Uniform distribution → max entropy."""
    counts = {"a": 5, "b": 5, "c": 5, "d": 5}
    expected = math.log2(4)  # 2.0
    assert _source_entropy(counts) == pytest.approx(expected)


def test_entropy_skewed():
    """Skewed distribution → lower entropy."""
    uniform = _source_entropy({"a": 5, "b": 5})
    skewed = _source_entropy({"a": 9, "b": 1})
    assert skewed < uniform


def test_entropy_empty():
    """Empty counts → 0."""
    assert _source_entropy({}) == 0.0


def test_max_entropy():
    """Max entropy = log₂(active sources)."""
    assert _max_entropy({"a": 5, "b": 5, "c": 5}) == pytest.approx(math.log2(3))
    assert _max_entropy({"a": 5, "b": 0}) == 0.0  # Only 1 active
    assert _max_entropy({}) == 0.0


# ── Coverage Tests ──

def test_coverage_all_terms_found():
    """All query terms in results → 1.0."""
    results = [
        SearchResult(
            source=SearchSource.SEARXNG,
            title="Free Energy Principle",
            content="The free energy principle explains active inference.",
        ),
    ]
    score = _coverage("free energy principle", results)
    assert score == pytest.approx(1.0)


def test_coverage_no_terms_found():
    """No query terms in results → 0.0."""
    results = [
        SearchResult(
            source=SearchSource.SEARXNG,
            title="Cooking Recipes",
            content="How to make pasta.",
        ),
    ]
    score = _coverage("quantum gravity theory", results)
    assert score == pytest.approx(0.0)


def test_coverage_partial():
    """Some terms found → between 0 and 1."""
    results = [
        SearchResult(
            source=SearchSource.SEARXNG,
            title="Energy Systems",
            content="Solar energy is renewable.",
        ),
    ]
    score = _coverage("free energy principle", results)
    assert 0.0 < score < 1.0


def test_coverage_empty_query():
    """Empty query → 1.0 (nothing to check)."""
    results = [SearchResult(source=SearchSource.SEARXNG, title="X", content="Y")]
    assert _coverage("", results) == 1.0


# ── QualityMetrics Tests ──

def test_metrics_overall_score():
    """Overall score is weighted average."""
    m = QualityMetrics(
        ndcg_at_10=1.0,
        source_entropy=math.log2(4),
        max_entropy=math.log2(4),
        coverage_score=1.0,
        score_spread=1.0,
        coherence_score=1.0,
    )
    assert m.overall_score == pytest.approx(1.0)


def test_metrics_summary():
    """Summary produces readable string."""
    m = QualityMetrics(ndcg_at_10=0.8, source_entropy=1.5, max_entropy=2.0, coverage_score=0.9)
    s = m.summary()
    assert "Quality:" in s
    assert "NDCG" in s


def test_metrics_markdown():
    """Markdown section is valid."""
    m = QualityMetrics(ndcg_at_10=0.85, source_entropy=1.5, max_entropy=2.0, coverage_score=0.7)
    md = m.markdown_section()
    assert "## Search Quality Metrics" in md
    assert "NDCG@10" in md
    assert "🟢" in md or "🟡" in md or "🔴" in md


# ── Integration Test ──

def test_compute_quality_metrics():
    """Full pipeline produces valid metrics."""
    results = [
        SearchResult(source=SearchSource.SEARXNG, title="FEP Paper", content="free energy principle", relevance=0.9),
        SearchResult(source=SearchSource.BRAVE, title="Active Inference", content="active inference framework", relevance=0.7),
        SearchResult(source=SearchSource.GNOSIS, title="Markov Blankets", content="markov blanket boundary", relevance=0.5),
    ]
    source_counts = {"searxng": 1, "brave": 1, "gnosis": 1}
    m = compute_quality_metrics("free energy principle", results, source_counts)
    assert 0.0 <= m.ndcg_at_10 <= 1.0
    assert m.source_entropy > 0
    assert 0.0 <= m.coverage_score <= 1.0
    assert 0.0 <= m.overall_score <= 1.0
