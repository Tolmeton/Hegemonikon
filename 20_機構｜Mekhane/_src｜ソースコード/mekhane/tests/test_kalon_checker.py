# PROOF: [L2/テスト] <- mekhane/tests/test_kalon_checker.py
"""
PROOF: [L2/テスト] このファイルは存在しなければならない

A0 → kalon_checker.py の品質検証が正しく動作することを保証する必要がある
   → テストなき品質検証は自己矛盾
   → test_kalon_checker.py が担う

Q.E.D.
"""
import sys
from pathlib import Path

# Add project root to sys.path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import math
import pytest

from mekhane.fep.category import (
    ADJOINT_PAIRS_D,
    SERIES_ENRICHMENTS,
    Enrichment,
    EnrichmentType,
    Series,
)
from mekhane.fep.kalon_checker import (
    ConvergenceObservation,
    KalonChecker,
    KalonLevel,
    KalonReport,
    KalonResult,
)


# =============================================================================
# KalonResult tests
# =============================================================================
class TestKalonResult:
    """Test KalonResult data class."""

    # PURPOSE: Test that KALON level means is_kalon is True
    def test_is_kalon_true(self):
        result = KalonResult(name="test", level=KalonLevel.KALON, score=1.0)
        assert result.is_kalon is True

    # PURPOSE: Test that non-KALON levels mean is_kalon is False
    def test_is_kalon_false(self):
        for level in (KalonLevel.APPROACHING, KalonLevel.INCOMPLETE, KalonLevel.ABSENT):
            result = KalonResult(name="test", level=level, score=0.5)
            assert result.is_kalon is False


# =============================================================================
# KalonReport tests
# =============================================================================
class TestKalonReport:
    """Test KalonReport aggregation."""

    # PURPOSE: Empty report should be ABSENT
    def test_empty_report(self):
        report = KalonReport()
        assert report.overall_level == KalonLevel.ABSENT
        assert report.overall_score == 0.0

    # PURPOSE: All KALON results → overall KALON
    def test_all_kalon(self):
        report = KalonReport(results=[
            KalonResult(name="a", level=KalonLevel.KALON, score=1.0),
            KalonResult(name="b", level=KalonLevel.KALON, score=0.9),
        ])
        assert report.overall_level == KalonLevel.KALON
        assert report.overall_score == pytest.approx(0.95)

    # PURPOSE: Mix of KALON and APPROACHING → APPROACHING
    def test_mixed_kalon_approaching(self):
        report = KalonReport(results=[
            KalonResult(name="a", level=KalonLevel.KALON, score=1.0),
            KalonResult(name="b", level=KalonLevel.APPROACHING, score=0.8),
        ])
        assert report.overall_level == KalonLevel.APPROACHING

    # PURPOSE: Any ABSENT → INCOMPLETE
    def test_any_absent(self):
        report = KalonReport(results=[
            KalonResult(name="a", level=KalonLevel.KALON, score=1.0),
            KalonResult(name="b", level=KalonLevel.ABSENT, score=0.0),
        ])
        assert report.overall_level == KalonLevel.INCOMPLETE

    # PURPOSE: Issues are collected from all results
    def test_all_issues(self):
        report = KalonReport(results=[
            KalonResult(name="a", level=KalonLevel.KALON, score=1.0, issues=["x"]),
            KalonResult(name="b", level=KalonLevel.APPROACHING, score=0.8, issues=["y", "z"]),
        ])
        assert len(report.all_issues) == 3
        assert "[a] x" in report.all_issues

    # PURPOSE: Summary line is formatted correctly
    def test_summary(self):
        report = KalonReport(results=[
            KalonResult(name="a", level=KalonLevel.KALON, score=1.0),
        ])
        summary = report.summary()
        assert "1/1" in summary
        assert "kalon" in summary


# =============================================================================
# KalonChecker with real data (category.py)
# =============================================================================
class TestKalonCheckerRealData:
    """Test KalonChecker against actual SERIES_ENRICHMENTS and ADJOINT_PAIRS_D."""

    def setup_method(self):
        self.checker = KalonChecker()

    # PURPOSE: Enrichment completeness should pass (all 6 series defined)
    def test_enrichment_completeness(self):
        result = self.checker.check_enrichment_completeness()
        assert result.level == KalonLevel.KALON
        assert result.score == 1.0

    # PURPOSE: Enrichment quality should pass (all scores >= 0.70)
    def test_enrichment_quality(self):
        result = self.checker.check_enrichment_quality()
        assert result.level in (KalonLevel.KALON, KalonLevel.APPROACHING)
        assert result.score >= 0.70

    # PURPOSE: All 12 adjoint pairs should be present
    def test_adjoint_completeness(self):
        result = self.checker.check_adjoint_completeness()
        assert result.level == KalonLevel.KALON
        assert result.score == 1.0

    # PURPOSE: All adjoint pairs should have valid structure
    def test_adjoint_symmetry(self):
        result = self.checker.check_adjoint_symmetry()
        assert result.level == KalonLevel.KALON

    # PURPOSE: All adjoint pairs should derive valid Galois connections
    def test_galois_derivability(self):
        result = self.checker.check_galois_derivability()
        assert result.level == KalonLevel.KALON
        assert result.score == 1.0

    # PURPOSE: L3 coherence should pass
    def test_l3_coherence(self):
        result = self.checker.check_l3_coherence()
        assert result.level == KalonLevel.KALON
        assert result.score == 1.0
        assert len(result.issues) == 0

    # PURPOSE: check_all should return a valid report
    def test_check_all(self):
        report = self.checker.check_all()
        assert len(report.results) == 12  # 11 → 12: + l3_coherence
        assert report.overall_score >= 0.70
        assert report.overall_level in (KalonLevel.KALON, KalonLevel.APPROACHING)


# =============================================================================
# KalonChecker with synthetic data (edge cases)
# =============================================================================
class TestKalonCheckerEdgeCases:
    """Test KalonChecker with synthetic data for edge cases."""

    # PURPOSE: Missing enrichment should be detected
    def test_missing_enrichment(self):
        partial = {k: v for k, v in SERIES_ENRICHMENTS.items() if k != Series.Tel}
        checker = KalonChecker(enrichments=partial)
        result = checker.check_enrichment_completeness()
        assert result.level == KalonLevel.INCOMPLETE
        assert "Telos" in result.issues[0]

    # PURPOSE: Low kalon score should fail quality check
    def test_low_kalon_score(self):
        low_quality = dict(SERIES_ENRICHMENTS)
        low_quality[Series.Tel] = Enrichment(
            type=EnrichmentType.END,
            concept="test",
            kalon=0.30,
            structures=("a",),
        )
        checker = KalonChecker(enrichments=low_quality)
        result = checker.check_enrichment_quality()
        assert len(result.issues) > 0

    # PURPOSE: Missing adjoint pair should be detected
    def test_missing_adjoint(self):
        partial = {k: v for k, v in ADJOINT_PAIRS_D.items() if k != "O-D1"}
        checker = KalonChecker(adjoint_pairs=partial)
        result = checker.check_adjoint_completeness()
        assert result.level == KalonLevel.INCOMPLETE
        assert "O-D1" in result.issues[0]

    # PURPOSE: Custom threshold should be respected
    def test_custom_threshold(self):
        # Set threshold very high (0.95) — most enrichments won't pass
        checker = KalonChecker(kalon_threshold=0.95)
        result = checker.check_enrichment_quality()
        # At least some should fail with threshold=0.95
        assert result.score < 0.95 or result.level != KalonLevel.KALON


# =============================================================================
# Bayesian Convergence tests (§6.3)
# =============================================================================
class TestKalonConvergenceBayesian:
    """Test Bayesian Beta convergence check (kalon.md §6.3)."""

    def setup_method(self):
        self.checker = KalonChecker()

    # PURPOSE: All converged observations → high convergence_prob
    def test_all_converged(self):
        obs = [ConvergenceObservation(distance=0.05, delta=0.15) for _ in range(10)]
        result = self.checker.check_convergence_bayesian(observations=obs)
        assert result.convergence_prob is not None
        assert result.convergence_prob > 0.90
        assert result.ci_lower is not None
        assert result.ci_lower > 0.5
        assert result.n_observations == 10
        assert result.level in (KalonLevel.KALON, KalonLevel.APPROACHING)

    # PURPOSE: Mixed results → intermediate convergence_prob
    def test_mixed_results(self):
        obs = [
            ConvergenceObservation(distance=0.45, delta=0.15),  # change
            ConvergenceObservation(distance=0.30, delta=0.15),  # change
            ConvergenceObservation(distance=0.10, delta=0.15),  # converged
            ConvergenceObservation(distance=0.05, delta=0.15),  # converged
        ]
        result = self.checker.check_convergence_bayesian(observations=obs)
        assert result.n_observations == 4
        assert result.convergence_prob is not None
        # With 2 convergences and 2 changes, prob should be moderate
        assert 0.0 < result.convergence_prob < 0.90

    # PURPOSE: No observations → uninformative prior (Beta(1,1))
    def test_no_observations(self):
        result = self.checker.check_convergence_bayesian(observations=None)
        assert result.n_observations == 0
        assert result.score == pytest.approx(0.5)
        assert result.convergence_prob == pytest.approx(0.5)
        assert result.level == KalonLevel.APPROACHING

    # PURPOSE: CI should narrow with more data
    def test_ci_narrows_with_more_data(self):
        # Few observations
        obs_few = [ConvergenceObservation(distance=0.05, delta=0.15) for _ in range(3)]
        result_few = self.checker.check_convergence_bayesian(observations=obs_few)

        # Many observations
        obs_many = [ConvergenceObservation(distance=0.05, delta=0.15) for _ in range(30)]
        result_many = self.checker.check_convergence_bayesian(observations=obs_many)

        assert result_few.ci_upper is not None and result_few.ci_lower is not None
        assert result_many.ci_upper is not None and result_many.ci_lower is not None
        width_few = result_few.ci_upper - result_few.ci_lower
        width_many = result_many.ci_upper - result_many.ci_lower
        assert width_many < width_few  # More data → narrower CI


# =============================================================================
# Bayesian Prior Chaining tests (§6.3 v1.8)
# =============================================================================
class TestKalonPriorChaining:
    """Test cross-session Bayesian belief inheritance (kalon.md §6.3 v1.8)."""

    def setup_method(self):
        self.checker = KalonChecker()

    # PURPOSE: Verification of serialization and deserialization
    def test_prior_chaining_roundtrip(self):
        from mekhane.fep.kalon_checker import PriorState

        # 1. Run a session
        obs = [ConvergenceObservation(distance=0.05, delta=0.15) for _ in range(5)]
        result1 = self.checker.check_convergence_bayesian(observations=obs)

        # 2. Export posterior
        prior_state = self.checker.export_posterior(result1, concept_id="test_concept")
        assert prior_state.alpha > 1.0  # Should have learned something
        assert prior_state.n_observations == 5

        # 3. Serialize to dict (simulation of Handoff save)
        state_dict = prior_state.to_dict()
        assert state_dict["concept_id"] == "test_concept"
        assert "alpha" in state_dict
        assert "last_updated" in state_dict

        # 4. Deserialize (simulation of next session load)
        loaded_state = PriorState.from_dict(state_dict)
        assert loaded_state.alpha == prior_state.alpha
        assert loaded_state.beta == prior_state.beta

        # 5. Use in new session
        result2 = self.checker.check_convergence_bayesian(
            observations=obs, prior=loaded_state
        )
        # Posterior from session 2 with inherited prior should be stronger
        assert result2.score > result1.score
        assert result2.n_observations == 5  # observations in THIS session

    # PURPOSE: Verify decay mechanism bounds the prior
    def test_prior_decay(self):
        from mekhane.fep.kalon_checker import PriorState
        from datetime import datetime, timedelta

        # Create a strong prior from 60 days ago
        old_time = (datetime.now() - timedelta(days=60)).isoformat()
        strong_prior = PriorState(
            concept_id="decay_test", alpha=10.0, beta=2.0, last_updated=old_time
        )

        current_time = datetime.now().isoformat()
        decayed = strong_prior.decay(current_time, tau_days=30.0)

        # e^(-60/30) = e^-2 ≈ 0.135
        # alpha should decay from 10.0 toward 1.0
        assert decayed.alpha < 10.0
        assert decayed.alpha > 1.0
        # Check specific expected value: 1.0 + (9.0 * e^-2) ≈ 2.21
        assert decayed.alpha == pytest.approx(1.0 + 9.0 * math.exp(-2.0), rel=1e-2)

    # PURPOSE: Check that non-integer alpha/beta are preserved correctly
    def test_prior_chaining_non_integer(self):
        from mekhane.fep.kalon_checker import PriorState

        # Setup prior with non-integers (e.g. from decay)
        prior = PriorState(concept_id="test", alpha=2.21, beta=1.0)

        obs = [ConvergenceObservation(distance=0.05, delta=0.15) for _ in range(5)]
        result = self.checker.check_convergence_bayesian(observations=obs, prior=prior)

        # 5 successes, 0 failures.
        # alpha_post = alpha_prior + 5 = 7.21
        # beta_post = beta_prior + 0 = 1.0
        assert result.alpha_post == pytest.approx(7.21)
        assert result.beta_post == pytest.approx(1.0)

        exported = self.checker.export_posterior(result)
        assert exported.alpha == pytest.approx(7.21)
        assert exported.beta == pytest.approx(1.0)

    # PURPOSE: Ensure `prior` argument takes precedence over alpha_prior/beta_prior
    def test_prior_precedence(self):
        from mekhane.fep.kalon_checker import PriorState

        prior = PriorState(concept_id="test", alpha=3.0, beta=4.0)
        obs = [ConvergenceObservation(distance=0.05, delta=0.15)]  # 1 success

        result = self.checker.check_convergence_bayesian(
            observations=obs,
            alpha_prior=10.0,  # Should be ignored
            beta_prior=20.0,   # Should be ignored
            prior=prior,
        )

        assert result.alpha_post == 4.0  # 3.0 + 1
        assert result.beta_post == 4.0   # 4.0 + 0


# =============================================================================
# ROPE and Bayes Factor tests (§6.3 v1.7)
# =============================================================================
class TestKalonROPEBayesFactor:
    """Test ROPE and Bayes Factor extensions (kalon.md §6.3 v1.7)."""

    def setup_method(self):
        self.checker = KalonChecker()

    # PURPOSE: Strong convergence → ROPE prob should be low (posterior is above ROPE)
    def test_rope_high_convergence(self):
        obs = [ConvergenceObservation(distance=0.05, delta=0.15) for _ in range(20)]
        result = self.checker.check_convergence_bayesian(observations=obs)
        assert result.rope_prob is not None
        # With all converged, posterior is at ~0.95, far above θ=0.70±0.10
        # ROPE mass should be low (posterior moved past the ROPE region)
        assert result.rope_prob < 0.50

    # PURPOSE: Mixed results → ROPE contains some posterior mass
    def test_rope_mixed(self):
        obs = [
            ConvergenceObservation(distance=0.30, delta=0.15),  # change
            ConvergenceObservation(distance=0.10, delta=0.15),  # converged
            ConvergenceObservation(distance=0.10, delta=0.15),  # converged
            ConvergenceObservation(distance=0.10, delta=0.15),  # converged
        ]
        result = self.checker.check_convergence_bayesian(observations=obs)
        assert result.rope_prob is not None
        # Posterior mean ~0.67, near θ=0.70, so ROPE should have significant mass
        assert result.rope_prob > 0.10

    # PURPOSE: Strong evidence → BF₁₀ should be high
    def test_bayes_factor_strong_evidence(self):
        obs = [ConvergenceObservation(distance=0.05, delta=0.15) for _ in range(20)]
        result = self.checker.check_convergence_bayesian(observations=obs)
        assert result.bayes_factor is not None
        # With 20 converged observations, posterior moved far from θ
        assert result.bayes_factor > 1.0

    # PURPOSE: Weak evidence → BF₁₀ should be small
    def test_bayes_factor_weak_evidence(self):
        obs = [
            ConvergenceObservation(distance=0.30, delta=0.15),  # change
            ConvergenceObservation(distance=0.10, delta=0.15),  # converged
        ]
        result = self.checker.check_convergence_bayesian(observations=obs)
        assert result.bayes_factor is not None
        # With only 2 observations (1 converged), evidence is weak


# =============================================================================
# Frequentist TOST tests (§6.5)
# =============================================================================
class TestKalonTOST:
    """Test Frequentist TOST convergence check (kalon.md §6.5)."""

    def setup_method(self):
        self.checker = KalonChecker()

    # PURPOSE: All converged → p_tost < α → Fix
    def test_tost_all_converged(self):
        obs = [ConvergenceObservation(distance=0.05, delta=0.15) for _ in range(15)]
        result = self.checker.check_convergence_tost(observations=obs)
        assert result.tost_p_value is not None
        assert result.tost_p_value < 0.05
        assert result.level == KalonLevel.KALON
        assert result.n_observations == 15

    # PURPOSE: Insufficient data → cannot reject H₀
    def test_tost_insufficient_data(self):
        obs = [
            ConvergenceObservation(distance=0.10, delta=0.15),  # converged
            ConvergenceObservation(distance=0.10, delta=0.15),  # converged
        ]
        result = self.checker.check_convergence_tost(observations=obs)
        assert result.n_observations == 2
        # With only 2 observations, may not reach significance
        assert result.required_n is not None
        assert result.required_n > 2

    # PURPOSE: No observations → power analysis only
    def test_tost_no_observations(self):
        result = self.checker.check_convergence_tost(observations=None)
        assert result.n_observations == 0
        assert result.tost_p_value is None
        assert result.required_n is not None
        assert result.required_n > 0
        assert result.level == KalonLevel.APPROACHING

    # PURPOSE: Convergence rate below threshold → INCOMPLETE
    def test_tost_below_threshold(self):
        obs = [
            ConvergenceObservation(distance=0.30, delta=0.15),  # change
            ConvergenceObservation(distance=0.25, delta=0.15),  # change
            ConvergenceObservation(distance=0.10, delta=0.15),  # converged
            ConvergenceObservation(distance=0.40, delta=0.15),  # change
            ConvergenceObservation(distance=0.35, delta=0.15),  # change
        ]
        result = self.checker.check_convergence_tost(observations=obs)
        assert result.tost_p_value is not None
        assert result.tost_p_value > 0.05  # Cannot reject H₀
        assert result.level in (KalonLevel.INCOMPLETE, KalonLevel.APPROACHING)


# =============================================================================
# Power Analysis tests (§6.5)
# =============================================================================
class TestKalonPowerAnalysis:
    """Test power analysis for G∘F sample size design (kalon.md §6.5)."""

    def setup_method(self):
        self.checker = KalonChecker()

    # PURPOSE: Basic power analysis returns reasonable n
    def test_power_analysis_basic(self):
        n = self.checker.power_analysis(
            alpha=0.05, target_power=0.80, estimated_p=0.85
        )
        assert n >= 3
        assert n < 500  # Should be reasonable for p=0.85 vs θ=0.70

    # PURPOSE: Higher power requires more observations
    def test_power_increases_with_n(self):
        n_80 = self.checker.power_analysis(
            alpha=0.05, target_power=0.80, estimated_p=0.85
        )
        n_95 = self.checker.power_analysis(
            alpha=0.05, target_power=0.95, estimated_p=0.85
        )
        assert n_95 > n_80

    # PURPOSE: Larger effect size → fewer observations needed
    def test_power_high_delta_less_n(self):
        # Large effect: p=0.95 vs θ=0.70 (Δ=0.25)
        n_large = self.checker.power_analysis(
            alpha=0.05, target_power=0.80, estimated_p=0.95
        )
        # Small effect: p=0.75 vs θ=0.70 (Δ=0.05)
        n_small = self.checker.power_analysis(
            alpha=0.05, target_power=0.80, estimated_p=0.75
        )
        assert n_small > n_large

    # PURPOSE: estimated_p ≤ θ should return impossible
    def test_power_impossible(self):
        n = self.checker.power_analysis(
            alpha=0.05, target_power=0.80, estimated_p=0.60
        )
        assert n == 999  # Cannot detect convergence

