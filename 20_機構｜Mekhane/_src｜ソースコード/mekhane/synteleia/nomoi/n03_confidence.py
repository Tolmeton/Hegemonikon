# PROOF: [L1/定理] <- mekhane/synteleia/nomoi/n03_confidence.py N-03 確信度を明示せよ
# PURPOSE: 不可能断定・SFBT チェック対象を検出 (S-I × Ekphrasis)
"""
N-03 Confidence Agent — 確信度を明示せよ

「できない」「不可能」等の断定を検出し、SFBT 5項目チェックを促す。
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
from ..pattern_loader import load_patterns, parse_keyword_list, parse_pattern_list, record_hit

_PATTERNS_YAML = Path(__file__).parent / "patterns.yaml"

_FALLBACK_IMPOSSIBLE = [
    (r"(?:できない|不可能|困難)(?:です|である|だ|。)", "N03-001",
     "不可能断定 — SFBT 5項目チェックを実施せよ"),
    (r"(?:ない(?:です|でしょう))$", "N03-002",
     "否定断定 — 代替案を検討したか"),
    (r"\b(?:impossible|cannot|unable)\b", "N03-003",
     "不可能断定(英語) — SFBT チェック"),
]

_FALLBACK_OVERCONFIDENCE_KW = ["唯一の方法", "以外にない", "他に手段はない"]


# PURPOSE: N-03 確信度明示エージェント
class N03ConfidenceAgent(AuditAgent):
    """N-03 確信度を明示せよ — 不可能断定検出"""

    name = "N03ConfidenceAgent"
    description = "N-3 確信度明示: 不可能断定と過剰確信を検出"
    stoicheion = "S-I"
    phase = "P3"  # Ekphrasis
    nomos = "N-03"

    def __init__(self):
        loaded = load_patterns(_PATTERNS_YAML, "n03_confidence")
        self.impossible_patterns = parse_pattern_list(
            loaded.get("impossible_patterns"), _FALLBACK_IMPOSSIBLE
        )
        self.overconfidence_keywords = parse_keyword_list(
            loaded.get("overconfidence_keywords"), _FALLBACK_OVERCONFIDENCE_KW
        )

    def audit(self, target: AuditTarget) -> AgentResult:
        """不可能断定と過剰確信を監査"""
        issues: List[AuditIssue] = []

        if target.target_type == AuditTargetType.CODE:
            return AgentResult(agent_name=self.name, passed=True, issues=[], confidence=1.0)

        content = target.content

        # 不可能断定の検出
        for pattern, code, message in self.impossible_patterns:
            if code is None:
                continue
            for match in re.finditer(pattern, content, re.MULTILINE):
                record_hit(code)
                issues.append(
                    AuditIssue(
                        agent=self.name,
                        code=code,
                        severity=AuditSeverity.HIGH,
                        message=message,
                        location=f"position {match.start()}",
                        suggestion="SFBT: 1.できるとしたら？ 2.代替5つ 3.過去の類似解決 4.やっていない≠できない 5.最小の一歩は？",
                    )
                )

        # 過剰確信キーワードの検出
        for kw in self.overconfidence_keywords:
            if kw in content:
                record_hit("N03-010")
                issues.append(
                    AuditIssue(
                        agent=self.name,
                        code="N03-010",
                        severity=AuditSeverity.MEDIUM,
                        message=f"過剰確信キーワード「{kw}」— 代替案を検討せよ",
                        suggestion="代替案を最低1つ提示し、不採用理由を明示",
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
        return target_type != AuditTargetType.CODE
