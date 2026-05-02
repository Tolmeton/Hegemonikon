# PROOF: [L2/テスト] <- hermeneus/tests/test_ccl_linter.py CCLLinter の単体テスト
"""CCLLinter の単体テスト。

5ルール:
1. bracket-mismatch / bracket-unclosed: 括弧の対応
2. undefined-workflow: 未定義 WF
3. empty-block: 空ブロック
4. syntax patterns: double-operator, tag-missing-brace
5. parse-error: パーサードライラン
"""

import pytest
from hermeneus.src.ccl_linter import CCLLinter, LintIssue, Severity, lint_ccl


@pytest.fixture
def linter():
    return CCLLinter()


class TestBracketChecks:
    """括弧の対応チェック"""

    def test_balanced(self, linter):
        issues = linter.lint("/noe+_V:{/dia+}")
        bracket_issues = [i for i in issues if "bracket" in i.rule]
        assert len(bracket_issues) == 0

    def test_unclosed_paren(self, linter):
        issues = linter.lint("(/noe+_/dia+")
        assert any(i.rule == "bracket-unclosed" for i in issues)

    def test_unclosed_brace(self, linter):
        issues = linter.lint("V:{/noe+")
        assert any(i.rule == "bracket-unclosed" for i in issues)

    def test_mismatch(self, linter):
        issues = linter.lint("(/noe+}")
        assert any(i.rule == "bracket-mismatch" for i in issues)

    def test_nested_balanced(self, linter):
        issues = linter.lint("C:{F:[×3]{/dia+}_V:{/noe+}}")
        bracket_issues = [i for i in issues if "bracket" in i.rule]
        assert len(bracket_issues) == 0


class TestUndefinedWorkflows:
    """未定義 WF の検出"""

    def test_known_workflow(self, linter):
        issues = linter.lint("/noe+")
        assert not any(i.rule == "undefined-workflow" for i in issues)

    def test_unknown_workflow(self, linter):
        issues = linter.lint("/xyzzy+")
        assert any(i.rule == "undefined-workflow" for i in issues)

    def test_multiple_known(self, linter):
        issues = linter.lint("/bou+_/noe_/tek")
        assert not any(i.rule == "undefined-workflow" for i in issues)


class TestEmptyBlocks:
    """空ブロックの検出"""

    def test_empty_brace(self, linter):
        issues = linter.lint("V:{}")
        assert any(i.rule == "empty-block" for i in issues)

    def test_non_empty_brace(self, linter):
        issues = linter.lint("V:{/dia+}")
        assert not any(i.rule == "empty-block" for i in issues)


class TestSyntaxPatterns:
    """構文パターンの検証"""

    def test_double_underscore(self, linter):
        issues = linter.lint("/noe+__/dia+")
        assert any(i.rule == "double-operator" for i in issues)

    def test_tag_missing_brace(self, linter):
        issues = linter.lint("V:noe")
        assert any(i.rule == "tag-missing-brace" for i in issues)


class TestParserDryRun:
    """パーサードライランのテスト"""

    def test_valid_ccl(self, linter):
        issues = linter.lint("/noe+_V:{/dia+}_/pis_/dox-")
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) == 0

    def test_ccl_plan_default(self, linter):
        """ccl-plan v5.0 のデフォルト CCL をリント"""
        ccl = "C:{/bou+~(/prm*/tek)_/m+~(/d*/k)_V:{/dia+}}_/pis_/dox-"
        issues = linter.lint(ccl)
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert len(errors) == 0

    def test_ccl_plan_plus(self, linter):
        """ccl-plan v6.0+ の CCL をリント"""
        ccl = "C:{F:[×3]{(/bou+*%/prm)~*(/m+*(/d*/k))}_V:{/dia+}_I:[ε>θ]{/ske_/zet+}}_/pis_/dox-"
        issues = linter.lint(ccl)
        # ε,θ は WF ではないのでパースエラーが出る可能性あり — 確認
        # 構文自体は正しいが I: の条件式がパーサーに渡されるか


class TestConvenienceFunction:
    """lint_ccl 便利関数"""

    def test_lint_ccl(self):
        issues = lint_ccl("/noe+")
        assert isinstance(issues, list)

    def test_empty_input(self):
        issues = lint_ccl("")
        assert any(i.rule == "empty-expression" for i in issues)
