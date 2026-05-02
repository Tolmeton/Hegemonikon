#!/usr/bin/env python3
"""
HGK Desktop API — 軽量 HTTP proxy for Cortex API + HGK Gateway

アシスタントパネルから Cortex (Gemini/Claude) にアクセスし、
HGK Gateway の全ツール群を HTTP API として公開する。

Usage:
    cd ~/oikos/01_ヘゲモニコン｜Hegemonikon && PYTHONPATH=. .venv/bin/uvicorn hgk.api.serve:app --port 9698 --host 127.0.0.1
"""
import sys, json, asyncio, threading, uuid, difflib
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Load .env BEFORE importing gateway (HGK_GATEWAY_TOKEN required at module level)


from mekhane.ochema.cortex_client import CortexClient
from mekhane.ochema.service import OchemaService

# --- HGK Gateway (I-1: single namespace import) ---
from mekhane.mcp import hgk_gateway as gw

app = FastAPI(title="HGK Desktop API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton client
_client: CortexClient | None = None

def _get_client() -> CortexClient:
    global _client
    if _client is None:
        _client = CortexClient()
    return _client


# ============================================================
# Cortex API endpoints (既存 — 変更なし)
# ============================================================

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "hgk-desktop-api"}


@app.post("/api/ask")
async def ask(request: Request):
    """Simple ask endpoint — non-streaming."""
    body = await request.json()
    message = body.get("message", "")
    model = body.get("model", "gemini-2.5-flash")

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


@app.post("/api/ask/stream")
async def ask_stream(request: Request):
    """SSE streaming endpoint — true token-by-token streaming via CortexClient.ask_stream()."""
    body = await request.json()
    message = body.get("message", "")
    model = body.get("model", "gemini-2.5-flash")
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
            if system_instruction: kwargs["system_instruction"] = system_instruction
            if temperature is not None: kwargs["temperature"] = float(temperature)
            if max_tokens is not None: kwargs["max_tokens"] = int(max_tokens)
            if thinking_budget is not None: kwargs["thinking_budget"] = int(thinking_budget)

            # Bridge sync generator → async SSE via Queue + executor
            q: asyncio.Queue = asyncio.Queue()
            loop = asyncio.get_running_loop()

            def _stream_worker():
                import time as _time
                max_retries = 2
                svc = OchemaService.get()
                is_claude = svc._is_claude_model(model)
                import sys
                print(f"[STREAM DEBUG] model={model!r}, is_claude={is_claude}", file=sys.stderr, flush=True)

                for retry in range(max_retries + 1):
                    try:
                        if is_claude:
                            # Claude → svc.chat() で generateChat を直接呼び出す
                            # tier_id='g1-ultra-tier' が必須: Cortex API は
                            # model_config_id だけでは Claude にルーティングしない
                            config_id = svc._resolve_model_config_id(model)
                            print(f"[STREAM DEBUG] Claude chat direct: config_id={config_id!r}, tier_id='g1-ultra-tier'", file=sys.stderr, flush=True)
                            resp = svc.chat(
                                message=message,
                                model=config_id,
                                tier_id="g1-ultra-tier",
                                thinking_budget=kwargs.get("thinking_budget"),
                            )
                            print(f"[STREAM DEBUG] Claude response model={resp.model!r}, text[:80]={resp.text[:80]!r}", file=sys.stderr, flush=True)
                            if resp.thinking:
                                loop.call_soon_threadsafe(q.put_nowait, ("chunk", f"<details><summary>💭 思考過程</summary>\n\n{resp.thinking}\n\n</details>\n\n"))
                            if resp.text:
                                loop.call_soon_threadsafe(q.put_nowait, ("chunk", resp.text))
                            actual_model = resp.model or model
                            loop.call_soon_threadsafe(q.put_nowait, ("done", actual_model))
                        else:
                            # Gemini → token-by-token streaming
                            for chunk in svc.stream(**kwargs):
                                if chunk.startswith("__THINKING__:"):
                                    thinking = chunk[len("__THINKING__:"):]
                                    loop.call_soon_threadsafe(q.put_nowait, ("chunk", f"<details><summary>💭 思考過程</summary>\n\n{thinking}\n\n</details>\n\n"))
                                else:
                                    loop.call_soon_threadsafe(q.put_nowait, ("chunk", chunk))
                            loop.call_soon_threadsafe(q.put_nowait, ("done", model))
                        return
                    except Exception as exc:  # noqa: BLE001
                        err_msg = str(exc)
                        # Retry on rate limit (429) or server errors (5xx)
                        if retry < max_retries and ("429" in err_msg or "503" in err_msg or "500" in err_msg):
                            wait = (retry + 1) * 3  # 3s, 6s
                            loop.call_soon_threadsafe(
                                q.put_nowait,
                                ("chunk", f"\n\n*⏳ レート制限 — {wait}秒後にリトライ...*\n\n")
                            )
                            _time.sleep(wait)
                            continue
                        loop.call_soon_threadsafe(q.put_nowait, ("error", err_msg))

            loop.run_in_executor(None, _stream_worker)

            while True:
                kind, data = await q.get()
                if kind == "chunk":
                    yield f"data: {json.dumps({'text': data, 'done': False})}\n\n"
                elif kind == "done":
                    yield f"data: {json.dumps({'text': '', 'done': True, 'model': data})}\n\n"
                    break
                elif kind == "error":
                    yield f"data: {json.dumps({'error': data, 'done': True})}\n\n"
                    break
        except Exception as e:  # noqa: BLE001
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ============================================================
# HGK Gateway API — Dynamic routing (D-4: replaces 24 boilerplate endpoints)
# ============================================================
#
# Routing table: (method, path, gateway_fn, arg_extractor)
#   GET endpoints:  arg_extractor receives query params dict
#   POST endpoints: arg_extractor receives parsed JSON body
#
# To add a new Gateway function, just add one entry here.
# No more triple-management (gateway.py + hgk_tools.py + serve.py).

from typing import Callable

_HGK_ROUTES: list[tuple[str, str, Callable, Callable]] = [
    # --- GET (no-arg) ---
    ("GET", "/api/hgk/status",         gw.hgk_status,        lambda p: ()),
    ("GET", "/api/hgk/health",         gw.hgk_health,        lambda p: ()),
    ("GET", "/api/hgk/doxa",           gw.hgk_doxa_read,     lambda p: ()),
    ("GET", "/api/hgk/pks/stats",      gw.hgk_pks_stats,     lambda p: ()),
    ("GET", "/api/hgk/pks/health",     gw.hgk_pks_health,    lambda p: ()),
    ("GET", "/api/hgk/digest/check",   gw.hgk_digest_check,  lambda p: ()),
    ("GET", "/api/hgk/digest/topics",  gw.hgk_digest_topics, lambda p: ()),
    ("GET", "/api/hgk/models",         gw.hgk_models,        lambda p: ()),
    ("GET", "/api/hgk/gateway/health", gw.hgk_gateway_health, lambda p: ()),
    ("GET", "/api/hgk/sessions",       gw.hgk_sessions,      lambda p: ()),
    # --- GET (with query params) ---
    ("GET", "/api/hgk/notifications",  gw.hgk_notifications,
     lambda p: (int(p.get("limit", 10)),)),
    ("GET", "/api/hgk/handoff",        gw.hgk_handoff_read,
     lambda p: (int(p.get("count", 1)),)),
    # --- POST ---
    ("POST", "/api/hgk/search",        gw.hgk_search,
     lambda b: (b["query"], b.get("max_results", 5), b.get("mode", "hybrid"))),
    ("POST", "/api/hgk/pks/search",    gw.hgk_pks_search,
     lambda b: (b["query"], b.get("k", 10), b.get("sources", ""))),
    ("POST", "/api/hgk/ccl/dispatch",  gw.hgk_ccl_dispatch,
     lambda b: (b["ccl"],)),
    ("POST", "/api/hgk/ccl/execute",   gw.hgk_ccl_execute,
     lambda b: (b["ccl"], b.get("context", ""))),
    ("POST", "/api/hgk/idea",          gw.hgk_idea_capture,
     lambda b: (b["idea"], b.get("tags", ""))),
    ("POST", "/api/hgk/papers/search", gw.hgk_paper_search,
     lambda b: (b["query"], b.get("limit", 5))),
    ("POST", "/api/hgk/digest/list",   gw.hgk_digest_list,
     lambda b: (b.get("topics", ""), b.get("max_candidates", 10))),
    ("POST", "/api/hgk/digest/run",    gw.hgk_digest_run,
     lambda b: (b.get("topics", ""), b.get("max_papers", 20), b.get("dry_run", True))),
    ("POST", "/api/hgk/digest/mark",   gw.hgk_digest_mark,
     lambda b: (b.get("filenames", ""),)),
    ("POST", "/api/hgk/proactive",     gw.hgk_proactive_push,
     lambda b: (b.get("topics", ""), b.get("max_results", 5), b.get("use_advocacy", True))),
    ("POST", "/api/hgk/sop",           gw.hgk_sop_generate,
     lambda b: (b["topic"], b.get("decision", ""), b.get("hypothesis", ""))),
    ("POST", "/api/hgk/sessions/read", gw.hgk_session_read,
     lambda b: (b["cascade_id"], b.get("max_turns", 10), b.get("full", False))),
]


def _register_hgk_routes(application: FastAPI) -> None:
    """Dynamically register all HGK Gateway routes from the routing table."""
    for method, path, fn, extractor in _HGK_ROUTES:
        # Capture in closure
        _fn, _ext = fn, extractor

        if method == "GET":
            async def _get_handler(request: Request, __fn=_fn, __ext=_ext):
                try:
                    args = __ext(dict(request.query_params))
                    result = await asyncio.to_thread(__fn, *args)
                    return {"result": result}
                except Exception as e:  # noqa: BLE001
                    return JSONResponse({"error": str(e)}, status_code=500)
            application.add_api_route(path, _get_handler, methods=["GET"])
        else:
            async def _post_handler(request: Request, __fn=_fn, __ext=_ext):
                body = await request.json()
                try:
                    args = __ext(body)
                    result = await asyncio.to_thread(__fn, *args)
                    return {"result": result}
                except KeyError as e:
                    return JSONResponse({"error": f"Missing required field: {e}"}, status_code=400)
                except Exception as e:  # noqa: BLE001
                    return JSONResponse({"error": str(e)}, status_code=500)
            application.add_api_route(path, _post_handler, methods=["POST"])


_register_hgk_routes(app)


# ============================================================
# Agent Mode — LLM with autonomous HGK + File tool access
# ============================================================

# Phase 5: Safety Gate — approval state for high-risk tool execution
# Maps request_id → (threading.Event, [approved: bool])
_approval_gates: dict[str, tuple[threading.Event, list]] = {}

@app.post("/api/ask/agent")
async def ask_agent(request: Request):
    """Agent mode — LLM with autonomous HGK + file tool access.

    Uses CortexClient.ask_with_tools() with HGK Gateway tools + file system tools.
    The LLM autonomously decides which tools to call based on the user's message.
    Returns final response after all tool calls are resolved.
    """
    body = await request.json()
    message = body.get("message", "")
    model = body.get("model", "gemini-2.5-flash")
    system_instruction = body.get("system_instruction")
    max_iterations = body.get("max_iterations", 10)
    thinking_budget = body.get("thinking_budget")

    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    try:
        client = _get_client()

        # Merge file tools + HGK tools
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

        # C-2: 2-minute hard limit to prevent Gateway timeout cascade
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


@app.post("/api/ask/agent/stream")
async def ask_agent_stream(request: Request):
    """SSE streaming agent mode — streams intermediate tool events + final result.

    Phase 4: Intermediate events via on_event callback in ask_with_tools().

    Event types:
    - iteration:   {iteration, max}           — Agent loop iteration started
    - tool_call:   {name, args}               — LLM requested a tool
    - tool_result: {name, output, duration_ms} — Tool execution completed
    - chunk:       {text}                      — Final answer text
    - done:        {model, token_usage, iterations} — Completion
    - error:       {error}                     — Error occurred
    """
    body = await request.json()
    message = body.get("message", "")
    model = body.get("model", "gemini-2.5-flash")
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
                """Callback from ask_with_tools — push intermediate events to SSE queue."""
                loop.call_soon_threadsafe(q.put_nowait, (event_type, data))

            def _on_gate(name: str, args: dict) -> bool:
                """Safety Gate callback — blocks worker thread until user approves/rejects."""
                request_id = uuid.uuid4().hex[:8]
                gate = threading.Event()
                result_box = [False]  # mutable container
                _approval_gates[request_id] = (gate, result_box)

                # Phase 5 Diff: compute unified diff for write_file
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
                            # New file — show all lines as additions
                            diff_text = f"--- /dev/null\n+++ {target}\n" + "".join(
                                f"+{line}\n" if not line.endswith("\n") else f"+{line}"
                                for line in new_content.splitlines(keepends=True)
                            )
                            if not new_content.endswith("\n") and new_content:
                                diff_text += "\n\\ No newline at end of file\n"
                    except Exception:  # noqa: BLE001
                        diff_text = None  # Fall back to raw preview

                # Send approval_required event to frontend via SSE
                evt_data: dict = {
                    "request_id": request_id,
                    "name": name,
                    "args": args,
                }
                if diff_text is not None:
                    evt_data["diff"] = diff_text
                loop.call_soon_threadsafe(q.put_nowait, ("approval_required", evt_data))

                # Block until approval or timeout (120s)
                gate.wait(timeout=120.0)
                _approval_gates.pop(request_id, None)
                return result_box[0]

            def _agent_worker():
                """Run ask_with_tools in thread, push events + result to queue."""
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
                        q.put_nowait,
                        ("chunk", {"text": result.text})
                    )
                    loop.call_soon_threadsafe(
                        q.put_nowait,
                        ("done", {
                            "model": result.model,
                            "token_usage": getattr(result, "token_usage", {}),
                        })
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


# ============================================================
# Phase 5: Safety Gate — Approval endpoint
# ============================================================

@app.post("/api/ask/agent/approve")
async def approve_agent_tool(request: Request):
    """Approve or reject a gated tool execution.

    Called by the frontend when a user clicks ✅ or ❌ on an approval panel.
    Unblocks the waiting worker thread via threading.Event.
    """
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
    gate.set()  # Unblock the worker thread
    return {"status": "ok", "request_id": request_id, "approved": approved}


# ============================================================
# Phase 6: Colony Mode — F6 Multi-AI Organization
# ============================================================

@app.post("/api/ask/colony")
async def ask_colony(request: Request):
    """F6 Colony mode — COO (Opus 4.6) decomposes, delegates to Workers.

    COO analyzes the request, decomposes into subtasks, dispatches them
    to specialized Workers (Engineer, Researcher, Jules), and synthesizes
    the results into a final answer.
    """
    body = await request.json()
    message = body.get("message", "")
    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    try:
        from hgk.api.colony import Colony
        colony = Colony()
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


@app.post("/api/ask/colony/stream")
async def ask_colony_stream(request: Request):
    """SSE streaming colony mode — streams worker progress + final synthesis.

    Event types:
    - phase:        {phase, status}                    — Pipeline phase change
    - decompose:    {subtasks: [...]}                  — COO decomposition result
    - worker_start: {task_id, worker_type, description} — Worker execution started
    - worker_done:  {task_id, worker_type, success, output_preview} — Worker completed
    - synthesis:    {text}                              — COO's final synthesis
    - done:         {coo_model, total_duration_ms}      — Pipeline complete
    - error:        {error}                             — Error occurred
    """
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
                    """Safety Gate for Colony — reuses Agent's _approval_gates."""
                    request_id = uuid.uuid4().hex[:8]
                    gate = threading.Event()
                    result_box = [False]
                    _approval_gates[request_id] = (gate, result_box)

                    evt_data: dict = {
                        "request_id": request_id,
                        "name": name,
                        "args": args,
                    }
                    # Compute diff for write_file (same as Agent mode)
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

                colony = Colony(on_event=_on_event, on_gate=_on_gate)
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
            payload = json.dumps(
                {"type": kind, **data, "done": is_done},
                ensure_ascii=False,
            )
            yield f"data: {payload}\n\n"
            if is_done:
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ─── Phase 6: Push SSE Endpoint ────────────────────────────────

@app.get("/api/push/stream")
async def push_stream():
    """
    SSE endpoint for Dashboard push notifications.
    On connect: runs hgk_proactive_push in background thread,
    streams results as SSE events, then sends 'done'.
    Dashboard connects to this for real-time Autophōnos notifications.
    """
    async def event_generator():
        q: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def _push_worker():
            try:
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


# ============================================================
# Jules API — Async coding agent integration
# ============================================================

from hgk.api.jules_client import get_jules_client

@app.get("/api/jules/sources")
async def jules_sources():
    """List available GitHub sources for Jules."""
    try:
        client = get_jules_client()
        if not client.available:
            return JSONResponse({"error": "No Jules API keys configured"}, status_code=503)
        sources = await asyncio.to_thread(client.list_sources)
        return {"sources": sources}
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/jules/sessions")
async def jules_sessions(page_size: int = 20):
    """List recent Jules sessions."""
    try:
        client = get_jules_client()
        sessions = await asyncio.to_thread(client.list_sessions, page_size)
        return {"sessions": sessions}
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/jules/sessions/{session_id}")
async def jules_session_detail(session_id: str):
    """Get Jules session details."""
    try:
        client = get_jules_client()
        session = await asyncio.to_thread(client.get_session, session_id)
        return session
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/jules/sessions")
async def jules_create_session(request: Request):
    """Create a new Jules coding session.

    Body:
        prompt: str — Task description
        source: str — Source ID (e.g., "sources/github/owner/repo")
        title: str (optional)
        branch: str (default: "main")
        require_plan_approval: bool (default: false)
    """
    body = await request.json()
    prompt = body.get("prompt", "")
    source = body.get("source", "")
    if not prompt or not source:
        return JSONResponse({"error": "prompt and source are required"}, status_code=400)
    try:
        client = get_jules_client()
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


@app.post("/api/jules/sessions/{session_id}/approve")
async def jules_approve_plan(session_id: str):
    """Approve a pending Jules plan."""
    try:
        client = get_jules_client()
        result = await asyncio.to_thread(client.approve_plan, session_id)
        return result
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/jules/sessions/{session_id}/message")
async def jules_send_message(session_id: str, request: Request):
    """Send a follow-up message to an active Jules session."""
    body = await request.json()
    message = body.get("message", "")
    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)
    try:
        client = get_jules_client()
        result = await asyncio.to_thread(client.send_message, session_id, message)
        return result
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/jules/sessions/{session_id}/activities")
async def jules_activities(session_id: str, page_size: int = 50):
    """List activities for a Jules session."""
    try:
        client = get_jules_client()
        activities = await asyncio.to_thread(client.list_activities, session_id, page_size)
        return {"activities": activities}
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/jules/sessions/{session_id}/poll")
async def jules_poll_session(session_id: str):
    """SSE endpoint to poll a Jules session until completion.

    Streams status updates as SSE events.
    """
    async def event_generator():
        client = get_jules_client()
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


# ============================================================
# File Operations API — Local file access for Chat UI
# ============================================================

import base64, mimetypes, os, tempfile
from fastapi import UploadFile, File

_ALLOWED_ROOT = Path.home() / "oikos"

def _safe_path(raw: str) -> Path:
    """Resolve path and ensure it's under ALLOWED_ROOT."""
    p = Path(raw).expanduser().resolve()
    if not str(p).startswith(str(_ALLOWED_ROOT)):
        raise ValueError(f"Access denied: {p} is outside {_ALLOWED_ROOT}")
    return p


@app.get("/api/files/list")
async def files_list(path: str = "~/oikos"):
    """List directory contents."""
    try:
        p = _safe_path(path)
        if not p.is_dir():
            return JSONResponse({"error": f"Not a directory: {p}"}, status_code=400)
        entries = []
        for item in sorted(p.iterdir()):
            try:
                stat = item.stat()
                entries.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": stat.st_size if item.is_file() else None,
                    "modified": stat.st_mtime,
                })
            except (PermissionError, OSError):
                continue
        return {"path": str(p), "entries": entries}
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=403)
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/files/read")
async def files_read(path: str):
    """Read file contents. Returns text or base64 for binary files."""
    try:
        p = _safe_path(path)
        if not p.is_file():
            return JSONResponse({"error": f"Not a file: {p}"}, status_code=400)
        mime, _ = mimetypes.guess_type(str(p))
        is_text = mime and mime.startswith("text/") or p.suffix in (
            ".md", ".py", ".ts", ".js", ".css", ".html", ".json", ".yaml", ".yml",
            ".toml", ".cfg", ".ini", ".sh", ".bash", ".rs", ".go", ".rb", ".tsx",
            ".jsx", ".vue", ".svelte", ".sql", ".xml", ".csv", ".env", ".txt",
            ".prompt", ".gitignore", ".dockerignore", ".conf",
        )
        if is_text:
            content = p.read_text(errors="replace")
            return {"path": str(p), "content": content, "encoding": "text", "mime": mime or "text/plain", "size": len(content)}
        else:
            raw = p.read_bytes()
            return {"path": str(p), "content": base64.b64encode(raw).decode(), "encoding": "base64", "mime": mime or "application/octet-stream", "size": len(raw)}
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=403)
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/files/upload")
async def files_upload(file: UploadFile = File(...)):
    """Upload a file. Saved to temp dir, returns path."""
    try:
        upload_dir = Path(tempfile.gettempdir()) / "hgk_uploads"
        upload_dir.mkdir(exist_ok=True)
        dest = upload_dir / f"{uuid.uuid4().hex[:8]}_{file.filename}"
        content = await file.read()
        dest.write_bytes(content)
        mime, _ = mimetypes.guess_type(file.filename or "")
        return {"path": str(dest), "filename": file.filename, "size": len(content), "mime": mime}
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


# ============================================================
# Gateway Trace — Cowork Dashboard data source
# ============================================================

@app.get("/api/hgk/gateway/trace")
async def gateway_trace(limit: int = 100):
    """Read recent Gateway tool traces from gateway_trace.jsonl."""
    try:
        mneme_dir = Path.home() / "oikos" / "mneme" / ".hegemonikon"
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
# IDE ConnectRPC — HGK Gateway 配下の IDE 内部情報アクセス
# ============================================================

from hgk.api.ls_client import call_ls, get_ide_status

@app.get("/api/hgk/ide/status")
async def ide_status():
    """IDE 接続ステータス (PID / Port / 接続状態)"""
    try:
        return await asyncio.to_thread(get_ide_status)
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": str(e)}

@app.get("/api/hgk/ide/workflows")
async def ide_workflows():
    """IDE 内部ワークフロー一覧"""
    try:
        return await asyncio.to_thread(call_ls, "GetAllWorkflows")
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/hgk/ide/memories")
async def ide_memories():
    """IDE ユーザーメモリー"""
    try:
        return await asyncio.to_thread(call_ls, "GetUserMemories")
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/hgk/ide/trajectories")
async def ide_trajectories():
    """IDE 会話トラジェクトリ"""
    try:
        return await asyncio.to_thread(call_ls, "GetAllCascadeTrajectories")
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=500)


# ============================================================
# Stub endpoints — 起動時の 404 を防ぐスタブ
# main.ts が起動時に呼ぶが Gateway 未接続でも動作するようにする
# ============================================================

@app.get("/api/pks/push")
@app.post("/api/pks/push")
async def pks_push_stub():
    """PKS push stub — returns empty nuggets list."""
    return {"timestamp": "", "topics": [], "nuggets": [], "total": 0}


@app.get("/api/sympatheia/notifications")
async def sympatheia_notifications_stub(limit: int = 50, level: str = ""):
    """Sympatheia notifications stub — returns empty list."""
    return []


@app.get("/api/status/health")
async def status_health_stub():
    """Status health stub."""
    return {"status": "ok", "service": "hgk-desktop-api"}


@app.get("/api/status")
async def status_stub():
    """Status stub — returns minimal status."""
    return {"status": "ok", "version": "0.2.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9698)
