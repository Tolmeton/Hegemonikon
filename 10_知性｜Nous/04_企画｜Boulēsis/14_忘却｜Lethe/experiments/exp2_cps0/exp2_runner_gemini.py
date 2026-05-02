#!/usr/bin/env python3
"""
exp2_runner_gemini.py — CPS0' Gemini 版ランナー (Ochema CortexClient)
======================================================================

Ochema の CortexClient (Cortex API) を使って Gemini で実験を実行する。
複数 Google アカウントを round-robin で利用し rate limit を分散。

Usage:
  python exp2_runner_gemini.py --phase mvp --seed 42
  python exp2_runner_gemini.py --phase pilot --seed 42
  python exp2_runner_gemini.py --phase full --seed 42
  python exp2_runner_gemini.py --phase full --dry-run

依存: pip install pyyaml (Ochema は同リポジトリ内)

出力:
  results/raw_{condition}_{task}_{trial:03d}.json
  results/manifest_{phase}_{timestamp}.csv
"""

import argparse
import csv
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml required. pip install pyyaml")
    sys.exit(1)

# Ochema import
_MEKHANE_SRC = Path(__file__).resolve().parents[5] / "20_機構｜Mekhane" / "_src｜ソースコード"
if str(_MEKHANE_SRC) not in sys.path:
    sys.path.insert(0, str(_MEKHANE_SRC))

from mekhane.ochema.cortex_client import CortexClient  # noqa: E402

# --- Config ---
BASE_DIR = Path(__file__).parent
STIMULI_DIR = BASE_DIR / "stimuli"
RESULTS_DIR = BASE_DIR / "results"

MODEL = "gemini-2.5-flash"
ACCOUNTS = ["movement", "rairaixoxoxo", "makaron"]

PHASE_CONFIG = {
    "mvp": {
        "tasks": ["T1", "T2"],
        "n_per_cell": 2,
    },
    "pilot": {
        "tasks": ["T1", "T2"],
        "n_per_cell": 10,
    },
    "full": {
        "tasks": ["T1", "T2", "T3", "T4", "T5"],
        "n_per_cell": 30,
    },
}

CONDITIONS = ["A_HiStr_HiCon", "B_HiStr_LoCon", "C_LoStr_HiCon", "D_LoStr_LoCon"]

TEMPERATURE = 0.7
MAX_OUTPUT_TOKENS = 16384
THINKING_BUDGET = 8192
INTER_CALL_DELAY = 20.0  # seconds between API calls (prevents rate limiting)
ACCOUNT_COOLDOWN = 180  # seconds to cool down a failed account

# Round-robin client pool with per-account cooldown
_CLIENT_POOL: list[tuple[CortexClient, str]] = []  # (client, account_name)
_CLIENT_IDX = 0
_ACCOUNT_COOLDOWNS: dict[str, float] = {}  # account -> cooldown_until timestamp


def _init_client_pool():
    """Create CortexClient instances for each account."""
    global _CLIENT_POOL
    _CLIENT_POOL.clear()
    for acct in ACCOUNTS:
        _CLIENT_POOL.append((
            CortexClient(account=acct, model=MODEL, max_tokens=MAX_OUTPUT_TOKENS),
            acct,
        ))
    print(f"Ochema: {len(_CLIENT_POOL)} accounts ({', '.join(ACCOUNTS)})")


def _recreate_client(account: str):
    """Recreate CortexClient for an account (fresh project assignment)."""
    global _CLIENT_POOL
    for i, (_, acct) in enumerate(_CLIENT_POOL):
        if acct == account:
            _CLIENT_POOL[i] = (
                CortexClient(account=acct, model=MODEL, max_tokens=MAX_OUTPUT_TOKENS),
                acct,
            )
            print(f"[{acct}:RECREATED] ", end="", flush=True)
            return


def _next_available_client() -> tuple[CortexClient, str]:
    """Return next available client, respecting per-account cooldowns."""
    global _CLIENT_IDX
    if not _CLIENT_POOL:
        _init_client_pool()

    now = time.time()
    # Try each account once in round-robin
    for _ in range(len(_CLIENT_POOL)):
        _CLIENT_IDX = (_CLIENT_IDX + 1) % len(_CLIENT_POOL)
        client, acct = _CLIENT_POOL[_CLIENT_IDX]
        cooldown_until = _ACCOUNT_COOLDOWNS.get(acct, 0)
        if now >= cooldown_until:
            return client, acct

    # All accounts on cooldown — wait for the soonest one
    soonest_acct = min(_ACCOUNT_COOLDOWNS, key=_ACCOUNT_COOLDOWNS.get)
    wait_time = _ACCOUNT_COOLDOWNS[soonest_acct] - now
    if wait_time > 0:
        print(f"[ALL-COOLDOWN] waiting {wait_time:.0f}s for {soonest_acct}... ", end="", flush=True)
        time.sleep(wait_time + 1)
    # Clear it and return
    del _ACCOUNT_COOLDOWNS[soonest_acct]
    for client, acct in _CLIENT_POOL:
        if acct == soonest_acct:
            return client, acct
    raise RuntimeError("unreachable")


def load_stimulus(condition: str, task: str) -> dict:
    """Load a stimulus file and extract system/user prompts."""
    path = STIMULI_DIR / f"{condition}_{task}.md"
    text = path.read_text(encoding="utf-8")

    parts = text.split("---", 2)
    meta = yaml.safe_load(parts[1]) if len(parts) >= 3 else {}

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


def call_gemini(system_prompt: str, user_prompt: str) -> dict:
    """Call Gemini via Ochema CortexClient with account failover.

    Handles both 429 rate limits and 403 permission errors by rotating accounts.
    """
    last_err = None
    tried = 0
    max_tries = len(_CLIENT_POOL) * 2  # allow retries after cooldown waits

    while tried < max_tries:
        tried += 1
        client, account = _next_available_client()
        try:
            t0 = time.time()
            resp = client.ask(
                user_prompt,
                system_instruction=system_prompt,
                temperature=TEMPERATURE,
                thinking_budget=THINKING_BUDGET,
            )
            elapsed = time.time() - t0

            usage = resp.token_usage or {}
            return {
                "model": resp.model or MODEL,
                "account": account,
                "response_text": resp.text,
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
                "thinking_tokens": usage.get("thoughts_tokens", 0),
                "stop_reason": resp.stop_reason or "STOP",
                "elapsed_seconds": round(elapsed, 2),
            }
        except Exception as e:
            last_err = e
            err_str = str(e)
            # Treat 429, 403, capacity errors as "account temporarily bad"
            if any(kw in err_str for kw in ("429", "403", "CAPACITY", "RESOURCE_EXHAUSTED", "PERMISSION_DENIED")):
                _ACCOUNT_COOLDOWNS[account] = time.time() + ACCOUNT_COOLDOWN
                # Recreate client on 403 to get fresh project assignment
                if "403" in err_str or "PERMISSION_DENIED" in err_str:
                    _recreate_client(account)
                print(f"[{account}:CD{ACCOUNT_COOLDOWN}s] ", end="", flush=True)
                continue
            raise  # truly unexpected error
    raise last_err  # all attempts exhausted


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


MAX_RETRIES = 5
RETRY_BASE_DELAY = 30.0


def call_model_with_retry(system_prompt: str, user_prompt: str) -> dict:
    """Call API with exponential backoff retry (CortexClient has internal retry too)."""
    for attempt in range(MAX_RETRIES):
        try:
            return call_gemini(system_prompt, user_prompt)
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

    model_name = MODEL
    _init_client_pool()
    print(f"=== CPS0' Experiment Phase: {phase} (Gemini: {model_name}) ===")
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
            "input_tokens", "output_tokens", "thinking_tokens", "elapsed_seconds",
            "output_file", "timestamp",
        ])
        writer.writeheader()

        errors = []
        for idx, t in enumerate(trials):
            cond, task, trial_num = t["condition"], t["task"], t["trial"]
            print(f"[{idx+1}/{total}] {cond} × {task} #{trial_num} ... ", end="", flush=True)

            try:
                stimulus = load_stimulus(cond, task)

                # Skip if output file already exists (resume support)
                output_file = f"raw_{cond}_{task}_{trial_num:03d}.json"
                output_path = RESULTS_DIR / output_file
                if output_path.exists():
                    print(f"SKIP (exists: {output_file})")
                    continue

                result = call_model_with_retry(stimulus["system_prompt"], stimulus["user_prompt"])
            except Exception as e:
                print(f"FAIL ({e})")
                errors.append({"idx": idx, "condition": cond, "task": task, "trial": trial_num, "error": str(e)})
                # Retreat condition: >80% errors in first 10 non-skip trials
                non_skip_count = sum(1 for j in range(idx + 1)
                                     if not (RESULTS_DIR / f"raw_{trials[j]['condition']}_{trials[j]['task']}_{trials[j]['trial']:03d}.json").exists())
                if non_skip_count <= 10 and len(errors) > non_skip_count * 0.8:
                    print(f"\n🔴 RETREAT: {len(errors)}/{non_skip_count} failures in first 10 trials. Halting.")
                    break
                continue

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
                "backend": "gemini",
            }
            output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

            writer.writerow({
                "trial_idx": idx,
                "condition": cond,
                "task": task,
                "trial_num": trial_num,
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "thinking_tokens": result["thinking_tokens"],
                "elapsed_seconds": result["elapsed_seconds"],
                "output_file": output_file,
                "timestamp": record["timestamp"],
            })
            manifest_file.flush()

            print(f"OK ({result['output_tokens']}+{result['thinking_tokens']}t, {result['elapsed_seconds']}s, @{result.get('account','-')})")
            time.sleep(INTER_CALL_DELAY)

    print(f"\n=== Complete: {total - len(errors)}/{total} trials ===")
    print(f"Manifest: {manifest_path}")
    if errors:
        print(f"\n⚠️ {len(errors)} errors:")
        for e in errors:
            print(f"  {e['condition']} × {e['task']} #{e['trial']}: {e['error']}")


def main():
    parser = argparse.ArgumentParser(description="CPS0' Experiment Runner (Gemini)")
    parser.add_argument("--phase", choices=["mvp", "pilot", "full"], default="mvp")
    parser.add_argument("--dry-run", action="store_true", help="List trials without calling API")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    args = parser.parse_args()

    run_experiment(args.phase, args.dry_run, seed=args.seed)


if __name__ == "__main__":
    main()
