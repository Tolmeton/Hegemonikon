from __future__ import annotations
# PROOF: [L2/Phase2] <- hermeneus/src/subscribers/convergence_sub.py
"""
ConvergenceSubscriber — 収束メトリクスのログ記録

段階 1 (最低リスク): 出力に一切影響を与えず、メトリクスだけを記録する。
C:{} ループの各イテレーションでエントロピー変化、類似度、イテレーション数を追跡し、
収束プロセスの可視化と事後分析を可能にする。

リスク: ゼロ (読取専用、副作用なし)
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..activation import BaseSubscriber, ActivationPolicy, PresetPolicies
from ..event_bus import CognitionEvent, EventType

logger = logging.getLogger(__name__)


@dataclass
class ConvergenceMetric:
    """収束プロセスの1イテレーションのメトリクス"""
    iteration: int
    entropy_before: float
    entropy_after: float
    entropy_delta: float
    similarity: float = 0.0
    delta_skip: bool = False
    duration_ms: float = 0.0
    timestamp: float = field(default_factory=time.monotonic)


class ConvergenceSubscriber(BaseSubscriber):
    """C:{} 収束ループのメトリクスを収集・記録する subscriber

    CONVERGENCE_ITER イベントを受け取り、
    各イテレーションのエントロピー変化と収束度をログに記録する。

    Usage:
        bus = CognitionEventBus()
        conv_sub = ConvergenceSubscriber()
        bus.subscribe(EventType.CONVERGENCE_ITER, conv_sub)

        # 実行後:
        print(conv_sub.summary())
    """

    def __init__(self):
        super().__init__(
            name="convergence_tracker",
            policy=ActivationPolicy(
                event_types={
                    EventType.CONVERGENCE_ITER,
                    EventType.EXECUTION_COMPLETE,
                },
            ),
            fire_threshold=0.0,  # 常に発火 (モニタリング/追跡が目的のため)
        )
        self._metrics: List[ConvergenceMetric] = []
        self._current_loop_id: str = ""

    def score(self, event: CognitionEvent) -> float:
        """収束度が低いほどスコアが高い (介入価値がある)

        Phase 3: C:{} ループで収束が遅い = もっとモニタリングが必要
        Phase 4a: Synteleia の品質アラート痕跡があればさらに監視を強める
        """
        if not self._metrics:
            s = 0.8  # 初回は高スコア (観測データなし)
        else:
            last = self._metrics[-1]
            # 収束していない = 類似度が低い = スコアが高い
            s = max(0.0, 1.0 - last.similarity)

        # Phase 4a: Stigmergy 文脈依存
        if getattr(self, "stigmergy_context", None):
            syn_traces = self.stigmergy_context.get_traces_by_subscriber("synteleia_l0", limit=3)
            if syn_traces:
                # 誰かが品質アラートを発しているなら、モニタリング価値 (score) を上げる
                avg_syn_intensity = sum(t.intensity for t in syn_traces) / len(syn_traces)
                s = min(1.0, s + avg_syn_intensity * 0.5)

        self._score_history.append(s)
        return s

    def handle(self, event: CognitionEvent) -> Optional[str]:
        """収束メトリクスを記録"""
        if event.event_type == EventType.EXECUTION_COMPLETE:
            # 実行完了時に保存してサマリーを生成
            if self._metrics:
                self._save_to_disk(event)
                return self.summary()
            return None

        # CONVERGENCE_ITER の処理
        metric = ConvergenceMetric(
            iteration=event.iteration,
            entropy_before=event.entropy_before,
            entropy_after=event.entropy_after,
            entropy_delta=event.entropy_delta,
            similarity=event.metadata.get("similarity", 0.0),
            delta_skip=event.metadata.get("delta_skip", False),
            duration_ms=event.metadata.get("duration_ms", 0.0),
        )
        self._metrics.append(metric)

        # ログ出力
        logger.info(
            "C:{} iter=%d | ε: %.3f → %.3f (Δ=%.3f) | sim=%.3f | skip=%s",
            metric.iteration,
            metric.entropy_before,
            metric.entropy_after,
            metric.entropy_delta,
            metric.similarity,
            metric.delta_skip,
        )

        # Phase 4a: 環境に痕跡を残す (他 subscriber へのシグナル)
        self.leave_trace(
            event=event,
            payload={
                "iteration": metric.iteration,
                "similarity": metric.similarity,
                "delta_skip": metric.delta_skip
            },
            intensity=self._score_history[-1] if self._score_history else 0.0
        )

        return None  # ログのみ、出力なし

    def _save_to_disk(self, event: CognitionEvent) -> None:
        """ログをファイルに永続化 (層6: ConvergenceTracker 機能)"""
        import json
        import os
        from pathlib import Path
        
        # hermeneus/src/subscribers → 3 levels up = project root
        # mneme は oikos 直下 (プロジェクトルートの兄弟)
        _hgk_root = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        _mneme_dir = os.environ.get("MNEME_DIR", str(_hgk_root.parent / "mneme"))
        path = Path(_mneme_dir) / ".hegemonikon" / "macro_entropy.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        
        first = self._metrics[0]
        last = self._metrics[-1]
        
        record = {
            "timestamp": time.time(),
            "ccl": event.metadata.get("ccl", ""),
            "expanded_ccl": event.metadata.get("expanded_ccl", ""),
            "total_iters": len(self._metrics),
            "final_confidence": event.metadata.get("confidence", 0.0),
            "entropy_before": first.entropy_before,
            "entropy_after": last.entropy_after,
            "total_reduction": first.entropy_before - last.entropy_after,
            "bottleneck": event.metadata.get("bottleneck"),
        }
        
        try:
            with open(path, "a") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:  # noqa: BLE001
            logger.debug(f"Failed to save convergence metrics: {e}")

    def summary(self) -> str:
        """収束プロセスのサマリーを生成"""
        if not self._metrics:
            return "No convergence data collected."

        total_iters = len(self._metrics)
        first = self._metrics[0]
        last = self._metrics[-1]
        total_reduction = first.entropy_before - last.entropy_after
        skipped = sum(1 for m in self._metrics if m.delta_skip)

        lines = [
            f"## 収束トラッカー",
            f"",
            f"| 指標 | 値 |",
            f"|:-----|:---|",
            f"| イテレーション数 | {total_iters} |",
            f"| 初期エントロピー | {first.entropy_before:.3f} |",
            f"| 最終エントロピー | {last.entropy_after:.3f} |",
            f"| 総エントロピー削減 | {total_reduction:.3f} |",
            f"| 差分スキップ数 | {skipped}/{total_iters} |",
        ]

        if total_iters > 1:
            lines.append(f"| 最終類似度 | {last.similarity:.3f} |")

        lines.append("")
        lines.append("### イテレーション詳細")
        lines.append("")
        lines.append("| # | ε_before | ε_after | Δε | sim | skip |")
        lines.append("|:--|:---------|:--------|:---|:----|:-----|")

        for m in self._metrics:
            skip_mark = "⚡" if m.delta_skip else ""
            lines.append(
                f"| {m.iteration} | {m.entropy_before:.3f} | "
                f"{m.entropy_after:.3f} | {m.entropy_delta:+.3f} | "
                f"{m.similarity:.3f} | {skip_mark} |"
            )

        return "\n".join(lines)

    def reset(self) -> None:
        """メトリクスをリセット"""
        self._metrics.clear()

    @property
    def metrics(self) -> List[ConvergenceMetric]:
        """生のメトリクスデータ"""
        return list(self._metrics)
