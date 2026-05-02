#!/usr/bin/env python3
"""
Sloppy Spectrum 実証: 3 つの Active Inference 生成モデルの Fisher 行列を明示計算し、
有効次元 d_eff を求める。

PURPOSE: HGK の 7 座標が Fisher 固有空間の「次元」ではなく、
「支配的固有方向の数 (d_eff)」として現れるかどうかを検証する。

模型:
  (a) 1 次元ガウス (dim(M) = 2) — 基線
  (b) 階層的ガウス 3 層 (dim(M) = 6) — active inference 標準モデル
  (c) POMDP カテゴリカル (dim(M) = n-1) — 離散 active inference

d_eff の定義:
  participation ratio: d_eff = (Σ λ_i)² / Σ λ_i²
"""

import numpy as np
from typing import NamedTuple


class FisherResult(NamedTuple):
    model_name: str
    dim_M: int
    eigenvalues: np.ndarray
    d_eff_participation: float
    d_eff_cumvar95: int


def model_a_univariate_gaussian(mu: float = 0.0, sigma: float = 1.0) -> FisherResult:
    """模型 (a): 1 次元ガウス N(μ, σ²)

    十分統計量: {x, x²} → dim(M) = 2
    Fisher 行列 (μ, σ² パラメトリゼーション):
      G = diag(1/σ², 1/(2σ⁴))

    SOURCE: Amari 2016 §1.3; Claude.ai analysis L37
    """
    G = np.diag([1.0 / sigma**2, 1.0 / (2.0 * sigma**4)])
    eigenvalues = np.sort(np.linalg.eigvalsh(G))[::-1]

    sum_sq = np.sum(eigenvalues)**2
    sq_sum = np.sum(eigenvalues**2)
    d_eff = sum_sq / sq_sum if sq_sum > 0 else 0

    # 累積分散 95%
    cumvar = np.cumsum(eigenvalues) / np.sum(eigenvalues)
    d_eff_95 = int(np.searchsorted(cumvar, 0.95) + 1)

    return FisherResult("(a) 1D Gaussian N(μ,σ²)", 2, eigenvalues, d_eff, d_eff_95)


def model_b_hierarchical_gaussian(
    n_levels: int = 3,
    precisions: list[float] | None = None,
) -> FisherResult:
    """模型 (b): 階層的ガウス n 層

    Active inference 標準モデル: 各レベルで μ_l, π_l (平均, 精度)
    dim(M) = 2 * n_levels

    階層的生成モデル:
      p(y | μ₁) = N(y; μ₁, π₁⁻¹)
      p(μ_l | μ_{l+1}) = N(μ_l; μ_{l+1}, π_{l+1}⁻¹)

    Fisher 行列 (Laplace 近似下):
      G ≈ -∇² ln p(η|b) = block diagonal with coupling
      各レベルの対角ブロック: diag(π_l, 1/(2π_l²))
      レベル間カップリング: -π_{l+1} (各 μ 間)

    SOURCE: Da Costa et al. 2021 §3 (natural gradient);
            Bogacz 2017 (predictive coding の Fisher 行列)
    """
    if precisions is None:
        # 典型的な active inference 精度の階層: 上位ほど精度が低い
        precisions = [10.0, 3.0, 1.0][:n_levels]

    dim = 2 * n_levels  # (μ_l, π_l) for each level

    # Fisher 行列の構築
    G = np.zeros((dim, dim))

    for l in range(n_levels):
        pi_l = precisions[l]
        # μ_l の Fisher 情報: π_l (精度そのもの)
        G[2*l, 2*l] = pi_l
        # π_l の Fisher 情報: 1/(2π_l²) (ガウス精度パラメータの Fisher 情報)
        G[2*l+1, 2*l+1] = 1.0 / (2.0 * pi_l**2)

        # レベル間カップリング (μ_l と μ_{l+1})
        if l < n_levels - 1:
            pi_next = precisions[l + 1]
            # 上位レベルの精度が下位レベルの μ に影響
            G[2*l, 2*(l+1)] = -pi_next * 0.1  # 弱い結合
            G[2*(l+1), 2*l] = -pi_next * 0.1

    # 対称化 (数値安定性)
    G = (G + G.T) / 2.0

    eigenvalues = np.sort(np.linalg.eigvalsh(G))[::-1]
    eigenvalues = np.abs(eigenvalues)  # 数値誤差で負になる微小固有値を処理

    sum_sq = np.sum(eigenvalues)**2
    sq_sum = np.sum(eigenvalues**2)
    d_eff = sum_sq / sq_sum if sq_sum > 0 else 0

    cumvar = np.cumsum(eigenvalues) / np.sum(eigenvalues)
    d_eff_95 = int(np.searchsorted(cumvar, 0.95) + 1)

    return FisherResult(
        f"(b) Hierarchical Gaussian {n_levels}-level", dim, eigenvalues, d_eff, d_eff_95
    )


def model_c_pomdp_categorical(
    n_states: int = 8,
    state_probs: np.ndarray | None = None,
) -> FisherResult:
    """模型 (c): POMDP カテゴリカル (n 状態)

    dim(M) = n - 1 (simplex)
    Fisher 行列: G = diag(1/s₁, ..., 1/sₙ) restricted to simplex

    SOURCE: Da Costa et al. 2021 Eq.13-15; Claude.ai analysis L23-25
    """
    if state_probs is None:
        # 非一様な信念分布 (typical active inference)
        raw = np.array([10.0, 5.0, 3.0, 2.0, 1.5, 1.0, 0.5, 0.3][:n_states])
        state_probs = raw / raw.sum()

    # Fisher 行列 on simplex: G = diag(1/s_i) (full n×n)
    # simplex 上の有効行列は (n-1)×(n-1) だが、固有値は 1/s_i
    G_full = np.diag(1.0 / state_probs)

    eigenvalues = np.sort(np.linalg.eigvalsh(G_full))[::-1]

    sum_sq = np.sum(eigenvalues)**2
    sq_sum = np.sum(eigenvalues**2)
    d_eff = sum_sq / sq_sum if sq_sum > 0 else 0

    cumvar = np.cumsum(eigenvalues) / np.sum(eigenvalues)
    d_eff_95 = int(np.searchsorted(cumvar, 0.95) + 1)

    return FisherResult(
        f"(c) POMDP Categorical {n_states}-state", n_states, eigenvalues, d_eff, d_eff_95
    )


def run_analysis():
    """3 模型の Fisher 行列を計算し d_eff を比較する。"""

    print("=" * 70)
    print("Sloppy Spectrum 実証: Fisher 行列の固有値分析")
    print("=" * 70)

    results = [
        model_a_univariate_gaussian(sigma=1.0),
        model_b_hierarchical_gaussian(n_levels=3, precisions=[10.0, 3.0, 1.0]),
        model_b_hierarchical_gaussian(n_levels=4, precisions=[10.0, 5.0, 2.0, 0.5]),
        model_b_hierarchical_gaussian(n_levels=5, precisions=[20.0, 10.0, 5.0, 2.0, 0.5]),
        model_c_pomdp_categorical(n_states=4),
        model_c_pomdp_categorical(n_states=8),
        model_c_pomdp_categorical(n_states=16),
    ]

    print("\n## 結果サマリー\n")
    print(f"{'模型':<45} {'dim(M)':>6} {'d_eff(PR)':>10} {'d_eff(95%)':>10}")
    print("-" * 75)

    for r in results:
        print(f"{r.model_name:<45} {r.dim_M:>6} {r.d_eff_participation:>10.2f} {r.d_eff_cumvar95:>10}")

    print("\n\n## 詳細: 固有値スペクトル\n")

    for r in results:
        print(f"\n### {r.model_name} (dim={r.dim_M})")
        print(f"  固有値: {np.array2string(r.eigenvalues, precision=4, separator=', ')}")
        print(f"  d_eff (participation ratio): {r.d_eff_participation:.3f}")
        print(f"  d_eff (cumvar 95%): {r.d_eff_cumvar95}")

        # Sloppy 判定
        if len(r.eigenvalues) > 1:
            ratio = r.eigenvalues[0] / r.eigenvalues[-1]
            print(f"  λ_max/λ_min = {ratio:.1f}")
            if ratio > 10:
                print(f"  → ✅ Sloppy spectrum (>10x range)")
            else:
                print(f"  → ❌ Non-sloppy (<10x range)")

    # d_eff のロバスト性検証
    print("\n\n## d_eff のロバスト性分析\n")

    # 階層ガウスの層数を 3-7 で変化させる
    print("### 階層的ガウス: 層数を変化させたときの d_eff\n")
    print(f"{'層数':>4} {'dim(M)':>6} {'d_eff(PR)':>10} {'d_eff(95%)':>10}")
    print("-" * 35)

    for n in range(2, 8):
        precs = [20.0 / (2**l) for l in range(n)]
        r = model_b_hierarchical_gaussian(n_levels=n, precisions=precs)
        print(f"{n:>4} {r.dim_M:>6} {r.d_eff_participation:>10.2f} {r.d_eff_cumvar95:>10}")

    # POMDP の状態数を変化させる
    print("\n### POMDP カテゴリカル: 状態数を変化させたときの d_eff\n")
    print(f"{'状態数':>6} {'dim(M)':>6} {'d_eff(PR)':>10} {'d_eff(95%)':>10}")
    print("-" * 35)

    for n in [3, 4, 6, 8, 12, 16, 32]:
        r = model_c_pomdp_categorical(n_states=n)
        print(f"{n:>6} {r.dim_M:>6} {r.d_eff_participation:>10.2f} {r.d_eff_cumvar95:>10}")


if __name__ == "__main__":
    run_analysis()
