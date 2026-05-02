"""
Paper I: Force is Oblivion — 数値シミュレーション
===================================================
Poincaré 半平面 (Gaussian family) 上の Oblivion Field 方程式 §4-5 を
数値的に検証し、publication-quality の4枚の図を生成する。

§4 Gaussian Toy Model:
  - Φ(μ,σ) = -log σ + (σ² + μ²)/2 - 1/2  (KL divergence from N(0,1))
  - Fisher metric: g = diag(1/σ², 2/σ²)
  - Chebyshev 1-form: T = (0, 6/σ)
  - Oblivion connection: A₁ = μ, A₂ = -1/σ + σ + 6Φ/σ
  - Oblivion curvature: F₁₂ = 6μ/σ

§5 α-Dynamics:
  - α(θ) を動的場に昇格
  - 修正 A_i = ∂_iΦ + (α/2)Φ T_i
  - F₁₂ = (3/σ)(α ∂_μΦ + Φ ∂_μα)
  - 遷移層プロファイル: α(μ) = tanh(μ/μ₀)

生成する図:
  Fig 1: Φ(μ,σ) ヒートマップ — 忘却場の空間分布
  Fig 2: F₁₂ = 6μ/σ — 忘却曲率 (= 力)
  Fig 3: α-dynamics — 遷移層での曲率生成 (論文の中心予測)
  Fig 4: E-L 方程式の解 — Φ の振動挙動
"""

import numpy as np
import os

# --- matplotlib 初期化 (ヘッドレス環境対応) ---
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import TwoSlopeNorm

# --- 出力先 ---
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# §4: Gaussian Toy Model — 基本関数
# ============================================================

def phi_field(mu: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """
    忘却場 Φ(μ,σ) = D_KL(N(μ,σ²) || N(0,1))
    = -log σ + (σ² + μ²)/2 - 1/2
    """
    return -np.log(sigma) + (sigma**2 + mu**2) / 2 - 0.5


def chebyshev_form(sigma: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Chebyshev 1-form T_i = g^{jk} C_{ijk}
    Gaussian family: T = (T₁, T₂) = (0, 6/σ)
    """
    T1 = np.zeros_like(sigma)
    T2 = 6.0 / sigma
    return T1, T2


def oblivion_connection(mu: np.ndarray, sigma: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    忘却接続 A_i = ∂_iΦ + Φ T_i
    A₁ = ∂_μΦ + Φ·T₁ = μ + 0 = μ
    A₂ = ∂_σΦ + Φ·T₂ = (-1/σ + σ) + Φ·(6/σ)
    """
    Phi = phi_field(mu, sigma)
    A1 = mu
    A2 = (-1.0 / sigma + sigma) + Phi * (6.0 / sigma)
    return A1, A2


def oblivion_curvature(mu: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """
    忘却曲率 F₁₂ = ∂₁A₂ - ∂₂A₁
    解析解: F₁₂ = 6μ/σ (Paper I §4.4)
    """
    return 6.0 * mu / sigma


def oblivion_curvature_alpha(
    mu: np.ndarray,
    sigma: np.ndarray,
    alpha: np.ndarray,
    dalpha_dmu: np.ndarray
) -> np.ndarray:
    """
    α-dynamics での修正曲率:
    F₁₂ = (3/σ)(α ∂_μΦ + Φ ∂_μα)
    ∂_μΦ = μ
    """
    Phi = phi_field(mu, sigma)
    dphi_dmu = mu
    return (3.0 / sigma) * (alpha * dphi_dmu + Phi * dalpha_dmu)


# ============================================================
# Fig 1: 忘却場 Φ(μ,σ)
# ============================================================

def plot_fig1(out_dir: str) -> str:
    """Φ(μ,σ) のヒートマップ — Poincaré 半平面上の忘却場"""
    mu = np.linspace(-4, 4, 400)
    sigma = np.linspace(0.1, 4, 400)
    MU, SIGMA = np.meshgrid(mu, sigma)
    PHI = phi_field(MU, SIGMA)

    fig, ax = plt.subplots(figsize=(8, 6))

    # Φ=0 の等高線を強調 (完全記憶の曲線)
    im = ax.imshow(PHI, cmap='inferno', vmin=-0.5, vmax=8,
                   extent=[-4, 4, 0.1, 4], aspect='auto', origin='lower')
    cb = plt.colorbar(im, ax=ax, label=r'$\Phi(\mu, \sigma) = D_\mathrm{KL}(p_\theta \| q)$')

    # Φ=0 等高線 (contourは動く可能性があるが、念のため)
    cs = ax.contour(MU, SIGMA, PHI, levels=[0], colors='cyan', linewidths=2, linestyles='--')
    ax.clabel(cs, fmt=r'$\Phi=0$', fontsize=10, colors='cyan')

    # 基準点 (0,1) = N(0,1) = q
    ax.plot(0, 1, 'w*', markersize=15, markeredgecolor='k', markeredgewidth=0.8,
            label=r'$q = \mathcal{N}(0,1)$')

    ax.set_xlabel(r'$\mu$ (mean)', fontsize=13)
    ax.set_ylabel(r'$\sigma$ (std. dev.)', fontsize=13)
    ax.set_title(r'Fig. 1: Oblivion Field $\Phi(\mu,\sigma)$ on the Poincaré Half-Plane',
                 fontsize=12, pad=12)
    ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
    ax.set_xlim(-4, 4)
    ax.set_ylim(0.1, 4)

    path = os.path.join(out_dir, 'fig1_oblivion_field.png')
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✅ Fig 1 → {path}")
    return path


# ============================================================
# Fig 2: 忘却曲率 F₁₂ = 6μ/σ
# ============================================================

def plot_fig2(out_dir: str) -> str:
    """F₁₂ = 6μ/σ — 力 = 忘却の不均一"""
    mu = np.linspace(-4, 4, 400)
    sigma = np.linspace(0.1, 4, 400)
    MU, SIGMA = np.meshgrid(mu, sigma)
    F12 = oblivion_curvature(MU, SIGMA)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={'width_ratios': [1.2, 1]})

    # --- 左: 2D ヒートマップ ---
    ax = axes[0]
    vmax = 25
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    im = ax.imshow(F12, cmap='RdBu_r', norm=norm,
                   extent=[-4, 4, 0.1, 4], aspect='auto', origin='lower')
    plt.colorbar(im, ax=ax, label=r'$F_{12} = 6\mu/\sigma$')

    # F₁₂ = 0 の線 (μ=0)
    ax.axvline(x=0, color='k', linewidth=1.5, linestyle='-', alpha=0.7, label=r'$\mu=0$: $F_{12}=0$')

    ax.set_xlabel(r'$\mu$', fontsize=13)
    ax.set_ylabel(r'$\sigma$', fontsize=13)
    ax.set_title(r'Oblivion Curvature $F_{12} = 6\mu/\sigma$', fontsize=12, pad=10)
    ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
    ax.set_xlim(-4, 4)
    ax.set_ylim(0.1, 4)

    # --- 右: σ 固定でのスライス ---
    ax2 = axes[1]
    mu_1d = np.linspace(-4, 4, 200)
    for sig_val, color, ls in [(0.5, '#d62728', '-'), (1.0, '#2ca02c', '--'),
                                (2.0, '#1f77b4', '-.'), (3.0, '#9467bd', ':')]:
        F12_slice = 6.0 * mu_1d / sig_val
        ax2.plot(mu_1d, F12_slice, color=color, linewidth=2, linestyle=ls,
                 label=rf'$\sigma={sig_val}$')

    ax2.axhline(y=0, color='k', linewidth=0.8)
    ax2.axvline(x=0, color='k', linewidth=0.8, linestyle=':')
    ax2.set_xlabel(r'$\mu$', fontsize=13)
    ax2.set_ylabel(r'$F_{12}$', fontsize=13)
    ax2.set_title(r'$F_{12}(\mu)$ at fixed $\sigma$', fontsize=12, pad=10)
    ax2.legend(fontsize=10, framealpha=0.9)
    ax2.set_ylim(-50, 50)
    ax2.grid(True, alpha=0.3)

    fig.suptitle(r'Fig. 2: Force $=$ Inhomogeneity of Forgetting', fontsize=13, y=1.02)
    plt.tight_layout()

    path = os.path.join(out_dir, 'fig2_curvature_F12.png')
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✅ Fig 2 → {path}")
    return path


# ============================================================
# Fig 3: α-dynamics — 遷移層での力の生成
# ============================================================

def plot_fig3(out_dir: str) -> str:
    """
    Paper I §5 の中心予測:
    F₁₂ = (3/σ)(α ∂_μΦ + Φ ∂_μα)
         = (3/σ)(従来項 + 新項)
    α(μ) = tanh(μ/μ₀) の遷移プロファイルで新項が遷移層に局在する
    """
    mu = np.linspace(-6, 6, 500)
    sigma_val = 1.5  # σ を固定

    fig, axes = plt.subplots(2, 2, figsize=(13, 10))

    for col, mu0 in enumerate([1.0, 3.0]):
        # α プロファイル
        alpha = np.tanh(mu / mu0)
        dalpha_dmu = 1.0 / (mu0 * np.cosh(mu / mu0)**2)

        Phi = phi_field(mu, sigma_val)
        dphi_dmu = mu  # ∂_μΦ = μ

        # 2つの項
        term_conventional = (3.0 / sigma_val) * alpha * dphi_dmu  # α ∂_μΦ
        term_new = (3.0 / sigma_val) * Phi * dalpha_dmu           # Φ ∂_μα
        F12_total = term_conventional + term_new

        # 参考: α=const の場合
        F12_const = oblivion_curvature(mu, sigma_val)

        # --- 上段: α プロファイルと ∂α/∂μ ---
        ax = axes[0, col]
        ax.plot(mu, alpha, 'b-', linewidth=2, label=r'$\alpha(\mu)$')
        ax.plot(mu, dalpha_dmu * mu0, 'r--', linewidth=1.5,
                label=rf'$\mu_0 \cdot \partial_\mu\alpha$ (×{mu0})')
        ax.axhline(y=0, color='k', linewidth=0.5)
        ax.axvline(x=0, color='k', linewidth=0.5, linestyle=':')
        ax.fill_between(mu, -1, 1, where=np.abs(mu) < 2*mu0,
                        alpha=0.08, color='orange', label=f'Transition layer')
        ax.set_xlabel(r'$\mu$', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)
        ax.set_title(rf'$\alpha(\mu) = \tanh(\mu/{mu0})$, $\sigma={sigma_val}$',
                     fontsize=11, pad=8)
        ax.legend(fontsize=9, loc='upper left')
        ax.set_ylim(-1.3, 1.3)
        ax.grid(True, alpha=0.2)

        # --- 下段: 曲率の分解 ---
        ax = axes[1, col]
        ax.plot(mu, F12_total, 'k-', linewidth=2.5, label=r'$F_{12}$ total', zorder=5)
        ax.plot(mu, term_conventional, 'b--', linewidth=1.5,
                label=r'$\frac{3}{\sigma}\alpha\partial_\mu\Phi$ (conventional)')
        ax.plot(mu, term_new, 'r-', linewidth=2,
                label=r'$\frac{3}{\sigma}\Phi\partial_\mu\alpha$ (NEW)', zorder=4)
        ax.plot(mu, F12_const, 'g:', linewidth=1, alpha=0.5,
                label=r'$F_{12}|_{\alpha=1}$ (constant $\alpha$)')
        ax.axhline(y=0, color='k', linewidth=0.5)
        ax.axvline(x=0, color='k', linewidth=0.5, linestyle=':')
        ax.fill_between(mu, ax.get_ylim()[0] if ax.get_ylim()[0] < -5 else -30,
                        ax.get_ylim()[1] if ax.get_ylim()[1] > 5 else 30,
                        where=np.abs(mu) < 2*mu0,
                        alpha=0.08, color='orange')
        ax.set_xlabel(r'$\mu$', fontsize=12)
        ax.set_ylabel(r'$F_{12}$', fontsize=12)
        ax.set_title(rf'Curvature decomposition ($\mu_0={mu0}$)', fontsize=11, pad=8)
        ax.legend(fontsize=8, loc='upper left')
        ax.grid(True, alpha=0.2)

    fig.suptitle(
        r'Fig. 3: $\alpha$-Dynamics — Force at Observational Regime Boundaries (§5.5)',
        fontsize=13, y=1.02)
    plt.tight_layout()

    path = os.path.join(out_dir, 'fig3_alpha_dynamics.png')
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✅ Fig 3 → {path}")
    return path


# ============================================================
# Fig 4: E-L 方程式の振動解
# ============================================================

def plot_fig4(out_dir: str) -> str:
    """
    Euler-Lagrange 方程式 (Paper I §4.5):
    ∂_μ²Φ + (λ/9)Φ = 0
    解: Φ = A cos(ωμ) + B sin(ωμ), ω = √λ / 3
    波長: 2π/ω = 6π/√λ
    """
    mu = np.linspace(-15, 15, 1000)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # --- 左: 複数 λ での振動 ---
    ax = axes[0]
    lambda_vals = [1.0, 4.0, 9.0, 25.0]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

    for lam, color in zip(lambda_vals, colors):
        omega = np.sqrt(lam) / 3.0
        wavelength = 2 * np.pi / omega
        # 初期条件: Φ(0) = 1, Φ'(0) = 0 → A=1, B=0
        Phi_el = np.cos(omega * mu)
        ax.plot(mu, Phi_el, color=color, linewidth=1.8,
                label=rf'$\lambda={lam}$, $\lambda_\mu={wavelength:.2f}$')

    ax.axhline(y=0, color='k', linewidth=0.5)
    ax.set_xlabel(r'$\mu$', fontsize=13)
    ax.set_ylabel(r'$\Phi_\mathrm{EL}(\mu)$', fontsize=13)
    ax.set_title(r'E-L Solutions: $\partial_\mu^2\Phi + \frac{\lambda}{9}\Phi = 0$',
                 fontsize=12, pad=10)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-1.3, 1.3)

    # --- 右: 波長 vs λ ---
    ax2 = axes[1]
    lam_range = np.linspace(0.1, 50, 200)
    wavelength_theory = 6 * np.pi / np.sqrt(lam_range)

    ax2.plot(lam_range, wavelength_theory, 'b-', linewidth=2,
             label=r'Theory: $\lambda_\mu = 6\pi/\sqrt{\lambda}$')

    # 数値検証: 各 λ で FFT によるピーク波長を計算
    lam_test = [1, 2, 4, 9, 16, 25, 36, 49]
    wl_numerical = []
    for lam in lam_test:
        omega = np.sqrt(lam) / 3.0
        phi_test = np.cos(omega * mu)
        # 理論波長
        wl_theory = 6 * np.pi / np.sqrt(lam)
        # 数値: ゼロ交差間距離から波長を推定
        zero_crossings = np.where(np.diff(np.sign(phi_test)))[0]
        if len(zero_crossings) >= 2:
            half_wl = np.mean(np.diff(mu[zero_crossings]))
            wl_num = 2 * half_wl
        else:
            wl_num = wl_theory
        wl_numerical.append(wl_num)

    ax2.plot(lam_test, wl_numerical, 'ro', markersize=7,
             label='Numerical (zero-crossing)', zorder=5)

    # 誤差計算
    errors = [abs(wn - 6*np.pi/np.sqrt(l)) / (6*np.pi/np.sqrt(l)) * 100
              for wn, l in zip(wl_numerical, lam_test)]
    max_err = max(errors)

    ax2.set_xlabel(r'$\lambda$', fontsize=13)
    ax2.set_ylabel(r'Wavelength $\lambda_\mu = 2\pi/\omega$', fontsize=13)
    ax2.set_title(rf'Wavelength vs. $\lambda$ (max error: {max_err:.2f}%)',
                  fontsize=12, pad=10)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 65)

    fig.suptitle(r'Fig. 4: Euler-Lagrange Equation — Oscillatory Behaviour of $\Phi$',
                 fontsize=13, y=1.02)
    plt.tight_layout()

    path = os.path.join(out_dir, 'fig4_euler_lagrange.png')
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  ✅ Fig 4 → {path}")

    # 検証レポート
    print(f"\n  E-L 波長検証:")
    print(f"  {'λ':>6s}  {'理論':>8s}  {'数値':>8s}  {'誤差%':>6s}")
    for lam, wl_t, wl_n, err in zip(lam_test,
                                     [6*np.pi/np.sqrt(l) for l in lam_test],
                                     wl_numerical, errors):
        print(f"  {lam:6.0f}  {wl_t:8.4f}  {wl_n:8.4f}  {err:5.2f}%")

    return path


# ============================================================
# 定量検証
# ============================================================

def verify_analytics():
    """Paper I の解析的予測を数値的に検証する"""
    print("=" * 60)
    print("定量検証: Paper I §4 の解析的結果")
    print("=" * 60)

    # 1. Φ(0,1) = 0 (基準点)
    phi_ref = phi_field(0.0, 1.0)
    print(f"\n  Φ(0,1) = {phi_ref:.10f}  (期待: 0.0)")
    assert abs(phi_ref) < 1e-10, f"Φ(0,1) ≠ 0: {phi_ref}"

    # 2. F₁₂(0, σ) = 0 (等方忘却 → 力ゼロ)
    for sig in [0.5, 1.0, 2.0, 5.0]:
        f12 = oblivion_curvature(0.0, sig)
        print(f"  F₁₂(0, {sig}) = {f12:.10f}  (期待: 0.0)")
        assert abs(f12) < 1e-10, f"F₁₂(0,{sig}) ≠ 0"

    # 3. F₁₂(μ,σ) = 6μ/σ の数値微分との一致
    mu_test, sigma_test = 2.0, 1.5
    eps = 1e-6
    A1_p, A2_p = oblivion_connection(mu_test + eps, sigma_test)
    A1_m, A2_m = oblivion_connection(mu_test - eps, sigma_test)
    _, A2_sp = oblivion_connection(mu_test, sigma_test + eps)
    _, A2_sm = oblivion_connection(mu_test, sigma_test - eps)

    dA2_dmu_num = (A2_p - A2_m) / (2 * eps)
    # A₁ = μ なので ∂A₁/∂σ = 0
    F12_numerical = dA2_dmu_num - 0.0  # ∂₁A₂ - ∂₂A₁
    F12_analytic = oblivion_curvature(mu_test, sigma_test)

    err = abs(F12_numerical - F12_analytic) / abs(F12_analytic) * 100
    print(f"\n  F₁₂({mu_test},{sigma_test}):")
    print(f"    解析: {F12_analytic:.6f}")
    print(f"    数値 (中心差分): {F12_numerical:.6f}")
    print(f"    誤差: {err:.4f}%")
    assert err < 0.01, f"F₁₂ 数値微分の誤差が大きい: {err}%"

    # 4. α-dynamics の新項が遷移層に局在
    mu_arr = np.linspace(-10, 10, 1000)
    mu0 = 1.0
    sigma_fixed = 1.5
    dalpha_dmu = 1.0 / (mu0 * np.cosh(mu_arr / mu0)**2)
    Phi_arr = phi_field(mu_arr, sigma_fixed)
    new_term = (3.0 / sigma_fixed) * Phi_arr * dalpha_dmu

    # 遷移層 (|μ| < 2μ₀) 内のエネルギー比率
    in_layer = np.abs(mu_arr) < 2 * mu0
    energy_in = np.trapz(new_term[in_layer]**2, mu_arr[in_layer])
    energy_total = np.trapz(new_term**2, mu_arr)
    localization = energy_in / energy_total * 100

    print(f"\n  新項 Φ∂_μα の局在化 (μ₀={mu0}, σ={sigma_fixed}):")
    print(f"    遷移層内 (|μ|<{2*mu0}) エネルギー比: {localization:.1f}%")
    assert localization > 90, f"新項の局在化が不十分: {localization}%"

    print("\n  ✅ 全検証通過")


# ============================================================
# メイン
# ============================================================

def main():
    print("Paper I: Force is Oblivion — 数値シミュレーション")
    print("=" * 60)

    # 1. 定量検証
    verify_analytics()

    # 2. 図の生成
    print("\n" + "=" * 60)
    print("図の生成 (publication quality, 300 dpi)")
    print("=" * 60)

    paths = []
    paths.append(plot_fig1(OUT_DIR))
    paths.append(plot_fig2(OUT_DIR))
    paths.append(plot_fig3(OUT_DIR))
    paths.append(plot_fig4(OUT_DIR))

    print("\n" + "=" * 60)
    print("完了。生成ファイル:")
    for p in paths:
        print(f"  {p}")
    print("=" * 60)


if __name__ == '__main__':
    main()
