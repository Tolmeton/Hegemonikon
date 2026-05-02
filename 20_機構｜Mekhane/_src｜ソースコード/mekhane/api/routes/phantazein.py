#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/api/routes/phantazein.py
"""
Phantazein Routes — F1 Phantazein API (常駐 Boot Cache + Push ナレーション)

設計:
  1. サーバ起動時に Boot Context を自動プリロード (on_startup)
  2. バックグラウンドで定期リフレッシュ (asyncio.Task, 5分間隔)
  3. /status は常にキャッシュを返す (ブロッキングなし)
  4. /refresh で手動リフレッシュ
  5. /narrate で Gemini Flash による Push ナレーション生成
"""

import time
import asyncio
import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

logger = logging.getLogger("hegemonikon.api.phantazein")
router = APIRouter(prefix="/phantazein", tags=["Phantazein"])


# ── Boot Cache ──────────────────────────────────────────────
_boot_cache: Optional[dict[str, Any]] = None
_boot_cache_time: float = 0.0
_refresh_task: Optional[asyncio.Task[None]] = None

CACHE_TTL = 300.0  # 5 minutes — background task will proactively refresh


# ── Models ──────────────────────────────────────────────────

# PURPOSE: Phantazein status response model
class PhantazeinStatusResponse(BaseModel):
    status: str = "ok"
    last_boot_time: float
    axes: dict[str, Any] = Field(description="Boot context data for dashboard")


# PURPOSE: Phantazein narration response model
class PhantazeinNarrateResponse(BaseModel):
    section: str
    narration: str
    urgency: str = Field(description="high | medium | low")
    action_suggestions: list[str] = Field(
        default_factory=list, description="CCL commands"
    )


# PURPOSE: Phantazein session register request/response
class SessionRegisterRequest(BaseModel):
    context: str = ""
    agent: str = "claude"
    mode: str = "fast"

class SessionRegisterResponse(BaseModel):
    session_id: str
    axes: dict[str, Any]


# PURPOSE: Phantazein project snapshot request/response
class ProjectSnapshotRequest(BaseModel):
    project_id: str
    phase: str = ""
    status: str = ""
    notes: str = ""
    session_id: str = ""

class ProjectSnapshotResponse(BaseModel):
    success: bool
    project_id: str


# PURPOSE: Phantazein consistency check request/response
class ConsistencyCheckRequest(BaseModel):
    proposed_action: str
    session_id: str = ""

class ConsistencyCheckResponse(BaseModel):
    has_issues: bool
    issues: list[dict[str, Any]]
    narration: str


# ── Background Refresh Engine ───────────────────────────────

# PURPOSE: Boot Context の同期ロードを asyncio.to_thread で非同期化
def _sync_get_boot_context(mode: str, context: Optional[str] = None) -> dict[str, Any]:
    """Synchronous wrapper for boot_integration.get_boot_context.

    ↓ asyncio.to_thread に渡すための通常関数 (ラムダではなく名前付き関数で Pyre 互換).
    """
    from mekhane.symploke.boot_integration import get_boot_context
    return get_boot_context(mode=mode, context=context)


# PURPOSE: キャッシュを更新する単発関数
async def _refresh_boot_cache(
    mode: str = "fast", context: Optional[str] = None
) -> dict[str, Any]:
    """Boot Context を再構築し、結果をキャッシュに保存する."""
    global _boot_cache, _boot_cache_time

    logger.info("Phantazein: Refreshing boot cache (mode=%s)", mode)
    t0 = time.monotonic()

    try:
        result = await asyncio.to_thread(_sync_get_boot_context, mode, context)
        # numpy / datetime → JSON-safe にサニタイズ
        sanitized: dict[str, Any] = json.loads(json.dumps(result, default=str))
        _boot_cache = sanitized
        _boot_cache_time = time.time()
        elapsed = time.monotonic() - t0
        logger.info(
            "Phantazein: Boot cache refreshed (%.1fs, %d axes)",
            elapsed,
            len(sanitized),
        )
        return _boot_cache
    except Exception as exc:  # noqa: BLE001
        logger.error("Phantazein: Boot cache refresh failed: %s", exc)
        # Keep stale cache if refresh fails
        if _boot_cache is not None:
            return _boot_cache
        return {}


# PURPOSE: サーバ起動時に自動起動するバックグラウンドリフレッシュループ
async def _background_refresh_loop() -> None:
    """Server startup → 初回プリロード → CACHE_TTL 毎にリフレッシュ.

    このタスクはサーバの lifespan 中ずっと動き続ける。
    """
    # 初回プリロード (fast mode でブロッキング時間を最小化)
    await _refresh_boot_cache(mode="fast")
    logger.info("Phantazein: Initial boot cache preloaded")

    while True:
        try:
            await asyncio.sleep(CACHE_TTL)
            await _refresh_boot_cache(mode="fast")
        except asyncio.CancelledError:
            logger.info("Phantazein: Background refresh loop cancelled")
            break
        except Exception as exc:  # noqa: BLE001
            logger.error("Phantazein: Background refresh error: %s", exc)
            # Error → wait half TTL before retry
            await asyncio.sleep(CACHE_TTL / 2)


# PURPOSE: ルーター起動/停止で background task を管理する lifespan イベント
@router.on_event("startup")
async def _on_startup() -> None:
    global _refresh_task
    _refresh_task = asyncio.create_task(
        _background_refresh_loop(), name="phantazein-refresh"
    )
    logger.info("Phantazein: Background refresh task started")


@router.on_event("shutdown")
async def _on_shutdown() -> None:
    global _refresh_task
    if _refresh_task and not _refresh_task.done():
        _refresh_task.cancel()
        try:
            await _refresh_task
        except asyncio.CancelledError:
            pass
    logger.info("Phantazein: Background refresh task stopped")


# ── Endpoints ───────────────────────────────────────────────

@router.get("/status", response_model=PhantazeinStatusResponse)
async def get_status() -> PhantazeinStatusResponse:
    """常駐キャッシュから Boot 状態を返す (ノンブロッキング).

    バックグラウンドタスクがまだ初回ロードを完了していない場合のみ待機する。
    """
    global _boot_cache, _boot_cache_time

    if _boot_cache is None:
        # Background task hasn't finished yet → wait for it
        await _refresh_boot_cache(mode="fast")

    return PhantazeinStatusResponse(
        last_boot_time=_boot_cache_time, axes=_boot_cache or {}
    )


@router.post("/refresh", response_model=PhantazeinStatusResponse)
async def refresh_status(
    mode: str = Query("fast", description="fast | standard | detailed"),
) -> PhantazeinStatusResponse:
    """手動で Boot Context を再構築する."""
    await _refresh_boot_cache(mode=mode)
    return PhantazeinStatusResponse(
        last_boot_time=_boot_cache_time, axes=_boot_cache or {}
    )


@router.get("/narrate/{section}", response_model=PhantazeinNarrateResponse)
async def get_narration(section: str) -> PhantazeinNarrateResponse:
    """指定セクションの状態から Push 型ナレーションを生成する."""
    global _boot_cache

    if _boot_cache is None:
        await _refresh_boot_cache(mode="fast")

    if _boot_cache is None:
        return PhantazeinNarrateResponse(
            section=section,
            narration="システムが初期化されていません。",
            urgency="low",
            action_suggestions=[],
        )

    # 1. セクションデータ抽出
    section_map: dict[str, str] = {
        "handoff": "handoffs",
        "handoffs": "handoffs",
        "projects": "projects",
        "safety": "safety",
        "ki": "ki",
        "attractor": "attractor",
        "digestor": "digestor",
        "persona": "persona",
    }
    axis_key = section_map.get(section, "")
    if axis_key:
        target_axis = _boot_cache.get(axis_key, {})
        section_data = (
            target_axis.get("formatted", "") if isinstance(target_axis, dict) else ""
        )
    else:
        section_data = f"Unknown section '{section}'."

    if not section_data:
        section_data = "このセクションのデータはありません。"

    # 2. プロンプト
    prompt = f"""あなたはシステムのマザーブレイン（監視者/海馬）です。
以下の状態データを元に、AIパートナーである私（隊長/COO）に向けて、**1〜2文の短い日本語のナレーション**を押し出し（Push型）で語りかけてください。
また、この状況の「緊急度(urgency)」と、もしやるべきことがあれば「次に実行すべきCCLコマンド(action_suggestions)」をJSONで提案してください。

[ルール]
- ナレーションは敬語（〜です、〜ます、〜しています）。
- エラーや未消化タスクがあればそれを指摘する。
- 順調なら落ち着いた報告をする。
- 決して長文にしない。

[セクション: {section}]
[状態データ]
{section_data}

[出力形式 (厳密なJSONのみ)]
{{
  "narration": "語りかけるナレーションテキスト（1-2文）",
  "urgency": "low, medium, or high",
  "action_suggestions": ["/CCL形式の提案コマンド", "..."]
}}"""

    # 3. CortexAPI → Gemini Flash
    try:
        from mekhane.ochema.service import OchemaService
        from mekhane.ochema.model_defaults import FLASH

        svc = OchemaService.get()
        result = await svc.ask_async(
            message=prompt,
            model=FLASH,
            system_instruction="You must respond in valid JSON format only.",
        )

        # 4. JSON パース (markdown codeblock 除去)
        text = result.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        data = json.loads(text.strip())

        return PhantazeinNarrateResponse(
            section=section,
            narration=data.get("narration", "読み込み完了しました。"),
            urgency=data.get("urgency", "low"),
            action_suggestions=data.get("action_suggestions", []),
        )

    except Exception as e:  # noqa: BLE001
        logger.error("Phantazein narration failed: %s", e)
        return PhantazeinNarrateResponse(
            section=section,
            narration=f"ナレーションの生成に失敗しました: {str(e)[:50]}",
            urgency="low",
            action_suggestions=[],
        )


@router.post("/session/register", response_model=SessionRegisterResponse)
async def register_session(req: SessionRegisterRequest) -> SessionRegisterResponse:
    """セッションを開始し、最新の Boot Context と Session ID を返す."""
    from mekhane.symploke.phantazein_store import get_store
    
    store = get_store()
    session = store.register_session(context=req.context, agent=req.agent)
    
    global _boot_cache
    if _boot_cache is None:
        await _refresh_boot_cache(mode=req.mode)
        
    return SessionRegisterResponse(
        session_id=session.id,
        axes=_boot_cache or {}
    )


@router.post("/project/snapshot", response_model=ProjectSnapshotResponse)
async def project_snapshot(req: ProjectSnapshotRequest) -> ProjectSnapshotResponse:
    """プロジェクトの進捗スナップショットを記録する."""
    from mekhane.symploke.phantazein_store import get_store
    
    store = get_store()
    store.add_project_snapshot(
        project_id=req.project_id,
        phase=req.phase,
        status=req.status,
        notes=req.notes,
        session_id=req.session_id
    )
    return ProjectSnapshotResponse(success=True, project_id=req.project_id)


@router.post("/consistency", response_model=ConsistencyCheckResponse)
async def check_consistency(req: ConsistencyCheckRequest) -> ConsistencyCheckResponse:
    """直近の Handoff/WAL と予定作業を比較し、不整合を Gemini で検知する."""
    from mekhane.symploke.phantazein_store import get_store
    from mekhane.ochema.service import OchemaService
    from mekhane.ochema.model_defaults import FLASH
    
    # 1. 最近の Handoff 情報を集める
    global _boot_cache
    if _boot_cache is None:
        await _refresh_boot_cache(mode="fast")
        
    handoff_text = "No handoff data."
    if _boot_cache and "handoffs" in _boot_cache:
        hf = _boot_cache["handoffs"]
        handoff_text = hf.get("formatted", "") if isinstance(hf, dict) else ""
        
    # 2. Gemini に判定させる
    prompt = f"""あなたは Hegemonikón の行動パターン監査官（Consistency Checker）です。
以下の直近のHandoff（引き継ぎ事項）と、Agent がこれから行おうとしている「予定作業」を比較し、
作業の重複、方向性の矛盾、または見落としがないか検査してください。

[直近の Handoffs]
{handoff_text}

[予定作業]
{req.proposed_action}

[出力形式 (厳密なJSONのみ)]
{{
  "has_issues": true/false,
  "issues": [
    {{"severity": "high/medium/low", "issue": "問題の簡潔な説明", "details": "詳細"}}
  ],
  "narration": "AIへ向けた1-2文のPush型警告または承認メッセージ"
}}"""

    svc = OchemaService.get()
    try:
        result = await svc.ask_async(
            message=prompt,
            model=FLASH,
            system_instruction="You must respond in valid JSON format only.",
        )
        
        text = result.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        data = json.loads(text.strip())
        has_issues = data.get("has_issues", False)
        issues = data.get("issues", [])
        narration = data.get("narration", "不整合チェック完了")
        
        store = get_store()
        for iss in issues:
            store.log_consistency_issue(
                session_id=req.session_id,
                issue=iss.get("issue", "Unknown"),
                severity=iss.get("severity", "medium"),
                details=iss.get("details", "")
            )
            
        return ConsistencyCheckResponse(
            has_issues=has_issues,
            issues=issues,
            narration=narration
        )
    except Exception as e:  # noqa: BLE001
        import logging
        logging.getLogger("hegemonikon.api.phantazein").error("Consistency check failed: %s", e)
        return ConsistencyCheckResponse(
            has_issues=False,
            issues=[],
            narration="不整合チェックモジュールがエラーを返しました"
        )

