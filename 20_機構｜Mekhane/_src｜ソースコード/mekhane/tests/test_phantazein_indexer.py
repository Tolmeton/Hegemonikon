#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/tests/test_phantazein_indexer.py
# PURPOSE: PhantazeinIndexer のスキャン・同期ロジックをテストする
"""
Tests for Phantazein Indexer.
"""

import json
import time
from pathlib import Path

import pytest

from mekhane.symploke.phantazein_store import PhantazeinStore


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "test_indexer.db"


@pytest.fixture
def store(temp_db: Path) -> PhantazeinStore:
    s = PhantazeinStore(db_path=temp_db)
    yield s
    s.close()


# ── IDE Session upsert テスト ──────────────────────────────


# PURPOSE: upsert の冪等性テスト
def test_ide_session_upsert(store: PhantazeinStore) -> None:
    session_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    # 初回挿入
    store.upsert_ide_session(
        session_id=session_id,
        title="Test Session",
        created_at=1000.0,
        updated_at=1000.0,
        dir_path="/tmp/test",
        artifact_count=3,
    )

    sessions = store.get_ide_sessions(limit=10)
    assert len(sessions) == 1
    assert sessions[0]["id"] == session_id
    assert sessions[0]["title"] == "Test Session"
    assert sessions[0]["artifact_count"] == 3

    # 同じ ID で更新 (upsert)
    store.upsert_ide_session(
        session_id=session_id,
        title="Updated Title",
        created_at=1000.0,
        updated_at=2000.0,
        artifact_count=5,
    )

    sessions = store.get_ide_sessions(limit=10)
    assert len(sessions) == 1  # 行数は変わらない (冪等)
    assert sessions[0]["title"] == "Updated Title"
    assert sessions[0]["artifact_count"] == 5

    # 空タイトルで upsert → 既存タイトルが保持される
    store.upsert_ide_session(
        session_id=session_id,
        title="",
        updated_at=3000.0,
    )
    sessions = store.get_ide_sessions(limit=10)
    assert sessions[0]["title"] == "Updated Title"  # COALESCE で保持


# ── Artifact CRUD テスト ──────────────────────────────────


# PURPOSE: アーティファクトの CRUD テスト
def test_artifact_crud(store: PhantazeinStore) -> None:
    session_id = "11111111-2222-3333-4444-555555555555"
    store.upsert_ide_session(session_id=session_id, created_at=1000.0)

    # アーティファクト追加
    store.upsert_artifact(
        session_id=session_id,
        filename="task.md",
        artifact_type="task",
        summary="Task file",
        size_bytes=500,
        is_standard=True,
    )
    store.upsert_artifact(
        session_id=session_id,
        filename="custom_report.md",
        artifact_type="other",
        summary="Custom report",
        size_bytes=15000,
        is_standard=False,
    )

    # セッション + アーティファクト取得
    result = store.get_session_with_artifacts(session_id)
    assert result is not None
    assert result["id"] == session_id
    assert len(result["artifacts"]) == 2

    # upsert 冪等性
    store.upsert_artifact(
        session_id=session_id,
        filename="task.md",
        artifact_type="task",
        summary="Updated task",
        size_bytes=600,
        is_standard=True,
    )
    result = store.get_session_with_artifacts(session_id)
    assert len(result["artifacts"]) == 2  # 件数変わらず


# ── Orphan 検出テスト ─────────────────────────────────────


# PURPOSE: 永続化漏れ検出のテスト
def test_orphan_detection(store: PhantazeinStore) -> None:
    session_id = "aaaaaaaa-1111-2222-3333-444444444444"
    store.upsert_ide_session(session_id=session_id, title="Orphan Test", created_at=1000.0)

    # 標準アーティファクト (orphan 対象外)
    store.upsert_artifact(
        session_id=session_id, filename="task.md",
        is_standard=True, size_bytes=500,
    )
    # 小さなカスタム (閾値以下)
    store.upsert_artifact(
        session_id=session_id, filename="small.md",
        is_standard=False, size_bytes=100,
    )
    # 大きなカスタム (orphan 候補)
    store.upsert_artifact(
        session_id=session_id, filename="big_report.md",
        is_standard=False, size_bytes=20000,
    )

    orphans = store.get_orphan_artifacts(min_size_bytes=1000)
    assert len(orphans) == 1
    assert orphans[0]["filename"] == "big_report.md"
    assert orphans[0]["session_title"] == "Orphan Test"


# ── Handoff / ROM CRUD テスト ──────────────────────────────


# PURPOSE: Handoff upsert テスト
def test_handoff_upsert(store: PhantazeinStore) -> None:
    store.upsert_handoff(
        filename="handoff_2026-03-12_2030.md",
        filepath="/path/to/handoff.md",
        created_at=1000.0,
        size_bytes=3000,
        title="Session Wrap-up",
    )

    handoffs = store.get_handoffs(limit=10)
    assert len(handoffs) == 1
    assert handoffs[0]["title"] == "Session Wrap-up"

    # 同じファイル名で upsert
    store.upsert_handoff(
        filename="handoff_2026-03-12_2030.md",
        filepath="/path/to/handoff.md",
        size_bytes=4000,
    )
    handoffs = store.get_handoffs(limit=10)
    assert len(handoffs) == 1
    assert handoffs[0]["size_bytes"] == 4000
    assert handoffs[0]["title"] == "Session Wrap-up"  # 保持


# PURPOSE: ROM upsert テスト
def test_rom_upsert(store: PhantazeinStore) -> None:
    store.upsert_rom(
        filename="rom_2026-03-12_kalon_engine.md",
        filepath="/path/to/rom.md",
        created_at=1000.0,
        size_bytes=5000,
        topic="kalon engine",
    )

    roms = store.get_roms(limit=10)
    assert len(roms) == 1
    assert roms[0]["topic"] == "kalon engine"


# ── Timeline テスト ───────────────────────────────────────


# PURPOSE: セッションタイムラインのテスト
def test_session_timeline(store: PhantazeinStore) -> None:
    now = time.time()
    # 直近のセッション
    store.upsert_ide_session(
        session_id="today-1", created_at=now, artifact_count=3,
    )
    store.upsert_ide_session(
        session_id="today-2", created_at=now - 100, artifact_count=2,
    )
    # 古いセッション (8日前)
    store.upsert_ide_session(
        session_id="old-1", created_at=now - 8 * 86400, artifact_count=1,
    )

    timeline = store.get_session_timeline(days=7)
    # 直近7日の行だけ返る
    for row in timeline:
        print(f"  {row['day']} | {row['session_count']} sessions")
    total_sessions = sum(row["session_count"] for row in timeline)
    assert total_sessions == 2  # old-1 は含まれない


# ── Indexer full_sync テスト (ダミーファイルシステム) ───────


# PURPOSE: ダミーのセッションディレクトリで full_scan を検証する
def test_scan_session_with_dummy(store: PhantazeinStore, tmp_path: Path) -> None:
    from mekhane.symploke.phantazein_indexer import _scan_session

    # ダミーセッションディレクトリ作成
    session_id = "12345678-abcd-ef01-ab12-123456789abc"
    session_dir = tmp_path / session_id
    session_dir.mkdir()

    # task.md (標準)
    task_file = session_dir / "task.md"
    task_file.write_text("# Task\n- [x] Done", encoding="utf-8")

    # task.md.metadata.json
    meta = session_dir / "task.md.metadata.json"
    meta.write_text(json.dumps({
        "artifactType": "ARTIFACT_TYPE_TASK",
        "summary": "Task tracking",
    }), encoding="utf-8")

    # カスタムアーティファクト
    custom = session_dir / "analysis_report.md"
    custom.write_text("# Analysis\n" + "x" * 5000, encoding="utf-8")

    # .resolved ファイル (除外対象)
    resolved = session_dir / "task.md.resolved"
    resolved.write_text("resolved content", encoding="utf-8")

    # スキャン実行
    art_count = _scan_session(session_dir, store)
    assert art_count == 2  # task.md + analysis_report.md (.resolved は除外)

    # DB 確認
    result = store.get_session_with_artifacts(session_id)
    assert result is not None
    assert result["artifact_count"] == 2
    assert len(result["artifacts"]) == 2

    # 標準チェック
    task_art = next(a for a in result["artifacts"] if a["filename"] == "task.md")
    assert task_art["is_standard"] == 1
    assert task_art["artifact_type"] == "task"

    custom_art = next(a for a in result["artifacts"] if a["filename"] == "analysis_report.md")
    assert custom_art["is_standard"] == 0
    assert custom_art["artifact_type"] == "other"


# ── S2: タイトル抽出テスト ────────────────────────────────


# PURPOSE: task.md からのタイトル自動抽出をテストする
def test_extract_title(tmp_path: Path) -> None:
    from mekhane.symploke.phantazein_indexer import _extract_title

    # task.md がある場合
    session_dir = tmp_path / "session-with-task"
    session_dir.mkdir()
    (session_dir / "task.md").write_text("# マザーブレイン S2 計画\n\n- [ ] タスク1", encoding="utf-8")
    assert _extract_title(session_dir) == "マザーブレイン S2 計画"

    # task.md がなく implementation_plan.md がある場合
    session_dir2 = tmp_path / "session-with-plan"
    session_dir2.mkdir()
    (session_dir2 / "implementation_plan.md").write_text("# API リファクタ計画\n\n...", encoding="utf-8")
    assert _extract_title(session_dir2) == "API リファクタ計画"

    # 何もない場合
    empty_dir = tmp_path / "empty-session"
    empty_dir.mkdir()
    assert _extract_title(empty_dir) == ""

    # # なしのファイル (ヘッダーがない)
    session_dir3 = tmp_path / "session-no-header"
    session_dir3.mkdir()
    (session_dir3 / "task.md").write_text("No header here\nJust plain text", encoding="utf-8")
    assert _extract_title(session_dir3) == ""


# PURPOSE: _scan_session がタイトルを抽出して DB に保存することをテストする
def test_scan_session_extracts_title(store: PhantazeinStore, tmp_path: Path) -> None:
    from mekhane.symploke.phantazein_indexer import _scan_session

    session_id = "aabbccdd-1111-2222-3333-444455556666"
    session_dir = tmp_path / session_id
    session_dir.mkdir()
    (session_dir / "task.md").write_text("# Boot ワークフロー実行\n\n- [x] done", encoding="utf-8")

    _scan_session(session_dir, store)

    sessions = store.get_ide_sessions(limit=10)
    assert len(sessions) == 1
    assert sessions[0]["title"] == "Boot ワークフロー実行"


# ── S2: find_closest_session テスト ────────────────────────


# PURPOSE: find_closest_session の日時近接ロジックをテストする
def test_find_closest_session(store: PhantazeinStore) -> None:
    # セッション A: 1000 ~ 2000
    store.upsert_ide_session(session_id="session-a", created_at=1000.0, updated_at=2000.0)
    # セッション B: 3000 ~ 4000
    store.upsert_ide_session(session_id="session-b", created_at=3000.0, updated_at=4000.0)

    # 期間内 → そのセッション
    assert store.find_closest_session(1500.0) == "session-a"
    assert store.find_closest_session(3500.0) == "session-b"

    # 期間外だが近い (updated_at + 30分以内)
    result = store.find_closest_session(2500.0, max_gap_seconds=600.0)
    assert result in ("session-a", "session-b")  # どちらか近い方

    # 遠すぎる → None
    assert store.find_closest_session(99999.0, max_gap_seconds=100.0) is None


# ── S2: Handoff/ROM リンクテスト ──────────────────────────


# PURPOSE: Handoff/ROM がセッションに紐づくことをテストする
def test_link_handoff_rom_to_session(store: PhantazeinStore) -> None:
    from mekhane.symploke.phantazein_indexer import _link_to_sessions

    # セッション: 1000 ~ 2000
    store.upsert_ide_session(session_id="session-x", created_at=1000.0, updated_at=2000.0)

    # Handoff: 1500 (セッション期間内)
    store.upsert_handoff(
        filename="handoff_test.md", filepath="/tmp/h1.md",
        created_at=1500.0, size_bytes=100,
    )
    # ROM: 1800 (セッション期間内)
    store.upsert_rom(
        filename="rom_test.md", filepath="/tmp/r1.md",
        created_at=1800.0, size_bytes=200,
    )
    # Handoff: 99999 (遠すぎ → リンクなし)
    store.upsert_handoff(
        filename="handoff_faraway.md", filepath="/tmp/h2.md",
        created_at=99999.0, size_bytes=100,
    )

    linked_h, linked_r = _link_to_sessions(store)
    assert linked_h == 1  # 1500 のみリンク
    assert linked_r == 1

    # DB 確認
    handoffs = store.get_handoffs(limit=10)
    linked = [h for h in handoffs if h["session_id"] == "session-x"]
    assert len(linked) == 1
    assert linked[0]["filename"] == "handoff_test.md"

    roms = store.get_roms(limit=10)
    linked_roms = [r for r in roms if r["session_id"] == "session-x"]
    assert len(linked_roms) == 1


# ── S2: ファイル名日時パースのテスト ──────────────────────


# PURPOSE: Handoff/ROM ファイル名から日時をパースするテスト
def test_parse_filename_datetime() -> None:
    from mekhane.symploke.phantazein_indexer import _parse_filename_datetime
    from datetime import datetime, timezone, timedelta

    jst = timezone(timedelta(hours=9))

    # パターン1: YYYY-MM-DD_HHMM
    ts = _parse_filename_datetime("handoff_2026-03-12_2234.md")
    assert ts is not None
    dt = datetime.fromtimestamp(ts, tz=jst)
    assert dt.year == 2026 and dt.month == 3 and dt.day == 12
    assert dt.hour == 22 and dt.minute == 34

    # パターン2: YYYY-MM-DD_HHMMSS_desc
    ts2 = _parse_filename_datetime("handoff_2026-03-12_215852_syncthing-setup.md")
    assert ts2 is not None
    dt2 = datetime.fromtimestamp(ts2, tz=jst)
    assert dt2.hour == 21 and dt2.minute == 58 and dt2.second == 52

    # パターン3: YYYYMMDD_desc
    ts3 = _parse_filename_datetime("handoff_20260312_session_restore.md")
    assert ts3 is not None
    dt3 = datetime.fromtimestamp(ts3, tz=jst)
    assert dt3.year == 2026 and dt3.month == 3 and dt3.day == 12
    assert dt3.hour == 12  # 正午

    # ROM パターン
    ts4 = _parse_filename_datetime("rom_2026-03-11_2124.md")
    assert ts4 is not None

    # マッチしないパターン
    assert _parse_filename_datetime("random_file.md") is None
    assert _parse_filename_datetime("notes_2026.md") is None


# ── Phase 2: Handoff パースのテスト ───────────────────────


# PURPOSE: 型 A (v2 YAML) のパーステスト
def test_parse_handoff_format_a() -> None:
    from mekhane.symploke.phantazein_indexer import _parse_handoff_content

    text = """# Session Handoff

```yaml
session_handoff:
  session_id: "abc12345-1111-2222-3333-444444444444"
  project: "Phantazein S3"
  workspace: "hegemonikon"
  version: "2.0"
```

## 成果
- Phase 1 完了
"""
    result = _parse_handoff_content(text)
    assert result["session_id"] == "abc12345-1111-2222-3333-444444444444"
    assert result["project"] == "Phantazein S3"
    assert result["workspace"] == "hegemonikon"
    assert result["handoff_version"] == "2.0"
    assert result["title"] == "Session Handoff"


# PURPOSE: 型 B (末尾 *Session: uuid*) のパーステスト
def test_parse_handoff_format_b() -> None:
    from mekhane.symploke.phantazein_indexer import _parse_handoff_content

    text = """# Legacy Handoff

## やったこと
- リファクタ完了

*Session: deadbeef-1234-5678-9abc-def012345678*
"""
    result = _parse_handoff_content(text)
    assert result["session_id"] == "deadbeef-1234-5678-9abc-def012345678"
    assert result["project"] is None  # 型 B には project がない
    assert result["title"] == "Legacy Handoff"


# PURPOSE: 型 C (Blockquote Session) のパーステスト
def test_parse_handoff_format_c() -> None:
    from mekhane.symploke.phantazein_indexer import _parse_handoff_content

    text = """# Blockquote Handoff

## 概要
- テスト

> **Session**: `aabbccdd-1111-2222-3333-444455556666`
"""
    result = _parse_handoff_content(text)
    assert result["session_id"] == "aabbccdd-1111-2222-3333-444455556666"
    assert result["title"] == "Blockquote Handoff"


# PURPOSE: 型 D (session_id なし) のパーステスト
def test_parse_handoff_format_d() -> None:
    from mekhane.symploke.phantazein_indexer import _parse_handoff_content

    text = """# No Session Handoff

## やったこと
- 何か
"""
    result = _parse_handoff_content(text)
    assert result["session_id"] is None
    assert result["project"] is None
    assert result["title"] == "No Session Handoff"


# PURPOSE: upsert_handoff 拡張パラメータの保存テスト
def test_upsert_handoff_with_project(store: PhantazeinStore) -> None:
    store.upsert_handoff(
        filename="handoff_2026-03-13_1000.md",
        filepath="/tmp/handoff.md",
        created_at=1000.0,
        size_bytes=500,
        title="Test Handoff",
        session_id="ses-111",
        project_name="Phantazein S3",
        handoff_version="2.0",
    )

    handoffs = store.get_handoffs(limit=10)
    assert len(handoffs) == 1
    h = handoffs[0]
    assert h["session_id"] == "ses-111"
    assert h["project_name"] == "Phantazein S3"
    assert h["handoff_version"] == "2.0"


# PURPOSE: _build_chains の η/ε 連鎖構築テスト
def test_build_chains(store: PhantazeinStore) -> None:
    from mekhane.symploke.phantazein_indexer import _build_chains

    # セッション A (1000), B (3000), C (5000)
    store.upsert_ide_session(session_id="sess-a", created_at=1000.0, updated_at=2000.0)
    store.upsert_ide_session(session_id="sess-b", created_at=3000.0, updated_at=4000.0)
    store.upsert_ide_session(session_id="sess-c", created_at=5000.0, updated_at=6000.0)

    # Handoff 1: sess-a が生成 (created_at=2500)
    store.upsert_handoff(
        filename="handoff_1.md", filepath="/tmp/h1.md",
        created_at=2500.0, size_bytes=100, title="Handoff 1",
        session_id="sess-a",
    )

    # Handoff 2: sess-b が生成 (created_at=4500)
    store.upsert_handoff(
        filename="handoff_2.md", filepath="/tmp/h2.md",
        created_at=4500.0, size_bytes=100, title="Handoff 2",
        session_id="sess-b",
    )

    chain_count = _build_chains(store)
    assert chain_count == 2

    # 連鎖確認: Handoff 1 の η は sess-b (Handoff 作成後の最初のセッション)
    chains = store._conn.execute(
        "SELECT * FROM handoff_chains ORDER BY handoff_id"
    ).fetchall()
    assert len(chains) == 2

    # Handoff 1: ε=sess-a, η=sess-b
    assert chains[0]["source_session_id"] == "sess-a"
    assert chains[0]["target_session_id"] == "sess-b"

    # Handoff 2: ε=sess-b, η=sess-c
    assert chains[1]["source_session_id"] == "sess-b"
    assert chains[1]["target_session_id"] == "sess-c"


# PURPOSE: get_handoff_by_filename のテスト
def test_get_handoff_by_filename(store: PhantazeinStore) -> None:
    store.upsert_handoff(
        filename="handoff_target.md", filepath="/tmp/h.md",
        created_at=1000.0, size_bytes=100, title="Target",
    )

    result = store.get_handoff_by_filename("handoff_target.md")
    assert result is not None
    assert result["title"] == "Target"

    # 存在しないファイル
    assert store.get_handoff_by_filename("nonexistent.md") is None
