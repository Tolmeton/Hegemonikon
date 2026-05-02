#!/usr/bin/env python3
"""E1 圧縮タスクを Ochema cortex 経由で一括実行するスクリプト

使い方:
  python3 execute_compression.py          # 圧縮を実行
  python3 execute_compression.py --test   # テストを実行
"""

import json
import sys
import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "results"
COMPRESSED_DIR = BASE_DIR / "compressed"
RESPONSES_DIR = RESULTS_DIR / "responses"


def call_ochema(message: str, model: str = "claude-sonnet-4-20250514", max_tokens: int = 2048) -> str:
    """Ochema MCP の cortex モードで LLM を呼び出す (同期)"""
    # MCP 呼び出しの代わりに、直接 Gemini/Claude API を使う
    # ここでは hub_execute 経由を想定したスタブ
    # 実際の実行はセッション内で mcp_ochema_ask を使う
    raise NotImplementedError("MCP 経由で実行してください")


def execute_compressions_manual():
    """圧縮タスクを表示し、手動実行用のプロンプトを生成"""
    tasks_path = RESULTS_DIR / "compression_tasks.json"
    with open(tasks_path, encoding="utf-8") as f:
        tasks = json.load(f)

    COMPRESSED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"圧縮タスク: {len(tasks)} 件")
    print(f"各タスクの compression_prompt を Claude (temperature=0) に投げ、")
    print(f"結果を compressed/{{task_id}}.txt に保存してください。")
    print()

    # 最初の3件を表示
    for task in tasks[:3]:
        print(f"--- {task['task_id']} ---")
        print(f"形式: {task['format']}, 圧縮率: {task['level']} ({task['ratio']*100:.0f}%)")
        print(f"元の文字数: {task['original_char_count']}")
        print(f"目標文字数: {int(task['original_char_count'] * task['ratio'])}")
        print()

    # バッチ形式で書き出し (Ochema chat 用)
    batch_path = RESULTS_DIR / "compression_batch.jsonl"
    with open(batch_path, "w", encoding="utf-8") as f:
        for task in tasks:
            f.write(json.dumps({
                "task_id": task["task_id"],
                "message": task["compression_prompt"],
                "model": "claude-sonnet-4-20250514",
                "temperature": 0,
            }, ensure_ascii=False) + "\n")

    print(f"バッチファイルを {batch_path} に保存しました")


def generate_test_batch():
    """テストタスクのバッチを生成"""
    tests_path = RESULTS_DIR / "test_tasks.json"
    with open(tests_path, encoding="utf-8") as f:
        tasks = json.load(f)

    RESPONSES_DIR.mkdir(parents=True, exist_ok=True)

    batch_path = RESULTS_DIR / "test_batch.jsonl"
    with open(batch_path, "w", encoding="utf-8") as f:
        for task in tasks:
            compressed_path = BASE_DIR / task["compressed_prompt_path"]
            if not compressed_path.exists():
                continue
            system_prompt = compressed_path.read_text(encoding="utf-8")
            f.write(json.dumps({
                "test_id": task["test_id"],
                "system_prompt": system_prompt,
                "user_message": task["question"],
                "model": "gemini-2.5-flash",
                "temperature": 0,
            }, ensure_ascii=False) + "\n")

    print(f"テストバッチを {batch_path} に保存")
    print(f"圧縮済みプロンプトが見つかったタスク数を確認中...")

    found = sum(1 for t in tasks if (BASE_DIR / t["compressed_prompt_path"]).exists())
    print(f"  圧縮済み: {found}/{len(tasks)}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        generate_test_batch()
    else:
        execute_compressions_manual()
