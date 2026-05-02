#!/usr/bin/env python3
# PROOF: [L2/実験] <- 60_実験/07_CCL-PL/measure_forgetfulness.py S(e) 実測
"""
S(e) 実測実験 — Thm 14 の経験的検証

CCL WF マクロの description から CCL 式を抽出し、
forgetfulness_score で S_explicit / S_implicit を計測。

目的:
  1. 実際の CCL 式の忘却スコア分布を計測
  2. どの座標が最も忘却されやすいかを特定
  3. 暗黙座標 (族帰属) の回復効果を定量化
  4. Theorema Egregium Cognitionis の予測力を検証

出力: テーブル + 統計 + 座標ごとの欠落頻度
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# PURPOSE: hermeneus パッケージを import パスに追加
WORKSPACE = Path("/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon")
SRC_DIR = WORKSPACE / "20_機構｜Mekhane" / "_src｜ソースコード" / "hermeneus" / "src"
sys.path.insert(0, str(SRC_DIR.parent.parent))

from hermeneus.src.forgetfulness_score import (
    COORDINATES,
    COORDINATE_TO_U_PATTERN,
    ScoreResult,
    ImplicitScoreResult,
    score_ccl,
    score_ccl_implicit,
    extract_coordinates,
    extract_implicit_coordinates,
)
from hermeneus.src.parser import CCLParser


# =============================================================================
# CCL 式の収集
# =============================================================================

# PURPOSE: WF マクロの description から CCL 式を抽出する
def collect_ccl_expressions(wf_dir: Path) -> List[Tuple[str, str]]:
    """WF マクロファイルから (名前, CCL式) のペアを収集する。

    description 行の「—」の後ろを CCL 式として抽出。
    自然言語のみの description はスキップ。
    """
    expressions = []
    for md_file in sorted(wf_dir.glob("ccl-*.md")):
        name = md_file.stem  # e.g., "ccl-build"
        text = md_file.read_text(encoding="utf-8")

        # YAML frontmatter の description を抽出
        match = re.search(r'description:\s*["\']?(.*?)["\']?\s*$', text, re.MULTILINE)
        if not match:
            continue

        desc = match.group(1).strip()

        # 「—」区切りで CCL 式を分離
        if "—" in desc:
            parts = desc.split("—", 1)
            ccl_str = parts[1].strip()
            # CCL 式らしさチェック: / で始まるか演算子を含むか
            if "/" in ccl_str or "@" in ccl_str:
                expressions.append((name, ccl_str))
        elif desc.startswith("/"):
            expressions.append((name, desc))

    return expressions


# =============================================================================
# 計測
# =============================================================================

# PURPOSE: 1つの CCL 式を計測し結果を返す
def measure_one(name: str, ccl_str: str) -> Optional[Dict]:
    """CCL 式をパースし、S_explicit と S_implicit を計測する。

    パースに失敗した場合は None を返す。
    """
    try:
        result = score_ccl_implicit(ccl_str)
        return {
            "name": name,
            "ccl": ccl_str,
            "s_explicit": result.explicit.score,
            "s_implicit": result.s_implicit,
            "recovery": result.explicit.score - result.s_implicit,
            "present_explicit": sorted(result.explicit.present_coordinates),
            "present_implicit": sorted(result.implicit_coordinates),
            "present_all": sorted(result.all_coordinates),
            "missing_explicit": sorted(result.explicit.missing_coordinates),
            "missing_implicit": sorted(result.missing_implicit),
            "verb_coverage": result.verb_coverage,
            "diagnoses": [
                {
                    "coord": d.coordinate,
                    "u_pattern": d.u_pattern,
                    "description": d.description,
                    "nomoi": d.candidate_nomoi,
                }
                for d in result.explicit.diagnoses
            ],
        }
    except Exception as e:
        return {
            "name": name,
            "ccl": ccl_str,
            "error": str(e),
        }


# =============================================================================
# 分析
# =============================================================================

# PURPOSE: 集計統計を計算する
def analyze(results: List[Dict]) -> Dict:
    """成功した計測結果から統計を集計する。"""
    successes = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]

    if not successes:
        return {"error": "パース成功なし", "errors": errors}

    # 基本統計
    s_exp = [r["s_explicit"] for r in successes]
    s_imp = [r["s_implicit"] for r in successes]
    recovery = [r["recovery"] for r in successes]

    # 座標ごとの欠落頻度 (明示座標)
    coord_missing_count = {c: 0 for c in sorted(COORDINATES)}
    for r in successes:
        for c in r["missing_explicit"]:
            coord_missing_count[c] += 1

    # 座標ごとの欠落頻度 (暗黙込み)
    coord_missing_implicit = {c: 0 for c in sorted(COORDINATES)}
    for r in successes:
        for c in r["missing_implicit"]:
            coord_missing_implicit[c] += 1

    # 動詞カバレッジの集計
    coord_verb_total = {c: 0 for c in sorted(COORDINATES)}
    for r in successes:
        for c, count in r["verb_coverage"].items():
            coord_verb_total[c] += count

    n = len(successes)
    return {
        "n_total": len(results),
        "n_success": n,
        "n_error": len(errors),
        "s_explicit": {
            "mean": sum(s_exp) / n,
            "min": min(s_exp),
            "max": max(s_exp),
            "median": sorted(s_exp)[n // 2],
        },
        "s_implicit": {
            "mean": sum(s_imp) / n,
            "min": min(s_imp),
            "max": max(s_imp),
            "median": sorted(s_imp)[n // 2],
        },
        "recovery": {
            "mean": sum(recovery) / n,
            "min": min(recovery),
            "max": max(recovery),
            "description": "S_explicit - S_implicit (暗黙座標による回復量)",
        },
        "coord_missing_explicit": coord_missing_count,
        "coord_missing_implicit": coord_missing_implicit,
        "coord_verb_total_coverage": coord_verb_total,
        "errors": [{"name": e["name"], "ccl": e["ccl"], "error": e["error"]} for e in errors],
    }


# =============================================================================
# 表示
# =============================================================================

# PURPOSE: 結果を見やすく表示する
def print_results(results: List[Dict], stats: Dict):
    """計測結果と統計をテーブル形式で表示する。"""

    successes = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]

    # --- 個別結果テーブル ---
    print("=" * 100)
    print("S(e) 実測結果 — CCL WF マクロ")
    print("=" * 100)
    print()
    print(f"{'名前':<18} {'S_exp':>6} {'S_imp':>6} {'回復':>6} {'明示座標':<20} {'欠落':>6}")
    print("-" * 80)

    for r in sorted(successes, key=lambda x: x["s_explicit"], reverse=True):
        present = ",".join(r["present_explicit"]) if r["present_explicit"] else "(なし)"
        print(f"{r['name']:<18} {r['s_explicit']:>6.3f} {r['s_implicit']:>6.3f} "
              f"{r['recovery']:>6.3f} {present:<20} {len(r['missing_explicit']):>2}/6")

    # --- エラー ---
    if errors:
        print()
        print(f"--- パースエラー ({len(errors)} 件) ---")
        for e in errors:
            print(f"  {e['name']}: {e['error'][:80]}")

    # --- 統計 ---
    print()
    print("=" * 100)
    print("統計サマリ")
    print("=" * 100)
    print()
    n = stats["n_success"]
    print(f"計測対象: {stats['n_total']} 式 (成功: {n}, エラー: {stats['n_error']})")
    print()

    for label, key in [("S_explicit", "s_explicit"), ("S_implicit", "s_implicit"), ("回復量", "recovery")]:
        s = stats[key]
        print(f"{label:>12}: mean={s['mean']:.3f}  min={s['min']:.3f}  max={s['max']:.3f}  "
              f"median={s.get('median', 'N/A')}")
    print()

    # --- 座標ごとの欠落頻度 ---
    print("座標ごとの欠落頻度:")
    print(f"  {'座標':>4} {'明示欠落':>10} {'暗黙込み':>10} {'動詞カバー':>10} {'U パターン':<15} {'説明'}")
    print(f"  {'-'*4} {'-'*10} {'-'*10} {'-'*10} {'-'*15} {'-'*10}")
    for c in sorted(COORDINATES):
        u_name, desc, _ = COORDINATE_TO_U_PATTERN[c]
        exp_miss = stats["coord_missing_explicit"][c]
        imp_miss = stats["coord_missing_implicit"][c]
        verb_cov = stats["coord_verb_total_coverage"][c]
        print(f"  {c:>4} {exp_miss:>7}/{n} {imp_miss:>7}/{n} {verb_cov:>10} {u_name:<15} {desc}")


# =============================================================================
# メイン
# =============================================================================

def main():
    wf_dir = WORKSPACE / ".agents" / "workflows"

    # 1. CCL 式の収集
    expressions = collect_ccl_expressions(wf_dir)
    print(f"収集した CCL 式: {len(expressions)} 個")
    print()

    # 2. 計測
    results = []
    for name, ccl_str in expressions:
        result = measure_one(name, ccl_str)
        if result:
            results.append(result)

    # 3. 分析
    stats = analyze(results)

    # 4. 表示
    print_results(results, stats)

    # 5. JSON 出力
    output_path = Path(__file__).parent / "forgetfulness_measurement.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"results": results, "stats": stats}, f, ensure_ascii=False, indent=2)
    print(f"\n詳細結果を保存: {output_path}")


if __name__ == "__main__":
    main()
