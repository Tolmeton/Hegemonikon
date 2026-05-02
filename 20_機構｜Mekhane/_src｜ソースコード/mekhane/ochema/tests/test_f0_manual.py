#!/usr/bin/env python3
# PROOF: mekhane/ochema/tests/test_f0_manual.py
# PURPOSE: ochema モジュールの f0_manual に対するテスト
"""F0 Tool Use — 手動検証スクリプト.

Usage:
    cd ~/oikos/01_ヘゲモニコン｜Hegemonikon
    PYTHONPATH=. .venv/bin/python mekhane/ochema/tests/test_f0_manual.py

テスト内容:
  1. tools.py ユニットテスト (セキュリティ、各ツール)
  2. ask_with_tools 統合テスト (実 API — Cortex 認証必須)
"""
from __future__ import annotations
import sys
sys.path.insert(0, ".")

from mekhane.ochema.tools import execute_tool, _is_path_allowed

def test_tools():
    print("=" * 50)
    print("F0 Tool Use — 検証")
    print("=" * 50)

    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            print(f"  ✓ {name}")
            passed += 1
        else:
            print(f"  ✗ {name}")
            failed += 1

    # --- Security ---
    print("\n[1] Security")
    check("empty path denied", not _is_path_allowed(""))
    check("/etc/passwd denied", not _is_path_allowed("/etc/passwd"))
    check("/root denied", not _is_path_allowed("/root/.ssh"))
    check("~/oikos allowed", _is_path_allowed("/home/makaron8426/Sync/oikos/test"))
    check("/tmp allowed", _is_path_allowed("/tmp/test"))

    # --- read_file ---
    print("\n[2] read_file")
    r = execute_tool("read_file", {"path": "/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/pyproject.toml"})
    check("can read pyproject.toml", "output" in r)
    check("has content", len(r.get("output", "")) > 10)

    r = execute_tool("read_file", {"path": "/etc/passwd"})
    check("denies /etc/passwd", "error" in r and "denied" in r["error"].lower())

    r = execute_tool("read_file", {"path": "/home/makaron8426/Sync/oikos/nonexistent.txt"})
    check("handles missing file", "error" in r)

    # --- list_directory ---
    print("\n[3] list_directory")
    r = execute_tool("list_directory", {"path": "/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/ochema"})
    check("lists ochema dir", "entries" in r)
    check("finds tools.py", any(e["name"] == "tools.py" for e in r.get("entries", [])))

    # --- search_text ---
    print("\n[4] search_text")
    r = execute_tool("search_text", {
        "pattern": "ask_with_tools",
        "directory": "/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/ochema",
        "file_pattern": "*.py",
    })
    check("finds ask_with_tools", r.get("count", 0) > 0)

    # --- run_command ---
    print("\n[5] run_command")
    r = execute_tool("run_command", {"command": "echo hello", "cwd": "/tmp"})
    check("echo works", "hello" in r.get("output", ""))
    check("exit code 0", r.get("exit_code") == 0)

    r = execute_tool("run_command", {"command": "rm -rf /", "cwd": "/tmp"})
    check("blocks rm -rf /", "error" in r and "blocked" in r["error"].lower())

    # --- write_file ---
    print("\n[6] write_file")
    r = execute_tool("write_file", {"path": "/tmp/f0_test.txt", "content": "hello from F0"})
    check("writes to /tmp", "output" in r)

    r = execute_tool("read_file", {"path": "/tmp/f0_test.txt"})
    check("reads back", r.get("output", "").strip() == "hello from F0")

    r = execute_tool("write_file", {"path": "/etc/evil.txt", "content": "hack"})
    check("denies write to /etc", "error" in r)

    # --- Summary ---
    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("✓ All tools tests passed!")
    return failed == 0


def test_api_integration():
    """Test ask_with_tools with real API (requires Cortex auth)."""
    print("\n" + "=" * 50)
    print("F0 API Integration Test")
    print("=" * 50)

    try:
        from mekhane.ochema.service import OchemaService
        svc = OchemaService.get()

        print("\n[7] ask_with_tools — 実API テスト")
        print("  Calling Gemini with tool use...")
        result = svc.ask_with_tools(
            "~/oikos/01_ヘゲモニコン｜Hegemonikon/pyproject.toml の [project] セクションの name と version を教えて。",
            model="gemini-3-flash-preview",
            max_iterations=5,
            timeout=30,
        )
        print(f"  Model: {result.model}")
        print(f"  Text: {result.text[:200]}...")
        print(f"  Tokens: {result.token_usage}")
        print("  ✓ API integration test passed!")
        return True

    except Exception as e:
        print(f"Ignored exception: {e}")
        print(f"  ✗ API test failed: {e}")
        return False


if __name__ == "__main__":
    ok = test_tools()
    if "--api" in sys.argv:
        ok = test_api_integration() and ok
    sys.exit(0 if ok else 1)
