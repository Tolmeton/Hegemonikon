from __future__ import annotations

import sqlite3
from pathlib import Path

from mekhane.symploke.phantazein_store import PhantazeinStore


def _columns(store: PhantazeinStore, table: str) -> set[str]:
    rows = store._conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(row[1]) for row in rows}


def _index_names(store: PhantazeinStore, table: str) -> set[str]:
    rows = store._conn.execute(f"PRAGMA index_list('{table}')").fetchall()
    return {str(row[1]) for row in rows}


def test_store_migrates_legacy_project_columns_before_creating_indexes(tmp_path: Path):
    db_path = tmp_path / "legacy" / "phantazein.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY,
            start_time REAL NOT NULL,
            context TEXT DEFAULT '',
            agent TEXT DEFAULT 'claude',
            status TEXT DEFAULT 'active'
        );

        CREATE TABLE handoffs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            filepath TEXT DEFAULT '',
            created_at REAL,
            size_bytes INTEGER DEFAULT 0,
            title TEXT DEFAULT '',
            session_id TEXT,
            project_name TEXT,
            handoff_version TEXT
        );

        CREATE TABLE observations (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            source_ref TEXT DEFAULT '',
            observation_kind TEXT NOT NULL,
            summary TEXT NOT NULL,
            confidence REAL DEFAULT 0.5,
            tags_json TEXT DEFAULT '[]',
            file_paths_json TEXT DEFAULT '[]',
            dedupe_key TEXT NOT NULL UNIQUE,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );

        CREATE TABLE projects (
            id TEXT PRIMARY KEY,
            name TEXT DEFAULT '',
            dir_path TEXT DEFAULT '',
            updated_at REAL DEFAULT 0,
            parent_id TEXT DEFAULT '',
            description TEXT DEFAULT '',
            status TEXT DEFAULT '',
            created_at REAL DEFAULT 0
        );
        """
    )
    conn.commit()
    conn.close()

    store = PhantazeinStore(db_path=db_path)

    assert "project_id" in _columns(store, "sessions")
    assert "project_id" in _columns(store, "handoffs")
    assert "project_id" in _columns(store, "observations")
    assert "project_id" in _columns(store, "projects")

    assert "idx_sessions_project" in _index_names(store, "sessions")
    assert "idx_handoffs_project" in _index_names(store, "handoffs")
    assert "idx_obs_project" in _index_names(store, "observations")
    assert "idx_projects_project_id" in _index_names(store, "projects")

    store.upsert_project("legacy/pinakas", "Pinakas")
    project = store._conn.execute(
        "SELECT id, project_id, name FROM projects WHERE project_id = ?",
        ("legacy/pinakas",),
    ).fetchone()
    assert project is not None
    assert tuple(project) == ("legacy/pinakas", "legacy/pinakas", "Pinakas")

    store.close()


def test_link_session_project_skips_legacy_fk_mismatch(tmp_path: Path):
    db_path = tmp_path / "legacy-fk" / "phantazein.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE ide_sessions (
            id TEXT PRIMARY KEY,
            title TEXT DEFAULT '',
            created_at REAL,
            updated_at REAL,
            dir_path TEXT DEFAULT '',
            artifact_count INTEGER DEFAULT 0
        );

        CREATE TABLE projects (
            id TEXT PRIMARY KEY,
            name TEXT DEFAULT '',
            dir_path TEXT DEFAULT '',
            updated_at REAL NOT NULL,
            parent_id TEXT DEFAULT NULL,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            created_at REAL DEFAULT 0.0
        );

        CREATE TABLE session_projects (
            session_id TEXT NOT NULL REFERENCES ide_sessions(id),
            project_id TEXT NOT NULL REFERENCES projects(id),
            PRIMARY KEY (session_id, project_id)
        );
        """
    )
    conn.commit()
    conn.close()

    store = PhantazeinStore(db_path=db_path)
    store.upsert_project("legacy/pinakas", "Pinakas")
    store.link_session_project("missing-session", "legacy/pinakas")

    rows = store._conn.execute("SELECT session_id, project_id FROM session_projects").fetchall()
    assert rows == []

    store.upsert_ide_session("sess-1", title="Pinakas")
    store.link_session_project("sess-1", "legacy/pinakas")
    rows = store._conn.execute("SELECT session_id, project_id FROM session_projects").fetchall()
    assert [tuple(row) for row in rows] == [("sess-1", "legacy/pinakas")]

    store.close()
