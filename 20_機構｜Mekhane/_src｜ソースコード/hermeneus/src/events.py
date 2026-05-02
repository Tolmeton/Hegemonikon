from __future__ import annotations
# PROOF: [L2/Phase5] <- hermeneus/src/events.py Cognition Event Definitions
"""
認知イベントのデータ定義

Phase 5 で event_bus.py から分離。
EventBus (CognitionEventBus) に依存しない純粋なデータ定義のみを含む。
leaf モジュール — 外部への依存なし。
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Event Types
# =============================================================================

class EventType(Enum):
    """認知イベントの種類

    逆拡散プロセスの各段階に対応。
    WF 実行 → 収束反復 → 検証 → エントロピー変化 の順で粒度が細かくなる。
    """
    # WF ノード実行完了 — 最も頻出。全ての workflow step で発火
    STEP_COMPLETE = "step_complete"

    # C:{} ループの各イテレーション完了 — 収束監視用
    CONVERGENCE_ITER = "convergence_iter"

    # V:{} ブロック完了 — 検証結果の伝播
    VERIFICATION = "verification"

    # エントロピーが閾値以上変化 — 情報価値の高い変化を検知
    ENTROPY_CHANGE = "entropy_change"

    # マクロ実行全体の完了 — 最終的な結果の集約
    EXECUTION_COMPLETE = "execution_complete"

    # D1/D2 Drift 検知 — セマンティックドリフトが閾値を超過した
    DRIFT_ALERT = "drift_alert"

    # マクロ展開開始 — 前処理 (PlanPreprocessor) が発火
    MACRO_START = "macro_start"

    # マクロ実行完了 — 後処理 (PlanRecorder) が発火
    MACRO_COMPLETE = "macro_complete"


# =============================================================================
# Event Data
# =============================================================================

def _generate_event_id() -> str:
    """Generate a unique event ID (12 chars)."""
    import uuid as _uuid
    h = _uuid.uuid4().hex
    # Pyre2 safe: avoid str slice
    return (h[0] + h[1] + h[2] + h[3] + h[4] + h[5]
            + h[6] + h[7] + h[8] + h[9] + h[10] + h[11])


@dataclass
class CognitionEvent:
    """認知イベント — 環境を流れるメッセージ

    StepResult を内包し、追加のメタデータを運ぶ。
    subscriber はこのオブジェクトを受け取って処理する。
    """
    event_type: EventType
    timestamp: float = field(default_factory=time.monotonic)

    # イベント固有の識別子 (痕跡追跡・Stigmergy で使用)
    event_id: str = field(default_factory=_generate_event_id)

    # StepResult (macro_executor.py から) — イベントの主ペイロード
    # 型注釈は文字列で遅延評価 (循環 import 回避)
    step_result: Any = None

    # ExecutionContext の snapshot — subscriber がコンテキスト参照用
    context_snapshot: Optional[Dict[str, Any]] = None

    # 追加メタデータ
    metadata: Dict[str, Any] = field(default_factory=dict)

    # イベント発生元の node_id
    source_node: str = ""

    # C:{} ループ固有: 現在のイテレーション番号
    iteration: int = 0

    # エントロピー情報
    entropy_before: float = 0.0
    entropy_after: float = 0.0

    # Blackboard (Phase 3: Subscriber 間共有状態)
    # 後方互換: None のとき旧 Subscriber は無視する
    blackboard: Any = field(default=None, compare=False, repr=False)

    @property
    def entropy_delta(self) -> float:
        """エントロピー変化量 (負 = 削減 = 良い方向)"""
        return self.entropy_after - self.entropy_before


# =============================================================================
# Subscriber Protocol
# =============================================================================

class EventSubscriber(Protocol):
    """subscriber の型プロトコル

    全ての subscriber は name と handle を持つ必要がある。
    should_activate は任意 (デフォルトは常に True)。
    """

    @property
    def name(self) -> str:
        """subscriber の識別名"""
        ...

    def should_activate(self, event: CognitionEvent) -> bool:
        """発火条件の判定 (activation.py で拡張)"""
        ...

    def handle(self, event: CognitionEvent) -> Optional[str]:
        """イベントを処理し、オプションで出力を返す"""
        ...


# =============================================================================
# Event Error
# =============================================================================

@dataclass
class EventError:
    """subscriber のハンドリング中に発生したエラー"""
    subscriber_name: str
    event_type: EventType
    error: Exception
    timestamp: float = field(default_factory=time.monotonic)
