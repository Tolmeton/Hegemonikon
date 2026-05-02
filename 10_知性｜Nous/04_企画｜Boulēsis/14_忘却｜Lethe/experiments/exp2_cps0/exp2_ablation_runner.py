#!/usr/bin/env python3
"""
exp2_ablation_runner.py — CPS0' Phase4 ablation + cross-model replication
=========================================================================

Q1-Q4 verification experiments using gemini-3.1-flash-lite-preview:
  - E condition (HiStr_noP4_LoCon): Phase 1-3 + convergence, no Phase 4 反駁
  - B' replication: B condition on flash-lite (cross-model)
  - C' replication: C condition on flash-lite (cross-model)

Usage:
  python exp2_ablation_runner.py --phase ablation --seed 42        # E only (N=30×5 = 150)
  python exp2_ablation_runner.py --phase crossmodel --seed 42      # B'+C' (N=30×5×2 = 300)
  python exp2_ablation_runner.py --phase all --seed 42             # E+B'+C' (450 total)
  python exp2_ablation_runner.py --phase all --dry-run
"""

import argparse
import csv
import json
import random
import sys
import time
import yaml
from datetime import datetime, timezone
from pathlib import Path

_MEKHANE_SRC = Path(__file__).resolve().parents[5] / "20_機構｜Mekhane" / "_src｜ソースコード"
if str(_MEKHANE_SRC) not in sys.path:
    sys.path.insert(0, str(_MEKHANE_SRC))

from mekhane.ochema.cortex_client import CortexClient  # noqa: E402

BASE_DIR = Path(__file__).parent
STIMULI_DIR = BASE_DIR / "stimuli"
RESULTS_DIR = BASE_DIR / "results"

MODEL = "gemini-3.1-flash-lite-preview"
ACCOUNTS = ["movement", "rairaixoxoxo", "makaron"]

TASKS = ["T1", "T2", "T3", "T4", "T5"]
N_PER_CELL = 30

ABLATION_CONDITIONS = ["E_HiStr_noP4_LoCon"]
CROSSMODEL_CONDITIONS = ["B_HiStr_LoCon", "C_LoStr_HiCon"]

TEMPERATURE = 0.7
MAX_OUTPUT_TOKENS = 16384
THINKING_BUDGET = 8192
INTER_CALL_DELAY = 20.0
ACCOUNT_COOLDOWN = 180
MAX_RETRIES = 5
RETRY_BASE_DELAY = 30.0

_CLIENT_POOL: list[tuple[CortexClient, str]] = []
_CLIENT_IDX = 0
_ACCOUNT_COOLDOWNS: dict[str, float] = {}


def _init_client_pool():
    global _CLIENT_POOL
    _CLIENT_POOL.clear()
    for acct in ACCOUNTS:
        _CLIENT_POOL.append((
            CortexClient(account=acct, model=MODEL, max_tokens=MAX_OUTPUT_TOKENS),
            acct,
        ))
    print(f"Ochema: {len(_CLIENT_POOL)} accounts ({', '.join(ACCOUNTS)}), model={MODEL}")


def _recreate_client(account: str):
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
    global _CLIENT_IDX
    if not _CLIENT_POOL:
        _init_client_pool()

    now = time.time()
    for _ in range(len(_CLIENT_POOL)):
        _CLIENT_IDX = (_CLIENT_IDX + 1) % len(_CLIENT_POOL)
        client, acct = _CLIENT_POOL[_CLIENT_IDX]
        cooldown_until = _ACCOUNT_COOLDOWNS.get(acct, 0)
        if now >= cooldown_until:
            return client, acct

    soonest_acct = min(_ACCOUNT_COOLDOWNS, key=_ACCOUNT_COOLDOWNS.get)
    wait_time = _ACCOUNT_COOLDOWNS[soonest_acct] - now
    if wait_time > 0:
        print(f"[ALL-COOLDOWN] waiting {wait_time:.0f}s for {soonest_acct}... ", end="", flush=True)
        time.sleep(wait_time + 1)
    del _ACCOUNT_COOLDOWNS[soonest_acct]
    for client, acct in _CLIENT_POOL:
        if acct == soonest_acct:
            return client, acct
    raise RuntimeError("unreachable")


def load_stimulus(condition: str, task: str) -> dict:
    path = STIMULI_DIR / f"{condition}_{task}.md"
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    meta = yaml.safe_load(parts[1]) if len(parts) >= 3 else {}
    body = parts[2] if len(parts) >= 3 else text
    sys_start = body.find("## System Prompt")
    user_start = body.find("## User Prompt")
    system_prompt = body[sys_start + len("## System Prompt"):user_start].strip()
    user_prompt = body[user_start + len("## User Prompt"):].strip()
    return {"meta": meta, "system_prompt": system_prompt, "user_prompt": user_prompt}


def call_model(system_prompt: str, user_prompt: str) -> dict:
    last_err = None
    tried = 0
    max_tries = len(_CLIENT_POOL) * 2

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
            return {
                "response_text": resp.text,
                "model": resp.model or MODEL,
                "input_tokens": getattr(resp, 'input_tokens', 0),
                "output_tokens": getattr(resp, 'output_tokens', 0),
                "thinking_tokens": getattr(resp, 'thinking_tokens', 0),
                "elapsed": round(elapsed, 2),
            }
        except Exception as e:
            err_str = str(e)
            last_err = e
            if "403" in err_str or "PERMISSION_DENIED" in err_str:
                _ACCOUNT_COOLDOWNS[account] = time.time() + ACCOUNT_COOLDOWN
                _recreate_client(account)
                print(f"[{account}:403-COOLDOWN {ACCOUNT_COOLDOWN}s] ", end="", flush=True)
                continue
            elif "429" in err_str or "RATE_LIMIT" in err_str:
                _ACCOUNT_COOLDOWNS[account] = time.time() + 60
                print(f"[{account}:429-COOLDOWN 60s] ", end="", flush=True)
                continue
            raise

    raise RuntimeError(f"All accounts exhausted after {tried} attempts: {last_err}")


def call_model_with_retry(system_prompt: str, user_prompt: str) -> dict:
    for attempt in range(MAX_RETRIES):
        try:
            return call_model(system_prompt, user_prompt)
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = RETRY_BASE_DELAY * (2 ** attempt)
            print(f"RETRY ({attempt + 1}/{MAX_RETRIES}, wait {wait:.0f}s: {e}) ", end="", flush=True)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def build_trial_list(conditions: list[str], seed: int | None = None) -> list[dict]:
    trials = []
    for cond in conditions:
        for task in TASKS:
            for trial in range(N_PER_CELL):
                trials.append({"condition": cond, "task": task, "trial": trial})
    if seed is not None:
        random.seed(seed)
        random.shuffle(trials)
    return trials


def run(phase: str, dry_run: bool = False, seed: int | None = None):
    RESULTS_DIR.mkdir(exist_ok=True)

    if phase == "ablation":
        conditions = ABLATION_CONDITIONS
    elif phase == "crossmodel":
        conditions = CROSSMODEL_CONDITIONS
    elif phase == "all":
        conditions = ABLATION_CONDITIONS + CROSSMODEL_CONDITIONS
    else:
        raise ValueError(f"Unknown phase: {phase}")

    trials = build_trial_list(conditions, seed=seed)
    total = len(trials)

    print(f"=== CPS0' Ablation/CrossModel (Gemini: {MODEL}) ===")
    print(f"Phase: {phase}")
    print(f"Total trials: {total}")
    print(f"Conditions: {conditions}")
    print(f"N/cell: {N_PER_CELL}")
    if seed is not None:
        print(f"Seed: {seed}")
    print()

    if dry_run:
        for i, t in enumerate(trials):
            print(f"  {i+1:3d}. {t['condition']} × {t['task']} #{t['trial']}")
        print(f"\n[DRY RUN] {total} trials")
        return

    _init_client_pool()

    tag = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    manifest_path = RESULTS_DIR / f"manifest_ablation_{tag}.csv"

    with open(manifest_path, "w", newline="", encoding="utf-8") as mf:
        writer = csv.DictWriter(mf, fieldnames=[
            "trial_idx", "condition", "task", "trial_num",
            "input_tokens", "output_tokens", "thinking_tokens",
            "elapsed_seconds", "output_file", "timestamp",
        ])
        writer.writeheader()

        errors = []
        for idx, t in enumerate(trials):
            cond, task, trial_num = t["condition"], t["task"], t["trial"]
            # Cross-model B'/C' get a model suffix to avoid overwriting originals
            if cond in CROSSMODEL_CONDITIONS:
                output_file = f"raw_{cond}_{task}_{trial_num:03d}_flashlite.json"
            else:
                output_file = f"raw_{cond}_{task}_{trial_num:03d}.json"
            output_path = RESULTS_DIR / output_file

            print(f"[{idx+1}/{total}] {cond} × {task} #{trial_num} ... ", end="", flush=True)

            if output_path.exists():
                print(f"SKIP (exists)")
                continue

            try:
                stimulus = load_stimulus(cond, task)
                result = call_model_with_retry(stimulus["system_prompt"], stimulus["user_prompt"])
            except Exception as e:
                print(f"FAIL ({e})")
                errors.append({"idx": idx, "condition": cond, "task": task, "trial": trial_num, "error": str(e)})
                if len(errors) > 10 and len(errors) / max(1, idx + 1) > 0.5:
                    print(f"\n🔴 RETREAT: {len(errors)} failures. Halting.")
                    break
                continue

            record = {
                "experiment": "exp2_cps0_ablation",
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
                "model": MODEL,
            }
            output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

            writer.writerow({
                "trial_idx": idx,
                "condition": cond,
                "task": task,
                "trial_num": trial_num,
                "input_tokens": result.get("input_tokens", 0),
                "output_tokens": result.get("output_tokens", 0),
                "thinking_tokens": result.get("thinking_tokens", 0),
                "elapsed_seconds": result.get("elapsed", 0),
                "output_file": output_file,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            mf.flush()

            in_tok = result.get("input_tokens", 0)
            out_tok = result.get("output_tokens", 0)
            print(f"OK ({in_tok}+{out_tok}tok, {result.get('elapsed', 0):.1f}s)")
            time.sleep(INTER_CALL_DELAY)

    print(f"\n=== Complete: {total - len(errors)}/{total} trials ===")
    if errors:
        print(f"Errors: {len(errors)}")
    print(f"Manifest: {manifest_path}")


def main():
    parser = argparse.ArgumentParser(description="CPS0' Ablation + CrossModel Runner")
    parser.add_argument("--phase", choices=["ablation", "crossmodel", "all"], required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run(args.phase, args.dry_run, args.seed)


if __name__ == "__main__":
    main()
