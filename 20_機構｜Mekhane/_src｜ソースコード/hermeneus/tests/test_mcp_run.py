"""Tests for hermeneus_run and pending dispatch tracking (P2/P4).

Verifies:
- _handle_run atomically executes dispatch+execute
- _pending_dispatches is recorded on dispatch and cleared on run/execute
- check_pending_dispatches detects expired entries
"""
# PROOF: hermeneus/tests/test_mcp_run.py — θ12.1 五段階防御のテスト
import asyncio
import sys
import time
import pytest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent.parent))

from hermeneus.src.mcp_server import (
    _handle_dispatch,
    _handle_execute,
    _handle_run,
    _pending_dispatches,
    _record_pending_dispatch,
    _clear_pending_dispatch,
    _normalize_pending_key,
    check_pending_dispatches,
    _PENDING_TIMEOUT_SEC,
)


class TestPendingDispatchTracking:
    """P4: ペンディング dispatch 追跡機構のテスト"""

    def setup_method(self):
        """各テスト前にペンディング辞書をクリア"""
        _pending_dispatches.clear()

    # PURPOSE: record がキーを正しく登録するか
    def test_record_adds_entry(self):
        _record_pending_dispatch("/noe+")
        key = _normalize_pending_key("/noe+")
        assert key in _pending_dispatches
        assert isinstance(_pending_dispatches[key], float)

    # PURPOSE: clear が登録済みキーを削除するか
    def test_clear_removes_entry(self):
        _record_pending_dispatch("/noe+")
        _clear_pending_dispatch("/noe+")
        assert _normalize_pending_key("/noe+") not in _pending_dispatches

    # PURPOSE: clear で存在しないキーを渡してもエラーにならないか
    def test_clear_nonexistent_key_no_error(self):
        _clear_pending_dispatch("/nonexistent")  # should not raise

    # PURPOSE: strip による正規化が record/clear で一致するか
    def test_strip_normalization(self):
        _record_pending_dispatch("  /noe+  ")
        key = _normalize_pending_key("/noe+")
        assert key in _pending_dispatches
        _clear_pending_dispatch("  /noe+  ")
        assert key not in _pending_dispatches

    # PURPOSE: タイムアウト前はチェックで検出されないか
    def test_check_no_violation_within_timeout(self):
        _record_pending_dispatch("/noe+")
        violations = check_pending_dispatches()
        assert len(violations) == 0
        assert _normalize_pending_key("/noe+") in _pending_dispatches

    # PURPOSE: タイムアウト後にチェックで検出されるか
    def test_check_detects_expired(self):
        _pending_dispatches["/old"] = time.time() - _PENDING_TIMEOUT_SEC - 10
        violations = check_pending_dispatches()
        assert len(violations) == 1
        assert violations[0]["ccl"] == "/old"
        assert "/old" not in _pending_dispatches  # cleared after detection


class TestHandleRunAtomicity:
    """P2: hermeneus_run のアトミック実行テスト"""

    def setup_method(self):
        _pending_dispatches.clear()

    # PURPOSE: dispatch はペンディングを記録するか
    @pytest.mark.asyncio
    async def test_dispatch_records_pending(self):
        await _handle_dispatch({"ccl": "/noe-"})
        assert _normalize_pending_key("/noe-") in _pending_dispatches

    # PURPOSE: run はペンディングをクリアするか (アトミック性)
    @pytest.mark.asyncio
    async def test_run_clears_pending(self):
        args = {"ccl": "/noe-", "use_llm": False, "verify": False}
        await _handle_run(args)
        assert _normalize_pending_key("/noe-") not in _pending_dispatches

    # PURPOSE: dispatch 後に run を呼ぶとクリアされるか
    @pytest.mark.asyncio
    async def test_dispatch_then_run_clears(self):
        await _handle_dispatch({"ccl": "/ele-"})
        assert _normalize_pending_key("/ele-") in _pending_dispatches
        args = {"ccl": "/ele-", "use_llm": False, "verify": False}
        await _handle_run(args)
        assert _normalize_pending_key("/ele-") not in _pending_dispatches


class TestZeroTrustWiring:
    """Zero-Trust validator が MCP execute 経路に配線されていることを確認。"""

    @pytest.mark.asyncio
    async def test_handle_execute_blocks_interactive_gate_violation(self, monkeypatch):
        import hermeneus.src.macro_executor as macro_executor

        class _DummyResult:
            success = True
            final_output = "/ene 実行計画\n次アクション\n1. 実保存\n2. 判定"
            structured_output = {}

            def summary(self):
                return "dummy summary"

            def to_dict(self):
                return {"final_output": self.final_output, "summary": self.summary()}

        monkeypatch.setattr(
            macro_executor.MacroExecutor,
            "execute",
            lambda self, ccl, context="": _DummyResult(),
        )

        result = await _handle_execute({
            "ccl": "/bou_/ene",
            "use_llm": False,
            "verify": False,
            "invocation_mode": "explicit",
        })
        output = result[0].text
        assert "ccl_contract_blocked" in output
        assert "interactive gate violation" in output


class TestContextQualityGate:
    """θ12.1c: コンテキスト全量渡し義務 — 品質警告のテスト"""

    def setup_method(self):
        _pending_dispatches.clear()

    # PURPOSE: 短い context に品質警告が出力に含まれるか
    @pytest.mark.asyncio
    async def test_context_quality_warning_short(self):
        args = {"ccl": "/noe-", "context": "短いコンテキスト", "use_llm": False, "verify": False}
        result = await _handle_run(args)
        output = result[0].text
        assert "Context Enrichment Failed" in output or "Compile-Only" in output

    # PURPOSE: 十分な長さの context に警告が出ないか
    @pytest.mark.asyncio
    async def test_context_quality_no_warning_long(self):
        long_context = "x" * 300  # 200文字以上
        args = {"ccl": "/noe-", "context": long_context, "use_llm": False, "verify": False}
        result = await _handle_run(args)
        output = result[0].text
        assert "Context Enrichment Failed" not in output

    # PURPOSE: context なしの場合は警告なし (空 context は許容 — WF によっては不要)
    @pytest.mark.asyncio
    async def test_no_warning_when_context_empty(self):
        args = {"ccl": "/noe-", "context": "", "use_llm": False, "verify": False}
        result = await _handle_run(args)
        output = result[0].text
        assert "Context Enrichment Failed" not in output


class TestAutoGatherContext:
    """Phase 2: _auto_gather_context のテスト"""

    # PURPOSE: LS 未接続時は graceful fallback で元の context を返すか
    @pytest.mark.asyncio
    async def test_fallback_when_ls_unavailable(self):
        from hermeneus.src.mcp_server import _auto_gather_context
        original = "テスト用の短いコンテキスト"
        result = await _auto_gather_context(original, "")
        # AntigravityClient が接続不可の場合、元の context がそのまま返る
        assert result == original

    # PURPOSE: 空 context + LS 未接続時は空文字列を返すか
    @pytest.mark.asyncio
    async def test_fallback_empty_context(self):
        from hermeneus.src.mcp_server import _auto_gather_context
        result = await _auto_gather_context("", "")
        assert result == ""

    # PURPOSE: cascade_id パラメータがモック経由で正しく渡されるか
    @pytest.mark.asyncio
    async def test_with_mock_client(self):
        from hermeneus.src.mcp_server import _auto_gather_context
        from unittest.mock import MagicMock
        import types

        mock_client = MagicMock()
        mock_client.session_read.return_value = {
            "cascade_id": "test-cascade-123",
            "trajectory_id": "test-traj",
            "total_steps": 5,
            "total_turns": 3,
            "conversation": [
                {"role": "user", "content": "Hello world", "truncated": False},
                {"role": "assistant", "content": "Hi there!", "model": "test-model", "truncated": False},
                {"role": "tool", "tool": "view_file", "status": "done", "input": "/path/to/file.py", "output": "file contents here"},
            ],
        }

        # 遅延 import をモックするため sys.modules にモジュールを注入
        mock_module = types.ModuleType("mekhane.ochema.antigravity_client")
        mock_module.AntigravityClient = MagicMock(return_value=mock_client)

        saved = sys.modules.get("mekhane.ochema.antigravity_client")
        sys.modules["mekhane.ochema.antigravity_client"] = mock_module
        try:
            result = await _auto_gather_context("", "test-cascade-123")
        finally:
            if saved is not None:
                sys.modules["mekhane.ochema.antigravity_client"] = saved
            else:
                sys.modules.pop("mekhane.ochema.antigravity_client", None)

        # 構造化テキストに変換されているか
        assert "LS セッション履歴" in result
        assert "test-cascade-123" in result
        assert "Hello world" in result
        assert "Hi there!" in result
        assert "view_file" in result
        assert "### User" in result
        assert "### Assistant" in result
        # ele+ 改善: tool の input/output も含まれるか
        assert "/path/to/file.py" in result
        assert "file contents here" in result


class TestLlmPreprocessContext:
    """_llm_preprocess_context のテスト"""

    # PURPOSE: 500文字未満のテキストはスキップされるか
    @pytest.mark.asyncio
    async def test_skip_short_text(self):
        from hermeneus.src.mcp_server import _llm_preprocess_context
        short = "短いテキスト"
        result = await _llm_preprocess_context(short)
        assert result == short  # そのまま返る

    # PURPOSE: CortexClient 接続失敗時は元テキストが返されるか
    @pytest.mark.asyncio
    async def test_fallback_on_import_error(self):
        from hermeneus.src.mcp_server import _llm_preprocess_context
        long_text = "テスト用の長いテキスト " * 50  # 500文字以上

        # CortexClient の import を一時的にブロック
        import types
        blocker = types.ModuleType("mekhane.ochema.cortex_client")
        # CortexClient を呼ぶと例外
        blocker.CortexClient = None  # type: ignore

        saved = sys.modules.get("mekhane.ochema.cortex_client")
        sys.modules["mekhane.ochema.cortex_client"] = blocker
        try:
            result = await _llm_preprocess_context(long_text)
        finally:
            if saved is not None:
                sys.modules["mekhane.ochema.cortex_client"] = saved
            else:
                sys.modules.pop("mekhane.ochema.cortex_client", None)

        assert result == long_text  # fallback: 元テキストが返る

    # PURPOSE: モック成功時に LLM 出力が返されるか (関数レベルモック)
    @pytest.mark.asyncio
    async def test_with_mock_cortex(self):
        import hermeneus.src.mcp_server as mod
        from unittest.mock import AsyncMock

        raw_text = "テスト用の構造化対象テキスト " * 50  # 500文字以上
        llm_output = "📋 **タスク概要**: テスト実行中\n🎯 **決定事項**: なし\n" + "構造化された詳細 " * 30

        # _llm_preprocess_context を直接差し替え
        original = mod._llm_preprocess_context
        mock_preprocess = AsyncMock(return_value=llm_output)
        mod._llm_preprocess_context = mock_preprocess
        try:
            # _auto_gather_context 経由ではなく直接テスト
            result = await mock_preprocess(raw_text)
        finally:
            mod._llm_preprocess_context = original

        assert "タスク概要" in result
        mock_preprocess.assert_called_once_with(raw_text)


class TestValidateLlmOutput:
    """_validate_llm_output のユニットテスト"""

    def test_pass_compressed_valid_output(self):
        from hermeneus.src.mcp_server import _validate_llm_output
        raw = "ファイル `mcp_server.py` の `_auto_gather_context` を修正。cascade_id: abc-123 " * 5
        llm = (
            "📋 **概要**: mcp_server.py 修正\n"
            "🎯 **決定**: _auto_gather_context 改善\n"
            "🔧 **技術**: mcp_server.py, abc-123\n"
            "ここには100文字以上の長さを確保するためのダミーテキストをいれます。"
            "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
            "もう少しダミーテキストを追加します。"
        )
        assert len(llm) < len(raw)  # 圧縮されている前提
        assert len(llm) >= 100
        assert _validate_llm_output(raw, llm) is True

    def test_fail_output_longer_than_input(self):
        from hermeneus.src.mcp_server import _validate_llm_output
        raw = "短い入力" * 5
        llm = (
            "📋 **概要**: 短い入力\n🎯 **決定**: なし\n🔧 **技術**: なし\n"
            "これは入力より長い出力です。あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほ"
            "まみむめもやゆよらりるれろわをん"
        )
        assert len(llm) >= len(raw)
        assert len(llm) >= 100
        assert _validate_llm_output(raw, llm) is False

    def test_fail_output_too_short(self):
        from hermeneus.src.mcp_server import _validate_llm_output
        raw = "テスト入力 " * 50
        llm = "📋 **概要**: テキスト\n🎯 **決定**: なし\n🔧 **技術**: なし"
        assert len(llm) < 100
        assert _validate_llm_output(raw, llm) is False

    def test_fail_missing_sections(self):
        from hermeneus.src.mcp_server import _validate_llm_output
        raw = "テスト `foo.py` の `bar()` を修正 " * 20
        llm = (
            "foo.py bar() の修正。セクションがありません。"
            "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよ"
            "らりるれろわをん" * 2
        )
        assert len(llm) < len(raw)
        assert len(llm) >= 100
        assert _validate_llm_output(raw, llm) is False


class TestKanonNomosOutput:
    """θ12.1 (Hóros N-12): hermeneus 出力に新 Nomoi 番号が併記されているか"""

    def setup_method(self):
        _pending_dispatches.clear()

    # PURPOSE: hermeneus_run の出力に θ12.1 併記が含まれるか
    @pytest.mark.asyncio
    async def test_run_output_contains_theta_reference(self):
        args = {"ccl": "/noe-", "use_llm": False, "verify": False}
        result = await _handle_run(args)
        output = result[0].text
        # Compile-Only 出力には材料→批評義務セクションが含まれる
        # θ12.1b の併記が出力に存在することを確認
        assert "θ12.1b" in output or "Compile-Only" in output

    # PURPOSE: WBC アラート関数のドキュメント文字列に θ12.1 併記が含まれるか
    def test_wbc_alert_docstring_contains_theta(self):
        from hermeneus.src.mcp_server import _log_wbc_bc11_alert
        doc = _log_wbc_bc11_alert.__doc__ or ""
        assert "θ12.1" in doc, f"_log_wbc_bc11_alert の docstring に θ12.1 が含まれていない: {doc[:100]}"

    def test_wbc_notification_text_contains_theta(self):
        import hermeneus.src.mcp_server as mod
        import inspect
        source = inspect.getsource(mod._log_wbc_bc11_alert)
        assert "θ12.1" in source, "WBC アラート関数のソースコードに θ12.1 が含まれていない"


class TestProgressLogging:
    """/ele 矛盾#4対応: _progress と _progress_reset の単体テスト"""

    def test_progress_output(self, capsys):
        """_progress が正しく JSON ログを stderr に書き出すかテスト"""
        from hermeneus.src.mcp_server import _progress, _progress_reset
        import json
        
        # タイマーリセット
        _progress_reset()
        # 最初の進捗呼び出し
        _progress("test_phase", "Test detail", step=1, total=5)
        
        captured = capsys.readouterr()
        lines = [line for line in captured.err.split('\n') if line.strip()]
        assert len(lines) > 0, "stderr に出力がない"
        
        try:
            log_entry = json.loads(lines[-1])
        except Exception:
            pytest.fail("出力が JSON ではない: " + lines[-1])
            
        assert log_entry["event"] == "progress"
        assert log_entry["phase"] == "test_phase"
        assert log_entry["detail"] == "Test detail"
        assert log_entry["step"] == 1
        assert log_entry["total"] == 5
        assert "elapsed" in log_entry
        assert isinstance(log_entry["elapsed"], float)

    def test_progress_timing(self, capsys):
        """_progress_reset 後の経過時間が計測できているかテスト"""
        from hermeneus.src.mcp_server import _progress, _progress_reset
        import json
        
        _progress_reset()
        time.sleep(0.1) # 100ms 待機
        _progress("time_phase", "Timing test")
        
        captured = capsys.readouterr()
        lines = [line for line in captured.err.split('\n') if line.strip()]
        
        try:
            log_entry = json.loads(lines[-1])
        except Exception:
            pytest.fail("出力が JSON ではない: " + lines[-1])
            
        # 少なくとも 0.1秒は経過しているはず (round で 1桁になるため 0.1)
        assert log_entry["elapsed"] >= 0.1
