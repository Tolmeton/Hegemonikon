"""GAP-2 統合テスト: PhantasiaField ⇔ PhantazeinStore 連携。

テスト対象:
1. PhantazeinStore の phantasia_* テーブルと新規メソッド
2. PhantasiaPipeline の on_dissolve コールバック
"""
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── PhantazeinStore テスト ────────────────────────────────────


class TestPhantasiaDissolves:
    """phantasia_dissolves テーブルと record_dissolve/get_dissolve_history メソッド。"""

    @pytest.fixture(autouse=True)
    def setup_store(self, tmp_path: Path):
        """テスト用の一時 DB で PhantazeinStore を初期化。"""
        from mekhane.symploke.phantazein_store import PhantazeinStore

        self.store = PhantazeinStore(db_path=tmp_path / "test.db")
        yield
        self.store.close()

    def test_record_dissolve_basic(self):
        """基本的な溶解イベントの記録と取得。"""
        self.store.record_dissolve(
            session_id="sess-001",
            chunk_count=5,
            total_chars=1000,
            source_type="session",
        )
        history = self.store.get_dissolve_history()
        assert len(history) == 1
        assert history[0]["session_id"] == "sess-001"
        assert history[0]["chunk_count"] == 5
        assert history[0]["total_chars"] == 1000
        assert history[0]["source_type"] == "session"

    def test_record_dissolve_multiple_sessions(self):
        """複数セッションの溶解記録。"""
        self.store.record_dissolve("sess-001", 3, 500)
        self.store.record_dissolve("sess-002", 7, 1500)
        self.store.record_dissolve("sess-003", 2, 300)

        # 全件取得 (新しい順)
        history = self.store.get_dissolve_history()
        assert len(history) == 3
        # 最新が先頭
        assert history[0]["session_id"] == "sess-003"

    def test_get_dissolve_history_filter_by_session(self):
        """セッション ID でフィルタリング。"""
        self.store.record_dissolve("sess-001", 3, 500)
        self.store.record_dissolve("sess-002", 7, 1500)
        self.store.record_dissolve("sess-001", 5, 800)

        # sess-001 のみ
        history = self.store.get_dissolve_history(session_id="sess-001")
        assert len(history) == 2
        for row in history:
            assert row["session_id"] == "sess-001"

    def test_get_dissolve_history_limit(self):
        """limit パラメータの動作。"""
        for i in range(10):
            self.store.record_dissolve(f"sess-{i:03d}", i + 1, (i + 1) * 100)

        history = self.store.get_dissolve_history(limit=3)
        assert len(history) == 3

    def test_record_dissolve_defaults(self):
        """デフォルト値 (total_chars=0, source_type='session') の確認。"""
        self.store.record_dissolve("sess-001", 5)
        history = self.store.get_dissolve_history()
        assert history[0]["total_chars"] == 0
        assert history[0]["source_type"] == "session"


class TestPhantasiaFieldStats:
    """phantasia_field_stats テーブルと record_field_stats/get_field_stats メソッド。"""

    @pytest.fixture(autouse=True)
    def setup_store(self, tmp_path: Path):
        from mekhane.symploke.phantazein_store import PhantazeinStore

        self.store = PhantazeinStore(db_path=tmp_path / "test.db")
        yield
        self.store.close()

    def test_record_field_stats_basic(self):
        """基本的なフィールド統計の記録と取得。"""
        self.store.record_field_stats(
            total_chunks=100,
            total_tables=3,
            avg_density=0.75,
        )
        stats = self.store.get_field_stats()
        assert len(stats) == 1
        assert stats[0]["total_chunks"] == 100
        assert stats[0]["total_tables"] == 3
        assert abs(stats[0]["avg_density"] - 0.75) < 0.01

    def test_record_field_stats_time_series(self):
        """タイムシリーズとしての統計記録。"""
        self.store.record_field_stats(50, 2, 0.5)
        self.store.record_field_stats(100, 3, 0.65)
        self.store.record_field_stats(150, 3, 0.72)

        stats = self.store.get_field_stats()
        assert len(stats) == 3
        # 最新が先頭
        assert stats[0]["total_chunks"] == 150

    def test_get_field_stats_limit(self):
        """limit パラメータの動作。"""
        for i in range(10):
            self.store.record_field_stats(i * 10, 1, i * 0.1)

        stats = self.store.get_field_stats(limit=5)
        assert len(stats) == 5


class TestPhantasiaTableCreation:
    """phantasia_* テーブルが DDL で正しく作成されるかの検証。"""

    def test_tables_exist(self, tmp_path: Path):
        """3テーブルが CREATE TABLE で作成される。"""
        from mekhane.symploke.phantazein_store import PhantazeinStore

        store = PhantazeinStore(db_path=tmp_path / "test.db")
        # テーブル一覧を取得
        rows = store._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = {row[0] for row in rows}

        assert "phantasia_dissolves" in table_names
        assert "phantasia_field_stats" in table_names
        assert "phantasia_config" in table_names
        store.close()


# ── PhantasiaPipeline on_dissolve コールバックテスト ──────────


class TestOnDissolveCallback:
    """PhantasiaPipeline の on_dissolve コールバック機構。"""

    def test_callback_called_on_successful_dissolve(self):
        """溶解成功時にコールバックが呼ばれる。"""
        from mekhane.anamnesis.phantasia_pipeline import PhantasiaPipeline

        # PhantasiaField のモック
        mock_field = MagicMock()
        mock_field.dissolve.return_value = 3  # 3 チャンク生成

        callback = MagicMock()
        pipeline = PhantasiaPipeline(mock_field, on_dissolve=callback)

        result = pipeline.dissolve(
            text="テストテキスト",
            session_id="sess-001",
        )

        assert result.chunks_count == 3
        callback.assert_called_once_with("sess-001", 3, len("テストテキスト"))

    def test_callback_not_called_when_none(self):
        """on_dissolve=None の場合はコールバックなし (回帰テスト)。"""
        from mekhane.anamnesis.phantasia_pipeline import PhantasiaPipeline

        mock_field = MagicMock()
        mock_field.dissolve.return_value = 3

        # コールバックなし — 例外が出ないことを確認
        pipeline = PhantasiaPipeline(mock_field, on_dissolve=None)
        result = pipeline.dissolve(text="テスト", session_id="sess-001")
        assert result.chunks_count == 3

    def test_callback_failure_does_not_break_dissolve(self):
        """コールバック失敗時も溶解結果は正常に返る。"""
        from mekhane.anamnesis.phantasia_pipeline import PhantasiaPipeline

        mock_field = MagicMock()
        mock_field.dissolve.return_value = 5

        # 例外を投げるコールバック
        def failing_callback(sid, count, chars):
            raise RuntimeError("コールバック失敗テスト")

        pipeline = PhantasiaPipeline(mock_field, on_dissolve=failing_callback)
        result = pipeline.dissolve(text="テストデータ", session_id="sess-001")

        # 溶解自体は成功
        assert result.chunks_count == 5
        assert result.session_id == "sess-001"

    def test_callback_receives_correct_total_chars(self):
        """コールバックに正しい total_chars が渡される。"""
        from mekhane.anamnesis.phantasia_pipeline import PhantasiaPipeline

        mock_field = MagicMock()
        mock_field.dissolve.return_value = 2

        received = {}

        def capture_callback(sid, count, chars):
            received["session_id"] = sid
            received["count"] = count
            received["chars"] = chars

        text = "これは200文字のテストテキストです" * 10
        pipeline = PhantasiaPipeline(mock_field, on_dissolve=capture_callback)
        pipeline.dissolve(text=text, session_id="test-sess")

        assert received["chars"] == len(text)
        assert received["count"] == 2
        assert received["session_id"] == "test-sess"


# ── 統合テスト: Store + Pipeline コールバック ──────────────────


class TestStoreCallbackIntegration:
    """PhantazeinStore.record_dissolve を Pipeline のコールバックとして使用するE2Eテスト。"""

    def test_pipeline_dissolve_records_to_store(self, tmp_path: Path):
        """Pipeline の溶解が Store に自動記録される (E2E)。"""
        from mekhane.symploke.phantazein_store import PhantazeinStore
        from mekhane.anamnesis.phantasia_pipeline import PhantasiaPipeline

        store = PhantazeinStore(db_path=tmp_path / "test.db")
        mock_field = MagicMock()
        mock_field.dissolve.return_value = 4

        pipeline = PhantasiaPipeline(
            mock_field,
            on_dissolve=store.record_dissolve,
        )

        pipeline.dissolve(text="E2Eテスト用テキスト", session_id="e2e-sess-001")

        history = store.get_dissolve_history()
        assert len(history) == 1
        assert history[0]["session_id"] == "e2e-sess-001"
        assert history[0]["chunk_count"] == 4
        assert history[0]["total_chars"] == len("E2Eテスト用テキスト")
        store.close()
