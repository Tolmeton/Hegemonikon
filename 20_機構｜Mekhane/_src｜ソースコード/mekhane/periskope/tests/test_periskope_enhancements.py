# PROOF: mekhane/periskope/tests/test_periskope_enhancements.py
# PURPOSE: periskope モジュールの periskope_enhancements に対するテスト
"""
Tests for Periskopē v2.0 Enhancements.

These tests verify the 5 enhancements are structurally integrated.
If any enhancement is removed, these tests MUST fail.

Purpose: Achieve 🟢 Naturalized /fit status by creating structural dependencies.
"""

import asyncio
import json
import pytest

# ─── Enhancement ① Tests: ProgressEvent / ProgressCallback ─────────

class TestProgressProtocol:
    """Test that ProgressEvent and ProgressCallback exist and work."""

    def test_progress_event_exists(self):
        """ProgressEvent must be importable from models."""
        from mekhane.periskope.models import ProgressEvent
        event = ProgressEvent(phase="test", detail={"key": "val"}, elapsed=1.5)
        assert event.phase == "test"
        assert event.detail == {"key": "val"}
        assert event.elapsed == 1.5

    def test_progress_event_summary(self):
        """ProgressEvent.summary() must produce readable output."""
        from mekhane.periskope.models import ProgressEvent
        event = ProgressEvent(phase="phase_1", detail={"results": 42}, elapsed=2.3, progress=0.5)
        s = event.summary()
        assert "[phase_1]" in s
        assert "50%" in s
        assert "2.3s" in s
        assert "results=42" in s

    def test_progress_callback_type_alias(self):
        """ProgressCallback type alias must exist."""
        from mekhane.periskope.models import ProgressCallback
        assert ProgressCallback is not None

    def test_research_accepts_progress_callback(self):
        """research() must accept progress_callback parameter."""
        import inspect
        from mekhane.periskope.engine import PeriskopeEngine
        sig = inspect.signature(PeriskopeEngine.research)
        assert "progress_callback" in sig.parameters
        param = sig.parameters["progress_callback"]
        assert param.default is None  # Optional

    def test_research_accepts_interaction_callback(self):
        """research() must accept interaction_callback parameter (Enhancement ⑤)."""
        import inspect
        from mekhane.periskope.engine import PeriskopeEngine
        sig = inspect.signature(PeriskopeEngine.research)
        assert "interaction_callback" in sig.parameters
        param = sig.parameters["interaction_callback"]
        assert param.default is None


# ─── Enhancement ② Tests: Task Decomposition ──────────────────────

class TestTaskDecomposition:
    """Test that Φ0.5 task decomposer exists and is importable."""

    def test_phi0_module_exists(self):
        """phi0_task_decompose module must exist at the correct path."""
        from mekhane.periskope.cognition.phi0_task_decompose import (
            decompose_query, SubTask, synthesize_subtask_results,
        )
        assert decompose_query is not None
        assert SubTask is not None
        assert synthesize_subtask_results is not None

    def test_subtask_dataclass(self):
        """SubTask must have query, focus, priority fields."""
        from mekhane.periskope.cognition.phi0_task_decompose import SubTask
        st = SubTask(query="test query", focus="testing", priority=1)
        assert st.query == "test query"
        assert st.focus == "testing"
        assert st.priority == 1

    def test_phi0_naming_convention(self):
        """Module must follow phi naming convention (phi0_*)."""
        import importlib
        mod = importlib.import_module("mekhane.periskope.cognition.phi0_task_decompose")
        assert hasattr(mod, "decompose_query")
        assert hasattr(mod, "synthesize_subtask_results")

    def test_engine_imports_phi0(self):
        """engine.py must import phi0_task_decompose (not task_decomposer)."""
        import ast
        from pathlib import Path
        engine_path = Path(__file__).parent.parent / "engine.py"
        source = engine_path.read_text(encoding="utf-8")
        assert "phi0_task_decompose" in source
        # Old import path must not exist (docstring mentions are OK)
        assert "import" not in source or "from mekhane.periskope.cognition.task_decomposer" not in source
        # G-02: multi-level Φ0.5 recursion parameters
        assert "_recursion_depth" in source
        assert "MAX_RECURSION" in source
        assert "breadth" in source


# ─── Enhancement ④ Tests: ReasoningTrace Serialization ─────────────

class TestReasoningTraceSerialization:
    """Test ReasoningTrace JSON roundtrip."""

    def test_reasoning_trace_has_from_dict(self):
        """ReasoningTrace must have from_dict classmethod."""
        from mekhane.periskope.cognition.reasoning_trace import ReasoningTrace
        assert hasattr(ReasoningTrace, "from_dict")
        assert callable(getattr(ReasoningTrace, "from_dict"))

    def test_roundtrip(self):
        """to_dict → from_dict must preserve all data."""
        from mekhane.periskope.cognition.reasoning_trace import (
            ReasoningTrace, ReasoningStep,
        )
        trace = ReasoningTrace(query="roundtrip test")
        trace.steps.append(ReasoningStep(
            iteration=1,
            learned=["fact A", "fact B"],
            contradictions=["contradiction X"],
            gaps=["gap Y"],
            next_queries=["query Z"],
            confidence=0.75,
            info_gain=0.42,
            new_results=5,
        ))
        trace.steps.append(ReasoningStep(
            iteration=2,
            learned=["fact C"],
            contradictions=[],
            gaps=[],
            next_queries=[],
            confidence=0.95,
            info_gain=0.1,
            new_results=2,
        ))

        d = trace.to_dict()
        restored = ReasoningTrace.from_dict(d)

        assert restored.query == "roundtrip test"
        assert len(restored.steps) == 2
        assert restored.steps[0].learned == ["fact A", "fact B"]
        assert restored.steps[0].contradictions == ["contradiction X"]
        assert restored.steps[0].confidence == 0.75
        assert restored.steps[0].info_gain == 0.42
        assert restored.steps[0].new_results == 5
        assert restored.steps[1].confidence == 0.95
        assert restored.latest_confidence == 0.95

    def test_json_roundtrip(self):
        """Full JSON string roundtrip via json.dumps/loads."""
        from mekhane.periskope.cognition.reasoning_trace import (
            ReasoningTrace, ReasoningStep,
        )
        trace = ReasoningTrace(query="json test")
        trace.steps.append(ReasoningStep(
            iteration=1, learned=["x"], confidence=0.8,
        ))
        d = trace.to_dict()
        json_str = json.dumps(d, ensure_ascii=False)
        restored_dict = json.loads(json_str)
        restored = ReasoningTrace.from_dict(restored_dict)
        assert restored.steps[0].learned == ["x"]
        assert restored.steps[0].confidence == 0.8


# ─── Enhancement ⑤: Thinking Trace ──────────────────────────────
# NOTE: _format_thinking_trace tests moved to mekhane/mcp/tests/test_periskope_benchmark.py
#       (TestFormatThinkingTrace class — tests label display, fallback to phase, detail filtering)


# ─── Structural Integration Tests ──────────────────────────────────

class TestStructuralIntegration:
    """Tests that verify structural dependencies exist (消去テスト)."""

    def test_engine_from_json_restores_trace(self):
        """ResearchReport.from_json must restore ReasoningTrace."""
        import ast
        from pathlib import Path
        engine_path = Path(__file__).parent.parent / "engine.py"
        source = engine_path.read_text(encoding="utf-8")
        assert "ReasoningTrace.from_dict" in source
        assert "reasoning_trace" in source

    def test_mcp_server_uses_progress_event(self):
        """MCP server must use ProgressEvent-based callback."""
        from pathlib import Path
        mcp_path = Path(__file__).parent.parent.parent / "mcp" / "periskope_mcp_server.py"
        source = mcp_path.read_text(encoding="utf-8")
        assert "event.summary()" in source
        assert "event.elapsed" in source
        assert "event.phase" in source
        assert "event.detail" in source
