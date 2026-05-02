"""構造式実験 v3 — 官能基 binary features の統合

発見した官能基 (functional_group_discovery.py の手法) を binary features として
49d + topo の特徴量に追加し、R@k 改善を検証する。

処理フロー:
  1. データ読込 + 49d baseline 評価
  2. トポロジー特徴量 (26d, v2 から継承)
  3. 官能基発見 (functional_group_discovery.py の手法を inline 実行)
  4. 最長ユニークパターンフィルタ (collinearity 防止)
  5. Binary feature 行列構築
  6. 実験: K=5/10/20/30 で R@k 評価
  7. 比較テーブル

v2 best baseline:
  S4: 49d + topo 26d → R@1=6.2%, R@10=29.4%

目標: R@10 > 29.4%

Usage:
  python structural_formula_v3.py
  python structural_formula_v3.py --top-k-list 5 10 20 30 --min-freq 50
"""

import pickle
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

_HGK_ROOT = Path(__file__).resolve().parents[4]
_PKL_PATH = _HGK_ROOT / "30_記憶｜Mneme" / "02_索引｜Index" / "code_ccl_features.pkl"

# ============================================================
# §1 トークン分類 (functional_group_discovery.py と同一体系)
#    atoms = 意味トークン (単独で意味を持つ)
#    bonds = 演算子 (原子間を接続する)
# ============================================================

BOND_MAP = {
    ">>": "COMPOSE", "<<": "COMPOSE", ">*": "COMPOSE",
    "~*": "COMPOSE", "~!": "COMPOSE", "~>": "COMPOSE",
    ">~": "COMPOSE", "<~": "COMPOSE", "<~>": "COMPOSE",
    "||": "COMPOSE", "|>": "COMPOSE", "<|": "COMPOSE",
    "&>": "COMPOSE", "&&": "COMPOSE",
    "~": "COMPOSE",
    "_": "SEQ",
    "*": "FUSE", "%": "FUSE",
    "&": "COND",
    "|": "SELECT",
}
MODIFIERS = {"^", "\\", "+", "-", "!"}
CONTROL_PREFIXES = ("F:", "I:", "EI:", "E:", "C:", "R:", "V:", "W:", "L:")


def classify_token(token: str) -> str:
    """§8.2 分類: atoms (EXT/INT/FUNC/METH/PRED/CTRL/LIT/ERR) + bonds (COMPOSE/FUSE/COND/SELECT/SEQ)."""
    if token in BOND_MAP:
        return BOND_MAP[token]
    if token in MODIFIERS:
        return "MOD"
    for cp in CONTROL_PREFIXES:
        if token.startswith(cp):
            return "CTRL"
    if token == "¥":
        return "EXT"
    if token == "#":
        return "INT"
    if token.startswith("."):
        return "METH"
    if token == "fn":
        return "FUNC"
    if token == "pred":
        return "PRED"
    if token.startswith("!"):
        return "ERR"
    if token.endswith("_"):
        return "LIT"
    if token.startswith("[") or token.startswith("("):
        return "OPEN"
    if token.endswith("]") or token.endswith(")"):
        return "CLOSE"
    return "X"


def classify_sequence(ccl_expr: str) -> list[str]:
    """CCL テキスト → 分類済みトークン列。MOD/OPEN/CLOSE/X を除外。"""
    tokens = ccl_expr.split()
    classified = [classify_token(t) for t in tokens]
    return [c for c in classified if c not in ("MOD", "OPEN", "CLOSE", "X")]


# ============================================================
# §2 官能基発見 (functional_group_discovery.py から移植)
# ============================================================

def extract_subsequences(
    classified_seqs: list[list[str]],
    min_len: int = 3,
    max_len: int = 7,
    min_freq: int = 50,
) -> dict[str, list[int]]:
    """全 CCL テキストから連続部分列を抽出し、頻度でフィルタ。

    Returns: {pattern_string: [function_indices_containing_it]}
    各 function に対して各 pattern を1度だけカウント (重複なし)。
    """
    subseq_to_indices: dict[str, set[int]] = defaultdict(set)
    for idx, seq in enumerate(classified_seqs):
        seen: set[str] = set()
        for n in range(min_len, min(max_len + 1, len(seq) + 1)):
            for i in range(len(seq) - n + 1):
                s = " ".join(seq[i:i + n])
                if s not in seen:
                    seen.add(s)
                    subseq_to_indices[s].add(idx)
    return {
        s: sorted(idxs)
        for s, idxs in subseq_to_indices.items()
        if len(idxs) >= min_freq
    }


def find_positive_pairs(
    sim_matrix: np.ndarray,
    cap: int = 3000,
    max_pairs: int = 1000,
) -> list[tuple[int, int]]:
    """49d baseline の正例ペア (高類似度ペア) を検出。"""
    N = min(sim_matrix.shape[0], cap)
    pairs = []
    for i in range(N):
        for j in range(i + 1, N):
            if sim_matrix[i, j] > 0.85:
                pairs.append((i, j))
    if not pairs:
        threshold = float(np.percentile(
            sim_matrix[:N, :N][np.triu_indices(N, k=1)], 95,
        ))
        for i in range(N):
            for j in range(i + 1, N):
                if sim_matrix[i, j] > threshold:
                    pairs.append((i, j))
    rng = np.random.default_rng(42)
    if len(pairs) > max_pairs:
        sel = rng.choice(len(pairs), max_pairs, replace=False)
        pairs = [pairs[i] for i in sel]
    return pairs


def compute_enrichment(
    subseq_indices: dict[str, list[int]],
    positive_pairs: list[tuple[int, int]],
    n_total: int,
    min_n: int = 10,
) -> list[dict]:
    """各候補の弁別力 (enrichment) を計算。

    enrichment = P(both in group | positive pair) / P(both in group | random)
    enrichment > 1 → この官能基を共有する関数は類似しやすい
    """
    results = []
    for subseq, indices in subseq_indices.items():
        idx_set = frozenset(indices)
        n_in = len(idx_set)
        if n_in < min_n or (n_total - n_in) < min_n:
            continue
        pairs_both_in = sum(1 for a, b in positive_pairs if a in idx_set and b in idx_set)
        p_in = n_in / n_total
        expected = p_in * p_in * len(positive_pairs)
        enrichment = pairs_both_in / expected if expected >= 1 else float(pairs_both_in)
        results.append({
            "subseq": subseq,
            "freq": n_in,
            "enrichment": enrichment,
            "pairs_both_in": pairs_both_in,
        })
    results.sort(key=lambda r: -r["enrichment"])
    return results


# ============================================================
# §3 最長ユニークパターンフィルタ (collinearity 防止)
# ============================================================

def longest_unique_pattern_filter(
    ranked_patterns: list[str],
    top_k: int,
) -> list[str]:
    """部分文字列関係にあるパターン対から高 enrichment 側のみ残す。

    問題: "CTRL FUSE COMPOSE" が "CTRL FUSE COMPOSE COMPOSE CTRL" の部分列
    → 両方を特徴量にすると feature_short ⊇ feature_long で collinearity

    アルゴリズム:
    - enrichment 降順で処理 (ranked_patterns は enrichment 降順であること)
    - pattern を選択すると、それとの部分文字列関係にある全候補を除外
    - トークン境界を保証するため " "+pattern+" " の string matching を使用
    """
    selected = []
    excluded: set[str] = set()

    for pattern in ranked_patterns:
        if pattern in excluded:
            continue
        selected.append(pattern)
        if len(selected) >= top_k:
            break
        # この pattern と部分文字列関係にある全候補を除外
        pat_padded = " " + pattern + " "
        for other in ranked_patterns:
            if other == pattern or other in excluded:
                continue
            oth_padded = " " + other + " "
            # pattern ⊂ other (pattern が other の部分列) または
            # other ⊂ pattern (other が pattern の部分列)
            if pat_padded in oth_padded or oth_padded in pat_padded:
                excluded.add(other)

    return selected


# ============================================================
# §4 トポロジー特徴量 (structural_formula_v2.py から移植)
#    26次元の構造的特徴量
# ============================================================

OPERATORS_V2 = {
    ">>", "<<", ">*", "~*", "~!", "~>", ">~", "<~", "<~>",
    "||", "|>", "<|", "&>", "&&",
    "*", "%", "&", "|", "_", "~",
    "^", "\\", "+", "-", "!",
}


def classify_token_v2(token: str) -> str:
    """v2 詳細分類 (トポロジー特徴量抽出用)。"""
    if token in OPERATORS_V2:
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
        return "LIT"
    return "X"


def extract_topology_features(ccl_expr: str) -> dict[str, float]:
    """v2 のトポロジー特徴量 (26d)。"""
    tokens = ccl_expr.split()
    n = max(len(tokens), 1)
    classified = [classify_token_v2(t) for t in tokens]
    feat = {}

    # A. パイプライン構造
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
    feat["chain_mean"] = float(np.mean(chains)) if chains else 0.0
    n_compose = sum(1 for c in classified if c == "OP:>>")
    feat["non_compose_ratio"] = 1.0 - (n_compose / n)

    # B. 分岐構造
    n_fuse = sum(1 for c in classified if c == "OP:*")
    n_branch = sum(1 for c in classified if c in ("OP:|", "OP:&"))
    feat["fuse_count"] = n_fuse
    feat["branch_count"] = n_branch
    feat["fuse_branch_ratio"] = n_fuse / max(n_fuse + n_branch, 1)
    fuse_contexts: set[tuple] = set()
    for i, c in enumerate(classified):
        if c == "OP:*":
            left = classified[i - 1] if i > 0 else "START"
            right = classified[i + 1] if i < len(classified) - 1 else "END"
            fuse_contexts.add((left, right))
    feat["fuse_context_diversity"] = len(fuse_contexts)

    # C. ネスト構造
    max_depth = 0
    depth = 0
    depth_histogram = [0, 0, 0, 0]
    for c in classified:
        if c == "OPEN" or c.startswith("CTRL:"):
            depth += 1
            max_depth = max(max_depth, depth)
        elif c == "CLOSE":
            depth = max(0, depth - 1)
        depth_histogram[min(depth, 3)] += 1
    feat["nest_max"] = max_depth
    feat["nest_ratio_0"] = depth_histogram[0] / n
    feat["nest_ratio_1"] = depth_histogram[1] / n
    feat["nest_ratio_2plus"] = (depth_histogram[2] + depth_histogram[3]) / n

    # D. 制御フロー
    n_ctrl = sum(1 for c in classified if c.startswith("CTRL:"))
    feat["ctrl_density"] = n_ctrl / n
    feat["has_loop"] = 1.0 if any(c in ("CTRL:F", "CTRL:W") for c in classified) else 0.0
    feat["has_cond"] = 1.0 if "CTRL:I" in classified else 0.0
    feat["has_valid"] = 1.0 if "CTRL:V" in classified else 0.0
    feat["has_converge"] = 1.0 if "CTRL:C" in classified else 0.0

    # E. 変数フロー
    n_ext = sum(1 for c in classified if c == "VAR:ext")
    n_int = sum(1 for c in classified if c == "VAR:int")
    feat["var_ext_density"] = n_ext / n
    feat["var_int_density"] = n_int / n
    flow_in = 0
    for i in range(len(classified) - 2):
        if (classified[i] == "VAR:ext"
                and classified[i + 1] == "OP:>>"
                and classified[i + 2] == "VAR:int"):
            flow_in += 1
    feat["flow_ext_to_int"] = float(flow_in)

    # F. メソッドチェーン
    n_dot = sum(1 for c in classified if c.startswith("DOT:"))
    feat["dot_density"] = n_dot / n
    dot_chain = 0
    max_dot_chain = 0
    for c in classified:
        if c.startswith("DOT:") or c == "OP:>>":
            dot_chain += 1
        else:
            max_dot_chain = max(max_dot_chain, dot_chain)
            dot_chain = 0
    feat["dot_chain_max"] = max_dot_chain

    # G. エラーハンドリング
    feat["has_err"] = 1.0 if any(c == "ERR" for c in classified) else 0.0

    # H. 演算子エントロピー (>> 以外)
    op_counts: Counter = Counter()
    for c in classified:
        if c.startswith("OP:") and c != "OP:>>":
            op_counts[c] += 1
    total_noncompose = sum(op_counts.values())
    if total_noncompose > 0:
        probs = np.array(list(op_counts.values())) / total_noncompose
        feat["op_entropy_no_compose"] = float(-np.sum(probs * np.log2(probs + 1e-10)))
    else:
        feat["op_entropy_no_compose"] = 0.0
    feat["op_diversity"] = len(op_counts)
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
    print(f"  {len(names)}d")
    return mat, names


# ============================================================
# §5 Binary feature 行列
# ============================================================

def build_fg_binary_matrix(
    metadata: list[dict],
    selected_patterns: list[str],
) -> np.ndarray:
    """官能基 binary feature 行列 (N × K)。

    matrix[i, j] = 1 iff pattern j が classify_sequence(ccl_expr_i) の
    連続部分列として出現する。

    トークン境界の保証: " " + " ".join(seq) + " " に対して
    " " + pattern + " " の string matching を使用。
    """
    N = len(metadata)
    K = len(selected_patterns)
    matrix = np.zeros((N, K), dtype=np.float32)

    classified_seqs = [classify_sequence(m.get("ccl_expr", "")) for m in metadata]

    for i, seq in enumerate(classified_seqs):
        if not seq:
            continue
        seq_padded = " " + " ".join(seq) + " "
        for j, pattern in enumerate(selected_patterns):
            pat_padded = " " + pattern + " "
            if pat_padded in seq_padded:
                matrix[i, j] = 1.0

    return matrix


# ============================================================
# §6 正規化と評価 (v2 と同一)
# ============================================================

def normalize(matrix: np.ndarray) -> np.ndarray:
    """Z-score + L2 正規化。"""
    mean = np.mean(matrix, axis=0)
    std = np.std(matrix, axis=0)
    std = np.where(std > 1e-10, std, 1.0)
    z = (matrix - mean) / std
    norms = np.linalg.norm(z, axis=1, keepdims=True)
    norms = np.where(norms > 1e-10, norms, 1.0)
    return z / norms


def compute_self_recall(
    matrix: np.ndarray,
    k_values: list[int] = [1, 3, 5, 10],
    fixed_pairs: list[tuple[int, int]] | None = None,
) -> tuple:
    """自己探索 Recall@k。

    fixed_pairs が渡された場合、それを正例ペアとして使用 (条件横断比較のため)。
    渡されない場合のみ、matrix の類似度から正例ペアを抽出 (49d baseline 用)。
    """
    N = matrix.shape[0]
    sim_matrix = matrix @ matrix.T
    np.fill_diagonal(sim_matrix, -np.inf)

    if fixed_pairs is not None:
        positive_pairs = fixed_pairs
    else:
        cap = min(N, 2000)
        positive_pairs = []
        for i in range(cap):
            for j in range(i + 1, cap):
                if sim_matrix[i, j] > 0.85:
                    positive_pairs.append((i, j))

        if not positive_pairs:
            threshold = float(np.percentile(
                sim_matrix[:cap, :cap][np.triu_indices(cap, k=1)], 95,
            ))
            for i in range(cap):
                for j in range(i + 1, cap):
                    if sim_matrix[i, j] > threshold:
                        positive_pairs.append((i, j))

        rng = np.random.default_rng(42)
        if len(positive_pairs) > 500:
            sel = rng.choice(len(positive_pairs), 500, replace=False)
            positive_pairs = [positive_pairs[i] for i in sel]

    if not positive_pairs:
        return {k: 0.0 for k in k_values}, 0, 0.0, []

    recalls = {k: 0 for k in k_values}
    for a, b in positive_pairs:
        ranked = np.argsort(-sim_matrix[a])
        rank_b = int(np.where(ranked == b)[0][0]) + 1
        for k in k_values:
            if rank_b <= k:
                recalls[k] += 1

    total = len(positive_pairs)
    recall_rates = {k: v / total for k, v in recalls.items()}
    avg_pos_sim = float(np.mean([sim_matrix[a, b] for a, b in positive_pairs]))
    return recall_rates, total, avg_pos_sim, positive_pairs


# ============================================================
# §7 メイン
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="構造式実験 v3 — 官能基 binary features")
    parser.add_argument("--top-k-list", type=int, nargs="+", default=[5, 10, 20, 30],
                        help="試す官能基数 K のリスト (複数指定可)")
    parser.add_argument("--min-freq", type=int, default=50,
                        help="官能基発見の最小出現頻度")
    parser.add_argument("--min-len", type=int, default=3,
                        help="部分列の最小長")
    parser.add_argument("--max-len", type=int, default=7,
                        help="部分列の最大長")
    parser.add_argument("--max-candidates", type=int, default=150,
                        help="フィルタ前の enrichment 上位 N 件")
    args = parser.parse_args()

    print("=" * 70)
    print("  構造式実験 v3 — 官能基 binary features")
    print("  目標: S4v2 (49d+topo, R@10=29.4%) を超える")
    print("=" * 70)

    if not _PKL_PATH.exists():
        print(f"\n  ⚠️  pkl not found: {_PKL_PATH}")
        sys.exit(1)

    # === [1] データ読込 ===
    print(f"\n[1] データ読込")
    with open(_PKL_PATH, "rb") as f:
        data = pickle.load(f)
    raw_49d = np.vstack(data["vectors"])   # list of ndarrays → (N, 49)
    metadata = data["metadata"]
    N, D = raw_49d.shape
    print(f"  {N} 関数, {D}d")

    # === [2] 49d baseline + 固定正例ペア確定 ===
    print(f"\n[2] 49d baseline (正例ペアを確定 → 全条件で共有)")
    normed_49 = normalize(raw_49d)
    recalls_49, n_pairs_49, avg_sim_49, fixed_pairs_49 = compute_self_recall(normed_49)
    print(f"  R@1={recalls_49[1]*100:.1f}%  R@3={recalls_49[3]*100:.1f}%  "
          f"R@5={recalls_49[5]*100:.1f}%  R@10={recalls_49[10]*100:.1f}%  "
          f"pairs={n_pairs_49}")
    print(f"  ⚠️ 正例ペア {n_pairs_49} 件を 49d baseline で確定。全条件で固定使用。")

    # === [3] トポロジー特徴量 (v2, 26d) ===
    print(f"\n[3] トポロジー特徴量")
    topo_mat, topo_names = build_structural_matrix(metadata)

    # === [4] 官能基発見 ===
    print(f"\n[4] 官能基発見")
    classified_seqs = [classify_sequence(m.get("ccl_expr", "")) for m in metadata]
    print(f"  部分列抽出 (len={args.min_len}-{args.max_len}, min_freq={args.min_freq})...")
    subseq_indices = extract_subsequences(
        classified_seqs,
        min_len=args.min_len,
        max_len=args.max_len,
        min_freq=args.min_freq,
    )
    print(f"  候補: {len(subseq_indices):,} 種 (freq≥{args.min_freq})")

    # 正例ペア (49d baseline ベース)
    sim_49 = normed_49 @ normed_49.T
    np.fill_diagonal(sim_49, -np.inf)
    disc_pairs = find_positive_pairs(sim_49, cap=3000, max_pairs=1000)
    print(f"  正例ペア: {len(disc_pairs)}")

    if not disc_pairs:
        print("  ⚠️ 正例ペアなし。データを確認してください。")
        sys.exit(1)

    enrichment_results = compute_enrichment(subseq_indices, disc_pairs, N)
    effective = [r for r in enrichment_results if r["enrichment"] > 1.0]
    print(f"  enrichment > 1.0: {len(effective)} / {len(enrichment_results)}")
    if effective:
        for i, r in enumerate(effective[:5]):
            print(f"    top-{i+1}: {r['subseq']} (enrich={r['enrichment']:.1f}, freq={r['freq']})")

    # === [5] 最長ユニークパターンフィルタ ===
    print(f"\n[5] 最長ユニークパターンフィルタ (collinearity 防止)")
    max_k = max(args.top_k_list)
    candidates = [r["subseq"] for r in effective[:args.max_candidates]]

    # 余裕を持って max_k+10 を要求
    all_filtered = longest_unique_pattern_filter(candidates, top_k=max_k + 10)
    print(f"  候補 {len(candidates)} → フィルタ後 {len(all_filtered)} (部分文字列関係を除去)")

    # フィルタ後 top-10 の詳細
    print(f"  フィルタ後 top-10:")
    for i, p in enumerate(all_filtered[:10]):
        enrich = next((r["enrichment"] for r in effective if r["subseq"] == p), 0.0)
        freq = next((r["freq"] for r in effective if r["subseq"] == p), 0)
        print(f"    {i+1:>2}. [{enrich:>6.1f}x, n={freq:>4}] {p}")

    if len(all_filtered) < min(args.top_k_list):
        print(f"  ⚠️ フィルタ後パターン不足 ({len(all_filtered)})。--max-candidates を増やしてください。")

    # === [6] 実験 ===
    print(f"\n[6] 実験")
    results = {}

    # S0: 49d baseline
    results["S0: 49d"] = {
        "dims": 49, "recalls": recalls_49, "n_pairs": n_pairs_49,
    }

    # S4v2: 49d + topo (v2 best)
    print(f"\n  ─── S4v2: 49d + topo ───")
    base_75d = np.hstack([raw_49d, topo_mat])
    normed_v2 = normalize(base_75d)
    rc_v2, np_v2, as_v2, _ = compute_self_recall(normed_v2, fixed_pairs=fixed_pairs_49)
    print(f"  {base_75d.shape[1]}d | R@1={rc_v2[1]*100:.1f}%  "
          f"R@3={rc_v2[3]*100:.1f}%  R@5={rc_v2[5]*100:.1f}%  "
          f"R@10={rc_v2[10]*100:.1f}%  pairs={np_v2}")
    results[f"S4v2: 49d+topo ({base_75d.shape[1]}d)"] = {
        "dims": base_75d.shape[1], "recalls": rc_v2, "n_pairs": np_v2,
    }

    # Sv3_K: 49d + topo + top-K fg
    for k in sorted(args.top_k_list):
        selected_k = all_filtered[:k]
        actual_k = len(selected_k)
        if actual_k == 0:
            print(f"\n  ─── Sv3_{k}: スキップ (パターン不足) ───")
            continue

        print(f"\n  ─── Sv3_{k}: 49d + topo + {actual_k} fg ───")
        fg_mat = build_fg_binary_matrix(metadata, selected_k)

        # カバレッジ診断
        n_covered = int(np.sum(fg_mat.sum(axis=1) > 0))
        coverage = n_covered / N
        mean_active = float(np.mean(fg_mat.sum(axis=1)))
        print(f"  カバレッジ: {coverage:.1%} ({n_covered}/{N} 関数が ≥1 官能基を持つ)")
        print(f"  平均アクティブ官能基数: {mean_active:.2f}")

        # variance 診断 (0 分散の官能基は除外検討)
        var = np.var(fg_mat, axis=0)
        n_zero_var = int(np.sum(var < 1e-10))
        if n_zero_var > 0:
            print(f"  ⚠️ 分散ゼロの官能基: {n_zero_var}/{actual_k} → 正規化で除外される")

        combined = np.hstack([raw_49d, topo_mat, fg_mat])
        normed = normalize(combined)
        rc, np_, as_, _ = compute_self_recall(normed, fixed_pairs=fixed_pairs_49)
        dims = combined.shape[1]
        print(f"  {dims}d | R@1={rc[1]*100:.1f}%  R@3={rc[3]*100:.1f}%  "
              f"R@5={rc[5]*100:.1f}%  R@10={rc[10]*100:.1f}%  pairs={np_}")

        delta_r10 = rc[10] - rc_v2[10]
        delta_r1 = rc[1] - rc_v2[1]
        print(f"  vs S4v2: R@1 Δ={delta_r1*100:+.1f}pp  R@10 Δ={delta_r10*100:+.1f}pp")

        results[f"Sv3_{k}: 49d+topo+{actual_k}fg ({dims}d)"] = {
            "dims": dims, "recalls": rc, "n_pairs": np_,
        }

    # === [7] 比較テーブル ===
    print(f"\n{'=' * 70}")
    print("  比較テーブル")
    print(f"{'=' * 70}")
    header = f"{'条件':<48} {'d':>4} {'R@1':>6} {'R@3':>6} {'R@5':>6} {'R@10':>6}"
    print(header)
    print("─" * 78)

    # v2 参考値
    print(f"{'(v1 ref) S5: 49d+all':<48} {'171':>4} {'3.2%':>6} {'7.4%':>6} {'12.0%':>6} {'20.4%':>6}")
    print(f"{'(v2 ref) S4: 49d+topo':<48} {'75':>4} {'6.2%':>6} {'--':>6} {'--':>6} {'29.4%':>6}")

    for name, r in results.items():
        rc = r["recalls"]
        mark = ""
        if "Sv3" in name:
            if rc.get(10, 0) > rc_v2.get(10, 0) + 0.005:
                mark = " ✅"
            elif rc.get(10, 0) < rc_v2.get(10, 0) - 0.005:
                mark = " ❌"
            else:
                mark = " ⚠️"
        print(f"{name:<48} {r['dims']:>4} "
              f"{rc.get(1,0)*100:>5.1f}% {rc.get(3,0)*100:>5.1f}% "
              f"{rc.get(5,0)*100:>5.1f}% {rc.get(10,0)*100:>5.1f}%{mark}")

    # === [8] 判定 ===
    print(f"\n{'=' * 70}")
    print("  判定")
    print(f"{'=' * 70}")

    # Best overall
    best_name_r10 = max(results, key=lambda k: results[k]["recalls"].get(10, 0))
    best_r10 = results[best_name_r10]["recalls"].get(10, 0)
    best_r1 = results[best_name_r10]["recalls"].get(1, 0)
    v2_r10 = rc_v2.get(10, 0)
    v2_r1 = rc_v2.get(1, 0)

    print(f"\n  Best (R@10): {best_name_r10}")
    print(f"    R@1={best_r1*100:.1f}%  R@10={best_r10*100:.1f}%")
    print(f"    vs S4v2: R@1 Δ={best_r1*100 - v2_r1*100:+.1f}pp  "
          f"R@10 Δ={best_r10*100 - v2_r10*100:+.1f}pp")

    if best_r10 > v2_r10 + 0.005:
        print(f"  → ✅ v2 best (S4v2) を超えた!")
        print(f"     化学的解釈: CTRL+FUSE 官能基が 49d では捕捉できない情報を付加")
    elif best_r10 > v2_r10 - 0.005:
        print(f"  → ⚠️ INCONCLUSIVE (±0.5pp 以内)")
        print(f"     化学的解釈: binary encoding では情報損失が大きい可能性。連続値化を検討")
    else:
        print(f"  → ❌ v2 baseline 未達")
        print(f"     化学的解釈: 官能基 binary features が 49d+topo と独立した情報を持たない")
        print(f"     次の手: (1) 連続値 (freq/coverage) に変換, (2) 官能基の組合せ特徴")

    print(f"\n📍 v3 実験完了。")
    print(f"🕳️ 未検証:")
    print(f"  - 官能基 weight (binary→連続値: freq / avg_sim_in)")
    print(f"  - 官能基の組合せ特徴 (CTRL+FUSE × 制御フロー)")
    print(f"  - 予測 P1-P4 の検証 (multi_scale_chemistry_isomorphism.md §7)")
    print(f"→ 次: 結果を多_scale_chemistry_isomorphism.md §7 の予測 P1-P4 に照合")


if __name__ == "__main__":
    main()
