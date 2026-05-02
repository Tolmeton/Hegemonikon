#!/usr/bin/env python3
"""Phase C v3: A/B/D 3条件アブレーション — CCL テキスト直接入力 vs Code vs 並置

Force is Oblivion / Hegemonikón Research (Lēthē)

目的: Phase C の入力形式を実験的に確定する。
  条件 A: CCL テキストのみ (raw CCL) — U⊣N の N 方向
  条件 B: Code + CCL 並置 — 両方向同時
  条件 D: Code のみ — U⊣N の U 方向

v2 からの変更:
  - --condition A/B/D フラグで入力形式切替
  - 統一 JSONL 形式 (text_a/text_b) 対応
  - 偏ρ (コード長除去) 追加
  - --all モードで 3条件一括実行
  - R@k: fold 内 retrieval (正例 recall in top-k)
  - ccl_edit_dist との相関 (ρ_ccl) で 49d を超えるか測定
  - MAX_LEN 条件別自動設定 (A/D=512, B=1024)
  - 診断ペア (構造異性体 + 49d 盲点) による事後評価

仮説:
  P11': 7B QLoRA > Phase C-mini CodeBERT (ρ=0.963)
  P14:  L_Ξ あり > L_Ξ なし
  P42:  A vs B vs D — どの入力形式が最も構造理解に優れるか

Usage:
  # 単一条件
  python phase_c_v3.py --condition A --data phase_c_condition_A_full.jsonl

  # 3条件一括
  python phase_c_v3.py --all

  # Quick test
  python phase_c_v3.py --all --quick
"""
from __future__ import annotations

import argparse
import gc
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

_SCRIPT_DIR = Path(__file__).parent


def write_json_atomic(path: Path, payload: dict) -> None:
    """JSON をテンポラリ経由で原子的に保存する。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    tmp.replace(path)


def make_condition_snapshot(
    condition: str,
    data_path: Path,
    n_pairs: int,
    started_at: float,
    results: dict,
    max_len: int,
    partial_path: Path,
    error: str | None = None,
    failed_condition: str | None = None,
    failed_fold: int | None = None,
) -> dict:
    return {
        "experiment": "phase_c_v3_ablation_partial",
        "condition": condition,
        "data_path": str(data_path.name),
        "n_pairs": n_pairs,
        "elapsed_minutes": round((time.time() - started_at) / 60, 1),
        "max_len": max_len,
        "results": results,
        "partial_path": str(partial_path.name),
        "updated_at": datetime.now().isoformat(),
        "error": error,
        "failed_condition": failed_condition,
        "failed_fold": failed_fold,
    }


# ============================================================
# L_Ξ カスタムトレーナー (v2 から継承)
# ============================================================

def make_lxi_trainer_class():
    """遅延 import で Trainer を継承したクラスを生成。"""
    from transformers import Trainer
    import torch
    import torch.nn.functional as F_t

    class LXiTrainer(Trainer):
        def __init__(self, *args, lxi_lambda: float = 0.0, **kwargs):
            super().__init__(*args, **kwargs)
            self.lxi_lambda = lxi_lambda

        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels = inputs.pop("labels") if "labels" in inputs else inputs.pop("label")
            need_attn = self.lxi_lambda > 0 and model.training
            outputs = model(**inputs, output_attentions=need_attn)
            logits = outputs.logits.squeeze(-1)

            # BCE 損失 (二値分類: 正例=1, 負例=0)
            loss_bce = F_t.binary_cross_entropy_with_logits(logits, labels.float())

            if self.lxi_lambda > 0 and outputs.attentions is not None:
                attn = outputs.attentions[-1]
                attn_flat = attn.mean(dim=-1)
                head_var = attn_flat.var(dim=1).mean()
                loss_xi = -head_var
                loss = loss_bce + self.lxi_lambda * loss_xi
            else:
                loss = loss_bce

            return (loss, outputs) if return_outputs else loss

    return LXiTrainer


# ============================================================
# 偏ρ (partial Spearman — コード長/CCL長の交絡除去)
# ============================================================

def partial_spearman(pred: np.ndarray, true: np.ndarray, confound: np.ndarray) -> float:
    """コード長 (confound) を除去した偏 Spearman ρ。

    Phase C-mini で使用された手法と同一:
    pred, true, confound を rank 変換 → confound を回帰で除去 → 残差の Spearman
    """
    from scipy.stats import spearmanr, rankdata

    r_pred = rankdata(pred)
    r_true = rankdata(true)
    r_conf = rankdata(confound)

    # confound を回帰で除去
    def residualize(y, x):
        x_mean = x.mean()
        x_centered = x - x_mean
        denom = (x_centered ** 2).sum()
        if denom < 1e-10:
            return y
        beta = (x_centered * (y - y.mean())).sum() / denom
        return y - beta * x_centered

    res_pred = residualize(r_pred, r_conf)
    res_true = residualize(r_true, r_conf)

    rho, _ = spearmanr(res_pred, res_true)
    return float(rho)


# ============================================================
# データ読込
# ============================================================

def load_condition_data(data_path: Path) -> list[dict]:
    """統一形式 JSONL を読込。"""
    records = []
    with open(data_path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records


# ============================================================
# メイン実験ループ (1条件分)
# ============================================================

def run_single_condition(
    condition: str,
    data_path: Path,
    model_name: str,
    n_folds: int,
    epochs: int,
    batch_size: int,
    grad_accum: int,
    lr: float,
    max_len: int,
    lxi_conditions: list[tuple[str, float]],
    output_dir: Path,
    b_lxi_max_len: int,
    b_lxi_train_batch_size: int,
    b_lxi_eval_batch_size: int,
) -> dict:
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

    LXiTrainer = make_lxi_trainer_class()

    # --- データ読込 ---
    records = load_condition_data(data_path)
    n_pos = sum(1 for r in records if r["label"] == 1)
    n_neg = sum(1 for r in records if r["label"] == 0)
    print(f"\n📂 条件 {condition}: {data_path.name}")
    print(f"  {len(records)} pairs (pos: {n_pos}, neg: {n_neg})")

    # --- モデルロード ---
    print(f"🔧 モデル: {model_name} (4bit QLoRA)")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=1,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        attn_implementation="eager",
    )
    model.config.pad_token_id = tokenizer.pad_token_id

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

    # --- MAX_LEN 条件別自動設定 ---
    if max_len <= 0:
        max_len = 1024 if condition == "B" else 512
    print(f"  MAX_LEN: {max_len}")

    # --- データセット ---
    def format_pair(record):
        text = f"Structure A: {record['text_a']}\n\nStructure B: {record['text_b']}"
        return {
            "text": text,
            "label": float(record["label"]),  # BCE: 二値 (0/1)
            "cosine_49d": float(record["cosine_49d"]),
            "pair_type": record.get("pair_type", "unknown"),
            "text_len": len(record["text_a"]) + len(record["text_b"]),
            "ccl_edit_dist": float(record.get("ccl_edit_dist", 0.5)),
        }

    formatted = [format_pair(r) for r in records]

    # confound (偏ρ) + ccl_edit_dist (独立教師信号)
    text_lengths = np.array([f["text_len"] for f in formatted])
    ccl_edit_dists = np.array([f["ccl_edit_dist"] for f in formatted])

    dataset = Dataset.from_list(formatted)

    # --- 実験ループ ---
    binary_labels = np.array([r["label"] for r in records])
    cosine_labels = np.array([r["cosine_49d"] for r in records])

    condition_results = {}
    t_cond_start = time.time()
    partial_path = output_dir / f"phase_c_v3_{condition}_partial.json"

    model.config.use_cache = False
    if hasattr(model, "gradient_checkpointing_enable"):
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})

    for cond_name, lxi_lambda in lxi_conditions:
        print(f"\n{'='*60}")
        print(f"  {condition} / {cond_name} (λ={lxi_lambda})")
        print(f"{'='*60}")

        effective_max_len = max_len
        train_batch_size = batch_size
        eval_batch_size = batch_size * 2

        if condition == "B" and lxi_lambda > 0:
            effective_max_len = min(max_len, b_lxi_max_len)
            train_batch_size = min(batch_size, b_lxi_train_batch_size)
            eval_batch_size = min(batch_size * 2, b_lxi_eval_batch_size)
            print(
                f"  OOM guard: MAX_LEN {max_len} -> {effective_max_len}, "
                f"train_bs {batch_size} -> {train_batch_size}, eval_bs {batch_size * 2} -> {eval_batch_size}"
            )

        def tokenize(batch):
            tokens = tokenizer(
                batch["text"],
                padding="max_length",
                truncation=True,
                max_length=effective_max_len,
                return_tensors="pt",
            )
            tokens["label"] = batch["label"]
            return tokens

        tokenized = dataset.map(tokenize, batched=True, batch_size=32, remove_columns=["text"])
        tokenized.set_format("torch", columns=["input_ids", "attention_mask", "label"])

        fold_results = []
        skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)

        for fold_idx, (train_idx, val_idx) in enumerate(skf.split(np.zeros(len(records)), binary_labels)):
            print(f"\n--- Fold {fold_idx+1}/{n_folds} ---")
            fold_start = time.time()
            trainer = None

            train_ds = tokenized.select(train_idx.tolist())
            val_ds = tokenized.select(val_idx.tolist())

            # LoRA リセット (lora_A=kaiming, lora_B=zeros で初期出力=0 を保証)
            import math
            for name, param in model.named_parameters():
                if "lora" in name and param.requires_grad:
                    if "lora_A" in name:
                        torch.nn.init.kaiming_uniform_(param, a=math.sqrt(5))
                    elif "lora_B" in name:
                        torch.nn.init.zeros_(param)
                    elif "bias" in name:
                        torch.nn.init.zeros_(param)

            training_args = TrainingArguments(
                output_dir=f"/tmp/phase_c_v3_{condition}_{cond_name}_f{fold_idx}",
                num_train_epochs=epochs,
                per_device_train_batch_size=train_batch_size,
                per_device_eval_batch_size=eval_batch_size,
                gradient_accumulation_steps=grad_accum,
                learning_rate=lr,
                weight_decay=0.01,
                warmup_ratio=0.1,
                lr_scheduler_type="cosine",
                eval_strategy="epoch",
                save_strategy="no",
                bf16=True,
                gradient_checkpointing=True,
                logging_steps=20,
                report_to="none",
                seed=42 + fold_idx,
            )

            try:
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
                pred_logits = preds_out.predictions.squeeze(-1)
                # BCE なので sigmoid でスコア化
                pred_probs = 1.0 / (1.0 + np.exp(-pred_logits))

                true_cosine = cosine_labels[val_idx]
                true_binary = binary_labels[val_idx]
                val_text_lens = text_lengths[val_idx]
                val_ccl_edit = ccl_edit_dists[val_idx]

                # Accuracy / F1 (閾値 0.5)
                from sklearn.metrics import accuracy_score, f1_score
                pred_binary = (pred_probs >= 0.5).astype(int)
                acc = accuracy_score(true_binary, pred_binary)
                f1 = f1_score(true_binary, pred_binary, zero_division=0)

                # Spearman ρ (pred_probs vs cosine_49d)
                rho, _ = spearmanr(pred_probs, true_cosine)

                # E2: logits (sigmoid 前) でも ρ を記録 — 飽和前の信号
                rho_logits, _ = spearmanr(pred_logits, true_cosine)
                rho_ccl_logits, _ = spearmanr(pred_logits, 1.0 - val_ccl_edit)

                # Spearman ρ (vs ccl_sim = 1 - ccl_edit_dist)
                rho_ccl, _ = spearmanr(pred_probs, 1.0 - val_ccl_edit)

                # 偏 ρ_49d (テキスト長除去)
                p_rho = partial_spearman(pred_probs, true_cosine, val_text_lens)

                # 偏 ρ_ccl (テキスト長除去) — 真の構造理解指標
                p_rho_ccl = partial_spearman(pred_probs, 1.0 - val_ccl_edit, val_text_lens)

                # R@k: fold 内 retrieval
                pos_mask = true_binary == 1
                neg_mask = true_binary == 0
                pos_scores = pred_probs[pos_mask]
                neg_scores = pred_probs[neg_mask]
                if len(pos_scores) > 0 and len(neg_scores) > 0:
                    neg_sorted = np.sort(neg_scores)[::-1]
                    k_vals = {1: 0, 5: 0, 10: 0}
                    for ps in pos_scores:
                        rank = int(np.searchsorted(-neg_sorted, -ps))
                        for k in k_vals:
                            if rank < k:
                                k_vals[k] += 1
                    n_pos_val = len(pos_scores)
                    r_at_1 = k_vals[1] / n_pos_val
                    r_at_5 = k_vals[5] / n_pos_val
                    r_at_10 = k_vals[10] / n_pos_val
                else:
                    r_at_1 = r_at_5 = r_at_10 = 0.0

                fold_sec = time.time() - fold_start

                fold_result = {
                    "fold": fold_idx,
                    "acc": float(acc),
                    "f1": float(f1),
                    "rho": float(rho),
                    "rho_ccl": float(rho_ccl),
                    "rho_logits": float(rho_logits),
                    "rho_ccl_logits": float(rho_ccl_logits),
                    "partial_rho": float(p_rho),
                    "partial_rho_ccl": float(p_rho_ccl),
                    "r_at_1": float(r_at_1),
                    "r_at_5": float(r_at_5),
                    "r_at_10": float(r_at_10),
                    "elapsed_sec": round(fold_sec, 1),
                    "max_len": effective_max_len,
                    "train_batch_size": train_batch_size,
                    "eval_batch_size": eval_batch_size,
                }
                fold_results.append(fold_result)

                print(
                    f"  acc={acc:.3f}  F1={f1:.3f}  ρ={rho:.4f}  ρ_logits={rho_logits:.4f}  "
                    f"偏ρ_ccl={p_rho_ccl:.4f}  R@1={r_at_1:.2f}  ({fold_sec:.0f}s)"
                )

                write_json_atomic(
                    partial_path,
                    make_condition_snapshot(
                        condition=condition,
                        data_path=data_path,
                        n_pairs=len(records),
                        started_at=t_cond_start,
                        results={**condition_results, cond_name: {"lambda": lxi_lambda, "folds": fold_results}},
                        max_len=effective_max_len,
                        partial_path=partial_path,
                    ),
                )
            except Exception as exc:
                write_json_atomic(
                    partial_path,
                    make_condition_snapshot(
                        condition=condition,
                        data_path=data_path,
                        n_pairs=len(records),
                        started_at=t_cond_start,
                        results={**condition_results, cond_name: {"lambda": lxi_lambda, "folds": fold_results}},
                        max_len=effective_max_len,
                        partial_path=partial_path,
                        error=repr(exc),
                        failed_condition=cond_name,
                        failed_fold=fold_idx,
                    ),
                )
                raise
            finally:
                if trainer is not None:
                    del trainer
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

        mean_acc = np.mean([r["acc"] for r in fold_results])
        mean_f1 = np.mean([r["f1"] for r in fold_results])
        mean_rho = np.mean([r["rho"] for r in fold_results])
        mean_rho_ccl = np.mean([r["rho_ccl"] for r in fold_results])
        mean_rho_logits = np.mean([r["rho_logits"] for r in fold_results])
        mean_rho_ccl_logits = np.mean([r["rho_ccl_logits"] for r in fold_results])
        mean_prho = np.mean([r["partial_rho"] for r in fold_results])
        mean_prho_ccl = np.mean([r["partial_rho_ccl"] for r in fold_results])
        mean_r1 = np.mean([r["r_at_1"] for r in fold_results])
        mean_r5 = np.mean([r["r_at_5"] for r in fold_results])
        mean_r10 = np.mean([r["r_at_10"] for r in fold_results])

        condition_results[cond_name] = {
            "lambda": lxi_lambda,
            "max_len": effective_max_len,
            "train_batch_size": train_batch_size,
            "eval_batch_size": eval_batch_size,
            "mean_acc": float(mean_acc),
            "mean_f1": float(mean_f1),
            "mean_rho": float(mean_rho),
            "mean_rho_ccl": float(mean_rho_ccl),
            "mean_rho_logits": float(mean_rho_logits),
            "mean_rho_ccl_logits": float(mean_rho_ccl_logits),
            "mean_partial_rho": float(mean_prho),
            "mean_partial_rho_ccl": float(mean_prho_ccl),
            "mean_r_at_1": float(mean_r1),
            "mean_r_at_5": float(mean_r5),
            "mean_r_at_10": float(mean_r10),
            "folds": fold_results,
        }

        print(f"\n  ★ {cond_name}: acc={mean_acc:.3f}  F1={mean_f1:.3f}  ρ_logits={mean_rho_logits:.4f}  偏ρ_ccl={mean_prho_ccl:.4f}  R@1={mean_r1:.2f}")
        write_json_atomic(
            partial_path,
            make_condition_snapshot(
                condition=condition,
                data_path=data_path,
                n_pairs=len(records),
                started_at=t_cond_start,
                results=condition_results,
                max_len=effective_max_len,
                partial_path=partial_path,
            ),
        )

    # モデル解放
    del model
    gc.collect()
    import torch as _torch
    if _torch.cuda.is_available():
        _torch.cuda.empty_cache()

    elapsed = time.time() - t_cond_start
    print(f"\n⏱️ 条件 {condition}: {elapsed/60:.1f} min")

    return {
        "condition": condition,
        "data_path": str(data_path.name),
        "n_pairs": len(records),
        "elapsed_minutes": round(elapsed / 60, 1),
        "results": condition_results,
    }


# ============================================================
# サマリー出力
# ============================================================

def print_summary(all_cond_results: list[dict]) -> None:
    print(f"\n{'='*100}")
    print(f"  Phase C v3 — 3条件アブレーション サマリー (BCE)")
    print(f"{'='*100}")
    print(f"{'条件':<6} {'λ':<10} {'acc':>5} {'F1':>5} {'偏ρ_ccl':>8} {'ρ_ccl':>7} {'ρ_49d':>7} {'R@1':>5} {'R@5':>5} {'N':>5}")
    print("-" * 100)

    for cond_data in all_cond_results:
        cond = cond_data["condition"]
        n = cond_data["n_pairs"]
        for cond_name, data in cond_data["results"].items():
            print(f"{cond:<6} {cond_name:<10} "
                  f"{data['mean_acc']:>5.3f} {data['mean_f1']:>5.3f} "
                  f"{data['mean_partial_rho_ccl']:>8.4f} {data['mean_rho_ccl']:>7.4f} {data['mean_rho']:>7.4f} "
                  f"{data['mean_r_at_1']:>5.2f} {data['mean_r_at_5']:>5.2f} {n:>5}")

    # 条件間比較 (baseline のみ)
    print(f"\n{'='*100}")
    print(f"  条件間比較 (baseline λ=0)")
    print(f"  偏ρ_ccl = テキスト長除去後の構造理解指標 (Phase C の真価)")
    print(f"{'='*100}")
    for cond_data in all_cond_results:
        cond = cond_data["condition"]
        bl = cond_data["results"].get("baseline", {})
        if bl:
            print(f"  {cond}: acc={bl['mean_acc']:.3f}  F1={bl['mean_f1']:.3f}  偏ρ_ccl={bl['mean_partial_rho_ccl']:.4f}  R@1={bl['mean_r_at_1']:.2f}")

    # E4: 条件間 paired t-test (fold を対応づけ)
    from scipy.stats import ttest_rel
    baselines = {}
    for cond_data in all_cond_results:
        cond = cond_data["condition"]
        bl = cond_data["results"].get("baseline", {})
        if bl and "folds" in bl:
            baselines[cond] = bl["folds"]

    cond_names = sorted(baselines.keys())
    if len(cond_names) >= 2:
        print(f"\n{'='*100}")
        print(f"  E4: 条件間 paired t-test (fold 対応, baseline λ=0)")
        print(f"{'='*100}")
        for i in range(len(cond_names)):
            for j in range(i + 1, len(cond_names)):
                c1, c2 = cond_names[i], cond_names[j]
                folds_1 = baselines[c1]
                folds_2 = baselines[c2]
                n_folds = min(len(folds_1), len(folds_2))
                for metric in ["partial_rho_ccl", "acc", "rho_ccl_logits"]:
                    vals_1 = [f[metric] for f in folds_1[:n_folds]]
                    vals_2 = [f[metric] for f in folds_2[:n_folds]]
                    if n_folds >= 3:
                        t_stat, p_val = ttest_rel(vals_1, vals_2)
                        m1, m2 = np.mean(vals_1), np.mean(vals_2)
                        sig = "✅" if p_val < 0.05 else "—"
                        print(f"  {c1} vs {c2} [{metric}]: {m1:.4f} vs {m2:.4f}  Δ={m1-m2:+.4f}  t={t_stat:.3f}  p={p_val:.4f} {sig}")
                    else:
                        print(f"  {c1} vs {c2} [{metric}]: fold 数 < 3, 検定不可")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Phase C v3: A/B/D ablation")
    parser.add_argument("--condition", choices=["A", "B", "D"], help="単一条件実行")
    parser.add_argument("--data", type=str, help="入力 JSONL パス (単一条件時)")
    parser.add_argument("--all", action="store_true", help="A/B/D 3条件一括実行")
    parser.add_argument("--model", default="codellama/CodeLlama-7b-hf")
    parser.add_argument("--output", default="phase_c_v3_results.json")
    parser.add_argument("--n-folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max-len", type=int, default=0, help="0=auto (A/D:512, B:1024)")
    parser.add_argument("--b-lxi-max-len", type=int, default=768, help="B条件で λ>0 のときに使う OOM guard 用 max_len")
    parser.add_argument("--b-lxi-train-batch-size", type=int, default=1, help="B条件で λ>0 のときに使う train batch size")
    parser.add_argument("--b-lxi-eval-batch-size", type=int, default=1, help="B条件で λ>0 のときに使う eval batch size")
    parser.add_argument("--quick", action="store_true", help="Quick: 2-fold × 2条件 × 2 epochs")
    args = parser.parse_args()

    if args.quick:
        args.n_folds = 2
        args.epochs = 2
        print("⚡ Quick モード: 2-fold × 2 λ条件 × 2 epochs")

    lxi_conditions = [
        ("baseline", 0.0),
        ("lxi_0.01", 0.01),
        ("lxi_0.1", 0.1),
        ("lxi_1.0", 1.0),
    ]
    if args.quick:
        lxi_conditions = [("baseline", 0.0), ("lxi_0.1", 0.1)]

    # 条件 → データパスの自動解決
    default_data = {
        "A": _SCRIPT_DIR / "phase_c_condition_A_full.jsonl",
        "B": _SCRIPT_DIR / "phase_c_condition_B.jsonl",
        "D": _SCRIPT_DIR / "phase_c_condition_D.jsonl",
    }

    if args.all:
        conditions = ["A", "B", "D"]
    elif args.condition:
        conditions = [args.condition]
    else:
        parser.error("--condition or --all required")
        return

    all_results = []
    t_total = time.time()
    output_path = Path(args.output)
    global_partial_path = output_path.with_name(output_path.stem + ".partial.json")

    for cond in conditions:
        data_path = Path(args.data) if args.data and len(conditions) == 1 else default_data[cond]
        if not data_path.exists():
            print(f"❌ {data_path} not found — skipping condition {cond}")
            continue

        result = run_single_condition(
            condition=cond,
            data_path=data_path,
            model_name=args.model,
            n_folds=args.n_folds,
            epochs=args.epochs,
            batch_size=args.batch_size,
            grad_accum=args.grad_accum,
            lr=args.lr,
            max_len=args.max_len,
            lxi_conditions=lxi_conditions,
            output_dir=_SCRIPT_DIR,
            b_lxi_max_len=args.b_lxi_max_len,
            b_lxi_train_batch_size=args.b_lxi_train_batch_size,
            b_lxi_eval_batch_size=args.b_lxi_eval_batch_size,
        )
        all_results.append(result)
        write_json_atomic(
            global_partial_path,
            {
                "experiment": "phase_c_v3_ablation_partial",
                "model": args.model,
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "n_folds": args.n_folds,
                    "epochs": args.epochs,
                    "batch_size": args.batch_size,
                    "grad_accum": args.grad_accum,
                    "lr": args.lr,
                    "max_len": args.max_len,
                    "b_lxi_max_len": args.b_lxi_max_len,
                    "b_lxi_train_batch_size": args.b_lxi_train_batch_size,
                    "b_lxi_eval_batch_size": args.b_lxi_eval_batch_size,
                    "quick": args.quick,
                },
                "conditions": all_results,
                "updated_at": datetime.now().isoformat(),
            },
        )

    total_min = (time.time() - t_total) / 60

    # サマリー
    print_summary(all_results)

    # JSON 保存
    import torch
    output = {
        "experiment": "phase_c_v3_ablation",
        "model": args.model,
        "timestamp": datetime.now().isoformat(),
        "total_minutes": round(total_min, 1),
        "config": {
            "n_folds": args.n_folds,
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "grad_accum": args.grad_accum,
            "lr": args.lr,
            "max_len": args.max_len,
            "lora_r": 16,
            "lora_alpha": 32,
            "quick": args.quick,
        },
        "reference": {
            "phase_c_mini_rho": 0.963,
            "phase_c_mini_partial_rho": 0.960,
            "phase_c_mini_model": "codebert-base (125M)",
            "phase_c_mini_pairs": 246,
        },
        "conditions": all_results,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
    }

    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n💾 結果: {output_path}")
    print(f"⏱️ 総実行時間: {total_min:.1f} min")


if __name__ == "__main__":
    main()
