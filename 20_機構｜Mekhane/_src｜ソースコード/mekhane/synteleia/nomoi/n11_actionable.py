# PROOF: [L1/定理] <- mekhane/synteleia/nomoi/n11_actionable.py N-11 行動可能な形で出せ
# PURPOSE: 構造的品質と用語定義の完全性を検出 (S-III × Ekphrasis)
"""
N-11 Actionable Agent — 読み手が行動できる形で出せ

旧 SchemaAgent (構造問題) + OusiaAgent O-010 (未定義用語) +
CompletenessAgent 必須要素チェックを統合。
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Set

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

_FALLBACK_STRUCTURE = [
    (r"(^#{1,6}\s+\S[^\n]*\n){2,}", "N11-001", "連続する見出し — 見出し間に内容を追加"),
    (r"^\n{4,}", "N11-002", "過剰な空行"),
    (r"^#{1}\s+.*\n(?:(?!^#{1,2}\s).*\n)*^#{3}\s+", "N11-003",
     "見出し階層の飛躍 (H1→H3)"),
]

# 必須要素の定義
_DEFAULT_REQUIRED: Dict[str, List[str]] = {
    "ccl_output": ["結論", "根拠"],
    "plan": ["目的", "ステップ", "検証"],
    "proof": ["PURPOSE", "PROOF"],
}


# PURPOSE: N-11 行動可能性エージェント
class N11ActionableAgent(AuditAgent):
    """N-11 行動可能な形で出せ — 構造品質・用語定義・必須要素"""

    name = "N11ActionableAgent"
    description = "N-11 行動可能性: 構造の品質と必須要素の完全性を検出"
    stoicheion = "S-III"
    phase = "P3"  # Ekphrasis
    nomos = "N-11"

    def __init__(self):
        loaded = load_patterns(_PATTERNS_YAML, "n11_actionable")
        self.structure_patterns = parse_pattern_list(
            loaded.get("structure_patterns"), _FALLBACK_STRUCTURE
        )
        # 必須要素定義
        raw_required = loaded.get("completeness_required")
        if isinstance(raw_required, dict):
            self.required_elements = raw_required
        else:
            self.required_elements = _DEFAULT_REQUIRED

    def audit(self, target: AuditTarget) -> AgentResult:
        """行動可能性を監査"""
        issues: List[AuditIssue] = []
        content = target.content

        # 構造パターンの検出
        for pattern, code, message in self.structure_patterns:
            if code is None:
                continue
            for match in re.finditer(pattern, content, re.MULTILINE):
                record_hit(code)
                issues.append(
                    AuditIssue(
                        agent=self.name,
                        code=code,
                        severity=AuditSeverity.LOW,
                        message=message,
                        location=f"position {match.start()}",
                        suggestion="文書構造を改善してください",
                    )
                )

        # 未定義用語の検出 (PLAN/THOUGHT のみ)
        if target.target_type in (AuditTargetType.PLAN, AuditTargetType.THOUGHT):
            issues.extend(self._check_undefined_terms(content))

        # 必須要素の完全性チェック
        issues.extend(self._check_required_elements(target))

        # 関数長の超過チェック (コード対象)
        if target.target_type == AuditTargetType.CODE:
            issues.extend(self._check_function_length(content))

        passed = not any(
            i.severity in (AuditSeverity.CRITICAL, AuditSeverity.HIGH)
            for i in issues
        )
        return AgentResult(
            agent_name=self.name,
            passed=passed,
            issues=issues,
            confidence=0.80,
        )

    def _check_undefined_terms(self, content: str) -> List[AuditIssue]:
        """未定義の専門用語を検出 (旧 O-010)"""
        issues = []
        technical_terms: Set[str] = set(
            re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b", content)
        )
        for term in technical_terms:
            definition_pattern = rf"\b{re.escape(term)}\s+(?:とは|is|means|=)"
            if not re.search(definition_pattern, content, re.IGNORECASE):
                record_hit("N11-010")
                issues.append(
                    AuditIssue(
                        agent=self.name,
                        code="N11-010",
                        severity=AuditSeverity.INFO,
                        message=f"用語 '{term}' の定義が見つかりません",
                        suggestion=f"'{term} とは...' の形式で定義を追加",
                    )
                )
        return issues

    def _check_required_elements(self, target: AuditTarget) -> List[AuditIssue]:
        """必須要素の完全性チェック (旧 CompletenessAgent 必須要素)"""
        issues = []
        target_type_key = target.target_type.value
        required = self.required_elements.get(target_type_key, [])
        if not required:
            return issues

        content_lower = target.content.lower()
        for element in required:
            if element.lower() not in content_lower:
                record_hit("N11-020")
                issues.append(
                    AuditIssue(
                        agent=self.name,
                        code="N11-020",
                        severity=AuditSeverity.MEDIUM,
                        message=f"必須要素 '{element}' が見つかりません",
                        suggestion=f"'{element}' セクションを追加してください",
                    )
                )
        return issues

    def _check_function_length(self, content: str, max_lines: int = 50) -> List[AuditIssue]:
        """関数の行数超過を検出 (旧 S-030)"""
        issues = []
        lines = content.split("\n")
        func_start = None
        func_name = ""
        indent_level = 0

        for i, line in enumerate(lines):
            # Python 関数定義の検出
            match = re.match(r"^(\s*)def\s+(\w+)", line)
            if match:
                # 前の関数を閉じる
                if func_start is not None:
                    length = i - func_start
                    if length > max_lines:
                        record_hit("N11-030")
                        issues.append(
                            AuditIssue(
                                agent=self.name,
                                code="N11-030",
                                severity=AuditSeverity.LOW,
                                message=f"関数 '{func_name}' が {length} 行 (> {max_lines})",
                                location=f"line {func_start + 1}",
                                suggestion="関数を分割して可読性を向上",
                            )
                        )
                func_start = i
                func_name = match.group(2)
                indent_level = len(match.group(1))

        # 最後の関数
        if func_start is not None:
            length = len(lines) - func_start
            if length > max_lines:
                record_hit("N11-030")
                issues.append(
                    AuditIssue(
                        agent=self.name,
                        code="N11-030",
                        severity=AuditSeverity.LOW,
                        message=f"関数 '{func_name}' が {length} 行 (> {max_lines})",
                        location=f"line {func_start + 1}",
                        suggestion="関数を分割して可読性を向上",
                    )
                )

        return issues

    def supports(self, target_type: AuditTargetType) -> bool:
        return True
