#!/usr/bin/env python3
"""
Θ(B) v3 — モデル × カテゴリ のフル n 計算。

v2 の問題点:
  - S(B) = 1.0 (全カテゴリ): ground truth ラベルの性質上、弁別力ゼロ
  - R(s,a) が 0 or 1 の二極化

v3 の解決策:
  - S(B) に各モデルの AST score を代入 (ツール選択+パラメータ推論の正確さ = MB 機能)
  - H(s), H(a) はカテゴリの raw データから計算した値を維持
  - R(s,a) もカテゴリの raw 値を維持
  - 5 models × 6 categories + HGK+ 2 sessions = n=32

Θ(B) := S(B) · (1 + α·H(s) + β·H(a) + γ·R(s,a))

H(s): カテゴリ内の利用可能ツール分布の正規化エントロピー
H(a): カテゴリ内の使用ツール分布の正規化エントロピー
R(s,a): サーバ-ツール結合分布の正規化相互情報量
S(B): モデルの AST score (ツール選択・パラメータ推論の正確さ)
"""

import json
import math
import numpy as np
from dataclasses import dataclass


# === データ構造 ===

@dataclass
class ThetaResult:
    """Θ(B) 計算結果"""
    system_name: str     # モデル名
    category: str        # カテゴリ
    source: str          # データソース

    # Θ(B) コンポーネント
    H_s: float           # sensory channel entropy (正規化, 0-1)
    H_a: float           # active channel entropy (正規化, 0-1)
    R_sa: float          # mutual information (正規化, 0-1)
    S_B: float           # blanket strength (AST score, 0-1)

    # 追加メタデータ
    pass_at_1: float = 0.0  # Pass@1 score (参考値)
    k_s: int = 0            # 利用可能ツール数
    k_a: int = 0            # 使用されたツール数
    n_tasks: int = 0        # タスク数

    # パラメータ (論文 §4.1 と同一)
    alpha: float = 0.4
    beta: float = 0.4
    gamma: float = 0.2

    @property
    def theta(self) -> float:
        """Θ(B) を計算"""
        return self.S_B * (1 + self.alpha * self.H_s
                           + self.beta * self.H_a
                           + self.gamma * self.R_sa)


# === MCPToolBench++ カテゴリデータ (v2 raw 計算結果) ===

# [SOURCE: compute_theta_b_v2.py 実行結果]
# H(s), H(a), R(s,a) はカテゴリの raw データから直接計算された値
CATEGORY_DATA = {
    "browser":     {"H_s": 1.000, "H_a": 0.942, "R_sa": 1.000, "k_s": 32, "k_a": 28, "n_tasks": 187},
    "file_system": {"H_s": 1.000, "H_a": 0.975, "R_sa": 0.000, "k_s": 11, "k_a":  9, "n_tasks": 241},
    "finance":     {"H_s": 0.000, "H_a": 0.000, "R_sa": 0.000, "k_s":  1, "k_a":  1, "n_tasks":  90},
    "map":         {"H_s": 1.000, "H_a": 0.944, "R_sa": 1.000, "k_s": 32, "k_a": 25, "n_tasks": 500},
    "pay":         {"H_s": 1.000, "H_a": 0.960, "R_sa": 0.000, "k_s":  6, "k_a":  6, "n_tasks": 310},
    "search":      {"H_s": 1.000, "H_a": 0.920, "R_sa": 1.000, "k_s":  5, "k_a":  5, "n_tasks": 181},
}

# [SOURCE: MCPToolBenchPP/README.md Performance Leaderboard]
# 5 models × 6 categories の AST + Pass@1
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


def compute_all_mcptoolbench() -> list[ThetaResult]:
    """MCPToolBench++ の全モデル × カテゴリの Θ(B) を計算"""
    results = []
    for model_name, cats in MODEL_SCORES.items():
        for cat_name, scores in cats.items():
            cat_data = CATEGORY_DATA[cat_name]
            result = ThetaResult(
                system_name=model_name,
                category=cat_name,
                source="MCPToolBench++",
                H_s=cat_data["H_s"],
                H_a=cat_data["H_a"],
                R_sa=cat_data["R_sa"],
                S_B=scores["AST"],       # S(B) = AST score
                pass_at_1=scores["P1"],
                k_s=cat_data["k_s"],
                k_a=cat_data["k_a"],
                n_tasks=cat_data["n_tasks"],
            )
            results.append(result)
    return results


def compute_hgk_internal() -> list[ThetaResult]:
    """HGK+ 内部セッションデータ (2セッション)

    [SOURCE: HGK+ セッションログから直接計算 + 正規化]
    """
    h_s_1 = 2.81 / math.log2(9)   # = 0.887
    h_a_1 = 2.32 / math.log2(47)  # = 0.418
    h_s_2 = 2.65 / math.log2(9)   # = 0.836
    h_a_2 = 2.18 / math.log2(42)  # = 0.404

    return [
        ThetaResult(
            system_name="HGK+ Session 1",
            category="internal",
            source="HGK+ Internal",
            H_s=h_s_1, H_a=h_a_1, R_sa=0.67, S_B=0.94,
            k_s=9, k_a=47, n_tasks=1,
        ),
        ThetaResult(
            system_name="HGK+ Session 2",
            category="internal",
            source="HGK+ Internal",
            H_s=h_s_2, H_a=h_a_2, R_sa=0.71, S_B=0.91,
            k_s=9, k_a=42, n_tasks=1,
        ),
    ]


def compute_reference_points() -> list[ThetaResult]:
    """理論的参照点 (Human, Vanilla LLM)"""
    return [
        ThetaResult(
            system_name="Human (理論的上限)",
            category="reference",
            source="理論値",
            H_s=1.0, H_a=1.0, R_sa=1.0, S_B=1.0,
        ),
        ThetaResult(
            system_name="Vanilla LLM",
            category="reference",
            source="理論値",
            H_s=0.0, H_a=0.0, R_sa=0.0, S_B=0.0,
        ),
    ]


def main():
    print("=" * 80)
    print("Θ(B) v3 — モデル × カテゴリ フル計算")
    print("=" * 80)

    # === 全データポイント計算 ===
    mcptb_results = compute_all_mcptoolbench()
    hgk_results = compute_hgk_internal()
    ref_results = compute_reference_points()

    all_results = mcptb_results + hgk_results

    # === カテゴリ別テーブル ===
    print(f"\n--- MCPToolBench++ モデル×カテゴリ別 Θ(B) ---")
    print(f"{'モデル':<22} {'カテゴリ':<12} {'Θ(B)':>8} {'S(B)=AST':>10} {'P@1':>8} "
          f"{'H(s)':>8} {'H(a)':>8} {'R(s,a)':>8}")
    print("-" * 90)
    for r in mcptb_results:
        print(f"{r.system_name:<22} {r.category:<12} {r.theta:>8.4f} {r.S_B:>10.4f} "
              f"{r.pass_at_1:>8.4f} {r.H_s:>8.3f} {r.H_a:>8.3f} {r.R_sa:>8.3f}")

    # === モデル別集約 ===
    print(f"\n--- モデル別集約 Θ(B) (タスク数加重平均) ---")
    print(f"{'モデル':<22} {'Θ(B) 加重平均':>14} {'Θ(B) 範囲 min':>14} {'Θ(B) 範囲 max':>14}")
    print("-" * 66)
    models = list(MODEL_SCORES.keys())
    for model in models:
        model_results = [r for r in mcptb_results if r.system_name == model]
        thetas = [r.theta for r in model_results]
        weights = [r.n_tasks for r in model_results]
        weighted_avg = sum(t * w for t, w in zip(thetas, weights)) / sum(weights)
        print(f"{model:<22} {weighted_avg:>14.4f} {min(thetas):>14.4f} {max(thetas):>14.4f}")

    # === カテゴリ別集約 ===
    print(f"\n--- カテゴリ別集約 Θ(B) (モデル平均) ---")
    print(f"{'カテゴリ':<12} {'Θ(B) 平均':>12} {'Θ(B) SD':>12} {'Θ(B) min':>12} {'Θ(B) max':>12}")
    print("-" * 62)
    for cat in CATEGORY_DATA:
        cat_results = [r for r in mcptb_results if r.category == cat]
        thetas = [r.theta for r in cat_results]
        print(f"{cat:<12} {np.mean(thetas):>12.4f} {np.std(thetas):>12.4f} "
              f"{min(thetas):>12.4f} {max(thetas):>12.4f}")

    # === HGK+ との比較 ===
    print(f"\n--- HGK+ 内部データ ---")
    for r in hgk_results:
        print(f"{r.system_name:<22} Θ(B)={r.theta:.4f} [S(B)={r.S_B:.3f}, "
              f"H(s)={r.H_s:.3f}, H(a)={r.H_a:.3f}, R(s,a)={r.R_sa:.3f}]")

    # === 全データポイント統計 ===
    all_thetas = [r.theta for r in all_results]
    print(f"\n--- 全体統計 (n={len(all_results)}) ---")
    print(f"  平均 Θ(B): {np.mean(all_thetas):.4f}")
    print(f"  SD:        {np.std(all_thetas):.4f}")
    print(f"  範囲:      [{min(all_thetas):.4f}, {max(all_thetas):.4f}]")
    print(f"  中央値:    {np.median(all_thetas):.4f}")

    # HGK+ の位置
    hgk_thetas = [r.theta for r in hgk_results]
    mcptb_thetas = [r.theta for r in mcptb_results]
    print(f"\n  MCPToolBench++ 平均: {np.mean(mcptb_thetas):.4f} (SD={np.std(mcptb_thetas):.4f})")
    print(f"  HGK+        平均: {np.mean(hgk_thetas):.4f}")
    print(f"  差分 (MCPTB - HGK): {np.mean(mcptb_thetas) - np.mean(hgk_thetas):.4f}")

    # === 理論的参照点 ===
    print(f"\n--- 理論的参照点 ---")
    for r in ref_results:
        print(f"  {r.system_name}: Θ(B)={r.theta:.4f}")

    # === Body Spectrum 用データ ===
    print(f"\n--- Body Spectrum 用 (φ vs Θ(B)) ---")
    print(f"{'システム':<22} {'φ (推定)':>10} {'Θ(B)':>10}")
    print("-" * 44)
    # Vanilla LLM: φ=0, Θ(B)=0
    print(f"{'Vanilla LLM':<22} {'0.00':>10} {'0.0000':>10}")
    # MCPToolBench++ 各モデル: φ ≈ AST score (ツール使用能力 ≈ 身体的能力)
    for model in models:
        model_res = [r for r in mcptb_results if r.system_name == model]
        avg_theta = np.mean([r.theta for r in model_res])
        avg_ast = np.mean([r.S_B for r in model_res])
        print(f"{model:<22} {avg_ast:>10.4f} {avg_theta:>10.4f}")
    # HGK+
    for r in hgk_results:
        print(f"{r.system_name:<22} {r.S_B:>10.4f} {r.theta:>10.4f}")
    # Human
    print(f"{'Human (理論)':<22} {'1.00':>10} {'2.0000':>10}")

    # === Θ(B) と AST の相関 ===
    asts = [r.S_B for r in all_results]
    thetas_all = [r.theta for r in all_results]
    corr = np.corrcoef(asts, thetas_all)[0, 1]
    print(f"\n--- 相関分析 ---")
    print(f"  r(AST, Θ(B)) = {corr:.4f}")
    print(f"  [推定] AST が S(B) に入っているため構造的に高い相関は自明。")
    print(f"  重要なのは H(s), H(a), R(s,a) がカテゴリ間で異なり Θ(B) に分散を与える点。")

    # === Pass@1 との関係 ===
    p1s = [r.pass_at_1 for r in mcptb_results]
    mcptb_t = [r.theta for r in mcptb_results]
    corr_p1 = np.corrcoef(p1s, mcptb_t)[0, 1]
    print(f"  r(Pass@1, Θ(B)) = {corr_p1:.4f} (MCPToolBench++ only)")

    # === JSON 出力 ===
    results_json = {
        "version": "v3",
        "description": "Θ(B) モデル×カテゴリ フル計算",
        "n_total": len(all_results),
        "data_points": [{
            "system": r.system_name,
            "category": r.category,
            "source": r.source,
            "theta_b": round(r.theta, 4),
            "S_B_AST": round(r.S_B, 4),
            "pass_at_1": round(r.pass_at_1, 4),
            "H_s": round(r.H_s, 4),
            "H_a": round(r.H_a, 4),
            "R_sa": round(r.R_sa, 4),
            "k_s": r.k_s,
            "k_a": r.k_a,
            "n_tasks": r.n_tasks,
        } for r in all_results],
        "statistics": {
            "mean": round(np.mean(all_thetas), 4),
            "sd": round(np.std(all_thetas), 4),
            "min": round(min(all_thetas), 4),
            "max": round(max(all_thetas), 4),
            "median": round(float(np.median(all_thetas)), 4),
            "r_AST_theta": round(corr, 4),
            "r_P1_theta": round(corr_p1, 4),
        },
    }
    with open("theta_b_v3_results.json", "w") as f:
        json.dump(results_json, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 結果を theta_b_v3_results.json に保存")


if __name__ == "__main__":
    main()
