#!/usr/bin/env python3
# PROOF: [L2/テスト] <- mekhane/tests/test_report_generator.py
# PURPOSE: report_generator.py のユニットテスト
"""
Report Generator テスト — render_report() の出力検証。

テスト対象:
  - 正常データでの Markdown 生成
  - 空データでの安全な出力
  - KPI 計算の正確性
  - 各セクション (§0~§6) の存在確認
"""

import pytest
import time
from mekhane.symploke.report_generator import render_report, _ts_to_str, _human_bytes


# ── ヘルパ ──────────────────────────────────────────────────


# PURPOSE: テスト用のサンプルデータを構築する
def _make_sample_data(num_sessions: int = 3, num_handoffs: int = 2) -> dict:
    """テスト用のレポートデータを構築する。"""
    now = time.time()
    sessions = []
    for i in range(num_sessions):
        artifacts = [
            {"artifact_type": "task", "size_bytes": 1000, "filename": f"task_{i}.md"},
            {"artifact_type": "walkthrough", "size_bytes": 2000, "filename": f"walk_{i}.md"},
        ]
        handoffs = []
        if i < num_handoffs:
            handoffs = [{"filename": f"handoff_{i}.md", "title": f"HO {i}"}]
        roms = [{"filename": f"rom_{i}.md"}] if i == 0 else []
        sessions.append({
            "id": f"session-{i:04d}-abcd-efgh-1234-5678",
            "title": f"セッション {i+1}",
            "created_at": now - (num_sessions - i) * 3600,
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
            "handoffs": handoffs,
            "roms": roms,
            "projects": [{"name": "HGK"}] if i == 0 else [],
            "has_handoff": len(handoffs) > 0,
        })

    return {
        "period": {
            "days": 1,
            "start": now - 86400,
            "end": now,
        },
        "summary": {
            "total_sessions": num_sessions,
            "active_sessions": num_sessions,
            "total_artifacts": num_sessions * 2,
            "total_handoffs": num_handoffs,
            "total_roms": 1,
            "handoff_coverage": round(num_handoffs / num_sessions * 100, 1) if num_sessions > 0 else 0.0,
        },
        "artifact_breakdown": {
            "task": {"count": num_sessions, "total_bytes": num_sessions * 1000},
            "walkthrough": {"count": num_sessions, "total_bytes": num_sessions * 2000},
        },
        "sessions": sessions,
        "orphan_artifacts": [],
        "timeline": [
            {"day": "2026-03-13", "session_count": num_sessions, "total_artifacts": num_sessions * 2},
        ],
    }


# ── テスト ──────────────────────────────────────────────────


class TestHelpers:
    """ヘルパ関数のテスト。"""

    def test_ts_to_str_zero(self):
        assert _ts_to_str(0.0) == "N/A"

    def test_ts_to_str_valid(self):
        # Unix timestamp 0 = 1970-01-01 09:00:00 JST
        result = _ts_to_str(0.0 + 1)  # epoch + 1sec
        assert "1970" in result

    def test_human_bytes_small(self):
        assert _human_bytes(500) == "500 B"

    def test_human_bytes_kb(self):
        result = _human_bytes(2048)
        assert "KB" in result

    def test_human_bytes_mb(self):
        result = _human_bytes(2 * 1024 * 1024)
        assert "MB" in result


class TestRenderReport:
    """render_report() のテスト。"""

    def test_basic_structure(self):
        """全セクションが含まれるか。"""
        data = _make_sample_data()
        md = render_report(data)

        assert "# セッション統合レポート" in md
        assert "## §1 サマリ KPI" in md
        assert "## §2 セッション一覧" in md
        assert "## §3 アーティファクト分類" in md
        assert "## §4 Orphan アーティファクト" in md
        assert "## §5 Handoff カバレッジ詳細" in md
        assert "## §6 タイムライン" in md

    def test_kpi_values(self):
        """KPI テーブルの値が正しいか。"""
        data = _make_sample_data(num_sessions=5, num_handoffs=3)
        md = render_report(data)

        assert "| セッション総数 | 5 |" in md
        assert "| アーティファクト総数 | 10 |" in md
        assert "| Handoff 総数 | 3 |" in md
        assert "| Handoff カバレッジ | 60.0% |" in md

    def test_low_coverage_warning(self):
        """Handoff カバレッジ < 50% で警告が出るか。"""
        data = _make_sample_data(num_sessions=5, num_handoffs=1)
        md = render_report(data)

        assert "[!CAUTION]" in md
        assert "カバレッジ" in md

    def test_no_sessions(self):
        """セッションゼロでも安全に生成できるか。"""
        data = _make_sample_data(num_sessions=0, num_handoffs=0)
        md = render_report(data)

        assert "# セッション統合レポート" in md
        assert "見つかりませんでした" in md

    def test_custom_title(self):
        """カスタムタイトルが適用されるか。"""
        data = _make_sample_data()
        md = render_report(data, title="テスト用レポート")

        assert "# テスト用レポート" in md

    def test_orphan_section_empty(self):
        """Orphan が0件のとき、安全メッセージが出るか。"""
        data = _make_sample_data()
        md = render_report(data)

        assert "永続化漏れの候補は検出されませんでした" in md

    def test_orphan_section_with_data(self):
        """Orphan がある場合、警告が出るか。"""
        data = _make_sample_data()
        data["orphan_artifacts"] = [
            {"filename": "big_file.md", "session_id": "abc123", "size_bytes": 10000, "session_title": "テスト"},
        ]
        md = render_report(data)

        assert "[!WARNING]" in md
        assert "big_file.md" in md

    def test_artifact_breakdown(self):
        """アーティファクト分類テーブルが正しいか。"""
        data = _make_sample_data(num_sessions=3)
        md = render_report(data)

        assert "task" in md
        assert "walkthrough" in md
        assert "**合計**" in md

    def test_handoff_coverage_detail(self):
        """Handoff なしセッションが正しくリストされるか。"""
        data = _make_sample_data(num_sessions=3, num_handoffs=1)
        md = render_report(data)

        # セッション3のうちHandoffありは1つ → 2つはHandoffなし
        assert "Handoff なしセッション: 2 件" in md

    def test_footer(self):
        """フッタが含まれるか。"""
        data = _make_sample_data()
        md = render_report(data)

        assert "Phantazein Report Generator v1.0" in md


class TestGetReportData:
    """get_report_data() の統合テスト (Store 必要)。"""

    def test_empty_db(self, tmp_path):
        """空 DB で get_report_data() が安全に動作するか。"""
        from mekhane.symploke.phantazein_store import PhantazeinStore

        store = PhantazeinStore(tmp_path / "test.db")
        data = store.get_report_data(days=1)

        assert data["summary"]["total_sessions"] == 0
        assert data["summary"]["handoff_coverage"] == 0.0
        assert data["artifact_breakdown"] == {}
        assert data["sessions"] == []

    def test_with_session(self, tmp_path):
        """セッションありで get_report_data() が正しくデータを返すか。"""
        from mekhane.symploke.phantazein_store import PhantazeinStore
        import time as _time

        store = PhantazeinStore(tmp_path / "test.db")

        # ide_sessions + artifacts に直接 INSERT (get_session_cross_ref が読むテーブル)
        now = _time.time()
        sid = "test-session-001"
        store._conn.execute(
            """INSERT INTO ide_sessions (id, title, created_at, updated_at, artifact_count, dir_path)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sid, "テストセッション", now, now, 1, "/tmp/test"),
        )
        store._conn.execute(
            """INSERT INTO artifacts (session_id, filename, artifact_type, size_bytes, is_standard, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (sid, "task.md", "task", 500, 1, now, now),
        )
        store._conn.commit()

        data = store.get_report_data(days=1)

        assert data["summary"]["total_sessions"] >= 1
        assert data["summary"]["total_artifacts"] >= 1
        assert len(data["sessions"]) >= 1
