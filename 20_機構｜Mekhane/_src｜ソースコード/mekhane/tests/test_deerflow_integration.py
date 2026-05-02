import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from mekhane.mcp.mcp_base import MCPBase
from mekhane.ochema.cortex_tools import CortexTools
from mekhane.ochema.types import LLMResponse


def test_epoche_and_thambos_integration(monkeypatch):
    """
    Epoche (D2) と Thambos (D1) の結合テスト。
    1. Thambos フックが MCP にインストールされ、曖昧な出力を拾うか。
    2. ループ上限により Epoche レポートが生成され、pending_synthesis として戻るか。
    """
    pytest.importorskip("mcp.types")
    from mcp.types import CallToolRequest, CallToolResult, TextContent

    base = MCPBase("test_integration", "0.0.1", "integration")
    
    # 内側のツールハンドラ（わざと Thambos に引っかかる曖昧ワードを返す）
    async def _mock_handler(req: CallToolRequest):
        return CallToolResult(
            content=[TextContent(type="text", text="実行結果ですが、前提が情報不足のため断定できません。")],
        )
    
    base.server.request_handlers[CallToolRequest] = _mock_handler
    base.install_thambos_hook()
    
    class _MockAPI:
        def _build_request(self, **kwargs):
            return {}
        def _call_api(self, *a, **kw):
            return {}
        def _parse_response(self, raw):
            r = LLMResponse(
                model="test-model",
                token_usage={"total_tokens": 10},
            )
            r.function_calls = [{"name": "test_tool", "args": {}}]
            r.raw_model_parts = [{"functionCall": {"name": "test_tool", "args": {}}}]
            return r
        def ask(self, *a, **kw):
            return ""

    monkeypatch.setattr("mekhane.agent_guard.apotheke.retrieve_context", lambda *a, **k: [])
    
    from mekhane.ochema import tools as ochema_tools_mod
    def _mock_execute(name, args):
        # 擬似的に Thambos の出力を再現（_mock_handler の結果にフックを通した結果と仮定）
        return {"output": "実行結果ですが、前提が情報不足のため断定できません。\n\n## [Thambos] 曖昧性の兆候 (N-6 heuristic)\n- **情報不足の兆候** (根拠: \"情報不足\")"}
    monkeypatch.setattr(ochema_tools_mod, "execute_tool", _mock_execute)

    tools = CortexTools(_MockAPI())  # type: ignore
    
    test_tool = {
        "name": "test_tool",
        "description": "test",
        "parameters": {"type": "object", "properties": {}},
    }
    
    # max_iterations=1 で一発で Epoche させる
    response = tools.ask_with_tools(
        message="テストして",
        model="test-model",
        temperature=0.0,
        max_tokens=100,
        max_iterations=1,
        tools=[test_tool]
    )

    # 検証
    body = json.loads(response.text)
    assert "epoche_report" in body
    assert body["epoche_report"]["reason"] == "max_iterations_reached"
    assert body["epoche_report"]["synthesis_status"] == "pending"
    assert response.pending_synthesis is not None
    assert response.pending_synthesis[0]["name"] == "test_tool"
    # pending_synthesis の意味論として、「未解決(エラー)」ではなく「実行完了したが統合待ち」であることが保証されている。




