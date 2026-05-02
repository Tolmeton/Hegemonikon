from __future__ import annotations
# PROOF: [L2/Phase2] <- hermeneus/src/subscribers/gnosis_sub.py
"""
GnosisSubscriber — 知識注入

段階 3 (出力に影響): ステップ完了時に Gnōsis (ナレッジベース) から
関連知識を検索し、コンテキストに注入する。

発火条件: エントロピーが高い (不確実性が高い) 時のみ。
エントロピーが低い (確信度が高い) 場合、余計な知識注入は邪魔になる。

リスク: 中 (出力に間接的に影響)
"""

import logging
from typing import Optional

from ..activation import BaseSubscriber, ActivationPolicy
from ..event_bus import CognitionEvent, EventType

logger = logging.getLogger(__name__)


class GnosisSubscriber(BaseSubscriber):
    """Gnōsis ナレッジベースから関連知識を検索・注入する subscriber

    STEP_COMPLETE イベントを受け取り、出力のエントロピーが高い場合に
    関連する知識を Gnōsis から検索してコンテキストに追加する。

    発火条件:
        - エントロピー > 0.5 (不確実性が高い時のみ)
        - STEP_COMPLETE イベント
    """

    def __init__(self, entropy_threshold: float = 0.5, max_results: int = 3, fire_threshold: float = 0.3):
        super().__init__(
            name="gnosis_injector",
            policy=ActivationPolicy(
                event_types={EventType.STEP_COMPLETE},
                min_entropy=entropy_threshold,
            ),
            fire_threshold=fire_threshold,  # ペナルティが大きくない限り自律発火
        )
        self.max_results = max_results
        self._injection_count = 0
        self._gnosis_available: Optional[bool] = None

    def score(self, event: CognitionEvent) -> float:
        """エントロピーが高いほど知識注入の価値が高い。
        ただし、既に注入済みの場合はスコアを減衰させる (Phase 3)
        """
        base_score = min(event.entropy_after, 1.0)
        penalty = self._injection_count * 0.3
        s = max(0.0, base_score - penalty)
        self._score_history.append(s)
        return s

    def handle(self, event: CognitionEvent) -> Optional[str]:
        """Gnōsis から関連知識を検索して注入テキストを返す"""
        result = event.step_result
        if result is None:
            return None

        output = result.output if hasattr(result, 'output') else ""
        if not output or len(output) < 20:
            return None

        # Gnōsis の利用可能性チェック (初回のみ)
        if self._gnosis_available is None:
            self._gnosis_available = self._check_gnosis()

        if not self._gnosis_available:
            return None

        # 検索クエリを構築: 出力の最初の100文字をクエリに
        query = output[:100].replace('\n', ' ').strip()

        try:
            results = self._search_gnosis(query)
            if results:
                self._injection_count += 1
                injection_text = self._format_injection(results)
                logger.info(
                    "Gnōsis: %d results injected for node %s",
                    len(results),
                    event.source_node,
                )
                return injection_text
        except Exception as e:  # noqa: BLE001
            logger.warning("Gnōsis search failed: %s", e)

        return None

    def _check_gnosis(self) -> bool:
        """Gnōsis が利用可能かチェック"""
        try:
            from mekhane.anamnesis.cli import GnosisSearch
            return True
        except ImportError:
            logger.info("Gnōsis not available (import failed)")
            return False

    def _search_gnosis(self, query: str) -> list:
        """Gnōsis でベクトル検索を実行"""
        try:
            from mekhane.anamnesis.cli import GnosisSearch
            searcher = GnosisSearch()
            results = searcher.search(query, limit=self.max_results)
            return results
        except Exception:  # noqa: BLE001
            return []

    def _format_injection(self, results: list) -> str:
        """検索結果をコンテキスト注入テキストに整形"""
        lines = ["[🧠 Gnōsis Knowledge Injection]"]
        for i, r in enumerate(results, 1):
            title = getattr(r, 'title', str(r))
            score = getattr(r, 'score', 0.0)
            snippet = getattr(r, 'snippet', str(r))[:200]
            lines.append(f"  {i}. [{score:.2f}] {title}")
            lines.append(f"     {snippet}")
        return "\n".join(lines)

    @property
    def injection_count(self) -> int:
        return self._injection_count
