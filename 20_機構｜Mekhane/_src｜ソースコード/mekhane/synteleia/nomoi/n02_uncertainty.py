# PROOF: [L1/定理] <- mekhane/synteleia/nomoi/n02_uncertainty.py N-02 不確実性を追跡せよ
# PURPOSE: 確信度ラベルなしの断定を検出 (S-I × Dianoia)
"""
N-02 Uncertainty Agent — 不確実性を追跡せよ

[確信]/[推定]/[仮説] ラベルのない断定表現を検出。
新規パターン — 旧体系に該当エージェントなし。
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

_FALLBACK_MISSING_LABEL = [
    (r"(?:正しい|最適|適切|当然|もちろん|間違いない)(?:です|である|だ)", "N02-001",
     "確信度ラベル[確信]/[推定]/[仮説]なしの断定"),
    (r"確実に|絶対に|必ず(?!し)", "N02-002",
     "過剰確信の表現 — ラベルと根拠を付与せよ"),
]


# PURPOSE: N-02 不確実性追跡エージェント
class N02UncertaintyAgent(AuditAgent):
    """N-02 不確実性を追跡せよ — ラベルなし断定検出"""

    name = "N02UncertaintyAgent"
    description = "N-2 不確実性追跡: 確信度ラベルなしの断定を検出"
    stoicheion = "S-I"
    phase = "P2"  # Dianoia
    nomos = "N-02"

    def __init__(self):
        loaded = load_patterns(_PATTERNS_YAML, "n02_uncertainty")
        self.missing_label_patterns = parse_pattern_list(
            loaded.get("missing_label_patterns"), _FALLBACK_MISSING_LABEL
        )

    def audit(self, target: AuditTarget) -> AgentResult:
        """確信度ラベルの欠如を監査"""
        issues: List[AuditIssue] = []

        # コード対象では発動しない（自然言語テキストのみ）
        if target.target_type == AuditTargetType.CODE:
            return AgentResult(agent_name=self.name, passed=True, issues=[], confidence=1.0)

        content = target.content

        for pattern, code, message in self.missing_label_patterns:
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
                        suggestion="[確信]/[推定]/[仮説] ラベルと SOURCE/TAINT 根拠を付与",
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
            confidence=0.65,  # 文脈依存性が高い
        )

    def supports(self, target_type: AuditTargetType) -> bool:
        # コード以外の全タイプをサポート
        return target_type != AuditTargetType.CODE
