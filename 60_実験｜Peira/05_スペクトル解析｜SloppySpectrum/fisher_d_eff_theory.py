#!/usr/bin/env python3
"""
50% エントロピー条件の理論的検証

検証項目:
  1. n-独立性: 状態数 n を変えても H/H_max ≈ 50% で d_eff ≈ 7 か？
  2. パラメトリゼーション独立性: logit の範囲を変えても同じか？
  3. H/H_max vs d_eff(95%) の厳密な関数関係
  4. d_eff=7 の β 値を各 n で逆算 → 普遍定数か？
"""

import numpy as np


def fisher_d_eff_95(probs: np.ndarray) -> int:
    eigenvalues = np.sort(1.0 / probs)[::-1]
    cumvar = np.cumsum(eigenvalues) / np.sum(eigenvalues)
    return int(np.searchsorted(cumvar, 0.95) + 1)


def entropy_ratio(probs: np.ndarray) -> float:
    h = -np.sum(probs * np.log2(probs + 1e-30))
    h_max = np.log2(len(probs))
    return h / h_max


def softmax_probs(n: int, beta: float, logit_range: float = 3.0) -> np.ndarray:
    logits = np.linspace(logit_range, -logit_range, n)
    raw = np.exp(beta * logits)
    return raw / raw.sum()


def find_beta_for_d_eff(n: int, target_d_eff: int, logit_range: float = 3.0) -> float | None:
    """二分探索で d_eff(95%) = target_d_eff となる β を見つける。"""
    # β が大きいほど d_eff は小さい
    # 粗いスキャンでブラケットを見つける
    betas = np.linspace(0.01, 30.0, 3000)
    for i in range(len(betas) - 1):
        p1 = softmax_probs(n, betas[i], logit_range)
        p2 = softmax_probs(n, betas[i + 1], logit_range)
        d1 = fisher_d_eff_95(p1)
        d2 = fisher_d_eff_95(p2)
        if d1 >= target_d_eff and d2 < target_d_eff:
            # d_eff が target に最も近い β
            return (betas[i] + betas[i + 1]) / 2
    return None


def run_deep_analysis():
    print("=" * 80)
    print("50% エントロピー条件の理論的検証")
    print("=" * 80)

    # ============================================================
    # 検証 1: n-独立性
    # 各 n に対して d_eff(95%) = 7 となる β を見つけ、H/H_max を記録
    # ============================================================
    print("\n## 検証 1: n-独立性 — d_eff(95%)=7 となる β と H/H_max\n")
    print(f"{'n':>6} {'β*':>8} {'H/H_max':>8} {'H (bits)':>9} {'H_max':>6}")
    print("-" * 42)

    n_values = [8, 12, 16, 24, 32, 48, 64, 96, 128, 256]
    for n in n_values:
        beta = find_beta_for_d_eff(n, 7)
        if beta:
            p = softmax_probs(n, beta)
            hr = entropy_ratio(p)
            h = -np.sum(p * np.log2(p + 1e-30))
            h_max = np.log2(n)
            print(f"{n:>6} {beta:>8.3f} {hr:>8.3f} {h:>9.2f} {h_max:>6.2f}")
        else:
            print(f"{n:>6}    N/A      N/A       N/A    N/A")

    # ============================================================
    # 検証 2: logit 範囲の依存性
    # ============================================================
    print(f"\n\n## 検証 2: logit 範囲の依存性 (n=32)\n")
    print(f"{'logit_range':>12} {'β*':>8} {'H/H_max':>8}")
    print("-" * 32)

    for lr in [1.0, 2.0, 3.0, 5.0, 10.0]:
        beta = find_beta_for_d_eff(32, 7, lr)
        if beta:
            p = softmax_probs(32, beta, lr)
            hr = entropy_ratio(p)
            print(f"{lr:>12.1f} {beta:>8.3f} {hr:>8.3f}")
        else:
            print(f"{lr:>12.1f}    N/A      N/A")

    # ============================================================
    # 検証 3: H/H_max vs d_eff の厳密な関数関係 (複数の n)
    # ============================================================
    print(f"\n\n## 検証 3: H/H_max vs d_eff(95%) の関係 = f(H/H_max) は n-普遍か？\n")
    print(f"{'H/H_max':>8}", end="")
    for n in [16, 32, 64, 128]:
        print(f" {'n='+str(n):>8}", end="")
    print()
    print("-" * 42)

    for target_hr in np.arange(0.10, 0.95, 0.05):
        print(f"{target_hr:>8.2f}", end="")
        for n in [16, 32, 64, 128]:
            # β を調整して H/H_max ≈ target_hr にする
            best_beta = None
            best_diff = float('inf')
            for beta in np.linspace(0.01, 30.0, 1000):
                p = softmax_probs(n, beta)
                hr = entropy_ratio(p)
                diff = abs(hr - target_hr)
                if diff < best_diff:
                    best_diff = diff
                    best_beta = beta

            p = softmax_probs(n, best_beta)
            d95 = fisher_d_eff_95(p)
            print(f" {d95:>8}", end="")
        print()

    # ============================================================
    # 検証 4: d_eff(95%) / n vs H/H_max の関係
    # → d_eff/n が H/H_max の普遍関数であれば、d_eff=7 は n=14 付近で出る「はず」
    # ============================================================
    print(f"\n\n## 検証 4: d_eff(95%)/n vs H/H_max\n")
    print(f"{'H/H_max':>8}", end="")
    for n in [16, 32, 64, 128]:
        print(f" {'n='+str(n):>8}", end="")
    print()
    print("-" * 42)

    for target_hr in np.arange(0.10, 0.95, 0.05):
        print(f"{target_hr:>8.2f}", end="")
        for n in [16, 32, 64, 128]:
            best_beta = None
            best_diff = float('inf')
            for beta in np.linspace(0.01, 30.0, 1000):
                p = softmax_probs(n, beta)
                hr = entropy_ratio(p)
                diff = abs(hr - target_hr)
                if diff < best_diff:
                    best_diff = diff
                    best_beta = beta

            p = softmax_probs(n, best_beta)
            d95 = fisher_d_eff_95(p)
            ratio = d95 / n
            print(f" {ratio:>8.3f}", end="")
        print()

    # ============================================================
    # 検証 5: β * logit_range (実効温度) の普遍性
    # ============================================================
    print(f"\n\n## 検証 5: β* × logit_range = 実効温度 (n=32)\n")
    print(f"{'logit_range':>12} {'β*':>8} {'β*×LR':>8}")
    print("-" * 32)

    for lr in [1.0, 2.0, 3.0, 5.0, 10.0]:
        beta = find_beta_for_d_eff(32, 7, lr)
        if beta:
            print(f"{lr:>12.1f} {beta:>8.3f} {beta*lr:>8.3f}")


if __name__ == "__main__":
    run_deep_analysis()
