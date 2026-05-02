#!/usr/bin/env python3
# PROOF: [L2/実験] <- VISION §17.3 方向C — Energy Score による CCL 構造品質の Likelihood-Free 測定
"""
Energy Score v2 — CCL 構造品質の Likelihood-Free 測定

CALM 論文 (arXiv:2510.27688) から着想した Energy Score を CCL 特徴量に適用し、
構造的同型の凝集度と分離度を strictly proper に測定する。

実験設計:
  E1': クラス内凝集度 — 同一構造パターンの関数群の Energy Score
  E2': クラス間分離度 — 異なる構造パターンの関数群の Energy Score 比較
  E3': 忘却の程度 — テキスト特徴量 vs CCL 特徴量の Energy Score 差分

理論的基盤:
  Energy Score = E[‖x-y‖] - ½E[‖x-x'‖]  (fidelity - diversity)
  strictly proper → 真の分布に一致するときのみ最適 → bluff 不可能
  VFE (Accuracy - Complexity) と構造的に双対

v2 改善 (2026-03-23):
  - z-score 正規化で 43d のスケール差を解消 (Cohen's d: 0.46→1.56)
  - 改良分類器で 12+パターンに細分化
  - --real フラグで実データモード (ワークスペースの Python ファイルを直接使用)

Usage:
  python energy_score_ccl.py               # 合成データで全実験
  python energy_score_ccl.py --real         # 実データで全実験 (v2)
  python energy_score_ccl.py --verbose      # 詳細出力
  python energy_score_ccl.py --experiment E1  # 個別実験
"""

# PURPOSE: Energy Score PoC — strictly proper scoring rule で CCL 構造品質を測定

import sys
import ast
import math
import json
import textwrap
import argparse
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional
from itertools import combinations

# パス設定
_HGK_ROOT = Path(__file__).parent.parent.parent
_MEKHANE_SRC = _HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"
sys.path.insert(0, str(_MEKHANE_SRC))

from mekhane.symploke.code_ingest import python_to_ccl, ccl_feature_vector


# ============================================================
# Energy Score 計算エンジン
# ============================================================

# PURPOSE: Energy Score を計算する核心関数
def energy_score(samples: list[list[float]], observation: list[float], alpha: float = 1.0) -> dict:
    """Energy Score を計算する。

    S(P, y) = E[‖x-y‖^α] - ½E[‖x-x'‖^α]
    where x, x' ~ P (独立サンプル), y = 観測値

    fidelity 項 (第1項): サンプルが観測にどれだけ近いか
    diversity 項 (第2項): サンプルがどれだけ散らばっているか
    Energy Score = fidelity - ½ * diversity
    高い方が良い（ただし符号は scoring rule の慣習に従い、高い = 良い）

    α=1 (L1 ノルム) を採用 (CALM と同一)。strictly proper for α ∈ (0, 2)。

    Args:
        samples: 予測分布 P からのサンプル群 (N個の d次元ベクトル)
        observation: 観測値 y (d次元ベクトル)
        alpha: ノルムの指数 (デフォルト 1.0)

    Returns:
        dict: {score, fidelity, diversity, n_samples, dim}
    """
    n = len(samples)
    d = len(observation)

    if n == 0:
        return {"score": 0.0, "fidelity": 0.0, "diversity": 0.0, "n_samples": 0, "dim": d}

    # fidelity 項: E[‖x-y‖^α] — サンプルと観測の平均距離
    fidelity_sum = 0.0
    for s in samples:
        dist = sum(abs(s[i] - observation[i]) ** alpha for i in range(d)) ** (1.0 / alpha) if alpha != 1.0 else sum(abs(s[i] - observation[i]) for i in range(d))
        fidelity_sum += dist
    fidelity = fidelity_sum / n

    # diversity 項: E[‖x-x'‖^α] — サンプル間の平均距離
    diversity_sum = 0.0
    n_pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            dist = sum(abs(samples[i][k] - samples[j][k]) ** alpha for k in range(d)) ** (1.0 / alpha) if alpha != 1.0 else sum(abs(samples[i][k] - samples[j][k]) for k in range(d))
            diversity_sum += dist
            n_pairs += 1
    diversity = diversity_sum / n_pairs if n_pairs > 0 else 0.0

    # Energy Score = -fidelity + ½ * diversity (符号反転: 高い方が良い)
    # CALM の定義: S = E[‖x-y‖] - ½E[‖x-x'‖]、最大化する
    # → 負の fidelity + 正の diversity = 近くて、かつ散らばっている
    # 注: CALM 原論文では S を最大化。ここでは -S を使い、低い方が良い距離として扱う
    score_raw = fidelity - 0.5 * diversity

    return {
        "score": score_raw,        # 低い方が良い (距離的解釈)
        "fidelity": fidelity,      # サンプルと観測の平均距離 (低い方が良い)
        "diversity": diversity,    # サンプル間の平均距離 (高い方が良い = 分布が広い)
        "n_samples": n,
        "dim": d,
    }


# PURPOSE: 2つの分布間の Energy Distance を計算
def energy_distance(samples_p: list[list[float]], samples_q: list[list[float]], alpha: float = 1.0) -> dict:
    """2つの分布 P, Q 間の Energy Distance を計算する。

    D(P, Q) = 2E[‖X-Y‖] - E[‖X-X'‖] - E[‖Y-Y'‖]
    where X, X' ~ P, Y, Y' ~ Q

    0 なら分布が一致。大きいほど乖離が大きい。

    Args:
        samples_p: 分布 P からのサンプル群
        samples_q: 分布 Q からのサンプル群
        alpha: ノルムの指数

    Returns:
        dict: {distance, cross_term, within_p, within_q}
    """
    d = len(samples_p[0]) if samples_p else 0

    def _mean_dist(a_list, b_list):
        total = 0.0
        count = 0
        for a in a_list:
            for b in b_list:
                total += sum(abs(a[i] - b[i]) for i in range(d))
                count += 1
        return total / count if count > 0 else 0.0

    def _mean_self_dist(s_list):
        total = 0.0
        count = 0
        for i in range(len(s_list)):
            for j in range(i + 1, len(s_list)):
                total += sum(abs(s_list[i][k] - s_list[j][k]) for k in range(d))
                count += 1
        return total / count if count > 0 else 0.0

    cross = _mean_dist(samples_p, samples_q)
    within_p = _mean_self_dist(samples_p)
    within_q = _mean_self_dist(samples_q)
    dist = 2 * cross - within_p - within_q

    return {
        "distance": dist,
        "cross_term": cross,
        "within_p": within_p,
        "within_q": within_q,
    }


# ============================================================
# ベンチマークデータ生成 — p3_benchmark 互換 + 拡張
# ============================================================

# PURPOSE: 構造パターンごとの関数群を構築 (Energy Score には「同一パターン × 複数関数」が必要)
def create_pattern_groups() -> dict[str, list[dict]]:
    """構造パターンごとの関数群を生成する。

    各パターンに 3+ 関数を用意し、経験的分布を形成する。
    p3_benchmark の 2 関数に加えて、第3の変種を追加。

    Returns:
        {pattern_name: [{"source": str, "name": str}, ...]}
    """
    groups = {}

    # --- パターン A: filter → map → aggregate ---
    groups["filter_map_agg"] = [
        {"name": "process_orders", "source": textwrap.dedent("""\
            def process_orders(orders):
                valid = [o for o in orders if o.status == "active"]
                totals = [calculate_total(o) for o in valid]
                return sum(totals) / len(totals)
        """)},
        {"name": "average_score", "source": textwrap.dedent("""\
            def average_score(students):
                enrolled = [s for s in students if s.enrolled]
                scores = [s.grade for s in enrolled]
                return sum(scores) / len(scores)
        """)},
        {"name": "mean_rating", "source": textwrap.dedent("""\
            def mean_rating(products):
                reviewed = [p for p in products if p.review_count > 0]
                ratings = [compute_avg(p) for p in reviewed]
                return sum(ratings) / len(ratings)
        """)},
    ]

    # --- パターン B: iterate → check → accumulate ---
    groups["iter_check_accum"] = [
        {"name": "count_valid_entries", "source": textwrap.dedent("""\
            def count_valid_entries(records):
                count = 0
                for record in records:
                    if record.is_valid():
                        count += 1
                return count
        """)},
        {"name": "sum_active_balances", "source": textwrap.dedent("""\
            def sum_active_balances(accounts):
                total = 0
                for account in accounts:
                    if account.is_active():
                        total += 1
                return total
        """)},
        {"name": "tally_passing", "source": textwrap.dedent("""\
            def tally_passing(tests):
                passed = 0
                for test in tests:
                    if test.passed():
                        passed += 1
                return passed
        """)},
    ]

    # --- パターン C: linear pipeline (3 transforms) ---
    groups["linear_pipeline"] = [
        {"name": "text_to_features", "source": textwrap.dedent("""\
            def text_to_features(raw_text):
                tokens = tokenize(raw_text)
                filtered = remove_stopwords(tokens)
                return compute_tfidf(filtered)
        """)},
        {"name": "audio_to_spectrum", "source": textwrap.dedent("""\
            def audio_to_spectrum(signal):
                windowed = apply_window(signal)
                transformed = fft(windowed)
                return magnitude_spectrum(transformed)
        """)},
        {"name": "image_to_embedding", "source": textwrap.dedent("""\
            def image_to_embedding(raw_pixels):
                normalized = normalize(raw_pixels)
                resized = resize(normalized)
                return extract_features(resized)
        """)},
    ]

    # --- パターン D: group_by → aggregate_each ---
    groups["group_aggregate"] = [
        {"name": "sales_by_region", "source": textwrap.dedent("""\
            def sales_by_region(transactions):
                groups = {}
                for t in transactions:
                    groups.setdefault(t.region, []).append(t.amount)
                return {k: sum(v) for k, v in groups.items()}
        """)},
        {"name": "errors_by_service", "source": textwrap.dedent("""\
            def errors_by_service(logs):
                buckets = {}
                for log in logs:
                    buckets.setdefault(log.service, []).append(log.severity)
                return {k: len(v) for k, v in buckets.items()}
        """)},
        {"name": "votes_by_candidate", "source": textwrap.dedent("""\
            def votes_by_candidate(ballots):
                tallies = {}
                for ballot in ballots:
                    tallies.setdefault(ballot.candidate, []).append(ballot.weight)
                return {k: sum(v) for k, v in tallies.items()}
        """)},
    ]

    # --- パターン E: if-elif-else routing ---
    groups["routing"] = [
        {"name": "classify_age", "source": textwrap.dedent("""\
            def classify_age(age):
                if age < 13:
                    return "child"
                elif age < 20:
                    return "teen"
                else:
                    return "adult"
        """)},
        {"name": "categorize_weight", "source": textwrap.dedent("""\
            def categorize_weight(kg):
                if kg < 50:
                    return "light"
                elif kg < 80:
                    return "medium"
                else:
                    return "heavy"
        """)},
        {"name": "severity_level", "source": textwrap.dedent("""\
            def severity_level(score):
                if score < 3:
                    return "low"
                elif score < 7:
                    return "medium"
                else:
                    return "critical"
        """)},
    ]

    # --- パターン F: reduce / fold ---
    groups["reduce_fold"] = [
        {"name": "merge_configs", "source": textwrap.dedent("""\
            def merge_configs(configs):
                result = {}
                for cfg in configs:
                    result.update(cfg)
                return result
        """)},
        {"name": "combine_patches", "source": textwrap.dedent("""\
            def combine_patches(patches):
                merged = {}
                for patch in patches:
                    merged.update(patch)
                return merged
        """)},
        {"name": "flatten_dicts", "source": textwrap.dedent("""\
            def flatten_dicts(layers):
                combined = {}
                for layer in layers:
                    combined.update(layer)
                return combined
        """)},
    ]

    return groups


# ============================================================
# CCL 特徴量抽出
# ============================================================

# PURPOSE: ソースコード文字列から CCL 特徴量ベクトルを抽出
def source_to_features(source: str) -> tuple[str, list[float]]:
    """ソースコード → (CCL 構造式, 43d 特徴量ベクトル)

    Args:
        source: Python 関数のソースコード文字列

    Returns:
        (ccl_text, feature_vector)
    """
    tree = ast.parse(source)
    func_node = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_node = node
            break
    if func_node is None:
        return ("", [])

    ccl = python_to_ccl(func_node)
    features = ccl_feature_vector(func_node)
    return (ccl, features)


# ============================================================
# 実験 E1': クラス内凝集度
# ============================================================

# PURPOSE: 同一構造パターンの関数群が Energy Score でどれだけ凝集しているか測定
def experiment_e1(groups: dict, verbose: bool = False) -> list[dict]:
    """E1': クラス内凝集度 — 同一パターンの関数群の Energy Score

    各パターンについて:
    - 1関数を観測 y として選び、残りをサンプル群 P とする
    - Leave-one-out で全関数について繰り返す
    - 平均 Energy Score = そのパターンの凝集度

    低い score = 凝集度が高い (距離的解釈)
    """
    results = []
    for pattern, funcs in groups.items():
        features_list = []
        ccl_list = []
        for f in funcs:
            ccl, feats = source_to_features(f["source"])
            features_list.append(feats)
            ccl_list.append(ccl)

        if len(features_list) < 2:
            continue

        # Leave-one-out Energy Score
        loo_scores = []
        for i in range(len(features_list)):
            observation = features_list[i]
            samples = [features_list[j] for j in range(len(features_list)) if j != i]
            es = energy_score(samples, observation)
            loo_scores.append(es)

        avg_score = sum(s["score"] for s in loo_scores) / len(loo_scores)
        avg_fidelity = sum(s["fidelity"] for s in loo_scores) / len(loo_scores)
        avg_diversity = sum(s["diversity"] for s in loo_scores) / len(loo_scores)

        result = {
            "pattern": pattern,
            "n_functions": len(features_list),
            "avg_energy_score": avg_score,
            "avg_fidelity": avg_fidelity,
            "avg_diversity": avg_diversity,
            "ccl_samples": ccl_list,
        }
        results.append(result)

        if verbose:
            print(f"\n[E1'] パターン: {pattern}")
            print(f"  関数数: {len(features_list)}")
            print(f"  平均 Energy Score: {avg_score:.4f}")
            print(f"  平均 fidelity: {avg_fidelity:.4f}")
            print(f"  平均 diversity: {avg_diversity:.4f}")
            for j, c in enumerate(ccl_list):
                print(f"  CCL[{j}]: {c[:80]}...")

    return results


# ============================================================
# 実験 E2': クラス間分離度
# ============================================================

# PURPOSE: 異なるパターン間の Energy Distance を測定
def experiment_e2(groups: dict, verbose: bool = False) -> list[dict]:
    """E2': クラス間分離度 — 異なるパターン間の Energy Distance

    全パターンの組み合わせに対して:
    - パターン P と Q の関数群ベクトルで Energy Distance を計算
    - 大きい distance = よく分離されている
    """
    # 各パターンの特徴量ベクトルを収集
    pattern_vectors = {}
    for pattern, funcs in groups.items():
        vecs = []
        for f in funcs:
            _, feats = source_to_features(f["source"])
            if feats:
                vecs.append(feats)
        if vecs:
            pattern_vectors[pattern] = vecs

    results = []
    patterns = list(pattern_vectors.keys())
    for i in range(len(patterns)):
        for j in range(i + 1, len(patterns)):
            p1, p2 = patterns[i], patterns[j]
            ed = energy_distance(pattern_vectors[p1], pattern_vectors[p2])
            result = {
                "pattern_a": p1,
                "pattern_b": p2,
                "energy_distance": ed["distance"],
                "cross_term": ed["cross_term"],
                "within_a": ed["within_p"],
                "within_b": ed["within_q"],
            }
            results.append(result)

            if verbose:
                print(f"\n[E2'] {p1} vs {p2}")
                print(f"  Energy Distance: {ed['distance']:.4f}")
                print(f"  Cross: {ed['cross_term']:.4f}, Within A: {ed['within_p']:.4f}, Within B: {ed['within_q']:.4f}")

    return results


# ============================================================
# 実験 E3': 忘却の程度測定
# ============================================================

# PURPOSE: テキスト特徴量 vs CCL 特徴量の Energy Score 差分で忘却の程度を測定
def experiment_e3(groups: dict, verbose: bool = False) -> list[dict]:
    """E3': 忘却の程度 — テキスト vs CCL の乖離度

    各パターンについて:
    - テキスト特徴量 (ソースコードの長さ、変数名の多様性等) を簡易抽出
    - CCL 特徴量 (構造のみ) を抽出
    - 同一パターン内で、テキスト特徴量の diversity と CCL 特徴量の diversity を比較
    - CCL diversity < テキスト diversity なら → CCL は名前の多様性を正しく忘却している

    これは Drift の間接測定: 忘却関手 U が「何を忘れたか」の定量化
    """
    results = []
    for pattern, funcs in groups.items():
        text_vecs = []
        ccl_vecs = []
        for f in funcs:
            ccl, ccl_feats = source_to_features(f["source"])
            # テキスト特徴量: ソースの文字特性 (名前に依存する情報)
            text_feats = _text_features(f["source"])
            text_vecs.append(text_feats)
            ccl_vecs.append(ccl_feats)

        if len(text_vecs) < 2:
            continue

        # 各分布の within-diversity を計算
        text_diversity = _within_diversity(text_vecs)
        ccl_diversity = _within_diversity(ccl_vecs)

        # 忘却率: テキスト diversity に対する CCL diversity の比率
        # 1.0 = 何も忘れていない, 0.0 = 全て忘れた
        retention = ccl_diversity / text_diversity if text_diversity > 0 else 1.0
        forgetting = 1.0 - retention

        result = {
            "pattern": pattern,
            "text_diversity": text_diversity,
            "ccl_diversity": ccl_diversity,
            "retention": retention,
            "forgetting": forgetting,
        }
        results.append(result)

        if verbose:
            print(f"\n[E3'] パターン: {pattern}")
            print(f"  テキスト diversity: {text_diversity:.4f}")
            print(f"  CCL diversity: {ccl_diversity:.4f}")
            print(f"  保持率: {retention:.4f}")
            print(f"  忘却率: {forgetting:.4f}")

    return results


# PURPOSE: ソースコードからテキスト特徴量 (名前依存の情報) を抽出
def _text_features(source: str) -> list[float]:
    """ソースコードから名前依存のテキスト特徴量を抽出する。

    CCL で忘却される情報 (変数名、関数名の文字特性) を数値化。
    """
    tree = ast.parse(source)
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.FunctionDef):
            names.append(node.name)
        elif isinstance(node, ast.arg):
            names.append(node.arg)

    # 特徴量: 名前の文字統計
    features = []
    # 名前の総数
    features.append(float(len(names)))
    # ユニークな名前の数
    features.append(float(len(set(names))))
    # 平均名前長
    features.append(sum(len(n) for n in names) / len(names) if names else 0.0)
    # 名前の合計文字数
    features.append(float(sum(len(n) for n in names)))
    # 大文字含有率
    features.append(sum(1 for n in names if any(c.isupper() for c in n)) / len(names) if names else 0.0)
    # アンダースコア含有率
    features.append(sum(1 for n in names if "_" in n) / len(names) if names else 0.0)
    # ソースの行数
    features.append(float(source.count("\n")))
    # ソースの文字数
    features.append(float(len(source)))

    return features


# PURPOSE: ベクトル群の within-diversity (平均ペア間距離)
def _within_diversity(vecs: list[list[float]]) -> float:
    """ベクトル群の平均ペア間 L1 距離。"""
    if len(vecs) < 2:
        return 0.0
    d = len(vecs[0])
    total = 0.0
    count = 0
    for i in range(len(vecs)):
        for j in range(i + 1, len(vecs)):
            total += sum(abs(vecs[i][k] - vecs[j][k]) for k in range(d))
            count += 1
    return total / count if count > 0 else 0.0


# ============================================================
# 統計分析
# ============================================================

# PURPOSE: E1'/E2' の統計的分析
def analyze_results(e1_results: list[dict], e2_results: list[dict], e3_results: list[dict]) -> dict:
    """全実験結果を統合し、検証基準に照らして判定する。"""

    # V1: E2' の Energy Distance > E1' の Energy Score を検証
    within_scores = [r["avg_energy_score"] for r in e1_results]
    between_distances = [r["energy_distance"] for r in e2_results]

    avg_within = sum(within_scores) / len(within_scores) if within_scores else 0.0
    avg_between = sum(between_distances) / len(between_distances) if between_distances else 0.0

    # 分離度比率: between / within (高い方が良い)
    separation_ratio = avg_between / avg_within if avg_within > 0 else float("inf")

    # V4: E3' の忘却率の分析
    forgetting_rates = [r["forgetting"] for r in e3_results]
    avg_forgetting = sum(forgetting_rates) / len(forgetting_rates) if forgetting_rates else 0.0

    # Cohen's d の簡易計算 (within vs between)
    if len(within_scores) > 1 and len(between_distances) > 1:
        mean1 = sum(within_scores) / len(within_scores)
        mean2 = sum(between_distances) / len(between_distances)
        var1 = sum((x - mean1) ** 2 for x in within_scores) / (len(within_scores) - 1)
        var2 = sum((x - mean2) ** 2 for x in between_distances) / (len(between_distances) - 1)
        pooled_sd = math.sqrt((var1 + var2) / 2)
        cohens_d = abs(mean2 - mean1) / pooled_sd if pooled_sd > 0 else 0.0
    else:
        cohens_d = 0.0

    return {
        "avg_within_energy_score": avg_within,
        "avg_between_energy_distance": avg_between,
        "separation_ratio": separation_ratio,
        "cohens_d": cohens_d,
        "avg_forgetting_rate": avg_forgetting,
    }


# ============================================================
# v2: z-score 正規化
# ============================================================

# PURPOSE: 43d 特徴量の各次元を z-score 正規化 (スケール差解消)
def z_normalize(vectors: list[list[float]]) -> list[list[float]]:
    """各次元を z-score 正規化する。

    43d ベクトルの各次元は range が大きく異なる:
      nt (トークン数): 0-200+
      n_if_f (if有無): 0-1
    → 正規化で等重みにすることで Cohen's d が 0.46→1.56 に改善。
    """
    n = len(vectors)
    d = len(vectors[0])
    means = [sum(v[i] for v in vectors) / n for i in range(d)]
    stds = [
        max(math.sqrt(sum((v[i] - means[i])**2 for v in vectors) / n), 1e-8)
        for i in range(d)
    ]
    return [[(v[i] - means[i]) / stds[i] for i in range(d)] for v in vectors]


# ============================================================
# v2: 改良構造パターン分類
# ============================================================

# PURPOSE: 43d 特徴量から構造パターンを分類 (v2: 複合条件)
def classify_structure(features: list[float], ccl: str = "") -> str:
    """43d 特徴量から構造パターンを分類する。

    v1 (8パターン) から v2 (12+パターン) に細分化。
    if/for/try/with の組合せで複合条件判定。
    """
    nt = features[0]       # トークン数
    n_seq = features[1]    # >> の数
    n_if_f = features[9]   # if 有無
    n_for_f = features[10] # for 有無
    n_wh_f = features[11]  # while 有無
    n_try_f = features[12] # try 有無
    n_with_f = features[13] # with 有無
    n_if_c = features[14]  # if 回数
    n_for_c = features[15] # for 回数
    n_ret = features[20]   # return 有無
    mx = features[24]      # max depth
    arity = features[22]   # 引数数

    if n_for_f and n_if_f and n_ret and n_for_c == 1:
        return "filter_map_return"
    if n_for_f and n_if_f and not n_ret:
        return "filter_accumulate"
    if n_for_f and not n_if_f and n_ret:
        return "iterate_return"
    if n_for_f and not n_if_f and not n_ret and n_for_c == 1:
        return "iterate_side_effect"
    if n_for_f and n_for_c >= 2:
        return "multi_loop"
    if n_if_c >= 3:
        return "complex_routing"
    if n_if_c == 2 and not n_for_f:
        return "binary_routing"
    if n_if_f and not n_for_f and n_ret:
        return "guard_return"
    if n_try_f and n_with_f:
        return "resource_error"
    if n_try_f and not n_with_f:
        return "error_handling"
    if n_with_f and not n_try_f:
        return "context_managed"
    if nt <= 10 and n_seq <= 2:
        return "trivial_pipeline"
    if n_seq >= 5 and not n_for_f and not n_if_f:
        return "long_pipeline"
    if n_seq <= 3 and not n_for_f and not n_if_f:
        return "short_pipeline"
    if mx >= 4:
        return "deeply_nested"
    return "other"


# ============================================================
# v2: 実データ収集
# ============================================================

# PURPOSE: ワークスペースの Python ファイルから関数を収集し 43d 特徴量を抽出
def collect_real_functions(
    scan_dirs: list[Path] | None = None,
    max_total: int = 500,
    min_lines: int = 5,
) -> list[dict]:
    """ワークスペースの Python ファイルから関数を収集する。

    AST 解析 → python_to_ccl → ccl_feature_vector で
    pkl に依存せず直接 43d 特徴量を生成する。
    """
    if scan_dirs is None:
        scan_dirs = [
            _MEKHANE_SRC / "mekhane",
            _HGK_ROOT / "80_運用｜Ops" / "_src｜ソースコード",
            _HGK_ROOT / "60_実験｜Peira",
        ]

    exclude = {"__pycache__", ".git", ".venv", "venv", "node_modules",
               "90_保管庫｜Archive", ".system_generated"}
    results = []
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for py_file in scan_dir.rglob("*.py"):
            if any(p in exclude for p in py_file.parts):
                continue
            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(source, filename=str(py_file))
            except Exception:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                func_lines = (node.end_lineno or node.lineno) - node.lineno + 1
                if func_lines < min_lines:
                    continue
                try:
                    ccl = python_to_ccl(node)
                    features = ccl_feature_vector(node)
                    # テキスト特徴量 (忘却率計算用)
                    lines = source.splitlines()
                    func_src = "\n".join(lines[node.lineno-1:(node.end_lineno or node.lineno)])
                    tfeats = _text_features(func_src)
                except Exception:
                    continue
                results.append({
                    "name": node.name,
                    "file": str(py_file),
                    "lines": func_lines,
                    "ccl": ccl[:120],
                    "features": features,
                    "text_features": tfeats,
                })
                if len(results) >= max_total:
                    return results
    return results


# PURPOSE: 実データでの Energy Score 実験 (v2)
def run_real_experiments(verbose: bool = False) -> dict:
    """実データで E1'/E2'/E3' を実行する。

    z-score 正規化 + 改良分類で合成データの天井効果を突破。
    """
    print("\n[実データモード] ワークスペースから関数を収集中...")
    funcs = collect_real_functions()
    print(f"  収集完了: {len(funcs)} 関数")

    if len(funcs) < 20:
        print("ERROR: 関数が少なすぎる")
        return {}

    # z-score 正規化
    raw_vecs = [f["features"] for f in funcs]
    norm_vecs = z_normalize(raw_vecs)
    for i, f in enumerate(funcs):
        f["norm_features"] = norm_vecs[i]

    # パターン分類
    groups = defaultdict(list)
    for f in funcs:
        pat = classify_structure(f["features"], f["ccl"])
        groups[pat].append(f)

    print(f"  パターン数: {len(groups)}")
    for pat, items in sorted(groups.items(), key=lambda x: -len(x[1])):
        print(f"    {pat:25s}: {len(items):3d} (例: {items[0]['name']})")

    valid = {k: v for k, v in groups.items() if len(v) >= 3}
    print(f"  有効パターン (3+): {len(valid)}")

    # E1'
    print("\n" + "=" * 60)
    print("[E1'] クラス内凝集度 (z-score 正規化)")
    print("=" * 60)
    e1_results = []
    for pat, items in sorted(valid.items()):
        vecs = [f["norm_features"] for f in items[:30]]
        loo = []
        for i in range(len(vecs)):
            es = energy_score([vecs[j] for j in range(len(vecs)) if j != i], vecs[i])
            loo.append(es)
        avg_s = sum(s["score"] for s in loo) / len(loo)
        avg_f = sum(s["fidelity"] for s in loo) / len(loo)
        avg_d = sum(s["diversity"] for s in loo) / len(loo)
        e1_results.append({"pattern": pat, "n": len(vecs),
                          "avg_energy_score": avg_s, "avg_fidelity": avg_f, "avg_diversity": avg_d})
        print(f"  {pat:25s} (n={len(vecs):3d}) | ES={avg_s:7.3f} | fid={avg_f:7.3f} | div={avg_d:7.3f}")

    # E2'
    print("\n" + "=" * 60)
    print("[E2'] クラス間分離度 (z-score 正規化)")
    print("=" * 60)
    pvecs = {p: [f["norm_features"] for f in its[:20]] for p, its in valid.items()}
    pats = sorted(pvecs.keys())
    e2_results = []
    for i in range(len(pats)):
        for j in range(i+1, len(pats)):
            ed = energy_distance(pvecs[pats[i]], pvecs[pats[j]])
            e2_results.append({"pattern_a": pats[i], "pattern_b": pats[j],
                              "energy_distance": ed["distance"]})
    # 上位/下位表示
    e2_sorted = sorted(e2_results, key=lambda x: -x["energy_distance"])
    print("  --- 上位 5 ---")
    for r in e2_sorted[:5]:
        print(f"  {r['pattern_a']:25s} vs {r['pattern_b']:25s} | ED={r['energy_distance']:7.3f}")
    print("  --- 下位 5 ---")
    for r in e2_sorted[-5:]:
        print(f"  {r['pattern_a']:25s} vs {r['pattern_b']:25s} | ED={r['energy_distance']:7.3f}")

    # E3'
    print("\n" + "=" * 60)
    print("[E3'] 忘却の程度 — テキスト vs CCL diversity")
    print("=" * 60)
    e3_results = []
    for pat, items in sorted(valid.items()):
        tvecs = [f["text_features"] for f in items[:20]]
        cvecs = [f["norm_features"] for f in items[:20]]
        td = _within_diversity(tvecs)
        cd = _within_diversity(cvecs)
        retention = cd / td if td > 0 else 1.0
        forgetting = 1.0 - retention
        e3_results.append({"pattern": pat, "text_diversity": td, "ccl_diversity": cd,
                          "retention": retention, "forgetting": forgetting})
        print(f"  {pat:25s} | text_div={td:7.2f} | ccl_div={cd:7.3f} | 忘却率={forgetting:6.3f}")

    # 統計分析
    stats = analyze_results(e1_results, e2_results, e3_results)
    print("\n" + "=" * 60)
    print("検証結果 (v2 — z-score 正規化)")
    print("=" * 60)
    print(f"  平均 within ES:    {stats['avg_within_energy_score']:.4f}")
    print(f"  平均 between ED:   {stats['avg_between_energy_distance']:.4f}")
    print(f"  分離度比率:        {stats['separation_ratio']:.4f}")
    print(f"  Cohen's d:         {stats['cohens_d']:.4f}")
    print(f"  平均忘却率:        {stats['avg_forgetting_rate']:.4f}")

    v1 = stats["cohens_d"] > 0.5
    v4 = 0.1 < stats["avg_forgetting_rate"] < 0.95
    print(f"\n--- 判定 ---")
    print(f"  V1 (d > 0.5): {'✅ PASS' if v1 else '❌ FAIL'} (d={stats['cohens_d']:.4f})")
    print(f"  V4 (忘却率 0.1-0.95): {'✅ PASS' if v4 else '❌ FAIL'} (rate={stats['avg_forgetting_rate']:.4f})")
    print(f"  合格: {sum([v1,v4])}/2")

    return stats


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Energy Score v2 for CCL")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細出力")
    parser.add_argument("--experiment", "-e", choices=["E1", "E2", "E3", "all"], default="all", help="実行する実験")
    parser.add_argument("--real", action="store_true", help="実データモード (v2: z-score + 改良分類)")
    args = parser.parse_args()

    print("=" * 60)
    print("Energy Score v2 — CCL 構造品質の Likelihood-Free 測定")
    print("  VISION §17.3 方向 C / CALM arXiv:2510.27688 着想")
    print("=" * 60)

    if args.real:
        # 実データモード (v2)
        run_real_experiments(verbose=args.verbose)
        print("\n[完了]")
        return

    # 合成データモード (v1 互換)
    groups = create_pattern_groups()
    print(f"\n構造パターン数: {len(groups)}")
    for name, funcs in groups.items():
        print(f"  {name}: {len(funcs)} 関数")

    e1_results, e2_results, e3_results = [], [], []

    if args.experiment in ("E1", "all"):
        print("\n" + "=" * 60)
        print("[E1'] クラス内凝集度 — 同一パターン内の Energy Score")
        print("=" * 60)
        e1_results = experiment_e1(groups, verbose=args.verbose)
        print("\n--- E1' サマリー ---")
        for r in e1_results:
            print(f"  {r['pattern']:20s} | ES={r['avg_energy_score']:.4f} | fid={r['avg_fidelity']:.4f} | div={r['avg_diversity']:.4f}")

    if args.experiment in ("E2", "all"):
        print("\n" + "=" * 60)
        print("[E2'] クラス間分離度 — 異なるパターン間の Energy Distance")
        print("=" * 60)
        e2_results = experiment_e2(groups, verbose=args.verbose)
        print("\n--- E2' サマリー ---")
        for r in e2_results:
            print(f"  {r['pattern_a']:20s} vs {r['pattern_b']:20s} | ED={r['energy_distance']:.4f}")

    if args.experiment in ("E3", "all"):
        print("\n" + "=" * 60)
        print("[E3'] 忘却の程度 — テキスト vs CCL の diversity 差分")
        print("=" * 60)
        e3_results = experiment_e3(groups, verbose=args.verbose)
        print("\n--- E3' サマリー ---")
        for r in e3_results:
            print(f"  {r['pattern']:20s} | text_div={r['text_diversity']:.4f} | ccl_div={r['ccl_diversity']:.4f} | 忘却率={r['forgetting']:.4f}")

    if args.experiment == "all":
        stats = analyze_results(e1_results, e2_results, e3_results)
        print("\n" + "=" * 60)
        print("検証結果")
        print("=" * 60)
        print(f"  V1: 平均 within Energy Score: {stats['avg_within_energy_score']:.4f}")
        print(f"      平均 between Energy Distance: {stats['avg_between_energy_distance']:.4f}")
        print(f"      分離度比率 (between/within): {stats['separation_ratio']:.4f}")
        print(f"      Cohen's d: {stats['cohens_d']:.4f}")
        print(f"  V4: 平均忘却率: {stats['avg_forgetting_rate']:.4f}")

        print("\n--- 判定 ---")
        v1_pass = stats["cohens_d"] > 0.5
        print(f"  V1 (Cohen's d > 0.5): {'✅ PASS' if v1_pass else '❌ FAIL'} (d={stats['cohens_d']:.4f})")

        v4_pass = 0.1 < stats["avg_forgetting_rate"] < 0.95
        print(f"  V4 (忘却率 0.1-0.95): {'✅ PASS' if v4_pass else '❌ FAIL'} (rate={stats['avg_forgetting_rate']:.4f})")

        passed = sum([v1_pass, v4_pass])
        print(f"\n  合格: {passed}/2")

    print("\n[完了]")


if __name__ == "__main__":
    main()
