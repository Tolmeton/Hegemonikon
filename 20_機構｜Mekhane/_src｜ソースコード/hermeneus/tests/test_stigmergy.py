import pytest
import time
from hermeneus.src.event_bus import CognitionEvent, EventType
from hermeneus.src.stigmergy import StigmergyContext, CognitionEnvironment, Trace
from hermeneus.src.activation import BaseSubscriber, ActivationPolicy
from hermeneus.src.subscribers.convergence_sub import ConvergenceSubscriber
from hermeneus.src.subscribers.synteleia_sub import SynteleiaSubscriber


def test_stigmergy_context_basic():
    ctx = StigmergyContext(max_traces=10)
    
    # Trace追加
    trace1 = Trace(subscriber_name="sub1", event_id="evt1", intensity=0.5)
    ctx.add_trace(trace1)
    
    # 取得
    assert ctx.get_trace(trace1.id) == trace1
    assert len(ctx.get_recent_traces()) == 1
    
    # Subscriberによる取得
    assert len(ctx.get_traces_by_subscriber("sub1")) == 1
    assert len(ctx.get_traces_by_subscriber("sub2")) == 0
    
    # Heads
    heads = ctx.get_event_heads("evt1")
    assert len(heads) == 1
    assert heads[0].id == trace1.id


def test_stigmergy_context_pruning():
    ctx = StigmergyContext(max_traces=10)
    
    # 最大件数を超える痕跡を追加
    # prune_count = max(1, 10//10) = 1. So every time it exceeds 10, it removes 1.
    for i in range(12):
        ctx.add_trace(Trace(subscriber_name=f"sub{i}", event_id="evt2"))
        
    assert len(ctx.get_recent_traces(100)) == 10
    assert len(ctx._trace_log) == 10


def test_stigmergy_context_cascade_limit():
    ctx = StigmergyContext(max_cascade_depth=3)
    
    t1 = Trace(cascade_depth=0)
    t2 = Trace(cascade_depth=1)
    t3 = Trace(cascade_depth=3)
    t4 = Trace(cascade_depth=4) # オーバー
    
    ctx.add_trace(t1)
    ctx.add_trace(t2)
    ctx.add_trace(t3)
    ctx.add_trace(t4)
    
    assert len(ctx.get_recent_traces()) == 3
    assert ctx.get_trace(t4.id) is None


class DummySubscriber(BaseSubscriber):
    def score(self, event: CognitionEvent) -> float:
        s = getattr(event, "dummy_score", 0.5)
        self._score_history.append(s)
        return s
        
    def handle(self, event: CognitionEvent) -> None:
        self.leave_trace(event, payload={})


def test_adaptive_threshold_behavior():
    sub = DummySubscriber(
        name="test_sub", 
        fire_threshold=0.5, 
        enable_adaptive_threshold=True,
        ema_alpha=0.5
    )
    
    evt_fire = CognitionEvent(event_type=EventType.STEP_COMPLETE, source_node="test")
    evt_fire.dummy_score = 0.8
    
    # 発火した場合、閾値はスコア(0.8)に近づくはず
    # threshold = 0.5 * 0.5 + 0.8 * 0.5 = 0.65
    assert sub.should_activate(evt_fire) is True
    assert abs(sub.fire_threshold - 0.65) < 0.01
    
    evt_skip = CognitionEvent(event_type=EventType.STEP_COMPLETE, source_node="test")
    evt_skip.dummy_score = 0.1
    
    # 今回は threshold(0.65) > score(0.1) なので発火しない
    # 発火しなかった場合、閾値はターゲット = max(0, 0.65 - 0.1) = 0.55 に向かう
    # new_th = 0.65 * 0.5 + 0.55 * 0.5 = 0.6
    assert sub.should_activate(evt_skip) is False
    assert abs(sub.fire_threshold - 0.6) < 0.01


def test_stigmergy_interaction_convergence_synteleia():
    ctx = StigmergyContext()
    
    conv_sub = ConvergenceSubscriber()
    conv_sub.bind_environment(ctx)
    
    syn_sub = SynteleiaSubscriber()
    syn_sub.bind_environment(ctx)
    
    evt = CognitionEvent(event_type=EventType.CONVERGENCE_ITER, source_node="test", metadata={"similarity": 0.99})
    
    # 1. 最初は両方普通
    s_conv1 = conv_sub.score(evt)
    s_syn1 = syn_sub.score(evt)
    
    # 2. Synteleia がアラート痕跡を残したとする
    trace_syn = Trace(subscriber_name="synteleia_l0", event_id="evt", intensity=1.0)
    ctx.add_trace(trace_syn)
    
    # 3. ConvergenceSubscriber のスコアが上がるはず
    s_conv2 = conv_sub.score(evt)
    assert s_conv2 > s_conv1, f"Convergence score should increase (before={s_conv1}, after={s_conv2})"
    
    # 4. 逆に ConvergenceSubscriber が苦戦痕跡（低 similarity -> 高 intensity）を残した場合
    trace_conv = Trace(subscriber_name="convergence_tracker", event_id="evt", intensity=0.8)
    ctx.add_trace(trace_conv)
    
    # 5. Synteleia のスキャンスコアが上がるはず
    s_syn2 = syn_sub.score(evt)
    assert s_syn2 > s_syn1, f"Synteleia score should increase (before={s_syn1}, after={s_syn2})"

    
def test_stigmergy_neural_graph_edges():
    ctx = StigmergyContext()
    
    # subA のイベントから subB が発火する連鎖をシミュレート
    t1 = Trace(id="1", subscriber_name="subA", event_id="evt1", intensity=0.5)
    t2 = Trace(id="2", subscriber_name="subB", event_id="evt1", parent_ids=["1"], intensity=0.8)
    
    ctx.add_trace(t1)
    ctx.add_trace(t2)
    
    edges = ctx.get_neural_edges()
    assert len(edges) == 1
    src, tgt, weight = edges[0]
    assert src == "subA"
    assert tgt == "subB"
    assert weight == 0.8


# =============================================================================
# Phase 4b: CognitionEnvironment 統合テスト (G3 亀裂修正)
# =============================================================================

class TracingSubscriber(BaseSubscriber):
    """テスト用: handle 時に痕跡を残す subscriber"""
    def score(self, event: CognitionEvent) -> float:
        s = 0.9  # 常に高スコア → 発火する
        self._score_history.append(s)
        return s
        
    def handle(self, event: CognitionEvent) -> str:
        self.leave_trace(event, payload={"handled": True})
        return f"[{self.name}] handled"


def test_environment_register_subscriber_binds():
    """G3-1: register_subscriber で双方向バインドが成立する"""
    env = CognitionEnvironment()
    sub = TracingSubscriber(name="tracer", fire_threshold=0.1)
    
    # 登録前: 環境未接続
    assert sub.stigmergy_context is None
    
    # 登録
    env.register_subscriber(sub)
    
    # 登録後: 環境が注入されている
    assert sub.stigmergy_context is env
    assert "tracer" in env.list_subscribers()


def test_environment_emit_triggers_subscriber_and_trace():
    """G3-2: emit で subscriber が発火し、痕跡が残る"""
    env = CognitionEnvironment()
    sub = TracingSubscriber(name="tracer", fire_threshold=0.1)
    env.register_subscriber(sub)
    
    evt = CognitionEvent(
        event_type=EventType.STEP_COMPLETE,
        source_node="test",
    )
    
    outputs = env.emit(evt)
    
    # subscriber が発火して出力を返した
    assert len(outputs) == 1
    assert "[tracer] handled" in outputs[0]
    
    # 痕跡が環境に残っている (手動 leave_trace + emit 自動 Trace = 2件)
    traces = env.get_traces_by_subscriber("tracer")
    assert len(traces) == 2
    # 手動 trace (leave_trace 経由) の payload が存在する
    payloads = [t.payload for t in traces]
    assert {"handled": True} in payloads
    
    # 統計が更新されている
    assert env.stats["total_emits"] == 1
    assert env.stats["total_activations"] == 1


def test_environment_without_subscriber_no_trace():
    """G3-3: subscriber 未登録のとき、emit しても痕跡は残らない"""
    env = CognitionEnvironment()
    
    evt = CognitionEvent(
        event_type=EventType.STEP_COMPLETE,
        source_node="test",
    )
    
    outputs = env.emit(evt)
    assert outputs == []
    assert len(env.get_recent_traces()) == 0


def test_environment_is_essential_for_trace():
    """G3-4: 環境を消す (None) と leave_trace が no-op になることを証明
    
    これにより「環境を消すとシステムの痕跡機能が壊れる」ことが構造的に保証される。
    """
    sub = TracingSubscriber(name="tracer", fire_threshold=0.1)
    # 環境なし
    assert sub.stigmergy_context is None
    
    evt = CognitionEvent(
        event_type=EventType.STEP_COMPLETE,
        source_node="test",
    )
    
    # leave_trace は no-op (何も起きない)
    sub.leave_trace(evt, payload={"should_not_persist": True})
    
    # 環境ありの場合
    env = CognitionEnvironment()
    env.register_subscriber(sub)
    
    # 今度は痕跡が残る
    sub.leave_trace(evt, payload={"should_persist": True})
    traces = env.get_traces_by_subscriber("tracer")
    assert len(traces) == 1
    assert traces[0].payload == {"should_persist": True}


# =============================================================================
# Phase 5: Hebbian Boost Tests
# =============================================================================

class ThresholdSubscriber(BaseSubscriber):
    """テスト用: 閾値が動的に変わる subscriber"""
    def __init__(self, name: str, threshold: float):
        super().__init__(name=name)
        self.fire_threshold = threshold
        
    def score(self, event: CognitionEvent) -> float:
        return 0.5  # 固定スコア
        
    def handle(self, event: CognitionEvent) -> str:
        self.leave_trace(event, payload={"handled": True})
        return "handled"

def test_apply_hebbian_boost():
    """Hebb則による閾値低下の基本的な動作を検証"""
    ctx = CognitionEnvironment()
    sub_a = ThresholdSubscriber("subA", 0.8)
    sub_b = ThresholdSubscriber("subB", 0.6)
    ctx.register_subscriber(sub_a)
    ctx.register_subscriber(sub_b)
    
    # subA の痕跡
    t1 = Trace(id="1", subscriber_name="subA", event_id="evt1", intensity=1.0)
    ctx.add_trace(t1)
    # subA から subB への連鎖 (weight = 1.0)
    t2 = Trace(id="2", subscriber_name="subB", event_id="evt2", intensity=1.0, parent_ids=["1"])
    ctx.add_trace(t2)
    
    # ブースト適用
    applied = ctx.apply_hebbian_boost(max_boost=0.2)
    
    # subB がブーストされている (A→B のエッジがあるため)
    assert "subB" in applied
    assert applied["subB"] == 0.2
    
    # subB の閾値が下がっている (0.6 -> 0.4)
    assert sub_b.fire_threshold == pytest.approx(0.4)
    # subA はブーストされていない
    assert "subA" not in applied
    assert sub_a.fire_threshold == pytest.approx(0.8)

def test_hebbian_boost_max_cap():
    """ブースト量が max_boost を超えないこと、最低閾値 (0.05) を下回らないことを検証"""
    ctx = CognitionEnvironment()
    # 閾値を非常に低く設定
    sub_c = ThresholdSubscriber("subC", 0.1)
    ctx.register_subscriber(sub_c)
    
    # 強力な連鎖 (weight = 5.0)
    t1 = Trace(id="1", subscriber_name="subA", event_id="evt1", intensity=5.0)
    t2 = Trace(id="2", subscriber_name="subC", event_id="evt2", intensity=5.0, parent_ids=["1"])
    ctx.add_trace(t1)
    ctx.add_trace(t2)
    
    ctx.apply_hebbian_boost(max_boost=0.5)
    
    # 閾値は 0.1 - 0.5 = -0.4 ではなく、最低値 0.05 でクリップされる
    assert sub_c.fire_threshold == pytest.approx(0.05)

def test_hebbian_boost_decay():
    """時間経過でブースト値が減衰し、閾値が元に戻ることを検証"""
    ctx = CognitionEnvironment()
    sub_d = ThresholdSubscriber("subD", 0.5)
    ctx.register_subscriber(sub_d)
    
    t1 = Trace(id="1", subscriber_name="subA", event_id="evt1", intensity=1.0)
    t2 = Trace(id="2", subscriber_name="subD", event_id="evt2", intensity=1.0, parent_ids=["1"])
    ctx.add_trace(t1)
    ctx.add_trace(t2)
    
    # 1回目のブースト (weight=1.0, max_boost=0.2 -> boost=0.2)
    ctx.apply_hebbian_boost(max_boost=0.2, decay_rate=0.5)
    assert sub_d.fire_threshold == pytest.approx(0.3)  # 0.5 - 0.2
    
    # 痕跡をクリア (連鎖が途絶える)
    ctx._traces.clear()
    
    # 2回目のブースト (減衰のみ)
    ctx.apply_hebbian_boost(max_boost=0.2, decay_rate=0.5)
    
    # ブースト値が 0.2 * 0.5 = 0.1 に減衰、閾値は 0.5 - 0.1 = 0.4 に回復
    assert sub_d.fire_threshold == pytest.approx(0.4)
    
    # 3回目のブースト (さらに減衰)
    ctx.apply_hebbian_boost(max_boost=0.2, decay_rate=0.5)
    
    # ブースト値 0.1 * 0.5 = 0.05、閾値 0.5 - 0.05 = 0.45
    assert sub_d.fire_threshold == pytest.approx(0.45)


# =============================================================================
# Phase 5: 統合テスト — emit→Trace→edges→boost のフルチェーン
# =============================================================================

class AlphaSubscriber(BaseSubscriber):
    """テスト用: 常に発火する subscriber A"""
    def score(self, event: CognitionEvent) -> float:
        return 0.9
    def handle(self, event: CognitionEvent) -> str:
        return "[alpha] done"

class BetaSubscriber(BaseSubscriber):
    """テスト用: 常に発火する subscriber B"""
    def score(self, event: CognitionEvent) -> float:
        return 0.9
    def handle(self, event: CognitionEvent) -> str:
        return "[beta] done"


def test_full_pipeline_emit_to_hebbian_boost():
    """統合テスト: emit→Trace自動生成→neural_edges→hebbian_boost→threshold変更
    
    手動 add_trace ではなく、emit() 経由で自然に Trace が蓄積され、
    apply_hebbian_boost() が fire_threshold を実際に変更することを検証する。
    これが「消したら壊れる」証拠。
    """
    env = CognitionEnvironment()
    alpha = AlphaSubscriber(name="alpha", fire_threshold=0.5)
    beta = BetaSubscriber(name="beta", fire_threshold=0.5)
    env.register_subscriber(alpha)
    env.register_subscriber(beta)
    
    evt = CognitionEvent(
        event_type=EventType.STEP_COMPLETE,
        source_node="test",
    )
    
    # 1回目の emit: alpha と beta が発火 → Trace 2件
    env.emit(evt)
    assert len(env.get_recent_traces(limit=10)) == 2
    
    # 2回目の emit: さらに Trace 2件 (parent_ids = 1回目の Trace IDs)
    env.emit(evt)
    assert len(env.get_recent_traces(limit=10)) == 4
    
    # Neural Graph: alpha→beta, beta→alpha のエッジが存在するはず
    edges = env.get_neural_edges()
    assert len(edges) > 0, "emit 2回で因果エッジが生成されるべき"
    
    # Hebbian Boost 適用前の閾値を記録
    original_alpha = alpha.fire_threshold
    original_beta = beta.fire_threshold
    
    # Hebbian Boost を適用
    applied = env.apply_hebbian_boost(max_boost=0.3)
    assert len(applied) > 0, "エッジがあるのでブーストが適用されるべき"
    
    # 少なくとも1つの subscriber の fire_threshold が下がっている
    threshold_changed = (
        alpha.fire_threshold < original_alpha
        or beta.fire_threshold < original_beta
    )
    assert threshold_changed, "Hebbian Boost が fire_threshold を変更すべき"
