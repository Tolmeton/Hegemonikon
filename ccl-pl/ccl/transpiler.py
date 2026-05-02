# CCL-PL トランスパイラ — Hermeneus トランスパイラの薄ラッパー
"""
CCL → Python トランスパイラ (CCL-PL 用ラッパー)

既存の ccl_transpiler.py (Lethe 実験) を CCL-PL 独立パッケージとして使えるよう、
import パスを調整した薄ラッパー。

将来的にはこのファイルに CCL-PL 固有の変換 (fn 構文等) を追加する。
"""

import sys
from pathlib import Path
from textwrap import indent
from typing import Any, List, Optional

# CCL-PL 内部の AST 定義を使用
from ccl.parser.ast import (
    ASTNode, Workflow, Sequence, Fusion, Oscillation,
    ConvergenceLoop, Adjunction, Pipeline, Parallel, Morphism,
    ForLoop, IfCondition, WhileLoop, Lambda, TaggedBlock,
    ColimitExpansion, LetBinding, Group, MacroRef, OpenEnd,
    PartialDiff, Integral, Summation, Condition, OpType,
    RawExpr, FnDef, FnCall, UseDecl, AdjointDecl,
)


class CCLTranspiler:
    """CCL AST → Python ソースコードのトランスパイラ"""

    # 深度修飾子 → detail_level のマッピング
    DEPTH_MAP = {
        OpType.DEEPEN: 3,     # + → L3
        OpType.CONDENSE: 1,   # - → L1
        OpType.ASCEND: 4,     # ^ → L4 (メタ)
        OpType.EXPAND: 5,     # ! → L5 (全展開)
    }

    def __init__(self, desugar: bool = False):
        """トランスパイラを初期化する"""
        self._desugar = desugar
        self._var_counter = 0
        self._indent_level = 0
        self._lines: List[str] = []
        self._functions_used: set = set()

    def transpile(self, ast: Any, include_header: bool = True) -> str:
        """AST を Python ソースコードに変換する"""
        self._var_counter = 0
        self._indent_level = 0
        self._lines = []
        self._functions_used = set()

        result_var = self._visit(ast)

        header_lines = []
        if include_header and self._functions_used:
            imports = sorted(self._functions_used)
            header_lines.append(f"from ccl.runtime import {', '.join(imports)}")
            header_lines.append("")

        body = "\n".join(self._lines)

        if result_var:
            body += f"\n\n# === CCL 実行結果 ===\nresult = {result_var}"

        if header_lines:
            return "\n".join(header_lines) + "\n" + body
        return body

    # ========= Visitor ディスパッチ =========

    def _visit(self, node: Any) -> Optional[str]:
        """AST ノードの型に応じて visit_* メソッドにディスパッチ"""
        if node is None:
            return None
        type_name = type(node).__name__
        visitor = getattr(self, f"_visit_{type_name}", None)
        if visitor is None:
            self._emit(f"# [未対応] {type_name}: {node}")
            return None
        return visitor(node)

    # ========= 基本ノード =========

    def _visit_Workflow(self, node: Workflow) -> str:
        var = self._new_var()
        is_inverted = OpType.INVERT in node.operators
        is_meta = OpType.ASCEND in node.operators

        kwargs = []
        for op in node.operators:
            if op in self.DEPTH_MAP:
                kwargs.append(f"detail_level={self.DEPTH_MAP[op]}")
                break
        for key, value in node.modifiers.items():
            if not key.startswith("_"):
                kwargs.append(f"{key}={repr(value)}")
        args_str = ", ".join(kwargs)

        if is_inverted:
            self._use("dual")
            self._emit(f'{var} = dual("{node.id}")({args_str})')
        elif is_meta and self._desugar:
            self._use("meta")
            self._emit(f"{var} = meta({node.id})({args_str})")
        else:
            self._emit(f"{var} = {node.id}({args_str})")
        return var

    def _visit_Sequence(self, node: Sequence) -> str:
        prev_var = None
        last_var = None
        for step in node.steps:
            if prev_var is not None and isinstance(step, Workflow):
                var = self._new_var()
                kwargs = [prev_var]
                for op in step.operators:
                    if op in self.DEPTH_MAP:
                        kwargs.append(f"detail_level={self.DEPTH_MAP[op]}")
                        break
                for key, value in step.modifiers.items():
                    if not key.startswith("_"):
                        kwargs.append(f"{key}={repr(value)}")
                args_str = ", ".join(kwargs)
                self._emit(f"{var} = {step.id}({args_str})")
                last_var = var
                prev_var = var
            else:
                last_var = self._visit(step)
                prev_var = last_var
        return last_var

    def _visit_Fusion(self, node: Fusion) -> str:
        left_var = self._visit(node.left)
        right_var = self._visit(node.right)
        var = self._new_var()
        if node.outer_product:
            self._use("product")
            self._emit(f"{var} = product({left_var}, {right_var})")
        elif node.fuse_outer:
            self._use("merge")
            self._use("product")
            self._emit(f"{var} = merge(product({left_var}, {right_var}))")
        else:
            self._use("merge")
            self._emit(f"{var} = merge({left_var}, {right_var})")
        return var

    def _visit_Oscillation(self, node: Oscillation) -> str:
        left_fn = self._visit_as_callable(node.left)
        right_fn = self._visit_as_callable(node.right)
        var = self._new_var()
        if node.convergent:
            self._use("converge")
            self._emit(f"{var} = converge({left_fn}, {right_fn}, max_iter={node.max_iterations})")
        elif node.divergent:
            self._use("diverge")
            self._emit(f"{var} = diverge({left_fn}, {right_fn}, max_iter={node.max_iterations})")
        else:
            self._use("oscillate")
            self._emit(f"{var} = list(oscillate({left_fn}, {right_fn}, max_iter={node.max_iterations}))")
        return var

    def _visit_ConvergenceLoop(self, node: ConvergenceLoop) -> str:
        var = self._new_var()
        self._emit(f"{var} = None")
        iter_var = self._new_var("_iter")
        self._emit(f"for {iter_var} in range({node.max_iterations}):")
        self._indent_level += 1
        if isinstance(node.body, Workflow):
            kwargs = [var]
            for op in node.body.operators:
                if op in self.DEPTH_MAP:
                    kwargs.append(f"detail_level={self.DEPTH_MAP[op]}")
                    break
            args_str = ", ".join(kwargs)
            self._emit(f"{var} = {node.body.id}({args_str})")
        else:
            body_var = self._visit(node.body)
            self._emit(f"{var} = {body_var}")
        cond_str = self._format_condition(node.condition, var)
        self._emit(f"if {cond_str}:")
        self._indent_level += 1
        self._emit("break")
        self._indent_level -= 1
        self._indent_level -= 1
        return var

    def _visit_Pipeline(self, node: Pipeline) -> str:
        current_var = None
        for step in node.steps:
            if current_var is None:
                current_var = self._visit(step)
            elif isinstance(step, Workflow):
                var = self._new_var()
                kwargs = [current_var]
                for op in step.operators:
                    if op in self.DEPTH_MAP:
                        kwargs.append(f"detail_level={self.DEPTH_MAP[op]}")
                        break
                args_str = ", ".join(kwargs)
                self._emit(f"{var} = {step.id}({args_str})")
                current_var = var
            else:
                step_var = self._visit(step)
                var = self._new_var()
                self._emit(f"{var} = {step_var}")
                current_var = var
        return current_var

    def _visit_Parallel(self, node: Parallel) -> str:
        fns = [self._visit_as_callable(b) for b in node.branches]
        var = self._new_var()
        self._use("parallel")
        fns_str = ", ".join(fns)
        self._emit("import asyncio")
        self._emit(f"{var} = asyncio.run(parallel({fns_str}))")
        return var

    def _visit_Morphism(self, node: Morphism) -> str:
        source_var = self._visit(node.source)
        target_var = self._visit(node.target)
        var = self._new_var()
        direction_map = {
            "forward": "morphism_forward",
            "reverse": "morphism_reverse",
            "lax": "morphism_lax",
            "oplax": "morphism_oplax",
            "directed_fusion": "morphism_directed_fuse",
            "pushforward": "morphism_pushforward",
        }
        fn_name = direction_map.get(node.direction, None)
        if fn_name:
            self._use(fn_name)
            self._emit(f"{var} = {fn_name}({source_var}, {target_var})")
        else:
            self._emit(f"{var} = ({source_var}, {target_var})  # 未知の射方向: {node.direction}")
        return var

    def _visit_Adjunction(self, node: Adjunction) -> str:
        var = self._new_var()
        if isinstance(node.right, OpenEnd) and not isinstance(node.left, OpenEnd):
            left_var = self._visit(node.left)
            wf_id = node.left.id if isinstance(node.left, Workflow) else left_var
            self._use("right_adjoint")
            self._emit(f'{var} = right_adjoint("{wf_id}")')
        elif isinstance(node.left, OpenEnd) and not isinstance(node.right, OpenEnd):
            right_var = self._visit(node.right)
            wf_id = node.right.id if isinstance(node.right, Workflow) else right_var
            self._use("left_adjoint")
            self._emit(f'{var} = left_adjoint("{wf_id}")')
        else:
            left_var = self._visit(node.left)
            right_var = self._visit(node.right)
            left_id = node.left.id if isinstance(node.left, Workflow) else left_var
            right_id = node.right.id if isinstance(node.right, Workflow) else right_var
            self._use("register_dual")
            self._emit(f'{var} = register_dual("{left_id}", "{right_id}")')
        return var

    # ========= 制御構文 =========

    def _visit_ForLoop(self, node: ForLoop) -> str:
        var = self._new_var()
        results_var = self._new_var("_results")
        self._emit(f"{results_var} = []")
        if isinstance(node.iterations, int):
            iter_var = self._new_var("_i")
            self._emit(f"for {iter_var} in range({node.iterations}):")
        else:
            iter_var = self._new_var("_item")
            items_str = ", ".join(repr(i) for i in node.iterations)
            self._emit(f"for {iter_var} in [{items_str}]:")
        self._indent_level += 1
        body_var = self._visit(node.body)
        self._emit(f"{results_var}.append({body_var})")
        self._indent_level -= 1
        self._emit(f"{var} = {results_var}")
        return var

    def _visit_IfCondition(self, node: IfCondition) -> str:
        var = self._new_var()
        cond_str = self._format_condition(node.condition)
        self._emit(f"if {cond_str}:")
        self._indent_level += 1
        then_var = self._visit(node.then_branch)
        self._emit(f"{var} = {then_var}")
        self._indent_level -= 1
        if node.else_branch:
            self._emit("else:")
            self._indent_level += 1
            else_var = self._visit(node.else_branch)
            self._emit(f"{var} = {else_var}")
            self._indent_level -= 1
        else:
            self._emit("else:")
            self._indent_level += 1
            self._emit(f"{var} = None")
            self._indent_level -= 1
        return var

    def _visit_WhileLoop(self, node: WhileLoop) -> str:
        var = self._new_var()
        self._emit(f"{var} = None")
        cond_str = self._format_condition(node.condition)
        self._emit(f"while {cond_str}:")
        self._indent_level += 1
        body_var = self._visit(node.body)
        self._emit(f"{var} = {body_var}")
        self._indent_level -= 1
        return var

    def _visit_Lambda(self, node: Lambda) -> str:
        var = self._new_var()
        params_str = ", ".join(node.params)
        saved_lines = self._lines[:]
        saved_counter = self._var_counter
        self._lines = []
        body_var = self._visit(node.body)
        body_lines = self._lines
        self._lines = saved_lines
        self._var_counter = saved_counter
        if len(body_lines) <= 1 and body_var:
            if body_lines:
                expr = body_lines[0].split(" = ", 1)[-1] if " = " in body_lines[0] else body_var
                self._emit(f"{var} = lambda {params_str}: {expr}")
            else:
                self._emit(f"{var} = lambda {params_str}: {body_var}")
        else:
            fn_name = self._new_var("_fn")
            self._emit(f"def {fn_name}({params_str}):")
            self._indent_level += 1
            for line in body_lines:
                self._emit(line.lstrip())
            self._emit(f"return {body_var}")
            self._indent_level -= 1
            self._emit(f"{var} = {fn_name}")
        return var

    def _visit_TaggedBlock(self, node: TaggedBlock) -> str:
        body_var = self._visit(node.body)
        var = self._new_var()
        tag_map = {"V": "validate", "C": "cycle", "R": "cycle", "M": "memo"}
        if node.tag in tag_map:
            fn_name = tag_map[node.tag]
            self._use(fn_name)
            self._emit(f"{var} = {fn_name}({body_var})")
        else:
            self._emit(f"{var} = {body_var}  # tag: {node.tag}")
        return var

    # ========= その他 =========

    def _visit_LetBinding(self, node: LetBinding) -> str:
        body_var = self._visit(node.body)
        self._emit(f"{node.name} = {body_var}")
        return node.name

    def _visit_Group(self, node: Group) -> str:
        return self._visit(node.body)

    def _visit_MacroRef(self, node: MacroRef) -> str:
        var = self._new_var()
        args_str = ", ".join(repr(a) for a in node.args) if node.args else ""
        self._emit(f"{var} = macro_{node.name}({args_str})")
        return var

    def _visit_ColimitExpansion(self, node: ColimitExpansion) -> str:
        var = self._new_var()
        self._use("dual")
        if isinstance(node.body, Workflow):
            wf = node.body
            kwargs = []
            for op in wf.operators:
                if op in self.DEPTH_MAP:
                    kwargs.append(f"detail_level={self.DEPTH_MAP[op]}")
                    break
            args_str = ", ".join(kwargs)
            self._emit(f'{var} = dual("{wf.id}")({args_str})')
        else:
            body_var = self._visit(node.body)
            self._emit(f"{var} = dual({body_var})")
        return var

    def _visit_OpenEnd(self, _node: OpenEnd) -> str:
        return "None"

    def _visit_PartialDiff(self, node: PartialDiff) -> str:
        body_var = self._visit(node.body)
        var = self._new_var()
        self._emit(f"{var} = partial_diff({body_var}, coordinate={repr(node.coordinate)})")
        return var

    def _visit_Integral(self, node: Integral) -> str:
        body_var = self._visit(node.body)
        var = self._new_var()
        self._emit(f"{var} = integrate({body_var})")
        return var

    def _visit_Summation(self, node: Summation) -> str:
        var = self._new_var()
        if node.body:
            body_var = self._visit(node.body)
            self._emit(f"{var} = sum_results({repr(node.items)}, {body_var})")
        else:
            self._emit(f"{var} = sum_results({repr(node.items)})")
        return var

    # ========= CCL-PL 拡張ノード (Phase 2) =========

    def _visit_RawExpr(self, node: RawExpr) -> str:
        """Python 式をそのまま出力"""
        var = self._new_var()
        self._emit(f"{var} = {node.code}")
        return var

    def _visit_FnDef(self, node: FnDef) -> str:
        """関数定義: fn name(params) { body } → Python def"""
        params_str = ", ".join(node.params)
        self._emit(f"def {node.name}({params_str}):")
        self._indent_level += 1
        if isinstance(node.body, RawExpr):
            self._emit(f"return {node.body.code}")
        else:
            body_var = self._visit(node.body)
            self._emit(f"return {body_var}")
        self._indent_level -= 1
        return node.name

    def _visit_FnCall(self, node: FnCall) -> str:
        """関数呼出: name(args)"""
        var = self._new_var()
        args = []
        for arg in node.args:
            if isinstance(arg, RawExpr):
                args.append(arg.code)
            else:
                args.append(self._visit(arg))
        args_str = ", ".join(args)
        self._emit(f"{var} = {node.name}({args_str})")
        return var

    def _visit_UseDecl(self, node: 'UseDecl') -> str:
        """モジュール宣言: use module.path → Python import"""
        # use hgk.telos → from ccl.stdlib.hgk.telos import *
        # use hgk → from ccl.stdlib.hgk import *
        parts = node.module_path.split('.')
        python_module = "ccl.stdlib." + node.module_path
        self._emit(f"from {python_module} import *")
        return "None"

    def _visit_AdjointDecl(self, node: 'AdjointDecl') -> str:
        """随伴対宣言: adjoint F <=> G → ランタイムに登録"""
        # __ccl_adjoint_pairs__ リストに追加（executor が参照）
        self._emit(f"__ccl_adjoint_pairs__ = __ccl_adjoint_pairs__ if '__ccl_adjoint_pairs__' in dir() else []")
        self._emit(f"__ccl_adjoint_pairs__.append(('{node.left}', '{node.right}'))")
        return "None"

    # ========= ヘルパー =========

    def _new_var(self, prefix: str = "v") -> str:
        self._var_counter += 1
        return f"{prefix}{self._var_counter}"

    def _emit(self, line: str) -> None:
        indented = "    " * self._indent_level + line
        self._lines.append(indented)

    def _use(self, fn_name: str) -> None:
        self._functions_used.add(fn_name)

    def _visit_as_callable(self, node: Any) -> str:
        """ノードをラムダとして返す (振動等で使用)"""
        if isinstance(node, Workflow):
            kwargs = []
            for op in node.operators:
                if op in self.DEPTH_MAP:
                    kwargs.append(f"detail_level={self.DEPTH_MAP[op]}")
                    break
            if kwargs:
                args_str = ", ".join(kwargs)
                return f"lambda _s=None: {node.id}(_s, {args_str})"
            return f"lambda _s=None: {node.id}(_s)"
        # 複合ノード → lambdaで包む
        saved_lines = self._lines[:]
        saved_counter = self._var_counter
        self._lines = []
        result_var = self._visit(node)
        body_lines = self._lines
        self._lines = saved_lines
        self._var_counter = saved_counter
        if body_lines:
            for line in body_lines:
                self._emit(line)
        return f"lambda _s=None: {result_var}"

    def _format_condition(self, cond: Any, result_var: str = "result") -> str:
        """条件ノードを Python 条件式にフォーマット"""
        if isinstance(cond, Condition):
            var_name = cond.var
            if var_name in ("V[]", "V"):
                var_name = result_var
            elif var_name in ("E[]", "E"):
                var_name = "error"
            return f"{var_name} {cond.op} {cond.value}"
        return str(cond)
