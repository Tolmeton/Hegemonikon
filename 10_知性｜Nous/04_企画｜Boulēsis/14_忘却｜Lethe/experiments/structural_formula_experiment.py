"""構造式実験 — CCL 演算子パターンの明示的特徴量化 (道 B)

化学的同型 (chemistry_of_ccl_features.md §4):
  原子 (22d 演繹核)    → R@1=0.4%  壊滅
  分子式 (テンソル積)   → R@1=2.8%  不足
  構造式 (本実験)       → R@1=???   未踏 ← ここ
  高分子 (Phase C)      → transformer に直接読ませる

PURPOSE: CCL 演算子の結合パターンを「官能基」として特徴量化し、
  49d baseline (R@1=6.2%) を超えるかを検証する。

条件:
  S0: 49d baseline (参照値)
  S1: 演算子 n-gram (bigram) のみ
  S2: 構造的特徴量 (深度・分岐・融合 etc.) のみ
  S3: 49d + 演算子 n-gram
  S4: 49d + 構造的特徴量
  S5: 49d + 演算子 n-gram + 構造的特徴量 (全結合)

Usage:
  python structural_formula_experiment.py
  python structural_formula_experiment.py --top-ngrams 50
"""

import pickle
import re
import sys
from collections import Counter
from itertools import islice
from pathlib import Path

import numpy as np

# ============================================================
# パス設定
# ============================================================
_HGK_ROOT = Path(__file__).resolve().parents[4]
_PKL_PATH = _HGK_ROOT / "30_記憶｜Mneme" / "02_索引｜Index" / "code_ccl_features.pkl"


# ============================================================
# §1 CCL トークナイザ — 演算子と構造トークンを分離
# ============================================================

# 演算子 (長い順にマッチ — 最長一致)
OPERATORS = [
    ">>", "<<", ">*", "~*", "~!", "~>", ">~", "<~", "<~>",
    "||", "|>", "<|", "&>", "&&",
    "*", "%", "&", "|", "_", "~",
    "^", "\\", "+", "-", "!",
]

# 制御構文
CONTROL_TOKENS = {"F:", "I:", "EI:", "E:", "C:", "R:", "V:", "W:", "L:"}

# 変数トークン
VAR_TOKENS = {"¥", "#"}

# 構造トークン
STRUCTURE_TOKENS = {".method", ".attr", "fn", "pred", "str_", "int_", "float_", "bool_", "none_"}


def tokenize_ccl(ccl_expr: str) -> list[str]:
    """CCL 式をトークンリストに変換。"""
    tokens = ccl_expr.split()
    return tokens


def classify_token(token: str) -> str:
    """トークンを分類する。"""
    if token in OPERATORS or token in {">>", "<<", ">*"}:
        return "op"
    for ct in CONTROL_TOKENS:
        if token.startswith(ct):
            return "ctrl"
    if token in VAR_TOKENS:
        return "var"
    if token.startswith("[") and token.endswith("]"):
        return "bracket"
    if token.startswith("(") or token.startswith(")"):
        return "paren"
    if token.startswith("!"):
        return "error"
    if token in STRUCTURE_TOKENS or token.startswith("."):
        return "struct"
    return "other"


# ============================================================
# §2 構造式特徴量の抽出
# ============================================================

def extract_operator_ngrams(tokens: list[str], n: int = 2) -> Counter:
    """演算子 n-gram を抽出。非演算子トークンは '_' に置換して文脈を保持。"""
    # トークンを演算子/非演算子に二値化
    binary = []
    for t in tokens:
        if t in OPERATORS:
            binary.append(t)
        else:
            cat = classify_token(t)
            binary.append(cat)  # op, ctrl, var, struct, other 等

    # n-gram
    ngrams = Counter()
    for i in range(len(binary) - n + 1):
        gram = tuple(binary[i:i + n])
        ngrams[gram] += 1
    return ngrams


def extract_structural_features(ccl_expr: str) -> dict[str, float]:
    """構造式レベルの特徴量を抽出する。"""
    tokens = tokenize_ccl(ccl_expr)
    n_tokens = max(len(tokens), 1)

    features = {}

    # --- 1. パイプライン深度 (>> の最長連鎖) ---
    max_chain = 0
    current_chain = 0
    for t in tokens:
        if t == ">>":
            current_chain += 1
            max_chain = max(max_chain, current_chain)
        else:
            current_chain = 0
    features["pipeline_depth"] = max_chain

    # --- 2. 演算子密度 (各演算子の出現率) ---
    op_counts = Counter()
    for t in tokens:
        if t in OPERATORS:
            op_counts[t] += 1

    features["op_density_compose"] = op_counts.get(">>", 0) / n_tokens  # >> 合成
    features["op_density_fuse"] = op_counts.get("*", 0) / n_tokens      # * 融合
    features["op_density_branch"] = op_counts.get("|", 0) / n_tokens    # | 選択
    features["op_density_cond"] = op_counts.get("&", 0) / n_tokens      # & 条件接続
    features["op_density_deepen"] = op_counts.get("+", 0) / n_tokens    # + 深化
    features["op_density_reduce"] = op_counts.get("-", 0) / n_tokens    # - 縮約
    features["op_density_oscillate"] = (
        op_counts.get("~", 0) + op_counts.get("~*", 0) + op_counts.get("~!", 0)
    ) / n_tokens  # 振動系

    # --- 3. 制御構造 ---
    ctrl_count = sum(1 for t in tokens if any(t.startswith(c) for c in CONTROL_TOKENS))
    features["ctrl_density"] = ctrl_count / n_tokens
    features["has_loop"] = 1.0 if any(t.startswith("F:") or t.startswith("W:") for t in tokens) else 0.0
    features["has_conditional"] = 1.0 if any(t.startswith("I:") for t in tokens) else 0.0
    features["has_validation"] = 1.0 if any(t.startswith("V:") for t in tokens) else 0.0

    # --- 4. ネスト深度 (括弧の最大深度) ---
    max_depth = 0
    depth = 0
    for t in tokens:
        if t.startswith("(") or t.startswith("{") or t.startswith("["):
            depth += 1
            max_depth = max(max_depth, depth)
        elif t.endswith(")") or t.endswith("}") or t.endswith("]"):
            depth = max(0, depth - 1)
    # 制御構文の { } もカウント
    for t in tokens:
        if "{" in t:
            depth += t.count("{")
            max_depth = max(max_depth, depth)
        if "}" in t:
            depth = max(0, depth - t.count("}"))
    features["nesting_depth"] = max_depth

    # --- 5. 変数フロー (¥ 外部入力 vs # 内部状態) ---
    n_external = sum(1 for t in tokens if t == "¥")
    n_internal = sum(1 for t in tokens if t == "#")
    features["var_external_ratio"] = n_external / n_tokens
    features["var_internal_ratio"] = n_internal / n_tokens
    features["var_ext_int_ratio"] = n_external / max(n_internal, 1)

    # --- 6. メソッドチェーン密度 ---
    n_method = sum(1 for t in tokens if t.startswith("."))
    features["method_chain_density"] = n_method / n_tokens

    # --- 7. エラーハンドリング ---
    features["has_error_handling"] = 1.0 if any(t.startswith("!err") for t in tokens) else 0.0

    # --- 8. 融合パターン (* の位置 — 中間 vs 末端) ---
    star_positions = [i / n_tokens for i, t in enumerate(tokens) if t == "*"]
    if star_positions:
        features["fuse_mean_pos"] = np.mean(star_positions)
        features["fuse_std_pos"] = np.std(star_positions) if len(star_positions) > 1 else 0.0
    else:
        features["fuse_mean_pos"] = 0.0
        features["fuse_std_pos"] = 0.0

    # --- 9. トークン総数 (スケール) ---
    features["n_tokens"] = n_tokens

    # --- 10. 演算子多様性 (Shannon entropy) ---
    total_ops = sum(op_counts.values())
    if total_ops > 0:
        probs = np.array(list(op_counts.values())) / total_ops
        features["op_entropy"] = float(-np.sum(probs * np.log2(probs + 1e-10)))
    else:
        features["op_entropy"] = 0.0

    return features


# ============================================================
# §3 特徴量ベクトル構築
# ============================================================

def build_ngram_matrix(metadata: list[dict], top_n: int = 100) -> tuple[np.ndarray, list[str]]:
    """全関数の演算子 bigram 特徴量行列を構築。"""
    print(f"  演算子 bigram 抽出中 (top-{top_n})...")

    # Phase 1: 全 bigram を収集して頻度順に top-N を選定
    global_counter = Counter()
    all_ngrams = []
    for m in metadata:
        tokens = tokenize_ccl(m.get("ccl_expr", ""))
        ngrams = extract_operator_ngrams(tokens, n=2)
        all_ngrams.append(ngrams)
        global_counter.update(ngrams)

    top_grams = [gram for gram, _ in global_counter.most_common(top_n)]
    gram_to_idx = {g: i for i, g in enumerate(top_grams)}

    print(f"  Top-5 bigrams: {[(str(g), c) for g, c in global_counter.most_common(5)]}")

    # Phase 2: 行列構築
    matrix = np.zeros((len(metadata), top_n), dtype=np.float32)
    for i, ngrams in enumerate(all_ngrams):
        for gram, count in ngrams.items():
            if gram in gram_to_idx:
                matrix[i, gram_to_idx[gram]] = count

    gram_names = [f"bg_{'_'.join(str(x) for x in g)}" for g in top_grams]
    return matrix, gram_names


def build_structural_matrix(metadata: list[dict]) -> tuple[np.ndarray, list[str]]:
    """全関数の構造的特徴量行列を構築。"""
    print("  構造的特徴量抽出中...")

    all_features = []
    for m in metadata:
        feat = extract_structural_features(m.get("ccl_expr", ""))
        all_features.append(feat)

    feature_names = sorted(all_features[0].keys())
    matrix = np.zeros((len(metadata), len(feature_names)), dtype=np.float32)
    for i, feat in enumerate(all_features):
        for j, name in enumerate(feature_names):
            matrix[i, j] = feat.get(name, 0.0)

    print(f"  構造的特徴量: {len(feature_names)}d ({feature_names[:5]}...)")
    return matrix, feature_names


# ============================================================
# ��4 評価 (tensor3_experiment.py と同一)
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


def variance_diagnosis(data: np.ndarray, label: str):
    """分散診断。"""
    var_per_dim = np.var(data, axis=0)
    n_zero = np.sum(var_per_dim < 1e-10)
    print(f"  [{label}] dims={data.shape[1]}, "
          f"var: mean={np.mean(var_per_dim):.4f}, "
          f"median={np.median(var_per_dim):.4f}, "
          f"max={np.max(var_per_dim):.4f}, "
          f"zero_var={n_zero}/{data.shape[1]}")


# ============================================================
# §5 メイン実験
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="構造式実験 — CCL 演算子パターン特徴量化")
    parser.add_argument("--top-ngrams", type=int, default=100, help="上位 N bigram を採用")
    args = parser.parse_args()

    print("=" * 70)
    print("  構造式実験 — CCL 演算子パターンの明示的特徴量化 (道 B)")
    print("=" * 70)

    if not _PKL_PATH.exists():
        print(f"\n  pkl not found: {_PKL_PATH}")
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
    recalls_49, n_pairs_49, avg_sim_49 = compute_self_recall(normed_49)
    print(f"  R@1={recalls_49[1]*100:.1f}%, R@3={recalls_49[3]*100:.1f}%, "
          f"R@10={recalls_49[10]*100:.1f}%, pairs={n_pairs_49}")

    # === 特徴量構築 ===
    ngram_matrix, ngram_names = build_ngram_matrix(metadata, top_n=args.top_ngrams)
    struct_matrix, struct_names = build_structural_matrix(metadata)

    print(f"\n--- 分散診断 ---")
    variance_diagnosis(ngram_matrix, "ngram (raw)")
    variance_diagnosis(struct_matrix, "structural (raw)")

    # === 実験条件 ===
    experiments = {
        "S0: 49d baseline": raw_49d,
        f"S1: ngram only ({ngram_matrix.shape[1]}d)": ngram_matrix,
        f"S2: structural only ({struct_matrix.shape[1]}d)": struct_matrix,
        f"S3: 49d + ngram ({49 + ngram_matrix.shape[1]}d)": np.hstack([raw_49d, ngram_matrix]),
        f"S4: 49d + structural ({49 + struct_matrix.shape[1]}d)": np.hstack([raw_49d, struct_matrix]),
        f"S5: 49d + ngram + structural ({49 + ngram_matrix.shape[1] + struct_matrix.shape[1]}d)": np.hstack([raw_49d, ngram_matrix, struct_matrix]),
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
    print(f"{'条件':<50} {'d':>4} {'R@1':>6} {'R@3':>6} {'R@5':>6} {'R@10':>6} {'pairs':>5}")
    print(f"{'─' * 85}")

    for name, r in results.items():
        r1 = r["recalls"].get(1, 0) * 100
        r3 = r["recalls"].get(3, 0) * 100
        r5 = r["recalls"].get(5, 0) * 100
        r10 = r["recalls"].get(10, 0) * 100
        print(f"{name:<50} {r['dims']:>4} {r1:>5.1f}% {r3:>5.1f}% {r5:>5.1f}% {r10:>5.1f}% {r['n_pairs']:>5}")

    # === 仮説判定 ===
    print(f"\n{'=' * 70}")
    print("  仮説判定")
    print(f"{'=' * 70}")

    baseline_r1 = results["S0: 49d baseline"]["recalls"].get(1, 0)

    print(f"\n  仮説 B1: 構造式特徴量 (S2) 単体が 22d 演繹核 (R@1=0.4%) を超える")
    s2_key = [k for k in results if k.startswith("S2:")][0]
    s2_r1 = results[s2_key]["recalls"].get(1, 0)
    print(f"    S2 R@1 = {s2_r1*100:.1f}% vs 22d = 0.4%", end="")
    if s2_r1 > 0.004 + 0.005:
        print(f" → SUPPORTED")
    else:
        print(f" → NOT SUPPORTED")

    print(f"\n  仮説 B2: 49d + 構造式 (S4/S5) が 49d baseline (R@1={baseline_r1*100:.1f}%) を超える")
    s5_key = [k for k in results if k.startswith("S5:")][0]
    s5_r1 = results[s5_key]["recalls"].get(1, 0)
    delta = s5_r1 - baseline_r1
    print(f"    S5 R@1 = {s5_r1*100:.1f}% vs S0 = {baseline_r1*100:.1f}% (Δ={delta*100:+.1f}pp)", end="")
    if delta > 0.005:
        print(f" → SUPPORTED (構造式が追加情報を持つ)")
    elif delta > -0.005:
        print(f" → INCONCLUSIVE")
    else:
        print(f" → REFUTED")

    print(f"\n  仮説 B3: 演算子 n-gram (S1) が構造的特徴量 (S2) を超える")
    s1_key = [k for k in results if k.startswith("S1:")][0]
    s1_r1 = results[s1_key]["recalls"].get(1, 0)
    print(f"    S1 R@1 = {s1_r1*100:.1f}% vs S2 = {s2_r1*100:.1f}%", end="")
    if s1_r1 > s2_r1 + 0.005:
        print(f" → n-gram > structural (データ駆動 > 手設計)")
    elif s2_r1 > s1_r1 + 0.005:
        print(f" → structural > n-gram (手設計 > データ駆動)")
    else:
        print(f" → INCONCLUSIVE")

    # === best vs tensor3 best ===
    print(f"\n  参考: tensor3 best (T4 Z-first 2nd+3rd) = R@1=2.4%, R@10=17.2%")
    best_name = max(results, key=lambda k: results[k]["recalls"].get(1, 0))
    best_r1 = results[best_name]["recalls"].get(1, 0)
    print(f"  今回 best: {best_name} = R@1={best_r1*100:.1f}%")
    print(f"  → 構造式 vs 分子式: {'構造式が勝利' if best_r1 > 0.024 else '分子式以下'}")


if __name__ == "__main__":
    main()
