"""
Exp0 — CC Agent 出力の JSON 永続化スクリプト

CC Agent (Claude Code Agent) で生成した A/B テスト出力を
batch_run.py と同じ JSON スキーマで永続化する。

使い方:
  cd exp0_structural_precision
  source ../../../../../../.venv/bin/activate

  # ファイルから読み込み
  python cc_agent_persist.py --condition A --task T1 --file output_A_T1.txt

  # stdin から読み込み (パイプ)
  cat output_A_T1.txt | python cc_agent_persist.py --condition A --task T1

  # クリップボードから (xclip)
  xclip -selection clipboard -o | python cc_agent_persist.py --condition B --task T3

  # trial 番号を明示 (デフォルト: 自動採番)
  python cc_agent_persist.py --condition A --task T1 --trial 0 --file output.txt

  # 一覧表示
  python cc_agent_persist.py --list

  # 全 cc_agent 結果を再分析 (analyze_output を再実行)
  python cc_agent_persist.py --reanalyze

  # バッチ + cc_agent の統合分散分析
  python cc_agent_persist.py --variance
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# batch_run.py から analyze_output を import
from batch_run import METRICS, analyze_output, TASK_PROMPTS

EXP_DIR = Path(__file__).parent
CC_AGENT_DIR = EXP_DIR / "results" / "cc_agent"
BATCH_DIR = EXP_DIR / "results" / "batch"


def next_trial_number(condition: str, task_id: str) -> int:
    """既存ファイルから次の trial 番号を自動採番"""
    CC_AGENT_DIR.mkdir(parents=True, exist_ok=True)
    existing = list(CC_AGENT_DIR.glob(f"{condition}_{task_id}_*.json"))
    if not existing:
        return 0
    nums = []
    for p in existing:
        # {condition}_{task_id}_{trial:02d}.json
        parts = p.stem.split("_")
        try:
            nums.append(int(parts[-1]))
        except (ValueError, IndexError):
            pass
    return max(nums) + 1 if nums else 0


def persist_output(condition: str, task_id: str, trial: int, text: str) -> Path:
    """CC Agent 出力を JSON として保存"""
    CC_AGENT_DIR.mkdir(parents=True, exist_ok=True)

    analysis = analyze_output(text)

    record = {
        "condition": condition,
        "task_id": task_id,
        "trial": trial,
        "model": "cc_agent",  # batch_run.py は "claude-sonnet-4-6"
        "source": "cc_agent",  # バッチとの区別用
        "timestamp": datetime.now().isoformat(),
        "input_tokens": 0,
        "output_tokens": 0,
        "output": text,
        "analysis": analysis,
    }

    out_path = CC_AGENT_DIR / f"{condition}_{task_id}_{trial:02d}.json"
    out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def list_results() -> None:
    """CC Agent 結果の一覧表示"""
    if not CC_AGENT_DIR.exists():
        print("CC Agent 結果なし")
        return

    files = sorted(CC_AGENT_DIR.glob("*.json"))
    files = [f for f in files if not f.name.startswith(("cc_agent_analysis", "variance"))]

    if not files:
        print("CC Agent 結果なし")
        return

    print(f"CC Agent 結果: {len(files)} 件")
    print(f"{'ファイル':<25} {'条件':>4} {'タスク':>5} {'構造語彙':>8} {'bond':>5} {'文字数':>6}")
    print("-" * 60)

    for p in files:
        data = json.loads(p.read_text(encoding="utf-8"))
        a = data.get("analysis", {})
        print(
            f"{p.name:<25} {data.get('condition', '?'):>4} "
            f"{data.get('task_id', '?'):>5} "
            f"{a.get('total_structural', 0):>8} "
            f"{a.get('bond_count', 0):>5} "
            f"{a.get('char_count', 0):>6}"
        )


def reanalyze() -> None:
    """全 cc_agent 結果の analysis を再計算"""
    if not CC_AGENT_DIR.exists():
        print("CC Agent 結果なし")
        return

    files = sorted(CC_AGENT_DIR.glob("*.json"))
    files = [f for f in files if not f.name.startswith(("cc_agent_analysis", "variance"))]

    updated = 0
    for p in files:
        data = json.loads(p.read_text(encoding="utf-8"))
        if "output" not in data:
            continue
        data["analysis"] = analyze_output(data["output"])
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        updated += 1

    print(f"再分析: {updated} 件更新")


def load_all_results(sources: list[str] | None = None) -> list[dict]:
    """batch + cc_agent の全結果を読み込み"""
    results = []

    if sources is None or "batch" in sources:
        if BATCH_DIR.exists():
            for p in sorted(BATCH_DIR.glob("*.json")):
                if p.name in ("batch_analysis.json", "variance_analysis.json"):
                    continue
                data = json.loads(p.read_text(encoding="utf-8"))
                data.setdefault("source", "batch")
                results.append(data)

    if sources is None or "cc_agent" in sources:
        if CC_AGENT_DIR.exists():
            for p in sorted(CC_AGENT_DIR.glob("*.json")):
                if p.name.startswith(("cc_agent_analysis", "variance")):
                    continue
                data = json.loads(p.read_text(encoding="utf-8"))
                data.setdefault("source", "cc_agent")
                results.append(data)

    return results


def compute_variance_analysis(results: list[dict]) -> dict:
    """
    bond_count, axiom_count, assumption_count, checkpoints の
    分散分析 (F検定 + Brown-Forsythe) を自動計算。

    手動カウントを完全に置換する。
    """
    from collections import defaultdict
    import math

    by_condition = defaultdict(list)
    for r in results:
        cond = r["condition"]
        by_condition[cond].append(r["analysis"])

    if not by_condition["A"] or not by_condition["B"]:
        return {"error": "条件 A or B の結果が不足"}

    targets = ["axiom_count", "assumption_count", "bond_count", "checkpoints"]
    analysis = {}

    for key in targets:
        a_vals = [r[key] for r in by_condition["A"]]
        b_vals = [r[key] for r in by_condition["B"]]

        n_a, n_b = len(a_vals), len(b_vals)
        a_mean = sum(a_vals) / n_a
        b_mean = sum(b_vals) / n_b
        a_var = sum((x - a_mean) ** 2 for x in a_vals) / max(n_a - 1, 1)
        b_var = sum((x - b_mean) ** 2 for x in b_vals) / max(n_b - 1, 1)
        a_sd = math.sqrt(a_var)
        b_sd = math.sqrt(b_var)

        # CV (変動係数)
        a_cv = a_sd / a_mean if a_mean > 0 else 0
        b_cv = b_sd / b_mean if b_mean > 0 else 0
        cv_ratio = b_cv / a_cv if a_cv > 0 else float("inf")

        # F検定 (分散比)
        f_ratio = a_var / b_var if b_var > 0 else float("inf")

        # Levene (mean-based) + Brown-Forsythe (median-based) — scipy
        from scipy.stats import levene as _levene
        _, levene_p = _levene(a_vals, b_vals, center="mean")
        _, bf_p = _levene(a_vals, b_vals, center="median")

        # Bonferroni 補正 (4 検定)
        bonferroni_alpha = 0.05 / len(targets)

        analysis[key] = {
            "A_n": n_a,
            "B_n": n_b,
            "A_mean": round(a_mean, 3),
            "B_mean": round(b_mean, 3),
            "A_sd": round(a_sd, 3),
            "B_sd": round(b_sd, 3),
            "A_cv": round(a_cv, 3),
            "B_cv": round(b_cv, 3),
            "cv_ratio_B_over_A": round(cv_ratio, 3),
            "F_ratio_A_over_B": round(f_ratio, 3),
            "levene_mean_p": round(levene_p, 4),
            "brown_forsythe_p": round(bf_p, 4),
            "bonferroni_alpha": bonferroni_alpha,
            "bonferroni_significant": "yes" if min(levene_p, bf_p) < bonferroni_alpha else "no",
            "direction_cv": "B stable" if b_cv < a_cv else "A stable",
        }

    return analysis


def _welch_t_test_p(a: list[float], b: list[float]) -> float:
    """Welch t 検定の両側 p 値。scipy.stats を使用。"""
    if len(a) < 2 or len(b) < 2:
        return 1.0
    from scipy.stats import ttest_ind
    _, p = ttest_ind(a, b, equal_var=False)
    return float(p)


def run_variance(sources: list[str] | None = None) -> None:
    """統合分散分析を実行・保存"""
    results = load_all_results(sources)
    if not results:
        print("結果なし")
        return

    # ソース別の件数
    batch_n = sum(1 for r in results if r.get("source") == "batch")
    cc_n = sum(1 for r in results if r.get("source") == "cc_agent")
    print(f"統合分散分析: batch={batch_n}, cc_agent={cc_n}, total={len(results)}")

    analysis = compute_variance_analysis(results)
    if "error" in analysis:
        print(f"ERROR: {analysis['error']}")
        return

    # 結果表示
    print(f"\n{'指標':<20} {'A_mean':>8} {'B_mean':>8} {'A_SD':>7} {'B_SD':>7} {'F比':>7} {'BF_p':>8} {'方向':>10}")
    print("-" * 80)
    for key, v in analysis.items():
        print(
            f"{key:<20} {v['A_mean']:>8.3f} {v['B_mean']:>8.3f} "
            f"{v['A_sd']:>7.3f} {v['B_sd']:>7.3f} "
            f"{v['F_ratio_A_over_B']:>7.3f} {v['brown_forsythe_p']:>8.4f} "
            f"{v['direction_cv']:>10}"
        )

    # 保存
    CC_AGENT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CC_AGENT_DIR / "variance_analysis.json"
    out_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n保存: {out_path}")

    # batch 側にも同じ形式で上書き (互換性)
    batch_out = BATCH_DIR / "variance_analysis.json"
    batch_out.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"保存: {batch_out}")


def main():
    parser = argparse.ArgumentParser(
        description="Exp0 CC Agent 出力の JSON 永続化",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 永続化モード
    parser.add_argument("--condition", "-c", choices=["A", "B"], help="条件 (A or B)")
    parser.add_argument("--task", "-t", help="タスク ID (T1-T10)")
    parser.add_argument("--trial", type=int, default=None, help="trial 番号 (デフォルト: 自動採番)")
    parser.add_argument("--file", "-f", help="出力テキストファイル (省略時: stdin)")

    # ユーティリティモード
    parser.add_argument("--list", "-l", action="store_true", help="CC Agent 結果一覧")
    parser.add_argument("--reanalyze", action="store_true", help="全結果の analysis を再計算")
    parser.add_argument("--variance", "-v", action="store_true", help="統合分散分析")
    parser.add_argument("--source", nargs="*", choices=["batch", "cc_agent"],
                        help="分散分析対象ソース (デフォルト: 全て)")

    args = parser.parse_args()

    if args.list:
        list_results()
        return

    if args.reanalyze:
        reanalyze()
        return

    if args.variance:
        run_variance(args.source)
        return

    # 永続化モード — 必須引数チェック
    if not args.condition or not args.task:
        parser.error("永続化には --condition (-c) と --task (-t) が必須")

    task_id = args.task.upper()
    if task_id not in TASK_PROMPTS:
        parser.error(f"不明なタスク ID: {task_id} (有効: {', '.join(TASK_PROMPTS.keys())})")

    # テキスト読み込み
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        print("テキストを入力 (Ctrl+D で終了):", file=sys.stderr)
        text = sys.stdin.read()

    if not text.strip():
        print("ERROR: 空のテキスト", file=sys.stderr)
        sys.exit(1)

    # trial 番号
    trial = args.trial if args.trial is not None else next_trial_number(args.condition, task_id)

    # 保存
    out_path = persist_output(args.condition, task_id, trial, text)
    analysis = json.loads(out_path.read_text(encoding="utf-8"))["analysis"]

    print(f"保存: {out_path}")
    print(f"  条件: {args.condition}, タスク: {task_id}, trial: {trial}")
    print(f"  文字数: {analysis['char_count']}, 構造語彙: {analysis['total_structural']}, "
          f"bond: {analysis['bond_count']}, AXIOM: {analysis['axiom_count']}")


if __name__ == "__main__":
    main()
