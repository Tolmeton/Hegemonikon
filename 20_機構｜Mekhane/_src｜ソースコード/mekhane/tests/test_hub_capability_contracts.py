# PROOF: [L2/テスト] <- mekhane/mcp/hub_mcp_server.py delegated capability の偽陰性を固定

from __future__ import annotations

import asyncio

from mekhane.mcp.hub_mcp_server import HubProxy


class _DummyUpstream:
    def __init__(self, *, is_connected: bool, tools: list[dict] | None = None):
        self.is_connected = is_connected
        self.tools = tools or []


def test_delegated_upstream_probe_skips_local_tool_visibility_check() -> None:
    hub = HubProxy(axis="aisthetikon", placement_profile="local")
    hub._delegated_backend_names = ["periskope"]
    hub._upstream_axis = _DummyUpstream(is_connected=True, tools=[])

    result = asyncio.run(hub._probe_backend_capability("periskope", refresh=True))

    assert result["status"] == "ok"
    assert result["reason"] == "delegated via upstream axis"
    assert result["observed_tools"] == []


def test_delegated_upstream_probe_reports_visible_upstream_tools_when_available() -> None:
    hub = HubProxy(axis="aisthetikon", placement_profile="local")
    hub._delegated_backend_names = ["periskope"]
    hub._upstream_axis = _DummyUpstream(
        is_connected=True,
        tools=[
            {"name": "periskope_search"},
            {"name": "hub_healthz"},
            {"name": "periskope_research"},
        ],
    )

    result = asyncio.run(hub._probe_backend_capability("periskope", refresh=True))

    assert result["status"] == "ok"
    assert result["observed_tools"] == ["periskope_research", "periskope_search"]
