#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/api/routes/ Digestor 候補閲覧 API
"""
Digestor API — digest_report の閲覧エンドポイント

Desktop App から Digestor 候補レポートを閲覧する。
scheduler が生成した digest_report_*.json を読み取ってフロントに返す。
"""

import glob
import json
import logging
import yaml
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/digestor", tags=["digestor"])

# ─── Constants ────────────────────────────────────────────
DIGESTOR_DIR = Path.home() / ".hegemonikon" / "digestor"


# ─── Models ───────────────────────────────────────────────
# PURPOSE: [L2-auto] Digestor 候補1件
class DigestCandidate(BaseModel):
    """Digestor 候補1件"""
    title: str
    source: str = ""
    url: str = ""
    score: float = 0.0
    matched_topics: list[str] = []
    rationale: str = ""
    suggested_templates: list[dict] = []


# PURPOSE: [L2-auto] Digestor レポート1件
class DigestReport(BaseModel):
    """Digestor レポート1件"""
    timestamp: str
    source: str = "gnosis"
    total_papers: int = 0
    candidates_selected: int = 0
    dry_run: bool = True
    candidates: list[DigestCandidate] = []
    filename: str = ""


# PURPOSE: [L2-auto] レポート一覧レスポンス
class DigestReportListResponse(BaseModel):
    """レポート一覧レスポンス"""
    reports: list[DigestReport]
    total: int


# ─── Helpers ──────────────────────────────────────────────
# PURPOSE: [L2-auto] JSON ファイルから DigestReport を生成。失敗時は None。
def _load_report(fpath: str) -> Optional[DigestReport]:
    """JSON ファイルから DigestReport を生成。失敗時は None。"""
    try:
        with open(fpath) as f:
            data = json.load(f)
        return DigestReport(
            timestamp=data.get("timestamp", ""),
            source=data.get("source", "gnosis"),
            total_papers=data.get("total_papers", 0),
            candidates_selected=data.get("candidates_selected", 0),
            dry_run=data.get("dry_run", True),
            candidates=[
                DigestCandidate(**c) for c in data.get("candidates", [])
            ],
            filename=Path(fpath).name,
        )
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        logger.warning("Failed to load digest report %s: %s", fpath, exc)
        return None


# PURPOSE: [L2-auto] digest_report_*.json を新しい順に返す。
def _list_report_files() -> list[str]:
    """digest_report_*.json を新しい順に返す。"""
    pattern = str(DIGESTOR_DIR / "digest_report_*.json")
    return sorted(glob.glob(pattern), reverse=True)


# ─── Endpoints ────────────────────────────────────────────
# PURPOSE: [L2-auto] digest_report 一覧を取得（新しい順）
@router.get("/reports", response_model=DigestReportListResponse)
async def list_reports(
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> DigestReportListResponse:
    """digest_report 一覧を取得（新しい順）"""
    files = _list_report_files()
    total = len(files)
    page = files[offset:offset + limit]

    reports: list[DigestReport] = []
    for fpath in page:
        report = _load_report(fpath)
        if report is not None:
            reports.append(report)

    return DigestReportListResponse(reports=reports, total=total)


# PURPOSE: [L2-auto] 最新のレポートを取得
@router.get("/latest", response_model=Optional[DigestReport])
async def latest_report() -> Optional[DigestReport]:
    """最新のレポートを取得"""
    files = _list_report_files()
    if not files:
        return None
    return _load_report(files[0])


# ─── Run Pipeline ─────────────────────────────────────────
# PURPOSE: [L2-auto] パイプライン実行リクエスト
class RunRequest(BaseModel):
    """パイプライン実行リクエスト"""
    max_papers: int = 30
    max_candidates: int = 10
    dry_run: bool = False
    topics: Optional[list[str]] = None


# PURPOSE: [L2-auto] パイプライン実行レスポンス
class RunResponse(BaseModel):
    """パイプライン実行レスポンス"""
    success: bool
    timestamp: str = ""
    total_papers: int = 0
    candidates_selected: int = 0
    candidates: list[DigestCandidate] = []
    error: str = ""


# PURPOSE: [L2-auto] Digestor パイプラインを実行（n8n Schedule Trigger 用）
@router.post("/run", response_model=RunResponse)
async def run_pipeline(req: RunRequest = RunRequest()) -> RunResponse:
    """Digestor パイプラインを実行（n8n Schedule Trigger 用）"""
    try:
        from mekhane.ergasterion.digestor.pipeline import DigestorPipeline

        pipeline = DigestorPipeline()
        result = pipeline.run(
            topics=req.topics,
            max_papers=req.max_papers,
            max_candidates=req.max_candidates,
            dry_run=req.dry_run,
        )

        candidates = []
        for c in result.candidates:
            candidates.append(DigestCandidate(
                title=c.paper.title,
                source=c.paper.source,
                url=c.paper.url or "",
                score=c.score,
                matched_topics=c.matched_topics,
                rationale=getattr(c, 'rationale', ''),
            ))

        return RunResponse(
            success=True,
            timestamp=result.timestamp,
            total_papers=result.total_papers,
            candidates_selected=result.candidates_selected,
            candidates=candidates,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Digestor pipeline failed: %s", exc)
        return RunResponse(success=False, error=str(exc))

# ─── Topics Management ────────────────────────────────────
TOPICS_FILE = Path(__file__).parent.parent.parent / "ergasterion" / "digestor" / "topics.yaml"

class TopicBase(BaseModel):
    id: str
    query: str
    digest_to: list[str]
    template_hint: str
    description: str

class TopicsResponse(BaseModel):
    topics: list[TopicBase]
    
class SuccessResponse(BaseModel):
    success: bool
    message: str

def _load_topics() -> dict:
    if not TOPICS_FILE.exists():
        return {"topics": []}
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"topics": []}

def _save_topics(data: dict):
    with open(TOPICS_FILE, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

@router.get("/topics", response_model=TopicsResponse)
def get_topics():
    """登録されている消化トピックの一覧を取得する"""
    data = _load_topics()
    return TopicsResponse(topics=data.get("topics", []))

@router.post("/topics", response_model=TopicBase)
def create_topic(topic: TopicBase):
    """新しい消化トピックを追加する"""
    data = _load_topics()
    topics = data.get("topics", [])
    
    if any(t.get("id") == topic.id for t in topics):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Topic '{topic.id}' already exists")
        
    topics.append(topic.model_dump())
    data["topics"] = topics
    _save_topics(data)
    
    return topic

@router.put("/topics/{topic_id}", response_model=TopicBase)
def update_topic(topic_id: str, topic_update: TopicBase):
    """既存の消化トピックを更新する"""
    data = _load_topics()
    topics = data.get("topics", [])
    
    for i, t in enumerate(topics):
        if t.get("id") == topic_id:
            # Ensure ID cannot be changed to an existing ID of another topic
            if topic_update.id != topic_id and any(other_t.get("id") == topic_update.id for other_t in topics):
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail=f"Target ID '{topic_update.id}' already in use")
                
            topics[i] = topic_update.model_dump()
            data["topics"] = topics
            _save_topics(data)
            return topic_update
            
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Topic not found")

@router.delete("/topics/{topic_id}", response_model=SuccessResponse)
def delete_topic(topic_id: str):
    """消化トピックを削除する"""
    data = _load_topics()
    topics = data.get("topics", [])
    
    initial_len = len(topics)
    topics = [t for t in topics if t.get("id") != topic_id]
    
    if len(topics) == initial_len:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Topic not found")
        
    data["topics"] = topics
    _save_topics(data)
    
    return SuccessResponse(success=True, message=f"Deleted topic {topic_id}")


# ─── Candidate Approval ──────────────────────────────────
from mekhane.paths import INCOMING_DIR

class ApproveRequest(BaseModel):
    title: str
    source: str
    url: str = ""
    score: float = 0.0
    matched_topics: list[str] = []
    rationale: str = ""

class ApproveResponse(BaseModel):
    success: bool
    filename: str
    message: str

@router.post("/approve", response_model=ApproveResponse)
def approve_candidate(req: ApproveRequest):
    """消化候補を承認し、incoming/ に /eat 入力ファイルを配置する"""
    from datetime import datetime

    INCOMING_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d")
    safe_title = "".join(
        ch if ch.isalnum() or ch in "-_ " else "" for ch in req.title[:40]
    ).strip().replace(" ", "_")
    filename = f"eat_{timestamp}_approved_{safe_title}.md"
    filepath = INCOMING_DIR / filename

    if filepath.exists():
        return ApproveResponse(success=True, filename=filename, message="Already approved")

    # digest_to を topics.yaml から取得
    topics_data = _load_topics()
    digest_targets = []
    for topic in topics_data.get("topics", []):
        if topic.get("id") in req.matched_topics:
            digest_targets.extend(topic.get("digest_to", []))
    targets_str = ", ".join(set(digest_targets)) if digest_targets else "未定"

    content = f"""---
title: "{req.title}"
source: {req.source}
url: {req.url or 'N/A'}
score: {req.score:.2f}
matched_topics: [{', '.join(req.matched_topics)}]
digest_to: [{targets_str}]
approved: {timestamp}
---

# /eat 承認済み: {req.title}

> **Score**: {req.score:.2f} | **Topics**: {', '.join(req.matched_topics)}
> **Source**: {req.source} | **URL**: {req.url or 'N/A'}
> **消化先候補**: {targets_str}

## 承認理由

{req.rationale or '(UI から承認)'}

## Phase 0: 圏の特定 (テンプレート)

| 項目 | 内容 |
|:-----|:-----|
| 圏 Ext (外部構造) | <!-- 論文の属する学問圏 --> |
| 圏 Int (内部構造) | <!-- HGK 内の対応する圏 --> |
| 関手 F (取込) | <!-- Ext → Int へのマッピング --> |
| 関手 G (忘却) | <!-- Int → Ext への写像 --> |

---

*Approved via Desktop App ({timestamp})*
"""
    filepath.write_text(content, encoding="utf-8")
    logger.info("Candidate approved: %s → %s", req.title[:40], filename)

    return ApproveResponse(success=True, filename=filename, message=f"Approved → incoming/{filename}")
