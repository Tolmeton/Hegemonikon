#!/usr/bin/env python3
"""過渡過程における trade-off 恒等式の検証 (v2)

PURPOSE: 定常状態で成立する trade-off 恒等式
    g^(c) · g^{(c,F)} = (σ⁴/4) I_F^{sp}
が過渡過程でどう変形するかを数値的に検証する。

理論:
  定常: g^{(c,F)} = 1/ω² (定義的)。∂_ω p_ss = 0 が本質。
  過渡: p(x,t) が ω に依存するため ∂_ω p ≠ 0。
        → I_F(t) ≠ I_F^{sp} (p(t) が定常に未到達)
        → g^{(c,F)}(t) ≠ 1/ω² (ω-微分が p を通じて流入)

  核心問題: g^{(c,F)}(t) の **定義自体** が定常を前提とする。
  過渡での R(t) は「定常からの乖離」を測る指標。

v2 の方針:
  旧版の ∂_ω log|j| 計算は数値的に不安定 (j→0 領域)。
  代わりに3つの直接的な量を追跡:
  1. I_F(t) → I_F^{sp} への収束 (定常到達の指標)
  2. ω±Δω での確率分布の差 ‖∂_ω p‖ の減衰
  3. EP(t) → EP_ss への収束

ポテンシャル: OU (参照) / Duffing (非線形) / ダブルウェル (双峰)
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Callable
import time


# ---------------------------------------------------------------------------
# ポテンシャル
# ---------------------------------------------------------------------------

@dataclass
class Potential:
    """ポテンシャル V(x) の定義。"""
    name: str
    V: Callable
    grad_V: Callable


def make_potentials() -> list[Potential]:
    return [
        Potential("OU",
                  V=lambda x1, x2: 0.5 * (x1**2 + x2**2),
                  grad_V=lambda x1, x2: (x1, x2)),
        Potential("Duffing",
                  V=lambda x1, x2: x1**4 / 4 + x2**2 / 2,
                  grad_V=lambda x1, x2: (x1**3, x2)),
        Potential("DoubleWell",
                  V=lambda x1, x2: (x1**2 - 1)**2 / 4 + x2**2 / 2,
                  grad_V=lambda x1, x2: (x1 * (x1**2 - 1), x2)),
    ]


# ---------------------------------------------------------------------------
# FP ソルバー (最小構成)
# ---------------------------------------------------------------------------

class FPSolver:
    """2D Fokker-Planck をグリッド上で explicit Euler。"""

    def __init__(self, pot: Potential, sigma: float, omega: float,
                 N: int = 80, L: float = 4.0):
        self.sigma = sigma
        self.omega = omega
        self.D = sigma**2 / 2
        self.N = N

        xs = np.linspace(-L, L, N)
        self.dx = xs[1] - xs[0]
        self.X1, self.X2 = np.meshgrid(xs, xs)

        # ∇V
        self.dV1, self.dV2 = np.vectorize(
            lambda a, b: pot.grad_V(a, b), otypes=[float, float]
        )(self.X1, self.X2)

        # ドリフト μ = -∇V + ωQx, Q=[[0,-1],[1,0]]
        self.mu1 = -self.dV1 + omega * (-self.X2)
        self.mu2 = -self.dV2 + omega * self.X1

        # 定常分布
        V_grid = np.vectorize(pot.V)(self.X1, self.X2)
        log_p = -V_grid / self.D
        log_p -= np.max(log_p)
        self.p_ss = np.exp(log_p)
        self.p_ss /= np.sum(self.p_ss) * self.dx**2

        # 定常 I_F
        self.I_F_ss = (4 / sigma**4) * np.sum(
            (self.dV1**2 + self.dV2**2) * self.p_ss) * self.dx**2

    def init_gauss(self, c1: float = 1.5, c2: float = 1.0, s: float = 0.6
                   ) -> np.ndarray:
        p = np.exp(-((self.X1 - c1)**2 + (self.X2 - c2)**2) / (2 * s**2))
        p /= np.sum(p) * self.dx**2
        return p

    def step(self, p: np.ndarray, dt: float) -> np.ndarray:
        dx = self.dx
        # flux divergence (中心差分)
        f1 = self.mu1 * p
        f2 = self.mu2 * p
        div_f = (
            (np.roll(f1, -1, axis=1) - np.roll(f1, 1, axis=1)) / (2 * dx)
            + (np.roll(f2, -1, axis=0) - np.roll(f2, 1, axis=0)) / (2 * dx)
        )
        # Laplacian
        lap = (
            (np.roll(p, -1, axis=1) - 2 * p + np.roll(p, 1, axis=1)) / dx**2
            + (np.roll(p, -1, axis=0) - 2 * p + np.roll(p, 1, axis=0)) / dx**2
        )
        p_new = p + dt * (-div_f + self.D * lap)
        # 境界ゼロ
        p_new[0, :] = p_new[-1, :] = p_new[:, 0] = p_new[:, -1] = 0
        p_new = np.maximum(p_new, 0.0)
        s = np.sum(p_new) * dx**2
        if s > 1e-30:
            p_new /= s
        return p_new

    def current(self, p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """確率流 j = μp - D∇p"""
        dx = self.dx
        dp1 = (np.roll(p, -1, axis=1) - np.roll(p, 1, axis=1)) / (2 * dx)
        dp2 = (np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0)) / (2 * dx)
        return self.mu1 * p - self.D * dp1, self.mu2 * p - self.D * dp2


# ---------------------------------------------------------------------------
# 計量計算
# ---------------------------------------------------------------------------

def compute_metrics(solver: FPSolver, p: np.ndarray,
                    p_plus: np.ndarray, p_minus: np.ndarray,
                    d_omega: float) -> dict:
    """各時刻での計量を計算。"""
    dx = solver.dx
    sig = solver.sigma
    omega = solver.omega

    # (1) I_F(t) = (4/σ⁴) ∫ |∇V|² p dx
    I_F_t = (4 / sig**4) * np.sum(
        (solver.dV1**2 + solver.dV2**2) * p) * dx**2

    # (2) ‖∂_ω p‖ = ‖(p_+ - p_-) / (2Δω)‖_L2
    dp_do = (p_plus - p_minus) / (2 * d_omega)
    dp_norm = np.sqrt(np.sum(dp_do**2) * dx**2)

    # (3) KL(p || p_ss)
    mask = p > 1e-30
    kl = np.sum(p[mask] * np.log(p[mask] / np.maximum(solver.p_ss[mask], 1e-30))) * dx**2

    # (4) EP(t) = ∫ |j|² / (D p) dx  (p > threshold の領域のみ)
    j1, j2 = solver.current(p)
    p_thresh = np.max(p) * 1e-6
    safe = p > p_thresh
    ep = np.sum((j1[safe]**2 + j2[safe]**2) / (solver.D * p[safe])) * dx**2

    # (5) EP_ss (定常 EP — housekeeping のみ)
    j1_ss, j2_ss = solver.current(solver.p_ss)
    p_ss_thresh = np.max(solver.p_ss) * 1e-6
    safe_ss = solver.p_ss > p_ss_thresh
    ep_ss = np.sum((j1_ss[safe_ss]**2 + j2_ss[safe_ss]**2) / (
        solver.D * solver.p_ss[safe_ss])) * dx**2

    # (6) g^{(c,F)} の直接推定: ω±Δω での |j| の比較
    # 正規化した Fisher 的指標: ∫ [(|j_+| - |j_-|) / (2Δω)]² / |j|² p dx
    # これは ∫ (∂_ω log|j|)² p dx の有限差分近似
    j1_p, j2_p = FPSolver.__new__(FPSolver), None  # solver_plus を別途使う

    # → 代わりに、trade-off 比率を
    #   R(t) = I_F(t) / I_F^{sp} として追跡
    # 定常で R → 1、過渡で R ≠ 1

    R_IF = I_F_t / solver.I_F_ss if solver.I_F_ss > 1e-30 else float("nan")

    return {
        "I_F": I_F_t,
        "I_F_ss": solver.I_F_ss,
        "R_IF": R_IF,
        "dp_norm": dp_norm,
        "KL": kl,
        "EP": ep,
        "EP_ss": ep_ss,
        "EP_ratio": ep / ep_ss if ep_ss > 1e-30 else float("nan"),
    }


# ---------------------------------------------------------------------------
# 実験
# ---------------------------------------------------------------------------

def run_experiment(pot: Potential, sigma: float = 1.0, omega: float = 1.0,
                   d_omega: float = 0.1, N: int = 80, L: float = 4.0,
                   dt: float = 0.0003, n_steps: int = 10000,
                   report_every: int = 1000) -> list[dict]:
    """FP を ω, ω±Δω で並列時間発展させ、各計量の時間挙動を追跡。"""
    print(f"\n  ▸ {pot.name}  (σ={sigma}, ω={omega}, Δω={d_omega}, "
          f"N={N}, dt={dt}, T={n_steps*dt:.1f})")

    sol   = FPSolver(pot, sigma, omega, N, L)
    sol_p = FPSolver(pot, sigma, omega + d_omega, N, L)
    sol_m = FPSolver(pot, sigma, omega - d_omega, N, L)

    p   = sol.init_gauss()
    p_p = sol_p.init_gauss()
    p_m = sol_m.init_gauss()

    hdr = (f"    {'t':>6}  {'I_F(t)':>10}  {'I_F^ss':>10}  {'R_IF':>8}  "
           f"{'‖∂ωp‖':>10}  {'KL':>8}  {'EP(t)':>10}  {'EP_ss':>10}  "
           f"{'EP_ratio':>8}")
    sep = "    " + "─" * len(hdr.strip())
    print(hdr)
    print(sep)

    results = []

    for i in range(n_steps + 1):
        if i % report_every == 0:
            t = i * dt
            m = compute_metrics(sol, p, p_p, p_m, d_omega)
            m["t"] = t
            results.append(m)

            print(f"    {t:6.3f}  {m['I_F']:10.4f}  {m['I_F_ss']:10.4f}  "
                  f"{m['R_IF']:8.4f}  {m['dp_norm']:10.2e}  {m['KL']:8.4f}  "
                  f"{m['EP']:10.4f}  {m['EP_ss']:10.4f}  {m['EP_ratio']:8.4f}")

        if i < n_steps:
            p   = sol.step(p, dt)
            p_p = sol_p.step(p_p, dt)
            p_m = sol_m.step(p_m, dt)

    return results


def main():
    print("=" * 80)
    print("過渡過程における trade-off 恒等式の検証 (v2)")
    print("  追跡量: I_F(t)→I_F^{sp}, ‖∂_ω p‖→0, KL→0, EP→EP_ss")
    print("=" * 80)

    pots = make_potentials()
    all_r: dict[str, list[dict]] = {}
    t0 = time.time()

    for pot in pots:
        L = 4.0
        if pot.name == "DoubleWell":
            L = 3.5  # 双峰に合わせて少し狭く
        all_r[pot.name] = run_experiment(
            pot, sigma=1.0, omega=1.0,
            N=60, L=L, dt=0.0005, n_steps=8000, report_every=1000,
        )

    elapsed = time.time() - t0

    # ── サマリ ──
    print(f"\n{'='*80}")
    print(f"サマリ  (計算時間: {elapsed:.1f}s)")
    print(f"{'='*80}\n")

    for name, rs in all_r.items():
        r0, rf = rs[0], rs[-1]
        print(f"  {name}:")
        print(f"    I_F:     {r0['I_F']:.4f} → {rf['I_F']:.4f}  "
              f"(定常 {rf['I_F_ss']:.4f}, 比率 {rf['R_IF']:.4f})")
        print(f"    ‖∂ωp‖:  {r0['dp_norm']:.2e} → {rf['dp_norm']:.2e}")
        print(f"    KL:      {r0['KL']:.4f} → {rf['KL']:.4f}")
        print(f"    EP:      {r0['EP']:.4f} → {rf['EP']:.4f}  "
              f"(定常 {rf['EP_ss']:.4f}, 比率 {rf['EP_ratio']:.4f})")

        # 減衰率推定
        kls = [(r["t"], r["KL"]) for r in rs if r["KL"] > 1e-10]
        if len(kls) >= 2:
            t1, k1 = kls[1]  # t=0 は skip (初期条件)
            t2, k2 = kls[-1]
            if k1 > 0 and k2 > 0 and t2 > t1:
                rate = -(np.log(k2) - np.log(k1)) / (t2 - t1)
                print(f"    KL 減衰率 ≈ {rate:.2f}")
        print()

    print("  解釈:")
    print("    R_IF(t) = I_F(t)/I_F^{sp} → 過渡過程での Fisher 情報の変形")
    print("    R_IF → 1 かつ KL → 0 が定常到達の指標")
    print("    ‖∂_ω p‖ → 0 は trade-off 恒等式の異常項消滅の指標")
    print("    EP_ratio → 1 は過渡 EP が定常 EP (housekeeping) に収束する指標")


if __name__ == "__main__":
    main()
