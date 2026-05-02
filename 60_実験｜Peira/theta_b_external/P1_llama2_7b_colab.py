#!/usr/bin/env python3
"""
P₁ 検証実験 v3: Mistral-7B on L4 GPU
======================================

GPT-2 (12層) → Mistral-7B-v0.1 (32層) に変更。
PyramidKV 原論文でも使用されたモデル。認証不要。

L4 GPU (24GB VRAM) で fp16 実行 (≈14GB VRAM)。

指標:
  1. RBF-CKA: σ = 中央値ヒューリスティクス
  2. Procrustes距離: scipy.spatial.procrustes (標準実装)
  3. Angular距離: コサイン類似度ベース
  4. 注意エントロピー E(l): GQA 対応 (全ヘッド平均)

使い方 (Colab):
  1. ランタイム → ランタイムのタイプを変更 → L4 GPU
  2. !pip install transformers accelerate scipy
  3. このスクリプトを実行
"""

import json
import os
import time
import numpy as np
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from scipy.spatial import procrustes as scipy_procrustes

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig


# ============================================================
# §1. 類似度指標
# ============================================================

def rbf_cka(X: np.ndarray, Y: np.ndarray, sigma: float = None) -> float:
    """RBF カーネル CKA。X: (n, p), Y: (n, q)"""
    n = X.shape[0]
    if sigma is None:
        dists_X = pdist(X, metric='euclidean')
        dists_Y = pdist(Y, metric='euclidean')
        sigma = np.median(np.concatenate([dists_X, dists_Y]))
        if sigma < 1e-10:
            sigma = 1.0
    K = np.exp(-squareform(pdist(X, 'sqeuclidean')) / (2 * sigma ** 2))
    L = np.exp(-squareform(pdist(Y, 'sqeuclidean')) / (2 * sigma ** 2))
    H = np.eye(n) - np.ones((n, n)) / n
    Kc = H @ K @ H
    Lc = H @ L @ H
    hsic_kl = np.trace(Kc @ Lc) / (n - 1) ** 2
    hsic_kk = np.trace(Kc @ Kc) / (n - 1) ** 2
    hsic_ll = np.trace(Lc @ Lc) / (n - 1) ** 2
    denom = np.sqrt(hsic_kk * hsic_ll)
    if denom < 1e-10:
        return 0.0
    return float(np.clip(hsic_kl / denom, -1.0, 1.0))


def procrustes_distance(X: np.ndarray, Y: np.ndarray) -> float:
    """Procrustes 距離 (scipy ベース)"""
    if X.shape[1] != Y.shape[1]:
        max_d = max(X.shape[1], Y.shape[1])
        X_pad = np.zeros((X.shape[0], max_d))
        Y_pad = np.zeros((Y.shape[0], max_d))
        X_pad[:, :X.shape[1]] = X
        Y_pad[:, :Y.shape[1]] = Y
        X, Y = X_pad, Y_pad
    try:
        _, _, disparity = scipy_procrustes(X, Y)
        return float(disparity)
    except ValueError:
        return 1.0


def angular_distance(X: np.ndarray, Y: np.ndarray) -> float:
    """Angular 距離: コサイン類似度ベース"""
    X = X - X.mean(axis=0, keepdims=True)
    Y = Y - Y.mean(axis=0, keepdims=True)
    X_norms = np.clip(np.linalg.norm(X, axis=1, keepdims=True), 1e-10, None)
    Y_norms = np.clip(np.linalg.norm(Y, axis=1, keepdims=True), 1e-10, None)
    X_unit = X / X_norms
    Y_unit = Y / Y_norms
    cos_sims = np.sum(X_unit * Y_unit, axis=1)
    return float(1.0 - np.mean(cos_sims))


# ============================================================
# §2. 注意エントロピー (GQA 対応)
# ============================================================

def layer_attention_entropy(layer_attn: np.ndarray) -> float:
    """層の注意エントロピー。
    
    layer_attn: (n_heads, seq_len, seq_len)
    注意: transformers は GQA でも n_heads 分に展開して返す。
    つまり KV head のグループ構造は見えず、全ヘッド平均となる。
    エントロピーはヘッドごとに計算し平均。
    """
    n_heads = layer_attn.shape[0]
    entropies = []
    for h in range(n_heads):
        attn = np.clip(layer_attn[h], 1e-12, None)
        # 行方向にエントロピー (各クエリ位置の注意分布)
        row_entropy = -np.sum(attn * np.log2(attn), axis=-1)
        entropies.append(float(np.mean(row_entropy)))
    return float(np.mean(entropies))


# ============================================================
# §3. メイン実験
# ============================================================

def run_experiment(
    n_sentences: int = 20,
    model_name: str = "mistralai/Mistral-7B-v0.1",
    max_length: int = 128,
) -> dict:
    """P₁ 検証実験 v3: Mistral-7B."""
    
    print(f"{'='*70}")
    print(f"P₁ 検証実験 v3: Mistral-7B (32層)")
    print(f"モデル: {model_name}")
    print(f"{'='*70}")
    
    # --- モデル読込 ---
    print("\n[1/5] モデル読み込み中...")
    t0 = time.time()
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        output_attentions=True,
        output_hidden_states=True,
        attn_implementation="eager",  # flash attention 無効化 (attention weights 取得のため)
    )
    model.eval()
    
    config = model.config
    n_layers = config.num_hidden_layers
    n_kv_heads = getattr(config, 'num_key_value_heads', config.num_attention_heads)
    n_heads = config.num_attention_heads
    
    print(f"  層数: {n_layers}, Attention heads: {n_heads}, KV heads: {n_kv_heads}")
    print(f"  Hidden dim: {config.hidden_size}")
    print(f"  読み込み時間: {time.time() - t0:.1f}秒")
    print(f"  VRAM: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
    
    # --- 入力テキスト (多ドメイン: AI, 科学, 歴史, 日常, 哲学) ---
    print("\n[2/5] 入力テキスト準備...")
    texts = [
        # AI/ML (5文)
        "The history of artificial intelligence began in antiquity, with myths and stories of artificial beings endowed with intelligence.",
        "Machine learning is a subset of artificial intelligence that provides systems the ability to automatically learn and improve from experience.",
        "Natural language processing is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language.",
        "The Transformer architecture was introduced in the paper Attention Is All You Need published in 2017 by researchers at Google.",
        "Large language models are neural network models that are trained on large amounts of text data and can generate human-like text.",
        # 自然科学 (5文)
        "The theory of general relativity describes gravity as a geometric property of space and time, or four-dimensional spacetime.",
        "Photosynthesis is a process used by plants and other organisms to convert light energy into chemical energy that can be stored and later released.",
        "The human genome contains approximately three billion base pairs of DNA arranged into twenty-three pairs of chromosomes.",
        "Quantum entanglement is a phenomenon in which quantum states of two or more objects are interconnected regardless of the distance between them.",
        "The second law of thermodynamics states that the total entropy of an isolated system can never decrease over time.",
        # 歴史・社会 (5文)
        "The French Revolution was a period of radical political and societal change in France that began with the Estates General of 1789.",
        "The invention of the printing press by Johannes Gutenberg around 1440 revolutionized communication and the spread of knowledge across Europe.",
        "The Industrial Revolution marked a major turning point in history, fundamentally changing how people lived and worked.",
        "Ancient Greek democracy originated in the city-state of Athens around the fifth century BC and influenced political systems worldwide.",
        "The Silk Road was an ancient network of trade routes that connected the East and West from China to the Mediterranean Sea.",
        # 日常・具体 (3文)
        "The recipe for a classic French omelette requires three eggs, a tablespoon of butter, and a pinch of salt.",
        "Regular exercise has been shown to reduce the risk of chronic diseases, improve mental health, and increase life expectancy.",
        "Tokyo is one of the most densely populated cities in the world with a metropolitan population exceeding thirteen million people.",
        # 哲学・抽象 (2文)
        "The free energy principle suggests that all adaptive systems minimize a quantity called variational free energy.",
        "Information geometry studies probability distributions using concepts from differential geometry such as the Fisher information metric.",
    ]
    texts = texts[:n_sentences]
    print(f"  使用文数: {len(texts)}, max_length: {max_length}")
    
    # --- 層別測定 ---
    print("\n[3/5] 層別測定実行中...")
    
    all_layer_entropies = [[] for _ in range(n_layers)]
    all_hidden_states = [[] for _ in range(n_layers + 1)]
    
    for i, text in enumerate(texts):
        print(f"  文 {i+1}/{len(texts)}: {text[:50]}...")
        
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
        
        # Attention: (n_layers, 1, n_heads, seq_len, seq_len)
        # GQA の場合でも transformers は n_heads 分展開して返す
        attentions = outputs.attentions
        hidden_states = outputs.hidden_states
        
        seq_len = inputs['input_ids'].shape[1]
        
        for l in range(n_layers):
            # attention: (1, n_heads, seq_len, seq_len)
            attn = attentions[l][0].cpu().float().numpy()
            e = layer_attention_entropy(attn)
            all_layer_entropies[l].append(e)
        
        for l in range(n_layers + 1):
            hs = hidden_states[l][0].cpu().float().numpy()
            all_hidden_states[l].append(hs)
        
        # メモリ解放
        del outputs, attentions, hidden_states
        torch.cuda.empty_cache()
    
    # --- 統計量計算 ---
    print("\n[4/5] 統計量計算中...")
    
    E_l = np.array([np.mean(all_layer_entropies[l]) for l in range(n_layers)])
    E_l_std = np.array([np.std(all_layer_entropies[l]) for l in range(n_layers)])
    
    rbf_cka_vals = []
    procrustes_vals = []
    angular_vals = []
    
    for l in range(n_layers):
        rbf_per_sent = []
        proc_per_sent = []
        ang_per_sent = []
        
        for i in range(len(texts)):
            X = all_hidden_states[l][i]
            Y = all_hidden_states[l + 1][i]
            
            rbf_per_sent.append(rbf_cka(X, Y))
            proc_per_sent.append(procrustes_distance(X, Y))
            ang_per_sent.append(angular_distance(X, Y))
        
        rbf_cka_vals.append(np.mean(rbf_per_sent))
        procrustes_vals.append(np.mean(proc_per_sent))
        angular_vals.append(np.mean(ang_per_sent))
        
        if (l + 1) % 8 == 0:
            print(f"  層 {l+1}/{n_layers} 完了")
    
    rbf_arr = np.array(rbf_cka_vals)
    proc_arr = np.array(procrustes_vals)
    ang_arr = np.array(angular_vals)
    
    Theta_RBF = 1.0 - rbf_arr
    Theta_Proc = proc_arr
    Theta_Ang = ang_arr
    
    # --- 結果表示 ---
    print(f"\n{'='*70}")
    print(f"結果 ({model_name}, {n_layers}層)")
    print(f"{'='*70}")
    
    print(f"\n層別データ:")
    print(f"{'層':>4} {'E(l)':>8} {'RBF-CKA':>9} {'Θ_RBF':>8} {'ProcDist':>9} {'AngDist':>8}")
    print("-" * 55)
    for l in range(n_layers):
        print(f"{l:>4d} {E_l[l]:>8.4f} {rbf_arr[l]:>9.4f} {Theta_RBF[l]:>8.4f} "
              f"{proc_arr[l]:>9.6f} {ang_arr[l]:>8.4f}")
    
    # 相関分析
    correlations = {}
    for name, theta_arr in [("Θ_RBF", Theta_RBF), ("Θ_Proc", Theta_Proc), ("Θ_Ang", Theta_Ang)]:
        rho, p = stats.spearmanr(E_l, theta_arr)
        pr, pp = stats.pearsonr(E_l, theta_arr)
        correlations[name] = {
            "spearman_rho": round(float(rho), 4),
            "spearman_p": round(float(p), 6),
            "pearson_r": round(float(pr), 4),
            "pearson_p": round(float(pp), 6),
        }
    
    print(f"\n相関分析: E(l) × 各 Θ 指標")
    print(f"{'指標':>10} {'Spearman ρ':>12} {'p値':>12} {'Pearson r':>12} {'p値':>12}")
    print("-" * 60)
    for name, c in correlations.items():
        print(f"{name:>10} {c['spearman_rho']:>12.4f} {c['spearman_p']:>12.6f} "
              f"{c['pearson_r']:>12.4f} {c['pearson_p']:>12.6f}")
    
    # 漏斗パターン
    tau, tau_p = stats.kendalltau(np.arange(n_layers), E_l)
    
    # 飽和チェック
    print(f"\n━━━ 飽和問題の解消度 ━━━")
    for name, arr in [("Θ_RBF", Theta_RBF), ("Θ_Proc", Theta_Proc), ("Θ_Ang", Theta_Ang)]:
        cv = np.std(arr) / (np.mean(arr) + 1e-10)
        n_nonzero = np.sum(arr > 0.001)
        print(f"  {name}: mean={np.mean(arr):.4f}, sd={np.std(arr):.4f}, "
              f"CV={cv:.2f}, 有効点={n_nonzero}/{n_layers}")
    
    # 中間層 (embedding直後と最終層を除外)
    mid = slice(2, n_layers - 2)
    print(f"\n━━━ 中間層 (2-{n_layers-3}) の相関 ━━━")
    for name, theta_arr in [("Θ_RBF", Theta_RBF), ("Θ_Proc", Theta_Proc), ("Θ_Ang", Theta_Ang)]:
        rho_m, p_m = stats.spearmanr(E_l[mid], theta_arr[mid])
        pr_m, pp_m = stats.pearsonr(E_l[mid], theta_arr[mid])
        print(f"  {name}: Spearman ρ={rho_m:+.4f} (p={p_m:.4f}), Pearson r={pr_m:+.4f} (p={pp_m:.4f})")
    
    # 判定
    any_supported = any(
        abs(c["spearman_rho"]) >= 0.5 and c["spearman_p"] < 0.05
        for c in correlations.values()
    )
    all_rejected = all(abs(c["spearman_rho"]) < 0.5 for c in correlations.values())
    
    print(f"\n━━━ 仮説判定 ━━━")
    best_metric = max(correlations.items(), key=lambda x: abs(x[1]["spearman_rho"]))
    print(f"  最強指標: {best_metric[0]} (ρ={best_metric[1]['spearman_rho']}, p={best_metric[1]['spearman_p']})")
    print(f"  漏斗パターン: τ={tau:.4f}, p={tau_p:.6f}")
    
    if any_supported:
        print(f"  判定: ✅ 支持 — |ρ| ≥ 0.5 (p < 0.05)")
    elif all_rejected:
        print(f"  判定: ❌ 棄却 — 全指標で |ρ| < 0.5")
    else:
        print(f"  判定: ⚠️ 混在")
    
    # 結果保存
    result = {
        "experiment": "P1_verification_v3_llama2_7b",
        "model": model_name,
        "n_layers": n_layers,
        "n_sentences": len(texts),
        "n_heads": n_heads,
        "n_kv_heads": n_kv_heads,
        "hidden_size": config.hidden_size,
        "max_length": max_length,
        "layer_data": {
            "E_l": E_l.tolist(),
            "E_l_std": E_l_std.tolist(),
            "RBF_CKA": rbf_arr.tolist(),
            "Theta_RBF": Theta_RBF.tolist(),
            "Procrustes_dist": proc_arr.tolist(),
            "Angular_dist": ang_arr.tolist(),
        },
        "correlations": correlations,
        "funnel_pattern": {
            "kendall_tau": round(float(tau), 4),
            "kendall_p": round(float(tau_p), 6),
        },
        "saturation_resolved": {
            name: {
                "mean": round(float(np.mean(arr)), 4),
                "std": round(float(np.std(arr)), 4),
                "cv": round(float(np.std(arr) / (np.mean(arr) + 1e-10)), 4),
                "n_nonzero": int(np.sum(arr > 0.001)),
            }
            for name, arr in [("Theta_RBF", Theta_RBF), ("Theta_Proc", Theta_Proc), ("Theta_Ang", Theta_Ang)]
        },
        "hypothesis_judgment": {
            "any_supported": bool(any_supported),
            "all_rejected": bool(all_rejected),
            "best_metric": best_metric[0],
            "best_rho": best_metric[1]["spearman_rho"],
            "best_p": best_metric[1]["spearman_p"],
        },
    }
    
    # JSON 保存
    outpath = "pei_p1_llama2_7b_results.json"
    with open(outpath, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 結果を {outpath} に保存")
    
    return result


if __name__ == "__main__":
    run_experiment(n_sentences=20, model_name="mistralai/Mistral-7B-v0.1")
