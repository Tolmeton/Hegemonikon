#!/usr/bin/env python3
"""Phase C layer sensitivity probe.

Goal:
  Test whether the D-only LXI gain is more recoverable through deeper LoRA
  adaptation than through shallow adaptation.

This is an MVP proxy, not a strict rerun of the 7B Phase C v3 experiment.
We keep the realistic B/D datasets and the same readouts, but switch the base
model to CodeBERT so the experiment is tractable on a single workstation.
"""

from __future__ import annotations

import argparse
import gc
import json
import math
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

SCRIPT_DIR = Path(__file__).parent
DEFAULT_B = SCRIPT_DIR / "phase_c_condition_B.jsonl"
DEFAULT_D = SCRIPT_DIR / "phase_c_condition_D.jsonl"
DEFAULT_OUTPUT = SCRIPT_DIR / "phase_c_layer_sensitivity_results.json"
_LAYER_INDEX_RE = re.compile(r"(?:^|\.)(?:layers|layer)\.(\d+)(?:\.|$)")


@dataclass
class PairRecord:
    text_a: str
    text_b: str
    label: int
    cosine_49d: float
    ccl_edit_dist: float
    ccl_sim: float
    pair_type: str
    condition: str

    @property
    def joined_text(self) -> str:
        return f"Structure A: {self.text_a}\n\nStructure B: {self.text_b}"

    @property
    def text_len(self) -> int:
        return len(self.text_a) + len(self.text_b)


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    tmp.replace(path)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
    except ImportError:
        return
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_jsonl(path: Path) -> list[PairRecord]:
    rows: list[PairRecord] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            rows.append(
                PairRecord(
                    text_a=obj["text_a"],
                    text_b=obj["text_b"],
                    label=int(obj["label"]),
                    cosine_49d=float(obj["cosine_49d"]),
                    ccl_edit_dist=float(obj["ccl_edit_dist"]),
                    ccl_sim=float(obj["ccl_sim"]),
                    pair_type=obj.get("pair_type", "unknown"),
                    condition=obj.get("condition", "unknown"),
                )
            )
    return rows


def verify_alignment(b_rows: list[PairRecord], d_rows: list[PairRecord]) -> dict[str, int]:
    if len(b_rows) != len(d_rows):
        raise ValueError(f"B/D length mismatch: {len(b_rows)} vs {len(d_rows)}")

    checks = {
        "label": 0,
        "cosine_49d": 0,
        "ccl_edit_dist": 0,
        "ccl_sim": 0,
    }
    for b_row, d_row in zip(b_rows, d_rows):
        checks["label"] += int(b_row.label == d_row.label)
        checks["cosine_49d"] += int(math.isclose(b_row.cosine_49d, d_row.cosine_49d, abs_tol=1e-9))
        checks["ccl_edit_dist"] += int(math.isclose(b_row.ccl_edit_dist, d_row.ccl_edit_dist, abs_tol=1e-9))
        checks["ccl_sim"] += int(math.isclose(b_row.ccl_sim, d_row.ccl_sim, abs_tol=1e-9))
    return checks


def stratified_sample_indices(labels: np.ndarray, sample_size: int, seed: int) -> list[int]:
    if sample_size <= 0 or sample_size >= len(labels):
        return list(range(len(labels)))

    pos_idx = np.where(labels == 1)[0]
    neg_idx = np.where(labels == 0)[0]
    rng = np.random.default_rng(seed)
    rng.shuffle(pos_idx)
    rng.shuffle(neg_idx)

    pos_target = min(len(pos_idx), sample_size // 2)
    neg_target = min(len(neg_idx), sample_size - pos_target)
    if pos_target + neg_target < sample_size:
        extra = sample_size - (pos_target + neg_target)
        if len(pos_idx) - pos_target >= extra:
            pos_target += extra
        else:
            neg_target += extra

    chosen = np.concatenate([pos_idx[:pos_target], neg_idx[:neg_target]])
    chosen = np.sort(chosen)
    return chosen.tolist()


def partial_spearman(pred: np.ndarray, true: np.ndarray, confound: np.ndarray) -> float:
    from scipy.stats import rankdata, spearmanr

    r_pred = rankdata(pred)
    r_true = rankdata(true)
    r_conf = rankdata(confound)

    def residualize(y: np.ndarray, x: np.ndarray) -> np.ndarray:
        x_centered = x - x.mean()
        denom = float((x_centered ** 2).sum())
        if denom < 1e-12:
            return y
        beta = float((x_centered * (y - y.mean())).sum() / denom)
        return y - beta * x_centered

    res_pred = residualize(r_pred, r_conf)
    res_true = residualize(r_true, r_conf)
    rho, _ = spearmanr(res_pred, res_true)
    return float(rho)


def discover_transformer_layer_indices(model: Any) -> list[int]:
    indices = set()
    for module_name, _module in model.named_modules():
        match = _LAYER_INDEX_RE.search(module_name)
        if match is not None:
            indices.add(int(match.group(1)))
    return sorted(indices)


def resolve_layer_window_indices(all_indices: list[int], layer_window: str) -> list[int]:
    if not all_indices:
        raise RuntimeError("Transformer layer index を検出できないため layer_window を解決できない")

    third = max(1, len(all_indices) // 3)
    if layer_window == "all":
        return list(all_indices)
    if layer_window == "shallow":
        return list(all_indices[:third])
    if layer_window == "mid":
        start = third
        end = min(len(all_indices), start + third)
        return list(all_indices[start:end])
    if layer_window == "deep":
        return list(all_indices[-third:])
    raise ValueError(f"Unknown layer_window: {layer_window}")


def extract_lora_layer_indices(model: Any) -> list[int]:
    indices = set()
    for param_name, param in model.named_parameters():
        if not param.requires_grad or "lora_" not in param_name:
            continue
        match = _LAYER_INDEX_RE.search(param_name)
        if match is not None:
            indices.add(int(match.group(1)))
    return sorted(indices)


def clone_trainable_state(model: Any) -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for name, param in model.named_parameters():
        if param.requires_grad:
            snapshot[name] = param.detach().cpu().clone()
    return snapshot


def restore_trainable_state(model: Any, snapshot: dict[str, Any], device: Any) -> None:
    named_params = dict(model.named_parameters())
    for name, saved in snapshot.items():
        param = named_params[name]
        param.data.copy_(saved.to(device=device, dtype=param.dtype))


def build_model(
    model_name: str,
    layer_window: str,
    device: Any,
    pad_token_id: int | None,
) -> tuple[Any, list[int], list[int]]:
    import torch
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import AutoModelForSequenceClassification

    try:
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=1,
            attn_implementation="eager",
        )
    except TypeError:
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=1,
        )
    if pad_token_id is not None:
        model.config.pad_token_id = pad_token_id

    available_layer_indices = discover_transformer_layer_indices(model)
    selected_layer_indices = resolve_layer_window_indices(available_layer_indices, layer_window)

    lora_kwargs: dict[str, Any] = {
        "r": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "bias": "none",
        "task_type": TaskType.SEQ_CLS,
        "target_modules": ["query", "key", "value"],
    }
    manual_layer_freeze = False
    if layer_window != "all":
        lora_kwargs["layers_to_transform"] = selected_layer_indices
        lora_kwargs["layers_pattern"] = "layer"

    try:
        lora_config = LoraConfig(**lora_kwargs)
    except TypeError:
        if layer_window == "all":
            raise
        manual_layer_freeze = True
        lora_kwargs.pop("layers_to_transform", None)
        lora_kwargs.pop("layers_pattern", None)
        lora_config = LoraConfig(**lora_kwargs)

    model = get_peft_model(model, lora_config)

    if manual_layer_freeze:
        selected_layer_set = set(selected_layer_indices)
        for param_name, param in model.named_parameters():
            if "lora_" not in param_name:
                continue
            match = _LAYER_INDEX_RE.search(param_name)
            if match is None:
                continue
            param.requires_grad = int(match.group(1)) in selected_layer_set

    active_lora_layers = extract_lora_layer_indices(model)
    if layer_window != "all" and set(active_lora_layers) != set(selected_layer_indices):
        raise RuntimeError(
            "layer_window verification failed: "
            f"expected={selected_layer_indices} actual={active_lora_layers}"
        )
    if not active_lora_layers:
        raise RuntimeError("LoRA layer index を抽出できない")

    model = model.to(device)
    return model, available_layer_indices, active_lora_layers


class TensorDictDataset:
    def __init__(self, encoded: dict[str, Any], labels: Any):
        self.encoded = encoded
        self.labels = labels

    def __len__(self) -> int:
        return int(self.labels.shape[0])

    def __getitem__(self, idx: int) -> dict[str, Any]:
        item = {k: v[idx] for k, v in self.encoded.items()}
        item["labels"] = self.labels[idx]
        return item


def build_tokenized_dataset(
    tokenizer: Any,
    texts: list[str],
    labels: np.ndarray,
    max_len: int,
) -> TensorDictDataset:
    import torch

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


def tensor_to_float(value: Any) -> float:
    return float(value.detach().float().cpu().item())


def train_one_epoch(
    model: Any,
    loader: Any,
    optimizer: Any,
    device: Any,
    lxi_lambda: float,
    grad_accum: int,
    max_grad_norm: float,
) -> float:
    import torch
    import torch.nn.functional as F_t

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

        if need_attn and outputs.attentions:
            attn = outputs.attentions[-1].float()
            attn_flat = attn.mean(dim=-1)
            head_var = attn_flat.var(dim=1).mean()
            loss = loss + lxi_lambda * (-head_var)

        (loss / grad_accum).backward()

        if step_idx % grad_accum == 0 or step_idx == len(loader):
            torch.nn.utils.clip_grad_norm_(
                [p for p in model.parameters() if p.requires_grad and p.grad is not None],
                max_grad_norm,
            )
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)

        running_loss += tensor_to_float(loss)
        steps += 1

    return running_loss / max(steps, 1)


def predict_scores(model: Any, loader: Any, device: Any) -> np.ndarray:
    model.eval()
    preds: list[np.ndarray] = []
    with torch_no_grad():
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
    if not preds:
        return np.empty((0,), dtype=np.float32)
    return np.concatenate(preds, axis=0)


def torch_no_grad():
    import torch

    return torch.no_grad()


def run_window_condition(
    *,
    condition: str,
    rows: list[PairRecord],
    sample_indices: list[int],
    model_name: str,
    max_len: int,
    layer_window: str,
    n_folds: int,
    epochs: int,
    batch_size: int,
    eval_batch_size: int,
    grad_accum: int,
    lr: float,
    max_grad_norm: float,
    lxi_conditions: list[tuple[str, float]],
    seed: int,
    device: Any,
    output_path: Path,
) -> dict[str, Any]:
    import torch
    from sklearn.metrics import accuracy_score, f1_score
    from sklearn.model_selection import StratifiedKFold
    from torch.utils.data import DataLoader, Subset
    from transformers import AutoTokenizer
    from scipy.stats import spearmanr

    sampled_rows = [rows[i] for i in sample_indices]
    texts = [row.joined_text for row in sampled_rows]
    labels = np.array([row.label for row in sampled_rows], dtype=np.float32)
    cosine_labels = np.array([row.cosine_49d for row in sampled_rows], dtype=np.float32)
    ccl_targets = np.array([1.0 - row.ccl_edit_dist for row in sampled_rows], dtype=np.float32)
    text_lengths = np.array([row.text_len for row in sampled_rows], dtype=np.float32)

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token or tokenizer.sep_token
    dataset = build_tokenized_dataset(tokenizer, texts, labels, max_len=max_len)

    model, available_layers, active_layers = build_model(
        model_name,
        layer_window,
        device,
        tokenizer.pad_token_id,
    )
    initial_state = clone_trainable_state(model)
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    condition_result: dict[str, Any] = {
        "condition": condition,
        "sample_size": len(sampled_rows),
        "max_len": max_len,
        "available_layer_indices": available_layers,
        "active_lora_layers": active_layers,
        "windows": {},
    }

    for cond_name, lxi_lambda in lxi_conditions:
        fold_results: list[dict[str, Any]] = []
        for fold_idx, (train_idx, val_idx) in enumerate(skf.split(np.zeros(len(labels)), labels.astype(int))):
            fold_seed = seed + fold_idx
            set_seed(fold_seed)
            restore_trainable_state(model, initial_state, device)

            train_subset = Subset(dataset, train_idx.tolist())
            val_subset = Subset(dataset, val_idx.tolist())
            train_loader = DataLoader(train_subset, batch_size=batch_size, shuffle=True, num_workers=0)
            val_loader = DataLoader(val_subset, batch_size=eval_batch_size, shuffle=False, num_workers=0)

            optimizer = torch.optim.AdamW(
                [param for param in model.parameters() if param.requires_grad],
                lr=lr,
                weight_decay=0.01,
            )

            fold_start = time.time()
            epoch_losses = []
            for _epoch in range(epochs):
                avg_loss = train_one_epoch(
                    model=model,
                    loader=train_loader,
                    optimizer=optimizer,
                    device=device,
                    lxi_lambda=lxi_lambda,
                    grad_accum=grad_accum,
                    max_grad_norm=max_grad_norm,
                )
                epoch_losses.append(avg_loss)

            pred_logits = predict_scores(model, val_loader, device)
            pred_probs = 1.0 / (1.0 + np.exp(-pred_logits))
            true_binary = labels[val_idx].astype(int)
            true_cosine = cosine_labels[val_idx]
            true_ccl = ccl_targets[val_idx]
            val_text_lens = text_lengths[val_idx]
            pred_binary = (pred_probs >= 0.5).astype(int)

            acc = accuracy_score(true_binary, pred_binary)
            f1 = f1_score(true_binary, pred_binary, zero_division=0)
            rho, _ = spearmanr(pred_probs, true_cosine)
            rho_logits, _ = spearmanr(pred_logits, true_cosine)
            rho_ccl, _ = spearmanr(pred_probs, true_ccl)
            rho_ccl_logits, _ = spearmanr(pred_logits, true_ccl)
            partial_rho = partial_spearman(pred_probs, true_cosine, val_text_lens)
            partial_rho_ccl = partial_spearman(pred_probs, true_ccl, val_text_lens)

            pos_mask = true_binary == 1
            neg_mask = true_binary == 0
            pos_scores = pred_probs[pos_mask]
            neg_scores = pred_probs[neg_mask]
            if len(pos_scores) > 0 and len(neg_scores) > 0:
                neg_sorted = np.sort(neg_scores)[::-1]
                hits = {1: 0, 10: 0}
                for ps in pos_scores:
                    rank = int(np.searchsorted(-neg_sorted, -ps))
                    for k in hits:
                        if rank < k:
                            hits[k] += 1
                n_pos = len(pos_scores)
                r_at_1 = hits[1] / n_pos
                r_at_10 = hits[10] / n_pos
            else:
                r_at_1 = 0.0
                r_at_10 = 0.0

            fold_result = {
                "fold": fold_idx,
                "seed": fold_seed,
                "acc": float(acc),
                "f1": float(f1),
                "rho": float(rho),
                "rho_logits": float(rho_logits),
                "rho_ccl": float(rho_ccl),
                "rho_ccl_logits": float(rho_ccl_logits),
                "partial_rho": float(partial_rho),
                "partial_rho_ccl": float(partial_rho_ccl),
                "r_at_1": float(r_at_1),
                "r_at_10": float(r_at_10),
                "epoch_train_loss": [round(v, 6) for v in epoch_losses],
                "elapsed_sec": round(time.time() - fold_start, 1),
            }
            fold_results.append(fold_result)
            del optimizer
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        means = {
            "lambda": lxi_lambda,
            "mean_acc": float(np.mean([f["acc"] for f in fold_results])),
            "mean_f1": float(np.mean([f["f1"] for f in fold_results])),
            "mean_rho": float(np.mean([f["rho"] for f in fold_results])),
            "mean_rho_logits": float(np.mean([f["rho_logits"] for f in fold_results])),
            "mean_rho_ccl": float(np.mean([f["rho_ccl"] for f in fold_results])),
            "mean_rho_ccl_logits": float(np.mean([f["rho_ccl_logits"] for f in fold_results])),
            "mean_partial_rho": float(np.mean([f["partial_rho"] for f in fold_results])),
            "mean_partial_rho_ccl": float(np.mean([f["partial_rho_ccl"] for f in fold_results])),
            "mean_r_at_1": float(np.mean([f["r_at_1"] for f in fold_results])),
            "mean_r_at_10": float(np.mean([f["r_at_10"] for f in fold_results])),
            "folds": fold_results,
        }
        condition_result["windows"][cond_name] = means

    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return condition_result


def summarize_condition_windows(results: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for window_name, condition_blob in results.items():
        baseline = condition_blob["windows"]["baseline"]
        item = {
            "baseline_partial_rho_ccl": baseline["mean_partial_rho_ccl"],
            "baseline_acc": baseline["mean_acc"],
        }
        delta_table: dict[str, Any] = {}
        for cond_name, blob in condition_blob["windows"].items():
            if cond_name == "baseline":
                continue
            delta_table[cond_name] = {
                "partial_rho_ccl": blob["mean_partial_rho_ccl"],
                "delta_partial_rho_ccl": blob["mean_partial_rho_ccl"] - baseline["mean_partial_rho_ccl"],
                "acc": blob["mean_acc"],
                "delta_acc": blob["mean_acc"] - baseline["mean_acc"],
            }

        if len(delta_table) == 1:
            only_name, only_blob = next(iter(delta_table.items()))
            item["comparison_label"] = only_name
            item["lxi_partial_rho_ccl"] = only_blob["partial_rho_ccl"]
            item["delta_partial_rho_ccl"] = only_blob["delta_partial_rho_ccl"]
            item["lxi_acc"] = only_blob["acc"]
            item["delta_acc"] = only_blob["delta_acc"]
        else:
            item["comparisons"] = delta_table
        summary[window_name] = item
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase C layer sensitivity probe")
    parser.add_argument("--model", default="microsoft/codebert-base")
    parser.add_argument("--conditions", nargs="+", default=["D", "B"], choices=["B", "D"])
    parser.add_argument("--windows", nargs="+", default=["shallow", "mid", "deep"], choices=["all", "shallow", "mid", "deep"])
    parser.add_argument("--sample-size", type=int, default=320)
    parser.add_argument("--max-len", type=int, default=256)
    parser.add_argument("--max-len-b", type=int, default=None)
    parser.add_argument("--max-len-d", type=int, default=None)
    parser.add_argument("--n-folds", type=int, default=2)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--eval-batch-size", type=int, default=16)
    parser.add_argument("--grad-accum", type=int, default=1)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max-grad-norm", type=float, default=1.0)
    parser.add_argument("--lxi-lambdas", nargs="+", type=float, default=[0.0, 1.0])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    import torch

    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    b_rows = load_jsonl(DEFAULT_B)
    d_rows = load_jsonl(DEFAULT_D)
    alignment = verify_alignment(b_rows, d_rows)

    labels = np.array([row.label for row in d_rows], dtype=np.int32)
    sample_indices = stratified_sample_indices(labels, args.sample_size, args.seed)

    by_condition = {"B": b_rows, "D": d_rows}
    condition_max_len = {
        "B": args.max_len_b if args.max_len_b is not None else args.max_len,
        "D": args.max_len_d if args.max_len_d is not None else args.max_len,
    }
    lxi_conditions: list[tuple[str, float]] = []
    for value in args.lxi_lambdas:
        if abs(value) < 1e-12:
            label = "baseline"
        else:
            label = f"lxi_{value:g}"
        lxi_conditions.append((label, value))

    payload: dict[str, Any] = {
        "experiment": "phase_c_layer_sensitivity",
        "timestamp": datetime.now().isoformat(),
        "model": args.model,
        "device": str(device),
        "alignment": alignment,
        "config": {
            "conditions": args.conditions,
            "windows": args.windows,
            "sample_size": args.sample_size,
            "sampled_indices": sample_indices,
            "max_len": args.max_len,
            "condition_max_len": condition_max_len,
            "n_folds": args.n_folds,
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "eval_batch_size": args.eval_batch_size,
            "grad_accum": args.grad_accum,
            "lr": args.lr,
            "max_grad_norm": args.max_grad_norm,
            "lxi_lambdas": args.lxi_lambdas,
            "seed": args.seed,
        },
        "conditions": {},
    }
    write_json_atomic(args.output, payload)

    for condition in args.conditions:
        per_window: dict[str, Any] = {}
        rows = by_condition[condition]
        for window in args.windows:
            window_result = run_window_condition(
                condition=condition,
                rows=rows,
                sample_indices=sample_indices,
                model_name=args.model,
                max_len=condition_max_len[condition],
                layer_window=window,
                n_folds=args.n_folds,
                epochs=args.epochs,
                batch_size=args.batch_size,
                eval_batch_size=args.eval_batch_size,
                grad_accum=args.grad_accum,
                lr=args.lr,
                max_grad_norm=args.max_grad_norm,
                lxi_conditions=lxi_conditions,
                seed=args.seed,
                device=device,
                output_path=args.output,
            )
            per_window[window] = window_result
            payload["conditions"][condition] = per_window
            write_json_atomic(args.output, payload)

        payload["conditions"][condition]["summary"] = summarize_condition_windows(per_window)
        write_json_atomic(args.output, payload)

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
