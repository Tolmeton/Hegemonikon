#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/api/routes/
# PURPOSE: Session Notes API — F2 セッション＝ノート (動的ナレッジ)
"""
Session Notes Routes — SessionNotes の REST API 公開

GET    /api/notes                    — ノート一覧 (PJ フィルタ付き)
GET    /api/notes/{session_id}       — ノート詳細 + チャンク
POST   /api/notes/{session_id}/digest — セッションを消化→ノート化
POST   /api/notes/digest-all         — 全未処理を一括消化
GET    /api/notes/{session_id}/links — リンク一覧
GET    /api/notes/search             — ベクトル類似検索
POST   /api/notes/{session_id}/classify — LLM 分類実行
GET    /api/notes/merge              — 類似チャンク統合候補
GET    /api/notes/{session_id}/resume — セッション再開用コンテキスト
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("hegemonikon.api.notes")

router = APIRouter(prefix="/notes", tags=["notes"])


# ------------------------------------------------------------------
# Lazy singleton — SessionNotes は SessionStore に依存
# ------------------------------------------------------------------

_notes_instance = None


def _get_notes():
    """SessionNotes シングルトンを取得 (遅延初期化)."""
    global _notes_instance
    if _notes_instance is None:
        from mekhane.ochema.session_notes import SessionNotes
        _notes_instance = SessionNotes()
    return _notes_instance


# ------------------------------------------------------------------
# Pydantic Models
# ------------------------------------------------------------------

class NoteChunkItem(BaseModel):
    """ノートチャンクの概要."""
    path: str
    content: str = Field(description="チャンクの Markdown テキスト")
    turn_range: list[int] = Field(default_factory=list, description="[start, end] ターン番号")
    metadata: dict = Field(default_factory=dict)


class NoteListItem(BaseModel):
    """ノート一覧の項目."""
    model_config = ConfigDict(populate_by_name=True)
    session_id: str = Field(alias="sessionId", default="")
    project: str = ""
    date: str = ""
    title: str = ""


class NoteListResponse(BaseModel):
    """ノート一覧レスポンス."""
    items: list[NoteListItem]
    total: int


class NoteDetailResponse(BaseModel):
    """ノート詳細レスポンス."""
    model_config = ConfigDict(populate_by_name=True)
    session_id: str = Field(alias="sessionId", default="")
    project: str = ""
    title: str = ""
    chunks: list[NoteChunkItem] = Field(default_factory=list)
    total_chunks: int = 0


class DigestResponse(BaseModel):
    """Digest 実行結果."""
    model_config = ConfigDict(populate_by_name=True)
    session_id: str = Field(alias="sessionId", default="")
    chunks_created: int = 0
    chunk_paths: list[str] = Field(default_factory=list)


class DigestAllResponse(BaseModel):
    """一括 Digest 結果."""
    total_chunks: int = 0


class LinkItem(BaseModel):
    """ノート間リンク."""
    source: str
    target: str
    distance: float = 0.0


class LinksResponse(BaseModel):
    """リンク一覧レスポンス."""
    model_config = ConfigDict(populate_by_name=True)
    session_id: str = Field(alias="sessionId", default="")
    links_created: int = 0
    backlinks: list[LinkItem] = Field(default_factory=list)


class SearchResultItem(BaseModel):
    """ベクトル検索結果."""
    path: str
    content: str
    distance: float = 0.0
    metadata: dict = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """検索レスポンス."""
    query: str
    results: list[SearchResultItem]
    total: int


class ClassifyResponse(BaseModel):
    """LLM 分類結果."""
    model_config = ConfigDict(populate_by_name=True)
    session_id: str = Field(alias="sessionId", default="")
    project: str = ""
    topics: list[str] = Field(default_factory=list)
    summary: str = ""
    confidence: float = 0.0


class F2ClassificationResponse(BaseModel):
    """F2 Fisher 固有分解ベースの分類結果."""
    model_config = ConfigDict(populate_by_name=True)
    session_id: str = Field(alias="sessionId", default="")
    cluster_label: str = Field(default="", alias="clusterLabel")
    cluster_id: int = Field(default=-1, alias="clusterId")
    tags: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    coords: list[float] = Field(default_factory=list)
    classified_at: str = Field(default="", alias="classifiedAt")
    found: bool = True


class F2SummaryItem(BaseModel):
    """クラスタごとの集計."""
    model_config = ConfigDict(populate_by_name=True)
    cluster_label: str = Field(alias="clusterLabel", default="")
    count: int = 0
    avg_confidence: float = Field(alias="avgConfidence", default=0.0)


class F2SummaryResponse(BaseModel):
    """F2 分類サマリー."""
    clusters: list[F2SummaryItem] = Field(default_factory=list)
    total: int = 0


class MergeCandidateItem(BaseModel):
    """類似チャンク統合候補."""
    chunk_a: str
    chunk_b: str
    similarity: float = 0.0
    synthesis: str = Field(default="", description="LLM 統合サマリー (オプション)")


class MergeResponse(BaseModel):
    """統合候補レスポンス."""
    candidates: list[MergeCandidateItem]
    total: int


class ResumeResponse(BaseModel):
    """セッション再開用コンテキスト."""
    model_config = ConfigDict(populate_by_name=True)
    session_id: str = Field(alias="sessionId", default="")
    turns: list[dict] = Field(default_factory=list, description="Cortex API contents 形式")
    total_turns: int = 0


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@router.get("", response_model=NoteListResponse)
async def list_notes(
    project: str = Query("", description="PJ 名でフィルタ (空=全 PJ)"),
) -> NoteListResponse:
    """ノート一覧を取得。PJ フィルタ付き。"""
    notes = _get_notes()
    try:
        items = notes.list_notes(project=project)
        return NoteListResponse(
            items=[NoteListItem(
                session_id=n.get("session_id", ""),
                project=n.get("project", ""),
                date=n.get("date", ""),
                title=n.get("title", ""),
            ) for n in items],
            total=len(items),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("list_notes failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/search", response_model=SearchResponse)
async def search_notes(
    q: str = Query(..., min_length=1, description="検索クエリ"),
    top_k: int = Query(5, ge=1, le=50, description="結果数"),
) -> SearchResponse:
    """ベクトル類似検索でノートを検索。"""
    notes = _get_notes()
    try:
        results = notes.get_relevant_chunks(query=q, top_k=top_k)
        return SearchResponse(
            query=q,
            results=[SearchResultItem(
                path=str(r.get("path", "")),
                content=r.get("content", ""),
                distance=r.get("distance", 0.0),
                metadata=r.get("metadata", {}),
            ) for r in results],
            total=len(results),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("search_notes failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/merge", response_model=MergeResponse)
async def merge_similar(
    project: str = Query("", description="PJ 名でフィルタ"),
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="類似度閾値"),
    synthesize: bool = Query(False, description="LLM 統合サマリーを生成するか"),
) -> MergeResponse:
    """類似チャンク統合候補を取得。"""
    notes = _get_notes()
    try:
        candidates = notes.merge_similar(
            project=project, threshold=threshold, synthesize=synthesize,
        )
        return MergeResponse(
            candidates=[MergeCandidateItem(
                chunk_a=str(c.get("chunk_a", c.get("path_a", ""))),
                chunk_b=str(c.get("chunk_b", c.get("path_b", ""))),
                similarity=c.get("similarity", 0.0),
                synthesis=c.get("synthesis", ""),
            ) for c in candidates],
            total=len(candidates),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("merge_similar failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/digest-all", response_model=DigestAllResponse)
async def digest_all() -> DigestAllResponse:
    """全未処理セッションを一括 digest する。"""
    notes = _get_notes()
    try:
        total = notes.digest_all()
        return DigestAllResponse(total_chunks=total)
    except Exception as exc:  # noqa: BLE001
        logger.error("digest_all failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{session_id}", response_model=NoteDetailResponse)
async def get_note(session_id: str) -> NoteDetailResponse:
    """ノート詳細 + チャンク一覧を取得。"""
    notes = _get_notes()
    try:
        # list_notes で該当セッションのノートを取得
        all_notes = notes.list_notes()
        matching = [n for n in all_notes if n.get("session_id") == session_id]

        if not matching:
            raise HTTPException(status_code=404, detail=f"Note not found: {session_id}")

        note = matching[0]

        # チャンクファイルを読み込み
        chunks = []
        note_path = note.get("path")
        if note_path:
            from pathlib import Path
            chunk_dir = Path(note_path).parent
            if chunk_dir.is_dir():
                for chunk_file in sorted(chunk_dir.glob("*.md")):
                    try:
                        content = chunk_file.read_text(encoding="utf-8")
                        chunks.append(NoteChunkItem(
                            path=str(chunk_file),
                            content=content,
                        ))
                    except Exception:  # noqa: BLE001
                        pass

        return NoteDetailResponse(
            session_id=session_id,
            project=note.get("project", ""),
            title=note.get("title", ""),
            chunks=chunks,
            total_chunks=len(chunks),
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("get_note failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{session_id}/digest", response_model=DigestResponse)
async def digest_session(session_id: str) -> DigestResponse:
    """セッションを消化→ノート化。"""
    notes = _get_notes()
    try:
        chunk_paths = notes.digest(session_id=session_id)
        return DigestResponse(
            session_id=session_id,
            chunks_created=len(chunk_paths),
            chunk_paths=[str(p) for p in chunk_paths],
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("digest failed for %s: %s", session_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{session_id}/links", response_model=LinksResponse)
async def get_links(session_id: str) -> LinksResponse:
    """リンク一覧を取得。"""
    notes = _get_notes()
    try:
        links_created = notes.link(session_id=session_id)

        # バックリンクはノート内の全チャンクに対して取得
        all_notes = notes.list_notes()
        matching = [n for n in all_notes if n.get("session_id") == session_id]

        backlinks = []
        if matching and matching[0].get("path"):
            from pathlib import Path
            chunk_dir = Path(matching[0]["path"]).parent
            for chunk_file in chunk_dir.glob("*.md"):
                try:
                    bl = notes.get_backlinks(chunk_file)
                    for link in bl:
                        backlinks.append(LinkItem(
                            source=str(link.get("source", "")),
                            target=str(link.get("target", "")),
                            distance=link.get("distance", 0.0),
                        ))
                except Exception:  # noqa: BLE001
                    pass

        return LinksResponse(
            session_id=session_id,
            links_created=links_created,
            backlinks=backlinks,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("get_links failed for %s: %s", session_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{session_id}/classify", response_model=ClassifyResponse)
async def classify_session(session_id: str) -> ClassifyResponse:
    """LLM でセッションを分類。"""
    notes = _get_notes()
    try:
        result = notes.classify_with_llm(session_id=session_id)
        return ClassifyResponse(
            session_id=session_id,
            project=result.get("project", ""),
            topics=result.get("topics", []),
            summary=result.get("summary", ""),
            confidence=result.get("confidence", 0.0),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("classify failed for %s: %s", session_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{session_id}/resume", response_model=ResumeResponse)
async def resume_session(
    session_id: str,
    max_chunks: int = Query(5, ge=1, le=20, description="最大チャンク数"),
) -> ResumeResponse:
    """セッション再開用のコンテキストを取得。Cortex API contents 形式。"""
    notes = _get_notes()
    try:
        turns = notes.resume_context(session_id=session_id, max_chunks=max_chunks)
        return ResumeResponse(
            session_id=session_id,
            turns=turns if isinstance(turns, list) else [],
            total_turns=len(turns) if isinstance(turns, list) else 0,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("resume_context failed for %s: %s", session_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ------------------------------------------------------------------
# F2 Fisher 固有分解ベースの分類結果
# ------------------------------------------------------------------

_store_instance = None


def _get_store():
    """PhantazeinStore シングルトンを取得 (遅延初期化)."""
    global _store_instance
    if _store_instance is None:
        from mekhane.symploke.phantazein_store import PhantazeinStore
        _store_instance = PhantazeinStore()
    return _store_instance


@router.get("/{session_id}/classification", response_model=F2ClassificationResponse)
async def get_f2_classification(session_id: str) -> F2ClassificationResponse:
    """F2 Fisher 分類結果を取得 (保存済みデータの読み取り)."""
    store = _get_store()
    try:
        row = store.get_session_classification(session_id)
        if row is None:
            return F2ClassificationResponse(
                session_id=session_id,
                found=False,
            )
        import json
        tags_raw = row.get("tags", "[]")
        tags = json.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw
        coords_raw = row.get("coords", "[]")
        coords = json.loads(coords_raw) if isinstance(coords_raw, str) else coords_raw

        return F2ClassificationResponse(
            session_id=session_id,
            cluster_label=row.get("cluster_label", ""),
            cluster_id=row.get("cluster_id", -1),
            tags=tags if isinstance(tags, list) else [],
            confidence=row.get("confidence", 0.0),
            coords=coords if isinstance(coords, list) else [],
            classified_at=row.get("classified_at", ""),
            found=True,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("get_f2_classification failed for %s: %s", session_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/classification-summary", response_model=F2SummaryResponse)
async def get_f2_summary() -> F2SummaryResponse:
    """F2 分類サマリー (クラスタごとの集計) を取得."""
    store = _get_store()
    try:
        summary = store.get_classification_summary()
        items = [
            F2SummaryItem(
                cluster_label=s.get("cluster_label", ""),
                count=s.get("count", 0),
                avg_confidence=s.get("avg_confidence", 0.0),
            )
            for s in summary
        ]
        return F2SummaryResponse(
            clusters=items,
            total=sum(s.count for s in items),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("get_f2_summary failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

