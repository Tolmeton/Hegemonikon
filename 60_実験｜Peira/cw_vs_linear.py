"""
CW 版 U(Θ) を用いた α-Θ 結合系の 2D 完全解
==============================================
線形近似 U(Θ) = -μ²Θ + ν²Θ²/2 を
Coleman-Weinberg: U(Θ) = BΘ⁴(2lnΘ - 1/2) に置き換え。

B = 3g⁴/(64π²) — SU(2) の 1ループ有効ポテンシャル
"""

import numpy as np
from scipy import sparse
from scipy.sparse import linalg as splinalg
import os

# === パラメータ ===
LAMBDA_GAMMA = 3.0
KAPPA = 1.0
G_GAUGE = 0.65        # SU(2) 結合定数
B_CW = 3 * G_GAUGE**4 / (64 * np.pi**2)  # CW 係数
THETA_VEV = np.exp(-0.25)  # CW の VEV: e^{-1/4} ≈ 0.779

N_GRID = 45
EPS_BDRY = 0.02
MAX_ITER = 500
DAMPING = 0.15  # やや小さめで安定性確保

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- CW ポテンシャル ---
def U_cw(theta):
    """U(Θ) = BΘ⁴(2lnΘ - 1/2) for Θ > 0"""
    th = np.maximum(theta, 1e-15)
    return B_CW * th**4 * (2*np.log(th) - 0.5)

def dU_cw(theta):
    """U'(Θ) = BΘ³(8lnΘ + 2)"""
    th = np.maximum(theta, 1e-15)
    return B_CW * th**3 * (8*np.log(th) + 2)

def d2U_cw(theta):
    """U''(Θ) = BΘ²(24lnΘ + 26)"""
    th = np.maximum(theta, 1e-15)
    return B_CW * th**2 * (24*np.log(th) + 26)

# --- 線形近似ポテンシャル (比較用) ---
MU2_LIN = 1.0; NU2_LIN = 2.0
def dU_lin(theta):
    return -MU2_LIN + NU2_LIN * theta
def d2U_lin(theta):
    return NU2_LIN * np.ones_like(theta)


def build_simplex_grid(n, eps):
    h = 1.0 / n
    points, indices = [], {}
    idx = 0
    for i in range(n + 1):
        for j in range(n + 1 - i):
            p1, p2 = i * h, j * h
            p3 = 1.0 - p1 - p2
            if p1 >= eps and p2 >= eps and p3 >= eps:
                points.append((p1, p2)); indices[(i, j)] = idx; idx += 1
    return np.array(points), indices, h


def build_laplacian_neumann(points, indices, h):
    n_pts = len(points)
    rows, cols, vals = [], [], []
    for (gi, gj), idx in indices.items():
        p1, p2 = points[idx]
        gi11 = p1 * (1 - p1); gi22 = p2 * (1 - p2); gi12 = -p1 * p2
        get = lambda di, dj: indices.get((gi+di, gj+dj), idx)
        idx_r, idx_l = get(1,0), get(-1,0)
        idx_u, idx_d = get(0,1), get(0,-1)
        idx_ru, idx_ld = get(1,1), get(-1,-1)
        idx_rd, idx_lu = get(1,-1), get(-1,1)
        c11 = gi11/(h*h); c22 = gi22/(h*h); c12 = gi12/(2*h*h)
        rows.extend([idx]*3); cols.extend([idx_r, idx_l, idx]); vals.extend([c11, c11, -2*c11])
        rows.extend([idx]*3); cols.extend([idx_u, idx_d, idx]); vals.extend([c22, c22, -2*c22])
        rows.extend([idx]*4); cols.extend([idx_ru, idx_ld, idx_rd, idx_lu])
        vals.extend([c12, c12, -c12, -c12])
        g1 = (1-2*p1)/2; g2 = (1-2*p2)/2
        rows.extend([idx]*2); cols.extend([idx_r, idx_l]); vals.extend([g1/(2*h), -g1/(2*h)])
        rows.extend([idx]*2); cols.extend([idx_u, idx_d]); vals.extend([g2/(2*h), -g2/(2*h)])
    return sparse.csr_matrix((vals, (rows, cols)), shape=(n_pts, n_pts))


def solve_coupled(use_cw=True, label="CW"):
    points, indices, h = build_simplex_grid(N_GRID, EPS_BDRY)
    n_pts = len(points)
    L = build_laplacian_neumann(points, indices, h)
    
    # 初期条件
    alpha = np.array([2.0*(1.0-p[0]) for p in points])
    theta = np.full(n_pts, THETA_VEV if use_cw else MU2_LIN/NU2_LIN)
    x = np.concatenate([alpha, theta])
    
    for it in range(MAX_ITER):
        a, th = x[:n_pts], x[n_pts:]
        e_th = np.exp(-np.minimum(th, 20.0))
        phi = 1 - e_th
        
        # 残差
        F_a = L @ a - LAMBDA_GAMMA * a**2 * phi
        if use_cw:
            F_th = KAPPA*(L@th) - (LAMBDA_GAMMA/3)*a**3*e_th + dU_cw(th)
        else:
            F_th = KAPPA*(L@th) - (LAMBDA_GAMMA/3)*a**3*e_th + dU_lin(th)
        
        F = np.concatenate([F_a, F_th])
        res = np.linalg.norm(F)
        if it % 50 == 0:
            print(f"  [{label}] Iter {it:3d}: |F|={res:.2e}, "
                  f"a=[{a.min():.2f},{a.max():.2f}], th=[{th.min():.3f},{th.max():.3f}]")
        if res < 1e-4:
            print(f"  [{label}] Converged at iter {it}, |F|={res:.2e}")
            break
        
        # Jacobian
        diag_aa = -2*LAMBDA_GAMMA*a*phi
        diag_ath = -LAMBDA_GAMMA*a**2*e_th
        diag_tha = -(LAMBDA_GAMMA)*a**2*e_th
        if use_cw:
            diag_thth = (LAMBDA_GAMMA/3)*a**3*e_th + d2U_cw(th)
        else:
            diag_thth = (LAMBDA_GAMMA/3)*a**3*e_th + d2U_lin(th)
        
        J = sparse.bmat([
            [L + sparse.diags(diag_aa), sparse.diags(diag_ath)],
            [sparse.diags(diag_tha), KAPPA*L + sparse.diags(diag_thth)]
        ], format='csr')
        
        try:
            dx = splinalg.spsolve(J, -F)
        except:
            break
        x += DAMPING * dx
        x[:n_pts] = np.maximum(x[:n_pts], 0.01)
        x[n_pts:] = np.maximum(x[n_pts:], 1e-10)
    
    return points, indices, x[:n_pts], x[n_pts:]


def main():
    print("=" * 60)
    print("CW U(Th) vs Linear U(Th) comparison")
    print(f"  B_CW = {B_CW:.6f}, Th_VEV = {THETA_VEV:.4f}")
    print("=" * 60)
    
    print("\n--- CW version ---")
    pts_cw, idx_cw, a_cw, th_cw = solve_coupled(use_cw=True, label="CW")
    
    print("\n--- Linear version ---")
    pts_lin, idx_lin, a_lin, th_lin = solve_coupled(use_cw=False, label="Lin")
    
    print("\n=== Comparison ===")
    print(f"  CW:  alpha=[{a_cw.min():.3f},{a_cw.max():.3f}]  theta=[{th_cw.min():.4f},{th_cw.max():.4f}]")
    print(f"  Lin: alpha=[{a_lin.min():.3f},{a_lin.max():.3f}]  theta=[{th_lin.min():.4f},{th_lin.max():.4f}]")
    print(f"  CW  Theta mean={th_cw.mean():.4f}, std={th_cw.std():.4f}, CV={th_cw.std()/th_cw.mean():.3f}")
    print(f"  Lin Theta mean={th_lin.mean():.4f}, std={th_lin.std():.4f}, CV={th_lin.std()/th_lin.mean():.3f}")
    
    # --- Plot ---
    try:
        import matplotlib; matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.tri as mtri
        
        fig, axes = plt.subplots(2, 3, figsize=(16, 10))
        for row, (pts, a, th, lbl) in enumerate([(pts_cw, a_cw, th_cw, "CW"), (pts_lin, a_lin, th_lin, "Linear")]):
            p1, p2 = pts[:,0], pts[:,1]
            tri = mtri.Triangulation(p1, p2)
            p3m = 1-np.mean(p1[tri.triangles],1)-np.mean(p2[tri.triangles],1)
            tri.set_mask(p3m < 0.01)
            
            axes[row,0].tricontourf(tri, a, levels=25, cmap='magma')
            axes[row,0].set_title(f'{lbl}: alpha'); axes[row,0].set_aspect('equal')
            
            axes[row,1].tricontourf(tri, th, levels=25, cmap='inferno')
            axes[row,1].set_title(f'{lbl}: Theta'); axes[row,1].set_aspect('equal')
            
            force2 = np.zeros(len(pts))
            for (gi,gj), idx in idx_cw.items():
                pp1, pp2 = pts[idx]
                gi11=pp1*(1-pp1); gi22=pp2*(1-pp2); gi12=-pp1*pp2
                h = 1.0/N_GRID
                def diff(arr, di, dj):
                    i2 = idx_cw.get((gi+di,gj+dj), idx); i1 = idx_cw.get((gi-di,gj-dj), idx)
                    if i2!=idx and i1!=idx: return (arr[i2]-arr[i1])/(2*h)
                    elif i2!=idx: return (arr[i2]-arr[idx])/h
                    elif i1!=idx: return (arr[idx]-arr[i1])/h
                    return 0.0
                dt1, dt2 = diff(th,1,0), diff(th,0,1)
                force2[idx] = np.sqrt(max(0, gi11*dt1**2+2*gi12*dt1*dt2+gi22*dt2**2))
            axes[row,2].tricontourf(tri, KAPPA*force2, levels=25, cmap='plasma')
            axes[row,2].set_title(f'{lbl}: 2nd Force'); axes[row,2].set_aspect('equal')
        
        plt.tight_layout()
        path = os.path.join(OUT_DIR, "cw_vs_linear.png")
        plt.savefig(path, dpi=150)
        print(f"\nSaved: {path}")
    except Exception as e:
        print(f"Plot error: {e}")


if __name__ == '__main__':
    main()
