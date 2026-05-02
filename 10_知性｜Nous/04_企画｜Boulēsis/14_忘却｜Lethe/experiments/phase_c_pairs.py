#!/usr/bin/env python3
# PROOF: [L2/実験] <- Phase C 訓練データ生成パイプライン
"""Phase C: 49d 特徴量ベクトルによる Positive/Negative ペア生成 + JSONL 変換

既存の p3a_v2_dataset.py (CCL 文字列 Levenshtein ベース) を 49d pkl インデックスの
コサイン類似度ベースに拡張。Phase C Structural Attention Layer の訓練データ生成。

設計方針:
  - 既存 code_ccl_features.pkl (49d, 11,768 ベクトル) を直接活用
  - Z-score 正規化済みコサイン類似度でペアを判定
  - Hard negatives: cosine > 0.8 かつ AST TED > 0.5 (構造的に似て見えるが違う)
  - JSONL 出力: TinyLlama 1.1B fine-tuning 用の入力形式

Usage:
  python phase_c_pairs.py                    # デフォルト生成
  python phase_c_pairs.py --stats            # 既存データの統計表示
  python phase_c_pairs.py --n-positive 500   # 正例500ペア
"""

# PURPOSE: Phase C 訓練用 Positive/Negative ペア生成 + JSONL 変換

import sys
import os
import json
import random
import argparse
import pickle
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np

# パス設定
_SCRIPT_DIR = Path(__file__).parent
_HGK_ROOT = _SCRIPT_DIR.parent.parent.parent.parent
_MEKHANE_SRC = _HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"

# pkl パス (mekhane/paths.py の CODE_CCL_FEATURES_INDEX に対応)
# INDICES_DIR = MNEME_INDEX = HGK_ROOT / "30_記憶｜Mneme" / "02_索引｜Index"
_DEFAULT_PKL = _HGK_ROOT / "30_記憶｜Mneme" / "02_索引｜Index" / "code_ccl_features.pkl"


# ============================================================
# §0. pkl ロード + Z-score 正規化
# ============================================================

# PURPOSE: pkl インデックスをロードし Z-score 正規化行列を構築
def load_index(pkl_path: Path) -> tuple[np.ndarray, list[dict]]:
    """pkl インデックスから (正規化行列, メタデータリスト) を返す。

    Returns:
        matrix_z: (N, 49) Z-score 正規化済みベクトル行列
        metadata: 各ベクトルに対応するメタデータ辞書のリスト
    """
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)

    vectors = data["vectors"]  # list[np.ndarray (49,)]
    metadata = data["metadata"]  # list[dict]

    raw = np.vstack(vectors)  # (N, 49)
    mean = np.mean(raw, axis=0)
    std = np.std(raw, axis=0)
    std = np.where(std > 1e-10, std, 1.0)  # ゼロ除算回避

    matrix_z = (raw - mean) / std  # (N, 49)

    # L2 正規化 (コサイン類似度の前提)
    norms = np.linalg.norm(matrix_z, axis=1, keepdims=True)
    norms = np.where(norms > 1e-10, norms, 1.0)
    matrix_z = matrix_z / norms

    return matrix_z, metadata


# ============================================================
# §1. ペアデータ構造
# ============================================================

# PURPOSE: 訓練ペアデータ
@dataclass
class TrainingPair:
    """Phase C 訓練用ペア。"""
    pair_id: str
    is_positive: bool          # 構造的類似 (cosine > threshold)
    pair_type: str             # positive / easy_neg / hard_neg_cosine / hard_neg_dir
    cosine_similarity: float   # 49d Z-score 正規化後のコサイン類似度
    # — 関数 A —
    func_a_file: str
    func_a_name: str
    func_a_ccl: str
    func_a_source: str         # ソースコード (raw)
    # — 関数 B —
    func_b_file: str
    func_b_name: str
    func_b_ccl: str
    func_b_source: str


# ============================================================
# §2. ペア生成エンジン (サンプリングベース — N×N 全行列なし)
# ============================================================

# PURPOSE: 行単位コサイン類似度 (L2 正規化済みなので内積)
def cosine_row(matrix_z: np.ndarray, i: int) -> np.ndarray:
    """ベクトル i と全ベクトルの類似度を返す (1, N)。"""
    return matrix_z @ matrix_z[i]


# PURPOSE: 正例/負例ペアを生成 (サンプリングベース)
def generate_pairs(
    matrix_z: np.ndarray,
    metadata: list[dict],
    n_positive: int = 200,
    n_easy_neg: int = 67,
    n_hard_neg_cos: int = 67,
    n_hard_neg_dir: int = 66,
    seed: int = 42,
    pos_threshold: float = 0.85,
    hard_neg_cos_min: float = 0.60,
    hard_neg_cos_max: float = 0.80,
    easy_neg_cos_max: float = 0.30,
) -> list[TrainingPair]:
    """49d コサイン類似度ベースのペア生成 (サンプリング方式)。

    N×N 全行列を持たず、行単位のコサイン計算 + ランダムサンプリングで
    O(N×k) に計算量を削減。

    4種ペア:
      positive:         cosine >= pos_threshold (構造一致)
      easy_neg:         cosine <= easy_neg_cos_max (完全に異なる)
      hard_neg_cosine:  hard_neg_cos_min < cosine < hard_neg_cos_max (中間帯)
      hard_neg_dir:     同一ディレクトリ, cosine < pos_threshold
    """
    rng = random.Random(seed)
    N = len(metadata)
    pairs: list[TrainingPair] = []
    used: set[tuple[int, int]] = set()
    pair_counter = 0

    # float32 に変換 (メモリ + 計算速度)
    mat32 = matrix_z.astype(np.float32)

    def _cosine(i: int, j: int) -> float:
        """2ベクトルのコサイン (L2 正規化済み → 内積)。"""
        return float(mat32[i] @ mat32[j])

    def _make_pair(i: int, j: int, pair_type: str, is_positive: bool, cos_val: float) -> TrainingPair:
        nonlocal pair_counter
        pair_counter += 1
        mi, mj = metadata[i], metadata[j]
        return TrainingPair(
            pair_id=f"PC_{pair_counter:05d}",
            is_positive=is_positive,
            pair_type=pair_type,
            cosine_similarity=cos_val,
            func_a_file=mi.get("file_path", ""),
            func_a_name=mi.get("function_name", ""),
            func_a_ccl=mi.get("ccl_expr", ""),
            func_a_source=mi.get("source", mi.get("code", "")),
            func_b_file=mj.get("file_path", ""),
            func_b_name=mj.get("function_name", ""),
            func_b_ccl=mj.get("ccl_expr", ""),
            func_b_source=mj.get("source", mj.get("code", "")),
        )

    def _try_add(i: int, j: int, pair_type: str, is_positive: bool, cos_val: float) -> bool:
        key = (min(i, j), max(i, j))
        if key in used or i == j:
            return False
        used.add(key)
        pairs.append(_make_pair(i, j, pair_type, is_positive, cos_val))
        return True

    # --- 正例: pos_threshold <= cosine < 0.999 ---
    # cosine=1.0 は同一 CCL パターン (49d 量子化で完全一致) → 訓練信号なし → 除外
    POS_UPPER = 0.999  # 完全一致除外閾値
    print(f"\n📍 正例ペア生成 (目標: {n_positive}, cosine ∈ [{pos_threshold}, {POS_UPPER}))...", flush=True)
    # アンカーをサンプリングし、各アンカーの近傍を行単位で計算
    anchor_sample = rng.sample(range(N), min(500, N))
    pos_candidates: list[tuple[float, int, int]] = []
    for idx, i in enumerate(anchor_sample):
        sims = mat32 @ mat32[i]  # (N,) — 行単位コサイン
        # threshold 以上 & 完全一致未満 & 自分以外
        mask = (sims >= pos_threshold) & (sims < POS_UPPER) & (np.arange(N) != i)
        for j in np.where(mask)[0]:
            # CCL 式が完全に同一なペアも除外 (構造的に同一 → 訓練信号なし)
            ccl_a = metadata[i].get("ccl_expr", "")
            ccl_b = metadata[int(j)].get("ccl_expr", "")
            if ccl_a != ccl_b:
                pos_candidates.append((float(sims[j]), i, int(j)))
        if (idx + 1) % 100 == 0:
            print(f"  ... {idx+1}/{len(anchor_sample)} アンカー走査済 (候補: {len(pos_candidates)})", flush=True)

    # 多様性重視: threshold 昇順ソート (cosine が低めの「本当に似ているが異なる」ペアを優先)
    pos_candidates.sort(key=lambda x: x[0])
    pos_count = 0
    for sim, i, j in pos_candidates:
        if pos_count >= n_positive:
            break
        if _try_add(i, j, "positive", True, sim):
            pos_count += 1
    print(f"  → {pos_count} 正例ペア生成 (候補: {len(pos_candidates)})", flush=True)

    # --- Easy Negative: cosine <= easy_neg_cos_max ---
    print(f"📍 Easy Negative (目標: {n_easy_neg}, max_cos: {easy_neg_cos_max})...", flush=True)
    easy_count = 0
    for _ in range(n_easy_neg * 20):
        if easy_count >= n_easy_neg:
            break
        i = rng.randint(0, N - 1)
        j = rng.randint(0, N - 1)
        if i == j:
            continue
        cos = _cosine(i, j)
        if cos <= easy_neg_cos_max:
            if _try_add(i, j, "easy_neg", False, cos):
                easy_count += 1
    print(f"  → {easy_count} easy negative 生成", flush=True)

    # --- Hard Negative (コサイン中間帯) ---
    print(f"📍 Hard Negative コサイン ({n_hard_neg_cos}, range: [{hard_neg_cos_min}, {hard_neg_cos_max}])...", flush=True)
    hard_sample = rng.sample(range(N), min(300, N))
    hard_cos_candidates: list[tuple[float, int, int]] = []
    for i in hard_sample:
        sims = mat32 @ mat32[i]
        mask = (sims >= hard_neg_cos_min) & (sims < hard_neg_cos_max) & (np.arange(N) != i)
        for j in np.where(mask)[0]:
            hard_cos_candidates.append((float(sims[j]), i, int(j)))
    rng.shuffle(hard_cos_candidates)

    hard_cos_count = 0
    for sim, i, j in hard_cos_candidates:
        if hard_cos_count >= n_hard_neg_cos:
            break
        if _try_add(i, j, "hard_neg_cosine", False, sim):
            hard_cos_count += 1
    print(f"  → {hard_cos_count} hard negative (cosine) 生成", flush=True)

    # --- Hard Negative (同一ディレクトリ) ---
    print(f"📍 Hard Negative ディレクトリ ({n_hard_neg_dir})...", flush=True)
    from collections import defaultdict
    dir_groups: dict[str, list[int]] = defaultdict(list)
    for idx, m in enumerate(metadata):
        dir_name = str(Path(m.get("file_path", "")).parent)
        dir_groups[dir_name].append(idx)

    hard_dir_count = 0
    for dir_name, group in dir_groups.items():
        if hard_dir_count >= n_hard_neg_dir:
            break
        if len(group) < 2:
            continue
        rng.shuffle(group)
        for a_idx in range(0, len(group) - 1):
            if hard_dir_count >= n_hard_neg_dir:
                break
            i, j = group[a_idx], group[a_idx + 1]
            cos = _cosine(i, j)
            # 同ディレクトリだが構造的に異なる (cosine < pos_threshold)
            if cos < pos_threshold:
                if _try_add(i, j, "hard_neg_dir", False, cos):
                    hard_dir_count += 1
    print(f"  → {hard_dir_count} hard negative (dir) 生成", flush=True)

    return pairs


# ============================================================
# §3. JSONL 出力 (C-pre-7)
# ============================================================

# PURPOSE: Contrastive Learning 用 JSONL 形式に変換
def pairs_to_jsonl(
    pairs: list[TrainingPair],
    output_path: Path,
    include_source: bool = True,
) -> None:
    """ペアを JSONL 形式で出力。

    各行の構造:
    {
        "anchor": "ソースコード A",
        "positive": "ソースコード B" (is_positive=True の場合),
        "negative": "ソースコード B" (is_positive=False の場合),
        "label": 1 or 0,
        "cosine_49d": float,
        "pair_type": str,
        "metadata": { ... }
    }
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for p in pairs:
            record = {
                "anchor": p.func_a_source if include_source else p.func_a_ccl,
                "candidate": p.func_b_source if include_source else p.func_b_ccl,
                "label": 1 if p.is_positive else 0,
                "cosine_49d": round(p.cosine_similarity, 4),
                "pair_type": p.pair_type,
                "metadata": {
                    "pair_id": p.pair_id,
                    "func_a": f"{p.func_a_file}::{p.func_a_name}",
                    "func_b": f"{p.func_b_file}::{p.func_b_name}",
                    "anchor_ccl": p.func_a_ccl[:200],
                    "candidate_ccl": p.func_b_ccl[:200],
                },
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"\n💾 JSONL 保存: {output_path} ({len(pairs)} 行)")


# PURPOSE: CCL のみの JSONL (ソースコードなし、軽量)
def pairs_to_ccl_jsonl(
    pairs: list[TrainingPair],
    output_path: Path,
) -> None:
    """CCL 式のみの JSONL。軽量での実験用。"""
    with open(output_path, "w", encoding="utf-8") as f:
        for p in pairs:
            record = {
                "anchor_ccl": p.func_a_ccl,
                "candidate_ccl": p.func_b_ccl,
                "label": 1 if p.is_positive else 0,
                "cosine_49d": round(p.cosine_similarity, 4),
                "pair_type": p.pair_type,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"💾 CCL JSONL 保存: {output_path} ({len(pairs)} 行)")


# ============================================================
# §4. 統計表示
# ============================================================

# PURPOSE: データセットの統計を表示
def print_stats(pairs: list[TrainingPair]) -> None:
    """ペアデータの統計を表示。"""
    print(f"\n{'='*60}")
    print(f"  Phase C Training Pairs — 統計")
    print(f"{'='*60}")
    print(f"  合計: {len(pairs)} ペア")
    print(f"  正例: {sum(1 for p in pairs if p.is_positive)}")
    print(f"  負例: {sum(1 for p in pairs if not p.is_positive)}")

    for ptype in ["positive", "easy_neg", "hard_neg_cosine", "hard_neg_dir"]:
        subset = [p for p in pairs if p.pair_type == ptype]
        if not subset:
            continue
        cos_vals = [p.cosine_similarity for p in subset]
        print(f"\n  {ptype} ({len(subset)} ペア):")
        print(f"    cosine: mean={np.mean(cos_vals):.3f}, "
              f"min={min(cos_vals):.3f}, max={max(cos_vals):.3f}, "
              f"std={np.std(cos_vals):.3f}")


# ============================================================
# §5. JSON メタデータ保存
# ============================================================

# PURPOSE: データセットの全メタデータを JSON で保存
def save_metadata(pairs: list[TrainingPair], output_path: Path) -> None:
    """ペアの全メタデータを JSON で保存。"""
    data = {
        "version": "phase_c_v1",
        "feature_dim": 49,
        "normalization": "z-score + L2",
        "n_pairs": len(pairs),
        "n_positive": sum(1 for p in pairs if p.is_positive),
        "n_negative": sum(1 for p in pairs if not p.is_positive),
        "pair_types": {
            t: sum(1 for p in pairs if p.pair_type == t)
            for t in ["positive", "easy_neg", "hard_neg_cosine", "hard_neg_dir"]
        },
        "cosine_stats": {
            "positive": {
                "mean": float(np.mean([p.cosine_similarity for p in pairs if p.is_positive])) if any(p.is_positive for p in pairs) else 0,
                "std": float(np.std([p.cosine_similarity for p in pairs if p.is_positive])) if any(p.is_positive for p in pairs) else 0,
            },
            "negative": {
                "mean": float(np.mean([p.cosine_similarity for p in pairs if not p.is_positive])) if any(not p.is_positive for p in pairs) else 0,
                "std": float(np.std([p.cosine_similarity for p in pairs if not p.is_positive])) if any(not p.is_positive for p in pairs) else 0,
            },
        },
    }
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"💾 メタデータ保存: {output_path}")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Phase C: 49d 特徴量ベースのペア生成 + JSONL 変換"
    )
    parser.add_argument(
        "--pkl", type=str, default=str(_DEFAULT_PKL),
        help=f"pkl インデックスのパス (default: {_DEFAULT_PKL})",
    )
    parser.add_argument(
        "--output-dir", "-o", type=str, default=str(_SCRIPT_DIR),
        help="出力ディレクトリ (default: experiments/)",
    )
    parser.add_argument(
        "--n-positive", type=int, default=200,
        help="正例ペア数 (default: 200)",
    )
    parser.add_argument(
        "--n-negative", type=int, default=200,
        help="負例ペア数合計 (default: 200, 3種均等)",
    )
    parser.add_argument(
        "--pos-threshold", type=float, default=0.85,
        help="正例判定コサイン閾値 (default: 0.85)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="乱数シード (default: 42)",
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="既存 JSONL の統計表示のみ",
    )
    parser.add_argument(
        "--no-source", action="store_true",
        help="ソースコードを含めない (CCL のみ)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    jsonl_path = output_dir / "phase_c_training.jsonl"
    ccl_jsonl_path = output_dir / "phase_c_training_ccl.jsonl"
    meta_path = output_dir / "phase_c_metadata.json"

    # --- 統計表示モード ---
    if args.stats:
        if jsonl_path.exists():
            pairs = []
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    d = json.loads(line)
                    pairs.append(TrainingPair(
                        pair_id=d["metadata"]["pair_id"],
                        is_positive=d["label"] == 1,
                        pair_type=d["pair_type"],
                        cosine_similarity=d["cosine_49d"],
                        func_a_file=d["metadata"]["func_a"].split("::")[0],
                        func_a_name=d["metadata"]["func_a"].split("::")[-1],
                        func_a_ccl=d["metadata"]["anchor_ccl"],
                        func_a_source=d.get("anchor", ""),
                        func_b_file=d["metadata"]["func_b"].split("::")[0],
                        func_b_name=d["metadata"]["func_b"].split("::")[-1],
                        func_b_ccl=d["metadata"]["candidate_ccl"],
                        func_b_source=d.get("candidate", ""),
                    ))
            print_stats(pairs)
        else:
            print(f"❌ {jsonl_path} が存在しません")
        return

    # --- pkl ロード ---
    pkl_path = Path(args.pkl)
    if not pkl_path.exists():
        print(f"❌ pkl not found: {pkl_path}")
        sys.exit(1)

    print(f"📂 pkl ロード: {pkl_path}")
    matrix_z, metadata = load_index(pkl_path)
    print(f"  → {matrix_z.shape[0]} ベクトル, {matrix_z.shape[1]}d")

    # --- ペア生成 ---
    n_neg = args.n_negative
    n_easy = n_neg // 3
    n_hard_cos = n_neg // 3
    n_hard_dir = n_neg - n_easy - n_hard_cos

    pairs = generate_pairs(
        matrix_z, metadata,
        n_positive=args.n_positive,
        n_easy_neg=n_easy,
        n_hard_neg_cos=n_hard_cos,
        n_hard_neg_dir=n_hard_dir,
        seed=args.seed,
        pos_threshold=args.pos_threshold,
    )

    # --- JSONL 出力 ---
    if not args.no_source:
        pairs_to_jsonl(pairs, jsonl_path)
    pairs_to_ccl_jsonl(pairs, ccl_jsonl_path)
    save_metadata(pairs, meta_path)
    print_stats(pairs)


if __name__ == "__main__":
    main()
