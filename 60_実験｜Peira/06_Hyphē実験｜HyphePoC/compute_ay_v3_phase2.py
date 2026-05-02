#!/usr/bin/env python3
"""compute_ay_v3 Phase 2 — 30 sessions × 4τ × gf_on/gf_off の Spectral AY 比較。

Phase 1 は等間隔近似で gf_off を模擬した。
Phase 2 は hyphe_chunker を直接呼んで真の gf_off (max_iterations=0) と
gf_on (max_iterations=10) の境界を再現し、Spectral AY を比較する。

設計書: DESIGN_compute_ay_v3.md §8 Phase 2
"""
import json
import os
import pickle
import sys
from pathlib import Path

import numpy as np

# Windows cp932 対策
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))

from compute_ay_v3 import (
    compute_centroids,
    compute_effective_rank,
    compute_similarity_matrix,
    compute_spectral_ay,
)
from hyphe_chunker import Step, chunk_session

BASE = Path(__file__).parent


def load_data():
    with open(BASE / "embedding_cache_100.pkl", "rb") as f:
        cache = pickle.load(f)
    with open(BASE / "gf_verification_100_results.json", encoding="utf-8") as f:
        gf_data = json.load(f)
    return cache, gf_data


def chunks_to_step_ranges(result) -> list[dict]:
    """ChunkingResult から step_range 形式のリストを生成。"""
    ranges = []
    for chunk in result.chunks:
        start = chunk.steps[0].index
        end = chunk.steps[-1].index
        ranges.append({"step_range": f"{start}-{end}", "num_steps": len(chunk.steps)})
    return ranges


def run_chunker(steps, embeddings, tau, max_iterations):
    """hyphe_chunker を指定条件で実行し、チャンク境界を返す。"""
    result = chunk_session(
        steps=steps,
        embeddings=embeddings,
        tau=tau,
        max_iterations=max_iterations,
    )
    return chunks_to_step_ranges(result), len(result.chunks)


def compute_session_spectral(
    session_id: str,
    cache_entry: dict,
    tau: float,
) -> dict:
    """1 session × 1 tau で gf_on/gf_off の Spectral AY を計算。"""
    steps = cache_entry["steps"]
    raw_embs = cache_entry["embeddings"]
    embeddings = np.array(raw_embs)

    # gf_off: max_iterations=0 (境界検出のみ、G∘F 反復なし)
    chunks_off, n_off = run_chunker(steps, raw_embs, tau, max_iterations=0)

    # gf_on: max_iterations=10 (G∘F 反復あり)
    chunks_on, n_on = run_chunker(steps, raw_embs, tau, max_iterations=10)

    # 両方 2 chunks 以上必要
    if n_off <= 1 or n_on <= 1:
        return {
            "session_id": session_id,
            "tau": tau,
            "skipped": True,
            "reason": f"chunks too few: off={n_off}, on={n_on}",
            "n_chunks_off": n_off,
            "n_chunks_on": n_on,
        }

    # Centroid → Similarity Matrix
    centroids_off = compute_centroids(embeddings, chunks_off)
    sim_off = compute_similarity_matrix(centroids_off)

    centroids_on = compute_centroids(embeddings, chunks_on)
    sim_on = compute_similarity_matrix(centroids_on)

    # Spectral AY (raw)
    spectral = compute_spectral_ay(sim_off, sim_on)

    # Normalized: eff_rank / num_chunks = チャンクあたりの情報効率
    er_off_norm = spectral["effective_rank_before"] / n_off
    er_on_norm = spectral["effective_rank_after"] / n_on
    ay_normalized = er_on_norm - er_off_norm

    return {
        "session_id": session_id,
        "tau": tau,
        "skipped": False,
        "n_chunks_off": n_off,
        "n_chunks_on": n_on,
        "total_steps": len(steps),
        **spectral,
        "er_norm_before": float(er_off_norm),
        "er_norm_after": float(er_on_norm),
        "ay_normalized": float(ay_normalized),
    }


def main():
    cache, gf_data = load_data()
    taus = gf_data["taus"]  # [0.6, 0.7, 0.75, 0.8]
    session_ids = sorted(cache.keys())

    print("=" * 60)
    print("AY v3 Phase 2: 30 sessions × 4τ × gf_on/gf_off")
    print("  Spectral AY (effective rank) — Good Money metric")
    print("=" * 60)
    print(f"  sessions: {len(session_ids)}")
    print(f"  taus: {taus}")
    print()

    all_results = []
    tau_summaries = {}

    for tau in taus:
        tau_results = []
        print(f"--- τ = {tau} ---")
        for sid in session_ids:
            result = compute_session_spectral(sid, cache[sid], tau)
            all_results.append(result)
            if not result["skipped"]:
                tau_results.append(result)

        # Summarize this tau
        if tau_results:
            ay_vals = np.array([r["ay_spectral"] for r in tau_results])
            ay_norm = np.array([r["ay_normalized"] for r in tau_results])
            summary = {
                "tau": tau,
                "n_sessions": len(tau_results),
                "n_skipped": len(session_ids) - len(tau_results),
                "mean_ay_spectral": float(ay_vals.mean()),
                "median_ay_spectral": float(np.median(ay_vals)),
                "std_ay_spectral": float(ay_vals.std()),
                "positive_count": int((ay_vals > 0).sum()),
                "positive_pct": float((ay_vals > 0).mean() * 100),
                "mean_ay_normalized": float(ay_norm.mean()),
                "median_ay_normalized": float(np.median(ay_norm)),
                "norm_positive_count": int((ay_norm > 0).sum()),
                "norm_positive_pct": float((ay_norm > 0).mean() * 100),
                "mean_er_before": float(
                    np.mean([r["effective_rank_before"] for r in tau_results])
                ),
                "mean_er_after": float(
                    np.mean([r["effective_rank_after"] for r in tau_results])
                ),
                "mean_n_chunks_off": float(
                    np.mean([r["n_chunks_off"] for r in tau_results])
                ),
                "mean_n_chunks_on": float(
                    np.mean([r["n_chunks_on"] for r in tau_results])
                ),
            }
            tau_summaries[tau] = summary
            print(
                f"  raw: mean={summary['mean_ay_spectral']:+.4f} pos={summary['positive_count']}/{summary['n_sessions']}"
                f"  |  norm: mean={summary['mean_ay_normalized']:+.4f} pos={summary['norm_positive_count']}/{summary['n_sessions']}"
                f"  |  chunks: off={summary['mean_n_chunks_off']:.1f} on={summary['mean_n_chunks_on']:.1f}"
            )
        else:
            print("  (all skipped)")

    # Cross-tau summary
    print()
    print("=" * 60)
    print("Cross-τ Summary (Spectral AY)")
    print("=" * 60)
    print(f"  {'τ':>5} | {'AY_raw':>8} | {'pos_r':>5} | {'AY_norm':>8} | {'pos_n':>5} | {'ch_off':>6} | {'ch_on':>5}")
    print(f"  {'-'*5}-+-{'-'*8}-+-{'-'*5}-+-{'-'*8}-+-{'-'*5}-+-{'-'*6}-+-{'-'*5}")
    for tau in taus:
        s = tau_summaries.get(tau)
        if s:
            print(
                f"  {s['tau']:5.2f} | {s['mean_ay_spectral']:+8.4f} | "
                f"{s['positive_count']:2d}/{s['n_sessions']:2d} | "
                f"{s['mean_ay_normalized']:+8.4f} | "
                f"{s['norm_positive_count']:2d}/{s['n_sessions']:2d} | "
                f"{s['mean_n_chunks_off']:6.1f} | {s['mean_n_chunks_on']:5.1f}"
            )

    # τ-invariance check
    if len(tau_summaries) >= 2:
        ay_range = max(s["mean_ay_spectral"] for s in tau_summaries.values()) - min(
            s["mean_ay_spectral"] for s in tau_summaries.values()
        )
        ay_mean = np.mean([s["mean_ay_spectral"] for s in tau_summaries.values()])
        print()
        if ay_mean != 0:
            print(f"  τ-invariance: range/mean = {ay_range/abs(ay_mean):.2f}")
            print(
                f"  → {'PASS (< 0.20)' if ay_range / abs(ay_mean) < 0.20 else 'PARTIAL' if ay_range / abs(ay_mean) < 0.50 else 'FAIL'}"
            )

    # Euporia principle check
    print()
    all_positive = all(
        s["mean_ay_spectral"] > 0 for s in tau_summaries.values()
    )
    majority_positive = all(
        s["positive_pct"] > 50 for s in tau_summaries.values()
    )
    print(
        f"  Euporia principle (mean > 0 for all τ): "
        f"{'YES' if all_positive else 'NO'}"
    )
    print(
        f"  Euporia principle (majority > 0 for all τ): "
        f"{'YES' if majority_positive else 'NO'}"
    )

    # Save
    output = {
        "version": "v3.1",
        "phase": "Phase 2 — True gf_on/gf_off comparison",
        "theory": "B_polynomial_linkage.md §3 + effective rank (Vershynin)",
        "metric": "AY_spec = effective_rank(sim_gf_on) - effective_rank(sim_gf_off)",
        "data_source": {
            "embeddings": "embedding_cache_100.pkl (30 sessions)",
            "gf_off": "hyphe_chunker max_iterations=0 (boundary detection only)",
            "gf_on": "hyphe_chunker max_iterations=10 (full G∘F iteration)",
        },
        "tau_summaries": {str(k): v for k, v in tau_summaries.items()},
        "results": all_results,
    }

    out_path = BASE / "ay_v3_phase2_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n→ Results saved to: {out_path}")


if __name__ == "__main__":
    main()
