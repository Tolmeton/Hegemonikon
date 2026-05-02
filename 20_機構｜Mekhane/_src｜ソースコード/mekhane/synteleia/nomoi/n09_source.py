# PROOF: [L1/定理] <- mekhane/synteleia/nomoi/n09_source.py N-09 原典に当たれ
# PURPOSE: TAINT による断言を検出 (S-III × Aisthēsis)
"""
N-09 Source Agent — 原典に当たれ

新規パターン — TAINT 情報での断言を検出。
精度最適化 — 情報源の precision を正確に評価し、高 precision の入力を優先する。
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

_FALLBACK_TAINT_ASSERTION = [
    (r"(?:〜のはず|はずです|だったはず)", "N09-001", "TAINT による断言 — SOURCE で確認せよ"),
    (r"(?:前に確認した|以前見た|記憶では)", "N09-002", "記憶ベースの断言 — SOURCE を確保"),
    (r"(?:たぶん|おそらく|probably).*(?:バージョン|version|v\d)", "N09-003",
     "バージョン情報の推測 — 原典で確認"),
]


# PURPOSE: N-09 原典参照エージェント
class N09SourceAgent(AuditAgent):
    """N-09 原典に当たれ — TAINT 断言検出"""

    name = "N09SourceAgent"
    description = "N-9 原典参照: TAINT 情報での断言を検出"
    stoicheion = "S-III"
    phase = "P1"  # Aisthēsis
    nomos = "N-09"

    def __init__(self):
        loaded = load_patterns(_PATTERNS_YAML, "n09_source")
        self.taint_assertion_patterns = parse_pattern_list(
            loaded.get("taint_assertion_patterns"), _FALLBACK_TAINT_ASSERTION
        )

    def audit(self, target: AuditTarget) -> AgentResult:
        """TAINT 断言を監査"""
        issues: List[AuditIssue] = []

        if target.target_type == AuditTargetType.CODE:
            return AgentResult(agent_name=self.name, passed=True, issues=[], confidence=1.0)

        content = target.content

        for pattern, code, message in self.taint_assertion_patterns:
            if code is None:
                continue
            for match in re.finditer(pattern, content):
                record_hit(code)
                issues.append(
                    AuditIssue(
                        agent=self.name,
                        code=code,
                        severity=AuditSeverity.MEDIUM,
                        message=message,
                        location=f"position {match.start()}",
                        suggestion="view_file / search_web で SOURCE を確保せよ",
                    )
                )

        passed = not any(
            i.severity in (AuditSeverity.CRITICAL, AuditSeverity.HIGH)
            for i in issues
        )
        return AgentResult(
            agent_name=self.name,
            passed=passed,
            issues=issues,
            confidence=0.60,  # テキストパターンの文脈依存性が高い
        )

    def supports(self, target_type: AuditTargetType) -> bool:
        return target_type != AuditTargetType.CODE
