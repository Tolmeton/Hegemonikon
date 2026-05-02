#!/usr/bin/env python3
"""Student t dT lower-bound envelope for OP-I-7.

This is a numerical stability certificate for the existing
non_exponential_dT_counterexample.py pipeline.  It does not claim formal
interval arithmetic.  It checks that the Student t dT witness remains
bounded away from zero across several central-difference step sizes.
"""

from __future__ import annotations

import numpy as np

from non_exponential_dT_counterexample import (
    COUNTEREXAMPLE_TOL,
    chebyshev_form,
    evaluate_point,
)


TEST_POINTS = [
    (3.0, 1.0),
    (5.0, 2.0),
    (10.0, 0.5),
]

NU_STEPS = [5e-5, 1e-4, 2e-4, 5e-4]
GAMMA_STEP_FRACTIONS = [5e-5, 1e-4, 2e-4, 5e-4]


def d_t_with_steps(nu: float, gamma: float, nu_step: float, gamma_fraction: float) -> float:
    gamma_step = max(gamma_fraction * gamma, 1e-5)
    d_t_d_nu = (chebyshev_form(nu + nu_step, gamma) - chebyshev_form(nu - nu_step, gamma)) / (
        2.0 * nu_step
    )
    d_t_d_gamma = (
        chebyshev_form(nu, gamma + gamma_step) - chebyshev_form(nu, gamma - gamma_step)
    ) / (2.0 * gamma_step)
    return float(d_t_d_nu[1] - d_t_d_gamma[0])


def interval_for_point(nu: float, gamma: float) -> dict[str, float]:
    base = evaluate_point(nu, gamma)
    t_norm = float(np.linalg.norm(base["chebyshev"]))
    values = np.array(
        [
            d_t_with_steps(nu, gamma, nu_step, gamma_fraction)
            for nu_step in NU_STEPS
            for gamma_fraction in GAMMA_STEP_FRACTIONS
        ],
        dtype=float,
    )
    ratios = np.abs(values) / max(t_norm, 1e-12)

    min_abs = float(np.min(np.abs(values)))
    min_ratio = float(np.min(ratios))
    if min_abs <= COUNTEREXAMPLE_TOL:
        raise AssertionError(f"dT lower bound too small at (nu, gamma)=({nu}, {gamma}): {min_abs}")
    if min_ratio <= COUNTEREXAMPLE_TOL:
        raise AssertionError(
            f"|dT|/|T| lower bound too small at (nu, gamma)=({nu}, {gamma}): {min_ratio}"
        )
    if np.any(np.sign(values) != np.sign(values[0])):
        raise AssertionError(f"dT sign is not stable at (nu, gamma)=({nu}, {gamma})")

    return {
        "base_d_t": float(base["d_t"]),
        "base_ratio": float(base["ratio"]),
        "min_d_t": float(np.min(values)),
        "max_d_t": float(np.max(values)),
        "min_abs_d_t": min_abs,
        "min_ratio": min_ratio,
        "spread": float(np.max(values) - np.min(values)),
    }


def main() -> None:
    print("Student t dT finite-difference stability envelope")
    print("=" * 80)
    print(
        "criterion: min |dT| > "
        f"{COUNTEREXAMPLE_TOL:.1e} and min |dT|/|T| > {COUNTEREXAMPLE_TOL:.1e}"
    )
    print(f"nu steps: {NU_STEPS}")
    print(f"gamma step fractions: {GAMMA_STEP_FRACTIONS}")

    global_min_abs = float("inf")
    global_min_ratio = float("inf")
    for nu, gamma in TEST_POINTS:
        interval = interval_for_point(nu, gamma)
        global_min_abs = min(global_min_abs, interval["min_abs_d_t"])
        global_min_ratio = min(global_min_ratio, interval["min_ratio"])
        print("\n" + "-" * 80)
        print(f"(nu, gamma) = ({nu}, {gamma})")
        print(f"base dT = {interval['base_d_t']:.9e}")
        print(f"dT envelope = [{interval['min_d_t']:.9e}, {interval['max_d_t']:.9e}]")
        print(f"envelope spread = {interval['spread']:.3e}")
        print(f"lower |dT| = {interval['min_abs_d_t']:.9e}")
        print(f"lower |dT|/|T| = {interval['min_ratio']:.9e}")

    print("\n" + "=" * 80)
    print(f"global lower |dT| = {global_min_abs:.9e}")
    print(f"global lower |dT|/|T| = {global_min_ratio:.9e}")
    print("OK: Student t dT remains bounded away from zero across the step envelope.")
    print("NOTE: this is a finite-difference stability bound, not formal interval arithmetic.")


if __name__ == "__main__":
    main()
