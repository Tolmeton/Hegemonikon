# PROOF: [L2/インフラ] <- mekhane/anamnesis/session_indexer.py A0→記憶永続化→セッション履歴のインデックス化
# PURPOSE: セッション履歴を GnosisIndex にインデックスする
"""
PROOF: [L2/インフラ] <- mekhane/anamnesis/

P3 → 記憶の永続化が必要
   → セッション履歴のセマンティック検索が必要
   → session_indexer.py が担う

Q.E.D.

---

Session Indexer — セッション履歴ベクトル検索

agq-sessions.sh --dump で取得した JSON を Paper モデルに変換し、
GnosisIndex に source="session" として投入する。

Usage:
    python mekhane/anamnesis/session_indexer.py <json_path>
    python mekhane/anamnesis/session_indexer.py --from-api
"""

import json
import re
import sys
import subprocess
import tempfile
from datetime import datetime

import yaml
from pathlib import Path
from typing import Optional

try:
    from mekhane.paths import HANDOFF_DIR, MNEME_RECORDS
except ImportError:
    HANDOFF_DIR = HANDOFF_DIR

# Ensure hegemonikon root is in path
_HEGEMONIKON_ROOT = Path(__file__).parent.parent.parent
if str(_HEGEMONIKON_ROOT) not in sys.path:
    sys.path.insert(0, str(_HEGEMONIKON_ROOT))

import os
from mekhane.symploke.handoff_files import list_handoff_files


# PURPOSE: チャンカーインスタンスを取得する (CHUNKER_MODE 環境変数で切替)
def _get_chunker(embed_fn=None):
    """チャンカーインスタンスを返す。

    環境変数 CHUNKER_MODE:
      - 'nucleator': NucleatorChunker (Embedder の embed_batch を自動注入)
      - 'markdown' (デフォルト): MarkdownChunker

    embed_fn 引数が明示指定されればそれを使用。
    未指定時は Embedder (Vertex AI singleton) から自動取得を試みる。
    Embedder 初期化失敗時は embed_fn=None のまま (NucleatorChunker 内部で
    MarkdownChunker にフォールバックする)。
    """
    mode = os.environ.get("CHUNKER_MODE", "markdown").lower()
    if mode == "nucleator":
        from mekhane.anamnesis.chunker import NucleatorChunker
        # embed_fn 未指定時は Embedder から自動注入
        if embed_fn is None:
            try:
                from mekhane.anamnesis.index import Embedder
                embedder = Embedder()
                embed_fn = embedder.embed_batch
            except Exception:  # noqa: BLE001
                pass  # Embedder 初期化失敗 → embed_fn=None → フォールバック
        # τ 決定: CHUNKER_TAU=auto でエントロピーベース動的決定
        tau_spec = os.environ.get("CHUNKER_TAU", "0.70")
        tau: float | str = "auto" if tau_spec == "auto" else float(tau_spec)
        return NucleatorChunker(embed_fn=embed_fn, tau=tau)
    else:
        from mekhane.anamnesis.chunker import MarkdownChunker
        return MarkdownChunker()


# PURPOSE: LS API の trajectorySummaries JSON からセッション情報を構造化 dict に抽出する
def parse_sessions_from_json(data: dict) -> list[dict]:
    """PURPOSE: LS API の trajectorySummaries JSON からセッション情報を構造化 dict に抽出する"""
    summaries = data.get("trajectorySummaries", {})
    sessions = []

    for conv_id, info in summaries.items():
        if not isinstance(info, dict):
            continue

        title = info.get("summary", "").strip()
        if not title:
            title = f"Session {conv_id[:8]}"

        # Workspace extraction
        workspaces = []
        for ws in info.get("workspaces", []):
            if isinstance(ws, dict):
                path = ws.get("workspacePath", "")
                if path:
                    workspaces.append(Path(path).name)

        sessions.append({
            "conversation_id": conv_id,
            "title": title,
            "step_count": info.get("stepCount", 0),
            "status": info.get("status", "unknown"),
            "created": info.get("createdTime", ""),
            "modified": info.get("lastModifiedTime", ""),
            "workspaces": workspaces,
        })

    return sessions


# PURPOSE: セッション情報を GnosisIndex レコード (既存スキーマ準拠) に変換する
def sessions_to_records(sessions: list[dict]) -> list[dict]:
    """PURPOSE: セッション情報を GnosisIndex レコード (既存スキーマ準拠) に変換する

    既存テーブルスキーマ:
      primary_key, title, source, abstract, content,
      authors, doi, arxiv_id, url, citations, vector

    P3 フィールド拡充 (v2):
      content  → 構造化メタデータ (timestamps, status, duration)
      authors  → ワークスペース名 (プロジェクト文脈)
      url      → セッション conversation_id (逆引き用)
    """
    records = []

    for s in sessions:
        conv_id = s["conversation_id"]
        title = s["title"]
        workspaces = s.get("workspaces", [])
        step_count = s.get("step_count", 0)
        status = s.get("status", "unknown")
        created = s.get("created", "")
        modified = s.get("modified", "")

        # Duration calculation (if timestamps available)
        duration_str = ""
        if created and modified:
            try:
                from datetime import datetime as _dt
                # Parse ISO 8601 timestamps
                t_created = _dt.fromisoformat(created.replace("Z", "+00:00"))
                t_modified = _dt.fromisoformat(modified.replace("Z", "+00:00"))
                delta = t_modified - t_created
                hours, remainder = divmod(int(delta.total_seconds()), 3600)
                minutes = remainder // 60
                duration_str = f"{hours}h{minutes:02d}m"
            except (ValueError, TypeError):
                pass

        # Build abstract: rich context for embedding quality
        abstract_parts = [
            f"Session: {title}",
            f"Steps: {step_count}",
            f"Status: {status}",
        ]
        if workspaces:
            abstract_parts.append(f"Workspaces: {', '.join(workspaces)}")
        if duration_str:
            abstract_parts.append(f"Duration: {duration_str}")

        abstract = ". ".join(abstract_parts)

        # P3: content — 構造化メタデータ (検索対象 + 情報保持)
        content_parts = []
        if created:
            content_parts.append(f"Created: {created}")
        if modified:
            content_parts.append(f"Modified: {modified}")
        if duration_str:
            content_parts.append(f"Duration: {duration_str}")
        content_parts.append(f"Status: {status}")
        content_parts.append(f"Steps: {step_count}")
        if workspaces:
            content_parts.append(f"Workspaces: {', '.join(workspaces)}")
        content = " | ".join(content_parts)

        # P3: authors — ワークスペース名 (プロジェクト文脈として活用)
        authors = ", ".join(workspaces) if workspaces else ""

        # P3: url — conversation_id (逆引き・リンク用)
        url = f"session://{conv_id}"

        record = {
            "primary_key": f"session:{conv_id}",
            "title": title,
            "source": "session",
            "abstract": abstract,
            "content": content,
            "authors": authors,
            "doi": "",
            "arxiv_id": "",
            "url": url,
            "citations": step_count,
            # vector will be added by indexer
        }
        records.append(record)

    return records


# ==============================================================
# Handoff Indexer — handoff_*.md を source="handoff" でインデックス
# ==============================================================

_HANDOFF_DIR = HANDOFF_DIR

# Regex patterns for Handoff parsing
_RE_TITLE = re.compile(r"^#\s+(?:🔄\s*)?(?:Handoff:\s*)?(.+)$", re.MULTILINE)
_RE_DATE = re.compile(
    r"\*\*日時\*\*:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", re.MULTILINE
)
_RE_SESSION_ID = re.compile(
    r"\*Session:\s*([0-9a-f-]{36})\*", re.MULTILINE
)
_RE_SECTION = re.compile(r"^##\s+(.+)$", re.MULTILINE)


# PURPOSE: Handoff マークダウンファイルをパースし構造化 dict に変換する
def parse_handoff_md(path: Path) -> dict:
    """PURPOSE: Handoff マークダウンファイルをパースし構造化 dict に変換する"""
    text = path.read_text(encoding="utf-8", errors="replace")

    # Title: first H1 line
    title_match = _RE_TITLE.search(text)
    title = title_match.group(1).strip() if title_match else path.stem

    # Date from metadata blockquote
    date_match = _RE_DATE.search(text)
    date_str = date_match.group(1).strip() if date_match else ""

    # Fallback: extract date from filename  handoff_YYYY-MM-DD_HHMM.md
    if not date_str:
        fname_match = re.search(r"(\d{4}-\d{2}-\d{2})_(\d{2})(\d{2})", path.stem)
        if fname_match:
            date_str = f"{fname_match.group(1)} {fname_match.group(2)}:{fname_match.group(3)}"

    # Session ID (if present at bottom)
    session_match = _RE_SESSION_ID.search(text)
    session_id = session_match.group(1) if session_match else ""

    # Section headers for content summary
    sections = _RE_SECTION.findall(text)
    # Clean emoji prefixes
    sections = [re.sub(r"^[^\w]+", "", s).strip() for s in sections]

    return {
        "title": title,
        "date": date_str,
        "session_id": session_id,
        "sections": sections,
        "text": text,
        "filename": path.name,
    }


# PURPOSE: パース済み Handoff dict を GnosisIndex 互換レコードに変換する (チャンキング対応)
def handoffs_to_records(handoffs: list[dict]) -> list[dict]:
    """PURPOSE: パース済み Handoff dict を GnosisIndex 互換レコードに変換する"""
    chunker = _get_chunker()
    
    records = []
    for h in handoffs:
        base_abstract_parts = [h["title"]]
        if h["date"]:
            base_abstract_parts.append(f"({h['date']})")
        base_abstract = " ".join(base_abstract_parts)

        # File-level identifier
        primary_key_base = f"handoff:{h['filename']}"
        url_base = f"session://{h['session_id']}" if h["session_id"] else ""

        # Chunking
        chunks = chunker.chunk(h["text"], source_id=primary_key_base, title=h["title"])
        
        # If no chunks were generated (empty file), skip
        if not chunks:
            continue

        for chunk in chunks:
            # Build chunk-specific abstract
            abstract_parts = [base_abstract]
            if chunk.get("section_title"):
                abstract_parts.append(f"— Section: {chunk['section_title']}")
            abstract = " ".join(abstract_parts)

            record = {
                "primary_key": chunk["id"],
                "title": f"[Handoff] {h['title']}" + (f" ({chunk['section_title']})" if chunk.get("section_title") else ""),
                "source": "handoff",
                "abstract": abstract,
                "content": chunk["text"],
                "authors": "",
                "doi": "",
                "arxiv_id": "",
                "url": url_base,
                "citations": 0,
            }
            records.append(record)

    return records


# PURPOSE: handoff_*.md ファイル群を GnosisIndex にセマンティックインデックスする
def index_handoffs(handoff_dir: Optional[str] = None) -> int:
    """PURPOSE: handoff_*.md ファイル群を GnosisIndex にセマンティックインデックスする"""
    directory = Path(handoff_dir) if handoff_dir else _HANDOFF_DIR

    if not directory.exists():
        print(f"[Error] Handoff directory not found: {directory}")
        return 1

    md_files = list_handoff_files(directory)
    if not md_files:
        print("[Error] No handoff_*.md or handoff_*.typos files found")
        return 1

    print(f"[HandoffIndexer] Found {len(md_files)} handoff files")

    # Parse all
    handoffs = [parse_handoff_md(f) for f in md_files]
    records = handoffs_to_records(handoffs)

    # Embed and add to index
    from mekhane.anamnesis.index import GnosisIndex

    index = GnosisIndex()
    embedder = index._get_embedder()

    # Dedupe against existing records
    existing_keys = index.list_primary_keys()
    if existing_keys:
        before = len(records)
        records = [r for r in records if r["primary_key"] not in existing_keys]
        skipped = before - len(records)
        if skipped:
            print(f"[HandoffIndexer] Skipped {skipped} duplicates")

    if not records:
        print("[HandoffIndexer] No new handoffs to add (all duplicates)")
        return 0

    # Generate embeddings (title + abstract for embedding text)
    texts = [f"{r['title']} {r['abstract']}" for r in records]
    vectors = embedder.embed_batch(texts)

    # Attach vectors
    data_with_vectors = []
    for rec, vec in zip(records, vectors):
        rec["vector"] = vec
        data_with_vectors.append(rec)

    # Add to index (schema filtering は add_records 内部で自動適用)
    index.add_records(data_with_vectors)

    print(f"[HandoffIndexer] ✅ Indexed {len(data_with_vectors)} handoffs")
    return 0


# PURPOSE: LS API 経由のセッション取得 (LS 削除により利用不可)
def fetch_all_conversations(max_sessions: int = 100) -> list[dict]:
    """PURPOSE: LS API 経由のセッション取得 (LS 削除により利用不可)"""
    raise RuntimeError(
        "fetch_all_conversations は LS 削除により利用不可です。"
        "Handoff ファイルベースのインデックス (index_handoffs) を使用してください。"
    )


# PURPOSE: 会話データを GnosisIndex セマンティック検索用レコードに変換する (チャンキング対応)
def conversations_to_records(conversations: list[dict]) -> list[dict]:
    """PURPOSE: 会話データを GnosisIndex セマンティック検索用レコードに変換する"""
    chunker = _get_chunker()
    
    records = []

    for conv in conversations:
        cascade_id = conv["cascade_id"]
        title = conv["title"]
        full_text = conv.get("full_text", "")

        # Base abstract: タイトル + ターン数 + 最初のユーザー入力の先頭200文字
        user_preview = conv.get("user_text", "")[:200]
        base_abstract = f"{title} ({conv.get('total_turns', 0)} turns) — {user_preview}"

        # 日付のパース
        created = conv.get("created", "")
        year = ""
        if created:
            try:
                # ISO format or timestamp
                if "T" in created:
                    from datetime import datetime
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    year = str(dt.year)
            except Exception:  # noqa: BLE001
                pass
                
        primary_key_base = f"conv:{cascade_id}"
        url_base = f"conversation://{cascade_id}"
        
        # Chunking
        chunks = chunker.chunk(full_text, source_id=primary_key_base, title=title)
        
        if not chunks:
            # Fallback for empty/short texts
            records.append({
                "primary_key": primary_key_base,
                "source": "conversation",
                "title": title,
                "abstract": base_abstract[:500],
                "content": base_abstract,
                "authors": "IDE Session",
                "year": year,
                "url": url_base,
                "citations": conv.get("step_count", 0),
            })
            continue
            
        for chunk in chunks:
            # Build chunk-specific abstract
            abstract_parts = [base_abstract]
            if chunk.get("section_title"):
                abstract_parts.append(f"— Section: {chunk['section_title']}")
            abstract = " ".join(abstract_parts)
            
            records.append({
                "primary_key": chunk["id"],
                "source": "conversation",
                "title": f"{title}" + (f" ({chunk['section_title']})" if chunk.get("section_title") else ""),
                "abstract": abstract[:500],
                "content": chunk["text"],
                "authors": "IDE Session",
                "year": year,
                "url": url_base,
                "citations": conv.get("step_count", 0),
            })

    return records


# PURPOSE: 全セッション会話を取得し GnosisIndex にセマンティックインデックスする
def index_conversations(max_sessions: int = 100) -> int:
    """PURPOSE: 全セッション会話を取得し GnosisIndex にセマンティックインデックスする"""
    conversations = fetch_all_conversations(max_sessions)
    if not conversations:
        print("[ConvIndexer] No conversations to index")
        return 1

    records = conversations_to_records(conversations)

    from mekhane.anamnesis.index import GnosisIndex

    index = GnosisIndex()
    embedder = index._get_embedder()

    # Dedupe against existing records
    existing_keys = index.list_primary_keys()
    if existing_keys:
        before = len(records)
        records = [r for r in records if r["primary_key"] not in existing_keys]
        skipped = before - len(records)
        if skipped:
            print(f"[ConvIndexer] Skipped {skipped} duplicates")

    if not records:
        print("[ConvIndexer] No new conversations to add (all duplicates)")
        return 0

    # Generate embeddings in batches
    BATCH_SIZE = 16
    data_with_vectors = []

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        texts = [f"{r['title']} {r['abstract']}" for r in batch]
        vectors = embedder.embed_batch(texts)

        for record, vector in zip(batch, vectors):
            record["vector"] = vector
            data_with_vectors.append(record)

        print(f"  Embedded {min(i + BATCH_SIZE, len(records))}/{len(records)}...")

    # Add to index (schema filtering は add_records 内部で自動適用)
    index.add_records(data_with_vectors)

    print(f"[ConvIndexer] ✅ Indexed {len(data_with_vectors)} conversations")
    return 0


# ==============================================================
# Steps Indexer — .system_generated/steps/*/output.txt をインデックス
# ==============================================================

_BRAIN_DIR = Path.home() / ".gemini" / "antigravity" / "brain"


# PURPOSE: .system_generated/steps/ 配下の output.txt をパースしレコード化する
def parse_step_outputs(brain_dir: Optional[str] = None, max_per_session: int = 20) -> list[dict]:
    """PURPOSE: .system_generated/steps/ 配下の output.txt をパースしレコード化する"""
    directory = Path(brain_dir) if brain_dir else _BRAIN_DIR
    if not directory.exists():
        return []

    steps = []
    # Each conversation has its own brain dir
    for conv_dir in directory.iterdir():
        if not conv_dir.is_dir():
            continue
        conv_id = conv_dir.name
        steps_dir = conv_dir / ".system_generated" / "steps"
        if not steps_dir.exists():
            continue

        # Find output.txt files, sorted by step number descending (newer first)
        output_files = sorted(
            steps_dir.glob("*/output.txt"),
            key=lambda p: int(p.parent.name) if p.parent.name.isdigit() else 0,
            reverse=True,
        )

        for i, out_file in enumerate(output_files[:max_per_session]):
            step_num = out_file.parent.name
            try:
                text = out_file.read_text(encoding="utf-8", errors="replace")[:4000]
            except Exception:  # noqa: BLE001
                continue

            if not text.strip():
                continue

            steps.append({
                "conversation_id": conv_id,
                "step_number": step_num,
                "content": text,
                "size": out_file.stat().st_size,
            })

    return steps


# PURPOSE: ステップ出力データを GnosisIndex 互換レコードに変換する
def steps_to_records(steps: list[dict]) -> list[dict]:
    """PURPOSE: ステップ出力データを GnosisIndex 互換レコードに変換する"""
    records = []
    for s in steps:
        conv_id = s["conversation_id"]
        step_num = s["step_number"]
        content = s["content"]

        # First line as title (often contains tool name or command)
        first_line = content.split("\n", 1)[0][:120].strip()
        title = f"[Step {step_num}] {first_line}" if first_line else f"Step {step_num}"

        abstract = f"Step {step_num} in session {conv_id[:8]}. Size: {s['size']} bytes. {first_line}"

        records.append({
            "primary_key": f"step:{conv_id}:{step_num}",
            "title": title,
            "source": "step",
            "abstract": abstract[:500],
            "content": content,
            "authors": "IDE Step Output",
            "doi": "",
            "arxiv_id": "",
            "url": f"session://{conv_id}#step-{step_num}",
            "citations": 0,
        })

    return records


# PURPOSE: .system_generated/steps/ の出力ファイルを GnosisIndex にインデックスする
def index_steps(brain_dir: Optional[str] = None, max_per_session: int = 20) -> int:
    """PURPOSE: .system_generated/steps/ の出力ファイルを GnosisIndex にインデックスする"""
    steps = parse_step_outputs(brain_dir, max_per_session)
    if not steps:
        print("[StepsIndexer] No step outputs found")
        return 1

    print(f"[StepsIndexer] Found {len(steps)} step outputs")

    records = steps_to_records(steps)

    from mekhane.anamnesis.index import GnosisIndex

    index = GnosisIndex()
    embedder = index._get_embedder()

    # Dedupe against existing records
    existing_keys = index.list_primary_keys()
    if existing_keys:
        before = len(records)
        records = [r for r in records if r["primary_key"] not in existing_keys]
        skipped = before - len(records)
        if skipped:
            print(f"[StepsIndexer] Skipped {skipped} duplicates")

    if not records:
        print("[StepsIndexer] No new steps to add (all duplicates)")
        return 0

    # Embed in batches
    BATCH_SIZE = 16
    data_with_vectors = []

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        texts = [f"{r['title']} {r['abstract']}" for r in batch]
        vectors = embedder.embed_batch(texts)

        for record, vector in zip(batch, vectors):
            record["vector"] = vector
            data_with_vectors.append(record)

        print(f"  Embedded {min(i + BATCH_SIZE, len(records))}/{len(records)}...")

    # Add to index (schema filtering は add_records 内部で自動適用)
    index.add_records(data_with_vectors)

    print(f"[StepsIndexer] ✅ Indexed {len(data_with_vectors)} steps")
    return 0


# ==============================================================
# Export MD Indexer — export_chats.py 出力の MD をインデックス
# ==============================================================

_EXPORT_DIR = HANDOFF_DIR
_RE_EXPORT_ID = re.compile(r"\*\*ID\*\*:\s*`([^`]+)`")
_RE_EXPORT_DATE = re.compile(r"\*\*エクスポート日時\*\*:\s*(.+)")
_RE_ROLE = re.compile(r"^##\s+(👤 User|🤖 Claude)", re.MULTILINE)


# PURPOSE: export_chats.py 出力の MD ファイルを構造化 dict にパースする
def parse_export_md(path: Path) -> dict:
    """PURPOSE: export_chats.py 出力の MD ファイルを構造化 dict にパースする"""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")

    # Title: first H1
    title = path.stem
    for line in lines[:5]:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # ID
    id_match = _RE_EXPORT_ID.search(text)
    conv_id = id_match.group(1) if id_match else ""

    # Export date
    date_match = _RE_EXPORT_DATE.search(text)
    exported_at = date_match.group(1).strip() if date_match else ""

    # Extract body (after first ---)
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip() == "---":
            body_start = i + 1
            break

    # Count messages by role markers
    user_count = len(re.findall(r"^## 👤 User", text, re.MULTILINE))
    assistant_count = len(re.findall(r"^## 🤖 Claude", text, re.MULTILINE))

    body = "\n".join(lines[body_start:])
    # Clean noise
    body = re.sub(r"Thought for \d+s\s*", "", body)
    body = re.sub(r"Thought for <\d+s\s*", "", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    return {
        "title": title,
        "conv_id": conv_id,
        "exported_at": exported_at,
        "user_count": user_count,
        "assistant_count": assistant_count,
        "content": body,  # Changed from body[:4000] for chunker
        "filename": path.name,
    }


# PURPOSE: パース済みエクスポート dict を GnosisIndex 互換レコードに変換する (チャンキング対応)
def exports_to_records(exports: list[dict]) -> list[dict]:
    """PURPOSE: パース済みエクスポート dict を GnosisIndex 互換レコードに変換する"""
    chunker = _get_chunker()
    
    records = []
    for e in exports:
        base_abstract = f"{e['title']} ({e['user_count']} user, {e['assistant_count']} assistant messages)"
        if e["exported_at"]:
            base_abstract += f" — exported {e['exported_at'][:10]}"

        primary_key_base = f"export:{e['filename']}"
        url_base = f"session://{e['conv_id']}" if e["conv_id"] else ""

        # Chunking
        chunks = chunker.chunk(e["content"], source_id=primary_key_base, title=e["title"])
        
        if not chunks:
            # Fallback
            records.append({
                "primary_key": primary_key_base,
                "title": e["title"],
                "source": "export",
                "abstract": base_abstract[:500],
                "content": base_abstract,
                "authors": "IDE Export",
                "doi": "",
                "arxiv_id": "",
                "url": url_base,
                "citations": e["user_count"] + e["assistant_count"],
            })
            continue

        for chunk in chunks:
            # Build chunk-specific abstract
            abstract_parts = [base_abstract]
            if chunk.get("section_title"):
                abstract_parts.append(f"— Section: {chunk['section_title']}")
            abstract = " ".join(abstract_parts)
            
            records.append({
                "primary_key": chunk["id"],
                "title": f"{e['title']}" + (f" ({chunk['section_title']})" if chunk.get("section_title") else ""),
                "source": "export",
                "abstract": abstract[:500],
                "content": chunk["text"],
                "authors": "IDE Export",
                "doi": "",
                "arxiv_id": "",
                "url": url_base,
                "citations": e["user_count"] + e["assistant_count"],
            })
            
    return records


# PURPOSE: export_chats.py 出力 MD を GnosisIndex にセマンティックインデックスする
def index_exports(export_dir: Optional[str] = None) -> int:
    """PURPOSE: export_chats.py 出力 MD を GnosisIndex にセマンティックインデックスする"""
    directory = Path(export_dir) if export_dir else _EXPORT_DIR
    if not directory.exists():
        print(f"[ExportIndexer] Directory not found: {directory}")
        return 1

    # export_chats.py output: YYYY-MM-DD_conv_N_Title.md
    md_files = sorted(directory.glob("*_conv_*.md"))
    if not md_files:
        print("[ExportIndexer] No export MD files found")
        return 1

    print(f"[ExportIndexer] Found {len(md_files)} export files")

    exports = [parse_export_md(f) for f in md_files]
    records = exports_to_records(exports)

    from mekhane.anamnesis.index import GnosisIndex
    index = GnosisIndex()
    embedder = index._get_embedder()

    # Dedupe against existing records
    existing_keys = index.list_primary_keys()
    if existing_keys:
        before = len(records)
        records = [r for r in records if r["primary_key"] not in existing_keys]
        skipped = before - len(records)
        if skipped:
            print(f"[ExportIndexer] Skipped {skipped} duplicates")

    if not records:
        print("[ExportIndexer] No new exports to add (all duplicates)")
        return 0

    # Embed
    BATCH_SIZE = 16
    data_with_vectors = []
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        texts = [f"{r['title']} {r['abstract']}" for r in batch]
        vectors = embedder.embed_batch(texts)
        for record, vector in zip(batch, vectors):
            record["vector"] = vector
            data_with_vectors.append(record)
        print(f"  Embedded {min(i + BATCH_SIZE, len(records))}/{len(records)}...")

    # Add to index (schema filtering は add_records 内部で自動適用)
    index.add_records(data_with_vectors)

    print(f"[ExportIndexer] ✅ Indexed {len(data_with_vectors)} exports")
    return 0


# ==============================================================
# ROM Indexer — /rom WF で蒸留されたコンテキストをインデックス
# ==============================================================

_ROM_DIR = MNEME_RECORDS / "c_ROM｜rom"

# Regex patterns for ROM parsing
_RE_ROM_TITLE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_RE_ROM_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
_RE_ROM_SEMANTIC_TAG = re.compile(
    r">\s*\*\*\[(DEF|FACT|RULE|CONFLICT|OPINION)\]\*\*", re.MULTILINE
)

# Regex patterns for Typos v8.4 ROM parsing
_RE_TYPOS_PROMPT = re.compile(r"^#prompt\s+(.+)$", re.MULTILINE)
_RE_TYPOS_DEPTH = re.compile(r"^#depth:\s+(.+)$", re.MULTILINE)
_RE_TYPOS_BLOCK = re.compile(
    r"<:(\w[\w\s]*?)(?:\s+([\w_]+))?:\s*\n(.*?)\n\s*/?\w*:>",
    re.DOTALL,
)
_RE_TYPOS_INLINE = re.compile(r"<:(\w+):\s*(.+?)\s*:>")
_RE_TYPOS_HIGHLIGHT = re.compile(
    r"<:highlight:\s*\[(DECISION|DISCOVERY|CONTEXT|FACT|RULE|CONFLICT|OPINION)\]",
    re.MULTILINE,
)
_RE_TYPOS_SEARCH_INDEX = re.compile(
    r"<:data\s+search_index:\s*\n(.*?)\n\s*/data:>",
    re.DOTALL,
)


# PURPOSE: ROM マークダウンファイルをパースし構造化 dict に変換する
def parse_rom_md(path: Path) -> dict:
    """PURPOSE: ROM マークダウンファイルをパースし構造化 dict に変換する"""
    text = path.read_text(encoding="utf-8", errors="replace")

    # Title: first H1 line
    title_match = _RE_ROM_TITLE.search(text)
    title = title_match.group(1).strip() if title_match else path.stem

    # Try to extract YAML frontmatter
    topics = []
    exec_summary = ""
    reliability = ""
    source_date = ""
    fm_match = _RE_ROM_FRONTMATTER.match(text)
    if fm_match:
        try:
            import yaml
            fm = yaml.safe_load(fm_match.group(1))
            if isinstance(fm, dict):
                topics = fm.get("topics", [])
                exec_summary = fm.get("exec_summary", "")
                reliability = fm.get("reliability", "")
                source_date = fm.get("source_date", "")
        except Exception:  # noqa: BLE001
            pass  # Intentional: frontmatter may be malformed

    # Date from filename: rom_YYYY-MM-DD_HHMM_slug.md
    date_str = ""
    fname_match = re.search(r"(\d{4}-\d{2}-\d{2})_(\d{2})(\d{2})", path.stem)
    if fname_match:
        date_str = f"{fname_match.group(1)} {fname_match.group(2)}:{fname_match.group(3)}"
    elif source_date and source_date != "Unknown":
        date_str = source_date

    # Derivative level from filename
    derivative = "standard"
    if "_snapshot_" in path.stem or path.stem.endswith("_snapshot"):
        derivative = "rom-"
    elif "_rag_" in path.stem or path.stem.endswith("_rag"):
        derivative = "rom+"

    # Semantic tags count
    semantic_tags = _RE_ROM_SEMANTIC_TAG.findall(text)

    # Section headers for content summary
    sections = _RE_SECTION.findall(text)
    sections = [re.sub(r"^[^\w]+", "", s).strip() for s in sections]

    return {
        "title": title,
        "date": date_str,
        "derivative": derivative,
        "topics": topics,
        "exec_summary": exec_summary,
        "reliability": reliability,
        "semantic_tags": semantic_tags,
        "sections": sections,
        "text": text,
        "filename": path.name,
    }


# PURPOSE: Typos v8.4 形式の ROM ファイルをパースし構造化 dict に変換する
def parse_rom_typos(path: Path) -> dict:
    """PURPOSE: Typos v8.4 形式の ROM ファイルをパースし構造化 dict に変換する"""
    text = path.read_text(encoding="utf-8", errors="replace")

    # Title from #prompt header
    prompt_match = _RE_TYPOS_PROMPT.search(text)
    title = prompt_match.group(1).strip() if prompt_match else path.stem

    # Depth → derivative mapping
    derivative = "standard"
    depth_match = _RE_TYPOS_DEPTH.search(text)
    if depth_match:
        depth = depth_match.group(1).strip()
        if depth == "L1":
            derivative = "rom-"
        elif depth == "L3":
            derivative = "rom+"

    # Extract search_index for topics/keywords
    topics = []
    si_match = _RE_TYPOS_SEARCH_INDEX.search(text)
    if si_match:
        si_text = si_match.group(1)
        for line in si_text.splitlines():
            line = line.strip()
            if line.startswith("keywords:"):
                keywords_str = line[len("keywords:"):].strip()
                topics = [k.strip() for k in keywords_str.split(",") if k.strip()]

    # Extract schema rom_meta for reliability, created_at, expiry
    reliability = ""
    source_date = ""
    schema_match = re.search(
        r"<:schema\s+rom_meta:\s*\n(.*?)\n\s*/schema:>", text, re.DOTALL
    )
    if schema_match:
        for line in schema_match.group(1).splitlines():
            line = line.strip()
            if line.startswith("reliability:"):
                reliability = line[len("reliability:"):].strip()
            elif line.startswith("created_at:"):
                source_date = line[len("created_at:"):].strip()

    # Extract summary
    exec_summary = ""
    summary_match = re.search(
        r"<:summary:\s*\n(.*?)\n\s*/summary:>", text, re.DOTALL
    )
    if summary_match:
        exec_summary = summary_match.group(1).strip()

    # Date from filename: rom_YYYY-MM-DD_slug.typos
    date_str = ""
    fname_match = re.search(r"(\d{4}-\d{2}-\d{2})", path.stem)
    if fname_match:
        date_str = fname_match.group(1)
    if source_date and not date_str:
        date_str = source_date

    # Semantic tags from <:highlight: [TAG]> blocks
    semantic_tags = _RE_TYPOS_HIGHLIGHT.findall(text)

    # Section headers — content blocks with names
    sections = []
    for m in _RE_TYPOS_BLOCK.finditer(text):
        directive = m.group(1).strip()
        qualifier = m.group(2) or ""
        if directive == "content" and qualifier:
            sections.append(qualifier)

    return {
        "title": title,
        "date": date_str,
        "derivative": derivative,
        "topics": topics[:15],
        "exec_summary": exec_summary,
        "reliability": reliability,
        "semantic_tags": semantic_tags,
        "sections": sections,
        "text": text,
        "filename": path.name,
    }


# PURPOSE: パース済み ROM dict を GnosisIndex 互換レコードに変換する (チャンキング対応)
def roms_to_records(roms: list[dict]) -> list[dict]:
    """PURPOSE: パース済み ROM dict を GnosisIndex 互換レコードに変換する"""
    chunker = _get_chunker()
    
    records = []
    for r in roms:
        base_abstract_parts = [f"[ROM/{r['derivative']}] {r['title']}"]
        if r["date"]:
            base_abstract_parts.append(f"({r['date']})")
        if r["exec_summary"]:
            base_abstract_parts.append(f"— {r['exec_summary'][:200]}")
        elif r["sections"]:
            base_abstract_parts.append("— " + ", ".join(r["sections"][:6]))
        if r["topics"]:
            base_abstract_parts.append(f"Topics: {', '.join(r['topics'][:5])}")
        base_abstract = " ".join(base_abstract_parts)

        primary_key_base = f"rom:{r['filename']}"
        url_base = str(_ROM_DIR / r["filename"])

        # Chunking
        chunks = chunker.chunk(r["text"], source_id=primary_key_base, title=r["title"])
        
        if not chunks:
            # Fallback
            records.append({
                "primary_key": primary_key_base,
                "title": f"[ROM] {r['title']}",
                "source": "rom",
                "abstract": base_abstract[:500],
                "content": base_abstract,
                "authors": f"derivative:{r['derivative']}",
                "doi": "",
                "arxiv_id": "",
                "url": url_base,
                "citations": len(r.get("semantic_tags", [])),
            })
            continue

        for chunk in chunks:
            # Build chunk-specific abstract
            abstract_parts = [base_abstract]
            if chunk.get("section_title"):
                abstract_parts.append(f"— Section: {chunk['section_title']}")
            abstract = " ".join(abstract_parts)
            
            records.append({
                "primary_key": chunk["id"],
                "title": f"[ROM] {r['title']}" + (f" ({chunk['section_title']})" if chunk.get("section_title") else ""),
                "source": "rom",
                "abstract": abstract[:500],
                "content": chunk["text"],
                "authors": f"derivative:{r['derivative']}",
                "doi": "",
                "arxiv_id": "",
                "url": url_base,
                "citations": len(r.get("semantic_tags", [])),
            })

    return records


# PURPOSE: ROM ファイル群を GnosisIndex にセマンティックインデックスする
def index_roms(rom_dir: Optional[str] = None) -> int:
    """PURPOSE: ROM ファイル群を GnosisIndex にセマンティックインデックスする"""
    directory = Path(rom_dir) if rom_dir else _ROM_DIR

    if not directory.exists():
        print(f"[ROMIndexer] ROM directory not found: {directory}")
        print("[ROMIndexer] Run /rom to generate ROM files first")
        return 1

    md_files = sorted(directory.glob("rom_*.md"))
    typos_files = sorted(directory.glob("rom_*.typos"))
    # Also pick up non-rom_* files (e.g. exe_coordinate_limit_evidence.typos)
    other_typos = sorted(
        f for f in directory.glob("*.typos")
        if not f.name.startswith("rom_")
    )
    all_files = md_files + typos_files + other_typos
    if not all_files:
        print("[ROMIndexer] No rom_*.md or *.typos files found")
        return 1

    print(f"[ROMIndexer] Found {len(all_files)} ROM files ({len(md_files)} .md, {len(typos_files) + len(other_typos)} .typos)")

    # Parse all — dispatch by extension
    roms = []
    for f in all_files:
        if f.suffix == ".typos":
            roms.append(parse_rom_typos(f))
        else:
            roms.append(parse_rom_md(f))
    records = roms_to_records(roms)

    # Embed and add to index
    from mekhane.anamnesis.index import GnosisIndex

    index = GnosisIndex()
    embedder = index._get_embedder()

    # Dedupe against existing records
    existing_keys = index.list_primary_keys()
    if existing_keys:
        before = len(records)
        records = [r for r in records if r["primary_key"] not in existing_keys]
        skipped = before - len(records)
        if skipped:
            print(f"[ROMIndexer] Skipped {skipped} duplicates")

    if not records:
        print("[ROMIndexer] No new ROMs to add (all duplicates)")
        return 0

    # Generate embeddings (title + abstract for embedding text)
    texts = [f"{r['title']} {r['abstract']}" for r in records]
    vectors = embedder.embed_batch(texts)

    # Attach vectors
    data_with_vectors = []
    for rec, vec in zip(records, vectors):
        rec["vector"] = vec
        data_with_vectors.append(rec)

    # Add to index (schema filtering は add_records 内部で自動適用)
    index.add_records(data_with_vectors)

    print(f"[ROMIndexer] ✅ Indexed {len(data_with_vectors)} ROMs")
    return 0


# ==============================================================
# Artifact Indexer — brain のアーティファクト (task/walkthrough/plan) をインデックス
# ==============================================================

_BRAIN_ARCHIVE_DIR = Path.home() / ".gemini" / "antigravity" / "brain_archive"
_ARTIFACT_NAMES = {"task.md", "walkthrough.md", "implementation_plan.md"}
_MNEME_ARTIFACT_DIR = MNEME_RECORDS / "d_成果物｜artifacts"


# PURPOSE: brain アーティファクト (.md) をパースし構造化 dict に変換する
def parse_artifact_md(path: Path, conv_id: str) -> dict:
    """PURPOSE: brain アーティファクト (.md) をパースし構造化 dict に変換する"""
    text = path.read_text(encoding="utf-8", errors="replace")

    # Title: first H1 line
    title = path.stem
    for line in text.split("\n")[:5]:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # Artifact type from filename
    artifact_type = path.stem  # task, walkthrough, implementation_plan

    # Try to load metadata.json for summary/updatedAt
    meta_path = path.parent / f"{path.name}.metadata.json"
    summary = ""
    updated_at = ""
    version = ""
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            summary = meta.get("summary", "")
            updated_at = meta.get("updatedAt", "")
            version = meta.get("version", "")
        except Exception:  # noqa: BLE001
            pass  # Intentional: metadata may be malformed

    # Section headers for content overview
    sections = _RE_SECTION.findall(text)
    sections = [re.sub(r"^[^\w]+", "", s).strip() for s in sections]

    return {
        "title": title,
        "artifact_type": artifact_type,
        "conv_id": conv_id,
        "summary": summary,
        "updated_at": updated_at,
        "version": version,
        "sections": sections,
        "text": text,
        "filename": path.name,
    }


# PURPOSE: パース済みアーティファクト dict を GnosisIndex 互換レコードに変換する (チャンキング対応)
def artifacts_to_records(artifacts: list[dict]) -> list[dict]:
    """PURPOSE: パース済みアーティファクト dict を GnosisIndex 互換レコードに変換する"""
    chunker = _get_chunker()

    records = []
    for a in artifacts:
        if not a:
            continue

        # Build abstract
        abstract_parts = [f"[{a['artifact_type']}] {a['title']}"]
        if a["updated_at"]:
            abstract_parts.append(f"({a['updated_at'][:10]})")
        if a["summary"]:
            abstract_parts.append(f"— {a['summary'][:300]}")
        elif a["sections"]:
            abstract_parts.append("— " + ", ".join(a["sections"][:6]))
        base_abstract = " ".join(abstract_parts)

        primary_key_base = f"artifact:{a['conv_id']}:{a['filename']}"
        url_base = f"session://{a['conv_id']}"

        # Chunking
        chunks = chunker.chunk(a["text"], source_id=primary_key_base, title=a["title"])

        if not chunks:
            # Fallback: single record
            records.append({
                "primary_key": primary_key_base,
                "title": f"[{a['artifact_type']}] {a['title']}",
                "source": "artifact",
                "abstract": base_abstract[:500],
                "content": base_abstract,
                "authors": f"type:{a['artifact_type']}",
                "doi": "",
                "arxiv_id": "",
                "url": url_base,
                "citations": int(a.get("version") or 0),
            })
            continue

        for chunk in chunks:
            abstract = base_abstract
            if chunk.get("section_title"):
                abstract += f" — Section: {chunk['section_title']}"

            records.append({
                "primary_key": chunk["id"],
                "title": f"[{a['artifact_type']}] {a['title']}"
                    + (f" ({chunk['section_title']})" if chunk.get("section_title") else ""),
                "source": "artifact",
                "abstract": abstract[:500],
                "content": chunk["text"],
                "authors": f"type:{a['artifact_type']}",
                "doi": "",
                "arxiv_id": "",
                "url": url_base,
                "citations": int(a.get("version") or 0),
            })

    return records


# PURPOSE: brain アーティファクトを GnosisIndex にセマンティックインデックスする
def index_artifacts(artifact_dir: Optional[str] = None,
                    artifact_types: Optional[list[str]] = None) -> int:
    """PURPOSE: brain アーティファクトを GnosisIndex にセマンティックインデックスする"""
    directory = Path(artifact_dir) if artifact_dir else _BRAIN_ARCHIVE_DIR

    if not directory.exists():
        print(f"[ArtifactIndexer] Directory not found: {directory}")
        return 1

    # Collect artifact files across all conversation dirs
    target_names = set(artifact_types) if artifact_types else _ARTIFACT_NAMES
    all_artifacts = []

    # Support both flat (single conv dir) and nested (brain_archive with many conv dirs)
    if any(directory.glob("*.md")):
        # Flat: directory itself contains .md files
        conv_id = directory.name
        for md_file in sorted(directory.glob("*.md")):
            if md_file.name in target_names:
                parsed = parse_artifact_md(md_file, conv_id)
                if parsed:
                    all_artifacts.append(parsed)
    else:
        # Nested: directory contains conv-id subdirectories
        for conv_dir in sorted(directory.iterdir()):
            if not conv_dir.is_dir():
                continue
            conv_id = conv_dir.name
            for md_file in sorted(conv_dir.glob("*.md")):
                if md_file.name in target_names:
                    parsed = parse_artifact_md(md_file, conv_id)
                    if parsed:
                        all_artifacts.append(parsed)

    if not all_artifacts:
        print(f"[ArtifactIndexer] No artifact files found in {directory}")
        return 1

    print(f"[ArtifactIndexer] Found {len(all_artifacts)} artifacts")

    records = artifacts_to_records(all_artifacts)

    if not records:
        print("[ArtifactIndexer] No valid records to index")
        return 1

    # Embed and add to index
    from mekhane.anamnesis.index import GnosisIndex

    index = GnosisIndex()
    embedder = index._get_embedder()

    # Dedupe against existing records
    existing_keys = index.list_primary_keys()
    if existing_keys:
        before = len(records)
        records = [r for r in records if r["primary_key"] not in existing_keys]
        skipped = before - len(records)
        if skipped:
            print(f"[ArtifactIndexer] Skipped {skipped} duplicates")

    if not records:
        print("[ArtifactIndexer] No new artifacts to add (all duplicates)")
        return 0

    # Generate embeddings in batches
    BATCH_SIZE = 16
    data_with_vectors = []
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        texts = [f"{r['title']} {r['abstract']}" for r in batch]
        vectors = embedder.embed_batch(texts)
        for record, vector in zip(batch, vectors):
            record["vector"] = vector
            data_with_vectors.append(record)
        print(f"  Embedded {min(i + BATCH_SIZE, len(records))}/{len(records)}...")

    # Add to index (schema filtering は add_records 内部で自動適用)
    index.add_records(data_with_vectors)

    print(f"[ArtifactIndexer] ✅ Indexed {len(data_with_vectors)} artifacts")
    return 0


# ==============================================================
# WAL Indexer — Intent-WAL YAML を source="wal" でインデックス
# ==============================================================

_WAL_DIR = HANDOFF_DIR


# PURPOSE: Intent-WAL YAML ファイルをパースし構造化 dict に変換する
def parse_wal_yaml(path: Path) -> dict:
    """PURPOSE: Intent-WAL YAML ファイルをパースし構造化 dict に変換する"""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            return {}
    except Exception as e:  # noqa: BLE001
        print(f"  [Warn] Failed to parse {path.name}: {e}")
        return {}

    meta = data.get("meta", {})
    intent = data.get("intent", {})
    progress = data.get("progress", [])
    recovery = data.get("recovery", {})
    context_health = data.get("context_health", {})

    session_id = meta.get("session_id", "")
    session_goal = intent.get("session_goal", "")
    acceptance = intent.get("acceptance_criteria", [])
    context = intent.get("context", "")

    # Progress summary
    progress_steps = []
    if isinstance(progress, list):
        for p in progress:
            if isinstance(p, dict):
                action = p.get("action", "")
                status = p.get("status", "")
                progress_steps.append(f"[{status}] {action}")

    return {
        "session_id": session_id,
        "session_goal": session_goal,
        "acceptance_criteria": acceptance,
        "context": context,
        "progress": progress_steps,
        "progress_count": len(progress_steps),
        "agent": meta.get("agent", ""),
        "created_at": meta.get("created_at", ""),
        "n_chat_messages": meta.get("n_chat_messages", 0),
        "blockers": recovery.get("blockers", []),
        "health_level": context_health.get("level", "green"),
        "text": text,
        "filename": path.name,
    }


# PURPOSE: パース済み WAL dict を GnosisIndex 互換レコードに変換する
def wals_to_records(wals: list[dict]) -> list[dict]:
    """PURPOSE: パース済み WAL dict を GnosisIndex 互換レコードに変換する"""
    records = []
    for w in wals:
        if not w:
            continue

        # Build abstract from goal + progress + health
        abstract_parts = [f"[WAL] {w['session_goal'][:200]}"]
        if w["created_at"]:
            abstract_parts.append(f"({w['created_at'][:10]})")
        if w["progress"]:
            abstract_parts.append(f"— {w['progress_count']} steps")
            # Last 3 progress entries
            recent = w["progress"][-3:]
            abstract_parts.append("; ".join(recent))
        if w["blockers"]:
            abstract_parts.append(f"Blockers: {', '.join(w['blockers'][:3])}")

        abstract = " ".join(abstract_parts)

        # Content: full YAML text
        content = w["text"][:4000]

        # Title
        title = f"[WAL] {w['session_goal'][:100]}" if w["session_goal"] else f"[WAL] {w['filename']}"

        records.append({
            "primary_key": f"wal:{w['filename']}",
            "title": title,
            "source": "wal",
            "abstract": abstract[:500],
            "content": content,
            "authors": w.get("agent", "Claude"),
            "doi": "",
            "arxiv_id": "",
            "url": str(_WAL_DIR / w["filename"]),
            "citations": w["progress_count"],
        })

    return records


# PURPOSE: Intent-WAL ファイル群を GnosisIndex にセマンティックインデックスする
def index_wals(wal_dir: Optional[str] = None) -> int:
    """PURPOSE: Intent-WAL ファイル群を GnosisIndex にセマンティックインデックスする"""
    directory = Path(wal_dir) if wal_dir else _WAL_DIR

    if not directory.exists():
        print(f"[WALIndexer] WAL directory not found: {directory}")
        print("[WALIndexer] Run /boot with WAL integration to generate WAL files first")
        return 1

    yaml_files = sorted(directory.glob("intent_*.yaml"))
    if not yaml_files:
        print("[WALIndexer] No intent_*.yaml files found")
        return 1

    print(f"[WALIndexer] Found {len(yaml_files)} WAL files")

    # Parse all
    wals = [parse_wal_yaml(f) for f in yaml_files]
    records = wals_to_records(wals)

    if not records:
        print("[WALIndexer] No valid WAL records to index")
        return 1

    # Embed and add to index
    from mekhane.anamnesis.index import GnosisIndex

    index = GnosisIndex()
    embedder = index._get_embedder()

    # Dedupe against existing records
    existing_keys = index.list_primary_keys()
    if existing_keys:
        before = len(records)
        records = [r for r in records if r["primary_key"] not in existing_keys]
        skipped = before - len(records)
        if skipped:
            print(f"[WALIndexer] Skipped {skipped} duplicates")

    if not records:
        print("[WALIndexer] No new WALs to add (all duplicates)")
        return 0

    # Generate embeddings (title + abstract for embedding text)
    texts = [f"{r['title']} {r['abstract']}" for r in records]
    vectors = embedder.embed_batch(texts)

    # Attach vectors
    data_with_vectors = []
    for rec, vec in zip(records, vectors):
        rec["vector"] = vec
        data_with_vectors.append(rec)

    # Add to index (schema filtering は add_records 内部で自動適用)
    index.add_records(data_with_vectors)

    print(f"[WALIndexer] ✅ Indexed {len(data_with_vectors)} WALs")
    return 0


# ==============================================================
# PhantasiaField 統合 — 既存パーサーの出力を PhantasiaField.dissolve() 経由で投入
# ==============================================================

# PURPOSE: 任意のソースを PhantasiaField.dissolve() 経由で GnosisIndex に溶解する
def dissolve_source(
    source_type: str,
    source_dir: Optional[str] = None,
    chunker_mode: str = "markdown",
) -> int:
    """PURPOSE: 既存パーサーの出力を PhantasiaField.dissolve() 経由で GnosisIndex に溶解する。

    session_indexer の各パーサー (parse_handoff_md, parse_rom_md, etc.) で
    テキストを抽出し、PhantasiaField.dissolve() で溶解 → add_chunks() → GnosisIndex に投入。

    Args:
        source_type: ソース種別 ("handoff", "rom", "export", "wal", "artifact")
        source_dir: カスタムディレクトリ (None = デフォルト)
        chunker_mode: チャンカー種別 ("markdown" or "nucleator")

    Returns:
        0 = 成功, 1 = エラー
    """
    from mekhane.anamnesis.phantasia_field import PhantasiaField

    field = PhantasiaField(chunker_mode=chunker_mode)
    total_dissolved = 0

    if source_type == "handoff":
        directory = Path(source_dir) if source_dir else _HANDOFF_DIR
        if not directory.exists():
            print(f"[Dissolve] Handoff directory not found: {directory}")
            return 1
        md_files = list_handoff_files(directory)
        if not md_files:
            print("[Dissolve] No handoff_*.md or handoff_*.typos files found")
            return 1
        print(f"[Dissolve] Found {len(md_files)} handoff files")
        for f in md_files:
            parsed = parse_handoff_md(f)
            session_id = parsed.get("session_id", "")
            count = field.dissolve(
                text=parsed["text"],
                source="handoff",
                session_id=session_id,
                title=parsed["title"],
                parent_id=f"handoff:{parsed['filename']}",
            )
            total_dissolved += count

    elif source_type == "rom":
        directory = Path(source_dir) if source_dir else _ROM_DIR
        if not directory.exists():
            print(f"[Dissolve] ROM directory not found: {directory}")
            return 1
        md_files = sorted(directory.glob("rom_*.md"))
        typos_files = sorted(directory.glob("*.typos"))
        all_rom_files = md_files + typos_files
        if not all_rom_files:
            print("[Dissolve] No rom_*.md or *.typos files found")
            return 1
        print(f"[Dissolve] Found {len(all_rom_files)} ROM files ({len(md_files)} .md, {len(typos_files)} .typos)")
        for f in all_rom_files:
            parsed = parse_rom_typos(f) if f.suffix == ".typos" else parse_rom_md(f)
            count = field.dissolve(
                text=parsed["text"],
                source="rom",
                title=parsed["title"],
                parent_id=f"rom:{parsed['filename']}",
            )
            total_dissolved += count

    elif source_type == "export":
        directory = Path(source_dir) if source_dir else _EXPORT_DIR
        if not directory.exists():
            print(f"[Dissolve] Export directory not found: {directory}")
            return 1
        md_files = sorted(directory.glob("*_conv_*.md"))
        if not md_files:
            print("[Dissolve] No export MD files found")
            return 1
        print(f"[Dissolve] Found {len(md_files)} export files")
        for f in md_files:
            parsed = parse_export_md(f)
            count = field.dissolve(
                text=parsed["content"],
                source="export",
                session_id=parsed.get("conv_id", ""),
                title=parsed["title"],
                parent_id=f"export:{parsed['filename']}",
            )
            total_dissolved += count

    elif source_type == "wal":
        directory = Path(source_dir) if source_dir else _WAL_DIR
        if not directory.exists():
            print(f"[Dissolve] WAL directory not found: {directory}")
            return 1
        yaml_files = sorted(directory.glob("intent_*.yaml"))
        if not yaml_files:
            print("[Dissolve] No intent_*.yaml files found")
            return 1
        print(f"[Dissolve] Found {len(yaml_files)} WAL files")
        for f in yaml_files:
            parsed = parse_wal_yaml(f)
            if not parsed:
                continue
            count = field.dissolve(
                text=parsed.get("text", ""),
                source="wal",
                session_id=parsed.get("session_id", ""),
                title=parsed.get("session_goal", f"WAL {f.name}"),
                parent_id=f"wal:{parsed['filename']}",
            )
            total_dissolved += count

    elif source_type == "artifact":
        directory = Path(source_dir) if source_dir else _BRAIN_ARCHIVE_DIR
        if not directory.exists():
            print(f"[Dissolve] Artifact directory not found: {directory}")
            return 1
        # brain_archive 以下の全アーティファクト
        for conv_dir in sorted(directory.iterdir()):
            if not conv_dir.is_dir():
                continue
            conv_id = conv_dir.name
            for md_file in sorted(conv_dir.glob("*.md")):
                if md_file.name in _ARTIFACT_NAMES:
                    parsed = parse_artifact_md(md_file, conv_id)
                    if parsed:
                        count = field.dissolve(
                            text=parsed["text"],
                            source="artifact",
                            session_id=conv_id,
                            title=parsed["title"],
                            parent_id=f"artifact:{conv_id}:{parsed['filename']}",
                        )
                        total_dissolved += count

    else:
        print(f"[Dissolve] Unknown source type: {source_type}")
        print("  Supported: handoff, rom, export, wal, artifact")
        return 1

    print(f"[Dissolve] ✅ Dissolved {total_dissolved} total chunks (source={source_type})")
    return 0


# PURPOSE: trajectorySummaries JSON からセッション情報を GnosisIndex にインデックスする
def index_from_json(json_path: str) -> int:
    """PURPOSE: trajectorySummaries JSON からセッション情報を GnosisIndex にインデックスする"""
    path = Path(json_path)
    if not path.exists():
        print(f"[Error] File not found: {json_path}")
        return 1

    with open(path) as f:
        data = json.load(f)

    sessions = parse_sessions_from_json(data)
    if not sessions:
        print("[Error] No sessions found in JSON")
        return 1

    print(f"[SessionIndexer] Parsed {len(sessions)} sessions")

    records = sessions_to_records(sessions)

    # Embed and add to index
    from mekhane.anamnesis.index import GnosisIndex

    index = GnosisIndex()
    embedder = index._get_embedder()

    # Dedupe against existing records
    existing_keys = index.list_primary_keys()
    if existing_keys:
        before = len(records)
        records = [r for r in records if r["primary_key"] not in existing_keys]
        skipped = before - len(records)
        if skipped:
            print(f"[SessionIndexer] Skipped {skipped} duplicates")

    if not records:
        print("[SessionIndexer] No new sessions to add (all duplicates)")
        return 0

    # Generate embeddings
    BATCH_SIZE = 32
    data_with_vectors = []

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        texts = [f"{r['title']} {r['abstract']}" for r in batch]
        vectors = embedder.embed_batch(texts)

        for record, vector in zip(batch, vectors):
            record["vector"] = vector
            data_with_vectors.append(record)

        print(f"  Processed {min(i + BATCH_SIZE, len(records))}/{len(records)}...")

    # Add to index
    index.add_records(data_with_vectors)

    print(f"[SessionIndexer] ✅ Indexed {len(data_with_vectors)} sessions")
    return 0


# PURPOSE: LS API から直接セッション情報を取得し GnosisIndex にインデックスする
def index_from_api() -> int:
    """PURPOSE: LS API から直接セッション情報を取得し GnosisIndex にインデックスする"""
    script = _HEGEMONIKON_ROOT / "scripts" / "agq-sessions.sh"
    if not script.exists():
        print(f"[Error] Script not found: {script}")
        return 1

    with tempfile.TemporaryDirectory(prefix="agq_sessions_") as tmpdir:
        dump_dir = Path(tmpdir)
        result = subprocess.run(
            ["bash", str(script), "--dump", str(dump_dir)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"[Error] agq-sessions.sh failed: {result.stderr}")
            return 1

        json_path = dump_dir / "trajectories_raw.json"
        if not json_path.exists():
            print("[Error] trajectories_raw.json not generated")
            return 1

        return index_from_json(str(json_path))


# PURPOSE: [L2-auto] 関数: main
def main() -> int:  # PURPOSE: CLI エントリポイント — サブコマンド (sessions/handoffs/conversations/steps/exports) をディスパッチする
    import argparse

    parser = argparse.ArgumentParser(
        description="Index session history into GnosisIndex"
    )
    parser.add_argument(
        "json_path",
        nargs="?",
        help="Path to trajectories_raw.json (from agq-sessions.sh --dump)",
    )
    parser.add_argument(
        "--from-api",
        action="store_true",
        help="Fetch from Language Server API directly",
    )
    parser.add_argument(
        "--handoffs",
        action="store_true",
        help="Index handoff_*.md files from mneme sessions directory",
    )
    parser.add_argument(
        "--handoff-dir",
        default=None,
        help="Custom handoff directory (default: ~/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff)",
    )
    parser.add_argument(
        "--conversations",
        action="store_true",
        help="Index full conversation content from Language Server API",
    )
    parser.add_argument(
        "--max-sessions",
        type=int,
        default=100,
        help="Max sessions to index for --conversations (default: 100)",
    )
    parser.add_argument(
        "--steps",
        action="store_true",
        help="Index .system_generated/steps/ output files from brain dirs",
    )
    parser.add_argument(
        "--max-steps-per-session",
        type=int,
        default=20,
        help="Max step outputs per session to index (default: 20)",
    )
    parser.add_argument(
        "--exports",
        action="store_true",
        help="Index export_chats.py output MD files",
    )
    parser.add_argument(
        "--export-dir",
        default=None,
        help="Custom export directory (default: ~/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff)",
    )
    parser.add_argument(
        "--roms",
        action="store_true",
        help="Index rom_*.md and *.typos files from mneme ROM directory",
    )
    parser.add_argument(
        "--rom-dir",
        default=None,
        help="Custom ROM directory (default: ~/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom)",
    )
    parser.add_argument(
        "--wals",
        action="store_true",
        help="Index intent_*.yaml WAL files into GnosisIndex",
    )
    parser.add_argument(
        "--wal-dir",
        default=None,
        help="Custom WAL directory (default: ~/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff)",
    )
    parser.add_argument(
        "--artifacts",
        action="store_true",
        help="Index brain artifacts (task.md, walkthrough.md, implementation_plan.md)",
    )
    parser.add_argument(
        "--artifact-dir",
        default=None,
        help="Custom artifact directory (default: ~/.gemini/antigravity/brain_archive)",
    )
    parser.add_argument(
        "--dissolve",
        metavar="SOURCE",
        default=None,
        help="Dissolve via PhantasiaField (source: handoff, rom, export, wal, artifact)",
    )
    parser.add_argument(
        "--chunker-mode",
        default="markdown",
        help="Chunker mode for --dissolve (markdown or nucleator, default: markdown)",
    )

    args = parser.parse_args()

    if args.dissolve:
        # PhantasiaField 統合パス
        src_dir = None
        if args.dissolve == "handoff":
            src_dir = args.handoff_dir
        elif args.dissolve == "rom":
            src_dir = args.rom_dir
        elif args.dissolve == "export":
            src_dir = args.export_dir
        elif args.dissolve == "wal":
            src_dir = args.wal_dir
        elif args.dissolve == "artifact":
            src_dir = args.artifact_dir
        return dissolve_source(args.dissolve, src_dir, args.chunker_mode)
    elif args.artifacts:
        return index_artifacts(args.artifact_dir)
    elif args.wals:
        return index_wals(args.wal_dir)
    elif args.exports:
        return index_exports(args.export_dir)
    elif args.roms:
        return index_roms(args.rom_dir)
    elif args.steps:
        return index_steps(max_per_session=args.max_steps_per_session)
    elif args.conversations:
        return index_conversations(args.max_sessions)
    elif args.handoffs:
        return index_handoffs(args.handoff_dir)
    elif args.from_api:
        return index_from_api()
    elif args.json_path:
        return index_from_json(args.json_path)
    else:
        print("Usage: session_indexer.py <json_path> | --from-api | --handoffs | --dissolve <source> | --artifacts | --roms | --steps | --exports")
        return 1


if __name__ == "__main__":
    sys.exit(main())
