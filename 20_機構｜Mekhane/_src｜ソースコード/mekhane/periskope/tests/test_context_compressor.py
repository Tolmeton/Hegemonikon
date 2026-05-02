# PROOF: mekhane/periskope/tests/test_context_compressor.py
# PURPOSE: periskope モジュールの context_compressor に対するテスト
"""
Tests for DialecticContextBuffer — LS-pattern context compression.

Tests:
  1. Buffer initialization with depth-aware budgets
  2. Append and render
  3. Budget utilization tracking
  4. Truncation fallback when over budget
  5. Compression trigger (mocked LLM)
  6. Clear and stats
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from mekhane.periskope.cognition.context_compressor import (
    DialecticContextBuffer,
    ContextEntry,
    CONTEXT_BUDGET,
    VERBATIM_WINDOW,
)


# ── Budget Tests ──────────────────────────────────────────────────


class TestBudget:
    """Depth-aware budget configuration."""

    def test_l1_budget(self):
        buf = DialecticContextBuffer(depth=1)
        assert buf.budget == 5_000
        assert buf.verbatim_window == 2

    def test_l2_budget(self):
        buf = DialecticContextBuffer(depth=2)
        assert buf.budget == 20_000
        assert buf.verbatim_window == 4

    def test_l3_budget(self):
        buf = DialecticContextBuffer(depth=3)
        assert buf.budget == 40_000
        assert buf.verbatim_window == 6

    def test_unknown_depth_defaults_to_l2(self):
        buf = DialecticContextBuffer(depth=99)
        assert buf.budget == 20_000
        assert buf.verbatim_window == 4


# ── Append and Render Tests ──────────────────────────────────────


class TestAppendAndRender:
    """Basic append and render operations."""

    def test_append_single(self):
        buf = DialecticContextBuffer(depth=2)
        buf.append(1, "antithesis", "Counter-evidence: X is weak because Y")
        assert len(buf.entries) == 1
        assert buf.total_chars > 0

    def test_append_ignores_short(self):
        buf = DialecticContextBuffer(depth=2)
        buf.append(1, "antithesis", "short")
        assert len(buf.entries) == 0

    def test_render_empty(self):
        buf = DialecticContextBuffer(depth=2)
        assert buf.render() == ""

    def test_render_with_entries(self):
        buf = DialecticContextBuffer(depth=2)
        buf.append(1, "antithesis", "Finding A is contradicted by B")
        buf.append(2, "thesis", "Evidence C supports D strongly")
        rendered = buf.render()
        assert "Iter 1" in rendered
        assert "Iter 2" in rendered
        assert "Finding A" in rendered

    def test_render_with_checkpoint(self):
        buf = DialecticContextBuffer(depth=2)
        buf._checkpoint_text = "Summary of old findings"
        buf.append(5, "antithesis", "Recent finding about Z")
        rendered = buf.render()
        assert "Compressed Checkpoint" in rendered
        assert "Summary of old" in rendered
        assert "Recent finding" in rendered


# ── Over Budget Tests ─────────────────────────────────────────────


class TestOverBudget:
    """Budget enforcement and truncation."""

    def test_not_over_budget(self):
        buf = DialecticContextBuffer(depth=1)
        buf.append(1, "anti", "Short finding about A")
        assert not buf.is_over_budget

    def test_over_budget_detection(self):
        buf = DialecticContextBuffer(depth=1)  # 5K budget
        # Add enough entries to exceed budget
        for i in range(20):
            buf.append(i, "anti", "X" * 300)
        assert buf.is_over_budget

    @pytest.mark.asyncio
    async def test_truncation_fallback(self):
        """When few entries, truncate oldest as fallback."""
        buf = DialecticContextBuffer(depth=1)  # 5K budget, window=2
        for i in range(3):
            buf.append(i, "anti", "X" * 2000)
        assert buf.is_over_budget

        # Compression should fall back to truncation (no LLM mock needed — fails gracefully)
        with patch(
            "mekhane.periskope.cognition.context_compressor.DialecticContextBuffer._llm_compress",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.side_effect = RuntimeError("no LLM")
            result = await buf.compress_if_needed()

        assert result is True
        # At least one entry should have been removed
        assert len(buf.entries) < 3

    @pytest.mark.asyncio
    async def test_llm_compression(self):
        """LLM compression creates checkpoint from old entries."""
        buf = DialecticContextBuffer(depth=2)  # 20K budget, window=4
        # Add 8 entries — 4 old + 4 recent
        for i in range(8):
            buf.append(i, "anti", f"Finding {i}: " + "detail " * 400)

        assert buf.is_over_budget

        with patch(
            "mekhane.periskope.cognition.context_compressor.DialecticContextBuffer._llm_compress",
            new_callable=AsyncMock,
        ) as mock_llm:
            mock_llm.return_value = "Compressed: findings 0-3 show X, Y, Z"
            result = await buf.compress_if_needed()

        assert result is True
        assert buf._checkpoint_text == "Compressed: findings 0-3 show X, Y, Z"
        assert len(buf.entries) == 4  # Only verbatim window kept

    @pytest.mark.asyncio
    async def test_no_compression_under_budget(self):
        """No compression when under budget."""
        buf = DialecticContextBuffer(depth=3)  # 40K budget
        buf.append(1, "anti", "Small finding")
        result = await buf.compress_if_needed()
        assert result is False


# ── Stats and Clear Tests ────────────────────────────────────────


class TestStatsAndClear:
    """Statistics and reset."""

    def test_stats(self):
        buf = DialecticContextBuffer(depth=2)
        buf.append(1, "anti", "Finding about X is important")
        stats = buf.stats()
        assert stats["entries"] == 1
        assert stats["budget"] == 20_000
        assert stats["has_checkpoint"] is False
        assert "utilization" in stats

    def test_clear(self):
        buf = DialecticContextBuffer(depth=2)
        buf.append(1, "anti", "Finding about X is important")
        buf._checkpoint_text = "old summary"
        buf.clear()
        assert len(buf.entries) == 0
        assert buf._checkpoint_text == ""
        assert buf.render() == ""
