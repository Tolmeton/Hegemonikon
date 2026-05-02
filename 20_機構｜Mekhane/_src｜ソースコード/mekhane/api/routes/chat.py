from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/api/routes/
# PURPOSE: Chat API — OchemaService 経由の統合 LLM Chat プロキシ
"""
Chat Router — LLM Chat の REST API エンドポイント

エンドポイント:
  POST /chat/send    — メッセージ送信 (SSE ストリーミング)
  POST /chat/cortex  — Cortex generateChat (無課金 Gemini 2MB)
  GET  /chat/models  — 利用可能なモデル一覧 (LS 接続状態含む)

消費者として OchemaService に委譲し、SSE フォーマット変換のみ担う。
"""


import json
import logging
import os
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from mekhane.ochema.service import (
    AVAILABLE_MODELS,
    CLAUDE_MODEL_MAP,
    OchemaService,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


# --- Models ---


# PURPOSE: [L2-auto] ChatContent のクラス定義
class ChatContent(BaseModel):
    """Single message content."""
    role: str
    parts: list[dict[str, str]]


# PURPOSE: [L2-auto] ChatRequest のクラス定義
class ChatRequest(BaseModel):
    """Chat send request."""
    model: str = "gemini-3.1-pro-preview"
    contents: list[ChatContent]
    system_instruction: dict[str, Any] | None = None
    generation_config: dict[str, Any] = Field(
        default_factory=lambda: {
            "temperature": 0.7,
            "maxOutputTokens": 65536,
        }
    )


# PURPOSE: [L2-auto] CortexChatMessage のクラス定義
class CortexChatMessage(BaseModel):
    """Cortex generateChat history message."""
    author: int  # 1 = USER, 2 = MODEL
    content: str


# PURPOSE: [L2-auto] CortexChatRequest のクラス定義
class CortexChatRequest(BaseModel):
    """Cortex generateChat request."""
    user_message: str
    history: list[CortexChatMessage] = []
    model_config_id: str = ""  # empty = server default (Gemini), e.g. "claude-sonnet-4-6"
    tier_id: str = ""  # empty = Gemini default
    include_thinking_summaries: bool = False


GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
CORTEX_CHAT_URL = "https://cloudcode-pa.googleapis.com/v1internal:generateChat"
CORTEX_STREAM_URL = "https://cloudcode-pa.googleapis.com/v1internal:streamGenerateChat"


# PURPOSE: [L2-auto] _get_api_key の関数定義
def _get_api_key() -> str:
    """Gemini API キーを環境変数から取得する。"""
    key = os.getenv("HGK_GEMINI_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    if not key:
        key = os.getenv("VITE_GOOGLE_API_KEY", "")
    return key


# --- Endpoints ---


# PURPOSE: [L2-auto] chat_send の非同期処理定義
@router.post("/chat/send")
async def chat_send(req: ChatRequest):
    """全モデルを Cortex 経由で処理し、SSE をフロントに流す。

    Claude モデル → model_config_id 指定で Cortex に送信
    Gemini モデル → Cortex generateChat (TokenVault 認証)
    """
    logger.info("Incoming chat_send request: %s", req.model_dump_json())
    
    # Claude モデルの場合は model_config_id を指定
    if req.model in CLAUDE_MODEL_MAP:
        return await _cortex_chat_from_gemini_format(
            req, model_config_id=CLAUDE_MODEL_MAP[req.model],
        )

    # 全 Gemini モデル (cortex-chat 含む) → Cortex 経由
    return await _cortex_chat_from_gemini_format(req)


# PURPOSE: [L2-auto] _cortex_chat_from_gemini_format の非同期処理定義
async def _cortex_chat_from_gemini_format(
    req: ChatRequest,
    model_config_id: str = "",
):
    """Gemini 形式の ChatRequest を Cortex に変換して実行する。"""
    import asyncio
    svc = OchemaService.get()
    
    contents = []
    for content in req.contents:
        text = content.parts[0].get("text", "") if content.parts else ""
        contents.append({"role": content.role, "parts": [{"text": text}]})

    system_instruction = None
    if req.system_instruction:
        sys_parts = req.system_instruction.get("parts", [])
        if sys_parts:
            system_instruction = sys_parts[0].get("text", "")

    model = model_config_id or req.model

    logger.info(
        "Cortex Chat request: model=%s history=%d",
        model, len(contents)
    )

    # PURPOSE: [L2-auto] stream_cortex の非同期処理定義
    async def stream_cortex():
        try:
            cortex = svc._get_cortex_client()
            queue: asyncio.Queue[str | None] = asyncio.Queue()
            
            loop = asyncio.get_running_loop()

            # PURPOSE: [L2-auto] _worker の関数定義
            def _worker():
                try:
                    for chunk in cortex.ask_stream(
                        model=model,
                        contents=contents,
                        system_instruction=system_instruction,
                        temperature=req.generation_config.get("temperature", 0.7),
                        max_tokens=req.generation_config.get("maxOutputTokens", 65536),
                    ):
                        loop.call_soon_threadsafe(queue.put_nowait, chunk)
                except Exception as e:  # noqa: BLE001
                    logger.error("stream_cortex _worker error: %s", e)
                    loop.call_soon_threadsafe(queue.put_nowait, f"__ERROR__:{e}")
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, None)

            loop.run_in_executor(None, _worker)
            
            while True:
                chunk = await queue.get()
                if chunk is None:
                    break
                if isinstance(chunk, str) and chunk.startswith("__ERROR__:"):
                    err_msg = chunk[len("__ERROR__:"):]
                    yield f"data: {json.dumps({'error': {'message': err_msg, 'code': 500}})}\n\n"
                    return

                gemini_compat = {
                    "candidates": [{
                        "content": {
                            "parts": [{"text": chunk}],
                            "role": "model",
                        },
                        "finishReason": "STOP",
                    }]
                }
                yield f"data: {json.dumps(gemini_compat)}\n\n"

        except Exception as e:  # noqa: BLE001
            logger.error("Cortex chat stream error: %s", e)
            yield f"data: {json.dumps({'error': {'message': str(e), 'code': 500}})}\n\n"

    return StreamingResponse(
        stream_cortex(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# PURPOSE: [L2-auto] chat_models の非同期処理定義
@router.get("/chat/models")
async def chat_models() -> dict[str, Any]:
    """利用可能なモデル一覧を返す。OchemaService に委譲。"""
    svc = OchemaService.get()
    return svc.models()
