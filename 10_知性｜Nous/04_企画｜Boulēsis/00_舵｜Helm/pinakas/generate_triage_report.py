#!/usr/bin/env python3
"""
PURPOSE: Pinakas 全ボードの triage 面を生成し、即修正すべき不整合と
判断待ちの open 束を Markdown で可視化する。

使い方:
  python generate_triage_report.py
  python generate_triage_report.py --stale-days 7 --limit 12
"""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml


PINAKAS_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = PINAKAS_DIR / "PINAKAS_TRIAGE.md"

BOARD_FILES = {
    "seed": PINAKAS_DIR / "PINAKAS_SEED.yaml",
    "task": PINAKAS_DIR / "PINAKAS_TASK.yaml",
    "question": PINAKAS_DIR / "PINAKAS_QUESTION.yaml",
    "wish": PINAKAS_DIR / "PINAKAS_WISH.yaml",
    "backlog": PINAKAS_DIR / "PINAKAS_BACKLOG.yaml",
    "whiteboard": PINAKAS_DIR / "PINAKAS_WHITEBOARD.yaml",
}

BOARD_LABELS = {
    "seed": "Seed",
    "task": "Task",
    "question": "Question",
    "wish": "Wish",
    "backlog": "Backlog",
    "whiteboard": "Whiteboard",
}

EXPECTED_STATUSES = {
    "seed": {"open", "adopted", "dropped", "done"},
    "task": {"open", "in_progress", "done", "dropped"},
    "question": {"open", "answered", "dropped"},
    "wish": {"open", "dropped", "promoted"},
    "backlog": {"open", "dropped", "promoted"},
    "whiteboard": {"active", "paused", "archived"},
}

ID_SUFFIX_RE = re.compile(r"(\d+)$")
NOISE_PATTERNS = ("文脈断片", "📋", "pinakas_store.py が未同期")


def parse_date(value: Any) -> date | None:
    if value is None:
        return None
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def truncate(text: str, limit: int = 88) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def extract_numeric_suffix(item_id: Any) -> int | None:
    if not isinstance(item_id, str):
        return None
    match = ID_SUFFIX_RE.search(item_id)
    if not match:
        return None
    return int(match.group(1))


def canonical_next_id(data: dict[str, Any]) -> int:
    items = data.get("items") or []
    from_items = max((extract_numeric_suffix(item.get("id")) or 0) for item in items) + 1
    candidates = [from_items]
    top_level = data.get("next_id")
    if isinstance(top_level, int) and top_level > 0:
        candidates.append(top_level)
    elif isinstance(top_level, str) and top_level.isdigit():
        candidates.append(int(top_level))
    meta = data.get("_meta")
    if isinstance(meta, dict):
        meta_next = meta.get("next_id")
        if isinstance(meta_next, int) and meta_next > 0:
            candidates.append(meta_next)
        elif isinstance(meta_next, str) and meta_next.isdigit():
            candidates.append(int(meta_next))
    return max(candidates) if candidates else 1


def load_board(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)
    return data, None


def board_items(data: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not data:
        return []
    items = data.get("items") or []
    return [item for item in items if isinstance(item, dict)]


def primary_open_statuses(board: str) -> set[str]:
    if board == "task":
        return {"open", "in_progress"}
    if board == "whiteboard":
        return {"active"}
    return {"open"}


def open_items(board: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    statuses = primary_open_statuses(board)
    return [item for item in items if item.get("status") in statuses]


def duplicate_ids(items: list[dict[str, Any]]) -> list[str]:
    counts = Counter(item.get("id") for item in items if item.get("id"))
    return sorted(item_id for item_id, count in counts.items() if count > 1)


def unexpected_statuses(board: str, items: list[dict[str, Any]]) -> list[str]:
    allowed = EXPECTED_STATUSES[board]
    statuses = {item.get("status") for item in items if item.get("status")}
    return sorted(status for status in statuses if status not in allowed)


def fragment_candidates(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for item in items:
        text = str(item.get("text", ""))
        if any(pattern in text for pattern in NOISE_PATTERNS) or text.startswith("`"):
            candidates.append(item)
    return candidates


def stale_items(board: str, items: list[dict[str, Any]], stale_days: int) -> list[dict[str, Any]]:
    today = date.today()
    result: list[dict[str, Any]] = []
    for item in open_items(board, items):
        created = parse_date(item.get("created") or item.get("date"))
        if created is None:
            continue
        age = (today - created).days
        if age >= stale_days:
            enriched = dict(item)
            enriched["_age_days"] = age
            result.append(enriched)
    return sorted(result, key=lambda item: (-item["_age_days"], item.get("id", "")))


def sprint_buckets(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for item in items:
        ref = item.get("sprint_ref") or "未紐付け"
        counts[str(ref)] += 1
    return dict(sorted(counts.items(), key=lambda kv: kv[0]))


def render_summary_row(board: str, items: list[dict[str, Any]]) -> str:
    statuses = Counter(item.get("status", "<missing>") for item in items)
    if board == "task":
        focus = f"{statuses.get('open', 0)} open / {statuses.get('in_progress', 0)} in_progress"
    elif board == "whiteboard":
        focus = f"{statuses.get('active', 0)} active"
    else:
        focus = f"{statuses.get('open', 0)} open"
    return f"| {BOARD_LABELS[board]} | {focus} | {len(items)} total | {dict(statuses)} |"


def generate_triage_report(stale_days: int, limit: int) -> Path:
    loaded: dict[str, tuple[dict[str, Any] | None, str | None]] = {
        board: load_board(path)
        for board, path in BOARD_FILES.items()
    }

    lines: list[str] = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append("# 📋 PINAKAS Triage")
    lines.append("")
    lines.append(f"> 自動生成: `generate_triage_report.py` | 最終更新: {now}")
    lines.append("")

    lines.append("## Kernel")
    lines.append("")
    lines.append("| ボード | 焦点件数 | 総件数 | status 分布 |")
    lines.append("|:-------|:---------|:-------|:------------|")
    for board in BOARD_FILES:
        data, error = loaded[board]
        if error:
            lines.append(f"| {BOARD_LABELS[board]} | parse error | — | `{truncate(error, 80)}` |")
            continue
        items = board_items(data)
        lines.append(render_summary_row(board, items))
    lines.append("")

    lines.append("## Immediate Anomalies")
    lines.append("")
    anomaly_rows: list[str] = []
    for board in BOARD_FILES:
        data, error = loaded[board]
        if error:
            anomaly_rows.append(
                f"| {BOARD_LABELS[board]} | parse-error | `{truncate(error, 96)}` |"
            )
            continue
        items = board_items(data)
        dups = duplicate_ids(items)
        if dups:
            anomaly_rows.append(
                f"| {BOARD_LABELS[board]} | duplicate-id | {', '.join(dups)} |"
            )
        weird_statuses = unexpected_statuses(board, items)
        if weird_statuses:
            anomaly_rows.append(
                f"| {BOARD_LABELS[board]} | non-protocol-status | {', '.join(weird_statuses)} |"
            )
        expected_next = canonical_next_id(data or {})
        top_next = data.get("next_id") if data else None
        meta = data.get("_meta") if isinstance(data, dict) else None
        meta_next = meta.get("next_id") if isinstance(meta, dict) else None
        if top_next is not None and top_next != expected_next:
            anomaly_rows.append(
                f"| {BOARD_LABELS[board]} | top-next-id-drift | top=`{top_next}` / expected=`{expected_next}` |"
            )
        if meta_next is not None and meta_next != expected_next:
            anomaly_rows.append(
                f"| {BOARD_LABELS[board]} | meta-next-id-drift | meta=`{meta_next}` / expected=`{expected_next}` |"
            )
    if anomaly_rows:
        lines.append("| ボード | 種別 | 詳細 |")
        lines.append("|:-------|:-----|:-----|")
        lines.extend(anomaly_rows)
        lines.append("")
    else:
        lines.append("_即時異常なし_")
        lines.append("")

    lines.append("## Machine-Suspicious Cleanup Candidates")
    lines.append("")
    cleanup_rows: list[str] = []
    for board in ("seed", "task", "question"):
        data, error = loaded[board]
        if error or not data:
            continue
        for item in fragment_candidates(open_items(board, board_items(data)))[:limit]:
            cleanup_rows.append(
                f"| {BOARD_LABELS[board]} | {item.get('id', '—')} | noise-fragment | {truncate(str(item.get('text', '')), 96)} |"
            )
    if cleanup_rows:
        lines.append("| ボード | ID | 理由 | text |")
        lines.append("|:-------|:---|:-----|:-----|")
        lines.extend(cleanup_rows)
        lines.append("")
    else:
        lines.append("_機械的に怪しい短冊は未検出_")
        lines.append("")

    lines.append(f"## Aged Open Items (>= {stale_days} days)")
    lines.append("")
    for board in ("task", "seed", "question"):
        data, error = loaded[board]
        if error or not data:
            continue
        stale = stale_items(board, board_items(data), stale_days)
        lines.append(f"### {BOARD_LABELS[board]}")
        lines.append("")
        if not stale:
            lines.append("_該当なし_")
            lines.append("")
            continue
        lines.append("| ID | Age | text |")
        lines.append("|:---|----:|:-----|")
        for item in stale[:limit]:
            lines.append(
                f"| {item.get('id', '—')} | {item['_age_days']}d | {truncate(str(item.get('text', '')), 96)} |"
            )
        lines.append("")

    lines.append("## Triage Surfaces")
    lines.append("")

    task_data, task_error = loaded["task"]
    if not task_error and task_data:
        tasks = board_items(task_data)
        unsprinted = [
            item for item in open_items("task", tasks)
            if not item.get("sprint_ref")
        ]
        lines.append("### Task")
        lines.append("")
        lines.append(
            f"- open={sum(1 for item in tasks if item.get('status') == 'open')} / in_progress={sum(1 for item in tasks if item.get('status') == 'in_progress')}"
        )
        lines.append(f"- sprint 未紐付け active task={len(unsprinted)}")
        lines.append(
            f"- sprint 分布={sprint_buckets(open_items('task', tasks))}"
        )
        if unsprinted:
            lines.append("")
            lines.append("| ID | status | text |")
            lines.append("|:---|:-------|:-----|")
            for item in unsprinted[:limit]:
                lines.append(
                    f"| {item.get('id', '—')} | {item.get('status', '—')} | {truncate(str(item.get('text', '')), 96)} |"
                )
        lines.append("")

    for board in ("wish", "backlog"):
        data, error = loaded[board]
        if error or not data:
            continue
        items = board_items(data)
        active = open_items(board, items)
        lines.append(f"### {BOARD_LABELS[board]}")
        lines.append("")
        lines.append(f"- open={len(active)}")
        lines.append(f"- sprint 分布={sprint_buckets(active)}")
        lines.append("")

    whiteboard_data, whiteboard_error = loaded["whiteboard"]
    if not whiteboard_error and whiteboard_data:
        whiteboards = board_items(whiteboard_data)
        active = open_items("whiteboard", whiteboards)
        lines.append("### Whiteboard")
        lines.append("")
        lines.append(f"- active={len(active)}")
        if active:
            lines.append("")
            lines.append("| ID | updated | title |")
            lines.append("|:---|:--------|:------|")
            for item in active[:limit]:
                lines.append(
                    f"| {item.get('id', '—')} | {item.get('updated', '—')} | {truncate(str(item.get('title', '')), 96)} |"
                )
        lines.append("")

    lines.append("## Suggested First Cuts")
    lines.append("")
    lines.append("- Seed: まず noise-fragment 候補を落とし、残りを `Wish` 昇格候補 / `Question` 化候補 / 純粋な seed に三分する。")
    lines.append("- Task: sprint 未紐付け active task を先に束ねる。実行中の監視タスクは done 条件を書き切る。")
    lines.append("- Question: 重複 ID と古い open を整理し、答えが出たものは `answered` に閉じる。")
    lines.append("- Wish / Backlog: いま全部 open なので、四半期内に触らない束を backlog 側へ沈めるか archive 面を別立てする。")
    lines.append("- Whiteboard: active が複数あるなら、今の front line 以外を `paused` 候補として点検する。")
    lines.append("")

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    return OUTPUT_FILE


def main() -> None:
    parser = argparse.ArgumentParser(description="Pinakas triage レポート生成")
    parser.add_argument("--stale-days", type=int, default=7, help="古い open と見なす日数")
    parser.add_argument("--limit", type=int, default=12, help="各セクションの最大表示件数")
    args = parser.parse_args()

    output = generate_triage_report(stale_days=args.stale_days, limit=args.limit)
    print(f"✅ triage report generated: {output}")


if __name__ == "__main__":
    main()
