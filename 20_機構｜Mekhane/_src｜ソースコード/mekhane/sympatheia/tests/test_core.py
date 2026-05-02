"""sympatheia/core.py のユニットテスト。

通知系ヘルパー (send/dismiss/purge/list) + WBC + Feedback のビジネスロジックを検証。
ファイル I/O は tmp_path + monkeypatch で隔離。
"""
# PROOF: mekhane/sympatheia/tests/test_core.py
# PURPOSE: core.py の通知系 + WBC + Feedback ロジックのテスト
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

# テスト対象を直接 import
from mekhane.sympatheia import core


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _isolate_fs(tmp_path, monkeypatch):
    """core.py のグローバルパスを tmp_path にリダイレクト。"""
    mneme = tmp_path / "mneme"
    mneme.mkdir()
    state_logs = tmp_path / "state" / "logs"
    state_logs.mkdir(parents=True)
    state_cache = tmp_path / "state" / "cache"
    state_cache.mkdir(parents=True)
    state_violations = tmp_path / "state" / "violations"
    state_violations.mkdir(parents=True)
    handoff_dir = tmp_path / "handoff"
    handoff_dir.mkdir()

    monkeypatch.setattr(core, "MNEME", mneme)
    monkeypatch.setattr(core, "STATE_LOGS", state_logs)
    monkeypatch.setattr(core, "STATE_CACHE", state_cache)
    monkeypatch.setattr(core, "STATE_VIOLATIONS", state_violations)
    monkeypatch.setattr(core, "HANDOFF_DIR", handoff_dir)


# ─────────────────────────────────────────────
# _read_json / _write_json
# ─────────────────────────────────────────────

class TestReadWriteJson:
    """JSON ヘルパー関数のテスト。"""

    def test_read_nonexistent_returns_default(self, tmp_path):
        result = core._read_json(tmp_path / "nope.json", {"k": "v"})
        assert result == {"k": "v"}

    def test_read_nonexistent_returns_empty_dict(self, tmp_path):
        result = core._read_json(tmp_path / "nope.json")
        assert result == {}

    def test_roundtrip(self, tmp_path):
        p = tmp_path / "test.json"
        core._write_json(p, {"hello": "世界"})
        assert core._read_json(p) == {"hello": "世界"}

    def test_corrupt_json_returns_default(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json!", "utf-8")
        assert core._read_json(p, [1, 2]) == [1, 2]


# ─────────────────────────────────────────────
# _send_notification (dedup ロジック含む)
# ─────────────────────────────────────────────

class TestSendNotification:
    """通知送信 + dedup ロジック。"""

    def test_creates_notification(self):
        notif_id = core._send_notification("test", "INFO", "タイトル", "本文")
        assert len(notif_id) == 8  # uuid[:8]

        # JSONL に書き込まれたか
        notif_file = core.MNEME / "notifications.jsonl"
        lines = notif_file.read_text("utf-8").strip().split("\n")
        assert len(lines) == 1
        rec = json.loads(lines[0])
        assert rec["source"] == "test"
        assert rec["title"] == "タイトル"
        assert rec["level"] == "INFO"

    def test_dedup_same_source_title(self):
        """同一 source+title の通知は 60秒以内は dedup される。"""
        id1 = core._send_notification("s", "INFO", "t", "body1")
        id2 = core._send_notification("s", "INFO", "t", "body2")

        # dedup が発動: id2 は id1 と同じ (または "dedup")
        notif_file = core.MNEME / "notifications.jsonl"
        lines = [l for l in notif_file.read_text("utf-8").strip().split("\n") if l.strip()]
        # JSONL には1行しかない
        assert len(lines) == 1

    def test_different_titles_not_deduped(self):
        """異なる title は dedup されない。"""
        core._send_notification("s", "INFO", "t1", "body")
        core._send_notification("s", "INFO", "t2", "body")

        notif_file = core.MNEME / "notifications.jsonl"
        lines = [l for l in notif_file.read_text("utf-8").strip().split("\n") if l.strip()]
        assert len(lines) == 2


# ─────────────────────────────────────────────
# _dismiss_notification
# ─────────────────────────────────────────────

class TestDismissNotification:
    """通知の dismiss (ソフト削除)。"""

    def test_dismiss_existing(self):
        notif_id = core._send_notification("s", "INFO", "t", "b")
        assert core._dismiss_notification(notif_id) is True

        # dismissed フラグが付いているか
        notif_file = core.MNEME / "notifications.jsonl"
        rec = json.loads(notif_file.read_text("utf-8").strip())
        assert rec["dismissed"] is True
        assert "dismissed_at" in rec

    def test_dismiss_nonexistent(self):
        core._send_notification("s", "INFO", "t", "b")
        assert core._dismiss_notification("nonexistent") is False

    def test_dismiss_empty_file(self):
        assert core._dismiss_notification("any") is False


# ─────────────────────────────────────────────
# _purge_notifications
# ─────────────────────────────────────────────

class TestPurgeNotifications:
    """TTL ベースの purge。"""

    def test_purge_old_info(self):
        """INFO (TTL=7日) の古い通知が purge される。"""
        notif_file = core.MNEME / "notifications.jsonl"
        old_ts = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        rec = json.dumps({
            "id": "old1", "timestamp": old_ts,
            "source": "s", "level": "INFO", "title": "t", "body": "b",
        })
        notif_file.write_text(rec + "\n", "utf-8")

        result = core._purge_notifications()
        assert result["purged"] == 1
        assert result["remaining"] == 0

    def test_keep_recent_info(self):
        """INFO でも新しければ purge されない。"""
        notif_file = core.MNEME / "notifications.jsonl"
        recent_ts = datetime.now(timezone.utc).isoformat()
        rec = json.dumps({
            "id": "new1", "timestamp": recent_ts,
            "source": "s", "level": "INFO", "title": "t", "body": "b",
        })
        notif_file.write_text(rec + "\n", "utf-8")

        result = core._purge_notifications()
        assert result["purged"] == 0
        assert result["remaining"] == 1

    def test_purge_empty_file(self):
        result = core._purge_notifications()
        assert result == {"purged": 0, "remaining": 0}


# ─────────────────────────────────────────────
# _list_notifications_raw
# ─────────────────────────────────────────────

class TestListNotifications:
    """通知リスト取得 + フィルタ。"""

    def _seed(self, n: int = 3):
        for i in range(n):
            level = "CRITICAL" if i == 0 else "INFO"
            core._send_notification(f"s{i}", level, f"t{i}", f"b{i}")

    def test_list_returns_newest_first(self):
        self._seed(3)
        results = core._list_notifications_raw(limit=10)
        assert len(results) == 3
        # 最新が先頭
        assert results[0]["timestamp"] >= results[-1]["timestamp"]

    def test_filter_by_level(self):
        self._seed(3)
        critical = core._list_notifications_raw(level="CRITICAL")
        assert all(r["level"] == "CRITICAL" for r in critical)

    def test_limit(self):
        self._seed(5)
        results = core._list_notifications_raw(limit=2)
        assert len(results) == 2

    def test_exclude_dismissed(self):
        notif_id = core._send_notification("s", "INFO", "t", "b")
        core._dismiss_notification(notif_id)
        results = core._list_notifications_raw(include_dismissed=False)
        assert len(results) == 0

    def test_include_dismissed(self):
        notif_id = core._send_notification("s", "INFO", "t", "b")
        core._dismiss_notification(notif_id)
        results = core._list_notifications_raw(include_dismissed=True)
        assert len(results) == 1

    def test_empty_file(self):
        results = core._list_notifications_raw()
        assert results == []


# ─────────────────────────────────────────────
# wbc_analyze (WF-09 脅威分析)
# ─────────────────────────────────────────────

class TestWBCAnalyze:
    """WBC 脅威分析のビジネスロジック。"""

    def test_low_threat(self):
        import asyncio
        req = core.WBCRequest(
            source="test", severity="low",
            details="minor change", files=["README.md"],
        )
        resp = asyncio.run(core.wbc_analyze(req))
        assert resp.level == "LOW"
        assert resp.shouldEscalate is False
        assert resp.source == "test"

    def test_critical_sacred_file(self):
        """SACRED_TRUTH.md への critical 変更 → HIGH/CRITICAL。"""
        import asyncio
        req = core.WBCRequest(
            source="test", severity="critical",
            details="sacred change",
            files=["SACRED_TRUTH.md"],
        )
        resp = asyncio.run(core.wbc_analyze(req))
        # threat_score = 5 (critical) + 10 (SACRED_TRUTH) = 15
        assert resp.threatScore >= 8
        assert resp.level in ("HIGH", "CRITICAL")
        assert resp.shouldEscalate is True

    def test_threat_score_calculation(self):
        """severity + THREAT_WEIGHTS の加算を検証。"""
        import asyncio
        req = core.WBCRequest(
            source="test", severity="high",
            details="bc change",
            files=["behavioral_constraints.md", "registry.yaml"],
        )
        resp = asyncio.run(core.wbc_analyze(req))
        # 3 (high) + 8 (bc) + 7 (registry) = 18 → CRITICAL
        assert resp.threatScore >= 8
        assert resp.level == "CRITICAL"

    def test_state_persistence(self):
        """アラートが wbc_state.json に保存される。"""
        import asyncio
        req = core.WBCRequest(
            source="test", severity="low", details="d", files=[],
        )
        asyncio.run(core.wbc_analyze(req))

        state = core._read_json(core.STATE_VIOLATIONS / "wbc_state.json")
        assert state["totalAlerts"] == 1
        assert len(state["alerts"]) == 1


# ─────────────────────────────────────────────
# feedback_loop (WF-12 恒常性)
# ─────────────────────────────────────────────

class TestFeedbackLoop:
    """Feedback loop の閾値調整ロジック。"""

    def _write_health_metrics(self, scores: list[float]):
        """健康スコアを health_metrics.jsonl に書き込む。"""
        health_file = core.STATE_LOGS / "health_metrics.jsonl"
        now = datetime.now(timezone.utc)
        with open(health_file, "w", encoding="utf-8") as f:
            for i, score in enumerate(scores):
                ts = (now - timedelta(hours=len(scores) - i)).isoformat()
                f.write(json.dumps({"timestamp": ts, "score": score}) + "\n")

    def test_no_adjustment_normal(self):
        """avg が中間域ならば調整なし。"""
        import asyncio
        self._write_health_metrics([0.5, 0.6, 0.5, 0.6, 0.5])
        resp = asyncio.run(core.feedback_loop(core.FeedbackRequest()))
        assert resp.adjusted is False
        assert resp.adjustments == []

    def test_adjust_on_high_avg(self):
        """avg > 0.9 かつ samples >= 10 で health_high を下げる。"""
        import asyncio
        self._write_health_metrics([0.95] * 12)
        resp = asyncio.run(core.feedback_loop(core.FeedbackRequest()))
        assert resp.adjusted is True
        assert any("health_high" in a for a in resp.adjustments)

    def test_adjust_on_low_avg(self):
        """avg < 0.4 かつ samples >= 5 で health_high を上げる。"""
        import asyncio
        self._write_health_metrics([0.2, 0.3, 0.1, 0.2, 0.3])
        resp = asyncio.run(core.feedback_loop(core.FeedbackRequest()))
        assert resp.adjusted is True

    def test_no_data(self):
        """データなしでもエラーにならない。"""
        import asyncio
        resp = asyncio.run(core.feedback_loop(core.FeedbackRequest()))
        assert resp.adjusted is False
        assert resp.metrics["samples"] == 0


# ─────────────────────────────────────────────
# incoming_route (WF-14 ルーター)
# ─────────────────────────────────────────────

class TestIncomingRoute:
    """ルーティングロジック (n8n 呼出はモック)。"""

    def test_unknown_type(self):
        import asyncio
        req = core.RouteRequest(type="unknown_xyz", source="test")
        resp = asyncio.run(core.incoming_route(req))
        assert resp.routed is False
        assert resp.error == "Unknown type"
        assert "health" in resp.available

    def test_known_type_routes(self):
        """既知の type は正しいルートにマッチする。"""
        import asyncio
        req = core.RouteRequest(type="health", source="test", payload={"k": "v"})
        import httpx as _httpx_mod
        with patch.object(_httpx_mod, "post") as mock_post:
            mock_resp = type("Resp", (), {"json": lambda self: {"ok": True}, "status_code": 200, "text": ""})()
            mock_post.return_value = mock_resp
            resp = asyncio.run(core.incoming_route(req))

        assert resp.routed is True
        assert resp.target == "health-alert"
        assert resp.wf == "WF-05"

    def test_forward_failure(self):
        """n8n 接続失敗時もエラーなし (forwardResult にエラー情報)。"""
        import asyncio
        req = core.RouteRequest(type="wbc", source="test", payload={})
        import httpx as _httpx_mod
        with patch.object(_httpx_mod, "post", side_effect=ConnectionError("no n8n")):
            resp = asyncio.run(core.incoming_route(req))

        assert resp.routed is True
        assert resp.forwardResult is not None
        assert "error" in resp.forwardResult


# ─────────────────────────────────────────────
# TestCognitiveScan (Phase c 統合)
# ─────────────────────────────────────────────

class TestCognitiveScan:
    """fixation + wf_pattern の統合スキャンと複合スコア・WBC 接続のテスト。"""

    @pytest.fixture(autouse=True)
    def _mock_dependencies(self, monkeypatch):
        # 依存するサブシステムをモック化
        from mekhane.sympatheia.core import FixationResponse, WFPatternResponse, WBCResponse

        async def mock_fixation(*args, **kwargs):
            self.fixation_called += 1
            return FixationResponse(
                timestamp="2026-03-15T12:00:00",
                total_hits=1 if self.mock_fix_detected else 0,
                has_fixation=self.mock_fix_detected,
                max_score=self.mock_fix_ratio,
            )
        
        async def mock_wf_pattern(*args, **kwargs):
            self.wf_called += 1
            return WFPatternResponse(
                timestamp="2026-03-15T12:00:00",
                total_records=10,
                has_imbalance=self.mock_wf_detected,
                ee_ratio=self.mock_wf_ee,
                entropy_ratio=self.mock_wf_en,
                alerts=["Mock WF Alert"] if self.mock_wf_detected else []
            )

        async def mock_wbc(*args, **kwargs):
            self.wbc_called += 1
            return WBCResponse(
                timestamp="2026-03-15T12:00:00",
                source="Q-series",
                severity="critical",
                threatScore=15,
                level="CRITICAL",
                details="Cognitive scan threshold exceeded",
                files=[],
                recentAlertCount=1,
                shouldEscalate=True,
            )

        # Core の _send_notification もモック化 (副作用防止)
        def mock_send(*args, **kwargs):
            self.send_called += 1
            return "notif123"

        monkeypatch.setattr(core, "fixation_analyze", mock_fixation)
        monkeypatch.setattr(core, "wf_pattern_analyze", mock_wf_pattern)
        monkeypatch.setattr(core, "wbc_analyze", mock_wbc)
        monkeypatch.setattr(core, "_send_notification", mock_send)

        self.fixation_called = 0
        self.wf_called = 0
        self.wbc_called = 0
        self.send_called = 0

        # デフォルトのモック復帰値 (正常状態)
        self.mock_fix_detected = False
        self.mock_fix_ratio = 0.0
        self.mock_wf_detected = False
        self.mock_wf_ee = 0.5
        self.mock_wf_en = 1.0

    def test_normal_scan(self):
        """正常時: いずれの偏りも検出されず、スコアは 0.0。WBC も呼ばれない。"""
        import asyncio
        req = core.CognitiveScanRequest(text="正常なテキスト", days=7, threshold=0.5)
        resp = asyncio.run(core.cognitive_scan(req))

        assert resp.cognitive_score == 0.0
        assert resp.wbc_triggered is False
        assert self.wbc_called == 0
        assert self.send_called == 0

    def test_fixation_only(self):
        """Fixation のみ検出: スコアは最大 0.4。閾値 (0.5) 未満なら WBC は呼ばれない。"""
        import asyncio
        self.mock_fix_detected = True
        self.mock_fix_ratio = 0.3  # 正規化上限
        
        req = core.CognitiveScanRequest(text="固着テキスト", days=7, threshold=0.5)
        resp = asyncio.run(core.cognitive_scan(req))

        assert resp.cognitive_score == 0.4
        assert resp.fixation_detected is True
        assert resp.wbc_triggered is False
        assert self.wbc_called == 0
        assert self.send_called == 0  # 閾値未満＋片方のみなので通知なし

    def test_fixation_and_wf_triggers_notification(self):
        """両方検出された場合はスコアが閾値以下でも通知 (WBC 発行とは別) が行われる。"""
        import asyncio
        self.mock_fix_detected = True
        self.mock_fix_ratio = 0.15  # score 0.2
        self.mock_wf_detected = True
        self.mock_wf_ee = 0.5
        self.mock_wf_en = 1.0
        
        req = core.CognitiveScanRequest(text="固着テキスト", days=7, threshold=0.8)
        resp = asyncio.run(core.cognitive_scan(req))

        # fix(0.2) + wf_alert(0.075) = 0.275 < 0.8 → WBC 未発行
        assert resp.wbc_triggered is False
        assert self.send_called == 1  # 固着+偏り両方検出による通知

    def test_wbc_triggered_on_threshold(self):
        """スコアが閾値 (0.5) を超えた場合に wbc_analyze が呼び出され、通知も飛ぶ。"""
        import asyncio
        self.mock_fix_detected = True
        self.mock_fix_ratio = 0.3   # fix = 0.4
        self.mock_wf_detected = True  # wf alerts = 1 → wf = 0.3 * (1/4) = 0.075
        self.mock_wf_ee = 0.1       # < 0.2 → ee = 0.3
        # 合計スコア = 0.4 + 0.075 + 0.3 = 0.775

        req = core.CognitiveScanRequest(text="重度の偏りテキスト", days=7, threshold=0.5)
        resp = asyncio.run(core.cognitive_scan(req))

        assert resp.cognitive_score == 0.775
        assert resp.wbc_triggered is True
        assert self.wbc_called == 1
        assert self.send_called == 1
        assert resp.wbc_threat_score == 15

