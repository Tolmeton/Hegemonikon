# PROOF: [L1/定理] <- mekhane/synteleia/nomoi/n08_tooluse.py N-08 道具を使い自動化せよ
# PURPOSE: 先延ばし表現を検出 (S-II × Praxis)
"""
N-08 ToolUse Agent — 道具を使い自動化せよ

旧 KairosAgent の先延ばしパターンを移植。
θ8.4: 先延ばし禁止。今やれることは今やる。
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

_FALLBACK_PROCRASTINATION = [
    (r"(?:後で|あとで|later|そのうち|いつか)", "N08-001", "先延ばしの兆候 — 今やれることは今やれ"),
    (r"(?:今度|次回|next\s+time|someday)", "N08-002", "先延ばしキーワード"),
    (r"そのうち(?:やる|する|対応|修正)", "N08-003", "不確定な対応時期"),
    (r"(?:暇|余裕)(?:が|の)(?:ある|でき)(?:たら|れば)", "N08-004", "条件付き先延ばし"),
    (r"(?:今は|currently)\s*(?:スキップ|skip|飛ばす)", "N08-005",
     "明示的スキップ — 理由を記録せよ"),
    (r"(?:将来的に|eventually|in the future)", "N08-006", "将来への丸投げ"),
]


# PURPOSE: N-08 道具使用エージェント
class N08ToolUseAgent(AuditAgent):
    """N-08 道具を使い自動化せよ — 先延ばし検出"""

    name = "N08ToolUseAgent"
    description = "N-8 道具使用: 先延ばし表現を検出"
    stoicheion = "S-II"
    phase = "P4"  # Praxis
    nomos = "N-08"

    def __init__(self):
        loaded = load_patterns(_PATTERNS_YAML, "n08_tooluse")
        self.procrastination_patterns = parse_pattern_list(
            loaded.get("procrastination_patterns"), _FALLBACK_PROCRASTINATION
        )

    def audit(self, target: AuditTarget) -> AgentResult:
        """先延ばしの兆候を監査"""
        issues: List[AuditIssue] = []
        content = target.content

        for pattern, code, message in self.procrastination_patterns:
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
                        suggestion="θ8.4: 今やれることは今やる。先延ばしは禁止",
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
            confidence=0.70,
        )

    def supports(self, target_type: AuditTargetType) -> bool:
        return True
