from __future__ import annotations
# PROOF: [L2/Phase3] <- hermeneus/src/blackboard.py
# PURPOSE: 全 Subscriber が読み書きする共有状態 (Blackboard Architecture)
"""
CognitionBlackboard — Phase 3 の基盤

VISION §4: 「各モジュールが条件が揃えば自律的に動く」の実現基盤。
全 Subscriber が Blackboard に書込み、他の Subscriber がそれを読む。
Phase 間情報伝播 (v10.0 PreprocessContext) を EventBus レベルに汎用化。

設計方針:
  - @dataclass で型付きフィールド (型安全性)
  - write() でソース追跡 (誰が書いたか)
  - series_limits: /ax 用の 6 Series Limit 保持
  - 汎用 slots: 任意の Subscriber が使える key-value
"""

import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class BlackboardEntry:
    """Blackboard への個別書込みエントリ (追跡用)"""
    key: str
    value: Any
    source: str  # 書込み元の Subscriber 名
    timestamp: float = field(default_factory=time.monotonic)


@dataclass
class CognitionBlackboard:
    """全 Subscriber が読み書きする共有状態

    VISION §5.5: Dynamic Interleaving の実現基盤。
    Blackboard の状態変化が、次に発火すべきモジュールを動的に決定する。
    """

    # ─── 問い ──────────────────────────────────────
    query: str = ""

    # ─── 記憶層の結果 (Phase A) ─────────────────────
    memory: dict[str, list[dict]] = field(default_factory=dict)
    memory_sources: set[str] = field(default_factory=set)
    information_deficit: float = 1.0  # 0=十分, 1=不足

    # ─── 6 Series の Limit 出力 (/ax 用) ───────────
    # key: "T", "M", "K", "D", "O", "C"
    series_limits: dict[str, str] = field(default_factory=dict)

    # ─── エントロピー履歴 ──────────────────────────
    entropy_history: list[float] = field(default_factory=list)

    # ─── 推薦 ─────────────────────────────────────
    recommended_verbs: list[str] = field(default_factory=list)

    # ─── 健康状態 ──────────────────────────────────
    health: dict[str, Any] = field(default_factory=dict)

    # ─── 汎用スロット (任意 Subscriber 用) ─────────
    slots: dict[str, Any] = field(default_factory=dict)

    # ─── 書込み履歴 (追跡用) ───────────────────────
    _log: list[BlackboardEntry] = field(default_factory=list, repr=False)

    def write(self, key: str, value: Any, source: str = "unknown") -> None:
        """Blackboard に書込み (ソース追跡付き)

        Args:
            key: 書込み先 ("series_limits.T", "memory.gnosis", "slots.foo" 等)
            value: 書込む値
            source: 書込み元の Subscriber 名
        """
        entry = BlackboardEntry(key=key, value=value, source=source)
        self._log.append(entry)

        # ドット記法でネストされたフィールドに書込み
        parts = key.split(".", 1)
        if len(parts) == 2:
            container_name, sub_key = parts
            container = getattr(self, container_name, None)
            if isinstance(container, dict):
                container[sub_key] = value
                return
            elif isinstance(container, set):
                container.add(value)
                return

        # トップレベルフィールドに直接書込み
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self.slots[key] = value

    def read(self, key: str, default: Any = None) -> Any:
        """Blackboard から読み取り

        Args:
            key: 読み取り元 ("series_limits.T", "memory.gnosis", "slots.foo" 等)
            default: キーが存在しない場合のデフォルト値
        """
        parts = key.split(".", 1)
        if len(parts) == 2:
            container_name, sub_key = parts
            container = getattr(self, container_name, None)
            if isinstance(container, dict):
                return container.get(sub_key, default)

        if hasattr(self, key):
            return getattr(self, key)
        return self.slots.get(key, default)

    @property
    def series_fill_rate(self) -> float:
        """6 Series の充填率 (0.0〜1.0)

        TaxisSubscriber の score() がこの値で自律発火を判断する。
        """
        expected = {"T", "M", "K", "D", "O", "C"}
        filled = expected & set(self.series_limits.keys())
        return len(filled) / len(expected)

    @property
    def write_count(self) -> int:
        """総書込み回数"""
        return len(self._log)

    def last_writer(self, key: str) -> Optional[str]:
        """指定キーの最後の書込み元を返す"""
        for entry in reversed(self._log):
            if entry.key == key:
                return entry.source
        return None
