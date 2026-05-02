from __future__ import annotations
# PROOF: [L2/Phase2] <- hermeneus/src/activation.py Subscriber Activation
"""
Activation Layer — subscriber の選択的発火条件

全イベントで全 subscriber が発火するのではなく、
条件に応じて選択的に発火する。FEP 的に言えば、
「驚きのない入力には反応しない」= 計算資源の最適配分。

各 subscriber は ActivationPolicy を持ち、
event の内容に基づいて should_activate() を判定する。
"""

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set

if TYPE_CHECKING:
    from .stigmergy import StigmergyContext

from .event_bus import CognitionEvent, EventType

logger = logging.getLogger(__name__)


# =============================================================================
# Activation Conditions
# =============================================================================

@dataclass
class ActivationPolicy:
    """subscriber の発火条件を定義する構造体

    複数の条件を AND / OR で組み合わせ可能。
    条件を満たさないイベントは subscriber に到達しない。

    Usage:
        policy = ActivationPolicy(
            min_entropy_delta=0.1,        # エントロピー変化が 10% 以上
            event_types={EventType.STEP_COMPLETE},
            custom_predicate=lambda e: "noe" in e.source_node,
        )
    """
    # エントロピー変化の最小閾値 (abs)
    # 0.0 = 常に発火, 0.1 = 10% 以上変化時のみ
    min_entropy_delta: float = 0.0

    # 現在のエントロピーの下限 (これ以上でないと発火しない)
    min_entropy: float = 0.0

    # 現在のエントロピーの上限 (これ以下でないと発火しない)
    max_entropy: float = 1.0

    # 対象イベントタイプ (空 = 全タイプで発火)
    event_types: Set[EventType] = field(default_factory=set)

    # 対象ノード ID のパターン (空 = 全ノードで発火)
    # 部分一致: "noe" → "/noe", "/noe+" 等にマッチ
    node_patterns: List[str] = field(default_factory=list)

    # 除外ノード ID のパターン
    exclude_patterns: List[str] = field(default_factory=list)

    # C:{} ループのイテレーション条件
    # None = 全イテレーションで発火
    # 整数 = そのイテレーション番号のみ発火 (0-indexed)
    # "last" = 最後のイテレーションのみ
    iteration_filter: Optional[Any] = None

    # カスタム述語 (最も柔軟な条件指定)
    custom_predicate: Optional[Callable[[CognitionEvent], bool]] = None

    # 発火頻度制限: N回に1回だけ発火
    # 1 = 毎回, 3 = 3回に1回
    frequency: int = 1

    # 内部カウンタ (frequency 用)
    _counter: int = field(default=0, repr=False)

    def evaluate(self, event: CognitionEvent) -> bool:
        """発火条件を評価

        全条件を AND で結合。1つでも False なら発火しない。
        """
        # 1. イベントタイプフィルタ
        if self.event_types and event.event_type not in self.event_types:
            return False

        # 2. エントロピー変化フィルタ
        if self.min_entropy_delta > 0:
            delta = abs(event.entropy_delta)
            if delta < self.min_entropy_delta:
                return False

        # 3. エントロピー範囲フィルタ
        if event.entropy_after < self.min_entropy:
            return False
        if event.entropy_after > self.max_entropy:
            return False

        # 4. ノードパターンフィルタ (inclusion)
        if self.node_patterns:
            matched = any(
                pat in event.source_node
                for pat in self.node_patterns
            )
            if not matched:
                return False

        # 5. 除外パターンフィルタ
        if self.exclude_patterns:
            excluded = any(
                pat in event.source_node
                for pat in self.exclude_patterns
            )
            if excluded:
                return False

        # 6. イテレーションフィルタ
        if self.iteration_filter is not None:
            if isinstance(self.iteration_filter, int):
                if event.iteration != self.iteration_filter:
                    return False
            # "last" はメタデータから判定
            elif self.iteration_filter == "last":
                if not event.metadata.get("is_last_iteration", False):
                    return False

        # 7. カスタム述語
        if self.custom_predicate is not None:
            if not self.custom_predicate(event):
                return False

        # 8. 頻度制限
        if self.frequency > 1:
            self._counter += 1
            if self._counter % self.frequency != 0:
                return False

        return True


# =============================================================================
# Base Subscriber
# =============================================================================

class BaseSubscriber:
    """全 subscriber の基底クラス

    Phase 2: ActivationPolicy に基づく should_activate() を提供。
    Phase 3: score() による情報価値の自己評価を提供。

    FEP 同型:
        EFE:    π* = argmin G(π)     — 最小自由エネルギーの方策を選ぶ
        Phase3: m* = argmax score(m) — 最大情報価値のモジュールを選ぶ

    サブクラスは handle() を必ず、score() を任意でオーバーライドする。
    """

    def __init__(
        self,
        name: str,
        policy: Optional[ActivationPolicy] = None,
        fire_threshold: float = 0.0,
        enable_adaptive_threshold: bool = False,
        ema_alpha: float = 0.1,  # 学習率
    ):
        self._name = name
        self.policy = policy or ActivationPolicy()
        self.fire_threshold = fire_threshold
        
        # Phase 4a: Adaptive Threshold (EMA)
        self.enable_adaptive_threshold = enable_adaptive_threshold
        self.ema_alpha = ema_alpha
        self.min_threshold = max(0.0, fire_threshold - 0.3)
        self.max_threshold = min(1.0, fire_threshold + 0.3)
        
        self._activation_count = 0
        self._skip_count = 0
        self._score_history: List[float] = []
        
        # Phase 4a: Stigmergy 共有環境への参照
        self.stigmergy_context: Optional['StigmergyContext'] = None

    @property
    def name(self) -> str:
        return self._name

    def should_activate(self, event: CognitionEvent) -> bool:
        """自律発火判定 (Phase 3b: 分散ルーティング)

        1. ActivationPolicy による前提条件 (event_types, pattern等) を評価。
        2. 前提をクリアした場合、自身の情報価値 (score) を評価。
        3. score が自身の閾値 (fire_threshold) を超えれば自律発火する。
        """
        # 1. 前提条件のチェック
        base_result = self.policy.evaluate(event)
        if not base_result:
            self._skip_count += 1
            return False

        # 2. 自律スコアの評価
        s = self.score(event)
        
        # 3. 閾値判定
        result = s >= self.fire_threshold
        if result:
            self._activation_count += 1
            if self.enable_adaptive_threshold:
                # 発火時: threshold はスコアに近づく (刺激への馴化)
                target = s
                self.fire_threshold = self.fire_threshold * (1 - self.ema_alpha) + target * self.ema_alpha
        else:
            self._skip_count += 1
            if self.enable_adaptive_threshold:
                # 非発火時: threshold は徐々に下がる (感度の回復)
                target = max(0.0, self.fire_threshold - 0.1)
                self.fire_threshold = self.fire_threshold * (1 - self.ema_alpha) + target * self.ema_alpha

        if self.enable_adaptive_threshold:
            # 安全のためクランプ
            self.fire_threshold = max(self.min_threshold, min(self.max_threshold, self.fire_threshold))
            
        return result

    def score(self, event: CognitionEvent) -> float:
        """この subscriber の現在の情報価値を 0.0-1.0 で返す (Phase 3)

        デフォルト実装: エントロピー変化量の絶対値。
        エントロピーが大きく変化するコンテキストほど、
        このモジュールの介入価値が高い。

        サブクラスでオーバーライドして、ドメイン固有のスコアを返す。
        """
        # デフォルト: エントロピー変化量の絶対値 (0.0-1.0 にクランプ)
        delta = abs(event.entropy_delta)
        s = min(delta, 1.0)
        self._score_history.append(s)
        return s

    def handle(self, event: CognitionEvent) -> Optional[str]:
        """イベントを処理 (サブクラスでオーバーライド)"""
        raise NotImplementedError

    def bind_environment(self, context: 'StigmergyContext') -> None:
        """Phase 4a: 環境 (StigmergyContext) の注入"""
        self.stigmergy_context = context

    def leave_trace(self, event: CognitionEvent, payload: Dict[str, Any], intensity: Optional[float] = None) -> None:
        """Phase 4a: StigmergyContext に痕跡を残す"""
        ctx = self.stigmergy_context
        if not ctx:
            return
            
        from .stigmergy import Trace
        
        # Git-like heads: 今この対象イベントに積まれている最新の痕跡 ID 郡を親とする
        parent_ids = [t.id for t in ctx.get_event_heads(event.event_id)]
        
        # カスケード深度
        depth = 0
        if parent_ids:
            parent_trace = ctx.get_trace(parent_ids[-1])
            if parent_trace:
                depth = parent_trace.cascade_depth + 1
                
        # 強度のデフォルトは直近の score
        actual_intensity = intensity if intensity is not None else (self._score_history[-1] if self._score_history else 0.0)

        trace = Trace(
            subscriber_name=self.name,
            event_id=event.event_id,
            parent_ids=parent_ids,
            intensity=actual_intensity,
            payload=payload,
            cascade_depth=depth
        )
        ctx.add_trace(trace)

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "activations": self._activation_count,
            "skips": self._skip_count,
            "avg_score": (
                sum(self._score_history) / len(self._score_history)
                if self._score_history else 0.0
            ),
            "score_count": len(self._score_history),
        }

    def __repr__(self) -> str:
        avg = self.stats["avg_score"]
        return (
            f"{self.__class__.__name__}("
            f"name='{self._name}', "
            f"activations={self._activation_count}, "
            f"avg_score={avg:.3f})"
        )


# =============================================================================
# Preset Policies
# =============================================================================

class PresetPolicies:
    """よく使う ActivationPolicy のプリセット集

    各モジュールの特性に合わせた最適な発火条件。
    """

    @staticmethod
    def always() -> ActivationPolicy:
        """常に発火 (ログ用)"""
        return ActivationPolicy()

    @staticmethod
    def on_entropy_change(threshold: float = 0.1) -> ActivationPolicy:
        """エントロピーが閾値以上変化した時のみ"""
        return ActivationPolicy(min_entropy_delta=threshold)

    @staticmethod
    def on_high_entropy(threshold: float = 0.6) -> ActivationPolicy:
        """エントロピーが高い (不確実性が高い) 時のみ"""
        return ActivationPolicy(min_entropy=threshold)

    @staticmethod
    def on_verification() -> ActivationPolicy:
        """V:{} ブロック完了時のみ"""
        return ActivationPolicy(
            event_types={EventType.VERIFICATION},
        )

    @staticmethod
    def on_convergence() -> ActivationPolicy:
        """C:{} ループのイテレーション完了時のみ"""
        return ActivationPolicy(
            event_types={EventType.CONVERGENCE_ITER},
        )

    @staticmethod
    def on_convergence_last() -> ActivationPolicy:
        """C:{} ループの最終イテレーション時のみ"""
        return ActivationPolicy(
            event_types={EventType.CONVERGENCE_ITER},
            iteration_filter="last",
        )

    @staticmethod
    def on_step_with_nodes(patterns: List[str]) -> ActivationPolicy:
        """特定のノードパターンにマッチした STEP_COMPLETE のみ"""
        return ActivationPolicy(
            event_types={EventType.STEP_COMPLETE},
            node_patterns=patterns,
        )

    @staticmethod
    def sampled(frequency: int = 3) -> ActivationPolicy:
        """N回に1回だけ発火 (重い処理の間引き)"""
        return ActivationPolicy(frequency=frequency)
