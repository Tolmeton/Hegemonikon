# PROOF: mekhane/tests/test_service_tool_loop_phase0.py
# PURPOSE: DeerFlow Phase 0 — D1 ミドルウェア・ブリッジ整形の単体検証
"""Tests for Phase 0 middleware and OpenAI-compat bridge formatting."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest


def test_d1_clarification_middleware_interrupts_on_missing_info_keyword():
    from mekhane.ochema.phase0_middleware import D1ClarificationMiddleware

    mw = D1ClarificationMiddleware()
    act = mw.before_tool_call({"name": "run_cmd", "args": {"reason": "情報不足のため停止"}})
    assert act.interrupt is True
    assert act.reason == "clarification_needed"
    assert act.interrupt_message


def test_format_phase0_bridge_epoche_json():
    from mekhane.ochema.epoche_report import build_max_iterations_epoche_response
    from mekhane.ochema.openai_compat_server import _format_phase0_bridge_content

    r = build_max_iterations_epoche_response(
        max_iterations=2,
        last_tool_calls=[{"name": "noop", "args": {}}],
        total_usage={"total_tokens": 1},
        model="m",
    )
    out = _format_phase0_bridge_content(r)
    assert "Phase 0" in out
    assert "pending" in out.lower() or "Pending" in out
    assert "noop" in out


def test_format_phase0_bridge_plain_text_with_pending():
    from mekhane.ochema.openai_compat_server import _format_phase0_bridge_content
    from mekhane.ochema.types import LLMResponse

    r = LLMResponse(
        text="ユーザーへの説明",
        model="m",
        token_usage={},
        pending_synthesis=[{"name": "t", "args": {}}],
    )
    out = _format_phase0_bridge_content(r)
    assert "Clarification" in out or "Pending" in out
    assert "ユーザーへの説明" in out


def test_phase0_mcp_hook_interrupts_before_inner_handler():
    pytest.importorskip("mcp.types")
    from mcp.types import CallToolRequest, CallToolResult, TextContent

    from mekhane.mcp.mcp_base import MCPBase

    base = MCPBase("test_phase0", "0.0.1", "test")

    inner = AsyncMock(
        return_value=CallToolResult(
            content=[TextContent(type="text", text="should not run")],
        )
    )
    base.server.request_handlers[CallToolRequest] = inner
    base.install_phase0_hook()
    handler = base.server.request_handlers[CallToolRequest]
    req = MagicMock()
    req.params = MagicMock()
    req.params.name = "demo"
    req.params.arguments = {"x": "情報不足"}

    async def _run():
        return await handler(req)

    result = asyncio.run(_run())
    inner.assert_not_awaited()
    texts = [c.text for c in result.content if getattr(c, "type", "") == "text"]
    assert any("情報不足" in t or "明確化" in t for t in texts)
