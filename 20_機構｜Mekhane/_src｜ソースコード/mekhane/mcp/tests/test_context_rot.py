#!/usr/bin/env python3
# PROOF: [L2/テスト] <- mekhane/mcp/tests/ V-003 Context Rot テスト
"""
Tests for V-003 Context Rot: rom_distiller + context_rot tools.
"""
import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest


# =============================================================================
# rom_distiller tests
# =============================================================================


class TestAssessHealth:
    """assess_health の健全度判定テスト。"""

    def test_green(self):
        from mekhane.mcp.rom_distiller import assess_health
        result = assess_health(10)
        assert result["health"] == "green"
        assert result["step_count"] == 10

    def test_yellow(self):
        from mekhane.mcp.rom_distiller import assess_health
        result = assess_health(35)
        assert result["health"] == "yellow"
        assert "/rom" in result["recommendation"]

    def test_orange(self):
        from mekhane.mcp.rom_distiller import assess_health
        result = assess_health(45)
        assert result["health"] == "orange"
        assert "/rom+" in result["recommendation"]

    def test_red(self):
        from mekhane.mcp.rom_distiller import assess_health
        result = assess_health(55)
        assert result["health"] == "red"
        assert "/bye" in result["recommendation"]

    def test_zero(self):
        from mekhane.mcp.rom_distiller import assess_health
        result = assess_health(0)
        assert result["health"] == "green"

    def test_boundary_30(self):
        from mekhane.mcp.rom_distiller import assess_health
        assert assess_health(30)["health"] == "green"
        assert assess_health(31)["health"] == "yellow"


class TestClassifyContent:
    """classify_content のヒューリスティック分類テスト。"""

    def test_decision_detection(self):
        from mekhane.mcp.rom_distiller import classify_content
        conversation = [
            {"author": 2, "content": "V-001 の設計方針を確定した。18関数に拡張する。"},
        ]
        items = classify_content(conversation)
        assert any(i["category"] == "DECISION" for i in items)

    def test_discovery_detection(self):
        from mekhane.mcp.rom_distiller import classify_content
        conversation = [
            {"author": 2, "content": "ベンチマーク結果: L0 は 0.1ms で目標の 500倍余裕がある。"},
        ]
        items = classify_content(conversation)
        assert any(i["category"] == "DISCOVERY" for i in items)

    def test_artifact_detection(self):
        from mekhane.mcp.rom_distiller import classify_content
        conversation = [
            {"author": 2, "content": "rom_distiller.py を作成した。66 テスト PASSED。"},
        ]
        items = classify_content(conversation)
        assert any(i["category"] == "ARTIFACT" for i in items)

    def test_failure_detection(self):
        from mekhane.mcp.rom_distiller import classify_content
        conversation = [
            {"author": 2, "content": "mockのside_effect順序がずれてエラーになった。修正した。"},
        ]
        items = classify_content(conversation)
        assert any(i["category"] == "FAILURE" for i in items)

    def test_empty_conversation(self):
        from mekhane.mcp.rom_distiller import classify_content
        items = classify_content([])
        assert items == []

    def test_system_messages_skipped(self):
        from mekhane.mcp.rom_distiller import classify_content
        conversation = [
            {"author": 0, "content": "system message with 確定"},
        ]
        items = classify_content(conversation)
        assert items == []


class TestDistill:
    """distill テンプレート適用テスト。"""

    def test_basic_distillation(self):
        from mekhane.mcp.rom_distiller import distill
        items = [
            {"category": "DECISION", "content": "18関数に拡張", "importance": "high"},
            {"category": "DISCOVERY", "content": "L0 は 0.1ms", "importance": "high"},
        ]
        result = distill(
            conversation=[{"author": 2, "content": "test"}],
            classified_items=items,
            topic="v001_pipeline",
            session_id="test-session",
        )
        assert "rom_id:" in result
        assert "18関数に拡張" in result
        assert "L0 は 0.1ms" in result
        assert "rom_type: rag_optimized" in result

    def test_empty_items(self):
        from mekhane.mcp.rom_distiller import distill
        result = distill(
            conversation=[],
            classified_items=[],
            topic="empty_test",
        )
        assert "rom_id:" in result
        assert "なし" in result

    def test_auto_topic_from_decision(self):
        from mekhane.mcp.rom_distiller import distill
        items = [
            {"category": "DECISION", "content": "プレウォームをスキップ", "importance": "high"},
        ]
        result = distill(
            conversation=[{"author": 2, "content": "test"}],
            classified_items=items,
        )
        assert "rom_id:" in result


class TestWriteRom:
    """write_rom ファイル保存テスト。"""

    def test_write_creates_file(self):
        from mekhane.mcp.rom_distiller import write_rom
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mekhane.mcp.rom_distiller.ROM_DIR", Path(tmpdir)):
                path = write_rom("# Test ROM\nContent here.", topic="test_rom")
                assert path.exists()
                assert "test_rom" in path.name
                content = path.read_text()
                assert "# Test ROM" in content

    def test_write_avoids_collision(self):
        from mekhane.mcp.rom_distiller import write_rom
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mekhane.mcp.rom_distiller.ROM_DIR", Path(tmpdir)):
                path1 = write_rom("Content 1", topic="collision")
                path2 = write_rom("Content 2", topic="collision")
                assert path1 != path2
                assert path1.exists()
                assert path2.exists()


class TestQualityCheck:
    """quality_check 品質メトリクステスト。"""

    def test_high_quality(self):
        from mekhane.mcp.rom_distiller import quality_check
        items = [
            {"category": "DECISION", "content": "test", "importance": "high"},
            {"category": "DISCOVERY", "content": "test", "importance": "high"},
        ]
        rom_content = "---\nrom_type: rag_optimized\ntopics: [test]\n---\n# Test"
        result = quality_check(rom_content, original_tokens=1000, classified_items=items)
        assert result["quality_verdict"] == "PASS"
        assert result["decisions_preserved"] == 1
        assert result["compression_ratio"] < 1.0

    def test_low_quality(self):
        from mekhane.mcp.rom_distiller import quality_check
        result = quality_check("short", original_tokens=10, classified_items=[])
        assert result["quality_verdict"] in ("MARGINAL", "FAIL")


class TestRunDistillation:
    """run_distillation 統合テスト。"""

    def test_full_pipeline(self):
        from mekhane.mcp.rom_distiller import run_distillation
        conversation = [
            {"author": 1, "content": "V-001の設計方針を確定して"},
            {"author": 2, "content": "V-001 の設計方針を確定した。18関数に拡張する決定をした。"},
            {"author": 1, "content": "ベンチマーク結果は？"},
            {"author": 2, "content": "ベンチマーク結果: L0 は 0.1ms で目標内。66テスト PASSED。"},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mekhane.mcp.rom_distiller.ROM_DIR", Path(tmpdir)):
                result = run_distillation(
                    topic="v001_benchmark",
                    conversation=conversation,
                )
                assert result["rom_path"]
                assert Path(result["rom_path"]).exists()
                assert result["quality"]["quality_verdict"] in ("PASS", "MARGINAL")
                assert result["health_after"]["health"] == "green"
                assert result["items_classified"] > 0

    def test_empty_conversation(self):
        from mekhane.mcp.rom_distiller import run_distillation
        result = run_distillation(conversation=[])
        assert "error" in result


# =============================================================================
# context_rot tool tests
# =============================================================================


class TestContextRotStatus:
    """context_rot_status ツールのテスト。"""

    def test_returns_health(self):
        async def _impl():
            from mekhane.mcp.context_rot import context_rot_status
            with patch("mekhane.ochema.antigravity_client.AntigravityClient") as MockClient:
                mock_instance = MagicMock()
                mock_instance.session_info.return_value = {
                    "sessions": [{"step_count": 25, "cascade_id": "test-123"}]
                }
                MockClient.return_value = mock_instance

                result = await context_rot_status()
                assert result["health"] == "green"
                assert result["step_count"] == 25
        asyncio.run(_impl())

    def test_returns_yellow_on_high_steps(self):
        async def _impl():
            from mekhane.mcp.context_rot import context_rot_status
            with patch("mekhane.ochema.antigravity_client.AntigravityClient") as MockClient:
                mock_instance = MagicMock()
                mock_instance.session_info.return_value = {
                    "sessions": [{"step_count": 38, "cascade_id": "test-456"}]
                }
                MockClient.return_value = mock_instance

                result = await context_rot_status()
                assert result["health"] == "yellow"
        asyncio.run(_impl())

    def test_fallback_on_error(self):
        async def _impl():
            from mekhane.mcp.context_rot import context_rot_status
            with patch("mekhane.ochema.antigravity_client.AntigravityClient", side_effect=Exception("no LS")):
                result = await context_rot_status()
                assert result["health"] == "green"
                assert result["step_count"] == 0
        asyncio.run(_impl())


class TestEvacuationUrgency:
    """evacuation_urgency マッピングのテスト。"""

    def test_green_is_none(self):
        from mekhane.mcp.rom_distiller import assess_health
        result = assess_health(10)
        assert result["evacuation_urgency"] == "none"

    def test_yellow_is_advisory(self):
        from mekhane.mcp.rom_distiller import assess_health
        result = assess_health(35)
        assert result["evacuation_urgency"] == "advisory"

    def test_orange_is_mandatory(self):
        from mekhane.mcp.rom_distiller import assess_health
        result = assess_health(45)
        assert result["evacuation_urgency"] == "mandatory"

    def test_red_is_critical(self):
        from mekhane.mcp.rom_distiller import assess_health
        result = assess_health(55)
        assert result["evacuation_urgency"] == "critical"


class TestEvacuationNotification:
    """Pre-Evacuation 通知のテスト。"""

    def test_notification_sent_on_orange(self):
        async def _impl():
            import sys
            mock_ac_module = MagicMock()
            mock_client_instance = MagicMock()
            mock_client_instance.session_info.return_value = {
                "sessions": [{"step_count": 45, "cascade_id": "test-orange"}]
            }
            mock_ac_module.AntigravityClient.return_value = mock_client_instance
            with patch.dict(sys.modules, {"mekhane.ochema.antigravity_client": mock_ac_module}):
                from mekhane.mcp.context_rot import context_rot_status
                with patch("mekhane.mcp.context_rot._send_evacuation_notification") as mock_notify:
                    mock_notify.return_value = True
                    result = await context_rot_status()
                    assert result["health"] == "orange"
                    assert result["notification_sent"] is True
                    mock_notify.assert_called_once()
        asyncio.run(_impl())

    def test_no_notification_on_green(self):
        async def _impl():
            import sys
            mock_ac_module = MagicMock()
            mock_client_instance = MagicMock()
            mock_client_instance.session_info.return_value = {
                "sessions": [{"step_count": 10, "cascade_id": "test-green"}]
            }
            mock_ac_module.AntigravityClient.return_value = mock_client_instance
            with patch.dict(sys.modules, {"mekhane.ochema.antigravity_client": mock_ac_module}):
                from mekhane.mcp.context_rot import context_rot_status
                with patch("mekhane.mcp.context_rot._send_evacuation_notification") as mock_notify:
                    result = await context_rot_status()
                    assert result["health"] == "green"
                    assert result["notification_sent"] is False
                    mock_notify.assert_not_called()
        asyncio.run(_impl())

    def test_send_evacuation_notification_writes_file(self):
        async def _impl():
            from mekhane.mcp.context_rot import _send_evacuation_notification
            import json
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch("mekhane.mcp.context_rot.os.getenv", return_value=tmpdir):
                    # Patch the path construction
                    with patch.object(
                        Path, '__new__',
                        side_effect=lambda cls, *args: Path.__new__(cls, *args)
                    ):
                        pass
                # Direct test of the helper
                with patch.dict(os.environ, {"HGK_SYMPATHEIA_DIR": tmpdir}):
                    result = await _send_evacuation_notification(
                        health="orange",
                        urgency="mandatory",
                        step_count=45,
                    )
                    assert result is True
                    notif_file = Path(tmpdir) / "notifications.jsonl"
                    assert notif_file.exists()
                    line = notif_file.read_text().strip()
                    data = json.loads(line)
                    assert data["level"] == "HIGH"
                    assert "orange" in data["title"].lower()
                    assert data["source"] == "context_rot"
        asyncio.run(_impl())
