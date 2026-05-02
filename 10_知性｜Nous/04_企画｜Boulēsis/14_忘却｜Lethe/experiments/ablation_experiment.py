#!/usr/bin/env python3
# PROOF: [L2/実験] <- 60_実験｜Peira/07_CCL-PL A0→§11.9→TF-IDF≈CodeBERT 問題のアブレーション検証
"""
§11.9 アブレーション実験: TF-IDF ≈ CodeBERT 問題の解明

解釈 A: CCL の設計が優秀で文字列レベルで構造を十分表現 → embedder は副次的
解釈 B: CodeBERT も TF-IDF も文字列一致に依存 → 「構造理解」は幻想

3条件のアブレーション:
  C0 (ベースライン): CCL 式をそのまま使用
  C1 (構造トークン破壊): >>, F:[], V:{}, I:[] 等をランダム文字列に置換
  C2 (語順シャッフル): CCL トークンの順序をランダムに並替
  C3 (構造正規化): 非構造トークン (fn, pred, _) を除去し構造のみ残す

Usage:
  python ablation_experiment.py --dry-run          # perturbation 確認のみ
  python ablation_experiment.py                    # 本実行
  python ablation_experiment.py --n-perms 500      # 置換検定回数指定
  python ablation_experiment.py --n 100            # 関数数制限
"""

# PURPOSE: §11.9 アブレーション実験 — TF-IDF≈CodeBERT の原因診断

import sys
import os
import re
import math
import random
import argparse
import json
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from itertools import combinations
from collections import Counter

# パス設定: p3b_benchmark.py と同階層なので同じルート解決
# p3b_benchmark は top-level で sys.path と mekhane を設定済み
_EXPERIMENTS_DIR = Path(__file__).parent
_LETHE_ROOT = _EXPERIMENTS_DIR.parent

# p3b_benchmark.py のルートから mekhane を解決
_HGK_ROOT = _LETHE_ROOT.parent.parent.parent  # 01_ヘゲモニコン｜Hegemonikon/
_MEKHANE_SRC = _HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"
sys.path.insert(0, str(_MEKHANE_SRC))
sys.path.insert(0, str(_EXPERIMENTS_DIR))  # p3b_benchmark を import するため

# p3b からインフラを再利用
from p3b_benchmark import (
    extract_functions,
    generate_pairs,
    ast_structural_distance,
    spearman_rho,
    _normalized_levenshtein,
    FunctionInfo,
    PairAnalysis,
)


# ============================================================
# 構造トークン定義
# ============================================================

# PURPOSE: CCL の構造トークン (演算子・修飾子) の正規表現パターン
# これらは CCL の「文法」を構成する要素
STRUCTURAL_PATTERNS = [
    # 射合成演算子
    r'^>>$',
    # 条件・反復・分岐の外枠
    r'^V:\{.*\}$',      # V:{...} 条件付き
    r'^C:\{.*\}$',      # C:{...} 条件分岐
    r'^F:\[.*\]\{.*\}$', # F:[each]{...} 反復
    r'^I:\[.*\]\{.*\}$', # I:[cond]{...} 分岐
    r'^E:\{.*\}$',      # E:{...} エラー処理
    # 随伴演算子
    r'^~$',
    r'^\*$',
    r'^%$',
    # 深度修飾子付きトークン
    r'^\/.+\+$',        # /verb+
    r'^\/.+\-$',        # /verb-
    # 座標修飾
    r'^\[.*\]$',        # [Va:E], [Pr:U] 等
    # 構造マーカー
    r'^_$',             # シーケンス区切り
]

# 構造トークンのキーワード (部分一致)
STRUCTURAL_KEYWORDS = {
    '>>', 'V:{', 'C:{', 'F:[', 'I:[', 'E:{',
    '~', '*', '%', '_',
}

# 非構造トークン: 具体的な関数名・変数名・リテラル
NON_STRUCTURAL_PATTERNS = [
    r'^[a-z][a-z0-9_]*$',     # 小文字のみ = 変数名/関数名 (fn, pred, cond 等)
    r'^\d+$',                  # 数値リテラル
    r'^".*"$',                 # 文字列リテラル
    r"^'.*'$",                 # 文字列リテラル
]


# ============================================================
# Perturbation 関数
# ============================================================

# PURPOSE: トークンが構造的かどうか判定
def is_structural_token(token: str) -> bool:
    """CCL トークンが構造的要素 (演算子・修飾子) かどうかを判定する。

    構造トークン: >>, V:{...}, F:[...]{...}, ~, *, %, _, /verb+, [座標]
    非構造トークン: fn, pred, cond, 123, "str" 等の具体名
    """
    # 射合成演算子
    if token == '>>':
        return True
    # シーケンス区切り
    if token == '_':
        return True
    # 随伴演算子
    if token in ('~', '*', '%'):
        return True
    # 条件/反復/分岐の外枠キーワードで始まる
    if any(token.startswith(kw) for kw in ('V:{', 'C:{', 'F:[', 'I:[', 'E:{')):
        return True
    # 深度修飾子付き verb
    if token.startswith('/') and (token.endswith('+') or token.endswith('-')):
        return True
    # 座標修飾 [...]
    if token.startswith('[') and token.endswith(']'):
        return True
    # 閉じ括弧
    if token in ('}', ']', '{', ')'):
        return True
    return False


# PURPOSE: 非構造トークンかどうか判定
def is_non_structural_token(token: str) -> bool:
    """具体的な関数名・変数名・リテラルかどうかを判定する。"""
    # 構造トークンなら非構造ではない
    if is_structural_token(token):
        return False
    # 小文字のみの識別子 (fn, pred, cond, handler 等)
    if re.match(r'^[a-z][a-z0-9_]*$', token):
        return True
    # 数値リテラル
    if re.match(r'^\d+$', token):
        return True
    # 文字列リテラル
    if (token.startswith('"') and token.endswith('"')) or \
       (token.startswith("'") and token.endswith("'")):
        return True
    return False


# PURPOSE: ランダム文字列生成
def _random_string(length: int = 4, seed_val: int = 0) -> str:
    """再現可能なランダム文字列を生成する。"""
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    rng = random.Random(seed_val)
    return ''.join(rng.choice(chars) for _ in range(length))


# PURPOSE: C1 — 構造トークンをランダム文字列に破壊
def perturb_c1_destroy(ccl: str, seed: int = 42) -> str:
    """構造トークン (>>, V:{}, F:[], I:[], ~, *, %) をランダム文字列に置換。

    構造が情報を持つなら、この操作で ρ は大幅に低下するはず。
    文字列一致のみをキャプチャしているなら、低下は小さいはず。
    """
    tokens = ccl.split()
    rng = random.Random(seed)
    result = []
    for token in tokens:
        if is_structural_token(token):
            # 構造トークンを同じ長さのランダム文字列に置換
            replacement = _random_string(max(len(token), 3), rng.randint(0, 100000))
            result.append(replacement)
        else:
            result.append(token)
    return ' '.join(result)


# PURPOSE: C2 — トークン順序をランダムシャッフル
def perturb_c2_shuffle(ccl: str, seed: int = 42) -> str:
    """CCL トークンの順序をランダムに並べ替える。

    トークン内容は保持するが合成構造 (順序) を破壊。
    bag-of-words 的処理なら影響は小さく、順序情報を持つ処理なら影響が大きい。
    """
    tokens = ccl.split()
    rng = random.Random(seed)
    shuffled = tokens.copy()
    rng.shuffle(shuffled)
    return ' '.join(shuffled)


# PURPOSE: C3 — 非構造トークンを除去して構造のみ残す
def perturb_c3_normalize(ccl: str) -> str:
    """非構造トークン (fn, pred, _, 数値) を除去して構造トークンのみ残す。

    CCL 表現が天井 (= ノイズ除去で改善) なら B 支持。
    非構造トークンも情報を持つ (= 低下) なら A 支持。
    """
    tokens = ccl.split()
    structural_only = [t for t in tokens if is_structural_token(t)]
    if not structural_only:
        # 構造トークンがない場合は元の式を返す (安全弁)
        return ccl
    return ' '.join(structural_only)


# PURPOSE: 統一 perturbation インターフェース
def perturb_ccl(ccl: str, condition: str, seed: int = 42) -> str:
    """条件に応じて CCL 式を perturbation する。"""
    if condition == "C0_baseline":
        return ccl
    elif condition == "C1_destroy":
        return perturb_c1_destroy(ccl, seed=seed)
    elif condition == "C2_shuffle":
        return perturb_c2_shuffle(ccl, seed=seed)
    elif condition == "C3_normalize":
        return perturb_c3_normalize(ccl)
    else:
        raise ValueError(f"Unknown condition: {condition}")


# ============================================================
# TF-IDF Embedder (軽量・CPU)
# ============================================================

# PURPOSE: TF-IDF ベースの embedder (scikit-learn 不要)
class SimpleTFIDF:
    """最小限の TF-IDF 実装。scikit-learn 不要。

    ドキュメント集合からプロファイルを学習し、各ドキュメントを
    固定次元のスパースベクトルとして表現する。
    """

    def __init__(self):
        self.vocab: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.n_docs: int = 0

    def fit(self, documents: list[str]):
        """語彙と IDF を学習する。"""
        self.n_docs = len(documents)
        # 語彙構築
        all_tokens = set()
        doc_freqs: Counter = Counter()
        for doc in documents:
            tokens = set(doc.split())
            all_tokens.update(tokens)
            for t in tokens:
                doc_freqs[t] += 1

        self.vocab = {t: i for i, t in enumerate(sorted(all_tokens))}

        # IDF 計算: log(N / (df + 1)) + 1 (smooth)
        for token, idx in self.vocab.items():
            df = doc_freqs.get(token, 0)
            self.idf[token] = math.log(self.n_docs / (df + 1)) + 1.0

    def transform(self, documents: list[str]) -> list[list[float]]:
        """ドキュメントを TF-IDF ベクトルに変換する。"""
        vectors = []
        dim = len(self.vocab)
        for doc in documents:
            tokens = doc.split()
            tf = Counter(tokens)
            vec = [0.0] * dim
            for token, count in tf.items():
                if token in self.vocab:
                    idx = self.vocab[token]
                    vec[idx] = (count / len(tokens)) * self.idf.get(token, 1.0)
            # L2 正規化
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0:
                vec = [x / norm for x in vec]
            vectors.append(vec)
        return vectors


# ============================================================
# Cosine 類似度
# ============================================================

# PURPOSE: ベクトル間の cosine 類似度
def cosine_similarity(a: list[float], b: list[float]) -> float:
    """2つのベクトルの cosine 類似度。"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ============================================================
# 実験パイプライン
# ============================================================

CONDITIONS = ["C0_baseline", "C1_destroy", "C2_shuffle", "C3_normalize"]

# PURPOSE: 単一条件の ρ を計算
def run_condition(
    functions: list[FunctionInfo],
    pairs: list[PairAnalysis],
    condition: str,
    embedder_name: str,  # "codebert" or "tfidf"
    seed: int = 42,
) -> dict:
    """指定条件で CCL を perturbation し、ρ(AST距離, cosine) を計算する。

    Returns:
        dict with rho, n_pairs, condition, embedder, perturbed_examples
    """
    # CCL perturbation
    perturbed_ccls = []
    for f in functions:
        perturbed = perturb_ccl(f.ccl, condition, seed=seed)
        perturbed_ccls.append(perturbed)

    # Embedding 取得
    if embedder_name == "codebert":
        embeddings = _embed_codebert(perturbed_ccls)
    elif embedder_name == "tfidf":
        embeddings = _embed_tfidf(perturbed_ccls)
    else:
        raise ValueError(f"Unknown embedder: {embedder_name}")

    # 名前→インデックスマッピング
    name_to_idx = {f.name: i for i, f in enumerate(functions)}

    # Cosine 類似度計算
    cosine_sims = []
    ast_sims = []
    for pair in pairs:
        idx_a = name_to_idx.get(pair.func_a)
        idx_b = name_to_idx.get(pair.func_b)
        if idx_a is None or idx_b is None:
            continue
        cos = cosine_similarity(embeddings[idx_a], embeddings[idx_b])
        cosine_sims.append(cos)
        ast_sims.append(1.0 - pair.ast_distance)  # 距離→類似度

    # Spearman ρ
    rho = spearman_rho(ast_sims, cosine_sims)

    # Perturbation 例 (最初の3件)
    examples = []
    for i in range(min(3, len(functions))):
        examples.append({
            "original": functions[i].ccl[:80],
            "perturbed": perturbed_ccls[i][:80],
        })

    return {
        "condition": condition,
        "embedder": embedder_name,
        "rho": rho,
        "n_pairs": len(cosine_sims),
        "examples": examples,
    }


# PURPOSE: torch が利用可能か確認
def _has_torch() -> bool:
    """torch がインストールされているか確認する。"""
    try:
        import torch  # noqa: F401
        return True
    except ImportError:
        return False


# PURPOSE: CodeBERT embedding
def _embed_codebert(texts: list[str]) -> list[list[float]]:
    """CodeBERT で embedding を取得する。torch が必要。"""
    from mekhane.anamnesis.codebert_embedder import CodeBertEmbedder
    embedder = CodeBertEmbedder(device="cpu")  # CPU 明示
    return embedder.embed_batch(texts)


# PURPOSE: TF-IDF embedding
def _embed_tfidf(texts: list[str]) -> list[list[float]]:
    """TF-IDF で embedding を取得する。"""
    tfidf = SimpleTFIDF()
    tfidf.fit(texts)
    return tfidf.transform(texts)


# ============================================================
# 置換検定
# ============================================================

# PURPOSE: 置換検定で Δρ の統計的有意性を検証
def permutation_test(
    functions: list[FunctionInfo],
    pairs: list[PairAnalysis],
    condition: str,
    embedder_name: str,
    baseline_rho: float,
    n_perms: int = 200,
    seed: int = 42,
) -> dict:
    """置換検定: CCL をランダムにペア間でシャッフルし、Δρ の分布を生成。

    帰無仮説: perturbation はρに影響しない (Δρ = 0)
    """
    observed_rho = run_condition(functions, pairs, condition, embedder_name, seed)["rho"]
    observed_delta = observed_rho - baseline_rho

    # シャッフル分布
    rng = random.Random(seed)
    null_deltas = []

    for perm_i in range(n_perms):
        # ランダムシードを変えて perturbation
        perm_seed = rng.randint(0, 1000000)
        perm_result = run_condition(functions, pairs, condition, embedder_name, perm_seed)
        null_deltas.append(perm_result["rho"] - baseline_rho)

    # p値: 観測された Δρ 以上に極端な値の割合
    # Δρ < 0 を期待するので片側検定 (ρ の低下)
    if observed_delta < 0:
        p_value = sum(1 for d in null_deltas if d <= observed_delta) / len(null_deltas)
    else:
        p_value = sum(1 for d in null_deltas if d >= observed_delta) / len(null_deltas)

    return {
        "condition": condition,
        "embedder": embedder_name,
        "observed_rho": observed_rho,
        "observed_delta": observed_delta,
        "null_mean": sum(null_deltas) / len(null_deltas) if null_deltas else 0,
        "null_std": (sum((d - sum(null_deltas)/len(null_deltas))**2 for d in null_deltas) / len(null_deltas))**0.5 if null_deltas else 0,
        "p_value": p_value,
        "n_perms": n_perms,
    }


# ============================================================
# Token 分析
# ============================================================

# PURPOSE: CCL トークンの構造/非構造比率を分析
def analyze_token_composition(functions: list[FunctionInfo]) -> dict:
    """CCL 式のトークン構成を分析する。"""
    total_tokens = 0
    structural_count = 0
    non_structural_count = 0
    other_count = 0
    structural_types: Counter = Counter()
    non_structural_examples: Counter = Counter()

    for f in functions:
        tokens = f.ccl.split()
        total_tokens += len(tokens)
        for t in tokens:
            if is_structural_token(t):
                structural_count += 1
                structural_types[t] += 1
            elif is_non_structural_token(t):
                non_structural_count += 1
                non_structural_examples[t] += 1
            else:
                other_count += 1

    return {
        "total_tokens": total_tokens,
        "structural": structural_count,
        "non_structural": non_structural_count,
        "other": other_count,
        "structural_ratio": structural_count / total_tokens if total_tokens > 0 else 0,
        "top_structural": structural_types.most_common(10),
        "top_non_structural": non_structural_examples.most_common(10),
    }


# ============================================================
# 結果出力
# ============================================================

# PURPOSE: 結果の表示
def print_results(results: list[dict], token_stats: dict, perm_results: list[dict] | None = None):
    """アブレーション結果を標準出力に表示する。"""
    print()
    print("=" * 80)
    print("  §11.9 アブレーション実験 — TF-IDF ≈ CodeBERT 問題の解明")
    print("=" * 80)

    # トークン構成
    print(f"\n  CCL トークン構成 ({token_stats['total_tokens']} tokens):")
    print(f"    構造トークン:   {token_stats['structural']:>5} ({token_stats['structural_ratio']:.1%})")
    print(f"    非構造トークン: {token_stats['non_structural']:>5} ({token_stats['non_structural']/token_stats['total_tokens']:.1%})")
    print(f"    その他:         {token_stats['other']:>5}")
    print(f"    上位構造: {', '.join(f'{t}({c})' for t, c in token_stats['top_structural'][:5])}")
    print(f"    上位非構造: {', '.join(f'{t}({c})' for t, c in token_stats['top_non_structural'][:5])}")

    # 条件ごとの結果テーブル
    # embedder 別にグループ化
    embedders = sorted(set(r["embedder"] for r in results))

    for emb in embedders:
        emb_results = [r for r in results if r["embedder"] == emb]
        baseline = next((r for r in emb_results if r["condition"] == "C0_baseline"), None)
        baseline_rho = baseline["rho"] if baseline else 0

        print(f"\n  [{emb.upper()}]")
        print(f"  {'条件':<20} {'ρ':>8} {'Δρ':>10} {'判定':>8}")
        print("  " + "-" * 50)

        for r in emb_results:
            delta = r["rho"] - baseline_rho
            if r["condition"] == "C0_baseline":
                judgment = "baseline"
            elif delta < -0.10:
                judgment = "A支持 ⬇️"
            elif delta < -0.05:
                judgment = "微低下"
            elif delta > 0.05:
                judgment = "B支持 ⬆️"
            else:
                judgment = "変化小"
            print(f"  {r['condition']:<20} {r['rho']:>8.4f} {delta:>+10.4f} {judgment:>8}")

    # perturbation 例
    print(f"\n  Perturbation 例:")
    for r in results:
        if r["condition"] != "C0_baseline" and r["embedder"] == embedders[0]:
            print(f"    [{r['condition']}]")
            for ex in r["examples"][:2]:
                print(f"      元: {ex['original']}")
                print(f"      後: {ex['perturbed']}")

    # 置換検定結果
    if perm_results:
        print(f"\n  置換検定結果:")
        print(f"  {'条件':<20} {'embedder':<10} {'Δρ':>8} {'p値':>8} {'判定':>10}")
        print("  " + "-" * 60)
        for pr in perm_results:
            sig = "✅ 有意" if pr["p_value"] < 0.05 else "❌ 非有意"
            print(f"  {pr['condition']:<20} {pr['embedder']:<10} "
                  f"{pr['observed_delta']:>+8.4f} {pr['p_value']:>8.4f} {sig:>10}")

    # 総合判定
    print(f"\n{'=' * 80}")
    _print_interpretation(results)
    print()


# PURPOSE: 結果の解釈
def _print_interpretation(results: list[dict]):
    """結果パターンから A/B 解釈を判定する。"""
    cb_results = {r["condition"]: r["rho"] for r in results if r["embedder"] == "codebert"}
    tf_results = {r["condition"]: r["rho"] for r in results if r["embedder"] == "tfidf"}

    # メインの比較対象を選択 (CodeBERT があれば CodeBERT、なければ TF-IDF)
    if cb_results and "C0_baseline" in cb_results:
        main_results = cb_results
        main_label = "CodeBERT"
    elif tf_results and "C0_baseline" in tf_results:
        main_results = tf_results
        main_label = "TF-IDF"
    else:
        print("  判定: データ不足")
        return

    main_baseline = main_results["C0_baseline"]
    tf_baseline = tf_results.get("C0_baseline", 0)

    evidence_a = 0
    evidence_b = 0

    # C1 判定
    if "C1_destroy" in main_results:
        delta = main_results["C1_destroy"] - main_baseline
        tf_delta = tf_results.get("C1_destroy", 0) - tf_baseline

        if delta < -0.10:
            evidence_a += 2
            print(f"  C1: {main_label} ρ 大幅低下 ({delta:+.4f}) → A支持 (構造トークンが情報を持つ)")
        elif delta > 0.05:
            evidence_b += 2
            print(f"  C1: {main_label} ρ 上昇 ({delta:+.4f}) → B支持 (構造トークンがノイズ)")
        elif delta > -0.05:
            evidence_b += 1
            print(f"  C1: {main_label} ρ 変化小 ({delta:+.4f}) → 弱B支持 (文字列一致)")
        else:
            evidence_a += 1
            print(f"  C1: {main_label} ρ 微低下 ({delta:+.4f}) → 弱A支持")

        # CodeBERT と TF-IDF の差分 (両方ある場合)
        if cb_results and main_label != "TF-IDF":
            if abs(delta - tf_delta) > 0.05:
                print(f"      CodeBERT vs TF-IDF の反応差: {delta - tf_delta:+.4f}")

    # C2 判定
    if "C2_shuffle" in main_results:
        delta = main_results["C2_shuffle"] - main_baseline
        tf_delta = tf_results.get("C2_shuffle", 0) - tf_baseline

        if delta < -0.10:
            evidence_a += 2
            print(f"  C2: {main_label} ρ 大幅低下 ({delta:+.4f}) → A支持 (順序構造を捉えている)")
        elif abs(delta) < 0.02:
            evidence_b += 2
            print(f"  C2: {main_label} ρ 不変 ({delta:+.4f}) → B支持 (bag-of-words 的)")
        elif delta > -0.05:
            evidence_b += 1
            print(f"  C2: {main_label} ρ 変化小 ({delta:+.4f}) → 弱B支持 (bag-of-words 的)")
        else:
            evidence_a += 1
            print(f"  C2: {main_label} ρ 微低下 ({delta:+.4f}) → 弱A支持")

        # TF-IDF は bag-of-words なので C2 で変化しないか確認
        if main_label == "TF-IDF" and abs(tf_delta) < 0.01:
            print(f"      TF-IDF は C2 で完全不変 ({tf_delta:+.4f}) — bag-of-words の直接確認")

    # C3 判定
    if "C3_normalize" in main_results:
        delta = main_results["C3_normalize"] - main_baseline

        if delta > 0.05:
            evidence_b += 2
            print(f"  C3: {main_label} ρ 改善 ({delta:+.4f}) → B支持 (ノイズ除去で改善 = CCL が天井)")
        elif delta < -0.05:
            evidence_a += 2
            print(f"  C3: {main_label} ρ 低下 ({delta:+.4f}) → A支持 (非構造トークンも情報を保持)")
        else:
            print(f"  C3: {main_label} ρ 変化小 ({delta:+.4f}) → 判定不明")

    # 総合
    print()
    if main_label == "TF-IDF" and not cb_results:
        print(f"  ⚠️ TF-IDF のみの結果 (CodeBERT なし)。解釈は暫定的。")

    if evidence_a > evidence_b:
        print(f"  → [推定] 解釈 A 優勢 (A:{evidence_a} vs B:{evidence_b})")
        print(f"    CCL の構造が文字列レベルで情報を持っている")
    elif evidence_b > evidence_a:
        print(f"  → [推定] 解釈 B 優勢 (A:{evidence_a} vs B:{evidence_b})")
        print(f"    embedder は文字列一致に依存")
    else:
        print(f"  → [仮説] A/B 拮抗 (A:{evidence_a} vs B:{evidence_b})")
        print(f"    ハイブリッド仮説: CCL は部分的に構造を表現 + 部分的に文字列一致")


# PURPOSE: 結果を JSON に保存
def save_results(results: list[dict], token_stats: dict,
                 perm_results: list[dict] | None,
                 output_path: Path):
    """結果を JSON ファイルに保存する。"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "experiment": "§11.9 ablation",
        "token_stats": {
            "total": token_stats["total_tokens"],
            "structural": token_stats["structural"],
            "non_structural": token_stats["non_structural"],
            "ratio": token_stats["structural_ratio"],
        },
        "results": results,
        "permutation_tests": perm_results or [],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"💾 結果を保存: {output_path}")


# ============================================================
# メインエントリ
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="§11.9 アブレーション実験")
    parser.add_argument("--dry-run", action="store_true",
                        help="perturbation 確認のみ (embedding なし)")
    parser.add_argument("-n", "--max-functions", type=int, default=200,
                        help="抽出する最大関数数 (デフォルト: 200)")
    parser.add_argument("--max-pairs", type=int, default=500,
                        help="分析する最大ペア数 (デフォルト: 500)")
    parser.add_argument("--n-perms", type=int, default=0,
                        help="置換検定回数 (0=スキップ、200 推奨)")
    parser.add_argument("--target-dir", type=str, default=None,
                        help="対象ディレクトリ (デフォルト: mekhane/)")
    parser.add_argument("--seed", type=int, default=42,
                        help="乱数シード")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="詳細出力")
    args = parser.parse_args()

    # ターゲットディレクトリの解決
    if args.target_dir:
        target_root = Path(args.target_dir)
    else:
        target_root = _MEKHANE_SRC / "mekhane"

    if not target_root.exists():
        print(f"❌ ディレクトリが見つかりません: {target_root}")
        sys.exit(1)

    print(f"🎯 対象: {target_root}")

    # Phase 1: 関数抽出 + CCL 変換 (p3b から再利用)
    print(f"📋 Phase 1: 関数抽出 (max {args.max_functions})...")
    functions = extract_functions(target_root, max_functions=args.max_functions)
    print(f"   抽出: {len(functions)} 関数")

    if len(functions) < 10:
        print("❌ 関数数が不十分 (最低 10 必要)")
        sys.exit(1)

    # Phase 2: トークン構成分析
    print("📋 Phase 2: トークン構成分析...")
    token_stats = analyze_token_composition(functions)
    print(f"   構造トークン比率: {token_stats['structural_ratio']:.1%}")

    # Phase 3: ペア生成 + 構造距離計算 (p3b から再利用)
    print(f"📋 Phase 3: ペア生成 + 構造距離計算...")
    pairs = generate_pairs(functions, max_pairs=args.max_pairs)
    print(f"   ペア: {len(pairs)}")

    # Dry-run: perturbation例の表示のみ
    if args.dry_run:
        print("\n  [dry-run] Perturbation 例:")
        for condition in CONDITIONS:
            print(f"\n    [{condition}]")
            for f in functions[:3]:
                original = f.ccl
                perturbed = perturb_ccl(original, condition, seed=args.seed)
                print(f"      元:  {original[:70]}")
                print(f"      後:  {perturbed[:70]}")

        # トークン判定のサンプル
        print("\n  トークン判定サンプル:")
        sample_tokens = set()
        for f in functions[:10]:
            sample_tokens.update(f.ccl.split())
        for t in sorted(sample_tokens)[:20]:
            s = is_structural_token(t)
            ns = is_non_structural_token(t)
            label = "構造" if s else ("非構造" if ns else "その他")
            print(f"    {t:<20} → {label}")

        print(f"\n  [dry-run] --dry-run を外して本実験を実行。")
        return

    # Phase 4: アブレーション実験 (CodeBERT + TF-IDF)
    print("📊 Phase 4: アブレーション実験...")
    results = []

    # 利用可能な embedder を動的に決定
    embedder_list = ["tfidf"]
    if _has_torch():
        embedder_list.append("codebert")
    else:
        print("  ⚠️ torch 未インストール: CodeBERT をスキップ (TF-IDF のみ)")

    for embedder_name in embedder_list:
        print(f"\n  [{embedder_name.upper()}]")
        for condition in CONDITIONS:
            print(f"    {condition}...", end=" ", flush=True)
            result = run_condition(functions, pairs, condition, embedder_name, seed=args.seed)
            results.append(result)
            print(f"ρ = {result['rho']:.4f}")

    # Phase 5: 置換検定 (オプション)
    perm_results = None
    if args.n_perms > 0:
        print(f"\n📊 Phase 5: 置換検定 ({args.n_perms} permutations)...")
        perm_results = []

        for embedder_name in embedder_list:
            baseline_rho = next(
                r["rho"] for r in results
                if r["embedder"] == embedder_name and r["condition"] == "C0_baseline"
            )
            for condition in ["C1_destroy", "C2_shuffle", "C3_normalize"]:
                print(f"    {embedder_name}/{condition}...", end=" ", flush=True)
                pr = permutation_test(
                    functions, pairs, condition, embedder_name,
                    baseline_rho, n_perms=args.n_perms, seed=args.seed,
                )
                perm_results.append(pr)
                print(f"p = {pr['p_value']:.4f}")

    # 結果出力
    print_results(results, token_stats, perm_results)

    # 保存
    output_path = Path(__file__).parent / "ablation_results.json"
    save_results(results, token_stats, perm_results, output_path)


if __name__ == "__main__":
    main()
