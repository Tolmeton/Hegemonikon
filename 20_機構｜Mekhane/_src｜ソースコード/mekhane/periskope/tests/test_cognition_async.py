# PROOF: mekhane/periskope/tests/test_cognition_async.py
# PURPOSE: periskope モジュールの cognition_async に対するテスト
"""Tests for async cognition functions with mocked LLM calls.

Patches each Φ module's _llm_ask to avoid real OchemaService/gRPC calls.
Verifies input → output contract, parsing logic, and edge cases.
"""
import pytest
from unittest.mock import AsyncMock, patch

from mekhane.periskope.cognition.phi1_blind_spot import (
    phi1_blind_spot_analysis,
    phi1_counterfactual_queries,
)
from mekhane.periskope.cognition.phi2_divergent import phi2_divergent_thinking
from mekhane.periskope.cognition.phi4_convergent import (
    phi4_pre_search_ranking,
    phi4_post_search_framing,
    RankedQuery,
    DecisionFrame,
)
from mekhane.periskope.cognition.phi7_belief_update import (
    phi7_belief_update,
    BeliefUpdate,
)


# ── Φ1 Tests ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_phi1_blind_spot_returns_queries():
    mock_response = "What are the ethical implications of X?\nHow does Y compare to Z?"
    with patch(
        "mekhane.periskope.cognition.phi1_blind_spot._llm_ask",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result = await phi1_blind_spot_analysis("free energy principle")
        assert len(result) == 2
        assert "ethical" in result[0].lower()


@pytest.mark.asyncio
async def test_phi1_blind_spot_none_response():
    with patch(
        "mekhane.periskope.cognition.phi1_blind_spot._llm_ask",
        new_callable=AsyncMock,
        return_value="NONE",
    ):
        result = await phi1_blind_spot_analysis("well-studied topic")
        assert result == []


@pytest.mark.asyncio
async def test_phi1_blind_spot_empty_response():
    with patch(
        "mekhane.periskope.cognition.phi1_blind_spot._llm_ask",
        new_callable=AsyncMock,
        return_value="",
    ):
        result = await phi1_blind_spot_analysis("anything")
        assert result == []


@pytest.mark.asyncio
async def test_phi1_counterfactual():
    mock_response = "What if the brain did not minimize prediction error?\nWhat if free energy were not conserved?"
    with patch(
        "mekhane.periskope.cognition.phi1_blind_spot._llm_ask",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result = await phi1_counterfactual_queries("free energy principle", max_queries=2)
        assert len(result) == 2


# ── Φ2 Tests ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_phi2_divergent_with_llm():
    mock_response = (
        "predictive processing theories\n"
        "active inference computational models\n"
        "criticisms of free energy principle\n"
        "history of Bayesian brain hypothesis"
    )
    with patch(
        "mekhane.periskope.cognition.phi2_divergent._llm_ask",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result = await phi2_divergent_thinking(
            "free energy principle", max_candidates=6,
        )
        assert len(result) >= 2  # original + divergent
        assert result[0] == "free energy principle"  # original is always first


@pytest.mark.asyncio
async def test_phi2_divergent_llm_failure():
    with patch(
        "mekhane.periskope.cognition.phi2_divergent._llm_ask",
        new_callable=AsyncMock,
        return_value="",
    ):
        result = await phi2_divergent_thinking("test query", max_candidates=5)
        assert result == ["test query"]  # only original when LLM fails


@pytest.mark.asyncio
async def test_phi2_divergent_deduplication():
    mock_response = "test query\ntest query\nnew query"
    with patch(
        "mekhane.periskope.cognition.phi2_divergent._llm_ask",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result = await phi2_divergent_thinking("test query", max_candidates=5)
        assert result.count("test query") == 1  # no duplicates
        assert "new query" in result


# ── Φ4 Tests ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_phi4_pre_search_ranking():
    mock_response = "[1] 8 9\n[2] 6 7\n[3] 9 5"
    with patch(
        "mekhane.periskope.cognition.phi4_convergent._llm_ask",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result = await phi4_pre_search_ranking(
            "test goal",
            ["query A", "query B", "query C"],
        )
        assert len(result) == 3
        assert all(isinstance(r, RankedQuery) for r in result)
        # Sorted by score desc
        assert result[0].score >= result[1].score >= result[2].score


@pytest.mark.asyncio
async def test_phi4_pre_search_with_known_context():
    """G3: known_context should be injected into the LLM prompt."""
    captured_prompt = {}

    async def capture_llm_ask(prompt, **kwargs):
        captured_prompt["text"] = prompt
        return "[1] 3 9\n[2] 8 7"

    with patch(
        "mekhane.periskope.cognition.phi4_convergent._llm_ask",
        side_effect=capture_llm_ask,
    ):
        result = await phi4_pre_search_ranking(
            "active inference",
            ["query A", "query B"],
            known_context="I already know that FEP minimizes surprise.",
        )
        assert len(result) == 2
        # Verify context was injected
        assert "The researcher already knows" in captured_prompt["text"]
        assert "FEP minimizes surprise" in captured_prompt["text"]
        assert "NEW TO THE RESEARCHER" in captured_prompt["text"]


@pytest.mark.asyncio
async def test_phi4_pre_search_without_known_context():
    """Without known_context, no context block in prompt."""
    captured_prompt = {}

    async def capture_llm_ask(prompt, **kwargs):
        captured_prompt["text"] = prompt
        return "[1] 8 9\n[2] 6 7"

    with patch(
        "mekhane.periskope.cognition.phi4_convergent._llm_ask",
        side_effect=capture_llm_ask,
    ):
        result = await phi4_pre_search_ranking(
            "test goal", ["query A", "query B"],
        )
        assert len(result) == 2
        assert "The researcher already knows" not in captured_prompt["text"]


@pytest.mark.asyncio
async def test_phi4_efe_dynamic_weighting():
    """F3: Verify EFE dynamic weighting effect.

    With rich known_context (>=10 words), novelty weight should increase (0.6),
    causing high-novelty/low-relevance queries to score relatively higher
    compared to no-context mode (0.5/0.5).
    """
    # LLM returns: query A (novelty=9, relevance=3), query B (novelty=3, relevance=9)
    mock_response = "[1] 9 3\n[2] 3 9"

    rich_context = "This is a test context with more than ten words to trigger the dynamic weighting mechanism"

    # With rich context: w_novelty=0.6, w_relevance=0.4
    # A: (0.6*9 + 0.4*3)/10 = 0.66
    # B: (0.6*3 + 0.4*9)/10 = 0.54
    with patch(
        "mekhane.periskope.cognition.phi4_convergent._llm_ask",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result_rich = await phi4_pre_search_ranking(
            "test", ["query A", "query B"],
            known_context=rich_context,
        )

    # Without context: w_novelty=0.5, w_relevance=0.5
    # A: (0.5*9 + 0.5*3)/10 = 0.60
    # B: (0.5*3 + 0.5*9)/10 = 0.60
    with patch(
        "mekhane.periskope.cognition.phi4_convergent._llm_ask",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result_no_ctx = await phi4_pre_search_ranking(
            "test", ["query A", "query B"],
        )

    # With context, novelty-heavy query A should score higher than B
    assert result_rich[0].query == "query A"
    assert result_rich[0].score > result_rich[1].score

    # Without context, both should score equally (0.60 each)
    assert abs(result_no_ctx[0].score - result_no_ctx[1].score) < 0.01


@pytest.mark.asyncio
async def test_phi4_pre_search_fallback():
    """When LLM fails, position-based fallback scores are used."""
    with patch(
        "mekhane.periskope.cognition.phi4_convergent._llm_ask",
        new_callable=AsyncMock,
        return_value="invalid output",
    ):
        result = await phi4_pre_search_ranking(
            "goal", ["q1", "q2", "q3"],
        )
        assert len(result) == 3
        assert result[0].score == 1.0  # position-based: first=1.0


@pytest.mark.asyncio
async def test_phi4_post_search_framing():
    mock_response = (
        "KEY FINDINGS:\n"
        "- FEP unifies perception and action under Bayesian inference\n"
        "- Active inference extends FEP to behavior\n"
        "OPEN QUESTIONS:\n"
        "- Is FEP falsifiable?\n"
        "DECISION OPTIONS:\n"
        "- Read Friston 2010 for foundations\n"
        "CONFIDENCE: 75%"
    )
    with patch(
        "mekhane.periskope.cognition.phi4_convergent._llm_ask",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result = await phi4_post_search_framing(
            "free energy principle", ["synthesis text here"],
        )
        assert isinstance(result, DecisionFrame)
        assert len(result.key_findings) == 2
        assert len(result.open_questions) == 1
        assert result.confidence == 0.75


@pytest.mark.asyncio
async def test_phi4_post_search_empty():
    with patch(
        "mekhane.periskope.cognition.phi4_convergent._llm_ask",
        new_callable=AsyncMock,
        return_value="",
    ):
        result = await phi4_post_search_framing("q", ["text"])
        assert isinstance(result, DecisionFrame)
        assert result.key_findings == []
        assert result.confidence == 0.0


# ── Φ7 Tests ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_phi7_no_loop_high_quality():
    """High quality score → no loop needed, no LLM call."""
    result = await phi7_belief_update(
        query="test",
        overall_score=0.8,
        synthesis_texts=["good results"],
        iteration=0,
    )
    assert isinstance(result, BeliefUpdate)
    assert result.residual_error == pytest.approx(0.2)
    assert result.should_loop is False
    assert result.seed_queries == []


@pytest.mark.asyncio
async def test_phi7_loop_low_quality():
    """Low quality score → loop with seed queries from LLM."""
    mock_response = "more specific query about X\nnarrower search on Y"
    with patch(
        "mekhane.periskope.cognition.phi7_belief_update._llm_ask",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result = await phi7_belief_update(
            query="broad topic",
            overall_score=0.3,
            synthesis_texts=["sparse results"],
            coverage_gaps=["No academic sources"],
            iteration=0,
            max_iterations=2,
            loop_threshold=0.5,
        )
        assert result.should_loop is True
        assert result.residual_error == pytest.approx(0.7)
        assert len(result.seed_queries) == 2


@pytest.mark.asyncio
async def test_phi7_max_iterations_reached():
    """Even with low quality, stop looping at max iterations."""
    result = await phi7_belief_update(
        query="test",
        overall_score=0.2,
        synthesis_texts=["bad"],
        iteration=2,
        max_iterations=2,
    )
    assert result.should_loop is False  # iteration >= max
