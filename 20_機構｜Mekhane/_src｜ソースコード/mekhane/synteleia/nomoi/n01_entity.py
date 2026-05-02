# PROOF: [L1/定理] <- mekhane/synteleia/nomoi/n01_entity.py N-01 実体を読め
# PURPOSE: 曖昧な参照を検出し、実体の明確化を促す (S-I × Aisthēsis)
"""
N-01 Entity Agent — 実体を読め

「これ」「それ」「あれ」等の曖昧な指示参照を検出。
N-1: prior(記憶)の precision を下げ、感覚入力(実体)の precision を上げる。
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

# 旧コード対応: O-001〜O-006 → N01-001〜N01-006
_FALLBACK_VAGUE = [
    (r"\bこれ\b(?!は)", "N01-001", "「これ」の指示対象が不明確"),
    (r"\bそれ\b(?!は)", "N01-002", "「それ」の指示対象が不明確"),
    (r"\bあれ\b", "N01-003", "「あれ」の指示対象が不明確"),
    (r"\b(?:something|anything|nothing)\b", "N01-004", "不定代名詞の使用"),
    (r"\betc\.?\b", "N01-005", "etc. は実体を曖昧にする"),
    (r"\.\.\.(?!\s*\])", "N01-006", "省略記号は実体を隠す"),
]


# PURPOSE: N-01 実体を読め — 曖昧参照検出エージェント
class N01EntityAgent(AuditAgent):
    """N-01 実体を読め — 曖昧参照検出"""

    name = "N01EntityAgent"
    description = "N-1 実体を読め: 曖昧な指示参照を検出"
    stoicheion = "S-I"  # Tapeinophrosyne
    phase = "P1"  # Aisthēsis
    nomos = "N-01"

    def __init__(self):
        loaded = load_patterns(_PATTERNS_YAML, "n01_entity")
        self.vague_patterns = parse_pattern_list(
            loaded.get("vague_patterns"), _FALLBACK_VAGUE
        )

    def audit(self, target: AuditTarget) -> AgentResult:
        """曖昧な参照を監査"""
        issues: List[AuditIssue] = []
        content = target.content

        for pattern, code, message in self.vague_patterns:
            if code is None:
                continue
            for match in re.finditer(pattern, content, re.IGNORECASE):
                record_hit(code)
                issues.append(
                    AuditIssue(
                        agent=self.name,
                        code=code,
                        severity=AuditSeverity.LOW,
                        message=message,
                        location=f"position {match.start()}",
                        suggestion="具体的な名称に置き換えてください",
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
            confidence=0.75,
        )

    def supports(self, target_type: AuditTargetType) -> bool:
        return True
