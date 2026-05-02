#!/usr/bin/env python3
# PROOF: [L3/実験] <- 60_実験|Peira/E1_FormalPrompt→CCL形式プロンプトがρに与える影響
"""
E1 実験: Formal Structural Prompt → ρ 変化の検証

背景:
  Phase B CoT 実験 (cot_experiment.py) で、natural-language CoT は
  構造プロービングの ρ を改善しない（むしろ劣化: partial ρ 0.249→0.203）ことが判明。
  
  理論的予測: recovery functor N は verbal CoT ではなく compositional constraints
  を通じて動作する → formal structural prompt は質的に異なるプロンプトクラス。

仮説:
  H0_E1: Δρ_formal = ρ(CCL) − ρ(bare) ≤ 0
  H1_E1: Δρ_formal > 0 (片側検定)

5条件の被験者内設計:
  C0: Bare             — コードのみ (既存ベースライン)
  C1: CoT-structure    — "describe the structure" (既存比較対象)
  C3: CCL-annotated    — CCL 式をコメントとして付与
  C4: CCL-workflow     — CCL パイプライン表記を付与
  C5: Category-formal  — 圏論的記法 (関手・射) で構造を記述

  ※ C2 (step-by-step) は既存データで ρ 劣化が確認済み → 省略

用量反応仮説 (E3 で本格検証、ここでは予備的):
  ρ(C0) ≈ ρ(C1) < ρ(C3) ≤ ρ(C4) ≤ ρ(C5)
  → structural compression が高いほど ρ が向上する

Usage:
  python e1_formal_prompt_experiment.py --dry-run --model codellama --bits 4
  python e1_formal_prompt_experiment.py --model codellama --bits 4 --conditions all
  python e1_formal_prompt_experiment.py --model codellama --bits 4 --conditions ccl_annotated
"""

# PURPOSE: E1 Formal Structural Prompt 実験パイプライン

import sys
import json
import argparse
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# mekhane パスの解決
_SCRIPT_DIR = Path(__file__).parent
_HGK_ROOT = _SCRIPT_DIR.parents[1]  # Peira → HGK ルート
_MEKHANE_SRC = _HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"
_LETHE_DIR = _HGK_ROOT / "10_知性｜Nous" / "04_企画｜Boulēsis" / "14_忘却｜Lethe"
_LETHE_EXPERIMENTS = _LETHE_DIR / "experiments"

if _MEKHANE_SRC.exists():
    sys.path.insert(0, str(_MEKHANE_SRC))
if _LETHE_EXPERIMENTS.exists():
    sys.path.insert(0, str(_LETHE_EXPERIMENTS))

import numpy as np

# structural_probe.py からのインポート
from structural_probe import (
    prepare_data,
    prepare_data_p3b,
    load_model,
    extract_hidden_states,
    cosine_similarity,
    code_to_ccl,
    multivariate_partial_correlation,
    ProbeDataPoint,
    MODEL_CONFIGS,
    _NumpyEncoder,
)

# cot_experiment.py の統計分析を再利用
from cot_experiment import (
    paired_permutation_test,
    bootstrap_ci,
    cohens_d,
    CoTResult,
    compute_rhos,
)


# ============================================================
# E1 プロンプトテンプレート
# ============================================================

def _generate_ccl_annotation(code: str) -> str:
    """コードから CCL 式を生成し、アノテーションとして付与する。
    
    code_to_ccl が利用可能ならそれを使い、利用できなければ
    ヒューリスティクスでコード構造から CCL を推定する。
    """
    try:
        ccl_expr = code_to_ccl(code)
        if ccl_expr and len(ccl_expr) > 2:
            return ccl_expr
    except Exception:
        pass
    
    # フォールバック: コード構造からヒューリスティック CCL
    lines = code.strip().split('\n')
    has_loop = any(l.strip().startswith(('for ', 'while ')) for l in lines)
    has_cond = any(l.strip().startswith(('if ', 'elif ', 'else:')) for l in lines)
    has_func = any(l.strip().startswith(('def ', 'class ')) for l in lines)
    has_return = any('return ' in l for l in lines)
    
    parts = []
    if has_func:
        parts.append('/noe')
    if has_cond:
        parts.append('/ske')
    if has_loop:
        parts.append('/pei')
    if has_return:
        parts.append('/ene')
    
    return '>'.join(parts) if parts else '/tek'


def _generate_ccl_workflow(code: str) -> str:
    """コードから CCL ワークフロー表記を生成する。
    
    より構造化された表現: 関数→分岐→反復→出力 のパイプラインとして記述する。
    """
    lines = code.strip().split('\n')
    n_lines = len(lines)
    
    # コード構造の特徴を抽出
    funcs = [l.strip() for l in lines if l.strip().startswith('def ')]
    classes = [l.strip() for l in lines if l.strip().startswith('class ')]
    loops = sum(1 for l in lines if l.strip().startswith(('for ', 'while ')))
    conds = sum(1 for l in lines if l.strip().startswith(('if ', 'elif ')))
    returns = sum(1 for l in lines if 'return ' in l)
    assigns = sum(1 for l in lines if '=' in l and not l.strip().startswith(('#', 'if', 'elif', 'for', 'while', 'def', 'class')))
    
    # CCL ワークフロー構造
    parts = []
    
    # 入力層 (関数定義)
    if classes:
        parts.append(f'/arc{{class×{len(classes)}}}')
    if funcs:
        parts.append(f'/noe{{def×{len(funcs)}}}')
    
    # 処理層 (制御フロー)
    if conds > 0:
        parts.append(f'/ske{{cond×{conds}}}')
    if loops > 0:
        parts.append(f'F:[×{loops}]{{/pei}}')
    if assigns > 2:
        parts.append(f'/tek{{assign×{assigns}}}')
    
    # 出力層
    if returns > 0:
        parts.append(f'/ene{{return×{returns}}}')
    
    if not parts:
        parts = [f'/tek{{lines={n_lines}}}']
    
    return '_'.join(parts)


def _generate_categorical_formal(code: str) -> str:
    """コードから圏論的記法を生成する。
    
    関手・射による構造記述:
    - 関数 = 射 (morphism)
    - クラス = 対象 (object) 間の関手 (functor)
    - 制御フロー = 自然変換 (natural transformation)
    """
    lines = code.strip().split('\n')
    n_lines = len(lines)
    
    funcs = [l.strip().split('def ')[1].split('(')[0] 
             for l in lines if l.strip().startswith('def ')]
    classes = [l.strip().split('class ')[1].split('(')[0].split(':')[0]
               for l in lines if l.strip().startswith('class ')]
    has_loop = any(l.strip().startswith(('for ', 'while ')) for l in lines)
    has_cond = any(l.strip().startswith(('if ', 'elif ')) for l in lines)
    
    parts = []
    
    # 対象と射の記述
    if classes:
        for cls in classes[:3]:
            parts.append(f'Ob({cls})')
    
    if funcs:
        for func in funcs[:5]:
            parts.append(f'Hom(A,B):{func}')
    elif n_lines > 0:
        parts.append(f'Hom(In,Out):program')
    
    # 構造的特徴
    if has_cond:
        parts.append('η:A⇒B (branch)')
    if has_loop:
        parts.append('F:C→C (endofunctor)')
    
    # 合成
    if len(funcs) > 1:
        composition = ' ∘ '.join(funcs[:3])
        parts.append(f'composition: {composition}')
    
    return ' | '.join(parts) if parts else f'Hom(In,Out):atomic[{n_lines}L]'


# プロンプトテンプレート (5条件)
E1_TEMPLATES = {
    # C0: ベースライン — コードのみ
    "bare": None,

    # C1: 構造分析特化 CoT (既存比較対象、cot_experiment.py と同一)
    "structure": (
        "# Analyze the structural pattern of this code:\n"
        "{code}\n"
        "# Structural analysis: This code uses"
    ),

    # C3: CCL アノテーション付き
    "ccl_annotated": (
        "# CCL structural annotation: {ccl_annotation}\n"
        "{code}"
    ),

    # C4: CCL ワークフロー表記
    "ccl_workflow": (
        "# Cognitive workflow:\n"
        "# Pipeline: {ccl_workflow}\n"
        "# Structural depth: {structural_depth}\n"
        "{code}"
    ),

    # C5: 圏論的形式記法
    "category_formal": (
        "# Category-theoretic structure:\n"
        "# {categorical_formal}\n"
        "# Forgetful functor: U(structure) → |code|\n"
        "{code}"
    ),
}

# 条件コード
E1_CONDITIONS = {
    "bare": "C0",
    "structure": "C1",
    "ccl_annotated": "C3",
    "ccl_workflow": "C4",
    "category_formal": "C5",
}


# PURPOSE: E1 formal prompt を生成
def generate_e1_prompt(code: str, mode: str) -> str:
    """コードに E1 formal prompt を付加する。

    Args:
        code: Python コードスニペット
        mode: "bare" / "structure" / "ccl_annotated" / "ccl_workflow" / "category_formal"
    Returns:
        プロンプト付きコード
    """
    template = E1_TEMPLATES.get(mode)
    if template is None:
        return code
    
    if mode == "structure":
        return template.format(code=code)
    
    elif mode == "ccl_annotated":
        ccl = _generate_ccl_annotation(code)
        return template.format(code=code, ccl_annotation=ccl)
    
    elif mode == "ccl_workflow":
        wf = _generate_ccl_workflow(code)
        lines = code.strip().split('\n')
        depth = sum(1 for l in lines if l.strip().startswith(
            ('def ', 'class ', 'for ', 'while ', 'if ', 'elif ', 'try:', 'with ')))
        return template.format(
            code=code, ccl_workflow=wf, structural_depth=depth)
    
    elif mode == "category_formal":
        cat = _generate_categorical_formal(code)
        return template.format(code=code, categorical_formal=cat)
    
    return code


# ============================================================
# メインパイプライン
# ============================================================

# PURPOSE: 1条件の hidden state 抽出 + cosine 計算
def run_e1_condition(
    data: list,
    model, tokenizer, device,
    n_layers: int,
    condition: str,
    model_key: str,
    max_length: int = 512,
) -> CoTResult:
    """1つの E1 条件で全ペアの hidden state を抽出し cosine を計算。"""
    condition_code = E1_CONDITIONS[condition]
    print(f"\n{'='*60}")
    print(f"  E1 条件: {condition_code} ({condition})")
    print(f"{'='*60}")

    # P3a の場合: p3_benchmark から取得
    from p3_benchmark import create_benchmark_pairs
    raw_pairs = create_benchmark_pairs()

    pair_cosines = []
    for idx, dp in enumerate(data):
        # コード取得
        code_a = dp.code_a if dp.code_a else ""
        code_b = dp.code_b if dp.code_b else ""
        
        if not code_a.strip() and idx < len(raw_pairs):
            code_a = raw_pairs[idx].func_a_source
            code_b = raw_pairs[idx].func_b_source

        # E1 プロンプト生成
        prompt_a = generate_e1_prompt(code_a, condition)
        prompt_b = generate_e1_prompt(code_b, condition)

        # Hidden state 抽出
        hs_a = extract_hidden_states(prompt_a, model, tokenizer, device, max_length)
        hs_b = extract_hidden_states(prompt_b, model, tokenizer, device, max_length)

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
        condition=condition,
        condition_code=condition_code,
        model_key=model_key,
        n_pairs=len(data),
        n_layers=n_layers,
        pair_cosines=pair_cosines,
    )
    return result


# PURPOSE: 全条件間の統計比較 (cot_experiment.py の拡張版)
def analyze_e1_results(
    results: dict,
    data: list,
) -> dict:
    """E1 の全条件結果を統計的に比較する。"""
    from scipy import stats

    ccl_sims = [d.ccl_similarity for d in data]
    n_layers = list(results.values())[0].n_layers

    analysis = {
        "comparisons": [],
        "per_layer": [],
        "judgment": {},
        "dose_response": {},  # 予備的用量反応分析
    }

    # 比較ペア: 各条件 vs bare
    comparisons = []
    for cond_name in results:
        if cond_name != "bare":
            code = E1_CONDITIONS[cond_name]
            comparisons.append((cond_name, "bare", f"{code} vs C0"))

    # Bonferroni 補正
    alpha_bonf = 0.05 / max(len(comparisons), 1)

    print(f"\n{'='*70}")
    print("  E1 実験: Formal Structural Prompt 条件間比較")
    print(f"{'='*70}")

    for cond_test, cond_base, label in comparisons:
        res_test = results[cond_test]
        res_base = results[cond_base]

        print(f"\n  --- {label} ---")
        print(f"  {'層':>4} | {'ρ(bare)':>8} | {'ρ(test)':>8} | "
              f"{'Δρ':>8} | {'p値':>10} | {'Cohen d':>8} | {'判定':>6}")
        print(f"  {'-'*4}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}-+-{'-'*10}-+-{'-'*8}-+-{'-'*6}")

        best_delta = -999
        best_delta_layer = -1
        best_delta_p = 1.0

        for layer_idx in range(n_layers + 1):
            perm_result = paired_permutation_test(
                res_base.pair_cosines, res_test.pair_cosines,
                ccl_sims, layer_idx,
            )
            bs_result = bootstrap_ci(
                res_base.pair_cosines, res_test.pair_cosines,
                ccl_sims, layer_idx,
            )

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

        # 判定
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

    # 用量反応分析 (予備的)
    structural_compression_order = ["bare", "structure", "ccl_annotated", "ccl_workflow", "category_formal"]
    available = [c for c in structural_compression_order if c in results]
    
    if len(available) >= 3:
        best_rhos = []
        for cond in available:
            best_rhos.append(results[cond].best_partial_rho)
        
        # 単調性チェック
        monotonic = all(best_rhos[i] <= best_rhos[i+1] for i in range(len(best_rhos)-1))
        correlation, p_val = stats.spearmanr(range(len(best_rhos)), best_rhos)
        
        analysis["dose_response"] = {
            "order": available,
            "best_partial_rhos": best_rhos,
            "monotonic": monotonic,
            "spearman_r": float(correlation),
            "spearman_p": float(p_val),
        }
        
        print(f"\n  📈 用量反応 (予備的):")
        for cond, rho in zip(available, best_rhos):
            print(f"    {cond:20s}: partial ρ = {rho:.4f}")
        print(f"    Spearman r = {correlation:.4f}, p = {p_val:.4f}")
        print(f"    単調性: {'✅' if monotonic else '❌'}")

    # 総合判定
    formal_comps = [c for c in analysis["comparisons"] 
                    if "C3" in c["comparison"] or "C4" in c["comparison"] or "C5" in c["comparison"]]
    
    if any(c["judgment"] == "Ship" for c in formal_comps):
        overall = "H1_E1 支持: Formal prompt は ρ を有意に増加させる"
    elif any(c["judgment"] == "Extend" for c in formal_comps):
        overall = "H1_E1 弱い支持: 効果あるがサンプル追加が必要"
    elif all(c["judgment"] == "Stop" for c in formal_comps):
        overall = "H1_E1 不支持: Formal prompt も ρ に影響しない → recovery functor N は prompt 非依存"
    else:
        overall = "H1_E1 反証: Formal prompt は ρ を減少させる"

    analysis["judgment"] = {
        "overall": overall,
        "bonferroni_alpha": float(alpha_bonf),
        "formal_conditions": [c for c in formal_comps],
    }

    print(f"\n{'='*70}")
    print(f"  総合判定: {overall}")
    print(f"{'='*70}")

    return analysis


# PURPOSE: 結果保存
def save_e1_results(
    condition_results: dict,
    analysis: dict,
    model_key: str,
    data_source: str = "p3a",
):
    """E1 実験結果を JSON に保存。"""
    output = {
        "experiment": "E1_FormalPrompt",
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
    out_path = _SCRIPT_DIR / f"e1_formal_prompt_{model_key}{suffix}.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, cls=_NumpyEncoder)
    print(f"\n💾 結果保存: {out_path}")
    return out_path


# PURPOSE: Dry-run でプロンプト確認
def dry_run(data: list):
    """各条件のプロンプトを表示して確認。"""
    print(f"\n{'='*60}")
    print("  E1 Dry-Run: Formal Prompt 確認")
    print(f"{'='*60}")

    from p3_benchmark import create_benchmark_pairs
    raw_pairs = create_benchmark_pairs()

    sample_code = ""
    if data[0].code_a:
        sample_code = data[0].code_a
    elif raw_pairs:
        sample_code = raw_pairs[0].func_a_source

    for mode in E1_CONDITIONS:
        prompt = generate_e1_prompt(sample_code, mode)
        print(f"\n  --- {E1_CONDITIONS[mode]}: {mode} ---")
        print(f"  トークン推定: ~{len(prompt.split())} words")
        print(f"  プロンプト全文 (先頭 500文字):")
        print(f"    {prompt[:500]}")
        if len(prompt) > 500:
            print(f"    ... ({len(prompt) - 500} 文字省略)")
        print()

    print(f"  データ: {len(data)} ペア")
    print(f"  正例: {sum(1 for d in data if d.is_positive)}")
    print(f"  負例: {sum(1 for d in data if not d.is_positive)}")


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="E1 実験: Formal Structural Prompt → ρ 変化の検証"
    )
    parser.add_argument(
        "--model", type=str, default="codellama",
        choices=list(MODEL_CONFIGS.keys()),
        help="使用するモデル (default: codellama)",
    )
    parser.add_argument(
        "--bits", type=int, default=4,
        help="量子化ビット数 (0=デフォルト, 4=4bit, 8=8bit)",
    )
    parser.add_argument(
        "--conditions", type=str, default="all",
        choices=["bare", "structure", "ccl_annotated", "ccl_workflow", 
                 "category_formal", "all", "formal_only"],
        help="実行条件 (default: all, formal_only=C3+C4+C5のみ)",
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
        help="データとプロンプトの確認のみ",
    )
    parser.add_argument(
        "--max-length", type=int, default=512,
        help="トークナイザーの最大長 (default: 512)",
    )
    args = parser.parse_args()

    # --- データ準備 ---
    print(f"📋 E1 データ準備: {args.data}")
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

    # --- 実行条件の決定 ---
    if args.conditions == "all":
        conditions = ["bare", "structure", "ccl_annotated", "ccl_workflow", "category_formal"]
    elif args.conditions == "formal_only":
        conditions = ["bare", "ccl_annotated", "ccl_workflow", "category_formal"]
    else:
        conditions = [args.conditions]

    # bare は常に含める
    if "bare" not in conditions:
        conditions = ["bare"] + conditions

    # --- 各条件で実行 ---
    condition_results = {}
    for cond in conditions:
        result = run_e1_condition(
            data, model, tokenizer, device, n_layers,
            condition=cond,
            model_key=args.model,
            max_length=args.max_length,
        )
        result = compute_rhos(result, data)
        condition_results[cond] = result

        print(f"\n  {E1_CONDITIONS[cond]}: best ρ = {result.best_rho:.4f} "
              f"@ Layer {result.best_rho_layer}")
        print(f"  {E1_CONDITIONS[cond]}: best 偏ρ = {result.best_partial_rho:.4f} "
              f"@ Layer {result.best_partial_layer}")

    # --- 統計分析 ---
    if len(condition_results) >= 2 and "bare" in condition_results:
        analysis = analyze_e1_results(condition_results, data)
    else:
        analysis = {"note": "bare 条件が必要"}

    # --- 結果保存 ---
    save_e1_results(condition_results, analysis, args.model, args.data)


if __name__ == "__main__":
    main()
