from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/api/routes/
# PURPOSE: Jules API — 非同期コーディングエージェント統合


import asyncio
import json
import logging
import threading

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["jules"])


def _get_jules_client():
    from hgk.api.jules_client import get_jules_client
    return get_jules_client()


@router.get("/api/jules/sources")
async def jules_sources():
    """List available GitHub sources for Jules."""
    try:
        client = _get_jules_client()
        if not client.available:
            return JSONResponse({"error": "No Jules API keys configured"}, status_code=503)
        sources = await asyncio.to_thread(client.list_sources)
        return {"sources": sources}
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/api/jules/sessions")
async def jules_sessions(page_size: int = 20):
    """List recent Jules sessions."""
    try:
        client = _get_jules_client()
        sessions = await asyncio.to_thread(client.list_sessions, page_size)
        return {"sessions": sessions}
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/api/jules/sessions/{session_id}")
async def jules_session_detail(session_id: str):
    """Get Jules session details."""
    try:
        client = _get_jules_client()
        session = await asyncio.to_thread(client.get_session, session_id)
        return session
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/api/jules/sessions")
async def jules_create_session(request: Request):
    """Create a new Jules coding session."""
    body = await request.json()
    prompt = body.get("prompt", "")
    source = body.get("source", "")
    if not prompt or not source:
        return JSONResponse({"error": "prompt and source are required"}, status_code=400)
    try:
        client = _get_jules_client()
        session = await asyncio.to_thread(
            client.create_session,
            prompt=prompt,
            source=source,
            title=body.get("title", ""),
            branch=body.get("branch", "main"),
            require_plan_approval=body.get("require_plan_approval", False),
        )
        return session
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/api/jules/sessions/{session_id}/approve")
async def jules_approve_plan(session_id: str):
    """Approve a pending Jules plan."""
    try:
        client = _get_jules_client()
        result = await asyncio.to_thread(client.approve_plan, session_id)
        return result
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/api/jules/sessions/{session_id}/message")
async def jules_send_message(session_id: str, request: Request):
    """Send a follow-up message to an active Jules session."""
    body = await request.json()
    message = body.get("message", "")
    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)
    try:
        client = _get_jules_client()
        result = await asyncio.to_thread(client.send_message, session_id, message)
        return result
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/api/jules/sessions/{session_id}/activities")
async def jules_activities(session_id: str, page_size: int = 50):
    """List activities for a Jules session."""
    try:
        client = _get_jules_client()
        activities = await asyncio.to_thread(client.list_activities, session_id, page_size)
        return {"activities": activities}
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/api/jules/sessions/{session_id}/poll")
async def jules_poll_session(session_id: str):
    """SSE endpoint to poll a Jules session until completion."""
    async def event_generator():
        client = _get_jules_client()
        q: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def _poll_worker():
            try:
                def _cb(sess: dict):
                    loop.call_soon_threadsafe(q.put_nowait, ("status", sess))

                final = client.poll_session(session_id, interval=5.0, max_wait=600.0, callback=_cb)
                loop.call_soon_threadsafe(q.put_nowait, ("done", final))
            except Exception as exc:  # noqa: BLE001
                loop.call_soon_threadsafe(q.put_nowait, ("error", {"error": str(exc)}))

        threading.Thread(target=_poll_worker, daemon=True).start()

        while True:
            kind, data = await asyncio.wait_for(q.get(), timeout=620.0)
            is_done = kind in ("done", "error")
            yield f"data: {json.dumps({'type': kind, 'data': data, 'done': is_done}, ensure_ascii=False)}\n\n"
            if is_done:
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")
