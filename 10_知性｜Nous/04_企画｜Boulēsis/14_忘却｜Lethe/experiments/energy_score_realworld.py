#!/usr/bin/env python3
# PROOF: [L2/実験] <- VISION §17.3 方向C — Energy Score v3 改善版
"""
Energy Score 実世界実験 v3 — V1 メトリクス改善

v2 の問題:
  - E1' で fidelity = diversity が常に成立 (LOO + 同一分布の数学的性質)
  - Energy Score と Energy Distance の比較が不適切

v3 の改善:
  - V1: Fisher 判別比 = var_between / var_within で分離度を測定
  - 直接的な within diversity vs between distance の比較
  - 三角不等式: max(0, ED) 正規化の効果も検証
  - ファイル粒度: テスト/本体/CLI の分類を追加
"""
import math
import os
import pickle
import sys
import time
from collections import defaultdict
from itertools import combinations

_HGK_ROOT = os.path.expanduser(
    "~/Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
)


def l1_distance(a, b):
    """L1 距離"""
    return sum(abs(a[i] - b[i]) for i in range(len(a)))


def pairwise_distances(group):
    """グループ内の全ペア L1 距離"""
    dists = []
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            dists.append(l1_distance(group[i], group[j]))
    return dists


def cross_distances(group_a, group_b):
    """グループ間の全ペア L1 距離"""
    dists = []
    for a in group_a:
        for b in group_b:
            dists.append(l1_distance(a, b))
    return dists


def mean(vals):
    return sum(vals) / len(vals) if vals else 0.0


def var(vals):
    if len(vals) < 2:
        return 0.0
    m = mean(vals)
    return sum((x - m) ** 2 for x in vals) / (len(vals) - 1)


def energy_distance(feats_p, feats_q):
    """Energy Distance: 2*E[||X-Y||] - E[||X-X'||] - E[||Y-Y'||]"""
    cross = mean(cross_distances(feats_p, feats_q))
    wp = mean(pairwise_distances(feats_p)) if len(feats_p) >= 2 else 0.0
    wq = mean(pairwise_distances(feats_q)) if len(feats_q) >= 2 else 0.0
    return 2 * cross - wp - wq


def text_features_from_ccl(ccl_expr):
    """CCL 式のテキスト特徴量"""
    if not ccl_expr:
        return [0.0] * 8
    tokens = ccl_expr.replace('(', ' ').replace(')', ' ').replace('>>', ' ') \
        .replace('*', ' ').replace('%', ' ').replace('[', ' ').replace(']', ' ') \
        .replace('{', ' ').replace('}', ' ').replace('_', ' ').split()
    if not tokens:
        return [0.0] * 8
    return [
        float(len(tokens)), float(len(set(tokens))),
        sum(len(t) for t in tokens) / len(tokens), float(len(ccl_expr)),
        ccl_expr.count('>>'), ccl_expr.count('*'),
        ccl_expr.count('I:'), ccl_expr.count('.'),
    ]


def classify_file(fname):
    """ファイルを test/impl/cli に分類"""
    if fname.startswith('test_'):
        return 'test'
    elif fname in ('cli.py', 'main.py', '__main__.py'):
        return 'cli'
    else:
        return 'impl'


def main():
    print("=" * 60)
    print("Energy Score 実世界実験 v3 — V1 メトリクス改善版")
    print("=" * 60)

    # 1. データ読み込み
    pkl_path = os.path.join(_HGK_ROOT, "30_記憶｜Mneme", "02_索引｜Index", "code.pkl")
    print(f"\nLoading {pkl_path} ...")
    t0 = time.time()
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)
    raw_meta = data.get("metadata", {})
    metas = list(raw_meta.values())
    print(f"Loaded in {time.time()-t0:.1f}s — {len(metas)} entries")

    # 2. ccl_features を持つエントリ抽出
    entries = []
    for m in metas:
        if not isinstance(m, dict):
            continue
        feats = m.get("ccl_features")
        if not feats or len(feats) != 43:
            continue
        fpath = str(m.get("file_path", ""))
        fname = os.path.basename(fpath)
        entries.append({
            "file": fname, "file_path": fpath,
            "func": m.get("function_name", m.get("method_name", "")),
            "ccl": m.get("ccl_expr", ""),
            "features": list(feats),
            "code_type": m.get("code_type", ""),
            "category": classify_file(fname),
        })
    print(f"  Valid entries: {len(entries)}")

    # 3. 意味的グルーピング: テスト vs 本体 (ファイル粒度よりも高レベル)
    by_category = defaultdict(list)
    for e in entries:
        by_category[e["category"]].append(e)
    print(f"\n分類別:")
    for cat, ents in sorted(by_category.items()):
        print(f"  {cat}: {len(ents)} entries")

    # 4. ファイル単位グルーピング (5+ 関数)
    by_file = defaultdict(list)
    for e in entries:
        by_file[e["file"]].append(e)
    groups = {f: ents for f, ents in by_file.items() if len(ents) >= 5}
    print(f"\nFiles with 5+ functions: {len(groups)}")

    # 5. V1 改善: Fisher 判別比
    print("\n" + "=" * 60)
    print("[V1 改善] Fisher 判別比 — within vs between diversity")
    print("=" * 60)

    top20 = dict(sorted(groups.items(), key=lambda x: -len(x[1]))[:20])

    # Within diversity: 各ファイル内のペア間 L1 距離
    within_dists_all = []
    within_by_file = {}
    for fname, ents in top20.items():
        feats = [e["features"] for e in ents[:20]]
        pw = pairwise_distances(feats)
        within_by_file[fname] = mean(pw)
        within_dists_all.extend(pw)

    avg_within = mean(within_dists_all)
    print(f"  平均 within-file 距離: {avg_within:.2f}")

    # Between distance: 異なるファイル間のペア間距離
    top8 = dict(sorted(top20.items(), key=lambda x: -len(x[1]))[:8])
    top8_names = list(top8.keys())

    between_dists_all = []
    between_by_pair = {}
    for i in range(len(top8_names)):
        for j in range(i + 1, len(top8_names)):
            f1, f2 = top8_names[i], top8_names[j]
            feats1 = [e["features"] for e in top8[f1][:15]]
            feats2 = [e["features"] for e in top8[f2][:15]]
            cd = cross_distances(feats1, feats2)
            between_by_pair[(f1, f2)] = mean(cd)
            between_dists_all.extend(cd)

    avg_between = mean(between_dists_all)
    print(f"  平均 between-file 距離: {avg_between:.2f}")

    # Fisher 判別比
    fisher_ratio = avg_between / avg_within if avg_within > 0 else float('inf')
    print(f"  Fisher 比 (between/within): {fisher_ratio:.4f}")

    # Cohen's d (within vs between 直接比較)
    if within_dists_all and between_dists_all:
        m_w = mean(within_dists_all)
        m_b = mean(between_dists_all)
        v_w = var(within_dists_all)
        v_b = var(between_dists_all)
        pooled_sd = math.sqrt((v_w + v_b) / 2)
        cohens_d = abs(m_b - m_w) / pooled_sd if pooled_sd > 0 else 0.0
        print(f"  Cohen's d (距離分布): {cohens_d:.4f}")
    else:
        cohens_d = 0.0

    # テスト vs 本体の分離 (カテゴリレベル)
    print("\n  --- テスト vs 本体 の分離 ---")
    test_files = {f for f, ents in top20.items() if ents[0]["category"] == "test"}
    impl_files = {f for f, ents in top20.items() if ents[0]["category"] == "impl"}

    test_within = [within_by_file[f] for f in test_files if f in within_by_file]
    impl_within = [within_by_file[f] for f in impl_files if f in within_by_file]

    if test_within:
        print(f"  テストファイル内 平均距離: {mean(test_within):.2f} (n={len(test_within)})")
    if impl_within:
        print(f"  実装ファイル内 平均距離: {mean(impl_within):.2f} (n={len(impl_within)})")

    # テスト間 vs 本体間 vs テスト-本体間
    test_feats_all = []
    impl_feats_all = []
    for fname, ents in top20.items():
        fs = [e["features"] for e in ents[:15]]
        if ents[0]["category"] == "test":
            test_feats_all.extend(fs)
        elif ents[0]["category"] == "impl":
            impl_feats_all.extend(fs)

    if test_feats_all and impl_feats_all:
        # サンプリング (計算量制限)
        t_sample = test_feats_all[:50]
        i_sample = impl_feats_all[:50]

        within_test = pairwise_distances(t_sample)
        within_impl = pairwise_distances(i_sample)
        cross_ti = cross_distances(t_sample, i_sample)

        print(f"\n  テスト内 平均距離: {mean(within_test):.2f}")
        print(f"  本体内 平均距離: {mean(within_impl):.2f}")
        print(f"  テスト↔本体 平均距離: {mean(cross_ti):.2f}")

        # Cohen's d (テスト内 vs テスト↔本体)
        if within_test and cross_ti:
            m1 = mean(within_test)
            m2 = mean(cross_ti)
            v1 = var(within_test)
            v2 = var(cross_ti)
            ps = math.sqrt((v1 + v2) / 2)
            cat_d = abs(m2 - m1) / ps if ps > 0 else 0.0
            print(f"  Cohen's d (テスト内 vs テスト↔本体): {cat_d:.4f}")

    # ============================================================
    # E2': Energy Distance (正規化版)
    # ============================================================
    print("\n" + "=" * 60)
    print("[E2'] Energy Distance — 正規化版")
    print("=" * 60)

    ed_results = []
    for i in range(len(top8_names)):
        for j in range(i + 1, len(top8_names)):
            f1, f2 = top8_names[i], top8_names[j]
            feats1 = [e["features"] for e in top8[f1][:15]]
            feats2 = [e["features"] for e in top8[f2][:15]]

            ed_raw = energy_distance(feats1, feats2)

            # within diversity を分母にした正規化
            d_w1 = mean(pairwise_distances(feats1)) if len(feats1) >= 2 else 1.0
            d_w2 = mean(pairwise_distances(feats2)) if len(feats2) >= 2 else 1.0
            denom = (d_w1 + d_w2) / 2
            ed_norm = ed_raw / denom if denom > 0 else 0.0

            ed_results.append({
                "f1": f1, "f2": f2,
                "ed_raw": ed_raw, "ed_norm": ed_norm,
                "ed_clamp": max(0.0, ed_raw),
            })
            cat1 = top8[f1][0]["category"]
            cat2 = top8[f2][0]["category"]
            print(f"  {f1:30s}({cat1}) vs {f2:30s}({cat2}) | raw={ed_raw:7.2f} norm={ed_norm:.4f}")

    # 三角不等式検証 (raw / clamped / normalized)
    print("\n--- 三角不等式検証 ---")
    for label, key in [("raw", "ed_raw"), ("max(0,)", "ed_clamp"), ("正規化", "ed_norm")]:
        dist_map = {}
        for r in ed_results:
            dist_map[(r["f1"], r["f2"])] = r[key]
            dist_map[(r["f2"], r["f1"])] = r[key]

        violations = 0
        total = 0
        for a, b, c in combinations(top8_names, 3):
            d_ab = dist_map.get((a, b), 0)
            d_bc = dist_map.get((b, c), 0)
            d_ac = dist_map.get((a, c), 0)
            total += 3
            for d1, d2, d3 in [(d_ac, d_ab, d_bc), (d_ab, d_ac, d_bc), (d_bc, d_ab, d_ac)]:
                if d1 > d2 + d3 + 1e-6:
                    violations += 1
        print(f"  {label:8s}: {total-violations}/{total} 成立 ({violations} 違反)")

    # ============================================================
    # E3': 忘却率 (v2 と同じ)
    # ============================================================
    print("\n" + "=" * 60)
    print("[E3'] 忘却率")
    print("=" * 60)

    forgetting_rates = []
    for fname, ents in sorted(top20.items(), key=lambda x: -len(x[1])):
        feats_ccl = [e["features"] for e in ents[:20]]
        feats_txt = [text_features_from_ccl(e["ccl"]) for e in ents[:20]]

        ccl_div = mean(pairwise_distances(feats_ccl)) if len(feats_ccl) >= 2 else 0.0
        txt_div = mean(pairwise_distances(feats_txt)) if len(feats_txt) >= 2 else 0.0

        forgetting = 1.0 - (ccl_div / txt_div if txt_div > 0 else 1.0)
        forgetting_rates.append(forgetting)
        cat = ents[0]["category"]
        print(f"  {fname:40s}({cat:4s}) | txt={txt_div:8.2f} ccl={ccl_div:8.2f} forget={forgetting:.4f}")

    avg_forget = mean(forgetting_rates)

    # ============================================================
    # 判定
    # ============================================================
    print("\n" + "=" * 60)
    print("判定")
    print("=" * 60)

    v1_pass = cohens_d > 0.5
    print(f"  V1 (Cohen's d > 0.5): {'✅ PASS' if v1_pass else '❌ FAIL'} (d={cohens_d:.4f})")
    print(f"       Fisher 比: {fisher_ratio:.4f}")

    v4_pass = 0.1 < avg_forget < 0.95
    print(f"  V4 (忘却率 0.1-0.95): {'✅ PASS' if v4_pass else '❌ FAIL'} (rate={avg_forget:.4f})")

    # 三角不等式 (正規化版)
    norm_violations = sum(1 for r in ed_results if r["ed_norm"] < 0)
    # Use clamped version for triangle check
    dist_map_c = {}
    for r in ed_results:
        dist_map_c[(r["f1"], r["f2"])] = r["ed_clamp"]
        dist_map_c[(r["f2"], r["f1"])] = r["ed_clamp"]
    tri_v = 0
    tri_t = 0
    for a, b, c in combinations(top8_names, 3):
        tri_t += 3
        for d1, d2, d3 in [
            (dist_map_c.get((a, c), 0), dist_map_c.get((a, b), 0), dist_map_c.get((b, c), 0)),
            (dist_map_c.get((a, b), 0), dist_map_c.get((a, c), 0), dist_map_c.get((c, b), 0)),
            (dist_map_c.get((b, c), 0), dist_map_c.get((b, a), 0), dist_map_c.get((a, c), 0)),
        ]:
            if d1 > d2 + d3 + 1e-6:
                tri_v += 1
    tri_pass = tri_v == 0
    print(f"  三角不等式 (clamp): {'✅ PASS' if tri_pass else '❌ FAIL'} ({tri_v} 違反)")

    passed = sum([v1_pass, v4_pass, tri_pass])
    print(f"\n  合格: {passed}/3")
    print("\n[完了]")


if __name__ == "__main__":
    main()
