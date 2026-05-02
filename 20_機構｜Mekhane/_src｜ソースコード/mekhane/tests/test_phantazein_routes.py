#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/tests/test_phantazein_routes.py
# PURPOSE: Phantazein FastAPI エンドポイントのテスト
"""
Tests for Phantazein API routes.
"""

import pytest
fastapi = pytest.importorskip("fastapi", reason="fastapi not installed")
from fastapi.testclient import TestClient
from pathlib import Path

from mekhane.api.server import app
from mekhane.symploke.phantazein_store import get_store, _store


@pytest.fixture
def mock_store(tmp_path: Path):
    """Provide a temporary SQLite store for tests."""
    global _store
    # Save original
    orig_store = _store
    
    # Override
    test_db = tmp_path / "test_mb.db"
    store = get_store(db_path=test_db)
    
    yield store
    
    # Restore
    store.close()
    import mekhane.symploke.phantazein_store as mb_store
    mb_store._store = orig_store


@pytest.fixture
def client(mock_store):
    return TestClient(app)


# PURPOSE: /phantazein/session/register のテスト
def test_session_register(client: TestClient, monkeypatch):
    async def mock_refresh(*args, **kwargs):
        import mekhane.api.routes.phantazein as mb
        mb._boot_cache = {"mock_axis": "mock_data"}
        mb._boot_cache_time = 9999999999.0

    import mekhane.api.routes.phantazein as mb
    monkeypatch.setattr(mb, "_refresh_boot_cache", mock_refresh)
    
    req_data = {
        "context": "Initial context",
        "agent": "test_agent",
        "mode": "fast"
    }
    response = client.post("/api/phantazein/session/register", json=req_data)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "axes" in data
    # PhantazeinStore に登録されているか確認
    from mekhane.symploke.phantazein_store import get_store
    store = get_store()
    recent = store.get_recent_sessions()
    assert len(recent) == 1
    assert recent[0]["agent"] == "test_agent"


# PURPOSE: /phantazein/project/snapshot のテスト
def test_project_snapshot(client: TestClient):
    req_data = {
        "project_id": "test_proj",
        "phase": "test_phase",
        "status": "green",
        "notes": "doing well",
        "session_id": "ses_123"
    }
    response = client.post("/api/phantazein/project/snapshot", json=req_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["project_id"] == "test_proj"
    
    from mekhane.symploke.phantazein_store import get_store
    store = get_store()
    latest = store.get_latest_snapshot("test_proj")
    assert latest is not None
    assert latest["phase"] == "test_phase"


# PURPOSE: /phantazein/consistency のテスト（Gemini モック）
# ネットワークとトークンを消費するため、OchemaService をモックする
def test_consistency_check(client: TestClient, monkeypatch):
    class MockResult:
        text = '```json\n{"has_issues": true, "issues": [{"severity": "high", "issue": "Conflict", "details": "test"}], "narration": "警告します"}\n```'

    class MockOchemaService:
        async def ask_async(self, *args, **kwargs):
            return MockResult()

    import mekhane.ochema.service
    monkeypatch.setattr(mekhane.ochema.service.OchemaService, "get", lambda: MockOchemaService())

    req_data = {
        "proposed_action": "I will do X",
        "session_id": "test_sess"
    }
    response = client.post("/api/phantazein/consistency", json=req_data)
    assert response.status_code == 200
    data = response.json()
    
    assert data["has_issues"] is True
    assert len(data["issues"]) == 1
    assert data["issues"][0]["issue"] == "Conflict"
    
    # Store に記録されたか？
    from mekhane.symploke.phantazein_store import get_store
    store = get_store()
    issues = store.get_recent_issues()
    assert len(issues) == 1
    assert issues[0]["issue"] == "Conflict"
