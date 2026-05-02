from __future__ import annotations
# PROOF: [L2/Phase3] <- hermeneus/src/subscribers/series.py
# PURPOSE: /ax 用 6 Series Subscribers (T/M/K/D/O/C)
"""
6 Series Subscribers — /ax の心臓部

各 Series が Blackboard に Limit (1行の統合判断) を書込む。
6 Limit が全て充填されると TaxisSubscriber が自律発火する。

VISION §5.5: Dynamic Interleaving により、score 降順で発火。
各 Series の score() は自 Series 未充填なら高、充填済みなら 0。

発火条件:
    - MACRO_START イベント
    - マクロ名に "ax" を含む (/ax, /ax-, /ax+)
"""

import logging
from typing import Optional

from ..activation import BaseSubscriber, ActivationPolicy
from ..event_bus import CognitionEvent, EventType

logger = logging.getLogger(__name__)


# ─── 共通基底 ──────────────────────────────────────────

class _SeriesSubscriberBase(BaseSubscriber):
    """6 Series の共通基底

    各 Series は:
      - series_key: "T", "M", "K", "D", "O", "C"
      - series_name: 人間可読名
      - _generate_limit(): context + blackboard からLimit文を生成
    """

    series_key: str = ""
    series_name: str = ""
    base_score: float = 0.8  # 未充填時のデフォルトscore

    def __init__(self):
        super().__init__(
            name=f"series_{self.series_key.lower()}",
            policy=ActivationPolicy(
                event_types={EventType.MACRO_START},
                custom_predicate=self._is_ax_macro,
            ),
            fire_threshold=0.0,
        )

    @staticmethod
    def _is_ax_macro(event: CognitionEvent) -> bool:
        """@ax, @ax-, @ax+ のいずれか、またはシリーズ単体"""
        name = event.metadata.get("macro_name", "")
        return "ax" in name.lower()

    def score(self, event: CognitionEvent) -> float:
        """自 Series が未充填なら発火、充填済みなら不要

        Dynamic Interleaving: Blackboard 状態で自律的に発火判断。
        """
        bb = getattr(event, 'blackboard', None)
        if bb and self.series_key in bb.series_limits:
            return 0.0  # 既に計算済み → 不要
        s = self.base_score
        self._score_history.append(s)
        return s

    def handle(self, event: CognitionEvent) -> Optional[str]:
        """Limit を生成して Blackboard に書込む"""
        bb = getattr(event, 'blackboard', None)
        query = event.metadata.get("context", "")

        # Limit 生成 (サブクラスで実装)
        limit = self._generate_limit(query, bb)

        # Blackboard に書込み
        if bb is not None:
            bb.write(
                f"series_limits.{self.series_key}",
                limit,
                source=self.name,
            )

        return f"[{self.series_key}: {self.series_name}] {limit}"

    def _generate_limit(self, query: str, bb) -> str:
        """サブクラスでオーバーライド: Limit 文を生成"""
        return f"{self.series_name} の分析結果"


# ─── 6 Series 実装 ────────────────────────────────────

class TelosSubscriber(_SeriesSubscriberBase):
    """T-series: 目的分析 (Telos)

    何を達成しようとしているか。成功条件は何か。
    """
    series_key = "T"
    series_name = "目的 (Telos)"
    base_score = 0.9  # 最初に発火すべき (目的が全ての上流)

    def _generate_limit(self, query: str, bb) -> str:
        if not query:
            return "目的が未指定。コンテキストが必要。"
        # ヒューリスティック: query から目的キーワードを抽出
        purpose_markers = ["ため", "ために", "目的", "goal", "want", "achieve",
                          "実現", "達成", "完成", "解決"]
        has_purpose = any(m in query.lower() for m in purpose_markers)
        if has_purpose:
            return f"明確な目的: {query[:100]}"
        return f"暗黙の目的を推定: {query[:80]} の改善・実現"


class MethodosSubscriber(_SeriesSubscriberBase):
    """M-series: 戦略分析 (Methodos)

    探索 (explore) と活用 (exploit) のバランス。
    """
    series_key = "M"
    series_name = "戦略 (Methodos)"
    base_score = 0.8

    def _generate_limit(self, query: str, bb) -> str:
        # Blackboard から memory を参照して戦略を決定
        if bb and bb.memory:
            return f"活用優先: 既存知識あり (memory {len(bb.memory)} domain)"
        return f"探索優先: 既存知識なし。調査が先行する"


class KrisisSubscriber(_SeriesSubscriberBase):
    """K-series: 確信分析 (Krisis)

    現時点での確信度と不確実性の源泉。
    """
    series_key = "K"
    series_name = "確信 (Krisis)"
    base_score = 0.7

    def _generate_limit(self, query: str, bb) -> str:
        if bb:
            deficit = bb.information_deficit
            if deficit > 0.7:
                return f"確信度低: 情報不足 (deficit={deficit:.1f})"
            elif deficit > 0.3:
                return f"確信度中: 部分的情報あり (deficit={deficit:.1f})"
            else:
                return f"確信度高: 情報充足 (deficit={deficit:.1f})"
        return "確信度不明: Blackboard 未初期化"


class DiastasisSubscriber(_SeriesSubscriberBase):
    """D-series: 空間分析 (Diástasis)

    変更の粒度と影響範囲。
    """
    series_key = "D"
    series_name = "空間 (Diástasis)"
    base_score = 0.6

    def _generate_limit(self, query: str, bb) -> str:
        # query の長さで粒度を推定
        if len(query) < 30:
            return "粒度: 局所的 (短い query → 限定的な変更)"
        elif len(query) < 100:
            return "粒度: 中規模 (標準的な変更範囲)"
        return "粒度: 広域的 (長い query → 多ファイルに影響の可能性)"


class OrexisSubscriber(_SeriesSubscriberBase):
    """O-series: 傾向分析 (Orexis)

    リスクと機会の評価。価値傾向。
    """
    series_key = "O"
    series_name = "傾向 (Orexis)"
    base_score = 0.5

    def _generate_limit(self, query: str, bb) -> str:
        risk_markers = ["危険", "risk", "壊", "削除", "変更", "移行", "破壊"]
        opp_markers = ["改善", "最適", "新規", "追加", "拡張", "機会"]
        risks = sum(1 for m in risk_markers if m in query.lower())
        opps = sum(1 for m in opp_markers if m in query.lower())
        if risks > opps:
            return f"リスク優位: 慎重なアプローチが必要 (risk={risks}, opp={opps})"
        elif opps > risks:
            return f"機会優位: 積極的なアプローチが可能 (risk={risks}, opp={opps})"
        return f"均衡: リスクと機会が拮抗 (risk={risks}, opp={opps})"


class ChronosSubscriber(_SeriesSubscriberBase):
    """C-series: 時間分析 (Chronos)

    時間制約と優先順位。
    """
    series_key = "C"
    series_name = "時間 (Chronos)"
    base_score = 0.4  # 最後に発火 (他の Series の結果を見てから)

    def _generate_limit(self, query: str, bb) -> str:
        if bb:
            filled = len(bb.series_limits)
            return f"先行 {filled} Series 完了。統合判断の準備段階。"
        return "時間制約未定義。工数見積もりにはコンテキストが必要。"


# ─── 全 Series のリスト (登録用) ─────────────────────

ALL_SERIES_SUBSCRIBERS = [
    TelosSubscriber,
    MethodosSubscriber,
    KrisisSubscriber,
    DiastasisSubscriber,
    OrexisSubscriber,
    ChronosSubscriber,
]
