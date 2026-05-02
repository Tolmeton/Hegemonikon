#!/usr/bin/env python3
"""高次元 (n>2) c-α 接続の数値検証

PURPOSE: n>2 次元 OU 過程での電流 Fisher 計量 g^{(c,F)} を数値計算し、
等方回転 (ω_k = ω) と異方回転 (ω_k ≠ ω_l) での構造的差異を検証する。

核心の問い:
  - 等方回転: g^{(c,F)} = (1/ω²) · I? (2D に帰着)
  - 異方回転: g^{(c,F)}_{kl} は V (=A) に依存するか?
  - 対角性: k≠l の交差項はゼロか?

手法: Monte Carlo サンプリング (OU 定常分布 p_ss は既知のガウス)
"""

import numpy as np
from typing import Optional

# --- 理論的準備 ---

def make_Q_normal_form(omegas: list[float], n: int) -> np.ndarray:
    """Q の正規形を構築 (反対称行列)

    Q = diag(ω_1 J, ω_2 J, ..., [0])
    J = [[0, -1], [1, 0]]
    """
    Q = np.zeros((n, n))
    for k, omega in enumerate(omegas):
        i = 2 * k
        Q[i, i+1] = -omega
        Q[i+1, i] = omega
    return Q

def make_A_block_diag(a_values: list[float], n: int) -> np.ndarray:
    """A を Q の正規形基底でブロック対角に構築

    A = diag(a_1 I_2, a_2 I_2, ..., [a_last])
    """
    A = np.zeros((n, n))
    for k, a in enumerate(a_values):
        if 2*k + 1 < n:
            A[2*k, 2*k] = a
            A[2*k+1, 2*k+1] = a
        else:
            # 奇数次元の最後
            A[2*k, 2*k] = a
    return A

def make_A_general(n: int, seed: int = 42) -> np.ndarray:
    """一般的な正定値対称行列 A を生成（Q の正規形基底で非ブロック対角）"""
    rng = np.random.default_rng(seed)
    # ランダム正定値行列
    M = rng.standard_normal((n, n))
    A = M.T @ M / n + np.eye(n)  # 正定値保証
    return A

def compute_steady_state_cov(A: np.ndarray, sigma: float) -> np.ndarray:
    """OU 過程 dx = -(A+Q)x dt + σ dW の定常共分散行列

    Lyapunov 方程式: (A+Q)Σ + Σ(A+Q)^T = σ² I
    OU の場合 p_ss ∝ exp(-x^T A x / σ²) なので Σ = (σ²/2) A^{-1}
    """
    # OU 定常分布は Q に依存しない (T1 ω-不変性)
    return (sigma**2 / 2) * np.linalg.inv(A)

def sample_from_steady_state(A: np.ndarray, sigma: float, n_samples: int,
                              seed: int = 123) -> np.ndarray:
    """定常分布 p_ss = N(0, Σ) からサンプリング"""
    Sigma = compute_steady_state_cov(A, sigma)
    rng = np.random.default_rng(seed)
    return rng.multivariate_normal(np.zeros(A.shape[0]), Sigma, size=n_samples)

# --- 電流 Fisher 計量の計算 ---

def compute_dw_log_j(x: np.ndarray, Q: np.ndarray, A: np.ndarray,
                      omegas: list[float]) -> np.ndarray:
    """∂_{ω_k} log|j_ss(x)| を計算

    j = p_ss · Q ∇V = p_ss · Q A x
    |j|² = (QAx)^T (QAx)
    log|j| = log p_ss + ½ log|QAx|²

    ∂_{ω_k} log|j| = ∂_{ω_k} [½ log|QAx|²]
                    = (QAx)^T (∂_{ω_k} Q) A x / |QAx|²

    ∂_{ω_k} Q は k 番目の 2D ブロックのみ非ゼロ:
    [∂_{ω_k} Q]_{2k, 2k+1} = -1,  [∂_{ω_k} Q]_{2k+1, 2k} = 1
    """
    n = Q.shape[0]
    n_omega = len(omegas)
    n_samples = x.shape[0]

    # QAx を計算
    Ax = x @ A.T  # (n_samples, n)
    QAx = Ax @ Q.T  # (n_samples, n) — Q は反対称なので Q^T = -Q

    QAx_norm_sq = np.sum(QAx**2, axis=1)  # (n_samples,)

    # 各 ω_k に対する微分
    dw_log_j = np.zeros((n_samples, n_omega))

    for k in range(n_omega):
        # ∂_{ω_k} Q の効果: k 番目の 2D ブロックに J を入れる
        # (∂_{ω_k} Q) A x の 2k, 2k+1 成分のみ非ゼロ
        # ∂_{ω_k} Q_{2k, 2k+1} = -1, ∂_{ω_k} Q_{2k+1, 2k} = 1
        # → (∂_{ω_k} Q · Ax)_{2k} = -Ax_{2k+1}, (∂_{ω_k} Q · Ax)_{2k+1} = Ax_{2k}
        dQ_Ax = np.zeros((n_samples, n))
        dQ_Ax[:, 2*k] = -Ax[:, 2*k+1]
        dQ_Ax[:, 2*k+1] = Ax[:, 2*k]

        # ∂_{ω_k} log|j| = QAx · dQ_Ax / |QAx|²
        numerator = np.sum(QAx * dQ_Ax, axis=1)  # (n_samples,)
        dw_log_j[:, k] = numerator / QAx_norm_sq

    return dw_log_j  # (n_samples, n_omega)

def compute_current_fisher_metric(x: np.ndarray, Q: np.ndarray, A: np.ndarray,
                                    omegas: list[float]) -> np.ndarray:
    """電流 Fisher 計量 g^{(c,F)}_{kl} = E[∂_{ω_k} log|j| · ∂_{ω_l} log|j|]"""
    dw = compute_dw_log_j(x, Q, A, omegas)  # (n_samples, n_omega)
    n_omega = len(omegas)

    # 期待値 (Monte Carlo)
    g_cF = np.zeros((n_omega, n_omega))
    for k in range(n_omega):
        for l in range(n_omega):
            g_cF[k, l] = np.mean(dw[:, k] * dw[:, l])

    return g_cF

def compute_g_circ(x: np.ndarray, Q: np.ndarray, A: np.ndarray,
                    sigma: float) -> float:
    """循環計量 g^(c) = E[|Q∇V|² · σ⁴/4] (p_ss 期待値)

    g^(c) = (σ⁴/4) Tr(Q^T Q · G^{sp})
    G^{sp}_{ij} = E[(∂_i V)(∂_j V)] · (4/σ⁴)

    直接計算: g^(c) = ∫ |Q∇V|² p_ss dx = E[|QAx|²]
    """
    Ax = x @ A.T
    QAx = Ax @ Q.T
    return np.mean(np.sum(QAx**2, axis=1))

# --- テストケース ---

def test_2d_recovery():
    """2D: g^{(c,F)} = 1/ω² を確認"""
    print("=" * 60)
    print("テスト 1: 2D 回復テスト")
    print("=" * 60)

    omega = 1.5
    sigma = 1.0
    n_samples = 500_000

    for a_vals, label in [
        ([1.0], "OU (a=1)"),
        ([2.0], "OU (a=2)"),
        ([3.0], "OU (a=3)")
    ]:
        A = make_A_block_diag(a_vals, 2)
        Q = make_Q_normal_form([omega], 2)
        x = sample_from_steady_state(A, sigma, n_samples)

        g_cF = compute_current_fisher_metric(x, Q, A, [omega])
        theory = 1.0 / omega**2

        print(f"  {label}: g^{{(c,F)}} = {g_cF[0,0]:.6f}, "
              f"理論値 1/ω² = {theory:.6f}, "
              f"誤差 = {abs(g_cF[0,0] - theory)/theory:.2e}")

    print()

def test_4d_isotropic():
    """4D 等方回転: g^{(c,F)} = (1/ω²) I₂ を確認"""
    print("=" * 60)
    print("テスト 2: 4D 等方回転 (ω₁ = ω₂ = ω)")
    print("=" * 60)

    omega = 1.0
    sigma = 1.0
    n_samples = 500_000

    for a_vals, label in [
        ([1.0, 2.0], "A = diag(1,1,2,2)"),
        ([1.0, 1.0], "A = diag(1,1,1,1)"),
        ([2.0, 3.0], "A = diag(2,2,3,3)")
    ]:
        A = make_A_block_diag(a_vals, 4)
        Q = make_Q_normal_form([omega, omega], 4)
        x = sample_from_steady_state(A, sigma, n_samples)

        g_cF = compute_current_fisher_metric(x, Q, A, [omega, omega])
        theory_diag = 1.0 / omega**2

        print(f"  {label}:")
        print(f"    g^{{(c,F)}} = ")
        for row in g_cF:
            print(f"      [{', '.join(f'{v:+.6f}' for v in row)}]")
        print(f"    理論値 (等方): diag(1/ω²) = {theory_diag:.6f}")
        print(f"    対角精度: {abs(g_cF[0,0] - theory_diag)/theory_diag:.2e}, "
              f"{abs(g_cF[1,1] - theory_diag)/theory_diag:.2e}")
        print(f"    交差項: |g_01| = {abs(g_cF[0,1]):.2e}")

    print()

def test_4d_anisotropic():
    """4D 異方回転: g^{(c,F)} の V 依存性を検証"""
    print("=" * 60)
    print("テスト 3: 4D 異方回転 (ω₁ ≠ ω₂) — V 依存性テスト")
    print("=" * 60)

    omegas = [1.0, 2.0]
    sigma = 1.0
    n_samples = 1_000_000

    results = []
    for a_vals, label in [
        ([1.0, 1.0], "A = diag(1,1,1,1)"),
        ([1.0, 3.0], "A = diag(1,1,3,3)"),
        ([2.0, 5.0], "A = diag(2,2,5,5)"),
        ([1.0, 10.0], "A = diag(1,1,10,10)")
    ]:
        A = make_A_block_diag(a_vals, 4)
        Q = make_Q_normal_form(omegas, 4)
        x = sample_from_steady_state(A, sigma, n_samples)

        g_cF = compute_current_fisher_metric(x, Q, A, omegas)
        g_c = compute_g_circ(x, Q, A, sigma)

        results.append((label, g_cF, g_c, a_vals))

        print(f"  {label}:")
        print(f"    g^{{(c,F)}} = ")
        for row in g_cF:
            print(f"      [{', '.join(f'{v:+.6f}' for v in row)}]")
        print(f"    g^(c) = {g_c:.6f}")

        # 等方理論値との比較
        iso_diag = [1.0/w**2 for w in omegas]
        print(f"    等方理論値: diag({iso_diag[0]:.4f}, {iso_diag[1]:.4f})")
        print(f"    偏差: g_00 - 1/ω₁² = {g_cF[0,0] - iso_diag[0]:+.6f}")
        print(f"          g_11 - 1/ω₂² = {g_cF[1,1] - iso_diag[1]:+.6f}")
        print(f"    交差項 g_01 = {g_cF[0,1]:+.6f}")

    # V 依存性の確認
    print("\n  ★ V 依存性テスト:")
    print(f"    異なる A での g^{{(c,F)}}_{'{00}'} の変動:")
    g00_values = [r[1][0,0] for r in results]
    g11_values = [r[1][1,1] for r in results]
    print(f"    g_00: {[f'{v:.4f}' for v in g00_values]}")
    print(f"    g_11: {[f'{v:.4f}' for v in g11_values]}")
    variation_00 = max(g00_values) - min(g00_values)
    variation_11 = max(g11_values) - min(g11_values)
    print(f"    g_00 変動幅: {variation_00:.4f} "
          f"({'V依存' if variation_00 > 0.01 else 'V非依存'})")
    print(f"    g_11 変動幅: {variation_11:.4f} "
          f"({'V依存' if variation_11 > 0.01 else 'V非依存'})")

    print()

def test_6d_anisotropic():
    """6D 異方回転: 3回転面"""
    print("=" * 60)
    print("テスト 4: 6D 異方回転 (ω₁, ω₂, ω₃)")
    print("=" * 60)

    omegas = [1.0, 2.0, 3.0]
    sigma = 1.0
    n_samples = 1_000_000

    for a_vals, label in [
        ([1.0, 1.0, 1.0], "A = I₆"),
        ([1.0, 2.0, 3.0], "A = diag(1,1,2,2,3,3)"),
        ([1.0, 5.0, 10.0], "A = diag(1,1,5,5,10,10)")
    ]:
        A = make_A_block_diag(a_vals, 6)
        Q = make_Q_normal_form(omegas, 6)
        x = sample_from_steady_state(A, sigma, n_samples)

        g_cF = compute_current_fisher_metric(x, Q, A, omegas)
        g_c = compute_g_circ(x, Q, A, sigma)

        print(f"  {label}:")
        print(f"    g^{{(c,F)}} (3×3):")
        for row in g_cF:
            print(f"      [{', '.join(f'{v:+.6f}' for v in row)}]")
        print(f"    g^(c) = {g_c:.6f}")

        # 等方理論値
        iso = [1.0/w**2 for w in omegas]
        print(f"    等方理論値: diag({', '.join(f'{v:.4f}' for v in iso)})")

    print()

def test_4d_general_A():
    """4D: 一般的な A (Q の正規形基底で非ブロック対角) で検証"""
    print("=" * 60)
    print("テスト 5: 4D 一般的 A (非ブロック対角)")
    print("=" * 60)

    omegas_iso = [1.0, 1.0]
    omegas_aniso = [1.0, 3.0]
    sigma = 1.0
    n_samples = 1_000_000

    A_gen = make_A_general(4, seed=42)
    print(f"  A (一般的正定値対称):")
    for row in A_gen:
        print(f"    [{', '.join(f'{v:+.4f}' for v in row)}]")

    for omegas, label in [
        (omegas_iso, "等方 ω=(1,1)"),
        (omegas_aniso, "異方 ω=(1,3)")
    ]:
        Q = make_Q_normal_form(omegas, 4)
        x = sample_from_steady_state(A_gen, sigma, n_samples)

        g_cF = compute_current_fisher_metric(x, Q, A_gen, omegas)
        g_c = compute_g_circ(x, Q, A_gen, sigma)

        print(f"\n  {label}:")
        print(f"    g^{{(c,F)}} =")
        for row in g_cF:
            print(f"      [{', '.join(f'{v:+.6f}' for v in row)}]")
        print(f"    g^(c) = {g_c:.6f}")

        # 等方理論値
        iso = [1.0/w**2 for w in omegas]
        print(f"    等方理論値: diag({', '.join(f'{v:.4f}' for v in iso)})")

    print()

def test_trade_off_identity():
    """高次元 trade-off 恒等式のテスト

    g^(c) · det(g^{(c,F)}) と (σ⁴/4)^n · det(I_F) の関係
    """
    print("=" * 60)
    print("テスト 6: Trade-off 恒等式の高次元版")
    print("=" * 60)

    sigma = 1.0
    n_samples = 1_000_000

    for omegas, a_vals, label in [
        ([1.0, 1.0], [1.0, 2.0], "4D 等方"),
        ([1.0, 2.0], [1.0, 2.0], "4D 異方"),
        ([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], "6D 異方")
    ]:
        n = 2 * len(omegas)
        A = make_A_block_diag(a_vals, n)
        Q = make_Q_normal_form(omegas, n)
        x = sample_from_steady_state(A, sigma, n_samples)

        g_cF = compute_current_fisher_metric(x, Q, A, omegas)
        g_c = compute_g_circ(x, Q, A, sigma)

        # 各回転面の寄与
        for k, (w, a) in enumerate(zip(omegas, a_vals)):
            # I_F^(k) = (2/σ²) · 2a = 4a/σ² (各面の Fisher 情報)
            I_F_k = 4 * a / sigma**2
            g_c_k = w**2 * sigma**4 / 4 * I_F_k
            print(f"  {label} 回転面 {k}: ω={w}, a={a}")
            print(f"    I_F^({k}) = {I_F_k:.4f}")
            print(f"    g^(c)_k (理論) = ω²(σ⁴/4)I_F^(k) = {g_c_k:.4f}")

        # 全体
        I_F_total = sum(4*a/sigma**2 for a in a_vals)
        g_c_theory = sigma**4/4 * sum(w**2 * 4*a/sigma**2 for w, a in zip(omegas, a_vals))

        print(f"  {label} 全体:")
        print(f"    g^(c) 数値: {g_c:.4f}")
        print(f"    g^(c) 理論: {g_c_theory:.4f}")
        print(f"    誤差: {abs(g_c - g_c_theory)/g_c_theory:.2e}")
        print()

    print()


# --- 非 OU ポテンシャル用ヘルパー ---

def mcmc_sample_general(grad_V_func, V_func, n_dim: int, sigma: float,
                         n_samples: int, n_burnin: int = 10000,
                         step_size: float = 0.3, seed: int = 42) -> np.ndarray:
    """一般ポテンシャル V(x) の定常分布 p_ss ∝ exp(-2V/σ²) から MCMC サンプリング

    Metropolis-Hastings 法を使用。
    """
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n_dim) * 0.5  # 初期点
    samples = np.zeros((n_samples, n_dim))

    n_accept = 0
    for i in range(n_burnin + n_samples):
        # 提案
        x_prop = x + rng.standard_normal(n_dim) * step_size
        # 受理確率: exp(-2(V(x')-V(x))/σ²)
        dV = V_func(x_prop) - V_func(x)
        log_alpha = -2 * dV / sigma**2
        if np.log(rng.uniform()) < log_alpha:
            x = x_prop
            if i >= n_burnin:
                n_accept += 1
        if i >= n_burnin:
            samples[i - n_burnin] = x

    accept_rate = n_accept / n_samples
    return samples, accept_rate

def compute_dw_log_j_general(x: np.ndarray, Q: np.ndarray,
                               grad_V_func, omegas: list[float]) -> np.ndarray:
    """一般ポテンシャル用の ∂_{ω_k} log|j_ss(x)| を計算

    j = p_ss · Q ∇V(x)
    |j|² ∝ |Q ∇V(x)|²  (p_ss は ω に依存しない: T1)
    ∂_{ω_k} log|j| = ∂_{ω_k} [½ log|Q ∇V|²]
                    = (Q∇V)^T (∂_{ω_k}Q) ∇V / |Q∇V|²
    """
    n = Q.shape[0]
    n_omega = len(omegas)
    n_samples = x.shape[0]

    # ∇V(x) を全サンプルで計算
    grad_V = np.array([grad_V_func(xi) for xi in x])  # (n_samples, n)

    # Q ∇V を計算
    QgV = grad_V @ Q.T  # (n_samples, n)
    QgV_norm_sq = np.sum(QgV**2, axis=1)  # (n_samples,)

    # |Q∇V| = 0 のサンプルを除外 (零電流点)
    valid = QgV_norm_sq > 1e-20
    if np.sum(~valid) > 0:
        print(f"    ⚠️ {np.sum(~valid)} サンプルで |Q∇V|≈0 を除外")

    dw_log_j = np.zeros((n_samples, n_omega))

    for k in range(n_omega):
        # (∂_{ω_k}Q) ∇V: k 番目の 2D ブロックに J を入れる
        dQgV = np.zeros((n_samples, n))
        dQgV[:, 2*k] = -grad_V[:, 2*k+1]
        dQgV[:, 2*k+1] = grad_V[:, 2*k]

        numerator = np.sum(QgV * dQgV, axis=1)
        dw_log_j[valid, k] = numerator[valid] / QgV_norm_sq[valid]

    return dw_log_j[valid]  # 有効サンプルのみ

def compute_current_fisher_general(x: np.ndarray, Q: np.ndarray,
                                     grad_V_func, omegas: list[float]) -> np.ndarray:
    """一般ポテンシャル用の電流 Fisher 計量"""
    dw = compute_dw_log_j_general(x, Q, grad_V_func, omegas)
    n_omega = len(omegas)
    g_cF = np.zeros((n_omega, n_omega))
    for k in range(n_omega):
        for l in range(n_omega):
            g_cF[k, l] = np.mean(dw[:, k] * dw[:, l])
    return g_cF

# --- 非 OU ポテンシャル定義 ---

def make_duffing_4d(a1: float, a2: float, b1: float = 1.0, b2: float = 1.0):
    """Duffing 4D: V = Σ_k [a_k (x_{2k}^4 + x_{2k+1}^4)/4 + b_k (x_{2k}^2 + x_{2k+1}^2)/2]

    ∇V_i = a_k x_i³ + b_k x_i  (i は k 番目の回転面)
    """
    def V(x):
        return (a1 * (x[0]**4 + x[1]**4)/4 + b1 * (x[0]**2 + x[1]**2)/2
                + a2 * (x[2]**4 + x[3]**4)/4 + b2 * (x[2]**2 + x[3]**2)/2)
    def grad_V(x):
        return np.array([
            a1 * x[0]**3 + b1 * x[0],
            a1 * x[1]**3 + b1 * x[1],
            a2 * x[2]**3 + b2 * x[2],
            a2 * x[3]**3 + b2 * x[3],
        ])
    return V, grad_V

def make_double_well_4d(barrier: float = 2.0, a2: float = 1.0):
    """Double Well 4D: V = (|x_{01}|²-1)² の 2D DW + harmonic 2D

    面1: V_1 = barrier * (x₀² + x₁² - 1)²
    面2: V_2 = a2 * (x₂² + x₃²) / 2
    """
    def V(x):
        r1_sq = x[0]**2 + x[1]**2
        return barrier * (r1_sq - 1)**2 + a2 * (x[2]**2 + x[3]**2) / 2
    def grad_V(x):
        r1_sq = x[0]**2 + x[1]**2
        return np.array([
            4 * barrier * (r1_sq - 1) * x[0],
            4 * barrier * (r1_sq - 1) * x[1],
            a2 * x[2],
            a2 * x[3],
        ])
    return V, grad_V

# --- 非 OU テストケース ---

def test_non_ou_duffing_4d():
    """テスト 7: Duffing 4D — 非 OU での T10 検証

    T10 予測:
    - 等方 (ω₁=ω₂): g^{(c,F)} は V パラメータに非依存 → dually flat
    - 異方 (ω₁≠ω₂): g^{(c,F)} は V パラメータに依存 → dually flat 崩壊
    """
    print("=" * 60)
    print("テスト 7: Duffing 4D — 非 OU での T10 (dually flat ⟺ 等方回転)")
    print("=" * 60)

    sigma = 1.0
    n_samples = 200_000
    n_burnin = 20_000

    # --- 異方回転: V 依存性を確認 ---
    print("\n  [異方回転] ω = (1.0, 2.0):")
    omegas_aniso = [1.0, 2.0]

    results_aniso = []
    for (a1, a2, b1, b2), label in [
        ((0.5, 0.5, 1.0, 1.0), "Duffing a=(0.5,0.5)"),
        ((2.0, 0.5, 1.0, 1.0), "Duffing a=(2.0,0.5)"),
        ((0.5, 2.0, 1.0, 1.0), "Duffing a=(0.5,2.0)"),
    ]:
        V_func, grad_V_func = make_duffing_4d(a1, a2, b1, b2)
        Q = make_Q_normal_form(omegas_aniso, 4)

        x, acc = mcmc_sample_general(grad_V_func, V_func, 4, sigma,
                                       n_samples, n_burnin)
        g_cF = compute_current_fisher_general(x, Q, grad_V_func, omegas_aniso)

        results_aniso.append((label, g_cF))
        print(f"    {label} (受理率={acc:.2f}):")
        print(f"      g^{{(c,F)}} = [[{g_cF[0,0]:.6f}, {g_cF[0,1]:.6f}],")
        print(f"                    [{g_cF[1,0]:.6f}, {g_cF[1,1]:.6f}]]")

    # V 依存性の定量評価
    g00_aniso = [r[1][0,0] for r in results_aniso]
    g11_aniso = [r[1][1,1] for r in results_aniso]
    var_00 = max(g00_aniso) - min(g00_aniso)
    var_11 = max(g11_aniso) - min(g11_aniso)
    print(f"\n    ★ 異方 V 依存性: g_00 変動={var_00:.4f}, g_11 変動={var_11:.4f}")
    print(f"      → {'V依存 (T10 一致)' if var_00 > 0.01 else 'V非依存 (T10 矛盾!)'}")

    # --- 等方回転: V 非依存性を確認 ---
    print("\n  [等方回転] ω = (1.0, 1.0):")
    omegas_iso = [1.0, 1.0]

    results_iso = []
    for (a1, a2, b1, b2), label in [
        ((0.5, 0.5, 1.0, 1.0), "Duffing a=(0.5,0.5)"),
        ((2.0, 0.5, 1.0, 1.0), "Duffing a=(2.0,0.5)"),
        ((0.5, 2.0, 1.0, 1.0), "Duffing a=(0.5,2.0)"),
    ]:
        V_func, grad_V_func = make_duffing_4d(a1, a2, b1, b2)
        Q = make_Q_normal_form(omegas_iso, 4)

        x, acc = mcmc_sample_general(grad_V_func, V_func, 4, sigma,
                                       n_samples, n_burnin)
        g_cF = compute_current_fisher_general(x, Q, grad_V_func, omegas_iso)

        results_iso.append((label, g_cF))
        print(f"    {label} (受理率={acc:.2f}):")
        print(f"      g^{{(c,F)}} = [[{g_cF[0,0]:.6f}, {g_cF[0,1]:.6f}],")
        print(f"                    [{g_cF[1,0]:.6f}, {g_cF[1,1]:.6f}]]")

    # ω をスカラーとして扱った場合の理論値: 1/ω² = 1.0
    g_scalar_iso = [r[1][0,0] + 2*r[1][0,1] + r[1][1,1] for r in results_iso]
    print(f"\n    ★ 等方 V 依存性テスト:")
    print(f"      g_scalar (=g_00+2g_01+g_11) = {[f'{v:.4f}' for v in g_scalar_iso]}")
    var_scalar = max(g_scalar_iso) - min(g_scalar_iso)
    print(f"      変動幅 = {var_scalar:.4f}")
    print(f"      → {'V非依存 (T10 一致)' if var_scalar < 0.05 else 'V依存 (T10 矛盾!)'}")

    print()

def test_non_ou_double_well_4d():
    """テスト 8: Double Well 4D — 強い非ガウス性での T10 検証

    DW ポテンシャル: V = barrier*(|x₀₁|²-1)² + (a₂/2)|x₂₃|²
    分布はリング状 (面1) + ガウス (面2)。強い非ガウス性。
    """
    print("=" * 60)
    print("テスト 8: Double Well (リング状) 4D — 強い非ガウス性での T10")
    print("=" * 60)

    sigma = 1.0
    n_samples = 200_000
    n_burnin = 30_000

    # 異方回転
    print("\n  [異方回転] ω = (1.0, 2.0):")
    omegas_aniso = [1.0, 2.0]

    results = []
    for barrier, a2, label in [
        (2.0, 1.0, "barrier=2, a2=1"),
        (2.0, 3.0, "barrier=2, a2=3"),
        (5.0, 1.0, "barrier=5, a2=1"),
    ]:
        V_func, grad_V_func = make_double_well_4d(barrier, a2)
        Q = make_Q_normal_form(omegas_aniso, 4)

        x, acc = mcmc_sample_general(grad_V_func, V_func, 4, sigma,
                                       n_samples, n_burnin, step_size=0.2)
        g_cF = compute_current_fisher_general(x, Q, grad_V_func, omegas_aniso)

        results.append((label, g_cF))
        print(f"    {label} (受理率={acc:.2f}):")
        print(f"      g^{{(c,F)}} = [[{g_cF[0,0]:.6f}, {g_cF[0,1]:.6f}],")
        print(f"                    [{g_cF[1,0]:.6f}, {g_cF[1,1]:.6f}]]")

    g00_vals = [r[1][0,0] for r in results]
    var_00 = max(g00_vals) - min(g00_vals)
    print(f"\n    ★ DW 異方 V 依存性: g_00 変動={var_00:.4f}")
    print(f"      → {'V依存 (T10 一致)' if var_00 > 0.01 else 'V非依存 (T10 矛盾!)'}")

    # 等方回転
    print("\n  [等方回転] ω = (1.0, 1.0):")
    omegas_iso = [1.0, 1.0]

    results_iso = []
    for barrier, a2, label in [
        (2.0, 1.0, "barrier=2, a2=1"),
        (2.0, 3.0, "barrier=2, a2=3"),
        (5.0, 1.0, "barrier=5, a2=1"),
    ]:
        V_func, grad_V_func = make_double_well_4d(barrier, a2)
        Q = make_Q_normal_form(omegas_iso, 4)

        x, acc = mcmc_sample_general(grad_V_func, V_func, 4, sigma,
                                       n_samples, n_burnin, step_size=0.2)
        g_cF = compute_current_fisher_general(x, Q, grad_V_func, omegas_iso)

        results_iso.append((label, g_cF))
        print(f"    {label} (受理率={acc:.2f}):")
        print(f"      g^{{(c,F)}} = [[{g_cF[0,0]:.6f}, {g_cF[0,1]:.6f}],")
        print(f"                    [{g_cF[1,0]:.6f}, {g_cF[1,1]:.6f}]]")

    g_scalar = [r[1][0,0] + 2*r[1][0,1] + r[1][1,1] for r in results_iso]
    var_scalar = max(g_scalar) - min(g_scalar)
    print(f"\n    ★ DW 等方スカラー g_scalar 変動 = {var_scalar:.4f}")
    print(f"      → {'V非依存 (T10 一致)' if var_scalar < 0.05 else 'V依存 (T10 矛盾!)'}")
    # 理論値: 等方スカラーとして 1/ω² = 1.0
    print(f"      理論値 1/ω² = 1.0, 数値 = {[f'{v:.4f}' for v in g_scalar]}")

    print()

def main():
    """全テストを順次実行"""
    print("高次元 c-α 接続の数値検証 (OU + 非 OU)")
    print("パラメータ: σ=1.0, Monte Carlo サンプル数 = 200K-1M")
    print()

    # OU テスト (既存)
    test_2d_recovery()
    test_4d_isotropic()
    test_4d_anisotropic()
    test_6d_anisotropic()
    test_4d_general_A()
    test_trade_off_identity()

    # 非 OU テスト (新規)
    test_non_ou_duffing_4d()
    test_non_ou_double_well_4d()

    print("=" * 60)
    print("まとめ")
    print("=" * 60)
    print("""
期待される結果:
  [OU + 非 OU 共通]
  1. 等方回転 (ω_k = ω): g^{(c,F)} は V 非依存 → dually flat
  2. 異方回転 (ω_k ≠ ω_l): g^{(c,F)} は V に依存 → dually flat 崩壊
  → T10 は一般のポテンシャルで成立

  [OU 固有]
  3. E[U²] = ρ(ρ²-2ρlnρ-1)/(ρ-1)³ の閉じた形はOU限定

  [非 OU 固有]
  4. 等方スカラー g_scalar = 1/ω² は一般 V で成立 (2D と同一)
  5. 異方回転では g^{(c,F)} の具体値は V 依存 (閉じた形なし)
""")


if __name__ == "__main__":
    main()
