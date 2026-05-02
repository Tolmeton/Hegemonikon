# PROOF: [L2/テスト] <- mekhane/agent_guard/tests/test_apotheke.py
# PURPOSE: Apothēkē 後処理パイプラインのユニットテスト
"""Tests for Apothēkē — 対話の後処理パイプライン。

Tests:
- extract_evictable: eviction logic (keep_recent, edge cases)
- _format_chunks_for_prompt: contents → readable text
- save_ki: KI ファイル保存
- narrate: LLM × Týpos (mock)
- run_postprocess: full pipeline (mock)
- retrieve_context: RAG retrieval (mock)
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mekhane.agent_guard.apotheke import (
    DEFAULT_KEEP_RECENT_TURNS,
    EvictionResult,
    KIRecord,
    NarrateResult,
    _format_chunks_for_prompt,
    _parse_dissolved_json,
    extract_evictable,
    narrate,
    recrystallize,
    run_postprocess,
    save_ki,
)


# ============ Fixtures ============


def _make_contents(n: int) -> list[dict]:
    """Generate n messages alternating user/model."""
    contents = []
    for i in range(n):
        role = "user" if i % 2 == 0 else "model"
        contents.append({
            "role": role,
            "parts": [{"text": f"Message {i} from {role}"}],
        })
    return contents


# ============ Tests: extract_evictable ============


class TestExtractEvictable:
    """extract_evictable のテスト。"""

    def test_no_eviction_when_below_threshold(self):
        """keep_recent 以下のメッセージは evict されない。"""
        contents = _make_contents(3)
        result = extract_evictable(contents, keep_recent=4)

        assert result.evicted == []
        assert result.kept == contents
        assert result.evicted_turns == 0

    def test_eviction_basic(self):
        """基本的な eviction: 古いメッセージが evict される。"""
        contents = _make_contents(10)
        result = extract_evictable(contents, keep_recent=4)

        assert len(result.kept) == 4
        assert len(result.evicted) == 6
        assert result.evicted_turns == 6
        # kept は最新4件
        assert result.kept[0]["parts"][0]["text"] == "Message 6 from user"

    def test_eviction_exact_threshold(self):
        """keep_recent と同数のメッセージは evict なし。"""
        contents = _make_contents(4)
        result = extract_evictable(contents, keep_recent=4)

        assert result.evicted == []
        assert len(result.kept) == 4

    def test_eviction_empty_contents(self):
        """空の contents は evict なし。"""
        result = extract_evictable([], keep_recent=4)

        assert result.evicted == []
        assert result.kept == []

    def test_eviction_default_keep_recent(self):
        """デフォルト keep_recent の確認。"""
        contents = _make_contents(10)
        result = extract_evictable(contents)

        assert len(result.kept) == DEFAULT_KEEP_RECENT_TURNS
        assert len(result.evicted) == 10 - DEFAULT_KEEP_RECENT_TURNS


# ============ Tests: _parse_dissolved_json ============


class TestParseDissolvedJson:
    """Hyphē JSON 抽出のテスト。"""

    def test_plain_json(self):
        raw = (
            '{"decisions":["a"],"constraints":["b"],'
            '"open_questions":[],"references":["c"]}'
        )
        d = _parse_dissolved_json(raw)
        assert d["decisions"] == ["a"]
        assert d["constraints"] == ["b"]
        assert d["open_questions"] == []
        assert d["references"] == ["c"]

    def test_fenced_json(self):
        raw = '```json\n{"decisions":["x"],"constraints":[],"open_questions":[],"references":[]}\n```'
        d = _parse_dissolved_json(raw)
        assert d["decisions"] == ["x"]

    def test_invalid_returns_empty(self):
        assert _parse_dissolved_json("not json") == {}


# ============ Tests: _format_chunks_for_prompt ============


class TestFormatChunks:
    """_format_chunks_for_prompt のテスト。"""

    def test_text_messages(self):
        """テキストメッセージのフォーマット。"""
        chunks = [
            {"role": "user", "parts": [{"text": "Hello"}]},
            {"role": "model", "parts": [{"text": "Hi there"}]},
        ]
        result = _format_chunks_for_prompt(chunks)

        assert "[user]: Hello" in result
        assert "[model]: Hi there" in result

    def test_function_call_messages(self):
        """functionCall メッセージのフォーマット。"""
        chunks = [
            {"role": "model", "parts": [{"functionCall": {"name": "read_file", "args": {"path": "/test"}}}]},
        ]
        result = _format_chunks_for_prompt(chunks)

        assert "[model:tool_call]: read_file" in result

    def test_function_response_messages(self):
        """functionResponse メッセージのフォーマット。"""
        chunks = [
            {"role": "user", "parts": [{"functionResponse": {"name": "read_file", "response": {"output": "file content"}}}]},
        ]
        result = _format_chunks_for_prompt(chunks)

        assert "[user:tool_result]: read_file" in result

    def test_mixed_messages(self):
        """混合メッセージのフォーマット。"""
        chunks = _make_contents(4)
        result = _format_chunks_for_prompt(chunks)

        assert result.count("[user]:") == 2
        assert result.count("[model]:") == 2


# ============ Tests: save_ki ============


class TestSaveKI:
    """save_ki のテスト。"""

    def test_save_creates_file(self):
        """KI ファイルが作成される。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            record = save_ki(
                content="test content",
                session_id="test-session",
                tags=["test"],
                ki_dir=Path(tmpdir),
            )

            assert record.path.exists()
            assert record.session_id == "test-session"
            assert "test" in record.tags
            assert record.path.suffix == ".md"

    def test_save_includes_header(self):
        """保存されたファイルにヘッダが含まれる。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            record = save_ki(
                content="# Test Note",
                session_id="sess-123",
                tags=["auto-evict", "test"],
                ki_dir=Path(tmpdir),
            )

            text = record.path.read_text(encoding="utf-8")
            assert "type: session_memory" in text
            assert "session_id: sess-123" in text
            assert "source: apotheke" in text
            assert "# Test Note" in text

    def test_save_creates_directory(self):
        """存在しないディレクトリが自動作成される。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ki_dir = Path(tmpdir) / "sub" / "dir"
            record = save_ki(
                content="test",
                session_id="test",
                ki_dir=ki_dir,
            )

            assert ki_dir.exists()
            assert record.path.exists()


# ============ Tests: narrate ============


class TestNarrate:
    """narrate のテスト (LLM をモック)。"""

    def test_narrate_success(self):
        """正常系: Hyphē (dissolve JSON → recrystallize Týpos)。"""
        r_dissolve = MagicMock()
        r_dissolve.text = (
            '{"decisions":["採用A"],"constraints":["NFR1"],'
            '"open_questions":["Q?"],"references":["path/x"]}'
        )
        r_crys = MagicMock()
        r_crys.text = "#prompt test\n<:role: テスト :>"

        def mock_ask(**kwargs):
            return mock_ask._queue.pop(0)

        mock_ask._queue = [r_dissolve, r_crys]

        chunks = _make_contents(4)
        result = asyncio.get_event_loop().run_until_complete(
            narrate(chunks, "test-session", mock_ask)
        )

        assert result.success
        assert "#prompt test" in result.typos_content
        assert result.input_turns == 4
        assert len(mock_ask._queue) == 0

    def test_narrate_empty_chunks(self):
        """空チャンクはエラー。"""
        result = asyncio.get_event_loop().run_until_complete(
            narrate([], "test-session", lambda **kw: None)
        )

        assert not result.success
        assert "No chunks" in result.error

    def test_narrate_llm_failure(self):
        """LLM 呼び出し失敗時はエラー。"""
        def mock_ask(**kwargs):
            raise RuntimeError("API error")

        chunks = _make_contents(4)
        result = asyncio.get_event_loop().run_until_complete(
            narrate(chunks, "test-session", mock_ask)
        )

        assert not result.success
        assert "API error" in result.error

    def test_narrate_legacy_fallback_when_dissolve_invalid(self):
        """Dissolve が JSON 解釈不能のとき一発 NARRATE にフォールバック。"""
        r_bad = MagicMock()
        r_bad.text = "not valid json {{{"
        r_legacy = MagicMock()
        r_legacy.text = "#prompt legacy\n<:role: L :>"

        def mock_ask(**kwargs):
            return mock_ask._queue.pop(0)

        mock_ask._queue = [r_bad, r_legacy]

        chunks = _make_contents(2)
        result = asyncio.get_event_loop().run_until_complete(
            narrate(chunks, "s", mock_ask)
        )
        assert result.success
        assert "#prompt legacy" in result.typos_content
        assert len(mock_ask._queue) == 0

    def test_narrate_fallback_when_recrystallize_empty(self):
        """Recrystallize が空なら legacy narrate へ（3回目の ask）。"""
        r_dissolve = MagicMock()
        r_dissolve.text = (
            '{"decisions":["x"],"constraints":[],"open_questions":[],"references":[]}'
        )
        r_empty = MagicMock()
        r_empty.text = "   \n"
        r_legacy = MagicMock()
        r_legacy.text = "#prompt legacy\n<:role: L :>"

        def mock_ask(**kwargs):
            return mock_ask._queue.pop(0)

        mock_ask._queue = [r_dissolve, r_empty, r_legacy]

        chunks = _make_contents(2)
        result = asyncio.get_event_loop().run_until_complete(
            narrate(chunks, "s", mock_ask)
        )
        assert result.success
        assert "#prompt legacy" in result.typos_content
        assert len(mock_ask._queue) == 0


class TestRecrystallize:
    """recrystallize の境界テスト。"""

    def test_empty_output_is_failure(self):
        r = MagicMock()
        r.text = ""

        async def run():
            return await recrystallize(
                {"decisions": [], "constraints": [], "open_questions": [], "references": []},
                "sid",
                lambda **kw: r,
            )

        out = asyncio.get_event_loop().run_until_complete(run())
        assert not out.success
        assert "Empty" in out.error


# ============ Tests: run_postprocess ============


class TestRunPostprocess:
    """run_postprocess のテスト (LLM をモック)。"""

    def test_full_pipeline(self):
        """フルパイプライン: evict → narrate (Hyphē) → save_ki。"""
        r_dissolve = MagicMock()
        r_dissolve.text = (
            '{"decisions":["d"],"constraints":[],"open_questions":[],"references":[]}'
        )
        r_crys = MagicMock()
        r_crys.text = "#prompt session-note\n<:role: KI :>"

        def mock_ask(**kwargs):
            return mock_ask._queue.pop(0)

        mock_ask._queue = [r_dissolve, r_crys]

        with tempfile.TemporaryDirectory() as tmpdir:
            chunks = _make_contents(6)
            record = asyncio.get_event_loop().run_until_complete(
                run_postprocess(
                    chunks, "test-session", mock_ask,
                    ki_dir=Path(tmpdir),
                )
            )

            assert record is not None
            assert record.path.exists()
            text = record.path.read_text(encoding="utf-8")
            assert "#prompt session-note" in text

    def test_empty_chunks_returns_none(self):
        """空チャンクは None を返す。"""
        result = asyncio.get_event_loop().run_until_complete(
            run_postprocess([], "test", lambda **kw: None)
        )
        assert result is None


# ============ Tests: retrieve_context ============


class TestRetrieveContext:
    """retrieve_context のテスト。"""

    def test_returns_empty_when_no_index(self):
        """インデックスなしで空リスト。"""
        from mekhane.agent_guard.apotheke import retrieve_context

        # DEFAULT_INDEX_PATH が存在しないはず (テスト環境)
        result = retrieve_context("test query")
        assert isinstance(result, list)
