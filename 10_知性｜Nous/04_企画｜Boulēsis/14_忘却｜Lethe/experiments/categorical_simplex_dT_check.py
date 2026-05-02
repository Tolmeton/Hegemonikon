#!/usr/bin/env python3
"""Categorical simplex Δ^n で dT = 0 を数値確認する。"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
import sympy as sp


DT_TOL = 1e-12
DET_TOL = 1e-12


@lru_cache(maxsize=None)
def build_symbolic_bundle(n: int):
    theta_symbols = sp.symbols(f"theta0:{n}", real=True)
    exp_terms = [sp.exp(symbol) for symbol in theta_symbols]
    partition = 1 + sum(exp_terms)
    probabilities = [term / partition for term in exp_terms] + [1 / partition]

    psi = sp.log(partition)
    fisher_metric = sp.hessian(psi, theta_symbols)
    log_det_metric = sp.simplify(sum(sp.log(probability) for probability in probabilities))
    chebyshev = sp.Matrix(
        [sp.simplify(sp.diff(log_det_metric, symbol)) for symbol in theta_symbols]
    )
    d_t = sp.Matrix(
        [
            [
                sp.simplify(
                    sp.diff(chebyshev[j], theta_symbols[i])
                    - sp.diff(chebyshev[i], theta_symbols[j])
                )
                for j in range(n)
            ]
            for i in range(n)
        ]
    )

    return {
        "theta_symbols": theta_symbols,
        "metric_fn": sp.lambdify(theta_symbols, fisher_metric, "numpy"),
        "probabilities_fn": sp.lambdify(theta_symbols, probabilities, "numpy"),
        "chebyshev_fn": sp.lambdify(theta_symbols, chebyshev, "numpy"),
        "d_t_fn": sp.lambdify(theta_symbols, d_t, "numpy"),
    }


def sample_thetas(n: int) -> list[np.ndarray]:
    return [
        np.zeros(n, dtype=float),
        np.linspace(-0.2, 0.3, n, dtype=float),
        np.array([(-1.0) ** idx * 0.15 * (idx + 1) / n for idx in range(n)], dtype=float),
    ]


def evaluate_case(n: int, theta: np.ndarray) -> dict[str, float | np.ndarray]:
    bundle = build_symbolic_bundle(n)
    theta_args = tuple(float(value) for value in theta)

    fisher_metric = np.asarray(bundle["metric_fn"](*theta_args), dtype=float)
    probabilities = np.asarray(bundle["probabilities_fn"](*theta_args), dtype=float).reshape(n + 1)
    chebyshev = np.asarray(bundle["chebyshev_fn"](*theta_args), dtype=float).reshape(n)
    d_t = np.asarray(bundle["d_t_fn"](*theta_args), dtype=float)

    det_metric = float(np.linalg.det(fisher_metric))
    det_product = float(np.prod(probabilities))
    det_error = abs(det_metric - det_product)
    max_abs_d_t = float(np.max(np.abs(d_t)))

    eigvals = np.linalg.eigvalsh(fisher_metric)
    if np.any(eigvals <= 0):
        raise AssertionError(f"Fisher metric is not positive definite for n={n}, theta={theta}.")

    if det_error >= DET_TOL:
        raise AssertionError(
            f"det g mismatch for n={n}, theta={theta}: {det_metric} vs {det_product}"
        )
    if max_abs_d_t >= DT_TOL:
        raise AssertionError(f"dT is not numerically zero for n={n}, theta={theta}: {max_abs_d_t}")

    return {
        "theta": theta,
        "probabilities": probabilities,
        "chebyshev": chebyshev,
        "det_metric": det_metric,
        "det_product": det_product,
        "det_error": det_error,
        "max_abs_d_t": max_abs_d_t,
    }


def main() -> None:
    print("Categorical simplex Δ^n: dT = 0 numerical check")
    print("=" * 72)
    print(f"thresholds: max|dT| < {DT_TOL:.1e}, |det g - ∏p_i| < {DET_TOL:.1e}")

    overall_max_d_t = 0.0
    for n in (2, 3, 4):
        print("\n" + "-" * 72)
        print(f"n = {n}")
        print("-" * 72)
        for case_index, theta in enumerate(sample_thetas(n), start=1):
            result = evaluate_case(n, theta)
            overall_max_d_t = max(overall_max_d_t, float(result["max_abs_d_t"]))
            theta_str = np.array2string(result["theta"], precision=4, separator=", ")
            t_str = np.array2string(result["chebyshev"], precision=6, separator=", ")
            print(f"case {case_index}: theta = {theta_str}")
            print(
                "  det g = "
                f"{result['det_metric']:.12e}, "
                f"∏p_i = {result['det_product']:.12e}, "
                f"|Δ| = {result['det_error']:.3e}"
            )
            print(f"  T = {t_str}")
            print(f"  max|dT| = {result['max_abs_d_t']:.3e}")

    print("\n" + "=" * 72)
    print(f"overall max|dT| = {overall_max_d_t:.3e}")
    print("OK: categorical simplex verifies dT = 0 for n = 2, 3, 4.")


if __name__ == "__main__":
    main()
