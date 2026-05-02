# PROOF: [L2/Phase3] <- hermeneus/tests/test_blackboard_e2e.py
# PURPOSE: Blackboard + Dynamic Interleaving + 6 Series + Taxis の統合テスト
"""
Step 1-5 統合テスト

検証項目:
  1. Blackboard の基本操作 (write/read/fill_rate)
  2. emit() が Blackboard を自動初期化
  3. Dynamic Interleaving: score 降順で発火
  4. 6 Series が全て Blackboard に書込み
  5. Taxis が 6 Limit 充填後に自律発火
  6. K₆ 張力計算と矛盾度 V
"""
import pytest

from hermeneus.src.blackboard import CognitionBlackboard
from hermeneus.src.event_bus import CognitionEventBus
from hermeneus.src.events import CognitionEvent, EventType
from hermeneus.src.subscribers.series import (
    ALL_SERIES_SUBSCRIBERS,
    TelosSubscriber,
    MethodosSubscriber,
)
from hermeneus.src.subscribers.taxis_sub import TaxisSubscriber


class TestBlackboardCore:
    """Step 1: CognitionBlackboard の基本操作"""

    def test_write_read(self):
        bb = CognitionBlackboard(query="テスト")
        bb.write("series_limits.T", "目的は明確", source="test")
        assert bb.read("series_limits.T") == "目的は明確"

    def test_series_fill_rate(self):
        bb = CognitionBlackboard()
        assert bb.series_fill_rate == 0.0
        bb.write("series_limits.T", "T", source="t")
        bb.write("series_limits.M", "M", source="m")
        assert bb.series_fill_rate == pytest.approx(2 / 6)

    def test_write_count_and_log(self):
        bb = CognitionBlackboard()
        bb.write("series_limits.T", "val", source="src")
        assert bb.write_count == 1
        assert bb.last_writer("series_limits.T") == "src"

    def test_slots_fallback(self):
        bb = CognitionBlackboard()
        bb.write("custom_key", "custom_val", source="test")
        assert bb.read("custom_key") == "custom_val"


class TestEventBlackboard:
    """Step 2: CognitionEvent.blackboard"""

    def test_event_has_blackboard_field(self):
        event = CognitionEvent(event_type=EventType.MACRO_START)
        assert event.blackboard is None

    def test_event_with_blackboard(self):
        bb = CognitionBlackboard(query="q")
        event = CognitionEvent(event_type=EventType.MACRO_START, blackboard=bb)
        assert event.blackboard is bb

    def test_backward_compat(self):
        """blackboard なしでも event は正常動作"""
        e1 = CognitionEvent(event_type=EventType.MACRO_START)
        assert e1.blackboard is None
        assert e1.event_type == EventType.MACRO_START


class TestDynamicInterleaving:
    """Step 3: emit() が score 降順で発火"""

    def test_emit_creates_blackboard(self):
        bus = CognitionEventBus()
        event = CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            metadata={"context": "テスト"}
        )
        bus.emit(event)
        assert event.blackboard is not None
        assert event.blackboard.query == "テスト"

    def test_score_ordering(self):
        """高 score の Subscriber が先に発火する"""
        bus = CognitionEventBus()
        telos = TelosSubscriber()      # base_score = 0.9
        methodos = MethodosSubscriber() # base_score = 0.8
        # Telos を後に登録
        bus.subscribe(EventType.MACRO_START, methodos)
        bus.subscribe(EventType.MACRO_START, telos)

        event = CognitionEvent(
            event_type=EventType.MACRO_START,
            metadata={"macro_name": "ax", "context": "テスト"}
        )
        outputs = bus.emit(event)
        # Telos (0.9) が Methodos (0.8) より先に発火
        assert len(outputs) == 2
        assert "[T:" in outputs[0]
        assert "[M:" in outputs[1]


class TestSeriesSubscribers:
    """Step 5a: 6 Series"""

    def test_all_6_series_exist(self):
        assert len(ALL_SERIES_SUBSCRIBERS) == 6

    def test_series_fills_blackboard(self):
        bus = CognitionEventBus()
        for SubClass in ALL_SERIES_SUBSCRIBERS:
            bus.subscribe(EventType.MACRO_START, SubClass())

        event = CognitionEvent(
            event_type=EventType.MACRO_START,
            metadata={"macro_name": "ax", "context": "設計方針"}
        )
        outputs = bus.emit(event)

        bb = event.blackboard
        assert bb.series_fill_rate == 1.0  # 6/6
        assert len(bb.series_limits) == 6
        assert "T" in bb.series_limits
        assert "C" in bb.series_limits

    def test_series_score_zero_when_filled(self):
        """充填済み Series は score=0 で発火しない"""
        telos = TelosSubscriber()
        event = CognitionEvent(
            event_type=EventType.MACRO_START,
            metadata={"macro_name": "ax"},
            blackboard=CognitionBlackboard(),
        )
        event.blackboard.series_limits["T"] = "already filled"
        assert telos.score(event) == 0.0


class TestTaxisSubscriber:
    """Step 5b: TaxisSubscriber + K₆"""

    def test_taxis_score_proportional_to_fill(self):
        taxis = TaxisSubscriber()
        bb = CognitionBlackboard()
        event = CognitionEvent(
            event_type=EventType.MACRO_START,
            metadata={"macro_name": "ax"},
            blackboard=bb,
        )
        assert taxis.score(event) == 0.0  # 0/6

        bb.series_limits["T"] = "t"
        bb.series_limits["M"] = "m"
        bb.series_limits["K"] = "k"
        assert taxis.score(event) == pytest.approx(3 / 6)

    def test_taxis_fires_after_all_6(self):
        """6 Series 全充填後に Taxis が自律発火"""
        bus = CognitionEventBus()
        for SubClass in ALL_SERIES_SUBSCRIBERS:
            bus.subscribe(EventType.MACRO_START, SubClass())
        bus.subscribe(EventType.MACRO_START, TaxisSubscriber())

        event = CognitionEvent(
            event_type=EventType.MACRO_START,
            metadata={"macro_name": "ax", "context": "テスト"}
        )
        outputs = bus.emit(event)

        # 7 outputs: 6 Series + 1 Taxis
        non_none = [o for o in outputs if o]
        assert len(non_none) == 7

        # Taxis の出力に K₆ 情報がある
        taxis_output = non_none[-1]
        assert "Taxis" in taxis_output or "K₆" in taxis_output or "矛盾度" in taxis_output

        # Blackboard に統合結論
        bb = event.blackboard
        assert bb.read("slots.taxis_V") is not None
        assert bb.read("slots.taxis_conclusion") is not None

    def test_k6_has_15_edges(self):
        """K₆ 完全グラフは C(6,2) = 15 エッジ"""
        taxis = TaxisSubscriber()
        bb = CognitionBlackboard()
        for k in "TMKDOC":
            bb.series_limits[k] = f"limit_{k}"
        tensions = taxis._compute_k6_tensions(bb)
        assert len(tensions) == 15
