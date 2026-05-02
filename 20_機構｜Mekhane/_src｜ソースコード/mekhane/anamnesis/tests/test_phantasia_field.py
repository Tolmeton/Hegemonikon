# PROOF: mekhane/anamnesis/tests/test_phantasia_field.py
# PURPOSE: anamnesis モジュールの phantasia_field に対するテスト
"""PhantasiaField テスト — 溶解・想起・密度更新のユニットテスト。

Mock を利用して GnosisIndex と Chunker を差し替えることで、
外部 API (Vertex AI Embedding) への依存なしにテストする。
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from mekhane.anamnesis.phantasia_field import PhantasiaField


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
    # テキストは purify_chunks の min_text_len=30 をクリアする長さが必要
    chunker.chunk.return_value = [
        {"id": "c1", "parent_id": "doc1", "text": "テスト1。FEP は自由エネルギー原理であり、認知の基盤理論を提供する。", "section_title": "概要", "chunk_index": 0},
        {"id": "c2", "parent_id": "doc1", "text": "テスト2。能動推論は行動によって環境を変え、予測誤差を最小化する手法である。", "section_title": "詳細", "chunk_index": 1},
        {"id": "c3", "parent_id": "doc1", "text": "テスト3。マルコフブランケットは内部と外部の境界を定義する統計的概念である。", "section_title": "結論", "chunk_index": 2},
    ]
    return chunker


@pytest.fixture
def field(mock_index, mock_chunker):
    """PhantasiaField インスタンス (モック注入)。"""
    f = PhantasiaField(chunker_mode="markdown")
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
        filtered = PhantasiaField._apply_filters(results)
        assert len(filtered) == 2

    def test_source_filter(self):
        """ソースフィルタ。"""
        results = [{"source": "session"}, {"source": "handoff"}]
        filtered = PhantasiaField._apply_filters(results, source_filter="session")
        assert len(filtered) == 1
        assert filtered[0]["source"] == "session"

    def test_session_filter(self):
        """セッションフィルタ。"""
        results = [
            {"session_id": "s1", "source": "session"},
            {"session_id": "s2", "source": "session"},
        ]
        filtered = PhantasiaField._apply_filters(results, session_filter="s1")
        assert len(filtered) == 1


# ── Gap 2: recall での rich metrics 活用テスト ──────────────────


class TestExpandMetadata:
    """_expand_metadata のテスト。"""

    def test_expand_from_json_string(self):
        """metadata_json (JSON 文字列) から coherence/drift/efe を展開する。"""
        from mekhane.anamnesis.phantasia_field import _expand_metadata

        results = [
            {
                "id": "c1",
                "metadata_json": json.dumps({"coherence": 0.85, "drift": 0.12, "efe": 0.67}),
            }
        ]
        _expand_metadata(results)
        assert results[0]["coherence"] == 0.85
        assert results[0]["drift"] == 0.12
        assert results[0]["efe"] == 0.67

    def test_no_overwrite_existing(self):
        """既にトップレベルに存在するフィールドは上書きしない。"""
        from mekhane.anamnesis.phantasia_field import _expand_metadata

        results = [
            {
                "id": "c1",
                "coherence": 0.99,  # 既存値
                "metadata_json": json.dumps({"coherence": 0.50}),
            }
        ]
        _expand_metadata(results)
        assert results[0]["coherence"] == 0.99  # 上書きされていない

    def test_empty_metadata(self):
        """空の metadata_json は何もしない。"""
        from mekhane.anamnesis.phantasia_field import _expand_metadata

        results = [{"id": "c1", "metadata_json": "{}"}]
        _expand_metadata(results)
        assert "coherence" not in results[0]

    def test_missing_metadata(self):
        """metadata_json がない場合も安全。"""
        from mekhane.anamnesis.phantasia_field import _expand_metadata

        results = [{"id": "c1"}]
        _expand_metadata(results)
        assert "coherence" not in results[0]


class TestRecallWithStoredPrecision:
    """DB に保存された precision を recall が活用するテスト。"""

    def test_exploit_uses_stored_precision(self, field, mock_index):
        """_recall_exploit が DB の precision を density 再計算より優先する。"""
        # mock_index.search は precision=0.8/0.6/0.9 を含むチャンクを返す
        results = field.recall("FEP", mode="exploit", limit=10)
        # precision がそのまま保持されているか確認
        for r in results:
            # DB の precision が 0.5 (デフォルト) でなければ直接使用される
            assert "precision" in r
            assert r["precision"] in [0.8, 0.6, 0.9]

    def test_exploit_fallback_to_density(self, field, mock_index):
        """precision=0.5 (デフォルト) の場合は density から再計算する。"""
        mock_index.search.return_value = [
            {
                "id": "chunk_fb",
                "source": "session",
                "title": "テスト",
                "content": "フォールバックテスト用のチャンク",
                "_distance": 0.2,
                "precision": 0.5,  # デフォルト = 未計算
                "density": 0.7,
            }
        ]
        results = field.recall("テスト", mode="exploit", limit=10)
        assert len(results) == 1
        # density=0.7 → precision = 0.7² × (3 - 2×0.7) = 0.49 × 1.6 = 0.784
        from mekhane.anamnesis.phantasia_field import compute_precision_from_density
        expected = compute_precision_from_density(0.7)
        assert abs(results[0]["precision"] - expected) < 0.01


class TestRefineWithDrift:
    """_refine_results の drift フィルタテスト。"""

    def test_high_drift_filtered(self):
        """drift > max_drift のチャンクが除去される。"""
        results = [
            {"id": "c1", "_distance": 0.1, "content": "低ドリフトの安定チャンク", "drift": 0.3},
            {"id": "c2", "_distance": 0.2, "content": "高ドリフトの不安定チャンク", "drift": 0.9},
        ]
        refined = PhantasiaField._refine_results(results, max_drift=0.85)
        assert len(refined) == 1
        assert refined[0]["id"] == "c1"

    def test_no_drift_passes(self):
        """drift がないチャンクはフィルタされない。"""
        results = [
            {"id": "c1", "_distance": 0.1, "content": "ドリフト情報なしのチャンク"},
        ]
        refined = PhantasiaField._refine_results(results, max_drift=0.85)
        assert len(refined) == 1

    def test_drift_at_threshold(self):
        """drift == max_drift のチャンクはフィルタされない (超過のみ)。"""
        results = [
            {"id": "c1", "_distance": 0.1, "content": "閾値ちょうどのドリフトチャンク", "drift": 0.85},
        ]
        refined = PhantasiaField._refine_results(results, max_drift=0.85)
        assert len(refined) == 1
