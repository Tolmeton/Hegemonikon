"""
忘却場 Θ と非対称性場 α の 2D完全結合解
=============================================
計算_αΘ結合系2D解.md (§8.1) に基づき、Δ² 上で以下の方程式系を解く:
    ∇²α = λγ α² (1 - e^{-Θ})
    κ∇²Θ = (λγ/3) α³ e^{-Θ} - μ² + ν²Θ

変数と次元:
    x = [α₁, ... α_N, Θ₁, ... Θ_N]^T  (2N次元ベクトル)
    F = [F_α, F_Θ]^T                  (2N次元残差)

Jacobian は 2Nx2N の疎行列。
Newton 法 + 減衰で境界条件は Neumann (dα/dn = dΘ/dn = 0)。
"""

import numpy as np
from scipy import sparse
from scipy.sparse import linalg as splinalg
import os

# === パラメータ (v2 §8.1) ===
LAMBDA_GAMMA = 3.0
KAPPA = 1.0
MU2 = 1.0
NU2 = 2.0

N_GRID = 45         # L1 グリッド分割数
EPS_BDRY = 0.02     # シンプレックス境界マージン
MAX_ITER = 300
TOL = 1e-6
DAMPING = 0.2       # Newton 法の減衰係数

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def build_simplex_grid(n, eps):
    h = 1.0 / n
    points = []
    indices = {}
    idx = 0
    for i in range(n + 1):
        for j in range(n + 1 - i):
            p1 = i * h
            p2 = j * h
            p3 = 1.0 - p1 - p2
            if p1 >= eps and p2 >= eps and p3 >= eps:
                points.append((p1, p2))
                indices[(i, j)] = idx
                idx += 1
    return np.array(points), indices, h


def build_laplacian_neumann(points, indices, h):
    """
    Fisher 計量上の Laplacian (Neumann BC)。
    境界に達する差分は「値が同じ」として扱う (= 勾配ゼロ)。
    """
    n_pts = len(points)
    rows, cols, vals = [], [], []
    
    for (gi, gj), idx in indices.items():
        p1, p2 = points[idx]
        p3 = 1.0 - p1 - p2
        
        # 逆計量
        gi11 = p1 * (1 - p1)
        gi22 = p2 * (1 - p2)
        gi12 = -p1 * p2
        
        # Neumann 処理用ヘルパー: グリッド外なら自分の index を返す (勾配0)
        def get_idx(di, dj):
            return indices.get((gi+di, gj+dj), idx)
        
        idx_r = get_idx(1, 0); idx_l = get_idx(-1, 0)
        idx_u = get_idx(0, 1); idx_d = get_idx(0, -1)
        idx_ru = get_idx(1, 1); idx_ld = get_idx(-1, -1)
        idx_rd = get_idx(1, -1); idx_lu = get_idx(-1, 1)
        
        # D2_p1
        c11 = gi11 / (h * h)
        rows.extend([idx, idx, idx])
        cols.extend([idx_r, idx_l, idx])
        vals.extend([c11, c11, -2*c11])
        
        # D2_p2
        c22 = gi22 / (h * h)
        rows.extend([idx, idx, idx])
        cols.extend([idx_u, idx_d, idx])
        vals.extend([c22, c22, -2*c22])
        
        # D2_p1p2 (交差項)
        c12 = gi12 / (2 * h * h)
        rows.extend([idx, idx, idx, idx])
        cols.extend([idx_ru, idx_ld, idx_rd, idx_lu])
        vals.extend([c12, c12, -c12, -c12])
        
        # 1次微分 (Christoffel 補正)
        gamma1 = (1 - 2*p1) / 2
        gamma2 = (1 - 2*p2) / 2
        
        # D1_p1
        c1 = gamma1 / (2 * h)
        rows.extend([idx, idx])
        cols.extend([idx_r, idx_l])
        vals.extend([c1, -c1])
        
        # D1_p2
        c2 = gamma2 / (2 * h)
        rows.extend([idx, idx])
        cols.extend([idx_u, idx_d])
        vals.extend([c2, -c2])
        
    L = sparse.csr_matrix((vals, (rows, cols)), shape=(n_pts, n_pts))
    return L


def solve_coupled_system(n_grid, eps):
    print(f"グリッド構築中 (N={n_grid})...")
    points, indices, h = build_simplex_grid(n_grid, eps)
    n_pts = len(points)
    print(f"  内部グリッド点数: {n_pts}")
    
    print("ラプラシアン行列構築中 (Neumann BC)...")
    L = build_laplacian_neumann(points, indices, h)
    
    # 初期条件
    # α: p1 方向の勾配を持つ (2*(1-p1))
    # Θ: MB の均一解 = μ²/ν²
    alpha = np.zeros(n_pts)
    theta = np.full(n_pts, MU2 / NU2)
    for i in range(n_pts):
        alpha[i] = 2.0 * (1.0 - points[i, 0])
    
    # x = [α, Θ] (長さ 2N)
    x = np.concatenate([alpha, theta])
    
    # L を 2Nx2N に拡張
    # L_full = [L  0]
    #          [0 kL]
    L_full = sparse.bmat([[L, None], [None, KAPPA * L]], format='csr')
    
    print(f"Newton 反復開始...")
    for it in range(MAX_ITER):
        a = x[:n_pts]
        th = x[n_pts:]
        
        e_th = np.exp(-th)
        
        # 残差 F = [F_α, F_Θ]
        # Eq I:  ∇²α - λγ α² (1 - e^{-Θ}) = 0
        # Eq II: κ∇²Θ - (λγ/3) α³ e^{-Θ} + μ² - ν²Θ = 0
        F_a = L @ a - LAMBDA_GAMMA * a**2 * (1 - e_th)
        F_th = KAPPA * (L @ th) - (LAMBDA_GAMMA / 3.0) * a**3 * e_th + MU2 - NU2 * th
        
        F = np.concatenate([F_a, F_th])
        res_norm = np.linalg.norm(F)
        
        if it % 20 == 0:
            print(f"  Iter {it:3d}: |F| = {res_norm:.2e}, "
                  f"α∈[{a.min():.2f}, {a.max():.2f}], "
                  f"Θ∈[{th.min():.2f}, {th.max():.2f}]")
            
        if res_norm < TOL:
            print(f"  収束! Iter {it}, |F| = {res_norm:.2e}")
            break
            
        # Jacobian J = ∂F / ∂x
        # J_aa = ∇² - 2λγ α (1 - e^{-Θ})
        # J_ath = -λγ α² e^{-Θ}
        # J_tha = -λγ α² e^{-Θ}  (対称!)
        # J_thth = κ∇² + (λγ/3) α³ e^{-Θ} - ν²
        
        diag_aa = -2 * LAMBDA_GAMMA * a * (1 - e_th)
        diag_ath = -LAMBDA_GAMMA * a**2 * e_th
        diag_tha = diag_ath.copy()
        diag_thth = (LAMBDA_GAMMA / 3.0) * a**3 * e_th - NU2
        
        J_aa = L + sparse.diags(diag_aa)
        J_ath = sparse.diags(diag_ath)
        J_tha = sparse.diags(diag_tha)
        J_thth = KAPPA * L + sparse.diags(diag_thth)
        
        J = sparse.bmat([[J_aa, J_ath], [J_tha, J_thth]], format='csr')
        
        try:
            dx = splinalg.spsolve(J, -F)
        except Exception as e:
            print(f"  Linear solver error: {e}")
            break
            
        # Newton 更新 (減衰つき)
        x = x + DAMPING * dx
        
        # 物理的制約: α ≥ 0, Θ ≥ 0
        x[:n_pts] = np.maximum(x[:n_pts], 0.0)
        x[n_pts:] = np.maximum(x[n_pts:], 0.0)
        
    else:
        print(f"  ⚠️ 最大反復到達. |F| = {res_norm:.2e}")
        
    return points, indices, x[:n_pts], x[n_pts:], h


def compute_gradients(points, indices, a, th, h):
    """|∇α|_g と |∇Θ|_g を計算"""
    grad_a = np.zeros(len(points))
    grad_th = np.zeros(len(points))
    
    for (gi, gj), idx in indices.items():
        p1, p2 = points[idx]
        gi11 = p1 * (1 - p1); gi22 = p2 * (1 - p2); gi12 = -p1 * p2
        
        def diff(arr, di, dj):
            idx_p = indices.get((gi+di, gj+dj), idx)
            idx_m = indices.get((gi-di, gj-dj), idx)
            if idx_p != idx and idx_m != idx:
                return (arr[idx_p] - arr[idx_m]) / (2*h)
            elif idx_p != idx:
                return (arr[idx_p] - arr[idx]) / h
            elif idx_m != idx:
                return (arr[idx] - arr[idx_m]) / h
            return 0.0
            
        da1 = diff(a, 1, 0); da2 = diff(a, 0, 1)
        dth1 = diff(th, 1, 0); dth2 = diff(th, 0, 1)
        
        gsq_a = gi11*da1**2 + 2*gi12*da1*da2 + gi22*da2**2
        gsq_th = gi11*dth1**2 + 2*gi12*dth1*dth2 + gi22*dth2**2
        
        grad_a[idx] = np.sqrt(max(0, gsq_a))
        grad_th[idx] = np.sqrt(max(0, gsq_th))
        
    return grad_a, grad_th


def save_results(points, alpha, theta, grad_a, grad_th):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.tri as mtri
        
        p1, p2 = points[:, 0], points[:, 1]
        triang = mtri.Triangulation(p1, p2)
        p3_c = 1.0 - np.mean(p1[triang.triangles], axis=1) - np.mean(p2[triang.triangles], axis=1)
        triang.set_mask(p3_c < EPS_BDRY * 0.5)
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # α
        ax = axes[0, 0]
        cf = ax.tricontourf(triang, alpha, levels=25, cmap='magma')
        plt.colorbar(cf, ax=ax)
        ax.set_title(r'Asymmetry Field $\alpha$')
        ax.set_aspect('equal')
        
        # Θ
        ax = axes[0, 1]
        cf = ax.tricontourf(triang, theta, levels=25, cmap='inferno')
        plt.colorbar(cf, ax=ax)
        ax.set_title(r'Oblivion Field $\Theta$')
        ax.set_aspect('equal')
        
        # 第一の力 |∇α|·φ
        force1 = grad_a * (1 - np.exp(-theta))
        ax = axes[1, 0]
        cf = ax.tricontourf(triang, force1, levels=25, cmap='viridis')
        plt.colorbar(cf, ax=ax)
        ax.set_title(r'1st Force $|\nabla\alpha|_g \cdot \phi(\Theta)$')
        ax.set_aspect('equal')
        
        # 第二の力 κ|∇Θ|
        force2 = KAPPA * grad_th
        ax = axes[1, 1]
        cf = ax.tricontourf(triang, force2, levels=25, cmap='plasma')
        plt.colorbar(cf, ax=ax)
        ax.set_title(r'2nd Force $\kappa |\nabla\Theta|_g$')
        ax.set_aspect('equal')
        
        plt.tight_layout()
        path = os.path.join(OUT_DIR, "coupled_alpha_theta.png")
        plt.savefig(path, dpi=150)
        print(f"画像保存: {path}")
        
    except Exception as e:
        print(f"プロットエラー: {e}")


def main():
    print("=" * 60)
    print("α-Θ 結合方程式の 2D 完全解 (Neumann BC)")
    print(f"  λγ={LAMBDA_GAMMA}, κ={KAPPA}, μ²={MU2}, ν²={NU2}")
    print("=" * 60)
    
    points, indices, alpha, theta, h = solve_coupled_system(N_GRID, EPS_BDRY)
    grad_a, grad_th = compute_gradients(points, indices, alpha, theta, h)
    
    print("\n=== 結果統計 ===")
    print(f"  α : [{alpha.min():.3f}, {alpha.max():.3f}] (mean={alpha.mean():.3f})")
    print(f"  Θ : [{theta.min():.3f}, {theta.max():.3f}] (mean={theta.mean():.3f})")
    print(f"  |∇α|_g : max={grad_a.max():.3f}")
    print(f"  |∇Θ|_g : max={grad_th.max():.3f}")
    
    force1 = grad_a * (1 - np.exp(-theta))
    force2 = KAPPA * grad_th
    print(f"  第一の力 max={force1.max():.3f}")
    print(f"  第二の力 max={force2.max():.3f}")
    
    save_results(points, alpha, theta, grad_a, grad_th)

if __name__ == '__main__':
    main()
