# PROOF: mekhane/periskope/tests/test_phi3_phi7_boundary.py
# PURPOSE: periskope モジュールの phi3_phi7_boundary に対するテスト
"""Boundary case tests for D3 (Φ3 LLM classification) and D6 (Φ7 threshold escalation).

Tests ensure:
- LLM failure gracefully falls back to keyword classification
- Ambiguous queries are handled without crashing
- Φ7 threshold escalates per iteration as designed
"""
import pytest
from unittest.mock import AsyncMock, patch

from mekhane.periskope.cognition.phi3_context import (
    phi3_context_setting,
    _classify_query_keyword,
    _classify_query_llm,
    ContextPlan,
)
from mekhane.periskope.cognition.phi7_belief_update import (
    phi7_belief_update,
    BeliefUpdate,
)
from mekhane.periskope.cognition.phi7_query_feedback import (
    phi7_query_feedback,
    _select_strategy,
)


# ── D3v: Φ3 Boundary Tests ─────────────────────────────────


class TestPhi3KeywordFallback:
    """Test keyword-based classification (fallback path)."""

    def test_academic_keywords(self):
        assert _classify_query_keyword("arxiv paper on transformers") == "academic"
        assert _classify_query_keyword("論文 FEP") == "academic"

    def test_implementation_keywords(self):
        assert _classify_query_keyword("how to implement BERT in Python") == "implementation"
        assert _classify_query_keyword("実装 方法 PyTorch") == "implementation"

    def test_news_keywords(self):
        assert _classify_query_keyword("latest GPT-5 release") == "news"
        assert _classify_query_keyword("最新 AI ニュース") == "news"

    def test_concept_default(self):
        assert _classify_query_keyword("free energy principle") == "concept"
        assert _classify_query_keyword("自由エネルギー原理") == "concept"

    def test_ambiguous_query(self):
        """Ambiguous queries that could be multiple categories."""
        # "latest paper" has both news and academic keywords — news takes priority
        result = _classify_query_keyword("latest paper on active inference")
        assert result in {"news", "academic"}  # either is acceptable

    def test_empty_query(self):
        assert _classify_query_keyword("") == "concept"


@pytest.mark.asyncio
class TestPhi3LLMClassification:

    async def test_llm_returns_valid_type(self):
        with patch(
            "mekhane.periskope.cognition.phi3_context._llm_ask",
            new_callable=AsyncMock,
            return_value="academic",
        ):
            result = await _classify_query_llm("study on neural correlates of FEP")
            assert result == "academic"

    async def test_llm_returns_invalid_type(self):
        """Invalid LLM output should return None (trigger fallback)."""
        with patch(
            "mekhane.periskope.cognition.phi3_context._llm_ask",
            new_callable=AsyncMock,
            return_value="scientific_research",
        ):
            result = await _classify_query_llm("some query")
            assert result is None

    async def test_llm_returns_empty(self):
        with patch(
            "mekhane.periskope.cognition.phi3_context._llm_ask",
            new_callable=AsyncMock,
            return_value="",
        ):
            result = await _classify_query_llm("some query")
            assert result is None

    async def test_llm_ask_failure_returns_none(self):
        """When _llm_ask fails internally (returns ''), _classify_query_llm returns None."""
        with patch(
            "mekhane.periskope.cognition.phi3_context._llm_ask",
            new_callable=AsyncMock,
            return_value="",
        ):
            result = await _classify_query_llm("some query")
            assert result is None


@pytest.mark.asyncio
class TestPhi3ContextSettingIntegration:

    async def test_llm_success_uses_llm_classification(self):
        """When LLM succeeds, should use LLM classification."""
        with patch(
            "mekhane.periskope.cognition.phi3_context._llm_ask",
            new_callable=AsyncMock,
            return_value="academic",
        ):
            plan = await phi3_context_setting(
                "free energy principle",
                candidates=["FEP overview", "FEP critique"],
            )
            assert isinstance(plan, ContextPlan)
            assert plan.query_type == "academic"
            assert "llm" in plan.reasoning

    async def test_llm_failure_falls_back_to_keyword(self):
        """When LLM fails, should fall back to keyword classification."""
        with patch(
            "mekhane.periskope.cognition.phi3_context._llm_ask",
            new_callable=AsyncMock,
            return_value="",
        ):
            plan = await phi3_context_setting(
                "how to implement active inference",
                candidates=["implement AI", "active inference code"],
            )
            assert isinstance(plan, ContextPlan)
            assert plan.query_type == "implementation"
            assert "keyword" in plan.reasoning

    async def test_site_scoped_queries_for_concept(self):
        """Concept queries should generate site-scoped queries."""
        with patch(
            "mekhane.periskope.cognition.phi3_context._llm_ask",
            new_callable=AsyncMock,
            return_value="concept",
        ):
            plan = await phi3_context_setting(
                "Bayesian brain",
                candidates=["Bayesian brain"],
            )
            assert len(plan.site_scoped_queries) > 0
            assert any("qiita.com" in q for q in plan.site_scoped_queries)


# ── D6v: Φ7 Threshold Escalation Tests ─────────────────────


@pytest.mark.asyncio
class TestPhi7ThresholdEscalation:

    async def test_iteration_0_base_threshold(self):
        """Iteration 0: threshold = 0.5 (base). Score 0.4 → should loop."""
        result = await phi7_belief_update(
            query="test", overall_score=0.4,
            synthesis_texts=["sparse"], iteration=0,
            loop_threshold=0.5,
        )
        # residual = 0.6, dynamic_threshold = max(0.2, 0.5 - 0*0.15) = 0.5
        assert result.should_loop is True

    async def test_iteration_1_stricter_threshold(self):
        """Iteration 1: threshold = 0.40. Score 0.55 → residual 0.45 > 0.40, should loop."""
        mock_response = "more specific query\nnarrower search"
        with patch(
            "mekhane.periskope.cognition.phi7_belief_update._llm_ask",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await phi7_belief_update(
                query="test", overall_score=0.55,
                synthesis_texts=["partial"], iteration=1,
                loop_threshold=0.5, max_iterations=3,
            )
            # residual = 0.45, dynamic_threshold = max(0.2, 0.5 - 1*0.10) = 0.40
            assert result.should_loop is True
            assert result.residual_error == pytest.approx(0.45)

    async def test_iteration_1_score_passes_stricter_threshold(self):
        """Iteration 1: Score 0.7 → residual 0.3 < 0.40, should NOT loop."""
        result = await phi7_belief_update(
            query="test", overall_score=0.7,
            synthesis_texts=["good"], iteration=1,
            loop_threshold=0.5, max_iterations=3,
        )
        # residual = 0.3, dynamic_threshold = 0.40 → 0.3 < 0.40 → no loop
        assert result.should_loop is False

    async def test_iteration_2_strictest_threshold(self):
        """Iteration 2: threshold = 0.30. Score 0.65 → residual 0.35 > 0.30, should loop."""
        mock_response = "ultra specific query"
        with patch(
            "mekhane.periskope.cognition.phi7_belief_update._llm_ask",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await phi7_belief_update(
                query="test", overall_score=0.65,
                synthesis_texts=["decent"], iteration=2,
                loop_threshold=0.5, max_iterations=4,
            )
            # residual = 0.35, dynamic_threshold = max(0.2, 0.5 - 2*0.10) = 0.30
            assert result.should_loop is True

    async def test_threshold_floor_at_02(self):
        """Threshold should never go below 0.2."""
        result = await phi7_belief_update(
            query="test", overall_score=0.85,
            synthesis_texts=["excellent"], iteration=10,
            loop_threshold=0.5, max_iterations=20,
        )
        # dynamic_threshold = max(0.2, 0.5 - 10*0.10) = max(0.2, -0.5) = 0.2
        # residual = 0.15 < 0.2 → no loop
        assert result.should_loop is False

    async def test_same_score_different_fate_by_iteration(self):
        """Same score (0.6): passes at iter 0 (req 0.5), fails at iter 1 (req 0.4)."""
        # Iter 0: residual 0.4, threshold 0.5 → 0.4 < 0.5 → no loop
        result_0 = await phi7_belief_update(
            query="test", overall_score=0.60,
            synthesis_texts=["ok"], iteration=0,
            loop_threshold=0.5,
        )
        assert result_0.should_loop is False

        # Iter 1: residual 0.4, threshold 0.4 → 0.4 > 0.4 is False, so to test failure, score=0.55 -> residual 0.45.
        # Wait, the test says same score different fate.
        # Iter 0: threshold 0.5. Score = 0.55. residual 0.45 < 0.5 -> NO LOOP
        # Iter 1: threshold 0.4. Score = 0.55. residual 0.45 > 0.4 -> LOOP
        result_0 = await phi7_belief_update(
            query="test", overall_score=0.55,
            synthesis_texts=["ok"], iteration=0,
            loop_threshold=0.5,
        )
        assert result_0.should_loop is False
        
        mock_response = "follow up query"
        with patch(
            "mekhane.periskope.cognition.phi7_belief_update._llm_ask",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result_1 = await phi7_belief_update(
                query="test", overall_score=0.55,
                synthesis_texts=["ok"], iteration=1,
                loop_threshold=0.5, max_iterations=3,
            )
            assert result_1.should_loop is True


# ── D6v: Φ7 QPP Gating Tests (V5 Adaptive Depth Control) ──────


class TestPhi7QPPGating:
    """Test adaptive strategy selection based on info_gain (QPP)."""

    def test_high_info_gain_selects_narrowing(self):
        """info_gain > threshold * 3 → 'narrowing'"""
        strategy = _select_strategy(1, info_gain=0.2, saturation_threshold=0.035)
        assert strategy == "narrowing"

        result = phi7_query_feedback(
            iteration=1,
            reasoning_next_queries=["q1"],
            plan_step2=["step2_query"],
            info_gain=0.2,
            saturation_threshold=0.035,
        )
        assert result.strategy == "narrowing"
        assert result.plan_injected is True
        assert "plan_step2" in result.sources.values()

    def test_medium_info_gain_selects_verification(self):
        """threshold < info_gain <= threshold * 3 → 'verification'"""
        strategy = _select_strategy(1, info_gain=0.08, saturation_threshold=0.035)
        assert strategy == "verification"

        result = phi7_query_feedback(
            iteration=1,
            reasoning_next_queries=["q1"],
            plan_step3=["step3_query"],
            info_gain=0.08,
            saturation_threshold=0.035,
        )
        assert result.strategy == "verification"
        assert result.plan_injected is True
        assert "plan_step3" in result.sources.values()

    def test_low_info_gain_selects_assumptions(self):
        """info_gain <= threshold → 'assumption_check'"""
        strategy = _select_strategy(1, info_gain=0.02, saturation_threshold=0.035)
        assert strategy == "assumption_check"

        result = phi7_query_feedback(
            iteration=1,
            reasoning_next_queries=["q1"],
            unchecked_assumptions=["implicit assumption"],
            info_gain=0.02,
            saturation_threshold=0.035,
        )
        assert result.strategy == "assumption_check"
        assert result.plan_injected is False
        assert "v1_assumption" in result.sources.values()

    def test_no_info_gain_falls_back_to_iteration(self):
        """When info_gain is None, fall back to legacy iteration-based strategy."""
        assert _select_strategy(1, info_gain=None, saturation_threshold=0.035) == "narrowing"
        assert _select_strategy(2, info_gain=None, saturation_threshold=0.035) == "verification"
        assert _select_strategy(3, info_gain=None, saturation_threshold=0.035) == "assumption_check"
        assert _select_strategy(4, info_gain=None, saturation_threshold=0.035) == "assumption_check"

        result = phi7_query_feedback(
            iteration=2,
            reasoning_next_queries=[],
            plan_step3=["s3"],
            info_gain=None,
        )
        assert result.strategy == "verification"
        assert result.plan_injected is True
