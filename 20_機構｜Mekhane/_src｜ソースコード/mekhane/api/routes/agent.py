from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/api/routes/
# PURPOSE: Agent Mode — LLM + HGK ツール自律呼出 (Safety Gate 付き)


import asyncio
import difflib
import json
import logging
import threading
import uuid
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from mekhane.ochema.model_defaults import FLASH

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agent"])

# Safety Gate state — maps request_id → (threading.Event, [approved: bool])
_approval_gates: dict[str, tuple[threading.Event, list]] = {}

# Singleton CortexClient (shared with cortex_ask)
_client = None


def _get_client():
    global _client
    if _client is None:
        from mekhane.ochema.cortex_client import CortexClient
        _client = CortexClient()
    return _client


@router.post("/api/ask/agent")
async def ask_agent(request: Request):
    """Agent mode — LLM with autonomous HGK + file tool access."""
    body = await request.json()
    message = body.get("message", "")
    model = body.get("model", FLASH)
    system_instruction = body.get("system_instruction")
    max_iterations = body.get("max_iterations", 10)
    thinking_budget = body.get("thinking_budget")

    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    try:
        client = _get_client()

        from mekhane.ochema.tools import TOOL_DEFINITIONS, HGK_SYSTEM_TEMPLATES
        from mekhane.ochema.hgk_tools import HGK_TOOL_DEFINITIONS
        all_tools = TOOL_DEFINITIONS + HGK_TOOL_DEFINITIONS

        kwargs: dict = dict(
            message=message,
            model=model,
            system_instruction=system_instruction or HGK_SYSTEM_TEMPLATES["hgk_citizen"],
            tools=all_tools,
            max_iterations=max_iterations,
        )
        if thinking_budget is not None:
            kwargs["thinking_budget"] = int(thinking_budget)

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(client.ask_with_tools, **kwargs),
                timeout=120.0,
            )
        except asyncio.TimeoutError:
            return JSONResponse(
                {"error": "Agent execution timed out (120s limit)"},
                status_code=504,
            )

        return {
            "text": result.text,
            "model": result.model,
            "token_usage": getattr(result, "token_usage", {}),
        }
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/api/ask/agent/stream")
async def ask_agent_stream(request: Request):
    """SSE streaming agent mode — streams intermediate tool events + final result."""
    body = await request.json()
    message = body.get("message", "")
    model = body.get("model", FLASH)
    system_instruction = body.get("system_instruction")
    max_iterations = body.get("max_iterations", 10)
    thinking_budget = body.get("thinking_budget")

    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    async def event_generator():
        try:
            client = _get_client()

            from mekhane.ochema.tools import TOOL_DEFINITIONS, HGK_SYSTEM_TEMPLATES
            from mekhane.ochema.hgk_tools import HGK_TOOL_DEFINITIONS
            all_tools = TOOL_DEFINITIONS + HGK_TOOL_DEFINITIONS

            q: asyncio.Queue = asyncio.Queue()
            loop = asyncio.get_running_loop()

            def _on_event(event_type: str, data: dict):
                loop.call_soon_threadsafe(q.put_nowait, (event_type, data))

            def _on_gate(name: str, args: dict) -> bool:
                request_id = uuid.uuid4().hex[:8]
                gate = threading.Event()
                result_box = [False]
                _approval_gates[request_id] = (gate, result_box)

                diff_text: str | None = None
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
                            if not new_content.endswith("\n") and new_content:
                                diff_text += "\n\\ No newline at end of file\n"
                    except Exception:  # noqa: BLE001
                        diff_text = None

                evt_data: dict = {
                    "request_id": request_id,
                    "name": name,
                    "args": args,
                }
                if diff_text is not None:
                    evt_data["diff"] = diff_text
                loop.call_soon_threadsafe(q.put_nowait, ("approval_required", evt_data))

                gate.wait(timeout=120.0)
                _approval_gates.pop(request_id, None)
                return result_box[0]

            def _agent_worker():
                try:
                    sys_inst = system_instruction or HGK_SYSTEM_TEMPLATES["hgk_citizen"]
                    kwargs: dict = dict(
                        message=message,
                        model=model,
                        system_instruction=sys_inst,
                        tools=all_tools,
                        max_iterations=max_iterations,
                        on_event=_on_event,
                        on_gate=_on_gate,
                    )
                    if thinking_budget is not None:
                        kwargs["thinking_budget"] = int(thinking_budget)

                    result = client.ask_with_tools(**kwargs)

                    loop.call_soon_threadsafe(
                        q.put_nowait, ("chunk", {"text": result.text})
                    )
                    loop.call_soon_threadsafe(
                        q.put_nowait,
                        ("done", {
                            "model": result.model,
                            "token_usage": getattr(result, "token_usage", {}),
                        }),
                    )
                except Exception as exc:  # noqa: BLE001
                    loop.call_soon_threadsafe(
                        q.put_nowait, ("error", {"error": str(exc)})
                    )

            loop.run_in_executor(None, _agent_worker)

            while True:
                kind, data = await q.get()
                yield f"data: {json.dumps({'type': kind, **data, 'done': kind in ('done', 'error')})}\n\n"
                if kind in ("done", "error"):
                    break

        except Exception as e:  # noqa: BLE001
            yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/api/ask/agent/approve")
async def approve_agent_tool(request: Request):
    """Approve or reject a gated tool execution."""
    body = await request.json()
    request_id = body.get("request_id", "")
    approved = body.get("approved", False)

    if request_id not in _approval_gates:
        return JSONResponse(
            {"error": f"Unknown or expired request_id: {request_id}"},
            status_code=404,
        )

    gate, result_box = _approval_gates[request_id]
    result_box[0] = bool(approved)
    gate.set()
    return {"status": "ok", "request_id": request_id, "approved": approved}
