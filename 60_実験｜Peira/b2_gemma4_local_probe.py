#!/usr/bin/env python3
"""B2 Gemma4 フォローアップ: ローカル probe 実験 (CPU-only)。

前提: b2_gemma4_extracted.npz が VM から転送済み。

実験:
  E1: PCA 768d → Attentive Probe (hidden_dim 仮説検証)
  E2: 全43層 mean-pool → baseline MLP probe (層選択仮説検証)
  E3: epochs=20 + dropout=0.5 (正則化強化)

Usage:
  python3 b2_gemma4_local_probe.py --data b2_gemma4_extracted.npz --experiment all
  python3 b2_gemma4_local_probe.py --data b2_gemma4_extracted.npz --experiment E1
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
from sklearn.model_selection import StratifiedKFold

import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================
# Probe Models (from nonlinear_probe.py, adapted for CPU)
# ============================================================

class AttentivePooling(nn.Module):
    """Learnable query × cross-attention."""
    def __init__(self, hidden_dim: int, n_queries: int = 4):
        super().__init__()
        self.queries = nn.Parameter(torch.randn(1, n_queries, hidden_dim) * 0.02)
        self.attn = nn.MultiheadAttention(hidden_dim, num_heads=4, batch_first=True)

    def forward(self, hidden_states):
        # hidden_states: (1, seq_len, hidden_dim)
        queries = self.queries.expand(hidden_states.size(0), -1, -1)
        out, attn_weights = self.attn(queries, hidden_states, hidden_states)
        pooled = out.mean(dim=1)  # (1, hidden_dim)
        return pooled, attn_weights


class StructuralHead(nn.Module):
    """Structural similarity prediction."""
    def __init__(self, hidden_dim: int, intermediate_dim: int = 64, dropout: float = 0.2):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(hidden_dim * 2, intermediate_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(intermediate_dim, 1),
            nn.Sigmoid(),
        )

    def forward(self, repr_a, repr_b):
        diff = torch.abs(repr_a - repr_b)
        product = repr_a * repr_b
        combined = torch.cat([diff, product], dim=-1)
        return self.mlp(combined).squeeze(-1)


class AttentiveProbe(nn.Module):
    """Full attentive probe: pooling + head."""
    def __init__(self, hidden_dim: int, n_queries: int = 4,
                 intermediate_dim: int = 64, dropout: float = 0.2):
        super().__init__()
        self.pooling = AttentivePooling(hidden_dim, n_queries)
        self.head = StructuralHead(hidden_dim, intermediate_dim, dropout)

    def forward(self, hs_a, hs_b):
        repr_a, _ = self.pooling(hs_a)
        repr_b, _ = self.pooling(hs_b)
        return self.head(repr_a, repr_b)


class MeanPoolProbe(nn.Module):
    """Baseline: mean-pool + MLP."""
    def __init__(self, hidden_dim: int, intermediate_dim: int = 64, dropout: float = 0.2):
        super().__init__()
        self.head = StructuralHead(hidden_dim, intermediate_dim, dropout)

    def forward(self, repr_a, repr_b):
        return self.head(repr_a, repr_b)


# ============================================================
# Training
# ============================================================

def train_probe(probe, train_pairs, val_pairs, epochs=50, lr=1e-3):
    """Train probe and evaluate. Returns (rho, partial_rho, mse)."""
    optimizer = torch.optim.Adam(probe.parameters(), lr=lr)

    for epoch in range(epochs):
        probe.train()
        total_loss = 0
        np.random.shuffle(train_pairs)

        for pair in train_pairs:
            optimizer.zero_grad()
            pred = probe(pair["hs_a"], pair["hs_b"])
            target = torch.tensor([pair["label"]], dtype=torch.float32)
            loss = F.mse_loss(pred, target)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

    # Evaluate
    probe.eval()
    preds = []
    labels = []
    with torch.no_grad():
        for pair in val_pairs:
            pred = probe(pair["hs_a"], pair["hs_b"])
            preds.append(pred.item())
            labels.append(pair["label"])

    preds = np.array(preds)
    labels = np.array(labels)

    if len(set(preds)) <= 1:
        return 0.0, 0.0, 0.0  # Collapsed to constant

    rho, _ = spearmanr(preds, labels)
    mse = float(np.mean((preds - labels) ** 2))

    # Partial rho (controlling for length_ratio)
    length_ratios = np.array([p["length_ratio"] for p in val_pairs])
    if np.std(length_ratios) > 1e-8:
        from scipy.stats import spearmanr as _sp
        # Residualize
        from numpy.polynomial import polynomial as P
        c_pred = P.polyfit(length_ratios, preds, 1)
        c_label = P.polyfit(length_ratios, labels, 1)
        resid_pred = preds - P.polyval(length_ratios, c_pred)
        resid_label = labels - P.polyval(length_ratios, c_label)
        partial_rho, _ = _sp(resid_pred, resid_label)
    else:
        partial_rho = rho

    return float(rho) if not np.isnan(rho) else 0.0, \
           float(partial_rho) if not np.isnan(partial_rho) else 0.0, \
           mse


# ============================================================
# Experiments
# ============================================================

def load_extracted(path: str):
    """Load pre-extracted data from npz."""
    data = np.load(path, allow_pickle=True)
    unique_hashes = data["unique_hashes"]
    pair_keys = json.loads(str(data["pair_keys_json"]))
    n_layers = int(data["n_layers"])
    hidden_dim = int(data["hidden_dim"])
    meanpool = data["meanpool"]  # (n_snippets, n_layers, hidden_dim)
    raw_last = data["raw_last_layer"]  # (total_tokens, hidden_dim)
    offsets = data["raw_last_offsets"]  # (n_snippets + 1,)

    hash_to_idx = {h: i for i, h in enumerate(unique_hashes)}
    return {
        "pair_keys": pair_keys,
        "hash_to_idx": hash_to_idx,
        "n_layers": n_layers,
        "hidden_dim": hidden_dim,
        "meanpool": meanpool,
        "raw_last": raw_last,
        "offsets": offsets,
    }


def get_raw_sequence(data, snippet_idx):
    """Get raw token-level sequence for a snippet."""
    start = data["offsets"][snippet_idx]
    end = data["offsets"][snippet_idx + 1]
    return data["raw_last"][start:end]  # (seq_len, hidden_dim)


def run_cv(data, make_probe_fn, prepare_pair_fn, n_folds=5, epochs=50, label=""):
    """Run cross-validation and return results."""
    pair_keys = data["pair_keys"]
    hash_to_idx = data["hash_to_idx"]

    labels_binary = np.array([1 if p["is_positive"] else 0 for p in pair_keys])
    labels_cont = np.array([p["ccl_similarity"] for p in pair_keys])

    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
    fold_results = []

    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(np.zeros(len(pair_keys)), labels_binary)):
        t0 = time.time()

        train_pairs = [prepare_pair_fn(data, pair_keys[i]) for i in train_idx]
        val_pairs = [prepare_pair_fn(data, pair_keys[i]) for i in val_idx]

        probe = make_probe_fn()
        rho, partial_rho, mse = train_probe(probe, train_pairs, val_pairs, epochs=epochs)

        elapsed = time.time() - t0
        fold_results.append({"fold": fold_idx, "rho": rho, "partial_rho": partial_rho, "mse": mse, "elapsed": elapsed})
        print(f"  [{label}] Fold {fold_idx+1}/{n_folds}: ρ={rho:.4f}  偏ρ={partial_rho:.4f}  MSE={mse:.4f}  ({elapsed:.0f}s)")

    mean_rho = np.mean([r["rho"] for r in fold_results])
    mean_partial = np.mean([r["partial_rho"] for r in fold_results])
    mean_mse = np.mean([r["mse"] for r in fold_results])
    print(f"  ★ {label} 平均: ρ={mean_rho:.4f}  偏ρ={mean_partial:.4f}  MSE={mean_mse:.4f}")
    return {"label": label, "mean_rho": mean_rho, "mean_partial_rho": mean_partial, "mean_mse": mean_mse, "folds": fold_results}


def experiment_E1(data, pca_dim=768):
    """E1: PCA dimension reduction → Attentive Probe."""
    print(f"\n{'='*60}")
    print(f"  E1: PCA {data['hidden_dim']}d → {pca_dim}d + Attentive Probe")
    print(f"{'='*60}")

    # Fit PCA on all raw last-layer tokens
    print("  Fitting PCA...")
    pca = PCA(n_components=pca_dim)
    pca.fit(data["raw_last"])
    explained = pca.explained_variance_ratio_.sum()
    print(f"  PCA explained variance: {explained:.3f}")

    def prepare_pair(data, pair):
        idx_a = data["hash_to_idx"][pair["hash_a"]]
        idx_b = data["hash_to_idx"][pair["hash_b"]]
        raw_a = get_raw_sequence(data, idx_a)
        raw_b = get_raw_sequence(data, idx_b)
        # PCA transform
        pca_a = pca.transform(raw_a)  # (seq_len, pca_dim)
        pca_b = pca.transform(raw_b)
        return {
            "hs_a": torch.from_numpy(pca_a).unsqueeze(0).float(),
            "hs_b": torch.from_numpy(pca_b).unsqueeze(0).float(),
            "label": pair["ccl_similarity"],
            "length_ratio": pair["length_ratio"],
        }

    def make_probe():
        return AttentiveProbe(pca_dim, n_queries=4, intermediate_dim=64, dropout=0.2)

    return run_cv(data, make_probe, prepare_pair, n_folds=5, epochs=30, label=f"E1_PCA{pca_dim}")


def experiment_E2(data):
    """E2: Layer scan with mean-pool baseline."""
    print(f"\n{'='*60}")
    print(f"  E2: Layer scan (mean-pool baseline, all {data['n_layers']} layers)")
    print(f"{'='*60}")

    results = []
    for layer_idx in range(data["n_layers"]):
        def prepare_pair(data, pair, _layer=layer_idx):
            idx_a = data["hash_to_idx"][pair["hash_a"]]
            idx_b = data["hash_to_idx"][pair["hash_b"]]
            repr_a = data["meanpool"][idx_a, _layer]
            repr_b = data["meanpool"][idx_b, _layer]
            return {
                "hs_a": torch.from_numpy(repr_a).unsqueeze(0).float(),
                "hs_b": torch.from_numpy(repr_b).unsqueeze(0).float(),
                "label": pair["ccl_similarity"],
                "length_ratio": pair["length_ratio"],
            }

        def make_probe():
            return MeanPoolProbe(data["hidden_dim"], intermediate_dim=64, dropout=0.2)

        r = run_cv(data, make_probe, prepare_pair, n_folds=5, epochs=30, label=f"L{layer_idx}")
        r["layer"] = layer_idx
        results.append(r)

    # Summary
    print(f"\n--- Layer scan summary ---")
    print(f"{'Layer':>5} {'ρ':>8} {'偏ρ':>8} {'MSE':>8}")
    best_rho = -1
    best_layer = -1
    for r in results:
        print(f"  L{r['layer']:>3}  {r['mean_rho']:>8.4f}  {r['mean_partial_rho']:>8.4f}  {r['mean_mse']:>8.4f}")
        if r["mean_rho"] > best_rho:
            best_rho = r["mean_rho"]
            best_layer = r["layer"]
    print(f"\n  Best: L{best_layer} (ρ={best_rho:.4f})")
    return results


def experiment_E3(data):
    """E3: Regularization — fewer epochs + higher dropout."""
    print(f"\n{'='*60}")
    print(f"  E3: Regularization (epochs=20, dropout=0.5) on last layer")
    print(f"{'='*60}")

    last_layer = data["n_layers"] - 1

    def prepare_pair(data, pair):
        idx_a = data["hash_to_idx"][pair["hash_a"]]
        idx_b = data["hash_to_idx"][pair["hash_b"]]
        raw_a = get_raw_sequence(data, idx_a)
        raw_b = get_raw_sequence(data, idx_b)
        return {
            "hs_a": torch.from_numpy(raw_a).unsqueeze(0).float(),
            "hs_b": torch.from_numpy(raw_b).unsqueeze(0).float(),
            "label": pair["ccl_similarity"],
            "length_ratio": pair["length_ratio"],
        }

    def make_probe():
        return AttentiveProbe(data["hidden_dim"], n_queries=4, intermediate_dim=32, dropout=0.5)

    return run_cv(data, make_probe, prepare_pair, n_folds=5, epochs=20, label="E3_RegHigh")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, required=True, help="b2_gemma4_extracted.npz")
    parser.add_argument("--experiment", type=str, default="all", choices=["all", "E1", "E2", "E3"])
    parser.add_argument("--pca-dim", type=int, default=768)
    parser.add_argument("--output", type=str, default="b2_gemma4_followup_results.json")
    args = parser.parse_args()

    print("Loading extracted data...")
    data = load_extracted(args.data)
    print(f"  Pairs: {len(data['pair_keys'])}")
    print(f"  Unique snippets: {len(data['hash_to_idx'])}")
    print(f"  Layers: {data['n_layers']}, hidden_dim: {data['hidden_dim']}")
    print(f"  Mean-pool shape: {data['meanpool'].shape}")
    print(f"  Raw last-layer: {data['raw_last'].shape}")

    all_results = {}

    if args.experiment in ("all", "E1"):
        all_results["E1"] = experiment_E1(data, pca_dim=args.pca_dim)

    if args.experiment in ("all", "E2"):
        all_results["E2"] = experiment_E2(data)

    if args.experiment in ("all", "E3"):
        all_results["E3"] = experiment_E3(data)

    # Save results
    print(f"\n--- Saving to {args.output} ---")
    with open(args.output, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print("Done.")


if __name__ == "__main__":
    main()
