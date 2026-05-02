#!/usr/bin/env python3
"""Threshold sensitivity probe for the OA-SAM bifurcation classifier.

The canonical bifurcation CLI intentionally fixes the classifier at:
  - Path A: L2 >= 0.8 and L3 <= 0.2
  - Path B: L3 >= 0.8 and L2 <= 0.2

This probe leaves that authoritative report untouched and asks a narrower
question: does the observed OA-SAM split survive modest threshold changes?
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


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


def parse_args():
    root = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description="Bifurcation threshold sensitivity probe")
    ap.add_argument(
        "--sources",
        nargs="+",
        default=[str(root / "results"), str(root / "results_cka")],
        help="探索する結果ディレクトリ群",
    )
    ap.add_argument(
        "--hi-values",
        default="0.70,0.75,0.80,0.85,0.90",
        help="preserve cutoff 候補 (comma-separated floats)",
    )
    ap.add_argument(
        "--lo-values",
        default="0.10,0.15,0.20,0.25,0.30",
        help="forget cutoff 候補 (comma-separated floats)",
    )
    ap.add_argument(
        "--out-json",
        default=str(root / "bifurcation_threshold_probe.json"),
        help="JSON 出力先",
    )
    ap.add_argument(
        "--out-md",
        default=str(root / "bifurcation_threshold_probe.md"),
        help="Markdown 出力先",
    )
    return ap.parse_args()


def parse_float_csv(spec: str):
    values = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        values.append(float(chunk))
    return values


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
    cka = final_profile.get("cka")
    if not isinstance(cka, list) or len(cka) != 4:
        raise ValueError(f"invalid final cka: {path}")
    return {
        "method": data["method"],
        "seed": int(data["seed"]),
        "source_file": str(path),
        "l2": float(cka[1]),
        "l3": float(cka[2]),
        "final_acc": float((data.get("test_acc") or [None])[-1]),
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


def classify(l2: float, l3: float, hi: float, lo: float):
    if l2 >= hi and l3 <= lo:
        return "path_a"
    if l3 >= hi and l2 <= lo:
        return "path_b"
    return "mixed_none"


def summarize_method(records, hi: float, lo: float):
    classified = {path: [] for path in PATH_ORDER}
    for record in records:
        classified[classify(record["l2"], record["l3"], hi, lo)].append(record)
    counts = Counter({path: len(classified[path]) for path in PATH_ORDER})
    return {
        "counts": {path: counts[path] for path in PATH_ORDER},
        "seeds": {path: [record["seed"] for record in classified[path]] for path in PATH_ORDER},
    }


def evaluate_combo(records_by_method, hi: float, lo: float):
    oa = summarize_method(records_by_method["oa_sam"], hi, lo)
    ctrl = summarize_method(records_by_method["oa_sam_pos"], hi, lo)
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
    return {
        "hi": hi,
        "lo": lo,
        "status": status,
        "oa_bifurcation_exists": oa_pass,
        "control_zero_extremes": ctrl_pass,
        "oa": oa,
        "control": ctrl,
    }


def build_summary(records_by_method, hi_values, lo_values, duplicates):
    combos = []
    for hi in hi_values:
        for lo in lo_values:
            combos.append(evaluate_combo(records_by_method, hi, lo))

    joint_passes = [combo for combo in combos if combo["status"] == "joint_pass"]
    oa_passes = [combo for combo in combos if combo["oa_bifurcation_exists"]]
    ctrl_passes = [combo for combo in combos if combo["control_zero_extremes"]]
    canonical = next(
        (combo for combo in combos if abs(combo["hi"] - 0.8) < 1e-9 and abs(combo["lo"] - 0.2) < 1e-9),
        None,
    )
    return {
        "sources": [str(Path(path).resolve()) for path in records_by_method.pop("_sources")],
        "duplicates": duplicates,
        "grid": {"hi_values": hi_values, "lo_values": lo_values},
        "record_counts": {
            method: len(records_by_method[method])
            for method in METHOD_LABELS
        },
        "combos": combos,
        "joint_pass_count": len(joint_passes),
        "oa_pass_count": len(oa_passes),
        "control_pass_count": len(ctrl_passes),
        "total_combos": len(combos),
        "canonical": canonical,
        "joint_passes": [{"hi": combo["hi"], "lo": combo["lo"]} for combo in joint_passes],
    }


def render_matrix(summary):
    hi_values = summary["grid"]["hi_values"]
    lo_values = summary["grid"]["lo_values"]
    combo_map = {(combo["hi"], combo["lo"]): combo["status"] for combo in summary["combos"]}
    lines = [
        "| hi \\\\ lo | " + " | ".join(f"{lo:.2f}" for lo in lo_values) + " |",
        "|:--|:--" + "|:--" * (len(lo_values) - 1) + "|",
    ]
    for hi in hi_values:
        cells = [STATUS_LABELS[combo_map[(hi, lo)]] for lo in lo_values]
        lines.append(f"| {hi:.2f} | " + " | ".join(cells) + " |")
    return lines


def render_method_counts(summary, method_key):
    label = METHOD_LABELS[method_key]
    lines = [f"### {label}", "", "| hi | lo | Path A | Path B | mixed/none |", "|---:|---:|---:|---:|---:|"]
    for combo in summary["combos"]:
        counts = combo["oa"]["counts"] if method_key == "oa_sam" else combo["control"]["counts"]
        lines.append(
            f"| {combo['hi']:.2f} | {combo['lo']:.2f} | {counts['path_a']} | {counts['path_b']} | {counts['mixed_none']} |"
        )
    return lines


def render_markdown(summary):
    canonical = summary["canonical"]
    lines = [
        "# Bifurcation Threshold Sensitivity Probe",
        "",
        "## Scope",
        "",
        "- Probe target: fixed bifurcation classifier の threshold sensitivity",
        "- Preserve cutoff (`hi`): " + ", ".join(f"{value:.2f}" for value in summary["grid"]["hi_values"]),
        "- Forget cutoff (`lo`): " + ", ".join(f"{value:.2f}" for value in summary["grid"]["lo_values"]),
        "- Methods: OA-SAM (λ<0), Control (λ>0)",
        "",
        "## Raw Status",
        "",
        f"- OA-SAM records: {summary['record_counts']['oa_sam']}",
        f"- Control records: {summary['record_counts']['oa_sam_pos']}",
        f"- Duplicate inputs ignored: {len(summary['duplicates'])}",
        f"- Joint-pass combos: {summary['joint_pass_count']}/{summary['total_combos']}",
        f"- OA-only pass combos: {sum(1 for combo in summary['combos'] if combo['status'] == 'oa_only')}",
        f"- Control-only pass combos: {sum(1 for combo in summary['combos'] if combo['status'] == 'ctrl_only')}",
        f"- Fail combos: {sum(1 for combo in summary['combos'] if combo['status'] == 'fail')}",
        "",
        "## Canonical Check",
        "",
        f"- canonical `(hi=0.80, lo=0.20)`: {STATUS_LABELS[canonical['status']]}",
        f"- canonical OA counts: A={canonical['oa']['counts']['path_a']}, B={canonical['oa']['counts']['path_b']}, mixed={canonical['oa']['counts']['mixed_none']}",
        f"- canonical control counts: A={canonical['control']['counts']['path_a']}, B={canonical['control']['counts']['path_b']}, mixed={canonical['control']['counts']['mixed_none']}",
        "",
        "## Status Matrix",
        "",
        *render_matrix(summary),
        "",
        "Legend:",
        "",
        "- `OA+CTRL`: OA bifurcation exists and control zero-extremes both hold",
        "- `OA_ONLY`: OA bifurcation holds but control zero-extremes fail",
        "- `CTRL_ONLY`: control zero-extremes hold but OA bifurcation fails",
        "- `FAIL`: both fail",
        "",
        *render_method_counts(summary, "oa_sam"),
        "",
        *render_method_counts(summary, "oa_sam_pos"),
        "",
    ]
    return "\n".join(lines).strip() + "\n"


def main():
    args = parse_args()
    hi_values = parse_float_csv(args.hi_values)
    lo_values = parse_float_csv(args.lo_values)
    records_by_method, duplicates = collect_records(args.sources)
    records_by_method["_sources"] = args.sources
    summary = build_summary(records_by_method, hi_values, lo_values, duplicates)

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    out_md.write_text(render_markdown(summary))

    print(
        "threshold_probe:",
        f"joint_pass={summary['joint_pass_count']}/{summary['total_combos']}",
        f"oa_pass={summary['oa_pass_count']}",
        f"control_pass={summary['control_pass_count']}",
    )
    print(f"→ {out_json}")
    print(f"→ {out_md}")


if __name__ == "__main__":
    main()
