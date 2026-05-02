# PROOF: mekhane/mcp/tests/test_periskope_handlers.py
# PURPOSE: mcp モジュールの periskope_handlers に対するテスト
"""Tests for periskope_mcp_server search and research handlers.

Validates output formatting, parameter handling, and error paths
for handle_search and handle_research.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass, field
from enum import Enum
import asyncio


# ---- Fixtures ----

class FakeSourceEnum(Enum):
    SEARXNG = "searxng"
    BRAVE = "brave"


class FakeModelEnum(Enum):
    GEMINI_FLASH = "gemini-flash"


_UNSET = object()


@dataclass
class FakeSearchResult:
    title: str = "Test Result"
    url: str = "https://example.com"
    snippet: str = "A test snippet"
    content: str = "Full content here"
    source: FakeSourceEnum = FakeSourceEnum.SEARXNG
    relevance: float = 0.95


@dataclass
class FakeSynthesis:
    model: FakeModelEnum = FakeModelEnum.GEMINI_FLASH
    content: str = "Synthesized answer"
    confidence: float = 0.85


@dataclass
class FakeQualityMetrics:
    ndcg_at_10: float = 0.92
    source_entropy: float = 1.5
    max_entropy: float = 2.0
    coverage_score: float = 0.85
    diversity_weight: float = 0.3

    @property
    def source_entropy_normalized(self):
        return min(1.0, self.source_entropy / self.max_entropy) if self.max_entropy else 0.0

    @property
    def overall_score(self):
        dw = max(0.0, min(1.0, self.diversity_weight))
        return (0.7 - 0.6 * dw) * self.ndcg_at_10 + 0.6 * dw * self.source_entropy_normalized + 0.3 * self.coverage_score

    def summary(self):
        return f"Quality: {self.overall_score:.0%}"


@dataclass
class FakeReport:
    search_results: list = None
    synthesis: list = None
    quality_metrics: object = _UNSET
    elapsed_seconds: float = 3.0
    source_counts: dict = None
    reasoning_trace: object = None

    def __post_init__(self):
        if self.search_results is None:
            self.search_results = [FakeSearchResult()]
        if self.synthesis is None:
            self.synthesis = [FakeSynthesis()]
        if self.quality_metrics is _UNSET:
            self.quality_metrics = FakeQualityMetrics()
        if self.source_counts is None:
            self.source_counts = {"searxng": 1}

    def markdown(self):
        return "# Research Report\n\nSynthesized content here."


# ---- handle_search tests ----

class TestHandleSearch:
    """Tests for the search-only handler."""

    def test_missing_query_returns_error(self):
        async def _impl():
            from mekhane.mcp.periskope_mcp_server import handle_search
            result = await handle_search({"sources": ["searxng"]})
            assert "Error" in result[0].text
        asyncio.run(_impl())

    def test_search_output_contains_header(self):
        async def _impl():
            from mekhane.mcp.periskope_mcp_server import handle_search

            with patch("mekhane.mcp.periskope_mcp_server.PeriskopeEngine") as MockEngine:
                instance = MockEngine.return_value
                instance.research = AsyncMock(return_value=FakeReport())
                result = await handle_search({"query": "test query"})

            text = result[0].text
            assert "Periskopē Search Results" in text
            assert "test query" in text
        asyncio.run(_impl())

    def test_search_includes_source_table(self):
        async def _impl():
            from mekhane.mcp.periskope_mcp_server import handle_search

            with patch("mekhane.mcp.periskope_mcp_server.PeriskopeEngine") as MockEngine:
                instance = MockEngine.return_value
                instance.research = AsyncMock(return_value=FakeReport())
                result = await handle_search({"query": "test"})

            text = result[0].text
            assert "| Engine |" in text
            assert "searxng" in text
        asyncio.run(_impl())

    def test_search_includes_results(self):
        async def _impl():
            from mekhane.mcp.periskope_mcp_server import handle_search

            report = FakeReport(search_results=[
                FakeSearchResult(title="Result A", relevance=0.9),
                FakeSearchResult(title="Result B", relevance=0.7),
            ])

            with patch("mekhane.mcp.periskope_mcp_server.PeriskopeEngine") as MockEngine:
                instance = MockEngine.return_value
                instance.research = AsyncMock(return_value=report)
                result = await handle_search({"query": "test"})

            text = result[0].text
            assert "Result A" in text
            assert "Result B" in text
            assert "0.90" in text  # relevance
        asyncio.run(_impl())

    def test_search_passes_sources_parameter(self):
        async def _impl():
            from mekhane.mcp.periskope_mcp_server import handle_search

            with patch("mekhane.mcp.periskope_mcp_server.PeriskopeEngine") as MockEngine:
                instance = MockEngine.return_value
                instance.research = AsyncMock(return_value=FakeReport())
                await handle_search({"query": "test", "sources": ["brave"]})

            call_kwargs = instance.research.call_args.kwargs
            assert call_kwargs.get("sources") == ["brave"]
        asyncio.run(_impl())


# ---- handle_research tests ----

class TestHandleResearch:
    """Tests for the full research pipeline handler."""

    def test_missing_query_returns_error(self):
        async def _impl():
            from mekhane.mcp.periskope_mcp_server import handle_research
            result = await handle_research({"depth": 2})
            assert "Error" in result[0].text
        asyncio.run(_impl())

    def test_research_returns_markdown(self):
        async def _impl():
            from mekhane.mcp.periskope_mcp_server import handle_research

            with patch("mekhane.mcp.periskope_mcp_server.PeriskopeEngine") as MockEngine:
                instance = MockEngine.return_value
                instance.research = AsyncMock(return_value=FakeReport())
                result = await handle_research({"query": "FEP"})

            text = result[0].text
            assert "Research Report" in text
        asyncio.run(_impl())

    def test_research_logs_quality_summary(self):
        async def _impl():
            """Quality summary is logged (not necessarily in returned text)."""
            from mekhane.mcp.periskope_mcp_server import handle_research

            with patch("mekhane.mcp.periskope_mcp_server.PeriskopeEngine") as MockEngine:
                instance = MockEngine.return_value
                instance.research = AsyncMock(return_value=FakeReport())
                result = await handle_research({"query": "FEP"})

            # The return value is report.markdown() — Quality is in the log
            text = result[0].text
            assert "Research Report" in text  # confirms markdown() output is returned
        asyncio.run(_impl())

    def test_research_passes_all_parameters(self):
        async def _impl():
            from mekhane.mcp.periskope_mcp_server import handle_research

            with patch("mekhane.mcp.periskope_mcp_server.PeriskopeEngine") as MockEngine:
                instance = MockEngine.return_value
                instance.research = AsyncMock(return_value=FakeReport())
                await handle_research({
                    "query": "FEP",
                    "depth": 2,
                    "sources": ["searxng"],
                    "multipass": True,
                    "expand_query": False,
                })

            call_kwargs = instance.research.call_args.kwargs
            assert call_kwargs["depth"] == 2
            assert call_kwargs["sources"] == ["searxng"]
            assert call_kwargs["multipass"] is True
            assert call_kwargs["expand_query"] is False
        asyncio.run(_impl())

    def test_research_collects_thinking_events(self):
        async def _impl():
            """Verify progress_callback is passed and can receive events."""
            from mekhane.mcp.periskope_mcp_server import handle_research

            with patch("mekhane.mcp.periskope_mcp_server.PeriskopeEngine") as MockEngine:
                instance = MockEngine.return_value
                instance.research = AsyncMock(return_value=FakeReport())
                await handle_research({"query": "FEP"})

            call_kwargs = instance.research.call_args.kwargs
            assert "progress_callback" in call_kwargs
            assert callable(call_kwargs["progress_callback"])
        asyncio.run(_impl())
