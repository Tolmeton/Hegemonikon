"""
Experiment 0 Phase B — 構造語彙伝搬の自動テキスト分析

目的: LLM 出力に構造構文がどの程度伝搬するかを自動カウントする。
      LLM judge の主観性を排除した客観指標。

指標 7 カテゴリ:
  1. ρ 記法 (ρ₀, ρ₁, ..., ρ_total)
  2. U_x 忘却ラベル (U_sensory, U_arrow, ...)
  3. 圏論語彙 (圏, 射, 関手, 随伴, Limit, Cone, 合成射, ...)
  4. 座標記法 (I×E, Afferent, Efferent, ×, 象限, ...)
  5. 4 方向分類 (+射, +Δπ, +変換, +自己参照)
  6. Fix/Kalon 記法 (Fix(G∘F), Kalon(0-1), ◎, Ostwald)
  7. CCL 式 (/noe, /ske, >>, ⊣)

各カテゴリの raw count + 正規化 (per 1000 tokens) を算出。
"""

import json
import re
import sys
from pathlib import Path


# --- 指標定義 ---

METRICS = {
    "rho_notation": {
        "description": "ρ 剰余記法",
        "patterns": [
            r"ρ[₀₁₂₃₄₅]",
            r"ρ_total",
            r"ρ_[a-z]",
            r"剰余\s*ρ",
            r"ρ\s*[>=<]",
            r"ρ\s*=\s*\{",
        ],
    },
    "U_labels": {
        "description": "U_x 忘却ラベル",
        "patterns": [
            r"U_sensory",
            r"U_arrow",
            r"U_depth",
            r"U_compose",
            r"U_context",
            r"U_adjoint",
            r"U_self",
            r"U_[a-z]+",  # catch-all for other U_ labels
        ],
    },
    "categorical_vocab": {
        "description": "圏論語彙",
        "patterns": [
            r"(?<![a-zA-Z])圏(?![論])",  # 圏 but not 圏論
            r"圏論",
            r"(?<![a-zA-Z])射(?![影出])",  # 射 but not 射影/射出
            r"合成射",
            r"関手",
            r"随伴",
            r"[Ll]imit",
            r"[Cc]one",
            r"[Cc]olimit",
            r"Yoneda",
            r"米田",
            r"自然変換",
            r"[Ff]unctor",
            r"[Ff]aithful",
            r"n-cell",
            r"前順序",
            r"ガロア",
            r"豊穣",
        ],
    },
    "coordinate_notation": {
        "description": "座標記法",
        "patterns": [
            r"I×E",
            r"[Aa]fferent",
            r"[Ee]fferent",
            r"象限",
            r"座標",
            r"I\s*象限",
            r"Explore.*Exploit|Exploit.*Explore",
        ],
    },
    "four_direction": {
        "description": "4 方向分類",
        "patterns": [
            r"\+射",
            r"\+Δπ",
            r"\+変換",
            r"\+自己参照",
            r"4方向",
            r"4方向分類",
        ],
    },
    "fix_kalon_notation": {
        "description": "Fix/Kalon 記法",
        "patterns": [
            r"Fix\(G∘F\)",
            r"Fix\(",
            r"G∘F",
            r"Kalon\([0-9]",
            r"Ostwald",
            r"不動点",
            r"[◎◯✗]",
        ],
    },
    "ccl_expressions": {
        "description": "CCL 式",
        "patterns": [
            r"/noe",
            r"/ske",
            r"/zet",
            r"/bou",
            r"/ene",
            r"/lys",
            r"/ele",
            r"/tek",
            r">>",  # 射演算子
            r"⊣",  # 随伴記号
            r"∘",  # 合成記号
        ],
    },
}


def count_matches(text: str, patterns: list[str]) -> int:
    """パターンリストの全マッチ数を返す (重複除外なし)"""
    total = 0
    for pattern in patterns:
        total += len(re.findall(pattern, text))
    return total


def estimate_tokens(text: str) -> int:
    """簡易トークン数推定 (日本語: ~1.5 chars/token, 英語: ~4 chars/token)"""
    # 雑な推定だが正規化には十分
    jp_chars = len(re.findall(r"[\u3000-\u9fff\uff00-\uffef]", text))
    en_chars = len(text) - jp_chars
    return int(jp_chars / 1.5 + en_chars / 4)


def analyze_output(text: str) -> dict:
    """1 つの出力テキストを全指標で分析"""
    est_tokens = estimate_tokens(text)
    results = {
        "char_count": len(text),
        "estimated_tokens": est_tokens,
    }

    total_structural = 0
    for metric_name, metric_def in METRICS.items():
        raw = count_matches(text, metric_def["patterns"])
        per_1k = round(raw / (est_tokens / 1000), 2) if est_tokens > 0 else 0
        results[metric_name] = {"raw": raw, "per_1k_tokens": per_1k}
        total_structural += raw

    results["total_structural"] = {
        "raw": total_structural,
        "per_1k_tokens": round(total_structural / (est_tokens / 1000), 2)
        if est_tokens > 0
        else 0,
    }

    # Phase 到達度
    phases_reached = []
    for p in ["P-0", "P-1", "P-2", "P-3", "P-4", "P-5", "P-6"]:
        if p in text:
            phases_reached.append(p)
    results["phases_reached"] = phases_reached
    results["max_phase"] = phases_reached[-1] if phases_reached else "none"

    # CHECKPOINT の数
    results["checkpoints"] = len(re.findall(r"\[CHECKPOINT", text))

    # 前提の数 (AXIOM/ASSUMPTION)
    results["axiom_count"] = len(re.findall(r"AXIOM", text))
    results["assumption_count"] = len(re.findall(r"ASSUMPTION", text))

    # 結合点の数
    bond_patterns = [r"結合[点分]", r"結合を.*外す", r"溶解"]
    results["bond_analysis_count"] = count_matches(text, bond_patterns)

    return results


def compare_conditions(result_a: dict, result_b: dict) -> dict:
    """条件 A と B の差分を算出"""
    comparison = {}
    for key in METRICS:
        a_raw = result_a[key]["raw"]
        b_raw = result_b[key]["raw"]
        a_norm = result_a[key]["per_1k_tokens"]
        b_norm = result_b[key]["per_1k_tokens"]
        comparison[key] = {
            "A_raw": a_raw,
            "B_raw": b_raw,
            "diff_raw": b_raw - a_raw,
            "A_per_1k": a_norm,
            "B_per_1k": b_norm,
            "diff_per_1k": round(b_norm - a_norm, 2),
            "ratio": round(b_norm / a_norm, 2) if a_norm > 0 else float("inf"),
        }
    # Total
    comparison["total_structural"] = {
        "A_raw": result_a["total_structural"]["raw"],
        "B_raw": result_b["total_structural"]["raw"],
        "A_per_1k": result_a["total_structural"]["per_1k_tokens"],
        "B_per_1k": result_b["total_structural"]["per_1k_tokens"],
    }
    return comparison


def print_report(result_a: dict, result_b: dict, comparison: dict) -> None:
    """比較レポートを出力"""
    print("=" * 70)
    print("構造語彙伝搬分析 — Experiment 0 Phase B")
    print("=" * 70)

    print(f"\n{'指標':<25} {'A (raw)':>8} {'B (raw)':>8} {'差':>6} {'A/1k':>7} {'B/1k':>7} {'倍率':>6}")
    print("-" * 70)

    for key, desc in [(k, METRICS[k]["description"]) for k in METRICS]:
        c = comparison[key]
        print(
            f"{desc:<25} {c['A_raw']:>8} {c['B_raw']:>8} {c['diff_raw']:>+6} "
            f"{c['A_per_1k']:>7.1f} {c['B_per_1k']:>7.1f} {c['ratio']:>5.1f}x"
        )

    t = comparison["total_structural"]
    print("-" * 70)
    print(
        f"{'合計':<25} {t['A_raw']:>8} {t['B_raw']:>8} "
        f"{'':>6} {t['A_per_1k']:>7.1f} {t['B_per_1k']:>7.1f}"
    )

    print(f"\n--- 構造的特徴 ---")
    print(f"{'':>25} {'条件A':>15} {'条件B':>15}")
    print(f"{'到達Phase':<25} {result_a['max_phase']:>15} {result_b['max_phase']:>15}")
    print(f"{'CHECKPOINT数':<25} {result_a['checkpoints']:>15} {result_b['checkpoints']:>15}")
    print(f"{'AXIOM数':<25} {result_a['axiom_count']:>15} {result_b['axiom_count']:>15}")
    print(f"{'ASSUMPTION数':<25} {result_a['assumption_count']:>15} {result_b['assumption_count']:>15}")
    print(f"{'結合分析語数':<25} {result_a['bond_analysis_count']:>15} {result_b['bond_analysis_count']:>15}")
    print(f"{'推定トークン数':<25} {result_a['estimated_tokens']:>15} {result_b['estimated_tokens']:>15}")


def main():
    results_dir = Path(__file__).parent / "results"

    # ドライラン出力を読み込み
    files = {
        "A": results_dir / "dry_run_v2_A_T1_output.md",
        "B": results_dir / "dry_run_v2_B_T1_output.md",
    }

    for cond, path in files.items():
        if not path.exists():
            print(f"ERROR: {path} が見つかりません", file=sys.stderr)
            sys.exit(1)

    text_a = files["A"].read_text(encoding="utf-8")
    text_b = files["B"].read_text(encoding="utf-8")

    result_a = analyze_output(text_a)
    result_b = analyze_output(text_b)
    comparison = compare_conditions(result_a, result_b)

    print_report(result_a, result_b, comparison)

    # JSON 保存
    analysis = {
        "condition_A": result_a,
        "condition_B": result_b,
        "comparison": comparison,
    }
    out_path = results_dir / "structural_propagation_analysis.json"
    out_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n保存: {out_path}")


if __name__ == "__main__":
    main()
