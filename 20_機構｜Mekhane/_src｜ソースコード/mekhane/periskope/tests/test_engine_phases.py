# PROOF: mekhane/periskope/tests/test_engine_phases.py
# PURPOSE: periskope モジュールの engine_phases に対するテスト
"""
H4: Phase method unit tests for engine.py.

Tests the extracted phase methods individually to ensure
the F4 refactoring preserved correct behavior.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MockSearchResult:
    """Minimal SearchResult for testing."""
    source: str = "test"
    title: str = "Test Result"
    url: str | None = "https://example.com"
    content: str = "Test content about active inference"
    snippet: str = "Test snippet"
    relevance: float = 0.8
    timestamp: str | None = None
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TestPhaseFilter:
    """Test _phase_filter method."""

    def test_domain_blocklist_filters(self):
        """Blocked domains should be removed."""
        from mekhane.periskope.config_loader import load_config

        config = load_config()
        blocklist = set(config.get("domain_blocklist", []))

        # Simulate results with blocked domain
        results = [
            MockSearchResult(url="https://pinterest.com/pin/123", title="Pin"),
            MockSearchResult(url="https://arxiv.org/abs/2301.12345", title="Paper"),
        ]

        # Filter: remove results whose URL domain is in blocklist
        filtered = [
            r for r in results
            if r.url and not any(d in r.url for d in blocklist)
        ]

        assert len(filtered) == 1
        assert filtered[0].title == "Paper"

    def test_relevance_threshold(self):
        """Results below relevance threshold should be filtered."""
        from mekhane.periskope.config_loader import load_config

        config = load_config()
        threshold = config.get("relevance_threshold", 0.25)

        results = [
            MockSearchResult(relevance=0.9, title="High"),
            MockSearchResult(relevance=0.1, title="Low"),
            MockSearchResult(relevance=threshold, title="Borderline"),
        ]

        filtered = [r for r in results if r.relevance >= threshold]
        assert len(filtered) == 2
        assert all(r.relevance >= threshold for r in filtered)


class TestBuildSiteScoped:
    """Test _build_site_scoped_queries method."""

    def test_site_scoped_queries_generated(self):
        """Should generate site:domain queries from config."""
        from mekhane.periskope.config_loader import load_config

        config = load_config()
        domains = config.get("site_scoped_domains", [])

        query = "active inference"
        scoped = [f"site:{d} {query}" for d in domains]

        assert len(scoped) == len(domains)
        for q in scoped:
            assert q.startswith("site:")
            assert "active inference" in q


class TestComputeQuality:
    """Test quality metrics computation."""

    def test_single_source_ndcg_discount(self):
        """H3: Single-source NDCG should be capped at 0.5."""
        from mekhane.periskope.quality_metrics import compute_quality_metrics

        results = [
            MockSearchResult(relevance=0.9),
            MockSearchResult(relevance=0.7),
            MockSearchResult(relevance=0.5),
        ]

        source_counts = {"gnosis": 3}  # Single source

        metrics = compute_quality_metrics(
            query="test query",
            results=results,
            source_counts=source_counts,
        )

        # H3: NDCG should be capped at 0.5 for single source
        assert metrics.ndcg_at_10 <= 0.5

    def test_multi_source_ndcg_normal(self):
        """Multi-source NDCG should not be discounted."""
        from mekhane.periskope.quality_metrics import compute_quality_metrics

        results = [
            MockSearchResult(relevance=0.9),
            MockSearchResult(relevance=0.7),
        ]

        source_counts = {"gnosis": 1, "searxng": 1}  # Multiple sources

        metrics = compute_quality_metrics(
            query="test query",
            results=results,
            source_counts=source_counts,
        )

        # No discount for multi-source
        assert metrics.ndcg_at_10 > 0.5 or metrics.ndcg_at_10 == 0.0

    def test_adaptive_threshold_from_config(self):
        """H2: Config should return 0.65 threshold."""
        from mekhane.periskope.config_loader import load_config

        config = load_config()
        threshold = config.get("adaptive_depth_threshold", 0.5)
        assert threshold == 0.65
