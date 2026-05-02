"""KalonGateSubscriber + ConeGuardSubscriber テスト

Phase 5 Step 4: Creator's Features の統合テスト。
"""
import pytest
from hermeneus.src.event_bus import CognitionEvent, EventType
from hermeneus.src.activation import BaseSubscriber
from hermeneus.src.stigmergy import CognitionEnvironment
from hermeneus.src.subscribers.kalon_gate_sub import KalonGateSubscriber
from hermeneus.src.subscribers.cone_guard_sub import ConeGuardSubscriber
from hermeneus.src.macro_executor import StepResult, StepType


def _make_verification_event(
    output: str,
    step_count: int = 3,
    metadata=None,
    child_node_id: str | None = None,
    source_node: str = "V:test",
):
    """VERIFICATION イベントを生成するヘルパー"""
    children = []
    if child_node_id:
        children.append(
            StepResult(
                step_type=StepType.WORKFLOW,
                node_id=child_node_id,
                output=output,
                entropy_before=0.5,
                entropy_after=0.3,
            )
        )
    result = StepResult(
        step_type=StepType.WORKFLOW,
        node_id="test_node",
        output=output,
        entropy_before=0.5,
        entropy_after=0.3,
        children=children,
    )
    return CognitionEvent(
        event_type=EventType.VERIFICATION,
        step_result=result,
        source_node=source_node,
        context_snapshot={"step_count": step_count, "depth": 1, "variables": {}},
        metadata=metadata or {},
    )


# =============================================================================
# KalonGateSubscriber テスト
# =============================================================================

class TestKalonGateSubscriber:
    """KalonGateSubscriber の品質ゲートロジック検証"""

    def test_name_is_kalon_gate(self):
        sub = KalonGateSubscriber()
        assert sub.name == "kalon_gate"

    def test_subscribes_to_verification_only(self):
        sub = KalonGateSubscriber()
        assert sub.policy.event_types == {EventType.VERIFICATION}

    def test_passes_good_output(self):
        """Trace + Negativa + Iso が含まれる出力 → 警告なし (None)"""
        good_output = (
            "## 計画\n"
            "1. 理由: この設計はパフォーマンス要件を満たすため最適です。\n"
            "2. 棄却した代替案: Redis を使わずインメモリキャッシュにする案は "
            "スケーラビリティの観点から不採用としました。\n"
            "[CHECKPOINT PHASE 1/3]\n"
        )
        sub = KalonGateSubscriber(fire_threshold=0.1)
        evt = _make_verification_event(good_output)
        result = sub.handle(evt)
        assert result is None, "Trace + Negativa + Iso があるので警告なし"

    def test_warns_missing_trace(self):
        """Trace がない出力 → Trace 欠落の警告"""
        no_trace = "## 計画\n棄却: Redis案は見送りです。\n具体的な手順を示します。\n"
        sub = KalonGateSubscriber(fire_threshold=0.1)
        evt = _make_verification_event(no_trace)
        result = sub.handle(evt)
        assert result is not None
        assert "Trace 欠落" in result

    def test_warns_missing_negativa(self):
        """Negativa がない出力 → Negativa 欠落の警告"""
        no_negativa = "## 計画\n理由: この設計が最適です。\n手順を以下に示します。\n"
        sub = KalonGateSubscriber(fire_threshold=0.1)
        evt = _make_verification_event(no_negativa)
        result = sub.handle(evt)
        assert result is not None
        assert "Negativa 欠落" in result

    def test_warns_both_missing(self):
        """Trace も Negativa も Iso もない → 警告"""
        shallow = "## タスク\nやります。\n"
        sub = KalonGateSubscriber(fire_threshold=0.1)
        evt = _make_verification_event(shallow)
        result = sub.handle(evt)
        assert result is not None
        assert "Trace 欠落" in result
        assert "Negativa 欠落" in result
        assert "Iso 欠落" in result

    def test_warns_missing_iso(self):
        """Trace + Negativa があっても構造痕跡が乏しければ Iso 欠落を警告"""
        no_iso = "理由: この設計が最適です。代替案Aは棄却しました。"
        sub = KalonGateSubscriber(fire_threshold=0.1)
        evt = _make_verification_event(no_iso)
        result = sub.handle(evt)
        assert result is not None
        assert "Iso 欠落" in result

    def test_warns_missing_implementation_report_surfaces_for_ene(self):
        """`/ene` 実装報告なのに renderer surfaces がない → O4 gate 警告"""
        shallow_report = (
            "## 実装報告\n"
            "理由: この変更は必要です。\n"
            "棄却した代替案: 全面書き換えは見送りました。\n"
            "[CHECKPOINT P-2/5]\n"
        )
        sub = KalonGateSubscriber(fire_threshold=0.1)
        evt = _make_verification_event(shallow_report, child_node_id="/ene")
        result = sub.handle(evt)
        assert result is not None
        assert "成果核 欠落" in result
        assert "変更面 欠落" in result
        assert "検証面 欠落" in result
        assert "復元面 欠落" in result
        assert "/ene 実装報告" in result

    def test_passes_implementation_report_with_required_surfaces(self):
        """`/ene` 実装報告が renderer policy を満たす → 警告なし"""
        good_report = (
            "## 成果核\n"
            "今回の変更で validator が /ene 実装報告の surface 欠落を検知できるようになりました。\n\n"
            "| path | intent | change |\n"
            "|---|---|---|\n"
            "| /home/makaron8426/project/file.py | readability gate | 追加 |\n\n"
            "## 検証\n"
            "```bash\n"
            "python -m pytest hermeneus/tests/test_creator_features.py -q\n"
            "```\n"
            "理由: 実装報告を reader-facing artifact に固定するためです。\n"
            "棄却した代替案: prompt だけで矯正する案は再発防止にならないため不採用です。\n"
            "[CHECKPOINT P-2/5]\n"
            "## 復元\n"
            "戻す場合は対象ファイルを巻き戻し、同じテストを再実行します。\n"
            "## Annex\n"
            "| raw path |\n"
            "|---|\n"
            "| /home/makaron8426/project/file.py |\n"
        )
        sub = KalonGateSubscriber(fire_threshold=0.1)
        evt = _make_verification_event(good_report, child_node_id="/ene")
        result = sub.handle(evt)
        assert result is None

    def test_empty_output_returns_none(self):
        """空の出力 → None (何もしない)"""
        sub = KalonGateSubscriber()
        evt = _make_verification_event("")
        result = sub.handle(evt)
        assert result is None

    def test_score_increases_with_steps(self):
        """step_count が多いほど score が高い"""
        sub = KalonGateSubscriber()
        evt_low = _make_verification_event("test", step_count=1)
        evt_high = _make_verification_event("test", step_count=5)
        assert sub.score(evt_low) < sub.score(evt_high)

    def test_environment_integration(self):
        """CognitionEnvironment に登録して emit → 発火 → Trace"""
        env = CognitionEnvironment()
        sub = KalonGateSubscriber(fire_threshold=0.1)
        env.register_subscriber(sub)

        shallow_output = "## やること\nとりあえずやります。\n"
        evt = _make_verification_event(shallow_output, step_count=3)
        outputs = env.emit(evt)

        # 警告が出力される
        assert len(outputs) == 1
        assert "Kalon" in outputs[0]
        # emit による自動 Trace が生成される
        assert len(env.get_recent_traces(limit=10)) >= 1


# =============================================================================
# ConeGuardSubscriber テスト
# =============================================================================

class TestConeGuardSubscriber:
    """ConeGuardSubscriber の Devil's Advocate ロジック検証"""

    def test_name_is_cone_guard(self):
        sub = ConeGuardSubscriber()
        assert sub.name == "cone_guard"

    def test_subscribes_to_verification_only(self):
        sub = ConeGuardSubscriber()
        assert sub.policy.event_types == {EventType.VERIFICATION}

    def test_insufficient_steps_returns_none(self):
        """step_outputs が 2 未満 → None"""
        sub = ConeGuardSubscriber(fire_threshold=0.1)
        evt = _make_verification_event(
            "test",
            metadata={"step_outputs": {"noe": "一つだけ"}},
        )
        result = sub.handle(evt)
        assert result is None

    def test_no_step_outputs_returns_none(self):
        """step_outputs がない → None"""
        sub = ConeGuardSubscriber(fire_threshold=0.1)
        evt = _make_verification_event("test", metadata={})
        result = sub.handle(evt)
        assert result is None

    def test_wf_to_theorem_mapping(self):
        """WF名→Theorem ID マッピングの正確性"""
        assert ConeGuardSubscriber.WF_TO_THEOREM["noe"] == "O1"
        assert ConeGuardSubscriber.WF_TO_THEOREM["dia"] == "A2"
        assert ConeGuardSubscriber.WF_TO_THEOREM["sop"] == "K4"

    def test_score_increases_with_steps(self):
        """step_count が多いほど score が高い"""
        sub = ConeGuardSubscriber()
        evt_low = _make_verification_event("test", step_count=1)
        evt_high = _make_verification_event("test", step_count=5)
        assert sub.score(evt_low) < sub.score(evt_high)

    def test_environment_integration_no_fep(self):
        """CognitionEnvironment で emit — fep モジュール不在時は None"""
        env = CognitionEnvironment()
        sub = ConeGuardSubscriber(fire_threshold=0.1)
        env.register_subscriber(sub)

        evt = _make_verification_event(
            "test",
            step_count=3,
            metadata={
                "step_outputs": {
                    "noe+:block": "本質の分析結果",
                    "dia+:block": "批判的レビュー結果",
                    "bou+:block": "目的の明確化結果",
                },
            },
        )
        outputs = env.emit(evt)
        # fep が ImportError でも crash しない (graceful degradation)
        # 出力は None (ImportError 時) か advice 文字列
        # emit 自体は成功する
        assert isinstance(outputs, list)


# =============================================================================
# Subscriber 登録テスト
# =============================================================================

class TestDefaultSubscriberRegistration:
    """KalonGate と ConeGuard がデフォルト subscriber に含まれるか"""

    def test_kalon_in_defaults(self):
        from hermeneus.src.subscribers import create_default_subscribers
        names = [s.name for s in create_default_subscribers()]
        assert "kalon_gate" in names

    def test_cone_in_defaults(self):
        from hermeneus.src.subscribers import create_default_subscribers
        names = [s.name for s in create_default_subscribers()]
        assert "cone_guard" in names
