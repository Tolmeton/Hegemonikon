from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/ドメイン] <- mekhane/symploke/ O4→scheduler異常検知→自律監視
"""F22: Scheduler Anomaly Detector — 成功率低下や連続失敗を検知し Sympatheia に通知する。

ログディレクトリのスケジューラ実行結果を分析し、
異常パターン（成功率急落、連続失敗、ゼロタスク週）を検出する。

Usage:
    python scheduler_anomaly.py [--days 7] [--notify]
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_DIR = _PROJECT_ROOT / "logs" / "scheduler"

# 異常判定閾値
THRESHOLD_SUCCESS_RATE = 0.6    # 成功率がこれ以下で警告
THRESHOLD_CONSECUTIVE_FAIL = 3  # 連続失敗回数
THRESHOLD_MIN_TASKS_PER_WEEK = 3  # 週あたり最小タスク数


# PURPOSE: [L2-auto] AnomalyReport のクラス定義
class AnomalyReport:
    """異常検知レポート。"""
    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(self) -> None:
        self.anomalies: list[dict] = []
        self.stats: dict = {}

    # PURPOSE: [L2-auto] add の関数定義
    def add(self, kind: str, severity: str, message: str, data: Optional[dict] = None) -> None:
        self.anomalies.append({
            "kind": kind,
            "severity": severity,
            "message": message,
            "data": data or {},
            "detected_at": datetime.now().isoformat(),
        })

    # PURPOSE: [L2-auto] has_critical の関数定義
    @property
    def has_critical(self) -> bool:
        return any(a["severity"] == "CRITICAL" for a in self.anomalies)

    # PURPOSE: [L2-auto] has_warnings の関数定義
    @property
    def has_warnings(self) -> bool:
        return len(self.anomalies) > 0

    # PURPOSE: [L2-auto] to_dict の関数定義
    def to_dict(self) -> dict:
        return {
            "total_anomalies": len(self.anomalies),
            "has_critical": self.has_critical,
            "anomalies": self.anomalies,
            "stats": self.stats,
            "generated_at": datetime.now().isoformat(),
        }


# PURPOSE: [L2-auto] _load_recent_logs の関数定義
def _load_recent_logs(days: int = 7) -> list[dict]:
    """直近 N 日分のスケジューラログを読み込む。"""
    if not LOG_DIR.exists():
        return []

    cutoff = datetime.now() - timedelta(days=days)
    logs = []

    for f in sorted(LOG_DIR.glob("scheduler_*.json"), reverse=True):
        try:
            data = json.loads(f.read_text())
            # ファイル名からタイムスタンプ推定: scheduler_YYYYMMDD_HHMM.json
            name_parts = f.stem.replace("scheduler_", "").split("_")
            if len(name_parts) >= 1:
                date_str = name_parts[0]
                file_date = datetime.strptime(date_str, "%Y%m%d")
                if file_date >= cutoff:
                    data["_file"] = str(f.name)
                    data["_date"] = file_date.isoformat()
                    logs.append(data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse {f}: {e}")

    return logs


# PURPOSE: [L2-auto] detect_anomalies の関数定義
def detect_anomalies(days: int = 7) -> AnomalyReport:
    """スケジューラログを分析し異常を検知する。"""
    report = AnomalyReport()
    logs = _load_recent_logs(days)

    if not logs:
        report.stats = {"total_runs": 0, "period_days": days}
        report.add(
            kind="no_data",
            severity="WARNING",
            message=f"直近 {days} 日間にスケジューラログが見つかりません",
        )
        return report

    # 基本統計
    total_tasks = sum(log.get("total_tasks", 0) for log in logs)
    total_started = sum(log.get("total_started", 0) for log in logs)
    total_failed = sum(log.get("total_failed", 0) for log in logs)
    success_rate = (total_started - total_failed) / total_started if total_started > 0 else 0.0

    report.stats = {
        "total_runs": len(logs),
        "total_tasks": total_tasks,
        "total_started": total_started,
        "total_failed": total_failed,
        "success_rate": round(success_rate, 3),
        "period_days": days,
    }

    # 異常1: 全体成功率低下
    if success_rate < THRESHOLD_SUCCESS_RATE and total_started > 0:
        report.add(
            kind="low_success_rate",
            severity="CRITICAL" if success_rate < 0.3 else "WARNING",
            message=f"成功率が {success_rate:.0%} に低下 (閾値: {THRESHOLD_SUCCESS_RATE:.0%})",
            data={"success_rate": success_rate, "threshold": THRESHOLD_SUCCESS_RATE},
        )

    # 異常2: 連続失敗
    consecutive_fails = 0
    max_consecutive = 0
    for log in logs:  # newest first
        failed = log.get("total_failed", 0)
        started = log.get("total_started", 0)
        if started > 0 and failed / started > 0.5:
            consecutive_fails += 1
            max_consecutive = max(max_consecutive, consecutive_fails)
        else:
            consecutive_fails = 0

    if max_consecutive >= THRESHOLD_CONSECUTIVE_FAIL:
        report.add(
            kind="consecutive_failures",
            severity="CRITICAL",
            message=f"{max_consecutive} 回連続で過半数が失敗",
            data={"consecutive": max_consecutive, "threshold": THRESHOLD_CONSECUTIVE_FAIL},
        )

    # 異常3: タスク数不足 (活動低下)
    if len(logs) < THRESHOLD_MIN_TASKS_PER_WEEK and days >= 7:
        report.add(
            kind="low_activity",
            severity="WARNING",
            message=f"直近 {days} 日間の実行回数が {len(logs)} 回 (最小: {THRESHOLD_MIN_TASKS_PER_WEEK})",
            data={"runs": len(logs), "threshold": THRESHOLD_MIN_TASKS_PER_WEEK},
        )

    return report


# PURPOSE: [L2-auto] notify_sympatheia の関数定義
def notify_sympatheia(report: AnomalyReport) -> dict:
    """Sympatheia API に異常通知を送信する。"""
    import urllib.request

    payload = {
        "source": "scheduler_anomaly",
        "level": "CRITICAL" if report.has_critical else "WARNING",
        "title": f"Scheduler Anomaly: {len(report.anomalies)} issues detected",
        "body": "\n".join(a["message"] for a in report.anomalies),
        "data": report.to_dict(),
    }

    try:
        req = urllib.request.Request(
            "http://localhost:8392/api/sympatheia/notification",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            logger.info(f"Sympatheia notification sent: {result.get('id', 'unknown')}")
            return {"sent": True, "response": result}
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Failed to notify Sympatheia: {e}")
        return {"sent": False, "error": str(e)}


# CLI エントリポイント
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="F22: Scheduler Anomaly Detector")
    parser.add_argument("--days", type=int, default=7, help="Analysis period in days")
    parser.add_argument("--notify", action="store_true", help="Send to Sympatheia")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    report = detect_anomalies(days=args.days)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*50}")
        print(f"Scheduler Anomaly Report ({args.days} days)")
        print(f"{'='*50}")
        print(f"  Runs: {report.stats.get('total_runs', 0)}")
        print(f"  Rate: {report.stats.get('success_rate', 0):.0%}")
        if report.anomalies:
            print(f"\n⚠️  {len(report.anomalies)} anomalies detected:")
            for a in report.anomalies:
                icon = "🔴" if a["severity"] == "CRITICAL" else "🟡"
                print(f"  {icon} [{a['kind']}] {a['message']}")
        else:
            print("\n✅ No anomalies detected")

    if args.notify and report.has_warnings:
        result = notify_sympatheia(report)
        sent = "✅" if result["sent"] else "❌"
        print(f"\n  Sympatheia: {sent}")
