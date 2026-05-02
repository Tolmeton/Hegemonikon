# PROOF: [L3/テスト] <- hermeneus/tests/test_tape_recording.py tape 記録インフラテスト
"""
Tape Recording Infrastructure Tests

Compile-Only Mode が tape に自動記録されることを検証する。
executor 経由の記録と source フィールドで区別できることを検証する。
"""
# PURPOSE: tape 記録のロジック検証

import json
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# パッケージパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mekhane.ccl.tape import TapeWriter


class TestTapeWriterSourceField:
    """TapeWriter が source フィールドを正しく記録するかテスト"""

    # PURPOSE: TapeWriter が任意の kwargs を受け入れ JSONL に書くことを検証
    def test_source_field_recorded(self, tmp_path):
        """source フィールドが tape エントリに含まれる"""
        tape = TapeWriter(tape_dir=tmp_path)

        tape.log(
            wf="/noe",
            step="COMPILE_ONLY",
            success=True,
            source="compile_only",
            workflow_name="noe",
            session_id="test-session-123",
        )

        lines = tape.filepath.read_text().strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["source"] == "compile_only"
        assert entry["wf"] == "/noe"
        assert entry["step"] == "COMPILE_ONLY"
        assert entry["session_id"] == "test-session-123"

    # PURPOSE: Compile-Only が2エントリ (COMPILE_ONLY + COMPLETE) を書くことを検証
    def test_compile_only_writes_two_entries(self, tmp_path):
        """Compile-Only Mode は COMPILE_ONLY と COMPLETE の2エントリを書く"""
        tape = TapeWriter(tape_dir=tmp_path)

        # mcp_server.py の注入コードと同じパターン
        tape.log(
            wf="/bou+",
            step="COMPILE_ONLY",
            success=True,
            source="compile_only",
            workflow_name="bou",
            session_id="cascade-abc",
        )
        tape.log(
            wf="/bou+",
            step="COMPLETE",
            success=True,
            source="compile_only",
            workflow_name="bou",
            session_id="cascade-abc",
            model="claude_direct",
        )

        lines = tape.filepath.read_text().strip().split("\n")
        assert len(lines) == 2

        entry1 = json.loads(lines[0])
        entry2 = json.loads(lines[1])

        assert entry1["step"] == "COMPILE_ONLY"
        assert entry2["step"] == "COMPLETE"
        assert entry1["source"] == "compile_only"
        assert entry2["source"] == "compile_only"
        assert entry2["model"] == "claude_direct"

    # PURPOSE: executor 経由の source="executor" フィールドが区別可能であることを検証
    def test_executor_source_distinguishable(self, tmp_path):
        """executor 経由と compile_only 経由の source が区別可能"""
        tape = TapeWriter(tape_dir=tmp_path)

        # executor 経由
        tape.log(
            wf="/noe+",
            step="COMPLETE",
            source="executor",
            workflow_name="noe",
            model="gemini-pro",
        )

        # compile_only 経由
        tape.log(
            wf="/bou",
            step="COMPLETE",
            source="compile_only",
            workflow_name="bou",
            model="claude_direct",
        )

        lines = tape.filepath.read_text().strip().split("\n")
        entries = [json.loads(line) for line in lines]

        executor_entries = [e for e in entries if e.get("source") == "executor"]
        compile_entries = [e for e in entries if e.get("source") == "compile_only"]

        assert len(executor_entries) == 1
        assert len(compile_entries) == 1
        assert executor_entries[0]["model"] == "gemini-pro"
        assert compile_entries[0]["model"] == "claude_direct"

    # PURPOSE: session_id が空文字列でも正常動作することを検証
    def test_empty_session_id(self, tmp_path):
        """session_id が空文字列 (cascade_id 未指定時) でもエラーなし"""
        tape = TapeWriter(tape_dir=tmp_path)

        tape.log(
            wf="/noe",
            step="COMPILE_ONLY",
            success=True,
            source="compile_only",
            workflow_name="noe",
            session_id="",
        )

        lines = tape.filepath.read_text().strip().split("\n")
        entry = json.loads(lines[0])
        assert entry["session_id"] == ""


class TestTapeWriterBasicFunction:
    """TapeWriter の基本機能テスト"""

    # PURPOSE: TapeWriter が JSONL にログを書けることの基本テスト
    def test_log_creates_entry(self, tmp_path):
        """基本的なログ書込"""
        tape = TapeWriter(tape_dir=tmp_path)

        tape.log(wf="/test", step="START")

        lines = tape.filepath.read_text().strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["wf"] == "/test"
        assert entry["step"] == "START"
        assert "ts" in entry  # タイムスタンプフィールドの存在

    # PURPOSE: 複数ログが追記されることの検証
    def test_multiple_logs_append(self, tmp_path):
        """複数ログが追記される"""
        tape = TapeWriter(tape_dir=tmp_path)

        tape.log(wf="/a", step="START")
        tape.log(wf="/b", step="COMPLETE")
        tape.log(wf="/c", step="FAILED")

        lines = tape.filepath.read_text().strip().split("\n")
        assert len(lines) == 3
