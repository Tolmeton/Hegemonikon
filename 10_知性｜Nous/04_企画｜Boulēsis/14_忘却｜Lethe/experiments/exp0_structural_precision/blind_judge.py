"""
Experiment 0 — LLM Blind Judge
条件A/B の出力を LLM がラベル隠蔽で採点する。

設計方針:
  - 採点モデル: gemini-2.0-flash (デフォルト) または claude-opus-4-6 (--model claude)
    生成モデル Sonnet 4.6 と別モデル/別会社が blinder になる
  - 5次元採点 (D1-D5)
  - 条件ラベルは判定後に復元して統計計算

使い方:
  cd exp0_structural_precision
  source ../../../../../../.venv/bin/activate

  # Gemini (別会社でよりblind — デフォルト)
  export GOOGLE_API_KEY=...
  python blind_judge.py

  # Anthropic Opus (クレジット要)
  export ANTHROPIC_API_KEY=...
  python blind_judge.py --model claude

  python blind_judge.py --analyze-only  # 既存スコアの再集計
"""

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results" / "batch"
JUDGE_DIR = Path(__file__).parent / "results" / "blind_judge"

# 出力の最初の N 文字を judge に渡す (長すぎるとコスト増大)
OUTPUT_TRUNCATE = 6000

JUDGE_SYSTEM = """あなたは学術論文の推論品質を評価する専門家です。
これから深い問いへの思考プロセスを含むテキストを読み、5つの次元で1〜5点で採点してください。

採点次元の定義:
D1 推論の深度: 表面的な事実列挙か、因果の骨格を貫通しているか
  1 = 事実や事例の列挙のみ
  3 = 「なぜ」を1〜2段掘り下げている
  5 = Why を3段以上掘り下げ、根本的なメカニズムに到達している

D2 前提の明示度: 暗黙の前提を可視化しているか
  1 = 前提を問わず結論に向かう
  3 = いくつかの前提を明示している
  5 = AXIOM（変更不可能）とASSUMPTION（変更可能）を明確に分類して扱っている

D3 構造的一貫性: 結論が推論ステップから論理的に導かれているか
  1 = 飛躍が多く論理的整合性が低い
  3 = 主要な論理的連鎖は保たれているが部分的に飛躍がある
  5 = 各推論ステップが前段に支持されており、結論が必然的に導かれる

D4 精度の自己申告: 自分の確信度・不確実性を明示しているか
  1 = 全て断定的な記述（確信度の区別なし）
  3 = 一部の主張に確信度の差を示している
  5 = 各主要な主張に確信度ラベル（高・中・低 または数値）を付与している

D5 行動可能性: 読後に具体的な次の問いや行動が立つか
  1 = 読後に何もしたいことが生まれない（完結している）
  3 = 1〜2個の後続問いや発展が示唆される
  5 = 3個以上の延伸（次の問い・実験・応用）が具体的に見えている

出力形式（JSONのみ。前後のテキスト不要）:
{
  "D1": <1-5の整数>,
  "D2": <1-5の整数>,
  "D3": <1-5の整数>,
  "D4": <1-5の整数>,
  "D5": <1-5の整数>,
  "total": <D1〜D5の合計>,
  "one_line": "<この出力の最大の特徴を1文で>"
}"""


def load_results() -> list[dict]:
    """既存のバッチ結果を読み込む（batch_analysis.json 除外）"""
    results = []
    for p in sorted(RESULTS_DIR.glob("*.json")):
        if p.name == "batch_analysis.json":
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        data["_source_file"] = p.name
        results.append(data)
    return results


def truncate_output(text: str, max_chars: int = OUTPUT_TRUNCATE) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... 出力が長いため省略 ...]"


def judge_single_claude(client, uid: str, output_text: str) -> dict:
    """Anthropic Claude で1件採点"""
    import anthropic as _anthropic
    user_msg = f"""以下の思考プロセスを採点してください。

--- 思考プロセス (ID: {uid}) ---
{truncate_output(output_text)}
--- 終わり ---

上記の指示に従い、D1〜D5の採点結果をJSONで返してください。"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=256,
        temperature=0.0,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = response.content[0].text.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    scores = json.loads(raw.strip())
    scores["uid"] = uid
    scores["input_tokens"] = response.usage.input_tokens
    scores["output_tokens"] = response.usage.output_tokens
    return scores


def judge_single_gemini(model, uid: str, output_text: str) -> dict:
    """Gemini で1件採点"""
    user_msg = f"""以下の思考プロセスを採点してください。

--- 思考プロセス (ID: {uid}) ---
{truncate_output(output_text)}
--- 終わり ---

上記の指示に従い、D1〜D5の採点結果をJSONで返してください。"""

    full_prompt = JUDGE_SYSTEM + "\n\n" + user_msg

    response = model.generate_content(
        full_prompt,
        generation_config={"temperature": 0.0, "max_output_tokens": 1024},
    )

    raw = response.text.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    scores = json.loads(raw.strip())
    scores["uid"] = uid
    scores["input_tokens"] = 0   # Gemini は usage 取得方法が異なるため省略
    scores["output_tokens"] = 0
    return scores


def judge_single_gpt(client, uid: str, output_text: str, model: str = "gpt-4.1") -> dict:
    """OpenAI GPT で1件採点"""
    user_msg = f"""以下の思考プロセスを採点してください。

--- 思考プロセス (ID: {uid}) ---
{truncate_output(output_text)}
--- 終わり ---

上記の指示に従い、D1〜D5の採点結果をJSONで返してください。"""

    response = client.chat.completions.create(
        model=model,
        temperature=0.0,
        max_tokens=1024,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
    )

    raw = response.choices[0].message.content.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    scores = json.loads(raw.strip())
    scores["uid"] = uid
    scores["input_tokens"] = response.usage.prompt_tokens if response.usage else 0
    scores["output_tokens"] = response.usage.completion_tokens if response.usage else 0
    return scores


def run_judge(results: list[dict], model_name: str = "gemini") -> list[dict]:
    """全出力を blind judge で採点"""
    JUDGE_DIR.mkdir(parents=True, exist_ok=True)

    if model_name == "gemini":
        if not os.environ.get("GOOGLE_API_KEY"):
            print("ERROR: GOOGLE_API_KEY が設定されていません", file=sys.stderr)
            sys.exit(1)
        from google import genai
        client = genai.Client()
        GEMINI_MODEL = "gemini-3.1-pro-preview"

        class _GeminiModel:
            def __init__(self, c): self._c = c
            def generate_content(self, prompt, generation_config=None):
                cfg = generation_config or {}
                resp = self._c.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config={"temperature": cfg.get("temperature", 0.0),
                            "max_output_tokens": 8192,
                            "response_mime_type": "application/json"},
                )
                class _R:
                    def __init__(self, text): self.text = text
                return _R(resp.text)
        gemini_model = _GeminiModel(client)
        judge_fn = lambda uid, text: judge_single_gemini(gemini_model, uid, text)
        judge_model_label = GEMINI_MODEL
    elif model_name == "gpt":
        if not os.environ.get("OPENAI_API_KEY"):
            print("ERROR: OPENAI_API_KEY が設定されていません", file=sys.stderr)
            sys.exit(1)
        import openai as _openai
        client = _openai.OpenAI()
        gpt_model = "gpt-4.1"
        judge_fn = lambda uid, text: judge_single_gpt(client, uid, text, model=gpt_model)
        judge_model_label = gpt_model
    else:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("ERROR: ANTHROPIC_API_KEY が設定されていません", file=sys.stderr)
            sys.exit(1)
        import anthropic as _anthropic
        client = _anthropic.Anthropic()
        judge_fn = lambda uid, text: judge_single_claude(client, uid, text)
        judge_model_label = "claude-opus-4-6"

    # UID と condition のマッピング（judge は UID だけ見る）
    uid_map = {}
    for r in results:
        uid = f"{r['condition']}_{r['task_id']}_{r['trial']:02d}"
        uid_map[uid] = r["condition"]

    # シャッフルして採点
    items = [(r["_source_file"].replace(".json", ""), r["output"]) for r in results]
    random.shuffle(items)

    judge_results = []
    total = len(items)

    print(f"Blind Judge: {total} 件 / モデル: {judge_model_label}")
    print(f"出力先: {JUDGE_DIR}")
    print()

    for i, (uid, output_text) in enumerate(items):
        out_path = JUDGE_DIR / f"{uid}.json"
        if out_path.exists():
            print(f"[{i+1}/{total}] {uid} → スキップ (既存)")
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            judge_results.append(existing)
            continue

        print(f"[{i+1}/{total}] {uid} → 採点中...", end=" ", flush=True)
        try:
            scores = judge_fn(uid, output_text)
            # condition を後付けで追加（judge 実行時は隠蔽）
            scores["condition"] = uid_map[uid]
            scores["task_id"] = uid.split("_")[1]
            out_path.write_text(json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8")
            judge_results.append(scores)
            print(f"完了 (total={scores['total']})")
        except Exception as e:
            print(f"ERROR: {e}")
            continue

        time.sleep(0.3)

    return judge_results


def load_existing_judge_results() -> list[dict]:
    results = []
    if not JUDGE_DIR.exists():
        return results
    for p in sorted(JUDGE_DIR.glob("*.json")):
        if p.name == "judge_analysis.json":
            continue
        results.append(json.loads(p.read_text(encoding="utf-8")))
    return results


# --- 統計分析 ---

def compute_statistics(judge_results: list[dict]) -> dict:
    from collections import defaultdict

    by_cond = defaultdict(list)
    for r in judge_results:
        by_cond[r["condition"]].append(r)

    if not by_cond["A"] or not by_cond["B"]:
        return {"error": "条件 A または B の結果が不足"}

    dims = ["D1", "D2", "D3", "D4", "D5", "total"]
    stats = {
        "n_A": len(by_cond["A"]),
        "n_B": len(by_cond["B"]),
        "dimensions": {},
    }

    for d in dims:
        a_vals = [r[d] for r in by_cond["A"]]
        b_vals = [r[d] for r in by_cond["B"]]

        a_mean = sum(a_vals) / len(a_vals)
        b_mean = sum(b_vals) / len(b_vals)
        a_var = sum((x - a_mean) ** 2 for x in a_vals) / max(len(a_vals) - 1, 1)
        b_var = sum((x - b_mean) ** 2 for x in b_vals) / max(len(b_vals) - 1, 1)
        a_sd = a_var ** 0.5
        b_sd = b_var ** 0.5

        n_a, n_b = len(a_vals), len(b_vals)
        pooled_sd = (((n_a - 1) * a_var + (n_b - 1) * b_var) / max(n_a + n_b - 2, 1)) ** 0.5
        cohens_d = (b_mean - a_mean) / pooled_sd if pooled_sd > 0 else 0.0

        # Welch t-stat
        se = ((a_var / n_a) + (b_var / n_b)) ** 0.5
        t_stat = (b_mean - a_mean) / se if se > 0 else 0.0

        # Mann-Whitney U (simple calculation)
        u_stat = sum(1 for av in a_vals for bv in b_vals if bv > av) + \
                 0.5 * sum(1 for av in a_vals for bv in b_vals if bv == av)
        u_max = n_a * n_b

        stats["dimensions"][d] = {
            "A_mean": round(a_mean, 3),
            "B_mean": round(b_mean, 3),
            "A_sd": round(a_sd, 3),
            "B_sd": round(b_sd, 3),
            "diff_B_minus_A": round(b_mean - a_mean, 3),
            "cohens_d": round(cohens_d, 3),
            "t_stat": round(t_stat, 3),
            "mann_whitney_U": round(u_stat, 1),
            "U_max": u_max,
            "U_normalized": round(u_stat / u_max, 3) if u_max > 0 else 0,
        }

    # トピック別集計
    topic_stats = {}
    for tid in ["T1", "T2", "T3", "T4", "T5"]:
        a_t = [r["total"] for r in by_cond["A"] if r.get("task_id") == tid]
        b_t = [r["total"] for r in by_cond["B"] if r.get("task_id") == tid]
        if a_t and b_t:
            topic_stats[tid] = {
                "n_A": len(a_t),
                "n_B": len(b_t),
                "A_mean_total": round(sum(a_t) / len(a_t), 2),
                "B_mean_total": round(sum(b_t) / len(b_t), 2),
                "diff": round(sum(b_t) / len(b_t) - sum(a_t) / len(a_t), 2),
            }

    stats["by_topic"] = topic_stats

    # 判定: ≥3次元で d>0.5 かつ B方向
    d_above_05 = [
        d for d in ["D1", "D2", "D3", "D4", "D5"]
        if stats["dimensions"][d]["cohens_d"] > 0.5
    ]
    d_below_neg05 = [
        d for d in ["D1", "D2", "D3", "D4", "D5"]
        if stats["dimensions"][d]["cohens_d"] < -0.5
    ]

    if len(d_above_05) >= 3:
        verdict = "支持 — B 条件が推論品質で優位"
    elif len(d_above_05) <= 1 and len(d_below_neg05) == 0:
        verdict = "棄却 — blind judge は差を検出できず"
    else:
        verdict = "不明 — 追加実験推奨"

    stats["verdict"] = verdict
    stats["dims_d_above_0.5"] = d_above_05
    stats["dims_d_below_-0.5"] = d_below_neg05

    return stats


def print_stats(stats: dict) -> None:
    if "error" in stats:
        print(f"\nERROR: {stats['error']}")
        return

    print("\n" + "=" * 70)
    print("LLM Blind Judge 結果")
    print(f"N: A={stats['n_A']}, B={stats['n_B']}")
    print("=" * 70)

    print(f"\n{'次元':<10} {'A mean':>8} {'B mean':>8} {'差':>8} {'t':>7} {'d':>7} {'U_norm':>8}")
    print("-" * 65)

    labels = {
        "D1": "推論深度",
        "D2": "前提明示",
        "D3": "構造一貫",
        "D4": "精度申告",
        "D5": "行動可能",
        "total": "合計",
    }
    for d, label in labels.items():
        m = stats["dimensions"][d]
        print(f"{label:<10} {m['A_mean']:>8.2f} {m['B_mean']:>8.2f} "
              f"{m['diff_B_minus_A']:>+8.2f} {m['t_stat']:>7.2f} "
              f"{m['cohens_d']:>7.2f} {m['U_normalized']:>8.3f}")

    print(f"\n--- トピック別 (合計スコア) ---")
    for tid, t in stats.get("by_topic", {}).items():
        print(f"  {tid}: A={t['A_mean_total']:.1f}  B={t['B_mean_total']:.1f}  "
              f"diff={t['diff']:+.1f}")

    print(f"\n判定: {stats['verdict']}")
    print(f"d>0.5 の次元: {stats.get('dims_d_above_0.5', [])}")


def main():
    parser = argparse.ArgumentParser(description="Blind Judge 実験")
    parser.add_argument("--analyze-only", action="store_true", help="既存スコアの再集計のみ")
    parser.add_argument("--model", choices=["gemini", "claude", "gpt"], default="gemini",
                        help="採点モデル (default: gemini)")
    args = parser.parse_args()

    if args.analyze_only:
        judge_results = load_existing_judge_results()
        if not judge_results:
            print("ERROR: 既存のjudge結果がありません", file=sys.stderr)
            sys.exit(1)
        print(f"既存 judge 結果 {len(judge_results)} 件を読み込み")
    else:
        raw_results = load_results()
        print(f"バッチ結果 {len(raw_results)} 件を読み込み")
        judge_results = run_judge(raw_results, model_name=args.model)

    stats = compute_statistics(judge_results)
    print_stats(stats)

    if "error" not in stats:
        JUDGE_DIR.mkdir(parents=True, exist_ok=True)
        analysis_path = JUDGE_DIR / "judge_analysis.json"
        analysis_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n分析結果保存: {analysis_path}")


if __name__ == "__main__":
    main()
