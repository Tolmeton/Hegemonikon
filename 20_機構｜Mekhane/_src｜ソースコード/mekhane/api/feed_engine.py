# PROOF: [L2/インフラ] <- mekhane/api/feed_engine.py F5 仮想Twitterフィードエンジン
"""
Feed Engine — 仮想 Twitter フィードの生成・管理エンジン

Creator 向けの知識プッシュを Twitter ライクなツイート形式で配信する。
情報ソース: PKS (知識プッシュ) + Digestor (論文候補) + Periskopē (検索)

Usage:
    engine = FeedEngine()
    items = engine.get_timeline(limit=20)
    engine.like(item_id)
    engine.comment(item_id, "面白い")
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# PURPOSE: フィードアイテム（ツイート）のデータモデル
@dataclass
class FeedItem:
    """フィードアイテム（ツイート）"""

    id: str
    persona_id: str
    persona_name: str
    persona_icon: str
    headline: str               # 3行要約（ツイート見出し）
    body: str                   # 10-20行要約（ツイート本文）
    source_url: str = ""        # 元ソースのURL
    source_type: str = "pks"    # pks | digestor | periskope | manual
    tags: list[str] = field(default_factory=list)
    liked: bool = False
    comments: list[dict] = field(default_factory=list)  # [{text, timestamp}]
    created_at: str = ""
    relevance_score: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


# PURPOSE: ペルソナ（仮想インフルエンサー）定義
@dataclass
class FeedPersona:
    """仮想インフルエンサーのペルソナ"""

    id: str
    name: str
    icon: str
    description: str
    system_prompt: str
    topics: list[str] = field(default_factory=list)


# 組込ペルソナ
BUILTIN_PERSONAS: list[FeedPersona] = [
    FeedPersona(
        id="fep_scholar",
        name="Φ-Observer",
        icon="🧠",
        description="FEP・能動推論・認知科学の最前線を追う研究者",
        system_prompt="あなたはFEP（自由エネルギー原理）と能動推論の専門家です。最新論文を Creator が興味を持つ角度で紹介してください。",
        topics=["FEP", "active inference", "predictive processing", "Bayesian brain"],
    ),
    FeedPersona(
        id="code_architect",
        name="Τέχνη",
        icon="⚙️",
        description="ソフトウェアアーキテクチャ・AI エンジニアリングの実践者",
        system_prompt="あなたはAIエンジニアリングとソフトウェアアーキテクチャの専門家です。MCP、LLM統合、エージェントシステムの最新動向を紹介してください。",
        topics=["MCP", "LLM", "agent systems", "software architecture"],
    ),
    FeedPersona(
        id="math_explorer",
        name="Κατηγορία",
        icon="∞",
        description="圏論・数学的構造のナビゲーター",
        system_prompt="あなたは圏論と数学的構造の専門家です。抽象代数、型理論、ホモトピー型理論の最新研究をCreatorが直感的に理解できる形で紹介してください。",
        topics=["category theory", "type theory", "homotopy", "abstract algebra"],
    ),
    FeedPersona(
        id="biz_strategist",
        name="Αγορά",
        icon="📊",
        description="AI ビジネス・収益化戦略のアナリスト",
        system_prompt="あなたはAIビジネスと収益化戦略の専門家です。AI SaaS、API経済、インディーハッカーの最新トレンドを紹介してください。",
        topics=["AI business", "SaaS", "API economy", "indie hacker"],
    ),
]


# PURPOSE: フィードエンジン本体
class FeedEngine:
    """
    仮想 Twitter フィードの生成・管理エンジン。

    データストア: SQLite (WAL モード) でツイートを永続化。
    旧 JSONL データがあれば自動マイグレーション。
    """

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data" / "feed"
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "feed.db"
        self._init_db()
        self._migrate_jsonl()

    def _init_db(self) -> None:
        """SQLite DB を初期化 (WAL モード)"""
        with self._conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feed_items (
                    id TEXT PRIMARY KEY,
                    persona_id TEXT NOT NULL,
                    persona_name TEXT NOT NULL,
                    persona_icon TEXT NOT NULL,
                    headline TEXT NOT NULL,
                    body TEXT NOT NULL DEFAULT '',
                    source_url TEXT NOT NULL DEFAULT '',
                    source_type TEXT NOT NULL DEFAULT 'pks',
                    tags TEXT NOT NULL DEFAULT '[]',
                    liked INTEGER NOT NULL DEFAULT 0,
                    comments TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    relevance_score REAL NOT NULL DEFAULT 0.0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_feed_created
                ON feed_items(created_at DESC)
            """)

    def _conn(self) -> sqlite3.Connection:
        """SQLite 接続を取得"""
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _row_to_item(self, row: sqlite3.Row) -> FeedItem:
        """行を FeedItem に変換"""
        return FeedItem(
            id=row["id"],
            persona_id=row["persona_id"],
            persona_name=row["persona_name"],
            persona_icon=row["persona_icon"],
            headline=row["headline"],
            body=row["body"],
            source_url=row["source_url"],
            source_type=row["source_type"],
            tags=json.loads(row["tags"]),
            liked=bool(row["liked"]),
            comments=json.loads(row["comments"]),
            created_at=row["created_at"],
            relevance_score=row["relevance_score"],
        )

    def _migrate_jsonl(self) -> None:
        """旧 JSONL データがあれば SQLite にマイグレーション"""
        jsonl_path = self.data_dir / "timeline.jsonl"
        if not jsonl_path.exists():
            return
        migrated = 0
        with self._conn() as conn:
            for line in jsonl_path.read_text(encoding="utf-8").strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    conn.execute(
                        "INSERT OR IGNORE INTO feed_items "
                        "(id, persona_id, persona_name, persona_icon, headline, body, "
                        "source_url, source_type, tags, liked, comments, created_at, relevance_score) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            data["id"], data["persona_id"], data["persona_name"],
                            data["persona_icon"], data["headline"], data.get("body", ""),
                            data.get("source_url", ""), data.get("source_type", "pks"),
                            json.dumps(data.get("tags", []), ensure_ascii=False),
                            1 if data.get("liked") else 0,
                            json.dumps(data.get("comments", []), ensure_ascii=False),
                            data.get("created_at", ""),
                            data.get("relevance_score", 0.0),
                        ),
                    )
                    migrated += 1
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue
        if migrated > 0:
            # マイグレーション完了後、JSONL を .bak にリネーム
            jsonl_path.rename(jsonl_path.with_suffix(".jsonl.bak"))

    # PURPOSE: タイムライン取得
    def get_timeline(self, limit: int = 20, offset: int = 0) -> list[FeedItem]:
        """タイムラインを取得（最新順）"""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM feed_items ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [self._row_to_item(r) for r in rows]

    # PURPOSE: タイムライン取得 + 総件数を同時返却
    def get_timeline_with_count(self, limit: int = 20, offset: int = 0) -> tuple[list[FeedItem], int]:
        """タイムライン + 総件数を同時取得"""
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM feed_items").fetchone()[0]
            rows = conn.execute(
                "SELECT * FROM feed_items ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [self._row_to_item(r) for r in rows], total

    # PURPOSE: タイムラインの総件数
    def get_timeline_count(self) -> int:
        """タイムラインの総件数を返す"""
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM feed_items").fetchone()[0]

    # PURPOSE: ツイートを追加
    def add_item(self, item: FeedItem) -> FeedItem:
        """ツイートをタイムラインに追加"""
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO feed_items "
                "(id, persona_id, persona_name, persona_icon, headline, body, "
                "source_url, source_type, tags, liked, comments, created_at, relevance_score) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item.id, item.persona_id, item.persona_name, item.persona_icon,
                    item.headline, item.body, item.source_url, item.source_type,
                    json.dumps(item.tags, ensure_ascii=False),
                    1 if item.liked else 0,
                    json.dumps(item.comments, ensure_ascii=False),
                    item.created_at, item.relevance_score,
                ),
            )
        return item

    # PURPOSE: いいねを付与
    def like(self, item_id: str) -> bool:
        """ツイートにいいねを付与"""
        with self._conn() as conn:
            cur = conn.execute("UPDATE feed_items SET liked=1 WHERE id=?", (item_id,))
            return cur.rowcount > 0

    # PURPOSE: いいねを取り消し
    def unlike(self, item_id: str) -> bool:
        """ツイートのいいねを取り消し"""
        with self._conn() as conn:
            cur = conn.execute("UPDATE feed_items SET liked=0 WHERE id=?", (item_id,))
            return cur.rowcount > 0

    # PURPOSE: コメント追加
    def comment(self, item_id: str, text: str) -> bool:
        """ツイートにコメントを追加"""
        with self._conn() as conn:
            row = conn.execute("SELECT comments FROM feed_items WHERE id=?", (item_id,)).fetchone()
            if not row:
                return False
            comments = json.loads(row["comments"])
            comments.append({
                "text": text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            conn.execute(
                "UPDATE feed_items SET comments=? WHERE id=?",
                (json.dumps(comments, ensure_ascii=False), item_id),
            )
            return True

    # PURPOSE: PKS の nuggets からツイートを生成
    def ingest_from_pks(self, nuggets: list[dict]) -> list[FeedItem]:
        """​PKS の nuggets からツイートを生成"""
        created = []
        for nugget in nuggets:
            persona = BUILTIN_PERSONAS[0]
            title = nugget.get("title", "").lower()
            for p in BUILTIN_PERSONAS:
                if any(t.lower() in title for t in p.topics):
                    persona = p
                    break

            item = FeedItem(
                id=uuid.uuid4().hex,
                persona_id=persona.id,
                persona_name=persona.name,
                persona_icon=persona.icon,
                headline=nugget.get("title", ""),
                body=nugget.get("abstract", nugget.get("push_reason", "")),
                source_url=nugget.get("url", ""),
                source_type="pks",
                tags=nugget.get("topics", []),
                relevance_score=nugget.get("relevance_score", 0.0),
            )
            self.add_item(item)
            created.append(item)

        return created

    # PURPOSE: 手動ツイート作成
    def create_manual(
        self,
        headline: str,
        body: str,
        persona_id: str = "fep_scholar",
        tags: list[str] | None = None,
        source_url: str = "",
    ) -> FeedItem:
        """手動でツイートを作成"""
        persona = next((p for p in BUILTIN_PERSONAS if p.id == persona_id), BUILTIN_PERSONAS[0])
        item = FeedItem(
            id=uuid.uuid4().hex,
            persona_id=persona.id,
            persona_name=persona.name,
            persona_icon=persona.icon,
            headline=headline,
            body=body,
            source_url=source_url,
            source_type="manual",
            tags=tags or [],
        )
        return self.add_item(item)

    # PURPOSE: ペルソナ一覧を返す
    def get_personas(self) -> list[FeedPersona]:
        """利用可能なペルソナ一覧を返す"""
        return BUILTIN_PERSONAS

    # PURPOSE: ストリーム集計でフィード統計を取得
    def get_stats(self) -> dict:
        """統計を SQL 集計で取得"""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as total, SUM(liked) as likes FROM feed_items"
            ).fetchone()
            total = row["total"] or 0
            likes = row["likes"] or 0

            # コメント数とペルソナカウントは行走査
            comments = 0
            persona_counts: dict[str, int] = {}
            for r in conn.execute("SELECT persona_name, comments FROM feed_items"):
                pname = r["persona_name"]
                persona_counts[pname] = persona_counts.get(pname, 0) + 1
                comments += len(json.loads(r["comments"]))

        return {
            "total_items": total,
            "total_likes": likes,
            "total_comments": comments,
            "persona_counts": persona_counts,
        }

    # PURPOSE: 単一アイテムを取得
    def get_item(self, item_id: str) -> FeedItem | None:
        """​ID でアイテムを取得"""
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM feed_items WHERE id=?", (item_id,)).fetchone()
        if not row:
            return None
        return self._row_to_item(row)
