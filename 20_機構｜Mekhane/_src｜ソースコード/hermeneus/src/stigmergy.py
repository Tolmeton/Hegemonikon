# PROOF: [L2/Phase4b] <- hermeneus/src/stigmergy.py CognitionEnvironment
"""
CognitionEnvironment — 認知環境

Phase 4a: StigmergyContext (痕跡ベースの共有環境)
Phase 4b: CognitionEnvironment に昇格。subscriber のルーティングループを吸収し、
         EventBus (仲介者) を概念的に消去する。

設計原理:
    EventBus = 仲介者 (メディエータ) パターン
    CognitionEnvironment = 環境 (Stigmergy) パターン
    
    仲介者は「誰に何を送るか」を管理する。
    環境は「痕跡を残す/読む」だけ。subscriber は環境を観察して自律的に判断する。
    
    Phase 4b では EventBus の emit() ループを環境に吸収することで、
    仲介者→環境への概念的移行を完了する。

特徴:
    1. Git-like Audit Trail: 痕跡は append-only の DAG を形成する
    2. Neural Graph Interface: (Phase 5 準備)
    3. カスケード制御: max_cascade_depth で無限ループを防止
    4. Subscriber ルーティング: emit() で subscriber ループを駆動 (旧 EventBus)
    5. Output Collection: subscriber 出力をコンテキストに還流
"""
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Set, Tuple

logger = logging.getLogger(__name__)


def _generate_trace_id() -> str:
    """Generate a short unique trace ID (8 chars, Pyre2 safe)."""
    h = uuid.uuid4().hex
    return h[0] + h[1] + h[2] + h[3] + h[4] + h[5] + h[6] + h[7]


@dataclass(frozen=True)
class Trace:
    """環境に残される単一の痕跡 (Git commit に相当)"""
    id: str = field(default_factory=_generate_trace_id)
    subscriber_name: str = ""
    event_id: str = ""
    timestamp: float = field(default_factory=time.time)
    
    # Git-like parents (この痕跡を生む原因となった直前の痕跡 ID 群を親とする)
    parent_ids: List[str] = field(default_factory=list)
    
    # 痕跡の「強さ」(発火時のスコアなど)
    intensity: float = 0.0
    
    # 任意のコンテキストデータ
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # カスケード深度 (初期イベントから何連鎖目か)
    cascade_depth: int = 0


# Phase 4b: EventBus の EventError を環境側にも用意
@dataclass
class EnvironmentError:
    """subscriber のハンドリング中に発生したエラー"""
    subscriber_name: str
    error: Exception
    timestamp: float = field(default_factory=time.monotonic)


class CognitionEnvironment:
    """認知環境 — 痕跡の集積場 + subscriber ルーティング

    Phase 4a の StigmergyContext に、Phase 4b で EventBus のルーティング責務を統合。
    
    責務:
        1. 痕跡管理 (Trace の追加・検索・プルーニング)
        2. Subscriber 管理 (登録・発火判定)  
        3. イベントルーティング (emit → should_activate → handle)
        4. 出力収集 (subscriber 出力のコンテキスト還流)
    """

    def __init__(
        self,
        max_traces: int = 1000,
        max_cascade_depth: int = 10,
        enabled: bool = True,
    ):
        # ---- Stigmergy (Phase 4a) ----
        self._traces: Dict[str, Trace] = {}
        self._trace_log: List[str] = []
        self.max_traces = max_traces
        self.max_cascade_depth = max_cascade_depth
        self._event_heads: Dict[str, List[str]] = {}

        # ---- Subscriber Routing (Phase 4b: EventBus から移植) ----
        self._subscribers: List[Any] = []  # BaseSubscriber instances
        self.enabled = enabled

        # 統計
        self._stats: Dict[str, int] = {
            "total_emits": 0,
            "total_activations": 0,
            "total_errors": 0,
        }
        self._errors: List[EnvironmentError] = []
        self._outputs: List[Dict[str, str]] = []

        # ---- Hebbian Boost (Phase 5) ----
        self._boost_map: Dict[str, float] = {}  # subscriber名 → 現在のブースト値
        self._last_emit_trace_ids: List[str] = []  # 前回 emit で生成された Trace ID 群

    # =========================================================================
    # Subscriber Management (Phase 4b)
    # =========================================================================

    def register_subscriber(self, subscriber: Any) -> None:
        """subscriber を環境に登録し、環境を注入する"""
        if subscriber not in self._subscribers:
            self._subscribers.append(subscriber)
            # 環境を subscriber に注入 (双方向バインド)
            if hasattr(subscriber, 'bind_environment'):
                subscriber.bind_environment(self)
            logger.debug(
                "Environment: registered %s",
                getattr(subscriber, 'name', subscriber.__class__.__name__),
            )

    def unregister_subscriber(self, subscriber: Any) -> None:
        """subscriber を環境から登録解除"""
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)

    # =========================================================================
    # Event Routing (Phase 4b: EventBus.emit() から移植)
    # =========================================================================

    def emit(self, event: Any) -> List[Optional[str]]:
        """イベントを全 subscriber にルーティング (同期)

        EventBus.emit() と同一のロジック:
        1. 全 subscriber を走査
        2. should_activate() で発火判定
        3. handle() で処理
        4. 出力を蓄積
        """
        if not self.enabled:
            return []

        self._stats["total_emits"] += 1
        outputs: List[Optional[str]] = []
        current_emit_trace_ids: List[str] = []

        for sub in self._subscribers:
            try:
                sub_name = getattr(sub, 'name', sub.__class__.__name__)

                # 発火条件チェック (Phase 3b: 分散ルーティング)
                if hasattr(sub, 'should_activate'):
                    if not sub.should_activate(event):
                        logger.debug(
                            "Environment: %s skipped (should_activate=False)",
                            sub_name,
                        )
                        continue

                # ハンドリング
                self._stats["total_activations"] += 1
                output = sub.handle(event)
                outputs.append(output)

                # Phase 5: subscriber 発火を Trace として記録
                # これにより get_neural_edges() が因果関係を計算できる
                event_type_val = getattr(
                    getattr(event, 'event_type', None), 'value', 'unknown'
                )
                trace = Trace(
                    subscriber_name=sub_name,
                    event_id=event_type_val,
                    intensity=getattr(sub, 'fire_threshold', 0.5),
                    parent_ids=list(self._last_emit_trace_ids),
                )
                self.add_trace(trace)
                current_emit_trace_ids.append(trace.id)

                if output:
                    self._outputs.append({
                        "subscriber": sub_name,
                        "output": output,
                        "event_type": event_type_val,
                    })
                    logger.debug(
                        "Environment: %s produced output (%d chars)",
                        sub_name,
                        len(output),
                    )

            except Exception as e:  # noqa: BLE001
                self._stats["total_errors"] += 1
                self._errors.append(EnvironmentError(
                    subscriber_name=getattr(sub, 'name', str(sub)),
                    error=e,
                ))
                logger.warning(
                    "Environment: error in %s: %s",
                    getattr(sub, 'name', str(sub)),
                    e,
                )

        # 次の emit で因果関係チェーンを構築するため記録
        if current_emit_trace_ids:
            self._last_emit_trace_ids = current_emit_trace_ids

        return outputs

    async def emit_async(self, event: Any) -> List[Optional[str]]:
        """イベントを非同期に全 subscriber に配信"""
        if not self.enabled:
            return []

        self._stats["total_emits"] += 1

        async def _run_sub(sub: Any) -> Optional[str]:
            sub_name = getattr(sub, 'name', sub.__class__.__name__)
            try:
                if hasattr(sub, 'should_activate'):
                    if not sub.should_activate(event):
                        return None

                self._stats["total_activations"] += 1

                if hasattr(sub, 'handle_async'):
                    return await sub.handle_async(event)
                else:
                    return sub.handle(event)

            except Exception as e:  # noqa: BLE001
                self._stats["total_errors"] += 1
                self._errors.append(EnvironmentError(
                    subscriber_name=sub_name,
                    error=e,
                ))
                logger.warning("Environment async error in %s: %s", sub_name, e)
                return None

        results = await asyncio.gather(
            *[_run_sub(sub) for sub in self._subscribers],
            return_exceptions=False,
        )

        for sub, output in zip(self._subscribers, results):
            if output:
                sub_name = getattr(sub, 'name', sub.__class__.__name__)
                self._outputs.append({
                    "subscriber": sub_name,
                    "output": str(output),
                    "event_type": getattr(
                        getattr(event, 'event_type', None), 'value', 'unknown'
                    ),
                })

        return list(results)

    # =========================================================================
    # Output Collection (Phase 4b: EventBus から移植)
    # =========================================================================

    def collect_outputs(self) -> List[Dict[str, str]]:
        """蓄積された subscriber の出力をすべて返す"""
        return list(self._outputs)

    def flush_outputs(self) -> List[Dict[str, str]]:
        """蓄積された出力を返してクリア"""
        outputs = list(self._outputs)
        self._outputs.clear()
        return outputs

    def inject_outputs_to_context(self, ctx_variables: Dict[str, Any]) -> None:
        """蓄積された subscriber 出力をコンテキスト変数に注入"""
        outputs = self.flush_outputs()
        if outputs:
            existing = ctx_variables.get('$event_outputs', [])
            existing.extend(outputs)
            ctx_variables['$event_outputs'] = existing

    # =========================================================================
    # Score-based Selection (Phase 3 から移植)
    # =========================================================================

    def score_subscribers(self, event: Any) -> List[Dict[str, Any]]:
        """全 subscriber のスコアを計算し、降順で返す"""
        if not self.enabled:
            return []

        scored = []
        for sub in self._subscribers:
            try:
                if hasattr(sub, 'should_activate'):
                    if not sub.should_activate(event):
                        continue

                if hasattr(sub, 'score'):
                    s = sub.score(event)
                else:
                    s = 0.5

                sub_name = getattr(sub, 'name', sub.__class__.__name__)
                scored.append({
                    "subscriber": sub,
                    "name": sub_name,
                    "score": s,
                })
            except Exception as e:  # noqa: BLE001
                logger.debug("Environment: score failed for %s: %s", sub, e)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    # =========================================================================
    # Trace Management (Phase 4a — 変更なし)
    # =========================================================================

    def add_trace(self, trace: Trace) -> None:
        """痕跡を残す"""
        if trace.cascade_depth > self.max_cascade_depth:
            return

        self._traces[trace.id] = trace
        self._trace_log.append(trace.id)
        
        # Update event HEADs
        heads = self._event_heads.setdefault(trace.event_id, [])
        for p_id in trace.parent_ids:
            if p_id in heads:
                heads.remove(p_id)
        heads.append(trace.id)

        if len(self._trace_log) > self.max_traces:
            self._prune_traces()

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        return self._traces.get(trace_id)

    def get_recent_traces(self, limit: int = 10) -> List[Trace]:
        """最新の痕跡を取得"""
        start_idx = max(0, len(self._trace_log) - limit)
        return [self._traces[self._trace_log[i]] for i in range(start_idx, len(self._trace_log))]

    def get_traces_by_subscriber(self, subscriber_name: str, limit: int = 10) -> List[Trace]:
        """特定の subscriber が残した痕跡を取得"""
        traces = []
        for t_id in reversed(self._trace_log):
            trace = self._traces[t_id]
            if trace.subscriber_name == subscriber_name:
                traces.append(trace)
                if len(traces) >= limit:
                    break
        return traces

    def get_event_heads(self, event_id: str) -> List[Trace]:
        """特定のイベントに対する末端の痕跡を取得"""
        head_ids = self._event_heads.get(event_id, [])
        return [self._traces[tid] for tid in head_ids]

    def _prune_traces(self) -> None:
        """最も古い痕跡を削除する (TTL / 忘却機能)"""
        prune_count = max(1, self.max_traces // 10)
        pruned_ids = []
        for i in range(prune_count):
            pruned_ids.append(self._trace_log[i])
            
        new_log = []
        for i in range(prune_count, len(self._trace_log)):
            new_log.append(self._trace_log[i])
        self._trace_log = new_log
        
        for p_id in pruned_ids:
            trace = self._traces.pop(p_id, None)
            if trace:
                heads = self._event_heads.get(trace.event_id, [])
                if p_id in heads:
                    heads.remove(p_id)
                    if len(heads) == 0:
                        self._event_heads.pop(trace.event_id, None)

    # =========================================================================
    # Neural Graph Interface (Phase 5 準備)
    # =========================================================================
    
    def get_neural_edges(self) -> List[Tuple[str, str, float]]:
        """subscriber をノード、痕跡の因果関係をエッジとする有向グラフ"""
        edge_weights: Dict[Tuple[str, str], float] = {}
        
        for trace in self._traces.values():
            target_sub = trace.subscriber_name
            for parent_id in trace.parent_ids:
                parent_trace = self._traces.get(parent_id)
                if parent_trace:
                    source_sub = parent_trace.subscriber_name
                    if source_sub != target_sub:
                        edge = (source_sub, target_sub)
                        edge_weights[edge] = edge_weights.get(edge, 0.0) + trace.intensity
                        
        return [(src, tgt, weight) for (src, tgt), weight in edge_weights.items()]

    def apply_hebbian_boost(
        self,
        max_boost: float = 0.3,
        decay_rate: float = 0.9,
    ) -> Dict[str, float]:
        """Hebb則スコアブースト — 協調発火パターンを強化する

        Neural Graph の連鎖構造を読み取り、頻繁に連続発火する
        subscriber ペア (A→B) の B の fire_threshold を一時的に下げる。
        
        「一緒に発火するニューロンは、一緒に配線される」
        (Neurons that fire together, wire together)
        
        Args:
            max_boost: subscriber の fire_threshold を下げる最大量 (0.3 = 0.5→0.2)
            decay_rate: 前回のブースト値に対する減衰係数 (0.9 = 毎ステップ10%減衰)
            
        Returns:
            subscriber名 → 適用されたブースト値の辞書
        """
        edges = self.get_neural_edges()
        
        if edges:
            # 各ターゲット subscriber のブースト量を計算
            # weight を正規化して max_boost にスケーリング
            max_weight = max(w for _, _, w in edges)
            if max_weight == 0:
                max_weight = 1.0
            
            active_targets = set()
            for _src, tgt, weight in edges:
                normalized = min(1.0, weight / max_weight)
                boost = normalized * max_boost
                # 既存のブースト値と新しい値の最大値を取る
                self._boost_map[tgt] = max(
                    self._boost_map.get(tgt, 0.0) * decay_rate,
                    boost,
                )
                active_targets.add(tgt)
            
            # アクティブでないエントリを減衰
            for name in list(self._boost_map.keys()):
                if name not in active_targets:
                    self._boost_map[name] = self._boost_map[name] * decay_rate
                    if self._boost_map[name] < 0.01:
                        del self._boost_map[name]
        else:
            # エッジなし: 全ブースト記録を減衰
            for name in list(self._boost_map.keys()):
                self._boost_map[name] = self._boost_map[name] * decay_rate
                if self._boost_map[name] < 0.01:
                    del self._boost_map[name]

        # subscriber に適用 (エッジの有無にかかわらず常に実行)
        applied: Dict[str, float] = {}
        for sub in self._subscribers:
            name = getattr(sub, "name", sub.__class__.__name__)
            boost_val = self._boost_map.get(name, 0.0)
            if hasattr(sub, "fire_threshold"):
                original = getattr(sub, "_original_threshold", sub.fire_threshold)
                if not hasattr(sub, "_original_threshold"):
                    sub._original_threshold = sub.fire_threshold
                if boost_val > 0.01:
                    # 閾値を一時的に下げる (最低値 0.05 を保証)
                    sub.fire_threshold = max(0.05, original - boost_val)
                    applied[name] = boost_val
                else:
                    # ブースト消滅: 元の閾値に復帰
                    if hasattr(sub, "_original_threshold"):
                        sub.fire_threshold = sub._original_threshold
        
        return applied

    # =========================================================================
    # Statistics & Introspection
    # =========================================================================

    @property
    def stats(self) -> Dict[str, Any]:
        """統計情報を返す"""
        return {
            **self._stats,
            "subscribers": len(self._subscribers),
            "traces": len(self._traces),
            "pending_outputs": len(self._outputs),
            "errors": len(self._errors),
            "active_boosts": len(self._boost_map),
        }

    @property
    def errors(self) -> List[EnvironmentError]:
        return list(self._errors)

    def list_subscribers(self) -> List[str]:
        """登録されている subscriber 名の一覧"""
        return list(set(
            getattr(s, 'name', s.__class__.__name__)
            for s in self._subscribers
        ))

    def reset_stats(self) -> None:
        """統計をリセット"""
        self._stats = {
            "total_emits": 0,
            "total_activations": 0,
            "total_errors": 0,
        }
        self._errors.clear()
        self._outputs.clear()
        self._boost_map.clear()
        self._last_emit_trace_ids.clear()
        # ブーストされた subscriber の閾値を元に戻す
        for sub in self._subscribers:
            if hasattr(sub, '_original_threshold'):
                sub.fire_threshold = sub._original_threshold
                del sub._original_threshold

    def __repr__(self) -> str:
        return (
            f"CognitionEnvironment("
            f"enabled={self.enabled}, "
            f"subscribers={len(self._subscribers)}, "
            f"traces={len(self._traces)}, "
            f"emits={self._stats['total_emits']})"
        )


# ─── 後方互換エイリアス ─────────────────────────────────────────
# Phase 4a のコードが StigmergyContext を参照している場合のため
StigmergyContext = CognitionEnvironment

# 旧関数名も互換
generate_trace_id = _generate_trace_id
