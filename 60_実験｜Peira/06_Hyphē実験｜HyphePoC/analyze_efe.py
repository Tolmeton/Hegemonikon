#!/usr/bin/env python3
"""EFE 2項分解の弁別力分析 — analyze_efe.py

PURPOSE: 既存実験データ (results.json) を v0.3 EFE 定義で再計算し、
I_epistemic と I_pragmatic の弁別力・独立性を検証する。

PROOF: linkage_hyphe.md §3.6 EFE(c) = α·I_epistemic + (1-α)·I_pragmatic
  I_epistemic = 1 - cos(chunk_centroid, global_centroid)
  I_pragmatic = boundary_novelty
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# hyphe_chunker をインポート
sys.path.insert(0, str(Path(__file__).parent))
from hyphe_chunker import (
    parse_session_file,
    compute_similarity_trace,
    detect_boundaries,
    steps_to_chunks,
    gf_iterate,
    compute_chunk_metrics,
)

# セッションログのディレクトリ
SESSIONS_DIR = Path(__file__).parent.parent.parent / "30_記憶｜Mneme" / "01_記録｜Records" / "sessions"

# Embedding キャッシュ (別スクリプトで生成済みの場合)
CACHE_DIR = Path(__file__).parent / "embedding_cache"


def load_cached_embeddings(session_id: str) -> list[list[float]] | None:
    """キャッシュ済み embedding を読み込む。"""
    cache_file = CACHE_DIR / f"{session_id}.json"
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)
    return None


def analyze_session(
    session_path: Path,
    tau: float = 0.70,
) -> dict | None:
    """1セッションの EFE 分析を実行。"""
    session_id, steps = parse_session_file(session_path)
    if len(steps) < 3:
        return None

    # embedding 読込
    embeddings = load_cached_embeddings(session_id)
    if embeddings is None:
        print(f"  ⚠️ {session_id}: embedding キャッシュなし。スキップ")
        return None

    if len(embeddings) != len(steps):
        print(f"  ⚠️ {session_id}: steps={len(steps)}, embeddings={len(embeddings)} 不一致")
        return None

    # チャンク化 + EFE 計算
    similarities = compute_similarity_trace(embeddings)
    boundaries = detect_boundaries(similarities, tau=tau)
    chunks = steps_to_chunks(steps, boundaries)
    chunks, iters, converged = gf_iterate(chunks, embeddings, tau=tau)
    chunks = compute_chunk_metrics(chunks, embeddings, similarities)

    if not chunks:
        return None

    # チャンクごとの詳細
    chunk_details = []
    for c in chunks:
        chunk_details.append({
            "chunk_id": c.chunk_id,
            "steps": len(c),
            "coherence": round(c.coherence, 4),
            "drift": round(c.drift, 4),
            "epistemic": round(c.epistemic, 4),
            "pragmatic": round(c.pragmatic, 4),
            "efe": round(c.efe, 4),
            "loss": round(c.loss, 4),
        })

    # 統計
    n = len(chunks)
    mean_epi = sum(c.epistemic for c in chunks) / n
    mean_prag = sum(c.pragmatic for c in chunks) / n
    mean_efe = sum(c.efe for c in chunks) / n
    var_epi = sum((c.epistemic - mean_epi) ** 2 for c in chunks) / n
    var_prag = sum((c.pragmatic - mean_prag) ** 2 for c in chunks) / n
    var_efe = sum((c.efe - mean_efe) ** 2 for c in chunks) / n

    # epistemic-pragmatic 相関 (Pearson)
    if n > 1 and var_epi > 0 and var_prag > 0:
        import math
        cov = sum(
            (c.epistemic - mean_epi) * (c.pragmatic - mean_prag) for c in chunks
        ) / n
        corr = cov / (math.sqrt(var_epi) * math.sqrt(var_prag))
    else:
        corr = 0.0

    return {
        "session_id": session_id,
        "tau": tau,
        "num_chunks": n,
        "mean_epistemic": round(mean_epi, 4),
        "mean_pragmatic": round(mean_prag, 4),
        "mean_efe": round(mean_efe, 4),
        "var_epistemic": round(var_epi, 6),
        "var_pragmatic": round(var_prag, 6),
        "var_efe": round(var_efe, 6),
        "corr_epi_prag": round(corr, 4),
        "chunks": chunk_details,
    }


def main():
    """全セッションの EFE 分析を実行。"""
    taus = [0.60, 0.70, 0.75, 0.80]

    # セッションファイルを列挙
    session_files = sorted(SESSIONS_DIR.glob("session_*.md"))
    if not session_files:
        print(f"❌ セッションファイルが見つかりません: {SESSIONS_DIR}")
        return

    print(f"📊 EFE 2項分解分析 — {len(session_files)} sessions × {len(taus)} τ values")
    print("=" * 70)

    all_results = []

    for tau in taus:
        print(f"\n--- τ = {tau} ---")
        tau_results = []

        for sf in session_files:
            result = analyze_session(sf, tau=tau)
            if result:
                tau_results.append(result)
                print(
                    f"  {result['session_id']}: "
                    f"chunks={result['num_chunks']:2d} | "
                    f"epi={result['mean_epistemic']:.4f} | "
                    f"prag={result['mean_pragmatic']:.4f} | "
                    f"EFE={result['mean_efe']:.4f} | "
                    f"r(e,p)={result['corr_epi_prag']:+.3f}"
                )

        if tau_results:
            # τ レベルの集計
            n_sessions = len(tau_results)
            avg_epi = sum(r["mean_epistemic"] for r in tau_results) / n_sessions
            avg_prag = sum(r["mean_pragmatic"] for r in tau_results) / n_sessions
            avg_efe = sum(r["mean_efe"] for r in tau_results) / n_sessions
            avg_var_epi = sum(r["var_epistemic"] for r in tau_results) / n_sessions
            avg_var_prag = sum(r["var_pragmatic"] for r in tau_results) / n_sessions
            avg_corr = sum(r["corr_epi_prag"] for r in tau_results) / n_sessions

            print(f"\n  📈 集計 ({n_sessions} sessions):")
            print(f"     mean epistemic:  {avg_epi:.4f} (var: {avg_var_epi:.6f})")
            print(f"     mean pragmatic:  {avg_prag:.4f} (var: {avg_var_prag:.6f})")
            print(f"     mean EFE:        {avg_efe:.4f}")
            print(f"     mean corr(e,p):  {avg_corr:+.4f}")
            print(f"     → 独立性: {'✅ 低相関' if abs(avg_corr) < 0.5 else '⚠️ 高相関'}")

        all_results.extend(tau_results)

    # 結果を JSON 保存
    output_path = Path(__file__).parent / "efe_analysis_results.json"
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 結果を保存: {output_path}")


if __name__ == "__main__":
    main()
