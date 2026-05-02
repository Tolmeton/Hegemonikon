#!/usr/bin/env python3
"""
PROOF Line Synchronizer
(I-2: 36 Issue の根本原因である「手動PROOF行の維持崩壊」を解決するスクリプト)

各Pythonファイルの1行目にある `# PROOF: ` 行を検証・自動アップデートする。
ファイルパスが実際の位置と異なる場合は修正する。

Usage:
  python scripts/proof_sync.py [--dry-run]
"""

import sys
from pathlib import Path
import re
import argparse

ROOT_DIR = Path(__file__).parent.parent
PROOF_PATTERN = re.compile(r"^# PROOF:\s*\[(L[^\]]+)\]\s*<-\s*([^\s]+)(\s.*)?$")


def sync_proof_lines(dry_run: bool = False):
    changed_count = 0
    total_count = 0
    error_count = 0

    print(f"Scanning Python files in {ROOT_DIR} ...")
    
    # .venv は除外
    target_files = [f for f in ROOT_DIR.rglob("*.py") if ".venv" not in f.parts]
    total_count = len(target_files)
    
    for filepath in target_files:
        try:
            rel_path = filepath.relative_to(ROOT_DIR)
            rel_str = str(rel_path)
            
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.startswith("# PROOF:"):
                # PROOF 行がない場合は一旦スキップするか、デフォルトを入れるか。
                # 現状は「既存のPROOF行のパス修正」にフォーカスする。
                continue

            lines = content.split("\n", 1)
            first_line = lines[0]
            rest_of_content = lines[1] if len(lines) > 1 else ""

            match = PROOF_PATTERN.match(first_line)
            if match:
                level_tag = match.group(1)
                declared_path = match.group(2)
                extra = match.group(3) or ""
                
                # 宣言されているパスと実際のパスが違う場合 (ディレクトリの移動等で壊れたケース)
                # あるいはパスがファイル名を含んでいなかった場合 (< - mekhane/anamnesis/ などの修正)
                expected_declared = rel_str
                
                # 'tests/' などの場合はパスが少し違うかもしれないが、原則完全一致を目指す
                if declared_path != expected_declared:
                    new_proof = f"# PROOF: [{level_tag}] <- {expected_declared}{extra}"
                    
                    if not dry_run:
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(new_proof + "\n" + rest_of_content)
                    
                    print(f"[MODIFIED] {rel_str}")
                    print(f"  Old: {first_line}")
                    print(f"  New: {new_proof}")
                    changed_count += 1

        except Exception as e:
            print(f"[ERROR] Could not process {filepath}: {e}")
            error_count += 1
            
    print("-" * 40)
    print(f"Total Python files: {total_count}")
    pattern_matched_changed = changed_count
    print(f"Files to modify: {pattern_matched_changed}")
    print(f"Errors: {error_count}")
    if dry_run:
        print("[DRY RUN] No files were actually modified.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synchronize PROOF lines in Python files.")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without applying them.")
    args = parser.parse_args()
    
    sync_proof_lines(dry_run=args.dry_run)
