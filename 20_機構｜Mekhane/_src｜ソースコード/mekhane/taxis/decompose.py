#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/taxis/ A0→G関手(第一原理分解)が必要→decomposeが担う
"""
PROOF: [L2/インフラ] このファイルは存在しなければならない

P3 → /eat v3.0 の G 関手（第一原理分解）を操作的にサポートする
   → HGK 内部対象から構造を剥いで最小チャンクに分解する CLI ツール

G(Y) = Y の構造を列挙 → 全構造を忘却 → 原子的チャンクのリスト

Lineage: /bou+ P3 (2026-02-10) — G のツール化
"""

import argparse
import json
import re
import sys
import yaml
from pathlib import Path
from typing import Any

# --- Constants ---

_HEGEMONIKON_ROOT = Path(__file__).resolve().parent.parent.parent
_WORKFLOWS_DIR = _HEGEMONIKON_ROOT / "nous" / "workflows"
_SKILLS_DIR = _HEGEMONIKON_ROOT / "nous" / "skills"
_KERNEL_DIR = _HEGEMONIKON_ROOT / "kernel"

# Structure markers in HGK workflow/skill files
_STRUCTURE_KEYS = [
    "hegemonikon",      # Series membership (e.g., "Telos", "Methodos")
    "modules",          # Theorem references (e.g., [O1, O2])
    "skill_ref",        # Skill references
    "derivatives",      # Derivative modes
    "trigonon",         # Trigonon structure (series, type, coordinates, bridge)
    "cognitive_algebra", # +/-/* modifiers
    "ccl_signature",    # CCL expression
    "category_theory",  # Category-theoretic metadata
    "absorbed",         # Absorbed techniques
    "sel_enforcement",  # SEL rules
    "related",          # X-series relations
]


# PURPOSE: decompose の extract frontmatter 処理を実行する
def extract_frontmatter(filepath: Path) -> dict[str, Any] | None:
    """Extract YAML frontmatter from a markdown file."""
    try:
        content = filepath.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return None
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None
        return yaml.safe_load(parts[1])
    except Exception:  # noqa: BLE001
        return None


# PURPOSE: decompose の extract body concepts 処理を実行する
def extract_body_concepts(filepath: Path) -> list[str]:
    """
    Extract atomic concepts from markdown body (headings, bold terms).
    This is a heuristic extraction, not exhaustive.
    """
    try:
        content = filepath.read_text(encoding="utf-8")
        # Skip frontmatter
        parts = content.split("---", 2)
        body = parts[2] if len(parts) >= 3 else content

        concepts = []

        # Extract ## headings as concepts
        for match in re.finditer(r"^##\s+(.+)$", body, re.MULTILINE):
            heading = match.group(1).strip()
            # Remove markdown formatting
            heading = re.sub(r"[*_`#]", "", heading).strip()
            if heading and len(heading) < 80:
                concepts.append(heading)

        return concepts
    except Exception:  # noqa: BLE001
        return []


# PURPOSE: decompose の decompose 処理を実行する
def decompose(target: str) -> dict[str, Any]:
    """
    G(Y): Apply the forgetful functor to an HGK internal object.

    Strips all HGK structure and returns atomic concept chunks.

    Args:
        target: Name of the WF/Skill/Kernel doc (e.g., "eat", "syn", "ousia")

    Returns:
        dict with:
          - target: input name
          - filepath: resolved file path
          - structures: dict of HGK structures found (what G forgets)
          - chunks: list of atomic concepts (what G preserves)
          - chunk_count: number of chunks
    """

    # Resolve target to file path
    filepath = _resolve_target(target)
    if filepath is None:
        return {
            "target": target,
            "error": f"Target '{target}' not found in workflows, skills, or kernel",
            "searched": [
                str(_WORKFLOWS_DIR),
                str(_SKILLS_DIR),
                str(_KERNEL_DIR),
            ],
        }

    # Phase 1: List all structures (what G will forget)
    fm = extract_frontmatter(filepath)
    structures = {}
    if fm:
        for key in _STRUCTURE_KEYS:
            if key in fm:
                structures[key] = fm[key]

    # Phase 2: Strip structures → extract atomic concepts
    chunks = []

    # From description (if exists in frontmatter)
    if fm and "description" in fm:
        chunks.append(fm["description"])

    # From body headings/concepts
    body_concepts = extract_body_concepts(filepath)
    chunks.extend(body_concepts)

    # Phase 3: Return G(Y) = chunks (structures forgotten)
    return {
        "target": target,
        "filepath": str(filepath),
        "structures": structures,
        "structure_count": len(structures),
        "chunks": chunks,
        "chunk_count": len(chunks),
    }


# PURPOSE: [L2-auto] _resolve_target の関数定義
def _resolve_target(target: str) -> Path | None:
    """Resolve target name to file path, searching WF → Skill → Kernel."""
    # Strip leading slash
    target = target.lstrip("/")

    # Search workflows
    wf_path = _WORKFLOWS_DIR / f"{target}.md"
    if wf_path.exists():
        return wf_path

    # Search skills (look for SKILL.md in subdirectories)
    for skill_dir in _SKILLS_DIR.iterdir():
        if skill_dir.is_dir():
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists() and target.lower() in skill_dir.name.lower():
                return skill_file

    # Search kernel
    kernel_path = _KERNEL_DIR / f"{target}.md"
    if kernel_path.exists():
        return kernel_path

    return None


# --- CLI Commands ---


# PURPOSE: decompose の cmd decompose 処理を実行する
def cmd_decompose(args: argparse.Namespace) -> int:
    """G(Y): Decompose an HGK internal object into atomic chunks."""
    result = decompose(args.target)

    if "error" in result:
        print(f"❌ {result['error']}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    # Human-readable output
    print(f"━━━ G({args.target}): 第一原理分解 ━━━\n")
    print(f"📂 {result['filepath']}\n")

    print("━━━ 忘却される構造 ━━━\n")
    if result["structures"]:
        for key, value in result["structures"].items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            elif isinstance(value, list):
                print(f"  {key}: {', '.join(str(v) for v in value)}")
            else:
                print(f"  {key}: {value}")
    else:
        print("  (構造なし)")

    print(f"\n━━━ 残る原子チャンク ({result['chunk_count']}個) ━━━\n")
    for i, chunk in enumerate(result["chunks"], 1):
        print(f"  {i}. {chunk}")

    print(f"\n📊 構造数: {result['structure_count']} → チャンク数: {result['chunk_count']}")
    return 0


# PURPOSE: decompose の cmd compare 処理を実行する
def cmd_compare(args: argparse.Namespace) -> int:
    """Compare G(A) and G(B) — find shared atomic chunks."""
    result_a = decompose(args.target_a)
    result_b = decompose(args.target_b)

    if "error" in result_a:
        print(f"❌ A: {result_a['error']}", file=sys.stderr)
        return 1
    if "error" in result_b:
        print(f"❌ B: {result_b['error']}", file=sys.stderr)
        return 1

    chunks_a = set(result_a["chunks"])
    chunks_b = set(result_b["chunks"])
    shared = chunks_a & chunks_b
    only_a = chunks_a - chunks_b
    only_b = chunks_b - chunks_a

    if args.json:
        print(json.dumps({
            "a": args.target_a,
            "b": args.target_b,
            "shared": sorted(shared),
            "only_a": sorted(only_a),
            "only_b": sorted(only_b),
        }, ensure_ascii=False, indent=2))
        return 0

    print(f"━━━ G({args.target_a}) vs G({args.target_b}) ━━━\n")

    if shared:
        print(f"🔗 共通チャンク ({len(shared)}個):")
        for c in sorted(shared):
            print(f"  • {c}")

    if only_a:
        print(f"\n📌 {args.target_a} のみ ({len(only_a)}個):")
        for c in sorted(only_a):
            print(f"  • {c}")

    if only_b:
        print(f"\n📌 {args.target_b} のみ ({len(only_b)}個):")
        for c in sorted(only_b):
            print(f"  • {c}")

    return 0


# PURPOSE: decompose の main 処理を実行する
def main() -> int:
    parser = argparse.ArgumentParser(
        prog="decompose",
        description="G 関手 (忘却 = 第一原理分解) の CLI ツール",
        epilog="HGK 内部対象から構造を剥いで最小チャンクに分解する",
    )
    subparsers = parser.add_subparsers(dest="command", help="サブコマンド")

    # decompose command
    p_decompose = subparsers.add_parser(
        "g",
        help="G(Y): 対象を第一原理に分解",
        description="HGK 内部対象から構造を剥いで原子的チャンクを抽出",
    )
    p_decompose.add_argument("target", help="対象名 (e.g., eat, syn, ousia)")
    p_decompose.add_argument("--json", action="store_true", help="JSON出力")
    p_decompose.set_defaults(func=cmd_decompose)

    # compare command
    p_compare = subparsers.add_parser(
        "compare",
        help="G(A) vs G(B): 二つの対象の原子チャンクを比較",
        description="二つの HGK 内部対象を分解し、共通チャンクを発見",
    )
    p_compare.add_argument("target_a", help="対象A (e.g., eat)")
    p_compare.add_argument("target_b", help="対象B (e.g., syn)")
    p_compare.add_argument("--json", action="store_true", help="JSON出力")
    p_compare.set_defaults(func=cmd_compare)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
