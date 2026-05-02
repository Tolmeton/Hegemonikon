# PROOF: mekhane/ochema/tests/test_gemini_bridge.py
# PURPOSE: gemini_bridge モジュールのユニットテスト
from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from mekhane.ochema.gemini_bridge import (
    _build_env,
    _find_gemini,
    _find_rotate,
    _get_current_account,
    _rotate_account,
    get_status,
    run_batch,
    run_gemini,
    run_review,
)


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------


class TestBuildEnv:
    def test_gcloud_pollution_blocked(self):
        env = _build_env()
        assert env["CLOUDSDK_CONFIG"] == "/dev/null"
        assert env["GOOGLE_CLOUD_PROJECT"] == ""
        assert env["GOOGLE_CLOUD_PROJECT_ID"] == ""
        assert env["GCLOUD_PROJECT"] == ""

    def test_preserves_existing_env(self):
        env = _build_env()
        assert "PATH" in env


class TestFindGemini:
    @patch("os.path.isfile", return_value=True)
    @patch("os.access", return_value=True)
    def test_prefers_wrapper(self, mock_access, mock_isfile):
        result = _find_gemini()
        assert "gemini-wrapper" in result

    @patch("os.path.isfile", return_value=False)
    @patch("shutil.which", side_effect=lambda name: f"/usr/bin/{name}" if name == "gemini" else None)
    def test_fallback_to_gemini(self, mock_which, mock_isfile):
        result = _find_gemini()
        assert result == "/usr/bin/gemini"

    @patch("os.path.isfile", return_value=False)
    @patch("shutil.which", return_value=None)
    def test_returns_none_if_not_found(self, mock_which, mock_isfile):
        result = _find_gemini()
        assert result is None


class TestFindRotate:
    @patch("os.path.isfile", return_value=True)
    @patch("os.access", return_value=True)
    def test_finds_rotate(self, mock_access, mock_isfile):
        result = _find_rotate()
        assert "gemini-rotate" in result

    @patch("os.path.isfile", return_value=False)
    @patch("shutil.which", return_value=None)
    def test_returns_none_if_not_found(self, mock_which, mock_isfile):
        result = _find_rotate()
        assert result is None


class TestRotateAccount:
    @patch("subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert _rotate_account("/usr/bin/gemini-rotate", {}) is True

    @patch("subprocess.run")
    def test_nonzero_returncode_returns_false(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        assert _rotate_account("/usr/bin/gemini-rotate", {}) is False

    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="", timeout=5))
    def test_timeout_returns_false(self, mock_run):
        assert _rotate_account("/usr/bin/gemini-rotate", {}) is False


class TestGetCurrentAccount:
    def test_none_rotate_path(self):
        assert _get_current_account(None, {}) == "unknown"

    @patch("subprocess.run")
    def test_parses_active_account(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Active: Tolmeton\nAvailable:\n  * Tolmeton (1234 bytes)\n",
        )
        assert _get_current_account("/usr/bin/gemini-rotate", {}) == "Tolmeton"

    @patch("subprocess.run", side_effect=Exception("fail"))
    def test_error_returns_unknown(self, mock_run):
        assert _get_current_account("/usr/bin/gemini-rotate", {}) == "unknown"


# ---------------------------------------------------------------------------
# run_gemini tests
# ---------------------------------------------------------------------------


class TestRunGemini:
    @patch("mekhane.ochema.gemini_bridge._find_gemini", return_value=None)
    def test_no_gemini_returns_error(self, mock_find):
        result = run_gemini("hello")
        assert result["status"] == "error"
        assert "not found" in result["error"]

    @patch("mekhane.ochema.gemini_bridge._find_rotate", return_value=None)
    @patch("mekhane.ochema.gemini_bridge._find_gemini", return_value="/usr/bin/gemini-wrapper")
    @patch("subprocess.run")
    def test_successful_execution(self, mock_run, mock_gemini, mock_rotate):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="4\n",
            stderr="",
        )
        result = run_gemini("2+2は？", rotate_before=False)
        assert result["status"] == "ok"
        assert result["output"] == "4"
        assert result["attempts"] == 1
        assert mock_run.call_args.kwargs["encoding"] == "utf-8"
        assert mock_run.call_args.kwargs["errors"] == "replace"

    @patch("mekhane.ochema.gemini_bridge._find_rotate", return_value="/usr/bin/gemini-rotate")
    @patch("mekhane.ochema.gemini_bridge._find_gemini", return_value="/usr/bin/gemini-wrapper")
    @patch("subprocess.run")
    def test_429_retry_with_rotation(self, mock_run, mock_gemini, mock_rotate):
        # Call sequence: rotate(pre) → status → attempt1(429) → rotate(retry) → status → attempt2(ok)
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout="Switched to: Tolmeton\n", stderr=""),  # rotate next (pre-call)
            subprocess.CompletedProcess([], 0, stdout="Active: Tolmeton\n", stderr=""),  # _get_current_account
            subprocess.CompletedProcess([], 1, stdout="", stderr="429 Resource Exhausted"),  # first attempt — 429
            subprocess.CompletedProcess([], 0, stdout="Switched to: movement\n", stderr=""),  # rotate next (retry)
            subprocess.CompletedProcess([], 0, stdout="Active: movement\n", stderr=""),  # _get_current_account (retry)
            subprocess.CompletedProcess([], 0, stdout="success\n", stderr=""),  # second attempt — ok
        ]
        result = run_gemini("test", max_retries=3)
        assert result["status"] == "ok"
        assert result["output"] == "success"

    @patch("mekhane.ochema.gemini_bridge._find_rotate", return_value=None)
    @patch("mekhane.ochema.gemini_bridge._find_gemini", return_value="/usr/bin/gemini-wrapper")
    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="", timeout=300))
    def test_timeout(self, mock_run, mock_gemini, mock_rotate):
        result = run_gemini("slow query", timeout=300, rotate_before=False)
        assert result["status"] == "error"
        assert "timeout" in result["error"]

    @patch("mekhane.ochema.gemini_bridge._find_rotate", return_value=None)
    @patch("mekhane.ochema.gemini_bridge._find_gemini", return_value="/usr/bin/gemini-wrapper")
    @patch("subprocess.run")
    def test_nonzero_exit_without_429(self, mock_run, mock_gemini, mock_rotate):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="some error",
        )
        result = run_gemini("fail", rotate_before=False)
        assert result["status"] == "error"
        assert "exit code 1" in result["error"]

    @patch("mekhane.ochema.gemini_bridge._find_rotate", return_value=None)
    @patch("mekhane.ochema.gemini_bridge._find_gemini", return_value="/usr/bin/gemini-wrapper")
    @patch("subprocess.run")
    def test_handles_missing_stderr_buffer(self, mock_run, mock_gemini, mock_rotate):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="problem",
            stderr=None,
        )
        result = run_gemini("fail", rotate_before=False)
        assert result["status"] == "error"
        assert result["stdout"] == "problem"

    @patch("mekhane.ochema.gemini_bridge._find_rotate", return_value=None)
    @patch("mekhane.ochema.gemini_bridge._find_gemini", return_value="/usr/bin/gemini-wrapper")
    @patch("subprocess.run")
    def test_model_and_yolo_flags(self, mock_run, mock_gemini, mock_rotate):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        run_gemini("test", model="gemini-2.5-flash", sandbox=False, rotate_before=False)
        cmd = mock_run.call_args[0][0]
        assert "-m" in cmd
        assert "gemini-2.5-flash" in cmd
        assert "--yolo" in cmd

    @patch("mekhane.ochema.gemini_bridge._find_rotate", return_value=None)
    @patch("mekhane.ochema.gemini_bridge._find_gemini", return_value="/usr/bin/gemini-wrapper")
    @patch("subprocess.run")
    def test_mcp_servers_flag(self, mock_run, mock_gemini, mock_rotate):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        run_gemini("test", mcp_servers=["mneme", "phantazein"], rotate_before=False)
        cmd = mock_run.call_args[0][0]
        assert "--allowed-mcp-server-names" in cmd
        assert "mneme,phantazein" in cmd


# ---------------------------------------------------------------------------
# run_batch tests
# ---------------------------------------------------------------------------


class TestRunBatch:
    @patch("mekhane.ochema.gemini_bridge.run_gemini")
    def test_batch_calls_with_rotation(self, mock_run):
        # side_effect returns a fresh dict each call (return_value shares the same object)
        mock_run.side_effect = lambda *a, **kw: {"status": "ok", "output": "result"}
        results = run_batch(["q1", "q2", "q3"])
        assert len(results) == 3
        assert mock_run.call_count == 3
        # Each call should have rotate_before=True
        for call in mock_run.call_args_list:
            assert call[1]["rotate_before"] is True
        # Index and preview should be set (each result is a distinct dict)
        assert results[0]["index"] == 0
        assert results[2]["index"] == 2
        assert results[0]["prompt_preview"] == "q1"


# ---------------------------------------------------------------------------
# run_review tests
# ---------------------------------------------------------------------------


class TestRunReview:
    @patch("mekhane.ochema.gemini_bridge.run_gemini")
    def test_review_constructs_prompt(self, mock_run):
        mock_run.return_value = {"status": "ok", "output": "review result"}
        result = run_review("def foo(): pass", focus="security")
        assert result["status"] == "ok"
        # Verify prompt includes content and focus
        prompt_arg = mock_run.call_args[0][0]
        assert "def foo(): pass" in prompt_arg
        assert "security" in prompt_arg

    @patch("mekhane.ochema.gemini_bridge.run_gemini")
    def test_review_without_focus(self, mock_run):
        mock_run.return_value = {"status": "ok", "output": "review"}
        run_review("code here")
        prompt_arg = mock_run.call_args[0][0]
        assert "code here" in prompt_arg


# ---------------------------------------------------------------------------
# get_status tests
# ---------------------------------------------------------------------------


class TestGetStatus:
    @patch("mekhane.ochema.gemini_bridge._find_rotate", return_value=None)
    @patch("mekhane.ochema.gemini_bridge._find_gemini", return_value="/usr/bin/gemini-wrapper")
    def test_status_without_rotate(self, mock_gemini, mock_rotate):
        info = get_status()
        assert info["available"] is True
        assert info["gemini_path"] == "/usr/bin/gemini-wrapper"
        assert info["rotate_path"] is None

    @patch("mekhane.ochema.gemini_bridge._find_rotate", return_value=None)
    @patch("mekhane.ochema.gemini_bridge._find_gemini", return_value=None)
    def test_status_no_gemini(self, mock_gemini, mock_rotate):
        info = get_status()
        assert info["available"] is False

    @patch("subprocess.run")
    @patch("mekhane.ochema.gemini_bridge._find_rotate", return_value="/usr/bin/gemini-rotate")
    @patch("mekhane.ochema.gemini_bridge._find_gemini", return_value="/usr/bin/gemini-wrapper")
    def test_status_single_subprocess_call(self, mock_gemini, mock_rotate, mock_run):
        """get_status should call subprocess.run only once (no double invocation)."""
        mock_run.return_value = subprocess.CompletedProcess(
            [], 0, stdout="Active: Tolmeton\nAvailable:\n  * Tolmeton\n", stderr=""
        )
        info = get_status()
        assert info["account"] == "Tolmeton"
        assert "rotate_output" in info
        # Only 1 subprocess call (status), not 2
        assert mock_run.call_count == 1


# ---------------------------------------------------------------------------
# run_gemini: all-accounts-exhaustion test
# ---------------------------------------------------------------------------


class TestRunGeminiExhaustion:
    @patch("mekhane.ochema.gemini_bridge._find_rotate", return_value="/usr/bin/gemini-rotate")
    @patch("mekhane.ochema.gemini_bridge._find_gemini", return_value="/usr/bin/gemini-wrapper")
    @patch("subprocess.run")
    def test_all_accounts_exhausted(self, mock_run, mock_gemini, mock_rotate):
        """When all retries return 429, should return exhaustion error."""
        # rotate(pre) + status + attempt0(429) + rotate + status +
        # attempt1(429) + rotate + status + attempt2(429) — max_retries=2
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout="Switched\n", stderr=""),   # rotate pre
            subprocess.CompletedProcess([], 0, stdout="Active: a1\n", stderr=""), # status
            subprocess.CompletedProcess([], 1, stdout="", stderr="429 Exhausted"),  # attempt 0
            subprocess.CompletedProcess([], 0, stdout="Switched\n", stderr=""),   # rotate retry
            subprocess.CompletedProcess([], 0, stdout="Active: a2\n", stderr=""), # status
            subprocess.CompletedProcess([], 1, stdout="", stderr="429 Exhausted"),  # attempt 1
            subprocess.CompletedProcess([], 0, stdout="Switched\n", stderr=""),   # rotate retry
            subprocess.CompletedProcess([], 0, stdout="Active: a3\n", stderr=""), # status
            subprocess.CompletedProcess([], 1, stdout="", stderr="429 Exhausted"),  # attempt 2 (last)
        ]
        result = run_gemini("test", max_retries=2)
        assert result["status"] == "error"
        assert "all accounts exhausted" in result["error"]
        assert result["attempts"] == 3


# ---------------------------------------------------------------------------
# CLI smoke tests (argument parsing)
# ---------------------------------------------------------------------------


class TestCLI:
    def test_main_module_importable(self):
        """Verify the module can be imported without errors."""
        import mekhane.ochema.gemini_bridge as gb
        assert hasattr(gb, "main")
        assert hasattr(gb, "run_gemini")
        assert hasattr(gb, "run_batch")
        assert hasattr(gb, "run_review")
        assert hasattr(gb, "get_status")
