"""Phase 2: Projection Head + Orthogonal Loss による Valence-aware Embedding.

PURPOSE: ker(G) の中だけを動かし、像（情報構造）を保存する。
Phase 1 の教訓: TripletLoss は全次元を均等に動かすため FIM stiff modes が劣化した。
Phase 2: encoder を凍結し、Projection head のみを訓練して Valence 軸を分離する。

PROOF: walkthrough.md Phase 1 結果 → Phase 2 設計
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from datasets import load_dataset
from scipy import stats
from sentence_transformers import SentenceTransformer
from torch.utils.data import DataLoader, Dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── ハイパーパラメータ ──
BASE_MODEL = "sentence-transformers/all-mpnet-base-v2"
VALENCE_DIM = 32          # Valence 射影空間の次元
TRIPLET_MARGIN = 0.5      # Phase 1 より大きいマージン (射影空間は狭い)
LR_HEAD = 2e-4            # Projection head の学習率
LR_ENCODER = 0.0          # encoder は凍結 (0 = frozen)
ALPHA_ORTHO = 0.1         # 直交正則化の重み
BETA_ALIGN = 0.05         # 元 embedding との alignment の重み
EPOCHS = 5
BATCH_SIZE = 32
MAX_SAMPLES = 50000
OUTPUT_DIR = "./output/valence-projhead"


# ── Projection Head ──
class ValenceProjectionHead(nn.Module):
    """768d → VALENCE_DIM の射影層。

    ker(G) 問題の操作化:
    - 全 embedding 空間から Valence 軸のみを抽出する射影
    - 直交正則化で Valence 軸同士の冗長性を排除
    """

    def __init__(self, input_dim: int = 768, valence_dim: int = VALENCE_DIM):
        super().__init__()
        self.proj = nn.Linear(input_dim, valence_dim, bias=False)
        self.norm = nn.LayerNorm(valence_dim)
        # 直交初期化 (Stiefel 多様体の一点)
        nn.init.orthogonal_(self.proj.weight)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.norm(self.proj(x))

    def orthogonal_loss(self) -> torch.Tensor:
        """直交正則化: ‖W^T W - I‖_F² を最小化。"""
        W = self.proj.weight  # (valence_dim, input_dim)
        WtW = W @ W.T  # (valence_dim, valence_dim)
        I = torch.eye(W.size(0), device=W.device)
        return torch.norm(WtW - I, p="fro") ** 2


# ── データセット ──
class TripletDataset(Dataset):
    """AllNLI トリプレットを encoder で事前 embed したデータセット。"""

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
    """Valence 弁別力を測定。proj_head がある場合は射影空間で測定。"""
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
        # L2 正規化してcos類似度
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        embs = embs / np.maximum(norms, 1e-8)
        return float(embs[0] @ embs[1])

    logger.info("=== Valence 弁別テスト ===")
    opposing_sims = []
    for a, b in pairs_opposing:
        sim = cos_sim(a, b)
        logger.info(f"  対立: {sim:.4f} | {a[:20]}... vs {b[:20]}...")
        opposing_sims.append(sim)

    similar_sims = []
    for a, b in pairs_similar:
        sim = cos_sim(a, b)
        logger.info(f"  類似: {sim:.4f} | {a[:20]}... vs {b[:20]}...")
        similar_sims.append(sim)

    mean_opp = float(np.mean(opposing_sims))
    mean_sim = float(np.mean(similar_sims))
    gap = mean_sim - mean_opp

    logger.info(f"  対立ペア平均 cos: {mean_opp:.4f}")
    logger.info(f"  類似ペア平均 cos: {mean_sim:.4f}")
    logger.info(f"  弁別ギャップ:     {gap:.4f}")
    logger.info(f"  目標: ギャップ > 0.1")
    return {"opposing": mean_opp, "similar": mean_sim, "gap": gap}


def main():
    parser = argparse.ArgumentParser(description="Phase 2: Projection Head + Orthogonal Loss")
    parser.add_argument("--dry-run", action="store_true", help="100件・1エポックで動作確認")
    parser.add_argument("--log-file", type=str, default=None, help="ログファイル出力先")
    args = parser.parse_args()

    # ログファイル設定
    if args.log_file:
        fh = logging.FileHandler(args.log_file, mode="w")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logging.getLogger().addHandler(fh)

    # パラメータ設定
    max_samples = 100 if args.dry_run else MAX_SAMPLES
    epochs = 1 if args.dry_run else EPOCHS

    # ── GPU セットアップ ──
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"デバイス: {device}")
    if device.type == "cuda":
        props = torch.cuda.get_device_properties(0)
        logger.info(f"  GPU: {props.name}")
        logger.info(f"  VRAM: {props.total_memory / 1e9:.1f} GB")

    # ── Encoder 読込 (凍結) ──
    logger.info(f"ベースモデル読込: {BASE_MODEL}")
    encoder = SentenceTransformer(BASE_MODEL, device=str(device))
    embed_dim = encoder.get_sentence_embedding_dimension()
    logger.info(f"  出力次元: {embed_dim}")

    if args.dry_run:
        logger.info(f"⚡ DRY RUN: {max_samples}件, {epochs}エポック")

    # ── データ読込 + 事前 embedding ──
    logger.info("AllNLI データセットを読込中...")
    ds = load_dataset("sentence-transformers/all-nli", "triplet", split="train")
    if max_samples < len(ds):
        ds = ds.select(range(max_samples))
    logger.info(f"  トリプレット数: {len(ds)}")

    # encoder で全テキストを事前 embed (encoder は凍結なので1回でよい)
    logger.info("事前 embedding 計算中...")
    all_anchors = ds["anchor"]
    all_positives = ds["positive"]
    all_negatives = ds["negative"]

    batch_encode = 256
    anchor_embs = encoder.encode(all_anchors, batch_size=batch_encode, show_progress_bar=True, convert_to_numpy=True)
    positive_embs = encoder.encode(all_positives, batch_size=batch_encode, show_progress_bar=True, convert_to_numpy=True)
    negative_embs = encoder.encode(all_negatives, batch_size=batch_encode, show_progress_bar=True, convert_to_numpy=True)

    # torch テンソルに変換
    anchor_t = torch.tensor(anchor_embs, dtype=torch.float32)
    positive_t = torch.tensor(positive_embs, dtype=torch.float32)
    negative_t = torch.tensor(negative_embs, dtype=torch.float32)

    # 元の embedding を保存 (alignment loss 用)
    original_anchor = anchor_t.clone()

    dataset = TripletDataset(anchor_t, positive_t, negative_t)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, drop_last=True)

    # ── Projection Head ──
    proj_head = ValenceProjectionHead(input_dim=embed_dim, valence_dim=VALENCE_DIM).to(device)
    logger.info(f"Projection Head: {embed_dim}d → {VALENCE_DIM}d")
    logger.info(f"  パラメータ数: {sum(p.numel() for p in proj_head.parameters()):,}")

    # ── Baseline 評価 ──
    logger.info("=== Baseline 評価 (768d 全空間) ===")
    baseline_valence_full = valence_discrimination_test(encoder, proj_head=None, device=device)
    logger.info("=== Baseline 評価 (32d 射影空間, 初期重み) ===")
    proj_head.eval()
    baseline_valence_proj = valence_discrimination_test(encoder, proj_head=proj_head, device=device)
    proj_head.train()

    # ── 訓練 ──
    optimizer = torch.optim.AdamW(proj_head.parameters(), lr=LR_HEAD, weight_decay=1e-4)
    triplet_loss_fn = nn.TripletMarginLoss(margin=TRIPLET_MARGIN, p=2)

    logger.info(f"=== 訓練開始 (epochs={epochs}, batch={BATCH_SIZE}) ===")
    logger.info(f"  L_triplet margin: {TRIPLET_MARGIN}")
    logger.info(f"  α_ortho: {ALPHA_ORTHO}")
    logger.info(f"  β_align: {BETA_ALIGN}")

    for epoch in range(epochs):
        total_loss = 0.0
        total_trip = 0.0
        total_orth = 0.0
        total_alig = 0.0
        n_batches = 0

        for batch_idx, (anc, pos, neg) in enumerate(dataloader):
            anc = anc.to(device)
            pos = pos.to(device)
            neg = neg.to(device)

            # Projection
            anc_proj = proj_head(anc)
            pos_proj = proj_head(pos)
            neg_proj = proj_head(neg)

            # L_triplet: 射影空間での TripletLoss
            l_triplet = triplet_loss_fn(anc_proj, pos_proj, neg_proj)

            # L_ortho: 直交正則化
            l_ortho = proj_head.orthogonal_loss()

            # L_align: 元 embedding との alignment 保持
            # anchor の射影を元に戻したとき、元embedding と近いか
            # (W^+ · proj(x))と x の cos similarity を最大化)
            # 簡易版: proj_head の出力と入力の cos similarity
            anc_norm = F.normalize(anc, dim=1)
            anc_proj_norm = F.normalize(anc_proj, dim=1)
            # 射影前後で情報が保存されているか (KL的に)
            # 代わりに: 共分散行列の対角性を促進
            l_align = torch.tensor(0.0, device=device)  # Phase 2a では省略

            # 総損失
            loss = l_triplet + ALPHA_ORTHO * l_ortho + BETA_ALIGN * l_align

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            total_trip += l_triplet.item()
            total_orth += l_ortho.item()
            n_batches += 1

            if (batch_idx + 1) % 50 == 0 or batch_idx == 0:
                logger.info(
                    f"  Epoch {epoch+1}/{epochs} | Batch {batch_idx+1}/{len(dataloader)} | "
                    f"Loss: {loss.item():.4f} (trip={l_triplet.item():.4f}, orth={l_ortho.item():.4f})"
                )

        avg_loss = total_loss / max(n_batches, 1)
        avg_trip = total_trip / max(n_batches, 1)
        avg_orth = total_orth / max(n_batches, 1)
        logger.info(
            f"  Epoch {epoch+1} 完了 | Avg Loss: {avg_loss:.4f} "
            f"(trip={avg_trip:.4f}, orth={avg_orth:.4f})"
        )

    # ── 最終評価 ──
    proj_head.eval()
    logger.info("=== 最終評価 (768d 全空間, encoder 不変) ===")
    final_valence_full = valence_discrimination_test(encoder, proj_head=None, device=device)
    logger.info("=== 最終評価 (32d 射影空間, 訓練済み) ===")
    final_valence_proj = valence_discrimination_test(encoder, proj_head=proj_head, device=device)

    # ── FIM 分析 (射影空間) ──
    logger.info("=== FIM 分析 (射影空間) ===")
    test_texts = [
        "kalon の定義を確認する。Fix(G∘F) の不動点条件を検証した。",
        "テスト結果は全て pass。CI/CD パイプラインが正常に動作している。",
        "このアプローチは失敗した。根本的な設計変更が必要。",
        "Handoff を作成。次回セッションへの引き継ぎ情報を記録した。",
        "FEP の自由エネルギー原理に基づき、認知制約を導出した。",
        "バグを発見。TypeError が発生しており、修正が必要。",
        "コードレビューの結果、品質は高く、Kalon に近い。",
        "パフォーマンスが低下している。最適化が必要。",
        "新しい定理を発見。24動詞の対称性が証明された。",
        "データベースが破損。バックアップから復元が必要。",
        "セッションは成功裏に終了。全目標を達成した。",
        "このプロジェクトは行き詰まっている。方向転換すべき。",
        "ドキュメントの整理が完了。MECE 構造が維持されている。",
        "エラーが連続している。根本原因の特定ができていない。",
        "sprint 計画を策定。次の2週間の目標を設定した。",
        "リソースが不足している。外部支援が必要。",
        "実験結果は予想通り。仮説が支持されている。",
        "deadlineに間に合わない可能性がある。優先度の再評価が必要。",
        "チームの士気は高い。生産性が向上している。",
        "技術的負債が蓄積している。リファクタリングが急務。",
    ]
    raw_embs = encoder.encode(test_texts, convert_to_numpy=True, show_progress_bar=False)

    # 全空間での FIM
    X_full = raw_embs - raw_embs.mean(axis=0)
    K_full = X_full @ X_full.T / len(test_texts)
    evals_full = np.sort(np.linalg.eigvalsh(K_full))[::-1]
    evals_full = evals_full[evals_full > 1e-10]
    logger.info(f"  全空間 Top-5 固有値: {[f'{v:.6f}' for v in evals_full[:5]]}")

    # 射影空間での FIM
    with torch.no_grad():
        proj_embs = proj_head(torch.tensor(raw_embs, dtype=torch.float32, device=device)).cpu().numpy()
    X_proj = proj_embs - proj_embs.mean(axis=0)
    K_proj = X_proj @ X_proj.T / len(test_texts)
    evals_proj = np.sort(np.linalg.eigvalsh(K_proj))[::-1]
    evals_proj = evals_proj[evals_proj > 1e-10]
    logger.info(f"  射影空間 Top-5 固有値: {[f'{v:.6f}' for v in evals_proj[:5]]}")

    # stiff modes (射影空間)
    gap_ratio = 1.20
    stiff_modes_proj = len(evals_proj)
    for i in range(len(evals_proj) - 1):
        r = evals_proj[i] / evals_proj[i + 1] if evals_proj[i + 1] > 0 else float("inf")
        if r >= gap_ratio and i > 0:
            stiff_modes_proj = i + 1
            break
    logger.info(f"  射影空間 stiff modes: {stiff_modes_proj}")

    # ── 保存 ──
    output_dir = OUTPUT_DIR if not args.dry_run else "/tmp/solvent_projhead_dry"
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Projection head の重みを保存
    torch.save(proj_head.state_dict(), out / "proj_head.pt")
    logger.info(f"Projection Head 保存: {out / 'proj_head.pt'}")

    # メタデータ保存
    meta = {
        "phase": 2,
        "base_model": BASE_MODEL,
        "valence_dim": VALENCE_DIM,
        "epochs": epochs,
        "batch_size": BATCH_SIZE,
        "max_samples": max_samples,
        "triplet_margin": TRIPLET_MARGIN,
        "lr_head": LR_HEAD,
        "lr_encoder": LR_ENCODER,
        "alpha_ortho": ALPHA_ORTHO,
        "beta_align": BETA_ALIGN,
        "baseline_gap_full": baseline_valence_full["gap"],
        "baseline_gap_proj": baseline_valence_proj["gap"],
        "final_gap_full": final_valence_full["gap"],
        "final_gap_proj": final_valence_proj["gap"],
        "fim_stiff_modes_proj": int(stiff_modes_proj),
        "fim_top5_full": evals_full[:5].tolist(),
        "fim_top5_proj": evals_proj[:5].tolist(),
    }
    meta_path = out / "training_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    logger.info(f"メタデータ保存: {meta_path}")

    # ── サマリー ──
    logger.info("")
    logger.info("=" * 60)
    logger.info("📊 Phase 2 PoC 結果サマリー")
    logger.info("=" * 60)
    logger.info(f"  Valence gap (768d 全空間):    {baseline_valence_full['gap']:.4f} → {final_valence_full['gap']:.4f}")
    logger.info(f"  Valence gap (32d 射影空間):   {baseline_valence_proj['gap']:.4f} → {final_valence_proj['gap']:.4f}")
    logger.info(f"  射影空間 FIM stiff modes: {stiff_modes_proj}")
    logger.info(f"  対立ペア cos (proj):    {final_valence_proj['opposing']:.4f}")
    logger.info(f"  類似ペア cos (proj):    {final_valence_proj['similar']:.4f}")


if __name__ == "__main__":
    main()
