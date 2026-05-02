#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/ A0→コード検索が必要→code_ingest が担う
"""
Code Ingest - CCL-IR ベースのコード構造検索

AST で関数/クラスに分割し、CCL 構造式に変換して code.pkl に保存する。
CCL (Cognitive Command Language) は圏論の構文的実現であり、
名前 (対象) を忘却し射 (構造) を保存する忘却関手 U として機能する。

理論的基盤: aletheia.md (U⊣N 随伴), VISION.md (CCL-IR)

Usage:
    python code_ingest.py                    # 全コードを投入
    python code_ingest.py --dry-run          # パースのみ
    python code_ingest.py --incremental      # 差分更新
"""

# PURPOSE: Python ソースコードを AST → CCL 構造式に変換し、ベクトルインデックスに投入

import sys
import os
import ast
import argparse
from pathlib import Path

# プロジェクトルートを PATH に追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from mekhane.paths import ensure_env
    ensure_env()
except ImportError:
    pass

from mekhane.symploke.indices import Document
from mekhane.paths import MEKHANE_DIR, OPS_DIR, PEIRA_DIR, POIEMA_DIR

# スキャン対象ディレクトリ
CODE_SCAN_DIRS: list[tuple[Path, str]] = [
    (MEKHANE_DIR / "_src｜ソースコード", "mekhane"),
    (OPS_DIR / "_src｜ソースコード", "ops"),
    (PEIRA_DIR, "peira"),
    (POIEMA_DIR / "_src｜ソースコード", "poiema"),
]

# 除外パターン
_EXCLUDE_DIRS = {
    "__pycache__", ".git", "node_modules", ".venv", "venv",
    "90_保管庫｜Archive", ".system_generated", "dist", "build",
    ".egg-info", ".mypy_cache", ".pytest_cache",
}

# チャンク化の閾値
_SMALL_FILE_THRESHOLD = 100  # 行数がこれ以下ならファイル全体もチャンク化
_MAX_CHUNK_LINES = 500       # 1チャンクの最大行数
_MIN_CHUNK_LINES = 5         # これ未満の関数は自明すぎるので除外


# ============================================================
# CCL 構造式変換 — 忘却関手 U: Code → CCL
# ============================================================

# PURPOSE: スコープマップを構築 (C3v2 ¥/# トークン体系)
def _build_scope_map(func_node: ast.FunctionDef) -> dict[str, str]:
    """関数のスコープ内変数をデータ出自でトークンにマッピングする。

    ¥ = 引数 (Markov blanket 外部入力)
    # = ローカル変数 (MB 内部状態)
    self/cls は除外。

    CCL operators.md §1.5.5 準拠。
    n=0 (名前) を忘却し、n=1 (データの出自: 外部/内部) を保存する。
    """
    scope_map: dict[str, str] = {}
    # 引数 → ¥ (外部入力)
    for a in func_node.args.args:
        if a.arg in ("self", "cls"):
            continue  # self/cls は構造的に無意味
        scope_map[a.arg] = "¥"
    # *args → ¥
    if func_node.args.vararg:
        scope_map[func_node.args.vararg.arg] = "¥"
    # **kwargs → ¥
    if func_node.args.kwarg:
        scope_map[func_node.args.kwarg.arg] = "¥"
    # keyword-only 引数 → ¥
    for a in func_node.args.kwonlyargs:
        scope_map[a.arg] = "¥"
    # ローカル変数 (代入ターゲット) → #
    for stmt in ast.walk(func_node):
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                for name_node in ast.walk(target):
                    if isinstance(name_node, ast.Name) and name_node.id not in scope_map:
                        scope_map[name_node.id] = "#"
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            if stmt.target.id not in scope_map:
                scope_map[stmt.target.id] = "#"
        elif isinstance(stmt, (ast.For, ast.AsyncFor)):
            for name_node in ast.walk(stmt.target):
                if isinstance(name_node, ast.Name) and name_node.id not in scope_map:
                    scope_map[name_node.id] = "#"
        elif isinstance(stmt, (ast.With, ast.AsyncWith)):
            for item in stmt.items:
                if item.optional_vars:
                    for name_node in ast.walk(item.optional_vars):
                        if isinstance(name_node, ast.Name) and name_node.id not in scope_map:
                            scope_map[name_node.id] = "#"
    return scope_map


# PURPOSE: 代入ターゲットの形状を CCL に変換 (CCL-B3)
def _target_shape(target: ast.expr, arg_map: dict[str, str] | None = None) -> str:
    """代入ターゲットの構造的形状を返す。

    単純な Name → トークン (¥/# またはフォールバック #)、
    Tuple/List → 合成形状、Subscript/Attribute → アクセスパターン。
    """
    if isinstance(target, ast.Name):
        # C3v2: スコープマップに基づきトークンを返す
        if arg_map and target.id in arg_map:
            return arg_map[target.id]
        return "#"  # フォールバック: 未知変数はローカル扱い
    elif isinstance(target, ast.Tuple):
        parts = [_target_shape(e, arg_map) for e in target.elts]
        return f"({' % '.join(parts)})"
    elif isinstance(target, ast.List):
        parts = [_target_shape(e, arg_map) for e in target.elts]
        return f"[{' % '.join(parts)}]"
    elif isinstance(target, ast.Subscript):
        return f"{_expr_to_ccl(target.value, arg_map)} >> [idx]"
    elif isinstance(target, ast.Attribute):
        return f"{_expr_to_ccl(target.value, arg_map)} >> .attr"
    elif isinstance(target, ast.Starred):
        return f"*{_target_shape(target.value, arg_map)}"
    return "#"  # フォールバック: 未知ターゲットはローカル扱い


# PURPOSE: AST の文 (statement) を CCL 構造式に変換
def _stmt_to_ccl(node: ast.stmt, arg_map: dict[str, str] | None = None) -> str:
    """AST の文ノードを CCL 構造式に変換（忘却関手 U）。

    名前・変数名を全て抜き、射の構造だけを残す。
    C3v2: 引数は ¥ (外部入力)、ローカル変数は # (内部状態) で識別。
    """
    if isinstance(node, ast.Return):
        if node.value:
            return f">> {_expr_to_ccl(node.value, arg_map)}"
        return ">> return"

    elif isinstance(node, ast.Assign):
        # x = f(y) → y >> f / (x, y) = f(z) → [T:(_ % _)] >> f(z)
        # CCL-B3: 代入ターゲットの形状を保存 (タプルアンパック等の構造差異)
        value_ccl = _expr_to_ccl(node.value, arg_map)
        if len(node.targets) == 1:
            shape = _target_shape(node.targets[0], arg_map)
            if shape != "#":  # 単純ローカル変数以外は形状を残す
                return f"[T:{shape}] >> {value_ccl}"
        return value_ccl

    elif isinstance(node, (ast.AugAssign,)):
        # x += f(y)
        return f">> {_expr_to_ccl(node.value, arg_map)}"

    elif isinstance(node, ast.For):
        # for x in xs: body → xs >> F:[each]{{body}}
        iter_ccl = _expr_to_ccl(node.iter, arg_map)
        body_parts = [c for s in node.body if (c := _stmt_to_ccl(s, arg_map))]
        body_ccl = " >> ".join(body_parts) if body_parts else "..."
        return f"{iter_ccl} >> F:[each]{{{body_ccl}}}"

    elif isinstance(node, ast.While):
        # while cond: body → C:*{{cond >> body}}
        cond_ccl = _expr_to_ccl(node.test, arg_map)
        body_parts = [c for s in node.body if (c := _stmt_to_ccl(s, arg_map))]
        body_ccl = " >> ".join(body_parts) if body_parts else "..."
        return f"C:*{{{cond_ccl} >> {body_ccl}}}"

    elif isinstance(node, ast.If):
        # if cond: a else: b → cond >> I:[ok]{{a}} E:{{b}}
        cond_ccl = _expr_to_ccl(node.test, arg_map)
        then_parts = [c for s in node.body if (c := _stmt_to_ccl(s, arg_map))]
        then_ccl = " >> ".join(then_parts) if then_parts else "..."
        if node.orelse:
            else_parts = [c for s in node.orelse if (c := _stmt_to_ccl(s, arg_map))]
            else_ccl = " >> ".join(else_parts) if else_parts else "..."
            return f"{cond_ccl} >> I:[ok]{{{then_ccl}}} E:{{{else_ccl}}}"
        return f"{cond_ccl} >> I:[ok]{{{then_ccl}}}"

    elif isinstance(node, ast.Try):
        # try: body except: handler → body >> C:{{handler}}
        body_parts = [c for s in node.body if (c := _stmt_to_ccl(s, arg_map))]
        body_ccl = " >> ".join(body_parts) if body_parts else "..."
        handler_parts = []
        for h in node.handlers:
            h_parts = [c for s in h.body if (c := _stmt_to_ccl(s, arg_map))]
            handler_parts.extend(h_parts)
        handler_ccl = " >> ".join(handler_parts) if handler_parts else "recover"
        return f"{body_ccl} >> C:{{{handler_ccl}}}"

    elif isinstance(node, ast.With):
        # with ctx: body → ctx >> scope{{body}}
        body_parts = [c for s in node.body if (c := _stmt_to_ccl(s, arg_map))]
        body_ccl = " >> ".join(body_parts) if body_parts else "..."
        return f"scope{{{body_ccl}}}"

    elif isinstance(node, ast.Expr):
        # 式文 (関数呼び出し等)
        return _expr_to_ccl(node.value, arg_map)

    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        # CCL-B1: ネスト関数の body を再帰展開 (クロージャ/デコレータの構造保存)
        # ネスト関数は親の arg_map を引き継ぐ (クロージャ変数のフロー保存)
        body_parts = [c for s in node.body if (c := _stmt_to_ccl(s, arg_map))]
        body_ccl = " >> ".join(body_parts) if body_parts else "..."
        # デコレータ: ^ (メタ/上昇) — 関数のメタ変換 (operators.md §1.2)
        n_decorators = len(getattr(node, 'decorator_list', []))
        if n_decorators > 0:
            return f"^{{[def]{{{body_ccl}}}}}"  # ^{body} = メタ変換で包む
        return f"[def]{{{body_ccl}}}"

    elif isinstance(node, ast.Yield):
        return f">> !{_expr_to_ccl(node.value, arg_map)}" if node.value else ">> !yield"

    elif isinstance(node, ast.YieldFrom):
        return f">> !*{_expr_to_ccl(node.value, arg_map)}"

    elif isinstance(node, ast.Assert):
        # CCL-B5: assert はガード条件 = 検証射 (構造的に意味がある)
        test_ccl = _expr_to_ccl(node.test, arg_map)
        return f"V:{{{test_ccl}}}"

    elif isinstance(node, ast.Raise):
        # CCL-B5: raise は例外射 (制御フローの一部)
        if node.exc:
            return f">> !err({_expr_to_ccl(node.exc, arg_map)})"
        return ">> !err"

    # その他の文は無視 (import, pass, etc.)
    return ""


# PURPOSE: AST の式 (expression) を CCL 構造式に変換
def _expr_to_ccl(node: ast.expr, arg_map: dict[str, str] | None = None) -> str:
    """AST の式ノードを CCL 構造式に変換。

    C3v2: arg_map が渡された場合、¥ (外部入力) / # (内部状態) で識別する。
    """
    if node is None:
        return "()"

    if isinstance(node, ast.Call):
        # f(a, b) → (a % b) >> f
        # ただし名前は抽象化
        args_ccl = [_expr_to_ccl(a, arg_map) for a in node.args]
        if len(args_ccl) == 0:
            args_str = "()"
        elif len(args_ccl) == 1:
            args_str = args_ccl[0]
        else:
            args_str = f"({' % '.join(args_ccl)})"

        # 関数名は構造的に重要な場合のみ保存
        func_name = _get_func_label(node.func, arg_map)
        return f"{args_str} >> {func_name}"

    elif isinstance(node, ast.BinOp):
        left = _expr_to_ccl(node.left, arg_map)
        right = _expr_to_ccl(node.right, arg_map)
        op = _op_to_ccl(node.op)
        return f"({left} {op} {right})"

    elif isinstance(node, ast.Compare):
        left = _expr_to_ccl(node.left, arg_map)
        # 比較は述語 (predicate) として抽象化
        return f"{left} >> pred"

    elif isinstance(node, ast.BoolOp):
        # and → & (条件付き接続: _ = 単純逐次と区別)
        # or  → | (選択型: CCL §1.5 の A|B = Union に対応)
        values = [_expr_to_ccl(v, arg_map) for v in node.values]
        op = "&" if isinstance(node.op, ast.And) else "|"
        return f"({f' {op} '.join(values)})"

    elif isinstance(node, ast.UnaryOp):
        operand = _expr_to_ccl(node.operand, arg_map)
        if isinstance(node.op, ast.Not):
            return f"\\{operand}"  # 双対 (否定 ≈ 双対関手)
        return operand

    elif isinstance(node, ast.ListComp):
        # [f(x) for x in xs if p(x)] → xs >> F:[comp]{{f}} >> V:{{p}}
        target = _expr_to_ccl(node.elt, arg_map)
        parts = []
        for gen in node.generators:
            iter_ccl = _expr_to_ccl(gen.iter, arg_map)
            parts.append(iter_ccl)
            for if_clause in gen.ifs:
                parts.append(f"V:{{{_expr_to_ccl(if_clause, arg_map)}}}")
        parts.append(f"F:[comp]{{{target}}}")
        return " >> ".join(parts)

    elif isinstance(node, ast.SetComp):
        # {f(x) for x in xs} → xs >> F:[scomp]{{f}}
        target = _expr_to_ccl(node.elt, arg_map)
        parts = []
        for gen in node.generators:
            iter_ccl = _expr_to_ccl(gen.iter, arg_map)
            parts.append(iter_ccl)
        parts.append(f"F:[scomp]{{{target}}}")
        return " >> ".join(parts)

    elif isinstance(node, ast.GeneratorExp):
        # (f(x) for x in xs) → xs >> F:[gen]{{f}}
        target = _expr_to_ccl(node.elt, arg_map)
        parts = []
        for gen in node.generators:
            iter_ccl = _expr_to_ccl(gen.iter, arg_map)
            parts.append(iter_ccl)
        parts.append(f"F:[gen]{{{target}}}")
        return " >> ".join(parts)

    elif isinstance(node, ast.DictComp):
        key = _expr_to_ccl(node.key, arg_map)
        val = _expr_to_ccl(node.value, arg_map)
        parts = []
        for gen in node.generators:
            parts.append(_expr_to_ccl(gen.iter, arg_map))
        parts.append(f"F:[dcomp]{{({key} % {val})}}")
        return " >> ".join(parts)

    elif isinstance(node, ast.Lambda):
        body = _expr_to_ccl(node.body, arg_map)
        return f"L:[_]{{{body}}}"

    elif isinstance(node, ast.IfExp):
        # a if cond else b → cond >> I:[ok]{{a}} E:{{b}}
        cond = _expr_to_ccl(node.test, arg_map)
        then = _expr_to_ccl(node.body, arg_map)
        else_ = _expr_to_ccl(node.orelse, arg_map)
        return f"{cond} >> I:[ok]{{{then}}} E:{{{else_}}}"

    elif isinstance(node, (ast.Tuple, ast.List)):
        elts = [_expr_to_ccl(e, arg_map) for e in node.elts]
        return f"({' % '.join(elts)})" if elts else "()"

    elif isinstance(node, ast.Dict):
        pairs = []
        for k, v in zip(node.keys, node.values):
            if k is not None:
                pairs.append(f"({_expr_to_ccl(k, arg_map)} % {_expr_to_ccl(v, arg_map)})")
        return f"({' * '.join(pairs)})" if pairs else "()"

    elif isinstance(node, ast.Subscript):
        return f"{_expr_to_ccl(node.value, arg_map)} >> [idx]"

    elif isinstance(node, ast.Attribute):
        return f"{_expr_to_ccl(node.value, arg_map)} >> .attr"

    elif isinstance(node, ast.Starred):
        return f"*{_expr_to_ccl(node.value, arg_map)}"

    elif isinstance(node, ast.JoinedStr):  # f-string
        return "format"

    elif isinstance(node, ast.Constant):
        # 定数は型だけ残す (値は忘却)
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
        # C3v2: ¥ (引数/外部入力) or # (ローカル変数/内部状態)
        if arg_map and node.id in arg_map:
            return arg_map[node.id]
        return "#"  # フォールバック: 未知変数はローカル扱い

    elif isinstance(node, ast.Await):
        return f"await >> {_expr_to_ccl(node.value, arg_map)}"

    # フォールバック: 未知式はローカル状態扱い
    return "#"


def _get_func_label(node: ast.expr, arg_map: dict[str, str] | None = None) -> str:
    """関数呼出の関数部分をラベル化。組込み/標準ライブラリは名前を残す。"""
    if isinstance(node, ast.Name):
        # C3v2: 引数が callable として使われた場合、¥ を返す
        if arg_map and node.id in arg_map:
            return arg_map[node.id]
        # 組込み関数は構造的に重要なので名前を残す
        builtins = {
            "len", "sorted", "reversed", "enumerate", "zip", "map", "filter",
            "sum", "min", "max", "any", "all", "range", "list", "dict",
            "set", "tuple", "str", "int", "float", "bool", "print",
            "isinstance", "hasattr", "getattr", "setattr", "type",
            "open", "iter", "next",
        }
        if node.id in builtins:
            return node.id
        return "fn"  # ユーザー定義関数は抽象化
    elif isinstance(node, ast.Attribute):
        # メソッド呼出: obj.method() → .method
        # 一般的なメソッド名は残す
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


def _op_to_ccl(op: ast.operator) -> str:
    """二項演算子を CCL に変換。"""
    op_map = {
        ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
        ast.Mod: "%", ast.Pow: "**", ast.FloorDiv: "//",
        ast.BitOr: "|", ast.BitAnd: "&", ast.BitXor: "^",
        ast.LShift: "<<", ast.RShift: ">>",
    }
    return op_map.get(type(op), "op")


# PURPOSE: 関数/メソッドの AST ノード全体を CCL 構造式に変換
def python_to_ccl(func_node: ast.FunctionDef) -> str:
    """関数の AST 全体を CCL 構造式に変換する忘却関手 U。

    名前・変数名を忘れ、射 (構造) のみを残す。
    Aletheia §2.1 の U_arrow (n=1) + U_compose (n=1.5) を実装。
    C3v2: 引数は ¥ (外部入力)、ローカル変数は # (内部状態) で識別。
    operators.md §1.5.5 準拠。

    Args:
        func_node: ast.FunctionDef or ast.AsyncFunctionDef

    Returns:
        CCL 構造式文字列
    """
    # C3v2: 変数名 → データ出自トークン (¥/# ) のマッピングを構築
    arg_map = _build_scope_map(func_node)

    parts = []
    for stmt in func_node.body:
        # docstring はスキップ
        if isinstance(stmt, ast.Expr) and isinstance(getattr(stmt, 'value', None), ast.Constant):
            if isinstance(stmt.value.value, str):
                continue
        ccl = _stmt_to_ccl(stmt, arg_map)
        if ccl:
            parts.append(ccl)

    if not parts:
        return "#"  # 空関数

    return " >> ".join(parts)


# ============================================================
# CCL 特徴量ベクトル化 — Wave 9 成果 (ρ=0.521→0.9195)
# ============================================================

# PURPOSE: CCL テキストから 29 次元の構造特徴量を抽出 (v2)
def ccl_features(ccl_text: str) -> list[float]:
    """CCL 構造式から 29 次元の特徴量ベクトルを抽出する (v2)。

    CCL テキストのトークン分布・構造パターンを数値化。
    名前情報は既に忘却済みのため、純粋な構造特徴量。

    v2 変更点 (C3v2 移行対応):
    - 除去 7d: n_assign, n_var, n_uvar, n_ret, n_def, arsum, var_reuse
      (C3v2 トークン体系で全て 100% ゼロ)
    - 追加 9d: n_product, n_dual, n_union, n_and, n_hash, mb_ratio,
      n_type_annot, n_guard, product_density
      (CCL 演算子の圏論的構造から演繹)

    Args:
        ccl_text: python_to_ccl() の出力

    Returns:
        29 次元の float リスト
    """
    toks = ccl_text.split()
    nt = len(toks)

    # === 基本構造メトリクス (6d) ===
    n_seq = ccl_text.count('>>')
    n_block = ccl_text.count('{')
    n_call = sum(1 for t in toks if t.startswith('fn') or t.startswith('.m'))
    n_builtin = sum(
        1 for t in toks if t in {
            'len', 'sorted', 'reversed', 'enumerate', 'zip', 'map', 'filter',
            'sum', 'min', 'max', 'any', 'all', 'range', 'list', 'dict',
            'set', 'tuple', 'str', 'int', 'float', 'bool', 'print',
            'isinstance', 'hasattr', 'getattr', 'setattr', 'type',
            'open', 'iter', 'next',
        }
    )
    # 属性アクセス: `.` 始まりで `.m` (メソッド呼出) でないトークン
    n_method = sum(
        1 for t in toks
        if t.startswith('.') and not t.startswith('.m') and len(t) > 1
    )

    # === フラグ (有無) (5d) ===
    n_if_f = 1 if 'I:[ok]' in ccl_text else 0
    n_for_f = 1 if 'F:[each]' in ccl_text else 0
    n_wh_f = 1 if 'C:*' in ccl_text else 0
    n_try_f = 1 if 'C:{' in ccl_text else 0
    n_with_f = 1 if 'scope{' in ccl_text else 0

    # === カウント (2d) ===
    n_if_c = ccl_text.count('I:[ok]')
    n_for_c = ccl_text.count('F:[each]')

    # === 定数型 (4d) ===
    n_str = toks.count('str_')
    n_num = toks.count('num_')
    n_nil = toks.count('nil_')
    n_bool = toks.count('bool_')
    n_pred = toks.count('pred')

    # === 引数 (1d) ===
    # arity: C3v2 では ¥ トークンが引数を示す
    n_yen = sum(1 for t in toks if t == '¥')

    # === 最大ネスト深度 (1d) ===
    mx = 0
    d = 0
    for c in ccl_text:
        if c == '{':
            d += 1
            mx = max(mx, d)
        elif c == '}':
            d -= 1

    # === 導出比率 (1d) ===
    seq_density = n_seq / max(nt, 1)

    # === CCL 演算子 (圏論的構造) (4d) ===
    # n_product: 射の積 (引数並列化, タプル構成)
    n_product = ccl_text.count('%')
    # n_dual: 双対関手 (否定, 反転)
    n_dual = ccl_text.count('\\')
    # n_union: 余積 (型分岐, union type)
    n_union = sum(1 for t in toks if t == '|')
    # n_and: 積 (条件合流, 論理積)
    n_and = sum(1 for t in toks if t == '&')

    # === MB 構造 (2d) ===
    # n_hash: Markov blanket 内部状態参照 (self/cls → #)
    # トークン分割で [T:# のように埋め込まれるケースがあるため、
    # ccl_text 全体での出現数をカウントする
    n_hash = ccl_text.count('#')
    # mb_ratio: MB 透過率 (外部引数 ¥ vs 内部参照 #)
    mb_ratio = n_yen / max(n_yen + n_hash, 1)

    # === 構造比率 (3d) ===
    # n_type_annot: 直積分解 (型注釈の存在)
    n_type_annot = ccl_text.count('T:')
    # n_guard: 部分対象分類器 (ガード条件, バリデーション)
    n_guard = ccl_text.count('V:{')
    # product_density: 直積の密度 (並列構造の割合)
    product_density = n_product / max(n_seq, 1)

    return [
        # 基本構造 (6d)
        nt, n_seq, n_block, n_call, n_builtin, n_method,
        # フラグ (5d)
        n_if_f, n_for_f, n_wh_f, n_try_f, n_with_f,
        # カウント (2d)
        n_if_c, n_for_c,
        # 定数型 (4d)
        n_str, n_num, n_nil + n_bool, n_pred,
        # 引数 (1d)
        n_yen,
        # 導出 (2d)
        mx, seq_density,
        # CCL 演算子 (4d)
        n_product, n_dual, n_union, n_and,
        # MB 構造 (2d)
        n_hash, mb_ratio,
        # 構造比率 (3d)
        n_type_annot, n_guard, product_density,
    ]


# ============================================================
# CCL 型推論 — Aletheia フィルトレーション n=2 (TypeSeq)
# ============================================================
# PURPOSE: U_type: CCL → TypeSeq 忘却関手。操作を忘却し計算の流れパターンを保存する。
#
# filtration:  Code → CCL → TypeSeq
#              n=0    n=1    n=2
#              名前   構造   流れ

# 組込み関数セット (ccl_features と共有すべきだが、独立定義で明示性を優先)
_BUILTINS = {
    'len', 'sorted', 'reversed', 'enumerate', 'zip', 'map', 'filter',
    'sum', 'min', 'max', 'any', 'all', 'range', 'list', 'dict',
    'set', 'tuple', 'str', 'int', 'float', 'bool', 'print',
    'isinstance', 'hasattr', 'getattr', 'setattr', 'type',
    'open', 'iter', 'next',
}

# 制御構造プレフィックス (T 型を示す CCL パターン)
_CONTROL_PREFIXES = ('I:[', 'F:[', 'W:[', 'C:', 'V:{', 'scope{')


# PURPOSE: CCL トークンから S/T/P/M 型を推論する
def ccl_infer_type(token: str) -> str | None:
    """CCL トークンに S/T/P/M 型を割り当てる。

    VISION §1.6 の型システム:
    S (状態), T (変換), P (プロセス), M (メタ)

    Args:
        token: CCL 式の個別トークン

    Returns:
        'S', 'T', 'P', 'M', または None (型付け不要: >>, 括弧等)
    """
    # 構造子・区切り子は型付けしない
    # %, * は CCL 構造演算子 (直積/融合)。型推論では構造子として扱う
    if token in ('>>', '(', ')', '{', '}', '%', '*', '=',
                 '[T:_]', '...'):
        return None

    # S (状態): return は出力状態
    if token == 'return':
        return 'S'

    # P (プロセス): 振動
    if token == '~':
        return 'P'

    # M (メタ): メタ化、定義
    if token == '^' or token.startswith('[def]'):
        return 'M'

    # T (変換): 算術演算子 — 値を変換する操作
    if token in ('+', '-', '/', '//', '**', '&', '|', 'op'):
        return 'T'

    # T (変換): 関数, メソッド, 組込み, 述語, 双対
    if token.startswith('fn'):
        return 'T'
    if token.startswith('.'):  # .method, .attr, .append 等
        return 'T'
    if token in _BUILTINS:
        return 'T'
    if token == 'pred':
        return 'T'
    if token.startswith('\\'):  # 双対関手
        return 'T'
    if token == 'format':  # f-string
        return 'T'
    if token in ('await', 'recover'):
        return 'T'
    if token.startswith('[idx]'):  # 添字アクセス
        return 'T'
    # 制御構造トークン (I:[ok], F:[each]{...} 等)
    for prefix in _CONTROL_PREFIXES:
        if token.startswith(prefix):
            return 'T'

    # S (状態): データ, 定数, 変数
    if token in ('¥', '#', '()'):
        return 'S'
    if token in ('str_', 'num_', 'nil_', 'bool_', 'const_'):
        return 'S'
    if token.startswith('!'):  # yield (!expr)
        return 'S'

    # フォールバック: 不明トークンは None (型判定保留)
    return None


# PURPOSE: CCL 式から型シーケンス (TypeSeq) を生成する忘却関手 U_type
def ccl_type_seq(ccl_text: str) -> list[str]:
    """CCL 式を >> でセグメント分割し、各セグメントの型を推論する。

    Aletheia フィルトレーション n=2: 操作を忘却し、計算の流れパターンのみを保存。

    例:
        "¥ >> fn >> V:{pred} >> F:[each]{fn} >> return"
        → ['S', 'T', 'T', 'T', 'S']

    Args:
        ccl_text: python_to_ccl() の出力

    Returns:
        ['S', 'T', 'P', 'M'] の列。空入力は ['S'] を返す。
    """
    if not ccl_text or not ccl_text.strip():
        return ['S']

    # >> でセグメント分割
    segments = [s.strip() for s in ccl_text.split('>>') if s.strip()]

    if not segments:
        return ['S']

    type_seq = []
    for seg in segments:
        seg_type = _infer_segment_type(seg)
        type_seq.append(seg_type)

    return type_seq


# PURPOSE: セグメント (>> 間のサブ式) の型を判定する
def _infer_segment_type(segment: str) -> str:
    """セグメント内のトークンから主要型を判定する。

    優先順位: P > M > T > S
    (振動が最優先、メタが次、変換、最後に状態)
    """
    tokens = segment.split()
    types_found: set[str] = set()

    for tok in tokens:
        t = ccl_infer_type(tok)
        if t:
            types_found.add(t)

    # 優先順位で返す
    if 'P' in types_found:
        return 'P'
    if 'M' in types_found:
        return 'M'
    if 'T' in types_found:
        return 'T'
    # S が見つかったか、何も見つからなかった場合
    return 'S'


# PURPOSE: TypeSeq から 8 次元の型特徴量を抽出する
def ccl_type_features(ccl_text: str) -> list[float]:
    """TypeSeq から型分布 (4d) + 型フロー (4d) = 8 次元の特徴量を返す。

    型分布 [S率, T率, P率, M率]:
        各型の出現比率。合計 1.0。

    型フロー [TypeSeq長, T連続最長, S→T遷移数, T→S遷移数]:
        TypeSeq長:     計算パイプラインの段数
        T連続最長:     最も長い変換の連鎖 (複雑さの指標)
        S→T遷移数:     状態→変換の切替回数 (入力注入の回数)
        T→S遷移数:     変換→状態の切替回数 (中間結果の確定回数)

    Args:
        ccl_text: python_to_ccl() の出力

    Returns:
        8 次元の float リスト
    """
    seq = ccl_type_seq(ccl_text)
    n = len(seq)

    # 型分布 (4d) — 正規化
    counts = {'S': 0, 'T': 0, 'P': 0, 'M': 0}
    for t in seq:
        counts[t] = counts.get(t, 0) + 1
    s_rate = counts['S'] / n
    t_rate = counts['T'] / n
    p_rate = counts['P'] / n
    m_rate = counts['M'] / n

    # 型フロー (4d)
    # TypeSeq 長
    seq_len = float(n)

    # T 連続最長
    max_t_run = 0
    cur_t_run = 0
    for t in seq:
        if t == 'T':
            cur_t_run += 1
            max_t_run = max(max_t_run, cur_t_run)
        else:
            cur_t_run = 0

    # S→T 遷移数, T→S 遷移数
    st_transitions = 0
    ts_transitions = 0
    for i in range(len(seq) - 1):
        if seq[i] == 'S' and seq[i + 1] == 'T':
            st_transitions += 1
        elif seq[i] == 'T' and seq[i + 1] == 'S':
            ts_transitions += 1

    return [
        s_rate, t_rate, p_rate, m_rate,
        seq_len, float(max_t_run), float(st_transitions), float(ts_transitions),
    ]


# PURPOSE: CCL テキストから 16 次元の構造補完特徴量を抽出 (ast_supplement の置換)
def ccl_supplement(ccl_text: str) -> list[float]:
    """CCL テキストから構造補完特徴量 (16d) を抽出する。

    旧 ast_supplement が Python AST から直接取得していた 16d を、
    CCL テキストのパターンマッチングで代替する。
    忘却関手 U の一貫性: CCL の外 (Python AST) から情報を持ち込まない。

    対応表:
      dim 0: ListComp  → F:[each]{} パターン数 (V:{} と共起)
      dim 1: DictComp  → (% %) * F:[each]{} パターン
      dim 2: SetComp   → F:[each]{} パターン (ListComp と構造同型)
      dim 3: GeneratorExp → ! + F:[each]{} パターン
      dim 4: ExceptHandler → C:{} 内のブロック数
      dim 5: Raise     → CCL 未対応 (暫定 0)
      dim 6: Assert    → CCL 未対応 (暫定 0)
      dim 7: デコレータ → CCL 未対応 (暫定 0)
      dim 8: AugAssign → >> パターン (代入的合成)
      dim 9: Subscript → [idx] トークン数
      dim 10: JoinedStr → format トークン数
      dim 11: Yield    → ! トークン数
      dim 12: Lambda   → L:[] トークン数
      dim 13: BoolOp   → & | トークン数
      dim 14: IfExp    → I:[ok]{} E:{} の単行パターン
      dim 15: Starred  → CCL 未対応 (暫定 0)

    Args:
        ccl_text: python_to_ccl() の出力

    Returns:
        16 次元の float リスト
    """
    import re
    toks = ccl_text.split()

    # dim 0: ListComp — F:[each]{} の出現数
    n_listcomp = ccl_text.count('F:[each]')
    # dim 1: DictComp — (% %) を含む F:[each]{} パターン
    n_dictcomp = len(re.findall(r'F:\[each\]\{[^}]*%[^}]*\}', ccl_text))
    # dim 2: SetComp — ListComp と構造同型 (CCL では区別不能)
    n_setcomp = 0  # CCL レベルで List/Set の区別は忘却される (n=0 情報)
    # dim 3: GeneratorExp — ! を含む F:[each]{} パターン
    n_genexp = len(re.findall(r'F:\[each\]\{[^}]*![^}]*\}', ccl_text))
    # dim 4: ExceptHandler — C:{} のブロック数 (recover トークンも含む)
    n_except = ccl_text.count('C:{') + toks.count('recover')
    # dim 5: Raise — !err トークン数 (既存変換: raise → >> !err(expr))
    n_raise = sum(1 for t in toks if t.startswith('!err'))
    # dim 6: Assert — V:{} パターン数 (既存変換: assert → V:{pred})
    n_assert = ccl_text.count('V:{')
    # dim 7: デコレータ — ^{} パターン数 (新変換: @decorator → ^{body})
    n_decorator = ccl_text.count('^{')
    # dim 8: AugAssign — >> の一部 (内部状態の更新パターン)
    n_augassign = len(re.findall(r'# >> ', ccl_text))
    # dim 9: Subscript — [idx] トークン数
    n_subscript = sum(1 for t in toks if t.startswith('[idx]'))
    # dim 10: JoinedStr — format トークン数
    n_fstring = toks.count('format')
    # dim 11: Yield/YieldFrom — ! トークン数 (!err を除外)
    n_yield = sum(1 for t in toks if t.startswith('!') and not t.startswith('!err'))
    # dim 12: Lambda — L:[] トークン数
    n_lambda = ccl_text.count('L:[')
    # dim 13: BoolOp — & と | の合計
    n_boolop = sum(1 for t in toks if t in ('&', '|'))
    # dim 14: IfExp (三項演算子) — I:[ok]{} の出現数
    n_ifexp = ccl_text.count('I:[ok]')
    # dim 15: Starred — * プレフィックストークン (既存変換: *args → *expr)
    n_starred = sum(1 for t in toks if t.startswith('*') and t != '*')

    return [
        float(n_listcomp),
        float(n_dictcomp),
        float(n_setcomp),
        float(n_genexp),
        float(n_except),
        float(n_raise),
        float(n_assert),
        float(n_decorator),
        float(n_augassign),
        float(n_subscript),
        float(n_fstring),
        float(n_yield),
        float(n_lambda),
        float(n_boolop),
        float(n_ifexp),
        float(n_starred),
    ]


# PURPOSE: CCL テキストから 12 次元の構造カウント特徴量を抽出 (v4 — 重複除去 + 内包表記分離)
def ccl_structural_counts(ccl_text: str) -> list[int]:
    """CCL テキストから構造パターンの出現数を直接カウントする。

    旧 ast_supplement (Python AST 依存) を置換し、さらに ccl_features との
    重複次元を除去した v4。

    除去した旧次元 (ccl_features に既に存在):
      - 旧[2,3]: 予約 (常時ゼロ)
      - 旧[6]: V:{ カウント = ccl_features.n_guard
      - 旧[7]: デコレータ (常時ゼロ)
      - 旧[13]: & + | カウント = ccl_features.n_and + n_union
      - 旧[14]: I:[ok]{} E:{} = ccl_features.n_if_c

    Args:
        ccl_text: python_to_ccl() の出力

    Returns:
        12 次元の int リスト
    """
    import re

    # [0] リスト内包表記: F:[comp]{} の出現数
    n_comp = ccl_text.count('F:[comp]{')

    # [1] 辞書内包表記: F:[dcomp]{} の出現数
    n_dcomp = ccl_text.count('F:[dcomp]{')

    # [2] 集合内包表記: F:[scomp]{} の出現数
    n_scomp = ccl_text.count('F:[scomp]{')

    # [3] ジェネレータ式: F:[gen]{} の出現数
    n_gen = ccl_text.count('F:[gen]{')

    # [4] 例外ハンドラ: C:{} (try-except) の出現数
    # ccl_features.n_try_f はフラグ (0/1) のため、カウントは追加情報
    n_except = ccl_text.count('C:{')

    # [5] 例外送出: !err の出現数
    n_raise = ccl_text.count('!err')

    # [6] 累積代入: >> 直後の算術演算パターン (AugAssign)
    n_aug_assign = len(re.findall(r'>>\s+(?:num_|#|\¥)', ccl_text))

    # [7] 添字アクセス: [idx] の出現数
    n_subscript = ccl_text.count('[idx]')

    # [8] フォーマット文字列: format トークンの出現数
    n_format = ccl_text.count('format')

    # [9] Yield 系: !yield + !* の出現数
    n_yield = ccl_text.count('!yield') + ccl_text.count('!*')

    # [10] Lambda: L:[_]{ の出現数
    n_lambda = ccl_text.count('L:[_]{')

    # [11] スプレッド: *¥ / *# パターン
    n_starred = len(re.findall(r'\*[¥#]', ccl_text))

    return [
        n_comp,        # [0] リスト内包 (F:[comp]{})
        n_dcomp,       # [1] 辞書内包 (F:[dcomp]{})
        n_scomp,       # [2] 集合内包 (F:[scomp]{})
        n_gen,         # [3] ジェネレータ (F:[gen]{})
        n_except,      # [4] 例外ハンドラ (C:{})
        n_raise,       # [5] 例外送出 (!err)
        n_aug_assign,  # [6] 累積代入
        n_subscript,   # [7] 添字アクセス ([idx])
        n_format,      # [8] フォーマット (format)
        n_yield,       # [9] Yield (!yield, !*)
        n_lambda,      # [10] Lambda (L:[_]{)
        n_starred,     # [11] スプレッド (*¥ *#)
    ]


# 互換性ラッパー: 旧 ast_supplement を使っている外部コードの移行用
def ast_supplement(func_node: ast.FunctionDef) -> list[int]:
    """[DEPRECATED] ccl_structural_counts() を使用してください。"""
    ccl_text = python_to_ccl(func_node)
    return ccl_structural_counts(ccl_text)


# PURPOSE: CCL テキスト特徴量 + 構造カウント + 型特徴量で 49 次元ベクトルを生成
def ccl_feature_vector(func_node: ast.FunctionDef) -> list[float]:
    """関数の全構造特徴量を 49 次元ベクトルとして返す。

    CCL テキスト特徴量 (29d) + 構造カウント特徴量 (12d) + 型特徴量 (8d) = 49d。
    v4: 全特徴量が CCL テキストから計算 (AST 直接参照なし)。
    v3→v4 変更: 重複6次元除去 + 内包表記4種分離。
    型特徴量は Aletheia フィルトレーション n=2 (TypeSeq) による。

    Args:
        func_node: ast.FunctionDef or ast.AsyncFunctionDef

    Returns:
        49 次元の float リスト
    """
    ccl_text = python_to_ccl(func_node)
    cf = ccl_features(ccl_text)
    sc = ccl_structural_counts(ccl_text)
    tf = ccl_type_features(ccl_text)
    return cf + [float(x) for x in sc] + tf


# PURPOSE: Python ファイルを AST で関数/クラスにチャンク化
def parse_python_file(file_path: Path) -> list[Document]:
    """Python ファイルを AST で解析し、関数/クラス単位の Document に変換。

    Args:
        file_path: パース対象の .py ファイル

    Returns:
        Document のリスト。空ファイルやパースエラー時は空リスト。
    """
    docs = []

    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:  # noqa: BLE001
        return docs
    if not source.strip():
        return docs

    lines = source.splitlines()

    # AST 解析
    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        # パースできない場合はファイル全体を1チャンクにする
        if len(lines) > 0:
            docs.append(_make_file_doc(file_path, source, lines))
        return docs

    # PROOF/PURPOSE ヘッダを抽出
    proof_line = ""
    purpose_line = ""
    for line in lines[:20]:  # 先頭20行を走査
        stripped = line.strip()
        if stripped.startswith("# PROOF:"):
            proof_line = stripped
        elif stripped.startswith("# PURPOSE:"):
            purpose_line = stripped

    # モジュール docstring
    module_doc = ast.get_docstring(tree) or ""

    # トップレベルの関数/クラスを抽出
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = _make_function_doc(file_path, source, lines, node, proof_line)
            if doc:
                docs.append(doc)
        elif isinstance(node, ast.ClassDef):
            # クラス自体を1チャンク
            doc = _make_class_doc(file_path, source, lines, node, proof_line)
            if doc:
                docs.append(doc)
            # クラス内のメソッドも個別にチャンク化
            for item in ast.iter_child_nodes(node):
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    doc = _make_method_doc(file_path, source, lines, node, item, proof_line)
                    if doc:
                        docs.append(doc)

    # 小さいファイルはファイル全体のチャンクも作成
    if len(lines) <= _SMALL_FILE_THRESHOLD:
        docs.append(_make_file_doc(file_path, source, lines))

    return docs


# PURPOSE: ファイル全体を1つの Document にする
def _make_file_doc(file_path: Path, source: str, lines: list[str]) -> Document:
    """ファイル全体を1つの Document に変換。"""
    title = file_path.stem

    # 先頭の docstring かコメントからタイトルを抽出
    for line in lines[:10]:
        stripped = line.strip()
        if stripped.startswith('"""') or stripped.startswith("'''"):
            title_candidate = stripped.strip('"""').strip("'''").strip()
            if title_candidate:
                title = title_candidate
                break

    content = source[:3000]  # 先頭3000文字
    file_id = str(file_path.stem).replace(" ", "_")

    return Document(
        id=f"code-file-{file_id}",
        content=f"[File] {file_path.name}\n\n{content}",
        metadata={
            "type": "code",
            "code_type": "file",
            "language": "python",
            "file_path": str(file_path),
            "ki_name": f"[code] {file_path.name}",
            "summary": f"Python ファイル: {file_path.name}",
            "line_start": 1,
            "line_end": len(lines),
        },
    )


# PURPOSE: 関数定義を CCL 構造式 Document にする
def _make_function_doc(
    file_path: Path, source: str, lines: list[str],
    node: ast.FunctionDef, proof_line: str
) -> Document | None:
    """トップレベル関数を CCL 構造式 Document に変換。

    忘却関手 U: 名前を忘れ、射の構造 (CCL 式) を保存する。
    """
    func_name = node.name
    docstring = ast.get_docstring(node) or ""
    start = node.lineno
    end = node.end_lineno or start

    # 自明な関数を除外 (_MIN_CHUNK_LINES 未満)
    func_lines = end - start + 1
    if func_lines < _MIN_CHUNK_LINES:
        return None

    # PURPOSE コメントを関数の直前から探す
    purpose = ""
    if start > 1:
        prev_line = lines[start - 2].strip() if start >= 2 else ""
        if prev_line.startswith("# PURPOSE:"):
            purpose = prev_line[len("# PURPOSE:"):].strip()

    # CCL 構造式に変換 (忘却関手 U)
    ccl_expr = python_to_ccl(node)

    # 引数の型シグネチャ (AST から取得可能な範囲)
    args = node.args
    arg_types = []
    for a in args.args:
        if a.annotation:
            arg_types.append(ast.dump(a.annotation))
        else:
            arg_types.append("_")
    ret_type = ast.dump(node.returns) if node.returns else "_"
    signature = f"({', '.join(arg_types)}) → {ret_type}"

    # CCL 式の構造メトリクス
    composition_depth = ccl_expr.count(">>")  # 合成の長さ
    branching = ccl_expr.count("I:[ok]")      # 条件分岐数
    iteration = ccl_expr.count("F:[each]")    # 反復数

    # Document content: CCL 構造式 + メタ情報
    content_parts = [
        f"[Function] {ccl_expr}",
        f"Signature: {signature}",
    ]
    if purpose:
        content_parts.append(f"Purpose: {purpose}")
    elif docstring:
        content_parts.append(f"Purpose: {docstring[:200]}")
    content_parts.append(
        f"Structure: depth={composition_depth} branch={branching} iter={iteration}"
    )
    content_parts.append(f"Source: {file_path.name}:{func_name}")

    return Document(
        id=f"code-func-{file_path.stem}-{func_name}",
        content="\n".join(content_parts),
        metadata={
            "type": "code",
            "code_type": "function",
            "language": "python",
            "function_name": func_name,
            "file_path": str(file_path),
            "ki_name": f"[code] {func_name}() in {file_path.name}",
            "summary": purpose or docstring[:200] or f"関数 {func_name}",
            "ccl_expr": ccl_expr,
            "ccl_features": ccl_feature_vector(node),
            "line_start": start,
            "line_end": end,
            "composition_depth": composition_depth,
        },
    )


# PURPOSE: クラス定義を Document にする (Overview チャンク)
def _make_class_doc(
    file_path: Path, source: str, lines: list[str],
    node: ast.ClassDef, proof_line: str
) -> Document | None:
    """クラス定義を Document に変換 (概要チャンク)。"""
    class_name = node.name
    docstring = ast.get_docstring(node) or ""
    start = node.lineno
    end = node.end_lineno or start

    # クラスの先頭部分のみ (メソッドのシグネチャ一覧)
    method_sigs = []
    for item in ast.iter_child_nodes(node):
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = ", ".join(a.arg for a in item.args.args)
            method_sigs.append(f"  def {item.name}({args})")

    content_parts = [f"[Class] {class_name}"]
    if docstring:
        content_parts.append(f"Docstring: {docstring[:300]}")
    if method_sigs:
        content_parts.append("Methods:\n" + "\n".join(method_sigs[:20]))

    return Document(
        id=f"code-class-{file_path.stem}-{class_name}",
        content="\n".join(content_parts),
        metadata={
            "type": "code",
            "code_type": "class",
            "language": "python",
            "class_name": class_name,
            "file_path": str(file_path),
            "ki_name": f"[code] class {class_name} in {file_path.name}",
            "summary": docstring[:200] or f"クラス {class_name}",
            "line_start": start,
            "line_end": end,
            "method_count": len(method_sigs),
        },
    )


# PURPOSE: クラスメソッドを CCL 構造式 Document にする
def _make_method_doc(
    file_path: Path, source: str, lines: list[str],
    class_node: ast.ClassDef, method_node: ast.FunctionDef,
    proof_line: str
) -> Document | None:
    """クラスメソッドを CCL 構造式 Document に変換。"""
    class_name = class_node.name
    method_name = method_node.name

    # __init__ 以外のダンダーメソッドはスキップ
    if method_name.startswith("__") and method_name.endswith("__") and method_name != "__init__":
        return None

    docstring = ast.get_docstring(method_node) or ""
    start = method_node.lineno
    end = method_node.end_lineno or start

    # 自明なメソッドを除外
    method_lines = end - start + 1
    if method_lines < _MIN_CHUNK_LINES:
        return None

    # PURPOSE コメント
    purpose = ""
    if start > 1:
        prev_line = lines[start - 2].strip() if start >= 2 else ""
        if prev_line.startswith("# PURPOSE:"):
            purpose = prev_line[len("# PURPOSE:"):].strip()

    # CCL 構造式に変換 (忘却関手 U)
    ccl_expr = python_to_ccl(method_node)

    # CCL 式の構造メトリクス
    composition_depth = ccl_expr.count(">>")

    content_parts = [
        f"[Method] {ccl_expr}",
    ]
    if purpose:
        content_parts.append(f"Purpose: {purpose}")
    elif docstring:
        content_parts.append(f"Purpose: {docstring[:200]}")
    content_parts.append(f"Source: {file_path.name}:{class_name}.{method_name}")

    return Document(
        id=f"code-method-{file_path.stem}-{class_name}-{method_name}",
        content="\n".join(content_parts),
        metadata={
            "type": "code",
            "code_type": "method",
            "language": "python",
            "class_name": class_name,
            "function_name": method_name,
            "file_path": str(file_path),
            "ki_name": f"[code] {class_name}.{method_name}() in {file_path.name}",
            "summary": purpose or docstring[:200] or f"メソッド {class_name}.{method_name}",
            "ccl_expr": ccl_expr,
            "ccl_features": ccl_feature_vector(method_node),
            "line_start": start,
            "line_end": end,
            "composition_depth": composition_depth,
        },
    )


# PURPOSE: 全コードファイルを収集・パース
def get_all_code_documents() -> list[Document]:
    """全 CODE_SCAN_DIRS からコード Document を収集。

    Returns:
        Document のリスト
    """
    docs = []
    seen_paths: set[Path] = set()

    for dir_path, label in CODE_SCAN_DIRS:
        if not dir_path.exists():
            continue

        for py_file in sorted(dir_path.rglob("*.py")):
            # 除外チェック
            parts = set(py_file.relative_to(dir_path).parts)
            if parts & _EXCLUDE_DIRS:
                continue

            resolved = py_file.resolve()
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)

            file_docs = parse_python_file(py_file)
            docs.extend(file_docs)

    return docs


# PURPOSE: コードをベクトルインデックスに投入
def ingest_to_code(docs: list[Document], save_path: str = None) -> int:
    """コード Document をインデックスに投入。

    embed_batch で事前にバッチ embedding を取得し、
    Document.embedding にセットしてから SophiaIndex.ingest に渡す。

    Args:
        docs: Document のリスト
        save_path: 保存先パス (省略時は保存しない)

    Returns:
        投入件数
    """
    from mekhane.symploke.adapters.vector_store import VectorStore
    from mekhane.symploke.indices.sophia import SophiaIndex
    from mekhane.symploke.embedder_factory import get_embed_fn, get_dimension, get_embedder

    adapter = VectorStore()
    dim = get_dimension()
    embed_fn = get_embed_fn()
    embedder = get_embedder()
    index = SophiaIndex(adapter, "code", dimension=dim, embed_fn=embed_fn)
    index.initialize()

    # バッチ embed (50件ずつ並列 — VertexEmbedder.embed_batch の内部設計)
    BATCH_SIZE = 200  # embed_batch 内でさらに50ずつ分割される
    total = len(docs)
    embedded_count = 0

    for i in range(0, total, BATCH_SIZE):
        batch_docs = docs[i:i + BATCH_SIZE]
        texts = [d.content for d in batch_docs]

        try:
            embeddings = embedder.embed_batch(texts)
            for doc, emb in zip(batch_docs, embeddings):
                doc.embedding = emb
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ Batch {i//BATCH_SIZE + 1} embedding failed: {e}")
            # embedding 無しで ingest に渡す (ingest 側で個別 embed)
            pass

        embedded_count += len(batch_docs)
        print(f"  📊 Embedded {embedded_count}/{total} ({embedded_count*100//total}%)")

    # ingest (embedding 済みなので API 呼び出しなし)
    count = index.ingest(docs)
    print(f"Ingested {count} code documents (VertexEmbedder, {dim}d)")

    if save_path:
        adapter.save(save_path)
        print(f"💾 Saved code index to: {save_path}")

    return count


# ============================================================
# CCL-only Document 生成 — 構造検索専用 (Dual Embedding)
# ============================================================

# PURPOSE: 全コード Document から CCL-only Document を生成
def get_ccl_only_documents(all_docs: list[Document] | None = None) -> list[Document]:
    """既存の code Document から CCL 式のみの Document を生成。

    Dual Embedding 設計:
    - code.pkl: ハイブリッド content (CCL + purpose + signature) → 自然言語検索
    - code_ccl.pkl: CCL 式のみ → 構造パターン検索

    Args:
        all_docs: 既に生成された code Document のリスト (None の場合は新規生成)

    Returns:
        CCL-only Document のリスト (ccl_expr を持つものだけ)
    """
    if all_docs is None:
        all_docs = get_all_code_documents()

    ccl_docs = []
    for doc in all_docs:
        ccl_expr = doc.metadata.get("ccl_expr")
        if not ccl_expr or ccl_expr == "_":
            continue  # CCL なし or 空関数はスキップ

        # CCL 式のみを content にした Document を生成
        ccl_doc = Document(
            id=f"ccl-{doc.id}",
            content=ccl_expr,
            metadata={
                **doc.metadata,
                "original_doc_id": doc.id,
                "facet": "ccl",
            },
        )
        ccl_docs.append(ccl_doc)

    return ccl_docs


# PURPOSE: CCL-only Document をベクトルインデックスに投入
def ingest_to_code_ccl(docs: list[Document], save_path: str = None) -> int:
    """CCL-only Document をインデックスに投入。

    content は CCL 式のみなので、embedding は純粋に構造を捉える。

    Args:
        docs: CCL-only Document のリスト
        save_path: 保存先パス

    Returns:
        投入件数
    """
    from mekhane.symploke.adapters.vector_store import VectorStore
    from mekhane.symploke.indices.sophia import SophiaIndex
    from mekhane.symploke.embedder_factory import get_embed_fn, get_dimension, get_embedder

    adapter = VectorStore()
    dim = get_dimension()
    embed_fn = get_embed_fn()
    embedder = get_embedder()
    index = SophiaIndex(adapter, "code_ccl", dimension=dim, embed_fn=embed_fn)
    index.initialize()

    # バッチ embed
    BATCH_SIZE = 200
    total = len(docs)
    embedded_count = 0

    for i in range(0, total, BATCH_SIZE):
        batch_docs = docs[i:i + BATCH_SIZE]
        texts = [d.content for d in batch_docs]

        try:
            embeddings = embedder.embed_batch(texts)
            for doc, emb in zip(batch_docs, embeddings):
                doc.embedding = emb
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ CCL batch {i//BATCH_SIZE + 1} embedding failed: {e}")
            pass

        embedded_count += len(batch_docs)
        print(f"  📊 CCL embedded {embedded_count}/{total} ({embedded_count*100//total}%)")

    count = index.ingest(docs)
    print(f"Ingested {count} CCL-only documents (VertexEmbedder, {dim}d)")

    if save_path:
        adapter.save(save_path)
        print(f"💾 Saved CCL index to: {save_path}")

    # 43d 構造類似検索インデックスを並行構築
    _build_ccl_feature_index(docs, save_path)

    return count



# PURPOSE: 43d CCL 特徴量インデックスを構築
def _build_ccl_feature_index(docs: list, ccl_save_path: str | None) -> None:
    """CCL Document リストから 43d 構造類似検索インデックスを構築・保存する。

    ingest_to_code_ccl から呼ばれる。
    code.pkl の全 Document (ccl_features metadata を含むもの) から構築。

    Args:
        docs: CCL-only Document のリスト (ccl_features を含む)
        ccl_save_path: CCL インデックスの保存パス (隣に *_features.pkl を保存)
    """
    try:
        from mekhane.symploke.ccl_feature_index import CCLFeatureIndex

        # code.pkl (全関数の metadata に ccl_features がある) から構築
        from mekhane.paths import CODE_INDEX, CODE_CCL_FEATURES_INDEX
        import os

        # code.pkl が存在する場合はそこから構築 (ccl_features metadata がある)
        code_pkl = str(CODE_INDEX)
        if os.path.exists(code_pkl):
            idx = CCLFeatureIndex()
            n = idx.build_from_code_pkl(code_pkl)
            features_path = str(CODE_CCL_FEATURES_INDEX)
            idx.save(features_path)
            print(f"💾 Saved CCL feature index ({n} entries, 49d) to: {features_path}")
        else:
            print("⚠️ code.pkl not found, skipping CCL feature index build")
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ CCL feature index build failed: {e}")

    # ファイル間構造距離インデックスを並行構築
    _build_file_distance_index()


# PURPOSE: ファイル間 ED 構造距離インデックスを構築
def _build_file_distance_index() -> None:
    """code.pkl から FileDistanceIndex を構築・保存する。

    ED(L1) → centroid L1 フォールバック → cl^0.25 → FW → d/(1+d)
    パイプラインで Lawvere [0,1]-距離空間を構成する。
    """
    try:
        from mekhane.symploke.energy_distance import FileDistanceIndex
        from mekhane.paths import CODE_INDEX, FILE_DISTANCES_INDEX
        import os

        code_pkl = str(CODE_INDEX)
        if os.path.exists(code_pkl):
            idx = FileDistanceIndex()
            n = idx.build(code_pkl)
            save_path = str(FILE_DISTANCES_INDEX)
            idx.save(save_path)
            stats = idx.stats()
            fallback_pct = (
                f"{stats['neg_ed_count']}/{stats['total_pairs']}"
                if stats['total_pairs'] > 0 else "0/0"
            )
            print(
                f"💾 Saved file distance index ({n} files, "
                f"α={stats['alpha']:.3f}, fallback={fallback_pct}) "
                f"to: {save_path}"
            )
        else:
            print("⚠️ code.pkl not found, skipping file distance index build")
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ File distance index build failed: {e}")


# PURPOSE: Code index 差分更新 — 変更ファイルのみ re-embed
def incremental_rebuild_code(index_path: str = None) -> dict:
    """manifest ベースの差分コードインデックス更新。

    Returns:
        dict: {added: int, updated: int, deleted: int, unchanged: int, total: int}
    """
    from mekhane.symploke.adapters.vector_store import VectorStore
    from mekhane.symploke.embedder_factory import get_embed_fn, get_dimension, get_embedder
    from mekhane.paths import CODE_INDEX

    if index_path is None:
        index_path = str(CODE_INDEX)

    return _incremental_rebuild_code_impl(
        index_path=index_path,
        make_docs_fn=lambda files: _code_docs_for_files(files),
        label="code",
    )


# PURPOSE: CCL-only index 差分更新
def incremental_rebuild_code_ccl(index_path: str = None) -> dict:
    """manifest ベースの差分 CCL-only インデックス更新。

    Returns:
        dict: {added: int, updated: int, deleted: int, unchanged: int, total: int}
    """
    from mekhane.paths import CODE_CCL_INDEX

    if index_path is None:
        index_path = str(CODE_CCL_INDEX)

    return _incremental_rebuild_code_impl(
        index_path=index_path,
        make_docs_fn=lambda files: _ccl_docs_for_files(files),
        label="code_ccl",
    )


# PURPOSE: code / code_ccl 共用の差分更新実装
def _incremental_rebuild_code_impl(
    index_path: str,
    make_docs_fn,
    label: str,
) -> dict:
    """code / code_ccl 共用の差分更新。"""
    from mekhane.symploke.adapters.vector_store import VectorStore
    from mekhane.symploke.embedder_factory import get_embed_fn, get_dimension, get_embedder
    import numpy as np

    adapter = VectorStore()
    stats = {"added": 0, "updated": 0, "deleted": 0, "unchanged": 0, "total": 0}

    # 1. pkl ロード → manifest 取得
    old_manifest: dict[str, float] = {}
    if Path(index_path).exists():
        old_manifest = adapter.load(index_path) or {}
    else:
        # pkl なし → フル再構築
        print(f"📦 No existing {label} index — full rebuild")
        if label == "code_ccl":
            all_docs = get_all_code_documents()
            ccl_docs = get_ccl_only_documents(all_docs)
            ingest_to_code_ccl(ccl_docs, save_path=index_path)
            new_manifest = _build_code_manifest()
            adapter.save(index_path, manifest=new_manifest)
            stats["added"] = len(ccl_docs)
        else:
            all_docs = get_all_code_documents()
            ingest_to_code(all_docs, save_path=index_path)
            new_manifest = _build_code_manifest()
            adapter.save(index_path, manifest=new_manifest)
            stats["added"] = len(all_docs)
        stats["total"] = adapter.count()
        return stats

    # 2. 現在のファイル mtime スキャン
    current_manifest = _build_code_manifest()

    # 3. 差分計算
    old_files = set(old_manifest.keys())
    current_files = set(current_manifest.keys())

    deleted_files = old_files - current_files
    new_files = current_files - old_files
    common_files = old_files & current_files
    modified_files = {
        f for f in common_files
        if current_manifest[f] != old_manifest[f]
    }
    unchanged_files = common_files - modified_files

    stats["deleted"] = len(deleted_files)
    stats["added"] = len(new_files)
    stats["updated"] = len(modified_files)
    stats["unchanged"] = len(unchanged_files)

    if not deleted_files and not new_files and not modified_files:
        print(f"✅ {label} index is up-to-date (0 changes)")
        stats["total"] = adapter.count()
        return stats

    print(f"📊 {label} diff: +{len(new_files)} new, ~{len(modified_files)} modified, -{len(deleted_files)} deleted, ={len(unchanged_files)} unchanged")

    # 4a. 削除: deleted + modified のエントリを除去
    files_to_remove = deleted_files | modified_files
    for fp in files_to_remove:
        adapter.delete_by_source(fp)

    # 4b. 追加: new + modified のファイルを Document 化して embed
    files_to_add = new_files | modified_files
    if files_to_add:
        new_docs = make_docs_fn(files_to_add)
        if new_docs:
            embedder = get_embedder()
            BATCH_SIZE = 200
            total_docs = len(new_docs)
            for i in range(0, total_docs, BATCH_SIZE):
                batch = new_docs[i:i + BATCH_SIZE]
                texts = [d.content for d in batch]
                try:
                    embeddings = embedder.embed_batch(texts)
                    for doc, emb in zip(batch, embeddings):
                        meta = {**doc.metadata, "source": doc.metadata.get("file_path", ""), "doc_id": doc.id}
                        adapter.add_vectors(np.array([emb]), metadata=[meta])
                except Exception as e:  # noqa: BLE001
                    print(f"  ⚠️ Batch embed error: {e}")

            print(f"  ✅ Added/updated {len(new_docs)} {label} documents")

    # 5. manifest 更新して保存
    adapter.save(index_path, manifest=current_manifest)
    stats["total"] = adapter.count()
    print(f"💾 Saved {label} ({stats['total']} vectors)")
    return stats


# PURPOSE: Code 用の manifest (全対象 .py の mtime) を構築
def _build_code_manifest() -> dict[str, float]:
    """コード対象ファイル全体の file_path → mtime マッピングを返す。"""
    manifest: dict[str, float] = {}
    seen: set[Path] = set()

    for dir_path, _ in CODE_SCAN_DIRS:
        if not dir_path.exists():
            continue
        for py_file in dir_path.rglob("*.py"):
            parts = set(py_file.relative_to(dir_path).parts)
            if parts & _EXCLUDE_DIRS:
                continue
            resolved = py_file.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            fp = str(py_file)
            try:
                manifest[fp] = py_file.stat().st_mtime
            except OSError:
                pass

    return manifest


# PURPOSE: 指定ファイルのみの code Document を生成
def _code_docs_for_files(file_paths: set[str]) -> list[Document]:
    """指定ファイルの code Document のみ生成。"""
    docs = []
    for fp in file_paths:
        p = Path(fp)
        if p.exists() and p.suffix == ".py":
            docs.extend(parse_python_file(p))
    return docs


# PURPOSE: 指定ファイルのみの CCL-only Document を生成
def _ccl_docs_for_files(file_paths: set[str]) -> list[Document]:
    """指定ファイルの CCL-only Document のみ生成。"""
    code_docs = _code_docs_for_files(file_paths)
    return get_ccl_only_documents(code_docs)


# PURPOSE: Python ソースコードを CCL 構造式に変換する公開 API
def code_snippet_to_ccl(code: str) -> str:
    """Python コードスニペットを CCL 構造式に変換。

    MCP ツール `code_to_ccl` のバックエンド。
    関数定義を検出し、CCL 式に変換する。
    関数定義がなければ、トップレベル文を連結する。

    Args:
        code: Python コード文字列

    Returns:
        CCL 構造式文字列
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return "⚠️ SyntaxError: パースできないコード"

    # 関数定義を探す
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return python_to_ccl(node)

    # 関数定義がなければトップレベル文を連結
    parts = []
    for stmt in ast.iter_child_nodes(tree):
        ccl = _stmt_to_ccl(stmt)
        if ccl:
            parts.append(ccl)

    return " >> ".join(parts) if parts else "_"


# PURPOSE: CLI エントリーポイント
def main():
    """CLI メイン関数。"""
    parser = argparse.ArgumentParser(description="Code Ingest - Python コードをベクトルインデックスに投入")
    parser.add_argument("--dry-run", action="store_true", help="パースのみ (インデックス構築しない)")
    parser.add_argument("--ccl-only", action="store_true", help="CCL-only インデックスのみ構築")
    parser.add_argument("--both", action="store_true", help="code.pkl + code_ccl.pkl + code_ccl_features.pkl を全構築")
    args = parser.parse_args()

    print("🔍 Scanning code files...")
    docs = get_all_code_documents()
    print(f"📄 Found {len(docs)} code chunks")

    # 統計
    types = {}
    for d in docs:
        ct = d.metadata.get("code_type", "unknown")
        types[ct] = types.get(ct, 0) + 1
    for ct, count in sorted(types.items()):
        print(f"   {ct}: {count}")

    # CCL-only 統計
    ccl_docs = get_ccl_only_documents(docs)
    print(f"   ccl-only: {len(ccl_docs)} (CCL 式を持つ関数/メソッド)")

    if args.dry_run:
        # サンプル表示
        print("\n📋 Sample documents:")
        for d in docs[:5]:
            print(f"  [{d.metadata.get('code_type')}] {d.metadata.get('ki_name', d.id)}")
        print("\n📋 Sample CCL-only:")
        for d in ccl_docs[:5]:
            print(f"  {d.id}: {d.content[:100]}")
        return

    # .env から API キーをロード (-m 実行時は自動ロードされないため)
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("  📎 Loaded .env")
    except ImportError:
        print("  ⚠️ python-dotenv not installed, skipping .env load")

    from mekhane.paths import CODE_INDEX, CODE_CCL_INDEX

    if args.ccl_only:
        # CCL-only のみ
        print(f"\n⚡ Ingesting CCL-only to {CODE_CCL_INDEX}...")
        ingest_to_code_ccl(ccl_docs, str(CODE_CCL_INDEX))
    elif args.both:
        # 両方
        print(f"\n⚡ Ingesting text+CCL to {CODE_INDEX}...")
        ingest_to_code(docs, str(CODE_INDEX))
        print(f"\n⚡ Ingesting CCL-only to {CODE_CCL_INDEX}...")
        ingest_to_code_ccl(ccl_docs, str(CODE_CCL_INDEX))
    else:
        # デフォルト: code.pkl のみ (後方互換)
        save_path = str(CODE_INDEX)
        print(f"\n⚡ Ingesting to {save_path}...")
        ingest_to_code(docs, save_path)

    print("✅ Done!")


if __name__ == "__main__":
    main()
