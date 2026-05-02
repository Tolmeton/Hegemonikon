from __future__ import annotations
# PROOF: [L2/Phase3] <- hermeneus/src/subscribers/taxis_sub.py
# PURPOSE: X-series 統合 — 6族間の K₆ 張力計算 (v4.1 新略称対応)
"""
TaxisSubscriber — X-series (関係層) の統合判断

6 Series の Limit が全て Blackboard に充填されたとき、
score() が 1.0 に達して**自律的に発火**する。

VISION §5.5 の Dynamic Interleaving の具体例:
  - 6 Series が充填されるまで score=充填率 (0.0〜1.0)
  - 6/6 充填で score=1.0 → 他の全 Subscriber より先に発火

K₆ 完全グラフの 15 エッジ:
  C(6,2) = 15 ペアの張力を計算し、矛盾度 V を算出。
  V > 0.3 → 重み付け融合 (高張力ペアの解消優先)
  V ≤ 0.3 → 通常融合 (均等集約)

発火条件:
  - MACRO_START イベント
  - マクロ名に "ax" を含む
  - Blackboard の 6 Series Limit が全て充填されている

出力:
  @converge: 統合結論 + 矛盾度 V + 高張力ペア
"""

import logging
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Optional

import yaml

from ..activation import BaseSubscriber, ActivationPolicy
from ..event_bus import CognitionEvent, EventType

logger = logging.getLogger(__name__)

# 6族のキー (v4.1 新略称)
SERIES_KEYS = ["Tel", "Met", "Kri", "Dia", "Ore", "Chr"]

# K₆ の 15辺の張力重みを YAML から読込
# SOURCE: mekhane/taxis/k6_weights.yaml (taxis.md と数値重みの統合)
_K6_YAML_PATH = Path(__file__).resolve().parent.parent.parent.parent / "mekhane" / "taxis" / "k6_weights.yaml"


def _load_k6_weights(yaml_path: Path = _K6_YAML_PATH) -> dict[tuple[str, str], float]:
    """k6_weights.yaml から張力重みを読み込む。ファイルが存在しない場合はフォールバック値を返す。"""
    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        weights = {}
        for edge in data.get("edges", []):
            pair = tuple(edge["pair"])
            weights[pair] = edge["weight"]
        return weights
    except (FileNotFoundError, KeyError, TypeError) as e:
        logger.warning("k6_weights.yaml の読込に失敗。フォールバック値を使用: %s", e)
        # フォールバック: 全辺 0.3
        return {(a, b): 0.3 for a, b in combinations(SERIES_KEYS, 2)}


K6_TENSION_WEIGHTS = _load_k6_weights()


@dataclass
class TensionEdge:
    """K₆ の1エッジ (2 Series 間の張力)"""
    series_a: str
    series_b: str
    weight: float        # 構造的張力 (K6_TENSION_WEIGHTS)
    semantic_score: float # 意味的張力 (limit 文の類似度から)
    tension: float       # = weight × semantic_score


class TaxisSubscriber(BaseSubscriber):
    """X-series: 6 Series 間の K₆ 張力計算 + 統合

    VISION Phase 3: score() が Blackboard 状態で自律発火を判断する
    最も明確な具体例。
    """

    def __init__(self):
        super().__init__(
            name="taxis",
            policy=ActivationPolicy(
                event_types={EventType.MACRO_START},
                custom_predicate=self._is_ax_macro,
            ),
            fire_threshold=0.0,
        )

    @staticmethod
    def _is_ax_macro(event: CognitionEvent) -> bool:
        name = event.metadata.get("macro_name", "")
        return "ax" in name.lower()

    def score(self, event: CognitionEvent) -> float:
        """6 Series の充填率で自律発火を判断

        VISION §5.5 の核心:
          0/6 充填 → score=0.0 (発火しない)
          3/6 充填 → score=0.5 (まだ不十分)
          6/6 充填 → score=1.0 (自律発火！)
        """
        bb = getattr(event, 'blackboard', None)
        if not bb:
            return 0.0
        s = bb.series_fill_rate
        self._score_history.append(s)
        return s

    def handle(self, event: CognitionEvent) -> Optional[str]:
        """K₆ 完全グラフの張力計算 + 統合結論"""
        bb = getattr(event, 'blackboard', None)
        if not bb or bb.series_fill_rate < 1.0:
            return None  # 6 Series 未充填

        # ═══ K₆ 張力計算 ═══
        tensions = self._compute_k6_tensions(bb)
        V = self._compute_contradiction(tensions)

        # ═══ 統合結論 ═══
        lines = ["[X: 関係 (Taxis) — K₆ 張力分析]"]
        lines.append(f"  矛盾度 V = {V:.3f}")

        # 高張力エッジ (上位3)
        top_tensions = sorted(tensions, key=lambda t: t.tension, reverse=True)[:3]
        for t in top_tensions:
            lines.append(f"  ⚡ {t.series_a}⊗{t.series_b}: "
                        f"tension={t.tension:.2f} (w={t.weight:.1f})")

        # 融合方式の選択
        if V > 0.3:
            conclusion = self._weighted_fusion(bb, tensions)
            lines.append(f"  → 重み付け融合 (V>{0.3}): {conclusion}")
        else:
            conclusion = self._simple_aggregate(bb)
            lines.append(f"  → 通常融合 (V≤{0.3}): {conclusion}")

        # Blackboard に統合結論を書込み
        bb.write("slots.taxis_conclusion", conclusion, source="taxis")
        bb.write("slots.taxis_V", V, source="taxis")

        return "\n".join(lines)

    def _compute_k6_tensions(self, bb) -> list[TensionEdge]:
        """15 エッジの張力を計算"""
        tensions = []
        for a, b in combinations(SERIES_KEYS, 2):
            weight = K6_TENSION_WEIGHTS.get((a, b), 0.3)
            limit_a = bb.series_limits.get(a, "")
            limit_b = bb.series_limits.get(b, "")

            # 意味的張力: 2つの limit 文の「矛盾度」をヒューリスティックに推定
            semantic = self._estimate_semantic_tension(limit_a, limit_b)
            tension = weight * semantic

            tensions.append(TensionEdge(
                series_a=a, series_b=b,
                weight=weight,
                semantic_score=semantic,
                tension=tension,
            ))
        return tensions

    @staticmethod
    def _estimate_semantic_tension(text_a: str, text_b: str) -> float:
        """2つの Limit 文の意味的張力を推定 (0=整合, 1=矛盾)

        ヒューリスティック:
          - 対立語の検出 (高/低, 大/小, 積極/慎重)
          - 文字列の重複率 (高重複 = 低張力)
        """
        if not text_a or not text_b:
            return 0.5  # 情報不足

        # 対立語ペア
        opposites = [
            ("高", "低"), ("大", "小"), ("積極", "慎重"),
            ("探索", "活用"), ("広域", "局所"),
            ("リスク", "安全"), ("不足", "充足"),
        ]
        opposition_count = 0
        for pos, neg in opposites:
            if (pos in text_a and neg in text_b) or (neg in text_a and pos in text_b):
                opposition_count += 1

        # n-gram 重複率
        words_a = set(text_a)
        words_b = set(text_b)
        if words_a | words_b:
            overlap = len(words_a & words_b) / len(words_a | words_b)
        else:
            overlap = 0.0

        # 対立語が多いほど、重複が少ないほど張力が高い
        tension = min(1.0, opposition_count * 0.3 + (1.0 - overlap) * 0.3)
        return tension

    @staticmethod
    def _compute_contradiction(tensions: list[TensionEdge]) -> float:
        """矛盾度 V = 全エッジの張力の平均"""
        if not tensions:
            return 0.0
        return sum(t.tension for t in tensions) / len(tensions)

    @staticmethod
    def _weighted_fusion(bb, tensions: list[TensionEdge]) -> str:
        """高張力ペアの解消を優先した融合"""
        top = sorted(tensions, key=lambda t: t.tension, reverse=True)[0]
        limit_a = bb.series_limits.get(top.series_a, "")
        limit_b = bb.series_limits.get(top.series_b, "")
        return (f"主要矛盾 {top.series_a}⊗{top.series_b} の解消を優先。"
                f" {top.series_a}: {limit_a[:50]}。"
                f" {top.series_b}: {limit_b[:50]}")

    @staticmethod
    def _simple_aggregate(bb) -> str:
        """低矛盾時の均等集約"""
        parts = []
        for key in SERIES_KEYS:
            limit = bb.series_limits.get(key, "")
            if limit:
                parts.append(f"{key}: {limit[:40]}")
        return " | ".join(parts)
