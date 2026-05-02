from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/api/routes/
# PURPOSE: IDE ConnectRPC + Push SSE + Gateway Trace — HGK 内部情報アクセス


import asyncio
import json
import logging
import threading
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ide"])


# ============================================================
# IDE ConnectRPC endpoints
# ============================================================

@router.get("/api/hgk/ide/status")
async def ide_status():
    """IDE 接続ステータス (PID / Port / 接続状態)"""
    try:
        from hgk.api.ls_client import get_ide_status
        return await asyncio.to_thread(get_ide_status)
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": str(e)}


@router.get("/api/hgk/ide/workflows")
async def ide_workflows():
    """IDE 内部ワークフロー一覧"""
    try:
        from hgk.api.ls_client import call_ls
        return await asyncio.to_thread(call_ls, "GetAllWorkflows")
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/api/hgk/ide/memories")
async def ide_memories():
    """IDE ユーザーメモリー"""
    try:
        from hgk.api.ls_client import call_ls
        return await asyncio.to_thread(call_ls, "GetUserMemories")
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/api/hgk/ide/trajectories")
async def ide_trajectories():
    """IDE 会話トラジェクトリ"""
    try:
        from hgk.api.ls_client import call_ls
        return await asyncio.to_thread(call_ls, "GetAllCascadeTrajectories")
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


# ============================================================
# Gateway Trace — Cowork Dashboard data source
# ============================================================

@router.get("/api/hgk/gateway/trace")
async def gateway_trace(limit: int = 100):
    """Read recent Gateway tool traces from gateway_trace.jsonl."""
    try:
        from mekhane.paths import MNEME_DIR as mneme_dir
        trace_file = mneme_dir / "gateway_trace.jsonl"
        if not trace_file.exists():
            return {"traces": []}
        lines = trace_file.read_text(errors="replace").strip().split("\n")
        traces = []
        for line in lines[-limit:]:
            if line.strip():
                try:
                    traces.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return {"traces": traces}
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


# ============================================================
# Push SSE — Autophōnos proactive notifications
# ============================================================

@router.get("/api/push/stream")
async def push_stream():
    """SSE endpoint for Dashboard push notifications."""
    async def event_generator():
        q: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def _push_worker():
            try:
                from mekhane.mcp import hgk_gateway as gw
                result = gw.hgk_proactive_push(topics="", max_results=5, use_advocacy=True)
                loop.call_soon_threadsafe(q.put_nowait, ("push", {"result": result}))
            except Exception as exc:  # noqa: BLE001
                loop.call_soon_threadsafe(q.put_nowait, ("error", {"error": str(exc)}))
            finally:
                loop.call_soon_threadsafe(q.put_nowait, ("done", {}))

        threading.Thread(target=_push_worker, daemon=True).start()

        while True:
            event_type, data = await asyncio.wait_for(q.get(), timeout=120.0)
            payload = json.dumps({"type": event_type, **data, "done": event_type == "done"}, ensure_ascii=False)
            yield f"data: {payload}\n\n"
            if event_type == "done":
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
