import numpy as np
import scipy.stats

def evaluate_valence_cross_terms(n_states=3, n_obs=2, n_actions=2):
    """
    Valence v = -dF/dt 定義に基づく、v と他の POMDP パラメータの交差項の定量評価
    Seth (2013), Joffily (2013) の Affective inference に基づき、
    v を「予測誤差の期待変化率」として扱い、独立した推論プロセスとみなせるかを検証。
    """
    np.random.seed(42)
    
    # POMDP パラメータ
    # A (Observation model)
    A = np.random.dirichlet(np.ones(n_obs), size=(n_states,)).T
    # B (Transition model)
    B = np.random.dirichlet(np.ones(n_states), size=(n_actions, n_states)).transpose(0, 2, 1)
    # C (Preferences)
    C = np.array([-2.0, 1.0]) # ex. observation 1 pref
    
    # 状態信念 s (mu)
    s = np.random.dirichlet(np.ones(n_states))
    
    # 方策信念 pi
    pi = np.random.dirichlet(np.ones(n_actions))
    
    # 精度 omega
    omega = 1.0
    
    # Valence v
    v = 0.0 # initial
    
    def calc_vfe(s, pi, omega, v):
        # 1. 状態VFE
        pred_obs = A @ s
        ambiguity = -np.sum(s * np.sum(A * np.log(A + 1e-12), axis=0))
        risk = np.sum(pred_obs * (np.log(pred_obs + 1e-12) - np.log(scipy.special.softmax(C) + 1e-12)))
        F_state = ambiguity + risk
        
        # 2. 方策VFE
        # EFE の計算 (ここでは F_state を行動ごとに分岐させる簡略版)
        G = np.zeros(n_actions)
        for a in range(n_actions):
            next_s = B[a] @ s
            pred_obs_a = A @ next_s
            G[a] = np.sum(pred_obs_a * (np.log(pred_obs_a + 1e-12) - np.log(scipy.special.softmax(C) + 1e-12)))
        
        F_pi = np.sum(pi * (np.log(pi + 1e-12) + omega * G))
        
        # 3. Valence 結合項 (Affective inference - Joffily)
        # 感情価 v は、方策の不確実性（precision omega）を修飾する、
        # あるいは「予測誤差自体の事前分布」を持つ。
        # ここでは Seth(2013) に従い、v が omega に影響を与えるとモデル化。
        # VFE += (v + dF/dt)^2 的な二次形式誤差、あるいは交差エントロピー。
        
        # v の事前分布 (mean=0, var=1) への KL
        F_v = 0.5 * (v**2)
        
        # coupling: 例えば omega = exp(v) という修飾を行う場合、
        # F は v に強く依存し、v と pi の間に交差項が生まれる。
        # 今回は独立推論を検証するため、結合 VFE モデルを構築。
        omega_eff = omega * np.exp(v)
        F_total = F_state + np.sum(pi * (np.log(pi + 1e-12) + omega_eff * G)) + F_v
        
        return F_total
        
    # Fisher 情報行列の数値微分のための関数
    def numeric_hessian(func, params, eps=1e-4):
        n = len(params)
        H = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                p_pp = params.copy()
                p_pp[i] += eps
                p_pp[j] += eps
                
                p_pm = params.copy()
                p_pm[i] += eps
                p_pm[j] -= eps
                
                p_mp = params.copy()
                p_mp[i] -= eps
                p_mp[j] += eps
                
                p_mm = params.copy()
                p_mm[i] -= eps
                p_mm[j] -= eps
                
                f_pp = func(*p_pp)
                f_pm = func(*p_pm)
                f_mp = func(*p_mp)
                f_mm = func(*p_mm)
                
                H[i, j] = (f_pp - f_pm - f_mp + f_mm) / (4 * eps**2)
        return H

    # Evaluate Hessian around current point
    # params: [s0, s1, pi0, omega, v] (s2 and pi1 are dependent, sum=1)
    
    def wrapper(s0, s1, pi0, om, val):
        s_arr = np.array([s0, s1, 1 - s0 - s1])
        pi_arr = np.array([pi0, 1 - pi0])
        return calc_vfe(s_arr, pi_arr, om, val)
        
    p0 = [s[0], s[1], pi[0], omega, v]
    H = numeric_hessian(wrapper, p0)
    
    print("=== Valence (v) Cross-Terms ===")
    print(f"Hessian dimensions: s0, s1, pi0, omega, v")
    
    # Extract cross-terms with v (index 4)
    v_idx = 4
    cross_terms = {
        "s0": H[v_idx, 0],
        "s1": H[v_idx, 1],
        "pi0": H[v_idx, 2],
        "omega": H[v_idx, 3]
    }
    
    for k, val in cross_terms.items():
        print(f"d^2F / (dv d{k}) = {val:.6f}")
        
    # Block diagonal check
    off_diag_v_sum = np.sum(np.abs(H[v_idx, :4]))
    diag_v = np.abs(H[v_idx, v_idx])
    
    print("---")
    print(f"Off-diagonal sum (v): {off_diag_v_sum:.6f}")
    print(f"Diagonal (v): {diag_v:.6f}")
    
    ratio = off_diag_v_sum / diag_v
    print(f"Coupling ratio (off/on): {ratio:.4f}")
    
    if ratio < 0.1:
        print("Conclusion: Valence is computationally independent (block diagonal supported).")
    else:
        print("Conclusion: Valence exhibits non-trivial cross-terms (structural coupling exists).")
        
if __name__ == "__main__":
    evaluate_valence_cross_terms()
