#!/usr/bin/env python3
"""Numerical interval scaffold for Paper I OP-I-7 Student t dT.

This script extends student_t_dT_nu_sweep.py from the four requested points to
a grid on nu in [1.5, 5.0].  It is intentionally labelled a scaffold: it is a
node/step/grid stability screen, not formal interval arithmetic.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from student_t_dT_nu_sweep import DEFAULT_GAMMA, StudentTQuadrature, markdown_report

DEFAULT_NU_MIN = 1.5
DEFAULT_NU_MAX = 5.0
DEFAULT_GRID_SIZE = 36
DEFAULT_NODE_COUNTS = [400, 600]
DEFAULT_OUTPUT_STEM = "student_t_dT_interval_scaffold_2026-05-01"


def parse_node_counts(raw: str) -> list[int]:
    values = [int(part.strip()) for part in raw.split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("at least one node count is required")
    if any(value < 50 for value in values):
        raise argparse.ArgumentTypeError("node counts below 50 are too coarse for this scaffold")
    return values


def run_grid(
    nu_min: float,
    nu_max: float,
    grid_size: int,
    gamma: float,
    node_counts: list[int],
) -> dict[str, Any]:
    if nu_min <= 0.0 or nu_max <= nu_min:
        raise ValueError("expected 0 < nu_min < nu_max")
    if grid_size < 3:
        raise ValueError("grid_size must be >= 3")

    nu_grid = np.linspace(nu_min, nu_max, grid_size)
    rows: list[dict[str, Any]] = []
    for nodes in node_counts:
        quadrature = StudentTQuadrature(nodes)
        for nu in nu_grid:
            result = quadrature.evaluate_point(float(nu), gamma)
            result["nodes"] = nodes
            rows.append(result)

    lower_abs = min(row["min_abs_d_t"] for row in rows)
    lower_ratio = min(row["min_abs_d_t_over_t_norm"] for row in rows)
    weakest_abs = min(rows, key=lambda row: row["min_abs_d_t"])
    weakest_ratio = min(rows, key=lambda row: row["min_abs_d_t_over_t_norm"])

    signs = {1 if row["base_d_t"] > 0 else -1 if row["base_d_t"] < 0 else 0 for row in rows}
    node_spreads: list[dict[str, Any]] = []
    for nu in nu_grid:
        at_nu = [row for row in rows if abs(row["nu"] - float(nu)) < 1e-12]
        base_values = [row["base_d_t"] for row in at_nu]
        abs_values = [row["min_abs_d_t"] for row in at_nu]
        node_spreads.append(
            {
                "nu": float(nu),
                "base_d_t_min": min(base_values),
                "base_d_t_max": max(base_values),
                "min_abs_d_t_min": min(abs_values),
                "min_abs_d_t_max": max(abs_values),
                "node_spread_base_d_t": max(base_values) - min(base_values),
            }
        )

    return {
        "experiment": "student_t_dT_interval_scaffold",
        "paper": "Paper I OP-I-7",
        "nu_interval": [nu_min, nu_max],
        "grid_size": grid_size,
        "gamma": gamma,
        "node_counts": node_counts,
        "status": "PASS" if signs == {1} and lower_abs > 0.0 and lower_ratio > 0.0 else "CHECK",
        "global_lower_abs_d_t_on_grid": lower_abs,
        "global_lower_abs_d_t_over_t_norm_on_grid": lower_ratio,
        "weakest_abs_point": weakest_abs,
        "weakest_ratio_point": weakest_ratio,
        "node_spreads": node_spreads,
        "rows": rows,
        "interpretation": (
            "Grid/node/step stability scaffold over nu in [1.5, 5.0]. "
            "This is not formal interval arithmetic and must not be cited as a proof. "
            "It identifies the weakest sampled region for later interval or analytic bounding."
        ),
    }


def markdown_interval_report(payload: dict[str, Any]) -> str:
    weakest_abs = payload["weakest_abs_point"]
    weakest_ratio = payload["weakest_ratio_point"]
    lines = [
        "# Student t dT interval scaffold for Paper I OP-I-7",
        "",
        f"- nu interval: `{payload['nu_interval'][0]}` to `{payload['nu_interval'][1]}`",
        f"- gamma: `{payload['gamma']}`",
        f"- grid size: `{payload['grid_size']}`",
        f"- quadrature nodes: `{payload['node_counts']}`",
        "- status: `{}`".format(payload["status"]),
        "- proof status: numerical scaffold only; not formal interval arithmetic",
        "",
        "## Global Screen",
        "",
        "| quantity | value | where | nodes |",
        "|:---|---:|:---|---:|",
        "| lower `|dT|` on grid | {:.9e} | nu = {:.9g} | {} |".format(
            payload["global_lower_abs_d_t_on_grid"], weakest_abs["nu"], weakest_abs["nodes"]
        ),
        "| lower `|dT|/||T||` on grid | {:.9e} | nu = {:.9g} | {} |".format(
            payload["global_lower_abs_d_t_over_t_norm_on_grid"],
            weakest_ratio["nu"],
            weakest_ratio["nodes"],
        ),
        "",
        "## Weakest Sampled Points",
        "",
        "| criterion | nu | nodes | base dT | lower |dT| | lower |dT|/||T|| |",
        "|:---|---:|---:|---:|---:|---:|",
        "| lower abs | {:.9g} | {} | {:.9e} | {:.9e} | {:.9e} |".format(
            weakest_abs["nu"],
            weakest_abs["nodes"],
            weakest_abs["base_d_t"],
            weakest_abs["min_abs_d_t"],
            weakest_abs["min_abs_d_t_over_t_norm"],
        ),
        "| lower ratio | {:.9g} | {} | {:.9e} | {:.9e} | {:.9e} |".format(
            weakest_ratio["nu"],
            weakest_ratio["nodes"],
            weakest_ratio["base_d_t"],
            weakest_ratio["min_abs_d_t"],
            weakest_ratio["min_abs_d_t_over_t_norm"],
        ),
        "",
        "## Interpretation",
        "",
        payload["interpretation"],
        "",
        "The useful next target is the high-nu end of the interval, because both `|dT|` and `|dT|/||T||` are weakest there. ",
        "A formal upgrade should bound that endpoint region first, then extend leftward.",
        "",
        "## Four-point sweep comparison",
        "",
        markdown_report([row for row in payload["rows"] if row["nodes"] == max(payload["node_counts"]) and row["nu"] in {1.5, 2.0, 3.0, 5.0}], max(payload["node_counts"])),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nu-min", type=float, default=DEFAULT_NU_MIN)
    parser.add_argument("--nu-max", type=float, default=DEFAULT_NU_MAX)
    parser.add_argument("--grid-size", type=int, default=DEFAULT_GRID_SIZE)
    parser.add_argument("--gamma", type=float, default=DEFAULT_GAMMA)
    parser.add_argument("--nodes", type=parse_node_counts, default=DEFAULT_NODE_COUNTS)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    payload = run_grid(args.nu_min, args.nu_max, args.grid_size, args.gamma, args.nodes)

    print("Student t dT interval scaffold for Paper I OP-I-7")
    print("=" * 80)
    print(f"nu interval = [{args.nu_min}, {args.nu_max}]")
    print(f"grid size = {args.grid_size}")
    print(f"gamma = {args.gamma}")
    print(f"nodes = {args.nodes}")
    print(f"status = {payload['status']}")
    print(f"global lower |dT| on grid = {payload['global_lower_abs_d_t_on_grid']:.9e}")
    print(
        "global lower |dT|/|T| on grid = "
        f"{payload['global_lower_abs_d_t_over_t_norm_on_grid']:.9e}"
    )
    print(
        "weakest abs point = "
        f"nu {payload['weakest_abs_point']['nu']:.9g}, "
        f"nodes {payload['weakest_abs_point']['nodes']}"
    )
    print("NOTE: numerical scaffold only; not formal interval arithmetic.")

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown_interval_report(payload))


if __name__ == "__main__":
    main()
