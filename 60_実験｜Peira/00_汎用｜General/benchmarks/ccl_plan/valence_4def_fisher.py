"""
PURPOSE: 4定義比較 Valence Fisher 実験
    Seth (2013), Hesp (2021), Pattisapu (2024), Joffily (2013)
    各定義の半直積作用 φ の結合強度を Fisher 情報行列で定量比較
"""
import numpy as np
import scipy.stats
from scipy.special import softmax


def numeric_hessian(func, params, eps=1e-4):
    """Fisher 情報行列の数値近似 (中心差分 Hessian)"""
    n = len(params)
    H = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            p_pp = params.copy(); p_pp[i] += eps; p_pp[j] += eps
            p_pm = params.copy(); p_pm[i] += eps; p_pm[j] -= eps
            p_mp = params.copy(); p_mp[i] -= eps; p_mp[j] += eps
            p_mm = params.copy(); p_mm[i] -= eps; p_mm[j] -= eps
            H[i, j] = (func(*p_pp) - func(*p_pm) - func(*p_mp) + func(*p_mm)) / (4 * eps**2)
    return H


def run_experiment(n_states=3, n_obs=2, n_actions=2, seed=42):
    """4定義比較 Fisher 実験"""
    np.random.seed(seed)

    # POMDP パラメータ
    A = np.random.dirichlet(np.ones(n_obs), size=(n_states,)).T
    B = np.random.dirichlet(np.ones(n_states), size=(n_actions, n_states)).transpose(0, 2, 1)
    C = np.array([-2.0, 1.0])

    s = np.random.dirichlet(np.ones(n_states))
    pi = np.random.dirichlet(np.ones(n_actions))
    omega = 1.0
    v = 0.5  # 非ゼロで測定 (v=0 だと勾配がゼロになり得る)

    # ユーティリティ関数
    def calc_efe_per_action(s_input, A_mat, B_mat, C_vec, n_act):
        G = np.zeros(n_act)
        for a in range(n_act):
            next_s = B_mat[a] @ s_input
            pred_obs_a = A_mat @ next_s
            # Pragmatic: risk (観測と C の KL)
            risk = np.sum(pred_obs_a * (np.log(pred_obs_a + 1e-12) - np.log(softmax(C_vec) + 1e-12)))
            # Epistemic: ambiguity
            ambig = -np.sum(next_s * np.sum(A_mat * np.log(A_mat + 1e-12), axis=0))
            G[a] = risk + ambig
        return G

    def base_vfe(s_arr, pi_arr, om, A_mat, B_mat, C_vec, n_act):
        """Base VFE (Valence なし)"""
        pred_obs = A_mat @ s_arr
        ambiguity = -np.sum(s_arr * np.sum(A_mat * np.log(A_mat + 1e-12), axis=0))
        risk = np.sum(pred_obs * (np.log(pred_obs + 1e-12) - np.log(softmax(C_vec) + 1e-12)))
        F_state = ambiguity + risk
        G = calc_efe_per_action(s_arr, A_mat, B_mat, C_vec, n_act)
        F_pi = np.sum(pi_arr * (np.log(pi_arr + 1e-12) + om * G))
        return F_state, F_pi, G

    # ===== 定義1: Seth (2013) — ω_eff = ω·exp(v) =====
    def vfe_seth(s0, s1, pi0, om, val):
        s_arr = np.array([s0, s1, 1 - s0 - s1])
        pi_arr = np.array([pi0, 1 - pi0])
        F_state, _, G = base_vfe(s_arr, pi_arr, om, A, B, C, n_actions)
        omega_eff = om * np.exp(val)
        F_pi = np.sum(pi_arr * (np.log(pi_arr + 1e-12) + omega_eff * G))
        F_v = 0.5 * val**2
        return F_state + F_pi + F_v

    # ===== 定義2: Hesp (2021) — v = log(π_precision) =====
    def vfe_hesp(s0, s1, pi0, om, val):
        s_arr = np.array([s0, s1, 1 - s0 - s1])
        pi_arr = np.array([pi0, 1 - pi0])
        F_state, _, G = base_vfe(s_arr, pi_arr, om, A, B, C, n_actions)
        # Hesp: v は方策の精度 (confidence) の対数
        # pi の精度 = exp(v), pi_sharpened = softmax(v * log(pi))
        # 実装: pi_precision = exp(v)、方策の温度を v が制御
        pi_logits = np.log(pi_arr + 1e-12)
        pi_sharp = softmax(np.exp(val) * pi_logits)
        F_pi = np.sum(pi_sharp * (np.log(pi_sharp + 1e-12) + om * G))
        F_v = 0.5 * val**2  # v の事前
        return F_state + F_pi + F_v

    # ===== 定義3: Pattisapu (2024) — v = C·E[o] - utility =====
    def vfe_pattisapu(s0, s1, pi0, om, val):
        s_arr = np.array([s0, s1, 1 - s0 - s1])
        pi_arr = np.array([pi0, 1 - pi0])
        F_state, F_pi, _ = base_vfe(s_arr, pi_arr, om, A, B, C, n_actions)
        # Pattisapu: v は期待観測と C の内積
        pred_obs = A @ s_arr
        expected_utility = np.dot(softmax(C), pred_obs)
        # v は期待効用からの偏差
        F_v_patt = 0.5 * (val - expected_utility)**2
        return F_state + F_pi + F_v_patt

    # ===== 定義4: Joffily (2013) — v = -dF/dt =====
    def vfe_joffily(s0, s1, pi0, om, val):
        s_arr = np.array([s0, s1, 1 - s0 - s1])
        pi_arr = np.array([pi0, 1 - pi0])
        F_state, F_pi, G = base_vfe(s_arr, pi_arr, om, A, B, C, n_actions)
        F_base = F_state + F_pi
        # Joffily: v = -dF/dt
        # v は VFE の時間変化率。正の v = F が減少している = 良い方向
        # F_total = F_base + 0.5 * (v + dF_approx)^2
        # dF_approx: 期待される VFE 変化 (行動の結果)
        dF_approx = np.sum(pi_arr * G) - F_state  # 次ステップの VFE - 現在
        F_v_joff = 0.5 * (val + dF_approx)**2
        return F_base + F_v_joff

    # 全4定義で Fisher 行列を計算
    definitions = {
        "Seth (2013)": vfe_seth,
        "Hesp (2021)": vfe_hesp,
        "Pattisapu (2024)": vfe_pattisapu,
        "Joffily (2013)": vfe_joffily,
    }

    p0 = [s[0], s[1], pi[0], omega, v]
    param_names = ["s0", "s1", "pi0", "omega", "v"]

    print("=" * 70)
    print("4-Definition Valence Fisher Experiment")
    print("=" * 70)
    print(f"Parameters: v={v}, ω={omega}")
    print(f"State belief: s={s.round(4)}")
    print(f"Policy: π={pi.round(4)}")
    print("-" * 70)

    results = {}
    for name, func in definitions.items():
        H = numeric_hessian(func, p0.copy())
        v_idx = 4

        cross_terms = {
            "s0": H[v_idx, 0],
            "s1": H[v_idx, 1],
            "pi0": H[v_idx, 2],
            "omega": H[v_idx, 3],
        }

        off_diag_sum = np.sum(np.abs(H[v_idx, :4]))
        diag_v = np.abs(H[v_idx, v_idx])
        ratio = off_diag_sum / diag_v if diag_v > 1e-12 else float('inf')

        # 座標別結合
        s_coupling = np.sum(np.abs([H[v_idx, 0], H[v_idx, 1]]))
        pi_coupling = np.abs(H[v_idx, 2])
        omega_coupling = np.abs(H[v_idx, 3])

        results[name] = {
            "ratio": ratio,
            "cross_terms": cross_terms,
            "diag": diag_v,
            "off_diag": off_diag_sum,
            "s_coupling": s_coupling,
            "pi_coupling": pi_coupling,
            "omega_coupling": omega_coupling,
        }

        print(f"\n### {name}")
        print(f"  Cross-terms with v:")
        for k, ct_val in cross_terms.items():
            print(f"    d²F/(dv d{k}) = {ct_val:+.6f}")
        print(f"  Off-diagonal sum: {off_diag_sum:.6f}")
        print(f"  Diagonal (v,v):   {diag_v:.6f}")
        print(f"  Coupling ratio:   {ratio:.4f}")
        print(f"  State coupling:   {s_coupling:.4f}")
        print(f"  Policy coupling:  {pi_coupling:.4f}")
        print(f"  ω coupling:       {omega_coupling:.4f}")

    # Summary table
    print("\n" + "=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    print(f"{'Definition':<22} {'Ratio':>8} {'State':>8} {'Policy':>8} {'ω':>8} {'Verdict':>12}")
    print("-" * 70)
    for name, r in results.items():
        if r["ratio"] < 0.15:
            verdict = "✅ 弱結合"
        elif r["ratio"] < 0.5:
            verdict = "🟡 中結合"
        else:
            verdict = "❌ 強結合"
        print(f"{name:<22} {r['ratio']:>8.4f} {r['s_coupling']:>8.4f} {r['pi_coupling']:>8.4f} {r['omega_coupling']:>8.4f} {verdict:>12}")

    # Smithe additivity test
    print("\n" + "=" * 70)
    print("SMITHE ADDITIVITY TEST (v=0 vs v≠0)")
    print("=" * 70)
    for name, func in definitions.items():
        p_v0 = p0.copy(); p_v0[4] = 0.0
        p_v1 = p0.copy(); p_v1[4] = v
        H_v0 = numeric_hessian(func, p_v0)
        H_v1 = numeric_hessian(func, p_v1)
        # v=0 のとき base ブロック
        F_base = H_v0[:4, :4]
        F_v0 = H_v0[4, 4]
        # v≠0 のとき
        delta_base = np.linalg.norm(H_v1[:4, :4] - F_base) / np.linalg.norm(F_base)
        print(f"  {name:<22}: ΔF_base = {delta_base:.4f} (base block change when v≠0)")

    return results


if __name__ == "__main__":
    results = run_experiment()
