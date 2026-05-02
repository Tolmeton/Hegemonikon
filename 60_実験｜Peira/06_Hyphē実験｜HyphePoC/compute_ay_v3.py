#!/usr/bin/env python3
"""compute_ay_v3 — Polynomial AY: チャンク間到達可能性の定量測定。

AY(index_op) = Σ_c (|Act_1(c)| - |Act_0(c)|)

where:
  Act_0(c) = gf_off でのチャンク c からの到達可能チャンク数
  Act_1(c) = gf_on  でのチャンク c からの到達可能チャンク数
  到達可能 = cosine_sim(centroid_c, centroid_c') > τ_link

Phase 1 (PoC): 13 sessions × τ=0.7 × τ_link sweep
  - embedding_cache.pkl + results.json
  - gf_on = results.json のチャンク境界 (G∘F 適用後)
  - gf_off = 等間隔分割 (G∘F 適用前の近似)

設計書: DESIGN_compute_ay_v3.md
理論: B_polynomial_linkage.md §3
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

BASE = Path(__file__).parent


def load_data():
    """embedding_cache.pkl + results.json を読み込む。"""
    with open(BASE / "embedding_cache.pkl", "rb") as f:
        cache = pickle.load(f)

    with open(BASE / "results.json", encoding="utf-8") as f:
        results = json.load(f)

    return cache, results


def parse_step_range(step_range_str: str) -> tuple[int, int]:
    """'0-5' → (0, 5)"""
    parts = step_range_str.split("-")
    return int(parts[0]), int(parts[1])


def compute_centroids(embeddings: np.ndarray, chunks: list[dict]) -> np.ndarray:
    """各チャンクのセントロイド (mean embedding, L2正規化) を計算。

    Args:
        embeddings: (N_steps, 768) の embedding 行列
        chunks: step_range を含むチャンクのリスト

    Returns:
        (N_chunks, 768) のセントロイド行列
    """
    centroids = []
    for chunk in chunks:
        start, end = parse_step_range(chunk["step_range"])
        chunk_embs = embeddings[start : end + 1]
        if len(chunk_embs) == 0:
            centroids.append(np.zeros(embeddings.shape[1]))
            continue
        centroid = np.mean(chunk_embs, axis=0)
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm
        centroids.append(centroid)
    return np.array(centroids)


def make_equal_chunks(total_steps: int, num_chunks: int) -> list[dict]:
    """等間隔分割でチャンク境界を生成 (gf_off 近似)。"""
    if num_chunks <= 0:
        return []
    chunk_size = total_steps / num_chunks
    chunks = []
    for i in range(num_chunks):
        start = int(round(i * chunk_size))
        end = int(round((i + 1) * chunk_size)) - 1
        end = min(end, total_steps - 1)
        chunks.append({"step_range": f"{start}-{end}", "num_steps": end - start + 1})
    return chunks


def compute_similarity_matrix(centroids: np.ndarray) -> np.ndarray:
    """セントロイド間のコサイン類似度行列を計算。"""
    # centroids は L2 正規化済みなので内積 = cosine sim
    return centroids @ centroids.T


def compute_act(sim_matrix: np.ndarray, tau_link: float) -> np.ndarray:
    """各チャンクの Act(c) = 到達可能な他チャンク数。

    Returns:
        (N_chunks,) の整数配列
    """
    n = sim_matrix.shape[0]
    # 対角を除外して閾値判定
    mask = sim_matrix > tau_link
    np.fill_diagonal(mask, False)
    return mask.sum(axis=1)


def compute_effective_rank(sim_matrix: np.ndarray) -> float:
    """類似度行列の有効ランク (effective rank)。

    effective_rank = exp(H(lambda_normalized))
    where H = Shannon entropy of normalized eigenvalues.

    解釈:
      - 全チャンクが同じ centroid → 固有値1個に集中 → eff_rank ≈ 1
      - 各チャンクが独立トピック → 固有値が分散 → eff_rank ≈ N
      - G∘F が良貨/悪貨を分離するなら、eff_rank は増加するはず

    Ref: Roy & Bhatti (2007), Vershynin (2018)
    """
    eigenvalues = np.linalg.eigvalsh(sim_matrix)
    # 数値安定性: 負の微小固有値をゼロに
    eigenvalues = np.maximum(eigenvalues, 0)
    total = eigenvalues.sum()
    if total == 0:
        return 1.0
    # 正規化
    p = eigenvalues / total
    # ゼロを除外してエントロピー計算
    p = p[p > 0]
    entropy = -np.sum(p * np.log(p))
    return float(np.exp(entropy))


def compute_spectral_ay(sim_before: np.ndarray, sim_after: np.ndarray) -> dict:
    """Spectral AY (B×C hybrid): 有効ランク差分 + 固有値スペクトル情報。

    AY_spectral = effective_rank(sim_after) - effective_rank(sim_before)

    良貨/悪貨の分離を固有値スペクトルの情報量で測定する。
    - 悪貨 (偽陽性到達): 全 centroid が似る → rank 1 に退化
    - 良貨 (真の到達): 各チャンクが固有トピック → rank ↑
    """
    er_before = compute_effective_rank(sim_before)
    er_after = compute_effective_rank(sim_after)

    # 固有値スペクトルも記録 (診断用)
    eig_before = sorted(np.linalg.eigvalsh(sim_before).tolist(), reverse=True)
    eig_after = sorted(np.linalg.eigvalsh(sim_after).tolist(), reverse=True)

    return {
        "ay_spectral": float(er_after - er_before),
        "effective_rank_before": float(er_before),
        "effective_rank_after": float(er_after),
        "eigenvalues_before": eig_before,
        "eigenvalues_after": eig_after,
    }


def compute_continuous_ay(sim_before: np.ndarray, sim_after: np.ndarray) -> dict:
    """連続 AY: 閾値なしでチャンク間類似度の合計差を測定。

    AY_continuous = Σ_{c≠c'} (sim_after(c,c') - sim_before(c,c'))

    天井効果 (全 sim > 0.85) で二値 AY が弁別不能な場合の補完指標。
    """
    n = sim_before.shape[0]
    idx = np.triu_indices(n, k=1)
    diff = sim_after[idx] - sim_before[idx]
    return {
        "ay_continuous": float(diff.sum()),
        "ay_continuous_mean": float(diff.mean()),
        "ay_continuous_per_pair": diff.tolist(),
        "n_pairs": len(diff),
        "pairs_improved": int((diff > 0).sum()),
        "pairs_degraded": int((diff < 0).sum()),
    }


def compute_ay_session(
    embeddings: np.ndarray,
    chunks_after: list[dict],
    total_steps: int,
    tau_links: list[float],
) -> dict:
    """1セッションの AY を τ_link sweep + 連続 AY で計算。

    gf_on = chunks_after (results.json の境界)
    gf_off = 等間隔分割 (G∘F 適用前の近似)
    """
    num_chunks = len(chunks_after)
    if num_chunks <= 1:
        return {
            "num_chunks": num_chunks,
            "skipped": True,
            "reason": "1 chunk or less",
            "tau_link_results": [],
            "continuous": None,
            "spectral": None,
        }

    # gf_on: G∘F 適用後のチャンク境界
    centroids_after = compute_centroids(embeddings, chunks_after)
    sim_after = compute_similarity_matrix(centroids_after)

    # gf_off: 等間隔分割 (G∘F 適用前の近似)
    chunks_before = make_equal_chunks(total_steps, num_chunks)
    centroids_before = compute_centroids(embeddings, chunks_before)
    sim_before = compute_similarity_matrix(centroids_before)

    # 二値 AY (τ_link sweep)
    tau_link_results = []
    for tau_link in tau_links:
        act_after = compute_act(sim_after, tau_link)
        act_before = compute_act(sim_before, tau_link)

        ay_per_chunk = act_after.astype(int) - act_before.astype(int)
        ay_total = int(ay_per_chunk.sum())

        tau_link_results.append(
            {
                "tau_link": tau_link,
                "ay_total": ay_total,
                "ay_per_chunk": ay_per_chunk.tolist(),
                "mean_act_before": float(act_before.mean()),
                "mean_act_after": float(act_after.mean()),
                "mean_sim_before": float(
                    sim_before[np.triu_indices(num_chunks, k=1)].mean()
                ),
                "mean_sim_after": float(
                    sim_after[np.triu_indices(num_chunks, k=1)].mean()
                ),
            }
        )

    # 連続 AY
    continuous = compute_continuous_ay(sim_before, sim_after)

    # Spectral AY (B×C hybrid)
    spectral = compute_spectral_ay(sim_before, sim_after)

    return {
        "num_chunks": num_chunks,
        "skipped": False,
        "tau_link_results": tau_link_results,
        "continuous": continuous,
        "spectral": spectral,
    }


def main():
    cache, results = load_data()

    tau_links = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]

    sessions_output = []
    tau_link_aggregates = {tl: [] for tl in tau_links}
    continuous_values = []
    spectral_values = []

    for sess in results:
        sid = sess["session_id"]
        total_steps = sess["total_steps"]
        chunks = sess.get("chunks", [])

        if sid not in cache:
            sys.stderr.write(f"WARN: {sid} not in embedding cache, skipping\n")
            continue

        raw_embs = cache[sid]["embeddings"]
        embeddings = np.array(raw_embs)

        result = compute_ay_session(embeddings, chunks, total_steps, tau_links)

        session_record = {
            "session_id": sid,
            "total_steps": total_steps,
            **result,
        }
        sessions_output.append(session_record)

        if not result["skipped"]:
            for tlr in result["tau_link_results"]:
                tau_link_aggregates[tlr["tau_link"]].append(tlr["ay_total"])
            if result["continuous"]:
                continuous_values.append(result["continuous"]["ay_continuous"])
            if result["spectral"]:
                spectral_values.append(result["spectral"]["ay_spectral"])

    # τ_link sweep 集計
    sweep_summary = []
    for tl in tau_links:
        values = tau_link_aggregates[tl]
        if not values:
            continue
        arr = np.array(values)
        sweep_summary.append(
            {
                "tau_link": tl,
                "mean_ay": float(arr.mean()),
                "median_ay": float(np.median(arr)),
                "std_ay": float(arr.std()),
                "ay_positive_count": int((arr > 0).sum()),
                "ay_zero_count": int((arr == 0).sum()),
                "ay_negative_count": int((arr < 0).sum()),
                "ay_positive_pct": float((arr > 0).mean() * 100),
                "n_sessions": len(values),
            }
        )

    # Best τ_link (最も高い mean_ay)
    best = max(sweep_summary, key=lambda x: x["mean_ay"]) if sweep_summary else None

    # 連続 AY 集計
    cont_arr = np.array(continuous_values) if continuous_values else np.array([])
    continuous_summary = {
        "mean_ay_continuous": float(cont_arr.mean()) if len(cont_arr) > 0 else 0,
        "median_ay_continuous": float(np.median(cont_arr)) if len(cont_arr) > 0 else 0,
        "std_ay_continuous": float(cont_arr.std()) if len(cont_arr) > 0 else 0,
        "positive_count": int((cont_arr > 0).sum()) if len(cont_arr) > 0 else 0,
        "negative_count": int((cont_arr < 0).sum()) if len(cont_arr) > 0 else 0,
        "n_sessions": len(continuous_values),
    }

    # Spectral AY 集計
    spec_arr = np.array(spectral_values) if spectral_values else np.array([])
    spectral_summary = {
        "mean_ay_spectral": float(spec_arr.mean()) if len(spec_arr) > 0 else 0,
        "median_ay_spectral": float(np.median(spec_arr)) if len(spec_arr) > 0 else 0,
        "std_ay_spectral": float(spec_arr.std()) if len(spec_arr) > 0 else 0,
        "positive_count": int((spec_arr > 0).sum()) if len(spec_arr) > 0 else 0,
        "negative_count": int((spec_arr < 0).sum()) if len(spec_arr) > 0 else 0,
        "n_sessions": len(spectral_values),
    }

    output = {
        "version": "v3.1",
        "phase": "Phase 1 PoC — Good Money / Bad Money",
        "theory": "B_polynomial_linkage.md §3 + effective rank (Vershynin)",
        "metric_binary": "AY = Σ_c (|Act_1(c)| - |Act_0(c)|)",
        "metric_continuous": "AY_cont = Σ_{c≠c'} (sim_after - sim_before)",
        "metric_spectral": "AY_spec = effective_rank(sim_after) - effective_rank(sim_before)",
        "data_source": {
            "embeddings": "embedding_cache.pkl (13 sessions, 768d)",
            "chunks": "results.json (τ=0.7, gf_on)",
            "gf_off_method": "equal-size chunks (same num_chunks as gf_on)",
        },
        "tau_link_sweep": sweep_summary,
        "best_tau_link": best["tau_link"] if best else None,
        "best_mean_ay": best["mean_ay"] if best else None,
        "continuous_summary": continuous_summary,
        "spectral_summary": spectral_summary,
        "sessions": sessions_output,
    }

    # JSON 出力
    out_path = BASE / "ay_v3_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Human-readable 出力
    print("=" * 60)
    print("AY v3: Polynomial Functor — チャンク間到達可能性")
    print("=" * 60)
    print(f"  sessions: {len(sessions_output)}")
    print(f"  τ (chunk boundary): 0.7")
    print(f"  τ_link sweep: {tau_links}")
    print(f"  gf_off: equal-size chunks (same N as gf_on)")
    print()
    print("τ_link sweep results:")
    print(f"  {'τ_link':>6} | {'mean_AY':>8} | {'med_AY':>7} | {'std':>6} | {'AY>0':>5} | {'%':>5}")
    print(f"  {'-'*6}-+-{'-'*8}-+-{'-'*7}-+-{'-'*6}-+-{'-'*5}-+-{'-'*5}")
    for s in sweep_summary:
        print(
            f"  {s['tau_link']:6.2f} | {s['mean_ay']:+8.2f} | {s['median_ay']:+7.1f} "
            f"| {s['std_ay']:6.2f} | {s['ay_positive_count']:2d}/{s['n_sessions']:2d} "
            f"| {s['ay_positive_pct']:5.1f}"
        )
    print()
    if best:
        print(f"  Best τ_link = {best['tau_link']:.2f}, mean_AY = {best['mean_ay']:+.2f}")
        print(
            f"  → Binary AY > 0: {'YES' if best['mean_ay'] > 0 else 'NO'} "
            f"(ceiling effect: sim range too narrow for binary threshold)"
        )

    # Spectral AY (PRIMARY METRIC)
    print()
    print("=" * 60)
    print("Spectral AY (B*C hybrid) — Good Money metric")
    print("=" * 60)
    print(f"  AY_spec = effective_rank(sim_after) - effective_rank(sim_before)")
    print(f"  effective_rank = exp(H(normalized_eigenvalues))")
    ss = spectral_summary
    print(f"  mean     = {ss['mean_ay_spectral']:+.6f}")
    print(f"  median   = {ss['median_ay_spectral']:+.6f}")
    print(f"  std      = {ss['std_ay_spectral']:.6f}")
    if ss['n_sessions'] > 0:
        print(
            f"  positive = {ss['positive_count']}/{ss['n_sessions']} "
            f"({ss['positive_count']/ss['n_sessions']*100:.1f}%)"
        )
        print(
            f"  → Spectral AY > 0: "
            f"{'YES' if ss['mean_ay_spectral'] > 0 else 'NO'}"
        )
        if ss['mean_ay_spectral'] > 0:
            print("  → G*F increases effective dimensionality (good money preserved)")
        else:
            print("  → G*F decreases effective dimensionality")

    print()
    print("Session details (spectral AY):")
    for s in sessions_output:
        if s.get("skipped"):
            print(f"  {s['session_id']}: SKIPPED ({s.get('reason', '')})")
            continue
        spec = s.get("spectral")
        if spec:
            ay_s = spec["ay_spectral"]
            sign = "+" if ay_s > 0 else ""
            print(
                f"  {s['session_id']}: {s['num_chunks']}ch, "
                f"AY_spec={sign}{ay_s:.4f}, "
                f"eff_rank_before={spec['effective_rank_before']:.3f}, "
                f"eff_rank_after={spec['effective_rank_after']:.3f}"
            )

    # 連続 AY (secondary)
    print()
    print("Continuous AY (threshold-free, secondary):")
    cs = continuous_summary
    print(f"  mean={cs['mean_ay_continuous']:+.6f}, "
          f"positive={cs['positive_count']}/{cs['n_sessions']}")

    print(f"\n→ Results saved to: {out_path}")


if __name__ == "__main__":
    main()
