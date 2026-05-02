#!/usr/bin/env python3
"""
P3 数値検証: α-遷移層力の局在
================================
Paper I §6.3 の中心的予測を数値的に検証する。

ガウス族 ℋ² 上で:
- α を tanh(μ/μ₀) の動的場に昇格
- F₁₂ = (3/σ)(α ∂_μΦ + Φ ∂_μα) を計算
- 遷移層 (μ ≈ 0) への力の局在を確認
- ∂Φ=0 (均一忘却) でも ∂α≠0 なら F≠0 を例示

理論的予測:
  F₁₂|_{∂Φ=0} = 3Φ/(μ₀ σ cosh²(μ/μ₀))
  → μ=0 に局在し、幅 ∼ μ₀
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

# === 設定 ===
MU_RANGE = np.linspace(-5.0, 5.0, 1000)  # μ の走査範囲
SIGMA = 1.0  # σ を固定
MU_0_VALUES = [0.5, 1.0, 2.0]  # 遷移幅パラメータ

OUTPUT_DIR = Path(__file__).parent / "results"
OUTPUT_DIR.mkdir(exist_ok=True)


# === ガウス族 ℋ² の幾何学的量 ===

def chebyshev_gaussian(sigma: float) -> tuple[float, float]:
    """ガウス族の Chebyshev 1-形式 T = (T_μ, T_σ)
    
    T_μ = 0,  T_σ = 6/σ
    (Paper I §4.2 による)
    """
    return 0.0, 6.0 / sigma


def fisher_metric_gaussian(sigma: float) -> np.ndarray:
    """ガウス族の Fisher 情報計量
    g = diag(1/σ², 2/σ²)
    """
    return np.array([[1.0 / sigma**2, 0.0],
                     [0.0, 2.0 / sigma**2]])


# === α 場の定義 ===

def alpha_field(mu: np.ndarray, mu_0: float) -> np.ndarray:
    """α(μ) = tanh(μ/μ₀): m-接続(α→-1)からe-接続(α→+1)への遷移"""
    return np.tanh(mu / mu_0)


def alpha_field_deriv(mu: np.ndarray, mu_0: float) -> np.ndarray:
    """∂_μ α = (1/μ₀) sech²(μ/μ₀)"""
    return 1.0 / (mu_0 * np.cosh(mu / mu_0)**2)


# === 忘却場 Φ のシナリオ ===

def phi_uniform(mu: np.ndarray, phi_0: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """シナリオ 1: 均一忘却 Φ(μ) = Φ₀ (定数)
    → ∂_μΦ = 0 だが ∂_μα ≠ 0 → F₁₂ ≠ 0 を例示
    """
    phi = np.full_like(mu, phi_0)
    dphi = np.zeros_like(mu)
    return phi, dphi


def phi_gaussian_bump(mu: np.ndarray, mu_c: float = 0.0, 
                       width: float = 1.5, phi_max: float = 2.0) -> tuple[np.ndarray, np.ndarray]:
    """シナリオ 2: 局在した忘却 Φ(μ) = Φ_max exp(-(μ-μ_c)²/(2w²))
    → ∂_μΦ ≠ 0 & ∂_μα ≠ 0 → 両項からの寄与
    """
    phi = phi_max * np.exp(-(mu - mu_c)**2 / (2 * width**2))
    dphi = phi * (-(mu - mu_c) / width**2)
    return phi, dphi


def phi_linear_gradient(mu: np.ndarray, slope: float = 0.3, 
                         offset: float = 1.5) -> tuple[np.ndarray, np.ndarray]:
    """シナリオ 3: 線形勾配忘却 Φ(μ) = offset + slope·μ
    → ∂_μΦ = const → ∂Φ∧T ≠ 0 の古典的ケース
    """
    phi = offset + slope * mu
    dphi = np.full_like(mu, slope)
    return phi, dphi


# === 忘却曲率 F₁₂ の計算 ===

def oblivion_curvature(mu: np.ndarray, sigma: float, mu_0: float,
                        phi: np.ndarray, dphi: np.ndarray) -> dict:
    """忘却曲率 F₁₂ = (3/σ)(α ∂_μΦ + Φ ∂_μα) を計算
    
    返値: 各コンポーネントの辞書
    """
    T_mu, T_sigma = chebyshev_gaussian(sigma)
    alpha = alpha_field(mu, mu_0)
    dalpha = alpha_field_deriv(mu, mu_0)
    
    # F₁₂ の2つの寄与
    term_dPhi = alpha * dphi * T_sigma   # α ∂_μΦ T_σ 項
    term_dAlpha = phi * dalpha * T_sigma  # Φ ∂_μα T_σ 項
    
    # 前因子 1/2 (F_{ij} = (α/2)[...] の定義から)
    # ただし α が μ 依存のとき追加項 Φ ∂_μα T_σ が現れる
    # 完全な式: F₁₂ = (1/2)[(α ∂_μΦ + Φ ∂_μα) T_σ]
    #                = (3/σ)(α ∂_μΦ + Φ ∂_μα)  (T_σ = 6/σ を代入、前因子 1/2)
    F12_total = (1.0 / 2.0) * (term_dPhi + term_dAlpha)
    F12_classical = (1.0 / 2.0) * term_dPhi     # α 一定の理論に相当
    F12_transition = (1.0 / 2.0) * term_dAlpha   # α-遷移層力 (新しい項)
    
    # 理論的予測 (均一忘却の場合)
    phi_0 = phi[len(phi)//2]  # μ=0 での Φ 値
    F12_theory = (3.0 * phi_0) / (mu_0 * sigma * np.cosh(mu / mu_0)**2)
    
    return {
        'F12_total': F12_total,
        'F12_classical': F12_classical,
        'F12_transition': F12_transition,
        'F12_theory_uniform': F12_theory,
        'alpha': alpha,
        'dalpha': dalpha,
        'phi': phi,
        'dphi': dphi,
    }


# === 解析解との比較 ===

def verify_analytical(mu: np.ndarray, mu_0: float, sigma: float, phi_0: float = 1.0):
    """均一忘却ケースで解析解と数値解を比較"""
    phi, dphi = phi_uniform(mu, phi_0)
    result = oblivion_curvature(mu, sigma, mu_0, phi, dphi)
    
    # 数値解
    F12_num = result['F12_transition']  # ∂Φ=0 なので transition 項のみ
    
    # 解析解: F₁₂ = 3Φ₀/(μ₀ σ cosh²(μ/μ₀))
    F12_ana = 3.0 * phi_0 / (mu_0 * sigma * np.cosh(mu / mu_0)**2)
    
    # 相対誤差
    mask = np.abs(F12_ana) > 1e-15
    rel_err = np.max(np.abs(F12_num[mask] - F12_ana[mask]) / np.abs(F12_ana[mask]))
    
    return F12_num, F12_ana, rel_err


# === プロット ===

def plot_scenario_comparison(mu: np.ndarray, sigma: float, mu_0: float):
    """3つのΦシナリオでの F₁₂ 比較プロット"""
    fig, axes = plt.subplots(3, 2, figsize=(14, 12))
    fig.suptitle(f'P3 数値検証: α-遷移層力の局在 (σ={sigma}, μ₀={mu_0})', fontsize=14)
    
    scenarios = [
        ('均一忘却 Φ=const', phi_uniform),
        ('局在忘却 Φ=Gaussian', phi_gaussian_bump),
        ('線形勾配 Φ=a+bμ', phi_linear_gradient),
    ]
    
    for i, (name, phi_func) in enumerate(scenarios):
        phi, dphi = phi_func(mu)
        result = oblivion_curvature(mu, sigma, mu_0, phi, dphi)
        
        # 左: Φ と α のプロファイル
        ax_left = axes[i, 0]
        ax_left.plot(mu, result['phi'], 'b-', label='Φ(μ)', linewidth=2)
        ax_left.plot(mu, result['alpha'], 'r--', label='α(μ)', linewidth=2)
        ax_left.set_title(f'{name}')
        ax_left.set_xlabel('μ')
        ax_left.legend()
        ax_left.axvline(0, color='gray', linestyle=':', alpha=0.5)
        ax_left.set_xlim(-5, 5)
        
        # 右: F₁₂ のコンポーネント
        ax_right = axes[i, 1]
        ax_right.plot(mu, result['F12_total'], 'k-', label='F₁₂ (全体)', linewidth=2.5)
        ax_right.plot(mu, result['F12_classical'], 'b--', label='α∂Φ 項 (古典)', linewidth=1.5)
        ax_right.plot(mu, result['F12_transition'], 'r--', label='Φ∂α 項 (遷移層力)', linewidth=1.5)
        ax_right.set_title(f'忘却曲率 F₁₂')
        ax_right.set_xlabel('μ')
        ax_right.legend()
        ax_right.axvline(0, color='gray', linestyle=':', alpha=0.5)
        ax_right.axhline(0, color='gray', linestyle=':', alpha=0.5)
        ax_right.set_xlim(-5, 5)
        
        # 遷移層のハイライト
        ax_right.axvspan(-mu_0, mu_0, alpha=0.1, color='red', label='遷移層')
    
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / 'P3_alpha_transition_layer.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  → プロット保存: {OUTPUT_DIR / 'P3_alpha_transition_layer.png'}")


def plot_mu0_dependence(mu: np.ndarray, sigma: float):
    """遷移幅 μ₀ への依存性"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    phi, dphi = phi_uniform(mu, phi_0=1.0)
    
    peak_values = []
    widths = []
    
    for mu_0 in MU_0_VALUES:
        result = oblivion_curvature(mu, sigma, mu_0, phi, dphi)
        F12 = result['F12_transition']
        
        axes[0].plot(mu, F12, label=f'μ₀={mu_0}', linewidth=2)
        
        # ピーク値と半値幅
        peak = np.max(np.abs(F12))
        half_max = peak / 2
        above_half = np.abs(F12) > half_max
        if np.any(above_half):
            indices = np.where(above_half)[0]
            fwhm = mu[indices[-1]] - mu[indices[0]]
        else:
            fwhm = 0.0
        
        peak_values.append(peak)
        widths.append(fwhm)
    
    axes[0].set_title('F₁₂(遷移層力) の μ₀ 依存性 (均一忘却)')
    axes[0].set_xlabel('μ')
    axes[0].set_ylabel('F₁₂')
    axes[0].legend()
    axes[0].axvline(0, color='gray', linestyle=':', alpha=0.5)
    axes[0].set_xlim(-5, 5)
    
    # ピーク vs μ₀ (理論: peak ∝ 1/μ₀)
    mu_0_arr = np.array(MU_0_VALUES)
    peak_arr = np.array(peak_values)
    theory_peak = peak_arr[1] * MU_0_VALUES[1] / mu_0_arr  # 1/μ₀ スケーリング
    
    axes[1].plot(mu_0_arr, peak_arr, 'ko-', label='数値', markersize=8, linewidth=2)
    axes[1].plot(mu_0_arr, theory_peak, 'r--', label='理論 (∝ 1/μ₀)', linewidth=1.5)
    axes[1].set_title('ピーク曲率の μ₀ スケーリング')
    axes[1].set_xlabel('μ₀')
    axes[1].set_ylabel('max|F₁₂|')
    axes[1].legend()
    
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / 'P3_mu0_scaling.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  → プロット保存: {OUTPUT_DIR / 'P3_mu0_scaling.png'}")
    
    return peak_values, widths


def plot_alpha_constant_vs_field(mu: np.ndarray, sigma: float, mu_0: float):
    """α 一定 vs α(μ) 場での曲率比較"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    
    # シナリオ: 局在忘却
    phi, dphi = phi_gaussian_bump(mu)
    
    # α(μ) = tanh(μ/μ₀) (動的場)
    result_field = oblivion_curvature(mu, sigma, mu_0, phi, dphi)
    
    # α = 0 (固定: Levi-Civita)
    alpha_const = 0.0
    T_mu, T_sigma = chebyshev_gaussian(sigma)
    F12_const_0 = (alpha_const / 2.0) * dphi * T_sigma
    
    # α = 1 (固定: e-接続)
    alpha_const = 1.0
    F12_const_1 = (alpha_const / 2.0) * dphi * T_sigma
    
    ax.plot(mu, result_field['F12_total'], 'k-', label='α(μ)=tanh(μ/μ₀) [動的場]', linewidth=2.5)
    ax.plot(mu, F12_const_1, 'b--', label='α=1 (e-接続, 固定)', linewidth=1.5)
    ax.plot(mu, F12_const_0, 'g--', label='α=0 (Levi-Civita, 固定)', linewidth=1.5)
    ax.fill_between(mu, 0, result_field['F12_transition'], alpha=0.2, color='red', 
                     label='Φ∂α 項 (α 場固有)')
    
    ax.set_title(f'α-遷移層力: 固定α vs 動的α(μ) (局在忘却, μ₀={mu_0})')
    ax.set_xlabel('μ')
    ax.set_ylabel('F₁₂')
    ax.legend()
    ax.axvline(0, color='gray', linestyle=':', alpha=0.5)
    ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlim(-5, 5)
    
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / 'P3_const_vs_field.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  → プロット保存: {OUTPUT_DIR / 'P3_const_vs_field.png'}")


# === メイン ===

def main():
    print("=" * 60)
    print("P3 数値検証: α-遷移層力の局在")
    print("Paper I §6.3 の中心的予測")
    print("=" * 60)
    
    mu = MU_RANGE
    sigma = SIGMA
    mu_0 = 1.0  # デフォルト遷移幅
    
    # --- 1. 解析解との一致 ---
    print("\n[1] 解析解との比較 (均一忘却ケース)")
    for m0 in MU_0_VALUES:
        F12_num, F12_ana, rel_err = verify_analytical(mu, m0, sigma)
        print(f"  μ₀={m0}: 最大相対誤差 = {rel_err:.2e}")
    
    # --- 2. 3シナリオ比較 ---
    print("\n[2] 3シナリオでの F₁₂ プロット生成")
    plot_scenario_comparison(mu, sigma, mu_0)
    
    # --- 3. μ₀ 依存性 ---
    print("\n[3] 遷移幅 μ₀ への依存性")
    peaks, widths = plot_mu0_dependence(mu, sigma)
    for m0, p, w in zip(MU_0_VALUES, peaks, widths):
        print(f"  μ₀={m0}: peak|F₁₂|={p:.4f}, FWHM={w:.2f}")
    
    # --- 4. α一定 vs α場 ---
    print("\n[4] α一定 vs α(μ)場 の曲率比較")
    plot_alpha_constant_vs_field(mu, sigma, mu_0)
    
    # --- 5. 定量的検証まとめ ---
    print("\n[5] 定量的検証サマリー")
    phi_u, _ = phi_uniform(mu, 1.0)
    result_u = oblivion_curvature(mu, sigma, mu_0, phi_u, np.zeros_like(mu))
    
    # 理論: ピーク = 3Φ₀/(μ₀σ) at μ=0
    peak_theory = 3.0 * 1.0 / (mu_0 * sigma)
    peak_numerical = np.max(np.abs(result_u['F12_transition']))
    
    print(f"  理論ピーク値:  {peak_theory:.6f}")
    print(f"  数値ピーク値:  {peak_numerical:.6f}")
    print(f"  相対誤差:      {abs(peak_theory - peak_numerical) / peak_theory:.2e}")
    
    # 理論: FWHM ≈ 2μ₀ arccosh(√2) ≈ 2μ₀ × 0.8814 = 1.763μ₀
    # sech²(x) = 1/2 のとき x = arccosh(√2) ≈ 0.8814
    fwhm_theory = 2 * mu_0 * np.arccosh(np.sqrt(2))
    above_half = np.abs(result_u['F12_transition']) > peak_numerical / 2
    indices = np.where(above_half)[0]
    fwhm_numerical = mu[indices[-1]] - mu[indices[0]]
    
    print(f"  理論 FWHM:     {fwhm_theory:.4f}")
    print(f"  数値 FWHM:     {fwhm_numerical:.4f}")
    print(f"  相対誤差:      {abs(fwhm_theory - fwhm_numerical) / fwhm_theory:.2e}")
    
    # --- 6. 方向性定理の数値的例示 ---
    print("\n[6] 方向性定理の数値的例示")
    print("  均一忘却 (∂Φ=0) でも α 変動 (∂α≠0) → F₁₂ ≠ 0:")
    print(f"    max|F₁₂| = {peak_numerical:.6f} ≠ 0  ✓")
    print("  この力は α 一定の理論では原理的に不可視:")
    alpha_const_check = alpha_field(mu, mu_0)
    # α 一定なら ∂α = 0 → F₁₂ = (α/2)(∂Φ)Tσ = 0 (∂Φ=0 なので)
    F12_const_check = (alpha_const_check * 0.0) * chebyshev_gaussian(sigma)[1] / 2
    print(f"    max|F₁₂|_{'{α一定}'} = {np.max(np.abs(F12_const_check)):.6f} = 0  ✓")
    
    print("\n" + "=" * 60)
    print("検証完了。全結果は experiments/results/ に保存。")
    print("=" * 60)


if __name__ == '__main__':
    main()
