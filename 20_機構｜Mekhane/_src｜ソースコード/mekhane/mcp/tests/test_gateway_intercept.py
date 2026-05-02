#!/usr/bin/env python3
# PROOF: [L1/テスト] <- mekhane/mcp/tests/
# PURPOSE: V-011 Gateway Intercept (Prokataskeve Pre-flight) の単体テスト
"""
V-011 テスト — gateway_hooks._apply_prokataskeve

_apply_prokataskeve 関数を直接テストし、L0 正規化の適用、
スキップ条件、不変性を検証する。
"""

import sys
from pathlib import Path
from typing import Any, Sequence

import pytest
import asyncio

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# FastMCP Stub (mcp パッケージなしでテストするための軽量スタブ)
# =============================================================================

class _StubFastMCP:
    """mcp.server.fastmcp.FastMCP の軽量スタブ。"""
    def __init__(self, *args, **kwargs):
        pass

class _StubTextContent:
    """mcp.types.TextContent の軽量スタブ。"""
    def __init__(self, type: str = "text", text: str = ""):
        self.type = type
        self.text = text


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def _patch_imports(monkeypatch):
    """FastMCP + prokataskeve 単体ファイルを注入する。"""
    import types

    # 1. mcp スタブ
    mcp_mod = types.ModuleType("mcp")
    mcp_server_mod = types.ModuleType("mcp.server")
    mcp_fastmcp_mod = types.ModuleType("mcp.server.fastmcp")
    mcp_types_mod = types.ModuleType("mcp.types")
    mcp_fastmcp_mod.FastMCP = _StubFastMCP
    mcp_types_mod.TextContent = _StubTextContent
    mcp_mod.server = mcp_server_mod
    mcp_server_mod.fastmcp = mcp_fastmcp_mod
    mcp_mod.types = mcp_types_mod

    monkeypatch.setitem(sys.modules, "mcp", mcp_mod)
    monkeypatch.setitem(sys.modules, "mcp.server", mcp_server_mod)
    monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", mcp_fastmcp_mod)
    monkeypatch.setitem(sys.modules, "mcp.types", mcp_types_mod)

    # 2. prokataskeve 単体ファイルを sys.modules に注入
    import importlib.util
    _single = Path(__file__).resolve().parent.parent / "prokataskeve.py"
    if _single.exists():
        _spec = importlib.util.spec_from_file_location(
            "mekhane.mcp.prokataskeve", str(_single),
        )
        if _spec and _spec.loader:
            _mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            monkeypatch.setitem(sys.modules, "mekhane.mcp.prokataskeve", _mod)

    # 3. 他のフック無効化
    monkeypatch.setenv("HGK_PROSTASIA_ENABLED", "0")
    monkeypatch.setenv("HGK_SEKISHO_ENABLED", "0")
    monkeypatch.setenv("HGK_QUALITY_GATE_ENABLED", "0")
    monkeypatch.setenv("HGK_PROKATASKEVE_ENABLED", "1")


# =============================================================================
# Tests: _apply_prokataskeve
# =============================================================================

class TestApplyProkataskeve:
    """_apply_prokataskeve 関数の単体テスト (8 件)。"""

    def test_normalizes_fullwidth(self):
        async def _impl():
            """全角英数字が半角に正規化される。"""
            from mekhane.mcp.gateway_hooks import _apply_prokataskeve
            args = {"message": "ＡＢＣ　ＤＥＦ　テスト入力です"}
            result = await _apply_prokataskeve("hgk_ask", args)
            assert result["message"] != args["message"], "全角は正規化されるべき"
            assert "ABC" in result["message"], "半角 ABC に変換されるべき"
        asyncio.run(_impl())

    def test_skips_short_text(self):
        async def _impl():
            """10文字未満のテキストはスキップされる。"""
            from mekhane.mcp.gateway_hooks import _apply_prokataskeve
            args = {"message": "short"}
            result = await _apply_prokataskeve("hgk_ask", args)
            assert result is args, "短いテキストは元の引数を返すべき"
        asyncio.run(_impl())

    def test_skips_excluded_tools(self):
        async def _impl():
            """除外ツールは前処理をスキップする。"""
            from mekhane.mcp.gateway_hooks import _apply_prokataskeve
            args = {"message": "ＡＢＣ　ＤＥＦ　テスト入力です"}
            result = await _apply_prokataskeve("prokataskeve_preprocess", args)
            assert result is args, "除外ツールは元の引数を返すべき"
        asyncio.run(_impl())

    def test_skips_non_text_args(self):
        async def _impl():
            """テキストフィールドのない引数はスキップされる。"""
            from mekhane.mcp.gateway_hooks import _apply_prokataskeve
            args = {"timeout": 30, "depth": "L1"}
            result = await _apply_prokataskeve("hgk_ask", args)
            assert result is args, "テキストフィールドなしは元の引数を返すべき"
        asyncio.run(_impl())

    def test_preserves_non_text_fields(self):
        async def _impl():
            """テキスト以外のフィールドは変更されない。"""
            from mekhane.mcp.gateway_hooks import _apply_prokataskeve
            args = {"message": "ＡＢＣ　テスト入力です", "timeout": 30, "depth": "L1"}
            result = await _apply_prokataskeve("hgk_ask", args)
            assert result["timeout"] == 30
            assert result["depth"] == "L1"
        asyncio.run(_impl())

    def test_does_not_mutate_original(self):
        async def _impl():
            """元の arguments dict を変更しない (shallow copy)。"""
            from mekhane.mcp.gateway_hooks import _apply_prokataskeve
            args = {"message": "ＡＢＣ　テスト入力です"}
            original_msg = args["message"]
            result = await _apply_prokataskeve("hgk_ask", args)
            assert args["message"] == original_msg, "元の dict は変更されないべき"
            assert result is not args, "新しい dict が返されるべき"
        asyncio.run(_impl())

    def test_multiple_text_fields(self):
        async def _impl():
            """複数のテキストフィールドが全て正規化される。"""
            from mekhane.mcp.gateway_hooks import _apply_prokataskeve
            args = {"message": "ＡＢＣ　テスト入力です", "context": "ＸＹＺ　コンテキスト"}
            result = await _apply_prokataskeve("hgk_ask", args)
            assert "ABC" in result["message"]
            assert "XYZ" in result["context"]
        asyncio.run(_impl())

    def test_ccl_preserved(self):
        async def _impl():
            """CCL パターンが正規化後も保存される。"""
            from mekhane.mcp.gateway_hooks import _apply_prokataskeve
            args = {"message": "/noe+ を実行してください"}
            result = await _apply_prokataskeve("hgk_ask", args)
            assert "/noe+" in result["message"], "CCL パターンは保存されるべき"
        asyncio.run(_impl())
