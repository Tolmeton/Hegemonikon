"""49d 特徴量空間の浄化実験 — 2026-03-31

ゴミの土台からはゴミしか生まれ得ない。
49d のうち何が演繹的で何がアドホックかを実験的に検証する。

Phase 0: 49d (ベースライン)
Phase 1: 41d (アドホック 8次元除外)
Phase 2: 36d (41d からフラグ 5次元除外)
Phase 3: 20d (演繹核のみ)
Phase 4: 48d (nt 除外)
Phase 5: 8d (TypeSeq のみ — 最もクリーンな演繹ブロック)

=== テンソル積実験 (v2) ===
Aletheia §2.1 の洞察: 原子的 U パターンは単独で機能しない。
テンソル積 (U_i ⊗ U_j) で初めて具体的構造が創発する。
22d 演繹核の 2次交差項 (C(22,2)=231 interaction terms) を追加し、
「アドホック次元は原子射のテンソル積の影だったか」を検証する。
"""

import pickle
import sys
from pathlib import Path

import numpy as np

# ============================================================
# パス設定
# ============================================================
_HGK_ROOT = Path(__file__).resolve().parents[4]
_PKL_PATH = _HGK_ROOT / "30_記憶｜Mneme" / "02_索引｜Index" / "code_ccl_features.pkl"

# ============================================================
# 次元分類 (監査結果に基づく)
# ============================================================

# D (演繹的): 忘却関手理論/CCL圏論から直接導出
DEDUCTIVE = [1, 3, 11, 12, 16, 17, 20, 21, 22, 24, 25, 27, 29, 33, 39, 41, 42, 43, 44, 45, 47, 48]

# A (アドホック): Python固有・理論的根拠なし
ADHOC = [4, 5, 8, 10, 35, 36, 37, 40]

# E (経験的): 指標改善のため追加
EMPIRICAL = [19, 28]

# H (混成): 理論的動機あるが実装がアドホック
HYBRID = [0, 2, 6, 7, 9, 13, 14, 15, 18, 23, 26, 30, 31, 32, 34, 38, 46]

# フラグ次元 (カウントと重複)
FLAGS = [6, 7, 8, 9, 10]

# スケール支配の元凶
SCALE_DIM = [0]  # nt (total tokens)

# TypeSeq ブロック (最もクリーン)
TYPESEQ = [41, 42, 43, 44, 45, 46, 47, 48]

ALL_DIMS = list(range(49))


# ============================================================
# 実験条件定義
# ============================================================

EXPERIMENTS = {
    "Phase 0: 49d (baseline)": ALL_DIMS,
    "Phase 1: 41d (adhoc除外)": [d for d in ALL_DIMS if d not in ADHOC],
    "Phase 2: 36d (adhoc+flag除外)": [d for d in ALL_DIMS if d not in ADHOC and d not in FLAGS],
    "Phase 3: 20d (演繹核のみ)": DEDUCTIVE,
    "Phase 4: 48d (nt除外)": [d for d in ALL_DIMS if d not in SCALE_DIM],
    "Phase 5: 8d (TypeSeqのみ)": TYPESEQ,
    "Phase 6: 20d演繹+nt除外": [d for d in DEDUCTIVE if d not in SCALE_DIM],
}


# ============================================================
# データ読込 + 正規化
# ============================================================

def load_raw_vectors(pkl_path: Path) -> tuple[np.ndarray, list[dict]]:
    """pkl から raw ベクトルとメタデータを読込む。正規化はしない。"""
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)
    vectors = np.vstack(data["vectors"])  # (N, 49)
    metadata = data["metadata"]
    return vectors, metadata


def normalize(matrix: np.ndarray) -> np.ndarray:
    """Z-score 正規化 → L2 正規化。"""
    mean = np.mean(matrix, axis=0)
    std = np.std(matrix, axis=0)
    std = np.where(std > 1e-10, std, 1.0)
    z = (matrix - mean) / std
    norms = np.linalg.norm(z, axis=1, keepdims=True)
    norms = np.where(norms > 1e-10, norms, 1.0)
    return z / norms


# ============================================================
# Recall@k 測定 (自己検索方式)
# ============================================================

def compute_self_recall(matrix: np.ndarray, k_values: list[int] = [1, 3, 5, 10]) -> dict:
    """各関数をクエリとし、最も類似する関数を検索。

    自己検索 Recall@k: ランダムに 500 ペアをサンプリングし、
    各ペアの A をクエリとしたとき B が top-k に入るかを測定。

    ペア生成: cos 類似度 > 0.85 の自然ペア (構造的類似) を正例とする。
    """
    N = matrix.shape[0]

    # 類似度行列 (cos: 正規化済みなので内積)
    sim_matrix = matrix @ matrix.T  # (N, N)

    # 対角を -inf にして自己マッチを除外
    np.fill_diagonal(sim_matrix, -np.inf)

    # 正例ペア: cos > 0.85 のペア (上三角のみ)
    positive_pairs = []
    for i in range(min(N, 2000)):  # 計算量制限
        for j in range(i + 1, min(N, 2000)):
            if sim_matrix[i, j] > 0.85:
                positive_pairs.append((i, j))

    if len(positive_pairs) == 0:
        # 閾値を下げて再試行
        threshold = np.percentile(sim_matrix[np.triu_indices(min(N, 2000), k=1)], 95)
        for i in range(min(N, 2000)):
            for j in range(i + 1, min(N, 2000)):
                if sim_matrix[i, j] > threshold:
                    positive_pairs.append((i, j))

    # サンプリング (最大 500 ペア)
    rng = np.random.default_rng(42)
    if len(positive_pairs) > 500:
        indices = rng.choice(len(positive_pairs), 500, replace=False)
        positive_pairs = [positive_pairs[i] for i in indices]

    if len(positive_pairs) == 0:
        return {k: 0.0 for k in k_values}, 0, 0.0

    # Recall@k 計算
    recalls = {k: 0 for k in k_values}
    for a, b in positive_pairs:
        # a をクエリ → b の順位は?
        ranked = np.argsort(-sim_matrix[a])
        rank_b = np.where(ranked == b)[0][0] + 1  # 1-indexed
        for k in k_values:
            if rank_b <= k:
                recalls[k] += 1

    total = len(positive_pairs)
    recall_rates = {k: v / total for k, v in recalls.items()}

    # 平均正例類似度
    avg_pos_sim = np.mean([sim_matrix[a, b] for a, b in positive_pairs])

    return recall_rates, total, avg_pos_sim


# ============================================================
# PCA 分散分析
# ============================================================

def pca_analysis(matrix: np.ndarray, top_n: int = 5) -> dict:
    """共分散行列の固有値から有効次元数を算出。"""
    # Z-score のみ (L2 正規化前)
    mean = np.mean(matrix, axis=0)
    std = np.std(matrix, axis=0)
    std = np.where(std > 1e-10, std, 1.0)
    z = (matrix - mean) / std

    cov = np.cov(z, rowvar=False)
    eigenvalues = np.linalg.eigvalsh(cov)[::-1]  # 降順

    total_var = eigenvalues.sum()
    cumulative = np.cumsum(eigenvalues) / total_var

    # 有効次元数 (80% 分散)
    d_eff_80 = int(np.searchsorted(cumulative, 0.80)) + 1
    # 有効次元数 (95% 分散)
    d_eff_95 = int(np.searchsorted(cumulative, 0.95)) + 1

    # Gini 係数
    n = len(eigenvalues)
    sorted_eig = np.sort(eigenvalues)
    index = np.arange(1, n + 1)
    gini = (2 * np.sum(index * sorted_eig) / (n * np.sum(sorted_eig))) - (n + 1) / n

    return {
        "d_total": len(eigenvalues),
        "d_eff_80": d_eff_80,
        "d_eff_95": d_eff_95,
        "gini": gini,
        "top_eigenvalues": eigenvalues[:top_n].tolist(),
        "cumulative_top5": cumulative[min(4, len(cumulative) - 1)],
        "pc1_ratio": eigenvalues[0] / total_var if total_var > 0 else 0,
    }


# ============================================================
# メイン実験
# ============================================================

def main():
    print("=" * 70)
    print("  49d 浄化実験 — ゴミの土台からはゴミしか生まれ得ない")
    print("=" * 70)

    if not _PKL_PATH.exists():
        print(f"\n❌ pkl not found: {_PKL_PATH}")
        print("  code_ccl_features.pkl が必要です。")
        sys.exit(1)

    raw, metadata = load_raw_vectors(_PKL_PATH)
    N, D = raw.shape
    print(f"\nデータ: {N} 関数, {D} 次元")
    print(f"pkl: {_PKL_PATH}")

    # --- 全実験実行 ---
    results = {}

    for name, dims in EXPERIMENTS.items():
        print(f"\n{'─' * 60}")
        print(f"  {name} ({len(dims)}d)")
        print(f"  dims: {dims[:10]}{'...' if len(dims) > 10 else ''}")
        print(f"{'─' * 60}")

        # 次元選択
        subset = raw[:, dims]

        # 正規化
        normed = normalize(subset)

        # PCA
        pca = pca_analysis(subset)
        print(f"  PCA: d_eff(80%)={pca['d_eff_80']}/{len(dims)}, "
              f"d_eff(95%)={pca['d_eff_95']}/{len(dims)}, "
              f"Gini={pca['gini']:.3f}, PC1={pca['pc1_ratio']*100:.1f}%")

        # Recall@k
        recalls, n_pairs, avg_sim = compute_self_recall(normed)
        print(f"  正例ペア数: {n_pairs}, 平均正例 cos: {avg_sim:.4f}")
        for k, v in recalls.items():
            print(f"  Recall@{k}: {v*100:.1f}%")

        results[name] = {
            "dims": len(dims),
            "pca": pca,
            "recalls": recalls,
            "n_pairs": n_pairs,
            "avg_pos_sim": avg_sim,
        }

    # --- テンソル積実験 ---
    print(f"\n{'=' * 70}")
    print("  テンソル積実験 — 原子射の組み合わせで構造が創発するか")
    print(f"{'=' * 70}")

    # 演繹核のみ抽出
    deductive_raw = raw[:, DEDUCTIVE]
    n_deductive = deductive_raw.shape[1]

    # 2次交差項 (interaction_only: x_i * x_j for i < j)
    n_interactions = n_deductive * (n_deductive - 1) // 2
    interactions = []
    interaction_names = []
    for i in range(n_deductive):
        for j in range(i + 1, n_deductive):
            interactions.append(deductive_raw[:, i] * deductive_raw[:, j])
            interaction_names.append(f"d{DEDUCTIVE[i]}×d{DEDUCTIVE[j]}")
    interaction_matrix = np.column_stack(interactions)  # (N, C(22,2))

    tensor_experiments = {
        "T0: 22d演繹核 (再掲)": deductive_raw,
        "T1: 22d + 231d交差項 = 253d": np.hstack([deductive_raw, interaction_matrix]),
        "T2: 231d交差項のみ": interaction_matrix,
        "T3: 22d演繹核 + top-50交差項": None,  # 後で設定
    }

    # T3: 分散が大きい交差項 top-50 を選択
    interaction_var = np.var(interaction_matrix, axis=0)
    top50_idx = np.argsort(-interaction_var)[:50]
    tensor_experiments["T3: 22d + top50交差項 = 72d"] = np.hstack([
        deductive_raw, interaction_matrix[:, top50_idx]
    ])
    del tensor_experiments["T3: 22d演繹核 + top-50交差項"]

    # top-50 の名前を表示
    print(f"\n  交差項: {n_deductive}d → C({n_deductive},2) = {n_interactions} interactions")
    print(f"  Top-10 高分散交差項:")
    for rank, idx in enumerate(top50_idx[:10]):
        print(f"    {rank+1}. {interaction_names[idx]}: var={interaction_var[idx]:.2f}")

    tensor_results = {}
    for name, data in tensor_experiments.items():
        print(f"\n{'─' * 60}")
        print(f"  {name} ({data.shape[1]}d)")
        print(f"{'─' * 60}")

        normed = normalize(data)

        # PCA (次元数が大きいと共分散行列が巨大なので簡易版)
        if data.shape[1] <= 100:
            pca = pca_analysis(data)
            print(f"  PCA: d_eff(80%)={pca['d_eff_80']}/{data.shape[1]}, "
                  f"Gini={pca['gini']:.3f}, PC1={pca['pc1_ratio']*100:.1f}%")
        else:
            pca = {"d_eff_80": "—", "gini": 0, "pc1_ratio": 0}
            print(f"  PCA: skipped (d={data.shape[1]} > 100)")

        recalls, n_pairs, avg_sim = compute_self_recall(normed)
        print(f"  正例ペア数: {n_pairs}, 平均正例 cos: {avg_sim:.4f}")
        for k, v in recalls.items():
            print(f"  Recall@{k}: {v*100:.1f}%")

        tensor_results[name] = {
            "dims": data.shape[1],
            "recalls": recalls,
            "n_pairs": n_pairs,
            "avg_pos_sim": avg_sim,
        }

    # テンソル積比較テーブル
    print(f"\n{'=' * 70}")
    print("  テンソル積 比較テーブル")
    print(f"{'=' * 70}")
    print(f"{'条件':<40} {'d':>4} {'R@1':>6} {'R@3':>6} {'R@10':>6} {'pairs':>5}")
    print(f"{'─' * 70}")

    # baseline も含めて表示
    base_r = results["Phase 0: 49d (baseline)"]
    print(f"{'(ref) 49d baseline':<40} {base_r['dims']:>4} "
          f"{base_r['recalls'].get(1,0)*100:>5.1f}% "
          f"{base_r['recalls'].get(3,0)*100:>5.1f}% "
          f"{base_r['recalls'].get(10,0)*100:>5.1f}% "
          f"{base_r['n_pairs']:>5}")

    for name, r in tensor_results.items():
        r1 = r["recalls"].get(1, 0) * 100
        r3 = r["recalls"].get(3, 0) * 100
        r10 = r["recalls"].get(10, 0) * 100
        print(f"{name:<40} {r['dims']:>4} {r1:>5.1f}% {r3:>5.1f}% {r10:>5.1f}% {r['n_pairs']:>5}")

    # 判定
    baseline_r1 = results["Phase 0: 49d (baseline)"]["recalls"].get(1, 0)
    t1_r1 = tensor_results.get("T1: 22d + 231d交差項 = 253d", {}).get("recalls", {}).get(1, 0)
    print(f"\n  ★ テンソル積仮説検証:")
    print(f"    49d baseline R@1 = {baseline_r1*100:.1f}%")
    print(f"    22d 演繹核 R@1   = {results['Phase 3: 20d (演繹核のみ)']['recalls'].get(1,0)*100:.1f}%")
    print(f"    253d テンソル積 R@1 = {t1_r1*100:.1f}%")
    if t1_r1 > baseline_r1:
        print(f"    → ✅ テンソル積仮説支持: 演繹核の交差項が 49d baseline を超えた")
        print(f"    → アドホック次元は原子射のテンソル積の不完全な影だった")
    elif t1_r1 > results["Phase 3: 20d (演繹核のみ)"]["recalls"].get(1, 0):
        print(f"    → △ 部分支持: 交差項で改善したが baseline 未達")
        print(f"    → 高次テンソル積 (3重以上) が必要か、理論の拡張が要る")
    else:
        print(f"    → ❌ テンソル積仮説不支持: 交差項を追加しても改善なし")
        print(f"    → 問題は次元設計ではなく embedding 方法 (解釈 B) の可能性")

    # --- 比較テーブル (元の実験) ---
    print(f"\n{'=' * 70}")
    print("  比較テーブル (浄化実験)")
    print(f"{'=' * 70}")
    print(f"{'条件':<35} {'d':>3} {'d_eff':>5} {'Gini':>5} {'PC1%':>5} {'R@1':>6} {'R@3':>6} {'pairs':>5}")
    print(f"{'─' * 70}")
    for name, r in results.items():
        short_name = name.split(":")[0] + ":" + name.split(":")[1][:20] if ":" in name else name[:35]
        r1 = r["recalls"].get(1, 0) * 100
        r3 = r["recalls"].get(3, 0) * 100
        print(f"{short_name:<35} {r['dims']:>3} "
              f"{r['pca']['d_eff_80']:>5} "
              f"{r['pca']['gini']:>5.3f} "
              f"{r['pca']['pc1_ratio']*100:>5.1f} "
              f"{r1:>5.1f}% "
              f"{r3:>5.1f}% "
              f"{r['n_pairs']:>5}")

    # --- 判定 ---
    print(f"\n{'=' * 70}")
    print("  判定")
    print(f"{'=' * 70}")

    baseline_r1 = results["Phase 0: 49d (baseline)"]["recalls"].get(1, 0)
    for name, r in results.items():
        if name.startswith("Phase 0"):
            continue
        r1 = r["recalls"].get(1, 0)
        delta = r1 - baseline_r1
        status = "✅ 維持" if delta >= -0.05 else "⚠️ 劣化" if delta >= -0.15 else "❌ 崩壊"
        print(f"  {name}: R@1 Δ={delta*100:+.1f}pp → {status}")


if __name__ == "__main__":
    main()
