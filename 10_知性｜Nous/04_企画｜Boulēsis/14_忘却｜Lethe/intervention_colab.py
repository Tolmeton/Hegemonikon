"""
介入実験: 選択的忘却定理 v3 の検証 — Colab スタンドアロン版

v3 核心予測: |∇_t Θ| > 0 → P > P(∇_t Θ = 0)

Colab 使い方:
  1. !pip install datasets google-generativeai scipy
  2. from google.colab import userdata; API_KEY = userdata.get('GEMINI_API_KEY')
     または直接 API_KEY = "..." を設定
  3. このファイル全体を1セルに貼り付けて実行
  4. run_experiment(api_key=API_KEY, n_per_strategy=5, budget=0.5) でパイロット
  5. run_experiment(api_key=API_KEY, n_per_strategy=150, budget=0.5) で本番
"""

import json
import time
import numpy as np
from dataclasses import dataclass
from typing import Optional

# ============================================================
# §1 データ構造
# ============================================================
@dataclass
class TrajectoryEntry:
    role: str       # user (observation) / ai (action)
    text: str
    turn_idx: int
    char_len: int

# ============================================================
# §2 trajectory パーサー
# ============================================================
def _extract_text(entry: dict) -> str:
    """エントリからテキストを抽出"""
    text = entry.get("text", "") or entry.get("content", "") or ""
    if isinstance(text, list):
        text = " ".join(
            item.get("text", str(item)) if isinstance(item, dict) else str(item)
            for item in text
        )
    return str(text) if text else ""


def parse_trajectory(raw_traj: list):
    """trajectory → (system_prompt, issue_text, turns)"""
    system_prompt = ""
    issue_text = ""
    turns = []
    found_first_user = False

    for entry in raw_traj:
        if not isinstance(entry, dict):
            continue
        role = entry.get("role", "")
        text = _extract_text(entry)

        if role == "system":
            system_prompt = text
        elif role == "user" and not found_first_user:
            issue_text = text
            found_first_user = True
        elif role in ("user", "tool", "ai", "assistant"):
            normalized = "ai" if role in ("ai", "assistant") else "user"
            turns.append(TrajectoryEntry(
                role=normalized, text=text,
                turn_idx=len(turns), char_len=len(text)
            ))
    return system_prompt, issue_text, turns

# ============================================================
# §3 忘却戦略 (総予算固定、配分のみ変更)
# ============================================================
def strategy_U(turns, budget):
    """均等: 各 turn を一律 budget 比率で截断。∇_t Θ = 0"""
    masked = []
    for t in turns:
        keep = max(1, int(t.char_len * budget))
        txt = t.text[:keep] + ("... [truncated]" if keep < t.char_len else "")
        masked.append({"role": t.role, "text": txt,
                       "original_len": t.char_len, "masked_len": len(txt)})
    return masked


def strategy_G(turns, budget):
    """勾配: 新しい turn ほど多く保持。∇_t Θ = 一定正"""
    n = len(turns)
    if n == 0:
        return []
    weights = np.linspace(0.2, 1.8, n)
    total_chars = sum(t.char_len for t in turns)
    target = int(total_chars * budget)
    raw = np.array([w * t.char_len for w, t in zip(weights, turns)])
    alloc = (raw / raw.sum() * target).astype(int) if raw.sum() > 0 else np.ones(n, dtype=int)
    alloc = np.clip(alloc, 1, [t.char_len for t in turns])

    masked = []
    for t, keep in zip(turns, alloc):
        txt = t.text[:keep] + ("... [truncated]" if keep < t.char_len else "")
        masked.append({"role": t.role, "text": txt,
                       "original_len": t.char_len, "masked_len": len(txt)})
    return masked


def strategy_S(turns, budget):
    """二値: turn の budget 割合を完全保持、残りを完全除去。∇_t Θ = δ関数"""
    n = len(turns)
    if n == 0:
        return []
    n_keep = max(1, int(n * budget))
    keep_idx = set(np.linspace(0, n - 1, n_keep, dtype=int).tolist())

    masked = []
    for i, t in enumerate(turns):
        if i in keep_idx:
            masked.append({"role": t.role, "text": t.text,
                           "original_len": t.char_len, "masked_len": t.char_len})
        else:
            ph = f"[Turn {i}: {t.role}, {t.char_len} chars removed]"
            masked.append({"role": t.role, "text": ph,
                           "original_len": t.char_len, "masked_len": len(ph)})
    return masked


STRATEGIES = {"U": strategy_U, "G": strategy_G, "S": strategy_S}

# ============================================================
# §4 プロンプト構築
# ============================================================
def build_prompt(issue_text, masked_turns):
    history = "\n\n---\n\n".join(
        f"[{'Agent' if m['role']=='ai' else 'Environment'}]\n{m['text']}"
        for m in masked_turns
    )
    return f"""You are a software bug-fixing expert.
Read the GitHub issue and debugging log below, then generate the final fix as a unified diff patch.

## Issue
{issue_text[:3000]}

## Debugging Log
{history}

## Task
Generate a unified diff patch that fixes this issue.
Include file paths. Output ONLY the diff, no explanation.
"""

# ============================================================
# §5 P (パッチ一致度)
# ============================================================
def compute_P(generated: str, gold: str) -> dict:
    def extract_files(t):
        files = set()
        for line in t.split("\n"):
            for pfx in ("--- a/", "+++ b/", "--- ", "+++ "):
                if line.startswith(pfx):
                    p = line[len(pfx):].strip()
                    if p and p != "/dev/null":
                        files.add(p.lstrip("ab/"))
        return files
    def extract_lines(t):
        lines = set()
        for line in t.split("\n"):
            s = line.strip()
            if s.startswith("+") and not s.startswith("+++"):
                lines.add(s[1:].strip())
            elif s.startswith("-") and not s.startswith("---"):
                lines.add(s[1:].strip())
        return lines

    gf, genf = extract_files(gold), extract_files(generated)
    gl, genl = extract_lines(gold), extract_lines(generated)
    file_match = bool(gf & genf) if gf else False
    if gl and genl:
        line_overlap = len(gl & genl) / len(gl | genl)
    else:
        line_overlap = 0.0
    return {"file_match": file_match, "line_overlap": line_overlap,
            "exact_match": generated.strip() == gold.strip(),
            "n_gold_files": len(gf), "n_gen_files": len(genf),
            "n_gold_lines": len(gl), "n_gen_lines": len(genl)}

# ============================================================
# §6 ∇_t Θ
# ============================================================
def compute_grad(theta_list):
    if len(theta_list) < 2:
        return {"mean_abs_grad": 0.0, "std_grad": 0.0, "max_abs_grad": 0.0,
                "mean_theta": 0.0, "std_theta": 0.0}
    a = np.array(theta_list)
    g = np.diff(a)
    return {"mean_abs_grad": float(np.mean(np.abs(g))),
            "std_grad": float(np.std(g)),
            "max_abs_grad": float(np.max(np.abs(g))),
            "mean_theta": float(np.mean(a)),
            "std_theta": float(np.std(a))}

# ============================================================
# §7 Gemini API 呼出 (ラウンドロビン)
# ============================================================
def setup_gemini(api_key: str):
    """Gemini API のセットアップ"""
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash-preview-05-20")


def call_gemini(model, prompt: str, max_retries: int = 3) -> str:
    """Gemini を呼出してパッチを生成。レート制限リトライ付き。"""
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config={"max_output_tokens": 4096, "temperature": 0.2}
            )
            return response.text
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower() or "rate" in err.lower():
                wait = 10 * (attempt + 1)
                print(f"  ⏳ Rate limit hit, waiting {wait}s... (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                print(f"  ❌ API error: {err}")
                return f"[ERROR: {err}]"
    return "[ERROR: max retries exceeded]"

# ============================================================
# §8 統計分析
# ============================================================
def analyze(results):
    from scipy import stats
    if not results:
        print("結果なし")
        return

    print(f"\n{'='*60}")
    print(f"介入実験結果 (N={len(results)}, per strategy={len(results)//3})")
    print(f"{'='*60}")

    for s in ["U", "G", "S"]:
        sr = [r for r in results if r["strategy"] == s]
        if not sr:
            continue
        fm = [r["file_match"] for r in sr]
        lo = [r["line_overlap"] for r in sr]
        grad = [r["mean_abs_grad"] for r in sr]
        print(f"\n📊 戦略 {s} (N={len(sr)}):")
        print(f"  ファイル特定率: {sum(fm)}/{len(fm)} ({100*sum(fm)/len(fm):.1f}%)")
        print(f"  行重複率 (mean±std): {np.mean(lo):.4f} ± {np.std(lo):.4f}")
        print(f"  |∇_t Θ| (mean): {np.mean(grad):.4f}")
        print(f"  保持率 (mean): {np.mean([r['actual_retention'] for r in sr]):.4f}")

    u = [r["line_overlap"] for r in results if r["strategy"] == "U"]
    g = [r["line_overlap"] for r in results if r["strategy"] == "G"]
    s = [r["line_overlap"] for r in results if r["strategy"] == "S"]

    if len(u) > 1 and len(g) > 1:
        t_ug, p_ug = stats.ttest_rel(u, g)
        d = (np.mean(g) - np.mean(u)) / (np.sqrt((np.var(u) + np.var(g))/2) + 1e-10)
        print(f"\n🔬 U vs G (核心テスト: ∇_t Θ = 0 vs > 0):")
        print(f"  G - U = {np.mean(g) - np.mean(u):+.4f}")
        print(f"  paired t = {t_ug:.3f}, p = {p_ug:.4e}")
        print(f"  Cohen's d = {d:.3f}")
        verdict = ("✅ v3 支持" if np.mean(g) > np.mean(u) and p_ug < 0.05
                   else "❌ v3 棄却" if np.mean(g) < np.mean(u) and p_ug < 0.05
                   else "❓ 有意差なし")
        print(f"  判定: {verdict}")

    if len(u) > 1 and len(s) > 1:
        t_us, p_us = stats.ttest_rel(u, s)
        print(f"\n🔬 U vs S (∇_t Θ = 0 vs δ関数):")
        print(f"  S - U = {np.mean(s) - np.mean(u):+.4f}")
        print(f"  paired t = {t_us:.3f}, p = {p_us:.4e}")

    if len(u) > 2 and len(g) > 2:
        lev, lp = stats.levene(u, g)
        print(f"\n📊 Var(P) 比較:")
        print(f"  Var(U)={np.var(u):.4f}  Var(G)={np.var(g):.4f}  Var(S)={np.var(s):.4f}")
        print(f"  Levene U vs G: F={lev:.3f}, p={lp:.4e}")

# ============================================================
# §9 メインループ
# ============================================================
def run_experiment(
    api_key: str,
    n_per_strategy: int = 5,
    budget: float = 0.5,
    output_path: str = "/content/intervention_results.json",
    seed: int = 42,
    dry_run: bool = False,
    save_interval: int = 10,
):
    """
    介入実験メインループ。

    Args:
        api_key: Gemini API キー
        n_per_strategy: 各戦略あたりの trajectory 数
        budget: 情報保持率 (0-1)
        output_path: 結果保存先
        seed: 乱数シード
        dry_run: LLM 呼出をスキップ
        save_interval: N件ごとに中間保存
    """
    from datasets import load_dataset
    np.random.seed(seed)

    # Gemini セットアップ
    model = None if dry_run else setup_gemini(api_key)

    # データロード
    print(f"📥 nebius/SWE-agent-trajectories をロード中...")
    ds = load_dataset("nebius/SWE-agent-trajectories", split="train", streaming=True)

    print(f"🔍 成功 trajectory を {n_per_strategy} 件収集中...")
    examples = []
    scanned = 0
    for ex in ds:
        scanned += 1
        if len(examples) >= n_per_strategy:
            break
        if ex.get("target", False):
            traj = ex.get("trajectory", [])
            if isinstance(traj, str):
                traj = json.loads(traj)
            if len(traj) >= 6:
                examples.append(ex)
                if len(examples) % 10 == 0:
                    print(f"  {len(examples)}/{n_per_strategy} (scanned {scanned})")
    print(f"✅ {len(examples)} 件収集 (scanned {scanned})")

    # 実験ループ
    results = []
    total_calls = 0
    t_start = time.time()

    for ex_idx, example in enumerate(examples):
        traj = example.get("trajectory", [])
        if isinstance(traj, str):
            traj = json.loads(traj)

        _, issue_text, turns = parse_trajectory(traj)
        gold_patch = example.get("generated_patch", "")
        inst_id = example.get("instance_id", f"unk_{ex_idx}")

        if not turns or not gold_patch:
            continue

        for sname, sfunc in STRATEGIES.items():
            masked = sfunc(turns, budget)

            # Θ(t) と ∇_t Θ
            theta = [1.0 - m["masked_len"]/m["original_len"]
                     if m["original_len"] > 0 else 0.0 for m in masked]
            grad_stats = compute_grad(theta)

            total_orig = sum(m["original_len"] for m in masked)
            total_mask = sum(m["masked_len"] for m in masked)
            retention = total_mask / total_orig if total_orig > 0 else 0

            prompt = build_prompt(issue_text, masked)

            if dry_run:
                gen_patch = "[DRY RUN]"
                p_metrics = {"file_match": False, "line_overlap": 0.0,
                             "exact_match": False, "n_gold_files": 0,
                             "n_gen_files": 0, "n_gold_lines": 0, "n_gen_lines": 0}
            else:
                gen_patch = call_gemini(model, prompt)
                p_metrics = compute_P(gen_patch, gold_patch)
                total_calls += 1

            results.append({
                "instance_id": inst_id,
                "strategy": sname,
                "budget": budget,
                "n_turns": len(turns),
                "actual_retention": retention,
                "total_original_chars": total_orig,
                "total_masked_chars": total_mask,
                **grad_stats,
                **p_metrics,
                "prompt_len": len(prompt),
            })

        # 進捗表示 + 中間保存
        if (ex_idx + 1) % save_interval == 0 or ex_idx == len(examples) - 1:
            elapsed = time.time() - t_start
            rate = total_calls / elapsed if elapsed > 0 and total_calls > 0 else 0
            print(f"  [{ex_idx+1}/{len(examples)}] {total_calls} calls, "
                  f"{elapsed:.0f}s, {rate:.1f} calls/s")
            # 中間保存
            with open(output_path, "w") as f:
                json.dump({"results": results, "n": len(results),
                           "dry_run": dry_run, "budget": budget}, f, indent=2)

    elapsed = time.time() - t_start
    print(f"\n✅ 完了: {total_calls} calls in {elapsed:.0f}s")

    # 分析
    analyze(results)

    # 最終保存
    with open(output_path, "w") as f:
        json.dump({
            "experiment": "intervention_v3",
            "n_per_strategy": n_per_strategy,
            "budget": budget,
            "dry_run": dry_run,
            "total_calls": total_calls,
            "elapsed_seconds": elapsed,
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"💾 {output_path} に保存完了")
    return results


# ============================================================
# §10 Colab 用エントリポイント
# ============================================================
# Colab で実行する場合: 以下のセルを貼り付けて実行
#
# --- セル 1: インストール ---
# !pip install -q datasets google-generativeai scipy
#
# --- セル 2: API キー設定 ---
# from google.colab import userdata
# API_KEY = userdata.get('GEMINI_API_KEY')
# # または: API_KEY = "your-key-here"
#
# --- セル 3: パイロット (N=5) ---
# results = run_experiment(api_key=API_KEY, n_per_strategy=5, budget=0.5, dry_run=False)
#
# --- セル 4: 本番 (N=150) ---
# results = run_experiment(api_key=API_KEY, n_per_strategy=150, budget=0.5, dry_run=False)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--api_key", required=True)
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--budget", type=float, default=0.5)
    parser.add_argument("--output", default="/tmp/intervention_results.json")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()
    run_experiment(args.api_key, args.n, args.budget, args.output, dry_run=args.dry_run)
