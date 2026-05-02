#!/usr/bin/env python3
"""B2 Gemma4 フォローアップ: キャッシュから前処理済みデータを抽出。

VM (34.29.169.168) で実行。GPU 不要、CPU + disk I/O のみ。
出力: b2_gemma4_extracted.npz (~200MB) をローカルに転送して probe 実験。

Usage:
    python3 b2_gemma4_extract.py --dataset dataset_v3.json --cache-dir .hidden_cache/gemma4
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np


def source_hash(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()[:16]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="dataset_v3.json")
    parser.add_argument("--cache-dir", type=str, default=".hidden_cache/gemma4")
    parser.add_argument("--output", type=str, default="b2_gemma4_extracted.npz")
    args = parser.parse_args()

    cache_dir = Path(args.cache_dir)
    if not cache_dir.exists():
        print(f"ERROR: cache dir not found: {cache_dir}", file=sys.stderr)
        sys.exit(1)

    # Load dataset
    with open(args.dataset) as f:
        raw = json.load(f)
    pairs = raw["pairs"] if isinstance(raw, dict) and "pairs" in raw else raw
    print(f"Pairs: {len(pairs)}")

    # Collect unique source codes
    sources = {}  # hash -> source
    pair_keys = []  # (hash_a, hash_b, label, pair_type)
    for p in pairs:
        ha = source_hash(p["func_a_source"])
        hb = source_hash(p["func_b_source"])
        sources[ha] = p["func_a_source"]
        sources[hb] = p["func_b_source"]
        pair_keys.append({
            "hash_a": ha,
            "hash_b": hb,
            "ccl_similarity": float(p.get("ccl_similarity", 0)),
            "is_positive": p.get("is_positive", False) if isinstance(p.get("is_positive"), bool) else str(p.get("is_positive", "False")).lower() == "true",
            "pair_type": p.get("pair_type", "unknown"),
            "length_ratio": float(p.get("length_ratio", 1.0)),
        })

    unique_hashes = sorted(sources.keys())
    print(f"Unique code snippets: {len(unique_hashes)}")

    # Check cache coverage
    missing = [h for h in unique_hashes if not (cache_dir / f"{h}.npz").exists()]
    if missing:
        print(f"WARNING: {len(missing)} snippets missing from cache")
        print(f"  First 5: {missing[:5]}")

    # Detect n_layers from first file
    sample_file = cache_dir / f"{unique_hashes[0]}.npz"
    sample = np.load(sample_file)
    n_layers = len(sample.files)
    hidden_dim = sample["layer_0"].shape[1]
    print(f"Layers: {n_layers}, hidden_dim: {hidden_dim}")
    sample.close()

    # Extract: mean-pooled per layer (for E2 layer scan)
    # Shape: (n_snippets, n_layers, hidden_dim)
    print("\n--- Extracting mean-pooled vectors (all layers) ---")
    hash_to_idx = {h: i for i, h in enumerate(unique_hashes)}
    meanpool = np.zeros((len(unique_hashes), n_layers, hidden_dim), dtype=np.float32)

    for i, h in enumerate(unique_hashes):
        cache_file = cache_dir / f"{h}.npz"
        if not cache_file.exists():
            continue
        data = np.load(cache_file)
        for layer_idx in range(n_layers):
            key = f"layer_{layer_idx}"
            if key in data:
                meanpool[i, layer_idx] = data[key].mean(axis=0)
        data.close()
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(unique_hashes)}")

    print(f"  Mean-pooled shape: {meanpool.shape}")
    print(f"  Size: {meanpool.nbytes / 1e6:.0f} MB")

    # Extract: raw last-layer sequences (for E1 Attentive + PCA)
    # Variable length → store as list of arrays, packed with offsets
    print("\n--- Extracting raw last-layer sequences ---")
    last_layer_idx = n_layers - 1
    all_tokens = []
    offsets = [0]

    for i, h in enumerate(unique_hashes):
        cache_file = cache_dir / f"{h}.npz"
        if not cache_file.exists():
            # Pad with zeros
            all_tokens.append(np.zeros((1, hidden_dim), dtype=np.float32))
            offsets.append(offsets[-1] + 1)
            continue
        data = np.load(cache_file)
        tokens = data[f"layer_{last_layer_idx}"]  # (seq_len, hidden_dim)
        all_tokens.append(tokens.astype(np.float32))
        offsets.append(offsets[-1] + tokens.shape[0])
        data.close()
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(unique_hashes)}")

    raw_last = np.concatenate(all_tokens, axis=0)  # (total_tokens, hidden_dim)
    offsets = np.array(offsets, dtype=np.int64)
    print(f"  Raw last-layer: {raw_last.shape} ({raw_last.nbytes / 1e6:.0f} MB)")
    print(f"  Offsets: {offsets.shape}")

    # Save everything
    print(f"\n--- Saving to {args.output} ---")
    np.savez_compressed(
        args.output,
        # Metadata
        unique_hashes=np.array(unique_hashes, dtype="U16"),
        pair_keys_json=json.dumps(pair_keys),
        n_layers=np.array(n_layers),
        hidden_dim=np.array(hidden_dim),
        # E2: mean-pooled (n_snippets, n_layers, hidden_dim)
        meanpool=meanpool,
        # E1: raw last-layer (total_tokens, hidden_dim) + offsets
        raw_last_layer=raw_last,
        raw_last_offsets=offsets,
    )

    out_size = Path(args.output).stat().st_size / 1e6
    print(f"  Output size: {out_size:.0f} MB")
    print("Done.")


if __name__ == "__main__":
    main()
