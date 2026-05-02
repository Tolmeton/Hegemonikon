# PROOF: [L1/定理] <- mekhane/synteleia/nomoi/n10_taint.py N-10 SOURCE/TAINTを区別せよ
# PURPOSE: 確信と推測の混合を検出 (S-III × Dianoia)
"""
N-10 Taint Agent — SOURCE/TAINTを区別せよ

新規パターン — 精度混同を検出。
精度最適化 — 処理中の各信号に正確な precision weight を割り当てる。
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

_FALLBACK_PRECISION_CONFUSION = [
    (r"(?:確か|確実).*(?:思う|思います|かも)", "N10-001",
     "確信と推測の混合 — 精度ラベルを付与せよ"),
    (r"(?:知っている|分かっている).*(?:はず|かも|思う)", "N10-002",
     "知識と推測の混合"),
]


# PURPOSE: N-10 TAINT 区別エージェント
class N10TaintAgent(AuditAgent):
    """N-10 SOURCE/TAINTを区別せよ — 精度混同検出"""

    name = "N10TaintAgent"
    description = "N-10 TAINT区別: 確信と推測の精度混同を検出"
    stoicheion = "S-III"
    phase = "P2"  # Dianoia
    nomos = "N-10"

    def __init__(self):
        loaded = load_patterns(_PATTERNS_YAML, "n10_taint")
        self.precision_confusion_patterns = parse_pattern_list(
            loaded.get("precision_confusion_patterns"), _FALLBACK_PRECISION_CONFUSION
        )

    def audit(self, target: AuditTarget) -> AgentResult:
        """精度混同を監査"""
        issues: List[AuditIssue] = []

        if target.target_type == AuditTargetType.CODE:
            return AgentResult(agent_name=self.name, passed=True, issues=[], confidence=1.0)

        content = target.content

        for pattern, code, message in self.precision_confusion_patterns:
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
                        suggestion="[SOURCE: xxx] / [TAINT: xxx] ラベルで情報の出自を明示",
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
            confidence=0.60,
        )

    def supports(self, target_type: AuditTargetType) -> bool:
        return target_type != AuditTargetType.CODE
