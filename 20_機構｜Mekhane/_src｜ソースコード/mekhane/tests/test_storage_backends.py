# PROOF: [L2/テスト] <- mekhane/tests/test_storage_backends.py
"""StorageBackend 実装テスト。

FAISS / NumPy の各 Backend が StorageBackend Protocol を満たすことを検証する。
テストは一時ディレクトリを使い、実 DB インスタンスは不要。
"""

import json
import os
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest

# ── テスト対象 ─────────────────────────────────────────────────

from mekhane.anamnesis.backends.storage_backend import StorageBackend
from mekhane.anamnesis.backends.numpy_backend import NumpyBackend

# FAISS は optional — 実行時パッケージの有無で判定
try:
    import faiss  # noqa: F401
    from mekhane.anamnesis.backends.faiss_backend import FAISSBackend
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    FAISSBackend = None  # type: ignore




# ── フィクスチャ ───────────────────────────────────────────────

DIM = 128  # テスト用の低次元

def _make_records(n: int, dim: int = DIM, source: str = "test") -> list[dict]:
    """テスト用レコードを生成。"""
    records = []
    for i in range(n):
        vec = np.random.randn(dim).astype(np.float32).tolist()
        records.append({
            "primary_key": f"pk_{i:04d}",
            "title": f"Test Paper {i}",
            "abstract": f"This is abstract number {i} about machine learning",
            "source": source,
            "vector": vec,
            "doi": f"10.1234/{i}",
            "arxiv_id": f"2301.{i:05d}",
            "content": f"Content chunk {i}",
            "density": 0.5,
        })
    return records


@pytest.fixture
def tmp_dir():
    """テスト用一時ディレクトリ。"""
    d = tempfile.mkdtemp(prefix="hgk_backend_test_")
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


# ── Protocol 準拠テスト ────────────────────────────────────────

class TestNumpyBackendProtocol:
    """NumpyBackend が StorageBackend Protocol に準拠するか。"""

    def test_isinstance_check(self, tmp_dir):
        backend = NumpyBackend(tmp_dir, table_name="test")
        assert isinstance(backend, StorageBackend)


@pytest.mark.skipif(not HAS_FAISS, reason="faiss 未インストール")
class TestFAISSBackendProtocol:
    """FAISSBackend が StorageBackend Protocol に準拠するか。"""

    def test_isinstance_check(self, tmp_dir):
        backend = FAISSBackend(tmp_dir, table_name="test")
        assert isinstance(backend, StorageBackend)




# ── NumpyBackend 機能テスト ────────────────────────────────────

class TestNumpyBackend:
    """NumpyBackend の全メソッドを検証。"""

    def test_create_and_exists(self, tmp_dir):
        backend = NumpyBackend(tmp_dir, table_name="test")
        assert not backend.exists()

        records = _make_records(5)
        backend.create(records)
        assert backend.exists()

    def test_count(self, tmp_dir):
        backend = NumpyBackend(tmp_dir, table_name="test")
        records = _make_records(10)
        backend.create(records)
        assert backend.count() == 10

    def test_add(self, tmp_dir):
        backend = NumpyBackend(tmp_dir, table_name="test")
        backend.create(_make_records(5))
        backend.add(_make_records(3, source="extra"))
        assert backend.count() == 8

    def test_search_vector(self, tmp_dir):
        backend = NumpyBackend(tmp_dir, table_name="test")
        records = _make_records(20)
        backend.create(records)

        # 最初のレコードのベクトルで検索 → 自分自身が最上位に来るはず
        query_vec = records[0]["vector"]
        results = backend.search_vector(query_vec, k=5)
        assert len(results) <= 5
        assert "_distance" in results[0]
        # 自分自身の距離は ~0
        assert results[0]["_distance"] < 0.1

    def test_search_vector_with_filter(self, tmp_dir):
        backend = NumpyBackend(tmp_dir, table_name="test")
        records_a = _make_records(10, source="alpha")
        records_b = _make_records(10, source="beta")
        backend.create(records_a + records_b)

        query_vec = records_a[0]["vector"]
        results = backend.search_vector(query_vec, k=20, filter_expr="source = 'alpha'")
        for r in results:
            assert r["source"] == "alpha"

    def test_search_fts(self, tmp_dir):
        backend = NumpyBackend(tmp_dir, table_name="test")
        records = _make_records(10)
        records[0]["title"] = "Attention Is All You Need"
        records[0]["abstract"] = "Transformer architecture for NLP"
        backend.create(records)

        results = backend.search_fts("transformer attention", k=5)
        assert len(results) > 0
        assert "Attention" in results[0]["title"]

    def test_delete(self, tmp_dir):
        backend = NumpyBackend(tmp_dir, table_name="test")
        records = _make_records(5, source="alpha") + _make_records(5, source="beta")
        backend.create(records)
        assert backend.count() == 10

        deleted = backend.delete("source = 'alpha'")
        assert deleted == 5
        assert backend.count() == 5

    def test_delete_all(self, tmp_dir):
        backend = NumpyBackend(tmp_dir, table_name="test")
        backend.create(_make_records(5))
        deleted = backend.delete("true")
        assert deleted == 5
        assert backend.count() == 0

    def test_to_list(self, tmp_dir):
        backend = NumpyBackend(tmp_dir, table_name="test")
        backend.create(_make_records(3))
        records = backend.to_list()
        assert len(records) == 3
        assert "vector" in records[0]
        assert "primary_key" in records[0]

    def test_to_pandas(self, tmp_dir):
        backend = NumpyBackend(tmp_dir, table_name="test")
        backend.create(_make_records(5))
        df = backend.to_pandas()
        assert len(df) == 5
        assert "primary_key" in df.columns

    def test_schema_fields(self, tmp_dir):
        backend = NumpyBackend(tmp_dir, table_name="test")
        backend.create(_make_records(1))
        fields = backend.schema_fields()
        assert "primary_key" in fields
        assert "vector" in fields
        assert "title" in fields

    def test_get_vector_dimension(self, tmp_dir):
        backend = NumpyBackend(tmp_dir, table_name="test")
        backend.create(_make_records(3, dim=256))
        assert backend.get_vector_dimension() == 256

    def test_persistence(self, tmp_dir):
        """保存 → 別インスタンスでロードできるか。"""
        backend1 = NumpyBackend(tmp_dir, table_name="test")
        backend1.create(_make_records(5))
        assert backend1.count() == 5

        # 新しいインスタンスで読み込み
        backend2 = NumpyBackend(tmp_dir, table_name="test")
        assert backend2.exists()
        assert backend2.count() == 5


# ── FAISSBackend 機能テスト ────────────────────────────────────

@pytest.mark.skipif(not HAS_FAISS, reason="faiss 未インストール")
class TestFAISSBackend:
    """FAISSBackend の全メソッドを検証。"""

    def test_create_and_exists(self, tmp_dir):
        backend = FAISSBackend(tmp_dir, table_name="test")
        assert not backend.exists()

        records = _make_records(5)
        backend.create(records)
        assert backend.exists()

    def test_count(self, tmp_dir):
        backend = FAISSBackend(tmp_dir, table_name="test")
        backend.create(_make_records(10))
        assert backend.count() == 10

    def test_add(self, tmp_dir):
        backend = FAISSBackend(tmp_dir, table_name="test")
        backend.create(_make_records(5))
        backend.add(_make_records(3, source="extra"))
        assert backend.count() == 8

    def test_search_vector(self, tmp_dir):
        backend = FAISSBackend(tmp_dir, table_name="test")
        records = _make_records(20)
        backend.create(records)

        query_vec = records[0]["vector"]
        results = backend.search_vector(query_vec, k=5)
        assert len(results) <= 5
        assert "_distance" in results[0]
        assert results[0]["_distance"] < 0.1

    def test_search_vector_with_filter(self, tmp_dir):
        backend = FAISSBackend(tmp_dir, table_name="test")
        records_a = _make_records(10, source="alpha")
        records_b = _make_records(10, source="beta")
        backend.create(records_a + records_b)

        query_vec = records_a[0]["vector"]
        results = backend.search_vector(query_vec, k=20, filter_expr="source = 'alpha'")
        for r in results:
            assert r["source"] == "alpha"

    def test_search_fts(self, tmp_dir):
        backend = FAISSBackend(tmp_dir, table_name="test")
        records = _make_records(10)
        records[0]["title"] = "Free Energy Principle"
        records[0]["abstract"] = "Active inference and predictive coding"
        backend.create(records)

        results = backend.search_fts("energy principle", k=5)
        assert len(results) > 0

    def test_delete(self, tmp_dir):
        backend = FAISSBackend(tmp_dir, table_name="test")
        records = _make_records(5, source="alpha") + _make_records(5, source="beta")
        backend.create(records)
        assert backend.count() == 10

        deleted = backend.delete("source = 'alpha'")
        assert deleted == 5
        assert backend.count() == 5

    def test_to_list(self, tmp_dir):
        backend = FAISSBackend(tmp_dir, table_name="test")
        backend.create(_make_records(3))
        records = backend.to_list()
        assert len(records) == 3
        assert "vector" in records[0]

    def test_to_pandas(self, tmp_dir):
        backend = FAISSBackend(tmp_dir, table_name="test")
        backend.create(_make_records(5))
        df = backend.to_pandas()
        assert len(df) == 5

    def test_schema_fields(self, tmp_dir):
        backend = FAISSBackend(tmp_dir, table_name="test")
        backend.create(_make_records(1))
        fields = backend.schema_fields()
        assert "primary_key" in fields
        assert "vector" in fields

    def test_get_vector_dimension(self, tmp_dir):
        backend = FAISSBackend(tmp_dir, table_name="test")
        backend.create(_make_records(3, dim=512))
        assert backend.get_vector_dimension() == 512

    def test_persistence(self, tmp_dir):
        backend1 = FAISSBackend(tmp_dir, table_name="test")
        backend1.create(_make_records(5))

        backend2 = FAISSBackend(tmp_dir, table_name="test")
        assert backend2.exists()
        assert backend2.count() == 5

    def test_cosine_similarity(self, tmp_dir):
        """L2正規化 + IP = コサイン類似度 を検証。"""
        backend = FAISSBackend(tmp_dir, table_name="test")

        # 同一方向のベクトル → 距離 ≈ 0
        vec_a = [1.0] * DIM
        vec_b = [2.0] * DIM  # 同じ方向、異なるノルム
        vec_c = [-1.0] * DIM  # 逆方向

        records = [
            {"primary_key": "a", "title": "A", "abstract": "", "source": "test", "vector": vec_a},
            {"primary_key": "b", "title": "B", "abstract": "", "source": "test", "vector": vec_b},
            {"primary_key": "c", "title": "C", "abstract": "", "source": "test", "vector": vec_c},
        ]
        backend.create(records)

        results = backend.search_vector(vec_a, k=3)
        # A と B は同方向 → 距離小、C は逆方向 → 距離大
        distances = {r["primary_key"]: r["_distance"] for r in results}
        assert distances["a"] < 0.01, f"自分自身の距離が大きい: {distances['a']}"
        assert distances["b"] < 0.01, f"同方向の距離が大きい: {distances['b']}"
        assert distances["c"] > 1.5, f"逆方向の距離が小さい: {distances['c']}"


# ── GnosisIndex 統合テスト ─────────────────────────────────────

class TestGnosisIndexBackendSwitch:
    """GnosisIndex が backend パラメータで切替可能か。"""

    def test_numpy_backend_init(self, tmp_dir):
        """NumPy Backend で GnosisIndex を初期化。"""
        from mekhane.anamnesis.index import GnosisIndex
        idx = GnosisIndex(db_dir=tmp_dir, backend="numpy")
        assert idx._backend_name == "numpy"
        assert idx.db is None  # NumPy では db は None

    @pytest.mark.skipif(not HAS_FAISS, reason="faiss 未インストール")
    def test_faiss_backend_init(self, tmp_dir):
        """FAISS Backend で GnosisIndex を初期化。"""
        from mekhane.anamnesis.index import GnosisIndex
        idx = GnosisIndex(db_dir=tmp_dir, backend="faiss")
        assert idx._backend_name == "faiss"
        assert idx.db is None



    def test_invalid_backend(self, tmp_dir):
        """未知の Backend → ValueError。"""
        from mekhane.anamnesis.index import GnosisIndex
        with pytest.raises(ValueError, match="Unknown backend"):
            GnosisIndex(db_dir=tmp_dir, backend="sqlite")

    def test_table_exists_empty(self, tmp_dir):
        """空の状態で _table_exists() は False。"""
        from mekhane.anamnesis.index import GnosisIndex
        idx = GnosisIndex(db_dir=tmp_dir, backend="numpy")
        assert not idx._table_exists()

    def test_stats_empty(self, tmp_dir):
        """空インデックスの統計。"""
        from mekhane.anamnesis.index import GnosisIndex
        idx = GnosisIndex(db_dir=tmp_dir, backend="numpy")
        stats = idx.stats()
        assert stats["total"] == 0


# ── migrate_schema テスト (NumPy) ──────────────────────────────

class TestNumpyMigrateSchema:
    """NumpyBackend の migrate_schema テスト。"""

    def test_migrate_adds_missing_fields(self, tmp_dir):
        """欠損フィールドがデフォルト値で追加される。"""
        backend = NumpyBackend(tmp_dir, table_name="test")
        # content や precision を含まないレコードを作成
        records = _make_records(5)
        for r in records:
            r.pop("content", None)
            r.pop("density", None)
        backend.create(records)

        migrated = backend.migrate_schema({"content": "", "precision": 0.5, "density": 0.0})
        assert migrated == 5

        # 全レコードに新フィールドが存在するか確認
        all_records = backend.to_list()
        for r in all_records:
            assert "content" in r
            assert r["content"] == ""
            assert "precision" in r
            assert r["precision"] == 0.5
            assert "density" in r
            assert r["density"] == 0.0

    def test_migrate_idempotent(self, tmp_dir):
        """2回目のマイグレーションは変更なし (返り値 0)。"""
        backend = NumpyBackend(tmp_dir, table_name="test")
        records = _make_records(3)
        backend.create(records)

        # 1回目: _make_records に含まれない新フィールドを追加
        first = backend.migrate_schema({"new_field_a": "", "new_field_b": 0.0})
        assert first > 0  # 新フィールドが追加される

        # 2回目: 全フィールド揃っているので変更なし
        second = backend.migrate_schema({"new_field_a": "", "new_field_b": 0.0})
        assert second == 0

    def test_migrate_preserves_existing_values(self, tmp_dir):
        """既存の値は上書きされない。"""
        backend = NumpyBackend(tmp_dir, table_name="test")
        records = _make_records(3)
        # 明示的に content を設定
        for i, r in enumerate(records):
            r["content"] = f"既存コンテンツ {i}"
        backend.create(records)

        # content のデフォルト値 "" でマイグレーション → 既存値は保持
        backend.migrate_schema({"content": "", "precision": 0.5})

        all_records = backend.to_list()
        for i, r in enumerate(all_records):
            assert r["content"] == f"既存コンテンツ {i}"  # 上書きされていない
            assert r["precision"] == 0.5  # 新フィールドは追加

    def test_schema_fields_union(self, tmp_dir):
        """異なるキーセットのレコードでも schema_fields は和集合を返す。"""
        backend = NumpyBackend(tmp_dir, table_name="test")
        records_a = _make_records(2)
        records_a[0]["extra_field"] = "value"  # 1件目のみに追加フィールド
        backend.create(records_a)

        fields = backend.schema_fields()
        assert "extra_field" in fields
        assert "primary_key" in fields
        assert "vector" in fields


# ── migrate_schema テスト (FAISS) ──────────────────────────────

@pytest.mark.skipif(not HAS_FAISS, reason="faiss 未インストール")
class TestFAISSMigrateSchema:
    """FAISSBackend の migrate_schema テスト。"""

    def test_migrate_adds_missing_fields(self, tmp_dir):
        """欠損フィールドがデフォルト値で追加される。"""
        backend = FAISSBackend(tmp_dir, table_name="test")
        records = _make_records(5)
        for r in records:
            r.pop("content", None)
            r.pop("density", None)
        backend.create(records)

        migrated = backend.migrate_schema({"content": "", "precision": 0.5, "density": 0.0})
        assert migrated == 5

        all_records = backend.to_list()
        for r in all_records:
            assert "content" in r
            assert r["content"] == ""
            assert "precision" in r
            assert r["precision"] == 0.5

    def test_migrate_idempotent(self, tmp_dir):
        """2回目のマイグレーションは変更なし。"""
        backend = FAISSBackend(tmp_dir, table_name="test")
        records = _make_records(3)
        backend.create(records)

        # 1回目: _make_records に含まれない新フィールドを追加
        first = backend.migrate_schema({"new_field_a": "", "new_field_b": 0.0})
        assert first > 0

        second = backend.migrate_schema({"new_field_a": "", "new_field_b": 0.0})
        assert second == 0

    def test_migrate_preserves_existing_values(self, tmp_dir):
        """既存の値は上書きされない。"""
        backend = FAISSBackend(tmp_dir, table_name="test")
        records = _make_records(3)
        for i, r in enumerate(records):
            r["content"] = f"既存コンテンツ {i}"
        backend.create(records)

        backend.migrate_schema({"content": "", "precision": 0.5})

        all_records = backend.to_list()
        for i, r in enumerate(all_records):
            assert r["content"] == f"既存コンテンツ {i}"
            assert r["precision"] == 0.5

    def test_schema_fields_after_delete(self, tmp_dir):
        """削除後も schema_fields がエラーにならない。"""
        backend = FAISSBackend(tmp_dir, table_name="test")
        records = _make_records(5, source="alpha") + _make_records(5, source="beta")
        backend.create(records)

        # alpha を全て削除 (ID 0-4 が消える → キー 0 が歯抜け)
        backend.delete("source = 'alpha'")
        assert backend.count() == 5

        # schema_fields がエラーなく動作するか
        fields = backend.schema_fields()
        assert "primary_key" in fields
        assert "vector" in fields

    def test_schema_fields_union(self, tmp_dir):
        """異なるキーセットのレコードでも和集合を返す。"""
        backend = FAISSBackend(tmp_dir, table_name="test")
        records = _make_records(2)
        records[0]["extra_field"] = "value"
        backend.create(records)

        fields = backend.schema_fields()
        assert "extra_field" in fields
        assert "primary_key" in fields


# ── GnosisIndex 統合テスト (migrate_schema) ────────────────────

class TestGnosisIndexMigrateSchema:
    """GnosisIndex.migrate_schema() がバックエンド経由で動作するか。"""

    def test_migrate_via_numpy_backend(self, tmp_dir):
        """NumPy バックエンド経由でマイグレーションが動作する。"""
        from mekhane.anamnesis.index import GnosisIndex

        idx = GnosisIndex(db_dir=tmp_dir, backend="numpy")
        # バックエンドに直接レコードを投入 (Embedding 不要)
        records = _make_records(5)
        idx._backend.create(records)

        # マイグレーション実行 (HYPHE_F2_COLUMNS を使用)
        migrated = idx.migrate_schema()
        assert migrated > 0  # 少なくとも一部のフィールドが追加されるはず

        # 冪等性チェック
        second = idx.migrate_schema()
        assert second == 0

