#!/usr/bin/env python3
"""p3b_figure_data.json から論文用 Figure 1-4 を描画する。"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


EXPERIMENTS_DIR = Path(__file__).parent
LETHE_DIR = EXPERIMENTS_DIR.parent
INPUT = EXPERIMENTS_DIR / "p3b_figure_data.json"
OUTPUT_DIR = LETHE_DIR / "paper_figures"

BANDS = ["B1", "B2", "B3", "B4", "B5"]
FAMILY_LABELS = {
    "cosine_49d": "49d cosine",
    "ccl_string": "CCL string distance",
    "d_lethe_candidate": "d_lethe candidate",
}
FAMILY_COLORS = {
    "cosine_49d": "#1f77b4",
    "ccl_string": "#d62728",
    "d_lethe_candidate": "#2ca02c",
}
FAILURE_ORDER = [
    "aligned",
    "mid_band_blur",
    "near_band_false_negative",
    "far_band_false_positive",
]
FAILURE_COLORS = {
    "aligned": "#9aa0a6",
    "mid_band_blur": "#f4b400",
    "near_band_false_negative": "#db4437",
    "far_band_false_positive": "#7e57c2",
}


def load_payload() -> dict:
    with open(INPUT, encoding="utf-8") as f:
        return json.load(f)


def style_axis(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.25)


def save_figure(fig, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_figure_1(payload: dict) -> Path:
    fig, ax = plt.subplots(figsize=(8, 4.8))
    values = [
        payload["band_mean_distances"]["cosine_49d"][band]
        for band in BANDS
    ]
    x = np.arange(len(BANDS))

    ax.plot(x, values, marker="o", linewidth=2.6, color=FAMILY_COLORS["cosine_49d"])
    ax.axvspan(0.85, 3.15, color="#f4b400", alpha=0.12)
    ax.text(2, max(values) * 0.94, "Middle regime", ha="center", va="top", fontsize=10)

    ax.set_xticks(x, BANDS)
    ax.set_ylim(0.0, max(values) * 1.18)
    ax.set_ylabel("Mean distance")
    ax.set_title("Figure 1. Middle-band collapse under 49d cosine")
    style_axis(ax)

    path = OUTPUT_DIR / "figure1_middle_band_collapse.png"
    save_figure(fig, path)
    return path


def plot_figure_2(payload: dict) -> Path:
    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    families = list(FAMILY_LABELS.keys())
    x = np.arange(len(families))
    bottoms = np.zeros(len(families))

    for failure in FAILURE_ORDER:
        values = [
            payload["failure_counts"].get(family, {}).get(failure, 0)
            for family in families
        ]
        ax.bar(
            x,
            values,
            bottom=bottoms,
            color=FAILURE_COLORS[failure],
            label=failure,
            width=0.62,
        )
        bottoms += np.asarray(values)

    ax.set_xticks(x, [FAMILY_LABELS[f] for f in families], rotation=0)
    ax.set_ylabel("Pair count")
    ax.set_title("Figure 2. Failure geometry by distance family")
    style_axis(ax)
    ax.legend(frameon=False, ncol=2, fontsize=9)

    path = OUTPUT_DIR / "figure2_failure_geometry.png"
    save_figure(fig, path)
    return path


def plot_figure_3(payload: dict) -> Path:
    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    x = np.arange(len(BANDS))

    for family in FAMILY_LABELS:
        values = [
            payload["band_mean_distances"][family][band]
            for band in BANDS
        ]
        ax.plot(
            x,
            values,
            marker="o",
            linewidth=2.4,
            label=FAMILY_LABELS[family],
            color=FAMILY_COLORS[family],
        )

    ax.set_xticks(x, BANDS)
    ax.set_ylabel("Mean distance")
    ax.set_title("Figure 3. Distance-family tradeoff across canonical bands")
    style_axis(ax)
    ax.legend(frameon=False)

    path = OUTPUT_DIR / "figure3_distance_family_tradeoff.png"
    save_figure(fig, path)
    return path


def wrap_cell(text: str, width: int = 20) -> str:
    return textwrap.fill(text, width=width, break_long_words=True, break_on_hyphens=False)


def plot_figure_4(payload: dict) -> Path:
    fig, ax = plt.subplots(figsize=(13.8, 4.2))
    ax.axis("off")

    rows = []
    for family in FAMILY_LABELS:
        example = payload["representative_examples"][family]
        rows.append([
            FAMILY_LABELS[family],
            example["failure_mode"],
            example["band_id"],
            wrap_cell(example["func_a"]),
            wrap_cell(example["func_b"]),
            f"{example['distance_value']:.4f}",
        ])

    col_labels = [
        "Family",
        "Failure mode",
        "Band",
        "func_a",
        "func_b",
        "Distance",
    ]

    table = ax.table(
        cellText=rows,
        colLabels=col_labels,
        cellLoc="left",
        colLoc="left",
        loc="center",
        colWidths=[0.17, 0.17, 0.07, 0.23, 0.23, 0.10],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.8)
    table.scale(1, 2.0)

    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#eceff1")
            cell.set_text_props(weight="bold")
        elif col == 0:
            family = list(FAMILY_LABELS.keys())[row - 1]
            cell.set_facecolor(FAMILY_COLORS[family] + "22")

    fig.suptitle("Figure 4. Representative failure pairs", fontsize=13, y=0.97)
    path = OUTPUT_DIR / "figure4_representative_pairs.png"
    save_figure(fig, path)
    return path


def main() -> None:
    payload = load_payload()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    outputs = [
        plot_figure_1(payload),
        plot_figure_2(payload),
        plot_figure_3(payload),
        plot_figure_4(payload),
    ]

    for output in outputs:
        print(f"saved: {output}")


if __name__ == "__main__":
    main()
