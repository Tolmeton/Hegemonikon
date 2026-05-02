#!/usr/bin/env python3
# PROOF: [L2/実験] <- 60_実験｜Peira/07_CCL-PL Phase B v2 データセット生成
"""
Phase B v2 データセット生成器

v1 の弱点を解消:
  - 手書き35ペア → 実コードから自動抽出 N≥200ペア
  - HGK + GitHub public repos の混合
  - ペア独立性保証 (各関数は最大1ペアにのみ出現)
  - Hard negative 含む (長さ一致 + 構造異なる)
  - メタデータ豊富 (長さ, 複雑度, ネスト深度 etc.)

Usage:
  python p3a_v2_dataset.py --output dataset_v2.json
  python p3a_v2_dataset.py --stats  # 統計のみ表示
"""

# PURPOSE: 実コードベースから構造プローブ用のペアデータセットを自動生成

import sys
import os
import ast
import json
import random
import argparse
import textwrap
import urllib.request
import zipfile
import tempfile
import io
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from collections import defaultdict

# パス設定
_HGK_ROOT = Path(__file__).parent.parent.parent
_MEKHANE_SRC = _HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"


# ============================================================
# §0. CCL 変換関数 (code_ingest.py からスタンドアロンでコピー)
#     ast モジュールのみに依存する純粋関数群
#     原典: mekhane/symploke/code_ingest.py L64-344
# ============================================================

# PURPOSE: 二項演算子を CCL に変換
def _op_to_ccl(op: ast.operator) -> str:
    """二項演算子を CCL に変換。"""
    op_map = {
        ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
        ast.Mod: "%", ast.Pow: "**", ast.FloorDiv: "//",
        ast.BitOr: "|", ast.BitAnd: "&", ast.BitXor: "^",
        ast.LShift: "<<", ast.RShift: ">>",
    }
    return op_map.get(type(op), "op")


# PURPOSE: 関数呼出の関数部分をラベル化
def _get_func_label(node: ast.expr) -> str:
    """関数呼出の関数部分をラベル化。組込み/標準ライブラリは名前を残す。"""
    if isinstance(node, ast.Name):
        builtins_set = {
            "len", "sorted", "reversed", "enumerate", "zip", "map", "filter",
            "sum", "min", "max", "any", "all", "range", "list", "dict",
            "set", "tuple", "str", "int", "float", "bool", "print",
            "isinstance", "hasattr", "getattr", "setattr", "type",
            "open", "iter", "next",
        }
        if node.id in builtins_set:
            return node.id
        return "fn"
    elif isinstance(node, ast.Attribute):
        common_methods = {
            "append", "extend", "insert", "pop", "remove",
            "get", "set", "update", "items", "keys", "values",
            "join", "split", "strip", "replace", "format",
            "read", "write", "close", "seek",
            "encode", "decode",
            "startswith", "endswith", "find",
        }
        if node.attr in common_methods:
            return f".{node.attr}"
        return ".method"
    return "fn"


# PURPOSE: AST の式 (expression) を CCL 構造式に変換
def _expr_to_ccl(node: ast.expr) -> str:
    """AST の式ノードを CCL 構造式に変換。"""
    if node is None:
        return "_"

    if isinstance(node, ast.Call):
        args_ccl = [_expr_to_ccl(a) for a in node.args]
        if len(args_ccl) == 0:
            args_str = "_"
        elif len(args_ccl) == 1:
            args_str = args_ccl[0]
        else:
            args_str = f"({' % '.join(args_ccl)})"
        func_name = _get_func_label(node.func)
        return f"{args_str} >> {func_name}"

    elif isinstance(node, ast.BinOp):
        left = _expr_to_ccl(node.left)
        right = _expr_to_ccl(node.right)
        op = _op_to_ccl(node.op)
        return f"({left} {op} {right})"

    elif isinstance(node, ast.Compare):
        left = _expr_to_ccl(node.left)
        return f"{left} >> pred"

    elif isinstance(node, ast.BoolOp):
        values = [_expr_to_ccl(v) for v in node.values]
        op = "&" if isinstance(node.op, ast.And) else "|"
        return f"({f' {op} '.join(values)})"

    elif isinstance(node, ast.UnaryOp):
        operand = _expr_to_ccl(node.operand)
        if isinstance(node.op, ast.Not):
            return f"\\{operand}"
        return operand

    elif isinstance(node, ast.ListComp):
        target = _expr_to_ccl(node.elt)
        parts = []
        for gen in node.generators:
            iter_ccl = _expr_to_ccl(gen.iter)
            parts.append(iter_ccl)
            for if_clause in gen.ifs:
                parts.append(f"V:{{{_expr_to_ccl(if_clause)}}}")
        parts.append(f"F:[each]{{{target}}}")
        return " >> ".join(parts)

    elif isinstance(node, (ast.SetComp, ast.GeneratorExp)):
        target = _expr_to_ccl(node.elt)
        parts = []
        for gen in node.generators:
            iter_ccl = _expr_to_ccl(gen.iter)
            parts.append(iter_ccl)
        parts.append(f"F:[each]{{{target}}}")
        return " >> ".join(parts)

    elif isinstance(node, ast.DictComp):
        key = _expr_to_ccl(node.key)
        val = _expr_to_ccl(node.value)
        parts = []
        for gen in node.generators:
            parts.append(_expr_to_ccl(gen.iter))
        parts.append(f"F:[each]{{({key} % {val})}}")
        return " >> ".join(parts)

    elif isinstance(node, ast.Lambda):
        body = _expr_to_ccl(node.body)
        return f"L:[_]{{{body}}}"

    elif isinstance(node, ast.IfExp):
        cond = _expr_to_ccl(node.test)
        then = _expr_to_ccl(node.body)
        else_ = _expr_to_ccl(node.orelse)
        return f"{cond} >> I:[ok]{{{then}}} E:{{{else_}}}"

    elif isinstance(node, (ast.Tuple, ast.List)):
        elts = [_expr_to_ccl(e) for e in node.elts]
        return f"({' % '.join(elts)})" if elts else "_"

    elif isinstance(node, ast.Dict):
        pairs = []
        for k, v in zip(node.keys, node.values):
            if k is not None:
                pairs.append(f"({_expr_to_ccl(k)} % {_expr_to_ccl(v)})")
        return f"({' * '.join(pairs)})" if pairs else "_"

    elif isinstance(node, ast.Subscript):
        return f"{_expr_to_ccl(node.value)} >> [idx]"

    elif isinstance(node, ast.Attribute):
        return f"{_expr_to_ccl(node.value)} >> .attr"

    elif isinstance(node, ast.Starred):
        return f"*{_expr_to_ccl(node.value)}"

    elif isinstance(node, ast.JoinedStr):
        return "format"

    elif isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return "str_"
        elif isinstance(node.value, (int, float)):
            return "num_"
        elif isinstance(node.value, bool):
            return "bool_"
        elif node.value is None:
            return "nil_"
        return "const_"

    elif isinstance(node, ast.Name):
        return "_"

    elif isinstance(node, ast.Await):
        return f"await >> {_expr_to_ccl(node.value)}"

    return "_"


# PURPOSE: AST の文ノードを CCL 構造式に変換（忘却関手 U）
def _stmt_to_ccl(node: ast.stmt) -> str:
    """AST の文ノードを CCL 構造式に変換。名前を忘却し構造のみ残す。"""
    if isinstance(node, ast.Return):
        if node.value:
            return f">> {_expr_to_ccl(node.value)}"
        return ">> return"

    elif isinstance(node, ast.Assign):
        value_ccl = _expr_to_ccl(node.value)
        return value_ccl

    elif isinstance(node, (ast.AugAssign,)):
        return f">> {_expr_to_ccl(node.value)}"

    elif isinstance(node, ast.For):
        iter_ccl = _expr_to_ccl(node.iter)
        body_parts = [c for s in node.body if (c := _stmt_to_ccl(s))]
        body_ccl = " >> ".join(body_parts) if body_parts else "..."
        return f"{iter_ccl} >> F:[each]{{{body_ccl}}}"

    elif isinstance(node, ast.While):
        cond_ccl = _expr_to_ccl(node.test)
        body_parts = [c for s in node.body if (c := _stmt_to_ccl(s))]
        body_ccl = " >> ".join(body_parts) if body_parts else "..."
        return f"C:*{{{cond_ccl} >> {body_ccl}}}"

    elif isinstance(node, ast.If):
        cond_ccl = _expr_to_ccl(node.test)
        then_parts = [c for s in node.body if (c := _stmt_to_ccl(s))]
        then_ccl = " >> ".join(then_parts) if then_parts else "..."
        if node.orelse:
            else_parts = [c for s in node.orelse if (c := _stmt_to_ccl(s))]
            else_ccl = " >> ".join(else_parts) if else_parts else "..."
            return f"{cond_ccl} >> I:[ok]{{{then_ccl}}} E:{{{else_ccl}}}"
        return f"{cond_ccl} >> I:[ok]{{{then_ccl}}}"

    elif isinstance(node, ast.Try):
        body_parts = [c for s in node.body if (c := _stmt_to_ccl(s))]
        body_ccl = " >> ".join(body_parts) if body_parts else "..."
        handler_parts = []
        for h in node.handlers:
            h_parts = [c for s in h.body if (c := _stmt_to_ccl(s))]
            handler_parts.extend(h_parts)
        handler_ccl = " >> ".join(handler_parts) if handler_parts else "recover"
        return f"{body_ccl} >> C:{{{handler_ccl}}}"

    elif isinstance(node, ast.With):
        body_parts = [c for s in node.body if (c := _stmt_to_ccl(s))]
        body_ccl = " >> ".join(body_parts) if body_parts else "..."
        return f"scope{{{body_ccl}}}"

    elif isinstance(node, ast.Expr):
        return _expr_to_ccl(node.value)

    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return "[def]"

    elif isinstance(node, ast.Yield):
        return f">> !{_expr_to_ccl(node.value)}" if node.value else ">> !yield"

    elif isinstance(node, ast.YieldFrom):
        return f">> !*{_expr_to_ccl(node.value)}"

    return ""


# PURPOSE: 関数の AST 全体を CCL 構造式に変換する忘却関手 U
def python_to_ccl(func_node: ast.FunctionDef) -> str:
    """関数の AST 全体を CCL 構造式に変換。名前・変数名を忘れ、射 (構造) のみを残す。"""
    parts = []
    for stmt in func_node.body:
        if isinstance(stmt, ast.Expr) and isinstance(getattr(stmt, 'value', None), ast.Constant):
            if isinstance(stmt.value.value, str):
                continue
        ccl = _stmt_to_ccl(stmt)
        if ccl:
            parts.append(ccl)

    if not parts:
        return "_"

    return " >> ".join(parts)


# ============================================================
# §1. Zhang-Shasha Tree Edit Distance (純粋Python実装)
# ============================================================

# PURPOSE: AST を簡略化したラベル付き木に変換
@dataclass
class SimpleNode:
    """ラベル付き木のノード。Zhang-Shasha 用。"""
    label: str
    children: list = field(default_factory=list)


# PURPOSE: Python AST → SimpleNode に変換 (名前を忘却)
def ast_to_simple_tree(node: ast.AST) -> SimpleNode:
    """AST ノードを構造ラベルのみの SimpleNode に変換。

    変数名・関数名は全て忘却し、ノードタイプ + 構造だけを保持。
    → python_to_ccl と独立した忘却関手。
    """
    label = type(node).__name__

    # 構造的に重要な属性のみ追加
    if isinstance(node, ast.BoolOp):
        label += f":{type(node.op).__name__}"
    elif isinstance(node, ast.BinOp):
        label += f":{type(node.op).__name__}"
    elif isinstance(node, ast.UnaryOp):
        label += f":{type(node.op).__name__}"
    elif isinstance(node, ast.Compare):
        ops = "+".join(type(o).__name__ for o in node.ops)
        label += f":{ops}"

    children = []
    for child in ast.iter_child_nodes(node):
        children.append(ast_to_simple_tree(child))

    return SimpleNode(label=label, children=children)


# PURPOSE: Zhang-Shasha Tree Edit Distance
def tree_edit_distance(t1: SimpleNode, t2: SimpleNode) -> int:
    """Zhang-Shasha TED アルゴリズム O(n^2 m^2)。

    参考: Zhang & Shasha (1989) "Simple Fast Algorithms for the
    Editing Distance between Trees and Related Problems"
    """
    # 木を left-most leaf descriptor 形式に変換
    def _index_tree(node):
        """木を post-order で走査し、ノードリスト・左端葉・キー根を構築。"""
        nodes = []  # post-order ノードリスト
        leftmost = []  # 各ノードの左端葉 (post-order index)
        keyroots = set()  # キー根の集合

        def _post_order(n, depth=0):
            """再帰的 post-order traversal。"""
            if not n.children:
                idx = len(nodes)
                nodes.append(n)
                leftmost.append(idx)  # 葉の左端葉は自分自身
                return idx
            # 子を再帰
            child_indices = []
            for c in n.children:
                ci = _post_order(c, depth + 1)
                child_indices.append(ci)
            idx = len(nodes)
            nodes.append(n)
            leftmost.append(leftmost[child_indices[0]])  # 最左の子の左端葉
            return idx

        root_idx = _post_order(node)
        # キー根の計算: 左端葉が異なるノード + ルート
        seen_leftmost = set()
        for i in range(len(nodes) - 1, -1, -1):
            if leftmost[i] not in seen_leftmost:
                keyroots.add(i)
                seen_leftmost.add(leftmost[i])

        return nodes, leftmost, sorted(keyroots)

    nodes1, lml1, kr1 = _index_tree(t1)
    nodes2, lml2, kr2 = _index_tree(t2)
    n1 = len(nodes1)
    n2 = len(nodes2)

    # コスト関数
    def _cost_del(_n):
        return 1

    def _cost_ins(_n):
        return 1

    def _cost_ren(n_a, n_b):
        return 0 if n_a.label == n_b.label else 1

    # TD テーブル (tree distance)
    td = [[0] * (n2 + 1) for _ in range(n1 + 1)]
    # FD テーブル (forest distance) — キー根ペアごとに計算
    for kr_i in kr1:
        for kr_j in kr2:
            # FD テーブルのサイズ
            i_start = lml1[kr_i]
            j_start = lml2[kr_j]
            fd_rows = kr_i - i_start + 2
            fd_cols = kr_j - j_start + 2
            fd = [[0] * fd_cols for _ in range(fd_rows)]

            # 初期化
            for i in range(1, fd_rows):
                fd[i][0] = fd[i - 1][0] + _cost_del(nodes1[i_start + i - 1])
            for j in range(1, fd_cols):
                fd[0][j] = fd[0][j - 1] + _cost_ins(nodes2[j_start + j - 1])

            for i in range(1, fd_rows):
                for j in range(1, fd_cols):
                    ni = i_start + i - 1  # 実際のノードインデックス
                    nj = j_start + j - 1
                    cost_d = fd[i - 1][j] + _cost_del(nodes1[ni])
                    cost_i = fd[i][j - 1] + _cost_ins(nodes2[nj])

                    if lml1[ni] == lml1[kr_i] and lml2[nj] == lml2[kr_j]:
                        # 両方が同じ左端葉を共有 → 木同士の比較
                        cost_r = fd[i - 1][j - 1] + _cost_ren(nodes1[ni], nodes2[nj])
                        fd[i][j] = min(cost_d, cost_i, cost_r)
                        td[ni + 1][nj + 1] = fd[i][j]
                    else:
                        # 部分forest の比較 → 既計算の td を使用
                        i_off = lml1[ni] - i_start
                        j_off = lml2[nj] - j_start
                        cost_r = fd[i_off][j_off] + td[ni + 1][nj + 1]
                        fd[i][j] = min(cost_d, cost_i, cost_r)

    return td[n1][n2]


# PURPOSE: 正規化 TED
def normalized_ted(t1: SimpleNode, t2: SimpleNode) -> float:
    """正規化 Tree Edit Distance (0=同一, 1=完全不一致)。"""
    def _tree_size(n: SimpleNode) -> int:
        return 1 + sum(_tree_size(c) for c in n.children)

    s1 = _tree_size(t1)
    s2 = _tree_size(t2)
    if s1 == 0 and s2 == 0:
        return 0.0
    ted = tree_edit_distance(t1, t2)
    return ted / max(s1, s2)


# ============================================================
# §2. 関数メタデータ
# ============================================================

# PURPOSE: 1つの関数の全メタデータ
@dataclass
class FunctionMeta:
    """抽出された関数の全メタデータ。"""
    func_id: str                  # ユニーク ID
    source: str                   # ソースコード文字列
    source_file: str              # 元ファイルパス
    source_origin: str            # "hgk" or "github:{repo}"
    func_name: str                # 関数名 (忘却前)
    # --- メタデータ ---
    code_length: int              # 文字数
    line_count: int               # 行数
    ast_node_count: int           # AST ノード数 (複雑度代理)
    max_nesting_depth: int        # 最大ネスト深度
    cyclomatic_complexity: int    # McCabe 循環的複雑度 (分岐+1)
    n_parameters: int             # パラメータ数
    # --- 構造 ---
    ccl: str                      # python_to_ccl の結果
    ast_tree: Optional[SimpleNode] = field(default=None, repr=False)  # TED 用


# PURPOSE: AST ノード数を計算
def _count_ast_nodes(node: ast.AST) -> int:
    """AST のノード数。"""
    return 1 + sum(_count_ast_nodes(c) for c in ast.iter_child_nodes(node))


# PURPOSE: 最大ネスト深度を計算
def _max_nesting(node: ast.AST, depth: int = 0) -> int:
    """制御構造の最大ネスト深度。"""
    nesting_nodes = (ast.For, ast.While, ast.If, ast.With, ast.Try)
    max_d = depth
    for child in ast.iter_child_nodes(node):
        child_depth = depth + 1 if isinstance(child, nesting_nodes) else depth
        max_d = max(max_d, _max_nesting(child, child_depth))
    return max_d


# PURPOSE: McCabe 循環的複雑度
def _cyclomatic_complexity(node: ast.AST) -> int:
    """McCabe's cyclomatic complexity = 分岐数 + 1。"""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(child, ast.BoolOp) and isinstance(child.op, ast.And):
            complexity += len(child.values) - 1
        elif isinstance(child, ast.BoolOp) and isinstance(child.op, ast.Or):
            complexity += len(child.values) - 1
    return complexity


# PURPOSE: FunctionDef → FunctionMeta に変換
def extract_function_meta(
    node: ast.FunctionDef,
    source: str,
    source_file: str,
    origin: str,
    func_id: str,
) -> Optional[FunctionMeta]:
    """FunctionDef ノードから FunctionMeta を生成。"""
    try:
        ccl = python_to_ccl(node)
    except Exception:
        ccl = "_"

    if ccl == "_" or len(ccl.strip()) < 3:
        return None  # 空 CCL は除外

    try:
        ast_tree = ast_to_simple_tree(node)
    except RecursionError:
        ast_tree = SimpleNode(label="<too_deep>")

    return FunctionMeta(
        func_id=func_id,
        source=source,
        source_file=source_file,
        source_origin=origin,
        func_name=node.name,
        code_length=len(source),
        line_count=source.count("\n") + 1,
        ast_node_count=_count_ast_nodes(node),
        max_nesting_depth=_max_nesting(node),
        cyclomatic_complexity=_cyclomatic_complexity(node),
        n_parameters=len(node.args.args),
        ccl=ccl,
        ast_tree=ast_tree,
    )


# ============================================================
# §3. コード収集
# ============================================================

# GitHub の有名 OSS リポジトリ (Python, 小〜中規模)
GITHUB_REPOS = [
    ("psf/requests", "main"),
    ("pallets/click", "main"),
    ("pallets/flask", "main"),
    ("httpie/cli", "master"),
    # Phase B2 拡張 (N≥300 目標)
    ("scikit-learn/scikit-learn", "main"),
    ("psf/black", "main"),
    ("Textualize/rich", "master"),
    ("fastapi/fastapi", "master"),
]

# PURPOSE: 1つのディレクトリから全 Python 関数を抽出
def extract_functions_from_dir(
    directory: Path, origin: str, prefix: str, min_lines: int = 5
) -> list[FunctionMeta]:
    """ディレクトリ内の全 .py ファイルから関数を抽出。"""
    functions = []
    counter = 0

    exclude_dirs = {
        "__pycache__", ".git", "node_modules", ".venv", "venv",
        "dist", "build", ".egg-info", ".mypy_cache", ".pytest_cache",
        "90_保管庫｜Archive", ".system_generated",
    }

    for py_file in sorted(directory.rglob("*.py")):
        # 除外ディレクトリのチェック
        if any(ex in py_file.parts for ex in exclude_dirs):
            continue

        try:
            source_text = py_file.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source_text)
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # ソースコードの抽出
            try:
                func_source = ast.get_source_segment(source_text, node)
            except Exception:
                func_source = None

            if func_source is None:
                # フォールバック: 行番号ベース
                lines = source_text.split("\n")
                if hasattr(node, "end_lineno") and node.end_lineno:
                    func_source = "\n".join(
                        lines[node.lineno - 1 : node.end_lineno]
                    )
                else:
                    continue

            if func_source.count("\n") + 1 < min_lines:
                continue

            counter += 1
            func_id = f"{prefix}_{counter:04d}"
            meta = extract_function_meta(
                node, func_source, str(py_file.relative_to(directory)),
                origin, func_id,
            )
            if meta:
                functions.append(meta)

    return functions


# PURPOSE: GitHub リポジトリをダウンロードして関数を抽出
def extract_functions_from_github(
    repo: str, branch: str, min_lines: int = 5
) -> list[FunctionMeta]:
    """GitHub リポジトリの zip をダウンロードし関数を抽出。"""
    url = f"https://github.com/{repo}/archive/refs/heads/{branch}.zip"
    print(f"  📥 ダウンロード: {repo} ({branch})...", end=" ", flush=True)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HGK-Probe/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            zip_data = resp.read()
    except Exception as e:
        print(f"❌ {e}")
        return []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        zip_path = tmppath / "repo.zip"
        zip_path.write_bytes(zip_data)

        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmppath)

        # 展開されたディレクトリを探す
        extracted = [d for d in tmppath.iterdir() if d.is_dir() and d.name != "__MACOSX"]
        if not extracted:
            print("❌ 展開失敗")
            return []

        repo_dir = extracted[0]
        repo_short = repo.replace("/", "_")
        prefix = f"gh_{repo_short}"
        origin = f"github:{repo}"

        funcs = extract_functions_from_dir(repo_dir, origin, prefix, min_lines)
        print(f"✅ {len(funcs)} 関数")
        return funcs


# ============================================================
# §4. ペア生成 (Hard Negative 対応)
# ============================================================

# PURPOSE: 正規化 Levenshtein 距離
def normalized_levenshtein(s1: str, s2: str) -> float:
    """正規化 Levenshtein 距離 (0=同一, 1=完全不一致)。"""
    if s1 == s2:
        return 0.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 1.0
    prev = list(range(len2 + 1))
    curr = [0] * (len2 + 1)
    for i in range(1, len1 + 1):
        curr[0] = i
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            curr[j] = min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
        prev, curr = curr, prev
    return prev[len2] / max(len1, len2)


# PURPOSE: ペアデータ
@dataclass
class ProbePair:
    """1つの実験ペア。"""
    pair_id: str
    func_a_id: str
    func_b_id: str
    is_positive: bool             # 構造的に類似 (True) or 異なる (False)
    pair_type: str                # "positive", "easy_neg", "hard_neg_length", "hard_neg_semantic"
    # --- Ground Truth ---
    ccl_distance: float           # CCL 正規化 Levenshtein
    ccl_similarity: float         # 1 - ccl_distance
    ast_ted: float                # 正規化 AST Tree Edit Distance
    ast_similarity: float         # 1 - ast_ted
    # --- 交絡因子 ---
    length_ratio: float           # min(len)/max(len) — 長さの一致度
    complexity_diff: float        # |complexity_a - complexity_b| / max
    nesting_diff: float           # |nesting_a - nesting_b| / max
    # --- 元データ参照 ---
    func_a_source: str = ""
    func_b_source: str = ""
    func_a_ccl: str = ""
    func_b_ccl: str = ""


# PURPOSE: ペアを体系的に生成
def generate_pairs(
    functions: list[FunctionMeta],
    n_positive: int = 100,
    n_easy_neg: int = 34,
    n_hard_neg_len: int = 33,
    n_hard_neg_sem: int = 33,
    seed: int = 42,
    max_reuse: int = 1,
) -> list[ProbePair]:
    """関数のリストからペアを自動生成。

    各関数は最大 max_reuse ペアにのみ出現 (独立性保証)。
    max_reuse=1: 完全独立 (v2 デフォルト)
    max_reuse=2: 緩和独立 (Phase B2 拡張用)
    """
    rng = random.Random(seed)
    used_count: dict[str, int] = {}  # func_id → 使用回数
    pairs = []
    pair_counter = 0

    def _make_pair(fa, fb, pair_type, is_positive, precomputed_ccl_dist=None):
        nonlocal pair_counter
        pair_counter += 1

        ccl_dist = precomputed_ccl_dist if precomputed_ccl_dist is not None else normalized_levenshtein(fa.ccl, fb.ccl)
        # AST TED は遅延計算 (後で _compute_ast_teds で一括)
        ast_sim = 0.0

        max_len = max(fa.code_length, fb.code_length)
        max_cx = max(fa.cyclomatic_complexity, fb.cyclomatic_complexity, 1)
        max_nd = max(fa.max_nesting_depth, fb.max_nesting_depth, 1)

        return ProbePair(
            pair_id=f"V2_{pair_counter:04d}",
            func_a_id=fa.func_id,
            func_b_id=fb.func_id,
            is_positive=is_positive,
            pair_type=pair_type,
            ccl_distance=ccl_dist,
            ccl_similarity=1.0 - ccl_dist,
            ast_ted=ast_sim,
            ast_similarity=1.0 - ast_sim,
            length_ratio=min(fa.code_length, fb.code_length) / max_len if max_len else 1.0,
            complexity_diff=abs(fa.cyclomatic_complexity - fb.cyclomatic_complexity) / max_cx,
            nesting_diff=abs(fa.max_nesting_depth - fb.max_nesting_depth) / max_nd,
            func_a_source=fa.source,
            func_b_source=fb.source,
            func_a_ccl=fa.ccl,
            func_b_ccl=fb.ccl,
        )

    def _try_pair(fa, fb, pair_type, is_positive, precomputed_ccl_dist=None):
        """独立性保証付きでペアを追加 (max_reuse 制約)。"""
        if used_count.get(fa.func_id, 0) >= max_reuse:
            return False
        if used_count.get(fb.func_id, 0) >= max_reuse:
            return False
        if fa.func_id == fb.func_id:
            return False
        p = _make_pair(fa, fb, pair_type, is_positive, precomputed_ccl_dist)
        pairs.append(p)
        used_count[fa.func_id] = used_count.get(fa.func_id, 0) + 1
        used_count[fb.func_id] = used_count.get(fb.func_id, 0) + 1
        return True

    # --- 正例: CCL 距離が近いペア ---
    print(f"\n📍 正例ペア生成 (目標: {n_positive})...")
    # CCL の先頭トークンでブロッキングし、同一ブロック内のみ比較 (O(N²)回避)
    candidates = list(functions)
    rng.shuffle(candidates)

    positive_candidates = []
    sample_size = min(len(candidates), 500)
    sampled = candidates[:sample_size]

    # ブロッキング: CCL の先頭30文字でグループ化
    from collections import defaultdict as _dd
    blocks = _dd(list)
    for f in sampled:
        key = f.ccl[:15] if f.ccl else ""
        blocks[key].append(f)

    # ブロック内で比較 (同一先頭CCL = 構造類似の可能性が高い)
    checked = 0
    for key, group in blocks.items():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                fa, fb = group[i], group[j]
                ccl_dist = normalized_levenshtein(fa.ccl, fb.ccl)
                checked += 1
                if ccl_dist < 0.3:
                    positive_candidates.append((ccl_dist, fa, fb))
    print(f"  ブロッキング比較: {checked} ペア (ブルートフォース: {sample_size*(sample_size-1)//2})")

    # ブロッキングで不足した場合、CCL長さ近似でフォールバック
    if len(positive_candidates) < n_positive * 2:
        print(f"  📍 ブロッキング候補不足 ({len(positive_candidates)})、長さ近似フォールバック...")
        # CCL 長さでソートし、近接ペアを比較 (長さが近い = 構造が似ている可能性)
        by_len = sorted(sampled, key=lambda f: len(f.ccl))
        for i in range(len(by_len)):
            for j in range(i + 1, min(i + 5, len(by_len))):
                fa, fb = by_len[i], by_len[j]
                # 長さ比フィルター
                max_ccl_len = max(len(fa.ccl), len(fb.ccl), 1)
                min_ccl_len = min(len(fa.ccl), len(fb.ccl))
                if min_ccl_len / max_ccl_len < 0.7:
                    continue
                ccl_dist = normalized_levenshtein(fa.ccl, fb.ccl)
                if ccl_dist < 0.3:
                    positive_candidates.append((ccl_dist, fa, fb))
        print(f"  → フォールバック後: {len(positive_candidates)} 候補")

    positive_candidates.sort(key=lambda x: x[0])
    pos_count = 0
    for _, fa, fb in positive_candidates:
        if pos_count >= n_positive:
            break
        if _try_pair(fa, fb, "positive", True, precomputed_ccl_dist=_):
            pos_count += 1

    print(f"  → {pos_count} 正例ペア生成")

    # --- Easy Negative: 構造・長さ共に異なる ---
    print(f"📍 Easy Negative (目標: {n_easy_neg})...")
    unused = [f for f in functions if used_count.get(f.func_id, 0) < max_reuse]
    rng.shuffle(unused)
    easy_count = 0
    for i in range(0, len(unused) - 1, 2):
        if easy_count >= n_easy_neg:
            break
        fa, fb = unused[i], unused[i + 1]
        ccl_dist = normalized_levenshtein(fa.ccl, fb.ccl)
        if ccl_dist > 0.7:
            if _try_pair(fa, fb, "easy_neg", False):
                easy_count += 1
    print(f"  → {easy_count} easy negative 生成")

    # --- Hard Negative (長さ一致): 長さ±20%以内だが構造は異なる ---
    print(f"📍 Hard Negative (長さ一致) (目標: {n_hard_neg_len})...")
    unused = [f for f in functions if used_count.get(f.func_id, 0) < max_reuse]
    # 長さでソート
    unused.sort(key=lambda f: f.code_length)
    hard_len_count = 0
    for i in range(len(unused)):
        if hard_len_count >= n_hard_neg_len:
            break
        fa = unused[i]
        if used_count.get(fa.func_id, 0) >= max_reuse:
            continue
        # 近い長さの関数を探す
        for j in range(i + 1, min(i + 20, len(unused))):
            fb = unused[j]
            if used_count.get(fb.func_id, 0) >= max_reuse:
                continue
            len_ratio = min(fa.code_length, fb.code_length) / max(fa.code_length, fb.code_length)
            if len_ratio < 0.8:
                continue  # 長さが20%以上異なる
            ccl_dist = normalized_levenshtein(fa.ccl, fb.ccl)
            if ccl_dist > 0.5:  # 構造は異なる
                if _try_pair(fa, fb, "hard_neg_length", False):
                    hard_len_count += 1
                    break
    print(f"  → {hard_len_count} hard negative (長さ一致) 生成")

    # --- Hard Negative (意味一致): 同じディレクトリ由来だが構造は異なる ---
    print(f"📍 Hard Negative (意味一致) (目標: {n_hard_neg_sem})...")
    unused = [f for f in functions if used_count.get(f.func_id, 0) < max_reuse]
    # ファイル単位でグループ化
    by_dir = defaultdict(list)
    for f in unused:
        dir_name = str(Path(f.source_file).parent)
        by_dir[dir_name].append(f)

    hard_sem_count = 0
    for dir_name, dir_funcs in by_dir.items():
        if hard_sem_count >= n_hard_neg_sem:
            break
        if len(dir_funcs) < 2:
            continue
        rng.shuffle(dir_funcs)
        for i in range(0, len(dir_funcs) - 1, 2):
            if hard_sem_count >= n_hard_neg_sem:
                break
            fa, fb = dir_funcs[i], dir_funcs[i + 1]
            ccl_dist = normalized_levenshtein(fa.ccl, fb.ccl)
            if ccl_dist > 0.4:
                if _try_pair(fa, fb, "hard_neg_semantic", False):
                    hard_sem_count += 1

    print(f"  → {hard_sem_count} hard negative (意味一致) 生成")

    return pairs


# ============================================================
# §5. データセット保存
# ============================================================

# PURPOSE: データセットを JSON に保存 (ast_tree は除外)
def save_dataset(pairs: list[ProbePair], output_path: Path):
    """ペアデータセットを JSON に保存。"""
    data = {
        "version": "v2",
        "n_pairs": len(pairs),
        "n_positive": sum(1 for p in pairs if p.is_positive),
        "n_negative": sum(1 for p in pairs if not p.is_positive),
        "pair_types": {
            t: sum(1 for p in pairs if p.pair_type == t)
            for t in ["positive", "easy_neg", "hard_neg_length", "hard_neg_semantic"]
        },
        "pairs": [asdict(p) for p in pairs],
    }
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n💾 保存: {output_path} ({len(pairs)} ペア)")


# PURPOSE: データセットの統計を表示
def print_stats(pairs: list[ProbePair]):
    """データセットの統計情報を表示。"""
    print(f"\n{'='*60}")
    print(f"  データセット統計")
    print(f"{'='*60}")
    print(f"  合計ペア数: {len(pairs)}")

    for ptype in ["positive", "easy_neg", "hard_neg_length", "hard_neg_semantic"]:
        subset = [p for p in pairs if p.pair_type == ptype]
        if not subset:
            continue
        ccl_sims = [p.ccl_similarity for p in subset]
        ast_sims = [p.ast_similarity for p in subset]
        len_ratios = [p.length_ratio for p in subset]
        print(f"\n  {ptype} ({len(subset)} ペア):")
        print(f"    CCL 類似度: mean={sum(ccl_sims)/len(ccl_sims):.3f}, "
              f"range=[{min(ccl_sims):.3f}, {max(ccl_sims):.3f}]")
        print(f"    AST 類似度: mean={sum(ast_sims)/len(ast_sims):.3f}, "
              f"range=[{min(ast_sims):.3f}, {max(ast_sims):.3f}]")
        print(f"    長さ比:     mean={sum(len_ratios)/len(len_ratios):.3f}, "
              f"range=[{min(len_ratios):.3f}, {max(len_ratios):.3f}]")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Phase B v2: 構造プローブ用データセット生成"
    )
    parser.add_argument(
        "--output", "-o", type=str, default="dataset_v2.json",
        help="出力ファイルパス (default: dataset_v2.json)",
    )
    parser.add_argument(
        "--no-github", action="store_true",
        help="GitHub リポジトリのダウンロードをスキップ (HGK のみ)",
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="統計のみ表示 (既存 dataset を読込)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="乱数シード (default: 42)",
    )
    parser.add_argument(
        "--min-pairs", type=int, default=300,
        help="最小ペア数 (default: 300)",
    )
    parser.add_argument(
        "--max-reuse", type=int, default=1,
        help="各関数の最大出現ペア数 (1=完全独立, 2=緩和独立)",
    )
    args = parser.parse_args()

    output_path = Path(args.output)

    if args.stats and output_path.exists():
        data = json.loads(output_path.read_text(encoding="utf-8"))
        pairs = [ProbePair(**p) for p in data["pairs"]]
        print_stats(pairs)
        return

    # --- 関数収集 ---
    all_functions = []

    # HGK コードベース
    hgk_src = _MEKHANE_SRC
    print(f"📂 HGK コードベース: {hgk_src}")
    hgk_funcs = extract_functions_from_dir(hgk_src, "hgk", "hgk")
    print(f"  → {len(hgk_funcs)} 関数抽出")
    all_functions.extend(hgk_funcs)

    # Ops ソースコード
    ops_src = _HGK_ROOT / "80_運用｜Ops" / "_src｜ソースコード"
    if ops_src.exists():
        print(f"📂 Ops ソースコード: {ops_src}")
        ops_funcs = extract_functions_from_dir(ops_src, "hgk_ops", "ops")
        print(f"  → {len(ops_funcs)} 関数抽出")
        all_functions.extend(ops_funcs)

    # Peira ソースコード
    peira_src = _HGK_ROOT / "60_実験｜Peira"
    if peira_src.exists():
        print(f"📂 Peira ソースコード: {peira_src}")
        peira_funcs = extract_functions_from_dir(peira_src, "hgk_peira", "peira")
        print(f"  → {len(peira_funcs)} 関数抽出")
        all_functions.extend(peira_funcs)

    # GitHub リポジトリ
    if not args.no_github:
        print(f"\n📦 GitHub リポジトリからの収集:")
        for repo, branch in GITHUB_REPOS:
            gh_funcs = extract_functions_from_github(repo, branch)
            all_functions.extend(gh_funcs)

    print(f"\n📊 全関数数: {len(all_functions)}")

    # --- ペア生成 ---
    n_total = max(args.min_pairs, 200)
    n_pos = n_total // 2
    n_neg = n_total - n_pos
    n_easy = n_neg // 3
    n_hard_len = n_neg // 3
    n_hard_sem = n_neg - n_easy - n_hard_len

    pairs = generate_pairs(
        all_functions,
        n_positive=n_pos,
        n_easy_neg=n_easy,
        n_hard_neg_len=n_hard_len,
        n_hard_neg_sem=n_hard_sem,
        seed=args.seed,
        max_reuse=args.max_reuse,
    )

    # --- AST TED バッチ計算 (ノード数100以下のみ) ---
    print(f"\n📍 AST TED バッチ計算 ({len(pairs)} ペア)...")
    # func_id → FunctionMeta のルックアップ構築
    func_lookup = {f.func_id: f for f in all_functions}
    ted_computed = 0
    ted_skipped = 0
    for p in pairs:
        fa = func_lookup.get(p.func_a_id)
        fb = func_lookup.get(p.func_b_id)
        if fa and fb and fa.ast_tree and fb.ast_tree:
            # 大きな AST はスキップ (性能)
            if fa.ast_node_count <= 100 and fb.ast_node_count <= 100:
                try:
                    ted_val = normalized_ted(fa.ast_tree, fb.ast_tree)
                    p.ast_ted = ted_val
                    p.ast_similarity = 1.0 - ted_val
                    ted_computed += 1
                except (RecursionError, Exception):
                    ted_skipped += 1
            else:
                ted_skipped += 1
        else:
            ted_skipped += 1
    print(f"  → 計算: {ted_computed}, スキップ: {ted_skipped}")

    # 最終チェック
    actual_total = len(pairs)
    if actual_total < args.min_pairs:
        print(f"\n⚠️ ペア数が目標 ({args.min_pairs}) に未達: {actual_total}")
        print(f"  → 関数数を増やす必要あり (現在 {len(all_functions)} 関数)")

    # 独立性チェック (max_reuse 対応)
    all_func_ids = []
    for p in pairs:
        all_func_ids.extend([p.func_a_id, p.func_b_id])
    from collections import Counter
    id_counts = Counter(all_func_ids)
    violations = {fid: cnt for fid, cnt in id_counts.items() if cnt > args.max_reuse}
    assert not violations, \
        f"独立性違反 (max_reuse={args.max_reuse}): {violations}"
    unique_funcs = len(set(all_func_ids))
    print(f"  ✅ 独立性: {unique_funcs} 関数, 重複なし")

    print_stats(pairs)
    save_dataset(pairs, output_path)


if __name__ == "__main__":
    main()
