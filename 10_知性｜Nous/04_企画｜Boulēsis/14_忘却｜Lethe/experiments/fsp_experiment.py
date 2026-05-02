#!/usr/bin/env python3
# PROOF: [L2/実験] <- 60_実験｜Peira/07_CCL-PL A0→Phase B-FSP→形式的構造プロンプトがρに与える影響
"""
H_FSP 実験: Formal Structural Prompts → ρ 変化の検証

§7.1.2 の CoT probing で自然言語 CoT は hidden states の構造信号を改善しないことを確認。
本実験は「形式的構造プロンプト」が質的に異なる効果を持つかを検証する。

4条件の被験者内設計:
  C0: Bare        — コードのみ (ベースライン, CoT 実験と同一)
  C_AST: AST-seq  — コード + AST ノード型シーケンス
  C_SIG: Sig      — コード + 関数シグネチャ注釈 (型・計算量)
  C_CCL_OTHER:    — コード + 別のコードの CCL 式 (シャッフル control)

データリーク対策:
  CCL 式は ground truth (ρ 計算用) にのみ使用。
  入力プロンプトには CCL 式を含めない (Shadow Gemini 反証に基づく設計)。
  C_CCL_OTHER は CCL フォーマット自体の影響を測定する control 条件。

主要仮説:
  H0: ρ(C_AST) ≈ ρ(C_SIG) ≈ ρ(C0) (形式プロンプトは構造信号に影響しない)
  H_FSP: ρ(C_AST or C_SIG) > ρ(C0) (形式プロンプトは構造信号を改善する)

Usage:
  python fsp_experiment.py --dry-run --model codellama --bits 4     # プロンプト確認
  python fsp_experiment.py --model codellama --bits 4 --cond all    # 全条件実行
  python fsp_experiment.py --model codellama --bits 4 --cond C_AST  # 個別条件
"""

# PURPOSE: H_FSP 形式的構造プロンプト実験パイプライン

import sys
import ast
import json
import argparse
import math
import textwrap
import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# パス解決 (ローカル: HGK ルートから mekhane を追加、リモート: 同一ディレクトリなのでスキップ)
_SCRIPT_DIR = Path(__file__).parent
try:
    _HGK_ROOT = _SCRIPT_DIR.parents[3]
    _MEKHANE_SRC = _HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"
    if _MEKHANE_SRC.exists():
        sys.path.insert(0, str(_MEKHANE_SRC))
except (IndexError, OSError):
    # リモート環境: フラットディレクトリなので HGK_ROOT は不要
    _HGK_ROOT = _SCRIPT_DIR

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
    _SCRIPT_DIR as RESULTS_DIR,
)

# cot_experiment.py の統計ユーティリティを再利用
from cot_experiment import (
    paired_permutation_test,
    bootstrap_ci,
    cohens_d,
    CoTResult,
    compute_rhos,
)


# ============================================================
# 形式的構造プロンプト生成
# ============================================================

# PURPOSE: コードから AST 型シーケンスを生成 (中粒度)
def ast_type_sequence(code: str) -> str:
    """Python コードの AST ノード型シーケンスを生成。

    中粒度: ノード型 + アリティ (Call の引数数) + ネスト ({} で表現)。
    変数名・関数名は含めない (データリーク対策)。

    例: FuncDef > Assign > Call(2) > If{Assign, Return} > Return
    """
    try:
        tree = ast.parse(textwrap.dedent(code))
    except SyntaxError:
        return "ParseError"

    def _node_label(node: ast.AST) -> str:
        """ノードの型ラベルを生成。"""
        name = type(node).__name__
        # Call のアリティを付加
        if isinstance(node, ast.Call):
            n_args = len(node.args) + len(node.keywords)
            return f"Call({n_args})"
        # For/While のイテレーション情報
        if isinstance(node, (ast.For, ast.While)):
            n_body = len(node.body)
            return f"{name}[{n_body}]"
        return name

    def _walk_body(nodes: list, depth: int = 0) -> str:
        """ノードリストを走査して型シーケンスを生成。"""
        parts = []
        for node in nodes:
            label = _node_label(node)

            # ネスト構造を持つノード
            children_bodies = []
            if hasattr(node, 'body') and isinstance(node.body, list):
                children_bodies.append(('body', node.body))
            if hasattr(node, 'orelse') and isinstance(node.orelse, list) and node.orelse:
                children_bodies.append(('else', node.orelse))
            if hasattr(node, 'handlers') and isinstance(node.handlers, list):
                children_bodies.append(('except', node.handlers))

            if children_bodies and depth < 3:  # 深度制限
                inner_parts = []
                for _, child_nodes in children_bodies:
                    inner = _walk_body(child_nodes, depth + 1)
                    if inner:
                        inner_parts.append(inner)
                if inner_parts:
                    label = f"{label}{{{', '.join(inner_parts)}}}"

            parts.append(label)

        return " > ".join(parts)

    # Module 直下の定義を走査
    result_parts = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body_seq = _walk_body(node.body)
            result_parts.append(f"FuncDef{{{body_seq}}}")
        elif isinstance(node, ast.ClassDef):
            body_seq = _walk_body(node.body)
            result_parts.append(f"ClassDef{{{body_seq}}}")
        else:
            result_parts.append(_node_label(node))

    return " > ".join(result_parts) if result_parts else "Empty"


# PURPOSE: コードから関数シグネチャ注釈を生成
def function_signature_annotation(code: str) -> str:
    """Python コードから関数の型・構造注釈を生成。

    内容:
    - パラメータ数とデフォルト値の有無
    - return 文の有無・数
    - ループ・条件分岐のネスト深度
    - 推定計算量 (ループ構造から)

    例: params=3(1default), returns=2, loops=1(nested=0), branches=2, complexity~O(n)
    """
    try:
        tree = ast.parse(textwrap.dedent(code))
    except SyntaxError:
        return "params=?, returns=?, complexity=?"

    parts = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # パラメータ情報
            n_params = len(node.args.args)
            n_defaults = len(node.args.defaults)
            parts.append(f"params={n_params}({n_defaults}default)")

            # return 文の数
            n_returns = sum(1 for n in ast.walk(node)
                          if isinstance(n, ast.Return))
            parts.append(f"returns={n_returns}")

            # ループ数 (For + While)
            n_loops = sum(1 for n in ast.walk(node)
                         if isinstance(n, (ast.For, ast.While)))
            # ネストしたループの確認
            n_nested = 0
            for n in ast.walk(node):
                if isinstance(n, (ast.For, ast.While)):
                    inner_loops = sum(1 for nn in ast.walk(n)
                                    if isinstance(nn, (ast.For, ast.While)))
                    n_nested += max(0, inner_loops - 1)
            parts.append(f"loops={n_loops}(nested={n_nested})")

            # 分岐数
            n_branches = sum(1 for n in ast.walk(node)
                           if isinstance(n, (ast.If, ast.IfExp)))
            parts.append(f"branches={n_branches}")

            # 推定計算量
            if n_nested > 0:
                complexity = f"O(n^{n_nested + 1})"
            elif n_loops > 0:
                complexity = "O(n)"
            else:
                complexity = "O(1)"
            parts.append(f"complexity~{complexity}")

            # 1つ目の関数のみ
            break

    return ", ".join(parts) if parts else "no_function"


# ============================================================
# プロンプトテンプレート
# ============================================================

# PURPOSE: 4条件のプロンプト生成
FSP_CONDITIONS = {
    "bare": "C0",
    "ast": "C_AST",
    "sig": "C_SIG",
    "ccl_other": "C_CCL_OTHER",
}


def generate_fsp_prompt(
    code: str,
    mode: str,
    ccl_other: str = "",
) -> str:
    """形式的構造プロンプトを生成。

    Args:
        code: Python コードスニペット
        mode: "bare" / "ast" / "sig" / "ccl_other"
        ccl_other: mode="ccl_other" のとき、付加する別コードの CCL 式
    Returns:
        プロンプト付きコード
    """
    if mode == "bare":
        return code

    if mode == "ast":
        ast_seq = ast_type_sequence(code)
        return (
            f"{code}\n"
            f"# Structure: {ast_seq}\n"
        )

    if mode == "sig":
        sig = function_signature_annotation(code)
        return (
            f"{code}\n"
            f"# Signature: {sig}\n"
        )

    if mode == "ccl_other":
        return (
            f"{code}\n"
            f"# Pattern: {ccl_other}\n"
        )

    raise ValueError(f"未知の条件: {mode}")


# ============================================================
# C_CCL_OTHER 用シャッフル
# ============================================================

# PURPOSE: CCL 式のランダムシャッフルマッピングを生成
def create_ccl_shuffle_map(
    data: list[ProbeDataPoint],
    seed: int = 42,
) -> dict[int, tuple[str, str]]:
    """各ペアに対して、別のペアの CCL 式を割り当てるマッピング。

    Returns:
        {pair_index: (ccl_other_for_a, ccl_other_for_b)}
        事後分析用に元の CCL との距離も記録。
    """
    rng = random.Random(seed)
    n = len(data)

    # 全 CCL 式を収集
    all_ccls_a = [d.ccl_a for d in data]
    all_ccls_b = [d.ccl_b for d in data]

    # シャッフル: 各ペアに別のペアの CCL を割り当て
    # (自分自身にはならないように)
    indices = list(range(n))
    shuffled = indices.copy()
    rng.shuffle(shuffled)

    # デランジュメント (自分と重ならないシャッフル) を試みる
    # 完全なデランジュメントは保証しないが、衝突を修正する
    for i in range(n):
        if shuffled[i] == i:
            # 隣と入れ替え
            j = (i + 1) % n
            shuffled[i], shuffled[j] = shuffled[j], shuffled[i]

    mapping = {}
    for i in range(n):
        j = shuffled[i]
        mapping[i] = (all_ccls_a[j], all_ccls_b[j])

    return mapping


# ============================================================
# メインパイプライン
# ============================================================

# PURPOSE: 1条件の hidden state 抽出 + cosine 計算
def run_fsp_condition(
    data: list[ProbeDataPoint],
    model, tokenizer, device,
    n_layers: int,
    fsp_mode: str,
    model_key: str,
    max_length: int = 512,
    ccl_shuffle_map: dict = None,
) -> CoTResult:
    """1つの FSP 条件で全ペアの hidden state を抽出し cosine を計算。"""
    condition_code = FSP_CONDITIONS[fsp_mode]
    print(f"\n{'='*60}")
    print(f"  条件: {condition_code} ({fsp_mode})")
    print(f"{'='*60}")

    pair_cosines = []
    for idx, dp in enumerate(data):
        code_a = dp.code_a if dp.code_a else ""
        code_b = dp.code_b if dp.code_b else ""

        # P3a フォールバック
        if not code_a.strip():
            from p3_benchmark import create_benchmark_pairs
            raw_pairs = create_benchmark_pairs()
            if idx < len(raw_pairs):
                code_a = raw_pairs[idx].func_a_source
                code_b = raw_pairs[idx].func_b_source

        # FSP プロンプト生成
        if fsp_mode == "ccl_other" and ccl_shuffle_map:
            ccl_a, ccl_b = ccl_shuffle_map.get(idx, ("_", "_"))
            prompt_a = generate_fsp_prompt(code_a, fsp_mode, ccl_other=ccl_a)
            prompt_b = generate_fsp_prompt(code_b, fsp_mode, ccl_other=ccl_b)
        else:
            prompt_a = generate_fsp_prompt(code_a, fsp_mode)
            prompt_b = generate_fsp_prompt(code_b, fsp_mode)

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
        condition=fsp_mode,
        condition_code=condition_code,
        model_key=model_key,
        n_pairs=len(data),
        n_layers=n_layers,
        pair_cosines=pair_cosines,
    )
    return result


# ============================================================
# 統計分析: 条件間比較
# ============================================================

# PURPOSE: 全条件間の統計比較
def analyze_fsp_results(
    results: dict[str, CoTResult],
    data: list[ProbeDataPoint],
) -> dict:
    """4条件の結果を統計的に比較する。"""
    from scipy import stats

    ccl_sims = [d.ccl_similarity for d in data]
    n_layers = list(results.values())[0].n_layers

    analysis = {
        "comparisons": [],
        "per_layer": [],
        "judgment": {},
    }

    # 比較ペア: 各条件 vs C0
    comparisons = [
        ("ast", "bare", "C_AST vs C0"),
        ("sig", "bare", "C_SIG vs C0"),
        ("ccl_other", "bare", "C_CCL_OTHER vs C0"),
    ]

    # Bonferroni 補正
    alpha_bonf = 0.05 / len(comparisons)

    print(f"\n{'='*70}")
    print("  H_FSP 実験: 条件間比較")
    print(f"  Bonferroni α = {alpha_bonf:.4f}")
    print(f"{'='*70}")

    for cond_test, cond_base, label in comparisons:
        if cond_test not in results or cond_base not in results:
            continue

        res_test = results[cond_test]
        res_base = results[cond_base]

        print(f"\n  --- {label} ---")
        print(f"  {'層':>4} | {'ρ(C0)':>8} | {'ρ(test)':>8} | "
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

            # Cohen's d
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
            judgment = "Significant"
        elif best_delta > 0 and best_delta_p < 0.05:
            judgment = "Trend"
        elif abs(best_delta) < 0.05:
            judgment = "No Effect"
        else:
            judgment = "Degradation"

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
    any_significant = any(c["judgment"] == "Significant"
                          for c in analysis["comparisons"])
    any_trend = any(c["judgment"] == "Trend"
                    for c in analysis["comparisons"])

    if any_significant:
        overall = "H_FSP 支持: 形式的構造プロンプトは ρ を有意に改善する"
    elif any_trend:
        overall = "H_FSP 弱い支持: 傾向はあるが Bonferroni 補正後に有意でない"
    else:
        overall = "H_FSP 不支持: 形式的構造プロンプトも hidden states の構造信号に影響しない → 構造信号は pre-training 由来"

    # C_CCL_OTHER の特別分析
    ccl_other_comp = next((c for c in analysis["comparisons"]
                          if "CCL_OTHER" in c["comparison"]), None)
    if ccl_other_comp:
        if ccl_other_comp["judgment"] in ("Significant", "Trend"):
            overall += "\n  → ただし C_CCL_OTHER も効果あり: CCL フォーマット自体が影響する可能性"
        else:
            overall += "\n  → C_CCL_OTHER は効果なし: CCL フォーマット自体は影響しない"

    analysis["judgment"] = {
        "overall": overall,
        "bonferroni_alpha": float(alpha_bonf),
    }

    print(f"\n{'='*70}")
    print(f"  総合判定: {overall}")
    print(f"{'='*70}")

    return analysis


# ============================================================
# 結果保存
# ============================================================

# PURPOSE: FSP 実験結果を保存
def save_fsp_results(
    condition_results: dict[str, CoTResult],
    analysis: dict,
    model_key: str,
    data_source: str = "p3b",
    ccl_shuffle_map: dict = None,
):
    """FSP 実験結果を JSON に保存。"""
    output = {
        "experiment": "H_FSP",
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

    # C_CCL_OTHER のシャッフル距離を記録 (事後分析用)
    if ccl_shuffle_map:
        output["ccl_shuffle_info"] = {
            str(idx): {
                "ccl_other_a": ccl_a[:100],
                "ccl_other_b": ccl_b[:100],
            }
            for idx, (ccl_a, ccl_b) in ccl_shuffle_map.items()
        }

    suffix = f"_{data_source}" if data_source != "p3a" else ""
    out_path = RESULTS_DIR / f"phase_b_fsp_{model_key}{suffix}.json"
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
    print("  Dry-Run: FSP プロンプト確認")
    print(f"{'='*60}")

    # サンプルコードの取得
    sample_code = ""
    if data[0].code_a:
        sample_code = data[0].code_a
    else:
        from p3_benchmark import create_benchmark_pairs
        raw_pairs = create_benchmark_pairs()
        if raw_pairs:
            sample_code = raw_pairs[0].func_a_source

    # C_CCL_OTHER 用のダミー CCL
    dummy_ccl = data[1].ccl_a if len(data) > 1 else "/noe_/bou"

    for mode in ["bare", "ast", "sig", "ccl_other"]:
        if mode == "ccl_other":
            prompt = generate_fsp_prompt(sample_code, mode, ccl_other=dummy_ccl)
        else:
            prompt = generate_fsp_prompt(sample_code, mode)

        cond_code = FSP_CONDITIONS[mode]
        print(f"\n  --- {cond_code}: {mode} ---")
        print(f"  トークン推定: ~{len(prompt.split())} 語 / {len(prompt)} 文字")
        print(f"  プロンプト全文:")
        # 短いのでそのまま表示
        for line in prompt.splitlines():
            print(f"    {line}")

    # AST 型シーケンスのサンプル (5件)
    print(f"\n  --- AST 型シーケンス サンプル (先頭5件) ---")
    for i, d in enumerate(data[:5]):
        code = d.code_a if d.code_a else ""
        if not code:
            from p3_benchmark import create_benchmark_pairs
            raw_pairs = create_benchmark_pairs()
            if i < len(raw_pairs):
                code = raw_pairs[i].func_a_source
        ast_seq = ast_type_sequence(code)
        print(f"    {d.pair_id}: {ast_seq[:120]}")

    # 関数シグネチャのサンプル (5件)
    print(f"\n  --- 関数シグネチャ サンプル (先頭5件) ---")
    for i, d in enumerate(data[:5]):
        code = d.code_a if d.code_a else ""
        if not code:
            from p3_benchmark import create_benchmark_pairs
            raw_pairs = create_benchmark_pairs()
            if i < len(raw_pairs):
                code = raw_pairs[i].func_a_source
        sig = function_signature_annotation(code)
        print(f"    {d.pair_id}: {sig}")

    print(f"\n  データ: {len(data)} ペア")
    print(f"  正例: {sum(1 for d in data if d.is_positive)}")
    print(f"  負例: {sum(1 for d in data if not d.is_positive)}")


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="H_FSP 実験: Formal Structural Prompts → ρ の検証"
    )
    parser.add_argument(
        "--model", type=str, default="codellama",
        choices=list(MODEL_CONFIGS.keys()),
        help="使用するモデル (default: codellama)",
    )
    parser.add_argument(
        "--bits", type=int, default=4,
        help="量子化ビット数 (default: 4)",
    )
    parser.add_argument(
        "--cond", type=str, default="all",
        choices=["bare", "ast", "sig", "ccl_other", "all"],
        help="実行する条件 (default: all)",
    )
    parser.add_argument(
        "--data", type=str, default="p3b",
        choices=["p3a", "p3b"],
        help="データソース (default: p3b)",
    )
    parser.add_argument(
        "--max-pairs", type=int, default=0,
        help="最大ペア数 (0=デフォルト: p3b=200, p3a=全ペア)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="データとプロンプトの確認のみ (モデルロードなし)",
    )
    parser.add_argument(
        "--max-length", type=int, default=512,
        help="トークナイザーの最大長 (default: 512)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="乱数シード (default: 42)",
    )
    args = parser.parse_args()

    # --- データ準備 ---
    print(f"📋 データ準備: {args.data}")
    if args.data == "p3a":
        data = prepare_data(max_pairs=args.max_pairs)
    else:
        max_p = args.max_pairs if args.max_pairs > 0 else 200
        # structural_probe.py の _HGK_ROOT が不正 (parent.parent = 04_企画)
        # → 正しいパスを明示的に渡す
        p3b_target = str(_HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード")
        data = prepare_data_p3b(
            target_dir=p3b_target,
            max_pairs=max_p,
            seed=args.seed,
        )

    print(f"  ペア数: {len(data)}")

    # --- C_CCL_OTHER 用シャッフルマップを事前生成 ---
    ccl_shuffle_map = create_ccl_shuffle_map(data, seed=args.seed)

    # --- Dry-run ---
    if args.dry_run:
        dry_run(data)
        return

    # --- モデルロード ---
    model, tokenizer, device, n_layers = load_model(args.model, bits=args.bits)

    # --- 実行条件の決定 ---
    if args.cond == "all":
        conditions = ["bare", "ast", "sig", "ccl_other"]
    else:
        conditions = [args.cond]

    # C0 は常に含める
    if "bare" not in conditions:
        conditions = ["bare"] + conditions

    # --- 各条件で hidden state 抽出 + cosine 計算 ---
    condition_results = {}
    for cond in conditions:
        result = run_fsp_condition(
            data, model, tokenizer, device, n_layers,
            fsp_mode=cond,
            model_key=args.model,
            max_length=args.max_length,
            ccl_shuffle_map=ccl_shuffle_map if cond == "ccl_other" else None,
        )
        result = compute_rhos(result, data)
        condition_results[cond] = result

        print(f"\n  {FSP_CONDITIONS[cond]}: best ρ = {result.best_rho:.4f} "
              f"@ Layer {result.best_rho_layer}")
        print(f"  {FSP_CONDITIONS[cond]}: best 偏ρ = {result.best_partial_rho:.4f} "
              f"@ Layer {result.best_partial_layer}")

    # --- 統計分析 ---
    if len(condition_results) >= 2 and "bare" in condition_results:
        analysis = analyze_fsp_results(condition_results, data)
    else:
        analysis = {"note": "比較には bare 条件が必要"}

    # --- 結果保存 ---
    save_fsp_results(
        condition_results, analysis, args.model, args.data,
        ccl_shuffle_map=ccl_shuffle_map,
    )


if __name__ == "__main__":
    main()
