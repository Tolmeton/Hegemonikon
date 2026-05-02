# PROOF: mekhane/periskope/tests/test_phi7_loop.py
# PURPOSE: periskope モジュールの phi7_loop に対するテスト
"""
F8: Φ7 Belief Update Loop — Integration Tests.

Tests that the Φ7 loop fires correctly when quality is below threshold,
generates seed queries, and respects max_iterations safety valve.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from mekhane.periskope.cognition.phi7_belief_update import (
    phi7_belief_update,
    BeliefUpdate,
)


class TestPhi7Loop:
    """Test Φ7 belief update loop behavior."""

    @pytest.mark.asyncio
    async def test_high_quality_no_loop(self):
        """When quality is high, should_loop=False and no seeds generated."""
        result = await phi7_belief_update(
            query="test query",
            overall_score=0.9,
            synthesis_texts=["Good synthesis content."],
            loop_threshold=0.5,
        )
        assert isinstance(result, BeliefUpdate)
        assert result.should_loop is False
        assert result.residual_error < 0.5
        assert len(result.seed_queries) == 0

    @pytest.mark.asyncio
    async def test_low_quality_triggers_loop(self):
        """When quality is below threshold, should_loop=True and seeds generated."""
        with patch(
            "mekhane.periskope.cognition.phi7_belief_update._llm_ask",
            new_callable=AsyncMock,
            return_value="Why is NDCG so low?\nAre there alternative sources?\nWhat terms are missing?",
        ):
            result = await phi7_belief_update(
                query="test query",
                overall_score=0.1,
                synthesis_texts=["Weak synthesis."],
                loop_threshold=0.5,
            )

        assert result.should_loop is True
        assert result.residual_error >= 0.5
        assert len(result.seed_queries) > 0

    @pytest.mark.asyncio
    async def test_max_iterations_safety(self):
        """Even if quality is low, max_iterations prevents infinite loops."""
        result = await phi7_belief_update(
            query="test query",
            overall_score=0.1,
            synthesis_texts=["Very bad synthesis."],
            loop_threshold=0.5,
            iteration=2,
            max_iterations=2,
        )
        assert result.should_loop is False  # max reached

    @pytest.mark.asyncio
    async def test_forced_loop_with_high_threshold(self):
        """Using a very high threshold (0.8) forces loop on moderate quality."""
        with patch(
            "mekhane.periskope.cognition.phi7_belief_update._llm_ask",
            new_callable=AsyncMock,
            return_value="Explore broader literature\nCheck alternative databases",
        ):
            result = await phi7_belief_update(
                query="test query",
                overall_score=0.1,  # residual=0.9 > threshold=0.8
                synthesis_texts=["Moderate synthesis content."],
                loop_threshold=0.8,
            )

        assert result.should_loop is True
        assert len(result.seed_queries) >= 1

    @pytest.mark.asyncio
    async def test_llm_failure_still_reports_error(self):
        """When LLM fails, seeds are empty but residual error is still computed."""
        with patch(
            "mekhane.periskope.cognition.phi7_belief_update._llm_ask",
            new_callable=AsyncMock,
            return_value="",
        ):
            result = await phi7_belief_update(
                query="test query",
                overall_score=0.1,
                synthesis_texts=["Failed synthesis."],
                loop_threshold=0.5,
            )

        assert result.residual_error >= 0.5
        assert len(result.seed_queries) == 0
