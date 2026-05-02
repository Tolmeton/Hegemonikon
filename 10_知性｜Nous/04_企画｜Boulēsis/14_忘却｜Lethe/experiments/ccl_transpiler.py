# CCL-PL トランスパイラ — CCL AST → Python ソースコード
"""
CCL → Python トランスパイラ

Hermeneus の CCL パーサーが生成する AST を入力として受け取り、
実行可能な Python ソースコードを出力する。

構造: Visitor パターン。各 AST ノード型に対して visit_* メソッドを定義。

使用例:
    from hermeneus.src.parser import CCLParser
    from ccl_transpiler import CCLTranspiler
    
    parser = CCLParser()
    ast = parser.parse("/noe+_/dia_/ene+")
    
    transpiler = CCLTranspiler()
    python_source = transpiler.transpile(ast)
    print(python_source)
"""

import sys
from pathlib import Path
from textwrap import indent
from typing import Any, List, Optional

# Hermeneus パーサーへのパス追加
_MEKHANE_SRC = Path(__file__).parent.parent.parent / "20_機構｜Mekhane" / "_src｜ソースコード"
if str(_MEKHANE_SRC) not in sys.path:
    sys.path.insert(0, str(_MEKHANE_SRC))

from hermeneus.src.ccl_ast import (
    ASTNode, Workflow, Sequence, Fusion, Oscillation,
    ConvergenceLoop, Adjunction, Pipeline, Parallel, Morphism,
    ForLoop, IfCondition, WhileLoop, Lambda, TaggedBlock,
    ColimitExpansion, LetBinding, Group, MacroRef, OpenEnd,
    PartialDiff, Integral, Summation, Condition, OpType,
)
from hermeneus.src.parser import CCLParser


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
        """トランスパイラを初期化する
        
        Args:
            desugar: True の場合、振動 (~) と メタ (^) を純粋な
                     Python 構文に desugar する。False (デフォルト) の場合は
                     ランタイム関数 (oscillate 等) に委譲する。
                     Creator の洞察: 全演算子は構文的に表現可能。
        """
        self._desugar = desugar
        self._var_counter = 0
        self._indent_level = 0
        self._lines: List[str] = []
        self._functions_used: set = set()  # ランタイム関数の使用追跡
    
    def transpile(self, ast: ASTNode, include_header: bool = True) -> str:
        """AST を Python ソースコードに変換する
        
        Args:
            ast: Hermeneus パーサーが生成した AST ノード
            include_header: ランタイム import を含めるか
        
        Returns:
            実行可能な Python ソースコード文字列
        """
        self._var_counter = 0
        self._indent_level = 0
        self._lines = []
        self._functions_used = set()
        
        # AST をトラバースして本体を生成
        result_var = self._visit(ast)
        
        # ヘッダー (ランタイム import) を生成
        header_lines = []
        if include_header and self._functions_used:
            imports = sorted(self._functions_used)
            header_lines.append(f"from ccl_runtime import {', '.join(imports)}")
            header_lines.append("")
        
        # 組み立て
        body = "\n".join(self._lines)
        
        if result_var:
            body += f"\n\n# === CCL 実行結果 ===\nresult = {result_var}"
        
        if header_lines:
            return "\n".join(header_lines) + "\n" + body
        return body
    
    # =========================================================================
    # Visitor ディスパッチ
    # =========================================================================
    
    def _visit(self, node: Any) -> Optional[str]:
        """AST ノードの型に応じて visit_* メソッドにディスパッチ"""
        if node is None:
            return None
        
        type_name = type(node).__name__
        visitor = getattr(self, f"_visit_{type_name}", None)
        
        if visitor is None:
            # 未対応のノード型 → コメントとして残す
            self._emit(f"# [未対応] {type_name}: {node}")
            return None
        
        return visitor(node)
    
    # =========================================================================
    # 基本ノード
    # =========================================================================
    
    def _visit_Workflow(self, node: Workflow) -> str:
        """ワークフロー → 関数呼出し
        
        /noe+  → noe(detail_level=3)
        /noe   → noe()
        /noe\  → dual("noe")()
        /noe^  → meta(noe)()  (desugar=True の場合)
        """
        var = self._new_var()
        is_inverted = OpType.INVERT in node.operators
        is_meta = OpType.ASCEND in node.operators
        
        # 引数構築
        kwargs = []
        
        # 深度修飾子
        for op in node.operators:
            if op in self.DEPTH_MAP:
                kwargs.append(f"detail_level={self.DEPTH_MAP[op]}")
                break
        
        # ブラケット修飾子
        for key, value in node.modifiers.items():
            if not key.startswith("_"):  # 内部キーは除外
                kwargs.append(f"{key}={repr(value)}")
        
        args_str = ", ".join(kwargs)
        
        if is_inverted:
            # \ 演算子: dual() で逆変換を取得して呼び出す
            self._use("dual")
            self._emit(f"{var} = dual(\"{node.id}\")({args_str})")
        elif is_meta and self._desugar:
            # ^ 演算子 (desugar): ネスト構造として生成
            # ^A = A をリストの各要素に適用 = 関手的適用
            # meta(fn)(items) → [fn(item) for item in items]
            self._use("meta")
            self._emit(f"{var} = meta({node.id})({args_str})  # ^ = ネスト (MB入れ子)")
        else:
            self._emit(f"{var} = {node.id}({args_str})")
        
        return var
    
    def _visit_Sequence(self, node: Sequence) -> str:
        """シーケンス → 逐次呼出し (前の結果を次に渡す)
        
        /noe+_/dia_/ene+  →
            v0 = noe(detail_level=3)
            v1 = dia(v0)
            v2 = ene(v1, detail_level=3)
        """
        prev_var = None
        last_var = None
        
        for step in node.steps:
            if prev_var is not None and isinstance(step, Workflow):
                # 前の結果を最初の引数として渡す
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
        """融合 → merge() / product()
        
        /noe * /dia   → merge(noe(), dia())
        /noe % /dia   → product(noe(), dia())
        /noe *% /dia  → merge(product(noe(), dia()))
        """
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
        """振動 → oscillate() / converge() / diverge()
        
        desugar=False (デフォルト):
            /u ~ /noe    → oscillate(u, noe)
            /u ~* /noe   → converge(u, noe)
            /u ~! /noe   → diverge(u, noe)
        
        desugar=True:
            /u ~ /noe    → for ループに展開 (F:[×N]{a_b})
            /u ~* /noe   → while ループ + 収束判定
        """
        if self._desugar:
            return self._visit_Oscillation_desugared(node)
        
        # 左右をラムダで包む (関数として渡す必要がある)
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
    
    def _visit_Oscillation_desugared(self, node: Oscillation) -> str:
        """振動の desugar — ランタイム関数を使わず純粋な for/while ループに展開
        
        Creator の洞察: ~ は F:[×N]{a_b} で構文化できる。
        AI が必要なのは構造ではなくパラメータ (何回回すか、いつ止めるか)。
        
        ~  (通常振動):  for ループに展開
        ~* (収束振動):  while ループ + 収束判定
        ~! (発散振動):  for ループ + 結果蓄積
        """
        max_iter = node.max_iterations
        var = self._new_var()
        state_var = self._new_var("_state")
        results_var = self._new_var("_osc_results")
        iter_var = self._new_var("_osc_i")
        
        # 左右のノードから関数名を取得
        left_name = node.left.id if isinstance(node.left, Workflow) else "fn_a"
        right_name = node.right.id if isinstance(node.right, Workflow) else "fn_b"
        
        # 左右の引数構築
        left_kwargs = self._build_kwargs(node.left)
        right_kwargs = self._build_kwargs(node.right)
        
        if node.convergent:
            # ~* (収束振動): while ループ + 収束判定
            # = F:[conv]{a_b} — 安定するまで交互適用
            prev_var = self._new_var("_prev")
            self._emit(f"# ~* desugar: 収束振動 → while ループ")
            self._emit(f"# = F:[conv]{{{left_name}_{right_name}}} (収束まで交互適用)")
            self._emit(f"{state_var} = None")
            self._emit(f"{prev_var} = None")
            self._emit(f"for {iter_var} in range({max_iter}):")
            self._indent_level += 1
            self._emit(f"{prev_var} = {state_var}")
            self._emit(f"{state_var} = {left_name}({state_var}{left_kwargs})  # 往路")
            self._emit(f"{state_var} = {right_name}({state_var}{right_kwargs})  # 復路")
            self._emit(f"if {prev_var} is not None and {state_var} == {prev_var}:  # 収束判定")
            self._indent_level += 1
            self._emit(f"break  # 不動点に到達")
            self._indent_level -= 1
            self._indent_level -= 1
            self._emit(f"{var} = {state_var}")
        
        elif node.divergent:
            # ~! (発散振動): for ループ + 全結果蓄積
            # = F:[×N]{a_b} — 結果を全て保持
            self._emit(f"# ~! desugar: 発散振動 → for ループ (全結果蓄積)")
            self._emit(f"# = F:[×{max_iter}]{{{left_name}_{right_name}}} (全展開)")
            self._emit(f"{results_var} = []")
            self._emit(f"{state_var} = None")
            self._emit(f"for {iter_var} in range({max_iter}):")
            self._indent_level += 1
            self._emit(f"{state_var} = {left_name}({state_var}{left_kwargs})")
            self._emit(f"{results_var}.append(('a', {iter_var}, {state_var}))")
            self._emit(f"{state_var} = {right_name}({state_var}{right_kwargs})")
            self._emit(f"{results_var}.append(('b', {iter_var}, {state_var}))")
            self._indent_level -= 1
            self._emit(f"{var} = {results_var}  # 発散: 全軌跡を保持")
        
        else:
            # ~ (通常振動): for ループに展開
            # = F:[×N]{a_b} — 交互適用の反復
            self._emit(f"# ~ desugar: 振動 → for ループ")
            self._emit(f"# = F:[×{max_iter}]{{{left_name}_{right_name}}} (交互適用)")
            self._emit(f"{results_var} = []")
            self._emit(f"{state_var} = None")
            self._emit(f"for {iter_var} in range({max_iter}):")
            self._indent_level += 1
            self._emit(f"{state_var} = {left_name}({state_var}{left_kwargs})  # 往路")
            self._emit(f"{results_var}.append(('a', {iter_var}, {state_var}))")
            self._emit(f"{state_var} = {right_name}({state_var}{right_kwargs})  # 復路")
            self._emit(f"{results_var}.append(('b', {iter_var}, {state_var}))")
            self._indent_level -= 1
            self._emit(f"{var} = {results_var}")
        
        return var
    
    def _build_kwargs(self, node: Any) -> str:
        """ノードから追加キーワード引数文字列を構築 (desugar 用)"""
        if not isinstance(node, Workflow):
            return ""
        kwargs = []
        for op in node.operators:
            if op in self.DEPTH_MAP:
                kwargs.append(f"detail_level={self.DEPTH_MAP[op]}")
                break
        if kwargs:
            return ", " + ", ".join(kwargs)
        return ""
    
    def _visit_ConvergenceLoop(self, node: ConvergenceLoop) -> str:
        """収束ループ → while ループ
        
        /noe+ >> V[] < 0.3  →
            v0 = None
            for _iter in range(5):
                v0 = noe(v0, detail_level=3)
                if v0 < 0.3:
                    break
        """
        var = self._new_var()
        self._emit(f"{var} = None")
        
        iter_var = self._new_var("_iter")
        self._emit(f"for {iter_var} in range({node.max_iterations}):")
        
        self._indent_level += 1
        
        # body を実行
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
        
        # 収束条件
        cond_str = self._format_condition(node.condition, var)
        self._emit(f"if {cond_str}:")
        self._indent_level += 1
        self._emit("break")
        self._indent_level -= 1
        
        self._indent_level -= 1
        
        return var
    
    def _visit_Pipeline(self, node: Pipeline) -> str:
        """分散パイプライン → ネストした関数呼出し
        
        /noe+ &> /dia &> /ene  →  ene(dia(noe(detail_level=3)))
        """
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
        """分散並列 → asyncio.gather
        
        /noe+ && /dia+  →
            import asyncio
            v = asyncio.run(parallel(
                lambda: noe(detail_level=3),
                lambda: dia(detail_level=3)
            ))
        """
        fns = []
        for branch in node.branches:
            fn = self._visit_as_callable(branch)
            fns.append(fn)
        
        var = self._new_var()
        self._use("parallel")
        fns_str = ", ".join(fns)
        self._emit(f"import asyncio")
        self._emit(f"{var} = asyncio.run(parallel({fns_str}))")
        
        return var
    
    def _visit_Morphism(self, node: Morphism) -> str:
        """射 (Morphism) → 構造的変換関数呼び出し
        
        /noe+ >> /ene  →  morphism_forward(noe(...), ene)
        /noe << /ene   →  morphism_reverse(noe(...), ene)  # pullback
        /noe >* /ene   →  morphism_lax(noe(...), ene)      # lax actegory
        """
        source_var = self._visit(node.source)
        target_var = self._visit(node.target)
        var = self._new_var()
        
        if node.direction == 'forward':
            self._use("morphism_forward")
            self._emit(f"{var} = morphism_forward({source_var}, {target_var})  # >> 順射")
        elif node.direction == 'reverse':
            self._use("morphism_reverse")
            self._emit(f"{var} = morphism_reverse({source_var}, {target_var})  # << 逆射 (pullback)")
        elif node.direction == 'lax':
            self._use("morphism_lax")
            self._emit(f"{var} = morphism_lax({source_var}, {target_var})  # >* 射的融合 (Lax Actegory)")
        elif node.direction == 'oplax':
            self._use("morphism_oplax")
            self._emit(f"{var} = morphism_oplax({source_var}, {target_var})  # <* 逆射融合 (Oplax)")
        elif node.direction == 'directed_fusion':
            self._use("morphism_directed_fuse")
            self._emit(f"{var} = morphism_directed_fuse({source_var}, {target_var})  # *> 方向付き融合")
        elif node.direction == 'pushforward':
            self._use("morphism_pushforward")
            self._emit(f"{var} = morphism_pushforward({source_var}, {target_var})  # >% 射的展開 (Pushforward)")
        else:
            self._emit(f"{var} = ({source_var}, {target_var})  # 未知の射方向: {node.direction}")
        
        return var
    
    def _visit_Adjunction(self, node: Adjunction) -> str:
        """随伴演算子 → register_dual / right_adjoint / left_adjoint
        
        /noe || /zet  → register_dual("noe", "zet")  (随伴宣言)
        /noe|>        → right_adjoint("noe")          (右随伴取得)
        /zet<|        → left_adjoint("zet")           (左随伴取得)
        """
        var = self._new_var()
        
        # 右随伴取得: left = WF, right = OpenEnd
        if isinstance(node.right, OpenEnd) and not isinstance(node.left, OpenEnd):
            left_var = self._visit(node.left)
            wf_id = node.left.id if isinstance(node.left, Workflow) else left_var
            self._use("right_adjoint")
            self._emit(f'{var} = right_adjoint("{wf_id}")  # |> 右随伴取得')
        # 左随伴取得: left = OpenEnd, right = WF
        elif isinstance(node.left, OpenEnd) and not isinstance(node.right, OpenEnd):
            right_var = self._visit(node.right)
            wf_id = node.right.id if isinstance(node.right, Workflow) else right_var
            self._use("left_adjoint")
            self._emit(f'{var} = left_adjoint("{wf_id}")  # <| 左随伴取得')
        # 随伴宣言: left = F, right = G
        else:
            left_var = self._visit(node.left)
            right_var = self._visit(node.right)
            left_id = node.left.id if isinstance(node.left, Workflow) else left_var
            right_id = node.right.id if isinstance(node.right, Workflow) else right_var
            self._use("register_dual")
            self._emit(f'{var} = register_dual("{left_id}", "{right_id}")  # || 随伴宣言 F ⊣ G')
        
        return var
    
    # =========================================================================
    # 制御構文
    # =========================================================================
    
    def _visit_ForLoop(self, node: ForLoop) -> str:
        """FOR ループ
        
        F:[×3]{/dia}      → for _ in range(3): dia(...)
        F:[A,B,C]{/dia}   → for x in [A, B, C]: dia(x)
        """
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
        """IF 条件分岐
        
        I:[V[] > 0.5]{/noe+} E:{/noe-}  →
            if result > 0.5:
                noe(detail_level=3)
            else:
                noe(detail_level=1)
        """
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
        """WHILE ループ
        
        W:[E[] > 0.3]{/dia}  →
            while error > 0.3:
                dia(...)
        """
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
        """Lambda
        
        L:[x]{x+}  →  lambda x: x_deep(x)
        """
        var = self._new_var()
        params_str = ", ".join(node.params)
        
        # Lambda の body はインラインで生成
        saved_lines = self._lines[:]
        saved_counter = self._var_counter
        self._lines = []
        
        body_var = self._visit(node.body)
        body_lines = self._lines
        
        self._lines = saved_lines
        self._var_counter = saved_counter
        
        if len(body_lines) <= 1 and body_var:
            # 1行で収まる場合 → lambda として出力
            if body_lines:
                # body_lines[0] は "vN = expr" 形式 → expr 部分を取り出す
                expr = body_lines[0].split(" = ", 1)[-1] if " = " in body_lines[0] else body_var
                self._emit(f"{var} = lambda {params_str}: {expr}")
            else:
                self._emit(f"{var} = lambda {params_str}: {body_var}")
        else:
            # 複数行 → def で定義
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
        """タグ付きブロック
        
        V:{/noe~/dia}  → validate(oscillate(noe, dia))
        C:{/dia+_/ene+} → cycle(lambda: dia_then_ene())
        M:{/dox-}       → memo(dox())
        """
        body_var = self._visit(node.body)
        var = self._new_var()
        
        tag_map = {
            "V": ("validate", "validate"),
            "C": ("cycle", "cycle"),
            "R": ("cycle", "cycle"),  # Repeat も同じ
            "M": ("memo", "memo"),
        }
        
        if node.tag in tag_map:
            runtime_fn, use_name = tag_map[node.tag]
            self._use(use_name)
            self._emit(f"{var} = {runtime_fn}({body_var})")
        else:
            # 未知のタグ → そのまま
            self._emit(f"{var} = {body_var}  # tag: {node.tag}")
        
        return var
    
    # =========================================================================
    # その他のノード
    # =========================================================================
    
    def _visit_LetBinding(self, node: LetBinding) -> str:
        """変数束縛 / マクロ定義
        
        let x = /noe+  →  x = noe(detail_level=3)
        """
        body_var = self._visit(node.body)
        self._emit(f"{node.name} = {body_var}")
        return node.name
    
    def _visit_Group(self, node: Group) -> str:
        """グループ修飾子"""
        return self._visit(node.body)
    
    def _visit_MacroRef(self, node: MacroRef) -> str:
        """マクロ参照 → 関数呼出し"""
        var = self._new_var()
        args_str = ", ".join(repr(a) for a in node.args) if node.args else ""
        self._emit(f"{var} = macro_{node.name}({args_str})")
        return var
    
    def _visit_ColimitExpansion(self, node: ColimitExpansion) -> str:
        """双対生成 (\\) — 式全体の逆変換を生成
        
        \\A         → dual("A")()
        \\(A _ B _ C) → dual("C")(dual("B")(dual("A")()))  # 逆順 + 各ステップ双対
        \\(A * B)    → product(A, B)  # 融合の双対 = 展開
        \\(A ~* B)   → diverge(A, B)  # 収束の双対 = 発散
        """
        var = self._new_var()
        self._use("dual")
        
        # ケース別処理
        if isinstance(node.body, Workflow):
            # \\A → dual("A")()
            wf = node.body
            kwargs = []
            for op in wf.operators:
                if op in self.DEPTH_MAP:
                    kwargs.append(f"detail_level={self.DEPTH_MAP[op]}")
                    break
            args_str = ", ".join(kwargs)
            self._emit(f"{var} = dual(\"{wf.id}\")({args_str})")
        
        elif isinstance(node.body, Sequence):
            # \\(A _ B _ C) → 逆順で各ステップを双対化
            # C' ← B' ← A' (逆変換パイプライン)
            reversed_steps = list(reversed(node.body.steps))
            prev_var = None
            
            for step in reversed_steps:
                if isinstance(step, Workflow):
                    step_var = self._new_var()
                    kwargs = []
                    if prev_var:
                        kwargs.append(prev_var)
                    for op in step.operators:
                        if op in self.DEPTH_MAP:
                            kwargs.append(f"detail_level={self.DEPTH_MAP[op]}")
                            break
                    args_str = ", ".join(kwargs)
                    self._emit(f"{step_var} = dual(\"{step.id}\")({args_str})")
                    prev_var = step_var
                else:
                    # 非ワークフロー → そのまま双対化
                    body_var = self._visit(step)
                    step_var = self._new_var()
                    self._emit(f"{step_var} = dual({body_var})")
                    prev_var = step_var
            
            self._emit(f"{var} = {prev_var}")
        
        elif isinstance(node.body, Fusion):
            # \\(A * B) → product(A, B)  (融合の双対 = 展開)
            left_var = self._visit(node.body.left)
            right_var = self._visit(node.body.right)
            
            if node.body.outer_product:
                # \\(A % B) → merge(A, B)  (展開の双対 = 融合)
                self._use("merge")
                self._emit(f"{var} = merge({left_var}, {right_var})  # \\ 展開→融合")
            else:
                # \\(A * B) → product(A, B)  (融合の双対 = 展開)
                self._use("product")
                self._emit(f"{var} = product({left_var}, {right_var})  # \\ 融合→展開")
        
        elif isinstance(node.body, Oscillation):
            # \\(A ~* B) → diverge(A, B)  (収束の双対 = 発散)
            left_fn = self._visit_as_callable(node.body.left)
            right_fn = self._visit_as_callable(node.body.right)
            
            if node.body.convergent:
                # \\(~*) → ~! (収束の双対 = 発散)
                self._use("diverge")
                self._emit(f"{var} = diverge({left_fn}, {right_fn}, max_iter={node.body.max_iterations})  # \\ 収束→発散")
            elif node.body.divergent:
                # \\(~!) → ~* (発散の双対 = 収束)
                self._use("converge")
                self._emit(f"{var} = converge({left_fn}, {right_fn}, max_iter={node.body.max_iterations})  # \\ 発散→収束")
            else:
                # \\(~) → ~ (振動は自己双対)
                self._use("oscillate")
                self._emit(f"{var} = list(oscillate({right_fn}, {left_fn}, max_iter={node.body.max_iterations}))  # \\ 振動 (左右反転)")
        
        else:
            # その他 → 汎用 dual() 呼出し
            body_var = self._visit(node.body)
            self._emit(f"{var} = dual({body_var})")
        
        return var
    
    def _visit_OpenEnd(self, _node: OpenEnd) -> str:
        """開放端 → None"""
        return "None"
    
    def _visit_PartialDiff(self, node: PartialDiff) -> str:
        """偏微分 → 座標制約付き呼出し"""
        body_var = self._visit(node.body)
        var = self._new_var()
        self._emit(f"{var} = partial_diff({body_var}, coordinate={repr(node.coordinate)})  # ∂{node.coordinate}")
        return var
    
    def _visit_Integral(self, node: Integral) -> str:
        """積分 → 履歴統合"""
        body_var = self._visit(node.body)
        var = self._new_var()
        self._emit(f"{var} = integrate({body_var})  # ∫ 履歴統合")
        return var
    
    def _visit_Summation(self, node: Summation) -> str:
        """総和 → 集約"""
        var = self._new_var()
        if node.body:
            body_var = self._visit(node.body)
            self._emit(f"{var} = sum_results({repr(node.items)}, {body_var})  # Σ[{node.items}]")
        else:
            self._emit(f"{var} = sum_results({repr(node.items)})  # Σ[{node.items}]")
        return var
    
    # =========================================================================
    # ヘルパー
    # =========================================================================
    
    def _visit_as_callable(self, node: Any) -> str:
        """ノードを callable (lambda) として生成"""
        if isinstance(node, Workflow):
            kwargs = []
            for op in node.operators:
                if op in self.DEPTH_MAP:
                    kwargs.append(f"detail_level={self.DEPTH_MAP[op]}")
                    break
            args_str = ", ".join(kwargs)
            return f"lambda x=None: {node.id}(x{', ' + args_str if args_str else ''})"
        else:
            # 複雑なノード → 一旦 def に包む
            saved_lines = self._lines[:]
            saved_counter = self._var_counter
            saved_indent = self._indent_level
            self._lines = []
            self._indent_level = 1  # def の内部
            
            body_var = self._visit(node)
            body_lines = self._lines
            
            self._lines = saved_lines
            self._var_counter = saved_counter
            self._indent_level = saved_indent
            
            fn_name = self._new_var("_fn")
            self._emit(f"def {fn_name}(x=None):")
            self._indent_level += 1
            for line in body_lines:
                # body_lines は indent_level=1 で生成されているので、
                # 先頭の4スペースを取り除く
                stripped = line.lstrip()
                self._emit(stripped)
            self._emit(f"return {body_var}")
            self._indent_level -= 1
            
            return fn_name
    
    def _new_var(self, prefix: str = "v") -> str:
        """新しい変数名を生成"""
        self._var_counter += 1
        return f"{prefix}{self._var_counter}"
    
    def _emit(self, line: str) -> None:
        """インデント付きで行を追加"""
        indented = "    " * self._indent_level + line
        self._lines.append(indented)
    
    def _use(self, fn_name: str) -> None:
        """ランタイム関数の使用を記録"""
        self._functions_used.add(fn_name)
    
    def _format_condition(self, cond: Condition, result_var: Optional[str] = None) -> str:
        """条件式を Python 条件文に変換"""
        # V[] → result_var or "value"、E[] → "error"
        var_name = cond.var
        if var_name.startswith("V["):
            var_name = result_var if result_var else "value"
        elif var_name.startswith("E["):
            var_name = "error"
        
        op_map = {"<": "<", ">": ">", "<=": "<=", ">=": ">=", "=": "=="}
        py_op = op_map.get(cond.op, cond.op)
        
        return f"{var_name} {py_op} {cond.value}"


# =============================================================================
# 便利関数
# =============================================================================

def transpile_ccl(ccl_source: str, include_header: bool = True, desugar: bool = False) -> str:
    """CCL 式を Python ソースに変換する便利関数
    
    Args:
        ccl_source: CCL 式文字列 (例: "/noe+_/dia_/ene+")
        include_header: ランタイム import を含めるか
        desugar: True の場合、振動 (~) とメタ (^) を純粋な
                 Python 構文に展開する (ランタイム関数を使わない)
    
    Returns:
        Python ソースコード文字列
    """
    # << (逆射/pullback) の前処理
    # パーサーに << が未実装なので、ここで検出して専用変換する
    if '<<' in ccl_source:
        return _transpile_backward(ccl_source, include_header, desugar=desugar)
    
    parser = CCLParser()
    ast = parser.parse(ccl_source)
    
    transpiler = CCLTranspiler(desugar=desugar)
    return transpiler.transpile(ast, include_header=include_header)


def _transpile_backward(ccl_source: str, include_header: bool = True, desugar: bool = False) -> str:
    """<< (逆射) を含む CCL 式を Python に変換する
    
    CCL: goal << A << B << C
    Python: result = dual("C")(dual("B")(dual("A")(goal_result)))
    
    意味: 目標 (goal) から逆算して、A → B → C の双対を順に適用し入力を推定する
    """
    # << で分割
    segments = [s.strip() for s in ccl_source.split('<<')]
    
    if len(segments) < 2:
        # フォールバック
        parser = CCLParser()
        ast = parser.parse(ccl_source)
        transpiler = CCLTranspiler(desugar=desugar)
        return transpiler.transpile(ast, include_header=include_header)
    
    parser = CCLParser()
    transpiler = CCLTranspiler(desugar=desugar)
    
    # 使用するランタイム関数
    functions_used = {"dual"}
    
    lines = []
    
    # goal (最初のセグメント) → 値として評価
    goal_segment = segments[0]
    goal_ast = parser.parse(goal_segment)
    goal_code = transpiler.transpile(goal_ast, include_header=False).strip()
    
    # goal のコード行を追加
    goal_lines = [l for l in goal_code.split('\n') if l.strip() and not l.strip().startswith('#')]
    lines.extend(goal_lines)
    
    # result 変数を特定 (最後の代入先)
    goal_var = "result"
    for line in reversed(goal_lines):
        if '=' in line and not line.strip().startswith('#'):
            goal_var = line.split('=')[0].strip()
            break
    
    # << チェインを dual() の連鎖に変換
    lines.append("")
    lines.append("# << 逆射: 目標から逆算して入力を推定する")
    lines.append(f"_bw = {goal_var}")
    
    for i, segment in enumerate(segments[1:], 1):
        # 各セグメントからWF名を抽出
        seg = segment.strip().lstrip('/')
        
        # 修飾子の検出
        for mod_char in ['+', '-', '^']:
            if seg.endswith(mod_char):
                seg = seg[:-1]
                break
        
        lines.append(f"_bw = dual(\"{seg}\")(_bw)  # << ステップ {i}")
    
    # ヘッダー生成
    header = ""
    if include_header:
        all_funcs = sorted(functions_used | transpiler._functions_used)
        if all_funcs:
            header = f"from ccl_runtime import {', '.join(all_funcs)}\n\n"
    
    body = "\n".join(lines)
    body += "\n\n# === CCL 実行結果 ===\nresult = _bw"
    
    return header + body


# =============================================================================
# CLI エントリポイント
# =============================================================================

if __name__ == "__main__":
    import sys
    
    # --desugar フラグの検出
    desugar_flag = "--desugar" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--desugar"]
    
    if args:
        ccl_expr = " ".join(args)
    else:
        ccl_expr = input("CCL式を入力: ")
    
    mode_label = "desugar" if desugar_flag else "standard"
    print(f"\n# === CCL 入力 ({mode_label} モード) ===")
    print(f"# {ccl_expr}")
    print(f"# === Python 出力 ===\n")
    print(transpile_ccl(ccl_expr, desugar=desugar_flag))
