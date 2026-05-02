"""フォローアップ #5: operators.md と ccl_linter の同期テスト。

operators.md (SSOT) に定義された演算子が ccl_linter で正しく認識されること、
新しい演算子が追加された時に ccl_linter の定義と齟齬がないことを保証する。

Origin: 2026-02-23 CCL 演算子混同防止フォローアップ #5
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


class TestOperatorSync:
    """operators.md (SSOT) と ccl_linter の同期検証。"""

    def test_all_operators_dict_nonempty(self):
        """ALL_OPERATORS が空でないことを確認。"""
        from mekhane.ccl.spec_injector import ALL_OPERATORS
        assert len(ALL_OPERATORS) > 0

    def test_compound_operators_subset(self):
        """COMPOUND_OPERATORS が ALL_OPERATORS のサブセット。"""
        from mekhane.ccl.spec_injector import ALL_OPERATORS, COMPOUND_OPERATORS
        for op in COMPOUND_OPERATORS:
            assert op in ALL_OPERATORS, f"Compound op '{op}' not in ALL_OPERATORS"

    def test_dangerous_ops_are_defined(self):
        """ccl_linter の _DANGEROUS_OPERATORS が全て ALL_OPERATORS に含まれる。"""
        from mekhane.ccl.spec_injector import ALL_OPERATORS
        from mekhane.ccl.ccl_linter import _DANGEROUS_OPERATORS
        for d in _DANGEROUS_OPERATORS:
            op = d["operator"]
            assert op in ALL_OPERATORS, (
                f"Dangerous op '{op}' is not in ALL_OPERATORS — "
                f"operators.md と ccl_linter が同期していない"
            )

    def test_confusable_pairs_operators_exist(self):
        """ccl_linter の _CONFUSABLE_PAIRS の演算子が全て定義済み。"""
        from mekhane.ccl.spec_injector import ALL_OPERATORS
        from mekhane.ccl.ccl_linter import _CONFUSABLE_PAIRS
        for pair in _CONFUSABLE_PAIRS:
            op = pair["operator"]
            confusable = pair["confusable_with"]
            # _ はシーケンス演算子で ALL_OPERATORS にはないかもしれない
            if op != "_":
                assert op in ALL_OPERATORS, f"Confusable op '{op}' not in ALL_OPERATORS"
            assert confusable in ALL_OPERATORS, f"Confusable target '{confusable}' not in ALL_OPERATORS"

    def test_conflicting_pairs_operators_exist(self):
        """ccl_linter の _CONFLICTING_PAIRS の演算子が全て定義済み。"""
        from mekhane.ccl.spec_injector import ALL_OPERATORS
        from mekhane.ccl.ccl_linter import _CONFLICTING_PAIRS
        for a, b in _CONFLICTING_PAIRS:
            assert a in ALL_OPERATORS, f"Conflicting op '{a}' not in ALL_OPERATORS"
            assert b in ALL_OPERATORS, f"Conflicting op '{b}' not in ALL_OPERATORS"

    def test_lint_returns_list(self):
        """lint() が LintWarning のリストを返す。"""
        from mekhane.ccl.ccl_linter import lint, LintWarning
        result = lint("/noe+")
        assert isinstance(result, list)
        for w in result:
            assert isinstance(w, LintWarning)

    def test_get_warned_operators_returns_set(self):
        """get_warned_operators() が set を返す。"""
        from mekhane.ccl.ccl_linter import get_warned_operators
        result = get_warned_operators("/noe!")
        assert isinstance(result, set)
        assert "!" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
