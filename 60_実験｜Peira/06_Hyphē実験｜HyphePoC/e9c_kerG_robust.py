#!/usr/bin/env python3
"""
E9c: ker(G) 方向の頑健な同定 — E9b の脆弱性修正版

修正:
  1. chunk_id をセッション横断で一意化 (E9b バグ修正)
  2. 複数 τ (0.70, 0.75, 0.80) で再現性確認
  3. proxy 改善: Function proxy 修正, Scale proxy 改善
  4. Bonferroni 補正付き多重比較
  5. chunk 数の報告とランク制約の明示

SOURCE: PINAKAS_TASK T-002
"""

import json
import pickle
import numpy as np
from pathlib import Path
from scipy import stats

HGK_ROOT = Path.home() / "Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
POC_DIR = HGK_ROOT / "60_実験｜Peira/06_Hyphē実験｜HyphePoC"

# Multiple tau results
TAU_FILES = {
    0.70: "results.json",
    0.75: "results_tau_0.75.json",
    0.80: "results_tau_0.80.json",
}


def load_cache():
    with open(POC_DIR / "embedding_cache.pkl", "rb") as f:
        return pickle.load(f)


def load_results(filename):
    path = POC_DIR / filename
    if not path.exists():
        return None
    return json.load(open(path, encoding="utf-8"))


def parse_step_range(sr):
    parts = sr.split("-")
    return int(parts[0]), int(parts[1])


def classify_valence_text(text):
    positive = ["success", "done", "pass", "resolved", "improved", "achieved",
                "complete", "good", "great", "fixed", "solved", "OK", "PASS",
                "Done", "Fixed", "kalon", "Kalon",
                "成功", "完了", "解消", "改善", "達成", "収束"]
    negative = ["fail", "error", "bug", "issue", "problem", "broken",
                "FAIL", "ERROR", "BUG", "violation", "drift",
                "失敗", "エラー", "問題", "違反", "障害", "未解決", "発散"]
    pos = sum(1 for m in positive if m in text)
    neg = sum(1 for m in negative if m in text)
    return pos - neg


def build_data(cache, results, tau_label):
    """Build per-step data with globally unique chunk IDs."""
    all_embs = []
    all_meta = []
    all_chunk_ids = []
    global_chunk_id = 0

    session_files = {}
    for r in results:
        sid = r["session_id"]
        if sid in cache:
            session_files[sid] = cache[sid].get("file", sid)

    session_order = {r["session_id"]: i for i, r in enumerate(results)}

    for r in results:
        sid = r["session_id"]
        if sid not in cache:
            continue
        sess = cache[sid]
        embs = np.array(sess["embeddings"])
        n_steps = embs.shape[0]
        source_file = sess.get("file", sid)

        # Build chunk map with GLOBAL chunk IDs
        chunk_map = {}
        chunk_sizes = {}
        for ci, chunk in enumerate(r["chunks"]):
            start, end = parse_step_range(chunk["step_range"])
            gid = global_chunk_id + ci
            chunk_size = min(end + 1, n_steps) - start
            chunk_sizes[gid] = chunk_size
            for s in range(start, min(end + 1, n_steps)):
                chunk_map[s] = gid
        global_chunk_id += len(r["chunks"])

        for step_idx in range(n_steps):
            step_obj = sess["steps"][step_idx] if step_idx < len(sess["steps"]) else None
            step_text = ""
            if step_obj is not None:
                if hasattr(step_obj, "text"):
                    step_text = step_obj.text
                elif hasattr(step_obj, "content"):
                    step_text = step_obj.content
                elif isinstance(step_obj, str):
                    step_text = step_obj

            gid = chunk_map.get(step_idx, -1)

            meta = {
                "session_id": sid,
                "session_order": session_order.get(sid, 0),
                "step_idx": step_idx,
                "total_steps": n_steps,
                # Scale proxy: position within chunk (0=start, 1=end)
                "relative_position": step_idx / max(n_steps - 1, 1),
                # Improved Scale proxy: chunk size (larger = coarser grain)
                "chunk_size": chunk_sizes.get(gid, 0),
                # Source info
                "source_file": source_file,
                "source_type": ("handoff" if "handoff" in source_file.lower()
                                else "rom" if "rom" in source_file.lower()
                                else "session"),
                # Valence
                "valence_score": classify_valence_text(step_text),
                "text_length": len(step_text),
                "chunk_id": gid,
            }
            all_embs.append(embs[step_idx])
            all_meta.append(meta)
            all_chunk_ids.append(gid)

    return np.array(all_embs), all_meta, np.array(all_chunk_ids)


def fisher_analysis(X, chunk_labels, n_pca=50):
    """Fisher discriminant with rank constraint check."""
    valid = chunk_labels >= 0
    X_v = X[valid]
    labels_v = chunk_labels[valid]
    unique_chunks = np.unique(labels_v)
    n_chunks = len(unique_chunks)
    n, d = X_v.shape

    max_between_rank = n_chunks - 1

    global_mean = X_v.mean(axis=0)

    # Between-chunk scatter
    S_b = np.zeros((d, d))
    for c in unique_chunks:
        mask = labels_v == c
        n_k = mask.sum()
        if n_k < 2:
            continue
        centroid = X_v[mask].mean(axis=0)
        diff = (centroid - global_mean).reshape(-1, 1)
        S_b += n_k * (diff @ diff.T)
    S_b /= n

    # Within-chunk scatter
    S_w = np.zeros((d, d))
    for c in unique_chunks:
        mask = labels_v == c
        if mask.sum() < 2:
            continue
        centroid = X_v[mask].mean(axis=0)
        residuals = X_v[mask] - centroid
        S_w += residuals.T @ residuals
    S_w /= n

    # PCA basis
    X_c = X_v - global_mean
    cov = X_c.T @ X_c / n
    from scipy.sparse.linalg import eigsh
    k = min(n_pca, d - 1, n - 1)
    eigenvalues, V = eigsh(cov, k=k, which='LM')
    idx = eigenvalues.argsort()[::-1]
    V = V[:, idx]

    # Fisher ratio per PCA direction
    fisher_ratios = []
    for i in range(k):
        v = V[:, i]
        var_b = v @ S_b @ v
        var_w = v @ S_w @ v
        fisher_ratios.append(var_b / max(var_w, 1e-10))

    return (np.array(fisher_ratios), V, n_chunks, max_between_rank,
            X_v, labels_v)


def correlate_and_report(X, meta, V, fisher_ratios, n_chunks, max_rank, tau):
    """Correlate top/bottom Fisher directions with proxies. Bonferroni corrected."""
    n = X.shape[0]
    sorted_idx = np.argsort(fisher_ratios)[::-1]

    # Proxies
    proxies = {
        "Scale(pos)": np.array([m["relative_position"] for m in meta]),
        "Scale(csz)": np.array([m["chunk_size"] for m in meta]),
        "Temporal": np.array([m["session_order"] for m in meta]),
        "Valence": np.array([m["valence_score"] for m in meta]),
        "TxtLen": np.array([m["text_length"] for m in meta]),
        "StepIdx": np.array([m["step_idx"] for m in meta]),
    }

    # Filter constant proxies
    proxies = {k: v for k, v in proxies.items() if np.std(v) > 1e-10}

    n_tests = 5 * len(proxies)  # 5 directions × proxies
    bonf_threshold = 0.05 / n_tests

    results = {"image_G": [], "ker_G": []}

    for direction_type, indices in [("image_G", sorted_idx[:5]), ("ker_G", sorted_idx[-5:][::-1])]:
        print(f"\n  {direction_type} (tau={tau}):")
        header = f"    {'Dir':<6} {'Fisher':>8} |"
        for pname in proxies:
            header += f" {pname:>11}"
        print(header)
        print("    " + "-" * (15 + 12 * len(proxies)))

        for rank, i in enumerate(indices):
            proj = X @ V[:, i]
            row_corrs = {}
            line = f"    PC-{i+1:<3} {fisher_ratios[i]:>8.4f} |"

            for pname, pvals in proxies.items():
                r_val, p_val = stats.spearmanr(proj, pvals)
                sig = "**" if p_val < bonf_threshold else "* " if p_val < 0.05 else "  "
                line += f" {r_val:>+.3f}{sig}"
                row_corrs[pname] = {"r": float(r_val), "p": float(p_val),
                                    "sig_bonf": p_val < bonf_threshold}
            print(line)
            results[direction_type].append({
                "pc": int(i + 1), "fisher": float(fisher_ratios[i]),
                "correlations": row_corrs
            })

    # Best matches (Bonferroni significant only)
    coord_map = {"Scale(pos)": "Scale", "Scale(csz)": "Scale",
                 "Temporal": "Temporality", "Valence": "Valence"}

    print(f"\n  Best matches (Bonferroni p < {bonf_threshold:.5f}):")
    for dt in ["image_G", "ker_G"]:
        print(f"    {dt}:")
        for row in results[dt][:3]:
            best = None
            best_r = 0
            for pname, data in row["correlations"].items():
                if pname not in coord_map:
                    continue
                if data["sig_bonf"] and abs(data["r"]) > best_r:
                    best_r = abs(data["r"])
                    best = coord_map[pname]
            if best:
                print(f"      PC-{row['pc']}: {best} (|r|={best_r:.3f}, Bonferroni sig)")
            else:
                print(f"      PC-{row['pc']}: no Bonferroni-significant match")

    return results


def main():
    print("=" * 70)
    print("E9c: ker(G) robust measurement — multi-tau + bug fixes")
    print("=" * 70)

    cache = load_cache()
    all_results = {}

    for tau, fname in sorted(TAU_FILES.items()):
        results = load_results(fname)
        if results is None:
            print(f"\n  tau={tau}: {fname} not found, skipping")
            continue

        print(f"\n{'='*70}")
        print(f"  tau = {tau}")
        print(f"{'='*70}")

        X, meta, chunk_ids = build_data(cache, results, tau)
        n_valid = np.sum(chunk_ids >= 0)
        n_chunks = len(np.unique(chunk_ids[chunk_ids >= 0]))

        print(f"  Steps: {X.shape[0]}, Valid (in chunk): {n_valid}")
        print(f"  Global unique chunks: {n_chunks}")
        print(f"  Max between-rank: {n_chunks - 1}")

        if n_chunks < 5:
            print(f"  SKIP: too few chunks ({n_chunks})")
            continue

        fisher_ratios, V, nc, max_rank, X_v, labels_v = fisher_analysis(
            X, chunk_ids)
        print(f"  Fisher: {nc} chunks, max_rank={max_rank}")
        print(f"  Top 5 ratios: {[f'{r:.4f}' for r in np.sort(fisher_ratios)[::-1][:5]]}")

        tau_results = correlate_and_report(X_v, [m for m, c in zip(meta, chunk_ids) if c >= 0],
                                           V, fisher_ratios, nc, max_rank, tau)
        tau_results["n_chunks"] = int(nc)
        tau_results["max_rank"] = int(max_rank)
        tau_results["n_steps"] = int(X_v.shape[0])
        all_results[str(tau)] = tau_results

    # Cross-tau stability
    print(f"\n{'='*70}")
    print("CROSS-TAU STABILITY")
    print(f"{'='*70}")

    taus = sorted(all_results.keys())
    if len(taus) >= 2:
        for dt in ["image_G"]:
            print(f"\n  {dt} top-3 matches across tau:")
            for tau_key in taus:
                r = all_results[tau_key]
                nc = r["n_chunks"]
                print(f"    tau={tau_key} ({nc} chunks):", end="")
                for row in r[dt][:3]:
                    best = None
                    best_r = 0
                    for pname, data in row["correlations"].items():
                        if pname in ("TxtLen", "StepIdx"):
                            continue
                        if abs(data["r"]) > best_r:
                            best_r = abs(data["r"])
                            best = pname
                    sig = "**" if row["correlations"].get(best, {}).get("sig_bonf", False) else ""
                    print(f"  {best}({best_r:.2f}{sig})", end="")
                print()
    else:
        print("  Only 1 tau available, cannot assess stability")

    # Save
    out_path = POC_DIR / "e9c_kerG_robust.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved: {out_path}")


if __name__ == "__main__":
    main()
