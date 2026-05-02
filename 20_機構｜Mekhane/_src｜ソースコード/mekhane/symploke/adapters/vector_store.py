#!/usr/bin/env python3
"""
# PROOF: [L2/インフラ] <- mekhane/symploke/adapters/ A0→ベクトルストレージが必要→vector_store が担う
VectorStore - FAISS ベクトルストレージ + コサイン検索アダプタ

FAISS IndexFlatIP による内積検索 (正規化済みベクトル = cosine similarity)。
メモリ効率: 旧 List[ndarray] + 毎回 vstack → FAISS の連続メモリ + ネイティブ検索。
エンベディング生成は embedder_factory 経由の VertexEmbedder が担当。

旧名: EmbeddingAdapter (後方互換エイリアスは embedding_adapter.py に残置)
"""

import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import faiss
from .base import VectorStoreAdapter, SearchResult


class VectorStore(VectorStoreAdapter):
    """
    FAISS ベクトルストレージ + コサイン検索アダプタ

    エンベディング生成は embedder_factory.get_embed_fn() を使うこと。
    このクラスはストレージとインデックス検索のみを担当する。

    Usage:
        store = VectorStore()
        store.create_index(3072)  # VertexEmbedder: 3072d
        ids = store.add_vectors(vectors, metadata=[...])
        results = store.search(query_vector, k=5)
    """

    def __init__(self, **kwargs):
        # model_name was removed (FAISS migration). kwargs absorbs legacy callers.
        self._dimension: Optional[int] = None
        self._index: Optional[faiss.IndexFlatIP] = None
        self._metadata: Dict[int, Dict[str, Any]] = {}
        self._next_id: int = 0

    @property
    def name(self) -> str:
        return "vector_store"

    @property
    def dimension(self) -> Optional[int]:
        return self._dimension

    def create_index(
        self, dimension: int, index_name: str = "default", **kwargs
    ) -> None:
        """インデックスを作成。

        kwargs:
            index_type: "flat" (default) | "ivfpq"
            nlist: IVF クラスタ数 (default: sqrt(n) 相当, 最低 16)
            m: PQ サブ量子化器数 (default: 96, dimension の約数)
            nbits: PQ ビット数 (default: 8)
            nprobe: 検索時の探索クラスタ数 (default: nlist//4)
        """
        self._dimension = dimension
        index_type = kwargs.get("index_type", "flat")

        if index_type == "ivfpq":
            nlist = kwargs.get("nlist", 16)
            m = kwargs.get("m", 96)
            nbits = kwargs.get("nbits", 8)
            if dimension % m != 0:
                raise ValueError(f"dimension ({dimension}) must be divisible by m ({m})")
            quantizer = faiss.IndexFlatIP(dimension)
            self._index = faiss.IndexIVFPQ(quantizer, dimension, nlist, m, nbits,
                                            faiss.METRIC_INNER_PRODUCT)
            self._nprobe = kwargs.get("nprobe", max(1, nlist // 4))
        else:
            self._index = faiss.IndexFlatIP(dimension)
            self._nprobe = None

        self._metadata = {}
        self._next_id = 0

    def add_vectors(
        self,
        vectors: np.ndarray,
        ids: Optional[List[int]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> List[int]:
        if self._index is None:
            raise RuntimeError("Index not created. Call create_index first.")

        if vectors.ndim != 2:
            raise ValueError(f"Expected 2D array, got {vectors.ndim}D")

        n = vectors.shape[0]

        if ids is None:
            ids = list(range(self._next_id, self._next_id + n))
            self._next_id += n

        # 正規化 (cosine similarity = 正規化ベクトルの内積)
        vecs = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(vecs)

        # IVFPQ は train が必要
        if hasattr(self._index, 'is_trained') and not self._index.is_trained:
            self._index.train(vecs)

        self._index.add(vecs)

        for i in range(n):
            if metadata and i < len(metadata):
                self._metadata[ids[i]] = metadata[i]
            else:
                self._metadata[ids[i]] = {}

        return ids

    def search(
        self, query: np.ndarray, k: int = 10, threshold: Optional[float] = None
    ) -> List[SearchResult]:
        if self._index is None:
            raise RuntimeError("Index not created.")

        if self._index.ntotal == 0:
            return []

        query = np.array(query, dtype=np.float32).reshape(1, -1)
        faiss.normalize_L2(query)

        # IVF 系は nprobe を設定
        if self._nprobe is not None and hasattr(self._index, 'nprobe'):
            self._index.nprobe = self._nprobe

        actual_k = min(k, self._index.ntotal)
        scores, indices = self._index.search(query, actual_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            if threshold is not None and score < threshold:
                continue
            results.append(
                SearchResult(
                    id=int(idx),
                    score=float(score),
                    metadata=self._metadata.get(int(idx), {}),
                )
            )

        return results

    def delete(self, ids: List[int]) -> int:
        """指定 id のベクトルと metadata を除去し、id を再割当て。

        FAISS IndexFlatIP は個別削除不可のため、インデックスを再構築する。
        """
        if not ids or self._index is None:
            return 0

        id_set = set(ids)
        total = self._index.ntotal
        if total == 0:
            return 0

        if hasattr(self._index, "get_xb"):
            all_vecs = faiss.rev_swig_ptr(self._index.get_xb(), total * self._dimension)
            all_vecs = all_vecs.reshape(total, self._dimension).copy()
        elif hasattr(self._index, "reconstruct_n"):
            if hasattr(self._index, "make_direct_map"):
                try:
                    self._index.make_direct_map()
                except Exception:
                    pass
            all_vecs = np.asarray(
                self._index.reconstruct_n(0, total),
                dtype=np.float32,
            ).reshape(total, self._dimension).copy()
        else:
            raise RuntimeError(
                f"Vector extraction is not supported for index type {type(self._index).__name__}"
            )

        new_vecs = []
        new_metadata: Dict[int, Dict[str, Any]] = {}
        new_id = 0
        for old_id in range(total):
            if old_id not in id_set:
                new_vecs.append(all_vecs[old_id])
                old_meta = self._metadata.get(old_id, {})
                new_metadata[new_id] = old_meta
                new_id += 1

        deleted = total - len(new_vecs)
        if new_vecs:
            mat = np.vstack(new_vecs).astype(np.float32)
            faiss.normalize_L2(mat)
        else:
            mat = None

        if isinstance(self._index, faiss.IndexIVFPQ) and mat is not None:
            nlist = self._index.nlist
            m = self._index.pq.M
            nbits = self._index.pq.nbits
            # FAISS は k=2**nbits に対して概ね 39*k 点以上を推奨する。
            min_train_points = max(nlist, (1 << nbits) * 39)
            if mat.shape[0] >= min_train_points:
                nprobe = getattr(self._index, "nprobe", max(1, nlist // 4))
                rebuilt = faiss.IndexIVFPQ(
                    faiss.IndexFlatIP(self._dimension),
                    self._dimension,
                    nlist,
                    m,
                    nbits,
                    faiss.METRIC_INNER_PRODUCT,
                )
                rebuilt.train(mat)
                rebuilt.add(mat)
                rebuilt.nprobe = min(max(1, nprobe), nlist)
                self._index = rebuilt
            else:
                self._index = faiss.IndexFlatIP(self._dimension)
                self._index.add(mat)
        else:
            self._index = faiss.IndexFlatIP(self._dimension)
            if mat is not None:
                self._index.add(mat)
        self._metadata = new_metadata
        self._next_id = new_id
        return deleted

    def delete_by_source(self, source_path: str) -> int:
        """metadata の 'source' フィールドが一致するエントリを一括削除。"""
        ids_to_delete = [
            idx for idx, meta in self._metadata.items()
            if meta.get("source") == source_path
        ]
        return self.delete(ids_to_delete)

    def get_ids_by_source(self, source_path: str) -> List[int]:
        """指定 source パスに属する全 id を返す。"""
        return [
            idx for idx, meta in self._metadata.items()
            if meta.get("source") == source_path
        ]

    def save(self, path: str, manifest: Optional[Dict[str, float]] = None) -> None:
        """FAISS index + metadata を保存。

        保存形式:
          {path}.faiss  — FAISS index (ベクトルのみ)
          {path}.meta   — metadata + manifest (pickle)
        旧 .pkl 互換: path が .pkl の場合も .faiss/.meta に分離保存。
        """
        base = path.removesuffix(".pkl")
        faiss_path = base + ".faiss"
        meta_path = base + ".meta"

        if self._index is not None:
            faiss.write_index(self._index, faiss_path)

        meta_data = {
            "dimension": self._dimension,
            "metadata": self._metadata,
            "next_id": self._next_id,
            "manifest": manifest or {},
        }
        with open(meta_path, "wb") as f:
            pickle.dump(meta_data, f)

    def load(self, path: str) -> Optional[Dict[str, float]]:
        """FAISS index + metadata を読込。既存 pkl からの自動 migration 対応。"""
        base = path.removesuffix(".pkl")
        faiss_path = base + ".faiss"
        meta_path = base + ".meta"

        if Path(faiss_path).exists() and Path(meta_path).exists():
            return self._load_faiss(faiss_path, meta_path)

        if Path(path).exists() and path.endswith(".pkl"):
            return self._migrate_from_pkl(path)

        raise FileNotFoundError(f"No index found at {path} (tried .faiss/.meta and .pkl)")

    def _load_faiss(self, faiss_path: str, meta_path: str) -> Optional[Dict[str, float]]:
        """FAISS native format から読込。"""
        self._index = faiss.read_index(faiss_path)
        self._dimension = self._index.d

        # IVF 系の nprobe を復元
        if hasattr(self._index, 'nprobe'):
            self._nprobe = max(1, self._index.nlist // 4) if hasattr(self._index, 'nlist') else 4
        else:
            self._nprobe = None

        with open(meta_path, "rb") as f:
            meta_data = pickle.load(f)
        self._metadata = meta_data["metadata"]
        self._next_id = meta_data["next_id"]
        return meta_data.get("manifest")

    def _migrate_from_pkl(self, pkl_path: str) -> Optional[Dict[str, float]]:
        """旧 pkl 形式を読み込み、FAISS 形式に変換して保存し直す。"""
        with open(pkl_path, "rb") as f:
            data = pickle.load(f)

        self._dimension = data["dimension"]
        self._metadata = data["metadata"]
        self._next_id = data["next_id"]

        vectors = data["vectors"]
        self._index = faiss.IndexFlatIP(self._dimension)
        if vectors:
            mat = np.vstack(vectors).astype(np.float32)
            faiss.normalize_L2(mat)
            self._index.add(mat)

        # FAISS 形式で保存し直す (次回からは高速ロード)
        self.save(pkl_path, manifest=data.get("manifest"))

        return data.get("manifest")

    def count(self) -> int:
        if self._index is None:
            return 0
        return self._index.ntotal

    def get_metadata(self, id: int) -> Optional[Dict[str, Any]]:
        return self._metadata.get(id)
