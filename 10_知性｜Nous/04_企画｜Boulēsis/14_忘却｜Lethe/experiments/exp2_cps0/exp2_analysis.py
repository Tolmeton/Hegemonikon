#!/usr/bin/env python3
"""
exp2_analysis.py — CPS0' 実験結果分析
======================================

judge_scores*.csv を読み込み、Two-way ANOVA + ANCOVA + B vs C 対比を実行。
Usage:
  python exp2_analysis.py [--scores results/judge_scores_*.csv]

依存: pip install pandas scipy statsmodels
"""

import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
    from scipy import stats
except ImportError:
    print("ERROR: pandas and scipy required. pip install pandas scipy")
    sys.exit(1)

try:
    from statsmodels.formula.api import ols
    from statsmodels.stats.anova import anova_lm
    HAS_STATSMODELS = True
except ImportError:
    print("WARNING: statsmodels not found. ANOVA disabled. pip install statsmodels")
    HAS_STATSMODELS = False

RESULTS_DIR = Path(__file__).parent / "results"


def load_scores(path: str | None = None) -> pd.DataFrame:
    """Load the most recent judge scores CSV."""
    if path:
        return pd.read_csv(path)
    files = sorted(RESULTS_DIR.glob("judge_scores_*.csv"))
    if not files:
        print("No judge_scores_*.csv found.")
        sys.exit(1)
    return pd.read_csv(files[-1])


def extract_factors(df: pd.DataFrame) -> pd.DataFrame:
    """Extract Structure and Content factors from condition labels."""
    df = df.copy()
    df["structure"] = df["condition"].apply(lambda c: "Hi" if "HiStr" in c else "Lo")
    df["content"] = df["condition"].apply(lambda c: "Hi" if "HiCon" in c else "Lo")
    return df


def cohens_d(g1, g2):
    """Cohen's d with pooled SD."""
    n1, n2 = len(g1), len(g2)
    var1, var2 = g1.var(ddof=1), g2.var(ddof=1)
    pooled_sd = ((var1 * (n1 - 1) + var2 * (n2 - 1)) / (n1 + n2 - 2)) ** 0.5
    if pooled_sd == 0:
        return 0.0
    return (g1.mean() - g2.mean()) / pooled_sd


def compute_icc(df: pd.DataFrame, score_col: str = "composite_5d") -> float | None:
    """Compute ICC(2,1) for multi-judge reliability.

    Expects columns like '{score_col}_judge1', '{score_col}_judge2', etc.
    If such columns don't exist, returns None.
    """
    judge_cols = [c for c in df.columns if c.startswith(f"{score_col}_judge")]
    if len(judge_cols) < 2:
        return None

    import numpy as np
    scores = df[judge_cols].dropna().values
    n, k = scores.shape
    if n < 2 or k < 2:
        return None

    row_mean = scores.mean(axis=1)
    grand_mean = scores.mean()

    ss_between = k * ((row_mean - grand_mean) ** 2).sum()
    ss_within = ((scores - row_mean[:, np.newaxis]) ** 2).sum()
    ss_judges = n * ((scores.mean(axis=0) - grand_mean) ** 2).sum()
    ss_error = ss_within - ss_judges

    ms_between = ss_between / max(n - 1, 1)
    ms_judges = ss_judges / max(k - 1, 1)
    ms_error = ss_error / max((n - 1) * (k - 1), 1)

    denom = ms_between + (k - 1) * ms_error + k * (ms_judges - ms_error) / max(n, 1)
    if denom == 0:
        return 0.0
    return round((ms_between - ms_error) / denom, 4)


def analyze(df: pd.DataFrame, score_col: str = "composite_5d"):
    """Run the full analysis: ANOVA → ANCOVA → B vs C → per-task → per-dimension."""
    df = extract_factors(df)

    print("=" * 60)
    print(f"CPS0' Experiment Analysis — Score: {score_col}")
    print("=" * 60)

    # --- Descriptives ---
    print("\n--- Condition Means ---")
    desc = df.groupby("condition")[score_col].agg(["mean", "std", "count"])
    print(desc.to_string())

    print("\n--- Factor Means ---")
    for factor in ["structure", "content"]:
        print(f"\n  {factor}:")
        print(df.groupby(factor)[score_col].agg(["mean", "std", "count"]).to_string())

    # --- PRIMARY: Two-way ANOVA (Structure × Content + interaction) ---
    if HAS_STATSMODELS:
        print("\n--- Two-way ANOVA (Structure × Content) ---")
        formula = f'{score_col} ~ C(structure) * C(content)'
        model = ols(formula, data=df).fit()
        anova_table = anova_lm(model, typ=2)
        print(anova_table.to_string())

        interaction_p = anova_table.loc["C(structure):C(content)", "PR(>F)"]
        if interaction_p < 0.05:
            print(f"\n  ⚠️ Significant interaction (p={interaction_p:.4f}) — interpret main effects with caution")
        else:
            print(f"\n  ✅ No significant interaction (p={interaction_p:.4f})")

        # --- ANCOVA with input_tokens covariate ---
        if "input_tokens" in df.columns:
            print("\n--- ANCOVA (covariate: input_tokens) ---")
            ancova_formula = f'{score_col} ~ C(structure) * C(content) + input_tokens'
            ancova_model = ols(ancova_formula, data=df).fit()
            ancova_table = anova_lm(ancova_model, typ=2)
            print(ancova_table.to_string())

            cov_p = ancova_table.loc["input_tokens", "PR(>F)"]
            print(f"\n  Token count covariate: p={cov_p:.4f}")
            if cov_p < 0.05:
                print("  ⚠️ Token count significantly predicts scores — verbosity confound present")
            else:
                print("  ✅ Token count is not a significant predictor")
        else:
            print("\n  (ANCOVA skipped — no input_tokens column)")
    else:
        print("\n--- ANOVA/ANCOVA skipped (install statsmodels) ---")

    # --- SUPPLEMENTARY: Mann-Whitney U (non-parametric robustness check) ---
    print("\n--- Supplementary: Mann-Whitney U ---")
    hi_str = df[df["structure"] == "Hi"][score_col]
    lo_str = df[df["structure"] == "Lo"][score_col]
    u_str, p_str = stats.mannwhitneyu(hi_str, lo_str, alternative="two-sided")
    d_str = cohens_d(hi_str, lo_str)
    print(f"  Structure: U={u_str:.1f}, p={p_str:.4f}, d={d_str:.3f}")

    hi_con = df[df["content"] == "Hi"][score_col]
    lo_con = df[df["content"] == "Lo"][score_col]
    u_con, p_con = stats.mannwhitneyu(hi_con, lo_con, alternative="two-sided")
    d_con = cohens_d(hi_con, lo_con)
    print(f"  Content:   U={u_con:.1f}, p={p_con:.4f}, d={d_con:.3f}")

    # --- Critical Test: B vs C ---
    print("\n--- CRITICAL TEST: B vs C ---")
    b = df[df["condition"] == "B_HiStr_LoCon"][score_col]
    c = df[df["condition"] == "C_LoStr_HiCon"][score_col]

    if len(b) == 0 or len(c) == 0:
        print("  ERROR: Missing B or C condition data.")
        return

    u_bc, p_bc = stats.mannwhitneyu(b, c, alternative="two-sided")
    t_bc, pt_bc = stats.ttest_ind(b, c)
    d_bc = cohens_d(b, c)

    print(f"  B (HiStr+LoCon): mean={b.mean():.3f}, sd={b.std():.3f}, n={len(b)}")
    print(f"  C (LoStr+HiCon): mean={c.mean():.3f}, sd={c.std():.3f}, n={len(c)}")
    print(f"  Mann-Whitney: U={u_bc:.1f}, p={p_bc:.4f}")
    print(f"  Welch t-test: t={t_bc:.3f}, p={pt_bc:.4f}")
    print(f"  Cohen's d={d_bc:.3f}")

    if p_bc < 0.05:
        if b.mean() > c.mean():
            verdict = "✅ CPS0' CONFIRMED (B > C, p < 0.05)"
        else:
            verdict = "❌ CPS0' REFUTED (C > B, p < 0.05)"
    else:
        if abs(d_bc) < 0.2:
            verdict = "⚖️ INCONCLUSIVE (B ≈ C, small effect)"
        elif b.mean() > c.mean():
            verdict = "🔶 CPS0' TREND (B > C, not significant)"
        else:
            verdict = "🔶 Content TREND (C > B, not significant)"

    print(f"\n  >>> {verdict}")

    # --- β_S vs β_C comparison ---
    print(f"\n--- β Comparison ---")
    print(f"  β_S (Structure effect size): d = {d_str:.3f}")
    print(f"  β_C (Content effect size):   d = {d_con:.3f}")
    if d_str > d_con:
        print(f"  → β_S > β_C: Structure has larger effect (CPS0' supportive)")
    else:
        print(f"  → β_C > β_S: Content has larger effect (against CPS0')")

    # --- ICC (multi-judge reliability) ---
    icc = compute_icc(df, score_col)
    if icc is not None:
        print(f"\n--- Inter-rater Reliability ---")
        print(f"  ICC(2,1) = {icc:.4f}")
        if icc >= 0.75:
            print("  ✅ Good reliability (ICC ≥ 0.75)")
        elif icc >= 0.50:
            print("  🔶 Moderate reliability (0.50 ≤ ICC < 0.75)")
        else:
            print("  ❌ Poor reliability (ICC < 0.50)")

    # --- Per-task analysis ---
    print("\n--- Per-Task B vs C ---")
    for task in sorted(df["task"].unique()):
        bt = df[(df["condition"] == "B_HiStr_LoCon") & (df["task"] == task)][score_col]
        ct = df[(df["condition"] == "C_LoStr_HiCon") & (df["task"] == task)][score_col]
        if len(bt) > 0 and len(ct) > 0:
            dt = cohens_d(bt, ct)
            direction = "B>C ✓" if bt.mean() > ct.mean() else "C>B ✗"
            print(f"  {task}: B={bt.mean():.3f} vs C={ct.mean():.3f}, d={dt:.3f} ({direction})")

    # --- Per-dimension analysis ---
    print("\n--- Per-Dimension B vs C ---")
    dims = ["analytical_depth", "logical_coherence", "novelty",
            "self_correction", "structural_organization", "precision"]
    for dim in dims:
        col = f"{dim}_score"
        if col not in df.columns:
            continue
        bd = df[df["condition"] == "B_HiStr_LoCon"][col]
        cd = df[df["condition"] == "C_LoStr_HiCon"][col]
        if len(bd) > 0 and len(cd) > 0:
            dd = cohens_d(bd, cd)
            direction = "B>C" if bd.mean() > cd.mean() else "C>B"
            marker = "⚠️" if dim == "structural_organization" else ""
            print(f"  {dim}: B={bd.mean():.2f} vs C={cd.mean():.2f}, d={dd:.3f} ({direction}) {marker}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="CPS0' Analysis")
    parser.add_argument("--scores", type=str, default=None)
    parser.add_argument("--score-col", default="composite_5d",
                        choices=["composite_5d", "composite_6d", "composite_3d"])
    args = parser.parse_args()

    df = load_scores(args.scores)
    analyze(df, args.score_col)


if __name__ == "__main__":
    main()
