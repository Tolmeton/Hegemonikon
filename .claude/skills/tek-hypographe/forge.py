#!/usr/bin/env python3
"""tek-hypographe: Prompt Forging Engine via Gemini/Codex CLI"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_GEMINI_TIMEOUT = int(os.environ.get("FORGE_GEMINI_TIMEOUT", "120"))
DEFAULT_CODEX_TIMEOUT = int(os.environ.get("FORGE_CODEX_TIMEOUT", "900"))


def run_gemini(prompt: str, timeout_s: int) -> tuple[bool, str]:
    """Try Gemini CLI. Returns (success, output_or_error)."""
    try:
        result = subprocess.run(
            ["gemini", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        if result.returncode == 0 and result.stdout.strip():
            return True, result.stdout
        return False, result.stderr or "Empty response"
    except subprocess.TimeoutExpired:
        return False, f"Gemini timed out after {timeout_s} seconds"
    except Exception as e:
        return False, str(e)


def run_codex(prompt: str, timeout_s: int) -> tuple[bool, str]:
    """Try Codex CLI. Returns (success, output_or_error)."""
    try:
        result = subprocess.run(
            ["codex", "exec", "-"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        if result.returncode == 0 and result.stdout.strip():
            return True, result.stdout
        return False, result.stderr or "Empty response"
    except subprocess.TimeoutExpired:
        return False, f"Codex timed out after {timeout_s} seconds"
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Forge structured Typos prompt")
    parser.add_argument("raw", help="Raw natural language prompt")
    parser.add_argument("-t", "--target", choices=["opus46", "gpt54", "generic"], default="generic")
    parser.add_argument("-f", "--forget", default="", help="π_low hints")
    parser.add_argument("-b", "--backend", choices=["auto", "gemini", "codex"], default="auto")
    parser.add_argument("--gemini-timeout", type=int, default=DEFAULT_GEMINI_TIMEOUT)
    parser.add_argument("--codex-timeout", type=int, default=DEFAULT_CODEX_TIMEOUT)
    args = parser.parse_args()

    meta_path = Path(__file__).parent / "meta_prompt.typos"
    meta = meta_path.read_text()
    prompt = f"{meta}\n\n---\nRAW: {args.raw}\nTARGET: {args.target}\nPI_LOW_HINTS: {args.forget or '(none)'}"

    if args.backend == "gemini":
        ok, out = run_gemini(prompt, args.gemini_timeout)
    elif args.backend == "codex":
        ok, out = run_codex(prompt, args.codex_timeout)
    else:  # auto: gemini first, fallback to codex
        ok, out = run_gemini(prompt, args.gemini_timeout)
        if not ok:
            print(f"[Gemini failed: {out[:100]}... trying Codex]", file=sys.stderr)
            ok, out = run_codex(prompt, args.codex_timeout)

    if not ok:
        print(f"Error: {out}", file=sys.stderr)
        raise SystemExit(1)
    print(out)

if __name__ == "__main__":
    main()
