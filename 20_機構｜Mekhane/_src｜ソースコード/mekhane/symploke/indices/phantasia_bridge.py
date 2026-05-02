#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/indices/ A0→PhantasiaField への直接アクセスが必要
"""
Phantasia Bridge — Symplokē Chronos/Sophia/Kairos を PhantasiaField に統合

VISION.md §5 Phase 2 実装:
Symplokē 4索引のうち chronos / kairos / sophia を、
source tag 事後フィルタで 1 つの PhantasiaField に統合する。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .base import DomainIndex, Document, IndexedResult, SourceType


_CHUNK_SUFFIX_RE = re.compile(r"(?:[_-]sec\d+(?:[_-]chunk\d+)?)$")


class PhantasiaBridge(DomainIndex):
    """Symploke SophiaIndex/ChronosIndex/KairosIndex を PhantasiaField に統合するブリッジ。

    VISION.md §5 Phase 2 実装: source_type tag で事後フィルタすることで
    4 索引を 1 つの PhantasiaField に統合する。
    """

    SOURCE_TAG_MAP = {
        "chronos": ["session"],
        "kairos": ["handoff"],
        "sophia": ["kernel", "rom", "sophia", "doxa"],
    }

    def __init__(self, source_type_name: str, db_dir: Optional[Path] = None):
        if source_type_name not in self.SOURCE_TAG_MAP:
            raise ValueError(f"Unsupported PhantasiaBridge source: {source_type_name}")

        super().__init__(adapter=None, name=source_type_name, dimension=3072)
        self._source_name = source_type_name
        self._db_dir = db_dir
        self._phantasia_field = None
        self._initialized = True

    @property
    def source_type(self) -> SourceType:
        return {
            "chronos": SourceType.CHRONOS,
            "kairos": SourceType.KAIROS,
            "sophia": SourceType.SOPHIA,
        }[self._source_name]

    def _get_field(self):
        if self._phantasia_field is None:
            from mekhane.anamnesis.phantasia_field import PhantasiaField

            db_path = str(self._db_dir) if self._db_dir else None
            self._phantasia_field = PhantasiaField(db_path=db_path)
        return self._phantasia_field

    def search(self, query: str, k: int = 10, **kwargs) -> list[IndexedResult]:
        field = self._get_field()
        tags = self.SOURCE_TAG_MAP[self._source_name]
        all_results: list[dict] = []
        per_tag_k = max(k // len(tags) + 2, 4)

        for tag in tags:
            results = field.recall(query, mode="exploit", limit=per_tag_k, source_filter=tag)
            all_results.extend(results)

        deduped: dict[str, dict] = {}
        for record in all_results:
            doc_key = self._doc_key(record)
            current = deduped.get(doc_key)
            if current is None or record.get("_distance", 1.0) < current.get("_distance", 1.0):
                deduped[doc_key] = record

        ranked = sorted(deduped.values(), key=lambda r: r.get("_distance", 1.0))
        return [self._to_indexed_result(r) for r in ranked[:k]]

    def _to_indexed_result(self, phantasia_dict: dict) -> IndexedResult:
        distance = float(phantasia_dict.get("_distance", 1.0))
        score = float(phantasia_dict.get("_field_score", max(0.0, 1.0 - distance)))
        content = phantasia_dict.get("content") or phantasia_dict.get("text") or ""
        path = (
            phantasia_dict.get("source_path")
            or phantasia_dict.get("file_path")
            or phantasia_dict.get("url")
            or ""
        )

        return IndexedResult(
            doc_id=self._doc_key(phantasia_dict),
            score=score,
            source=self.source_type,
            content=content,
            metadata={
                **phantasia_dict,
                "title": phantasia_dict.get("title", "Untitled"),
                "source_path": path,
                "file_path": path,
                "doc_type": phantasia_dict.get("source"),
                "url": phantasia_dict.get("url", path),
            },
        )

    def count(self) -> int:
        try:
            storage = self._get_field()._get_storage()
            if hasattr(storage, "table_exists") and not storage.table_exists():
                return 0

            backend = getattr(storage, "_backend", None)
            if backend is not None and hasattr(backend, "_load"):
                backend._load()
                metadata = getattr(backend, "_metadata", {})
                tags = set(self.SOURCE_TAG_MAP[self._source_name])
                return sum(1 for record in metadata.values() if record.get("source") in tags)
        except Exception:
            return 0

        return 0

    def exists(self) -> bool:
        return self.count() > 0

    def ingest(self, documents: list[Document]) -> int:
        raise NotImplementedError(
            "PhantasiaBridge does not support ingest. "
            "Use PhantasiaField.dissolve() directly, or run bulk_dissolve_md.py"
        )

    def initialize(self) -> None:
        self._initialized = True

    def save(self, path: str) -> None:
        pass

    def load(self, path: str) -> None:
        self._initialized = True

    @staticmethod
    def _doc_key(record: dict) -> str:
        for key in ("doc_id", "source_path", "file_path", "parent_id", "source_id", "url"):
            value = record.get(key)
            if value:
                return str(value)

        primary_key = str(record.get("primary_key") or record.get("id") or "")
        if primary_key:
            return _CHUNK_SUFFIX_RE.sub("", primary_key)

        title = record.get("title")
        if title:
            return f"title::{title}"

        return "unknown"
