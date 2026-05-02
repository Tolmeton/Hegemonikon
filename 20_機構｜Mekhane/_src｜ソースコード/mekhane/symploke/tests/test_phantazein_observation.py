from __future__ import annotations

import json
from pathlib import Path

from mekhane.symploke import phantazein_observation as obs


class _FakeStore:
    def __init__(self, observations=None, linked=None):
        self._observations = observations or []
        self._linked = linked or {}

    def get_recent_observations(self, *, limit=10, min_confidence=0.0, kinds=None, session_id=None, project_id=None):
        rows = []
        for item in self._observations:
            if item["confidence"] < min_confidence:
                continue
            if kinds and item["observation_kind"] not in kinds:
                continue
            if session_id and item["session_id"] != session_id:
                continue
            if project_id and item.get("project_id", "") != project_id:
                continue
            rows.append(item)
        return rows[:limit]

    def get_linked_observations(self, *, link_type, link_ref, limit=10, min_confidence=0.0, kinds=None, session_id=None, project_id=None):
        rows = []
        for item in self._linked.get((link_type, link_ref), []):
            if item["confidence"] < min_confidence:
                continue
            if kinds and item["observation_kind"] not in kinds:
                continue
            if session_id and item["session_id"] != session_id:
                continue
            if project_id and item.get("project_id", "") != project_id:
                continue
            rows.append(item)
        return rows[:limit]


def test_tool_event_to_specs_creates_file_and_warning_observations(tmp_path: Path):
    file_path = tmp_path / "foo.py"
    event = {
        "session_id": "sess-1",
        "tool_name": "Edit",
        "tool_input": {"file_path": str(file_path)},
        "tool_output": "warning: duplicate definition detected",
    }

    specs = obs.tool_event_to_specs(event)

    assert [spec.observation_kind for spec in specs] == ["file_fact", "warning"]
    assert specs[0].file_paths == [str(file_path.resolve())]
    assert specs[0].confidence == 0.8
    assert specs[1].confidence == 0.5


def test_legacy_artifacts_to_specs_extracts_goal_constraints_and_files(
    monkeypatch,
    tmp_path: Path,
):
    decision_log = tmp_path / "decision.json"
    decision_log.write_text(
        json.dumps(
            {
                "session_id": "sess-2",
                "assistant_summary": "Phantazein を主系にする。",
                "self_impl_files": [str((tmp_path / "core.py").resolve())],
                "warnings": ["legacy warning"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    context_pack = tmp_path / "context.json"
    context_pack.write_text(
        json.dumps(
            {
                "session_id": "sess-2",
                "goal": "boot packet を薄く復元する",
                "key_files": [str((tmp_path / "core.py").resolve())],
                "open_questions": ["Pinakas をどこまで出すか"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return_ticket = tmp_path / "ticket.json"
    return_ticket.write_text(
        json.dumps(
            {
                "task_id": "session-sess-2",
                "unresolved": ["queue pending"],
                "next_task_context": {"warnings": ["queue pending"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        obs,
        "load_latest_handoff_summary",
        lambda: {
            "path": str((tmp_path / "handoff.md").resolve()),
            "title": "handoff.md",
            "summary": "直近 Handoff の要約",
        },
    )

    specs = obs.legacy_artifacts_to_specs(
        decision_log_path=str(decision_log),
        context_pack_path=str(context_pack),
        return_ticket_path=str(return_ticket),
    )

    kinds = {spec.observation_kind for spec in specs}
    assert {"decision", "constraint", "todo", "file_fact", "handoff"} <= kinds
    assert any("goal" in spec.tags for spec in specs if spec.observation_kind == "decision")


def test_build_boot_packet_respects_order_and_limit(monkeypatch):
    observations = [
        {
            "id": "goal-1",
            "session_id": "old",
            "project_id": "proj-1",
            "observation_kind": "decision",
            "summary": "goal summary",
            "confidence": 1.0,
            "tags": ["goal"],
            "file_paths": [],
        },
        {
            "id": "dec-1",
            "session_id": "old",
            "project_id": "proj-1",
            "observation_kind": "decision",
            "summary": "important decision",
            "confidence": 1.0,
            "tags": [],
            "file_paths": [],
        },
        {
            "id": "warn-1",
            "session_id": "old",
            "project_id": "proj-1",
            "observation_kind": "constraint",
            "summary": "active warning",
            "confidence": 1.0,
            "tags": [],
            "file_paths": [],
        },
        {
            "id": "file-1",
            "session_id": "old",
            "project_id": "proj-1",
            "observation_kind": "file_fact",
            "summary": "Touched file: /tmp/core.py",
            "confidence": 1.0,
            "tags": [],
            "file_paths": ["/tmp/core.py"],
        },
        {
            "id": "handoff-1",
            "session_id": "old",
            "project_id": "proj-1",
            "observation_kind": "handoff",
            "summary": "latest handoff summary",
            "confidence": 0.8,
            "tags": [],
            "file_paths": [],
        },
        {
            "id": "todo-1",
            "session_id": "old",
            "project_id": "proj-1",
            "observation_kind": "todo",
            "summary": "follow-up todo",
            "confidence": 1.0,
            "tags": [],
            "file_paths": [],
        },
    ]
    monkeypatch.setattr(
        obs,
        "load_active_pinakas_items",
        lambda limit=8: [{"id": "T-001", "board": "task", "priority": "high", "text": "pinakas item"}],
    )

    packet, observation_ids = obs.build_boot_packet(
        _FakeStore(observations=observations),
        "sess-new",
        project_id="proj-1",
        previous_session_id="old",
    )

    assert len(packet) <= obs.BOOT_PACKET_LIMIT
    assert "prev_goal: goal summary" in packet
    assert "latest_decisions" in packet
    assert "active_pinakas" in packet
    assert observation_ids[0] == "goal-1"


def test_build_file_packet_uses_linked_observations(monkeypatch):
    file_path = "/tmp/core.py"
    linked = {
        ("file_path", file_path): [
            {
                "id": "file-1",
                "session_id": "sess-3",
                "project_id": "proj-1",
                "observation_kind": "file_fact",
                "summary": "Edit: /tmp/core.py",
                "confidence": 0.8,
                "tags": [],
                "file_paths": [file_path],
            },
            {
                "id": "dec-1",
                "session_id": "sess-3",
                "project_id": "proj-1",
                "observation_kind": "decision",
                "summary": "core.py を中心に変更する",
                "confidence": 1.0,
                "tags": [],
                "file_paths": [file_path],
            },
        ]
    }
    observations = [
        {
            "id": "handoff-1",
            "session_id": "sess-2",
            "project_id": "proj-1",
            "observation_kind": "handoff",
            "summary": "latest handoff summary",
            "confidence": 0.8,
            "tags": [],
            "file_paths": [],
        }
    ]
    monkeypatch.setattr(
        obs,
        "matching_pinakas_items",
        lambda file_path, limit=3: [{"id": "WB-001", "board": "whiteboard", "priority": "", "text": "core.py memo"}],
    )

    packet, observation_ids = obs.build_file_packet(
        _FakeStore(observations=observations, linked=linked),
        "sess-3",
        file_path,
        project_id="proj-1",
        previous_session_id="sess-2",
    )

    assert len(packet) <= obs.FILE_PACKET_LIMIT
    assert "file_observations" in packet
    assert "related_decision" in packet
    assert "related_pinakas" in packet
    assert observation_ids == ["file-1", "dec-1", "handoff-1"]


def test_scoped_packets_do_not_bleed_other_projects():
    observations = [
        {
            "id": "goal-a",
            "session_id": "sess-A",
            "project_id": "proj-A",
            "observation_kind": "decision",
            "summary": "A goal",
            "confidence": 1.0,
            "tags": ["goal"],
            "file_paths": ["/tmp/a.py"],
        },
        {
            "id": "warn-a",
            "session_id": "sess-A",
            "project_id": "proj-A",
            "observation_kind": "constraint",
            "summary": "A warning",
            "confidence": 1.0,
            "tags": ["warning"],
            "file_paths": ["/tmp/a.py"],
        },
        {
            "id": "handoff-a",
            "session_id": "sess-A",
            "project_id": "proj-A",
            "observation_kind": "handoff",
            "summary": "A handoff",
            "confidence": 0.8,
            "tags": ["latest_handoff"],
            "file_paths": [],
        },
        {
            "id": "goal-b",
            "session_id": "sess-B",
            "project_id": "proj-B",
            "observation_kind": "decision",
            "summary": "B goal",
            "confidence": 1.0,
            "tags": ["goal"],
            "file_paths": ["/tmp/b.py"],
        },
        {
            "id": "file-b",
            "session_id": "sess-B",
            "project_id": "proj-B",
            "observation_kind": "file_fact",
            "summary": "Touched file: /tmp/b.py",
            "confidence": 1.0,
            "tags": ["touched_file"],
            "file_paths": ["/tmp/b.py"],
        },
    ]
    linked = {
        ("file_path", "/tmp/b.py"): [
            observations[4],
            observations[3],
        ]
    }

    boot_packet, _ = obs.build_boot_packet(
        _FakeStore(observations=observations, linked=linked),
        "sess-B",
        project_id="proj-B",
        previous_session_id="sess-A",
    )
    file_packet, _ = obs.build_file_packet(
        _FakeStore(observations=observations, linked=linked),
        "sess-B",
        "/tmp/b.py",
        project_id="proj-B",
        previous_session_id="sess-A",
    )

    assert "A warning" not in boot_packet
    assert "A handoff" not in file_packet
    assert "B goal" in boot_packet
