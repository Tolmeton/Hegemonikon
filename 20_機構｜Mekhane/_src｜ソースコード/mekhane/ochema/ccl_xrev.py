#!/usr/bin/env python3
# PROOF: mekhane/ochema/ccl_xrev.py
# PURPOSE: ochema モジュールの ccl_xrev
"""ccl_xrev — Cross-Model Review Automation Script.

Usage:
    python ccl_xrev.py file1.py file2.py ...
    python ccl_xrev.py --git-diff          # Review changed files
    python ccl_xrev.py --help

Architecture:
    1. Collect target files
    2. Send to Gemini + Claude in parallel via OchemaService.ask_with_tools()
    3. Merge results with xrev_synthesis template
    4. Output structured report

Requires: OchemaService running (MCP ochema server)
"""


from __future__ import annotations
import argparse
import asyncio
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# --- Default models ---
GEMINI_MODEL = "gemini-3.1-pro-preview"
CLAUDE_MODEL = "MODEL_PLACEHOLDER_M26"  # Claude Opus 4.6

# --- Review prompt template ---

_REVIEW_PROMPT_CACHE: str | None = None


def _load_review_prompt() -> str:
    """Týpos .prompt ファイルからレビュープロンプトをロードする。"""
    from mekhane.ergasterion.typos.loader import load_typos_prompt
    return load_typos_prompt("ccl_xrev", fallback_text=_FALLBACK_REVIEW_PROMPT)


_FALLBACK_REVIEW_PROMPT = """\
以下のファイルを read_file で読み、独立したコードレビューを行ってください。

## レビュー対象ファイル
{file_list}

## レビュー観点
1. 設計の妥当性 — 構造は適切か？ 過剰/不足はないか？
2. バグ・ロジック欠陥 — 動作しない/意図と異なるコードはないか？
3. 命名・可読性 — 6ヶ月後に読めるか？
4. 盲点 — 見落とされているエッジケースや暗黙の前提はないか？
"""


# PURPOSE: [L2-auto] get_changed_files の関数定義
def get_changed_files(repo_path: str = ".") -> list[str]:
    """Get list of changed files from git diff."""
    result = subprocess.run(
        ["git", "-C", repo_path, "diff", "--name-only", "HEAD"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        # Fall back to staged
        result = subprocess.run(
            ["git", "-C", repo_path, "diff", "--name-only", "--cached"],
            capture_output=True, text=True
        )
    files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    # Convert to absolute paths
    repo = Path(repo_path).resolve()
    return [str(repo / f) for f in files]


# PURPOSE: [L2-auto] build_review_prompt の関数定義
def build_review_prompt(files: list[str]) -> str:
    """Build the review prompt with file list."""
    file_list = "\n".join(f"- {f}" for f in files)
    template = _load_review_prompt()
    return template.format(file_list=file_list) if "{file_list}" in template else f"{template}\n\n{file_list}"


# PURPOSE: [L2-auto] run_review の非同期処理定義
async def run_review(
    files: list[str],
    gemini_model: str = GEMINI_MODEL,
    claude_model: str = CLAUDE_MODEL,
    max_iterations: int = 10,
    thinking_budget: int = 32768,
) -> dict[str, str]:
    """Run cross-model review.

    Returns dict with keys: gemini_review, claude_review, file_list
    Note: Actual execution requires OchemaService MCP.
    This function generates the prompts and parameters for manual or MCP invocation.
    """
    prompt = build_review_prompt(files)

    return {
        "file_list": "\n".join(files),
        "prompt": prompt,
        "gemini_call": {
            "message": prompt,
            "model": gemini_model,
            "system_instruction": "cross_review",
            "max_iterations": max_iterations,
            "thinking_budget": thinking_budget,
        },
        "claude_call": {
            "message": prompt,
            "model": claude_model,
            "system_instruction": "cross_review",
            "max_iterations": max_iterations,
        },
        "synthesis_template": "xrev_synthesis",
    }


# PURPOSE: [L2-auto] main の関数定義
def main():
    parser = argparse.ArgumentParser(
        description="Cross-Model Review (ccl-xrev) automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python ccl_xrev.py tools.py test_tools.py
  python ccl_xrev.py --git-diff
  python ccl_xrev.py --dry-run *.py
""",
    )
    parser.add_argument("files", nargs="*", help="Files to review")
    parser.add_argument("--git-diff", action="store_true", help="Review git-changed files")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts without executing")
    parser.add_argument("--gemini-model", default=GEMINI_MODEL)
    parser.add_argument("--claude-model", default=CLAUDE_MODEL)

    args = parser.parse_args()

    # Collect files
    if args.git_diff:
        files = get_changed_files()
    elif args.files:
        files = [str(Path(f).resolve()) for f in args.files]
    else:
        parser.print_help()
        sys.exit(1)

    if not files:
        print("No files to review.", file=sys.stderr)
        sys.exit(1)

    print(f"📋 Review targets ({len(files)} files):")
    for f in files:
        print(f"  - {f}")

    # Generate review config
    config = asyncio.run(run_review(
        files,
        gemini_model=args.gemini_model,
        claude_model=args.claude_model,
    ))

    if args.dry_run:
        import json
        print("\n--- Gemini call ---")
        print(json.dumps(config["gemini_call"], indent=2, ensure_ascii=False))
        print("\n--- Claude call ---")
        print(json.dumps(config["claude_call"], indent=2, ensure_ascii=False))
        print(f"\n--- Synthesis template: {config['synthesis_template']} ---")
    else:
        print("\n⚠️  Full automation requires MCP ochema server.")
        print("Use the following in IDE:")
        print(f"\n  mcp_ochema_ask_with_tools(**{config['gemini_call']})")
        print(f"  mcp_ochema_ask_with_tools(**{config['claude_call']})")
        print(f"\n  Synthesize with: system_instruction=\"{config['synthesis_template']}\"")


if __name__ == "__main__":
    main()
