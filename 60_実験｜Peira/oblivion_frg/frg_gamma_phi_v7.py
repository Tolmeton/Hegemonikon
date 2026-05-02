"""
P-V.7: FRG gamma_Phi v7 — progressive Np refinement
====================================================
Fix: v6's 3D Ising spurious FP by solving Np=2 first,
then using that solution as seed for higher Np.

LPA' with Litim regulator, N=1 scalar, Z2, broken phase.
T-projection: n-dim theory -> d=(n-1)-dim isotropic.
"""
import numpy as np
from scipy.optimize import fsolve
from scipy.special import gamma as Gamma
import json, sys, warnings
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

def vd(d):
    return 1.0 / (2**(d+1) * np.pi**(d/2) * Gamma(d/2))

def cd(d):
    return 2.0 * vd(d) / d

# ── Np=2: closed 3-equation system (kappa, lam2, eta) ──

def fp_np2(params, d):
    k, l2, eta = params
    if k <= 0 or l2 <= 0:
        return [1e10, 1e10, 1e10]
    CD, VD = cd(d), vd(d)
    w = 2*k*l2
    d1 = (1+w)**2; d2 = (1+w)**3; d3 = (1+w)**4
    return [
        -(d-2+eta)*k + 3*CD*(2-eta)/d1,
        (d-4+2*eta)*l2 + 18*CD*(2-eta)*l2**2/d2,
        eta - 16*VD/d * k*l2**2/d3,
    ]

def solve_np2(d):
    eps = 4.0 - d
    if eps <= 0:
        return None
    CD = cd(d)
    k0 = 6*CD / max(d-2, 0.1)
    l0 = eps / (36*CD) if CD > 0 else 10.0
    best, best_r = None, 1e30
    for kf in [.01,.05,.1,.3,.5,1,2,5,10]:
        for lf in [.01,.1,.3,.5,1,2,5,10,50]:
            for e0 in [.001,.01,.05]:
                try:
                    sol,info,ier,_ = fsolve(fp_np2,[k0*kf,l0*lf,e0],
                                            args=(d,),full_output=True,maxfev=5000)
                    if ier==1 and sol[0]>1e-10 and sol[1]>1e-6 and 0<=sol[2]<.5:
                        r = np.max(np.abs(info['fvec']))
                        if r < 1e-10 and r < best_r:
                            best_r = r; best = tuple(sol)
                except: pass
    return best

# ── General Np: Taylor-series flow residuals ──
# params = [kappa, lam2, lam3, ..., lam_Np] → len = Np
# Returns Np residuals R[1]..R[Np]

def fp_general(params, d, Np):
    kappa = params[0]
    lams = params[1:]  # lam2, lam3, ..., lam_Np → len = Np-1
    if kappa <= 0 or lams[0] <= 0:
        return np.full(Np, 1e10)
    CD, VD = cd(d), vd(d)
    l2 = lams[0]; w = 2*kappa*l2
    eta = 16*VD/d * kappa*l2**2/(1+w)**4
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
    xi_cpp = np.zeros(N); xi_cpp[1:min(N,len(cpp))] = cpp[:N-1]
    P = cp + 2*kappa*cpp + 2*xi_cpp
    D = P.copy(); D[0] += 1.0
    b = np.zeros(N)
    if abs(D[0]) < 1e-30: return np.full(Np, 1e10)
    b[0] = 1.0/D[0]
    for j in range(1, N):
        s = sum(D[m]*b[j-m] for m in range(1, min(j+1, N)))
        b[j] = -s/D[0]
    if np.any(np.isnan(b)): return np.full(Np, 1e10)
    xi_cp = np.zeros(N); xi_cp[1:min(N,len(cp))] = cp[:N-1]
    R = -d*c[:N] + (d-2+eta)*(kappa*cp + xi_cp) + CD*(2-eta)*b
    return R[1:Np+1]

# ── Progressive Np solving ──

def solve_progressive(d, max_Np=10):
    sol2 = solve_np2(d)
    if sol2 is None: return None
    k, l2, eta = sol2
    w = 2*k*l2
    results = {}
    # Np=2: params=[kappa, lam2] for fp_general
    p2 = np.array([k, l2])
    results[2] = {"params": p2.copy(), "kappa":k, "lam2":l2,
                  "eta":eta, "w":w}
    cur = p2.copy()
    for Np in range(3, max_Np+1):
        new_p = np.zeros(Np); new_p[:len(cur)] = cur
        found = False
        try:
            sol,info,ier,_ = fsolve(fp_general, new_p, args=(d,Np),
                                    full_output=True, maxfev=10000)
            if ier==1 and sol[0]>1e-10 and sol[1]>1e-6:
                r = np.max(np.abs(info['fvec']))
                if r < 1e-8:
                    cur = sol.copy()
                    ww = 2*sol[0]*sol[1]
                    eta_s = 16*vd(d)/d * sol[0]*sol[1]**2/(1+ww)**4
                    results[Np] = {"params":sol.copy(),
                                   "kappa":float(sol[0]),
                                   "lam2":float(sol[1]), "eta":float(eta_s),
                                   "w":float(ww), "res":float(r)}
                    found = True
        except: pass
        if not found:
            prev = results[Np-1]
            padded = np.zeros(Np)
            pp = prev["params"]
            padded[:len(pp)] = pp
            results[Np] = {**prev, "params":padded}
    return results

# ── Stability analysis ──

def stability(d, params):
    """Critical exponents from stability matrix at fixed point.
    Uses fp_general with Np = len(params)."""
    Np = len(params)
    h = 1e-7
    f0 = np.array(fp_general(params, d, Np))
    J = np.zeros((Np, Np))
    for j in range(Np):
        xp = params.copy()
        step = h * max(abs(xp[j]), 1e-6)
        xp[j] += step
        fp = np.array(fp_general(xp, d, Np))
        J[:, j] = (fp - f0) / step
    eigs = np.linalg.eigvals(-J)
    th = sorted(np.real(eigs), reverse=True)
    nu = 1.0/th[0] if th[0] > 0.01 else None
    omega = -th[1] if len(th) > 1 and th[1] < 0 else None
    gp = 2*nu - 1 if nu and nu > 0.5 else None
    return {"nu":nu, "omega":omega, "gamma_phi":gp,
            "thetas":[float(t) for t in th[:4]]}

# ── Main ──

def main():
    print("="*70)
    print("BENCHMARK: 3D Ising (d=3, N=1, eps=1)")
    print("="*70)
    print(f"  Exact:  nu=0.6300, eta=0.0363, omega=0.830")
    d = 3.0
    res = solve_progressive(d, max_Np=10)
    if res:
        print(f"\n  {'Np':>4} | {'eta':>9} | {'nu':>8} | {'omega':>8} | {'gPhi':>8}")
        print("  "+"-"*50)
        for Np in sorted(res.keys()):
            r = res[Np]
            sa = stability(d, r["params"])
            nu_s = f"{sa['nu']:.4f}" if sa['nu'] else "---"
            om_s = f"{sa['omega']:.4f}" if sa['omega'] else "---"
            gp_s = f"{sa['gamma_phi']:.4f}" if sa['gamma_phi'] else "---"
            print(f"  {Np:4d} | {r['eta']:9.6f} | {nu_s:>8} | {om_s:>8} | {gp_s:>8}")
        best_Np = max(res.keys())
        best = res[best_Np]
        sa_best = stability(d, best["params"])
        if sa_best['nu']:
            err_nu = abs(sa_best['nu'] - 0.630)/0.630*100
            err_eta = abs(best['eta'] - 0.0363)/0.0363*100
            print(f"\n  Best Np={best_Np}: nu={sa_best['nu']:.4f} (err {err_nu:.1f}%), "
                  f"eta={best['eta']:.6f} (err {err_eta:.1f}%)")

    print("\n"+"="*70)
    print("OBLIVION FIELD: T-projection (n_c=5, d=n-1)")
    print("="*70)
    print(f"\n  {'n':>6} | {'d':>5} | {'eps':>5} | {'eta':>9} | "
          f"{'nu':>8} | {'gPhi_FRG':>9} | {'gPhi_1L':>8}")
    print("  "+"-"*68)
    all_res = []
    for n in [4.9, 4.5, 4.0, 3.5, 3.0, 2.78, 2.5]:
        d = n - 1; eps = 5.0 - n
        g1l = (n-2)*eps/(2*(n+1)*(n-1)) if 2<n<5 else 0
        rr = solve_progressive(d, max_Np=10)
        if rr:
            best_Np = max(rr.keys()); r = rr[best_Np]
            sa = stability(d, r["params"])
            if sa.get('gamma_phi') and sa['gamma_phi'] > 0:
                print(f"  {n:6.2f} | {d:5.2f} | {eps:5.2f} | {r['eta']:9.6f} | "
                      f"{sa['nu']:8.4f} | {sa['gamma_phi']:9.4f} | {g1l:8.4f}")
                all_res.append({"n":n,"d":d,"eps":eps,"eta":r['eta'],
                                "nu":sa['nu'],"gamma_phi":sa['gamma_phi'],"gamma_1L":g1l})
                continue
        print(f"  {n:6.2f} | {d:5.2f} | {eps:5.2f} | {'---':>9} | "
              f"{'---':>8} | {'---':>9} | {g1l:8.4f}")
        all_res.append({"n":n,"d":d,"eps":eps,"gamma_phi":None,"gamma_1L":g1l})

    print("\n"+"="*70)
    print("KEY: n=2.78 (d=1.78) Np convergence")
    print("="*70)
    d_key = 1.78
    rr = solve_progressive(d_key, max_Np=12)
    if rr:
        print(f"\n  {'Np':>4} | {'eta':>9} | {'nu':>8} | {'gPhi':>8}")
        print("  "+"-"*40)
        for Np in sorted(rr.keys()):
            r = rr[Np]
            sa = stability(d_key, r["params"])
            gp = f"{sa['gamma_phi']:.4f}" if sa.get('gamma_phi') else "---"
            nu = f"{sa['nu']:.4f}" if sa.get('nu') else "---"
            print(f"  {Np:4d} | {r['eta']:9.6f} | {nu:>8} | {gp:>8}")
        best_Np = max(rr.keys())
        best = rr[best_Np]
        sa = stability(d_key, best["params"])
        if sa.get('gamma_phi'):
            print(f"\n  gPhi_FRG = {sa['gamma_phi']:.4f}")
            print(f"  target   = 0.86")
            print(f"  ratio    = {sa['gamma_phi']/0.86:.2f}")

    with open("frg_results_v7.json","w",encoding="utf-8") as f:
        json.dump(all_res, f, indent=2, ensure_ascii=False)
    print("\nDone.")

if __name__ == "__main__":
    main()
