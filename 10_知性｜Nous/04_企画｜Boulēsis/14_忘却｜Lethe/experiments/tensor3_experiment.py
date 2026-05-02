"""3次テンソル積実験 — 2026-03-31

仮説: Z-score 正規化を交差項計算の *前* に適用すれば var=0.00 問題が解消し、
テンソル積の情報がコサイン類似度に反映される。

条件:
  T0: 22d 演繹核のみ (baseline)
  T1: 22d + 231 2nd-order = 253d
  T2: 22d + 231 2nd-order + top200 3rd-order = ~453d
  T3: Z-score first, then 22d + 231 2nd-order = 253d
  T4: Z-score first, then 22d + 231 2nd-order + top200 3rd-order
"""

import pickle
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

# ============================================================
# パス設定
# ============================================================
_HGK_ROOT = Path(__file__).resolve().parents[4]
_PKL_PATH = _HGK_ROOT / "30_記憶｜Mneme" / "02_索引｜Index" / "code_ccl_features.pkl"

# 22 演繹的次元
DEDUCTIVE = [1, 3, 11, 12, 16, 17, 20, 21, 22, 24, 25, 27, 29, 33, 39, 41, 42, 43, 44, 45, 47, 48]

ALL_DIMS = list(range(49))


# ============================================================
# 共通関数 (purification_experiment.py と同一)
# ============================================================

def normalize(matrix: np.ndarray) -> np.ndarray:
    """Z-score 正規化 -> L2 正規化。"""
    mean = np.mean(matrix, axis=0)
    std = np.std(matrix, axis=0)
    std = np.where(std > 1e-10, std, 1.0)
    z = (matrix - mean) / std
    norms = np.linalg.norm(z, axis=1, keepdims=True)
    norms = np.where(norms > 1e-10, norms, 1.0)
    return z / norms


def compute_self_recall(matrix: np.ndarray, k_values: list[int] = [1, 3, 5, 10]) -> tuple:
    """自己検索 Recall@k。cos > 0.85 の自然ペアを正例とする。"""
    N = matrix.shape[0]
    sim_matrix = matrix @ matrix.T
    np.fill_diagonal(sim_matrix, -np.inf)

    positive_pairs = []
    cap = min(N, 2000)
    for i in range(cap):
        for j in range(i + 1, cap):
            if sim_matrix[i, j] > 0.85:
                positive_pairs.append((i, j))

    if len(positive_pairs) == 0:
        threshold = np.percentile(sim_matrix[np.triu_indices(cap, k=1)], 95)
        for i in range(cap):
            for j in range(i + 1, cap):
                if sim_matrix[i, j] > threshold:
                    positive_pairs.append((i, j))

    rng = np.random.default_rng(42)
    if len(positive_pairs) > 500:
        indices = rng.choice(len(positive_pairs), 500, replace=False)
        positive_pairs = [positive_pairs[i] for i in indices]

    if len(positive_pairs) == 0:
        return {k: 0.0 for k in k_values}, 0, 0.0

    recalls = {k: 0 for k in k_values}
    for a, b in positive_pairs:
        ranked = np.argsort(-sim_matrix[a])
        rank_b = np.where(ranked == b)[0][0] + 1
        for k in k_values:
            if rank_b <= k:
                recalls[k] += 1

    total = len(positive_pairs)
    recall_rates = {k: v / total for k, v in recalls.items()}
    avg_pos_sim = np.mean([sim_matrix[a, b] for a, b in positive_pairs])
    return recall_rates, total, avg_pos_sim


# ============================================================
# テンソル積の構築
# ============================================================

def build_2nd_order(raw: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """C(d,2) の 2次交差項を構築。"""
    d = raw.shape[1]
    interactions = []
    names = []
    for i in range(d):
        for j in range(i + 1, d):
            interactions.append(raw[:, i] * raw[:, j])
            names.append(f"d{DEDUCTIVE[i]}*d{DEDUCTIVE[j]}")
    return np.column_stack(interactions), names


def build_3rd_order_top(raw: np.ndarray, top_n: int = 200) -> tuple[np.ndarray, list[str]]:
    """C(d,3) の 3次交差項のうち分散 top-N を返す。"""
    d = raw.shape[1]
    n_total = d * (d - 1) * (d - 2) // 6  # C(d,3)
    print(f"  3次交差項: C({d},3) = {n_total} total, selecting top-{top_n} by variance")

    # 全 3次項を一度に計算するとメモリが大きいので、分散を逐次計算
    variances = []
    triplets = []
    for i in range(d):
        for j in range(i + 1, d):
            for k in range(j + 1, d):
                prod = raw[:, i] * raw[:, j] * raw[:, k]
                variances.append(np.var(prod))
                triplets.append((i, j, k))

    variances = np.array(variances)
    top_idx = np.argsort(-variances)[:top_n]

    interactions = []
    names = []
    for idx in top_idx:
        i, j, k = triplets[idx]
        interactions.append(raw[:, i] * raw[:, j] * raw[:, k])
        names.append(f"d{DEDUCTIVE[i]}*d{DEDUCTIVE[j]}*d{DEDUCTIVE[k]}")

    print(f"  Top-5 3次交差項 (by variance):")
    for rank, idx in enumerate(top_idx[:5]):
        i, j, k = triplets[idx]
        print(f"    {rank+1}. d{DEDUCTIVE[i]}*d{DEDUCTIVE[j]}*d{DEDUCTIVE[k]}: var={variances[idx]:.4f}")

    return np.column_stack(interactions), names


def zscore_only(matrix: np.ndarray) -> np.ndarray:
    """Z-score 正規化のみ (L2 正規化なし)。交差項計算の前処理用。"""
    mean = np.mean(matrix, axis=0)
    std = np.std(matrix, axis=0)
    std = np.where(std > 1e-10, std, 1.0)
    return (matrix - mean) / std


# ============================================================
# 分散診断
# ============================================================

def variance_diagnosis(data: np.ndarray, label: str):
    """交差項の分散分布を診断。"""
    var_per_dim = np.var(data, axis=0)
    n_zero = np.sum(var_per_dim < 1e-10)
    print(f"  [{label}] dims={data.shape[1]}, "
          f"var: mean={np.mean(var_per_dim):.4f}, "
          f"median={np.median(var_per_dim):.4f}, "
          f"max={np.max(var_per_dim):.4f}, "
          f"min={np.min(var_per_dim):.6f}, "
          f"zero_var={n_zero}/{data.shape[1]}")


# ============================================================
# メイン実験
# ============================================================

def main():
    print("=" * 70)
    print("  3次テンソル積実験 — Z-score 前処理仮説の検証")
    print("=" * 70)

    if not _PKL_PATH.exists():
        print(f"\n  pkl not found: {_PKL_PATH}")
        sys.exit(1)

    with open(_PKL_PATH, "rb") as f:
        data = pickle.load(f)
    raw = np.vstack(data["vectors"])
    N, D = raw.shape
    print(f"\nデータ: {N} 関数, {D} 次元")

    # 49d baseline
    print(f"\n{'=' * 70}")
    print("  49d baseline (参照値)")
    print(f"{'=' * 70}")
    normed_49 = normalize(raw)
    recalls_49, n_pairs_49, avg_sim_49 = compute_self_recall(normed_49)
    print(f"  R@1={recalls_49[1]*100:.1f}%, R@3={recalls_49[3]*100:.1f}%, "
          f"R@10={recalls_49[10]*100:.1f}%, pairs={n_pairs_49}")

    # 演繹核抽出
    ded_raw = raw[:, DEDUCTIVE]
    n_ded = ded_raw.shape[1]
    print(f"\n演繹核: {n_ded}d (indices: {DEDUCTIVE})")

    # === 分散診断: raw vs Z-scored ===
    print(f"\n{'=' * 70}")
    print("  分散診断: raw vs Z-score 前処理")
    print(f"{'=' * 70}")

    variance_diagnosis(ded_raw, "raw 22d")
    ded_z = zscore_only(ded_raw)
    variance_diagnosis(ded_z, "Z-scored 22d")

    # 2nd-order from raw
    int2_raw, names2 = build_2nd_order(ded_raw)
    variance_diagnosis(int2_raw, "raw 2nd-order")

    # 2nd-order from Z-scored
    int2_z, _ = build_2nd_order(ded_z)
    variance_diagnosis(int2_z, "Z-scored 2nd-order")

    # 3rd-order from raw
    print(f"\n--- 3次交差項 (raw) ---")
    int3_raw, names3_raw = build_3rd_order_top(ded_raw, top_n=200)
    variance_diagnosis(int3_raw, "raw 3rd-order top200")

    # 3rd-order from Z-scored
    print(f"\n--- 3次交差項 (Z-scored) ---")
    int3_z, names3_z = build_3rd_order_top(ded_z, top_n=200)
    variance_diagnosis(int3_z, "Z-scored 3rd-order top200")

    # === 実験条件 ===
    experiments = {
        "T0: 22d deductive only": ded_raw,
        "T1: 22d + 231 2nd-order (253d)": np.hstack([ded_raw, int2_raw]),
        "T2: 22d + 231 2nd + top200 3rd (~453d)": np.hstack([ded_raw, int2_raw, int3_raw]),
        "T3: Z-first, 22d + 231 2nd (253d)": np.hstack([ded_z, int2_z]),
        "T4: Z-first, 22d + 231 2nd + top200 3rd": np.hstack([ded_z, int2_z, int3_z]),
    }

    results = {}

    for name, mat in experiments.items():
        print(f"\n{'─' * 60}")
        print(f"  {name} ({mat.shape[1]}d)")
        print(f"{'─' * 60}")

        normed = normalize(mat)
        recalls, n_pairs, avg_sim = compute_self_recall(normed)
        print(f"  正例ペア数: {n_pairs}, 平均正例 cos: {avg_sim:.4f}")
        for k, v in recalls.items():
            print(f"  Recall@{k}: {v*100:.1f}%")

        results[name] = {
            "dims": mat.shape[1],
            "recalls": recalls,
            "n_pairs": n_pairs,
            "avg_pos_sim": avg_sim,
        }

    # === 比較テーブル ===
    print(f"\n{'=' * 70}")
    print("  比較テーブル")
    print(f"{'=' * 70}")
    print(f"{'条件':<45} {'d':>4} {'R@1':>6} {'R@3':>6} {'R@5':>6} {'R@10':>6} {'pairs':>5}")
    print(f"{'─' * 80}")

    # 49d baseline
    print(f"{'(ref) 49d baseline':<45} {49:>4} "
          f"{recalls_49.get(1,0)*100:>5.1f}% "
          f"{recalls_49.get(3,0)*100:>5.1f}% "
          f"{recalls_49.get(5,0)*100:>5.1f}% "
          f"{recalls_49.get(10,0)*100:>5.1f}% "
          f"{n_pairs_49:>5}")

    for name, r in results.items():
        r1 = r["recalls"].get(1, 0) * 100
        r3 = r["recalls"].get(3, 0) * 100
        r5 = r["recalls"].get(5, 0) * 100
        r10 = r["recalls"].get(10, 0) * 100
        print(f"{name:<45} {r['dims']:>4} {r1:>5.1f}% {r3:>5.1f}% {r5:>5.1f}% {r10:>5.1f}% {r['n_pairs']:>5}")

    # === 判定 ===
    print(f"\n{'=' * 70}")
    print("  判定")
    print(f"{'=' * 70}")

    baseline_49_r1 = recalls_49.get(1, 0)
    t0_r1 = results["T0: 22d deductive only"]["recalls"].get(1, 0)
    t1_r1 = results["T1: 22d + 231 2nd-order (253d)"]["recalls"].get(1, 0)
    t3_r1 = results["T3: Z-first, 22d + 231 2nd (253d)"]["recalls"].get(1, 0)
    t4_r1 = results["T4: Z-first, 22d + 231 2nd + top200 3rd"]["recalls"].get(1, 0)

    print(f"  49d baseline R@1      = {baseline_49_r1*100:.1f}%")
    print(f"  T0 (22d deductive)    = {t0_r1*100:.1f}%")
    print(f"  T1 (raw 2nd-order)    = {t1_r1*100:.1f}%")
    print(f"  T3 (Z-first 2nd)      = {t3_r1*100:.1f}%")
    print(f"  T4 (Z-first 2nd+3rd)  = {t4_r1*100:.1f}%")

    print(f"\n  仮説1: Z-score 前処理で var=0.00 問題が解消する")
    print(f"    → T3 vs T1: R@1 {t3_r1*100:.1f}% vs {t1_r1*100:.1f}%", end="")
    if t3_r1 > t1_r1 + 0.005:
        print(f" → SUPPORTED (Z-score helps)")
    elif t3_r1 < t1_r1 - 0.005:
        print(f" → REFUTED (Z-score hurts)")
    else:
        print(f" → INCONCLUSIVE")

    print(f"\n  仮説2: 3次テンソル積が追加情報を持つ")
    t2_r1 = results["T2: 22d + 231 2nd + top200 3rd (~453d)"]["recalls"].get(1, 0)
    print(f"    → T2 vs T1: R@1 {t2_r1*100:.1f}% vs {t1_r1*100:.1f}%", end="")
    if t2_r1 > t1_r1 + 0.005:
        print(f" → 3rd-order adds information")
    else:
        print(f" → 3rd-order does NOT help (raw)")
    print(f"    → T4 vs T3: R@1 {t4_r1*100:.1f}% vs {t3_r1*100:.1f}%", end="")
    if t4_r1 > t3_r1 + 0.005:
        print(f" → 3rd-order adds information (Z-scored)")
    else:
        print(f" → 3rd-order does NOT help (Z-scored)")

    print(f"\n  仮説3: テンソル積が 49d baseline を超える")
    best_name = max(results, key=lambda k: results[k]["recalls"].get(1, 0))
    best_r1 = results[best_name]["recalls"].get(1, 0)
    print(f"    Best: {best_name} = {best_r1*100:.1f}% vs 49d = {baseline_49_r1*100:.1f}%")
    if best_r1 > baseline_49_r1:
        print(f"    → SUPPORTED: テンソル積が 49d baseline を超えた!")
    else:
        print(f"    → NOT YET: テンソル積は 49d baseline に未達 (gap={best_r1*100 - baseline_49_r1*100:+.1f}pp)")


if __name__ == "__main__":
    main()
