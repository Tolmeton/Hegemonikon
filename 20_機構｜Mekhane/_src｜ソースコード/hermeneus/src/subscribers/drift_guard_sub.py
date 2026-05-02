from __future__ import annotations
# PROOF: [L2/Phase2] <- hermeneus/src/subscribers/drift_guard_sub.py
"""
DriftGuardSubscriber — D1→D2 動的結合

D1 (Semantic Drift 検出) が DRIFT_ALERT を発行したとき、
D2 (verify_step) を自動発動し、ドリフトしたステップの論理的妥当性を検証する。

Confabulation Guard (D3) が「全員合意 → 疑え」なら、
DriftGuard は「文脈断絶 → 検証せよ」。

設計原則:
    - DRIFT_ALERT に subscribe し、verify_step で局所検証
    - score() はドリフトスコアをそのまま返す (Phase 3 argmax 連携)
    - 検証結果を出力として EventBus に還流 → コンテキスト変数に注入
"""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..activation import BaseSubscriber, ActivationPolicy
from ..event_bus import CognitionEvent, EventType

logger = logging.getLogger(__name__)


@dataclass
class DriftAlert:
    """ドリフト検証結果の記録"""
    source_node: str
    drift_score: float
    verdict_type: str  # "ACCEPT" | "REJECT" | "UNCERTAIN"
    verdict_confidence: float
    verdict_reasoning: str
    prev_step: str = ""
    timestamp: float = field(default_factory=time.monotonic)


class DriftGuardSubscriber(BaseSubscriber):
    """DRIFT_ALERT → verify_step 自動発動 subscriber

    D1 (estimate_drift) が閾値超過を検出すると DRIFT_ALERT イベントが発行される。
    この subscriber がそれを受け取り、D2 (verify_step) で
    当該ステップの論理的妥当性を軽量検証する。

    Usage:
        bus = CognitionEventBus()
        guard = DriftGuardSubscriber()
        bus.subscribe(EventType.DRIFT_ALERT, guard)
    """

    def __init__(
        self,
        use_llm: bool = True,
        name: str = "drift_guard",
        event_type: EventType = EventType.DRIFT_ALERT,
        score_key: str = "drift",
        cache_ttl: float = 300.0,
    ):
        super().__init__(
            name=name,
            policy=ActivationPolicy(
                event_types={event_type},
            ),
        )
        self._alerts: List[DriftAlert] = []
        self._use_llm = use_llm
        self._score_key = score_key
        self._cache: Dict[str, tuple] = {}  # {key: (verdict, timestamp)}
        self._cache_ttl = cache_ttl
        self._cache_hits = 0
        self._cache_misses = 0

    def score(self, event: CognitionEvent) -> float:
        """ドリフトスコアが高いほどスコアが高い (介入価値が高い)

        Phase 3: argmax 選択時、高ドリフト = 最優先で検証すべき
        """
        drift = event.metadata.get(self._score_key, 0.0)
        s = min(1.0, drift)  # drift は 0.0-1.0
        self._score_history.append(s)
        return s

    def handle(self, event: CognitionEvent) -> Optional[str]:
        """DRIFT_ALERT を受け取り、verify_step で局所検証する"""
        drift = event.metadata.get(self._score_key, 0.0)
        source_node = event.source_node
        prev_step = event.metadata.get("prev_step", "")
        prev_output = event.metadata.get("prev_output", "")
        curr_output = event.metadata.get("curr_output", "")

        logger.info(
            "[DriftGuard] DRIFT_ALERT received: %s (drift=%.2f, prev=%s)",
            source_node, drift, prev_step,
        )

        if not self._use_llm or not prev_output or not curr_output:
            # LLM 不使用モード or 出力がない場合 → ログのみ
            alert = DriftAlert(
                source_node=source_node,
                drift_score=drift,
                verdict_type="SKIPPED",
                verdict_confidence=0.0,
                verdict_reasoning="LLM 検証スキップ (use_llm=False or 出力なし)",
                prev_step=prev_step,
            )
            self._alerts.append(alert)
            return f"⚠️ Drift detected at {source_node} (score={drift:.2f}) — verification skipped"

        # D2: verify_step で局所検証
        try:
            from hermeneus.src.verifier import verify_step

            context = f"前ステップ ({prev_step}) から現ステップ ({source_node}) へのドリフト={drift:.2f}"

            # キャッシュ: 同一入出力ペアの再検証を回避 (TTL 付き)
            combined = f"{prev_output}|{curr_output}".encode("utf-8")
            cache_key = hashlib.sha256(combined).hexdigest()[:16]
            now = time.time()
            cached = self._cache.get(cache_key)
            if cached and (now - cached[1]) < self._cache_ttl:
                self._cache_hits += 1
                verdict = cached[0]
                logger.debug("[DriftGuard] Cache hit for %s", source_node)
            else:
                self._cache_misses += 1
                verdict = verify_step(
                    step_input=prev_output,
                    step_output=curr_output,
                    context=context,
                )
                self._cache[cache_key] = (verdict, now)

            alert = DriftAlert(
                source_node=source_node,
                drift_score=drift,
                verdict_type=verdict.type.value,
                verdict_confidence=verdict.confidence,
                verdict_reasoning=verdict.reasoning,
                prev_step=prev_step,
            )
            self._alerts.append(alert)

            # Verdict をイベントメタデータに還元 → 後続の StepResult.metadata に残る
            event.metadata["drift_verdict"] = verdict.type.value
            event.metadata["drift_verdict_confidence"] = verdict.confidence
            event.metadata["drift_verdict_reasoning"] = verdict.reasoning[:200]

            # REJECT 時: 実行制御フラグを注入
            if verdict.type.value == "REJECT":
                event.metadata["drift_rejected"] = True
                logger.warning(
                    "[DriftGuard] ❌ REJECT at %s (drift=%.2f, confidence=%.0f%%): %s",
                    source_node, drift, verdict.confidence * 100,
                    verdict.reasoning[:100],
                )

            # 結果をフォーマットして返す
            icon = {"ACCEPT": "✅", "REJECT": "❌", "UNCERTAIN": "⚠️"}.get(
                verdict.type.value, "❓"
            )
            result = (
                f"{icon} DriftGuard: {source_node} (drift={drift:.2f})\n"
                f"  判定: {verdict.type.value} ({verdict.confidence:.0%})\n"
                f"  理由: {verdict.reasoning[:200]}"
            )

            logger.info("[DriftGuard] %s → %s (%.0f%%)",
                        source_node, verdict.type.value, verdict.confidence * 100)

            return result

        except Exception as e:  # noqa: BLE001
            logger.warning("[DriftGuard] verify_step failed: %s", e)
            alert = DriftAlert(
                source_node=source_node,
                drift_score=drift,
                verdict_type="ERROR",
                verdict_confidence=0.0,
                verdict_reasoning=f"verify_step failed: {e}",
                prev_step=prev_step,
            )
            self._alerts.append(alert)
            return f"⚠️ DriftGuard error at {source_node}: {e}"

    @property
    def alerts(self) -> List[DriftAlert]:
        """蓄積されたドリフト検証結果"""
        return list(self._alerts)

    def reset(self) -> None:
        """検証結果とキャッシュをリセット"""
        self._alerts.clear()
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

    @property
    def cache_stats(self) -> Dict[str, int]:
        """キャッシュ統計"""
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "size": len(self._cache),
        }


def create_verify_guard(
    event_type: EventType,
    name: str,
    score_key: str = "drift",
    use_llm: bool = True,
) -> DriftGuardSubscriber:
    """任意の EventType に対する verify_step ガードを生成するファクトリ

    DriftGuardSubscriber のコンストラクタに委譲する薄いラッパー。

    Usage:
        entropy_guard = create_verify_guard(
            EventType.ENTROPY_CHANGE, "entropy_guard",
            score_key="entropy_delta",
        )
        bus.subscribe(EventType.ENTROPY_CHANGE, entropy_guard)
    """
    return DriftGuardSubscriber(
        use_llm=use_llm,
        name=name,
        event_type=event_type,
        score_key=score_key,
    )
