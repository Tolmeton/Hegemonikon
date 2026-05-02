from __future__ import annotations
# PROOF: KalonDetector — Good-Turing based saturation detector for Periskopē
# PURPOSE: Statistically determine when the search space is saturated (Fix(G∘F))
#          using citation frequency patterns. Complements existing info_gain stopping.
#
# Design: kalon_saturation_detector.md (§2 Statistics, §7 Implementation)
# Theory: Good-Turing (1953), Chao1 (Chao et al. 2017), Koukos & Glykos (2013)
# v1.7: Bayesian ROPE + BF₁₀ and Frequentist TOST bridge via kalon_checker


import math
from dataclasses import dataclass, field
from typing import Optional, Sequence


@dataclass
class SaturationState:
    """Good-Turing based saturation tracking.

    Tracks citation URL frequencies across search iterations to estimate
    how much of the search space remains undiscovered.
    """

    # Citation occurrence counts: {citation_url: count}
    citation_counts: dict[str, int] = field(default_factory=dict)

    # New results per iteration
    discovery_series: list[int] = field(default_factory=list)

    # Discoveries per query
    query_discoveries: dict[str, list[int]] = field(default_factory=dict)

    # G∘F 収束履歴: F=drift (探索), G=1-redundancy (統合)
    gf_series: list[float] = field(default_factory=list)

    @property
    def n(self) -> int:
        """Total observations."""
        return sum(self.citation_counts.values())

    @property
    def s_obs(self) -> int:
        """Observed species count (unique citations)."""
        return len(self.citation_counts)

    @property
    def f1(self) -> int:
        """Singleton count (citations seen exactly once)."""
        return sum(1 for c in self.citation_counts.values() if c == 1)

    @property
    def f2(self) -> int:
        """Doubleton count (citations seen exactly twice)."""
        return sum(1 for c in self.citation_counts.values() if c == 2)

    @property
    def p_new(self) -> float:
        """Good-Turing: probability of finding an unseen citation next."""
        if self.n == 0:
            return 1.0
        return self.f1 / self.n

    @property
    def coverage(self) -> float:
        """Good-Turing Coverage: 1 - P(new)."""
        return 1.0 - self.p_new

    @property
    def chao1(self) -> float:
        """Chao1 estimate: total number of relevant results."""
        if self.f2 == 0:
            # Bias-corrected form when no doubletons
            return self.s_obs + self.f1 * (self.f1 - 1) / 2
        return self.s_obs + self.f1 ** 2 / (2 * self.f2)

    @property
    def chao1_var(self) -> float:
        """Variance of the Chao1 estimate."""
        f1 = self.f1
        f2 = self.f2
        if f2 > 0:
            return f2 * (0.25 * (f1/f2)**4 + (f1/f2)**3 + 0.5 * (f1/f2)**2)
        else:
            return max(0.0, 0.25 * f1**4 + f1**3 + 0.5 * f1**2)

    def _calculate_ci(self) -> tuple[float, float]:
        """Calculate the 95% asymmetric confidence interval for Chao1 (Chao 1987)."""
        s_obs = self.s_obs
        est = self.chao1
        var = self.chao1_var

        if est == s_obs:
            return s_obs, s_obs

        # T = est - s_obs; var(T) = var(est)
        diff = est - s_obs
        if diff <= 0:
            return s_obs, s_obs
        
        # Calculate C factor
        try:
            c = math.exp(1.96 * math.sqrt(math.log(1 + var / (diff ** 2))))
        except (ValueError, ZeroDivisionError):
            c = 1.0

        lo_ci = s_obs + diff / c
        hi_ci = s_obs + diff * c
        return lo_ci, hi_ci

    @property
    def chao1_lo_ci(self) -> float:
        """95% Confidence Interval Lower Bound for Chao1."""
        return self._calculate_ci()[0]

    @property
    def chao1_hi_ci(self) -> float:
        """95% Confidence Interval Upper Bound for Chao1."""
        return self._calculate_ci()[1]

    @property
    def completeness(self) -> float:
        """Estimated completeness: observed / estimated total."""
        est = self.chao1
        if est == 0:
            return 1.0
        return min(1.0, self.s_obs / est)

    @property
    def gf_current(self) -> float:
        """最新の G∘F 値。G∘F = drift × (1 - redundancy)。"""
        if not self.gf_series:
            return 0.0
        return self.gf_series[-1]

    @property
    def gf_convergence(self) -> float:
        """G∘F 収束度: 直近2回の差分。0 に近いほど不動点。

        Kalon(x) ⟺ x = Fix(G∘F) の操作化。
        F = drift (既存→新規の意味的距離, Explore)
        G = 1 - redundancy (新結果群の内部多様性, Exploit)
        """
        if len(self.gf_series) < 2:
            return 1.0  # データ不十分 → 未収束
        return abs(self.gf_series[-1] - self.gf_series[-2])

    def information_gain(self, last_n: int = 3) -> float:
        """Information gain from the last N iterations."""
        if len(self.discovery_series) < last_n:
            return 1.0
        recent = self.discovery_series[-last_n:]  # pyre-ignore[16]
        return sum(recent) / max(1, self.n)


# PURPOSE: Compute adaptive token budget based on Kalon saturation state
def compute_data_budget(
    state: SaturationState,
    base_chars: int = 150_000,
    floor_ratio: float = 0.40,
) -> int:
    """Kalon-driven adaptive token budget for synthesis prompts.

    Uses the Good-Turing P(new) to decide how much search result text
    to inject into synthesis prompts.  When P(new) is high (early phase,
    many unseen citations), the full budget is used.  As saturation
    approaches (P(new) → 0), the budget shrinks towards floor_ratio.

    Args:
        state: Current SaturationState from KalonDetector.
        base_chars: Maximum character budget (default: 150_000 ≈ 100K tokens).
        floor_ratio: Minimum ratio of base_chars to keep (default: 0.40 = 60% max compression).

    Returns:
        Character budget (int).  Always >= base_chars * floor_ratio.

    Design:
        budget = base_chars × (floor + (1 - floor) × P(new))

        P(new) = 1.0 → budget = base_chars        (no compression)
        P(new) = 0.5 → budget = base_chars × 0.70  (30% compression)
        P(new) = 0.0 → budget = base_chars × 0.40  (60% compression)
    """
    p_new = state.p_new  # 0.0–1.0
    ratio = floor_ratio + (1.0 - floor_ratio) * p_new
    return max(int(base_chars * floor_ratio), int(base_chars * ratio))


# PURPOSE: Detect Fix(G∘F) via Good-Turing statistics on citation frequencies
class KalonDetector:
    """Detect search space saturation using Good-Turing statistics.

    Complements the existing info_gain based stopping in engine.py
    by tracking citation URL frequency patterns — an orthogonal signal.
    """

    # CCL modifier → α (significance level)
    ALPHA = {
        "L1": 0.20,   # + (quick)
        "L2": 0.05,   # standard
        "L3": 0.02,   # - (thorough)
    }

    # P(new) threshold per level
    P_NEW_THRESHOLD = {
        "L1": 0.05,
        "L2": 0.01,
        "L3": 0.001,
    }

    def __init__(self, level: str = "L2"):
        self.level = level
        self.state = SaturationState()

    def update(
        self,
        iteration: int,
        query: str,
        new_citation_urls: list[str],
        all_citation_urls: list[str],
    ) -> None:
        """Update state with results from one search iteration."""
        for url in all_citation_urls:
            self.state.citation_counts[url] = (
                self.state.citation_counts.get(url, 0) + 1
            )
        self.state.discovery_series.append(len(new_citation_urls))

        if query not in self.state.query_discoveries:
            self.state.query_discoveries[query] = []
        self.state.query_discoveries[query].append(len(new_citation_urls))

    def update_gf(self, *, drift: float = 0.0, redundancy: float = 0.0) -> None:
        """G∘F 収束値を記録する。density 計算後に呼ぶこと。

        Args:
            drift: 新結果の既存結果からの意味的距離 (F=Explore)。
            redundancy: 新結果群の内部冗長性。G=1-redundancy (Exploit)。
        """
        # G∘F = drift × (1 - redundancy)
        # F=drift (遠くに行く力), G=1-redundancy (独立情報を持ち帰る力)
        gf_value = drift * (1.0 - redundancy)
        self.state.gf_series.append(gf_value)

    def _build_convergence_observations(self) -> list:
        """Convert discovery_series to ConvergenceObservation objects.

        Each iteration with 0 new discoveries is treated as "converged".
        Uses distance=new_count, delta=1.0 so converged iff new_count < 1.
        """
        from mekhane.fep.kalon_checker import ConvergenceObservation

        return [
            ConvergenceObservation(
                distance=float(new_count),
                delta=1.0,
            )
            for new_count in self.state.discovery_series
        ]

    def is_kalon(self) -> tuple[bool, dict]:
        """Check if Fix(G∘F) has been reached.

        Combines Good-Turing frequency statistics with v1.7 Bayesian/Frequentist
        convergence checks from kalon_checker.

        Returns:
            (is_saturated, metrics_dict)
        """
        p_new = self.state.p_new
        threshold = self.P_NEW_THRESHOLD[self.level]
        alpha = self.ALPHA[self.level]

        # Condition 1: Result space saturation (Good-Turing)
        result_saturated = p_new < threshold

        # Condition 2: Query space saturation (recent IG is tiny)
        ig = self.state.information_gain(last_n=3)
        query_saturated = ig < threshold

        # Condition 3: G∘F 収束 (意味的不動点)
        gf_conv = self.state.gf_convergence
        gf_converged = gf_conv < 0.05  # ε = 0.05

        # Kalon = 3条件中2つ以上が成立 (多数決)
        conditions = [result_saturated, query_saturated, gf_converged]
        is_fix = sum(conditions) >= 2

        metrics: dict = {
            "kalon": is_fix,
            "p_new": p_new,
            "coverage": self.state.coverage,
            "chao1_estimate": self.state.chao1,
            "chao1_lo_ci": self.state.chao1_lo_ci,
            "chao1_hi_ci": self.state.chao1_hi_ci,
            "completeness": self.state.completeness,
            "information_gain": ig,
            "result_saturated": result_saturated,
            "query_saturated": query_saturated,
            "gf_current": self.state.gf_current,
            "gf_convergence": gf_conv,
            "gf_converged": gf_converged,
            "level": self.level,
            "alpha": alpha,
            "threshold": threshold,
            "s_obs": self.state.s_obs,
            "f1": self.state.f1,
            "f2": self.state.f2,
            "n": self.state.n,
        }

        # v1.7 Bridge: Bayesian + Frequentist convergence checks
        observations = self._build_convergence_observations()
        if observations:
            from mekhane.fep.kalon_checker import KalonChecker

            checker = KalonChecker(kalon_threshold=0.70)
            bayesian = checker.check_convergence_bayesian(observations=observations)
            tost = checker.check_convergence_tost(observations=observations)

            metrics["bayesian_prob"] = bayesian.convergence_prob
            metrics["bayesian_rope"] = bayesian.rope_prob
            metrics["bayesian_bf10"] = bayesian.bayes_factor
            metrics["bayesian_level"] = bayesian.level.value
            metrics["tost_p_value"] = tost.tost_p_value
            metrics["tost_level"] = tost.level.value
        else:
            metrics["bayesian_prob"] = None
            metrics["bayesian_rope"] = None
            metrics["bayesian_bf10"] = None
            metrics["bayesian_level"] = None
            metrics["tost_p_value"] = None
            metrics["tost_level"] = None

        return is_fix, metrics

    def report(self) -> str:
        """Generate a saturation status report."""
        is_fix, m = self.is_kalon()
        status = "◎ Kalon (Fix到達)" if is_fix else "◯ 未到達 (G∘F 継続)"
        lines = [
            f"Kalon Status: {status}",
            f"  P(new) = {m['p_new']:.4f} (threshold: {m['threshold']})",
            f"  Coverage = {m['coverage']:.4f}",
            f"  Chao1 = {m['chao1_estimate']:.1f} (95% CI: [{m['chao1_lo_ci']:.1f}, {m['chao1_hi_ci']:.1f}], observed: {m['s_obs']})",
            f"  Completeness = {m['completeness']:.2%}",
            f"  Info Gain = {m['information_gain']:.4f}",
            f"  G∘F current = {m['gf_current']:.4f}",
            f"  G∘F convergence = {m['gf_convergence']:.4f} (ε=0.05, {'converged' if m['gf_converged'] else 'not converged'})",
            f"  Level: {m['level']} (α={m['alpha']})",
        ]

        # v1.7 Bayesian + Frequentist metrics
        if m.get("bayesian_prob") is not None:
            lines.append(
                f"  [v1.7 Bayesian] P(K>θ)={m['bayesian_prob']:.3f}"
                f", ROPE={m['bayesian_rope']:.3f}"
                f", BF₁₀={m['bayesian_bf10']:.1f}"
                f" → {m['bayesian_level']}"
            )
        if m.get("tost_p_value") is not None:
            lines.append(
                f"  [v1.7 TOST] p={m['tost_p_value']:.4f}"
                f" → {m['tost_level']}"
            )

        return "\n".join(lines)
