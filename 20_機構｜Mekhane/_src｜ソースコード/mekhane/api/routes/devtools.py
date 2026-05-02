from __future__ import annotations
# PROOF: mekhane/api/routes/devtools.py
# PURPOSE: api モジュールの devtools
"""
DevTools API routes — ファイル操作・ターミナル・Ochema (AI) をフロントエンド DevTools ビューに提供。

Endpoints:
  GET  /files/list          ディレクトリ一覧
  GET  /files/read          ファイル読み取り
  POST /terminal/execute    コマンド実行
  POST /ochema/ask_with_tools  AI (Cortex API) でツール実行
"""


import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from mekhane.ochema.model_defaults import FLASH

logger = logging.getLogger("hegemonikon.api.devtools")

router = APIRouter(tags=["devtools"])

from mekhane import paths

# ─── Security: allowed base paths ──────────────────────────────
ALLOWED_BASES = [
    paths.OIKOS_ROOT.resolve(),
    (Path.home() / "oikos").resolve(),
    (Path.home() / ".gemini").resolve(),
    Path("/tmp").resolve(),
]


# PURPOSE: [L2-auto] _is_safe_path の関数定義
def _is_safe_path(path: str) -> bool:
    """Check if the path is under allowed base directories."""
    resolved = Path(path).expanduser().resolve()
    return any(resolved.is_relative_to(base) for base in ALLOWED_BASES)


# ─── File Operations ──────────────────────────────────────────

# PURPOSE: [L2-auto] list_directory の非同期処理定義
@router.get("/files/list")
async def list_directory(
    path: str = Query(default=str(paths.HGK_ROOT)),
) -> dict[str, Any]:
    """List directory entries with name, is_dir, size, children count."""
    if not _is_safe_path(path):
        raise HTTPException(403, f"Access denied: {path}")

    target = Path(path).expanduser().resolve()
    if not target.is_dir():
        raise HTTPException(404, f"Not a directory: {path}")

    entries = []
    try:
        for item in sorted(target.iterdir()):
            # Skip hidden files and __pycache__
            if item.name.startswith(".") or item.name == "__pycache__":
                continue
            entry: dict[str, Any] = {
                "name": item.name,
                "path": str(item),
                "is_dir": item.is_dir(),
            }
            if item.is_file():
                try:
                    entry["size"] = item.stat().st_size
                except OSError:
                    entry["size"] = 0
            elif item.is_dir():
                try:
                    entry["children"] = sum(1 for _ in item.iterdir())
                except OSError:
                    entry["children"] = 0
            entries.append(entry)
    except PermissionError:
        raise HTTPException(403, f"Permission denied: {path}")

    return {"entries": entries, "path": path}


# PURPOSE: [L2-auto] read_file の非同期処理定義
@router.get("/files/read")
async def read_file(
    path: str = Query(...),
) -> dict[str, Any]:
    """Read file content as text."""
    if not _is_safe_path(path):
        raise HTTPException(403, f"Access denied: {path}")

    target = Path(path).expanduser().resolve()
    if not target.is_file():
        raise HTTPException(404, f"Not a file: {path}")

    # Size limit: 2MB
    size = target.stat().st_size
    if size > 2 * 1024 * 1024:
        raise HTTPException(413, f"File too large: {size} bytes (max 2MB)")

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Read error: {exc}")

    return {"content": content, "path": str(target), "size": size}


# ─── Terminal ─────────────────────────────────────────────────

# PURPOSE: [L2-auto] TerminalRequest のクラス定義
class TerminalRequest(BaseModel):
    command: str
    cwd: str = str(paths.HGK_ROOT)


# Dangerous commands that should be blocked
BLOCKED_COMMANDS = {
    "rm -rf /", "rm -rf /*", "mkfs", "dd if=",
    ":(){ :|:& };:", "shutdown", "reboot", "halt",
}


# PURPOSE: [L2-auto] execute_command の非同期処理定義
@router.post("/terminal/execute")
async def execute_command(req: TerminalRequest) -> dict[str, Any]:
    """Execute a shell command and return output."""
    cmd = req.command.strip()
    cwd = req.cwd

    if not _is_safe_path(cwd):
        raise HTTPException(403, f"Access denied: {cwd}")

    # Block dangerous commands
    for blocked in BLOCKED_COMMANDS:
        if blocked in cmd:
            raise HTTPException(403, f"Blocked command: {cmd}")

    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env={**os.environ, "PYTHONPATH": str(Path(cwd))},
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

        output = stdout.decode("utf-8", errors="replace")
        error = stderr.decode("utf-8", errors="replace")

        return {
            "output": output + ("\n" + error if error else ""),
            "stdout": output,
            "stderr": error,
            "returncode": proc.returncode,
            "command": cmd,
            "cwd": cwd,
        }
    except asyncio.TimeoutError:
        return {"output": "(タイムアウト: 30秒)", "returncode": -1, "command": cmd, "cwd": cwd}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Execution error: {exc}")


# ─── Git Operations ──────────────────────────────────────────

# PURPOSE: [L2-auto] git_status の非同期処理定義
@router.get("/git/status")
async def git_status(
    repo: str = Query(default=str(paths.HGK_ROOT)),
) -> dict[str, Any]:
    """Get git status (changed files) for a repository."""
    if not _is_safe_path(repo):
        raise HTTPException(403, f"Access denied: {repo}")

    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "status", "--porcelain", "-uall",
            cwd=repo,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
        output = stdout.decode("utf-8", errors="replace").strip()

        files = []
        for line in output.split("\n"):
            if not line.strip():
                continue
            status_code = line[:2]
            filepath = line[3:].strip()
            # Map git status codes
            status_map = {
                "M": "modified", "A": "added", "D": "deleted",
                "R": "renamed", "??": "untracked", "!!": "ignored",
            }
            status = status_map.get(status_code.strip(), "unknown")
            files.append({"path": filepath, "status": status, "code": status_code.strip()})

        return {"files": files, "total": len(files), "repo": repo}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Git status error: {exc}")


# PURPOSE: [L2-auto] git_diff の非同期処理定義
@router.get("/git/diff")
async def git_diff(
    repo: str = Query(default=str(paths.HGK_ROOT)),
    path: str = Query(default=""),
    staged: bool = Query(default=False),
) -> dict[str, Any]:
    """Get git diff for a file or entire repo."""
    if not _is_safe_path(repo):
        raise HTTPException(403, f"Access denied: {repo}")

    cmd = ["git", "diff", "--no-color"]
    if staged:
        cmd.append("--cached")
    if path:
        cmd.extend(["--", path])

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=repo,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
        diff_output = stdout.decode("utf-8", errors="replace")

        return {
            "diff": diff_output,
            "path": path or "(all)",
            "staged": staged,
            "repo": repo,
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Git diff error: {exc}")


# ─── Ochema (AI with Tools) ──────────────────────────────────

# PURPOSE: [L2-auto] OchemaRequest のクラス定義
class OchemaRequest(BaseModel):
    message: str
    model: str = FLASH
    max_iterations: int = 10
    system_instruction: str = ""
    max_tokens: int = 65536
    thinking_budget: int | None = None


# PURPOSE: [L2-auto] ask_with_tools の非同期処理定義
@router.post("/ochema/ask_with_tools")
async def ask_with_tools(req: OchemaRequest) -> dict[str, Any]:
    """Proxy to Cortex API ask_with_tools."""
    try:
        from mekhane.ochema.service import OchemaService

        client = OchemaService.get()
        response = client.ask_with_tools(
            message=req.message,
            model=req.model,
            system_instruction=req.system_instruction or None,
            max_iterations=req.max_iterations,
            max_tokens=req.max_tokens,
            thinking_budget=req.thinking_budget,
            timeout=120.0,
        )
        return {
            "text": response.text,
            "model": response.model,
            "thinking": response.thinking,
        }
    except Exception as exc:  # noqa: BLE001
        exc_str = str(exc)
        logger.exception("ask_with_tools failed")
        # User-friendly error messages
        if "RESOURCE_EXHAUSTED" in exc_str or "429" in exc_str:
            raise HTTPException(429, "API の処理枠が一時的に満杯です。数分後に再試行してください。")
        if "500" in exc_str and "INTERNAL" in exc_str:
            raise HTTPException(502, "API サーバーで一時エラーが発生しました。")
        raise HTTPException(500, f"AI error: {exc}")
