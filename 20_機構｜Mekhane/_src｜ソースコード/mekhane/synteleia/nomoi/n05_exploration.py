# PROOF: [L1/定理] <- mekhane/synteleia/nomoi/n05_exploration.py N-05 能動的に情報を探せ
# PURPOSE: 時期尚早な最適化を検出 (S-II × Aisthēsis)
"""
N-05 Exploration Agent — 能動的に情報を探せ

旧 KairosAgent の早すぎる最適化パターンを配置。
FEP F3: 今は探索すべきか実行すべきか？
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

_FALLBACK_PREMATURE = [
    (r"(?:最適化|optimize).*(?:後で|later|あとで)", "N05-001", "時期尚早な最適化の兆候"),
    (r"premature\s+optimization", "N05-002", "早すぎる最適化"),
    (r"パフォーマンス.*(?:心配|気になる)(?!.*ベンチマーク)", "N05-003",
     "ベンチマークなしのパフォーマンス懸念"),
]


# PURPOSE: N-05 能動探索エージェント
class N05ExplorationAgent(AuditAgent):
    """N-05 能動的に情報を探せ — 探索/活用判断の検出"""

    name = "N05ExplorationAgent"
    description = "N-5 能動探索: 時期尚早な最適化と探索不足を検出"
    stoicheion = "S-II"
    phase = "P1"  # Aisthēsis
    nomos = "N-05"

    def __init__(self):
        loaded = load_patterns(_PATTERNS_YAML, "n05_exploration")
        self.premature_patterns = parse_pattern_list(
            loaded.get("premature_patterns"), _FALLBACK_PREMATURE
        )

    def audit(self, target: AuditTarget) -> AgentResult:
        """探索/活用判断を監査"""
        issues: List[AuditIssue] = []
        content = target.content

        for pattern, code, message in self.premature_patterns:
            if code is None:
                continue
            for match in re.finditer(pattern, content, re.IGNORECASE):
                record_hit(code)
                issues.append(
                    AuditIssue(
                        agent=self.name,
                        code=code,
                        severity=AuditSeverity.MEDIUM,
                        message=message,
                        location=f"position {match.start()}",
                        suggestion="FEP F3: 情報が十分か確認してから実行に移れ",
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
            confidence=0.65,
        )

    def supports(self, target_type: AuditTargetType) -> bool:
        return True
