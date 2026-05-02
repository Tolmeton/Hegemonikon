# PROOF: mekhane/kube/tests/test_kube_integration.py
# PURPOSE: kube モジュールの kube_integration に対するテスト
"""
Kube MCP 統合テスト: handle_kube_tool → Agent → Bridge の統合を検証。

消去テスト: kube_mcp_server.py を消すとこのテストが壊れる。
"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from mekhane.mcp.kube_mcp_server import handle_kube_tool
from mekhane.kube.playwright_bridge import PageState, ActionResult


def make_plan_json():
    return json.dumps({
        "goal_understanding": "テスト",
        "feasibility": "possible",
        "subgoals": [
            {"id": 1, "description": "テスト", "security_level": "read",
             "success_criteria": "OK"},
        ],
        "requires_login": False, "requires_payment": False, "warnings": [],
    })


def make_decide_json(action="subgoal_complete"):
    return json.dumps({
        "thinking": "OK", "action": action,
        "args": {"summary": "done"}, "confidence": 0.9,
        "security_level": "read", "confirm_required": False,
    })


class TestHandleKubeTool:
    @pytest.mark.asyncio
    async def test_kube_plan_returns_plan(self):
        """kube_plan ツールが Plan 構造を返す"""
        llm = AsyncMock(return_value=make_plan_json())

        result = await handle_kube_tool(
            "kube_plan",
            {"goal": "example.com を開く"},
            llm_callable=llm,
        )

        assert "goal_understanding" in json.dumps(result, ensure_ascii=False, default=str)
        llm.assert_awaited()

    @pytest.mark.asyncio
    async def test_kube_observe_returns_state(self):
        """kube_observe ツールがページ状態を返す"""
        mock_state = PageState(
            url="https://example.com", title="Example",
            snapshot="[button] Submit", interactive_count=1,
        )

        # _active_bridge グローバル変数をパッチする
        with patch("mekhane.mcp.kube_mcp_server._active_bridge") as bridge:
            bridge.observe = AsyncMock(return_value=mock_state)

            result = await handle_kube_tool("kube_observe", {})
            assert "url" in json.dumps(result, ensure_ascii=False, default=str)

    @pytest.mark.asyncio
    async def test_unknown_tool_raises(self):
        """未知のツール名はエラーを返す"""
        result = await handle_kube_tool("kube_unknown", {})
        result_str = json.dumps(result, ensure_ascii=False, default=str)
        assert "error" in result_str.lower() or "unknown" in result_str.lower()
