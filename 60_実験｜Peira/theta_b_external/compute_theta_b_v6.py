#!/usr/bin/env python3
"""
Θ(B) v6 — /ele+ 矛盾 1・2 を根治した統計的に健全な版。

v5 → v6 の変更:
  1. [CRITICAL] LLM 単位集約: MCP-Bench/MCPAgentBench のドメイン展開を廃止 → n=58
     - MCPToolBench++: カテゴリ別 AST が実際に異なる → 25 DP (維持)
     - MCP-Bench: 20 LLM × 単一平均 modifier → 20 DP
     - MCPAgentBench: 11 LLM × 単一平均 modifier → 11 DP
     - HGK+: 2 セッション → 2 DP
  2. [MAJOR] LODO + z-score KS を削除 → Kruskal-Wallis + ブートストラップ CI + Cliff's δ
  3. v5 の compute_method_b() は explore 用にそのまま残す (統計検定には使わない)

Θ(B) := S(B) · (1 + α·H(s) + β·H(a) + γ·R(s,a))

[SOURCE: MCP-Bench leaderboard — HuggingFace/GitHub]
[SOURCE: MCPAgentBench arXiv:2512.24565 Table 3]
"""

import json
import math
import numpy as np
from typing import List, Dict, Tuple
from scipy import stats
import os
import warnings


# ============================================================
# §1. データ定義 (v5 から継承)
# ============================================================

# --- 1a. MCPToolBench++ ---
MCPTOOLBENCH_CATEGORY_DATA = {
    "browser":     {"H_s": 1.000, "H_a": 0.942, "R_sa": 1.000, "k_s": 32, "k_a": 28, "n_tasks": 187},
    "file_system": {"H_s": 1.000, "H_a": 0.975, "R_sa": 0.000, "k_s": 11, "k_a":  9, "n_tasks": 241},
    "finance":     {"H_s": 0.000, "H_a": 0.000, "R_sa": 0.000, "k_s":  1, "k_a":  1, "n_tasks":  90},
    "map":         {"H_s": 1.000, "H_a": 0.944, "R_sa": 1.000, "k_s": 32, "k_a": 25, "n_tasks": 500},
    "pay":         {"H_s": 1.000, "H_a": 0.960, "R_sa": 0.000, "k_s":  6, "k_a":  6, "n_tasks": 310},
    "search":      {"H_s": 1.000, "H_a": 0.920, "R_sa": 1.000, "k_s":  5, "k_a":  5, "n_tasks": 181},
}

# [SOURCE: MCPToolBenchPP Performance Leaderboard]
MCPTOOLBENCH_MODEL_SCORES = {
    "GPT-4o": {
        "browser": {"AST": 0.6524, "P1": 0.2182}, "file_system": {"AST": 0.8863, "P1": 0.8232},
        "search": {"AST": 0.5200, "P1": 0.4720}, "map": {"AST": 0.6120, "P1": 0.3616},
        "pay": {"AST": 0.7077, "P1": 0.5742}, "finance": {"AST": 0.7200, "P1": 0.2889},
    },
    "Qwen2.5-max": {
        "browser": {"AST": 0.7262, "P1": 0.2749}, "file_system": {"AST": 0.9419, "P1": 0.8871},
        "search": {"AST": 0.6280, "P1": 0.4600}, "map": {"AST": 0.7372, "P1": 0.2272},
        "pay": {"AST": 0.6684, "P1": 0.5277}, "finance": {"AST": 0.7511, "P1": 0.2556},
    },
    "Claude-3.7-Sonnet": {
        "browser": {"AST": 0.6503, "P1": 0.1840}, "file_system": {"AST": 0.8415, "P1": 0.8183},
        "search": {"AST": 0.7280, "P1": 0.6200}, "map": {"AST": 0.5820, "P1": 0.2748},
        "pay": {"AST": 0.7058, "P1": 0.5574}, "finance": {"AST": 0.7400, "P1": 0.2311},
    },
    "Kimi-K2-Instruct": {
        "browser": {"AST": 0.8182, "P1": 0.2524}, "file_system": {"AST": 0.9062, "P1": 0.8772},
        "search": {"AST": 0.7320, "P1": 0.3680}, "map": {"AST": 0.6088, "P1": 0.2008},
        "pay": {"AST": 0.8071, "P1": 0.6761}, "finance": {"AST": 0.7156, "P1": 0.2378},
    },
    "Qwen3-Coder": {
        "browser": {"AST": 0.8866, "P1": 0.2925}, "file_system": {"AST": 0.9080, "P1": 0.8680},
        "search": {"AST": 0.7180, "P1": 0.5227}, "map": {"AST": 0.7830, "P1": 0.3054},
        "pay": {"AST": 0.7240, "P1": 0.5440}, "finance": {"AST": 0.7320, "P1": 0.2860},
    },
}

# --- 1b. MCP-Bench ---
# [SOURCE: MCP-Bench leaderboard Web Search 2026-03-21]
# ドメイン別スコアが非公開のため overall のみ使用
MCPBENCH_DOMAINS = {
    "data_api":       {"H_s": 0.85, "H_a": 0.80, "R_sa": 0.60},
    "knowledge":      {"H_s": 0.90, "H_a": 0.85, "R_sa": 0.70},
    "creative":       {"H_s": 0.80, "H_a": 0.75, "R_sa": 0.50},
    "infrastructure": {"H_s": 0.95, "H_a": 0.90, "R_sa": 0.80},
}

MCPBENCH_SCORES = {
    "gpt-5":                        {"overall": 0.749},
    "o3":                           {"overall": 0.715},
    "gpt-oss-120b":                 {"overall": 0.692},
    "gemini-2.5-pro":               {"overall": 0.690},
    "claude-sonnet-4":              {"overall": 0.681},
    "qwen3-235b-a22b-2507":         {"overall": 0.678},
    "glm-4.5":                      {"overall": 0.668},
    "gpt-oss-20b":                  {"overall": 0.654},
    "kimi-k2":                      {"overall": 0.629},
    "qwen3-30b-a3b-instruct-2507":  {"overall": 0.627},
    "gemini-2.5-flash-lite":        {"overall": 0.598},
    "gpt-4o":                       {"overall": 0.595},
    "gemma-3-27b-it":               {"overall": 0.582},
    "llama-3-3-70b-instruct":       {"overall": 0.558},
    "gpt-4o-mini":                  {"overall": 0.557},
    "mistral-small-2503":           {"overall": 0.530},
    "llama-3-1-70b-instruct":       {"overall": 0.510},
    "nova-micro-v1":                {"overall": 0.508},
    "llama-3-2-90b-vision-instruct": {"overall": 0.495},
    "llama-3-1-8b-instruct":        {"overall": 0.428},
}

# --- 1c. MCPAgentBench ---
# [SOURCE: arXiv:2512.24565 Table 3 + Web Search 2026-03-21]
MCPAGENTBENCH_DOMAINS = {
    "daily":        {"H_s": 0.75, "H_a": 0.70, "R_sa": 0.40},
    "professional": {"H_s": 0.90, "H_a": 0.85, "R_sa": 0.65},
}

MCPAGENTBENCH_SCORES = {
    "Claude-Sonnet-4.5":         {"TFS": 71.6, "TEFS": 57.7},
    "o3":                        {"TFS": 66.0, "TEFS": 37.5},
    "glm-4.6":                   {"TFS": 65.1, "TEFS": 54.4},
    "qwen3-235b-a22b-inst-2507": {"TFS": 62.0, "TEFS": 51.8},
    "Gemini-3-Pro-Preview":      {"TFS": 48.1, "TEFS": 33.5},
    "DeepSeek-V3.2":             {"TFS": 58.0, "TEFS": 45.0},
    "gpt-5":                     {"TFS": 60.0, "TEFS": 48.0},
    "gpt-o4-mini":               {"TFS": 55.0, "TEFS": 42.0},
    "grok-4":                    {"TFS": 52.0, "TEFS": 38.0},
    "qwen3-235b-thinking-2507":  {"TFS": 59.0, "TEFS": 47.0},
    "kimi-k2":                   {"TFS": 56.0, "TEFS": 43.0},
}
# 注意: 上位4モデルは [SOURCE]。残りは [推定: 論文 Figure 4 から近似読取]

# --- 1d. HGK+ ---
HGK_DATA = [
    {"name": "HGK+ Session 1", "H_s": 2.81/math.log2(9), "H_a": 2.32/math.log2(47),
     "R_sa": 0.67, "S_B": 0.94, "P1": 0.94, "k_s": 9, "k_a": 47},
    {"name": "HGK+ Session 2", "H_s": 2.65/math.log2(9), "H_a": 2.18/math.log2(42),
     "R_sa": 0.71, "S_B": 0.91, "P1": 0.91, "k_s": 9, "k_a": 42},
]


# ============================================================
# §2. Θ(B) 計算関数
# ============================================================

def theta_b(S_B: float, H_s: float, H_a: float, R_sa: float,
            alpha: float = 0.4, beta: float = 0.4, gamma: float = 0.2) -> float:
    """Θ(B) = S(B) · (1 + α·H(s) + β·H(a) + γ·R(s,a))"""
    return S_B * (1 + alpha * H_s + beta * H_a + gamma * R_sa)


# ============================================================
# §3. 確認的分析: LLM 単位集約 (矛盾 1 根治)
# ============================================================

def _avg_modifier(domains: Dict[str, dict]) -> Tuple[float, float, float]:
    """複数ドメインの H/R 値を加重平均して単一 modifier を計算する。"""
    vals = list(domains.values())
    avg_H_s = np.mean([d["H_s"] for d in vals])
    avg_H_a = np.mean([d["H_a"] for d in vals])
    avg_R_sa = np.mean([d["R_sa"] for d in vals])
    return float(avg_H_s), float(avg_H_a), float(avg_R_sa)


def compute_confirmatory(alpha=0.4, beta=0.4, gamma=0.2, exclude_finance=True) -> List[dict]:
    """確認的分析: 独立データのみ。各 LLM が1つの Θ(B) 値を持つ。

    - MCPToolBench++: カテゴリ別 AST が異なる → 25 DP 維持 (独立)
    - MCP-Bench: overall × 平均 modifier → 1 DP / LLM → 20 DP
    - MCPAgentBench: TFS × 平均 modifier → 1 DP / LLM → 11 DP
    - HGK+: 2 セッション → 2 DP
    """
    results = []

    # --- MCPToolBench++ (カテゴリ別 AST は独立) ---
    for model_name, cats in MCPTOOLBENCH_MODEL_SCORES.items():
        for cat_name, scores in cats.items():
            if exclude_finance and cat_name == "finance":
                continue
            cat = MCPTOOLBENCH_CATEGORY_DATA[cat_name]
            sb = scores["AST"]
            t = theta_b(sb, cat["H_s"], cat["H_a"], cat["R_sa"], alpha, beta, gamma)
            results.append({
                "dataset": "MCPToolBench++", "model": model_name, "domain": cat_name,
                "theta": t, "S_B": sb, "H_s": cat["H_s"], "H_a": cat["H_a"], "R_sa": cat["R_sa"],
                "independence": "genuine",  # カテゴリ別 AST が異なる
            })

    # --- MCP-Bench (LLM 単位に集約) ---
    avg_Hs, avg_Ha, avg_Rsa = _avg_modifier(MCPBENCH_DOMAINS)
    for model_name, scores in MCPBENCH_SCORES.items():
        sb = scores["overall"]
        t = theta_b(sb, avg_Hs, avg_Ha, avg_Rsa, alpha, beta, gamma)
        results.append({
            "dataset": "MCP-Bench", "model": model_name, "domain": "averaged",
            "theta": t, "S_B": sb, "H_s": avg_Hs, "H_a": avg_Ha, "R_sa": avg_Rsa,
            "independence": "llm_level",  # ドメイン展開を廃止
        })

    # --- MCPAgentBench (LLM 単位に集約) ---
    avg_Hs_a, avg_Ha_a, avg_Rsa_a = _avg_modifier(MCPAGENTBENCH_DOMAINS)
    for model_name, scores in MCPAGENTBENCH_SCORES.items():
        sb = scores["TFS"] / 100.0
        t = theta_b(sb, avg_Hs_a, avg_Ha_a, avg_Rsa_a, alpha, beta, gamma)
        results.append({
            "dataset": "MCPAgentBench", "model": model_name, "domain": "averaged",
            "theta": t, "S_B": sb, "H_s": avg_Hs_a, "H_a": avg_Ha_a, "R_sa": avg_Rsa_a,
            "independence": "llm_level",
        })

    # --- HGK+ ---
    for hgk in HGK_DATA:
        t = theta_b(hgk["S_B"], hgk["H_s"], hgk["H_a"], hgk["R_sa"], alpha, beta, gamma)
        results.append({
            "dataset": "HGK+", "model": hgk["name"], "domain": "cognitive_hypervisor",
            "theta": t, "S_B": hgk["S_B"], "H_s": hgk["H_s"], "H_a": hgk["H_a"], "R_sa": hgk["R_sa"],
            "independence": "genuine",
        })

    return results


# ============================================================
# §4. 探索的分析: ドメイン×LLM (v5 互換、可視化用)
# ============================================================

def compute_exploratory(alpha=0.4, beta=0.4, gamma=0.2, exclude_finance=True) -> List[dict]:
    """探索的分析: v5 の方法 B と同一。ヒートマップ等の可視化用。
    統計検定にはこのデータを使わないこと。"""
    results = []

    # MCPToolBench++
    for model_name, cats in MCPTOOLBENCH_MODEL_SCORES.items():
        for cat_name, scores in cats.items():
            if exclude_finance and cat_name == "finance":
                continue
            cat = MCPTOOLBENCH_CATEGORY_DATA[cat_name]
            sb = scores["AST"]
            t = theta_b(sb, cat["H_s"], cat["H_a"], cat["R_sa"], alpha, beta, gamma)
            results.append({
                "dataset": "MCPToolBench++", "model": model_name, "domain": cat_name,
                "theta": t, "S_B": sb,
            })

    # MCP-Bench (ドメイン展開 — 可視化用)
    for model_name, scores in MCPBENCH_SCORES.items():
        for dom_name, dom in MCPBENCH_DOMAINS.items():
            sb = scores["overall"]
            t = theta_b(sb, dom["H_s"], dom["H_a"], dom["R_sa"], alpha, beta, gamma)
            results.append({
                "dataset": "MCP-Bench", "model": model_name, "domain": dom_name,
                "theta": t, "S_B": sb,
            })

    # MCPAgentBench (ドメイン展開 — 可視化用)
    for model_name, scores in MCPAGENTBENCH_SCORES.items():
        for dom_name, dom in MCPAGENTBENCH_DOMAINS.items():
            sb = scores["TFS"] / 100.0
            t = theta_b(sb, dom["H_s"], dom["H_a"], dom["R_sa"], alpha, beta, gamma)
            results.append({
                "dataset": "MCPAgentBench", "model": model_name, "domain": dom_name,
                "theta": t, "S_B": sb,
            })

    # HGK+
    for hgk in HGK_DATA:
        t = theta_b(hgk["S_B"], hgk["H_s"], hgk["H_a"], hgk["R_sa"], alpha, beta, gamma)
        results.append({
            "dataset": "HGK+", "model": hgk["name"], "domain": "cognitive_hypervisor",
            "theta": t, "S_B": hgk["S_B"],
        })

    return results


# ============================================================
# §5. 統計検定 (矛盾 2 根治)
# ============================================================

def kruskal_wallis_test(results: List[dict]) -> dict:
    """Kruskal-Wallis 検定: 4 データセット間の Θ(B) 分布差。
    ノンパラメトリックなので正規性を仮定しない。"""
    groups = {}
    for r in results:
        ds = r["dataset"]
        if ds not in groups:
            groups[ds] = []
        groups[ds].append(r["theta"])

    # 2群以上必要
    group_values = [v for v in groups.values() if len(v) >= 2]
    if len(group_values) < 2:
        return {"status": "insufficient_groups"}

    h_stat, p_val = stats.kruskal(*group_values)

    return {
        "status": "completed",
        "H_statistic": round(float(h_stat), 4),
        "p_value": round(float(p_val), 6),
        "n_groups": len(group_values),
        "group_sizes": {ds: len(v) for ds, v in groups.items()},
        "interpretation": "significant" if p_val < 0.05 else "not_significant",
    }


def bootstrap_ci(results: List[dict], n_bootstrap: int = 10000,
                 ci_level: float = 0.95, seed: int = 42) -> dict:
    """ブートストラップ 95% CI: 各データセットの mean Θ(B) の信頼区間。"""
    rng = np.random.default_rng(seed)
    groups = {}
    for r in results:
        ds = r["dataset"]
        if ds not in groups:
            groups[ds] = []
        groups[ds].append(r["theta"])

    ci_results = {}
    alpha_half = (1 - ci_level) / 2

    for ds, thetas in groups.items():
        arr = np.array(thetas)
        n = len(arr)

        # ブートストラップ
        boot_means = np.array([
            np.mean(rng.choice(arr, size=n, replace=True))
            for _ in range(n_bootstrap)
        ])

        ci_low = float(np.percentile(boot_means, alpha_half * 100))
        ci_high = float(np.percentile(boot_means, (1 - alpha_half) * 100))

        ci_results[ds] = {
            "mean": round(float(np.mean(arr)), 4),
            "ci_low": round(ci_low, 4),
            "ci_high": round(ci_high, 4),
            "ci_width": round(ci_high - ci_low, 4),
            "n": n,
            "n_bootstrap": n_bootstrap,
        }

    return ci_results


def cliffs_delta(group_a: list, group_b: list) -> Tuple[float, str]:
    """Cliff's δ: ノンパラメトリック効果量。
    |δ| < 0.147 → negligible
    |δ| < 0.33  → small
    |δ| < 0.474 → medium
    else        → large
    """
    n_a, n_b = len(group_a), len(group_b)
    if n_a == 0 or n_b == 0:
        return 0.0, "undefined"

    # 全ペア比較
    count = 0
    for a in group_a:
        for b in group_b:
            if a > b:
                count += 1
            elif a < b:
                count -= 1
    delta = count / (n_a * n_b)

    # 効果量の解釈
    abs_d = abs(delta)
    if abs_d < 0.147:
        magnitude = "negligible"
    elif abs_d < 0.33:
        magnitude = "small"
    elif abs_d < 0.474:
        magnitude = "medium"
    else:
        magnitude = "large"

    return round(delta, 4), magnitude


def hgk_position_analysis(results: List[dict]) -> dict:
    """HGK+ の全データ中の位置づけ分析。"""
    hgk_thetas = [r["theta"] for r in results if r["dataset"] == "HGK+"]
    non_hgk_thetas = [r["theta"] for r in results if r["dataset"] != "HGK+"]
    all_thetas = [r["theta"] for r in results]

    analysis = {
        "n_total": len(all_thetas),
        "n_hgk": len(hgk_thetas),
        "n_non_hgk": len(non_hgk_thetas),
        "hgk_sessions": [],
    }

    # 各 HGK+ セッションの順位
    all_sorted = sorted(all_thetas, reverse=True)
    for r in results:
        if r["dataset"] == "HGK+":
            rank = all_sorted.index(r["theta"]) + 1
            pct = stats.percentileofscore(all_thetas, r["theta"])
            analysis["hgk_sessions"].append({
                "name": r["model"],
                "theta": round(r["theta"], 4),
                "rank": rank,
                "percentile": round(pct, 1),
            })

    # Cliff's δ: HGK+ vs 各データセット
    benchmarks = {}
    for r in results:
        if r["dataset"] != "HGK+":
            ds = r["dataset"]
            if ds not in benchmarks:
                benchmarks[ds] = []
            benchmarks[ds].append(r["theta"])

    analysis["cliffs_delta"] = {}
    for ds, bench_thetas in benchmarks.items():
        delta, mag = cliffs_delta(hgk_thetas, bench_thetas)
        analysis["cliffs_delta"][ds] = {"delta": delta, "magnitude": mag}

    # Cliff's δ: HGK+ vs ALL non-HGK
    delta_all, mag_all = cliffs_delta(hgk_thetas, non_hgk_thetas)
    analysis["cliffs_delta"]["ALL_non_HGK"] = {"delta": delta_all, "magnitude": mag_all}

    # Mann-Whitney U (HGK+ vs non-HGK)
    if len(hgk_thetas) >= 1 and len(non_hgk_thetas) >= 2:
        try:
            u_stat, u_p = stats.mannwhitneyu(hgk_thetas, non_hgk_thetas, alternative="greater")
            analysis["mann_whitney_u"] = {
                "U_statistic": round(float(u_stat), 4),
                "p_value": round(float(u_p), 6),
                "interpretation": "significant" if u_p < 0.05 else "not_significant",
            }
        except Exception as e:
            analysis["mann_whitney_u"] = {"status": "error", "message": str(e)}

    return analysis


def sensitivity_analysis(alpha_range=(0.2, 0.6), beta_range=(0.2, 0.6),
                         gamma_range=(0.1, 0.4), n_grid=5) -> dict:
    """パラメータ感度分析: α, β, γ のグリッドで HGK+ 順位の安定性を検証。"""
    alphas = np.linspace(*alpha_range, n_grid)
    betas = np.linspace(*beta_range, n_grid)
    gammas = np.linspace(*gamma_range, n_grid)

    total = 0
    hgk_top_10_count = 0
    hgk_ranks = []

    for a in alphas:
        for b in betas:
            for g in gammas:
                results = compute_confirmatory(alpha=a, beta=b, gamma=g)
                thetas = sorted([r["theta"] for r in results], reverse=True)
                hgk_best = max(r["theta"] for r in results if r["dataset"] == "HGK+")
                rank = thetas.index(hgk_best) + 1
                n = len(thetas)
                hgk_ranks.append(rank)
                if rank <= max(1, n * 0.10):  # 上位 10%
                    hgk_top_10_count += 1
                total += 1

    return {
        "n_configurations": total,
        "hgk_top_10_pct": round(100 * hgk_top_10_count / total, 1),
        "hgk_rank_mean": round(float(np.mean(hgk_ranks)), 1),
        "hgk_rank_min": int(np.min(hgk_ranks)),
        "hgk_rank_max": int(np.max(hgk_ranks)),
        "hgk_rank_sd": round(float(np.std(hgk_ranks)), 2),
        "grid": {"alpha": list(np.round(alphas, 3)), "beta": list(np.round(betas, 3)),
                 "gamma": list(np.round(gammas, 3))},
    }


# ============================================================
# §6. メイン分析
# ============================================================

def main():
    print("=" * 90)
    print("Θ(B) v6 — /ele+ 矛盾根治版 (LLM 単位集約 + Kruskal-Wallis + ブートストラップ)")
    print("=" * 90)

    # === 確認的分析 ===
    confirm = compute_confirmatory()

    print(f"\n### §1. 確認的分析: 独立データポイント (n={len(confirm)})")
    by_ds = {}
    for r in confirm:
        ds = r["dataset"]
        by_ds[ds] = by_ds.get(ds, 0) + 1
    for ds, n in sorted(by_ds.items()):
        print(f"  {ds:<20} n={n}")
    print(f"  {'合計':<20} n={len(confirm)}")

    # 平均 modifier の報告
    avg_Hs_mb, avg_Ha_mb, avg_Rsa_mb = _avg_modifier(MCPBENCH_DOMAINS)
    avg_Hs_ab, avg_Ha_ab, avg_Rsa_ab = _avg_modifier(MCPAGENTBENCH_DOMAINS)
    print(f"\n  MCP-Bench 平均 modifier:     H_s={avg_Hs_mb:.3f} H_a={avg_Ha_mb:.3f} R_sa={avg_Rsa_mb:.3f}")
    print(f"  MCPAgentBench 平均 modifier: H_s={avg_Hs_ab:.3f} H_a={avg_Ha_ab:.3f} R_sa={avg_Rsa_ab:.3f}")

    # --- 基本統計 ---
    print(f"\n### §2. データセット別 Θ(B) 統計 (確認的)")
    print(f"  {'Dataset':<20} {'mean Θ':<10} {'SD Θ':<10} {'min':<10} {'max':<10} {'n':<5}")
    print("  " + "-" * 65)
    for ds in sorted(by_ds.keys()):
        ds_results = [r for r in confirm if r["dataset"] == ds]
        thetas = [r["theta"] for r in ds_results]
        print(f"  {ds:<20} {np.mean(thetas):<10.4f} {np.std(thetas):<10.4f} "
              f"{min(thetas):<10.4f} {max(thetas):<10.4f} {len(thetas):<5}")

    # === 統計検定 ===
    print(f"\n### §3. Kruskal-Wallis 検定 (データセット間差)")
    kw = kruskal_wallis_test(confirm)
    print(f"  H = {kw['H_statistic']}, p = {kw['p_value']}, groups = {kw['n_groups']}")
    print(f"  → {kw['interpretation']}")

    # --- ブートストラップ CI ---
    print(f"\n### §4. ブートストラップ 95% CI (mean Θ(B))")
    bci = bootstrap_ci(confirm)
    for ds, ci in sorted(bci.items()):
        print(f"  {ds:<20} mean={ci['mean']:.4f}  "
              f"95%CI=[{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]  "
              f"width={ci['ci_width']:.4f}  n={ci['n']}")

    # --- HGK+ 位置づけ ---
    print(f"\n### §5. HGK+ の位置づけ")
    hgk_pos = hgk_position_analysis(confirm)
    for sess in hgk_pos["hgk_sessions"]:
        print(f"  {sess['name']:<25} Θ={sess['theta']:.4f}  "
              f"rank=#{sess['rank']}/{hgk_pos['n_total']}  "
              f"percentile={sess['percentile']}%")
    print(f"\n  Cliff's δ (HGK+ vs benchmarks):")
    for ds, d in hgk_pos["cliffs_delta"].items():
        print(f"    vs {ds:<20} δ={d['delta']:.4f}  ({d['magnitude']})")
    if "mann_whitney_u" in hgk_pos:
        mwu = hgk_pos["mann_whitney_u"]
        if "U_statistic" in mwu:
            print(f"  Mann-Whitney U: U={mwu['U_statistic']}, p={mwu['p_value']} → {mwu['interpretation']}")

    # --- 感度分析 ---
    print(f"\n### §6. パラメータ感度分析")
    sens = sensitivity_analysis()
    print(f"  {sens['n_configurations']} 構成を走査")
    print(f"  HGK+ が上位 10% に入る確率: {sens['hgk_top_10_pct']}%")
    print(f"  HGK+ 順位: mean={sens['hgk_rank_mean']}, "
          f"range=[{sens['hgk_rank_min']}, {sens['hgk_rank_max']}], "
          f"SD={sens['hgk_rank_sd']}")

    # === 探索的分析 (参考) ===
    explore = compute_exploratory()
    print(f"\n### §7. 探索的分析 (参考、統計検定には不使用): n={len(explore)}")

    # === 結果出力 ===
    output = {
        "version": "v6",
        "description": "LLM 単位集約 + Kruskal-Wallis + ブートストラップ CI + Cliff's δ",
        "changes_from_v5": [
            "矛盾1根治: MCP-Bench/MCPAgentBench のドメイン展開を廃止。LLM 単位に集約 (n=129→n=58)",
            "矛盾2根治: z-score+LODO+KS を削除。Kruskal-Wallis + ブートストラップ CI に置換",
        ],
        "confirmatory": {
            "n_total": len(confirm),
            "n_by_dataset": by_ds,
            "kruskal_wallis": kw,
            "bootstrap_ci": bci,
            "hgk_position": hgk_pos,
            "sensitivity": sens,
        },
        "exploratory": {
            "n_total": len(explore),
            "note": "ドメイン×LLM 展開。統計検定には使わない。可視化用。",
        },
    }

    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "theta_b_v6_results.json")
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n✅ 結果を {outpath} に保存")


if __name__ == "__main__":
    main()
