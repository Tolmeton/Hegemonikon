#!/usr/bin/env python3
"""Phase C: CodeLlama 13B QLoRA — CCL Structural Similarity
Lēthē / Force is Oblivion / Hegemonikón Research

Usage: python phase_c_qlora_run.py [--data DATA_PATH] [--model MODEL] [--output OUTPUT_DIR]
"""
import argparse
import json
import os
import time
import copy

import numpy as np
import torch
import torch.nn as nn
from scipy.stats import spearmanr
from sklearn.metrics import accuracy_score, f1_score, mean_squared_error
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType
from datasets import Dataset


# === Config ===
MAX_LEN = 512
XI_LAMBDA = 1.0
N_EPOCHS = 5
BATCH_SIZE = 4
GRAD_ACCUM = 4
LR = 2e-4
SEED = 42


def load_pairs(path):
    """JSONL から CCL ペアを読み込み"""
    pairs = []
    with open(path) as f:
        for line in f:
            d = json.loads(line)
            anchor = d.get('anchor_ccl', '')
            candidate = d.get('candidate_ccl', '')
            if not anchor and 'metadata' in d:
                anchor = d['metadata'].get('anchor_ccl', '')
                candidate = d['metadata'].get('candidate_ccl', '')
            if anchor and candidate:
                pairs.append({
                    'anchor': anchor,
                    'candidate': candidate,
                    'label': d['label'],
                    'cosine_49d': d.get('cosine_49d', 0.0),
                    'pair_type': d.get('pair_type', 'unknown'),
                })
    return pairs


def encode_pair(tokenizer, anchor, candidate):
    text = f'Structure A: {anchor}\n\nStructure B: {candidate}'
    return tokenizer(
        text, padding='max_length', truncation=True,
        max_length=MAX_LEN, return_tensors='pt',
    )


def measure_rho(model, tokenizer, pairs, n_sample=200):
    """fine-tune 前/後の Spearman ρ 測定"""
    model.eval()
    rng = np.random.RandomState(SEED)
    indices = rng.choice(len(pairs), min(n_sample, len(pairs)), replace=False)
    preds, labels, lengths = [], [], []
    with torch.no_grad():
        for i, idx in enumerate(indices):
            p = pairs[idx]
            inputs = encode_pair(tokenizer, p['anchor'], p['candidate'])
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
            out = model(**inputs)
            preds.append(out.logits.squeeze().item())
            labels.append(p['label'])
            lengths.append(len(p['anchor']) + len(p['candidate']))
            if (i + 1) % 50 == 0:
                print(f'  [{i+1}/{len(indices)}]')

    preds = np.array(preds)
    labels = np.array(labels)
    lengths = np.array(lengths)

    rho, p_val = spearmanr(preds, labels)

    # 偏ρ (コード長除去)
    rho_pl, _ = spearmanr(preds, lengths)
    rho_ll, _ = spearmanr(labels, lengths)
    denom = np.sqrt(max(1 - rho_pl**2, 1e-10)) * np.sqrt(max(1 - rho_ll**2, 1e-10))
    partial_rho = (rho - rho_pl * rho_ll) / denom

    return {'rho': rho, 'p_val': p_val, 'partial_rho': partial_rho}


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = logits.squeeze()
    rho, p_val = spearmanr(preds, labels)
    mse = mean_squared_error(labels, preds)
    bp = (preds > 0.5).astype(int)
    bl = (labels > 0.5).astype(int)
    return {
        'rho': rho, 'mse': mse,
        'accuracy': accuracy_score(bl, bp),
        'f1': f1_score(bl, bp, average='binary'),
    }


class XiRegularizedTrainer(Trainer):
    """Ξ 正則化: LoRA 重みの不均一度を最大化"""
    def __init__(self, *args, xi_lambda=1.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.xi_lambda = xi_lambda

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        outputs = model(**inputs)
        loss = outputs.loss
        if self.xi_lambda > 0:
            xi_total, n_p = 0.0, 0
            for name, param in model.named_parameters():
                if 'lora' in name and param.requires_grad and param.numel() > 1:
                    xi_total += param.view(-1).float().var()
                    n_p += 1
            if n_p > 0:
                loss = loss - self.xi_lambda * (xi_total / n_p)
        return (loss, outputs) if return_outputs else loss


def make_args(output_dir):
    return TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=N_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=8,
        gradient_accumulation_steps=GRAD_ACCUM,
        learning_rate=LR,
        weight_decay=0.01,
        warmup_ratio=0.1,
        lr_scheduler_type='cosine',
        eval_strategy='epoch',
        save_strategy='epoch',
        load_best_model_at_end=True,
        metric_for_best_model='rho',
        greater_is_better=True,
        bf16=True,
        logging_steps=10,
        report_to='none',
        remove_unused_columns=False,
        seed=SEED,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default='phase_c_training_ccl.jsonl')
    parser.add_argument('--model', default='codellama/CodeLlama-13b-hf')
    parser.add_argument('--output', default='phase_c_results')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    t0 = time.time()

    # === Data ===
    print('=' * 60)
    print('Phase C QLoRA — CCL Structural Similarity')
    print('=' * 60)
    pairs = load_pairs(args.data)
    pos = sum(1 for p in pairs if p['label'] == 1)
    print(f'Data: {len(pairs)} pairs (pos={pos}, neg={len(pairs)-pos})')

    # === Model ===
    print(f'\nLoading {args.model} (4bit)...')
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type='nf4',
        bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = 'right'

    model = AutoModelForSequenceClassification.from_pretrained(
        args.model, num_labels=1, quantization_config=bnb_config,
        device_map='auto', torch_dtype=torch.bfloat16,
    )
    model.config.pad_token_id = tokenizer.pad_token_id
    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias='none',
        task_type=TaskType.SEQ_CLS,
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj'],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    print(f'GPU mem: {torch.cuda.memory_allocated()/1e9:.2f} GB')

    # === Baseline ===
    print('\n--- Baseline (pre-finetune) ---')
    baseline = measure_rho(model, tokenizer, pairs)
    print(f'Baseline ρ = {baseline["rho"]:.4f} (partial ρ = {baseline["partial_rho"]:.4f})')

    # === Dataset ===
    texts, labels = [], []
    for p in pairs:
        texts.append(f"Structure A: {p['anchor']}\n\nStructure B: {p['candidate']}")
        labels.append(float(p['label']))
    full_ds = Dataset.from_dict({'text': texts, 'label': labels})
    split = full_ds.train_test_split(test_size=0.2, seed=SEED)

    def tok_fn(batch):
        return tokenizer(batch['text'], padding='max_length', truncation=True, max_length=MAX_LEN)

    train_tok = split['train'].map(tok_fn, batched=True, remove_columns=['text'])
    eval_tok = split['test'].map(tok_fn, batched=True, remove_columns=['text'])
    train_tok.set_format('torch')
    eval_tok.set_format('torch')
    print(f'Train: {len(train_tok)}, Eval: {len(eval_tok)}')

    # Save initial LoRA state for reset
    initial_state = {}
    for name, param in model.named_parameters():
        if 'lora' in name and param.requires_grad:
            initial_state[name] = param.data.clone()

    # === Condition A: λ=0 ===
    print('\n' + '=' * 60)
    print('Condition A: λ=0 (no L_Ξ)')
    print('=' * 60)
    trainer_a = Trainer(
        model=model, args=make_args(f'{args.output}/lambda0'),
        train_dataset=train_tok, eval_dataset=eval_tok,
        compute_metrics=compute_metrics,
    )
    trainer_a.train()
    eval_a = trainer_a.evaluate()
    print(f'Cond A: ρ={eval_a["eval_rho"]:.4f}, F1={eval_a["eval_f1"]:.4f}')

    # Full eval for Condition A
    print('\n--- Condition A full evaluation ---')
    full_a = measure_rho(model, tokenizer, pairs)
    print(f'Full ρ={full_a["rho"]:.4f}, partial ρ={full_a["partial_rho"]:.4f}')

    model.save_pretrained(f'{args.output}/lora_lambda0')

    # === Reset LoRA ===
    for name, param in model.named_parameters():
        if name in initial_state:
            param.data.copy_(initial_state[name])
    print('\nLoRA weights reset.')

    # === Condition B: λ=1.0 ===
    print('\n' + '=' * 60)
    print(f'Condition B: λ={XI_LAMBDA} (with L_Ξ)')
    print('=' * 60)
    trainer_b = XiRegularizedTrainer(
        model=model, args=make_args(f'{args.output}/lambda1'),
        train_dataset=train_tok, eval_dataset=eval_tok,
        compute_metrics=compute_metrics, xi_lambda=XI_LAMBDA,
    )
    trainer_b.train()
    eval_b = trainer_b.evaluate()
    print(f'Cond B: ρ={eval_b["eval_rho"]:.4f}, F1={eval_b["eval_f1"]:.4f}')

    # Full eval for Condition B
    print('\n--- Condition B full evaluation ---')
    full_b = measure_rho(model, tokenizer, pairs)
    print(f'Full ρ={full_b["rho"]:.4f}, partial ρ={full_b["partial_rho"]:.4f}')

    model.save_pretrained(f'{args.output}/lora_lambda1')
    tokenizer.save_pretrained(f'{args.output}/lora_lambda1')

    elapsed = time.time() - t0

    # === Results ===
    rho_a = eval_a['eval_rho']
    rho_b = eval_b['eval_rho']

    summary = {
        'experiment': 'Phase C QLoRA',
        'model': args.model,
        'n_pairs': len(pairs),
        'elapsed_seconds': elapsed,
        'baseline': baseline,
        'condition_a': {
            'lambda': 0.0,
            'eval_rho': rho_a, 'eval_f1': eval_a['eval_f1'],
            'eval_accuracy': eval_a['eval_accuracy'], 'eval_mse': eval_a['eval_mse'],
            'full_rho': full_a['rho'], 'full_partial_rho': full_a['partial_rho'],
        },
        'condition_b': {
            'lambda': XI_LAMBDA,
            'eval_rho': rho_b, 'eval_f1': eval_b['eval_f1'],
            'eval_accuracy': eval_b['eval_accuracy'], 'eval_mse': eval_b['eval_mse'],
            'full_rho': full_b['rho'], 'full_partial_rho': full_b['partial_rho'],
        },
        'comparison': {'phase_c_mini_codebert': 0.963, 'phase_b2_probe': 0.745},
        'hypotheses': {
            'P11_prime': {'verdict': 'supported' if rho_b > 0.963 else 'not_reached',
                          'delta_rho': rho_b - 0.963},
            'P14': {'verdict': 'supported' if rho_b > rho_a else 'not_reached',
                    'delta_rho': rho_b - rho_a},
        },
    }

    out_path = f'{args.output}/phase_c_qlora_results.json'
    with open(out_path, 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print('\n' + '=' * 60)
    print('RESULTS')
    print('=' * 60)
    print(f'{"":30s} {"ρ":>8s} {"偏ρ":>8s} {"F1":>8s}')
    print('-' * 60)
    print(f'{"Phase B2 (Attentive Probe)":30s} {0.745:8.4f} {"":>8s} {"":>8s}')
    print(f'{"Phase C-mini (CodeBERT)":30s} {0.963:8.4f} {"":>8s} {"":>8s}')
    print(f'{"Baseline (pre-finetune)":30s} {baseline["rho"]:8.4f} {baseline["partial_rho"]:8.4f} {"":>8s}')
    print(f'{"Condition A (λ=0)":30s} {rho_a:8.4f} {full_a["partial_rho"]:8.4f} {eval_a["eval_f1"]:8.4f}')
    print(f'{"Condition B (λ=1.0)":30s} {rho_b:8.4f} {full_b["partial_rho"]:8.4f} {eval_b["eval_f1"]:8.4f}')
    print('-' * 60)
    print(f'Δρ (B vs baseline): {rho_b - baseline["rho"]:+.4f}')
    print(f'Δρ (B vs A):        {rho_b - rho_a:+.4f}')
    print(f'Δρ (B vs C-mini):   {rho_b - 0.963:+.4f}')
    print(f'\nP11\' (QLoRA > C-mini): {"SUPPORTED" if rho_b > 0.963 else "NOT REACHED"}')
    print(f'P14  (λ>0 > λ=0):    {"SUPPORTED" if rho_b > rho_a else "NOT REACHED"}')
    print(f'\nElapsed: {elapsed:.0f}s ({elapsed/60:.1f}m)')
    print(f'Results: {out_path}')


if __name__ == '__main__':
    main()
