#!/usr/bin/env python3
"""
PURPOSE: Pinakas ダッシュボード生成 — 6ボード (Task/Seed/Question/Wish/Backlog/Whiteboard) を統合し、
Sprint 紐付き俯瞰ビューを PINAKAS_DASHBOARD.md として生成する。
Whiteboard は索引 YAML + 本体 md の二層構造のため、本体 md 内容は展開せず索引情報のみ表示する。
"""

import yaml
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# -- 定数 --
PINAKAS_DIR = Path(__file__).resolve().parent
TASK_FILE = PINAKAS_DIR / "PINAKAS_TASK.yaml"
SEED_FILE = PINAKAS_DIR / "PINAKAS_SEED.yaml"
QUESTION_FILE = PINAKAS_DIR / "PINAKAS_QUESTION.yaml"
WISH_FILE = PINAKAS_DIR / "PINAKAS_WISH.yaml"
BACKLOG_FILE = PINAKAS_DIR / "PINAKAS_BACKLOG.yaml"
WHITEBOARD_FILE = PINAKAS_DIR / "PINAKAS_WHITEBOARD.yaml"
OUTPUT_FILE = PINAKAS_DIR / "PINAKAS_DASHBOARD.md"

# Sprint ストリーム名 (march_2026_sprint.typos より)
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
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def parse_date(value):
    """Pinakas の日付フィールドを datetime に変換する。"""
    if not value:
        return None
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d")
    except ValueError:
        return None


def extract_created_date(item: dict):
    """created/date のどちらでも作成日を取る。"""
    return parse_date(item.get("created") or item.get("date"))


def extract_closed_date(item: dict):
    """done/completed/closed/date の順で終了日を取る。"""
    for key in ("completed", "done_date", "closed", "date", "created"):
        parsed = parse_date(item.get(key))
        if parsed:
            return parsed
    return None


def format_priority(p: str) -> str:
    """優先度を絵文字付きで表示。"""
    return {"high": "🔴", "medium": "🟡", "low": "⚪"}.get(p, "")


def generate_dashboard():
    """ダッシュボードを生成する。"""
    # -- データ読み込み --
    tasks_data = load_yaml(TASK_FILE)
    seeds_data = load_yaml(SEED_FILE)
    questions_data = load_yaml(QUESTION_FILE)
    wishes_data = load_yaml(WISH_FILE) if WISH_FILE.exists() else {}
    backlog_data = load_yaml(BACKLOG_FILE) if BACKLOG_FILE.exists() else {}
    whiteboard_data = load_yaml(WHITEBOARD_FILE) if WHITEBOARD_FILE.exists() else {}

    tasks = tasks_data.get("items", []) or []
    seeds = seeds_data.get("items", []) or []
    questions = questions_data.get("items", []) or []
    wishes = wishes_data.get("items", []) or []
    backlog = backlog_data.get("items", []) or []
    whiteboards = whiteboard_data.get("items", []) or []

    # -- 集計 --
    task_by_status = defaultdict(list)
    for t in tasks:
        task_by_status[t.get("status", "unknown")].append(t)

    seed_by_status = defaultdict(list)
    for s in seeds:
        seed_by_status[s.get("status", "unknown")].append(s)

    q_by_status = defaultdict(list)
    for q in questions:
        q_by_status[q.get("status", "unknown")].append(q)

    # Sprint 紐付け集計
    sprint_tasks = defaultdict(list)
    unlinked_tasks = []
    for t in tasks:
        ref = t.get("sprint_ref")
        if ref and ref != "null":
            sprint_tasks[ref].append(t)
        elif t.get("status") in ("open", "in_progress"):
            unlinked_tasks.append(t)

    # -- Markdown 生成 --
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []
    lines.append("# 📋 PINAKAS ダッシュボード")
    lines.append("")
    lines.append(f"> 自動生成: `generate_dashboard.py` | 最終更新: {now}")
    lines.append("")

    # サマリー バー
    n_task_open = len(task_by_status.get("open", []))
    n_task_prog = len(task_by_status.get("in_progress", []))
    n_task_done = len(task_by_status.get("done", []))
    n_seed_open = len(seed_by_status.get("open", []))
    n_seed_adopted = len(seed_by_status.get("adopted", []))
    n_q_open = len(q_by_status.get("open", []))
    n_wish_open = len([w for w in wishes if w.get("status") == "open"])
    n_backlog_open = len([b for b in backlog if b.get("status") == "open"])
    wb_active = [w for w in whiteboards if w.get("status") == "active"]
    wb_paused = [w for w in whiteboards if w.get("status") == "paused"]
    wb_archived = [w for w in whiteboards if w.get("status") == "archived"]
    n_wb_active = len(wb_active)

    lines.append("## 📊 サマリー")
    lines.append("")
    lines.append("| ボード | 温度 | Open | Active | Closed | Total |")
    lines.append("|:-------|:-----|-----:|-------:|-------:|------:|")
    lines.append(
        f"| **Task** | ⚡即時 | {n_task_open} | {n_task_open + n_task_prog + len(task_by_status.get('queued', []))} | {n_task_done + len(task_by_status.get('dropped', []))} | {len(tasks)} |"
    )
    lines.append(
        f"| **Seed** | 🌱芽 | {n_seed_open} | {n_seed_open} | {n_seed_adopted + len(seed_by_status.get('done', [])) + len(seed_by_status.get('dropped', []))} | {len(seeds)} |"
    )
    lines.append(
        f"| **Wish** | 🟠WARM | {n_wish_open} | {n_wish_open} | {len([w for w in wishes if w.get('status') != 'open'])} | {len(wishes)} |"
    )
    lines.append(
        f"| **Backlog** | ❄️COLD | {n_backlog_open} | {n_backlog_open} | {len([b for b in backlog if b.get('status') != 'open'])} | {len(backlog)} |"
    )
    lines.append(
        f"| **Question** | ❓ | {n_q_open} | {n_q_open} | {len(q_by_status.get('answered', [])) + len(q_by_status.get('dropped', []))} | {len(questions)} |"
    )
    lines.append(
        f"| **Whiteboard** | 📝NOTES | {n_wb_active} | {n_wb_active + len(wb_paused)} | {len(wb_archived)} | {len(whiteboards)} |"
    )
    lines.append("")

    # Sprint × Task マトリクス
    lines.append("## 🎯 Sprint ストリーム × アクティブ Task")
    lines.append("")
    for sid, sname in SPRINT_STREAMS.items():
        stream_tasks = sprint_tasks.get(sid, [])
        open_in_stream = [
            t for t in stream_tasks if t.get("status") in ("open", "in_progress")
        ]
        done_in_stream = [t for t in stream_tasks if t.get("status") == "done"]
        lines.append(
            f"### {sid}: {sname}  ({len(open_in_stream)} open / {len(done_in_stream)} done)"
        )
        lines.append("")
        if open_in_stream:
            for t in sorted(open_in_stream, key=lambda x: (
                {"high": 0, "medium": 1, "low": 2}.get(x.get("priority", ""), 3)
            )):
                p = format_priority(t.get("priority", ""))
                status = t.get("status", "open")
                assignee = t.get("assignee", "")
                assignee_str = f" → {assignee}" if assignee else ""
                lines.append(
                    f"- {p} **{t['id']}** [{status}] {t['text'][:80]}{assignee_str}"
                )
            lines.append("")
        else:
            lines.append("_アクティブタスクなし_")
            lines.append("")

    # Sprint 未紐付けタスク
    if unlinked_tasks:
        lines.append("### ⚠️ Sprint 未紐付け (open)")
        lines.append("")
        for t in unlinked_tasks:
            p = format_priority(t.get("priority", ""))
            lines.append(f"- {p} **{t['id']}** {t['text'][:80]}")
        lines.append("")

    # アクション可能タスク (open + high priority)
    lines.append("## 🔥 今日のアクション候補 (open × high)")
    lines.append("")
    high_open = [
        t
        for t in tasks
        if t.get("status") == "open" and t.get("priority") == "high"
    ]
    if high_open:
        lines.append("| ID | タスク | Sprint | Assignee |")
        lines.append("|:---|:-------|:-------|:---------|")
        for t in high_open:
            ref = t.get("sprint_ref") or "—"
            assignee = t.get("assignee") or "未割当"
            text_short = t["text"][:60] + ("…" if len(t["text"]) > 60 else "")
            lines.append(f"| {t['id']} | {text_short} | {ref} | {assignee} |")
        lines.append("")
    else:
        lines.append("_high 優先度の open タスクなし_ 🎉")
        lines.append("")

    # Seed ボード
    lines.append("## 🌱 Seed ボード (アイデア)")
    lines.append("")
    open_seeds = seed_by_status.get("open", [])
    if open_seeds:
        lines.append("| ID | アイデア | 起源 | Tags |")
        lines.append("|:---|:--------|:-----|:-----|")
        for s in open_seeds:
            origin = s.get("origin", "—")
            tags = ", ".join(s.get("tags", [])[:3])
            text_short = s["text"][:60] + ("…" if len(s["text"]) > 60 else "")
            lines.append(f"| {s['id']} | {text_short} | {origin} | {tags} |")
        lines.append("")

    # Question ボード
    if questions:
        lines.append("## ❓ Question ボード")
        lines.append("")
        open_q = q_by_status.get("open", [])
        if open_q:
            for q in open_q:
                lines.append(f"- **{q['id']}** {q['text']}")
            lines.append("")
        else:
            lines.append("_未回答の質問なし_")
            lines.append("")

    # Wish ボード (WARM)
    if wishes:
        lines.append("## 🟠 Wish ボード (WARM — 四半期候補)")
        lines.append("")
        # Sprint 別に集計
        wish_by_sprint = defaultdict(list)
        for w in wishes:
            if w.get("status") == "open":
                ref = w.get("sprint_ref") or "未紐付け"
                wish_by_sprint[ref].append(w)
        for sid in sorted(wish_by_sprint.keys()):
            sname = SPRINT_STREAMS.get(sid, sid)
            items = wish_by_sprint[sid]
            lines.append(f"**{sid}** {sname} ({len(items)}件)")
            lines.append("")
            for w in sorted(items, key=lambda x: ({"high": 0, "medium": 1, "low": 2}.get(x.get("priority", ""), 3))):
                p = format_priority(w.get("priority", ""))
                lines.append(f"- {p} **{w['id']}** {w['text'][:80]}")
            lines.append("")

    # Backlog ボード (COLD)
    if backlog:
        open_backlog = [b for b in backlog if b.get("status") == "open"]
        lines.append(f"## ❄️ Backlog ボード (COLD — {len(open_backlog)}件)")
        lines.append("")
        # カテゴリ別にタグで分類
        bl_by_sprint = defaultdict(list)
        for b in open_backlog:
            ref = b.get("sprint_ref") or "未紐付け"
            bl_by_sprint[ref].append(b)
        for sid in sorted(bl_by_sprint.keys()):
            sname = SPRINT_STREAMS.get(sid, sid)
            items = bl_by_sprint[sid]
            lines.append(f"- **{sid}** {sname}: {len(items)}件")
        lines.append("")

    # Whiteboard ボード (NOTES — 索引のみ。本体 md は展開しない)
    if whiteboards:
        lines.append(
            f"## 📝 Whiteboards (戦略ノート — active {n_wb_active} / total {len(whiteboards)})"
        )
        lines.append("")
        lines.append(
            "_本体 md は `pinakas/whiteboards/WB-NNN_*.md` に存在。索引のみ表示する (本体非展開)。_"
        )
        lines.append("")
        if wb_active:
            lines.append("### active")
            lines.append("")
            lines.append("| ID | Title | Updated | Target | Note |")
            lines.append("|:---|:------|:--------|:-------|:-----|")
            for w in wb_active:
                wid = w.get("id", "")
                title = (w.get("title") or "")[:50]
                updated = w.get("updated", "—")
                target = w.get("target") or "—"
                if len(target) > 50:
                    target = "…" + target[-47:]
                note = (w.get("note") or "")[:40]
                lines.append(
                    f"| {wid} | {title} | {updated} | {target} | {note} |"
                )
            lines.append("")
        if wb_paused:
            lines.append(
                f"<details><summary>paused ({len(wb_paused)})</summary>"
            )
            lines.append("")
            for w in wb_paused:
                lines.append(
                    f"- {w.get('id', '')} {w.get('title', '')[:60]} (updated: {w.get('updated', '—')})"
                )
            lines.append("")
            lines.append("</details>")
            lines.append("")
        if wb_archived:
            lines.append(
                f"<details><summary>archived ({len(wb_archived)})</summary>"
            )
            lines.append("")
            for w in wb_archived:
                lines.append(
                    f"- {w.get('id', '')} {w.get('title', '')[:60]}"
                )
            lines.append("")
            lines.append("</details>")
            lines.append("")

    # 完了ログ (直近5件)
    lines.append("## ✅ 直近の完了 Task (最新5件)")
    lines.append("")
    done_tasks = sorted(
        task_by_status.get("done", []),
        key=lambda t: extract_closed_date(t) or datetime.min,
        reverse=True,
    )[:5]
    if done_tasks:
        for t in done_tasks:
            ref = t.get("sprint_ref") or "—"
            closed = extract_closed_date(t)
            closed_label = closed.strftime("%Y-%m-%d") if closed else "?"
            lines.append(
                f"- ~~{t['id']}~~ {t['text'][:60]}… ({closed_label}, {ref})"
            )
        lines.append("")

    # フッター
    lines.append("---")
    lines.append("")
    lines.append(
        f"*全管理層統合: Task({len(tasks)}) + Seed({len(seeds)}) + Question({len(questions)}) + Wish({len(wishes)}) + Backlog({len(backlog)}) + Whiteboard({len(whiteboards)}) = **{len(tasks)+len(seeds)+len(questions)+len(wishes)+len(backlog)+len(whiteboards)}件***"
    )
    lines.append("")
    lines.append(
        "*温度階層: ⚡即時(Task) → 🌱芽(Seed) → 🟠WARM(Wish) → ❄️COLD(Backlog)  |  📝NOTES(Whiteboard: 戦略ノート)*"
    )
    lines.append("")
    lines.append(
        "生成コマンド: `python pinakas/generate_dashboard.py`"
    )

    # -- 書き出し --
    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ ダッシュボード生成完了: {OUTPUT_FILE}")
    print(f"   Task: {len(tasks)} 件 (open: {n_task_open}, done: {n_task_done})")
    print(f"   Seed: {len(seeds)} 件 (open: {n_seed_open})")
    print(f"   Wish: {len(wishes)} 件 (open: {n_wish_open})")
    print(f"   Backlog: {len(backlog)} 件 (open: {n_backlog_open})")
    print(f"   Question: {len(questions)} 件")
    print(f"   Whiteboard: {len(whiteboards)} 件 (active: {n_wb_active})")
    print(f"   合計: {len(tasks)+len(seeds)+len(questions)+len(wishes)+len(backlog)+len(whiteboards)} 件")


if __name__ == "__main__":
    generate_dashboard()
