# PROOF: mekhane/ochema/tests/test_task_planner.py
# PURPOSE: ochema モジュールの task_planner に対するテスト
"""
Tests for Φ0.5-Code: Jules Task Planner.

Verifies decomposition logic, parallel group building,
and format conversion without requiring LLM calls.
"""


from __future__ import annotations
from mekhane.ochema.task_planner import (
    CodeSubTask,
    DecompositionPlan,
    _build_parallel_groups,
    format_batch_tasks,
    format_plan_summary,
)


class TestCodeSubTask:
    """Test CodeSubTask dataclass."""

    def test_basic_creation(self):
        st = CodeSubTask(prompt="Fix auth", focus="Auth", priority=1)
        assert st.prompt == "Fix auth"
        assert st.files == []
        assert st.depends_on == []

    def test_with_dependencies(self):
        st = CodeSubTask(
            prompt="Write tests", focus="Tests", priority=2,
            files=["tests/test_auth.py"],
            depends_on=[0],
        )
        assert st.depends_on == [0]
        assert st.files == ["tests/test_auth.py"]


class TestBuildParallelGroups:
    """Test topological sorting of task dependencies."""

    def test_no_dependencies(self):
        """All tasks independent → single parallel group."""
        tasks = [
            CodeSubTask(prompt="A", focus="A", priority=1),
            CodeSubTask(prompt="B", focus="B", priority=1),
            CodeSubTask(prompt="C", focus="C", priority=1),
        ]
        groups = _build_parallel_groups(tasks)
        assert len(groups) == 1
        assert set(groups[0]) == {0, 1, 2}

    def test_linear_chain(self):
        """A → B → C → three waves."""
        tasks = [
            CodeSubTask(prompt="A", focus="A", priority=1),
            CodeSubTask(prompt="B", focus="B", priority=2, depends_on=[0]),
            CodeSubTask(prompt="C", focus="C", priority=3, depends_on=[1]),
        ]
        groups = _build_parallel_groups(tasks)
        assert len(groups) == 3
        assert groups[0] == [0]
        assert groups[1] == [1]
        assert groups[2] == [2]

    def test_diamond(self):
        """A → B, A → C, B+C → D → two waves."""
        tasks = [
            CodeSubTask(prompt="A", focus="A", priority=1),
            CodeSubTask(prompt="B", focus="B", priority=2, depends_on=[0]),
            CodeSubTask(prompt="C", focus="C", priority=2, depends_on=[0]),
            CodeSubTask(prompt="D", focus="D", priority=3, depends_on=[1, 2]),
        ]
        groups = _build_parallel_groups(tasks)
        assert len(groups) == 3
        assert groups[0] == [0]
        assert set(groups[1]) == {1, 2}
        assert groups[2] == [3]

    def test_empty(self):
        assert _build_parallel_groups([]) == []

    def test_mixed_deps(self):
        """0 and 2 are independent. 1 depends on 0."""
        tasks = [
            CodeSubTask(prompt="A", focus="A", priority=1),
            CodeSubTask(prompt="B", focus="B", priority=2, depends_on=[0]),
            CodeSubTask(prompt="C", focus="C", priority=1),
        ]
        groups = _build_parallel_groups(tasks)
        assert len(groups) == 2
        assert set(groups[0]) == {0, 2}
        assert groups[1] == [1]


class TestFormatBatchTasks:
    """Test conversion to Jules batch_execute format."""

    def test_basic_format(self):
        plan = DecompositionPlan(
            original_prompt="Big change",
            repo="owner/repo",
            branch="main",
            subtasks=[
                CodeSubTask(prompt="Fix auth", focus="Auth", priority=1, files=["auth.py"]),
                CodeSubTask(prompt="Add tests", focus="Tests", priority=2, depends_on=[0]),
            ],
            is_compound=True,
            parallel_groups=[[0], [1]],
        )
        wave0 = format_batch_tasks(plan, group_index=0)
        assert len(wave0) == 1
        assert wave0[0]["repo"] == "owner/repo"
        assert "Auth" in wave0[0]["prompt"]
        assert "auth.py" in wave0[0]["prompt"]

        wave1 = format_batch_tasks(plan, group_index=1)
        assert len(wave1) == 1
        assert "Tests" in wave1[0]["prompt"]

    def test_out_of_range(self):
        plan = DecompositionPlan(
            original_prompt="x", repo="o/r", branch="main",
            subtasks=[], is_compound=False, parallel_groups=[],
        )
        assert format_batch_tasks(plan, group_index=5) == []


class TestFormatPlanSummary:
    """Test human-readable plan formatting."""

    def test_simple_plan(self):
        plan = DecompositionPlan(
            original_prompt="Small fix", repo="o/r", branch="main",
            subtasks=[], is_compound=False,
        )
        output = format_plan_summary(plan)
        assert "Simple task" in output

    def test_compound_plan(self):
        plan = DecompositionPlan(
            original_prompt="Big refactor",
            repo="owner/repo",
            branch="dev",
            subtasks=[
                CodeSubTask(prompt="A", focus="API", priority=1, files=["api.py"]),
                CodeSubTask(prompt="B", focus="Tests", priority=2, depends_on=[0]),
            ],
            is_compound=True,
            parallel_groups=[[0], [1]],
            reasoning="2 sub-tasks in 2 waves",
        )
        output = format_plan_summary(plan)
        assert "Wave 1" in output
        assert "Wave 2" in output
        assert "API" in output
        assert "Tests" in output
        assert "owner/repo" in output
