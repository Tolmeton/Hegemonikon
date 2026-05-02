#!/usr/bin/env python3
# PROOF: [L2/実験] <- 60_実験｜Peira/07_CCL-PL A0→Phase B-CoT→CoTプロンプトがρに与える影響
"""
H1 実験: CoT Prompting → ρ 増加の検証

VISION.md §8.3H の予測:
  CoT prompting は中間対象を外部化し、U_output の像を拡大する
  → fullness 上昇 → ρ 増加

3条件の被験者内設計:
  C0: Bare      — コードのみ (ベースライン)
  C1: CoT-structure — 構造分析を促すプロンプト付き
  C2: CoT-step     — 一般的 step-by-step プロンプト付き

主要仮説:
  H0: Δρ_CoT = ρ(C1) − ρ(C0) ≤ 0
  H1: Δρ_CoT > 0 (片側検定)

Usage:
  python cot_experiment.py --dry-run --model codebert       # プロンプト確認
  python cot_experiment.py --model codebert --cot all        # 全条件実行
  python cot_experiment.py --model codellama --bits 4 --cot all
"""

# PURPOSE: H1 CoT 実験パイプライン

import sys
import json
import argparse
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# mekhane パスの解決 — structural_probe.py の import 前に設定する必要がある
# structural_probe.py内の _HGK_ROOT がディレクトリ深度の計算ミスにより
# 04_企画|Boulēsis を指してしまうため、正しいルートからのパスを先に注入する
_SCRIPT_DIR = Path(__file__).parent
_HGK_ROOT_CORRECT = _SCRIPT_DIR.parents[3]  # experiments → Lethe → Boulēsis → Nous → HGK ルート
_MEKHANE_SRC = _HGK_ROOT_CORRECT / "20_機構｜Mekhane" / "_src｜ソースコード"
if _MEKHANE_SRC.exists():
    sys.path.insert(0, str(_MEKHANE_SRC))

import numpy as np

# structural_probe.py から関数を import
from structural_probe import (
    prepare_data,
    prepare_data_p3b,
    load_model,
    extract_hidden_states,
    cosine_similarity,
    normalized_levenshtein,
    code_to_ccl,
    multivariate_partial_correlation,
    ProbeDataPoint,
    MODEL_CONFIGS,
    _NumpyEncoder,
    _SCRIPT_DIR,
)


# ============================================================
# CoT プロンプト生成
# ============================================================

# 3条件のプロンプトテンプレート
COT_TEMPLATES = {
    # C0: ベースライン — コードのみ (=既存 structural_probe と同一)
    "bare": None,

    # C1: 構造分析特化 — 構造情報の外部化を促す
    "structure": (
        "# Analyze the structural pattern of this code:\n"
        "{code}\n"
        "# Structural analysis: This code uses"
    ),

    # C2: 汎用 step-by-step — 構造に特化しない一般的 CoT
    "step": (
        "# Let's analyze this step by step:\n"
        "{code}\n"
        "# Step 1: First, this code"
    ),
}

# 条件コード
COT_CONDITIONS = {
    "bare": "C0",
    "structure": "C1",
    "step": "C2",
}


# PURPOSE: CoT プロンプトを生成
def generate_cot_prompt(code: str, mode: str) -> str:
    """コードに CoT プロンプトを付加する。

    Args:
        code: Python コードスニペット
        mode: "bare" / "structure" / "step"
    Returns:
        プロンプト付きコード (bare の場合はそのまま)
    """
    template = COT_TEMPLATES.get(mode)
    if template is None:
        return code
    return template.format(code=code)


# ============================================================
# CoT 条件別データ構造
# ============================================================

@dataclass
class CoTResult:
    """1つの条件での全ペア結果。"""
    condition: str           # "bare" / "structure" / "step"
    condition_code: str      # "C0" / "C1" / "C2"
    model_key: str
    n_pairs: int
    n_layers: int
    # 各ペア × 各層の cosine 類似度
    pair_cosines: list = field(default_factory=list)  # [pair_idx][layer_idx]
    # 層別の Spearman ρ (cos vs ccl_similarity)
    layer_rhos: list = field(default_factory=list)
    # 層別の偏相関 ρ
    layer_partial_rhos: list = field(default_factory=list)
    # ベスト ρ
    best_rho: float = 0.0
    best_rho_layer: int = -1
    best_partial_rho: float = 0.0
    best_partial_layer: int = -1


# ============================================================
# メインパイプライン
# ============================================================

# PURPOSE: 1条件の hidden state 抽出 + cosine 計算
def run_condition(
    data: list[ProbeDataPoint],
    model, tokenizer, device,
    n_layers: int,
    cot_mode: str,
    model_key: str,
    max_length: int = 512,
) -> CoTResult:
    """1つの CoT 条件で全ペアの hidden state を抽出し cosine を計算。"""
    condition_code = COT_CONDITIONS[cot_mode]
    print(f"\n{'='*60}")
    print(f"  条件: {condition_code} ({cot_mode})")
    print(f"{'='*60}")

    pair_cosines = []
    for idx, dp in enumerate(data):
        # CoT プロンプト生成
        code_a = generate_cot_prompt(dp.code_a if dp.code_a else "", cot_mode)
        code_b = generate_cot_prompt(dp.code_b if dp.code_b else "", cot_mode)

        # P3a の場合: code_a/code_b が空 → pair から取得
        # P3a は StructuralPair から作成されるため code_a/code_b を持たない
        # → 別途取得が必要
        if not code_a.strip() or code_a == generate_cot_prompt("", cot_mode):
            # P3a の場合: p3_benchmark の生データから再取得
            from p3_benchmark import create_benchmark_pairs
            raw_pairs = create_benchmark_pairs()
            if idx < len(raw_pairs):
                code_a = generate_cot_prompt(raw_pairs[idx].func_a_source, cot_mode)
                code_b = generate_cot_prompt(raw_pairs[idx].func_b_source, cot_mode)

        # Hidden state 抽出
        hs_a = extract_hidden_states(code_a, model, tokenizer, device, max_length)
        hs_b = extract_hidden_states(code_b, model, tokenizer, device, max_length)

        # 層別 cosine 類似度
        cosines = []
        for layer_idx in range(min(len(hs_a), len(hs_b))):
            cos = cosine_similarity(hs_a[layer_idx], hs_b[layer_idx])
            cosines.append(cos)
        pair_cosines.append(cosines)

        if (idx + 1) % 10 == 0 or idx == 0:
            print(f"  ペア {idx + 1}/{len(data)}: {dp.pair_id} "
                  f"(CCL sim={dp.ccl_similarity:.3f})")

    result = CoTResult(
        condition=cot_mode,
        condition_code=condition_code,
        model_key=model_key,
        n_pairs=len(data),
        n_layers=n_layers,
        pair_cosines=pair_cosines,
    )
    return result


# PURPOSE: 層別 Spearman ρ を計算
def compute_rhos(
    result: CoTResult,
    data: list[ProbeDataPoint],
) -> CoTResult:
    """CoTResult に層別 ρ と偏相関 ρ を計算して追加。"""
    from scipy import stats
    from scipy.stats import rankdata

    ccl_sims = [d.ccl_similarity for d in data]
    length_sims = [d.length_similarity for d in data]

    best_rho = -1.0
    best_rho_layer = -1
    best_partial = -1.0
    best_partial_layer = -1

    for layer_idx in range(result.n_layers + 1):
        # 各ペアのこの層での cosine を集める
        cosines = [result.pair_cosines[i][layer_idx]
                   for i in range(len(result.pair_cosines))
                   if layer_idx < len(result.pair_cosines[i])]

        if len(cosines) != len(ccl_sims):
            result.layer_rhos.append(0.0)
            result.layer_partial_rhos.append(0.0)
            continue

        # Spearman ρ
        try:
            rho, _ = stats.spearmanr(cosines, ccl_sims)
        except Exception:
            rho = 0.0
        result.layer_rhos.append(float(rho))

        if rho > best_rho:
            best_rho = rho
            best_rho_layer = layer_idx

        # 偏相関 ρ (コード長制御)
        r_x = rankdata(cosines)
        r_y = rankdata(ccl_sims)
        r_z = rankdata(length_sims)

        r_xy = np.corrcoef(r_x, r_y)[0, 1]
        r_xz = np.corrcoef(r_x, r_z)[0, 1]
        r_yz = np.corrcoef(r_y, r_z)[0, 1]

        denom = math.sqrt((1 - r_xz**2) * (1 - r_yz**2))
        partial_rho = (r_xy - r_xz * r_yz) / denom if denom > 0 else 0.0
        result.layer_partial_rhos.append(float(partial_rho))

        if partial_rho > best_partial:
            best_partial = partial_rho
            best_partial_layer = layer_idx

    result.best_rho = best_rho
    result.best_rho_layer = best_rho_layer
    result.best_partial_rho = best_partial
    result.best_partial_layer = best_partial_layer

    return result


# ============================================================
# 統計分析: 条件間比較
# ============================================================

# PURPOSE: paired permutation test
def paired_permutation_test(
    cosines_c0: list[list[float]],
    cosines_c1: list[list[float]],
    ccl_sims: list[float],
    layer_idx: int,
    n_permutations: int = 10000,
    seed: int = 42,
) -> dict:
    """ペア対応付き置換検定で Δρ の有意性を検証。

    各ペアについて C0 と C1 の cosine を入れ替え、
    シャッフル後の ρ 差の分布から p 値を推定する。
    """
    from scipy import stats
    rng = np.random.RandomState(seed)

    n_pairs = len(cosines_c0)
    cos_0 = np.array([cosines_c0[i][layer_idx] for i in range(n_pairs)])
    cos_1 = np.array([cosines_c1[i][layer_idx] for i in range(n_pairs)])
    ccl = np.array(ccl_sims)

    # 実測 Δρ
    rho_0, _ = stats.spearmanr(cos_0, ccl)
    rho_1, _ = stats.spearmanr(cos_1, ccl)
    observed_delta = rho_1 - rho_0

    # 置換検定
    count_ge = 0
    for _ in range(n_permutations):
        # 各ペアで 50% の確率で C0/C1 を入れ替え
        swap = rng.randint(0, 2, size=n_pairs).astype(bool)
        perm_0 = np.where(swap, cos_1, cos_0)
        perm_1 = np.where(swap, cos_0, cos_1)

        r0, _ = stats.spearmanr(perm_0, ccl)
        r1, _ = stats.spearmanr(perm_1, ccl)
        if (r1 - r0) >= observed_delta:
            count_ge += 1

    p_value = (count_ge + 1) / (n_permutations + 1)

    return {
        "layer": layer_idx,
        "rho_C0": float(rho_0),
        "rho_C1": float(rho_1),
        "delta_rho": float(observed_delta),
        "p_value": float(p_value),
        "n_permutations": n_permutations,
    }


# PURPOSE: ブートストラップ信頼区間
def bootstrap_ci(
    cosines_c0: list[list[float]],
    cosines_c1: list[list[float]],
    ccl_sims: list[float],
    layer_idx: int,
    n_bootstrap: int = 10000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    """Δρ のブートストラップ信頼区間を計算。"""
    from scipy import stats
    rng = np.random.RandomState(seed)

    n_pairs = len(cosines_c0)
    cos_0 = np.array([cosines_c0[i][layer_idx] for i in range(n_pairs)])
    cos_1 = np.array([cosines_c1[i][layer_idx] for i in range(n_pairs)])
    ccl = np.array(ccl_sims)

    deltas = []
    for _ in range(n_bootstrap):
        idx = rng.choice(n_pairs, size=n_pairs, replace=True)
        r0, _ = stats.spearmanr(cos_0[idx], ccl[idx])
        r1, _ = stats.spearmanr(cos_1[idx], ccl[idx])
        deltas.append(r1 - r0)

    deltas = np.array(deltas)
    ci_low = np.percentile(deltas, 100 * alpha / 2)
    ci_high = np.percentile(deltas, 100 * (1 - alpha / 2))

    return {
        "layer": layer_idx,
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "ci_alpha": alpha,
        "mean_delta": float(np.mean(deltas)),
        "std_delta": float(np.std(deltas)),
        "n_bootstrap": n_bootstrap,
    }


# PURPOSE: Cohen's d (効果量)
def cohens_d(x: np.ndarray, y: np.ndarray) -> float:
    """対応ありの Cohen's d (差の平均 / 差の標準偏差)。"""
    diff = x - y
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    if std_diff == 0:
        return 0.0
    return float(mean_diff / std_diff)


# PURPOSE: 全条件間の統計比較
def analyze_cot_results(
    results: dict[str, CoTResult],
    data: list[ProbeDataPoint],
) -> dict:
    """3条件の結果を統計的に比較する。"""
    from scipy import stats

    ccl_sims = [d.ccl_similarity for d in data]
    n_layers = list(results.values())[0].n_layers

    analysis = {
        "comparisons": [],
        "per_layer": [],
        "judgment": {},
    }

    # 比較ペア: C1 vs C0, C2 vs C0
    comparisons = [
        ("structure", "bare", "C1 vs C0"),
        ("step", "bare", "C2 vs C0"),
    ]

    # Bonferroni 補正の閾値
    alpha_bonf = 0.05 / len(comparisons)

    print(f"\n{'='*70}")
    print("  H1 CoT 実験: 条件間比較")
    print(f"{'='*70}")

    for cond_test, cond_base, label in comparisons:
        res_test = results[cond_test]
        res_base = results[cond_base]

        print(f"\n  --- {label} ---")
        print(f"  {'層':>4} | {'ρ(base)':>8} | {'ρ(test)':>8} | "
              f"{'Δρ':>8} | {'p値':>10} | {'Cohen d':>8} | {'判定':>6}")
        print(f"  {'-'*4}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}-+-{'-'*10}-+-{'-'*8}-+-{'-'*6}")

        best_delta = -999
        best_delta_layer = -1
        best_delta_p = 1.0

        for layer_idx in range(n_layers + 1):
            # paired permutation test
            perm_result = paired_permutation_test(
                res_base.pair_cosines, res_test.pair_cosines,
                ccl_sims, layer_idx,
            )

            # ブートストラップ CI
            bs_result = bootstrap_ci(
                res_base.pair_cosines, res_test.pair_cosines,
                ccl_sims, layer_idx,
            )

            # Cohen's d (各ペアの cosine 差)
            cos_base = np.array([res_base.pair_cosines[i][layer_idx]
                                for i in range(len(data))])
            cos_test = np.array([res_test.pair_cosines[i][layer_idx]
                                for i in range(len(data))])
            d = cohens_d(cos_test, cos_base)

            delta = perm_result["delta_rho"]
            p = perm_result["p_value"]

            sig = "✅" if p < alpha_bonf and delta > 0 else "  "
            print(f"  {layer_idx:4d} | {perm_result['rho_C0']:8.4f} | "
                  f"{perm_result['rho_C1']:8.4f} | {delta:+8.4f} | "
                  f"{p:10.4f} | {d:+8.4f} | {sig}")

            if delta > best_delta:
                best_delta = delta
                best_delta_layer = layer_idx
                best_delta_p = p

            analysis["per_layer"].append({
                "comparison": label,
                "layer": layer_idx,
                **perm_result,
                **bs_result,
                "cohens_d": d,
            })

        # 判定 (VISION §8.3H 基準)
        d_best = cohens_d(
            np.array([res_test.pair_cosines[i][best_delta_layer]
                      for i in range(len(data))]),
            np.array([res_base.pair_cosines[i][best_delta_layer]
                      for i in range(len(data))]),
        )

        if best_delta > 0 and best_delta_p < alpha_bonf and abs(d_best) > 0.3:
            judgment = "Ship"
        elif best_delta > 0 and best_delta_p < 0.05 and abs(d_best) < 0.3:
            judgment = "Extend"
        elif abs(best_delta) < 0.05:
            judgment = "Stop"
        else:
            judgment = "Don't Ship"

        comp_summary = {
            "comparison": label,
            "best_delta_rho": float(best_delta),
            "best_delta_layer": best_delta_layer,
            "best_p_value": float(best_delta_p),
            "best_cohens_d": float(d_best),
            "judgment": judgment,
        }
        analysis["comparisons"].append(comp_summary)

        print(f"\n  📊 {label}: best Δρ = {best_delta:+.4f} @ Layer {best_delta_layer}")
        print(f"     p = {best_delta_p:.4f}, d = {d_best:+.4f}")
        print(f"     判定: {judgment}")

    # 総合判定
    c1_comp = analysis["comparisons"][0]
    if c1_comp["judgment"] == "Ship":
        overall = "H1 支持: CoT は ρ を有意に増加させる"
    elif c1_comp["judgment"] == "Extend":
        overall = "H1 弱い支持: P3b で追試が必要"
    elif c1_comp["judgment"] == "Stop":
        overall = "H1 不支持: CoT は ρ に影響しない"
    else:
        overall = "H1 反証: CoT は ρ を減少させる → T21 予測の修正が必要"

    analysis["judgment"] = {
        "overall": overall,
        "c1_vs_c0": c1_comp,
        "bonferroni_alpha": float(alpha_bonf),
    }

    print(f"\n{'='*70}")
    print(f"  総合判定: {overall}")
    print(f"{'='*70}")

    return analysis


# ============================================================
# 結果保存
# ============================================================

# PURPOSE: CoT 実験結果を保存
def save_cot_results(
    condition_results: dict[str, CoTResult],
    analysis: dict,
    model_key: str,
    data_source: str = "p3a",
):
    """CoT 実験結果を JSON に保存。"""
    output = {
        "experiment": "H1_CoT",
        "model": model_key,
        "data_source": data_source,
        "conditions": {},
        "analysis": analysis,
    }

    for cond_name, res in condition_results.items():
        output["conditions"][cond_name] = {
            "condition_code": res.condition_code,
            "n_pairs": res.n_pairs,
            "n_layers": res.n_layers,
            "best_rho": res.best_rho,
            "best_rho_layer": res.best_rho_layer,
            "best_partial_rho": res.best_partial_rho,
            "best_partial_layer": res.best_partial_layer,
            "layer_rhos": res.layer_rhos,
            "layer_partial_rhos": res.layer_partial_rhos,
            "pair_cosines": res.pair_cosines,
        }

    suffix = f"_{data_source}" if data_source != "p3a" else ""
    out_path = _SCRIPT_DIR / f"phase_b_cot_{model_key}{suffix}.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, cls=_NumpyEncoder)
    print(f"\n💾 結果保存: {out_path}")
    return out_path


# ============================================================
# Dry-run: プロンプト確認
# ============================================================

# PURPOSE: dry-run でプロンプト確認
def dry_run(data: list[ProbeDataPoint]):
    """各条件のプロンプトを表示して確認。"""
    print(f"\n{'='*60}")
    print("  Dry-Run: CoT プロンプト確認")
    print(f"{'='*60}")

    # P3a の場合は p3_benchmark から取得
    from p3_benchmark import create_benchmark_pairs
    raw_pairs = create_benchmark_pairs()

    sample_code = ""
    if data[0].code_a:
        sample_code = data[0].code_a
    elif raw_pairs:
        sample_code = raw_pairs[0].func_a_source

    for mode in ["bare", "structure", "step"]:
        prompt = generate_cot_prompt(sample_code, mode)
        print(f"\n  --- {COT_CONDITIONS[mode]}: {mode} ---")
        print(f"  トークン推定: ~{len(prompt.split())} tokens")
        print(f"  先頭 200 文字:")
        print(f"    {prompt[:200]}...")
        print(f"  末尾 100 文字:")
        print(f"    ...{prompt[-100:]}")

    print(f"\n  データ: {len(data)} ペア")
    print(f"  正例: {sum(1 for d in data if d.is_positive)}")
    print(f"  負例: {sum(1 for d in data if not d.is_positive)}")


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="H1 実験: CoT Prompting → ρ 増加の検証"
    )
    parser.add_argument(
        "--model", type=str, default="codebert",
        choices=list(MODEL_CONFIGS.keys()),
        help="使用するモデル (default: codebert)",
    )
    parser.add_argument(
        "--bits", type=int, default=0,
        help="量子化ビット数 (0=デフォルト, 4=4bit, 8=8bit)",
    )
    parser.add_argument(
        "--cot", type=str, default="all",
        choices=["bare", "structure", "step", "all"],
        help="実行する CoT 条件 (default: all)",
    )
    parser.add_argument(
        "--data", type=str, default="p3a",
        choices=["p3a", "p3b"],
        help="データソース (default: p3a)",
    )
    parser.add_argument(
        "--max-pairs", type=int, default=0,
        help="最大ペア数 (0=全ペア)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="データとプロンプトの確認のみ (モデルロードなし)",
    )
    parser.add_argument(
        "--max-length", type=int, default=512,
        help="トークナイザーの最大長 (default: 512)",
    )
    args = parser.parse_args()

    # --- データ準備 ---
    print(f"📋 データ準備: {args.data}")
    if args.data == "p3a":
        data = prepare_data(max_pairs=args.max_pairs)
    else:
        data = prepare_data_p3b(max_pairs=args.max_pairs or 60)

    print(f"  ペア数: {len(data)}")

    # --- Dry-run ---
    if args.dry_run:
        dry_run(data)
        return

    # --- モデルロード ---
    model, tokenizer, device, n_layers = load_model(args.model, bits=args.bits)

    # --- 実行する条件を決定 ---
    if args.cot == "all":
        conditions = ["bare", "structure", "step"]
    else:
        conditions = [args.cot]

    # ベースライン (C0) は常に含める
    if "bare" not in conditions:
        conditions = ["bare"] + conditions

    # --- 各条件で hidden state 抽出 + cosine 計算 ---
    condition_results = {}
    for cond in conditions:
        result = run_condition(
            data, model, tokenizer, device, n_layers,
            cot_mode=cond,
            model_key=args.model,
            max_length=args.max_length,
        )
        result = compute_rhos(result, data)
        condition_results[cond] = result

        print(f"\n  {COT_CONDITIONS[cond]}: best ρ = {result.best_rho:.4f} "
              f"@ Layer {result.best_rho_layer}")
        print(f"  {COT_CONDITIONS[cond]}: best 偏ρ = {result.best_partial_rho:.4f} "
              f"@ Layer {result.best_partial_layer}")

    # --- 統計分析 ---
    if len(condition_results) >= 2 and "bare" in condition_results:
        analysis = analyze_cot_results(condition_results, data)
    else:
        analysis = {"note": "比較には bare 条件が必要"}

    # --- 結果保存 ---
    save_cot_results(condition_results, analysis, args.model, args.data)


if __name__ == "__main__":
    main()
