# PROOF: mekhane/tests/test_thambos_hook.py
# PURPOSE: N-6 Thambos フックと install_all_hooks 順序
"""Tests for Thambos ambiguity hook in mcp_base."""

import ast
import asyncio
import inspect
import textwrap
from unittest.mock import AsyncMock, MagicMock

import pytest


def test_thambos_scan_empty():
    from mekhane.mcp.mcp_base import _thambos_scan_response_text

    assert _thambos_scan_response_text("") == ""
    assert _thambos_scan_response_text("   ") == ""


def test_thambos_scan_detects_japanese_missing_info():
    from mekhane.mcp.mcp_base import _thambos_scan_response_text

    out = _thambos_scan_response_text("情報不足のため続行できません")
    assert "Thambos" in out
    assert "heuristic" in out
    assert "情報不足の兆候" in out
    assert '"情報不足"' in out  # matched phrase as evidence


def test_thambos_scan_detects_english_ambiguous():
    from mekhane.mcp.mcp_base import _thambos_scan_response_text

    out = _thambos_scan_response_text("The requirements are ambiguous; please clarify.")
    assert "曖昧性の兆候" in out
    assert '"ambiguous"' in out  # matched phrase quoted as evidence


def test_thambos_scan_clean_result():
    from mekhane.mcp.mcp_base import _thambos_scan_response_text

    assert _thambos_scan_response_text("Status: OK. 42 files indexed.") == ""


def test_install_all_hooks_invokes_thambos_first():
    """install_all_hooks 本文で install_thambos が他より先に呼ばれること。"""
    from mekhane.mcp import mcp_base

    src = textwrap.dedent(inspect.getsource(mcp_base.MCPBase.install_all_hooks))
    tree = ast.parse(src)
    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr.startswith("install_"):
                calls.append(node.func.attr)
    assert calls[0] == "install_thambos_hook"
    assert "install_prostasia_hook" in calls


def test_thambos_hook_appends_warning():
    pytest.importorskip("mcp.types")
    from mcp.types import CallToolRequest, CallToolResult, TextContent

    from mekhane.mcp.mcp_base import MCPBase

    base = MCPBase("test_thambos", "0.0.1", "test")

    async def _inner(req: CallToolRequest):
        return CallToolResult(
            content=[TextContent(type="text", text="情報不足です")],
        )

    base.server.request_handlers[CallToolRequest] = _inner
    base.install_thambos_hook()

    handler = base.server.request_handlers[CallToolRequest]
    req = MagicMock()
    req.params = MagicMock()
    req.params.name = "demo_tool"
    req.params.arguments = {}

    async def _run():
        return await handler(req)

    result = asyncio.run(_run())
    texts = [c.text for c in result.content if getattr(c, "type", "") == "text"]
    assert any("情報不足" in t for t in texts)
    assert any("Thambos" in t for t in texts)


def test_existing_inner_hook_preserved():
    """Thambos が内側ハンドラを呼び結果を返すこと。"""
    pytest.importorskip("mcp.types")
    from mcp.types import CallToolRequest, CallToolResult, TextContent

    from mekhane.mcp.mcp_base import MCPBase

    base = MCPBase("test_thambos2", "0.0.1", "test")
    inner = AsyncMock(
        return_value=CallToolResult(
            content=[TextContent(type="text", text="plain ok")],
        )
    )
    base.server.request_handlers[CallToolRequest] = inner
    base.install_thambos_hook()
    handler = base.server.request_handlers[CallToolRequest]
    req = MagicMock()
    req.params = MagicMock()
    req.params.name = "x"
    req.params.arguments = {}

    async def _run():
        await handler(req)

    asyncio.run(_run())
    inner.assert_awaited_once()
