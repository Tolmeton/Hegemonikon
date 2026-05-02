#!/usr/bin/env python3
"""
P₁ 検証実験 v2: RBF-CKA で中間層分解能を改善
===============================================

前回の問題: 線形 CKA が層3-10 で ≈1.0 に飽和し、Θ_CKA ≈ 0 で分散なし
解決策: 3つの非類似度指標を並列計測 → ロバスト性の高い相関推定

指標:
  1. RBF-CKA: σ を中央値ヒューリスティクスで設定。非線形類似構造を捉える
  2. Procrustes距離: 最適直交変換後の残差。回転不変な距離
  3. 注意エントロピー E(l): 前回と同一定義 (全ヘッド平均)

反証条件: 3指標すべてで Spearman |ρ| < 0.5 → P₁ 棄却
"""

import json
import os
import numpy as np
from scipy import stats
from scipy.spatial.distance import pdist, squareform

import torch
from transformers import GPT2Tokenizer, GPT2Model


# ============================================================
# §1. 類似度指標の実装
# ============================================================

def rbf_cka(X: np.ndarray, Y: np.ndarray, sigma: float = None) -> float:
    """RBF カーネル CKA。
    
    X: (n, p), Y: (n, q)
    σ: RBF 幅。None なら中央値ヒューリスティクス
    """
    n = X.shape[0]
    
    # 中央値ヒューリスティクス
    if sigma is None:
        dists_X = pdist(X, metric='euclidean')
        dists_Y = pdist(Y, metric='euclidean')
        sigma = np.median(np.concatenate([dists_X, dists_Y]))
        if sigma < 1e-10:
            sigma = 1.0
    
    # RBF カーネル行列
    K = np.exp(-squareform(pdist(X, 'sqeuclidean')) / (2 * sigma ** 2))
    L = np.exp(-squareform(pdist(Y, 'sqeuclidean')) / (2 * sigma ** 2))
    
    # 中心化
    H = np.eye(n) - np.ones((n, n)) / n
    Kc = H @ K @ H
    Lc = H @ L @ H
    
    # HSIC ベースの CKA
    hsic_kl = np.trace(Kc @ Lc) / (n - 1) ** 2
    hsic_kk = np.trace(Kc @ Kc) / (n - 1) ** 2
    hsic_ll = np.trace(Lc @ Lc) / (n - 1) ** 2
    
    denom = np.sqrt(hsic_kk * hsic_ll)
    if denom < 1e-10:
        return 0.0
    
    return float(np.clip(hsic_kl / denom, -1.0, 1.0))


def procrustes_distance(X: np.ndarray, Y: np.ndarray) -> float:
    """Procrustes 距離 (scipy.spatial.procrustes ベース)。
    
    X, Y: (n, p) — 同じ次元数
    戻り値: disparity (正規化された残差二乗和)
    """
    from scipy.spatial import procrustes as scipy_procrustes
    
    # scipy は (n, k) の行列を要求。次元を揃える
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
    """Angular CKA: cos 類似度ベースの距離。線形 CKA の角度版で飽和しにくい。
    
    X, Y: (n, p)
    """
    # 中心化
    X = X - X.mean(axis=0, keepdims=True)
    Y = Y - Y.mean(axis=0, keepdims=True)
    
    # 各サンプルをユニットベクトルに正規化
    X_norms = np.linalg.norm(X, axis=1, keepdims=True)
    Y_norms = np.linalg.norm(Y, axis=1, keepdims=True)
    
    X_norms = np.clip(X_norms, 1e-10, None)
    Y_norms = np.clip(Y_norms, 1e-10, None)
    
    X_unit = X / X_norms
    Y_unit = Y / Y_norms
    
    # サンプルごとのコサイン類似度
    cos_sims = np.sum(X_unit * Y_unit, axis=1)
    
    # 角度距離 = 1 - 平均コサイン類似度
    return float(1.0 - np.mean(cos_sims))


# ============================================================
# §2. 注意エントロピー (前回と同一)
# ============================================================

def layer_attention_entropy(layer_attn: np.ndarray) -> float:
    """層全体の注意エントロピー = 全ヘッドのエントロピーの平均。"""
    n_heads = layer_attn.shape[0]
    entropies = []
    for h in range(n_heads):
        attn = np.clip(layer_attn[h], 1e-12, None)
        row_entropy = -np.sum(attn * np.log2(attn), axis=-1)
        entropies.append(float(np.mean(row_entropy)))
    return float(np.mean(entropies))


# ============================================================
# §3. メイン実験
# ============================================================

def run_experiment(n_sentences: int = 10, model_name: str = "gpt2") -> dict:
    """P₁ 検証実験 v2: RBF-CKA + Procrustes + Angular で中間層分解能改善。"""
    
    print(f"{'='*70}")
    print(f"P₁ 検証実験 v2: RBF-CKA で中間層分解能改善")
    print(f"モデル: {model_name}, 入力: {n_sentences} 文")
    print(f"{'='*70}")
    
    # --- モデル読込 ---
    print("\n[1/5] モデル読み込み中...")
    tokenizer = GPT2Tokenizer.from_pretrained(model_name)
    model = GPT2Model.from_pretrained(model_name, output_attentions=True)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    model.eval()
    
    n_layers = model.config.n_layer
    print(f"  層数: {n_layers}, デバイス: {device}")
    
    # --- 入力テキスト ---
    print("\n[2/5] 入力テキスト準備...")
    texts = [
        "The history of artificial intelligence began in antiquity, with myths and stories of artificial beings endowed with intelligence.",
        "Machine learning is a subset of artificial intelligence that provides systems the ability to automatically learn and improve from experience.",
        "Natural language processing is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language.",
        "Deep learning is part of a broader family of machine learning methods based on artificial neural networks with representation learning.",
        "Reinforcement learning is an area of machine learning concerned with how intelligent agents ought to take actions in an environment.",
        "Computer vision is an interdisciplinary scientific field that deals with how computers can gain high-level understanding from digital images or videos.",
        "The Transformer architecture was introduced in the paper Attention Is All You Need published in 2017 by researchers at Google.",
        "Large language models are neural network models that are trained on large amounts of text data and can generate human-like text.",
        "The free energy principle suggests that all adaptive systems minimize a quantity called variational free energy.",
        "Information geometry studies probability distributions using concepts from differential geometry such as the Fisher information metric.",
    ]
    texts = texts[:n_sentences]
    print(f"  使用文数: {len(texts)}")
    
    # --- 層別測定 ---
    print("\n[3/5] 層別測定実行中...")
    
    all_layer_entropies = [[] for _ in range(n_layers)]
    all_hidden_states = [[] for _ in range(n_layers + 1)]
    
    for i, text in enumerate(texts):
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs, output_hidden_states=True)
        
        attentions = outputs.attentions
        hidden_states = outputs.hidden_states
        
        for l in range(n_layers):
            attn = attentions[l][0].cpu().numpy()
            e = layer_attention_entropy(attn)
            all_layer_entropies[l].append(e)
            
        for l in range(n_layers + 1):
            hs = hidden_states[l][0].cpu().numpy()
            all_hidden_states[l].append(hs)
    
    # --- 統計量計算 ---
    print("\n[4/5] 統計量計算中...")
    
    # E(l)
    E_l = np.array([np.mean(all_layer_entropies[l]) for l in range(n_layers)])
    E_l_std = np.array([np.std(all_layer_entropies[l]) for l in range(n_layers)])
    
    # 3つの非類似度指標を各層ペアで計算
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
    
    rbf_arr = np.array(rbf_cka_vals)
    proc_arr = np.array(procrustes_vals)
    ang_arr = np.array(angular_vals)
    
    # Θ 指標 (非類似度 = 忘却場の操作的定義)
    Theta_RBF = 1.0 - rbf_arr        # RBF-CKA の補数
    Theta_Proc = proc_arr             # Procrustes 距離 (既に距離)
    Theta_Ang = ang_arr               # Angular 距離 (既に距離)
    
    # --- 相関分析 ---
    print(f"\n{'='*70}")
    print(f"結果")
    print(f"{'='*70}")
    
    print(f"\n層別データ:")
    print(f"{'層':>4} {'E(l)':>8} {'RBF-CKA':>9} {'Θ_RBF':>8} {'ProcDist':>9} {'AngDist':>8}")
    print("-" * 55)
    for l in range(n_layers):
        print(f"{l:>4d} {E_l[l]:>8.4f} {rbf_arr[l]:>9.4f} {Theta_RBF[l]:>8.4f} "
              f"{proc_arr[l]:>9.4f} {ang_arr[l]:>8.4f}")
    
    # Spearman 相関 (E(l) × 各Θ指標)
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
    
    # Θ指標の分散比較 (飽和問題の解消度)
    print(f"\n━━━ 飽和問題の解消度 ━━━")
    for name, arr in [("Θ_RBF", Theta_RBF), ("Θ_Proc", Theta_Proc), ("Θ_Ang", Theta_Ang)]:
        cv = np.std(arr) / (np.mean(arr) + 1e-10)
        n_nonzero = np.sum(arr > 0.001)
        print(f"  {name}: mean={np.mean(arr):.4f}, sd={np.std(arr):.4f}, "
              f"CV={cv:.2f}, 有効点={n_nonzero}/12")
    
    # 判定
    any_supported = any(
        abs(c["spearman_rho"]) >= 0.5 and c["spearman_p"] < 0.05
        for c in correlations.values()
    )
    all_rejected = all(
        abs(c["spearman_rho"]) < 0.5
        for c in correlations.values()
    )
    
    print(f"\n━━━ 仮説判定 ━━━")
    best_metric = max(correlations.items(), key=lambda x: abs(x[1]["spearman_rho"]))
    print(f"  最強指標: {best_metric[0]} (ρ={best_metric[1]['spearman_rho']}, p={best_metric[1]['spearman_p']})")
    print(f"  漏斗パターン: τ={tau:.4f}, p={tau_p:.6f}")
    
    if any_supported:
        print(f"  判定: ✅ 支持 — 少なくとも1指標で |ρ| ≥ 0.5 (p < 0.05)")
    elif all_rejected:
        print(f"  判定: ❌ 棄却 — 全指標で |ρ| < 0.5")
    else:
        print(f"  判定: ⚠️ 混在 — 一部で閾値以上だが有意でない")
    
    # 結果保存
    result = {
        "experiment": "P1_verification_v2_rbf_cka",
        "model": model_name,
        "n_layers": n_layers,
        "n_sentences": len(texts),
        "device": str(device),
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
    
    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "pei_p1_rbf_cka_results.json")
    with open(outpath, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 結果を {outpath} に保存")
    
    return result


if __name__ == "__main__":
    run_experiment(n_sentences=10, model_name="gpt2")
