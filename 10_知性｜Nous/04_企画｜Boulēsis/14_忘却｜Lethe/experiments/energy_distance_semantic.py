#!/usr/bin/env python3
# PROOF: [L2/実験] <- VISION §17.8-§17.12 方向A — 意味的妥当性検証 + 縮退解消
"""
メトリック閉包距離の意味的妥当性検証

問い: FW 距離は構造的類似度を正しく反映しているか？

検証方法:
  1. 特徴量 cosine 類似度との順位相関 (Spearman ρ)
  2. 最近傍分析 (各ファイルの NN が直感的に妥当か)
  3. test↔対応impl ペアの距離 vs 無関連ペアの距離
  4. Stress 分析 (MDS の distortion)
  5. カテゴリ内/間の距離分布の分離度 (Mann-Whitney U)
"""
import math
import os
import pickle
from collections import defaultdict
from itertools import combinations

import numpy as np
from scipy import stats

_HGK_ROOT = os.path.expanduser(
    "~/Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
)


def l1_distance(a, b):
    return sum(abs(a[i] - b[i]) for i in range(len(a)))


def cosine_similarity(a, b):
    """ファイル代表ベクトル (平均) 間の cosine 類似度"""
    dot = sum(a[i] * b[i] for i in range(len(a)))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return dot / (na * nb)


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
    n = len(names)
    idx = {name: i for i, name in enumerate(names)}
    d = [[float('inf')] * n for _ in range(n)]
    for i in range(n):
        d[i][i] = 0.0
    for (a, b), val in dist_matrix.items():
        i, j = idx[a], idx[b]
        d[i][j] = val
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if d[i][k] + d[k][j] < d[i][j]:
                    d[i][j] = d[i][k] + d[k][j]
    result = {}
    for i in range(n):
        for j in range(n):
            result[(names[i], names[j])] = d[i][j]
    return result


def main():
    print("=" * 70)
    print("方向 A: 意味的妥当性検証")
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
        func_name = m.get("name", "")
        code_type = m.get("code_type", "")
        entries.append({
            "file": fname, "features": list(feats),
            "category": classify_file(fname),
            "name": func_name, "code_type": code_type,
        })
    print(f"エントリ数: {len(entries)}")

    # ファイルグルーピング
    by_file = defaultdict(list)
    for e in entries:
        by_file[e["file"]].append(e)
    groups = {f: ents for f, ents in by_file.items() if len(ents) >= 5}

    top_k = 20
    top_files = dict(sorted(groups.items(), key=lambda x: -len(x[1]))[:top_k])
    names = list(top_files.keys())
    sample_size = 20

    # ====================================================================
    # 1. ED → cl^0.25 → FW → d/(1+d) パイプライン
    # ====================================================================
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

    # ====================================================================
    # 2. ファイル代表ベクトルの計算 (平均特徴量)
    # ====================================================================
    centroids = {}
    for f in names:
        feats = [e["features"] for e in top_files[f][:sample_size]]
        dim = 43
        centroid = [0.0] * dim
        for feat in feats:
            for d in range(dim):
                centroid[d] += feat[d]
        for d in range(dim):
            centroid[d] /= len(feats)
        centroids[f] = centroid

    # §17.12 centroid L1 フォールバック
    # 負 ED → centroid 間 L1 距離で代替 (α 正規化)
    centroid_l1_dists = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            f1, f2 = names[i], names[j]
            cl1 = l1_distance(centroids[f1], centroids[f2])
            centroid_l1_dists[(f1, f2)] = cl1
            centroid_l1_dists[(f2, f1)] = cl1

    # α 正規化: ED>0 の中央値 / L1 の中央値
    ed_pos = [v for (a, b), v in ed_raw.items() if a < b and v > 0]
    cl1_vals = [v for (a, b), v in centroid_l1_dists.items() if a < b]
    alpha = (np.median(ed_pos) / np.median(cl1_vals)) if cl1_vals and ed_pos else 1.0

    neg_count = sum(1 for (a, b), v in ed_raw.items() if a < b and v < -0.01)
    print(f"\n負 ED ペア数: {neg_count}")
    print(f"α 正規化係数: {alpha:.4f}")

    ed_fixed = {}
    for (a, b), v in ed_raw.items():
        if a == b:
            ed_fixed[(a, b)] = 0.0
        elif v <= 0:
            # フォールバック: centroid L1 × α
            cl1 = centroid_l1_dists.get((a, b), 0.0)
            ed_fixed[(a, b)] = alpha * cl1
        else:
            ed_fixed[(a, b)] = v

    # cl^0.25 変換 (フォールバック後)
    d_pre = {}
    for (a, b), v in ed_fixed.items():
        d_pre[(a, b)] = max(0.0, v) ** 0.25

    # Floyd-Warshall
    d_fw = floyd_warshall(names, d_pre)

    # d/(1+d) 正規化
    d_01 = {}
    for (a, b), v in d_fw.items():
        d_01[(a, b)] = v / (1 + v)

    # ====================================================================
    # タスク 1: Spearman 順位相関 (FW距離 vs cosine 非類似度)
    # ====================================================================
    print("\n" + "=" * 70)
    print("タスク 1: Spearman 順位相関")
    print("=" * 70)

    fw_dists = []
    cos_dists = []  # 1 - cosine = 非類似度
    raw_eds = []
    pairs_list = []

    for f1, f2 in combinations(names, 2):
        fw_dists.append(d_01[(f1, f2)])
        cos_sim = cosine_similarity(centroids[f1], centroids[f2])
        cos_dists.append(1.0 - cos_sim)
        raw_eds.append(ed_raw[(f1, f2)])
        pairs_list.append((f1, f2))

    # Spearman
    rho_fw_cos, p_fw_cos = stats.spearmanr(fw_dists, cos_dists)
    rho_raw_cos, p_raw_cos = stats.spearmanr(raw_eds, cos_dists)

    print(f"  FW距離[0,1] vs cosine非類似度: ρ={rho_fw_cos:.4f}, p={p_fw_cos:.2e}")
    print(f"  raw ED vs cosine非類似度:       ρ={rho_raw_cos:.4f}, p={p_raw_cos:.2e}")

    # Pearson (線形相関)
    r_fw_cos, p_r = stats.pearsonr(fw_dists, cos_dists)
    print(f"  FW距離 vs cosine非類似度 (Pearson): r={r_fw_cos:.4f}, p={p_r:.2e}")

    # ====================================================================
    # タスク 2: 最近傍分析
    # ====================================================================
    print("\n" + "=" * 70)
    print("タスク 2: 最近傍分析")
    print("=" * 70)

    # カテゴリ情報
    cat_map = {f: top_files[f][0]["category"] for f in names}

    for f in names:
        # FW 距離でソート
        dists_to_f = [(f2, d_01[(f, f2)]) for f2 in names if f2 != f]
        dists_to_f.sort(key=lambda x: x[1])

        nn3 = dists_to_f[:3]
        farthest = dists_to_f[-1]

        cat = cat_map[f]
        nn_str = ", ".join(f"{n}({cat_map[n]})={d:.3f}" for n, d in nn3)
        print(f"  {f:30s}({cat}) → NN: {nn_str}")

    # ====================================================================
    # タスク 3: test↔対応impl ペアの距離 vs 無関連ペア
    # ====================================================================
    print("\n" + "=" * 70)
    print("タスク 3: test↔対応impl ペアの距離")
    print("=" * 70)

    # test_X.py → X.py の対応を探す
    test_impl_pairs = []
    for f in names:
        if f.startswith("test_"):
            impl_name = f[5:]  # test_X.py → X.py
            if impl_name in top_files:
                d_val = d_01[(f, impl_name)]
                test_impl_pairs.append((f, impl_name, d_val))
                print(f"  対応ペア: {f} ↔ {impl_name}: d={d_val:.4f}")

    if test_impl_pairs:
        paired_dists = [p[2] for p in test_impl_pairs]
        # 無関連ペア (test↔impl で対応しないもの)
        unrelated_dists = []
        paired_set = set()
        for t, i, _ in test_impl_pairs:
            paired_set.add((t, i))
            paired_set.add((i, t))

        for f1, f2 in combinations(names, 2):
            c1, c2 = cat_map[f1], cat_map[f2]
            if (c1 == "test" and c2 == "impl") or (c1 == "impl" and c2 == "test"):
                if (f1, f2) not in paired_set:
                    unrelated_dists.append(d_01[(f1, f2)])

        if unrelated_dists:
            print(f"\n  対応ペア平均距離:   {mean(paired_dists):.4f} (n={len(paired_dists)})")
            print(f"  無関連ペア平均距離: {mean(unrelated_dists):.4f} (n={len(unrelated_dists)})")

            # Mann-Whitney U
            U, p = stats.mannwhitneyu(paired_dists, unrelated_dists, alternative='less')
            print(f"  Mann-Whitney U: U={U:.1f}, p={p:.4f} (対応ペア < 無関連ペア?)")

            # Cohen's d
            d_cohen = (mean(unrelated_dists) - mean(paired_dists)) / (
                np.std(paired_dists + unrelated_dists) if len(paired_dists) > 1 else 1.0)
            print(f"  Cohen's d: {d_cohen:.4f}")
    else:
        print("  対応ペア (test_X.py → X.py) が見つからなかった")

    # ====================================================================
    # タスク 4: カテゴリ内/間 距離分布の分離度
    # ====================================================================
    print("\n" + "=" * 70)
    print("タスク 4: カテゴリ内/間 距離分布")
    print("=" * 70)

    within_cat = []
    between_cat = []
    for f1, f2 in combinations(names, 2):
        c1, c2 = cat_map[f1], cat_map[f2]
        v = d_01[(f1, f2)]
        if c1 == c2:
            within_cat.append(v)
        else:
            between_cat.append(v)

    print(f"  カテゴリ内 距離: μ={mean(within_cat):.4f}, σ={np.std(within_cat):.4f} (n={len(within_cat)})")
    print(f"  カテゴリ間 距離: μ={mean(between_cat):.4f}, σ={np.std(between_cat):.4f} (n={len(between_cat)})")

    # Mann-Whitney U
    U, p = stats.mannwhitneyu(within_cat, between_cat, alternative='less')
    print(f"  Mann-Whitney U: U={U:.1f}, p={p:.4f} (カテゴリ内 < カテゴリ間?)")

    # Cohen's d
    all_vals = within_cat + between_cat
    d_cohen = (mean(between_cat) - mean(within_cat)) / np.std(all_vals) if np.std(all_vals) > 0 else 0
    print(f"  Cohen's d: {d_cohen:.4f}")

    # ====================================================================
    # タスク 5: L1 特徴量距離との直接比較
    # ====================================================================
    print("\n" + "=" * 70)
    print("タスク 5: centroid L1 距離との相関")
    print("=" * 70)

    l1_dists = []
    for f1, f2 in combinations(names, 2):
        l1_dists.append(l1_distance(centroids[f1], centroids[f2]))

    rho_fw_l1, p_fw_l1 = stats.spearmanr(fw_dists, l1_dists)
    r_fw_l1, p_r_l1 = stats.pearsonr(fw_dists, l1_dists)
    print(f"  FW距離[0,1] vs centroid L1: Spearman ρ={rho_fw_l1:.4f} (p={p_fw_l1:.2e})")
    print(f"  FW距離[0,1] vs centroid L1: Pearson  r={r_fw_l1:.4f} (p={p_r_l1:.2e})")

    # raw ED vs centroid L1
    rho_raw_l1, p_raw_l1 = stats.spearmanr(raw_eds, l1_dists)
    print(f"  raw ED vs centroid L1: Spearman ρ={rho_raw_l1:.4f} (p={p_raw_l1:.2e})")

    # ====================================================================
    # タスク 6: 凝集度 (内部分散 vs 距離)
    # ====================================================================
    print("\n" + "=" * 70)
    print("タスク 6: ファイル内凝集度 vs FW 距離")
    print("=" * 70)

    intra_vars = []
    for f in names:
        feats = [e["features"] for e in top_files[f][:sample_size]]
        if len(feats) >= 2:
            pw_dists = pairwise_distances(feats)
            intra_vars.append((f, mean(pw_dists), len(feats)))
        else:
            intra_vars.append((f, 0.0, len(feats)))

    intra_vars.sort(key=lambda x: x[1])
    print(f"  {'ファイル':30s} {'内部距離':>10s} {'n':>5s}  {'カテゴリ':>6s}")
    print(f"  {'-'*30} {'-'*10} {'-'*5}  {'-'*6}")
    for f, var, n in intra_vars:
        print(f"  {f:30s} {var:10.2f} {n:5d}  {cat_map[f]:>6s}")

    # 凝集度と FW 距離の関係
    # ファイル内分散が大きい → 他ファイルとの距離が小さい？(境界がぼける)
    avg_fw_dists = []
    for f in names:
        avg_d = mean([d_01[(f, f2)] for f2 in names if f2 != f])
        avg_fw_dists.append(avg_d)

    intra_means = [iv[1] for iv in intra_vars]
    rho_intra, p_intra = stats.spearmanr(
        [iv[1] for iv in sorted(intra_vars, key=lambda x: x[0])],
        [mean([d_01[(f, f2)] for f2 in names if f2 != f])
         for f in sorted(names)]
    )
    print(f"\n  内部距離 vs 平均 FW 距離: Spearman ρ={rho_intra:.4f} (p={p_intra:.4f})")
    print(f"    → ρ>0: 分散が大きいファイルは他との距離も大きい (散在)")
    print(f"    → ρ<0: 分散が大きいファイルは他との距離が小さい (境界ぼけ)")

    # ====================================================================
    # サマリー
    # ====================================================================
    print("\n" + "=" * 70)
    print("サマリー")
    print("=" * 70)

    print(f"""
  距離のタイプ     | 相関指標
  FW[0,1] ↔ cos非類似 | Spearman ρ={rho_fw_cos:.3f}
  FW[0,1] ↔ L1 直接    | Spearman ρ={rho_fw_l1:.3f}
  raw ED  ↔ cos非類似  | Spearman ρ={rho_raw_cos:.3f}

  分離指標         |
  カテゴリ内/間     | Cohen's d={d_cohen:.3f}, p={p:.4f}
""")

    # 妥当性判定
    valid = True
    issues = []
    if rho_fw_cos < 0.5:
        issues.append(f"FW ↔ cosine 相関が低い (ρ={rho_fw_cos:.3f} < 0.5)")
        valid = False
    if d_cohen < 0.2:
        issues.append(f"カテゴリ分離が弱い (d={d_cohen:.3f} < 0.2)")
        valid = False

    if valid:
        print("  判定: ✅ 意味的妥当性を支持")
    else:
        print("  判定: ⚠️ 意味的妥当性に懸念あり")
        for iss in issues:
            print(f"    - {iss}")

    print("\n[完了]")


if __name__ == "__main__":
    main()
