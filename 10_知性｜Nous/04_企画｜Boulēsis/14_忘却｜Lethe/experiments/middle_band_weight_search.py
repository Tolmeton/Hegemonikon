#!/usr/bin/env python3
"""Search a better d_lethe blend for middle-band recovery.

This stays intentionally boring:
- load the existing p3b_stratification.json
- reconstruct control-flow distance from the stored baseline blend
- sweep a single scalar alpha in d = alpha * ccl + (1-alpha) * cf
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).parent
DEFAULT_INPUT_JSON = ROOT / "p3b_stratification.json"
DEFAULT_OUT_JSON = ROOT / "middle_band_weight_search.json"
DEFAULT_OUT_MD = ROOT / "middle_band_weight_search.md"
DEFAULT_TOLERANCE = 0.05
BLEND_FORMULA_RE = re.compile(
    r"^\s*(?P<ccl>[0-9]+(?:\.[0-9]+)?)\s*\*\s*ccl_normalized_distance\s*"
    r"\+\s*(?P<cf>[0-9]+(?:\.[0-9]+)?)\s*\*\s*control_flow_distance\s*$"
)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def parse_blend_weights(formula: str) -> tuple[float, float]:
    match = BLEND_FORMULA_RE.match(formula)
    if not match:
        raise ValueError(f"unsupported d_lethe_candidate_formula: {formula}")

    ccl_weight = float(match.group("ccl"))
    cf_weight = float(match.group("cf"))
    if cf_weight <= 0:
        raise ValueError("control_flow_distance weight must be positive for reconstruction")
    if abs((ccl_weight + cf_weight) - 1.0) > 1e-6:
        raise ValueError(f"blend weights must sum to 1.0: {formula}")
    return ccl_weight, cf_weight


def load_pair_rows(input_json: Path) -> tuple[dict, list[dict], dict[str, float]]:
    payload = json.loads(input_json.read_text(encoding="utf-8"))
    ccl_weight, cf_weight = parse_blend_weights(payload["d_lethe_candidate_formula"])
    band_by_id = {band["band_id"]: band for band in payload["band_edges"]}
    rows = []

    for record in payload["records"]:
        if record["distance_family"] != "d_lethe_candidate":
            continue

        ccl_distance = float(record["ccl_distance"])
        baseline_distance = float(record["distance_value"])
        cf_distance = clamp01((baseline_distance - ccl_weight * ccl_distance) / cf_weight)
        band = band_by_id[record["band_id"]]

        rows.append(
            {
                "pair_id": record["pair_id"],
                "band_id": record["band_id"],
                "pair_type": record["pair_type"],
                "lower": float(band["lower"]),
                "upper": float(band["upper"]),
                "ast_distance": float(record["ast_distance"]),
                "ccl_distance": ccl_distance,
                "cf_distance": cf_distance,
                "baseline_distance": baseline_distance,
            }
        )

    return payload, rows, {
        "ccl_weight": ccl_weight,
        "control_flow_weight": cf_weight,
    }


def blended_distance(row: dict, alpha: float) -> float:
    return alpha * row["ccl_distance"] + (1.0 - alpha) * row["cf_distance"]


def failure_mode(row: dict, distance_value: float, tolerance: float) -> str:
    lower = row["lower"]
    upper = row["upper"]

    if row["pair_type"] == "mid_structure":
        if distance_value < (lower - tolerance) or distance_value > (upper + tolerance):
            return "mid_band_blur"
        return "aligned"
    if row["pair_type"] == "near_structure" and distance_value > (upper + tolerance):
        return "near_band_false_negative"
    if row["pair_type"] == "far_structure" and distance_value < (lower - tolerance):
        return "far_band_false_positive"
    return "aligned"


def evaluate_alpha(rows: list[dict], alpha: float, tolerance: float) -> dict:
    totals = {
        "near_total": 0,
        "near_fail": 0,
        "mid_total": 0,
        "mid_fail": 0,
        "far_total": 0,
        "far_fail": 0,
        "total": 0,
        "fail": 0,
    }
    band_failures = {band_id: {"total": 0, "fail": 0} for band_id in ("B1", "B2", "B3", "B4", "B5")}

    for row in rows:
        distance_value = blended_distance(row, alpha)
        failed = failure_mode(row, distance_value, tolerance) != "aligned"

        band_bucket = band_failures[row["band_id"]]
        band_bucket["total"] += 1
        band_bucket["fail"] += int(failed)

        totals["total"] += 1
        totals["fail"] += int(failed)

        if row["pair_type"] == "near_structure":
            totals["near_total"] += 1
            totals["near_fail"] += int(failed)
        elif row["pair_type"] == "mid_structure":
            totals["mid_total"] += 1
            totals["mid_fail"] += int(failed)
        else:
            totals["far_total"] += 1
            totals["far_fail"] += int(failed)

    return {
        "alpha": round(alpha, 4),
        "formula": f"{alpha:.2f} * ccl_normalized_distance + {1.0 - alpha:.2f} * control_flow_distance",
        "near_fail_rate": round(totals["near_fail"] / totals["near_total"], 3),
        "mid_fail_rate": round(totals["mid_fail"] / totals["mid_total"], 3),
        "far_fail_rate": round(totals["far_fail"] / totals["far_total"], 3),
        "total_fail_rate": round(totals["fail"] / totals["total"], 3),
        "band_fail_rates": {
            band_id: round(bucket["fail"] / bucket["total"], 3)
            for band_id, bucket in band_failures.items()
        },
        "objective": {
            "mid_first": round(totals["mid_fail"] / totals["mid_total"], 6),
            "total_second": round(totals["fail"] / totals["total"], 6),
            "edge_third": round(
                totals["near_fail"] / totals["near_total"] + totals["far_fail"] / totals["far_total"],
                6,
            ),
        },
    }


def candidate_sort_key(result: dict, baseline_alpha: float) -> tuple[float, float, float, float]:
    return (
        result["objective"]["mid_first"],
        result["objective"]["total_second"],
        result["objective"]["edge_third"],
        abs(result["alpha"] - baseline_alpha),
    )


def build_payload(args: argparse.Namespace) -> dict:
    source_payload, rows, source_weights = load_pair_rows(args.input_json)
    baseline_alpha = (
        source_weights["ccl_weight"]
        if args.baseline_alpha is None
        else args.baseline_alpha
    )

    alphas = []
    current = args.alpha_start
    while current <= args.alpha_end + 1e-9:
        alphas.append(round(current, 10))
        current += args.alpha_step

    if not any(abs(alpha - baseline_alpha) < 1e-9 for alpha in alphas):
        alphas.append(baseline_alpha)
        alphas = sorted(alphas)

    results = [evaluate_alpha(rows, alpha, args.tolerance) for alpha in alphas]
    baseline = next(result for result in results if abs(result["alpha"] - baseline_alpha) < 1e-9)
    ranked = sorted(results, key=lambda result: candidate_sort_key(result, baseline_alpha))
    best = ranked[0]
    near_guardrail = baseline["near_fail_rate"] + args.near_guardrail_delta
    far_guardrail = baseline["far_fail_rate"] + args.far_guardrail_delta
    guardrailed_pool = [
        result for result in ranked
        if result["near_fail_rate"] <= near_guardrail
        and result["far_fail_rate"] <= far_guardrail
    ]
    guardrailed_best = guardrailed_pool[0] if guardrailed_pool else baseline

    improvement = {
        "mid_fail_rate_delta": round(best["mid_fail_rate"] - baseline["mid_fail_rate"], 3),
        "near_fail_rate_delta": round(best["near_fail_rate"] - baseline["near_fail_rate"], 3),
        "far_fail_rate_delta": round(best["far_fail_rate"] - baseline["far_fail_rate"], 3),
        "total_fail_rate_delta": round(best["total_fail_rate"] - baseline["total_fail_rate"], 3),
        "alpha_delta": round(best["alpha"] - baseline["alpha"], 3),
    }
    guardrailed_improvement = {
        "mid_fail_rate_delta": round(guardrailed_best["mid_fail_rate"] - baseline["mid_fail_rate"], 3),
        "near_fail_rate_delta": round(guardrailed_best["near_fail_rate"] - baseline["near_fail_rate"], 3),
        "far_fail_rate_delta": round(guardrailed_best["far_fail_rate"] - baseline["far_fail_rate"], 3),
        "total_fail_rate_delta": round(guardrailed_best["total_fail_rate"] - baseline["total_fail_rate"], 3),
        "alpha_delta": round(guardrailed_best["alpha"] - baseline["alpha"], 3),
    }

    return {
        "schema_version": "middle_band_weight_search.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "input_json": str(args.input_json),
            "baseline_formula": source_payload["d_lethe_candidate_formula"],
            "cf_reconstruction": (
                "control_flow_distance = clamp01((baseline_distance - "
                "source_alpha * ccl_distance) / source_control_flow_weight)"
            ),
        },
        "search_config": {
            "alpha_start": args.alpha_start,
            "alpha_end": args.alpha_end,
            "alpha_step": args.alpha_step,
            "source_baseline_alpha": source_weights["ccl_weight"],
            "source_control_flow_weight": source_weights["control_flow_weight"],
            "baseline_alpha": baseline_alpha,
            "tolerance": args.tolerance,
            "near_guardrail_delta": args.near_guardrail_delta,
            "far_guardrail_delta": args.far_guardrail_delta,
        },
        "sample": {
            "function_count": source_payload.get("function_count"),
            "pair_count": len(rows),
        },
        "baseline": baseline,
        "best": best,
        "improvement": improvement,
        "guardrailed_best": guardrailed_best,
        "guardrailed_improvement": guardrailed_improvement,
        "top_candidates": ranked[:10],
        "decision_surface": {
            "aggressive_alpha": best["alpha"],
            "aggressive_formula": best["formula"],
            "guardrailed_alpha": guardrailed_best["alpha"],
            "guardrailed_formula": guardrailed_best["formula"],
            "primary_focus": "mid_fail_rate",
            "secondary_focus": "total_fail_rate",
            "guardrail_focus": "near_far_edge_stability",
        },
    }


def render_markdown(payload: dict) -> str:
    baseline = payload["baseline"]
    best = payload["best"]
    improvement = payload["improvement"]
    guardrailed_best = payload["guardrailed_best"]
    guardrailed_improvement = payload["guardrailed_improvement"]
    top_candidates = payload["top_candidates"]

    lines = [
        "# Middle-Band Weight Search",
        "",
        "既存 `p3b_stratification.json` から `control_flow_distance` を復元し、`d_lethe_candidate` の重みを掃いて middle-band failure を最優先で下げる。",
        "",
        "## Sample",
        "",
        f"- function_count: `{payload['sample']['function_count']}`",
        f"- pair_count: `{payload['sample']['pair_count']}`",
        f"- alpha_grid: `{payload['search_config']['alpha_start']:.2f}` → `{payload['search_config']['alpha_end']:.2f}` (step `{payload['search_config']['alpha_step']:.2f}`)",
        f"- tolerance: `{payload['search_config']['tolerance']:.2f}`",
        f"- near_guardrail_delta: `{payload['search_config']['near_guardrail_delta']:.2f}`",
        f"- far_guardrail_delta: `{payload['search_config']['far_guardrail_delta']:.2f}`",
        "",
        "## Baseline vs Aggressive Best",
        "",
        "| Metric | Baseline | Best | Delta |",
        "|---|---:|---:|---:|",
        f"| alpha | {baseline['alpha']:.2f} | {best['alpha']:.2f} | {improvement['alpha_delta']:+.2f} |",
        f"| mid_fail_rate | {baseline['mid_fail_rate']:.3f} | {best['mid_fail_rate']:.3f} | {improvement['mid_fail_rate_delta']:+.3f} |",
        f"| near_fail_rate | {baseline['near_fail_rate']:.3f} | {best['near_fail_rate']:.3f} | {improvement['near_fail_rate_delta']:+.3f} |",
        f"| far_fail_rate | {baseline['far_fail_rate']:.3f} | {best['far_fail_rate']:.3f} | {improvement['far_fail_rate_delta']:+.3f} |",
        f"| total_fail_rate | {baseline['total_fail_rate']:.3f} | {best['total_fail_rate']:.3f} | {improvement['total_fail_rate_delta']:+.3f} |",
        "",
        "## Baseline vs Guardrailed Best",
        "",
        "| Metric | Baseline | Guardrailed | Delta |",
        "|---|---:|---:|---:|",
        f"| alpha | {baseline['alpha']:.2f} | {guardrailed_best['alpha']:.2f} | {guardrailed_improvement['alpha_delta']:+.2f} |",
        f"| mid_fail_rate | {baseline['mid_fail_rate']:.3f} | {guardrailed_best['mid_fail_rate']:.3f} | {guardrailed_improvement['mid_fail_rate_delta']:+.3f} |",
        f"| near_fail_rate | {baseline['near_fail_rate']:.3f} | {guardrailed_best['near_fail_rate']:.3f} | {guardrailed_improvement['near_fail_rate_delta']:+.3f} |",
        f"| far_fail_rate | {baseline['far_fail_rate']:.3f} | {guardrailed_best['far_fail_rate']:.3f} | {guardrailed_improvement['far_fail_rate_delta']:+.3f} |",
        f"| total_fail_rate | {baseline['total_fail_rate']:.3f} | {guardrailed_best['total_fail_rate']:.3f} | {guardrailed_improvement['total_fail_rate_delta']:+.3f} |",
        "",
        "## Recommendation",
        "",
        f"- aggressive_alpha: `{payload['decision_surface']['aggressive_alpha']:.2f}`",
        f"- aggressive_formula: `{payload['decision_surface']['aggressive_formula']}`",
        f"- guardrailed_alpha: `{payload['decision_surface']['guardrailed_alpha']:.2f}`",
        f"- guardrailed_formula: `{payload['decision_surface']['guardrailed_formula']}`",
        "",
        "## Top Candidates",
        "",
        "| alpha | mid | total | near | far |",
        "|---|---:|---:|---:|---:|",
    ]

    for candidate in top_candidates:
        lines.append(
            f"| {candidate['alpha']:.2f} | {candidate['mid_fail_rate']:.3f} | "
            f"{candidate['total_fail_rate']:.3f} | {candidate['near_fail_rate']:.3f} | "
            f"{candidate['far_fail_rate']:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Sources",
            "",
            f"- `{payload['sources']['input_json']}`",
            f"- baseline_formula: `{payload['sources']['baseline_formula']}`",
            f"- cf_reconstruction: `{payload['sources']['cf_reconstruction']}`",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", type=Path, default=DEFAULT_INPUT_JSON)
    parser.add_argument("--alpha-start", type=float, default=0.0)
    parser.add_argument("--alpha-end", type=float, default=1.0)
    parser.add_argument("--alpha-step", type=float, default=0.05)
    parser.add_argument("--baseline-alpha", type=float, default=None)
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    parser.add_argument("--near-guardrail-delta", type=float, default=0.05)
    parser.add_argument("--far-guardrail-delta", type=float, default=0.05)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload(args)
    args.out_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.out_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"saved: {args.out_json}")
    print(f"saved: {args.out_md}")


if __name__ == "__main__":
    main()
