"""
FRG eta coefficient diagnostic
===============================
Given literature 3D Ising LPA' values:
  kappa ~ 0.0781, lambda2 ~ 9.066, eta ~ 0.040, nu ~ 0.624
  
Determine the correct coefficient A in:
  eta = A * kappa * lambda2^2 / (1 + 2*kappa*lambda2)^4

Also check the kappa and lambda equations.
"""
import numpy as np
from scipy.special import gamma as Gamma

def v_d(d):
    return 1.0 / (2**(d+1) * np.pi**(d/2) * Gamma(d/2))

d = 3.0
vd = v_d(d)
print(f"v_d({d}) = {vd:.8f}")
print(f"1/(8*pi^2) = {1/(8*np.pi**2):.8f}")
print(f"Ratio: {vd / (1/(8*np.pi**2)):.6f}")

print("\n" + "="*60)
print("REVERSE ENGINEERING: What coefficient reproduces eta=0.040?")
print("="*60)

# Literature values for 3D Ising LPA' with Litim regulator
# From Litim (2002), Delamotte lectures, Canet PhD thesis
for label, kappa, lam2, eta_lit in [
    ("Litim 2002",      0.0781, 9.066, 0.040),
    ("Canet et al",     0.078,  9.0,   0.039),
    ("Typical LPA'",    0.076,  9.2,   0.042),
]:
    w = 2*kappa*lam2
    
    # eta = A * kappa * lam2^2 / (1+w)^4
    A_needed = eta_lit * (1+w)**4 / (kappa * lam2**2)
    
    # Compare with various candidate coefficients
    c_16vd_d = 16*vd/d   # = 16/(8*pi^2) / 3 = 2/(3*pi^2)
    c_36vd_d = 36*vd/d
    c_4vd_d = 4*vd/d
    c_8vd_d = 8*vd/d
    c_2_d = 2.0 / d * vd  # = cd(d)
    
    print(f"\n--- {label}: kappa={kappa}, lam2={lam2}, eta={eta_lit}, w={w:.3f} ---")
    print(f"  A needed to match eta: {A_needed:.6f}")
    print(f"  16*vd/d = {c_16vd_d:.6f}  (ratio: {A_needed/c_16vd_d:.3f})")
    print(f"  36*vd/d = {c_36vd_d:.6f}  (ratio: {A_needed/c_36vd_d:.3f})")
    print(f"   4*vd/d = {c_4vd_d:.6f}  (ratio: {A_needed/c_4vd_d:.3f})")
    print(f"   8*vd/d = {c_8vd_d:.6f}  (ratio: {A_needed/c_8vd_d:.3f})")
    print(f"   2*vd/d = {c_2_d:.6f}   (ratio: {A_needed/c_2_d:.3f})")

print("\n" + "="*60)
print("FULL SYSTEM CHECK: kappa and lambda equations")
print("="*60)

for A_factor_label, A_factor in [("16vd/d", 16*vd/d), ("36vd/d", 36*vd/d), 
                                   ("4vd/d", 4*vd/d), ("8vd/d", 8*vd/d)]:
    print(f"\n--- eta = {A_factor_label} * kappa*lam2^2/(1+w)^4 ---")
    
    # Self-consistent solution
    from scipy.optimize import fsolve
    
    def fp(x, _d, _A):
        k, l2 = x
        if k <= 0 or l2 <= 0: return [1e10, 1e10]
        w = 2*k*l2
        eta = _A * k * l2**2 / (1+w)**4
        # c_d factor in potential flow: includes (2-eta) factor?
        # Two conventions:
        # (i)  CT = (2/d)*vd*(2-eta)  [Berges-Tetradis-Wetterich]
        # (ii) CT = (2/d)*vd*(1-eta/(d+2))  [Litim optimized]
        #
        # The (2-eta) factor comes from dt R_k containing a Z_k term
        # For Litim: dt R_k = Z_k * [2*k^2 - eta*(k^2-q^2)] * theta(k^2-q^2)
        # Integrating: the (2-eta) factor is exact for Litim
        CT = (2.0/_d)*vd*(2-eta)
        
        eq1 = -(_d-2+eta)*k + 3*CT/(1+w)**2
        eq2 = (_d-4+2*eta)*l2 + 18*CT*l2**2/(1+w)**3
        return [eq1, eq2]
    
    for k0, l0 in [(0.08, 9.0), (0.05, 10.0), (0.1, 8.0), (0.03, 12.0)]:
        try:
            sol, info, ier, _ = fsolve(fp, [k0, l0], args=(d, A_factor), full_output=True)
            if ier == 1 and sol[0] > 0 and sol[1] > 0:
                res = np.max(np.abs(info['fvec']))
                if res < 1e-10:
                    k, l2 = sol
                    w = 2*k*l2
                    eta = A_factor * k * l2**2 / (1+w)**4
                    nu = 1/(2-eta)
                    print(f"    kappa={k:.5f}, lam2={l2:.4f}, eta={eta:.5f}, "
                          f"nu_approx={nu:.4f}, w={w:.4f}")
                    break
        except: pass
    else:
        print(f"    No solution found")

# Also check: what if cd(d) should be (2/d)*vd withOUT the (2-eta)?
print("\n--- Checking: CT = (2/d)*vd (no (2-eta) factor) ---")
def fp_noeta(x, _d, _A):
    k, l2 = x
    if k <= 0 or l2 <= 0: return [1e10, 1e10]
    w = 2*k*l2
    eta = _A * k * l2**2 / (1+w)**4
    CT = (2.0/_d)*vd  # No (2-eta)
    eq1 = -(_d-2+eta)*k + 3*CT/(1+w)**2
    eq2 = (_d-4+2*eta)*l2 + 18*CT*l2**2/(1+w)**3
    return [eq1, eq2]

for A_factor_label, A_factor in [("16vd/d", 16*vd/d), ("36vd/d", 36*vd/d)]:
    print(f"\n  {A_factor_label}:")
    for k0, l0 in [(0.08, 9.0), (0.05, 10.0), (0.1, 8.0), (0.03, 12.0)]:
        try:
            sol, info, ier, _ = fsolve(fp_noeta, [k0, l0], args=(d, A_factor), full_output=True)
            if ier == 1 and sol[0] > 0 and sol[1] > 0:
                res = np.max(np.abs(info['fvec']))
                if res < 1e-10:
                    k, l2 = sol
                    w = 2*k*l2
                    eta = A_factor * k * l2**2 / (1+w)**4
                    print(f"    kappa={k:.5f}, lam2={l2:.4f}, eta={eta:.5f}, w={w:.4f}")
                    break
        except: pass
    else:
        print(f"    No solution found")

print("\n\nDone.")
