#!/usr/bin/env python3
# PROOF: [L2/Sympatheia] <- mekhane/api/routes/
# PURPOSE: Sympatheia FastAPI routes — thin wrapper around mekhane.sympatheia.core
"""
Sympatheia Routes — FastAPI API layer.

POST /api/sympatheia/wbc            — WF-09: White blood cell (threat analysis)
POST /api/sympatheia/digest         — WF-10: Memory compression (weekly digest)
POST /api/sympatheia/attractor      — WF-11: Reflex arc (theorem recommendation)
POST /api/sympatheia/feedback       — WF-12: Homeostasis (threshold adjustment)
POST /api/sympatheia/route          — WF-14: Thalamus (routing + forwarding)
POST /api/sympatheia/notifications  — Notification receive
GET  /api/sympatheia/notifications  — Notification list

All business logic lives in mekhane.sympatheia.core.
This file only provides FastAPI route decorators.
"""

from typing import Optional

from fastapi import APIRouter, Query

# Re-export everything from core for backwards compatibility
from mekhane.sympatheia.core import (
    # Models
    WBCRequest, WBCResponse,
    DigestRequest, DigestResponse,
    AttractorRequest, AttractorResponse,
    FeedbackRequest, FeedbackResponse,
    RouteRequest, RouteResponse,
    NotificationRequest, NotificationResponse,
    # Helpers (re-exported for any external code that imports from here)
    MNEME,
    _read_json, _write_json, _load_config,
    _send_notification, _dismiss_notification,
    _purge_notifications, _list_notifications_raw,
    # Constants
    THREAT_WEIGHTS, ROUTES,
    # Business logic (async functions)
    wbc_analyze as _wbc_analyze,
    weekly_digest as _weekly_digest,
    attractor_dispatch as _attractor_dispatch,
    feedback_loop as _feedback_loop,
    incoming_route as _incoming_route,
    receive_notification as _receive_notification,
    _digestor_virtual_notifications,
)

import logging
logger = logging.getLogger("hegemonikon.api.sympatheia")

router = APIRouter(prefix="/sympatheia", tags=["sympatheia"])


# ===========================================================================
# FastAPI Route Decorators — delegate to core functions
# ===========================================================================

@router.post("/wbc", response_model=WBCResponse)
async def wbc_analyze(req: WBCRequest) -> WBCResponse:
    """白血球: 脅威分析 + エスカレーション。"""
    return await _wbc_analyze(req)


@router.post("/digest", response_model=DigestResponse)
async def weekly_digest(req: DigestRequest) -> DigestResponse:
    """記憶圧縮: 全メトリクス集約。"""
    return await _weekly_digest(req)


@router.post("/attractor", response_model=AttractorResponse)
async def attractor_dispatch(req: AttractorRequest) -> AttractorResponse:
    """反射弓: TheoremAttractor による定理推薦。"""
    return await _attractor_dispatch(req)


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback_loop(req: FeedbackRequest) -> FeedbackResponse:
    """恒常性: 閾値の動的調整。"""
    return await _feedback_loop(req)


@router.post("/route", response_model=RouteResponse)
async def incoming_route(req: RouteRequest) -> RouteResponse:
    """視床: 入力分類 + 実際に転送。"""
    return await _incoming_route(req)


@router.post("/notifications", response_model=NotificationResponse, status_code=201)
async def receive_notification(req: NotificationRequest) -> NotificationResponse:
    """通知受信: n8n WF や内部モジュールからの通知を JSONL に保存。"""
    return await _receive_notification(req)


@router.get("/notifications")
async def list_notifications(
    limit: int = Query(50, ge=1, le=500),
    since: Optional[str] = Query(None, description="ISO8601 timestamp filter"),
    level: Optional[str] = Query(None, description="Filter by level: INFO|HIGH|CRITICAL"),
    include_digestor: bool = Query(True, description="Include Digestor candidates as virtual notifications"),
    include_dismissed: bool = Query(False, description="Include dismissed notifications"),
) -> list[NotificationResponse]:
    """通知一覧: JSONL から読み込み、最新順で返す。dismissed はデフォルトで除外。"""
    results = _list_notifications_raw(
        limit=limit,
        level=level,
        since=since,
        include_dismissed=include_dismissed,
    )

    if include_digestor and (not level or level.upper() == "INFO"):
        digestor_notifs = _digestor_virtual_notifications()
        for dn in digestor_notifs:
            if since and dn.get("timestamp", "") < since:
                continue
            results.append(dn)

    results.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return [NotificationResponse(**r) for r in results[:limit]]
