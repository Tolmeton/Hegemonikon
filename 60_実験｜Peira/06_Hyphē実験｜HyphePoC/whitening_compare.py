#!/usr/bin/env python3
"""min-max vs quantile 正規化: precision 分布比較。

hyphe_chunker.py の v0.8 quantile 実装を活用し、
Before (v0.7 min-max) と After (v0.8 quantile) の precision 分布を比較する。
"""
import json
import math
import sys
from pathlib import Path
from collections import Counter

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE.parent.parent / "20_機構｜Mekhane" / "_src｜ソースコード"))

from hyphe_chunker import _l2_normalize, _compute_knn_density
import numpy as np


def calc_prec_minmax(rho_effs):
    """v0.7: min-max 正規化"""
    mn, mx = min(rho_effs), max(rho_effs)
    rng = mx - mn
    if rng < 1e-9:
        return [0.5] * len(rho_effs)
    return [(r - mn) / rng for r in rho_effs]


def calc_prec_quantile(rho_effs):
    """v0.8: rank-based quantile 正規化"""
    n = len(rho_effs)
    if n < 2:
        return [0.5] * n
    # 昇順ソートでランク割当 (同値は平均ランク)
    sorted_rhos = sorted(enumerate(rho_effs), key=lambda x: x[1])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n and abs(sorted_rhos[j][1] - sorted_rhos[i][1]) < 1e-12:
            j += 1
        avg_rank = sum(range(i, j)) / (j - i)
        for k in range(i, j):
            ranks[sorted_rhos[k][0]] = avg_rank
        i = j
    return [r / (n - 1) for r in ranks]


def calc_prec_log(rho_effs):
    """log 正規化: log(rho_eff) → min-max"""
    log_rhos = [math.log(max(r, 1e-10)) for r in rho_effs]
    mn, mx = min(log_rhos), max(log_rhos)
    rng = mx - mn
    if rng < 1e-9:
        return [0.5] * len(rho_effs)
    return [(r - mn) / rng for r in log_rhos]


def bimodality(vals):
    n = len(vals)
    if n < 4:
        return 0.0
    m = sum(vals) / n
    m2 = sum((v - m) ** 2 for v in vals) / n
    m3 = sum((v - m) ** 3 for v in vals) / n
    m4 = sum((v - m) ** 4 for v in vals) / n
    if m2 < 1e-15:
        return 0.0
    sk = m3 / (m2 ** 1.5)
    ku = m4 / (m2 ** 2) - 3
    return (sk ** 2 + 1) / (ku + 3)


def print_hist(vals, label):
    bins = Counter()
    for v in vals:
        b = round(int(v * 10) / 10, 1)
        bins[b] += 1
    print("\n{}:".format(label))
    for b in sorted(bins.keys()):
        bar = "#" * bins[b]
        print("  [{:.1f}): {:3d} {}".format(b, bins[b], bar))


def main():
    # v0.7 結果からチャンクごとの rho_eff を再計算
    with open(BASE / "precision_v07_results.json") as f:
        v07_data = json.load(f)

    # embedding キャッシュ読み込み
    cache = np.load(str(BASE / "embedding_cache.npz"), allow_pickle=True)
    all_embs = cache["embeddings"].tolist()
    session_map = cache["session_map"].item()

    v07_map = {r["session_id"]: r for r in v07_data if r.get("status") == "ok"}

    # 各セッションの rho_eff を収集
    all_rho_effs = []
    session_chunks = []  # (sid, chunk_info, rho_eff) のリスト

    for sid, info in session_map.items():
        if sid not in v07_map:
            continue
        s_idx = info["start"]
        e_idx = info["end"]
        embs = all_embs[s_idx:e_idx]
        ci_list = v07_map[sid].get("chunks", [])
        if not ci_list:
            continue

        normed = [_l2_normalize(ev) for ev in embs]
        k = min(5, len(normed) - 1)
        dc = _compute_knn_density(normed, k=k) if len(normed) > 3 else None

        for ci in ci_list:
            sr = ci["step_range"]
            a, b = map(int, sr.split("-"))
            idxs = list(range(a, b + 1))
            if dc:
                rv = [dc[i] for i in idxs if i < len(dc)]
                rm = sum(rv) / len(rv) if rv else 0.5
            else:
                rm = 0.5
            rho = rm * ci.get("coherence", 1.0) * (1.0 - ci.get("drift", 0.0))
            all_rho_effs.append(rho)
            session_chunks.append((sid, ci, rho))

    n = len(all_rho_effs)
    print("Total chunks: {}".format(n))

    # rho_eff の生分布
    rho_m = sum(all_rho_effs) / n
    rho_v = sum((r - rho_m) ** 2 for r in all_rho_effs) / n
    rho_min = min(all_rho_effs)
    rho_max = max(all_rho_effs)
    print("rho_eff: mean={:.4f} var={:.6f} range=[{:.4f}, {:.4f}]".format(
        rho_m, rho_v, rho_min, rho_max))

    # 3 つの正規化を比較
    p_mm = calc_prec_minmax(all_rho_effs)
    p_qt = calc_prec_quantile(all_rho_effs)
    p_lg = calc_prec_log(all_rho_effs)

    methods = [
        ("v0.7 min-max", p_mm),
        ("v0.8 quantile", p_qt),
        ("log + min-max", p_lg),
    ]

    print("\n" + "=" * 60)
    print("{:20s} {:>8s} {:>8s} {:>8s}".format("Method", "mean", "var", "BC"))
    for name, vals in methods:
        m = sum(vals) / n
        v = sum((p - m) ** 2 for p in vals) / n
        bc = bimodality(vals)
        bimod = " BIMODAL" if bc > 0.555 else ""
        print("{:20s} {:8.4f} {:8.4f} {:8.4f}{}".format(name, m, v, bc, bimod))

    for name, vals in methods:
        print_hist(vals, name)

    # チャンク別詳細 (quantile vs min-max)
    print("\n\nChunk Detail (min-max -> quantile):")
    for i, (sid, ci, rho) in enumerate(session_chunks):
        dd = p_qt[i] - p_mm[i]
        ind = "UP" if dd > 0.05 else ("DN" if dd < -0.05 else "--")
        print("  {} c{:2d}: rho={:.4f} mm={:.3f} qt={:.3f} (d={:+.3f}) {}".format(
            sid[:8], ci["chunk_id"], rho, p_mm[i], p_qt[i], dd, ind))


if __name__ == "__main__":
    main()
