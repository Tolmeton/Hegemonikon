# PROOF: [L1/機能] <- mekhane/ochema/session_store.py A0→永続化→Cortex API セッションログ
# PURPOSE: Cortex API の会話履歴を MECE な3層スキーマ (session/turn/part) で SQLite に永続化する。
#   FTS5 を用いて全文検索をサポート。

from __future__ import annotations
from typing import Any, Optional
import sqlite3
import uuid
import time
import json
from pathlib import Path

import logging

logger = logging.getLogger(__name__)

# Default location: ~/.config/ochema/sessions.db
_DEFAULT_DB_PATH = Path.home() / ".config" / "ochema" / "sessions.db"

# PURPOSE: [L2-auto] SessionStore のクラス定義
class SessionStore:
    """SQLite-based session log for Cortex API conversations."""

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path or _DEFAULT_DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # PURPOSE: [L2-auto] _get_conn の関数定義
    def _get_conn(self) -> sqlite3.Connection:
        """Get a configured SQLite connection."""
        conn = sqlite3.connect(self._db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        # Enable WAL for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        # Ensure foreign keys are enforced
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # PURPOSE: [L2-auto] _init_db の関数定義
    def _init_db(self) -> None:
        """Initialize SQLite schema if it doesn't exist."""
        with self._get_conn() as conn:
            # 1. Sessions table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id          TEXT PRIMARY KEY,
                    account     TEXT NOT NULL,
                    model       TEXT NOT NULL,
                    pipeline    TEXT DEFAULT '',
                    created_at  TEXT NOT NULL,
                    closed_at   TEXT,
                    metadata    TEXT DEFAULT '{}'
                )
            ''')

            # 2. Turns table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS turns (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    turn_number INTEGER NOT NULL,
                    role        TEXT NOT NULL,
                    content     TEXT NOT NULL,
                    token_count INTEGER DEFAULT 0,
                    model       TEXT DEFAULT '',
                    duration_ms INTEGER DEFAULT 0,
                    created_at  TEXT NOT NULL,
                    UNIQUE(session_id, turn_number, role)
                )
            ''')

            # 3. FTS5 Virtual Table for full-text search on turns content
            # fts5 allows efficient searching of text. content=turns, content_rowid=id makes it an external content table
            conn.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS turns_fts USING fts5(
                    content,
                    content=turns,
                    content_rowid=id
                )
            ''')
            
            # Triggers to keep FTS table in sync with turns
            conn.execute('''
                CREATE TRIGGER IF NOT EXISTS turns_ai AFTER INSERT ON turns BEGIN
                    INSERT INTO turns_fts(rowid, content) VALUES (new.id, new.content);
                END;
            ''')
            conn.execute('''
                CREATE TRIGGER IF NOT EXISTS turns_ad AFTER DELETE ON turns BEGIN
                    INSERT INTO turns_fts(turns_fts, rowid, content) VALUES ('delete', old.id, old.content);
                END;
            ''')
            conn.execute('''
                CREATE TRIGGER IF NOT EXISTS turns_au AFTER UPDATE ON turns BEGIN
                    INSERT INTO turns_fts(turns_fts, rowid, content) VALUES ('delete', old.id, old.content);
                    INSERT INTO turns_fts(rowid, content) VALUES (new.id, new.content);
                END;
            ''')
            
            # Indexes
            conn.execute('CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id, turn_number)')

    # PURPOSE: [L2-auto] create_session の関数定義
    def create_session(self, account: str, model: str, pipeline: str = "", metadata: Optional[dict[str, Any]] = None) -> str:
        """Create a new session and return its UUID."""
        session_id = str(uuid.uuid4())
        created_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        meta_str = json.dumps(metadata or {}, ensure_ascii=False)
        
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO sessions (id, account, model, pipeline, created_at, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, account, model, pipeline, created_at, meta_str)
            )
        logger.info("Created session %s (account=%s, model=%s)", session_id[:8], account, model)
        return session_id

    # PURPOSE: [L2-auto] add_turn の関数定義
    def add_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        turn_number: int,
        token_count: int = 0,
        model: str = "",
        duration_ms: int = 0
    ) -> int:
        """Append a turn to the session. Returns the turn's internal ID.
        
        Args:
            session_id: UUID of the session
            role: 'user' or 'model' (or 'system')
            content: The text content
            turn_number: Logical turn number in the conversation
            token_count: Tokens used (for model responses)
            model: Actual model used (if overriding session default)
            duration_ms: Request duration in ms
        """
        created_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO turns 
                (session_id, turn_number, role, content, token_count, model, duration_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, turn_number, role, content, token_count, model, duration_ms, created_at)
            )
            return cursor.lastrowid

    # PURPOSE: list_sessions — 直近セッション一覧を返す
    def list_sessions(self, limit: int = 20) -> list[dict[str, Any]]:
        """List recent sessions, ordered by created_at ascending.
        
        Note: ASC order so that sessions[-1] returns the latest session,
        matching the pattern in boot_axes.py and session_notes.py.
        
        Returns list of dicts with keys:
            session_id, account, model, pipeline, created_at, closed_at
        """
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                SELECT id as session_id, account, model, pipeline, 
                       created_at, closed_at
                FROM sessions 
                ORDER BY created_at DESC 
                LIMIT ?
                """,
                (limit,)
            )
            # Reverse to ASC so [-1] = latest
            rows = [dict(row) for row in cursor.fetchall()]
            rows.reverse()
            return rows

    # PURPOSE: [L2-auto] close_session の関数定義
    def close_session(self, session_id: str) -> None:
        """Mark a session as closed."""
        closed_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        with self._get_conn() as conn:
            conn.execute("UPDATE sessions SET closed_at = ? WHERE id = ?", (closed_at, session_id))

    # PURPOSE: [L2-auto] get_history の関数定義
    def get_history(self, session_id: str) -> list[dict[str, Any]]:
        """Get the full conversation history. Useful for resuming or exporting."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT turn_number, role, content, model, token_count, duration_ms FROM turns WHERE session_id = ? ORDER BY turn_number ASC, _rowid_ ASC",
                (session_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    # PURPOSE: [L2-auto] search の関数定義
    def search(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        """FTS5 full-text search across all turns."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                SELECT t.session_id, t.turn_number, t.role, t.content, 
                       snippet(turns_fts, -1, '>>>', '<<<', '...', 64) as snippet,
                       s.account, s.created_at
                FROM turns_fts f
                JOIN turns t ON f.rowid = t.id
                JOIN sessions s ON t.session_id = s.id
                WHERE turns_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (query, limit)
            )
            return [dict(row) for row in cursor.fetchall()]

    # PURPOSE: [L2-auto] get_stats の関数定義
    def get_stats(self) -> dict[str, Any]:
        """Aggregate stats."""
        stats = {}
        with self._get_conn() as conn:
            stats['total_sessions'] = conn.execute("SELECT count(*) FROM sessions").fetchone()[0]
            stats['total_turns'] = conn.execute("SELECT count(*) FROM turns").fetchone()[0]
            
            # By account
            cur = conn.execute("SELECT account, count(*) as c FROM sessions GROUP BY account")
            stats['by_account'] = {row['account']: row['c'] for row in cur.fetchall()}
            
            # By model
            cur = conn.execute("SELECT model, count(*) as c FROM sessions GROUP BY model")
            stats['by_model'] = {row['model']: row['c'] for row in cur.fetchall()}
            
            # Total tokens by account
            cur = conn.execute("""
                SELECT s.account, sum(t.token_count) as tokens
                FROM turns t JOIN sessions s ON t.session_id = s.id
                GROUP BY s.account
            """)
            stats['tokens_by_account'] = {row['account']: row['tokens'] for row in cur.fetchall() if row['tokens']}
            
        return stats

# Global default instance (lazy init)
_STORE: Optional[SessionStore] = None

# PURPOSE: [L2-auto] get_default_store の関数定義
def get_default_store() -> SessionStore:
    global _STORE
    if _STORE is None:
        _STORE = SessionStore()
    return _STORE
