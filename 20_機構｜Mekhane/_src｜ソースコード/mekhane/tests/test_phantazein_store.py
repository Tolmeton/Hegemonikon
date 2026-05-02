#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/tests/test_phantazein_store.py
# PURPOSE: PhantazeinStore の永続化・CRUD をテストする
"""
Tests for PhantazeinStore.
"""

import pytest
import sqlite3
import time
from pathlib import Path
from mekhane.symploke.phantazein_store import PhantazeinStore


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "test_phantazein.db"


@pytest.fixture
def store(temp_db: Path) -> PhantazeinStore:
    s = PhantazeinStore(db_path=temp_db)
    yield s
    s.close()


# PURPOSE: セッション登録と取得のテスト
def test_session_lifecycle(store: PhantazeinStore) -> None:
    session1 = store.register_session(context="test_context_1", agent="claude")
    assert session1.id
    assert session1.context == "test_context_1"
    assert session1.agent == "claude"
    assert session1.status == "active"

    session2 = store.register_session(context="test_context_2", agent="gemini")

    recent = store.get_recent_sessions(limit=10)
    assert len(recent) == 2
    # Ordered by start_time DESC, so session2 should be first
    assert recent[0]["id"] == session2.id
    assert recent[1]["id"] == session1.id

    store.update_session_status(session1.id, "completed")
    recent = store.get_recent_sessions()
    first_session = next(s for s in recent if s["id"] == session1.id)
    assert first_session["status"] == "completed"


# PURPOSE: プロジェクトスナップショットのテスト
def test_project_snapshots(store: PhantazeinStore) -> None:
    store.add_project_snapshot("proj_A", phase="design", status="in_progress", notes="Started", session_id="ses_1")
    time.sleep(0.01)
    store.add_project_snapshot("proj_B", phase="impl", status="active", notes="Coding", session_id="ses_1")
    time.sleep(0.01)
    store.add_project_snapshot("proj_A", phase="impl", status="completed", notes="Done", session_id="ses_2")

    # Get latest for proj_A
    latest_a = store.get_latest_snapshot("proj_A")
    assert latest_a is not None
    assert latest_a["phase"] == "impl"
    assert latest_a["status"] == "completed"

    # Get all latest
    all_latest = store.get_all_latest_snapshots()
    assert len(all_latest) == 2
    # Should contain the latest of A and B
    a_snap = next(s for s in all_latest if s["project_id"] == "proj_A")
    b_snap = next(s for s in all_latest if s["project_id"] == "proj_B")
    assert a_snap["status"] == "completed"
    assert b_snap["status"] == "active"


# PURPOSE: Consistency Log のテスト
def test_consistency_log(store: PhantazeinStore) -> None:
    store.log_consistency_issue(session_id="ses_1", issue="Duplicate work", severity="high", details="Details1")
    time.sleep(0.01)
    store.log_consistency_issue(session_id="ses_2", issue="Context mismatch", severity="medium", details="Details2")

    issues = store.get_recent_issues(limit=5)
    assert len(issues) == 2
    assert issues[0]["issue"] == "Context mismatch"
    assert issues[0]["severity"] == "medium"
    assert issues[1]["issue"] == "Duplicate work"
    assert issues[1]["severity"] == "high"


# PURPOSE: stats のテスト
def test_get_stats(store: PhantazeinStore) -> None:
    store.register_session()
    store.register_session()
    store.add_project_snapshot("A")
    store.log_consistency_issue()

    stats = store.get_stats()
    assert stats["sessions_total"] == 2
    assert stats["sessions_active"] == 2
    assert stats["snapshots_total"] == 1
    assert stats["issues_total"] == 1


# PURPOSE: S2 get_session_summary のテスト
def test_get_session_summary(store: PhantazeinStore) -> None:
    # セッション作成
    store.upsert_ide_session(
        session_id="ses_abc", title="Test Session",
        created_at=1000.0, updated_at=2000.0,
    )
    # Handoff 作成 + 紐づけ
    store.upsert_handoff(
        filename="handoff_test.md", filepath="/tmp/handoff_test.md",
        created_at=1500.0, size_bytes=100, title="Test Handoff",
    )
    store.link_handoff_to_session("handoff_test.md", "ses_abc")
    # ROM 作成 + 紐づけ
    store.upsert_rom(
        filename="rom_test.md", filepath="/tmp/rom_test.md",
        created_at=1600.0, size_bytes=200, topic="test topic",
    )
    store.link_rom_to_session("rom_test.md", "ses_abc")

    summary = store.get_session_summary(limit=5)
    assert len(summary) == 1
    assert summary[0]["id"] == "ses_abc"
    assert summary[0]["title"] == "Test Session"
    assert summary[0]["handoff_count"] == 1
    assert summary[0]["rom_count"] == 1


# PURPOSE: S2 get_recent_handoff_summaries のテスト
def test_get_recent_handoff_summaries(store: PhantazeinStore) -> None:
    # セッション + Handoff
    store.upsert_ide_session(
        session_id="ses_xyz", title="Linked Session",
        created_at=1000.0, updated_at=2000.0,
    )
    store.upsert_handoff(
        filename="handoff_linked.md", filepath="/tmp/handoff_linked.md",
        created_at=1500.0, size_bytes=100, title="Linked Handoff",
    )
    store.link_handoff_to_session("handoff_linked.md", "ses_xyz")
    # 紐づけなし Handoff
    store.upsert_handoff(
        filename="handoff_orphan.md", filepath="/tmp/handoff_orphan.md",
        created_at=2000.0, size_bytes=50, title="Orphan Handoff",
    )

    summaries = store.get_recent_handoff_summaries(limit=3)
    assert len(summaries) == 2
    # 最新が先 (orphan が created_at=2000)
    assert summaries[0]["filename"] == "handoff_orphan.md"
    assert summaries[0]["session_title"] is None  # 未紐づけ
    assert summaries[1]["filename"] == "handoff_linked.md"
    assert summaries[1]["session_title"] == "Linked Session"


# ── Hyphē 統一索引テスト ──────────────────────────────────


# PURPOSE: knowledge_node の作成・更新テスト
def test_knowledge_node_crud(store: PhantazeinStore) -> None:
    # 新規作成
    store.upsert_knowledge_node(
        "node_001", "kairos",
        source_id="handoff_test.md",
        title="テスト Handoff",
        content_preview="これはテスト用の Handoff です。",
        metadata_json='{"type": "handoff"}',
        session_id="ses_abc",
        project_id="proj_A",
        precision=0.9,
    )

    # 検索で確認 (LIKE フォールバック)
    results = store.search_knowledge("テスト")
    assert len(results) >= 1
    assert results[0]["id"] == "node_001"
    assert results[0]["source"] == "kairos"
    assert results[0]["title"] == "テスト Handoff"
    assert results[0]["precision"] == 0.9

    # 更新 (upsert)
    store.upsert_knowledge_node(
        "node_001", "kairos",
        source_id="handoff_test.md",
        title="更新された Handoff",
        content_preview="更新後のプレビュー。",
        precision=0.95,
    )
    results = store.search_knowledge("更新")
    assert len(results) >= 1
    assert results[0]["title"] == "更新された Handoff"


# PURPOSE: knowledge_edge の作成と重複排除テスト
def test_knowledge_edge_crud(store: PhantazeinStore) -> None:
    # ノードを2つ作成
    store.upsert_knowledge_node("edge_a", "kairos", title="Node A")
    store.upsert_knowledge_node("edge_b", "kairos", title="Node B")

    # エッジ追加
    store.add_knowledge_edge("edge_a", "edge_b", "same_session", weight=0.8, evidence="同一セッション")

    # 重複は無視される (INSERT OR IGNORE)
    store.add_knowledge_edge("edge_a", "edge_b", "same_session", weight=0.9)

    # 同じペアでも異なる relation_type なら追加可能
    store.add_knowledge_edge("edge_a", "edge_b", "same_project")

    stats = store.get_knowledge_stats()
    assert stats["total_nodes"] == 2
    assert stats["total_edges"] == 2  # same_session + same_project
    assert stats["edges_by_relation"]["same_session"] == 1
    assert stats["edges_by_relation"]["same_project"] == 1


# PURPOSE: FTS5 全文検索テスト (またはフォールバック)
def test_fts5_search(store: PhantazeinStore) -> None:
    store.upsert_knowledge_node(
        "fts_1", "gnosis",
        title="Free Energy Principle",
        content_preview="The free energy principle unifies perception and action.",
    )
    store.upsert_knowledge_node(
        "fts_2", "sophia",
        title="Active Inference",
        content_preview="Active inference is a corollary of the free energy principle.",
    )
    store.upsert_knowledge_node(
        "fts_3", "artifact",
        title="Implementation Plan",
        content_preview="This plan describes the implementation of new features.",
    )

    # ソースフィルタ付き検索
    results = store.search_knowledge("free energy", source_filter="gnosis")
    assert len(results) >= 1
    assert all(r["source"] == "gnosis" for r in results)

    # 全ソース検索
    results = store.search_knowledge("free energy")
    assert len(results) >= 1


# PURPOSE: グラフ探索 (2ホップ) テスト
def test_graph_traversal(store: PhantazeinStore) -> None:
    # A -> B -> C のチェーン
    store.upsert_knowledge_node("g_a", "kairos", title="Node A")
    store.upsert_knowledge_node("g_b", "kairos", title="Node B")
    store.upsert_knowledge_node("g_c", "kairos", title="Node C")
    store.add_knowledge_edge("g_a", "g_b", "same_session")
    store.add_knowledge_edge("g_b", "g_c", "same_session")

    # depth=1: A から B のみ
    neighbors_1 = store.get_node_neighbors("g_a", depth=1)
    assert len(neighbors_1) == 1
    assert neighbors_1[0]["node_id"] == "g_b"
    assert neighbors_1[0]["direction"] == "outgoing"

    # depth=2: A から B, C
    neighbors_2 = store.get_node_neighbors("g_a", depth=2)
    assert len(neighbors_2) == 2
    node_ids = {n["node_id"] for n in neighbors_2}
    assert node_ids == {"g_b", "g_c"}

    # relation_type フィルタ
    neighbors_filtered = store.get_node_neighbors(
        "g_a", relation_types=["same_project"], depth=2
    )
    assert len(neighbors_filtered) == 0  # same_project エッジは存在しない


# PURPOSE: 統一索引統計テスト
def test_knowledge_stats(store: PhantazeinStore) -> None:
    # 初期状態
    stats = store.get_knowledge_stats()
    assert stats["total_nodes"] == 0
    assert stats["total_edges"] == 0

    # データ追加
    store.upsert_knowledge_node("s_1", "kairos", title="Handoff 1")
    store.upsert_knowledge_node("s_2", "gnosis", title="Paper 1")
    store.upsert_knowledge_node("s_3", "kairos", title="ROM 1")
    store.add_knowledge_edge("s_1", "s_2", "cites")
    store.add_knowledge_edge("s_1", "s_3", "same_session")

    stats = store.get_knowledge_stats()
    assert stats["total_nodes"] == 3
    assert stats["total_edges"] == 2
    assert stats["nodes_by_source"]["kairos"] == 2
    assert stats["nodes_by_source"]["gnosis"] == 1
    assert stats["edges_by_relation"]["cites"] == 1
    assert stats["edges_by_relation"]["same_session"] == 1


# ── セッション×資産クロスリファレンステスト ──────────────────


# PURPOSE: get_session_cross_ref の基本統合ビューテスト
def test_session_cross_ref(store: PhantazeinStore) -> None:
    # セッション2つ作成
    store.upsert_ide_session(session_id="cr-ses-1", title="Session One", created_at=1000.0, updated_at=2000.0)
    store.upsert_ide_session(session_id="cr-ses-2", title="Session Two", created_at=3000.0, updated_at=4000.0)

    # セッション1に Handoff 2件
    store.upsert_handoff(filename="handoff_cr_1.md", filepath="/tmp/h1.md", created_at=1500.0, size_bytes=100, title="H1")
    store.link_handoff_to_session("handoff_cr_1.md", "cr-ses-1")
    store.upsert_handoff(filename="handoff_cr_2.md", filepath="/tmp/h2.md", created_at=1600.0, size_bytes=200, title="H2")
    store.link_handoff_to_session("handoff_cr_2.md", "cr-ses-1")

    # セッション1に ROM 1件
    store.upsert_rom(filename="rom_cr_1.md", filepath="/tmp/r1.md", created_at=1700.0, size_bytes=300, topic="test topic")
    store.link_rom_to_session("rom_cr_1.md", "cr-ses-1")

    # セッション1にアーティファクト3件
    store.upsert_artifact(session_id="cr-ses-1", filename="task.md", artifact_type="task", size_bytes=500, is_standard=True)
    store.upsert_artifact(session_id="cr-ses-1", filename="report.md", artifact_type="other", size_bytes=10000, is_standard=False)
    store.upsert_artifact(session_id="cr-ses-1", filename="plan.md", artifact_type="implementation_plan", size_bytes=3000, is_standard=True)

    # セッション2にアーティファクト1件
    store.upsert_artifact(session_id="cr-ses-2", filename="task.md", artifact_type="task", size_bytes=400, is_standard=True)

    # クロスリファレンス取得
    results = store.get_session_cross_ref(limit=10)
    assert len(results) == 2

    # セッション2が先 (created_at DESC)
    ses2 = results[0]
    ses1 = results[1]
    assert ses2["id"] == "cr-ses-2"
    assert ses1["id"] == "cr-ses-1"

    # セッション1の Handoff
    assert len(ses1["handoffs"]) == 2

    # セッション1の ROM
    assert len(ses1["roms"]) == 1
    assert ses1["roms"][0]["topic"] == "test topic"

    # セッション1のアーティファクト
    assert len(ses1["artifacts"]) == 3

    # セッション2は紐づけなし
    assert len(ses2["handoffs"]) == 0
    assert len(ses2["roms"]) == 0
    assert len(ses2["artifacts"]) == 1


# PURPOSE: get_session_cross_ref の days フィルタテスト
def test_session_cross_ref_with_days_filter(store: PhantazeinStore) -> None:
    now = time.time()
    # 今日のセッション
    store.upsert_ide_session(session_id="day-ses-1", title="Today", created_at=now, updated_at=now)
    # 8日前のセッション
    store.upsert_ide_session(session_id="day-ses-2", title="Old", created_at=now - 8 * 86400, updated_at=now - 8 * 86400)

    results = store.get_session_cross_ref(days=3)
    assert len(results) == 1
    assert results[0]["id"] == "day-ses-1"

    # days 指定なし → 全件
    results_all = store.get_session_cross_ref(limit=10)
    assert len(results_all) == 2


# PURPOSE: get_session_cross_ref の PJ 紐づけテスト
def test_session_cross_ref_with_project(store: PhantazeinStore) -> None:
    # セッション + PJ 作成
    store.upsert_ide_session(session_id="pj-ses-1", title="PJ Session", created_at=1000.0, updated_at=2000.0)
    store.upsert_project(project_id="pj_001", name="Phantazein S3")

    # session_projects に紐づけ
    store._conn.execute(
        "INSERT OR IGNORE INTO session_projects (session_id, project_id) VALUES (?, ?)",
        ("pj-ses-1", "pj_001"),
    )
    store._conn.commit()

    results = store.get_session_cross_ref(limit=5)
    assert len(results) == 1
    assert len(results[0]["projects"]) == 1
    assert results[0]["projects"][0]["project_id"] == "pj_001"
    assert results[0]["projects"][0]["name"] == "Phantazein S3"


# PURPOSE: V-012 ヘルスチェックのバッチ記録とサマリーをテストする
def test_health_check_log(store):
    """log_health_batch / get_health_summary の基本テスト。"""
    # UP/DOWN 混在のバッチ記録
    results = [
        {"server_name": "ochema", "port": 9701, "status": "up", "latency_ms": 12.5},
        {"server_name": "jules", "port": 9708, "status": "down", "error": "connection refused"},
        {"server_name": "jules", "port": 9708, "status": "down", "error": "connection refused"},
        {"server_name": "mneme", "port": 9704, "status": "up", "latency_ms": 8.3},
    ]
    store.log_health_batch(results)

    # DB に記録されているか確認
    rows = store._conn.execute("SELECT COUNT(*) FROM health_checks").fetchone()
    assert rows[0] == 4

    # サマリー: jules のみ down 2件
    summary = store.get_health_summary()
    assert "failures_24h" in summary
    assert summary["failures_24h"].get("jules") == 2
    assert "ochema" not in summary["failures_24h"]
    assert "mneme" not in summary["failures_24h"]

