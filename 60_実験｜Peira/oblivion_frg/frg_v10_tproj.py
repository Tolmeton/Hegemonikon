"""
P-V.7 v10: Full T-projection FRG (NOT d=n-1 mapping)
=====================================================
Key insight: d=n-1 mapping kills broken phase at d<2.
T-projection keeps physical dim n>2, only modifies loops.
This preserves the WF fixed point down to n~2.78.
"""
import numpy as np
from scipy.optimize import fsolve
from scipy.special import gamma as G, beta as B
import json, sys, warnings
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

# ── T-projection threshold functions (§5.5.2) ──

def C_T(n, eta):
    """T-projection loop coefficient: replaces c_d*(2-eta) in isotropic."""
    vn = 1.0 / (2**(n+1) * np.pi**(n/2) * G(n/2))
    om = G(n/2) / (np.sqrt(np.pi) * G((n-1)/2))
    I = (2-eta)*B((n-1)/2, 0.5) + eta*B((n+1)/2, 0.5)
    return (2*vn/n) * om * I

def C_eta_T(n):
    """T-projection eta coefficient with sin^4 theta suppression."""
    vn = 1.0 / (2**(n+1) * np.pi**(n/2) * G(n/2))
    om = G(n/2) / (np.sqrt(np.pi) * G((n-1)/2))
    Bm4 = B((n+3)/2, 0.5)
    return 16*vn/n * om * Bm4

def cd_iso(d):
    """Isotropic loop coefficient (for benchmark)."""
    vd = 1.0 / (2**(d+1) * np.pi**(d/2) * G(d/2))
    return 2*vd/d

# ── Fixed point equations ──

def fp_T_projection(params, n):
    """T-projection FRG, broken phase, Np=2. Physical dim = n."""
    k, l2, eta = params
    if k <= 0 or l2 <= 0: return [1e10]*3
    CT = C_T(n, eta)
    CE = C_eta_T(n)
    w = 2*k*l2
    return [
        -(n-2+eta)*k + 3*CT/(1+w)**2,        # kappa
        (n-4+2*eta)*l2 + 18*CT*l2**2/(1+w)**3, # lambda2
        eta - CE*k*l2**2/(1+w)**4,              # eta
    ]

def fp_isotropic(params, d):
    """Standard isotropic FRG (for 3D Ising benchmark)."""
    k, l2, eta = params
    if k <= 0 or l2 <= 0: return [1e10]*3
    CD = cd_iso(d); VD = 1.0/(2**(d+1)*np.pi**(d/2)*G(d/2))
    w = 2*k*l2
    return [
        -(d-2+eta)*k + 3*CD*(2-eta)/(1+w)**2,
        (d-4+2*eta)*l2 + 18*CD*(2-eta)*l2**2/(1+w)**3,
        eta - 16*VD/d * k*l2**2/(1+w)**4,
    ]

def solve_fp(fp_func, param, verbose=False):
    """Solve FP equations with multi-start."""
    best, best_r = None, 1e30
    # Estimate scale
    for kf in [.005,.01,.03,.05,.1,.3,.5,1,2,5,10,30]:
        for lf in [.01,.05,.1,.3,.5,1,2,5,10,30,100]:
            for e0 in [.001,.005,.01,.03,.05,.1]:
                try:
                    sol,info,ier,_ = fsolve(fp_func,[kf,lf,e0],
                        args=(param,),full_output=True,maxfev=5000)
                    if ier==1 and sol[0]>1e-10 and sol[1]>1e-6 and 0<=sol[2]<0.5:
                        r = np.max(np.abs(info['fvec']))
                        if r < 1e-10 and r < best_r:
                            best_r = r; best = tuple(sol)
                except: pass
    if best and verbose:
        k,l2,eta = best
        print(f"    kappa={k:.6f} lam2={l2:.4f} w={2*k*l2:.4f} eta={eta:.6f} res={best_r:.1e}")
    return best

def stability_3(fp_func, params, param):
    """Stability matrix eigenvalues → nu, omega, gamma_phi."""
    h = 1e-7
    f0 = np.array(fp_func(list(params), param))
    J = np.zeros((3,3))
    for j in range(3):
        xp = list(params); step = h*max(abs(xp[j]),1e-6)
        xp[j] += step
        J[:,j] = (np.array(fp_func(xp, param)) - f0) / step
    eigs = np.linalg.eigvals(-J)
    th = sorted(np.real(eigs), reverse=True)
    nu = 1.0/th[0] if th[0] > 0.01 else None
    omega = -th[1] if len(th)>1 and th[1]<0 else None
    gp = 2*nu - 1 if nu and nu > 0.5 else None
    return {"nu":nu, "omega":omega, "gamma_phi":gp, "thetas":th}

# ── Main ──

def main():
    # 1. Benchmark: 3D Ising (isotropic, d=3)
    print("="*70)
    print("BENCHMARK: 3D Ising (isotropic d=3, d_c=4)")
    print("="*70)
    sol = solve_fp(fp_isotropic, 3.0, verbose=True)
    if sol:
        sa = stability_3(fp_isotropic, sol, 3.0)
        print(f"  nu={sa['nu']:.4f} (exact 0.630)")
        print(f"  eta={sol[2]:.6f} (exact 0.0363)")

    # 2. Diagnostic: why d=n-1 fails
    print("\n"+"="*70)
    print("DIAGNOSTIC: isotropic d=n-1 mapping")
    print("="*70)
    print(f"  {'d':>5} | {'n-2+eta':>8} | {'FP?':>4} | note")
    print("  "+"-"*45)
    for d in [3.0, 2.5, 2.2, 2.0, 1.9, 1.78]:
        sign = d - 2
        sol = solve_fp(fp_isotropic, d)
        status = "YES" if sol else "NO"
        note = "n-2+eta < 0 → kappa forced negative" if sign < 0 else ""
        print(f"  {d:5.2f} | {sign:8.2f} | {status:>4} | {note}")

    # 3. T-projection: direct n-dimensional
    print("\n"+"="*70)
    print("T-PROJECTION FRG: direct n-dim (n_c=5)")
    print("="*70)
    print(f"  Key: n-2+eta > 0 for all n > 2 → broken phase preserved!")
    print(f"\n  {'n':>6} | {'n-2':>5} | {'CT':>8} | {'kappa':>8} | "
          f"{'lam2':>8} | {'eta':>9} | {'nu':>7} | {'gPhi':>7}")
    print("  "+"-"*78)

    results = []
    for n in [4.9, 4.5, 4.0, 3.5, 3.0, 2.78, 2.5, 2.3, 2.1]:
        ct = C_T(n, 0)
        sol = solve_fp(fp_T_projection, n)
        if sol:
            k,l2,eta = sol
            sa = stability_3(fp_T_projection, sol, n)
            nu_s = f"{sa['nu']:.4f}" if sa['nu'] else "---"
            gp_s = f"{sa['gamma_phi']:.4f}" if sa.get('gamma_phi') else "---"
            print(f"  {n:6.2f} | {n-2:5.2f} | {ct:8.5f} | {k:8.5f} | "
                  f"{l2:8.3f} | {eta:9.6f} | {nu_s:>7} | {gp_s:>7}")
            results.append({"n":n, "kappa":k, "lam2":l2, "eta":eta,
                            "nu":sa['nu'], "gamma_phi":sa.get('gamma_phi'),
                            "CT":ct})
        else:
            print(f"  {n:6.2f} | {n-2:5.2f} | {ct:8.5f} | {'---':>8} | "
                  f"{'---':>8} | {'---':>9} | {'---':>7} | {'---':>7}")
            results.append({"n":n, "gamma_phi":None, "CT":ct})

    # 4. Key result
    print("\n"+"="*70)
    print("KEY: n=2.78")
    print("="*70)
    sol = solve_fp(fp_T_projection, 2.78, verbose=True)
    if sol:
        sa = stability_3(fp_T_projection, sol, 2.78)
        if sa.get('gamma_phi'):
            print(f"\n  gamma_Phi^FRG = {sa['gamma_phi']:.4f}")
            print(f"  target        = 0.86")
            print(f"  ratio         = {sa['gamma_phi']/0.86:.2f}")
        # Compare with isotropic d=1.78
        sol_iso = solve_fp(fp_isotropic, 1.78)
        print(f"\n  Isotropic d=1.78: {'FP found' if sol_iso else 'NO FP (d<2 kills broken phase)'}")
    else:
        print("  No FP found at n=2.78")

    with open("frg_results_v10.json","w",encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print("\nDone.")

if __name__ == "__main__":
    main()
