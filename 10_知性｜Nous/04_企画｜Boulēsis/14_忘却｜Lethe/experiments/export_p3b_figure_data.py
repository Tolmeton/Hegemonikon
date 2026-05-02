#!/usr/bin/env python3
"""p3b_stratification.json から paper-facing figure data を抽出する。"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).parent
INPUT = ROOT / "p3b_stratification.json"
OUTPUT = ROOT / "p3b_figure_data.json"
FAMILIES = ("cosine_49d", "ccl_string", "d_lethe_candidate")
BANDS = ("B1", "B2", "B3", "B4", "B5")
FAILURE_PRIORITY_BY_FAMILY = {
    "cosine_49d": (
        "far_band_false_positive",
        "mid_band_blur",
        "aligned",
    ),
    "ccl_string": (
        "near_band_false_negative",
        "mid_band_blur",
        "aligned",
    ),
    "d_lethe_candidate": (
        "mid_band_blur",
        "near_band_false_negative",
        "aligned",
    ),
}


def first_example(records: list[dict], family: str, failure_mode: str) -> dict | None:
    candidates = [
        r for r in records
        if r["distance_family"] == family and r["failure_mode"] == failure_mode
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda r: (r["band_id"], r["pair_id"]))
    r = candidates[0]
    return {
        "pair_id": r["pair_id"],
        "band_id": r["band_id"],
        "func_a": r["func_a"],
        "func_b": r["func_b"],
        "distance_value": r["distance_value"],
        "failure_mode": r["failure_mode"],
    }


def main() -> None:
    with open(INPUT, encoding="utf-8") as f:
        payload = json.load(f)

    records: list[dict] = payload["records"]
    band_counts = Counter(r["band_id"] for r in records if r["distance_family"] == "cosine_49d")

    band_mean_distances: dict[str, dict[str, float | None]] = {}
    failure_counts: dict[str, dict[str, int]] = {}
    representative_examples: dict[str, dict] = {}

    for family in FAMILIES:
        band_mean_distances[family] = {}
        failure_counts[family] = dict(
            Counter(r["failure_mode"] for r in records if r["distance_family"] == family)
        )

        for band in BANDS:
            vals = [
                r["distance_value"]
                for r in records
                if r["distance_family"] == family
                and r["band_id"] == band
                and r["distance_value"] is not None
            ]
            band_mean_distances[family][band] = (
                round(sum(vals) / len(vals), 6) if vals else None
            )

        for failure_mode in FAILURE_PRIORITY_BY_FAMILY[family]:
            example = first_example(records, family, failure_mode)
            if example is not None:
                representative_examples[family] = example
                break

    out = {
        "schema_version": "p3b_figure_data.v1",
        "generated_at": payload["generated_at"],
        "source_json": str(INPUT),
        "function_count": payload.get("function_count"),
        "pair_count": payload.get("pair_count"),
        "cosine_49d_meta": payload.get("cosine_49d_meta", {}),
        "band_counts": {band: band_counts.get(band, 0) for band in BANDS},
        "band_mean_distances": band_mean_distances,
        "failure_counts": failure_counts,
        "representative_examples": representative_examples,
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"saved: {OUTPUT}")


if __name__ == "__main__":
    main()
