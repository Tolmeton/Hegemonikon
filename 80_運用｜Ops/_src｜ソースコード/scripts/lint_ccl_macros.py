#!/usr/bin/env python3
"""CCL Macro Linter — 全マクロ定義の CCL 式を一括 lint する CI 用スクリプト。

Usage:
    PYTHONPATH=. .venv/bin/python scripts/lint_ccl_macros.py [--strict]

Exit code:
    0: 全マクロ OK (info のみ)
    1: warning 以上の問題あり (--strict 時)

Origin: 2026-02-23 CCL 演算子混同防止フォローアップ #1
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Hegemonikón ルートからの相対パスで実行
ROOT = Path(__file__).resolve().parent.parent
WF_DIR = ROOT / "nous" / "workflows"

# CCL 式の抽出パターン: > **CCL**: `...` または CCL: `...`
CCL_PATTERN = re.compile(r'[`]([^`]*(?:/[a-z]+)[^`]*)[`]')
# description 行内の CCL 式 (例: "噛む — /s-_/pro_...")
DESC_CCL_PATTERN = re.compile(r'(?:—|:)\s+(/[a-z][\w+\-^!~*_\\\'\"(){}@:|><,.\[\]]*)')


def extract_ccl_from_file(path: Path) -> list[tuple[int, str]]:
    """ファイルから CCL 式を抽出。(行番号, CCL 式) のリスト。"""
    results = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return results

    for i, line in enumerate(lines, 1):
        # > **CCL**: `...` パターン
        if "CCL" in line.upper():
            for m in CCL_PATTERN.finditer(line):
                expr = m.group(1).strip()
                if "/" in expr:
                    results.append((i, expr))
        # description: の CCL
        if line.strip().startswith("description:"):
            for m in DESC_CCL_PATTERN.finditer(line):
                expr = m.group(1).strip()
                if len(expr) > 3:
                    results.append((i, expr))
    return results


def main():
    strict = "--strict" in sys.argv

    try:
        from mekhane.ccl.ccl_linter import lint, LintWarning
    except ImportError:
        print("ERROR: mekhane.ccl.ccl_linter が import できません。PYTHONPATH を確認。")
        sys.exit(2)

    ccl_files = sorted(WF_DIR.glob("ccl-*.md"))
    if not ccl_files:
        print(f"WARNING: {WF_DIR} に ccl-*.md が見つかりません")
        sys.exit(0)

    total_exprs = 0
    total_warnings = 0
    total_errors = 0
    results: list[tuple[str, int, str, list[LintWarning]]] = []

    for f in ccl_files:
        exprs = extract_ccl_from_file(f)
        for line_no, expr in exprs:
            total_exprs += 1
            warnings = lint(expr)
            if warnings:
                results.append((f.name, line_no, expr, warnings))
                for w in warnings:
                    if w.level == "error":
                        total_errors += 1
                    elif w.level == "warning":
                        total_warnings += 1

    # レポート出力
    print(f"═══ CCL Macro Lint Report ═══")
    print(f"ファイル数: {len(ccl_files)}")
    print(f"CCL 式: {total_exprs}")
    print(f"警告: {total_warnings}, エラー: {total_errors}")
    print()

    if results:
        for fname, line_no, expr, warnings in results:
            print(f"  {fname}:{line_no}")
            print(f"    CCL: {expr[:80]}{'...' if len(expr) > 80 else ''}")
            for w in warnings:
                icon = "❌" if w.level == "error" else "⚠️" if w.level == "warning" else "🔍"
                print(f"    {icon} [{w.level}] {w.message}")
            print()
    else:
        print("  ✅ 全マクロ OK — 問題なし")

    # 終了コード
    if strict and (total_warnings > 0 or total_errors > 0):
        sys.exit(1)
    elif total_errors > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
