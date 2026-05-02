import os
from pathlib import Path

TARGETS = ['.agent', '.agents', '10_知性｜Nous']
ROOT = Path.cwd()

def find_file_by_name(name, search_dirs):
    matches = []
    for d in search_dirs:
        for root, _, files in os.walk(d):
            if name in files:
                p = Path(root) / name
                if not p.is_symlink():
                    matches.append(p)
    return matches

broken = []
for t in TARGETS:
    if not os.path.exists(t): continue
    for root, dirs, files in os.walk(t):
        for name in files + dirs:
            path = Path(root) / name
            if path.is_symlink() and not path.exists():
                broken.append(path)

print(f"Found {len(broken)} broken symlinks.")

fixed = 0
for path in broken:
    basename = path.name
    # Search inside 10_知性｜Nous
    matches = find_file_by_name(basename, ['10_知性｜Nous'])
    
    # Exclude matches that are in old Archive or inside .obsidian if necessary
    matches = [m for m in matches if '.obsidian' not in m.parts and '90_旧構造｜Archive' not in m.parts]
    
    if len(matches) == 1:
        target = matches[0]
        # Calculate relative path
        rel_target = os.path.relpath(target, start=path.parent)
        os.unlink(path)
        os.symlink(rel_target, path)
        print(f"Fixed: {path} -> {rel_target}")
        fixed += 1
    elif len(matches) > 1:
        print(f"Ambiguous target for {path}: {[str(m) for m in matches]}")
    else:
        print(f"No target found for {path}")

print(f"Fixed {fixed} of {len(broken)} broken symlinks.")
