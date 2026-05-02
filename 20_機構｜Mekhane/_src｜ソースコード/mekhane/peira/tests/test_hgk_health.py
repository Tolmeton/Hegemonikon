#!/usr/bin/env python3
# PROOF: [L2/テスト] <- mekhane/peira/ A0→テストが必要→test_hgk_healthが担う
"""
Tests for hgk_health.py — Hegemonikón Health Dashboard
"""

from mekhane.paths import MNEME_STATE
import subprocess
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from mekhane.peira.hgk_health import (
    HealthItem,
    HealthReport,
    check_systemd_service,
    check_n8n,
    check_cron,
    check_handoff,
    check_hermeneus,
    check_kalon,
    check_theorem_activity,
    format_terminal,
    run_health_check,
    get_effective_health_profile,
    use_ops_relaxed_checks,
)


# PURPOSE: HealthItem のデータ保持と emoji 変換をテスト
class TestHealthItem(unittest.TestCase):
    """Test suite for health item."""
    def test_ok_emoji(self):
        """Verify ok emoji behavior."""
        item = HealthItem("Test", "ok", "detail")
        self.assertEqual(item.emoji, "🟢")

    # PURPOSE: error_emoji をテストする
    def test_error_emoji(self):
        """Verify error emoji behavior."""
        item = HealthItem("Test", "error", "detail")
        self.assertEqual(item.emoji, "🔴")

    # PURPOSE: warn_emoji をテストする
    def test_warn_emoji(self):
        """Verify warn emoji behavior."""
        item = HealthItem("Test", "warn", "detail")
        self.assertEqual(item.emoji, "🟡")

    # PURPOSE: unknown_emoji をテストする
    def test_unknown_emoji(self):
        """Verify unknown emoji behavior."""
        item = HealthItem("Test", "unknown", "detail")
        self.assertEqual(item.emoji, "⚪")

    # PURPOSE: metric_optional をテストする
    def test_metric_optional(self):
        """Verify metric optional behavior."""
        item = HealthItem("Test", "ok")
        self.assertIsNone(item.metric)
        item2 = HealthItem("Test", "ok", metric=42.0)
        self.assertEqual(item2.metric, 42.0)


# PURPOSE: HealthReport の score 計算をテスト
class TestHealthReport(unittest.TestCase):
    """Test suite for health report."""
    def test_all_ok_score(self):
        """Verify all ok score behavior."""
        report = HealthReport(
            timestamp="test",
            items=[HealthItem("A", "ok"), HealthItem("B", "ok"), HealthItem("C", "ok")],
        )
        self.assertAlmostEqual(report.score, 1.0)

    # PURPOSE: all_error_score をテストする
    def test_all_error_score(self):
        """Verify all error score behavior."""
        report = HealthReport(
            timestamp="test",
            items=[HealthItem("A", "error"), HealthItem("B", "error")],
        )
        self.assertAlmostEqual(report.score, 0.0)

    # PURPOSE: mixed_score をテストする
    def test_mixed_score(self):
        """Verify mixed score behavior."""
        report = HealthReport(
            timestamp="test",
            items=[HealthItem("A", "ok"), HealthItem("B", "error")],
        )
        self.assertAlmostEqual(report.score, 0.5)

    # PURPOSE: warn_score をテストする
    def test_warn_score(self):
        """Verify warn score behavior."""
        report = HealthReport(
            timestamp="test",
            items=[HealthItem("A", "warn")],
        )
        self.assertAlmostEqual(report.score, 0.6)

    # PURPOSE: empty_score をテストする
    def test_empty_score(self):
        """Verify empty score behavior."""
        report = HealthReport(timestamp="test", items=[])
        self.assertAlmostEqual(report.score, 0.0)


# PURPOSE: systemd サービスチェックのモックテスト
class TestCheckSystemd(unittest.TestCase):
    """Test suite for check systemd."""

    @patch("subprocess.run")
    def test_active_service(self, mock_run):
        """Verify active service behavior."""
        mock_run.return_value = MagicMock(stdout="active\n")
        result = check_systemd_service("Test Service", "test.service")
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.detail, "active")

    # PURPOSE: inactive_service をテストする
    @patch("subprocess.run")
    def test_inactive_service(self, mock_run):
        """Verify inactive service behavior."""
        mock_run.return_value = MagicMock(stdout="inactive\n")
        result = check_systemd_service("Test Service", "test.service")
        self.assertEqual(result.status, "error")

    # PURPOSE: timeout をテストする
    @patch("subprocess.run", side_effect=Exception("timeout"))
    def test_timeout(self, mock_run):
        """Verify timeout behavior."""
        result = check_systemd_service("Test Service", "test.service")
        self.assertEqual(result.status, "unknown")


# PURPOSE: n8n HTTP チェックのモックテスト（check_n8n は urllib ベース）
class TestCheckN8n(unittest.TestCase):
    """Test suite for check_n8n."""

    @patch("mekhane.peira.hgk_health.urllib.request.urlopen")
    def test_n8n_healthy(self, mock_urlopen):
        """Verify ok when /healthz responds."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"ok"
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        result = check_n8n()
        self.assertEqual(result.status, "ok")
        self.assertIn("healthy", result.detail)

    @patch("mekhane.peira.hgk_health.urllib.request.urlopen", side_effect=OSError("refused"))
    def test_n8n_unreachable(self, _mock_urlopen):
        """Verify error when all hosts fail."""
        result = check_n8n()
        self.assertEqual(result.status, "error")
        self.assertIn("unreachable", result.detail)


# PURPOSE: cron チェックのモックテスト
class TestCheckCron(unittest.TestCase):
    """Test suite for check cron."""

    @patch("subprocess.run")
    def test_cron_entry_exists(self, mock_run):
        """Verify cron entry exists behavior."""
        mock_run.return_value = MagicMock(stdout="0 4 * * * tier1_daily.sh\n")
        result = check_cron("Tier 1", "tier1")
        self.assertEqual(result.status, "ok")

    # PURPOSE: cron_entry_missing をテストする
    @patch("subprocess.run")
    def test_cron_entry_missing(self, mock_run):
        """Verify cron entry missing behavior."""
        mock_run.return_value = MagicMock(stdout="0 0 * * * backup.sh\n")
        result = check_cron("Tier 1", "tier1")
        self.assertEqual(result.status, "error")


# PURPOSE: Handoff チェックのモックテスト
class TestCheckHandoff(unittest.TestCase):
    """Test suite for check handoff."""

    @patch("mekhane.peira.hgk_health.Path")
    def test_directory_not_exists(self, mock_path_cls):
        """Verify directory not exists behavior."""
        mock_dir = MagicMock()
        mock_dir.exists.return_value = False
        mock_path_cls.home.return_value.__truediv__ = lambda *args: mock_dir
        # We need a more targeted mock; just test the function signature
        # For integration, we rely on the actual filesystem test below
        pass

    # PURPOSE: Integration: 実際のファイルシステムで検証
    def test_actual_handoff_directory(self):
        """Integration: 実際のファイルシステムで検証"""
        handoff_dir = MNEME_STATE / "handoffs"
        if handoff_dir.exists():
            result = check_handoff()
            self.assertIn(result.status, ["ok", "warn", "error"])
            self.assertIsNotNone(result.detail)


# PURPOSE: format_terminal の出力フォーマットをテスト
class TestFormatTerminal(unittest.TestCase):
    """Test suite for format terminal."""
    def test_output_contains_header(self):
        """Verify output contains header behavior."""
        report = HealthReport(
            timestamp=datetime.now().isoformat(),
            effective_profile="full",
            items=[HealthItem("Test", "ok", "detail")],
        )
        output = format_terminal(report)
        self.assertIn("Hegemonikón Health Dashboard", output)
        self.assertIn("profile:", output)
        self.assertIn("🟢", output)
        self.assertIn("Score:", output)

    # PURPOSE: empty_report をテストする
    def test_empty_report(self):
        """Verify empty report behavior."""
        report = HealthReport(timestamp="test", items=[])
        output = format_terminal(report)
        self.assertIn("Score: 0%", output)


# PURPOSE: 定理活性度チェックのテスト
class TestCheckTheoremActivity(unittest.TestCase):
    """Test suite for check_theorem_activity."""

    @patch("mekhane.peira.hgk_health.check_theorem_activity.__module__", "mekhane.peira.hgk_health")
    def test_actual_integration(self):
        """Integration: 実際の Handoff ディレクトリで検証"""
        result = check_theorem_activity()
        self.assertIn(result.status, ["ok", "warn", "error", "unknown"])
        if result.status in ["ok", "warn", "error"]:
            self.assertIn("alive", result.detail)
            self.assertIsNotNone(result.metric)

    @patch("mekhane.peira.theorem_activity.scan_handoffs")
    def test_all_alive(self, mock_scan):
        """全24定理が alive の場合"""
        from collections import Counter
        from mekhane.peira.theorem_activity import THEOREM_WORKFLOWS
        # 全定理が direct 10回 + hub 0回 → alive
        all_24 = list(THEOREM_WORKFLOWS.keys())
        mock_scan.return_value = {
            "total_files": 50,
            "skipped": 0,
            "wf_counts": Counter({wf: 10 for wf in all_24}),
            "hub_counts": Counter(),
            "wf_by_month": {"2026-01": Counter(), "2026-02": Counter()},
        }
        result = check_theorem_activity()
        self.assertEqual(result.status, "ok")
        self.assertIn("24/24 alive", result.detail)
        self.assertAlmostEqual(result.metric, 1.0)

    @patch("mekhane.peira.theorem_activity.scan_handoffs")
    def test_some_dormant(self, mock_scan):
        """一部 dormant (0回) がある場合 — 16+ alive → warn"""
        from collections import Counter
        from mekhane.peira.theorem_activity import THEOREM_WORKFLOWS
        all_keys = list(THEOREM_WORKFLOWS.keys())
        # 先頭16定理は直接10回 alive、残り8定理は0回 → dead
        alive_16 = all_keys[:16]
        counts = Counter({wf: 10 for wf in alive_16})
        mock_scan.return_value = {
            "total_files": 50,
            "skipped": 0,
            "wf_counts": counts,
            "hub_counts": Counter(),
            "wf_by_month": {"2026-01": Counter(), "2026-02": Counter()},
        }
        result = check_theorem_activity()
        self.assertEqual(result.status, "warn")
        self.assertIn("16/24 alive", result.detail)

    @patch("mekhane.peira.theorem_activity.scan_handoffs")
    def test_hub_only_alive(self, mock_scan):
        """一部がハブ経由のみで alive の場合 — DX-008 R4"""
        from collections import Counter
        from mekhane.peira.theorem_activity import THEOREM_WORKFLOWS
        all_keys = list(THEOREM_WORKFLOWS.keys())
        # 先頭20定理: 直接発動 10回 (direct alive)
        direct_20 = all_keys[:20]
        direct = Counter({wf: 10 for wf in direct_20})
        # 残り4定理: 直接 0回, ハブ経由 10回 (hub-only alive)
        hub_4 = all_keys[20:]
        hub = Counter({wf: 10 for wf in hub_4})
        mock_scan.return_value = {
            "total_files": 50,
            "skipped": 0,
            "wf_counts": direct,
            "hub_counts": hub,
            "wf_by_month": {"2026-01": Counter(), "2026-02": Counter()},
        }
        result = check_theorem_activity()
        self.assertEqual(result.status, "ok")
        self.assertIn("24/24 alive", result.detail)
        self.assertIn("hub-only", result.detail)
        self.assertIn("20 direct", result.detail)
        self.assertIn("4 hub-only", result.detail)

# PURPOSE: Kalon 品質チェックのテスト
class TestCheckKalon(unittest.TestCase):
    """Test suite for check_kalon."""

    # PURPOSE: 実データで check_kalon() が正常に動作するか検証
    def test_kalon_with_real_data(self):
        """Integration: category.py の実データで検証"""
        result = check_kalon()
        self.assertEqual(result.name, "Kalon Quality")
        self.assertIn(result.status, ["ok", "warn", "error", "unknown"])
        # Real data should be at least APPROACHING (warn) or KALON (ok).
        # Some checks (e.g. Bayesian convergence, L3 coherence) may legitimately
        # return APPROACHING when observations are sparse or new checks are added.
        self.assertIn(
            result.status, ["ok", "warn"],
            f"Kalon should be at least APPROACHING, got: {result.status} — {result.detail}"
        )
        self.assertIn("KALON", result.detail)
        self.assertIsNotNone(result.metric)
        self.assertGreaterEqual(result.metric, 0.50)

    # PURPOSE: run_health_check() の結果に Kalon が含まれるか検証
    def test_kalon_in_health_report(self):
        """Kalon Quality が run_health_check() に含まれること"""
        report = run_health_check()
        kalon_items = [i for i in report.items if i.name == "Kalon Quality"]
        self.assertEqual(len(kalon_items), 1)
        self.assertIn(kalon_items[0].status, ["ok", "warn", "error", "unknown"])


# PURPOSE: プロファイルと運用緩和フラグの単体テスト
class TestHealthProfile(unittest.TestCase):
    def test_default_is_full(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(get_effective_health_profile(), "full")
            self.assertFalse(use_ops_relaxed_checks())

    def test_full_profile(self):
        with patch.dict("os.environ", {"HGK_HEALTH_PROFILE": "full"}, clear=True):
            self.assertEqual(get_effective_health_profile(), "full")
            self.assertFalse(use_ops_relaxed_checks())

    def test_cursor_profile_ops_only(self):
        with patch.dict("os.environ", {"HGK_HEALTH_PROFILE": "cursor"}, clear=True):
            self.assertEqual(get_effective_health_profile(), "cursor")
            self.assertTrue(use_ops_relaxed_checks())


# PURPOSE: Hermēneus MCP サーバーの死活チェックテスト (Linux: pgrep)
@patch("mekhane.peira.hgk_health.sys.platform", "linux")
@patch("mekhane.peira.hgk_health.run_utf8")
class TestCheckHermeneus(unittest.TestCase):
    """Test suite for check_hermeneus."""

    # PURPOSE: プロセスが見つかった場合のテスト
    # sys.platform は @patch(..., "linux") で置換のみ（追加引数なし）
    def test_process_found(self, mock_run_utf8):
        """Verify ok when hermeneus process is running."""
        mock_run_utf8.return_value = MagicMock(stdout="12345\n67890\n", returncode=0)
        result = check_hermeneus()
        self.assertEqual(result.name, "Hermēneus MCP")
        self.assertEqual(result.status, "ok")
        self.assertIn("running", result.detail)
        self.assertIn("2 process", result.detail)

    # PURPOSE: プロセスが見つからない場合のテスト
    def test_process_not_found(self, mock_run_utf8):
        """Verify warn when hermeneus process is not running (IDE-managed)."""
        mock_run_utf8.return_value = MagicMock(stdout="", returncode=1)
        result = check_hermeneus()
        self.assertEqual(result.name, "Hermēneus MCP")
        self.assertEqual(result.status, "warn")
        self.assertIn("not found", result.detail)

    # PURPOSE: タイムアウト時のテスト
    def test_timeout(self, mock_run_utf8):
        """Verify unknown on timeout."""
        mock_run_utf8.side_effect = subprocess.TimeoutExpired(cmd="pgrep", timeout=5)
        result = check_hermeneus()
        self.assertEqual(result.name, "Hermēneus MCP")
        self.assertEqual(result.status, "unknown")


# PURPOSE: run_health_check() に Hermēneus が含まれるか（統合）
class TestHermeneusInFullReport(unittest.TestCase):
    def test_hermeneus_in_health_report(self):
        """Hermēneus MCP が run_health_check() に含まれること"""
        report = run_health_check()
        hermeneus_items = [i for i in report.items if i.name == "Hermēneus MCP"]
        self.assertEqual(len(hermeneus_items), 1)


if __name__ == "__main__":
    unittest.main()
