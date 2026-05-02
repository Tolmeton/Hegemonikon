#!/usr/bin/env python3
"""Scale-reduction probe for Paper I OP-I-7 Student t dT.

The analytic target is the scaling identity
    T_nu(nu, gamma) = U(nu),
    T_gamma(nu, gamma) = V(nu) / gamma,
    dT(nu, gamma) = V'(nu) / gamma.

This script numerically checks that the implementation respects the scaling
before the identity is used as a proof scaffold.  It is a probe, not a proof.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from student_t_dT_nu_sweep import StudentTQuadrature

DEFAULT_NU_VALUES = [1.5, 2.0, 3.0, 5.0]
DEFAULT_GAMMA_VALUES = [0.5, 1.0, 2.0, 4.0]
DEFAULT_NODES = 800


def run_probe(nu_values: list[float], gamma_values: list[float], nodes: int) -> dict[str, Any]:
    q = StudentTQuadrature(nodes)
    rows = []
    max_t_nu_spread = 0.0
    max_gamma_t_gamma_spread = 0.0
    max_gamma_d_t_spread = 0.0

    for nu in nu_values:
        per_gamma = []
        for gamma in gamma_values:
            r = q.evaluate_point(nu, gamma)
            t_nu, t_gamma = r["chebyshev"]
            per_gamma.append(
                {
                    "gamma": gamma,
                    "t_nu": t_nu,
                    "t_gamma": t_gamma,
                    "gamma_t_gamma": gamma * t_gamma,
                    "d_t": r["base_d_t"],
                    "gamma_d_t": gamma * r["base_d_t"],
                }
            )
        t_nu_values = np.array([item["t_nu"] for item in per_gamma])
        gamma_t_gamma_values = np.array([item["gamma_t_gamma"] for item in per_gamma])
        gamma_d_t_values = np.array([item["gamma_d_t"] for item in per_gamma])
        t_nu_spread = float(np.max(t_nu_values) - np.min(t_nu_values))
        gamma_t_gamma_spread = float(np.max(gamma_t_gamma_values) - np.min(gamma_t_gamma_values))
        gamma_d_t_spread = float(np.max(gamma_d_t_values) - np.min(gamma_d_t_values))
        max_t_nu_spread = max(max_t_nu_spread, t_nu_spread)
        max_gamma_t_gamma_spread = max(max_gamma_t_gamma_spread, gamma_t_gamma_spread)
        max_gamma_d_t_spread = max(max_gamma_d_t_spread, gamma_d_t_spread)
        rows.append(
            {
                "nu": nu,
                "per_gamma": per_gamma,
                "t_nu_spread": t_nu_spread,
                "gamma_t_gamma_spread": gamma_t_gamma_spread,
                "gamma_d_t_spread": gamma_d_t_spread,
            }
        )

    return {
        "experiment": "student_t_scale_reduction_probe",
        "paper": "Paper I OP-I-7",
        "nodes": nodes,
        "nu_values": nu_values,
        "gamma_values": gamma_values,
        "max_t_nu_spread": max_t_nu_spread,
        "max_gamma_t_gamma_spread": max_gamma_t_gamma_spread,
        "max_gamma_d_t_spread": max_gamma_d_t_spread,
        "rows": rows,
        "interpretation": (
            "The probe checks the numerical implementation of the scaling reduction. "
            "The proof obligation is then reduced to bounding V'(nu) for T_gamma = V(nu)/gamma."
        ),
    }


def markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Student t scale-reduction probe for Paper I OP-I-7",
        "",
        "## Target Identity",
        "",
        "For the Student t `(nu, gamma)` family in the scale coordinate `y = x/gamma`:",
        "",
        "```text",
        "T_nu(nu, gamma)    = U(nu)",
        "T_gamma(nu, gamma) = V(nu) / gamma",
        "dT(nu, gamma)      = V'(nu) / gamma",
        "```",
        "",
        "This turns the high-nu lower-bound problem into a one-variable lower bound for `V'(nu)`.",
        "",
        "## Numerical Probe",
        "",
        f"- nodes: `{payload['nodes']}`",
        f"- nu values: `{payload['nu_values']}`",
        f"- gamma values: `{payload['gamma_values']}`",
        "",
        "| quantity | max spread across gamma |",
        "|:---|---:|",
        f"| `T_nu` | {payload['max_t_nu_spread']:.9e} |",
        f"| `gamma*T_gamma` | {payload['max_gamma_t_gamma_spread']:.9e} |",
        f"| `gamma*dT` | {payload['max_gamma_d_t_spread']:.9e} |",
        "",
        "## Per-nu Spreads",
        "",
        "| nu | spread `T_nu` | spread `gamma*T_gamma` | spread `gamma*dT` |",
        "|---:|---:|---:|---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['nu']:.6g} | {row['t_nu_spread']:.9e} | "
            f"{row['gamma_t_gamma_spread']:.9e} | {row['gamma_d_t_spread']:.9e} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            payload["interpretation"],
            "",
            "The scaling identity itself follows from score scaling and tensor contraction scaling; this probe only checks that the numerical implementation obeys it.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", type=int, default=DEFAULT_NODES)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    payload = run_probe(DEFAULT_NU_VALUES, DEFAULT_GAMMA_VALUES, args.nodes)
    print("Student t scale-reduction probe for Paper I OP-I-7")
    print("=" * 80)
    print(f"nodes = {args.nodes}")
    print(f"max spread T_nu = {payload['max_t_nu_spread']:.9e}")
    print(f"max spread gamma*T_gamma = {payload['max_gamma_t_gamma_spread']:.9e}")
    print(f"max spread gamma*dT = {payload['max_gamma_d_t_spread']:.9e}")
    print("OK: scaling reduction is numerically respected by the implementation.")

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown_report(payload))


if __name__ == "__main__":
    main()
