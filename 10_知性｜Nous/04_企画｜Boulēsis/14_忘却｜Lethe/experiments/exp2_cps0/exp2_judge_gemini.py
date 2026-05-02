#!/usr/bin/env python3
"""
exp2_judge_gemini.py — CPS0' Gemini 版盲検評価ランナー (Ochema CortexClient)
==============================================================================

results/ の raw_*.json を読み込み、Gemini judge が6次元評価を実行。
Ochema の CortexClient 経由で複数アカウント round-robin。

Usage:
  python exp2_judge_gemini.py [--dry-run] [--sample 5]

依存: pyyaml (Ochema は同リポジトリ内)

出力: results/judge_scores_gemini_{timestamp}.csv
"""

import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ochema import
_MEKHANE_SRC = Path(__file__).resolve().parents[5] / "20_機構｜Mekhane" / "_src｜ソースコード"
if str(_MEKHANE_SRC) not in sys.path:
    sys.path.insert(0, str(_MEKHANE_SRC))

from mekhane.ochema.cortex_client import CortexClient  # noqa: E402

RESULTS_DIR = Path(__file__).parent / "results"

JUDGE_MODEL = "gemini-2.5-flash"
ACCOUNTS = ["movement", "rairaixoxoxo", "makaron"]

JUDGE_SYSTEM = """あなたは学術的なテキスト品質の厳格な評価者です。
分析出力を受け取り、6つの次元で 1-7 のスコアを付けてください。
この出力がどのような条件で生成されたかは知らされていません。
純粋にテキストの質のみで評価してください。

重要な評価基準:
- 7 は極めて稀です。査読付き学術論文レベルの品質にのみ付与してください。
- 5 を「十分に良い」の基準としてください。
- スコア 6-7 は卓越した品質の出力にのみ付与してください。
- 異なる品質の出力を弁別できるよう、1-7 の全範囲を活用してください。
- 「良い出力」が自動的に高スコアにならないよう注意してください。"""

JUDGE_USER_TEMPLATE = """以下の分析テキストを評価してください。

---
{response_text}
---

以下の6次元で 1-7 のスコアと簡潔な理由（各1文）を JSON で回答してください。
各次元のアンカー定義を厳密に参照し、記述と最も一致するレベルを選んでください。

1. analytical_depth: 分析が表面的でなく、因果メカニズムの深層に到達しているか
   7=3層以上の因果連鎖+層間相互作用を定量的に記述
   6=複数層のメカニズムを特定+層間関係明示、一部暗黙的
   5=2層以上の主要メカニズム特定、層間関係不完全
   4=1つのメカニズムは深いが他層への展開なし
   3=表面的メカニズム同定、因果の方向性曖昧
   2=現象の記述はあるが因果メカニズム不到達
   1=表面的記述のみ

2. logical_coherence: 議論の論理構造が一貫しているか
   7=全主張に明示的根拠+反例処理+完全な論理鎖、暗黙の前提ゼロ
   6=堅固な論理鎖、1-2箇所に暗黙の前提
   5=主要論理鎖は一貫、補助的主張に飛躍あり
   4=概ね一貫、中核議論に1つの暗黙の仮定
   3=大筋は追える、複数箇所で暗黙の仮定や飛躍
   2=主張間の接続が弱く読者の推測が必要
   1=論理構造不明瞭

3. novelty: 独自の洞察があるか
   7=既存フレームワーク統合で新概念/予測を生成+検証可能な仮説
   6=複数の独自視点で既存議論を実質的に拡張
   5=1つの明確に独自な視点が議論の核心に貢献
   4=既知議論の新しい組み合わせ、統合に独自性
   3=一部独自の表現あり、本質的に既知議論の再構成
   2=既知議論の忠実な要約
   1=既知議論のコピー

4. self_correction: 自らの限界を認識し反論を考慮しているか
   7=steel-man反論を構成+再反論を経て結論を修正・統合
   6=強力な反論を構成し結論に統合、再反論が不完全
   5=具体的反論を1つ以上構成し限界として認識
   4=限界への言及あり、反論が具体性に欠ける
   3=「限界がある」程度の一般的言及のみ
   2=適用範囲について曖昧な但し書きのみ
   1=自己批判なし

5. structural_organization: 論理的に構造化されているか
   7=階層的構造+各部分の役割明確+導入→展開→統合が有機的、冗長ゼロ
   6=明確な構造+有機的統合、微小な冗長あり
   5=良好な構造、主要セクション接続は明確、一部接続弱い
   4=基本的構造あり、セクション間の論理的接続不十分
   3=形式的構造はあるが内容的構造化不十分
   2=部分的構造あるが全体の組織化弱い
   1=構造不明瞭

6. precision: 主張が具体的で曖昧さがないか
   7=全主張に数値・事例・定義+定量的比較+誤差範囲の議論
   6=大部分の主張に具体的根拠+主要論点に定量的議論
   5=主要主張に具体的根拠あり、補助的主張に曖昧さ
   4=概ね具体的、重要な主張の一部に裏付け不足
   3=具体的記述と曖昧な記述が混在
   2=抽象的表現多く具体的裏付け少ない
   1=抽象的・曖昧な表現のみ

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


INTER_CALL_DELAY = 20.0
ACCOUNT_COOLDOWN = 180

_CLIENT_POOL: list[tuple[CortexClient, str]] = []
_CLIENT_IDX = 0
_ACCOUNT_COOLDOWNS: dict[str, float] = {}


_ACTIVE_MODEL = JUDGE_MODEL


def _init_client_pool(model: str = JUDGE_MODEL):
    global _CLIENT_POOL, _ACTIVE_MODEL
    _ACTIVE_MODEL = model
    _CLIENT_POOL.clear()
    for acct in ACCOUNTS:
        _CLIENT_POOL.append((
            CortexClient(account=acct, model=model, max_tokens=4096),
            acct,
        ))
    print(f"Ochema: {len(_CLIENT_POOL)} accounts ({', '.join(ACCOUNTS)}), model={model}")


def _recreate_client(account: str):
    global _CLIENT_POOL
    for i, (_, acct) in enumerate(_CLIENT_POOL):
        if acct == account:
            _CLIENT_POOL[i] = (
                CortexClient(account=acct, model=_ACTIVE_MODEL, max_tokens=4096),
                acct,
            )
            print(f"[{acct}:RECREATED] ", end="", flush=True)
            return


def _next_available_client() -> tuple[CortexClient, str]:
    global _CLIENT_IDX
    if not _CLIENT_POOL:
        _init_client_pool(_ACTIVE_MODEL)

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


def find_raw_files() -> list[Path]:
    """Find all raw response files."""
    return sorted(RESULTS_DIR.glob("raw_*.json"))


def _extract_json(text: str) -> dict:
    """Robustly extract JSON from model response with fallbacks."""
    cleaned = text.strip()
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

    # Attempt 3: regex extraction
    scores = {}
    for dim in DIMENSIONS:
        pat = rf'"{dim}"[^{{]*\{{\s*"score"\s*:\s*(\d+)'
        m = re.search(pat, cleaned)
        if m:
            scores[dim] = {"score": int(m.group(1)), "reason": "(extracted by regex)"}
    if scores:
        return scores

    raise ValueError(f"Could not parse judge response: {cleaned[:200]}")


MAX_RETRIES = 5
RETRY_BASE_DELAY = 30.0


def _call_gemini_judge(user_msg: str) -> tuple[str, dict]:
    """Call Gemini judge via Ochema CortexClient (with account failover)."""
    last_err = None
    tried = 0
    max_tries = len(_CLIENT_POOL) * 2

    while tried < max_tries:
        tried += 1
        client, account = _next_available_client()
        try:
            resp = client.ask(
                user_msg,
                system_instruction=JUDGE_SYSTEM,
                temperature=0.0,
            )
            return resp.text, resp.token_usage or {}
        except Exception as e:
            last_err = e
            err_str = str(e)
            if any(kw in err_str for kw in ("429", "403", "CAPACITY", "RESOURCE_EXHAUSTED", "PERMISSION_DENIED")):
                _ACCOUNT_COOLDOWNS[account] = time.time() + ACCOUNT_COOLDOWN
                if "403" in err_str or "PERMISSION_DENIED" in err_str:
                    _recreate_client(account)
                print(f"[{account}:CD{ACCOUNT_COOLDOWN}s] ", end="", flush=True)
                continue
            raise
    raise last_err


def judge_response(response_text: str) -> dict:
    """Call the Gemini judge model with retry."""
    user_msg = JUDGE_USER_TEMPLATE.format(response_text=response_text)

    for attempt in range(MAX_RETRIES):
        try:
            t0 = time.time()
            text, usage = _call_gemini_judge(user_msg)
            elapsed = time.time() - t0

            total_tokens = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
            scores = _extract_json(text)

            return {
                "scores": scores,
                "judge_model": JUDGE_MODEL,
                "judge_tokens": total_tokens,
                "elapsed": round(elapsed, 2),
            }
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"RETRY({attempt+1}, wait {wait:.0f}s) ", end="", flush=True)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("unreachable")


def run_judging(dry_run: bool = False, sample: int = 0, judge_model: str = JUDGE_MODEL):
    """Judge all raw files."""
    files = find_raw_files()
    if not files:
        print("No raw response files found in results/")
        return

    if sample > 0:
        import random
        files = random.sample(files, min(sample, len(files)))

    _init_client_pool(judge_model)
    print(f"=== CPS0' Blind Judging (Gemini: {judge_model}) ===")
    print(f"Files to judge: {len(files)}")

    if dry_run:
        for f in files:
            data = json.loads(f.read_text(encoding="utf-8"))
            print(f"  {f.name}: {data['condition']} × {data['task']} #{data['trial']}")
        return

    tag = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    csv_path = RESULTS_DIR / f"judge_scores_gemini_{tag}.csv"
    fieldnames = [
        "file", "condition", "task", "trial", "judge_model",
    ] + [f"{d}_score" for d in DIMENSIONS] + [f"{d}_reason" for d in DIMENSIONS] + [
        "composite_6d", "composite_5d", "composite_3d", "judge_tokens", "elapsed",
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
                result = judge_response(resp_text)
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
            score_values_3d = []
            discrim_dims = {"novelty", "self_correction", "precision"}
            for d in DIMENSIONS:
                s = scores.get(d, {})
                sc = s.get("score", 0) if isinstance(s, dict) else 0
                reason = s.get("reason", "") if isinstance(s, dict) else ""
                row[f"{d}_score"] = sc
                row[f"{d}_reason"] = reason
                score_values.append(sc)
                if d != "structural_organization":
                    score_values_5d.append(sc)
                if d in discrim_dims:
                    score_values_3d.append(sc)

            row["composite_6d"] = round(sum(score_values) / 6, 3)
            row["composite_5d"] = round(sum(score_values_5d) / 5, 3)
            row["composite_3d"] = round(sum(score_values_3d) / 3, 3)
            row["judge_tokens"] = result["judge_tokens"]
            row["elapsed"] = result["elapsed"]

            writer.writerow(row)
            csvf.flush()

            print(f"OK (6d={row['composite_6d']}, 5d={row['composite_5d']}, 3d={row['composite_3d']})")
            time.sleep(INTER_CALL_DELAY)

    print(f"\n=== Judging Complete ===")
    print(f"Scores: {csv_path}")


def main():
    parser = argparse.ArgumentParser(description="CPS0' Blind Judge (Gemini)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sample", type=int, default=0, help="Judge only N random files")
    parser.add_argument("--judge-model", type=str, default=JUDGE_MODEL)
    args = parser.parse_args()
    run_judging(args.dry_run, args.sample, args.judge_model)


if __name__ == "__main__":
    main()
