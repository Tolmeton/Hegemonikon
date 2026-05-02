"""F7: dispatch.py の警告統合テスト。

spec_injector / failure_db の警告が plan_template に正しく注入されることを検証する。
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


class TestDispatchWarnings:
    """dispatch の Step 7 警告統合テスト。"""

    def test_expand_operator_triggers_warning(self):
        """'!' 演算子を含む CCL 式で 演算子注意 ブロックが表示される。"""
        from hermeneus.src.dispatch import dispatch

        result = dispatch("/dia!")

        plan = result.get("plan_template", "")
        assert "演算子注意" in plan, "! 含有時に【⚠️ 演算子注意】が表示されるべき"
        assert "階乗" in plan or "全派生同時実行" in plan, "! の正しい意味が表示されるべき"

    def test_deepen_operator_no_warning(self):
        """'+' のみの CCL 式で演算子注意ブロックが表示されない。"""
        from hermeneus.src.dispatch import dispatch

        result = dispatch("/noe+")

        plan = result.get("plan_template", "")
        assert "演算子注意" not in plan, "+ のみでは警告不要"

    def test_expand_operator_triggers_quiz(self):
        """'!' 演算子を含む CCL 式で理解確認クイズが挿入される。"""
        from hermeneus.src.dispatch import dispatch

        result = dispatch("/dia!")

        plan = result.get("plan_template", "")
        assert "理解確認" in plan, "危険演算子含有時に【理解確認】が表示されるべき"

    def test_deepen_operator_no_quiz(self):
        """'+' のみの CCL 式で理解確認クイズが表示されない。"""
        from hermeneus.src.dispatch import dispatch

        result = dispatch("/noe+")

        plan = result.get("plan_template", "")
        assert "理解確認" not in plan, "+ のみではクイズ不要"

    def test_multiple_dangerous_ops(self):
        """複数の危険演算子で複数の警告/クイズが生成される。"""
        from hermeneus.src.dispatch import dispatch

        result = dispatch("/noe!*^/dia")

        plan = result.get("plan_template", "")
        assert "演算子注意" in plan

    def test_spec_injector_definitions_complete(self):
        """spec_injector が基本演算子11個を定義している。"""
        from mekhane.ccl.spec_injector import OPERATOR_DEFINITIONS

        required = {"+", "-", "^", "/", "?", "\\", "*", "~", "_", "!", "'"}
        actual = set(OPERATOR_DEFINITIONS.keys())
        missing = required - actual
        assert not missing, f"OPERATOR_DEFINITIONS に不足: {missing}"


class TestFailureDBIntegration:
    """failure_db の dispatch 連携テスト。"""

    def test_failure_db_warnings_for_expand(self):
        """failure_db が '!' に対して critical 警告を返す。"""
        from mekhane.ccl.learning.failure_db import get_failure_db

        db = get_failure_db()
        warnings = db.get_warnings("/dia!")

        bang_warnings = [w for w in warnings if w.operator == "!"]
        assert len(bang_warnings) >= 1, "! に対する警告がない"
        assert bang_warnings[0].severity == "critical"

    def test_failure_db_no_warnings_for_safe(self):
        """安全な式に対して failure_db が不要な警告を返さない。"""
        from mekhane.ccl.learning.failure_db import get_failure_db

        db = get_failure_db()
        warnings = db.get_warnings("/noe+")

        assert len(warnings) == 0, f"+ のみで警告が出力された: {warnings}"

    def test_failure_db_backslash_warning(self):
        r"""failure_db が '\' に対して warning を返す。"""
        from mekhane.ccl.learning.failure_db import get_failure_db

        db = get_failure_db()
        warnings = db.get_warnings("/noe\\")

        bs_warnings = [w for w in warnings if w.operator == "\\"]
        assert len(bs_warnings) >= 1, r"\ に対する警告がない"
        assert bs_warnings[0].severity == "warning"


class TestCompoundOperators:
    """F8/F10: 複合演算子の parse_operators テスト。"""

    def test_parse_star_caret(self):
        """'*^' が単一の複合演算子として検出される。"""
        from mekhane.ccl.spec_injector import SpecInjector

        injector = SpecInjector()
        ops = injector.parse_operators("/noe*^/dia")
        assert "*^" in ops, "*^ が検出されない"
        # * と ^ が個別に検出されてはいけない (貪欲マッチ)
        assert "*" not in ops, "* が単独で検出された (貪欲マッチ失敗)"
        assert "^" not in ops, "^ が単独で検出された (貪欲マッチ失敗)"

    def test_parse_tilde_star(self):
        """'~*' が単一の複合演算子として検出される。"""
        from mekhane.ccl.spec_injector import SpecInjector

        injector = SpecInjector()
        ops = injector.parse_operators("/noe~*/dia")
        assert "~*" in ops, "~* が検出されない"

    def test_parse_pipeline(self):
        """'>>' が単一の複合演算子として検出される。"""
        from mekhane.ccl.spec_injector import SpecInjector

        injector = SpecInjector()
        ops = injector.parse_operators("/noe >> /dia")
        assert ">>" in ops, ">> が検出されない"

    def test_parse_mixed_operators(self):
        """複合+単一の混在式で正しく分離される。"""
        from mekhane.ccl.spec_injector import SpecInjector

        injector = SpecInjector()
        ops = injector.parse_operators("/noe!*^/dia+")
        assert "*^" in ops, "*^ が検出されない"
        assert "!" in ops, "! が検出されない"
        assert "+" in ops, "+ が検出されない"

    def test_compound_definitions_exist(self):
        """COMPOUND_OPERATORS に 3 種の複合演算子が定義されている。"""
        from mekhane.ccl.spec_injector import COMPOUND_OPERATORS

        required = {"*^", "~*", ">>"}
        actual = set(COMPOUND_OPERATORS.keys())
        missing = required - actual
        assert not missing, f"COMPOUND_OPERATORS に不足: {missing}"

    def test_all_operators_unified(self):
        """ALL_OPERATORS が COMPOUND + SINGLE の合計を含む。"""
        from mekhane.ccl.spec_injector import ALL_OPERATORS, OPERATOR_DEFINITIONS, COMPOUND_OPERATORS

        assert len(ALL_OPERATORS) == len(OPERATOR_DEFINITIONS) + len(COMPOUND_OPERATORS)


class TestGetWarnedOperators:
    """F9: get_warned_operators のテスト。"""

    def test_bang_warned(self):
        """'!' 含有式で '!' が warned set に含まれる。"""
        from mekhane.ccl.spec_injector import get_warned_operators

        warned = get_warned_operators("/dia!")
        assert "!" in warned

    def test_star_caret_warned(self):
        """'*^' 含有式で '*^' が warned set に含まれる。"""
        from mekhane.ccl.spec_injector import get_warned_operators

        warned = get_warned_operators("/noe*^/dia")
        assert "*^" in warned

    def test_backslash_warned(self):
        r"""'\' 含有式で '\' が warned set に含まれる。"""
        from mekhane.ccl.spec_injector import get_warned_operators

        warned = get_warned_operators(r"/noe\dia")
        assert "\\" in warned

    def test_safe_expr_no_warned(self):
        """安全な式で warned set が空。"""
        from mekhane.ccl.spec_injector import get_warned_operators

        warned = get_warned_operators("/noe+")
        assert len(warned) == 0


class TestBackslashOperator:
    r"""F12: '\' 演算子の統合テスト。"""

    def test_backslash_triggers_warning(self):
        r"""'\' 含有式で演算子注意ブロックが表示される。"""
        from hermeneus.src.dispatch import dispatch

        result = dispatch(r"/noe\dia")
        plan = result.get("plan_template", "")
        assert "演算子注意" in plan, r"\ 含有時に警告が表示されるべき"

    def test_backslash_triggers_quiz(self):
        r"""'\' 含有式で理解確認クイズが挿入される。"""
        from hermeneus.src.dispatch import dispatch

        result = dispatch(r"/noe\dia")
        plan = result.get("plan_template", "")
        assert "理解確認" in plan, r"\ は危険演算子なのでクイズが表示されるべき"


class TestSequenceVsCondenseWarning:
    """_ vs - 混同防止の警告テスト。"""

    def test_underscore_triggers_confusable_warning(self):
        """/dia_/fit で _ の警告が表示される。"""
        from mekhane.ccl.spec_injector import get_warnings_for_expr

        warnings = get_warnings_for_expr("/dia_/fit")
        underscore_warnings = [w for w in warnings if "シーケンス" in w]
        assert len(underscore_warnings) >= 1, "_ があるのに混同防止警告がない"
        assert "`/dia_`" in underscore_warnings[0], "検出パターンが表示されるべき"

    def test_condense_no_confusable_warning(self):
        """/dia- で _ の混同防止警告が表示されない。"""
        from mekhane.ccl.spec_injector import get_warnings_for_expr

        warnings = get_warnings_for_expr("/dia-")
        underscore_warnings = [w for w in warnings if "シーケンス" in w]
        assert len(underscore_warnings) == 0, "- のみでは混同防止警告は不要"

    def test_warned_operators_includes_underscore(self):
        """/dia_/fit で warned set に _ が含まれる。"""
        from mekhane.ccl.spec_injector import get_warned_operators

        warned = get_warned_operators("/dia_/fit")
        assert "_" in warned, "_ がない式以外では warned に含まれるべき"

    def test_warned_operators_excludes_underscore_when_absent(self):
        """/dia- で warned set に _ が含まれない。"""
        from mekhane.ccl.spec_injector import get_warned_operators

        warned = get_warned_operators("/dia-")
        assert "_" not in warned, "_ がない式では warned に含まれるべきでない"

    def test_dispatch_includes_confusable_warning(self):
        """dispatch 経由で /dia_/fit の plan_template に警告が含まれる。"""
        from hermeneus.src.dispatch import dispatch

        result = dispatch("/dia_/fit")
        plan = result.get("plan_template", "")
        assert "シーケンス" in plan, "dispatch の plan_template に _ 混同防止警告が含まれるべき"

    def test_dispatch_ast_shows_sequence_label(self):
        """dispatch の AST ツリーに '順次実行' ラベルが表示される。"""
        from hermeneus.src.dispatch import dispatch

        result = dispatch("/dia_/fit")
        tree = result.get("tree", "")
        assert "順次実行" in tree, "AST ツリーに '順次実行' ラベルが表示されるべき"

    def test_dispatch_ast_shows_condense_label(self):
        """dispatch の AST ツリーで - に '軽量' ラベルが表示される。"""
        from hermeneus.src.dispatch import dispatch

        result = dispatch("/dia-")
        tree = result.get("tree", "")
        assert "軽量" in tree, "AST ツリーに '軽量' ラベルが表示されるべき"

    def test_tilde_triggers_confusable_warning(self):
        """/noe~/dia で ~ の混同防止警告が表示される。"""
        from mekhane.ccl.spec_injector import get_warnings_for_expr

        warnings = get_warnings_for_expr("/noe~/dia")
        tilde_warnings = [w for w in warnings if "振動" in w]
        assert len(tilde_warnings) >= 1, "~ があるのに混同防止警告がない"

    def test_condense_no_tilde_warning(self):
        """/noe- で ~ の混同防止警告が表示されない。"""
        from mekhane.ccl.spec_injector import get_warnings_for_expr

        warnings = get_warnings_for_expr("/noe-")
        tilde_warnings = [w for w in warnings if "振動" in w]
        assert len(tilde_warnings) == 0, "- のみでは ~ 混同防止警告は不要"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
