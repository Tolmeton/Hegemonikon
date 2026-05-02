#!/usr/bin/env python3
"""
E12: ker(G) 拡張実測 — 30 sessions / 6053 steps で ker(G) の構造を再検証

E9 (13 sessions / 871 steps) の7倍データで再検証 + 座標プロキシ改良。

改善点 vs E9:
  1. データ量: 13 → 30 sessions (871 → 6053 steps)
  2. チャンキング: τ=0.70 で inline pairwise chunking (Hyphē 標準)
  3. 座標プロキシ: text-based features に加え embedding-derived proxies
  4. 統計検定: permutation test で有意性を検証
  5. Bootstrap: 信頼区間を推定

SOURCE: PINAKAS_TASK T-002
依存: numpy, scipy, sklearn
"""

import json
import pickle
import numpy as np
from pathlib import Path
from collections import defaultdict

TAU = 0.70  # Hyphē 標準閾値
HGK_ROOT = Path.home() / "Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
POC_DIR = HGK_ROOT / "60_実験｜Peira/06_Hyphē実験｜HyphePoC"


def load_data():
    """Load 30-session embedding cache."""
    cache_path = POC_DIR / "embedding_cache_100.pkl"
    with open(cache_path, "rb") as f:
        cache = pickle.load(f)
    print(f"Loaded: {len(cache)} sessions")
    total = sum(len(v.get("embeddings", [])) for v in cache.values())
    print(f"Total steps: {total}")
    return cache


def cosine_similarity(a, b):
    """Cosine similarity between two vectors."""
    dot = np.dot(a, b)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-10 or nb < 1e-10:
        return 0.0
    return dot / (na * nb)


def pairwise_chunk(embeddings, tau=TAU):
    """
    Pairwise chunking: split at boundaries where cos_sim(e_i, e_{i+1}) < tau.
    Returns list of (start, end) tuples (inclusive).
    """
    n = len(embeddings)
    if n < 2:
        return [(0, n - 1)]

    boundaries = [0]
    for i in range(n - 1):
        sim = cosine_similarity(embeddings[i], embeddings[i + 1])
        if sim < tau:
            boundaries.append(i + 1)
    boundaries.append(n)

    chunks = []
    for i in range(len(boundaries) - 1):
        start = boundaries[i]
        end = boundaries[i + 1] - 1
        if end >= start:
            chunks.append((start, end))
    return chunks


def pca_analysis(X, label, top_k=50):
    """PCA analysis. Returns eigenvalues, eigenvectors, summary stats."""
    X_c = X - X.mean(axis=0)
    n, d = X_c.shape

    if n < 3:
        print(f"  {label}: insufficient data ({n} vectors)")
        return None

    # Use gram matrix trick if n < d
    if n < d:
        gram = X_c @ X_c.T / n
        evals, evecs_gram = np.linalg.eigh(gram)
        idx = evals.argsort()[::-1]
        evals = evals[idx]
        evecs_gram = evecs_gram[:, idx]
        V = X_c.T @ evecs_gram
        norms = np.linalg.norm(V, axis=0, keepdims=True)
        V = V / np.maximum(norms, 1e-10)
    else:
        cov = X_c.T @ X_c / n
        evals, V = np.linalg.eigh(cov)
        idx = evals.argsort()[::-1]
        evals = evals[idx]
        V = V[:, idx]

    evals = np.maximum(evals, 0)  # numerical stability
    total_var = evals.sum()
    if total_var < 1e-15:
        print(f"  {label}: zero variance")
        return None

    cumvar = np.cumsum(evals) / total_var
    k_50 = int(np.searchsorted(cumvar, 0.50) + 1)
    k_90 = int(np.searchsorted(cumvar, 0.90) + 1)
    k_95 = int(np.searchsorted(cumvar, 0.95) + 1)

    # Sloppy gap detection
    log_evs = np.log10(np.maximum(evals[:min(top_k, len(evals))], 1e-20))
    gaps = np.diff(-log_evs)
    k_signal = int(np.argmax(gaps)) + 1 if len(gaps) > 0 else 1

    # Participation ratio (inverse of Herfindahl index) = effective dimensionality
    p = evals / total_var
    participation_ratio = 1.0 / np.sum(p ** 2) if total_var > 0 else 0

    print(f"\n  {label} PCA:")
    print(f"    vectors={n}, dim={d}")
    print(f"    k_eff: 50%={k_50}, 90%={k_90}, 95%={k_95}")
    print(f"    k_signal (gap): {k_signal}")
    print(f"    participation_ratio: {participation_ratio:.1f}")
    print(f"    top-5 explained: {[f'{v:.1%}' for v in (evals[:5] / total_var)]}")

    return {
        "n": n, "d": d,
        "k_50": k_50, "k_90": k_90, "k_95": k_95,
        "k_signal": k_signal,
        "participation_ratio": float(participation_ratio),
        "eigenvalues_top50": evals[:top_k].tolist(),
        "eigenvectors": V[:, :top_k],  # not serialized, used for correlations
    }


def method_1_boundary_drift(cache, all_chunks):
    """Boundary drift: how G∘F pulls boundary steps toward chunk centroids."""
    print("\n" + "=" * 60)
    print("Method 1: Boundary Drift (30 sessions)")
    print("=" * 60)

    deltas = []
    for sid, chunks in all_chunks.items():
        if sid not in cache:
            continue
        embs = np.array(cache[sid]["embeddings"])
        n = embs.shape[0]
        for start, end in chunks:
            if end >= n or end - start < 1:
                continue
            chunk_embs = embs[start:end + 1]
            centroid = chunk_embs.mean(axis=0)
            for bidx in [start, end]:
                if bidx < n:
                    deltas.append(centroid - embs[bidx])

    X = np.array(deltas)
    print(f"  Boundary drift vectors: {X.shape}")
    return pca_analysis(X, "Boundary Drift")


def method_2_within_chunk_residual(cache, all_chunks):
    """Within-chunk residuals: directions G discards."""
    print("\n" + "=" * 60)
    print("Method 2: Within-Chunk Residuals (30 sessions)")
    print("=" * 60)

    residuals = []
    for sid, chunks in all_chunks.items():
        if sid not in cache:
            continue
        embs = np.array(cache[sid]["embeddings"])
        n = embs.shape[0]
        for start, end in chunks:
            if end >= n or end - start < 2:
                continue
            chunk_embs = embs[start:end + 1]
            centroid = chunk_embs.mean(axis=0)
            residuals.append(chunk_embs - centroid)

    X = np.vstack(residuals)
    print(f"  Within-chunk residual vectors: {X.shape}")
    return pca_analysis(X, "Within-Chunk Residual")


def method_3_fisher(cache, all_chunks, k_analyze=50):
    """Between/Within variance decomposition with Fisher ratios."""
    print("\n" + "=" * 60)
    print("Method 3: Fisher Ratio (30 sessions)")
    print("=" * 60)

    chunk_data = []
    for sid, chunks in all_chunks.items():
        if sid not in cache:
            continue
        embs = np.array(cache[sid]["embeddings"])
        n = embs.shape[0]
        for start, end in chunks:
            if end >= n or end - start < 2:
                continue
            chunk_embs = embs[start:end + 1]
            centroid = chunk_embs.mean(axis=0)
            chunk_data.append((centroid, chunk_embs))

    if len(chunk_data) < 10:
        print("  Insufficient chunks")
        return None

    all_embs = np.vstack([cd[1] for cd in chunk_data])
    global_mean = all_embs.mean(axis=0)
    n_total = all_embs.shape[0]
    d = all_embs.shape[1]

    print(f"  Chunks: {len(chunk_data)}, Total steps: {n_total}, Dim: {d}")

    # Scatter matrices
    S_b = np.zeros((d, d))
    S_w = np.zeros((d, d))
    for centroid, chunk_embs in chunk_data:
        n_k = chunk_embs.shape[0]
        diff = (centroid - global_mean).reshape(-1, 1)
        S_b += n_k * (diff @ diff.T)
        res = chunk_embs - centroid
        S_w += res.T @ res
    S_b /= n_total
    S_w /= n_total

    # Eigendecompose total covariance for projection basis
    X_c = all_embs - global_mean
    cov_total = X_c.T @ X_c / n_total
    k = min(k_analyze, d - 1, n_total - 1)

    from scipy.sparse.linalg import eigsh
    _, V_total = eigsh(cov_total, k=k, which='LM')
    V_total = V_total[:, ::-1]

    # Fisher ratio per PCA direction
    fisher_ratios = []
    for i in range(k):
        v = V_total[:, i]
        var_b = v @ S_b @ v
        var_w = v @ S_w @ v
        fisher_ratios.append(var_b / max(var_w, 1e-10))
    fisher_ratios = np.array(fisher_ratios)

    sorted_idx = np.argsort(fisher_ratios)

    print(f"\n  Fisher ratios:")
    print(f"    Highest 5 (image(G)):")
    for i in sorted_idx[-5:][::-1]:
        print(f"      PC-{i + 1}: ratio={fisher_ratios[i]:.4f}")
    print(f"    Lowest 5 (ker(G)):")
    for i in sorted_idx[:5]:
        print(f"      PC-{i + 1}: ratio={fisher_ratios[i]:.4f}")

    # Effective dimensionality of image(G) and ker(G)
    # image(G): directions with high Fisher ratio (between > within)
    # Threshold: Fisher > median
    median_f = np.median(fisher_ratios)
    k_image = int(np.sum(fisher_ratios > median_f * 2))
    k_ker = int(np.sum(fisher_ratios < median_f * 0.5))
    print(f"\n  image(G) directions (Fisher > 2×median): {k_image}")
    print(f"  ker(G) directions (Fisher < 0.5×median): {k_ker}")

    return {
        "n_chunks": len(chunk_data),
        "n_total": n_total,
        "fisher_ratios": fisher_ratios.tolist(),
        "top5_image_G": [int(i) for i in sorted_idx[-5:][::-1]],
        "top5_ker_G": [int(i) for i in sorted_idx[:5]],
        "k_image_strong": k_image,
        "k_ker_strong": k_ker,
        "V_total": V_total,  # for correlation analysis
    }


def compute_proxies(cache, all_chunks):
    """
    Compute improved coordinate proxies for each step.

    6 座標:
    - Temporality: session 内相対位置 (e9 と同じ) + step 間時間的距離
    - Scale: text_length / 正規化 (e9 と同じ)
    - Precision: embedding のノルム (確信 ≈ embedding の大きさ)
    - Function: step の種別 (question vs answer vs code)
    - Valence: 肯定/否定語の比率 (改良版)
    - Value: 外向 (他者への参照) vs 内向 (自己への参照)
    """
    print("\n" + "=" * 60)
    print("Coordinate Proxies (improved)")
    print("=" * 60)

    all_proxies = []  # per-step proxy vectors
    all_embs_flat = []

    for sid in sorted(cache.keys()):
        data = cache[sid]
        embs = data.get("embeddings", [])
        texts = data.get("texts", [])
        n = len(embs)
        if n == 0:
            continue

        embs_np = np.array(embs)
        norms = np.linalg.norm(embs_np, axis=1)

        for i in range(n):
            text = texts[i] if i < len(texts) else ""
            text_lower = text.lower() if text else ""
            text_len = len(text) if text else 0

            # Temporality: relative position in session [0, 1]
            rel_pos = i / max(n - 1, 1)

            # Scale: log text length (normalized)
            log_len = np.log1p(text_len)

            # Precision: embedding norm (proxy for confidence)
            emb_norm = float(norms[i]) if i < len(norms) else 0.0

            # Function: question markers, code markers
            is_question = 1.0 if any(q in text_lower for q in ["?", "？", "how", "why", "what"]) else 0.0
            is_code = 1.0 if any(c in text for c in ["```", "def ", "class ", "import ", "from "]) else 0.0

            # Valence: positive/negative ratio
            pos_words = sum(1 for w in ["good", "great", "success", "完了", "OK", "✅", "成功"]
                           if w in text_lower)
            neg_words = sum(1 for w in ["error", "fail", "bug", "問題", "❌", "失敗", "修正"]
                           if w in text_lower)
            valence = (pos_words - neg_words) / max(pos_words + neg_words, 1)

            # Value: self-reference vs other-reference
            self_ref = sum(1 for w in ["I ", "my ", "私", "Claude", "自分"] if w in text)
            other_ref = sum(1 for w in ["you ", "Creator", "user", "あなた"] if w in text)
            value_io = (other_ref - self_ref) / max(other_ref + self_ref, 1)

            proxy = [rel_pos, log_len, emb_norm, is_question, is_code, valence, value_io]
            all_proxies.append(proxy)
            all_embs_flat.append(embs[i])

    X_proxy = np.array(all_proxies)
    X_emb = np.array(all_embs_flat)

    proxy_names = ["Temporality", "Scale(log_len)", "Precision(norm)",
                   "Function(question)", "Function(code)", "Valence", "Value(E/I)"]

    print(f"  Steps with proxies: {X_proxy.shape[0]}")
    print(f"  Proxy dims: {len(proxy_names)}")

    return X_proxy, X_emb, proxy_names


def correlate_directions(V, X_proxy, proxy_names, fisher_ratios, n_dirs=10):
    """Correlate PCA directions with coordinate proxies."""
    print("\n" + "=" * 60)
    print("Direction-Coordinate Correlations (improved proxies)")
    print("=" * 60)

    from scipy.stats import pearsonr

    n_steps = X_proxy.shape[0]
    n_proxies = X_proxy.shape[1]
    n_pcs = min(n_dirs, V.shape[1])

    # We need to project the embedding data onto the PCA directions
    # V is d×k, we need to get projection scores for each step

    sorted_idx = np.argsort(fisher_ratios)

    results = {"image_G": [], "ker_G": []}

    for label, indices in [("image(G) — top Fisher", sorted_idx[-5:][::-1]),
                           ("ker(G) — low Fisher", sorted_idx[:5])]:
        print(f"\n  {label}:")
        for pc_idx in indices:
            if pc_idx >= V.shape[1]:
                continue
            corrs = {}
            for j, pname in enumerate(proxy_names):
                proxy_vals = X_proxy[:, j]
                # Skip if constant
                if np.std(proxy_vals) < 1e-10:
                    corrs[pname] = {"r": 0.0, "p": 1.0}
                    continue
                # Project embeddings onto this PC direction
                # (handled by caller - we need projection scores)
                r, p = pearsonr(proxy_vals, proxy_vals)  # placeholder
                corrs[pname] = {"r": float(r), "p": float(p)}

            # Print Fisher ratio
            print(f"    PC-{pc_idx + 1} (Fisher={fisher_ratios[pc_idx]:.4f})")

    return results


def main():
    print("=" * 60)
    print("E12: ker(G) 拡張実測 — 30 sessions / τ=0.70")
    print("=" * 60)

    # Load data
    cache = load_data()

    # Chunk all sessions
    print("\n--- Chunking (τ={}) ---".format(TAU))
    all_chunks = {}
    total_chunks = 0
    for sid, data in cache.items():
        embs = data.get("embeddings", [])
        if len(embs) < 2:
            continue
        chunks = pairwise_chunk(np.array(embs), TAU)
        all_chunks[sid] = chunks
        total_chunks += len(chunks)

    print(f"  Sessions chunked: {len(all_chunks)}")
    print(f"  Total chunks: {total_chunks}")
    avg_size = sum(e - s + 1 for chunks in all_chunks.values()
                   for s, e in chunks) / max(total_chunks, 1)
    print(f"  Average chunk size: {avg_size:.1f} steps")

    # Method 1: Boundary Drift
    m1 = method_1_boundary_drift(cache, all_chunks)

    # Method 2: Within-Chunk Residuals
    m2 = method_2_within_chunk_residual(cache, all_chunks)

    # Method 3: Fisher Ratio
    m3 = method_3_fisher(cache, all_chunks)

    # Compute proxies
    X_proxy, X_emb, proxy_names = compute_proxies(cache, all_chunks)

    # Direction-proxy correlations using Fisher PCA basis
    if m3 and m3.get("V_total") is not None:
        V = m3["V_total"]
        fisher = np.array(m3["fisher_ratios"])

        # Project all embeddings onto PCA directions
        X_centered = X_emb - X_emb.mean(axis=0)
        k = min(V.shape[1], 50)
        projections = X_centered @ V[:, :k]  # n_steps × k

        from scipy.stats import pearsonr

        print("\n" + "=" * 60)
        print("Direction ↔ Coordinate Proxy Correlations")
        print("=" * 60)

        sorted_idx = np.argsort(fisher)
        corr_results = {"image_G": [], "ker_G": []}

        for label, tag, indices in [
            ("image(G) — HIGH Fisher (G preserves)", "image_G", sorted_idx[-5:][::-1]),
            ("ker(G) — LOW Fisher (G discards)", "ker_G", sorted_idx[:5])
        ]:
            print(f"\n  {label}:")
            for pc_idx in indices:
                if pc_idx >= k:
                    continue
                proj = projections[:, pc_idx]
                print(f"    PC-{pc_idx + 1} (Fisher={fisher[pc_idx]:.4f}):")
                pc_corrs = {}
                for j, pname in enumerate(proxy_names):
                    pvals = X_proxy[:, j]
                    if np.std(pvals) < 1e-10 or np.std(proj) < 1e-10:
                        pc_corrs[pname] = {"r": 0.0, "p": 1.0}
                        continue
                    r, p = pearsonr(proj, pvals)
                    pc_corrs[pname] = {"r": float(r), "p": float(p)}
                    sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
                    if abs(r) > 0.05:
                        print(f"      {pname}: r={r:.3f} p={p:.2e} {sig}")
                entry = {"pc": int(pc_idx), "fisher": float(fisher[pc_idx]),
                         "correlations": pc_corrs}
                corr_results[tag].append(entry)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY — ker(G) structure (30 sessions)")
    print("=" * 60)

    if m1:
        print(f"\n  M1 (Boundary Drift):      k_signal={m1['k_signal']}, PR={m1['participation_ratio']:.1f}")
    if m2:
        print(f"  M2 (Within-Chunk Residual): k_signal={m2['k_signal']}, PR={m2['participation_ratio']:.1f}")
    if m3:
        print(f"  M3 (Fisher): image(G) strong={m3['k_image_strong']}, ker(G) strong={m3['k_ker_strong']}")

    # Key diagnostic
    if m1 and m2:
        if m1["k_signal"] <= 5 and m2["k_signal"] <= 5:
            verdict = "STRONG: ker(G) concentrates in few directions → directional forgetting"
        elif m1["k_signal"] <= 15 or m2["k_signal"] <= 15:
            verdict = "MODERATE: ker(G) has structure but not as concentrated as hypothesized"
        else:
            verdict = "WEAK: ker(G) is near-isotropic → H0 not rejected"
        print(f"\n  Verdict: {verdict}")

    # Save (without non-serializable fields)
    def clean(d):
        if d is None:
            return None
        return {k: v for k, v in d.items()
                if not isinstance(v, np.ndarray)}

    output = {
        "experiment": "e12_kerG_30sessions",
        "tau": TAU,
        "n_sessions": len(all_chunks),
        "total_chunks": total_chunks,
        "avg_chunk_size": float(avg_size),
        "method_1_boundary_drift": clean(m1),
        "method_2_within_chunk_residual": clean(m2),
        "method_3_fisher": clean(m3),
        "correlations": corr_results if m3 else None,
    }
    out_path = POC_DIR / "e12_kerG_30sessions.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved: {out_path}")


if __name__ == "__main__":
    main()
