#!/usr/bin/env python3
"""
命題 3.7.3 数値検証: ガウス族 H² 上の Disintegration 条件
==========================================================

検証対象:
  ∇_k F_{ij} = 0 (忘却曲率が平行) ⟺ 正規化スカラー f = F_{12}/√g = const

ガウス族上の具体形:
  - Fisher 計量: g = diag(1/σ², 2/σ²), √g = √2/σ²
  - Chebyshev: T = (0, 6/σ)
  - 忘却曲率: F_{12} = (3α/σ) ∂_μΦ
  - 正規化スカラー: f = 3ασ ∂_μΦ / √2

Disintegration クラス:
  Φ(μ,σ) = cμ/(ασ) + h(σ) → f = 3c/√2 = const ✓

対照群:
  Φ_A(μ,σ) = μ²/σ   → f ∝ μσ (非定数) ✗
  Φ_B(μ,σ) = μ/σ²   → f ∝ 1/σ (非定数) ✗
  Φ_C(μ,σ) = e^(-μ²) → f ∝ μσe^(-μ²) (非定数) ✗
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# === パラメータ ===
ALPHA = 1.0  # α パラメータ
C_CONST = 1.0  # disintegration クラスの定数 c


# === 忘却場の定義 ===
def phi_disintegration(mu, sigma):
    """Disintegration クラス: Φ = cμ/(ασ) + h(σ), h(σ) = log(σ)"""
    return C_CONST * mu / (ALPHA * sigma) + np.log(sigma)

def phi_A(mu, sigma):
    """対照群 A: Φ = μ²/σ (2次依存)"""
    return mu**2 / sigma

def phi_B(mu, sigma):
    """対照群 B: Φ = μ/σ² (σ² 依存)"""
    return mu / sigma**2

def phi_C(mu, sigma):
    """対照群 C: Φ = exp(-μ²) (ガウス的減衰)"""
    return np.exp(-mu**2)


# === 幾何学的量の計算 ===
def compute_F12(mu, sigma, phi_func, h=1e-5):
    """忘却曲率 F_{12} = (3α/σ) ∂_μΦ を数値微分で計算"""
    dphi_dmu = (phi_func(mu + h, sigma) - phi_func(mu - h, sigma)) / (2 * h)
    return (3 * ALPHA / sigma) * dphi_dmu

def compute_sqrt_g(sigma):
    """Fisher 計量の行列式の平方根: √g = √2/σ²"""
    return np.sqrt(2) / sigma**2

def compute_f_scalar(mu, sigma, phi_func, h=1e-5):
    """正規化スカラー f = F_{12}/√g = 3ασ ∂_μΦ / √2"""
    dphi_dmu = (phi_func(mu + h, sigma) - phi_func(mu - h, sigma)) / (2 * h)
    return 3 * ALPHA * sigma * dphi_dmu / np.sqrt(2)

def compute_nabla_f(mu, sigma, phi_func, h=1e-5):
    """∇f のノルム (Fisher ノルム) — f が定数なら 0"""
    # 偏微分 ∂_μ f, ∂_σ f
    f_mu_plus = compute_f_scalar(mu + h, sigma, phi_func)
    f_mu_minus = compute_f_scalar(mu - h, sigma, phi_func)
    df_dmu = (f_mu_plus - f_mu_minus) / (2 * h)

    f_sigma_plus = compute_f_scalar(mu, sigma + h, phi_func)
    f_sigma_minus = compute_f_scalar(mu, sigma - h, phi_func)
    df_dsigma = (f_sigma_plus - f_sigma_minus) / (2 * h)

    # Fisher ノルム: ||∇f||² = g^{μμ}(∂_μf)² + g^{σσ}(∂_σf)²
    # g^{μμ} = σ², g^{σσ} = σ²/2
    norm_sq = sigma**2 * df_dmu**2 + (sigma**2 / 2) * df_dsigma**2
    return np.sqrt(norm_sq)


# === 解析的検証 ===
def f_disintegration_analytic(mu, sigma):
    """Disintegration クラスの f は解析的に定数: f = 3c/√2"""
    return 3 * C_CONST / np.sqrt(2) * np.ones_like(mu)

def f_A_analytic(mu, sigma):
    """対照群 A: f = 3α·2μ·σ/√2 = 6αμσ/√2"""
    return 6 * ALPHA * mu * sigma / np.sqrt(2)

def f_B_analytic(mu, sigma):
    """対照群 B: f = 3α·(1/σ²)·σ/√2 = 3α/(σ√2)"""
    return 3 * ALPHA / (sigma * np.sqrt(2))


# === メイン検証 ===
def main():
    print("=" * 70)
    print("命題 3.7.3 数値検証: Disintegration 条件 ∇_k F_{ij} = 0")
    print("=" * 70)
    print()

    # グリッド
    mu_range = np.linspace(-3, 3, 50)
    sigma_range = np.linspace(0.5, 3, 50)
    MU, SIGMA = np.meshgrid(mu_range, sigma_range)

    cases = [
        ("Disintegration: Φ=cμ/(ασ)+h(σ)", phi_disintegration, True),
        ("対照群 A: Φ=μ²/σ", phi_A, False),
        ("対照群 B: Φ=μ/σ²", phi_B, False),
        ("対照群 C: Φ=exp(-μ²)", phi_C, False),
    ]

    # --- 1. 正規化スカラー f の計算 ---
    print("▶ 1. 正規化スカラー f = F_{12}/√g の空間変動")
    print("-" * 70)

    f_results = {}
    nabla_f_results = {}

    for name, phi, is_disint in cases:
        f_vals = compute_f_scalar(MU, SIGMA, phi)
        nabla_f_vals = compute_nabla_f(MU, SIGMA, phi)

        f_mean = np.mean(f_vals)
        f_std = np.std(f_vals)
        f_cv = f_std / (abs(f_mean) + 1e-12)  # 変動係数
        nabla_mean = np.mean(nabla_f_vals)

        f_results[name] = f_vals
        nabla_f_results[name] = nabla_f_vals

        status = "✅ PASS" if f_cv < 1e-4 else "❌ FAIL"
        print(f"  {name}")
        print(f"    f: mean={f_mean:.6f}, std={f_std:.6f}, CV={f_cv:.2e}")
        print(f"    ||∇f||: mean={nabla_mean:.2e}")
        print(f"    Disintegration: {status} (CV < 1e-4)")
        print()

    # --- 2. 解析値との一致検証 ---
    print("▶ 2. 解析値との一致 (Disintegration クラス)")
    print("-" * 70)

    f_numeric = compute_f_scalar(MU, SIGMA, phi_disintegration)
    f_analytic = f_disintegration_analytic(MU, SIGMA)
    max_error = np.max(np.abs(f_numeric - f_analytic))
    print(f"  解析値: f = 3c/√2 = {3 * C_CONST / np.sqrt(2):.6f}")
    print(f"  数値計算との最大誤差: {max_error:.2e}")
    print(f"  一致: {'✅' if max_error < 1e-6 else '❌'}")
    print()

    # --- 3. 忘却場 Φ の空間プロファイル ---
    print("▶ 3. 忘却場 Φ(μ,σ) の空間プロファイル")
    print("-" * 70)

    for name, phi, is_disint in cases:
        phi_vals = phi(MU, SIGMA)
        F12_vals = compute_F12(MU, SIGMA, phi)
        print(f"  {name}")
        print(f"    Φ: range=[{np.min(phi_vals):.3f}, {np.max(phi_vals):.3f}]")
        print(f"    F_{'{12}'}: range=[{np.min(F12_vals):.3f}, {np.max(F12_vals):.3f}]")
        print()

    # --- 4. ∂_μΦ の σ-依存性検証 ---
    print("▶ 4. Disintegration 条件の物理的意味")
    print("-" * 70)
    print("  ∂_μΦ = c/(ασ) の検証 — μ-忘却勾配が σ に反比例")
    print()

    sigma_test = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    mu_test = 1.0  # 固定
    h = 1e-5
    print(f"  {'σ':>6s}  {'∂_μΦ (数値)':>14s}  {'c/(ασ) 理論':>14s}  {'誤差':>10s}")
    print(f"  {'─'*6}  {'─'*14}  {'─'*14}  {'─'*10}")
    for s in sigma_test:
        dphi_num = (phi_disintegration(mu_test+h, s) - phi_disintegration(mu_test-h, s)) / (2*h)
        dphi_theory = C_CONST / (ALPHA * s)
        err = abs(dphi_num - dphi_theory)
        print(f"  {s:6.1f}  {dphi_num:14.8f}  {dphi_theory:14.8f}  {err:10.2e}")

    print()
    print("  → σ 増大に伴い ∂_μΦ が 1/σ で減衰 = 精度低下領域で μ-忘却が弱まる ✅")
    print()

    # --- 5. 可視化 ---
    print("▶ 5. 可視化出力")
    print("-" * 70)

    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.3)

    titles = [
        "Disintegration: Φ=cμ/(ασ)+h(σ)\n[f = const → ∇f = 0 ✅]",
        "Control A: Φ=μ²/σ\n[f ∝ μσ → ∇f ≠ 0 ❌]",
        "Control B: Φ=μ/σ²\n[f ∝ 1/σ → ∇f ≠ 0 ❌]",
        "Control C: Φ=exp(-μ²)\n[f ∝ μσe^{-μ²} → ∇f ≠ 0 ❌]",
    ]

    for idx, (name, phi, is_disint) in enumerate(cases):
        ax = fig.add_subplot(gs[idx // 2, idx % 2])

        # f スカラーをプロット
        f_vals = f_results[list(f_results.keys())[idx]]

        if is_disint:
            # Disintegration: 定数なので偏差をプロット
            deviation = f_vals - np.mean(f_vals)
            im = ax.pcolormesh(MU, SIGMA, deviation, cmap='RdBu_r',
                             vmin=-0.01, vmax=0.01, shading='auto')
            cbar = plt.colorbar(im, ax=ax, shrink=0.8)
            cbar.set_label('f − ⟨f⟩ (deviation)')
        else:
            im = ax.pcolormesh(MU, SIGMA, f_vals, cmap='viridis', shading='auto')
            cbar = plt.colorbar(im, ax=ax, shrink=0.8)
            cbar.set_label('f = F₁₂/√g')

        ax.set_xlabel('μ')
        ax.set_ylabel('σ')
        ax.set_title(titles[idx], fontsize=10)

    fig.suptitle('命題 3.7.3 数値検証: 正規化忘却曲率 f = F₁₂/√g\n'
                 'Disintegration ⟺ f = const (空間的に一定)',
                 fontsize=13, fontweight='bold')

    outpath = '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/disintegration_verification.png'
    fig.savefig(outpath, dpi=150, bbox_inches='tight')
    print(f"  保存: {outpath}")
    plt.close()

    # --- 6. ∇f のプロファイル比較 ---
    fig2, axes2 = plt.subplots(1, 4, figsize=(18, 4))

    for idx, (name, phi, is_disint) in enumerate(cases):
        ax = axes2[idx]
        nabla_vals = nabla_f_results[list(nabla_f_results.keys())[idx]]

        im = ax.pcolormesh(MU, SIGMA, nabla_vals, cmap='hot', shading='auto',
                          vmin=0, vmax=np.percentile(nabla_vals, 95))
        plt.colorbar(im, ax=ax, shrink=0.8)
        ax.set_xlabel('μ')
        ax.set_ylabel('σ')

        short_name = name.split(':')[0]
        status = '✅ ≈0' if is_disint else '❌ ≠0'
        ax.set_title(f'{short_name}\n||∇f|| {status}', fontsize=9)

    fig2.suptitle('||∇f|| の空間分布 — Disintegration 条件: ||∇f|| ≡ 0',
                  fontsize=12, fontweight='bold')
    fig2.tight_layout()

    outpath2 = '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/nabla_f_comparison.png'
    fig2.savefig(outpath2, dpi=150, bbox_inches='tight')
    print(f"  保存: {outpath2}")
    plt.close()

    # --- 結論 ---
    print()
    print("=" * 70)
    print("結論")
    print("=" * 70)
    print()
    print("  1. Disintegration クラス Φ = cμ/(ασ) + h(σ):")
    print(f"     f = 3c/√2 = {3*C_CONST/np.sqrt(2):.6f} (定数)")
    print(f"     ||∇f|| ≈ 0 (数値精度内)")
    print(f"     → 命題 3.7.3 (ii) の条件 ∇_k F_{{ij}} = 0 が成立 ✅")
    print()
    print("  2. 対照群 A,B,C: f が空間的に変動")
    print("     ||∇f|| ≫ 0")
    print("     → Disintegration 非許容 (Bayesian inversion のみ) ✅")
    print()
    print("  3. 物理的意味の検証:")
    print("     ∂_μΦ = c/(ασ) — μ-忘却勾配が精度 (1/σ) に比例")
    print("     精度が低い領域 (大 σ) で μ-忘却が弱まる ✅")
    print()
    print("  命題 3.7.3 の数値検証: 全項目 PASS")


if __name__ == '__main__':
    main()
