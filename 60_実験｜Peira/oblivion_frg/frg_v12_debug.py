"""
P-V.7 v12: T-projection FRG — debugged solver + stability
============================================================
Fixes from v11:
  1. Progressive solver: multi-start perturbation at each Np level
  2. Stability analysis: central differences + correct sign convention
  3. Beta-function formulation for proper critical exponents

Physics: same as v10/v11.
  - T-projection: physical dim = n, loop integrals get angular suppression
  - NOT d=n-1 mapping (which kills broken phase at d<2)
  - Np=2..10 polynomial truncation of LPA' potential
"""
import numpy as np
from scipy.optimize import fsolve
from scipy.special import gamma as G, beta as B
import json, sys, warnings
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

# ── Coefficients ──

def vd(d):
    return 1.0 / (2**(d+1) * np.pi**(d/2) * G(d/2))

def cd_iso(d):
    return 2*vd(d)/d

def C_T(n, eta):
    """T-projection loop coefficient (replaces cd*(2-eta) in isotropic)."""
    v = vd(n)
    om = G(n/2) / (np.sqrt(np.pi) * G((n-1)/2))
    I = (2-eta)*B((n-1)/2, 0.5) + eta*B((n+1)/2, 0.5)
    return (2*v/n) * om * I

def C_eta_T(n):
    """T-projection eta coefficient with sin^4 angular suppression."""
    v = vd(n)
    om = G(n/2) / (np.sqrt(np.pi) * G((n-1)/2))
    return 16*v/n * om * B((n+3)/2, 0.5)

# ── Np=2 closed-form equations ──

def fp_iso_2(x, d):
    k, l2, eta = x
    if k <= 0 or l2 <= 0: return [1e10]*3
    CD = cd_iso(d); VD = vd(d)
    w = 2*k*l2
    return [
        -(d-2+eta)*k + 3*CD*(2-eta)/(1+w)**2,
        (d-4+2*eta)*l2 + 18*CD*(2-eta)*l2**2/(1+w)**3,
        eta - 16*VD/d * k*l2**2/(1+w)**4,
    ]

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

def multi_solve_2(fp_func, param):
    """Multi-start Np=2 solver."""
    best, best_r = None, 1e30
    for kf in [.005,.01,.02,.05,.08,.1,.2,.5,1,2,5,10,30]:
        for lf in [.05,.1,.3,.5,1,2,5,8,10,20,50,100]:
            for e0 in [.001,.005,.01,.03,.05,.1]:
                try:
                    sol,info,ier,_ = fsolve(fp_func,[kf,lf,e0],
                        args=(param,),full_output=True,maxfev=5000)
                    if ier==1 and sol[0]>1e-10 and sol[1]>1e-6 and 0<=sol[2]<0.5:
                        r = np.max(np.abs(info['fvec']))
                        if r < 1e-10 and r < best_r:
                            best_r = r; best = sol.copy()
                except: pass
    return best

# ── General Np: Taylor coefficient flow ──

def build_flow(params, dim, Np, mode='iso'):
    """
    Build flow residuals R[1..Np] for Taylor coefficients c_1..c_Np.
    
    params = [kappa, lam2, lam3, ..., lam_Np]  (length Np)
    dim: either d (isotropic) or n (T-projection)
    mode: 'iso' or 'T'
    """
    kappa = params[0]
    lams = params[1:]  # lam2, lam3, ..., lam_Np
    if kappa <= 0 or lams[0] <= 0:
        return np.full(Np, 1e10)
    l2 = lams[0]; w = 2*kappa*l2
    if 1+w <= 0: return np.full(Np, 1e10)
    
    # Compute eta self-consistently
    if mode == 'T':
        CE = C_eta_T(dim)
        eta = CE * kappa * l2**2 / (1+w)**4
        CT = C_T(dim, eta)
        d_eff = dim  # physical dimension = n
    else:
        VD = vd(dim)
        eta = 16*VD/dim * kappa * l2**2 / (1+w)**4
        CT = cd_iso(dim) * (2-eta)
        d_eff = dim
    
    if eta < 0 or eta > 0.5: return np.full(Np, 1e10)
    
    # Taylor coefficients of u around kappa
    N = Np + 3  # working array size
    c = np.zeros(N)
    for j in range(2, min(Np+1, N)):
        idx = j - 2
        if idx < len(lams):
            fac = 1.0
            for m in range(2, j+1): fac *= m
            c[j] = lams[idx] / fac
    
    # u', u'' as Taylor series
    cp = np.zeros(N)
    for j in range(N-1): cp[j] = c[j+1]*(j+1)
    cpp = np.zeros(N)
    for j in range(N-2): cpp[j] = cp[j+1]*(j+1)
    
    # g(xi) = u'(kappa+xi) + 2*(kappa+xi)*u''(kappa+xi)
    xi_cpp = np.zeros(N)
    for j in range(1, min(N, len(cpp))): xi_cpp[j] = cpp[j-1]
    P = cp + 2*kappa*cpp + 2*xi_cpp
    
    # D(xi) = 1 + g(xi)
    D = P.copy(); D[0] += 1.0
    
    # b(xi) = 1/D(xi) via power series inversion
    if abs(D[0]) < 1e-30: return np.full(Np, 1e10)
    b = np.zeros(N)
    b[0] = 1.0/D[0]
    for j in range(1, N):
        s = 0.0
        for m in range(1, j+1):
            if m < N: s += D[m] * b[j-m]
        b[j] = -s / D[0]
    if np.any(np.isnan(b)): return np.full(Np, 1e10)
    
    # (kappa + xi)*u'(kappa+xi)
    xi_cp = np.zeros(N)
    for j in range(1, min(N, len(cp))): xi_cp[j] = cp[j-1]
    
    # Flow: dt u = -d*u + (d-2+eta)*rho*u' + CT*b(xi)
    R = -d_eff*c[:N] + (d_eff-2+eta)*(kappa*cp + xi_cp) + CT*b
    
    return R[1:Np+1]

# ── Progressive solver ──

def solve_progressive(dim, max_Np=10, mode='iso', verbose=False):
    """
    Find Wilson-Fisher FP progressively from Np=2 to max_Np.
    Each level seeds from the previous solution.
    """
    # Step 1: Solve Np=2
    if mode == 'T':
        sol2 = multi_solve_2(fp_T_2, dim)
    else:
        sol2 = multi_solve_2(fp_iso_2, dim)
    
    if sol2 is None:
        if verbose: print(f"  No Np=2 FP found (dim={dim:.2f}, mode={mode})")
        return None
    
    k, l2, eta = sol2
    w = 2*k*l2
    results = {}
    results[2] = {"kappa": k, "lam2": l2, "eta": eta, "w": w,
                   "params": np.array([k, l2]), "converged": True}
    
    if verbose:
        print(f"  Np=2: kappa={k:.5f} lam2={l2:.4f} eta={eta:.6f} w={w:.4f}")
    
    cur = np.array([k, l2])
    
    for Np in range(3, max_Np + 1):
        found = False
        best_sol = None
        best_res = 1e30
        
        # Strategy: try multiple perturbations around padded previous solution
        for trial in range(50):
            new_p = np.zeros(Np)
            new_p[:len(cur)] = cur.copy()
            
            if trial > 0:
                # Perturb: random noise on higher couplings + small noise on lower
                scale = max(abs(cur[1]), 1.0)
                for j in range(len(cur), Np):
                    new_p[j] = scale * np.random.randn() * 10**(-(j-1))
                for j in range(len(cur)):
                    new_p[j] *= 1.0 + 0.1 * np.random.randn()
                new_p[0] = abs(new_p[0])
                new_p[1] = abs(new_p[1])
            
            try:
                sol, info, ier, _ = fsolve(
                    build_flow, new_p, args=(dim, Np, mode),
                    full_output=True, maxfev=10000)
                if ier == 1 and sol[0] > 1e-10 and sol[1] > 1e-6:
                    r = np.max(np.abs(info['fvec']))
                    if r < 1e-8 and r < best_res:
                        # Verify eta is physical
                        ww = 2*sol[0]*sol[1]
                        if mode == 'T':
                            CE = C_eta_T(dim)
                            eta_s = CE * sol[0]*sol[1]**2/(1+ww)**4
                        else:
                            eta_s = 16*vd(dim)/dim * sol[0]*sol[1]**2/(1+ww)**4
                        if 0 <= eta_s < 0.5:
                            best_res = r
                            best_sol = sol.copy()
                            found = True
            except: pass
        
        if found:
            cur = best_sol.copy()
            ww = 2*best_sol[0]*best_sol[1]
            if mode == 'T':
                CE = C_eta_T(dim)
                eta_s = CE * best_sol[0]*best_sol[1]**2/(1+ww)**4
            else:
                eta_s = 16*vd(dim)/dim * best_sol[0]*best_sol[1]**2/(1+ww)**4
            results[Np] = {"kappa": float(best_sol[0]), "lam2": float(best_sol[1]),
                           "eta": float(eta_s), "w": float(ww),
                           "params": best_sol.copy(), "converged": True,
                           "res": float(best_res)}
            if verbose:
                print(f"  Np={Np}: kappa={best_sol[0]:.5f} lam2={best_sol[1]:.4f} "
                      f"eta={eta_s:.6f} w={ww:.4f} res={best_res:.1e}")
        else:
            # Stale: carry forward
            prev_Np = max(rr for rr in results if results[rr].get('converged',False))
            prev = results[prev_Np]
            pp = prev["params"]
            padded = np.zeros(Np); padded[:len(pp)] = pp
            results[Np] = {**{kk:vv for kk,vv in prev.items() if kk!='params'},
                           "params": padded, "converged": False}
            if verbose:
                print(f"  Np={Np}: stale (from Np={prev_Np})")
    
    return results

# ── Stability analysis with central differences ──

def stability(fp_func, params, dim, Np, mode='iso'):
    """
    Critical exponents from stability matrix via central finite differences.
    Uses the build_flow function directly.
    """
    n_var = len(params)
    
    def F(x):
        return build_flow(x, dim, Np, mode)
    
    f0 = F(params)
    n_eq = len(f0)
    
    if n_eq != n_var:
        return {"nu": None, "omega": None, "gamma_phi": None}
    
    # Central differences for Jacobian
    J = np.zeros((n_eq, n_var))
    for j in range(n_var):
        h = 1e-6 * max(abs(params[j]), 1e-4)
        xp = params.copy(); xp[j] += h
        xm = params.copy(); xm[j] -= h
        fp = F(xp); fm = F(xm)
        if np.any(np.abs(fp) > 1e8) or np.any(np.abs(fm) > 1e8):
            return {"nu": None, "omega": None, "gamma_phi": None}
        J[:, j] = (fp - fm) / (2*h)
    
    # T-matrix: convert R[1..Np] Jacobian to physical flow Jacobian
    # dt kappa = -R[1]/lam2, dt lam_j = j!*R[j] - (lam_{j+1}/lam2)*R[1]
    lam2 = params[1]
    T = np.zeros((n_var, n_var))
    T[0, 0] = -1.0 / lam2
    for i in range(1, n_var):
        j = i + 1  # coupling index lam_j
        fac = 1.0
        for kk in range(2, j + 1): fac *= kk
        T[i, i] = fac
        if i + 1 < n_var:
            lam_next = params[i + 1]
        else:
            lam_next = 0.0
        T[i, 0] = -lam_next / lam2
    
    M = T @ J
    if np.any(np.isnan(M)) or np.any(np.isinf(M)):
        return {"nu": None, "omega": None, "gamma_phi": None}
    
    try:
        eigs = np.linalg.eigvals(-M)
    except:
        return {"nu": None, "omega": None, "gamma_phi": None}
    
    th = sorted(np.real(eigs), reverse=True)
    nu = 1.0/th[0] if len(th) > 0 and th[0] > 0.1 else None
    omega = -th[1] if len(th) > 1 and th[1] < -0.01 else None
    gamma_phi = 2*nu - 1 if nu and nu > 0.5 else None
    
    return {"nu": nu, "omega": omega, "gamma_phi": gamma_phi,
            "thetas": [float(t) for t in th[:min(5, len(th))]]}

def stability_3eq(fp_func, params, dim):
    """Stability from the 3-equation (kappa, lambda, eta) system."""
    f0 = np.array(fp_func(list(params), dim))
    J = np.zeros((3, 3))
    for j in range(3):
        h = 1e-6 * max(abs(params[j]), 1e-4)
        xp = list(params); xp[j] += h
        xm = list(params); xm[j] -= h
        fp = np.array(fp_func(xp, dim))
        fm = np.array(fp_func(xm, dim))
        J[:, j] = (fp - fm) / (2*h)
    eigs = np.linalg.eigvals(-J)
    th = sorted(np.real(eigs), reverse=True)
    nu = 1.0/th[0] if th[0] > 0.1 else None
    omega = -th[1] if len(th)>1 and th[1]<-0.01 else None
    gp = 2*nu - 1 if nu and nu > 0.5 else None
    return {"nu": nu, "omega": omega, "gamma_phi": gp,
            "thetas": [float(t) for t in th]}

# ── Main ──

def main():
    print("="*70)
    print("P-V.7 v12: T-projection FRG + debugged progressive Np")
    print("="*70)
    
    # ========== PART 1: 3D Ising Benchmark ==========
    print("\n" + "="*70)
    print("PART 1: 3D Ising Benchmark (d=3, N=1)")
    print("  Exact: eta=0.0363, nu=0.6300, omega=0.830")
    print("="*70)
    
    # 1a: Np=2 with 3-equation system
    sol2 = multi_solve_2(fp_iso_2, 3.0)
    if sol2 is not None:
        k, l2, eta = sol2
        sa = stability_3eq(fp_iso_2, sol2, 3.0)
        print(f"\n  Np=2 (3-eq): kappa={k:.5f} lam2={l2:.4f} eta={eta:.6f}")
        print(f"    nu={sa['nu']:.4f}" if sa['nu'] else "    nu=---")
        print(f"    omega={sa['omega']:.4f}" if sa['omega'] else "    omega=---")
        print(f"    thetas={sa['thetas']}")
    
    # 1b: Progressive Np
    print(f"\n  Progressive Np (isotropic d=3):")
    print(f"  {'Np':>4} | {'eta':>9} | {'kappa':>8} | {'lam2':>8} "
          f"| {'nu':>8} | {'omega':>8} | {'gamma':>8}")
    print("  " + "-"*70)
    
    res_iso = solve_progressive(3.0, max_Np=10, mode='iso', verbose=False)
    
    if res_iso:
        for Np in sorted(res_iso.keys()):
            r = res_iso[Np]
            if r.get('converged', False):
                sa = stability(build_flow, r['params'], 3.0, Np, mode='iso')
                nu_s = f"{sa['nu']:.4f}" if sa.get('nu') else "---"
                om_s = f"{sa['omega']:.4f}" if sa.get('omega') else "---"
                gam = sa['nu']*(2-r['eta']) if sa.get('nu') else None
                gam_s = f"{gam:.4f}" if gam else "---"
                tag = ""
            else:
                nu_s = om_s = gam_s = "---"
                tag = " STALE"
            print(f"  {Np:4d} | {r['eta']:9.6f} | {r['kappa']:8.5f} | "
                  f"{r['lam2']:8.4f} | {nu_s:>8} | {om_s:>8} | {gam_s:>8}{tag}")
    
    # ========== PART 2: T-projection scan ==========
    print(f"\n{'='*70}")
    print("PART 2: T-projection (n_c=5, Np=2)")
    print(f"{'='*70}")
    print(f"  {'n':>6} | {'kappa':>8} | {'lam2':>8} | {'eta':>9} "
          f"| {'nu':>7} | {'gPhi':>7}")
    print("  " + "-"*60)
    
    for n in [4.5, 4.0, 3.5, 3.0, 2.78, 2.5]:
        sol = multi_solve_2(fp_T_2, n)
        if sol is not None:
            k, l2, eta = sol
            sa = stability_3eq(fp_T_2, sol, n)
            nu_s = f"{sa['nu']:.4f}" if sa.get('nu') else "---"
            gp_s = f"{sa['gamma_phi']:.4f}" if sa.get('gamma_phi') else "---"
            print(f"  {n:6.2f} | {k:8.5f} | {l2:8.3f} | {eta:9.6f} "
                  f"| {nu_s:>7} | {gp_s:>7}")
        else:
            print(f"  {n:6.2f} | {'---':>8} | {'---':>8} | {'---':>9} "
                  f"| {'---':>7} | {'---':>7}")
    
    # ========== PART 3: KEY — n=2.78 convergence ==========
    print(f"\n{'='*70}")
    print("PART 3: n=2.78 T-projection — progressive Np convergence")
    print(f"{'='*70}")
    
    res_278 = solve_progressive(2.78, max_Np=10, mode='T', verbose=True)
    
    if res_278:
        print(f"\n  Stability analysis:")
        print(f"  {'Np':>4} | {'eta':>9} | {'nu':>8} | {'gPhi':>8} | {'thetas'}")
        print("  " + "-"*60)
        
        for Np in sorted(res_278.keys()):
            r = res_278[Np]
            if r.get('converged', False):
                sa = stability(build_flow, r['params'], 2.78, Np, mode='T')
                nu_s = f"{sa['nu']:.4f}" if sa.get('nu') else "---"
                gp_s = f"{sa['gamma_phi']:.4f}" if sa.get('gamma_phi') else "---"
                th_s = str([f"{t:.3f}" for t in sa.get('thetas',[])])
                print(f"  {Np:4d} | {r['eta']:9.6f} | {nu_s:>8} | {gp_s:>8} | {th_s}")
            else:
                print(f"  {Np:4d} | {r['eta']:9.6f} | {'---':>8} | {'---':>8} | STALE")
    
    # ========== PART 4: n scan at best Np ==========
    print(f"\n{'='*70}")
    print("PART 4: T-projection n-scan (progressive Np)")
    print(f"{'='*70}")
    
    all_results = []
    for n in [4.5, 4.0, 3.5, 3.0, 2.78, 2.5, 2.3]:
        rr = solve_progressive(n, max_Np=8, mode='T', verbose=False)
        if rr:
            best_Np = max(k for k in rr if rr[k].get('converged', False))
            r = rr[best_Np]
            sa = stability(build_flow, r['params'], n, best_Np, mode='T')
            nu_v = sa.get('nu')
            gp_v = sa.get('gamma_phi')
            eps = 5.0 - n
            g1l = (n-2)*eps/(2*(n+1)*(n-1)) if 2<n<5 else 0
            nu_s = f"{nu_v:.4f}" if nu_v else "---"
            gp_s = f"{gp_v:.4f}" if gp_v else "---"
            print(f"  n={n:.2f} (eps={eps:.2f}): Np={best_Np}, eta={r['eta']:.6f}, "
                  f"nu={nu_s:>8}, gPhi={gp_s:>8} (1-loop: {g1l:.4f})")
            all_results.append({"n": n, "eps": eps, "Np": best_Np,
                                "eta": r['eta'], "nu": nu_v, "gamma_phi": gp_v,
                                "gamma_1L": g1l})
        else:
            eps = 5.0 - n
            print(f"  n={n:.2f} (eps={eps:.2f}): No WF FP")
            all_results.append({"n": n, "eps": eps, "gamma_phi": None})
    
    # ========== Summary ==========
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"  Target: gamma_Phi ~= 0.86 at n = 2.78 (eps = 2.22)")
    print(f"  1-loop: gamma_Phi = 0.129")
    
    r278 = [r for r in all_results if r['n'] == 2.78]
    if r278:
        r = r278[0]
        if r.get('gamma_phi') and r['gamma_phi'] > 0:
            print(f"  FRG:   gamma_Phi = {r['gamma_phi']:.4f}")
            print(f"  Ratio: FRG/target = {r['gamma_phi']/0.86:.2f}")
        elif r.get('nu'):
            print(f"  FRG:   nu = {r['nu']:.4f} (< 0.5 → gamma_Phi = 2*nu - 1 < 0)")
            print(f"  -> polynomial truncation insufficient at eps=2.22")
        else:
            print(f"  FRG:   stability analysis inconclusive")
    
    with open("frg_results_v12.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print("\nDone.")

if __name__ == "__main__":
    main()
