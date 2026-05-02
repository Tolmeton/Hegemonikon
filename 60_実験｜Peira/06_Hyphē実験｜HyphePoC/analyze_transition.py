#!/usr/bin/env python3
"""相転移点の特定 — similarity 分布の解析。

PURPOSE: 全13セッションの隣接ステップ cosine similarity 分布を解析し、
τ の相転移点を正確に特定する。

出力:
  1. similarity のヒストグラム (テキスト版)
  2. 基本統計量 (mean, median, std, percentiles)
  3. τ sweep (0.60-0.85, 0.01刻み) でのチャンク数変化
  4. 二次微分による相転移点の特定
"""

import json
import math
import sys
from pathlib import Path

# τ=0.7 の結果から similarity_trace を取得
RESULTS_DIR = Path(__file__).resolve().parent

def load_similarity_traces() -> list[float]:
    """全セッションの similarity trace を結合。"""
    results_file = RESULTS_DIR / "results.json"
    if not results_file.exists():
        print(f"❌ {results_file} が見つかりません")
        sys.exit(1)

    with open(results_file) as f:
        results = json.load(f)

    all_sims = []
    for r in results:
        if r.get("status") == "ok" and "similarity_trace" in r:
            all_sims.extend(r["similarity_trace"])

    return all_sims


def histogram(values: list[float], bins: int = 20, width: int = 50) -> str:
    """テキストベースのヒストグラム。"""
    if not values:
        return "データなし"

    min_v, max_v = min(values), max(values)
    bin_width = (max_v - min_v) / bins

    counts = [0] * bins
    for v in values:
        idx = int((v - min_v) / bin_width)
        idx = min(idx, bins - 1)
        counts[idx] += 1

    max_count = max(counts) if counts else 1
    lines = []
    for i in range(bins):
        lo = min_v + i * bin_width
        hi = lo + bin_width
        bar_len = int(counts[i] / max_count * width)
        bar = "█" * bar_len
        lines.append(f"  {lo:.3f}-{hi:.3f} | {bar} ({counts[i]})")

    return "\n".join(lines)


def percentiles(values: list[float], ps: list[int]) -> dict[int, float]:
    """パーセンタイル計算。"""
    sorted_v = sorted(values)
    n = len(sorted_v)
    result = {}
    for p in ps:
        idx = int(n * p / 100)
        idx = min(idx, n - 1)
        result[p] = sorted_v[idx]
    return result


def tau_sweep(
    all_sims: list[float],
    tau_range: tuple[float, float] = (0.55, 0.90),
    step: float = 0.01,
) -> list[tuple[float, int]]:
    """τ を sweep してチャンク数 (= 境界数 + セッション数) を計算。

    境界数 = similarity < τ の個数
    チャンク数 ≈ 境界数 + 13 (セッション数)
    """
    results = []
    tau = tau_range[0]
    while tau <= tau_range[1]:
        boundaries = sum(1 for s in all_sims if s < tau)
        # 各セッションの境界数は近似: total_boundaries + 13 sessions
        results.append((round(tau, 3), boundaries + 13))
        tau += step
    return results


def find_phase_transition(sweep: list[tuple[float, int]]) -> tuple[float, float]:
    """二次微分 (加速度) が最大の点 = 相転移点。

    一次微分: d(chunks)/d(τ)
    二次微分: d²(chunks)/d(τ)²
    相転移点: 二次微分の最大値の位置
    """
    if len(sweep) < 3:
        return sweep[0][0], 0.0

    # 一次微分
    first_deriv = []
    for i in range(1, len(sweep)):
        dt = sweep[i][0] - sweep[i-1][0]
        dc = sweep[i][1] - sweep[i-1][1]
        first_deriv.append((sweep[i][0], dc / dt if dt > 0 else 0))

    # 二次微分
    second_deriv = []
    for i in range(1, len(first_deriv)):
        dt = first_deriv[i][0] - first_deriv[i-1][0]
        dd = first_deriv[i][1] - first_deriv[i-1][1]
        second_deriv.append((first_deriv[i][0], dd / dt if dt > 0 else 0))

    # 最大加速度の位置
    max_accel = max(second_deriv, key=lambda x: x[1])
    return max_accel


def main():
    print("=" * 60)
    print("Hyphē 相転移点解析")
    print("=" * 60)

    # 1. 全 similarity trace を読み込み
    all_sims = load_similarity_traces()
    print(f"\n総データ点: {len(all_sims)} (隣接ステップペア)")

    # 2. 基本統計量
    mean = sum(all_sims) / len(all_sims)
    sorted_sims = sorted(all_sims)
    median = sorted_sims[len(sorted_sims) // 2]
    variance = sum((x - mean) ** 2 for x in all_sims) / len(all_sims)
    std = math.sqrt(variance)

    pcts = percentiles(all_sims, [5, 10, 25, 50, 75, 90, 95])

    print(f"\n--- 基本統計量 ---")
    print(f"  Mean:   {mean:.4f}")
    print(f"  Median: {median:.4f}")
    print(f"  Std:    {std:.4f}")
    print(f"  Min:    {min(all_sims):.4f}")
    print(f"  Max:    {max(all_sims):.4f}")
    print(f"\n--- パーセンタイル ---")
    for p, v in sorted(pcts.items()):
        print(f"  P{p:2d}: {v:.4f}")

    # 3. ヒストグラム
    print(f"\n--- Similarity 分布 (隣接ステップ) ---")
    print(histogram(all_sims, bins=25))

    # 4. τ sweep
    print(f"\n--- τ Sweep (0.55-0.90, 0.01刻み) ---")
    sweep = tau_sweep(all_sims)

    print(f"  {'τ':>6}  {'Chunks':>8}  {'Δ':>8}  Graph")
    prev_chunks = 0
    for tau, chunks in sweep:
        delta = chunks - prev_chunks
        bar = "▓" * min(int(delta / 5), 40)
        marker = " ◄◄" if delta > 50 else ""
        print(f"  {tau:6.3f}  {chunks:8d}  {delta:+8d}  {bar}{marker}")
        prev_chunks = chunks

    # 5. 相転移点の特定
    print(f"\n--- 相転移点解析 ---")
    transition_tau, acceleration = find_phase_transition(sweep)
    print(f"  最大加速度の τ: {transition_tau:.3f}")
    print(f"  加速度:         {acceleration:.1f}")

    # 相転移周辺の詳細 sweep
    print(f"\n--- 相転移周辺の詳細 (0.001刻み) ---")
    fine_sweep = tau_sweep(all_sims, (transition_tau - 0.03, transition_tau + 0.03), 0.001)
    prev_chunks = fine_sweep[0][1] if fine_sweep else 0
    for tau, chunks in fine_sweep:
        delta = chunks - prev_chunks
        bar = "▓" * min(delta, 40)
        print(f"  {tau:7.4f}  {chunks:6d}  {delta:+4d}  {bar}")
        prev_chunks = chunks

    # 最終結論
    print(f"\n{'=' * 60}")
    print(f"結論:")
    print(f"  相転移点 τ* ≈ {transition_tau:.3f}")
    print(f"  この τ で隣接類似度分布の密度が最大 → チャンク数が最も急激に変化")
    print(f"  推奨 τ 範囲: [{transition_tau - 0.02:.3f}, {transition_tau + 0.02:.3f}]")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
