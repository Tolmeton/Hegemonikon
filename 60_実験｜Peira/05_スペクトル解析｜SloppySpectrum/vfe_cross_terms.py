#!/usr/bin/env python3
"""
VFE 交差項の漸近消滅実験
=========================

仮説: POMDP VFE を反復最小化すると、パラメータ間の交差項
∂²F/∂θ_i∂θ_j (i≠j) が漸近的にゼロに近づく。

実験設計:
- 簡易 POMDP (3状態, 2観測, 2行動) を構成
- VFE = D_KL[q(s)||p(s|o,π)] - log p(o|π)
- パラメータ: μ (状態確信度), π (方策), ω (精度)
- VFE を反復最小化しながら、ヘシアンの非対角ブロックを追跡

結果:
- 交差項|∂²F/∂μ∂π|, |∂²F/∂π∂ω|, |∂²F/∂μ∂ω| の時系列
- 各対角ブロック|∂²F/∂μ²|, |∂²F/∂π²|, |∂²F/∂ω²| と比較

Level A 仮説 v2: 自己直交化 ↔ 合成性 の循環が不動点を生む
"""

import numpy as np
from scipy.special import softmax
from typing import NamedTuple


class POMDPModel(NamedTuple):
    """簡易 POMDP 生成モデル"""
    A: np.ndarray   # 観測モデル p(o|s): (n_obs, n_states)
    B: np.ndarray   # 遷移モデル p(s'|s,a): (n_states, n_states, n_actions)
    C: np.ndarray   # 選好 p(o): (n_obs,)
    D: np.ndarray   # 初期状態 p(s_0): (n_states,)


def make_pomdp(n_states: int = 3, n_obs: int = 2, n_actions: int = 2,
               seed: int = 42) -> POMDPModel:
    """ランダム POMDP の生成"""
    rng = np.random.default_rng(seed)

    # 観測モデル (列正規化)
    A_raw = rng.dirichlet(np.ones(n_obs), size=n_states).T  # (n_obs, n_states)

    # 遷移モデル (列正規化)
    B = np.zeros((n_states, n_states, n_actions))
    for a in range(n_actions):
        B[:, :, a] = rng.dirichlet(np.ones(n_states), size=n_states).T

    # 選好 (観測の望ましさ)
    C = softmax(rng.standard_normal(n_obs))

    # 初期状態
    D = rng.dirichlet(np.ones(n_states))

    return POMDPModel(A=A_raw, B=B, C=C, D=D)


def compute_vfe(model: POMDPModel, mu: np.ndarray, pi: np.ndarray,
                omega: float, obs: np.ndarray) -> float:
    """
    VFE の計算

    F = D_KL[q(s)||p(s)] - E_q[log p(o|s)] + ω_penalty

    パラメータ:
      mu: q(s) の softmax 前パラメータ (n_states,)
      pi: π(a) の softmax 前パラメータ (n_actions,)
      omega: 精度パラメータ (スカラー, sigmoid で [0,1] に写像)
    """
    eps = 1e-10

    # softmax で確率に変換
    q_s = softmax(mu)
    q_pi = softmax(pi * sigmoid(omega))  # 精度が方策のエントロピーを制御

    # p(s) = Σ_a B[:,s,a] * π(a) * D(s)  (方策依存の事前分布)
    p_s = np.zeros_like(q_s)
    for a in range(model.B.shape[2]):
        p_s += q_pi[a] * (model.B[:, :, a] @ model.D)
    p_s = p_s / (p_s.sum() + eps)

    # D_KL[q(s) || p(s)]
    kl = np.sum(q_s * (np.log(q_s + eps) - np.log(p_s + eps)))

    # -E_q[log p(o|s)]
    p_o_given_s = model.A @ q_s  # (n_obs,)
    neg_log_evidence = -np.sum(obs * np.log(p_o_given_s + eps))

    # 精度の正則化 (complexity cost)
    omega_sig = sigmoid(omega)
    omega_prior = 0.5
    omega_penalty = 0.1 * (omega_sig * np.log(omega_sig / omega_prior + eps) +
                           (1 - omega_sig) * np.log((1 - omega_sig) / (1 - omega_prior) + eps))

    return kl + neg_log_evidence + omega_penalty


def sigmoid(x: float) -> float:
    """数値安定な sigmoid"""
    if x >= 0:
        z = np.exp(-x)
        return 1 / (1 + z)
    else:
        z = np.exp(x)
        return z / (1 + z)


def compute_hessian(model: POMDPModel, theta: np.ndarray, obs: np.ndarray,
                    n_states: int, n_actions: int) -> np.ndarray:
    """
    数値ヘシアンの計算

    theta = [mu_0, ..., mu_{n_s-1}, pi_0, ..., pi_{n_a-1}, omega]
    """
    n = len(theta)
    H = np.zeros((n, n))
    eps = 1e-4

    def f(th):
        mu = th[:n_states]
        pi = th[n_states:n_states + n_actions]
        omega = th[-1]
        return compute_vfe(model, mu, pi, omega, obs)

    f0 = f(theta)

    for i in range(n):
        for j in range(i, n):
            th_pp = theta.copy()
            th_pm = theta.copy()
            th_mp = theta.copy()
            th_mm = theta.copy()

            th_pp[i] += eps; th_pp[j] += eps
            th_pm[i] += eps; th_pm[j] -= eps
            th_mp[i] -= eps; th_mp[j] += eps
            th_mm[i] -= eps; th_mm[j] -= eps

            H[i, j] = (f(th_pp) - f(th_pm) - f(th_mp) + f(th_mm)) / (4 * eps**2)
            H[j, i] = H[i, j]

    return H


def run_experiment(n_iterations: int = 200, lr: float = 0.05,
                   seed: int = 42) -> dict:
    """
    VFE 最小化の反復と交差項の追跡

    Returns:
        dict: iterations, vfe, cross_terms, diagonal_terms, off_diag_ratio
    """
    model = make_pomdp(seed=seed)
    n_states = model.A.shape[1]
    n_actions = model.B.shape[2]
    n_params = n_states + n_actions + 1  # mu + pi + omega

    # ランダムな観測
    rng = np.random.default_rng(seed + 1)
    obs = softmax(rng.standard_normal(model.A.shape[0]))

    # 初期パラメータ (ランダム)
    theta = rng.standard_normal(n_params) * 0.5

    # 追跡変数
    vfe_history = []
    cross_mu_pi = []
    cross_pi_omega = []
    cross_mu_omega = []
    diag_mu = []
    diag_pi = []
    diag_omega = []

    # ブロック境界
    mu_idx = slice(0, n_states)
    pi_idx = slice(n_states, n_states + n_actions)
    omega_idx = -1

    for it in range(n_iterations):
        # VFE 計算
        mu = theta[:n_states]
        pi = theta[n_states:n_states + n_actions]
        omega = theta[-1]
        vfe = compute_vfe(model, mu, pi, omega, obs)
        vfe_history.append(vfe)

        # ヘシアン計算 (10 反復ごと + 最初の10反復)
        if it % 10 == 0 or it < 10:
            H = compute_hessian(model, theta, obs, n_states, n_actions)

            # 交差項ブロックのフロベニウスノルム
            H_mu_pi = H[mu_idx, pi_idx]  # (n_states, n_actions)
            H_pi_omega = H[n_states:n_states + n_actions, -1:]  # (n_actions, 1)
            H_mu_omega = H[:n_states, -1:]  # (n_states, 1)

            cross_mu_pi.append(np.linalg.norm(H_mu_pi))
            cross_pi_omega.append(np.linalg.norm(H_pi_omega))
            cross_mu_omega.append(np.linalg.norm(H_mu_omega))

            # 対角ブロックのフロベニウスノルム
            diag_mu.append(np.linalg.norm(H[mu_idx, mu_idx]))
            diag_pi.append(np.linalg.norm(H[pi_idx, pi_idx]))
            diag_omega.append(abs(H[-1, -1]))

        # 勾配降下 (数値勾配)
        grad = np.zeros_like(theta)
        eps_grad = 1e-4
        for k in range(n_params):
            th_plus = theta.copy()
            th_minus = theta.copy()
            th_plus[k] += eps_grad
            th_minus[k] -= eps_grad
            mu_p, pi_p, omega_p = th_plus[:n_states], th_plus[n_states:-1], th_plus[-1]
            mu_m, pi_m, omega_m = th_minus[:n_states], th_minus[n_states:-1], th_minus[-1]
            grad[k] = (compute_vfe(model, mu_p, pi_p, omega_p, obs) -
                       compute_vfe(model, mu_m, pi_m, omega_m, obs)) / (2 * eps_grad)

        theta -= lr * grad

    # 非対角/対角比の計算
    total_cross = np.array(cross_mu_pi) + np.array(cross_pi_omega) + np.array(cross_mu_omega)
    total_diag = np.array(diag_mu) + np.array(diag_pi) + np.array(diag_omega)
    off_diag_ratio = total_cross / (total_diag + 1e-10)

    return {
        "vfe": vfe_history,
        "cross_mu_pi": cross_mu_pi,
        "cross_pi_omega": cross_pi_omega,
        "cross_mu_omega": cross_mu_omega,
        "diag_mu": diag_mu,
        "diag_pi": diag_pi,
        "diag_omega": diag_omega,
        "off_diag_ratio": off_diag_ratio,
        "n_states": n_states,
        "n_actions": n_actions,
    }


def print_results(results: dict) -> None:
    """結果の表示"""
    n = len(results["cross_mu_pi"])

    print("=" * 70)
    print("VFE 交差項の漸近消滅実験")
    print("=" * 70)
    print(f"\nPOMDP: {results['n_states']} states, {results['n_actions']} actions")
    print(f"VFE 反復: {len(results['vfe'])} iterations")
    print(f"VFE: {results['vfe'][0]:.4f} → {results['vfe'][-1]:.4f}")

    print("\n--- 交差項ブロック (||H_ij||_F for i≠j) ---")
    print(f"{'Iter':>4} | {'μ-π':>10} | {'π-ω':>10} | {'μ-ω':>10} | {'Off/Diag':>10}")
    print("-" * 55)

    for k in range(n):
        it = k * 10 if k >= 10 else k  # 最初の10は1ステップごと
        print(f"{it:4d} | {results['cross_mu_pi'][k]:10.6f} | "
              f"{results['cross_pi_omega'][k]:10.6f} | "
              f"{results['cross_mu_omega'][k]:10.6f} | "
              f"{results['off_diag_ratio'][k]:10.6f}")

    # 初期 vs 最終の比較
    print("\n--- 初期 vs 最終 ---")
    for name, vals in [("μ-π", results["cross_mu_pi"]),
                       ("π-ω", results["cross_pi_omega"]),
                       ("μ-ω", results["cross_mu_omega"])]:
        initial = vals[0] if vals[0] > 1e-10 else 1e-10
        ratio = vals[-1] / initial
        print(f"  {name}: {vals[0]:.6f} → {vals[-1]:.6f} (×{ratio:.4f})")

    # 対角項との比較
    print("\n--- 対角ブロック (||H_ii||_F) ---")
    for name, vals in [("μ-μ", results["diag_mu"]),
                       ("π-π", results["diag_pi"]),
                       ("ω-ω", results["diag_omega"])]:
        print(f"  {name}: {vals[0]:.6f} → {vals[-1]:.6f}")

    # 判定
    ratio_initial = results["off_diag_ratio"][0]
    ratio_final = results["off_diag_ratio"][-1]
    print(f"\n--- 非対角/対角 比 ---")
    print(f"  初期: {ratio_initial:.6f}")
    print(f"  最終: {ratio_final:.6f}")

    if ratio_final < ratio_initial * 0.5:
        print(f"\n  ✅ 仮説支持: 交差項は対角項に対して相対的に減少 (×{ratio_final/ratio_initial:.4f})")
    elif ratio_final < ratio_initial:
        print(f"\n  🟡 弱い支持: 微減 (×{ratio_final/ratio_initial:.4f})")
    else:
        print(f"\n  ❌ 仮説棄却: 交差項は減少しなかった (×{ratio_final/ratio_initial:.4f})")

    # 複数シードで再現性確認
    print("\n" + "=" * 70)
    print("複数シードでの再現性チェック")
    print("=" * 70)


def run_multi_seed(n_seeds: int = 5) -> None:
    """複数シードで実験を実行し、ロバスト性を確認"""
    ratios = []
    for seed in range(n_seeds):
        results = run_experiment(seed=seed * 7 + 1)
        r_init = results["off_diag_ratio"][0]
        r_final = results["off_diag_ratio"][-1]
        change = r_final / r_init if r_init > 1e-10 else float('inf')
        ratios.append(change)
        verdict = "✅" if change < 0.5 else ("🟡" if change < 1.0 else "❌")
        print(f"  Seed {seed}: off/diag ratio {r_init:.4f} → {r_final:.4f} (×{change:.4f}) {verdict}")

    mean_change = np.mean(ratios)
    print(f"\n  平均変化率: ×{mean_change:.4f}")
    if mean_change < 0.5:
        print(f"  ✅ ロバスト: 複数シードで交差項の漸近消滅を確認")
    elif mean_change < 1.0:
        print(f"  🟡 弱いロバスト: 平均的には減少する傾向")
    else:
        print(f"  ❌ 仮説不支持: ロバスト性なし")


if __name__ == "__main__":
    # メイン実験
    results = run_experiment()
    print_results(results)

    # 複数シード
    run_multi_seed()
