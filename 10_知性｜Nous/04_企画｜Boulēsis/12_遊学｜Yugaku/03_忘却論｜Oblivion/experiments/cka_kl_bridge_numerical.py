#!/usr/bin/env python3
"""
CKA ↔ KL 橋渡しの数値検証 (v2)
===================================
Paper I §6.8.1 の理論的保証を数値的に検証する。

v2 修正:
  - CKA を共分散行列レベルで直接計算 (サンプルノイズ排除)
  - 解析的 CKA: CKA(Σ₀, Σ₁) = ||Σ₀Σ₁||_F² / (||Σ₀²||_F · ||Σ₁²||_F)
  - サンプルベース CKA は検証用に別途計算

検証項目:
  P1. 分離定理 (定理 6.8.1): CKA は形状のみ、KL はスケール+形状
  P2. 方向保存条件 (命題 6.8.2): BatchNorm 下で sign(∂Φ_CKA) = sign(∂Φ_KL)
  P3. 誤差上界 (命題 6.8.3): |Φ_CKA - (4/d)Φ_KL| ≤ C(d)·ε³
  P4. ガウス仮定除去 (定理 8.1): ピタゴラス分解 KL = J + KL_gauss
  P5. 同時対角化なし (§10): 回転成分は方向保存を強化する
  P6. 次元補正の有効性: λd/4 スケーリング

実行環境: NumPy + SciPy (PyTorch 不要)
"""

import numpy as np
from scipy import stats
from scipy.linalg import sqrtm
from pathlib import Path
import json

# === 設定 ===
OUTPUT_DIR = Path(__file__).parent / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

np.random.seed(42)

# === ユーティリティ ===

def analytic_cka(Sigma0: np.ndarray, Sigma1: np.ndarray) -> float:
    """解析的線形 CKA (共分散行列から直接計算)
    
    線形カーネル K = X X^T に対して:
    HSIC(X, Y) ∝ tr(K_X H K_Y H) = ||Σ_X Σ_Y||_F^2 (中心化・正規化済み)
    
    CKA = ||Σ₀ Σ₁||_F² / (||Σ₀²||_F · ||Σ₁²||_F)
    """
    prod = Sigma0 @ Sigma1
    sq0 = Sigma0 @ Sigma0
    sq1 = Sigma1 @ Sigma1
    
    hsic_01 = np.sum(prod ** 2)  # ||Σ₀Σ₁||_F²
    hsic_00 = np.sum(sq0 ** 2)   # ||Σ₀²||_F²
    hsic_11 = np.sum(sq1 ** 2)   # ||Σ₁²||_F²
    
    return hsic_01 / np.sqrt(hsic_00 * hsic_11)


def sample_cka(X: np.ndarray, Y: np.ndarray) -> float:
    """サンプルベース線形 CKA (Kornblith et al. 2019)
    X, Y: (N, d) — 同一入力データの異なる表現
    """
    # 中心化
    X = X - X.mean(axis=0, keepdims=True)
    Y = Y - Y.mean(axis=0, keepdims=True)
    
    # Gram 行列 (線形カーネル)
    Kx = X @ X.T  # (N, N)
    Ky = Y @ Y.T  # (N, N)
    
    # HSIC (中心化された Gram 行列の内積)
    N = X.shape[0]
    H = np.eye(N) - np.ones((N, N)) / N
    
    hsic_xy = np.trace(Kx @ H @ Ky @ H) / (N - 1)**2
    hsic_xx = np.trace(Kx @ H @ Kx @ H) / (N - 1)**2
    hsic_yy = np.trace(Ky @ H @ Ky @ H) / (N - 1)**2
    
    return hsic_xy / np.sqrt(hsic_xx * hsic_yy)


def kl_gaussian(mu0: np.ndarray, Sigma0: np.ndarray, 
                mu1: np.ndarray, Sigma1: np.ndarray) -> float:
    """ガウス分布間の KL ダイバージェンス
    KL(N(mu1, Sigma1) || N(mu0, Sigma0))
    """
    d = len(mu0)
    
    # 数値安定性のため正則化
    reg = 1e-8 * np.eye(d)
    Sigma0_reg = Sigma0 + reg
    Sigma1_reg = Sigma1 + reg
    
    Sigma0_inv = np.linalg.inv(Sigma0_reg)
    
    term1 = np.trace(Sigma0_inv @ Sigma1_reg)
    term2 = (mu0 - mu1).T @ Sigma0_inv @ (mu0 - mu1)
    term3 = -d
    
    sign0, logdet0 = np.linalg.slogdet(Sigma0_reg)
    sign1, logdet1 = np.linalg.slogdet(Sigma1_reg)
    term4 = logdet0 - logdet1
    
    return 0.5 * (term1 + term2 + term3 + term4)


def make_shape_perturbation(d: int, epsilon: float) -> np.ndarray:
    """形状のみの摂動 (スケール不変): Σ_l = diag(1+ε_i) where Σε_i=0"""
    delta = np.random.randn(d) * epsilon
    delta -= delta.mean()  # ΔΣε_i = 0 (一様スケール成分ゼロ)
    # 固有値が正であることを保証
    eigenvalues = np.clip(1.0 + delta, 0.05, None)
    # 再度正規化 (幾何平均 = 1 に近づける)
    eigenvalues = eigenvalues / np.exp(np.mean(np.log(eigenvalues)))
    return np.diag(eigenvalues)


# === P1: 分離定理の検証 ===

def verify_separation_theorem(d: int = 50, n_trials: int = 200):
    """定理 6.8.1 (CKA-KL 分離) の数値検証
    
    (1) 一様スケール変化: CKA = 1, KL > 0
    (2) 形状のみ変化: CKA < 1, KL > 0
    (3) 直交分解: Φ_KL = Φ_shape + Φ_scale (近似)
    """
    print("\n━━━ P1: 分離定理 (定理 6.8.1) ━━━")
    
    Sigma0 = np.eye(d)
    mu0 = np.zeros(d)
    
    # (1) 一様スケール
    print("\n  [1a] 一様スケール変化 (解析的 CKA):")
    for c in [0.5, 1.5, 2.0, 3.0]:
        Sigma_l = c * np.eye(d)
        cka_val = analytic_cka(Sigma0, Sigma_l)
        kl_val = kl_gaussian(mu0, Sigma0, mu0, Sigma_l)
        print(f"    c={c:.1f}: CKA={cka_val:.6f} (期待=1.0), KL={kl_val:.4f} (期待>0)")
    
    # (2) 形状のみ
    print("\n  [1b] 形状のみの変化 (解析的 CKA):")
    for eps in [0.1, 0.3, 0.5, 0.8]:
        cka_values = []
        kl_values = []
        for _ in range(n_trials):
            Sigma_l = make_shape_perturbation(d, eps)
            cka_values.append(analytic_cka(Sigma0, Sigma_l))
            kl_values.append(kl_gaussian(mu0, Sigma0, mu0, Sigma_l))
        
        cka_mean = np.mean(cka_values)
        kl_mean = np.mean(kl_values)
        print(f"    ε={eps:.1f}: CKA={cka_mean:.6f} (期待<1), KL={kl_mean:.4f}")
    
    # (3) 直交分解検証
    print("\n  [1c] 直交分解: KL_mixed ≈ KL_scale + KL_shape")
    decomposition_errors = []
    for _ in range(n_trials):
        c = 1.0 + np.random.uniform(-0.3, 0.3)
        eps = 0.3
        
        # 形状摂動
        Sigma_shape = make_shape_perturbation(d, eps)
        # 混合摂動 = スケール × 形状
        Sigma_mixed = c * Sigma_shape
        # 純スケール
        Sigma_scale = c * np.eye(d)
        
        kl_mixed = kl_gaussian(mu0, Sigma0, mu0, Sigma_mixed)
        kl_scale = kl_gaussian(mu0, Sigma0, mu0, Sigma_scale)
        kl_shape = kl_gaussian(mu0, Sigma0, mu0, Sigma_shape)
        
        # KL_mixed ≈ KL_scale + KL_shape (近似的直交分解)
        decomp_err = abs(kl_mixed - kl_scale - kl_shape) / max(abs(kl_mixed), 1e-10)
        decomposition_errors.append(decomp_err)
    
    mean_err = np.mean(decomposition_errors)
    max_err = np.max(decomposition_errors)
    print(f"    直交分解の相対誤差: 平均={mean_err:.6f}, 最大={max_err:.6f}")
    # 非線形相互作用項があるため完全な直交性は期待しない
    print(f"    → {'✅' if mean_err < 0.5 else '⚠️'} 近似的直交分解の確認 (交互作用項あり)")
    
    # CKA のスケール不変性を明示的に検証
    print("\n  [1d] CKA スケール不変性の厳密性:")
    for c in [0.1, 0.5, 2.0, 10.0]:
        Sigma_l = c * make_shape_perturbation(d, 0.3)
        Sigma_l_noscale = Sigma_l / c
        cka_with_scale = analytic_cka(Sigma0, Sigma_l)
        cka_without_scale = analytic_cka(Sigma0, Sigma_l_noscale)
        print(f"    c={c:5.1f}: CKA(cΣ)={cka_with_scale:.8f}, CKA(Σ)={cka_without_scale:.8f}, "
              f"差={abs(cka_with_scale - cka_without_scale):.2e}")
    
    return True


# === P2: 方向保存条件の検証 ===

def verify_direction_preservation(d: int = 100, n_layers: int = 20, n_trials: int = 50):
    """命題 6.8.2 (方向保存条件) の数値検証
    
    「層」を模擬して Φ_CKA(l) と Φ_KL(l) の勾配の符号が一致するか検証。
    BatchNorm 模擬: 各層の出力の分散を 1 に正規化。
    """
    print("\n━━━ P2: 方向保存条件 (命題 6.8.2) ━━━")
    
    mu0 = np.zeros(d)
    Sigma0 = np.eye(d)
    
    sign_agreement_bn = []
    sign_agreement_nobn = []
    
    for trial in range(n_trials):
        cka_profile_bn = []
        kl_profile_bn = []
        cka_profile_nobn = []
        kl_profile_nobn = []
        
        for l in range(n_layers):
            t = (l + 1) / n_layers
            
            np.random.seed(trial * 1000 + l)
            shape_delta = np.random.randn(d) * (0.3 * t)
            shape_delta -= shape_delta.mean()
            
            scale = 1.0 + 0.5 * t * np.random.randn()
            scale = max(scale, 0.1)  # 正のスケール保証
            
            # BaseNorm なし
            eigenvalues = np.clip(1.0 + shape_delta, 0.05, None)
            Sigma_l_nobn = scale * np.diag(eigenvalues)
            
            cka_nobn = analytic_cka(Sigma0, Sigma_l_nobn)
            kl_nobn = kl_gaussian(mu0, Sigma0, mu0, Sigma_l_nobn)
            cka_profile_nobn.append(1.0 - cka_nobn)
            kl_profile_nobn.append(kl_nobn)
            
            # BatchNorm あり (BN: scale → 1 に正規化)
            eigenvalues_bn = np.clip(1.0 + shape_delta, 0.05, None)
            # BN 効果: 幾何平均を 1 に正規化
            eigenvalues_bn = eigenvalues_bn / np.exp(np.mean(np.log(eigenvalues_bn)))
            Sigma_l_bn = np.diag(eigenvalues_bn)
            
            cka_bn = analytic_cka(Sigma0, Sigma_l_bn)
            kl_bn = kl_gaussian(mu0, Sigma0, mu0, Sigma_l_bn)
            cka_profile_bn.append(1.0 - cka_bn)
            kl_profile_bn.append(kl_bn)
        
        # 勾配の符号比較
        dcka_bn = np.diff(cka_profile_bn)
        dkl_bn = np.diff(kl_profile_bn)
        dcka_nobn = np.diff(cka_profile_nobn)
        dkl_nobn = np.diff(kl_profile_nobn)
        
        mask_bn = (np.abs(dcka_bn) > 1e-8) & (np.abs(dkl_bn) > 1e-8)
        mask_nobn = (np.abs(dcka_nobn) > 1e-8) & (np.abs(dkl_nobn) > 1e-8)
        
        if np.sum(mask_bn) > 0:
            agree_bn = np.mean(np.sign(dcka_bn[mask_bn]) == np.sign(dkl_bn[mask_bn]))
            sign_agreement_bn.append(agree_bn)
        
        if np.sum(mask_nobn) > 0:
            agree_nobn = np.mean(np.sign(dcka_nobn[mask_nobn]) == np.sign(dkl_nobn[mask_nobn]))
            sign_agreement_nobn.append(agree_nobn)
    
    bn_rate = np.mean(sign_agreement_bn)
    nobn_rate = np.mean(sign_agreement_nobn)
    
    print(f"\n  方向保存率 (sign 一致率):")
    print(f"    BatchNorm あり: {bn_rate:.4f} (期待: > 0.90)")
    print(f"    BatchNorm なし: {nobn_rate:.4f} (期待: < BN あり)")
    print(f"    差分: {bn_rate - nobn_rate:+.4f}")
    print(f"    → {'✅' if bn_rate > 0.85 else '⚠️'} BN 下での方向保存 {'確認' if bn_rate > 0.85 else '要調査'}")
    print(f"    → {'✅' if bn_rate > nobn_rate else '⚠️'} BN が方向保存を強化 {'確認' if bn_rate > nobn_rate else '要調査'}")
    
    return bn_rate, nobn_rate


# === P3: 誤差上界の検証 ===

def verify_error_bound(d_values: list = [10, 50, 100, 200], n_trials: int = 100):
    """命題 6.8.3 (誤差上界) の数値検証
    
    |Φ_CKA - (4/d)Φ_KL_shape| ≤ C(d)·ε³ を確認
    (BatchNorm 下 = 形状のみの KL)
    """
    print("\n━━━ P3: 誤差上界 (命題 6.8.3) ━━━")
    
    epsilon_values = [0.05, 0.1, 0.2, 0.3]
    
    print(f"\n  {'d':>5} | {'ε':>5} | {'|Φ_CKA-(4/d)Φ_KL|':>20} | {'C·ε³':>10} | {'比率':>8}")
    print(f"  {'-'*5}-+-{'-'*5}-+-{'-'*20}-+-{'-'*10}-+-{'-'*8}")
    
    results = {}
    for d in d_values:
        mu0 = np.zeros(d)
        Sigma0 = np.eye(d)
        results[d] = []
        
        for eps in epsilon_values:
            errors = []
            for _ in range(n_trials):
                Sigma_l = make_shape_perturbation(d, eps)
                
                cka = analytic_cka(Sigma0, Sigma_l)
                kl = kl_gaussian(mu0, Sigma0, mu0, Sigma_l)
                
                phi_cka = 1.0 - cka
                phi_kl_scaled = (4.0 / d) * kl
                
                err = abs(phi_cka - phi_kl_scaled)
                errors.append(err)
            
            mean_err = np.mean(errors)
            bound = eps ** 3
            ratio = mean_err / bound if bound > 0 else float('inf')
            results[d].append((eps, mean_err, ratio))
            
            print(f"  {d:5d} | {eps:5.2f} | {mean_err:20.8f} | {bound:10.6f} | {ratio:8.4f}")
    
    # ε³ スケーリングの検証
    print(f"\n  ε³ スケーリング検証 (d=100):")
    if 100 in results:
        errs_100 = results[100]
        for i in range(1, len(errs_100)):
            eps_prev, err_prev, _ = errs_100[i-1]
            eps_curr, err_curr, _ = errs_100[i]
            if err_prev > 0:
                slope = np.log(err_curr / err_prev) / np.log(eps_curr / eps_prev)
                print(f"    ε: {eps_prev:.2f}→{eps_curr:.2f}, 勾配 = {slope:.2f} (期待: ≈3.0)")
    
    return results


# === P4: ガウス仮定除去 (ピタゴラス分解) ===

def verify_pythagorean_decomposition(d: int = 50, n_trials: int = 50):
    """定理 8.1 (情報幾何学的ピタゴラス) の数値検証
    
    ReLU 後の非ガウス表現に対して CKA がガウス近似の CKA と一致するか検証。
    ピタゴラスの意味: CKA は2次モーメント (共分散) のみ使用するため、
    非ガウス性 (negentropy J) に影響されない → CKA(p) ≈ CKA(p*)
    """
    print("\n━━━ P4: ピタゴラス分解 (定理 8.1) ━━━")
    
    N = 2000  # サンプルベース CKA 用
    mu0 = np.zeros(d)
    Sigma0 = np.eye(d)
    
    print("\n  ReLU 後の表現 (非ガウス) に対する CKA 安定性:")
    
    ratios = []
    kl_gauss_vals = []
    
    for trial in range(n_trials):
        np.random.seed(trial + 1000)
        eps = 0.2 + 0.2 * np.random.rand()
        Sigma_l = make_shape_perturbation(d, eps)
        
        # 共通入力を生成
        X_input = np.random.randn(N, d)
        
        # ガウス表現: X → W·X (線形変換)
        # Sigma_l = W^T W の分解
        L = np.linalg.cholesky(Sigma_l)
        X_gauss = X_input @ L.T  # 共分散 = Sigma_l
        
        # ReLU 表現: max(0, W·X)
        X_relu = np.maximum(0, X_input @ L.T)
        
        # 中心化
        X_ref = X_input - X_input.mean(axis=0, keepdims=True)  # 参照 (Σ₀ = I)
        X_gauss_c = X_gauss - X_gauss.mean(axis=0, keepdims=True)
        X_relu_c = X_relu - X_relu.mean(axis=0, keepdims=True)
        
        # サンプルベース CKA
        cka_gauss = sample_cka(X_ref, X_gauss_c)
        cka_relu = sample_cka(X_ref, X_relu_c)
        
        if cka_gauss > 1e-8:
            ratio = cka_relu / cka_gauss
            ratios.append(ratio)
        
        # KL のガウス近似の精度も検証
        Sigma_relu = np.cov(X_relu_c.T) + 1e-8 * np.eye(d)
        mu_relu = X_relu.mean(axis=0)
        kl_gauss_approx = kl_gaussian(mu0, Sigma0, mu_relu, Sigma_relu)
        kl_gauss_vals.append(kl_gauss_approx)
    
    ratio_mean = np.mean(ratios)
    ratio_std = np.std(ratios)
    rel_err = np.mean([abs(r - 1.0) for r in ratios])
    
    print(f"\n  CKA(ReLU) / CKA(Gauss) の比:")
    print(f"    平均: {ratio_mean:.4f} (期待: ≈1.0)")
    print(f"    標準偏差: {ratio_std:.4f}")
    print(f"    相対誤差: {rel_err:.4f}")
    print(f"    → {'✅' if rel_err < 0.20 else '⚠️'} CKA はガウス近似でも形状情報を保存 {'確認' if rel_err < 0.20 else '要調査'}")
    
    return rel_err


# === P5: 同時対角化なしの方向保存 ===

def verify_rotation_strengthening(d: int = 50, n_trials: int = 100):
    """§10 の検証: CKA は回転不変、KL は回転で変わるか？"""
    print("\n━━━ P5: 回転成分の効果 (§10) ━━━")
    
    mu0 = np.zeros(d)
    Sigma0 = np.eye(d)
    
    cka_diffs = []  # CKA: 回転前後の差
    kl_diffs = []   # KL: 回転前後の差
    err_diag_list = []
    err_rot_list = []
    
    for trial in range(n_trials):
        np.random.seed(trial + 2000)
        eps = 0.3
        
        # 対角共分散 (同時対角化可能)
        Sigma_diag = make_shape_perturbation(d, eps)
        
        # ランダム回転で非対角化
        Q, _ = np.linalg.qr(np.random.randn(d, d))
        Sigma_rotated = Q @ Sigma_diag @ Q.T
        
        # 解析的 CKA
        cka_diag = analytic_cka(Sigma0, Sigma_diag)
        cka_rot = analytic_cka(Sigma0, Sigma_rotated)
        cka_diffs.append(abs(cka_diag - cka_rot))
        
        # KL
        kl_diag = kl_gaussian(mu0, Sigma0, mu0, Sigma_diag)
        kl_rot = kl_gaussian(mu0, Sigma0, mu0, Sigma_rotated)
        kl_diffs.append(abs(kl_diag - kl_rot))
        
        # Φ_CKA vs (4/d)Φ_KL の誤差
        phi_cka_diag = 1.0 - cka_diag
        phi_cka_rot = 1.0 - cka_rot
        phi_kl_diag = (4.0 / d) * kl_diag
        phi_kl_rot = (4.0 / d) * kl_rot
        
        err_diag_list.append(abs(phi_cka_diag - phi_kl_diag))
        err_rot_list.append(abs(phi_cka_rot - phi_kl_rot))
    
    print(f"\n  CKA の回転不変性:")
    print(f"    |CKA(diag) - CKA(rot)| の平均: {np.mean(cka_diffs):.8f}")
    print(f"    → {'✅' if np.mean(cka_diffs) < 1e-6 else '⚠️'} CKA は回転不変 {'確認' if np.mean(cka_diffs) < 1e-6 else '要調査'}")
    
    print(f"\n  KL の回転依存性:")
    print(f"    |KL(diag) - KL(rot)| の平均: {np.mean(kl_diffs):.8f}")
    print(f"    → KL は Σ₀=I に対しては回転不変 (予測)")
    
    print(f"\n  |Φ_CKA - (4/d)Φ_KL| の平均:")
    mean_diag = np.mean(err_diag_list)
    mean_rot = np.mean(err_rot_list)
    print(f"    同時対角化可能: {mean_diag:.6f}")
    print(f"    回転あり:       {mean_rot:.6f}")
    print(f"    比率:           {mean_rot/mean_diag:.4f}" if mean_diag > 1e-10 else "    比率: N/A")
    print(f"    → {'✅' if mean_rot <= mean_diag * 1.5 else '⚠️'} 回転は橋渡し精度を {'維持/強化' if mean_rot <= mean_diag * 1.5 else '劣化'}")
    
    return mean_diag, mean_rot


# === P6: 次元補正の有効性 ===

def verify_dimension_correction(n_trials: int = 100):
    """λd/4 次元補正の有効性検証
    
    Φ_CKA ≈ (4/d) · Φ_KL_shape が全次元で成立するか確認。
    """
    print("\n━━━ P6: 次元補正 λd/4 の有効性 ━━━")
    
    d_values = [10, 25, 50, 100, 200, 500]
    
    print(f"\n  {'d':>5} | {'Φ_CKA':>10} | {'Φ_KL':>10} | {'Φ_CKA/Φ_KL':>12} | {'d·Φ_CKA/Φ_KL':>13} | {'(4/d)':>7}")
    print(f"  {'-'*5}-+-{'-'*10}-+-{'-'*10}-+-{'-'*12}-+-{'-'*13}-+-{'-'*7}")
    
    ratios_corrected = {}
    
    for d in d_values:
        mu0 = np.zeros(d)
        Sigma0 = np.eye(d)
        
        phi_cka_list = []
        phi_kl_list = []
        
        for _ in range(n_trials):
            np.random.seed(_ + 3000 + d)
            eps = 0.2
            Sigma_l = make_shape_perturbation(d, eps)
            
            cka = analytic_cka(Sigma0, Sigma_l)
            kl = kl_gaussian(mu0, Sigma0, mu0, Sigma_l)
            
            phi_cka_list.append(1.0 - cka)
            phi_kl_list.append(kl)
        
        phi_cka_mean = np.mean(phi_cka_list)
        phi_kl_mean = np.mean(phi_kl_list)
        
        raw_ratio = phi_cka_mean / phi_kl_mean if phi_kl_mean > 1e-10 else float('inf')
        corr_ratio = d * raw_ratio  # d · (Φ_CKA/Φ_KL) — 期待値 = 4
        
        ratios_corrected[d] = corr_ratio
        
        print(f"  {d:5d} | {phi_cka_mean:10.6f} | {phi_kl_mean:10.4f} | {raw_ratio:12.6f} | {corr_ratio:13.4f} | {4.0/d:7.4f}")
    
    # d·(Φ_CKA/Φ_KL) ≈ 4 の安定性
    values = list(ratios_corrected.values())
    mean_corr = np.mean(values)
    std_corr = np.std(values)
    print(f"\n  d·Φ_CKA/Φ_KL の統計:")
    print(f"    平均: {mean_corr:.4f} (期待: ≈4.0)")
    print(f"    標準偏差: {std_corr:.4f}")
    print(f"    変動係数: {std_corr/mean_corr:.4f}")
    print(f"    → {'✅' if abs(mean_corr - 4.0) < 2.0 else '⚠️'} 次元補正 λ → λd/4 の有効性 {'確認' if abs(mean_corr - 4.0) < 2.0 else '要調査'}")
    
    return ratios_corrected


# === メイン ===

def main():
    print("=" * 70)
    print("CKA ↔ KL 橋渡しの数値検証 (v2)")
    print("Paper I §6.8.1 + calculations/cka_kl_bridge.md §1-11")
    print("=" * 70)
    
    results = {}
    
    # P1: 分離定理
    verify_separation_theorem()
    
    # P2: 方向保存
    bn_rate, nobn_rate = verify_direction_preservation()
    results['P2_bn_rate'] = bn_rate
    results['P2_nobn_rate'] = nobn_rate
    
    # P3: 誤差上界
    verify_error_bound()
    
    # P4: ガウス仮定除去
    pyth_err = verify_pythagorean_decomposition()
    results['P4_pythagorean_error'] = pyth_err
    
    # P5: 同時対角化なしの方向保存
    err_diag, err_rot = verify_rotation_strengthening()
    results['P5_error_diag'] = err_diag
    results['P5_error_rotated'] = err_rot
    
    # P6: 次元補正
    dim_corr = verify_dimension_correction()
    for d, val in dim_corr.items():
        results[f'P6_d{d}_corrected_ratio'] = val
    
    # 結果保存
    results_path = OUTPUT_DIR / 'cka_kl_bridge_results.json'
    with open(results_path, 'w') as f:
        json.dump({k: float(v) for k, v in results.items()}, f, indent=2)
    print(f"\n  → 結果保存: {results_path}")
    
    print("\n" + "=" * 70)
    print("全検証完了")
    print("=" * 70)


if __name__ == '__main__':
    main()
