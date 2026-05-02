#!/usr/bin/env python3
"""Phase C v2: CCL Structural Pattern Recognition — CodeLlama 7B QLoRA

Force is Oblivion / Hegemonikón Research (Lēthē)

目的: CCL の構造的パターンを対照学習で獲得し、
Phase C-mini (CodeBERT 125M, ρ=0.963) をスケールアップ検証する。

仮説:
  P11': CodeLlama QLoRA > Phase C-mini CodeBERT (ρ=0.963)
  P14:  L_Ξ あり > L_Ξ なし
  P41:  7B モデルは hard negative を分離できる

Usage:
  # フル実行 (5-fold × 4条件 = 20 runs)
  python phase_c_v2.py --data phase_c_training_ccl.jsonl

  # Quick test (2-fold × 2条件, 2 epochs)
  python phase_c_v2.py --data phase_c_training_ccl.jsonl --quick

  # 13B モデル (A100 推奨)
  python phase_c_v2.py --data phase_c_training_ccl.jsonl --model codellama/CodeLlama-13b-hf
"""
from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

# ============================================================
# L_Ξ カスタムトレーナー
# ============================================================

def make_lxi_trainer_class():
    """遅延 import で Trainer を継承したクラスを生成。"""
    from transformers import Trainer
    import torch
    import torch.nn.functional as F_t

    class LXiTrainer(Trainer):
        """L_Ξ 正則化付きトレーナー。

        λ > 0: アテンション重みのヘッド間分散を最大化 = 不均一忘却促進
        λ = 0: ベースライン (正則化なし)
        """

        def __init__(self, *args, lxi_lambda: float = 0.0, **kwargs):
            super().__init__(*args, **kwargs)
            self.lxi_lambda = lxi_lambda

        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels = inputs.pop("labels") if "labels" in inputs else inputs.pop("label")
            # 訓練時のみ attentions を取得 (predict 時は OOM 回避)
            need_attn = self.lxi_lambda > 0 and model.training
            outputs = model(**inputs, output_attentions=need_attn)
            logits = outputs.logits.squeeze(-1)

            # MSE 損失 (回帰: cosine_49d 予測)
            loss_mse = F_t.mse_loss(logits, labels.float())

            if self.lxi_lambda > 0 and outputs.attentions is not None:
                attn = outputs.attentions[-1]  # (B, H, S, S)
                attn_flat = attn.mean(dim=-1)  # (B, H, S)
                head_var = attn_flat.var(dim=1).mean()
                loss_xi = -head_var  # 分散最大化
                loss = loss_mse + self.lxi_lambda * loss_xi
            else:
                loss = loss_mse

            return (loss, outputs) if return_outputs else loss

    return LXiTrainer


# ============================================================
# メイン実験ループ
# ============================================================

def run_experiment(args):
    import torch
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType
    from datasets import Dataset
    from sklearn.model_selection import StratifiedKFold
    from scipy.stats import spearmanr
    from sklearn.metrics import accuracy_score, f1_score

    LXiTrainer = make_lxi_trainer_class()

    # --- データ読込 ---
    print(f"\n📂 データ読込: {args.data}")
    records = []
    with open(args.data) as f:
        for line in f:
            records.append(json.loads(line))

    n_pos = sum(1 for r in records if r["label"] == 1)
    n_neg = sum(1 for r in records if r["label"] == 0)
    types = {}
    for r in records:
        t = r.get("pair_type", "unknown")
        types[t] = types.get(t, 0) + 1

    print(f"  合計: {len(records)} ペア (positive: {n_pos}, negative: {n_neg})")
    print(f"  種別: {types}")

    cos_pos = [r["cosine_49d"] for r in records if r["label"] == 1]
    cos_neg = [r["cosine_49d"] for r in records if r["label"] == 0]
    print(f"  cosine_49d — pos: mean={np.mean(cos_pos):.3f} | neg: mean={np.mean(cos_neg):.3f}")

    # --- モデルロード ---
    print(f"\n🔧 モデルロード: {args.model} (4bit QLoRA)")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForSequenceClassification.from_pretrained(
        args.model,
        num_labels=1,  # 回帰
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        attn_implementation="eager",  # L_Ξ で output_attentions=True が必要
    )
    model.config.pad_token_id = tokenizer.pad_token_id

    print(f"  パラメータ数: {model.num_parameters():,}")
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  GPU メモリ: {torch.cuda.memory_allocated() / 1e9:.2f} GB")

    # QLoRA
    model = prepare_model_for_kbit_training(model)
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.SEQ_CLS,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # --- データセット準備 ---
    MAX_LEN = 512

    def format_pair(record):
        text = f"Structure A: {record['anchor_ccl']}\n\nStructure B: {record['candidate_ccl']}"
        return {
            "text": text,
            "label": float(record["cosine_49d"]),
            "label_binary": record["label"],
            "pair_type": record.get("pair_type", "unknown"),
        }

    formatted = [format_pair(r) for r in records]
    dataset = Dataset.from_list(formatted)

    def tokenize(batch):
        tokens = tokenizer(
            batch["text"],
            padding="max_length",
            truncation=True,
            max_length=MAX_LEN,
            return_tensors="pt",
        )
        tokens["label"] = batch["label"]
        return tokens

    tokenized = dataset.map(tokenize, batched=True, batch_size=32, remove_columns=["text"])
    tokenized.set_format("torch", columns=["input_ids", "attention_mask", "label"])
    print(f"\n📊 データセット: {len(tokenized)} 件 (MAX_LEN={MAX_LEN})")

    # --- 実験パラメータ ---
    n_folds = args.n_folds
    epochs = args.epochs
    batch_size = args.batch_size
    grad_accum = args.grad_accum
    lr = args.lr

    lxi_conditions = [
        ("baseline", 0.0),
        ("lxi_0.01", 0.01),
        ("lxi_0.1", 0.1),
        ("lxi_1.0", 1.0),
    ]
    if args.quick:
        lxi_conditions = [("baseline", 0.0), ("lxi_0.1", 0.1)]

    binary_labels = np.array([r["label"] for r in records])
    cosine_labels = np.array([r["cosine_49d"] for r in records])
    pair_types = np.array([r.get("pair_type", "unknown") for r in records])

    all_results = {}
    t_start = time.time()

    for cond_name, lxi_lambda in lxi_conditions:
        print(f"\n{'='*60}")
        print(f"  条件: {cond_name} (λ={lxi_lambda})")
        print(f"{'='*60}")

        fold_results = []
        skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)

        for fold_idx, (train_idx, val_idx) in enumerate(skf.split(np.zeros(len(records)), binary_labels)):
            print(f"\n--- Fold {fold_idx+1}/{n_folds} ---")
            fold_start = time.time()

            train_ds = tokenized.select(train_idx.tolist())
            val_ds = tokenized.select(val_idx.tolist())

            # LoRA 重みリセット
            for name, param in model.named_parameters():
                if "lora" in name and param.requires_grad:
                    if "weight" in name:
                        torch.nn.init.kaiming_uniform_(param)
                    elif "bias" in name:
                        torch.nn.init.zeros_(param)

            output_dir = f"/tmp/phase_c_{cond_name}_fold{fold_idx}"
            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=epochs,
                per_device_train_batch_size=batch_size,
                per_device_eval_batch_size=batch_size * 2,
                gradient_accumulation_steps=grad_accum,
                learning_rate=lr,
                weight_decay=0.01,
                warmup_ratio=0.1,
                lr_scheduler_type="cosine",
                eval_strategy="epoch",
                save_strategy="no",
                bf16=True,
                logging_steps=20,
                report_to="none",
                seed=42 + fold_idx,
            )

            trainer = LXiTrainer(
                model=model,
                args=training_args,
                train_dataset=train_ds,
                eval_dataset=val_ds,
                lxi_lambda=lxi_lambda,
            )

            trainer.train()

            # --- 評価 ---
            preds_out = trainer.predict(val_ds)
            pred_scores = preds_out.predictions.squeeze(-1)
            true_cosine = cosine_labels[val_idx]
            true_binary = binary_labels[val_idx]
            val_types = pair_types[val_idx]

            rho, p_val = spearmanr(pred_scores, true_cosine)

            threshold = np.median(pred_scores)
            pred_binary = (pred_scores >= threshold).astype(int)
            acc = accuracy_score(true_binary, pred_binary)
            f1 = f1_score(true_binary, pred_binary, zero_division=0)

            type_acc = {}
            for ptype in ["positive", "easy_neg", "hard_neg_cosine", "hard_neg_dir"]:
                mask = val_types == ptype
                if mask.sum() > 0:
                    expected = np.ones(mask.sum()) if ptype == "positive" else np.zeros(mask.sum())
                    type_acc[ptype] = float(accuracy_score(expected.astype(int), pred_binary[mask]))

            mse = float(np.mean((pred_scores - true_cosine) ** 2))
            fold_sec = time.time() - fold_start

            fold_result = {
                "fold": fold_idx,
                "rho": float(rho),
                "p_val": float(p_val),
                "accuracy": float(acc),
                "f1": float(f1),
                "mse": float(mse),
                "type_accuracy": type_acc,
                "elapsed_sec": round(fold_sec, 1),
            }
            fold_results.append(fold_result)

            print(f"  ρ={rho:.4f}  acc={acc:.4f}  F1={f1:.4f}  MSE={mse:.4f}  ({fold_sec:.0f}s)")
            for ptype, pacc in type_acc.items():
                print(f"    {ptype}: acc={pacc:.3f}")

            del trainer
            gc.collect()
            torch.cuda.empty_cache()

        mean_rho = np.mean([r["rho"] for r in fold_results])
        mean_acc = np.mean([r["accuracy"] for r in fold_results])
        mean_f1 = np.mean([r["f1"] for r in fold_results])
        mean_mse = np.mean([r["mse"] for r in fold_results])

        all_results[cond_name] = {
            "lambda": lxi_lambda,
            "mean_rho": float(mean_rho),
            "mean_accuracy": float(mean_acc),
            "mean_f1": float(mean_f1),
            "mean_mse": float(mean_mse),
            "folds": fold_results,
        }

        print(f"\n  ★ {cond_name} 平均: ρ={mean_rho:.4f}  acc={mean_acc:.4f}  F1={mean_f1:.4f}  MSE={mean_mse:.4f}")

    total_sec = time.time() - t_start

    # --- サマリー ---
    print(f"\n{'='*70}")
    print(f"  Phase C v2 — 全条件サマリー  ({total_sec/60:.1f} min)")
    print(f"{'='*70}")
    print(f"{'条件':<15} {'λ':>5} {'ρ':>8} {'acc':>8} {'F1':>8} {'MSE':>8}")
    print("-" * 70)
    print(f"{'C-mini ref':<15} {'—':>5} {'0.963':>8} {'—':>8} {'—':>8} {'0.010':>8}")

    for cond_name, data in all_results.items():
        print(f"{cond_name:<15} {data['lambda']:>5.2f} {data['mean_rho']:>8.4f} {data['mean_accuracy']:>8.4f} {data['mean_f1']:>8.4f} {data['mean_mse']:>8.4f}")

    # --- 仮説判定 ---
    print(f"\n{'='*70}")
    print("  仮説判定")
    print(f"{'='*70}")

    baseline_rho = all_results["baseline"]["mean_rho"]

    delta_p11 = baseline_rho - 0.963
    p11_v = "✅ 支持" if delta_p11 > 0 else "⚠️ 未達" if delta_p11 > -0.05 else "❌ 棄却"
    print(f"P11': CodeLlama 7B QLoRA vs C-mini (ρ=0.963)")
    print(f"  baseline ρ = {baseline_rho:.4f}, Δ = {delta_p11:+.4f} → {p11_v}")

    lxi_conds = [(k, v) for k, v in all_results.items() if k != "baseline"]
    if lxi_conds:
        best_lxi = max(lxi_conds, key=lambda x: x[1]["mean_rho"])
        delta_p14 = best_lxi[1]["mean_rho"] - baseline_rho
        p14_v = "✅ 支持" if delta_p14 > 0.005 else "⚠️ 弱支持" if delta_p14 > 0 else "❌ 棄却"
        print(f"\nP14: L_Ξ ablation")
        print(f"  best = {best_lxi[0]} (ρ={best_lxi[1]['mean_rho']:.4f}), Δ = {delta_p14:+.4f} → {p14_v}")

    # --- JSON 保存 ---
    output = {
        "experiment": "phase_c_v2_qlora",
        "model": args.model,
        "timestamp": datetime.now().isoformat(),
        "elapsed_minutes": round(total_sec / 60, 1),
        "config": {
            "n_folds": n_folds,
            "epochs": epochs,
            "batch_size": batch_size,
            "grad_accum": grad_accum,
            "lr": lr,
            "max_len": MAX_LEN,
            "lora_r": 16,
            "lora_alpha": 32,
            "n_pairs": len(records),
            "quick": args.quick,
        },
        "reference": {
            "phase_c_mini_rho": 0.963,
            "phase_c_mini_model": "codebert-base (125M)",
            "phase_c_mini_pairs": 246,
        },
        "results": all_results,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
    }

    output_path = Path(args.output)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n💾 結果保存: {output_path}")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Phase C v2: CodeLlama QLoRA for CCL patterns")
    parser.add_argument("--data", required=True, help="phase_c_training_ccl.jsonl のパス")
    parser.add_argument("--model", default="codellama/CodeLlama-7b-hf", help="モデル名")
    parser.add_argument("--output", default="phase_c_v2_results.json", help="結果 JSON のパス")
    parser.add_argument("--n-folds", type=int, default=5, help="CV fold 数")
    parser.add_argument("--epochs", type=int, default=5, help="エポック数")
    parser.add_argument("--batch-size", type=int, default=4, help="バッチサイズ")
    parser.add_argument("--grad-accum", type=int, default=4, help="勾配蓄積ステップ")
    parser.add_argument("--lr", type=float, default=2e-4, help="学習率")
    parser.add_argument("--quick", action="store_true", help="Quick test (2-fold × 2条件, 2 epochs)")
    args = parser.parse_args()

    if args.quick:
        args.n_folds = 2
        args.epochs = 2
        print("⚡ Quick モード: 2-fold × 2条件 × 2 epochs")

    run_experiment(args)


if __name__ == "__main__":
    main()
