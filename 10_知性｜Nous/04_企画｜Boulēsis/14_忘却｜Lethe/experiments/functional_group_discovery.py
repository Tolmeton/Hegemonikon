"""官能基発見スクリプト — データ駆動の CCL 部分構造発見

§8.4 (v2) のデータ駆動手順を実装:
  1. CCL テキスト → 分類済みトークン列 (§8.2 の原子/結合分類)
  2. 長さ 3-7 の部分列を全抽出
  3. 出現頻度 ≥ 50 でフィルタ
  4. 弁別力検定 (正例ペアの enrichment)
  5. 官能基の特性計算 (§8.5)

Usage:
  python functional_group_discovery.py
  python functional_group_discovery.py --min-freq 30 --min-len 3 --max-len 7
"""

import pickle
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

_HGK_ROOT = Path(__file__).resolve().parents[4]
_PKL_PATH = _HGK_ROOT / "30_記憶｜Mneme" / "02_索引｜Index" / "code_ccl_features.pkl"

# ============================================================
# §1 トークン分類 (§8.2 の原子/結合分類に基づく)
# ============================================================

# 結合 (演算子) — 原子間を接続する
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
# 修飾子 (原子でも結合でもない)
MODIFIERS = {"^", "\\", "+", "-", "!"}
CONTROL_PREFIXES = ("F:", "I:", "EI:", "E:", "C:", "R:", "V:", "W:", "L:")


def classify_token(token: str) -> str:
    """§8.2 の原子/結合分類。"""
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
# §2 部分列抽出と頻度フィルタ
# ============================================================

def extract_subsequences(
    classified_seqs: list[list[str]],
    min_len: int = 3,
    max_len: int = 7,
    min_freq: int = 50,
) -> dict[str, list[int]]:
    """全 CCL テキストから部分列を抽出し、頻度でフィルタ。

    Returns: {subsequence_string: [function_indices_containing_it]}
    """
    print(f"  部分列抽出中 (len={min_len}-{max_len}, min_freq={min_freq})...")

    subseq_to_indices: dict[str, set[int]] = defaultdict(set)

    for idx, seq in enumerate(classified_seqs):
        seen_in_this_func: set[str] = set()
        for n in range(min_len, min(max_len + 1, len(seq) + 1)):
            for i in range(len(seq) - n + 1):
                subseq = " ".join(seq[i:i + n])
                if subseq not in seen_in_this_func:
                    seen_in_this_func.add(subseq)
                    subseq_to_indices[subseq].add(idx)

    # 頻度フィルタ
    filtered = {
        subseq: sorted(indices)
        for subseq, indices in subseq_to_indices.items()
        if len(indices) >= min_freq
    }

    print(f"  全部分列: {len(subseq_to_indices):,} 種")
    print(f"  freq>={min_freq}: {len(filtered):,} 種")

    return filtered


# ============================================================
# §3 弁別力検定
# ============================================================

def compute_discriminative_power(
    subseq_indices: dict[str, list[int]],
    sim_matrix: np.ndarray,
    positive_pairs: list[tuple[int, int]],
    n_total: int,
) -> list[dict]:
    """各候補官能基の弁別力を検定。

    弁別力 = 正例ペアの enrichment:
      P(both in group | positive pair) / P(both in group | random pair)
    enrichment > 1 → この官能基を共有する関数は類似しやすい
    """
    print(f"  弁別力検定中 ({len(subseq_indices)} 候補, "
          f"{len(positive_pairs)} 正例ペア)...")

    results = []
    for subseq, indices in subseq_indices.items():
        idx_set = frozenset(indices)
        n_in = len(idx_set)
        n_out = n_total - n_in

        if n_in < 10 or n_out < 10:
            continue

        # 正例ペアのうち、両方がグループ内にある割合
        pairs_both_in = sum(
            1 for a, b in positive_pairs if a in idx_set and b in idx_set
        )

        # 期待値 (ランダム)
        p_in = n_in / n_total
        expected = p_in * p_in * len(positive_pairs)
        enrichment = pairs_both_in / expected if expected >= 1 else float(pairs_both_in)

        # グループ内の平均類似度 (サンプリング)
        rng = np.random.default_rng(42)
        sample_n = min(n_in, 300)
        sample_idx = (
            rng.choice(indices, sample_n, replace=False)
            if n_in > sample_n
            else np.array(indices)
        )
        sub_sim = sim_matrix[np.ix_(sample_idx, sample_idx)]
        triu = np.triu_indices(len(sample_idx), k=1)
        avg_sim_in = float(np.mean(sub_sim[triu])) if len(triu[0]) > 0 else 0.0

        results.append({
            "subseq": subseq,
            "freq": n_in,
            "coverage": n_in / n_total,
            "enrichment": enrichment,
            "pairs_both_in": pairs_both_in,
            "expected": expected,
            "avg_sim_in": avg_sim_in,
        })

    results.sort(key=lambda r: -r["enrichment"])
    return results


# ============================================================
# §4 官能基の特性計算 (§8.5 の分子特性を部分構造に適用)
# ============================================================

def compute_properties(subseq: str) -> dict[str, float]:
    """発見された官能基の化学的特性を計算。"""
    tokens = subseq.split()
    n = len(tokens)
    bond_types = {"COMPOSE", "FUSE", "SELECT", "COND", "SEQ"}
    atoms = [t for t in tokens if t not in bond_types]
    bonds = [t for t in tokens if t in bond_types]

    n_ext = atoms.count("EXT")
    n_int = atoms.count("INT")
    n_ctrl = atoms.count("CTRL")
    n_err = atoms.count("ERR")
    n_fuse = bonds.count("FUSE")
    unique_bonds = len(set(bonds))

    return {
        "polarity": (n_ext - n_int) / max(len(atoms), 1),
        "reactivity": (n_ctrl + n_err) / max(len(atoms), 1),
        "stability": 1.0 if n_ctrl > 0 else 0.0,
        "complexity": unique_bonds / max(len(bonds), 1),
        "bond_energy": n_fuse / max(len(bonds), 1),
        "length": n,
    }


# ============================================================
# §5 基盤ユーティリティ
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


def find_positive_pairs(
    sim_matrix: np.ndarray, cap: int = 3000, max_pairs: int = 1000,
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


# ============================================================
# §6 メイン
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="データ駆動の CCL 官能基発見")
    parser.add_argument("--min-freq", type=int, default=50)
    parser.add_argument("--min-len", type=int, default=3)
    parser.add_argument("--max-len", type=int, default=7)
    parser.add_argument("--top-k", type=int, default=30)
    args = parser.parse_args()

    print("=" * 70)
    print("CCL 官能基発見 — §8.4 データ駆動パイプライン")
    print("=" * 70)

    # --- [1] Load data ---
    print(f"\n[1] データ読込: {_PKL_PATH.name}")
    with open(_PKL_PATH, "rb") as f:
        data = pickle.load(f)
    features = np.array(data["vectors"])  # (N, 49)
    metadata = data["metadata"]
    N = features.shape[0]
    print(f"  {N} 関数, {features.shape[1]}d")

    # --- [2] Classify tokens ---
    print(f"\n[2] トークン分類 (§8.2 原子/結合)")
    classified_seqs = [classify_sequence(m.get("ccl_expr", "")) for m in metadata]

    all_tokens = [t for seq in classified_seqs for t in seq]
    token_counts = Counter(all_tokens)
    print(f"  全トークン (フィルタ後): {len(all_tokens):,}")
    print(f"  分類分布:")
    for tok, cnt in token_counts.most_common():
        print(f"    {tok:<12} {cnt:>8,} ({cnt / len(all_tokens) * 100:5.1f}%)")

    # --- [3] Extract subsequences ---
    print(f"\n[3] 部分列抽出と頻度フィルタ")
    subseq_indices = extract_subsequences(
        classified_seqs,
        min_len=args.min_len,
        max_len=args.max_len,
        min_freq=args.min_freq,
    )
    if not subseq_indices:
        print("  ⚠️ 候補なし。--min-freq を下げてください。")
        sys.exit(0)

    # --- [4] 49d similarity matrix ---
    print(f"\n[4] 49d baseline 類似度行列")
    normed = normalize(features)
    sim_matrix = normed @ normed.T
    np.fill_diagonal(sim_matrix, -np.inf)
    print(f"  行列: {sim_matrix.shape}")

    # --- [5] Positive pairs ---
    print(f"\n[5] 正例ペア検出")
    positive_pairs = find_positive_pairs(sim_matrix)
    print(f"  正例ペア: {len(positive_pairs)}")

    if not positive_pairs:
        print("  ⚠️ 正例ペアが見つかりません。")
        sys.exit(1)

    # --- [6] Discriminative power ---
    print(f"\n[6] 弁別力検定")
    results = compute_discriminative_power(
        subseq_indices, sim_matrix, positive_pairs, N,
    )
    print(f"  有効候補: {len(results)}")

    # --- Report: top enrichment ---
    effective = [r for r in results if r["enrichment"] > 1.0]
    top_k = min(args.top_k, len(results))

    print(f"\n{'=' * 70}")
    print(f"発見された官能基 (top-{top_k}, enrichment 順)")
    print(f"{'=' * 70}")
    hdr = f"{'#':>3} {'部分列':<45} {'freq':>5} {'cov':>5} {'enrich':>7} {'pairs':>5} {'sim':>6}"
    print(hdr)
    print("-" * len(hdr))
    for i, r in enumerate(results[:top_k]):
        print(
            f"{i + 1:>3} {r['subseq']:<45} {r['freq']:>5} "
            f"{r['coverage']:>5.1%} {r['enrichment']:>7.2f} "
            f"{r['pairs_both_in']:>5} {r['avg_sim_in']:>6.3f}"
        )

    # --- Report: properties ---
    n_props = min(15, top_k)
    print(f"\n{'=' * 70}")
    print(f"官能基の特性 (top-{n_props})")
    print(f"{'=' * 70}")
    phdr = (f"{'#':>3} {'部分列':<40} {'polar':>6} {'react':>6} "
            f"{'stab':>5} {'cmplx':>6} {'Ebond':>6}")
    print(phdr)
    print("-" * len(phdr))
    for i, r in enumerate(results[:n_props]):
        p = compute_properties(r["subseq"])
        print(
            f"{i + 1:>3} {r['subseq']:<40} {p['polarity']:>+6.2f} "
            f"{p['reactivity']:>6.2f} {p['stability']:>5.1f} "
            f"{p['complexity']:>6.2f} {p['bond_energy']:>6.2f}"
        )

    # --- Hypothesis check ---
    print(f"\n{'=' * 70}")
    print("§8.4 仮説官能基との照合")
    print(f"{'=' * 70}")
    hypotheses = {
        "外部取込": "EXT COMPOSE FUNC COMPOSE INT",
        "検証ゲート": "CTRL COMPOSE CTRL",
        "蓄積ループ": "CTRL COMPOSE INT COMPOSE FUNC",
        "単純変換": "FUNC COMPOSE METH",
        "融合変換": "INT FUSE EXT COMPOSE FUNC",
    }
    for name, pattern in hypotheses.items():
        if pattern in subseq_indices:
            freq = len(subseq_indices[pattern])
            match = next((r for r in results if r["subseq"] == pattern), None)
            if match:
                tag = "✅" if match["enrichment"] > 1.0 else "❌"
                print(f"  {name:<12} [{pattern}]: "
                      f"freq={freq}, enrich={match['enrichment']:.2f} → {tag}")
            else:
                print(f"  {name:<12} [{pattern}]: freq={freq}, enrich=N/A")
        else:
            print(f"  {name:<12} [{pattern}]: 🟡 freq<{args.min_freq}")

    # --- Summary ---
    print(f"\n{'=' * 70}")
    print("Summary")
    print(f"{'=' * 70}")
    print(f"  全部分列候補: {len(subseq_indices):,}")
    print(f"  弁別力あり (enrichment > 1.0): {len(effective)} / {len(results)}")
    if effective:
        best = effective[0]
        print(f"  最高 enrichment: {best['subseq']} "
              f"(enrich={best['enrichment']:.2f}, freq={best['freq']})")

    print(f"\n📍 発見フェーズ完了。")
    print(f"🕳️ v3 実験: 上位官能基を binary feature 化 → 49d+topo に結合")
    print(f"→ 次: functional_group_features.py (官能基→特徴量変換)")


if __name__ == "__main__":
    main()
