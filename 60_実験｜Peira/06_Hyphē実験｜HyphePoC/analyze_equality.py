#!/usr/bin/env python3
"""等号条件の出現頻度分析 (NumPy 最適化版)

統合命題「正規化凸性の presheaf 整合性」の展開:
  等号条件 ‖norm(Σ)‖ = ‖Σ(norm)‖ ⟺ 全ベクトルが同一方向

実データ上で:
  1. bias (= s_merged - s_weighted) の分布形状
  2. ICS (inter_centroid_sim) → 1.0 に近づくとバイアスが消えるか
  3. 等号近傍 (bias < ε) の出現率とその条件
  4. セッション別の ICS 分布

最適化メモ (v2.0):
  - Pure Python のペアワイズループ → NumPy 行列演算 (O(k) cos_sim の定数倍改善)
  - intra_alignment のキャッシュ (同一チャンクの重複計算を排除)
  - centroid 計算の NumPy 化
"""

import json
import math
import pickle
import sys
from pathlib import Path

import numpy as np

# パス設定
HGK_ROOT = Path("/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon")
MEKHANE_SRC = HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"
EXPERIMENT_DIR = HGK_ROOT / "60_実験｜Peira" / "06_Hyphē実験｜HyphePoC"
CACHE_FILE = EXPERIMENT_DIR / "embedding_cache.pkl"

sys.path.insert(0, str(MEKHANE_SRC))
sys.path.insert(0, str(EXPERIMENT_DIR))

from hyphe_chunker import (
    Step,
    chunk_session,
)


def np_l2_normalize(vecs: np.ndarray) -> np.ndarray:
    """L2 正規化 (行列版)。"""
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return vecs / norms


def np_centroid(normed: np.ndarray, indices: list[int]) -> np.ndarray:
    """L2 正規化済み embedding から centroid を計算 (NumPy 版)。"""
    if not indices:
        return np.zeros(normed.shape[1])
    c = normed[indices].mean(axis=0)
    norm = np.linalg.norm(c)
    return c / norm if norm > 0 else c


def np_intra_alignment(normed: np.ndarray, indices: list[int]) -> float:
    """チャンク内の全ベクトル間の cos_sim の平均 (NumPy 版)。
    = 1.0 なら全ベクトルが同一方向 (等号条件)。

    NumPy の行列積で O(k²) のペアワイズ cos_sim をベクトル化。
    """
    k = len(indices)
    if k < 2:
        return 1.0
    sub = normed[indices]  # (k, d)
    # cos_sim 行列 (既に L2 正規化済みなのでドット積のみ)
    sim_matrix = sub @ sub.T  # (k, k)
    # 上三角 (対角を除く) の平均
    triu_indices = np.triu_indices(k, k=1)
    return float(sim_matrix[triu_indices].mean())


def main():
    # τ パラメータ (CLI引数で指定可能、デフォルト 0.70)
    tau = float(sys.argv[1]) if len(sys.argv) > 1 else 0.70
    print(f"Using tau = {tau:.2f}")

    # キャッシュ読み込み
    with open(CACHE_FILE, "rb") as f:
        cache = pickle.load(f)

    # 全ペアのデータ収集
    records = []

    for sid, data in sorted(cache.items()):
        embs = data["embeddings"]
        n = len(embs)
        if n < 6:
            continue

        # NumPy 配列に一括変換
        embs_np = np.array(embs, dtype=np.float32)
        normed = np_l2_normalize(embs_np)

        # チャンク分割 (hyphe_chunker を使用 — 元のインターフェースを維持)
        dummy = [Step(index=i, text=f"s{i}") for i in range(n)]
        result = chunk_session(dummy, embs, tau=tau)
        chunks = result.chunks

        if len(chunks) < 2:
            continue

        # チャンク別の intra_alignment をキャッシュ (同一チャンクの重複計算排除)
        chunk_align_cache = {}
        chunk_centroid_cache = {}

        for ci in range(len(chunks)):
            indices = [s.index for s in chunks[ci].steps]
            key = tuple(indices)
            chunk_align_cache[key] = np_intra_alignment(normed, indices)
            chunk_centroid_cache[key] = np_centroid(normed, indices)

        for ci in range(len(chunks) - 1):
            c_a = chunks[ci]
            c_b = chunks[ci + 1]
            a_steps = [s.index for s in c_a.steps]
            b_steps = [s.index for s in c_b.steps]
            merged = a_steps + b_steps
            merged_set = set(merged)

            key_a = tuple(a_steps)
            key_b = tuple(b_steps)
            key_m = tuple(merged)

            cent_a = chunk_centroid_cache[key_a]
            cent_b = chunk_centroid_cache[key_b]
            # merged の centroid はキャッシュにないので計算
            cent_m = np_centroid(normed, merged)

            total = len(a_steps) + len(b_steps)
            w_a = len(a_steps) / total
            w_b = len(b_steps) / total

            # centroid 間距離
            ics = float(cent_a @ cent_b)

            # チャンク内アラインメント (キャッシュから取得 + merged 計算)
            align_a = chunk_align_cache[key_a]
            align_b = chunk_align_cache[key_b]
            # merged の alignment は毎回異なるので計算
            if key_m in chunk_align_cache:
                align_merged = chunk_align_cache[key_m]
            else:
                align_merged = np_intra_alignment(normed, merged)

            # クエリ — 一括でベクトル化
            query_indices = [i for i in range(n) if i not in merged_set]
            if not query_indices:
                continue

            queries = normed[query_indices]  # (nq, d)
            s_m = queries @ cent_m  # (nq,)
            s_a = queries @ cent_a  # (nq,)
            s_b = queries @ cent_b  # (nq,)
            s_w = w_a * s_a + w_b * s_b  # (nq,)
            biases = s_m - s_w  # (nq,)

            for idx_offset, qi in enumerate(query_indices):
                records.append({
                    "sid": sid,
                    "qi": qi,
                    "ci": ci,
                    "bias": float(biases[idx_offset]),
                    "ics": ics,
                    "align_a": align_a,
                    "align_b": align_b,
                    "align_merged": align_merged,
                    "size_a": len(a_steps),
                    "size_b": len(b_steps),
                    "w_a": w_a,
                })

    n = len(records)
    print(f"Total records: {n}")

    if n == 0:
        print("\n⚠️ レコードなし (τ が低すぎてチャンク分割が発生しなかった可能性)")
        # 空の結果を保存して終了
        tau_str = f"{tau:.2f}".replace(".", "")
        out_path = EXPERIMENT_DIR / f"results_equality_tau{tau_str}.json"
        output = {"tau": tau, "n_records": 0, "note": "No chunk pairs found at this tau"}
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"空の結果を {out_path.name} に保存")
        return

    # === 分析1: bias の分布 ===
    print("\n=== 分析1: bias (s_merged - s_weighted) の分布 ===")
    biases = sorted(r["bias"] for r in records)
    percentiles = [0, 5, 10, 25, 50, 75, 90, 95, 100]
    print(f"{'Pctl':>5}  {'Bias':>10}")
    print("-" * 20)
    for p in percentiles:
        idx = min(int(n * p / 100), n - 1)
        print(f"{p:>5}  {biases[idx]:>10.6f}")

    # 等号近傍の定義: bias < ε
    epsilons = [0.001, 0.002, 0.005, 0.01, 0.02]
    print(f"\n{'ε':>8}  {'Count':>6}  {'Rate':>7}  {'Mean ICS':>9}  {'Mean Align':>10}")
    print("-" * 50)
    for eps in epsilons:
        near = [r for r in records if r["bias"] < eps]
        cnt = len(near)
        rate = cnt / n * 100
        mean_ics = sum(r["ics"] for r in near) / cnt if cnt else 0
        mean_align = sum(r["align_merged"] for r in near) / cnt if cnt else 0
        print(f"{eps:>8.3f}  {cnt:>6}  {rate:>6.1f}%  {mean_ics:>9.4f}  {mean_align:>10.4f}")

    # === 分析2: ICS ビン別のバイアス ===
    print("\n=== 分析2: ICS (centroid間類似度) ビン別のバイアス ===")
    ics_bins = [
        (0.0, 0.7, "ICS < 0.70 (異質)"),
        (0.7, 0.8, "0.70-0.80"),
        (0.8, 0.85, "0.80-0.85"),
        (0.85, 0.9, "0.85-0.90"),
        (0.9, 0.95, "0.90-0.95"),
        (0.95, 1.01, "ICS ≥ 0.95 (同質)"),
    ]
    print(f"{'ICS Range':>20}  {'N':>6}  {'Mean Bias':>10}  {'Std Bias':>10}  {'Min':>10}  {'Max':>10}")
    print("-" * 75)
    for lo, hi, label in ics_bins:
        group = [r for r in records if lo <= r["ics"] < hi]
        if not group:
            print(f"{label:>20}  {'---':>6}")
            continue
        bs = [r["bias"] for r in group]
        mean_b = sum(bs) / len(bs)
        std_b = math.sqrt(sum((b - mean_b) ** 2 for b in bs) / len(bs))
        print(f"{label:>20}  {len(group):>6}  {mean_b:>10.6f}  {std_b:>10.6f}  {min(bs):>10.6f}  {max(bs):>10.6f}")

    # === 分析3: intra-alignment ビン別 ===
    print("\n=== 分析3: チャンク内アラインメント (merged) とバイアスの関係 ===")
    align_bins = [
        (0.0, 0.6, "align < 0.60"),
        (0.6, 0.7, "0.60-0.70"),
        (0.7, 0.8, "0.70-0.80"),
        (0.8, 0.9, "0.80-0.90"),
        (0.9, 1.01, "align ≥ 0.90"),
    ]
    print(f"{'Alignment':>16}  {'N':>6}  {'Mean Bias':>10}  {'Mean ICS':>9}")
    print("-" * 50)
    for lo, hi, label in align_bins:
        group = [r for r in records if lo <= r["align_merged"] < hi]
        if not group:
            print(f"{label:>16}  {'---':>6}")
            continue
        mean_b = sum(r["bias"] for r in group) / len(group)
        mean_ics = sum(r["ics"] for r in group) / len(group)
        print(f"{label:>16}  {len(group):>6}  {mean_b:>10.6f}  {mean_ics:>9.4f}")

    # === 分析4: セッション別の ICS 分布 ===
    print("\n=== 分析4: セッション別の ICS 分布と平均バイアス ===")
    sessions = {}
    for r in records:
        sid = r["sid"]
        if sid not in sessions:
            sessions[sid] = {"ics_list": [], "bias_list": [], "pairs": set()}
        sessions[sid]["ics_list"].append(r["ics"])
        sessions[sid]["bias_list"].append(r["bias"])
        sessions[sid]["pairs"].add(r["ci"])

    print(f"{'Session':>10}  {'Pairs':>5}  {'Checks':>7}  {'Mean ICS':>9}  {'Min ICS':>8}  {'Mean Bias':>10}  {'Max Bias':>10}")
    print("-" * 75)
    for sid in sorted(sessions.keys()):
        s = sessions[sid]
        mean_ics = sum(s["ics_list"]) / len(s["ics_list"])
        min_ics = min(s["ics_list"])
        mean_bias = sum(s["bias_list"]) / len(s["bias_list"])
        max_bias = max(s["bias_list"])
        print(f"{sid:>10}  {len(s['pairs']):>5}  {len(s['bias_list']):>7}  {mean_ics:>9.4f}  {min_ics:>8.4f}  {mean_bias:>10.6f}  {max_bias:>10.6f}")

    # === 分析5: 等号条件の理論的到達可能性 ===
    print("\n=== 分析5: 等号条件の理論的考察 ===")
    all_ics = [r["ics"] for r in records]
    all_biases = [r["bias"] for r in records]

    # Pearson: bias vs (1 - ICS)
    one_minus_ics = [1 - x for x in all_ics]
    from analyze_nonlinearity import pearson
    r_bias_ics = pearson(all_biases, one_minus_ics)
    print(f"Pearson(bias, 1-ICS): r = {r_bias_ics:+.4f}")

    # bias vs align_merged
    all_align = [r["align_merged"] for r in records]
    one_minus_align = [1 - x for x in all_align]
    r_bias_align = pearson(all_biases, one_minus_align)
    print(f"Pearson(bias, 1-align_merged): r = {r_bias_align:+.4f}")

    # 最小バイアスのケースの特性
    print(f"\n最小バイアスのケース (下位10件):")
    sorted_by_bias = sorted(records, key=lambda r: r["bias"])
    print(f"{'Bias':>10}  {'ICS':>7}  {'AlignM':>7}  {'AlignA':>7}  {'AlignB':>7}  {'SzA':>4}  {'SzB':>4}")
    print("-" * 55)
    for r in sorted_by_bias[:10]:
        print(f"{r['bias']:>10.6f}  {r['ics']:>7.4f}  {r['align_merged']:>7.4f}  {r['align_a']:>7.4f}  {r['align_b']:>7.4f}  {r['size_a']:>4}  {r['size_b']:>4}")

    print(f"\n最大バイアスのケース (上位10件):")
    print(f"{'Bias':>10}  {'ICS':>7}  {'AlignM':>7}  {'AlignA':>7}  {'AlignB':>7}  {'SzA':>4}  {'SzB':>4}")
    print("-" * 55)
    for r in sorted_by_bias[-10:]:
        print(f"{r['bias']:>10.6f}  {r['ics']:>7.4f}  {r['align_merged']:>7.4f}  {r['align_a']:>7.4f}  {r['align_b']:>7.4f}  {r['size_a']:>4}  {r['size_b']:>4}")

    # JSON 保存
    output = {
        "tau": tau,
        "n_records": n,
        "bias_distribution": {
            f"P{p}": biases[min(int(n * p / 100), n - 1)]
            for p in percentiles
        },
        "near_equality": {
            str(eps): {
                "count": len([r for r in records if r["bias"] < eps]),
                "rate_pct": len([r for r in records if r["bias"] < eps]) / n * 100,
            }
            for eps in epsilons
        },
        "correlation": {
            "bias_vs_1-ICS": r_bias_ics,
            "bias_vs_1-align": r_bias_align,
        },
    }

    # τ 値に応じたファイル名
    tau_str = f"{tau:.2f}".replace(".", "")
    out_path = EXPERIMENT_DIR / f"results_equality_tau{tau_str}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n結果を {out_path.name} に保存")


if __name__ == "__main__":
    main()
