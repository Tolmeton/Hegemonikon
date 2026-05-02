#!/usr/bin/env python3
"""Build a reproducible Lethe access-path scorecard from canonical records.

The scorecard intentionally stays thin:
- source of truth for headline hierarchy metrics: EXPERIMENTS.md
- source of truth for structure sensitivity: ablation_results.json
- source of truth for middle-band failure geometry: p3b_stratification.json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent
DEFAULT_EXPERIMENTS_MD = SCRIPT_DIR.parent / "EXPERIMENTS.md"
DEFAULT_ABLATION_JSON = SCRIPT_DIR / "ablation_results.json"
DEFAULT_STRATIFICATION_JSON = SCRIPT_DIR / "p3b_stratification.json"
DEFAULT_OUTPUT_JSON = SCRIPT_DIR / "access_path_scorecard.json"
DEFAULT_OUTPUT_MD = SCRIPT_DIR / "access_path_scorecard.md"


@dataclass(frozen=True)
class HeadlineMetric:
    label: str
    value: float


def _extract_float(pattern: str, text: str, label: str) -> float:
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"missing canonical metric: {label}")
    return float(match.group("value"))


def extract_headline_metrics(experiments_md: Path) -> dict[str, HeadlineMetric]:
    text = experiments_md.read_text(encoding="utf-8")
    return {
        "codebert_single_partial_rho": HeadlineMetric(
            label="CodeBERT single-vector partial rho",
            value=_extract_float(
                r"\| CodeBERT \(125M\) \| [^|]+ \| \*\*(?P<value>0\.\d+)\*\* \(L6\) \|",
                text,
                "codebert single",
            ),
        ),
        "codellama_single_partial_rho": HeadlineMetric(
            label="CodeLlama single-vector partial rho",
            value=_extract_float(
                r"\| CodeLlama \(7B\) \| [^|]+ \| \*\*(?P<value>0\.\d+)\*\* \(L14\) \|",
                text,
                "codellama single",
            ),
        ),
        "mistral_single_partial_rho": HeadlineMetric(
            label="Mistral single-vector partial rho",
            value=_extract_float(
                r"\| Mistral \(7B\) \| [^|]+ \| \*\*(?P<value>0\.\d+)\*\* \(L18\) \|",
                text,
                "mistral single",
            ),
        ),
        "codebert_attentive_partial_rho": HeadlineMetric(
            label="CodeBERT attentive partial rho",
            value=_extract_float(
                r"\| CodeBERT \(L12\) \| 0\.45 \| \*\*(?P<value>0\.\d+)\*\* \|",
                text,
                "codebert attentive",
            ),
        ),
    }


def extract_ablation_metrics(ablation_json: Path) -> dict[str, float]:
    payload = json.loads(ablation_json.read_text(encoding="utf-8"))
    rows = {
        row["condition"]: row["rho"]
        for row in payload["results"]
        if row["embedder"] == "codebert"
    }
    baseline = rows["C0_baseline"]
    return {
        "baseline_rho": baseline,
        "destroy_drop": round(baseline - rows["C1_destroy"], 3),
        "shuffle_drop": round(baseline - rows["C2_shuffle"], 3),
        "normalize_drop": round(baseline - rows["C3_normalize"], 3),
    }


def extract_band_failure_metrics(stratification_json: Path) -> dict[str, dict[str, float | int]]:
    payload = json.loads(stratification_json.read_text(encoding="utf-8"))
    grouped: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "mid_total": 0,
            "mid_fail": 0,
            "near_total": 0,
            "near_fail": 0,
            "far_total": 0,
            "far_fail": 0,
        }
    )

    for row in payload["records"]:
        family = row["distance_family"]
        band = row["band_id"]
        failed = 0 if row["failure_mode"] == "aligned" else 1
        bucket = grouped[family]
        if band in {"B2", "B3", "B4"}:
            bucket["mid_total"] += 1
            bucket["mid_fail"] += failed
        elif band == "B1":
            bucket["near_total"] += 1
            bucket["near_fail"] += failed
        elif band == "B5":
            bucket["far_total"] += 1
            bucket["far_fail"] += failed

    out: dict[str, dict[str, float | int]] = {}
    for family, bucket in grouped.items():
        out[family] = {
            "mid_total": bucket["mid_total"],
            "mid_fail_rate": round(bucket["mid_fail"] / bucket["mid_total"], 3),
            "near_fail_rate": round(bucket["near_fail"] / bucket["near_total"], 3),
            "far_fail_rate": round(bucket["far_fail"] / bucket["far_total"], 3),
        }
    return out


def build_scorecard(
    experiments_md: Path,
    ablation_json: Path,
    stratification_json: Path,
) -> dict:
    headline = extract_headline_metrics(experiments_md)
    ablation = extract_ablation_metrics(ablation_json)
    band_failures = extract_band_failure_metrics(stratification_json)

    codebert_single = headline["codebert_single_partial_rho"].value
    size_best = max(
        headline["codellama_single_partial_rho"].value,
        headline["mistral_single_partial_rho"].value,
    )
    attentive = headline["codebert_attentive_partial_rho"].value
    access_lift = round(attentive - codebert_single, 3)
    size_lift = round(size_best - codebert_single, 3)
    reversal_margin = round(attentive - size_best, 3)

    hypothesis_supported = access_lift >= 0.20 and attentive > size_best
    optimize_priority = (
        "access_path_and_middle_band"
        if hypothesis_supported
        else "model_scale_or_probe_reassessment"
    )

    return {
        "schema_version": "access_path_scorecard.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "experiments_md": str(experiments_md),
            "ablation_json": str(ablation_json),
            "stratification_json": str(stratification_json),
        },
        "headline_metrics": {
            key: {"label": metric.label, "value": metric.value}
            for key, metric in headline.items()
        },
        "derived_metrics": {
            "size_best_single_partial_rho": size_best,
            "access_lift": access_lift,
            "size_lift": size_lift,
            "reversal_margin": reversal_margin,
            "access_beats_size": attentive > size_best,
            "hypothesis_supported": hypothesis_supported,
            "optimize_priority": optimize_priority,
        },
        "structure_sensitivity": ablation,
        "band_failure_rates": band_failures,
        "decision_surface": {
            "primary_focus": "access_path" if hypothesis_supported else "reassess_scale",
            "secondary_focus": "middle_band_resolution",
            "next_kpis": [
                "access_lift",
                "reversal_margin",
                "d_lethe_candidate.mid_fail_rate",
                "destroy_drop",
                "shuffle_drop",
            ],
        },
    }


def render_markdown(scorecard: dict) -> str:
    hm = scorecard["headline_metrics"]
    dm = scorecard["derived_metrics"]
    ss = scorecard["structure_sensitivity"]
    bf = scorecard["band_failure_rates"]

    lines = [
        "# Access-Path Scorecard",
        "",
        "Lethe canonical record から、`model size` と `access-path` の優先順位を再利用可能な形で固定する。",
        "",
        "## Headline",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| CodeBERT single-vector partial rho | {hm['codebert_single_partial_rho']['value']:.2f} |",
        f"| CodeBERT attentive partial rho | {hm['codebert_attentive_partial_rho']['value']:.2f} |",
        f"| CodeLlama single-vector partial rho | {hm['codellama_single_partial_rho']['value']:.2f} |",
        f"| Mistral single-vector partial rho | {hm['mistral_single_partial_rho']['value']:.2f} |",
        f"| Access lift | {dm['access_lift']:.2f} |",
        f"| Size lift | {dm['size_lift']:.2f} |",
        f"| Reversal margin | {dm['reversal_margin']:.2f} |",
        "",
        "## Structure Sensitivity",
        "",
        "| Metric | Drop |",
        "|---|---:|",
        f"| Destroy structural tokens | {ss['destroy_drop']:.3f} |",
        f"| Shuffle token order | {ss['shuffle_drop']:.3f} |",
        f"| Normalize non-structural tokens | {ss['normalize_drop']:.3f} |",
        "",
        "## Middle-Band Geometry",
        "",
        "| Family | Near fail | Mid fail | Far fail |",
        "|---|---:|---:|---:|",
        f"| ccl_string | {bf['ccl_string']['near_fail_rate']:.3f} | {bf['ccl_string']['mid_fail_rate']:.3f} | {bf['ccl_string']['far_fail_rate']:.3f} |",
        f"| cosine_49d | {bf['cosine_49d']['near_fail_rate']:.3f} | {bf['cosine_49d']['mid_fail_rate']:.3f} | {bf['cosine_49d']['far_fail_rate']:.3f} |",
        f"| d_lethe_candidate | {bf['d_lethe_candidate']['near_fail_rate']:.3f} | {bf['d_lethe_candidate']['mid_fail_rate']:.3f} | {bf['d_lethe_candidate']['far_fail_rate']:.3f} |",
        "",
        "## Decision",
        "",
        f"- access_beats_size: `{str(dm['access_beats_size']).lower()}`",
        f"- hypothesis_supported: `{str(dm['hypothesis_supported']).lower()}`",
        f"- optimize_priority: `{dm['optimize_priority']}`",
        "",
        "## Sources",
        "",
        f"- `{scorecard['sources']['experiments_md']}`",
        f"- `{scorecard['sources']['ablation_json']}`",
        f"- `{scorecard['sources']['stratification_json']}`",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments-md", type=Path, default=DEFAULT_EXPERIMENTS_MD)
    parser.add_argument("--ablation-json", type=Path, default=DEFAULT_ABLATION_JSON)
    parser.add_argument("--stratification-json", type=Path, default=DEFAULT_STRATIFICATION_JSON)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUTPUT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scorecard = build_scorecard(
        experiments_md=args.experiments_md,
        ablation_json=args.ablation_json,
        stratification_json=args.stratification_json,
    )

    args.out_json.write_text(
        json.dumps(scorecard, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.out_md.write_text(render_markdown(scorecard), encoding="utf-8")

    print(f"saved: {args.out_json}")
    print(f"saved: {args.out_md}")


if __name__ == "__main__":
    main()
