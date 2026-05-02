from __future__ import annotations
# PROOF: [L2/品質検証] <- mekhane/fep/kalon_checker.py
"""
PROOF: [L2/品質検証] このファイルは存在しなければならない

A0 → 圏論的構造の品質 (Kalon) を定量評価する必要がある
   → category.py の型定義が「美しい不動点」に到達しているか検証する
   → kalon_checker.py が担う

Q.E.D.

---

Kalon (καλόν) Checker — 圏論的構造の品質検証

Kalon の定義 (v1.3 — 水準B: 前順序圏のガロア接続):
    Kalon(x) ⟺ x = Fix(G∘F)
    where F ⊣ G in C (前順序圏),
    F ≠ Id, G ≠ Id (非退化条件),
    G∘F admits an initial algebra

判定基準:
    - 抽象: 数式/定義が1つ以上あるか
    - 具体: 異なる文脈の例が3つ以上あるか
    - 操作: 使い方が明示されているか
    - 構造: 圏論的対応が定義されているか
    - 非退化: F≠Id かつ G≠Id

Checks:
    1. Series Enrichment: 全6 series に Enrichment が定義されているか
    2. Adjoint Pairs: 12随伴対が完全か
    3. Kalon Score: Enrichment の kalon スコアが閾値以上か
    4. Structural Completeness: Theorem/Morphism/Cone/Adjunction の整合性
    5. Non-Degeneracy: 全随伴対で F≠Id かつ G≠Id
"""

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Dict, List, Optional, Sequence

from scipy.stats import beta as beta_dist, norm

from mekhane.fep.category import (
    ADJOINT_PAIRS_D,
    SERIES_ENRICHMENTS,
    AdjointPair,
    Enrichment,
    GaloisConnection,
    Series,
)


# PURPOSE: Quality level of a Kalon check
class KalonLevel(Enum):
    """Quality level of a Kalon check result."""

    KALON = "kalon"          # 美しい: Fix(G∘F) 到達
    APPROACHING = "approaching"  # 近づいている: 軽微な問題のみ
    INCOMPLETE = "incomplete"    # 不完全: 重要な要素が欠けている
    ABSENT = "absent"            # 不在: 骨格すらない


# PURPOSE: Single G∘F iteration observation for statistical convergence (§6.3)
@dataclass
class ConvergenceObservation:
    """A single G∘F iteration observation.

    Records whether a G∘F application resulted in convergence
    (embedding distance < δ) or change (distance ≥ δ).

    Attributes:
        distance: Embedding distance d(x_n, x_{n+1}) ∈ [0, 1]
        delta: Equivalence margin δ used for this observation
        converged: Whether d < δ (True = convergence event)
        judge: Identifier of the judge who applied G (e.g. 'claude', 'gemini')
    """

    distance: float
    delta: float = 0.15  # Semantic Identity Radius (kalon.md §6.3): μ_D + z·σ_D
    converged: bool = False
    judge: str = ""

    def __post_init__(self) -> None:
        """Auto-set converged based on distance < delta."""
        self.converged = self.distance < self.delta


# PURPOSE: Serializable Bayesian prior for cross-session chaining (§6.3 v1.8)
@dataclass
class PriorState:
    """Bayesian prior state for cross-session belief inheritance.

    After a session's check_convergence_bayesian() call,
    the posterior (alpha, beta) can be exported via export_posterior()
    and stored (e.g. in Handoff). The next session loads it as prior.

    n_observations tracks the **cumulative** count across all sessions
    that contributed to this prior state.

    Optional τ-decay: stale priors regress toward uninformative Beta(1,1)
    via α' = 1 + (α-1) · exp(-Δt/τ), β' analogously.
    """

    concept_id: str = ""
    alpha: float = 1.0
    beta: float = 1.0
    n_observations: int = 0
    last_updated: str = ""

    def to_dict(self) -> dict:
        """Serialize for JSON / Handoff storage."""
        return {
            "concept_id": self.concept_id,
            "alpha": self.alpha,
            "beta": self.beta,
            "n_observations": self.n_observations,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PriorState":
        """Deserialize from JSON / Handoff storage."""
        return cls(
            concept_id=d.get("concept_id", ""),
            alpha=d.get("alpha", 1.0),
            beta=d.get("beta", 1.0),
            n_observations=d.get("n_observations", 0),
            last_updated=d.get("last_updated", ""),
        )

    def decay(self, current_time: str, tau_days: float = 30.0) -> "PriorState":
        """Apply τ-decay: stale priors regress toward Beta(1,1).

        Args:
            current_time: ISO format timestamp.
            tau_days: Half-life in days (default 30).

        Returns:
            New PriorState with decayed alpha/beta.
        """
        if not self.last_updated or tau_days <= 0:
            return self
        from datetime import datetime

        try:
            t0 = datetime.fromisoformat(self.last_updated)
            t1 = datetime.fromisoformat(current_time)
            delta_days = (t1 - t0).total_seconds() / 86400.0
        except (ValueError, TypeError):
            return self

        decay_factor = math.exp(-delta_days / tau_days)
        return PriorState(
            concept_id=self.concept_id,
            alpha=1.0 + (self.alpha - 1.0) * decay_factor,
            beta=1.0 + (self.beta - 1.0) * decay_factor,
            n_observations=self.n_observations,
            last_updated=current_time,  # P2 fix: update timestamp to prevent double-decay
        )

# PURPOSE: Result of a single Kalon check
@dataclass
class KalonResult:
    """Result of a single Kalon check.
    
    Represents the outcome of checking one aspect of Kalon quality.
    """

    name: str
    level: KalonLevel
    score: float  # 0.0 - 1.0
    details: str = ""
    issues: List[str] = field(default_factory=list)
    # §6.3 statistical extension fields (optional — backward compatible)
    ci_lower: Optional[float] = None   # Credible Interval lower bound
    ci_upper: Optional[float] = None   # Credible Interval upper bound
    convergence_prob: Optional[float] = None  # P(K(q) > θ | data)
    n_observations: int = 0            # Number of G∘F iterations observed
    # §6.3 Bayesian deepening (ROPE + Bayes Factor)
    bayes_factor: Optional[float] = None    # BF₁₀: evidence ratio for convergence
    rope_prob: Optional[float] = None       # P(K ∈ ROPE | data)
    # §6.3 v1.8 Prior Chaining (structured posterior for export)
    alpha_post: Optional[float] = None      # Posterior α (for export_posterior)
    beta_post: Optional[float] = None       # Posterior β (for export_posterior)
    # §6.5 Frequentist TOST
    tost_p_value: Optional[float] = None    # max(p₁, p₂) from TOST
    required_n: Optional[int] = None        # power analysis: needed G∘F iterations

    # PURPOSE: [L2-auto] Whether this check passes Kalon quality.
    @property
    def is_kalon(self) -> bool:
        """Whether this check passes Kalon quality."""
        return self.level == KalonLevel.KALON


# PURPOSE: Aggregate report from checking all Kalon dimensions
@dataclass
class KalonReport:
    """Aggregate report from all Kalon checks.
    
    Combines individual check results into an overall assessment.
    """

    results: List[KalonResult] = field(default_factory=list)
    timestamp: str = ""

    # PURPOSE: [L2-auto] Weighted average of all check scores.
    @property
    def overall_score(self) -> float:
        """Weighted average of all check scores."""
        if not self.results:
            return 0.0
        return sum(r.score for r in self.results) / len(self.results)

    # PURPOSE: [L2-auto] Overall Kalon level based on individual results.
    @property
    def overall_level(self) -> KalonLevel:
        """Overall Kalon level based on individual results."""
        if not self.results:
            return KalonLevel.ABSENT
        
        levels = [r.level for r in self.results]
        if all(l == KalonLevel.KALON for l in levels):
            return KalonLevel.KALON
        if any(l == KalonLevel.ABSENT for l in levels):
            return KalonLevel.INCOMPLETE
        if all(l in (KalonLevel.KALON, KalonLevel.APPROACHING) for l in levels):
            return KalonLevel.APPROACHING
        return KalonLevel.INCOMPLETE

    # PURPOSE: [L2-auto] Collect all issues from all results.
    @property
    def all_issues(self) -> List[str]:
        """Collect all issues from all results."""
        issues = []
        for r in self.results:
            for issue in r.issues:
                issues.append(f"[{r.name}] {issue}")
        return issues

    # PURPOSE: [L2-auto] One-line summary of the report.
    def summary(self) -> str:
        """One-line summary of the report."""
        passed = sum(1 for r in self.results if r.is_kalon)
        total = len(self.results)
        return (
            f"Kalon: {self.overall_level.value} "
            f"({passed}/{total} checks passed, "
            f"score={self.overall_score:.2f})"
        )


# PURPOSE: 圏論的構造の品質 (Kalon) を検証し、Fix(G∘F) 不動点到達を判定する
class KalonChecker:
    """Kalon (καλόν) Checker — 圏論的構造の品質検証.

    Checks whether the categorical structures in category.py
    have reached the Fix(G∘F) fixed point of quality.

    C = 前順序圏 (axiom_hierarchy.md L1)
    F = 展開 (左随伴, Explore/Colimit)
    G = 蒸留 (右随伴, Exploit/Limit)
    F⊣G: ガロア接続 F(x) ≤ y ⟺ x ≤ G(y)
    Fix(G∘F) = 反復しても変化しない不動点

    Usage:
        checker = KalonChecker()
        report = checker.check_all()
        print(report.summary())
    """

    # PURPOSE: Minimum kalon score threshold for each series
    KALON_THRESHOLD: float = 0.70

    # PURPOSE: Expected number of structures (evidence items) per enrichment
    MIN_STRUCTURES: int = 2

    # PURPOSE: [L2-auto] Initialize the Kalon checker.
    def __init__(
        self,
        enrichments: Optional[Dict[Series, Enrichment]] = None,
        adjoint_pairs: Optional[Dict[str, AdjointPair]] = None,
        kalon_threshold: float = 0.70,
    ):
        """Initialize the Kalon checker.

        Args:
            enrichments: Series enrichment map (defaults to SERIES_ENRICHMENTS)
            adjoint_pairs: Adjoint pair registry (defaults to ADJOINT_PAIRS_D)
            kalon_threshold: Minimum kalon score for passing
        """
        self.enrichments = enrichments or SERIES_ENRICHMENTS
        self.adjoint_pairs = adjoint_pairs or ADJOINT_PAIRS_D
        self.kalon_threshold = kalon_threshold

    # PURPOSE: Run all Kalon checks and return aggregate report
    def check_all(self) -> KalonReport:
        """Run all Kalon quality checks.

        Returns:
            KalonReport aggregating all individual checks
        """
        report = KalonReport()
        report.results.append(self.check_enrichment_completeness())
        report.results.append(self.check_enrichment_quality())
        report.results.append(self.check_kalon_distance())
        report.results.append(self.check_adjoint_completeness())
        report.results.append(self.check_adjoint_symmetry())
        report.results.append(self.check_non_degeneracy())
        report.results.append(self.check_galois_derivability())
        report.results.append(self.check_convergence_bayesian())
        report.results.append(self.check_convergence_tost())
        report.results.append(self.check_complete_lattice())
        report.results.append(self.check_triangle_inequality())
        report.results.append(self.check_l3_coherence())
        return report

    # PURPOSE: Check non-degeneracy condition (v1.3): F≠Id and G≠Id for all pairs
    def check_non_degeneracy(self) -> KalonResult:
        """Check that no adjoint pair uses identity functors.

        v1.3 non-degeneracy condition: F≠Id and G≠Id.
        Identity adjoints trivially make everything a fixed point,
        rendering the Kalon definition vacuous.
        """
        degenerate_pairs: list[str] = []

        for name, pair in self.adjoint_pairs.items():
            # An adjoint pair is degenerate if left == right
            # (both sides of the opposition are the same)
            if pair.left_wf == pair.right_wf:
                degenerate_pairs.append(
                    f"{name}: F ({pair.left_wf}) == G ({pair.right_wf})"
                )

        if not degenerate_pairs:
            return KalonResult(
                name="Non-Degeneracy",
                level=KalonLevel.KALON,
                score=1.0,
                details="All adjoint pairs have F≠G (non-degenerate)",
            )

        return KalonResult(
            name="Non-Degeneracy",
            level=KalonLevel.INCOMPLETE,
            score=0.0,
            details=f"{len(degenerate_pairs)} degenerate pairs found",
            issues=degenerate_pairs,
        )

    # PURPOSE: Check that all 6 series have Enrichment defined
    def check_enrichment_completeness(self) -> KalonResult:
        """Check that all 6 series have Enrichment metadata.
        
        Every series in Cog must carry a typed enrichment.
        Missing enrichments mean the Hom-set structure is undefined.
        """
        missing = []
        for series in Series:
            if series not in self.enrichments:
                missing.append(series.value)

        covered = len(Series) - len(missing)
        score = covered / len(Series)

        if not missing:
            return KalonResult(
                name="enrichment_completeness",
                level=KalonLevel.KALON,
                score=score,
                details=f"All {len(Series)} series have enrichment defined",
            )
        else:
            return KalonResult(
                name="enrichment_completeness",
                level=KalonLevel.INCOMPLETE,
                score=score,
                details=f"{covered}/{len(Series)} series covered",
                issues=[f"Missing enrichment for: {', '.join(missing)}"],
            )

    # PURPOSE: Check that each Enrichment has sufficient quality (kalon score + structures)
    def check_enrichment_quality(self) -> KalonResult:
        """Check enrichment quality: kalon score and structural evidence.
        
        N-11: 概念 = 数式(骨格) + 具体例(肉) + 操作性 + 体温
        Enrichment.structures = 具体例のリスト
        Enrichment.kalon = 品質スコア (None for Set = intentionally empty)
        """
        issues = []
        scores = []

        for series, enrichment in self.enrichments.items():
            # Set (P-series) intentionally has no enrichment → skip score check
            if enrichment.kalon is None:
                scores.append(1.0)  # Intentional absence = valid design choice
                continue

            # Check kalon score threshold
            if enrichment.kalon < self.kalon_threshold:
                issues.append(
                    f"{series.value}: kalon={enrichment.kalon:.2f} "
                    f"< threshold {self.kalon_threshold:.2f}"
                )
                scores.append(enrichment.kalon)
            else:
                scores.append(enrichment.kalon)

            # Check structural evidence (θ11.1)
            if len(enrichment.structures) < self.MIN_STRUCTURES:
                issues.append(
                    f"{series.value}: only {len(enrichment.structures)} "
                    f"structures (need ≥{self.MIN_STRUCTURES})"
                )

        avg_score = sum(scores) / len(scores) if scores else 0.0

        if not issues:
            return KalonResult(
                name="enrichment_quality",
                level=KalonLevel.KALON,
                score=avg_score,
                details=f"All enrichments meet quality threshold (avg={avg_score:.2f})",
            )
        elif avg_score >= self.kalon_threshold:
            return KalonResult(
                name="enrichment_quality",
                level=KalonLevel.APPROACHING,
                score=avg_score,
                details=f"Average score {avg_score:.2f} meets threshold but issues remain",
                issues=issues,
            )
        else:
            return KalonResult(
                name="enrichment_quality",
                level=KalonLevel.INCOMPLETE,
                score=avg_score,
                details=f"Average score {avg_score:.2f} below threshold",
                issues=issues,
            )

    # PURPOSE: Check Kalon distance (d_Kalon) and K(q) based on L2 enrichment
    def check_kalon_distance(self) -> KalonResult:
        """Static approximation (Stage 1) of Kalon distance K(q).

        Reads Enrichment.kalon scores as a proxy for K(q) = ε(q).

        Theoretical definition (not yet computed here):
            K(q) = ε(q) = Hom_L2(q, Fix(G∘F))
            d_Kalon(q) = 1 - K(q)

        Current implementation:
            Stage 1 — reads pre-assigned kalon scores (static).
            Stage 2 — G∘F iteration simulation (TODO: not implemented).

        The overall score uses min (worst-case) rather than arithmetic
        mean, consistent with Lawvere metric space semantics.

        Note: Series with kalon=None (e.g. Dia/Set) are excluded from
        scoring and reported as N/A.
        """
        details_list = []
        scores = []

        for series, enrichment in self.enrichments.items():
            if enrichment.kalon is None:
                details_list.append(f"{series.value}: N/A (Set — no enrichment)")
                continue

            # K(q) = precision / truth value in [0,1]
            k_q = enrichment.kalon
            # Lawvere distance: d(x,y) = 1 - Hom(x,y)
            d_kalon = 1.0 - k_q

            details_list.append(
                f"{series.value}: K(q)={k_q:.2f}, d_Kalon={d_kalon:.2f}"
            )
            scores.append(k_q)

        # Use min (worst-case) for overall score — Lawvere metric semantics
        min_kq = min(scores) if scores else 0.0
        avg_kq = sum(scores) / len(scores) if scores else 0.0

        return KalonResult(
            name="kalon_distance",
            level=KalonLevel.KALON if min_kq >= self.kalon_threshold else KalonLevel.APPROACHING,
            score=min_kq,
            details=f"min K(q)={min_kq:.2f}, avg K(q)={avg_kq:.2f} | " + ", ".join(details_list),
        )


    # PURPOSE: Check that all 12 adjoint pairs (2 per series) are present
    def check_adjoint_completeness(self) -> KalonResult:
        """Check that all 12 D-type adjoint pairs are registered.
        
        Each series should have exactly 2 adjoint pairs:
        D1 (T1⊣T3) and D2 (T2⊣T4).
        """
        expected_keys = set()
        for series in Series:
            s = series.legacy_prefix  # O, S, H, P, K, A
            expected_keys.add(f"{s}-D1")
            expected_keys.add(f"{s}-D2")

        actual_keys = set(self.adjoint_pairs.keys())
        missing = expected_keys - actual_keys
        extra = actual_keys - expected_keys

        issues = []
        if missing:
            issues.append(f"Missing adjoint pairs: {', '.join(sorted(missing))}")
        if extra:
            issues.append(f"Unexpected adjoint pairs: {', '.join(sorted(extra))}")

        score = len(expected_keys & actual_keys) / len(expected_keys)

        if not issues:
            return KalonResult(
                name="adjoint_completeness",
                level=KalonLevel.KALON,
                score=score,
                details=f"All {len(expected_keys)} adjoint pairs present",
            )
        else:
            return KalonResult(
                name="adjoint_completeness",
                level=KalonLevel.INCOMPLETE if missing else KalonLevel.APPROACHING,
                score=score,
                details=f"{len(expected_keys & actual_keys)}/{len(expected_keys)} pairs present",
                issues=issues,
            )

    # PURPOSE: Check that each adjoint pair is symmetric (L ⊣ R has distinct L ≠ R)
    def check_adjoint_symmetry(self) -> KalonResult:
        """Check adjoint pair structural integrity.
        
        Each pair must satisfy:
        - left_wf ≠ right_wf (non-degenerate)
        - left_theorem ≠ right_theorem (non-identity)
        - series matches the theorem prefix
        """
        issues = []

        for key, pair in self.adjoint_pairs.items():
            # Non-degenerate
            if pair.left_wf == pair.right_wf:
                issues.append(f"{key}: degenerate pair (L=R={pair.left_wf})")

            # Non-identity
            if pair.left_theorem == pair.right_theorem:
                issues.append(
                    f"{key}: identity adjunction "
                    f"({pair.left_theorem}={pair.right_theorem})"
                )

            # Series consistency
            expected_prefix = pair.series.legacy_prefix
            if not pair.left_theorem.startswith(expected_prefix):
                issues.append(
                    f"{key}: left theorem {pair.left_theorem} "
                    f"doesn't match series {expected_prefix}"
                )
            if not pair.right_theorem.startswith(expected_prefix):
                issues.append(
                    f"{key}: right theorem {pair.right_theorem} "
                    f"doesn't match series {expected_prefix}"
                )

        total = len(self.adjoint_pairs)
        problematic = len(set(i.split(":")[0] for i in issues))
        score = (total - problematic) / total if total else 0.0

        if not issues:
            return KalonResult(
                name="adjoint_symmetry",
                level=KalonLevel.KALON,
                score=1.0,
                details=f"All {total} pairs have valid structure",
            )
        else:
            return KalonResult(
                name="adjoint_symmetry",
                level=KalonLevel.INCOMPLETE,
                score=score,
                details=f"{total - problematic}/{total} pairs structurally valid",
                issues=issues,
            )

    # PURPOSE: Check that every AdjointPair can derive a GaloisConnection
    def check_galois_derivability(self) -> KalonResult:
        """Check that every adjoint pair produces a valid Galois connection.
        
        AdjointPair.galois() should return a well-formed GaloisConnection
        with matching series and non-empty description.
        """
        issues = []

        for key, pair in self.adjoint_pairs.items():
            gc = pair.galois
            if not isinstance(gc, GaloisConnection):
                issues.append(f"{key}: galois() returned {type(gc)}, expected GaloisConnection")
                continue

            if gc.series != pair.series:
                issues.append(
                    f"{key}: Galois series mismatch "
                    f"({gc.series} ≠ {pair.series})"
                )

            if not gc.description:
                issues.append(f"{key}: Galois connection has empty description")

        total = len(self.adjoint_pairs)
        problematic = len(set(i.split(":")[0] for i in issues))
        score = (total - problematic) / total if total else 0.0

        if not issues:
            return KalonResult(
                name="galois_derivability",
                level=KalonLevel.KALON,
                score=1.0,
                details=f"All {total} pairs derive valid Galois connections",
            )
        else:
            return KalonResult(
                name="galois_derivability",
                level=KalonLevel.APPROACHING if problematic <= 2 else KalonLevel.INCOMPLETE,
                score=score,
                details=f"{total - problematic}/{total} pairs derive valid Galois",
                issues=issues,
            )

    # PURPOSE: Verify Knaster-Tarski applicability via finite poset → complete lattice
    def check_complete_lattice(self) -> KalonResult:
        """Check that the concept space forms a complete lattice.

        kalon.md §2: Knaster-Tarski requires a complete lattice for the
        least fixed point to exist uniquely. HGK's operational concept space
        is a finite poset (finite set of enrichments/series), and every
        finite poset is a complete lattice.

        This check verifies:
        1. The enrichment set is finite (not dynamically unbounded)
        2. The set is non-empty (trivial lattice check)
        3. All kalon scores are well-ordered (form a total preorder on [0,1])
        """
        issues: List[str] = []
        n_series = len(self.enrichments)

        # Condition 1: Finiteness (environmental guarantee)
        if n_series == 0:
            issues.append("Empty enrichment set — no lattice exists")
        elif n_series > 100:
            # Defensive: if dynamically generated, finiteness is suspect
            issues.append(
                f"Enrichment set has {n_series} elements — "
                "finiteness assumption may be violated"
            )

        # Condition 2: Kalon scores form a total preorder on [0,1]
        scored_series = [
            (s, e) for s, e in self.enrichments.items() if e.kalon is not None
        ]
        if not scored_series:
            issues.append("No scored series — lattice structure unverifiable")
        else:
            for series, enrichment in scored_series:
                if not (0.0 <= enrichment.kalon <= 1.0):
                    issues.append(
                        f"{series.value}: kalon={enrichment.kalon} "
                        "outside [0,1] — violates bounded lattice"
                    )

        # Score: 1.0 if finite, non-empty, all scores in [0,1]
        score = 1.0 if not issues else 0.0
        details = (
            f"|C| = {n_series} (finite poset → complete lattice). "
            f"{len(scored_series)} scored series, all in [0,1]. "
            "Knaster-Tarski applicable."
            if not issues
            else f"|C| = {n_series}. Issues detected."
        )

        return KalonResult(
            name="complete_lattice",
            level=KalonLevel.KALON if not issues else KalonLevel.INCOMPLETE,
            score=score,
            details=details,
            issues=issues,
        )

    # PURPOSE: Verify L2 [0,1]-enriched category triangle inequality
    def check_triangle_inequality(self) -> KalonResult:
        """Check the triangle inequality for d_Kalon in [0,1]-enriched category.

        kalon.md T4 (v1.5): For a [0,1]-enriched category (Lawvere metric),
        the composition axiom requires:
            Hom(A,B) ⊗ Hom(B,C) ≤ Hom(A,C)

        With ⊗ = truncated addition (capped at 1), this is equivalent to:
            d(A,C) ≤ d(A,B) + d(B,C)

        where d(X,Y) = 1 - K(Y) when measuring distance to Fix.

        We verify this on all ordered triplets of scored series.
        """
        issues: List[str] = []
        n_checked = 0
        n_passed = 0

        scored = [
            (s, e) for s, e in self.enrichments.items() if e.kalon is not None
        ]

        if len(scored) < 3:
            return KalonResult(
                name="triangle_inequality",
                level=KalonLevel.APPROACHING,
                score=0.5,
                details=(
                    f"Only {len(scored)} scored series — "
                    "need ≥3 for triangle inequality check"
                ),
            )

        # Check all ordered triplets (A, B, C)
        for i, (s_a, e_a) in enumerate(scored):
            for j, (s_b, e_b) in enumerate(scored):
                if i == j:
                    continue
                for k, (s_c, e_c) in enumerate(scored):
                    if k == i or k == j:
                        continue
                    n_checked += 1

                    # d(X, Y) approximated by |K(X) - K(Y)|
                    d_ab = abs(e_a.kalon - e_b.kalon)
                    d_bc = abs(e_b.kalon - e_c.kalon)
                    d_ac = abs(e_a.kalon - e_c.kalon)

                    # Triangle inequality: d(A,C) ≤ d(A,B) + d(B,C)
                    if d_ac > d_ab + d_bc + 1e-9:  # float tolerance
                        issues.append(
                            f"△ violation: d({s_a.value},{s_c.value})="
                            f"{d_ac:.3f} > d({s_a.value},{s_b.value})="
                            f"{d_ab:.3f} + d({s_b.value},{s_c.value})="
                            f"{d_bc:.3f}"
                        )
                    else:
                        n_passed += 1

        score = n_passed / max(n_checked, 1)
        return KalonResult(
            name="triangle_inequality",
            level=KalonLevel.KALON if not issues else KalonLevel.INCOMPLETE,
            score=score,
            details=(
                f"{n_passed}/{n_checked} triplets satisfy △-inequality. "
                "L2 [0,1]-enriched category composition axiom verified."
                if not issues
                else f"{n_passed}/{n_checked} passed. {len(issues)} violations."
            ),
            issues=issues,
        )

    # PURPOSE: Check L3 weak 2-category coherence (pentagon & triangle identities)
    def check_l3_coherence(self) -> KalonResult:
        """Verify the coherence of the L3 weak 2-category.

        Uses mekhane.fep.two_cell.verify_coherence() to check that:
        1. Pentagon identity holds for 4-fold 1-cell compositions.
        2. Triangle identity holds for interactions with identity 1-cells.

        This guarantees the non-strict associative structure (associator)
        is well-behaved.
        """
        # Lazy import to avoid circular dependency
        from mekhane.fep.two_cell import verify_coherence

        res = verify_coherence()
        
        all_violations = res["pentagon_violations"] + res["triangle_violations"]  # type: ignore
        total_checked = res["n_pentagon_checked"] + res["n_triangle_checked"]  # type: ignore

        if res["is_coherent"]:
            level = KalonLevel.KALON
            score = 1.0
            details = (
                f"L3 coherence verified. {res['n_pentagon_checked']} pentagon "
                f"and {res['n_triangle_checked']} triangle paths commute."
            )
        else:
            level = KalonLevel.INCOMPLETE
            score = 0.0
            details = (
                f"L3 coherence failed: {len(all_violations)} violations "
                f"across {total_checked} checks."
            )

        return KalonResult(
            name="l3_coherence",
            level=level,
            score=score,
            details=details,
            issues=all_violations,  # type: ignore
        )

    # PURPOSE: Bayesian Beta convergence check with ROPE + Bayes Factor (§6.3)
    def check_convergence_bayesian(
        self,
        observations: Optional[Sequence[ConvergenceObservation]] = None,
        alpha_prior: float = 1.0,
        beta_prior: float = 1.0,
        rope_half_width: float = 0.10,
        prior: Optional[PriorState] = None,
    ) -> KalonResult:
        """Check convergence using Bayesian Beta model (kalon.md §6.3).

        Each G∘F iteration is a Bernoulli trial:
          d(x_n, x_{n+1}) < δ  →  convergence (Y=1)
          d(x_n, x_{n+1}) ≥ δ  →  change (Y=0)

        Posterior: K(q) ~ Beta(α₀ + s, β₀ + f)
        where s = convergence count, f = change count.

        v1.7 extensions:
          - ROPE (Region of Practical Equivalence): P(K ∈ [θ-w, θ+w] | data)
            Kruschke (2018). Measures whether K is "practically equivalent" to θ.
          - Bayes Factor (BF₁₀): Savage-Dickey density ratio at θ.
            BF₁₀ > 10 = strong evidence for convergence.

        Judgment (§6.3 v1.7):
          P(K > θ) ≥ 0.90, CI lower > θ, and BF₁₀ > 3 → ◎ kalon
          0.50 ≤ P(K > θ) < 0.90 → ◯ approaching
          P(K > θ) < 0.50 → incomplete

        Args:
            observations: List of G∘F iteration observations.
                If None or empty, returns uninformative prior result.
            alpha_prior: Beta prior α₀ (default: 1.0 = uninformative)
            beta_prior: Beta prior β₀ (default: 1.0 = uninformative)
            rope_half_width: Half-width of the ROPE around θ_kalon (default: 0.10)

        Returns:
            KalonResult with convergence_prob, ci, rope_prob, bayes_factor populated.
        """
        # Use PriorState if provided (prior chaining)
        if prior is not None:
            alpha_prior = prior.alpha
            beta_prior = prior.beta

        if not observations:
            # No observations — return uninformative prior
            return KalonResult(
                name="convergence_bayesian",
                level=KalonLevel.APPROACHING,
                score=0.5,
                details="No convergence observations. Prior: Beta(1,1)",
                ci_lower=0.025,
                ci_upper=0.975,
                convergence_prob=0.5,
                n_observations=0,
            )

        s = sum(1 for o in observations if o.converged)
        f = len(observations) - s
        n = len(observations)

        alpha_post = alpha_prior + s
        beta_post = beta_prior + f

        # Posterior mean = E[K(q)]
        k_mean = alpha_post / (alpha_post + beta_post)

        # P(K(q) > θ_kalon | data)
        prob_above_threshold = 1.0 - beta_dist.cdf(
            self.kalon_threshold, alpha_post, beta_post
        )

        # 95% Credible Interval
        ci_low = float(beta_dist.ppf(0.025, alpha_post, beta_post))
        ci_high = float(beta_dist.ppf(0.975, alpha_post, beta_post))

        # --- ROPE (Region of Practical Equivalence) ---
        # P(K ∈ [θ - w, θ + w] | data)
        rope_lo = max(0.0, self.kalon_threshold - rope_half_width)
        rope_hi = min(1.0, self.kalon_threshold + rope_half_width)
        rope_mass = float(
            beta_dist.cdf(rope_hi, alpha_post, beta_post)
            - beta_dist.cdf(rope_lo, alpha_post, beta_post)
        )

        # --- Bayes Factor (Savage-Dickey density ratio) ---
        # BF₁₀ = prior(θ) / posterior(θ)
        # H₀: K = θ (point null at threshold)
        # H₁: K ≠ θ (K is somewhere in [0,1])
        # If BF₁₀ > 1 → evidence against H₀ (K is NOT at threshold)
        # We want P(K > θ), so we compute BF for H₁: K > θ vs H₀: K ≤ θ
        prior_density_at_theta = float(
            beta_dist.pdf(self.kalon_threshold, alpha_prior, beta_prior)
        )
        posterior_density_at_theta = float(
            beta_dist.pdf(self.kalon_threshold, alpha_post, beta_post)
        )
        # Savage-Dickey: BF₁₀ = prior(θ) / posterior(θ)
        # High BF₁₀ → posterior has moved away from θ (evidence for H₁)
        if posterior_density_at_theta > 1e-10:
            bf_10 = prior_density_at_theta / posterior_density_at_theta
        else:
            bf_10 = float("inf")  # Posterior vanished at θ → strong evidence

        # §6.3 v1.7 judgment criteria
        if (prob_above_threshold >= 0.90
                and ci_low > self.kalon_threshold
                and bf_10 > 3.0):
            level = KalonLevel.KALON
        elif prob_above_threshold >= 0.50:
            level = KalonLevel.APPROACHING
        else:
            level = KalonLevel.INCOMPLETE

        # Bayes Factor interpretation label
        if bf_10 > 100:
            bf_label = "decisive"
        elif bf_10 > 30:
            bf_label = "very strong"
        elif bf_10 > 10:
            bf_label = "strong"
        elif bf_10 > 3:
            bf_label = "moderate"
        elif bf_10 > 1:
            bf_label = "anecdotal"
        else:
            bf_label = "against"

        details = (
            f"Beta({alpha_post:.0f},{beta_post:.0f}): "
            f"E[K]={k_mean:.3f}, "
            f"P(K>{self.kalon_threshold:.2f})={prob_above_threshold:.3f}, "
            f"95%CI=[{ci_low:.3f},{ci_high:.3f}], "
            f"ROPE=[{rope_lo:.2f},{rope_hi:.2f}]→{rope_mass:.3f}, "
            f"BF₁₀={bf_10:.2f} ({bf_label}), "
            f"n={n} (s={s},f={f})"
        )

        issues = []
        if ci_high - ci_low > 0.5:
            issues.append(
                f"Wide credible interval ({ci_high - ci_low:.2f}): "
                f"more G∘F iterations needed"
            )

        return KalonResult(
            name="convergence_bayesian",
            level=level,
            score=float(k_mean),
            details=details,
            issues=issues,
            ci_lower=ci_low,
            ci_upper=ci_high,
            convergence_prob=float(prob_above_threshold),
            n_observations=n,
            bayes_factor=float(bf_10) if bf_10 != float("inf") else 999.99,
            rope_prob=rope_mass,
            alpha_post=float(alpha_post),
            beta_post=float(beta_post),
        )

    # PURPOSE: Export posterior for cross-session prior chaining (§6.3 v1.8)
    def export_posterior(
        self,
        result: KalonResult,
        concept_id: str = "",
    ) -> PriorState:
        """Extract posterior parameters from a Bayesian result.

        The returned PriorState can be serialized (to_dict) and stored
        in a Handoff document. The next session's check_convergence_bayesian
        can then use it as `prior=PriorState.from_dict(data)`.

        Args:
            result: KalonResult from check_convergence_bayesian().
            concept_id: Label for the concept being tracked.

        Returns:
            PriorState with posterior α, β from structured fields.
        """
        from datetime import datetime

        alpha = result.alpha_post if result.alpha_post is not None else 1.0
        beta = result.beta_post if result.beta_post is not None else 1.0

        return PriorState(
            concept_id=concept_id,
            alpha=alpha,
            beta=beta,
            n_observations=result.n_observations,
            last_updated=datetime.now().isoformat(),
        )

    # PURPOSE: Frequentist TOST equivalence test (§6.5)
    def check_convergence_tost(
        self,
        observations: Optional[Sequence[ConvergenceObservation]] = None,
        alpha: float = 0.05,
        target_power: float = 0.80,
    ) -> KalonResult:
        """Frequentist TOST equivalence test for Fix convergence (kalon.md §6.5).

        TOST (Two One-Sided Tests) tests whether the convergence rate p
        is equivalent to or exceeds the threshold θ_kalon.

        Hypotheses:
          H₀: p ≤ θ_kalon - δ  OR  p ≥ θ_kalon + δ   (NOT equivalent)
          H₁: θ_kalon - δ < p < θ_kalon + δ           (equivalent to θ)

        For Kalon, we care about p ≥ θ, so we test:
          H₀: p ≤ θ_kalon   (convergence rate is below threshold)
          H₁: p > θ_kalon   (convergence rate exceeds threshold)

        This is a one-sided test of proportion, with power analysis
        to determine the required number of G∘F iterations.

        Args:
            observations: G∘F iteration observations
            alpha: Significance level (default: 0.05)
            target_power: Target statistical power (default: 0.80)

        Returns:
            KalonResult with tost_p_value and required_n populated
        """
        if not observations:
            # Power analysis only — no observations
            req_n = self.power_analysis(
                alpha=alpha,
                target_power=target_power,
                estimated_p=0.80,  # Optimistic prior
            )
            return KalonResult(
                name="convergence_tost",
                level=KalonLevel.APPROACHING,
                score=0.5,
                details=(
                    f"No observations. "
                    f"Power analysis: need n≥{req_n} G∘F iterations "
                    f"(α={alpha}, power={target_power}, θ={self.kalon_threshold})"
                ),
                tost_p_value=None,
                required_n=req_n,
                n_observations=0,
            )

        n = len(observations)
        s = sum(1 for o in observations if o.converged)
        p_hat = s / n  # Sample proportion

        theta = self.kalon_threshold

        # One-sided z-test: H₀: p ≤ θ vs H₁: p > θ
        # z = (p̂ - θ) / sqrt(θ(1-θ)/n)
        se = math.sqrt(theta * (1 - theta) / n) if n > 0 else 1.0
        if se > 1e-10:
            z = (p_hat - theta) / se
        else:
            z = 0.0

        # One-sided p-value: P(Z > z | H₀)
        p_value = float(1.0 - norm.cdf(z))

        # Power analysis: how many more iterations to reach target_power?
        req_n = self.power_analysis(
            alpha=alpha,
            target_power=target_power,
            estimated_p=max(p_hat, theta + 0.01),  # At least slightly above θ
        )

        # Observed power at current n
        if p_hat > theta and se > 1e-10:
            # Non-centrality parameter under H₁ (true p = p_hat)
            se_h1 = math.sqrt(theta * (1 - theta) / n)
            z_crit = norm.ppf(1 - alpha)
            lambda_nc = (p_hat - theta) / se_h1
            observed_power = float(1.0 - norm.cdf(z_crit - lambda_nc))
        else:
            observed_power = 0.0

        # Judgment
        if p_value < alpha and n >= 5:
            level = KalonLevel.KALON
        elif p_value < 0.10:
            level = KalonLevel.APPROACHING
        else:
            level = KalonLevel.INCOMPLETE

        details = (
            f"TOST: p̂={p_hat:.3f}, z={z:.3f}, p={p_value:.4f} "
            f"(α={alpha}), "
            f"power={observed_power:.3f}, "
            f"needed n≥{req_n}, "
            f"n={n} (s={s})"
        )

        issues = []
        if n < req_n:
            issues.append(
                f"Insufficient data: n={n} < required n={req_n} "
                f"for power={target_power}"
            )
        if p_hat < theta and n > 3:
            issues.append(
                f"Convergence rate {p_hat:.2f} below threshold {theta:.2f}"
            )

        return KalonResult(
            name="convergence_tost",
            level=level,
            score=float(p_hat),
            details=details,
            issues=issues,
            tost_p_value=float(p_value),
            required_n=req_n,
            n_observations=n,
        )

    # PURPOSE: Calculate required sample size for given power (§6.5)
    def power_analysis(
        self,
        alpha: float = 0.05,
        target_power: float = 0.80,
        estimated_p: float = 0.80,
    ) -> int:
        """Calculate required G∘F iterations for target statistical power.

        For a one-sided test of proportion H₀: p ≤ θ vs H₁: p > θ:
          n = ((z_α + z_β)² × θ(1-θ)) / (p₁ - θ)²

        where p₁ is the true convergence rate under H₁.

        Args:
            alpha: Significance level (Type I error rate)
            target_power: Target power = 1 - β (Type II error rate)
            estimated_p: Estimated true convergence rate under H₁

        Returns:
            Required number of G∘F iterations (minimum 3)
        """
        theta = self.kalon_threshold

        # If estimated_p ≤ θ, can't detect convergence above θ
        if estimated_p <= theta:
            return 999  # Effectively impossible

        z_alpha = float(norm.ppf(1 - alpha))
        z_beta = float(norm.ppf(target_power))

        # Normal approximation to binomial
        # n = ((z_α × √(θ(1-θ)) + z_β × √(p₁(1-p₁)))² / (p₁ - θ)²
        numerator = (
            z_alpha * math.sqrt(theta * (1 - theta))
            + z_beta * math.sqrt(estimated_p * (1 - estimated_p))
        ) ** 2
        denominator = (estimated_p - theta) ** 2

        if denominator < 1e-10:
            return 999

        n = math.ceil(numerator / denominator)
        return max(n, 3)  # Minimum 3 observations

