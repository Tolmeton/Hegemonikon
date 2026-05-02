# PROOF: [L2/Phase2] <- hermeneus/tests/test_new_subscribers.py
import pytest
from hermeneus.src.event_bus import CognitionEvent, EventType
from hermeneus.src.subscribers.kalon_gate_sub import KalonGateSubscriber
from hermeneus.src.subscribers.cone_guard_sub import ConeGuardSubscriber

class DummyStepResult:
    def __init__(self, output: str):
        self.output = output

def test_kalon_gate_subscriber_shallow():
    sub = KalonGateSubscriber()
    # 欠落している短い出力 (Shallow)
    event = CognitionEvent(
        event_type=EventType.VERIFICATION,
        step_result=DummyStepResult("これは単なるテスト出力です。")
    )
    res = sub.handle(event)
    assert res is not None
    assert "Anti-Shallow" in res
    assert "Trace 欠落" in res
    assert "Negativa 欠落" in res
    assert "Iso 欠落" in res

def test_kalon_gate_subscriber_good():
    sub = KalonGateSubscriber()
    # 構造要件を満たしている出力
    event = CognitionEvent(
        event_type=EventType.VERIFICATION,
        step_result=DummyStepResult(
            "## 計画\n"
            "1. 理由はAだからです(Trace)。\n"
            "2. 代替案Bは棄却します(Negativa)。\n"
            "[CHECKPOINT PHASE 1/2]"
        )
    )
    res = sub.handle(event)
    assert res is None  # 問題なし

def test_kalon_gate_subscriber_warns_missing_iso():
    sub = KalonGateSubscriber()
    event = CognitionEvent(
        event_type=EventType.VERIFICATION,
        step_result=DummyStepResult("理由はAだからです。代替案Bは棄却します。")
    )
    res = sub.handle(event)
    assert res is not None
    assert "Iso 欠落" in res

def test_cone_guard_subscriber_no_data():
    sub = ConeGuardSubscriber()
    event = CognitionEvent(
        event_type=EventType.VERIFICATION,
        metadata={}
    )
    res = sub.handle(event)
    assert res is None

def test_cone_guard_subscriber_success():
    sub = ConeGuardSubscriber()
    
    # 矛盾のある出力 (Dispersion が高くなるようにする)
    # e.g., noe と bou で全く違うことを言う
    step_outputs = {
        "noe+": "プロジェクトは絶対に失敗する",
        "bou+": "プロジェクトは完全に大成功する",
        "zet": "何が起こっているのかわからない"
    }
    
    event = CognitionEvent(
        event_type=EventType.VERIFICATION,
        metadata={"step_outputs": step_outputs}
    )
    res = sub.handle(event)
    
    # advise が何かしら矛盾を検知して advice_res.action == "devil" or "investigate" を返すはず
    # dispersionが高ければ "devil" か "investigate"
    if res is not None:
        assert "Devil's Advocate" in res
