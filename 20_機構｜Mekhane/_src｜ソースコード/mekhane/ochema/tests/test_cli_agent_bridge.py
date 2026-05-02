from __future__ import annotations

import os
from pathlib import Path
import shutil
from unittest.mock import patch
import subprocess

from mekhane.ochema import cli_agent_bridge


def test_run_cli_agent_codex_normalizes_model_and_effort() -> None:
    with (
        patch("mekhane.ochema.cli_agent_bridge._find_tool", return_value="/usr/bin/codex"),
        patch("mekhane.ochema.cli_agent_bridge.subprocess.run") as mock_run,
        patch("mekhane.ochema.cli_agent_bridge.time.time", side_effect=[10.0, 10.2]),
    ):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "OK"
        mock_run.return_value.stderr = ""

        result = cli_agent_bridge.run_cli_agent(
            "Reply with OK only.",
            tool="codex",
            model="gpt-5.3-codex:high",
            timeout=30,
        )

    assert result["status"] == "ok"
    cmd = mock_run.call_args.args[0]
    assert cmd[:3] == ["/usr/bin/codex", "exec", "--skip-git-repo-check"]
    assert "-m" in cmd
    assert "gpt-5.3-codex" in cmd
    assert "-c" in cmd
    assert 'model_reasoning_effort="high"' in cmd
    assert mock_run.call_args.kwargs["cwd"] == os.path.expanduser("~")
    assert mock_run.call_args.kwargs["encoding"] == "utf-8"
    assert mock_run.call_args.kwargs["errors"] == "replace"
    assert mock_run.call_args.kwargs["env"]["CODEX_HOME"]


def test_run_cli_agent_copilot_defaults_to_expected_effort() -> None:
    with (
        patch("mekhane.ochema.cli_agent_bridge._find_tool", return_value="/usr/bin/copilot"),
        patch("mekhane.ochema.cli_agent_bridge.subprocess.run") as mock_run,
        patch("mekhane.ochema.cli_agent_bridge.time.time", side_effect=[20.0, 20.1]),
    ):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "OK"
        mock_run.return_value.stderr = ""

        result = cli_agent_bridge.run_cli_agent(
            "Analyze this.",
            tool="copilot",
            model="gpt-5.4",
            timeout=30,
        )

    assert result["status"] == "ok"
    cmd = mock_run.call_args.args[0]
    effort_index = cmd.index("--effort")
    assert cmd[effort_index + 1] == "xhigh"


def test_run_cli_agent_handles_missing_stderr_buffer() -> None:
    with (
        patch("mekhane.ochema.cli_agent_bridge._find_tool", return_value="/usr/bin/copilot"),
        patch("mekhane.ochema.cli_agent_bridge.subprocess.run") as mock_run,
        patch("mekhane.ochema.cli_agent_bridge.time.time", side_effect=[30.0, 30.1]),
    ):
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "problem"
        mock_run.return_value.stderr = None

        result = cli_agent_bridge.run_cli_agent(
            "Analyze this.",
            tool="copilot",
            model="gpt-5.4:high",
            timeout=30,
        )

    assert result["status"] == "error"
    assert "problem" in result["error"]


def test_run_cli_agent_timeout_returns_partial_output() -> None:
    with (
        patch("mekhane.ochema.cli_agent_bridge._find_tool", return_value="/usr/bin/codex"),
        patch("mekhane.ochema.cli_agent_bridge.time.time", side_effect=[40.0, 60.5]),
        patch("mekhane.ochema.cli_agent_bridge._prepare_cli_env", return_value={"CODEX_HOME": "/tmp/codex-home"}),
        patch("mekhane.ochema.cli_agent_bridge.subprocess.run", side_effect=subprocess.TimeoutExpired(
            cmd=["/usr/bin/codex", "exec"],
            timeout=20,
            output="partial stdout",
            stderr="partial stderr",
        )),
    ):
        result = cli_agent_bridge.run_cli_agent(
            "Reply with OK only.",
            tool="codex",
            model="gpt-5.3-codex:high",
            timeout=20,
        )

    assert result["status"] == "error"
    assert result["stdout"] == "partial stdout"
    assert result["stderr"] == "partial stderr"


def test_status_includes_gemini_without_running_smoke() -> None:
    with (
        patch("mekhane.ochema.cli_agent_bridge._find_tool") as mock_find,
        patch("mekhane.ochema.cli_agent_bridge._tool_version", return_value="1.0.0"),
        patch("mekhane.ochema.gemini_bridge.get_status") as mock_gemini_status,
        patch("mekhane.ochema.cli_agent_bridge._ensure_codex_runtime_home", return_value=Path("/tmp/codex-home")),
    ):
        mock_find.side_effect = lambda name: f"/usr/bin/{name}" if name != "cursor-agent" else None
        mock_gemini_status.return_value = {
            "available": True,
            "gemini_path": "/usr/bin/gemini",
            "account": "test-account",
        }

        info = cli_agent_bridge.status()

    assert info["copilot"]["available"] is True
    assert info["codex"]["available"] is True
    assert Path(info["codex"]["runtime_home"]) == Path("/tmp/codex-home")
    assert info["cursor-agent"]["available"] is False
    assert info["gemini"]["available"] is True
    assert info["gemini"]["smoke"]["supported"] is True


def test_smoke_allows_gemini_path() -> None:
    with patch("mekhane.ochema.gemini_bridge.run_gemini") as mock_run:
        mock_run.return_value = {"status": "ok", "output": "OK"}
        result = cli_agent_bridge.smoke("gemini", timeout=15)

    assert result["status"] == "ok"
    _, kwargs = mock_run.call_args
    assert kwargs["model"] == "gemini-3.1-pro"
    assert kwargs["rotate_before"] is False


def test_prepare_cli_env_for_codex_uses_workspace_runtime_home() -> None:
    sandbox = cli_agent_bridge._PROJECT_ROOT / ".tmp" / "pytest-codex-home"
    if sandbox.exists():
        shutil.rmtree(sandbox)
    try:
        source_home = sandbox / "source-home"
        codex_source = source_home / ".codex"
        codex_source.mkdir(parents=True)
        (codex_source / "auth.json").write_text('{"token":"abc"}', encoding="utf-8")
        (codex_source / "config.toml").write_text("model = 'gpt-5.3-codex'\n", encoding="utf-8")

        runtime_home = sandbox / "runtime-home"

        with (
            patch.dict(os.environ, {"HGK_CODEX_HOME": str(runtime_home)}, clear=False),
            patch("pathlib.Path.home", return_value=source_home),
        ):
            env = cli_agent_bridge._prepare_cli_env("codex")

        assert env["CODEX_HOME"] == str(runtime_home)
        assert (runtime_home / "auth.json").exists()
        assert (runtime_home / "config.toml").exists()
    finally:
        if sandbox.exists():
            shutil.rmtree(sandbox)
