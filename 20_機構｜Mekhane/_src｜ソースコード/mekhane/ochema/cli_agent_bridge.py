#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/ochema/cli_agent_bridge.py A0→CC↔CLI Agent 統合ブリッジ
"""
CC↔CLI Agent 統合ブリッジ — Claude Code から Copilot / Codex / Cursor Agent を呼び出す。

gemini_bridge.py と同構造。直接 subprocess で CLI Agent を呼び出す。

使い方 (CC の Bash tool から):
  SRC="20_機構｜Mekhane/_src｜ソースコード"
  python -m mekhane.ochema.cli_agent_bridge ask copilot "このコードをレビューして" --model gpt-5.4:xhigh
  python -m mekhane.ochema.cli_agent_bridge ask codex "2+2は？"
  python -m mekhane.ochema.cli_agent_bridge ask cursor-agent "バグを修正して" --model composer-2
  python -m mekhane.ochema.cli_agent_bridge status

対応ツール:
  copilot      — GitHub Copilot CLI (copilot -p)。Pro+ リクエスト課金 → 常に最高 effort。model 例: gpt-5.4 (→auto xhigh), claude-opus-4-6 (→auto high)。
  codex        — OpenAI Codex CLI (codex exec)。GPT-5.2-codex。セカンドオピニオン。
  cursor-agent — Cursor Agent CLI (cursor-agent --trust -p)。Composer 2。コーディング特化。

設計:
  - 統一インターフェース: run_cli_agent(prompt, tool, model, timeout) → dict
  - 出力パース: 各ツールのメタ情報を除去し clean text を抽出
  - タイムアウト: cursor-agent ベータのハング対策
  - JSON 出力 (CC がパース可能)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[4]  # mekhane/ochema → _src → Mekhane → HGK root
_WORKSPACE_TMP = _PROJECT_ROOT / ".tmp"
_CODEX_RUNTIME_HOME = _WORKSPACE_TMP / "codex-home"
_TEXT_SUBPROCESS_KWARGS = {
    "text": True,
    "encoding": "utf-8",
    "errors": "replace",
}


# ---------------------------------------------------------------------------
# Tool discovery
# ---------------------------------------------------------------------------

# cursor-agent は "agent" という名前でもインストールされる
_TOOL_ALIASES: dict[str, list[str]] = {
    "cursor-agent": ["cursor-agent", "agent"],
    "copilot": ["copilot"],
    "codex": ["codex"],
    "gemini": ["gemini-wrapper", "gemini"],
}


def _find_tool(name: str) -> str | None:
    """CLI ツールのパスを検索。エイリアスも探索する。"""
    candidates = _TOOL_ALIASES.get(name, [name])
    for alias in candidates:
        for d in ("~/.local/bin", "~/.npm-global/bin", "/usr/local/bin"):
            path = os.path.expanduser(f"{d}/{alias}")
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        found = shutil.which(alias)
        if found:
            return found
    return None


# ---------------------------------------------------------------------------
# Output parsers — 各ツールのメタ情報を除去し clean text を抽出
# ---------------------------------------------------------------------------

def _parse_copilot_output(stdout: str) -> str:
    """Copilot CLI 出力からメタ情報を除去。

    出力例:
        応答テキスト

        Total usage est:        3 Premium requests
        API time spent:         4s
        ...
    """
    lines = stdout.strip().splitlines()
    # 末尾のメタ情報ブロックを除去
    clean_lines: list[str] = []
    meta_started = False
    for line in reversed(lines):
        if not meta_started and re.match(
            r"^(Total usage est|API time spent|Total session time|Total code changes|Breakdown by)",
            line.strip(),
        ):
            meta_started = True
            continue
        if meta_started and line.strip() == "":
            continue
        if meta_started and re.match(r"^\s+\S", line):
            # indented continuation of meta block
            continue
        meta_started = False
        clean_lines.append(line)
    clean_lines.reverse()
    return "\n".join(clean_lines).strip()


def _parse_codex_output(stdout: str) -> str:
    """Codex CLI 出力からヘッダ/フッターを除去。

    出力例:
        OpenAI Codex v0.93.0 (research preview)
        --------
        workdir: ...
        model: gpt-5.2-codex
        ...
        --------
        user
        What is 2+2?
        mcp startup: no servers
        codex
        4
        tokens used
        4,123
        4
    """
    lines = stdout.strip().splitlines()

    # -------- で区切られたヘッダをスキップ
    separator_count = 0
    content_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("--------"):
            separator_count += 1
            if separator_count == 2:
                content_start = i + 1
                break

    if content_start == 0:
        return stdout.strip()

    content_lines = lines[content_start:]

    # "user\n<prompt>" をスキップ
    if content_lines and content_lines[0].strip() == "user":
        content_lines = content_lines[1:]
        # skip the user's prompt line(s) until "mcp startup:" or "codex"
        while content_lines:
            line = content_lines[0].strip()
            if line.startswith("mcp startup:") or line == "codex":
                break
            content_lines = content_lines[1:]

    # "mcp startup:" をスキップ
    if content_lines and content_lines[0].strip().startswith("mcp startup:"):
        content_lines = content_lines[1:]

    # "codex" ラベルをスキップ
    if content_lines and content_lines[0].strip() == "codex":
        content_lines = content_lines[1:]

    # 末尾の "tokens used\nN,NNN\nN" を除去
    while content_lines:
        last = content_lines[-1].strip()
        if last in ("tokens used",) or re.match(r"^[\d,]+$", last):
            content_lines.pop()
        else:
            break

    return "\n".join(content_lines).strip()


def _parse_cursor_agent_output(stdout: str) -> str:
    """Cursor Agent 出力はそのまま (--output-format text は clean)。"""
    return stdout.strip()


_PARSERS = {
    "copilot": _parse_copilot_output,
    "codex": _parse_codex_output,
    "cursor-agent": _parse_cursor_agent_output,
}

_COPILOT_DEFAULT_EFFORT = {
    "gpt-5.4": "xhigh",
    "claude-opus-4-6": "high",
}
_CODEX_DEFAULT_EFFORT = {
    "gpt-5.3-codex": "high",
}
_SMOKE_MODELS = {
    "copilot": "gpt-5.4:high",
    "codex": "gpt-5.3-codex:high",
    "cursor-agent": "auto",
    "gemini": "gemini-3.1-pro",
}
_SMOKE_PROMPT = "Reply with OK only."


def _split_model_and_effort(model: str | None) -> tuple[str | None, str | None]:
    if not model:
        return None, None
    if ":" not in model:
        return model, None
    model_name, effort = model.rsplit(":", 1)
    if effort in {"low", "medium", "high", "xhigh"}:
        return model_name, effort
    return model, None


def _normalize_cli_request(tool: str, model: str | None) -> tuple[str | None, str | None]:
    model_name, effort = _split_model_and_effort(model)

    if tool == "copilot":
        if model_name is None:
            return None, "xhigh"
        return model_name, effort or _COPILOT_DEFAULT_EFFORT.get(model_name, "xhigh")

    if tool == "codex":
        if model_name is None:
            return None, None
        return model_name, effort or _CODEX_DEFAULT_EFFORT.get(model_name)

    if tool == "cursor-agent":
        return model_name, effort

    return model_name, effort


def _prepare_cli_cwd(tool: str) -> str:
    if tool == "codex":
        return os.path.expanduser("~")
    return str(_PROJECT_ROOT)


def _ensure_codex_runtime_home() -> Path:
    runtime_home = Path(os.environ.get("HGK_CODEX_HOME", str(_CODEX_RUNTIME_HOME))).expanduser()
    runtime_home.mkdir(parents=True, exist_ok=True)

    source_home = Path.home() / ".codex"
    for filename in ("auth.json", "config.toml"):
        source = source_home / filename
        target = runtime_home / filename
        if source.exists() and not target.exists():
            try:
                shutil.copy2(source, target)
            except OSError:
                # 読み取り/コピー失敗時は runtime home 自体だけ使う。
                pass
    return runtime_home


def _prepare_cli_env(tool: str) -> dict[str, str]:
    env = dict(os.environ)
    if tool == "codex":
        env["CODEX_HOME"] = str(_ensure_codex_runtime_home())
    return env


def _tool_version(path: str) -> str:
    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True,
            timeout=5,
            **_TEXT_SUBPROCESS_KWARGS,
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        return (stdout or stderr or "unknown").splitlines()[0]
    except Exception:  # noqa: BLE001
        return "unknown"


def _clip_timeout_buffer(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="replace")
    else:
        text = str(value)
    clipped = text.strip()
    return clipped[:2000] if clipped else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_cli_agent(
    prompt: str,
    *,
    tool: str = "copilot",
    model: str | None = None,
    timeout: int = 300,
) -> dict:
    """CLI Agent を実行し結果を返す。

    Args:
        prompt: プロンプト文字列
        tool: "copilot" | "codex" | "cursor-agent"
        model: モデル名。copilot/codex は "model:effort" 形式を許容
        timeout: タイムアウト秒数

    Returns:
        dict: {status, output/error, tool, model, elapsed_s}
    """
    # ツール検索
    tool_path = _find_tool(tool)
    if not tool_path:
        return {"status": "error", "error": f"{tool} CLI not found in PATH"}

    model_name, effort = _normalize_cli_request(tool, model)

    # コマンド構築
    if tool == "copilot":
        cmd = [tool_path, "-p", prompt, "--allow-all"]
        if model_name:
            cmd.extend(["--model", model_name, "--effort", effort])
        else:
            cmd.extend(["--effort", "xhigh"])
    elif tool == "codex":
        cmd = [tool_path, "exec", "--skip-git-repo-check", prompt]
        if model_name:
            cmd.extend(["-m", model_name])
        if effort:
            cmd.extend(["-c", f'model_reasoning_effort="{effort}"'])
    elif tool == "cursor-agent":
        cmd = [tool_path, "--trust", "-p", prompt, "--output-format", "text"]
        if model_name:
            cmd.extend(["--model", model_name])
    else:
        return {"status": "error", "error": f"Unknown tool: {tool}"}

    start = time.time()

    cwd = _prepare_cli_cwd(tool)
    env = _prepare_cli_env(tool)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
            **_TEXT_SUBPROCESS_KWARGS,
        )
        elapsed = time.time() - start
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()

        if result.returncode != 0:
            # quota / auth errors
            error_msg = stderr or stdout or f"exit code {result.returncode}"
            return {
                "status": "error",
                "error": error_msg[:2000],
                "tool": tool,
                "model": model_name or "default",
                "effort": effort,
                "elapsed_s": round(elapsed, 1),
            }

        # 出力パース
        parser = _PARSERS.get(tool, lambda x: x.strip())
        clean_output = parser(stdout)

        return {
            "status": "ok",
            "output": clean_output,
            "tool": tool,
            "model": model_name or "default",
            "effort": effort,
            "chars": len(clean_output),
            "elapsed_s": round(elapsed, 1),
        }

    except subprocess.TimeoutExpired as exc:
        elapsed = time.time() - start
        payload = {
            "status": "error",
            "error": f"Timeout after {timeout}s (tool: {tool})",
            "tool": tool,
            "model": model_name or "default",
            "effort": effort,
            "elapsed_s": round(elapsed, 1),
        }
        stdout = _clip_timeout_buffer(getattr(exc, "stdout", None))
        stderr = _clip_timeout_buffer(getattr(exc, "stderr", None))
        if stdout:
            payload["stdout"] = stdout
        if stderr:
            payload["stderr"] = stderr
        return payload
    except FileNotFoundError:
        return {
            "status": "error",
            "error": f"{tool} binary not found at {tool_path}",
            "tool": tool,
        }


def smoke(tool: str, *, timeout: int = 30) -> dict:
    if tool == "gemini":
        from mekhane.ochema.gemini_bridge import run_gemini

        return run_gemini(
            _SMOKE_PROMPT,
            model=_SMOKE_MODELS["gemini"],
            timeout=timeout,
            max_retries=0,
            rotate_before=False,
        )

    return run_cli_agent(
        _SMOKE_PROMPT,
        tool=tool,
        model=_SMOKE_MODELS[tool],
        timeout=timeout,
    )


def status(*, run_smoke: bool = False, smoke_timeout: int = 30) -> dict:
    """全 CLI Agent の利用可能性を返す。"""
    tools = {}
    for name in ("copilot", "codex", "cursor-agent"):
        path = _find_tool(name)
        if path:
            tools[name] = {
                "available": True,
                "path": path,
                "version": _tool_version(path),
                "smoke": (
                    smoke(name, timeout=smoke_timeout)
                    if run_smoke
                    else {"supported": True, "hint": _SMOKE_MODELS[name]}
                ),
            }
            if name == "codex":
                tools[name]["runtime_home"] = str(_ensure_codex_runtime_home())
        else:
            tools[name] = {
                "available": False,
                "smoke": {"supported": True, "hint": _SMOKE_MODELS[name]},
            }
            if name == "codex":
                tools[name]["runtime_home"] = str(_ensure_codex_runtime_home())

    from mekhane.ochema.gemini_bridge import get_status as get_gemini_status

    gemini_info = get_gemini_status()
    gemini_info["smoke"] = (
        smoke("gemini", timeout=smoke_timeout)
        if run_smoke and gemini_info.get("available")
        else {"supported": True, "hint": _SMOKE_MODELS["gemini"]}
    )
    tools["gemini"] = gemini_info
    return tools


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    parser = argparse.ArgumentParser(
        description="CLI Agent Bridge — copilot / codex / cursor-agent",
    )
    sub = parser.add_subparsers(dest="command")

    # ask
    ask_p = sub.add_parser("ask", help="Execute a CLI agent")
    ask_p.add_argument("tool", choices=["copilot", "codex", "cursor-agent"])
    ask_p.add_argument("prompt")
    ask_p.add_argument("--model", default=None, help="Model name or model:effort")
    ask_p.add_argument("--timeout", type=int, default=300)

    # status
    status_p = sub.add_parser("status", help="Check tool availability")
    status_p.add_argument("--smoke", action="store_true")
    status_p.add_argument("--timeout", type=int, default=30)

    smoke_p = sub.add_parser("smoke", help="Run a minimal smoke test")
    smoke_p.add_argument("tool", choices=["copilot", "codex", "cursor-agent", "gemini", "all"])
    smoke_p.add_argument("--timeout", type=int, default=30)

    args = parser.parse_args()

    if args.command == "ask":
        result = run_cli_agent(
            args.prompt,
            tool=args.tool,
            model=args.model,
            timeout=args.timeout,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "status":
        print(
            json.dumps(
                status(run_smoke=args.smoke, smoke_timeout=args.timeout),
                ensure_ascii=False,
                indent=2,
            ),
        )
    elif args.command == "smoke":
        if args.tool == "all":
            result = {
                name: smoke(name, timeout=args.timeout)
                for name in ("copilot", "codex", "cursor-agent", "gemini")
            }
        else:
            result = smoke(args.tool, timeout=args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
