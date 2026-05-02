#!/usr/bin/env python3
"""Alternative decision-metric probe for the OA-SAM bifurcation surface.

This probe does not replace the canonical fixed classifier.
It asks whether the observed split survives under alternative gap metrics
derived from the same recorded profile family.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from statistics import mean


METHOD_LABELS = {
    "oa_sam": "OA-SAM (λ<0)",
    "oa_sam_pos": "Control (λ>0)",
}

PATH_ORDER = ("path_a", "path_b", "mixed_none")
STATUS_LABELS = {
    "joint_pass": "OA+CTRL",
    "oa_only": "OA_ONLY",
    "ctrl_only": "CTRL_ONLY",
    "fail": "FAIL",
}

METRIC_FAMILIES = {
    "final_cka_gap": {
        "label": "final CKA gap",
        "description": "final_epoch の (L2 CKA - L3 CKA)",
        "margins": [0.30, 0.40, 0.50, 0.60, 0.70, 0.80],
    },
    "temporal_cka_gap_mean": {
        "label": "temporal CKA gap mean",
        "description": "全 profile epoch における mean(L2 CKA - L3 CKA)",
        "margins": [0.20, 0.25, 0.30, 0.35, 0.40, 0.45],
    },
    "final_grad_gap": {
        "label": "final grad gap",
        "description": "final_epoch の (grad_phi[L3] - grad_phi[L2])",
        "margins": [0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80],
    },
    "temporal_grad_gap_mean": {
        "label": "temporal grad gap mean",
        "description": "全 profile epoch における mean(grad_phi[L3] - grad_phi[L2])",
        "margins": [0.10, 0.15, 0.20, 0.25, 0.30, 0.35],
    },
}


def parse_args():
    root = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description="Alternative metric probe for bifurcation robustness")
    ap.add_argument(
        "--sources",
        nargs="+",
        default=[str(root / "results"), str(root / "results_cka")],
        help="探索する結果ディレクトリ群",
    )
    ap.add_argument(
        "--out-json",
        default=str(root / "bifurcation_alt_metric_probe.json"),
        help="JSON 出力先",
    )
    ap.add_argument(
        "--out-md",
        default=str(root / "bifurcation_alt_metric_probe.md"),
        help="Markdown 出力先",
    )
    return ap.parse_args()


def parse_result_name(path: Path):
    match = re.match(r"(?P<method>.+)_seed(?P<seed>\d+)\.json$", path.name)
    if not match:
        return None
    return match.group("method"), int(match.group("seed"))


def load_record(path: Path):
    data = json.loads(path.read_text())
    profiles = data.get("profiles") or data.get("cka_profiles") or []
    if not profiles:
        raise ValueError(f"profiles missing: {path}")
    final_profile = max(profiles, key=lambda item: item.get("epoch", -1))
    final_cka = final_profile.get("cka")
    final_grad = final_profile.get("grad_phi")
    if not isinstance(final_cka, list) or len(final_cka) != 4:
        raise ValueError(f"invalid final cka: {path}")
    if not isinstance(final_grad, list) or len(final_grad) != 4:
        raise ValueError(f"invalid final grad_phi: {path}")
    return {
        "method": data["method"],
        "seed": int(data["seed"]),
        "source_file": str(path),
        "profiles": profiles,
        "final_acc": float((data.get("test_acc") or [None])[-1]),
        "metrics": {
            "final_cka_gap": float(final_cka[1]) - float(final_cka[2]),
            "temporal_cka_gap_mean": mean(float(profile["cka"][1]) - float(profile["cka"][2]) for profile in profiles),
            "final_grad_gap": float(final_grad[2]) - float(final_grad[1]),
            "temporal_grad_gap_mean": mean(
                float(profile["grad_phi"][2]) - float(profile["grad_phi"][1]) for profile in profiles
            ),
        },
    }


def collect_records(source_dirs):
    records = {method: {} for method in METHOD_LABELS}
    duplicates = []
    for source_dir in source_dirs:
        for path in sorted(Path(source_dir).glob("*.json")):
            parsed = parse_result_name(path)
            if parsed is None:
                continue
            method, seed = parsed
            if method not in records:
                continue
            if seed in records[method]:
                duplicates.append(
                    {
                        "method": method,
                        "seed": seed,
                        "kept": records[method][seed]["source_file"],
                        "ignored": str(path),
                    }
                )
                continue
            records[method][seed] = load_record(path)
    return {k: [v for _, v in sorted(m.items())] for k, m in records.items()}, duplicates


def classify(metric_value: float, margin: float):
    if metric_value >= margin:
        return "path_a"
    if metric_value <= -margin:
        return "path_b"
    return "mixed_none"


def summarize_method(records, family_key: str, margin: float):
    classified = {path: [] for path in PATH_ORDER}
    for record in records:
        classified[classify(record["metrics"][family_key], margin)].append(record)
    counts = Counter({path: len(classified[path]) for path in PATH_ORDER})
    return {
        "counts": {path: counts[path] for path in PATH_ORDER},
        "seeds": {path: [record["seed"] for record in classified[path]] for path in PATH_ORDER},
    }


def evaluate_family(records_by_method, family_key: str):
    margins = METRIC_FAMILIES[family_key]["margins"]
    oa_values = [record["metrics"][family_key] for record in records_by_method["oa_sam"]]
    ctrl_values = [record["metrics"][family_key] for record in records_by_method["oa_sam_pos"]]
    combos = []
    for margin in margins:
        oa = summarize_method(records_by_method["oa_sam"], family_key, margin)
        ctrl = summarize_method(records_by_method["oa_sam_pos"], family_key, margin)
        oa_total = sum(oa["counts"].values())
        oa_mixed_fraction = oa["counts"]["mixed_none"] / oa_total if oa_total else None
        oa_pass = (
            oa["counts"]["path_a"] > 0
            and oa["counts"]["path_b"] > 0
            and oa_mixed_fraction is not None
            and oa_mixed_fraction <= 0.10
        )
        ctrl_pass = ctrl["counts"]["path_a"] == 0 and ctrl["counts"]["path_b"] == 0
        if oa_pass and ctrl_pass:
            status = "joint_pass"
        elif oa_pass:
            status = "oa_only"
        elif ctrl_pass:
            status = "ctrl_only"
        else:
            status = "fail"
        combos.append(
            {
                "margin": margin,
                "status": status,
                "oa_bifurcation_exists": oa_pass,
                "control_zero_extremes": ctrl_pass,
                "oa": oa,
                "control": ctrl,
            }
        )
    return {
        "label": METRIC_FAMILIES[family_key]["label"],
        "description": METRIC_FAMILIES[family_key]["description"],
        "margins": margins,
        "oa_range": {"min": min(oa_values), "max": max(oa_values)},
        "control_range": {"min": min(ctrl_values), "max": max(ctrl_values)},
        "oa_abs_min": min(abs(value) for value in oa_values),
        "control_abs_max": max(abs(value) for value in ctrl_values),
        "seed_values": {
            "oa_sam": {record["seed"]: record["metrics"][family_key] for record in records_by_method["oa_sam"]},
            "oa_sam_pos": {record["seed"]: record["metrics"][family_key] for record in records_by_method["oa_sam_pos"]},
        },
        "combos": combos,
        "joint_pass_count": sum(1 for combo in combos if combo["status"] == "joint_pass"),
        "total_combos": len(combos),
    }


def build_summary(records_by_method, duplicates, sources):
    families = {
        family_key: evaluate_family(records_by_method, family_key)
        for family_key in METRIC_FAMILIES
    }
    return {
        "sources": [str(Path(path).resolve()) for path in sources],
        "duplicates": duplicates,
        "record_counts": {
            method: len(records_by_method[method])
            for method in METHOD_LABELS
        },
        "families": families,
    }


def render_family_table(family):
    lines = [
        "| margin | status | OA Path A | OA Path B | OA mixed | CTRL Path A | CTRL Path B | CTRL mixed |",
        "|---:|:---|---:|---:|---:|---:|---:|---:|",
    ]
    for combo in family["combos"]:
        lines.append(
            f"| {combo['margin']:.2f} | {STATUS_LABELS[combo['status']]} | "
            f"{combo['oa']['counts']['path_a']} | {combo['oa']['counts']['path_b']} | {combo['oa']['counts']['mixed_none']} | "
            f"{combo['control']['counts']['path_a']} | {combo['control']['counts']['path_b']} | {combo['control']['counts']['mixed_none']} |"
        )
    return lines


def render_seed_values(family):
    lines = ["| method | seed | value |", "|:--|---:|---:|"]
    for method in ("oa_sam", "oa_sam_pos"):
        for seed, value in sorted(family["seed_values"][method].items()):
            lines.append(f"| {METHOD_LABELS[method]} | {seed} | {value:.4f} |")
    return lines


def render_markdown(summary):
    lines = [
        "# Bifurcation Alternative Metric Probe",
        "",
        "## Scope",
        "",
        "- Probe target: bifurcation が fixed threshold box ではなく、別の gap metrics でも残るか",
        "- Note: これは raw activation を使う外部 metric replacement ではなく、既存 CKA-family profile 上の alternative decision metrics probe",
        "",
        "## Raw Status",
        "",
        f"- OA-SAM records: {summary['record_counts']['oa_sam']}",
        f"- Control records: {summary['record_counts']['oa_sam_pos']}",
        f"- Duplicate inputs ignored: {len(summary['duplicates'])}",
        "",
    ]
    for family_key, family in summary["families"].items():
        lines.extend(
            [
                f"## {family['label']}",
                "",
                f"- description: {family['description']}",
                f"- OA range: {family['oa_range']['min']:.4f} .. {family['oa_range']['max']:.4f}",
                f"- Control range: {family['control_range']['min']:.4f} .. {family['control_range']['max']:.4f}",
                f"- OA abs-min: {family['oa_abs_min']:.4f}",
                f"- Control abs-max: {family['control_abs_max']:.4f}",
                f"- Joint-pass margins: {family['joint_pass_count']}/{family['total_combos']}",
                "",
                *render_family_table(family),
                "",
                "Seed values:",
                "",
                *render_seed_values(family),
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def main():
    args = parse_args()
    records_by_method, duplicates = collect_records(args.sources)
    summary = build_summary(records_by_method, duplicates, args.sources)
    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    out_md.write_text(render_markdown(summary))
    family_status = " ".join(
        f"{key}={summary['families'][key]['joint_pass_count']}/{summary['families'][key]['total_combos']}"
        for key in METRIC_FAMILIES
    )
    print("alt_metric_probe:", family_status)
    print(f"→ {out_json}")
    print(f"→ {out_md}")


if __name__ == "__main__":
    main()
