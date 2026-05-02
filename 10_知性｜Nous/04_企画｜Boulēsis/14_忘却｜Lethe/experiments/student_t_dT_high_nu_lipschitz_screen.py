#!/usr/bin/env python3
"""High-nu endpoint Lipschitz screen for Paper I OP-I-7.

This is a numerical bridge toward a formal interval bound.  It screens the
weakest region found by student_t_dT_interval_scaffold.py, estimates a local
Lipschitz envelope for dT(nu), and reports a conservative cell lower bound.

Important: the Lipschitz constant is empirically estimated from the same
quadrature pipeline.  This is not outward-rounded interval arithmetic and must
not be cited as a proof.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from student_t_dT_nu_sweep import DEFAULT_GAMMA, StudentTQuadrature

DEFAULT_NU_MIN = 4.5
DEFAULT_NU_MAX = 5.0
DEFAULT_GRID_SIZE = 101
DEFAULT_NODES = 1000
DEFAULT_SAFETY_FACTOR = 20.0


def run_screen(
    nu_min: float,
    nu_max: float,
    grid_size: int,
    gamma: float,
    nodes: int,
    safety_factor: float,
) -> dict[str, Any]:
    if nu_min <= 0.0 or nu_max <= nu_min:
        raise ValueError("expected 0 < nu_min < nu_max")
    if grid_size < 5:
        raise ValueError("grid_size must be >= 5")
    if safety_factor < 1.0:
        raise ValueError("safety_factor must be >= 1")

    quadrature = StudentTQuadrature(nodes)
    nu_grid = np.linspace(nu_min, nu_max, grid_size)
    rows = []
    for nu in nu_grid:
        result = quadrature.evaluate_point(float(nu), gamma)
        rows.append(
            {
                "nu": float(nu),
                "base_d_t": result["base_d_t"],
                "min_abs_d_t": result["min_abs_d_t"],
                "min_abs_d_t_over_t_norm": result["min_abs_d_t_over_t_norm"],
                "step_envelope_spread": result["step_envelope_spread"],
            }
        )

    values = np.array([row["base_d_t"] for row in rows], dtype=float)
    lower_abs_values = np.array([row["min_abs_d_t"] for row in rows], dtype=float)
    spacing = float(nu_grid[1] - nu_grid[0])
    slopes = np.abs(np.diff(values)) / spacing
    observed_lipschitz = float(np.max(slopes))
    guarded_lipschitz = safety_factor * observed_lipschitz
    cell_radius = 0.5 * spacing
    weakest_index = int(np.argmin(lower_abs_values))
    weakest = rows[weakest_index]
    guarded_cell_lower = float(weakest["min_abs_d_t"] - guarded_lipschitz * cell_radius)

    return {
        "experiment": "student_t_dT_high_nu_lipschitz_screen",
        "paper": "Paper I OP-I-7",
        "nu_interval": [nu_min, nu_max],
        "gamma": gamma,
        "grid_size": grid_size,
        "nodes": nodes,
        "spacing": spacing,
        "safety_factor": safety_factor,
        "observed_lipschitz_base_d_t": observed_lipschitz,
        "guarded_lipschitz_base_d_t": guarded_lipschitz,
        "cell_radius": cell_radius,
        "weakest_sample": weakest,
        "guarded_cell_lower_abs_d_t": guarded_cell_lower,
        "status": "PASS" if guarded_cell_lower > 0.0 and np.all(values > 0.0) else "CHECK",
        "rows": rows,
        "interpretation": (
            "This screen supports positivity near the high-nu endpoint under an empirical "
            "Lipschitz guard. It is not formal interval arithmetic because the Lipschitz "
            "constant is estimated numerically and the quadrature is not outward rounded."
        ),
    }


def markdown_report(payload: dict[str, Any]) -> str:
    weakest = payload["weakest_sample"]
    lines = [
        "# Student t dT high-nu Lipschitz screen for Paper I OP-I-7",
        "",
        f"- nu interval: `{payload['nu_interval'][0]}` to `{payload['nu_interval'][1]}`",
        f"- gamma: `{payload['gamma']}`",
        f"- grid size: `{payload['grid_size']}`",
        f"- nodes: `{payload['nodes']}`",
        f"- safety factor over observed slope: `{payload['safety_factor']}`",
        f"- status: `{payload['status']}`",
        "- proof status: numerical Lipschitz screen only; not formal interval arithmetic",
        "",
        "## Guarded Lower Bound Screen",
        "",
        "| quantity | value |",
        "|:---|---:|",
        f"| observed Lipschitz proxy for base dT | {payload['observed_lipschitz_base_d_t']:.9e} |",
        f"| guarded Lipschitz proxy | {payload['guarded_lipschitz_base_d_t']:.9e} |",
        f"| grid cell radius | {payload['cell_radius']:.9e} |",
        f"| weakest sampled nu | {weakest['nu']:.9g} |",
        f"| weakest sampled lower `|dT|` | {weakest['min_abs_d_t']:.9e} |",
        f"| guarded cell lower `|dT|` | {payload['guarded_cell_lower_abs_d_t']:.9e} |",
        "",
        "## Interpretation",
        "",
        payload["interpretation"],
        "",
        "The screen remains far from zero even after multiplying the observed slope by the safety factor. ",
        "This makes the high-nu endpoint a good first target for a real interval or analytic proof, but it does not replace that proof.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nu-min", type=float, default=DEFAULT_NU_MIN)
    parser.add_argument("--nu-max", type=float, default=DEFAULT_NU_MAX)
    parser.add_argument("--grid-size", type=int, default=DEFAULT_GRID_SIZE)
    parser.add_argument("--gamma", type=float, default=DEFAULT_GAMMA)
    parser.add_argument("--nodes", type=int, default=DEFAULT_NODES)
    parser.add_argument("--safety-factor", type=float, default=DEFAULT_SAFETY_FACTOR)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    payload = run_screen(
        args.nu_min,
        args.nu_max,
        args.grid_size,
        args.gamma,
        args.nodes,
        args.safety_factor,
    )

    print("Student t dT high-nu Lipschitz screen for Paper I OP-I-7")
    print("=" * 80)
    print(f"nu interval = [{args.nu_min}, {args.nu_max}]")
    print(f"grid size = {args.grid_size}")
    print(f"nodes = {args.nodes}")
    print(f"safety factor = {args.safety_factor}")
    print(f"status = {payload['status']}")
    print(f"observed Lipschitz proxy = {payload['observed_lipschitz_base_d_t']:.9e}")
    print(f"guarded Lipschitz proxy = {payload['guarded_lipschitz_base_d_t']:.9e}")
    print(f"weakest sampled nu = {payload['weakest_sample']['nu']:.9g}")
    print(f"weakest sampled lower |dT| = {payload['weakest_sample']['min_abs_d_t']:.9e}")
    print(f"guarded cell lower |dT| = {payload['guarded_cell_lower_abs_d_t']:.9e}")
    print("NOTE: numerical Lipschitz screen only; not formal interval arithmetic.")

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown_report(payload))


if __name__ == "__main__":
    main()
