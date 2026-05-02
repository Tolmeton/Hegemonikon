# PROOF: mekhane/mcp/gateway_tools/sekisho.py
# PURPOSE: Daimonion γ (Akribeia) — 精密監査ツール (旧 Sekisho gateway)
# NOTE: v3 — Daimonion 統合。sekisho バックエンドは γ モードとして残存。
#   関数名は後方互換のため sekisho_* を維持しつつ、docstring で Daimonion γ を明示。
"""Gateway tools: sekisho domain (= Daimonion γ backend).

関数はモジュールレベルに定義し、register_sekisho_tools(mcp) で MCP 登録のみ行う。
mcp.client.* は関数内で遅延 import し、mcp パッケージ未インストール環境でも
モジュール自体の import は成功する。
"""
import os
import sys
import json
import asyncio
from typing import Any

from mekhane.mcp.hub_config import axis_url
from mekhane.mcp.gateway_tools._utils import _trace_tool_call, _traced


def _call_sekisho_mcp_sync(tool_name: str, args: dict[str, Any]) -> str:
    """Synchronously call a tool on the Sekisho endpoint via Hub."""
    # 遅延 import — mcp パッケージが無い環境でもモジュール import は成功する
    from mcp.client.streamable_http import streamablehttp_client
    from mcp.client.session import ClientSession
    from mcp.types import CallToolResult

    hub_url = os.environ.get("HGK_DIANOETIKON_MCP_URL", axis_url("dianoetikon").removesuffix("/mcp"))
    url = f"{hub_url}/mcp"

    async def _do_call():
        try:
            async with streamablehttp_client(url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result: CallToolResult = await session.call_tool(tool_name, args)
                    out = []
                    for content in result.content:
                        if content.type == "text":
                            out.append(content.text)
                    return "\n".join(out)
        except Exception as e:  # noqa: BLE001
            return f"❌ Sekisho MCP Call Error ({tool_name}): {e}"

    return asyncio.run(_do_call())


# =========================================================================
# モジュールレベル関数 — import 可能
# =========================================================================

@_traced
def sekisho_audit(draft_response: str, reasoning: str, depth: str = "L1") -> str:
    """Daimonion γ (Akribeia) — BC 精密監査。Agent の最終応答を Gemini Pro で監査。PASS なら監査ログを返す (応答末尾に付記)。BLOCK なら差し止め+修正指示。最終応答前に必ず1回呼ぶこと。"""
    return _call_sekisho_mcp_sync("sekisho_audit", {
        "action": "audit",
        "draft_response": draft_response,
        "reasoning": reasoning,
        "depth": depth
    })


@_traced
def sekisho_gate(draft_response: str, reasoning: str, depth: str = "L1") -> str:
    """Daimonion γ (Akribeia) — Gate 発行。Gemini Pro で監査し、PASS なら gate_token を発行。BLOCK 時は修正指示を返す。"""
    return _call_sekisho_mcp_sync("sekisho_audit", {
        "action": "gate",
        "draft_response": draft_response,
        "reasoning": reasoning,
        "depth": depth
    })


@_traced
def sekisho_history(limit: int = 10) -> str:
    """過去の監査結果を表示する。"""
    return _call_sekisho_mcp_sync("sekisho_admin", {"action": "history", "limit": limit})


# =========================================================================
# MCP 登録 — hgk_gateway.py から呼ばれる
# =========================================================================

def register_sekisho_tools(mcp):
    """Sekisho ドメインの 3 tools を mcp インスタンスに登録する。"""
    mcp.tool()(sekisho_audit)
    mcp.tool()(sekisho_gate)
    mcp.tool()(sekisho_history)
