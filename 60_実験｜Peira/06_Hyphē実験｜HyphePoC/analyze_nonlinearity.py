#!/usr/bin/env python3
"""R² 非線形成分の分析スクリプト

ev proxy 検証 (R²=0.656) の残差35%がどこから来るかを特定する。

分析内容:
  1. 誤差と各特徴量の Pearson 相関
  2. パーセンタイル別の特性比較
  3. 高誤差ペア (P95) の詳細
  4. 非線形性の方向 (s_merged vs s_weighted)
"""

import json
import math
import pickle
import sys
from pathlib import Path

# パス設定
HGK_ROOT = Path("/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon")
MEKHANE_SRC = HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"
EXPERIMENT_DIR = HGK_ROOT / "60_実験｜Peira" / "06_Hyphē実験｜HyphePoC"
CACHE_FILE = EXPERIMENT_DIR / "embedding_cache.pkl"

sys.path.insert(0, str(MEKHANE_SRC))
sys.path.insert(0, str(EXPERIMENT_DIR))

from hyphe_chunker import (
    Step,
    _cosine_similarity,
    _l2_normalize,
    chunk_session,
)


def chunk_centroid(normed, indices):
    """L2正規化済みembeddingからcentroidを計算。"""
    if not indices:
        return []
    dim = len(normed[0])
    c = [0.0] * dim
    for i in indices:
        for d in range(dim):
            c[d] += normed[i][d]
    n = len(indices)
    return _l2_normalize([x / n for x in c])


def pearson(xs, ys):
    """2変数のPearson相関係数。"""
    n = len(xs)
    if n < 3:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / n
    vx = sum((x - mx) ** 2 for x in xs) / n
    vy = sum((y - my) ** 2 for y in ys) / n
    d = math.sqrt(vx * vy)
    return cov / d if d > 1e-12 else 0.0


def main():
    # キャッシュ読み込み
    with open(CACHE_FILE, "rb") as f:
        cache = pickle.load(f)

    # 全ペアを再計算して詳細データを収集
    records = []

    for sid, data in sorted(cache.items()):
        embs = data["embeddings"]
        n = len(embs)
        if n < 6:
            continue

        normed = [_l2_normalize(e) for e in embs]
        dummy = [Step(index=i, text=f"s{i}") for i in range(n)]
        result = chunk_session(dummy, embs, tau=0.70)
        chunks = result.chunks

        if len(chunks) < 2:
            continue

        for ci in range(len(chunks) - 1):
            c_a = chunks[ci]
            c_b = chunks[ci + 1]
            a_steps = [s.index for s in c_a.steps]
            b_steps = [s.index for s in c_b.steps]
            merged = a_steps + b_steps
            merged_set = set(merged)

            cent_a = chunk_centroid(normed, a_steps)
            cent_b = chunk_centroid(normed, b_steps)
            cent_m = chunk_centroid(normed, merged)

            total = len(a_steps) + len(b_steps)
            w_a = len(a_steps) / total
            w_b = len(b_steps) / total
            size_ratio = min(len(a_steps), len(b_steps)) / max(
                len(a_steps), len(b_steps)
            )

            # 境界の similarity
            boundary_sim = _cosine_similarity(
                normed[a_steps[-1]], normed[b_steps[0]]
            )

            # centroid 間距離
            inter_centroid_sim = _cosine_similarity(cent_a, cent_b)

            # チャンク内 coherence
            coh_a = (
                sum(_cosine_similarity(normed[i], cent_a) for i in a_steps)
                / len(a_steps)
            )
            coh_b = (
                sum(_cosine_similarity(normed[i], cent_b) for i in b_steps)
                / len(b_steps)
            )
            coh_diff = abs(coh_a - coh_b)

            query_indices = [i for i in range(n) if i not in merged_set]

            for qi in query_indices:
                q = normed[qi]

                s_m = _cosine_similarity(q, cent_m)
                s_a = _cosine_similarity(q, cent_a)
                s_b = _cosine_similarity(q, cent_b)
                s_w = w_a * s_a + w_b * s_b
                error = abs(s_m - s_w)
                signed_error = s_m - s_w

                # クエリとチャンクの距離
                min_dist_a = min(abs(qi - i) for i in a_steps)
                min_dist_b = min(abs(qi - i) for i in b_steps)
                min_dist = min(min_dist_a, min_dist_b)

                records.append(
                    {
                        "sid": sid,
                        "qi": qi,
                        "ci": ci,
                        "error": error,
                        "signed_error": signed_error,
                        "s_merged": s_m,
                        "s_weighted": s_w,
                        "s_a": s_a,
                        "s_b": s_b,
                        "w_a": w_a,
                        "w_b": w_b,
                        "size_a": len(a_steps),
                        "size_b": len(b_steps),
                        "size_ratio": size_ratio,
                        "boundary_sim": boundary_sim,
                        "inter_centroid_sim": inter_centroid_sim,
                        "query_dist": min_dist,
                        "coh_diff": coh_diff,
                        "abs_sa_sb": abs(s_a - s_b),
                        "n_steps": n,
                    }
                )

    n = len(records)
    print(f"Total records: {n}")
    print()

    # === 分析1: 誤差と各特徴量の相関 ===
    errors = [r["error"] for r in records]
    signed_errors = [r["signed_error"] for r in records]
    features = {
        "size_ratio": ([r["size_ratio"] for r in records], "チャンクサイズの均衡度"),
        "boundary_sim": ([r["boundary_sim"] for r in records], "分割境界の類似度"),
        "inter_centroid_sim": (
            [r["inter_centroid_sim"] for r in records],
            "centroid 間の類似度",
        ),
        "query_dist": ([r["query_dist"] for r in records], "クエリのチャンクからの距離"),
        "w_a": ([r["w_a"] for r in records], "チャンクA の重み"),
        "size_a+b": (
            [r["size_a"] + r["size_b"] for r in records],
            "結合チャンクの総サイズ",
        ),
        "s_merged": ([r["s_merged"] for r in records], "ev(q, c_merged)"),
        "s_a": ([r["s_a"] for r in records], "ev(q, c_a)"),
        "s_b": ([r["s_b"] for r in records], "ev(q, c_b)"),
        "|s_a - s_b|": (
            [r["abs_sa_sb"] for r in records],
            "スコア差 (チャンク間の非対称性)",
        ),
        "coh_diff": ([r["coh_diff"] for r in records], "coherence の差 |coh_a - coh_b|"),
    }

    print("=== 分析1: |誤差| と特徴量の Pearson 相関 ===")
    print(f'{"Feature":<25} {"r(|err|)":>9} {"r(sign)":>9}  意味')
    print("-" * 85)
    sorted_feats = sorted(
        features.items(),
        key=lambda x: abs(pearson(errors, x[1][0])),
        reverse=True,
    )
    for name, (vals, meaning) in sorted_feats:
        r_abs = pearson(errors, vals)
        r_sign = pearson(signed_errors, vals)
        print(f"{name:<25} {r_abs:>+9.4f} {r_sign:>+9.4f}  {meaning}")

    # === 分析2: パーセンタイル別の特性 ===
    print()
    print("=== 分析2: 誤差パーセンタイル別の特性 ===")
    sorted_records = sorted(records, key=lambda r: r["error"])
    bins = [
        ("P0-25 低誤差", sorted_records[: n // 4]),
        ("P25-50", sorted_records[n // 4 : n // 2]),
        ("P50-75", sorted_records[n // 2 : 3 * n // 4]),
        ("P75-100 高誤差", sorted_records[3 * n // 4 :]),
    ]

    print(
        f'{"Bin":<18} {"N":>5} {"MeanErr":>9} {"SzRat":>7} {"BdySim":>7} {"ICS":>7} '
        f'{"QDist":>6} {"|sa-sb|":>8} {"cohDf":>7} {"w_a":>6}'
    )
    print("-" * 95)
    for bname, recs in bins:
        me = sum(r["error"] for r in recs) / len(recs)
        sr = sum(r["size_ratio"] for r in recs) / len(recs)
        bs = sum(r["boundary_sim"] for r in recs) / len(recs)
        ic = sum(r["inter_centroid_sim"] for r in recs) / len(recs)
        qd = sum(r["query_dist"] for r in recs) / len(recs)
        sd = sum(r["abs_sa_sb"] for r in recs) / len(recs)
        cd = sum(r["coh_diff"] for r in recs) / len(recs)
        wa = sum(r["w_a"] for r in recs) / len(recs)
        print(
            f"{bname:<18} {len(recs):>5} {me:>9.5f} {sr:>7.3f} {bs:>7.4f} "
            f"{ic:>7.4f} {qd:>6.1f} {sd:>8.5f} {cd:>7.4f} {wa:>6.3f}"
        )

    # === 分析3: 高誤差ペア (P95+) の詳細 ===
    print()
    print("=== 分析3: 高誤差ペア (P95+) の詳細 ===")
    top5 = sorted_records[int(n * 0.95) :]
    print(f"P95 閾値: err >= {top5[0]['error']:.5f}, N={len(top5)}")
    print(
        f'{"Session":<12} {"qi":>4} {"ci":>3} {"error":>8} {"s_m":>7} '
        f'{"s_w":>7} {"|sa-sb|":>8} {"szA+B":>6} {"ratio":>6} {"bdySim":>7} {"ics":>7}'
    )
    for r in top5[:20]:
        print(
            f'{r["sid"]:<12} {r["qi"]:>4} {r["ci"]:>3} {r["error"]:>8.5f} '
            f'{r["s_merged"]:>7.4f} {r["s_weighted"]:>7.4f} {r["abs_sa_sb"]:>8.5f} '
            f'{r["size_a"]+r["size_b"]:>6} {r["size_ratio"]:>6.3f} '
            f'{r["boundary_sim"]:>7.4f} {r["inter_centroid_sim"]:>7.4f}'
        )

    # === 分析4: 非線形性の方向 ===
    print()
    print("=== 分析4: 非線形性の方向 ===")
    over = sum(1 for r in records if r["signed_error"] > 0)
    under = sum(1 for r in records if r["signed_error"] < 0)
    print(f"s_merged > s_weighted (正): {over} ({100*over/n:.1f}%)")
    print(f"s_merged < s_weighted (負): {under} ({100*under/n:.1f}%)")
    mean_bias = sum(r["signed_error"] for r in records) / n
    std_bias = math.sqrt(
        sum((r["signed_error"] - mean_bias) ** 2 for r in records) / n
    )
    print(f"平均バイアス: {mean_bias:+.6f} ± {std_bias:.6f}")

    # === 分析5: 2次的寄与の推定 ===
    # ev(q, c_m) と s_weighted の差 = 非線形の寄与
    # これが (s_a - s_b)^2 に比例するか検証 (2次項)
    print()
    print("=== 分析5: 2次項の検証 ===")
    # signed_error vs (s_a - s_b)^2
    sq_diff = [(r["s_a"] - r["s_b"]) ** 2 for r in records]
    r_sq = pearson(signed_errors, sq_diff)
    print(f"signed_error vs (s_a - s_b)²: r = {r_sq:+.4f}")

    # signed_error vs (w_a - 0.5)*(s_a - s_b)
    asym = [(r["w_a"] - 0.5) * (r["s_a"] - r["s_b"]) for r in records]
    r_asym = pearson(signed_errors, asym)
    print(f"signed_error vs (w_a - 0.5)·(s_a - s_b): r = {r_asym:+.4f}")

    # signed_error vs w_a*w_b*(s_a - s_b)^2
    quad = [r["w_a"] * r["w_b"] * (r["s_a"] - r["s_b"]) ** 2 for r in records]
    r_quad = pearson(signed_errors, quad)
    print(f"signed_error vs w_a·w_b·(s_a - s_b)²: r = {r_quad:+.4f}")

    # 補正 R² テスト:
    # s_merged ≈ w_a·s_a + w_b·s_b + β·(s_a - s_b)²
    # ← centroid の cos_sim の非線形成分
    print()
    print("=== 分析6: 補正モデルの R² ===")
    s_merged_vals = [r["s_merged"] for r in records]
    s_weighted_vals = [r["s_weighted"] for r in records]
    mean_sm = sum(s_merged_vals) / n

    # 基本モデル R²
    ss_tot = sum((sm - mean_sm) ** 2 for sm in s_merged_vals)
    ss_res_linear = sum(
        (sm - sw) ** 2 for sm, sw in zip(s_merged_vals, s_weighted_vals)
    )
    r2_linear = 1 - ss_res_linear / ss_tot if ss_tot > 0 else 0

    # 2次補正モデル: s_merged ≈ s_weighted + β·w_a·w_b·(s_a-s_b)²
    # βの最適推定: β = Cov(residual, predictor) / Var(predictor)
    residuals = [sm - sw for sm, sw in zip(s_merged_vals, s_weighted_vals)]
    predictors = [
        r["w_a"] * r["w_b"] * (r["s_a"] - r["s_b"]) ** 2 for r in records
    ]
    mean_r = sum(residuals) / n
    mean_p = sum(predictors) / n
    cov_rp = sum((r - mean_r) * (p - mean_p) for r, p in zip(residuals, predictors)) / n
    var_p = sum((p - mean_p) ** 2 for p in predictors) / n
    beta = cov_rp / var_p if var_p > 1e-12 else 0

    s_corrected = [sw + beta * p for sw, p in zip(s_weighted_vals, predictors)]
    ss_res_quad = sum(
        (sm - sc) ** 2 for sm, sc in zip(s_merged_vals, s_corrected)
    )
    r2_quad = 1 - ss_res_quad / ss_tot if ss_tot > 0 else 0

    # 3次: + γ·(w_a - 0.5)·(s_a - s_b)
    predictors2 = [(r["w_a"] - 0.5) * (r["s_a"] - r["s_b"]) for r in records]
    residuals2 = [sm - sc for sm, sc in zip(s_merged_vals, s_corrected)]
    mean_r2 = sum(residuals2) / n
    mean_p2 = sum(predictors2) / n
    cov_rp2 = (
        sum((r - mean_r2) * (p - mean_p2) for r, p in zip(residuals2, predictors2))
        / n
    )
    var_p2 = sum((p - mean_p2) ** 2 for p in predictors2) / n
    gamma = cov_rp2 / var_p2 if var_p2 > 1e-12 else 0

    s_corrected2 = [
        sc + gamma * p2 for sc, p2 in zip(s_corrected, predictors2)
    ]
    ss_res_full = sum(
        (sm - sc2) ** 2 for sm, sc2 in zip(s_merged_vals, s_corrected2)
    )
    r2_full = 1 - ss_res_full / ss_tot if ss_tot > 0 else 0

    print(f"線形モデル R² (s_w only):            {r2_linear:.4f}")
    print(f"2次補正 R² (+β·w_a·w_b·Δ²):          {r2_quad:.4f}  β={beta:+.4f}")
    print(f"3次補正 R² (+γ·(w-0.5)·Δ):           {r2_full:.4f}  γ={gamma:+.4f}")
    print(f"R² 増分 (線形→2次):                  {r2_quad - r2_linear:+.4f}")
    print(f"R² 増分 (2次→3次):                   {r2_full - r2_quad:+.4f}")

    # JSON 保存
    output = {
        "n_records": n,
        "correlations": {
            name: {"r_abs_error": pearson(errors, vals), "r_signed_error": pearson(signed_errors, vals)}
            for name, (vals, _) in features.items()
        },
        "direction": {
            "over_count": over,
            "under_count": under,
            "mean_bias": mean_bias,
            "std_bias": std_bias,
        },
        "quadratic_analysis": {
            "r_signed_vs_sq_diff": r_sq,
            "r_signed_vs_asymmetry": r_asym,
            "r_signed_vs_quad": r_quad,
            "beta_coefficient": beta,
            "gamma_coefficient": gamma,
        },
        "r_squared": {
            "linear": r2_linear,
            "quadratic_corrected": r2_quad,
            "full_corrected": r2_full,
        },
    }

    out_path = EXPERIMENT_DIR / "results_nonlinearity_analysis.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n結果を {out_path.name} に保存")


if __name__ == "__main__":
    main()
