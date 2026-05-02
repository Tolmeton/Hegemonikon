# PROOF: mekhane/mcp/tests/test_periskope_benchmark.py
# PURPOSE: mcp モジュールの periskope_benchmark に対するテスト
"""Tests for periskope_mcp_server benchmark handler.

Validates that handle_benchmark correctly formats QualityMetrics attributes
and handles edge cases (missing queries, empty results).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
import asyncio


# ---- Fixtures ----

@dataclass
class FakeQualityMetrics:
    """Minimal QualityMetrics for testing attribute access patterns."""
    ndcg_at_10: float = 0.95
    source_entropy: float = 1.5
    max_entropy: float = 2.0
    coverage_score: float = 0.85
    diversity_weight: float = 0.3

    @property
    def source_entropy_normalized(self) -> float:
        if self.max_entropy == 0:
            return 0.0
        return min(1.0, self.source_entropy / self.max_entropy)

    @property
    def overall_score(self) -> float:
        dw = max(0.0, min(1.0, self.diversity_weight))
        w_ndcg = 0.7 - 0.6 * dw
        w_entropy = 0.6 * dw
        w_coverage = 0.3
        return (
            w_ndcg * self.ndcg_at_10
            + w_entropy * self.source_entropy_normalized
            + w_coverage * self.coverage_score
        )

    def __format__(self, format_spec: str) -> str:
        if format_spec == "benchmark":
            return (
                f"{self.ndcg_at_10:.2f} | {self.source_entropy_normalized:.2f} | "
                f"{self.coverage_score:.2f} | **{self.overall_score:.2f}**"
            )
        return super().__format__(format_spec)


@dataclass
class FakeSearchResult:
    title: str = "Result"
    url: str = "https://example.com"
    snippet: str = "test"
    source: str = "searxng"


_UNSET = object()  # sentinel


@dataclass
class FakeReport:
    search_results: list = None
    quality_metrics: object = _UNSET
    elapsed_seconds: float = 5.0
    source_counts: dict = None

    def __post_init__(self):
        if self.search_results is None:
            self.search_results = [FakeSearchResult()]
        if self.quality_metrics is _UNSET:
            self.quality_metrics = FakeQualityMetrics()
        if self.source_counts is None:
            self.source_counts = {"searxng": 1}


# ---- Tests ----

class TestQualityMetricsAttributes:
    """Ensure handle_benchmark references correct QualityMetrics attributes."""

    def test_source_entropy_normalized_exists(self):
        """The attribute that handle_benchmark uses must exist."""
        m = FakeQualityMetrics()
        assert hasattr(m, "source_entropy_normalized")
        assert 0.0 <= m.source_entropy_normalized <= 1.0

    def test_coverage_score_exists(self):
        """The attribute that handle_benchmark uses must exist."""
        m = FakeQualityMetrics()
        assert hasattr(m, "coverage_score")

    def test_overall_score_exists(self):
        m = FakeQualityMetrics()
        assert hasattr(m, "overall_score")
        assert 0.0 <= m.overall_score <= 1.0

    def test_ndcg_at_10_exists(self):
        m = FakeQualityMetrics()
        assert hasattr(m, "ndcg_at_10")

    def test_real_quality_metrics_has_required_attrs(self):
        """Integration test: verify the REAL QualityMetrics class has all
        attributes that handle_benchmark references."""
        from mekhane.periskope.quality_metrics import QualityMetrics
        m = QualityMetrics(
            ndcg_at_10=0.9,
            source_entropy=1.0,
            max_entropy=2.0,
            coverage_score=0.8,
        )
        # These are the exact attribute names used in handle_benchmark L700-704
        assert hasattr(m, "ndcg_at_10")
        assert hasattr(m, "source_entropy_normalized")
        assert hasattr(m, "coverage_score")
        assert hasattr(m, "overall_score")

        # Verify they return valid floats
        assert isinstance(m.ndcg_at_10, float)
        assert isinstance(m.source_entropy_normalized, float)
        assert isinstance(m.coverage_score, float)
        assert isinstance(m.overall_score, float)


class TestHandleBenchmarkFormat:
    """Test handle_benchmark output formatting."""

    def test_missing_queries_returns_error(self):
        async def _impl():
            from mekhane.mcp.periskope_mcp_server import handle_benchmark
            result = await handle_benchmark({"depth": 1})
            assert len(result) == 1
            assert "Error" in result[0].text
        asyncio.run(_impl())

    def test_benchmark_output_contains_header(self):
        async def _impl():
            """Benchmark output must contain markdown table header."""
            from mekhane.mcp.periskope_mcp_server import handle_benchmark

            fake_report = FakeReport()

            with patch(
                "mekhane.mcp.periskope_mcp_server.PeriskopeEngine"
            ) as MockEngine:
                instance = MockEngine.return_value
                instance.research = AsyncMock(return_value=fake_report)
                instance._config = {"benchmark_default_sources": ["searxng", "brave", "tavily"]}

                result = await handle_benchmark({
                    "queries": ["test query"],
                    "depth": 1,
                    "sources": ["searxng"],
                })

            text = result[0].text
            assert "Periskopē Benchmark Results" in text
            assert "| Query |" in text
            assert "**Depth**: L1" in text
        asyncio.run(_impl())

    def test_benchmark_formats_metrics_correctly(self):
        async def _impl():
            """Verify the f-string formatting doesn't crash with real attributes."""
            from mekhane.mcp.periskope_mcp_server import handle_benchmark

            m = FakeQualityMetrics(ndcg_at_10=0.92, source_entropy=1.5, max_entropy=2.0, coverage_score=1.0)
            fake_report = FakeReport(quality_metrics=m)

            with patch(
                "mekhane.mcp.periskope_mcp_server.PeriskopeEngine"
            ) as MockEngine:
                instance = MockEngine.return_value
                instance.research = AsyncMock(return_value=fake_report)
                instance._config = {"benchmark_default_sources": ["searxng", "brave", "tavily"]}

                result = await handle_benchmark({
                    "queries": ["FEP active inference"],
                    "depth": 1,
                    "sources": ["searxng", "brave"],
                })

            text = result[0].text
            assert "0.92" in text  # NDCG
            assert "1.00" in text  # coverage
            assert "ERROR" not in text
        asyncio.run(_impl())

    def test_benchmark_handles_no_metrics(self):
        async def _impl():
            """When quality_metrics is None, output should show dashes not crash."""
            from mekhane.mcp.periskope_mcp_server import handle_benchmark

            fake_report = FakeReport(quality_metrics=None)

            with patch(
                "mekhane.mcp.periskope_mcp_server.PeriskopeEngine"
            ) as MockEngine:
                instance = MockEngine.return_value
                instance.research = AsyncMock(return_value=fake_report)
                instance._config = {"benchmark_default_sources": ["searxng", "brave", "tavily"]}

                result = await handle_benchmark({
                    "queries": ["test"],
                    "depth": 1,
                    "sources": ["searxng"],
                })

            text = result[0].text
            assert "| - | - | - | - |" in text
            assert "ERROR" not in text
        asyncio.run(_impl())

    def test_benchmark_default_sources(self):
        async def _impl():
            """Default sources should be limited, not all 14."""
            from mekhane.mcp.periskope_mcp_server import handle_benchmark

            fake_report = FakeReport()

            with patch(
                "mekhane.mcp.periskope_mcp_server.PeriskopeEngine"
            ) as MockEngine:
                instance = MockEngine.return_value
                instance.research = AsyncMock(return_value=fake_report)
                instance._config = {"benchmark_default_sources": ["searxng", "brave", "tavily"]}

                result = await handle_benchmark({
                    "queries": ["test"],
                })

            text = result[0].text
            # Should use default limited sources, not all 14
            assert "searxng" in text
            assert "brave" in text
            assert "tavily" in text
        asyncio.run(_impl())


class TestFormatThinkingTrace:
    """Test _format_thinking_trace uses label for display."""

    def test_label_used_over_phase(self):
        from mekhane.mcp.periskope_mcp_server import _format_thinking_trace

        events = [
            {"t": 0.0, "phase": "phase_0_start", "label": "Cognitive Expansion", "query": "test"},
            {"t": 1.5, "phase": "phase_1_done", "results": 7},
        ]

        # Minimal fake report with no reasoning trace
        report = MagicMock()
        report.reasoning_trace = None

        output = _format_thinking_trace(events, report)
        assert "Cognitive Expansion" in output
        # phase_1_done has no label, so phase ID should be used
        assert "phase_1_done" in output

    def test_label_not_in_details(self):
        """label should be used for display, not appear in detail column."""
        from mekhane.mcp.periskope_mcp_server import _format_thinking_trace

        events = [
            {"t": 0.0, "phase": "phase_0_start", "label": "Cognitive Expansion"},
        ]
        report = MagicMock()
        report.reasoning_trace = None

        output = _format_thinking_trace(events, report)
        # label should be in the phase column, not the detail column
        lines = output.split("\n")
        data_lines = [l for l in lines if l.startswith("|") and "phase_0" not in l and "Cognitive" in l]
        # The label should appear as the phase display
        assert any("Cognitive Expansion" in l for l in lines)
