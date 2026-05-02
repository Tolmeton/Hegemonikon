"""
Experiment 0 — Dry Run
条件 A (NL) と条件 B (構造構文) で T1 を 1 回ずつ実行し、出力を比較する。

使い方:
  cd "10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/exp0_structural_precision"
  source ../../../../../../.venv/bin/activate
  python dry_run.py
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import anthropic

# --- 設定 ---
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 8192
TEMPERATURE = 0.7

TASK_T1 = (
    "以下の問いについて、深い内部透徹を実行してください。\n\n"
    "問い: なぜ複雑系はある閾値を超えると自己組織化するのか\n\n"
    "上記のシステムプロンプトで定義された認知スキルの手順に従い、"
    "L2（標準モード: P-0, P-1, P-2, P-5）で実行してください。"
)

EXP_DIR = Path(__file__).parent
RESULTS_DIR = EXP_DIR / "results"


def load_condition_a() -> str:
    """条件 A (NL) — v2 等量設計"""
    path = EXP_DIR / "condition_A_v2_noe.md"
    return path.read_text(encoding="utf-8")


def load_condition_b() -> str:
    """条件 B (構造構文) — v2 等量設計"""
    path = EXP_DIR / "condition_B_v2_noe.md"
    return path.read_text(encoding="utf-8")


def run_trial(client: anthropic.Anthropic, condition_name: str, system_prompt: str) -> dict:
    """1 試行を実行"""
    print(f"\n{'='*60}")
    print(f"条件 {condition_name} を実行中...")
    print(f"System prompt: {len(system_prompt)} chars")
    print(f"{'='*60}")

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=system_prompt,
        messages=[{"role": "user", "content": TASK_T1}],
    )

    output_text = response.content[0].text
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }

    print(f"完了: {usage['input_tokens']} input / {usage['output_tokens']} output tokens")
    print(f"出力冒頭 200 chars:\n{output_text[:200]}...")

    return {
        "condition": condition_name,
        "model": MODEL,
        "task": "T1",
        "timestamp": datetime.now().isoformat(),
        "system_prompt_chars": len(system_prompt),
        "usage": usage,
        "output": output_text,
    }


def main():
    # API キーの確認
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY が設定されていません", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic()
    RESULTS_DIR.mkdir(exist_ok=True)

    # 条件の読み込み
    condition_a = load_condition_a()
    condition_b = load_condition_b()

    print(f"条件 A (NL): {len(condition_a)} chars")
    print(f"条件 B (構造): {len(condition_b)} chars")
    print(f"差分: {len(condition_b) - len(condition_a):+d} chars")

    # 実行
    result_a = run_trial(client, "A", condition_a)
    result_b = run_trial(client, "B", condition_b)

    # 保存
    for result in [result_a, result_b]:
        cond = result["condition"]
        path = RESULTS_DIR / f"dry_run_v2_{cond}_T1.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n保存: {path}")

        # 出力全文も別ファイルに保存 (読みやすさ)
        txt_path = RESULTS_DIR / f"dry_run_v2_{cond}_T1_output.md"
        txt_path.write_text(result["output"], encoding="utf-8")
        print(f"出力: {txt_path}")

    # サマリー
    print(f"\n{'='*60}")
    print("ドライラン完了")
    print(f"{'='*60}")
    print(f"条件 A: {result_a['usage']['output_tokens']} output tokens")
    print(f"条件 B: {result_b['usage']['output_tokens']} output tokens")
    print(f"\n次のステップ:")
    print("  1. results/dry_run_v2_A_T1_output.md と dry_run_v2_B_T1_output.md を肉眼で比較")
    print("  2. rubric の 6 次元で差が見えるか確認")
    print("  3. 問題があれば条件 A/B の調整 or rubric の修正")


if __name__ == "__main__":
    main()
