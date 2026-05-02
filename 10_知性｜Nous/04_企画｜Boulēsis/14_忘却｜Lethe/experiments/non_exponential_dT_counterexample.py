#!/usr/bin/env python3
"""非指数型分布族の dT != 0 を Student t 族で示す。"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from scipy import integrate, special


ABS_TOL = 1e-10
REL_TOL = 1e-10
DERIVATIVE_STEP_NU = 1e-4
DERIVATIVE_STEP_GAMMA_FRACTION = 1e-4
COUNTEREXAMPLE_TOL = 1e-3


def student_t_base_pdf(y: float, nu: float) -> float:
    return float(
        np.exp(
            special.gammaln((nu + 1.0) / 2.0)
            - special.gammaln(nu / 2.0)
            - 0.5 * np.log(np.pi * nu)
            - 0.5 * (nu + 1.0) * np.log1p((y * y) / nu)
        )
    )


def score_vector(y: float, nu: float, gamma: float) -> np.ndarray:
    y2 = y * y
    score_gamma = nu * (y2 - 1.0) / (gamma * (nu + y2))
    score_nu = (
        0.5 * special.digamma((nu + 1.0) / 2.0)
        - 0.5 * special.digamma(nu / 2.0)
        - 0.5 / nu
        - 0.5 * np.log1p(y2 / nu)
        + 0.5 * (nu + 1.0) * y2 / (nu * (nu + y2))
    )
    return np.array([score_nu, score_gamma], dtype=float)


def expectation(nu: float, integrand) -> float:
    def wrapped(y: float) -> float:
        return float(integrand(y) * student_t_base_pdf(y, nu))

    value, _ = integrate.quad(
        wrapped,
        -np.inf,
        np.inf,
        limit=300,
        epsabs=ABS_TOL,
        epsrel=REL_TOL,
    )
    return float(value)


@lru_cache(maxsize=None)
def fisher_matrix_cached(nu: float, gamma: float) -> tuple[float, ...]:
    matrix = np.zeros((2, 2), dtype=float)
    for i in range(2):
        for j in range(i, 2):
            value = expectation(
                nu,
                lambda y, i=i, j=j: score_vector(y, nu, gamma)[i]
                * score_vector(y, nu, gamma)[j],
            )
            matrix[i, j] = matrix[j, i] = value
    return tuple(matrix.ravel())


@lru_cache(maxsize=None)
def amari_tensor_cached(nu: float, gamma: float) -> tuple[float, ...]:
    tensor = np.zeros((2, 2, 2), dtype=float)
    for i in range(2):
        for j in range(i, 2):
            for k in range(j, 2):
                value = expectation(
                    nu,
                    lambda y, i=i, j=j, k=k: np.prod(score_vector(y, nu, gamma)[[i, j, k]]),
                )
                for a, b, c in {
                    (i, j, k),
                    (i, k, j),
                    (j, i, k),
                    (j, k, i),
                    (k, i, j),
                    (k, j, i),
                }:
                    tensor[a, b, c] = value
    return tuple(tensor.ravel())


def fisher_matrix(nu: float, gamma: float) -> np.ndarray:
    return np.array(fisher_matrix_cached(float(nu), float(gamma)), dtype=float).reshape(2, 2)


def amari_chentsov_tensor(nu: float, gamma: float) -> np.ndarray:
    return np.array(amari_tensor_cached(float(nu), float(gamma)), dtype=float).reshape(2, 2, 2)


def chebyshev_form(nu: float, gamma: float) -> np.ndarray:
    metric = fisher_matrix(nu, gamma)
    tensor = amari_chentsov_tensor(nu, gamma)
    return np.einsum("jk,ijk->i", np.linalg.inv(metric), tensor)


def d_t_scalar(nu: float, gamma: float) -> tuple[float, np.ndarray, np.ndarray]:
    gamma_step = max(DERIVATIVE_STEP_GAMMA_FRACTION * gamma, 1e-5)

    d_t_d_nu = (
        chebyshev_form(nu + DERIVATIVE_STEP_NU, gamma)
        - chebyshev_form(nu - DERIVATIVE_STEP_NU, gamma)
    ) / (2.0 * DERIVATIVE_STEP_NU)
    d_t_d_gamma = (
        chebyshev_form(nu, gamma + gamma_step)
        - chebyshev_form(nu, gamma - gamma_step)
    ) / (2.0 * gamma_step)

    return float(d_t_d_nu[1] - d_t_d_gamma[0]), d_t_d_nu, d_t_d_gamma


def evaluate_point(nu: float, gamma: float) -> dict[str, float | np.ndarray]:
    metric = fisher_matrix(nu, gamma)
    chebyshev = chebyshev_form(nu, gamma)
    d_t, d_t_d_nu, d_t_d_gamma = d_t_scalar(nu, gamma)
    ratio = abs(d_t) / max(np.linalg.norm(chebyshev), 1e-12)
    eigvals = np.linalg.eigvalsh(metric)

    if np.any(eigvals <= 0):
        raise AssertionError(f"Fisher metric is not positive definite at (nu, gamma)=({nu}, {gamma})")
    if abs(d_t) <= COUNTEREXAMPLE_TOL:
        raise AssertionError(f"dT is too small at (nu, gamma)=({nu}, {gamma}): {d_t}")
    if ratio <= COUNTEREXAMPLE_TOL:
        raise AssertionError(
            f"|dT|/|T| is too small at (nu, gamma)=({nu}, {gamma}): {ratio}"
        )

    return {
        "metric": metric,
        "chebyshev": chebyshev,
        "d_t": d_t,
        "ratio": ratio,
        "d_t_d_nu": d_t_d_nu,
        "d_t_d_gamma": d_t_d_gamma,
    }


def main() -> None:
    test_points = [
        (3.0, 1.0),
        (5.0, 2.0),
        (10.0, 0.5),
    ]

    print("Non-exponential counterexample: Student t(nu, gamma)")
    print("=" * 72)
    print(
        "criterion: |dT| > "
        f"{COUNTEREXAMPLE_TOL:.1e} and |dT| / |T| > {COUNTEREXAMPLE_TOL:.1e}"
    )

    for nu, gamma in test_points:
        result = evaluate_point(nu, gamma)
        t_str = np.array2string(result["chebyshev"], precision=6, separator=", ")
        print("\n" + "-" * 72)
        print(f"(nu, gamma) = ({nu}, {gamma})")
        print("Fisher metric:")
        print(np.array2string(result["metric"], precision=6, separator=", "))
        print(f"T = {t_str}")
        print(f"∂_nu T = {np.array2string(result['d_t_d_nu'], precision=6, separator=', ')}")
        print(
            f"∂_gamma T = "
            f"{np.array2string(result['d_t_d_gamma'], precision=6, separator=', ')}"
        )
        print(f"dT = ∂_nu T_gamma - ∂_gamma T_nu = {result['d_t']:.6e}")
        print(f"|dT| / |T| = {result['ratio']:.6e}")

    print("\n" + "=" * 72)
    print("OK: Student t family gives a non-trivial dT != 0 counterexample.")


if __name__ == "__main__":
    main()
