# PROOF: [L2/Phase2] <- hermeneus/tests/test_event_bus.py
"""
Phase 2 イベント駆動アーキテクチャのテストスイート

テスト対象:
    1. EventBus の subscribe/emit/unsubscribe
    2. ActivationPolicy の条件評価
    3. BaseSubscriber の発火判定
    4. MacroExecutor + EventBus の結合テスト
    5. Subscriber の発火テスト
"""
import pytest
import time
from unittest.mock import MagicMock, patch

from hermeneus.src.event_bus import (
    CognitionEvent,
    CognitionEventBus,
    EventError,
    EventType,
)
from hermeneus.src.activation import (
    ActivationPolicy,
    BaseSubscriber,
    PresetPolicies,
)
from hermeneus.src.subscribers.convergence_sub import (
    ConvergenceSubscriber,
    ConvergenceMetric,
)
from hermeneus.src.subscribers.synteleia_sub import (
    SynteleiaSubscriber,
    QualityAlert,
)


# =============================================================================
# Helper: Simple Test Subscriber
# =============================================================================

class SimpleSubscriber(BaseSubscriber):
    """テスト用の単純な subscriber"""

    def __init__(self, name="test_sub", policy=None):
        super().__init__(name=name, policy=policy or ActivationPolicy())
        self.received_events = []

    def handle(self, event: CognitionEvent):
        self.received_events.append(event)
        return f"handled:{event.source_node}"


class FailingSubscriber(BaseSubscriber):
    """エラーを投げる subscriber (エラー隔離テスト用)"""

    def __init__(self):
        super().__init__(name="failing_sub")

    def handle(self, event: CognitionEvent):
        raise ValueError("Intentional test error")


# =============================================================================
# EventBus Tests
# =============================================================================

class TestCognitionEventBus:
    """EventBus のコアテスト"""

    def test_subscribe_and_emit(self):
        """subscribe して emit するとハンドラが呼ばれる"""
        bus = CognitionEventBus()
        sub = SimpleSubscriber()
        bus.subscribe(EventType.STEP_COMPLETE, sub)

        event = CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            source_node="/noe",
        )
        outputs = bus.emit(event)

        assert len(sub.received_events) == 1
        assert sub.received_events[0].source_node == "/noe"
        assert outputs == ["handled:/noe"]

    def test_subscribe_wrong_type_no_fire(self):
        """subscribe していないイベントタイプでは発火しない"""
        bus = CognitionEventBus()
        sub = SimpleSubscriber()
        bus.subscribe(EventType.VERIFICATION, sub)

        event = CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            source_node="/noe",
        )
        bus.emit(event)

        assert len(sub.received_events) == 0

    def test_subscribe_all(self):
        """subscribe_all で全イベントタイプに対して発火"""
        bus = CognitionEventBus()
        sub = SimpleSubscriber()
        bus.subscribe_all(sub)

        for et in [EventType.STEP_COMPLETE, EventType.VERIFICATION]:
            bus.emit(CognitionEvent(event_type=et, source_node="test"))

        assert len(sub.received_events) == 2

    def test_unsubscribe(self):
        """unsubscribe 後は発火しない"""
        bus = CognitionEventBus()
        sub = SimpleSubscriber()
        bus.subscribe(EventType.STEP_COMPLETE, sub)
        bus.unsubscribe(EventType.STEP_COMPLETE, sub)

        bus.emit(CognitionEvent(event_type=EventType.STEP_COMPLETE))
        assert len(sub.received_events) == 0

    def test_error_isolation(self):
        """1つの subscriber のエラーが他に影響しない"""
        bus = CognitionEventBus()
        failing_sub = FailingSubscriber()
        good_sub = SimpleSubscriber(name="good_sub")

        bus.subscribe(EventType.STEP_COMPLETE, failing_sub)
        bus.subscribe(EventType.STEP_COMPLETE, good_sub)

        event = CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            source_node="/test",
        )
        bus.emit(event)

        # good_sub は影響を受けない
        assert len(good_sub.received_events) == 1
        # エラーが記録されている
        assert bus.stats["total_errors"] == 1
        assert len(bus.errors) == 1
        assert "Intentional test error" in str(bus.errors[0].error)

    def test_disabled_bus(self):
        """enabled=False の時は emit しない"""
        bus = CognitionEventBus(enabled=False)
        sub = SimpleSubscriber()
        bus.subscribe(EventType.STEP_COMPLETE, sub)

        bus.emit(CognitionEvent(event_type=EventType.STEP_COMPLETE))
        assert len(sub.received_events) == 0

    def test_stats_tracking(self):
        """統計が正しく追跡される"""
        bus = CognitionEventBus()
        sub = SimpleSubscriber()
        bus.subscribe(EventType.STEP_COMPLETE, sub)

        for _ in range(5):
            bus.emit(CognitionEvent(event_type=EventType.STEP_COMPLETE))

        assert bus.stats["total_emits"] == 5
        assert bus.stats["total_activations"] == 5

    def test_output_collection(self):
        """subscriber の出力が収集される"""
        bus = CognitionEventBus()
        sub = SimpleSubscriber()
        bus.subscribe(EventType.STEP_COMPLETE, sub)

        bus.emit(CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            source_node="/noe",
        ))

        outputs = bus.collect_outputs()
        assert len(outputs) == 1
        assert outputs[0]["subscriber"] == "test_sub"
        assert outputs[0]["output"] == "handled:/noe"

    def test_flush_outputs(self):
        """flush_outputs で出力がクリアされる"""
        bus = CognitionEventBus()
        sub = SimpleSubscriber()
        bus.subscribe(EventType.STEP_COMPLETE, sub)

        bus.emit(CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            source_node="/noe",
        ))

        flushed = bus.flush_outputs()
        assert len(flushed) == 1
        assert len(bus.collect_outputs()) == 0  # クリア済み

    def test_list_subscribers(self):
        """subscriber 一覧が取得できる"""
        bus = CognitionEventBus()
        bus.subscribe(EventType.STEP_COMPLETE, SimpleSubscriber(name="a"))
        bus.subscribe(EventType.VERIFICATION, SimpleSubscriber(name="b"))

        all_subs = bus.list_subscribers()
        assert "a" in all_subs
        assert "b" in all_subs

        step_subs = bus.list_subscribers(EventType.STEP_COMPLETE)
        assert "a" in step_subs
        assert "b" not in step_subs

    def test_repr(self):
        """repr が正しく動作する"""
        bus = CognitionEventBus()
        assert "enabled=True" in repr(bus)


# =============================================================================
# ActivationPolicy Tests
# =============================================================================

class TestActivationPolicy:
    """ActivationPolicy の条件評価テスト"""

    def test_default_always_true(self):
        """デフォルトポリシーは常に True"""
        policy = ActivationPolicy()
        event = CognitionEvent(event_type=EventType.STEP_COMPLETE)
        assert policy.evaluate(event) is True

    def test_event_type_filter(self):
        """イベントタイプでフィルタリング"""
        policy = ActivationPolicy(
            event_types={EventType.VERIFICATION},
        )
        assert policy.evaluate(CognitionEvent(
            event_type=EventType.VERIFICATION,
        )) is True
        assert policy.evaluate(CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
        )) is False

    def test_entropy_delta_filter(self):
        """エントロピー変化量でフィルタリング"""
        policy = ActivationPolicy(min_entropy_delta=0.1)

        # 変化量が大きい → True
        event_big = CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            entropy_before=0.5,
            entropy_after=0.2,
        )
        assert policy.evaluate(event_big) is True

        # 変化量が小さい → False
        event_small = CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            entropy_before=0.5,
            entropy_after=0.49,
        )
        assert policy.evaluate(event_small) is False

    def test_entropy_range_filter(self):
        """エントロピー範囲でフィルタリング"""
        policy = ActivationPolicy(min_entropy=0.5, max_entropy=0.9)

        # 範囲内 → True
        assert policy.evaluate(CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            entropy_after=0.7,
        )) is True

        # 範囲外 → False
        assert policy.evaluate(CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            entropy_after=0.3,
        )) is False

    def test_node_pattern_filter(self):
        """ノードパターンでフィルタリング"""
        policy = ActivationPolicy(node_patterns=["noe", "dia"])

        assert policy.evaluate(CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            source_node="/noe",
        )) is True
        assert policy.evaluate(CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            source_node="/tek",
        )) is False

    def test_exclude_pattern_filter(self):
        """除外パターンでフィルタリング"""
        policy = ActivationPolicy(exclude_patterns=["dox"])

        assert policy.evaluate(CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            source_node="/noe",
        )) is True
        assert policy.evaluate(CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            source_node="/dox",
        )) is False

    def test_frequency_filter(self):
        """頻度制限でフィルタリング"""
        policy = ActivationPolicy(frequency=3)

        results = []
        for _ in range(9):
            results.append(policy.evaluate(CognitionEvent(
                event_type=EventType.STEP_COMPLETE,
            )))

        # 3回に1回だけ True
        assert results.count(True) == 3

    def test_custom_predicate(self):
        """カスタム述語でフィルタリング"""
        policy = ActivationPolicy(
            custom_predicate=lambda e: "important" in e.metadata.get("tag", ""),
        )

        assert policy.evaluate(CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            metadata={"tag": "important"},
        )) is True
        assert policy.evaluate(CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            metadata={"tag": "trivial"},
        )) is False

    def test_preset_always(self):
        """PresetPolicies.always() は常に True"""
        policy = PresetPolicies.always()
        assert policy.evaluate(CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
        )) is True

    def test_preset_on_verification(self):
        """PresetPolicies.on_verification() は VERIFICATION のみ"""
        policy = PresetPolicies.on_verification()
        assert policy.evaluate(CognitionEvent(
            event_type=EventType.VERIFICATION,
        )) is True
        assert policy.evaluate(CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
        )) is False


# =============================================================================
# Subscriber Tests
# =============================================================================

class TestConvergenceSubscriber:
    """ConvergenceSubscriber のテスト"""

    def test_collects_metrics(self):
        """CONVERGENCE_ITER で メトリクスが収集される"""
        sub = ConvergenceSubscriber()

        event = CognitionEvent(
            event_type=EventType.CONVERGENCE_ITER,
            entropy_before=0.8,
            entropy_after=0.5,
            iteration=0,
            metadata={"similarity": 0.6, "delta_skip": False},
        )

        result = sub.handle(event)
        assert result is None  # ログのみ
        assert len(sub.metrics) == 1
        assert sub.metrics[0].entropy_delta == pytest.approx(-0.3, abs=0.01)

    def test_summary_on_execution_complete(self):
        """EXECUTION_COMPLETE でサマリーが生成される"""
        sub = ConvergenceSubscriber()

        # メトリクス追加
        sub.handle(CognitionEvent(
            event_type=EventType.CONVERGENCE_ITER,
            entropy_before=0.8,
            entropy_after=0.5,
            iteration=0,
        ))
        sub.handle(CognitionEvent(
            event_type=EventType.CONVERGENCE_ITER,
            entropy_before=0.5,
            entropy_after=0.3,
            iteration=1,
        ))

        # サマリー生成
        summary = sub.handle(CognitionEvent(
            event_type=EventType.EXECUTION_COMPLETE,
        ))
        assert summary is not None
        assert "収束トラッカー" in summary
        assert "イテレーション数" in summary


class TestSynteleiaSubscriber:
    """SynteleiaSubscriber のテスト"""

    def test_detects_empty_output(self):
        """短すぎる出力を検出する"""
        sub = SynteleiaSubscriber()

        mock_result = MagicMock()
        mock_result.output = "short"
        mock_result.node_id = "/test"
        mock_result.entropy_before = 0.5
        mock_result.entropy_after = 0.4

        event = CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            step_result=mock_result,
            source_node="/test",
        )
        sub.handle(event)

        assert len(sub.alerts) == 1
        assert sub.alerts[0].category == "empty_output"

    def test_detects_unresolved_refs(self):
        """未解決参照を検出する"""
        sub = SynteleiaSubscriber()

        mock_result = MagicMock()
        mock_result.output = "This has a TODO marker and needs FIXME attention " * 5
        mock_result.node_id = "/test"
        mock_result.entropy_before = 0.5
        mock_result.entropy_after = 0.3

        event = CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            step_result=mock_result,
        )
        sub.handle(event)

        unresolved_alerts = [a for a in sub.alerts if a.category == "unresolved_refs"]
        assert len(unresolved_alerts) >= 1

    def test_detects_entropy_increase(self):
        """エントロピー増大を検出する"""
        sub = SynteleiaSubscriber()

        mock_result = MagicMock()
        mock_result.output = "Some structured output\n- Item 1\n- Item 2\n| Col | Val |\n" * 5
        mock_result.node_id = "/test"
        mock_result.entropy_before = 0.3
        mock_result.entropy_after = 0.8  # 増大

        event = CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            step_result=mock_result,
        )
        sub.handle(event)

        entropy_alerts = [a for a in sub.alerts if a.category == "entropy_increase"]
        assert len(entropy_alerts) == 1
        assert entropy_alerts[0].level == "error"


# =============================================================================
# MacroExecutor Integration Tests
# =============================================================================

class TestMacroExecutorEventBusIntegration:
    """MacroExecutor + EventBus の結合テスト"""

    def test_backward_compatible_no_bus(self):
        """event_bus=None で従来通り動作する (後方互換)"""
        from hermeneus.src.macro_executor import MacroExecutor

        executor = MacroExecutor()  # event_bus なし
        result = executor.execute("/noe_/dia", context="test")

        assert result.success
        assert len(result.steps) > 0

    def test_with_event_bus(self):
        """EventBus を渡すとイベントが emit される"""
        from hermeneus.src.macro_executor import MacroExecutor

        bus = CognitionEventBus()
        sub = SimpleSubscriber()
        bus.subscribe(EventType.STEP_COMPLETE, sub)

        executor = MacroExecutor(event_bus=bus)
        result = executor.execute("/noe_/dia", context="test")

        assert result.success
        # STEP_COMPLETE イベントが発火している
        assert len(sub.received_events) > 0
        # イベントに source_node が含まれる
        nodes = [e.source_node for e in sub.received_events]
        assert any("/noe" in n for n in nodes)
        # 統計が更新されている
        assert bus.stats["total_emits"] > 0

    def test_with_convergence_subscriber(self):
        """ConvergenceSubscriber が C:{} で動作する"""
        from hermeneus.src.macro_executor import MacroExecutor

        bus = CognitionEventBus()
        conv_sub = ConvergenceSubscriber()
        bus.subscribe(EventType.CONVERGENCE_ITER, conv_sub)
        bus.subscribe(EventType.EXECUTION_COMPLETE, conv_sub)

        executor = MacroExecutor(event_bus=bus)
        result = executor.execute("C:{/noe_/dia}", context="test convergence")

        assert result.success
        # 収束メトリクスが収集されている
        # CognitiveStepHandler はテンプレート応答なので高速収束する場合がある
        assert len(conv_sub.metrics) >= 1

    def test_with_synteleia_subscriber(self):
        """SynteleiaSubscriber が品質スキャンを行う"""
        from hermeneus.src.macro_executor import MacroExecutor

        bus = CognitionEventBus()
        syn_sub = SynteleiaSubscriber(fire_threshold=0.0)  # テスト環境では常に発火
        bus.subscribe(EventType.STEP_COMPLETE, syn_sub)

        executor = MacroExecutor(event_bus=bus)
        result = executor.execute("/noe_/dia", context="test quality")

        assert result.success
        # スキャンが実行された（アラートの有無は出力次第）
        assert syn_sub._activation_count > 0

    def test_execution_complete_event(self):
        """EXECUTION_COMPLETE がマクロ実行完了後に発火する"""
        from hermeneus.src.macro_executor import MacroExecutor

        bus = CognitionEventBus()
        sub = SimpleSubscriber()
        bus.subscribe(EventType.EXECUTION_COMPLETE, sub)

        executor = MacroExecutor(event_bus=bus)
        result = executor.execute("/noe", context="test")

        assert result.success
        assert len(sub.received_events) == 1
        assert sub.received_events[0].event_type == EventType.EXECUTION_COMPLETE
        assert "ccl" in sub.received_events[0].metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
