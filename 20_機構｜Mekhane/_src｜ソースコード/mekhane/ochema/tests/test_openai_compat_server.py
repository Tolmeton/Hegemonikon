# PROOF: [L2/インフラ] <- mekhane/ochema/tests/test_openai_compat_server.py
# PURPOSE: OpenAI 互換ブリッジ + Anthropic Messages API のスモーク（外部 LLM なし）

from __future__ import annotations
import os
from unittest.mock import MagicMock, patch
import pytest

pytest.importorskip("fastapi", reason="fastapi not installed (see requirements.txt)")
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("HGK_OPENAI_COMPAT_TOKEN", "test-secret-token")
    from mekhane.ochema.openai_compat_server import create_app

    return TestClient(create_app())


# =============================================================================
# Health & Auth (既存テスト)
# =============================================================================


def test_health_no_auth(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_models_requires_bearer(client: TestClient) -> None:
    r = client.get("/v1/models")
    assert r.status_code == 401


def test_models_with_bearer(client: TestClient) -> None:
    r = client.get(
        "/v1/models",
        headers={"Authorization": "Bearer test-secret-token"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("object") == "list"
    assert isinstance(body.get("data"), list)
    assert len(body["data"]) >= 1


def test_cli_status_requires_bearer(client: TestClient) -> None:
    r = client.get("/v1/cli/status")
    assert r.status_code == 401


def test_cli_status_returns_bridge_status(client: TestClient) -> None:
    with patch("mekhane.ochema.cli_agent_bridge.status") as mock_status:
        mock_status.return_value = {
            "codex": {"available": True},
            "copilot": {"available": False},
        }
        r = client.get(
            "/v1/cli/status",
            headers={"Authorization": "Bearer test-secret-token"},
        )

    assert r.status_code == 200
    assert r.json() == {
        "status": "ok",
        "tools": {
            "codex": {"available": True},
            "copilot": {"available": False},
        },
    }
    _, kwargs = mock_status.call_args
    assert kwargs == {"run_smoke": False, "smoke_timeout": 30}


def test_cli_status_can_request_smoke(client: TestClient) -> None:
    with patch("mekhane.ochema.cli_agent_bridge.status") as mock_status:
        mock_status.return_value = {"codex": {"available": True}}
        r = client.get(
            "/v1/cli/status?smoke=true&timeout=12",
            headers={"Authorization": "Bearer test-secret-token"},
        )

    assert r.status_code == 200
    _, kwargs = mock_status.call_args
    assert kwargs == {"run_smoke": True, "smoke_timeout": 12}


def test_cli_smoke_single_tool(client: TestClient) -> None:
    with patch("mekhane.ochema.cli_agent_bridge.smoke") as mock_smoke:
        mock_smoke.return_value = {"status": "ok", "tool": "codex"}
        r = client.post(
            "/v1/cli/smoke",
            headers={"Authorization": "Bearer test-secret-token"},
            json={"tool": "codex", "timeout": 9},
        )

    assert r.status_code == 200
    assert r.json() == {
        "status": "ok",
        "result": {"status": "ok", "tool": "codex"},
    }
    _, kwargs = mock_smoke.call_args
    assert kwargs == {"timeout": 9}


def test_cli_smoke_all_tools(client: TestClient) -> None:
    with patch("mekhane.ochema.cli_agent_bridge.smoke") as mock_smoke:
        mock_smoke.side_effect = lambda tool, timeout=30: {"status": "ok", "tool": tool, "timeout": timeout}
        r = client.post(
            "/v1/cli/smoke",
            headers={"Authorization": "Bearer test-secret-token"},
            json={"tool": "all", "timeout": 7},
        )

    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert sorted(r.json()["result"].keys()) == ["codex", "copilot", "cursor-agent", "gemini"]


def test_chat_completions_requires_bearer(client: TestClient) -> None:
    r = client.post(
        "/v1/chat/completions",
        json={
            "model": "gemini-3-flash-preview",
            "messages": [{"role": "user", "content": "ping"}],
        },
    )
    assert r.status_code == 401


def test_chat_completions_empty_messages_400_with_auth(client: TestClient) -> None:
    r = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer test-secret-token"},
        json={"model": "gemini-3-flash-preview", "messages": []},
    )
    assert r.status_code == 400


# =============================================================================
# Anthropic Messages API (/v1/messages) テスト
# =============================================================================


def test_messages_requires_api_key(client: TestClient) -> None:
    """x-api-key がないと 401."""
    r = client.post(
        "/v1/messages",
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 100,
            "messages": [{"role": "user", "content": "ping"}],
        },
    )
    assert r.status_code == 401


def test_messages_bearer_also_works(client: TestClient) -> None:
    """Bearer トークンでも認証できる (互換性)."""
    r = client.post(
        "/v1/messages",
        headers={"Authorization": "Bearer test-secret-token"},
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 100,
            "messages": [],
        },
    )
    # 空メッセージなので 400 であること (401 ではない = 認証は通った)
    assert r.status_code == 400


def test_messages_empty_messages_400(client: TestClient) -> None:
    """空 messages は 400."""
    r = client.post(
        "/v1/messages",
        headers={"x-api-key": "test-secret-token"},
        json={
            "model": "claude-opus-4-20250514",
            "max_tokens": 100,
            "messages": [],
        },
    )
    assert r.status_code == 400


def _mock_llm_response(text: str = "pong") -> MagicMock:
    resp = MagicMock()
    resp.text = text
    resp.token_usage = {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    resp.stop_reason = "end_turn"
    return resp


def test_messages_non_streaming_response_format(client: TestClient) -> None:
    """非ストリーミングレスポンスが Anthropic Messages API 形式."""
    mock_resp = _mock_llm_response("test response")

    with (
        patch.dict(os.environ, {"HGK_SONNET_BACKEND": "ls:claude-sonnet"}, clear=False),
        patch("mekhane.ochema.service.OchemaService.get") as mock_svc,
    ):
        instance = MagicMock()
        instance._ask_ls.return_value = mock_resp
        mock_svc.return_value = instance

        r = client.post(
            "/v1/messages",
            headers={"x-api-key": "test-secret-token"},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "ping"}],
            },
        )

    assert r.status_code == 200
    body = r.json()
    # Anthropic Messages API レスポンス形式の検証
    assert body["type"] == "message"
    assert body["role"] == "assistant"
    assert isinstance(body["content"], list)
    assert len(body["content"]) >= 1
    assert body["content"][0]["type"] == "text"
    assert body["content"][0]["text"] == "test response"
    assert body["model"] == "claude-sonnet-4-20250514"
    assert body["stop_reason"] == "end_turn"
    assert "usage" in body
    assert "input_tokens" in body["usage"]
    assert "output_tokens" in body["usage"]
    assert body["id"].startswith("msg_")


def test_messages_streaming_response_format(client: TestClient) -> None:
    """SSE ストリーミングが Anthropic SSE 形式."""
    mock_resp = _mock_llm_response("streamed content")

    with (
        patch.dict(os.environ, {"HGK_OPUS_BACKEND": "ls:claude-opus"}, clear=False),
        patch("mekhane.ochema.service.OchemaService.get") as mock_svc,
    ):
        instance = MagicMock()
        instance._ask_ls.return_value = mock_resp
        mock_svc.return_value = instance

        r = client.post(
            "/v1/messages",
            headers={"x-api-key": "test-secret-token"},
            json={
                "model": "claude-opus-4-20250514",
                "max_tokens": 100,
                "stream": True,
                "messages": [{"role": "user", "content": "ping"}],
            },
        )

    assert r.status_code == 200
    # SSE 形式の検証
    content = r.text
    assert "event: message_start" in content
    assert "event: content_block_start" in content
    assert "event: content_block_delta" in content
    assert "event: content_block_stop" in content
    assert "event: message_delta" in content
    assert "event: message_stop" in content
    # テキスト内容の検証
    assert "streamed content" in content


def test_messages_model_routing_claude(client: TestClient) -> None:
    """claude-* モデルは slot policy に従って解決される."""
    from mekhane.ochema.openai_compat_server import _normalize_anthropic_model

    model, route = _normalize_anthropic_model("claude-sonnet-4-20250514")
    assert route == "cli_agent_smart"
    assert model == "operator"

    model, route = _normalize_anthropic_model("claude-opus-4-20250514")
    assert route == "anthropic_passthrough"
    assert model == "claude-opus"


def test_messages_model_routing_claude_ls_override(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from mekhane.ochema.openai_compat_server import _normalize_anthropic_model

    monkeypatch.setenv("HGK_OPUS_BACKEND", "ls:claude-opus")
    model, route = _normalize_anthropic_model("claude-opus-4-20250514")
    assert route == "ls"
    assert model == "claude-opus"


def test_messages_model_routing_gemini(client: TestClient) -> None:
    """gemini-* モデルは Cortex ルートに行く."""
    from mekhane.ochema.openai_compat_server import _normalize_anthropic_model

    model, route = _normalize_anthropic_model("gemini-3.1-pro-preview")
    assert route == "cortex"
    assert "gemini" in model


def test_messages_smart_route_coding_uses_codex(client: TestClient) -> None:
    with patch("mekhane.ochema.cli_agent_bridge.run_cli_agent") as mock_run:
        mock_run.return_value = {"status": "ok", "output": "done"}
        r = client.post(
            "/v1/messages",
            headers={"x-api-key": "test-secret-token"},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 100,
                "system": "task_class: coding",
                "messages": [{"role": "user", "content": "Fix this bug."}],
            },
        )

    assert r.status_code == 200
    _, kwargs = mock_run.call_args
    assert kwargs["tool"] == "codex"
    assert kwargs["model"] == "gpt-5.3-codex:high"


def test_messages_smart_route_analysis_uses_copilot_xhigh(client: TestClient) -> None:
    with patch("mekhane.ochema.cli_agent_bridge.run_cli_agent") as mock_run:
        mock_run.return_value = {"status": "ok", "output": "analysis"}
        r = client.post(
            "/v1/messages",
            headers={"x-api-key": "test-secret-token"},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 100,
                "system": "task_class: analysis",
                "messages": [{"role": "user", "content": "Review this plan."}],
            },
        )

    assert r.status_code == 200
    _, kwargs = mock_run.call_args
    assert kwargs["tool"] == "copilot"
    assert kwargs["model"] == "gpt-5.4:xhigh"


def test_messages_smart_route_multimodal_uses_gemini_handler(client: TestClient) -> None:
    from fastapi.responses import JSONResponse

    with patch(
        "mekhane.ochema.openai_compat_server._gemini_cli_handler",
        autospec=True,
    ) as mock_handler:
        mock_handler.return_value = JSONResponse(
            content={
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": "gemini"}],
                "model": "claude-sonnet-4-20250514",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        )
        r = client.post(
            "/v1/messages",
            headers={"x-api-key": "test-secret-token"},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 100,
                "system": "task_class: multimodal_heavy",
                "messages": [{"role": "user", "content": "Scan this large document and report."}],
            },
        )

    assert r.status_code == 200
    assert mock_handler.call_args.args[1] == "gemini-3.1-pro"


def test_messages_system_prompt_extraction() -> None:
    """system フィールドが正しく抽出される."""
    from mekhane.ochema.openai_compat_server import (
        AnthropicMessage,
        _anthropic_messages_to_ask_params,
    )

    msgs = [AnthropicMessage(role="user", content="hello")]
    sys_inst, message = _anthropic_messages_to_ask_params(msgs, system="You are helpful")
    assert sys_inst == "You are helpful"
    assert "user: hello" in message


def test_messages_content_blocks_extraction() -> None:
    """content blocks 形式のメッセージが正しく変換される."""
    from mekhane.ochema.openai_compat_server import (
        AnthropicMessage,
        _anthropic_messages_to_ask_params,
    )

    msgs = [
        AnthropicMessage(
            role="user",
            content=[
                {"type": "text", "text": "What is this?"},
                {"type": "text", "text": "Tell me more."},
            ],
        )
    ]
    sys_inst, message = _anthropic_messages_to_ask_params(msgs)
    assert sys_inst is None
    assert "What is this?" in message
    assert "Tell me more." in message
