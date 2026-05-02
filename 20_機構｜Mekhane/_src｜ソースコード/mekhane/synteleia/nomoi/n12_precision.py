# PROOF: [L1/定理] <- mekhane/synteleia/nomoi/n12_precision.py N-12 正確に実行せよ
# PURPOSE: CCL 誤用・コードスタイル・未完了マーカー・空ブロックを検出 (S-III × Praxis)
"""
N-12 Precision Agent — 正確に実行せよ

旧 OperatorAgent (CCL誤用 + コードスタイル) +
CompletenessAgent (未完了マーカー + 空ブロック) を統合。
行動の precision error を最小化する S-III の最終段。
"""

import re
from pathlib import Path
from typing import List

from ..base import (
    AgentResult,
    AuditAgent,
    AuditIssue,
    AuditSeverity,
    AuditTarget,
    AuditTargetType,
)
from ..pattern_loader import load_patterns, parse_pattern_list, record_hit

_PATTERNS_YAML = Path(__file__).parent / "patterns.yaml"

_FALLBACK_CCL_OP = [
    (r"\/{2,}", "N12-001", "連続スラッシュ — CCL演算子の誤用"),
    (r"\+{2,}", "N12-002", "連続プラス — CCL修飾子の誤用"),
    (r"\*{3,}", "N12-003", "過剰なアスタリスク"),
    (r"~{2,}", "N12-004", "連続チルダ — CCL演算子の誤用"),
    (r">>{2,}", "N12-005", "過剰なパイプ"),
]

_FALLBACK_CODE_STYLE = [
    (r"==\s*True\b", "N12-010", "冗長な比較 — bool値は直接使用"),
    (r"==\s*False\b", "N12-011", "冗長な比較 — not を使用"),
    (r"!=\s*None\b", "N12-012", "!= None は is not None を使用"),
    (r"==\s*None\b", "N12-013", "== None は is None を使用"),
]

_FALLBACK_INCOMPLETE = [
    (r"\bTODO\b", "N12-020", "未完了マーカー TODO"),
    (r"\bFIXME\b", "N12-021", "未修正マーカー FIXME"),
    (r"\bXXX\b", "N12-022", "問題マーカー XXX"),
    (r"\bHACK\b", "N12-023", "一時的回避策 HACK"),
    (r"\bBUG\b", "N12-024", "既知バグマーカー BUG"),
    (r"\bWARNING\b(?!.*import|.*log)", "N12-025", "警告マーカー WARNING"),
    (r"\bTEMP\b(?!.*orary|.*late)", "N12-026", "一時的コードマーカー TEMP"),
    (r"\bDEPRECATED\b", "N12-027", "非推奨マーカー DEPRECATED"),
]

_FALLBACK_EMPTY_BLOCK = [
    (r"(?:def|class)\s+\w+[^:]*:\s*\n\s*pass\s*$", "N12-030",
     "空の関数/クラス定義 (pass)"),
    (r"(?:def|class)\s+\w+[^:]*:\s*\n\s*\.\.\.\s*$", "N12-031",
     "空の関数/クラス定義 (...)"),
    (r"raise\s+NotImplementedError", "N12-032", "未実装メソッド"),
    (r"(?:except|catch)[^:]*:\s*\n\s*pass\s*$", "N12-033", "空の例外ハンドラ"),
    (r"\{\s*\}", "N12-034", "空のブロック"),
]


# PURPOSE: N-12 正確実行エージェント
class N12PrecisionAgent(AuditAgent):
    """N-12 正確に実行せよ — CCL誤用・コードスタイル・未完了・空ブロック"""

    name = "N12PrecisionAgent"
    description = "N-12 正確実行: 行動の precision error を最小化"
    stoicheion = "S-III"
    phase = "P4"  # Praxis
    nomos = "N-12"

    def __init__(self):
        loaded = load_patterns(_PATTERNS_YAML, "n12_precision")
        self.ccl_op_patterns = parse_pattern_list(
            loaded.get("ccl_operator_patterns"), _FALLBACK_CCL_OP
        )
        self.code_style_patterns = parse_pattern_list(
            loaded.get("code_style_patterns"), _FALLBACK_CODE_STYLE
        )
        self.incomplete_patterns = parse_pattern_list(
            loaded.get("incomplete_patterns"), _FALLBACK_INCOMPLETE
        )
        self.empty_block_patterns = parse_pattern_list(
            loaded.get("empty_block_patterns"), _FALLBACK_EMPTY_BLOCK
        )

    def audit(self, target: AuditTarget) -> AgentResult:
        """実行精度を監査"""
        issues: List[AuditIssue] = []

        if target.target_type == AuditTargetType.CODE:
            # コード対象: stripped_content を使用
            stripped = target.stripped_content
            issues.extend(self._check_patterns(
                stripped, self.code_style_patterns, AuditSeverity.LOW
            ))
            issues.extend(self._check_patterns(
                stripped, self.incomplete_patterns, AuditSeverity.LOW
            ))
            issues.extend(self._check_patterns(
                stripped, self.empty_block_patterns, AuditSeverity.MEDIUM,
                flags=re.MULTILINE
            ))
        else:
            # テキスト対象: CCL 演算子誤用のみ
            issues.extend(self._check_patterns(
                target.content, self.ccl_op_patterns, AuditSeverity.LOW
            ))
            # テキスト内の未完了マーカーも検出
            issues.extend(self._check_patterns(
                target.content, self.incomplete_patterns, AuditSeverity.INFO
            ))

        passed = not any(
            i.severity in (AuditSeverity.CRITICAL, AuditSeverity.HIGH)
            for i in issues
        )
        return AgentResult(
            agent_name=self.name,
            passed=passed,
            issues=issues,
            confidence=0.90,  # パターンマッチベースなので高精度
        )

    def _check_patterns(
        self,
        content: str,
        patterns: list,
        default_severity: AuditSeverity,
        flags: int = 0,
    ) -> List[AuditIssue]:
        """汎用パターンチェック"""
        issues = []
        for pattern, code, message in patterns:
            if code is None:
                continue
            for match in re.finditer(pattern, content, flags):
                record_hit(code)
                issues.append(
                    AuditIssue(
                        agent=self.name,
                        code=code,
                        severity=default_severity,
                        message=message,
                        location=f"position {match.start()}",
                    )
                )
        return issues

    def supports(self, target_type: AuditTargetType) -> bool:
        return True
