from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from mekhane.api.routes import phantazein as route_module
from mekhane.symploke.phantazein_store import PhantazeinStore


def _make_client(monkeypatch, tmp_path: Path) -> tuple[TestClient, PhantazeinStore]:
    store = PhantazeinStore(db_path=tmp_path / "phantazein-test.db")
    monkeypatch.setattr(
        "mekhane.symploke.phantazein_store.get_store",
        lambda db_path=None: store,
    )
    monkeypatch.setattr(route_module, "_boot_cache", {"boot": "ok"})
    monkeypatch.setattr(route_module, "_boot_cache_time", 1.0)
    monkeypatch.setattr(route_module, "_refresh_task", None)

    async def _fake_background_refresh_loop() -> None:
        route_module._boot_cache = {"boot": "ok"}
        route_module._boot_cache_time = 1.0
        return None

    monkeypatch.setattr(route_module, "_background_refresh_loop", _fake_background_refresh_loop)

    app = FastAPI()
    app.include_router(route_module.router, prefix="/api")
    return TestClient(app), store


def test_session_register_accepts_external_session_id_and_returns_boot_packet(
    monkeypatch,
    tmp_path: Path,
):
    client, store = _make_client(monkeypatch, tmp_path)
    store.upsert_observation(
        session_id="old-sess",
        source_kind="context_pack",
        source_ref="/tmp/context.json",
        observation_kind="decision",
        summary="前回 goal",
        confidence=1.0,
        tags=["goal"],
        file_paths=[],
    )

    response = client.post(
        "/api/phantazein/session/register",
        json={"session_id": "hook-sess", "agent": "codex", "context": "cwd=/tmp"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "hook-sess"
    assert data["axes"] == {"boot": "ok"}
    assert "recent_project_goal: 前回 goal" in data["boot_packet"]
    assert store.get_recent_sessions(limit=1)[0]["id"] == "hook-sess"


def test_observe_tool_and_inject_file_round_trip(monkeypatch, tmp_path: Path):
    client, _store = _make_client(monkeypatch, tmp_path)
    file_path = str((tmp_path / "core.py").resolve())

    observe = client.post(
        "/api/phantazein/observe/tool",
        json={
            "event": {
                "session_id": "sess-tool",
                "tool_name": "Edit",
                "tool_input": {"file_path": file_path},
                "tool_output": "warning: duplicate key",
            }
        },
    )
    assert observe.status_code == 200
    assert observe.json()["ingested"] == 2

    inject = client.post(
        "/api/phantazein/inject/file",
        json={"session_id": "sess-tool", "file_path": file_path},
    )
    assert inject.status_code == 200
    data = inject.json()
    assert "file_observations" in data["packet"]
    assert any(obs_id.startswith("obs-") for obs_id in data["observation_ids"])


def test_observe_stop_marks_session_completed(monkeypatch, tmp_path: Path):
    client, store = _make_client(monkeypatch, tmp_path)
    store.register_session(session_id="sess-stop", agent="codex")

    decision_log = tmp_path / "decision.json"
    decision_log.write_text(
        json.dumps(
            {
                "session_id": "sess-stop",
                "assistant_summary": "stop summary",
                "warnings": ["constraint text"],
                "self_impl_files": [str((tmp_path / "core.py").resolve())],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    context_pack = tmp_path / "context.json"
    context_pack.write_text(
        json.dumps(
            {
                "session_id": "sess-stop",
                "goal": "goal text",
                "key_files": [str((tmp_path / "core.py").resolve())],
                "open_questions": ["todo text"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return_ticket = tmp_path / "ticket.json"
    return_ticket.write_text(
        json.dumps(
            {
                "task_id": "session-sess-stop",
                "unresolved": ["constraint text"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "mekhane.symploke.phantazein_observation.load_latest_handoff_summary",
        lambda: None,
    )

    response = client.post(
        "/api/phantazein/observe/stop",
        json={
            "session_id": "sess-stop",
            "decision_log_path": str(decision_log),
            "context_pack_path": str(context_pack),
            "return_ticket_path": str(return_ticket),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ingested"] >= 4
    sessions = store.get_recent_sessions(limit=5)
    session = next(item for item in sessions if item["id"] == "sess-stop")
    assert session["status"] == "completed"
