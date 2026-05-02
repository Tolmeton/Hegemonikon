# PROOF: [L1/機能] <- mekhane/ochema/session_notes.py A0→永続化→セッションログのチャンク化・ベクトル化・リンク構造
# PURPOSE: SessionStore (正本) の生ログを加工し、MECE ディレクトリ + ベクトル検索 + リンク構造を構築する
from __future__ import annotations
from typing import Optional
"""SessionNotes — セッションログの加工品レイヤー。

正本 (SessionStore/SQLite) の生ログを:
  1. チャンク化してMECEディレクトリに保存 (digest)
  2. ベクトル計算してインデックスに登録 (embed)
  3. 類似ノート間のリンクを生成 (link)

Architecture:
  SessionStore (正本) ──digest()──▶ notes/{pj}/*.md (加工品)
                                        │
                                  embed()▼
                                  Notes vector table
                                        │
                                   link()▼
                                  _index/links.json

Usage:
    from mekhane.ochema.session_notes import SessionNotes

    notes = SessionNotes()
    notes.digest(session_id)                    # チャンク化 + ファイル保存
    notes.embed(session_id)                     # ベクトル化 (GPU 必要)
    notes.link(session_id)                      # リンク生成
    chunks = notes.get_relevant_chunks("FEP")   # 類似チャンク検索
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from mekhane.ochema.model_defaults import FLASH

logger = logging.getLogger(__name__)

# Default notes directory
_NOTES_DIR = Path.home() / ".config" / "ochema" / "notes"
_INDEX_DIR = _NOTES_DIR / "_index"
_DAILY_DIR = _NOTES_DIR / "_daily"

# Link similarity threshold (L2 distance, lower = more similar)
_LINK_THRESHOLD = 0.75


# PURPOSE: [L2-auto] SessionNotes のクラス定義
class SessionNotes:
    """セッションログの加工品レイヤー。

    正本 (SessionStore) から MECE ディレクトリ構造 + ベクトル検索 +
    リンク構造を構築する。
    """

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(self, notes_dir: Optional[Path] = None):
        """Initialize.

        Args:
            notes_dir: Override for notes directory (testing)
        """
        self.notes_dir = notes_dir or _NOTES_DIR
        self._index_dir = self.notes_dir / "_index"
        self._daily_dir = self.notes_dir / "_daily"
        self._links_file = self._index_dir / "links.json"
        self._tags_file = self._index_dir / "tags.json"

        # Ensure dirs exist
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self._index_dir.mkdir(parents=True, exist_ok=True)
        self._daily_dir.mkdir(parents=True, exist_ok=True)

    # --- Public API ---

    # PURPOSE: [L2-auto] digest の関数定義
    def digest(self, session_id: str, session_store=None) -> list[Path]:
        """正本のセッションを加工してMECEディレクトリに保存する。

        AMBITION F2 核心要件: 「具体を全く損ねずに各PJディレクトリに保存・分類仕訳」

        処理:
          1. ターン構造を保持したままチャンク化 (ターン境界を跨がない)
          2. 各チャンクにキーワード自動抽出
          3. チャンク↔ターン番号の対応表を保存 (逆参照用)
          4. セッション全体の要約を自動生成

        Args:
            session_id: SessionStore の session_id
            session_store: SessionStore instance (optional, auto-created if None)

        Returns:
            List of created chunk file paths
        """
        store = session_store or self._get_store()

        # 1. セッション情報取得
        session = store.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        turns = store.get_turns(session_id)
        if not turns:
            logger.warning("Session %s has no turns", session_id)
            return []

        # 2. メタデータ抽出
        meta = self._extract_metadata(session, turns)

        # 3. ターン構造を保持したチャンク化
        #    ターン境界を跨がない = 「具体を損ねない」の核心
        structured_chunks = self._chunk_turns(turns)

        # 4. 各チャンクのキーワード抽出
        for chunk in structured_chunks:
            chunk["keywords"] = self._extract_keywords(chunk["content"])

        # 5. セッション全体の要約 (extractive: 最初のユーザーメッセージ + 最後のモデルメッセージ)
        summary = self._generate_summary(turns)
        meta["summary"] = summary

        # 6. PJ ディレクトリ決定 + ファイル保存
        pj_dir = self.notes_dir / meta["project"]
        pj_dir.mkdir(parents=True, exist_ok=True)

        created_files: list[Path] = []
        turn_map: list[dict] = []  # チャンク↔ターン対応表

        for i, chunk in enumerate(structured_chunks):
            filename = f"{meta['date']}_{meta['slug']}_{i:02d}.md"
            filepath = pj_dir / filename

            # 拡張 frontmatter (ターン範囲 + キーワード + 要約)
            frontmatter = self._build_frontmatter(
                session_id, meta, i, len(structured_chunks),
                turn_start=chunk["turn_start"],
                turn_end=chunk["turn_end"],
                keywords=chunk["keywords"],
            )
            filepath.write_text(f"{frontmatter}\n{chunk['content']}\n", encoding="utf-8")
            created_files.append(filepath)

            # ターンマッピング記録
            turn_map.append({
                "chunk_idx": i,
                "file": str(filepath),
                "turn_start": chunk["turn_start"],
                "turn_end": chunk["turn_end"],
                "keywords": chunk["keywords"],
                "char_count": len(chunk["content"]),
            })

        # 6.5. セッションマップインデックスを更新 (O(1) 検索用)
        self._update_session_map(session_id, created_files)

        # 7. ターンマッピングを保存 (逆参照用)
        map_file = self._index_dir / f"turn_map_{session_id[:12]}.json"
        self._save_json(map_file, {
            "session_id": session_id,
            "total_turns": len(turns),
            "total_chunks": len(structured_chunks),
            "summary": summary,
            "chunks": turn_map,
        })

        # 8. セッション要約ファイルを生成
        summary_file = pj_dir / f"{meta['date']}_{meta['slug']}_summary.md"
        self._write_session_summary(summary_file, session_id, meta, created_files, turns)

        # 9. デイリーノートにリンク追記
        self._append_daily(meta["date"], meta, created_files)

        # 10. タグインデックス更新
        self._update_tags(meta, created_files)

        logger.info(
            "Digested session %s → %d chunks (%d turns) in %s/, summary: %s",
            session_id[:8], len(created_files), len(turns), meta["project"],
            summary[:60]
        )
        return created_files

    # PURPOSE: [L2-auto] embed の関数定義
    def embed(self, session_id: str, session_store=None) -> int:
        """加工済みチャンクをベクトル化してインデックスに登録する。

        Args:
            session_id: SessionStore の session_id
            session_store: SessionStore instance (optional)

        Returns:
            Number of chunks embedded
        """
        # digest 済みファイルを検索
        files = self._find_chunks_for_session(session_id)
        if not files:
            logger.warning("No digested files for session %s", session_id[:8])
            return 0

        # Gnōsis index (FAISSBackend)
        from mekhane.anamnesis.index import GnosisIndex
        from mekhane.anamnesis.backends.faiss_backend import FAISSBackend
        from mekhane.paths import GNOSIS_DB_DIR

        index = GnosisIndex()
        backend = FAISSBackend(GNOSIS_DB_DIR, table_name="notes")
        embedder = index._get_embedder()
        _table_name = "notes"

        # 既存キーを取得
        existing_keys: set[str] = set()
        if backend.exists():
            backend._load()
            for idx, meta in backend._metadata.items():
                pk = meta.get("primary_key", "")
                if pk:
                    existing_keys.add(str(pk))

        # チャンクデータ構築
        data = []
        for f in files:
            content = f.read_text(encoding="utf-8")
            meta = self._parse_frontmatter(content)
            body = self._strip_frontmatter(content)

            pk = f"notes:{f.parent.name}:{f.stem}"
            if pk in existing_keys:
                continue

            data.append({
                "primary_key": pk,
                "title": meta.get("title", f.stem),
                "source": "session_note",
                "abstract": body[:300],
                "content": body,
                "authors": "",
                "doi": "",
                "arxiv_id": "",
                "url": str(f),
                "citations": 0,
                "session_id": session_id,
                "project": meta.get("project", "general"),
                "tags": json.dumps(meta.get("tags", [])),
            })

        if not data:
            logger.info("All chunks already embedded for session %s", session_id[:8])
            return 0

        # バッチ embedding
        BATCH_SIZE = 32
        for i in range(0, len(data), BATCH_SIZE):
            batch = data[i:i + BATCH_SIZE]
            texts = [
                f"[session_note] {d['title']}\n{d['content'][:500]}"
                for d in batch
            ]
            vectors = embedder.embed_batch(texts)
            for d, v in zip(batch, vectors):
                d["vector"] = v

        # インデックスに追加
        backend.add(data)

        logger.info("Embedded %d chunks for session %s", len(data), session_id[:8])
        return len(data)

    # PURPOSE: [L2-auto] link の関数定義
    def link(self, session_id: str) -> int:
        """類似ノート間の双方向リンクを生成する。

        Args:
            session_id: SessionStore の session_id

        Returns:
            Number of links created
        """
        from mekhane.anamnesis.index import GnosisIndex
        from mekhane.anamnesis.backends.faiss_backend import FAISSBackend
        from mekhane.paths import GNOSIS_DB_DIR

        index = GnosisIndex()
        backend = FAISSBackend(GNOSIS_DB_DIR, table_name="notes")
        if not backend.exists():
            logger.warning("No notes index found")
            return 0

        embedder = index._get_embedder()

        # このセッションのチャンクを取得
        files = self._find_chunks_for_session(session_id)
        links = self._load_links()
        created = 0

        for f in files:
            content = f.read_text(encoding="utf-8")
            body = self._strip_frontmatter(content)
            pk = f"notes:{f.parent.name}:{f.stem}"

            # ベクトル検索で類似チャンクを取得
            qvec = embedder.embed(body[:500])
            results = backend.search_vector(qvec, k=6)

            for r in results:
                target_pk = r.get("primary_key", "")
                dist = r.get("_distance", 999)

                # 自分自身は除外、閾値以上は除外
                if target_pk == pk or dist > _LINK_THRESHOLD:
                    continue

                # 双方向リンク追加
                link_key = tuple(sorted([pk, target_pk]))
                link_id = f"{link_key[0]}--{link_key[1]}"

                if link_id not in links:
                    links[link_id] = {
                        "source": pk,
                        "target": target_pk,
                        "distance": round(dist, 4),
                        "created": datetime.now().isoformat(),
                    }
                    created += 1

        self._save_links(links)
        logger.info("Created %d links for session %s", created, session_id[:8])
        return created

    # PURPOSE: [L2-auto] get_relevant_chunks の関数定義
    def get_relevant_chunks(self, query: str, top_k: int = 5) -> list[dict]:
        """クエリに関連するチャンクをベクトル検索で取得する。

        Args:
            query: 検索クエリ
            top_k: 返すチャンク数

        Returns:
            List of dicts with path, content, distance, metadata
        """
        from mekhane.anamnesis.index import GnosisIndex
        from mekhane.anamnesis.backends.faiss_backend import FAISSBackend
        from mekhane.paths import GNOSIS_DB_DIR

        index = GnosisIndex()
        backend = FAISSBackend(GNOSIS_DB_DIR, table_name="notes")
        if not backend.exists():
            return []

        embedder = index._get_embedder()
        qvec = embedder.embed(query)

        results = backend.search_vector(qvec, k=top_k)
        return [
            {
                "path": r.get("url", ""),
                "content": r.get("content", ""),
                "distance": r.get("_distance", 999),
                "title": r.get("title", ""),
                "project": r.get("project", ""),
                "session_id": r.get("session_id", ""),
            }
            for r in results
        ]

    # --- GAP-A: 正本への逆参照 (traceability) ---

    # PURPOSE: [L2-auto] trace_to_source の関数定義
    def trace_to_source(self, chunk_path: Path, session_store=None) -> dict:
        """加工品チャンクから正本 (SessionStore) への正確な逆参照を取得する。

        チャンクに含まれるターン範囲を特定し、正本の該当ターンを
        直接取得できる形で返す。

        Args:
            chunk_path: 加工品チャンクの Path
            session_store: SessionStore (optional)

        Returns:
            Dict with session_id, turn_range, source_turns, etc.
        """
        content = chunk_path.read_text(encoding="utf-8")
        meta = self._parse_frontmatter(content)
        session_id = meta.get("session_id", "")
        chunk_info = meta.get("chunk", "0/0")
        turn_start = int(meta.get("turn_start", "0"))
        turn_end = int(meta.get("turn_end", "0"))

        result = {
            "session_id": session_id,
            "chunk": chunk_info,
            "turn_start": turn_start,
            "turn_end": turn_end,
            "source_store": "sqlite:sessions.db",
            "source_uri": f"session_store://{session_id}",
            "project": meta.get("project", ""),
            "keywords": meta.get("keywords", ""),
            "file": str(chunk_path),
        }

        # 正本からターンを取得して照合
        try:
            store = session_store or self._get_store()
            all_turns = store.get_turns(session_id)
            if all_turns and turn_start >= 0 and turn_end > 0:
                source_turns = all_turns[turn_start:turn_end]
                result["source_turns"] = [
                    {"role": t.get("role", ""), "content_preview": t.get("content", "")[:200]}
                    for t in source_turns
                ]
                result["verified"] = True
            else:
                result["verified"] = False
        except (OSError, ValueError, TypeError, AttributeError) as _e:
            logger.debug("Ignored exception: %s", _e)
            result["verified"] = False

        return result

    # --- GAP-B: バックリンク一覧 ---

    # PURPOSE: [L2-auto] get_backlinks の関数定義
    def get_backlinks(self, chunk_path: Path) -> list[dict]:
        """指定チャンクへのバックリンク一覧を取得する。

        Args:
            chunk_path: 対象チャンクの Path

        Returns:
            List of dicts with source, target, distance
        """
        pk = f"notes:{chunk_path.parent.name}:{chunk_path.stem}"
        links = self._load_links()
        backlinks = []

        for link_id, link_data in links.items():
            if pk in link_id:
                # 相手側のキーを取得
                other = link_data["target"] if link_data["source"] == pk else link_data["source"]
                backlinks.append({
                    "linked_to": other,
                    "distance": link_data.get("distance", 0),
                    "created": link_data.get("created", ""),
                })

        return backlinks

    # --- GAP-C: セッション再開コンテキスト ---

    # PURPOSE: [L2-auto] resume_context の関数定義
    def resume_context(self, session_id: str, max_chunks: int = 5,
                       format: str = "cortex") -> list[dict]:
        """セッション再開用のコンテキストをCortex API送信形式で取得する。

        AMBITION F2: 「分類されたノートはセッションも兼ねる
        (分類後もそのままセッションの続きを行える)」

        Cortex API の generateContent に直接注入可能な contents 形式で返す。
        ターン構造を復元し、user/model の交互配置を保証する。

        Args:
            session_id: 再開するセッションの ID
            max_chunks: 返す最大チャンク数
            format: 'cortex' (API形式) or 'raw' (生テキスト)

        Returns:
            Cortex API contents 形式のターンリスト
        """
        files = self._find_chunks_for_session(session_id)
        if not files:
            return []

        # 最新 N チャンクを取得 (時系列順)
        recent = files[-max_chunks:]

        if format == "raw":
            # 生テキスト形式
            result = []
            for f in recent:
                content = f.read_text(encoding="utf-8")
                body = self._strip_frontmatter(content)
                meta = self._parse_frontmatter(content)
                result.append({
                    "role": "context",
                    "content": body,
                    "chunk": meta.get("chunk", ""),
                    "path": str(f),
                    "project": meta.get("project", ""),
                })
            return result

        # Cortex API contents 形式: frontmatter メタデータ + 正本ターンから復元
        # マーカー (`## USER/MODEL`) 依存を排除し、frontmatter の turn_start/end を使用
        contents: list[dict] = []
        store = None  # store は最大 1 回だけ取得
        for f in recent:
            content = f.read_text(encoding="utf-8")
            body = self._strip_frontmatter(content)
            meta = self._parse_frontmatter(content)

            # 方法1: frontmatter の turn_start/end から正本ターンを復元 (高信頼)
            turn_start = int(meta.get("turn_start", "0"))
            turn_end = int(meta.get("turn_end", "0"))
            sid = meta.get("session_id", session_id)

            restored_from_store = False
            if turn_start >= 0 and turn_end > turn_start:
                try:
                    if store is None:
                        store = self._get_store()
                    all_turns = store.get_turns(sid)
                    if all_turns and turn_end <= len(all_turns):
                        for t in all_turns[turn_start:turn_end]:
                            role = "user" if t.get("role") == "user" else "model"
                            text = t.get("content", "").strip()
                            if text:
                                contents.append({
                                    "role": role,
                                    "parts": [{"text": text}],
                                })
                        restored_from_store = True
                except (OSError, ValueError, TypeError, AttributeError) as _e:
                    logger.debug("Ignored exception: %s", _e)

            # 方法2: フォールバック — チャンク本文からマーカーで復元
            if not restored_from_store:
                turn_blocks = re.split(r'\n## (USER|MODEL)\n', body)
                i = 1
                while i < len(turn_blocks) - 1:
                    role_label = turn_blocks[i].strip()
                    text = turn_blocks[i + 1].strip()
                    # --- セパレータを除去
                    text = text.rstrip("-").rstrip().rstrip("\n")
                    if text:
                        role = "user" if role_label == "USER" else "model"
                        contents.append({
                            "role": role,
                            "parts": [{"text": text}],
                        })
                    i += 2

        # user/model 交互配置を保証 (Cortex API 要件)
        merged: list[dict] = []
        for c in contents:
            if merged and merged[-1]["role"] == c["role"]:
                merged[-1]["parts"][0]["text"] += "\n\n" + c["parts"][0]["text"]
            else:
                merged.append(c)

        return merged

    # --- GAP-D: 類似チャンク統合 + 新アイデア生成 (MemX 的) ---

    # PURPOSE: [L2-auto] merge_similar の関数定義
    def merge_similar(self, project: str = "", threshold: float = 0.5,
                      synthesize: bool = False) -> list[dict]:
        """類似チャンクを発見し、オプションでLLM統合サマリーを生成する。

        AMBITION F2 MemX: 「似たテーマのメモをジャンル分け + 統合
        → 新しいアイデアの提供」

        synthesize=True の場合:
          1. 類似ペアの内容を読み込む
          2. LLM に統合サマリー + 新しい洞察の生成を依頼
          3. 結果を _index/merges/ に保存

        Args:
            project: フィルタするプロジェクト (空=全て)
            threshold: 統合候補の距離閾値 (低い=類似)
            synthesize: True で LLM 統合サマリーを生成

        Returns:
            List of merge candidates with chunk content and optional synthesis
        """
        links = self._load_links()
        candidates = []

        for link_id, link_data in links.items():
            dist = link_data.get("distance", 999)
            if dist > threshold:
                continue

            source_pk = link_data["source"]
            target_pk = link_data["target"]

            # プロジェクトフィルタ
            if project:
                source_pj = source_pk.split(":")[1] if ":" in source_pk else ""
                target_pj = target_pk.split(":")[1] if ":" in target_pk else ""
                if project not in (source_pj, target_pj):
                    continue

            candidate = {
                "source": source_pk,
                "target": target_pk,
                "distance": dist,
                "similarity": f"{1 - dist:.0%}",
            }

            # 両チャンクの内容を読み込む
            source_content = self._read_chunk_by_pk(source_pk)
            target_content = self._read_chunk_by_pk(target_pk)
            if source_content and target_content:
                candidate["source_preview"] = source_content[:200]
                candidate["target_preview"] = target_content[:200]

            # LLM 統合サマリー生成
            if synthesize and source_content and target_content:
                synthesis = self._synthesize_chunks(source_content, target_content)
                candidate["synthesis"] = synthesis

                # 結果を保存
                merges_dir = self._index_dir / "merges"
                merges_dir.mkdir(exist_ok=True)
                merge_file = merges_dir / f"merge_{link_id.replace('--', '_vs_')[:60]}.md"
                merge_file.write_text(
                    f"# 統合サマリー\n\n"
                    f"**類似度**: {candidate['similarity']}\n\n"
                    f"## ソース A\n{source_content[:500]}\n\n"
                    f"## ソース B\n{target_content[:500]}\n\n"
                    f"## 統合・新しい洞察\n{synthesis}\n",
                    encoding="utf-8"
                )
                candidate["merge_file"] = str(merge_file)

            candidates.append(candidate)

        candidates.sort(key=lambda c: c["distance"])
        return candidates

    # --- GAP-E: LLM 構造化分類 ---

    # PURPOSE: [L2-auto] classify_with_llm の関数定義
    def classify_with_llm(self, session_id: str, session_store=None) -> dict:
        """LLM で構造化分類する。プロジェクト + トピック + 要約を返す。

        Args:
            session_id: セッション ID
            session_store: SessionStore (optional)

        Returns:
            Dict with project, topics, summary, confidence
        """
        store = session_store or self._get_store()
        turns = store.get_turns(session_id)
        if not turns:
            return {"project": "general", "topics": [], "summary": "", "confidence": 0.0}

        # サンプリング: 最初3ターン + 最後2ターン (文脈と結論)
        sample_turns = turns[:3] + turns[-2:] if len(turns) > 5 else turns
        sample = "\n".join(
            f"{t['role']}: {t['content'][:200]}"
            for t in sample_turns
        )

        prompt = (
            "以下の会話ログを分析し、JSON 形式で回答してください。\n\n"
            "```json\n"
            '{\n'
            '  "project": "(ochema|periskope|hermeneus|hegemonikon|synteleia|dendron|hgk-app|mneme|general)",\n'
            '  "topics": ["トピック1", "トピック2"],\n'
            '  "summary": "1行要約",\n'
            '  "confidence": 0.0-1.0\n'
            '}\n'
            "```\n\n"
            f"--- 会話ログ ---\n{sample}\n---"
        )

        try:
            try:
                from mekhane.ochema.account_router import get_account_for
                account = get_account_for("chat")
            except ImportError as _e:
                logger.debug("Ignored exception: %s", _e)
                account = "default"
            client = CortexClient(model=FLASH, account=account)
            response = client.ask(prompt, max_tokens=200, temperature=0.0)

            # JSON 抽出 — code fence 除去 + 堅牢なパース
            text = response.text.strip()
            # markdown code fence を除去
            text = re.sub(r'```(?:json)?\s*', '', text)
            text = re.sub(r'```\s*$', '', text)
            # 最外 {} を貪欲に抽出 (ネストした配列に対応)
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    result = None
                if result and isinstance(result, dict):
                    valid_projects = {
                        "ochema", "periskope", "hermeneus", "hegemonikon",
                        "synteleia", "dendron", "hgk-app", "mneme", "general",
                    }
                    if result.get("project") not in valid_projects:
                        result["project"] = "general"
                    # 型安全性
                    result.setdefault("topics", [])
                    result.setdefault("summary", "")
                    result.setdefault("confidence", 0.5)
                    return result

            # JSON パース失敗時はフォールバック
            return {
                "project": self._infer_project(turns, "default"),
                "topics": [],
                "summary": "",
                "confidence": 0.5,
            }
        except (OSError, json.JSONDecodeError, KeyError, Exception) as e:  # Intentional Catch-All  # noqa: BLE001
            logger.warning("LLM classification failed: %s", e)
            return {
                "project": self._infer_project(turns, "default"),
                "topics": [],
                "summary": "",
                "confidence": 0.0,
            }

    # --- GAP-B extension: プロジェクト内のノート一覧 ---

    # PURPOSE: [L2-auto] list_notes の関数定義
    def list_notes(self, project: str = "") -> list[dict]:
        """プロジェクト内 (またはが全体) のノート一覧を取得する。

        Args:
            project: フィルタするプロジェクト (空=全PJ)

        Returns:
            List of dicts with path, project, date, title, session_id
        """
        results = []
        search_dir = self.notes_dir / project if project else self.notes_dir

        for md in sorted(search_dir.rglob("*.md")):
            if md.parent.name.startswith("_"):
                continue
            try:
                content = md.read_text(encoding="utf-8")[:2000]
                meta = self._parse_frontmatter(content)
                if not meta:
                    continue
                results.append({
                    "path": str(md),
                    "project": meta.get("project", md.parent.name),
                    "date": meta.get("date", ""),
                    "title": meta.get("title", md.stem),
                    "session_id": meta.get("session_id", ""),
                    "chunk": meta.get("chunk", ""),
                })
            except OSError as _e:
                logger.debug("Ignored exception: %s", _e)
                continue

        return results

    # PURPOSE: [L2-auto] digest_all の関数定義
    def digest_all(self, session_store=None) -> int:
        """全未処理セッションを一括 digest する。

        Returns:
            Total number of chunks created
        """
        store = session_store or self._get_store()
        sessions = store.list_sessions()
        total = 0
        for s in sessions:
            sid = s["session_id"]
            # 既に digest 済みならスキップ
            if self._find_chunks_for_session(sid):
                continue
            try:
                files = self.digest(sid, session_store=store)
                total += len(files)
            except (OSError, ValueError) as e:
                logger.warning("Failed to digest %s: %s", sid[:8], e)
        return total

    # --- Private Methods ---

    # PURPOSE: [L2-auto] _get_store の関数定義
    def _get_store(self):
        """Get or create default SessionStore."""
        from mekhane.ochema.session_store import get_default_store
        return get_default_store()

    # PURPOSE: [L2-auto] _extract_metadata の関数定義
    def _extract_metadata(self, session: dict, turns: list[dict]) -> dict:
        """セッションからメタデータを抽出する。"""
        # 日付
        created = session.get("created_at", "")
        if created:
            date = created[:10]  # YYYY-MM-DD
        else:
            date = datetime.now().strftime("%Y-%m-%d")

        # タイトル + スラッグ
        model = session.get("model", "unknown")
        account = session.get("account", "default")

        # 最初のユーザーメッセージからスラッグ生成
        first_user = ""
        for t in turns:
            if t.get("role") == "user":
                first_user = t.get("content", "")[:100]
                break

        slug = self._make_slug(first_user or f"session_{session.get('session_id', '')[:8]}")

        # PJ 推定 (アカウント名ベース、将来は LLM 分類)
        project = self._infer_project(turns, account)

        # タグ
        tags = [model, account, project]

        return {
            "date": date,
            "slug": slug,
            "project": project,
            "model": model,
            "account": account,
            "tags": tags,
            "title": first_user[:60] if first_user else slug,
        }

    # PURPOSE: [L2-auto] _infer_project の関数定義
    def _infer_project(self, turns: list[dict], account: str) -> str:
        """ターン内容からプロジェクト名を推定する。

        ルールベース (将来は LLM 分類に拡張可能)。
        """
        all_text = " ".join(t.get("content", "")[:200] for t in turns[:5]).lower()

        # キーワードマッチ
        project_keywords = {
            "ochema": ["cortex", "token", "vault", "oauth", "quota", "gemini api"],
            "periskope": ["research", "search", "periskope", "searxng", "brave"],
            "hermeneus": ["ccl", "dispatch", "workflow", "lmql"],
            "hegemonikon": ["fep", "axiom", "theorem", "doctrine", "bc-"],
            "synteleia": ["audit", "synteleia", "immunitas"],
            "dendron": ["dendron", "proof", "purpose", "existence"],
            "hgk-app": ["tauri", "three.js", "frontend", "vite", "hgk app"],
        }

        for project, keywords in project_keywords.items():
            if any(kw in all_text for kw in keywords):
                return project

        return "general"

    # PURPOSE: [L2-auto] _turns_to_text の関数定義
    def _turns_to_text(self, turns: list[dict]) -> str:
        """ターンリストをテキストに変換する。"""
        parts = []
        for t in turns:
            role = t.get("role", "unknown")
            content = t.get("content", "")
            parts.append(f"## {role.upper()}\n\n{content}")
        return "\n\n---\n\n".join(parts)

    # PURPOSE: [L2-auto] _chunk_text の関数定義
    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
        """テキストをセマンティック境界で分割する。

        KnowledgeIndexer._chunk_text() と同じアルゴリズム。
        """
        if len(text) <= chunk_size:
            return [text]

        # Phase 1: Markdown セクション分割
        sections = re.split(r'\n(?=#{1,4}\s|\-{3,})', text)

        chunks: list[str] = []
        for section in sections:
            section = section.strip()
            if not section:
                continue

            if len(section) <= chunk_size:
                chunks.append(section)
            else:
                # Phase 2: 空行で段落分割
                paragraphs = re.split(r'\n\s*\n', section)
                buffer = ""
                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue

                    if len(buffer) + len(para) + 2 <= chunk_size:
                        buffer = f"{buffer}\n\n{para}" if buffer else para
                    else:
                        if buffer:
                            chunks.append(buffer)
                        if len(para) > chunk_size:
                            # Phase 3: 改行で切る
                            start = 0
                            while start < len(para):
                                end = start + chunk_size
                                piece = para[start:end]
                                if end < len(para):
                                    last_nl = piece.rfind("\n")
                                    if last_nl > chunk_size // 2:
                                        end = start + last_nl + 1
                                        piece = para[start:end]
                                chunks.append(piece.strip())
                                start = max(start + 1, end - overlap)
                        else:
                            buffer = para
                            continue
                        buffer = ""
                if buffer:
                    chunks.append(buffer)

        return [c for c in chunks if c and len(c) > 20]

    # PURPOSE: [L2-auto] _make_slug の関数定義
    def _make_slug(self, text: str) -> str:
        """テキストからファイル名用スラッグを生成する。"""
        # ASCII + 日本語以外を除去、空白をアンダースコアに
        slug = re.sub(r'[^\w\s\u3040-\u9fff-]', '', text)
        slug = re.sub(r'\s+', '_', slug.strip())
        return slug[:50].rstrip('_') or "untitled"

    # PURPOSE: [L2-auto] _build_frontmatter の関数定義
    def _build_frontmatter(self, session_id: str, meta: dict, chunk_idx: int, total: int,
                            turn_start: int = 0, turn_end: int = 0,
                            keywords: list[str] | None = None) -> str:
        """YAML frontmatter を生成する。ターン範囲 + キーワード付き。"""
        kw_str = json.dumps(keywords or [], ensure_ascii=False)
        summary_line = meta.get('summary', '')[:80]
        return (
            f"---\n"
            f"session_id: {session_id}\n"
            f"source_uri: session_store://{session_id}\n"
            f"project: {meta['project']}\n"
            f"date: {meta['date']}\n"
            f"model: {meta['model']}\n"
            f"account: {meta['account']}\n"
            f"chunk: {chunk_idx}/{total}\n"
            f"turn_start: {turn_start}\n"
            f"turn_end: {turn_end}\n"
            f"keywords: {kw_str}\n"
            f"tags: {json.dumps(meta['tags'])}\n"
            f"title: \"{meta['title']}\"\n"
            f"summary: \"{summary_line}\"\n"
            f"---\n"
        )

    # PURPOSE: [L2-auto] _parse_frontmatter の関数定義
    def _parse_frontmatter(self, text: str) -> dict:
        """YAML frontmatter を解析する。"""
        match = re.match(r'^---\n(.*?)\n---\n', text, re.DOTALL)
        if not match:
            return {}
        meta = {}
        for line in match.group(1).split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                meta[key.strip()] = val.strip().strip('"')
        return meta

    # PURPOSE: [L2-auto] _strip_frontmatter の関数定義
    def _strip_frontmatter(self, text: str) -> str:
        """YAML frontmatter を除去する。"""
        return re.sub(r'^---\n.*?\n---\n', '', text, flags=re.DOTALL).strip()

    # PURPOSE: [L2-auto] _append_daily の関数定義
    def _append_daily(self, date: str, meta: dict, files: list[Path]) -> None:
        """デイリーノートにリンクを追記する。"""
        daily_file = self._daily_dir / f"{date}.md"

        if not daily_file.exists():
            daily_file.write_text(f"# Daily Notes — {date}\n\n", encoding="utf-8")

        links = [f"- [{f.stem}]({f})" for f in files]
        entry = (
            f"\n## {meta['title'][:60]}\n"
            f"- Project: {meta['project']}\n"
            f"- Model: {meta['model']}\n"
            f"- Chunks: {len(files)}\n"
            + "\n".join(links) + "\n"
        )

        with daily_file.open("a", encoding="utf-8") as fh:
            fh.write(entry)

    # PURPOSE: [L2-auto] _update_tags の関数定義
    def _update_tags(self, meta: dict, files: list[Path]) -> None:
        """タグインデックスを更新する。"""
        tags = self._load_json(self._tags_file) or {}

        for tag in meta.get("tags", []):
            if tag not in tags:
                tags[tag] = []
            for f in files:
                path_str = str(f)
                if path_str not in tags[tag]:
                    tags[tag].append(path_str)

        self._save_json(self._tags_file, tags)

    # PURPOSE: [L2-auto] _find_chunks_for_session の関数定義
    def _find_chunks_for_session(self, session_id: str) -> list[Path]:
        """session_id に対応する digest 済みファイルを検索する。

        O(1) インデックス検索: session_map.json を使用。
        インデックスがなければフォールバックで全スキャン + インデックス再構築。
        """
        # 1. インデックスから O(1) 検索
        session_map = self._load_session_map()
        if session_id in session_map:
            paths = [Path(p) for p in session_map[session_id] if Path(p).exists()]
            if paths:
                return sorted(paths)

        # 2. フォールバック: 全スキャン + インデックス再構築
        results = []
        for md in self.notes_dir.rglob("*.md"):
            if md.parent.name.startswith("_"):
                continue
            try:
                content = md.read_text(encoding="utf-8")[:2000]
                if f"session_id: {session_id}" in content:
                    results.append(md)
            except OSError as _e:
                logger.debug("Ignored exception: %s", _e)
                continue
        results = sorted(results)

        # インデックスに登録
        if results:
            self._update_session_map(session_id, results)

        return results

    def _load_session_map(self) -> dict:
        """session_map.json を読み込む。"""
        map_file = self._index_dir / "session_map.json"
        return self._load_json(map_file) or {}

    def _update_session_map(self, session_id: str, files: list[Path]) -> None:
        """session_map.json を更新する。"""
        map_file = self._index_dir / "session_map.json"
        session_map = self._load_json(map_file) or {}
        session_map[session_id] = [str(f) for f in files]
        self._save_json(map_file, session_map)

    # PURPOSE: [L2-auto] _load_links の関数定義
    def _load_links(self) -> dict:
        return self._load_json(self._links_file) or {}

    # PURPOSE: [L2-auto] _save_links の関数定義
    def _save_links(self, links: dict) -> None:
        self._save_json(self._links_file, links)

    # PURPOSE: [L2-auto] _load_json の関数定義
    def _load_json(self, path: Path) -> Optional[dict]:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as _e:
                logger.debug("Ignored exception: %s", _e)
                return None
        return None

    # PURPOSE: [L2-auto] _save_json の関数定義
    def _save_json(self, path: Path, data: dict) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- 新規 private メソッド: ターン構造保持チャンク ---

    # PURPOSE: [L2-auto] _chunk_turns の関数定義
    def _chunk_turns(self, turns: list[dict], max_chars: int = 1600) -> list[dict]:
        """ターン境界を跨がずにチャンク化する。

        user→model ペアを最小単位とし、ペア境界でのみ分割する。
        Mem0 設計思想: "chunked sessions break conversations at logical boundaries"

        アルゴリズム:
          1. ターンを user→model ペアにグループ化
          2. ペア単位でバッファに追加
          3. バッファが max_chars を超えたら、model 応答の後でのみ切る
          4. 単一の巨大ペア (max_chars 超) はそのまま 1 チャンクにする

        Returns:
            List of dicts: content, turn_start, turn_end
        """
        if not turns:
            return []

        # Phase 1: user→model ペアにグループ化
        pairs: list[dict] = []
        current_pair_texts: list[str] = []
        pair_start = 0

        for i, t in enumerate(turns):
            role = t.get("role", "unknown").upper()
            content = t.get("content", "")
            turn_text = f"## {role}\n\n{content}\n\n---\n\n"
            current_pair_texts.append(turn_text)

            # model 応答の後 or 最後のターンでペアを確定
            if role == "MODEL" or i == len(turns) - 1:
                pairs.append({
                    "content": "".join(current_pair_texts),
                    "turn_start": pair_start,
                    "turn_end": i + 1,
                })
                current_pair_texts = []
                pair_start = i + 1

        # Phase 2: ペア単位でバッファリング → チャンク化
        chunks: list[dict] = []
        buffer = ""
        buffer_start = pairs[0]["turn_start"] if pairs else 0

        # F4: Periskopē 長文レポート対応 (MarkdownChunker)
        try:
            from mekhane.anamnesis.chunker import MarkdownChunker
            chunker = MarkdownChunker(max_chars=max_chars)
        except ImportError:
            logger.warning("MarkdownChunker not found, skipping semantic chunking for large turns")
            chunker = None

        for pair in pairs:
            content_len = len(pair["content"])

            # 単一の巨大ペア (max_chars 超) の特例処理 (F4対応)
            if content_len > max_chars and chunker:
                # 既存バッファを確定
                if buffer.strip():
                    chunks.append({
                        "content": buffer.strip(),
                        "turn_start": buffer_start,
                        "turn_end": pair["turn_start"],
                    })
                    buffer = ""

                # MarkdownChunker でセクション単位に再帰分割
                sub_chunks = chunker.chunk(pair["content"], source_id="turn", title="")
                for sc in sub_chunks:
                    if sc.get("text", "").strip():
                        chunks.append({
                            "content": sc["text"].strip(),
                            "turn_start": pair["turn_start"],
                            "turn_end": pair["turn_end"],
                        })

                # バッファ開始位置を次へ更新
                buffer_start = pair["turn_end"]
                continue

            # バッファ + 新ペアが max_chars を超える → バッファを確定
            if buffer and len(buffer) + content_len > max_chars:
                chunks.append({
                    "content": buffer.strip(),
                    "turn_start": buffer_start,
                    "turn_end": pair["turn_start"],
                })
                buffer = ""
                buffer_start = pair["turn_start"]

            buffer += pair["content"]

        # 残りをチャンクに
        if buffer.strip():
            chunks.append({
                "content": buffer.strip(),
                "turn_start": buffer_start,
                "turn_end": pairs[-1]["turn_end"] if pairs else len(turns),
            })

        return chunks

    # PURPOSE: [L2-auto] _extract_keywords の関数定義
    @staticmethod
    def _extract_keywords(text: str, max_keywords: int = 8) -> list[str]:
        """テキストからキーワードを抽出する。

        Primary: YAKE (教師なし、外部コーパス不要、言語非依存、高速)
        Fallback: regex ベース (YAKE 未インストール時)
        """
        # YAKE で抽出 (推奨)
        try:
            import yake
            # 日本語+英語混在テキスト: lan="ja" でもASCII語を拾える
            kw_extractor = yake.KeywordExtractor(
                lan="ja",
                n=2,                # 最大 2-gram
                top=max_keywords,
                dedupLim=0.7,       # 重複排除閾値
                windowsSize=2,
            )
            raw_keywords = kw_extractor.extract_keywords(text[:3000])  # 入力制限
            yake_results = [kw for kw, _score in raw_keywords]
            if yake_results:
                return yake_results[:max_keywords]
        except ImportError:
            pass  # YAKE 未インストール → regex フォールバック
        except (ValueError, RuntimeError) as e:
            logger.debug("YAKE keyword extraction failed, falling back to regex: %s", e)

        # Fallback: regex ベース
        return SessionNotes._extract_keywords_regex(text, max_keywords)

    @staticmethod
    def _extract_keywords_regex(text: str, max_keywords: int = 8) -> list[str]:
        """regex ベースのキーワード抽出 (YAKE フォールバック)。"""
        tech_patterns = [
            r'[A-Z][a-z]+(?:[A-Z][a-z]+)+',         # CamelCase
            r'[A-Z]{2,}[_-]?[A-Z0-9]*',              # UPPER or UPPER_CASE
            r'[a-z]+[-_][a-z]+(?:[-_][a-z]+)*',       # kebab-case, snake_case
            r'/[a-z]{2,4}\+?',                        # WF names like /noe+
            r'\b(?:API|LLM|GPU|FEP|SSE|OAuth|MECE)\b', # 知られた略語
        ]

        keywords: dict[str, int] = {}
        for pattern in tech_patterns:
            for match in re.finditer(pattern, text):
                word = match.group().strip()
                if len(word) >= 2:
                    keywords[word] = keywords.get(word, 0) + 1

        # 日本語: カタカナ複合語 (3文字以上)
        for match in re.finditer(r'[\u30a0-\u30ff]{3,}', text):
            word = match.group()
            keywords[word] = keywords.get(word, 0) + 1

        sorted_kw = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        return [kw for kw, _ in sorted_kw[:max_keywords]]

    # PURPOSE: [L2-auto] _generate_summary の関数定義
    @staticmethod
    def _generate_summary(turns: list[dict], use_llm: bool = False) -> str:
        """セッションの要約を生成する。

        Phase 1 (Extractive, 常時): 最初の問い + ターン数 + 最後の結論
        Phase 2 (Abstractive, オプション): LLM で1行要約
        """
        # Phase 1: Extractive — 構造的要約
        first_user = ""
        last_model = ""
        user_count = 0
        model_count = 0

        for t in turns:
            role = t.get("role", "")
            content = t.get("content", "")
            if role == "user":
                user_count += 1
                if not first_user:
                    first_user = content[:120]
            elif role == "model":
                model_count += 1
                last_model = content[:120]

        # 構造的要約: 問い + ターン統計 + 結論
        parts = []
        if first_user:
            parts.append(f"問: {first_user}")
        parts.append(f"({user_count}問{model_count}答)")
        if last_model:
            parts.append(f"結: {last_model}")

        extractive = " → ".join(parts) if parts else ""

        if not use_llm:
            return extractive

        # Phase 2: Abstractive — LLM 1行要約
        try:
            try:
                from mekhane.ochema.account_router import get_account_for
                account = get_account_for("chat")
            except ImportError as _e:
                logger.debug("Ignored exception: %s", _e)
                account = "default"
            from mekhane.ochema.cortex_client import CortexClient
            client = CortexClient(model="gemini-3.1-flash", account=account)
            sample = "\n".join([f"{t.get('role', '')}: {t.get('content', '')[:100]}" for t in turns[-3:]])
            resp = client.ask(
                f"以下の会話を1行 (50文字以内) で要約してください:\n{sample}",
                max_tokens=100, temperature=0.0,
            )
            llm_summary = resp.text.strip()[:80]
            if llm_summary:
                return llm_summary
        except Exception as _e:  # Intentional Catch-All (Fallback to Extractive)  # noqa: BLE001
            logger.debug("Ignored exception (LLM summary fallback): %s", _e)

        return extractive

    # PURPOSE: [L2-auto] _write_session_summary の関数定義
    def _write_session_summary(self, filepath: Path, session_id: str,
                                meta: dict, chunk_files: list[Path],
                                turns: list[dict]) -> None:
        """セッション要約ファイルを生成する。

        各チャンクへのリンク + キーワード + ターン数 + 要約を含む。
        """
        summary = meta.get("summary", "")
        lines = [
            f"# Session Summary: {meta['title'][:60]}\n",
            f"- **Session ID**: `{session_id}`",
            f"- **Date**: {meta['date']}",
            f"- **Model**: {meta['model']}",
            f"- **Account**: {meta['account']}",
            f"- **Turns**: {len(turns)}",
            f"- **Chunks**: {len(chunk_files)}",
            f"- **Project**: {meta['project']}\n",
            "## 要約\n",
            f"{summary}\n",
            "## チャンク一覧\n",
        ]

        for f in chunk_files:
            lines.append(f"- [{f.stem}]({f})")

        filepath.write_text("\n".join(lines), encoding="utf-8")

    # PURPOSE: [L2-auto] _read_chunk_by_pk の関数定義
    def _read_chunk_by_pk(self, pk: str) -> str:
        """プライマリキーからチャンクの内容を読み込む。

        pk 形式: 'notes:{project}:{stem}'
        """
        parts = pk.split(":")
        if len(parts) < 3:
            return ""

        project = parts[1]
        stem = ":".join(parts[2:])  # stem に : が含まれる可能性

        filepath = self.notes_dir / project / f"{stem}.md"
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8")
            return self._strip_frontmatter(content)
        return ""

    # PURPOSE: [L2-auto] _synthesize_chunks の関数定義
    def _synthesize_chunks(self, content_a: str, content_b: str) -> str:
        """類似チャンクをLLMで統合し、新しい洞察を生成する。

        MemX 的「統合 → 新アイデア」の核心。
        """
        prompt = (
            "以下の2つのノートは類似した内容です。\n"
            "統合サマリーを作成し、両方のノートから導かれる"
            "「新しい洞察」を提案してください。\n\n"
            f"--- ノート A ---\n{content_a[:600]}\n\n"
            f"--- ノート B ---\n{content_b[:600]}\n\n"
            "回答形式:\n"
            "1. 統合サマリー (3-5行)\n"
            "2. 新しい洞察 (両方を統合して初めて見えるもの, 2-3行)\n"
            "3. 提案アクション (1行)"
        )

        try:
            try:
                from mekhane.ochema.account_router import get_account_for
                account = get_account_for("chat")
            except ImportError as _e:
                logger.debug("Ignored exception: %s", _e)
                account = "default"
            client = CortexClient(model=FLASH, account=account)
            response = client.ask(prompt, max_tokens=300, temperature=0.3)
            return response.text.strip()
        except (OSError, Exception) as e:  # Intentional Catch-All  # noqa: BLE001
            logger.warning("Synthesis failed: %s", e)
            return "統合失敗: LLM 接続不可"

    # --- パイプライン一括実行 ---

    # PURPOSE: [L2-auto] process の関数定義
    def process(self, session_id: str, session_store=None,
                skip_embed: bool = False) -> dict:
        """digest → embed → link のパイプラインを一括実行する。

        Args:
            session_id: 処理対象セッション ID
            session_store: SessionStore (optional)
            skip_embed: True で embed/link をスキップ (GPU なし環境)

        Returns:
            Dict with chunks_created, chunks_embedded, links_created
        """
        result = {"chunks_created": 0, "chunks_embedded": 0, "links_created": 0}

        # 1. Digest
        files = self.digest(session_id, session_store=session_store)
        result["chunks_created"] = len(files)

        if skip_embed or not files:
            return result

        # 2. Embed
        try:
            result["chunks_embedded"] = self.embed(session_id, session_store=session_store)
        except (OSError, ValueError, TypeError) as e:
            logger.warning("Embed failed for %s: %s", session_id[:8], e)

        # 3. Link
        try:
            result["links_created"] = self.link(session_id)
        except (OSError, ValueError, TypeError) as e:
            logger.warning("Link failed for %s: %s", session_id[:8], e)

        logger.info(
            "Processed session %s: %d chunks, %d embedded, %d links",
            session_id[:8], result["chunks_created"],
            result["chunks_embedded"], result["links_created"]
        )
        return result
