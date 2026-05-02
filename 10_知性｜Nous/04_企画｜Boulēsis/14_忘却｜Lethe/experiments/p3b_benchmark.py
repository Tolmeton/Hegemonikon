#!/usr/bin/env python3
# PROOF: [L2/実験] <- 60_実験｜Peira/07_CCL-PL A0→P3b検証→実世界コードベースでの CCL embedding 検証
"""
P3b 検証実験: 実世界コードベースでの CCL embedding vs Text embedding

VISION.md §8.1 P3b:
  P3 (合成ベンチマーク) を実世界コードベースで再現検証。
  循環論法を回避するため、CCL 非依存の構造距離指標と embedding cosine の
  Spearman 順位相関を主指標とする。

実験設計 (構造距離相関法):
  1. mekhane/ から medium (4-10 stmts) の関数を抽出
  2. python_to_ccl() で CCL 構造式を取得
  3. AST 構造距離 + 制御フロー距離を計算 (CCL 非依存)
  4. text embedding + CCL embedding で cosine 類似度を計算
  5. Spearman ρ(構造距離, cosine) を CCL vs Text で比較

Usage:
  python p3b_benchmark.py --dry-run   # 関数抽出 + CCL 変換 + 距離計算のみ
  python p3b_benchmark.py             # 本実験
  python p3b_benchmark.py -n 100      # 関数数を制限
"""

# PURPOSE: P3b 検証実験 — 実世界コードベースの構造距離相関法

import sys
import os
import ast
import json
import math
import random
import argparse
import textwrap
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from itertools import combinations

# パス設定
_HGK_ROOT = Path(__file__).parent.parent.parent
_MEKHANE_SRC = _HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"
sys.path.insert(0, str(_MEKHANE_SRC))

# PURPOSE: 手動 .env ローダー (python-dotenv 不要)
def _load_env_file(env_path: Path):
    """KEY=VALUE 形式の .env ファイルを読み、環境変数に設定する。"""
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # クォート除去
        if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value

from mekhane.symploke.code_ingest import python_to_ccl


# ============================================================
# データ構造
# ============================================================

# PURPOSE: 抽出された実世界関数の情報
@dataclass
class FunctionInfo:
    """実世界関数の情報。"""
    name: str              # 関数名
    file_path: str         # ソースファイルパス (相対)
    source: str            # ソースコード
    ccl: str               # CCL 構造式
    stmt_count: int        # 文の数
    control_flow: dict     # 制御フロー要素の出現回数 (multiset)
    ast_node_types: list   # AST ノード型のリスト (全ノード走査、順序付き)


# PURPOSE: ペアの分析結果
@dataclass
class PairAnalysis:
    """関数ペアの距離・類似度分析。"""
    func_a: str            # 関数名 A
    func_b: str            # 関数名 B
    # 構造距離 (0=同一, 1=完全に異なる)
    ast_distance: float    # AST 構造距離 (CCL 非依存)
    cf_distance: float     # 制御フロー距離 (CCL 非依存)
    ccl_edit_distance: float  # CCL 編集距離 (参考)
    # embedding 類似度 (0=無関係, 1=同一)
    text_cosine: float = 0.0
    ccl_cosine: float = 0.0


# ============================================================
# Phase 1: 関数抽出 + CCL 変換
# ============================================================

# PURPOSE: Python コードベースから medium 関数を抽出
def extract_functions(
    target_root: Path,
    max_functions: int = 200,
    min_stmts: int = 4,
    max_stmts: int = 10,
    seed: int = 42,
) -> list[FunctionInfo]:
    """指定ディレクトリ配下から medium サイズの関数を抽出し CCL に変換する。

    テストファイル (test_*.py) は除外。
    """
    # 除外ディレクトリパターン (外部パッケージ混入防止)
    _EXCLUDE_DIRS = {".venv", "venv", "node_modules", "__pycache__",
                     ".git", "site-packages", ".tox", ".eggs", "dist", "build"}
    candidates = []

    for py_file in sorted(target_root.rglob("*.py")):
        # 除外ディレクトリ内のファイルをスキップ
        if any(part in _EXCLUDE_DIRS for part in py_file.parts):
            continue
        # テストファイルを除外
        if py_file.name.startswith("test_"):
            continue
        if "/tests/" in str(py_file):
            continue

        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        lines = source.splitlines()

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # docstring を除いた実文の数
            real_stmts = [
                s for s in node.body
                if not (
                    isinstance(s, ast.Expr)
                    and isinstance(getattr(s, "value", None), ast.Constant)
                    and isinstance(s.value.value, str)
                )
            ]
            n = len(real_stmts)
            if n < min_stmts or n > max_stmts:
                continue

            # ソースコード抽出
            try:
                start = node.lineno - 1
                end = node.end_lineno if hasattr(node, "end_lineno") and node.end_lineno else start + 1
                func_source = "\n".join(lines[start:end])
            except (IndexError, AttributeError):
                continue

            # CCL 変換
            try:
                ccl = python_to_ccl(node)
            except Exception:
                continue

            if not ccl or ccl == "_":
                continue

            # 制御フロー要素の抽出
            cf = _extract_control_flow(node)

            # AST ノード型の抽出
            node_types = _extract_ast_node_types(node)

            rel_path = str(py_file.relative_to(target_root))

            candidates.append(FunctionInfo(
                name=f"{py_file.stem}.{node.name}",
                file_path=rel_path,
                source=func_source,
                ccl=ccl,
                stmt_count=n,
                control_flow=cf,
                ast_node_types=node_types,
            ))

    # ランダムサンプリング (再現性のため seed 固定)
    if len(candidates) > max_functions:
        random.seed(seed)
        candidates = random.sample(candidates, max_functions)

    return candidates


# PURPOSE: 関数から制御フロー要素を抽出 (CCL 非依存, multiset)
def _extract_control_flow(node: ast.AST) -> dict:
    """AST ノードから制御フロー構造を multiset (出現回数込み) で抽出する。

    v2: set → Counter。{if, return, for} のような粗い集合では
    弁別力が低い (ユニーク率 32%)。出現回数を含めることで
    弁別力を大幅に向上させる。
    """
    from collections import Counter
    elements = Counter()
    CF_MAP = {
        ast.If: "if", ast.For: "for", ast.While: "while",
        ast.Try: "try", ast.With: "with", ast.Return: "return",
        ast.Yield: "yield", ast.YieldFrom: "yield_from",
        ast.Raise: "raise", ast.Assert: "assert",
        ast.ListComp: "listcomp", ast.DictComp: "dictcomp",
        ast.SetComp: "setcomp", ast.GeneratorExp: "genexpr",
        ast.AsyncFor: "async_for", ast.AsyncWith: "async_with",
    }
    for child in ast.walk(node):
        for ast_type, label in CF_MAP.items():
            if isinstance(child, ast_type):
                elements[label] += 1
                break
    return dict(elements)


# PURPOSE: AST ノード型のシーケンスを抽出 (CCL 非依存, Deep 走査)
def _extract_ast_node_types(node: ast.AST) -> list[str]:
    """関数の全 AST ノード型のシーケンス (DFS 順)。

    v2: body トップレベルのみ → 全ノード走査。
    情報量が 23x 増加 (平均 6→141 要素)。
    弁別力を大幅に向上させる。
    """
    types = []
    for child in ast.walk(node):
        # Module, docstring Constant はスキップ
        if isinstance(child, ast.Module):
            continue
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            # docstring 等の文字列定数はノイズなので除外
            continue
        types.append(type(child).__name__)
    return types


# ============================================================
# Phase 2: 構造距離計算
# ============================================================

# PURPOSE: AST 構造距離 (CCL 非依存)
def ast_structural_distance(a: FunctionInfo, b: FunctionInfo) -> float:
    """2つの関数の AST ノード型シーケンスの正規化編集距離。

    Levenshtein 距離をシーケンス長で正規化。
    CCL に依存しない独立指標。
    """
    seq_a = a.ast_node_types
    seq_b = b.ast_node_types
    return _normalized_levenshtein(seq_a, seq_b)


# PURPOSE: 制御フロー距離 (CCL 非依存, multiset Jaccard)
def control_flow_distance(a: FunctionInfo, b: FunctionInfo) -> float:
    """2つの関数の制御フロー要素の multiset Jaccard 距離。

    v2: set Jaccard → multiset Jaccard。
    出現回数を考慮することで弁別力を向上。
    J(A,B) = Σ min(a_i, b_i) / Σ max(a_i, b_i)
    CCL に依存しない独立指標。
    """
    cf_a = a.control_flow  # dict: {element: count}
    cf_b = b.control_flow
    if not cf_a and not cf_b:
        return 0.0
    all_keys = set(cf_a.keys()) | set(cf_b.keys())
    if not all_keys:
        return 0.0
    intersection_sum = sum(min(cf_a.get(k, 0), cf_b.get(k, 0)) for k in all_keys)
    union_sum = sum(max(cf_a.get(k, 0), cf_b.get(k, 0)) for k in all_keys)
    if union_sum == 0:
        return 0.0
    return 1.0 - intersection_sum / union_sum


# PURPOSE: CCL 編集距離 (参考指標)
def ccl_edit_distance(a: FunctionInfo, b: FunctionInfo) -> float:
    """2つの関数の CCL 構造式の正規化編集距離。"""
    tokens_a = a.ccl.split()
    tokens_b = b.ccl.split()
    return _normalized_levenshtein(tokens_a, tokens_b)


# .d/.h/.x 展開パターン → 元記法への折り畳みマップ
# 展開ルール (parser.py _parse_workflow):
#   .d (diagonal) = WF + zet
#   .h (horizontal) = WF + bou
#   .x (tension) = WF ~ anti(WF)
_DOT_EXPANSION_MAP = {
    # (展開後トークン列) → 展開前のトークン
    # .d: /WF_/zet → /WF.d
    "d": lambda wf_id: ([f"/{wf_id}", f"/zet"], f"/{wf_id}.d"),
    # .h: /WF_/bou → /WF.h
    "h": lambda wf_id: ([f"/{wf_id}", f"/bou"], f"/{wf_id}.h"),
}


# PURPOSE: .d/.h/.x 展開を折り畳んだ正規化 CCL 距離
def ccl_normalized_distance(a: FunctionInfo, b: FunctionInfo) -> float:
    """2つの関数の CCL 構造式の正規化編集距離 (.d/.h/.x 展開を折り畳み)。

    展開前の記法に戻してからトークン Levenshtein を計算することで、
    `/noe.d` と `/noe_/zet` が同一とみなされる。
    """
    tokens_a = _fold_dot_expansions(a.ccl.split())
    tokens_b = _fold_dot_expansions(b.ccl.split())
    return _normalized_levenshtein(tokens_a, tokens_b)


# PURPOSE: トークン列から .d/.h 展開パターンを検出し折り畳む
def _fold_dot_expansions(tokens: list[str]) -> list[str]:
    """トークン列中の .d/.h 展開パターンを元記法に折り畳む。

    /WF_/zet → /WF.d (diagonal)
    /WF_/bou → /WF.h (horizontal)
    /WF~/anti_WF → /WF.x (tension) — ~ 演算子は別トークンなので個別処理

    折り畳み不可能なトークンはそのまま残す。
    """
    result = []
    i = 0
    while i < len(tokens):
        folded = False
        # 2トークン先読み: /WF _ /zet or /WF _ /bou
        if i + 2 < len(tokens) and tokens[i + 1] == "_":
            wf_token = tokens[i]
            next_token = tokens[i + 2]
            if wf_token.startswith("/"):
                wf_id = wf_token.lstrip("/").rstrip("+-")
                # .d パターン: /WF _ /zet
                if next_token.lstrip("/").rstrip("+-") == "zet":
                    result.append(f"/{wf_id}.d")
                    i += 3
                    folded = True
                # .h パターン: /WF _ /bou
                elif next_token.lstrip("/").rstrip("+-") == "bou":
                    result.append(f"/{wf_id}.h")
                    i += 3
                    folded = True
        # ~ 演算子パターン: /WF ~ /anti_WF → /WF.x
        if not folded and i + 2 < len(tokens) and tokens[i + 1] == "~":
            wf_token = tokens[i]
            anti_token = tokens[i + 2]
            if wf_token.startswith("/"):
                wf_id = wf_token.lstrip("/").rstrip("+-")
                anti_id = anti_token.lstrip("/").rstrip("+-")
                # tension の anti-pair を検出 (同じ族の対を判定)
                # 簡易的: 同じ WF 同士の振動は .x として折り畳む
                if wf_id == anti_id:
                    result.append(f"/{wf_id}.x")
                    i += 3
                    folded = True
        if not folded:
            result.append(tokens[i])
            i += 1
    return result



# PURPOSE: シーケンス間の正規化 Levenshtein 距離
def _normalized_levenshtein(seq_a: list, seq_b: list) -> float:
    """正規化 Levenshtein 距離 (0=同一, 1=完全に異なる)。"""
    n, m = len(seq_a), len(seq_b)
    if n == 0 and m == 0:
        return 0.0
    if n == 0 or m == 0:
        return 1.0

    # DP テーブル
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if seq_a[i - 1] == seq_b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # 削除
                dp[i][j - 1] + 1,      # 挿入
                dp[i - 1][j - 1] + cost  # 置換
            )

    return dp[n][m] / max(n, m)


# ============================================================
# Phase 2b: ペア生成
# ============================================================

# PURPOSE: 関数リストからペアを生成し構造距離を計算
def generate_pairs(
    functions: list[FunctionInfo],
    max_pairs: int = 500,
    seed: int = 42,
) -> list[PairAnalysis]:
    """関数の全組み合わせからサンプリングし、構造距離を計算する。"""
    all_pairs = list(combinations(range(len(functions)), 2))

    # ペア数制限
    if len(all_pairs) > max_pairs:
        random.seed(seed)
        sampled = random.sample(all_pairs, max_pairs)
    else:
        sampled = all_pairs

    pairs = []
    for i, j in sampled:
        fa, fb = functions[i], functions[j]
        pairs.append(PairAnalysis(
            func_a=fa.name,
            func_b=fb.name,
            ast_distance=ast_structural_distance(fa, fb),
            cf_distance=control_flow_distance(fa, fb),
            ccl_edit_distance=ccl_edit_distance(fa, fb),
        ))

    return pairs


# ============================================================
# Phase 3: Embedding + Cosine 類似度
# ============================================================

# PURPOSE: embedding 取得と cosine 計算
def compute_embeddings(
    functions: list[FunctionInfo],
    pairs: list[PairAnalysis],
) -> list[PairAnalysis]:
    """text + CCL の embedding を取得し、ペアごとの cosine を計算する。"""
    # .env を手動ロード (python-dotenv 不要)
    _load_env_file(_HGK_ROOT / ".env")

    # VertexEmbedder 初期化
    try:
        from mekhane.anamnesis.vertex_embedder import VertexEmbedder
        embedder = VertexEmbedder()
    except Exception as e:
        print(f"⚠️ Embedder 初期化失敗: {e}")
        return pairs

    print(f"   Model: {embedder.model_name}, Dim: {embedder._dimension}")

    # 名前→インデックスのマッピング
    name_to_idx = {f.name: i for i, f in enumerate(functions)}

    # text embedding (ソースコード)
    print("📊 Text embedding 取得中...")
    text_inputs = [f.source for f in functions]
    text_embeddings = embedder.embed_batch(text_inputs)

    # CCL embedding
    print("📊 CCL embedding 取得中...")
    ccl_inputs = [f.ccl for f in functions]
    ccl_embeddings = embedder.embed_batch(ccl_inputs)

    # ペアの cosine 計算
    print("📊 Cosine 類似度計算中...")
    try:
        from mekhane.anamnesis.embedder_mixin import cosine_similarity
    except ImportError:
        # フォールバック
        def cosine_similarity(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x ** 2 for x in a))
            norm_b = math.sqrt(sum(x ** 2 for x in b))
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return dot / (norm_a * norm_b)

    for pair in pairs:
        idx_a = name_to_idx.get(pair.func_a)
        idx_b = name_to_idx.get(pair.func_b)
        if idx_a is None or idx_b is None:
            continue
        if text_embeddings[idx_a] and text_embeddings[idx_b]:
            pair.text_cosine = cosine_similarity(text_embeddings[idx_a], text_embeddings[idx_b])
        if ccl_embeddings[idx_a] and ccl_embeddings[idx_b]:
            pair.ccl_cosine = cosine_similarity(ccl_embeddings[idx_a], ccl_embeddings[idx_b])

    return pairs


# ============================================================
# Phase 4: 統計分析
# ============================================================

# PURPOSE: Spearman 順位相関係数の計算
def spearman_rho(x: list[float], y: list[float]) -> float:
    """Spearman 順位相関係数 ρ を計算する。"""
    n = len(x)
    if n < 3:
        return 0.0
    # 順位付け (同順位の平均順位)
    rank_x = _rank(x)
    rank_y = _rank(y)
    # Pearson 相関を順位に適用
    return _pearson(rank_x, rank_y)


def _rank(values: list[float]) -> list[float]:
    """値のリストを順位のリストに変換 (同順位→平均順位)。"""
    n = len(values)
    indexed = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n - 1 and values[indexed[j]] == values[indexed[j + 1]]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[indexed[k]] = avg_rank
        i = j + 1
    return ranks


def _pearson(x: list[float], y: list[float]) -> float:
    """Pearson 相関係数。"""
    n = len(x)
    if n < 2:
        return 0.0
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
    if std_x == 0 or std_y == 0:
        return 0.0
    return cov / (std_x * std_y)


# PURPOSE: Fisher z-test で2つの相関係数の差の有意性を検定
def fisher_z_test(r1: float, r2: float, n: int) -> float:
    """2つの相関係数の差の有意性を p 値で返す。

    H0: ρ1 = ρ2
    """
    if n < 4:
        return 1.0
    # Fisher z 変換
    def fisher_z(r):
        r = max(-0.9999, min(0.9999, r))
        return 0.5 * math.log((1 + r) / (1 - r))

    z1 = fisher_z(r1)
    z2 = fisher_z(r2)
    se = math.sqrt(2.0 / (n - 3))
    z_stat = abs(z1 - z2) / se
    # 正規分布の上側確率の近似
    p_value = math.erfc(z_stat / math.sqrt(2))
    return p_value


# PURPOSE: 統計分析の実行
def analyze_results(pairs: list[PairAnalysis]) -> dict:
    """Spearman 相関 + Fisher z-test を計算する。"""
    # 構造距離 → 類似度に変換 (距離が小さい = 類似度が高い)
    # cosine は類似度なので、距離と負の相関が期待される
    # → 距離を反転 (1 - distance) して正の相関として扱う
    ast_sim = [1.0 - p.ast_distance for p in pairs]
    cf_sim = [1.0 - p.cf_distance for p in pairs]
    ccl_edit_sim = [1.0 - p.ccl_edit_distance for p in pairs]
    text_cos = [p.text_cosine for p in pairs]
    ccl_cos = [p.ccl_cosine for p in pairs]

    n = len(pairs)

    # Spearman ρ: AST 類似度 vs cosine 類似度
    rho_ast_text = spearman_rho(ast_sim, text_cos)
    rho_ast_ccl = spearman_rho(ast_sim, ccl_cos)

    # Spearman ρ: 制御フロー類似度 vs cosine 類似度
    rho_cf_text = spearman_rho(cf_sim, text_cos)
    rho_cf_ccl = spearman_rho(cf_sim, ccl_cos)

    # Fisher z-test: ρ_CCL vs ρ_Text
    p_ast = fisher_z_test(rho_ast_ccl, rho_ast_text, n)
    p_cf = fisher_z_test(rho_cf_ccl, rho_cf_text, n)

    # 5-bin 層別分析 (AST 距離ベース)
    bins = _bin_analysis(pairs, ast_sim, text_cos, ccl_cos)

    return {
        "n_pairs": n,
        "n_functions": len(set(p.func_a for p in pairs) | set(p.func_b for p in pairs)),
        "spearman": {
            "ast_text": rho_ast_text,
            "ast_ccl": rho_ast_ccl,
            "cf_text": rho_cf_text,
            "cf_ccl": rho_cf_ccl,
        },
        "fisher_z": {
            "p_ast": p_ast,
            "p_cf": p_cf,
        },
        "bins": bins,
        # P3b 判定
        "h1_pass": rho_ast_ccl > 0.3,  # CCL embedding が構造を捉えている
        "h2_pass": rho_ast_ccl > rho_ast_text,  # CCL > Text
        "h3_pass": p_ast < 0.05,  # 統計的に有意
    }


# PURPOSE: 5-bin 層別分析
def _bin_analysis(
    pairs: list[PairAnalysis],
    ast_sim: list[float],
    text_cos: list[float],
    ccl_cos: list[float],
) -> list[dict]:
    """AST 類似度を5等分し、各層でのcosine平均を計算。"""
    n = len(pairs)
    if n < 5:
        return []

    # AST 類似度でソート
    indexed = sorted(range(n), key=lambda i: ast_sim[i])
    bin_size = n // 5
    bins = []

    for b in range(5):
        start = b * bin_size
        end = start + bin_size if b < 4 else n
        indices = indexed[start:end]

        bin_ast = [ast_sim[i] for i in indices]
        bin_text = [text_cos[i] for i in indices]
        bin_ccl = [ccl_cos[i] for i in indices]

        bins.append({
            "bin": b + 1,
            "label": f"{'低' if b < 2 else '中' if b == 2 else '高'}類似",
            "n": len(indices),
            "ast_sim_range": f"{min(bin_ast):.3f}-{max(bin_ast):.3f}",
            "text_cos_mean": sum(bin_text) / len(bin_text) if bin_text else 0,
            "ccl_cos_mean": sum(bin_ccl) / len(bin_ccl) if bin_ccl else 0,
        })

    return bins


# ============================================================
# 結果出力
# ============================================================

# PURPOSE: 結果の表示
def print_results(
    functions: list[FunctionInfo],
    pairs: list[PairAnalysis],
    stats: dict,
    dry_run: bool = False,
):
    """結果を標準出力に表示する。"""
    print()
    print("=" * 80)
    print("  P3b 検証実験 — 実世界コードベース結果")
    print("=" * 80)

    print(f"\n  データ: {stats.get('n_functions', len(functions))} 関数, "
          f"{stats['n_pairs']} ペア")

    # CCL 変換例 (上位5件)
    print("\n  CCL 変換例:")
    for f in functions[:5]:
        name_short = f.name[:35].ljust(35)
        ccl_short = f.ccl[:60] + ("..." if len(f.ccl) > 60 else "")
        print(f"    {name_short} → {ccl_short}")

    if dry_run:
        # dry-run: 距離分布のみ表示
        print("\n  構造距離分布:")
        ast_dists = [p.ast_distance for p in pairs]
        cf_dists = [p.cf_distance for p in pairs]
        ccl_dists = [p.ccl_edit_distance for p in pairs]
        print(f"    AST 距離: min={min(ast_dists):.3f} max={max(ast_dists):.3f} "
              f"mean={sum(ast_dists)/len(ast_dists):.3f}")
        print(f"    CF 距離:  min={min(cf_dists):.3f} max={max(cf_dists):.3f} "
              f"mean={sum(cf_dists)/len(cf_dists):.3f}")
        print(f"    CCL 距離: min={min(ccl_dists):.3f} max={max(ccl_dists):.3f} "
              f"mean={sum(ccl_dists)/len(ccl_dists):.3f}")
        print("\n  [dry-run] embedding なし。--dry-run を外して本実験を実行。")
        return

    # Spearman ρ
    sp = stats["spearman"]
    fz = stats["fisher_z"]

    print("\n" + "-" * 80)
    print("  Spearman 順位相関 (構造類似度 vs cosine 類似度):")
    print(f"    ρ(AST, Text):  {sp['ast_text']:.4f}")
    print(f"    ρ(AST, CCL):   {sp['ast_ccl']:.4f}"
          f"  {'✅' if sp['ast_ccl'] > sp['ast_text'] else '❌'} CCL > Text")
    print(f"    ρ(CF, Text):   {sp['cf_text']:.4f}")
    print(f"    ρ(CF, CCL):    {sp['cf_ccl']:.4f}"
          f"  {'✅' if sp['cf_ccl'] > sp['cf_text'] else '❌'} CCL > Text")

    print(f"\n  Fisher z-test (ρ_CCL vs ρ_Text):")
    print(f"    AST ベース: p={fz['p_ast']:.4f}"
          f"  {'✅ 有意' if fz['p_ast'] < 0.05 else '❌ 非有意'}")
    print(f"    CF ベース:  p={fz['p_cf']:.4f}"
          f"  {'✅ 有意' if fz['p_cf'] < 0.05 else '❌ 非有意'}")

    # 5-bin 層別分析
    if stats.get("bins"):
        print("\n  5-bin 層別分析 (AST 類似度):")
        print(f"  {'Bin':>4} {'ラベル':>6} {'n':>4} {'AST範囲':>15} "
              f"{'Text cos':>10} {'CCL cos':>10} {'Δ':>8}")
        print("  " + "-" * 65)
        for b in stats["bins"]:
            delta = b["ccl_cos_mean"] - b["text_cos_mean"]
            print(f"  {b['bin']:>4} {b['label']:>6} {b['n']:>4} {b['ast_sim_range']:>15} "
                  f"{b['text_cos_mean']:>10.4f} {b['ccl_cos_mean']:>10.4f} "
                  f"{delta:>+8.4f}")

    # P3b 判定
    print("\n" + "=" * 80)
    print("  P3b 判定:")
    print(f"    H1 (ρ_CCL > 0.3):    {'✅' if stats['h1_pass'] else '❌'}"
          f"  ρ={sp['ast_ccl']:.4f}")
    print(f"    H2 (CCL > Text):     {'✅' if stats['h2_pass'] else '❌'}"
          f"  Δρ={sp['ast_ccl'] - sp['ast_text']:+.4f}")
    print(f"    H3 (p < 0.05):       {'✅' if stats['h3_pass'] else '❌'}"
          f"  p={fz['p_ast']:.4f}")

    all_pass = stats["h1_pass"] and stats["h2_pass"] and stats["h3_pass"]
    if all_pass:
        print("\n  → P3b 支持 [確信度: 確信 — 実世界コードベース + 統計的有意]")
    elif stats["h1_pass"] and stats["h2_pass"]:
        print("\n  → P3b 部分支持 [推定 — H1/H2 通過、H3 未達]")
    else:
        print("\n  → P3b 未支持 [要検討]")
    print()


# PURPOSE: 結果をファイルに保存
def save_results(
    functions: list[FunctionInfo],
    pairs: list[PairAnalysis],
    stats: dict,
    output_path: Path,
):
    """結果を Markdown ファイルに保存する。"""
    sp = stats["spearman"]
    fz = stats["fisher_z"]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# P3b 検証実験結果 — 実世界コードベース\n\n")
        f.write(f"**実行日時**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        f.write("## データ\n\n")
        f.write(f"- 関数数: {stats.get('n_functions', len(functions))}\n")
        f.write(f"- ペア数: {stats['n_pairs']}\n")
        f.write(f"- データソース: mekhane/ (medium 4-10 stmts)\n\n")

        f.write("## Spearman 順位相関\n\n")
        f.write("| 基準距離 | ρ(Text) | ρ(CCL) | Δρ | Fisher p |\n")
        f.write("|:--|--:|--:|--:|--:|\n")
        f.write(f"| AST 構造距離 | {sp['ast_text']:.4f} | **{sp['ast_ccl']:.4f}** | "
                f"{sp['ast_ccl'] - sp['ast_text']:+.4f} | {fz['p_ast']:.4f} |\n")
        f.write(f"| 制御フロー距離 | {sp['cf_text']:.4f} | **{sp['cf_ccl']:.4f}** | "
                f"{sp['cf_ccl'] - sp['cf_text']:+.4f} | {fz['p_cf']:.4f} |\n\n")

        if stats.get("bins"):
            f.write("## 5-bin 層別分析\n\n")
            f.write("| Bin | n | AST 範囲 | Text cos | CCL cos | Δ |\n")
            f.write("|--:|--:|:--|--:|--:|--:|\n")
            for b in stats["bins"]:
                delta = b["ccl_cos_mean"] - b["text_cos_mean"]
                f.write(f"| {b['bin']} | {b['n']} | {b['ast_sim_range']} | "
                        f"{b['text_cos_mean']:.4f} | {b['ccl_cos_mean']:.4f} | {delta:+.4f} |\n")
            f.write("\n")

        f.write("## P3b 判定\n\n")
        f.write(f"- H1 (ρ_CCL > 0.3): {'✅' if stats['h1_pass'] else '❌'} "
                f"ρ={sp['ast_ccl']:.4f}\n")
        f.write(f"- H2 (CCL > Text): {'✅' if stats['h2_pass'] else '❌'} "
                f"Δρ={sp['ast_ccl'] - sp['ast_text']:+.4f}\n")
        f.write(f"- H3 (p < 0.05): {'✅' if stats['h3_pass'] else '❌'} "
                f"p={fz['p_ast']:.4f}\n")

    print(f"💾 結果を保存: {output_path}")


# ============================================================
# メインエントリ
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="P3b 実世界コードベース CCL embedding 検証")
    parser.add_argument("--dry-run", action="store_true", help="embedding なしで構造距離のみ計算")
    parser.add_argument("-n", "--max-functions", type=int, default=200,
                        help="抽出する最大関数数 (デフォルト: 200)")
    parser.add_argument("--max-pairs", type=int, default=500,
                        help="分析する最大ペア数 (デフォルト: 500)")
    parser.add_argument("--target-dir", type=str, default=None,
                        help="対象ディレクトリ (デフォルト: mekhane/)")
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細出力")
    args = parser.parse_args()

    # ターゲットディレクトリの解決
    if args.target_dir:
        target_root = Path(args.target_dir)
        if not target_root.exists():
            print(f"❌ ディレクトリが見つかりません: {target_root}")
            sys.exit(1)
    else:
        target_root = _MEKHANE_SRC / "mekhane"
        if not target_root.exists():
            print(f"❌ mekhane ディレクトリが見つかりません: {target_root}")
            sys.exit(1)

    print(f"🎯 対象: {target_root}")

    # Phase 1: 関数抽出 + CCL 変換
    print(f"📋 Phase 1: 関数抽出 (max {args.max_functions})...")
    functions = extract_functions(target_root, max_functions=args.max_functions)
    print(f"   抽出: {len(functions)} 関数")

    if len(functions) < 10:
        print("❌ 関数数が不十分 (最低 10 必要)")
        sys.exit(1)

    # Phase 2: ペア生成 + 構造距離計算
    print(f"📋 Phase 2: ペア生成 + 構造距離計算...")
    pairs = generate_pairs(functions, max_pairs=args.max_pairs)
    print(f"   ペア: {len(pairs)}")

    if args.dry_run:
        stats = {"n_pairs": len(pairs), "n_functions": len(functions)}
        print_results(functions, pairs, stats, dry_run=True)
        return

    # Phase 3: Embedding + Cosine 類似度
    print(f"📊 Phase 3: Embedding 取得中...")
    pairs = compute_embeddings(functions, pairs)

    # Phase 4: 統計分析
    print(f"📊 Phase 4: 統計分析...")
    stats = analyze_results(pairs)

    # 結果出力
    print_results(functions, pairs, stats)

    output_path = Path(__file__).parent / "p3b_results.md"
    save_results(functions, pairs, stats, output_path)


if __name__ == "__main__":
    main()
