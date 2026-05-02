"""
P-V.7: FRG gamma_Phi — v9 (LM solver + projected stability)
=============================================================
Fixes from v6-v8:
  1. Levenberg-Marquardt solver (more robust than fsolve for stiff Np≥4)
  2. Projected Jacobian for nu (η as dependent variable, not free)
  3. Adaptive threshold (1e-6 not 1e-8)
  4. Sequential Np continuation with damped updates
"""
import numpy as np
from scipy.optimize import least_squares, fsolve
from scipy.special import gamma as gamma_func
import sys, warnings
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

def vd(d): return 1.0/(2**(d+1)*np.pi**(d/2)*gamma_func(d/2))
def cd(d): return 2.0*vd(d)/d

# ── Np=2 base solver (v5, verified) ──────────────────────────
def solve_np2(d):
    CD=cd(d)
    def eqs(x):
        k,l,eta=x
        if k<=0 or l<=0: return [1e6]*3
        w=2*k*l; dn=1+w
        return [
            (d-2+eta)*k - 3*CD*(2-eta)/dn**2,
            (4-d-2*eta) - 18*CD*(2-eta)*l/dn**3,
            eta - 8*CD*k*l**2/dn**4
        ]
    best,best_r=None,1e30
    for eta_t in np.linspace(0.001,0.4,40):
        for w_t in np.linspace(0.01,4.0,40):
            dn_t=1+w_t
            l_t=(4-d-2*eta_t)*dn_t**3/(18*CD*(2-eta_t))
            if l_t<=0: continue
            k_t=w_t/(2*l_t)
            if k_t<=0: continue
            try:
                sol,info,ier,_=fsolve(eqs,[k_t,l_t,eta_t],full_output=True)
                if ier==1 and sol[0]>1e-12 and sol[1]>1e-12 and 0<sol[2]<0.5:
                    r=np.max(np.abs(info['fvec']))
                    if r<1e-8 and r<best_r: best_r=r; best=sol.copy()
            except: pass
    return best

# ── Taylor series utilities ──────────────────────────────────
def poly_shift(a, N):
    r=np.zeros(N); r[1:min(N,len(a))]=a[:N-1]; return r

def poly_inv(D, N):
    b=np.zeros(N)
    if abs(D[0])<1e-30: return b*np.nan
    b[0]=1/D[0]
    for j in range(1,N):
        s=0.0
        for m in range(1,min(j+1,len(D))): s+=D[m]*b[j-m]
        b[j]=-s/D[0]
    return b

def eta_formula(k, l2, d):
    w=2*k*l2
    if w<-0.9 or k<=0 or l2<=0: return 0
    return 8*cd(d)*k*l2**2/(1+w)**4

# ── General Np residuals ─────────────────────────────────────
def frg_residuals(params, d, Np):
    """
    params=[kappa, lam2, ..., lam_Np, eta] (Np+1 unknowns)
    Returns Np+1 residuals: R[1..Np] + eta_eq
    """
    k=params[0]; eta_val=params[-1]
    n_lams=Np-1  # number of lambda couplings
    lams=list(params[1:1+n_lams])
    while len(lams)<n_lams: lams.append(0)
    
    if k<=0 or (n_lams>0 and lams[0]<=0):
        return np.full(Np+1,1e10)
    
    CD=cd(d); N=Np+4
    c=np.zeros(N)
    for j in range(2,min(Np+1,N)):
        idx=j-2
        if idx<len(lams):
            fac=1.0
            for kk in range(2,j+1): fac*=kk
            c[j]=lams[idx]/fac
    
    cp=np.zeros(N)
    for j in range(N-1): cp[j]=c[j+1]*(j+1)
    cpp=np.zeros(N)
    for j in range(N-2): cpp[j]=cp[j+1]*(j+1)
    
    P=cp+2*k*cpp+2*poly_shift(cpp,N)
    D=P.copy(); D[0]+=1
    b=poly_inv(D,N)
    if np.any(np.isnan(b)): return np.full(Np+1,1e10)
    
    T1=-d*c[:N]
    rho_cp=k*cp+poly_shift(cp,N)
    T2=(d-2+eta_val)*rho_cp
    T3=CD*(2-eta_val)*b
    R=T1+T2+T3
    
    res=np.zeros(Np+1)
    res[:Np]=R[1:Np+1]
    w=2*k*lams[0]
    res[Np]=eta_val - 8*CD*k*lams[0]**2/(1+w)**4
    return res

# ── Solve general Np using least_squares (LM) ───────────────
def solve_general(d, Np, x0):
    """Solve using Levenberg-Marquardt."""
    # Bounds: kappa>0, lam2>0, others free, 0<eta<0.5
    n=Np+1
    lb=np.full(n,-np.inf); ub=np.full(n,np.inf)
    lb[0]=1e-12; lb[1]=1e-6; lb[-1]=0; ub[-1]=0.5
    
    try:
        result=least_squares(
            frg_residuals, x0, args=(d,Np),
            method='lm', max_nfev=20000,
            ftol=1e-12, xtol=1e-12
        )
        if result.cost < 1e-10 and result.x[0]>0 and result.x[1]>0 and result.x[-1]>0:
            return result.x
    except: pass
    
    # Fallback: try fsolve
    try:
        sol,info,ier,_=fsolve(frg_residuals,x0,args=(d,Np),full_output=True,maxfev=20000)
        if ier==1 and np.max(np.abs(info['fvec']))<1e-6 and sol[0]>0 and sol[1]>0 and sol[-1]>0:
            return sol
    except: pass
    
    return None

# ── Np continuation ──────────────────────────────────────────
def np_continuation(d, Np_max, base2=None):
    """Build solution from Np=2 to Np_max by sequential extension."""
    if base2 is None: base2=solve_np2(d)
    if base2 is None: return None,2
    
    solutions={}
    # Np=2: [k, l2, eta]
    solutions[2]=base2.copy()
    
    for Np in range(3,Np_max+1):
        prev=solutions.get(Np-1)
        if prev is None: break
        
        # Extend: prev=[k,l2,...,lam_{Np-1},eta], new=[k,...,lam_Np,eta]
        x0=np.zeros(Np+1)
        x0[0]=prev[0]          # kappa
        x0[1:len(prev)-1]=prev[1:-1]  # existing lambdas
        x0[len(prev)-1]=0.0    # new lambda = 0
        x0[-1]=prev[-1]        # eta
        
        sol=solve_general(d,Np,x0)
        if sol is not None:
            solutions[Np]=sol
        else:
            # Try with small perturbations of new coupling
            found=False
            for lam_init in [0.01,-0.01,0.1,-0.1,1.0,-1.0]:
                x0_p=x0.copy()
                x0_p[Np-1]=lam_init*x0[1]  # scale relative to lam2
                sol=solve_general(d,Np,x0_p)
                if sol is not None:
                    solutions[Np]=sol; found=True; break
            if not found:
                break
    
    best_Np=max(solutions.keys())
    return solutions[best_Np], best_Np

# ── Physical stability → nu ──────────────────────────────────
def compute_nu(sol, d, Np, debug=False):
    """
    Compute nu from the PHYSICAL stability matrix M = T · J_R.
    
    R[j] = Taylor coeff of ∂_t u(κ+ξ) are NOT dt(lam_j).
    Physical flows:
      dt κ     = −R[1]/λ₂
      dt λ_j   = j!·R[j] − (λ_{j+1}/λ₂)·R[1]   (j=2..Np)
    T matrix encodes this transformation.
    """
    h=1e-5  # larger step for numerical stability
    n_phys=Np
    
    def flow_R(x_phys):
        """Return R[1..Np] with eta self-consistent."""
        eta_c=eta_formula(x_phys[0], x_phys[1], d)
        x_full=np.zeros(Np+1)
        x_full[:Np]=x_phys
        x_full[Np]=eta_c
        res=frg_residuals(x_full, d, Np)
        return res[:Np]  # R[1], R[2], ..., R[Np]
    
    x_phys=sol[:Np]
    
    # Jacobian of R wrt physical params
    J_R=np.zeros((n_phys,n_phys))
    f0=flow_R(x_phys)
    for j in range(n_phys):
        xp=x_phys.copy()
        step=h*max(abs(xp[j]),1e-6)
        xp[j]+=step
        fp=flow_R(xp)
        J_R[:,j]=(fp-f0)/step
    
    # T matrix: maps R[1..Np] → dt(κ, λ₂, ..., λ_Np)
    # x_phys = [κ, λ₂, λ₃, ..., λ_Np]
    # Row 0: dt κ = −R[1]/λ₂ → T[0,0] = −1/λ₂
    # Row i (i≥1): dt λ_{i+1} = (i+1)!·R[i+1] − (λ_{i+2}/λ₂)·R[1]
    #   → T[i,0] = −λ_{i+2}/λ₂,  T[i,i] = (i+1)!
    #   where λ_{i+2} = x_phys[i+1] if i+1 < Np, else 0
    
    lam2 = x_phys[1]
    T = np.zeros((n_phys, n_phys))
    T[0,0] = -1.0/lam2
    for i in range(1, n_phys):
        j = i + 1  # coupling index: λ_j
        fac = 1.0
        for kk in range(2, j+1): fac *= kk  # j!
        T[i,i] = fac
        # Correction from moving κ: −λ_{j+1}/λ₂
        if i+1 < n_phys:
            lam_next = x_phys[i+1]  # λ_{j+1}
        else:
            lam_next = 0.0  # truncation: λ_{Np+1} = 0
        T[i,0] = -lam_next / lam2
    
    # Physical stability matrix
    M = T @ J_R
    eigs = np.linalg.eigvals(-M)
    re = sorted(np.real(eigs), reverse=True)
    
    if debug:
        print(f"    J_R eigs: {sorted(np.real(np.linalg.eigvals(-J_R)),reverse=True)[:4]}")
        print(f"    M eigs:   {re[:4]}")
    
    pos = [e for e in re if e > 0.01]
    if not pos: return None, re[:4]
    nu = 1.0/pos[0]
    return nu, re[:4]

# ── Main ─────────────────────────────────────────────────────
def main():
    print("="*72)
    print("P-V.7: FRG v9 (LM solver + projected stability)")
    print("="*72)
    
    # ─── 1. 3D Ising benchmark: Np convergence ───
    print("\n--- 3D Ising (d=3): Np convergence ---")
    print(f"{'Np':>4} {'kappa':>8} {'lam2':>8} {'lam3':>8} {'eta':>8} {'nu':>7} {'gPhi':>7}")
    print("-"*56)
    
    base3=solve_np2(3.0)
    sols3={}
    if base3 is not None:
        sols3[2]=base3
    
    for Np in range(2,9):
        sol,actual_np=np_continuation(3.0,Np,base3)
        if sol is not None and actual_np==Np:
            sols3[Np]=sol
            dbg = (Np<=3)  # debug first two
            nu,eigs=compute_nu(sol,3.0,Np,debug=dbg)
            gP=2*(nu-0.5) if nu and nu>0.5 else None
            l3=sol[2] if Np>=3 else 0
            if nu:
                print(f"{Np:4d} {sol[0]:8.5f} {sol[1]:8.3f} {l3:8.3f} "
                      f"{sol[-1]:8.5f} {nu:7.4f} {gP:7.4f}" if gP else
                      f"{Np:4d} {sol[0]:8.5f} {sol[1]:8.3f} {l3:8.3f} "
                      f"{sol[-1]:8.5f} {nu:7.4f} {'---':>7}")
            else:
                print(f"{Np:4d} {sol[0]:8.5f} {sol[1]:8.3f} {l3:8.3f} "
                      f"{sol[-1]:8.5f} {'---':>7}")
        else:
            print(f"{Np:4d} fail (reached Np={actual_np})")
    print(f"  Literature: eta=0.0363, nu=0.630")
    
    # ─── 2. d-continuation at each Np ───
    print(f"\n--- d-continuation ---")
    
    for Np_lev in [2, 3, 4, 6, 8]:
        sol_d3, actual = np_continuation(3.0, Np_lev, base3)
        if sol_d3 is None or actual < Np_lev:
            print(f"\n  Np={Np_lev}: cannot start (max Np={actual})")
            continue
        
        print(f"\n  Np={Np_lev}:")
        sol_cur=sol_d3.copy()
        d_cur=3.0
        
        d_targets=[2.8, 2.6, 2.4, 2.2, 2.0, 1.78]
        for d_tgt in d_targets:
            # Small steps
            n_steps=max(3, int(abs(d_cur-d_tgt)/0.02)+1)
            d_path=np.linspace(d_cur,d_tgt,n_steps)
            x_c=sol_cur.copy()
            ok=True
            for ds in d_path[1:]:
                sol_new=solve_general(ds,Np_lev,x_c)
                if sol_new is not None:
                    x_c=sol_new
                else:
                    ok=False; break
            
            if not ok:
                n_eff=d_cur+1
                print(f"    d={d_tgt:.2f}: LOST (WF FP gone at d≈{d_cur:.2f}, n≈{n_eff:.2f})")
                break
            
            sol_cur=x_c; d_cur=d_tgt
            n=d_tgt+1; eps=5-n
            g1l=(n-2)*eps/(2*(n+1)*(n-1)) if 2<n<5 else 0
            nu,_=compute_nu(sol_cur,d_tgt,Np_lev)
            gP=2*(nu-0.5) if nu and nu>0.5 else None
            if gP:
                print(f"    d={d_tgt:.2f} (n={n:.2f}): gPhi={gP:.4f} nu={nu:.4f} eta={sol_cur[-1]:.5f}")
            else:
                print(f"    d={d_tgt:.2f} (n={n:.2f}): no gPhi (nu={nu})")
    
    # ─── 3. Summary ───
    print(f"\n--- Summary ---")
    print(f"  Target: gamma_Phi ≈ 0.86 at n_eff ≈ 2.78 (d=1.78)")
    print(f"  WF FP disappearance dimension d_c(Np) shows whether higher")
    print(f"  truncation extends the reachable regime.")
    
    print("\nDone.")

if __name__=="__main__":
    main()
