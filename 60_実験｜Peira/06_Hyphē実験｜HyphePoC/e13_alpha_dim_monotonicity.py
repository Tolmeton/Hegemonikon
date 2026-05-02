#!/usr/bin/env python3
"""
E13: alpha-dim(image(G)) monotonicity test

Hypothesis (Paper I conjecture 5.9.2):
  As forgetting strength alpha increases, dim(image(G)) decreases monotonically.
  tau is the operational proxy for alpha: higher tau = stricter chunking = stronger forgetting.

Method:
  Sweep tau from 0.50 to 0.95 (step 0.01).
  At each tau, chunk all 30 sessions, compute Fisher ratios, measure:
  - k_image: number of directions with Fisher > 2*median (image(G) effective dim)
  - k_ker: number of directions with Fisher < 0.5*median (ker(G) effective dim)
  - participation_ratio of within-chunk residuals
  - max Fisher ratio (strength of strongest preserved direction)

Prediction:
  tau UP => alpha UP => k_image DOWN (monotonic)
  tau UP => alpha UP => participation_ratio of ker(G) UP (more isotropic)

SOURCE: Paper I conjecture 5.9.2, E12 results, PINAKAS Q candidate
"""

import json
import pickle
import numpy as np
from pathlib import Path

HGK_ROOT = Path.home() / "Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
POC_DIR = HGK_ROOT / "60_実験｜Peira/06_Hyphē実験｜HyphePoC"


def cosine_similarity(a, b):
    dot = np.dot(a, b)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-10 or nb < 1e-10:
        return 0.0
    return dot / (na * nb)


def pairwise_chunk(embeddings, tau):
    n = len(embeddings)
    if n < 2:
        return [(0, n - 1)]
    boundaries = [0]
    for i in range(n - 1):
        if cosine_similarity(embeddings[i], embeddings[i + 1]) < tau:
            boundaries.append(i + 1)
    boundaries.append(n)
    chunks = []
    for i in range(len(boundaries) - 1):
        s, e = boundaries[i], boundaries[i + 1] - 1
        if e >= s:
            chunks.append((s, e))
    return chunks


def fisher_analysis(cache, all_chunks, k_analyze=50):
    """Compute Fisher ratios and return image(G)/ker(G) metrics."""
    chunk_data = []
    for sid, chunks in all_chunks.items():
        if sid not in cache:
            continue
        embs = np.array(cache[sid]["embeddings"])
        n = embs.shape[0]
        for s, e in chunks:
            if e >= n or e - s < 2:
                continue
            ce = embs[s:e + 1]
            chunk_data.append((ce.mean(axis=0), ce))

    if len(chunk_data) < 10:
        return None

    all_embs = np.vstack([cd[1] for cd in chunk_data])
    global_mean = all_embs.mean(axis=0)
    n_total = all_embs.shape[0]
    d = all_embs.shape[1]

    S_b = np.zeros((d, d))
    S_w = np.zeros((d, d))
    for centroid, ce in chunk_data:
        nk = ce.shape[0]
        diff = (centroid - global_mean).reshape(-1, 1)
        S_b += nk * (diff @ diff.T)
        res = ce - centroid
        S_w += res.T @ res
    S_b /= n_total
    S_w /= n_total

    X_c = all_embs - global_mean
    cov = X_c.T @ X_c / n_total
    k = min(k_analyze, d - 1, n_total - 1)

    from scipy.sparse.linalg import eigsh
    _, V = eigsh(cov, k=k, which='LM')
    V = V[:, ::-1]

    fisher = np.array([
        (V[:, i] @ S_b @ V[:, i]) / max(V[:, i] @ S_w @ V[:, i], 1e-10)
        for i in range(k)
    ])

    median_f = np.median(fisher)
    k_image = int(np.sum(fisher > median_f * 2))
    k_ker = int(np.sum(fisher < median_f * 0.5))

    # Within-chunk residual participation ratio
    residuals = []
    for centroid, ce in chunk_data:
        residuals.append(ce - centroid)
    X_res = np.vstack(residuals)
    X_rc = X_res - X_res.mean(axis=0)
    cov_res = X_rc.T @ X_rc / X_rc.shape[0]
    evals_res = np.sort(np.linalg.eigvalsh(cov_res))[::-1]
    evals_res = np.maximum(evals_res, 0)
    total = evals_res.sum()
    if total > 1e-15:
        p = evals_res / total
        pr = 1.0 / np.sum(p ** 2)
    else:
        pr = 0.0

    return {
        "n_chunks": len(chunk_data),
        "n_steps": n_total,
        "k_image": k_image,
        "k_ker": k_ker,
        "max_fisher": float(np.max(fisher)),
        "median_fisher": float(median_f),
        "participation_ratio": float(pr),
        "fisher_top5": sorted(fisher, reverse=True)[:5],
    }


def main():
    print("=" * 60)
    print("E13: alpha-dim(image(G)) monotonicity test")
    print("=" * 60)

    with open(POC_DIR / "embedding_cache_100.pkl", "rb") as f:
        cache = pickle.load(f)
    print(f"Sessions: {len(cache)}")

    taus = np.arange(0.50, 0.96, 0.01)
    results = []

    for tau in taus:
        all_chunks = {}
        total_chunks = 0
        for sid, data in cache.items():
            embs = data.get("embeddings", [])
            if len(embs) < 2:
                continue
            chunks = pairwise_chunk(np.array(embs), tau)
            all_chunks[sid] = chunks
            total_chunks += len(chunks)

        if total_chunks < 10:
            print(f"  tau={tau:.2f}: too few chunks ({total_chunks})")
            continue

        metrics = fisher_analysis(cache, all_chunks)
        if metrics is None:
            print(f"  tau={tau:.2f}: Fisher analysis failed")
            continue

        entry = {"tau": float(f"{tau:.2f}"), **metrics}
        results.append(entry)
        print(f"  tau={tau:.2f}: chunks={metrics['n_chunks']:4d}, "
              f"k_image={metrics['k_image']:2d}, k_ker={metrics['k_ker']:2d}, "
              f"PR={metrics['participation_ratio']:.1f}, "
              f"max_F={metrics['max_fisher']:.3f}")

    # Analysis: monotonicity
    print("\n" + "=" * 60)
    print("MONOTONICITY ANALYSIS")
    print("=" * 60)

    taus_arr = np.array([r["tau"] for r in results])
    k_img_arr = np.array([r["k_image"] for r in results])
    pr_arr = np.array([r["participation_ratio"] for r in results])
    max_f_arr = np.array([r["max_fisher"] for r in results])

    from scipy.stats import spearmanr

    # tau vs k_image: expect negative (tau UP => k_image DOWN)
    rho_ki, p_ki = spearmanr(taus_arr, k_img_arr)
    print(f"\n  tau vs k_image (image(G) dim):")
    print(f"    Spearman rho = {rho_ki:.4f}, p = {p_ki:.2e}")
    print(f"    Prediction: rho < 0 (monotonic decrease)")
    print(f"    Result: {'CONFIRMED' if rho_ki < 0 and p_ki < 0.05 else 'NOT CONFIRMED'}")

    # tau vs participation_ratio: expect positive (tau UP => more isotropic ker)
    rho_pr, p_pr = spearmanr(taus_arr, pr_arr)
    print(f"\n  tau vs participation_ratio (ker(G) isotropy):")
    print(f"    Spearman rho = {rho_pr:.4f}, p = {p_pr:.2e}")
    print(f"    Prediction: rho > 0 (more isotropic)")
    print(f"    Result: {'CONFIRMED' if rho_pr > 0 and p_pr < 0.05 else 'NOT CONFIRMED'}")

    # tau vs max_fisher: expect positive (tau UP => stronger preservation)
    rho_mf, p_mf = spearmanr(taus_arr, max_f_arr)
    print(f"\n  tau vs max_fisher (preservation strength):")
    print(f"    Spearman rho = {rho_mf:.4f}, p = {p_mf:.2e}")
    print(f"    Prediction: rho > 0 (stronger selective preservation)")
    print(f"    Result: {'CONFIRMED' if rho_mf > 0 and p_mf < 0.05 else 'NOT CONFIRMED'}")

    # Overall verdict
    print(f"\n  VERDICT:")
    n_confirmed = sum([
        rho_ki < 0 and p_ki < 0.05,
        rho_pr > 0 and p_pr < 0.05,
        rho_mf > 0 and p_mf < 0.05,
    ])
    if n_confirmed == 3:
        print("    STRONG: All 3 predictions confirmed. Conjecture 5.9.2 supported.")
    elif n_confirmed >= 2:
        print("    MODERATE: 2/3 predictions confirmed.")
    else:
        print("    WEAK: Fewer than 2/3 predictions confirmed.")

    # Save
    output = {
        "experiment": "e13_alpha_dim_monotonicity",
        "n_sessions": len(cache),
        "tau_range": [float(taus[0]), float(taus[-1])],
        "tau_step": 0.01,
        "results": results,
        "monotonicity": {
            "tau_vs_k_image": {"rho": float(rho_ki), "p": float(p_ki)},
            "tau_vs_participation_ratio": {"rho": float(rho_pr), "p": float(p_pr)},
            "tau_vs_max_fisher": {"rho": float(rho_mf), "p": float(p_mf)},
            "n_confirmed": n_confirmed,
        },
    }
    out_path = POC_DIR / "e13_alpha_dim_monotonicity.json"

    def convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Not serializable: {type(obj)}")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=convert)
    print(f"\n  Saved: {out_path}")


if __name__ == "__main__":
    main()
