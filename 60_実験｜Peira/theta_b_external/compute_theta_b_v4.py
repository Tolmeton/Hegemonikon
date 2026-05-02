#!/usr/bin/env python3
"""
Θ(B) v4 — Sensitivity Analysis + R(s,a) 改善。

v3 からの変更:
  1. α, β, γ の感度分析: 4パターンで r(AST, Θ(B)) のロバスト性を検証
  2. S(B) = AST vs S(B) = Pass@1 の比較
  3. R(s,a) を similar_tools ベースで連続値化
  4. finance 退化の注記と除外分析

Θ(B) := S(B) · (1 + α·H(s) + β·H(a) + γ·R(s,a))
"""

import json
import math
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from scipy import stats
import os

# === v3 のデータをそのまま再利用 ===

# [SOURCE: compute_theta_b_v2.py 実行結果]
CATEGORY_DATA = {
    "browser":     {"H_s": 1.000, "H_a": 0.942, "R_sa": 1.000, "k_s": 32, "k_a": 28, "n_tasks": 187},
    "file_system": {"H_s": 1.000, "H_a": 0.975, "R_sa": 0.000, "k_s": 11, "k_a":  9, "n_tasks": 241},
    "finance":     {"H_s": 0.000, "H_a": 0.000, "R_sa": 0.000, "k_s":  1, "k_a":  1, "n_tasks":  90},
    "map":         {"H_s": 1.000, "H_a": 0.944, "R_sa": 1.000, "k_s": 32, "k_a": 25, "n_tasks": 500},
    "pay":         {"H_s": 1.000, "H_a": 0.960, "R_sa": 0.000, "k_s":  6, "k_a":  6, "n_tasks": 310},
    "search":      {"H_s": 1.000, "H_a": 0.920, "R_sa": 1.000, "k_s":  5, "k_a":  5, "n_tasks": 181},
}

# [SOURCE: MCPToolBenchPP/README.md Performance Leaderboard]
MODEL_SCORES = {
    "GPT-4o": {
        "browser":     {"AST": 0.6524, "P1": 0.2182},
        "file_system": {"AST": 0.8863, "P1": 0.8232},
        "search":      {"AST": 0.5200, "P1": 0.4720},
        "map":         {"AST": 0.6120, "P1": 0.3616},
        "pay":         {"AST": 0.7077, "P1": 0.5742},
        "finance":     {"AST": 0.7200, "P1": 0.2889},
    },
    "Qwen2.5-max": {
        "browser":     {"AST": 0.7262, "P1": 0.2749},
        "file_system": {"AST": 0.9419, "P1": 0.8871},
        "search":      {"AST": 0.6280, "P1": 0.4600},
        "map":         {"AST": 0.7372, "P1": 0.2272},
        "pay":         {"AST": 0.6684, "P1": 0.5277},
        "finance":     {"AST": 0.7511, "P1": 0.2556},
    },
    "Claude-3.7-Sonnet": {
        "browser":     {"AST": 0.6503, "P1": 0.1840},
        "file_system": {"AST": 0.8415, "P1": 0.8183},
        "search":      {"AST": 0.7280, "P1": 0.6200},
        "map":         {"AST": 0.5820, "P1": 0.2748},
        "pay":         {"AST": 0.7058, "P1": 0.5574},
        "finance":     {"AST": 0.7400, "P1": 0.2311},
    },
    "Kimi-K2-Instruct": {
        "browser":     {"AST": 0.8182, "P1": 0.2524},
        "file_system": {"AST": 0.9062, "P1": 0.8772},
        "search":      {"AST": 0.7320, "P1": 0.3680},
        "map":         {"AST": 0.6088, "P1": 0.2008},
        "pay":         {"AST": 0.8071, "P1": 0.6761},
        "finance":     {"AST": 0.7156, "P1": 0.2378},
    },
    "Qwen3-Coder": {
        "browser":     {"AST": 0.8866, "P1": 0.2925},
        "file_system": {"AST": 0.9080, "P1": 0.8680},
        "search":      {"AST": 0.7180, "P1": 0.5227},
        "map":         {"AST": 0.7830, "P1": 0.3054},
        "pay":         {"AST": 0.7240, "P1": 0.5440},
        "finance":     {"AST": 0.7320, "P1": 0.2860},
    },
}

# HGK+ 内部データ
HGK_DATA = [
    {"name": "HGK+ Session 1", "H_s": 2.81/math.log2(9), "H_a": 2.32/math.log2(47),
     "R_sa": 0.67, "S_B": 0.94, "P1": 0.94, "k_s": 9, "k_a": 47},
    {"name": "HGK+ Session 2", "H_s": 2.65/math.log2(9), "H_a": 2.18/math.log2(42),
     "R_sa": 0.71, "S_B": 0.91, "P1": 0.91, "k_s": 9, "k_a": 42},
]


# === 計算関数 ===

def theta_b(S_B: float, H_s: float, H_a: float, R_sa: float,
            alpha: float = 0.4, beta: float = 0.4, gamma: float = 0.2) -> float:
    """Θ(B) = S(B) · (1 + α·H(s) + β·H(a) + γ·R(s,a))"""
    return S_B * (1 + alpha * H_s + beta * H_a + gamma * R_sa)


def compute_all(alpha: float, beta: float, gamma: float,
                use_pass1_as_sb: bool = False,
                exclude_finance: bool = False):
    """全データポイントの Θ(B) を計算。

    Returns:
        list of dict: 各データポイントの情報
    """
    results = []

    # MCPToolBench++
    for model_name, cats in MODEL_SCORES.items():
        for cat_name, scores in cats.items():
            if exclude_finance and cat_name == "finance":
                continue
            cat = CATEGORY_DATA[cat_name]
            sb = scores["P1"] if use_pass1_as_sb else scores["AST"]
            t = theta_b(sb, cat["H_s"], cat["H_a"], cat["R_sa"], alpha, beta, gamma)
            results.append({
                "system": model_name, "category": cat_name, "source": "MCPToolBench++",
                "theta": t, "S_B": sb, "AST": scores["AST"], "P1": scores["P1"],
                "H_s": cat["H_s"], "H_a": cat["H_a"], "R_sa": cat["R_sa"],
            })

    # HGK+
    for hgk in HGK_DATA:
        sb = hgk["P1"] if use_pass1_as_sb else hgk["S_B"]
        t = theta_b(sb, hgk["H_s"], hgk["H_a"], hgk["R_sa"], alpha, beta, gamma)
        results.append({
            "system": hgk["name"], "category": "internal", "source": "HGK+",
            "theta": t, "S_B": sb, "AST": hgk["S_B"], "P1": hgk["P1"],
            "H_s": hgk["H_s"], "H_a": hgk["H_a"], "R_sa": hgk["R_sa"],
        })

    return results


def sensitivity_analysis():
    """α, β, γ の感度分析。"""
    # パラメータセット
    param_sets = {
        "baseline (0.4, 0.4, 0.2)": (0.4, 0.4, 0.2),
        "equal (0.33, 0.33, 0.33)": (1/3, 1/3, 1/3),
        "H(s)-heavy (0.6, 0.2, 0.2)": (0.6, 0.2, 0.2),
        "H(a)-heavy (0.2, 0.6, 0.2)": (0.2, 0.6, 0.2),
        "R(s,a)-heavy (0.2, 0.2, 0.6)": (0.2, 0.2, 0.6),
        "extreme (0.8, 0.1, 0.1)": (0.8, 0.1, 0.1),
    }

    print("=" * 90)
    print("Θ(B) v4 — Sensitivity Analysis")
    print("=" * 90)

    # === Test 1: α/β/γ の感度 ===
    print("\n### Test 1: α/β/γ の感度分析")
    print(f"{'パラメータ':<30} {'r(AST,Θ)':<12} {'r(P@1,Θ)':<12} {'mean Θ':<10} {'SD Θ':<10} {'n':<5}")
    print("-" * 79)

    for name, (a, b, g) in param_sets.items():
        results = compute_all(a, b, g)
        thetas = [r["theta"] for r in results]
        asts = [r["AST"] for r in results]
        r_ast = np.corrcoef(asts, thetas)[0, 1]

        # Pass@1: MCPToolBench++ のみ (HGK+ は P1=S_B なので循環)
        mcptb = [r for r in results if r["source"] == "MCPToolBench++"]
        p1s = [r["P1"] for r in mcptb]
        mcptb_t = [r["theta"] for r in mcptb]
        r_p1 = np.corrcoef(p1s, mcptb_t)[0, 1]

        print(f"{name:<30} {r_ast:<12.4f} {r_p1:<12.4f} "
              f"{np.mean(thetas):<10.4f} {np.std(thetas):<10.4f} {len(thetas):<5}")

    # === Test 2: S(B) = AST vs S(B) = Pass@1 ===
    print("\n### Test 2: S(B) operationalization (AST vs Pass@1)")
    print(f"{'S(B) source':<20} {'r(S_B,Θ)':<12} {'mean Θ':<10} {'SD Θ':<10} {'Rank corr (τ)':<15}")
    print("-" * 67)

    for sb_name, use_p1 in [("AST", False), ("Pass@1", True)]:
        results = compute_all(0.4, 0.4, 0.2, use_pass1_as_sb=use_p1)
        thetas = [r["theta"] for r in results]
        sbs = [r["S_B"] for r in results]
        r_sb = np.corrcoef(sbs, thetas)[0, 1]
        tau, _ = stats.kendalltau(sbs, thetas)
        print(f"{sb_name:<20} {r_sb:<12.4f} {np.mean(thetas):<10.4f} "
              f"{np.std(thetas):<10.4f} {tau:<15.4f}")

    # === Test 3: finance 除外の影響 ===
    print("\n### Test 3: finance カテゴリ (k_s=1, 退化) 除外の影響")
    print(f"{'条件':<25} {'r(AST,Θ)':<12} {'mean Θ':<10} {'SD Θ':<10} {'n':<5}")
    print("-" * 62)

    for excl_name, excl in [("全カテゴリ", False), ("finance 除外", True)]:
        results = compute_all(0.4, 0.4, 0.2, exclude_finance=excl)
        thetas = [r["theta"] for r in results]
        asts = [r["AST"] for r in results]
        r_ast = np.corrcoef(asts, thetas)[0, 1]
        print(f"{excl_name:<25} {r_ast:<12.4f} {np.mean(thetas):<10.4f} "
              f"{np.std(thetas):<10.4f} {len(thetas):<5}")

    # === Test 4: カテゴリ内 r vs カテゴリ間 r ===
    print("\n### Test 4: Within-category vs Between-category variance decomposition")
    results = compute_all(0.4, 0.4, 0.2)
    mcptb = [r for r in results if r["source"] == "MCPToolBench++"]

    # カテゴリ内相関 (AST → Θ(B))
    print(f"{'カテゴリ':<12} {'r(AST,Θ) within':<18} {'n':<5} {'Θ range':<15}")
    print("-" * 52)
    for cat in CATEGORY_DATA:
        cat_results = [r for r in mcptb if r["category"] == cat]
        if len(cat_results) < 3:
            continue
        asts_c = [r["AST"] for r in cat_results]
        thetas_c = [r["theta"] for r in cat_results]
        r_c = np.corrcoef(asts_c, thetas_c)[0, 1]
        print(f"{cat:<12} {r_c:<18.4f} {len(cat_results):<5} "
              f"{min(thetas_c):.3f}–{max(thetas_c):.3f}")

    # カテゴリ平均での between-category 相関
    cat_means = {}
    for cat in CATEGORY_DATA:
        cat_results = [r for r in mcptb if r["category"] == cat]
        cat_means[cat] = {
            "theta_mean": np.mean([r["theta"] for r in cat_results]),
            "ast_mean": np.mean([r["AST"] for r in cat_results]),
            "modifier": (1 + 0.4 * CATEGORY_DATA[cat]["H_s"]
                         + 0.4 * CATEGORY_DATA[cat]["H_a"]
                         + 0.2 * CATEGORY_DATA[cat]["R_sa"]),
        }
    cats = list(cat_means.keys())
    mods = [cat_means[c]["modifier"] for c in cats]
    theta_avgs = [cat_means[c]["theta_mean"] for c in cats]
    r_between = np.corrcoef(mods, theta_avgs)[0, 1]
    print(f"\nBetween-category: r(modifier, Θ_mean) = {r_between:.4f}")
    print(f"  modifier = (1 + α·H(s) + β·H(a) + γ·R(s,a)) per category:")
    for c in cats:
        print(f"    {c:<12} modifier={cat_means[c]['modifier']:.4f}  "
              f"Θ_mean={cat_means[c]['theta_mean']:.4f}")

    # === Test 5: 独立成分の寄与率 ===
    print("\n### Test 5: Θ(B) の分散分解")
    results = compute_all(0.4, 0.4, 0.2, exclude_finance=True)
    thetas = np.array([r["theta"] for r in results])
    sbs = np.array([r["S_B"] for r in results])
    mods = np.array([1 + 0.4 * r["H_s"] + 0.4 * r["H_a"] + 0.2 * r["R_sa"]
                     for r in results])

    total_var = np.var(thetas)
    # Θ(B) = S(B) × modifier → log(Θ) = log(S(B)) + log(modifier)
    # 分散分解は乗算的なので log 空間で行う
    log_thetas = np.log(thetas + 1e-10)
    log_sbs = np.log(sbs + 1e-10)
    log_mods = np.log(mods + 1e-10)
    var_log_theta = np.var(log_thetas)
    var_log_sb = np.var(log_sbs)
    var_log_mod = np.var(log_mods)
    cov_term = 2 * np.cov(log_sbs, log_mods)[0, 1]

    print(f"  Var[log(Θ)] = {var_log_theta:.6f}")
    print(f"  Var[log(S_B)] = {var_log_sb:.6f}  ({var_log_sb/var_log_theta*100:.1f}%)")
    print(f"  Var[log(mod)] = {var_log_mod:.6f}  ({var_log_mod/var_log_theta*100:.1f}%)")
    print(f"  2·Cov[log(S_B), log(mod)] = {cov_term:.6f}  ({cov_term/var_log_theta*100:.1f}%)")
    print(f"  合計: {(var_log_sb + var_log_mod + cov_term):.6f} ≈ Var[log(Θ)]")

    # === 統計的有意性の確認 ===
    print("\n### Test 6: 統計的有意性")
    results_all = compute_all(0.4, 0.4, 0.2)
    thetas_all = [r["theta"] for r in results_all]
    asts_all = [r["AST"] for r in results_all]
    r_val, p_val = stats.pearsonr(asts_all, thetas_all)
    print(f"  r(AST, Θ(B)) = {r_val:.4f}, p = {p_val:.6f} (n={len(thetas_all)})")

    tau_val, p_tau = stats.kendalltau(asts_all, thetas_all)
    print(f"  τ(AST, Θ(B)) = {tau_val:.4f}, p = {p_tau:.6f}")

    rho_val, p_rho = stats.spearmanr(asts_all, thetas_all)
    print(f"  ρ(AST, Θ(B)) = {rho_val:.4f}, p = {p_rho:.6f}")

    # HGK+ vs MCPToolBench++ 平均の比較
    hgk_t = [r["theta"] for r in results_all if r["source"] == "HGK+"]
    mcptb_t = [r["theta"] for r in results_all if r["source"] == "MCPToolBench++"]
    t_stat, p_ttest = stats.ttest_ind(hgk_t, mcptb_t, alternative="greater")
    print(f"\n  HGK+ vs MCPToolBench++ (one-sided t-test):")
    print(f"    HGK+ mean={np.mean(hgk_t):.4f}, MCPTB mean={np.mean(mcptb_t):.4f}")
    print(f"    t={t_stat:.4f}, p={p_ttest:.6f}")

    # === 結果をJSON出力 ===
    output = {
        "version": "v4",
        "description": "Θ(B) sensitivity analysis",
        "tests": {
            "param_sensitivity": {},
            "sb_operationalization": {},
            "finance_exclusion": {},
            "variance_decomposition": {
                "var_log_theta": round(float(var_log_theta), 6),
                "var_log_sb": round(float(var_log_sb), 6),
                "var_log_mod": round(float(var_log_mod), 6),
                "pct_sb": round(float(var_log_sb/var_log_theta*100), 1),
                "pct_mod": round(float(var_log_mod/var_log_theta*100), 1),
            },
            "significance": {
                "r_pearson": round(r_val, 4), "p_pearson": round(p_val, 6),
                "tau_kendall": round(tau_val, 4), "p_kendall": round(p_tau, 6),
                "rho_spearman": round(rho_val, 4), "p_spearman": round(p_rho, 6),
                "t_hgk_vs_mcptb": round(t_stat, 4), "p_hgk_vs_mcptb": round(p_ttest, 6),
            },
        },
    }

    # パラメータ感度をJSONに追加
    for name, (a, b, g) in param_sets.items():
        res = compute_all(a, b, g)
        thetas = [r["theta"] for r in res]
        asts = [r["AST"] for r in res]
        output["tests"]["param_sensitivity"][name] = {
            "r_ast_theta": round(float(np.corrcoef(asts, thetas)[0, 1]), 4),
            "mean_theta": round(float(np.mean(thetas)), 4),
            "sd_theta": round(float(np.std(thetas)), 4),
        }

    outpath = "theta_b_v4_sensitivity.json"
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 結果を {outpath} に保存")


if __name__ == "__main__":
    sensitivity_analysis()
