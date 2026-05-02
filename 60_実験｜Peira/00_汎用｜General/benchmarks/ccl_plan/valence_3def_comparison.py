"""
Valence 3定義比較実験 — /ele 反駁 #1 (循環論法) の検証
========================================================
3つの Valence 定式化それぞれで Fisher 交差項を評価し、
「構造的結合」が定義依存か普遍的かを判定する。

定義 A: Seth (2013) — ω_eff = ω · exp(v)  (乗法的修飾)
定義 B: Pattisapu (2024) — v = C_pref - E[o]  (utility差)
定義 C: Hesp (2021) — v = log(π_precision)  (行動精度の対数)
"""
import numpy as np
import scipy.special

np.random.seed(42)

N_STATES = 3
N_OBS = 2
N_ACTIONS = 2

# POMDP 構造
A = np.random.dirichlet(np.ones(N_OBS), size=(N_STATES,)).T
B = np.random.dirichlet(np.ones(N_STATES), size=(N_ACTIONS, N_STATES)).transpose(0, 2, 1)
C = np.array([-2.0, 1.0])

s = np.random.dirichlet(np.ones(N_STATES))
pi = np.random.dirichlet(np.ones(N_ACTIONS))
omega = 1.0
v = 0.0


def numeric_hessian(func, params, eps=1e-4):
    n = len(params)
    H = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            pp = params.copy(); pp[i] += eps; pp[j] += eps
            pm = params.copy(); pm[i] += eps; pm[j] -= eps
            mp = params.copy(); mp[i] -= eps; mp[j] += eps
            mm = params.copy(); mm[i] -= eps; mm[j] -= eps
            H[i, j] = (func(*pp) - func(*pm) - func(*mp) + func(*mm)) / (4 * eps**2)
    return H


def _efe_per_action(s_vec):
    G = np.zeros(N_ACTIONS)
    for a in range(N_ACTIONS):
        next_s = B[a] @ s_vec
        pred = A @ next_s
        G[a] = np.sum(pred * (np.log(pred + 1e-12) - np.log(scipy.special.softmax(C) + 1e-12)))
    return G


# ===== 定義 A: Seth (2013) — ω_eff = ω · exp(v) =====
def vfe_seth(s0, s1, pi0, om, val):
    s_arr = np.array([s0, s1, 1 - s0 - s1])
    pi_arr = np.array([pi0, 1 - pi0])
    
    pred_obs = A @ s_arr
    ambiguity = -np.sum(s_arr * np.sum(A * np.log(A + 1e-12), axis=0))
    risk = np.sum(pred_obs * (np.log(pred_obs + 1e-12) - np.log(scipy.special.softmax(C) + 1e-12)))
    
    G = _efe_per_action(s_arr)
    omega_eff = om * np.exp(val)  # ← 結合仮定
    F_pi = np.sum(pi_arr * (np.log(pi_arr + 1e-12) + omega_eff * G))
    F_v = 0.5 * val**2
    
    return ambiguity + risk + F_pi + F_v


# ===== 定義 B: Pattisapu (2024) — v = utility差 (独立パラメータ) =====
def vfe_pattisapu(s0, s1, pi0, om, val):
    s_arr = np.array([s0, s1, 1 - s0 - s1])
    pi_arr = np.array([pi0, 1 - pi0])
    
    pred_obs = A @ s_arr
    ambiguity = -np.sum(s_arr * np.sum(A * np.log(A + 1e-12), axis=0))
    risk = np.sum(pred_obs * (np.log(pred_obs + 1e-12) - np.log(scipy.special.softmax(C) + 1e-12)))
    
    G = _efe_per_action(s_arr)
    F_pi = np.sum(pi_arr * (np.log(pi_arr + 1e-12) + om * G))
    
    # Valence = utility差 → 独立した事前分布のみ。ω とは結合しない
    expected_obs = pred_obs
    utility = np.sum(expected_obs * C)
    F_v = 0.5 * (val - utility)**2  # v の事後は utility に近づく
    
    return ambiguity + risk + F_pi + F_v


# ===== 定義 C: Hesp (2021) — v = log(action precision) =====
def vfe_hesp(s0, s1, pi0, om, val):
    s_arr = np.array([s0, s1, 1 - s0 - s1])
    pi_arr = np.array([pi0, 1 - pi0])
    
    pred_obs = A @ s_arr
    ambiguity = -np.sum(s_arr * np.sum(A * np.log(A + 1e-12), axis=0))
    risk = np.sum(pred_obs * (np.log(pred_obs + 1e-12) - np.log(scipy.special.softmax(C) + 1e-12)))
    
    G = _efe_per_action(s_arr)
    F_pi = np.sum(pi_arr * (np.log(pi_arr + 1e-12) + om * G))
    
    # Valence = expected action precision の対数
    # v は方策精度の事前期待 → pi の entropy に近い
    pi_entropy = -np.sum(pi_arr * np.log(pi_arr + 1e-12))
    F_v = 0.5 * (val - (-pi_entropy))**2  # precision = -entropy
    
    return ambiguity + risk + F_pi + F_v


def analyze(name, func):
    p0 = [s[0], s[1], pi[0], omega, v]
    H = numeric_hessian(func, p0)
    v_idx = 4
    
    cross = {
        "s0": H[v_idx, 0],
        "s1": H[v_idx, 1],
        "pi0": H[v_idx, 2],
        "omega": H[v_idx, 3],
    }
    off_diag = np.sum(np.abs(H[v_idx, :4]))
    diag = np.abs(H[v_idx, v_idx])
    ratio = off_diag / diag if diag > 1e-12 else float('inf')
    
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")
    for k, val in cross.items():
        print(f"  d²F/(dv d{k}) = {val:+.6f}")
    print(f"  ────────────────────────────")
    print(f"  off-diag sum: {off_diag:.6f}")
    print(f"  diagonal:     {diag:.6f}")
    print(f"  ratio:        {ratio:.4f}")
    
    if ratio < 0.1:
        verdict = "✅ INDEPENDENT (block diagonal)"
    elif ratio < 0.3:
        verdict = "🟡 WEAKLY COUPLED"
    else:
        verdict = "❌ STRONGLY COUPLED"
    print(f"  verdict:      {verdict}")
    return ratio


print("Valence 3定義比較実験")
print("=" * 50)

r_seth = analyze("A: Seth (2013) — ω·exp(v)", vfe_seth)
r_patt = analyze("B: Pattisapu (2024) — utility差", vfe_pattisapu)
r_hesp = analyze("C: Hesp (2021) — action precision", vfe_hesp)

print(f"\n{'='*50}")
print("SUMMARY")
print(f"{'='*50}")
print(f"  Seth:      ratio={r_seth:.4f}")
print(f"  Pattisapu: ratio={r_patt:.4f}")
print(f"  Hesp:      ratio={r_hesp:.4f}")
print()
if r_patt < 0.1 or r_hesp < 0.1:
    print("結論: Valence の独立性は定義依存。")
    print("  → 非結合定義 (Pattisapu/Hesp) では 7 ブロック分解が維持される。")
    print("  → Seth 定義の結合は ω_eff=ω·exp(v) という仮定の恒等的帰結。")
else:
    print("結論: 全定義で結合あり。Valence は本質的に非独立。")
