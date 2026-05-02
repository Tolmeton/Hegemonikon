#!/usr/bin/env python3
"""Possati PDE PoC — MB Density 結晶化実験

PURPOSE: embedding 空間上で ρ(x) (MB density) と L(c) (Kalon 損失) を計算し、
駆動力方程式 ẋ = -(1-ρ(x))·∇F(x) の挙動を観察する。

数学的基盤:
  - ρ(x) = 1 - d_inner/d_outer (KSG-inspired density estimation)
  - ẋ(t) = -(1 - ρ(x)) · ∇F(x)  (Possati 2025)
  - L(c) = λ₁·||G∘F(c)-c||² + λ₂·(-EFE(c))  (Kalon loss)

入力: Hyphē PoC の embedding_cache.pkl (13セッション, 768次元)
出力: ρ(x), ∇F(x), L(c) の時間発展 + JSON 結果

参照: EXPERIMENT_DESIGN.md, Possati 2025 (arXiv:2506.05794)
"""

import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
from scipy.spatial.distance import cdist

# === パス ===
HGK_ROOT = Path("/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon")
HYPHE_DIR = HGK_ROOT / "60_実験｜Peira" / "06_Hyphē実験｜HyphePoC"
SLOPPY_DIR = HGK_ROOT / "60_実験｜Peira" / "05_スペクトル解析｜SloppySpectrum"
CACHE_FILE = HYPHE_DIR / "embedding_cache.pkl"

# pickle が hyphe_chunker モジュールを参照するため
sys.path.insert(0, str(HYPHE_DIR))

# === ハイパーパラメータ ===
K_NEIGHBORS = 7       # KSG 用 k-近傍数
PCA_DIM = 30           # PCA で削減する次元数 (k_eff_90≈33 に近い値)
PDE_DT = 0.002         # PDE の時間刻み (安定性のため縮小)
PDE_STEPS = 500        # PDE のステップ数 (dt 縮小補正)
RECALC_INTERVAL = 2    # ρ/∇F の再計算間隔 (離散化ノイズ最小化)
LAMBDA1 = 1.0          # L(c) の Drift 項係数
LAMBDA2 = 0.01         # L(c) の EFE 項係数 (drift 項優位に)
GF_ALPHA = 0.3         # G∘F サイクルの近似パラメータ (近傍平均への縮約率)


def load_cache():
    """Hyphē PoC の embedding キャッシュを読み込む."""
    print(f"📂 キャッシュ読み込み: {CACHE_FILE.name}")
    with open(CACHE_FILE, "rb") as f:
        cache = pickle.load(f)
    print(f"   {len(cache)} セッション")
    return cache


def flatten_embeddings(cache):
    """全セッションの embedding を1つの行列に統合."""
    all_embeddings = []
    session_labels = []
    for sid, data in sorted(cache.items()):
        embs = data["embeddings"]
        if isinstance(embs, list):
            embs = np.array(embs)
        all_embeddings.append(embs)
        session_labels.extend([sid] * len(embs))
    X = np.vstack(all_embeddings)
    print(f"   全 embedding: {X.shape} (点数 × 次元)")
    return X, session_labels


def reduce_dim(X, n_components=PCA_DIM):
    """PCA で次元削減 (numpy SVD ベース, 高次元 KSG バイアス対策)."""
    X_centered = X - X.mean(axis=0)
    # Truncated SVD — n_components だけ計算
    U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
    X_reduced = U[:, :n_components] * S[:n_components]
    explained = (S[:n_components] ** 2).sum() / (S ** 2).sum()
    print(f"   PCA(SVD): {X.shape[1]}d → {n_components}d (累積寄与率: {explained:.3f})")
    return X_reduced


def compute_rho(X, k=K_NEIGHBORS):
    """KSG-inspired MB density estimation (vectorized).

    ρ(x) = 1 - d_inner / d_outer
    d_inner: k-近傍の平均距離 (ブランケット内)
    d_outer: 遠方の平均距離 (ブランケット外)
    """
    n = len(X)
    # 全点間距離行列 (n×n)
    D = cdist(X, X, metric='euclidean')
    # 各行をソート (距離順)
    sorted_idx = np.argsort(D, axis=1)
    sorted_D = np.take_along_axis(D, sorted_idx, axis=1)

    # d_inner: k-近傍の平均 (index 1..k, 0 は自分自身)
    d_inner = sorted_D[:, 1:k+1].mean(axis=1)
    # d_outer: k+1 以遠の平均
    n_outer = min(n // 2, 50)
    d_outer = sorted_D[:, k+1:k+1+n_outer].mean(axis=1)

    rho = 1.0 - (d_inner / (d_outer + 1e-8))
    rho = np.clip(rho, 0.0, 1.0)
    return rho


def compute_vfe_gradient(X, rho, k=K_NEIGHBORS):
    """VFE 上昇勾配の embedding 空間上の近似 (vectorized).

    ∇F(x_i) ≈ (1/k) Σ_j∈N(i) (ρ_i - ρ_j) · (x_j - x_i) / ||x_j - x_i||

    符号規約: ∇F は VFE の**上昇**方向。
    駆動力 ẋ = -(1-ρ)·∇F で VFE **下降**方向（= ρ 増加方向）に移動。
    """
    n, d = X.shape
    # 距離行列とk近傍インデックス
    D = cdist(X, X, metric='euclidean')
    knn_idx = np.argsort(D, axis=1)[:, 1:k+1]  # 各点のk近傍

    grad_F = np.zeros_like(X)
    for i in range(n):
        neighbors = knn_idx[i]
        deltas = X[neighbors] - X[i]  # (k, d)
        norms = np.linalg.norm(deltas, axis=1, keepdims=True) + 1e-8  # (k, 1)
        # 修正: ρ_i - ρ_j (VFE 上昇方向 = ρ が低い方向)
        rho_diffs = (rho[i] - rho[neighbors]).reshape(-1, 1)  # (k, 1)
        grad_F[i] = (rho_diffs * deltas / norms).mean(axis=0)

    return grad_F


def apply_gf_cycle(X, k=K_NEIGHBORS):
    """G∘F サイクルの embedding 空間上の近似 (vectorized).

    G∘F = 近傍平均への部分的縮約 (merge) + 元位置への弾性復帰 (split)
    x_gf = (1-α)·x + α·mean(N(x))
    """
    D = cdist(X, X, metric='euclidean')
    knn_idx = np.argsort(D, axis=1)[:, 1:k+1]

    # 各点の近傍平均を一括計算
    neighbor_means = np.array([X[knn_idx[i]].mean(axis=0) for i in range(len(X))])
    X_gf = (1 - GF_ALPHA) * X + GF_ALPHA * neighbor_means
    return X_gf


def compute_lc(X, X_gf, k=K_NEIGHBORS, lambda1=LAMBDA1, lambda2=LAMBDA2):
    """L(c) = λ₁·||G∘F(c)-c||² + λ₂·(-EFE(c)).

    Drift: G∘F からの距離 (不動点条件)
    EFE: 近傍方向の angular diversity (展開可能性)
         密集しても方向が多様なら展開可能 → 結晶化と非矛盾
    """
    # Drift: ||G∘F(c) - c||²  (vectorized)
    drift = np.sum((X_gf - X) ** 2, axis=1)  # (n,)

    # EFE: angular diversity (近傍方向ベクトルの分散)
    D = cdist(X, X, metric='euclidean')
    knn_idx = np.argsort(D, axis=1)[:, 1:k+1]
    efe = np.zeros(len(X))
    for i in range(len(X)):
        neighbors = knn_idx[i]
        deltas = X[neighbors] - X[i]  # (k, d)
        norms = np.linalg.norm(deltas, axis=1, keepdims=True) + 1e-8
        directions = deltas / norms  # 正規化方向ベクトル
        # 方向ベクトルの分散 = 全方向に均等に広がる度合い
        efe[i] = np.std(directions, axis=0).mean()

    lc = lambda1 * drift + lambda2 * (-efe)
    return lc


def simulate_pde(X, dt=PDE_DT, steps=PDE_STEPS, recalc_interval=RECALC_INTERVAL):
    """駆動力方程式 ẋ = -(1-ρ(x))·∇F(x) のシミュレーション.

    記録:
    - rho_history: 各ステップの平均 ρ
    - grad_norm_history: 各ステップの ||∇F|| 平均
    - lc_history: 各ステップの L(c) 平均
    - x_trajectory: embedding の軌跡 (一部)
    """
    x = X.copy()
    rho = compute_rho(x)
    grad_F = compute_vfe_gradient(x, rho)

    rho_history = [float(np.mean(rho))]
    rho_std_history = [float(np.std(rho))]
    grad_norm_history = [float(np.mean(np.linalg.norm(grad_F, axis=1)))]

    # L(c) 初期値
    x_gf = apply_gf_cycle(x)
    lc = compute_lc(x, x_gf)
    lc_history = [float(np.mean(lc))]

    print(f"\n🔬 PDE シミュレーション開始")
    print(f"   dt={dt}, steps={steps}, recalc_interval={recalc_interval}")
    print(f"   初期状態: ρ̄={rho_history[0]:.4f}, ||∇F||={grad_norm_history[0]:.6f}, L̄(c)={lc_history[0]:.6f}")

    for t in range(1, steps + 1):
        # 駆動力: ẋ = -(1-ρ(x))·∇F(x)
        mobility = 1.0 - rho  # (1-ρ): ρ=1 なら停止, ρ=0 なら最大移動
        dx = -mobility[:, None] * grad_F
        x = x + dt * dx

        # 周期的に ρ と ∇F を再計算
        if t % recalc_interval == 0:
            rho = compute_rho(x)
            grad_F = compute_vfe_gradient(x, rho)

            # L(c) も再計算
            x_gf = apply_gf_cycle(x)
            lc = compute_lc(x, x_gf)

            rho_history.append(float(np.mean(rho)))
            rho_std_history.append(float(np.std(rho)))
            grad_norm_history.append(float(np.mean(np.linalg.norm(grad_F, axis=1))))
            lc_history.append(float(np.mean(lc)))

            if t % 50 == 0:
                print(f"   t={t:4d}: ρ̄={rho_history[-1]:.4f}±{rho_std_history[-1]:.4f}, "
                      f"||∇F||={grad_norm_history[-1]:.6f}, L̄(c)={lc_history[-1]:.6f}")

    return {
        "final_x": x,
        "rho_history": rho_history,
        "rho_std_history": rho_std_history,
        "grad_norm_history": grad_norm_history,
        "lc_history": lc_history,
    }


def evaluate_results(sim_result):
    """成功基準の評価."""
    rho_h = sim_result["rho_history"]
    grad_h = sim_result["grad_norm_history"]
    lc_h = sim_result["lc_history"]

    # ρ 単調増加チェック
    rho_increases = sum(1 for i in range(1, len(rho_h)) if rho_h[i] > rho_h[i-1])
    rho_monotone = rho_increases / max(len(rho_h) - 1, 1)

    # ∇F 単調減少チェック
    grad_decreases = sum(1 for i in range(1, len(grad_h)) if grad_h[i] < grad_h[i-1])
    grad_monotone = grad_decreases / max(len(grad_h) - 1, 1)

    # L(c) 単調減少チェック
    lc_decreases = sum(1 for i in range(1, len(lc_h)) if lc_h[i] < lc_h[i-1])
    lc_monotone = lc_decreases / max(len(lc_h) - 1, 1)

    # 変化率
    rho_change = rho_h[-1] - rho_h[0]
    grad_change = grad_h[-1] - grad_h[0]
    lc_change = lc_h[-1] - lc_h[0]

    eval_results = {
        "rho_monotone_ratio": rho_monotone,
        "rho_initial": rho_h[0],
        "rho_final": rho_h[-1],
        "rho_change": rho_change,
        "rho_pass": rho_monotone > 0.6,  # 60%+ 単調増加

        "grad_monotone_ratio": grad_monotone,
        "grad_initial": grad_h[0],
        "grad_final": grad_h[-1],
        "grad_change": grad_change,
        "grad_pass": grad_monotone > 0.6,

        "lc_monotone_ratio": lc_monotone,
        "lc_initial": lc_h[0],
        "lc_final": lc_h[-1],
        "lc_change": lc_change,
        "lc_pass": lc_monotone > 0.5,  # L(c) はノイジーなので緩和
    }

    return eval_results


def print_evaluation(eval_results, elapsed):
    """評価結果の表示."""
    print(f"\n{'='*60}")
    print(f"📊 評価結果")
    print(f"{'='*60}")

    metrics = [
        ("ρ(x) 収束", "rho", "単調増加"),
        ("||∇F|| 減少", "grad", "単調減少"),
        ("L(c) 減少", "lc", "単調減少"),
    ]

    for label, prefix, direction in metrics:
        mono = eval_results[f"{prefix}_monotone_ratio"]
        initial = eval_results[f"{prefix}_initial"]
        final = eval_results[f"{prefix}_final"]
        change = eval_results[f"{prefix}_change"]
        passed = eval_results[f"{prefix}_pass"]
        mark = "✅" if passed else "❌"

        print(f"\n  {mark} {label}: {direction} {mono:.1%}")
        print(f"     初期: {initial:.6f} → 最終: {final:.6f} (Δ={change:+.6f})")

    overall = all(eval_results[f"{p}_pass"] for p in ["rho", "grad", "lc"])
    print(f"\n  {'🎉 総合: PASS' if overall else '⚠️ 総合: PARTIAL'}")
    print(f"  ⏱️  計算時間: {elapsed:.1f}秒")


def main():
    print("=" * 60)
    print("Possati PDE PoC — MB Density 結晶化実験")
    print("=" * 60)
    start = time.time()

    # Phase 1: Embedding 空間構築
    print("\n--- Phase 1: Embedding 空間構築 ---")
    cache = load_cache()
    X_raw, session_labels = flatten_embeddings(cache)
    X = reduce_dim(X_raw)

    n_points = len(X)
    print(f"   点数: {n_points}, PCA次元: {X.shape[1]}")

    # Phase 2: 初期 ρ(x) 計算
    print("\n--- Phase 2: ρ(x) 計算 ---")
    rho_initial = compute_rho(X)
    print(f"   ρ(x): mean={np.mean(rho_initial):.4f}, std={np.std(rho_initial):.4f}, "
          f"min={np.min(rho_initial):.4f}, max={np.max(rho_initial):.4f}")

    # Phase 3: PDE シミュレーション
    print("\n--- Phase 3: PDE シミュレーション ---")
    sim_result = simulate_pde(X)

    # Phase 4: 評価
    print("\n--- Phase 4: 評価 ---")
    elapsed = time.time() - start
    eval_results = evaluate_results(sim_result)
    print_evaluation(eval_results, elapsed)

    # 結果保存
    output = {
        "metadata": {
            "n_points": n_points,
            "original_dim": X_raw.shape[1],
            "pca_dim": X.shape[1],
            "k_neighbors": K_NEIGHBORS,
            "pde_dt": PDE_DT,
            "pde_steps": PDE_STEPS,
            "recalc_interval": RECALC_INTERVAL,
            "gf_alpha": GF_ALPHA,
            "lambda1": LAMBDA1,
            "lambda2": LAMBDA2,
            "elapsed_seconds": elapsed,
            "n_sessions": len(cache),
        },
        "evaluation": eval_results,
        "time_series": {
            "rho_mean": sim_result["rho_history"],
            "rho_std": sim_result["rho_std_history"],
            "grad_norm_mean": sim_result["grad_norm_history"],
            "lc_mean": sim_result["lc_history"],
        },
    }

    output_path = SLOPPY_DIR / "possati_pde_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n💾 結果保存: {output_path.name}")


if __name__ == "__main__":
    main()
