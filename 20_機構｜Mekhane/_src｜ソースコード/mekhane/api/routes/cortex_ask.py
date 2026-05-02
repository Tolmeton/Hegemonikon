from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/api/routes/
# PURPOSE: Cortex Ask — LLM 問い合わせプロキシ (非ストリーミング＋SSE ストリーミング)


import asyncio
import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from mekhane.ochema.model_defaults import FLASH

logger = logging.getLogger(__name__)

router = APIRouter(tags=["cortex-ask"])


@router.get("/api/health")
async def health_check():
    """Health check — Dashboard / hgk-cli.sh 接続確認用."""
    return {"status": "ok", "service": "hgk-api"}

# Singleton CortexClient
_client = None


def _get_client():
    global _client
    if _client is None:
        from mekhane.ochema.cortex_client import CortexClient
        _client = CortexClient()
    return _client


@router.post("/api/ask")
async def ask(request: Request):
    """Simple ask endpoint — non-streaming."""
    body = await request.json()
    message = body.get("message", "")
    model = body.get("model", FLASH)

    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    try:
        client = _get_client()
        result = await asyncio.to_thread(
            client.ask, message=message, model=model
        )
        return {"text": result.text, "model": result.model}
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/api/ask/stream")
async def ask_stream(request: Request):
    """SSE streaming endpoint — true token-by-token streaming via CortexClient."""
    body = await request.json()
    message = body.get("message", "")
    model = body.get("model", FLASH)
    system_instruction = body.get("system_instruction")
    temperature = body.get("temperature")
    max_tokens = body.get("max_tokens")
    thinking_budget = body.get("thinking_budget")

    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    async def event_generator():
        try:
            client = _get_client()
            kwargs: dict = dict(message=message, model=model)
            if system_instruction:
                kwargs["system_instruction"] = system_instruction
            if temperature is not None:
                kwargs["temperature"] = float(temperature)
            if max_tokens is not None:
                kwargs["max_tokens"] = int(max_tokens)
            if thinking_budget is not None:
                kwargs["thinking_budget"] = int(thinking_budget)

            q: asyncio.Queue = asyncio.Queue()
            loop = asyncio.get_running_loop()

            def _stream_worker():
                import time as _time
                from mekhane.ochema.service import OchemaService

                max_retries = 2
                svc = OchemaService.get()
                is_claude = svc._is_claude_model(model)

                for retry in range(max_retries + 1):
                    try:
                        if is_claude:
                            config_id = svc._resolve_model_config_id(model)
                            resp = svc.chat(
                                message=message,
                                model=config_id,
                                tier_id="g1-ultra-tier",
                                thinking_budget=kwargs.get("thinking_budget"),
                            )
                            if resp.thinking:
                                loop.call_soon_threadsafe(
                                    q.put_nowait,
                                    ("thinking", resp.thinking),
                                )
                            if resp.text:
                                loop.call_soon_threadsafe(q.put_nowait, ("chunk", resp.text))
                            actual_model = resp.model or model
                            # done イベントに thinking メタデータを含める
                            done_meta = {
                                "model": actual_model,
                                "thinking_duration": resp.thinking_duration,
                                "stop_reason": resp.stop_reason,
                                "message_id": resp.message_id,
                            }
                            loop.call_soon_threadsafe(q.put_nowait, ("done_meta", done_meta))
                        else:
                            for chunk in svc.stream(**kwargs):
                                if chunk.startswith("__THINKING__:"):
                                    thinking = chunk[len("__THINKING__:"):]
                                    loop.call_soon_threadsafe(
                                        q.put_nowait,
                                        ("thinking", thinking),
                                    )
                                else:
                                    loop.call_soon_threadsafe(q.put_nowait, ("chunk", chunk))
                            loop.call_soon_threadsafe(q.put_nowait, ("done_meta", {"model": model}))
                        return
                    except Exception as exc:  # noqa: BLE001
                        err_msg = str(exc)
                        if retry < max_retries and ("429" in err_msg or "503" in err_msg or "500" in err_msg):
                            wait = (retry + 1) * 3
                            loop.call_soon_threadsafe(
                                q.put_nowait,
                                ("chunk", f"\n\n*⏳ レート制限 — {wait}秒後にリトライ...*\n\n"),
                            )
                            _time.sleep(wait)
                            continue
                        loop.call_soon_threadsafe(q.put_nowait, ("error", err_msg))
                        return

            loop.run_in_executor(None, _stream_worker)

            while True:
                kind, data = await q.get()
                if kind == "chunk":
                    yield f"data: {json.dumps({'text': data, 'done': False})}\n\n"
                elif kind == "thinking":
                    yield f"data: {json.dumps({'thinking': data, 'done': False})}\n\n"
                elif kind == "done_meta":
                    yield f"data: {json.dumps({'text': '', 'done': True, **data})}\n\n"
                    break
                elif kind == "error":
                    yield f"data: {json.dumps({'error': data, 'done': True})}\n\n"
                    break
        except Exception as e:  # noqa: BLE001
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
