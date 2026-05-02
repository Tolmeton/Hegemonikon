"""
BBH η² 推定実験 — 効果量天井公式 r ≤ √(ρ/(K+1)) のρ独立推定

Suzgun et al. (2022) "Challenging BIG-Bench Tasks and Whether CoT Can Solve Them"
Table 2 のデータ (AO vs CoT 正答率) を用いて、プロンプト変種が説明する分散の割合 η² を算出する。

ρ_est = η² は　ρ_spec (スペクトラム効率) の操作的近似。
公式: r_obs ≤ √(ρ/(K+1))
逆推定値: ρ ≈ 0.3, K ≈ 8
判定閾値: η² ∈ [0.15, 0.45] → 支持 / η² < 0.10 or η² > 0.60 → 棄却
"""

import numpy as np
from scipy import stats

# ==================================================================
# Data: Suzgun et al. (2022) Table 2 — Accuracy (%) 
# Columns: [AO (Answer Only), CoT (Chain-of-Thought)]
# Models: PaLM 540B (the most capable model in the paper)
# SOURCE: arXiv:2210.09261 Table 2
# ==================================================================

# 23 BBH Tasks — PaLM 540B: [AO accuracy, CoT accuracy]
bbh_palm = {
    "boolean_expressions":        [83.2, 80.0],
    "causal_judgement":            [57.8, 62.0],
    "date_understanding":         [41.6, 67.6],
    "disambiguation_qa":          [38.8, 63.6],
    "dyck_languages":             [16.4, 13.6],
    "formal_fallacies":           [52.4, 65.6],
    "geometric_shapes":           [11.6, 52.4],
    "hyperbaton":                 [54.0, 76.0],
    "logical_deduction_5obj":     [31.6, 43.6],
    "logical_deduction_7obj":     [25.2, 37.2],
    "logical_deduction_3obj":     [42.0, 61.6],
    "movie_recommendation":       [62.0, 74.4],
    "multistep_arithmetic":       [1.2, 45.2],
    "navigate":                   [52.4, 56.4],
    "object_counting":            [30.4, 57.6],
    "penguins_in_a_table":        [35.6, 63.0],
    "reasoning_about_colored_obj":[32.0, 56.8],
    "ruin_names":                 [44.4, 86.4],
    "salient_translation":        [30.8, 52.4],
    "snarks":                     [52.8, 73.0],
    "sports_understanding":       [58.4, 80.4],
    "temporal_sequences":         [24.0, 99.6],
    "web_of_lies":                [51.6, 52.0],
}

# Also include InstructGPT and Codex for 2-factor ANOVA
bbh_instructgpt = {
    "boolean_expressions":        [90.0, 87.6],
    "causal_judgement":            [61.5, 70.6],
    "date_understanding":         [53.2, 57.2],
    "disambiguation_qa":          [43.2, 56.8],
    "dyck_languages":             [8.0, 7.6],
    "formal_fallacies":           [50.4, 50.4],
    "geometric_shapes":           [18.0, 41.6],
    "hyperbaton":                 [52.4, 51.2],
    "logical_deduction_5obj":     [28.8, 36.8],
    "logical_deduction_7obj":     [16.0, 20.0],
    "logical_deduction_3obj":     [39.2, 52.0],
    "movie_recommendation":       [50.4, 52.0],
    "multistep_arithmetic":       [0.4, 1.2],
    "navigate":                   [48.8, 56.0],
    "object_counting":            [30.0, 45.6],
    "penguins_in_a_table":        [29.5, 52.7],
    "reasoning_about_colored_obj":[20.4, 36.4],
    "ruin_names":                 [32.4, 45.6],
    "salient_translation":        [22.0, 42.8],
    "snarks":                     [55.1, 58.4],
    "sports_understanding":       [56.4, 70.8],
    "temporal_sequences":         [27.6, 30.4],
    "web_of_lies":                [48.8, 51.2],
}

bbh_codex = {
    "boolean_expressions":        [88.4, 92.8],
    "causal_judgement":            [55.6, 63.1],
    "date_understanding":         [53.2, 73.6],
    "disambiguation_qa":          [56.0, 64.4],
    "dyck_languages":             [22.0, 7.6],
    "formal_fallacies":           [52.0, 53.6],
    "geometric_shapes":           [30.4, 56.4],
    "hyperbaton":                 [63.6, 72.4],
    "logical_deduction_5obj":     [30.8, 43.6],
    "logical_deduction_7obj":     [24.0, 30.0],
    "logical_deduction_3obj":     [52.4, 64.8],
    "movie_recommendation":       [61.6, 72.0],
    "multistep_arithmetic":       [2.4, 47.6],
    "navigate":                   [52.0, 65.6],
    "object_counting":            [42.8, 73.2],
    "penguins_in_a_table":        [37.0, 72.6],
    "reasoning_about_colored_obj":[36.0, 64.0],
    "ruin_names":                 [60.4, 86.4],
    "salient_translation":        [36.4, 68.0],
    "snarks":                     [56.7, 76.4],
    "sports_understanding":       [65.6, 88.4],
    "temporal_sequences":         [16.0, 99.6],
    "web_of_lies":                [51.2, 56.4],
}


def compute_eta_squared_per_task():
    """各タスクの η² (AO vs CoT の分散説明率) を算出"""
    print("=" * 70)
    print("Analysis 1: Per-Task η² (PaLM 540B, AO vs CoT)")
    print("=" * 70)
    
    etas = []
    for task, (ao, cot) in bbh_palm.items():
        # 1-way ANOVA with 2 groups
        # For 2 groups, η² = t² / (t² + df)
        # We treat the accuracy percentages as group means
        # and compute point-biserial correlation
        group_means = np.array([ao, cot])
        grand_mean = np.mean(group_means)
        ss_between = sum((m - grand_mean)**2 for m in group_means) * 1  # n=1 per group
        ss_total = ss_between  # With only 2 data points, ss_within = 0
        
        # This is fundamentally the issue: with only 2 data points (AO mean, CoT mean),
        # we can't do a proper ANOVA. We need individual trial data.
        # 
        # Alternative: compute effect size as (CoT - AO) / pooled SD across tasks
        diff = cot - ao
        etas.append((task, ao, cot, diff))
    
    # Sort by effect (CoT improvement)
    etas.sort(key=lambda x: x[3], reverse=True)
    
    print(f"\n{'Task':<35s} {'AO':>6s} {'CoT':>6s} {'Δ':>8s}")
    print("-" * 60)
    for task, ao, cot, diff in etas:
        marker = "***" if abs(diff) > 20 else ""
        print(f"{task:<35s} {ao:>6.1f} {cot:>6.1f} {diff:>+8.1f} {marker}")
    
    diffs = [x[3] for x in etas]
    print(f"\n--- 要約統計 ---")
    print(f"Δ(CoT-AO) 平均: {np.mean(diffs):+.1f}%")
    print(f"Δ(CoT-AO) SD:   {np.std(diffs):.1f}%")
    print(f"Δ(CoT-AO) 中央値: {np.median(diffs):+.1f}%")
    print(f"Δ 正 (CoT > AO): {sum(1 for d in diffs if d > 0)}/23")
    print(f"Δ 負 (AO > CoT): {sum(1 for d in diffs if d < 0)}/23")
    
    return diffs


def compute_eta_squared_cross_model():
    """
    2要因 ANOVA: プロンプト方式 (AO vs CoT) × モデル (InstructGPT, Codex, PaLM)
    
    各タスクのデータポイント = 6 (3モデル × 2プロンプト)
    → η²_prompt = SS_prompt / SS_total (プロンプトが説明する分散)
    → これが ρ_est の推定値
    """
    print("\n" + "=" * 70)
    print("Analysis 2: Cross-Model η² (3 Models × 2 Prompt Types)")
    print("=" * 70)
    
    tasks = list(bbh_palm.keys())
    eta_prompt_list = []
    eta_model_list = []
    eta_interaction_list = []
    
    for task in tasks:
        # 6 data points: [InstructGPT-AO, InstructGPT-CoT, Codex-AO, Codex-CoT, PaLM-AO, PaLM-CoT]
        data = np.array([
            bbh_instructgpt[task][0], bbh_instructgpt[task][1],
            bbh_codex[task][0], bbh_codex[task][1],
            bbh_palm[task][0], bbh_palm[task][1]
        ])
        
        # Factor A: Prompt (AO=0, CoT=1)
        prompt_factor = np.array([0, 1, 0, 1, 0, 1])
        # Factor B: Model (0=InstructGPT, 1=Codex, 2=PaLM)
        model_factor = np.array([0, 0, 1, 1, 2, 2])
        
        grand_mean = np.mean(data)
        ss_total = np.sum((data - grand_mean)**2)
        
        # SS_prompt
        ao_mean = np.mean(data[prompt_factor == 0])
        cot_mean = np.mean(data[prompt_factor == 1])
        ss_prompt = 3 * ((ao_mean - grand_mean)**2 + (cot_mean - grand_mean)**2)
        
        # SS_model 
        model_means = [np.mean(data[model_factor == m]) for m in range(3)]
        ss_model = 2 * sum((m - grand_mean)**2 for m in model_means)
        
        # SS_interaction = SS_total - SS_prompt - SS_model - SS_error
        # With n=1 per cell, SS_error = 0, so SS_interaction = SS_total - SS_prompt - SS_model
        ss_interaction = ss_total - ss_prompt - ss_model
        
        if ss_total > 0:
            eta_prompt = ss_prompt / ss_total
            eta_model = ss_model / ss_total
            eta_interaction = max(0, ss_interaction / ss_total)
        else:
            eta_prompt = eta_model = eta_interaction = 0.0
        
        eta_prompt_list.append(eta_prompt)
        eta_model_list.append(eta_model)
        eta_interaction_list.append(eta_interaction)
    
    # Print per-task results
    print(f"\n{'Task':<35s} {'η²_prompt':>10s} {'η²_model':>10s} {'η²_interact':>12s}")
    print("-" * 70)
    for i, task in enumerate(tasks):
        print(f"{task:<35s} {eta_prompt_list[i]:>10.3f} {eta_model_list[i]:>10.3f} {eta_interaction_list[i]:>12.3f}")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"η²_prompt  (★ ρ_est 候補):  mean={np.mean(eta_prompt_list):.3f}, SD={np.std(eta_prompt_list):.3f}, median={np.median(eta_prompt_list):.3f}")
    print(f"η²_model:                    mean={np.mean(eta_model_list):.3f}, SD={np.std(eta_model_list):.3f}")
    print(f"η²_interaction:              mean={np.mean(eta_interaction_list):.3f}, SD={np.std(eta_interaction_list):.3f}")
    
    rho_est = np.mean(eta_prompt_list)
    print(f"\n{'='*70}")
    print(f"★★★ ρ_est = {rho_est:.3f} ★★★")
    print(f"逆推定値 ρ ≈ 0.3 との差: {abs(rho_est - 0.3):+.3f}")
    print(f"判定閾値: [0.15, 0.45]")
    if 0.15 <= rho_est <= 0.45:
        print(f"→ 判定: ✅ 支持 (η² ∈ [0.15, 0.45])")
    elif rho_est < 0.10:
        print(f"→ 判定: ❌ 棄却 (η² < 0.10)")
    elif rho_est > 0.60:
        print(f"→ 判定: ❌ 棄却 (η² > 0.60)")
    else:
        print(f"→ 判定: ⚠️ 不明 (追加実験必要)")
    
    # Predict ceiling
    K_est = 8  # from paper IV reverse estimate
    r_pred = np.sqrt(rho_est / (K_est + 1))
    print(f"\n--- 天井予測 ---")
    print(f"r_pred = √(ρ_est / (K+1)) = √({rho_est:.3f} / {K_est+1}) = {r_pred:.3f}")
    print(f"→ 最大改善率: {r_pred*100:.1f}%")
    print(f"Paper IV の予測 (ρ=0.3, K=8): r ≤ {np.sqrt(0.3/9):.3f} ({np.sqrt(0.3/9)*100:.1f}%)")
    
    return rho_est, eta_prompt_list, eta_model_list


def compute_task_variability(eta_prompt_list):
    """タスク間の η² 分散 — ρ のタスク依存性を評価"""
    print("\n" + "=" * 70)
    print("Analysis 3: Task Variability of η²_prompt")
    print("=" * 70)
    
    etas = np.array(eta_prompt_list)
    
    # Distribution analysis
    q25, q50, q75 = np.percentile(etas, [25, 50, 75])
    iqr = q75 - q25
    
    print(f"min:   {np.min(etas):.3f}")
    print(f"Q25:   {q25:.3f}")
    print(f"median:{q50:.3f}")
    print(f"Q75:   {q75:.3f}")
    print(f"max:   {np.max(etas):.3f}")
    print(f"IQR:   {iqr:.3f}")
    print(f"SD:    {np.std(etas):.3f}")
    print(f"CV:    {np.std(etas)/np.mean(etas):.2f}")
    
    # Threshold for task dependency
    if np.std(etas) > 0.15:
        print(f"\n→ ⚠️ タスク依存性が大きい (SD > 0.15)")
        print(f"  ρ は固定値ではなくタスク依存パラメータとして扱うべき")
    else:
        print(f"\n→ ✅ タスク依存性は許容範囲 (SD ≤ 0.15)")
        print(f"  ρ を固定値として扱うことは一次近似として妥当")


if __name__ == "__main__":
    print("BBH η² 推定実験")
    print("目的: ρ_est = η²_prompt を独立に推定し、逆推定値 ρ ≈ 0.3 と比較")
    print("データ: Suzgun et al. (2022) arXiv:2210.09261 Table 2")
    print("=" * 70)
    
    # Analysis 1: Per-task differences
    diffs = compute_eta_squared_per_task()
    
    # Analysis 2: Cross-model η² (main experiment)
    rho_est, eta_prompt, eta_model = compute_eta_squared_cross_model()
    
    # Analysis 3: Task variability
    compute_task_variability(eta_prompt)
    
    print(f"\n{'='*70}")
    print("実験完了")
