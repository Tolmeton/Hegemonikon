#!/usr/bin/env python3
"""
E10: Direction-Level Ablation — image(G) 方向の因果的必要性の検証

PURPOSE:
  §5.7 Limitation (i) を解消する。E9 M1 で特定した image(G) の上位 k 方向を
  embedding から射影除去し、chunker を再実行して coherence degradation を測定する。

  image(G) 方向が G∘F の結晶化に因果的に必要なら:
    - image(G) 方向の除去 → coherence 大幅低下
    - ランダム方向の除去 → coherence 微小変化
  この非対称性が因果証拠。

設計:
  1. E9 M1 (boundary drift) の PCA で image(G) 上位 k 方向を特定
  2. 各方向を embedding 空間から射影除去 (project out)
  3. 改変 embedding で chunk_session を再実行
  4. coherence の変化量 ΔC を測定
  5. 対照: 同数のランダム PCA 方向を除去

条件:
  - k ∈ {1, 2, 3, 5, 10} (段階的除去)
  - τ ∈ {0.70, 0.75, 0.80}
  - 対照: ランダム方向除去 (10回平均)

SOURCE: PINAKAS_TASK T-002 (direction-level ablation)
"""

import json
import pickle
import sys
import numpy as np
from pathlib import Path

HGK_ROOT = Path.home() / "Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
POC_DIR = HGK_ROOT / "60_実験｜Peira/06_Hyphē実験｜HyphePoC"

# chunker import
sys.path.insert(0, str(POC_DIR))
sys.path.insert(0, str(HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"))

from hyphe_chunker import chunk_session, Step, parse_session_file


def load_cache():
    with open(POC_DIR / "embedding_cache.pkl", "rb") as f:
        return pickle.load(f)


def load_results(filename="results.json"):
    return json.load(open(POC_DIR / filename, encoding="utf-8"))


def parse_step_range(sr):
    parts = sr.split("-")
    return int(parts[0]), int(parts[1])


def compute_boundary_drift_pca(cache, results):
    """E9 M1: boundary drift の PCA で image(G) 方向を抽出。"""
    all_deltas = []

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

            for boundary_idx in [start, end]:
                if boundary_idx < n_steps:
                    delta = centroid - embs[boundary_idx]
                    all_deltas.append(delta)

    X = np.array(all_deltas)
    X_c = X - X.mean(axis=0)
    n, d = X_c.shape

    # Gram trick (n < d)
    gram = X_c @ X_c.T / n
    eigenvalues, eigvecs_gram = np.linalg.eigh(gram)
    idx = eigenvalues.argsort()[::-1]
    eigenvalues = eigenvalues[idx]
    eigvecs_gram = eigvecs_gram[:, idx]

    # Recover eigenvectors in original 768d space
    V = X_c.T @ eigvecs_gram
    norms = np.linalg.norm(V, axis=0, keepdims=True)
    V = V / np.maximum(norms, 1e-10)

    # Also compute global mean for centering
    global_mean = X.mean(axis=0)

    return V, eigenvalues, global_mean


def project_out(embeddings, directions, k):
    """embedding から上位 k 方向の成分を射影除去する。

    P_out = I - Σ_{i=1}^{k} v_i v_i^T
    embeddings_ablated = embeddings @ P_out
    """
    embs = np.array(embeddings)
    for i in range(k):
        v = directions[:, i]
        # 各 embedding から v 方向の射影を引く
        proj = embs @ v  # (n,)
        embs = embs - np.outer(proj, v)
    return embs.tolist()


def run_chunking_with_embeddings(steps, embeddings, tau):
    """chunk_session を呼び出して coherence 等を返す。"""
    result = chunk_session(
        steps, embeddings,
        tau=tau, min_steps=2, max_iterations=10,
        sim_mode="pairwise",
    )
    coherences = [c.coherence for c in result.chunks]
    chunk_sizes = [len(c) for c in result.chunks]
    return {
        "num_chunks": len(result.chunks),
        "mean_coherence": float(np.mean(coherences)) if coherences else 0.0,
        "std_coherence": float(np.std(coherences)) if coherences else 0.0,
        "mean_chunk_size": float(np.mean(chunk_sizes)) if chunk_sizes else 0.0,
        "converged": result.converged,
        "iterations": result.iterations,
    }


def main():
    print("=" * 70)
    print("E10: Direction-Level Ablation — image(G) 方向の因果的必要性")
    print("=" * 70)

    cache = load_cache()
    results = load_results()

    # Step 1: E9 M1 PCA
    print("\n[Phase 1] Computing image(G) directions (E9 M1 boundary drift PCA)...")
    V, eigenvalues, global_mean = compute_boundary_drift_pca(cache, results)
    print(f"  Boundary drift vectors: eigenvalues top-5 = {[f'{v:.6f}' for v in eigenvalues[:5]]}")

    # Step 2: Ablation experiment
    K_VALUES = [1, 2, 3, 5, 10]
    TAU_VALUES = [0.70, 0.75, 0.80]
    N_RANDOM = 10  # ランダム対照の繰り返し数

    all_results = {}

    for tau in TAU_VALUES:
        print(f"\n{'='*70}")
        print(f"  τ = {tau}")
        print(f"{'='*70}")

        tau_results = {"baseline": {}, "ablate_imageG": {}, "ablate_random": {}}

        # Per-session processing
        session_baselines = []
        session_data = []  # (steps, embeddings, sid) for reuse

        for r in results:
            sid = r["session_id"]
            if sid not in cache:
                continue
            sess = cache[sid]
            embs = sess["embeddings"]
            steps_raw = sess.get("steps", [])

            # Reconstruct Step objects
            steps = []
            for i, s in enumerate(steps_raw):
                if isinstance(s, Step):
                    steps.append(s)
                elif isinstance(s, str):
                    steps.append(Step(index=i, text=s))
                elif hasattr(s, "text"):
                    steps.append(Step(index=i, text=s.text))
                else:
                    steps.append(Step(index=i, text=str(s)))

            if len(steps) < 2:
                continue

            session_data.append((steps, embs, sid))

            # Baseline
            try:
                baseline = run_chunking_with_embeddings(steps, embs, tau)
                session_baselines.append(baseline["mean_coherence"])
            except Exception as e:
                print(f"    SKIP {sid}: {e}")
                session_data.pop()
                continue

        baseline_mean = float(np.mean(session_baselines))
        baseline_std = float(np.std(session_baselines))
        tau_results["baseline"] = {
            "mean_coherence": baseline_mean,
            "std_coherence": baseline_std,
            "n_sessions": len(session_baselines),
        }
        print(f"  Baseline: C̄ = {baseline_mean:.4f} ± {baseline_std:.4f} ({len(session_baselines)} sessions)")

        # Ablation: image(G) directions
        for k in K_VALUES:
            coherences = []
            for steps, embs, sid in session_data:
                embs_ablated = project_out(embs, V, k)
                try:
                    result = run_chunking_with_embeddings(steps, embs_ablated, tau)
                    coherences.append(result["mean_coherence"])
                except Exception:
                    continue

            if coherences:
                mean_c = float(np.mean(coherences))
                delta_c = mean_c - baseline_mean
                tau_results["ablate_imageG"][str(k)] = {
                    "mean_coherence": mean_c,
                    "delta_coherence": delta_c,
                    "relative_change": delta_c / max(baseline_mean, 1e-10),
                    "n_sessions": len(coherences),
                }
                print(f"  image(G) k={k}: C̄ = {mean_c:.4f}, ΔC = {delta_c:+.4f} ({delta_c/max(baseline_mean,1e-10):+.1%})")

        # === 3 control groups (fair comparison) ===
        rng = np.random.default_rng(42)
        n_pca = V.shape[1]  # 96 (= n boundary drift vectors)
        d_emb = V.shape[0]  # 768

        control_groups = {
            # Control A: adjacent-rank PCA directions (same variance band)
            "adjacent": lambda k: list(range(k, min(2 * k, n_pca))),
            # Control B: mid-rank PCA directions
            "mid": lambda k: list(range(n_pca // 3, min(n_pca // 3 + k, n_pca))),
        }

        for ctrl_name, idx_fn in control_groups.items():
            tau_results[f"ablate_{ctrl_name}"] = {}
            for k in K_VALUES:
                indices = idx_fn(k)
                if len(indices) < 1:
                    continue
                V_ctrl = V[:, indices]
                ctrl_coherences = []
                for steps, embs, sid in session_data:
                    embs_ablated = project_out(embs, V_ctrl, V_ctrl.shape[1])
                    try:
                        result = run_chunking_with_embeddings(steps, embs_ablated, tau)
                        ctrl_coherences.append(result["mean_coherence"])
                    except Exception:
                        continue

                if ctrl_coherences:
                    mean_c = float(np.mean(ctrl_coherences))
                    delta_c = mean_c - baseline_mean
                    tau_results[f"ablate_{ctrl_name}"][str(k)] = {
                        "mean_coherence": mean_c,
                        "delta_coherence": delta_c,
                        "relative_change": delta_c / max(baseline_mean, 1e-10),
                        "n_sessions": len(ctrl_coherences),
                    }
                    print(f"  {ctrl_name:>10} k={k}: C̄ = {mean_c:.4f}, ΔC = {delta_c:+.4f} ({delta_c/max(baseline_mean,1e-10):+.1%})")

        # Control C: random 768d directions (not constrained to PCA basis)
        tau_results["ablate_random768d"] = {}
        for k in K_VALUES:
            trial_coherences_all = []
            for trial in range(N_RANDOM):
                # Generate k random orthonormal directions in full 768d space
                random_dirs = rng.standard_normal((d_emb, k))
                random_dirs, _ = np.linalg.qr(random_dirs)  # orthonormalize

                trial_coherences = []
                for steps, embs, sid in session_data:
                    embs_ablated = project_out(embs, random_dirs, k)
                    try:
                        result = run_chunking_with_embeddings(steps, embs_ablated, tau)
                        trial_coherences.append(result["mean_coherence"])
                    except Exception:
                        continue

                if trial_coherences:
                    trial_coherences_all.append(float(np.mean(trial_coherences)))

            if trial_coherences_all:
                mean_c = float(np.mean(trial_coherences_all))
                std_c = float(np.std(trial_coherences_all))
                delta_c = mean_c - baseline_mean
                tau_results["ablate_random768d"][str(k)] = {
                    "mean_coherence": mean_c,
                    "std_coherence": std_c,
                    "delta_coherence": delta_c,
                    "relative_change": delta_c / max(baseline_mean, 1e-10),
                    "n_trials": len(trial_coherences_all),
                }
                print(f"  {'rand768d':>10} k={k}: C̄ = {mean_c:.4f} ± {std_c:.4f}, ΔC = {delta_c:+.4f} ({delta_c/max(baseline_mean,1e-10):+.1%})")

        # Effect size: image(G) vs adjacent (fair Cohen's d with session-level pooled SD)
        print(f"\n  --- Effect Size (image(G) vs adjacent, session-level pooled SD) ---")
        for k in K_VALUES:
            ig = tau_results["ablate_imageG"].get(str(k))
            adj = tau_results["ablate_adjacent"].get(str(k))
            if ig and adj:
                # Collect per-session coherences for proper pooled SD
                ig_coherences = []
                adj_coherences = []
                indices_adj = list(range(k, min(2 * k, n_pca)))
                V_adj = V[:, indices_adj]
                for steps, embs, sid in session_data:
                    embs_ig = project_out(embs, V, k)
                    embs_adj = project_out(embs, V_adj, V_adj.shape[1])
                    try:
                        r_ig = run_chunking_with_embeddings(steps, embs_ig, tau)
                        r_adj = run_chunking_with_embeddings(steps, embs_adj, tau)
                        ig_coherences.append(r_ig["mean_coherence"])
                        adj_coherences.append(r_adj["mean_coherence"])
                    except Exception:
                        continue

                if len(ig_coherences) >= 2:
                    ig_arr = np.array(ig_coherences)
                    adj_arr = np.array(adj_coherences)
                    pooled_sd = np.sqrt((np.var(ig_arr, ddof=1) + np.var(adj_arr, ddof=1)) / 2)
                    if pooled_sd > 1e-10:
                        d_val = (np.mean(ig_arr) - np.mean(adj_arr)) / pooled_sd
                        print(f"  k={k}: Cohen's d = {d_val:.2f} (pooled SD = {pooled_sd:.4f}, n={len(ig_coherences)})")
                        tau_results["ablate_imageG"][str(k)]["cohen_d_vs_adjacent"] = float(d_val)
                        tau_results["ablate_imageG"][str(k)]["pooled_sd"] = float(pooled_sd)

        all_results[str(tau)] = tau_results

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY — Direction-Level Ablation")
    print(f"{'='*70}")

    print("\n  Coherence degradation when removing image(G) directions:")
    print(f"  {'k':>4} |", end="")
    for tau in TAU_VALUES:
        print(f"  τ={tau}    ", end="")
    print()
    print("  " + "-" * 50)

    for k in K_VALUES:
        print(f"  {k:>4} |", end="")
        for tau in TAU_VALUES:
            r = all_results.get(str(tau), {}).get("ablate_imageG", {}).get(str(k))
            if r:
                print(f"  {r['relative_change']:+.1%}    ", end="")
            else:
                print(f"  {'N/A':>8}  ", end="")
        print()

    for ctrl_name in ["adjacent", "mid", "random768d"]:
        label = {"adjacent": "adjacent-rank PCA", "mid": "mid-rank PCA", "random768d": "random 768d"}[ctrl_name]
        print(f"\n  Coherence change when removing {label} directions:")
        print(f"  {'k':>4} |", end="")
        for tau in TAU_VALUES:
            print(f"  τ={tau}    ", end="")
        print()
        print("  " + "-" * 50)

        for k in K_VALUES:
            print(f"  {k:>4} |", end="")
            for tau in TAU_VALUES:
                r = all_results.get(str(tau), {}).get(f"ablate_{ctrl_name}", {}).get(str(k))
                if r:
                    print(f"  {r['relative_change']:+.1%}    ", end="")
                else:
                    print(f"  {'N/A':>8}  ", end="")
        print()

    # Save
    out_path = POC_DIR / "e10_direction_ablation.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved: {out_path}")


if __name__ == "__main__":
    main()
