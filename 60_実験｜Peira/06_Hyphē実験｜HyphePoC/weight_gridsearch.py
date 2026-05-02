#!/usr/bin/env python3
"""Ensemble weight (w) のグリッドサーチ。

w ∈ {0.0, 0.1, 0.2, ..., 1.0} の 11 点で E2E 比較し、
precision_mean, loss_mean, discriminability を最適化する w を探索する。
"""
import sys
import time
import json
from pathlib import Path

# パス設定
root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root / "20_機構｜Mekhane" / "_src｜ソースコード"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from scipy import stats
from hyphe_chunker import Step, chunk_session

# E2E スクリプトから再利用
from run_ensemble_e2e_5sessions import (
    generate_dummy_sessions,
    embed_local,
    embed_model_b,
    cos_sim_matrix,
    compute_chunk_ensemble_precisions,
)


def run_with_weight(session_steps: list[dict], w: float) -> dict | None:
    """1セッションを指定 weight で実行し、メトリクスを返す。"""
    steps = [Step(index=s["index"], text=s["text"]) for s in session_steps]
    if len(steps) < 8:
        return None

    texts = [s.text for s in steps]
    emb_loc = embed_local(texts)
    emb_b = embed_model_b(texts)
    emb_list = emb_loc.tolist()

    # kNN チャンキング (ベースライン: w=0.0)
    result_base = chunk_session(
        steps, emb_list,
        tau=0.70, sim_mode="knn", sim_k=3,
        ensemble_precisions=None,
        ensemble_weight=0.0,
    )

    # チャンクのステップ構成を取得
    chunk_step_indices = []
    for chunk in result_base.chunks:
        indices = [s.index for s in chunk.steps]
        chunk_step_indices.append(indices)

    # RSA ベース Ensemble Precision
    ensemble_precs = compute_chunk_ensemble_precisions(
        chunk_step_indices, emb_loc, emb_b
    )

    # 指定 weight でチャンキング
    result = chunk_session(
        steps, emb_list,
        tau=0.70, sim_mode="knn", sim_k=3,
        ensemble_precisions=ensemble_precs,
        ensemble_weight=w,
    )

    m = result.metrics
    p = m.get("mean_precision", 0)
    v = m.get("precision_var", 0)
    return {
        "precision_mean": p,
        "precision_var": v,
        "loss_mean": m.get("mean_loss", 0),
        "discriminability": (v ** 0.5) / (p + 1e-9) if p > 0 else 0,
        "n_chunks": m.get("num_chunks", 0),
    }


def main():
    weights = [round(w * 0.1, 1) for w in range(11)]  # 0.0, 0.1, ..., 1.0
    sessions = generate_dummy_sessions(5)

    print("=" * 80)
    print("Ensemble Weight グリッドサーチ")
    print(f"weights = {weights}")
    print(f"sessions = {len(sessions)}")
    print("=" * 80)

    # 全 weight × 全セッションを実行
    all_results = {}  # {w: [session_results]}
    t0_total = time.time()

    for w in weights:
        t0 = time.time()
        session_results = []
        for i, session in enumerate(sessions):
            r = run_with_weight(session, w)
            if r:
                session_results.append(r)
        all_results[w] = session_results
        dt = time.time() - t0
        n = len(session_results)
        avg_p = sum(r["precision_mean"] for r in session_results) / n if n else 0
        avg_l = sum(r["loss_mean"] for r in session_results) / n if n else 0
        print(f"  w={w:.1f} | {dt:.1f}s | P={avg_p:.4f} | L={avg_l:.4f} | sessions={n}")

    dt_total = time.time() - t0_total
    print(f"\n合計: {dt_total:.1f}s")

    # 集約テーブル
    print("\n" + "=" * 80)
    print("集約結果")
    print("=" * 80)
    print(f"\n{'w':>5} {'P_mean':>8} {'P_var':>10} {'Loss':>8} {'Disc(CV)':>10} {'Chunks':>7} {'ΔP':>8}")
    print("-" * 66)

    baseline_p = None
    best_w = 0.0
    best_p = -1.0
    rows = []

    for w in weights:
        rs = all_results[w]
        n = len(rs)
        if n == 0:
            continue
        avg_p = sum(r["precision_mean"] for r in rs) / n
        avg_v = sum(r["precision_var"] for r in rs) / n
        avg_l = sum(r["loss_mean"] for r in rs) / n
        avg_d = sum(r["discriminability"] for r in rs) / n
        avg_c = sum(r["n_chunks"] for r in rs) / n

        if baseline_p is None:
            baseline_p = avg_p

        dp = avg_p - baseline_p
        print(f"  {w:.1f} {avg_p:>8.4f} {avg_v:>10.6f} {avg_l:>8.4f} {avg_d:>10.4f} {avg_c:>7.1f} {dp:>+8.4f}")

        rows.append({
            "w": w,
            "precision_mean": avg_p,
            "precision_var": avg_v,
            "loss_mean": avg_l,
            "discriminability": avg_d,
            "n_chunks": avg_c,
            "delta_p": dp,
        })

        if avg_p > best_p:
            best_p = avg_p
            best_w = w

    # 最適 weight
    print(f"\n{'='*50}")
    print(f"最適 w = {best_w:.1f} (precision_mean = {best_p:.4f})")
    if baseline_p and baseline_p > 0:
        print(f"改善率: {(best_p - baseline_p) / baseline_p * 100:+.1f}% (vs w=0.0)")
    print(f"{'='*50}")

    # JSON 保存
    output = {
        "weights": weights,
        "best_w": best_w,
        "best_precision": best_p,
        "baseline_precision": baseline_p,
        "results": rows,
    }
    out_path = Path(__file__).parent / "weight_gridsearch_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n結果保存: {out_path}")


if __name__ == "__main__":
    main()
