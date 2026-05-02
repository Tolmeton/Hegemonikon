#!/usr/bin/env python3
"""
Sloppy Spectrum 延長実験: d_eff=6 飽和の信念分布依存性

PURPOSE: POMDP で観測された d_eff(95%)=6 飽和が
  - 信念分布の「形」(指数, Zipf, 一様, 集中) にどう依存するか
  - 分布のパラメータ (温度, 指数) でどう変化するか
  を系統的に調べる。

仮説: d_eff 飽和値は分布の「尖り具合」(エントロピー) に支配される
"""

import numpy as np


def fisher_d_eff(probs: np.ndarray) -> tuple[float, int, np.ndarray]:
    """Fisher 行列の d_eff を計算。

    Returns: (d_eff_PR, d_eff_95, eigenvalues)
    """
    eigenvalues = np.sort(1.0 / probs)[::-1]
    total = np.sum(eigenvalues)
    d_eff_pr = total**2 / np.sum(eigenvalues**2)
    cumvar = np.cumsum(eigenvalues) / total
    d_eff_95 = int(np.searchsorted(cumvar, 0.95) + 1)
    return d_eff_pr, d_eff_95, eigenvalues


def make_distributions(n_states: int) -> dict[str, np.ndarray]:
    """各種信念分布を生成。"""
    dists = {}

    # 1. 一様分布 (最大エントロピー)
    dists["uniform"] = np.ones(n_states) / n_states

    # 2. 指数分布 (異なる温度)
    for temp in [0.3, 0.5, 1.0, 2.0, 5.0]:
        raw = np.exp(-np.arange(n_states) / temp)
        dists[f"exp(T={temp})"] = raw / raw.sum()

    # 3. Zipf の法則 (異なる指数)
    for alpha in [0.5, 1.0, 1.5, 2.0, 3.0]:
        raw = 1.0 / (np.arange(1, n_states + 1) ** alpha)
        dists[f"zipf(α={alpha})"] = raw / raw.sum()

    # 4. ソフトマックス (typical active inference)
    for beta in [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]:
        logits = np.linspace(3.0, -3.0, n_states)
        raw = np.exp(beta * logits)
        dists[f"softmax(β={beta})"] = raw / raw.sum()

    # 5. デルタ (1 状態に集中)
    delta = np.ones(n_states) * 0.001
    delta[0] = 1.0
    dists["delta-like"] = delta / delta.sum()

    # 6. 2-peak (双峰)
    bipeak = np.ones(n_states) * 0.01
    bipeak[0] = 1.0
    bipeak[n_states // 2] = 1.0
    dists["bipeak"] = bipeak / bipeak.sum()

    return dists


def entropy(p: np.ndarray) -> float:
    """Shannon エントロピー (bits)。"""
    return -np.sum(p * np.log2(p + 1e-30))


def run_extended_analysis():
    print("=" * 80)
    print("d_eff 飽和実験: 信念分布の形状依存性")
    print("=" * 80)

    # パート 1: 固定状態数 (n=32) で分布形状を変化
    n = 32
    dists = make_distributions(n)

    print(f"\n## パート1: n={n} 状態、分布形状の変化\n")
    print(f"{'分布':<25} {'H(bits)':>8} {'d_eff(PR)':>10} {'d_eff(95%)':>10} {'λmax/λmin':>12}")
    print("-" * 70)

    results = []
    for name, p in sorted(dists.items(), key=lambda x: -entropy(x[1])):
        d_pr, d_95, eig = fisher_d_eff(p)
        h = entropy(p)
        ratio = eig[0] / eig[-1]
        print(f"{name:<25} {h:>8.2f} {d_pr:>10.2f} {d_95:>10} {ratio:>12.1f}")
        results.append((name, h, d_pr, d_95, ratio))

    # パート 2: Zipf α=1.0 で状態数を変化 (n=4 → 128)
    print(f"\n\n## パート2: Zipf(α=1.0) 分布、状態数 n を変化\n")
    print(f"{'n':>6} {'H(bits)':>8} {'d_eff(PR)':>10} {'d_eff(95%)':>10} {'λmax/λmin':>12}")
    print("-" * 50)

    for n in [4, 8, 16, 32, 64, 128, 256]:
        raw = 1.0 / np.arange(1, n + 1)
        p = raw / raw.sum()
        d_pr, d_95, eig = fisher_d_eff(p)
        h = entropy(p)
        ratio = eig[0] / eig[-1]
        print(f"{n:>6} {h:>8.2f} {d_pr:>10.2f} {d_95:>10} {ratio:>12.1f}")

    # パート 3: ソフトマックス β を変化 (β → ∞ で集中, β → 0 で一様)
    print(f"\n\n## パート3: ソフトマックス(n=32), β を連続変化\n")
    print(f"{'β':>8} {'H(bits)':>8} {'d_eff(PR)':>10} {'d_eff(95%)':>10}")
    print("-" * 40)

    betas = np.concatenate([
        np.linspace(0.01, 0.1, 5),
        np.linspace(0.2, 1.0, 5),
        np.linspace(1.5, 5.0, 8),
        np.linspace(6.0, 20.0, 8),
    ])
    n = 32
    logits = np.linspace(3.0, -3.0, n)

    beta_d95_pairs = []
    for beta in betas:
        raw = np.exp(beta * logits)
        p = raw / raw.sum()
        d_pr, d_95, _ = fisher_d_eff(p)
        h = entropy(p)
        print(f"{beta:>8.2f} {h:>8.2f} {d_pr:>10.2f} {d_95:>10}")
        beta_d95_pairs.append((beta, h, d_pr, d_95))

    # パート 4: エントロピー vs d_eff の関係
    print(f"\n\n## パート4: エントロピー H vs d_eff(95%) の関係\n")
    print("以下の傾向が見られるか:")
    print("  - H が大きい (一様に近い) → d_eff ≈ n (全方向が等しく重要)")
    print("  - H が小さい (集中) → d_eff は小さい定数に飽和")
    print("  - 中間のエントロピーで d_eff が ≈ 6-7 になる「甘い点」があるか？\n")

    # ソフトマックスの結果からエントロピーの「ゾーン」を特定
    sweet_spot = [(b, h, dpr, d95) for b, h, dpr, d95 in beta_d95_pairs if 5 <= d95 <= 8]
    if sweet_spot:
        print(f"d_eff(95%) ∈ [5, 8] の「甘い点」:")
        print(f"{'β':>8} {'H(bits)':>8} {'d_eff(PR)':>10} {'d_eff(95%)':>10}")
        print("-" * 40)
        for b, h, dpr, d95 in sweet_spot:
            print(f"{b:>8.2f} {h:>8.2f} {dpr:>10.2f} {d95:>10}")

        h_min = min(x[1] for x in sweet_spot)
        h_max = max(x[1] for x in sweet_spot)
        print(f"\n→ エントロピー範囲: {h_min:.2f} 〜 {h_max:.2f} bits")
        print(f"  (最大エントロピー {np.log2(n):.2f} bits の {h_min/np.log2(n)*100:.0f}% 〜 {h_max/np.log2(n)*100:.0f}%)")


if __name__ == "__main__":
    run_extended_analysis()
