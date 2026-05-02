"""Phase 3: Valence-specific データで Projection Head を訓練。

PURPOSE: Phase 2 の教訓 — NLI (論理的含意) ≠ Valence (感情的極性)。
Sentiment データから明確な Valence 対立トリプレットを構築し、
Phase 2 と同じ Projection Head アーキテクチャで再訓練する。

PROOF: walkthrough.md Phase 2 結果 → Phase 3 設計
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
import torch.nn.functional as F
from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from torch.utils.data import DataLoader, Dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── ハイパーパラメータ ──
BASE_MODEL = "sentence-transformers/all-mpnet-base-v2"
VALENCE_DIM = 32
TRIPLET_MARGIN = 0.3      # 射影空間用。Phase 2 の 0.5 だと即収束した
LR_HEAD = 5e-4            # Phase 2 より高め (データが小さいため)
ALPHA_ORTHO = 0.1
EPOCHS = 10               # データが小さいのでエポック増
BATCH_SIZE = 32
OUTPUT_DIR = "./output/valence-phase3"


# ── Projection Head (Phase 2 と同一) ──
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


# ── Valence トリプレット構築 ──
def build_valence_triplets_from_sst2() -> list[tuple[str, str, str]]:
    """SST-2 から Valence トリプレットを構築。

    戦略: positive 文と negative 文をランダムにペアリング。
    anchor=positive文, positive=別のpositive文, negative=negative文。
    """
    logger.info("SST-2 データセットを読込中...")
    ds = load_dataset("stanfordnlp/sst2", split="train")

    pos_texts = [row["sentence"] for row in ds if row["label"] == 1]
    neg_texts = [row["sentence"] for row in ds if row["label"] == 0]

    logger.info(f"  Positive 文: {len(pos_texts)}")
    logger.info(f"  Negative 文: {len(neg_texts)}")

    # シャッフル
    random.shuffle(pos_texts)
    random.shuffle(neg_texts)

    triplets = []
    n = min(len(pos_texts) // 2, len(neg_texts))

    for i in range(n):
        anchor = pos_texts[2 * i]
        positive = pos_texts[2 * i + 1]
        negative = neg_texts[i]
        triplets.append((anchor, positive, negative))

    # 逆パターンも追加: anchor=neg, positive=別neg, negative=pos
    random.shuffle(pos_texts)
    random.shuffle(neg_texts)
    n2 = min(len(neg_texts) // 2, len(pos_texts))
    for i in range(n2):
        anchor = neg_texts[2 * i]
        positive = neg_texts[2 * i + 1]
        negative = pos_texts[i]
        triplets.append((anchor, positive, negative))

    random.shuffle(triplets)
    logger.info(f"  SST-2 トリプレット数: {len(triplets)}")
    return triplets


def build_hgk_valence_triplets() -> list[tuple[str, str, str]]:
    """HGK ドメイン特化の手動 Valence トリプレット。"""
    # Valence 極性が明確な文を手動定義
    positive_texts = [
        "この設計は美しく、効率的だ",
        "実験は成功し、仮説が支持された",
        "コードの品質は高い",
        "テスト結果は全て pass した",
        "このアプローチは問題を解決する",
        "プロジェクトは順調に進んでいる",
        "チームの生産性が向上している",
        "品質改善が実現した",
        "Kalon に近い出力が得られた",
        "構造の整合性が保たれている",
        "This approach is elegant and effective",
        "The experiment yielded positive results",
        "Code quality has significantly improved",
        "The architecture is well-designed and maintainable",
        "Performance optimization was successful",
        "The test suite provides comprehensive coverage",
        "Documentation is clear and actionable",
        "The refactoring reduced technical debt",
        "This is a good solution to the problem",
        "The design pattern fits perfectly here",
    ]
    negative_texts = [
        "この設計は醜く、非効率的だ",
        "実験は失敗し、仮説が棄却された",
        "コードの品質は低い",
        "テスト結果はエラーだらけだ",
        "このアプローチは新たな問題を生む",
        "プロジェクトは行き詰まっている",
        "生産性が著しく低下している",
        "品質が劣化した",
        "出力に違和感がある。Kalon から遠い",
        "構造の整合性が崩壊している",
        "This approach is clumsy and useless",
        "The experiment produced negative results",
        "Code quality has severely degraded",
        "The architecture is poorly designed and unmaintainable",
        "Performance has deteriorated significantly",
        "The test suite has critical gaps",
        "Documentation is confusing and incomplete",
        "The refactoring introduced new bugs",
        "This solution creates more problems than it solves",
        "The design pattern is completely wrong here",
    ]

    triplets = []
    n = len(positive_texts)
    for i in range(n):
        # anchor=pos[i], positive=pos[(i+1)%n], negative=neg[i]
        triplets.append((positive_texts[i], positive_texts[(i + 1) % n], negative_texts[i]))
        # anchor=neg[i], positive=neg[(i+1)%n], negative=pos[i]
        triplets.append((negative_texts[i], negative_texts[(i + 1) % n], positive_texts[i]))

    logger.info(f"  HGK 手動トリプレット数: {len(triplets)}")
    return triplets


class TripletDataset(Dataset):
    def __init__(self, anchor_embs, positive_embs, negative_embs):
        self.anchor = anchor_embs
        self.positive = positive_embs
        self.negative = negative_embs

    def __len__(self):
        return len(self.anchor)

    def __getitem__(self, idx):
        return self.anchor[idx], self.positive[idx], self.negative[idx]


# ── Valence 弁別テスト ──
def valence_discrimination_test(
    model: SentenceTransformer,
    proj_head: ValenceProjectionHead | None = None,
    device: torch.device = torch.device("cpu"),
) -> dict:
    """Valence 弁別力を測定。"""
    pairs_opposing = [
        ("この設計は美しく、効率的だ", "この設計は醜く、非効率的だ"),
        ("実験は成功し、仮説が支持された", "実験は失敗し、仮説が棄却された"),
        ("このアプローチは問題を解決する", "このアプローチは新たな問題を生む"),
        ("コードの品質は高い", "コードの品質は低い"),
        ("This approach is elegant and effective", "This approach is clumsy and useless"),
    ]
    pairs_similar = [
        ("この設計は美しく、効率的だ", "この設計は優雅で、パフォーマンスが良い"),
        ("実験は成功した", "テストは pass した"),
        ("コードの品質は高い", "コードはよく書かれている"),
        ("This is a good solution", "This is an excellent approach"),
    ]

    def cos_sim(a_text, b_text):
        embs = model.encode([a_text, b_text], convert_to_numpy=True)
        if proj_head is not None:
            with torch.no_grad():
                t = torch.tensor(embs, dtype=torch.float32, device=device)
                t = proj_head(t)
                embs = t.cpu().numpy()
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        embs = embs / np.maximum(norms, 1e-8)
        return float(embs[0] @ embs[1])

    opposing_sims = [cos_sim(a, b) for a, b in pairs_opposing]
    similar_sims = [cos_sim(a, b) for a, b in pairs_similar]

    mean_opp = float(np.mean(opposing_sims))
    mean_sim = float(np.mean(similar_sims))
    gap = mean_sim - mean_opp

    logger.info(f"  対立平均: {mean_opp:.4f} | 類似平均: {mean_sim:.4f} | gap: {gap:.4f}")
    return {"opposing": mean_opp, "similar": mean_sim, "gap": gap}


def main():
    parser = argparse.ArgumentParser(description="Phase 3: Valence-specific データ")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--log-file", type=str, default=None)
    parser.add_argument("--epochs", type=int, default=None, help="エポック数 (Early Stopping 用)")
    parser.add_argument("--output-dir", type=str, default=None, help="出力ディレクトリ")
    parser.add_argument("--seed", type=int, default=42, help="ランダムシード (再現性)")
    args = parser.parse_args()

    # シード固定 (再現性)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    if args.log_file:
        fh = logging.FileHandler(args.log_file, mode="w")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logging.getLogger().addHandler(fh)

    epochs = 2 if args.dry_run else (args.epochs if args.epochs else EPOCHS)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"デバイス: {device} | seed: {args.seed}")

    # ── Encoder 読込 (凍結) ──
    logger.info(f"ベースモデル読込: {BASE_MODEL}")
    encoder = SentenceTransformer(BASE_MODEL, device=str(device))
    embed_dim = encoder.get_sentence_embedding_dimension()

    # ── Valence トリプレット構築 ──
    sst2_triplets = build_valence_triplets_from_sst2()
    hgk_triplets = build_hgk_valence_triplets()

    if args.dry_run:
        sst2_triplets = sst2_triplets[:200]

    # HGK ペアを 10x オーバーサンプリング (ドメイン特化を強化)
    all_triplets = sst2_triplets + hgk_triplets * 10
    random.shuffle(all_triplets)
    logger.info(f"総トリプレット数: {len(all_triplets)} (SST2={len(sst2_triplets)}, HGK={len(hgk_triplets)}×10)")

    # ── 事前 embedding ──
    logger.info("事前 embedding 計算中...")
    anchors = [t[0] for t in all_triplets]
    positives = [t[1] for t in all_triplets]
    negatives = [t[2] for t in all_triplets]

    anchor_embs = encoder.encode(anchors, batch_size=256, show_progress_bar=True, convert_to_numpy=True)
    positive_embs = encoder.encode(positives, batch_size=256, show_progress_bar=True, convert_to_numpy=True)
    negative_embs = encoder.encode(negatives, batch_size=256, show_progress_bar=True, convert_to_numpy=True)

    anchor_t = torch.tensor(anchor_embs, dtype=torch.float32)
    positive_t = torch.tensor(positive_embs, dtype=torch.float32)
    negative_t = torch.tensor(negative_embs, dtype=torch.float32)

    dataset = TripletDataset(anchor_t, positive_t, negative_t)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, drop_last=True)

    # ── Projection Head ──
    proj_head = ValenceProjectionHead(input_dim=embed_dim, valence_dim=VALENCE_DIM).to(device)
    logger.info(f"Projection Head: {embed_dim}d → {VALENCE_DIM}d (パラメータ: {sum(p.numel() for p in proj_head.parameters()):,})")

    # ── Baseline ──
    logger.info("=== Baseline (768d 全空間) ===")
    baseline_full = valence_discrimination_test(encoder, proj_head=None, device=device)
    proj_head.eval()
    logger.info("=== Baseline (32d 射影, 初期重み) ===")
    baseline_proj = valence_discrimination_test(encoder, proj_head=proj_head, device=device)
    proj_head.train()

    # ── 訓練 ──
    optimizer = torch.optim.AdamW(proj_head.parameters(), lr=LR_HEAD, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    triplet_loss_fn = nn.TripletMarginLoss(margin=TRIPLET_MARGIN, p=2)

    logger.info(f"=== 訓練開始 (epochs={epochs}, batches={len(dataloader)}) ===")

    for epoch in range(epochs):
        total_loss = 0.0
        total_trip = 0.0
        total_orth = 0.0
        n_batches = 0

        for batch_idx, (anc, pos, neg) in enumerate(dataloader):
            anc, pos, neg = anc.to(device), pos.to(device), neg.to(device)

            anc_proj = proj_head(anc)
            pos_proj = proj_head(pos)
            neg_proj = proj_head(neg)

            l_triplet = triplet_loss_fn(anc_proj, pos_proj, neg_proj)
            l_ortho = proj_head.orthogonal_loss()
            loss = l_triplet + ALPHA_ORTHO * l_ortho

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            total_trip += l_triplet.item()
            total_orth += l_ortho.item()
            n_batches += 1

        scheduler.step()
        avg_loss = total_loss / max(n_batches, 1)
        avg_trip = total_trip / max(n_batches, 1)
        avg_orth = total_orth / max(n_batches, 1)

        # エポック毎の Valence gap 追跡
        proj_head.eval()
        epoch_result = valence_discrimination_test(encoder, proj_head=proj_head, device=device)
        proj_head.train()

        logger.info(
            f"  Epoch {epoch+1}/{epochs} | Loss: {avg_loss:.4f} (trip={avg_trip:.4f}, orth={avg_orth:.4f}) "
            f"| Valence gap: {epoch_result['gap']:.4f} | lr: {scheduler.get_last_lr()[0]:.6f}"
        )

    # ── 最終評価 ──
    proj_head.eval()
    logger.info("=== 最終評価 (768d 全空間) ===")
    final_full = valence_discrimination_test(encoder, proj_head=None, device=device)
    logger.info("=== 最終評価 (32d 射影, 訓練済み) ===")
    final_proj = valence_discrimination_test(encoder, proj_head=proj_head, device=device)

    # ── FIM 分析 ──
    logger.info("=== FIM 分析 ===")
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

    # 全空間 FIM
    X_full = raw_embs - raw_embs.mean(axis=0)
    K_full = X_full @ X_full.T / len(test_texts)
    evals_full = np.sort(np.linalg.eigvalsh(K_full))[::-1]
    evals_full = evals_full[evals_full > 1e-10]

    # 射影空間 FIM
    with torch.no_grad():
        proj_embs = proj_head(torch.tensor(raw_embs, dtype=torch.float32, device=device)).cpu().numpy()
    X_proj = proj_embs - proj_embs.mean(axis=0)
    K_proj = X_proj @ X_proj.T / len(test_texts)
    evals_proj = np.sort(np.linalg.eigvalsh(K_proj))[::-1]
    evals_proj = evals_proj[evals_proj > 1e-10]

    # stiff modes
    gap_ratio = 1.20
    stiff_proj = len(evals_proj)
    for i in range(len(evals_proj) - 1):
        r = evals_proj[i] / evals_proj[i + 1] if evals_proj[i + 1] > 0 else float("inf")
        if r >= gap_ratio and i > 0:
            stiff_proj = i + 1
            break

    logger.info(f"  全空間 Top-5: {[f'{v:.6f}' for v in evals_full[:5]]}")
    logger.info(f"  射影空間 Top-5: {[f'{v:.6f}' for v in evals_proj[:5]]}")
    logger.info(f"  射影空間 stiff modes: {stiff_proj}")

    # ── 保存 ──
    output_dir = args.output_dir if args.output_dir else (OUTPUT_DIR if not args.dry_run else "/tmp/solvent_phase3_dry")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    torch.save(proj_head.state_dict(), out / "proj_head.pt")

    meta = {
        "phase": 3,
        "data_source": "SST-2 + HGK manual",
        "total_triplets": len(all_triplets),
        "sst2_triplets": len(sst2_triplets),
        "hgk_triplets": len(hgk_triplets),
        "epochs": epochs,
        "baseline_gap_full": baseline_full["gap"],
        "baseline_gap_proj": baseline_proj["gap"],
        "final_gap_full": final_full["gap"],
        "final_gap_proj": final_proj["gap"],
        "final_opposing_proj": final_proj["opposing"],
        "final_similar_proj": final_proj["similar"],
        "fim_stiff_modes_proj": int(stiff_proj),
        "fim_top5_full": evals_full[:5].tolist(),
        "fim_top5_proj": evals_proj[:5].tolist(),
    }
    (out / "training_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))

    # ── サマリー ──
    logger.info("")
    logger.info("=" * 60)
    logger.info("📊 Phase 3 結果サマリー")
    logger.info("=" * 60)
    logger.info(f"  Valence gap (768d 全空間):    {baseline_full['gap']:.4f} → {final_full['gap']:.4f}")
    logger.info(f"  Valence gap (32d 射影空間):   {baseline_proj['gap']:.4f} → {final_proj['gap']:.4f}")
    logger.info(f"  射影空間 FIM stiff modes: {stiff_proj}")
    logger.info(f"  対立ペア cos (proj): {final_proj['opposing']:.4f}")
    logger.info(f"  類似ペア cos (proj): {final_proj['similar']:.4f}")
    logger.info(f"  目標: gap > 0.1")


if __name__ == "__main__":
    main()
