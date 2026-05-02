# PROOF: [L3/ユーティリティ] <- mekhane/peira/scripts/faiss_store.py O4→FAISS ストレージヘルパー
"""
FaissStore — peira/scripts 用の軽量 FAISS ストレージ
=====================================================

最小限のベクトルストア。
各スクリプト (aidb-kb, arxiv-collector, chat-history-kb) が共通利用。

ストレージ形式:
    {base_dir}/{name}.faiss    — FAISS IndexFlatIP (内積検索)
    {base_dir}/{name}_meta.json — メタデータ (list of dict)
"""

import json
from pathlib import Path
from typing import Optional

import faiss
import numpy as np


# PURPOSE: peira/scripts 向けの軽量 FAISS ベクトルストア
class FaissStore:
    """peira/scripts 向けの軽量 FAISS ベクトルストア。

    connect/create_table/search を提供する最小 API。
    """

    # PURPOSE: ストアの初期化。base_dir にインデックスとメタデータを保存
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _index_path(self, name: str) -> Path:
        return self.base_dir / f"{name}.faiss"

    def _meta_path(self, name: str) -> Path:
        return self.base_dir / f"{name}_meta.json"

    # PURPOSE: 利用可能なテーブル名の一覧を返す
    def list_tables(self) -> list[str]:
        """利用可能なテーブル名の一覧を返す。"""
        return [
            p.stem for p in self.base_dir.glob("*.faiss")
        ]

    # PURPOSE: テーブルの存在チェック
    def has_table(self, name: str) -> bool:
        """テーブルが存在するか。"""
        return self._index_path(name).exists()

    # PURPOSE: テーブルを作成し、ベクトルとメタデータを保存
    def create(self, name: str, data: list[dict], vector_key: str = "vector") -> int:
        """テーブルを作成。既存があれば上書き。

        Args:
            name: テーブル名
            data: レコードのリスト。各レコードに vector_key のベクトルを含む
            vector_key: ベクトルフィールド名

        Returns:
            追加されたレコード数
        """
        if not data:
            return 0

        # ベクトルとメタデータを分離
        vectors = []
        metadata = []
        for record in data:
            rec = dict(record)
            vec = rec.pop(vector_key)
            vectors.append(vec)
            metadata.append(rec)

        # FAISS インデックス作成 (内積検索)
        dim = len(vectors[0])
        arr = np.array(vectors, dtype=np.float32)
        # L2 正規化済みベクトルなら IP ≈ cosine
        faiss.normalize_L2(arr)
        index = faiss.IndexFlatIP(dim)
        index.add(arr)

        # 保存
        faiss.write_index(index, str(self._index_path(name)))
        with open(self._meta_path(name), "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False)

        return len(data)

    # PURPOSE: テーブルを削除
    def drop(self, name: str) -> None:
        """テーブルを削除。"""
        idx = self._index_path(name)
        meta = self._meta_path(name)
        if idx.exists():
            idx.unlink()
        if meta.exists():
            meta.unlink()

    # PURPOSE: ベクトル検索を実行し、メタデータ付きの結果を返す
    def search(self, name: str, query_vector: list[float], k: int = 5) -> list[dict]:
        """ベクトル検索。

        Args:
            name: テーブル名
            query_vector: クエリベクトル
            k: 返す結果数

        Returns:
            メタデータに _score を追加した dict のリスト
        """
        idx_path = self._index_path(name)
        meta_path = self._meta_path(name)

        if not idx_path.exists():
            return []

        index = faiss.read_index(str(idx_path))
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        q = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(q)

        # 実際の結果数を index のサイズに制限
        actual_k = min(k, index.ntotal)
        if actual_k == 0:
            return []

        scores, indices = index.search(q, actual_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(metadata):
                continue
            rec = dict(metadata[idx])
            rec["_score"] = float(score)
            results.append(rec)

        return results

    # PURPOSE: テーブルのレコード数を返す
    def count(self, name: str) -> int:
        """テーブルのレコード数。"""
        idx_path = self._index_path(name)
        if not idx_path.exists():
            return 0
        index = faiss.read_index(str(idx_path))
        return index.ntotal

    # PURPOSE: 既存テーブルにレコードを追加 (incremental 用)
    def add(self, name: str, data: list[dict], vector_key: str = "vector") -> int:
        """既存テーブルにレコードを追加。テーブルがなければ create。

        Args:
            name: テーブル名
            data: 追加するレコードのリスト
            vector_key: ベクトルフィールド名

        Returns:
            追加されたレコード数
        """
        if not data:
            return 0

        if not self.has_table(name):
            return self.create(name, data, vector_key)

        # 既存データを読み込み
        index = faiss.read_index(str(self._index_path(name)))
        with open(self._meta_path(name), "r", encoding="utf-8") as f:
            existing_meta = json.load(f)

        # 新規データを分離
        new_vectors = []
        new_meta = []
        for record in data:
            rec = dict(record)
            vec = rec.pop(vector_key)
            new_vectors.append(vec)
            new_meta.append(rec)

        # 追加
        arr = np.array(new_vectors, dtype=np.float32)
        faiss.normalize_L2(arr)
        index.add(arr)
        existing_meta.extend(new_meta)

        # 保存
        faiss.write_index(index, str(self._index_path(name)))
        with open(self._meta_path(name), "w", encoding="utf-8") as f:
            json.dump(existing_meta, f, ensure_ascii=False)

        return len(data)

    # PURPOSE: ID ベースでレコードを削除し再構築 (incremental update 用)
    def delete_by_ids(self, name: str, id_field: str, ids_to_delete: list[str]) -> int:
        """ID ベースでレコードを削除 (rebuild)。

        FAISS は直接削除をサポートしないため、フィルタして再構築する。

        Args:
            name: テーブル名
            id_field: ID フィールド名
            ids_to_delete: 削除する ID のリスト

        Returns:
            削除されたレコード数
        """
        if not self.has_table(name):
            return 0

        index = faiss.read_index(str(self._index_path(name)))
        with open(self._meta_path(name), "r", encoding="utf-8") as f:
            metadata = json.load(f)

        ids_set = set(ids_to_delete)

        # 全ベクトルを取り出し
        all_vectors = faiss.rev_swig_ptr(
            index.get_xb(), index.ntotal * index.d
        ).reshape(index.ntotal, index.d).copy()

        # フィルタ
        keep_indices = [
            i for i, m in enumerate(metadata)
            if m.get(id_field) not in ids_set
        ]
        deleted = len(metadata) - len(keep_indices)

        if deleted == 0:
            return 0

        # 再構築
        if keep_indices:
            kept_vectors = all_vectors[keep_indices]
            kept_meta = [metadata[i] for i in keep_indices]
            new_index = faiss.IndexFlatIP(index.d)
            new_index.add(kept_vectors)
        else:
            new_index = faiss.IndexFlatIP(index.d)
            kept_meta = []

        faiss.write_index(new_index, str(self._index_path(name)))
        with open(self._meta_path(name), "w", encoding="utf-8") as f:
            json.dump(kept_meta, f, ensure_ascii=False)

        return deleted
