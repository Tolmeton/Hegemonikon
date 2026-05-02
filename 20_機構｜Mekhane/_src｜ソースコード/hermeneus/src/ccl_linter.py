# PROOF: [L2/インフラ] <- hermeneus/src/ccl_linter.py CCL 静的整合性検証
# PURPOSE: CCL 式の静的解析（パース前の構文チェック）を行う Linter。
#   ccl-plan.md L82 で「層1: CCLLinter が式の静的整合性を検証する」と定義されている。
"""
CCLLinter — CCL 式の静的整合性検証

パース前に以下をチェック:
1. 括弧の対応 ((), {}, [])
2. 未定義 WF の検出
3. 空ブロックの検出
4. 構文パターンの検証

Usage:
    linter = CCLLinter()
    issues = linter.lint("/noe+_V:{/dia+}")
    if issues:
        for issue in issues:
            print(f"[{issue.severity}] {issue.message}")
"""

import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Set, Any

from hermeneus.src.parser import CCLParser

logger = logging.getLogger(__name__)


class Severity(Enum):
    """リント問題の深刻度"""
    ERROR = "error"      # パース不能な構文エラー
    WARNING = "warning"  # パースはできるが疑わしい構文
    INFO = "info"        # スタイル改善の提案


@dataclass
class LintIssue:
    """リント問題"""
    severity: Severity
    message: str
    position: int = -1  # 問題のある文字位置 (-1 = 不明)
    rule: str = ""      # ルール ID (例: "bracket-mismatch")

    def __str__(self) -> str:
        pos = f" (pos {self.position})" if self.position >= 0 else ""
        return f"[{self.severity.value}] {self.message}{pos}"


# PURPOSE: CCL 式の静的整合性を検証する Linter
class CCLLinter:
    """CCL 式の静的整合性を検証する。

    パーサー (CCLParser) に渡す前の段階で、明らかな構文エラーを
    検出し、ユーザーに分かりやすいメッセージを返す。

    FEP 同型: 予測誤差の事前検出 — 実行時にクラッシュする前に、
    構文レベルの不整合を「驚き」として検出する。
    """

    # CCLParser.WORKFLOWS を参照 (ソースの一元管理)
    KNOWN_WORKFLOWS: Set[str] = CCLParser.WORKFLOWS

    # 有効なタグブロック接頭辞
    VALID_TAGS = {"V", "C", "R", "M", "E"}

    # 有効な制御構文接頭辞
    CONTROL_PREFIXES = {"F:", "I:", "EI:", "W:", "L:", "lim["}

    # 括弧ペア
    BRACKET_PAIRS = {"(": ")", "{": "}", "[": "]"}
    CLOSE_TO_OPEN = {v: k for k, v in BRACKET_PAIRS.items()}

    def lint(self, ccl: str) -> List[LintIssue]:
        """CCL 式をリントし、問題のリストを返す。

        Args:
            ccl: CCL 式の文字列

        Returns:
            LintIssue のリスト。空なら問題なし。
        """
        issues: List[LintIssue] = []

        if not ccl or not ccl.strip():
            issues.append(LintIssue(
                severity=Severity.ERROR,
                message="空の CCL 式",
                rule="empty-expression",
            ))
            return issues

        ccl = ccl.strip()

        # Rule 1: 括弧の対応チェック
        issues.extend(self._check_brackets(ccl))

        # Rule 2: 未定義 WF の検出
        issues.extend(self._check_undefined_workflows(ccl))

        # Rule 3: 空ブロックの検出
        issues.extend(self._check_empty_blocks(ccl))

        # Rule 4: 構文パターンの検証
        issues.extend(self._check_syntax_patterns(ccl))

        # Rule 5: 射影構文の静的検証 (AST を使用)
        issues.extend(self._check_projections(ccl))

        # Rule 6: パーサーのドライラン
        issues.extend(self._try_parse(ccl))

        return issues

    def _check_projections(self, ccl: str) -> List[LintIssue]:
        """AST をトラバースし、射影構文 (.field) の静的検証を行う。"""
        issues: List[LintIssue] = []
        try:
            parser = CCLParser()
            ast = parser.parse(ccl)
            issues.extend(self._validate_ast_projections(ast))
        except Exception:
            # パースエラーは _try_parse で報告するためここでは無視
            pass
        return issues

    def _validate_ast_projections(self, node: Any) -> List[LintIssue]:
        """AST ノードをトラバースして射影構文を検証。"""
        from hermeneus.src.ccl_ast import Workflow
        issues: List[LintIssue] = []

        # wm-L: 知覚型
        WM_L_FIELDS = {"goal", "gaps", "next"}
        # wm-M: 判断型
        WM_M_FIELDS = {"goal", "constraints", "decision", "next"}
        # wm-H: 行動型
        WM_H_FIELDS = {"goal", "current_state", "constraints", "next_step"}

        VERB_PROJECTIONS = {
            "the": WM_L_FIELDS | {"perceived", "suspended"},
            "ant": WM_L_FIELDS | {"baseline", "deltas"},
            "ere": WM_L_FIELDS | {"scope", "discoveries", "absences", "surprises"},
            "agn": WM_L_FIELDS | {"pattern", "matches", "mismatches", "coverage"},
            "sap": WM_L_FIELDS | {"facts", "priors", "gaps"},
            "ski": WM_L_FIELDS | {"map", "hotspots", "gaps"},
            "prs": WM_L_FIELDS | {"details", "deviations"},
            "per": WM_L_FIELDS | {"structure", "statistics"},
            "apo": WM_L_FIELDS | {"strengths", "balance"},
            "exe": WM_L_FIELDS | {"issues", "balance"},
            "his": WM_L_FIELDS | {"records", "deviations"},
            "prg": WM_L_FIELDS | {"signals", "suspended", "separation"},
            
            "noe": WM_M_FIELDS | {"insight", "anomaly", "limit"},
            "bou": WM_M_FIELDS | {"desire", "feasibility", "will"},
            "epo": WM_M_FIELDS | {"current_state"},
            "beb": WM_M_FIELDS | {"belief", "condition"},
            
            "tek": WM_H_FIELDS | {"artifacts"},
            "kop": {"direction", "terrain", "anchor", "discovery", "next"},
        }

        # Peras 全族 (/t /m /k /d /o /c /ax) -> wm-M
        for p in ["t", "m", "k", "d", "o", "c", "ax", "Ia", "Ib", "Sa", "Sb", "Aa", "Ab"]:
            VERB_PROJECTIONS[p] = set(WM_M_FIELDS)
            
        # Hub固有の1フィールドは省略（ここでは厳密なチェックはせず、未知は警告しない）
        
        for v in ["kat", "sag", "pai", "dok", "akr", "arh", "dio", "par"]:
            if v in ["arh", "dio", "par"]:
                VERB_PROJECTIONS[v] = set(WM_H_FIELDS)
            else:
                VERB_PROJECTIONS[v] = set(WM_M_FIELDS)

        def _walk(n: Any):
            if n is None:
                return
            if isinstance(n, Workflow):
                if n.projection:
                    fields = VERB_PROJECTIONS.get(n.id)
                    # 定義済みのスキルの場合のみチェック (未知のスキルやHubフィールドは許容)
                    if fields is not None and n.projection not in fields:
                        issues.append(LintIssue(
                            severity=Severity.ERROR,
                            message=f"未定義の射影 '{n.projection}' が '/{n.id}' に指定されています。有効な射影: {', '.join(sorted(fields))}",
                            rule="undefined-projection"
                        ))
            elif hasattr(n, "__dataclass_fields__"):
                for field_name in n.__dataclass_fields__:
                    val = getattr(n, field_name)
                    if isinstance(val, list):
                        for item in val:
                            _walk(item)
                    else:
                        _walk(val)

        _walk(node)
        return issues

    def _check_brackets(self, ccl: str) -> List[LintIssue]:
        """括弧の対応をチェック。"""
        issues: List[LintIssue] = []
        stack: list[tuple[str, int]] = []  # (open_bracket, position)

        for i, ch in enumerate(ccl):
            if ch in self.BRACKET_PAIRS:
                stack.append((ch, i))
            elif ch in self.CLOSE_TO_OPEN:
                expected_open = self.CLOSE_TO_OPEN[ch]
                if not stack:
                    issues.append(LintIssue(
                        severity=Severity.ERROR,
                        message=f"閉じ括弧 '{ch}' に対応する開き括弧がない",
                        position=i,
                        rule="bracket-mismatch",
                    ))
                elif stack[-1][0] != expected_open:
                    open_ch, open_pos = stack[-1]
                    issues.append(LintIssue(
                        severity=Severity.ERROR,
                        message=(
                            f"括弧の不一致: '{open_ch}' (pos {open_pos}) に対して "
                            f"'{ch}' (pos {i}) が閉じている。"
                            f"期待: '{self.BRACKET_PAIRS[open_ch]}'"
                        ),
                        position=i,
                        rule="bracket-mismatch",
                    ))
                    stack.pop()
                else:
                    stack.pop()

        for open_ch, pos in stack:
            issues.append(LintIssue(
                severity=Severity.ERROR,
                message=f"開き括弧 '{open_ch}' が閉じられていない",
                position=pos,
                rule="bracket-unclosed",
            ))

        return issues

    def _check_undefined_workflows(self, ccl: str) -> List[LintIssue]:
        """未定義の WF ID を検出。"""
        issues: List[LintIssue] = []

        # /wf_id パターンを全て抽出
        for match in re.finditer(r'/([a-z][a-z0-9]*)', ccl):
            wf_id = match.group(1)
            if wf_id not in self.KNOWN_WORKFLOWS:
                issues.append(LintIssue(
                    severity=Severity.WARNING,
                    message=f"未定義の WF: '/{wf_id}'",
                    position=match.start(),
                    rule="undefined-workflow",
                ))

        return issues

    def _check_empty_blocks(self, ccl: str) -> List[LintIssue]:
        """空ブロック ({}, V:{}, C:{} 等) を検出。"""
        issues: List[LintIssue] = []

        # {} の空チェック
        for match in re.finditer(r'\{\s*\}', ccl):
            issues.append(LintIssue(
                severity=Severity.WARNING,
                message="空のブロック '{}'",
                position=match.start(),
                rule="empty-block",
            ))

        return issues

    def _check_syntax_patterns(self, ccl: str) -> List[LintIssue]:
        """一般的な構文ミスを検出。"""
        issues: List[LintIssue] = []

        # 連続する演算子 (例: __  ~~  **) — OpenEnd を除く
        for match in re.finditer(r'(__|\~\~|\*\*)', ccl):
            issues.append(LintIssue(
                severity=Severity.WARNING,
                message=f"連続する演算子: '{match.group()}'",
                position=match.start(),
                rule="double-operator",
            ))

        # タグブロックの不正な形式 (例: V:noe — V:{} の {} が欠落)
        for match in re.finditer(r'([VCRME]):(?!\{)([a-z])', ccl):
            tag = match.group(1)
            if tag in self.VALID_TAGS:
                issues.append(LintIssue(
                    severity=Severity.ERROR,
                    message=f"タグブロック '{tag}:' の後に '{{' が必要",
                    position=match.start(),
                    rule="tag-missing-brace",
                ))

        return issues

    def _try_parse(self, ccl: str) -> List[LintIssue]:
        """パーサーのドライランで実際のパースエラーを検出。"""
        issues: List[LintIssue] = []

        try:
            parser = CCLParser()
            parser.parse(ccl)
            # パーサーの内部エラーもチェック
            for err in parser.errors:
                issues.append(LintIssue(
                    severity=Severity.WARNING,
                    message=f"パーサー警告: {err}",
                    rule="parser-warning",
                ))
        except (ValueError, Exception) as e:  # noqa: BLE001
            issues.append(LintIssue(
                severity=Severity.ERROR,
                message=f"パースエラー: {e}",
                rule="parse-error",
            ))

        return issues


def lint_ccl(ccl: str) -> List[LintIssue]:
    """CCL 式をリントする (便利関数)。"""
    return CCLLinter().lint(ccl)
