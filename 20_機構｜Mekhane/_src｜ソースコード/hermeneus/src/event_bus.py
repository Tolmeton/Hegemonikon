from __future__ import annotations
# PROOF: [L2/Phase5] <- hermeneus/src/event_bus.py CognitionEventBus
"""
CognitionEventBus — Phase 5 移行中

データ定義 (EventType, CognitionEvent, EventSubscriber, EventError) は
hermeneus/src/events.py に移動済み。後方互換のため re-export する。

CognitionEventBus クラスは Phase 5 Step 1b で削除予定。
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
)

# Phase 5 Step 1a: データ定義は events.py に移動済み。
# 後方互換のため re-export する。
from hermeneus.src.events import (  # noqa: F401
    EventType,
    CognitionEvent,
    EventSubscriber,
    EventError,
    _generate_event_id,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CognitionEventBus
# =============================================================================

class CognitionEventBus:
    """認知イベントバス — subscriber のルーティングとディスパッチ

    設計方針:
        - 直列 emit (デフォルト): 各 subscriber を順次呼び出す
        - emit_async: asyncio.gather で並列実行 (LLM 系)
        - エラー隔離: 1つの subscriber の失敗が他に影響しない
        - 統計収集: emit 回数, 発火回数, エラー数を追跡
        - output_collector: subscriber の出力をコンテキストに還流可能

    Usage:
        bus = CognitionEventBus()
        bus.subscribe(EventType.STEP_COMPLETE, my_subscriber)
        bus.emit(CognitionEvent(event_type=EventType.STEP_COMPLETE, ...))
    """

    def __init__(self, enabled: bool = True):
        # EventType ごとの subscriber リスト
        self._subscribers: Dict[EventType, List[EventSubscriber]] = {
            et: [] for et in EventType
        }
        # 全イベント用の subscriber (ワイルドカード)
        self._global_subscribers: List[EventSubscriber] = []

        # 有効/無効フラグ (テスト時やパフォーマンス重視時に OFF)
        self.enabled = enabled

        # 統計
        self._stats: Dict[str, int] = {
            "total_emits": 0,
            "total_activations": 0,
            "total_errors": 0,
        }
        self._errors: List[EventError] = []

        # subscriber の出力を蓄積 (コンテキスト還流用)
        self._outputs: List[Dict[str, str]] = []

    # ─── Registration ────────────────────────────────────────

    def subscribe(
        self,
        event_type: EventType,
        subscriber: EventSubscriber,
    ) -> None:
        """subscriber をイベントタイプに登録"""
        if subscriber not in self._subscribers[event_type]:
            self._subscribers[event_type].append(subscriber)
            logger.debug(
                "EventBus: subscribed %s to %s",
                getattr(subscriber, 'name', subscriber.__class__.__name__),
                event_type.value,
            )

    def subscribe_all(self, subscriber: EventSubscriber) -> None:
        """全イベントタイプに subscriber を登録 (ワイルドカード)"""
        if subscriber not in self._global_subscribers:
            self._global_subscribers.append(subscriber)
            logger.debug(
                "EventBus: subscribed %s to ALL events",
                getattr(subscriber, 'name', subscriber.__class__.__name__),
            )

    def unsubscribe(
        self,
        event_type: EventType,
        subscriber: EventSubscriber,
    ) -> None:
        """subscriber を登録解除"""
        subs = self._subscribers.get(event_type, [])
        if subscriber in subs:
            subs.remove(subscriber)

    def unsubscribe_all(self, subscriber: EventSubscriber) -> None:
        """全イベントタイプから subscriber を登録解除"""
        for subs in self._subscribers.values():
            if subscriber in subs:
                subs.remove(subscriber)
        if subscriber in self._global_subscribers:
            self._global_subscribers.remove(subscriber)

    # ─── Emit (Synchronous) ──────────────────────────────────

    def emit(self, event: CognitionEvent) -> List[Optional[str]]:
        """イベントを同期的に全 subscriber に配信 (Dynamic Interleaving)

        VISION §5.5: score 降順で発火し、Blackboard 状態が次の発火を動的に決定する。
        各 subscriber の handle() 完了後、Blackboard の状態が変化するため、
        次の subscriber が読む Blackboard は前の subscriber の出力を反映する。

        Returns:
            各 subscriber の出力のリスト (None 含む)
        """
        if not self.enabled:
            return []

        self._stats["total_emits"] += 1
        outputs: List[Optional[str]] = []

        # ═══ Blackboard 初期化 (Phase 3) ═══
        if event.blackboard is None:
            from .blackboard import CognitionBlackboard
            event.blackboard = CognitionBlackboard(
                query=event.metadata.get("context", ""),
            )

        # 対象 subscriber = 型別 + グローバル
        subscribers = (
            self._subscribers.get(event.event_type, [])
            + self._global_subscribers
        )

        # ═══ Dynamic Interleaving: score 降順でソート ═══
        scored_subs = []
        for sub in subscribers:
            sub_name = getattr(sub, 'name', sub.__class__.__name__)
            try:
                # should_activate でフィルタ (Phase 2 前段フィルタ)
                if hasattr(sub, 'should_activate'):
                    if not sub.should_activate(event):
                        logger.debug(
                            "EventBus: %s skipped (should_activate=False)",
                            sub_name,
                        )
                        continue

                # score を計算 (Phase 3)
                if hasattr(sub, 'score'):
                    s = sub.score(event)
                else:
                    s = 0.5  # デフォルト: score() なしの旧 Subscriber

                scored_subs.append((s, sub_name, sub))

            except Exception as e:  # noqa: BLE001
                self._stats["total_errors"] += 1
                self._errors.append(EventError(
                    subscriber_name=sub_name,
                    event_type=event.event_type,
                    error=e,
                ))
                logger.warning(
                    "EventBus: score/activate error in %s: %s",
                    sub_name, e,
                )

        # score 降順でソート (同スコアは登録順を維持 = stable sort)
        scored_subs.sort(key=lambda x: x[0], reverse=True)

        # ═══ Dynamic Interleaving: score 降順で発火 + リスコアリング ═══
        deferred = []  # score=0 の Subscriber を保持
        for score_val, sub_name, sub in scored_subs:
            if score_val <= 0.0:
                # 「今は不要」— Blackboard 変化後に再評価
                deferred.append((sub_name, sub))
                logger.debug(
                    "EventBus: %s deferred (score=%.2f)",
                    sub_name, score_val,
                )
                continue

            try:
                self._stats["total_activations"] += 1
                output = sub.handle(event)
                outputs.append(output)

                if output:
                    self._outputs.append({
                        "subscriber": sub_name,
                        "output": output,
                        "event_type": event.event_type.value,
                    })
                    logger.debug(
                        "EventBus: %s fired (score=%.2f, %d chars)",
                        sub_name, score_val, len(output),
                    )

            except Exception as e:  # noqa: BLE001
                self._stats["total_errors"] += 1
                err = EventError(
                    subscriber_name=sub_name,
                    event_type=event.event_type,
                    error=e,
                )
                self._errors.append(err)
                logger.warning(
                    "EventBus: error in %s handling %s: %s",
                    err.subscriber_name,
                    event.event_type.value,
                    e,
                )

        # ═══ リスコアリング: Blackboard 変化後に deferred を再評価 ═══
        # VISION §5.5: 「6 Series が全て書込んだ後、Taxis が自律的に発火」
        if deferred:
            for sub_name, sub in deferred:
                try:
                    new_score = sub.score(event) if hasattr(sub, 'score') else 0.0
                    if new_score > 0.0:
                        logger.debug(
                            "EventBus: %s re-scored (0→0%.2f), firing",
                            sub_name, new_score,
                        )
                        self._stats["total_activations"] += 1
                        output = sub.handle(event)
                        outputs.append(output)
                        if output:
                            self._outputs.append({
                                "subscriber": sub_name,
                                "output": output,
                                "event_type": event.event_type.value,
                            })
                except Exception as e:  # noqa: BLE001
                    self._stats["total_errors"] += 1
                    self._errors.append(EventError(
                        subscriber_name=sub_name,
                        event_type=event.event_type,
                        error=e,
                    ))

        return outputs

    # ─── Emit (Async) ────────────────────────────────────────

    async def emit_async(self, event: CognitionEvent) -> List[Optional[str]]:
        """イベントを非同期に全 subscriber に配信 (LLM 呼び出し等に使用)

        Returns:
            各 subscriber の出力のリスト (None 含む)
        """
        if not self.enabled:
            return []

        self._stats["total_emits"] += 1
        subscribers = (
            self._subscribers.get(event.event_type, [])
            + self._global_subscribers
        )

        async def _run_sub(sub: EventSubscriber) -> Optional[str]:
            sub_name = getattr(sub, 'name', sub.__class__.__name__)
            try:
                if hasattr(sub, 'should_activate'):
                    if not sub.should_activate(event):
                        return None

                self._stats["total_activations"] += 1

                # async handle があれば使う
                if hasattr(sub, 'handle_async'):
                    return await sub.handle_async(event)
                else:
                    return sub.handle(event)

            except Exception as e:  # noqa: BLE001
                self._stats["total_errors"] += 1
                self._errors.append(EventError(
                    subscriber_name=sub_name,
                    event_type=event.event_type,
                    error=e,
                ))
                logger.warning("EventBus async error in %s: %s", sub_name, e)
                return None

        results = await asyncio.gather(
            *[_run_sub(sub) for sub in subscribers],
            return_exceptions=False,
        )

        # 出力を収集
        for sub, output in zip(subscribers, results):
            if output:
                sub_name = getattr(sub, 'name', sub.__class__.__name__)
                self._outputs.append({
                    "subscriber": sub_name,
                    "output": output,
                    "event_type": event.event_type.value,
                })

        return list(results)

    # ─── Output Collection ───────────────────────────────────

    def collect_outputs(self) -> List[Dict[str, str]]:
        """蓄積された subscriber の出力をすべて返す (コンテキスト還流用)"""
        return list(self._outputs)

    def flush_outputs(self) -> List[Dict[str, str]]:
        """蓄積された出力を返してクリア"""
        outputs = list(self._outputs)
        self._outputs.clear()
        return outputs

    def inject_outputs_to_context(self, ctx_variables: Dict[str, Any]) -> None:
        """蓄積された subscriber 出力をコンテキスト変数に注入

        ctx.variables['$event_outputs'] に subscriber 出力を追加。
        MacroExecutor の次のステップで参照可能になる。
        """
        outputs = self.flush_outputs()
        if outputs:
            existing = ctx_variables.get('$event_outputs', [])
            existing.extend(outputs)
            ctx_variables['$event_outputs'] = existing

    # ─── Phase 3: Score-based Selection ──────────────────────

    def score_subscribers(
        self,
        event: CognitionEvent,
        event_type: Optional[EventType] = None,
    ) -> List[Dict[str, Any]]:
        """全アクティブ subscriber のスコアを計算し、降順で返す (Phase 3)

        FEP 同型: EFE argmin と同じ構造。
        各モジュールが自身の「情報価値」を自己評価し、
        最も高いスコアのモジュールが選択される。

        Returns:
            [{"subscriber": sub, "name": name, "score": float}, ...] (降順)
        """
        if not self.enabled:
            return []

        et = event_type or event.event_type
        candidates = (
            self._subscribers.get(et, [])
            + self._global_subscribers
        )

        scored = []
        for sub in candidates:
            try:
                # should_activate でフィルタ (Phase 2 の前段フィルタ)
                if hasattr(sub, 'should_activate'):
                    if not sub.should_activate(event):
                        continue

                # score() を持つ subscriber のみスコアリング
                if hasattr(sub, 'score'):
                    s = sub.score(event)
                else:
                    s = 0.5  # デフォルト

                sub_name = getattr(sub, 'name', sub.__class__.__name__)
                scored.append({
                    "subscriber": sub,
                    "name": sub_name,
                    "score": s,
                })
            except Exception as e:  # noqa: BLE001
                logger.debug("EventBus: score failed for %s: %s", sub, e)

        # スコア降順でソート
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored



    # ─── Statistics ──────────────────────────────────────────

    @property
    def stats(self) -> Dict[str, Any]:
        """統計情報を返す"""
        sub_counts = {
            et.value: len(subs)
            for et, subs in self._subscribers.items()
            if subs
        }
        return {
            **self._stats,
            "subscribers": sub_counts,
            "global_subscribers": len(self._global_subscribers),
            "pending_outputs": len(self._outputs),
            "errors": len(self._errors),
        }

    @property
    def errors(self) -> List[EventError]:
        """発生したエラー一覧"""
        return list(self._errors)

    def clear_errors(self) -> None:
        """エラーログをクリア"""
        self._errors.clear()

    def reset_stats(self) -> None:
        """統計をリセット"""
        self._stats = {
            "total_emits": 0,
            "total_activations": 0,
            "total_errors": 0,
        }
        self._errors.clear()
        self._outputs.clear()

    # ─── Introspection ───────────────────────────────────────

    def list_subscribers(self, event_type: Optional[EventType] = None) -> List[str]:
        """登録されている subscriber 名の一覧"""
        if event_type:
            subs = self._subscribers.get(event_type, [])
        else:
            subs = []
            for sub_list in self._subscribers.values():
                subs.extend(sub_list)
            subs.extend(self._global_subscribers)

        return list(set(
            getattr(s, 'name', s.__class__.__name__)
            for s in subs
        ))

    def __repr__(self) -> str:
        total_subs = sum(len(s) for s in self._subscribers.values())
        total_subs += len(self._global_subscribers)
        return (
            f"CognitionEventBus("
            f"enabled={self.enabled}, "
            f"subscribers={total_subs}, "
            f"emits={self._stats['total_emits']})"
        )
