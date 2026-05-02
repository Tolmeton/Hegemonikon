#!/usr/bin/env python3
# PROOF: [L2/実験] <- VISION §17.6 方向A — メトリック閉包
"""
Energy Distance のメトリック閉包 (Metric Closure)

理論:
  任意の対称・非負関数 d(x,y) に対して、最短経路距離
    d*(x,y) = min_{x=z0,...,zk=y} Σ d(zi, zi+1)
  は d* <= d を満たす最大のメトリック。

  Lawvere 距離空間 ([0,∞]-豊穣圏) の定義:
    d(x,x) = 0, d(x,z) <= d(x,y) + d(y,z)
  まさに最短経路メトリック化で得られる構造。

  → Floyd-Warshall は O(n^3) で最短経路メトリックを計算
  → 変換関数で「ほぼメトリック」にした後、残違反を FW で修正
  → 歪みの大きさ = 変換の品質指標
"""
import math
import os
import pickle
import time
from collections import defaultdict
from itertools import combinations

_HGK_ROOT = os.path.expanduser(
    "~/Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
)


def l1_distance(a, b):
    return sum(abs(a[i] - b[i]) for i in range(len(a)))


def pairwise_distances(group):
    dists = []
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            dists.append(l1_distance(group[i], group[j]))
    return dists


def cross_distances(group_a, group_b):
    dists = []
    for a in group_a:
        for b in group_b:
            dists.append(l1_distance(a, b))
    return dists


def mean(vals):
    return sum(vals) / len(vals) if vals else 0.0


def energy_distance(feats_p, feats_q):
    cross = mean(cross_distances(feats_p, feats_q))
    wp = mean(pairwise_distances(feats_p)) if len(feats_p) >= 2 else 0.0
    wq = mean(pairwise_distances(feats_q)) if len(feats_q) >= 2 else 0.0
    return 2 * cross - wp - wq


def classify_file(fname):
    if fname.startswith('test_'):
        return 'test'
    elif fname in ('cli.py', 'main.py', '__main__.py'):
        return 'cli'
    return 'impl'


def floyd_warshall(names, dist_matrix):
    """Floyd-Warshall 最短経路メトリック化"""
    n = len(names)
    idx = {name: i for i, name in enumerate(names)}

    # 距離行列を 2D リストに変換
    d = [[float('inf')] * n for _ in range(n)]
    for i in range(n):
        d[i][i] = 0.0
    for (a, b), val in dist_matrix.items():
        i, j = idx[a], idx[b]
        d[i][j] = val

    # Floyd-Warshall
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if d[i][k] + d[k][j] < d[i][j]:
                    d[i][j] = d[i][k] + d[k][j]

    # 名前付き辞書に戻す
    result = {}
    for i in range(n):
        for j in range(n):
            result[(names[i], names[j])] = d[i][j]
    return result


def check_triangle(names, dist_map):
    violations = 0
    total = 0
    for a, b, c in combinations(names, 3):
        total += 3
        for d1, d2, d3 in [
            (dist_map[(a, c)], dist_map[(a, b)], dist_map[(b, c)]),
            (dist_map[(a, b)], dist_map[(a, c)], dist_map[(c, b)]),
            (dist_map[(b, c)], dist_map[(b, a)], dist_map[(a, c)]),
        ]:
            if d1 > d2 + d3 + 1e-9:
                violations += 1
    return total, violations


def main():
    print("=" * 70)
    print("方向 A: メトリック閉包 (Floyd-Warshall)")
    print("=" * 70)

    # データ読み込み
    pkl_path = os.path.join(_HGK_ROOT, "30_記憶｜Mneme", "02_索引｜Index", "code.pkl")
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)
    metas = list(data.get("metadata", {}).values())

    entries = []
    for m in metas:
        if not isinstance(m, dict):
            continue
        feats = m.get("ccl_features")
        if not feats or len(feats) != 43:
            continue
        fname = os.path.basename(str(m.get("file_path", "")))
        entries.append({"file": fname, "features": list(feats), "category": classify_file(fname)})
    print(f"Valid entries: {len(entries)}")

    # ファイルグルーピング
    by_file = defaultdict(list)
    for e in entries:
        by_file[e["file"]].append(e)
    groups = {f: ents for f, ents in by_file.items() if len(ents) >= 5}

    for top_k in [12, 20]:
        print(f"\n{'=' * 70}")
        print(f"Top-{top_k} ファイルでの検証")
        print(f"{'=' * 70}")

        top_files = dict(sorted(groups.items(), key=lambda x: -len(x[1]))[:top_k])
        names = list(top_files.keys())
        sample_size = 20

        # ED 行列
        ed_raw = {}
        for f in names:
            ed_raw[(f, f)] = 0.0
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                f1, f2 = names[i], names[j]
                feats1 = [e["features"] for e in top_files[f1][:sample_size]]
                feats2 = [e["features"] for e in top_files[f2][:sample_size]]
                ed = energy_distance(feats1, feats2)
                ed_raw[(f1, f2)] = ed
                ed_raw[(f2, f1)] = ed

        # === ステップ 1: 変換関数適用 ===
        transforms = {
            "log(1+cl)": lambda x: math.log1p(max(0.0, x)),
            "sqrt(cl)":  lambda x: math.sqrt(max(0.0, x)),
            "cl^0.25":   lambda x: max(0.0, x) ** 0.25,
        }

        for tname, tfunc in transforms.items():
            # 変換適用
            d_pre = {}
            for (a, b), v in ed_raw.items():
                d_pre[(a, b)] = tfunc(v)

            total, v_pre = check_triangle(names, d_pre)
            print(f"\n  [{tname}] 変換後: {total-v_pre}/{total} 成立 ({v_pre} 違反)")

            # === ステップ 2: Floyd-Warshall メトリック化 ===
            d_post = floyd_warshall(names, d_pre)

            total, v_post = check_triangle(names, d_post)
            print(f"  [{tname}] FW 後:  {total-v_post}/{total} 成立 ({v_post} 違反)")

            # === ステップ 3: 歪み分析 ===
            distortions = []
            for f1, f2 in combinations(names, 2):
                pre = d_pre[(f1, f2)]
                post = d_post[(f1, f2)]
                if pre > 0:
                    distortions.append({
                        "pair": (f1, f2),
                        "pre": pre, "post": post,
                        "ratio": post / pre,
                        "abs_diff": abs(pre - post),
                    })

            ratios = [d["ratio"] for d in distortions]
            abs_diffs = [d["abs_diff"] for d in distortions]
            unchanged = sum(1 for r in ratios if abs(r - 1.0) < 1e-6)

            print(f"  歪み統計:")
            print(f"    変更ゼロ: {unchanged}/{len(ratios)} ペア")
            print(f"    比率 range: [{min(ratios):.6f}, {max(ratios):.6f}]")
            print(f"    絶対差 mean: {mean(abs_diffs):.6f}, max: {max(abs_diffs):.6f}")

            # 最も歪んだペア
            worst = sorted(distortions, key=lambda d: d["abs_diff"], reverse=True)[:5]
            if worst and worst[0]["abs_diff"] > 1e-6:
                print(f"    最大歪みペア:")
                for w in worst:
                    if w["abs_diff"] > 1e-6:
                        c1 = top_files[w["pair"][0]][0]["category"]
                        c2 = top_files[w["pair"][1]][0]["category"]
                        print(f"      {w['pair'][0]:30s}({c1}) - {w['pair'][1]:30s}({c2}): "
                              f"{w['pre']:.4f} → {w['post']:.4f} (ratio={w['ratio']:.4f})")

            # === ステップ 4: [0,1] 正規化 ===
            post_vals = [d_post[(f1, f2)] for f1, f2 in combinations(names, 2)]
            d_max = max(post_vals) if post_vals else 1.0

            # d/(1+d) で [0,1] 化
            d_01 = {}
            for (a, b), v in d_post.items():
                d_01[(a, b)] = v / (1 + v)

            total, v_01 = check_triangle(names, d_01)
            vals_01 = [d_01[(f1, f2)] for f1, f2 in combinations(names, 2)]
            print(f"  [0,1] d/(1+d): [{min(vals_01):.4f}, {max(vals_01):.4f}]  "
                  f"{total-v_01}/{total} ({v_01} 違反)")

            # カテゴリ別の距離分布
            test_test = []
            impl_impl = []
            test_impl = []
            for f1, f2 in combinations(names, 2):
                c1 = top_files[f1][0]["category"]
                c2 = top_files[f2][0]["category"]
                v = d_01[(f1, f2)]
                if c1 == "test" and c2 == "test":
                    test_test.append(v)
                elif c1 == "impl" and c2 == "impl":
                    impl_impl.append(v)
                else:
                    test_impl.append(v)

            if test_test and impl_impl:
                print(f"  カテゴリ距離 [0,1]:")
                print(f"    test↔test: {mean(test_test):.4f} (n={len(test_test)})")
                print(f"    impl↔impl: {mean(impl_impl):.4f} (n={len(impl_impl)})")
                print(f"    test↔impl: {mean(test_impl):.4f} (n={len(test_impl)})")

    print("\n[完了]")


if __name__ == "__main__":
    main()
