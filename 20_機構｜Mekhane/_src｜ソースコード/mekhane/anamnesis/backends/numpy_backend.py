from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/anamnesis/backends/numpy_backend.py
"""NumpyBackend — NumPy brute-force コサイン検索のフォールバック。

FAISS が利用できない環境用。純粋な NumPy のみで動作。
精度は IndexFlatIP と同一 (brute-force)、ただし速度は劣る。
"""


import json
import logging
import pickle
import re
from pathlib import Path
from typing import Optional, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import pandas as pd

log = logging.getLogger(__name__)


class NumpyBackend:
    """NumPy brute-force ストレージバックエンド。

    FAISS 非対応環境のフォールバック。
    ベクトルとメタデータを NumPy + pickle で管理。
    """

    # PURPOSE: NumpyBackend の初期化
    def __init__(self, storage_dir: Path, table_name: str = "knowledge"):
        self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._table_name = table_name

        # ファイルパス
        self._vectors_path = self._storage_dir / f"{table_name}.vectors.npy"
        self._meta_path = self._storage_dir / f"{table_name}.meta.pkl"

        # 遅延ロード
        self._vectors: Optional[np.ndarray] = None
        self._metadata: list[dict] = []
        self._loaded = False

    # PURPOSE: ロード
    def _load(self) -> None:
        """永続化データをロード。"""
        if self._loaded:
            return

        if self._vectors_path.exists() and self._meta_path.exists():
            self._vectors = np.load(str(self._vectors_path))
            with open(self._meta_path, "rb") as f:
                self._metadata = pickle.load(f)
        self._loaded = True

    # PURPOSE: 保存
    def _save(self) -> None:
        """データをファイルに保存。"""
        if self._vectors is not None:
            np.save(str(self._vectors_path), self._vectors)
            with open(self._meta_path, "wb") as f:
                pickle.dump(self._metadata, f)

    # PURPOSE: 存在チェック
    def exists(self) -> bool:
        return self._vectors_path.exists() and self._meta_path.exists()

    # PURPOSE: 新規作成
    def create(self, data: list[dict]) -> None:
        if not data:
            return

        vectors = np.array([d["vector"] for d in data], dtype=np.float32)
        # L2正規化
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        self._vectors = vectors / norms

        self._metadata = [
            {k: v for k, v in d.items() if k != "vector"}
            for d in data
        ]

        self._loaded = True
        self._save()

    # PURPOSE: レコード追加
    def add(self, records: list[dict]) -> int:
        self._load()

        if not records:
            return 0

        if self._vectors is None:
            self.create(records)
            return len(records)

        new_vectors = np.array([r["vector"] for r in records], dtype=np.float32)
        norms = np.linalg.norm(new_vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        new_vectors = new_vectors / norms

        self._vectors = np.vstack([self._vectors, new_vectors])

        for r in records:
            self._metadata.append(
                {k: v for k, v in r.items() if k != "vector"}
            )

        self._save()
        return len(records)

    # PURPOSE: ベクトル検索
    def search_vector(
        self,
        query_vector: list[float],
        k: int = 10,
        filter_expr: Optional[str] = None,
    ) -> list[dict]:
        self._load()

        if self._vectors is None or len(self._vectors) == 0:
            return []

        # クエリ正規化
        query = np.array(query_vector, dtype=np.float32)
        norm = np.linalg.norm(query)
        if norm > 0:
            query = query / norm

        # コサイン類似度 (正規化済みベクトルの内積)
        similarities = self._vectors @ query

        # argpartition で top-k 候補を O(N) 抽出 + k件のみソート
        n = len(similarities)
        if n == 0:
            return []

        # フィルタがある場合は全件走査が必要 (フィルタ通過数が k 未満の可能性)
        if filter_expr:
            sorted_indices = np.argsort(similarities)[::-1]
        elif k >= n:
            sorted_indices = np.argsort(similarities)[::-1]
        else:
            top_k_idx = np.argpartition(similarities, -k)[-k:]
            sorted_indices = top_k_idx[np.argsort(similarities[top_k_idx])[::-1]]

        results = []
        for idx in sorted_indices:
            idx = int(idx)
            if idx >= len(self._metadata):
                continue

            record = dict(self._metadata[idx])
            record["_distance"] = float(1.0 - similarities[idx])

            if filter_expr and not self._match_filter(record, filter_expr):
                continue

            results.append(record)
            if len(results) >= k:
                break

        return results

    # PURPOSE: 簡易フィルタ
    @staticmethod
    def _match_filter(record: dict, filter_expr: str) -> bool:
        match = re.match(r"(\w+)\s*=\s*'([^']*)'", filter_expr.strip())
        if match:
            field, value = match.groups()
            return str(record.get(field, "")) == value
        if filter_expr.strip().lower() == "true":
            return True
        return False  # パース不能なフィルタは安全側で拒否

    # PURPOSE: 全文検索
    def search_fts(
        self,
        query: str,
        k: int = 10,
        filter_expr: Optional[str] = None,
    ) -> list[dict]:
        self._load()

        if not self._metadata:
            return []

        keywords = [w.strip().lower() for w in re.split(r'[\s　]+', query) if len(w.strip()) >= 2]
        if not keywords:
            return []

        results = []
        for meta in self._metadata:
            title = str(meta.get("title", "")).lower()
            abstract = str(meta.get("abstract", "")).lower()
            content = str(meta.get("content", "")).lower()
            text = f"{title} {abstract} {content}"

            score = sum(1 for kw in keywords if kw in text)
            if score == 0:
                continue

            if filter_expr and not self._match_filter(meta, filter_expr):
                continue

            record = dict(meta)
            record["_distance"] = 1.0 / (1.0 + score)
            results.append((score, record))

        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:k]]

    # PURPOSE: 削除
    def delete(self, filter_expr: str) -> int:
        self._load()

        if self._vectors is None or not self._metadata:
            return 0

        keep_indices = []
        delete_count = 0
        for i, meta in enumerate(self._metadata):
            if self._match_filter(meta, filter_expr):
                delete_count += 1
            else:
                keep_indices.append(i)

        if delete_count == 0:
            return 0

        if not keep_indices:
            self._vectors = np.zeros((0, self._vectors.shape[1]), dtype=np.float32)
            self._metadata = []
        else:
            self._vectors = self._vectors[keep_indices]
            self._metadata = [self._metadata[i] for i in keep_indices]

        self._save()
        return delete_count

    # PURPOSE: レコード総数
    def count(self) -> int:
        self._load()
        return len(self._vectors) if self._vectors is not None else 0

    # PURPOSE: 全レコードリスト
    def to_list(self) -> list[dict]:
        self._load()
        if self._vectors is None or not self._metadata:
            return []

        results = []
        for i, meta in enumerate(self._metadata):
            record = dict(meta)
            record["vector"] = self._vectors[i].tolist()
            results.append(record)
        return results

    # PURPOSE: DataFrame
    def to_pandas(self) -> "pd.DataFrame":
        import pandas as _pd
        records = self.to_list()
        return _pd.DataFrame(records) if records else _pd.DataFrame()

    # PURPOSE: スキーマフィールド名 (全レコードのキー和集合)
    def schema_fields(self) -> set[str]:
        self._load()
        if not self._metadata:
            return set()
        # 全レコードのキー和集合
        fields: set[str] = set()
        for meta in self._metadata:
            fields.update(meta.keys())
        fields.add("vector")  # ベクトルは別管理だがスキーマには含める
        return fields

    # PURPOSE: スキーマに不足フィールドを追加 (冪等)
    def migrate_schema(self, columns: dict[str, object]) -> int:
        """既存レコードに欠損フィールドをデフォルト値で追加する。

        Args:
            columns: {フィールド名: デフォルト値} の辞書

        Returns:
            更新されたレコード数 (全レコード揃っていれば 0)
        """
        self._load()
        if not self._metadata:
            return 0

        migrated_count = 0
        for meta in self._metadata:
            changed = False
            for col_name, default_val in columns.items():
                if col_name not in meta:
                    meta[col_name] = default_val
                    changed = True
            if changed:
                migrated_count += 1

        if migrated_count > 0:
            self._save()
            log.info(f"[NumpyBackend] migrate_schema: {migrated_count} レコードを更新")

        return migrated_count

    # PURPOSE: ベクトル次元数
    def get_vector_dimension(self) -> Optional[int]:
        self._load()
        if self._vectors is not None and len(self._vectors) > 0:
            return self._vectors.shape[1]
        return None
