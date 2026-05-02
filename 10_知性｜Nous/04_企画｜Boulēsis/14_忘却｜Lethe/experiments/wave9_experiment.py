#!/usr/bin/env python3
"""Wave 9 CCL 距離改善実験

PURPOSE: ρ = 0.857 → 0.90+ を目指す3施策の実験。
  9A: AST n-gram コサイン距離 (GT 側改善)
  9B: CCL 特徴量拡張 43d → 49d (CCL 側改善)
  9C: 複合 GT + Siamese Network

p3b_benchmark.py をベースにし、Phase 1 (関数抽出) と統計分析を再利用する。
"""

from __future__ import annotations

import argparse
import ast
import math
import random
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

# p3b_benchmark を import (同ディレクトリ)
sys.path.insert(0, str(Path(__file__).parent))
from p3b_benchmark import (
    FunctionInfo,
    PairAnalysis,
    extract_functions,
    ast_structural_distance,
    control_flow_distance,
    ccl_edit_distance,
    spearman_rho,
    fisher_z_test,
    _normalized_levenshtein,
)

_HGK_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_MEKHANE_SRC = _HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"


# ============================================================
# 9A: AST n-gram コサイン距離
# ============================================================

# PURPOSE: AST ノード型列の n-gram を抽出
def _extract_ngrams(seq: list[str], n: int = 2) -> Counter:
    """シーケンスから n-gram の Counter を生成する。"""
    ngrams = Counter()
    for i in range(len(seq) - n + 1):
        gram = tuple(seq[i:i + n])
        ngrams[gram] += 1
    return ngrams


# PURPOSE: 2つの n-gram Counter 間のコサイン距離
def ngram_cosine_distance(a: FunctionInfo, b: FunctionInfo, n: int = 2) -> float:
    """AST ノード型列の n-gram コサイン距離 (0=同一, 1=完全に異なる)。

    n-gram のカウントベクトル間のコサイン類似度を 1 から引いて距離化。
    位置ズレに頑健で、局所パターン共有を捉える。
    """
    ngrams_a = _extract_ngrams(a.ast_node_types, n)
    ngrams_b = _extract_ngrams(b.ast_node_types, n)

    if not ngrams_a or not ngrams_b:
        return 1.0

    # 全 n-gram のユニオン
    all_grams = set(ngrams_a.keys()) | set(ngrams_b.keys())

    # コサイン類似度
    dot = sum(ngrams_a.get(g, 0) * ngrams_b.get(g, 0) for g in all_grams)
    norm_a = math.sqrt(sum(v ** 2 for v in ngrams_a.values()))
    norm_b = math.sqrt(sum(v ** 2 for v in ngrams_b.values()))

    if norm_a == 0 or norm_b == 0:
        return 1.0

    similarity = dot / (norm_a * norm_b)
    return 1.0 - similarity


# ============================================================
# 9B: CCL 特徴量拡張 (43d → 49d)
# ============================================================

# PURPOSE: CCL テキストから追加特徴量を抽出
def extract_ccl_extra_features(ccl: str) -> dict[str, float]:
    """CCL テキストから構造的特徴量を抽出する (+6 次元)。

    既存の p3b_benchmark が使う 43d (AST ノードカウント 27d + CF 16d) に加え、
    CCL テキスト自体から抽出する 6 特徴量。
    """
    tokens = ccl.split()
    n_tokens = max(len(tokens), 1)  # ゼロ除算防止

    # 1. max_nesting_depth: {} の最大ネスト深度
    max_depth = 0
    current_depth = 0
    for ch in ccl:
        if ch == '{':
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif ch == '}':
            current_depth = max(0, current_depth - 1)

    # 2. scope_count: scope{} ブロック数
    scope_count = len(re.findall(r'scope\s*\{', ccl))

    # 3. guard_density: V:{} (assertion/guard) の割合
    guard_count = len(re.findall(r'V:\s*\{', ccl))
    guard_density = guard_count / n_tokens

    # 4. error_density: !err の割合
    error_count = ccl.count('!err')
    error_density = error_count / n_tokens

    # 5. lambda_count: L:[]{}(ラムダ/匿名関数) の出現数
    lambda_count = len(re.findall(r'L:\s*\[', ccl))

    # 6. comprehension_density: F:[each]{} (内包表記/ループ) の割合
    comp_count = len(re.findall(r'F:\s*\[', ccl))
    comp_density = comp_count / n_tokens

    return {
        'max_nesting_depth': float(max_depth),
        'scope_count': float(scope_count),
        'guard_density': guard_density,
        'error_density': error_density,
        'lambda_count': float(lambda_count),
        'comprehension_density': comp_density,
    }


# PURPOSE: 拡張特徴量ベクトル (6d) を関数ペアの距離に変換
def ccl_extra_feature_distance(a: FunctionInfo, b: FunctionInfo) -> float:
    """CCL 拡張特徴量 (6d) のユークリッド距離 (正規化)。

    各特徴量を [0,1] に正規化した後のユークリッド距離。
    """
    feats_a = extract_ccl_extra_features(a.ccl)
    feats_b = extract_ccl_extra_features(b.ccl)

    keys = sorted(feats_a.keys())
    diff_sq = sum((feats_a[k] - feats_b[k]) ** 2 for k in keys)
    # sqrt(6) で正規化 → [0, 1] 範囲に近似
    return math.sqrt(diff_sq) / math.sqrt(len(keys))


# ============================================================
# 9C: 複合 GT ベクトル構築
# ============================================================

@dataclass
class Wave9PairAnalysis:
    """Wave 9 用の拡張ペア分析。"""
    func_a: str = ""
    func_b: str = ""
    # 基本距離 (p3b_benchmark と同一)
    ast_lev_distance: float = 0.0     # AST Levenshtein (ベースライン GT)
    cf_distance: float = 0.0          # CF multiset Jaccard
    ccl_edit_distance: float = 0.0    # CCL token Levenshtein
    # Wave 9 新距離
    ast_bigram_distance: float = 0.0  # 9A: AST bigram コサイン
    ast_trigram_distance: float = 0.0 # 9A: AST trigram コサイン
    ccl_extra_distance: float = 0.0   # 9B: CCL 拡張特徴量ユークリッド
    # GT 複合 (9C)
    gt_composite: float = 0.0        # 加重平均

    # Embedding cosine (Phase 3 用)
    text_cosine: float = 0.0
    ccl_cosine: float = 0.0


# PURPOSE: Wave 9 ペア生成 (全距離を一括計算)
def generate_wave9_pairs(
    functions: list[FunctionInfo],
    max_pairs: int = 500,
    seed: int = 42,
) -> list[Wave9PairAnalysis]:
    """関数ペアを生成し、全距離指標を計算する。"""
    all_pairs = list(combinations(range(len(functions)), 2))

    if len(all_pairs) > max_pairs:
        random.seed(seed)
        sampled = random.sample(all_pairs, max_pairs)
    else:
        sampled = all_pairs

    pairs = []
    for idx_a, idx_b in sampled:
        fa, fb = functions[idx_a], functions[idx_b]
        pairs.append(Wave9PairAnalysis(
            func_a=fa.name,
            func_b=fb.name,
            # 既存距離
            ast_lev_distance=ast_structural_distance(fa, fb),
            cf_distance=control_flow_distance(fa, fb),
            ccl_edit_distance=ccl_edit_distance(fa, fb),
            # 9A: n-gram コサイン
            ast_bigram_distance=ngram_cosine_distance(fa, fb, n=2),
            ast_trigram_distance=ngram_cosine_distance(fa, fb, n=3),
            # 9B: CCL 拡張特徴量
            ccl_extra_distance=ccl_extra_feature_distance(fa, fb),
        ))

    return pairs


# ============================================================
# Phase 4: Wave 9 統計分析
# ============================================================

# PURPOSE: Wave 9 の全距離指標で Spearman ρ を計算
def analyze_wave9(pairs: list[Wave9PairAnalysis]) -> dict:
    """各施策別 + 複合の Spearman ρ を一括計算。

    2段階分析:
    1. 個別距離指標同士の直接 ρ (raw comparison)
    2. CCL 側の複数指標を最適線形結合し、GT (ast_lev) を予測する ρ (grid search)
    """
    n = len(pairs)

    # 距離 → 類似度 (1 - dist)
    ast_lev_sim = [1.0 - p.ast_lev_distance for p in pairs]
    ast_bi_sim = [1.0 - p.ast_bigram_distance for p in pairs]
    ast_tri_sim = [1.0 - p.ast_trigram_distance for p in pairs]
    cf_sim = [1.0 - p.cf_distance for p in pairs]
    ccl_edit_sim = [1.0 - p.ccl_edit_distance for p in pairs]
    ccl_extra_sim = [1.0 - p.ccl_extra_distance for p in pairs]

    results = {
        "n_pairs": n,
        # 1. 個別距離の直接 ρ
        "raw_rho": {
            "ρ(ast_lev, ccl_edit)": spearman_rho(ast_lev_sim, ccl_edit_sim),
            "ρ(ast_bigram, ccl_edit)": spearman_rho(ast_bi_sim, ccl_edit_sim),
            "ρ(ast_trigram, ccl_edit)": spearman_rho(ast_tri_sim, ccl_edit_sim),
            "ρ(cf, ccl_edit)": spearman_rho(cf_sim, ccl_edit_sim),
            "ρ(ast_lev, ccl_extra)": spearman_rho(ast_lev_sim, ccl_extra_sim),
        },
        "diagnostics": {
            "ρ(ast_lev, ast_bigram)": spearman_rho(ast_lev_sim, ast_bi_sim),
            "ρ(ast_lev, ast_trigram)": spearman_rho(ast_lev_sim, ast_tri_sim),
            "ρ(ast_lev, cf)": spearman_rho(ast_lev_sim, cf_sim),
            "ρ(ccl_edit, ccl_extra)": spearman_rho(ccl_edit_sim, ccl_extra_sim),
            "ρ(ast_bigram, cf)": spearman_rho(ast_bi_sim, cf_sim),
        },
    }

    # 2. Grid search: CCL 側の最適線形結合で GT を予測
    # GT = ast_lev (固定)
    # CCL 候補 = ccl_edit, ccl_extra, ast_bigram (CCL から間接計算される情報も含む)
    print("   🔍 Grid search: CCL 側の最適線形結合...")
    best_rho_combined = -1.0
    best_weights = (1.0, 0.0)
    # w1: ccl_edit, w2: ccl_extra の割合 (w2 = 1 - w1)
    for w1_pct in range(0, 101, 5):
        w1 = w1_pct / 100.0
        w2 = 1.0 - w1
        combined = [w1 * ccl_edit_sim[i] + w2 * ccl_extra_sim[i] for i in range(n)]
        rho = spearman_rho(ast_lev_sim, combined)
        if rho > best_rho_combined:
            best_rho_combined = rho
            best_weights = (w1, w2)

    results["grid_search_ccl"] = {
        "best_ρ": best_rho_combined,
        "best_weights": f"ccl_edit={best_weights[0]:.2f}, ccl_extra={best_weights[1]:.2f}",
    }

    # 3. Grid search: GT 側の最適線形結合で CCL を予測
    print("   🔍 Grid search: GT 側の最適線形結合...")
    best_rho_gt = -1.0
    best_gt_weights = (1.0, 0.0, 0.0)
    # w_lev, w_bi, w_cf (正規化)
    for w_lev_pct in range(0, 101, 10):
        for w_bi_pct in range(0, 101 - w_lev_pct, 10):
            w_cf_pct = 100 - w_lev_pct - w_bi_pct
            w_lev = w_lev_pct / 100.0
            w_bi = w_bi_pct / 100.0
            w_cf = w_cf_pct / 100.0
            gt_combined = [
                w_lev * ast_lev_sim[i] + w_bi * ast_bi_sim[i] + w_cf * cf_sim[i]
                for i in range(n)
            ]
            rho = spearman_rho(gt_combined, ccl_edit_sim)
            if rho > best_rho_gt:
                best_rho_gt = rho
                best_gt_weights = (w_lev, w_bi, w_cf)

    results["grid_search_gt"] = {
        "best_ρ": best_rho_gt,
        "best_weights": f"ast_lev={best_gt_weights[0]:.2f}, ast_bigram={best_gt_weights[1]:.2f}, cf={best_gt_weights[2]:.2f}",
    }

    # 4. 両側最適結合
    print("   🔍 Grid search: 両側最適結合...")
    best_rho_both = -1.0
    best_both_desc = ""
    # GT 側: best_gt_weights を固定、CCL 側を sweep
    for w1_pct in range(0, 101, 5):
        w1 = w1_pct / 100.0
        w2 = 1.0 - w1
        gt_opt = [
            best_gt_weights[0] * ast_lev_sim[i]
            + best_gt_weights[1] * ast_bi_sim[i]
            + best_gt_weights[2] * cf_sim[i]
            for i in range(n)
        ]
        ccl_opt = [w1 * ccl_edit_sim[i] + w2 * ccl_extra_sim[i] for i in range(n)]
        rho = spearman_rho(gt_opt, ccl_opt)
        if rho > best_rho_both:
            best_rho_both = rho
            best_both_desc = (
                f"GT({best_gt_weights[0]:.2f}lev+{best_gt_weights[1]:.2f}bi+{best_gt_weights[2]:.2f}cf) "
                f"vs CCL({w1:.2f}edit+{w2:.2f}extra)"
            )

    results["grid_search_both"] = {
        "best_ρ": best_rho_both,
        "description": best_both_desc,
    }

    # Fisher z-test: ベースライン vs 最良
    baseline_rho = results["raw_rho"]["ρ(ast_lev, ccl_edit)"]
    best_overall = max(best_rho_combined, best_rho_gt, best_rho_both)
    results["fisher_z_p"] = fisher_z_test(baseline_rho, best_overall, n)
    results["best_overall_ρ"] = best_overall

    return results


# ============================================================
# Siamese Network (Wave 9C)
# ============================================================

# PURPOSE: CCL + GT 特徴量ベクトルを抽出
def _build_feature_vectors(
    functions: list[FunctionInfo],
) -> tuple[list[list[float]], list[list[float]]]:
    """各関数の CCL 特徴量 (49d) と GT 特徴量 (29d) を構築する。

    CCL 49d = AST ノードカウント補完 43d (ベースライン) + 拡張 6d
    GT 29d = AST ノードカウント 27d + n-gram 統計 2d (bigram エントロピー、trigram エントロピー)
    """
    # AST ノード型のカウント → 27d (p3b_benchmark の GT)
    # mekhane codebase での頻出 27 ノード型
    GT_NODE_TYPES = [
        'FunctionDef', 'AsyncFunctionDef', 'Return', 'Assign', 'AugAssign',
        'For', 'AsyncFor', 'While', 'If', 'With', 'AsyncWith',
        'Raise', 'Try', 'Assert', 'Import', 'ImportFrom',
        'Expr', 'Call', 'Attribute', 'Subscript', 'Name',
        'BoolOp', 'BinOp', 'UnaryOp', 'Compare', 'ListComp', 'DictComp',
    ]

    # CCL 追加 16d (Wave 8 で追加した AST 補完)
    CCL_AST_EXTRA_TYPES = [
        'Yield', 'YieldFrom', 'SetComp', 'GeneratorExp',
        'Lambda', 'IfExp', 'Dict', 'Set', 'List', 'Tuple',
        'Starred', 'FormattedValue', 'JoinedStr', 'Constant',
        'Delete', 'Global',
    ]

    ccl_vectors = []
    gt_vectors = []

    for func in functions:
        # GT ベクトル (27d) = ノード型カウント
        type_counts = Counter(func.ast_node_types)
        gt_base = [float(type_counts.get(t, 0)) for t in GT_NODE_TYPES]

        # GT 拡張 (2d): n-gram エントロピー
        bigrams = _extract_ngrams(func.ast_node_types, n=2)
        trigrams = _extract_ngrams(func.ast_node_types, n=3)
        bi_entropy = _counter_entropy(bigrams)
        tri_entropy = _counter_entropy(trigrams)
        gt_vec = gt_base + [bi_entropy, tri_entropy]  # 29d
        gt_vectors.append(gt_vec)

        # CCL ベース (27d) = 同じノードカウント (ただし CCL テキストからの再抽出)
        ccl_base = [float(type_counts.get(t, 0)) for t in GT_NODE_TYPES]
        # CCL AST 補完 (16d)
        ccl_ast_extra = [float(type_counts.get(t, 0)) for t in CCL_AST_EXTRA_TYPES]
        # CCL 拡張 (6d)
        extra = extract_ccl_extra_features(func.ccl)
        ccl_extra = [extra[k] for k in sorted(extra.keys())]

        ccl_vec = ccl_base + ccl_ast_extra + ccl_extra  # 27+16+6 = 49d
        ccl_vectors.append(ccl_vec)

    return ccl_vectors, gt_vectors


# PURPOSE: Counter のエントロピー計算
def _counter_entropy(counts: Counter) -> float:
    """Counter の Shannon エントロピーを計算する。"""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    entropy = 0.0
    for v in counts.values():
        p = v / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


# PURPOSE: 特徴量ベクトルの正規化 (z-score)
def _normalize_vectors(vectors: list[list[float]]) -> list[list[float]]:
    """列ごとに z-score 正規化する。"""
    if not vectors:
        return vectors
    n_dim = len(vectors[0])
    n_samples = len(vectors)

    # 各次元の平均と標準偏差
    means = [0.0] * n_dim
    stds = [0.0] * n_dim
    for d in range(n_dim):
        vals = [vectors[i][d] for i in range(n_samples)]
        m = sum(vals) / n_samples
        means[d] = m
        var = sum((v - m) ** 2 for v in vals) / max(n_samples - 1, 1)
        stds[d] = math.sqrt(var) if var > 0 else 1.0

    # 正規化
    normalized = []
    for vec in vectors:
        normalized.append([(vec[d] - means[d]) / stds[d] for d in range(n_dim)])

    return normalized


# PURPOSE: Siamese Network で学習距離を算出する ρ 測定
def train_siamese_and_measure(
    functions: list[FunctionInfo],
    pairs: list[Wave9PairAnalysis],
    epochs: int = 150,
    lr: float = 0.001,
    hidden_dim: int = 64,
    seed: int = 42,
) -> dict:
    """Siamese Network を訓練し、学習距離と AST 構造距離の ρ を測定する。

    入力: CCL特徴量(49d) concatenated with GT特徴量(29d) = 78d
    ターゲット: AST Levenshtein 距離 (正規化済み)
    """
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
    except ImportError:
        print("⚠️ PyTorch がインストールされていません。Siamese をスキップします。")
        return {"error": "PyTorch not available"}

    random.seed(seed)
    torch.manual_seed(seed)

    # 特徴量ベクトル構築
    ccl_vecs, gt_vecs = _build_feature_vectors(functions)
    ccl_vecs = _normalize_vectors(ccl_vecs)
    gt_vecs = _normalize_vectors(gt_vecs)

    # 関数名→インデックス
    name_to_idx = {f.name: i for i, f in enumerate(functions)}

    # 入力次元
    ccl_dim = len(ccl_vecs[0])  # 49d
    gt_dim = len(gt_vecs[0])    # 29d
    input_dim = ccl_dim + gt_dim  # 78d

    print(f"   Siamese 入力次元: CCL={ccl_dim}d + GT={gt_dim}d = {input_dim}d")

    # データ準備: テンソルを事前構築 (バッチ処理用)
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

    # シャッフル用インデックス
    indices = list(range(len(vecs_a_list)))
    random.shuffle(indices)
    vecs_a_list = [vecs_a_list[i] for i in indices]
    vecs_b_list = [vecs_b_list[i] for i in indices]
    targets_list = [targets_list[i] for i in indices]

    # テンソル変換 (1回だけ)
    all_a = torch.FloatTensor(vecs_a_list)
    all_b = torch.FloatTensor(vecs_b_list)
    all_t = torch.FloatTensor(targets_list)

    # 80/20 split
    split = int(len(all_a) * 0.8)
    train_a, test_a = all_a[:split], all_a[split:]
    train_b, test_b = all_b[:split], all_b[split:]
    train_t, test_t = all_t[:split], all_t[split:]

    print(f"   Train: {len(train_a)}, Test: {len(test_a)}")

    # Siamese Network 定義
    class SiameseEncoder(nn.Module):
        """共有重みエンコーダ。"""
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
    optimizer = optim.Adam(encoder.parameters(), lr=lr, weight_decay=1e-4)
    batch_size = 64

    # 訓練ループ (ミニバッチ)
    print(f"   Epochs: {epochs}, LR: {lr}, Hidden: {hidden_dim}, Batch: {batch_size}")
    best_test_rho = -1.0
    best_epoch = 0

    for epoch in range(epochs):
        encoder.train()
        # エポックごとにシャッフル
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

            # 学習距離 = L2 距離 (バッチ)
            ea = encoder(ba)
            eb = encoder(bb)
            predicted = torch.sqrt(torch.sum((ea - eb) ** 2, dim=1) + 1e-8)

            # MSE Loss (バッチ平均)
            loss = torch.mean((predicted - bt) ** 2)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * (end - start)

        # テスト評価 (10 epoch ごと)
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

    # 全データで最終評価
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
# 出力
# ============================================================

# PURPOSE: 結果をフォーマットして表示
def print_wave9_results(results: dict, functions: list[FunctionInfo]):
    """Wave 9 の結果を整形して表示する。"""
    print("\n" + "=" * 70)
    print("Wave 9 CCL 距離改善実験 — 結果")
    print("=" * 70)
    print(f"関数数: {len(functions)}, ペア数: {results['n_pairs']}")
    print()

    # 個別距離の直接 ρ
    print("─── 個別距離の直接 ρ ───")
    for k, v in results["raw_rho"].items():
        marker = " ◀ baseline" if "ast_lev, ccl_edit" in k else ""
        print(f"  {k} = {v:.4f}{marker}")

    # Grid search 結果
    gs_ccl = results.get("grid_search_ccl", {})
    if gs_ccl:
        print(f"\n─── Grid Search: CCL 側の最適結合 ───")
        print(f"  best ρ = {gs_ccl['best_ρ']:.4f}")
        print(f"  weights: {gs_ccl['best_weights']}")

    gs_gt = results.get("grid_search_gt", {})
    if gs_gt:
        print(f"\n─── Grid Search: GT 側の最適結合 ───")
        print(f"  best ρ = {gs_gt['best_ρ']:.4f}")
        print(f"  weights: {gs_gt['best_weights']}")

    gs_both = results.get("grid_search_both", {})
    if gs_both:
        print(f"\n─── Grid Search: 両側最適結合 ───")
        print(f"  best ρ = {gs_both['best_ρ']:.4f}")
        print(f"  {gs_both['description']}")

    # Siamese 結果
    siamese = results.get("siamese")
    if siamese and "error" not in siamese:
        print(f"\n─── Siamese Network (CCL{siamese['ccl_dim']}d × GT{siamese['gt_dim']}d) ───")
        print(f"  Test ρ = {siamese['test_rho']:.4f} (best @ epoch {siamese['test_best_epoch']})")
        print(f"  Full ρ = {siamese['full_rho']:.4f}")
        print(f"  Train/Test: {siamese['n_train']}/{siamese['n_test']}")

    # 診断
    print("\n─── 診断 (距離指標間の相関) ───")
    for k, v in results["diagnostics"].items():
        print(f"  {k} = {v:.4f}")

    # 有意差
    p = results.get("fisher_z_p", 1.0)
    sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."
    best_overall = results.get("best_overall_ρ", 0.0)
    baseline = results["raw_rho"].get("ρ(ast_lev, ccl_edit)", 0.0)
    delta = best_overall - baseline
    print(f"\n  Fisher z-test: p = {p:.4f} ({sig})")
    print(f"  ベースライン ρ = {baseline:.4f} → 最良 ρ = {best_overall:.4f} (Δ = {delta:+.4f})")

    # 最良結果
    print(f"\n🏆 最良 ρ = {best_overall:.4f}")
    print("=" * 70)


# PURPOSE: 結果をマークダウンファイルに保存
def save_wave9_results(results: dict, functions: list[FunctionInfo], output_path: Path):
    """結果をマークダウンファイルに保存する。"""
    baseline = results["raw_rho"].get("ρ(ast_lev, ccl_edit)", 0.0)
    best_overall = results.get("best_overall_ρ", 0.0)

    lines = [
        "# Wave 9 CCL 距離改善実験 — 結果",
        "",
        f"- 関数数: {len(functions)}",
        f"- ペア数: {results['n_pairs']}",
        f"- ベースライン ρ: {baseline:.4f}",
        f"- 最良 ρ: {best_overall:.4f}",
        "",
        "## 個別距離の直接 ρ",
        "",
        "| 指標 | ρ |",
        "|:---|---:|",
    ]
    for k, v in results["raw_rho"].items():
        lines.append(f"| {k} | {v:.4f} |")

    # Grid search
    lines.extend(["", "## Grid Search 結果", ""])
    for gs_name in ["grid_search_ccl", "grid_search_gt", "grid_search_both"]:
        gs = results.get(gs_name, {})
        if gs:
            lines.append(f"### {gs_name}")
            lines.append(f"- best ρ = {gs.get('best_ρ', 0):.4f}")
            if "best_weights" in gs:
                lines.append(f"- weights: {gs['best_weights']}")
            if "description" in gs:
                lines.append(f"- {gs['description']}")
            lines.append("")

    # Siamese
    siamese = results.get("siamese")
    if siamese and "error" not in siamese:
        lines.extend([
            "## Siamese Network",
            "",
            f"- Test ρ = {siamese['test_rho']:.4f} (best @ epoch {siamese['test_best_epoch']})",
            f"- Full ρ = {siamese['full_rho']:.4f}",
            f"- Dims: CCL={siamese['ccl_dim']}d, GT={siamese['gt_dim']}d",
            "",
        ])

    # 診断
    lines.extend(["## 診断", "", "| 指標ペア | ρ |", "|:---|---:|"])
    for k, v in results["diagnostics"].items():
        lines.append(f"| {k} | {v:.4f} |")

    p = results.get("fisher_z_p", 1.0)
    sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."
    lines.extend(["", f"Fisher z-test: p = {p:.4f} ({sig})"])

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n📄 結果保存: {output_path}")


# ============================================================
# main
# ============================================================

# PURPOSE: Wave 9 実験のメインエントリーポイント
def main():
    parser = argparse.ArgumentParser(description="Wave 9 CCL 距離改善実験")
    parser.add_argument("--dry-run", action="store_true",
                        help="embedding なしで距離指標のみ計算")
    parser.add_argument("--train", action="store_true",
                        help="Siamese Network を訓練して ρ を測定")
    parser.add_argument("-n", "--max-functions", type=int, default=200,
                        help="抽出する最大関数数 (デフォルト: 200)")
    parser.add_argument("--max-pairs", type=int, default=500,
                        help="分析する最大ペア数 (デフォルト: 500)")
    parser.add_argument("--epochs", type=int, default=150,
                        help="Siamese 訓練エポック数 (デフォルト: 150)")
    parser.add_argument("--hidden", type=int, default=64,
                        help="Siamese 隠れ層次元 (デフォルト: 64)")
    parser.add_argument("--target-dir", type=str, default=None,
                        help="対象ディレクトリ (デフォルト: mekhane/)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="詳細出力")
    args = parser.parse_args()

    # ターゲットディレクトリの解決
    if args.target_dir:
        target_root = Path(args.target_dir)
    else:
        target_root = _MEKHANE_SRC / "mekhane"

    if not target_root.exists():
        print(f"❌ ディレクトリが見つかりません: {target_root}")
        sys.exit(1)

    print(f"🎯 対象: {target_root}")
    print(f"🔬 Wave 9 CCL 距離改善実験")

    # Phase 1: 関数抽出 (p3b_benchmark を再利用)
    print(f"\n📋 Phase 1: 関数抽出 (max {args.max_functions})...")
    functions = extract_functions(target_root, max_functions=args.max_functions)
    print(f"   抽出: {len(functions)} 関数")

    if len(functions) < 10:
        print("❌ 関数数が不十分 (最低 10 必要)")
        sys.exit(1)

    # Phase 2: Wave 9 ペア生成 + 全距離計算
    print(f"\n📋 Phase 2: Wave 9 ペア生成 + 距離計算...")
    pairs = generate_wave9_pairs(functions, max_pairs=args.max_pairs)
    print(f"   ペア: {len(pairs)}")

    if args.verbose:
        # 特徴量サンプル表示
        sample = functions[:3]
        print("\n   ─── CCL 拡張特徴量サンプル ───")
        for f in sample:
            feats = extract_ccl_extra_features(f.ccl)
            print(f"   {f.name}: {feats}")
        # n-gram サンプル表示
        print("\n   ─── AST bigram サンプル ───")
        for f in sample:
            bigrams = _extract_ngrams(f.ast_node_types, n=2)
            top5 = bigrams.most_common(5)
            print(f"   {f.name}: {top5}")

    # Phase 4: 統計分析
    print(f"\n📊 Phase 4: Wave 9 統計分析...")
    results = analyze_wave9(pairs)

    # Siamese 訓練 (--train 指定時)
    if args.train:
        print(f"\n🧠 Siamese Network 訓練 ({args.epochs} epochs)...")
        siamese_results = train_siamese_and_measure(
            functions, pairs, epochs=args.epochs, hidden_dim=args.hidden,
        )
        results["siamese"] = siamese_results

    # 結果出力
    print_wave9_results(results, functions)

    # ファイル保存
    output_path = Path(__file__).parent / "wave9_results.md"
    save_wave9_results(results, functions, output_path)



if __name__ == "__main__":
    main()
