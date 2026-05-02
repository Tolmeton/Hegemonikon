"""構造式実験 v2 — 道 B の3つの改善

v1 の根本原因:
  1. >> が 43549 回出現し n-gram を支配 → TF-IDF
  2. 弁別力の低い次元が有効信号を希釈 → 特徴選択 (mutual information)
  3. >> 連鎖を平坦にしており木構造が消失 → AST 的トポロジー特徴

v2 の改善:
  改善1: TF-IDF 正規化 — >> のような万能トークンの重みを下げる
  改善2: 特徴選択 — 自己相関の高い (正例ペアで差が大きい) 特徴のみ残す
  改善3: トポロジー特徴 — 括弧/制御のネスト構造、分岐ファンアウト、>> 以外の連結パターン

条件 (v1 継承 + v2 拡張):
  S0: 49d baseline
  S1: TF-IDF n-gram only
  S2: structural v2 (トポロジー拡張) only
  S3: 49d + TF-IDF n-gram
  S4: 49d + structural v2
  S5: 49d + TF-IDF n-gram + structural v2
  S6: S5 + 特徴選択 (MI top-k)

Usage:
  python structural_formula_v2.py
  python structural_formula_v2.py --top-ngrams 100 --mi-top 30
"""

import pickle
import sys
from collections import Counter
from pathlib import Path

import numpy as np

_HGK_ROOT = Path(__file__).resolve().parents[4]
_PKL_PATH = _HGK_ROOT / "30_記憶｜Mneme" / "02_索引｜Index" / "code_ccl_features.pkl"

# ============================================================
# §1 トークン分類 (v1 と共通)
# ============================================================

OPERATORS = {
    ">>", "<<", ">*", "~*", "~!", "~>", ">~", "<~", "<~>",
    "||", "|>", "<|", "&>", "&&",
    "*", "%", "&", "|", "_", "~",
    "^", "\\", "+", "-", "!",
}
CONTROL_PREFIXES = ("F:", "I:", "EI:", "E:", "C:", "R:", "V:", "W:", "L:")


def classify_token(token: str) -> str:
    if token in OPERATORS:
        return "OP:" + token
    for cp in CONTROL_PREFIXES:
        if token.startswith(cp):
            return "CTRL:" + cp.rstrip(":")
    if token == "¥":
        return "VAR:ext"
    if token == "#":
        return "VAR:int"
    if token.startswith("."):
        return "DOT:" + token
    if token.startswith("[") or token.startswith("("):
        return "OPEN"
    if token.endswith("]") or token.endswith(")"):
        return "CLOSE"
    if token.startswith("!"):
        return "ERR"
    if token in ("fn", "pred"):
        return "CALL:" + token
    if token.endswith("_"):
        return "LIT"  # str_, int_, etc.
    return "X"  # その他


# ============================================================
# §2 改善1: TF-IDF n-gram
# ============================================================

def extract_classified_ngrams(ccl_expr: str, n: int = 2) -> Counter:
    """分類済みトークンの n-gram。"""
    tokens = ccl_expr.split()
    classified = [classify_token(t) for t in tokens]
    ngrams = Counter()
    for i in range(len(classified) - n + 1):
        gram = "|".join(classified[i:i + n])
        ngrams[gram] += 1
    return ngrams


def build_tfidf_ngram_matrix(
    metadata: list[dict], top_n: int = 100
) -> tuple[np.ndarray, list[str]]:
    """TF-IDF 正規化された n-gram 行列。"""
    print(f"  TF-IDF bigram 構築中 (top-{top_n})...")
    N = len(metadata)

    # Phase 1: 全 bigram 収集
    all_ngrams = []
    global_counter = Counter()
    for m in metadata:
        ngrams = extract_classified_ngrams(m.get("ccl_expr", ""))
        all_ngrams.append(ngrams)
        global_counter.update(ngrams)

    # 頻度上位を選定
    top_grams = [gram for gram, _ in global_counter.most_common(top_n * 3)]  # 候補を多めに取る

    # Phase 2: DF (document frequency) 計算
    df = Counter()
    for ngrams in all_ngrams:
        for gram in ngrams:
            if gram in set(top_grams):
                df[gram] += 1

    # IDF = log(N / (df + 1))
    idf = {}
    for gram in top_grams:
        idf[gram] = np.log(N / (df.get(gram, 0) + 1))

    # IDF で並べ替え — IDF が高い (レアな) gram を優先
    # ただし df < 5 のレアすぎるものは除外
    valid_grams = [g for g in top_grams if df.get(g, 0) >= 5]
    valid_grams.sort(key=lambda g: -idf[g])
    selected = valid_grams[:top_n]

    gram_to_idx = {g: i for i, g in enumerate(selected)}

    # Phase 3: TF-IDF 行列
    matrix = np.zeros((N, len(selected)), dtype=np.float32)
    for i, ngrams in enumerate(all_ngrams):
        total = sum(ngrams.values()) or 1
        for gram, count in ngrams.items():
            if gram in gram_to_idx:
                tf = count / total
                matrix[i, gram_to_idx[gram]] = tf * idf[gram]

    print(f"  Selected {len(selected)} grams (from {len(global_counter)} unique)")
    print(f"  Top-5 by IDF: {selected[:5]}")
    print(f"  Bottom-5 by IDF: {selected[-5:]}")

    return matrix, selected


# ============================================================
# §3 改善3: トポロジー特徴
# ============================================================

def extract_topology_features(ccl_expr: str) -> dict[str, float]:
    """v2 構造的特徴量 — トポロジー重視。"""
    tokens = ccl_expr.split()
    n = max(len(tokens), 1)
    classified = [classify_token(t) for t in tokens]

    feat = {}

    # --- A. パイプライン構造 ---
    # >> の連鎖長ヒストグラム (長さ 1, 2, 3, 4+)
    chains = []
    current = 0
    for c in classified:
        if c == "OP:>>":
            current += 1
        else:
            if current > 0:
                chains.append(current)
            current = 0
    if current > 0:
        chains.append(current)

    feat["chain_count"] = len(chains)
    feat["chain_max"] = max(chains) if chains else 0
    feat["chain_mean"] = np.mean(chains) if chains else 0
    # >> を除いた「非パイプライン」比率 — >> 以外の構造の豊かさ
    n_compose = sum(1 for c in classified if c == "OP:>>")
    feat["non_compose_ratio"] = 1.0 - (n_compose / n)

    # --- B. 分岐構造 ---
    # * (融合) の左右文脈 — 何を融合しているか
    n_fuse = sum(1 for c in classified if c == "OP:*")
    n_branch = sum(1 for c in classified if c in ("OP:|", "OP:&"))
    feat["fuse_count"] = n_fuse
    feat["branch_count"] = n_branch
    feat["fuse_branch_ratio"] = n_fuse / max(n_fuse + n_branch, 1)

    # * の前後トークンの多様性
    fuse_contexts = set()
    for i, c in enumerate(classified):
        if c == "OP:*":
            left = classified[i - 1] if i > 0 else "START"
            right = classified[i + 1] if i < len(classified) - 1 else "END"
            fuse_contexts.add((left, right))
    feat["fuse_context_diversity"] = len(fuse_contexts)

    # --- C. ネスト構造 ---
    max_depth = 0
    depth = 0
    depth_histogram = [0, 0, 0, 0]  # depth 0, 1, 2, 3+
    for c in classified:
        if c == "OPEN" or c.startswith("CTRL:"):
            depth += 1
            max_depth = max(max_depth, depth)
        elif c == "CLOSE":
            depth = max(0, depth - 1)
        idx = min(depth, 3)
        depth_histogram[idx] += 1

    feat["nest_max"] = max_depth
    feat["nest_ratio_0"] = depth_histogram[0] / n
    feat["nest_ratio_1"] = depth_histogram[1] / n
    feat["nest_ratio_2plus"] = (depth_histogram[2] + depth_histogram[3]) / n

    # --- D. 制御フロー ---
    n_ctrl = sum(1 for c in classified if c.startswith("CTRL:"))
    feat["ctrl_density"] = n_ctrl / n
    feat["has_loop"] = 1.0 if any(c in ("CTRL:F", "CTRL:W") for c in classified) else 0.0
    feat["has_cond"] = 1.0 if "CTRL:I" in classified else 0.0
    feat["has_valid"] = 1.0 if "CTRL:V" in classified else 0.0
    feat["has_converge"] = 1.0 if "CTRL:C" in classified else 0.0

    # --- E. 変数フロー ---
    n_ext = sum(1 for c in classified if c == "VAR:ext")
    n_int = sum(1 for c in classified if c == "VAR:int")
    feat["var_ext_density"] = n_ext / n
    feat["var_int_density"] = n_int / n

    # 外部→内部の「流入パターン」: ¥ の後に # が来る回数
    flow_in = 0
    for i in range(len(classified) - 2):
        if classified[i] == "VAR:ext" and classified[i + 1] == "OP:>>" and classified[i + 2] == "VAR:int":
            flow_in += 1
    feat["flow_ext_to_int"] = flow_in

    # --- F. メソッドチェーン ---
    n_dot = sum(1 for c in classified if c.startswith("DOT:"))
    feat["dot_density"] = n_dot / n
    # メソッドチェーンの最長連鎖 (>> .method >> .attr >> .method)
    dot_chain = 0
    max_dot_chain = 0
    for c in classified:
        if c.startswith("DOT:") or c == "OP:>>":
            dot_chain += 1
        else:
            max_dot_chain = max(max_dot_chain, dot_chain)
            dot_chain = 0
    feat["dot_chain_max"] = max_dot_chain

    # --- G. エラーハンドリング ---
    feat["has_err"] = 1.0 if any(c == "ERR" for c in classified) else 0.0

    # --- H. 演算子エントロピー (>> 以外) ---
    op_counts = Counter()
    for c in classified:
        if c.startswith("OP:") and c != "OP:>>":
            op_counts[c] += 1
    total_noncompose = sum(op_counts.values())
    if total_noncompose > 0:
        probs = np.array(list(op_counts.values())) / total_noncompose
        feat["op_entropy_no_compose"] = float(-np.sum(probs * np.log2(probs + 1e-10)))
    else:
        feat["op_entropy_no_compose"] = 0.0
    feat["op_diversity"] = len(op_counts)  # 使用演算子の種類数

    # --- I. トークン総数 ---
    feat["n_tokens"] = n

    return feat


def build_structural_matrix(metadata: list[dict]) -> tuple[np.ndarray, list[str]]:
    print("  トポロジー特徴量抽出中...")
    all_feats = [extract_topology_features(m.get("ccl_expr", "")) for m in metadata]
    names = sorted(all_feats[0].keys())
    mat = np.zeros((len(metadata), len(names)), dtype=np.float32)
    for i, f in enumerate(all_feats):
        for j, name in enumerate(names):
            mat[i, j] = f.get(name, 0.0)
    print(f"  トポロジー特徴量: {len(names)}d")
    return mat, names


# ============================================================
# §4 改善2: 特徴選択 (Mutual Information proxy)
# ============================================================

def select_features_by_variance_ratio(
    matrix: np.ndarray, sim_matrix: np.ndarray, positive_pairs: list[tuple[int, int]],
    top_k: int = 30,
) -> tuple[np.ndarray, list[int]]:
    """正例ペアの差分分散 / 全体分散 が大きい特徴を選択 (MI の近似)。

    高い = 「正例ペア間で差が小さく、全体では差が大きい」特徴 = 弁別に有用。
    """
    n_dims = matrix.shape[1]
    scores = np.zeros(n_dims)

    for d in range(n_dims):
        col = matrix[:, d]
        global_var = np.var(col)
        if global_var < 1e-10:
            continue
        # 正例ペア間の差の分散
        diffs = np.array([abs(col[a] - col[b]) for a, b in positive_pairs])
        pair_diff_mean = np.mean(diffs)
        # スコア = 全体分散 / ペア差分平均 (高い = ペア内で似ている + 全体で多様)
        scores[d] = global_var / (pair_diff_mean + 1e-10)

    top_idx = np.argsort(-scores)[:top_k]
    return matrix[:, top_idx], top_idx.tolist()


# ============================================================
# §5 評価 (v1 と同一)
# ============================================================

def normalize(matrix: np.ndarray) -> np.ndarray:
    mean = np.mean(matrix, axis=0)
    std = np.std(matrix, axis=0)
    std = np.where(std > 1e-10, std, 1.0)
    z = (matrix - mean) / std
    norms = np.linalg.norm(z, axis=1, keepdims=True)
    norms = np.where(norms > 1e-10, norms, 1.0)
    return z / norms


def compute_self_recall(matrix: np.ndarray, k_values: list[int] = [1, 3, 5, 10]) -> tuple:
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
        return {k: 0.0 for k in k_values}, 0, 0.0, []

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
    return recall_rates, total, avg_pos_sim, positive_pairs


# ============================================================
# §6 メイン
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="構造式実験 v2")
    parser.add_argument("--top-ngrams", type=int, default=100)
    parser.add_argument("--mi-top", type=int, default=30, help="特徴選択で残す次元数")
    args = parser.parse_args()

    print("=" * 70)
    print("  構造式実験 v2 — TF-IDF + トポロジー + 特徴選択")
    print("=" * 70)

    if not _PKL_PATH.exists():
        print(f"  pkl not found: {_PKL_PATH}")
        sys.exit(1)

    with open(_PKL_PATH, "rb") as f:
        data = pickle.load(f)

    raw_49d = np.vstack(data["vectors"])
    metadata = data["metadata"]
    N, D = raw_49d.shape
    print(f"\nデータ: {N} 関数, {D} 次元")

    # === S0: 49d baseline ===
    print(f"\n{'=' * 70}")
    print("  S0: 49d baseline")
    print(f"{'=' * 70}")
    normed_49 = normalize(raw_49d)
    recalls_49, n_pairs_49, avg_sim_49, pos_pairs_49 = compute_self_recall(normed_49)
    print(f"  R@1={recalls_49[1]*100:.1f}%, R@3={recalls_49[3]*100:.1f}%, "
          f"R@10={recalls_49[10]*100:.1f}%, pairs={n_pairs_49}")

    # === 特徴量構築 ===
    tfidf_mat, tfidf_names = build_tfidf_ngram_matrix(metadata, top_n=args.top_ngrams)
    topo_mat, topo_names = build_structural_matrix(metadata)

    # 分散診断
    print(f"\n--- 分散診断 ---")
    for label, mat in [("TF-IDF ngram", tfidf_mat), ("topology", topo_mat)]:
        var = np.var(mat, axis=0)
        n_zero = np.sum(var < 1e-10)
        print(f"  [{label}] dims={mat.shape[1]}, var: mean={np.mean(var):.4f}, "
              f"median={np.median(var):.4f}, zero_var={n_zero}/{mat.shape[1]}")

    # === 実験条件 ===
    combined_all = np.hstack([raw_49d, tfidf_mat, topo_mat])

    experiments = {
        "S0: 49d baseline": raw_49d,
        f"S1: TF-IDF ngram ({tfidf_mat.shape[1]}d)": tfidf_mat,
        f"S2: topology ({topo_mat.shape[1]}d)": topo_mat,
        f"S3: 49d + TF-IDF ({49 + tfidf_mat.shape[1]}d)": np.hstack([raw_49d, tfidf_mat]),
        f"S4: 49d + topo ({49 + topo_mat.shape[1]}d)": np.hstack([raw_49d, topo_mat]),
        f"S5: 49d + all ({combined_all.shape[1]}d)": combined_all,
    }

    results = {}
    for name, mat in experiments.items():
        print(f"\n{'─' * 60}")
        print(f"  {name}")
        print(f"{'─' * 60}")
        normed = normalize(mat)
        recalls, n_pairs, avg_sim, _ = compute_self_recall(normed)
        print(f"  pairs={n_pairs}, avg_cos={avg_sim:.4f}")
        for k, v in recalls.items():
            print(f"  Recall@{k}: {v*100:.1f}%")
        results[name] = {"dims": mat.shape[1], "recalls": recalls, "n_pairs": n_pairs}

    # === S6: 特徴選択 ===
    print(f"\n{'─' * 60}")
    print(f"  S6: 特徴選択 (MI proxy, top-{args.mi_top})")
    print(f"{'─' * 60}")

    # 49d の正例ペアを使って特徴選択
    # 正例ペアを compute_self_recall から取り直す (normed_49 ベース)
    normed_all = normalize(combined_all)
    sim_all = normed_all @ normed_all.T
    np.fill_diagonal(sim_all, -np.inf)

    # 正例ペア: 49d baseline の正例を再利用
    if pos_pairs_49:
        selected_mat, selected_idx = select_features_by_variance_ratio(
            combined_all, sim_all, pos_pairs_49, top_k=args.mi_top
        )
        normed_sel = normalize(selected_mat)
        recalls_sel, n_pairs_sel, avg_sim_sel, _ = compute_self_recall(normed_sel)
        print(f"  Selected {len(selected_idx)} features from {combined_all.shape[1]}")
        print(f"  pairs={n_pairs_sel}, avg_cos={avg_sim_sel:.4f}")
        for k, v in recalls_sel.items():
            print(f"  Recall@{k}: {v*100:.1f}%")

        # どの特徴が選ばれたか
        all_names = [f"49d_{i}" for i in range(49)] + tfidf_names + topo_names
        sel_names = [all_names[i] for i in selected_idx]
        n_from_49d = sum(1 for i in selected_idx if i < 49)
        n_from_tfidf = sum(1 for i in selected_idx if 49 <= i < 49 + len(tfidf_names))
        n_from_topo = sum(1 for i in selected_idx if i >= 49 + len(tfidf_names))
        print(f"  内訳: 49d={n_from_49d}, TF-IDF={n_from_tfidf}, topo={n_from_topo}")
        print(f"  Top-10 selected: {sel_names[:10]}")

        results[f"S6: MI-selected ({len(selected_idx)}d)"] = {
            "dims": len(selected_idx), "recalls": recalls_sel, "n_pairs": n_pairs_sel,
        }
    else:
        print("  ⚠️ 正例ペアなし — 特徴選択をスキップ")

    # === 比較テーブル ===
    print(f"\n{'=' * 70}")
    print("  比較テーブル")
    print(f"{'=' * 70}")
    print(f"{'条件':<45} {'d':>4} {'R@1':>6} {'R@3':>6} {'R@5':>6} {'R@10':>6}")
    print(f"{'─' * 75}")

    # v1 参考値
    print(f"{'(v1 ref) S1 ngram-only':<45} {'100':>4} {'0.2%':>6} {'0.8%':>6} {'0.8%':>6} {'1.4%':>6}")
    print(f"{'(v1 ref) S5 49d+all':<45} {'171':>4} {'3.2%':>6} {'7.4%':>6} {'12.0%':>6} {'20.4%':>6}")

    for name, r in results.items():
        rc = r["recalls"]
        print(f"{name:<45} {r['dims']:>4} "
              f"{rc.get(1,0)*100:>5.1f}% {rc.get(3,0)*100:>5.1f}% "
              f"{rc.get(5,0)*100:>5.1f}% {rc.get(10,0)*100:>5.1f}%")

    # === 判定 ===
    print(f"\n{'=' * 70}")
    print("  判定")
    print(f"{'=' * 70}")
    baseline_r1 = results["S0: 49d baseline"]["recalls"].get(1, 0)

    # v2 vs v1 改善
    s1_key = [k for k in results if k.startswith("S1:")][0]
    s1_r1 = results[s1_key]["recalls"].get(1, 0)
    print(f"\n  改善1 (TF-IDF): S1 v2={s1_r1*100:.1f}% vs v1=0.2% → {'改善' if s1_r1 > 0.002 + 0.003 else '変化なし'}")

    s5_key = [k for k in results if k.startswith("S5:")][0]
    s5_r1 = results[s5_key]["recalls"].get(1, 0)
    s5_v1 = 0.032  # v1 の S5 R@1
    print(f"  改善全体: S5 v2={s5_r1*100:.1f}% vs v1={s5_v1*100:.1f}% → {'改善' if s5_r1 > s5_v1 + 0.005 else '変化なし'}")

    # 49d 超え判定
    best_name = max(results, key=lambda k: results[k]["recalls"].get(1, 0))
    best_r1 = results[best_name]["recalls"].get(1, 0)
    delta = best_r1 - baseline_r1
    print(f"\n  49d 超え: best={best_name}")
    print(f"    R@1={best_r1*100:.1f}% vs 49d={baseline_r1*100:.1f}% (Δ={delta*100:+.1f}pp)")
    if delta > 0.005:
        print(f"    → ✅ 49d baseline を超えた!")
    elif delta > -0.005:
        print(f"    → ⚠️ INCONCLUSIVE")
    else:
        print(f"    → ❌ 49d baseline 未達")


if __name__ == "__main__":
    main()
