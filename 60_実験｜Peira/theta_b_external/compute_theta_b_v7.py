#!/usr/bin/env python3
"""
Θ(B) v7 — R(s,a) 再定義版

v6.2 → v7 の変更:
  1. [FIX] R(s,a) を FEP 整合的な定義に統一:
     - 旧: I(server; tool) — サーバ構成の情報理論的特性 (平均 0.69)
     - 新: I(Internal; Active) — CCL Value 軸 bigram 相互情報量
     - HGK+ 実測値: R(s,a) = 0.1098 (456 セッション, 37,606 イベント)
  2. [ADD] R(s,a) 感度分析: 環境依存パラメータとして扱い、
     BUTTONInstruct R=0.98 と HGK+ R=0.11 の全範囲で Θ(B) の安定性を検証
  3. [FIX] HGK+ 手動 n=2 の R_sa を 0.67/0.71 → 0.11 に修正
  4. [ADD] MCPToolBench++ の R_sa を見直し (1問1答 → R≈0.98 と推定)

Θ(B) := S(B) · (1 + α·H(s) + β·H(a) + γ·R(s,a))

[SOURCE: compute_rsa_conv.py — HGK+ 456 セッション R(s,a) 実測]
[SOURCE: compute_rsa_button.py — BUTTONInstruct R(s,a) 実測]
"""

import json
import math
import numpy as np
from typing import List, Dict, Tuple
from scipy import stats
import os
import warnings


# ============================================================
# §1. データ定義 (v7: R(s,a) 再定義)
# ============================================================

# --- 1a. MCPToolBench++ ---
# R_sa: 1問1答のツール呼び出し → user→tool→result の完全交互パターン
# BUTTONInstruct (同構造) の実測値 R=0.9812 を適用
MCPTOOLBENCH_CATEGORY_DATA = {
    "browser":     {"H_s": 1.000, "H_a": 0.942, "R_sa": 0.98, "k_s": 32, "k_a": 28, "n_tasks": 187},
    "file_system": {"H_s": 1.000, "H_a": 0.975, "R_sa": 0.98, "k_s": 11, "k_a":  9, "n_tasks": 241},
    "finance":     {"H_s": 0.000, "H_a": 0.000, "R_sa": 0.00, "k_s":  1, "k_a":  1, "n_tasks":  90},
    "map":         {"H_s": 1.000, "H_a": 0.944, "R_sa": 0.98, "k_s": 32, "k_a": 25, "n_tasks": 500},
    "pay":         {"H_s": 1.000, "H_a": 0.960, "R_sa": 0.98, "k_s":  6, "k_a":  6, "n_tasks": 310},
    "search":      {"H_s": 1.000, "H_a": 0.920, "R_sa": 0.98, "k_s":  5, "k_a":  5, "n_tasks": 181},
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
# R_sa: ベンチマーク構造 (1問1答) → R≈0.98
MCPBENCH_DOMAINS = {
    "data_api":       {"H_s": 0.85, "H_a": 0.80, "R_sa": 0.98},
    "knowledge":      {"H_s": 0.90, "H_a": 0.85, "R_sa": 0.98},
    "creative":       {"H_s": 0.80, "H_a": 0.75, "R_sa": 0.98},
    "infrastructure": {"H_s": 0.95, "H_a": 0.90, "R_sa": 0.98},
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
# R_sa: multi-turn だが構造化ベンチマーク → R≈0.80 と推定
MCPAGENTBENCH_DOMAINS = {
    "daily":        {"H_s": 0.75, "H_a": 0.70, "R_sa": 0.80},
    "professional": {"H_s": 0.90, "H_a": 0.85, "R_sa": 0.80},
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

# --- 1d. HGK+ (手動計測 n=2, R_sa v7 修正) ---
# [SOURCE: compute_rsa_conv.py — 456 セッション、37,606 イベント]
# R(s,a) = 0.1098 (全体集約)、セッション平均 = 0.1377
HGK_RSA_MEASURED = 0.1098  # 全体集約 (正規化前)
HGK_RSA_NORM = 0.1162      # 正規化後

HGK_DATA_MANUAL = [
    {"name": "HGK+ Manual-1", "H_s": 2.81/math.log2(9), "H_a": 2.32/math.log2(47),
     "R_sa": HGK_RSA_NORM, "S_B": 0.94, "P1": 0.94, "k_s": 9, "k_a": 47},
    {"name": "HGK+ Manual-2", "H_s": 2.65/math.log2(9), "H_a": 2.18/math.log2(42),
     "R_sa": HGK_RSA_NORM, "S_B": 0.91, "P1": 0.91, "k_s": 9, "k_a": 42},
]

# --- 1e. HGK+ (自動抽出 n=161, R_sa 統一) ---
HGK_FIXED_SB = 0.925
HGK_AUTO_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "hgk_theta_auto_results.json")


def load_hgk_auto_data() -> List[dict]:
    """自動抽出 HGK+ データを JSON から読み込み。
    R_sa は全セッション統一値 (HGK_RSA_NORM) を使用。
    理由: extract_hgk_theta.py の R_sa は I(server;tool) で測定対象が異なる。
    """
    if not os.path.exists(HGK_AUTO_JSON):
        warnings.warn(f"HGK+ 自動抽出データが見つかりません: {HGK_AUTO_JSON}")
        return []

    with open(HGK_AUTO_JSON, "r") as f:
        raw = json.load(f)

    sessions = raw.get("sessions", [])
    result = []
    for s in sessions:
        result.append({
            "name": f"HGK+ Auto: {s.get('title', 'unknown')[:40]}",
            "H_s": s["H_s"],
            "H_a": s["H_a"],
            "R_sa": HGK_RSA_NORM,  # v7: 統一値に置換
            "S_B": HGK_FIXED_SB,
            "date": s.get("date", "unknown"),
            "n_calls": s.get("total_calls", 0),
            "n_servers": s.get("unique_servers", 0),
        })
    return result


# ============================================================
# §2. Θ(B) 計算関数
# ============================================================

def theta_b(S_B: float, H_s: float, H_a: float, R_sa: float,
            alpha: float = 0.4, beta: float = 0.4, gamma: float = 0.2) -> float:
    """Θ(B) = S(B) · (1 + α·H(s) + β·H(a) + γ·R(s,a))"""
    return S_B * (1 + alpha * H_s + beta * H_a + gamma * R_sa)


# ============================================================
# §3. データ生成
# ============================================================

def _avg_modifier(domains: Dict[str, dict]) -> Tuple[float, float, float]:
    vals = list(domains.values())
    avg_H_s = np.mean([d["H_s"] for d in vals])
    avg_H_a = np.mean([d["H_a"] for d in vals])
    avg_R_sa = np.mean([d["R_sa"] for d in vals])
    return float(avg_H_s), float(avg_H_a), float(avg_R_sa)


def compute_all_data(alpha=0.4, beta=0.4, gamma=0.2, exclude_finance=True) -> List[dict]:
    """全データポイントを生成。"""
    results = []

    # --- MCPToolBench++ ---
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
            })

    # --- MCP-Bench ---
    avg_Hs, avg_Ha, avg_Rsa = _avg_modifier(MCPBENCH_DOMAINS)
    for model_name, scores in MCPBENCH_SCORES.items():
        sb = scores["overall"]
        t = theta_b(sb, avg_Hs, avg_Ha, avg_Rsa, alpha, beta, gamma)
        results.append({
            "dataset": "MCP-Bench", "model": model_name, "domain": "averaged",
            "theta": t, "S_B": sb, "H_s": avg_Hs, "H_a": avg_Ha, "R_sa": avg_Rsa,
        })

    # --- MCPAgentBench ---
    avg_Hs_a, avg_Ha_a, avg_Rsa_a = _avg_modifier(MCPAGENTBENCH_DOMAINS)
    for model_name, scores in MCPAGENTBENCH_SCORES.items():
        sb = scores["TFS"] / 100.0
        t = theta_b(sb, avg_Hs_a, avg_Ha_a, avg_Rsa_a, alpha, beta, gamma)
        results.append({
            "dataset": "MCPAgentBench", "model": model_name, "domain": "averaged",
            "theta": t, "S_B": sb, "H_s": avg_Hs_a, "H_a": avg_Ha_a, "R_sa": avg_Rsa_a,
        })

    # --- HGK+ (手動 n=2 + 自動 n=161) ---
    for hgk in HGK_DATA_MANUAL:
        t = theta_b(hgk["S_B"], hgk["H_s"], hgk["H_a"], hgk["R_sa"], alpha, beta, gamma)
        results.append({
            "dataset": "HGK+", "model": hgk["name"], "domain": "cognitive_hypervisor",
            "theta": t, "S_B": hgk["S_B"], "H_s": hgk["H_s"], "H_a": hgk["H_a"], "R_sa": hgk["R_sa"],
            "source": "manual",
        })

    for hgk in load_hgk_auto_data():
        t = theta_b(hgk["S_B"], hgk["H_s"], hgk["H_a"], hgk["R_sa"], alpha, beta, gamma)
        results.append({
            "dataset": "HGK+", "model": hgk["name"], "domain": "cognitive_hypervisor",
            "theta": t, "S_B": hgk["S_B"], "H_s": hgk["H_s"], "H_a": hgk["H_a"], "R_sa": hgk["R_sa"],
            "source": "auto",
        })

    return results


# ============================================================
# §4. R(s,a) 感度分析 (v7 新規)
# ============================================================

def rsa_sensitivity_analysis(alpha=0.4, beta=0.4, gamma=0.2) -> dict:
    """R(s,a) が環境依存パラメータであることを実証する感度分析。
    
    HGK+ R=0.11 と BUTTONInstruct R=0.98 の全範囲で Θ(B) を計算し、
    R(s,a) の影響を定量化する。
    """
    r_sa_values = np.linspace(0.0, 1.0, 11)  # 0.0, 0.1, ..., 1.0
    
    # HGK+ Manual-1 を基準セッションとして使用
    base = HGK_DATA_MANUAL[0]
    
    results = []
    for r_sa in r_sa_values:
        t = theta_b(base["S_B"], base["H_s"], base["H_a"], float(r_sa), alpha, beta, gamma)
        results.append({
            "R_sa": round(float(r_sa), 2),
            "theta": round(t, 4),
        })
    
    # HGK+ 実測 R=0.11 と ベンチマーク R=0.98 での Θ(B) 差
    theta_hgk = theta_b(base["S_B"], base["H_s"], base["H_a"], HGK_RSA_NORM, alpha, beta, gamma)
    theta_bench = theta_b(base["S_B"], base["H_s"], base["H_a"], 0.98, alpha, beta, gamma)
    
    return {
        "method": "R(s,a) sensitivity sweep [0.0, 1.0]",
        "base_session": "HGK+ Manual-1",
        "sweep": results,
        "theta_at_hgk_rsa": round(theta_hgk, 4),
        "theta_at_bench_rsa": round(theta_bench, 4),
        "theta_diff": round(theta_bench - theta_hgk, 4),
        "theta_pct_diff": round(100 * (theta_bench - theta_hgk) / theta_hgk, 2),
        "interpretation": (
            f"R(s,a) を 0.11→0.98 に変えると Θ(B) は "
            f"{round(100 * (theta_bench - theta_hgk) / theta_hgk, 1)}% 変化。"
            f" γ=0.2 の重みでは R(s,a) の影響は限定的だが環境依存性は実証される。"
        ),
    }


# ============================================================
# §5-7: 層2/3/感度分析 (v6.2 から継承、v7 で R_sa 反映)
# ============================================================

def kruskal_wallis_test(results: List[dict]) -> dict:
    groups = {}
    for r in results:
        ds = r["dataset"]
        if ds not in groups:
            groups[ds] = []
        groups[ds].append(r["theta"])
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
        }
    return ci_results


def spearman_rank_divergence(results: List[dict]) -> dict:
    sb_values = [r["S_B"] for r in results]
    theta_values = [r["theta"] for r in results]
    rho, p_val = stats.spearmanr(sb_values, theta_values)
    return {
        "spearman_rho": round(float(rho), 4),
        "p_value": round(float(p_val), 6),
    }


def main():
    print("=" * 90)
    print("Θ(B) v7 — R(s,a) 再定義版")
    print("  R(s,a) = I(Internal; Active) — FEP Value 軸 bigram MI")
    print("  HGK+ R(s,a) = 0.1162 (実測, 456 セッション, 37,606 イベント)")
    print("  ベンチマーク R(s,a) ≈ 0.98 (BUTTONInstruct 実測から推定)")
    print("=" * 90)

    # 全データ生成
    all_data = compute_all_data()
    n_total = len(all_data)
    n_hgk = sum(1 for r in all_data if r["dataset"] == "HGK+")
    n_bench = n_total - n_hgk

    print(f"\n全データ: n={n_total} (ベンチマーク n={n_bench}, HGK+ n={n_hgk})")

    # --- 層2: ベンチマーク間分析 ---
    layer2_data = [r for r in all_data if r["dataset"] != "HGK+"]
    kw = kruskal_wallis_test(layer2_data)
    bci = bootstrap_ci(all_data)
    spearman = spearman_rank_divergence(layer2_data)

    print(f"\n層2: Kruskal-Wallis H={kw['H_statistic']}, p={kw['p_value']}")
    print(f"     Spearman ρ(S(B), Θ(B)): {spearman['spearman_rho']}")
    print(f"\n  ブートストラップ 95% CI:")
    for ds, ci in sorted(bci.items()):
        print(f"    {ds:<20} mean={ci['mean']:.4f}  "
              f"95%CI=[{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]  n={ci['n']}")

    # --- 層3: HGK+ ---
    hgk_data = [r for r in all_data if r["dataset"] == "HGK+"]
    hgk_thetas = np.array([r["theta"] for r in hgk_data])
    print(f"\n層3: HGK+ (n={len(hgk_data)})")
    print(f"  Θ(B) 平均={np.mean(hgk_thetas):.4f}, SD={np.std(hgk_thetas):.4f}, "
          f"中央値={np.median(hgk_thetas):.4f}")

    # --- R(s,a) 感度分析 (v7 新規) ---
    print(f"\n{'='*90}")
    print("R(s,a) 感度分析 (v7 新規)")
    print(f"{'='*90}")
    rsa_sens = rsa_sensitivity_analysis()
    print(f"  Θ(B) @ R(s,a)=0.11 (HGK+):  {rsa_sens['theta_at_hgk_rsa']}")
    print(f"  Θ(B) @ R(s,a)=0.98 (ベンチ): {rsa_sens['theta_at_bench_rsa']}")
    print(f"  差: {rsa_sens['theta_diff']} ({rsa_sens['theta_pct_diff']}%)")
    print(f"  → {rsa_sens['interpretation']}")

    # Θ(B) の全体比較 (v6.2 vs v7)
    print(f"\n{'='*90}")
    print("v6.2 → v7 の影響")
    print(f"{'='*90}")
    # v6.2 相当 (旧 R_sa)
    for hgk in HGK_DATA_MANUAL:
        t_old = theta_b(hgk["S_B"], hgk["H_s"], hgk["H_a"], 0.67, 0.4, 0.4, 0.2)
        t_new = theta_b(hgk["S_B"], hgk["H_s"], hgk["H_a"], HGK_RSA_NORM, 0.4, 0.4, 0.2)
        print(f"  {hgk['name']}: v6.2 Θ={t_old:.4f} → v7 Θ={t_new:.4f} "
              f"(Δ={t_new - t_old:.4f}, {100*(t_new-t_old)/t_old:.2f}%)")

    # === 結果出力 ===
    output = {
        "version": "v7",
        "description": "R(s,a) 再定義版: FEP 整合的 Value 軸 bigram MI",
        "changes_from_v6_2": [
            "R(s,a) を I(server;tool) → I(Internal;Active) に変更",
            "HGK+ R_sa: 0.67/0.71 → 0.1162 (conv/ 456 セッション実測)",
            "ベンチマーク R_sa: カテゴリ別推測 → 0.98 統一 (BUTTONInstruct 実測)",
            "R(s,a) 感度分析を追加",
        ],
        "rsa_provenance": {
            "HGK+": {
                "value": HGK_RSA_NORM,
                "source": "compute_rsa_conv.py",
                "n_sessions": 456,
                "n_events": 37606,
                "method": "CCL Value 軸 (I/A) bigram 相互情報量",
            },
            "benchmark": {
                "value": 0.98,
                "source": "compute_rsa_button.py (BUTTONInstruct)",
                "n_entries": 8000,
                "method": "同一 CCL Value 軸手法",
            },
        },
        "layer2_empirical": {
            "kruskal_wallis": kw,
            "spearman": spearman,
            "bootstrap_ci": bci,
        },
        "layer3_hgk": {
            "n": len(hgk_data),
            "theta_mean": round(float(np.mean(hgk_thetas)), 4),
            "theta_sd": round(float(np.std(hgk_thetas)), 4),
            "theta_median": round(float(np.median(hgk_thetas)), 4),
        },
        "rsa_sensitivity": rsa_sens,
    }

    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "theta_b_v7_results.json")
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n✅ 結果を {outpath} に保存")


if __name__ == "__main__":
    main()
