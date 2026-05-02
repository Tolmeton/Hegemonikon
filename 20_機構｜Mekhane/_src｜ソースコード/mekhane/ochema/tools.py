#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
# PROOF: [L2/インフラ] <- mekhane/ochema/ A0→AI Tool Use — ローカルファイル操作能力
# PURPOSE: API 直叩き AI にファイル読み書き・コマンド実行能力を付与する
#   Function Calling (Tool Use) のツール定義と実行ディスパッチャ

"""
Ochema Tool Use — AI のローカルファイル操作基盤

Gemini/Claude API の Function Calling を利用し、
API 直叩き AI がローカルファイルの読み書き・検索・コマンド実行を行えるようにする。

Architecture:
    User → OchemaService.ask_with_tools() → CortexClient
         → LLM API (+ tools definitions)
         ← functionCall / tool_use response
         → execute_tool() → ローカル実行
         → LLM API (results)
         ← 最終テキスト

Supports:
    - Gemini: Native Function Calling (structured JSON)
    - Claude: Text-based Tool Use (system prompt + parsing)
"""


import json
import logging
import subprocess
import re
import time
from datetime import datetime
from pathlib import Path

from mekhane.subprocess_utils import run_utf8

logger = logging.getLogger(__name__)

# --- Security: Allowed directories ---

# Only allow file operations within these directories
# resolve() is critical: ~/oikos may be a symlink (e.g. → ~/Sync/oikos)
# and _is_path_allowed() resolves input paths, so roots must also be resolved.
ALLOWED_ROOTS: list[Path] = [
    (Path.home() / "Sync" / "oikos").resolve(),
    Path("/tmp").resolve(),
]

# Primary workspace root for relative path resolution
PRIMARY_WORKSPACE: Path = (Path.home() / "Sync" / "oikos" / "hegemonikon").resolve()

# Keys in tool args that contain file/directory paths
_PATH_ARG_KEYS: frozenset[str] = frozenset({"path", "directory", "cwd", "repo_path"})

# Maximum file read size (bytes)
MAX_READ_SIZE = 512 * 1024  # 512KB

# Maximum command execution time
MAX_CMD_TIMEOUT = 30  # seconds

# Safety Gate: tools requiring user approval before execution
GATED_TOOLS: frozenset[str] = frozenset({"write_file", "run_command"})

# Tool execution log
_TOOL_LOG: list[dict[str, Any]] = []


# PURPOSE: [L2-auto] _normalize_path_args の関数定義
def _normalize_path_args(args: dict[str, Any]) -> dict[str, Any]:
    """Normalize relative paths in tool args to absolute paths.

    Relative paths are resolved against PRIMARY_WORKSPACE.
    Absolute paths and ~ paths are left to expanduser/resolve.
    Security boundary (_is_path_allowed) is NOT affected.
    """
    result = dict(args)
    for key in _PATH_ARG_KEYS:
        if key not in result:
            continue
        val = result[key]
        if not isinstance(val, str) or not val.strip():
            continue
        p = Path(val).expanduser()
        if not p.is_absolute():
            result[key] = str((PRIMARY_WORKSPACE / p).resolve())
    return result


# PURPOSE: [L2-auto] _is_path_allowed の関数定義
def _is_path_allowed(path: str) -> bool:
    """Check if a path is within allowed directories."""
    if not path or not path.strip():
        return False
    try:
        resolved = Path(path).expanduser().resolve()
        return any(
            resolved == root or root in resolved.parents
            for root in ALLOWED_ROOTS
        )
    except (ValueError, OSError):
        return False


# PURPOSE: [L2-auto] _log_tool_use の関数定義
def _log_tool_use(name: str, args: dict, result: dict, elapsed: float) -> None:
    """Record tool execution for audit trail (F5)."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": name,
        "args_summary": {k: str(v)[:100] for k, v in args.items()},
        "success": result.get("error") is None,  # E6: explicit key check
        "elapsed_ms": round(elapsed * 1000, 1),
    }
    _TOOL_LOG.append(entry)
    # Keep only last 100 entries
    if len(_TOOL_LOG) > 100:
        _TOOL_LOG.pop(0)


# PURPOSE: [L2-auto] get_tool_log の関数定義
def get_tool_log() -> list[dict[str, Any]]:
    """Get the tool execution audit log (F5)."""
    return list(_TOOL_LOG)


# --- Tool Definitions (Gemini Function Calling format) ---

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "read_file",
        "description": (
            "Read the content of a local file. "
            "Returns the file content as text. "
            "Use start_line/end_line to read specific ranges."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path (e.g. /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/file.py or relative like mekhane/file.py)",
                },
                "start_line": {
                    "type": "integer",
                    "description": "Start line number (1-indexed, optional)",
                },
                "end_line": {
                    "type": "integer",
                    "description": "End line number (1-indexed, inclusive, optional)",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": (
            "Write content to a local file. "
            "Creates parent directories if needed. "
            "Set append=true to append instead of overwrite."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path (absolute or relative to workspace)",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write",
                },
                "append": {
                    "type": "boolean",
                    "description": "Append to file instead of overwrite (default: false)",
                },
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_directory",
        "description": (
            "List files and subdirectories in a directory. "
            "Returns entries with type (file/dir) and size."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute directory path",
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum recursion depth (default: 1, max: 3)",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "search_text",
        "description": (
            "Search for a text pattern in files (grep-like). "
            "Returns matching lines with file paths and line numbers."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Text pattern to search for",
                },
                "directory": {
                    "type": "string",
                    "description": "Directory to search in",
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Glob pattern for file names (e.g. '*.py', default: '*')",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 50)",
                },
            },
            "required": ["pattern", "directory"],
        },
    },
    {
        "name": "run_command",
        "description": (
            "Execute a shell command and return the output. "
            "Use for safe, read-only commands (ls, git status, python -c, etc). "
            "Timeout: 30 seconds."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute",
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory (default: ~/oikos)",
                },
            },
            "required": ["command"],
        },
    },
    # --- F2: Developer Tools ---
    {
        "name": "git_diff",
        "description": (
            "Show git diff for the repository. "
            "Returns staged or unstaged changes. "
            "Use ref to compare with a specific commit."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Path to git repo (default: ~/oikos/01_ヘゲモニコン｜Hegemonikon)",
                },
                "staged": {
                    "type": "boolean",
                    "description": "Show staged changes (--cached)",
                },
                "ref": {
                    "type": "string",
                    "description": "Compare with ref (e.g. HEAD~3, main)",
                },
                "file_path": {
                    "type": "string",
                    "description": "Limit diff to specific file",
                },
            },
        },
    },
    {
        "name": "git_log",
        "description": (
            "Show git commit history. "
            "Returns recent commits with hash, author, date, and message."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Path to git repo (default: ~/oikos/01_ヘゲモニコン｜Hegemonikon)",
                },
                "max_count": {
                    "type": "integer",
                    "description": "Number of commits to show (default: 10, max: 50)",
                },
                "file_path": {
                    "type": "string",
                    "description": "Show commits for specific file only",
                },
                "oneline": {
                    "type": "boolean",
                    "description": "One-line format (default: true)",
                },
            },
        },
    },
]

# --- search_tools: Tool Discovery Meta-Tool ---

# PURPOSE: search_tools ツール定義 — LLM がカテゴリ/プリセットで拡張ツールを自己発見する
SEARCH_TOOLS_DEFINITION: dict[str, Any] = {
    "name": "search_tools",
    "description": (
        "Discover and load additional HGK tools by category or preset. "
        "Call this when you need specialized tools not in your current toolset. "
        "Categories: knowledge, ccl, system, session, digest, research, gateway. "
        "Presets: research (papers + knowledge), digest (ingestion pipeline), "
        "session (handoffs + sessions), ccl (cognitive control). "
        "Returns tool names and descriptions. Loaded tools become available next turn."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": (
                    "Tool category to load. "
                    "Options: knowledge, ccl, system, session, digest, research, gateway, all"
                ),
            },
            "preset": {
                "type": "string",
                "description": (
                    "Preset tool pack to load. "
                    "Options: research, digest, session, ccl"
                ),
            },
            "query": {
                "type": "string",
                "description": "Free-text query to search tool names and descriptions",
            },
        },
    },
}

# PURPOSE: プリセットパック定義 — よく使うツール組合せ
TOOL_PRESETS: dict[str, list[str]] = {
    "research": [
        "hgk_paper_search", "hgk_pks_search", "hgk_search",
        "hgk_proactive_push", "hgk_sop_generate",
    ],
    "digest": [
        "hgk_digest_check", "hgk_digest_list", "hgk_digest_run",
        "hgk_digest_topics", "hgk_digest_mark",
    ],
    "session": [
        "hgk_handoff_read", "hgk_sessions", "hgk_session_read",
        "hgk_notifications",
    ],
    "ccl": [
        "hgk_ccl_execute", "hgk_ccl_dispatch",
    ],
}

# All valid HGK tool categories
HGK_CATEGORIES: frozenset[str] = frozenset({
    "knowledge", "ccl", "system", "session", "digest", "research", "gateway", "hub", "sekisho",
})


# PURPOSE: カテゴリベースのツールフィルタリング
def get_tools_by_category(category: str) -> list[dict[str, Any]]:
    """Return HGK tool definitions matching the given category.

    Args:
        category: One of HGK_CATEGORIES, or "all" for everything.

    Returns:
        List of tool definitions (dict with name, description, parameters).
    """
    from .hgk_tools import HGK_TOOL_DEFINITIONS

    if category == "all":
        return list(HGK_TOOL_DEFINITIONS)

    return [t for t in HGK_TOOL_DEFINITIONS if t.get("category") == category]


# PURPOSE: プリセットベースのツール取得
def get_tools_by_preset(preset: str) -> list[dict[str, Any]]:
    """Return HGK tool definitions for a preset pack.

    Args:
        preset: One of TOOL_PRESETS keys.

    Returns:
        List of tool definitions matching the preset.
    """
    from .hgk_tools import HGK_TOOL_DEFINITIONS

    names = TOOL_PRESETS.get(preset, [])
    if not names:
        return []

    name_set = set(names)
    return [t for t in HGK_TOOL_DEFINITIONS if t["name"] in name_set]


# PURPOSE: フリーテキスト検索によるツール発見
def search_extended_tools(query: str) -> list[dict[str, Any]]:
    """Search HGK tools by free-text query against name and description.

    Args:
        query: Search string (case-insensitive, matched against name + description).

    Returns:
        List of matching tool definitions.
    """
    from .hgk_tools import HGK_TOOL_DEFINITIONS

    q = query.lower()
    results: list[dict[str, Any]] = []
    for t in HGK_TOOL_DEFINITIONS:
        name = t["name"].lower()
        desc = t.get("description", "").lower()
        cat = t.get("category", "").lower()
        if q in name or q in desc or q in cat:
            results.append(t)
    return results


# PURPOSE: search_tools ツール実行ハンドラ
def execute_search_tools(args: dict[str, Any]) -> dict[str, Any]:
    """Execute the search_tools meta-tool.

    Resolves category, preset, or query and returns discovered tools.

    Returns:
        dict with 'output' (str) describing discovered tools,
        and 'loaded_tools' (list[dict]) of tool definitions to merge.
    """
    category = args.get("category", "")
    preset = args.get("preset", "")
    query = args.get("query", "")

    discovered: list[dict[str, Any]] = []

    if preset:
        discovered = get_tools_by_preset(preset)
        source = f"preset '{preset}'"
    elif category:
        discovered = get_tools_by_category(category)
        source = f"category '{category}'"
    elif query:
        discovered = search_extended_tools(query)
        source = f"query '{query}'"
    else:
        # No filter → list categories and presets
        lines = [
            "Available categories: " + ", ".join(sorted(HGK_CATEGORIES)),
            "Available presets: " + ", ".join(sorted(TOOL_PRESETS.keys())),
            "Use category, preset, or query to discover tools.",
        ]
        return {"output": "\n".join(lines), "loaded_tools": []}

    if not discovered:
        return {
            "output": f"No tools found for {source}.",
            "loaded_tools": [],
        }

    lines = [f"Discovered {len(discovered)} tools ({source}):\n"]
    for t in discovered:
        lines.append(f"- **{t['name']}**: {t.get('description', '')[:120]}")

    lines.append("\nThese tools are now available for use.")

    # Strip 'category' key from tool defs before passing to LLM API
    clean_defs = [
        {k: v for k, v in t.items() if k != "category"}
        for t in discovered
    ]

    return {
        "output": "\n".join(lines),
        "loaded_tools": clean_defs,
    }



# --- Tool Execution ---

from .utils import fuzzy_suggest as _fuzzy_suggest

# PURPOSE: [L2-auto] execute_tool の関数定義
def execute_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Dispatch and execute a tool call.

    Args:
        name: Tool name (must be one of TOOL_DEFINITIONS)
        args: Tool arguments

    Returns:
        Result dict with 'output' or 'error' key
    """
    # Normalize relative paths before dispatch (Kalon: single-point resolution)
    args = _normalize_path_args(args)

    dispatch = {
        "read_file": _exec_read_file,
        "write_file": _exec_write_file,
        "list_directory": _exec_list_directory,
        "search_text": _exec_search_text,
        "run_command": _exec_run_command,
        "git_diff": _exec_git_diff,
        "git_log": _exec_git_log,
    }

    if name not in dispatch:
        # Fallthrough to HGK Gateway tools
        from .hgk_tools import is_hgk_tool, execute_hgk_tool
        if is_hgk_tool(name):
            logger.info("Tool execute (HGK): %s(%s)", name, args)
            return execute_hgk_tool(name, args)
        # D-2: Fuzzy match — suggest closest tool name for typos
        from .hgk_tools import HGK_TOOL_DEFINITIONS
        all_names = list(dispatch.keys()) + [t["name"] for t in HGK_TOOL_DEFINITIONS]
        suggestion = _fuzzy_suggest(name, all_names)
        hint = f" Did you mean '{suggestion}'?" if suggestion else ""
        return {"error": f"Unknown tool: {name}.{hint}"}

    # High-risk tool detection for WBC alerting
    HIGH_RISK_TOOLS = {"write_file", "run_command"}

    try:
        logger.info("Tool execute: %s(%s)", name, args)
        start = time.monotonic()
        result = dispatch[name](args)
        elapsed = time.monotonic() - start
        logger.info("Tool result: %s → %d bytes (%.1fms)", name, len(str(result)), elapsed * 1000)
        _log_tool_use(name, args, result, elapsed)

        # WBC alert for high-risk tool executions
        if name in HIGH_RISK_TOOLS:
            _wbc_alert(name, args, result)

        return result
    except Exception as e:  # Intentional Catch-All (Tool execution boundary)  # noqa: BLE001
        logger.error("Tool error: %s → %s", name, e)
        result = {"error": f"{type(e).__name__}: {e}"}
        _log_tool_use(name, args, result, 0)
        return result


# PURPOSE: [L2-auto] _wbc_alert の関数定義
def _wbc_alert(tool_name: str, args: dict[str, Any], result: dict[str, Any]) -> None:
    """Send high-risk tool execution alert to Sympatheia WBC.

    Non-blocking: logs errors but never raises.
    """
    try:
        severity = "medium"
        if tool_name == "run_command":
            cmd = args.get("command", "")
            # Elevated severity for commands that modify state
            if any(kw in cmd for kw in ("rm", "mv", "cp", "git push", "pip", "npm")):
                severity = "high"
        elif tool_name == "write_file":
            path = args.get("path", "")
            # Elevated severity for config/kernel files
            if any(kw in path for kw in ("kernel/", ".env", "config", "SACRED")):
                severity = "high"

        details = (
            f"AI Tool Use: {tool_name}\n"
            f"Args: {json.dumps(args, ensure_ascii=False)[:500]}\n"
            f"Result: {'error' if 'error' in result else 'success'}"
        )
        files = [args.get("path", args.get("cwd", ""))]

        # Try to import and call WBC — non-fatal if unavailable
        try:
            from mekhane.mcp.sympatheia_server import wbc_alert as _sym_wbc
            _sym_wbc(
                details=details,
                severity=severity,
                files=[f for f in files if f],
                source="ochema-tool-use",
            )
            logger.debug("WBC alert sent: %s (%s)", tool_name, severity)
        except ImportError:
            logger.debug("Sympatheia WBC not available — skipping alert")
        except Exception as e_wbc:  # Intentional Catch-All (WBC alert boundary)  # noqa: BLE001
            logger.debug("WBC alert failed: %s", e_wbc)
    except Exception as e:  # Intentional Catch-All (WBC preparation boundary)  # noqa: BLE001
        # Never crash on WBC alerting
        logger.debug("WBC alert preparation failed: %s", e)


# PURPOSE: [L2-auto] _exec_read_file の関数定義
def _exec_read_file(args: dict[str, Any]) -> dict[str, Any]:
    """Read a local file."""
    path = args["path"]
    if not _is_path_allowed(path):
        return {"error": f"Access denied: {path} is outside allowed directories. Hint: Use absolute paths under {PRIMARY_WORKSPACE}"}

    p = Path(path).expanduser().resolve()
    if not p.exists():
        return {"error": f"File not found: {path}"}
    if not p.is_file():
        return {"error": f"Not a file: {path}"}
    if p.stat().st_size > MAX_READ_SIZE:
        return {"error": f"File too large: {p.stat().st_size} bytes (max {MAX_READ_SIZE})"}

    try:
        content = p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, ValueError):
        return {"error": f"Cannot read binary file: {path}"}

    # Additional binary detection: null bytes in content
    if "\x00" in content:
        return {"error": f"Binary file detected (contains null bytes): {path}"}

    # Line range filtering
    start = args.get("start_line")
    end = args.get("end_line")
    if start is not None or end is not None:
        lines = content.splitlines(keepends=True)
        start_idx = max(0, (start or 1) - 1)
        end_idx = end or len(lines)
        content = "".join(lines[start_idx:end_idx])
        total = len(lines)
        return {"output": content, "total_lines": total, "range": f"{start_idx+1}-{end_idx}"}

    return {"output": content, "total_lines": content.count("\n") + 1}


# PURPOSE: [L2-auto] _exec_write_file の関数定義
def _exec_write_file(args: dict[str, Any]) -> dict[str, Any]:
    """Write content to a local file."""
    path = args["path"]
    if not _is_path_allowed(path):
        return {"error": f"Access denied: {path} is outside allowed directories. Hint: Use absolute paths under {PRIMARY_WORKSPACE}"}

    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)

    mode = "a" if args.get("append") else "w"
    with p.open(mode, encoding="utf-8") as f:
        f.write(args["content"])

    return {"output": f"Written {len(args['content'])} bytes to {path}", "mode": mode}


# PURPOSE: [L2-auto] _exec_list_directory の関数定義
def _exec_list_directory(args: dict[str, Any]) -> dict[str, Any]:
    """List directory contents."""
    path = args["path"]
    if not _is_path_allowed(path):
        return {"error": f"Access denied: {path} is outside allowed directories. Hint: Use absolute paths under {PRIMARY_WORKSPACE}"}

    p = Path(path).expanduser().resolve()
    if not p.exists():
        return {"error": f"Directory not found: {path}"}
    if not p.is_dir():
        return {"error": f"Not a directory: {path}"}

    raw_depth = args.get("max_depth")
    max_depth = min(raw_depth if isinstance(raw_depth, int) else 1, 3)
    entries: list[dict[str, Any]] = []

    # PURPOSE: [L2-auto] _scan の関数定義
    def _scan(dir_path: Path, depth: int) -> None:
        if depth >= max_depth or len(entries) >= 200:
            return
        try:
            for entry in sorted(dir_path.iterdir()):
                if entry.name.startswith("."):
                    continue  # Skip hidden files
                info: dict[str, Any] = {
                    "name": str(entry.relative_to(p)),
                    "type": "dir" if entry.is_dir() else "file",
                }
                if entry.is_file():
                    info["size"] = entry.stat().st_size
                entries.append(info)
                if entry.is_dir() and depth + 1 < max_depth:
                    _scan(entry, depth + 1)
        except PermissionError:
            pass

    _scan(p, 0)
    return {"entries": entries, "total": len(entries), "path": str(p)}


# PURPOSE: [L2-auto] _exec_search_text の関数定義
def _exec_search_text(args: dict[str, Any]) -> dict[str, Any]:
    """Search for text pattern in files."""
    directory = args["directory"]
    if not _is_path_allowed(directory):
        return {"error": f"Access denied: {directory} is outside allowed directories. Hint: Use absolute paths under {PRIMARY_WORKSPACE}"}

    pattern = args["pattern"]
    file_pattern = args.get("file_pattern", "*")
    max_results = min(args.get("max_results", 50), 100)

    # Use ripgrep if available, fallback to grep
    # --vimgrep: file:line:col:content format (LLM-friendly, not JSON)
    # Note: rg -m N limits per-file, not total. Post-filter to cap total results.
    rg_path = "/usr/bin/rg"
    if Path(rg_path).exists():
        cmd = [rg_path, "--vimgrep", "--glob", file_pattern, pattern, directory]
    else:
        cmd = ["grep", "-rnI", f"--include={file_pattern}", pattern, directory]

    try:
        result = run_utf8(
            cmd, timeout=MAX_CMD_TIMEOUT
        )
        lines = result.stdout.strip().split("\n")[:max_results]
        matches = [line for line in lines if line]
        return {"matches": matches, "count": len(matches), "pattern": pattern}
    except subprocess.TimeoutExpired:
        return {"error": "Search timed out"}


# PURPOSE: [L2-auto] _exec_run_command の関数定義
def _exec_run_command(args: dict[str, Any]) -> dict[str, Any]:
    """Execute a shell command."""
    command = args["command"]
    cwd = args.get("cwd", str(Path.home() / "Sync" / "oikos"))

    if not _is_path_allowed(cwd):
        return {"error": f"Access denied: cwd {cwd} is outside allowed directories. Hint: Use absolute paths under {PRIMARY_WORKSPACE}"}

    # Block dangerous commands
    dangerous = ["rm -rf /", "mkfs", "dd if=", "> /dev/", "chmod -R 777"]
    if any(d in command for d in dangerous):
        return {"error": f"Blocked dangerous command: {command}"}

    try:
        result = run_utf8(
            command,
            shell=True,
            timeout=MAX_CMD_TIMEOUT,
            cwd=cwd,
            extra_env={"PAGER": "cat"},
        )

        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr}"

        # Truncate if too large
        if len(output) > MAX_READ_SIZE:
            output = output[:MAX_READ_SIZE] + f"\n... (truncated, total {len(output)} bytes)"

        return {
            "output": output,
            "exit_code": result.returncode,
            "command": command,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {MAX_CMD_TIMEOUT}s: {command}"}


# --- F2: Git Tools ---


# PURPOSE: [L2-auto] _exec_git_diff の関数定義
def _exec_git_diff(args: dict[str, Any]) -> dict[str, Any]:
    """Show git diff."""
    repo = args.get("repo_path", str(Path.home() / "Sync" / "oikos" / "hegemonikon"))
    if not _is_path_allowed(repo):
        return {"error": f"Access denied: {repo}. Hint: Use absolute paths under {PRIMARY_WORKSPACE}"}

    cmd = ["git", "-C", repo, "diff"]
    if args.get("staged"):
        cmd.append("--cached")
    if args.get("ref"):
        cmd.append(args["ref"])
    cmd.append("--stat")  # Always include stat summary
    if args.get("file_path"):
        cmd.extend(["--", args["file_path"]])

    try:
        # Get stat first
        stat_result = run_utf8(
            cmd, timeout=MAX_CMD_TIMEOUT
        )
        # Get actual diff (without --stat)
        # Build new cmd instead of filtering to avoid accidental removal of
        # user-supplied args that happen to equal "--stat"
        diff_cmd = ["git", "-C", repo, "diff"]
        if args.get("staged"):
            diff_cmd.append("--cached")
        if args.get("ref"):
            diff_cmd.append(args["ref"])
        if args.get("file_path"):
            fp = args["file_path"]
            if isinstance(fp, str):
                diff_cmd.extend(["--", fp])
            elif isinstance(fp, list):
                diff_cmd.append("--")
                diff_cmd.extend(str(f) for f in fp)
        diff_result = run_utf8(
            diff_cmd, timeout=MAX_CMD_TIMEOUT
        )
        output = diff_result.stdout
        if len(output) > MAX_READ_SIZE:
            output = output[:MAX_READ_SIZE] + "\n... (diff truncated)"

        # Include stderr if present (e.g. invalid ref)
        result_dict: dict[str, Any] = {
            "stat": stat_result.stdout.strip(),
            "diff": output,
            "repo": repo,
        }
        stderr = (stat_result.stderr or "") + (diff_result.stderr or "")
        if stderr.strip():
            result_dict["stderr"] = stderr.strip()
        return result_dict
    except subprocess.TimeoutExpired:
        return {"error": "git diff timed out"}


# PURPOSE: [L2-auto] _exec_git_log の関数定義
def _exec_git_log(args: dict[str, Any]) -> dict[str, Any]:
    """Show git log."""
    repo = args.get("repo_path", str(Path.home() / "Sync" / "oikos" / "hegemonikon"))
    if not _is_path_allowed(repo):
        return {"error": f"Access denied: {repo}. Hint: Use absolute paths under {PRIMARY_WORKSPACE}"}

    max_count = min(args.get("max_count", 10), 50)
    oneline = args.get("oneline", True)

    cmd = ["git", "-C", repo, "log", f"-{max_count}"]
    if oneline:
        cmd.append("--oneline")
    else:
        cmd.extend(["--format=%H %an %ad %s", "--date=short"])

    if args.get("file_path"):
        cmd.extend(["--", args["file_path"]])

    try:
        result = run_utf8(
            cmd, timeout=MAX_CMD_TIMEOUT
        )
        result_dict: dict[str, Any] = {
            "output": result.stdout.strip(),
            "count": len(result.stdout.strip().split("\n")),
            "repo": repo,
        }
        if result.stderr and result.stderr.strip():
            result_dict["stderr"] = result.stderr.strip()
        return result_dict
    except subprocess.TimeoutExpired:
        return {"error": "git log timed out"}


# --- F3: Claude Text-based Tool Use ---

# System prompt that teaches Claude how to use tools via text
# F3 Postel's Law: System prompt enforces strict ```tool_call format (send strict),
# while parse_tool_calls_from_text() accepts ```json fallback (receive tolerant).

_TOOL_USE_PROMPT_CACHE: str | None = None


def _load_tool_use_prompt() -> str:
    """Týpos .prompt ファイルからツール使用プロンプトをロードする。"""
    from mekhane.ergasterion.typos.loader import load_typos_prompt
    return load_typos_prompt("tool_use", fallback_text=_FALLBACK_TOOL_USE_PROMPT)


_FALLBACK_TOOL_USE_PROMPT = """You have access to the following tools for interacting with the local file system.
To use a tool, respond with a JSON block in this exact format:

```tool_call
{"name": "tool_name", "args": {"arg1": "value1"}}
```

You can make multiple tool calls in one response. After each tool call, you will receive the results.
When you have enough information, provide your final answer as normal text (without tool_call blocks).

Available tools:
{tool_descriptions}

IMPORTANT:
- Always use absolute paths starting with /home/ or /tmp/
- File operations are restricted to ~/oikos and /tmp
- The main repository is at /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/
- Key directories: kernel/, mekhane/, nous/, hgk/
- Commands have a 30-second timeout
"""


# PURPOSE: [L2-auto] build_tool_descriptions の関数定義
def build_tool_descriptions() -> str:
    """Build human-readable tool descriptions for Claude's system prompt."""
    lines = []
    for tool in TOOL_DEFINITIONS:
        name = tool["name"]
        desc = tool["description"]
        params = tool.get("parameters", {}).get("properties", {})
        required = tool.get("parameters", {}).get("required", [])

        param_lines = []
        for pname, pinfo in params.items():
            req = " (required)" if pname in required else ""
            param_lines.append(f"    - {pname}: {pinfo.get('description', '')}{req}")

        lines.append(f"### {name}\n{desc}")
        if param_lines:
            lines.append("Parameters:")
            lines.extend(param_lines)
        lines.append("")

    return "\n".join(lines)


# PURPOSE: [L2-auto] get_claude_system_prompt の関数定義
def get_claude_system_prompt(extra_instructions: str = "") -> str:
    """Build the complete system prompt for Claude text-based tool use."""
    tool_desc = build_tool_descriptions()
    prompt = _load_tool_use_prompt()
    if "{tool_descriptions}" in prompt:
        prompt = prompt.replace("{tool_descriptions}", tool_desc)
    else:
        prompt = f"{prompt}\n\n{tool_desc}"
    if extra_instructions:
        prompt += f"\n\n{extra_instructions}"
    return prompt


# PURPOSE: [L2-auto] parse_tool_calls_from_text の関数定義
def parse_tool_calls_from_text(text: str) -> list[dict[str, Any]]:
    """Parse tool calls from Claude's text response.

    Looks for ```tool_call blocks containing JSON.
    Falls back to ```json blocks if no tool_call blocks found.

    Returns:
        List of {"name": str, "args": dict} dicts
    """
    # Primary: explicit tool_call blocks
    pattern = r"```tool_call\s*\r?\n(.*?)\r?\n```"
    matches = re.findall(pattern, text, re.DOTALL)

    # Fallback: json blocks containing tool-call-shaped objects
    if not matches:
        json_pattern = r"```json\s*\r?\n(.*?)\r?\n```"
        json_matches = re.findall(json_pattern, text, re.DOTALL)
        for m in json_matches:
            try:
                candidate = json.loads(m.strip())
                # Only accept if it looks like a tool call
                if isinstance(candidate, dict) and "name" in candidate:
                    matches.append(m)
                elif isinstance(candidate, list) and any(
                    isinstance(item, dict) and "name" in item for item in candidate
                ):
                    matches.append(m)
            except json.JSONDecodeError:
                pass

    tool_calls = []
    for match in matches:
        try:
            parsed = json.loads(match.strip())
            # Handle both single dict and array of dicts
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and "name" in item:
                        tool_calls.append({
                            "name": item["name"],
                            "args": item.get("args", {}),
                        })
            elif isinstance(parsed, dict) and "name" in parsed:
                tool_calls.append({
                    "name": parsed["name"],
                    "args": parsed.get("args", {}),
                })
        except json.JSONDecodeError:
            logger.warning("Failed to parse tool call JSON: %s", match[:100])

    return tool_calls


# PURPOSE: [L2-auto] has_tool_calls の関数定義
def has_tool_calls(text: str) -> bool:
    """Check if text contains any tool_call or json blocks with tool calls."""
    if "```tool_call" in text:
        return True
    # Fallback: check json blocks for tool-call-shaped content
    if "```json" in text:
        json_pattern = r"```json\s*\r?\n(.*?)\r?\n```"
        for m in re.findall(json_pattern, text, re.DOTALL):
            try:
                candidate = json.loads(m.strip())
                if isinstance(candidate, dict) and "name" in candidate:
                    return True
                if isinstance(candidate, list) and any(
                    isinstance(item, dict) and "name" in item for item in candidate
                ):
                    return True
            except json.JSONDecodeError:
                pass
    return False


# PURPOSE: [L2-auto] strip_tool_calls の関数定義
def strip_tool_calls(text: str) -> str:
    """Remove tool_call blocks from text, returning only the narrative."""
    return re.sub(r"```tool_call\s*\n.*?\n```", "", text, flags=re.DOTALL).strip()


# --- F4: HGK System Instruction Templates ---

HGK_SYSTEM_TEMPLATES: dict[str, str] = {
    "default": (
        "You are an AI assistant with access to local file system tools. "
        "Use tools to read, write, search files, and run commands as needed. "
        "Always verify file paths before writing. Be precise and efficient."
    ),
    "hgk_citizen": (
        "You are an AI operating within the Hegemonikón framework. "
        "Core principles:\n"
        "1. N-4: Before destructive operations, explain what you plan to do\n"
        "2. N-3: Mark uncertain claims with [推定] or [仮説]\n"
        "3. N-9: Read files before modifying them\n"
        "4. I-1 (Safety): Never delete files without explicit permission\n"
        "5. Zero Entropy: If instructions are ambiguous, ask for clarification\n"
        "6. Japanese output: Respond in Japanese unless code/technical terms\n\n"
        "Workspace: ~/oikos/01_ヘゲモニコン｜Hegemonikon\n"
        "Output language: 日本語"
    ),
    "code_review": (
        "You are a code reviewer with file system access. "
        "Read the specified files, analyze the code, and provide:\n"
        "1. Potential bugs and issues\n"
        "2. Design improvements\n"
        "3. Security concerns\n"
        "4. Performance optimizations\n"
        "Be specific — cite line numbers and file paths."
    ),
    "researcher": (
        "You are a research assistant with access to the local knowledge base. "
        "Search files in ~/oikos for relevant information. "
        "Cite sources with file paths and line numbers. "
        "Distinguish between facts (from files) and inferences (your analysis)."
    ),
    "cross_review": (
        "あなたは独立した技術レビュアーです。"
        "他のAIの分析結果は参照せず、自分の判断で分析してください。\n"
        "ファイルを read_file で読み、以下の観点でレビューしてください:\n"
        "1. 設計の妥当性 — 構造は適切か？ 過剰/不足はないか？\n"
        "2. バグ・ロジック欠陥 — 動作しない/意図と異なるコードはないか？\n"
        "3. 命名・可読性 — 6ヶ月後に読めるか？\n"
        "4. 盲点 — 見落とされているエッジケースや暗黙の前提はないか？\n\n"
        "出力形式:\n"
        "## レビュー結果\n"
        "- **設計**: [所見]\n"
        "- **バグ**: [所見]\n"
        "- **可読性**: [所見]\n"
        "- **盲点**: [所見]\n"
        "- **確信度**: [0-100%] + 根拠\n"
        "- **総合判定**: PASS / WARN / FAIL\n\n"
        "Workspace: ~/oikos/01_ヘゲモニコン｜Hegemonikon\n"
        "Output language: 日本語"
    ),
    "xrev_synthesis": (
        "あなたはクロスモデルレビューの統合分析官です。\n"
        "以下の2つの独立レビュー結果を受け取り、統合分析を行ってください。\n\n"
        "## 統合分析の手順\n"
        "1. **共通懸念**: 両レビュアーが指摘した共通の問題を抽出し、重大度順に並べる\n"
        "2. **対立点**: 片方のみが指摘した問題を列挙し、客観的に妥当性を評価\n"
        "3. **盲点**: どちらのレビュアーも見落としている可能性のある問題を独自に指摘\n"
        "4. **アクションアイテム**: 修正すべき項目を優先度順にリスト化\n\n"
        "## 出力形式\n"
        "### 共通懸念 (重大度順)\n"
        "| # | 問題 | 重大度 | Gemini所見 | Claude所見 |\n\n"
        "### 対立点\n"
        "| # | 問題 | 指摘元 | 妥当性評価 |\n\n"
        "### 盲点 (統合分析官の独自指摘)\n\n"
        "### アクションアイテム (優先度順)\n"
        "| # | 対処 | 優先度 | 対象ファイル |\n\n"
        "### 総合判定: PASS / WARN / FAIL\n\n"
        "Output language: 日本語"
    ),
}


# PURPOSE: [L2-auto] get_system_template の関数定義
def get_system_template(template_name: str) -> str:
    """Get a pre-defined system instruction template."""
    return HGK_SYSTEM_TEMPLATES.get(template_name, HGK_SYSTEM_TEMPLATES["default"])
