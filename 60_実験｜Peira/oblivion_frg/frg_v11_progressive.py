"""
P-V.7 v11: T-projection FRG with progressive Np refinement
============================================================
Combines v10's T-projection insight (n-dim, NOT d=n-1 mapping)
with v7's progressive Np solver.

Key insight from v10:
  - d=n-1 mapping kills broken phase at d<2 (kappa forced negative)
  - T-projection keeps physical dim n>2, only modifies loop integrals
  - WF fixed point found at n=2.78 with Np=2

This script extends to Np=2..10 at n=2.78 to check if
nu converges above 1/2, enabling gamma_Phi = 2*nu - 1 > 0.
"""
import numpy as np
from scipy.optimize import fsolve
from scipy.special import gamma as G, beta as B
import json, sys, warnings
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

# ── T-projection coefficients (§5.5.2) ──

def C_T(n, eta):
    """T-projection loop coefficient."""
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
    vd = 1.0 / (2**(d+1) * np.pi**(d/2) * G(d/2))
    return 2*vd/d

# ── Np=2 solver (T-projection) ──

def fp_T_np2(params, n):
    k, l2, eta = params
    if k <= 0 or l2 <= 0: return [1e10]*3
    CT = C_T(n, eta)
    CE = C_eta_T(n)
    w = 2*k*l2
    return [
        -(n-2+eta)*k + 3*CT/(1+w)**2,
        (n-4+2*eta)*l2 + 18*CT*l2**2/(1+w)**3,
        eta - CE*k*l2**2/(1+w)**4,
    ]

def solve_T_np2(n):
    best, best_r = None, 1e30
    for kf in [.005,.01,.03,.05,.1,.3,.5,1,2,5,10,30]:
        for lf in [.01,.05,.1,.3,.5,1,2,5,10,30,100]:
            for e0 in [.001,.005,.01,.03,.05,.1]:
                try:
                    sol,info,ier,_ = fsolve(fp_T_np2,[kf,lf,e0],
                        args=(n,),full_output=True,maxfev=5000)
                    if ier==1 and sol[0]>1e-10 and sol[1]>1e-6 and 0<=sol[2]<0.5:
                        r = np.max(np.abs(info['fvec']))
                        if r < 1e-10 and r < best_r:
                            best_r = r; best = tuple(sol)
                except: pass
    return best

# ── General Np (T-projection): Taylor-series flow ──

def fp_T_general(params, n, Np):
    """
    T-projection FRG, broken phase, general Np.
    params = [kappa, lam2, lam3, ..., lam_Np]  (length = Np)
    
    The potential: u(rho) = sum_{j=2}^{Np} (lam_j / j!) * (rho - kappa)^j
    
    Flow: dt u = -n*u + (n-2+eta)*rho*u' + C_T(n,eta) / (1+u'+2*rho*u'')
    
    At fixed point: project onto each Taylor coefficient.
    """
    kappa = params[0]
    lams = params[1:]  # lam2, lam3, ..., lam_Np
    if kappa <= 0 or lams[0] <= 0:
        return np.full(Np, 1e10)
    
    l2 = lams[0]
    w = 2*kappa*l2
    if 1+w <= 0:
        return np.full(Np, 1e10)
    
    # Compute eta from lam2 and kappa (self-consistent)
    CE = C_eta_T(n)
    eta = CE * kappa * l2**2 / (1+w)**4
    if eta < 0 or eta > 0.5:
        return np.full(Np, 1e10)
    
    CT = C_T(n, eta)
    
    # Build Taylor coefficients of u(rho) around kappa
    # c[j] = lam_j / j!  for j >= 2
    N = Np + 3
    c = np.zeros(N)
    for j in range(2, min(Np+1, N)):
        idx = j - 2
        if idx < len(lams):
            fac = 1.0
            for m in range(2, j+1): fac *= m
            c[j] = lams[idx] / fac
    
    # u'(rho-kappa) Taylor coefficients: cp[j] = c[j+1]*(j+1)
    cp = np.zeros(N)
    for j in range(N-1): cp[j] = c[j+1]*(j+1)
    
    # u''(rho-kappa) Taylor coefficients
    cpp = np.zeros(N)
    for j in range(N-2): cpp[j] = cp[j+1]*(j+1)
    
    # g(rho) = u' + 2*(kappa + xi)*u'' where xi = rho - kappa
    # g = cp + 2*kappa*cpp + 2*xi*cpp
    # As Taylor in xi: g[j] for j >= 0
    xi_cpp = np.zeros(N)
    xi_cpp[1:min(N, len(cpp))] = cpp[:N-1]
    P = cp + 2*kappa*cpp + 2*xi_cpp
    
    # D(xi) = 1 + g(xi) = 1 + P(xi)
    D = P.copy(); D[0] += 1.0
    
    # 1/D(xi) = b[0] + b[1]*xi + ... via recursion
    # D[0]*b[j] = -sum_{m=1}^{j} D[m]*b[j-m]  (j >= 1), b[0] = 1/D[0]
    if abs(D[0]) < 1e-30:
        return np.full(Np, 1e10)
    b = np.zeros(N)
    b[0] = 1.0/D[0]
    for j in range(1, N):
        s = sum(D[m]*b[j-m] for m in range(1, min(j+1, N)))
        b[j] = -s/D[0]
    if np.any(np.isnan(b)):
        return np.full(Np, 1e10)
    
    # Flow of u: dt u = -n*u + (n-2+eta)*(kappa+xi)*u' + CT*b(xi)
    # (kappa+xi)*u' as Taylor: kappa*cp + xi*cp
    xi_cp = np.zeros(N)
    xi_cp[1:min(N, len(cp))] = cp[:N-1]
    
    # Residual R[j] = coefficient of xi^j in the flow equation
    R = -n*c[:N] + (n-2+eta)*(kappa*cp + xi_cp) + CT*b
    
    # R[0] determines u(kappa) shift (irrelevant), R[1]=0 is kappa equation
    # R[j] for j=1..Np are our equations
    return R[1:Np+1]

# ── Isotropic benchmark (3D Ising) ──

def fp_iso_general(params, d, Np):
    """Isotropic FRG for benchmark."""
    kappa = params[0]
    lams = params[1:]
    if kappa <= 0 or lams[0] <= 0:
        return np.full(Np, 1e10)
    l2 = lams[0]; w = 2*kappa*l2
    if 1+w <= 0: return np.full(Np, 1e10)
    
    VD = 1.0/(2**(d+1)*np.pi**(d/2)*G(d/2))
    CD = cd_iso(d)
    eta = 16*VD/d * kappa*l2**2/(1+w)**4
    if eta < 0 or eta > 0.5: return np.full(Np, 1e10)
    
    N = Np + 3
    c = np.zeros(N)
    for j in range(2, min(Np+1, N)):
        idx = j-2
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
    if abs(D[0]) < 1e-30: return np.full(Np, 1e10)
    b = np.zeros(N); b[0] = 1.0/D[0]
    for j in range(1, N):
        s = sum(D[m]*b[j-m] for m in range(1, min(j+1,N)))
        b[j] = -s/D[0]
    if np.any(np.isnan(b)): return np.full(Np, 1e10)
    xi_cp = np.zeros(N); xi_cp[1:min(N,len(cp))] = cp[:N-1]
    R = -d*c[:N] + (d-2+eta)*(kappa*cp+xi_cp) + CD*(2-eta)*b
    return R[1:Np+1]

# ── Solver helper ──

from scipy.optimize import least_squares

def _try_solve(fp_func, x0, param, Np):
    """Try LM first, then fsolve fallback."""
    # LM
    try:
        result = least_squares(fp_func, x0, args=(param, Np),
                               method='lm', max_nfev=20000,
                               ftol=1e-12, xtol=1e-12)
        if result.cost < 1e-10 and result.x[0] > 0 and result.x[1] > 0:
            return result.x
    except: pass
    # fsolve fallback
    try:
        sol, info, ier, _ = fsolve(fp_func, x0, args=(param, Np),
                                    full_output=True, maxfev=20000)
        if ier == 1 and np.max(np.abs(info['fvec'])) < 1e-8 and sol[0] > 0 and sol[1] > 0:
            return sol
    except: pass
    return None

# ── Progressive solver ──

def solve_progressive(fp_func, param, max_Np=10, label=""):
    """Find WF fixed point, starting from Np=2 and building up."""
    # First: Np=2 by dedicated solver
    if label == "T":
        sol2 = solve_T_np2(param)
    else:
        # Isotropic Np=2
        sol2 = None
        best_r = 1e30
        for kf in [.005,.01,.03,.05,.08,.1,.3,.5,1,2,5]:
            for lf in [.05,.1,.5,1,3,5,8,10,15,30]:
                for e0 in [.001,.01,.03,.05]:
                    try:
                        def fp2(x): 
                            k,l2,eta = x
                            if k<=0 or l2<=0: return [1e10]*3
                            VD=1.0/(2**(param+1)*np.pi**(param/2)*G(param/2))
                            CD=cd_iso(param); w=2*k*l2
                            return [
                                -(param-2+eta)*k+3*CD*(2-eta)/(1+w)**2,
                                (param-4+2*eta)*l2+18*CD*(2-eta)*l2**2/(1+w)**3,
                                eta-16*VD/param*k*l2**2/(1+w)**4
                            ]
                        s,info,ier,_ = fsolve(fp2,[kf,lf,e0],full_output=True,maxfev=5000)
                        if ier==1 and s[0]>1e-10 and s[1]>1e-6 and 0<=s[2]<.5:
                            r = np.max(np.abs(info['fvec']))
                            if r<1e-10 and r<best_r: best_r=r; sol2=tuple(s)
                    except: pass
        
    if sol2 is None:
        return None
    
    k, l2, eta = sol2
    results = {}
    results[2] = {"kappa":k, "lam2":l2, "eta":eta, "params":np.array([k,l2])}
    
    cur = np.array([k, l2])
    for Np in range(3, max_Np+1):
        new_p = np.zeros(Np)
        new_p[:len(cur)] = cur
        
        fp = fp_T_general if label == "T" else fp_iso_general
        sol = _try_solve(fp, new_p, param, Np)
        
        if sol is None:
            # Perturbation retry
            for lam_init in [0.01, -0.01, 0.1, -0.1, 1.0, -1.0]:
                trial = new_p.copy()
                trial[Np-1] = lam_init * abs(new_p[1])
                sol = _try_solve(fp, trial, param, Np)
                if sol is not None:
                    break
        
        if sol is not None:
            ww = 2*sol[0]*sol[1]
            if label == "T":
                CE = C_eta_T(param)
                eta_s = CE * sol[0]*sol[1]**2/(1+ww)**4
            else:
                VD = 1.0/(2**(param+1)*np.pi**(param/2)*G(param/2))
                eta_s = 16*VD/param * sol[0]*sol[1]**2/(1+ww)**4
            results[Np] = {"kappa":float(sol[0]), "lam2":float(sol[1]),
                           "eta":float(eta_s), "params":sol.copy(), "res":"ok"}
            cur = sol.copy()
        else:
            prev = results[max(results.keys())]
            pp = prev["params"]
            padded = np.zeros(Np); padded[:len(pp)] = pp
            results[Np] = {**{k:v for k,v in prev.items() if k!="params"},
                           "params": padded, "stale": True}
    
    return results

# ── Stability analysis ──

def stability(fp_func, params, param, Np):
    """Critical exponents from PHYSICAL stability matrix M = T · J_R.
    
    R[j] (Taylor coefficients of dt u) are NOT dt(lam_j).
    Physical flows:
      dt kappa   = -R[1]/lam2
      dt lam_j   = j!*R[j] - (lam_{j+1}/lam2)*R[1]   (j=2..Np)
    T matrix encodes this.
    """
    h = 1e-5
    params = np.array(params, dtype=float)
    
    # For Np=2 with fp_T_np2: params=[k,l2,eta], 3 equations
    # We handle this specially: take 3x3 Jacobian, no T-matrix needed
    # (the equations are already in physical form)
    if Np == 2 and len(params) == 3:
        f0 = np.array(fp_func(params, param))
        J = np.zeros((3, 3))
        for j in range(3):
            xp = params.copy()
            step = h * max(abs(xp[j]), 1e-6)
            xp[j] += step
            fp = np.array(fp_func(xp, param))
            J[:, j] = (fp - f0) / step
        eigs = np.linalg.eigvals(-J)
        th = sorted(np.real(eigs), reverse=True)
        nu = 1.0/th[0] if th[0] > 0.01 else None
        omega = -th[1] if len(th) > 1 and th[1] < 0 else None
        gp = 2*nu - 1 if nu and nu > 0.5 else None
        return {"nu": nu, "omega": omega, "gamma_phi": gp, "thetas": th[:4]}
    
    # General case: fp_T_general with params=[kappa, lam2, ..., lam_Np]
    # (Np variables, Np residuals R[1..Np])
    n_phys = len(params)
    f0 = np.array(fp_func(params, param, Np))
    if len(f0) != n_phys:
        return {"nu": None, "omega": None, "gamma_phi": None}
    
    # J_R: Jacobian of R[1..Np] wrt (kappa, lam2, ...)
    J_R = np.zeros((n_phys, n_phys))
    for j in range(n_phys):
        xp = params.copy()
        step = h * max(abs(xp[j]), 1e-6)
        xp[j] += step
        fp = np.array(fp_func(xp, param, Np))
        J_R[:, j] = (fp - f0) / step
    
    # T matrix: maps R[1..Np] -> dt(kappa, lam2, ..., lam_Np)
    # params = [kappa, lam2, lam3, ..., lam_Np]
    lam2 = params[1]
    T = np.zeros((n_phys, n_phys))
    T[0, 0] = -1.0 / lam2  # dt kappa = -R[1]/lam2
    for i in range(1, n_phys):
        j = i + 1  # coupling index lam_j
        fac = 1.0
        for kk in range(2, j + 1): fac *= kk  # j!
        T[i, i] = fac
        # Correction: -lam_{j+1}/lam2
        if i + 1 < n_phys:
            lam_next = params[i + 1]
        else:
            lam_next = 0.0  # truncation
        T[i, 0] = -lam_next / lam2
    
    M = T @ J_R
    if np.any(np.isnan(M)) or np.any(np.isinf(M)):
        return {"nu": None, "omega": None, "gamma_phi": None}
    eigs = np.linalg.eigvals(-M)
    th = sorted(np.real(eigs), reverse=True)
    nu = 1.0/th[0] if th[0] > 0.01 else None
    omega = -th[1] if len(th) > 1 and th[1] < 0 else None
    gp = 2*nu - 1 if nu and nu > 0.5 else None
    return {"nu": nu, "omega": omega, "gamma_phi": gp, "thetas": th[:4]}

# ── Main ──

def main():
    print("="*70)
    print("P-V.7 v11: T-projection FRG + progressive Np")
    print("="*70)
    
    # 1. 3D Ising benchmark
    print("\n--- 3D Ising (d=3): Np convergence ---")
    print(f"  {'Np':>4} | {'eta':>9} | {'nu':>8} | {'omega':>8} | {'gPhi':>8}")
    print("  "+"-"*50)
    
    res_iso = solve_progressive(fp_iso_general, 3.0, max_Np=10, label="iso")
    if res_iso:
        for Np in sorted(res_iso.keys()):
            r = res_iso[Np]
            if r.get("stale"):
                sa = {"nu":None, "omega":None, "gamma_phi":None}
            else:
                p = r["params"]
                sa = stability(fp_iso_general, p, 3.0, Np)
            nu_s = f"{sa['nu']:.4f}" if sa.get('nu') else "---"
            om_s = f"{sa['omega']:.4f}" if sa.get('omega') else "---"
            gp_s = f"{sa['gamma_phi']:.4f}" if sa.get('gamma_phi') else "---"
            print(f"  {Np:4d} | {r['eta']:9.6f} | {nu_s:>8} | {om_s:>8} | {gp_s:>8}")
    
    # 2. T-projection: n scan at Np=2
    print(f"\n--- T-projection: n scan (Np=2) ---")
    print(f"  {'n':>6} | {'kappa':>8} | {'lam2':>8} | {'eta':>9} | {'nu':>7} | {'gPhi':>7}")
    print("  "+"-"*60)
    
    for n in [4.5, 4.0, 3.5, 3.0, 2.78, 2.5]:
        sol = solve_T_np2(n)
        if sol:
            k,l2,eta = sol
            sa = stability(fp_T_np2, list(sol), n, 2)
            nu_s = f"{sa['nu']:.4f}" if sa.get('nu') else "---"
            gp_s = f"{sa['gamma_phi']:.4f}" if sa.get('gamma_phi') else "---"
            print(f"  {n:6.2f} | {k:8.5f} | {l2:8.3f} | {eta:9.6f} | {nu_s:>7} | {gp_s:>7}")
        else:
            print(f"  {n:6.2f} | {'---':>8} | {'---':>8} | {'---':>9} | {'---':>7} | {'---':>7}")
    
    # 3. KEY: n=2.78 progressive Np
    print(f"\n--- KEY: n=2.78 progressive Np convergence ---")
    print(f"  {'Np':>4} | {'eta':>9} | {'kappa':>8} | {'lam2':>8} | {'nu':>8} | {'gPhi':>8}")
    print("  "+"-"*55)
    
    res_278 = solve_progressive(fp_T_general, 2.78, max_Np=10, label="T")
    key_results = []
    if res_278:
        for Np in sorted(res_278.keys()):
            r = res_278[Np]
            stale = r.get("stale", False)
            if stale:
                sa = {"nu":None, "gamma_phi":None}
            elif Np == 2:
                sa = stability(fp_T_np2, [r['kappa'],r['lam2'],r['eta']], 2.78, 2)
            else:
                sa = stability(fp_T_general, r["params"], 2.78, Np)
            nu_s = f"{sa['nu']:.4f}" if sa.get('nu') else "---"
            gp_s = f"{sa['gamma_phi']:.4f}" if sa.get('gamma_phi') else "---"
            stale_mark = " *" if stale else ""
            print(f"  {Np:4d} | {r['eta']:9.6f} | {r['kappa']:8.5f} | "
                  f"{r['lam2']:8.3f} | {nu_s:>8} | {gp_s:>8}{stale_mark}")
            key_results.append({"Np": Np, "eta": r['eta'], "nu": sa.get('nu'),
                                "gamma_phi": sa.get('gamma_phi'), "stale": stale})
    
    # 4. Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"  Target: gamma_Phi = 0.86 at n_eff = 2.78")
    print(f"  1-loop upper bound: gamma_Phi = 0.129")
    
    if key_results:
        valid = [r for r in key_results if r.get('gamma_phi') and r['gamma_phi'] > 0]
        if valid:
            best = max(valid, key=lambda r: r['Np'])
            print(f"  Best FRG (Np={best['Np']}): gamma_Phi = {best['gamma_phi']:.4f}")
            print(f"  Ratio to target: {best['gamma_phi']/0.86:.2f}")
        else:
            print("  No valid gamma_Phi obtained (nu < 0.5 at all Np)")
            print("  This indicates gamma_Phi = 2*nu - 1 formula may be inappropriate")
            print("  for the T-projected theory. Alternative: gamma_Phi from vertex")
    
    # Save
    with open("frg_results_v11.json", "w", encoding="utf-8") as f:
        json.dump(key_results, f, indent=2, default=str)
    
    print("\nDone.")

if __name__ == "__main__":
    main()
