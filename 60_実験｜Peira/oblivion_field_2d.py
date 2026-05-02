"""
忘却場 Θ の2D完全解 — v4 最小実装
====================================
§9.5 で成功した 1D BVP を忠実に再現する最小テストから開始。
成功を確認してから多重 slice に拡張。

場の方程式: ∇²Θ = -m²_eff·Θ + 4λ·Θ³
1D (p₁固定、s方向): 平坦ラプラシアン近似
    d²Θ/ds² = -m²_eff·Θ + 4λ·Θ³
"""

import numpy as np
from scipy.integrate import solve_bvp
import os

M2_EFF = 5.0
LAMBDA = 1.0
THETA0 = 0.5 * np.sqrt(M2_EFF / LAMBDA)  # ≈ 1.118

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def ode_flat(s, y):
    """
    最も単純な定式化 (§9.5 再現):
    d²Θ/ds² = -m²_eff·Θ + 4λ·Θ³
    
    Fisher 計量の効果は無視 (平坦近似)。
    §9.5 の結果: 中心 s=0.5 で Θ_max ≈ 0.841
    """
    theta, dtheta = y
    d2theta = -M2_EFF * theta + 4 * LAMBDA * theta**3
    return np.vstack([dtheta, d2theta])


def bc(ya, yb):
    return np.array([ya[0], yb[0]])


def solve_single_slice(s_min=0.05, s_max=0.95, n=100):
    """1D BVP を解く (§9.5 の再現)"""
    s = np.linspace(s_min, s_max, n)
    
    # 初期推定: sin 型の bump
    y_init = np.zeros((2, n))
    y_init[0] = THETA0 * 0.8 * np.sin(np.pi * (s - s_min) / (s_max - s_min))
    y_init[1] = THETA0 * 0.8 * np.pi / (s_max - s_min) * np.cos(np.pi * (s - s_min) / (s_max - s_min))
    
    sol = solve_bvp(ode_flat, bc, s, y_init, tol=1e-8, max_nodes=5000)
    return sol


def solve_with_metric(p1, s_min=0.05, s_max=0.95, n=100):
    """
    Fisher 計量込みの 1D BVP。
    s 座標での場の方程式:
    
    g_ss = (1-p₁)² [1/(s(1-p₁)) + 1/((1-s)(1-p₁))]
         = (1-p₁) [1/s + 1/(1-s)]
         = (1-p₁) / [s(1-s)]

    g^ss = s(1-s)(1-p₁)

    ∇²Θ|_{1D} = g^ss { d²Θ/ds² + [d ln√g_ss/ds] dΘ/ds }

    ただし d ln√g_ss/ds = (1-2s) / [2s(1-s)]
    
    場の方程式 ∇²Θ = -m²Θ + 4λΘ³ を整理:
    
    d²Θ/ds² + [(1-2s)/(2s(1-s))] dΘ/ds = [1/(s(1-s)(1-p₁))] [-m²Θ + 4λΘ³]
    
    d²Θ/ds² = -[(1-2s)/(2s(1-s))] dΘ/ds + [1/(s(1-s)(1-p₁))] [-m²Θ + 4λΘ³]
    """
    s = np.linspace(s_min, s_max, n)
    
    def ode_metric(s_arr, y):
        theta = y[0]
        dtheta = y[1]
        
        d2theta = np.zeros_like(s_arr)
        for i, si in enumerate(s_arr):
            if si < 1e-10 or si > 1 - 1e-10:
                d2theta[i] = 0.0
                continue
            # Christoffel 項
            christoffel = (1 - 2*si) / (2 * si * (1 - si))
            # 反応項のスケール因子 (g^ss の逆数)
            scale = 1.0 / (si * (1 - si) * (1 - p1))
            # d²Θ/ds²
            d2theta[i] = -christoffel * dtheta[i] + scale * (-M2_EFF * theta[i] + 4 * LAMBDA * theta[i]**3)
        
        return np.vstack([dtheta, d2theta])
    
    y_init = np.zeros((2, n))
    y_init[0] = THETA0 * 0.8 * np.sin(np.pi * (s - s_min) / (s_max - s_min))
    y_init[1] = THETA0 * 0.8 * np.pi / (s_max - s_min) * np.cos(np.pi * (s - s_min) / (s_max - s_min))
    
    sol = solve_bvp(ode_metric, bc, s, y_init, tol=1e-6, max_nodes=5000)
    return sol


def main():
    print("=" * 60)
    print("Step 1: §9.5 再現テスト (平坦ラプラシアン)")
    print("=" * 60)
    
    sol_flat = solve_single_slice()
    print(f"  success: {sol_flat.success}")
    print(f"  Θ_max = {sol_flat.y[0].max():.4f} (期待値: 0.841)")
    print(f"  Θ_max / Θ₀ = {sol_flat.y[0].max() / THETA0:.4f}")
    
    # s=0.5 での値
    s05_idx = np.argmin(np.abs(sol_flat.x - 0.5))
    print(f"  Θ(s=0.5) = {sol_flat.y[0][s05_idx]:.4f}")
    
    if not sol_flat.success or sol_flat.y[0].max() < 0.1:
        print("  ⚠️ 再現失敗。ODE 定式化を確認")
        return
    
    print(f"\n  §9.5 比較テーブル:")
    s_ref = {0.10: 0.251, 0.20: 0.561, 0.30: 0.730, 0.40: 0.815, 
             0.50: 0.841, 0.60: 0.815, 0.70: 0.730, 0.80: 0.561, 0.90: 0.251}
    print(f"  {'s':>6s}  {'Θ_calc':>8s}  {'Θ_§9.5':>8s}  {'err%':>6s}")
    for s_val, th_ref in sorted(s_ref.items()):
        idx = np.argmin(np.abs(sol_flat.x - s_val))
        th_calc = sol_flat.y[0][idx]
        err = abs(th_calc - th_ref) / th_ref * 100
        print(f"  {s_val:6.3f}  {th_calc:8.4f}  {th_ref:8.4f}  {err:5.1f}%")
    
    print("\n" + "=" * 60)
    print("Step 2: Fisher 計量込み 多重 slice")
    print("=" * 60)
    
    P1_VALUES = np.linspace(0.05, 0.90, 35)
    results = []
    
    for p1 in P1_VALUES:
        sol = solve_with_metric(p1)
        th_max = sol.y[0].max() if sol.success else 0.0
        results.append((p1, sol.x, sol.y[0], sol.success, th_max))
    
    success_count = sum(1 for r in results if r[3])
    nontrivial = sum(1 for r in results if r[3] and r[4] > 0.01)
    print(f"\n  成功: {success_count}/{len(results)}")
    print(f"  非自明解: {nontrivial}/{len(results)}")
    
    print(f"\n  p₁ 依存性:")
    print(f"  {'p₁':>5s}  {'Θ_max':>8s}  {'Θ_max/Θ₀':>9s}  {'s(max)':>6s}")
    for p1, s_arr, theta_arr, success, th_max in results:
        if success and th_max > 0.01:
            idx_m = np.argmax(theta_arr)
            s_m = s_arr[idx_m]
            if abs(p1 - round(p1 * 10) / 10) < 0.02:  # きりの良い p₁ のみ表示
                print(f"  {p1:5.3f}  {th_max:8.4f}  {th_max/THETA0:9.4f}  {s_m:6.3f}")
    
    # 2D データ構築 + プロット
    all_p1, all_p2, all_theta, all_grad = [], [], [], []
    for p1, s_arr, theta_arr, success, _ in results:
        if not success:
            continue
        for j in range(len(s_arr)):
            s = s_arr[j]
            p2 = s * (1 - p1)
            p3 = (1 - s) * (1 - p1)
            if p2 > 0.01 and p3 > 0.01:
                all_p1.append(p1)
                all_p2.append(p2)
                all_theta.append(theta_arr[j])
                if 0 < j < len(s_arr) - 1:
                    ds = s_arr[j+1] - s_arr[j-1]
                    dth = theta_arr[j+1] - theta_arr[j-1]
                    grad_s = dth / ds if ds > 0 else 0
                    g_inv = s * (1-s) * (1-p1)
                    all_grad.append(np.sqrt(max(0, g_inv * grad_s**2)))
                else:
                    all_grad.append(0.0)
    
    all_p1 = np.array(all_p1)
    all_p2 = np.array(all_p2)
    all_theta = np.array(all_theta)
    all_grad = np.array(all_grad)
    
    print(f"\n=== 2D 統合結果 ===")
    print(f"  データ点数: {len(all_p1)}")
    print(f"  Θ_max = {all_theta.max():.4f}")
    if all_theta.max() > 0:
        idx_max = np.argmax(all_theta)
        print(f"  Θ_max 位置: p₁={all_p1[idx_max]:.3f}, p₂={all_p2[idx_max]:.3f}")
    
    # テキスト保存
    txt_path = os.path.join(OUT_DIR, "results_2d.txt")
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"# v4: m2_eff={M2_EFF}, lambda={LAMBDA}, Theta0={THETA0:.4f}\n")
        f.write(f"# Theta_max={all_theta.max():.6f}\n")
        f.write("# p1\tp2\tp3\ttheta\tgrad\n")
        for i in range(len(all_p1)):
            f.write(f"{all_p1[i]:.4f}\t{all_p2[i]:.4f}\t{1-all_p1[i]-all_p2[i]:.4f}\t"
                    f"{all_theta[i]:.6f}\t{all_grad[i]:.6f}\n")
    
    # プロット
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.tri as mtri
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        if all_theta.max() > 0.01:
            triang = mtri.Triangulation(all_p1, all_p2)
            p3_c = 1.0 - np.mean(all_p1[triang.triangles], axis=1) - np.mean(all_p2[triang.triangles], axis=1)
            triang.set_mask((p3_c < 0.01) | (np.mean(all_p1[triang.triangles], axis=1) < 0.03))
            
            ax = axes[0]
            cf = ax.tricontourf(triang, all_theta, levels=np.linspace(0, all_theta.max(), 25), cmap='inferno')
            plt.colorbar(cf, ax=ax, label='Θ')
            ax.set_xlabel('p₁'); ax.set_ylabel('p₂')
            ax.set_title(f'Oblivion Field Θ (m²_eff={M2_EFF})')
            ax.set_aspect('equal')
            p1_l = np.linspace(0.05, 0.9, 50)
            ax.plot(p1_l, (1-p1_l)/2, 'w:', alpha=0.8, label='p₂=p₃')
            ax.legend(fontsize=8)
            
            ax = axes[1]
            gm = all_grad.copy()
            gm_clip = np.percentile(gm[gm>0], 99) if np.any(gm>0) else 1.0
            gm = np.minimum(gm, gm_clip)
            cf2 = ax.tricontourf(triang, gm, levels=np.linspace(0, gm_clip, 25), cmap='viridis')
            plt.colorbar(cf2, ax=ax, label='|∇Θ|_g')
            ax.set_xlabel('p₁'); ax.set_ylabel('p₂')
            ax.set_title(f'Force |∇Θ|_g (m²_eff={M2_EFF})')
            ax.set_aspect('equal')
        
        ax = axes[2]
        for p1, s_arr, theta_arr, success, _ in results:
            if abs(p1 - 0.3) < 0.02 and success:
                ax.plot(s_arr, theta_arr, 'b-', linewidth=2, label=f'Metric (p₁={p1:.2f})')
                break
        ax.plot(sol_flat.x, sol_flat.y[0], 'g--', linewidth=1.5, label='Flat (§9.5)')
        s_1d = np.array([0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90])
        theta_1d = np.array([0.251, 0.561, 0.730, 0.815, 0.841, 0.815, 0.730, 0.561, 0.251])
        ax.plot(s_1d, theta_1d, 'r--s', markersize=5, label='§9.5 ref')
        ax.set_xlabel('s'); ax.set_ylabel('Θ')
        ax.set_title('Slice comparison (p₁=0.3)')
        ax.legend(); ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        fig.savefig(os.path.join(OUT_DIR, "oblivion_field_2d.png"), dpi=150)
        plt.close()
        
        # p₁ 依存性
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        p1s = [r[0] for r in results if r[3] and r[4] > 0.01]
        ths = [r[4] for r in results if r[3] and r[4] > 0.01]
        if p1s:
            ax2.plot(p1s, ths, 'bo-', markersize=5)
        ax2.axhline(y=THETA0, color='r', linestyle='--', label=f'Θ₀ = {THETA0:.3f}')
        ax2.set_xlabel('p₁'); ax2.set_ylabel('Θ_max')
        ax2.set_title('p₁ dependence of Θ_max'); ax2.legend(); ax2.grid(True, alpha=0.3)
        fig2.savefig(os.path.join(OUT_DIR, "oblivion_p1_dependence.png"), dpi=150)
        plt.close()
        
    except Exception as e:
        print(f"プロットエラー: {e}")
    
    print("\n出力ファイル:")
    print(f"  {os.path.join(OUT_DIR, 'oblivion_field_2d.png')}")
    print(f"  {os.path.join(OUT_DIR, 'oblivion_p1_dependence.png')}")
    print(f"  {txt_path}")


if __name__ == '__main__':
    main()
