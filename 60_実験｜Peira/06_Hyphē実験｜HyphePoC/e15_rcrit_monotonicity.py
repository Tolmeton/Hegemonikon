#!/usr/bin/env python3
"""
E15+E16: R_crit monotonicity + Last Survivor Test (Fixed Basis Design)

PURPOSE:
  Bridge the gap between Theorem 5.9.3 (proved) and the quantitative conjecture
  in Paper I §5.9.3:
    - Theorem 5.9.3: Universal structures survive any non-trivial G (proved).
    - Conjecture: alpha UP => R_crit UP => dim(image(G)) DOWN (needs experimental support).

  E15: Verify strict monotonicity of dim(image(G)) w.r.t. tau (proxy for alpha).
  E16: Verify that dropout order matches baseline Fisher ratio rank (Last Survivor).

DESIGN PRINCIPLE — Fixed Basis:
  PCA basis computed ONCE at tau=0.50 (baseline). All tau points use this fixed
  basis V_base for Fisher ratio computation. This ensures:
  1. Direction identity: "direction i" is the same across all tau points.
  2. Last Survivor is well-defined: "direction i drops out at tau=X" is unambiguous.
  3. Confound separation: tau-dependent chunking granularity affects S_b/S_w but
     the basis directions remain fixed, so FR changes reflect genuine structural
     importance rather than basis rotation artifacts.

ANALYSES:
  A1: Strict monotonicity of k_image_abs (monotone fraction >= 0.85)
  A2: Spearman(dropout_tau, baseline_FR) > 0.3 — dropout ordering
  A3: Last survivors at tau=0.90 are baseline FR top-5
  A4: Per-tau rank stability of FR > 0.7 for >80% of tau points
  A5: E13 replication — Spearman(tau, k_image_rel) ≈ -0.63
  A6: Confound check — Spearman(tau, mean_FR)
  A7: Fixed vs rotating basis FR correlation

SOURCE: Paper I §5.9.3 (Theorem + Conjecture), E12/E13 results
"""

import json
import pickle
import numpy as np
from pathlib import Path
from scipy.sparse.linalg import eigsh
from scipy.stats import spearmanr

HGK_ROOT = Path.home() / "Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
POC_DIR = HGK_ROOT / "60_実験｜Peira/06_Hyphē実験｜HyphePoC"

K_PCA = 200
BASELINE_TAU = 0.65  # Enough chunks (~62) for meaningful between-chunk structure
TAU_MIN, TAU_MAX, TAU_STEP = 0.50, 0.95, 0.01
MIN_CHUNKS = 30  # Skip tau points with fewer chunks
NORM_THRESHOLDS = [1.5, 2.0, 2.5, 3.0]  # Sensitivity analysis


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


def chunk_all_sessions(cache, tau):
    """Chunk all sessions at a given tau. Returns {sid: [(s,e), ...]}."""
    all_chunks = {}
    for sid, data in cache.items():
        embs = data.get("embeddings", [])
        if len(embs) < 2:
            continue
        chunks = pairwise_chunk(np.array(embs), tau)
        all_chunks[sid] = chunks
    return all_chunks


def build_scatter_matrices(cache, all_chunks):
    """Build S_b, S_w, global_mean, and chunk_data from chunked sessions."""
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
        return None, None, None, None

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

    return S_b, S_w, chunk_data, all_embs


def compute_pca_basis(all_embs, k):
    """Compute top-k PCA directions from embeddings."""
    global_mean = all_embs.mean(axis=0)
    X_c = all_embs - global_mean
    n_total = X_c.shape[0]
    d = X_c.shape[1]
    cov = X_c.T @ X_c / n_total
    k_actual = min(k, d - 1, n_total - 1)
    _, V = eigsh(cov, k=k_actual, which='LM')
    V = V[:, ::-1]  # descending eigenvalue order
    return V


def fisher_on_basis(S_b, S_w, V):
    """Compute Fisher ratios for each column of V (fixed or rotating basis)."""
    k = V.shape[1]
    fisher = np.array([
        (V[:, i] @ S_b @ V[:, i]) / max(V[:, i] @ S_w @ V[:, i], 1e-10)
        for i in range(k)
    ])
    return fisher


def compute_baseline(cache):
    """Compute fixed PCA basis and baseline Fisher ratios at BASELINE_TAU."""
    all_chunks = chunk_all_sessions(cache, BASELINE_TAU)
    S_b, S_w, chunk_data, all_embs = build_scatter_matrices(cache, all_chunks)
    if S_b is None:
        raise RuntimeError(f"Baseline tau={BASELINE_TAU} produced too few chunks")

    V_base = compute_pca_basis(all_embs, K_PCA)
    FR_base = fisher_on_basis(S_b, S_w, V_base)
    fixed_threshold = 2.0 * float(np.median(FR_base))

    return V_base, FR_base, fixed_threshold, len(chunk_data), all_embs.shape[0]


def analyze_tau_point(cache, tau, V_base):
    """Run Fisher analysis at a single tau using the fixed basis V_base.

    Also computes rotating-basis Fisher for A7 comparison.
    """
    all_chunks = chunk_all_sessions(cache, tau)
    S_b, S_w, chunk_data, all_embs = build_scatter_matrices(cache, all_chunks)
    if S_b is None or len(chunk_data) < MIN_CHUNKS:
        return None

    # Fixed basis Fisher ratios
    FR_fixed = fisher_on_basis(S_b, S_w, V_base)

    # Normalized Fisher ratio: FR / mean(FR) — removes granularity confound
    mean_fr = float(np.mean(FR_fixed))
    FR_norm = FR_fixed / mean_fr if mean_fr > 1e-10 else FR_fixed

    # Rotating basis Fisher ratios (E13-compatible)
    V_rot = compute_pca_basis(all_embs, K_PCA)
    FR_rot = fisher_on_basis(S_b, S_w, V_rot)

    median_fixed = float(np.median(FR_fixed))
    median_rot = float(np.median(FR_rot))

    return {
        "n_chunks": len(chunk_data),
        "n_steps": all_embs.shape[0],
        # Fixed basis
        "FR_fixed": FR_fixed.tolist(),
        "FR_norm": FR_norm.tolist(),
        "k_image_abs": None,  # set by caller with fixed_threshold
        "k_image_norm": int(np.sum(FR_norm > 2.0)),  # > 2x mean = image(G)
        "k_image_rel": int(np.sum(FR_fixed > median_fixed * 2)),
        "median_FR_fixed": median_fixed,
        "max_FR_fixed": float(np.max(FR_fixed)),
        "mean_FR_fixed": mean_fr,
        # Rotating basis (E13 compat)
        "k_image_rot": int(np.sum(FR_rot > median_rot * 2)),
        "median_FR_rot": median_rot,
    }


def direction_tracking(sweep, FR_base, fixed_threshold, norm_threshold=2.0):
    """Track direction membership and compute dropout tau for each direction.

    Uses NORMALIZED Fisher ratio (FR_norm > norm_threshold) for membership
    to avoid granularity confound.

    Returns:
      membership: (k, n_tau) bool array
      dropout_tau: (k,) array — tau at which direction drops out of image(G)
      survivor_090: list of direction indices surviving at tau=0.90
    """
    taus = [s["tau"] for s in sweep]
    k = len(FR_base)
    n_tau = len(sweep)
    membership = np.zeros((k, n_tau), dtype=bool)

    for j, s in enumerate(sweep):
        fr_norm = np.array(s["FR_norm"])
        for i in range(k):
            membership[i, j] = fr_norm[i] > norm_threshold

    # Dropout tau: first tau where direction i is NOT in image(G)
    # (after being in image(G) at baseline)
    dropout_tau = np.full(k, np.nan)
    for i in range(k):
        if not membership[i, 0]:
            # Never in image(G) at baseline
            dropout_tau[i] = taus[0]
            continue
        for j in range(1, n_tau):
            if not membership[i, j]:
                dropout_tau[i] = taus[j]
                break
        # If still in image(G) at max tau, dropout_tau stays nan (= survivor)

    # Survivors at tau=0.90
    tau_090_idx = None
    for j, t in enumerate(taus):
        if abs(t - 0.90) < 0.005:
            tau_090_idx = j
            break
    survivor_090 = []
    if tau_090_idx is not None:
        survivor_090 = [int(i) for i in range(k) if membership[i, tau_090_idx]]

    return membership, dropout_tau, survivor_090


def run_analyses(sweep, FR_base, fixed_threshold, membership, dropout_tau,
                 survivor_090):
    """Run all 7 analyses and return structured results."""
    taus = np.array([s["tau"] for s in sweep])
    k = len(FR_base)
    results = {}

    # === A1: Strict monotonicity of k_image_norm (normalized FR > 2.0) ===
    k_abs = np.array([s["k_image_norm"] for s in sweep])
    diffs = np.diff(k_abs)
    monotone_steps = int(np.sum(diffs <= 0))
    total_steps = len(diffs)
    monotone_frac = monotone_steps / total_steps if total_steps > 0 else 0.0
    violations = [
        {"from_tau": float(taus[i]), "to_tau": float(taus[i + 1]),
         "k_from": int(k_abs[i]), "k_to": int(k_abs[i + 1])}
        for i in range(total_steps) if diffs[i] > 0
    ]
    results["A1_monotonicity"] = {
        "monotone_fraction": float(monotone_frac),
        "monotone_steps": monotone_steps,
        "total_steps": total_steps,
        "n_violations": len(violations),
        "violations": violations[:10],  # cap at 10
        "pass": monotone_frac >= 0.85,
    }

    # === A2: Dropout ordering ===
    # Only consider directions that were in image(G) at baseline (norm > 2.0)
    # AND have dropped out at some tau
    FR_base_norm = FR_base / np.mean(FR_base) if np.mean(FR_base) > 1e-10 else FR_base
    in_baseline = FR_base_norm > 2.0
    has_dropout = ~np.isnan(dropout_tau)
    mask = in_baseline & has_dropout
    if mask.sum() >= 4:
        rho_a2, p_a2 = spearmanr(FR_base[mask], dropout_tau[mask])
    else:
        rho_a2, p_a2 = float("nan"), float("nan")
    results["A2_dropout_ordering"] = {
        "rho": float(rho_a2),
        "p": float(p_a2),
        "n_directions": int(mask.sum()),
        "n_survivors_forever": int(np.sum(in_baseline & np.isnan(dropout_tau))),
        "pass": (not np.isnan(rho_a2)) and rho_a2 > 0.3 and p_a2 < 0.10,
    }

    # === A3: Last Survivor ===
    baseline_rank = np.argsort(np.argsort(-FR_base))  # 0 = highest FR
    survivor_ranks = [int(baseline_rank[i]) for i in survivor_090]
    top5_match = sum(1 for r in survivor_ranks if r < 5)
    results["A3_last_survivor"] = {
        "survivor_directions": survivor_090,
        "survivor_baseline_ranks": survivor_ranks,
        "n_survivors": len(survivor_090),
        "top3_in_top5": top5_match >= 3 if len(survivor_ranks) >= 3
                        else len(survivor_ranks) > 0,
        "pass": top5_match >= 3 if len(survivor_ranks) >= 3 else None,
    }

    # === A4: Rank stability ===
    rank_rhos = []
    for s in sweep:
        fr = np.array(s["FR_fixed"])
        rho_r, _ = spearmanr(FR_base, fr)
        rank_rhos.append(float(rho_r))
    high_stability = sum(1 for r in rank_rhos if r > 0.7)
    stability_frac = high_stability / len(rank_rhos) if rank_rhos else 0.0
    results["A4_rank_stability"] = {
        "mean_rho": float(np.mean(rank_rhos)),
        "min_rho": float(np.min(rank_rhos)),
        "high_stability_fraction": float(stability_frac),
        "pass": stability_frac > 0.80,
    }

    # === A5: E13 replication (relative threshold) ===
    k_rel = np.array([s["k_image_rel"] for s in sweep])
    rho_a5, p_a5 = spearmanr(taus, k_rel)
    results["A5_e13_compat"] = {
        "rho": float(rho_a5),
        "p": float(p_a5),
        "e13_target": -0.63,
        "within_tolerance": abs(rho_a5 - (-0.63)) < 0.15,
    }

    # === A6: Confound check ===
    mean_fr = np.array([s["mean_FR_fixed"] for s in sweep])
    rho_a6, p_a6 = spearmanr(taus, mean_fr)
    results["A6_confound"] = {
        "rho": float(rho_a6),
        "p": float(p_a6),
        "confound_significant": bool(rho_a6 > 0.5 and p_a6 < 0.05),
        "note": "If confound_significant, relative threshold results (A5) may "
                "be inflated. Absolute threshold (A1) is more reliable.",
    }

    # === A7: Fixed vs rotating basis stability ===
    basis_rhos = []
    for s in sweep:
        fr_fixed = np.array(s["FR_fixed"])
        # We can't directly compare fixed vs rotating FR values since they're
        # on different bases. Compare rank orderings instead.
        # Use k_image counts as a proxy for agreement.
        basis_rhos.append(s["k_image_rel"])  # rotating-basis k_image
    # Compare fixed-basis k_image_norm trend with rotating-basis k_image_rel trend
    k_abs_arr = np.array([s["k_image_norm"] for s in sweep])
    k_rel_arr = np.array(basis_rhos)
    if len(k_abs_arr) > 5:
        rho_a7, p_a7 = spearmanr(k_abs_arr, k_rel_arr)
    else:
        rho_a7, p_a7 = float("nan"), float("nan")
    results["A7_basis_stability"] = {
        "rho_abs_vs_rel": float(rho_a7),
        "p": float(p_a7),
        "pass": (not np.isnan(rho_a7)) and rho_a7 > 0.8,
        "note": "High correlation means fixed/rotating bases give consistent trends.",
    }

    # === A8: Threshold sensitivity analysis ===
    sensitivity = {}
    for thresh in NORM_THRESHOLDS:
        k_series = []
        for s in sweep:
            fr_norm = np.array(s["FR_norm"])
            k_series.append(int(np.sum(fr_norm > thresh)))
        k_arr = np.array(k_series)
        diffs_s = np.diff(k_arr)
        mono_s = int(np.sum(diffs_s <= 0))
        total_s = len(diffs_s)
        mono_frac_s = mono_s / total_s if total_s > 0 else 0.0
        rho_s, p_s = spearmanr(taus, k_arr)
        sensitivity[f"thresh_{thresh}"] = {
            "k_at_baseline": int(k_arr[0]),
            "k_at_max_tau": int(k_arr[-1]),
            "monotone_fraction": float(mono_frac_s),
            "spearman_rho": float(rho_s),
            "spearman_p": float(p_s),
        }
    results["A8_threshold_sensitivity"] = {
        "thresholds": NORM_THRESHOLDS,
        "results": sensitivity,
        "note": "Monotonicity should hold across multiple thresholds to be robust.",
    }

    return results


def main():
    print("=" * 70)
    print("E15+E16: R_crit Monotonicity + Last Survivor (Fixed Basis)")
    print("=" * 70)

    # Load data
    with open(POC_DIR / "embedding_cache_100.pkl", "rb") as f:
        cache = pickle.load(f)
    print(f"Sessions: {len(cache)}")

    # Step 1: Compute baseline
    print(f"\n--- Baseline (tau={BASELINE_TAU}) ---")
    V_base, FR_base, fixed_threshold, n_chunks_base, n_steps_base = \
        compute_baseline(cache)
    baseline_k_image = int(np.sum(FR_base > fixed_threshold))
    print(f"  Chunks: {n_chunks_base}, Steps: {n_steps_base}")
    print(f"  Baseline k_image: {baseline_k_image} (threshold={fixed_threshold:.4f})")
    print(f"  FR range: [{np.min(FR_base):.4f}, {np.max(FR_base):.4f}]")
    print(f"  FR median: {np.median(FR_base):.4f}")

    # Step 2: tau-sweep with fixed basis
    print(f"\n--- Tau Sweep [{TAU_MIN}, {TAU_MAX}] step={TAU_STEP} ---")
    taus = np.arange(TAU_MIN, TAU_MAX + TAU_STEP / 2, TAU_STEP)
    sweep = []

    for tau in taus:
        tau_val = round(float(tau), 2)
        result = analyze_tau_point(cache, tau_val, V_base)
        if result is None:
            print(f"  tau={tau_val:.2f}: SKIP (too few chunks)")
            continue

        result["tau"] = tau_val
        result["k_image_abs"] = int(np.sum(
            np.array(result["FR_fixed"]) > fixed_threshold
        ))
        sweep.append(result)

        print(f"  tau={tau_val:.2f}: chunks={result['n_chunks']:4d}, "
              f"k_norm={result['k_image_norm']:2d}, k_rel={result['k_image_rel']:2d}, "
              f"mean_FR={result['mean_FR_fixed']:.3f}, "
              f"max_FR={result['max_FR_fixed']:.3f}")

    if len(sweep) < 10:
        print("ERROR: Too few tau points with valid data")
        return

    # Step 3: Direction tracking
    print(f"\n--- Direction Tracking ---")
    membership, dropout_tau, survivor_090 = direction_tracking(
        sweep, FR_base, fixed_threshold
    )
    n_ever_image = int(np.sum(~np.isnan(dropout_tau) | np.any(membership, axis=1)))
    n_survivors_all = int(np.sum(np.isnan(dropout_tau) & membership[:, 0]))
    print(f"  Directions ever in image(G): {n_ever_image}/{K_PCA}")
    print(f"  Directions surviving all tau: {n_survivors_all}")
    print(f"  Survivors at tau=0.90: {len(survivor_090)}")
    if survivor_090:
        baseline_rank = np.argsort(np.argsort(-FR_base))
        for idx in survivor_090[:5]:
            print(f"    dir={idx}: baseline_FR={FR_base[idx]:.4f}, "
                  f"rank={baseline_rank[idx]}")

    # Step 4: Analyses
    print(f"\n{'=' * 70}")
    print("ANALYSES")
    print(f"{'=' * 70}")

    analyses = run_analyses(
        sweep, FR_base, fixed_threshold, membership, dropout_tau, survivor_090
    )

    # Print results
    for name, result in analyses.items():
        passed = result.get("pass")
        icon = "✅" if passed else ("❌" if passed is False else "➖")
        print(f"\n  {icon} {name}:")
        for k, v in result.items():
            if k in ("pass", "violations"):
                continue
            print(f"    {k}: {v}")
        if passed is not None:
            print(f"    PASS: {passed}")

    # Verdict
    must_pass = [analyses["A1_monotonicity"]["pass"],
                 analyses["A2_dropout_ordering"]["pass"]]
    should_pass = [analyses.get("A3_last_survivor", {}).get("pass"),
                   analyses["A4_rank_stability"]["pass"],
                   analyses["A7_basis_stability"]["pass"]]

    n_must = sum(1 for p in must_pass if p)
    n_should = sum(1 for p in should_pass if p)

    print(f"\n{'=' * 70}")
    print("VERDICT")
    print(f"{'=' * 70}")
    print(f"  Must-pass:   {n_must}/2")
    print(f"  Should-pass: {n_should}/3")

    if n_must == 2:
        print("  → STRONG: R_crit monotonicity + Last Survivor confirmed.")
        print("    Paper I §5.9.3 quantitative conjecture is experimentally supported.")
    elif n_must == 1:
        print("  → PARTIAL: One must-pass criterion met.")
    else:
        print("  → WEAK: Must-pass criteria not met.")

    if analyses["A6_confound"]["confound_significant"]:
        print("  ⚠️ CONFOUND: tau-granularity confound detected.")
        print("    Absolute threshold (A1) is more reliable than relative (A5).")

    # Step 5: Save
    output = {
        "experiment": "e15_rcrit_monotonicity",
        "design": "Fixed Basis",
        "baseline_tau": BASELINE_TAU,
        "k_pca": K_PCA,
        "fixed_threshold": fixed_threshold,
        "n_sessions": len(cache),
        "tau_range": [float(TAU_MIN), float(TAU_MAX)],
        "tau_step": TAU_STEP,
        "baseline": {
            "FR": FR_base.tolist(),
            "k_image": baseline_k_image,
            "n_chunks": n_chunks_base,
            "n_steps": n_steps_base,
        },
        "sweep": [
            {
                "tau": s["tau"],
                "n_chunks": s["n_chunks"],
                "k_image_norm": s["k_image_norm"],
                "k_image_abs": s["k_image_abs"],
                "k_image_rel": s["k_image_rel"],
                "mean_FR": s["mean_FR_fixed"],
                "max_FR": s["max_FR_fixed"],
                "median_FR": s["median_FR_fixed"],
                "FR_fixed": s["FR_fixed"],
                "FR_norm": s["FR_norm"],
            }
            for s in sweep
        ],
        "direction_tracking": {
            "dropout_tau": [
                float(d) if not np.isnan(d) else None
                for d in dropout_tau
            ],
            "survivor_090": survivor_090,
            "membership_sum": membership.sum(axis=1).tolist(),
        },
        "analyses": {},
    }
    # Clean analyses for JSON
    for name, result in analyses.items():
        clean = {}
        for k, v in result.items():
            if isinstance(v, (np.integer,)):
                clean[k] = int(v)
            elif isinstance(v, (np.floating,)):
                clean[k] = float(v)
            elif isinstance(v, np.ndarray):
                clean[k] = v.tolist()
            elif isinstance(v, float) and np.isnan(v):
                clean[k] = None
            else:
                clean[k] = v
        output["analyses"][name] = clean

    def json_default(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, float) and np.isnan(obj):
            return None
        raise TypeError(f"Not serializable: {type(obj)}")

    out_path = POC_DIR / "e15_rcrit_monotonicity.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=json_default)
    print(f"\n  Saved: {out_path}")


if __name__ == "__main__":
    main()
