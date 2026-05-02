"""
DriftGuardSubscriber のテスト

テスト対象:
    1. DRIFT_ALERT イベントで handle() が発火する
    2. score() がドリフトスコアを反映する
    3. use_llm=False で LLM スキップモードが動作する
    4. メタデータに prev/curr_output があるときの出力フォーマット
    5. __init__.py の create_default_subscribers に含まれる
"""
import pytest
from unittest.mock import MagicMock, patch

from hermeneus.src.event_bus import CognitionEvent, CognitionEventBus, EventType
from hermeneus.src.subscribers.drift_guard_sub import DriftGuardSubscriber, DriftAlert


class TestDriftGuardSubscriber:
    """DriftGuardSubscriber のユニットテスト"""

    def _make_drift_event(
        self,
        drift: float = 0.85,
        source_node: str = "/dia",
        prev_step: str = "/noe",
        prev_output: str = "前ステップの出力",
        curr_output: str = "現ステップの出力",
    ) -> CognitionEvent:
        return CognitionEvent(
            event_type=EventType.DRIFT_ALERT,
            source_node=source_node,
            entropy_before=0.5,
            entropy_after=0.8,
            metadata={
                "drift": drift,
                "prev_step": prev_step,
                "step": source_node,
                "prev_output": prev_output,
                "curr_output": curr_output,
            },
        )

    def test_subscribes_to_drift_alert(self):
        """DRIFT_ALERT に subscribe している"""
        sub = DriftGuardSubscriber(use_llm=False)
        assert EventType.DRIFT_ALERT in sub.policy.event_types

    def test_score_reflects_drift(self):
        """score() はドリフトスコアをそのまま返す"""
        sub = DriftGuardSubscriber(use_llm=False)

        event_high = self._make_drift_event(drift=0.95)
        event_low = self._make_drift_event(drift=0.3)

        assert sub.score(event_high) == pytest.approx(0.95)
        assert sub.score(event_low) == pytest.approx(0.3)

    def test_handle_no_llm_skips_verification(self):
        """use_llm=False のとき、verify_step をスキップしログのみ"""
        sub = DriftGuardSubscriber(use_llm=False)
        event = self._make_drift_event(drift=0.88)

        result = sub.handle(event)

        assert result is not None
        assert "Drift detected" in result
        assert "verification skipped" in result
        assert len(sub.alerts) == 1
        assert sub.alerts[0].verdict_type == "SKIPPED"
        assert sub.alerts[0].drift_score == pytest.approx(0.88)

    def test_handle_no_output_skips(self):
        """prev_output/curr_output がない場合もスキップ"""
        sub = DriftGuardSubscriber(use_llm=True)
        event = self._make_drift_event(prev_output="", curr_output="")

        result = sub.handle(event)

        assert "skipped" in result
        assert sub.alerts[0].verdict_type == "SKIPPED"

    def test_handle_with_llm_calls_verify_step(self):
        """use_llm=True のとき、verify_step が呼ばれる"""
        sub = DriftGuardSubscriber(use_llm=True)
        event = self._make_drift_event()

        mock_verdict = MagicMock()
        mock_verdict.type.value = "ACCEPT"
        mock_verdict.confidence = 0.85
        mock_verdict.reasoning = "論理的に妥当"

        with patch("hermeneus.src.subscribers.drift_guard_sub.verify_step",
                   create=True) as mock_vs:
            # verify_step はモジュールレベルではなく handle 内で import されるので
            # hermeneus.src.verifier.verify_step を patch
            pass

        # verify_step を直接 patch
        with patch("hermeneus.src.verifier.verify_step", return_value=mock_verdict):
            result = sub.handle(event)

        assert "ACCEPT" in result
        assert "85%" in result
        assert len(sub.alerts) == 1
        assert sub.alerts[0].verdict_type == "ACCEPT"
        
        # event.metadata への書き戻し確認
        assert event.metadata["drift_verdict"] == "ACCEPT"
        assert event.metadata["drift_verdict_confidence"] == 0.85
        assert "drift_rejected" not in event.metadata

    def test_handle_reject_sets_flag(self):
        """REJECT 判定時に drift_rejected=True が metadata に設定される"""
        sub = DriftGuardSubscriber(use_llm=True)
        event = self._make_drift_event()

        mock_verdict = MagicMock()
        mock_verdict.type.value = "REJECT"
        mock_verdict.confidence = 0.90
        mock_verdict.reasoning = "文脈が完全に断絶している"

        with patch("hermeneus.src.verifier.verify_step", return_value=mock_verdict):
            result = sub.handle(event)

        assert "REJECT" in result
        assert event.metadata["drift_verdict"] == "REJECT"
        assert event.metadata["drift_rejected"] is True

    def test_handle_verify_step_error(self):
        """verify_step がエラーを投げてもクラッシュしない"""
        sub = DriftGuardSubscriber(use_llm=True)
        event = self._make_drift_event()

        with patch("hermeneus.src.verifier.verify_step",
                   side_effect=RuntimeError("LLM unavailable")):
            result = sub.handle(event)

        assert result is not None
        assert "error" in result.lower()
        assert len(sub.alerts) == 1
        assert sub.alerts[0].verdict_type == "ERROR"

    def test_eventbus_integration(self):
        """EventBus 経由で DRIFT_ALERT を受信して発火する"""
        bus = CognitionEventBus()
        sub = DriftGuardSubscriber(use_llm=False)
        bus.subscribe(EventType.DRIFT_ALERT, sub)

        event = self._make_drift_event()
        outputs = bus.emit(event)

        assert len(outputs) == 1
        assert "Drift detected" in outputs[0]
        assert bus.stats["total_activations"] == 1

    def test_reset_clears_alerts(self):
        """reset() でアラートがクリアされる"""
        sub = DriftGuardSubscriber(use_llm=False)
        sub.handle(self._make_drift_event())
        assert len(sub.alerts) == 1

        sub.reset()
        assert len(sub.alerts) == 0

    def test_cache_avoids_duplicate_calls(self):
        """同一入出力に対して verify_step は 1 回のみ呼ばれる"""
        sub = DriftGuardSubscriber(use_llm=True)

        mock_verdict = MagicMock()
        mock_verdict.type.value = "ACCEPT"
        mock_verdict.confidence = 0.9
        mock_verdict.reasoning = "OK"

        with patch("hermeneus.src.verifier.verify_step", return_value=mock_verdict) as mock_vs:
            # 同一入力で 2 回呼ぶ
            sub.handle(self._make_drift_event())
            sub.handle(self._make_drift_event())

            # verify_step は 1 回だけ
            assert mock_vs.call_count == 1

        assert sub.cache_stats["hits"] == 1
        assert sub.cache_stats["misses"] == 1
        assert sub.cache_stats["size"] == 1

    def test_reset_clears_cache(self):
        """reset() でキャッシュもクリアされる"""
        sub = DriftGuardSubscriber(use_llm=False)
        sub.handle(self._make_drift_event())
        sub.reset()
        assert sub.cache_stats["size"] == 0
        assert sub.cache_stats["hits"] == 0

    def test_cache_ttl_expires(self):
        """TTL を経過するとキャッシュミスになり、再検証される"""
        # TTL を 0.1 秒に設定
        sub = DriftGuardSubscriber(use_llm=True, cache_ttl=0.1)

        mock_verdict = MagicMock()
        mock_verdict.type.value = "ACCEPT"
        mock_verdict.confidence = 0.9
        mock_verdict.reasoning = "OK"

        with patch("hermeneus.src.verifier.verify_step", return_value=mock_verdict) as mock_vs:
            # 1回目 (キャッシュミス → 保存)
            sub.handle(self._make_drift_event())
            assert mock_vs.call_count == 1
            assert sub.cache_stats["misses"] == 1
            assert sub.cache_stats["hits"] == 0

            # 2回目 直後 (キャッシュヒット)
            sub.handle(self._make_drift_event())
            assert mock_vs.call_count == 1
            assert sub.cache_stats["hits"] == 1

            # TTL 経過待ち
            import time
            time.sleep(0.15)

            # 3回目 (TTL 切れ → キャッシュミス → 再検証)
            sub.handle(self._make_drift_event())
            assert mock_vs.call_count == 2
            assert sub.cache_stats["misses"] == 2

    def test_name_is_drift_guard(self):
        """subscriber 名が 'drift_guard'"""
        sub = DriftGuardSubscriber()
        assert sub.name == "drift_guard"


class TestDriftGuardInDefaultSubscribers:
    """DriftGuardSubscriber が create_default_subscribers に含まれる"""

    def test_included_in_defaults(self):
        """create_default_subscribers に DriftGuardSubscriber がある"""
        from hermeneus.src.subscribers import create_default_subscribers
        subs = create_default_subscribers()
        names = [s.name for s in subs]
        assert "drift_guard" in names

    def test_included_in_all(self):
        """create_all_subscribers に DriftGuardSubscriber がある"""
        from hermeneus.src.subscribers import create_all_subscribers
        subs = create_all_subscribers()
        names = [s.name for s in subs]
        assert "drift_guard" in names


class TestCreateVerifyGuard:
    """create_verify_guard ファクトリのテスト"""

    def test_creates_guard_for_entropy_change(self):
        """ENTROPY_CHANGE 用ガードが生成される"""
        from hermeneus.src.subscribers.drift_guard_sub import create_verify_guard
        guard = create_verify_guard(
            EventType.ENTROPY_CHANGE, "entropy_guard",
            score_key="entropy_delta", use_llm=False,
        )
        assert guard.name == "entropy_guard"
        assert EventType.ENTROPY_CHANGE in guard.policy.event_types
        assert guard._score_key == "entropy_delta"

    def test_factory_guard_scores_with_custom_key(self):
        """カスタム score_key でスコアリングする"""
        from hermeneus.src.subscribers.drift_guard_sub import create_verify_guard
        guard = create_verify_guard(
            EventType.ENTROPY_CHANGE, "entropy_guard",
            score_key="entropy_delta", use_llm=False,
        )
        event = CognitionEvent(
            event_type=EventType.ENTROPY_CHANGE,
            source_node="/test",
            entropy_before=0.3, entropy_after=0.9,
            metadata={"entropy_delta": 0.6},
        )
        assert guard.score(event) == pytest.approx(0.6)

    def test_factory_guard_handles_event(self):
        """ファクトリで生成したガードもイベントを処理できる"""
        from hermeneus.src.subscribers.drift_guard_sub import create_verify_guard
        guard = create_verify_guard(
            EventType.ENTROPY_CHANGE, "entropy_guard",
            score_key="entropy_delta", use_llm=False,
        )
        event = CognitionEvent(
            event_type=EventType.ENTROPY_CHANGE,
            source_node="/test",
            entropy_before=0.3, entropy_after=0.9,
            metadata={"drift": 0.75, "prev_output": "", "curr_output": ""},
        )
        result = guard.handle(event)
        assert result is not None
        assert len(guard.alerts) == 1
