#!/usr/bin/env python3
"""
exp2_runner.py — CPS0' 制御実験 パイロットランナー
==================================================

Phase 1 パイロット: Sonnet × T1+T2 × 4条件 × N=10/cell = 80 trials
Usage:
  python exp2_runner.py --phase pilot [--dry-run]
  python exp2_runner.py --phase full  [--dry-run]

依存: pip install anthropic pyyaml

出力:
  results/raw_{condition}_{task}_{trial:03d}.json
  results/manifest.csv
"""

import argparse
import json
import os
import sys
import time
import random
import csv
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml required. pip install pyyaml")
    sys.exit(1)

# --- Config ---
BASE_DIR = Path(__file__).parent
STIMULI_DIR = BASE_DIR / "stimuli"
RESULTS_DIR = BASE_DIR / "results"

MODELS = {
    "primary": "claude-sonnet-4-6-20250514",
    "judge": "claude-opus-4-6-20250514",
}

PHASE_CONFIG = {
    "pilot": {
        "tasks": ["T1", "T2"],
        "n_per_cell": 10,
        "models": ["primary"],
    },
    "full": {
        "tasks": ["T1", "T2", "T3", "T4", "T5"],
        "n_per_cell": 15,
        "models": ["primary"],
    },
}

CONDITIONS = ["A_HiStr_HiCon", "B_HiStr_LoCon", "C_LoStr_HiCon", "D_LoStr_LoCon"]

TEMPERATURE = 0.7
MAX_TOKENS = 4096


def load_stimulus(condition: str, task: str) -> dict:
    """Load a stimulus file and extract system/user prompts."""
    path = STIMULI_DIR / f"{condition}_{task}.md"
    text = path.read_text(encoding="utf-8")

    # Parse YAML frontmatter
    parts = text.split("---", 2)
    meta = yaml.safe_load(parts[1]) if len(parts) >= 3 else {}

    # Extract prompts
    body = parts[2] if len(parts) >= 3 else text
    sys_start = body.find("## System Prompt")
    user_start = body.find("## User Prompt")

    system_prompt = body[sys_start + len("## System Prompt"):user_start].strip()
    user_prompt = body[user_start + len("## User Prompt"):].strip()

    return {
        "meta": meta,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
    }


def call_model(system_prompt: str, user_prompt: str, model_key: str = "primary") -> dict:
    """Call the Anthropic API."""
    import anthropic

    client = anthropic.Anthropic()
    model_id = MODELS[model_key]

    t0 = time.time()
    response = client.messages.create(
        model=model_id,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    elapsed = time.time() - t0

    return {
        "model": model_id,
        "response_text": response.content[0].text,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "stop_reason": response.stop_reason,
        "elapsed_seconds": round(elapsed, 2),
    }


def build_trial_list(phase: str, seed: int | None = None) -> list[dict]:
    """Build randomized list of trials."""
    cfg = PHASE_CONFIG[phase]
    trials = []
    for condition in CONDITIONS:
        for task in cfg["tasks"]:
            for i in range(cfg["n_per_cell"]):
                trials.append({
                    "condition": condition,
                    "task": task,
                    "trial": i,
                })
    rng = random.Random(seed)
    rng.shuffle(trials)
    return trials


MAX_RETRIES = 3
RETRY_BASE_DELAY = 5.0


def call_model_with_retry(system_prompt: str, user_prompt: str, model_key: str = "primary") -> dict:
    """Call API with exponential backoff retry."""
    for attempt in range(MAX_RETRIES):
        try:
            return call_model(system_prompt, user_prompt, model_key)
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = RETRY_BASE_DELAY * (2 ** attempt)
            print(f"RETRY ({attempt + 1}/{MAX_RETRIES}, wait {wait:.0f}s: {e}) ", end="", flush=True)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def run_experiment(phase: str, dry_run: bool = False, seed: int | None = None):
    """Execute the experiment."""
    RESULTS_DIR.mkdir(exist_ok=True)
    trials = build_trial_list(phase, seed=seed)
    total = len(trials)

    print(f"=== CPS0' Experiment Phase: {phase} ===")
    print(f"Total trials: {total}")
    print(f"Conditions: {CONDITIONS}")
    print(f"Tasks: {PHASE_CONFIG[phase]['tasks']}")
    print(f"N/cell: {PHASE_CONFIG[phase]['n_per_cell']}")
    if seed is not None:
        print(f"Seed: {seed}")
    print()

    if dry_run:
        print("[DRY RUN] Trial list:")
        for i, t in enumerate(trials):
            print(f"  {i+1:3d}. {t['condition']} × {t['task']} #{t['trial']}")
        print(f"\n[DRY RUN] {total} trials would be executed.")
        return

    manifest_path = RESULTS_DIR / f"manifest_{phase}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(manifest_file, fieldnames=[
            "trial_idx", "condition", "task", "trial_num",
            "input_tokens", "output_tokens", "elapsed_seconds",
            "output_file", "timestamp",
        ])
        writer.writeheader()

        errors = []
        for idx, t in enumerate(trials):
            cond, task, trial_num = t["condition"], t["task"], t["trial"]
            print(f"[{idx+1}/{total}] {cond} × {task} #{trial_num} ... ", end="", flush=True)

            try:
                stimulus = load_stimulus(cond, task)
                result = call_model_with_retry(stimulus["system_prompt"], stimulus["user_prompt"])
            except Exception as e:
                print(f"FAIL ({e})")
                errors.append({"idx": idx, "condition": cond, "task": task, "trial": trial_num, "error": str(e)})
                continue

            # Save raw response
            output_file = f"raw_{cond}_{task}_{trial_num:03d}.json"
            output_path = RESULTS_DIR / output_file
            record = {
                "experiment": "exp2_cps0",
                "phase": phase,
                "condition": cond,
                "task": task,
                "trial": trial_num,
                "stimulus": {
                    "system_prompt": stimulus["system_prompt"],
                    "user_prompt": stimulus["user_prompt"],
                },
                "response": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

            writer.writerow({
                "trial_idx": idx,
                "condition": cond,
                "task": task,
                "trial_num": trial_num,
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "elapsed_seconds": result["elapsed_seconds"],
                "output_file": output_file,
                "timestamp": record["timestamp"],
            })
            manifest_file.flush()

            print(f"OK ({result['output_tokens']} tokens, {result['elapsed_seconds']}s)")
            time.sleep(0.5)

    print(f"\n=== Complete: {total - len(errors)}/{total} trials ===")
    print(f"Manifest: {manifest_path}")
    if errors:
        print(f"\n⚠️ {len(errors)} errors:")
        for e in errors:
            print(f"  {e['condition']} × {e['task']} #{e['trial']}: {e['error']}")


def main():
    parser = argparse.ArgumentParser(description="CPS0' Experiment Runner")
    parser.add_argument("--phase", choices=["pilot", "full"], default="pilot")
    parser.add_argument("--dry-run", action="store_true", help="List trials without calling API")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    args = parser.parse_args()

    run_experiment(args.phase, args.dry_run, seed=args.seed)


if __name__ == "__main__":
    main()
