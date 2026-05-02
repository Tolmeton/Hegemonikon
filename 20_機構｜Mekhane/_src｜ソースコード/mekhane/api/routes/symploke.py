#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/api/routes/
# PURPOSE: Symploke 知識統合層の REST API — 統合検索, 人格, Boot コンテキスト
"""
Symploke Routes — 知識統合層 REST API

GET    /api/symploke/search          — Handoff/Sophia/Kairos 統合検索
GET    /api/symploke/persona         — 現在の Persona 状態
GET    /api/symploke/boot-context    — Boot コンテキスト (全軸データ)
GET    /api/symploke/stats           — 知識統合層の統計情報

Note:
    Symploke は mekhane/symploke/ の統合層。
    synergeia/ (マルチエージェント分散実行) とは全く別のモジュール。
"""

import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

logger = logging.getLogger("hegemonikon.api.symploke")
router = APIRouter(prefix="/symploke", tags=["symploke"])

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


# --- Pydantic Models ---


# PURPOSE: 検索結果アイテム
class SearchResultItem(BaseModel):
    """統合検索結果の1件。"""
    id: str
    source: str = Field(description="handoff | sophia | kairos | gnosis | chronos")
    score: float = Field(description="類似度スコア")
    title: str = ""
    snippet: str = Field(default="", description="内容の抜粋")
    metadata: dict = Field(default_factory=dict)


# PURPOSE: 統合検索レスポンス
class SearchResponse(BaseModel):
    """統合検索レスポンス。"""
    query: str
    results: list[SearchResultItem]
    total: int
    sources_searched: list[str]
    sources_failed: list[str] = Field(
        default_factory=list,
        description="初期化に失敗したソース名のリスト"
    )


# PURPOSE: Persona レスポンス
class PersonaResponse(BaseModel):
    """Persona 状態レスポンス。"""
    persona: dict = Field(description="Claude の Persona 状態")
    creator: dict = Field(default_factory=dict, description="Creator プロファイル")


# PURPOSE: Boot コンテキストレスポンス
class BootContextResponse(BaseModel):
    """Boot コンテキストレスポンス。"""
    mode: str
    axes: dict = Field(description="各軸のデータ")
    summary: str = ""


# PURPOSE: 統計レスポンス
class StatsResponse(BaseModel):
    """知識統合層の統計情報。"""
    handoff_count: int = 0
    sophia_index_exists: bool = False
    kairos_index_exists: bool = False
    persona_exists: bool = False
    boot_axes_available: list[str] = Field(default_factory=list)


# --- Routes ---


# PURPOSE: symploke の search 処理を実行する
@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="検索クエリ"),
    k: int = Query(5, ge=1, le=50, description="結果数"),
    sources: str = Query(
        "handoff,sophia,kairos,gnosis,chronos",
        description="検索対象 (カンマ区切り: handoff, sophia, kairos, gnosis, chronos)"
    ),
):
    """Handoff/Sophia/Kairos/Gnosis/Chronos の統合セマンティック検索。"""
    source_list = [s.strip() for s in sources.split(",")]
    
    try:
        from mekhane.symploke.search.search_factory import get_search_engine
        
        # ファクトリから初期化済みの SearchEngine を取得 (シングルトンキャッシュ)
        engine, init_errors = get_search_engine(source_list)
        
        # SearchEngine による統合検索 (リランキング + HybridSearch)
        engine_results = engine.search(q, sources=source_list, k=k)
        
        # IndexedResult → SearchResultItem
        results = []
        for r in engine_results:
            meta = r.metadata or {}
            title = meta.get("title") or meta.get("primary_task") or meta.get("ki_name") or str(r.doc_id)
            
            clean_meta = {}
            for key in ["timestamp", "file_path", "type", "artifact", "mneme", "category", "tags"]:
                if key in meta:
                    clean_meta[key] = meta[key]
                    
            results.append(SearchResultItem(
                id=str(r.doc_id),
                source=r.source.value,
                score=r.score,
                title=title,
                snippet=r.content[:200] if r.content else "",
                metadata=clean_meta,
            ))
            
        return SearchResponse(
            query=q,
            results=results[:k],
            total=len(results),
            sources_searched=list(engine.registered_sources),
            sources_failed=init_errors,
        )
        
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Symploke search failed: {exc}")
        return SearchResponse(
            query=q,
            results=[],
            total=0,
            sources_searched=[],
            sources_failed=source_list,
        )


# PURPOSE: persona を取得する
@router.get("/persona", response_model=PersonaResponse)
async def get_persona():
    """現在の Persona 状態と Creator プロファイルを取得。"""
    persona_data = {}
    creator_data = {}

    try:
        from mekhane.symploke.persona import load_persona, load_creator_profile
        persona_data = load_persona()
        creator_data = load_creator_profile()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Persona load failed: %s", exc)

    return PersonaResponse(persona=persona_data, creator=creator_data)


# PURPOSE: boot context を取得する (非同期 + タイムアウト)
@router.get("/boot-context", response_model=BootContextResponse)
async def get_boot_context(
    mode: str = Query("standard", description="fast | standard | detailed"),
    context: Optional[str] = Query(None, description="セッションコンテキスト"),
    timeout: int = Query(90, ge=10, le=300, description="タイムアウト秒数"),
):
    """Boot コンテキスト (全軸データ) を取得。

    Embedder は API Server startup で事前ロード済み (warm cache)。
    get_boot_context() は asyncio.to_thread で非同期実行し、
    API Server のイベントループをブロックしない。
    """
    import asyncio

    try:
        # PURPOSE: [L2-auto] _run の関数定義
        def _run():
            from mekhane.symploke.boot_integration import get_boot_context as _get_ctx
            return _get_ctx(mode=mode, context=context)

        result = await asyncio.wait_for(
            asyncio.to_thread(_run),
            timeout=timeout,
        )

        # numpy.float32 等の非JSON型を sanitize
        sanitized = json.loads(json.dumps(result, default=str))

        return BootContextResponse(
            mode=mode,
            axes=sanitized,
            summary=f"Boot context loaded ({mode} mode)",
        )
    except asyncio.TimeoutError:
        logger.warning("Boot context timed out after %ds", timeout)
        return BootContextResponse(
            mode=mode, axes={}, summary=f"Timeout after {timeout}s"
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Boot context load failed: %s", exc)
        return BootContextResponse(mode=mode, axes={}, summary=f"Error: {exc}")


# PURPOSE: stats を取得する
@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """知識統合層の統計情報を取得。"""
    from mekhane.symploke.sophia_ingest import DEFAULT_INDEX_PATH as SOPHIA_INDEX
    from mekhane.symploke.kairos_ingest import (
        DEFAULT_INDEX_PATH as KAIROS_INDEX,
        get_handoff_files,
    )

    # Handoff 数
    handoff_count = len(get_handoff_files())

    # Persona 存在確認
    persona_path = _PROJECT_ROOT / "kernel" / "persona" / "claude_persona.yaml"

    # Boot axes の確認
    boot_axes = []
    try:
        from mekhane.symploke.boot_axes import BOOT_AXES
        boot_axes = list(BOOT_AXES.keys()) if hasattr(BOOT_AXES, 'keys') else []
    except Exception:  # noqa: BLE001
        pass

    return StatsResponse(
        handoff_count=handoff_count,
        sophia_index_exists=SOPHIA_INDEX.exists(),
        kairos_index_exists=KAIROS_INDEX.exists(),
        persona_exists=persona_path.exists(),
        boot_axes_available=boot_axes,
    )
