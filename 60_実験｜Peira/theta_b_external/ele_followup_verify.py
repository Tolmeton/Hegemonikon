#!/usr/bin/env python3
"""
/ele 未踏項目の検証スクリプト
==============================
A-2: 中間層 (1-10) のみの相関を再計算
A-3: Procrustes 非標準実装を scipy.spatial.procrustes と比較
A-5: (追加) 層0,11 除外時の相関変化を確認

前提: pei_p1_rbf_cka_results.json が同ディレクトリに存在
"""

import json
import os
import numpy as np
from scipy import stats
from scipy.spatial import procrustes as scipy_procrustes


def load_results():
    """前回の実験結果を読み込む"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "pei_p1_rbf_cka_results.json")
    with open(path) as f:
        return json.load(f)


def custom_procrustes(X, Y):
    """measure_attention_cka_v2.py の Procrustes 実装を再現"""
    # 中心化
    X = X - X.mean(axis=0)
    Y = Y - Y.mean(axis=0)
    
    X_norm = np.linalg.norm(X, 'fro')
    Y_norm = np.linalg.norm(Y, 'fro')
    
    if X_norm < 1e-10 or Y_norm < 1e-10:
        return 1.0
    
    X = X / X_norm
    Y = Y / Y_norm
    
    # SVD
    U, _, Vt = np.linalg.svd(Y.T @ X)
    # 非標準 Procrustes 距離
    d = 1 - np.trace(U @ Vt) ** 2 / X.shape[1]
    return float(np.clip(abs(d), 0, 1))


def scipy_procrustes_distance(X, Y):
    """scipy.spatial.procrustes を使った標準 Procrustes 距離"""
    # scipy.spatial.procrustes は (n, k) の行列を要求
    # 次元が異なる場合はゼロパディング
    if X.shape[1] != Y.shape[1]:
        max_d = max(X.shape[1], Y.shape[1])
        X_pad = np.zeros((X.shape[0], max_d))
        Y_pad = np.zeros((Y.shape[0], max_d))
        X_pad[:, :X.shape[1]] = X
        Y_pad[:, :Y.shape[1]] = Y
        X, Y = X_pad, Y_pad
    
    _, _, disparity = scipy_procrustes(X, Y)
    return float(disparity)


def a2_midlayer_correlation(data):
    """A-2: 中間層 (1-10) のみの相関"""
    print("\n" + "=" * 70)
    print("A-2: 中間層 (層1-10) のみの相関再計算")
    print("=" * 70)
    
    layer_data = data["layer_data"]
    E_l = np.array(layer_data["E_l"])
    Theta_RBF = np.array(layer_data["Theta_RBF"])
    Theta_Proc = np.array(layer_data["Procrustes_dist"])
    Theta_Ang = np.array(layer_data["Angular_dist"])
    
    # 全層 vs 中間層
    mid = slice(1, 11)  # 層1-10 (0-indexed)
    
    print(f"\n--- 全層 (0-11, N=12) ---")
    for name, theta in [("Θ_RBF", Theta_RBF), ("Θ_Proc", Theta_Proc), ("Θ_Ang", Theta_Ang)]:
        rho, p = stats.spearmanr(E_l, theta)
        pr, pp = stats.pearsonr(E_l, theta)
        print(f"  {name:>8}: Spearman ρ={rho:+.4f} (p={p:.4f}), Pearson r={pr:+.4f} (p={pp:.4f})")
    
    print(f"\n--- 中間層 (1-10, N=10) ---")
    results_mid = {}
    for name, theta in [("Θ_RBF", Theta_RBF), ("Θ_Proc", Theta_Proc), ("Θ_Ang", Theta_Ang)]:
        rho, p = stats.spearmanr(E_l[mid], theta[mid])
        pr, pp = stats.pearsonr(E_l[mid], theta[mid])
        results_mid[name] = {"spearman_rho": rho, "spearman_p": p, "pearson_r": pr, "pearson_p": pp}
        print(f"  {name:>8}: Spearman ρ={rho:+.4f} (p={p:.4f}), Pearson r={pr:+.4f} (p={pp:.4f})")
    
    # 外れ値の影響可視化
    print(f"\n--- 層0 と層11 のデータ ---")
    print(f"  層0:  E={E_l[0]:.4f}, Θ_RBF={Theta_RBF[0]:.4f}, Θ_Proc={Theta_Proc[0]:.4f}, Θ_Ang={Theta_Ang[0]:.4f}")
    print(f"  層11: E={E_l[11]:.4f}, Θ_RBF={Theta_RBF[11]:.4f}, Θ_Proc={Theta_Proc[11]:.4f}, Θ_Ang={Theta_Ang[11]:.4f}")
    print(f"  中間層 E(l) 範囲: [{E_l[mid].min():.4f}, {E_l[mid].max():.4f}]")
    print(f"  中間層 Θ_RBF 範囲: [{Theta_RBF[mid].min():.4f}, {Theta_RBF[mid].max():.4f}]")
    
    return results_mid


def a3_procrustes_comparison(data):
    """A-3: カスタム vs scipy Procrustes 距離の比較"""
    print("\n" + "=" * 70)
    print("A-3: カスタム Procrustes vs scipy.spatial.procrustes")
    print("=" * 70)
    
    # テスト行列で比較
    np.random.seed(42)
    n_tests = 5
    
    print(f"\n--- ランダム行列での比較 (n={n_tests}) ---")
    print(f"{'テスト':>6} {'カスタム':>10} {'scipy':>10} {'差':>10} {'関係':>12}")
    
    custom_vals = []
    scipy_vals = []
    
    for i in range(n_tests):
        n, d = 20, 64
        X = np.random.randn(n, d)
        
        # 異なるレベルの変換を適用
        scale = 0.1 * (i + 1)
        Y = X + np.random.randn(n, d) * scale
        
        c = custom_procrustes(X, Y)
        s = scipy_procrustes_distance(X, Y)
        
        custom_vals.append(c)
        scipy_vals.append(s)
        
        print(f"{i+1:>6} {c:>10.6f} {s:>10.6f} {abs(c-s):>10.6f} {'モノトニック?' if i == 0 else ''}")
    
    # モノトニシティチェック: 両者が同じ順序を保つか
    custom_rank = stats.rankdata(custom_vals)
    scipy_rank = stats.rankdata(scipy_vals)
    rank_corr, _ = stats.spearmanr(custom_vals, scipy_vals)
    print(f"\n  順位相関 (カスタム vs scipy): ρ = {rank_corr:.4f}")
    print(f"  カスタム順位: {custom_rank}")
    print(f"  scipy 順位:   {scipy_rank}")
    
    # 同一行列テスト
    print(f"\n--- 同一行列テスト ---")
    X_same = np.random.randn(10, 32)
    c_same = custom_procrustes(X_same, X_same.copy())
    s_same = scipy_procrustes_distance(X_same, X_same.copy())
    print(f"  カスタム(X,X) = {c_same:.8f}")
    print(f"  scipy(X,X)    = {s_same:.8f}")
    
    # 直交変換不変性テスト
    print(f"\n--- 直交変換不変性テスト ---")
    X_orth = np.random.randn(10, 32)
    Q, _ = np.linalg.qr(np.random.randn(32, 32))
    Y_orth = X_orth @ Q
    c_orth = custom_procrustes(X_orth, Y_orth)
    s_orth = scipy_procrustes_distance(X_orth, Y_orth)
    print(f"  カスタム(X, XQ) = {c_orth:.8f}  (理想: 0)")
    print(f"  scipy(X, XQ)    = {s_orth:.8f}  (理想: 0)")
    
    return {"rank_correlation": rank_corr, "custom_vals": custom_vals, "scipy_vals": scipy_vals}


def sensitivity_analysis(data):
    """追加: 各外れ値除外パターンの感度分析"""
    print("\n" + "=" * 70)
    print("追加: Jackknife 感度分析 (1層ずつ除外)")
    print("=" * 70)
    
    layer_data = data["layer_data"]
    E_l = np.array(layer_data["E_l"])
    Theta_Ang = np.array(layer_data["Angular_dist"])
    
    n = len(E_l)
    rho_full, _ = stats.spearmanr(E_l, Theta_Ang)
    
    print(f"\n  全層 Θ_Ang Spearman ρ = {rho_full:.4f}")
    print(f"\n  {'除外層':>6} {'ρ':>8} {'Δρ':>8} {'影響':>8}")
    print("  " + "-" * 35)
    
    for i in range(n):
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        rho_i, _ = stats.spearmanr(E_l[mask], Theta_Ang[mask])
        delta = rho_i - rho_full
        influence = "★★★" if abs(delta) > 0.1 else ("★★" if abs(delta) > 0.05 else "")
        print(f"  {i:>6} {rho_i:>8.4f} {delta:>+8.4f} {influence:>8}")


def main():
    data = load_results()
    
    print("=" * 70)
    print("/ele 未踏項目検証")
    print("=" * 70)
    
    # A-2: 中間層のみの相関
    mid_results = a2_midlayer_correlation(data)
    
    # A-3: Procrustes 比較
    proc_results = a3_procrustes_comparison(data)
    
    # 追加: Jackknife 感度分析
    sensitivity_analysis(data)
    
    # 結果まとめ
    print("\n" + "=" * 70)
    print("まとめ")
    print("=" * 70)
    
    print(f"\nA-2 結果:")
    for name, r in mid_results.items():
        status = "✅ |ρ|≥0.5" if abs(r["spearman_rho"]) >= 0.5 else "❌ |ρ|<0.5"
        sig = "有意" if r["spearman_p"] < 0.05 else "非有意"
        print(f"  {name}: ρ={r['spearman_rho']:+.4f} ({sig}), r={r['pearson_r']:+.4f} → {status}")
    
    print(f"\nA-3 結果:")
    print(f"  カスタム-scipy 順位相関: ρ={proc_results['rank_correlation']:.4f}")
    if proc_results['rank_correlation'] > 0.9:
        print(f"  → ✅ モノトニシティ保持。距離性は実質的に同等")
    else:
        print(f"  → ⚠️ 順位が一致しない。カスタム実装に問題あり")
    
    # JSON 保存
    output = {
        "a2_midlayer": {name: {k: round(float(v), 6) for k, v in r.items()} for name, r in mid_results.items()},
        "a3_procrustes": {
            "rank_correlation": round(proc_results["rank_correlation"], 4),
            "monotonicity_preserved": proc_results["rank_correlation"] > 0.9,
        }
    }
    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "ele_followup_results.json")
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 結果を {outpath} に保存")


if __name__ == "__main__":
    main()
