"""
Statistical Reinforcement — ULTRA-FAST vectorized version
==========================================================
All bootstrap + permutation done via batch numpy operations.
No Python for-loops in hot path. Target: <10 seconds.
"""
import json, math, os
import numpy as np
from scipy import stats as sp_stats

np.random.seed(42)

RESULTS_PATH = r"c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\10_知性｜Nous\04_企画｜Boulēsis\12_遊学｜Yugaku\03_忘却論｜Oblivion\experiments\results\rho_fine_extended.json"
OUT_DIR = os.path.dirname(RESULTS_PATH)

with open(RESULTS_PATH, "r") as f:
    data = json.load(f)

N = data["n_samples"]   # 30
TASKS = data["tasks"]
VARIANTS = data["variants"]
per_task_accs = data["per_task_accs"]
K = len(VARIANTS)       # 5
B = 10000               # bootstrap/permutation iterations

print("=== Statistical Reinforcement (ultra-fast) ===", flush=True)
print(f"Tasks={len(TASKS)}, Variants={K}, N={N}, B={B}", flush=True)

# === Reconstruct binary data ===
trial_np = {}
for task in TASKS:
    rows = []
    for v in VARIANTS:
        acc = per_task_accs[task][v]
        nc = round(acc * N / 100)
        arr = np.array([1]*nc + [0]*(N-nc))
        np.random.shuffle(arr)
        rows.append(arr)
    trial_np[task] = np.vstack(rows)  # (K, N)

def eta2_vec(mat):
    """eta2 from (K, N) matrix — scalar."""
    gm = mat.mean()
    ss_b = N * np.sum((mat.mean(axis=1) - gm)**2)
    ss_t = np.sum((mat - gm)**2)
    return ss_b / ss_t if ss_t > 1e-15 else 0.0

def eta2_batch(mats):
    """Batch eta2 from (B, K, N) array — returns (B,) array."""
    # mats: (B, K, N)
    gm = mats.mean(axis=(1, 2), keepdims=True)      # (B,1,1)
    group_means = mats.mean(axis=2, keepdims=True)   # (B,K,1)
    ss_b = N * np.sum((group_means - gm)**2, axis=(1, 2))  # (B,)
    ss_t = np.sum((mats - gm)**2, axis=(1, 2))             # (B,)
    mask = ss_t > 1e-15
    result = np.zeros(len(mats))
    result[mask] = ss_b[mask] / ss_t[mask]
    return result

# ================================================================
# 1. BOOTSTRAP CI FOR PER-TASK η²
# ================================================================
print(f"\n{'='*60}", flush=True)
print("1. BOOTSTRAP CI (95%) FOR PER-TASK η²", flush=True)
print(f"{'='*60}", flush=True)

boot_task = {}
for task in TASKS:
    mat = trial_np[task]  # (K, N)
    obs = eta2_vec(mat)
    
    # Generate all bootstrap indices at once: (B, N)
    idx = np.random.randint(0, N, size=(B, N))
    # Resample: (K, B, N) then transpose to (B, K, N)
    resampled = mat[:, idx]  # broadcasting: (K, B, N)
    resampled = resampled.transpose(1, 0, 2)  # (B, K, N)
    boot_vals = eta2_batch(resampled)
    
    ci_lo, ci_hi = np.percentile(boot_vals, [2.5, 97.5])
    phase = "CEILING" if obs < 0.001 else "TRANSITION"
    
    boot_task[task] = {
        "observed_eta2": float(obs),
        "ci_95_lower": float(ci_lo),
        "ci_95_upper": float(ci_hi),
        "boot_mean": float(boot_vals.mean()),
        "boot_sd": float(boot_vals.std()),
    }
    print(f"  {task}: η²={obs:.6f} CI[{ci_lo:.6f}, {ci_hi:.6f}] [{phase}]", flush=True)

# ================================================================
# 2. BOOTSTRAP CI FOR OVERALL ρ_fine
# ================================================================
print(f"\n{'='*60}", flush=True)
print("2. BOOTSTRAP CI (95%) FOR OVERALL ρ_fine", flush=True)
print(f"{'='*60}", flush=True)

rho_obs = data["rho_fine_mean"]

# Cluster bootstrap: resample tasks, then resample trials
task_idx = np.random.randint(0, len(TASKS), size=(B, len(TASKS)))  # (B, 7)
col_idx = np.random.randint(0, N, size=(B, N))                     # (B, N)

boot_rhos = np.zeros(B)
for b in range(B):
    eta2s = []
    for ti in task_idx[b]:
        mat = trial_np[TASKS[ti]][:, col_idx[b]]  # (K, N)
        eta2s.append(eta2_vec(mat))
    boot_rhos[b] = np.mean(eta2s)

ci_lo_r, ci_hi_r = np.percentile(boot_rhos, [2.5, 97.5])
print(f"  ρ_fine = {rho_obs:.6f}", flush=True)
print(f"  95% CI [{ci_lo_r:.6f}, {ci_hi_r:.6f}]", flush=True)
print(f"  Boot mean = {boot_rhos.mean():.6f}", flush=True)

for Kv in [5, 8]:
    r_lo = math.sqrt(max(ci_lo_r, 0)/(Kv+1))
    r_hi = math.sqrt(ci_hi_r/(Kv+1))
    r_pt = math.sqrt(rho_obs/(Kv+1))
    print(f"  r_ceiling (K={Kv}): {r_pt*100:.1f}% [{r_lo*100:.1f}%, {r_hi*100:.1f}%]", flush=True)

# ================================================================
# 3. PERMUTATION TEST — FULLY VECTORIZED
# ================================================================
print(f"\n{'='*60}", flush=True)
print("3. PERMUTATION TEST", flush=True)
print(f"{'='*60}", flush=True)

perm_results = {}
for task in TASKS:
    mat = trial_np[task]
    obs = eta2_vec(mat)
    
    if obs < 0.001:
        perm_results[task] = {"observed_eta2": float(obs), "p_value": 1.0, "note": "ceiling"}
        print(f"  {task}: η²=0.000, p=1.000 [CEILING]", flush=True)
        continue
    
    # Pool and batch-shuffle
    pooled = mat.flatten()  # (K*N,)
    total = K * N
    
    # Create B copies and shuffle each independently
    perm_data = np.tile(pooled, (B, 1))  # (B, K*N)
    # Vectorized shuffle: argsort of random values
    rand_idx = np.argsort(np.random.rand(B, total), axis=1)
    perm_data = np.take_along_axis(perm_data, rand_idx, axis=1)
    perm_mats = perm_data.reshape(B, K, N)  # (B, K, N)
    
    perm_eta2s = eta2_batch(perm_mats)
    p_val = float(np.mean(perm_eta2s >= obs))
    
    sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
    perm_results[task] = {"observed_eta2": float(obs), "p_value": p_val}
    print(f"  {task}: η²={obs:.6f}, p={p_val:.4f} {sig}", flush=True)

# ================================================================
# 4. FISHER'S EXACT (scipy)
# ================================================================
print(f"\n{'='*60}", flush=True)
print("4. PAIRWISE FISHER'S EXACT (transition tasks)", flush=True)
print(f"{'='*60}", flush=True)

pairwise = {}
for task in TASKS:
    if data["per_task_eta2"].get(task, 0) < 0.001:
        continue
    
    accs = per_task_accs[task]
    ranked = sorted(VARIANTS, key=lambda v: accs[v], reverse=True)
    best_v, worst_v = ranked[0], ranked[-1]
    
    nb = round(accs[best_v]*N/100); nw = round(accs[worst_v]*N/100)
    _, p_bw = sp_stats.fisher_exact([[nb, N-nb], [nw, N-nw]])
    
    nc = round(accs["v4_concise"]*N/100); np_ = round(accs["v2_persona"]*N/100)
    _, p_cp = sp_stats.fisher_exact([[nc, N-nc], [np_, N-np_]])
    
    d_bw = accs[best_v] - accs[worst_v]
    d_cp = accs["v4_concise"] - accs["v2_persona"]
    
    s1 = "***" if p_bw<.001 else "**" if p_bw<.01 else "*" if p_bw<.05 else "ns"
    s2 = "***" if p_cp<.001 else "**" if p_cp<.01 else "*" if p_cp<.05 else "ns"
    
    print(f"\n  {task}:", flush=True)
    print(f"    Best: {best_v}({accs[best_v]:.1f}%) vs Worst: {worst_v}({accs[worst_v]:.1f}%) Δ={d_bw:.1f}% p={p_bw:.4f} {s1}", flush=True)
    print(f"    Concise({accs['v4_concise']:.1f}%) vs Persona({accs['v2_persona']:.1f}%) Δ={d_cp:+.1f}% p={p_cp:.4f} {s2}", flush=True)
    
    pairwise[task] = {
        "best": best_v, "worst": worst_v,
        "best_acc": accs[best_v], "worst_acc": accs[worst_v],
        "delta_bw": d_bw, "p_bw": float(p_bw),
        "delta_cp": d_cp, "p_cp": float(p_cp),
    }

# ================================================================
# 5. SUMMARY
# ================================================================
print(f"\n{'='*60}", flush=True)
print("5. SUMMARY", flush=True)
print(f"{'='*60}", flush=True)

n_sig = sum(1 for t in perm_results if perm_results[t]["p_value"] < 0.05)
n_ceil = sum(1 for t in TASKS if data["per_task_eta2"].get(t,0) < 0.001)
print(f"  Significant: {n_sig}/{len(TASKS)}", flush=True)
print(f"  Ceiling/Transition: {n_ceil}/{len(TASKS)-n_ceil}", flush=True)
print(f"  ρ_fine = {rho_obs:.6f} CI[{ci_lo_r:.6f}, {ci_hi_r:.6f}]", flush=True)

ceil_ci = {}
for Kv in [5,8]:
    r = math.sqrt(rho_obs/(Kv+1))
    rl = math.sqrt(max(ci_lo_r,0)/(Kv+1))
    rh = math.sqrt(ci_hi_r/(Kv+1))
    ceil_ci[f"K={Kv}"] = {"point": float(r), "ci_lo": float(rl), "ci_hi": float(rh)}
    print(f"  r_ceil(K={Kv}): {r*100:.1f}% [{rl*100:.1f}%, {rh*100:.1f}%]", flush=True)

# Save
out = {
    "experiment": "statistical_reinforcement_v3",
    "B_boot": B, "B_perm": B,
    "bootstrap_per_task": boot_task,
    "bootstrap_rho": {"obs": float(rho_obs), "ci_lo": float(ci_lo_r), "ci_hi": float(ci_hi_r), "mean": float(boot_rhos.mean())},
    "permutation": perm_results,
    "fisher_pairwise": pairwise,
    "ceiling_ci": ceil_ci,
    "summary": {"n_sig": n_sig, "n_tasks": len(TASKS)},
}
outpath = os.path.join(OUT_DIR, "statistical_reinforcement.json")
with open(outpath, "w") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print(f"\nSaved: {outpath}", flush=True)
print("=== DONE ===", flush=True)
