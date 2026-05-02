#!/usr/bin/env python3
"""
sync_nous.py — nous/ → nous/ 一方向同期スクリプト

oikos/01_ヘゲモニコン｜Hegemonikon/nous/ および kernel/ の内容を
oikos/01_ヘゲモニコン｜Hegemonikon/nous/ (Obsidian 閲覧用) に同期する。

正規ソースは常に oikos/01_ヘゲモニコン｜Hegemonikon 側。nous/ は Obsidian 閲覧用コピー。

Usage:
    python scripts/sync_nous.py          # dry-run (変更を表示のみ)
    python scripts/sync_nous.py --apply  # 実行
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# === Paths ===
HEGEMONIKON = Path.home() / "oikos" / "hegemonikon"
NOUS = Path.home() / "oikos" / "hegemonikon" / "nous"

# === Sync mappings: (source_relative_to_hegemonikon, dest_relative_to_nous) ===
SYNC_MAP = [
    ("nous/rules", "rules"),
    ("nous/skills", "skills"),
    ("nous/workflows", "workflows"),
    ("nous/macros", "ccl"),
    ("nous/standards", "standards"),
    ("nous/templates", "templates"),
    ("kernel", "kernel"),
]

# Files to exclude from sync
EXCLUDES = [
    "desktop.ini",
    ".DS_Store",
    "__pycache__",
    "*.pyc",
]


def build_rsync_excludes() -> list[str]:
    """rsync 除外オプションを構築"""
    args = []
    for exc in EXCLUDES:
        args.extend(["--exclude", exc])
    return args


def sync_directory(src: Path, dst: Path, dry_run: bool = True) -> dict:
    """rsync で一方向同期を実行"""
    if not src.exists():
        return {"src": str(src), "status": "SKIP", "reason": "source not found"}

    # dst が存在しなければ作成
    dst.mkdir(parents=True, exist_ok=True)

    cmd = [
        "rsync", "-av", "--delete",
        *build_rsync_excludes(),
    ]
    if dry_run:
        cmd.append("--dry-run")

    # rsync は末尾の / が重要
    cmd.extend([f"{src}/", f"{dst}/"])

    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=30,
    )

    # rsync 出力から変更ファイルを抽出
    changed = [
        line for line in result.stdout.strip().split("\n")
        if line and not line.startswith("sending")
        and not line.startswith("sent ")
        and not line.startswith("total ")
        and not line.startswith("building ")
        and line != "./"
    ]

    return {
        "src": str(src),
        "dst": str(dst),
        "status": "OK" if result.returncode == 0 else "ERROR",
        "changed": changed,
        "error": result.stderr.strip() if result.returncode != 0 else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Sync nous/ → nous/")
    parser.add_argument(
        "--apply", action="store_true",
        help="実際に同期を実行 (デフォルトは dry-run)",
    )
    args = parser.parse_args()

    dry_run = not args.apply
    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"🔄 sync_nous.py [{mode}]")
    print(f"   Source: {HEGEMONIKON}")
    print(f"   Dest:   {NOUS}")
    print()

    total_changed = 0
    for src_rel, dst_rel in SYNC_MAP:
        src = HEGEMONIKON / src_rel
        dst = NOUS / dst_rel
        result = sync_directory(src, dst, dry_run=dry_run)

        status_icon = {"OK": "✅", "SKIP": "⏭️", "ERROR": "❌"}.get(
            result["status"], "?"
        )
        n_changed = len(result.get("changed", []))
        total_changed += n_changed

        print(f"  {status_icon} {src_rel:30s} → {dst_rel:15s} ({n_changed} changes)")

        if result.get("error"):
            print(f"     ❌ {result['error']}")
        if n_changed > 0 and n_changed <= 10:
            for f in result["changed"]:
                print(f"     {'→' if not dry_run else '~'} {f}")
        elif n_changed > 10:
            for f in result["changed"][:5]:
                print(f"     {'→' if not dry_run else '~'} {f}")
            print(f"     ... and {n_changed - 5} more")

    print()
    if dry_run:
        print(f"📋 合計 {total_changed} ファイルが変更対象 (dry-run)")
        if total_changed > 0:
            print("   実行するには: python scripts/sync_nous.py --apply")
    else:
        print(f"✅ 合計 {total_changed} ファイルを同期しました")


if __name__ == "__main__":
    main()
