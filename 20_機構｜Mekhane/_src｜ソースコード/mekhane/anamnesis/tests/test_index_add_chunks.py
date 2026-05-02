# PROOF: mekhane/anamnesis/tests/test_index_add_chunks.py
# PURPOSE: anamnesis モジュールの index_add_chunks に対するテスト
"""GnosisIndex.add_chunks テスト — 溶解メソッドのユニットテスト。

Mock embedder を利用して Vertex AI API への依存なしにテストする。
_get_embedder() と _table_exists() を直接パッチして内部実装に依存しない。
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from mekhane.anamnesis.index import GnosisIndex


class MockField:
    """スキーマフィールドのモック。"""
    def __init__(self, name):
        self.name = name


# Hyphē 拡張を含む全スキーマフィールド
ALL_SCHEMA_FIELDS = [
    MockField(f) for f in [
        "id", "primary_key", "source", "source_id", "title", "abstract",
        "authors", "published", "url", "pdf_url", "citations", "categories",
        "venue", "collected_at", "doi", "arxiv_id", "vector",
        "content", "chunk_index", "parent_id", "section_title",
        "precision", "density", "session_id", "project_id", "metadata_json",
    ]
]


@pytest.fixture
def mock_embedder():
    """Embedder のモック。"""
    embedder = MagicMock()
    embedder._dimension_mismatch = False
    # 3072 次元のダミーベクトルを返す（バッチサイズに合わせて動的に返す）
    embedder.embed_batch.side_effect = lambda texts: [[0.1] * 3072 for _ in texts]
    return embedder


@pytest.fixture
def mock_table():
    """Backend テーブルのモック。"""
    table = MagicMock()
    table.schema = ALL_SCHEMA_FIELDS
    return table


@pytest.fixture
def sample_chunks():
    """サンプルチャンク (chunker.chunk() の出力形式)。"""
    return [
        {
            "id": "chunk_001",
            "parent_id": "session_20260314",
            "text": "FEP は変分自由エネルギーの最小化原理である",
            "section_title": "概要",
            "chunk_index": 0,
        },
        {
            "id": "chunk_002",
            "parent_id": "session_20260314",
            "text": "能動推論は行動で環境を変える",
            "section_title": "能動推論",
            "chunk_index": 1,
            "coherence": 0.95,
            "drift": 0.1,
            "efe": 0.72,
        },
        {
            "id": "chunk_003",
            "parent_id": "session_20260314",
            "text": "精度最適化は precision の正確な設定",
            "section_title": "精度",
            "chunk_index": 2,
        },
    ]


def _make_index(mock_embedder, mock_table, table_exists=False, primary_keys=None):
    """テスト用 GnosisIndex を構成する (コンストラクタを経由せず)。"""
    index = GnosisIndex.__new__(GnosisIndex)
    index.db = MagicMock()
    index.TABLE_NAME = "knowledge"
    index._primary_key_cache = set(primary_keys or [])
    index._backend_name = "faiss"

    # _get_embedder → mock_embedder を返す
    index._get_embedder = MagicMock(return_value=mock_embedder)

    # _table_exists → table_exists を返す
    index._table_exists = MagicMock(return_value=table_exists)

    # _load_primary_keys → 何もしない
    index._load_primary_keys = MagicMock()

    # db.open_table → mock_table を返す
    index.db.open_table.return_value = mock_table

    # StorageBackend モック (Backend API に移行済みの add_chunks が使用)
    mock_backend = MagicMock()
    mock_backend.exists.return_value = table_exists
    # schema_fields() は mock_table.schema のフィールド名を返す
    mock_backend.schema_fields.return_value = [f.name for f in mock_table.schema]
    # create() / add() は db.create_table / table.add に委譲
    def _backend_create(data):
        index.db.create_table(index.TABLE_NAME, data=data)
    def _backend_add(data):
        mock_table.add(data)
    mock_backend.create.side_effect = _backend_create
    mock_backend.add.side_effect = _backend_add
    index._backend = mock_backend

    return index


class TestAddChunks:
    """add_chunks テスト。"""

    def test_add_chunks_creates_table(self, mock_embedder, mock_table, sample_chunks):
        """テーブルが存在しない場合 create_table を呼ぶ。"""
        index = _make_index(mock_embedder, mock_table, table_exists=False)

        count = index.add_chunks(
            chunks=sample_chunks,
            source="session",
            session_id="test_session",
        )

        assert count == 3
        index.db.create_table.assert_called_once()
        call_args = index.db.create_table.call_args
        assert call_args[0][0] == "knowledge"
        data = call_args[1].get("data") or call_args[0][1]
        assert len(data) == 3

    def test_add_chunks_to_existing_table(self, mock_embedder, mock_table, sample_chunks):
        """テーブルが存在する場合 table.add を呼ぶ。"""
        index = _make_index(mock_embedder, mock_table, table_exists=True)

        count = index.add_chunks(
            chunks=sample_chunks,
            source="session",
        )

        assert count == 3
        mock_table.add.assert_called_once()

    def test_add_chunks_empty(self, mock_embedder, mock_table):
        """空チャンクリスト。"""
        index = _make_index(mock_embedder, mock_table)
        count = index.add_chunks(chunks=[])
        assert count == 0

    def test_add_chunks_dedupe(self, mock_embedder, mock_table, sample_chunks):
        """重複排除: chunk_001 は既存 → 除外される。"""
        index = _make_index(
            mock_embedder, mock_table,
            table_exists=True,
            primary_keys=["chunk_001"],
        )

        count = index.add_chunks(
            chunks=sample_chunks,
            source="session",
            dedupe=True,
        )

        # chunk_001 は重複で除外、chunk_002 と chunk_003 のみ
        assert count == 2
        mock_embedder.embed_batch.assert_called()

    def test_add_chunks_metadata_json(self, mock_embedder, mock_table, sample_chunks):
        """NucleatorChunker のメタデータが metadata_json に格納される。"""
        index = _make_index(mock_embedder, mock_table, table_exists=False)

        index.add_chunks(chunks=sample_chunks, source="session")

        # create_table の data を検査
        data = index.db.create_table.call_args[1].get("data") or index.db.create_table.call_args[0][1]

        # chunk_002 は coherence/drift/efe 付き
        chunk_002_record = [d for d in data if d["id"] == "chunk_002"][0]
        meta = json.loads(chunk_002_record["metadata_json"])
        assert meta["coherence"] == 0.95
        assert meta["drift"] == 0.1
        assert meta["efe"] == 0.72

        # chunk_001 は追加メタなし
        chunk_001_record = [d for d in data if d["id"] == "chunk_001"][0]
        meta = json.loads(chunk_001_record["metadata_json"])
        assert meta == {}

    def test_add_chunks_dimension_mismatch(self, mock_embedder, mock_table, sample_chunks):
        """次元不一致時にブロック。"""
        mock_embedder._dimension_mismatch = True
        index = _make_index(mock_embedder, mock_table)

        count = index.add_chunks(chunks=sample_chunks, source="session")
        assert count == 0

    def test_add_chunks_no_dedupe(self, mock_embedder, mock_table, sample_chunks):
        """重複排除なし: 全件追加。"""
        index = _make_index(
            mock_embedder, mock_table,
            table_exists=False,
            primary_keys=["chunk_001"],  # 既存だが dedupe=False
        )

        count = index.add_chunks(
            chunks=sample_chunks,
            source="session",
            dedupe=False,
        )

        # dedupe=False なので全件追加
        assert count == 3

    def test_add_chunks_record_structure(self, mock_embedder, mock_table, sample_chunks):
        """レコード構造が正しいことを確認。"""
        index = _make_index(mock_embedder, mock_table, table_exists=False)

        index.add_chunks(
            chunks=sample_chunks,
            source="handoff",
            session_id="sid_001",
            project_id="proj_001",
        )

        data = index.db.create_table.call_args[1].get("data") or index.db.create_table.call_args[0][1]
        record = data[0]

        # 必須フィールドの存在確認
        assert record["source"] == "handoff"
        assert record["session_id"] == "sid_001"
        assert record["project_id"] == "proj_001"
        assert record["primary_key"] == "chunk_001"
        assert record["content"] == sample_chunks[0]["text"]
        assert isinstance(record["vector"], list)
        assert len(record["vector"]) == 3072

    def test_add_chunks_schema_filter(self, mock_embedder, mock_table, sample_chunks):
        """既存テーブルへの追加時、スキーマにないフィールドはフィルタされる。"""
        # スキーマを限定 (拡張フィールドなし)
        limited_schema = [MockField(f) for f in ["id", "primary_key", "source", "vector"]]
        mock_table.schema = limited_schema
        index = _make_index(mock_embedder, mock_table, table_exists=True)

        index.add_chunks(chunks=sample_chunks, source="session")

        # table.add に渡されたデータを検査
        call_data = mock_table.add.call_args[0][0]
        for record in call_data:
            assert set(record.keys()) == {"id", "primary_key", "source", "vector"}

    def test_add_chunks_updates_cache(self, mock_embedder, mock_table, sample_chunks):
        """add_chunks 後に primary_key_cache が更新される。"""
        index = _make_index(mock_embedder, mock_table, table_exists=False)
        assert "chunk_001" not in index._primary_key_cache

        index.add_chunks(chunks=sample_chunks, source="session")

        assert "chunk_001" in index._primary_key_cache
        assert "chunk_002" in index._primary_key_cache
        assert "chunk_003" in index._primary_key_cache
