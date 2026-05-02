#!/usr/bin/env python3
"""
E9: ker(G) の実測 — G∘F 前後の embedding 差分 PCA

PURPOSE:
  G (蒸留) が embedding 空間上でどの方向に情報を落とすかを測定する。
  ker(G) = {Scale, Valence} の仮説を PoC データで検証。

仮説:
  H0: G∘F 前後の差分ベクトル Δe は等方的 (ker(G) は特定方向を持たない)
  H1: Δe は低ランク (少数の主成分に集中 → ker(G) に方向性がある)

測定手法:
  1. G∘F 前: 各チャンク境界 step の embedding (boundary embedding)
  2. G∘F 後: 境界が G∘F で統合された場合の embedding (chunk centroid)
  3. 差分: Δe_i = centroid(chunk) - e_i (境界 step の embedding が chunk に「溶けた」方向)
  4. PCA on Δe → 主成分 = G が情報を落とす方向

代替手法 (チャンク内分散分析):
  G が情報を保存する方向 = チャンク内分散が小さい方向
  G が情報を捨てる方向 = チャンク内分散が大きい方向
  → PCA on within-chunk residuals

SOURCE: PINAKAS_TASK T-002
依存: numpy, scipy, sklearn, embedding_cache.pkl, results.json
"""

import json
import pickle
import numpy as np
from pathlib import Path
from collections import defaultdict

HGK_ROOT = Path.home() / "Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
POC_DIR = HGK_ROOT / "60_実験｜Peira/06_Hyphē実験｜HyphePoC"


def load_data():
    """Load embedding cache and chunking results."""
    with open(POC_DIR / "embedding_cache.pkl", "rb") as f:
        cache = pickle.load(f)
    results = json.load(open(POC_DIR / "results.json", encoding="utf-8"))
    return cache, results


def parse_step_range(sr: str) -> tuple[int, int]:
    """Parse '0-5' → (0, 5)."""
    parts = sr.split("-")
    return int(parts[0]), int(parts[1])


def method_1_boundary_drift(cache, results):
    """
    Method 1: Boundary Drift Analysis
    境界 step が chunk centroid に「引き寄せられる」方向を測定。

    Δe_i = centroid(chunk_containing_i) - e_i
    → PCA(Δe) の主成分 = G が情報を落とす方向
    """
    print("\n" + "=" * 60)
    print("Method 1: Boundary Drift — G∘F が境界を引き寄せる方向")
    print("=" * 60)

    all_deltas = []
    all_embeddings = []

    for r in results:
        sid = r["session_id"]
        if sid not in cache:
            continue
        embs = np.array(cache[sid]["embeddings"])
        n_steps = embs.shape[0]

        for chunk in r["chunks"]:
            start, end = parse_step_range(chunk["step_range"])
            end = min(end, n_steps - 1)
            if end <= start:
                continue

            chunk_embs = embs[start:end + 1]
            centroid = chunk_embs.mean(axis=0)

            # Boundary steps: first and last of chunk
            for boundary_idx in [start, end]:
                if boundary_idx < n_steps:
                    delta = centroid - embs[boundary_idx]
                    all_deltas.append(delta)
                    all_embeddings.append(embs[boundary_idx])

    X_delta = np.array(all_deltas)
    print(f"  Boundary drift vectors: {X_delta.shape}")

    return pca_analysis(X_delta, "Boundary Drift")


def method_2_within_chunk_residual(cache, results):
    """
    Method 2: Within-Chunk Residual Analysis
    各 step の embedding からチャンク centroid を引いた残差を分析。

    残差の分散が大きい方向 = G が保存しなかった情報 = ker(G) の方向
    残差の分散が小さい方向 = G が保存した情報 = image(G) の方向
    """
    print("\n" + "=" * 60)
    print("Method 2: Within-Chunk Residuals — G が捨てた情報の方向")
    print("=" * 60)

    all_residuals = []

    for r in results:
        sid = r["session_id"]
        if sid not in cache:
            continue
        embs = np.array(cache[sid]["embeddings"])
        n_steps = embs.shape[0]

        for chunk in r["chunks"]:
            start, end = parse_step_range(chunk["step_range"])
            end = min(end, n_steps - 1)
            if end - start < 2:
                continue

            chunk_embs = embs[start:end + 1]
            centroid = chunk_embs.mean(axis=0)
            residuals = chunk_embs - centroid
            all_residuals.append(residuals)

    X_residual = np.vstack(all_residuals)
    print(f"  Within-chunk residual vectors: {X_residual.shape}")

    return pca_analysis(X_residual, "Within-Chunk Residual")


def method_3_between_vs_within(cache, results):
    """
    Method 3: Between-Chunk vs Within-Chunk variance decomposition

    Total variance = Between-chunk variance + Within-chunk variance

    方向ごとに Between/Within の比率を計算:
    - 高い方向 = G が保存した情報 (チャンク間で異なる = 弁別的)
    - 低い方向 = G が捨てた情報 (チャンク内で異なる = ノイズ)
    """
    print("\n" + "=" * 60)
    print("Method 3: Between/Within Variance Ratio — Fisher 判別分析的")
    print("=" * 60)

    chunk_data = []  # list of (centroid, embeddings)

    for r in results:
        sid = r["session_id"]
        if sid not in cache:
            continue
        embs = np.array(cache[sid]["embeddings"])
        n_steps = embs.shape[0]

        for chunk in r["chunks"]:
            start, end = parse_step_range(chunk["step_range"])
            end = min(end, n_steps - 1)
            if end - start < 2:
                continue
            chunk_embs = embs[start:end + 1]
            centroid = chunk_embs.mean(axis=0)
            chunk_data.append((centroid, chunk_embs))

    if len(chunk_data) < 5:
        print("  Insufficient chunks for analysis")
        return None

    # Global mean
    all_embs = np.vstack([cd[1] for cd in chunk_data])
    global_mean = all_embs.mean(axis=0)
    n_total = all_embs.shape[0]
    d = all_embs.shape[1]

    # Between-chunk scatter
    S_b = np.zeros((d, d))
    for centroid, chunk_embs in chunk_data:
        n_k = chunk_embs.shape[0]
        diff = (centroid - global_mean).reshape(-1, 1)
        S_b += n_k * (diff @ diff.T)
    S_b /= n_total

    # Within-chunk scatter
    S_w = np.zeros((d, d))
    for centroid, chunk_embs in chunk_data:
        residuals = chunk_embs - centroid
        S_w += residuals.T @ residuals
    S_w /= n_total

    # Eigendecompose S_w (within-chunk = directions G discards)
    print(f"  Chunks: {len(chunk_data)}, Total steps: {n_total}, Dim: {d}")

    # Use S_w eigenvalues for ker(G) directions
    print("\n  Within-chunk scatter (S_w) — ker(G) 候補方向:")
    evals_w = np.sort(np.linalg.eigvalsh(S_w))[::-1]
    evals_b = np.sort(np.linalg.eigvalsh(S_b))[::-1]

    # Effective dimensions
    cumvar_w = np.cumsum(evals_w) / np.sum(evals_w)
    cumvar_b = np.cumsum(evals_b) / np.sum(evals_b)
    k_w_90 = int(np.searchsorted(cumvar_w, 0.90) + 1)
    k_b_90 = int(np.searchsorted(cumvar_b, 0.90) + 1)

    print(f"    k_eff_90 (within): {k_w_90}")
    print(f"    k_eff_90 (between): {k_b_90}")
    print(f"    Top 10 within eigenvalues:  {[f'{v:.6f}' for v in evals_w[:10]]}")
    print(f"    Top 10 between eigenvalues: {[f'{v:.6f}' for v in evals_b[:10]]}")

    # Fisher ratio per direction (using PCA basis)
    # Project onto top PCA directions of total variance
    X_centered = all_embs - global_mean
    cov_total = X_centered.T @ X_centered / n_total

    # Get top k eigenvectors
    k_analyze = min(50, d - 1)
    from scipy.sparse.linalg import eigsh
    _, V_total = eigsh(cov_total, k=k_analyze, which='LM')
    V_total = V_total[:, ::-1]  # descending order

    # Project S_b and S_w onto these directions
    fisher_ratios = []
    for i in range(k_analyze):
        v = V_total[:, i]
        var_b = v @ S_b @ v
        var_w = v @ S_w @ v
        ratio = var_b / max(var_w, 1e-10)
        fisher_ratios.append(ratio)

    fisher_ratios = np.array(fisher_ratios)
    sorted_idx = np.argsort(fisher_ratios)

    print(f"\n  Fisher ratio (between/within) per PCA direction:")
    print(f"    Highest (image(G) = G preserves):")
    for i in sorted_idx[-5:][::-1]:
        print(f"      PC-{i+1}: ratio={fisher_ratios[i]:.4f}")
    print(f"    Lowest (ker(G) = G discards):")
    for i in sorted_idx[:5]:
        print(f"      PC-{i+1}: ratio={fisher_ratios[i]:.4f}")

    # Sloppy gap in Fisher ratios
    log_ratios = np.log10(np.maximum(np.sort(fisher_ratios)[::-1], 1e-10))
    gaps = np.diff(-log_ratios)
    if len(gaps) > 0:
        max_gap_idx = int(np.argmax(gaps))
        print(f"\n  Sloppy gap in Fisher ratios at PC-{max_gap_idx + 1}")
        print(f"    k_image(G) ≈ {max_gap_idx + 1} (directions G preserves)")
        print(f"    k_ker(G) ≈ {k_analyze - max_gap_idx - 1} (directions G discards)")

    return {
        "k_within_90": k_w_90,
        "k_between_90": k_b_90,
        "fisher_ratios": fisher_ratios.tolist(),
        "top5_image_G": [int(i) for i in sorted_idx[-5:][::-1]],
        "top5_ker_G": [int(i) for i in sorted_idx[:5]],
    }


def pca_analysis(X: np.ndarray, label: str) -> dict:
    """PCA analysis on a matrix and report effective dimensionality."""
    X_centered = X - X.mean(axis=0)
    n, d = X_centered.shape

    if n < d:
        gram = X_centered @ X_centered.T / n
        eigenvalues, eigenvectors_gram = np.linalg.eigh(gram)
        idx = eigenvalues.argsort()[::-1]
        eigenvalues = eigenvalues[idx]
        # Recover eigenvectors in original space
        eigenvectors_gram = eigenvectors_gram[:, idx]
        V = X_centered.T @ eigenvectors_gram
        norms = np.linalg.norm(V, axis=0, keepdims=True)
        V = V / np.maximum(norms, 1e-10)
    else:
        cov = X_centered.T @ X_centered / n
        eigenvalues, V = np.linalg.eigh(cov)
        idx = eigenvalues.argsort()[::-1]
        eigenvalues = eigenvalues[idx]
        V = V[:, idx]

    eigenvalues = eigenvalues[eigenvalues > 1e-10]
    cumvar = np.cumsum(eigenvalues) / np.sum(eigenvalues)

    k_50 = int(np.searchsorted(cumvar, 0.50) + 1)
    k_90 = int(np.searchsorted(cumvar, 0.90) + 1)
    k_95 = int(np.searchsorted(cumvar, 0.95) + 1)

    # Sloppy spectrum gap
    log_evs = np.log10(np.maximum(eigenvalues[:min(30, len(eigenvalues))], 1e-20))
    gaps = np.diff(-log_evs)
    max_gap_idx = int(np.argmax(gaps)) if len(gaps) > 0 else 0
    k_signal = max_gap_idx + 1

    print(f"\n  {label} PCA Results:")
    print(f"    Total vectors: {X.shape[0]}")
    print(f"    k_eff_50: {k_50}")
    print(f"    k_eff_90: {k_90}")
    print(f"    k_eff_95: {k_95}")
    print(f"    k_signal (sloppy gap at): {k_signal}")
    print(f"    Top 10 eigenvalues: {[f'{v:.6f}' for v in eigenvalues[:10]]}")
    print(f"    Explained variance top-5: {[f'{v:.1%}' for v in (eigenvalues[:5]/eigenvalues.sum())]}")

    # Concentration measure
    gini = 1 - 2 * np.sum(cumvar) / len(cumvar)
    print(f"    Gini coefficient: {gini:.4f} (1=fully concentrated, 0=uniform)")

    if k_signal <= 5:
        print(f"    ★ 高度に集中: ker(G) は {k_signal} 方向に集約")
    elif k_signal <= 15:
        print(f"    ○ 中程度の集中: ker(G) は {k_signal} 方向")
    else:
        print(f"    △ 分散的: ker(G) は等方的傾向 (H0 支持)")

    return {
        "n_vectors": X.shape[0],
        "k_eff_50": k_50,
        "k_eff_90": k_90,
        "k_eff_95": k_95,
        "k_signal": k_signal,
        "gini": float(gini),
        "eigenvalues_top30": eigenvalues[:30].tolist(),
    }


def main():
    print("=" * 60)
    print("E9: ker(G) の実測 — G∘F 前後の embedding 差分 PCA")
    print("=" * 60)

    cache, results = load_data()
    print(f"Sessions: {len(results)}")
    total_steps = sum(r["total_steps"] for r in results)
    total_chunks = sum(r["num_chunks"] for r in results)
    print(f"Total steps: {total_steps}, Total chunks: {total_chunks}")

    # Method 1: Boundary drift
    m1 = method_1_boundary_drift(cache, results)

    # Method 2: Within-chunk residuals
    m2 = method_2_within_chunk_residual(cache, results)

    # Method 3: Between/Within variance
    m3 = method_3_between_vs_within(cache, results)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY — ker(G) 構造の検証")
    print("=" * 60)

    if m1 and m2:
        print(f"\n  Method 1 (Boundary Drift):      k_signal={m1['k_signal']}, gini={m1['gini']:.3f}")
        print(f"  Method 2 (Within-Chunk Residual): k_signal={m2['k_signal']}, gini={m2['gini']:.3f}")

        if m1["k_signal"] <= 5 and m2["k_signal"] <= 5:
            print("\n  ★★ 強い証拠: ker(G) は少数方向に集中 → 方向性忘却")
            print("     → linkage_crystallization.md の「ker(G) = {Scale, Valence}」仮説と整合")
            print("     → Paper I の F_{ij} (忘却曲率) が非ゼロ")
        elif m1["k_signal"] <= 15 or m2["k_signal"] <= 15:
            print("\n  ○ 中程度の証拠: ker(G) に構造あり、ただし 2座標より多い")
        else:
            print("\n  △ 弱い証拠: ker(G) は等方的傾向 → H0 棄却困難")

    if m3:
        print(f"\n  Method 3 (Fisher ratio):")
        print(f"    k_between_90 (image(G)): {m3['k_between_90']}")
        print(f"    k_within_90 (ker(G)):    {m3['k_within_90']}")

    # Save
    output = {
        "experiment": "e9_kerG_measurement",
        "method_1_boundary_drift": m1,
        "method_2_within_chunk_residual": m2,
        "method_3_fisher_ratio": m3,
    }
    out_path = POC_DIR / "e9_kerG_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved: {out_path}")


if __name__ == "__main__":
    main()
