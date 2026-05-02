# PROOF: [L2/Ergonテスト] <- mekhane/fep/ergon/tests/test_types.py
# REASON: [auto] 初回実装 (2026-03-15)
"""
PROOF: [L2/Ergonテスト] このファイルは存在しなければならない

A0 → Ergon の型定義・分類器・関手ロジックの正当性を検証
   → types, classifier, functors の3モジュールを横断統合テスト
   → 3a+3b 同時の G∘F サイクル = 型と使用の同時検証

Q.E.D.
"""

import pytest

from mekhane.fep.ergon.types import (
    SafetyClass,
    SourceLabel,
    Confidence,
    Plan,
    Task,
    ExecutionResult,
    ErgonBeliefUpdate,
)
from mekhane.fep.ergon.classifier import (
    classify_tool,
    is_boundary_tool,
    requires_confirmation,
    BOUNDARY_TOOL_DEFAULTS,
)
from mekhane.fep.ergon.functors import (
    source_label_rule,
    forgetting_rate,
    compute_prediction_error,
    triangle_identity_check,
)


from mekhane.fep.ergon.protocols import (
    BeliefChannelProtocol,
    ergon_to_channel,
    phi7_to_channel,
    compare_channels,
)


# ━━━ types.py ━━━


# REASON: [auto] クラス TestSafetyClass の実装が必要だったため
class TestSafetyClass:
    """SafetyClass enum tests."""

# REASON: [auto] 品質保証のため
    def test_three_levels(self):
        """SafetyClass has exactly 3 levels."""
        assert len(SafetyClass) == 3

# REASON: [auto] 品質保証のため
    def test_ordering(self):
        """SafetyClass has a natural ordering by risk."""
        levels = list(SafetyClass)
        assert levels[0] == SafetyClass.READ_ONLY
        assert levels[1] == SafetyClass.REVERSIBLE
        assert levels[2] == SafetyClass.IRREVERSIBLE

# REASON: [auto] 品質保証のため
    def test_str_serialization(self):
        """SafetyClass values are string-serializable."""
        assert SafetyClass.READ_ONLY.value == "read_only"
# REASON: [auto] クラス TestSourceLabel の実装が必要だったため
        assert SafetyClass("reversible") == SafetyClass.REVERSIBLE


class TestSourceLabel:
    """SourceLabel enum tests."""

# REASON: [auto] 品質保証のため
    def test_three_levels(self):
        """SourceLabel has exactly 3 levels (N-10 compliance)."""
        assert len(SourceLabel) == 3

# REASON: [auto] 品質保証のため
# REASON: [auto] クラス TestPlanTask の実装が必要だったため
    def test_source_is_highest(self):
        """SOURCE should be the highest precision label."""
        assert SourceLabel.SOURCE.value == "SOURCE"


class TestPlanTask:
    """Plan and Task dataclass tests."""

# REASON: [auto] 品質保証のため
    def test_plan_defaults(self):
        """Plan has sensible defaults."""
        p = Plan(intent="test")
        assert p.depth == "L2"
        assert p.source_label == SourceLabel.TAINT
        assert p.confidence_threshold == 0.6

# REASON: [auto] 品質保証のため
    def test_task_creation(self):
        """Task is constructable from a Plan."""
        t = Task(
            tool_name="hermeneus_run",
            parameters={"ccl": "/noe+"},
            safety_class=SafetyClass.REVERSIBLE,
            deterministic=False,
            plan_id="plan_001",
        )
        assert t.safety_class == SafetyClass.REVERSIBLE
        assert not t.deterministic

# REASON: [auto] 品質保証のため
    def test_execution_result(self):
        """ExecutionResult captures tool output and side effects."""
        r = ExecutionResult(
            plan_id="plan_001",
# REASON: [auto] クラス TestErgonBeliefUpdate の実装が必要だったため
            tool_name="hermeneus_run",
            raw_output={"result": "ok"},
            exit_status="success",
        )
        assert r.exit_status == "success"
        assert isinstance(r.raw_output, dict)


class TestErgonBeliefUpdate:
    """ErgonBeliefUpdate tests."""

# REASON: [auto] 品質保証のため
    def test_basic_creation(self):
        """BeliefUpdate can be created with minimal fields."""
        b = ErgonBeliefUpdate(
            source_label=SourceLabel.SOURCE,
            confidence=Confidence.CERTAIN,
            belief_delta="new",
            summary="Test was deterministic and passed.",
        )
        assert b.confidence == Confidence.CERTAIN
        assert b.prediction_error is None

# REASON: [auto] 品質保証のため
    def test_with_prediction_error(self):
        """BeliefUpdate records prediction errors."""
        b = ErgonBeliefUpdate(
            source_label=SourceLabel.TAINT,
            confidence=Confidence.ESTIMATED,
            belief_delta="refuted",
# REASON: [auto] クラス TestClassifier の実装が必要だったため
            summary="Expected success but got timeout.",
            prediction_error="Exit status: timeout",
        )
        assert b.prediction_error is not None
        assert b.belief_delta == "refuted"


# ━━━ classifier.py ━━━


# REASON: [auto] クラス TestClassifier の実装が必要だったため
class TestClassifier:
    """Tool classifier tests (3b)."""

# REASON: [auto] 品質保証のため
    def test_boundary_tools_count(self):
        """At least 7 boundary tools are classified."""
        boundary_tools = [
            name for name, tc in BOUNDARY_TOOL_DEFAULTS.items()
            if tc.boundary
        ]
        assert len(boundary_tools) >= 7

# REASON: [auto] 品質保証のため
    def test_classify_known_tool(self):
        """Known tools return their default safety_class."""
        assert classify_tool("hermeneus_run") == SafetyClass.REVERSIBLE
        assert classify_tool("ask_with_tools") == SafetyClass.IRREVERSIBLE
        assert classify_tool("periskope_research") == SafetyClass.READ_ONLY

# REASON: [auto] 品質保証のため
    def test_classify_unknown_tool(self):
        """Unknown tools default to READ_ONLY (conservative)."""
        assert classify_tool("unknown_tool_xyz") == SafetyClass.READ_ONLY

# REASON: [auto] 品質保証のため
    def test_override(self):
        """Explicit override takes precedence."""
        assert classify_tool("hermeneus_run", override=SafetyClass.IRREVERSIBLE) == SafetyClass.IRREVERSIBLE

# REASON: [auto] 品質保証のため
    def test_dry_run(self):
        """dry_run=True forces READ_ONLY."""
        assert classify_tool("run_digestor", dry_run=True) == SafetyClass.READ_ONLY

# REASON: [auto] 品質保証のため
# REASON: [auto] クラス TestSourceLabelRule の実装が必要だったため
    def test_is_boundary(self):
        """Boundary status is correctly detected."""
        assert is_boundary_tool("hermeneus_run")
        assert is_boundary_tool("ask_with_tools")
        assert not is_boundary_tool("hermeneus_dispatch")
        assert not is_boundary_tool("unknown_tool")

# REASON: [auto] 品質保証のため
    def test_requires_confirmation(self):
        """IRREVERSIBLE and ask_with_tools require confirmation."""
        assert requires_confirmation("ask_with_tools")
        assert not requires_confirmation("hermeneus_dispatch")


# ━━━ functors.py ━━━


# REASON: [auto] クラス TestSourceLabelRule の実装が必要だったため
class TestSourceLabelRule:
    """source_label_rule tests (R functor §6)."""

# REASON: [auto] 品質保証のため
    def test_deterministic_success(self):
        """Deterministic + success → SOURCE / 確信."""
        task = Task(tool_name="hermeneus_dispatch", deterministic=True)
        result = ExecutionResult(plan_id="", tool_name="hermeneus_dispatch", exit_status="success")
        label, conf = source_label_rule(task, result)
        assert label == SourceLabel.SOURCE
        assert conf == Confidence.CERTAIN

# REASON: [auto] 品質保証のため
    def test_verified_llm_output(self):
        """LLM + verification PASS → SOURCE / 確信 (promotion)."""
# REASON: [auto] クラス TestForgettingRate の実装が必要だったため
        task = Task(tool_name="hermeneus_run", deterministic=False)
        result = ExecutionResult(
            plan_id="", tool_name="hermeneus_run",
            exit_status="success",
            verification={"verdict": "PASS", "confidence": 0.95},
        )
        label, conf = source_label_rule(task, result)
        assert label == SourceLabel.SOURCE
        assert conf == Confidence.CERTAIN

# REASON: [auto] 品質保証のため
    def test_unverified_llm_output(self):
        """LLM without verification → TAINT / 推定."""
        task = Task(tool_name="hermeneus_run", deterministic=False)
        result = ExecutionResult(plan_id="", tool_name="hermeneus_run", exit_status="success")
        label, conf = source_label_rule(task, result)
        assert label == SourceLabel.TAINT
        assert conf == Confidence.ESTIMATED


# REASON: [auto] クラス TestForgettingRate の実装が必要だったため
class TestForgettingRate:
    """Forgetting rate calculation tests."""

# REASON: [auto] 品質保証のため
    def test_empty_result(self):
        """Empty result → 0.0 forgetting rate."""
        result = ExecutionResult(plan_id="", tool_name="test", raw_output="")
        belief = ErgonBeliefUpdate(
            source_label=SourceLabel.TAINT,
            confidence=Confidence.ESTIMATED,
            belief_delta="new",
            summary="",
        )
        assert forgetting_rate(result, belief) == 0.0

# REASON: [auto] 品質保証のため
    def test_full_forgetting(self):
        """Large result + empty belief → high forgetting rate."""
        result = ExecutionResult(plan_id="", tool_name="test", raw_output="x" * 1000)
# REASON: [auto] クラス TestPredictionError の実装が必要だったため
        belief = ErgonBeliefUpdate(
            source_label=SourceLabel.TAINT,
            confidence=Confidence.ESTIMATED,
            belief_delta="new",
            summary="",
        )
        rate = forgetting_rate(result, belief)
        assert rate > 0.9

# REASON: [auto] 品質保証のため
    def test_bounded(self):
        """Forgetting rate is always in [0, 1]."""
        result = ExecutionResult(plan_id="", tool_name="test", raw_output="short")
        belief = ErgonBeliefUpdate(
            source_label=SourceLabel.TAINT,
            confidence=Confidence.ESTIMATED,
            belief_delta="new",
            summary="a very detailed and long belief summary that exceeds the original",
        )
        rate = forgetting_rate(result, belief)
        assert 0.0 <= rate <= 1.0


# REASON: [auto] クラス TestPredictionError の実装が必要だったため
class TestPredictionError:
    """Prediction error computation tests."""

# REASON: [auto] 品質保証のため
    def test_no_error(self):
        """Matching expectations → None."""
        task = Task(tool_name="test", expected_side_effects=["file_create:a.md"])
        result = ExecutionResult(
            plan_id="", tool_name="test",
# REASON: [auto] クラス TestTriangleIdentity の実装が必要だったため
            actual_side_effects=["file_create:a.md"],
        )
        assert compute_prediction_error(task, result) is None

# REASON: [auto] 品質保証のため
    def test_unexpected_side_effect(self):
        """Unexpected side effect → recorded."""
        task = Task(tool_name="test", expected_side_effects=[])
        result = ExecutionResult(
            plan_id="", tool_name="test",
            actual_side_effects=["api_call:gemini"],
        )
        error = compute_prediction_error(task, result)
        assert error is not None
        assert "Unexpected" in error

# REASON: [auto] 品質保証のため
    def test_failure_status(self):
        """Non-success exit status → recorded."""
        task = Task(tool_name="test")
        result = ExecutionResult(plan_id="", tool_name="test", exit_status="timeout")
        error = compute_prediction_error(task, result)
        assert error is not None
        assert "timeout" in error

# REASON: [auto] クラス TestIntegration の実装が必要だったため

class TestTriangleIdentity:
    """Triangle identity type check tests."""

# REASON: [auto] 品質保証のため
    def test_identity_holds(self):
        """Same tool_name + safety_class → identity holds."""
        t1 = Task(tool_name="hermeneus_run", safety_class=SafetyClass.REVERSIBLE)
        t2 = Task(tool_name="hermeneus_run", safety_class=SafetyClass.REVERSIBLE, parameters={"ccl": "/noe+"})
        assert triangle_identity_check(t1, t2)

# REASON: [auto] 品質保証のため
    def test_identity_fails_on_tool_name(self):
        """Different tool_name → identity fails."""
        t1 = Task(tool_name="hermeneus_run", safety_class=SafetyClass.REVERSIBLE)
        t2 = Task(tool_name="ask_with_tools", safety_class=SafetyClass.REVERSIBLE)
        assert not triangle_identity_check(t1, t2)

# REASON: [auto] 品質保証のため
    def test_identity_fails_on_safety(self):
        """Different safety_class → identity fails."""
        t1 = Task(tool_name="hermeneus_run", safety_class=SafetyClass.REVERSIBLE)
        t2 = Task(tool_name="hermeneus_run", safety_class=SafetyClass.IRREVERSIBLE)
        assert not triangle_identity_check(t1, t2)


# ━━━ 統合テスト: 3a+3b 接続 ━━━


# REASON: [auto] クラス TestIntegration の実装が必要だったため
class TestIntegration:
    """Integration tests connecting types (3a) with classifier (3b)."""

# REASON: [auto] 品質保証のため
    def test_full_lr_cycle(self):
        """Full L → Execute → R cycle with connected types and classifier."""
        # L functor: Plan → Task
        plan = Plan(
            intent="Execute /noe+ for deep analysis",
            source_label=SourceLabel.TAINT,
            depth="L3",
        )
        task = Task(
            tool_name="hermeneus_run",
            parameters={"ccl": "/noe+"},
            safety_class=classify_tool("hermeneus_run"),
            deterministic=False,
            plan_id="integration_001",
        )

        # Verify classifier connected to types
        assert task.safety_class == SafetyClass.REVERSIBLE
        assert not requires_confirmation("hermeneus_run")

        # R functor: Result → Belief
        result = ExecutionResult(
            plan_id="integration_001",
            tool_name="hermeneus_run",
            raw_output="Deep analysis output with multiple sections. " * 20,  # ~1000 chars
            exit_status="success",
        )

        label, conf = source_label_rule(task, result)
        assert label == SourceLabel.TAINT  # LLM = TAINT

        belief = ErgonBeliefUpdate(
# REASON: [auto] クラス TestErgonToChannel の実装が必要だったため
            source_label=label,
            confidence=conf,
            belief_delta="new",
            summary="Analysis revealed 3 structural patterns.",
            plan_id="integration_001",
            prediction_error=compute_prediction_error(task, result),
            next_action="→次: /fit で品質検証 (なぜ: TAINT 結果は検証が必要)",
        )

        assert belief.prediction_error is None  # No side effect mismatch
        assert belief.next_action is not None

        # Forgetting rate should be > 0 (distillation happened)
        rate = forgetting_rate(result, belief)
        assert rate > 0

# REASON: [auto] 品質保証のため
    def test_ask_with_tools_always_requires_confirmation(self):
        """ask_with_tools is IRREVERSIBLE — full pipeline check."""
        task = Task(
            tool_name="ask_with_tools",
            safety_class=classify_tool("ask_with_tools"),
            deterministic=False,
        )
        assert task.safety_class == SafetyClass.IRREVERSIBLE
        assert requires_confirmation("ask_with_tools")


# ━━━ protocols.py (3c) ━━━


# REASON: [auto] クラス TestErgonToChannel の実装が必要だったため
class TestErgonToChannel:
    """Ergon → BeliefChannelProtocol adapter tests."""

# REASON: [auto] 品質保証のため
    def test_no_error_maps_to_zero_residual(self):
        """No prediction error → residual 0.0, no iteration."""
        belief = ErgonBeliefUpdate(
            source_label=SourceLabel.SOURCE,
            confidence=Confidence.CERTAIN,
            belief_delta="confirmed",
            summary="All good.",
# REASON: [auto] クラス TestPhi7ToChannel の実装が必要だったため
        )
        ch = ergon_to_channel(belief)
        assert ch["prediction_residual"] == 0.0
        assert ch["should_iterate"] is False
        assert ch["confidence_direction"] == "stable"

# REASON: [auto] 品質保証のため
    def test_error_maps_to_full_residual(self):
        """Prediction error → residual 1.0, should iterate."""
        belief = ErgonBeliefUpdate(
            source_label=SourceLabel.TAINT,
            confidence=Confidence.ESTIMATED,
            belief_delta="refuted",
            summary="Failed.",
            prediction_error="Exit status: timeout",
        )
        ch = ergon_to_channel(belief)
        assert ch["prediction_residual"] == 1.0
        assert ch["should_iterate"] is True
        assert ch["confidence_direction"] == "declining"

# REASON: [auto] 品質保証のため
    def test_new_belief_is_improving(self):
        """New belief → confidence improving."""
        belief = ErgonBeliefUpdate(
            source_label=SourceLabel.SOURCE,
            confidence=Confidence.CERTAIN,
            belief_delta="new",
# REASON: [auto] クラス TestCompareChannels の実装が必要だったため
            summary="Learned something.",
        )
        ch = ergon_to_channel(belief)
        assert ch["confidence_direction"] == "improving"


class TestPhi7ToChannel:
    """phi7 → BeliefChannelProtocol adapter tests (using mock)."""

# REASON: [auto] 品質保証のため
    def test_phi7_mock(self):
        """Mock phi7.BeliefUpdate adapts correctly."""
        # Simulate phi7.BeliefUpdate with a simple namespace
        # REASON: [auto] クラス MockPhi7 の実装が必要だったため
        class MockPhi7:
            residual_error = 0.3
            should_loop = False
            confidence_trend = "improving"

        ch = phi7_to_channel(MockPhi7())
        assert ch["prediction_residual"] == 0.3
        assert ch["should_iterate"] is False
        assert ch["confidence_direction"] == "improving"
# REASON: [auto] 品質保証のため

    def test_phi7_loop(self):
        """phi7 with high residual → should iterate."""
        # REASON: [auto] クラス MockPhi7 の実装が必要だったため
        class MockPhi7:
            residual_error = 0.7
            should_loop = True
            confidence_trend = "declining"

        ch = phi7_to_channel(MockPhi7())
        assert ch["should_iterate"] is True
        assert ch["confidence_direction"] == "declining"


# REASON: [auto] クラス TestCompareChannels の実装が必要だったため
class TestCompareChannels:
# REASON: [auto] 品質保証のため
    """Cross-channel comparison tests."""

    def test_both_low(self):
        """Both channels OK → commit."""
        ergon = {"prediction_residual": 0.0, "should_iterate": False, "confidence_direction": "stable"}
        phi7 = {"prediction_residual": 0.2, "should_iterate": False, "confidence_direction": "improving"}
        result = compare_channels(ergon, phi7)
        assert result["uncertainty_type"] == "epistemic"
# REASON: [auto] 品質保証のため
        assert result["recommended_action"] == "commit"

    def test_one_high(self):
        """One channel iterating → iterate."""
        ergon = {"prediction_residual": 1.0, "should_iterate": True, "confidence_direction": "declining"}
        phi7 = {"prediction_residual": 0.2, "should_iterate": False, "confidence_direction": "stable"}
        result = compare_channels(ergon, phi7)
        assert result["uncertainty_type"] == "epistemic"
# REASON: [auto] 品質保証のため
        assert result["recommended_action"] == "iterate"

    def test_both_high(self):
        """Both channels high → aleatoric, accept."""
        ergon = {"prediction_residual": 0.8, "should_iterate": True, "confidence_direction": "declining"}
        phi7 = {"prediction_residual": 0.7, "should_iterate": True, "confidence_direction": "declining"}
        result = compare_channels(ergon, phi7)
        assert result["uncertainty_type"] == "aleatoric"
        assert result["recommended_action"] == "accept_uncertainty"

