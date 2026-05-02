#!/usr/bin/env python3
# PROOF: [L3/ユーティリティ] <- mekhane/symploke/ O4→結果収集が必要→collect_results が担う
"""
Jules Specialist レビュー結果収集パイプライン v1.0

run_specialists.py の実行結果を収集・集計・分析し、
/boot で消化可能な形式で保存する。

Output:
  - logs/specialist_daily/digest_YYYYMMDD.md  (人間向けダイジェスト)
  - logs/specialist_daily/digest_YYYYMMDD.json (機械向けデータ)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

# PURPOSE: 結果ファイルを探索
def find_result_files(
    base_dir: str = "logs/specialist_daily",
    date_filter: str = "",
    days_back: int = 1,
) -> list[Path]:
    """結果JSONファイルを探索する

    Args:
        base_dir: 結果ディレクトリ
        date_filter: 特定日付 (YYYYMMDD)
        days_back: 過去N日分を取得

    ファイル名パターン (両対応):
        - YYYYMMDD_HHMM_*.json  (cron 実行)
        - run_YYYYMMDD_*.json   (手動実行)
    """
    result_dir = Path(base_dir)
    if not result_dir.exists():
        return []

    # 対象日付を決定
    if date_filter:
        dates = [date_filter]
    else:
        dates = []
        for d in range(days_back):
            dt = datetime.now() - timedelta(days=d)
            dates.append(dt.strftime("%Y%m%d"))

    # 全 JSON を走査し、日付でフィルタ
    files = []
    for f in sorted(result_dir.glob("*.json"), reverse=True):
        if f.name.startswith("digest_"):
            continue
        for date_prefix in dates:
            if date_prefix in f.name:
                files.append(f)
                break
    return files


# PURPOSE: 結果ファイルを読んで集計する
def aggregate_results(files: list[Path]) -> dict:
    """複数の結果ファイルを集計"""
    summary = {
        "total_runs": 0,
        "total_files_reviewed": 0,
        "total_specialists": 0,
        "total_started": 0,
        "total_failed": 0,
        "by_file": {},
        "by_category": Counter(),
        "errors": [],
        "sessions": [],
    }

    for fp in files:
        try:
            data = json.loads(fp.read_text())
        except (json.JSONDecodeError, OSError) as e:
            summary["errors"].append({"file": str(fp), "error": str(e)})
            continue

        summary["total_runs"] += 1

        # v4.0 形式
        if "files" in data:
            for file_entry in data["files"]:
                target = file_entry.get("target_file", "unknown")
                specialists_count = file_entry.get("specialists_count", 0)
                started = file_entry.get("started", 0)
                failed = file_entry.get("failed", 0)

                summary["total_files_reviewed"] += 1
                summary["total_specialists"] += specialists_count
                summary["total_started"] += started
                summary["total_failed"] += failed

                if target not in summary["by_file"]:
                    summary["by_file"][target] = {"started": 0, "failed": 0, "total": 0}
                summary["by_file"][target]["started"] += started
                summary["by_file"][target]["failed"] += failed
                summary["by_file"][target]["total"] += specialists_count

                # セッション追跡
                for result in file_entry.get("results", []):
                    if "session_id" in result:
                        summary["sessions"].append({
                            "session_id": result["session_id"],
                            "specialist": result.get("specialist_id", ""),
                            "category": result.get("category", ""),
                            "target": target,
                        })
                    if "category" in result:
                        summary["by_category"][result["category"]] += 1

        # v3.0 形式 (後方互換)
        elif "results" in data:
            target = data.get("target_file", "unknown")
            results = data.get("results", [])
            summary["total_files_reviewed"] += 1
            summary["total_specialists"] += len(results)
            started = sum(1 for r in results if "session_id" in r)
            failed = sum(1 for r in results if "error" in r)
            summary["total_started"] += started
            summary["total_failed"] += failed

    return summary


# PURPOSE: Markdown ダイジェストを生成
def generate_digest(summary: dict, date_str: str = "") -> str:
    """人間向けダイジェスト (Markdown) を生成"""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    total = summary["total_specialists"]
    started = summary["total_started"]
    failed = summary["total_failed"]
    rate = (started / total * 100) if total else 0

    lines = [
        f"# 📊 Specialist Daily Digest — {date_str}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|:-------|------:|",
        f"| Runs | {summary['total_runs']} |",
        f"| Files reviewed | {summary['total_files_reviewed']} |",
        f"| Total specialists | {total} |",
        f"| Started | {started} ({rate:.0f}%) |",
        f"| Failed | {failed} |",
        "",
    ]

    # ファイル別
    if summary["by_file"]:
        lines.append("## By File")
        lines.append("")
        lines.append("| File | Started | Failed | Total |")
        lines.append("|:-----|--------:|-------:|------:|")
        for fname, stats in sorted(summary["by_file"].items()):
            lines.append(
                f"| `{fname}` | {stats['started']} | {stats['failed']} | {stats['total']} |"
            )
        lines.append("")

    # カテゴリ別
    if summary["by_category"]:
        lines.append("## By Category")
        lines.append("")
        lines.append("| Category | Count |")
        lines.append("|:---------|------:|")
        for cat, count in summary["by_category"].most_common(20):
            lines.append(f"| {cat} | {count} |")
        lines.append("")

    # エラー
    if summary["errors"]:
        lines.append("## ⚠️ Errors")
        lines.append("")
        for err in summary["errors"]:
            lines.append(f"- `{err['file']}`: {err['error']}")
        lines.append("")

    # セッション数
    lines.append(f"---")
    lines.append(f"*Active sessions: {len(summary['sessions'])}*")

    return "\n".join(lines)


# PURPOSE: メインエントリポイント
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Jules Specialist Results Collector v1.0")
    parser.add_argument("--date", "-d", default="", help="Date filter (YYYYMMDD)")
    parser.add_argument("--days", type=int, default=1, help="Days back to collect")
    parser.add_argument("--dir", default="logs/specialist_daily", help="Results directory")
    parser.add_argument("--output", "-o", default="", help="Output directory for digest")
    parser.add_argument("--dry-run", action="store_true", help="Print digest without saving")
    parser.add_argument("--json-only", action="store_true", help="Output JSON only")

    args = parser.parse_args()

    # 結果ファイル探索
    files = find_result_files(
        base_dir=args.dir,
        date_filter=args.date,
        days_back=args.days,
    )

    if not files:
        print(f"No result files found in {args.dir}")
        return

    print(f"Found {len(files)} result file(s)")

    # 集計
    summary = aggregate_results(files)

    # 日付文字列
    date_str = args.date if args.date else datetime.now().strftime("%Y%m%d")

    if args.json_only or args.dry_run:
        if args.json_only:
            # JSON 出力
            print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
        else:
            # Markdown 出力
            digest = generate_digest(summary, date_str)
            print(digest)
        return

    # 保存
    output_dir = Path(args.output) if args.output else Path(args.dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Markdown
    digest = generate_digest(summary, date_str)
    md_path = output_dir / f"digest_{date_str}.md"
    md_path.write_text(digest)
    print(f"Digest: {md_path}")

    # JSON
    json_path = output_dir / f"digest_{date_str}.json"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    print(f"Data: {json_path}")


if __name__ == "__main__":
    main()
