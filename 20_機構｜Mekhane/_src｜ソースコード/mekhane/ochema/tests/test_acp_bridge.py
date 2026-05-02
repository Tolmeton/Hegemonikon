from __future__ import annotations

from mekhane.ochema.acp_bridge import (
    _RuntimeConfig,
    _build_session_new_params,
    _build_session_prompt_params,
)


def test_build_session_new_params_for_gemini_cli_uses_cwd_and_mcp_servers() -> None:
    runtime = _RuntimeConfig(
        tool="gemini-cli",
        cmd_candidates=[["gemini", "--acp"]],
        cwd="/tmp/runtime",
        env={},
        project_dir="/tmp/project",
        model="gemini-3.1-pro-preview",
    )

    params = _build_session_new_params(runtime)

    assert params == {
        "cwd": "/tmp/project",
        "mcpServers": [],
        "model": "gemini-3.1-pro-preview",
    }


def test_build_session_new_params_for_codex_keeps_project_directory_shape() -> None:
    runtime = _RuntimeConfig(
        tool="codex",
        cmd_candidates=[["npx", "@zed-industries/codex-acp"]],
        cwd="/tmp/runtime",
        env={},
        project_dir="/tmp/project",
        model="gpt-5.3-codex",
    )

    params = _build_session_new_params(runtime)

    assert params == {
        "projectDirectory": "/tmp/project",
        "model": "gpt-5.3-codex",
    }


def test_build_session_prompt_params_for_gemini_cli_uses_prompt_key() -> None:
    runtime = _RuntimeConfig(
        tool="gemini-cli",
        cmd_candidates=[["gemini", "--acp"]],
        cwd="/tmp/runtime",
        env={},
        project_dir="/tmp/project",
        model="gemini-3.1-pro-preview",
    )

    params = _build_session_prompt_params(
        runtime,
        session_id="sess-1",
        prompt="Reply with OK only.",
    )

    assert params == {
        "sessionId": "sess-1",
        "prompt": [{"type": "text", "text": "Reply with OK only."}],
    }


def test_build_session_prompt_params_for_codex_keeps_input_key() -> None:
    runtime = _RuntimeConfig(
        tool="codex",
        cmd_candidates=[["npx", "@zed-industries/codex-acp"]],
        cwd="/tmp/runtime",
        env={},
        project_dir="/tmp/project",
        model="gpt-5.3-codex",
    )

    params = _build_session_prompt_params(
        runtime,
        session_id="sess-1",
        prompt="Reply with OK only.",
    )

    assert params == {
        "sessionId": "sess-1",
        "input": [{"type": "text", "text": "Reply with OK only."}],
    }
