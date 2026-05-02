#!/usr/bin/env python3
# PROOF: [L1/テスト] <- mekhane/mcp/tests/
# PURPOSE: V-011 品質ゲートの単体テスト
"""
L1 テスト — quality_gate.py

サーバーを起動せず、品質ゲートのリスク判定ロジック + ゲート実行結果を検証する。
LLM 呼出しはモックで置き換え。
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# Risk Assessment Tests
# =============================================================================

class TestAssessRisk:
    """assess_risk() のリスク判定ロジックをテスト。"""

    def test_low_risk_readonly_tools(self):
        """読取専用ツールが LOW と判定される。"""
        from mekhane.mcp.quality_gate import assess_risk, RiskLevel

        for tool in ["sekisho_ping", "hgk_health", "hgk_status", "hgk_doxa_read"]:
            result = assess_risk(tool)
            assert result == RiskLevel.LOW, f"{tool} should be LOW, got {result}"

    def test_medium_risk_execution_tools(self):
        """実行系ツールが MEDIUM と判定される。"""
        from mekhane.mcp.quality_gate import assess_risk, RiskLevel

        for tool in ["write_to_file", "replace_file_content", "run_command",
                      "hermeneus_run", "hgk_ccl_execute"]:
            result = assess_risk(tool)
            assert result == RiskLevel.MEDIUM, f"{tool} should be MEDIUM, got {result}"

    def test_high_risk_notify_user(self):
        """notify_user が HIGH と判定される。"""
        from mekhane.mcp.quality_gate import assess_risk, RiskLevel

        result = assess_risk("notify_user")
        assert result == RiskLevel.HIGH

    def test_excluded_tools_are_low(self):
        """除外ツールが LOW と判定される。"""
        from mekhane.mcp.quality_gate import assess_risk, RiskLevel

        result = assess_risk("sekisho_audit")
        assert result == RiskLevel.LOW

    def test_unknown_tools_default_to_low(self):
        """未知のツールがデフォルトで LOW と判定される。"""
        from mekhane.mcp.quality_gate import assess_risk, RiskLevel

        result = assess_risk("some_unknown_tool_xyz")
        assert result == RiskLevel.LOW

    def test_unaudited_escalation_to_medium(self):
        """連続未監査数が閾値を超えると MEDIUM に昇格する。"""
        from mekhane.mcp.quality_gate import assess_risk, RiskLevel

        # 未知ツール + 連続未監査15 → MEDIUM
        context = {"consecutive_unaudited": 15}
        result = assess_risk("some_unknown_tool", session_context=context)
        assert result == RiskLevel.MEDIUM

    def test_periodic_audit_interval(self):
        """定期監査間隔で MEDIUM に昇格する。"""
        from mekhane.mcp.quality_gate import assess_risk, RiskLevel

        # 未知ツール + 10ツール目 → MEDIUM
        context = {"total_tool_calls": 10}
        result = assess_risk("some_unknown_tool", session_context=context)
        assert result == RiskLevel.MEDIUM

    def test_disabled_policy_always_low(self):
        """ポリシーが無効の場合、常に LOW を返す。"""
        from mekhane.mcp.quality_gate import assess_risk, RiskLevel, _load_quality_gate_policy
        import mekhane.mcp.quality_gate as qg

        # ポリシーキャッシュを一時的に上書き
        original = qg._policy_cache
        qg._policy_cache = {"enabled": False}
        try:
            result = assess_risk("notify_user")  # 通常は HIGH
            assert result == RiskLevel.LOW
        finally:
            qg._policy_cache = original


# =============================================================================
# Gate Execution Tests (モック)
# =============================================================================

class TestExecuteQualityGate:
    """execute_quality_gate() の統合テスト (LLM はモック)。"""

    def test_low_risk_skips_all_gates(self):
        """LOW リスクでは L1/L2 が実行されない。"""
        from mekhane.mcp.quality_gate import execute_quality_gate

        result = execute_quality_gate(
            tool_name="sekisho_ping",
            arguments={},
            response_text="pong",
        )
        assert result["risk_level"] == "low"
        assert result["l1_result"] is None
        assert result["l2_result"] is None
        assert result["overall_verdict"] == "PASS"

    @patch("mekhane.mcp.quality_gate.run_l1_gate")
    def test_medium_risk_runs_l1_only(self, mock_l1):
        """MEDIUM リスクでは L1 のみ実行される。"""
        from mekhane.mcp.quality_gate import execute_quality_gate

        mock_l1.return_value = {
            "verdict": "PASS",
            "overall_score": 0.9,
            "confidence": 0.8,
            "violations": [],
        }

        result = execute_quality_gate(
            tool_name="write_to_file",
            arguments={"TargetFile": "/tmp/test.py"},
            response_text="Created file test.py",
        )
        assert result["risk_level"] == "medium"
        assert result["l1_result"] is not None
        assert result["l2_result"] is None
        assert result["overall_verdict"] == "PASS"
        mock_l1.assert_called_once()

    @patch("mekhane.mcp.quality_gate.run_l2_gate")
    @patch("mekhane.mcp.quality_gate.run_l1_gate")
    def test_high_risk_runs_l1_and_l2(self, mock_l1, mock_l2):
        """HIGH リスクでは L1 と L2 の両方が実行される。"""
        from mekhane.mcp.quality_gate import execute_quality_gate

        mock_l1.return_value = {
            "verdict": "PASS",
            "overall_score": 0.85,
            "confidence": 0.8,
            "violations": [],
        }
        mock_l2.return_value = {
            "verdict": "PASS",
            "confidence": 0.8,
        }

        result = execute_quality_gate(
            tool_name="notify_user",
            arguments={"Message": "Done"},
            response_text="Task completed successfully",
        )
        assert result["risk_level"] == "high"
        assert result["l1_result"] is not None
        assert result["l2_result"] is not None
        assert result["overall_verdict"] == "PASS"
        mock_l1.assert_called_once()
        mock_l2.assert_called_once()

    @patch("mekhane.mcp.quality_gate.run_l1_gate")
    def test_l1_block_stops_pipeline(self, mock_l1):
        """L1 が BLOCK を返した場合、L2 は実行されない。"""
        from mekhane.mcp.quality_gate import execute_quality_gate

        mock_l1.return_value = {
            "verdict": "BLOCK",
            "violations": [{"bc_id": "N-3", "reason": "確信度偽装"}],
            "suggestions": "確信度を [推定] に変更してください",
            "confidence": 0.9,
        }

        result = execute_quality_gate(
            tool_name="notify_user",
            arguments={"Message": "Done"},
            response_text="This is definitely correct",
        )
        assert result["overall_verdict"] == "BLOCK"
        assert result["l2_result"] is None  # L1 BLOCK → L2 スキップ
        assert "確信度" in result["block_reason"]


# =============================================================================
# Format Tests
# =============================================================================

class TestFormatGateResult:
    """format_gate_result() の出力フォーマットをテスト。"""

    def test_low_risk_returns_none(self):
        """LOW リスクの PASS は None を返す (応答に追加しない)。"""
        from mekhane.mcp.quality_gate import format_gate_result

        result = format_gate_result({
            "risk_level": "low",
            "overall_verdict": "PASS",
            "l1_result": None,
            "l2_result": None,
            "block_reason": None,
            "elapsed_ms": 1.0,
        })
        assert result is None

    def test_block_returns_formatted_text(self):
        """BLOCK 時は差し止め指示テキストを返す。"""
        from mekhane.mcp.quality_gate import format_gate_result

        result = format_gate_result({
            "risk_level": "high",
            "overall_verdict": "BLOCK",
            "l1_result": {
                "violations": [{"bc_id": "N-3", "reason": "確信度偽装"}],
            },
            "l2_result": None,
            "block_reason": "L1 BC 監査で違反検出",
            "elapsed_ms": 15000.0,
        })
        assert result is not None
        assert "QUALITY GATE" in result
        assert "差し止め" in result
        assert "N-3" in result

    def test_medium_pass_with_score(self):
        """MEDIUM PASS でスコアが表示される。"""
        from mekhane.mcp.quality_gate import format_gate_result

        result = format_gate_result({
            "risk_level": "medium",
            "overall_verdict": "PASS",
            "l1_result": {"overall_score": 0.92, "confidence": 0.85},
            "l2_result": None,
            "block_reason": None,
            "elapsed_ms": 12000.0,
        })
        assert result is not None
        assert "QG" in result
        assert "0.92" in result


# =============================================================================
# Policy Tests
# =============================================================================

class TestPolicyLoading:
    """gateway_policy.yaml の読込テスト。"""

    def test_policy_loads_without_error(self):
        """ポリシーがエラーなく読み込める。"""
        import mekhane.mcp.quality_gate as qg
        qg._policy_cache = None  # キャッシュをクリア
        policy = qg._load_quality_gate_policy()
        assert policy is not None
        assert "enabled" in policy
        assert isinstance(policy.get("high_risk_tools", []), list)

    def test_default_policy_fallback(self):
        """YAML が見つからない場合、デフォルトポリシーにフォールバックする。"""
        from mekhane.mcp.quality_gate import _DEFAULT_POLICY
        assert "notify_user" in _DEFAULT_POLICY["high_risk_tools"]
        assert "write_to_file" in _DEFAULT_POLICY["medium_risk_tools"]
        assert "sekisho_ping" in _DEFAULT_POLICY["excluded_tools"]


# =============================================================================
# Runner
# =============================================================================

if __name__ == "__main__":
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-q",
    ])
    sys.exit(exit_code)
