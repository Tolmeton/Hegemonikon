#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- scripts/ tape 可視化ダッシュボード
"""
Tape Dashboard — WF 実行統計の可視化 CLI

Usage:
    python scripts/tape_dashboard.py              # 直近 7 日間
    python scripts/tape_dashboard.py --days 1     # 今日のみ
    python scripts/tape_dashboard.py --json       # JSON 出力
"""
import argparse
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

TAPE_DIR = Path(__file__).resolve().parents[1] / "nous" / "tape"


def load_all_entries(days: int = 7) -> list[dict]:
    """指定日数以内の全 tape エントリを読み込む。"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    entries = []
    for f in sorted(TAPE_DIR.glob("tape_*.jsonl")):
        try:
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    ts = datetime.fromisoformat(entry["ts"])
                    if ts >= cutoff:
                        entries.append(entry)
        except (json.JSONDecodeError, KeyError):
            continue
    return entries


def compute_stats(entries: list[dict]) -> dict:
    """エントリから WF 別統計を計算。"""
    wf_stats: dict[str, dict] = defaultdict(lambda: {
        "runs": 0, "success": 0, "fail": 0,
        "total_ms": 0.0, "last": "",
        "phases": defaultdict(int),
    })

    for e in entries:
        wf = e.get("wf", "unknown")
        step = e.get("step", "")

        # COMPLETE/FAILED は最終サマリー → run カウント
        if step in ("COMPLETE", "FAILED"):
            wf_stats[wf]["runs"] += 1
            if step == "COMPLETE":
                wf_stats[wf]["success"] += 1
            else:
                wf_stats[wf]["fail"] += 1
            wf_stats[wf]["total_ms"] += e.get("duration_ms", 0)
            wf_stats[wf]["last"] = e.get("ts", "")[:16]
        else:
            # フェーズ単位のカウント
            wf_stats[wf]["phases"][step] += 1

    return dict(wf_stats)


def format_table(stats: dict) -> str:
    """統計をテーブル形式にフォーマット。"""
    if not stats:
        return "📊 tape ログなし"

    lines = []
    now = datetime.now().strftime("%Y-%m-%d")
    lines.append(f"📊 Tape Dashboard ({now})")
    lines.append("━" * 60)
    lines.append(f"{'WF':<12}| {'Runs':>4} | {'✅':>3} | {'❌':>3} | {'Avg(ms)':>8} | {'Last':>16}")
    lines.append("-" * 60)

    total_runs = 0
    total_success = 0

    for wf, s in sorted(stats.items()):
        runs = s["runs"]
        if runs == 0:
            continue
        avg_ms = int(s["total_ms"] / runs) if runs else 0
        lines.append(
            f"{wf:<12}| {runs:>4} | {s['success']:>3} | {s['fail']:>3} | {avg_ms:>8} | {s['last']:>16}"
        )
        total_runs += runs
        total_success += s["success"]

    lines.append("━" * 60)
    rate = f"{total_success / total_runs * 100:.0f}%" if total_runs else "N/A"
    lines.append(f"Total: {total_runs} runs, {rate} success rate")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Tape Dashboard")
    parser.add_argument("--days", type=int, default=7, help="集計日数 (default: 7)")
    parser.add_argument("--json", action="store_true", help="JSON 出力")
    args = parser.parse_args()

    entries = load_all_entries(args.days)
    stats = compute_stats(entries)

    if args.json:
        # defaultdict を通常の dict に変換
        clean = {}
        for wf, s in stats.items():
            clean[wf] = {k: (dict(v) if isinstance(v, defaultdict) else v) for k, v in s.items()}
        print(json.dumps(clean, ensure_ascii=False, indent=2))
    else:
        print(format_table(stats))


if __name__ == "__main__":
    main()
