#!/usr/bin/env python3
"""
q_invariance_check.py  —  Forgetting curvature F_{ij} under reference change
=============================================================================

Paper I §4 の Gaussian toy model で、参照分布 q を変えたとき
忘却曲率 F_{12} がどう変わるかを symbolic + numeric に検証する。

Setup:
  - 1D Gaussian family  p(x|μ,σ), parameter space M = {(μ,σ): σ>0}
  - Fisher metric:  g_{11} = 1/σ², g_{12} = 0, g_{22} = 2/σ²
  - Chebyshev 1-form:  T₁ = 0, T₂ = 6/σ
  - dT = 0  (verified in Paper I)
  - Forgetting field:  Φ(θ) = D_KL(p_θ ‖ q)
  - Forgetting connection:  A_i = ∂_iΦ + (α/2)Φ T_i
  - Forgetting curvature:  F_{ij} = (α/2)[(∂_iΦ)T_j − (∂_jΦ)T_i]   (since dT=0)

Questions:
  1. Is ∂_k F_{ij} q-independent?
  2. Is the SIGN of F_{ij} q-dependent?
  3. Under what conditions on (μ₀,σ₀) vs (μ₀',σ₀') does the sign flip?
"""

import sympy as sp
import numpy as np
from itertools import product

# ═══════════════════════════════════════════════════════════════════════
# Part 1: Symbolic computation
# ═══════════════════════════════════════════════════════════════════════

print("=" * 72)
print("PART 1: SYMBOLIC COMPUTATION")
print("=" * 72)

# Symbols
mu, sigma = sp.symbols("mu sigma", real=True, positive=True)
mu0, sigma0 = sp.symbols("mu_0 sigma_0", real=True, positive=True)
mu0p, sigma0p = sp.symbols("mu_0' sigma_0'", real=True, positive=True)
alpha = sp.symbols("alpha", real=True)

# -----------------------------------------------------------------------
# Step 1: KL divergence Φ(μ,σ) = D_KL(N(μ,σ²) ‖ N(μ₀,σ₀²))
# -----------------------------------------------------------------------
Phi = sp.log(sigma0 / sigma) + (sigma**2 + (mu - mu0)**2) / (2 * sigma0**2) - sp.Rational(1, 2)

print("\n--- Step 1: Forgetting field Φ(μ,σ) ---")
print(f"Φ = {Phi}")

# -----------------------------------------------------------------------
# Step 2: Partial derivatives
# -----------------------------------------------------------------------
dPhi_dmu = sp.diff(Phi, mu)
dPhi_dsigma = sp.diff(Phi, sigma)

dPhi_dmu_simplified = sp.simplify(dPhi_dmu)
dPhi_dsigma_simplified = sp.simplify(dPhi_dsigma)

print("\n--- Step 2: Partial derivatives ---")
print(f"∂_μ Φ  = {dPhi_dmu_simplified}")
print(f"∂_σ Φ  = {dPhi_dsigma_simplified}")

# -----------------------------------------------------------------------
# Step 3: Chebyshev 1-form
# -----------------------------------------------------------------------
T1 = sp.Integer(0)
T2 = 6 / sigma

print("\n--- Step 3: Chebyshev 1-form ---")
print(f"T₁ = {T1}")
print(f"T₂ = {T2}")

# -----------------------------------------------------------------------
# Step 4: Forgetting curvature F_{12}
# Since T₁ = 0:
#   F_{12} = (α/2)[(∂_μΦ)T₂ − (∂_σΦ)T₁] = (α/2)(∂_μΦ)(6/σ)
# -----------------------------------------------------------------------
F12 = (alpha / 2) * (dPhi_dmu * T2 - dPhi_dsigma * T1)
F12_simplified = sp.simplify(F12)

print("\n--- Step 4: Forgetting curvature F_{12} ---")
print(f"F_{{12}} = {sp.expand(F12_simplified)}")

# Factor out to see structure
F12_factored = sp.factor(F12)
print(f"F_{{12}} (factored) = {F12_factored}")

# -----------------------------------------------------------------------
# Step 5: Change reference to q' = N(μ₀', σ₀'²)
# -----------------------------------------------------------------------
Phi_prime = sp.log(sigma0p / sigma) + (sigma**2 + (mu - mu0p)**2) / (2 * sigma0p**2) - sp.Rational(1, 2)
dPhi_prime_dmu = sp.diff(Phi_prime, mu)
dPhi_prime_dsigma = sp.diff(Phi_prime, sigma)

F12_prime = (alpha / 2) * (dPhi_prime_dmu * T2 - dPhi_prime_dsigma * T1)
F12_prime_simplified = sp.simplify(F12_prime)

print("\n--- Step 5: F'_{12} with reference q' = N(μ₀', σ₀'²) ---")
print(f"F'_{{12}} = {sp.expand(F12_prime_simplified)}")

# -----------------------------------------------------------------------
# Step 6: Difference F'_{12} − F_{12}
# -----------------------------------------------------------------------
diff_F = sp.simplify(F12_prime - F12)
diff_F_expanded = sp.expand(diff_F)

print("\n--- Step 6: Difference F'_{12} − F_{12} ---")
print(f"F'_{{12}} − F_{{12}} = {diff_F_expanded}")

# Check if difference depends on (μ, σ)
depends_on_mu = diff_F_expanded.has(mu)
depends_on_sigma = diff_F_expanded.has(sigma)

print(f"\nDoes F'_{{12}} − F_{{12}} depend on μ?  → {depends_on_mu}")
print(f"Does F'_{{12}} − F_{{12}} depend on σ?  → {depends_on_sigma}")

if depends_on_mu or depends_on_sigma:
    print("⇒ The difference IS position-dependent → F_{12} is NOT simply shifted by a constant")
else:
    print("⇒ The difference is position-independent → F_{12} shifts by a constant")

# -----------------------------------------------------------------------
# Step 7: Derivatives of F_{12} w.r.t. μ and σ
# -----------------------------------------------------------------------
dF12_dmu = sp.simplify(sp.diff(F12, mu))
dF12_dsigma = sp.simplify(sp.diff(F12, sigma))

print("\n--- Step 7: Derivatives of F_{12} (q-independence check) ---")
print(f"∂_μ F_{{12}} = {dF12_dmu}")
print(f"∂_σ F_{{12}} = {dF12_dsigma}")

# Check q-dependence
dF12_dmu_depends_q = dF12_dmu.has(mu0) or dF12_dmu.has(sigma0)
dF12_dsigma_depends_q = dF12_dsigma.has(mu0) or dF12_dsigma.has(sigma0)

print(f"\nDoes ∂_μ F_{{12}} depend on (μ₀, σ₀)?  → {dF12_dmu_depends_q}")
print(f"Does ∂_σ F_{{12}} depend on (μ₀, σ₀)?  → {dF12_dsigma_depends_q}")

# Cross-check: compute derivatives of F'_{12}
dF12p_dmu = sp.simplify(sp.diff(F12_prime, mu))
dF12p_dsigma = sp.simplify(sp.diff(F12_prime, sigma))

print(f"\n∂_μ F'_{{12}} = {dF12p_dmu}")
print(f"∂_σ F'_{{12}} = {dF12p_dsigma}")

# Check if derivatives are equal
dmu_equal = sp.simplify(dF12_dmu - dF12p_dmu) == 0
dsigma_equal = sp.simplify(dF12_dsigma - dF12p_dsigma) == 0

print(f"\n∂_μ F_{{12}} == ∂_μ F'_{{12}}?  → {dmu_equal}")
print(f"∂_σ F_{{12}} == ∂_σ F'_{{12}}?  → {dsigma_equal}")

if dmu_equal and dsigma_equal:
    print("⇒ CONFIRMED: ∂_k F_{12} is q-independent")
else:
    print("⇒ WARNING: ∂_k F_{12} appears q-dependent — checking further...")
    # Expand and compare
    diff_dmu = sp.expand(sp.simplify(dF12_dmu - dF12p_dmu))
    diff_dsigma = sp.expand(sp.simplify(dF12_dsigma - dF12p_dsigma))
    print(f"  Difference in ∂_μ: {diff_dmu}")
    print(f"  Difference in ∂_σ: {diff_dsigma}")

# -----------------------------------------------------------------------
# Step 8: Sign analysis — when does F_{12} = 0?
# -----------------------------------------------------------------------
print("\n--- Step 8: Sign analysis of F_{12} ---")

# F_{12} = (α/2)(∂_μΦ)(6/σ) = (α/2)(μ − μ₀)/σ₀² · (6/σ) = 3α(μ − μ₀)/(σ₀² σ)
# Since σ > 0, sign(F_{12}) = sign(α) · sign(μ − μ₀) / sign(σ₀²)
# σ₀² > 0 always, so: sign(F_{12}) = sign(α) · sign(μ − μ₀)

print(f"\nF_{{12}} in explicit form:")
F12_explicit = sp.factor(F12)
print(f"  F_{{12}} = {F12_explicit}")

# Zero locus
F12_zero = sp.solve(F12, mu)
print(f"\nF_{{12}} = 0  when:  μ = {F12_zero}  (or α = 0)")

print(f"\nSign structure (assuming α > 0, σ > 0, σ₀ > 0):")
print(f"  F_{{12}} > 0  ⟺  μ > μ₀  (field point is to the RIGHT of reference)")
print(f"  F_{{12}} < 0  ⟺  μ < μ₀  (field point is to the LEFT of reference)")
print(f"  F_{{12}} = 0  ⟺  μ = μ₀  (field point has same mean as reference)")

print(f"\n⇒ Changing q from N(μ₀,σ₀²) to N(μ₀',σ₀'²) shifts the zero locus")
print(f"   from μ = μ₀ to μ = μ₀'.")
print(f"   At any fixed point (μ,σ), the SIGN of F_{{12}} can flip")
print(f"   if μ₀ < μ < μ₀' (or μ₀' < μ < μ₀).")

# ═══════════════════════════════════════════════════════════════════════
# Part 2: Deeper symbolic analysis — the full structure
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 72)
print("PART 2: STRUCTURAL DECOMPOSITION")
print("=" * 72)

# Write F_{12} = (α/2) * (∂_μΦ) * (6/σ) and decompose ∂_μΦ
print("\n∂_μΦ = (μ − μ₀) / σ₀²")
print("∂_σΦ = −1/σ + σ/σ₀²")
print()
print("F_{12} = (α/2) · [(μ−μ₀)/σ₀²] · [6/σ]")
print("       = 3α(μ−μ₀) / (σ₀² σ)")
print()
print("Key observations:")
print("  1. F_{12} depends on q only through μ₀ and σ₀ — both appear")
print("  2. The μ₀-dependence is AFFINE:  F_{12} = 3α/(σ₀²σ) · μ  −  3αμ₀/(σ₀²σ)")
print("  3. The σ₀-dependence is via 1/σ₀²  (overall scale)")
print()

# Decompose F_{12} into q-dependent and q-independent parts
# F_{12} = [3α μ / (σ₀² σ)] − [3α μ₀ / (σ₀² σ)]
#         = [3α / (σ₀² σ)] (μ − μ₀)
# Both terms depend on σ₀, so there's no clean q-independent piece.
# BUT: the *derivative* kills the constant μ₀ term.

print("∂_μ F_{12} = 3α / (σ₀² σ)")
print("∂_σ F_{12} = −3α(μ−μ₀) / (σ₀² σ²)")
print()
print("Both derivatives STILL depend on σ₀  (via 1/σ₀²).")
print("So ∂_k F_{12} is NOT q-independent in general.")
print()
print("However, the σ₀ dependence is a GLOBAL SCALE FACTOR:")
print("  ∂_μ F_{12} = [3α/σ₀²] · [1/σ]")
print("  ∂_σ F_{12} = [3α/σ₀²] · [−(μ−μ₀)/σ²]")
print()
print("The 'shape' on M (the dependence on μ,σ) is q-independent.")
print("Only the amplitude 1/σ₀² depends on q.")


# ═══════════════════════════════════════════════════════════════════════
# Part 3: Ratio analysis — what IS q-independent?
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 72)
print("PART 3: RATIO ANALYSIS — WHAT IS q-INDEPENDENT?")
print("=" * 72)

# The ratio ∂_σ F_{12} / ∂_μ F_{12} kills σ₀
ratio = sp.simplify(dF12_dsigma / dF12_dmu)
print(f"\n∂_σ F_{{12}} / ∂_μ F_{{12}} = {ratio}")
ratio_has_q = ratio.has(mu0) or ratio.has(sigma0)
print(f"Does this ratio depend on (μ₀, σ₀)?  → {ratio_has_q}")

# The gradient direction is q-independent
print("\n⇒ The DIRECTION of ∇F_{12} on M is q-independent.")
print("   Only the MAGNITUDE of the gradient depends on q (via 1/σ₀²).")

# What about σ₀² F_{12}?
scaled_F12 = sp.simplify(sigma0**2 * F12)
print(f"\nσ₀² · F_{{12}} = {sp.expand(scaled_F12)}")
scaled_has_q = scaled_F12.has(mu0) or scaled_F12.has(sigma0)
print(f"Does σ₀² · F_{{12}} depend on (μ₀, σ₀)?  → {scaled_has_q}")

# So σ₀² F_{12} depends on μ₀ but not σ₀
scaled_has_sigma0 = scaled_F12.has(sigma0)
scaled_has_mu0 = scaled_F12.has(mu0)
print(f"  Depends on σ₀? → {scaled_has_sigma0}")
print(f"  Depends on μ₀? → {scaled_has_mu0}")

# Normalize: σ₀² σ F_{12} / (3α)
fully_normalized = sp.simplify(sigma0**2 * sigma * F12 / (3 * alpha))
print(f"\nσ₀² σ F_{{12}} / (3α) = {sp.expand(fully_normalized)}")
print(f"This is simply (μ − μ₀), which depends on μ₀ but not σ₀.")


# ═══════════════════════════════════════════════════════════════════════
# Part 4: Connection to Fisher metric — gauge-covariant form
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 72)
print("PART 4: GEOMETRIC INTERPRETATION")
print("=" * 72)

# F_{12} using Fisher metric components
# g^{11} = σ², g^{22} = σ²/2
# ∂_μΦ = (μ−μ₀)/σ₀² ; raise index: (∂Φ)^1 = g^{11} ∂_1Φ = σ²(μ−μ₀)/σ₀²
# (∂Φ)^1 T_2 = σ²(μ−μ₀)/σ₀² · 6/σ = 6σ(μ−μ₀)/σ₀²
print("Raised-index gradient of Φ:")
print("  (∂Φ)^1 = g^{11} ∂_μΦ = σ²(μ−μ₀)/σ₀²")
print("  (∂Φ)^2 = g^{22} ∂_σΦ = (σ²/2)(−1/σ + σ/σ₀²) = −σ/2 + σ³/(2σ₀²)")
print()

# The forgetting curvature as a "wedge" of gradient and Chebyshev
print("F_{12} = (α/2)(∂Φ ∧ T)_{12}")
print("       = (α/2)[(∂_1Φ)(T_2) − (∂_2Φ)(T_1)]")
print("       = (α/2)(∂_1Φ)(T_2)          since T_1 = 0")
print()
print("This is the 'torsion-gradient wedge product'.")
print("The sign of F_{12} depends on the sign of ∂_μΦ = (μ−μ₀)/σ₀².")
print("Since σ₀² > 0, sign(∂_μΦ) = sign(μ − μ₀).")
print()
print("CONCLUSION on sign:")
print("  The sign of F_{12} at point (μ,σ) is determined by sign(α)·sign(μ−μ₀).")
print("  This DEPENDS on the reference q through μ₀.")
print("  Changing q shifts the 'zero line' of F_{12} from μ=μ₀ to μ=μ₀'.")


# ═══════════════════════════════════════════════════════════════════════
# Part 5: Numerical verification
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 72)
print("PART 5: NUMERICAL VERIFICATION")
print("=" * 72)

def kl_gaussian(mu_val, sigma_val, mu0_val, sigma0_val):
    """D_KL(N(μ,σ²) ‖ N(μ₀,σ₀²))"""
    return (np.log(sigma0_val / sigma_val)
            + (sigma_val**2 + (mu_val - mu0_val)**2) / (2 * sigma0_val**2)
            - 0.5)

def F12_numeric(mu_val, sigma_val, mu0_val, sigma0_val, alpha_val):
    """F_{12} = 3α(μ−μ₀)/(σ₀² σ)"""
    return 3 * alpha_val * (mu_val - mu0_val) / (sigma0_val**2 * sigma_val)

def dF12_dmu_numeric(sigma_val, sigma0_val, alpha_val):
    """∂_μ F_{12} = 3α/(σ₀² σ)"""
    return 3 * alpha_val / (sigma0_val**2 * sigma_val)

def dF12_dsigma_numeric(mu_val, sigma_val, mu0_val, sigma0_val, alpha_val):
    """∂_σ F_{12} = −3α(μ−μ₀)/(σ₀² σ²)"""
    return -3 * alpha_val * (mu_val - mu0_val) / (sigma0_val**2 * sigma_val**2)

# Test configurations
alpha_val = 1.0

# Reference q = N(0, 1)
q1 = (0.0, 1.0)
# Reference q' = N(2, 1)
q2 = (2.0, 1.0)
# Reference q'' = N(0, 3)
q3 = (0.0, 3.0)
# Reference q''' = N(2, 3)
q4 = (2.0, 3.0)

refs = [q1, q2, q3, q4]
ref_names = ["N(0,1)", "N(2,1)", "N(0,3)", "N(2,3)"]

# Test points on M
test_points = [(1.0, 1.0), (1.0, 2.0), (-1.0, 1.0), (3.0, 0.5), (0.5, 1.5)]
point_names = ["(1,1)", "(1,2)", "(-1,1)", "(3,0.5)", "(0.5,1.5)"]

print(f"\nα = {alpha_val}")
print(f"\n{'Point':>10} | ", end="")
for rn in ref_names:
    print(f"  q={rn:>8} ", end="")
print("\n" + "-" * (14 + 14 * len(refs)))

for (mv, sv), pn in zip(test_points, point_names):
    print(f"{pn:>10} | ", end="")
    for (m0, s0) in refs:
        f = F12_numeric(mv, sv, m0, s0, alpha_val)
        print(f"  {f:>+10.4f} ", end="")
    print()

print("\n--- Sign comparison ---")
print(f"{'Point':>10} | ", end="")
for rn in ref_names:
    print(f"  q={rn:>8} ", end="")
print("\n" + "-" * (14 + 14 * len(refs)))

for (mv, sv), pn in zip(test_points, point_names):
    print(f"{pn:>10} | ", end="")
    signs = []
    for (m0, s0) in refs:
        f = F12_numeric(mv, sv, m0, s0, alpha_val)
        s = "+" if f > 0 else ("-" if f < 0 else "0")
        signs.append(s)
        print(f"  {'':>4}{s:>6} ", end="")
    print()

# -----------------------------------------------------------------------
# Sign flip detection
# -----------------------------------------------------------------------
print("\n--- Sign flip detection ---")
print("Comparing all pairs of references:")
for i in range(len(refs)):
    for j in range(i + 1, len(refs)):
        print(f"\n  {ref_names[i]} → {ref_names[j]}:")
        for (mv, sv), pn in zip(test_points, point_names):
            f1 = F12_numeric(mv, sv, refs[i][0], refs[i][1], alpha_val)
            f2 = F12_numeric(mv, sv, refs[j][0], refs[j][1], alpha_val)
            if np.sign(f1) != np.sign(f2) and f1 != 0 and f2 != 0:
                print(f"    SIGN FLIP at {pn}: F={f1:+.4f} → F={f2:+.4f}")

# -----------------------------------------------------------------------
# Derivative q-dependence check
# -----------------------------------------------------------------------
print("\n--- Derivative q-dependence check ---")
print("∂_μ F_{12} at each test point for different q's:")
print(f"{'Point':>10} | ", end="")
for rn in ref_names:
    print(f"  q={rn:>8} ", end="")
print("\n" + "-" * (14 + 14 * len(refs)))

for (mv, sv), pn in zip(test_points, point_names):
    print(f"{pn:>10} | ", end="")
    for (m0, s0) in refs:
        d = dF12_dmu_numeric(sv, s0, alpha_val)
        print(f"  {d:>+10.4f} ", end="")
    print()

print("\n∂_σ F_{12} at each test point for different q's:")
print(f"{'Point':>10} | ", end="")
for rn in ref_names:
    print(f"  q={rn:>8} ", end="")
print("\n" + "-" * (14 + 14 * len(refs)))

for (mv, sv), pn in zip(test_points, point_names):
    print(f"{pn:>10} | ", end="")
    for (m0, s0) in refs:
        d = dF12_dsigma_numeric(mv, sv, m0, s0, alpha_val)
        print(f"  {d:>+10.4f} ", end="")
    print()

print("\n⇒ The VALUES of ∂_k F_{12} DO change with q (via 1/σ₀² scaling).")
print("   BUT: the ratio ∂_σ F_{12} / ∂_μ F_{12} = −(μ−μ₀)/σ is q-dependent through μ₀!")
print("   So ∂_k F_{12} is NOT q-independent.")

# -----------------------------------------------------------------------
# Refined question: what about ∂²Φ contribution?
# Let's check if the second derivative ∂_μ ∂_σ Φ is q-independent
# -----------------------------------------------------------------------
print("\n" + "=" * 72)
print("PART 6: SECOND DERIVATIVES OF Φ  (HESSIAN)")
print("=" * 72)

d2Phi_dmu2 = sp.simplify(sp.diff(Phi, mu, mu))
d2Phi_dmu_dsigma = sp.simplify(sp.diff(Phi, mu, sigma))
d2Phi_dsigma2 = sp.simplify(sp.diff(Phi, sigma, sigma))

print(f"\n∂²Φ/∂μ²        = {d2Phi_dmu2}")
print(f"∂²Φ/∂μ∂σ       = {d2Phi_dmu_dsigma}")
print(f"∂²Φ/∂σ²        = {d2Phi_dsigma2}")

print(f"\n∂²Φ/∂μ² depends on q?  → {d2Phi_dmu2.has(mu0) or d2Phi_dmu2.has(sigma0)}")
print(f"∂²Φ/∂μ∂σ depends on q? → {d2Phi_dmu_dsigma.has(mu0) or d2Phi_dmu_dsigma.has(sigma0)}")
print(f"∂²Φ/∂σ² depends on q?  → {d2Phi_dsigma2.has(mu0) or d2Phi_dsigma2.has(sigma0)}")

# The Hessian's q-dependence:
# ∂²Φ/∂μ² = 1/σ₀²  — depends on σ₀ only
# ∂²Φ/∂μ∂σ = 0     — q-independent!
# ∂²Φ/∂σ² = 1/σ² + 1/σ₀² — depends on σ₀

print("\n⇒ Only ∂²Φ/∂μ∂σ = 0 is trivially q-independent.")
print("   The diagonal Hessian entries depend on σ₀ via 1/σ₀².")


# ═══════════════════════════════════════════════════════════════════════
# Part 7: The critical decomposition — exact gauge transformation
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 72)
print("PART 7: EXACT GAUGE TRANSFORMATION UNDER q → q'")
print("=" * 72)

# Φ'(μ,σ) − Φ(μ,σ) = D_KL(p ‖ q') − D_KL(p ‖ q)
delta_Phi = sp.simplify(Phi_prime - Phi)
delta_Phi_expanded = sp.expand(delta_Phi)

print(f"\nΔΦ = Φ' − Φ = {delta_Phi_expanded}")

# Derivatives of ΔΦ
d_delta_dmu = sp.simplify(sp.diff(delta_Phi, mu))
d_delta_dsigma = sp.simplify(sp.diff(delta_Phi, sigma))

print(f"\n∂_μ ΔΦ = {d_delta_dmu}")
print(f"∂_σ ΔΦ = {d_delta_dsigma}")

print(f"\n∂_μ ΔΦ depends on σ?  → {d_delta_dmu.has(sigma)}")
print(f"∂_σ ΔΦ depends on μ?  → {d_delta_dsigma.has(mu)}")

# The curvature difference
# F'_{12} − F_{12} = (α/2)[(∂_μΔΦ)T₂ − (∂_σΔΦ)T₁]
#                   = (α/2)(∂_μΔΦ)(6/σ)
delta_F12 = sp.simplify((alpha / 2) * d_delta_dmu * T2)
print(f"\nF'_{{12}} − F_{{12}} = (α/2)(∂_μΔΦ)(6/σ)")
print(f"                   = {sp.expand(delta_F12)}")

# Check: does this depend on (μ, σ)?
delta_F12_depends_mu = delta_F12.has(mu)
delta_F12_depends_sigma = delta_F12.has(sigma)

print(f"\nDepends on μ? → {delta_F12_depends_mu}")
print(f"Depends on σ? → {delta_F12_depends_sigma}")

# Simplify ∂_μ ΔΦ
print(f"\nKey insight: ∂_μ ΔΦ = {d_delta_dmu}")
print("This is independent of σ but DOES depend on μ.")
print("Specifically: ∂_μ ΔΦ = (μ−μ₀')/σ₀'² − (μ−μ₀)/σ₀²")
print("             = μ(1/σ₀'² − 1/σ₀²) − (μ₀'/σ₀'² − μ₀/σ₀²)")
print()
print("So F'_{12}−F_{12} = 3α/σ · [μ(1/σ₀'²−1/σ₀²) − (μ₀'/σ₀'²−μ₀/σ₀²)]")
print()
print("This depends on BOTH μ and σ unless σ₀' = σ₀.")

# Special case: σ₀' = σ₀
print("\n--- Special case: σ₀' = σ₀ (only μ₀ changes) ---")
delta_F12_same_sigma = delta_F12.subs(sigma0p, sigma0)
delta_F12_same_sigma = sp.simplify(delta_F12_same_sigma)
print(f"F'_{{12}} − F_{{12}} |_{{σ₀'=σ₀}} = {sp.expand(delta_F12_same_sigma)}")
same_sigma_depends_mu = delta_F12_same_sigma.has(mu)
same_sigma_depends_sigma = delta_F12_same_sigma.has(sigma)
print(f"Depends on μ? → {same_sigma_depends_mu}")
print(f"Depends on σ? → {same_sigma_depends_sigma}")
if same_sigma_depends_sigma and not same_sigma_depends_mu:
    print("⇒ When only μ₀ changes, the difference depends on σ (via 1/σ) but NOT on μ.")
    print("   The difference is a function of σ alone — still position-dependent!")


# ═══════════════════════════════════════════════════════════════════════
# Part 8: FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 72)
print("FINAL SUMMARY")
print("=" * 72)

print("""
1. FORGETTING CURVATURE:
   F_{12}(μ,σ; q) = 3α(μ − μ₀) / (σ₀² σ)

2. q-DEPENDENCE OF F_{12}:
   F_{12} depends on q = N(μ₀,σ₀²) through BOTH μ₀ and σ₀.
   - μ₀ determines the ZERO LOCUS (the line μ = μ₀)
   - σ₀ determines the AMPLITUDE (via 1/σ₀²)

3. q-DEPENDENCE OF ∂_k F_{12}:
   ∂_μ F_{12} = 3α / (σ₀² σ)      — depends on σ₀ (NOT on μ₀)
   ∂_σ F_{12} = −3α(μ−μ₀)/(σ₀²σ²) — depends on BOTH μ₀ and σ₀

   ⇒ ∂_k F_{12} is NOT q-independent in the naive sense.
   ⇒ However, the σ₀-dependence is a global scale (1/σ₀²),
     and ∂_μ F_{12} loses the μ₀ dependence.

4. SIGN OF F_{12}:
   sign(F_{12}) = sign(α) · sign(μ − μ₀)

   The sign IS q-dependent (through μ₀).

   Sign flip condition: For a fixed point (μ,σ), changing reference
   from q = N(μ₀,σ₀²) to q' = N(μ₀',σ₀'²) flips the sign iff
   μ₀ and μ₀' are on OPPOSITE SIDES of μ:

     (μ − μ₀)(μ − μ₀') < 0

   i.e., μ₀ < μ < μ₀'  or  μ₀' < μ < μ₀.

   σ₀ NEVER affects the sign (only the magnitude).

5. WHAT IS GENUINELY q-INDEPENDENT:
   - The zero locus topology: F_{12} = 0 is always a line μ = const
   - The gradient direction ratio at fixed μ₀:
     ∂_σ F / ∂_μ F = −(μ−μ₀)/σ  (depends on μ₀)
   - The fact that F_{12} changes sign exactly once as μ crosses μ₀
   - The functional form F_{12} ∝ (μ−μ₀)/σ (up to q-dependent scale)
   - ∂_μ² F_{12} = 0  (the curvature field is LINEAR in μ, always)
   - ∂_σ² F_{12} = 6α(μ−μ₀)/(σ₀²σ³)  (shape ∝ (μ−μ₀)/σ³)

6. PHYSICAL INTERPRETATION:
   The forgetting curvature F_{12} measures the 'twist' between
   the KL gradient and the Chebyshev torsion. Since T₁ = 0 in the
   Gaussian case, only the μ-component of the gradient contributes.

   The reference q determines WHERE on the parameter manifold the
   curvature vanishes (μ = μ₀) and HOW STRONG the curvature is
   (via 1/σ₀²). But the QUALITATIVE STRUCTURE — a single sign
   change across a hyperplane in M — is universal.
""")

# ═══════════════════════════════════════════════════════════════════════
# Part 9: Numerical sign-flip diagram
# ═══════════════════════════════════════════════════════════════════════

print("=" * 72)
print("PART 9: NUMERICAL SIGN-FLIP DIAGRAM")
print("=" * 72)

mu_range = np.linspace(-3, 5, 9)
sigma_fixed = 1.0
alpha_val = 1.0

print(f"\nσ = {sigma_fixed}, α = {alpha_val}")
print(f"\n{'μ':>6} | q=N(0,1)  q=N(2,1)  q=N(1,1)  | flip(0→2)?  flip(0→1)?")
print("-" * 72)

for mv in mu_range:
    f_01 = F12_numeric(mv, sigma_fixed, 0.0, 1.0, alpha_val)
    f_21 = F12_numeric(mv, sigma_fixed, 2.0, 1.0, alpha_val)
    f_11 = F12_numeric(mv, sigma_fixed, 1.0, 1.0, alpha_val)

    flip_02 = "YES" if np.sign(f_01) * np.sign(f_21) < 0 else "no"
    flip_01 = "YES" if np.sign(f_01) * np.sign(f_11) < 0 else "no"

    s01 = "+" if f_01 > 0 else ("-" if f_01 < 0 else "0")
    s21 = "+" if f_21 > 0 else ("-" if f_21 < 0 else "0")
    s11 = "+" if f_11 > 0 else ("-" if f_11 < 0 else "0")

    print(f"{mv:>+6.1f} | {s01:>5} {f_01:>+7.3f}  {s21:>3} {f_21:>+7.3f}  {s11:>3} {f_11:>+7.3f}  |   {flip_02:>5}        {flip_01:>5}")

print("""
Reading: For μ between 0 and 2, changing q from N(0,1) to N(2,1) flips
the sign of F_{12}. For μ between 0 and 1, changing q from N(0,1) to
N(1,1) flips the sign. This confirms the sign-flip condition:
  (μ − μ₀)(μ − μ₀') < 0  ⟺  μ lies BETWEEN μ₀ and μ₀'.
""")

print("=" * 72)
print("DONE")
print("=" * 72)
