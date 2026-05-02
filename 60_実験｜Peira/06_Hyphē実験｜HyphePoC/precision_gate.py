"""Precision Gate — CacheBlend HKVD 原理の Hyphē 同型対応。

チャンクの precision 値に基づいて 3段ゲートを適用し、
コンテキスト処理戦略 (reuse / selective / full) を決定する。

CacheBlend との対応 (同型であって同一ではない):
  KV deviation ≅ 1 - precision (cross-attention 不足度)
  HKVD tokens ≅ low-precision chunks (集中的処理が必要)
  r* = 15% ≅ NOT 直接転用 (数値は Hyphē 実験で校正)

設計根拠:
  - CacheBlend (Yao et al., 2024): §3.3 Selective KV Recomputation
  - Hyphē Implementation Plan: §Hyphē × CacheBlend 設計思想
  - 閾値は実験的に決定 (Otsu / k-means / percentile)

PROOF: implementation_plan.md §Precision Gate + §CacheBlend 設計思想
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hyphe_chunker import Chunk, PrecisionResult


# ── 閾値設定 ────────────────────────────────────────────────────────
# 実験的に決定 (2026-03-15):
#   5セッション × 64チャンク, ensemble_weight=0.5
#   3手法コンセンサス (Otsu 3class / k-means / Percentile P25/P75)
#   ゲート分布: high 32.8% / mid 45.3% / low 21.9%
DEFAULT_THETA_HIGH = 0.67
DEFAULT_THETA_LOW = 0.34


@dataclass
class GateConfig:
    """精度ゲートの設定。

    theta_high: この値以上 → "high" (KV cache reuse)
    theta_low: この値未満 → "low" (full recomputation)
    theta_low <= x < theta_high → "mid" (selective recomputation)
    """
    theta_high: float = DEFAULT_THETA_HIGH
    theta_low: float = DEFAULT_THETA_LOW

    def __post_init__(self) -> None:
        if self.theta_low >= self.theta_high:
            raise ValueError(
                f"theta_low ({self.theta_low}) は "
                f"theta_high ({self.theta_high}) より小さい必要がある"
            )
        if not (0.0 <= self.theta_low <= 1.0):
            raise ValueError(f"theta_low は [0, 1] 範囲: {self.theta_low}")
        if not (0.0 <= self.theta_high <= 1.0):
            raise ValueError(f"theta_high は [0, 1] 範囲: {self.theta_high}")


# ── ゲート判定 ────────────────────────────────────────────────────────


def classify_gate(precision: float, config: GateConfig | None = None) -> str:
    """precision 値からゲートラベルを判定する。

    Args:
        precision: 統合 precision 値 [0, 1]
        config: ゲート設定 (None の場合はデフォルト値)

    Returns:
        "high" / "mid" / "low"
    """
    if config is None:
        config = GateConfig()

    if precision >= config.theta_high:
        return "high"
    elif precision < config.theta_low:
        return "low"
    else:
        return "mid"


def apply_gate(chunks: list["Chunk"], config: GateConfig | None = None) -> list["Chunk"]:
    """チャンクリストの precision_result に gate_label を設定する。

    各チャンクの precision_result.gate_label を実際の閾値に基づいて更新。
    precision_result が None のチャンクはスキップ。

    Args:
        chunks: calculate_chunk_metrics() で処理済みのチャンクリスト
        config: ゲート設定 (None の場合はデフォルト値)

    Returns:
        ゲートが適用されたチャンクリスト (in-place 変更)
    """
    if config is None:
        config = GateConfig()

    for chunk in chunks:
        if chunk.precision_result is not None:
            chunk.precision_result.gate_label = classify_gate(
                chunk.precision_result.integrated, config
            )

    return chunks


def gate_summary(chunks: list["Chunk"]) -> dict:
    """ゲート適用後のサマリ統計を返す。

    Args:
        chunks: apply_gate() 適用済みのチャンクリスト

    Returns:
        dict: ゲートラベルの分布と再計算率の統計
          - counts: {high: N, mid: N, low: N}
          - ratios: {high: %, mid: %, low: %}
          - mean_recompute: 平均 recompute_ratio
          - min_recompute: 最小 recompute_ratio
          - max_recompute: 最大 recompute_ratio
    """
    counts = {"high": 0, "mid": 0, "low": 0}
    recompute_ratios: list[float] = []

    for chunk in chunks:
        if chunk.precision_result is not None:
            label = chunk.precision_result.gate_label
            if label in counts:
                counts[label] += 1
            recompute_ratios.append(chunk.precision_result.recompute_ratio)

    total = sum(counts.values())
    ratios = {k: v / total if total > 0 else 0.0 for k, v in counts.items()}

    return {
        "counts": counts,
        "ratios": {k: round(v, 4) for k, v in ratios.items()},
        "mean_recompute": round(sum(recompute_ratios) / len(recompute_ratios), 4) if recompute_ratios else 0.0,
        "min_recompute": round(min(recompute_ratios), 4) if recompute_ratios else 0.0,
        "max_recompute": round(max(recompute_ratios), 4) if recompute_ratios else 0.0,
        "total_chunks": total,
    }
