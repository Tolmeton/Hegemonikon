#!/usr/bin/env python3
"""Hyphē-Possati 接続分析 — 離散と連続の対応検証

PURPOSE: Hyphē (離散 cosine similarity) と Possati PDE (連続 ρ(x)) が
同じ underlying structure を測定しているかを検証する。

接続方法:
  1. PDE 後の embedding 空間から per-session ρ を計算
  2. Hyphē の per-session coherence/drift と比較
  3. Spearman 相関で対応を定量化

予測:
  - Hyphē coherence ↑ ⇔ PDE ρ ↑ (正の相関)
  - Hyphē drift ↑ ⇔ PDE ρ ↓ (負の相関)

入力:
  - possati_pde_poc.py のキャッシュと PDE パラメータ
  - HyphePoC/results.json
出力:
  - 相関統計 + JSON 結果
"""

import json
import pickle
import sys
from pathlib import Path

import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr

# === パス ===
HGK_ROOT = Path("/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon")
HYPHE_DIR = HGK_ROOT / "60_実験｜Peira" / "06_Hyphē実験｜HyphePoC"
SLOPPY_DIR = HGK_ROOT / "60_実験｜Peira" / "05_スペクトル解析｜SloppySpectrum"
CACHE_FILE = HYPHE_DIR / "embedding_cache.pkl"
RESULTS_FILE = HYPHE_DIR / "results.json"
PDE_RESULTS_FILE = SLOPPY_DIR / "possati_pde_results.json"

# pickle が hyphe_chunker モジュールを参照するため
sys.path.insert(0, str(HYPHE_DIR))

# PDE からのパラメータ (一致させる)
PCA_DIM = 30
K_NEIGHBORS = 7


def load_data():
    """データ読み込み."""
    # Hyphē 結果
    with open(RESULTS_FILE, encoding="utf-8") as f:
        hyphe_results = json.load(f)
    print(f"📂 Hyphē 結果: {len(hyphe_results)} セッション")

    # PDE 結果 (メタデータ確認用)
    with open(PDE_RESULTS_FILE, encoding="utf-8") as f:
        pde_results = json.load(f)
    print(f"📂 PDE 結果: {pde_results['metadata']['n_points']} 点, "
          f"PCA {pde_results['metadata']['pca_dim']}d")

    # Embedding キャッシュ
    with open(CACHE_FILE, "rb") as f:
        cache = pickle.load(f)
    print(f"📂 Embedding キャッシュ: {len(cache)} セッション")

    return hyphe_results, pde_results, cache


def compute_per_session_rho(cache, k=K_NEIGHBORS, pca_dim=PCA_DIM):
    """PDE と同じ前処理で per-session ρ を計算.

    全セッションを結合 → PCA → ρ 計算 → セッション別に集約
    """
    # 全 embedding を結合 (PDE と同じ前処理)
    all_embeddings = []
    session_ids = []
    session_indices = {}  # session_id → [indices]

    idx = 0
    for sid, data in sorted(cache.items()):
        embs = data["embeddings"]
        if isinstance(embs, list):
            embs = np.array(embs)
        n = len(embs)
        all_embeddings.append(embs)
        session_ids.append(sid)
        session_indices[sid] = list(range(idx, idx + n))
        idx += n

    X = np.vstack(all_embeddings)
    print(f"\n🔬 全 embedding: {X.shape}")

    # PCA (PDE と同じ処理)
    X_centered = X - X.mean(axis=0)
    U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
    X_pca = U[:, :pca_dim] * S[:pca_dim]
    explained = (S[:pca_dim] ** 2).sum() / (S ** 2).sum()
    print(f"   PCA: {X.shape[1]}d → {pca_dim}d (累積寄与率: {explained:.3f})")

    # ρ 計算 (PDE と同じ KSG-inspired)
    n = len(X_pca)
    D = cdist(X_pca, X_pca, metric='euclidean')
    sorted_D = np.take_along_axis(D, np.argsort(D, axis=1), axis=1)
    d_inner = sorted_D[:, 1:k+1].mean(axis=1)
    n_outer = min(n // 2, 50)
    d_outer = sorted_D[:, k+1:k+1+n_outer].mean(axis=1)
    rho = np.clip(1.0 - (d_inner / (d_outer + 1e-8)), 0.0, 1.0)

    print(f"   ρ 全体: mean={np.mean(rho):.4f}, std={np.std(rho):.4f}")

    # Per-session 集約
    per_session = {}
    for sid in session_ids:
        indices = session_indices[sid]
        rho_session = rho[indices]
        per_session[sid] = {
            "n_points": len(indices),
            "rho_mean": float(np.mean(rho_session)),
            "rho_std": float(np.std(rho_session)),
            "rho_min": float(np.min(rho_session)),
            "rho_max": float(np.max(rho_session)),
        }
        print(f"   {sid[:8]}: n={len(indices):3d}, ρ̄={np.mean(rho_session):.4f}±{np.std(rho_session):.4f}")

    return per_session


def correlate(hyphe_results, per_session_rho):
    """Hyphē coherence/drift と PDE ρ の相関分析."""
    # session_id のマッチング (Hyphē の短縮 ID で検索)
    matched = []
    for hr in hyphe_results:
        hyphe_sid = hr["session_id"]
        # キャッシュの session_id は完全な UUID、Hyphē は短縮形
        matched_key = None
        for key in per_session_rho:
            if key.startswith(hyphe_sid):
                matched_key = key
                break
        if matched_key:
            matched.append({
                "session_id": hyphe_sid,
                "hyphe_coherence": hr["mean_coherence"],
                "hyphe_drift": hr["mean_drift"],
                "hyphe_steps": hr["total_steps"],
                "hyphe_chunks": hr["num_chunks"],
                "pde_rho_mean": per_session_rho[matched_key]["rho_mean"],
                "pde_rho_std": per_session_rho[matched_key]["rho_std"],
                "pde_n_points": per_session_rho[matched_key]["n_points"],
            })
        else:
            print(f"   ⚠️ マッチなし: {hyphe_sid}")

    print(f"\n📊 マッチ: {len(matched)} / {len(hyphe_results)} セッション")

    if len(matched) < 3:
        print("   ❌ マッチ不足 — 相関計算不可")
        return None, matched

    # 相関計算
    coherences = [m["hyphe_coherence"] for m in matched]
    drifts = [m["hyphe_drift"] for m in matched]
    rhos = [m["pde_rho_mean"] for m in matched]
    steps = [m["hyphe_steps"] for m in matched]

    # Spearman 相関 (順序統計量、小標本に適する)
    r_coh_rho, p_coh_rho = spearmanr(coherences, rhos)
    r_drift_rho, p_drift_rho = spearmanr(drifts, rhos)
    r_steps_rho, p_steps_rho = spearmanr(steps, rhos)

    stats = {
        "coherence_vs_rho": {
            "spearman_r": float(r_coh_rho),
            "p_value": float(p_coh_rho),
            "prediction": "positive",
            "interpretation": "coherence ↑ ⇔ ρ ↑ (密集 = 高品質)",
        },
        "drift_vs_rho": {
            "spearman_r": float(r_drift_rho),
            "p_value": float(p_drift_rho),
            "prediction": "negative",
            "interpretation": "drift ↑ ⇔ ρ ↓ (設計上 drift = 1 - coherence)",
        },
        "steps_vs_rho": {
            "spearman_r": float(r_steps_rho),
            "p_value": float(p_steps_rho),
            "prediction": "unknown",
            "interpretation": "ステップ数と密度の相関 (探索的)",
        },
    }

    print(f"\n{'='*60}")
    print(f"📈 相関結果 (Spearman)")
    print(f"{'='*60}")
    for name, s in stats.items():
        r, p = s["spearman_r"], s["p_value"]
        pred = s["prediction"]
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
        direction = "✅" if (pred == "positive" and r > 0) or (pred == "negative" and r < 0) else "❌" if pred != "unknown" else "🔍"
        print(f"  {name:25s}: r={r:+.3f}, p={p:.4f} {sig} {direction}")
        print(f"    予測: {pred}, 解釈: {s['interpretation']}")

    return stats, matched


def main():
    print("=" * 60)
    print("Hyphē-Possati 接続分析")
    print("=" * 60)

    hyphe_results, pde_results, cache = load_data()
    per_session_rho = compute_per_session_rho(cache)
    stats, matched = correlate(hyphe_results, per_session_rho)

    # 結果保存
    output = {
        "metadata": {
            "description": "Hyphē (離散) と Possati PDE (連続) の接続分析",
            "n_sessions": len(matched),
            "pca_dim": PCA_DIM,
            "k_neighbors": K_NEIGHBORS,
        },
        "correlations": stats,
        "per_session": matched,
    }

    output_path = SLOPPY_DIR / "hyphe_possati_bridge_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n💾 結果保存: {output_path.name}")

    # サマリテーブル
    print(f"\n{'='*60}")
    print(f"📋 Per-Session 対応表")
    print(f"{'='*60}")
    print(f"{'SID':>10s} {'Coh':>6s} {'Drift':>6s} {'Steps':>6s} {'ρ_PDE':>8s} {'ρ_std':>8s}")
    print(f"{'─'*10} {'─'*6} {'─'*6} {'─'*6} {'─'*8} {'─'*8}")
    for m in sorted(matched, key=lambda x: x["pde_rho_mean"], reverse=True):
        print(f"{m['session_id']:>10s} {m['hyphe_coherence']:6.3f} {m['hyphe_drift']:6.3f} "
              f"{m['hyphe_steps']:6d} {m['pde_rho_mean']:8.4f} {m['pde_rho_std']:8.4f}")


if __name__ == "__main__":
    main()
