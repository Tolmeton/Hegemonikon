# PROOF: KalonDetector unit tests
# PURPOSE: Verify Good-Turing statistics and saturation detection logic

import pytest

from mekhane.periskope.kalon_detector import KalonDetector, SaturationState


class TestSaturationState:
    """Test Good-Turing statistics calculations."""

    def test_empty_state(self):
        s = SaturationState()
        assert s.n == 0
        assert s.s_obs == 0
        assert s.f1 == 0
        assert s.f2 == 0
        assert s.p_new == 1.0  # Everything is new
        assert s.coverage == 0.0
        assert s.completeness == 1.0  # Vacuously complete

    def test_all_singletons(self):
        s = SaturationState()
        s.citation_counts = {"a": 1, "b": 1, "c": 1, "d": 1, "e": 1}
        assert s.n == 5
        assert s.s_obs == 5
        assert s.f1 == 5
        assert s.f2 == 0
        assert s.p_new == 1.0  # All singletons → high P(new)
        assert s.coverage == 0.0

    def test_mixed_frequencies(self):
        s = SaturationState()
        # 10 citations: 2 singletons, 3 doubletons, 1 tripleton
        s.citation_counts = {
            "a": 1, "b": 1,  # singletons
            "c": 2, "d": 2, "e": 2,  # doubletons
            "f": 3,  # tripleton
        }
        assert s.n == 1 + 1 + 2 + 2 + 2 + 3  # = 11
        assert s.s_obs == 6
        assert s.f1 == 2
        assert s.f2 == 3
        assert abs(s.p_new - 2 / 11) < 1e-10
        assert abs(s.coverage - (1 - 2 / 11)) < 1e-10
        # Chao1 = 6 + 4/6 ≈ 6.667
        assert abs(s.chao1 - (6 + 4 / 6)) < 1e-10

    def test_no_singletons_saturated(self):
        s = SaturationState()
        # All citations seen multiple times
        s.citation_counts = {"a": 5, "b": 3, "c": 4}
        assert s.f1 == 0
        assert s.p_new == 0.0
        assert s.coverage == 1.0  # Fully saturated

    def test_chao1_no_doubletons(self):
        """Bias-corrected Chao1 when f2 = 0."""
        s = SaturationState()
        s.citation_counts = {"a": 1, "b": 1, "c": 1, "d": 3}
        assert s.f1 == 3
        assert s.f2 == 0
        # Chao1 = 4 + 3*(3-1)/2 = 4 + 3 = 7
        assert abs(s.chao1 - 7.0) < 1e-10

    def test_information_gain_insufficient_data(self):
        s = SaturationState()
        s.discovery_series = [10]
        assert s.information_gain(last_n=3) == 1.0  # Not enough data

    def test_information_gain_normal(self):
        s = SaturationState()
        s.citation_counts = {"a": 1}  # n = 1
        s.discovery_series = [10, 5, 2, 1, 0]
        # last 3: [2, 1, 0] = 3, n = 1
        assert s.information_gain(last_n=3) == 3.0


class TestKalonDetector:
    """Test saturation detection logic."""

    def test_not_saturated_early(self):
        kd = KalonDetector(level="L2")
        urls = [f"url_{i}" for i in range(20)]
        kd.update(0, "query1", urls, urls)
        is_fix, m = kd.is_kalon()
        assert not is_fix
        assert m["p_new"] == 1.0  # All singletons
        # v1.7 bridge keys present
        assert "bayesian_prob" in m
        assert "tost_p_value" in m

    def test_saturated_all_seen(self):
        kd = KalonDetector(level="L1")
        # Simulate many iterations with same URLs
        urls = ["url_a", "url_b", "url_c"]
        for i in range(10):
            kd.update(i, f"q{i}", [], urls)
        is_fix, m = kd.is_kalon()
        assert m["p_new"] == 0.0
        assert m["result_saturated"]

    def test_level_affects_threshold(self):
        kd1 = KalonDetector(level="L1")
        kd3 = KalonDetector(level="L3")
        assert kd1.P_NEW_THRESHOLD["L1"] > kd3.P_NEW_THRESHOLD["L3"]

    def test_report_output(self):
        kd = KalonDetector(level="L2")
        urls = ["a", "b"]
        kd.update(0, "q", urls, urls)
        report = kd.report()
        assert "Kalon Status:" in report
        assert "P(new)" in report
        assert "Coverage" in report
        assert "Chao1" in report
        # v1.7 bridge metrics in report
        assert "[v1.7 Bayesian]" in report
        assert "[v1.7 TOST]" in report

    def test_update_tracks_queries(self):
        kd = KalonDetector(level="L2")
        kd.update(0, "q1", ["a"], ["a", "b"])
        kd.update(1, "q2", ["c"], ["a", "c"])
        assert "q1" in kd.state.query_discoveries
        assert "q2" in kd.state.query_discoveries
        assert kd.state.citation_counts["a"] == 2

    def test_v17_bayesian_metrics_converged(self):
        """v1.7 bridge: fully saturated state should produce strong Bayesian evidence."""
        kd = KalonDetector(level="L1")
        urls = ["url_a", "url_b", "url_c"]
        for i in range(10):
            kd.update(i, f"q{i}", [], urls)
        _, m = kd.is_kalon()
        # All 10 iterations had 0 new discoveries → all converged
        assert m["bayesian_prob"] is not None
        assert m["bayesian_prob"] > 0.90  # Strong convergence evidence
        assert m["bayesian_bf10"] is not None
        assert m["bayesian_bf10"] > 1.0  # Evidence against H₀
        assert m["tost_p_value"] is not None


class TestGFConvergence:
    """G∘F 収束ロジックのテスト (C1-C5)。"""

    # --- SaturationState の gf_* プロパティ ---

    def test_gf_current_empty(self):
        """gf_series が空のとき gf_current = 0.0。"""
        s = SaturationState()
        assert s.gf_current == 0.0

    def test_gf_current_returns_last(self):
        """gf_current は gf_series の最新値を返す。"""
        s = SaturationState()
        s.gf_series = [0.5, 0.3, 0.1]
        assert s.gf_current == 0.1

    def test_gf_convergence_insufficient_data(self):
        """データ不足時は gf_convergence = 1.0 (未収束)。"""
        s = SaturationState()
        assert s.gf_convergence == 1.0
        s.gf_series = [0.5]
        assert s.gf_convergence == 1.0

    def test_gf_convergence_calculation(self):
        """gf_convergence は直近2値の絶対差。"""
        s = SaturationState()
        s.gf_series = [0.5, 0.3]
        assert abs(s.gf_convergence - 0.2) < 1e-10

    def test_gf_convergence_near_zero(self):
        """ほぼ同一の連続値で収束判定 (< 0.05)。"""
        s = SaturationState()
        s.gf_series = [0.12, 0.13]
        assert s.gf_convergence < 0.05

    # --- KalonDetector.update_gf ---

    def test_update_gf_records_value(self):
        """update_gf がG∘F値を gf_series に追加する。"""
        kd = KalonDetector(level="L2")
        kd.update_gf(drift=0.8, redundancy=0.2)
        # G∘F = 0.8 × (1 - 0.2) = 0.64
        assert len(kd.state.gf_series) == 1
        assert abs(kd.state.gf_series[0] - 0.64) < 1e-10

    def test_update_gf_multiple_calls(self):
        """update_gf の複数呼び出しで履歴が蓄積される。"""
        kd = KalonDetector(level="L2")
        kd.update_gf(drift=1.0, redundancy=0.0)  # G∘F = 1.0
        kd.update_gf(drift=0.5, redundancy=0.5)  # G∘F = 0.25
        kd.update_gf(drift=0.3, redundancy=0.1)  # G∘F = 0.27
        assert len(kd.state.gf_series) == 3
        assert abs(kd.state.gf_series[0] - 1.0) < 1e-10
        assert abs(kd.state.gf_series[1] - 0.25) < 1e-10
        assert abs(kd.state.gf_series[2] - 0.27) < 1e-10

    def test_update_gf_defaults_zero(self):
        """デフォルト引数 (drift=0, redundancy=0) で G∘F = 0。"""
        kd = KalonDetector(level="L2")
        kd.update_gf()
        assert kd.state.gf_series[0] == 0.0

    def test_update_gf_full_redundancy(self):
        """redundancy=1.0 のとき G∘F = 0 (完全冗長)。"""
        kd = KalonDetector(level="L2")
        kd.update_gf(drift=0.9, redundancy=1.0)
        assert kd.state.gf_series[0] == 0.0

    # --- is_kalon 多数決判定 ---

    def test_is_kalon_majority_all_true(self):
        """3条件全て成立 → kalon=True。"""
        kd = KalonDetector(level="L1")
        # result_saturated: p_new=0 (全て複数回出現)
        urls = ["a", "b", "c"]
        for i in range(10):
            kd.update(i, f"q{i}", [], urls)
        # query_saturated: info_gain ≈ 0
        # gf_converged: 近い値を2回
        kd.update_gf(drift=0.1, redundancy=0.1)
        kd.update_gf(drift=0.1, redundancy=0.1)
        is_fix, m = kd.is_kalon()
        assert is_fix
        assert m["result_saturated"]
        assert m["gf_converged"]

    def test_is_kalon_majority_two_of_three(self):
        """2条件成立 → kalon=True (多数決)。"""
        kd = KalonDetector(level="L2")
        # result_saturated: p_new=0
        urls = ["a", "b"]
        for i in range(10):
            kd.update(i, f"q{i}", [], urls)
        # gf_converged: 同じ値で収束
        kd.update_gf(drift=0.05, redundancy=0.0)
        kd.update_gf(drift=0.05, redundancy=0.0)
        is_fix, m = kd.is_kalon()
        # result_saturated=True, gf_converged=True → 2/3 → kalon
        assert is_fix

    def test_is_kalon_majority_one_of_three(self):
        """1条件のみ成立 → kalon=False。"""
        kd = KalonDetector(level="L2")
        # 全 singleton → p_new=1.0 → result_saturated=False
        urls = [f"url_{i}" for i in range(20)]
        kd.update(0, "q1", urls, urls)
        # gf: divergent → gf_converged=False
        kd.update_gf(drift=0.9, redundancy=0.1)
        kd.update_gf(drift=0.2, redundancy=0.5)  # 差分大きい
        is_fix, m = kd.is_kalon()
        assert not is_fix

    def test_is_kalon_metrics_include_gf(self):
        """is_kalon の metrics に G∘F 関連キーが含まれる。"""
        kd = KalonDetector(level="L2")
        kd.update(0, "q", ["a"], ["a"])
        kd.update_gf(drift=0.5, redundancy=0.2)
        _, m = kd.is_kalon()
        assert "gf_current" in m
        assert "gf_convergence" in m
        assert "gf_converged" in m

    # --- report に G∘F メトリクスが含まれる ---

    def test_report_includes_gf_metrics(self):
        """report() に G∘F current と G∘F convergence が表示される。"""
        kd = KalonDetector(level="L2")
        kd.update(0, "q", ["a"], ["a"])
        kd.update_gf(drift=0.5, redundancy=0.3)
        report = kd.report()
        assert "G∘F current" in report
        assert "G∘F convergence" in report
