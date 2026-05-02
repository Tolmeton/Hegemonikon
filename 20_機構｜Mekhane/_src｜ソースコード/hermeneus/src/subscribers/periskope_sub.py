from __future__ import annotations
# PROOF: [L2/Phase2] <- hermeneus/src/subscribers/periskope_sub.py
"""
PeriskopeSubscriber — エントロピー増大時の外部検索

段階 5: エントロピーが大幅に増大した場合に
Periskopē を使って外部検索で情報を補完する。

発火条件:
    - ENTROPY_CHANGE イベント
    - エントロピー変化量が +0.15 以上 (情報が不足している兆候)

リスク: 中-高 (外部 API 依存、レート制限に注意)
"""

import logging
from typing import Optional

from ..activation import BaseSubscriber, ActivationPolicy
from ..event_bus import CognitionEvent, EventType

logger = logging.getLogger(__name__)


class PeriskopeSubscriber(BaseSubscriber):
    """エントロピー増大時に Periskopē で外部検索する subscriber

    ENTROPY_CHANGE イベントを受け取り、
    エントロピーが大幅に増大 (情報不足) している場合に
    外部検索で情報補完のヒントを提供する。

    発火条件:
        - エントロピー変化量 > 0.15 (大幅な情報不足)
        - ENTROPY_CHANGE イベント
    """

    def __init__(self, delta_threshold: float = 0.15, fire_threshold: float = 0.2):
        super().__init__(
            name="periskope_searcher",
            policy=ActivationPolicy(
                event_types={EventType.ENTROPY_CHANGE},
                min_entropy_delta=delta_threshold,
                # 重い処理なので3回に1回だけ発火
                frequency=3,
            ),
            fire_threshold=fire_threshold,
        )
        self._search_count = 0
        self._periskope_available: Optional[bool] = None

    def score(self, event: CognitionEvent) -> float:
        """エントロピーの増大(Δ)が大きいほど外部検索の価値が高い (Phase 3)
        ただし検索は重いので、実行回数に応じてスコアを減衰させる。
        """
        # +に変化しているほど高スコア (max 1.0)
        base_score = min(max(0.0, event.entropy_delta) * 3.0, 1.0)
        penalty = self._search_count * 0.4
        s = max(0.0, base_score - penalty)
        self._score_history.append(s)
        return s

    def handle(self, event: CognitionEvent) -> Optional[str]:
        """外部検索で情報を補完"""
        # エントロピーが増大 (正の変化) していない場合はスキップ
        if event.entropy_delta <= 0:
            return None

        result = event.step_result
        if result is None:
            return None

        output = result.output if hasattr(result, 'output') else ""
        if not output or len(output) < 20:
            return None

        # Periskopē の利用可能性チェック (初回のみ)
        if self._periskope_available is None:
            self._periskope_available = self._check_periskope()

        if not self._periskope_available:
            # フォールバック: 検索提案のみ
            query = output[:80].replace('\n', ' ').strip()
            return (
                f"[🔭 Periskopē Suggestion]\n"
                f"  エントロピー増大 (Δ={event.entropy_delta:+.3f})。\n"
                f"  推奨: `periskope_search('{query}')` で外部情報を補完。"
            )

        # Periskopē 検索実行
        try:
            query = output[:80].replace('\n', ' ').strip()
            results = self._search_periskope(query)
            if results:
                self._search_count += 1
                return self._format_results(results, event.entropy_delta)
        except Exception as e:  # noqa: BLE001
            logger.warning("Periskopē search failed: %s", e)

        return None

    def _check_periskope(self) -> bool:
        """Periskopē が利用可能かチェック"""
        try:
            from mekhane.periskope.engine import PeriskopeEngine
            return True
        except ImportError:
            logger.info("Periskopē not available (import failed)")
            return False

    def _search_periskope(self, query: str) -> list:
        """Periskopē で検索実行"""
        try:
            from mekhane.periskope.engine import PeriskopeEngine
            engine = PeriskopeEngine()
            results = engine.search(query, max_results=3)
            return results
        except Exception:  # noqa: BLE001
            return []

    def _format_results(self, results: list, entropy_delta: float) -> str:
        """検索結果をフォーマット"""
        lines = [
            f"[🔭 Periskopē External Search (Δε={entropy_delta:+.3f})]",
        ]
        for i, r in enumerate(results, 1):
            title = getattr(r, 'title', str(r))[:100]
            url = getattr(r, 'url', '')
            lines.append(f"  {i}. {title}")
            if url:
                lines.append(f"     {url}")
        return "\n".join(lines)

    @property
    def search_count(self) -> int:
        return self._search_count
