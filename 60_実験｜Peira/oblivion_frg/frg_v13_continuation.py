"""
P-V.7 v13: n-continuation solver
=================================
Strategy: Start from n=3.5 (where WF is well-captured at Np=2-8),
smoothly decrease n toward 2.78 in small steps (dn=0.02),
using each solution as seed for the next.

This avoids the Gaussian attractor that plagues the direct n=2.78 solver.
"""
import numpy as np
from scipy.optimize import fsolve
from scipy.special import gamma as G, beta as B
import json, sys, warnings
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

# ── Coefficients (identical to v12) ──

def vd(d):
    return 1.0 / (2**(d+1) * np.pi**(d/2) * G(d/2))

def C_T(n, eta):
    v = vd(n)
    om = G(n/2) / (np.sqrt(np.pi) * G((n-1)/2))
    I = (2-eta)*B((n-1)/2, 0.5) + eta*B((n+1)/2, 0.5)
    return (2*v/n) * om * I

def C_eta_T(n):
    v = vd(n)
    om = G(n/2) / (np.sqrt(np.pi) * G((n-1)/2))
    return 16*v/n * om * B((n+3)/2, 0.5)

# ── Flow residuals (identical to v12) ──

def build_flow_T(params, n, Np):
    kappa = params[0]
    lams = params[1:]
    if kappa <= 0 or lams[0] <= 0:
        return np.full(Np, 1e10)
    l2 = lams[0]; w = 2*kappa*l2
    if 1+w <= 0: return np.full(Np, 1e10)
    
    CE = C_eta_T(n)
    eta = CE * kappa * l2**2 / (1+w)**4
    CT = C_T(n, eta)
    
    if eta < 0 or eta > 0.5: return np.full(Np, 1e10)
    
    N = Np + 3
    c = np.zeros(N)
    for j in range(2, min(Np+1, N)):
        idx = j - 2
        if idx < len(lams):
            fac = 1.0
            for m in range(2, j+1): fac *= m
            c[j] = lams[idx] / fac
    
    cp = np.zeros(N)
    for j in range(N-1): cp[j] = c[j+1]*(j+1)
    cpp = np.zeros(N)
    for j in range(N-2): cpp[j] = cp[j+1]*(j+1)
    
    xi_cpp = np.zeros(N)
    for j in range(1, min(N, len(cpp))): xi_cpp[j] = cpp[j-1]
    P = cp + 2*kappa*cpp + 2*xi_cpp
    
    D = P.copy(); D[0] += 1.0
    if abs(D[0]) < 1e-30: return np.full(Np, 1e10)
    b = np.zeros(N); b[0] = 1.0/D[0]
    for j in range(1, N):
        s = 0.0
        for m in range(1, j+1):
            if m < N: s += D[m] * b[j-m]
        b[j] = -s / D[0]
    if np.any(np.isnan(b)): return np.full(Np, 1e10)
    
    xi_cp = np.zeros(N)
    for j in range(1, min(N, len(cp))): xi_cp[j] = cp[j-1]
    
    R = -n*c[:N] + (n-2+eta)*(kappa*cp + xi_cp) + CT*b
    return R[1:Np+1]

# ── Np=2 solver ──

def fp_T_2(x, n):
    k, l2, eta = x
    if k <= 0 or l2 <= 0: return [1e10]*3
    CT = C_T(n, eta); CE = C_eta_T(n)
    w = 2*k*l2
    return [
        -(n-2+eta)*k + 3*CT/(1+w)**2,
        (n-4+2*eta)*l2 + 18*CT*l2**2/(1+w)**3,
        eta - CE*k*l2**2/(1+w)**4,
    ]

def multi_solve_2(n):
    best, best_r = None, 1e30
    for kf in [.005,.01,.02,.05,.08,.1,.2,.5,1,2,5,10,30]:
        for lf in [.05,.1,.3,.5,1,2,5,8,10,20,50,100]:
            for e0 in [.001,.005,.01,.03,.05,.1]:
                try:
                    sol,info,ier,_ = fsolve(fp_T_2,[kf,lf,e0],
                        args=(n,),full_output=True,maxfev=5000)
                    if ier==1 and sol[0]>1e-10 and sol[1]>1e-6 and 0<=sol[2]<0.5:
                        r = np.max(np.abs(info['fvec']))
                        if r < 1e-10 and r < best_r:
                            best_r = r; best = sol.copy()
                except: pass
    return best

# ── Stability (with Creator's T-matrix fix from v12) ──

def stability_T(params, n, Np):
    n_var = len(params)
    def F(x): return build_flow_T(x, n, Np)
    
    J = np.zeros((n_var, n_var))
    for j in range(n_var):
        h = 1e-6 * max(abs(params[j]), 1e-4)
        xp = params.copy(); xp[j] += h
        xm = params.copy(); xm[j] -= h
        fp = F(xp); fm = F(xm)
        if np.any(np.abs(fp) > 1e8) or np.any(np.abs(fm) > 1e8):
            return {"nu": None, "omega": None, "gamma_phi": None, "thetas": []}
        J[:, j] = (fp - fm) / (2*h)
    
    # T-matrix: Taylor coefficients → physical flow
    lam2 = params[1]
    T = np.zeros((n_var, n_var))
    T[0, 0] = -1.0 / lam2
    for i in range(1, n_var):
        jj = i + 1
        fac = 1.0
        for kk in range(2, jj+1): fac *= kk
        T[i, i] = fac
        lam_next = params[i+1] if i+1 < n_var else 0.0
        T[i, 0] = -lam_next / lam2
    
    M = T @ J
    if np.any(np.isnan(M)) or np.any(np.isinf(M)):
        return {"nu": None, "omega": None, "gamma_phi": None, "thetas": []}
    
    try:
        eigs = np.linalg.eigvals(-M)
    except:
        return {"nu": None, "omega": None, "gamma_phi": None, "thetas": []}
    
    th = sorted(np.real(eigs), reverse=True)
    nu = 1.0/th[0] if len(th) > 0 and th[0] > 0.1 else None
    omega = -th[1] if len(th) > 1 and th[1] < -0.01 else None
    gp = 2*nu - 1 if nu and nu > 0.5 else None
    return {"nu": nu, "omega": omega, "gamma_phi": gp,
            "thetas": [float(t) for t in th[:min(5, len(th))]]}

# ── n-continuation ──

def continuation(n_start, n_end, dn, Np_target=8):
    """
    Track WF fixed point from n_start to n_end in steps of dn.
    At each n, progressively build Np from 2 to Np_target.
    """
    n_values = []
    n = n_start
    while n >= n_end - 1e-10:
        n_values.append(round(n, 4))
        n -= abs(dn)
    
    print(f"n-continuation: {n_values[0]:.2f} → {n_values[-1]:.2f} "
          f"({len(n_values)} steps, Np_target={Np_target})")
    print(f"{'n':>6} | {'Np':>3} | {'kappa':>8} | {'lam2':>8} | "
          f"{'eta':>9} | {'nu':>8} | {'gPhi':>8} | {'theta1':>8}")
    print("-" * 80)
    
    results = []
    prev_params = {}  # Np → params at previous n
    
    for n in n_values:
        # Step 1: Solve Np=2
        sol2 = multi_solve_2(n)
        if sol2 is None:
            print(f"  {n:6.2f} | --- | No Np=2 FP")
            results.append({"n": n, "status": "no_fp"})
            continue
        
        k, l2, eta = sol2
        cur = {2: np.array([k, l2])}
        
        # Step 2: Build up to Np_target using previous n's solution as seed
        for Np in range(3, Np_target + 1):
            found = False
            candidates = []
            
            # Seed 1: pad current Np-1 solution
            if Np - 1 in cur:
                seed = np.zeros(Np)
                seed[:len(cur[Np-1])] = cur[Np-1]
                candidates.append(seed)
            
            # Seed 2: use previous n's Np solution (the continuation seed)
            if Np in prev_params:
                candidates.append(prev_params[Np].copy())
            
            # Seed 3: use previous n's Np-1 solution, padded
            if Np - 1 in prev_params:
                seed = np.zeros(Np)
                seed[:len(prev_params[Np-1])] = prev_params[Np-1]
                candidates.append(seed)
            
            best_sol = None
            best_res = 1e30
            
            for base_seed in candidates:
                # Try the seed directly + perturbed versions
                for trial in range(20):
                    if trial == 0:
                        seed = base_seed.copy()
                    else:
                        seed = base_seed.copy()
                        for j in range(len(seed)):
                            seed[j] *= 1.0 + 0.05 * np.random.randn()
                        seed[0] = abs(seed[0])
                        seed[1] = abs(seed[1])
                    
                    try:
                        sol, info, ier, _ = fsolve(
                            build_flow_T, seed, args=(n, Np),
                            full_output=True, maxfev=10000)
                        if ier == 1 and sol[0] > 1e-10 and sol[1] > 0.01:
                            r = np.max(np.abs(info['fvec']))
                            ww = 2*sol[0]*sol[1]
                            CE = C_eta_T(n)
                            eta_s = CE * sol[0]*sol[1]**2/(1+ww)**4
                            if r < 1e-8 and r < best_res and 0 <= eta_s < 0.5:
                                # Reject near-Gaussian: require lam2 > 0.5
                                if sol[1] > 0.5:
                                    best_res = r
                                    best_sol = sol.copy()
                                    found = True
                    except: pass
            
            if found:
                cur[Np] = best_sol.copy()
            else:
                # Use Np-1 padded
                if Np - 1 in cur:
                    seed = np.zeros(Np)
                    seed[:len(cur[Np-1])] = cur[Np-1]
                    cur[Np] = seed
        
        # Best available Np
        best_Np = max(Np for Np in cur if cur[Np][1] > 0.5) if any(cur[Np][1] > 0.5 for Np in cur) else 2
        p = cur[best_Np]
        ww = 2*p[0]*p[1]
        CE = C_eta_T(n)
        eta_val = CE * p[0]*p[1]**2/(1+ww)**4
        
        sa = stability_T(p, n, best_Np)
        nu_s = f"{sa['nu']:.4f}" if sa.get('nu') else "---"
        gp_s = f"{sa['gamma_phi']:.4f}" if sa.get('gamma_phi') else "---"
        th1_s = f"{sa['thetas'][0]:.4f}" if sa.get('thetas') else "---"
        
        print(f"  {n:6.2f} | {best_Np:3d} | {p[0]:8.5f} | {p[1]:8.4f} | "
              f"{eta_val:9.6f} | {nu_s:>8} | {gp_s:>8} | {th1_s:>8}")
        
        results.append({
            "n": n, "Np": best_Np, "kappa": float(p[0]), "lam2": float(p[1]),
            "eta": float(eta_val), "nu": sa.get('nu'), "gamma_phi": sa.get('gamma_phi'),
            "thetas": sa.get('thetas', []), "status": "ok"
        })
        
        # Save for next step's seeding
        prev_params = cur.copy()
    
    return results

# ── Main ──

def main():
    print("="*70)
    print("P-V.7 v13: n-continuation for T-projection FRG")
    print("="*70)
    
    # Phase 1: Coarse scan n=3.5 → 2.5
    print("\n--- Phase 1: Coarse (dn=0.1) ---")
    coarse = continuation(3.5, 2.5, 0.1, Np_target=6)
    
    # Phase 2: Fine scan around n=2.78 (if WF persists)
    wf_exists = [r for r in coarse if r.get('lam2', 0) > 0.5 and r['n'] <= 3.0]
    if wf_exists:
        n_min = min(r['n'] for r in wf_exists)
        print(f"\n--- Phase 2: Fine around n=2.78 (dn=0.02, from n={max(n_min+0.2, 3.0):.2f}) ---")
        fine = continuation(max(n_min + 0.2, 3.0), max(n_min - 0.1, 2.5), 0.02, Np_target=8)
    else:
        print("\nNo WF FP below n=3.0 in coarse scan.")
        fine = []
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY: gamma_Phi along n-continuation")
    print(f"{'='*70}")
    
    all_res = coarse + fine
    for r in all_res:
        if r.get('status') == 'ok' and r.get('gamma_phi'):
            print(f"  n={r['n']:.2f}: gamma_Phi = {r['gamma_phi']:.4f} "
                  f"(nu={r['nu']:.4f}, eta={r['eta']:.6f})")
    
    target = [r for r in all_res if abs(r.get('n',0) - 2.78) < 0.03 and r.get('gamma_phi')]
    if target:
        best = min(target, key=lambda r: abs(r['n'] - 2.78))
        print(f"\n  At n≈2.78: gamma_Phi = {best['gamma_phi']:.4f}")
        print(f"  Target: 0.86")
        print(f"  Ratio: {best['gamma_phi']/0.86:.2f}")
    else:
        print(f"\n  No valid gamma_Phi obtained at n≈2.78")
    
    with open("frg_continuation_v13.json", "w", encoding="utf-8") as f:
        json.dump(all_res, f, indent=2, default=str)
    
    print("\nDone.")

if __name__ == "__main__":
    main()
