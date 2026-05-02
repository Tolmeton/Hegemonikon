#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- scripts/ Context Rot 環境強制検知
"""
Context Sentinel — Context Rot 環境強制検知スクリプト
=====================================================

LS ログから N chat messages を自動検出し、
閾値超過時にアクションを強制実行する。

N-4 (旧 BC-18: コンテキスト予算意識) の環境強制実装。
「意志で気をつける」→「環境が強制する」への転換。

Usage:
    python scripts/context_sentinel.py              # 現在の N を表示
    python scripts/context_sentinel.py --json        # JSON 出力
    python scripts/context_sentinel.py --savepoint   # Savepoint テンプレート生成
    python scripts/context_sentinel.py --watch 5     # 5秒間隔で監視

Exit codes:
    0 = 🟢 健全 (N ≤ 30)
    1 = 🟡 注意 (31-40) — Savepoint 推奨
    2 = 🟠 危険予兆 (41-50) — 新規タスク停止
    3 = 🔴 危険 (> 50) — /bye 強制
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# =============================================================================
# Constants
# =============================================================================

# PURPOSE: N-4 (旧 BC-18) の閾値定義
THRESHOLDS = {
    "green": 30,   # ≤ 30: 健全
    "yellow": 40,  # 31-40: 注意
    "orange": 50,  # 41-50: 危険予兆
    # > 50: 🔴 危険
}

LOG_BASE = Path.home() / ".config" / "Antigravity" / "logs"
MNEME_DIR = Path.home() / "oikos" / "mneme" / ".hegemonikon" / "sessions"
WS_FILTER = os.environ.get("AGQ_WORKSPACE", "hegemonikon")
N_PATTERN = re.compile(r"with (\d+) chat messages")


# =============================================================================
# Core Logic
# =============================================================================

def find_antigravity_log() -> Optional[Path]:
    # PURPOSE: 最新の Antigravity.log を検出する
    """最新の Antigravity.log を検出"""
    if not LOG_BASE.exists():
        return None

    # 最新のセッションディレクトリを探す
    sessions = sorted(LOG_BASE.glob("20*"), reverse=True)
    for session_dir in sessions:
        logs = list(session_dir.rglob("**/google.antigravity/Antigravity.log"))
        if logs:
            # 最大サイズのログを優先
            logs.sort(key=lambda p: p.stat().st_size, reverse=True)
            if logs[0].stat().st_size > 0:
                return logs[0]
    return None


def extract_n_chat_messages(log_path: Path) -> list[int]:
    # PURPOSE: LS ログから N chat messages の推移を抽出する
    """ログから N chat messages の推移を抽出"""
    values = []
    try:
        with open(log_path, "r", errors="replace") as f:
            for line in f:
                match = N_PATTERN.search(line)
                if match:
                    values.append(int(match.group(1)))
    except Exception:
        pass
    return values


def get_current_n(log_path: Optional[Path] = None) -> int:
    # PURPOSE: 現在の N chat messages を取得する (最新値)
    """現在の N chat messages (最新値)"""
    if log_path is None:
        log_path = find_antigravity_log()
    if log_path is None:
        return 0
    values = extract_n_chat_messages(log_path)
    return values[-1] if values else 0


def classify(n: int) -> dict:
    # PURPOSE: N chat messages を 4段階 (🟢🟡🟠🔴) に分類する
    """N を 4段階に分類"""
    if n <= THRESHOLDS["green"]:
        return {
            "level": "green",
            "emoji": "🟢",
            "label": "健全",
            "action": "通常作業",
            "exit_code": 0,
        }
    elif n <= THRESHOLDS["yellow"]:
        return {
            "level": "yellow",
            "emoji": "🟡",
            "label": "注意",
            "action": "中間セーブ (Savepoint) を強制実行",
            "exit_code": 1,
        }
    elif n <= THRESHOLDS["orange"]:
        return {
            "level": "orange",
            "emoji": "🟠",
            "label": "危険予兆",
            "action": "新規タスク受付停止。現タスク完了に集中。/bye を提案",
            "exit_code": 2,
        }
    else:
        return {
            "level": "red",
            "emoji": "🔴",
            "label": "危険",
            "action": "/bye 強制。Handoff を自動生成し新セッションへ移行",
            "exit_code": 3,
        }


# =============================================================================
# Output Formatters
# =============================================================================

def format_human(n: int, history: list[int], log_path: Optional[Path]) -> str:
    # PURPOSE: 人間向けのコンソール表示をフォーマットする
    """人間向け表示"""
    cl = classify(n)
    lines = [
        "┌─────────────────────────────────────────────────┐",
        f"│ {cl['emoji']} Context Sentinel — N = {n}",
        "├─────────────────────────────────────────────────┤",
        f"│ 状態: {cl['label']}",
        f"│ アクション: {cl['action']}",
    ]
    if history:
        trend = history[-min(5, len(history)):]
        trend_str = " → ".join(str(v) for v in trend)
        lines.append(f"│ 推移 (直近): {trend_str}")
    if log_path:
        lines.append(f"│ ログ: .../{log_path.parent.parent.parent.name}/.../{log_path.name}")
    lines.append(f"│ 時刻: {datetime.now().strftime('%H:%M:%S')}")
    lines.append("└─────────────────────────────────────────────────┘")
    return "\n".join(lines)


def format_json(n: int, history: list[int]) -> str:
    # PURPOSE: n8n / プログラム連携用の JSON 出力をフォーマットする
    """JSON 出力"""
    cl = classify(n)
    return json.dumps({
        "n": n,
        "level": cl["level"],
        "label": cl["label"],
        "action": cl["action"],
        "exit_code": cl["exit_code"],
        "history": history[-10:],
        "peak": max(history) if history else 0,
        "timestamp": datetime.now().isoformat(),
    }, ensure_ascii=False, indent=2)


def generate_savepoint_template(n: int) -> str:
    # PURPOSE: Savepoint テンプレートを生成する (🟡遷移時)
    """Savepoint テンプレート"""
    now = datetime.now()
    filename = f"savepoint_{now.strftime('%Y-%m-%d_%H%M')}.md"
    filepath = MNEME_DIR / filename

    template = f"""# Savepoint — {now.strftime('%Y-%m-%d %H:%M')}

> Context Sentinel: N = {n} (🟡 注意)

## 今やっていること

<!-- ここに現在のタスクを記載 -->

## Creator の判断

<!-- 重要な意思決定を記載 -->

## 試して失敗したもの

<!-- 失敗した試みを記載 -->

## 次にやること

<!-- 次のアクションを記載 -->
"""
    try:
        MNEME_DIR.mkdir(parents=True, exist_ok=True)
        filepath.write_text(template, encoding="utf-8")
        return f"📸 Savepoint template: {filepath}"
    except Exception as e:
        return f"⚠️ Savepoint 生成失敗: {e}\n\n{template}"


# =============================================================================
# CLI
# =============================================================================

def main():
    # PURPOSE: Context Sentinel CLI エントリーポイント
    parser = argparse.ArgumentParser(
        description="Context Sentinel — N-4 (旧 BC-18) 環境強制検知"
    )
    parser.add_argument("--json", action="store_true", help="JSON 出力")
    parser.add_argument("--savepoint", action="store_true", help="Savepoint テンプレート生成")
    parser.add_argument("--watch", type=int, metavar="SEC", help="監視モード (秒間隔)")
    parser.add_argument("--history", action="store_true", help="N の全推移を表示")
    args = parser.parse_args()

    log_path = find_antigravity_log()
    history = extract_n_chat_messages(log_path) if log_path else []
    n = history[-1] if history else 0
    cl = classify(n)

    if args.watch:
        try:
            while True:
                log_path = find_antigravity_log()
                history = extract_n_chat_messages(log_path) if log_path else []
                n = history[-1] if history else 0
                cl = classify(n)
                os.system("clear" if os.name != "nt" else "cls")
                print(format_human(n, history, log_path))
                if cl["exit_code"] >= 1:
                    print(f"\n⚠️  {cl['action']}")
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print("\n👋 監視終了")
            sys.exit(0)

    if args.savepoint:
        print(generate_savepoint_template(n))
        sys.exit(cl["exit_code"])

    if args.history and history:
        print("N chat messages 推移:")
        for i, v in enumerate(history):
            marker = classify(v)["emoji"]
            print(f"  [{i+1:3d}] {marker} {v}")
        print(f"\nPeak: {max(history)}, Current: {n}")
        sys.exit(cl["exit_code"])

    if args.json:
        print(format_json(n, history))
    else:
        print(format_human(n, history, log_path))

    sys.exit(cl["exit_code"])


if __name__ == "__main__":
    main()
