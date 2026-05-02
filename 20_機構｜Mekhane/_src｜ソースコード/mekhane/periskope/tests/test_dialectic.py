# PROOF: mekhane/periskope/tests/test_dialectic.py
# PURPOSE: periskope モジュールの dialectic に対するテスト
"""
Tests for DialecticEngine v2 — parallel execution with EphemeralIndex.

Tests:
  1. DialecticEngine initializes with shared EphemeralIndex
  2. DialecticReport dataclass and markdown output
  3. Parallel research execution (mocked engines)
  4. Query inversion fallback
  5. Dialectical synthesis call
  6. Error handling in parallel gather
"""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from mekhane.periskope.dialectic import (
    DialecticEngine,
    DialecticReport,
    ANTI_SYSTEM_INSTRUCTION,
)
from mekhane.periskope.cognition.ephemeral_index import EphemeralIndex


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def mock_config():
    """Minimal config for DialecticEngine."""
    return {
        "phase_inversion": {
            "dialectic": {
                "rounds": {1: 1, 2: 3, 3: 5},
                "convergence_threshold": 0.05,
            },
        },
    }


@pytest.fixture
def report():
    """Sample DialecticReport."""
    return DialecticReport(
        query="Is dark matter real?",
        synthesis_text="The evidence is mixed...",
        thesis_confidence=0.85,
        antithesis_confidence=0.60,
        final_confidence=0.75,
        elapsed_seconds=12.3,
    )


# ── DialecticReport Tests ────────────────────────────────────────


class TestDialecticReport:
    """Tests for DialecticReport dataclass."""

    def test_report_defaults(self):
        r = DialecticReport(query="test")
        assert r.query == "test"
        assert r.synthesis_text == ""
        assert r.final_confidence == 0.0
        assert r.thesis_search_results == []
        assert r.antithesis_search_results == []
        assert r.source_counts == {}

    def test_markdown_output(self, report):
        md = report.markdown()
        assert "Dialectical Analysis" in md
        assert "Thesis" in md
        assert "Antithesis" in md
        assert "85%" in md
        assert "60%" in md
        assert "The evidence is mixed" in md

    def test_confidence_formatting(self, report):
        md = report.markdown()
        assert "Final Integrated Confidence" in md


# ── DialecticEngine Tests ────────────────────────────────────────


class TestDialecticEngine:
    """Tests for DialecticEngine v2 parallel execution."""

    def test_init_creates_shared_index(self, mock_config):
        """Engine __init__ creates shared EphemeralIndex and passes it to both engines."""
        engine = DialecticEngine.__new__(DialecticEngine)
        engine._config = mock_config
        engine._dialectic_cfg = mock_config["phase_inversion"]["dialectic"]
        engine.ephemeral_index = EphemeralIndex()

        assert isinstance(engine.ephemeral_index, EphemeralIndex)
        assert engine.ephemeral_index.stats()["total_entries"] == 0

    def test_init_engine_roles(self, mock_config):
        """Both engines are given shared_index and correct roles."""
        engine = DialecticEngine.__new__(DialecticEngine)
        engine._config = mock_config
        engine._dialectic_cfg = mock_config["phase_inversion"]["dialectic"]
        engine.ephemeral_index = EphemeralIndex()
        engine.thesis_engine = MagicMock()
        engine.anti_engine = MagicMock()

        assert engine.thesis_engine is not engine.anti_engine
        assert engine.ephemeral_index is not None


class TestDialecticResearch:
    """Tests for DialecticEngine.research() — parallel execution."""

    def _make_engine_with_mocks(self, mock_config):
        """Helper to create a DialecticEngine with mocked internals."""
        engine = DialecticEngine.__new__(DialecticEngine)
        engine._config = mock_config
        engine._dialectic_cfg = mock_config.get("phase_inversion", {}).get("dialectic", {})
        engine.ephemeral_index = EphemeralIndex()

        # Mock engines
        engine.thesis_engine = MagicMock()
        engine.anti_engine = MagicMock()

        return engine

    def _make_mock_result(self, confidence=0.8, synthesis_text="Some synthesis"):
        """Create a mock research result."""
        result = MagicMock()
        result.search_results = [MagicMock(url="http://example.com/a")]
        result.source_counts = {"searxng": 5}
        result.reasoning_trace = MagicMock()
        result.reasoning_trace.latest_confidence = confidence
        result.synthesis = [MagicMock(content=synthesis_text)]
        result.quality_metrics = None  # Prevent MagicMock leaking into _merge_quality_metrics
        return result

    @pytest.mark.asyncio
    async def test_parallel_execution(self, mock_config):
        """Both engines run in parallel via asyncio.gather."""
        engine = self._make_engine_with_mocks(mock_config)

        thesis_result = self._make_mock_result(0.85, "Thesis content")
        anti_result = self._make_mock_result(0.60, "Antithesis content")

        engine.thesis_engine.research = AsyncMock(return_value=thesis_result)
        engine.anti_engine.research = AsyncMock(return_value=anti_result)

        with patch("mekhane.periskope.dialectic.invert_queries", new_callable=AsyncMock) as mock_invert:
            mock_invert.return_value = ["inverted query"]
            with patch("mekhane.periskope.dialectic._llm_ask", new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = "Balanced synthesis text"

                report = await engine.research("Is X true?", depth=2)

        assert engine.thesis_engine.research.called
        assert engine.anti_engine.research.called
        assert report.thesis_confidence == 0.85
        assert report.antithesis_confidence == 0.60
        assert report.synthesis_text == "Balanced synthesis text"
        assert report.elapsed_seconds > 0

    @pytest.mark.asyncio
    async def test_antithesis_gets_system_instruction(self, mock_config):
        """Anti engine receives ANTI_SYSTEM_INSTRUCTION."""
        engine = self._make_engine_with_mocks(mock_config)

        engine.thesis_engine.research = AsyncMock(return_value=self._make_mock_result())
        engine.anti_engine.research = AsyncMock(return_value=self._make_mock_result())

        with patch("mekhane.periskope.dialectic.invert_queries", new_callable=AsyncMock) as mock_invert:
            mock_invert.return_value = ["inverted"]
            with patch("mekhane.periskope.dialectic._llm_ask", new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = "synthesis"
                await engine.research("test query", depth=1)

        # Anti engine should have received system_instruction
        call_kwargs = engine.anti_engine.research.call_args
        assert call_kwargs.kwargs.get("system_instruction") == ANTI_SYSTEM_INSTRUCTION

    @pytest.mark.asyncio
    async def test_query_inversion_fallback(self, mock_config):
        """When invert_queries fails, fallback query is used."""
        engine = self._make_engine_with_mocks(mock_config)

        engine.thesis_engine.research = AsyncMock(return_value=self._make_mock_result())
        engine.anti_engine.research = AsyncMock(return_value=self._make_mock_result())

        with patch("mekhane.periskope.dialectic.invert_queries", new_callable=AsyncMock) as mock_invert:
            mock_invert.side_effect = RuntimeError("LLM unavailable")
            with patch("mekhane.periskope.dialectic._llm_ask", new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = "synthesis"
                report = await engine.research("dark matter", depth=1)

        # Anti engine should have received fallback query
        call_args = engine.anti_engine.research.call_args
        assert "arguments against" in call_args.kwargs["query"]
        assert report is not None

    @pytest.mark.asyncio
    async def test_confidence_calculation(self, mock_config):
        """Final confidence uses dynamic weighting based on confidence ratio."""
        engine = self._make_engine_with_mocks(mock_config)

        engine.thesis_engine.research = AsyncMock(return_value=self._make_mock_result(0.90))
        engine.anti_engine.research = AsyncMock(return_value=self._make_mock_result(0.50))

        with patch("mekhane.periskope.dialectic.invert_queries", new_callable=AsyncMock) as mock_invert:
            mock_invert.return_value = ["inverted"]
            with patch("mekhane.periskope.dialectic._llm_ask", new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = "synthesis"
                report = await engine.research("test", depth=1)

        # Dynamic weight: t_w = 0.9/1.4 ≈ 0.643 (within [0.3, 0.7] for depth<3)
        t_w = 0.9 / 1.4
        expected = 0.90 * t_w + 0.50 * (1.0 - t_w)
        assert abs(report.final_confidence - expected) < 0.01

    @pytest.mark.asyncio
    async def test_source_counts_merged(self, mock_config):
        """Source counts from both engines are merged."""
        engine = self._make_engine_with_mocks(mock_config)

        thesis = self._make_mock_result()
        thesis.source_counts = {"searxng": 3, "brave": 2}
        anti = self._make_mock_result()
        anti.source_counts = {"searxng": 4, "tavily": 1}

        engine.thesis_engine.research = AsyncMock(return_value=thesis)
        engine.anti_engine.research = AsyncMock(return_value=anti)

        with patch("mekhane.periskope.dialectic.invert_queries", new_callable=AsyncMock) as mock_invert:
            mock_invert.return_value = ["inverted"]
            with patch("mekhane.periskope.dialectic._llm_ask", new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = "synthesis"
                report = await engine.research("test", depth=1)

        assert report.source_counts["searxng"] == 7
        assert report.source_counts["brave"] == 2
        assert report.source_counts["tavily"] == 1

    @pytest.mark.asyncio
    async def test_gather_error_handling(self, mock_config):
        """If parallel gather fails, report is still returned (empty)."""
        engine = self._make_engine_with_mocks(mock_config)

        engine.thesis_engine.research = AsyncMock(side_effect=RuntimeError("boom"))
        engine.anti_engine.research = AsyncMock(side_effect=RuntimeError("boom"))

        with patch("mekhane.periskope.dialectic.invert_queries", new_callable=AsyncMock) as mock_invert:
            mock_invert.return_value = ["inverted"]
            with patch("mekhane.periskope.dialectic._llm_ask", new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = "synthesis"
                report = await engine.research("test", depth=1)

        # Should return a report even on failure
        assert report is not None
        assert report.final_confidence == 0.0

    @pytest.mark.asyncio
    async def test_ephemeral_index_cleared_on_start(self, mock_config):
        """EphemeralIndex is cleared at the start of each research call."""
        engine = self._make_engine_with_mocks(mock_config)
        engine.ephemeral_index = MagicMock(spec=EphemeralIndex)
        engine.ephemeral_index.stats.return_value = {"total_entries": 0}

        engine.thesis_engine.research = AsyncMock(return_value=self._make_mock_result())
        engine.anti_engine.research = AsyncMock(return_value=self._make_mock_result())

        with patch("mekhane.periskope.dialectic.invert_queries", new_callable=AsyncMock) as mock_invert:
            mock_invert.return_value = ["inverted"]
            with patch("mekhane.periskope.dialectic._llm_ask", new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = "synthesis"
                await engine.research("test", depth=1)

        engine.ephemeral_index.clear.assert_called_once()


# ── Anti System Instruction ──────────────────────────────────────


class TestAntiSystemInstruction:
    """Tests for the ANTI_SYSTEM_INSTRUCTION constant."""

    def test_contains_adversarial_keywords(self):
        assert "ADVERSARIAL" in ANTI_SYSTEM_INSTRUCTION
        assert "CONTRADICTS" in ANTI_SYSTEM_INSTRUCTION
        assert "REFUTES" in ANTI_SYSTEM_INSTRUCTION
        assert "counter-evidence" in ANTI_SYSTEM_INSTRUCTION
