# PROOF: [L2/テスト] <- mekhane/fep/tests/test_precision_dynamics.py
# PURPOSE: Proietti H₁ — Precision 座標内 γ/γ' 特殊化の回帰テスト
"""Tests for mekhane.fep.basis — PrecisionDynamics (Proietti H₁).

P₃ (axiom_hierarchy.md v4.2.2) の 5 条件を回帰テスト化:
  P1: Phase1 end: H_s_prec → 1 (habit 形成)
  P2: Context switch 後 H_s が急落 (drop > 0.1)
  P3: γ' peak ratio > 1.5x
  P4: γ'=0 → habit 固着 (drop < 0.01)
  P5: corr(H_s_prec, γ') < -0.3 (負相関)

理論的根拠:
  - Proietti, Parr, Tessari, Friston, Pezzulo (2025)
  - pei_gamma_hs_hypothesis_2026-03-15.md (ODE v2, MC 20/20)
"""

import pytest
from mekhane.fep.basis import (
    PrecisionDynamics,
    PrecisionDynamicsParams,
    DEFAULT_PRECISION_PARAMS,
    HelmholtzScore,
    precision_helmholtz_score,
    update_precision_dynamics,
    simulate_precision_trajectory,
)


# ---------------------------------------------------------------------------
# PrecisionDynamics 基本テスト
# ---------------------------------------------------------------------------

# PURPOSE: PrecisionDynamics の基本構造テスト
class TestPrecisionDynamicsBasic:
    """PrecisionDynamics の型と基本挙動。"""

    def test_dataclass_frozen(self):
        """PrecisionDynamics は immutable。"""
        pd = PrecisionDynamics(gamma=0.5, gamma_prime=0.3, surprise=0.1, h_s_precision=0.625)
        with pytest.raises(AttributeError):
            pd.gamma = 0.9  # type: ignore

    def test_precision_helmholtz_score_habit(self):
        """γ >> γ' → H_s ≈ 1 (habit)。"""
        hs = precision_helmholtz_score(gamma=0.99, gamma_prime=0.01)
        assert isinstance(hs, HelmholtzScore)
        assert hs.score == pytest.approx(0.99, abs=0.01)

    def test_precision_helmholtz_score_deliberation(self):
        """γ' > γ → H_s < 0.5 (deliberation)。"""
        hs = precision_helmholtz_score(gamma=0.3, gamma_prime=0.7)
        assert hs.score < 0.5

    def test_precision_helmholtz_score_balance(self):
        """γ = γ' → H_s = 0.5 (バランス)。"""
        hs = precision_helmholtz_score(gamma=0.5, gamma_prime=0.5)
        assert hs.score == pytest.approx(0.5)

    def test_precision_helmholtz_score_both_zero(self):
        """γ = γ' = 0 → H_s = 0.5 (デフォルト)。"""
        hs = precision_helmholtz_score(gamma=0.0, gamma_prime=0.0)
        assert hs.score == 0.5

    def test_precision_helmholtz_score_negative_raises(self):
        """負の値で ValueError。"""
        with pytest.raises(ValueError):
            precision_helmholtz_score(gamma=-0.1, gamma_prime=0.5)


# ---------------------------------------------------------------------------
# update_precision_dynamics テスト
# ---------------------------------------------------------------------------

# PURPOSE: 1ステップ更新の挙動テスト
class TestUpdatePrecisionDynamics:
    """update_precision_dynamics の挙動。"""

    def test_reward_increases_gamma(self):
        """報酬あり → γ が増加。"""
        state = PrecisionDynamics(gamma=0.5, gamma_prime=0.2, surprise=0.0, h_s_precision=0.714)
        next_state = update_precision_dynamics(state, reward=1.0, surprise=0.0)
        assert next_state.gamma > state.gamma

    def test_surprise_increases_gamma_prime(self):
        """surprise → γ' が増加。"""
        state = PrecisionDynamics(gamma=0.5, gamma_prime=0.1, surprise=0.0, h_s_precision=0.833)
        next_state = update_precision_dynamics(state, reward=0.0, surprise=0.8)
        assert next_state.gamma_prime > state.gamma_prime

    def test_gamma_prime_capped(self):
        """γ' は上限を超えない。"""
        state = PrecisionDynamics(gamma=0.5, gamma_prime=0.79, surprise=0.0, h_s_precision=0.387)
        next_state = update_precision_dynamics(state, reward=0.0, surprise=1.0)
        assert next_state.gamma_prime <= DEFAULT_PRECISION_PARAMS.gamma_prime_max

    def test_no_reward_no_surprise_decay(self):
        """報酬なし・surprise なし → 両方減衰。"""
        state = PrecisionDynamics(gamma=1.0, gamma_prime=0.5, surprise=0.0, h_s_precision=0.667)
        next_state = update_precision_dynamics(state, reward=0.0, surprise=0.0)
        assert next_state.gamma < state.gamma
        assert next_state.gamma_prime < state.gamma_prime

    def test_custom_params(self):
        """カスタムパラメータで動作。"""
        custom = PrecisionDynamicsParams(
            gamma_learning_rate=0.1,
            gamma_decay_rate=0.02,
            gamma_prime_gain=1.0,
            gamma_prime_decay=0.1,
            gamma_prime_max=1.0,
        )
        state = PrecisionDynamics(gamma=0.1, gamma_prime=0.1, surprise=0.0, h_s_precision=0.5)
        next_state = update_precision_dynamics(state, reward=1.0, surprise=0.5, params=custom)
        # γ は大きく増加 (learning_rate=0.1)
        assert next_state.gamma > 0.18
        # γ' は大きく増加 (gain=1.0)
        assert next_state.gamma_prime > 0.4


# ---------------------------------------------------------------------------
# P₃ 5 条件 — 回帰テスト
# ---------------------------------------------------------------------------

# PURPOSE: P₃ の 5 条件を回帰テスト化 (pei v2 検証済み)
class TestP3Conditions:
    """P₃ (axiom_hierarchy.md v4.2.2) の 5 条件。

    pei 実験 v2 (MC 20 seeds, 100% 支持) の結果を回帰テスト化。
    各条件の閾値は pei 報告と一致。
    """

    @pytest.fixture
    def trajectory(self):
        """決定論的な標準軌道 (seed=None)。"""
        return simulate_precision_trajectory(n_trials=300, context_switch_at=150)

    def test_p1_habit_formation(self, trajectory):
        """P1: Phase1 end で H_s → 1 (habit 形成)。

        pei v2: H_s Phase1 end = 0.9901。閾値: > 0.65。
        """
        phase1_end = trajectory[149]
        assert phase1_end.h_s_precision > 0.65, (
            f"P1 失敗: Phase1 end H_s = {phase1_end.h_s_precision:.4f} (期待 > 0.65)"
        )

    def test_p2_context_switch_drop(self, trajectory):
        """P2: Context switch 後に H_s が急落 (drop > 0.1)。

        pei v2: drop = 0.1427。閾値: > 0.1。
        """
        h_s_at_switch = trajectory[149].h_s_precision
        # Phase 2 の最小 H_s を探す (switch 後 50 trial 以内)
        phase2_min = min(s.h_s_precision for s in trajectory[150:200])
        drop = h_s_at_switch - phase2_min
        assert drop > 0.1, (
            f"P2 失敗: drop = {drop:.4f} (期待 > 0.1)"
        )

    def test_p3_gamma_prime_peak_ratio(self, trajectory):
        """P3: γ' peak ratio > 1.5x。

        pei v2: ratio = 3.97x。閾値: > 1.5x。
        """
        phase1_mean_gp = sum(s.gamma_prime for s in trajectory[:150]) / 150
        phase2_peak_gp = max(s.gamma_prime for s in trajectory[150:200])
        if phase1_mean_gp > 0:
            ratio = phase2_peak_gp / phase1_mean_gp
        else:
            ratio = float("inf")
        assert ratio > 1.5, (
            f"P3 失敗: γ' ratio = {ratio:.2f}x (期待 > 1.5x)"
        )

    def test_p4_no_metacontrol_fixation(self):
        """P4: γ'=0 → habit 固着 (Proietti Sim1 相当)。

        pei v2: drop = 0.0001 (ほぼゼロ)。閾値: drop < 0.01。
        """
        # γ' を完全に無効化するパラメータ
        no_meta = PrecisionDynamicsParams(
            gamma_prime_gain=0.0,      # surprise が γ' を駆動しない
            gamma_prime_decay=1.0,     # 既存の γ' も即座に消失
            gamma_prime_max=0.0,       # γ' の上限をゼロに
        )
        traj = simulate_precision_trajectory(
            n_trials=300, context_switch_at=150, params=no_meta
        )
        h_s_at_switch = traj[149].h_s_precision
        phase2_min = min(s.h_s_precision for s in traj[150:200])
        drop = h_s_at_switch - phase2_min
        assert drop < 0.01, (
            f"P4 失敗: γ'=0 で drop = {drop:.4f} (期待 < 0.01: 固着)"
        )

    def test_p5_negative_correlation(self, trajectory):
        """P5: corr(H_s_prec, γ') < -0.3。

        pei v2: corr = -0.845 ± 0.020。閾値: < -0.3。
        """
        h_s_values = [s.h_s_precision for s in trajectory]
        gp_values = [s.gamma_prime for s in trajectory]
        n = len(h_s_values)
        mean_h = sum(h_s_values) / n
        mean_g = sum(gp_values) / n

        # ピアソン相関
        cov = sum((h - mean_h) * (g - mean_g) for h, g in zip(h_s_values, gp_values)) / n
        std_h = (sum((h - mean_h) ** 2 for h in h_s_values) / n) ** 0.5
        std_g = (sum((g - mean_g) ** 2 for g in gp_values) / n) ** 0.5

        if std_h > 0 and std_g > 0:
            corr = cov / (std_h * std_g)
        else:
            corr = 0.0

        assert corr < -0.3, (
            f"P5 失敗: corr(H_s, γ') = {corr:.4f} (期待 < -0.3)"
        )


# ---------------------------------------------------------------------------
# simulate_precision_trajectory テスト
# ---------------------------------------------------------------------------

# PURPOSE: 軌道シミュレーションの挙動テスト
class TestSimulatePrecisionTrajectory:
    """simulate_precision_trajectory の構造テスト。"""

    def test_trajectory_length(self):
        """軌道長 = n_trials。"""
        traj = simulate_precision_trajectory(n_trials=100, context_switch_at=50)
        assert len(traj) == 100

    def test_deterministic_without_seed(self):
        """seed=None → 決定論的 (同一)。"""
        traj1 = simulate_precision_trajectory(n_trials=50, context_switch_at=25)
        traj2 = simulate_precision_trajectory(n_trials=50, context_switch_at=25)
        assert traj1[0].gamma == traj2[0].gamma
        assert traj1[-1].gamma == traj2[-1].gamma

    def test_stochastic_with_seed(self):
        """seed 指定 → 再現可能なランダム性。"""
        traj1 = simulate_precision_trajectory(n_trials=50, context_switch_at=25, seed=42)
        traj2 = simulate_precision_trajectory(n_trials=50, context_switch_at=25, seed=42)
        assert traj1[-1].gamma == pytest.approx(traj2[-1].gamma)

    def test_all_states_valid(self):
        """全状態の H_s が [0, 1] 範囲内。"""
        traj = simulate_precision_trajectory(n_trials=300)
        for s in traj:
            assert 0.0 <= s.h_s_precision <= 1.0
            assert s.gamma >= 0.0
            assert s.gamma_prime >= 0.0
