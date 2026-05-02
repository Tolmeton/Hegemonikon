# PROOF: mekhane/tests/test_subagent_registry.py
# PURPOSE: tests モジュールの subagent_registry に対するテスト
"""
AGENT GUARD モジュールのテスト — Subagent Registry (T-21)
"""
import json
import time
from pathlib import Path

import pytest

from mekhane.agent_guard.subagent_registry import (
    RunStatus,
    SubagentRun,
    SubagentRegistry,
)


def test_register_and_complete():
    reg = SubagentRegistry(state_path="/dev/null", max_active=10)
    
    run = reg.register_run("session-1", "jules", prompt="Fix bug")
    assert run.status == RunStatus.RUNNING
    assert run.agent_id == "jules"
    assert reg.count_active() == 1
    
    reg.complete_run(run.run_id, RunStatus.COMPLETED, outcome="PR created")
    assert run.status == RunStatus.COMPLETED
    assert run.outcome == "PR created"
    assert reg.count_active() == 0


def test_list_runs_filter():
    reg = SubagentRegistry(state_path="/dev/null")
    
    r1 = reg.register_run("s1", "jules")
    r2 = reg.register_run("s2", "jules")
    reg.complete_run(r1.run_id, RunStatus.COMPLETED)
    
    active = reg.list_runs(status=RunStatus.RUNNING)
    assert len(active) == 1
    assert active[0].run_id == r2.run_id
    
    s1_runs = reg.list_runs(session_key="s1")
    assert len(s1_runs) == 1
    assert s1_runs[0].run_id == r1.run_id


def test_can_spawn_limit():
    reg = SubagentRegistry(state_path="/dev/null", max_active=2)
    
    reg.register_run("s1", "a1")
    assert reg.can_spawn()
    
    reg.register_run("s1", "a2")
    assert not reg.can_spawn()


def test_sweep_stale():
    reg = SubagentRegistry(state_path="/dev/null")
    
    run = reg.register_run("s1", "jules")
    # started_at を過去に設定
    run.started_at = time.time() - 3600  # 1時間前
    
    swept = reg.sweep_stale(timeout_s=60)  # 60秒タイムアウト
    assert len(swept) == 1
    assert swept[0].run_id == run.run_id
    assert swept[0].status == RunStatus.TIMEOUT
    assert reg.count_active() == 0


def test_persist_and_restore(tmp_path: Path):
    state_path = str(tmp_path / "registry.json")
    
    # 保存
    reg1 = SubagentRegistry(state_path=state_path)
    r1 = reg1.register_run("s1", "jules")
    reg1.complete_run(r1.run_id, RunStatus.COMPLETED, outcome="done")
    r2 = reg1.register_run("s2", "jules")
    reg1.persist()
    
    # 復元
    reg2 = SubagentRegistry(state_path=state_path)
    count = reg2.restore()
    assert count == 2
    
    restored = reg2.get_run(r1.run_id)
    assert restored is not None
    assert restored.status == RunStatus.COMPLETED
    assert restored.outcome == "done"
    
    assert reg2.count_active() == 1  # r2 is still running


def test_stats():
    reg = SubagentRegistry(state_path="/dev/null", max_active=5)
    
    r1 = reg.register_run("s1", "a")
    r2 = reg.register_run("s1", "b")
    reg.complete_run(r1.run_id, RunStatus.COMPLETED)
    reg.complete_run(r2.run_id, RunStatus.FAILED)
    reg.register_run("s2", "c")
    
    stats = reg.stats()
    assert stats["total"] == 3
    assert stats["active"] == 1
    assert stats["completed"] == 1
    assert stats["failed"] == 1
    assert stats["running"] == 1
