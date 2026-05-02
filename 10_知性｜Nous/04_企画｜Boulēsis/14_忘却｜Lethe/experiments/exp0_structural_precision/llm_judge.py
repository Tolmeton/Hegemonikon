"""
Experiment 0 — LLM Judge (Opus 盲検評価)
claude-opus-4-6 が条件ラベルを知らない状態で推論「質」を5次元評価する。

設計原則:
  - 盲検: Opus は条件 A/B を知らない。出力テキストのみ渡す
  - 語彙バイアス回避: 評価指示に「専門記法の有無で判断するな」を明示
  - 構造化出力: JSON で ratings + justification を返させる
  - 事後ラベル開示: 全評価完了後に条件を紐付け

使い方:
  cd exp0_structural_precision
  source ../../../../../../.venv/bin/activate
  export ANTHROPIC_API_KEY=...

  python llm_judge.py                   # 各条件から N=5 をランダムサンプル
  python llm_judge.py --n 10            # 各条件から N=10 サンプル
  python llm_judge.py --all             # 全 32 件を評価 (A=18, B=14)
  python llm_judge.py --analyze-only    # 既存 judge 結果の再集計のみ

Ochema LS 経由での実行 (代替):
  hub_execute(ochema, plan_task, {task: "llm_judge.py --n 5 を実行して結果を報告"})
"""

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

# anthropic は --direct 時のみ使用 (遅延 import)

# --- 設定 ---
JUDGE_MODEL_DIRECT = "claude-opus-4-6"           # Anthropic API 直接
JUDGE_MODEL_OCHEMA = "[LS]:Claude Opus 4.6"      # Ochema LS ラウンドロビン (CC quota)
OCHEMA_BASE_URL = os.environ.get("OCHEMA_BASE_URL", "http://localhost:8766")
MAX_TOKENS = 2048
TEMPERATURE = 0.3  # 評価の一貫性を高めるため低め

EXP_DIR = Path(__file__).parent
RESULTS_DIR = EXP_DIR / "results" / "batch"
JUDGE_DIR = EXP_DIR / "results" / "judge"

# --- 評価プロンプト ---

JUDGE_SYSTEM = """あなたは推論品質の評価者です。
以下の出力を評価してください。この出力は「深い内部透徹」を行う認知スキルの実行結果です。
6つの次元で 1-5 の整数スコアを付けてください。出力がどのような条件で生成されたかは知らされていません。

各次元の定義とアンカー（5と3と1の基準）:
1. coordinate_alignment: 認識的・理論的焦点を保ち、内部思考に留まっているか
   - 5: 完全に内部思考に留まり、認識的焦点が一貫している
   - 3: 概ね内部思考だが、時折外部行動の提案や実用的助言に逸れる
   - 1: 内部思考と外部行動が混在し、認識的焦点が不明瞭

2. phase_hierarchy: 知覚・前提確認から構造透徹・検証へ段階的に深化しているか
   - 5: 明確な段階的深化。各段階が前段の成果を受けて進む
   - 3: 段階構造はあるが、一部の段階間の接続が曖昧
   - 1: 段階構造が不明瞭。フラットに議論が展開

3. bond_dissolution: 構造の結合点を特定し、各結合を溶解して核を見通しているか
   - 5: 結合点が具体的に特定され、溶解の結果が明示的に異なる
   - 3: 結合分析はあるが、溶解前後の差が曖昧
   - 1: 結合分析が形式的。溶解しても構造が変わっていない

4. convergence_quality: 結論が「蒸留しても変化しない」不動点の特性を持つか
   - 5: 結論を再蒸留しても変化しない。余分も不足もない
   - 3: 結論は妥当だが、さらに蒸留すれば改善の余地がある
   - 1: 結論が冗長または不足。蒸留が不十分

5. faithful_preservation: 透徹の過程で元の構造の本質的関係が保存されているか
   - 5: 元の構造の本質的関係が全て保存され、損失が説明されている
   - 3: 大部分は保存されているが、一部の損失が未説明
   - 1: 元の構造との関係が不明瞭。保存検証がない

6. residue_generation: 各段階で「元にはなかった新しい構造」が生成されているか
   - 5: 複数段階で具体的な新規洞察が生成されている
   - 3: 一部の段階で新規洞察はあるが、他は形式的
   - 1: 新規洞察がほぼない。入力の言い換えに留まる

必ず以下の JSON 形式で回答してください:
{
  "coordinate_alignment": <1-5>,
  "coordinate_alignment_why": "<1-2文の理由>",
  "phase_hierarchy": <1-5>,
  "phase_hierarchy_why": "<1-2文の理由>",
  "bond_dissolution": <1-5>,
  "bond_dissolution_why": "<1-2文の理由>",
  "convergence_quality": <1-5>,
  "convergence_quality_why": "<1-2文の理由>",
  "faithful_preservation": <1-5>,
  "faithful_preservation_why": "<1-2文の理由>",
  "residue_generation": <1-5>,
  "residue_generation_why": "<1-2文の理由>",
  "overall_note": "<全体的な印象を1文>"
}

JSON 以外のテキストは不要です。"""

JUDGE_USER_TEMPLATE = """以下は「{topic}」という問いに対する回答です。
推論の質を評価してください。

---
{output_text}
---"""

TASK_TOPICS = {
    "T1": "なぜ複雑系はある閾値を超えると自己組織化するのか",
    "T2": "マイクロサービスアーキテクチャはなぜ意図に反して複雑さを増大させるのか",
    "T3": "『理解した』という確信はなぜ理解の正確さと無相関なのか",
    "T4": "なぜ言語は思考を制約すると同時に可能にするのか",
    "T5": "成功した組織がなぜ次第に革新できなくなるのか",
    # Exp0-hard: 科学的抽象タスク
    "T6": "なぜ随伴関手は『最良の近似』を与えるのか — 自由関手と忘却関手の間の tension は何を最適化しているか",
    "T7": "49次元の adhoc 特徴量がなぜ理論的に導出した特徴量より cosine 類似度で優位なのか — メトリクス問題か情報問題か",
    "T8": "変分自由エネルギーの最小化はなぜ『正確さの最大化』と『複雑さの最小化』のトレードオフを同時に達成するのか",
    "T9": "embedding 空間で異なるレジスタ（学術論文 vs 会話ログ）が意味的に近接配置されるための条件は何か",
    "T10": "偏 ρ_ccl > 0 が『構造理解の証拠』と確定できる閾値はどう設定すべきか — 帰無分布はどう構成するか",
}

DIMENSIONS = [
    "coordinate_alignment",
    "phase_hierarchy",
    "bond_dissolution",
    "convergence_quality",
    "faithful_preservation",
    "residue_generation",
]


# --- データ読み込み ---

def load_all_results() -> list[dict]:
    results = []
    for p in sorted(RESULTS_DIR.glob("*.json")):
        if p.name == "batch_analysis.json":
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        results.append(data)
    return results


def sample_balanced(results: list[dict], n_per_condition: int | None) -> list[dict]:
    """条件ごとに n_per_condition をサンプル (None = 全件)"""
    by_condition = {"A": [], "B": []}
    for r in results:
        cond = r["condition"]
        if cond in by_condition:
            by_condition[cond].append(r)

    sampled = []
    for cond, items in by_condition.items():
        if n_per_condition is None or n_per_condition >= len(items):
            sampled.extend(items)
        else:
            sampled.extend(random.sample(items, n_per_condition))

    return sampled


def blind_samples(samples: list[dict]) -> tuple[list[dict], dict[str, str]]:
    """
    条件ラベルを隠す。
    Returns: (blind_list, id_to_condition)
      blind_list: [{sample_id, task_id, topic, output}, ...]
      id_to_condition: {sample_id: condition}
    """
    shuffled = samples.copy()
    random.shuffle(shuffled)

    blind_list = []
    id_to_condition = {}

    for i, r in enumerate(shuffled):
        sid = f"S{i+1:03d}"
        id_to_condition[sid] = r["condition"]
        blind_list.append({
            "sample_id": sid,
            "task_id": r["task_id"],
            "topic": TASK_TOPICS[r["task_id"]],
            "output": r["output"],
            # 条件ラベルは含めない
        })

    return blind_list, id_to_condition


# --- Judge 実行 ---

def _parse_ratings(raw_text: str) -> dict:
    """JSON レスポンスをパース。失敗時は parse_error を返す。"""
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        import re
        m = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if m:
            return json.loads(m.group())
        return {"parse_error": raw_text}


def judge_single_ls_direct(sample: dict, svc) -> dict:
    """OchemaService._ask_ls を直接呼ぶ (hgk 上で実行時)。HTTP ブリッジをバイパス。"""
    user_msg = JUDGE_USER_TEMPLATE.format(
        topic=sample["topic"],
        output_text=sample["output"],
    )
    full_msg = f"{JUDGE_SYSTEM}\n\n{user_msg}"

    resp = svc._ask_ls(full_msg, "claude-opus", timeout=300.0)
    raw_text = (resp.text or "").strip()

    return {
        "sample_id": sample["sample_id"],
        "task_id": sample["task_id"],
        "timestamp": datetime.now().isoformat(),
        "input_tokens": 0,
        "output_tokens": 0,
        "route": "ls_direct",
        "ratings": _parse_ratings(raw_text),
    }


def judge_single_ochema(sample: dict, bearer_token: str) -> dict:
    """Ochema LS ルート経由 (OpenAI 互換 API)"""
    user_msg = JUDGE_USER_TEMPLATE.format(
        topic=sample["topic"],
        output_text=sample["output"],
    )

    headers = {"Authorization": f"Bearer {bearer_token}"}
    payload = {
        "model": JUDGE_MODEL_OCHEMA,
        "messages": [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "stream": False,
    }

    resp = httpx.post(
        f"{OCHEMA_BASE_URL}/v1/chat/completions",
        json=payload,
        headers=headers,
        timeout=300,
    )
    resp.raise_for_status()
    data = resp.json()

    raw_text = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})

    return {
        "sample_id": sample["sample_id"],
        "task_id": sample["task_id"],
        "timestamp": datetime.now().isoformat(),
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
        "route": "ochema_ls",
        "ratings": _parse_ratings(raw_text),
    }


def judge_single_direct(client, sample: dict) -> dict:
    """Anthropic API 直接 (--direct フラグ時)"""
    user_msg = JUDGE_USER_TEMPLATE.format(
        topic=sample["topic"],
        output_text=sample["output"],
    )

    response = client.messages.create(
        model=JUDGE_MODEL_DIRECT,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw_text = response.content[0].text.strip()

    return {
        "sample_id": sample["sample_id"],
        "task_id": sample["task_id"],
        "timestamp": datetime.now().isoformat(),
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "route": "anthropic_direct",
        "ratings": _parse_ratings(raw_text),
    }


def run_judge(n_per_condition: int | None, use_all: bool, use_direct: bool = False, use_ls_direct: bool = False) -> list[dict]:
    svc = None  # OchemaService (--ls-direct 時のみ)

    if use_ls_direct:
        # OchemaService._ask_ls を直接呼ぶ (hgk 上で実行時)
        try:
            from mekhane.ochema.service import OchemaService
        except ImportError:
            print("ERROR: mekhane が import できません。hgk の src ディレクトリで実行してください:", file=sys.stderr)
            print("  cd 20_機構｜Mekhane/_src｜ソースコード && python -m exp0_structural_precision.llm_judge --ls-direct", file=sys.stderr)
            sys.exit(1)
        svc = OchemaService()
        ls = svc._get_ls_client()
        if not ls:
            print("ERROR: LS に接続できません", file=sys.stderr)
            sys.exit(1)
        client = None
        bearer_token = None
        route_label = "OchemaService._ask_ls 直接 (LS ラウンドロビン)"
    elif use_direct:
        import anthropic
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("ERROR: ANTHROPIC_API_KEY が設定されていません", file=sys.stderr)
            sys.exit(1)
        client = anthropic.Anthropic()
        bearer_token = None
        route_label = f"Anthropic API 直接 ({JUDGE_MODEL_DIRECT})"
    else:
        client = None
        bearer_token = os.environ.get("HGK_OPENAI_COMPAT_TOKEN", "").strip()
        if not bearer_token:
            print("ERROR: HGK_OPENAI_COMPAT_TOKEN が設定されていません", file=sys.stderr)
            print("  Ochema サーバーの Bearer トークンを設定してください。")
            print("  直接 API を使う場合: python llm_judge.py --direct", file=sys.stderr)
            print("  LS 直接: python llm_judge.py --ls-direct (hgk 上)", file=sys.stderr)
            sys.exit(1)
        route_label = f"Ochema LS ({JUDGE_MODEL_OCHEMA} @ {OCHEMA_BASE_URL})"

    JUDGE_DIR.mkdir(parents=True, exist_ok=True)

    all_results = load_all_results()
    if not all_results:
        print("ERROR: バッチ結果が見つかりません", file=sys.stderr)
        sys.exit(1)

    n = None if use_all else n_per_condition
    samples = sample_balanced(all_results, n)
    blind_list, id_to_condition = blind_samples(samples)

    total = len(blind_list)
    print(f"盲検評価: {total} サンプル (A={sum(1 for v in id_to_condition.values() if v=='A')}, "
          f"B={sum(1 for v in id_to_condition.values() if v=='B')})")
    print(f"Judge: {route_label}")
    print()

    judge_results = []
    for i, sample in enumerate(blind_list):
        sid = sample["sample_id"]

        # 既存結果をスキップ
        out_path = JUDGE_DIR / f"{sid}.json"
        if out_path.exists():
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            existing["condition"] = id_to_condition[sid]
            judge_results.append(existing)
            print(f"[{i+1}/{total}] {sid} → スキップ (既存)")
            continue

        print(f"[{i+1}/{total}] {sid} ({sample['task_id']}) → 評価中...", end=" ", flush=True)
        try:
            if use_ls_direct:
                result = judge_single_ls_direct(sample, svc)
            elif use_direct:
                result = judge_single_direct(client, sample)
            else:
                result = judge_single_ochema(sample, bearer_token)
            result_with_cond = {**result, "condition": id_to_condition[sid]}
            out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            judge_results.append(result_with_cond)
            dims_str = " ".join(f"{d[:3]}={result['ratings'].get(d, '?')}" for d in DIMENSIONS)
            print(f"完了 [{dims_str}]")
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                print("レート制限。60秒待機...", flush=True)
                time.sleep(60)
                try:
                    if use_ls_direct:
                        result = judge_single_ls_direct(sample, svc)
                    elif use_direct:
                        result = judge_single_direct(client, sample)
                    else:
                        result = judge_single_ochema(sample, bearer_token)
                    result_with_cond = {**result, "condition": id_to_condition[sid]}
                    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                    judge_results.append(result_with_cond)
                    print(f"  リトライ完了")
                except Exception as e2:
                    print(f"  リトライ ERROR: {e2}")
                    continue
            else:
                print(f"ERROR: {e}")
                continue

        time.sleep(1)

    # 条件マッピングを保存
    map_path = JUDGE_DIR / "condition_map.json"
    map_path.write_text(json.dumps(id_to_condition, ensure_ascii=False, indent=2), encoding="utf-8")

    return judge_results


# --- 統計分析 ---

def load_existing_judge_results() -> list[dict]:
    """既存 judge 結果を読み込み、condition_map.json で条件を紐付け"""
    map_path = JUDGE_DIR / "condition_map.json"
    if not map_path.exists():
        return []
    id_to_condition = json.loads(map_path.read_text(encoding="utf-8"))

    results = []
    for p in sorted(JUDGE_DIR.glob("S*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        sid = data["sample_id"]
        data["condition"] = id_to_condition.get(sid, "?")
        results.append(data)
    return results


def compute_judge_statistics(judge_results: list[dict]) -> dict:
    from collections import defaultdict

    by_condition = defaultdict(list)
    for r in judge_results:
        if "ratings" not in r or "parse_error" in r.get("ratings", {}):
            continue
        by_condition[r["condition"]].append(r["ratings"])

    if not by_condition["A"] or not by_condition["B"]:
        return {"error": "条件 A or B の結果が不足"}

    stats = {
        "n_A": len(by_condition["A"]),
        "n_B": len(by_condition["B"]),
        "dimensions": {},
    }

    for dim in DIMENSIONS:
        a_vals = [r[dim] for r in by_condition["A"] if isinstance(r.get(dim), (int, float))]
        b_vals = [r[dim] for r in by_condition["B"] if isinstance(r.get(dim), (int, float))]
        if not a_vals or not b_vals:
            continue

        a_mean = sum(a_vals) / len(a_vals)
        b_mean = sum(b_vals) / len(b_vals)
        a_var = sum((x - a_mean) ** 2 for x in a_vals) / max(len(a_vals) - 1, 1)
        b_var = sum((x - b_mean) ** 2 for x in b_vals) / max(len(b_vals) - 1, 1)

        se = ((a_var / len(a_vals)) + (b_var / len(b_vals))) ** 0.5
        t_stat = (b_mean - a_mean) / se if se > 0 else 0

        n_a, n_b = len(a_vals), len(b_vals)
        pooled_sd = (((n_a - 1) * a_var + (n_b - 1) * b_var) / max(n_a + n_b - 2, 1)) ** 0.5
        cohens_d = (b_mean - a_mean) / pooled_sd if pooled_sd > 0 else 0

        stats["dimensions"][dim] = {
            "A_mean": round(a_mean, 3),
            "B_mean": round(b_mean, 3),
            "diff": round(b_mean - a_mean, 3),
            "t_stat": round(t_stat, 3),
            "cohens_d": round(cohens_d, 3),
            "n_A": len(a_vals),
            "n_B": len(b_vals),
        }

    # composite score
    a_totals = [sum(r[d] for d in DIMENSIONS if isinstance(r.get(d), (int, float))) for r in by_condition["A"]]
    b_totals = [sum(r[d] for d in DIMENSIONS if isinstance(r.get(d), (int, float))) for r in by_condition["B"]]
    if a_totals and b_totals:
        a_m = sum(a_totals) / len(a_totals)
        b_m = sum(b_totals) / len(b_totals)
        stats["composite"] = {
            "A_mean": round(a_m, 2),
            "B_mean": round(b_m, 2),
            "diff": round(b_m - a_m, 2),
            "max_possible": len(DIMENSIONS) * 5,
        }

    return stats


def print_judge_stats(stats: dict) -> None:
    print("\n" + "=" * 70)
    print("Exp0 — LLM Judge 分析結果 (Opus 盲検)")
    print(f"N: A={stats['n_A']}, B={stats['n_B']}")
    print("=" * 70)

    dim_labels = {
        "coordinate_alignment": "座標一致度",
        "phase_hierarchy": "段階的深化",
        "bond_dissolution": "結合溶解",
        "convergence_quality": "収束品質",
        "faithful_preservation": "構造保存",
        "residue_generation": "新規構造",
    }

    print(f"\n{'次元':<18} {'A mean':>8} {'B mean':>8} {'差':>7} {'t':>7} {'d':>7}")
    print("-" * 60)
    for dim in DIMENSIONS:
        m = stats["dimensions"].get(dim)
        if not m:
            continue
        label = dim_labels[dim]
        print(f"{label:<18} {m['A_mean']:>8.2f} {m['B_mean']:>8.2f} "
              f"{m['diff']:>+7.2f} {m['t_stat']:>7.2f} {m['cohens_d']:>7.2f}")

    if "composite" in stats:
        c = stats["composite"]
        print("-" * 60)
        print(f"{'総合スコア (30点満点)':<18} {c['A_mean']:>8.2f} {c['B_mean']:>8.2f} {c['diff']:>+7.2f}")


def main():
    parser = argparse.ArgumentParser(description="Exp0 LLM Judge (Opus 盲検)")
    parser.add_argument("--n", type=int, default=5, help="各条件からのサンプル数 (default: 5)")
    parser.add_argument("--all", action="store_true", help="全件評価 (A=18, B=14)")
    parser.add_argument("--direct", action="store_true", help="Anthropic API 直接")
    parser.add_argument("--ls-direct", action="store_true", help="OchemaService._ask_ls 直接 (hgk 上で実行)")
    parser.add_argument("--analyze-only", action="store_true", help="既存 judge 結果の再集計のみ")
    args = parser.parse_args()

    if args.analyze_only:
        judge_results = load_existing_judge_results()
        if not judge_results:
            print("ERROR: 既存 judge 結果がありません", file=sys.stderr)
            sys.exit(1)
        print(f"既存 judge 結果 {len(judge_results)} 件を読み込み")
    else:
        judge_results = run_judge(
            n_per_condition=args.n, use_all=args.all,
            use_direct=args.direct, use_ls_direct=args.ls_direct,
        )

    stats = compute_judge_statistics(judge_results)
    if "error" in stats:
        print(f"\nERROR: {stats['error']}")
        print("judge 結果が 0 件です。クレジット補充後に再実行してください。")
        sys.exit(1)
    print_judge_stats(stats)

    JUDGE_DIR.mkdir(parents=True, exist_ok=True)
    analysis_path = JUDGE_DIR / "judge_analysis.json"
    analysis_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n分析結果保存: {analysis_path}")


if __name__ == "__main__":
    main()
