#!/usr/bin/env python3
"""
exp2_judge.py — CPS0' 盲検評価ランナー
========================================

results/ の raw_*.json を読み込み、blind judge が6次元評価を実行。
Usage:
  python exp2_judge.py [--dry-run] [--sample 5]

依存: pip install anthropic pyyaml

出力: results/judge_scores.csv
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"

JUDGE_MODEL = "claude-opus-4-6-20250514"
SECOND_JUDGE_MODEL = "gpt-4.1"  # for IRR subsample

JUDGE_SYSTEM = """あなたは学術的なテキスト品質の評価者です。
分析出力を受け取り、6つの次元で 0-5 のスコアを付けてください。
この出力がどのような条件で生成されたかは知らされていません。
純粋にテキストの質のみで評価してください。"""

JUDGE_USER_TEMPLATE = """以下の分析テキストを評価してください。

---
{response_text}
---

以下の6次元で 0-5 のスコアと簡潔な理由（各1文）を JSON で回答してください。

1. analytical_depth: 分析が表面的でなく、因果メカニズムの深層に到達しているか
   5=複数層のメカニズムを特定し各層間の関係を明示 / 3=主要メカニズムは特定 / 1=表面的
2. logical_coherence: 議論の論理構造が一貫しているか
   5=全主張が根拠に支えられ論理が途切れない / 3=概ね一貫 / 1=論理構造不明瞭
3. novelty: 独自の洞察があるか
   5=複数の独自視点で既存議論を拡張 / 3=一部独自 / 1=既知の要約
4. self_correction: 自らの限界を認識し反論を考慮しているか
   5=最強の反論を構成し統合 / 3=限界への言及あり / 1=自己批判なし
5. structural_organization: 論理的に構造化されているか
   5=明確な構造、有機的統合 / 3=構造あるが接続弱い / 1=構造不明瞭
6. precision: 主張が具体的で曖昧さがないか
   5=数値・事例・定義を用いた精密な議論 / 3=概ね具体的 / 1=抽象的

回答フォーマット（JSON のみ、他のテキスト不要）:
{{
  "analytical_depth": {{"score": N, "reason": "..."}},
  "logical_coherence": {{"score": N, "reason": "..."}},
  "novelty": {{"score": N, "reason": "..."}},
  "self_correction": {{"score": N, "reason": "..."}},
  "structural_organization": {{"score": N, "reason": "..."}},
  "precision": {{"score": N, "reason": "..."}}
}}"""

DIMENSIONS = [
    "analytical_depth", "logical_coherence", "novelty",
    "self_correction", "structural_organization", "precision",
]


def find_raw_files() -> list[Path]:
    """Find all raw response files."""
    return sorted(RESULTS_DIR.glob("raw_*.json"))


def _extract_json(text: str) -> dict:
    """Robustly extract JSON from model response with fallbacks."""
    import re

    cleaned = text.strip()
    # Strip markdown code fences
    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        if len(parts) >= 2:
            cleaned = parts[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    # Attempt 1: direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Attempt 2: find first { ... } block
    match = re.search(r'\{[\s\S]*\}', cleaned)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Attempt 3: build scores from regex patterns
    scores = {}
    for dim in DIMENSIONS:
        pat = rf'"{dim}"[^{{]*\{{\s*"score"\s*:\s*(\d+)'
        m = re.search(pat, cleaned)
        if m:
            scores[dim] = {"score": int(m.group(1)), "reason": "(extracted by regex)"}
    if scores:
        return scores

    raise ValueError(f"Could not parse judge response: {cleaned[:200]}")


def judge_response(response_text: str, model: str = JUDGE_MODEL) -> dict:
    """Call the judge model."""
    import anthropic

    client = anthropic.Anthropic()
    user_msg = JUDGE_USER_TEMPLATE.format(response_text=response_text)

    t0 = time.time()
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=0.0,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    elapsed = time.time() - t0

    text = resp.content[0].text.strip()
    scores = _extract_json(text)

    return {
        "scores": scores,
        "judge_model": model,
        "judge_tokens": resp.usage.input_tokens + resp.usage.output_tokens,
        "elapsed": round(elapsed, 2),
    }


def run_judging(dry_run: bool = False, sample: int = 0, judge_model: str = JUDGE_MODEL):
    """Judge all raw files."""
    files = find_raw_files()
    if not files:
        print("No raw response files found in results/")
        return

    if sample > 0:
        import random
        files = random.sample(files, min(sample, len(files)))

    model_tag = judge_model.replace("-", "").replace(".", "")[:12]
    print(f"=== CPS0' Blind Judging (model: {judge_model}) ===")
    print(f"Files to judge: {len(files)}")

    if dry_run:
        for f in files:
            data = json.loads(f.read_text(encoding="utf-8"))
            print(f"  {f.name}: {data['condition']} × {data['task']} #{data['trial']}")
        return

    # Output CSV
    csv_path = RESULTS_DIR / f"judge_scores_{model_tag}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    fieldnames = [
        "file", "condition", "task", "trial", "judge_model",
    ] + [f"{d}_score" for d in DIMENSIONS] + [f"{d}_reason" for d in DIMENSIONS] + [
        "composite_6d", "composite_5d", "judge_tokens", "elapsed",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as csvf:
        writer = csv.DictWriter(csvf, fieldnames=fieldnames)
        writer.writeheader()

        for idx, fpath in enumerate(files):
            data = json.loads(fpath.read_text(encoding="utf-8"))
            cond = data["condition"]
            task = data["task"]
            trial = data["trial"]
            resp_text = data["response"]["response_text"]

            print(f"[{idx+1}/{len(files)}] Judging {fpath.name} ... ", end="", flush=True)

            try:
                result = judge_response(resp_text, model=judge_model)
            except (ValueError, Exception) as e:
                print(f"FAIL ({e})")
                continue

            scores = result["scores"]

            row = {
                "file": fpath.name,
                "condition": cond,
                "task": task,
                "trial": trial,
                "judge_model": judge_model,
            }
            score_values = []
            score_values_5d = []
            for d in DIMENSIONS:
                s = scores.get(d, {})
                sc = s.get("score", 0) if isinstance(s, dict) else 0
                reason = s.get("reason", "") if isinstance(s, dict) else ""
                row[f"{d}_score"] = sc
                row[f"{d}_reason"] = reason
                score_values.append(sc)
                if d != "structural_organization":
                    score_values_5d.append(sc)

            row["composite_6d"] = round(sum(score_values) / 6, 3)
            row["composite_5d"] = round(sum(score_values_5d) / 5, 3)
            row["judge_tokens"] = result["judge_tokens"]
            row["elapsed"] = result["elapsed"]

            writer.writerow(row)
            csvf.flush()

            print(f"OK (6d={row['composite_6d']}, 5d={row['composite_5d']})")
            time.sleep(1.0)

    print(f"\n=== Judging Complete ===")
    print(f"Scores: {csv_path}")


def main():
    parser = argparse.ArgumentParser(description="CPS0' Blind Judge")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sample", type=int, default=0, help="Judge only N random files")
    parser.add_argument("--judge-model", type=str, default=JUDGE_MODEL,
                        help=f"Judge model ID (default: {JUDGE_MODEL})")
    args = parser.parse_args()
    run_judging(args.dry_run, args.sample, args.judge_model)


if __name__ == "__main__":
    main()
