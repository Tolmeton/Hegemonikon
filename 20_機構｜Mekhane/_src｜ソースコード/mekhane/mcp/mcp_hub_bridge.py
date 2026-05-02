#!/usr/bin/env python3
"""
stdio-to-HTTP ブリッジ for Hub MCP Proxy
=========================================
Antigravity (type: stdio) → このスクリプト → Hub (streamable-http)

使い方:
  python3 mcp_hub_bridge.py ochema
  python3 mcp_hub_bridge.py hermeneus
  python3 mcp_hub_bridge.py hub

mcp.json での設定:
  "ochema": {
    "command": "/path/to/.venv/bin/python3",
    "type": "stdio",
    "args": ["/path/to/mcp_hub_bridge.py", "ochema"]
  }
"""
import sys
import asyncio
import os
from pathlib import Path


def _ensure_project_src_on_path() -> None:
    """フルパス直起動でも `mekhane` を import できるよう source root を補う。"""
    source_root = Path(__file__).resolve().parents[2]
    source_root_str = str(source_root)
    if source_root_str not in sys.path:
        sys.path.insert(0, source_root_str)


_ensure_project_src_on_path()

from mekhane.mcp.hub_config import AXIS_PORTS, BACKENDS, axis_url, get_backend_axis


def _router_base(target_name: str) -> tuple[str, str]:
    """target 名から axis router base URL と path を返す。"""
    if target_name in AXIS_PORTS:
        base = os.environ.get(f"HGK_{target_name.upper()}_MCP_URL", axis_url(target_name).removesuffix("/mcp"))
        return base, "/mcp"

    if target_name == "hub":
        base = os.environ.get("HGK_DIANOETIKON_MCP_URL", axis_url("dianoetikon").removesuffix("/mcp"))
        return base, "/mcp/hub"

    axis_name = get_backend_axis(target_name) or "dianoetikon"
    base = os.environ.get(f"HGK_{axis_name.upper()}_MCP_URL", axis_url(axis_name).removesuffix("/mcp"))
    if BACKENDS.get(target_name, {}).get("placement") == "remote":
        return base, "/mcp"
    return base, f"/mcp/{target_name}"


async def bridge(backend_name: str):
    """stdin/stdout を Hub の streamable-http エンドポイントに中継する"""
    from mcp.client.streamable_http import streamablehttp_client
    from mcp.server.stdio import stdio_server
    from mcp import ClientSession

    hub_base, path = _router_base(backend_name)
    url = f"{hub_base}{path}"

    # Hub への接続
    async with streamablehttp_client(url) as (hub_read, hub_write, _):
        async with ClientSession(hub_read, hub_write) as hub_session:
            await hub_session.initialize()

            # Hub からツール一覧を取得
            tools_result = await hub_session.list_tools()
            tool_list = tools_result.tools

            # ローカル MCP サーバー (stdio) を作成し、Hub のツールを公開
            from mcp.server import Server
            server = Server(f"bridge-{backend_name}")

            @server.list_tools()
            async def list_tools():
                # Hub から取得したツール定義をそのまま返す
                return tool_list

            @server.call_tool()
            async def call_tool(name: str, arguments: dict):
                # Hub 経由でバックエンドのツールを呼び出す
                result = await hub_session.call_tool(name, arguments)
                return result.content

            # stdio で Antigravity に公開
            from mcp.server.stdio import stdio_server as run_stdio
            async with run_stdio() as (read_stream, write_stream):
                await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    if len(sys.argv) < 2:
        print("Usage: mcp_hub_bridge.py <backend_name>", file=sys.stderr)
        print("  e.g.: mcp_hub_bridge.py ochema", file=sys.stderr)
        sys.exit(1)

    backend_name = sys.argv[1]
    asyncio.run(bridge(backend_name))


if __name__ == "__main__":
    main()
