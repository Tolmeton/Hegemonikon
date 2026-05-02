# PROOF: mekhane/mcp/gateway_tools/hub.py
# PURPOSE: Hub MCP server tools — Ochema からも直接 import 可能な設計
"""Gateway tools: hub domain.

関数はモジュールレベルに定義し、register_hub_tools(mcp) で MCP 登録のみ行う。
mcp.client.* は関数内で遅延 import し、mcp パッケージ未インストール環境でも
モジュール自体の import は成功する。

FEP 3能力 (τὸ -τικόν 系):
  hub_aisthetikon — 知覚能力 (S群)  旧名: hub_sense
  hub_dianoetikon — 推論能力 (I群)  旧名: hub_infer
  hub_poietikon   — 生産能力 (E群)  旧名: hub_effect

Daimonion (δαιμόνιον):
  hub_daimonion_status — 統一監視体の状態/切替  旧名: hub_shadow_status
  hub_daimonion_judge  — γ 精密監査 PASS/BLOCK  旧名: hub_gate
"""
import asyncio
import json
import os
import urllib.request
from typing import Any

from mekhane.mcp.hub_config import AXIS_PORTS, axis_url, get_backend_axis
from mekhane.mcp.gateway_tools._utils import _traced


def _axis_router_url(axis_name: str) -> str:
    env_name = f"HGK_{axis_name.upper()}_MCP_URL"
    return os.environ.get(env_name, axis_url(axis_name).removesuffix("/mcp"))


def _tool_axis(tool_name: str, backend: str | None = None) -> str:
    if backend:
        axis = get_backend_axis(backend)
        if axis:
            return axis
    if tool_name in ("hub_aisthetikon", "hub_sense", "hub_boot_context"):
        return "aisthetikon"
    if tool_name in ("hub_poietikon", "hub_effect"):
        return "poietikon"
    return "dianoetikon"


async def _call_hub_mcp(tool_name: str, args: dict[str, Any], *, axis_name: str) -> str:
    """Call a tool on an axis router (async-native)."""
    # 遅延 import — mcp パッケージが無い環境でもモジュール import は成功する
    from mcp.client.streamable_http import streamablehttp_client
    from mcp.client.session import ClientSession
    from mcp.types import CallToolResult

    url = f"{_axis_router_url(axis_name)}/mcp"

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
        return f"❌ Hub MCP Call Error ({axis_name}.{tool_name}): {e}"


async def _axis_health(axis_name: str) -> dict[str, Any]:
    url = f"{_axis_router_url(axis_name)}/health"

    def _fetch() -> dict[str, Any]:
        with urllib.request.urlopen(url, timeout=5) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))

    try:
        data = await asyncio.to_thread(_fetch)
        return {"axis": axis_name, "ok": True, "stats": data}
    except Exception as exc:  # noqa: BLE001
        return {"axis": axis_name, "ok": False, "error": str(exc), "url": url}


# =========================================================================
# モジュールレベル関数 — import 可能
# =========================================================================

# --- Daimonion (統一監視体) ---

@_traced
async def hub_daimonion_status(enabled: bool | None = None) -> str:
    """Daimonion (δαιμόνιον) の状態/切替"""
    args: dict[str, Any] = {}
    if enabled is not None:
        args["enabled"] = enabled
    return await _call_hub_mcp("hub_daimonion_status", args, axis_name="dianoetikon")

# 後方互換エイリアス
hub_shadow_status = hub_daimonion_status


@_traced
async def hub_daimonion_judge(draft_response: str, reasoning: str, depth: str = "L1") -> str:
    """Daimonion γ (Akribeia) — 精密監査"""
    return await _call_hub_mcp("hub_daimonion_judge", {
        "draft_response": draft_response,
        "reasoning": reasoning,
        "depth": depth
    }, axis_name="dianoetikon")

# 後方互換エイリアス
hub_gate = hub_daimonion_judge


@_traced
async def hub_stats() -> str:
    """3 軸 router のヘルス統計を集約する。"""
    stats = await asyncio.gather(*[
        _axis_health(axis_name) for axis_name in AXIS_PORTS
    ])
    return json.dumps({"axes": stats}, ensure_ascii=False, indent=2)


@_traced
async def hub_recommend(task_description: str, top_k: int = 3) -> str:
    """推奨ツールの取得"""
    return await _call_hub_mcp(
        "hub_recommend",
        {"task_description": task_description, "top_k": top_k},
        axis_name="dianoetikon",
    )


@_traced
async def hub_execute(backend: str, tool: str, arguments: dict | None = None) -> str:
    """ツールの実行をプロキシ"""
    args: dict[str, Any] = {"backend": backend, "tool": tool}
    if arguments:
        args["arguments"] = arguments
    return await _call_hub_mcp("hub_execute", args, axis_name=_tool_axis("hub_execute", backend))


# --- FEP 認知入口: 3能力 (τὸ -τικόν 系) ---

@_traced
async def hub_aisthetikon(task_description: str, top_k: int = 3) -> str:
    """Aisthetikon (τὸ αἰσθητικόν) — 知覚能力: 調べたいとき"""
    return await _call_hub_mcp(
        "hub_aisthetikon",
        {"task_description": task_description, "top_k": top_k},
        axis_name="aisthetikon",
    )

# 後方互換エイリアス
hub_sense = hub_aisthetikon


@_traced
async def hub_dianoetikon(task_description: str, top_k: int = 3) -> str:
    """Dianoetikon (τὸ διανοητικόν) — 推論能力: 処理を深めたいとき"""
    return await _call_hub_mcp(
        "hub_dianoetikon",
        {"task_description": task_description, "top_k": top_k},
        axis_name="dianoetikon",
    )

# 後方互換エイリアス
hub_infer = hub_dianoetikon


@_traced
async def hub_poietikon(task_description: str, top_k: int = 3) -> str:
    """Poietikon (τὸ ποιητικόν) — 生産能力: 成果物を生成したいとき"""
    return await _call_hub_mcp(
        "hub_poietikon",
        {"task_description": task_description, "top_k": top_k},
        axis_name="poietikon",
    )

# 後方互換エイリアス
hub_effect = hub_poietikon


# =========================================================================
# MCP 登録 — hgk_gateway.py から呼ばれる
# =========================================================================

def register_hub_tools(mcp):
    """Hub ドメインのツールを mcp インスタンスに登録する。"""
    # Daimonion
    mcp.tool()(hub_daimonion_status)
    mcp.tool()(hub_daimonion_judge)
    # Core
    mcp.tool()(hub_stats)
    mcp.tool()(hub_recommend)
    mcp.tool()(hub_execute)
    # FEP 認知入口 (新名)
    mcp.tool()(hub_aisthetikon)
    mcp.tool()(hub_dianoetikon)
    mcp.tool()(hub_poietikon)
