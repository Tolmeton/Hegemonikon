#!/usr/bin/env python3
"""SciPy-free Student t nu sweep for Paper I OP-I-7.

This script independently retests the Student t (nu, gamma) dT witness at
nu = {1.5, 2, 3, 5}.  It uses the same Fisher / Amari-Chentsov / Chebyshev
definitions as non_exponential_dT_counterexample.py, but avoids scipy so it
can run in the bundled Codex runtime.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


DEFAULT_NU_VALUES = [1.5, 2.0, 3.0, 5.0]
DEFAULT_GAMMA = 1.0
DEFAULT_QUADRATURE_NODES = 600
COUNTEREXAMPLE_TOL = 1e-3
NU_STEPS = [5e-5, 1e-4, 2e-4, 5e-4]
GAMMA_STEP_FRACTIONS = [5e-5, 1e-4, 2e-4, 5e-4]


def digamma(x: float) -> float:
    """Approximate psi(x) for positive x using recurrence + asymptotic series."""
    if x <= 0.0:
        raise ValueError("digamma approximation expects x > 0")

    result = 0.0
    while x < 8.0:
        result -= 1.0 / x
        x += 1.0

    inv = 1.0 / x
    inv2 = inv * inv
    return (
        result
        + math.log(x)
        - 0.5 * inv
        - inv2 / 12.0
        + inv2**2 / 120.0
        - inv2**3 / 252.0
        + inv2**4 / 240.0
        - 5.0 * inv2**5 / 660.0
    )


class StudentTQuadrature:
    """Gauss-Legendre quadrature on R via y = tan(pi u / 2)."""

    def __init__(self, node_count: int) -> None:
        nodes, weights = np.polynomial.legendre.leggauss(node_count)
        self.nodes = nodes
        self.weights = weights
        self.y = np.tan(0.5 * math.pi * nodes)
        self.jacobian = 0.5 * math.pi * (1.0 + self.y * self.y)

    def base_pdf(self, nu: float) -> np.ndarray:
        y2 = self.y * self.y
        log_norm = (
            math.lgamma((nu + 1.0) / 2.0)
            - math.lgamma(nu / 2.0)
            - 0.5 * math.log(math.pi * nu)
        )
        return np.exp(log_norm - 0.5 * (nu + 1.0) * np.log1p(y2 / nu))

    def expectation(self, nu: float, values: np.ndarray) -> float:
        weighted = self.weights * values * self.base_pdf(nu) * self.jacobian
        return float(np.sum(weighted))

    def score_vector(self, nu: float, gamma: float) -> np.ndarray:
        y2 = self.y * self.y
        score_gamma = nu * (y2 - 1.0) / (gamma * (nu + y2))
        psi_term = (
            0.5 * digamma((nu + 1.0) / 2.0)
            - 0.5 * digamma(nu / 2.0)
            - 0.5 / nu
        )
        score_nu = (
            psi_term
            - 0.5 * np.log1p(y2 / nu)
            + 0.5 * (nu + 1.0) * y2 / (nu * (nu + y2))
        )
        return np.stack([score_nu, score_gamma], axis=0)

    def fisher_matrix(self, nu: float, gamma: float) -> np.ndarray:
        score = self.score_vector(nu, gamma)
        matrix = np.zeros((2, 2), dtype=float)
        for i in range(2):
            for j in range(i, 2):
                value = self.expectation(nu, score[i] * score[j])
                matrix[i, j] = matrix[j, i] = value
        return matrix

    def amari_chentsov_tensor(self, nu: float, gamma: float) -> np.ndarray:
        score = self.score_vector(nu, gamma)
        tensor = np.zeros((2, 2, 2), dtype=float)
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    tensor[i, j, k] = self.expectation(nu, score[i] * score[j] * score[k])
        return tensor

    def chebyshev_form(self, nu: float, gamma: float) -> np.ndarray:
        metric = self.fisher_matrix(nu, gamma)
        tensor = self.amari_chentsov_tensor(nu, gamma)
        return np.einsum("jk,ijk->i", np.linalg.inv(metric), tensor)

    def d_t_with_steps(
        self, nu: float, gamma: float, nu_step: float, gamma_fraction: float
    ) -> float:
        gamma_step = max(gamma_fraction * gamma, 1e-5)
        d_t_d_nu = (
            self.chebyshev_form(nu + nu_step, gamma)
            - self.chebyshev_form(nu - nu_step, gamma)
        ) / (2.0 * nu_step)
        d_t_d_gamma = (
            self.chebyshev_form(nu, gamma + gamma_step)
            - self.chebyshev_form(nu, gamma - gamma_step)
        ) / (2.0 * gamma_step)
        return float(d_t_d_nu[1] - d_t_d_gamma[0])

    def evaluate_point(self, nu: float, gamma: float) -> dict[str, Any]:
        metric = self.fisher_matrix(nu, gamma)
        chebyshev = self.chebyshev_form(nu, gamma)
        t_norm = float(np.linalg.norm(chebyshev))
        eigvals = np.linalg.eigvalsh(metric)
        if np.any(eigvals <= 0.0):
            raise AssertionError(f"Fisher metric is not positive definite at nu={nu}")

        values = np.array(
            [
                self.d_t_with_steps(nu, gamma, nu_step, gamma_fraction)
                for nu_step in NU_STEPS
                for gamma_fraction in GAMMA_STEP_FRACTIONS
            ],
            dtype=float,
        )
        ratios = np.abs(values) / max(t_norm, 1e-12)
        min_abs = float(np.min(np.abs(values)))
        min_ratio = float(np.min(ratios))
        if min_abs <= COUNTEREXAMPLE_TOL:
            raise AssertionError(f"dT lower bound too small at nu={nu}: {min_abs}")
        if min_ratio <= COUNTEREXAMPLE_TOL:
            raise AssertionError(f"|dT|/|T| lower bound too small at nu={nu}: {min_ratio}")
        if np.any(np.sign(values) != np.sign(values[0])):
            raise AssertionError(f"dT sign is not stable at nu={nu}")

        base_d_t = self.d_t_with_steps(nu, gamma, 1e-4, 1e-4)
        return {
            "nu": nu,
            "gamma": gamma,
            "fisher_metric": metric.tolist(),
            "fisher_eigenvalues": eigvals.tolist(),
            "chebyshev": chebyshev.tolist(),
            "base_d_t": base_d_t,
            "base_ratio": abs(base_d_t) / max(t_norm, 1e-12),
            "min_d_t": float(np.min(values)),
            "max_d_t": float(np.max(values)),
            "min_abs_d_t": min_abs,
            "min_abs_d_t_over_t_norm": min_ratio,
            "step_envelope_spread": float(np.max(values) - np.min(values)),
        }


def markdown_report(results: list[dict[str, Any]], node_count: int) -> str:
    lines = [
        "# Student t dT ν sweep for Paper I OP-I-7",
        "",
        f"- quadrature: Gauss-Legendre on `y = tan(pi*u/2)`, nodes = {node_count}",
        f"- gamma: {results[0]['gamma'] if results else DEFAULT_GAMMA}",
        f"- criterion: min `|dT|` and min `|dT|/|T|` both exceed `{COUNTEREXAMPLE_TOL:.1e}`",
        "- note: this checks the `(nu, gamma)` manifold; it is not the same tangent plane as the Cauchy location-scale N0 witness.",
        "",
        "| nu | T = (T_nu, T_gamma) | base dT | dT envelope | lower |dT| | lower |dT|/|T| | verdict |",
        "|:---|:---|---:|:---|---:|---:|:---|",
    ]
    for result in results:
        t_nu, t_gamma = result["chebyshev"]
        lines.append(
            "| "
            f"{result['nu']:.3g} | "
            f"({t_nu:+.6f}, {t_gamma:+.6f}) | "
            f"{result['base_d_t']:.6e} | "
            f"[{result['min_d_t']:.6e}, {result['max_d_t']:.6e}] | "
            f"{result['min_abs_d_t']:.6e} | "
            f"{result['min_abs_d_t_over_t_norm']:.6e} | "
            "PASS |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "All requested nu values remain bounded away from zero under the step envelope. "
            "This supports the N1 twist-positive bucket for the Student t `(nu, gamma)` family at gamma = 1.0.",
            "",
            "The sweep should not be read as a continuous convergence proof from N1 to the N0 Cauchy location-scale witness. "
            "The Cauchy proof in `cauchy_closed_form_chebyshev.py` concerns the `(mu, gamma)` location-scale manifold, "
            "whereas this sweep includes the `nu` direction as a parameter direction.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gamma", type=float, default=DEFAULT_GAMMA)
    parser.add_argument("--nodes", type=int, default=DEFAULT_QUADRATURE_NODES)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    quadrature = StudentTQuadrature(args.nodes)
    results = [quadrature.evaluate_point(nu, args.gamma) for nu in DEFAULT_NU_VALUES]

    print("Student t dT nu sweep for Paper I OP-I-7")
    print("=" * 80)
    print(f"gamma = {args.gamma}")
    print(f"quadrature nodes = {args.nodes}")
    print(f"nu values = {DEFAULT_NU_VALUES}")
    print(f"criterion = {COUNTEREXAMPLE_TOL:.1e}")
    for result in results:
        print("\n" + "-" * 80)
        print(f"nu = {result['nu']:.3g}, gamma = {result['gamma']}")
        print(f"T = {np.array2string(np.array(result['chebyshev']), precision=6, separator=', ')}")
        print(f"base dT = {result['base_d_t']:.9e}")
        print(f"dT envelope = [{result['min_d_t']:.9e}, {result['max_d_t']:.9e}]")
        print(f"lower |dT| = {result['min_abs_d_t']:.9e}")
        print(f"lower |dT|/|T| = {result['min_abs_d_t_over_t_norm']:.9e}")
        print(f"Fisher eigenvalues = {np.array2string(np.array(result['fisher_eigenvalues']), precision=6, separator=', ')}")

    global_lower_abs = min(result["min_abs_d_t"] for result in results)
    global_lower_ratio = min(result["min_abs_d_t_over_t_norm"] for result in results)
    print("\n" + "=" * 80)
    print(f"global lower |dT| = {global_lower_abs:.9e}")
    print(f"global lower |dT|/|T| = {global_lower_ratio:.9e}")
    print("OK: requested nu sweep supports Student t N1 twist-positive bucket.")
    print("NOTE: this is a numerical stability sweep, not formal interval arithmetic.")

    payload = {
        "experiment": "student_t_dT_nu_sweep",
        "paper": "Paper I OP-I-7",
        "gamma": args.gamma,
        "quadrature": {
            "method": "Gauss-Legendre on y = tan(pi*u/2)",
            "nodes": args.nodes,
        },
        "nu_values": DEFAULT_NU_VALUES,
        "counterexample_tol": COUNTEREXAMPLE_TOL,
        "nu_steps": NU_STEPS,
        "gamma_step_fractions": GAMMA_STEP_FRACTIONS,
        "results": results,
        "interpretation": (
            "All requested nu values remain bounded away from zero on the "
            "(nu, gamma) Student t manifold at gamma=1.0. This is not the same "
            "tangent plane as the Cauchy location-scale N0 witness."
        ),
    }
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown_report(results, args.nodes))


if __name__ == "__main__":
    main()
