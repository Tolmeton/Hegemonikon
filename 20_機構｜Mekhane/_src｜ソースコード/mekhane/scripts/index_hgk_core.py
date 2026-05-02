#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/scripts/index_hgk_core.py
"""
HGK 核心層を専用 FAISS index に投入する CLI。

Usage:
    PYTHONPATH=. python -m mekhane.scripts.index_hgk_core --rebuild
    PYTHONPATH=. python -m mekhane.scripts.index_hgk_core --incremental
    PYTHONPATH=. python -m mekhane.scripts.index_hgk_core --stats
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Iterable

import numpy as np

from mekhane.anamnesis.backends.faiss_backend import FAISSBackend
from mekhane.anamnesis.chunker import MarkdownChunker
from mekhane.anamnesis.vertex_embedder import VertexEmbedder
from mekhane.paths import (
    CONSTRAINTS_DIR,
    EPISTEME_DIR,
    HGK_ROOT,
    INDEX_DIR,
    KERNEL_DIR,
    STATE_VIOLATIONS,
)

LOG = logging.getLogger("hegemonikon.index_hgk_core")

TABLE_NAME = "hgk_core"
MANIFEST_PATH = INDEX_DIR / "hgk_core_manifest.json"
INDEX_PATH = INDEX_DIR / f"{TABLE_NAME}.faiss"
META_PATH = INDEX_DIR / f"{TABLE_NAME}.meta.pkl"
RULES_DIR = Path.home() / ".claude" / "rules"
SKILLS_DIR = Path.home() / ".claude" / "skills"
EMBED_BATCH_SIZE = 50
EMBED_MAX_RETRIES = 5
EXCLUDE_PARTS = {
    ".git",
    "__pycache__",
    ".obsidian",
    "_src",
    "_src｜ソースコード",
    "node_modules",
    "90_保管庫｜Archive",
}


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        env_path = HGK_ROOT / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass


def collect_target_files() -> list[Path]:
    """対象ファイル一覧を返す。"""
    files: set[Path] = set()
    files.update(_glob_files(RULES_DIR, "*.md", recursive=False))
    files.update(_glob_files(SKILLS_DIR, "SKILL.md", recursive=True))

    for root in (KERNEL_DIR, CONSTRAINTS_DIR, EPISTEME_DIR, STATE_VIOLATIONS):
        files.update(_glob_files(root, "*.md", recursive=True))
        files.update(_glob_files(root, "*.typos", recursive=True))

    return sorted(path.resolve() for path in files if path.is_file())


def _glob_files(root: Path, pattern: str, recursive: bool) -> Iterable[Path]:
    if not root.exists():
        return []

    iterator = root.rglob(pattern) if recursive else root.glob(pattern)
    return [path for path in iterator if not _is_excluded(path, root)]


def _is_excluded(path: Path, root: Path) -> bool:
    try:
        relative_parts = set(path.relative_to(root).parts[:-1])
    except ValueError:
        relative_parts = set(path.parts[:-1])
    return bool(relative_parts & EXCLUDE_PARTS)


def build_file_state(paths: Iterable[Path]) -> dict[str, dict[str, float | int]]:
    state: dict[str, dict[str, float | int]] = {}
    for path in paths:
        stat = path.stat()
        state[str(path)] = {
            "mtime": stat.st_mtime,
            "size": stat.st_size,
        }
    return state


def diff_states(
    previous: dict[str, dict[str, float | int]],
    current: dict[str, dict[str, float | int]],
) -> tuple[list[str], list[str]]:
    changed = [
        path
        for path, info in current.items()
        if previous.get(path) != info
    ]
    removed = [path for path in previous if path not in current]
    return sorted(changed), sorted(removed)


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {"files": {}}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def save_manifest(file_state: dict[str, dict[str, float | int]], chunk_counts: dict[str, int]) -> None:
    payload = {
        "table_name": TABLE_NAME,
        "updated_at": time.time(),
        "files": {
            path: {
                **file_state[path],
                "chunks": chunk_counts.get(path, 0),
            }
            for path in sorted(file_state)
        },
    }
    MANIFEST_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def delete_records_for_source(backend: FAISSBackend, source_path: str) -> int:
    """source_path 一致のレコードを削除する。

    FAISSBackend の簡易 filter 式はクォートを含む値に弱いので、
    manifest 差分更新では内部メタデータを直接走査して削除する。
    """
    backend._load()  # noqa: SLF001 - 差分更新のため内部状態に直接アクセスする

    if backend._index is None or not backend._metadata:  # noqa: SLF001
        return 0

    ids_to_delete = [
        idx
        for idx, meta in backend._metadata.items()  # noqa: SLF001
        if str(meta.get("source_path", "")) == source_path
    ]
    if not ids_to_delete:
        return 0

    if len(ids_to_delete) == len(backend._metadata):  # noqa: SLF001
        dim = backend._dimension or 3072  # noqa: SLF001
        flat_index = backend._faiss.IndexFlatIP(dim)  # noqa: SLF001
        backend._index = backend._faiss.IndexIDMap(flat_index)  # noqa: SLF001
        backend._metadata = {}  # noqa: SLF001
        backend._save()  # noqa: SLF001
        return len(ids_to_delete)

    id_array = np.array(ids_to_delete, dtype=np.int64)
    backend._index.remove_ids(id_array)  # noqa: SLF001
    for idx in ids_to_delete:
        del backend._metadata[idx]  # noqa: SLF001
    backend._save()  # noqa: SLF001
    return len(ids_to_delete)


def build_records(
    paths: Iterable[Path],
    chunker: MarkdownChunker,
    embedder: VertexEmbedder,
) -> tuple[list[dict], dict[str, int]]:
    chunk_rows: list[dict] = []
    chunk_counts: dict[str, int] = {}

    for path in paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not text.strip():
            continue

        source_path = str(path.resolve())
        title = _extract_title(path, text)
        chunk_text = strip_redundant_h1(text, title)
        source_id = source_path
        chunks = chunker.chunk(text=chunk_text, source_id=source_id, title=title)
        chunk_counts[source_path] = len(chunks)

        for chunk in chunks:
            section_title = chunk.get("section_title", "") or ""
            heading_path = build_heading_path(title, section_title)
            chunk_rows.append(
                {
                    "id": chunk["id"],
                    "primary_key": chunk["id"],
                    "doc_id": source_path,
                    "source": "hgk_core",
                    "source_path": source_path,
                    "heading_path": heading_path,
                    "chunk_type": "hgk_core",
                    "title": title,
                    "section_title": section_title,
                    "content": chunk["text"],
                    "file_mtime": path.stat().st_mtime,
                    "_embed_text": chunk["text"],
                }
            )

    if not chunk_rows:
        return [], chunk_counts

    embeddings = embed_texts_with_backoff(
        embedder=embedder,
        texts=[row["_embed_text"] for row in chunk_rows],
        batch_size=EMBED_BATCH_SIZE,
    )

    records: list[dict] = []
    for row, vector in zip(chunk_rows, embeddings):
        record = dict(row)
        record.pop("_embed_text", None)
        record["vector"] = vector
        records.append(record)

    return records, chunk_counts


def build_heading_path(title: str, section_title: str) -> str:
    if not section_title or section_title in {"Introduction", title}:
        return title
    if not title:
        return section_title
    return f"{title} > {section_title}"


def embed_texts_with_backoff(
    embedder: VertexEmbedder,
    texts: list[str],
    batch_size: int = EMBED_BATCH_SIZE,
) -> list[list[float]]:
    vectors: list[list[float]] = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        for attempt in range(EMBED_MAX_RETRIES):
            try:
                vectors.extend(embedder.embed_batch(batch))
                break
            except Exception:  # noqa: BLE001
                if attempt == EMBED_MAX_RETRIES - 1:
                    raise
                sleep_sec = min(30, 2 ** attempt)
                LOG.warning("Embedding batch failed; retry in %ss", sleep_sec)
                time.sleep(sleep_sec)

    return vectors


def rebuild_index() -> dict:
    _load_env()
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    for path in (INDEX_PATH, META_PATH, MANIFEST_PATH):
        path.unlink(missing_ok=True)

    backend = FAISSBackend(INDEX_DIR, table_name=TABLE_NAME)
    chunker = MarkdownChunker(max_chars=2000, overlap=200)
    embedder = VertexEmbedder()
    target_files = collect_target_files()
    records, chunk_counts = build_records(target_files, chunker, embedder)
    if records:
        backend.create(records)
    file_state = build_file_state(target_files)
    save_manifest(file_state, chunk_counts)
    return stats()


def incremental_index() -> dict:
    _load_env()
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    backend = FAISSBackend(INDEX_DIR, table_name=TABLE_NAME)
    chunker = MarkdownChunker(max_chars=2000, overlap=200)
    embedder = VertexEmbedder()

    current_files = collect_target_files()
    current_state = build_file_state(current_files)
    manifest = load_manifest()
    previous_files = manifest.get("files", {})
    previous_state = {
        path: {
            "mtime": info.get("mtime"),
            "size": info.get("size"),
        }
        for path, info in previous_files.items()
    }

    changed, removed = diff_states(previous_state, current_state)

    for source_path in changed + removed:
        delete_records_for_source(backend, source_path)

    changed_paths = [Path(path) for path in changed]
    records, chunk_counts = build_records(changed_paths, chunker, embedder)
    if records:
        backend.add(records)

    merged_chunk_counts = {
        path: int(previous_files.get(path, {}).get("chunks", 0))
        for path in current_state
    }
    merged_chunk_counts.update(chunk_counts)

    for removed_path in removed:
        merged_chunk_counts.pop(removed_path, None)

    save_manifest(current_state, merged_chunk_counts)
    result = stats()
    result["changed_files"] = len(changed)
    result["removed_files"] = len(removed)
    return result


def stats() -> dict:
    manifest = load_manifest()
    file_entries = manifest.get("files", {})
    indexed_chunks = sum(int(info.get("chunks", 0)) for info in file_entries.values())
    faiss_available = True

    try:
        backend = FAISSBackend(INDEX_DIR, table_name=TABLE_NAME)
        index_exists = backend.exists()
        if index_exists:
            indexed_chunks = backend.count()
    except ImportError:
        faiss_available = False
        index_exists = INDEX_PATH.exists() and META_PATH.exists()

    return {
        "index_name": TABLE_NAME,
        "index_exists": index_exists,
        "faiss_available": faiss_available,
        "index_path": str(INDEX_PATH),
        "meta_path": str(META_PATH),
        "manifest_path": str(MANIFEST_PATH),
        "indexed_files": len(file_entries),
        "indexed_chunks": indexed_chunks,
    }


def _extract_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return path.stem


def strip_redundant_h1(text: str, title: str) -> str:
    """先頭 H1 が title と一致する場合は除去して chunker に渡す。"""
    lines = text.splitlines()
    if not lines:
        return text

    first_line = lines[0].strip()
    if title and first_line == f"# {title}":
        return "\n".join(lines[1:]).lstrip("\n")

    return text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build hgk_core FAISS index")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--rebuild", action="store_true", help="Rebuild from scratch")
    mode.add_argument("--incremental", action="store_true", help="Update by mtime diff")
    mode.add_argument("--stats", action="store_true", help="Show current index stats")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()

    if args.rebuild:
        result = rebuild_index()
    elif args.incremental:
        result = incremental_index()
    else:
        result = stats()

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
