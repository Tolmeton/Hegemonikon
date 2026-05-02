#!/usr/bin/env python3
"""Wave 9/10 Siamese Network — CCL 距離学習

PURPOSE: Cross-Attention Siamese で CCL 43d → 学習距離を最適化し、
  AST 構造距離 (GT) との Spearman ρ を最大化する。

Conv 0ff8 Wave 9 (ρ=0.9195) の再現 + 改善実験。
/tmp/torch_env/bin/python で実行すること (PyTorch 2.10 必須)。
"""

from __future__ import annotations

import argparse
import ast
import math
import random
import sys
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

import numpy as np

# torch は /tmp/torch_env にのみ存在
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# mekhane の import パス追加
_HGK_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_MEKHANE_SRC = _HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"
sys.path.insert(0, str(_MEKHANE_SRC))
sys.path.insert(0, str(Path(__file__).parent))

from p3b_benchmark import (
    FunctionInfo,
    extract_functions,
    ast_structural_distance,
    control_flow_distance,
    spearman_rho,
    _normalized_levenshtein,
)
from mekhane.symploke.code_ingest import ccl_features, ast_supplement


# ============================================================
# 特徴量抽出
# ============================================================

# PURPOSE: FunctionInfo から CCL 特徴量を抽出 (43d または 49d)
def extract_ccl_features(func: FunctionInfo, extra: bool = False) -> list[float]:
    """CCL 27d + AST 16d = 43d 特徴量。extra=True で +6d (9B 拡張)。

    code_ingest.py の ccl_features + ast_supplement を利用。
    extra=True: max_nesting_depth, scope_count, guard_density,
                error_density, lambda_count, comprehension_density を追加。
    """
    import re
    # CCL 27d
    cf = ccl_features(func.ccl)

    # AST 16d: ソースコードを再パースして AST ノードを取得
    try:
        tree = ast.parse(func.source)
        func_node = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_node = node
                break
        if func_node:
            sup = ast_supplement(func_node)
        else:
            sup = [0] * 16
    except (SyntaxError, Exception):
        sup = [0] * 16

    vec = cf + [float(x) for x in sup]

    if extra:
        # 9B: CCL テキストから +6d 拡張特徴量
        ccl = func.ccl
        tokens = ccl.split()
        nt = max(len(tokens), 1)
        # ネスト深度
        mx, d = 0, 0
        for ch in ccl:
            if ch == '{': d += 1; mx = max(mx, d)
            elif ch == '}': d = max(0, d - 1)
        vec.append(float(mx))
        # scope_count
        vec.append(float(len(re.findall(r'scope\s*\{', ccl))))
        # guard_density
        vec.append(len(re.findall(r'V:\s*\{', ccl)) / nt)
        # error_density
        vec.append(ccl.count('!err') / nt)
        # lambda_count
        vec.append(float(len(re.findall(r'L:\s*\[', ccl))))
        # comprehension_density
        vec.append(len(re.findall(r'F:\s*\[', ccl)) / nt)

    return vec


# PURPOSE: GT ベクトル (AST ノード型カウント 27d) を抽出
def extract_gt27d(func: FunctionInfo) -> list[float]:
    """AST ノード型のカウントベクトル (27d)。

    p3b_benchmark の ast_node_types から top-27 ノード型のカウント。
    """
    # 固定の top-27 ノード型 (コードベース共通)
    TOP_TYPES = [
        'Name', 'Load', 'Call', 'Attribute', 'Constant', 'Store',
        'Assign', 'Return', 'If', 'Compare', 'BoolOp', 'Subscript',
        'keyword', 'arg', 'arguments', 'Tuple', 'List', 'FunctionDef',
        'For', 'BinOp', 'JoinedStr', 'UnaryOp', 'Dict', 'Starred',
        'AugAssign', 'Expr', 'FormattedValue',
    ]
    counter = Counter(func.ast_node_types)
    total = max(len(func.ast_node_types), 1)
    return [counter.get(t, 0) / total for t in TOP_TYPES]


# ============================================================
# Siamese Network アーキテクチャ
# ============================================================

if HAS_TORCH:
    # PURPOSE: V2 Residual Siamese (ベースライン)
    class SiameseV2(nn.Module):
        """Residual MLP Siamese — Conv 0ff8 Wave 7 相当。"""
        def __init__(self, input_dim: int = 43, hidden: int = 128):
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Linear(input_dim, hidden),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(hidden, hidden),
                nn.ReLU(),
            )
            # 残差ブロック
            self.res = nn.Sequential(
                nn.Linear(hidden, hidden),
                nn.ReLU(),
                nn.Linear(hidden, hidden),
            )
            self.head = nn.Sequential(
                nn.Linear(hidden * 3, 64),  # |a-b| + a*b + a+b
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(64, 1),
                nn.Sigmoid(),
            )

        def encode(self, x):
            h = self.encoder(x)
            return h + self.res(h)  # 残差接続

        def forward(self, x_a, x_b):
            e_a = self.encode(x_a)
            e_b = self.encode(x_b)
            diff = torch.abs(e_a - e_b)
            prod = e_a * e_b
            total = e_a + e_b
            combined = torch.cat([diff, prod, total], dim=-1)
            return self.head(combined).squeeze(-1)

    # PURPOSE: V3 Cross-Attention Siamese (最高性能)
    class SiameseV3(nn.Module):
        """Cross-Attention Siamese — Conv 0ff8 Wave 9 相当。

        2つのエンコード出力間で cross-attention を計算し、
        相互情報を組み込んだ距離学習。
        """
        def __init__(self, input_dim: int = 43, hidden: int = 128, n_heads: int = 4):
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Linear(input_dim, hidden),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(hidden, hidden),
                nn.ReLU(),
            )
            # Cross-attention
            self.query = nn.Linear(hidden, hidden)
            self.key = nn.Linear(hidden, hidden)
            self.value = nn.Linear(hidden, hidden)
            self.n_heads = n_heads
            self.head_dim = hidden // n_heads
            self.scale = math.sqrt(self.head_dim)

            self.head = nn.Sequential(
                nn.Linear(hidden * 4, 64),  # |a-b| + a*b + attn_a + attn_b
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(64, 1),
                nn.Sigmoid(),
            )

        def encode(self, x):
            return self.encoder(x)

        def cross_attend(self, q_src, kv_src):
            """単一ベクトル間の擬似 cross-attention。

            バッチ内の各ペアで q←a, kv←b として attention を計算。
            """
            q = self.query(q_src)   # [B, H]
            k = self.key(kv_src)    # [B, H]
            v = self.value(kv_src)  # [B, H]

            # スカラー attention (ベクトル間の単一 attention スコア)
            attn_score = torch.sum(q * k, dim=-1, keepdim=True) / self.scale
            attn_weight = torch.sigmoid(attn_score)
            attended = attn_weight * v
            return attended

        def forward(self, x_a, x_b):
            e_a = self.encode(x_a)
            e_b = self.encode(x_b)

            # Cross-attention: a が b を参照 / b が a を参照
            attn_ab = self.cross_attend(e_a, e_b)  # a の視点で b を見る
            attn_ba = self.cross_attend(e_b, e_a)  # b の視点で a を見る

            diff = torch.abs(e_a - e_b)
            prod = e_a * e_b
            combined = torch.cat([diff, prod, attn_ab, attn_ba], dim=-1)
            return self.head(combined).squeeze(-1)


# ============================================================
# 学習パイプライン
# ============================================================

# PURPOSE: 学習データの準備
def prepare_training_data(
    functions: list[FunctionInfo],
    max_pairs: int = 2000,
    seed: int = 42,
    **kwargs,
) -> tuple:
    """関数ペアから (CCL43d_a, CCL43d_b, GT距離) のデータセットを作成。"""
    all_pairs = list(combinations(range(len(functions)), 2))
    if len(all_pairs) > max_pairs:
        random.seed(seed)
        all_pairs = random.sample(all_pairs, max_pairs)

    # 特徴量の事前計算
    extra = kwargs.get('extra_features', False)
    dim_label = '49d' if extra else '43d'
    print(f"   特徴量抽出: {len(functions)} 関数 ({dim_label})...")
    ccl_vecs = [extract_ccl_features(f, extra=extra) for f in functions]
    gt_vecs = [extract_gt27d(f) for f in functions]

    # ペアデータ
    ccl_a_list, ccl_b_list, gt_dist_list = [], [], []
    for i, j in all_pairs:
        ccl_a_list.append(ccl_vecs[i])
        ccl_b_list.append(ccl_vecs[j])
        # GT 距離: AST Levenshtein
        gt_dist = ast_structural_distance(functions[i], functions[j])
        gt_dist_list.append(gt_dist)

    return (
        np.array(ccl_a_list, dtype=np.float32),
        np.array(ccl_b_list, dtype=np.float32),
        np.array(gt_dist_list, dtype=np.float32),
    )


# PURPOSE: 特徴量の正規化 (z-score)
def normalize_features(train_a, train_b, test_a=None, test_b=None):
    """z-score 正規化。train の統計量で test も正規化。"""
    all_train = np.vstack([train_a, train_b])
    mean = all_train.mean(axis=0)
    std = all_train.std(axis=0) + 1e-8

    train_a = (train_a - mean) / std
    train_b = (train_b - mean) / std

    if test_a is not None:
        test_a = (test_a - mean) / std
        test_b = (test_b - mean) / std
        return train_a, train_b, test_a, test_b
    return train_a, train_b


# PURPOSE: Siamese の学習と評価
def train_and_evaluate(
    ccl_a: np.ndarray,
    ccl_b: np.ndarray,
    gt_dist: np.ndarray,
    model_class: type,
    epochs: int = 100,
    lr: float = 0.001,
    train_ratio: float = 0.8,
    seed: int = 42,
    hidden: int = 128,
) -> dict:
    """Siamese を学習し、テストセットでの ρ を返す。"""
    if not HAS_TORCH:
        print("❌ PyTorch が利用できません")
        return {"test_rho": 0.0}

    # train/test 分割
    n = len(gt_dist)
    indices = list(range(n))
    random.seed(seed)
    random.shuffle(indices)
    split = int(n * train_ratio)
    train_idx, test_idx = indices[:split], indices[split:]

    # データ準備
    train_a, train_b = ccl_a[train_idx], ccl_b[train_idx]
    test_a, test_b = ccl_a[test_idx], ccl_b[test_idx]
    train_gt = gt_dist[train_idx]
    test_gt = gt_dist[test_idx]

    # 正規化
    train_a, train_b, test_a, test_b = normalize_features(train_a, train_b, test_a, test_b)

    # Tensor 化
    device = torch.device("cpu")
    train_a_t = torch.tensor(train_a, dtype=torch.float32, device=device)
    train_b_t = torch.tensor(train_b, dtype=torch.float32, device=device)
    train_gt_t = torch.tensor(train_gt, dtype=torch.float32, device=device)
    test_a_t = torch.tensor(test_a, dtype=torch.float32, device=device)
    test_b_t = torch.tensor(test_b, dtype=torch.float32, device=device)

    # モデル
    input_dim = ccl_a.shape[1]
    model = model_class(input_dim=input_dim, hidden=hidden).to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.MSELoss()

    # 学習
    best_test_rho = -1.0
    best_epoch = 0
    patience = 20
    no_improve = 0

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        pred = model(train_a_t, train_b_t)
        loss = criterion(pred, train_gt_t)
        loss.backward()
        optimizer.step()

        # 評価 (10epoch ごと)
        if (epoch + 1) % 5 == 0 or epoch == 0:
            model.eval()
            with torch.no_grad():
                test_pred = model(test_a_t, test_b_t).numpy()
            test_rho = spearman_rho(test_pred.tolist(), test_gt.tolist())

            if test_rho > best_test_rho:
                best_test_rho = test_rho
                best_epoch = epoch + 1
                no_improve = 0
            else:
                no_improve += 5

            if (epoch + 1) % 20 == 0:
                print(f"   Epoch {epoch+1:3d}: loss={loss.item():.4f}, test_ρ={test_rho:.4f} (best={best_test_rho:.4f}@{best_epoch})")

            if no_improve >= patience:
                print(f"   Early stop at epoch {epoch+1}")
                break

    # 最終評価
    model.eval()
    with torch.no_grad():
        test_pred = model(test_a_t, test_b_t).numpy()
    final_rho = spearman_rho(test_pred.tolist(), test_gt.tolist())

    # train ρ
    with torch.no_grad():
        train_pred = model(train_a_t, train_b_t).numpy()
    train_rho = spearman_rho(train_pred.tolist(), train_gt.tolist())

    return {
        "train_rho": train_rho,
        "test_rho": final_rho,
        "best_test_rho": best_test_rho,
        "best_epoch": best_epoch,
        "n_train": len(train_idx),
        "n_test": len(test_idx),
    }


# ============================================================
# main
# ============================================================

# PURPOSE: Siamese 実験のメインエントリーポイント
def main():
    parser = argparse.ArgumentParser(description="Wave 9/10 Siamese CCL 距離学習")
    parser.add_argument("-n", "--max-functions", type=int, default=200,
                        help="抽出する最大関数数 (デフォルト: 200)")
    parser.add_argument("--max-pairs", type=int, default=2000,
                        help="学習ペア数 (デフォルト: 2000)")
    parser.add_argument("--epochs", type=int, default=200,
                        help="学習エポック数 (デフォルト: 200)")
    parser.add_argument("--lr", type=float, default=0.001,
                        help="学習率 (デフォルト: 0.001)")
    parser.add_argument("--target-dir", type=str, default=None,
                        help="対象ディレクトリ")
    parser.add_argument("--seeds", type=int, default=3,
                        help="ランダムシード数 (デフォルト: 3)")
    parser.add_argument("--extra-features", action="store_true",
                        help="9B 拡張特徴量を追加 (43d → 49d)")
    parser.add_argument("--v2-only", action="store_true",
                        help="V2 Residual のみ実行 (高速)")
    parser.add_argument("--label", type=str, default="",
                        help="結果ファイルのサフィックスラベル")
    parser.add_argument("--hidden", type=int, default=128,
                        help="隠れ層サイズ (デフォルト: 128)")
    args = parser.parse_args()

    if not HAS_TORCH:
        print("❌ PyTorch が利用できません。")
        print("   /tmp/torch_env/bin/python で実行してください")
        sys.exit(1)

    # ターゲットディレクトリ
    if args.target_dir:
        target_root = Path(args.target_dir)
    else:
        target_root = _MEKHANE_SRC / "mekhane"

    if not target_root.exists():
        print(f"❌ ディレクトリが見つかりません: {target_root}")
        sys.exit(1)

    print(f"🎯 対象: {target_root}")
    print(f"🔬 Siamese CCL 距離学習実験")
    print(f"   PyTorch: {torch.__version__}, hidden: {args.hidden}")

    # Phase 1: 関数抽出
    print(f"\n📋 Phase 1: 関数抽出 (max {args.max_functions})...")
    functions = extract_functions(target_root, max_functions=args.max_functions)
    print(f"   抽出: {len(functions)} 関数")

    if len(functions) < 20:
        print("❌ 関数数が不十分 (最低 20 必要)")
        sys.exit(1)

    # Phase 2: データ準備
    extra_label = " (+9B 49d)" if args.extra_features else " (43d)"
    print(f"\n📋 Phase 2: 学習データ準備 (max {args.max_pairs} ペア){extra_label}...")
    ccl_a, ccl_b, gt_dist = prepare_training_data(
        functions, max_pairs=args.max_pairs, seed=42,
        extra_features=args.extra_features,
    )
    print(f"   ペア: {len(gt_dist)}, 特徴量: {ccl_a.shape[1]}d")
    print(f"   GT 距離: mean={gt_dist.mean():.3f}, std={gt_dist.std():.3f}")

    # Phase 3: 学習 + 評価 (複数シード)
    if args.v2_only:
        models = {"V2_Residual": SiameseV2}
    else:
        models = {
            "V2_Residual": SiameseV2,
            "V3_CrossAttn": SiameseV3,
        }

    print(f"\n📊 Phase 3: Siamese 学習 ({args.seeds} seeds × {len(models)} models)")
    print("=" * 60)

    all_results = {}
    for model_name, model_class in models.items():
        seed_results = []
        for s in range(args.seeds):
            seed = 42 + s * 17
            print(f"\n--- {model_name} (seed={seed}) ---")
            result = train_and_evaluate(
                ccl_a, ccl_b, gt_dist,
                model_class=model_class,
                epochs=args.epochs,
                lr=args.lr,
                seed=seed,
                hidden=args.hidden,
            )
            seed_results.append(result)
            print(f"   → train_ρ={result['train_rho']:.4f}, test_ρ={result['test_rho']:.4f}, best_ρ={result['best_test_rho']:.4f}@{result['best_epoch']}")

        all_results[model_name] = seed_results

    # 結果サマリ
    print("\n" + "=" * 60)
    print("結果サマリ")
    print("=" * 60)
    print(f"{'モデル':<20} {'test_ρ mean':>12} {'test_ρ std':>12} {'best_ρ max':>12}")
    print("-" * 60)

    for model_name, results in all_results.items():
        test_rhos = [r['test_rho'] for r in results]
        best_rhos = [r['best_test_rho'] for r in results]
        mean_rho = np.mean(test_rhos)
        std_rho = np.std(test_rhos)
        max_best = np.max(best_rhos)
        print(f"{model_name:<20} {mean_rho:>12.4f} {std_rho:>12.4f} {max_best:>12.4f}")

    print("=" * 60)

    # 結果保存
    suffix = f"_{args.label}" if args.label else ""
    output_path = Path(__file__).parent / f"wave9_siamese_results{suffix}.md"
    lines = [
        "# Wave 9/10 Siamese CCL 距離学習 — 結果",
        "",
        f"- 関数数: {len(functions)}",
        f"- ペア数: {len(gt_dist)}",
        f"- 特徴量: {ccl_a.shape[1]}d (CCL 27d + AST 16d)",
        f"- GT: AST Levenshtein 正規化距離",
        f"- エポック数: {args.epochs}, 学習率: {args.lr}, 隠れ層: {args.hidden}",
        "",
        "## 結果",
        "",
        "| モデル | test_ρ mean | test_ρ std | best_ρ max |",
        "|:---|---:|---:|---:|",
    ]
    for model_name, results in all_results.items():
        test_rhos = [r['test_rho'] for r in results]
        best_rhos = [r['best_test_rho'] for r in results]
        mean_rho = np.mean(test_rhos)
        std_rho = np.std(test_rhos)
        max_best = np.max(best_rhos)
        lines.append(f"| {model_name} | {mean_rho:.4f} | {std_rho:.4f} | {max_best:.4f} |")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n📄 結果保存: {output_path}")


if __name__ == "__main__":
    main()
