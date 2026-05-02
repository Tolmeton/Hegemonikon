#!/usr/bin/env python3
"""S-009 Gate 1: Gemma4 / TriAttention feasibility profiler.

PURPOSE:
  TriAttention の前提である pre-RoPE Q/K 幾何を、Gemma4 の layer type
  (sliding vs full) ごとに機械的に点検する。

  1. config-only mode:
     - raw config.json から Gemma4 の text_config を読み、layer_types,
       rope parameters, head geometry を JSON 化
     - 現環境の Transformers が Gemma4 runtime を解釈可能かも併記

  2. runtime mode:
     - Gemma4 text decoder をロード
     - 各 layer 入力 hidden state に q_proj / k_proj を適用
     - pre-RoPE rotary 部分の head-wise MRL を算出
     - layer type 別集計を出力

NOTE:
  現在の Lethe 実験環境では Transformers 5.3.0 のため Gemma4 runtime は
  失敗する。config-only mode はその制約下でも動く。

Usage:
  python triattention_gemma4_profile.py --config-only --model gemma4
  python triattention_gemma4_profile.py --model gemma4 --max-samples 8 --max-length 512
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np

from structural_probe import MODEL_CONFIGS, load_model, _load_raw_hf_config


DEFAULT_SNIPPETS = [
    "def add(a, b):\n    return a + b\n",
    "def fib(n):\n    if n <= 1:\n        return n\n    return fib(n - 1) + fib(n - 2)\n",
]


def resolve_repo_id(model_key: str, repo_id: str | None) -> str:
    if repo_id:
        return repo_id
    if model_key in MODEL_CONFIGS:
        return MODEL_CONFIGS[model_key]["hf_name"]
    return model_key


def load_text_config(repo_id: str) -> tuple[dict, dict]:
    raw_config = _load_raw_hf_config(repo_id)
    text_config = raw_config.get("text_config")
    if not isinstance(text_config, dict):
        raise ValueError(f"{repo_id} の config.json に text_config がありません")
    return raw_config, text_config


def detect_runtime_support(repo_id: str) -> tuple[bool, str | None]:
    try:
        from transformers import AutoConfig  # type: ignore

        AutoConfig.from_pretrained(repo_id)
        return True, None
    except Exception as exc:
        return False, str(exc)


def summarize_config(repo_id: str, raw_config: dict, text_config: dict) -> dict:
    layer_types = text_config.get("layer_types") or []
    layer_type_counts = Counter(layer_types)
    layer_type_indices = {
        layer_type: [i for i, value in enumerate(layer_types) if value == layer_type]
        for layer_type in sorted(layer_type_counts)
    }
    rope_parameters = text_config.get("rope_parameters") or {}
    runtime_supported, runtime_error = detect_runtime_support(repo_id)

    return {
        "repo_id": repo_id,
        "config_model_type": raw_config.get("model_type"),
        "checkpoint_transformers_version": raw_config.get("transformers_version"),
        "runtime_supported": runtime_supported,
        "runtime_error": runtime_error,
        "text_config": {
            "num_hidden_layers": text_config.get("num_hidden_layers"),
            "num_attention_heads": text_config.get("num_attention_heads"),
            "num_key_value_heads": text_config.get("num_key_value_heads"),
            "num_global_key_value_heads": text_config.get("num_global_key_value_heads"),
            "head_dim": text_config.get("head_dim"),
            "global_head_dim": text_config.get("global_head_dim"),
            "hidden_size": text_config.get("hidden_size"),
            "sliding_window": text_config.get("sliding_window"),
            "num_kv_shared_layers": text_config.get("num_kv_shared_layers"),
            "attention_k_eq_v": text_config.get("attention_k_eq_v"),
        },
        "layer_type_counts": dict(layer_type_counts),
        "layer_type_indices": layer_type_indices,
        "rope_parameters": rope_parameters,
    }


def load_sample_texts(
    dataset_path: Path,
    sample_text_file: Path | None,
    max_samples: int,
) -> list[str]:
    if sample_text_file is not None:
        raw_text = sample_text_file.read_text(encoding="utf-8")
        chunks = [chunk.strip() for chunk in raw_text.split("\n\n") if chunk.strip()]
        if len(chunks) <= 1:
            chunks = [line.strip() for line in raw_text.splitlines() if line.strip()]
        return chunks[:max_samples] or DEFAULT_SNIPPETS[:max_samples]

    if dataset_path.exists():
        data = json.loads(dataset_path.read_text(encoding="utf-8"))
        samples: list[str] = []
        seen: set[str] = set()
        for pair in data.get("pairs", []):
            for key in ("func_a_source", "func_b_source"):
                value = pair.get(key)
                if isinstance(value, str) and value not in seen:
                    seen.add(value)
                    samples.append(value)
                if len(samples) >= max_samples:
                    return samples
        if samples:
            return samples[:max_samples]

    return DEFAULT_SNIPPETS[:max_samples]


def resolve_layer_modules(model) -> list:
    if hasattr(model, "layers"):
        return list(model.layers)
    if hasattr(model, "model") and hasattr(model.model, "layers"):
        return list(model.model.layers)
    raise AttributeError("language model から layers を解決できません")


def resolve_attention_module(layer):
    for attr in ("self_attn", "attn", "attention"):
        if hasattr(layer, attr):
            return getattr(layer, attr)
    raise AttributeError(f"{type(layer).__name__} から attention module を解決できません")


def reshape_heads(projected, n_heads: int):
    import torch

    if projected.ndim != 3:
        raise ValueError(f"projection tensor rank が不正です: {projected.shape}")

    batch, seq_len, total_dim = projected.shape
    if total_dim % n_heads != 0:
        raise ValueError(f"head reshape 不可: total_dim={total_dim}, n_heads={n_heads}")

    head_dim = total_dim // n_heads
    return projected.view(batch, seq_len, n_heads, head_dim)


def compute_rotary_head_mrl(projected, attention_mask, rotary_factor: float) -> dict:
    import torch

    if projected.ndim != 4:
        raise ValueError(f"expected (batch, seq, heads, head_dim), got {projected.shape}")

    head_dim = projected.shape[-1]
    rotary_dim = int(head_dim * rotary_factor)
    rotary_dim -= rotary_dim % 2
    rotary_dim = max(0, min(rotary_dim, head_dim))

    if rotary_dim < 2:
        return {
            "head_dim": int(head_dim),
            "rotary_dim": int(rotary_dim),
            "nonrotary_dim": int(head_dim - rotary_dim),
            "mean": None,
            "std": None,
            "high_ratio": None,
            "per_head": [],
            "nonrotary_norm_share": None,
        }

    rotary = projected[..., :rotary_dim]
    nonrotary = projected[..., rotary_dim:]

    flat_mask = attention_mask.reshape(-1).bool()
    rotary_pairs = rotary.reshape(-1, rotary.shape[2], rotary_dim // 2, 2)
    rotary_pairs = rotary_pairs[flat_mask]

    if rotary_pairs.numel() == 0:
        return {
            "head_dim": int(head_dim),
            "rotary_dim": int(rotary_dim),
            "nonrotary_dim": int(head_dim - rotary_dim),
            "mean": None,
            "std": None,
            "high_ratio": None,
            "per_head": [],
            "nonrotary_norm_share": None,
        }

    pair_norms = torch.linalg.norm(rotary_pairs, dim=-1)
    mean_vec = rotary_pairs.mean(dim=0)
    mean_norm = pair_norms.mean(dim=0).clamp_min(1e-12)
    frequency_mrl = torch.linalg.norm(mean_vec, dim=-1) / mean_norm
    head_mrl = frequency_mrl.mean(dim=-1)

    nonrotary_share = None
    if nonrotary.shape[-1] > 0:
        full_norm = torch.linalg.norm(projected, dim=-1).reshape(-1, projected.shape[2])[flat_mask]
        nonrotary_norm = torch.linalg.norm(nonrotary, dim=-1).reshape(-1, projected.shape[2])[flat_mask]
        full_norm = full_norm.clamp_min(1e-12)
        nonrotary_share = float((nonrotary_norm / full_norm).mean().item())

    head_values = head_mrl.detach().cpu().tolist()
    mean_value = float(head_mrl.mean().item())
    std_value = float(head_mrl.std(unbiased=False).item())
    high_ratio = float((head_mrl > 0.95).float().mean().item())

    return {
        "head_dim": int(head_dim),
        "rotary_dim": int(rotary_dim),
        "nonrotary_dim": int(head_dim - rotary_dim),
        "mean": mean_value,
        "std": std_value,
        "high_ratio": high_ratio,
        "per_head": head_values,
        "nonrotary_norm_share": nonrotary_share,
    }


def infer_head_count(attn_module, fallback: int, attr_names: Iterable[str]) -> int:
    for attr in attr_names:
        if hasattr(attn_module, attr):
            value = getattr(attn_module, attr)
            if isinstance(value, int) and value > 0:
                return value
    return fallback


def profile_runtime(
    model_key: str,
    repo_id: str,
    text_config: dict,
    dataset_path: Path,
    sample_text_file: Path | None,
    bits: int,
    max_samples: int,
    max_length: int,
) -> dict:
    import torch

    if model_key not in MODEL_CONFIGS:
        raise ValueError("runtime mode は MODEL_CONFIGS 登録済みモデルのみ対応します")

    samples = load_sample_texts(dataset_path, sample_text_file, max_samples)
    model, tokenizer, device, _ = load_model(model_key, bits=bits)

    inputs = tokenizer(
        samples,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_length,
    )
    inputs = {key: value.to(device) for key, value in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True, use_cache=False)

    hidden_states = outputs.hidden_states
    attention_mask = inputs["attention_mask"]
    layers = resolve_layer_modules(model)
    layer_types = text_config.get("layer_types") or []
    rope_parameters = text_config.get("rope_parameters") or {}
    default_num_heads = int(text_config.get("num_attention_heads") or 0)
    default_num_kv_heads = int(text_config.get("num_key_value_heads") or default_num_heads)

    per_layer = []
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for layer_idx, layer in enumerate(layers):
        layer_input = hidden_states[layer_idx]
        attn = resolve_attention_module(layer)
        layer_type = (
            layer_types[layer_idx]
            if layer_idx < len(layer_types)
            else "unknown"
        )
        rope_cfg = rope_parameters.get(layer_type, {})
        rotary_factor = float(rope_cfg.get("partial_rotary_factor", 1.0))

        q_heads = infer_head_count(attn, default_num_heads, ("num_heads", "num_attention_heads"))
        kv_fallback = text_config.get("num_global_key_value_heads")
        if layer_type != "full_attention" or kv_fallback is None:
            kv_fallback = default_num_kv_heads
        k_heads = infer_head_count(attn, int(kv_fallback or default_num_kv_heads), ("num_key_value_heads", "num_kv_heads"))

        with torch.no_grad():
            q = attn.q_proj(layer_input)
            k = attn.k_proj(layer_input)

        q = reshape_heads(q, q_heads)
        k = reshape_heads(k, k_heads)

        q_stats = compute_rotary_head_mrl(q, attention_mask, rotary_factor)
        k_stats = compute_rotary_head_mrl(k, attention_mask, rotary_factor)

        record = {
            "layer": layer_idx,
            "layer_type": layer_type,
            "rope_type": rope_cfg.get("rope_type"),
            "rope_theta": rope_cfg.get("rope_theta"),
            "partial_rotary_factor": rope_cfg.get("partial_rotary_factor", 1.0),
            "q_stats": q_stats,
            "k_stats": k_stats,
        }
        per_layer.append(record)

        for prefix, stats in (("q", q_stats), ("k", k_stats)):
            if stats["mean"] is not None:
                grouped[layer_type][f"{prefix}_mean"].append(stats["mean"])
                grouped[layer_type][f"{prefix}_high_ratio"].append(stats["high_ratio"])
                if stats["nonrotary_norm_share"] is not None:
                    grouped[layer_type][f"{prefix}_nonrotary_share"].append(stats["nonrotary_norm_share"])

    aggregates = {}
    for layer_type, values in grouped.items():
        aggregates[layer_type] = {}
        for key, series in values.items():
            aggregates[layer_type][key] = {
                "mean": float(np.mean(series)),
                "std": float(np.std(series)),
                "n_layers": len(series),
            }

    return {
        "samples_used": len(samples),
        "sample_preview": samples[:2],
        "max_length": max_length,
        "per_layer": per_layer,
        "aggregates": aggregates,
    }


def main():
    parser = argparse.ArgumentParser(description="Gemma4 / TriAttention Gate 1 profiler")
    parser.add_argument(
        "--model",
        type=str,
        default="gemma4",
        help="MODEL_CONFIGS のキー (gemma4, gemma4-31b) または repo id",
    )
    parser.add_argument(
        "--repo-id",
        type=str,
        default=None,
        help="raw config を読む HF repo id。未指定時は --model から推定",
    )
    parser.add_argument(
        "--config-only",
        action="store_true",
        help="raw config 解析のみ実行し、runtime profile をスキップ",
    )
    parser.add_argument(
        "--config-path",
        type=Path,
        default=None,
        help="ローカル config.json を直接読む場合のパス",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("dataset_v3.json"),
        help="サンプルコード抽出用 dataset JSON",
    )
    parser.add_argument(
        "--sample-text-file",
        type=Path,
        default=None,
        help="校正用の plain text / code サンプルファイル",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=8,
        help="runtime profile に使う最大サンプル数",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=512,
        help="各サンプルの最大トークン長",
    )
    parser.add_argument(
        "--bits",
        type=int,
        default=0,
        help="runtime mode の量子化ビット数 (0=モデル既定)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/triattention_gemma4_profile.json"),
        help="出力 JSON パス",
    )
    args = parser.parse_args()

    repo_id = resolve_repo_id(args.model, args.repo_id)
    if args.config_path is not None:
        raw_config = json.loads(args.config_path.read_text(encoding="utf-8"))
        text_config = raw_config.get("text_config")
        if not isinstance(text_config, dict):
            raise ValueError(f"{args.config_path} に text_config がありません")
    else:
        raw_config, text_config = load_text_config(repo_id)

    result = {
        "config_summary": summarize_config(repo_id, raw_config, text_config),
        "runtime_profile": None,
    }

    if not args.config_only:
        result["runtime_profile"] = profile_runtime(
            model_key=args.model,
            repo_id=repo_id,
            text_config=text_config,
            dataset_path=args.dataset,
            sample_text_file=args.sample_text_file,
            bits=args.bits,
            max_samples=args.max_samples,
            max_length=args.max_length,
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=== Gemma4 / TriAttention profile ===")
    print(f"repo_id: {repo_id}")
    print(f"output:  {args.output}")
    print(f"runtime supported: {result['config_summary']['runtime_supported']}")
    if args.config_only:
        print("mode: config-only")
    else:
        print("mode: runtime")


if __name__ == "__main__":
    main()
