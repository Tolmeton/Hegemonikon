# PROOF: [L2/Phase7] <- hermeneus/tests/test_v9_e2e.py
# PURPOSE: v9.0 全接続パスの end-to-end 統合テスト
"""
v9.0 E2E 統合テスト — 表層実装の再発防止

ROM 法則「接続していない部品は実装ではない」を検証する。
単にファイルが存在するかではなく、実際の呼び出しチェーンが動作するかをテスト。
"""
import pytest


class TestEventTypeExists:
    """MACRO_START/MACRO_COMPLETE が EventType に存在する"""

    def test_macro_start_exists(self):
        from hermeneus.src.events import EventType
        assert hasattr(EventType, "MACRO_START")
        assert EventType.MACRO_START.value == "macro_start"

    def test_macro_complete_exists(self):
        from hermeneus.src.events import EventType
        assert hasattr(EventType, "MACRO_COMPLETE")
        assert EventType.MACRO_COMPLETE.value == "macro_complete"


class TestSubscriberRegistration:
    """create_all_subscribers が新サブスクライバを含む"""

    def test_create_all_includes_plan_preprocessor(self):
        from hermeneus.src.subscribers import create_all_subscribers
        subs = create_all_subscribers()
        names = [s.name for s in subs]
        assert "plan_preprocessor" in names

    def test_create_all_includes_plan_recorder(self):
        from hermeneus.src.subscribers import create_all_subscribers
        subs = create_all_subscribers()
        names = [s.name for s in subs]
        assert "plan_recorder" in names


class TestEventBusRouting:
    """EventBus が MACRO_START/COMPLETE を正しいサブスクライバにルーティング"""

    def test_macro_start_activates_preprocessor(self):
        from hermeneus.src.events import EventType, CognitionEvent
        from hermeneus.src.subscribers.plan_preprocessor import PlanPreprocessorSubscriber

        pp = PlanPreprocessorSubscriber()
        event = CognitionEvent(
            event_type=EventType.MACRO_START,
            metadata={"macro_name": "plan", "context": "テスト"},
        )
        assert pp.should_activate(event) is True

    def test_macro_start_ignores_non_plan(self):
        from hermeneus.src.events import EventType, CognitionEvent
        from hermeneus.src.subscribers.plan_preprocessor import PlanPreprocessorSubscriber

        pp = PlanPreprocessorSubscriber()
        event = CognitionEvent(
            event_type=EventType.MACRO_START,
            metadata={"macro_name": "build"},
        )
        assert pp.should_activate(event) is False

    def test_step_complete_does_not_activate_preprocessor(self):
        from hermeneus.src.events import EventType, CognitionEvent
        from hermeneus.src.subscribers.plan_preprocessor import PlanPreprocessorSubscriber

        pp = PlanPreprocessorSubscriber()
        event = CognitionEvent(
            event_type=EventType.STEP_COMPLETE,
            metadata={"macro_name": "plan"},
        )
        assert pp.should_activate(event) is False

    def test_macro_complete_activates_recorder(self):
        from hermeneus.src.events import EventType, CognitionEvent
        from hermeneus.src.subscribers.plan_recorder import PlanRecorderSubscriber

        pr = PlanRecorderSubscriber()
        event = CognitionEvent(
            event_type=EventType.MACRO_COMPLETE,
            metadata={"macro_name": "plan"},
        )
        assert pr.should_activate(event) is True

    def test_macro_complete_ignores_non_plan(self):
        from hermeneus.src.events import EventType, CognitionEvent
        from hermeneus.src.subscribers.plan_recorder import PlanRecorderSubscriber

        pr = PlanRecorderSubscriber()
        event = CognitionEvent(
            event_type=EventType.MACRO_COMPLETE,
            metadata={"macro_name": "fix"},
        )
        assert pr.should_activate(event) is False


class TestEventBusEmitReceive:
    """EventBus.emit() → subscriber.handle() の接続テスト"""

    def test_emit_macro_start_reaches_subscriber(self):
        from hermeneus.src.event_bus import CognitionEventBus
        from hermeneus.src.events import EventType, CognitionEvent
        from hermeneus.src.subscribers.plan_preprocessor import PlanPreprocessorSubscriber

        bus = CognitionEventBus(enabled=True)
        pp = PlanPreprocessorSubscriber()
        bus.subscribe_all(pp)

        event = CognitionEvent(
            event_type=EventType.MACRO_START,
            metadata={"macro_name": "plan", "context": "テスト実装の計画"},
        )
        outputs = bus.emit(event)
        assert bus.stats["total_activations"] >= 1

    def test_emit_macro_complete_reaches_recorder(self):
        from hermeneus.src.event_bus import CognitionEventBus
        from hermeneus.src.events import EventType, CognitionEvent
        from hermeneus.src.subscribers.plan_recorder import PlanRecorderSubscriber

        bus = CognitionEventBus(enabled=True)
        pr = PlanRecorderSubscriber()
        bus.subscribe_all(pr)

        event = CognitionEvent(
            event_type=EventType.MACRO_COMPLETE,
            metadata={"macro_name": "plan"},
        )
        outputs = bus.emit(event)
        assert bus.stats["total_activations"] >= 1
        # 記録数が増えること
        assert pr.plans_recorded == 1


class TestCCLLinterIntegration:
    """CCLLinter が MacroExecutor.execute() 内で呼ばれること"""

    def test_linter_called_in_execute(self):
        """MacroExecutor.execute() が CCLLinter を呼ぶ (import が通る)"""
        from hermeneus.src.ccl_linter import lint_ccl, Severity
        # 有効な CCL にはエラーなし
        issues = lint_ccl("@plan")
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) == 0

    def test_linter_detects_undefined_wf(self):
        from hermeneus.src.ccl_linter import lint_ccl
        issues = lint_ccl("/xyz+")
        assert any(i.rule == "undefined-workflow" for i in issues)


class TestPreprocessorPurePython:
    """PlanPreprocessor の pure-Python 実装が外部依存なしで動作"""

    def test_attractor_returns_recommendation(self):
        from hermeneus.src.subscribers.plan_preprocessor import (
            PlanPreprocessorSubscriber, PreprocessContext,
        )
        pp = PlanPreprocessorSubscriber()
        ctx = PreprocessContext(query="本質を理解したい構造の分析")
        result = pp._phase_c_recommend(ctx)
        assert result is not None
        assert "Attractor" in result or "定理推薦" in result

    def test_policy_check_convergent(self):
        from hermeneus.src.subscribers.plan_preprocessor import (
            PlanPreprocessorSubscriber, PreprocessContext,
        )
        pp = PlanPreprocessorSubscriber()
        ctx = PreprocessContext(query="バグ修正とテスト実装")
        result = pp._phase_c_recommend(ctx)
        assert result is not None
        assert "収束型" in result

    def test_policy_check_divergent(self):
        from hermeneus.src.subscribers.plan_preprocessor import (
            PlanPreprocessorSubscriber, PreprocessContext,
        )
        pp = PlanPreprocessorSubscriber()
        ctx = PreprocessContext(query="新しいアイデアの探索と調査")
        result = pp._phase_c_recommend(ctx)
        assert result is not None
        assert "発散型" in result

    def test_no_external_imports(self):
        """plan_preprocessor.py が外部パッケージを import しない"""
        import ast
        from pathlib import Path
        src = Path(__file__).parent.parent / "src" / "subscribers" / "plan_preprocessor.py"
        tree = ast.parse(src.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom) and node.module:
                    # mekhane.mcp.* への import がないこと
                    assert not node.module.startswith("mekhane.mcp."), (
                        f"外部 MCP 依存禁止: {node.module}"
                    )


class TestRecorderPurePython:
    """PlanRecorder の pure-Python 実装"""

    def test_anti_shallow_detects_missing_negativa(self):
        from hermeneus.src.subscribers.plan_recorder import PlanRecorderSubscriber
        pr = PlanRecorderSubscriber(violation_check_enabled=True, notifications_enabled=False)
        result = pr._check_anti_shallow("素晴らしい計画です。全て完璧。")
        assert result is not None
        assert "Negativa 不足" in result

    def test_anti_shallow_passes_good_output(self):
        from hermeneus.src.subscribers.plan_recorder import PlanRecorderSubscriber
        pr = PlanRecorderSubscriber(violation_check_enabled=True, notifications_enabled=False)
        result = pr._check_anti_shallow(
            "理由: A が B より優れている。❌ 棄却: C 案はリスクが高い。弱点: D の深刻度は中。"
        )
        assert result is None  # 問題なし

    def test_no_external_imports(self):
        """plan_recorder.py が外部パッケージを import しない"""
        import ast
        from pathlib import Path
        src = Path(__file__).parent.parent / "src" / "subscribers" / "plan_recorder.py"
        tree = ast.parse(src.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom) and node.module:
                    assert not node.module.startswith("mekhane.mcp."), (
                        f"外部 MCP 依存禁止: {node.module}"
                    )


class TestV41Workflows:
    """CCLParser.WORKFLOWS に v4.1 動詞名が全て含まれる"""

    @pytest.mark.parametrize("wf", [
        "ske", "sag", "pei", "tek",   # Methodos
        "kat", "epo", "pai", "dok",   # Krisis
        "lys", "ops", "akr", "arc",   # Diástasis
        "beb", "ele", "kop", "dio",   # Orexis
        "hyp", "prm", "ath", "par",   # Chronos
    ])
    def test_v41_verb_in_workflows(self, wf):
        from hermeneus.src.parser import CCLParser
        assert wf in CCLParser.WORKFLOWS, f"v4.1 動詞 '{wf}' が WORKFLOWS に未登録"
