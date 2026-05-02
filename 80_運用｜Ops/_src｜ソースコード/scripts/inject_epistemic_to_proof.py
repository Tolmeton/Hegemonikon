#!/usr/bin/env python3
"""
F7: Epistemic Status → PROOF.md Injector

PURPOSE: epistemic_status.yaml のパッチ情報を、関連する PROOF.md に
「認識論的地位」セクションとして自動注入する。

- 各パッチの file フィールドから所属ディレクトリを特定
- そのディレクトリの PROOF.md に認識論的地位セクションを追加/更新
- 冪等: 何度実行しても同じ結果

Usage:
    python scripts/inject_epistemic_to_proof.py          # Dry run
    python scripts/inject_epistemic_to_proof.py --apply  # 実適用
"""

import sys
from pathlib import Path
from collections import defaultdict

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = PROJECT_ROOT / "kernel" / "epistemic_status.yaml"

# Section markers for idempotent injection
SECTION_START = "<!-- EPISTEMIC_STATUS_START -->"
SECTION_END = "<!-- EPISTEMIC_STATUS_END -->"


def load_registry() -> dict:
    """Load epistemic_status.yaml"""
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def group_patches_by_directory(patches: dict) -> dict[str, list[tuple[str, dict]]]:
    """パッチをファイルが属するディレクトリでグループ化"""
    groups: dict[str, list[tuple[str, dict]]] = defaultdict(list)

    for patch_id, patch in patches.items():
        file_path = patch.get("file", "")
        if not file_path:
            continue

        # Determine the directory containing the file
        parts = Path(file_path).parts
        if len(parts) >= 2:
            # Use the first two directory levels (e.g., kernel/, nous/skills/)
            dir_path = str(Path(*parts[:-1]))
        else:
            dir_path = "."

        groups[dir_path].append((patch_id, patch))

    return dict(groups)


def generate_epistemic_section(patches: list[tuple[str, dict]]) -> str:
    """認識論的地位セクションを生成"""
    lines = [
        "",
        SECTION_START,
        "",
        "## 認識論的地位 (Epistemic Status)",
        "",
        "> 自動生成: `epistemic_status.yaml` から注入",
        "",
        "| ID | 主張 | 地位 | 反証条件 |",
        "|:---|:-----|:-----|:---------|",
    ]

    status_emoji = {
        "empirical": "🟢",
        "reference": "🔵",
        "analogue": "🟡",
        "hypothesis": "🔴",
    }

    for patch_id, patch in patches:
        status = patch.get("status", "unknown")
        emoji = status_emoji.get(status, "⚪")
        claim = patch.get("claim", "")[:60]
        falsification = patch.get("falsification", "")[:80]
        lines.append(
            f"| {patch_id} | {claim} | {emoji} {status} | {falsification} |"
        )

    lines.extend([
        "",
        SECTION_END,
        "",
    ])

    return "\n".join(lines)


def inject_to_proof(proof_path: Path, section_content: str, apply: bool = False) -> str:
    """PROOF.md にセクションを注入 (冪等)"""
    if not proof_path.exists():
        return f"  ⚠️ PROOF.md not found: {proof_path}"

    content = proof_path.read_text(encoding="utf-8")

    # Remove existing section if present
    if SECTION_START in content:
        start_idx = content.index(SECTION_START)
        if SECTION_END in content:
            end_idx = content.index(SECTION_END) + len(SECTION_END)
            # Also remove any trailing newline
            if end_idx < len(content) and content[end_idx] == "\n":
                end_idx += 1
            content = content[:start_idx] + content[end_idx:]

    # Find insertion point (before the last --- or at end)
    # Insert before the final italicized line or at end
    insertion_point = len(content.rstrip())
    content_stripped = content.rstrip()

    # Try to insert before concluding remarks
    last_hr = content_stripped.rfind("\n---\n")
    if last_hr > 0:
        # Check if there's content after the last HR that looks like a conclusion
        after_hr = content_stripped[last_hr + 5:].strip()
        if after_hr and len(after_hr) < 200:  # Short concluding remark
            insertion_point = last_hr

    new_content = (
        content[:insertion_point].rstrip() + "\n" +
        section_content +
        content[insertion_point:].lstrip("\n")
    )

    if apply:
        proof_path.write_text(new_content, encoding="utf-8")
        return f"  ✅ Updated: {proof_path}"
    else:
        return f"  📝 Would update: {proof_path}"


def main():
    apply = "--apply" in sys.argv

    print("=" * 60)
    print(f"F7: Epistemic Status → PROOF.md {'(APPLY)' if apply else '(DRY RUN)'}")
    print("=" * 60)

    registry = load_registry()
    patches = registry.get("patches", {})
    print(f"\nTotal patches: {len(patches)}")

    groups = group_patches_by_directory(patches)
    print(f"Target directories: {len(groups)}")
    print()

    fallback_patches: dict[str, list[tuple[str, dict]]] = {}

    for dir_path, dir_patches in sorted(groups.items()):
        print(f"--- {dir_path}/ ({len(dir_patches)} patches) ---")

        # Find PROOF.md in this directory, fallback to kernel/PROOF.md
        proof_path = PROJECT_ROOT / dir_path / "PROOF.md"
        if not proof_path.exists():
            # Fallback: collect these patches under kernel/PROOF.md
            fallback_key = "kernel"
            if fallback_key not in fallback_patches:
                fallback_patches[fallback_key] = []
            fallback_patches[fallback_key].extend(dir_patches)
            print(f"  ↳ Fallback to kernel/PROOF.md ({len(dir_patches)} patches)")
            continue

        section = generate_epistemic_section(dir_patches)
        result = inject_to_proof(proof_path, section, apply=apply)
        print(result)
        print()

    # Process fallback patches
    for fallback_dir, fb_patches in fallback_patches.items():
        proof_path = PROJECT_ROOT / fallback_dir / "PROOF.md"
        if proof_path.exists():
            # Merge with existing patches for this directory
            existing = groups.get(fallback_dir, [])
            all_patches = existing + fb_patches
            # Deduplicate
            seen = set()
            unique_patches = []
            for pid, p in all_patches:
                if pid not in seen:
                    seen.add(pid)
                    unique_patches.append((pid, p))
            section = generate_epistemic_section(unique_patches)
            print(f"--- {fallback_dir}/ (合計 {len(unique_patches)} patches, fallback含む) ---")
            result = inject_to_proof(proof_path, section, apply=apply)
            print(result)
            print()

    if not apply:
        print("💡 実適用するには: python scripts/inject_epistemic_to_proof.py --apply")


if __name__ == "__main__":
    main()
