#!/usr/bin/env python3
# PROOF: [L2/分析] <- mekhane/symploke/ F9→閉ループ→jules_result_parser が担う
# PURPOSE: Jules セッション結果から Perspective 有用性を判定
"""
Jules Result Parser

Jules の PR/セッション結果を解析し、各 Perspective の有用性を判定する。
basanos_feedback.FeedbackStore と連携してフィードバックループを閉じる。

Integration:
    - basanos_feedback.py: FeedbackStore.record_usage(was_useful=True/False) に接続
    - jules_daily_scheduler.py: scheduler ログの session_id 拡張で紐付け
    - collect_and_update() を cron から定期実行

Usage:
    # CLI: 過去7日分の Jules 結果から有用性を判定
    python jules_result_parser.py analyze --days 7

    # プログラム: 単一セッション解析
    from jules_result_parser import JulesResultParser
    parser = JulesResultParser()
    result = parser.analyze_session("session-id-123")
"""

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent.parent
_SCHEDULER_LOG_DIR = _PROJECT_ROOT / "logs" / "specialist_daily"


# PURPOSE: セッション解析結果
@dataclass
class SessionAnalysis:
    """単一 Jules セッションの解析結果。"""
    session_id: str
    file_path: str
    specialist_name: str = ""
    perspective_id: str = ""  # BP-{domain}-{axis}
    status: str = "unknown"   # pending, completed, failed
    has_pr: bool = False
    pr_merged: bool = False
    pr_comments: int = 0
    was_useful: bool = False
    confidence: float = 0.0   # 判定の確信度

    # PURPOSE: [L2-auto] to_dict の関数定義
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "file_path": self.file_path,
            "specialist_name": self.specialist_name,
            "perspective_id": self.perspective_id,
            "status": self.status,
            "has_pr": self.has_pr,
            "pr_merged": self.pr_merged,
            "was_useful": self.was_useful,
            "confidence": self.confidence,
        }


# PURPOSE: 有用性判定ロジック
class UsefulnessJudge:
    """PR/セッション結果から有用性を判定するルール集。

    判定基準 (優先順):
        1. PR merged → useful (confidence: 0.9)
        2. PR with comments > 0 → useful (confidence: 0.7)
        3. PR closed without merge → not useful (confidence: 0.6)
        4. Session completed (no PR) → neutral (confidence: 0.3)
        5. Session failed → not useful (confidence: 0.8)
    """

    # PURPOSE: [L2-auto] judge の関数定義
    @staticmethod
    def judge(analysis: SessionAnalysis) -> tuple[bool, float]:
        """有用性と確信度を返す。"""
        if analysis.status == "failed":
            return False, 0.8

        if analysis.has_pr:
            if analysis.pr_merged:
                return True, 0.9
            if analysis.pr_comments > 0:
                return True, 0.7
            # PR あるが merge も comment もなし → pending or closed
            return False, 0.6

        if analysis.status == "completed":
            # PR なしだが完了 → 判断困難
            return False, 0.3

        return False, 0.2


# PURPOSE: メインパーサー
class JulesResultParser:
    """Jules セッション結果を解析するパーサー。"""

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(self, log_dir: Optional[Path] = None):
        self._log_dir = log_dir or _SCHEDULER_LOG_DIR
        self._judge = UsefulnessJudge()

    # PURPOSE: [L2-auto] analyze_session の関数定義
    def analyze_session(self, session_id: str) -> SessionAnalysis:
        """単一セッションの結果を解析する。

        NOTE: API ベースの実装 (MCP jules_get_status) は外部呼び出しが必要。
        ここではローカルログベースの解析を行い、API 解析は呼び出し側に委譲。
        """
        analysis = SessionAnalysis(session_id=session_id, file_path="")

        # 拡張ログ (session_id 入り) を探す
        for log_file in sorted(self._log_dir.glob("scheduler_*.json"), reverse=True):
            try:
                data = json.loads(log_file.read_text())
                files = data.get("result", {}).get("files", [])
                if not isinstance(files, list):
                    files = data.get("files", [])

                for f in files:
                    sessions = f.get("sessions", [])
                    for s in sessions:
                        if s.get("session_id") == session_id:
                            analysis.file_path = f.get("file", "")
                            analysis.specialist_name = s.get("specialist", "")
                            analysis.perspective_id = s.get("perspective_id", "")
                            if "error" in s:
                                analysis.status = "failed"
                            else:
                                analysis.status = "completed"
                            break
            except (json.JSONDecodeError, KeyError):
                continue

        # 有用性判定
        useful, conf = self._judge.judge(analysis)
        analysis.was_useful = useful
        analysis.confidence = conf

        return analysis

    # PURPOSE: [L2-auto] analyze_log_file の関数定義
    def analyze_log_file(self, log_path: Path) -> list[SessionAnalysis]:
        """ログファイル内の全セッションを解析する。"""
        results = []

        try:
            data = json.loads(log_path.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return results

        files = data.get("files", [])
        if not isinstance(files, list):
            return results

        for f in files:
            sessions = f.get("sessions", [])
            file_path = f.get("file", "")
            for s in sessions:
                sid = s.get("session_id", "")
                if not sid:
                    continue

                analysis = SessionAnalysis(
                    session_id=sid,
                    file_path=file_path,
                    specialist_name=s.get("specialist", ""),
                    perspective_id=s.get("perspective_id", ""),
                    status="failed" if "error" in s else "completed",
                )

                useful, conf = self._judge.judge(analysis)
                analysis.was_useful = useful
                analysis.confidence = conf
                results.append(analysis)

        return results


# PURPOSE: フィードバックループ統合
def collect_and_update(days: int = 7) -> dict:
    """スケジューラーログの拡張版から Jules 結果を収集し、FeedbackStore に反映。

    collect_from_logs (basanos_feedback.py) の Phase 2 実装。
    """
    # Lazy import for basanos_feedback
    import sys
    if str(_THIS_DIR) not in sys.path:
        sys.path.insert(0, str(_THIS_DIR))
    from basanos_feedback import FeedbackStore

    store = FeedbackStore()
    parser = JulesResultParser()

    cutoff = datetime.now() - timedelta(days=days)
    processed = 0
    sessions_analyzed = 0
    useful_count = 0

    for log_file in sorted(_SCHEDULER_LOG_DIR.glob("scheduler_*.json")):
        try:
            data = json.loads(log_file.read_text())
            ts_str = data.get("timestamp", "")
            if not ts_str:
                continue
            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M")
            if ts < cutoff:
                continue
        except (json.JSONDecodeError, ValueError):
            continue

        analyses = parser.analyze_log_file(log_file)
        for a in analyses:
            if a.perspective_id:
                # domain と axis を perspective_id から抽出 (BP-{domain}-{axis})
                parts = a.perspective_id.split("-", 2)
                domain = parts[1] if len(parts) > 1 else ""
                axis = parts[2] if len(parts) > 2 else ""

                store.record_usage(
                    perspective_id=a.perspective_id,
                    domain=domain,
                    axis=axis,
                    was_useful=a.was_useful,
                )
                sessions_analyzed += 1
                if a.was_useful:
                    useful_count += 1

        processed += 1

    store.save()
    return {
        "processed_logs": processed,
        "sessions_analyzed": sessions_analyzed,
        "useful": useful_count,
        "not_useful": sessions_analyzed - useful_count,
    }


# PURPOSE: CLI
def main():
    parser = argparse.ArgumentParser(description="Jules Result Parser — F9 Feedback Loop")
    sub = parser.add_subparsers(dest="command")

    analyze_parser = sub.add_parser("analyze", help="Analyze Jules results and update feedback")
    analyze_parser.add_argument("--days", type=int, default=7, help="Days to look back")

    sub.add_parser("show", help="Show recent analysis results")

    args = parser.parse_args()

    if args.command == "analyze":
        result = collect_and_update(args.days)
        print(f"📊 Jules Result Analysis:")
        print(f"  Logs processed: {result['processed_logs']}")
        print(f"  Sessions analyzed: {result['sessions_analyzed']}")
        print(f"  Useful: {result['useful']}")
        print(f"  Not useful: {result['not_useful']}")
    elif args.command == "show":
        p = JulesResultParser()
        for log_file in sorted(_SCHEDULER_LOG_DIR.glob("scheduler_*.json"))[-3:]:
            print(f"\n📄 {log_file.name}:")
            analyses = p.analyze_log_file(log_file)
            for a in analyses:
                emoji = "✅" if a.was_useful else "❌"
                print(f"  {emoji} {a.session_id[:16]}... → {a.file_path} ({a.status}, conf={a.confidence:.1f})")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
