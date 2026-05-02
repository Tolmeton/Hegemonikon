from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/anamnesis/backends/faiss_backend.py
"""FAISSBackend — FAISS IndexFlatIP ベースのベクトルストレージ。

特徴:
- 精度 100% (brute-force 内積検索)
- ベクトル: FAISS IndexFlatIP に格納
- メタデータ: NumPy structured array + pickle で永続化
- ~10万ベクトルで ~10ms の検索速度
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


class FAISSBackend:
    """FAISS IndexFlatIP ストレージバックエンド。

    ベクトルは FAISS Index に、メタデータは pickle で永続化。
    """

    # PURPOSE: FAISSBackend の初期化
    def __init__(self, storage_dir: Path, table_name: str = "knowledge"):
        try:
            import faiss as _faiss
            self._faiss = _faiss
        except ImportError:
            raise ImportError("faiss package required: pip install faiss-cpu")

        self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._table_name = table_name

        # ファイルパス
        self._index_path = self._storage_dir / f"{table_name}.faiss"
        self._meta_path = self._storage_dir / f"{table_name}.meta.pkl"

        # 遅延ロード
        # IDMap でラップ: remove_ids による効率的削除を実現
        self._index: Optional[_faiss.IndexIDMap] = None
        self._metadata: dict[int, dict] = {}  # id -> metadata
        self._dimension: Optional[int] = None
        self._loaded = False
        self._next_id: int = 0

    # PURPOSE: インデックスとメタデータのロード
    def _load(self) -> None:
        """永続化されたインデックスとメタデータをロードする。"""
        if self._loaded:
            return

        if self._index_path.exists() and self._meta_path.exists():
            self._index = self._faiss.read_index(str(self._index_path))
            with open(self._meta_path, "rb") as f:
                loaded = pickle.load(f)
            # 後方互換: list[dict] → dict[int, dict] への移行
            if isinstance(loaded, list):
                self._metadata = {i: m for i, m in enumerate(loaded)}
                self._next_id = len(loaded)
            else:
                self._metadata = loaded.get("metadata", {})
                self._next_id = loaded.get("next_id", len(self._metadata))
            self._dimension = self._index.d
            log.debug(f"[FAISSBackend] Loaded: {self._index.ntotal} vectors, dim={self._dimension}")
        self._loaded = True

    # PURPOSE: インデックスとメタデータの永続化
    def _save(self) -> None:
        """インデックスとメタデータをファイルに保存する。"""
        if self._index is not None:
            self._faiss.write_index(self._index, str(self._index_path))
            with open(self._meta_path, "wb") as f:
                pickle.dump({"metadata": self._metadata, "next_id": self._next_id}, f)

    # PURPOSE: テーブル/インデックスが存在するか
    def exists(self) -> bool:
        """インデックスファイルが存在するか。"""
        return self._index_path.exists() and self._meta_path.exists()

    # PURPOSE: 新規作成 (IDMap ラップ)
    def create(self, data: list[dict]) -> None:
        """新規インデックスを作成し、初期データを投入する。"""
        if not data:
            return

        # 次元を最初のベクトルから推定
        first_vector = data[0].get("vector", [])
        dim = len(first_vector)
        if dim == 0:
            raise ValueError("データにベクトルが含まれていません")

        self._dimension = dim
        # IDMap(IndexFlatIP): 明示的 ID 管理 + remove_ids 対応
        flat_index = self._faiss.IndexFlatIP(dim)
        self._index = self._faiss.IndexIDMap(flat_index)
        self._next_id = 0

        # ベクトルを抽出して追加
        vectors = np.array([d["vector"] for d in data], dtype=np.float32)
        # L2正規化 → 内積 = コサイン類似度
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        vectors = vectors / norms

        # 連番 ID を割当
        ids = np.arange(len(data), dtype=np.int64)
        self._index.add_with_ids(vectors, ids)
        self._next_id = len(data)

        # メタデータ (id -> dict, ベクトルを除外して保存)
        self._metadata = {
            i: {k: v for k, v in d.items() if k != "vector"}
            for i, d in enumerate(data)
        }

        self._loaded = True
        self._save()
        log.info(f"[FAISSBackend] Created: {len(data)} records, dim={dim}")

    # PURPOSE: レコードを追加
    def add(self, records: list[dict]) -> int:
        """レコードを追加する。"""
        self._load()

        if not records:
            return 0

        if self._index is None:
            self.create(records)
            return len(records)

        # ベクトル抽出
        vectors = np.array([r["vector"] for r in records], dtype=np.float32)
        # L2正規化
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        vectors = vectors / norms

        # 連番 ID を割当して追加
        ids = np.arange(self._next_id, self._next_id + len(records), dtype=np.int64)
        self._index.add_with_ids(vectors, ids)

        # メタデータ追加
        for i, r in enumerate(records):
            self._metadata[self._next_id + i] = (
                {k: v for k, v in r.items() if k != "vector"}
            )
        self._next_id += len(records)

        self._save()
        return len(records)

    # PURPOSE: ベクトル検索
    def search_vector(
        self,
        query_vector: list[float],
        k: int = 10,
        filter_expr: Optional[str] = None,
    ) -> list[dict]:
        """ベクトル検索 (IDMap(IndexFlatIP) — 内積ベース)。"""
        self._load()

        if self._index is None or self._index.ntotal == 0:
            return []

        # クエリベクトルの正規化
        query = np.array([query_vector], dtype=np.float32)
        norm = np.linalg.norm(query)
        if norm > 0:
            query = query / norm

        # フィルタがある場合は多めに取得してフィルタリング
        search_k = min(k * 3 if filter_expr else k, self._index.ntotal)
        distances, indices = self._index.search(query, search_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx not in self._metadata:
                continue

            record = dict(self._metadata[idx])
            # 内積スコアを距離に変換 (1 - similarity)
            record["_distance"] = float(1.0 - dist)

            # フィルタ適用
            if filter_expr and not self._match_filter(record, filter_expr):
                continue

            results.append(record)
            if len(results) >= k:
                break

        return results

    # PURPOSE: 簡易フィルタ式のマッチング
    @staticmethod
    def _match_filter(record: dict, filter_expr: str) -> bool:
        """簡易フィルタ式をレコードに適用する。

        サポート: "field = 'value'" 形式のみ。
        """
        # "source = 'handoff'" のようなパターンをパース
        match = re.match(r"(\w+)\s*=\s*'([^']*)'", filter_expr.strip())
        if match:
            field, value = match.groups()
            return str(record.get(field, "")) == value

        # "true" は全マッチ
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
        """全文検索 (キーワードマッチング)。"""
        self._load()

        if not self._metadata:
            return []

        keywords = [w.strip().lower() for w in re.split(r'[\s　]+', query) if len(w.strip()) >= 2]
        if not keywords:
            return []

        results = []
        for idx, meta in self._metadata.items():
            # title と abstract でキーワードマッチ
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
            record["_distance"] = 1.0 / (1.0 + score)  # スコアが高いほど距離が小さい
            results.append((score, record))

        # スコア降順でソート
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:k]]

    # PURPOSE: 条件に合致するレコードを削除 (IDMap remove_ids)
    def delete(self, filter_expr: str) -> int:
        """条件に合致するレコードを削除する。

        IDMap の remove_ids を使用し、全再構築を回避する。
        """
        self._load()

        if self._index is None or not self._metadata:
            return 0

        # フィルタにマッチする ID を収集
        ids_to_delete = []
        for idx, meta in self._metadata.items():
            if self._match_filter(meta, filter_expr):
                ids_to_delete.append(idx)

        if not ids_to_delete:
            return 0

        if len(ids_to_delete) == len(self._metadata):
            # 全削除: インデックスを空で再作成
            dim = self._dimension or 3072
            flat_index = self._faiss.IndexFlatIP(dim)
            self._index = self._faiss.IndexIDMap(flat_index)
            self._metadata = {}
            self._save()
            return len(ids_to_delete)

        # IDMap の remove_ids でベクトルを削除
        id_array = np.array(ids_to_delete, dtype=np.int64)
        self._index.remove_ids(id_array)

        # メタデータからも削除
        for idx in ids_to_delete:
            del self._metadata[idx]

        self._save()
        return len(ids_to_delete)

    # PURPOSE: レコード総数
    def count(self) -> int:
        """レコード総数。"""
        self._load()
        return self._index.ntotal if self._index else 0

    # PURPOSE: 全レコードをリストで返す
    def to_list(self) -> list[dict]:
        """全レコードを辞書のリストで返す (ベクトル付き)。"""
        self._load()

        if self._index is None or not self._metadata:
            return []

        # IDMap からベクトルを reconstruct して返す
        results = []
        for idx, meta in self._metadata.items():
            record = dict(meta)
            try:
                vec = self._index.reconstruct(int(idx))
                record["vector"] = vec.tolist()
            except RuntimeError:
                # reconstruct 不能な場合（通常起こらない）
                record["vector"] = [0.0] * (self._dimension or 0)
            results.append(record)

        return results

    # PURPOSE: 全レコードを DataFrame で返す
    def to_pandas(self) -> "pd.DataFrame":
        """全レコードを pandas DataFrame で返す。"""
        import pandas as _pd
        records = self.to_list()
        return _pd.DataFrame(records) if records else _pd.DataFrame()

    # PURPOSE: スキーマフィールド名の集合
    def schema_fields(self) -> set[str]:
        """スキーマのフィールド名の集合 (全レコードのキー和集合)。"""
        self._load()
        if not self._metadata:
            return set()
        # 全レコードのキー和集合 (削除でキーが歯抜けになる場合を考慮)
        fields: set[str] = set()
        for meta in self._metadata.values():
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
        for idx, meta in self._metadata.items():
            changed = False
            for col_name, default_val in columns.items():
                if col_name not in meta:
                    meta[col_name] = default_val
                    changed = True
            if changed:
                migrated_count += 1

        if migrated_count > 0:
            self._save()
            log.info(f"[FAISSBackend] migrate_schema: {migrated_count} レコードを更新")

        return migrated_count

    # PURPOSE: ベクトル次元数を返す
    def get_vector_dimension(self) -> Optional[int]:
        """ベクトルの次元数。"""
        self._load()
        return self._dimension
