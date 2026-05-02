from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/api/routes/
# PURPOSE: HGK Gateway — /api/hgk/* を hgk_gateway 実関数に動的ルーティング


import asyncio
import logging
from typing import Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["hgk"])


def _register_hgk_dynamic_routes(r: APIRouter) -> None:
    """Dynamically register all HGK Gateway routes from the routing table."""
    try:
        from mekhane.mcp import hgk_gateway as gw
    except Exception as exc:  # noqa: BLE001
        logger.warning("HGK Gateway import failed — skipping dynamic routes: %s", exc)
        return

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

    for method, path, fn, extractor in _HGK_ROUTES:
        _fn, _ext = fn, extractor

        if method == "GET":
            async def _get_handler(request: Request, __fn=_fn, __ext=_ext):
                try:
                    args = __ext(dict(request.query_params))
                    result = await asyncio.to_thread(__fn, *args)
                    return {"result": result}
                except Exception as e:  # noqa: BLE001
                    return JSONResponse({"error": str(e)}, status_code=500)
            r.add_api_route(path, _get_handler, methods=["GET"])
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
            r.add_api_route(path, _post_handler, methods=["POST"])

    logger.info("HGK Gateway dynamic routes registered (%d routes)", len(_HGK_ROUTES))


# Register dynamic routes at import time
_register_hgk_dynamic_routes(router)
