#!/usr/bin/env python3
"""
PURPOSE: Pinakas の open 件数を減らす前提で、
重複 ID / stale open / 明白な断片候補を洗い出す監査レポートを生成する。

使い方:
  python pinakas_audit.py
  python pinakas_audit.py --stale-days 7
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import yaml


PINAKAS_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = PINAKAS_DIR / "PINAKAS_AUDIT.md"

BOARD_FILES = {
    "task": ("PINAKAS_TASK.yaml", {"open", "in_progress", "queued"}),
    "seed": ("PINAKAS_SEED.yaml", {"open"}),
    "question": ("PINAKAS_QUESTION.yaml", {"open"}),
    "wish": ("PINAKAS_WISH.yaml", {"open"}),
    "backlog": ("PINAKAS_BACKLOG.yaml", {"open"}),
    "whiteboard": ("PINAKAS_WHITEBOARD.yaml", {"active"}),
}


def load_items(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("items", []) or []


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d")
    except ValueError:
        return None


def extract_open_anchor(item: dict):
    for key in ("created", "date", "updated"):
        parsed = parse_date(item.get(key))
        if parsed:
            return parsed
    return None


def is_fragment(item: dict) -> bool:
    text = (item.get("text") or item.get("title") or "").strip()
    if not text:
        return True
    fragment_markers = (
        "文脈断片",
        "誤キャプチャ断片",
        "テスト用",
    )
    if any(marker in text for marker in fragment_markers):
        return True
    if text.startswith(")"):
        return True
    if text.startswith("` / `"):
        return True
    return False


def summarize_board(board: str, items: list[dict], open_like: set[str]) -> dict:
    by_status = Counter((item.get("status") or "unknown") for item in items)
    active_count = sum(
        1 for item in items if (item.get("status") or "unknown") in open_like
    )
    return {
        "board": board,
        "total": len(items),
        "active": active_count,
        "by_status": by_status,
    }


def find_duplicate_ids(items: list[dict]) -> dict[str, list[dict]]:
    bucket = defaultdict(list)
    for item in items:
        item_id = item.get("id")
        if item_id:
            bucket[item_id].append(item)
    return {item_id: dupes for item_id, dupes in bucket.items() if len(dupes) > 1}


def render_counts(stats: list[dict]) -> list[str]:
    lines = []
    lines.append("| Board | Active | Total | Statuses |")
    lines.append("|:------|------:|------:|:---------|")
    for stat in stats:
        statuses = ", ".join(
            f"{status}={count}" for status, count in sorted(stat["by_status"].items())
        )
        lines.append(
            f"| {stat['board']} | {stat['active']} | {stat['total']} | {statuses} |"
        )
    return lines


def main(stale_days: int):
    now = datetime.now()
    stats = []
    duplicate_lines = []
    stale_lines = []
    fragment_lines = []

    for board, (filename, open_like) in BOARD_FILES.items():
        path = PINAKAS_DIR / filename
        items = load_items(path)
        stats.append(summarize_board(board, items, open_like))

        duplicates = find_duplicate_ids(items)
        for item_id, dupes in sorted(duplicates.items()):
            duplicate_lines.append(
                f"- `{board}` `{item_id}` が {len(dupes)} 回出現"
            )
            for dupe in dupes:
                text = (dupe.get("text") or dupe.get("title") or "").strip()
                duplicate_lines.append(f"  - {text[:120]}")

        for item in items:
            status = item.get("status") or "unknown"
            item_id = item.get("id", "NO-ID")
            text = (item.get("text") or item.get("title") or "").strip()

            if is_fragment(item) and status in open_like:
                fragment_lines.append(
                    f"- `{board}` `{item_id}` [{status}] {text[:120]}"
                )

            if status in open_like:
                anchor = extract_open_anchor(item)
                if anchor and (now - anchor).days >= stale_days:
                    stale_lines.append(
                        f"- `{board}` `{item_id}` [{status}] {(now - anchor).days}日経過 — {text[:120]}"
                    )

    lines = []
    lines.append("# PINAKAS Audit")
    lines.append("")
    lines.append(
        f"> Generated: {now.strftime('%Y-%m-%d %H:%M')} | stale threshold: {stale_days} days"
    )
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.extend(render_counts(stats))
    lines.append("")

    lines.append("## Duplicate IDs")
    lines.append("")
    if duplicate_lines:
        lines.extend(duplicate_lines)
    else:
        lines.append("_none_")
    lines.append("")

    lines.append("## Fragment Candidates")
    lines.append("")
    if fragment_lines:
        lines.extend(fragment_lines)
    else:
        lines.append("_none_")
    lines.append("")

    lines.append("## Stale Active Items")
    lines.append("")
    if stale_lines:
        lines.extend(stale_lines)
    else:
        lines.append("_none_")
    lines.append("")

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pinakas audit")
    parser.add_argument(
        "--stale-days",
        type=int,
        default=7,
        help="Flag active items older than this many days",
    )
    args = parser.parse_args()
    main(stale_days=args.stale_days)
