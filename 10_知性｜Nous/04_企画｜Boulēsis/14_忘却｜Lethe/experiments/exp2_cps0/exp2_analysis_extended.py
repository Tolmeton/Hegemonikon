#!/usr/bin/env python3
"""
exp2_analysis_extended.py — CPS0' extended analysis for Q1-Q4 verification
==========================================================================

Analyzes:
1. Cross-judge agreement (original 2.5-flash vs flash-lite)
2. Phase 4 ablation (E vs B on self_correction)
3. Cross-model replication (flash-lite B' vs C')
4. 4d composite (sans self_correction) as standard output

Usage:
  python exp2_analysis_extended.py                          # all analyses
  python exp2_analysis_extended.py --crossjudge             # cross-judge only
  python exp2_analysis_extended.py --ablation               # ablation only
  python exp2_analysis_extended.py --crossmodel             # cross-model only
"""

import argparse
import csv
import sys
from pathlib import Path
from collections import defaultdict

import numpy as np
from scipy import stats

RESULTS_DIR = Path(__file__).parent / "results"
DIMENSIONS = ["analytical_depth", "logical_coherence", "novelty", "self_correction", "precision"]
DIMS_NO_SC = [d for d in DIMENSIONS if d != "self_correction"]


def load_scores(csv_path: Path) -> list[dict]:
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            for d in DIMENSIONS:
                r[f"{d}_score"] = float(r[f"{d}_score"]) if r.get(f"{d}_score") else 0
            r["composite_5d"] = float(r.get("composite_5d", 0))
            rows.append(r)
    return rows


def compute_composite_4d(row: dict) -> float:
    vals = [row[f"{d}_score"] for d in DIMS_NO_SC]
    return sum(vals) / len(vals) if vals else 0


def welch_t(a: list, b: list) -> tuple:
    a, b = np.array(a), np.array(b)
    t, p = stats.ttest_ind(a, b, equal_var=False)
    d = (a.mean() - b.mean()) / np.sqrt((a.std()**2 + b.std()**2) / 2) if (a.std() + b.std()) > 0 else 0
    return t, p, d


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ─── Cross-Judge Agreement (Q3) ───────────────────────────────

def analyze_crossjudge():
    print_section("Cross-Judge Agreement: 2.5-flash vs 3.1-flash-lite")

    # Find score files
    original_files = sorted(RESULTS_DIR.glob("judge_scores_gemini_20260409*.csv"))
    flashlite_files = sorted(RESULTS_DIR.glob("judge_scores_gemini_20260411*.csv"))

    if not original_files:
        print("  ❌ Original judge scores not found (judge_scores_gemini_20260409*.csv)")
        return
    if not flashlite_files:
        print("  ❌ Flash-lite judge scores not found (judge_scores_gemini_20260411*.csv)")
        return

    orig = load_scores(original_files[0])
    lite = load_scores(flashlite_files[-1])  # latest flash-lite file

    print(f"  Original: {original_files[0].name} ({len(orig)} rows)")
    print(f"  FlashLite: {flashlite_files[-1].name} ({len(lite)} rows)")

    # Match by filename
    orig_by_file = {r["file"]: r for r in orig}
    lite_by_file = {r["file"]: r for r in lite}
    common = set(orig_by_file.keys()) & set(lite_by_file.keys())
    print(f"  Common files: {len(common)}")

    if len(common) < 50:
        print("  ⚠️  Too few common files for meaningful analysis")
        return

    # Per-dimension correlation
    print(f"\n  Per-dimension Pearson r (N={len(common)}):")
    print(f"  {'Dimension':<25} {'r':>8} {'p':>10} {'MAE':>8} {'Bias':>8}")
    print(f"  {'-'*61}")

    for d in DIMENSIONS:
        o_vals = [orig_by_file[f][f"{d}_score"] for f in common]
        l_vals = [lite_by_file[f][f"{d}_score"] for f in common]
        r, p = stats.pearsonr(o_vals, l_vals)
        mae = np.mean(np.abs(np.array(o_vals) - np.array(l_vals)))
        bias = np.mean(np.array(l_vals) - np.array(o_vals))
        print(f"  {d:<25} {r:8.3f} {p:10.4f} {mae:8.2f} {bias:+8.2f}")

    # Composite correlations
    for comp_name, dims in [("composite_5d", DIMENSIONS), ("composite_4d_noSC", DIMS_NO_SC)]:
        o_vals = [sum(orig_by_file[f][f"{d}_score"] for d in dims) / len(dims) for f in common]
        l_vals = [sum(lite_by_file[f][f"{d}_score"] for d in dims) / len(dims) for f in common]
        r, p = stats.pearsonr(o_vals, l_vals)
        mae = np.mean(np.abs(np.array(o_vals) - np.array(l_vals)))
        print(f"  {comp_name:<25} {r:8.3f} {p:10.4f} {mae:8.2f}")

    # Critical test: does flash-lite ALSO show B > C?
    print(f"\n  Critical B vs C test (flash-lite judge):")
    b_scores_5d = [float(lite_by_file[f]["composite_5d"]) for f in common
                   if lite_by_file[f]["condition"] == "B_HiStr_LoCon"]
    c_scores_5d = [float(lite_by_file[f]["composite_5d"]) for f in common
                   if lite_by_file[f]["condition"] == "C_LoStr_HiCon"]

    if b_scores_5d and c_scores_5d:
        t, p, d = welch_t(b_scores_5d, c_scores_5d)
        print(f"    5d: B={np.mean(b_scores_5d):.3f}, C={np.mean(c_scores_5d):.3f}, "
              f"t={t:.3f}, p={p:.4f}, d={d:.3f}")

    # B vs C on self_correction only (flash-lite)
    b_sc = [lite_by_file[f]["self_correction_score"] for f in common
            if lite_by_file[f]["condition"] == "B_HiStr_LoCon"]
    c_sc = [lite_by_file[f]["self_correction_score"] for f in common
            if lite_by_file[f]["condition"] == "C_LoStr_HiCon"]
    if b_sc and c_sc:
        t, p, d = welch_t(b_sc, c_sc)
        print(f"    SC: B={np.mean(b_sc):.3f}, C={np.mean(c_sc):.3f}, "
              f"t={t:.3f}, p={p:.4f}, d={d:.3f}")

    # B vs C on 4d-noSC (flash-lite)
    b_4d = [sum(lite_by_file[f][f"{d}_score"] for d in DIMS_NO_SC) / len(DIMS_NO_SC)
            for f in common if lite_by_file[f]["condition"] == "B_HiStr_LoCon"]
    c_4d = [sum(lite_by_file[f][f"{d}_score"] for d in DIMS_NO_SC) / len(DIMS_NO_SC)
            for f in common if lite_by_file[f]["condition"] == "C_LoStr_HiCon"]
    if b_4d and c_4d:
        t, p, d = welch_t(b_4d, c_4d)
        print(f"    4d: B={np.mean(b_4d):.3f}, C={np.mean(c_4d):.3f}, "
              f"t={t:.3f}, p={p:.4f}, d={d:.3f}")

    # Per-dimension B vs C contribution (flash-lite)
    print(f"\n  Per-dimension B-C gap (flash-lite):")
    print(f"  {'Dimension':<25} {'B_mean':>8} {'C_mean':>8} {'Gap':>8} {'d':>8}")
    print(f"  {'-'*57}")
    for dim in DIMENSIONS:
        b_d = [lite_by_file[f][f"{dim}_score"] for f in common
               if lite_by_file[f]["condition"] == "B_HiStr_LoCon"]
        c_d = [lite_by_file[f][f"{dim}_score"] for f in common
               if lite_by_file[f]["condition"] == "C_LoStr_HiCon"]
        if b_d and c_d:
            _, _, eff = welch_t(b_d, c_d)
            print(f"  {dim:<25} {np.mean(b_d):8.3f} {np.mean(c_d):8.3f} "
                  f"{np.mean(b_d)-np.mean(c_d):+8.3f} {eff:8.3f}")


# ─── Phase 4 Ablation (Q2) ──────────────────────────────────

def analyze_ablation():
    print_section("Phase 4 Ablation: E (noPhase4) vs B (fullHiStr)")

    # Load judge scores that include E condition
    all_judge_files = sorted(RESULTS_DIR.glob("judge_scores_gemini_*.csv"))
    e_rows = []
    b_rows = []

    for jf in all_judge_files:
        rows = load_scores(jf)
        for r in rows:
            if r["condition"] == "E_HiStr_noP4_LoCon":
                e_rows.append(r)
            elif r["condition"] == "B_HiStr_LoCon":
                b_rows.append(r)

    if not e_rows:
        print("  ❌ No E condition scores found. Run ablation generation + judging first.")
        return

    print(f"  E (noPhase4): {len(e_rows)} rows")
    print(f"  B (fullHiStr): {len(b_rows)} rows")

    # Critical: self_correction comparison
    e_sc = [r["self_correction_score"] for r in e_rows]
    b_sc = [r["self_correction_score"] for r in b_rows]
    t, p, d = welch_t(b_sc, e_sc)

    print(f"\n  *** CRITICAL TEST: self_correction ***")
    print(f"    B (full HiStr): {np.mean(b_sc):.3f} ± {np.std(b_sc):.3f}")
    print(f"    E (no Phase4):  {np.mean(e_sc):.3f} ± {np.std(e_sc):.3f}")
    print(f"    Welch t={t:.3f}, p={p:.6f}, d={d:.3f}")

    if p < 0.05 and d > 0.3:
        print(f"    → Phase 4 DOES drive self_correction (tautology risk confirmed)")
    elif p >= 0.05:
        print(f"    → Phase 4 does NOT uniquely drive self_correction (genuine metacognition)")

    # All dimensions
    print(f"\n  Per-dimension B vs E:")
    print(f"  {'Dimension':<25} {'B_mean':>8} {'E_mean':>8} {'Gap':>8} {'d':>8} {'p':>10}")
    print(f"  {'-'*69}")
    for dim in DIMENSIONS:
        b_d = [r[f"{dim}_score"] for r in b_rows]
        e_d = [r[f"{dim}_score"] for r in e_rows]
        t_d, p_d, d_d = welch_t(b_d, e_d)
        print(f"  {dim:<25} {np.mean(b_d):8.3f} {np.mean(e_d):8.3f} "
              f"{np.mean(b_d)-np.mean(e_d):+8.3f} {d_d:8.3f} {p_d:10.4f}")

    # Composite
    b_5d = [float(r["composite_5d"]) for r in b_rows]
    e_5d = [sum(r[f"{d}_score"] for d in DIMENSIONS) / 5 for r in e_rows]
    t, p, d = welch_t(b_5d, e_5d)
    print(f"\n  Composite 5d: B={np.mean(b_5d):.3f} vs E={np.mean(e_5d):.3f}, d={d:.3f}, p={p:.4f}")


# ─── Cross-Model Replication (Q1, Q4) ────────────────────────

def analyze_crossmodel():
    print_section("Cross-Model Replication: flash-lite generated B' vs C'")

    # Find flashlite-generated raw files
    b_files = sorted(RESULTS_DIR.glob("raw_B_HiStr_LoCon_*_flashlite.json"))
    c_files = sorted(RESULTS_DIR.glob("raw_C_LoStr_HiCon_*_flashlite.json"))

    if not b_files and not c_files:
        print("  ❌ No cross-model files found. Run crossmodel generation first.")
        return

    print(f"  B' raw files: {len(b_files)}")
    print(f"  C' raw files: {len(c_files)}")

    # Check if they've been judged
    all_judge_files = sorted(RESULTS_DIR.glob("judge_scores_gemini_*.csv"))
    b_judged = []
    c_judged = []
    for jf in all_judge_files:
        rows = load_scores(jf)
        for r in rows:
            fname = r.get("file", "")
            if "flashlite" in fname:
                if r["condition"] == "B_HiStr_LoCon":
                    b_judged.append(r)
                elif r["condition"] == "C_LoStr_HiCon":
                    c_judged.append(r)

    if not b_judged or not c_judged:
        print("  ⚠️  Cross-model files not yet judged. Judge them first.")
        return

    print(f"  B' judged: {len(b_judged)}")
    print(f"  C' judged: {len(c_judged)}")

    # B' vs C' on 5d
    b_5d = [float(r["composite_5d"]) for r in b_judged]
    c_5d = [float(r["composite_5d"]) for r in c_judged]
    t, p, d = welch_t(b_5d, c_5d)
    print(f"\n  5d: B'={np.mean(b_5d):.3f} vs C'={np.mean(c_5d):.3f}, t={t:.3f}, p={p:.4f}, d={d:.3f}")

    # B' vs C' on self_correction
    b_sc = [r["self_correction_score"] for r in b_judged]
    c_sc = [r["self_correction_score"] for r in c_judged]
    t, p, d = welch_t(b_sc, c_sc)
    print(f"  SC: B'={np.mean(b_sc):.3f} vs C'={np.mean(c_sc):.3f}, t={t:.3f}, p={p:.4f}, d={d:.3f}")

    # B' vs C' on 4d (no SC)
    b_4d = [sum(r[f"{d}_score"] for d in DIMS_NO_SC) / len(DIMS_NO_SC) for r in b_judged]
    c_4d = [sum(r[f"{d}_score"] for d in DIMS_NO_SC) / len(DIMS_NO_SC) for r in c_judged]
    t, p, d = welch_t(b_4d, c_4d)
    print(f"  4d: B'={np.mean(b_4d):.3f} vs C'={np.mean(c_4d):.3f}, t={t:.3f}, p={p:.4f}, d={d:.3f}")

    # Per-dimension
    print(f"\n  Per-dimension B' vs C' (flash-lite generated):")
    print(f"  {'Dimension':<25} {'B_mean':>8} {'C_mean':>8} {'Gap':>8} {'d':>8}")
    print(f"  {'-'*57}")
    for dim in DIMENSIONS:
        bd = [r[f"{dim}_score"] for r in b_judged]
        cd = [r[f"{dim}_score"] for r in c_judged]
        _, _, eff = welch_t(bd, cd)
        print(f"  {dim:<25} {np.mean(bd):8.3f} {np.mean(cd):8.3f} "
              f"{np.mean(bd)-np.mean(cd):+8.3f} {eff:8.3f}")


def main():
    parser = argparse.ArgumentParser(description="CPS0' Extended Analysis")
    parser.add_argument("--crossjudge", action="store_true")
    parser.add_argument("--ablation", action="store_true")
    parser.add_argument("--crossmodel", action="store_true")
    args = parser.parse_args()

    run_all = not (args.crossjudge or args.ablation or args.crossmodel)

    if run_all or args.crossjudge:
        analyze_crossjudge()
    if run_all or args.ablation:
        analyze_ablation()
    if run_all or args.crossmodel:
        analyze_crossmodel()


if __name__ == "__main__":
    main()
