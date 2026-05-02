# PROOF: [L2/インフラ] <- mekhane/api/routes/feed.py F5 仮想Twitterフィード API
"""
Feed API — 仮想 Twitter フィードのエンドポイント

Endpoints:
    GET  /api/feed/timeline    — タイムライン取得
    POST /api/feed/generate    — PKS からツイート生成
    POST /api/feed/create      — 手動ツイート作成
    POST /api/feed/{id}/like   — いいね付与/解除
    POST /api/feed/{id}/comment — コメント追加
    GET  /api/feed/personas    — ペルソナ一覧
    GET  /api/feed/stats       — 統計
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from dataclasses import asdict

from mekhane.api.feed_engine import FeedEngine, BUILTIN_PERSONAS

router = APIRouter(prefix="/api/feed", tags=["feed"])
engine = FeedEngine()


# ─── Request / Response Models ──────────────────────────────


# PURPOSE: ツイート手動作成リクエスト
class CreatePostRequest(BaseModel):
    headline: str
    body: str
    persona_id: str = "fep_scholar"
    tags: list[str] = []
    source_url: str = ""


# PURPOSE: コメント追加リクエスト
class CommentRequest(BaseModel):
    text: str


# PURPOSE: フィードアイテムのレスポンスモデル
class FeedItemResponse(BaseModel):
    id: str
    persona_id: str
    persona_name: str
    persona_icon: str
    headline: str
    body: str
    source_url: str
    source_type: str
    tags: list[str]
    liked: bool
    comments: list[dict]
    created_at: str
    relevance_score: float


# PURPOSE: タイムラインレスポンスモデル
class TimelineResponse(BaseModel):
    items: list[FeedItemResponse]
    total: int
    has_more: bool


# PURPOSE: ペルソナレスポンスモデル
class PersonaResponse(BaseModel):
    id: str
    name: str
    icon: str
    description: str
    topics: list[str]


# PURPOSE: フィード統計レスポンスモデル
class StatsResponse(BaseModel):
    total_items: int
    total_likes: int
    total_comments: int
    persona_counts: dict[str, int]


# ─── Endpoints ──────────────────────────────────────────────


# PURPOSE: タイムライン取得
@router.get("/timeline")
async def get_timeline(
    limit: int = 20,
    offset: int = 0,
) -> TimelineResponse:
    """タイムライン取得（最新順）"""
    items, total = engine.get_timeline_with_count(limit=limit, offset=offset)
    return TimelineResponse(
        items=[FeedItemResponse(**asdict(item)) for item in items],
        total=total,
        has_more=offset + limit < total,
    )


# PURPOSE: PKS からツイート生成
@router.post("/generate")
async def generate_from_pks() -> dict:
    """PKS の最新 nuggets からツイートを生成"""
    try:
        from mekhane.api.routes.pks import _get_or_generate_push
        push_data = await _get_or_generate_push()
        nuggets = push_data.get("nuggets", [])
        if not nuggets:
            return {"generated": 0, "message": "PKS に新しい nuggets がありません"}

        # nugget を dict に変換（Pydantic モデルの場合）
        nugget_dicts = []
        for n in nuggets:
            if hasattr(n, "model_dump"):
                nugget_dicts.append(n.model_dump())
            elif hasattr(n, "dict"):
                nugget_dicts.append(n.dict())
            elif isinstance(n, dict):
                nugget_dicts.append(n)

        created = engine.ingest_from_pks(nugget_dicts)
        return {"generated": len(created), "items": [asdict(item) for item in created]}
    except ImportError:
        return {"generated": 0, "message": "PKS モジュールが利用不可"}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))


# PURPOSE: 手動ツイート作成
@router.post("/create")
async def create_post(req: CreatePostRequest) -> FeedItemResponse:
    """手動でツイートを作成"""
    item = engine.create_manual(
        headline=req.headline,
        body=req.body,
        persona_id=req.persona_id,
        tags=req.tags,
        source_url=req.source_url,
    )
    return FeedItemResponse(**asdict(item))


# PURPOSE: いいね付与/解除
@router.post("/{item_id}/like")
async def toggle_like(item_id: str) -> dict:
    """ツイートのいいねをトグル"""
    current = engine.get_item(item_id)
    if not current:
        raise HTTPException(status_code=404, detail="ツイートが見つかりません")

    if current.liked:
        engine.unlike(item_id)
        return {"liked": False, "item_id": item_id}
    else:
        engine.like(item_id)
        return {"liked": True, "item_id": item_id}


# PURPOSE: コメント追加
@router.post("/{item_id}/comment")
async def add_comment(item_id: str, req: CommentRequest) -> dict:
    """ツイートにコメントを追加"""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="コメントが空です")

    success = engine.comment(item_id, req.text.strip())
    if not success:
        raise HTTPException(status_code=404, detail="ツイートが見つかりません")

    return {"success": True, "item_id": item_id}


# PURPOSE: ペルソナ一覧
@router.get("/personas")
async def list_personas() -> list[PersonaResponse]:
    """利用可能なペルソナ一覧"""
    return [
        PersonaResponse(
            id=p.id,
            name=p.name,
            icon=p.icon,
            description=p.description,
            topics=p.topics,
        )
        for p in BUILTIN_PERSONAS
    ]


# PURPOSE: フィード統計
@router.get("/stats")
async def feed_stats() -> StatsResponse:
    """フィード統計（ストリーム集計）"""
    stats = engine.get_stats()
    return StatsResponse(
        total_items=stats["total_items"],
        total_likes=stats["total_likes"],
        total_comments=stats["total_comments"],
        persona_counts=stats["persona_counts"],
    )
