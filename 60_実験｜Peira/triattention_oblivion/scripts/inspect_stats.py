#!/usr/bin/env python3
"""Gate 1 準備: TriAttention calibration stats (.pt) の構造可視化。

stats ファイルに保存された Q/K 周波数統計を読み込み、
- 各 head の Q 平均複素ベクトルの性質 (Mean Resultant Length = R_h)
- 層ごとの R_h 分布 (← 忘却論的に重要: 二峰性の有無)
- 周波数ドメインでの Q 集中パターン
を可視化する。

CPU 専用。GPU 不要。既存の .pt ファイルを読むだけ。

Usage:
    python inspect_stats.py --stats path/to/qwen3_8b.pt --output-dir ./plots/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import torch
import numpy as np

# --- plotting ---
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    import matplotlib.cm as cm
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


def load_stats(stats_path: Path) -> Tuple[dict, Dict[Tuple[int, int], dict]]:
    """Load a TriAttention .pt stats file and return (metadata, per_head_stats)."""
    payload = torch.load(stats_path, map_location="cpu", weights_only=False)
    metadata = payload["metadata"]
    stats_raw = payload["stats"]

    per_head: Dict[Tuple[int, int], dict] = {}
    for (layer, head) in metadata["sampled_heads"]:
        key = f"layer{layer:02d}_head{head:02d}"
        entry = stats_raw.get(key)
        if entry is None:
            continue
        q_mean_complex = torch.complex(
            entry["q_mean_real"].float(),
            entry["q_mean_imag"].float(),
        )
        q_abs_mean = entry["q_abs_mean"].float()
        per_head[(layer, head)] = {
            "q_mean_complex": q_mean_complex,
            "q_abs_mean": q_abs_mean,
        }
    return metadata, per_head


def compute_mean_resultant_length(q_mean_complex: torch.Tensor, q_abs_mean: torch.Tensor) -> float:
    """R_h = |<q>| / <|q|> — Mean Resultant Length per head.

    R_h ≈ 1: Q ベクトルが周波数ドメインで強く方向集中 → trig score が効く
    R_h ≈ 0: Q ベクトルが散逸 → trig score の寄与小

    忘却論的意味: R_h は距離ポテンシャル V_h(Δ) の effective amplitude。
    R_h が高い head ほど TriAttention の圧縮に「適した」head。
    """
    q_mean_abs = q_mean_complex.abs()  # [freq_count]
    # R_h = sum(|<q_f>|) / sum(<|q_f|>) averaged over frequencies
    numerator = q_mean_abs.sum().item()
    denominator = q_abs_mean.sum().item()
    if denominator < 1e-12:
        return 0.0
    return numerator / denominator


def compute_per_freq_concentration(q_mean_complex: torch.Tensor, q_abs_mean: torch.Tensor) -> np.ndarray:
    """各周波数ビンの concentration ratio: |<q_f>| / <|q_f|>."""
    q_mean_abs = q_mean_complex.abs()
    ratio = q_mean_abs / q_abs_mean.clamp(min=1e-12)
    return ratio.numpy()


def plot_rh_by_layer(
    per_head: Dict[Tuple[int, int], dict],
    output_dir: Path,
    model_name: str,
) -> None:
    """層ごとの R_h 分布を箱ひげ図で可視化。"""
    if not HAS_MPL:
        print("[warn] matplotlib not available, skipping plots", file=sys.stderr)
        return

    # Collect R_h per layer
    layer_rh: Dict[int, List[float]] = {}
    for (layer, head), stats in per_head.items():
        rh = compute_mean_resultant_length(stats["q_mean_complex"], stats["q_abs_mean"])
        layer_rh.setdefault(layer, []).append(rh)

    layers = sorted(layer_rh.keys())
    data = [layer_rh[l] for l in layers]

    fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={"height_ratios": [3, 1]})

    # --- Boxplot ---
    ax1 = axes[0]
    bp = ax1.boxplot(data, positions=layers, widths=0.6, patch_artist=True,
                     showmeans=True, meanprops=dict(marker='D', markeredgecolor='red', markerfacecolor='red', markersize=4))
    for patch in bp["boxes"]:
        patch.set_facecolor("#4C72B0")
        patch.set_alpha(0.7)
    ax1.set_xlabel("Layer Index")
    ax1.set_ylabel("R_h (Mean Resultant Length)")
    ax1.set_title(f"TriAttention Q Directional Concentration per Layer — {model_name}")
    ax1.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label="R_h = 0.5")
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)

    # --- Layer mean heatmap ---
    ax2 = axes[1]
    means = [np.mean(layer_rh[l]) for l in layers]
    ax2.bar(layers, means, color=[cm.viridis(m) for m in means], edgecolor='none')
    ax2.set_xlabel("Layer Index")
    ax2.set_ylabel("Mean R_h")
    ax2.set_title("Layer-wise Mean R_h")
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    out = output_dir / "rh_by_layer.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out}", file=sys.stderr)


def plot_rh_heatmap(
    per_head: Dict[Tuple[int, int], dict],
    output_dir: Path,
    model_name: str,
) -> None:
    """全 head の R_h を layer × head のヒートマップで表示。"""
    if not HAS_MPL:
        return

    all_layers = sorted(set(l for l, _ in per_head.keys()))
    all_heads = sorted(set(h for _, h in per_head.keys()))
    n_layers = max(all_layers) + 1
    n_heads = max(all_heads) + 1

    grid = np.full((n_layers, n_heads), np.nan)
    for (layer, head), stats in per_head.items():
        rh = compute_mean_resultant_length(stats["q_mean_complex"], stats["q_abs_mean"])
        grid[layer, head] = rh

    fig, ax = plt.subplots(figsize=(max(12, n_heads * 0.3), max(8, n_layers * 0.2)))
    im = ax.imshow(grid, aspect="auto", cmap="viridis", interpolation="nearest",
                   norm=Normalize(vmin=0, vmax=1))
    ax.set_xlabel("Head Index")
    ax.set_ylabel("Layer Index")
    ax.set_title(f"R_h Heatmap (Layer × Head) — {model_name}")
    plt.colorbar(im, ax=ax, label="R_h")
    plt.tight_layout()
    out = output_dir / "rh_heatmap.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out}", file=sys.stderr)


def plot_freq_concentration(
    per_head: Dict[Tuple[int, int], dict],
    output_dir: Path,
    model_name: str,
    sample_layers: List[int] | None = None,
) -> None:
    """選択した層の周波数ビンごとの concentration を可視化。"""
    if not HAS_MPL:
        return

    all_layers = sorted(set(l for l, _ in per_head.keys()))
    if sample_layers is None:
        # Early, middle, late layers
        n = len(all_layers)
        sample_layers = [all_layers[0], all_layers[n // 4], all_layers[n // 2],
                         all_layers[3 * n // 4], all_layers[-1]]

    fig, axes = plt.subplots(len(sample_layers), 1, figsize=(14, 3 * len(sample_layers)))
    if len(sample_layers) == 1:
        axes = [axes]

    for ax, layer_idx in zip(axes, sample_layers):
        heads_in_layer = [(l, h) for (l, h) in per_head.keys() if l == layer_idx]
        if not heads_in_layer:
            continue
        for (l, h) in sorted(heads_in_layer):
            conc = compute_per_freq_concentration(
                per_head[(l, h)]["q_mean_complex"],
                per_head[(l, h)]["q_abs_mean"],
            )
            ax.plot(conc, alpha=0.3, linewidth=0.5)
        # Mean
        all_conc = np.stack([
            compute_per_freq_concentration(per_head[(l, h)]["q_mean_complex"], per_head[(l, h)]["q_abs_mean"])
            for (l, h) in sorted(heads_in_layer)
        ])
        ax.plot(all_conc.mean(axis=0), color="red", linewidth=2, label="Layer mean")
        ax.set_title(f"Layer {layer_idx}")
        ax.set_xlabel("Frequency bin")
        ax.set_ylabel("|⟨q_f⟩| / ⟨|q_f|⟩")
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

    fig.suptitle(f"Per-Frequency Q Concentration — {model_name}", fontsize=14)
    plt.tight_layout()
    out = output_dir / "freq_concentration.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out}", file=sys.stderr)


def print_summary(metadata: dict, per_head: Dict[Tuple[int, int], dict]) -> None:
    """テキストサマリーを stdout に出力。"""
    print("=" * 60)
    print("TriAttention Stats Summary")
    print("=" * 60)
    print(f"  head_dim:    {metadata.get('head_dim', '?')}")
    print(f"  rope_style:  {metadata.get('rope_style', '?')}")
    print(f"  rope_type:   {metadata.get('rope_type', '?')}")
    print(f"  dtype:       {metadata.get('dtype', '?')}")
    print(f"  num_heads:   {len(per_head)}")

    all_rh = []
    for (layer, head), stats in sorted(per_head.items()):
        rh = compute_mean_resultant_length(stats["q_mean_complex"], stats["q_abs_mean"])
        all_rh.append(rh)

    rh_arr = np.array(all_rh)
    print(f"\n  R_h statistics:")
    print(f"    mean:   {rh_arr.mean():.4f}")
    print(f"    std:    {rh_arr.std():.4f}")
    print(f"    min:    {rh_arr.min():.4f}")
    print(f"    max:    {rh_arr.max():.4f}")
    print(f"    median: {np.median(rh_arr):.4f}")

    # Bimodality check (Hartigan's dip test proxy: coefficient of bimodality)
    n = len(rh_arr)
    if n > 3:
        skew = float(((rh_arr - rh_arr.mean()) ** 3).mean() / (rh_arr.std() ** 3 + 1e-12))
        kurt = float(((rh_arr - rh_arr.mean()) ** 4).mean() / (rh_arr.std() ** 4 + 1e-12)) - 3
        bc = (skew ** 2 + 1) / (kurt + 3 * (n - 1) ** 2 / ((n - 2) * (n - 3)) + 1e-12)
        print(f"\n  Bimodality coefficient: {bc:.4f}")
        print(f"    (BC > 5/9 ≈ 0.556 suggests bimodal distribution)")
        if bc > 5 / 9:
            print(f"    → R_h 分布に二峰性の可能性あり (忘却場の非一様性)")
        else:
            print(f"    → R_h 分布は概ね単峰 (均一な忘却場)")

    # Top/bottom heads
    sorted_heads = sorted(per_head.items(), key=lambda x: compute_mean_resultant_length(x[1]["q_mean_complex"], x[1]["q_abs_mean"]))
    print(f"\n  Bottom 5 R_h heads (weakest directional concentration):")
    for (l, h), stats in sorted_heads[:5]:
        rh = compute_mean_resultant_length(stats["q_mean_complex"], stats["q_abs_mean"])
        print(f"    layer={l:2d} head={h:2d}  R_h={rh:.4f}")

    print(f"\n  Top 5 R_h heads (strongest directional concentration):")
    for (l, h), stats in sorted_heads[-5:]:
        rh = compute_mean_resultant_length(stats["q_mean_complex"], stats["q_abs_mean"])
        print(f"    layer={l:2d} head={h:2d}  R_h={rh:.4f}")

    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect TriAttention calibration stats.")
    parser.add_argument("--stats", required=True, help="Path to .pt stats file")
    parser.add_argument("--output-dir", default="./plots", help="Output directory for plots")
    parser.add_argument("--model-name", default=None, help="Model name for plot titles")
    args = parser.parse_args()

    stats_path = Path(args.stats)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model_name = args.model_name or stats_path.stem

    print(f"Loading stats: {stats_path}", file=sys.stderr)
    metadata, per_head = load_stats(stats_path)

    print_summary(metadata, per_head)

    if HAS_MPL:
        print("\nGenerating plots...", file=sys.stderr)
        plot_rh_by_layer(per_head, output_dir, model_name)
        plot_rh_heatmap(per_head, output_dir, model_name)
        plot_freq_concentration(per_head, output_dir, model_name)
        print("Done.", file=sys.stderr)
    else:
        print("\n[warn] matplotlib not installed. Install with: pip install matplotlib", file=sys.stderr)


if __name__ == "__main__":
    main()
