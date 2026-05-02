#!/usr/bin/env python3
"""Closed-form Cauchy location-scale Chebyshev calculation for OP-I-7.

Parameter order is (mu, gamma).  The script keeps every integral as an exact
rational multiple of pi, then verifies that the Amari-Chentsov tensor vanishes.
"""

from __future__ import annotations

from fractions import Fraction
from math import factorial


def gamma_half_coefficient(k: int) -> Fraction:
    """Return Gamma(k + 1/2) / sqrt(pi) for integer k >= 0."""
    if k < 0:
        raise ValueError("k must be non-negative")
    return Fraction(factorial(2 * k), (4**k) * factorial(k))


def even_integral_coefficient(power_half: int, denominator_power: int) -> Fraction:
    """Return c where int_R y^(2m)/(1+y^2)^n dy = c*pi."""
    m = power_half
    n = denominator_power
    if n <= m:
        raise ValueError("integral does not converge")
    return gamma_half_coefficient(m) * gamma_half_coefficient(n - m - 1) / factorial(n - 1)


def main() -> None:
    i_1_3 = even_integral_coefficient(1, 3)
    i_0_3 = even_integral_coefficient(0, 3)
    i_2_3 = even_integral_coefficient(2, 3)

    # Scores:
    # s_mu = 2y / (gamma(1+y^2))
    # s_gamma = (y^2 - 1) / (gamma(1+y^2))
    g_mu_mu = 4 * i_1_3
    g_gamma_gamma = i_2_3 - 2 * i_1_3 + i_0_3
    g_mu_gamma = Fraction(0)

    i_0_4 = even_integral_coefficient(0, 4)
    i_1_4 = even_integral_coefficient(1, 4)
    i_2_4 = even_integral_coefficient(2, 4)
    i_3_4 = even_integral_coefficient(3, 4)

    c_mu_mu_mu = Fraction(0)  # odd integrand
    c_mu_mu_gamma = 4 * (i_2_4 - i_1_4)
    c_mu_gamma_gamma = Fraction(0)  # odd integrand
    c_gamma_gamma_gamma = i_3_4 - 3 * i_2_4 + 3 * i_1_4 - i_0_4

    expected_metric = Fraction(1, 2)
    if (g_mu_mu, g_gamma_gamma, g_mu_gamma) != (expected_metric, expected_metric, Fraction(0)):
        raise AssertionError("unexpected Fisher metric coefficients")

    tensor_coefficients = [
        c_mu_mu_mu,
        c_mu_mu_gamma,
        c_mu_gamma_gamma,
        c_gamma_gamma_gamma,
    ]
    if any(value != 0 for value in tensor_coefficients):
        raise AssertionError(f"Amari-Chentsov tensor did not vanish: {tensor_coefficients}")

    print("Cauchy location-scale closed-form Chebyshev calculation")
    print("=" * 72)
    print("parameter order: (mu, gamma)")
    print("density coordinate: y = (x - mu) / gamma")
    print("scores:")
    print("  s_mu = 2y / (gamma(1+y^2))")
    print("  s_gamma = (y^2 - 1) / (gamma(1+y^2))")
    print()
    print("Fisher metric:")
    print(f"  g_mu_mu = {g_mu_mu} / gamma^2")
    print(f"  g_mu_gamma = {g_mu_gamma} / gamma^2")
    print(f"  g_gamma_gamma = {g_gamma_gamma} / gamma^2")
    print()
    print("Amari-Chentsov tensor coefficients, scaled by gamma^3:")
    print(f"  C_mu_mu_mu = {c_mu_mu_mu}")
    print(f"  C_mu_mu_gamma = 4*(pi/16 - pi/16)/pi = {c_mu_mu_gamma}")
    print(f"  C_mu_gamma_gamma = {c_mu_gamma_gamma}")
    print(
        "  C_gamma_gamma_gamma = "
        f"(5pi/16 - 3pi/16 + 3pi/16 - 5pi/16)/pi = {c_gamma_gamma_gamma}"
    )
    print()
    print("T_i = g^{jk} C_ijk = 0")
    print("dT = 0")
    print("OK: Cauchy is an exact twist-dull non-exponential witness.")


if __name__ == "__main__":
    main()
