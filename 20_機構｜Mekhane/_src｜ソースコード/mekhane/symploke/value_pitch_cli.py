from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/
# PURPOSE: /bye Step 2.5π の補助 — Git log からタスク収集し Value Pitch 骨格を出力
"""
PROOF: [L2/インフラ] このファイルは存在しなければならない

A0 → /bye の Value Pitch は成果ごとの意義を語る (Step 2.5π)
   → 成果タスクの手動収集は面倒
   → value_pitch_cli.py が Git log から自動収集し骨格を出力する:
     1. git log からコミットメッセージを取得
     2. value_pitch_proposer で Angle 推定
     3. 骨格ドラフトを stdout に出力

Q.E.D.
"""


import argparse
import subprocess
import sys

# 同じパッケージから
from mekhane.symploke.value_pitch_proposer import (
    format_proposals,
    propose_pitches,
    tasks_from_git_stat,
)


# PURPOSE: [L2-auto] _get_git_log の関数定義
def _get_git_log(n: int, cwd: str | None = None) -> list[dict]:
    """Git log から直近 N コミットの情報を取得。"""
    try:
        result = subprocess.run(
            ["git", "log", f"-{n}", "--pretty=format:%s"],
            capture_output=True,
            text=True,
            cwd=cwd or ".",
        )
        if result.returncode != 0:
            print(f"⚠️ git log 失敗: {result.stderr.strip()}", file=sys.stderr)
            return []
        messages = [m.strip() for m in result.stdout.strip().split("\n") if m.strip()]
        return messages
    except FileNotFoundError:
        print("⚠️ git が見つかりません", file=sys.stderr)
        return []


# PURPOSE: [L2-auto] _get_git_diff_stat の関数定義
def _get_git_diff_stat(n: int, cwd: str | None = None) -> list[str]:
    """Git log から直近 N コミットの変更ファイルを取得。"""
    try:
        result = subprocess.run(
            ["git", "log", f"-{n}", "--pretty=format:", "--name-only"],
            capture_output=True,
            text=True,
            cwd=cwd or ".",
        )
        if result.returncode != 0:
            return []
        files = list(set(f.strip() for f in result.stdout.strip().split("\n") if f.strip()))
        return files
    except FileNotFoundError:
        return []


# PURPOSE: value_pitch_cli の main 処理を実行する
def main():
    parser = argparse.ArgumentParser(
        description="Value Pitch 骨格生成 — Git log からタスク収集",
        epilog="例: python -m mekhane.symploke.value_pitch_cli --git-log 3",
    )
    parser.add_argument(
        "--git-log",
        type=int,
        default=3,
        metavar="N",
        help="直近 N コミットからタスク収集 (default: 3)",
    )
    parser.add_argument(
        "--cwd",
        type=str,
        default=None,
        help="Git リポジトリのパス (default: カレントディレクトリ)",
    )

    args = parser.parse_args()

    # Git log からタスク収集
    messages = _get_git_log(args.git_log, cwd=args.cwd)
    if not messages:
        print("> Value Pitch: コミットが見つかりません。\n")
        return

    files = _get_git_diff_stat(args.git_log, cwd=args.cwd)
    tasks = tasks_from_git_stat(messages, files_changed=files)

    # Angle 推定 + 骨格生成
    proposals = propose_pitches(tasks)
    output = format_proposals(proposals)

    # Gallery リマインダー
    print("━" * 60)
    print("🔥 書く前に pitch_gallery.md を読め。温度を上げろ。")
    print("━" * 60)
    print()
    print(output)


if __name__ == "__main__":
    main()
