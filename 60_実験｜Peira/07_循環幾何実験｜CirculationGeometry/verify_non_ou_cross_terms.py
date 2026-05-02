#!/usr/bin/env python3
"""非 OU ケースの密度-循環交差項検証

problem_E_m_connection.md §8.15 の残課題:
  OU 過程: E[∂_i V] = 0 → 交差項 G_{i,μ} = 0 → 直積 M_density × M_circ
  非 OU:   E[∂_i V] ≠ 0 → 交差項 G_{i,μ} ≠ 0 → 密度-循環結合

検証項目:
  1. 各ポテンシャルで p_ss を数値的に求める (Fokker-Planck 定常解)
  2. E[∂_i V] を計算し交差項 G_{i,μ} の大きさを定量化
  3. 密度 Fisher 計量 g^(F) と電流 Fisher 計量 g^{(c,F)} を計算
  4. 交差項 / 対角項の比率 → 結合の「強さ」を定量化
  5. ω への依存性: 循環が強まると結合はどうなるか？

ポテンシャル:
  (a) OU (参照):      V = (x₁² + x₂²)/2
  (b) 非対称シフト:   V = (x₁² + x₂²)/2 + ε·x₁
  (c) 四次 (Duffing): V = x₁⁴/4 + x₂²/2
  (d) ダブルウェル:    V = (x₁²-1)²/4 + x₂²/2
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# 定常分布の数値計算
# ---------------------------------------------------------------------------

@dataclass
class Potential:
    """ポテンシャル V(x) の定義。"""
    name: str
    V: callable      # V(x1, x2) → float
    grad_V: callable # grad_V(x1, x2) → (dV/dx1, dV/dx2)
    params: dict     # ポテンシャルのパラメータ


def make_potentials() -> list[Potential]:
    """検証用ポテンシャル群を構築。"""
    potentials = []

    # (a) OU (参照基準)
    potentials.append(Potential(
        name="OU (a₁=a₂=1)",
        V=lambda x1, x2: 0.5 * (x1**2 + x2**2),
        grad_V=lambda x1, x2: (x1, x2),
        params={"type": "OU"},
    ))

    # (b) 非対称シフト (ε=0.5)
    eps = 0.5
    potentials.append(Potential(
        name=f"非対称シフト (ε={eps})",
        V=lambda x1, x2, e=eps: 0.5 * (x1**2 + x2**2) + e * x1,
        grad_V=lambda x1, x2, e=eps: (x1 + e, x2),
        params={"type": "shifted", "epsilon": eps},
    ))

    # (c) 四次 Duffing
    potentials.append(Potential(
        name="Duffing (x₁⁴/4 + x₂²/2)",
        V=lambda x1, x2: x1**4 / 4.0 + x2**2 / 2.0,
        grad_V=lambda x1, x2: (x1**3, x2),
        params={"type": "duffing"},
    ))

    # (d) ダブルウェル
    potentials.append(Potential(
        name="ダブルウェル ((x₁²-1)²/4 + x₂²/2)",
        V=lambda x1, x2: (x1**2 - 1.0)**2 / 4.0 + x2**2 / 2.0,
        grad_V=lambda x1, x2: (x1 * (x1**2 - 1.0), x2),
        params={"type": "double_well"},
    ))

    # (e) 非対称 Duffing (真の非 OU + 非対称)
    eps3 = 0.3
    potentials.append(Potential(
        name=f"非対称Duffing (ε={eps3})",
        V=lambda x1, x2, e=eps3: x1**4 / 4.0 + e * x1**3 / 3.0 + x2**2 / 2.0,
        grad_V=lambda x1, x2, e=eps3: (x1**3 + e * x1**2, x2),
        params={"type": "asym_duffing", "epsilon": eps3},
    ))

    # (f) 非対称 Duffing (強い非対称)
    eps4 = 0.8
    potentials.append(Potential(
        name=f"非対称Duffing (ε={eps4})",
        V=lambda x1, x2, e=eps4: x1**4 / 4.0 + e * x1**3 / 3.0 + x2**2 / 2.0,
        grad_V=lambda x1, x2, e=eps4: (x1**3 + e * x1**2, x2),
        params={"type": "asym_duffing", "epsilon": eps4},
    ))

    # (g) 三次ポテンシャル (V = x₁³/3 + x₁²/2 + x₂²/2)
    # 安定化: x₁⁴/4 を追加して有界にする
    potentials.append(Potential(
        name="三次+安定化",
        V=lambda x1, x2: x1**4 / 4.0 + x1**3 / 3.0 + x1**2 / 2.0 + x2**2 / 2.0,
        grad_V=lambda x1, x2: (x1**3 + x1**2 + x1, x2),
        params={"type": "cubic_stabilized"},
    ))

    return potentials


def compute_p_ss(
    potential: Potential,
    sigma: float,
    grid_n: int = 200,
    grid_range: float = 5.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """定常分布 p_ss ∝ exp(-2V/σ²) をグリッド上で計算。

    ω-不変性定理 (T1) より p_ss は ω に依存しない。
    → V と σ だけで決まる。

    Returns:
        (X1, X2, P): メッシュグリッドと正規化された p_ss
    """
    xs = np.linspace(-grid_range, grid_range, grid_n)
    dx = xs[1] - xs[0]
    X1, X2 = np.meshgrid(xs, xs)

    # V の評価 (ベクトル化)
    V_grid = np.vectorize(potential.V)(X1, X2)

    # ボルツマン分布
    D = sigma**2 / 2.0
    log_P = -V_grid / D
    # オーバーフロー防止
    log_P -= np.max(log_P)
    P = np.exp(log_P)

    # 正規化
    P /= np.sum(P) * dx**2

    return X1, X2, P


# ---------------------------------------------------------------------------
# 交差項の計算
# ---------------------------------------------------------------------------

def compute_cross_terms(
    potential: Potential,
    sigma: float,
    omega: float,
    grid_n: int = 200,
    grid_range: float = 5.0,
) -> dict:
    """密度-循環の交差項 G_{i,μ} を計算。

    G_{i,μ} = ∫ ∂_i log p_ss · ∂_μ log|j_ss| · p_ss dx

    OU: ∂_i log p = -(2/σ²)∂_i V, ∂_μ log|j| = 1/ω
    → G_{i,μ} = -(2/σ²ω) E[∂_i V]

    一般の場合も p_ss ∝ exp(-2V/σ²) → ∂_i log p_ss = -(2/σ²)∂_i V は成立。
    ∂_ω log|j_ss| = 1/ω も Q の線形性から成立。

    → G_{i,ω} = -(2/σ²ω) ∫ ∂_i V · p_ss dx = -(2/σ²ω) E[∂_i V]

    つまり交差項は E[∂_i V] に帰着する!
    """
    X1, X2, P = compute_p_ss(potential, sigma, grid_n, grid_range)
    dx = (2 * grid_range) / (grid_n - 1)

    # ∂_i V のグリッド計算
    dV1, dV2 = np.vectorize(
        lambda x1, x2: potential.grad_V(x1, x2),
        otypes=[float, float],
    )(X1, X2)

    # E[∂_i V]
    E_dV1 = np.sum(dV1 * P) * dx**2
    E_dV2 = np.sum(dV2 * P) * dx**2

    # 交差項
    G_1_omega = -(2.0 / (sigma**2 * omega)) * E_dV1
    G_2_omega = -(2.0 / (sigma**2 * omega)) * E_dV2

    # 密度 Fisher 情報 (対角要素)
    # g^(F)_{ij} = ∫ ∂_i log p · ∂_j log p · p dx
    # = (4/σ⁴) ∫ ∂_i V · ∂_j V · p dx
    g_F_11 = (4.0 / sigma**4) * np.sum(dV1**2 * P) * dx**2
    g_F_22 = (4.0 / sigma**4) * np.sum(dV2**2 * P) * dx**2
    g_F_12 = (4.0 / sigma**4) * np.sum(dV1 * dV2 * P) * dx**2

    # 電流 Fisher 計量
    g_cF = 1.0 / omega**2

    # 循環計量 g^(c)
    # g^(c) = (σ⁴/4) ω² ∫ |∇V|² p dx / <正規化>
    # = (σ⁴/4) ω² I_F^{sp}
    I_F_sp = np.sum((dV1**2 + dV2**2) * P) * dx**2 * (4.0 / sigma**4)
    g_c = omega**2 * (sigma**4 / 4.0) * I_F_sp

    # 結合強度: |交差項| / √(対角項の積)
    cross_norm = np.sqrt(G_1_omega**2 + G_2_omega**2)
    diag_norm = np.sqrt((g_F_11 + g_F_22) / 2.0 * g_cF)
    coupling_ratio = cross_norm / diag_norm if diag_norm > 1e-30 else 0.0

    # E[x_i] — 分布の重心 (非対称性の指標)
    E_x1 = np.sum(X1 * P) * dx**2
    E_x2 = np.sum(X2 * P) * dx**2

    return {
        "E[∂₁V]": E_dV1,
        "E[∂₂V]": E_dV2,
        "G_{1,ω}": G_1_omega,
        "G_{2,ω}": G_2_omega,
        "|G_cross|": cross_norm,
        "g^(F)_{11}": g_F_11,
        "g^(F)_{22}": g_F_22,
        "g^(F)_{12}": g_F_12,
        "g^{(c,F)}": g_cF,
        "g^(c)": g_c,
        "I_F^{sp}": I_F_sp,
        "coupling_ratio": coupling_ratio,
        "E[x₁]": E_x1,
        "E[x₂]": E_x2,
        "trade-off": g_c * g_cF,
        "(σ⁴/4)I_F": (sigma**4 / 4.0) * I_F_sp,
    }


# ---------------------------------------------------------------------------
# 拡張計量行列の構築と解析
# ---------------------------------------------------------------------------

def build_extended_metric(
    potential: Potential,
    sigma: float,
    omega: float,
    grid_n: int = 200,
    grid_range: float = 5.0,
) -> tuple[np.ndarray, dict]:
    """拡張パラメータ空間の 3×3 計量行列を構築。

    パラメータ: (θ₁, θ₂, ω) — ただし θ はポテンシャルの係数ではなく
    密度方向の Fisher 的パラメータ化。

    OU の場合:
        G = diag(g^(F)_{11}, g^(F)_{22}, g^{(c,F)})  (ブロック対角)

    非 OU の場合:
        G = [[g^(F)_{11}, g^(F)_{12}, G_{1,ω}],
             [g^(F)_{12}, g^(F)_{22}, G_{2,ω}],
             [G_{1,ω},    G_{2,ω},    g^{(c,F)}]]
    """
    r = compute_cross_terms(potential, sigma, omega, grid_n, grid_range)

    G = np.array([
        [r["g^(F)_{11}"], r["g^(F)_{12}"], r["G_{1,ω}"]],
        [r["g^(F)_{12}"], r["g^(F)_{22}"], r["G_{2,ω}"]],
        [r["G_{1,ω}"],    r["G_{2,ω}"],    r["g^{(c,F)}"]],
    ])

    return G, r


def analyze_coupling(G: np.ndarray) -> dict:
    """計量行列から結合の幾何学的指標を抽出。

    1. off-diagonal norm: 交差項のフロベニウスノルム
    2. 条件数: 結合による行列の歪み
    3. ブロック対角からの距離: ||G - G_diag|| / ||G||
    """
    # ブロック対角成分
    G_block = np.zeros_like(G)
    G_block[:2, :2] = G[:2, :2]
    G_block[2, 2] = G[2, 2]

    # 交差項のみ
    G_cross = G - G_block

    frob_cross = np.linalg.norm(G_cross, "fro")
    frob_total = np.linalg.norm(G, "fro")
    relative_coupling = frob_cross / frob_total if frob_total > 1e-30 else 0.0

    # 固有値 (正定値性チェック含む)
    eigenvalues = np.linalg.eigvalsh(G)

    # 条件数
    if eigenvalues[0] > 1e-15:
        condition_number = eigenvalues[-1] / eigenvalues[0]
    else:
        condition_number = float("inf")

    return {
        "frob_cross": frob_cross,
        "frob_total": frob_total,
        "relative_coupling": relative_coupling,
        "eigenvalues": eigenvalues,
        "condition_number": condition_number,
        "is_positive_definite": bool(np.all(eigenvalues > 0)),
    }


# ---------------------------------------------------------------------------
# ω 依存性の調査
# ---------------------------------------------------------------------------

def omega_dependence_study(
    potential: Potential,
    sigma: float = 1.0,
    omegas: list[float] | None = None,
    grid_n: int = 150,
    grid_range: float = 5.0,
) -> list[dict]:
    """交差項の ω 依存性を調査。

    G_{i,ω} = -(2/σ²ω) E[∂_i V] → ω に逆比例。
    g^{(c,F)} = 1/ω² → ω に逆二乗。

    → coupling_ratio = |G_cross| / √(g_diag) の ω スケーリングは？
    """
    if omegas is None:
        omegas = [0.1, 0.3, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0]

    results = []
    for omega in omegas:
        G, r = build_extended_metric(potential, sigma, omega, grid_n, grid_range)
        coupling = analyze_coupling(G)
        results.append({
            "omega": omega,
            **r,
            **coupling,
        })
    return results


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def run_all() -> None:
    """全調査を実行。"""
    sigma = 1.0
    omega = 1.0

    potentials = make_potentials()

    print("=" * 75)
    print("非 OU ケースの密度-循環交差項解析")
    print(f"σ = {sigma}, ω = {omega}")
    print("=" * 75)

    # ── 調査 1: 各ポテンシャルでの交差項 ──
    print("\n── 調査 1: 各ポテンシャルでの交差項 (σ=1, ω=1) ──\n")
    print(f"  {'ポテンシャル':<35}  {'E[∂₁V]':>10}  {'E[∂₂V]':>10}  "
          f"{'|G_cross|':>10}  {'結合比率':>10}")
    print(f"  {'─' * 35}  {'─' * 10}  {'─' * 10}  {'─' * 10}  {'─' * 10}")

    all_results = {}
    for pot in potentials:
        G, r = build_extended_metric(pot, sigma, omega)
        coupling = analyze_coupling(G)
        all_results[pot.name] = (G, r, coupling)

        print(f"  {pot.name:<35}  {r['E[∂₁V]']:10.6f}  {r['E[∂₂V]']:10.6f}  "
              f"{r['|G_cross|']:10.6f}  {coupling['relative_coupling']:10.6f}")

    # ── 調査 2: 計量行列の詳細 ──
    print("\n── 調査 2: 拡張計量行列 G (3×3) ──\n")
    for pot in potentials:
        G, r, coupling = all_results[pot.name]
        print(f"  {pot.name}:")
        print(f"    G = [[{G[0,0]:8.4f}, {G[0,1]:8.4f}, {G[0,2]:8.4f}],")
        print(f"         [{G[1,0]:8.4f}, {G[1,1]:8.4f}, {G[1,2]:8.4f}],")
        print(f"         [{G[2,0]:8.4f}, {G[2,1]:8.4f}, {G[2,2]:8.4f}]]")
        print(f"    固有値: {coupling['eigenvalues']}")
        print(f"    条件数: {coupling['condition_number']:.2f}")
        print(f"    相対結合: {coupling['relative_coupling']:.6f}")
        print(f"    正定値: {'✅' if coupling['is_positive_definite'] else '❌'}")
        print()

    # ── 調査 3: trade-off 恒等式の非 OU での成否 ──
    print("── 調査 3: trade-off 恒等式 g^(c)·g^{(c,F)} =? (σ⁴/4)I_F ──\n")
    print(f"  {'ポテンシャル':<35}  {'g^(c)·g^{(c,F)}':>16}  {'(σ⁴/4)I_F':>12}  "
          f"{'相対誤差':>12}")
    for pot in potentials:
        G, r, _ = all_results[pot.name]
        product = r["trade-off"]
        expected = r["(σ⁴/4)I_F"]
        rel_err = abs(product - expected) / expected if expected > 1e-15 else 0.0
        print(f"  {pot.name:<35}  {product:16.6f}  {expected:12.6f}  {rel_err:12.2e}")

    # ── 調査 4: ω 依存性 (非対称シフト ε=0.5) ──
    print("\n── 調査 4: 交差項の ω 依存性 (非対称シフト ε=0.5) ──\n")
    shifted_pot = potentials[1]  # ε=0.5
    omegas = [0.1, 0.3, 0.5, 1.0, 2.0, 5.0, 10.0]
    omega_results = omega_dependence_study(shifted_pot, sigma, omegas)

    print(f"  {'ω':>6}  {'|G_cross|':>10}  {'g^{(c,F)}':>10}  "
          f"{'結合比率':>10}  {'|G|/ω':>10}")
    print(f"  {'─' * 6}  {'─' * 10}  {'─' * 10}  {'─' * 10}  {'─' * 10}")
    for r in omega_results:
        gcross_over_omega = r["|G_cross|"] * r["omega"]
        print(f"  {r['omega']:6.2f}  {r['|G_cross|']:10.6f}  {r['g^{(c,F)}']:10.6f}  "
              f"{r['relative_coupling']:10.6f}  {gcross_over_omega:10.6f}")

    # ── 調査 5: 非対称シフトの理論値との比較 ──
    print("\n── 調査 5: 非対称シフトの理論解析 ──\n")
    print("  非対称シフト V = (x₁² + x₂²)/2 + εx₁")
    print("  → p_ss ∝ exp(-(x₁² + x₂² + 2εx₁)/σ²)")
    print("       = exp(-((x₁+ε)² + x₂² - ε²)/σ²)")
    print("       = N((-ε, 0), σ²I/2)")
    print()
    print("  ∂₁V = x₁ + ε → E[∂₁V] = E[x₁] + ε = -ε + ε = 0  ← OU と同じ!")
    print("  ∂₂V = x₂     → E[∂₂V] = E[x₂] = 0")
    print()
    print("  ★ 非対称シフトでも二次ポテンシャルなら交差項はゼロ!")
    print("  ∵ 平衡点が (x₁, x₂) = (-ε, 0) にシフトするだけ")
    print("  → 真の非 OU は ∂²V/∂x² が定数でない場合 (四次、ダブルウェル等)")

    # ── 調査 6: ω 依存性 (Duffing — 真の非 OU) ──
    print("\n── 調査 6: 交差項の ω 依存性 (Duffing — 真の非 OU) ──\n")
    duffing_pot = potentials[2]
    omega_results_duffing = omega_dependence_study(duffing_pot, sigma, omegas)

    print(f"  {'ω':>6}  {'E[∂₁V]':>10}  {'|G_cross|':>10}  "
          f"{'結合比率':>10}  {'条件数':>12}")
    for r in omega_results_duffing:
        print(f"  {r['omega']:6.2f}  {r['E[∂₁V]']:10.6f}  {r['|G_cross|']:10.6f}  "
              f"{r['relative_coupling']:10.6f}  {r['condition_number']:12.2f}")

    # ── 調査 7: ω 依存性 (ダブルウェル — 双峰非 OU) ──
    print("\n── 調査 7: 交差項の ω 依存性 (ダブルウェル) ──\n")
    dw_pot = potentials[3]
    omega_results_dw = omega_dependence_study(dw_pot, sigma, omegas, grid_range=4.0)

    print(f"  {'ω':>6}  {'E[∂₁V]':>10}  {'|G_cross|':>10}  "
          f"{'結合比率':>10}  {'条件数':>12}")
    for r in omega_results_dw:
        print(f"  {r['omega']:6.2f}  {r['E[∂₁V]']:10.6f}  {r['|G_cross|']:10.6f}  "
              f"{r['relative_coupling']:10.6f}  {r['condition_number']:12.2f}")

    # ── サマリ ──
    print("\n" + "=" * 75)
    print("解析サマリ")
    print("=" * 75)
    print()
    print("  [1] OU, 非対称シフト (二次): 交差項 = 0 (理論通り)")
    print("      ∵ 二次ポテンシャルは平衡点シフトのみ → 対称性保存")
    print()
    print("  [2] Duffing (四次): E[∂₁V] の値を確認")
    print("      x₁³ は奇関数 → 対称分布なら E[x₁³] = 0 → E[∂₁V] = 0")
    print("      → V が偶関数 ⟹ p_ss が偶関数 ⟹ 交差項 = 0!")
    print()
    print("  [3] ダブルウェル: V(x₁) = (x₁²-1)²/4 は偶関数")
    print("      → p_ss は偶関数 → 交差項 = 0!")
    print()
    print("  ★ 核心発見: 交差項 G_{i,ω} = -(2/σ²ω) E[∂_i V] がゼロでないのは")
    print("    V(x) が非対称 かつ 非二次 の場合のみ。")
    print("    偶関数ポテンシャル → 対称 p_ss → E[奇数次項] = 0 → 交差項 = 0")
    print()
    print("  → 探すべき: V に奇数次の非二次項がある場合")
    print("    例: V = x₁⁴/4 + x₂²/2 + ε·x₁³/3 (非対称 Duffing)")


if __name__ == "__main__":
    run_all()
