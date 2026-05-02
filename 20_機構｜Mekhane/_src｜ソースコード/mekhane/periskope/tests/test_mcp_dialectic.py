# PROOF: mekhane/periskope/tests/test_mcp_dialectic.py
# PURPOSE: periskope モジュールの mcp_dialectic に対するテスト
"""
MCP Integration Tests for DialecticEngine (periskope_research + dialectic=true).

Tests:
  1. dialectic=true → DialecticEngine used
  2. dialectic=false → PeriskopeEngine used (default)
  3. dialectic omitted → PeriskopeEngine used
  4. Arguments pass through correctly to DialecticEngine
  5. DialecticReport.markdown() returned in response
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Helper: mock handle_research internals ────────────────────────

def _make_mock_standard_report():
    """Mock PeriskopeEngine report."""
    report = MagicMock()
    report.markdown.return_value = "# Standard Report"
    report.search_results = [MagicMock()]
    report.source_counts = {"searxng": 3}
    report.synthesis = [MagicMock()]
    report.elapsed_seconds = 5.0
    report.quality_metrics = None
    report.reasoning_trace = None
    return report


def _make_mock_dialectic_report():
    """Mock DialecticEngine report."""
    report = MagicMock()
    report.markdown.return_value = "# Dialectic Report\n\nThesis vs Anti"
    report.thesis_search_results = [MagicMock()]
    report.elapsed_seconds = 12.0
    report.reasoning_trace = None
    return report


# ── Tests ─────────────────────────────────────────────────────────


class TestMCPDialecticRouting:
    """Test that handle_research routes to correct engine based on dialectic flag."""

    @pytest.mark.asyncio
    @patch("mekhane.mcp.periskope_mcp_server.PeriskopeEngine")
    async def test_dialectic_false_uses_standard_engine(self, mock_pe_cls):
        """dialectic=false → PeriskopeEngine."""
        from mekhane.mcp.periskope_mcp_server import handle_research

        mock_engine = MagicMock()
        mock_engine.research = AsyncMock(return_value=_make_mock_standard_report())
        mock_engine._config = {"iterative_deepening": {}}
        mock_pe_cls.return_value = mock_engine

        result = await handle_research({
            "query": "test query",
            "dialectic": False,
        })

        assert len(result) == 1
        assert "Standard Report" in result[0].text
        mock_pe_cls.assert_called_once()

    @pytest.mark.asyncio
    @patch("mekhane.mcp.periskope_mcp_server.PeriskopeEngine")
    async def test_dialectic_omitted_uses_standard_engine(self, mock_pe_cls):
        """dialectic omitted → PeriskopeEngine (default)."""
        from mekhane.mcp.periskope_mcp_server import handle_research

        mock_engine = MagicMock()
        mock_engine.research = AsyncMock(return_value=_make_mock_standard_report())
        mock_engine._config = {"iterative_deepening": {}}
        mock_pe_cls.return_value = mock_engine

        result = await handle_research({"query": "test query"})

        assert len(result) == 1
        mock_pe_cls.assert_called_once()

    @pytest.mark.asyncio
    @patch("mekhane.mcp.periskope_mcp_server.PeriskopeEngine")
    async def test_dialectic_true_uses_dialectic_engine(self, mock_pe_cls):
        """dialectic=true → DialecticEngine."""
        from mekhane.mcp.periskope_mcp_server import handle_research

        mock_report = _make_mock_dialectic_report()

        with patch(
            "mekhane.periskope.dialectic.DialecticEngine"
        ) as mock_de_cls:
            mock_de = MagicMock()
            mock_de.research = AsyncMock(return_value=mock_report)
            mock_de_cls.return_value = mock_de

            result = await handle_research({
                "query": "is dark matter real?",
                "dialectic": True,
                "depth": 2,
            })

        assert len(result) == 1
        assert "Dialectic Report" in result[0].text
        # PeriskopeEngine should NOT have been instantiated
        mock_pe_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_dialectic_passes_arguments(self):
        """Arguments (query, depth, sources) pass through to DialecticEngine."""
        from mekhane.mcp.periskope_mcp_server import handle_research

        mock_report = _make_mock_dialectic_report()

        with patch(
            "mekhane.periskope.dialectic.DialecticEngine"
        ) as mock_de_cls:
            mock_de = MagicMock()
            mock_de.research = AsyncMock(return_value=mock_report)
            mock_de_cls.return_value = mock_de

            with patch("mekhane.mcp.periskope_mcp_server.PeriskopeEngine"):
                await handle_research({
                    "query": "FEP and active inference",
                    "dialectic": True,
                    "depth": 3,
                    "sources": ["semantic_scholar", "searxng"],
                    "expand_query": False,
                })

            call_kwargs = mock_de.research.call_args.kwargs
            assert call_kwargs["query"] == "FEP and active inference"
            assert call_kwargs["depth"] == 3
            assert call_kwargs["sources"] == ["semantic_scholar", "searxng"]
            assert call_kwargs["expand_query"] is False

    @pytest.mark.asyncio
    async def test_depth3_auto_activates_dialectic(self):
        """depth=3 + dialectic omitted → DialecticEngine auto-activated."""
        from mekhane.mcp.periskope_mcp_server import handle_research

        mock_report = _make_mock_dialectic_report()

        with patch(
            "mekhane.periskope.dialectic.DialecticEngine"
        ) as mock_de_cls:
            mock_de = MagicMock()
            mock_de.research = AsyncMock(return_value=mock_report)
            mock_de_cls.return_value = mock_de

            with patch("mekhane.mcp.periskope_mcp_server.PeriskopeEngine") as mock_pe_cls:
                result = await handle_research({
                    "query": "deep research topic",
                    "depth": 3,
                    # dialectic NOT specified → should auto-activate
                })

            assert len(result) == 1
            assert "Dialectic Report" in result[0].text
            mock_pe_cls.assert_not_called()

    @pytest.mark.asyncio
    @patch("mekhane.mcp.periskope_mcp_server.PeriskopeEngine")
    async def test_depth3_explicit_false_uses_standard(self, mock_pe_cls):
        """depth=3 + dialectic=false → PeriskopeEngine (explicit opt-out)."""
        from mekhane.mcp.periskope_mcp_server import handle_research

        mock_engine = MagicMock()
        mock_engine.research = AsyncMock(return_value=_make_mock_standard_report())
        mock_engine._config = {"iterative_deepening": {}}
        mock_pe_cls.return_value = mock_engine

        result = await handle_research({
            "query": "deep but standard",
            "depth": 3,
            "dialectic": False,  # explicit opt-out
        })

        assert len(result) == 1
        assert "Standard Report" in result[0].text
        mock_pe_cls.assert_called_once()


class TestMCPDialecticSchema:
    """Test that the MCP tool schema includes dialectic parameter."""

    @pytest.mark.asyncio
    async def test_list_tools_includes_dialectic(self):
        """periskope_research inputSchema includes dialectic boolean."""
        from mekhane.mcp.periskope_mcp_server import list_tools

        tools = await list_tools()
        research_tool = next(t for t in tools if t.name == "periskope_research")
        schema_props = research_tool.inputSchema["properties"]

        assert "dialectic" in schema_props
        assert schema_props["dialectic"]["type"] == "boolean"
        assert schema_props["dialectic"]["default"] is False
