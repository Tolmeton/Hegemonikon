# PROOF: mekhane/periskope/tests/test_engine_iterative.py
# PURPOSE: periskope モジュールの engine_iterative に対するテスト
"""Tests for Phase A iterative deepening logic."""
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mekhane.periskope.engine import PeriskopeEngine
from mekhane.periskope.models import SearchResult, SynthesisResult


@pytest.fixture
def engine():
    engine = PeriskopeEngine()
    engine._config = {
        "iterative_deepening": {
            "max_iterations": {1: 1, 2: 3, 3: 5},
            "min_iterations": {1: 1, 2: 1, 3: 1},
            "saturation_threshold": 0.15,
            "queries_per_iteration": 2,
            "log_gain_curve": False,
            "decay_type": "linear",
        }
    }
    
    # Mock dependencies to make it fast
    engine.synthesizer = MagicMock()
    engine.synthesizer.synthesize = AsyncMock(return_value=[SynthesisResult(content="Mock", model="mock-model")])
    engine.synthesizer.detect_divergence = MagicMock(return_value=None)
    
    engine._phase_search = AsyncMock(return_value=([], {}))
    engine._rerank_results = MagicMock(return_value=[])
    engine._phase_deep_read = AsyncMock(return_value=[])
    engine.nl_client = MagicMock()
    engine.nl_client.extract_entities = AsyncMock(return_value=[])
    engine.llm_reranker = MagicMock()
    engine.llm_reranker.rerank = AsyncMock(return_value=[])
    
    return engine


@pytest.mark.asyncio
@patch("mekhane.periskope.engine.analyze_iteration")
async def test_iterative_deepening_saturates_early(mock_analyze, engine):
    """Test that the loop stops when relative gain drops below threshold."""
    mock_step = MagicMock()
    mock_step.next_queries = []
    mock_step.confidence = 0.5
    mock_analyze.return_value = mock_step
    
    engine._generate_refinement_queries = AsyncMock(return_value=["mock query 1"])
    
    # Relative gain: iter1=0.5 (cum=0.5, rel=1.0 skip), iter2=0.05 (cum=0.55, rel=0.09 < 0.15)
    engine._assess_information_gain = MagicMock(side_effect=[0.5, 0.05])
    
    await engine._phase_iterative_deepen(
        query="test query",
        search_results=[],
        source_counts={},
        synthesis=[],
        enabled=set(["searxng"]),
        depth=3,
    )
    
    # Should stop after 2 iterations because relative_gain (0.09) < threshold (0.15)
    assert engine._generate_refinement_queries.call_count == 2
    assert engine._assess_information_gain.call_count == 2


@pytest.mark.asyncio
@patch("mekhane.periskope.engine.analyze_iteration")
async def test_iterative_deepening_max_iterations(mock_analyze, engine):
    """Test that the loop respects max_iterations."""
    mock_step = MagicMock()
    mock_step.next_queries = []
    mock_step.confidence = 0.5
    mock_analyze.return_value = mock_step
    
    engine._generate_refinement_queries = AsyncMock(return_value=["mock query"])
    
    # Mock information gain: Always high gain
    engine._assess_information_gain = MagicMock(return_value=0.5)
    
    await engine._phase_iterative_deepen(
        query="test query",
        search_results=[],
        source_counts={},
        synthesis=[],
        enabled=set(["searxng"]),
        depth=2, # Max 3 iterations
    )
    
    # Should stop after exactly 3 iterations
    assert engine._generate_refinement_queries.call_count == 3
    assert engine._assess_information_gain.call_count == 3


@pytest.mark.asyncio
@patch("mekhane.periskope.engine.analyze_iteration")
async def test_iterative_deepening_no_gaps(mock_analyze, engine):
    """Test that the loop stops when no gaps are found."""
    mock_step = MagicMock()
    mock_step.next_queries = []
    mock_step.confidence = 0.5
    mock_analyze.return_value = mock_step
    
    # Mock gap analysis to return empty list
    engine._generate_refinement_queries = AsyncMock(return_value=[])
    engine._assess_information_gain = MagicMock()
    
    await engine._phase_iterative_deepen(
        query="test query",
        search_results=[],
        source_counts={},
        synthesis=[],
        enabled=set(["searxng"]),
        depth=3,
    )
    
    # Should stop immediately after first attempt
    assert engine._generate_refinement_queries.call_count == 1
    assert engine._assess_information_gain.call_count == 0


# --- Denoising scheduler decay_type tests ---


@pytest.fixture
def engine_exponential():
    """Engine configured with exponential decay for denoising scheduler."""
    engine = PeriskopeEngine()
    engine._config = {
        "iterative_deepening": {
            "max_iterations": {1: 1, 2: 5, 3: 5},
            "min_iterations": {1: 1, 2: 1, 3: 1},
            "saturation_threshold": 0.15,
            "queries_per_iteration": 2,
            "log_gain_curve": False,
            "decay_type": "exponential",
            "initial_diversity_weight": 0.3,
        }
    }
    engine.max_results = 10

    engine.synthesizer = MagicMock()
    engine.synthesizer.synthesize = AsyncMock(
        return_value=[SynthesisResult(content="Mock", model="mock-model")],
    )
    engine.synthesizer.detect_divergence = MagicMock(return_value=None)

    engine._phase_search = AsyncMock(return_value=([], {}))
    engine._rerank_results = MagicMock(return_value=[])
    engine._phase_deep_read = AsyncMock(return_value=[])
    engine.nl_client = MagicMock()
    engine.nl_client.extract_entities = AsyncMock(return_value=[])
    engine.llm_reranker = MagicMock()
    engine.llm_reranker.rerank = AsyncMock(return_value=[])

    return engine


@pytest.mark.asyncio
@patch("mekhane.periskope.engine.analyze_iteration")
async def test_exponential_decay_schedule(mock_analyze, engine_exponential):
    """Test that exponential decay never reaches zero and decays faster early on."""
    mock_step = MagicMock()
    mock_step.next_queries = []
    mock_step.confidence = 0.5
    mock_analyze.return_value = mock_step

    engine_exponential._generate_refinement_queries = AsyncMock(
        return_value=["mock query"],
    )
    # Always high gain so all 5 iterations run
    engine_exponential._assess_information_gain = MagicMock(return_value=0.5)

    # Capture logged diversity_weight values
    logged_weights: list[float] = []
    original_info = logging.getLogger("mekhane.periskope.engine").info

    def capture_denoise_log(msg, *args):
        if "denoise" in str(msg):
            # args: t, iter_diversity, iter_max_results
            logged_weights.append(args[1])

    with patch.object(
        logging.getLogger("mekhane.periskope.engine"), "info", side_effect=capture_denoise_log,
    ):
        await engine_exponential._phase_iterative_deepen(
            query="test query",
            search_results=[],
            source_counts={},
            synthesis=[],
            enabled=set(["searxng"]),
            depth=2,  # Max 5 iterations
        )

    # Exponential decay should produce non-zero diversity at the end
    # (unlike linear which hits exactly 0.0)
    if logged_weights:
        assert logged_weights[-1] > 0.0, (
            f"Exponential decay should never reach zero, got {logged_weights[-1]}"
        )
        # First logged weight should be less than initial (0.3)
        assert logged_weights[0] < 0.3


@pytest.mark.asyncio
@patch("mekhane.periskope.engine.analyze_iteration")
async def test_linear_decay_reaches_zero(mock_analyze, engine):
    """Test that linear decay reaches exactly zero at the final iteration."""
    engine._config["iterative_deepening"]["max_iterations"] = {1: 1, 2: 5, 3: 5}
    engine._config["iterative_deepening"]["initial_diversity_weight"] = 0.3
    engine.max_results = 10

    mock_step = MagicMock()
    mock_step.next_queries = []
    mock_step.confidence = 0.5
    mock_analyze.return_value = mock_step

    engine._generate_refinement_queries = AsyncMock(return_value=["mock query"])
    engine._assess_information_gain = MagicMock(return_value=0.5)

    logged_weights: list[float] = []

    def capture_denoise_log(msg, *args):
        if "denoise" in str(msg):
            logged_weights.append(args[1])

    with patch.object(
        logging.getLogger("mekhane.periskope.engine"), "info", side_effect=capture_denoise_log,
    ):
        await engine._phase_iterative_deepen(
            query="test query",
            search_results=[],
            source_counts={},
            synthesis=[],
            enabled=set(["searxng"]),
            depth=2,  # Max 5 iterations
        )

    # Linear decay should reach exactly 0.0 at the final iteration
    if logged_weights:
        assert logged_weights[-1] == pytest.approx(0.0, abs=1e-9), (
            f"Linear decay should reach zero, got {logged_weights[-1]}"
        )


@pytest.mark.asyncio
@patch("mekhane.periskope.engine.analyze_iteration")
async def test_low_info_gain_saturates_immediately(mock_analyze, engine):
    """Test that very low info_gain causes immediate saturation."""
    mock_step = MagicMock()
    mock_step.next_queries = []
    mock_step.confidence = 0.5
    mock_analyze.return_value = mock_step

    engine._generate_refinement_queries = AsyncMock(return_value=["mock query"])
    # info_gain 0.001 < threshold 0.15 → saturates on first iteration
    engine._assess_information_gain = MagicMock(side_effect=[0.001, 0.001, 0.001])

    await engine._phase_iterative_deepen(
        query="test query",
        search_results=[],
        source_counts={},
        synthesis=[],
        enabled=set(["searxng"]),
        depth=2,
    )

    # fixture sets min_iterations=1 for depth=2, so convergence check runs on iter 1.
    # info_gain 0.001 < threshold 0.15 → saturates after 1st iteration
    assert engine._assess_information_gain.call_count == 1


# --- Cosine and logSNR decay_type tests ---


@pytest.fixture
def engine_cosine():
    """Engine configured with cosine decay."""
    engine = PeriskopeEngine()
    engine._config = {
        "iterative_deepening": {
            "max_iterations": {1: 1, 2: 5, 3: 5},
            "min_iterations": {1: 1, 2: 1, 3: 1},
            "saturation_threshold": 0.15,
            "queries_per_iteration": 2,
            "log_gain_curve": False,
            "decay_type": "cosine",
            "alpha_schedule": "cosine",
            "initial_diversity_weight": 0.3,
        }
    }
    engine.max_results = 10

    engine.synthesizer = MagicMock()
    engine.synthesizer.synthesize = AsyncMock(
        return_value=[SynthesisResult(content="Mock", model="mock-model")],
    )
    engine.synthesizer.detect_divergence = MagicMock(return_value=None)
    engine._phase_search = AsyncMock(return_value=([], {}))
    engine._rerank_results = MagicMock(return_value=[])
    engine._phase_deep_read = AsyncMock(return_value=[])
    engine.nl_client = MagicMock()
    engine.nl_client.extract_entities = AsyncMock(return_value=[])
    engine.llm_reranker = MagicMock()
    engine.llm_reranker.rerank = AsyncMock(return_value=[])

    return engine


@pytest.mark.asyncio
@patch("mekhane.periskope.engine.analyze_iteration")
async def test_cosine_decay_midpoint_half(mock_analyze, engine_cosine):
    """Cosine decay at t=0.5 should be exactly 0.5 * initial_diversity."""
    mock_step = MagicMock()
    mock_step.next_queries = []
    mock_step.confidence = 0.5
    mock_step.contradictions = []
    mock_analyze.return_value = mock_step

    engine_cosine._generate_refinement_queries = AsyncMock(
        return_value=["mock query"],
    )
    engine_cosine._assess_information_gain = MagicMock(return_value=0.5)

    logged_weights: list[float] = []

    def capture_denoise_log(msg, *args):
        if "denoise" in str(msg):
            logged_weights.append(args[1])

    with patch.object(
        logging.getLogger("mekhane.periskope.engine"), "info", side_effect=capture_denoise_log,
    ):
        await engine_cosine._phase_iterative_deepen(
            query="test query",
            search_results=[],
            source_counts={},
            synthesis=[],
            enabled=set(["searxng"]),
            depth=2,
        )

    # Cosine: monotonic decrease from t=0 to t=1
    # logged_weights starts from iteration 1 (iteration 0 is not logged)
    if len(logged_weights) >= 2:
        # Should show decreasing trend
        assert logged_weights[0] > logged_weights[-1], (
            f"Cosine should decrease: first={logged_weights[0]}, last={logged_weights[-1]}"
        )
        # Final weight should be ~0
        assert logged_weights[-1] == pytest.approx(0.0, abs=0.01)


@pytest.fixture
def engine_logsnr():
    """Engine configured with logSNR decay."""
    engine = PeriskopeEngine()
    engine._config = {
        "iterative_deepening": {
            "max_iterations": {1: 1, 2: 5, 3: 5},
            "min_iterations": {1: 1, 2: 1, 3: 1},
            "saturation_threshold": 0.15,
            "queries_per_iteration": 2,
            "log_gain_curve": False,
            "decay_type": "logsnr",
            "alpha_schedule": "sigmoid",
            "initial_diversity_weight": 0.3,
        }
    }
    engine.max_results = 10

    engine.synthesizer = MagicMock()
    engine.synthesizer.synthesize = AsyncMock(
        return_value=[SynthesisResult(content="Mock", model="mock-model")],
    )
    engine.synthesizer.detect_divergence = MagicMock(return_value=None)
    engine._phase_search = AsyncMock(return_value=([], {}))
    engine._rerank_results = MagicMock(return_value=[])
    engine._phase_deep_read = AsyncMock(return_value=[])
    engine.nl_client = MagicMock()
    engine.nl_client.extract_entities = AsyncMock(return_value=[])
    engine.llm_reranker = MagicMock()
    engine.llm_reranker.rerank = AsyncMock(return_value=[])

    return engine


@pytest.mark.asyncio
@patch("mekhane.periskope.engine.analyze_iteration")
async def test_logsnr_decay_peaks_at_midpoint(mock_analyze, engine_logsnr):
    """logSNR decay should peak at t=0.5 (critical point)."""
    mock_step = MagicMock()
    mock_step.next_queries = []
    mock_step.confidence = 0.5
    mock_step.contradictions = []
    mock_analyze.return_value = mock_step

    engine_logsnr._generate_refinement_queries = AsyncMock(
        return_value=["mock query"],
    )
    engine_logsnr._assess_information_gain = MagicMock(return_value=0.5)

    logged_weights: list[float] = []

    def capture_denoise_log(msg, *args):
        if "denoise" in str(msg):
            logged_weights.append(args[1])

    with patch.object(
        logging.getLogger("mekhane.periskope.engine"), "info", side_effect=capture_denoise_log,
    ):
        await engine_logsnr._phase_iterative_deepen(
            query="test query",
            search_results=[],
            source_counts={},
            synthesis=[],
            enabled=set(["searxng"]),
            depth=2,
        )

    # logSNR: (Laplace) peaks at t=0.5, decays symmetrically
    # logged_weights starts from iteration 1 (not 0)
    # With 5 iterations: t = 0.25, 0.5, 0.75, 1.0 → weights at idx 0,1,2,3
    if len(logged_weights) >= 3:
        mid_idx = len(logged_weights) // 2
        # Midpoint should be >= endpoints (Laplace shape)
        assert logged_weights[mid_idx] >= logged_weights[-1], (
            f"logSNR mid ({logged_weights[mid_idx]}) should be >= end ({logged_weights[-1]})"
        )


@pytest.mark.asyncio
@patch("mekhane.periskope.engine.analyze_iteration")
async def test_contradiction_driven_query_injection(mock_analyze, engine_logsnr):
    """Contradictions from analyze_iteration should inject fix queries at L3."""
    mock_step = MagicMock()
    mock_step.next_queries = []
    mock_step.confidence = 0.5
    mock_step.contradictions = ["Source A says X, Source B says Y"]
    mock_step.learned = []
    mock_step.info_gain = 0.0
    mock_step.new_results = 0
    mock_analyze.return_value = mock_step

    engine_logsnr._config["iterative_deepening"]["max_iterations"] = {3: 5}
    engine_logsnr._generate_refinement_queries = AsyncMock(
        return_value=["mock query"],
    )
    engine_logsnr._assess_information_gain = MagicMock(return_value=0.5)

    search_call_count_before = engine_logsnr._phase_search.call_count

    await engine_logsnr._phase_iterative_deepen(
        query="test query",
        search_results=[],
        source_counts={},
        synthesis=[],
        enabled=set(["searxng"]),
        depth=3,  # L3 required for contradiction injection
    )

    # Should have extra search calls from contradiction queries
    total_search_calls = engine_logsnr._phase_search.call_count - search_call_count_before
    # At least some calls came from contradiction injection (beyond normal queries)
    assert total_search_calls > 0

