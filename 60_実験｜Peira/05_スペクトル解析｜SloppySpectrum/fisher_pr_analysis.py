#!/usr/bin/env python3
"""
Participation Ratio (PR) ベースの d_eff — カットオフ非依存な有効次元

PR = (Σ λ_i)² / Σ λ_i²

PR は任意のカットオフに依存しない自然な有効次元の定義。
d_eff(95%) が 95% カットオフ依存だったのに対し、PR は内在的量。

検証:
  1. PR の n-独立性: d_eff(PR) が特定の H で定数に収束するか？
  2. H vs d_eff(PR) の普遍関数関係
  3. d_eff(PR) ≈ 7 となる H の値
  4. 解析的導出: PR の連続極限での閉じた形
"""

import numpy as np
from scipy.optimize import brentq


def fisher_metrics(probs: np.ndarray) -> dict:
    """Fisher 情報行列の各種メトリクスを計算。"""
    eigenvalues = 1.0 / probs  # Fisher: F_ii = 1/p_i
    total = np.sum(eigenvalues)
    
    pr = total**2 / np.sum(eigenvalues**2)
    
    sorted_eigs = np.sort(eigenvalues)[::-1]
    cumvar = np.cumsum(sorted_eigs) / total
    d95 = int(np.searchsorted(cumvar, 0.95) + 1)
    d90 = int(np.searchsorted(cumvar, 0.90) + 1)
    d99 = int(np.searchsorted(cumvar, 0.99) + 1)
    
    return {'pr': pr, 'd95': d95, 'd90': d90, 'd99': d99}


def softmax_probs(n: int, beta: float, logit_range: float = 3.0) -> np.ndarray:
    logits = np.linspace(logit_range, -logit_range, n)
    raw = np.exp(beta * logits)
    return raw / raw.sum()


def entropy_bits(probs: np.ndarray) -> float:
    return -np.sum(probs * np.log2(probs + 1e-30))


def pr_continuum(alpha: float) -> float:
    """連続極限での Participation Ratio (n に依存しない部分)。
    
    λ(x) = 1/p(x) ∝ exp(-αx),  x ∈ [-1, 1]
    
    Σλ → ∫ exp(-αx) dx = 2sinh(α)/α
    Σλ² → ∫ exp(-2αx) dx = 2sinh(2α)/(2α) = sinh(2α)/α
    
    PR_continuum = (Σλ)² / Σλ² = [2sinh(α)/α]² / [sinh(2α)/α]
                 = 4 sinh²(α) / (α × sinh(2α))
                 = 4 sinh²(α) / (α × 2 sinh(α) cosh(α))
                 = 2 sinh(α) / (α × cosh(α))
                 = 2 tanh(α) / α
    """
    if alpha < 1e-6:
        return 2.0  # lim = 2 (一様)
    return 2.0 * np.tanh(alpha) / alpha


def run_pr_analysis():
    print("=" * 80)
    print("Participation Ratio (PR) — カットオフ非依存な有効次元")
    print("=" * 80)

    # ============================================================
    # 検証 1: 連続極限 PR の閉じた形の解析式
    # ============================================================
    print("\n## 発見: PR の連続極限は閉じた形を持つ\n")
    print("  PR_continuous = 2 tanh(α) / α")
    print("  ここで α = β × L (ソフトマックス実効温度)\n")
    print("  α → 0:  PR → 2 (一様分布に近い)")
    print("  α → ∞:  PR → 0 (δ関数に近い)\n")
    
    print("  離散の場合: PR_discrete ≈ PR_continuous × n/2")
    print("  (n/2 は [-1,1] の離散化密度のスケーリング)\n")

    # ============================================================
    # 検証 2: 解析的 PR vs 離散計算の比較
    # ============================================================
    print("\n## 検証: PR の解析式 vs 離散計算\n")
    print(f"{'α':>6} {'PR(n=32)':>10} {'PR(n=64)':>10} {'PR(n=128)':>10} {'PR×n/2(32)':>12} {'2tanh(α)/α':>12}")
    print("-" * 65)
    
    for alpha in [0.5, 1.0, 2.0, 3.0, 5.0, 7.73, 10.0, 15.0, 20.0]:
        pr32 = fisher_metrics(softmax_probs(32, alpha/3.0, 3.0))['pr']
        pr64 = fisher_metrics(softmax_probs(64, alpha/3.0, 3.0))['pr']
        pr128 = fisher_metrics(softmax_probs(128, alpha/3.0, 3.0))['pr']
        pr_cont = pr_continuum(alpha)
        # PR_discrete ≈ PR_cont × n/2 ?
        print(f"{alpha:>6.2f} {pr32:>10.3f} {pr64:>10.3f} {pr128:>10.3f} {pr32/(32/2):>12.6f} {pr_cont:>12.6f}")

    # ============================================================
    # 検証 3: d_eff(PR) = 7 となる条件
    # ============================================================
    print(f"\n\n## d_eff(PR) = 7 となる α の解析的導出\n")
    print("条件: PR_discrete = n × tanh(α) / α = 7")
    print("→ tanh(α) / α = 7/n\n")
    
    print(f"{'n':>6} {'α* (数値)':>12} {'H* (bits)':>10} {'2^H*':>8} {'d_eff(95%)':>10}")
    print("-" * 52)
    
    for n in [8, 12, 16, 24, 32, 48, 64, 96, 128, 256]:
        target = 7.0 / n
        # tanh(α)/α = target を解く
        # tanh(α)/α は α=0 で 1, α→∞ で 0 (単調減少)
        if target >= 1.0:
            print(f"{n:>6} {'N/A (PR>n)':>12}")
            continue
        
        def eq(a):
            return np.tanh(a) / a - target
        
        try:
            alpha_sol = brentq(eq, 0.01, 200.0)
            beta = alpha_sol / 3.0  # logit_range = 3.0
            p = softmax_probs(n, beta, 3.0)
            h = entropy_bits(p)
            metrics = fisher_metrics(p)
            print(f"{n:>6} {alpha_sol:>12.4f} {h:>10.4f} {2**h:>8.2f} {metrics['d95']:>10}")
        except Exception as e:
            print(f"{n:>6} {'ERROR':>12} {str(e)}")

    # ============================================================
    # 検証 4: H vs d_eff(PR) の普遍関数関係
    # ============================================================
    print(f"\n\n## H vs d_eff(PR) の関係 — 複数の n\n")
    print(f"{'H/H_max':>8} {'H(bits)':>8}", end="")
    for n in [16, 32, 64, 128]:
        print(f" {'PR(n='+str(n)+')':>10}", end="")
    print()
    print("-" * 55)
    
    for target_hr in np.arange(0.10, 0.95, 0.05):
        vals = []
        h_ref = None
        for n in [16, 32, 64, 128]:
            best_beta = None
            best_diff = float('inf')
            for beta in np.linspace(0.01, 30.0, 2000):
                p = softmax_probs(n, beta)
                hr = entropy_bits(p) / np.log2(n)
                diff = abs(hr - target_hr)
                if diff < best_diff:
                    best_diff = diff
                    best_beta = beta
            
            p = softmax_probs(n, best_beta)
            pr_val = fisher_metrics(p)['pr']
            vals.append(pr_val)
            if n == 32:
                h_ref = entropy_bits(p)
        
        print(f"{target_hr:>8.2f} {h_ref:>8.2f}", end="")
        for v in vals:
            print(f" {v:>10.2f}", end="")
        print()

    # ============================================================
    # 検証 5: PR/n vs H/H_max (スケーリング崩壊)
    # ============================================================
    print(f"\n\n## PR/n vs H/H_max — スケーリング崩壊の確認\n")
    print(f"{'H/H_max':>8}", end="")
    for n in [16, 32, 64, 128]:
        print(f" {'PR/n('+str(n)+')':>10}", end="")
    print()
    print("-" * 50)
    
    for target_hr in np.arange(0.10, 0.95, 0.05):
        print(f"{target_hr:>8.2f}", end="")
        for n in [16, 32, 64, 128]:
            best_beta = None
            best_diff = float('inf')
            for beta in np.linspace(0.01, 30.0, 2000):
                p = softmax_probs(n, beta)
                hr = entropy_bits(p) / np.log2(n)
                diff = abs(hr - target_hr)
                if diff < best_diff:
                    best_diff = diff
                    best_beta = beta
            
            p = softmax_probs(n, best_beta)
            pr_val = fisher_metrics(p)['pr']
            print(f" {pr_val/n:>10.4f}", end="")
        print()

    # ============================================================
    # 検証 6: 解析式 tanh(α)/α = 7/n の α* → H* の追跡
    # ============================================================
    print(f"\n\n## 解析的まとめ\n")
    print("PR = n × tanh(α) / α  (離散近似)")
    print("PR = 7 → tanh(α)/α = 7/n")
    print()
    print("n → ∞ のとき tanh(α)/α → 0 なので α → ∞")
    print("tanh(α) → 1 のとき: 1/α ≈ 7/n → α ≈ n/7")
    print()
    print("漸近解:")
    print("  α* ≈ n/7  (n → ∞)")
    print(f"  β*×L ≈ n/d_eff")
    print()
    print("これは d_eff(95%) の漸近解 α* ≈ (ln20/2) × n/k と同じ構造。")
    print(f"  d_eff(95%): α* ≈ {np.log(20)/2:.4f} × n/7 = {np.log(20)/2/7:.4f} × n")
    print(f"  d_eff(PR):  α* ≈ 1/7 × n = {1/7:.4f} × n")
    print()
    print("PR 版は自然定数を含まない (ln 20 が消える)。")
    print("PR は本質的に tanh の逆関数で決まる。")


if __name__ == "__main__":
    run_pr_analysis()
