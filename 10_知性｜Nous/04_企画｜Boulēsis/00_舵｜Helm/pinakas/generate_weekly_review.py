#!/usr/bin/env python3
"""
PURPOSE: Pinakas 週次レビュー生成 — PINAKAS_TASK.yaml から
今週の進捗サマリーを自動生成し、WEEKLY_REVIEW.md として出力する。

使い方:
  python generate_weekly_review.py              # 直近7日間
  python generate_weekly_review.py --days 14    # 直近14日間
"""

import yaml
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


# -- 定数 --
PINAKAS_DIR = Path(__file__).resolve().parent
TASK_FILE = PINAKAS_DIR / "PINAKAS_TASK.yaml"
SEED_FILE = PINAKAS_DIR / "PINAKAS_SEED.yaml"
OUTPUT_FILE = PINAKAS_DIR / "WEEKLY_REVIEW.md"

# Sprint ストリーム名
SPRINT_STREAMS = {
    "S-001": "① FEP × 圏論 ガチ深化",
    "S-002": "② インフラ並行ループ",
    "S-003": "③ Claude × Gemini 分業",
    "S-004": "④ 情報収集の再設計",
    "S-005": "⑤ WF プロンプト最適化",
    "S-006": "⑥ Hub MCP / 秘書 MCP",
    "S-007": "⑦ SKILL/WF 精密化",
    "S-008": "⑧ 忘却論出版パイプライン",
    "S-009": "⑨ Mekhane Vision 実装",
}


def load_yaml(path: Path) -> dict:
    """YAML ファイルを読み込む。"""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def parse_date(date_str: str) -> datetime | None:
    """日付文字列をパース。"""
    if not date_str:
        return None
    try:
        return datetime.strptime(str(date_str).strip(), "%Y-%m-%d")
    except ValueError:
        return None


def extract_done_date(task: dict) -> datetime | None:
    """タスクの完了日を複数候補から抽出する。"""
    for key in ("completed", "done_date", "closed"):
        parsed = parse_date(task.get(key, ""))
        if parsed:
            return parsed

    note = task.get("note", "") or ""
    # "Done 2026-04-01" パターン
    for line in note.split("\n"):
        line = line.strip()
        if line.lower().startswith("done") or line.startswith("完了"):
            for word in line.split():
                d = parse_date(word)
                if d:
                    return d
    return parse_date(task.get("date", "")) or parse_date(task.get("created", ""))


def extract_created_date(task: dict) -> datetime | None:
    """created/date のどちらでも作成日を取る。"""
    return parse_date(task.get("created", "")) or parse_date(task.get("date", ""))


def generate_weekly_review(days: int = 7):
    """週次レビューを生成する。"""
    now = datetime.now()
    cutoff = now - timedelta(days=days)
    period_label = f"{cutoff.strftime('%m/%d')}〜{now.strftime('%m/%d')}"

    # -- データ読み込み --
    tasks_data = load_yaml(TASK_FILE)
    seeds_data = load_yaml(SEED_FILE)
    tasks = tasks_data.get("items", []) or []
    seeds = seeds_data.get("items", []) or []

    # -- 期間内の完了タスク --
    completed_this_period = []
    for t in tasks:
        if t.get("status") != "done":
            continue
        done_date = extract_done_date(t)
        if done_date and done_date >= cutoff:
            completed_this_period.append((t, done_date))

    completed_this_period.sort(key=lambda x: x[1])

    # -- 期間内の新規タスク --
    new_this_period = []
    for t in tasks:
        task_date = extract_created_date(t)
        if task_date and task_date >= cutoff:
            new_this_period.append(t)

    # -- Sprint 進捗 --
    sprint_stats = {}
    for sid in SPRINT_STREAMS:
        stream = [t for t in tasks if t.get("sprint_ref") == sid]
        done = len([t for t in stream if t.get("status") == "done"])
        total = len(stream)
        done_period = len([
            t for t, d in completed_this_period
            if t.get("sprint_ref") == sid
        ])
        sprint_stats[sid] = {
            "done": done, "total": total,
            "done_period": done_period,
            "pct": round(done / total * 100) if total > 0 else 0,
        }

    # -- 全体統計 --
    total_open = len([t for t in tasks if t.get("status") == "open"])
    total_done = len([t for t in tasks if t.get("status") == "done"])
    total_tasks = len(tasks)

    # -- Markdown 生成 --
    lines = []
    lines.append(f"# 📊 週次レビュー ({period_label})")
    lines.append("")
    lines.append(f"> 自動生成: `generate_weekly_review.py` | 生成日: {now.strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # サマリー
    lines.append("## 🎯 サマリー")
    lines.append("")
    lines.append(f"| 指標 | 値 |")
    lines.append(f"|:-----|---:|")
    lines.append(f"| 期間内完了 | **{len(completed_this_period)}** 件 |")
    lines.append(f"| 期間内新規 | {len(new_this_period)} 件 |")
    lines.append(f"| 残り open | {total_open} 件 |")
    lines.append(f"| 全体進捗 | {total_done}/{total_tasks} ({round(total_done/total_tasks*100) if total_tasks else 0}%) |")
    net = len(new_this_period) - len(completed_this_period)
    trend = "📈 増加" if net > 0 else "📉 減少" if net < 0 else "→ 横ばい"
    lines.append(f"| タスク増減 | {net:+d} ({trend}) |")
    lines.append("")

    # Sprint 進捗バー
    lines.append("## 🏃 Sprint 進捗")
    lines.append("")
    lines.append("| Sprint | 進捗 | 今週 | バー |")
    lines.append("|:-------|-----:|-----:|:-----|")
    for sid, sname in SPRINT_STREAMS.items():
        st = sprint_stats[sid]
        if st["total"] == 0:
            continue
        bar_full = st["pct"] // 10
        bar = "█" * bar_full + "░" * (10 - bar_full)
        period_str = f"+{st['done_period']}" if st["done_period"] > 0 else "—"
        lines.append(
            f"| {sid} {sname[:12]} | {st['done']}/{st['total']} ({st['pct']}%) | {period_str} | {bar} |"
        )
    lines.append("")

    # 完了タスク詳細
    lines.append("## ✅ 完了タスク")
    lines.append("")
    if completed_this_period:
        for t, d in completed_this_period:
            ref = t.get("sprint_ref", "—")
            lines.append(f"- **{t['id']}** {t['text'][:70]} ({d.strftime('%m/%d')}, {ref})")
        lines.append("")
    else:
        lines.append("_期間内の完了タスクなし_")
        lines.append("")

    # 新規タスク
    lines.append("## 🆕 新規タスク")
    lines.append("")
    if new_this_period:
        for t in new_this_period:
            status = t.get("status", "open")
            emoji = "✅" if status == "done" else "🔵"
            lines.append(f"- {emoji} **{t['id']}** {t['text'][:70]}")
        lines.append("")
    else:
        lines.append("_期間内の新規タスクなし_")
        lines.append("")

    # 停滞警告 (7日以上 open で high priority)
    lines.append("## ⚠️ 停滞警告")
    lines.append("")
    stale = []
    for t in tasks:
        if t.get("status") not in ("open", "in_progress", "queued") or t.get("priority") != "high":
            continue
        task_date = extract_created_date(t)
        if task_date and (now - task_date).days >= 7:
            stale.append((t, (now - task_date).days))

    if stale:
        stale.sort(key=lambda x: -x[1])
        for t, age in stale:
            lines.append(f"- 🔴 **{t['id']}** ({age}日経過) {t['text'][:60]}")
        lines.append("")
    else:
        lines.append("_停滞タスクなし_ 🎉")
        lines.append("")

    # フッター
    lines.append("---")
    lines.append("")
    lines.append(f"生成コマンド: `python pinakas/generate_weekly_review.py --days {days}`")

    # -- 書き出し --
    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ 週次レビュー生成完了: {OUTPUT_FILE}")
    print(f"   期間: {period_label} ({days}日間)")
    print(f"   完了: {len(completed_this_period)} 件 / 新規: {len(new_this_period)} 件")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pinakas 週次レビュー生成")
    parser.add_argument("--days", type=int, default=7, help="対象期間の日数 (デフォルト: 7)")
    args = parser.parse_args()
    generate_weekly_review(days=args.days)
