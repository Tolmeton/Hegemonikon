# PROOF: mekhane/scripts/update_hegemonikon.py
# PURPOSE: scripts モジュールの update_hegemonikon
from mekhane.paths import MEKHANE_SRC, MNEME_STATE
import os
from pathlib import Path

SRC_DIR = MEKHANE_SRC / "mekhane"

def process_file(filepath: Path):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    
    # We want to replace .hegemonikon with 05_状態｜State BUT ONLY when it's part of a path.
    # We saw these patterns in grep:
    # 1. / ".hegemonikon" -> but not if preceded by Path.home() / directly!
    #    Lookarounds to ensure it's preceded by "mneme"
    replacements = [
        ('"mneme" / "05_状態｜State"', '"mneme" / "05_状態｜State"'),
        ("'mneme' / '05_状態｜State'", "'mneme' / '05_状態｜State'"),
        ('str(MNEME_STATE)', 'str(MNEME_STATE)'),
        ('M:\\\\Brain\\\\.hegemonikon', 'M:\\\\Brain\\\\05_状態｜State'),
        ('M:\\Brain\\05_状態｜State', 'M:\\Brain\\05_状態｜State')
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
        
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {filepath.relative_to(SRC_DIR)}")

if __name__ == "__main__":
    for root, dirs, files in os.walk(SRC_DIR):
        for file in files:
            if file.endswith('.py') or file.endswith('.md'):
                process_file(Path(root) / file)
