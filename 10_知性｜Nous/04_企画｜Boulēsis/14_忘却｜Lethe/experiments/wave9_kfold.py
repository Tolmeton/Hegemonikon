#!/usr/bin/env python3
"""Wave 9 Siamese k-fold 交差検証

PURPOSE: Siamese test ρ の安定性を 5-fold CV で検証し、信頼区間を算出する。
  wave9_experiment.py の Siamese 訓練コードを再利用。
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from wave9_experiment import (
    extract_functions,
    generate_wave9_pairs,
    _build_feature_vectors,
    _normalize_vectors,
    _extract_ngrams,
    extract_ccl_extra_features,
    Wave9PairAnalysis,
)
from p3b_benchmark import spearman_rho, FunctionInfo

_HGK_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_MEKHANE_SRC = _HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"


# PURPOSE: k-fold CV で Siamese の test ρ を評価
def kfold_siamese(
    functions: list[FunctionInfo],
    pairs: list[Wave9PairAnalysis],
    k: int = 5,
    epochs: int = 150,
    lr: float = 0.001,
    hidden_dim: int = 64,
    seed: int = 42,
) -> dict:
    """k-fold 交差検証で Siamese test ρ の安定性を評価する。"""
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
    except ImportError:
        print("❌ PyTorch が必要です")
        return {"error": "PyTorch not available"}

    random.seed(seed)
    torch.manual_seed(seed)

    # 特徴量構築
    ccl_vecs, gt_vecs = _build_feature_vectors(functions)
    ccl_vecs = _normalize_vectors(ccl_vecs)
    gt_vecs = _normalize_vectors(gt_vecs)

    name_to_idx = {f.name: i for i, f in enumerate(functions)}

    # ペアデータ準備
    vecs_a, vecs_b, targets = [], [], []
    for p in pairs:
        ia = name_to_idx.get(p.func_a)
        ib = name_to_idx.get(p.func_b)
        if ia is None or ib is None:
            continue
        vecs_a.append(ccl_vecs[ia] + gt_vecs[ia])
        vecs_b.append(ccl_vecs[ib] + gt_vecs[ib])
        targets.append(p.ast_lev_distance)

    # シャッフル
    indices = list(range(len(vecs_a)))
    random.shuffle(indices)
    vecs_a = [vecs_a[i] for i in indices]
    vecs_b = [vecs_b[i] for i in indices]
    targets = [targets[i] for i in indices]

    all_a = torch.FloatTensor(vecs_a)
    all_b = torch.FloatTensor(vecs_b)
    all_t = torch.FloatTensor(targets)
    input_dim = all_a.shape[1]

    n_total = len(all_a)
    fold_size = n_total // k

    print(f"📊 {k}-fold CV: {n_total} ペア, fold_size={fold_size}")
    print(f"   入力次元: {input_dim}d, hidden={hidden_dim}, epochs={epochs}")

    # Siamese 定義 (関数内で毎 fold 再初期化)
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
        def forward(self, x):
            return self.net(x)

    fold_rhos = []
    batch_size = 64

    for fold in range(k):
        # fold 分割
        test_start = fold * fold_size
        test_end = test_start + fold_size if fold < k - 1 else n_total

        test_idx = list(range(test_start, test_end))
        train_idx = list(range(0, test_start)) + list(range(test_end, n_total))

        train_a = all_a[train_idx]
        train_b = all_b[train_idx]
        train_t = all_t[train_idx]
        test_a = all_a[test_idx]
        test_b = all_b[test_idx]
        test_t = all_t[test_idx]

        # 毎 fold で新しいモデルを初期化
        torch.manual_seed(seed + fold)
        encoder = SiameseEncoder(input_dim, hidden_dim)
        optimizer = optim.Adam(encoder.parameters(), lr=lr, weight_decay=1e-4)

        best_test_rho = -1.0

        for epoch in range(epochs):
            encoder.train()
            perm = torch.randperm(len(train_a))
            sa, sb, st = train_a[perm], train_b[perm], train_t[perm]

            for start in range(0, len(sa), batch_size):
                end = min(start + batch_size, len(sa))
                ea = encoder(sa[start:end])
                eb = encoder(sb[start:end])
                pred = torch.sqrt(torch.sum((ea - eb) ** 2, dim=1) + 1e-8)
                loss = torch.mean((pred - st[start:end]) ** 2)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            # 10 epoch ごとにテスト
            if (epoch + 1) % 10 == 0 or epoch == epochs - 1:
                encoder.eval()
                with torch.no_grad():
                    te_a = encoder(test_a)
                    te_b = encoder(test_b)
                    tp = torch.sqrt(torch.sum((te_a - te_b) ** 2, dim=1) + 1e-8)
                    rho = spearman_rho(tp.tolist(), test_t.tolist())
                    if rho > best_test_rho:
                        best_test_rho = rho

        fold_rhos.append(best_test_rho)
        print(f"   Fold {fold+1}/{k}: test ρ = {best_test_rho:.4f} (train={len(train_a)}, test={len(test_a)})")

    # 統計
    mean_rho = sum(fold_rhos) / k
    std_rho = math.sqrt(sum((r - mean_rho) ** 2 for r in fold_rhos) / max(k - 1, 1))
    ci95 = 1.96 * std_rho / math.sqrt(k)

    print(f"\n{'='*50}")
    print(f"📊 {k}-fold CV 結果:")
    print(f"   Mean test ρ = {mean_rho:.4f} ± {std_rho:.4f}")
    print(f"   95% CI: [{mean_rho - ci95:.4f}, {mean_rho + ci95:.4f}]")
    print(f"   Fold ρ: {[f'{r:.4f}' for r in fold_rhos]}")
    print(f"{'='*50}")

    # 結果保存
    result = {
        "k": k,
        "fold_rhos": fold_rhos,
        "mean_rho": mean_rho,
        "std_rho": std_rho,
        "ci95_lower": mean_rho - ci95,
        "ci95_upper": mean_rho + ci95,
        "n_total": n_total,
        "epochs": epochs,
        "hidden_dim": hidden_dim,
    }

    output_path = Path(__file__).parent / "wave9_kfold_results.md"
    lines = [
        "# Wave 9 Siamese k-fold 交差検証結果",
        "",
        f"- k = {k}",
        f"- ペア数: {n_total}",
        f"- Epochs: {epochs}, Hidden: {hidden_dim}",
        "",
        "## Fold 別結果",
        "",
        "| Fold | test ρ |",
        "|---:|---:|",
    ]
    for i, r in enumerate(fold_rhos):
        lines.append(f"| {i+1} | {r:.4f} |")
    lines.extend([
        "",
        f"**Mean test ρ = {mean_rho:.4f} ± {std_rho:.4f}**",
        f"**95% CI: [{mean_rho - ci95:.4f}, {mean_rho + ci95:.4f}]**",
    ])
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n📄 保存: {output_path}")

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Wave 9 Siamese k-fold CV")
    parser.add_argument("-k", type=int, default=5, help="fold 数 (デフォルト: 5)")
    parser.add_argument("-n", "--max-functions", type=int, default=500,
                        help="最大関数数 (デフォルト: 500)")
    parser.add_argument("--max-pairs", type=int, default=2000,
                        help="最大ペア数 (デフォルト: 2000)")
    parser.add_argument("--epochs", type=int, default=150,
                        help="Siamese 訓練エポック (デフォルト: 150)")
    parser.add_argument("--hidden", type=int, default=64,
                        help="隠れ層次元 (デフォルト: 64)")
    parser.add_argument("--target-dir", type=str, default=None)
    args = parser.parse_args()

    if args.target_dir:
        target_root = Path(args.target_dir)
    else:
        target_root = _MEKHANE_SRC / "mekhane"

    if not target_root.exists():
        print(f"❌ ディレクトリが見つかりません: {target_root}")
        sys.exit(1)

    print(f"🎯 対象: {target_root}")

    # 関数抽出
    print(f"📋 関数抽出 (max {args.max_functions})...")
    functions = extract_functions(target_root, max_functions=args.max_functions)
    print(f"   抽出: {len(functions)} 関数")

    # ペア生成
    print(f"📋 ペア生成 (max {args.max_pairs})...")
    pairs = generate_wave9_pairs(functions, max_pairs=args.max_pairs)
    print(f"   ペア: {len(pairs)}")

    # k-fold CV
    kfold_siamese(
        functions, pairs,
        k=args.k,
        epochs=args.epochs,
        hidden_dim=args.hidden,
    )


if __name__ == "__main__":
    main()
