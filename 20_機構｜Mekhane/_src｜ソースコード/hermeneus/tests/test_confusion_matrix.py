"""F6: Confusion Matrix テスト — 全演算子ペアの区別保証。

パーサーが視覚的に類似する演算子を正しく区別できることを保証する。
各テストは「この演算子をあの演算子と間違えたらどうなるか」を検証。

Origin: 2026-02-23 CCL 演算子混同防止対策 (F6)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from hermeneus.src.parser import CCLParser
from hermeneus.src.ccl_ast import Sequence, Workflow, Oscillation, Fusion


class TestConfusionMatrix:
    """視覚的に類似する演算子ペアの区別テスト。"""

    # ─── _ vs - ─────────────────────────────────────────────

    def test_underscore_parses_as_sequence(self):
        """/dia_/fit は Sequence になる (NOT Workflow with condense)。"""
        parser = CCLParser()
        ast = parser.parse("/dia_/fit")
        assert isinstance(ast, Sequence), f"Expected Sequence, got {type(ast).__name__}"
        assert len(ast.steps) == 2
        assert ast.steps[0].id == "dia"
        assert ast.steps[1].id == "fit"
        # dia には演算子がない
        assert len(ast.steps[0].operators) == 0

    def test_hyphen_parses_as_condense(self):
        """/dia- は Workflow with CONDENSE operator。"""
        parser = CCLParser()
        ast = parser.parse("/dia-")
        assert isinstance(ast, Workflow), f"Expected Workflow, got {type(ast).__name__}"
        assert ast.id == "dia"
        from hermeneus.src.ccl_ast import OpType
        assert OpType.CONDENSE in ast.operators

    def test_underscore_then_hyphen_distinct(self):
        """/dia_/dia- は Sequence(dia, dia-) — 区別される。"""
        parser = CCLParser()
        ast = parser.parse("/dia_/dia-")
        assert isinstance(ast, Sequence)
        assert len(ast.steps) == 2
        # step 1: /dia (no operators)
        assert ast.steps[0].id == "dia"
        assert len(ast.steps[0].operators) == 0
        # step 2: /dia- (CONDENSE)
        assert ast.steps[1].id == "dia"
        from hermeneus.src.ccl_ast import OpType
        assert OpType.CONDENSE in ast.steps[1].operators

    def test_hyphen_then_underscore_distinct(self):
        """/dia-_/fit は Sequence(dia-, fit)。"""
        parser = CCLParser()
        ast = parser.parse("/dia-_/fit")
        assert isinstance(ast, Sequence)
        assert len(ast.steps) == 2
        from hermeneus.src.ccl_ast import OpType
        assert OpType.CONDENSE in ast.steps[0].operators
        assert len(ast.steps[1].operators) == 0

    # ─── ~ vs - ─────────────────────────────────────────────

    def test_tilde_parses_as_oscillation(self):
        """/noe~/dia は Oscillation になる (NOT condense)。"""
        parser = CCLParser()
        ast = parser.parse("/noe~/dia")
        assert isinstance(ast, Oscillation), f"Expected Oscillation, got {type(ast).__name__}"

    def test_tilde_vs_hyphen_distinct(self):
        """/noe~/dia と /noe-/dia は異なる AST。"""
        parser = CCLParser()
        ast_tilde = parser.parse("/noe~/dia")
        ast_hyphen = parser.parse("/noe-_/dia")
        # tilde = Oscillation
        assert isinstance(ast_tilde, Oscillation)
        # hyphen = Sequence(noe-, dia) or Workflow with condense
        assert not isinstance(ast_hyphen, Oscillation)

    # ─── * vs + ─────────────────────────────────────────────

    def test_star_parses_as_fusion(self):
        """/noe*/dia は Fusion になる (NOT deepen)。"""
        parser = CCLParser()
        ast = parser.parse("/noe*/dia")
        assert isinstance(ast, Fusion), f"Expected Fusion, got {type(ast).__name__}"

    def test_plus_parses_as_deepen(self):
        """/noe+ は Workflow with DEEPEN。"""
        parser = CCLParser()
        ast = parser.parse("/noe+")
        assert isinstance(ast, Workflow)
        from hermeneus.src.ccl_ast import OpType
        assert OpType.DEEPEN in ast.operators

    def test_star_vs_plus_distinct(self):
        """/noe*/dia と /noe+/dia は異なる AST。"""
        parser = CCLParser()
        ast_star = parser.parse("/noe*/dia")
        ast_plus = parser.parse("/noe+_/dia")
        assert isinstance(ast_star, Fusion)
        assert not isinstance(ast_plus, Fusion)

    # ─── dispatch AST ラベル検証 ─────────────────────────────

    def test_sequence_label_in_tree(self):
        """AST ツリーに Sequence の '順次実行' ラベルが含まれる。"""
        from hermeneus.src.dispatch import dispatch
        result = dispatch("/dia_/fit")
        assert "順次実行" in result["tree"]

    def test_condense_label_in_tree(self):
        """AST ツリーに Condense の '軽量' ラベルが含まれる。"""
        from hermeneus.src.dispatch import dispatch
        result = dispatch("/dia-")
        assert "軽量" in result["tree"]

    def test_deepen_label_in_tree(self):
        """AST ツリーに Deepen の '深化' ラベルが含まれる。"""
        from hermeneus.src.dispatch import dispatch
        result = dispatch("/noe+")
        assert "深化" in result["tree"]


class TestLinterConfusionDetection:
    """ccl_linter が混同ペアを検出することを検証。"""

    def test_linter_detects_underscore_confusable(self):
        from mekhane.ccl.ccl_linter import lint
        warnings = lint("/dia_/fit")
        confusable = [w for w in warnings if "シーケンス" in w.message]
        assert len(confusable) >= 1

    def test_linter_detects_tilde_confusable(self):
        from mekhane.ccl.ccl_linter import lint
        warnings = lint("/noe~/dia")
        confusable = [w for w in warnings if "振動" in w.message]
        assert len(confusable) >= 1

    def test_linter_no_false_positive_on_condense(self):
        from mekhane.ccl.ccl_linter import lint
        warnings = lint("/dia-")
        confusable = [w for w in warnings if "シーケンス" in w.message or "振動" in w.message]
        assert len(confusable) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
