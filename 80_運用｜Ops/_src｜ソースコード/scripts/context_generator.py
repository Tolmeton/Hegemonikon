#!/usr/bin/env python3
# PROOF: [L2/自動化] <- scripts/ F6 設計 (designs/f6_context_auto_update.md) の実装 Phase 1
"""
Context Generator — context/ ファイルの自動更新スケルトン

KI や Sophia の更新を検知し、context/ の各テーマファイルを差分更新する。
F6 設計ドキュメントに基づく実装。

Usage:
    python context_generator.py --check       # 変更検知のみ
    python context_generator.py --generate    # 再生成実行
    python context_generator.py --status      # 現在の状態表示
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

# === 設定 ===
PROJECT_ROOT = Path(__file__).parent.parent
CONTEXT_DIR = PROJECT_ROOT / "mekhane" / "symploke" / "context"
KI_DIR = Path.home() / ".gemini" / "antigravity" / "knowledge"
SOPHIA_DIR = Path.home() / "oikos" / "mneme" / ".hegemonikon" / "sophia"
STATE_FILE = PROJECT_ROOT / ".context_generator_state.json"

# テーマ分類ヒューリスティック
THEME_KEYWORDS: dict[str, list[str]] = {
    "fep_foundation": ["fep", "free energy", "active inference", "precision",
                       "variational", "markov blanket", "prediction error"],
    "hgk_knowledge": ["hegemonikon", "theorem", "定理", "series", "ousia",
                      "schema", "horme", "kairos", "akribeia"],
    "hgk_vocabulary": ["definition", "greek", "名前", "用語", "意味"],
    "category_patterns": ["adjunction", "functor", "category", "morphism",
                          "圏論", "随伴", "関手", "自然変換"],
    "ccl_language": ["ccl", "operator", "syntax", "演算子", "構文"],
    "quality_assurance": ["test", "review", "quality", "check", "品質",
                          "検証", "dendron", "proof"],
    "design_patterns": ["design", "pattern", "architecture", "設計",
                        "アーキテクチャ", "module"],
    "morphism_guide": ["morphism", "bridge", "anchor", "射", "提案"],
}


def load_state() -> dict:
    """前回の状態を読み込む。"""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"last_check": None, "file_hashes": {}}


def save_state(state: dict) -> None:
    """状態を保存する。"""
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str),
                          encoding="utf-8")


def hash_file(path: Path) -> str:
    """ファイルの MD5 ハッシュを計算する。"""
    return hashlib.md5(path.read_bytes()).hexdigest()


def detect_changes(state: dict) -> dict[str, list[Path]]:
    """KI, Sophia の変更を検知する。"""
    changes: dict[str, list[Path]] = {"new": [], "modified": [], "deleted": []}
    old_hashes = state.get("file_hashes", {})
    current_hashes: dict[str, str] = {}

    for source_dir in [KI_DIR, SOPHIA_DIR]:
        if not source_dir.exists():
            continue
        for md_file in source_dir.rglob("*.md"):
            key = str(md_file)
            h = hash_file(md_file)
            current_hashes[key] = h
            if key not in old_hashes:
                changes["new"].append(md_file)
            elif old_hashes[key] != h:
                changes["modified"].append(md_file)

    for key in old_hashes:
        if key not in current_hashes:
            changes["deleted"].append(Path(key))

    state["file_hashes"] = current_hashes
    state["last_check"] = datetime.now().isoformat()
    return changes


def classify_theme(content: str) -> str:
    """内容からテーマを分類する。"""
    content_lower = content.lower()
    scores: dict[str, int] = {}
    for theme, keywords in THEME_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in content_lower)
        if score > 0:
            scores[theme] = score

    if not scores:
        return "hgk_knowledge"  # デフォルト
    return max(scores, key=scores.get)  # type: ignore[arg-type]


def show_status() -> None:
    """現在の状態を表示する。"""
    state = load_state()
    print("=== Context Generator Status ===")
    print(f"  Last check: {state.get('last_check', 'never')}")
    print(f"  Tracked files: {len(state.get('file_hashes', {}))}")
    print()
    print("=== context/ Files ===")
    if CONTEXT_DIR.exists():
        for md_file in sorted(CONTEXT_DIR.glob("*.md")):
            lines = len(md_file.read_text(encoding="utf-8").splitlines())
            print(f"  {md_file.name:<35} {lines:>4} lines")
    print()
    print("=== Source Directories ===")
    for name, d in [("KI", KI_DIR), ("Sophia", SOPHIA_DIR)]:
        if d.exists():
            count = len(list(d.rglob("*.md")))
            print(f"  {name}: {d} ({count} files)")
        else:
            print(f"  {name}: {d} (not found)")


def check_changes() -> None:
    """変更を検知して表示する。"""
    state = load_state()
    changes = detect_changes(state)

    total = sum(len(v) for v in changes.values())
    if total == 0:
        print("✅ No changes detected since last check.")
    else:
        print(f"🔄 {total} changes detected:")
        for kind, files in changes.items():
            for f in files:
                print(f"  [{kind}] {f}")

        # テーマ分類のプレビュー
        print("\n--- Theme Classification Preview ---")
        for f in changes["new"] + changes["modified"]:
            if f.exists():
                content = f.read_text(encoding="utf-8")
                theme = classify_theme(content)
                print(f"  {f.name} → {theme}")

    save_state(state)


def generate() -> None:
    """context/ ファイルを再生成する (Phase 1: 影響範囲の表示のみ)。"""
    state = load_state()
    changes = detect_changes(state)
    total = sum(len(v) for v in changes.values())

    if total == 0:
        print("✅ No changes — nothing to generate.")
        save_state(state)
        return

    print(f"🔧 Generation plan ({total} source changes):")
    affected_themes: set[str] = set()
    for f in changes["new"] + changes["modified"]:
        if f.exists():
            content = f.read_text(encoding="utf-8")
            theme = classify_theme(content)
            affected_themes.add(theme)
            print(f"  {f.name} → {theme}")

    print(f"\n📁 Affected context files: {', '.join(sorted(affected_themes))}")
    print("\n⚠️ Phase 1: Dry-run only. Actual generation not yet implemented.")
    print("   TODO: Implement incremental update logic for each theme file.")

    save_state(state)


def main() -> None:
    parser = argparse.ArgumentParser(description="Context Generator (Phase 1)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="変更検知のみ")
    group.add_argument("--generate", action="store_true", help="再生成 (dry-run)")
    group.add_argument("--status", action="store_true", help="現在の状態表示")
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.check:
        check_changes()
    elif args.generate:
        generate()


if __name__ == "__main__":
    main()
