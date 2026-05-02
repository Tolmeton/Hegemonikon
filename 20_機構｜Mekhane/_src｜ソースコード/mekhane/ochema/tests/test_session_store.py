# PROOF: mekhane/ochema/tests/test_session_store.py
# PURPOSE: ochema モジュールの session_store に対するテスト
from __future__ import annotations
import pytest
from pathlib import Path
from mekhane.ochema.session_store import SessionStore

@pytest.fixture
def store(tmp_path: Path):
    """Use an in-memory SQLite for tests via a temp file (WAL works better on temp file than :memory:)."""
    db_file = tmp_path / "test_sessions.db"
    return SessionStore(db_path=db_file)

def test_create_and_add_turns(store: SessionStore):
    session_id = store.create_session("movement", "gemini-3-flash-preview", "test-pipeline")
    assert isinstance(session_id, str)
    assert len(session_id) > 20
    
    # Add turns
    store.add_turn(session_id, "user", "What is 2+2?", 1)
    store.add_turn(session_id, "model", "4.", 2, token_count=10, model="gemini-3-flash-preview", duration_ms=500)
    
    # History
    history = store.get_history(session_id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "What is 2+2?"
    assert history[1]["role"] == "model"
    assert history[1]["content"] == "4."
    assert history[1]["token_count"] == 10

def test_close_session(store: SessionStore):
    session_id = store.create_session("default", "gemini")
    store.close_session(session_id)
    
    # Check updated
    with store._get_conn() as conn:
        row = conn.execute("SELECT closed_at FROM sessions WHERE id = ?", (session_id,)).fetchone()
        assert row["closed_at"] is not None

def test_fts_search(store: SessionStore):
    s1 = store.create_session("A", "model1")
    s2 = store.create_session("B", "model2")
    
    store.add_turn(s1, "user", "Hello world and universe.", 1)
    store.add_turn(s2, "model", "The quick brown fox jumps over the lazy dog.", 1)
    
    # Search 'universe'
    res1 = store.search("universe")
    assert len(res1) == 1
    assert res1[0]["session_id"] == s1
    assert "universe" in res1[0]["snippet"]
    
    # Search 'fox'
    res2 = store.search("fox")
    assert len(res2) == 1
    assert res2[0]["session_id"] == s2

def test_stats_by_account(store: SessionStore):
    s1 = store.create_session("A", "m1")
    s2 = store.create_session("A", "m1")
    s3 = store.create_session("B", "m2")
    
    store.add_turn(s1, "user", "test", 1, token_count=50)
    store.add_turn(s2, "model", "test", 1, token_count=100)
    store.add_turn(s3, "model", "test", 1, token_count=200)
    
    stats = store.get_stats()
    assert stats["total_sessions"] == 3
    assert stats["total_turns"] == 3
    assert stats["by_account"]["A"] == 2
    assert stats["by_account"]["B"] == 1
    assert stats["tokens_by_account"]["A"] == 150
    assert stats["tokens_by_account"]["B"] == 200
