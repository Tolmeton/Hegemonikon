# PROOF: mekhane/anamnesis/tests/test_hyphe_field.py
# PURPOSE: anamnesis モジュールの hyphe_field に対するテスト
"""HypheField テスト — 溶解・想起・密度更新のユニットテスト。

Mock を利用して GnosisIndex と Chunker を差し替えることで、
外部 API (Vertex AI Embedding) への依存なしにテストする。
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from mekhane.anamnesis.hyphe_field import HypheField


@pytest.fixture
def mock_index():
    """GnosisIndex のモック。"""
    index = MagicMock()
    index.stats.return_value = {
        "total": 50,
        "sources": {"session": 30, "handoff": 20},
        "unique_dois": 0,
        "unique_arxiv": 0,
    }
    index.add_chunks.return_value = 5
    index.update_density.return_value = 50
    index.search.return_value = [
        {
            "id": "chunk_1",
            "source": "session",
            "title": "FEP 概要",
            "content": "FEP は自由エネルギー原理です",
            "_distance": 0.1,
            "precision": 0.8,
            "density": 0.3,
            "session_id": "session_abc",
        },
        {
            "id": "chunk_2",
            "source": "handoff",
            "title": "能動推論",
            "content": "能動推論は行動で環境を変える",
            "_distance": 0.3,
            "precision": 0.6,
            "density": 0.7,
            "session_id": "session_def",
        },
        {
            "id": "chunk_3",
            "source": "session",
            "title": "Markov Blanket",
            "content": "マルコフブランケットは境界を定義する",
            "_distance": 0.5,
            "precision": 0.9,
            "density": 0.1,
            "session_id": "session_abc",
        },
    ]
    return index


@pytest.fixture
def mock_chunker():
    """Chunker のモック。"""
    chunker = MagicMock()
    chunker.chunk.return_value = [
        {"id": "c1", "parent_id": "doc1", "text": "テスト1", "section_title": "概要", "chunk_index": 0},
        {"id": "c2", "parent_id": "doc1", "text": "テスト2", "section_title": "詳細", "chunk_index": 1},
        {"id": "c3", "parent_id": "doc1", "text": "テスト3", "section_title": "結論", "chunk_index": 2},
    ]
    return chunker


@pytest.fixture
def field(mock_index, mock_chunker):
    """HypheField インスタンス (モック注入)。"""
    f = HypheField(chunker_mode="markdown")
    f._index = mock_index
    f._chunker = mock_chunker
    return f


class TestDissolve:
    """溶解テスト。"""

    def test_dissolve_basic(self, field, mock_index, mock_chunker):
        """基本的な溶解。"""
        count = field.dissolve("# テスト\nコンテンツ", source="session", session_id="s1")
        assert count == 5
        mock_chunker.chunk.assert_called_once()
        mock_index.add_chunks.assert_called_once()
        call_args = mock_index.add_chunks.call_args
        assert call_args.kwargs["source"] == "session"
        assert call_args.kwargs["session_id"] == "s1"

    def test_dissolve_empty_text(self, field, mock_index):
        """空テキストの溶解。"""
        count = field.dissolve("")
        assert count == 0
        mock_index.add_chunks.assert_not_called()

    def test_dissolve_whitespace_only(self, field, mock_index):
        """空白のみテキストの溶解。"""
        count = field.dissolve("   \n  ")
        assert count == 0
        mock_index.add_chunks.assert_not_called()

    def test_dissolve_with_parent_id(self, field, mock_index, mock_chunker):
        """parent_id の外部上書き。"""
        field.dissolve("# テスト\nコンテンツ", parent_id="custom_parent")
        chunks_passed = mock_index.add_chunks.call_args.kwargs["chunks"]
        for chunk in chunks_passed:
            assert chunk["parent_id"] == "custom_parent"

    def test_dissolve_no_chunks_produced(self, field, mock_index, mock_chunker):
        """チャンカーが空リストを返す場合。"""
        mock_chunker.chunk.return_value = []
        count = field.dissolve("何か")
        assert count == 0
        mock_index.add_chunks.assert_not_called()


class TestRecall:
    """想起テスト。"""

    def test_recall_exploit(self, field):
        """Exploit モードの想起。"""
        results = field.recall("FEP", mode="exploit", limit=2)
        assert len(results) <= 2
        # スコア降順
        if len(results) >= 2:
            assert results[0]["_field_score"] >= results[1]["_field_score"]

    def test_recall_explore(self, field):
        """Explore モードの想起。"""
        results = field.recall("FEP", mode="explore", limit=10)
        # 低密度チャンクが上位に来る
        for r in results:
            assert "_epistemic_value" in r
            assert "_pragmatic_value" in r

    def test_recall_exploit_with_source_filter(self, field):
        """ソースフィルタ付き Exploit。"""
        results = field.recall("FEP", mode="exploit", source_filter="session")
        for r in results:
            assert r.get("source") == "session"

    def test_recall_exploit_with_session_filter(self, field):
        """セッションフィルタ付き Exploit。"""
        results = field.recall("FEP", mode="exploit", session_filter="session_abc")
        for r in results:
            assert r.get("session_id") == "session_abc"

    def test_recall_default_mode(self, field):
        """デフォルトモードは exploit。"""
        results = field.recall("FEP")
        # exploit のスコアがあることを確認
        for r in results:
            assert "_field_score" in r
            assert "_epistemic_value" not in r  # explore 固有フィールドはない


class TestDensity:
    """密度更新テスト。"""

    def test_update_density(self, field, mock_index):
        """密度更新。"""
        count = field.update_density(k=5)
        assert count == 50
        mock_index.update_density.assert_called_once_with(k=5)


class TestStats:
    """統計・健全性テスト。"""

    def test_stats(self, field):
        """統計情報の取得。"""
        stats = field.stats()
        assert stats["total"] == 50
        assert stats["chunker_mode"] == "markdown"

    def test_health_growing(self, field):
        """健全性チェック (growing)。"""
        health = field.health()
        assert health["status"] == "sparse"  # total=50 < 100

    def test_health_empty(self, field, mock_index):
        """健全性チェック (empty)。"""
        mock_index.stats.return_value = {"total": 0, "sources": {}}
        health = field.health()
        assert health["status"] == "empty"

    def test_health_error(self, field, mock_index):
        """健全性チェック (error)。"""
        mock_index.stats.side_effect = Exception("DB error")
        health = field.health()
        assert health["status"] == "error"


class TestApplyFilters:
    """フィルタテスト。"""

    def test_no_filter(self):
        """フィルタなし。"""
        results = [{"source": "session"}, {"source": "handoff"}]
        filtered = HypheField._apply_filters(results)
        assert len(filtered) == 2

    def test_source_filter(self):
        """ソースフィルタ。"""
        results = [{"source": "session"}, {"source": "handoff"}]
        filtered = HypheField._apply_filters(results, source_filter="session")
        assert len(filtered) == 1
        assert filtered[0]["source"] == "session"

    def test_session_filter(self):
        """セッションフィルタ。"""
        results = [
            {"session_id": "s1", "source": "session"},
            {"session_id": "s2", "source": "session"},
        ]
        filtered = HypheField._apply_filters(results, session_filter="s1")
        assert len(filtered) == 1
