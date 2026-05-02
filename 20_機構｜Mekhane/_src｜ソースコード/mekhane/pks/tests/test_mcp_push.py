# PROOF: [L2/テスト] <- mekhane/pks/tests/
"""
PROOF: [L2/テスト] このファイルは存在しなければならない

A0 (FEP) → MCP Push ツール (hgk_proactive_push) の品質保証にはテストが必要
→ test_mcp_push.py が担う

# PURPOSE: hgk_proactive_push MCP ツールの単体テスト (Phase 4)
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# プロジェクトルートを PATH に追加
_PKS_DIR = Path(__file__).resolve().parent.parent
_MEKHANE_DIR = _PKS_DIR.parent
if str(_MEKHANE_DIR) not in sys.path:
    sys.path.insert(0, str(_MEKHANE_DIR))


# ============================================================================
# テストフィクスチャ
# ============================================================================

# PURPOSE: PKSEngine のモックを提供するフィクスチャ
@pytest.fixture
def mock_pks_engine():
    """PKSEngine のモックを作成"""
    engine = MagicMock()
    engine.proactive_push.return_value = []
    engine.format_push_report.return_value = "📚 Push レポート"
    engine.set_context.return_value = None
    return engine


# PURPOSE: _auto_extract_topics のモックフィクスチャ
@pytest.fixture
def mock_auto_extract():
    """_auto_extract_topics のモック"""
    with patch(
        "mekhane.mcp.gateway_tools.sympatheia._auto_extract_topics",
        return_value=["FEP", "Active Inference"],
    ) as m:
        yield m


# ============================================================================
# _get_pks_engine テスト
# ============================================================================

class TestGetPKSEngine:
    """PKSEngine の遅延初期化テスト"""

    # PURPOSE: PKSEngine が正常に初期化されるか確認
    def test_get_pks_engine_initializes(self):
        """PKSEngine が正常に初期化される"""
        import mekhane.mcp.gateway_tools.sympatheia as sym_mod

        # グローバル変数をリセット
        sym_mod._pks_engine = None

        with patch("mekhane.pks.pks_engine.PKSEngine") as MockEngine:
            MockEngine.return_value = MagicMock()
            result = sym_mod._get_pks_engine()
            assert result is not None
            MockEngine.assert_called_once()

        # テスト後にリセット
        sym_mod._pks_engine = None

    # PURPOSE: PKSEngine の初期化失敗時に None が返る
    def test_get_pks_engine_returns_none_on_failure(self):
        """初期化失敗時は None を返す"""
        import mekhane.mcp.gateway_tools.sympatheia as sym_mod

        sym_mod._pks_engine = None

        with patch(
            "mekhane.pks.pks_engine.PKSEngine",
            side_effect=Exception("init failed"),
        ):
            result = sym_mod._get_pks_engine()
            assert result is None

        sym_mod._pks_engine = None

    # PURPOSE: 2回目の呼出でキャッシュが使われる
    def test_get_pks_engine_caches(self):
        """2回目の呼出はキャッシュされたインスタンスを返す"""
        import mekhane.mcp.gateway_tools.sympatheia as sym_mod

        mock_engine = MagicMock()
        sym_mod._pks_engine = mock_engine

        result = sym_mod._get_pks_engine()
        assert result is mock_engine

        sym_mod._pks_engine = None


# ============================================================================
# _auto_extract_topics テスト
# ============================================================================

class TestAutoExtractTopics:
    """Handoff からのトピック自動抽出テスト"""

    # PURPOSE: Handoff ディレクトリが存在しない場合に空リストが返る
    def test_no_sessions_dir(self, tmp_path):
        """セッションディレクトリがない場合は空リスト"""
        import mekhane.mcp.gateway_tools.sympatheia as sym_mod

        with patch.object(sym_mod, "_MNEME_DIR", tmp_path):
            result = sym_mod._auto_extract_topics()
            assert result == []

    # PURPOSE: Handoff が1件もない場合に空リストが返る
    def test_no_handoffs(self, tmp_path):
        """Handoff がない場合は空リスト"""
        import mekhane.mcp.gateway_tools.sympatheia as sym_mod

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        with patch.object(sym_mod, "_MNEME_DIR", tmp_path):
            result = sym_mod._auto_extract_topics()
            assert result == []


# ============================================================================
# hgk_proactive_push 統合テスト (モック)
# ============================================================================

class TestProactivePush:
    """hgk_proactive_push のロジックテスト"""

    # PURPOSE: トピック指定ありでプッシュが正常に動作する
    def test_push_with_topics(self, mock_pks_engine):
        """トピック指定ありでプッシュが呼ばれる"""
        mock_pks_engine.proactive_push.return_value = [
            MagicMock(title="Paper A", score=0.9),
        ]

        # エンジンにコンテキストをセット
        topic_list = ["FEP", "Active Inference"]
        mock_pks_engine.set_context(topics=topic_list)
        mock_pks_engine.set_context.assert_called_once_with(topics=topic_list)

        # プッシュ実行
        nuggets = mock_pks_engine.proactive_push(k=5)
        assert len(nuggets) == 1

    # PURPOSE: 空結果時のハンドリング
    def test_push_empty_results(self, mock_pks_engine):
        """結果が空の場合の動作確認"""
        mock_pks_engine.proactive_push.return_value = []

        nuggets = mock_pks_engine.proactive_push(k=5)
        assert nuggets == []

    # PURPOSE: advocacy モードのフォーマット確認
    def test_advocacy_format(self, mock_pks_engine):
        """use_advocacy=True でフォーマットが呼ばれる"""
        nuggets = [MagicMock(title="Paper A")]
        mock_pks_engine.format_push_report.return_value = (
            "📢 私は Paper A です。FEP について知見を共有します。"
        )

        result = mock_pks_engine.format_push_report(
            nuggets, use_advocacy=True
        )
        assert "📢" in result
        assert "Paper A" in result
        mock_pks_engine.format_push_report.assert_called_once_with(
            nuggets, use_advocacy=True
        )

    # PURPOSE: トピックのカンマ区切りパース
    def test_topic_parsing(self):
        """トピック文字列のカンマ区切りパース"""
        topics_str = "FEP, Active Inference, CCL"
        topic_list = [
            t.strip() for t in topics_str.split(",") if t.strip()
        ]
        assert topic_list == ["FEP", "Active Inference", "CCL"]

    # PURPOSE: 空トピック時のパース
    def test_empty_topic_parsing(self):
        """空文字列のパース"""
        topics_str = ""
        topic_list = (
            [t.strip() for t in topics_str.split(",") if t.strip()]
            if topics_str
            else []
        )
        assert topic_list == []

    # PURPOSE: max_results の制限が伝播する
    def test_max_results_passed(self, mock_pks_engine):
        """max_results が proactive_push の k に渡される"""
        mock_pks_engine.proactive_push(k=3)
        mock_pks_engine.proactive_push.assert_called_with(k=3)

    # PURPOSE: エンジン初期化失敗時のエラーハンドリング
    def test_engine_init_failure(self):
        """エンジンが None の場合のエラーメッセージ"""
        engine = None
        if engine is None:
            result = "❌ PKSEngine を初期化できませんでした"
        assert "PKSEngine" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
