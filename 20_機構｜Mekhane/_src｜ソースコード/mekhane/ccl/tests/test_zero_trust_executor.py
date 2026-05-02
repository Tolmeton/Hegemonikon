#!/usr/bin/env python3
# PROOF: [L2/テスト] <- mekhane/ccl/tests/
# PURPOSE: Zero-Trust CCL Executor の contract enforcement テスト
"""Zero-Trust CCL Executor Tests"""

import pytest

from mekhane.ccl.executor import ZeroTrustCCLExecutor
from mekhane.ccl.workflow_signature import EnforcementLevel


class TestZeroTrustCCLExecutor:
    """Zero-Trust executor contract enforcement tests."""

    @pytest.fixture
    def executor(self):
        """Return a fresh executor."""
        return ZeroTrustCCLExecutor()

    def test_prepare_builds_manifest_for_multi_skill(self, executor):
        """H1 should build manifest and trace for expanded multi-skill CCL."""
        context = executor.prepare("/bou_/ene")
        assert context.raw_expr == "/bou_/ene"
        assert context.expanded_expr == "/bou_/ene"
        assert context.workflow_count == 2
        assert context.enforcement_level == EnforcementLevel.MULTI
        assert context.execution_manifest["workflow_list"] == ["/bou", "/ene"]
        assert context.contract_trace["workflow_count"] == 2

    def test_prepare_blocks_unresolved_macro(self, executor):
        """Unresolved macro should produce CCL CONTRACT BLOCKED preflight."""
        context = executor.prepare("@unknown_macro")
        assert context.execution_manifest["blocked"] is True
        assert "CCL CONTRACT BLOCKED" in context.injected_prompt

    def test_execute_marks_gate_violation_and_mixing(self, executor):
        """Multi-skill CCL should fail closed on skipped interactive gate."""
        result = executor.execute(
            "/bou_/ene",
            "/ene 実行計画\n次アクション\n1. 実保存\n2. 判定",
            record=False,
        )
        assert result.success is False
        assert result.validation.blocked is True
        error_types = [error.error_type for error in result.validation.errors]
        assert "interactive gate violation" in error_types
        assert "責務混入" in error_types
        trace = {item["name"]: item for item in result.contract_trace["workflows"]}
        assert trace["/bou"]["gate_status"] == "violated"
        assert trace["/ene"]["validation_status"] == "failed"

    def test_execute_allows_waiting_output_for_interactive_chain(self, executor):
        """Interactive gate should allow waiting output without forcing downstream completion."""
        result = executor.execute(
            "/bou_/ene",
            "P-0\n反応待ち\nCreator の反応を待つ",
            record=False,
        )
        assert result.success is True
        trace = {item["name"]: item for item in result.contract_trace["workflows"]}
        assert trace["/bou"]["gate_status"] == "pending_creator"
        assert trace["/ene"]["phase_status"] == "pending"

    def test_complex_chain_adds_runtime_stages(self, executor):
        """4+ workflow CCL should expose plan/execution/verification stages."""
        result = executor.execute(
            "/noe_/bou_/ene_/dia",
            "/ene 実行計画\n次アクション\n1. 実保存\n2. 判定",
            record=False,
        )
        assert result.context.enforcement_level == EnforcementLevel.COMPLEX
        assert result.success is False
        assert result.contract_trace["stages"]["plan"] == "completed"
        assert result.contract_trace["stages"]["execution"] == "completed"
        assert result.contract_trace["stages"]["verification"] == "invalid"
