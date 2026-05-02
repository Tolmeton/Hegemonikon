#!/usr/bin/env python3
"""
E9b: ker(G) 方向の同定 — image(G) の 2-3 方向は何を表すか

PURPOSE:
  E9 で発見した image(G) の 2-3 方向が HGK 6座標のどれに対応するかを同定する。

手法:
  1. Fisher ratio 上位方向 (image(G)) への全 step embedding の射影を計算
  2. 射影値と利用可能なメタデータの相関を分析:
     - Scale proxy: chunk_idx / total_chunks (文書内の位置 = 粒度)
     - Temporality proxy: source file の日時順
     - Valence proxy: positive/negative marker の有無
     - Function proxy: source type (handoff vs ROM vs KI)
  3. 各方向がどの座標と最も強く相関するかで同定

SOURCE: PINAKAS_TASK T-002 (continuation of E9)
"""

import json
import pickle
import numpy as np
from pathlib import Path
from collections import defaultdict
from scipy import stats

HGK_ROOT = Path.home() / "Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
POC_DIR = HGK_ROOT / "60_実験｜Peira/06_Hyphē実験｜HyphePoC"


def load_data():
    with open(POC_DIR / "embedding_cache.pkl", "rb") as f:
        cache = pickle.load(f)
    results = json.load(open(POC_DIR / "results.json", encoding="utf-8"))
    return cache, results


def parse_step_range(sr):
    parts = sr.split("-")
    return int(parts[0]), int(parts[1])


def extract_date_from_filename(fname):
    """Extract date-like number from filename for temporal ordering."""
    import re
    # Match patterns like 164ceafc, dates, etc.
    # Use file hash as proxy for temporal order (files are sorted by creation)
    return fname


def classify_valence_text(text):
    """Heuristic valence classification of text."""
    positive = ["success", "done", "pass", "resolved", "improved", "achieved",
                "complete", "good", "great", "fixed", "solved",
                "OK", "PASS", "Done", "Fixed",
                "成功", "完了", "解消", "改善", "達成"]
    negative = ["fail", "error", "bug", "issue", "problem", "broken",
                "FAIL", "ERROR", "BUG",
                "失敗", "エラー", "問題", "違反", "障害", "未解決"]

    pos = sum(1 for m in positive if m in text)
    neg = sum(1 for m in negative if m in text)
    return pos - neg  # continuous valence score


def build_step_metadata(cache, results):
    """Build per-step metadata array aligned with embeddings."""
    all_embeddings = []
    all_meta = []
    all_chunk_labels = []

    session_order = {}
    for i, r in enumerate(results):
        session_order[r["session_id"]] = i

    for r in results:
        sid = r["session_id"]
        if sid not in cache:
            continue
        sess = cache[sid]
        embs = np.array(sess["embeddings"])
        n_steps = embs.shape[0]
        source_file = sess.get("file", sid)

        # Build chunk map: step_idx -> chunk_id
        chunk_map = {}
        for ci, chunk in enumerate(r["chunks"]):
            start, end = parse_step_range(chunk["step_range"])
            for s in range(start, min(end + 1, n_steps)):
                chunk_map[s] = ci

        for step_idx in range(n_steps):
            # Get step text if available
            step_obj = sess["steps"][step_idx] if step_idx < len(sess["steps"]) else None
            step_text = ""
            if step_obj is not None:
                if hasattr(step_obj, "text"):
                    step_text = step_obj.text
                elif hasattr(step_obj, "content"):
                    step_text = step_obj.content
                elif isinstance(step_obj, str):
                    step_text = step_obj

            meta = {
                "session_id": sid,
                "session_order": session_order[sid],
                "step_idx": step_idx,
                "total_steps": n_steps,
                "relative_position": step_idx / max(n_steps - 1, 1),  # 0..1
                "source_file": source_file,
                "is_handoff": "handoff" in source_file.lower(),
                "is_rom": "rom" in source_file.lower(),
                "valence_score": classify_valence_text(step_text),
                "text_length": len(step_text),
                "chunk_id": chunk_map.get(step_idx, -1),
            }
            all_embeddings.append(embs[step_idx])
            all_meta.append(meta)
            all_chunk_labels.append(chunk_map.get(step_idx, -1))

    return np.array(all_embeddings), all_meta, np.array(all_chunk_labels)


def compute_image_G_directions(X, chunk_labels):
    """Compute top image(G) directions via Fisher discriminant analysis."""
    unique_chunks = [c for c in np.unique(chunk_labels) if c >= 0]
    n, d = X.shape

    # Global mean
    global_mean = X.mean(axis=0)

    # Between-chunk scatter
    S_b = np.zeros((d, d))
    for c in unique_chunks:
        mask = chunk_labels == c
        n_k = mask.sum()
        if n_k < 2:
            continue
        centroid = X[mask].mean(axis=0)
        diff = (centroid - global_mean).reshape(-1, 1)
        S_b += n_k * (diff @ diff.T)
    S_b /= n

    # Within-chunk scatter
    S_w = np.zeros((d, d))
    for c in unique_chunks:
        mask = chunk_labels == c
        if mask.sum() < 2:
            continue
        centroid = X[mask].mean(axis=0)
        residuals = X[mask] - centroid
        S_w += residuals.T @ residuals
    S_w /= n

    # Total PCA for basis
    X_c = X - global_mean
    cov = X_c.T @ X_c / n

    from scipy.sparse.linalg import eigsh
    k = min(50, d - 1)
    eigenvalues, V = eigsh(cov, k=k, which='LM')
    idx = eigenvalues.argsort()[::-1]
    eigenvalues = eigenvalues[idx]
    V = V[:, idx]

    # Fisher ratio per PCA direction
    fisher_ratios = []
    for i in range(k):
        v = V[:, i]
        var_b = v @ S_b @ v
        var_w = v @ S_w @ v
        ratio = var_b / max(var_w, 1e-10)
        fisher_ratios.append(ratio)

    fisher_ratios = np.array(fisher_ratios)
    sorted_idx = np.argsort(fisher_ratios)[::-1]

    # Top image(G) directions
    top_directions = V[:, sorted_idx[:10]]  # top 10
    top_ratios = fisher_ratios[sorted_idx[:10]]

    # Also get bottom directions = ker(G)
    bottom_idx = np.argsort(fisher_ratios)[:10]
    bottom_directions = V[:, bottom_idx]
    bottom_ratios = fisher_ratios[bottom_idx]

    return top_directions, top_ratios, bottom_directions, bottom_ratios


def correlate_directions_with_metadata(X, meta, directions, direction_labels, direction_type):
    """Project all embeddings onto directions and correlate with metadata."""
    n = X.shape[0]

    # Extract metadata arrays
    relative_pos = np.array([m["relative_position"] for m in meta])
    session_order = np.array([m["session_order"] for m in meta])
    valence = np.array([m["valence_score"] for m in meta])
    is_handoff = np.array([float(m["is_handoff"]) for m in meta])
    text_length = np.array([m["text_length"] for m in meta])
    step_idx = np.array([m["step_idx"] for m in meta])

    # Proxy names and arrays
    proxies = {
        "Scale (relative_position)": relative_pos,
        "Temporality (session_order)": session_order,
        "Valence (sentiment_score)": valence,
        "Function (is_handoff)": is_handoff,
        "text_length": text_length,
        "step_idx (absolute)": step_idx,
    }

    print(f"\n  {direction_type} Directions vs 6-Coordinate Proxies:")
    print(f"  {'Direction':<12} {'Fisher':>7} | ", end="")
    for pname in proxies:
        short = pname.split("(")[0].strip()[:12]
        print(f"{short:>13}", end="")
    print()
    print("  " + "-" * 100)

    results = []

    for i in range(min(directions.shape[1], 5)):
        proj = X @ directions[:, i]
        label = direction_labels[i] if i < len(direction_labels) else f"D-{i}"

        row = {"direction": label, "fisher_ratio": float(direction_labels[i]) if isinstance(direction_labels[i], (int, float, np.floating)) else 0}
        print(f"  {f'D-{i+1}':<12} {row.get('fisher_ratio', 0):>7.4f} | ", end="")

        correlations = {}
        for pname, pvals in proxies.items():
            # Filter out zero-variance
            if np.std(pvals) < 1e-10 or np.std(proj) < 1e-10:
                r_val, p_val = 0.0, 1.0
            else:
                r_val, p_val = stats.spearmanr(proj, pvals)

            correlations[pname] = {"r": float(r_val), "p": float(p_val)}
            sig = "*" if p_val < 0.01 else " "
            print(f"  {r_val:>+.3f}{sig}", end="")
            short = pname.split("(")[0].strip()[:12]

        print()
        row["correlations"] = correlations
        results.append(row)

    return results


def identify_directions(image_results, ker_results):
    """Identify what each direction represents based on correlation patterns."""
    print("\n" + "=" * 60)
    print("DIRECTION IDENTIFICATION")
    print("=" * 60)

    coord_names = {
        "Scale (relative_position)": "Scale",
        "Temporality (session_order)": "Temporality",
        "Valence (sentiment_score)": "Valence",
        "Function (is_handoff)": "Function",
    }

    print("\n  image(G) directions (G preserves these):")
    for i, row in enumerate(image_results[:3]):
        best_proxy = None
        best_r = 0
        for pname in coord_names:
            r_abs = abs(row["correlations"][pname]["r"])
            p_val = row["correlations"][pname]["p"]
            if r_abs > best_r and p_val < 0.05:
                best_r = r_abs
                best_proxy = coord_names[pname]

        if best_proxy and best_r > 0.1:
            print(f"    D-{i+1}: best match = {best_proxy} (|r| = {best_r:.3f})")
        else:
            print(f"    D-{i+1}: no clear match (max |r| = {best_r:.3f})")

    print("\n  ker(G) directions (G discards these):")
    for i, row in enumerate(ker_results[:3]):
        best_proxy = None
        best_r = 0
        for pname in coord_names:
            r_abs = abs(row["correlations"][pname]["r"])
            p_val = row["correlations"][pname]["p"]
            if r_abs > best_r and p_val < 0.05:
                best_r = r_abs
                best_proxy = coord_names[pname]

        if best_proxy and best_r > 0.1:
            print(f"    D-{i+1}: best match = {best_proxy} (|r| = {best_r:.3f})")
        else:
            print(f"    D-{i+1}: no clear match (max |r| = {best_r:.3f})")


def main():
    print("=" * 60)
    print("E9b: ker(G) direction identification")
    print("=" * 60)

    cache, results = load_data()

    # Build step-level data
    print("\n[Phase 1] Building step metadata...")
    X, meta, chunk_labels = build_step_metadata(cache, results)
    print(f"  Steps: {X.shape[0]}, Dim: {X.shape[1]}")
    print(f"  Chunks: {len(np.unique(chunk_labels[chunk_labels >= 0]))}")

    # Metadata stats
    valences = [m["valence_score"] for m in meta]
    print(f"  Valence scores: mean={np.mean(valences):.2f}, std={np.std(valences):.2f}, "
          f"range=[{min(valences)}, {max(valences)}]")
    n_handoff = sum(1 for m in meta if m["is_handoff"])
    n_rom = sum(1 for m in meta if m["is_rom"])
    print(f"  Sources: handoff={n_handoff}, rom={n_rom}, other={len(meta)-n_handoff-n_rom}")

    # Compute image(G) and ker(G) directions
    print("\n[Phase 2] Computing Fisher discriminant directions...")
    top_dirs, top_ratios, bot_dirs, bot_ratios = compute_image_G_directions(X, chunk_labels)
    print(f"  Top 5 Fisher ratios (image(G)): {[f'{r:.4f}' for r in top_ratios[:5]]}")
    print(f"  Bottom 5 Fisher ratios (ker(G)): {[f'{r:.4f}' for r in bot_ratios[:5]]}")

    # Correlate with metadata
    print("\n[Phase 3] Correlating directions with coordinate proxies...")
    image_results = correlate_directions_with_metadata(
        X, meta, top_dirs, top_ratios, "image(G)")
    ker_results = correlate_directions_with_metadata(
        X, meta, bot_dirs, bot_ratios, "ker(G)")

    # Identify
    identify_directions(image_results, ker_results)

    # Save
    output = {
        "experiment": "e9b_kerG_direction_identification",
        "n_steps": X.shape[0],
        "n_chunks": int(len(np.unique(chunk_labels[chunk_labels >= 0]))),
        "image_G_correlations": image_results,
        "ker_G_correlations": ker_results,
    }
    out_path = POC_DIR / "e9b_kerG_direction_id.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved: {out_path}")


if __name__ == "__main__":
    main()
