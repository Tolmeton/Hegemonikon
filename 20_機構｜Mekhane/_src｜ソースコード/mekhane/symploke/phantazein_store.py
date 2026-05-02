#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/phantazein_store.py
# PURPOSE: Phantazein 永続状態ストア — SQLite による sessions / project_snapshots / consistency_log 管理
"""
Phantazein Store — F1 常時 Boot 機構の永続状態層

Tables:
  - sessions: セッション登録 (id, start_time, context, agent, status)
  - project_snapshots: PJ 進捗スナップショット (project_id, timestamp, phase, status, notes)
  - consistency_log: 不整合検知ログ (timestamp, session_id, issue, severity)

DB Path: 30_記憶｜Mneme/05_状態｜State/phantazein.db
"""

import sqlite3
import time
import uuid
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger("hegemonikon.phantazein.store")

# ── Data Models ─────────────────────────────────────────────


@dataclass
class Session:
    """セッション登録レコード."""

    id: str = ""
    start_time: float = 0.0
    context: str = ""
    agent: str = "claude"
    status: str = "active"  # active | completed | abandoned

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if self.start_time == 0.0:
            self.start_time = time.time()


@dataclass
class ProjectSnapshot:
    """PJ 進捗スナップショット."""

    project_id: str = ""
    timestamp: float = 0.0
    phase: str = ""
    status: str = ""
    notes: str = ""
    session_id: str = ""

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class ConsistencyIssue:
    """不整合検知レコード."""

    timestamp: float = 0.0
    session_id: str = ""
    issue: str = ""
    severity: str = "medium"  # low | medium | high | critical
    details: str = ""

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


# ── Store ───────────────────────────────────────────────────


# PURPOSE: Phantazein の永続状態を SQLite で管理する
class PhantazeinStore:
    """SQLite-backed persistent store for Phantazein.

    Thread-safe: uses check_same_thread=False for async compatibility.
    All writes are atomic (autocommit per operation).
    """

    # PURPOSE: Store を初期化し、テーブルを作成する
    def __init__(self, db_path: Optional[Path] = None) -> None:
        if db_path is None:
            from mekhane.paths import MNEME_STATE

            db_path = MNEME_STATE / "phantazein.db"

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db_path = db_path
        self._has_fts: bool = False
        self._conn = sqlite3.connect(
            str(db_path), check_same_thread=False, timeout=10.0
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()
        logger.info("PhantazeinStore initialized: %s", db_path)

    def _create_tables(self) -> None:
        """Create tables if they don't exist."""
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                start_time REAL NOT NULL,
                context TEXT DEFAULT '',
                agent TEXT DEFAULT 'claude',
                status TEXT DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS project_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                phase TEXT DEFAULT '',
                status TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                session_id TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS consistency_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                session_id TEXT DEFAULT '',
                issue TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                details TEXT DEFAULT ''
            );

            -- S2: IDE セッション (brain/ ディレクトリから取得)
            CREATE TABLE IF NOT EXISTS ide_sessions (
                id TEXT PRIMARY KEY,
                title TEXT DEFAULT '',
                created_at REAL,
                updated_at REAL,
                dir_path TEXT DEFAULT '',
                artifact_count INTEGER DEFAULT 0
            );

            -- S2: アーティファクト (セッション内の .md ファイル)
            CREATE TABLE IF NOT EXISTS artifacts (
                session_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                artifact_type TEXT DEFAULT 'other',
                summary TEXT DEFAULT '',
                size_bytes INTEGER DEFAULT 0,
                created_at REAL,
                updated_at REAL,
                version TEXT DEFAULT '',
                is_standard INTEGER DEFAULT 0,
                PRIMARY KEY (session_id, filename)
            );

            -- S2: Handoff ファイル
            CREATE TABLE IF NOT EXISTS handoffs (
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

            -- S2: ROM ファイル
            CREATE TABLE IF NOT EXISTS roms (
                filename TEXT PRIMARY KEY,
                filepath TEXT DEFAULT '',
                created_at REAL,
                size_bytes INTEGER DEFAULT 0,
                topic TEXT DEFAULT '',
                session_id TEXT
            );

            -- S2: プロジェクト
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                name TEXT DEFAULT ''
            );

            -- S2: セッション × プロジェクト 紐づけ
            CREATE TABLE IF NOT EXISTS session_projects (
                session_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                PRIMARY KEY (session_id, project_id)
            );

            -- S2: Handoff η/ε 連鎖
            CREATE TABLE IF NOT EXISTS handoff_chains (
                handoff_id TEXT NOT NULL,
                source_session_id TEXT NOT NULL,
                target_session_id TEXT NOT NULL,
                PRIMARY KEY (handoff_id, source_session_id, target_session_id)
            );

            -- S3: 知識ノード (Hyphē 統一索引)
            CREATE TABLE IF NOT EXISTS knowledge_nodes (
                id TEXT PRIMARY KEY,
                source TEXT DEFAULT '',
                source_id TEXT DEFAULT '',
                title TEXT DEFAULT '',
                content_preview TEXT DEFAULT '',
                metadata_json TEXT DEFAULT '{}',
                session_id TEXT,
                project_id TEXT,
                precision REAL DEFAULT 0.5,
                density REAL DEFAULT 0.0,
                created_at REAL,
                updated_at REAL
            );

            -- S3: 知識エッジ
            CREATE TABLE IF NOT EXISTS knowledge_edges (
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                evidence TEXT DEFAULT '',
                PRIMARY KEY (from_id, to_id, relation_type)
            );

            CREATE INDEX IF NOT EXISTS idx_snapshots_project
                ON project_snapshots(project_id);
            CREATE INDEX IF NOT EXISTS idx_snapshots_time
                ON project_snapshots(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_consistency_time
                ON consistency_log(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_sessions_time
                ON sessions(start_time DESC);
            CREATE INDEX IF NOT EXISTS idx_ide_sessions_created
                ON ide_sessions(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_artifacts_session
                ON artifacts(session_id);
            CREATE INDEX IF NOT EXISTS idx_handoffs_created
                ON handoffs(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_roms_created
                ON roms(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_kn_source
                ON knowledge_nodes(source);

            -- V-012: MCP サーバーヘルスチェック履歴
            CREATE TABLE IF NOT EXISTS health_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                server_name TEXT NOT NULL,
                port INTEGER NOT NULL,
                status TEXT NOT NULL,
                latency_ms REAL DEFAULT 0,
                error TEXT DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_health_time
                ON health_checks(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_health_server
                ON health_checks(server_name, timestamp DESC);

            -- F2: 場の固有軸 (Fisher 固有分解結果の永続化)
            CREATE TABLE IF NOT EXISTS field_axes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                computed_at TEXT NOT NULL,
                k INTEGER NOT NULL,
                gap_index INTEGER DEFAULT 0,
                sloppy_ratio REAL DEFAULT 0.0,
                total_points INTEGER DEFAULT 0,
                eigenvalues_json TEXT DEFAULT '[]',
                eigenvectors_blob BLOB,
                source_filter TEXT DEFAULT '',
                use_centroids INTEGER DEFAULT 0,
                k_neighbors INTEGER DEFAULT 10
            );
            CREATE INDEX IF NOT EXISTS idx_field_axes_time
                ON field_axes(computed_at DESC);

            -- F2: セッション分類結果
            CREATE TABLE IF NOT EXISTS session_classifications (
                session_id TEXT NOT NULL,
                axes_id INTEGER NOT NULL,
                cluster_id INTEGER DEFAULT -1,
                cluster_label TEXT DEFAULT '',
                coords_json TEXT DEFAULT '[]',
                tags_json TEXT DEFAULT '[]',
                confidence REAL DEFAULT 0.0,
                classified_at REAL NOT NULL,
                PRIMARY KEY (session_id, axes_id),
                FOREIGN KEY (axes_id) REFERENCES field_axes(id)
            );
            CREATE INDEX IF NOT EXISTS idx_sc_axes
                ON session_classifications(axes_id);
            CREATE INDEX IF NOT EXISTS idx_sc_cluster
                ON session_classifications(cluster_label);

            -- Always-On Boot: 軸ごとのキャッシュ
            CREATE TABLE IF NOT EXISTS boot_context_cache (
                axis_key TEXT NOT NULL,
                mode TEXT NOT NULL DEFAULT 'standard',
                data_json TEXT NOT NULL DEFAULT '{}',
                formatted TEXT NOT NULL DEFAULT '',
                updated_at REAL NOT NULL,
                stale_after REAL NOT NULL,
                PRIMARY KEY (axis_key, mode)
            );

            -- GAP-2: PhantasiaField ⇔ PhantazeinStore 統合
            -- 溶解イベントの記録 (セッション毎)
            CREATE TABLE IF NOT EXISTS phantasia_dissolves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                source_type TEXT DEFAULT 'session',
                chunk_count INTEGER NOT NULL,
                total_chars INTEGER DEFAULT 0,
                dissolved_at TEXT NOT NULL,
                UNIQUE(session_id, dissolved_at)
            );
            CREATE INDEX IF NOT EXISTS idx_pd_session
                ON phantasia_dissolves(session_id);

            -- 場の統計スナップショット (タイムシリーズ)
            CREATE TABLE IF NOT EXISTS phantasia_field_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_chunks INTEGER DEFAULT 0,
                total_tables INTEGER DEFAULT 0,
                avg_density REAL DEFAULT 0.0,
                recorded_at TEXT NOT NULL
            );

            -- 場の設定 (KV 形式)
            CREATE TABLE IF NOT EXISTS phantasia_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            -- Boot 軸タイミング (自己観測データ — FEP 感覚入力)
            -- boot システムが自身のパフォーマンスを記録し、
            -- 次回 boot で軸分類の prior を更新するフィードバックループの基盤
            CREATE TABLE IF NOT EXISTS boot_axis_timings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                boot_id TEXT NOT NULL,
                axis_name TEXT NOT NULL,
                elapsed_sec REAL NOT NULL,
                status TEXT DEFAULT 'ok',
                mode TEXT DEFAULT 'standard',
                recorded_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_bat_axis
                ON boot_axis_timings(axis_name, recorded_at DESC);
            CREATE INDEX IF NOT EXISTS idx_bat_boot
                ON boot_axis_timings(boot_id);
            """
        )
        # S3: FTS5 全文検索テーブル (エラー耐性)
        try:
            self._conn.execute(
                """CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_nodes_fts
                   USING fts5(id, title, content_preview)"""
            )
            self._has_fts = True
        except Exception:  # noqa: BLE001
            self._has_fts = False
            logger.warning("FTS5 not available, falling back to LIKE search")

        # マイグレーション: Hyphē 拡張 — density カラム追加 (既存 DB 互換)
        try:
            cols = [
                row[1]
                for row in self._conn.execute(
                    "PRAGMA table_info(knowledge_nodes)"
                ).fetchall()
            ]
            if "density" not in cols:
                self._conn.execute(
                    "ALTER TABLE knowledge_nodes ADD COLUMN density REAL DEFAULT 0.0"
                )
                self._conn.commit()
                logger.info("Migrated knowledge_nodes: added density column")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Migration check failed (non-fatal): {e}")

    # ── Session CRUD ────────────────────────────────────────

    # PURPOSE: 新しいセッションを登録する
    def register_session(
        self,
        context: str = "",
        agent: str = "claude",
    ) -> Session:
        """Register a new session. Returns the created Session."""
        session = Session(context=context, agent=agent)
        self._conn.execute(
            "INSERT INTO sessions (id, start_time, context, agent, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (session.id, session.start_time, session.context, session.agent, session.status),
        )
        self._conn.commit()
        logger.info("Session registered: %s (agent=%s)", session.id, agent)
        return session

    # PURPOSE: セッションのステータスを更新する
    def update_session_status(self, session_id: str, status: str) -> None:
        """Update session status (active → completed | abandoned)."""
        self._conn.execute(
            "UPDATE sessions SET status = ? WHERE id = ?",
            (status, session_id),
        )
        self._conn.commit()

    # PURPOSE: 直近のセッション一覧を取得する
    def get_recent_sessions(self, limit: int = 5) -> list[dict]:
        """Get recent sessions ordered by start_time DESC."""
        rows = self._conn.execute(
            "SELECT * FROM sessions ORDER BY start_time DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Project Snapshot CRUD ───────────────────────────────

    # PURPOSE: PJ 進捗のスナップショットを記録する
    def add_project_snapshot(
        self,
        project_id: str,
        phase: str = "",
        status: str = "",
        notes: str = "",
        session_id: str = "",
    ) -> ProjectSnapshot:
        """Add a project progress snapshot."""
        snap = ProjectSnapshot(
            project_id=project_id,
            phase=phase,
            status=status,
            notes=notes,
            session_id=session_id,
        )
        self._conn.execute(
            "INSERT INTO project_snapshots "
            "(project_id, timestamp, phase, status, notes, session_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (snap.project_id, snap.timestamp, snap.phase, snap.status, snap.notes, snap.session_id),
        )
        self._conn.commit()
        logger.info("Project snapshot: %s → phase=%s, status=%s", project_id, phase, status)
        return snap

    # PURPOSE: 特定 PJ の直近スナップショットを取得する
    def get_latest_snapshot(self, project_id: str) -> Optional[dict]:
        """Get the latest snapshot for a project."""
        row = self._conn.execute(
            "SELECT * FROM project_snapshots "
            "WHERE project_id = ? ORDER BY timestamp DESC LIMIT 1",
            (project_id,),
        ).fetchone()
        return dict(row) if row else None

    # PURPOSE: 全 PJ の最新スナップショットを一括取得する
    def get_all_latest_snapshots(self) -> list[dict]:
        """Get the latest snapshot for each project."""
        rows = self._conn.execute(
            """
            SELECT ps.* FROM project_snapshots ps
            INNER JOIN (
                SELECT project_id, MAX(timestamp) as max_ts
                FROM project_snapshots
                GROUP BY project_id
            ) latest
            ON ps.project_id = latest.project_id
               AND ps.timestamp = latest.max_ts
            ORDER BY ps.timestamp DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Consistency Log CRUD ────────────────────────────────

    # PURPOSE: 不整合検知を記録する
    def log_consistency_issue(
        self,
        session_id: str = "",
        issue: str = "",
        severity: str = "medium",
        details: str = "",
    ) -> ConsistencyIssue:
        """Log a consistency issue."""
        ci = ConsistencyIssue(
            session_id=session_id,
            issue=issue,
            severity=severity,
            details=details,
        )
        self._conn.execute(
            "INSERT INTO consistency_log "
            "(timestamp, session_id, issue, severity, details) "
            "VALUES (?, ?, ?, ?, ?)",
            (ci.timestamp, ci.session_id, ci.issue, ci.severity, ci.details),
        )
        self._conn.commit()
        logger.info("Consistency issue logged: [%s] %s", severity, issue[:80])
        return ci

    # PURPOSE: 直近の不整合ログを取得する
    def get_recent_issues(self, limit: int = 10) -> list[dict]:
        """Get recent consistency issues."""
        rows = self._conn.execute(
            "SELECT * FROM consistency_log ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Statistics ──────────────────────────────────────────

    # PURPOSE: ストア全体の統計を返す
    def get_stats(self) -> dict:
        """Get store statistics."""
        session_count = self._conn.execute(
            "SELECT COUNT(*) FROM sessions"
        ).fetchone()[0]
        active_sessions = self._conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE status = 'active'"
        ).fetchone()[0]
        snapshot_count = self._conn.execute(
            "SELECT COUNT(*) FROM project_snapshots"
        ).fetchone()[0]
        issue_count = self._conn.execute(
            "SELECT COUNT(*) FROM consistency_log"
        ).fetchone()[0]
        return {
            "sessions_total": session_count,
            "sessions_active": active_sessions,
            "snapshots_total": snapshot_count,
            "issues_total": issue_count,
            "db_path": str(self._db_path),
        }

    # ── S2: IDE Session CRUD ─────────────────────────────────

    # PURPOSE: IDE セッションを挿入または更新する
    def upsert_ide_session(
        self,
        session_id: str,
        title: str = "",
        created_at: Optional[float] = None,
        updated_at: Optional[float] = None,
        dir_path: str = "",
        artifact_count: int = 0,
    ) -> None:
        """Upsert an IDE session record."""
        now = time.time()
        self._conn.execute(
            """INSERT INTO ide_sessions (id, title, created_at, updated_at, dir_path, artifact_count)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 title = COALESCE(NULLIF(excluded.title, ''), ide_sessions.title),
                 updated_at = COALESCE(excluded.updated_at, ide_sessions.updated_at),
                 dir_path = CASE WHEN excluded.dir_path != '' THEN excluded.dir_path ELSE ide_sessions.dir_path END,
                 artifact_count = CASE WHEN excluded.artifact_count > 0 THEN excluded.artifact_count ELSE ide_sessions.artifact_count END
            """,
            (session_id, title, created_at or now, updated_at or now, dir_path, artifact_count),
        )
        self._conn.commit()

    # PURPOSE: IDE セッション一覧を取得する
    def get_ide_sessions(self, limit: int = 50) -> list[dict]:
        """Get IDE sessions ordered by created_at DESC."""
        rows = self._conn.execute(
            "SELECT * FROM ide_sessions ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    # PURPOSE: セッション + アーティファクトをまとめて取得する
    def get_session_with_artifacts(self, session_id: str) -> Optional[dict]:
        """Get a session with its artifacts."""
        row = self._conn.execute(
            "SELECT * FROM ide_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        result = dict(row)
        art_rows = self._conn.execute(
            "SELECT * FROM artifacts WHERE session_id = ? ORDER BY filename",
            (session_id,),
        ).fetchall()
        result["artifacts"] = [dict(a) for a in art_rows]
        return result

    # ── S2: Artifact CRUD ──────────────────────────────────

    # PURPOSE: アーティファクトを挿入または更新する
    def upsert_artifact(
        self,
        session_id: str,
        filename: str,
        artifact_type: str = "other",
        summary: str = "",
        size_bytes: int = 0,
        created_at: Optional[float] = None,
        updated_at: Optional[float] = None,
        version: str = "",
        is_standard: bool = False,
    ) -> None:
        """Upsert an artifact record."""
        now = time.time()
        self._conn.execute(
            """INSERT INTO artifacts (session_id, filename, artifact_type, summary, size_bytes, created_at, updated_at, version, is_standard)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(session_id, filename) DO UPDATE SET
                 artifact_type = excluded.artifact_type,
                 summary = COALESCE(NULLIF(excluded.summary, ''), artifacts.summary),
                 size_bytes = excluded.size_bytes,
                 updated_at = excluded.updated_at,
                 version = COALESCE(NULLIF(excluded.version, ''), artifacts.version),
                 is_standard = excluded.is_standard
            """,
            (session_id, filename, artifact_type, summary, size_bytes, created_at or now, updated_at or now, version, int(is_standard)),
        )
        self._conn.commit()

    # PURPOSE: 永続化漏れの大型カスタムアーティファクトを検出する
    def get_orphan_artifacts(self, min_size_bytes: int = 1000) -> list[dict]:
        """Get custom artifacts that are large but not standard (potential orphans)."""
        rows = self._conn.execute(
            """SELECT a.*, s.title as session_title
               FROM artifacts a
               LEFT JOIN ide_sessions s ON a.session_id = s.id
               WHERE a.is_standard = 0 AND a.size_bytes >= ?
               ORDER BY a.size_bytes DESC
            """,
            (min_size_bytes,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── S2: Handoff CRUD ───────────────────────────────────

    # PURPOSE: Handoff を挿入または更新する
    def upsert_handoff(
        self,
        filename: str,
        filepath: str = "",
        created_at: Optional[float] = None,
        size_bytes: int = 0,
        title: str = "",
        session_id: Optional[str] = None,
        project_name: Optional[str] = None,
        handoff_version: Optional[str] = None,
    ) -> None:
        """Upsert a Handoff record."""
        now = time.time()
        self._conn.execute(
            """INSERT INTO handoffs (filename, filepath, created_at, size_bytes, title, session_id, project_name, handoff_version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(filename) DO UPDATE SET
                 filepath = CASE WHEN excluded.filepath != '' THEN excluded.filepath ELSE handoffs.filepath END,
                 size_bytes = CASE WHEN excluded.size_bytes > 0 THEN excluded.size_bytes ELSE handoffs.size_bytes END,
                 title = COALESCE(NULLIF(excluded.title, ''), handoffs.title),
                 session_id = COALESCE(excluded.session_id, handoffs.session_id),
                 project_name = COALESCE(excluded.project_name, handoffs.project_name),
                 handoff_version = COALESCE(excluded.handoff_version, handoffs.handoff_version)
            """,
            (filename, filepath, created_at or now, size_bytes, title, session_id, project_name, handoff_version),
        )
        self._conn.commit()

    # PURPOSE: Handoff 一覧を取得する
    def get_handoffs(self, limit: int = 50) -> list[dict]:
        """Get handoffs ordered by created_at DESC."""
        rows = self._conn.execute(
            "SELECT * FROM handoffs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    # PURPOSE: ファイル名で Handoff を取得する
    def get_handoff_by_filename(self, filename: str) -> Optional[dict]:
        """Get a handoff by filename."""
        row = self._conn.execute(
            "SELECT * FROM handoffs WHERE filename = ?",
            (filename,),
        ).fetchone()
        return dict(row) if row else None

    # PURPOSE: Handoff をセッションに紐づける
    def link_handoff_to_session(self, filename: str, session_id: str) -> None:
        """Link a handoff to a session."""
        self._conn.execute(
            "UPDATE handoffs SET session_id = ? WHERE filename = ?",
            (session_id, filename),
        )
        self._conn.commit()

    # ── S2: ROM CRUD ───────────────────────────────────────

    # PURPOSE: ROM を挿入または更新する
    def upsert_rom(
        self,
        filename: str,
        filepath: str = "",
        created_at: Optional[float] = None,
        size_bytes: int = 0,
        topic: str = "",
    ) -> None:
        """Upsert a ROM record."""
        now = time.time()
        self._conn.execute(
            """INSERT INTO roms (filename, filepath, created_at, size_bytes, topic)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(filename) DO UPDATE SET
                 filepath = CASE WHEN excluded.filepath != '' THEN excluded.filepath ELSE roms.filepath END,
                 size_bytes = CASE WHEN excluded.size_bytes > 0 THEN excluded.size_bytes ELSE roms.size_bytes END,
                 topic = COALESCE(NULLIF(excluded.topic, ''), roms.topic)
            """,
            (filename, filepath, created_at or now, size_bytes, topic),
        )
        self._conn.commit()

    # PURPOSE: ROM 一覧を取得する
    def get_roms(self, limit: int = 50) -> list[dict]:
        """Get ROMs ordered by created_at DESC."""
        rows = self._conn.execute(
            "SELECT * FROM roms ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    # PURPOSE: ROM をセッションに紐づける
    def link_rom_to_session(self, filename: str, session_id: str) -> None:
        """Link a ROM to a session."""
        self._conn.execute(
            "UPDATE roms SET session_id = ? WHERE filename = ?",
            (session_id, filename),
        )
        self._conn.commit()

    # ── S2: Project CRUD ───────────────────────────────────

    # PURPOSE: プロジェクトを挿入または更新する
    def upsert_project(self, project_id: str, name: str = "") -> None:
        """Upsert a project record."""
        self._conn.execute(
            """INSERT INTO projects (project_id, name) VALUES (?, ?)
               ON CONFLICT(project_id) DO UPDATE SET
                 name = COALESCE(NULLIF(excluded.name, ''), projects.name)
            """,
            (project_id, name),
        )
        self._conn.commit()

    # ── S2: Session summary / cross-ref ────────────────────

    # PURPOSE: セッション + Handoff/ROM カウントの要約を取得する
    def get_session_summary(self, limit: int = 20) -> list[dict]:
        """Get session summary with handoff and ROM counts."""
        rows = self._conn.execute(
            """SELECT s.id, s.title, s.created_at, s.updated_at, s.artifact_count,
                      (SELECT COUNT(*) FROM handoffs h WHERE h.session_id = s.id) as handoff_count,
                      (SELECT COUNT(*) FROM roms r WHERE r.session_id = s.id) as rom_count
               FROM ide_sessions s
               ORDER BY s.created_at DESC
               LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    # PURPOSE: 直近の Handoff + セッション名の要約を取得する
    def get_recent_handoff_summaries(self, limit: int = 10) -> list[dict]:
        """Get recent handoffs with linked session titles."""
        rows = self._conn.execute(
            """SELECT h.filename, h.title, h.created_at, h.size_bytes,
                      h.session_id, h.project_name, h.handoff_version,
                      s.title as session_title
               FROM handoffs h
               LEFT JOIN ide_sessions s ON h.session_id = s.id
               ORDER BY h.created_at DESC
               LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    # PURPOSE: セッション × Handoff × ROM × アーティファクト × PJ のクロスリファレンス
    def get_session_cross_ref(self, limit: int = 20, days: Optional[int] = None) -> list[dict]:
        """Get full cross-reference view: session + handoffs + ROMs + artifacts + projects."""
        where_clause = ""
        params: list = []
        if days is not None:
            cutoff = time.time() - days * 86400
            where_clause = "WHERE s.created_at >= ?"
            params.append(cutoff)
        params.append(limit)

        rows = self._conn.execute(
            f"""SELECT * FROM ide_sessions s
               {where_clause}
               ORDER BY s.created_at DESC
               LIMIT ?
            """,
            params,
        ).fetchall()

        results = []
        for row in rows:
            entry = dict(row)
            sid = entry["id"]
            # Handoff
            hrows = self._conn.execute(
                "SELECT * FROM handoffs WHERE session_id = ? ORDER BY created_at",
                (sid,),
            ).fetchall()
            entry["handoffs"] = [dict(h) for h in hrows]
            # ROM
            rrows = self._conn.execute(
                "SELECT * FROM roms WHERE session_id = ? ORDER BY created_at",
                (sid,),
            ).fetchall()
            entry["roms"] = [dict(r) for r in rrows]
            # Artifact
            arows = self._conn.execute(
                "SELECT * FROM artifacts WHERE session_id = ? ORDER BY filename",
                (sid,),
            ).fetchall()
            entry["artifacts"] = [dict(a) for a in arows]
            # Project (テーブルが未作成の場合あり — ガード)
            try:
                prows = self._conn.execute(
                    """SELECT p.project_id, p.name
                       FROM session_projects sp
                       JOIN projects p ON sp.project_id = p.project_id
                       WHERE sp.session_id = ?
                    """,
                    (sid,),
                ).fetchall()
                entry["projects"] = [dict(p) for p in prows]
            except Exception:  # noqa: BLE001
                entry["projects"] = []
            results.append(entry)
        return results

    # ── S2: Timeline ───────────────────────────────────────

    # PURPOSE: 日別セッション数のタイムラインを返す
    def get_session_timeline(self, days: int = 30) -> list[dict]:
        """Get daily session count timeline."""
        cutoff = time.time() - days * 86400
        rows = self._conn.execute(
            """SELECT date(created_at, 'unixepoch', 'localtime') as day,
                      COUNT(*) as session_count,
                      SUM(artifact_count) as total_artifacts
               FROM ide_sessions
               WHERE created_at >= ?
               GROUP BY day
               ORDER BY day DESC
            """,
            (cutoff,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── S2: find_closest_session ────────────────────────────

    # PURPOSE: タイムスタンプに最も近いセッションを返す
    def find_closest_session(
        self, timestamp: float, max_gap_seconds: float = 1800.0
    ) -> Optional[str]:
        """Find the closest session to a given timestamp."""
        # まず期間内のセッションを探す
        row = self._conn.execute(
            """SELECT id FROM ide_sessions
               WHERE created_at <= ? AND (updated_at >= ? OR updated_at IS NULL)
               ORDER BY created_at DESC LIMIT 1
            """,
            (timestamp, timestamp),
        ).fetchone()
        if row:
            return row["id"]

        # 期間外: 最も近いセッションを探す
        row = self._conn.execute(
            """SELECT id,
                      MIN(ABS(created_at - ?), ABS(COALESCE(updated_at, created_at) - ?)) as gap
               FROM ide_sessions
               WHERE MIN(ABS(created_at - ?), ABS(COALESCE(updated_at, created_at) - ?)) <= ?
               ORDER BY gap ASC LIMIT 1
            """,
            (timestamp, timestamp, timestamp, timestamp, max_gap_seconds),
        ).fetchone()
        return row["id"] if row else None

    # ── S3: Knowledge Graph ────────────────────────────────

    # PURPOSE: 知識ノードを挿入または更新する
    def upsert_knowledge_node(
        self,
        node_id: str,
        source: str,
        source_id: str = "",
        title: str = "",
        content_preview: str = "",
        metadata_json: str = "{}",
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        precision: float = 0.5,
        density: float = 0.0,
    ) -> None:
        """Upsert a knowledge node."""
        now = time.time()
        self._conn.execute(
            """INSERT INTO knowledge_nodes (id, source, source_id, title, content_preview, metadata_json, session_id, project_id, precision, density, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 source = excluded.source,
                 source_id = COALESCE(NULLIF(excluded.source_id, ''), knowledge_nodes.source_id),
                 title = COALESCE(NULLIF(excluded.title, ''), knowledge_nodes.title),
                 content_preview = COALESCE(NULLIF(excluded.content_preview, ''), knowledge_nodes.content_preview),
                 metadata_json = CASE WHEN excluded.metadata_json != '{}' THEN excluded.metadata_json ELSE knowledge_nodes.metadata_json END,
                 session_id = COALESCE(excluded.session_id, knowledge_nodes.session_id),
                 project_id = COALESCE(excluded.project_id, knowledge_nodes.project_id),
                 precision = excluded.precision,
                 density = excluded.density,
                 updated_at = excluded.updated_at
            """,
            (node_id, source, source_id, title, content_preview, metadata_json, session_id, project_id, precision, density, now, now),
        )
        self._conn.commit()
        # FTS 同期 (DELETE + INSERT)
        if self._has_fts:
            try:
                self._conn.execute(
                    "DELETE FROM knowledge_nodes_fts WHERE id = ?",
                    (node_id,),
                )
                self._conn.execute(
                    """INSERT INTO knowledge_nodes_fts(id, title, content_preview)
                       SELECT id, title, content_preview FROM knowledge_nodes WHERE id = ?
                    """,
                    (node_id,),
                )
                self._conn.commit()
            except Exception:  # noqa: BLE001
                pass  # FTS 同期失敗は致命的ではない

    # PURPOSE: 知識ノードを検索する (FTS5 優先、フォールバック LIKE)
    def search_knowledge(
        self, query: str, source_filter: Optional[str] = None, limit: int = 20
    ) -> list[dict]:
        """Search knowledge nodes. Uses FTS5 if available, otherwise LIKE."""
        if self._has_fts:
            try:
                if source_filter:
                    rows = self._conn.execute(
                        """SELECT kn.* FROM knowledge_nodes kn
                           JOIN knowledge_nodes_fts fts ON kn.id = fts.id
                           WHERE knowledge_nodes_fts MATCH ? AND kn.source = ?
                           ORDER BY rank LIMIT ?
                        """,
                        (query, source_filter, limit),
                    ).fetchall()
                else:
                    rows = self._conn.execute(
                        """SELECT kn.* FROM knowledge_nodes kn
                           JOIN knowledge_nodes_fts fts ON kn.id = fts.id
                           WHERE knowledge_nodes_fts MATCH ?
                           ORDER BY rank LIMIT ?
                        """,
                        (query, limit),
                    ).fetchall()
                if rows:  # FTS が結果を返した場合のみ使用 (日本語等で空になる場合は LIKE へ)
                    return [dict(r) for r in rows]
            except Exception:  # noqa: BLE001
                pass  # フォールバック

        # LIKE フォールバック
        like_q = f"%{query}%"
        if source_filter:
            rows = self._conn.execute(
                """SELECT * FROM knowledge_nodes
                   WHERE (title LIKE ? OR content_preview LIKE ?) AND source = ?
                   ORDER BY updated_at DESC LIMIT ?
                """,
                (like_q, like_q, source_filter, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """SELECT * FROM knowledge_nodes
                   WHERE title LIKE ? OR content_preview LIKE ?
                   ORDER BY updated_at DESC LIMIT ?
                """,
                (like_q, like_q, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    # PURPOSE: 知識エッジを追加する
    def add_knowledge_edge(
        self,
        from_id: str,
        to_id: str,
        relation_type: str,
        weight: float = 1.0,
        evidence: str = "",
    ) -> None:
        """Add a knowledge edge (INSERT OR IGNORE for dedup)."""
        self._conn.execute(
            """INSERT OR IGNORE INTO knowledge_edges (from_id, to_id, relation_type, weight, evidence)
               VALUES (?, ?, ?, ?, ?)
            """,
            (from_id, to_id, relation_type, weight, evidence),
        )
        self._conn.commit()

    # PURPOSE: ノードの近傍を探索する (N ホップ)
    def get_node_neighbors(
        self,
        node_id: str,
        depth: int = 1,
        relation_types: Optional[list[str]] = None,
    ) -> list[dict]:
        """Get neighbors of a node up to N hops."""
        visited: set[str] = {node_id}
        result: list[dict] = []
        current_nodes = [node_id]

        for _ in range(depth):
            next_nodes: list[str] = []
            for nid in current_nodes:
                # 正方向
                rel_filter = ""
                params: list = [nid]
                if relation_types:
                    placeholders = ",".join("?" for _ in relation_types)
                    rel_filter = f" AND relation_type IN ({placeholders})"
                    params.extend(relation_types)

                rows = self._conn.execute(
                    f"""SELECT to_id as node_id, relation_type, weight, 'outgoing' as direction
                       FROM knowledge_edges
                       WHERE from_id = ?{rel_filter}
                    """,
                    params,
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    if d["node_id"] not in visited:
                        visited.add(d["node_id"])
                        result.append(d)
                        next_nodes.append(d["node_id"])

                # 逆方向
                params2: list = [nid]
                if relation_types:
                    params2.extend(relation_types)
                rows2 = self._conn.execute(
                    f"""SELECT from_id as node_id, relation_type, weight, 'incoming' as direction
                       FROM knowledge_edges
                       WHERE to_id = ?{rel_filter}
                    """,
                    params2,
                ).fetchall()
                for r in rows2:
                    d = dict(r)
                    if d["node_id"] not in visited:
                        visited.add(d["node_id"])
                        result.append(d)
                        next_nodes.append(d["node_id"])

            current_nodes = next_nodes
        return result

    # PURPOSE: 知識グラフの統計を返す
    def get_knowledge_stats(self) -> dict:
        """Get knowledge graph statistics."""
        total_nodes = self._conn.execute(
            "SELECT COUNT(*) FROM knowledge_nodes"
        ).fetchone()[0]
        total_edges = self._conn.execute(
            "SELECT COUNT(*) FROM knowledge_edges"
        ).fetchone()[0]

        # ソース別ノード数
        src_rows = self._conn.execute(
            "SELECT source, COUNT(*) as cnt FROM knowledge_nodes GROUP BY source"
        ).fetchall()
        nodes_by_source = {r["source"]: r["cnt"] for r in src_rows}

        # 関係タイプ別エッジ数
        rel_rows = self._conn.execute(
            "SELECT relation_type, COUNT(*) as cnt FROM knowledge_edges GROUP BY relation_type"
        ).fetchall()
        edges_by_relation = {r["relation_type"]: r["cnt"] for r in rel_rows}

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "nodes_by_source": nodes_by_source,
            "edges_by_relation": edges_by_relation,
        }

    # ── V-012: Health Check ─────────────────────────────────────

    # PURPOSE: ヘルスチェック結果をバッチ記録する
    def log_health_batch(self, results: list[dict]) -> None:
        """V-012: ヘルスチェック結果をバッチ記録する。"""
        now = time.time()
        for r in results:
            self._conn.execute(
                "INSERT INTO health_checks "
                "(timestamp, server_name, port, status, latency_ms, error) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    now,
                    r.get("server_name", ""),
                    r.get("port", 0),
                    r.get("status", "unknown"),
                    r.get("latency_ms", 0),
                    r.get("error", ""),
                ),
            )
        self._conn.commit()
        logger.info("Health batch logged: %d results", len(results))

    # PURPOSE: 24時間のヘルスサマリーを返す
    def get_health_summary(self) -> dict:
        """V-012: 24h のヘルスサマリーを返す。"""
        cutoff = time.time() - 86400
        rows = self._conn.execute(
            "SELECT server_name, COUNT(*) as cnt "
            "FROM health_checks WHERE status = 'down' AND timestamp >= ? "
            "GROUP BY server_name",
            (cutoff,),
        ).fetchall()
        return {"failures_24h": {r["server_name"]: r["cnt"] for r in rows}}

    # ── S2: Handoff Chain ──────────────────────────────────────

    # PURPOSE: Handoff η/ε 連鎖を記録する
    def record_chain(
        self,
        handoff_id: str,
        source_session_id: str,
        target_session_id: Optional[str] = None,
    ) -> None:
        """Record a handoff chain (η/ε chain)."""
        if target_session_id is None:
            return  # target がない場合は記録しない
        self._conn.execute(
            """INSERT OR IGNORE INTO handoff_chains (handoff_id, source_session_id, target_session_id)
               VALUES (?, ?, ?)
            """,
            (handoff_id, source_session_id, target_session_id),
        )
        self._conn.commit()

    # ── S3: ker(G) 保管 ──────────────────────────────────────

    # PURPOSE: Nucleator チャンキングで捨てられる情報 (ker(G)) をエッジとして保管する
    def save_chunk_kernel(
        self,
        chunks: list[dict],
        source_sessions: Optional[list[dict]] = None,
    ) -> int:
        """Nucleator ker(G) をknowledge_edges に保存する。

        保存するエッジ:
        1. adjacency — 隣接 chunk 間 (Temporality 保全)
        2. same_session — 同一セッション由来の chunk 間 (Scale 保全)

        Args:
            chunks: chunk_cross_ref() の戻り値 (list[dict])。
                各 dict に source_id, section_title, text, coherence 等。
            source_sessions: 元セッション情報 (list[dict])。
                各 dict に id, title, created_at 等。

        Returns:
            追加されたエッジ数。
        """
        import json as _json

        if len(chunks) < 2:
            return 0

        edge_count = 0

        # 1. 隣接エッジ (adjacency) — Temporality 保全
        for i in range(len(chunks) - 1):
            c_cur = chunks[i]
            c_nxt = chunks[i + 1]
            from_id = f"chunk:{c_cur.get('source_id', '?')}:{c_cur.get('chunk_index', i)}"
            to_id = f"chunk:{c_nxt.get('source_id', '?')}:{c_nxt.get('chunk_index', i + 1)}"

            # weight = 隣接 chunk の coherence の平均
            coh_cur = c_cur.get("coherence", 0.5)
            coh_nxt = c_nxt.get("coherence", 0.5)
            weight = (coh_cur + coh_nxt) / 2.0

            evidence = _json.dumps({
                "from_title": c_cur.get("section_title", ""),
                "to_title": c_nxt.get("section_title", ""),
                "drift": c_cur.get("drift", 0.0),
            }, ensure_ascii=False)

            self.add_knowledge_edge(
                from_id=from_id,
                to_id=to_id,
                relation_type="adjacency",
                weight=weight,
                evidence=evidence,
            )
            edge_count += 1

        # 2. 同一セッション由来エッジ (same_session) — Scale 保全
        if source_sessions:
            # セッション ID → chunk index のマッピングを構築
            session_chunks: dict[str, list[str]] = {}
            for i, c in enumerate(chunks):
                title = c.get("section_title", "")
                # cross_ref_to_text が "## Session: {title}" を生成するので
                # section_title からセッションを逆引き
                for sess in source_sessions:
                    sess_title = sess.get("title", sess.get("id", ""))
                    if sess_title and sess_title in title:
                        sid = sess.get("id", sess_title)
                        chunk_id = f"chunk:{c.get('source_id', '?')}:{c.get('chunk_index', i)}"
                        session_chunks.setdefault(sid, []).append(chunk_id)
                        break

            # 同一セッション由来の chunk ペアにエッジ追加
            for sid, cids in session_chunks.items():
                if len(cids) < 2:
                    continue
                for j in range(len(cids)):
                    for k in range(j + 1, len(cids)):
                        sess_info = next(
                            (s for s in source_sessions if s.get("id") == sid),
                            {},
                        )
                        evidence = _json.dumps({
                            "session_id": sid,
                            "session_title": sess_info.get("title", ""),
                            "created_at": sess_info.get("created_at", 0),
                        }, ensure_ascii=False)

                        self.add_knowledge_edge(
                            from_id=cids[j],
                            to_id=cids[k],
                            relation_type="same_session",
                            weight=0.8,
                            evidence=evidence,
                        )
                        edge_count += 1

        return edge_count

    # ── F2: Field Axes CRUD ─────────────────────────────────

    # PURPOSE: Fisher 固有分解結果を保存する
    def save_field_axes(
        self,
        axes: "FieldAxes",
        source_filter: str = "",
        use_centroids: bool = False,
        k_neighbors: int = 10,
    ) -> int:
        """Save FieldAxes to database. Returns the axes ID."""
        import json as _json
        import numpy as np
        from mekhane.symploke.blob_utils import encode_ndarray_blob
        eigenvalues_json = _json.dumps(axes.eigenvalues.tolist())
        # E2 修正: shape ヘッダ付き BLOB (blob_utils に抽出済み)
        eigenvectors_blob = encode_ndarray_blob(axes.eigenvectors)
        # E1 修正: FieldAxes.computed_at (ISO8601 str) をそのまま保存
        computed_at = axes.computed_at or datetime.now(timezone.utc).isoformat()

        cursor = self._conn.execute(
            """INSERT INTO field_axes
               (computed_at, k, gap_index, sloppy_ratio, total_points,
                eigenvalues_json, eigenvectors_blob, source_filter,
                use_centroids, k_neighbors)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                computed_at, axes.k, axes.gap_index, axes.sloppy_ratio,
                axes.total_points, eigenvalues_json, eigenvectors_blob,
                source_filter, int(use_centroids), k_neighbors,
            ),
        )
        self._conn.commit()
        axes_id = cursor.lastrowid
        if axes_id is None:
            raise RuntimeError("Failed to insert field axes (lastrowid is None)")
        logger.info("Field axes saved: id=%d, k=%d, sloppy=%.2f", axes_id, axes.k, axes.sloppy_ratio)
        return axes_id
    # PURPOSE: 最新の固有軸を取得する
    def get_latest_field_axes(self) -> Optional[dict]:
        """Get the most recent field axes record."""
        row = self._conn.execute(
            "SELECT * FROM field_axes ORDER BY computed_at DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None

    # PURPOSE: 固有軸を FieldAxes オブジェクトとして復元する
    def load_field_axes(self, axes_id: Optional[int] = None) -> Optional["FieldAxes"]:
        """Load FieldAxes from database.

        Args:
            axes_id: 固有軸 ID (None → 最新)

        Returns:
            FieldAxes または None
        """
        import json as _json
        import numpy as np
        from mekhane.anamnesis.fisher_field import FieldAxes

        if axes_id is not None:
            row = self._conn.execute(
                "SELECT * FROM field_axes WHERE id = ?", (axes_id,)
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT * FROM field_axes ORDER BY computed_at DESC LIMIT 1"
            ).fetchone()

        if not row:
            return None

        row = dict(row)
        eigenvalues = np.array(_json.loads(row["eigenvalues_json"]), dtype=np.float64)
        k = row["k"]

        # E2 修正: shape ヘッダ付き BLOB (blob_utils に抽出済み)
        from mekhane.symploke.blob_utils import decode_ndarray_blob
        blob = row["eigenvectors_blob"]
        eigenvectors, is_new_fmt = decode_ndarray_blob(blob, ndim=2, fallback_cols=k)
        if not is_new_fmt and blob:
            logger.info("旧形式 BLOB を読み込みました (axes_id=%s)", row.get("id"))

        return FieldAxes(
            eigenvectors=eigenvectors,
            eigenvalues=eigenvalues,
            k=k,
            gap_index=row.get("gap_index", 0),
            sloppy_ratio=row.get("sloppy_ratio", 0.0),
            computed_at=str(row.get("computed_at", "")),
            total_points=row.get("total_points", 0),
        )

    # ── F2: Session Classification CRUD ────────────────────

    # E3 修正: UPSERT SQL をクラス定数に抽出 (save_classification / save_classifications_batch 共通)
    _UPSERT_CLASSIFICATION_SQL = """INSERT INTO session_classifications
        (session_id, axes_id, cluster_id, cluster_label,
         coords_json, tags_json, confidence, classified_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id, axes_id) DO UPDATE SET
          cluster_id = excluded.cluster_id,
          cluster_label = excluded.cluster_label,
          coords_json = excluded.coords_json,
          tags_json = excluded.tags_json,
          confidence = excluded.confidence,
          classified_at = excluded.classified_at
    """

    # PURPOSE: セッション分類結果を保存する
    def save_classification(
        self,
        result: "ClassificationResult",
        axes_id: int,
    ) -> None:
        """Save a single classification result."""
        import json as _json
        now = time.time()
        coords_json = _json.dumps(result.coords.tolist())
        tags_json = _json.dumps(result.tags, ensure_ascii=False)

        self._conn.execute(
            self._UPSERT_CLASSIFICATION_SQL,
            (
                result.session_id, axes_id, result.cluster_id,
                result.cluster_label, coords_json, tags_json,
                result.confidence, now,
            ),
        )
        self._conn.commit()

    # PURPOSE: 全分類結果を一括保存する
    def save_classifications_batch(
        self,
        results: list["ClassificationResult"],
        axes_id: int,
    ) -> int:
        """Save multiple classification results. Returns count saved."""
        import json as _json
        now = time.time()
        rows = []
        for r in results:
            rows.append((
                r.session_id, axes_id, r.cluster_id, r.cluster_label,
                _json.dumps(r.coords.tolist()),
                _json.dumps(r.tags, ensure_ascii=False),
                r.confidence, now,
            ))

        self._conn.executemany(
            self._UPSERT_CLASSIFICATION_SQL,
            rows,
        )
        self._conn.commit()
        logger.info("Saved %d classifications for axes_id=%d", len(rows), axes_id)
        return len(rows)

    # PURPOSE: セッションの分類結果を取得する
    def get_session_classification(
        self,
        session_id: str,
        axes_id: Optional[int] = None,
    ) -> Optional[dict]:
        """Get classification for a session.

        Args:
            session_id: セッション ID
            axes_id: 固有軸 ID (None → 最新の axes)
        """
        if axes_id is not None:
            row = self._conn.execute(
                "SELECT * FROM session_classifications WHERE session_id = ? AND axes_id = ?",
                (session_id, axes_id),
            ).fetchone()
        else:
            row = self._conn.execute(
                """SELECT sc.* FROM session_classifications sc
                   INNER JOIN (
                       SELECT MAX(axes_id) as max_aid FROM session_classifications
                       WHERE session_id = ?
                   ) latest ON sc.axes_id = latest.max_aid
                   WHERE sc.session_id = ?
                """,
                (session_id, session_id),
            ).fetchone()
        return dict(row) if row else None

    # PURPOSE: 最新の axes_id を取得するヘルパー (E6 修正: 重複排除)
    def _get_latest_axes_id(self) -> Optional[int]:
        """Get the latest axes_id from field_axes table."""
        row = self._conn.execute(
            "SELECT MAX(id) as max_id FROM field_axes"
        ).fetchone()
        if not row or row["max_id"] is None:
            return None
        return row["max_id"]

    # PURPOSE: 全セッションの分類結果を取得する
    def get_all_classifications(
        self,
        axes_id: Optional[int] = None,
        cluster_label: Optional[str] = None,
    ) -> list[dict]:
        """Get all classifications, optionally filtered."""
        if axes_id is None:
            axes_id = self._get_latest_axes_id()
            if axes_id is None:
                return []

        if cluster_label:
            rows = self._conn.execute(
                """SELECT * FROM session_classifications
                   WHERE axes_id = ? AND cluster_label = ?
                   ORDER BY confidence DESC
                """,
                (axes_id, cluster_label),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """SELECT * FROM session_classifications
                   WHERE axes_id = ?
                   ORDER BY confidence DESC
                """,
                (axes_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    # PURPOSE: クラスタラベル別の集計を取得する
    def get_classification_summary(self, axes_id: Optional[int] = None) -> list[dict]:
        """Get classification summary grouped by cluster_label."""
        if axes_id is None:
            axes_id = self._get_latest_axes_id()
            if axes_id is None:
                return []

        rows = self._conn.execute(
            """SELECT cluster_label, COUNT(*) as count,
                      AVG(confidence) as avg_confidence
               FROM session_classifications
               WHERE axes_id = ?
               GROUP BY cluster_label
               ORDER BY count DESC
            """,
            (axes_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Always-On Boot キャッシュ ──────────────────────────────

    # PURPOSE: 全軸のキャッシュを一括読み出しする (Boot プル時のメイン API)
    def get_cached_boot_context(self, mode: str = "standard") -> Optional[dict]:
        """全軸のキャッシュから boot context を組み立てる。

        Returns:
            dict | None: キャッシュヒット時は boot context dict。キャッシュが空なら None。
            "all_stale" キーが True なら全軸が失効済み。
        """
        import time as _time

        now = _time.time()
        rows = self._conn.execute(
            "SELECT axis_key, data_json, formatted, updated_at, stale_after "
            "FROM boot_context_cache WHERE mode = ? ORDER BY axis_key",
            (mode,),
        ).fetchall()

        if not rows:
            return None

        result = {}
        all_formatted_parts: list[str] = []
        stale_count = 0
        total_count = len(rows)

        for row in rows:
            axis_key = row["axis_key"]
            data = json.loads(row["data_json"])
            formatted = row["formatted"]
            is_stale = now > row["stale_after"]

            if is_stale:
                stale_count += 1

            result[axis_key] = data
            if formatted:
                all_formatted_parts.append(formatted)

        result["formatted"] = "\n\n".join(all_formatted_parts)
        result["all_stale"] = stale_count == total_count
        result["_cache_meta"] = {
            "total": total_count,
            "stale": stale_count,
            "fresh": total_count - stale_count,
        }
        return result

    # PURPOSE: 個別軸のキャッシュを更新する (watcher / refresh から呼ばれる)
    def update_boot_cache(
        self,
        axis_key: str,
        mode: str,
        data: dict,
        formatted: str,
        ttl_sec: float = 300.0,
    ) -> None:
        """指定軸のキャッシュを更新 (upsert)。"""
        import time as _time

        now = _time.time()
        self._conn.execute(
            """INSERT INTO boot_context_cache
               (axis_key, mode, data_json, formatted, updated_at, stale_after)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(axis_key, mode) DO UPDATE SET
                 data_json = excluded.data_json,
                 formatted = excluded.formatted,
                 updated_at = excluded.updated_at,
                 stale_after = excluded.stale_after
            """,
            (axis_key, mode, json.dumps(data, ensure_ascii=False, default=str),
             formatted, now, now + ttl_sec),
        )
        self._conn.commit()

    # PURPOSE: 指定軸のキャッシュを無効化する
    def invalidate_boot_cache(
        self,
        axis_keys: "str | list[str] | None" = None,
    ) -> int:
        """指定軸のキャッシュを無効化 (stale_after を過去に設定)。

        Args:
            axis_keys: 無効化する軸。str / list[str] / None (全軸)。
                       str が渡された場合は自動的に [str] にラップする。

        Returns:
            無効化した行数。
        """
        # 矛盾 #2 修正: str が渡された場合の防御
        if isinstance(axis_keys, str):
            axis_keys = [axis_keys]

        if axis_keys:
            placeholders = ",".join("?" for _ in axis_keys)
            cursor = self._conn.execute(
                f"UPDATE boot_context_cache SET stale_after = 0 "
                f"WHERE axis_key IN ({placeholders})",
                axis_keys,
            )
        else:
            cursor = self._conn.execute(
                "UPDATE boot_context_cache SET stale_after = 0"
            )
        self._conn.commit()
        return cursor.rowcount

    # PURPOSE: キャッシュの鮮度情報を返す (デバッグ・ステータス用)
    def get_boot_cache_status(self) -> dict:
        """全モード×全軸のキャッシュステータスを返す。"""
        import time as _time

        now = _time.time()
        rows = self._conn.execute(
            "SELECT axis_key, mode, updated_at, stale_after "
            "FROM boot_context_cache ORDER BY mode, axis_key"
        ).fetchall()

        axes = []
        for row in rows:
            is_fresh = now <= row["stale_after"]
            age_sec = now - row["updated_at"]
            axes.append({
                "axis": row["axis_key"],
                "mode": row["mode"],
                "fresh": is_fresh,
                "age_sec": round(age_sec, 1),
                "ttl_remaining": round(max(0, row["stale_after"] - now), 1),
            })

        fresh_count = sum(1 for a in axes if a["fresh"])
        return {
            "total_axes": len(axes),
            "fresh": fresh_count,
            "stale": len(axes) - fresh_count,
            "axes": axes,
        }

    # ── Phantasia Field 統合 (GAP-2) ─────────────────────────

    # PURPOSE: 溶解イベントを記録する
    def record_dissolve(
        self,
        session_id: str,
        chunk_count: int,
        total_chars: int = 0,
        source_type: str = "session",
    ) -> None:
        """PhantasiaField への溶解イベントを記録する。

        Args:
            session_id: セッション ID
            chunk_count: 溶解したチャンク数
            total_chars: 溶解したテキストの総文字数
            source_type: データソース種別 (session, rom, handoff)
        """
        from datetime import datetime
        now = datetime.now().isoformat()
        try:
            self._conn.execute(
                "INSERT OR REPLACE INTO phantasia_dissolves "
                "(session_id, source_type, chunk_count, total_chars, dissolved_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (session_id, source_type, chunk_count, total_chars, now),
            )
            self._conn.commit()
            logger.info(
                "Dissolve recorded: session=%s chunks=%d chars=%d",
                session_id, chunk_count, total_chars,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to record dissolve: %s", e)

    # PURPOSE: 場の統計スナップショットを記録する
    def record_field_stats(
        self,
        total_chunks: int = 0,
        total_tables: int = 0,
        avg_density: float = 0.0,
    ) -> None:
        """PhantasiaField の統計スナップショットを記録する。

        Args:
            total_chunks: 場内の全チャンク数
            total_tables: テーブル数
            avg_density: 平均密度
        """
        from datetime import datetime
        now = datetime.now().isoformat()
        try:
            self._conn.execute(
                "INSERT INTO phantasia_field_stats "
                "(total_chunks, total_tables, avg_density, recorded_at) "
                "VALUES (?, ?, ?, ?)",
                (total_chunks, total_tables, avg_density, now),
            )
            self._conn.commit()
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to record field stats: %s", e)

    # PURPOSE: 溶解履歴を取得する
    def get_dissolve_history(
        self,
        session_id: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """溶解イベントの履歴を取得する。

        Args:
            session_id: 特定セッションに絞る場合に指定
            limit: 最大件数

        Returns:
            溶解イベントのリスト (新しい順)
        """
        if session_id:
            rows = self._conn.execute(
                "SELECT * FROM phantasia_dissolves "
                "WHERE session_id = ? ORDER BY dissolved_at DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM phantasia_dissolves "
                "ORDER BY dissolved_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    # PURPOSE: 場の統計推移を取得する
    def get_field_stats(self, limit: int = 10) -> list[dict]:
        """場の統計スナップショットの推移を取得する。

        Args:
            limit: 最大件数

        Returns:
            統計スナップショットのリスト (新しい順)
        """
        rows = self._conn.execute(
            "SELECT * FROM phantasia_field_stats "
            "ORDER BY recorded_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Boot Axis Timing CRUD (自己観測フィードバック) ──────

    # PURPOSE: boot 実行のタイミングデータを一括記録する (フィードバックループの書込側)
    def record_boot_timings(
        self,
        boot_id: str,
        timings: dict[str, float],
        statuses: dict[str, str] | None = None,
        mode: str = "standard",
    ) -> int:
        """Record timing data for a single boot execution.

        Args:
            boot_id: この boot 実行の一意 ID
            timings: {axis_name: elapsed_sec} の辞書
            statuses: {axis_name: 'ok'|'timeout'|'error'|'skipped'} (省略時は全 'ok')
            mode: boot モード ('fast', 'standard', 'detailed')

        Returns:
            記録した行数
        """
        now = time.time()
        statuses = statuses or {}
        rows = []
        for axis_name, elapsed in timings.items():
            status = statuses.get(axis_name, "ok")
            rows.append((boot_id, axis_name, elapsed, status, mode, now))

        self._conn.executemany(
            "INSERT INTO boot_axis_timings "
            "(boot_id, axis_name, elapsed_sec, status, mode, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )
        self._conn.commit()
        logger.info("Boot timings recorded: boot_id=%s, %d axes", boot_id, len(rows))
        return len(rows)

    # PURPOSE: 特定軸のタイミング履歴を取得する (フィードバックループの読出側)
    def get_axis_timing_profile(
        self,
        axis_name: str,
        last_n: int = 10,
        status_filter: str = "ok",
    ) -> list[float]:
        """Get recent timing data for a specific axis.

        Returns:
            直近 last_n 回の elapsed_sec のリスト (新しい順)
        """
        rows = self._conn.execute(
            "SELECT elapsed_sec FROM boot_axis_timings "
            "WHERE axis_name = ? AND status = ? "
            "ORDER BY recorded_at DESC LIMIT ?",
            (axis_name, status_filter, last_n),
        ).fetchall()
        return [r[0] for r in rows]

    # PURPOSE: 全軸のタイミングプロファイルを一括取得する (適応的分類の入力)
    def get_all_axis_profiles(
        self,
        last_n: int = 10,
    ) -> dict[str, dict]:
        """Get timing profiles for all known axes.

        Returns:
            {axis_name: {'median': float, 'p95': float, 'stddev': float,
             'cv': float, 'count': int, 'last': float}} の辞書
            count < 2 の軸は含まない (prior にフォールバックすべき)

        G∘F 2周目: p95 を追加。_derive_timeouts が適応的タイムアウト導出に使用。
        G∘F 3周目: stddev/cv を追加。_derive_observation_windows が観測窓適応化に使用。
        """
        rows = self._conn.execute(
            """
            SELECT axis_name, elapsed_sec, recorded_at
            FROM boot_axis_timings
            WHERE status = 'ok'
            ORDER BY axis_name, recorded_at DESC
            """
        ).fetchall()

        # 軸ごとに直近 last_n 件を集計
        from collections import defaultdict
        axis_data: dict[str, list[float]] = defaultdict(list)
        for axis_name, elapsed, _ in rows:
            if len(axis_data[axis_name]) < last_n:
                axis_data[axis_name].append(elapsed)

        profiles: dict[str, dict] = {}
        for axis_name, timings_list in axis_data.items():
            if len(timings_list) < 2:
                continue  # 証拠不十分 — prior にフォールバック
            sorted_t = sorted(timings_list)
            n = len(sorted_t)
            median = sorted_t[n // 2]
            # p95: 95パーセンタイル (最近似インデックス)
            p95_idx = min(int(n * 0.95), n - 1)
            p95 = sorted_t[p95_idx]
            mean = sum(sorted_t) / n
            variance = sum((x - mean) ** 2 for x in sorted_t) / n
            stddev = variance ** 0.5
            cv = stddev / mean if mean > 0 else 0.0
            profiles[axis_name] = {
                "median": median,
                "p95": p95,
                "stddev": stddev,
                "cv": cv,
                "count": n,
                "last": timings_list[0],  # 最新
            }
        return profiles

    # PURPOSE: DB 接続を閉じる
    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()


# ── Singleton ───────────────────────────────────────────────

_store: Optional[PhantazeinStore] = None


# PURPOSE: グローバルシングルトンの PhantazeinStore を取得する
def get_store(db_path: Optional[Path] = None) -> PhantazeinStore:
    """Get or create the global PhantazeinStore singleton."""
    global _store
    if _store is None:
        _store = PhantazeinStore(db_path=db_path)
    return _store
