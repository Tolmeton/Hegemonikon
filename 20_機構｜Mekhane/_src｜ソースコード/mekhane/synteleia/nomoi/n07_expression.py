# PROOF: [L1/定理] <- mekhane/synteleia/nomoi/n07_expression.py N-07 主観を述べ次を提案せよ
# PURPOSE: 動機不明確な表現を検出 (S-II × Ekphrasis)
"""
N-07 Expression Agent — 主観を述べ次を提案せよ

旧 HormeAgent のパターンを移植。
能動推論の出力 — 内部状態を外部に表出し、次の行動を提案する。
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

_FALLBACK_VAGUE_MOTIVATION = [
    (r"とりあえず|一応|念のため", "N07-001", "動機が不明確 — なぜ必要か述べよ"),
    (r"なんとなく|何となく|somehow", "N07-002", "根拠なき行動 — 理由を明示せよ"),
    (r"たぶん.*(?:いい|よい|OK|良い)(?:と思う|かな|でしょう)", "N07-003",
     "推測的判断 — 根拠を付与せよ"),
    (r"(?:just|only)\s+(?:in case|to be safe)", "N07-004",
     "防御的動機 — 明確なリスク根拠を述べよ"),
    (r"might\s+(?:need|want|be\s+(?:good|nice|useful))", "N07-005",
     "漠然とした必要性 — 具体的根拠を付与せよ"),
]

_FALLBACK_PURPOSE_KW = [
    "目的", "理由", "なぜ", "ゴール", "purpose", "goal", "motivation", "because", "rationale",
]


# PURPOSE: N-07 主観表出エージェント
class N07ExpressionAgent(AuditAgent):
    """N-07 主観を述べ次を提案せよ — 動機不明確検出"""

    name = "N07ExpressionAgent"
    description = "N-7 主観表出: 動機不明確な表現を検出"
    stoicheion = "S-II"
    phase = "P3"  # Ekphrasis
    nomos = "N-07"

    def __init__(self):
        loaded = load_patterns(_PATTERNS_YAML, "n07_expression")
        self.vague_motivation_patterns = parse_pattern_list(
            loaded.get("vague_motivation_patterns"), _FALLBACK_VAGUE_MOTIVATION
        )
        self.purpose_keywords = parse_keyword_list(
            loaded.get("purpose_keywords"), _FALLBACK_PURPOSE_KW
        )

    def audit(self, target: AuditTarget) -> AgentResult:
        """動機の明確さを監査"""
        issues: List[AuditIssue] = []
        content = target.content

        # 動機不明確パターンの検出
        for pattern, code, message in self.vague_motivation_patterns:
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
                        suggestion="明確な根拠を付与してください",
                    )
                )

        # 計画文書での目的キーワード欠如チェック
        if target.target_type == AuditTargetType.PLAN:
            has_purpose = any(kw in content for kw in self.purpose_keywords)
            if not has_purpose:
                record_hit("N07-010")
                issues.append(
                    AuditIssue(
                        agent=self.name,
                        code="N07-010",
                        severity=AuditSeverity.MEDIUM,
                        message="計画文書に目的キーワードが見つかりません",
                        suggestion="「目的:」「なぜ:」等のセクションを追加",
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
