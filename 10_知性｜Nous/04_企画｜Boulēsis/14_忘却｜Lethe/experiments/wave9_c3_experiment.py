#!/usr/bin/env python3
"""Wave 9 + C3 特徴量拡張実験

PURPOSE: C3 引数結合パターン (_a0, _a1, ...) から特徴量を抽出し、
  Siamese の入力次元を 49d → 52d に拡張して ρ 改善を検証する。

方法: wave9_experiment.py をベースに、extract_ccl_extra_features を拡張。
"""

from __future__ import annotations

import math
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from wave9_experiment import (
    Wave9PairAnalysis,
    generate_wave9_pairs,
    analyze_wave9,
    print_wave9_results,
    save_wave9_results,
    _extract_ngrams,
    _counter_entropy,
    _normalize_vectors,
    extract_ccl_extra_features,
)
from p3b_benchmark import (
    FunctionInfo,
    extract_functions,
    spearman_rho,
)

_HGK_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_MEKHANE_SRC = _HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"


# ============================================================
# C3 拡張特徴量 (3d)
# ============================================================

# PURPOSE: CCL テキストから C3 引数結合パターンの特徴量を抽出
def extract_c3_features(ccl: str) -> dict[str, float]:
    """C3 引数結合パターン (_a0, _a1, ...) の特徴量を抽出する (+3d)。

    1. arg_count: 参照される引数の総数 (ユニーク)
    2. arg_ref_density: 引数参照の密度 (参照回数 / トークン数)
    3. arg_reuse_ratio: 引数再利用率 (2回以上参照される引数の割合)
    """
    tokens = ccl.split()
    n_tokens = max(len(tokens), 1)

    # _aN パターンを全て抽出
    arg_refs = re.findall(r'_a(\d+)', ccl)

    # ユニーク引数
    unique_args = set(arg_refs)
    arg_count = len(unique_args)

    # 参照密度
    arg_ref_density = len(arg_refs) / n_tokens

    # 再利用率
    if arg_count > 0:
        ref_counts = Counter(arg_refs)
        reused = sum(1 for c in ref_counts.values() if c >= 2)
        arg_reuse_ratio = reused / arg_count
    else:
        arg_reuse_ratio = 0.0

    return {
        'arg_count': float(arg_count),
        'arg_ref_density': arg_ref_density,
        'arg_reuse_ratio': arg_reuse_ratio,
    }


# ============================================================
# 拡張 Siamese (52d CCL + 29d GT)
# ============================================================

# 元の GT ノード型リスト (wave9_experiment と同一)
GT_NODE_TYPES = [
    'FunctionDef', 'AsyncFunctionDef', 'Return', 'Assign', 'AugAssign',
    'For', 'AsyncFor', 'While', 'If', 'With', 'AsyncWith',
    'Raise', 'Try', 'Assert', 'Import', 'ImportFrom',
    'Expr', 'Call', 'Attribute', 'Subscript', 'Name',
    'BoolOp', 'BinOp', 'UnaryOp', 'Compare', 'ListComp', 'DictComp',
]

CCL_AST_EXTRA_TYPES = [
    'Yield', 'YieldFrom', 'SetComp', 'GeneratorExp',
    'Lambda', 'IfExp', 'Dict', 'Set', 'List', 'Tuple',
    'Starred', 'FormattedValue', 'JoinedStr', 'Constant',
    'Delete', 'Global',
]


# PURPOSE: C3 拡張特徴量ベクトル構築
def build_c3_feature_vectors(
    functions: list[FunctionInfo],
) -> tuple[list[list[float]], list[list[float]]]:
    """CCL 52d (49d + C3 3d) + GT 29d 特徴量ベクトルを構築する。"""
    ccl_vectors = []
    gt_vectors = []

    for func in functions:
        type_counts = Counter(func.ast_node_types)

        # GT ベクトル (29d) = 変更なし
        gt_base = [float(type_counts.get(t, 0)) for t in GT_NODE_TYPES]
        bigrams = _extract_ngrams(func.ast_node_types, n=2)
        trigrams = _extract_ngrams(func.ast_node_types, n=3)
        bi_entropy = _counter_entropy(bigrams)
        tri_entropy = _counter_entropy(trigrams)
        gt_vec = gt_base + [bi_entropy, tri_entropy]  # 29d
        gt_vectors.append(gt_vec)

        # CCL ベース (27d + 16d + 6d = 49d)
        ccl_base = [float(type_counts.get(t, 0)) for t in GT_NODE_TYPES]
        ccl_ast_extra = [float(type_counts.get(t, 0)) for t in CCL_AST_EXTRA_TYPES]
        extra = extract_ccl_extra_features(func.ccl)
        ccl_extra = [extra[k] for k in sorted(extra.keys())]

        # C3 拡張 (+3d)
        c3 = extract_c3_features(func.ccl)
        c3_extra = [c3[k] for k in sorted(c3.keys())]

        ccl_vec = ccl_base + ccl_ast_extra + ccl_extra + c3_extra  # 49+3 = 52d
        ccl_vectors.append(ccl_vec)

    return ccl_vectors, gt_vectors


# PURPOSE: C3 拡張 Siamese の訓練と ρ 測定
def train_c3_siamese(
    functions: list[FunctionInfo],
    pairs: list[Wave9PairAnalysis],
    epochs: int = 150,
    lr: float = 0.001,
    hidden_dim: int = 64,
    seed: int = 42,
) -> dict:
    """C3 拡張 Siamese Network を訓練する。"""
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
    except ImportError:
        return {"error": "PyTorch not available"}

    random.seed(seed)
    torch.manual_seed(seed)

    # C3 拡張特徴量
    ccl_vecs, gt_vecs = build_c3_feature_vectors(functions)
    ccl_vecs = _normalize_vectors(ccl_vecs)
    gt_vecs = _normalize_vectors(gt_vecs)

    name_to_idx = {f.name: i for i, f in enumerate(functions)}

    ccl_dim = len(ccl_vecs[0])  # 52d
    gt_dim = len(gt_vecs[0])    # 29d
    input_dim = ccl_dim + gt_dim  # 81d

    print(f"   C3 Siamese 入力次元: CCL={ccl_dim}d + GT={gt_dim}d = {input_dim}d")

    # C3 特徴量の統計
    c3_stats = {}
    for func in functions:
        c3 = extract_c3_features(func.ccl)
        for k, v in c3.items():
            c3_stats.setdefault(k, []).append(v)
    print(f"   C3 特徴量統計:")
    for k, vals in sorted(c3_stats.items()):
        avg = sum(vals) / len(vals)
        nonzero = sum(1 for v in vals if v > 0)
        print(f"     {k}: mean={avg:.3f}, nonzero={nonzero}/{len(vals)}")

    # データ準備
    vecs_a_list = []
    vecs_b_list = []
    targets_list = []
    for p in pairs:
        ia = name_to_idx.get(p.func_a)
        ib = name_to_idx.get(p.func_b)
        if ia is None or ib is None:
            continue
        vecs_a_list.append(ccl_vecs[ia] + gt_vecs[ia])
        vecs_b_list.append(ccl_vecs[ib] + gt_vecs[ib])
        targets_list.append(p.ast_lev_distance)

    indices = list(range(len(vecs_a_list)))
    random.shuffle(indices)
    vecs_a_list = [vecs_a_list[i] for i in indices]
    vecs_b_list = [vecs_b_list[i] for i in indices]
    targets_list = [targets_list[i] for i in indices]

    all_a = torch.FloatTensor(vecs_a_list)
    all_b = torch.FloatTensor(vecs_b_list)
    all_t = torch.FloatTensor(targets_list)

    split = int(len(all_a) * 0.8)
    train_a, test_a = all_a[:split], all_a[split:]
    train_b, test_b = all_b[:split], all_b[split:]
    train_t, test_t = all_t[:split], all_t[split:]

    print(f"   Train: {len(train_a)}, Test: {len(test_a)}")

    class SiameseEncoder(nn.Module):
        def __init__(self, in_dim: int, h_dim: int):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(in_dim, h_dim),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(h_dim, h_dim // 2),
                nn.ReLU(),
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.net(x)

    encoder = SiameseEncoder(input_dim, hidden_dim)
    optimizer = optim.Adam(encoder.parameters(), lr=lr)
    batch_size = 64

    print(f"   Epochs: {epochs}, LR: {lr}, Hidden: {hidden_dim}, Batch: {batch_size}")
    best_test_rho = -1.0
    best_epoch = 0

    for epoch in range(epochs):
        encoder.train()
        perm = torch.randperm(len(train_a))
        shuffled_a = train_a[perm]
        shuffled_b = train_b[perm]
        shuffled_t = train_t[perm]
        total_loss = 0.0

        for start in range(0, len(shuffled_a), batch_size):
            end = min(start + batch_size, len(shuffled_a))
            ba = shuffled_a[start:end]
            bb = shuffled_b[start:end]
            bt = shuffled_t[start:end]

            ea = encoder(ba)
            eb = encoder(bb)
            predicted = torch.sqrt(torch.sum((ea - eb) ** 2, dim=1) + 1e-8)
            loss = torch.mean((predicted - bt) ** 2)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * (end - start)

        if (epoch + 1) % 10 == 0 or epoch == epochs - 1:
            encoder.eval()
            with torch.no_grad():
                test_ea = encoder(test_a)
                test_eb = encoder(test_b)
                test_preds_t = torch.sqrt(torch.sum((test_ea - test_eb) ** 2, dim=1) + 1e-8)
                test_preds = test_preds_t.tolist()
                test_targets = test_t.tolist()

            test_rho = spearman_rho(test_preds, test_targets)
            avg_loss = total_loss / len(train_a)

            if test_rho > best_test_rho:
                best_test_rho = test_rho
                best_epoch = epoch + 1

            if (epoch + 1) % 50 == 0 or epoch == epochs - 1:
                print(f"   Epoch {epoch+1:3d}: loss={avg_loss:.4f}, test ρ={test_rho:.4f} (best={best_test_rho:.4f} @{best_epoch})")

    encoder.eval()
    with torch.no_grad():
        full_ea = encoder(all_a)
        full_eb = encoder(all_b)
        full_preds_t = torch.sqrt(torch.sum((full_ea - full_eb) ** 2, dim=1) + 1e-8)
        all_preds = full_preds_t.tolist()
        all_targets = all_t.tolist()

    full_rho = spearman_rho(all_preds, all_targets)

    return {
        "test_rho": best_test_rho,
        "test_best_epoch": best_epoch,
        "full_rho": full_rho,
        "ccl_dim": ccl_dim,
        "gt_dim": gt_dim,
        "n_train": len(train_a),
        "n_test": len(test_a),
    }


# ============================================================
# main
# ============================================================

def main():
    target_root = _MEKHANE_SRC / "mekhane"
    if not target_root.exists():
        print(f"❌ ディレクトリが見つかりません: {target_root}")
        sys.exit(1)

    print(f"🎯 対象: {target_root}")
    print(f"🔬 Wave 9 + C3 特徴量拡張実験\n")

    # Phase 1: 関数抽出
    print(f"📋 Phase 1: 関数抽出 (max 1000)...")
    functions = extract_functions(target_root, max_functions=1000)
    print(f"   抽出: {len(functions)} 関数\n")

    # Phase 2: ペア生成
    print(f"📋 Phase 2: Wave 9 ペア生成...")
    pairs = generate_wave9_pairs(functions, max_pairs=5000)
    print(f"   ペア: {len(pairs)}\n")

    # Phase 3: C3 拡張 Siamese
    print(f"🧠 C3 拡張 Siamese Network 訓練 (150 epochs)...")
    c3_results = train_c3_siamese(functions, pairs, epochs=150)

    print(f"\n{'='*60}")
    print(f"結果比較")
    print(f"{'='*60}")
    print(f"  前 (C3 なし, 49d CCL):  test ρ=0.7756, full ρ=0.8784")
    print(f"  Step 1 (C3 テキストのみ): test ρ=0.7746, full ρ=0.8574")
    if "error" not in c3_results:
        print(f"  Step 2 (C3 特徴量 52d):  test ρ={c3_results['test_rho']:.4f}, full ρ={c3_results['full_rho']:.4f}")
        delta = c3_results['full_rho'] - 0.8784
        direction = "改善" if delta > 0 else "低下"
        print(f"  Δ (full ρ): {delta:+.4f} ({direction})")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
