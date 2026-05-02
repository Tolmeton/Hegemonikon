# PROOF: [L2/インフラ] <- mekhane/ochema/openai_compat_server.py
# PURPOSE: Cursor 等の OpenAI 互換クライアント向け HTTP ブリッジ。
#   Claude Code を control plane とし、Claude/Codex/Copilot/Gemini に task-class でルーティングする。
from __future__ import annotations
from typing import Any
"""OpenAI-compatible HTTP bridge for Cursor custom models.

- ``POST /v1/chat/completions`` — maps to :meth:`OchemaService.ask` / :meth:`OchemaService.stream`
- ``GET /v1/models`` — static list (see ``AVAILABLE_MODELS`` in ``service.py``)

Security (defaults):
  - Bind to ``127.0.0.1`` only
  - Require ``Authorization: Bearer <token>`` matching env ``HGK_OPENAI_COMPAT_TOKEN``

Environment:
  - ``HGK_OPENAI_COMPAT_TOKEN`` — required bearer secret (set same value in Cursor API Key)
  - ``HGK_OPENAI_COMPAT_HOST`` — default ``127.0.0.1``
  - ``HGK_OPENAI_COMPAT_PORT`` — default ``8765``
  - ``HGK_LS_CONNECT_HOST`` — LS ConnectRPC 接続先（AntigravityClient）。既定 ``127.0.0.1``。Claude 失敗時はブリッジから当該ホスト:port への **TCP 到達**を先に確認（タイムアウト延長は根因ではない）。

Run::
    python -m mekhane.ochema.openai_compat_server
    # or: uvicorn mekhane.ochema.openai_compat_server:app --host 127.0.0.1 --port 8765
"""


import asyncio
import functools
import json
import logging
import os
import time
import uuid
from typing import Iterator

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from mekhane.ochema.task_routing import resolve_cli_task_route
from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)


async def _async_ask_ls(
    svc: Any,
    *,
    message: str,
    model: str,
    system_instruction: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    thinking_budget: int | None = None,
    timeout: float = 120.0,
) -> Any:
    """OchemaService._ask_ls をスレッドで実行する。

    FastAPI の async ハンドラ内で同期の LS Cascade (ポーリング含む) を直に呼ぶと
    イベントループがブロックされ、クライアント・プロキシ側がタイムアウト/502 に見える。
    ask_async / _execute_attempt_async と同様に asyncio.to_thread を使う。
    """
    fn = functools.partial(
        svc._ask_ls,
        message,
        model,
        system_instruction=system_instruction,
        temperature=temperature,
        max_tokens=max_tokens,
        thinking_budget=thinking_budget,
        timeout=timeout,
    )
    return await asyncio.to_thread(fn)


# --- env ---

_ENV_TOKEN = "HGK_OPENAI_COMPAT_TOKEN"
_ENV_HOST = "HGK_OPENAI_COMPAT_HOST"
_ENV_PORT = "HGK_OPENAI_COMPAT_PORT"


def _expected_bearer() -> str:
    t = os.environ.get(_ENV_TOKEN, "").strip()
    return t


def _is_loopback(host: str | None) -> bool:
    if not host:
        return False
    h = host.lower()
    # Starlette TestClient uses host "testclient"
    if h in ("127.0.0.1", "localhost", "::1", "testclient"):
        return True
    return h.endswith("127.0.0.1")


async def verify_localhost(request: Request) -> None:
    """Reject non-loopback clients (defense in depth; server should bind 127.0.0.1).

    cloudflared トンネル経由の場合は HGK_OPENAI_COMPAT_ALLOW_REMOTE=1 で緩和可能。
    Bearer トークン認証 (verify_bearer) が防衛線として機能する。
    """
    # cloudflared / リバースプロキシ経由の場合はバイパス
    if os.environ.get("HGK_OPENAI_COMPAT_ALLOW_REMOTE", "").strip() == "1":
        return
    c = request.client
    if c is None or not _is_loopback(c.host):
        raise HTTPException(status_code=403, detail="Only loopback clients are allowed")


async def verify_bearer(request: Request) -> None:
    expected = _expected_bearer()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail=f"Set {_ENV_TOKEN} to a non-empty secret",
        )
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth[7:].strip()
    if token != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")


# =============================================================================
# Anthropic Messages API (/v1/messages) — Claude Code ブリッジ
# =============================================================================
# ANTHROPIC_BASE_URL=http://localhost:8765 で Claude Code を起動すると
# 全リクエストがここに来る。model フィールドで Anthropic/CLI/Gemini にルーティング。


class AnthropicContentBlock(BaseModel):
    """Anthropic content block (text, tool_use, etc.)."""
    type: str = "text"
    text: str = ""
    # tool_use fields (Phase 2 — 構造だけ定義)
    id: str | None = None
    name: str | None = None
    input: dict | None = None


class AnthropicMessage(BaseModel):
    """Anthropic messages API message format."""
    role: str  # "user" | "assistant"
    content: str | list[dict] = ""


class AnthropicMessagesRequest(BaseModel):
    """POST /v1/messages request body (Anthropic Messages API)."""
    model: str
    messages: list[AnthropicMessage]
    system: str | list[dict] | None = None
    max_tokens: int = 8192
    temperature: float | None = None
    stream: bool = False
    # Phase 2: tool_use / thinking (構造だけ受け入れて drop)
    tools: list[dict] | None = None
    tool_choice: dict | str | None = None
    thinking: dict | None = None
    # 追加パラメータ (Claude Code が送る可能性があるもの)
    top_p: float | None = None
    top_k: int | None = None
    stop_sequences: list[str] | None = None
    metadata: dict | None = None


async def verify_anthropic_auth(request: Request) -> None:
    """Anthropic x-api-key ヘッダ認証 (Bearer も許容)."""
    expected = _expected_bearer()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail=f"Set {_ENV_TOKEN} to a non-empty secret",
        )
    # x-api-key ヘッダ (Anthropic 標準)
    api_key = request.headers.get("x-api-key", "").strip()
    if api_key == expected:
        return
    # Authorization: Bearer (互換)
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        if token == expected:
            return
    raise HTTPException(status_code=401, detail="Invalid API key")


def _anthropic_messages_to_ask_params(
    messages: list[AnthropicMessage],
    system: str | list[dict] | None = None,
) -> tuple[str | None, str]:
    """Anthropic messages → (system_instruction, combined_message) に変換."""
    # System prompt
    sys_text: str | None = None
    if isinstance(system, str):
        sys_text = system
    elif isinstance(system, list):
        # system が content blocks の配列の場合
        parts = []
        for block in system:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        sys_text = "\n\n".join(parts) if parts else None

    # Messages → user/assistant transcript
    lines: list[str] = []
    for m in messages:
        role = (m.role or "user").lower()
        if isinstance(m.content, str):
            content = m.content
        elif isinstance(m.content, list):
            # content blocks 形式
            parts = []
            for block in m.content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_result":
                        # tool_result は内部のテキストを抽出
                        inner = block.get("content", "")
                        if isinstance(inner, str):
                            parts.append(inner)
                        elif isinstance(inner, list):
                            for ib in inner:
                                if isinstance(ib, dict) and ib.get("type") == "text":
                                    parts.append(ib.get("text", ""))
            content = "\n".join(parts)
        else:
            content = str(m.content)
        lines.append(f"{role}: {content}")

    message = "\n\n".join(lines) if lines else ""
    return sys_text, message


def _parse_backend_spec(spec: str) -> tuple[str, str]:
    """Parse 'route:model' backend spec → (internal_model, route).

    環境変数 HGK_HAIKU_BACKEND / HGK_SONNET_BACKEND の値をパースする。

    Examples:
        "gemini_cli:gemini-3.1-pro"         → ("gemini-3.1-pro", "gemini_cli")
        "cli_agent:copilot:gpt-5.4:xhigh"   → ("copilot:gpt-5.4:xhigh", "cli_agent")
        "cli_agent:codex:gpt-5.3-codex:high" → ("codex:gpt-5.3-codex:high", "cli_agent")
        "cli_agent_smart:analysis"          → ("analysis", "cli_agent_smart")
        "ls:claude-sonnet"                  → ("claude-sonnet", "ls")

    cli_agent_smart ルート:
        task class から route を自動選択する。
        - coding           → Codex gpt-5.3-codex high
        - analysis         → Copilot gpt-5.4 xhigh
        - operator         → Copilot gpt-5.4 high
        - multimodal_heavy → Gemini CLI 3.1 Pro
    """
    parts = spec.strip().split(":", 1)
    route = parts[0]
    model = parts[1] if len(parts) > 1 else ""

    _ROUTE_DEFAULTS = {
        "cli_agent": "copilot",
        "cli_agent_smart": "operator",
        "gemini_cli": "gemini-3.1-pro",
        "ls": "claude-sonnet",
        "anthropic_passthrough": "claude-opus",
        "cortex": "gemini-3.1-pro-preview",
    }
    if route not in _ROUTE_DEFAULTS:
        raise ValueError(f"Unknown route in backend spec: {route!r} (full spec: {spec!r})")

    return model or _ROUTE_DEFAULTS[route], route


# --- 環境変数キー ---
_ENV_OPUS_BACKEND = "HGK_OPUS_BACKEND"
_ENV_SONNET_BACKEND = "HGK_SONNET_BACKEND"
_ENV_HAIKU_BACKEND = "HGK_HAIKU_BACKEND"
_DEFAULT_OPUS_SPEC = "anthropic_passthrough:claude-opus"
_DEFAULT_SONNET_SPEC = "cli_agent_smart:operator"
_DEFAULT_HAIKU_SPEC = "gemini_cli:gemini-3.1-pro"


def _normalize_anthropic_model(name: str) -> tuple[str, str]:
    """Anthropic model 名 → (internal_model, route) に変換.

    Returns:
        (model_name, route)
        route: "ls" | "cortex" | "gemini_cli" | "cli_agent" | "cli_agent_smart" | "anthropic_passthrough"

    Claude Code subagent ルーティング (ANTHROPIC_BASE_URL 経由):
      opus   → 環境変数 HGK_OPUS_BACKEND (デフォルト: Anthropic API パススルー)
      sonnet → 環境変数 HGK_SONNET_BACKEND (デフォルト: task-class router)
      haiku  → 環境変数 HGK_HAIKU_BACKEND (デフォルト: Gemini CLI 3.1 Pro lane)

    環境変数の形式: "route:model" (例: "cli_agent:codex:gpt-5.3-codex:high", "ls:claude-opus")
    有効な route: ls, gemini_cli, cli_agent, cli_agent_smart, anthropic_passthrough, cortex
    """
    n = (name or "").strip().lower()

    # haiku slot: configurable via HGK_HAIKU_BACKEND
    if "haiku" in n:
        spec = os.environ.get(_ENV_HAIKU_BACKEND, _DEFAULT_HAIKU_SPEC)
        return _parse_backend_spec(spec)

    # sonnet slot: configurable via HGK_SONNET_BACKEND
    # デフォルト: task-class router (coding/analysis/operator)
    if "sonnet" in n:
        spec = os.environ.get(_ENV_SONNET_BACKEND, _DEFAULT_SONNET_SPEC)
        return _parse_backend_spec(spec)

    # opus slot: configurable via HGK_OPUS_BACKEND
    # デフォルト: Anthropic API パススルー (CC quota)
    # オプション: "ls:claude-opus" で LS 経由 (Antigravity 無料枠)
    if "opus" in n or "claude" in n:
        spec = os.environ.get(_ENV_OPUS_BACKEND, _DEFAULT_OPUS_SPEC)
        return _parse_backend_spec(spec)

    # Gemini 系 = Cortex 直
    if "gemini" in n:
        # 既知のモデル名をそのまま渡す
        for known in ("gemini-3.1-pro", "gemini-3.1-pro-preview", "gemini-3-pro-preview",
                       "gemini-3-flash-preview", "gemini-2.5-pro",
                       "gemini-2.5-flash", "gemini-2.0-flash"):
            if known in name:
                return known, "cortex"
        return "gemini-3.1-pro", "cortex"

    # デフォルト: Anthropic mainline
    spec = os.environ.get(_ENV_OPUS_BACKEND, _DEFAULT_OPUS_SPEC)
    return _parse_backend_spec(spec)


_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_API_VERSION = "2023-06-01"


async def _anthropic_passthrough(
    body: AnthropicMessagesRequest,
) -> JSONResponse | StreamingResponse:
    """Anthropic API にリクエストをそのまま転送 (CC quota 保持).

    ANTHROPIC_REAL_API_KEY 環境変数を使用。
    ANTHROPIC_API_KEY は ANTHROPIC_BASE_URL 設定時に ochema のトークンに
    書き換えられている可能性があるため、別の環境変数を使う。
    """
    import httpx

    api_key = os.environ.get("ANTHROPIC_REAL_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_REAL_API_KEY not set")

    # リクエストボディを再構築 (Pydantic model → dict)
    req_body = body.model_dump(exclude_none=True)

    headers = {
        "x-api-key": api_key,
        "anthropic-version": _ANTHROPIC_API_VERSION,
        "content-type": "application/json",
    }

    logger.info("Anthropic passthrough: model=%s stream=%s", body.model, body.stream)

    if body.stream:
        # SSE ストリーミング — httpx でストリーム接続し、そのまま転送
        async def stream_passthrough():
            async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
                async with client.stream(
                    "POST", _ANTHROPIC_API_URL, json=req_body, headers=headers,
                ) as resp:
                    if resp.status_code != 200:
                        error_body = await resp.aread()
                        logger.error("Anthropic passthrough error: %s %s", resp.status_code, error_body[:500])
                        yield f"event: error\ndata: {json.dumps({'type': 'error', 'error': {'type': 'api_error', 'message': error_body.decode()[:500]}})}\n\n"
                        return
                    async for line in resp.aiter_lines():
                        yield line + "\n"

        return StreamingResponse(
            stream_passthrough(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    # 非ストリーミング — httpx で POST して JSON をそのまま返す
    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
        resp = await client.post(_ANTHROPIC_API_URL, json=req_body, headers=headers)

    if resp.status_code != 200:
        logger.error("Anthropic passthrough error: %s %s", resp.status_code, resp.text[:500])
        raise HTTPException(status_code=resp.status_code, detail=resp.text[:500])

    return JSONResponse(content=resp.json(), status_code=200)


async def _gemini_cli_handler(
    body: AnthropicMessagesRequest,
    internal_model: str,
) -> JSONResponse | StreamingResponse:
    """Gemini CLI 経由でリクエストを処理 (asyncio.to_thread で blocking 回避).

    run_gemini() は subprocess.run() を使うため blocking。
    uvicorn の event loop をブロックしないよう to_thread() に逃がす。
    """
    import asyncio

    from mekhane.ochema.gemini_bridge import run_gemini

    sys_inst, message = _anthropic_messages_to_ask_params(
        body.messages, body.system,
    )
    full_prompt = f"{sys_inst}\n\n{message}" if sys_inst else message
    if not full_prompt.strip():
        raise HTTPException(status_code=400, detail="No content in messages")

    logger.info("Gemini CLI handler: model=%s stream=%s", internal_model, body.stream)

    # blocking subprocess を thread に逃がす
    gemini_result = await asyncio.to_thread(
        run_gemini,
        full_prompt,
        model=internal_model,
        sandbox=False,
        timeout=300,
    )

    text = gemini_result.get("output", gemini_result.get("error", ""))
    message_id = f"msg_{uuid.uuid4().hex[:24]}"

    if body.stream:
        # SSE ストリーミング (全体取得 → チャンク分割)
        def gemini_sse_gen() -> Iterator[str]:
            yield _anthropic_sse_event("message_start", {
                "type": "message_start",
                "message": {
                    "id": message_id, "type": "message", "role": "assistant",
                    "content": [], "model": body.model,
                    "stop_reason": None, "stop_sequence": None,
                    "usage": {"input_tokens": 0, "output_tokens": 0},
                },
            })
            yield _anthropic_sse_event("content_block_start", {
                "type": "content_block_start", "index": 0,
                "content_block": {"type": "text", "text": ""},
            })
            chunk_size = 100
            for i in range(0, len(text), chunk_size):
                yield _anthropic_sse_event("content_block_delta", {
                    "type": "content_block_delta", "index": 0,
                    "delta": {"type": "text_delta", "text": text[i:i + chunk_size]},
                })
            yield _anthropic_sse_event("content_block_stop", {
                "type": "content_block_stop", "index": 0,
            })
            yield _anthropic_sse_event("message_delta", {
                "type": "message_delta",
                "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                "usage": {"output_tokens": len(text) // 4},
            })
            yield _anthropic_sse_event("message_stop", {"type": "message_stop"})

        return StreamingResponse(
            gemini_sse_gen(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    # 非ストリーミング
    out = _build_anthropic_response(
        text=text,
        model=body.model,
        input_tokens=len(full_prompt) // 4,
        output_tokens=len(text) // 4,
        message_id=message_id,
    )
    return JSONResponse(content=out)


async def _cli_agent_handler(
    body: AnthropicMessagesRequest,
    internal_model: str,
    *,
    smart_route: bool = False,
) -> JSONResponse | StreamingResponse:
    """CLI Agent (copilot / codex / cursor-agent) 経由でリクエストを処理.

    cli_agent_bridge.run_cli_agent() は subprocess.run() を使うため blocking。
    uvicorn の event loop をブロックしないよう asyncio.to_thread() に逃がす。

    Args:
        smart_route: True の場合、task class から route を自動選択。
                     internal_model は task-class hint として扱う。
    """
    import asyncio

    from mekhane.ochema.cli_agent_bridge import run_cli_agent

    sys_inst, message = _anthropic_messages_to_ask_params(
        body.messages, body.system,
    )
    full_prompt = f"{sys_inst}\n\n{message}" if sys_inst else message
    if not full_prompt.strip():
        raise HTTPException(status_code=400, detail="No content in messages")

    if smart_route:
        decision = resolve_cli_task_route(
            full_prompt,
            default_task_class=internal_model,
        )
        logger.info(
            "CLI Agent SMART handler: task_class=%s route=%s tool=%s model=%s effort=%s",
            decision.task_class,
            decision.route,
            decision.tool,
            decision.model,
            decision.effort,
        )
        if decision.route == "anthropic_passthrough":
            return await _anthropic_passthrough(body)
        if decision.route == "gemini_cli":
            return await _gemini_cli_handler(body, decision.model or "gemini-3.1-pro")
        tool = decision.tool or "copilot"
        model = decision.bridge_model
    else:
        # 通常: internal_model からツールとモデルを決定 (形式: "tool" or "tool:model")
        if ":" in internal_model:
            tool, model = internal_model.split(":", 1)
            model = model or None
        else:
            tool = internal_model
            model = None

    logger.info("CLI Agent handler: tool=%s model=%s stream=%s", tool, model, body.stream)

    result = await asyncio.to_thread(
        run_cli_agent,
        full_prompt,
        tool=tool,
        model=model,
        timeout=300,
    )

    if result.get("status") != "ok":
        raise HTTPException(status_code=502, detail=result.get("error", "CLI agent failed"))

    text = result.get("output", "")
    message_id = f"msg_{uuid.uuid4().hex[:24]}"

    if body.stream:
        def cli_agent_sse_gen() -> Iterator[str]:
            yield _anthropic_sse_event("message_start", {
                "type": "message_start",
                "message": {
                    "id": message_id, "type": "message", "role": "assistant",
                    "content": [], "model": body.model,
                    "stop_reason": None, "stop_sequence": None,
                    "usage": {"input_tokens": 0, "output_tokens": 0},
                },
            })
            yield _anthropic_sse_event("content_block_start", {
                "type": "content_block_start", "index": 0,
                "content_block": {"type": "text", "text": ""},
            })
            chunk_size = 100
            for i in range(0, len(text), chunk_size):
                yield _anthropic_sse_event("content_block_delta", {
                    "type": "content_block_delta", "index": 0,
                    "delta": {"type": "text_delta", "text": text[i:i + chunk_size]},
                })
            yield _anthropic_sse_event("content_block_stop", {
                "type": "content_block_stop", "index": 0,
            })
            yield _anthropic_sse_event("message_delta", {
                "type": "message_delta",
                "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                "usage": {"output_tokens": len(text) // 4},
            })
            yield _anthropic_sse_event("message_stop", {"type": "message_stop"})

        return StreamingResponse(
            cli_agent_sse_gen(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    # 非ストリーミング
    out = _build_anthropic_response(
        text=text,
        model=body.model,
        input_tokens=len(full_prompt) // 4,
        output_tokens=len(text) // 4,
        message_id=message_id,
    )
    return JSONResponse(content=out)


def _build_anthropic_response(
    *,
    text: str,
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    stop_reason: str = "end_turn",
    message_id: str = "",
) -> dict[str, Any]:
    """非ストリーミング Anthropic Messages API レスポンスを構築."""
    if not message_id:
        message_id = f"msg_{uuid.uuid4().hex[:24]}"
    return {
        "id": message_id,
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": text}],
        "model": model,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        },
    }


def _anthropic_sse_event(event_type: str, data: dict) -> str:
    """Anthropic SSE 形式の1イベントを構築."""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# =============================================================================
# OpenAI Chat Completions (/v1/chat/completions) — 既存 Cursor ブリッジ
# =============================================================================


class ChatMessage(BaseModel):
    role: str
    content: str | list = ""

    @model_validator(mode="before")
    @classmethod
    def _flatten_content(cls, values: Any) -> Any:
        """Cursor は content を [{"type":"text","text":"..."}] 形式で送信する。
        配列形式を文字列に平坦化する。"""
        c = values.get("content", "")
        if isinstance(c, list):
            # テキストパーツだけを結合
            parts = []
            for item in c:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif isinstance(item, str):
                    parts.append(item)
            values["content"] = "\n".join(parts)
        return values


# --- ブリッジデフォルト (Cursor が送らない場合に適用) ---
# Cursor は max_tokens / thinking_budget を送らないことが多いため、
# ブリッジ側で性能最大値をデフォルトとして設定する。
_DEFAULT_MAX_TOKENS = 65536      # CortexClient の DEFAULT_MAX_TOKENS と同値
_DEFAULT_THINKING_BUDGET = 32768  # 思考トークン予算
_DEFAULT_TEMPERATURE = 0.4       # IDE コーディング向けデフォルト

# --- モデル名 → (ルート, 実モデル名, temperature上書き) マッピング ---
# Cursor のドロップダウンに登録するモデル名。
# [Cortex]: = generateContent 直 (LS 不要)
# [LS]:     = LS Cascade ConnectRPC (LS 必要)
# [N.N]     = temperature
_MODEL_REGISTRY: dict[str, dict] = {
    # Cortex 直 (Gemini)
    "[Cortex]:Gemini 3.1 Pro[0.4]":  {"model": "gemini-3.1-pro",  "route": "cortex", "temperature": 0.4},
    "[Cortex]:Gemini 3.1 Pro[0.2]":  {"model": "gemini-3.1-pro",  "route": "cortex", "temperature": 0.2},
    "[Cortex]:Gemini 3.1 Pro[1.0]":  {"model": "gemini-3.1-pro",  "route": "cortex", "temperature": 1.0},
    # LS Cascade (Claude / Gemini)
    "[LS]:Claude Opus 4.6":          {"model": "claude-opus",            "route": "ls"},
    "[LS]:Gemini 3.1 Pro":           {"model": "gemini-3.1-pro",  "route": "ls"},
    # Claude Code CLI (claude -p headless)
    "Claude code":                   {"model": "claude-code",             "route": "claude_code"},
    # CLI Agents (subprocess 経由 — cli_agent_bridge.py)
    "[Copilot]:GPT-5.4 xhigh":       {"model": "copilot:gpt-5.4:xhigh",    "route": "cli_agent"},
    "[Copilot]:GPT-5.4 high":        {"model": "copilot:gpt-5.4:high",     "route": "cli_agent"},
    "[Copilot]:Opus 4.6":            {"model": "copilot",                  "route": "cli_agent"},
    "[Codex]:GPT-5.3 high":          {"model": "codex:gpt-5.3-codex:high", "route": "cli_agent"},
    "[Cursor]:Auto":                  {"model": "cursor-agent:auto",          "route": "cli_agent"},
    "[Cursor]:Composer 2":           {"model": "cursor-agent:composer-2",    "route": "cli_agent"},
    "[Cursor]:Composer 2 Fast":      {"model": "cursor-agent:composer-2-fast", "route": "cli_agent"},
}


class ChatCompletionRequest(BaseModel):
    model: str = Field(default="[Cortex]:Gemini 3.1 Pro[0.4]")
    messages: list[ChatMessage] = Field(default_factory=list)
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False


class CliSmokeRequest(BaseModel):
    tool: str = "all"
    timeout: int = Field(default=30, ge=1, le=300)

    @model_validator(mode="after")
    def _validate_tool(self) -> CliSmokeRequest:
        allowed = {"all", "copilot", "codex", "cursor-agent", "gemini"}
        if self.tool not in allowed:
            raise ValueError(f"tool must be one of: {', '.join(sorted(allowed))}")
        return self


def _messages_to_ask_params(
    messages: list[ChatMessage],
) -> tuple[str | None, str]:
    """Split system prompt vs combined user/assistant transcript for OchemaService.ask."""
    system_parts: list[str] = []
    lines: list[str] = []
    for m in messages:
        r = (m.role or "user").lower()
        c = m.content or ""
        if r == "system":
            system_parts.append(c)
        else:
            lines.append(f"{r}: {c}")
    system_instruction = "\n\n".join(system_parts) if system_parts else None
    message = "\n\n".join(lines) if lines else ""
    return system_instruction, message


def _normalize_model(name: str) -> tuple[str, str, float | None]:
    """Resolve model name to (actual_model, route, temperature_override).

    Returns:
        (model_name, route, temperature_override)
        route: "cortex" or "ls"
        temperature_override: None means use request value or default
    """
    n = (name or "").strip()

    # レジストリに完全一致
    entry = _MODEL_REGISTRY.get(n)
    if entry:
        return entry["model"], entry["route"], entry.get("temperature")

    # 大文字小文字を無視して検索
    for key, entry in _MODEL_REGISTRY.items():
        if key.lower() == n.lower():
            return entry["model"], entry["route"], entry.get("temperature")

    # レガシーエイリアス（旧モデル名からの移行用）
    aliases = {
        "gpt-4": "gemini-3.1-pro-preview",
        "gpt-4o": "gemini-3.1-pro-preview",
        "default": "gemini-3.1-pro-preview",
        "gemini-pro": "gemini-3.1-pro-preview",
        "gemini-flash": "gemini-3-flash-preview",
    }
    aliased = aliases.get(n.lower())
    if aliased:
        route = "ls" if "claude" in aliased else "cortex"
        return aliased, route, None

    # パススルー: claude- → ls, それ以外 → cortex
    route = "ls" if "claude" in n.lower() else "cortex"
    return n, route, None


def _usage_from_response(token_usage: dict[str, Any]) -> dict[str, int]:
    pt = int(token_usage.get("prompt_tokens", 0) or 0)
    ct = int(token_usage.get("completion_tokens", 0) or 0)
    tt = int(token_usage.get("total_tokens", pt + ct) or (pt + ct))
    return {
        "prompt_tokens": pt,
        "completion_tokens": ct,
        "total_tokens": tt,
    }


def _chat_completion_chunk(
    completion_id: str,
    model: str,
    delta: dict[str, Any],
    finish_reason: str | None = None,
) -> dict[str, Any]:
    choice: dict[str, Any] = {"index": 0, "delta": delta}
    if finish_reason is not None:
        choice["finish_reason"] = finish_reason
    return {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [choice],
    }



def create_app() -> FastAPI:
    app = FastAPI(title="HGK OpenAI-compat bridge", version="1.0.0")
    _SLOT_CONFIG = {
        "opus": (_ENV_OPUS_BACKEND, _DEFAULT_OPUS_SPEC),
        "sonnet": (_ENV_SONNET_BACKEND, _DEFAULT_SONNET_SPEC),
        "haiku": (_ENV_HAIKU_BACKEND, _DEFAULT_HAIKU_SPEC),
    }

    # --- デバッグ: リクエストボディログ (422 原因調査用) ---
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request as StarletteRequest

    class _DebugBodyLogger(BaseHTTPMiddleware):
        async def dispatch(self, request: StarletteRequest, call_next):  # type: ignore[override]
            if request.method == "POST" and request.url.path in (
                "/v1/chat/completions", "/v1/messages",
            ):
                body_bytes = await request.body()
                logger.info("RAW_REQUEST_BODY [%s]: %s", request.url.path, body_bytes[:2000].decode("utf-8", errors="replace"))
            resp = await call_next(request)
            return resp

    app.add_middleware(_DebugBodyLogger)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/ls/status")
    async def ls_status(
        _lh: None = Depends(verify_localhost),
        _auth: None = Depends(verify_bearer),
    ) -> dict[str, Any]:
        from mekhane.ochema.service import OchemaService
        svc = OchemaService.get()
        return svc.ls_diagnostic()

    @app.post("/v1/ls/reset")
    async def ls_reset(
        _lh: None = Depends(verify_localhost),
        _auth: None = Depends(verify_bearer),
    ) -> dict[str, Any]:
        from mekhane.ochema.service import OchemaService
        svc = OchemaService.get()
        svc.reset_ls()
        return {"status": "ok", "diagnostic": svc.ls_diagnostic()}

    @app.get("/v1/models")
    async def list_models(
        _lh: None = Depends(verify_localhost),
        _auth: None = Depends(verify_bearer),
    ) -> dict[str, Any]:
        data = []
        for display_name, entry in _MODEL_REGISTRY.items():
            data.append(
                {
                    "id": display_name,
                    "object": "model",
                    "owned_by": "hgk-ochema",
                    "description": f"{entry['route'].upper()}: {entry['model']}",
                }
            )
        return {"object": "list", "data": data, "default": "[Cortex]:Gemini 3.1 Pro[0.4]"}

    def _routing_state() -> dict[str, dict[str, Any]]:
        state: dict[str, dict[str, Any]] = {}
        for slot, (env_key, default_spec) in _SLOT_CONFIG.items():
            current = os.environ.get(env_key, default_spec)
            state[slot] = {
                "current": current,
                "default": default_spec,
                "is_default": current == default_spec,
            }
        return state

    @app.get("/v1/routing")
    async def get_routing(
        _lh: None = Depends(verify_localhost),
        _auth: None = Depends(verify_bearer),
    ) -> dict[str, Any]:
        return {"slots": _routing_state()}

    @app.put("/v1/routing")
    async def put_routing(
        body: dict[str, str],
        _lh: None = Depends(verify_localhost),
        _auth: None = Depends(verify_bearer),
    ) -> dict[str, Any]:
        unknown_slots = sorted(set(body) - set(_SLOT_CONFIG))
        if unknown_slots:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown routing slots: {', '.join(unknown_slots)}",
            )

        before = _routing_state()
        for spec in body.values():
            try:
                _parse_backend_spec(spec)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

        for slot, spec in body.items():
            env_key, _default_spec = _SLOT_CONFIG[slot]
            os.environ[env_key] = spec

        return {"before": before, "after": _routing_state()}

    @app.delete("/v1/routing")
    async def delete_routing(
        _lh: None = Depends(verify_localhost),
        _auth: None = Depends(verify_bearer),
    ) -> dict[str, Any]:
        before = _routing_state()
        for env_key, _default_spec in _SLOT_CONFIG.values():
            os.environ.pop(env_key, None)
        return {"before": before, "after": _routing_state()}

    @app.get("/v1/cli/status")
    async def cli_status(
        smoke: bool = False,
        timeout: int = 30,
        _lh: None = Depends(verify_localhost),
        _auth: None = Depends(verify_bearer),
    ) -> dict[str, Any]:
        from mekhane.ochema.cli_agent_bridge import status

        if timeout < 1 or timeout > 300:
            raise HTTPException(status_code=400, detail="timeout must be between 1 and 300")
        return {
            "status": "ok",
            "tools": status(run_smoke=smoke, smoke_timeout=timeout),
        }

    @app.post("/v1/cli/smoke")
    async def cli_smoke(
        body: CliSmokeRequest,
        _lh: None = Depends(verify_localhost),
        _auth: None = Depends(verify_bearer),
    ) -> dict[str, Any]:
        from mekhane.ochema.cli_agent_bridge import smoke

        tools = ("copilot", "codex", "cursor-agent", "gemini")
        if body.tool == "all":
            result = {tool: smoke(tool, timeout=body.timeout) for tool in tools}
        else:
            result = smoke(body.tool, timeout=body.timeout)
        return {"status": "ok", "result": result}

    @app.post("/v1/chat/completions", response_model=None)
    async def chat_completions(
        body: ChatCompletionRequest,
        _lh: None = Depends(verify_localhost),
        _auth: None = Depends(verify_bearer),
    ) -> JSONResponse | StreamingResponse:
        from mekhane.ochema.service import OchemaService

        model, route, temp_override = _normalize_model(body.model)
        sys_inst, message = _messages_to_ask_params(body.messages)
        if not message.strip():
            raise HTTPException(status_code=400, detail="No user/assistant content in messages")

        svc = OchemaService.get()
        # temperature: モデルレジストリの上書き > リクエスト値 > デフォルト
        temperature = temp_override if temp_override is not None else (body.temperature or _DEFAULT_TEMPERATURE)
        max_tokens = body.max_tokens or _DEFAULT_MAX_TOKENS
        thinking_budget = _DEFAULT_THINKING_BUDGET

        # アカウントラウンドロビン: account_router で quota 分散
        try:
            from mekhane.ochema.account_router import get_account_for
            account = get_account_for("cursor")
        except ImportError as _e:
            logger.debug("Ignored exception: %s", _e)
            account = "default"

        # --- cli_agent: Copilot / Codex / Cursor Agent subprocess ---
        if route == "cli_agent":
            from mekhane.ochema.cli_agent_bridge import run_cli_agent

            full_prompt = f"{sys_inst}\n\n{message}" if sys_inst else message
            # internal_model からツールとモデルを決定 (形式: "tool" or "tool:model")
            if ":" in model:
                cli_tool, cli_model = model.split(":", 1)
                cli_model = cli_model or None
            else:
                cli_tool = model  # "copilot" or "codex"
                cli_model = None

            logger.info("CLI Agent handler (OpenAI): tool=%s model=%s", cli_tool, cli_model)
            result = await asyncio.to_thread(
                run_cli_agent, full_prompt, tool=cli_tool, model=cli_model, timeout=300,
            )
            if result.get("status") != "ok":
                raise HTTPException(status_code=502, detail=result.get("error", "CLI agent failed"))

            text = result.get("output", "")
            completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
            if body.stream:
                def cli_sse_gen() -> Iterator[str]:
                    yield "data: " + json.dumps(
                        _chat_completion_chunk(completion_id, model, {"role": "assistant", "content": ""}),
                        ensure_ascii=False,
                    ) + "\n\n"
                    yield "data: " + json.dumps(
                        _chat_completion_chunk(completion_id, model, {"content": text}),
                        ensure_ascii=False,
                    ) + "\n\n"
                    yield "data: " + json.dumps(
                        _chat_completion_chunk(completion_id, model, {}, finish_reason="stop"),
                        ensure_ascii=False,
                    ) + "\n\n"
                    yield "data: [DONE]\n\n"
                return StreamingResponse(cli_sse_gen(), media_type="text/event-stream")

            out = {
                "id": completion_id,
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": len(full_prompt) // 4, "completion_tokens": len(text) // 4, "total_tokens": (len(full_prompt) + len(text)) // 4},
            }
            return JSONResponse(content=out)

        # --- ルート分岐: route == "ls" → LS Cascade (ConnectRPC) 経由 ---
        # LS は Cortex API (cloudcode-pa) とは別のルートで LLM に到達する。
        # Cortex が 429 でも LS 経由なら動作する。
        if route == "ls":
            try:
                resp = await _async_ask_ls(
                    svc,
                    message=message,
                    model=model,
                    system_instruction=sys_inst,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    thinking_budget=thinking_budget,
                    timeout=120.0,
                )
            except Exception as e:  # noqa: BLE001
                logger.exception("LS ask failed: %s", e)
                diag = svc.ls_diagnostic()
                detail = f"LS connection failed ({e}). Diagnostic: {diag}"
                raise HTTPException(status_code=502, detail=detail) from e

            completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
            if body.stream:
                # LS はストリーミング非対応のため、全体を1チャンクで SSE に変換
                def ls_sse_gen() -> Iterator[str]:
                    yield "data: " + json.dumps(
                        _chat_completion_chunk(completion_id, model, {"role": "assistant", "content": ""}),
                        ensure_ascii=False,
                    ) + "\n\n"
                    yield "data: " + json.dumps(
                        _chat_completion_chunk(completion_id, model, {"content": resp.text or ""}),
                        ensure_ascii=False,
                    ) + "\n\n"
                    yield "data: " + json.dumps(
                        _chat_completion_chunk(completion_id, model, {}, finish_reason="stop"),
                        ensure_ascii=False,
                    ) + "\n\n"
                    yield "data: [DONE]\n\n"

                return StreamingResponse(ls_sse_gen(), media_type="text/event-stream")

            out = {
                "id": completion_id,
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": resp.text or ""}, "finish_reason": "stop"}],
                "usage": _usage_from_response(resp.token_usage or {}),
            }
            return JSONResponse(content=out)

        if body.stream:

            def sync_gen() -> Iterator[str]:
                completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
                # Role chunk (OpenAI-style first chunk often has role)
                yield (
                    "data: "
                    + json.dumps(
                        _chat_completion_chunk(
                            completion_id,
                            model,
                            {"role": "assistant", "content": ""},
                        ),
                        ensure_ascii=False,
                    )
                    + "\n\n"
                )
                try:
                    for piece in svc.stream(
                        message,
                        model=model,
                        system_instruction=sys_inst,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        thinking_budget=thinking_budget,
                        account=account,
                    ):
                        if piece:
                            yield (
                                "data: "
                                + json.dumps(
                                    _chat_completion_chunk(
                                        completion_id,
                                        model,
                                        {"content": piece},
                                    ),
                                    ensure_ascii=False,
                                )
                                + "\n\n"
                            )
                except Exception as e:  # noqa: BLE001
                    logger.exception("stream failed: %s", e)
                    err = {"error": {"message": str(e), "type": "server_error"}}
                    yield "data: " + json.dumps(err, ensure_ascii=False) + "\n\n"
                    return
                yield (
                    "data: "
                    + json.dumps(
                        _chat_completion_chunk(
                            completion_id,
                            model,
                            {},
                            finish_reason="stop",
                        ),
                        ensure_ascii=False,
                    )
                    + "\n\n"
                )
                yield "data: [DONE]\n\n"

            return StreamingResponse(sync_gen(), media_type="text/event-stream")

        try:
            resp = svc.ask(
                message,
                model=model,
                system_instruction=sys_inst,
                temperature=temperature,
                max_tokens=max_tokens,
                thinking_budget=thinking_budget,
                account=account,
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("ask failed: %s", e)
            raise HTTPException(status_code=502, detail=str(e)) from e

        completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
        out = {
            "id": completion_id,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": resp.text or ""},
                    "finish_reason": "stop",
                }
            ],
            "usage": _usage_from_response(resp.token_usage or {}),
        }
        return JSONResponse(content=out)

    # =================================================================
    # POST /v1/messages — Anthropic Messages API ブリッジ
    # =================================================================
    # Claude Code が ANTHROPIC_BASE_URL 経由で全リクエストをここに送る。
    # model フィールドで LS (Claude) / Cortex (Gemini) にルーティング。

    @app.post("/v1/messages", response_model=None)
    async def anthropic_messages(
        body: AnthropicMessagesRequest,
        _lh: None = Depends(verify_localhost),
        _auth: None = Depends(verify_anthropic_auth),
    ) -> JSONResponse | StreamingResponse:
        from mekhane.ochema.service import OchemaService

        internal_model, route = _normalize_anthropic_model(body.model)
        sys_inst, message = _anthropic_messages_to_ask_params(
            body.messages, body.system,
        )
        if not message.strip():
            raise HTTPException(status_code=400, detail="No user/assistant content in messages")

        # --- anthropic_passthrough: 実 Anthropic API にリクエストをそのまま転送 ---
        if route == "anthropic_passthrough":
            return await _anthropic_passthrough(body)

        # --- gemini_cli: Gemini CLI subprocess (blocking → asyncio.to_thread) ---
        if route == "gemini_cli":
            return await _gemini_cli_handler(body, internal_model)

        # --- cli_agent: Copilot / Codex / Cursor Agent subprocess ---
        if route == "cli_agent":
            return await _cli_agent_handler(body, internal_model)

        # --- cli_agent_smart: system prompt から Copilot/Codex 自動分岐 ---
        if route == "cli_agent_smart":
            return await _cli_agent_handler(body, internal_model, smart_route=True)

        svc = OchemaService.get()
        temperature = body.temperature or _DEFAULT_TEMPERATURE
        max_tokens = body.max_tokens or _DEFAULT_MAX_TOKENS

        # thinking パラメータの抽出
        thinking_budget = _DEFAULT_THINKING_BUDGET
        if body.thinking and isinstance(body.thinking, dict):
            if body.thinking.get("type") == "enabled":
                thinking_budget = body.thinking.get("budget_tokens", _DEFAULT_THINKING_BUDGET)

        logger.info(
            "Anthropic /v1/messages: model=%s → internal=%s route=%s stream=%s",
            body.model, internal_model, route, body.stream,
        )

        message_id = f"msg_{uuid.uuid4().hex[:24]}"

        if body.stream:
            # --- LS: 先に to_thread で応答を取り、SSE はチャンク送出のみ（同期ジェネレータ内で _ask_ls しない）---
            if route == "ls":
                try:
                    ls_resp = await _async_ask_ls(
                        svc,
                        message=message,
                        model=internal_model,
                        system_instruction=sys_inst,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        thinking_budget=thinking_budget,
                        timeout=120.0,
                    )
                except Exception as e:  # noqa: BLE001
                    logger.exception("Anthropic LS stream prefetch failed: %s", e)
                    raise HTTPException(status_code=502, detail=str(e)) from e

                text = ls_resp.text or ""
                total_prefetch = int(
                    (getattr(ls_resp, "token_usage", {}) or {}).get("completion_tokens", 0)
                    or (len(text) // 4)
                )

                def anthropic_sse_ls() -> Iterator[str]:
                    yield _anthropic_sse_event("message_start", {
                        "type": "message_start",
                        "message": {
                            "id": message_id,
                            "type": "message",
                            "role": "assistant",
                            "content": [],
                            "model": body.model,
                            "stop_reason": None,
                            "stop_sequence": None,
                            "usage": {"input_tokens": 0, "output_tokens": 0},
                        },
                    })
                    yield _anthropic_sse_event("content_block_start", {
                        "type": "content_block_start",
                        "index": 0,
                        "content_block": {"type": "text", "text": ""},
                    })
                    chunk_size = 100
                    for i in range(0, len(text), chunk_size):
                        chunk = text[i:i + chunk_size]
                        yield _anthropic_sse_event("content_block_delta", {
                            "type": "content_block_delta",
                            "index": 0,
                            "delta": {"type": "text_delta", "text": chunk},
                        })
                    yield _anthropic_sse_event("content_block_stop", {
                        "type": "content_block_stop",
                        "index": 0,
                    })
                    yield _anthropic_sse_event("message_delta", {
                        "type": "message_delta",
                        "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                        "usage": {"output_tokens": total_prefetch},
                    })
                    yield _anthropic_sse_event("message_stop", {"type": "message_stop"})

                return StreamingResponse(
                    anthropic_sse_ls(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                    },
                )

            # --- Cortex: 真のストリーミング（同期ジェネレータ内で stream）---
            def anthropic_sse_gen() -> Iterator[str]:
                yield _anthropic_sse_event("message_start", {
                    "type": "message_start",
                    "message": {
                        "id": message_id,
                        "type": "message",
                        "role": "assistant",
                        "content": [],
                        "model": body.model,
                        "stop_reason": None,
                        "stop_sequence": None,
                        "usage": {"input_tokens": 0, "output_tokens": 0},
                    },
                })

                yield _anthropic_sse_event("content_block_start", {
                    "type": "content_block_start",
                    "index": 0,
                    "content_block": {"type": "text", "text": ""},
                })

                total_output_tokens = 0
                try:
                    for piece in svc.stream(
                        message,
                        model=internal_model,
                        system_instruction=sys_inst,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        thinking_budget=thinking_budget,
                    ):
                        if piece:
                            total_output_tokens += len(piece) // 4  # 概算
                            yield _anthropic_sse_event("content_block_delta", {
                                "type": "content_block_delta",
                                "index": 0,
                                "delta": {"type": "text_delta", "text": piece},
                            })
                except Exception as e:  # noqa: BLE001
                    logger.exception("Anthropic stream failed: %s", e)
                    yield _anthropic_sse_event("content_block_delta", {
                        "type": "content_block_delta",
                        "index": 0,
                        "delta": {"type": "text_delta", "text": f"\n\n[Bridge Error: {e}]"},
                    })

                yield _anthropic_sse_event("content_block_stop", {
                    "type": "content_block_stop",
                    "index": 0,
                })

                yield _anthropic_sse_event("message_delta", {
                    "type": "message_delta",
                    "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                    "usage": {"output_tokens": total_output_tokens},
                })

                yield _anthropic_sse_event("message_stop", {
                    "type": "message_stop",
                })

            return StreamingResponse(
                anthropic_sse_gen(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            )

        # --- 非ストリーミング ---
        try:
            if route == "ls":
                resp = await _async_ask_ls(
                    svc,
                    message=message,
                    model=internal_model,
                    system_instruction=sys_inst,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    thinking_budget=thinking_budget,
                    timeout=120.0,
                )
            else:
                resp = svc.ask(
                    message,
                    model=internal_model,
                    system_instruction=sys_inst,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    thinking_budget=thinking_budget,
                )
        except Exception as e:  # noqa: BLE001
            logger.exception("Anthropic ask failed: %s", e)
            if route == "ls":
                diag = svc.ls_diagnostic()
                detail = f"LS connection failed ({e}). Diagnostic: {diag}"
            else:
                detail = str(e)
            raise HTTPException(status_code=502, detail=detail) from e

        # token usage を取得
        token_usage = getattr(resp, "token_usage", {}) or {}
        input_tokens = int(token_usage.get("prompt_tokens", 0) or 0)
        output_tokens = int(token_usage.get("completion_tokens", 0) or 0)

        out = _build_anthropic_response(
            text=resp.text or "",
            model=body.model,  # リクエスト時のモデル名を返す (Claude Code の期待)
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            message_id=message_id,
        )
        return JSONResponse(content=out)

    return app


app = create_app()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    import uvicorn

    host = os.environ.get(_ENV_HOST, "127.0.0.1")
    port = int(os.environ.get(_ENV_PORT, "8765"))
    if not _expected_bearer():
        logger.error("Set %s before starting (same value as Cursor API Key)", _ENV_TOKEN)
        raise SystemExit(1)
    logger.info("OpenAI-compat bridge on http://%s:%s (token from %s)", host, port, _ENV_TOKEN)
    logger.info(
        "CC subagent routing: opus=%s, sonnet=%s, haiku=%s",
        os.environ.get(_ENV_OPUS_BACKEND, "anthropic_passthrough (default)"),
        os.environ.get(_ENV_SONNET_BACKEND, "cli_agent_smart:gpt-5.4 (default)"),
        os.environ.get(_ENV_HAIKU_BACKEND, "gemini_cli:gemini-3.1-pro-preview (default)"),
    )
    uvicorn.run(
        "mekhane.ochema.openai_compat_server:app",
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
