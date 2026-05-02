from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/api/routes/
# PURPOSE: Colony Mode — F6 マルチ AI 組織 (COO + Workers)


import asyncio
import difflib
import json
import logging
import threading
import uuid
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["colony"])

# Reuse agent's approval gates
from mekhane.api.routes.agent import _approval_gates


@router.post("/api/ask/colony")
async def ask_colony(request: Request):
    """F6 Colony mode — COO decomposes, delegates to Workers."""
    body = await request.json()
    message = body.get("message", "")
    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    try:
        from hgk.api.colony import Colony
        colony = Colony(vertex_mode=body.get("vertex_mode"))
        result = await colony.execute(message)
        return {
            "synthesis": result.synthesis,
            "subtasks": [
                {"id": st.id, "description": st.description,
                 "worker_type": st.worker_type.value}
                for st in result.subtasks
            ],
            "results": [
                {"task_id": wr.task_id, "worker_type": wr.worker_type.value,
                 "success": wr.success, "duration_ms": wr.duration_ms,
                 "output_preview": wr.output[:500] if wr.output else wr.error[:500]}
                for wr in result.results
            ],
            "coo_model": result.coo_model,
            "total_duration_ms": result.total_duration_ms,
        }
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/api/ask/colony/stream")
async def ask_colony_stream(request: Request):
    """SSE streaming colony mode — streams worker progress + final synthesis."""
    body = await request.json()
    message = body.get("message", "")
    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    async def event_generator():
        q: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def _on_event(event_type: str, data: dict):
            loop.call_soon_threadsafe(q.put_nowait, (event_type, data))

        async def _colony_worker():
            try:
                from hgk.api.colony import Colony

                def _on_gate(name: str, args: dict) -> bool:
                    request_id = uuid.uuid4().hex[:8]
                    gate = threading.Event()
                    result_box = [False]
                    _approval_gates[request_id] = (gate, result_box)

                    evt_data: dict = {
                        "request_id": request_id,
                        "name": name,
                        "args": args,
                    }
                    if name == "write_file":
                        try:
                            target = Path(args.get("path", ""))
                            new_content = str(args.get("content", ""))
                            new_lines = new_content.splitlines(keepends=True)
                            if target.is_file():
                                old_lines = target.read_text(errors="replace").splitlines(keepends=True)
                                diff_text = "".join(difflib.unified_diff(
                                    old_lines, new_lines,
                                    fromfile=str(target) + " (before)",
                                    tofile=str(target) + " (after)",
                                    lineterm="",
                                ))
                            else:
                                diff_text = f"--- /dev/null\n+++ {target}\n" + "".join(
                                    f"+{line}\n" if not line.endswith("\n") else f"+{line}"
                                    for line in new_content.splitlines(keepends=True)
                                )
                            evt_data["diff"] = diff_text
                        except Exception:  # noqa: BLE001
                            pass

                    loop.call_soon_threadsafe(q.put_nowait, ("approval_required", evt_data))
                    gate.wait(timeout=120.0)
                    _approval_gates.pop(request_id, None)
                    return result_box[0]

                colony = Colony(on_event=_on_event, on_gate=_on_gate, vertex_mode=body.get("vertex_mode"))
                result = await colony.execute(message)

                await q.put(("synthesis", {"text": result.synthesis}))
                if result.thinking:
                    await q.put(("thinking", {"text": result.thinking}))
                await q.put(("done", {
                    "coo_model": result.coo_model,
                    "total_duration_ms": result.total_duration_ms,
                }))
            except Exception as exc:  # noqa: BLE001
                await q.put(("error", {"error": str(exc)}))

        asyncio.ensure_future(_colony_worker())

        while True:
            try:
                kind, data = await asyncio.wait_for(q.get(), timeout=300.0)
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'error', 'error': 'Colony timeout (300s)', 'done': True})}\n\n"
                break

            is_done = kind in ("done", "error")
            payload = json.dumps({"type": kind, **data, "done": is_done}, ensure_ascii=False)
            yield f"data: {payload}\n\n"
            if is_done:
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
