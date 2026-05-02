#!/usr/bin/env python3
# PROOF: [L2/Sympatheia] <- mekhane/sympatheia/
# PURPOSE: Sympatheia core logic — FastAPI-independent models, helpers, and business logic
"""
Sympatheia Core — FastAPI-free business logic layer.

This module contains all Pydantic models, helpers, and async business functions
used by both:
  - mekhane/api/routes/sympatheia.py (FastAPI REST API)
  - mekhane/mcp/sympatheia_mcp_server.py (MCP server)

No FastAPI imports are present here. Only pydantic + stdlib.
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
import uuid

from pydantic import BaseModel, Field

from mekhane.dual_logger import DualLogger
from mekhane.symploke.handoff_files import list_handoff_files

logger = logging.getLogger("hegemonikon.sympatheia.core")

# PURPOSE: State files base paths (L2 subdirectories)
try:
    from mekhane.paths import (
    HANDOFF_DIR,
    MNEME_DIR,
    MNEME_STATE as _MNEME_STATE,
    STATE_CACHE,
    STATE_LOGS,
    STATE_VIOLATIONS,
)
except ImportError:
    # Fallback for standalone execution
    _MNEME_STATE = Path(os.getenv("HGK_MNEME", str(MNEME_DIR))) / "05_状態｜State"
    STATE_VIOLATIONS = _MNEME_STATE / "A_違反｜Violations"
    STATE_CACHE = _MNEME_STATE / "B_キャッシュ｜Cache"
    STATE_LOGS = _MNEME_STATE / "C_ログ｜Logs"

# 後方互換エイリアス
MNEME = STATE_LOGS  # 既存コードは MNEME をログ用に使用していた

# PURPOSE: DualLogger インスタンス (平文テキスト + 補助 JSONL の二重ログ)
# 既存の notifications.jsonl / incoming_router.jsonl は互換スキーマで自前書込。
# DualLogger は平文テキスト出力 + 補助構造化ログ (_detail.jsonl) を担当。
_notif_logger = DualLogger(
    jsonl_path=STATE_LOGS / "notifications_detail.jsonl",
    text_path=STATE_LOGS / "notifications.txt",
    component="sympatheia.notifications",
)

_router_logger = DualLogger(
    jsonl_path=STATE_LOGS / "incoming_router_detail.jsonl",
    text_path=STATE_LOGS / "incoming_router.txt",
    component="sympatheia.router",
)


# ===========================================================================
# Pydantic Models
# ===========================================================================

# --- WBC ---
# PURPOSE: WBC request/response models
class WBCRequest(BaseModel):
    source: str = "unknown"
    severity: str = "medium"
    details: str = "No details"
    files: list[str] = Field(default_factory=list)


class WBCResponse(BaseModel):
    timestamp: str
    source: str
    severity: str
    threatScore: int
    level: str
    details: str
    files: list[str]
    recentAlertCount: int
    shouldEscalate: bool


# --- Digest ---
class DigestRequest(BaseModel):
    pass  # webhook trigger, no payload needed


class DigestResponse(BaseModel):
    timestamp: str
    weekEnding: str
    heartbeat: dict = Field(default_factory=dict)
    fileMon: dict = Field(default_factory=dict)
    git: dict = Field(default_factory=dict)
    wbc: dict = Field(default_factory=dict)
    health: dict = Field(default_factory=dict)
    sessions: int = 0


# --- Attractor ---
class AttractorRequest(BaseModel):
    context: str = ""
    text: str = ""  # fallback


class AttractorResponse(BaseModel):
    timestamp: str
    recommendation: dict | None = None
    autoDispatch: bool = False
    context: str = ""


# --- Feedback ---
class FeedbackRequest(BaseModel):
    pass


class FeedbackResponse(BaseModel):
    timestamp: str
    metrics: dict = Field(default_factory=dict)
    thresholds: dict = Field(default_factory=dict)
    adjusted: bool = False
    adjustments: list[str] = Field(default_factory=list)


# --- Route ---
class RouteRequest(BaseModel):
    type: str = ""
    source: str = "unknown"
    payload: dict = Field(default_factory=dict)


class RouteResponse(BaseModel):
    routed: bool = False
    target: str = ""
    wf: str = ""
    timestamp: str = ""
    error: str = ""
    available: list[str] = Field(default_factory=list)
    forwardResult: dict | None = None


# --- Notification ---
class NotificationRequest(BaseModel):
    source: str = "unknown"
    level: str = "INFO"
    title: str = ""
    body: str = ""
    data: dict = Field(default_factory=dict)


class NotificationResponse(BaseModel):
    id: str
    timestamp: str
    source: str
    level: str
    title: str
    body: str
    data: dict = Field(default_factory=dict)


# ===========================================================================
# Helpers
# ===========================================================================

# PURPOSE: Read JSON file safely
def _read_json(path: Path, default: Any = None) -> Any:
    """JSON file safe reader."""
    try:
        return json.loads(path.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return default if default is not None else {}


# PURPOSE: Write JSON file safely
def _write_json(path: Path, data: Any) -> None:
    """JSON file safe writer."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to write %s: %s", path, e)


# PURPOSE: Load sympatheia_config.json (WF-12 output → WF-09 input = closed loop)
def _load_config() -> dict:
    """Load sympatheia config (closed loop: WF-12 → WF-09)."""
    default = {
        "thresholds": {"health_high": 0.5, "health_low": 0.3, "stale_minutes": 60},
        "sensitivity": 1.0,
        "lastAdjusted": None,
        "adjustmentHistory": [],
    }
    return _read_json(STATE_CACHE / "sympatheia_config.json", default)


# PURPOSE: Save local notification to JSONL with dedup
def _send_notification(source: str, level: str, title: str, body: str, data: Optional[dict] = None) -> str:
    """Save notification to JSONL. Dedup: skip if same source+title within 60s."""
    notif_file = MNEME / "notifications.jsonl"
    now = datetime.now(timezone.utc)

    # --- Dedup ---
    try:
        if notif_file.exists():
            cutoff = (now - timedelta(seconds=60)).isoformat()
            for line in reversed(notif_file.read_text("utf-8").strip().split("\n")[-20:]):
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("timestamp", "") < cutoff:
                        break
                    if rec.get("source") == source and rec.get("title") == title:
                        logger.debug("Notification dedup: skipping %s/%s", source, title)
                        return rec.get("id", "dedup")
                except Exception:  # noqa: BLE001
                    continue
    except Exception:  # noqa: BLE001
        pass

    notif_id = str(uuid.uuid4())[:8]
    record = {
        "id": notif_id,
        "timestamp": now.isoformat(),
        "source": source,
        "level": level,
        "title": title,
        "body": body,
        "data": data or {},
    }
    try:
        notif_file.parent.mkdir(parents=True, exist_ok=True)
        # JSONL: 既存スキーマ {id, timestamp, source, level, ...} を維持 (読取互換性)
        with open(notif_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        # 平文ログ: DualLogger で可読テキストも同時出力
        _notif_logger.info(f"[{notif_id}] {source}: {title}", body=body)
        logger.info("Notification [%s] %s: %s", notif_id, source, title)
    except Exception as e:  # noqa: BLE001
        logger.warning("Notification write failed: %s", e)
    return notif_id


# PURPOSE: Soft-delete a notification
def _dismiss_notification(notif_id: str) -> bool:
    """Set notification as dismissed. Rewrites JSONL."""
    notif_file = MNEME / "notifications.jsonl"
    if not notif_file.exists():
        return False
    lines = notif_file.read_text("utf-8").strip().split("\n")
    found = False
    new_lines = []
    for line in lines:
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            if rec.get("id") == notif_id:
                rec["dismissed"] = True
                rec["dismissed_at"] = datetime.now(timezone.utc).isoformat()
                found = True
            new_lines.append(json.dumps(rec, ensure_ascii=False))
        except Exception:  # noqa: BLE001
            new_lines.append(line)
    if found:
        notif_file.write_text("\n".join(new_lines) + "\n", "utf-8")
    return found


# PURPOSE: Purge old notifications by TTL
def _purge_notifications(ttl_days: Optional[dict] = None) -> dict:
    """Purge old notifications by TTL. Returns purge count."""
    defaults = {"INFO": 7, "HIGH": 30, "CRITICAL": 90}
    ttl = {**defaults, **(ttl_days or {})}
    notif_file = MNEME / "notifications.jsonl"
    if not notif_file.exists():
        return {"purged": 0, "remaining": 0}
    now = datetime.now(timezone.utc)
    lines = notif_file.read_text("utf-8").strip().split("\n")
    kept = []
    purged = 0
    for line in lines:
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            level = rec.get("level", "INFO")
            ts = rec.get("timestamp", "")
            max_age = timedelta(days=ttl.get(level, 30))
            if ts and (now - datetime.fromisoformat(ts)) > max_age:
                purged += 1
                continue
            kept.append(json.dumps(rec, ensure_ascii=False))
        except Exception:  # noqa: BLE001
            kept.append(line)
    if purged > 0:
        notif_file.write_text("\n".join(kept) + "\n" if kept else "", "utf-8")
    return {"purged": purged, "remaining": len(kept)}


# PURPOSE: Common notification list logic (shared by MCP and API)
def _list_notifications_raw(
    *,
    limit: int = 50,
    level: Optional[str] = None,
    since: Optional[str] = None,
    include_dismissed: bool = False,
) -> list[dict]:
    """Read notifications from JSONL, filter, return newest-first."""
    notif_file = MNEME / "notifications.jsonl"
    results: list[dict] = []
    try:
        for line in notif_file.read_text("utf-8").strip().split("\n"):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if not include_dismissed and record.get("dismissed"):
                    continue
                if since and record.get("timestamp", "") < since:
                    continue
                if level and record.get("level", "") != level.upper():
                    continue
                record.setdefault("id", f"legacy-{hash(record.get('timestamp', '')) & 0xFFFF:04x}")
                record.setdefault("level", "INFO")
                record.setdefault("title", "System Event")
                record.setdefault("body", "")
                record.setdefault("data", {})
                results.append(record)
            except Exception:  # noqa: BLE001
                continue
    except FileNotFoundError:
        pass
    except Exception as e:  # noqa: BLE001
        logger.warning("Notification read failed: %s", e)
    results.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return results[:limit]


# ===========================================================================
# WF-09: White Blood Cell (threat analysis)
# ===========================================================================

THREAT_WEIGHTS: dict[str, int] = {
    "SACRED_TRUTH.md": 10,
    "behavioral_constraints.md": 8,
    "registry.yaml": 7,
    "docker-compose.yml": 7,
    "hegemonikon.md": 6,
    "CONSTITUTION.md": 6,
    "axiom_hierarchy.md": 5,
    "safety-invariants.md": 5,
}


# PURPOSE: WBC threat analysis
async def wbc_analyze(req: WBCRequest) -> WBCResponse:
    """White blood cell: threat analysis + escalation."""
    now = datetime.now(timezone.utc)
    state_file = STATE_VIOLATIONS / "wbc_state.json"
    state = _read_json(state_file, {"alerts": [], "totalAlerts": 0, "lastEscalation": None})

    config = _load_config()
    sensitivity = config.get("sensitivity", 1.0)

    threat_score = 0
    if req.severity == "critical":
        threat_score += 5
    elif req.severity == "high":
        threat_score += 3
    else:
        threat_score += 1

    for f in req.files:
        for key, weight in THREAT_WEIGHTS.items():
            if key in f:
                threat_score += weight

    one_hour_ago = (now - timedelta(hours=1)).isoformat()
    recent = [a for a in state.get("alerts", []) if a.get("timestamp", "") > one_hour_ago]
    if len(recent) >= 3:
        threat_score += 5

    threat_score = int(threat_score * sensitivity)
    level = "CRITICAL" if threat_score >= 8 else "HIGH" if threat_score >= 4 else "LOW"
    should_escalate = level in ("CRITICAL", "HIGH")

    diagnosis = WBCResponse(
        timestamp=now.isoformat(),
        source=req.source,
        severity=req.severity,
        threatScore=threat_score,
        level=level,
        details=req.details,
        files=req.files,
        recentAlertCount=len(recent),
        shouldEscalate=should_escalate,
    )

    one_day_ago = (now - timedelta(days=1)).isoformat()
    state["alerts"] = [a for a in state.get("alerts", []) if a.get("timestamp", "") > one_day_ago]
    state["alerts"].append(diagnosis.model_dump())
    state["totalAlerts"] = state.get("totalAlerts", 0) + 1
    if should_escalate:
        state["lastEscalation"] = now.isoformat()
    _write_json(state_file, state)

    if should_escalate:
        emoji = "🚨" if level == "CRITICAL" else "⚠️"
        file_list = ", ".join(req.files[:5]) or "N/A"
        _send_notification(
            source="WF-09",
            level=level,
            title=f"{emoji} WBC: {level} threat detected",
            body=f"Source: {req.source}\nScore: {threat_score}/15\nFiles: {file_list}\nTotal: {state['totalAlerts']}",
            data={"threatScore": threat_score, "files": req.files[:5]},
        )

    return diagnosis


# ===========================================================================
# Q3: Fixation Detection (Q-series circulation stagnation)
# ===========================================================================

# PURPOSE: Pydantic モデル — 固着検出リクエスト/レスポンス
class FixationRequest(BaseModel):
    text: str = ""
    threshold: float = 0.3


class FixationResponse(BaseModel):
    timestamp: str
    total_hits: int
    has_fixation: bool
    dominant_pattern: Optional[str] = None
    max_score: float = 0.0
    alerts: list[str] = Field(default_factory=list)
    pattern_scores: dict[str, float] = Field(default_factory=dict)
    text_length: int = 0


# PURPOSE: Q3 固着パターン検出 + Sympatheia 通知
async def fixation_analyze(req: FixationRequest) -> FixationResponse:
    """テキスト表層の停止ワードから固着パターンを検出し、通知する。

    Q-series の辺にマッピングされた停止ワードの出現頻度から
    固着スコアを算出し、閾値超過で Sympatheia 通知を発行する。
    """
    now = datetime.now(timezone.utc)

    try:
        from mekhane.taxis.fixation_detector import detect_fixation, FIXATION_PATTERNS
    except ImportError as e:
        logger.warning("fixation_detector import failed: %s", e)
        return FixationResponse(
            timestamp=now.isoformat(),
            total_hits=0,
            has_fixation=False,
        )

    report = detect_fixation(req.text, threshold=req.threshold)

    # 閾値超過で通知
    if report.has_fixation:
        # 支配的パターンの名前を取得
        dominant_name = ""
        if report.dominant_pattern:
            pattern = FIXATION_PATTERNS.get(report.dominant_pattern)
            dominant_name = pattern.name if pattern else report.dominant_pattern

        level = "HIGH" if report.max_score > 0.7 else "INFO"
        _send_notification(
            source="Q-series",
            level=level,
            title=f"🔄 固着検出: {dominant_name}",
            body=report.summary,
            data={
                "dominant_pattern": report.dominant_pattern,
                "max_score": report.max_score,
                "alerts": report.alerts,
            },
        )

    return FixationResponse(
        timestamp=now.isoformat(),
        total_hits=report.total_hits,
        has_fixation=report.has_fixation,
        dominant_pattern=report.dominant_pattern,
        max_score=report.max_score,
        alerts=report.alerts,
        pattern_scores=report.pattern_scores,
        text_length=report.text_length,
    )


# ===========================================================================
# Q3-b: WF Usage Pattern Detection (定理ログからの偏り検出)
# ===========================================================================

# PURPOSE: Pydantic モデル — WF パターン検出リクエスト/レスポンス
class WFPatternRequest(BaseModel):
    days: int = 7
    records: list = Field(default_factory=list)


class WFPatternResponse(BaseModel):
    timestamp: str
    total_records: int
    ee_ratio: float = 0.0
    entropy_ratio: float = 0.0
    has_imbalance: bool = False
    alerts: list[str] = Field(default_factory=list)
    unused_theorems: list[str] = Field(default_factory=list)
    top_theorem: str = ""
    top_count: int = 0
    family_counts: dict[str, int] = Field(default_factory=dict)


# PURPOSE: Q3-b WF 使用パターン偏り検出 + Sympatheia 通知
async def wf_pattern_analyze(req: WFPatternRequest) -> WFPatternResponse:
    """定理ログから WF 使用パターンの偏りを検出し、通知する。

    Explore/Exploit 比率、族エントロピー、未使用定理を分析し、
    偏りが閾値を超えた場合に Sympatheia 通知を発行する。
    """
    now = datetime.now(timezone.utc)

    try:
        from mekhane.taxis.wf_pattern_detector import detect_wf_pattern
    except ImportError as e:
        logger.warning("wf_pattern_detector import failed: %s", e)
        return WFPatternResponse(
            timestamp=now.isoformat(),
            total_records=0,
        )

    report = detect_wf_pattern(
        days=req.days,
        records=req.records if req.records else None,
    )

    # 偏り検出で通知
    if report.has_imbalance:
        alert_summary = " / ".join(report.alerts[:3])
        level = "HIGH" if len(report.alerts) >= 2 else "INFO"
        _send_notification(
            source="Q-series",
            level=level,
            title="📊 WF パターン偏り検出",
            body=f"E/E比: {report.ee_ratio:.2f}, エントロピー比: {report.entropy_ratio:.2f}\n{alert_summary}",
            data={
                "ee_ratio": report.ee_ratio,
                "entropy_ratio": report.entropy_ratio,
                "unused_theorems": report.unused_theorems,
                "alerts": report.alerts,
            },
        )

    return WFPatternResponse(
        timestamp=now.isoformat(),
        total_records=report.total_records,
        ee_ratio=report.ee_ratio,
        entropy_ratio=report.entropy_ratio,
        has_imbalance=report.has_imbalance,
        alerts=report.alerts,
        unused_theorems=report.unused_theorems,
        top_theorem=report.top_theorem,
        top_count=report.top_count,
        family_counts=report.family_counts,
    )


# ===========================================================================
# Q3-c: Cognitive Scan (fixation + wf_pattern → WBC 統合)
# ===========================================================================

# PURPOSE: 認知スキャン リクエスト/レスポンスモデル
class CognitiveScanRequest(BaseModel):
    text: str = ""
    days: int = 7
    threshold: float = 0.5
    records: list = Field(default_factory=list)


class CognitiveScanResponse(BaseModel):
    timestamp: str
    cognitive_score: float = 0.0
    fixation_detected: bool = False
    fixation_ratio: float = 0.0
    wf_imbalance_detected: bool = False
    wf_ee_ratio: float = 0.0
    wf_entropy_ratio: float = 0.0
    wf_alert_count: int = 0
    wbc_triggered: bool = False
    wbc_threat_score: int = 0
    alerts: list[str] = Field(default_factory=list)
    components: dict[str, float] = Field(default_factory=dict)


# PURPOSE: Q3-c 認知スキャン — fixation + wf_pattern を複合スコアに変換し WBC 接続
async def cognitive_scan(req: CognitiveScanRequest) -> CognitiveScanResponse:
    """認知スキャン: テキスト固着 + WF偏りを複合スコア化し、閾値超過で WBC アラート発行。

    スコア配分:
        fixation (停止ワード比率)     → 最大 0.4
        wf_alerts (偏りアラート数)     → 最大 0.3
        ee_extreme (E/E 極端偏り)     → 最大 0.3
    """
    now = datetime.now(timezone.utc)
    alerts: list[str] = []
    components: dict[str, float] = {}

    # --- Phase (a): テキスト固着検出 ---
    fixation_detected = False
    fixation_ratio = 0.0
    if req.text:
        try:
            fix_resp = await fixation_analyze(FixationRequest(text=req.text))
            fixation_detected = fix_resp.has_fixation
            fixation_ratio = fix_resp.max_score
            if fixation_detected:
                alerts.append(f"固着検出: スコア {fixation_ratio:.2f}")
        except Exception as e:  # noqa: BLE001
            logger.warning("cognitive_scan: fixation_analyze failed: %s", e)

    # --- Phase (b): WF パターン偏り検出 ---
    wf_imbalance = False
    wf_ee_ratio = 0.5
    wf_entropy_ratio = 1.0
    wf_alert_count = 0
    try:
        wf_resp = await wf_pattern_analyze(
            WFPatternRequest(days=req.days, records=req.records)
        )
        wf_imbalance = wf_resp.has_imbalance
        wf_ee_ratio = wf_resp.ee_ratio
        wf_entropy_ratio = wf_resp.entropy_ratio
        wf_alert_count = len(wf_resp.alerts)
        if wf_imbalance:
            alerts.extend(wf_resp.alerts[:3])
    except Exception as e:  # noqa: BLE001
        logger.warning("cognitive_scan: wf_pattern_analyze failed: %s", e)

    # --- 複合スコア算出 (0.0 - 1.0) ---
    score = 0.0

    # 固着成分: 停止ワード比率 / 0.3 で正規化、最大 0.4
    fix_component = 0.0
    if fixation_detected and fixation_ratio > 0:
        fix_component = 0.4 * min(fixation_ratio / 0.3, 1.0)
    score += fix_component
    components["fixation"] = round(fix_component, 3)

    # WF アラート成分: アラート数 / 4 で正規化、最大 0.3
    wf_alert_component = 0.0
    if wf_imbalance and wf_alert_count > 0:
        wf_alert_component = 0.3 * min(wf_alert_count / 4, 1.0)
    score += wf_alert_component
    components["wf_alerts"] = round(wf_alert_component, 3)

    # E/E 極端偏り成分: 0.2 未満 or 0.8 超で 0.3
    ee_component = 0.0
    if wf_ee_ratio < 0.2 or wf_ee_ratio > 0.8:
        ee_component = 0.3
    score += ee_component
    components["ee_extreme"] = round(ee_component, 3)

    score = round(min(score, 1.0), 3)

    # --- WBC 接続: 閾値超過で自動アラート発行 ---
    wbc_triggered = False
    wbc_threat_score = 0
    if score >= req.threshold:
        severity = "high" if score >= 0.7 else "medium"
        alert_summary = " / ".join(alerts[:3]) if alerts else "認知的偏り検出"
        try:
            wbc_resp = await wbc_analyze(WBCRequest(
                source="Q-series",
                severity=severity,
                details=f"Cognitive scan score={score:.2f}: {alert_summary}",
                files=[],
            ))
            wbc_triggered = True
            wbc_threat_score = wbc_resp.threatScore
            alerts.append(f"WBC アラート発行: threatScore={wbc_threat_score}")
        except Exception as e:  # noqa: BLE001
            logger.warning("cognitive_scan: wbc_analyze failed: %s", e)

    # 通知 (スコア閾値超過 or 固着+偏り両方検出)
    if wbc_triggered or (fixation_detected and wf_imbalance):
        level = "HIGH" if score >= 0.7 else "INFO"
        _send_notification(
            source="Q-series",
            level=level,
            title="🧠 認知スキャン: 偏り検出",
            body=(
                f"Score: {score:.2f}\n"
                f"固着: {'⚠️' if fixation_detected else '✅'} "
                f"(ratio={fixation_ratio:.2f})\n"
                f"WF偏り: {'⚠️' if wf_imbalance else '✅'} "
                f"(E/E={wf_ee_ratio:.2f}, entropy={wf_entropy_ratio:.2f})\n"
                f"WBC: {'🚨 発行' if wbc_triggered else '未発行'}"
            ),
            data={"score": score, "components": components},
        )

    return CognitiveScanResponse(
        timestamp=now.isoformat(),
        cognitive_score=score,
        fixation_detected=fixation_detected,
        fixation_ratio=fixation_ratio,
        wf_imbalance_detected=wf_imbalance,
        wf_ee_ratio=wf_ee_ratio,
        wf_entropy_ratio=wf_entropy_ratio,
        wf_alert_count=wf_alert_count,
        wbc_triggered=wbc_triggered,
        wbc_threat_score=wbc_threat_score,
        alerts=alerts,
        components=components,
    )


# ===========================================================================
# WF-10: Weekly Digest
# ===========================================================================

# PURPOSE: Weekly digest computation
async def weekly_digest(req: DigestRequest) -> DigestResponse:
    """Memory compression: aggregate all metrics."""
    now = datetime.now(timezone.utc)
    one_week_ago = (now - timedelta(weeks=1)).isoformat()

    hb = _read_json(STATE_LOGS / "heartbeat.json")
    fm = _read_json(STATE_CACHE / "file_monitor_state.json")
    git = _read_json(STATE_CACHE / "git_sentinel_state.json")

    wbc = _read_json(STATE_VIOLATIONS / "wbc_state.json", {"alerts": []})
    week_alerts = [a for a in wbc.get("alerts", []) if a.get("timestamp", "") > one_week_ago]

    health_file = STATE_LOGS / "health_metrics.jsonl"
    health_scores: list[float] = []
    try:
        for line in health_file.read_text("utf-8").strip().split("\n")[-200:]:
            try:
                m = json.loads(line)
                if m.get("timestamp", "") > one_week_ago:
                    health_scores.append(m.get("score", 0))
            except (json.JSONDecodeError, KeyError):
                continue
    except (FileNotFoundError, OSError) as e:
        logger.debug("health_metrics.jsonl read skipped: %s", e)

    sessions_dir = HANDOFF_DIR
    session_count = 0
    try:
        for f in list_handoff_files(sessions_dir):
            try:
                if f.stat().st_mtime > (now - timedelta(weeks=1)).timestamp():
                    session_count += 1
            except OSError:
                continue
    except (FileNotFoundError, OSError) as e:
        logger.debug("sessions dir scan skipped: %s", e)

    result = DigestResponse(
        timestamp=now.isoformat(),
        weekEnding=now.strftime("%Y-%m-%d"),
        heartbeat={"beats": hb.get("beats", 0), "healthy": hb.get("healthy", True)},
        fileMon={"scans": fm.get("scanCount", 0), "changes": fm.get("changeCount", 0)},
        git={"dirty": git.get("dirty", False), "changes": git.get("totalChanges", 0),
             "branch": git.get("branch", "unknown")},
        wbc={"weekAlerts": len(week_alerts),
             "criticals": sum(1 for a in week_alerts if a.get("level") == "CRITICAL"),
             "highs": sum(1 for a in week_alerts if a.get("level") == "HIGH")},
        health={"avg": round(sum(health_scores) / len(health_scores), 2) if health_scores else 0,
                "samples": len(health_scores)},
        sessions=session_count,
    )

    _write_json(STATE_LOGS / "weekly_digest.json", result.model_dump())

    _send_notification(
        source="WF-10",
        level="INFO",
        title=f"📊 Weekly Digest — {result.weekEnding}",
        body=(
            f"Heart: {result.heartbeat.get('beats',0)} beats\n"
            f"Files: {result.fileMon.get('scans',0)} scans\n"
            f"Git: {result.git.get('changes',0)} changes\n"
            f"WBC: {result.wbc.get('weekAlerts',0)} alerts\n"
            f"Sessions: {result.sessions}"
        ),
        data=result.model_dump(),
    )

    return result


# ===========================================================================
# WF-11: Attractor Dispatch
# ===========================================================================

_advisor = None


# PURPOSE: Lazy init for AttractorAdvisor
def _get_advisor():
    """Lazy init for AttractorAdvisor."""
    global _advisor
    if _advisor is None:
        try:
            from mekhane.fep.attractor_advisor import AttractorAdvisor
            _advisor = AttractorAdvisor(force_cpu=True, use_gnosis=False)
            logger.info("AttractorAdvisor initialized")
        except Exception as e:  # noqa: BLE001
            logger.warning("AttractorAdvisor init failed: %s", e)
    return _advisor


# PURPOSE: Attractor dispatch
async def attractor_dispatch(req: AttractorRequest) -> AttractorResponse:
    """Reflex arc: theorem recommendation via TheoremAttractor."""
    now = datetime.now(timezone.utc)
    context = req.context or req.text or ""
    state_file = STATE_LOGS / "attractor_dispatch.json"
    state = _read_json(state_file, {"dispatches": [], "totalDispatches": 0})

    recommendation = None
    auto_dispatch = False

    advisor = _get_advisor()
    if advisor and context:
        try:
            rec = advisor.recommend_theorem(context, top_k=1)
            if rec and rec.primary_theorem:
                recommendation = {
                    "theorem": rec.primary_theorem,
                    "name": rec.theorem_workflows[0][1] if rec.theorem_workflows else "",
                    "series": rec.primary_theorem[0],
                    "command": rec.primary_command,
                    "confidence": round(rec.confidence, 3),
                }
                auto_dispatch = rec.confidence >= 0.7
        except Exception as e:  # noqa: BLE001
            logger.warning("TheoremAttractor error: %s", e)

    state["dispatches"] = state.get("dispatches", [])[-50:]
    state["dispatches"].append({
        "timestamp": now.isoformat(),
        "context": context[:200],
        "recommendation": recommendation,
        "autoDispatched": auto_dispatch,
    })
    state["totalDispatches"] = state.get("totalDispatches", 0) + 1
    _write_json(state_file, state)

    return AttractorResponse(
        timestamp=now.isoformat(),
        recommendation=recommendation,
        autoDispatch=auto_dispatch,
        context=context[:100],
    )


# ===========================================================================
# WF-12: Feedback Loop (homeostasis)
# ===========================================================================

# PURPOSE: Feedback loop
async def feedback_loop(req: FeedbackRequest) -> FeedbackResponse:
    """Homeostasis: dynamic threshold adjustment."""
    now = datetime.now(timezone.utc)
    three_days_ago = (now - timedelta(days=3)).isoformat()
    config = _load_config()

    scores: list[float] = []
    try:
        for line in (STATE_LOGS / "health_metrics.jsonl").read_text("utf-8").strip().split("\n")[-200:]:
            try:
                m = json.loads(line)
                if m.get("timestamp", "") > three_days_ago:
                    scores.append(m.get("score", 0))
            except (json.JSONDecodeError, KeyError):
                continue
    except (FileNotFoundError, OSError) as e:
        logger.debug("health_metrics.jsonl read skipped (feedback): %s", e)

    wbc = _read_json(STATE_VIOLATIONS / "wbc_state.json", {"alerts": []})
    wbc_alerts = len([a for a in wbc.get("alerts", []) if a.get("timestamp", "") > three_days_ago])

    avg = sum(scores) / len(scores) if scores else 0.5
    trend = 0.0
    if len(scores) >= 6:
        recent3 = sum(scores[-3:]) / 3
        prev3 = sum(scores[-6:-3]) / 3
        trend = recent3 - prev3

    adjustments: list[str] = []
    old_th = {**config.get("thresholds", {})}

    if avg > 0.9 and len(scores) >= 10:
        config["thresholds"]["health_high"] = max(0.3, config["thresholds"].get("health_high", 0.5) - 0.05)
        adjustments.append(f"health_high: {old_th.get('health_high')} → {config['thresholds']['health_high']}")

    if avg < 0.4 and len(scores) >= 5:
        config["thresholds"]["health_high"] = min(0.7, config["thresholds"].get("health_high", 0.5) + 0.05)
        adjustments.append(f"health_high: {old_th.get('health_high')} → {config['thresholds']['health_high']}")

    if wbc_alerts > 10:
        config["thresholds"]["stale_minutes"] = min(120, config["thresholds"].get("stale_minutes", 60) + 15)
        adjustments.append(f"stale_minutes: → {config['thresholds']['stale_minutes']}")

    adjusted = len(adjustments) > 0
    if adjusted:
        config["lastAdjusted"] = now.isoformat()
        history = config.get("adjustmentHistory", [])[-20:]
        history.append({"timestamp": now.isoformat(), "changes": adjustments})
        config["adjustmentHistory"] = history
        _write_json(STATE_CACHE / "sympatheia_config.json", config)

        _send_notification(
            source="WF-12",
            level="INFO",
            title="⚖️ Homeostasis: threshold adjustment",
            body="\n".join(f"• {a}" for a in adjustments),
            data={"adjustments": adjustments},
        )

    return FeedbackResponse(
        timestamp=now.isoformat(),
        metrics={"avg": round(avg, 2), "trend": round(trend, 2), "samples": len(scores), "wbcAlerts": wbc_alerts},
        thresholds=config.get("thresholds", {}),
        adjusted=adjusted,
        adjustments=adjustments,
    )


# ===========================================================================
# WF-14: Incoming Router
# ===========================================================================

ROUTES: dict[str, dict[str, str]] = {
    "health": {"target": "health-alert", "wf": "WF-05"},
    "session-start": {"target": "session-state", "wf": "WF-06"},
    "session-end": {"target": "session-state", "wf": "WF-06"},
    "paper": {"target": "incoming-digest", "wf": "WF-03"},
    "alert": {"target": "wbc-alert", "wf": "WF-09"},
    "wbc": {"target": "wbc-alert", "wf": "WF-09"},
    "feedback": {"target": "feedback-loop", "wf": "WF-12"},
    "git": {"target": "git-sentinel", "wf": "WF-13"},
    "digest": {"target": "weekly-digest", "wf": "WF-10"},
    "heartbeat": {"target": "heartbeat", "wf": "WF-15"},
    "attractor": {"target": "attractor", "wf": "WF-11"},
}


# PURPOSE: Incoming route handler
async def incoming_route(req: RouteRequest) -> RouteResponse:
    """Thalamus: classify input + forward."""
    now = datetime.now(timezone.utc)
    route_type = req.type.lower()
    route = ROUTES.get(route_type)

    log_file = STATE_LOGS / "incoming_router.jsonl"
    routed_wf = route["wf"] if route else "UNKNOWN"
    try:
        # JSONL: 既存スキーマ {timestamp, type, routed, source} を維持
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": now.isoformat(),
                "type": route_type,
                "routed": routed_wf,
                "source": req.source,
            }, ensure_ascii=False) + "\n")
        # 平文ログ: DualLogger で可読テキストも同時出力
        _router_logger.info(f"Route: {route_type} → {routed_wf}", source=req.source)
    except OSError as e:
        logger.debug("Router log write skipped: %s", e)

    if not route:
        return RouteResponse(
            error="Unknown type",
            timestamp=now.isoformat(),
            available=list(ROUTES.keys()),
        )

    import httpx
    n8n_base = os.getenv("N8N_BASE_URL", "http://localhost:5678")
    target_url = f"{n8n_base}/webhook/{route['target']}"
    forward_result = None

    try:
        resp = httpx.post(target_url, json=req.payload, timeout=15.0)
        try:
            forward_result = resp.json()
        except Exception:  # noqa: BLE001
            forward_result = {"status": resp.status_code, "text": resp.text[:200]}
    except Exception as e:  # noqa: BLE001
        forward_result = {"error": str(e)}

    return RouteResponse(
        routed=True,
        target=route["target"],
        wf=route["wf"],
        timestamp=now.isoformat(),
        forwardResult=forward_result,
    )


# ===========================================================================
# Notifications (receive + list)
# ===========================================================================

# PURPOSE: Receive notification
async def receive_notification(req: NotificationRequest) -> NotificationResponse:
    """Receive notification from n8n WF or internal module."""
    notif_id = _send_notification(
        source=req.source,
        level=req.level,
        title=req.title,
        body=req.body,
        data=req.data,
    )
    return NotificationResponse(
        id=notif_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        source=req.source,
        level=req.level,
        title=req.title,
        body=req.body,
        data=req.data,
    )


# PURPOSE: Convert latest Digestor candidates to virtual notifications
def _digestor_virtual_notifications(max_candidates: int = 5) -> list[dict]:
    """Convert latest Digestor report candidates to virtual notifications."""
    try:
        from mekhane.api.routes.digestor import _list_report_files, _load_report
        files = _list_report_files()
        if not files:
            return []
        report = _load_report(files[0])
        if not report or not report.candidates:
            return []
        virtuals = []
        for c in report.candidates[:max_candidates]:
            topics_str = ", ".join(c.matched_topics[:3]) if c.matched_topics else ""
            body_parts = [f"スコア: {c.score:.0%}"]
            if c.rationale:
                body_parts.append(c.rationale[:200])
            if topics_str:
                body_parts.append(f"トピック: {topics_str}")
            if c.url:
                body_parts.append(f"URL: {c.url}")
            virtuals.append({
                "id": f"digestor-{hash(c.title) & 0xFFFF:04x}",
                "timestamp": report.timestamp,
                "source": "🧬 Digestor",
                "level": "INFO",
                "title": f"📰 {c.title}",
                "body": "\n".join(body_parts),
                "data": {"digestor": True, "score": c.score, "url": c.url or ""},
            })
        return virtuals
    except Exception as e:  # noqa: BLE001
        logger.debug("Digestor virtual notifications skipped: %s", e)
        return []
