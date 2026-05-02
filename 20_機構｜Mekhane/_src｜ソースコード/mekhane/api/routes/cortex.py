# PROOF: mekhane/api/routes/cortex.py
# PURPOSE: api モジュールの cortex
from typing import Any, AsyncGenerator

import asyncio
import json
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from mekhane.ochema.service import OchemaService
from mekhane.ochema.model_defaults import FLASH

logger = logging.getLogger("hegemonikon.api.cortex")

router = APIRouter(prefix="/api/cortex", tags=["Cortex"])


# PURPOSE: [L2-auto] health の非同期処理定義
@router.get("/health")
async def health():
    """Health check for Cortex Proxy."""
    return {"status": "ok", "service": "hgk-desktop-api-cortex"}


# PURPOSE: [L2-auto] ask の非同期処理定義
@router.post("/ask")
async def ask(request: Request):
    """Simple ask endpoint — non-streaming."""
    body = await request.json()
    message = body.get("message", "")
    model = body.get("model", FLASH)

    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    try:
        svc = OchemaService.get()
        result = await svc.ask_async(message=message, model=model)
        return {"text": result.text, "model": result.model}
    except Exception as e:  # noqa: BLE001
        logger.error("Cortex API error (ask): %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


# PURPOSE: [L2-auto] ask_stream の非同期処理定義
@router.post("/ask/stream")
async def ask_stream(request: Request):
    """SSE streaming endpoint — OchemaService.stream() で自動ルーティング。

    Claude モデル → CortexClient.chat_stream() (streamGenerateChat)
    Gemini モデル → CortexClient.ask_stream() (generateContent streaming)
    """
    body = await request.json()
    message = body.get("message", "")
    model = body.get("model", FLASH)
    system_instruction = body.get("system_instruction")
    temperature = body.get("temperature")
    max_tokens = body.get("max_tokens")
    thinking_budget = body.get("thinking_budget")

    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    # PURPOSE: [L2-auto] event_generator の非同期処理定義
    async def event_generator() -> AsyncGenerator[str, Any]:
        try:
            svc = OchemaService.get()
            kwargs: dict[str, Any] = dict(message=message, model=model)
            if system_instruction: kwargs["system_instruction"] = system_instruction
            if temperature is not None: kwargs["temperature"] = float(temperature)
            if max_tokens is not None: kwargs["max_tokens"] = int(max_tokens)
            if thinking_budget is not None: kwargs["thinking_budget"] = int(thinking_budget)

            # Bridge sync generator → async via Queue
            queue: asyncio.Queue[str | None] = asyncio.Queue()

            # PURPOSE: [L2-auto] _stream_worker の関数定義
            def _stream_worker():
                try:
                    chunk_count = 0
                    thinking_count = 0
                    for chunk in svc.stream(**kwargs):
                        chunk_count += 1
                        if isinstance(chunk, str) and chunk.startswith("__THINKING__:"):
                            thinking_count += 1
                            logger.info("stream_worker: thinking chunk #%d received (len=%d)", thinking_count, len(chunk))
                        queue.put_nowait(chunk)
                    logger.info("stream_worker: completed. total_chunks=%d thinking_chunks=%d", chunk_count, thinking_count)
                except Exception as e:  # noqa: BLE001
                    logger.error("stream_worker: error: %s", e)
                    queue.put_nowait(f"__ERROR__:{e}")
                finally:
                    queue.put_nowait(None)  # sentinel

            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, _stream_worker)

            while True:
                chunk = await queue.get()
                if chunk is None:
                    break
                if isinstance(chunk, str) and chunk.startswith("__ERROR__:"):
                    err_msg = chunk[len("__ERROR__:"):]
                    yield f"data: {json.dumps({'error': f'Stream failed: {err_msg}', 'done': True})}\n\n"
                    return
                if isinstance(chunk, str) and chunk.startswith("__THINKING__:"):
                    thinking_text = chunk[len("__THINKING__:"):]
                    yield f"data: {json.dumps({'thinking': thinking_text, 'done': False})}\n\n"
                else:
                    yield f"data: {json.dumps({'text': chunk, 'done': False})}\n\n"
            yield f"data: {json.dumps({'text': '', 'done': True, 'model': model})}\n\n"
        except Exception as e:  # noqa: BLE001
            logger.error("Cortex API error (stream): %s", e)
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
