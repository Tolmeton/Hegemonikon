"""複数シード統計 + ker(G) 射影空間分析。

PURPOSE: Phase 3 の再現性を検証し、ker(G) の構造を定量化する。
(1) seed 0-9 で Projection Head を訓練し gap の分布を取得
(2) 各 seed の射影空間で FIM / density-coherence / Valence 弁別を評価

PROOF: walkthrough.md Phase 3 シード感度問題
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from datasets import load_dataset
from scipy import stats
from sentence_transformers import SentenceTransformer
from torch.utils.data import DataLoader, Dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── ハイパーパラメータ (Phase 3 と同一) ──
BASE_MODEL = "sentence-transformers/all-mpnet-base-v2"
VALENCE_DIM = 32
TRIPLET_MARGIN = 0.3
LR_HEAD = 5e-4
ALPHA_ORTHO = 0.1
BATCH_SIZE = 32


class ValenceProjectionHead(nn.Module):
    def __init__(self, input_dim: int = 768, valence_dim: int = VALENCE_DIM):
        super().__init__()
        self.proj = nn.Linear(input_dim, valence_dim, bias=False)
        self.norm = nn.LayerNorm(valence_dim)
        nn.init.orthogonal_(self.proj.weight)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.norm(self.proj(x))

    def orthogonal_loss(self) -> torch.Tensor:
        W = self.proj.weight
        WtW = W @ W.T
        I = torch.eye(W.size(0), device=W.device)
        return torch.norm(WtW - I, p="fro") ** 2


class TripletDataset(Dataset):
    def __init__(self, anchor_embs, positive_embs, negative_embs):
        self.anchor = anchor_embs
        self.positive = positive_embs
        self.negative = negative_embs

    def __len__(self):
        return len(self.anchor)

    def __getitem__(self, idx):
        return self.anchor[idx], self.positive[idx], self.negative[idx]


def set_seed(seed: int):
    """全乱数源のシード固定。"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def build_triplets():
    """SST-2 + HGK トリプレット構築 (Phase 3 と同一)。"""
    ds = load_dataset("stanfordnlp/sst2", split="train")
    pos = [r["sentence"] for r in ds if r["label"] == 1]
    neg = [r["sentence"] for r in ds if r["label"] == 0]

    random.shuffle(pos)
    random.shuffle(neg)

    triplets = []
    n = min(len(pos) // 2, len(neg))
    for i in range(n):
        triplets.append((pos[2*i], pos[2*i+1], neg[i]))

    random.shuffle(pos)
    random.shuffle(neg)
    n2 = min(len(neg) // 2, len(pos))
    for i in range(n2):
        triplets.append((neg[2*i], neg[2*i+1], pos[i]))

    # HGK 手動ペア
    hgk_pos = [
        "この設計は美しく、効率的だ", "実験は成功し、仮説が支持された",
        "コードの品質は高い", "テスト結果は全て pass した",
        "このアプローチは問題を解決する", "プロジェクトは順調に進んでいる",
        "チームの生産性が向上している", "品質改善が実現した",
        "Kalon に近い出力が得られた", "構造の整合性が保たれている",
        "This approach is elegant and effective", "The experiment yielded positive results",
        "Code quality has significantly improved", "The architecture is well-designed and maintainable",
        "Performance optimization was successful", "The test suite provides comprehensive coverage",
        "Documentation is clear and actionable", "The refactoring reduced technical debt",
        "This is a good solution to the problem", "The design pattern fits perfectly here",
    ]
    hgk_neg = [
        "この設計は醜く、非効率的だ", "実験は失敗し、仮説が棄却された",
        "コードの品質は低い", "テスト結果はエラーだらけだ",
        "このアプローチは新たな問題を生む", "プロジェクトは行き詰まっている",
        "生産性が著しく低下している", "品質が劣化した",
        "出力に違和感がある。Kalon から遠い", "構造の整合性が崩壊している",
        "This approach is clumsy and useless", "The experiment produced negative results",
        "Code quality has severely degraded", "The architecture is poorly designed and unmaintainable",
        "Performance has deteriorated significantly", "The test suite has critical gaps",
        "Documentation is confusing and incomplete", "The refactoring introduced new bugs",
        "This solution creates more problems than it solves", "The design pattern is completely wrong here",
    ]
    hgk_triplets = []
    nh = len(hgk_pos)
    for i in range(nh):
        hgk_triplets.append((hgk_pos[i], hgk_pos[(i+1) % nh], hgk_neg[i]))
        hgk_triplets.append((hgk_neg[i], hgk_neg[(i+1) % nh], hgk_pos[i]))

    all_triplets = triplets + hgk_triplets * 10
    random.shuffle(all_triplets)
    return all_triplets, len(triplets), len(hgk_triplets)


def valence_gap(encoder, proj_head, device):
    """Valence 弁別 gap を測定。"""
    pairs_opp = [
        ("この設計は美しく、効率的だ", "この設計は醜く、非効率的だ"),
        ("実験は成功し、仮説が支持された", "実験は失敗し、仮説が棄却された"),
        ("このアプローチは問題を解決する", "このアプローチは新たな問題を生む"),
        ("コードの品質は高い", "コードの品質は低い"),
        ("This approach is elegant and effective", "This approach is clumsy and useless"),
    ]
    pairs_sim = [
        ("この設計は美しく、効率的だ", "この設計は優雅で、パフォーマンスが良い"),
        ("実験は成功した", "テストは pass した"),
        ("コードの品質は高い", "コードはよく書かれている"),
        ("This is a good solution", "This is an excellent approach"),
    ]

    def cos(a, b):
        embs = encoder.encode([a, b], convert_to_numpy=True)
        if proj_head is not None:
            with torch.no_grad():
                t = torch.tensor(embs, dtype=torch.float32, device=device)
                t = proj_head(t)
                embs = t.cpu().numpy()
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        embs = embs / np.maximum(norms, 1e-8)
        return float(embs[0] @ embs[1])

    opp = [cos(a, b) for a, b in pairs_opp]
    sim = [cos(a, b) for a, b in pairs_sim]
    return float(np.mean(sim) - np.mean(opp)), float(np.mean(opp)), float(np.mean(sim))


def train_one_seed(encoder, all_triplets, seed, epochs, device):
    """1シードで Projection Head を訓練し結果を返す。"""
    set_seed(seed)

    # シード後に再シャッフル
    random.shuffle(all_triplets)

    anchors = [t[0] for t in all_triplets]
    positives = [t[1] for t in all_triplets]
    negatives = [t[2] for t in all_triplets]

    # 事前 embedding は encoder 凍結なので seed 不問
    anchor_t = torch.tensor(encoder.encode(anchors, batch_size=256, show_progress_bar=False, convert_to_numpy=True), dtype=torch.float32)
    positive_t = torch.tensor(encoder.encode(positives, batch_size=256, show_progress_bar=False, convert_to_numpy=True), dtype=torch.float32)
    negative_t = torch.tensor(encoder.encode(negatives, batch_size=256, show_progress_bar=False, convert_to_numpy=True), dtype=torch.float32)

    dataset = TripletDataset(anchor_t, positive_t, negative_t)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, drop_last=True)

    embed_dim = anchor_t.shape[1]
    set_seed(seed)  # Projection Head 初期化前に再固定
    proj_head = ValenceProjectionHead(input_dim=embed_dim, valence_dim=VALENCE_DIM).to(device)

    optimizer = torch.optim.AdamW(proj_head.parameters(), lr=LR_HEAD, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    triplet_loss_fn = nn.TripletMarginLoss(margin=TRIPLET_MARGIN, p=2)

    # Baseline
    proj_head.eval()
    baseline_gap, _, _ = valence_gap(encoder, proj_head, device)
    proj_head.train()

    epoch_gaps = []
    for epoch in range(epochs):
        total_loss = 0.0
        n_batches = 0
        for anc, pos, neg in dataloader:
            anc, pos, neg = anc.to(device), pos.to(device), neg.to(device)
            anc_p = proj_head(anc)
            pos_p = proj_head(pos)
            neg_p = proj_head(neg)
            l_trip = triplet_loss_fn(anc_p, pos_p, neg_p)
            l_orth = proj_head.orthogonal_loss()
            loss = l_trip + ALPHA_ORTHO * l_orth
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            n_batches += 1
        scheduler.step()

        proj_head.eval()
        gap, opp, sim = valence_gap(encoder, proj_head, device)
        proj_head.train()
        epoch_gaps.append(gap)

    # 最終評価
    proj_head.eval()
    final_gap, final_opp, final_sim = valence_gap(encoder, proj_head, device)

    # ker(G) 分析: FIM stiff modes (射影空間)
    test_texts = [
        "kalon の定義を確認する。Fix(G∘F) の不動点条件を検証した。",
        "テスト結果は全て pass。CI/CD パイプラインが正常に動作している。",
        "このアプローチは失敗した。根本的な設計変更が必要。",
        "FEP の自由エネルギー原理に基づき、認知制約を導出した。",
        "バグを発見。TypeError が発生しており、修正が必要。",
        "コードの品質は高く、Kalon に近い。",
        "パフォーマンスが低下している。最適化が必要。",
        "新しい定理を発見。24動詞の対称性が証明された。",
        "データベースが破損。バックアップから復元が必要。",
        "セッションは成功裏に終了。全目標を達成した。",
        "このプロジェクトは行き詰まっている。方向転換すべき。",
        "MECE 構造が維持されている。整理完了。",
        "エラーが連続している。根本原因の特定ができていない。",
        "sprint 計画を策定。次の2週間の目標を設定した。",
        "実験結果は予想通り。仮説が支持されている。",
        "deadline に間に合わない可能性がある。",
        "チームの士気は高い。生産性が向上している。",
        "技術的負債が蓄積している。リファクタリングが急務。",
        "設計レビューの結果、品質基準を満たしている。",
        "重大な脆弱性が発見された。緊急パッチが必要。",
    ]
    raw_embs = encoder.encode(test_texts, convert_to_numpy=True, show_progress_bar=False)
    with torch.no_grad():
        proj_embs = proj_head(torch.tensor(raw_embs, dtype=torch.float32, device=device)).cpu().numpy()

    X = proj_embs - proj_embs.mean(axis=0)
    K = X @ X.T / len(test_texts)
    evals = np.sort(np.linalg.eigvalsh(K))[::-1]
    evals = evals[evals > 1e-10]

    stiff = len(evals)
    for i in range(len(evals) - 1):
        r = evals[i] / evals[i+1] if evals[i+1] > 0 else float("inf")
        if r >= 1.20 and i > 0:
            stiff = i + 1
            break

    # density-coherence (簡易: 4文ずつチャンク)
    norms = np.linalg.norm(proj_embs, axis=1, keepdims=True)
    normed = proj_embs / np.maximum(norms, 1e-8)
    sim_mat = normed @ normed.T

    densities, coherences = [], []
    for ci in range(0, len(test_texts), 4):
        idx = list(range(ci, min(ci+4, len(test_texts))))
        if len(idx) < 2:
            continue
        chunk_d = []
        for ii in idx:
            top_k = np.sort(sim_mat[ii])[::-1][1:6]
            chunk_d.append(top_k.mean())
        densities.append(np.mean(chunk_d))
        pairs = [sim_mat[a, b] for ai, a in enumerate(idx) for b in idx[ai+1:]]
        coherences.append(np.mean(pairs) if pairs else 0)

    if len(densities) >= 3:
        rho_dc, p_dc = stats.spearmanr(densities, coherences)
    else:
        rho_dc, p_dc = float("nan"), float("nan")

    return {
        "seed": seed,
        "baseline_gap": baseline_gap,
        "final_gap": final_gap,
        "best_gap": max(epoch_gaps),
        "best_epoch": int(np.argmax(epoch_gaps)) + 1,
        "epoch_gaps": epoch_gaps,
        "final_opposing": final_opp,
        "final_similar": final_sim,
        "stiff_modes": int(stiff),
        "top5_evals": evals[:5].tolist(),
        "dc_rho": float(rho_dc),
        "dc_p": float(p_dc),
    }


def main():
    parser = argparse.ArgumentParser(description="複数シード + ker(G) 分析")
    parser.add_argument("--seeds", type=str, default="0-9", help="シード範囲 (例: 0-9)")
    parser.add_argument("--epochs", type=int, default=5, help="エポック数")
    parser.add_argument("--log-file", type=str, default=None)
    parser.add_argument("--output", type=str, default="./output/multi_seed_results.json")
    args = parser.parse_args()

    if args.log_file:
        fh = logging.FileHandler(args.log_file, mode="w")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logging.getLogger().addHandler(fh)

    # シード範囲のパース
    if "-" in args.seeds:
        start, end = args.seeds.split("-")
        seeds = list(range(int(start), int(end) + 1))
    else:
        seeds = [int(s) for s in args.seeds.split(",")]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"デバイス: {device}")
    logger.info(f"シード: {seeds}")
    logger.info(f"エポック: {args.epochs}")

    # Encoder 読込 (1回だけ)
    logger.info(f"ベースモデル読込: {BASE_MODEL}")
    encoder = SentenceTransformer(BASE_MODEL, device=str(device))

    # トリプレット構築 (seed ごとにシャッフル)
    set_seed(0)
    all_triplets, n_sst2, n_hgk = build_triplets()
    logger.info(f"トリプレット: {len(all_triplets)} (SST2={n_sst2}, HGK={n_hgk}×10)")

    # Baseline (射影なし)
    baseline_gap, _, _ = valence_gap(encoder, None, device)
    logger.info(f"全空間 Baseline gap: {baseline_gap:.4f}")

    # 各シードで訓練
    results = []
    for seed in seeds:
        logger.info(f"\n{'='*40} Seed {seed} {'='*40}")
        result = train_one_seed(encoder, list(all_triplets), seed, args.epochs, device)
        results.append(result)
        logger.info(
            f"  seed={seed} | baseline={result['baseline_gap']:.4f} | "
            f"best={result['best_gap']:.4f} (ep{result['best_epoch']}) | "
            f"final={result['final_gap']:.4f} | stiff={result['stiff_modes']} | "
            f"dc_rho={result['dc_rho']:.4f}"
        )

    # 統計サマリー
    gaps = [r["final_gap"] for r in results]
    best_gaps = [r["best_gap"] for r in results]
    stiffs = [r["stiff_modes"] for r in results]
    dc_rhos = [r["dc_rho"] for r in results]

    logger.info(f"\n{'='*60}")
    logger.info("📊 複数シード統計サマリー")
    logger.info("="*60)
    logger.info(f"  全空間 Baseline gap: {baseline_gap:.4f}")
    logger.info(f"  最終 gap:  mean={np.mean(gaps):.4f} ± {np.std(gaps):.4f}  range=[{min(gaps):.4f}, {max(gaps):.4f}]")
    logger.info(f"  ピーク gap: mean={np.mean(best_gaps):.4f} ± {np.std(best_gaps):.4f}")
    logger.info(f"  正転率: {sum(1 for g in gaps if g > 0)}/{len(gaps)} ({100*sum(1 for g in gaps if g > 0)/len(gaps):.0f}%)")
    logger.info(f"  stiff modes: mean={np.mean(stiffs):.1f} ± {np.std(stiffs):.1f}  [{min(stiffs)}, {max(stiffs)}]")
    logger.info(f"  D-C rho: mean={np.nanmean(dc_rhos):.4f} ± {np.nanstd(dc_rhos):.4f}")

    # 保存
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "config": {"seeds": seeds, "epochs": args.epochs, "model": BASE_MODEL},
        "baseline_gap_full": baseline_gap,
        "per_seed": results,
        "summary": {
            "final_gap_mean": float(np.mean(gaps)),
            "final_gap_std": float(np.std(gaps)),
            "best_gap_mean": float(np.mean(best_gaps)),
            "best_gap_std": float(np.std(best_gaps)),
            "positive_rate": sum(1 for g in gaps if g > 0) / len(gaps),
            "stiff_modes_mean": float(np.mean(stiffs)),
            "dc_rho_mean": float(np.nanmean(dc_rhos)),
        },
    }
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    logger.info(f"\n結果保存: {out}")


if __name__ == "__main__":
    main()
