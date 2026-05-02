#!/usr/bin/env python3
"""xrev — Cross-Model Review CLI.

Automated cross-model code review using Gemini and Claude.
Detects changed files from git, sends to both models for independent review,
then synthesizes results into a unified report.

Usage:
    python scripts/xrev.py                  # Review staged changes
    python scripts/xrev.py --ref HEAD~3     # Review against a ref
    python scripts/xrev.py file1.py file2.py  # Review specific files
    python scripts/xrev.py --dry-run        # Show files, don't review
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from mekhane.ochema.service import OchemaService
from mekhane.ochema.tools import get_system_template


# --- Configuration ---

GEMINI_MODEL = "gemini-3.1-pro-preview"
CLAUDE_MODEL = "MODEL_PLACEHOLDER_M26"  # Claude Opus 4.6
REVIEW_TIMEOUT = 300  # F12: Extended timeout for multi-file analysis
MAX_FILES = 20  # Safety limit
REVIEW_TEMPLATE = "cross_review"
SYNTHESIS_TEMPLATE = "xrev_synthesis"


def get_changed_files(ref: str | None = None, staged: bool = True) -> list[str]:
    """Get list of changed files from git."""
    if ref:
        cmd = ["git", "diff", "--name-only", ref]
    elif staged:
        cmd = ["git", "diff", "--name-only", "--cached"]
    else:
        cmd = ["git", "diff", "--name-only"]

    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    if result.returncode != 0:
        print(f"[ERROR] git command failed: {result.stderr}", file=sys.stderr)
        return []

    files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    # Resolve to absolute paths and filter to existing files
    resolved = []
    for f in files:
        p = PROJECT_ROOT / f
        if p.exists() and p.is_file():
            resolved.append(str(p))
    return resolved[:MAX_FILES]


def build_review_prompt(files: list[str]) -> str:
    """Build the review prompt with file list."""
    file_list = "\n".join(f"- {f}" for f in files)
    return (
        f"以下の{len(files)}ファイルを read_file で読み、独立したコードレビューを行ってください。\n\n"
        f"## レビュー対象ファイル\n{file_list}\n\n"
        "## レビュー観点\n"
        "1. 設計の妥当性 — 構造は適切か？ 過剰/不足はないか？\n"
        "2. バグ・ロジック欠陥 — 動作しない/意図と異なるコードはないか？\n"
        "3. 命名・可読性 — 6ヶ月後に読めるか？\n"
        "4. 盲点 — 見落とされているエッジケースや暗黙の前提はないか？"
    )


def review_with_model(
    service: OchemaService,
    model: str,
    prompt: str,
    label: str,
) -> tuple[str, str, float]:
    """Run review with a single model. Returns (label, response_text, elapsed)."""
    start = time.monotonic()
    template = get_system_template(REVIEW_TEMPLATE)
    try:
        response = service.ask_with_tools(
            message=prompt,
            model=model,
            system_instruction=template,
            timeout=REVIEW_TIMEOUT,
            max_iterations=15,
        )
        elapsed = time.monotonic() - start
        return label, response.text, elapsed
    except Exception as e:
        elapsed = time.monotonic() - start
        return label, f"[ERROR] {type(e).__name__}: {e}", elapsed


def synthesize(
    service: OchemaService,
    gemini_result: str,
    claude_result: str,
) -> str:
    """Synthesize two reviews into a unified report."""
    template = get_system_template(SYNTHESIS_TEMPLATE)
    prompt = (
        "## Gemini 3.1 Pro のレビュー結果\n\n"
        f"{gemini_result}\n\n"
        "---\n\n"
        "## Claude Opus 4.6 のレビュー結果\n\n"
        f"{claude_result}\n\n"
        "---\n\n"
        "上記の2つの独立レビュー結果を統合分析してください。"
    )
    try:
        response = service.ask_with_tools(
            message=prompt,
            model=GEMINI_MODEL,  # Use Gemini for synthesis (faster)
            system_instruction=template,
            timeout=REVIEW_TIMEOUT,
        )
        return response.text
    except Exception as e:
        return f"[ERROR] Synthesis failed: {type(e).__name__}: {e}"


def write_report(
    output_path: Path,
    files: list[str],
    gemini_result: str,
    gemini_time: float,
    claude_result: str,
    claude_time: float,
    synthesis: str,
) -> None:
    """Write the full report to a markdown file."""
    file_list = "\n".join(f"- `{f}`" for f in files)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    report = f"""# Cross-Model Review Report

**Date**: {timestamp}
**Files**: {len(files)}

## レビュー対象
{file_list}

---

## Gemini 3.1 Pro ({gemini_time:.1f}s)

{gemini_result}

---

## Claude Opus 4.6 ({claude_time:.1f}s)

{claude_result}

---

## 統合分析

{synthesis}
"""
    output_path.write_text(report, encoding="utf-8")
    print(f"\n📄 Report saved: {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cross-Model Review CLI — Gemini × Claude independent review"
    )
    parser.add_argument("files", nargs="*", help="Specific files to review")
    parser.add_argument("--ref", help="Git ref to compare against (e.g., HEAD~3, main)")
    parser.add_argument("--unstaged", action="store_true", help="Review unstaged changes")
    parser.add_argument("--dry-run", action="store_true", help="Show files without reviewing")
    parser.add_argument(
        "--output", "-o",
        default=str(PROJECT_ROOT / "output" / "xrev_report.md"),
        help="Output report path (default: output/xrev_report.md)",
    )
    args = parser.parse_args()

    # Step 1: Determine files
    if args.files:
        files = [str(Path(f).resolve()) for f in args.files if Path(f).exists()]
    else:
        files = get_changed_files(ref=args.ref, staged=not args.unstaged)

    if not files:
        print("❌ No files to review. Stage changes or specify files.", file=sys.stderr)
        return 1

    print(f"🔍 Cross-Model Review: {len(files)} file(s)")
    for f in files:
        print(f"   📄 {f}")

    if args.dry_run:
        print("\n🏁 Dry run complete.")
        return 0

    # Step 2: Initialize service
    print("\n⚡ Initializing Ochema service...")
    service = OchemaService()
    prompt = build_review_prompt(files)

    # Step 3: Parallel review (F12: timeout=300)
    print("🚀 Starting parallel reviews...")
    print(f"   🟦 Gemini 3.1 Pro (timeout: {REVIEW_TIMEOUT}s)")
    print(f"   🟪 Claude Opus 4.6 (timeout: {REVIEW_TIMEOUT}s)")

    results: dict[str, tuple[str, float]] = {}
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(
                review_with_model, service, GEMINI_MODEL, prompt, "gemini"
            ): "gemini",
            executor.submit(
                review_with_model, service, CLAUDE_MODEL, prompt, "claude"
            ): "claude",
        }
        for future in as_completed(futures):
            label, text, elapsed = future.result()
            results[label] = (text, elapsed)
            icon = "🟦" if label == "gemini" else "🟪"
            print(f"   {icon} {label} done ({elapsed:.1f}s)")

    gemini_text, gemini_time = results.get("gemini", ("", 0.0))
    claude_text, claude_time = results.get("claude", ("", 0.0))

    # Step 4: Synthesis
    print("🔄 Synthesizing reviews...")
    synthesis_text = synthesize(service, gemini_text, claude_text)

    # Step 5: Write report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_report(
        output_path, files,
        gemini_text, gemini_time,
        claude_text, claude_time,
        synthesis_text,
    )

    print("✅ Cross-Model Review complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
