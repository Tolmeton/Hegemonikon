#!/usr/bin/env python3
"""
忘却の場の方程式 — ガウス族 Toy Model の数値計算と可視化

Paper I §4 の解析結果を数値的に検証する:
  - Fisher 計量 (Poincaré 半平面)
  - Chebyshev 1-form T = (0, 6/σ)
  - 忘却場 Φ(μ,σ) = D_KL(N(μ,σ²) ‖ N(0,1))
  - 忘却接続 A_i = ∂_iΦ + ΦT_i
  - 忘却曲率 F₁₂ = ∂_μA₂ - ∂_σA₁
  - α-dynamics: F₁₂(α) と遷移層プロファイル
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import os

# 出力ディレクトリ
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def phi_gaussian(mu: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """忘却場: Φ = D_KL(N(μ,σ²) ‖ N(0,1))"""
    return -np.log(sigma) + (sigma**2 + mu**2) / 2 - 0.5


def chebyshev_form(sigma: np.ndarray):
    """Chebyshev 1-form: T = (T₁, T₂) = (0, 6/σ)"""
    T1 = np.zeros_like(sigma)
    T2 = 6.0 / sigma
    return T1, T2


def oblivion_connection(mu, sigma, phi, T1, T2):
    """忘却接続: A_i = ∂_iΦ + ΦT_i"""
    # ∂_μΦ = μ
    A1 = mu
    # ∂_σΦ = -1/σ + σ
    A2 = -1.0 / sigma + sigma + phi * T2
    return A1, A2


def curvature_analytic(mu, sigma):
    """解析的曲率: F₁₂ = 6μ/σ"""
    return 6.0 * mu / sigma


def curvature_numerical(mu, sigma, dmu=1e-6, dsigma=1e-6):
    """数値的曲率: F₁₂ = ∂_μA₂ - ∂_σA₁ (有限差分で検証)"""
    # ∂_μA₂ (σ を固定、μ を微小変動)
    phi_p = phi_gaussian(mu + dmu, sigma)
    phi_m = phi_gaussian(mu - dmu, sigma)
    _, T2 = chebyshev_form(sigma)

    A2_p = -1.0 / sigma + sigma + phi_p * T2
    A2_m = -1.0 / sigma + sigma + phi_m * T2
    dA2_dmu = (A2_p - A2_m) / (2 * dmu)

    # ∂_σA₁ = ∂_σ(μ) = 0
    dA1_dsigma = 0.0

    return dA2_dmu - dA1_dsigma


def alpha_curvature(mu, sigma, alpha_func, dalpha_dmu_func, phi):
    """α-依存曲率: F₁₂ = (3/σ)(α·μ + Φ·∂_μα)"""
    alpha = alpha_func(mu)
    dalpha = dalpha_dmu_func(mu)
    return (3.0 / sigma) * (alpha * mu + phi * dalpha)


def plot_curvature_field(save=True):
    """F₁₂ = 6μ/σ の2Dヒートマップ"""
    mu = np.linspace(-5, 5, 200)
    sigma = np.linspace(0.3, 5, 200)
    MU, SIGMA = np.meshgrid(mu, sigma)

    F12_analytic = curvature_analytic(MU, SIGMA)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 1. 忘却場 Φ
    PHI = phi_gaussian(MU, SIGMA)
    im0 = axes[0].pcolormesh(MU, SIGMA, PHI, cmap='magma', shading='auto')
    axes[0].set_title('Oblivion Field  Φ(μ,σ) = D_KL', fontsize=13)
    axes[0].set_xlabel('μ (mean displacement)')
    axes[0].set_ylabel('σ (uncertainty)')
    plt.colorbar(im0, ax=axes[0], label='Φ')

    # 2. 忘却曲率 F₁₂
    vmax = np.percentile(np.abs(F12_analytic), 95)
    im1 = axes[1].pcolormesh(MU, SIGMA, F12_analytic, cmap='RdBu_r',
                              vmin=-vmax, vmax=vmax, shading='auto')
    axes[1].set_title('Oblivion Curvature  F₁₂ = 6μ/σ', fontsize=13)
    axes[1].set_xlabel('μ (mean displacement)')
    axes[1].set_ylabel('σ (uncertainty)')
    axes[1].contour(MU, SIGMA, F12_analytic, levels=[0], colors='black',
                     linewidths=1.5)
    plt.colorbar(im1, ax=axes[1], label='F₁₂ (force)')

    # 3. 曲率の μ-断面 (σ=1)
    mu_1d = np.linspace(-5, 5, 500)
    for s in [0.5, 1.0, 2.0, 4.0]:
        F12_s = curvature_analytic(mu_1d, s)
        axes[2].plot(mu_1d, F12_s, label=f'σ={s:.1f}')
    axes[2].axhline(0, color='gray', linestyle='--', linewidth=0.5)
    axes[2].set_title('F₁₂(μ) at fixed σ', fontsize=13)
    axes[2].set_xlabel('μ')
    axes[2].set_ylabel('F₁₂ = 6μ/σ')
    axes[2].legend()
    axes[2].set_ylim(-35, 35)

    plt.tight_layout()
    if save:
        path = os.path.join(OUT_DIR, 'oblivion_curvature.png')
        plt.savefig(path, dpi=150, bbox_inches='tight')
        print(f"保存: {path}")
    plt.close()


def plot_alpha_dynamics(save=True):
    """α-dynamics: 遷移層プロファイルと力の生成"""
    mu = np.linspace(-5, 5, 500)
    sigma = 1.0
    mu0_list = [0.5, 1.0, 2.0]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 1. α(μ) = tanh(μ/μ₀) の遷移プロファイル
    for mu0 in mu0_list:
        alpha = np.tanh(mu / mu0)
        axes[0].plot(mu, alpha, label=f'μ₀={mu0:.1f}')
    axes[0].axhline(0, color='gray', linestyle='--', linewidth=0.5)
    axes[0].set_title('Precision Field  α(μ) = tanh(μ/μ₀)', fontsize=13)
    axes[0].set_xlabel('μ')
    axes[0].set_ylabel('α')
    axes[0].legend()
    axes[0].set_ylim(-1.5, 1.5)

    # 2. F₁₂(α) = (3/σ)(αμ + Φ∂_μα)
    phi = phi_gaussian(mu, sigma)
    for mu0 in mu0_list:
        alpha = np.tanh(mu / mu0)
        dalpha = 1.0 / (mu0 * np.cosh(mu / mu0)**2)
        F12 = (3.0 / sigma) * (alpha * mu + phi * dalpha)
        axes[1].plot(mu, F12, label=f'μ₀={mu0:.1f}')

    # α=const (=1) の場合を比較表示
    F12_const = curvature_analytic(mu, sigma)
    axes[1].plot(mu, F12_const, '--', color='gray', label='α=const(=2)', alpha=0.6)
    axes[1].axhline(0, color='gray', linestyle='--', linewidth=0.5)
    axes[1].set_title('Curvature with dynamic α  (σ=1)', fontsize=13)
    axes[1].set_xlabel('μ')
    axes[1].set_ylabel('F₁₂')
    axes[1].legend()

    # 3. 遷移層力 (∂Φ=0 の場合): F₁₂|_{∂Φ=0} = 3Φ/(μ₀σ cosh²)
    phi_0 = phi_gaussian(np.array([0.0]), sigma)[0]
    for mu0 in mu0_list:
        F12_transition = 3.0 * phi_0 / (mu0 * sigma * np.cosh(mu / mu0)**2)
        axes[2].plot(mu, F12_transition, label=f'μ₀={mu0:.1f}')
    axes[2].axhline(0, color='gray', linestyle='--', linewidth=0.5)
    axes[2].set_title('Transition-Layer Force (∂Φ=0, Φ=const)', fontsize=13)
    axes[2].set_xlabel('μ')
    axes[2].set_ylabel('F₁₂ (new physics)')
    axes[2].legend()

    plt.tight_layout()
    if save:
        path = os.path.join(OUT_DIR, 'alpha_dynamics.png')
        plt.savefig(path, dpi=150, bbox_inches='tight')
        print(f"保存: {path}")
    plt.close()


def verify_analytic_vs_numerical():
    """解析解と数値計算の整合性検証"""
    print("=" * 60)
    print("忘却の場の方程式 — ガウス族 Toy Model 数値検証")
    print("=" * 60)

    # テストポイント
    test_points = [
        (0, 1),    # 参照点（曲率ゼロ）
        (1, 1),    # 中程度のずれ
        (3, 1),    # 大きなずれ
        (1, 0.5),  # 低不確実性
        (1, 3),    # 高不確実性
    ]

    print(f"\n{'μ':>6}  {'σ':>6}  {'Φ':>10}  {'F₁₂(解析)':>12}  {'F₁₂(数値)':>12}  {'誤差':>12}")
    print("-" * 70)

    max_rel_error = 0
    for mu, sigma in test_points:
        phi = phi_gaussian(mu, sigma)
        F12_a = curvature_analytic(mu, sigma)
        F12_n = curvature_numerical(mu, sigma)
        if abs(F12_a) > 1e-10:
            rel_err = abs(F12_a - F12_n) / abs(F12_a)
        else:
            rel_err = abs(F12_n)
        max_rel_error = max(max_rel_error, rel_err)
        print(f"{mu:6.1f}  {sigma:6.1f}  {phi:10.4f}  {F12_a:12.6f}  {F12_n:12.6f}  {rel_err:12.2e}")

    print(f"\n最大相対誤差: {max_rel_error:.2e}")
    assert max_rel_error < 1e-8, f"解析解と数値解に大きな乖離: {max_rel_error}"
    print("✓ 解析解と数値計算は整合 (相対誤差 < 1e-8)")

    # α-dynamics の検証
    print("\n" + "=" * 60)
    print("α-dynamics 検証: F₁₂ = (3/σ)(αμ + Φ∂_μα)")
    print("=" * 60)

    mu0 = 1.0
    sigma = 1.0
    test_mus = [0, 0.5, 1.0, 2.0, 3.0]

    print(f"\nα(μ) = tanh(μ/{mu0}),  σ = {sigma}")
    print(f"{'μ':>6}  {'α':>8}  {'∂α':>8}  {'Φ':>8}  {'αμ項':>10}  {'Φ∂α項':>10}  {'F₁₂':>10}")
    print("-" * 75)

    for mu_val in test_mus:
        alpha = np.tanh(mu_val / mu0)
        dalpha = 1.0 / (mu0 * np.cosh(mu_val / mu0)**2)
        phi = phi_gaussian(mu_val, sigma)
        term1 = alpha * mu_val  # αμ 項 (忘却勾配)
        term2 = phi * dalpha    # Φ∂α 項 (新物理)
        F12 = (3.0 / sigma) * (term1 + term2)
        print(f"{mu_val:6.1f}  {alpha:8.4f}  {dalpha:8.4f}  {phi:8.4f}  {term1:10.4f}  {term2:10.4f}  {F12:10.4f}")

    # 自己無撞着条件の検証
    phi_0 = phi_gaussian(0, sigma)
    kappa_sc = 9 * phi_0 / (2 * mu0**2)
    print(f"\n自己無撞着条件: κ = 9Φ₀/(2μ₀²)")
    print(f"  Φ₀ = Φ(0,1) = {phi_0:.6f}")
    print(f"  μ₀ = {mu0}")
    print(f"  κ = {kappa_sc:.6f}")


def main():
    # 1. 解析 vs 数値の整合性検証
    verify_analytic_vs_numerical()

    # 2. 可視化
    print("\n可視化を生成中...")
    plot_curvature_field(save=True)
    plot_alpha_dynamics(save=True)
    print("完了！")


if __name__ == "__main__":
    main()
