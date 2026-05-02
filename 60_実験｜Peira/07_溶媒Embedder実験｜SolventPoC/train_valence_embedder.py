"""Valence-aware Embedding Fine-tuning — Phase 1 PoC.

PURPOSE: NLI データの entailment/contradiction ペアを使い、
all-mpnet-base-v2 に Valence 弁別力を付与する。

理論的根拠 (THEORY.md §4-6):
  ker(G) = {Scale, Valence}
  FIM stiff modes = 2 (3座標 → 2方向に圧縮)
  → Valence 方向を cos similarity 空間に追加すれば stiff modes ≥ 3

損失関数: TripletLoss (sentence-transformers v5 API)
  distance_metric = COSINE
  triplet_margin = 0.3
  データ: AllNLI triplet (anchor, positive=entailment, negative=contradiction)

PROOF: implementation_plan.md §Step 3
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import torch
from datasets import load_dataset
from sentence_transformers import (
    SentenceTransformer,
    SentenceTransformerTrainer,
    SentenceTransformerTrainingArguments,
    losses,
)
from sentence_transformers.evaluation import (
    EmbeddingSimilarityEvaluator,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── 定数 ──────────────────────────────────────────────────────────────

BASE_MODEL = "sentence-transformers/all-mpnet-base-v2"
OUTPUT_DIR = "./output/valence-mpnet"
TRIPLET_MARGIN = 0.3
BATCH_SIZE = 16
EPOCHS = 3
LR = 2e-5
WARMUP_RATIO = 0.1


# ── Valence 弁別テスト ────────────────────────────────────────────────

def valence_discrimination_test(model: SentenceTransformer) -> dict:
    """Valence 弁別力のテスト。

    対立する文ペアと類似する文ペアの cos similarity を比較。
    fine-tuned モデルでは、対立ペアの cos が有意に低くなるべき。
    """
    # 対立ペア (cos が低くあるべき)
    valence_pairs = [
        ("この設計は美しく、効率的だ", "この設計は醜く、非効率的だ"),
        ("実験は成功し、仮説が支持された", "実験は失敗し、仮説が棄却された"),
        ("このアプローチは問題を解決する", "このアプローチは新たな問題を生む"),
        ("コードの品質は高い", "コードの品質は低い"),
        ("This approach is elegant and effective", "This approach is clumsy and useless"),
    ]
    # 類似ペア (cos が高くあるべき)
    similar_pairs = [
        ("この設計は美しく、効率的だ", "この設計は優雅で、パフォーマンスが良い"),
        ("実験は成功した", "テストは pass した"),
        ("コードの品質は高い", "コードはよく書かれている"),
        ("This is a good solution", "This is an excellent approach"),
    ]

    logger.info("=== Valence 弁別テスト ===")

    # 対立ペア
    valence_sims = []
    for a, b in valence_pairs:
        emb = model.encode([a, b], convert_to_tensor=True)
        sim = torch.nn.functional.cosine_similarity(
            emb[0].unsqueeze(0), emb[1].unsqueeze(0)
        ).item()
        valence_sims.append(sim)
        logger.info(f"  対立: {sim:.4f} | {a[:25]}... vs {b[:25]}...")

    # 類似ペア
    similar_sims = []
    for a, b in similar_pairs:
        emb = model.encode([a, b], convert_to_tensor=True)
        sim = torch.nn.functional.cosine_similarity(
            emb[0].unsqueeze(0), emb[1].unsqueeze(0)
        ).item()
        similar_sims.append(sim)
        logger.info(f"  類似: {sim:.4f} | {a[:25]}... vs {b[:25]}...")

    mean_valence = sum(valence_sims) / len(valence_sims)
    mean_similar = sum(similar_sims) / len(similar_sims)
    gap = mean_similar - mean_valence

    logger.info(f"  対立ペア平均 cos: {mean_valence:.4f}")
    logger.info(f"  類似ペア平均 cos: {mean_similar:.4f}")
    logger.info(f"  弁別ギャップ:     {gap:.4f}")
    logger.info(f"  目標: ギャップ > 0.1")

    return {
        "valence_pairs": valence_sims,
        "similar_pairs": similar_sims,
        "mean_valence": mean_valence,
        "mean_similar": mean_similar,
        "gap": gap,
    }


# ── メイン ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Valence-aware Embedding Fine-tuning")
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--max-samples", type=int, default=50000)
    parser.add_argument("--dry-run", action="store_true",
                        help="100件・1エポックで動作確認")
    parser.add_argument("--eval-only", action="store_true",
                        help="既存モデルの Valence 弁別テストのみ")
    parser.add_argument("--model-path", type=str, default=None,
                        help="eval-only 時のモデルパス")
    parser.add_argument("--log-file", type=str, default=None,
                        help="ログ出力ファイル (stdout と同時に出力)")
    args = parser.parse_args()

    # ログをファイルにも出力
    if args.log_file:
        fh = logging.FileHandler(args.log_file, mode="w")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logging.getLogger().addHandler(fh)

    if args.eval_only:
        model_path = args.model_path or OUTPUT_DIR
        logger.info(f"評価モード: {model_path}")
        model = SentenceTransformer(model_path)
        results = valence_discrimination_test(model)
        print(json.dumps(results, indent=2))
        return

    # ── GPU 確認 ──
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"デバイス: {device}")
    if device == "cuda":
        logger.info(f"  GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    # ── モデル読込 ──
    logger.info(f"ベースモデル読込: {BASE_MODEL}")
    model = SentenceTransformer(BASE_MODEL, device=device)
    dim = model.get_sentence_embedding_dimension()
    logger.info(f"  出力次元: {dim}")

    # ── データ準備 ──
    if args.dry_run:
        max_samples = 100
        epochs = 1
        batch_size = 8
        logger.info("⚡ DRY RUN: 100件, 1エポック")
    else:
        max_samples = args.max_samples
        epochs = args.epochs
        batch_size = args.batch_size

    logger.info("AllNLI データセットを読込中...")
    # sentence-transformers v5: HF Dataset を直接 Trainer に渡す
    train_ds = load_dataset(
        "sentence-transformers/all-nli",
        "triplet",
        split=f"train[:{max_samples}]",
    )
    logger.info(f"  トリプレット数: {len(train_ds)}")
    logger.info(f"  列名: {train_ds.column_names}")

    # STS-B 評価セット
    logger.info("STS-B 評価セットを読込中...")
    sts_ds = load_dataset("sentence-transformers/stsb", split="test")
    sts_evaluator = EmbeddingSimilarityEvaluator(
        sentences1=sts_ds["sentence1"],
        sentences2=sts_ds["sentence2"],
        scores=[s / 5.0 for s in sts_ds["score"]],  # 0-5 → 0-1 正規化
        name="stsb-test",
    )

    # ── Baseline 評価 ──
    logger.info("=== Baseline 評価 ===")
    baseline_results = sts_evaluator(model)
    baseline_score = baseline_results["stsb-test_spearman_cosine"]
    logger.info(f"  STS-B baseline (Spearman): {baseline_score:.4f}")

    baseline_valence = valence_discrimination_test(model)

    # ── 損失関数 ──
    # TripletLoss: explicit negative (contradiction) を使う
    triplet_loss = losses.TripletLoss(
        model=model,
        distance_metric=losses.TripletDistanceMetric.COSINE,
        triplet_margin=TRIPLET_MARGIN,
    )

    # ── 訓練設定 ──
    output_dir = OUTPUT_DIR if not args.dry_run else "/tmp/solvent_dry_run"
    training_args = SentenceTransformerTrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        warmup_ratio=WARMUP_RATIO,
        learning_rate=LR,
        fp16=torch.cuda.is_available(),
        logging_steps=50 if not args.dry_run else 5,
        save_strategy="epoch",
        eval_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="stsb-test_spearman_cosine",
        save_total_limit=2,
    )

    # ── 訓練実行 ──
    logger.info(f"=== 訓練開始 (epochs={epochs}, batch={batch_size}) ===")
    trainer = SentenceTransformerTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        loss=triplet_loss,
        evaluator=sts_evaluator,
    )

    trainer.train()

    # ── 最終評価 ──
    logger.info("=== 最終評価 ===")
    final_results = sts_evaluator(model)
    final_score = final_results["stsb-test_spearman_cosine"]
    logger.info(f"  STS-B baseline (Spearman): {baseline_score:.4f}")
    logger.info(f"  STS-B final    (Spearman): {final_score:.4f}")
    retention = final_score / baseline_score if baseline_score > 0 else 0
    logger.info(f"  STS retention: {retention * 100:.1f}%")

    finetuned_valence = valence_discrimination_test(model)

    # ── 保存 ──
    if not args.dry_run:
        model.save(output_dir)
        logger.info(f"モデル保存先: {output_dir}")

    # メタデータ保存
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    meta = {
        "base_model": BASE_MODEL,
        "epochs": epochs,
        "batch_size": batch_size,
        "max_samples": max_samples,
        "triplet_margin": TRIPLET_MARGIN,
        "lr": LR,
        "warmup_ratio": WARMUP_RATIO,
        "sts_baseline": baseline_score,
        "sts_final": final_score,
        "sts_retention_pct": retention * 100,
        "baseline_valence_gap": baseline_valence["gap"],
        "finetuned_valence_gap": finetuned_valence["gap"],
        "gap_improvement": finetuned_valence["gap"] - baseline_valence["gap"],
    }
    meta_path = out / "training_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    logger.info(f"メタデータ保存: {meta_path}")

    # ── サマリー ──
    logger.info("")
    logger.info("=" * 60)
    logger.info("📊 Phase 1 PoC 結果サマリー")
    logger.info("=" * 60)
    logger.info(f"  STS-B retention: {retention * 100:.1f}% (目標: >95%)")
    logger.info(f"  Valence gap baseline:  {baseline_valence['gap']:.4f}")
    logger.info(f"  Valence gap finetuned: {finetuned_valence['gap']:.4f}")
    logger.info(f"  Gap 改善: {finetuned_valence['gap'] - baseline_valence['gap']:+.4f}")


if __name__ == "__main__":
    main()
