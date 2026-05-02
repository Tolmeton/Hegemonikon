#!/usr/bin/env python3
"""Phase C v3 TPU 版 — A/B/D 3条件アブレーションを PyTorch/XLA で実行。

この版は CUDA / bitsandbytes / Trainer 前提を捨て、単一 TPU チップ (v5e/v6e) での
LoRA + bfloat16 学習を狙う。現行 GPU 版と評価指標は揃えるが、実装は XLA 向けに
手書きループへ置き換えている。

注意:
  - Hugging Face 側は TPU 対応ビルドが前提。v6e では pytorch-tpu/transformers fork
    または TPU 対応 runtime を使うこと。
  - QLoRA / bitsandbytes は使わない。LoRA + bf16 のみ。
  - B 条件の λ>0 は attention 正則化のメモリが重いので max_len / batch を縮退。
"""
from __future__ import annotations

import argparse
import gc
import json
import math
import time
from datetime import datetime
from pathlib import Path
from typing import Any
import platform

import numpy as np

_SCRIPT_DIR = Path(__file__).parent

try:
    import torch
    import torch.nn.functional as F_t
    from torch.utils.data import DataLoader, Dataset
except ImportError as exc:  # pragma: no cover - import failure is runtime env issue
    raise SystemExit(f"PyTorch is required: {exc}") from exc

try:  # TPU は実行環境依存なので import 失敗を許容
    import torch_xla.core.xla_model as xm
    HAS_XLA = True
except ImportError:
    HAS_XLA = False


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    tmp.replace(path)


def make_condition_snapshot(
    condition: str,
    data_path: Path,
    n_pairs: int,
    started_at: float,
    results: dict[str, Any],
    max_len: int,
    partial_path: Path,
    device_name: str,
    error: str | None = None,
    failed_condition: str | None = None,
    failed_fold: int | None = None,
) -> dict[str, Any]:
    return {
        "experiment": "phase_c_v3_tpu_partial",
        "condition": condition,
        "data_path": str(data_path.name),
        "n_pairs": n_pairs,
        "elapsed_minutes": round((time.time() - started_at) / 60, 1),
        "max_len": max_len,
        "results": results,
        "partial_path": str(partial_path.name),
        "device": device_name,
        "updated_at": datetime.now().isoformat(),
        "error": error,
        "failed_condition": failed_condition,
        "failed_fold": failed_fold,
    }


def get_device() -> tuple[torch.device, str]:
    if HAS_XLA:
        dev = xm.xla_device()
        return dev, f"tpu:{dev}"
    if torch.cuda.is_available():
        return torch.device("cuda"), "cuda"
    return torch.device("cpu"), "cpu"


def mark_step() -> None:
    if HAS_XLA:
        xm.mark_step()


def optimizer_step(optimizer: torch.optim.Optimizer) -> None:
    if HAS_XLA:
        xm.optimizer_step(optimizer, barrier=True)
    else:
        optimizer.step()


def set_seed(seed: int) -> None:
    torch.manual_seed(seed)
    if HAS_XLA:
        xm.set_rng_state(seed)
    elif torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def make_warmup_cosine_scheduler(
    optimizer: torch.optim.Optimizer,
    total_steps: int,
    warmup_ratio: float,
) -> torch.optim.lr_scheduler.LambdaLR:
    total_steps = max(1, total_steps)
    warmup_steps = min(total_steps - 1, int(total_steps * warmup_ratio)) if total_steps > 1 else 0

    def lr_lambda(current_step: int) -> float:
        if warmup_steps > 0 and current_step < warmup_steps:
            return float(current_step + 1) / float(max(1, warmup_steps))

        if total_steps <= warmup_steps:
            return 1.0

        progress = (current_step - warmup_steps) / float(max(1, total_steps - warmup_steps))
        progress = min(max(progress, 0.0), 1.0)
        return 0.5 * (1.0 + math.cos(math.pi * progress))

    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)


def get_runtime_metadata() -> dict[str, Any]:
    meta: dict[str, Any] = {
        "python": platform.python_version(),
        "torch": getattr(torch, "__version__", "unknown"),
        "has_xla": HAS_XLA,
    }
    if HAS_XLA:
        import torch_xla  # type: ignore

        meta["torch_xla"] = getattr(torch_xla, "__version__", "unknown")
        meta["pjrt_device"] = "TPU"
    return meta


def partial_spearman(pred: np.ndarray, true: np.ndarray, confound: np.ndarray) -> float:
    from scipy.stats import rankdata, spearmanr

    r_pred = rankdata(pred)
    r_true = rankdata(true)
    r_conf = rankdata(confound)

    def residualize(y: np.ndarray, x: np.ndarray) -> np.ndarray:
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


def load_condition_data(data_path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with open(data_path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records


class TensorDictDataset(Dataset):
    def __init__(self, encoded: dict[str, torch.Tensor], labels: torch.Tensor):
        self.encoded = encoded
        self.labels = labels

    def __len__(self) -> int:
        return int(self.labels.shape[0])

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        item = {k: v[idx] for k, v in self.encoded.items()}
        item["labels"] = self.labels[idx]
        return item


def build_tokenized_dataset(
    tokenizer: Any,
    texts: list[str],
    labels: np.ndarray,
    max_len: int,
) -> TensorDictDataset:
    encoded = tokenizer(
        texts,
        padding="max_length",
        truncation=True,
        max_length=max_len,
        return_tensors="pt",
    )
    keep = {
        "input_ids": encoded["input_ids"].long(),
        "attention_mask": encoded["attention_mask"].long(),
    }
    label_t = torch.tensor(labels, dtype=torch.float32)
    return TensorDictDataset(keep, label_t)


def clone_trainable_state(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    snapshot: dict[str, torch.Tensor] = {}
    for name, param in model.named_parameters():
        if param.requires_grad:
            snapshot[name] = param.detach().cpu().clone()
    return snapshot


def restore_trainable_state(model: torch.nn.Module, snapshot: dict[str, torch.Tensor], device: torch.device) -> None:
    named_params = dict(model.named_parameters())
    for name, saved in snapshot.items():
        param = named_params[name]
        param.data.copy_(saved.to(device=device, dtype=param.dtype))


def tensor_to_float(value: torch.Tensor) -> float:
    return float(value.detach().float().cpu().item())


def clip_optimizer_gradients(
    optimizer: torch.optim.Optimizer,
    max_grad_norm: float,
) -> None:
    if max_grad_norm <= 0:
        return

    params: list[torch.Tensor] = []
    for group in optimizer.param_groups:
        params.extend(param for param in group["params"] if param.grad is not None)

    if params:
        torch.nn.utils.clip_grad_norm_(params, max_grad_norm)


def train_one_epoch(
    model: torch.nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.LRScheduler,
    device: torch.device,
    lxi_lambda: float,
    grad_accum: int,
    max_grad_norm: float,
) -> float:
    model.train()
    optimizer.zero_grad(set_to_none=True)
    running_loss = 0.0
    steps = 0

    for step_idx, batch in enumerate(loader, start=1):
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)
        need_attn = lxi_lambda > 0

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_attentions=need_attn,
        )
        logits = outputs.logits.squeeze(-1).float()
        loss = F_t.binary_cross_entropy_with_logits(logits, labels.float())

        if need_attn and outputs.attentions is not None:
            attn = outputs.attentions[-1].float()
            attn_flat = attn.mean(dim=-1)
            head_var = attn_flat.var(dim=1).mean()
            loss = loss + lxi_lambda * (-head_var)

        loss_to_backprop = loss / grad_accum
        loss_to_backprop.backward()

        if step_idx % grad_accum == 0 or step_idx == len(loader):
            # Keep the TPU loop aligned with Trainer's default stability guard.
            clip_optimizer_gradients(optimizer, max_grad_norm)
            optimizer_step(optimizer)
            scheduler.step()
            optimizer.zero_grad(set_to_none=True)
            mark_step()

        running_loss += tensor_to_float(loss)
        steps += 1

    return running_loss / max(steps, 1)


def predict_scores(
    model: torch.nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> np.ndarray:
    model.eval()
    preds: list[np.ndarray] = []
    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_attentions=False,
            )
            logits = outputs.logits.squeeze(-1).detach().float().cpu().numpy()
            preds.append(np.atleast_1d(logits))
            mark_step()
    if not preds:
        return np.empty((0,), dtype=np.float32)
    return np.concatenate(preds, axis=0)


def run_single_condition(
    condition: str,
    data_path: Path,
    model_name: str,
    n_folds: int,
    epochs: int,
    batch_size: int,
    eval_batch_size: int,
    grad_accum: int,
    lr: float,
    max_len: int,
    lxi_conditions: list[tuple[str, float]],
    output_dir: Path,
    b_lxi_max_len: int,
    b_lxi_train_batch_size: int,
    b_lxi_eval_batch_size: int,
    lora_r: int,
    lora_alpha: int,
    lora_dropout: float,
    warmup_ratio: float,
    max_grad_norm: float,
    trust_remote_code: bool,
) -> dict[str, Any]:
    from peft import LoraConfig, TaskType, get_peft_model
    from scipy.stats import spearmanr
    from sklearn.metrics import accuracy_score, f1_score
    from sklearn.model_selection import StratifiedKFold
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    device, device_name = get_device()

    records = load_condition_data(data_path)
    n_pos = sum(1 for r in records if r["label"] == 1)
    n_neg = sum(1 for r in records if r["label"] == 0)
    print(f"\n📂 条件 {condition}: {data_path.name}")
    print(f"  {len(records)} pairs (pos: {n_pos}, neg: {n_neg})")
    print(f"🔧 モデル: {model_name} (TPU LoRA bf16)")
    print(f"  device: {device_name}")

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=trust_remote_code)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=1,
        torch_dtype=torch.bfloat16,
        trust_remote_code=trust_remote_code,
    )
    model.config.pad_token_id = tokenizer.pad_token_id
    model.config.use_cache = False
    if not hasattr(model.config, "flash_attention"):
        model.config.flash_attention = False

    lora_config = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        bias="none",
        task_type=TaskType.SEQ_CLS,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )
    model = get_peft_model(model, lora_config)
    if hasattr(model, "gradient_checkpointing_enable") and not HAS_XLA:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    elif HAS_XLA:
        print("  XLA note: gradient checkpointing disabled due to torch.utils.checkpoint incompatibility")
    model = model.to(device)
    mark_step()

    initial_trainable_state = clone_trainable_state(model)
    if hasattr(model, "print_trainable_parameters"):
        model.print_trainable_parameters()

    if max_len <= 0:
        max_len = 1024 if condition == "B" else 512
    print(f"  MAX_LEN: {max_len}")

    formatted = []
    for record in records:
        formatted.append(
            {
                "text": f"Structure A: {record['text_a']}\n\nStructure B: {record['text_b']}",
                "label": float(record["label"]),
                "cosine_49d": float(record["cosine_49d"]),
                "pair_type": record.get("pair_type", "unknown"),
                "text_len": len(record["text_a"]) + len(record["text_b"]),
                "ccl_edit_dist": float(record.get("ccl_edit_dist", 0.5)),
            }
        )

    texts = [f["text"] for f in formatted]
    labels = np.array([f["label"] for f in formatted], dtype=np.float32)
    text_lengths = np.array([f["text_len"] for f in formatted], dtype=np.float32)
    ccl_edit_dists = np.array([f["ccl_edit_dist"] for f in formatted], dtype=np.float32)
    cosine_labels = np.array([f["cosine_49d"] for f in formatted], dtype=np.float32)

    condition_results: dict[str, Any] = {}
    t_cond_start = time.time()
    partial_path = output_dir / f"phase_c_v3_tpu_{condition}_partial.json"
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)

    for cond_name, lxi_lambda in lxi_conditions:
        print(f"\n{'='*60}")
        print(f"  {condition} / {cond_name} (λ={lxi_lambda})")
        print(f"{'='*60}")

        effective_max_len = max_len
        train_batch_size = batch_size
        effective_eval_batch_size = eval_batch_size

        if condition == "B" and lxi_lambda > 0:
            effective_max_len = min(max_len, b_lxi_max_len)
            train_batch_size = min(batch_size, b_lxi_train_batch_size)
            effective_eval_batch_size = min(eval_batch_size, b_lxi_eval_batch_size)
            print(
                f"  TPU guard: MAX_LEN {max_len} -> {effective_max_len}, "
                f"train_bs {batch_size} -> {train_batch_size}, eval_bs {eval_batch_size} -> {effective_eval_batch_size}"
            )

        dataset = build_tokenized_dataset(tokenizer, texts, labels, effective_max_len)
        fold_results: list[dict[str, Any]] = []

        for fold_idx, (train_idx, val_idx) in enumerate(skf.split(np.zeros(len(records)), labels.astype(int))):
            print(f"\n--- Fold {fold_idx + 1}/{n_folds} ---")
            fold_start = time.time()
            set_seed(42 + fold_idx)

            restore_trainable_state(model, initial_trainable_state, device)
            mark_step()

            train_subset = torch.utils.data.Subset(dataset, train_idx.tolist())
            val_subset = torch.utils.data.Subset(dataset, val_idx.tolist())
            train_loader = DataLoader(train_subset, batch_size=train_batch_size, shuffle=True, num_workers=0)
            val_loader = DataLoader(val_subset, batch_size=effective_eval_batch_size, shuffle=False, num_workers=0)

            trainable = [p for p in model.parameters() if p.requires_grad]
            optimizer = torch.optim.AdamW(trainable, lr=lr, weight_decay=0.01)
            total_opt_steps = max(1, math.ceil(len(train_loader) * epochs / grad_accum))
            scheduler = make_warmup_cosine_scheduler(
                optimizer=optimizer,
                total_steps=total_opt_steps,
                warmup_ratio=warmup_ratio,
            )

            try:
                ep_losses = []
                for epoch in range(epochs):
                    avg_train_loss = train_one_epoch(
                        model=model,
                        loader=train_loader,
                        optimizer=optimizer,
                        scheduler=scheduler,
                        device=device,
                        lxi_lambda=lxi_lambda,
                        grad_accum=grad_accum,
                        max_grad_norm=max_grad_norm,
                    )
                    ep_losses.append(avg_train_loss)
                    print(f"    epoch={epoch + 1}/{epochs} train_loss={avg_train_loss:.4f}")

                pred_logits = predict_scores(model, val_loader, device)
                pred_probs = 1.0 / (1.0 + np.exp(-pred_logits))

                true_cosine = cosine_labels[val_idx]
                true_binary = labels[val_idx].astype(int)
                val_text_lens = text_lengths[val_idx]
                val_ccl_edit = ccl_edit_dists[val_idx]

                pred_binary = (pred_probs >= 0.5).astype(int)
                acc = accuracy_score(true_binary, pred_binary)
                f1 = f1_score(true_binary, pred_binary, zero_division=0)
                rho, _ = spearmanr(pred_probs, true_cosine)
                rho_logits, _ = spearmanr(pred_logits, true_cosine)
                rho_ccl_logits, _ = spearmanr(pred_logits, 1.0 - val_ccl_edit)
                rho_ccl, _ = spearmanr(pred_probs, 1.0 - val_ccl_edit)
                p_rho = partial_spearman(pred_probs, true_cosine, val_text_lens)
                p_rho_ccl = partial_spearman(pred_probs, 1.0 - val_ccl_edit, val_text_lens)

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
                    "eval_batch_size": effective_eval_batch_size,
                    "seed": 42 + fold_idx,
                    "epoch_train_loss": [round(v, 6) for v in ep_losses],
                }
                fold_results.append(fold_result)

                print(
                    f"  acc={acc:.3f} F1={f1:.3f} ρ={rho:.4f} ρ_logits={rho_logits:.4f} "
                    f"偏ρ_ccl={p_rho_ccl:.4f} R@1={r_at_1:.2f} ({fold_sec:.0f}s)"
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
                        device_name=device_name,
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
                        device_name=device_name,
                        error=repr(exc),
                        failed_condition=cond_name,
                        failed_fold=fold_idx,
                    ),
                )
                raise
            finally:
                del optimizer
                del scheduler
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                mark_step()

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
            "eval_batch_size": effective_eval_batch_size,
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

        print(
            f"\n  ★ {cond_name}: acc={mean_acc:.3f} F1={mean_f1:.3f} "
            f"ρ_logits={mean_rho_logits:.4f} 偏ρ_ccl={mean_prho_ccl:.4f} R@1={mean_r1:.2f}"
        )
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
                device_name=device_name,
            ),
        )

    del model
    gc.collect()
    mark_step()

    elapsed = time.time() - t_cond_start
    print(f"\n⏱️ 条件 {condition}: {elapsed / 60:.1f} min")
    return {
        "condition": condition,
        "data_path": str(data_path.name),
        "n_pairs": len(records),
        "elapsed_minutes": round(elapsed / 60, 1),
        "results": condition_results,
    }


def print_summary(all_cond_results: list[dict[str, Any]]) -> None:
    print(f"\n{'=' * 100}")
    print("  Phase C v3 TPU — 3条件アブレーション サマリー (BCE)")
    print(f"{'=' * 100}")
    print(f"{'条件':<6} {'λ':<10} {'acc':>5} {'F1':>5} {'偏ρ_ccl':>8} {'ρ_ccl':>7} {'ρ_49d':>7} {'R@1':>5} {'R@5':>5} {'N':>5}")
    print("-" * 100)

    for cond_data in all_cond_results:
        cond = cond_data["condition"]
        n = cond_data["n_pairs"]
        for cond_name, data in cond_data["results"].items():
            print(
                f"{cond:<6} {cond_name:<10} "
                f"{data['mean_acc']:>5.3f} {data['mean_f1']:>5.3f} "
                f"{data['mean_partial_rho_ccl']:>8.4f} {data['mean_rho_ccl']:>7.4f} {data['mean_rho']:>7.4f} "
                f"{data['mean_r_at_1']:>5.2f} {data['mean_r_at_5']:>5.2f} {n:>5}"
            )

    print(f"\n{'=' * 100}")
    print("  条件間比較 (baseline λ=0)")
    print("  偏ρ_ccl = テキスト長除去後の構造理解指標")
    print(f"{'=' * 100}")
    for cond_data in all_cond_results:
        cond = cond_data["condition"]
        bl = cond_data["results"].get("baseline", {})
        if bl:
            print(
                f"  {cond}: acc={bl['mean_acc']:.3f} F1={bl['mean_f1']:.3f} "
                f"偏ρ_ccl={bl['mean_partial_rho_ccl']:.4f} R@1={bl['mean_r_at_1']:.2f}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase C v3 TPU: A/B/D ablation")
    parser.add_argument("--condition", choices=["A", "B", "D"], help="単一条件実行")
    parser.add_argument("--data", type=str, help="入力 JSONL パス (単一条件時)")
    parser.add_argument("--all", action="store_true", help="A/B/D 3条件一括実行")
    parser.add_argument("--model", default="codellama/CodeLlama-7b-hf")
    parser.add_argument("--output", default="phase_c_v3_tpu_results.json")
    parser.add_argument("--n-folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--eval-batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max-len", type=int, default=0, help="0=auto (A/D:512, B:1024)")
    parser.add_argument("--b-lxi-max-len", type=int, default=768)
    parser.add_argument("--b-lxi-train-batch-size", type=int, default=1)
    parser.add_argument("--b-lxi-eval-batch-size", type=int, default=1)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--warmup-ratio", type=float, default=0.1)
    parser.add_argument("--max-grad-norm", type=float, default=1.0)
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--quick", action="store_true", help="Quick: 2-fold × 2 λ条件 × 2 epochs")
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

    all_results: list[dict[str, Any]] = []
    t_total = time.time()
    output_path = Path(args.output)
    global_partial_path = output_path.with_name(output_path.stem + ".partial.json")
    _, device_name = get_device()
    runtime_meta = get_runtime_metadata()

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
            eval_batch_size=args.eval_batch_size,
            grad_accum=args.grad_accum,
            lr=args.lr,
            max_len=args.max_len,
            lxi_conditions=lxi_conditions,
            output_dir=_SCRIPT_DIR,
            b_lxi_max_len=args.b_lxi_max_len,
            b_lxi_train_batch_size=args.b_lxi_train_batch_size,
            b_lxi_eval_batch_size=args.b_lxi_eval_batch_size,
            lora_r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
            warmup_ratio=args.warmup_ratio,
            max_grad_norm=args.max_grad_norm,
            trust_remote_code=args.trust_remote_code,
        )
        all_results.append(result)
        write_json_atomic(
            global_partial_path,
            {
                "experiment": "phase_c_v3_tpu_partial",
                "model": args.model,
                "timestamp": datetime.now().isoformat(),
                "device": device_name,
                "config": {
                    "n_folds": args.n_folds,
                    "epochs": args.epochs,
                    "batch_size": args.batch_size,
                    "eval_batch_size": args.eval_batch_size,
                    "grad_accum": args.grad_accum,
                    "lr": args.lr,
                    "max_len": args.max_len,
                    "b_lxi_max_len": args.b_lxi_max_len,
                    "b_lxi_train_batch_size": args.b_lxi_train_batch_size,
                    "b_lxi_eval_batch_size": args.b_lxi_eval_batch_size,
                    "lora_r": args.lora_r,
                    "lora_alpha": args.lora_alpha,
                    "lora_dropout": args.lora_dropout,
                    "warmup_ratio": args.warmup_ratio,
                    "max_grad_norm": args.max_grad_norm,
                    "quick": args.quick,
                },
                "runtime": runtime_meta,
                "conditions": all_results,
                "updated_at": datetime.now().isoformat(),
            },
        )

    total_min = (time.time() - t_total) / 60
    print_summary(all_results)

    output = {
        "experiment": "phase_c_v3_tpu_ablation",
        "model": args.model,
        "timestamp": datetime.now().isoformat(),
        "total_minutes": round(total_min, 1),
        "device": device_name,
        "config": {
            "n_folds": args.n_folds,
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "eval_batch_size": args.eval_batch_size,
            "grad_accum": args.grad_accum,
            "lr": args.lr,
            "max_len": args.max_len,
            "b_lxi_max_len": args.b_lxi_max_len,
            "b_lxi_train_batch_size": args.b_lxi_train_batch_size,
            "b_lxi_eval_batch_size": args.b_lxi_eval_batch_size,
            "lora_r": args.lora_r,
            "lora_alpha": args.lora_alpha,
            "lora_dropout": args.lora_dropout,
            "warmup_ratio": args.warmup_ratio,
            "max_grad_norm": args.max_grad_norm,
            "quick": args.quick,
        },
        "runtime": runtime_meta,
        "implementation_notes": [
            "TPU/XLA rewrite uses LoRA + bf16 and a manual training loop.",
            "Results are backend-port results, not numerically identical reruns of the CUDA QLoRA Trainer path.",
            "Gradient checkpointing is disabled on XLA due to torch.utils.checkpoint device-module incompatibility.",
        ],
        "reference": {
            "phase_c_mini_rho": 0.963,
            "phase_c_mini_partial_rho": 0.960,
            "phase_c_mini_model": "codebert-base (125M)",
            "phase_c_mini_pairs": 246,
        },
        "conditions": all_results,
    }
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n💾 結果: {output_path}")
    print(f"⏱️ 総実行時間: {total_min:.1f} min")


if __name__ == "__main__":
    main()
