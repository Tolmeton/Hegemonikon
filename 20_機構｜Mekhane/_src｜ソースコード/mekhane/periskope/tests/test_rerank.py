# PROOF: mekhane/periskope/tests/test_rerank.py
# PURPOSE: periskope モジュールの rerank に対するテスト
"""Tests for W4 Rerank: effectiveness and batch performance.

Validates that:
  1. Embedder.similarity_batch() produces correct scores
  2. _rerank_results improves ordering (relevant > irrelevant)
  3. max_rerank correctly limits reranked results
"""
import pytest
from unittest.mock import MagicMock, patch
from mekhane.periskope.models import SearchResult, SearchSource


def _make_result(title: str, snippet: str, relevance: float = 0.5) -> SearchResult:
    """Create a SearchResult with given fields."""
    return SearchResult(
        title=title,
        snippet=snippet,
        url=f"https://example.com/{title.replace(' ', '_')}",
        source=SearchSource.SEARXNG,
        relevance=relevance,
    )


class TestSimilarityBatch:
    """Embedder.similarity_batch() unit tests (mocked)."""

    def test_empty_documents(self):
        """Empty doc list returns empty scores."""
        from mekhane.anamnesis.index import Embedder

        embedder = MagicMock(spec=Embedder)
        embedder.similarity_batch = Embedder.similarity_batch.__get__(embedder)
        embedder.embed_batch = MagicMock(return_value=[[1.0, 0.0]])

        scores = embedder.similarity_batch("query", [])
        assert scores == []

    def test_single_document(self):
        """Single doc returns single score."""
        from mekhane.anamnesis.index import Embedder

        embedder = MagicMock(spec=Embedder)
        embedder.similarity_batch = Embedder.similarity_batch.__get__(embedder)
        # query=[1,0], doc=[0.8,0.6] → dot = 0.8
        embedder.embed_batch = MagicMock(return_value=[
            [1.0, 0.0],   # query
            [0.8, 0.6],   # doc
        ])

        scores = embedder.similarity_batch("query", ["doc1"])
        assert len(scores) == 1
        assert abs(scores[0] - 0.8) < 1e-6

    def test_scores_clamped(self):
        """Scores are clamped to [0.0, 1.0]."""
        from mekhane.anamnesis.index import Embedder

        embedder = MagicMock(spec=Embedder)
        embedder.similarity_batch = Embedder.similarity_batch.__get__(embedder)
        # Negative dot product → clamped to 0.0
        embedder.embed_batch = MagicMock(return_value=[
            [1.0, 0.0],    # query
            [-1.0, 0.0],   # anti-correlated doc
        ])

        scores = embedder.similarity_batch("q", ["d"])
        assert scores[0] == 0.0  # clamped


class TestRerankResults:
    """_rerank_results integration tests (mocked embedder)."""

    def _make_engine(self):
        """Create engine with mocked embedder."""
        from mekhane.periskope.engine import PeriskopeEngine
        engine = PeriskopeEngine.__new__(PeriskopeEngine)
        engine._embedder = MagicMock()
        engine._search_cache = {}
        engine._config = {}  # W4 rerank reads from config
        engine.nl_client = None  # Cloud NL API client (not used in tests)
        engine.cloud_nl_cfg = {}  # Cloud NL config
        engine.llm_reranker = None  # LLM reranker (not used in unit tests)
        engine.decay_type_override = None
        engine.alpha_schedule_override = None
        return engine

    def test_rerank_improves_ordering(self):
        """Relevant results should be ranked higher after reranking."""
        engine = self._make_engine()

        # Simulate: irrelevant doc is ranked first, relevant doc is ranked last
        results = [
            _make_result("cat videos", "funny cats", relevance=0.9),
            _make_result("machine learning basics", "neural networks", relevance=0.1),
        ]

        # Embedder says: second doc is more similar to query
        engine._embedder.similarity_batch = MagicMock(return_value=[0.2, 0.9])

        reranked = engine._rerank_results("neural network training", results)

        assert reranked[0].title == "machine learning basics"
        assert reranked[1].title == "cat videos"
        assert reranked[0].relevance > reranked[1].relevance

    def test_max_rerank_limits_scope(self):
        """Only top max_rerank results should be reranked."""
        engine = self._make_engine()

        results = [_make_result(f"doc{i}", f"snippet{i}", relevance=0.5)
                    for i in range(10)]

        # Only 3 docs get reranked
        engine._embedder.similarity_batch = MagicMock(return_value=[0.8, 0.6, 0.4])

        reranked = engine._rerank_results("query", results, max_rerank=3)

        assert len(reranked) == 10
        # First 3 have new scores
        assert reranked[0].relevance == 0.8
        # Remaining 7 keep original relevance
        assert reranked[3].relevance == 0.5

    def test_empty_results(self):
        """Empty input returns empty output."""
        engine = self._make_engine()
        assert engine._rerank_results("q", []) == []

    def test_rerank_ndcg_improvement(self):
        """Reranking should improve NDCG over random ordering."""
        engine = self._make_engine()

        # Deliberately mis-ordered results
        results = [
            _make_result("noise", "irrelevant content", relevance=0.9),
            _make_result("partial match", "somewhat related", relevance=0.7),
            _make_result("best answer", "exactly what we need", relevance=0.3),
        ]

        # Embedder correctly identifies relevance
        engine._embedder.similarity_batch = MagicMock(return_value=[0.1, 0.5, 0.95])

        reranked = engine._rerank_results("specific technical query", results)

        # After reranking, best answer should be first
        assert reranked[0].title == "best answer"

        # Compute simple DCG improvement
        pre_dcg = sum(r.relevance / (i + 2) for i, r in enumerate(results))
        post_dcg = sum(r.relevance / (i + 2) for i, r in enumerate(reranked))
        assert post_dcg >= pre_dcg, "Reranking should not worsen DCG"
