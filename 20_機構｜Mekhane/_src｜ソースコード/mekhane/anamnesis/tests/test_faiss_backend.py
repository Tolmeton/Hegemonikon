# PROOF: [L3/テスト] <- mekhane/anamnesis/tests/test_faiss_backend.py
# PURPOSE: FAISSBackend.to_list() の zero-vector bug 回帰防止
"""FAISSBackend zero-vector regression test.

Background:
    旧 to_list() は self._index.reconstruct(external_id) を呼んでいたが、
    IndexIDMap.reconstruct() は未実装。RuntimeError は silently catch され
    [0.0] * dim が返り、上流 (PhantasiaField, WikiLayer LinkGraph) が
    211,118 vectors 全て zero として扱う SNR 0 状態に陥った。

Fix:
    inner = faiss.downcast_index(self._index.index)
    if hasattr(inner, "make_direct_map"): inner.make_direct_map()
    ext_to_local = {eid: i for i, eid in enumerate(faiss.vector_to_array(self._index.id_map))}
    vec = inner.reconstruct(ext_to_local[external_id])
"""

from __future__ import annotations

import pickle

import numpy as np
import pytest

from mekhane.anamnesis.backends.faiss_backend import FAISSBackend


@pytest.fixture
def backend_with_5_chunks(tmp_path):
    """5 chunks を投入した FAISSBackend (IndexIDMap(IndexFlatIP))。"""
    backend = FAISSBackend(storage_dir=tmp_path, table_name="test")
    rng = np.random.default_rng(seed=42)
    data = []
    for i in range(5):
        v = rng.standard_normal(8).astype("float32").tolist()
        data.append(
            {
                "chunk_id": f"chunk_{i}",
                "parent_id": f"doc_{i // 2}",
                "title": f"Title {i}",
                "content": f"Content {i}",
                "density": 0.5,
                "vector": v,
            }
        )
    backend.create(data)
    return backend


def test_to_list_returns_non_zero_vectors(backend_with_5_chunks):
    """to_list() で取り出したベクトルが zero ではないこと (主目的)。"""
    records = backend_with_5_chunks.to_list()
    assert len(records) == 5
    for r in records:
        v = r["vector"]
        norm = float(np.linalg.norm(v))
        assert norm > 0.0, f"zero-vector regression: {r.get('chunk_id')} norm={norm}"


def test_to_list_vectors_are_l2_normalized(backend_with_5_chunks):
    """L2 正規化済み (norm ≈ 1.0)。create() で正規化していることの確認。"""
    records = backend_with_5_chunks.to_list()
    for r in records:
        norm = float(np.linalg.norm(r["vector"]))
        # 正規化後の浮動小数点誤差を許容
        assert abs(norm - 1.0) < 1e-3, f"unexpected norm: {norm}"


def test_to_list_preserves_metadata_fields(backend_with_5_chunks):
    """vector 以外のメタデータフィールドが正しく保持されていること。"""
    records = backend_with_5_chunks.to_list()
    for i, r in enumerate(records):
        assert r["chunk_id"] == f"chunk_{i}"
        assert r["parent_id"] == f"doc_{i // 2}"
        assert r["title"] == f"Title {i}"
        assert r["density"] == 0.5
        assert "vector" in r


def test_to_list_after_add(tmp_path):
    """create + 追加 add 後も to_list() が全レコードのベクトルを返すこと。"""
    backend = FAISSBackend(storage_dir=tmp_path, table_name="test_add")
    rng = np.random.default_rng(seed=1)
    initial = [
        {"chunk_id": f"a_{i}", "vector": rng.standard_normal(8).astype("float32").tolist()}
        for i in range(3)
    ]
    backend.create(initial)
    extra = [
        {"chunk_id": f"b_{i}", "vector": rng.standard_normal(8).astype("float32").tolist()}
        for i in range(2)
    ]
    backend.add(extra)

    records = backend.to_list()
    assert len(records) == 5
    norms = [float(np.linalg.norm(r["vector"])) for r in records]
    assert all(n > 0.5 for n in norms), f"zero-vector after add: {norms}"


def test_to_list_after_delete(tmp_path):
    """delete() でレコード除去後も残レコードの vector が正しく取れること。"""
    backend = FAISSBackend(storage_dir=tmp_path, table_name="test_del")
    rng = np.random.default_rng(seed=2)
    data = [
        {
            "chunk_id": f"c_{i}",
            "tag": "keep" if i % 2 == 0 else "drop",
            "vector": rng.standard_normal(8).astype("float32").tolist(),
        }
        for i in range(6)
    ]
    backend.create(data)
    deleted = backend.delete("tag = 'drop'")
    assert deleted == 3

    records = backend.to_list()
    assert len(records) == 3
    for r in records:
        assert r["tag"] == "keep"
        norm = float(np.linalg.norm(r["vector"]))
        assert norm > 0.5, f"zero-vector after delete: {r.get('chunk_id')}"


def test_load_migrates_legacy_indexidmap_and_persists_delete_support(tmp_path):
    """旧 IndexIDMap 永続化物を load 時に IndexIDMap2 へ移行し delete() を有効化する。"""
    import faiss

    dim = 8
    rng = np.random.default_rng(seed=7)
    vectors = rng.standard_normal((3, dim)).astype("float32")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / np.where(norms == 0, 1, norms)
    ids = np.array([10, 11, 12], dtype=np.int64)

    legacy_index = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
    legacy_index.add_with_ids(vectors, ids)

    index_path = tmp_path / "legacy.faiss"
    meta_path = tmp_path / "legacy.meta.pkl"
    faiss.write_index(legacy_index, str(index_path))
    with open(meta_path, "wb") as f:
        pickle.dump(
            {
                "metadata": {
                    10: {"chunk_id": "legacy_0", "tag": "keep"},
                    11: {"chunk_id": "legacy_1", "tag": "drop"},
                    12: {"chunk_id": "legacy_2", "tag": "keep"},
                },
                "next_id": 13,
            },
            f,
        )

    backend = FAISSBackend(storage_dir=tmp_path, table_name="legacy")
    records = backend.to_list()

    assert len(records) == 3
    assert type(backend._index).__name__ == "IndexIDMap2"
    assert sorted(r["chunk_id"] for r in records) == ["legacy_0", "legacy_1", "legacy_2"]

    deleted = backend.delete("tag = 'drop'")
    assert deleted == 1

    reloaded = FAISSBackend(storage_dir=tmp_path, table_name="legacy")
    remaining = reloaded.to_list()
    assert type(reloaded._index).__name__ == "IndexIDMap2"
    assert sorted(r["chunk_id"] for r in remaining) == ["legacy_0", "legacy_2"]
    assert all(float(np.linalg.norm(r["vector"])) > 0.5 for r in remaining)


def test_to_list_empty_backend(tmp_path):
    """空の backend は空リストを返す (regression check)。"""
    backend = FAISSBackend(storage_dir=tmp_path, table_name="empty")
    assert backend.to_list() == []
