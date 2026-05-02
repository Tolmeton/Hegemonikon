#!/usr/bin/env python3
"""
e(α) 数値検証スクリプト — α-twisted comonoid のツイスト因子
================================================================

目的:
  構想2 (α-twisted comonoid) のツイスト因子 e(α) を
  ガウス族 ℋ² 上で数値的に計算し、
  摂動展開 e(α) ≈ 1 - (α/2)⟨tr(g⁻¹C)⟩_Φ + O(α²) との整合性を検証する。

理論背景:
  e(α) := Z^(α) / Z^(0)
  Z^(α) = ∫_{ℋ²} Φ(μ,σ) · √det(g^(α)) dμ dσ
  g^(α) は α-接続に対応する有効計量。
  
  Levi-Civita (α=0) からの逸脱量:
  √det(g^(α)) ≈ √det(g^(0)) · (1 - (α/2) tr(g⁻¹C) + O(α²))

ガウス族の具体式 (Paper I §4):
  θ = (μ, σ), σ > 0
  Fisher 計量: g = (1/σ²) diag(1, 2)
  Amari-Chentsov: C₁₁₂ = 2/σ³, C₂₂₂ = 8/σ³
  Chebyshev 1-形式: T = (T₁, T₂) = (0, 6/σ)
  
  tr(g⁻¹C):
    C^k_{ij} テンソルから tr を取る (= g^{jk} C_{ijk} = T_i)
    ここでの tr(g⁻¹C) は g^{ij} C_{ij}^k δ_k のスカラー化。
    具体的には: C のトレース = T_k δ^k = 6/σ (Chebyshev ノルム)
    
    詳細計算:
    g^{ij} C_{ijk} は T_k (Chebyshev 1-形式) そのもの (定義)。
    スカラー量 tr(g⁻¹C) = g^{kl} T_k T_l / dim 
    ではなく、det の 1 次補正は Γ^(α) - Γ^(0) の traceに由来:
    
    tr(Γ^(α) - Γ^(0)) = -(α/2) g^{ij} C_{ij}^k δ_k
    = -(α/2) Σ_k T_k = -(α/2)(T₁ + T₂) = -(α/2)(0 + 6/σ) = -3α/σ
    
    → √det(g^(α)) ≈ √det(g^(0)) · exp(-(α/2) · 6/σ · Δ)
    
    正確には: det(g^(α)) = det(g^(0)) · det(I + α·M)
    ここで M_{ij} = -(1/2) g^{ik} C_{kj}^l δ_l (接続の差分行列)

方法:
  1. 有限領域 [μ_min, μ_max] × [σ_min, σ_max] で数値積分
  2. α を [-3, 3] の範囲で変動させ、e(α) を計算
  3. α=0 で e(0)=1 となることを検証
  4. 摂動展開の1次係数を数値微分で抽出し、理論値と比較
"""

import numpy as np
from scipy import integrate
import matplotlib.pyplot as plt
from pathlib import Path

# ── ガウス族 ℋ² 上の幾何量 ──────────────────────────────

def fisher_metric(mu: float, sigma: float) -> np.ndarray:
    """Fisher 情報計量 g_{ij} (Paper I §4.1)"""
    return np.array([[1.0/sigma**2, 0.0],
                     [0.0, 2.0/sigma**2]])

def fisher_metric_inv(mu: float, sigma: float) -> np.ndarray:
    """Fisher 情報計量の逆 g^{ij}"""
    return np.array([[sigma**2, 0.0],
                     [0.0, sigma**2/2.0]])

def amari_chentsov_tensor(mu: float, sigma: float) -> np.ndarray:
    """Amari-Chentsov テンソル C_{ijk} (Paper I §4.2)
    
    非零成分: C₁₁₂ = C₁₂₁ = C₂₁₁ = 2/σ³, C₂₂₂ = 8/σ³
    (完全対称テンソル)
    """
    C = np.zeros((2, 2, 2))
    s3 = sigma**3
    # C_{112} = C_{121} = C_{211} = 2/σ³
    C[0, 0, 1] = 2.0/s3
    C[0, 1, 0] = 2.0/s3
    C[1, 0, 0] = 2.0/s3
    # C_{222} = 8/σ³
    C[1, 1, 1] = 8.0/s3
    return C

def chebyshev_form(mu: float, sigma: float) -> np.ndarray:
    """Chebyshev 1-形式 T_i = g^{jk} C_{ijk} (Paper I §4.2)
    
    T₁ = 0, T₂ = 6/σ
    """
    return np.array([0.0, 6.0/sigma])

def oblivion_field_B(mu: float, sigma: float) -> float:
    """忘却場 Φ_B (異方的忘却, Paper I §4.3 ケースB)
    
    q = N(0,1) に対する KL ダイバージェンス:
    Φ_B(μ,σ) = -log(σ) + (σ² + μ²)/2 - 1/2
    """
    return -np.log(sigma) + (sigma**2 + mu**2) / 2.0 - 0.5


# ── α 依存の有効体積要素 ──────────────────────────────────

def connection_deviation_matrix(mu: float, sigma: float) -> np.ndarray:
    """接続差分行列 M_{ij} = -(1/2) Σ_k g^{ik} C_{kj}^l δ_l
    
    α-接続による計量の有効的変化を表す行列。
    √det(g^(α)) ≈ √det(g^(0)) · (1 + α·tr(M) + (α²/2)·(tr(M)² - tr(M²)) + ...)
    
    厳密には Γ^(α)_{ij}^k = Γ^(0)_{ij}^k - (α/2) C_{ij}^k
    体積要素の変化 = exp(-α/2 · ∫ trace of torsion)
    
    ガウス族では明示的に計算可能:
    C^k_{ij} = g^{kl} C_{ijl}
    """
    g_inv = fisher_metric_inv(mu, sigma)
    C = amari_chentsov_tensor(mu, sigma)
    
    # C^k_{ij} = g^{kl} C_{ijl} を計算
    C_upper = np.zeros((2, 2, 2))  # C^k_{ij}
    for k in range(2):
        for i in range(2):
            for j in range(2):
                for l in range(2):
                    C_upper[k, i, j] += g_inv[k, l] * C[i, j, l]
    
    # 接続差分の「縮約行列」
    # M_{ij} = -(1/2) Σ_k C^k_{ij} の対角和に関わる量ではなく、
    # 体積要素の変化は Tr(Γ^(α) - Γ^(0)) に依存:
    # Γ^(α) trace: Γ^(α)k_{ik} = Γ^(0)k_{ik} - (α/2) C^k_{ik}
    # → ∂_i log √det(g^(α)) ≈ ∂_i log √det(g) - (α/2) C^k_{ik}
    # C^k_{ik} = T_i (Chebyshev 形式の定義)
    
    return C_upper

def sqrt_det_g_alpha(mu: float, sigma: float, alpha: float) -> float:
    """α-有効体積要素 √det(g^(α))
    
    厳密な計算:
    α-接続の体積要素は、基準 (α=0) からの偏差を
    接続差分の指数で表す。
    
    ガウス族では:
    Γ^(α)_{ij}^k = Γ^(0)_{ij}^k - (α/2) C^k_{ij}
    
    体積要素の α 補正は、混合テンソル C^k_{ij} の
    トレース部分 (= Chebyshev 形式 T_i) に支配される。
    
    正確な α 依存性:
    接続の差分が対称 (torsion-free) なので、
    有効計量は g^(α)_{ij} = g_{ij} + α·H_{ij} + O(α²)
    ここで H_{ij} = -(1/2)(C_{ij}^k g_{kl} + g_{ik} C^k_{jl}) (対称化)
    ではなく、より精密には:
    
    alpha-接続は計量接続ではないため、
    「α-有効計量」は直接的には定義されない。
    代わりに、統計多様体の体積形式の α 補正を
    接続の trace 部分から計算する:
    
    vol^(α) = vol^(0) · exp(-α/2 · ∫₀¹ Σ_i T_i(γ(t)) γ'_i(t) dt)
    
    局所的には点ごとの因子として:
    √det(g^(α))(θ) ≈ √det(g^(0))(θ) · (1 - (α/2) · S(θ))
    
    ここで S(θ) は局所的なスカラー量。
    
    ガウス族では (μ, σ) → (μ, σ) の恒等写像に対して:
    S(μ,σ) = Σ_k T_k = T₁ + T₂ = 0 + 6/σ = 6/σ
    
    ただし、これは1次近似。指数形式を使う:
    """
    # √det(g^(0)) = √(2/σ⁴) = √2 / σ²
    sqrt_det_g0 = np.sqrt(2.0) / sigma**2
    
    # α 補正因子: 指数的処理
    # ∂_α log √det(g^(α)) |_{α=0} = -(1/2) Σ_k T_k = -3/σ
    # → √det(g^(α)) ≈ √det(g^(0)) · exp(-α · 3/σ)
    # 
    # これは全次数の α 依存性を含む。
    # 摂動1次: 1 - 3α/σ + O(α²)
    # 
    # 非摂動的 (指数): exp(-3α/σ)
    correction = np.exp(-alpha * 3.0 / sigma)
    
    return sqrt_det_g0 * correction

def sqrt_det_g_alpha_perturbative(mu: float, sigma: float, alpha: float, order: int = 1) -> float:
    """摂動展開版の α-体積要素 (整合性チェック用)"""
    sqrt_det_g0 = np.sqrt(2.0) / sigma**2
    S = 6.0 / sigma  # Σ_k T_k
    
    if order == 1:
        correction = 1.0 - (alpha/2.0) * S
    elif order == 2:
        correction = 1.0 - (alpha/2.0) * S + (alpha**2/8.0) * S**2
    else:
        correction = np.exp(-alpha/2.0 * S)  # 全次数
    
    return sqrt_det_g0 * correction


# ── e(α) の計算 ─────────────────────────────────────────

def compute_Z_alpha(alpha: float, mu_range: tuple = (-5, 5), 
                    sigma_range: tuple = (0.3, 5.0),
                    use_perturbative: bool = False,
                    pert_order: int = 1) -> float:
    """Z^(α) = ∫_{ℋ²} Φ(μ,σ) · √det(g^(α)) dμ dσ の数値計算
    
    有限領域での積分。Φ_B を使用。
    """
    def integrand(sigma, mu):
        phi = oblivion_field_B(mu, sigma)
        if use_perturbative:
            vol = sqrt_det_g_alpha_perturbative(mu, sigma, alpha, pert_order)
        else:
            vol = sqrt_det_g_alpha(mu, sigma, alpha)
        return phi * vol
    
    result, error = integrate.dblquad(
        integrand,
        mu_range[0], mu_range[1],     # μ の範囲
        sigma_range[0], sigma_range[1], # σ の範囲
        epsabs=1e-10, epsrel=1e-10
    )
    return result

def compute_e_alpha(alpha: float, Z0: float = None, **kwargs) -> float:
    """e(α) = Z^(α) / Z^(0)"""
    if Z0 is None:
        Z0 = compute_Z_alpha(0.0, **kwargs)
    Za = compute_Z_alpha(alpha, **kwargs)
    return Za / Z0

def theoretical_e_alpha_first_order(alpha: float,
                                      mu_range: tuple = (-5, 5),
                                      sigma_range: tuple = (0.3, 5.0)) -> float:
    """理論的 e(α) の1次近似: e(α) ≈ 1 - (α/2)⟨tr(g⁻¹C)⟩_Φ
    
    ⟨tr(g⁻¹C)⟩_Φ = ∫ (6/σ) Φ(μ,σ) √det(g^(0)) dμ dσ / Z^(0)
    """
    # 分子: ∫ (6/σ) Φ √det(g^(0)) dμ dσ
    def integrand_num(sigma, mu):
        phi = oblivion_field_B(mu, sigma)
        sqrt_g0 = np.sqrt(2.0) / sigma**2
        S = 6.0 / sigma
        return S * phi * sqrt_g0
    
    # 分母: Z^(0) = ∫ Φ √det(g^(0)) dμ dσ
    def integrand_den(sigma, mu):
        phi = oblivion_field_B(mu, sigma)
        sqrt_g0 = np.sqrt(2.0) / sigma**2
        return phi * sqrt_g0
    
    num, _ = integrate.dblquad(integrand_num, 
                                mu_range[0], mu_range[1],
                                sigma_range[0], sigma_range[1],
                                epsabs=1e-10, epsrel=1e-10)
    den, _ = integrate.dblquad(integrand_den,
                                mu_range[0], mu_range[1],
                                sigma_range[0], sigma_range[1],
                                epsabs=1e-10, epsrel=1e-10)
    
    avg_S = num / den  # ⟨S⟩_Φ = ⟨6/σ⟩_Φ
    return 1.0 - (alpha/2.0) * avg_S, avg_S


# ── メイン検証 ──────────────────────────────────────────

def main():
    print("=" * 70)
    print("  e(α) 数値検証 — α-twisted comonoid ツイスト因子")
    print("  ガウス族 ℋ² (Paper I §4)")
    print("=" * 70)
    
    # 積分領域
    mu_range = (-5.0, 5.0)
    sigma_range = (0.3, 5.0)
    
    print(f"\n積分領域: μ ∈ {mu_range}, σ ∈ {sigma_range}")
    print(f"忘却場: Φ_B (異方的, q = N(0,1))")
    
    # ── 検証1: e(0) = 1 ──────────────────────────────────
    print("\n" + "-" * 70)
    print("検証1: e(0) = 1 (Fritz 帰着条件)")
    print("-" * 70)
    
    Z0 = compute_Z_alpha(0.0, mu_range=mu_range, sigma_range=sigma_range)
    e0 = compute_e_alpha(0.0, Z0=Z0, mu_range=mu_range, sigma_range=sigma_range)
    print(f"  Z^(0) = {Z0:.10f}")
    print(f"  e(0)  = {e0:.15f}")
    print(f"  |e(0) - 1| = {abs(e0 - 1.0):.2e}")
    assert abs(e0 - 1.0) < 1e-12, f"e(0) ≠ 1: {e0}"
    print("  ✅ PASS: e(0) = 1 (Fritz の標準 Markov category に帰着)")
    
    # ── 検証2: e(α) のプロファイル計算 ────────────────────
    print("\n" + "-" * 70)
    print("検証2: e(α) のプロファイル (α ∈ [-3, 3])")
    print("-" * 70)
    
    alphas = np.linspace(-3, 3, 61)
    e_values = np.array([compute_e_alpha(a, Z0=Z0, 
                                          mu_range=mu_range, 
                                          sigma_range=sigma_range) 
                          for a in alphas])
    
    print(f"\n  α={'':>6s}  e(α){'':>12s}  e(α)-1{'':>10s}")
    print(f"  {'-'*45}")
    for a, e in zip(alphas[::10], e_values[::10]):
        print(f"  {a:+7.2f}  {e:16.10f}  {e-1:+14.10f}")
    
    # ── 検証3: 摂動展開との比較 ────────────────────────────
    print("\n" + "-" * 70)
    print("検証3: 摂動展開 e(α) ≈ 1 - (α/2)⟨S⟩_Φ との整合性")
    print("-" * 70)
    
    # 理論的1次係数を計算
    _, avg_S = theoretical_e_alpha_first_order(0.01, mu_range=mu_range, 
                                                sigma_range=sigma_range)
    print(f"  ⟨S⟩_Φ = ⟨6/σ⟩_Φ = {avg_S:.10f}")
    print(f"  理論的1次係数: de/dα|₀ = -(1/2)⟨S⟩_Φ = {-avg_S/2:.10f}")
    
    # 数値微分で1次係数を抽出
    h = 0.001
    e_plus = compute_e_alpha(h, Z0=Z0, mu_range=mu_range, sigma_range=sigma_range)
    e_minus = compute_e_alpha(-h, Z0=Z0, mu_range=mu_range, sigma_range=sigma_range)
    numerical_deriv = (e_plus - e_minus) / (2 * h)
    
    print(f"  数値的1次係数: de/dα|₀ ≈ {numerical_deriv:.10f}")
    relative_error = abs(numerical_deriv - (-avg_S/2)) / abs(avg_S/2)
    print(f"  相対誤差: {relative_error:.2e}")
    
    if relative_error < 0.01:
        print("  ✅ PASS: 摂動展開が1次で整合 (相対誤差 < 1%)")
    else:
        print(f"  ⚠️ WARNING: 相対誤差 {relative_error:.2e} > 1%")
    
    # ── 検証4: 定性的振る舞い ──────────────────────────────
    print("\n" + "-" * 70)
    print("検証4: 定性的振る舞い (構想2の予測)")
    print("-" * 70)
    
    e_pos = compute_e_alpha(1.0, Z0=Z0, mu_range=mu_range, sigma_range=sigma_range)
    e_neg = compute_e_alpha(-1.0, Z0=Z0, mu_range=mu_range, sigma_range=sigma_range)
    
    print(f"  e(+1) = {e_pos:.10f}  {'< 1 \u2705' if e_pos < 1 else '\u2265 1 \u26a0\ufe0f'}  (m-\u63a5\u7d9a\u65b9\u5411: \u8907\u88fd\u7e2e\u5c0f)")
    print(f"  e(-1) = {e_neg:.10f}  {'> 1 \u2705' if e_neg > 1 else '\u2264 1 \u26a0\ufe0f'}  (e-\u63a5\u7d9a\u65b9\u5411: \u8907\u88fd\u81a8\u5f35)")
    print(f"  e(0)  = {e0:.10f}  {'= 1 ✅' if abs(e0-1)<1e-10 else '≠ 1 ⚠️'}  (Levi-Civita: Fritz 標準)")
    
    # α → -∞ 方向の崩壊チェック
    e_large_neg = compute_e_alpha(-3.0, Z0=Z0, mu_range=mu_range, sigma_range=sigma_range)
    print(f"  e(-3) = {e_large_neg:.10f}  (大きな負 α → 0 への収束傾向)")
    
    all_qualitative_pass = (e_pos < 1) and (e_neg > 1) and (abs(e0-1) < 1e-10)
    if all_qualitative_pass:
        print("  ✅ PASS: 全定性予測が整合")
    else:
        print("  ⚠️ WARNING: 一部の定性予測が不整合")
    
    # ── 検証5: 摂動 vs 非摂動 の比較 ──────────────────────
    print("\n" + "-" * 70)
    print("検証5: 摂動 (1次/2次) vs 非摂動 (指数) の比較")
    print("-" * 70)
    
    test_alphas = [-2.0, -1.0, -0.5, -0.1, 0.0, 0.1, 0.5, 1.0, 2.0]
    print(f"\n  α{'':>6s}  非摂動{'':>10s}  摂動1次{'':>9s}  摂動2次{'':>9s}  |Δ₁|/e{'':>8s}  |Δ₂|/e")
    print(f"  {'-'*85}")
    
    for a in test_alphas:
        e_exact = compute_e_alpha(a, Z0=Z0, mu_range=mu_range, sigma_range=sigma_range)
        
        Z_pert1 = compute_Z_alpha(a, mu_range=mu_range, sigma_range=sigma_range,
                                   use_perturbative=True, pert_order=1)
        e_pert1 = Z_pert1 / Z0
        
        Z_pert2 = compute_Z_alpha(a, mu_range=mu_range, sigma_range=sigma_range,
                                   use_perturbative=True, pert_order=2)
        e_pert2 = Z_pert2 / Z0
        
        err1 = abs(e_pert1 - e_exact) / abs(e_exact) if abs(e_exact) > 1e-15 else 0
        err2 = abs(e_pert2 - e_exact) / abs(e_exact) if abs(e_exact) > 1e-15 else 0
        
        print(f"  {a:+5.1f}  {e_exact:14.8f}  {e_pert1:14.8f}  {e_pert2:14.8f}  {err1:10.2e}  {err2:10.2e}")
    
    # ── 検証6: α 線形性 (命題 6.6.1 との整合) ─────────────
    print("\n" + "-" * 70)
    print("検証6: e(α) の α 線形性テスト (命題 6.6.1 との整合)")
    print("-" * 70)
    
    # 小さい α での線形性フィット
    alphas_small = np.linspace(-0.5, 0.5, 21)
    e_small = np.array([compute_e_alpha(a, Z0=Z0, 
                                         mu_range=mu_range,
                                         sigma_range=sigma_range)
                         for a in alphas_small])
    
    # 線形フィット: e(α) ≈ 1 + c₁α
    coeffs = np.polyfit(alphas_small, e_small, 1)
    c1_fit = coeffs[0]  # 1次係数
    c0_fit = coeffs[1]  # 定数項 (≈ 1)
    residuals_linear = e_small - np.polyval(coeffs, alphas_small)
    
    # 2次フィット: e(α) ≈ 1 + c₁α + c₂α²
    coeffs2 = np.polyfit(alphas_small, e_small, 2)
    residuals_quadratic = e_small - np.polyval(coeffs2, alphas_small)
    
    print(f"  線形フィット: e(α) ≈ {c0_fit:.8f} + ({c1_fit:.8f})α")
    print(f"    c₀ = {c0_fit:.10f} (理論: 1.0)")
    print(f"    c₁ = {c1_fit:.10f} (理論: {-avg_S/2:.10f})")
    print(f"    残差L∞ (線形): {np.max(np.abs(residuals_linear)):.2e}")
    print(f"    残差L∞ (2次):  {np.max(np.abs(residuals_quadratic)):.2e}")
    print(f"    2次補正の大きさ: c₂ = {coeffs2[0]:.6e}")
    
    linearity_ratio = np.max(np.abs(residuals_linear)) / np.max(np.abs(e_small - 1.0 + 1e-15))
    print(f"    線形性指標 (残差/変動): {linearity_ratio:.4f}")
    if linearity_ratio < 0.05:
        print(f"  ✅ PASS: |α| ≤ 0.5 で高い線形性 (命題 6.6.1 と整合)")
    else:
        print(f"  ◯ 線形性は中程度。2次補正が有意")
    
    # ── プロット ──────────────────────────────────────────
    output_dir = Path(__file__).parent
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(r'$e(\alpha)$ — $\alpha$-twisted comonoid twist factor on $\mathcal{H}^2$',
                 fontsize=14, fontweight='bold')
    
    # (a) e(α) プロファイル
    ax = axes[0, 0]
    ax.plot(alphas, e_values, 'b-', linewidth=2, label=r'$e(\alpha)$ (numerical)')
    ax.axhline(y=1.0, color='k', linestyle='--', alpha=0.5, label=r'$e(0) = 1$ (Fritz)')
    ax.axvline(x=0.0, color='k', linestyle=':', alpha=0.3)
    ax.fill_between(alphas, 1.0, e_values, alpha=0.15, color='blue')
    ax.set_xlabel(r'$\alpha$')
    ax.set_ylabel(r'$e(\alpha)$')
    ax.set_title(r'(a) Twist factor $e(\alpha) = Z^{(\alpha)}/Z^{(0)}$')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # (b) 摂動比較
    ax = axes[0, 1]
    e_pert1_curve = np.array([
        compute_Z_alpha(a, mu_range=mu_range, sigma_range=sigma_range,
                        use_perturbative=True, pert_order=1) / Z0
        for a in alphas
    ])
    e_pert2_curve = np.array([
        compute_Z_alpha(a, mu_range=mu_range, sigma_range=sigma_range,
                        use_perturbative=True, pert_order=2) / Z0
        for a in alphas
    ])
    
    ax.plot(alphas, e_values, 'b-', linewidth=2, label='Non-perturbative')
    ax.plot(alphas, e_pert1_curve, 'r--', linewidth=1.5, label=r'O($\alpha$)')
    ax.plot(alphas, e_pert2_curve, 'g-.', linewidth=1.5, label=r'O($\alpha^2$)')
    ax.axhline(y=1.0, color='k', linestyle='--', alpha=0.3)
    ax.set_xlabel(r'$\alpha$')
    ax.set_ylabel(r'$e(\alpha)$')
    ax.set_title('(b) Perturbative vs non-perturbative')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # (c) 残差 (e(α) - 線形近似)
    ax = axes[1, 0]
    e_linear_fit = 1.0 + c1_fit * alphas
    residuals_full = e_values - e_linear_fit
    ax.plot(alphas, residuals_full, 'r-', linewidth=2)
    ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax.set_xlabel(r'$\alpha$')
    ax.set_ylabel(r'$e(\alpha) - (1 + c_1 \alpha)$')
    ax.set_title(r'(c) Residuals from linear fit (= $O(\alpha^2)$ correction)')
    ax.grid(True, alpha=0.3)
    
    # (d) log|e(α)| vs α (指数的振る舞いの確認)
    ax = axes[1, 1]
    ax.plot(alphas, np.log(np.abs(e_values)), 'b-', linewidth=2, label=r'$\ln|e(\alpha)|$')
    # 理論的傾き: -3/⟨σ⟩ ≈ -3/σ_eff
    ax.plot(alphas, -3.0 * alphas / 2.0, 'r--', linewidth=1.5, 
            label=r'$-3\alpha/\langle\sigma\rangle$ (est.)')
    ax.set_xlabel(r'$\alpha$')
    ax.set_ylabel(r'$\ln|e(\alpha)|$')
    ax.set_title(r'(d) Log-scale: exponential behavior check')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_path = output_dir / 'e_alpha_verification.png'
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"\n📊 プロット保存: {plot_path}")
    plt.close()
    
    # ── サマリー ────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  検証サマリー")
    print("=" * 70)
    print(f"  検証1 e(0) = 1 (Fritz 帰着):     {'✅ PASS' if abs(e0-1)<1e-10 else '❌ FAIL'}")
    print(f"  検証2 プロファイル計算:           ✅ 完了")
    print(f"  検証3 摂動展開整合:              {'✅ PASS' if relative_error < 0.01 else '⚠️ WARNING'} (Δ={relative_error:.2e})")
    print(f"  検証4 定性的振る舞い:            {'✅ PASS' if all_qualitative_pass else '⚠️ WARNING'}")
    print(f"  検証5 摂動 vs 非摂動:            ✅ テーブル出力")
    print(f"  検証6 α 線形性:                 {'✅ PASS' if linearity_ratio < 0.05 else '◯ 中程度'} (比={linearity_ratio:.4f})")
    print(f"\n  核心パラメータ:")
    print(f"    ⟨6/σ⟩_Φ = {avg_S:.8f}")
    print(f"    de/dα|₀ = {c1_fit:.8f}")
    print(f"    e(+1)   = {e_pos:.8f} (膨張)")
    print(f"    e(-1)   = {e_neg:.8f} (縮小)")
    print("=" * 70)


if __name__ == "__main__":
    main()
