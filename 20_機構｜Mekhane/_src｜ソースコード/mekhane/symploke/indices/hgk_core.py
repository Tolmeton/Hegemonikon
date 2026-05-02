# PROOF: [L2/インフラ] <- mekhane/symploke/indices/hgk_core.py
"""
HGK Core Index

HGK の核心層 (rules / skills / kernel / constraints / episteme / violations)
を専用 FAISS から検索する読み取り専用インデックス。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np

from mekhane.anamnesis.backends.faiss_backend import FAISSBackend
from mekhane.paths import INDEX_DIR

from .base import IndexedResult, SourceType


class HGKCoreIndex:
    """hgk_core.faiss を検索する読み取り専用インデックス。"""

    TABLE_NAME = "hgk_core"

    def __init__(
        self,
        name: str = "hgk_core",
        storage_dir: Optional[Path] = None,
        dimension: int = 3072,
        embed_fn: Optional[Callable[[str], Any]] = None,
    ):
        self._name = name
        self._storage_dir = storage_dir or INDEX_DIR
        self._dimension = dimension
        self._backend = FAISSBackend(self._storage_dir, table_name=self.TABLE_NAME)
        self._embed_fn = embed_fn

        if self._embed_fn is None:
            try:
                from mekhane.symploke.embedder_factory import get_embed_fn

                self._embed_fn = get_embed_fn()
            except Exception:  # noqa: BLE001
                self._embed_fn = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def source_type(self) -> SourceType:
        return SourceType.HGK_CORE

    def exists(self) -> bool:
        return self._backend.exists()

    def count(self) -> int:
        return self._backend.count() if self.exists() else 0

    def load(self, _path: str | None = None) -> None:
        """FAISSBackend は遅延ロードなので no-op。"""

    def ingest(self, _documents) -> int:
        raise NotImplementedError("HGKCoreIndex は index_hgk_core.py からのみ更新します")

    def search(self, query: str, k: int = 10, **kwargs) -> list[IndexedResult]:
        if not self.exists():
            return []

        query_vector = self._embed_query(query)
        if query_vector is not None:
            records = self._backend.search_vector(query_vector, k=k)
        else:
            records = self._backend.search_fts(query, k=k)

        results: list[IndexedResult] = []
        for record in records:
            doc_id = self._doc_id(record)
            score = self._score(record)
            results.append(
                IndexedResult(
                    doc_id=doc_id,
                    score=score,
                    source=self.source_type,
                    content=str(record.get("content", "")),
                    metadata=record,
                )
            )
        return results

    def _embed_query(self, query: str) -> Optional[list[float]]:
        if self._embed_fn is None:
            return None
        try:
            vector = self._embed_fn(query)
        except Exception:  # noqa: BLE001
            return None
        if isinstance(vector, np.ndarray):
            vector = vector.tolist()
        return list(vector)

    @staticmethod
    def _score(record: dict) -> float:
        if "weighted_score" in record:
            return float(record["weighted_score"])
        if "_rrf_score" in record:
            return float(record["_rrf_score"])
        distance = float(record.get("_distance", 1.0))
        return 1.0 - distance

    @staticmethod
    def _doc_id(record: dict) -> str:
        for key in ("doc_id", "source_path", "file_path", "parent_id", "source_id"):
            value = record.get(key)
            if value:
                return str(value)

        primary_key = str(record.get("primary_key") or record.get("id") or "")
        if primary_key:
            return re.sub(r"(?:[_-]sec\d+(?:[_-]chunk\d+)?)$", "", primary_key)
        return "unknown"
