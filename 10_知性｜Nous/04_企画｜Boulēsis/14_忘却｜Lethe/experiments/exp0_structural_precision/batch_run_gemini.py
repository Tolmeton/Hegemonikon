"""
Experiment 0 — Gemini CLI バッチ実行 (AI Ultra Personal tier)
クロスモデル検証: Claude Sonnet で得た H₃/H₃' を Gemini で追試

設計:
  - Tolmeton OAuth (681255 client) + GEMINI_WRAPPER_BYPASS=1
  - AI Ultra Personal tier 経由 (project-f2526536 = Tolmeton の project)
  - 結果は results/gemini/ に保存

前提:
  - ~/.gemini/oauth_creds.json に Tolmeton の gemini-cli OAuth creds が必要
  - Working creds backup: ~/.gemini/oauth_creds_Tolmeton_working.json

使い方:
  cd exp0_structural_precision

  # デフォルト (N=3 per condition per topic = 30 total for T1-T5)
  python batch_run_gemini.py

  # 本実験 (N=10 per condition per topic = 100 total)
  python batch_run_gemini.py --n 10

  # 分析のみ
  python batch_run_gemini.py --analyze-only
"""

import argparse
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# --- 設定 ---
MODEL = "gemini-3.1-pro-preview"  # /about で確認済みの AI Ultra model
GEMINI_BIN = "/usr/local/bin/gemini"  # wrapper ではなく直接呼出
ACCOUNT = "Tolmeton"  # ghost project binding 回避のため固定

EXP_DIR = Path(__file__).parent
RESULTS_DIR = EXP_DIR / "results" / "gemini"

TASK_PROMPTS = {
    "T1": {
        "topic": "なぜ複雑系はある閾値を超えると自己組織化するのか",
        "domain": "哲学・自然科学",
    },
    "T2": {
        "topic": "マイクロサービスアーキテクチャはなぜ意図に反して複雑さを増大させるのか",
        "domain": "ソフトウェア設計",
    },
    "T3": {
        "topic": "『理解した』という確信はなぜ理解の正確さと無相関なのか",
        "domain": "メタ認知",
    },
    "T4": {
        "topic": "なぜ言語は思考を制約すると同時に可能にするのか",
        "domain": "言語哲学",
    },
    "T5": {
        "topic": "成功した組織がなぜ次第に革新できなくなるのか",
        "domain": "組織論",
    },
}

USER_TEMPLATE = (
    "以下の問いについて、深い内部透徹を実行してください。\n\n"
    "問い: {topic}\n\n"
    "上記のシステムプロンプトで定義された認知スキルの手順に従い、"
    "標準モード（P-0, P-1, P-2, P-5）で実行してください。"
)


# --- 分析関数 (batch_run.py から移植) ---

import re

METRICS = {
    "rho_notation": [r"ρ[₀₁₂₃₄₅]", r"ρ_total", r"ρ_[a-z]", r"剰余\s*ρ", r"ρ\s*[>=<]", r"ρ\s*=\s*\{"],
    "U_labels": [r"U_sensory", r"U_arrow", r"U_depth", r"U_compose", r"U_context", r"U_adjoint", r"U_self", r"U_[a-z]+"],
    "categorical_vocab": [r"圏論", r"(?<![a-zA-Z])圏(?![論])", r"合成射", r"関手", r"随伴", r"[Ll]imit", r"[Cc]one", r"Yoneda", r"米田", r"自然変換", r"[Ff]unctor", r"[Ff]aithful", r"n-cell", r"(?<![a-zA-Z])射(?![影出])"],
    "coordinate_notation": [r"I×E", r"[Aa]fferent", r"[Ee]fferent", r"象限", r"座標"],
    "four_direction": [r"\+射", r"\+Δπ", r"\+変換", r"\+自己参照", r"4方向"],
    "fix_kalon_notation": [r"Fix\(", r"G∘F", r"Kalon\([0-9]", r"Ostwald", r"不動点", r"[◎◯✗]"],
    "ccl_expressions": [r"/noe", r"/ske", r"/zet", r"/bou", r"/ene", r"/lys", r"/ele", r"/tek", r">>", r"⊣", r"∘"],
}


def count_matches(text: str, patterns: list[str]) -> int:
    return sum(len(re.findall(p, text)) for p in patterns)


def analyze_output(text: str) -> dict:
    result = {}
    total = 0
    for name, patterns in METRICS.items():
        raw = count_matches(text, patterns)
        result[name] = raw
        total += raw
    result["total_structural"] = total
    result["axiom_count"] = len(re.findall(r"AXIOM", text))
    result["assumption_count"] = len(re.findall(r"ASSUMPTION", text))
    axiom_total = result["axiom_count"] + result["assumption_count"]
    result["axiom_ratio"] = round(result["axiom_count"] / axiom_total, 3) if axiom_total > 0 else 0.0
    result["bond_count"] = count_matches(text, [r"結合[点分]", r"結合を.*外す", r"溶解"])
    result["checkpoints"] = len(re.findall(r"\[CHECKPOINT", text))
    result["char_count"] = len(text)
    return result


# --- 実行 ---

def load_conditions() -> dict[str, str]:
    return {
        "A": (EXP_DIR / "condition_A_v2_noe.md").read_text(encoding="utf-8"),
        "B": (EXP_DIR / "condition_B_v2_noe.md").read_text(encoding="utf-8"),
    }


def run_gemini(system_prompt: str, user_prompt: str) -> tuple[str, float]:
    """Gemini CLI を subprocess で実行 (Tolmeton + BYPASS mode)"""
    full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"

    env = os.environ.copy()
    env["GEMINI_WRAPPER_BYPASS"] = "1"  # wrapper の project override を防ぐ

    start = time.time()
    result = subprocess.run(
        [GEMINI_BIN, "-p", full_prompt],
        capture_output=True,
        text=True,
        env=env,
        timeout=600,  # 10分タイムアウト (thinking model は遅い)
    )
    elapsed = time.time() - start

    if result.returncode != 0:
        raise RuntimeError(f"gemini failed: {result.stderr[:300]}")

    return result.stdout.strip(), elapsed


def run_single(condition: str, system_prompt: str, task_id: str, topic: str, trial: int) -> dict:
    user_msg = USER_TEMPLATE.format(topic=topic)
    output_text, elapsed = run_gemini(system_prompt, user_msg)

    return {
        "condition": condition,
        "task_id": task_id,
        "trial": trial,
        "model": MODEL,
        "account": ACCOUNT,
        "timestamp": datetime.now().isoformat(),
        "elapsed_sec": round(elapsed, 1),
        "output": output_text,
        "analysis": analyze_output(output_text),
    }


def run_batch(n_per_condition: int) -> list[dict]:
    conditions = load_conditions()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 全試行をシャッフルしたリストを作成
    trials = []
    for task_id, task_info in TASK_PROMPTS.items():
        for cond in ["A", "B"]:
            for trial_num in range(n_per_condition):
                trials.append((cond, task_id, task_info["topic"], trial_num))

    random.shuffle(trials)
    total = len(trials)

    n_topics = len(TASK_PROMPTS)
    print(f"Gemini バッチ実行: {total} 試行 ({n_per_condition}/条件/トピック × {n_topics} topics × 2 conditions)")
    print(f"モデル: {MODEL}, アカウント: {ACCOUNT}")
    print(f"保存先: {RESULTS_DIR}")
    print()

    results = []
    for i, (cond, task_id, topic, trial_num) in enumerate(trials):
        label = f"[{i+1}/{total}] {cond}-{task_id}-{trial_num:02d}"

        # 既存結果をスキップ
        out_path = RESULTS_DIR / f"{cond}_{task_id}_{trial_num:02d}.json"
        if out_path.exists():
            print(f"{label} → スキップ (既存)")
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            results.append(existing)
            continue

        print(f"{label} → 実行中...", end=" ", flush=True)

        try:
            result = run_single(cond, conditions[cond], task_id, topic, trial_num)
            out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            results.append(result)
            print(f"完了 ({result['elapsed_sec']}s, {result['analysis']['total_structural']} struct)")
        except subprocess.TimeoutExpired:
            print("タイムアウト")
            continue
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "quota" in err_msg.lower() or "rate" in err_msg.lower():
                print(f"レート制限。60秒待機...")
                time.sleep(60)
                try:
                    result = run_single(cond, conditions[cond], task_id, topic, trial_num)
                    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                    results.append(result)
                    print(f"  リトライ完了")
                except Exception as e2:
                    print(f"  リトライ ERROR: {e2}")
                    continue
            else:
                print(f"ERROR: {e}")
                continue

        # レート制限回避 (thinking model は遅いので間隔を空ける)
        time.sleep(5)

    return results


def load_existing_results() -> list[dict]:
    results = []
    if not RESULTS_DIR.exists():
        return results
    for p in sorted(RESULTS_DIR.glob("*.json")):
        if p.name.endswith("_analysis.json"):
            continue
        results.append(json.loads(p.read_text(encoding="utf-8")))
    return results


# --- 統計分析 ---

def compute_statistics(results: list[dict]) -> dict:
    from collections import defaultdict

    by_condition = defaultdict(list)
    by_condition_topic = defaultdict(list)
    for r in results:
        cond = r["condition"]
        by_condition[cond].append(r["analysis"])
        by_condition_topic[(cond, r["task_id"])].append(r["analysis"])

    if not by_condition["A"] or not by_condition["B"]:
        return {"error": "条件 A or B の結果が不足"}

    stats = {
        "n_A": len(by_condition["A"]),
        "n_B": len(by_condition["B"]),
        "model": MODEL,
        "metrics": {},
    }

    metric_keys = list(METRICS.keys()) + ["total_structural", "axiom_ratio", "axiom_count", "assumption_count", "bond_count", "checkpoints"]

    for key in metric_keys:
        a_vals = [r[key] for r in by_condition["A"]]
        b_vals = [r[key] for r in by_condition["B"]]

        a_mean = sum(a_vals) / len(a_vals)
        b_mean = sum(b_vals) / len(b_vals)

        a_var = sum((x - a_mean) ** 2 for x in a_vals) / max(len(a_vals) - 1, 1)
        b_var = sum((x - b_mean) ** 2 for x in b_vals) / max(len(b_vals) - 1, 1)
        a_sd = a_var ** 0.5
        b_sd = b_var ** 0.5

        # Welch t-test
        if a_var + b_var > 0:
            se = ((a_var / len(a_vals)) + (b_var / len(b_vals))) ** 0.5
            t_stat = (b_mean - a_mean) / se if se > 0 else 0
        else:
            t_stat = 0

        # Cohen's d (pooled)
        n_a, n_b = len(a_vals), len(b_vals)
        pooled_sd = (((n_a - 1) * a_var + (n_b - 1) * b_var) / max(n_a + n_b - 2, 1)) ** 0.5
        cohens_d = (b_mean - a_mean) / pooled_sd if pooled_sd > 0 else 0

        stats["metrics"][key] = {
            "A_mean": round(a_mean, 3),
            "B_mean": round(b_mean, 3),
            "A_sd": round(a_sd, 3),
            "B_sd": round(b_sd, 3),
            "diff": round(b_mean - a_mean, 3),
            "t_stat": round(t_stat, 3),
            "cohens_d": round(cohens_d, 3),
        }

    # トピック別
    stats["by_topic"] = {}
    for task_id in TASK_PROMPTS:
        a_vals = [r["total_structural"] for r in by_condition_topic.get(("A", task_id), [])]
        b_vals = [r["total_structural"] for r in by_condition_topic.get(("B", task_id), [])]
        if a_vals and b_vals:
            stats["by_topic"][task_id] = {
                "n": len(a_vals),
                "A_mean": round(sum(a_vals) / len(a_vals), 1),
                "B_mean": round(sum(b_vals) / len(b_vals), 1),
            }

    return stats


def print_stats(stats: dict) -> None:
    print("\n" + "=" * 80)
    print(f"構造的精度加重仮説 — Gemini クロスモデル検証")
    print(f"Model: {stats.get('model', MODEL)}")
    print(f"N: A={stats['n_A']}, B={stats['n_B']}")
    print("=" * 80)

    print(f"\n{'指標':<22} {'A mean':>8} {'B mean':>8} {'差':>8} {'t':>7} {'d':>7}")
    print("-" * 70)

    key_labels = {
        "total_structural": "構造語彙合計",
        "rho_notation": "ρ 記法",
        "U_labels": "U_x ラベル",
        "categorical_vocab": "圏論語彙",
        "coordinate_notation": "座標記法",
        "four_direction": "4 方向分類",
        "fix_kalon_notation": "Fix/Kalon",
        "ccl_expressions": "CCL 式",
        "axiom_ratio": "AXIOM 比率",
        "axiom_count": "AXIOM 数",
        "assumption_count": "ASSUMPTION 数",
        "bond_count": "結合分析語数",
        "checkpoints": "CHECKPOINT 数",
    }

    for key, label in key_labels.items():
        m = stats["metrics"].get(key)
        if not m:
            continue
        print(f"{label:<22} {m['A_mean']:>8.2f} {m['B_mean']:>8.2f} {m['diff']:>+8.2f} {m['t_stat']:>7.2f} {m['cohens_d']:>7.2f}")

    if stats.get("by_topic"):
        print(f"\n--- トピック別 (total_structural) ---")
        for tid, t in stats["by_topic"].items():
            topic_short = TASK_PROMPTS[tid]["topic"][:20]
            print(f"  {tid} {topic_short}... A={t['A_mean']:>6.1f}  B={t['B_mean']:>6.1f}")


def main():
    parser = argparse.ArgumentParser(description="Exp0 Gemini バッチ実行 (6垢ローテーション)")
    parser.add_argument("--n", type=int, default=3, help="条件あたりトピックあたりの試行数 (default: 3)")
    parser.add_argument("--analyze-only", action="store_true", help="既存結果の再分析のみ")
    args = parser.parse_args()

    if args.analyze_only:
        results = load_existing_results()
        if not results:
            print("ERROR: 既存結果がありません", file=sys.stderr)
            sys.exit(1)
        print(f"既存結果 {len(results)} 件を読み込み")
    else:
        results = run_batch(args.n)

    if not results:
        print("ERROR: 結果が 0 件")
        sys.exit(1)

    stats = compute_statistics(results)
    if "error" in stats:
        print(f"\nERROR: {stats['error']}")
        sys.exit(1)
    print_stats(stats)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    analysis_path = RESULTS_DIR / "gemini_analysis.json"
    analysis_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n分析結果保存: {analysis_path}")


if __name__ == "__main__":
    main()
