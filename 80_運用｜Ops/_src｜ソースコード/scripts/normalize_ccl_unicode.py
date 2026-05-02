#!/usr/bin/env python3
"""CCL マクロの未定義 Unicode 演算子を一括正規化するスクリプト。"""
from pathlib import Path
import re

WF_DIR = Path(__file__).resolve().parent.parent / "nous" / "workflows"

replacements = [
    ("×2", "N=2"),
    ("×3", "N=3"),
    ("×N", "N=N"),
    ("[✓]", "[pass]"),
    ("[∅]", "[null]"),
]

changed = 0
for f in sorted(WF_DIR.glob("ccl-*.md")):
    text = f.read_text(encoding="utf-8")
    new_text = text
    for old, new in replacements:
        new_text = new_text.replace(old, new)
    if new_text != text:
        f.write_text(new_text, encoding="utf-8")
        changed += 1
        print(f"UPDATED: {f.name}")

print(f"\n{changed} files updated")
