# PROOF: [L3/テスト] <- hermeneus/tests/test_parser.py Hermēneus パーサーテスト
"""
Hermēneus Parser Unit Tests

CCLParser の単体テスト。
"""

import pytest
import sys
from pathlib import Path

# パッケージパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hermeneus.src import compile_ccl
from hermeneus.src.ccl_ast import Workflow, Sequence, ConvergenceLoop, Fusion, Oscillation, ForLoop, IfCondition, WhileLoop, Lambda, OpType, PartialDiff, Integral, Summation
from hermeneus.src.parser import parse_ccl, CCLParser


class TestBasicWorkflows:
    """基本ワークフローのテスト"""
    
    # PURPOSE: 単純なワークフロー
    def test_simple_workflow(self):
        """単純なワークフロー"""
        ast = parse_ccl("/noe")
        assert isinstance(ast, Workflow)
        assert ast.id == "noe"
    
    # PURPOSE: /noe+ (深化)
    def test_workflow_with_deepen(self):
        """/noe+ (深化)"""
        ast = parse_ccl("/noe+")
        assert isinstance(ast, Workflow)
        assert ast.id == "noe"
        assert OpType.DEEPEN in ast.operators
    
    # PURPOSE: /bou- (縮約)
    def test_workflow_with_condense(self):
        """/bou- (縮約)"""
        ast = parse_ccl("/bou-")
        assert isinstance(ast, Workflow)
        assert ast.id == "bou"
        assert OpType.CONDENSE in ast.operators
    
    # PURPOSE: /noe+^ (深化 + 上昇)
    def test_workflow_with_multiple_ops(self):
        """/noe+^ (深化 + 上昇)"""
        ast = parse_ccl("/noe+^")
        assert isinstance(ast, Workflow)
        assert OpType.DEEPEN in ast.operators
        assert OpType.ASCEND in ast.operators
    
    # PURPOSE: /s! (全展開)
    def test_workflow_expand(self):
        """/s! (全展開)"""
        ast = parse_ccl("/s!")
        assert isinstance(ast, Workflow)
        assert OpType.EXPAND in ast.operators


class TestSequence:
    """シーケンスのテスト"""
    
    # PURPOSE: /s+_/ene
    def test_simple_sequence(self):
        """/s+_/ene"""
        ast = parse_ccl("/s+_/ene")
        assert isinstance(ast, Sequence)
        assert len(ast.steps) == 2
        assert ast.steps[0].id == "s"
        assert ast.steps[1].id == "ene"
    
    # PURPOSE: /boot_/bou_/ene
    def test_three_step_sequence(self):
        """/boot_/bou_/ene"""
        ast = parse_ccl("/boot_/bou_/ene")
        assert isinstance(ast, Sequence)
        assert len(ast.steps) == 3


class TestConvergenceLoop:
    """収束ループのテスト"""
    
    # PURPOSE: /noe+ ~> V[] < 0.3
    def test_simple_convergence(self):
        """/noe+ ~> V[] < 0.3"""
        ast = parse_ccl("/noe+ ~> V[] < 0.3")
        assert isinstance(ast, ConvergenceLoop)
        assert isinstance(ast.body, Workflow)
        assert ast.condition.var == "V[]"
        assert ast.condition.op == "<"
        assert ast.condition.value == 0.3
    
    # PURPOSE: lim[V[] < 0.3]{/noe+}
    def test_lim_formal(self):
        """lim[V[] < 0.3]{/noe+}"""
        ast = parse_ccl("lim[V[] < 0.3]{/noe+}")
        assert isinstance(ast, ConvergenceLoop)
        assert ast.condition.value == 0.3


class TestFusionAndOscillation:
    """融合と振動のテスト"""
    
    # PURPOSE: /noe * /dia
    def test_fusion(self):
        """/noe * /dia"""
        ast = parse_ccl("/noe * /dia")
        assert isinstance(ast, Fusion)
    
    # PURPOSE: /u+ ~ /noe!
    def test_oscillation(self):
        """/u+ ~ /noe!"""
        ast = parse_ccl("/u+ ~ /noe!")
        assert isinstance(ast, Oscillation)


class TestCPLControlStructures:
    """CPL v2.0 制御構文のテスト"""
    
    # PURPOSE: F:[×3]{/dia}
    def test_for_loop_count(self):
        """F:[×3]{/dia}"""
        ast = parse_ccl("F:[×3]{/dia}")
        assert isinstance(ast, ForLoop)
        assert ast.iterations == 3
    
    # PURPOSE: I:[V[] > 0.5]{/noe+}
    def test_if_condition(self):
        """I:[V[] > 0.5]{/noe+}"""
        ast = parse_ccl("I:[V[] > 0.5]{/noe+}")
        assert isinstance(ast, IfCondition)
        assert ast.condition.op == ">"
    
    # PURPOSE: I:[V[] > 0.5]{/noe+} E:{/noe-}
    def test_if_else(self):
        """I:[V[] > 0.5]{/noe+} E:{/noe-}"""
        ast = parse_ccl("I:[V[] > 0.5]{/noe+} E:{/noe-}")
        assert isinstance(ast, IfCondition)
        assert ast.else_branch is not None
    
    # PURPOSE: W:[E[] > 0.3]{/dia}
    def test_while_loop(self):
        """W:[E[] > 0.3]{/dia}"""
        ast = parse_ccl("W:[E[] > 0.3]{/dia}")
        assert isinstance(ast, WhileLoop)
    
    # PURPOSE: L:[wf]{wf+}
    def test_lambda(self):
        """L:[wf]{wf+}"""
        ast = parse_ccl("L:[wf]{wf+}")
        assert isinstance(ast, Lambda)
        assert "wf" in ast.params


class TestCompilation:
    """コンパイル統合テスト"""
    
    # PURPOSE: 単純なコンパイル
    def test_compile_simple(self):
        """単純なコンパイル"""
        lmql = compile_ccl("/noe+")
        assert "@lmql.query" in lmql
        assert "def ccl_noe" in lmql
    
    # PURPOSE: シーケンスのコンパイル
    def test_compile_sequence(self):
        """シーケンスのコンパイル"""
        lmql = compile_ccl("/s+_/ene")
        assert "Step 1" in lmql
        assert "Step 2" in lmql
    
    # PURPOSE: 収束ループのコンパイル
    def test_compile_convergence(self):
        """収束ループのコンパイル"""
        lmql = compile_ccl("/noe+ ~> V[] < 0.3")
        assert "MAX_ITERATIONS" in lmql
        assert "while" in lmql.lower()


class TestProcessOperators:
    """Process Layer 演算子のテスト (~*, ~!, \\, (), {})"""
    
    # PURPOSE: /dia+~*/noe (収束振動)
    def test_convergent_oscillation(self):
        """/dia+~*/noe (収束振動)"""
        ast = parse_ccl("/dia+~*/noe")
        assert isinstance(ast, Oscillation)
        assert ast.convergent is True
        assert ast.divergent is False
    
    # PURPOSE: /dia+~!/noe (発散振動)
    def test_divergent_oscillation(self):
        """/dia+~!/noe (発散振動)"""
        ast = parse_ccl("/dia+~!/noe")
        assert isinstance(ast, Oscillation)
        assert ast.divergent is True
        assert ast.convergent is False
    
    # PURPOSE: /dia+ ~ /noe (通常振動、既存互換)
    def test_plain_oscillation_unchanged(self):
        """/dia+ ~ /noe (通常振動、既存互換)"""
        ast = parse_ccl("/dia+ ~ /noe")
        assert isinstance(ast, Oscillation)
        assert ast.convergent is False
        assert ast.divergent is False
    
    # PURPOSE: (/dia+~*/noe) — 括弧グループの剥離
    def test_parenthesized_group(self):
        """(/dia+~*/noe) — 括弧グループの剥離"""
        ast = parse_ccl("(/dia+~*/noe)")
        assert isinstance(ast, Oscillation)
        assert ast.convergent is True
    
    # PURPOSE: {/dia+~*/noe} — ブレースグループの剥離
    def test_brace_group(self):
        """{/dia+~*/noe} — ブレースグループの剥離"""
        ast = parse_ccl("{/dia+~*/noe}")
        assert isinstance(ast, Oscillation)
        assert ast.convergent is True
    
    # PURPOSE: \pan+ — Colimit 演算子
    def test_colimit(self):
        """\\pan+ — Colimit 演算子"""
        from hermeneus.src.ccl_ast import ColimitExpansion
        ast = parse_ccl("\\pan+")
        assert isinstance(ast, ColimitExpansion)
        assert isinstance(ast.body, Workflow)
        assert ast.body.id == "pan"
    
    # PURPOSE: (/dia+~*/noe)~*/pan+ — ネストされた収束振動
    def test_nested_convergent(self):
        """(/dia+~*/noe)~*/pan+ — ネストされた収束振動"""
        ast = parse_ccl("(/dia+~*/noe)~*/pan+")
        assert isinstance(ast, Oscillation)
        assert ast.convergent is True
        # left は /dia+~*/noe の Oscillation
        assert isinstance(ast.left, Oscillation)
        assert ast.left.convergent is True
    
    # PURPOSE: {(/dia+~*/noe)~*/pan+} — マクロ前半
    def test_full_macro_group_a(self):
        """{(/dia+~*/noe)~*/pan+} — マクロ前半"""
        ast = parse_ccl("{(/dia+~*/noe)~*/pan+}")
        assert isinstance(ast, Oscillation)
        assert ast.convergent is True
    
    # PURPOSE: {(/dia+~*/noe)~*\pan+} — マクロ後半 (Colimit 含む)
    def test_full_macro_group_b(self):
        """{(/dia+~*/noe)~*\\pan+} — マクロ後半 (Colimit 含む)"""
        from hermeneus.src.ccl_ast import ColimitExpansion
        ast = parse_ccl("{(/dia+~*/noe)~*\\pan+}")
        assert isinstance(ast, Oscillation)
        assert ast.convergent is True
        assert isinstance(ast.right, ColimitExpansion)
    
    # PURPOSE: 完全マクロ: {(/dia+~*/noe)~*/pan+}~*{(/dia+~*/noe)~*\pan+}
    def test_full_macro(self):
        """完全マクロ: {(/dia+~*/noe)~*/pan+}~*{(/dia+~*/noe)~*\\pan+}"""
        ast = parse_ccl("{(/dia+~*/noe)~*/pan+}~*{(/dia+~*/noe)~*\\pan+}")
        assert isinstance(ast, Oscillation)
        assert ast.convergent is True
        # left = グループ A, right = グループ B
        assert isinstance(ast.left, Oscillation)
        assert isinstance(ast.right, Oscillation)


class TestFusionMeta:
    """融合メタ表示 (*^) のテスト"""
    
    # PURPOSE: /u+*^/u^ — 基本的な *^ 融合
    def test_fusion_meta_basic(self):
        """/u+*^/u^ — 基本的な *^ 融合"""
        ast = parse_ccl("/u+*^/u^")
        assert isinstance(ast, Fusion)
        assert ast.meta_display is True
        assert isinstance(ast.left, Workflow)
        assert ast.left.id == "u"
        assert isinstance(ast.right, Workflow)
        assert ast.right.id == "u"
    
    # PURPOSE: *^ と * の区別
    def test_fusion_meta_vs_plain(self):
        """*^ と * の区別"""
        ast_meta = parse_ccl("/noe*^/dia")
        ast_plain = parse_ccl("/noe*/dia")
        assert isinstance(ast_meta, Fusion)
        assert isinstance(ast_plain, Fusion)
        assert ast_meta.meta_display is True
        assert ast_plain.meta_display is False
    
    # PURPOSE: /dox+*^/u+_/bye+ — マクロ @learn 相当
    def test_fusion_meta_in_sequence(self):
        """/dox+*^/u+_/bye+ — マクロ @learn 相当"""
        ast = parse_ccl("/dox+*^/u+_/bye+")
        assert isinstance(ast, Sequence)
        assert isinstance(ast.steps[0], Fusion)
        assert ast.steps[0].meta_display is True


class TestPipeline:
    """分散パイプライン (&>) のテスト (v7.6)"""
    
    # PURPOSE: /noe+&>/dia+ — 基本パイプライン
    def test_pipeline_basic(self):
        """/noe+&>/dia+ — 基本パイプライン"""
        from hermeneus.src.ccl_ast import Pipeline
        ast = parse_ccl("/noe+&>/dia+")
        assert isinstance(ast, Pipeline)
        assert len(ast.steps) == 2
        assert ast.steps[0].id == "noe"
        assert ast.steps[1].id == "dia"
    
    # PURPOSE: /noe+&>/dia+&>/ene — 3段パイプライン
    def test_pipeline_three_steps(self):
        """/noe+&>/dia+&>/ene — 3段パイプライン"""
        from hermeneus.src.ccl_ast import Pipeline
        ast = parse_ccl("/noe+&>/dia+&>/ene")
        assert isinstance(ast, Pipeline)
        assert len(ast.steps) == 3
    
    # PURPOSE: /boot_/noe+&>/dia+ — &> は _ より弱い結合力 → Pipeline(Seq(boot,noe+), dia+)
    def test_pipeline_in_sequence(self):
        """/boot_/noe+&>/dia+ — &> は _ より弱い結合力 → Pipeline(Seq(boot,noe+), dia+)"""
        from hermeneus.src.ccl_ast import Pipeline
        ast = parse_ccl("/boot_/noe+&>/dia+")
        assert isinstance(ast, Pipeline)
        assert len(ast.steps) == 2
        assert isinstance(ast.steps[0], Sequence)  # /boot_/noe+ がシーケンス
        assert isinstance(ast.steps[1], Workflow)   # /dia+ が単体 WF


class TestParallel:
    """分散並列 (&&) のテスト (v7.6)"""
    
    # PURPOSE: /noe+&&/dia+ — 基本並列
    def test_parallel_basic(self):
        """/noe+&&/dia+ — 基本並列"""
        from hermeneus.src.ccl_ast import Parallel
        ast = parse_ccl("/noe+&&/dia+")
        assert isinstance(ast, Parallel)
        assert len(ast.branches) == 2
        assert ast.branches[0].id == "noe"
        assert ast.branches[1].id == "dia"
    
    # PURPOSE: /noe+&&/dia+&&/ene — 3並列
    def test_parallel_three_branches(self):
        """/noe+&&/dia+&&/ene — 3並列"""
        from hermeneus.src.ccl_ast import Parallel
        ast = parse_ccl("/noe+&&/dia+&&/ene")
        assert isinstance(ast, Parallel)
        assert len(ast.branches) == 3
    
    # PURPOSE: /boot_/noe+&&/dia+ — && は _ より弱い結合力 → Parallel(Seq(boot,noe+), dia+)
    def test_parallel_in_sequence(self):
        """/boot_/noe+&&/dia+ — && は _ より弱い結合力 → Parallel(Seq(boot,noe+), dia+)"""
        from hermeneus.src.ccl_ast import Parallel
        ast = parse_ccl("/boot_/noe+&&/dia+")
        assert isinstance(ast, Parallel)
        assert len(ast.branches) == 2
        assert isinstance(ast.branches[0], Sequence)  # /boot_/noe+ がシーケンス
        assert isinstance(ast.branches[1], Workflow)   # /dia+ が単体 WF


class TestMorphism:
    """射演算子 (>*, <*, *>, >%, <<) のテスト"""

    # PURPOSE: /noe+>*/dia+ — Lax (投射して融合)
    def test_lax(self):
        """/noe+>*/dia+ → Morphism(direction='lax')"""
        from hermeneus.src.ccl_ast import Morphism
        ast = parse_ccl("/noe+>*/dia+")
        assert isinstance(ast, Morphism)
        assert isinstance(ast.source, Workflow)
        assert ast.source.id == "noe"
        assert isinstance(ast.target, Workflow)
        assert ast.target.id == "dia"
        assert ast.direction == "lax"

    # PURPOSE: /noe+<*/dia+ — Oplax (引き込んで融合)
    def test_oplax(self):
        """/noe+<*/dia+ → Morphism(direction='oplax')"""
        from hermeneus.src.ccl_ast import Morphism
        ast = parse_ccl("/noe+<*/dia+")
        assert isinstance(ast, Morphism)
        assert ast.source.id == "noe"
        assert ast.target.id == "dia"
        assert ast.direction == "oplax"

    # PURPOSE: /noe+*>/dia+ — 方向付き融合
    def test_directed_fusion(self):
        """/noe+*>/dia+ → Morphism(direction='directed_fusion')"""
        from hermeneus.src.ccl_ast import Morphism
        ast = parse_ccl("/noe+*>/dia+")
        assert isinstance(ast, Morphism)
        assert ast.direction == "directed_fusion"

    # PURPOSE: /noe+>%/dia+ — Pushforward
    def test_pushforward(self):
        """/noe+>%/dia+ → Morphism(direction='pushforward')"""
        from hermeneus.src.ccl_ast import Morphism
        ast = parse_ccl("/noe+>%/dia+")
        assert isinstance(ast, Morphism)
        assert ast.direction == "pushforward"

    # PURPOSE: /noe+<</dia+ — 逆射 (pullback)
    def test_reverse(self):
        """/noe+<</dia+ → Morphism(direction='reverse')"""
        from hermeneus.src.ccl_ast import Morphism
        ast = parse_ccl("/noe+<</dia+")
        assert isinstance(ast, Morphism)
        assert ast.direction == "reverse"

    # PURPOSE: <* の右結合テスト — /noe<*/dia<*/ene
    def test_oplax_chaining(self):
        """/noe<*/dia<*/ene → ネスト構造"""
        from hermeneus.src.ccl_ast import Morphism
        ast = parse_ccl("/noe<*/dia<*/ene")
        assert isinstance(ast, Morphism)
        assert ast.direction == "oplax"
        assert isinstance(ast.target, Morphism)
        assert ast.target.direction == "oplax"


class TestAdjunction:
    """随伴演算子 (|>, <|, ||) のテスト (v7.6)"""
    
    # PURPOSE: /noe+|> — 右随伴 (単項後置)
    def test_right_adjunction(self):
        """/noe+|> — 右随伴: Adjunction(left=WF, right=OpenEnd)"""
        from hermeneus.src.ccl_ast import Adjunction, OpenEnd
        ast = parse_ccl("/noe+|>")
        assert isinstance(ast, Adjunction)
        assert isinstance(ast.left, Workflow)
        assert ast.left.id == "noe"
        assert isinstance(ast.right, OpenEnd)
    
    # PURPOSE: /dia+<| — 左随伴 (単項後置: WF が G 側)
    def test_left_adjunction(self):
        """/dia+<| — 左随伴: Adjunction(left=OpenEnd, right=WF)"""
        from hermeneus.src.ccl_ast import Adjunction, OpenEnd
        ast = parse_ccl("/dia+<|")
        assert isinstance(ast, Adjunction)
        assert isinstance(ast.left, OpenEnd)
        assert isinstance(ast.right, Workflow)
        assert ast.right.id == "dia"
    
    # PURPOSE: /noe+||/dia+ — 随伴宣言 (F ⊣ G)
    def test_adjunction_declaration(self):
        """/noe+||/dia+ — 随伴宣言: Adjunction(left=noe, right=dia)"""
        from hermeneus.src.ccl_ast import Adjunction
        ast = parse_ccl("/noe+||/dia+")
        assert isinstance(ast, Adjunction)
        assert isinstance(ast.left, Workflow)
        assert ast.left.id == "noe"
        assert isinstance(ast.right, Workflow)
        assert ast.right.id == "dia"


class TestElifAndLet:
    """EI: (ELIF) と let 構文のテスト"""
    
    # PURPOSE: EI:[cond]{body} — トップレベル EI: は IF として処理
    def test_elif_toplevel(self):
        """EI:[cond]{body} — トップレベル EI: は IF として処理"""
        ast = parse_ccl("EI:[V[]>0.5]{/noe+}")
        assert isinstance(ast, IfCondition)
        assert ast.condition.op == ">"
    
    # PURPOSE: I:[V[]>0.5]{/noe+}EI:[V[]<0.3]{/ene+}E:{/zet}
    def test_if_elif_else_chain(self):
        """I:[V[]>0.5]{/noe+}EI:[V[]<0.3]{/ene+}E:{/zet}"""
        ast = parse_ccl("I:[V[]>0.5]{/noe+}EI:[V[]<0.3]{/ene+}E:{/zet}")
        assert isinstance(ast, IfCondition)
        assert ast.else_branch is not None
        # else_branch は ネストされた IfCondition (EI → I 変換)
        assert isinstance(ast.else_branch, IfCondition)
        assert ast.else_branch.else_branch is not None  # E:{/zet}
    
    # PURPOSE: let x = /noe — 変数束縛 (@ なし)
    def test_let_variable_binding(self):
        """let x = /noe — 変数束縛 (@ なし)"""
        from hermeneus.src.ccl_ast import LetBinding
        ast = parse_ccl("let x = /noe")
        assert isinstance(ast, LetBinding)
        assert ast.name == "x"
        assert isinstance(ast.body, Workflow)
        assert ast.body.id == "noe"
    
    # PURPOSE: let @think = /noe+_/dia — マクロ定義 (@ 付き)
    def test_let_macro_definition(self):
        """let @think = /noe+_/dia — マクロ定義 (@ 付き)"""
        from hermeneus.src.ccl_ast import LetBinding
        ast = parse_ccl("let @think = /noe+_/dia")
        assert isinstance(ast, LetBinding)
        assert ast.name == "think"
        assert isinstance(ast.body, Sequence)
    
    # PURPOSE: let result = /noe+~/dia — 複雑な式
    def test_let_complex_expression(self):
        """let result = /noe+~/dia — 複雑な式"""
        from hermeneus.src.ccl_ast import LetBinding
        ast = parse_ccl("let result = /noe+~/dia")
        assert isinstance(ast, LetBinding)
        assert ast.name == "result"
        assert isinstance(ast.body, Oscillation)


class TestTaggedBlocks:
    """V:/C:/R:/M: タグ付きブロックのテスト"""
    
    # PURPOSE: V:{/noe~/dia} — 検証ブロック
    def test_verify_block(self):
        """V:{/noe~/dia} — 検証ブロック"""
        from hermeneus.src.ccl_ast import TaggedBlock
        ast = parse_ccl("V:{/noe~/dia}")
        assert isinstance(ast, TaggedBlock)
        assert ast.tag == "V"
    
    # PURPOSE: C:{/dia+_/ene+} — サイクルブロック
    def test_cycle_block(self):
        """C:{/dia+_/ene+} — サイクルブロック"""
        from hermeneus.src.ccl_ast import TaggedBlock
        ast = parse_ccl("C:{/dia+_/ene+}")
        assert isinstance(ast, TaggedBlock)
        assert ast.tag == "C"
    
    # PURPOSE: R:{/u+} — 累積融合ブロック
    def test_reduce_block(self):
        """R:{/u+} — 累積融合ブロック"""
        from hermeneus.src.ccl_ast import TaggedBlock
        ast = parse_ccl("R:{/u+}")
        assert isinstance(ast, TaggedBlock)
        assert ast.tag == "R"
    
    # PURPOSE: M:{/dox-} — 記憶ブロック
    def test_memo_block(self):
        """M:{/dox-} — 記憶ブロック"""
        from hermeneus.src.ccl_ast import TaggedBlock
        ast = parse_ccl("M:{/dox-}")
        assert isinstance(ast, TaggedBlock)
        assert ast.tag == "M"


class TestConvergentOscillationBehavior:
    """B1: ~* (収束振動 / terminal coalgebra) の操作的テスト

    F6 operators.md で定義: ~* = terminal coalgebra (最大不動点への収束)
    Colimit (合流点) との区別を検証する。
    """

    # PURPOSE: ~* の max_iterations フィールドに既定値がある
    def test_convergent_has_max_iterations(self):
        """~* ノードは max_iterations=5 をデフォルトで持つ"""
        ast = parse_ccl("/dia+~*/noe")
        assert isinstance(ast, Oscillation)
        assert ast.convergent is True
        assert ast.max_iterations == 5  # terminal coalgebra: 有限で打ち切り

    # PURPOSE: 通常振動 ~ には max_iterations があるが convergent=False
    def test_plain_oscillation_not_convergent(self):
        """~ は ~* ではない: convergent=False"""
        ast = parse_ccl("/dia+~/noe")
        assert isinstance(ast, Oscillation)
        assert ast.convergent is False
        assert ast.max_iterations == 5  # 存在するが収束判定には使わない

    # PURPOSE: format_ast_tree が ~* を正しく表示する
    def test_ast_tree_shows_convergent_mode(self):
        """AST tree 表示で (~*) と表記される"""
        from hermeneus.src.dispatch import format_ast_tree
        ast = parse_ccl("/dia+~*/noe")
        tree = format_ast_tree(ast)
        assert "(~*)" in tree
        assert "Oscillation" in tree

    # PURPOSE: ネストされた ~* が全て convergent=True
    def test_nested_convergent_all_true(self):
        """(/dia+~*/noe)~*/pan+ — 全ネスト層が convergent"""
        ast = parse_ccl("(/dia+~*/noe)~*/pan+")
        assert isinstance(ast, Oscillation)
        assert ast.convergent is True
        assert isinstance(ast.left, Oscillation)
        assert ast.left.convergent is True
        # right は単純な Workflow
        assert isinstance(ast.right, Workflow)
        assert ast.right.id == "pan"

    # PURPOSE: ~* と ~ の混合ネスト
    def test_mixed_convergent_and_plain(self):
        """(/dia+~/noe)~*/pan+ — 内側は通常振動、外側が収束"""
        ast = parse_ccl("(/dia+~/noe)~*/pan+")
        assert isinstance(ast, Oscillation)
        assert ast.convergent is True  # 外側
        assert isinstance(ast.left, Oscillation)
        assert ast.left.convergent is False  # 内側は通常

    # PURPOSE: dispatch 出力に adaptive_depth が含まれる
    def test_dispatch_includes_adaptive_depth(self):
        """dispatch() の結果に adaptive_depth キーがある"""
        from hermeneus.src.dispatch import dispatch
        result = dispatch("/noe-~*/dia")
        assert result["success"] is True
        assert "adaptive_depth" in result
        assert result["adaptive_depth"]["current_level"] == 2  # IR max_depth: /dia (無修飾=L2) が式全体の最大
        assert len(result["adaptive_depth"]["triggers"]) == 3

    # PURPOSE: dispatch 出力の depth_level が ~* によって変わらない
    def test_convergent_does_not_affect_depth(self):
        """~* はプロセス演算子であり、深度レベルには影響しない"""
        from hermeneus.src.dispatch import dispatch
        result_plain = dispatch("/noe~/dia")
        result_conv = dispatch("/noe~*/dia")
        assert result_plain["depth_level"] == result_conv["depth_level"]


class TestFEPOperators:
    """FEP 演算子のテスト"""

    # --- ∂ (偏微分) ---

    # PURPOSE: ∂Pr/noe の基本パース
    def test_partial_diff_basic(self):
        """∂Pr/noe — Precision 座標での偏微分"""
        ast = parse_ccl("∂Pr/noe")
        assert isinstance(ast, PartialDiff)
        assert ast.coordinate == "Pr"
        assert isinstance(ast.body, Workflow)
        assert ast.body.id == "noe"

    # PURPOSE: ∂に深化修飾子が付いた場合
    def test_partial_diff_with_modifier(self):
        """∂Va/bou+ — Value 座標 + 深化"""
        ast = parse_ccl("∂Va/bou+")
        assert isinstance(ast, PartialDiff)
        assert ast.coordinate == "Va"
        assert isinstance(ast.body, Workflow)
        assert ast.body.id == "bou"
        assert OpType.DEEPEN in ast.body.operators

    # PURPOSE: ∂の不正構文でエラー
    def test_partial_diff_invalid(self):
        """∂without_slash — 不正構文"""
        with pytest.raises(ValueError, match="Invalid partial diff"):
            parse_ccl("∂Pr_noe")

    # --- ∫ (積分) ---

    # PURPOSE: ∫/ath+ の基本パース
    def test_integral_basic(self):
        """∫/ath+ — 過去の省察を累積統合"""
        ast = parse_ccl("∫/ath+")
        assert isinstance(ast, Integral)
        assert isinstance(ast.body, Workflow)
        assert ast.body.id == "ath"
        assert OpType.DEEPEN in ast.body.operators

    # PURPOSE: ∫/noe — 無修飾
    def test_integral_no_modifier(self):
        """∫/noe — 無修飾の積分"""
        ast = parse_ccl("∫/noe")
        assert isinstance(ast, Integral)
        assert isinstance(ast.body, Workflow)
        assert ast.body.id == "noe"

    # --- Σ (総和) ---

    # PURPOSE: Σ[results] の基本パース
    def test_summation_basic(self):
        """Σ[results] — アイテムのみ"""
        ast = parse_ccl("Σ[results]")
        assert isinstance(ast, Summation)
        assert ast.items == "results"
        assert ast.body is None

    # PURPOSE: Σ[findings]{/noe+} — body 付き
    def test_summation_with_body(self):
        """Σ[findings]{/noe+} — アイテム + body"""
        ast = parse_ccl("Σ[findings]{/noe+}")
        assert isinstance(ast, Summation)
        assert ast.items == "findings"
        assert isinstance(ast.body, Workflow)
        assert ast.body.id == "noe"
        assert OpType.DEEPEN in ast.body.operators

    # PURPOSE: Σの不正構文でエラー
    def test_summation_invalid(self):
        """Σno_bracket — 不正構文"""
        with pytest.raises(ValueError, match="Invalid summation"):
            parse_ccl("Σno_brackets")

    # --- 組合せ ---

    # PURPOSE: ∫/ath+_Σ[results] — シーケンスには確認が必要
    # 現状 ∫ は次の WF のみを body に取るため、シーケンス中では _ 分割が先行する

    # PURPOSE: ∂Pr/noe の dispatch 表示確認
    def test_partial_diff_dispatch_tree(self):
        """∂Pr/noe の AST ツリー表示"""
        from hermeneus.src.dispatch import format_ast_tree
        ast = parse_ccl("∂Pr/noe")
        tree = format_ast_tree(ast)
        assert "PartialDiff (∂Pr)" in tree
        assert "Workflow: /noe" in tree

    # PURPOSE: ∫/ath+ の dispatch 表示確認
    def test_integral_dispatch_tree(self):
        """∫/ath+ の AST ツリー表示"""
        from hermeneus.src.dispatch import format_ast_tree
        ast = parse_ccl("∫/ath+")
        tree = format_ast_tree(ast)
        assert "Integral (∫)" in tree
        assert "Workflow: /ath+" in tree

    # PURPOSE: Σ[findings]{/noe+} の dispatch 表示確認
    def test_summation_dispatch_tree(self):
        """Σ[findings]{/noe+} の AST ツリー表示"""
        from hermeneus.src.dispatch import format_ast_tree
        ast = parse_ccl("Σ[findings]{/noe+}")
        tree = format_ast_tree(ast)
        assert "Σ[findings]" in tree
        assert "Workflow: /noe+" in tree

    # PURPOSE: FEP 演算子の body から WF 抽出
    def test_fep_extract_workflows(self):
        """FEP ノードから WF ID が抽出される"""
        from hermeneus.src.dispatch import extract_workflows
        # ∂Pr/noe
        ast_pd = parse_ccl("∂Pr/noe")
        wfs_pd = extract_workflows(ast_pd)
        assert "/noe" in wfs_pd
        # ∫/ath+
        ast_int = parse_ccl("∫/ath+")
        wfs_int = extract_workflows(ast_int)
        assert "/ath" in wfs_int
        # Σ[x]{/bou}
        ast_sum = parse_ccl("Σ[x]{/bou}")
        wfs_sum = extract_workflows(ast_sum)
        assert "/bou" in wfs_sum
        # Σ[x] (body なし)
        ast_sum_no = parse_ccl("Σ[x]")
        wfs_sum_no = extract_workflows(ast_sum_no)
        assert wfs_sum_no == []


# =============================================================================
# S極動詞 (v5.0) テスト
# =============================================================================

class TestSPoleVerbs:
    """v5.0 で追加された S極 (感覚) 12動詞のパーステスト。"""

    # S極12動詞の ID リスト
    S_VERBS = ["the", "ant", "ere", "agn", "sap", "ski", "prs", "per", "apo", "exe", "his", "prg"]

    def test_all_s_verbs_in_workflows(self):
        """S極12動詞が全て WORKFLOWS セットに登録されている。"""
        for verb in self.S_VERBS:
            assert verb in CCLParser.WORKFLOWS, f"/{verb} が WORKFLOWS に未登録"

    def test_all_36_verbs_registered(self):
        """v5.0 の全36動詞が WORKFLOWS に登録されている (I/A極24 + S極12)。"""
        all_36 = [
            # I/A極 24動詞
            "noe", "bou", "zet", "ene",
            "ske", "sag", "pei", "tek",
            "kat", "epo", "pai", "dok",
            "lys", "ops", "akr", "arc",
            "beb", "ele", "kop", "dio",
            "hyp", "prm", "ath", "par",
            # S極 12動詞
            "the", "ant", "ere", "agn", "sap", "ski",
            "prs", "per", "apo", "exe", "his", "prg",
        ]
        for verb in all_36:
            assert verb in CCLParser.WORKFLOWS, f"/{verb} が WORKFLOWS に未登録"

    @pytest.mark.parametrize("verb", S_VERBS)
    def test_s_verb_basic_parse(self, verb):
        """各S極動詞が単体でパースできる。"""
        ast = parse_ccl(f"/{verb}")
        assert isinstance(ast, Workflow)
        assert ast.id == verb

    @pytest.mark.parametrize("verb", S_VERBS)
    def test_s_verb_with_plus(self, verb):
        """S極動詞 + 修飾子 (+) のパース。"""
        ast = parse_ccl(f"/{verb}+")
        assert isinstance(ast, Workflow)
        assert ast.id == verb
        assert OpType.DEEPEN in ast.operators

    @pytest.mark.parametrize("verb", S_VERBS)
    def test_s_verb_with_minus(self, verb):
        """S極動詞 - 修飾子 (-) のパース。"""
        ast = parse_ccl(f"/{verb}-")
        assert isinstance(ast, Workflow)
        assert ast.id == verb
        assert OpType.CONDENSE in ast.operators

    def test_s_verb_sequence(self):
        """S極動詞を含むシーケンスのパース。"""
        ast = parse_ccl("/the+_/noe+")
        assert isinstance(ast, Sequence)
        assert len(ast.steps) == 2
        assert ast.steps[0].id == "the"
        assert ast.steps[1].id == "noe"

    def test_s_verb_oscillation(self):
        """S極動詞を含む振動のパース。"""
        ast = parse_ccl("/ere+~/agn+")
        assert isinstance(ast, Oscillation)
        assert ast.left.id == "ere"
        assert ast.right.id == "agn"

    def test_s_verb_in_loop(self):
        """S極動詞をループ内で使用。"""
        ast = parse_ccl("F:[×3]{/sap+~/ski+}")
        assert isinstance(ast, ForLoop)
        assert ast.iterations == 3

    # --- RELATION_PARTNERS (.d/.h/.x) テスト ---

    # S極の .d ペア (族内S極対角)
    S_D_PAIRS = [
        ("the", "ant"), ("ere", "agn"), ("sap", "ski"),
        ("prs", "per"), ("apo", "exe"), ("his", "prg"),
    ]

    @pytest.mark.parametrize("verb,partner", S_D_PAIRS)
    def test_s_verb_relation_d(self, verb, partner):
        """S極動詞の .d (対角=随伴) 展開。"""
        ast = parse_ccl(f"/{verb}.d")
        assert isinstance(ast, Sequence)
        assert ast.steps[0].id == verb
        assert ast.steps[1].id == partner

    # S極の .h パートナー (同座標I極)
    S_H_PARTNERS = [
        ("the", "noe"), ("ant", "bou"), ("ere", "ske"), ("agn", "sag"),
        ("sap", "kat"), ("ski", "epo"), ("prs", "lys"), ("per", "ops"),
        ("apo", "beb"), ("exe", "ele"), ("his", "hyp"), ("prg", "prm"),
    ]

    @pytest.mark.parametrize("verb,partner", S_H_PARTNERS)
    def test_s_verb_relation_h(self, verb, partner):
        """S極動詞の .h (水平=自然変換) 展開。"""
        ast = parse_ccl(f"/{verb}.h")
        assert isinstance(ast, Sequence)
        assert ast.steps[0].id == verb
        assert ast.steps[1].id == partner

    def test_s_verb_relation_d_symmetry(self):
        """S極 .d は対称: /the.d → ant, /ant.d → the。"""
        ast_fwd = parse_ccl("/the.d")
        ast_rev = parse_ccl("/ant.d")
        assert ast_fwd.steps[1].id == "ant"
        assert ast_rev.steps[1].id == "the"

    def test_s_verb_with_modifier(self):
        """S極動詞 + 座標修飾子のパース。"""
        ast = parse_ccl("/the+[Va:E]")
        assert isinstance(ast, Workflow)
        assert ast.id == "the"
        assert "Va" in ast.modifiers


# =============================================================================
# H-series 前動詞（中動態）テスト
# =============================================================================

class TestPreVerbs:
    """H-series 前動詞 [xx] 記法のパーステスト。"""

    from hermeneus.src.ccl_ast import PreVerb

    # 全12前動詞 ID
    ALL_PREVERBS = ["tr", "sy", "pa", "he", "ek", "th", "eu", "sh", "ho", "ph", "an", "pl"]

    # PURPOSE: 全12前動詞が PREVERBS セットに登録されている
    def test_all_preverbs_registered(self):
        """全12前動詞が CCLParser.PREVERBS に登録されている。"""
        for pv in self.ALL_PREVERBS:
            assert pv in CCLParser.PREVERBS, f"[{pv}] が PREVERBS に未登録"

    # PURPOSE: 全12前動詞に正式名がマッピングされている
    def test_all_preverb_names_mapped(self):
        """全12前動詞に PREVERB_NAMES マッピングがある。"""
        for pv in self.ALL_PREVERBS:
            assert pv in CCLParser.PREVERB_NAMES, f"[{pv}] の正式名が未設定"
            assert len(CCLParser.PREVERB_NAMES[pv]) > 0

    @pytest.mark.parametrize("pv_id", ALL_PREVERBS)
    def test_preverb_basic_parse(self, pv_id):
        """各前動詞が [xx] 記法でパースできる。"""
        from hermeneus.src.ccl_ast import PreVerb
        ast = parse_ccl(f"[{pv_id}]")
        assert isinstance(ast, PreVerb)
        assert ast.id == pv_id
        assert ast.full_name == CCLParser.PREVERB_NAMES[pv_id]

    # PURPOSE: [th] の具体的なパース結果を検証
    def test_thambos_parse(self):
        """[th] → PreVerb(id='th', full_name='Thambos')"""
        from hermeneus.src.ccl_ast import PreVerb
        ast = parse_ccl("[th]")
        assert isinstance(ast, PreVerb)
        assert ast.id == "th"
        assert ast.full_name == "Thambos"

    # PURPOSE: 前動詞とワークフローのシーケンス
    def test_preverb_sequence(self):
        """[ph]_/noe+ → Sequence(PreVerb, Workflow)"""
        from hermeneus.src.ccl_ast import PreVerb
        ast = parse_ccl("[ph]_/noe+")
        assert isinstance(ast, Sequence)
        assert len(ast.steps) == 2
        assert isinstance(ast.steps[0], PreVerb)
        assert ast.steps[0].id == "ph"
        assert isinstance(ast.steps[1], Workflow)
        assert ast.steps[1].id == "noe"

    # PURPOSE: 前動詞とワークフローの射 (>% = pushforward)
    # 注: >> は CCL で収束ループ演算子として優先パースされるため >% を使用
    def test_preverb_morphism(self):
        """[th]>%/noe → Morphism(PreVerb, Workflow)"""
        from hermeneus.src.ccl_ast import PreVerb, Morphism
        ast = parse_ccl("[th]>%/noe")
        assert isinstance(ast, Morphism)
        assert isinstance(ast.source, PreVerb)
        assert ast.source.id == "th"
        assert isinstance(ast.target, Workflow)
        assert ast.target.id == "noe"

    # PURPOSE: 前動詞同士のシーケンス
    def test_preverb_pair_sequence(self):
        """[ho]_[ph] → Sequence(PreVerb, PreVerb)"""
        from hermeneus.src.ccl_ast import PreVerb
        ast = parse_ccl("[ho]_[ph]")
        assert isinstance(ast, Sequence)
        assert len(ast.steps) == 2
        assert isinstance(ast.steps[0], PreVerb)
        assert ast.steps[0].id == "ho"
        assert isinstance(ast.steps[1], PreVerb)
        assert ast.steps[1].id == "ph"

    # PURPOSE: 未知の略記は PreVerb にならない（修飾子ブラケットとして消費されてパースエラー）
    def test_unknown_bracket_not_preverb(self):
        """[zz] は PreVerb として認識されず、パースエラーになる。"""
        with pytest.raises((ValueError, Exception)):
            parse_ccl("[zz]")

    # ---- dispatch 統合テスト ----

    # PURPOSE: format_ast_tree が PreVerb を正しく表示する
    def test_format_ast_tree_preverb(self):
        """format_ast_tree が PreVerb を '中動態宣言' として表示する。"""
        from hermeneus.src.dispatch import format_ast_tree
        from hermeneus.src.ccl_ast import PreVerb
        ast = parse_ccl("[th]")
        assert isinstance(ast, PreVerb)
        tree = format_ast_tree(ast)
        assert "PreVerb:" in tree
        assert "[th]" in tree
        assert "Thambos" in tree
        assert "中動態宣言" in tree

    # PURPOSE: extract_workflows が PreVerb をスキップする
    def test_extract_workflows_excludes_preverb(self):
        """extract_workflows は PreVerb を WF リストに含めない。"""
        from hermeneus.src.dispatch import extract_workflows
        ast = parse_ccl("[th]_/noe+")
        wfs = extract_workflows(ast)
        assert "/noe" in wfs
        # PreVerb の ID は WF リストに含まれない
        assert "[th]" not in wfs
        assert "/th" not in wfs
        assert len(wfs) == 1

    # PURPOSE: format_ast_tree が PreVerb + Workflow シーケンスを正しく表示
    def test_format_ast_tree_preverb_sequence(self):
        """[ph]_/noe+ のツリー表示で PreVerb と Workflow が並ぶ。"""
        from hermeneus.src.dispatch import format_ast_tree
        ast = parse_ccl("[ph]_/noe+")
        tree = format_ast_tree(ast)
        assert "PreVerb:" in tree
        assert "Workflow:" in tree
        assert "[ph]" in tree
        assert "/noe+" in tree

    # PURPOSE: dispatch 統合テスト ([an]_/hyp+)
    def test_dispatch_preverb_section(self):
        """[an]_/hyp+ の dispatch 結果に PreVerb セクションが含まれる"""
        from hermeneus.src.dispatch import dispatch
        result = dispatch("[an]_/hyp+")
        assert result["success"] is True
        tmpl = result["plan_template"]
        assert "【前動詞 (H-series) 環境設定】" in tmpl
        assert "[an] Anamnēsis" in tmpl

    # PURPOSE: dispatch 統合テスト BDQ チェックリスト
    def test_dispatch_preverb_bdq(self):
        """BDQ チェックリスト (Detection / Labeling / Transition) が含まれる"""
        from hermeneus.src.dispatch import dispatch
        result = dispatch("[an]_/hyp+")
        tmpl = result["plan_template"]
        assert "□ Detection:" in tmpl
        assert "□ Labeling:" in tmpl
        assert "□ Transition:" in tmpl

    # PURPOSE: dispatch 統合テスト L3 外部検索義務セクション
    def test_dispatch_l3_search_section_present(self):
        """L3 (+ 修飾子) の dispatch 結果に外部検索義務セクションが含まれる"""
        from hermeneus.src.dispatch import dispatch
        result = dispatch("/noe+")
        assert result["success"] is True
        tmpl = result["plan_template"]
        assert "【L3 外部検索義務 — N-5 θ5.2】" in tmpl
        assert "□ Periskopē" in tmpl
        assert "□ Gnōsis" in tmpl
        assert "□ S2" in tmpl

    # PURPOSE: dispatch 統合テスト L2 では外部検索義務セクションが含まれない
    def test_dispatch_l2_no_search_section(self):
        """L2 (無印) の dispatch 結果には外部検索義務セクションが含まれない"""
        from hermeneus.src.dispatch import dispatch
        result = dispatch("/noe")
        assert result["success"] is True
        tmpl = result["plan_template"]
        assert "【L3 外部検索義務" not in tmpl

# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
