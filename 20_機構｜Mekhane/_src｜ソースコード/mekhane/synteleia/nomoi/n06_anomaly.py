# PROOF: [L1/定理] <- mekhane/synteleia/nomoi/n06_anomaly.py N-06 違和感を検知せよ
# PURPOSE: 論理的矛盾・デッドコード・自己否定を検出 (S-II × Dianoia)
"""
N-06 Anomaly Agent — 違和感を検知せよ

旧 LogicAgent の全パターンを完全移植。
予測誤差検出 — 矛盾(誤差)を検出しモデルを更新する。
"""

import re
from pathlib import Path
from typing import List, Set

from ..base import (
    AgentResult,
    AuditAgent,
    AuditIssue,
    AuditSeverity,
    AuditTarget,
    AuditTargetType,
)
from ..pattern_loader import (
    load_patterns,
    parse_pair_list,
    parse_pattern_list,
    record_hit,
)

_PATTERNS_YAML = Path(__file__).parent / "patterns.yaml"

_FALLBACK_LOGIC = [
    (r"(?:必須|required|mandatory).*(?:任意|optional|省略可)", "N06-001",
     "「必須」と「任意」の矛盾"),
    (r"(?:常に|always).*(?:決して|never)", "N06-002",
     "「常に」と「決して」の矛盾"),
    (r"(?:全て|all).*(?:一部|some|部分的)", "N06-003",
     "「全て」と「一部」の矛盾"),
    (r"(?:同期|synchronous).*(?:非同期|asynchronous)", "N06-004",
     "同期/非同期の混在"),
]

_FALLBACK_CONTRADICTION_PAIRS = [
    ("必須", "任意"), ("常に", "決して"), ("全て", "一部"),
    ("同期", "非同期"), ("public", "private"), ("immutable", "mutable"),
    ("必ず", "場合によって"), ("always", "never"), ("required", "optional"),
]

_FALLBACK_DEAD_CODE = [
    (r"\bif\s+True\s*:", "N06-010", "常に真の条件 — デッドコード"),
    (r"\bif\s+False\s*:", "N06-011", "常に偽の条件 — 到達不能コード"),
    (r"\bwhile\s+True\s*:(?!.*break)", "N06-012", "break なしの無限ループ"),
]

_FALLBACK_SELF_NEGATION = [
    (r"(?:^|\n)[^\n]*(?:する|します|implement|add)\b[^\n]*\n[^\n]*(?:しない|しません|not\s+implement|remove)\b[^\n]*(?:同じ|same|上記)",
     "N06-020", "直後に否定される記述"),
    (r"(?:TODO|FIXME).*(?:完了|done|finished)", "N06-021", "TODO が完了と矛盾"),
]


# PURPOSE: N-06 違和感検知エージェント
class N06AnomalyAgent(AuditAgent):
    """N-06 違和感を検知せよ — 論理矛盾・デッドコード検出"""

    name = "N06AnomalyAgent"
    description = "N-6 違和感検知: 論理矛盾・デッドコード・自己否定を検出"
    stoicheion = "S-II"
    phase = "P2"  # Dianoia
    nomos = "N-06"

    def __init__(self):
        loaded = load_patterns(_PATTERNS_YAML, "n06_anomaly")
        self.logic_patterns = parse_pattern_list(
            loaded.get("logic_patterns"), _FALLBACK_LOGIC
        )
        self.contradiction_pairs = parse_pair_list(
            loaded.get("contradiction_pairs"), _FALLBACK_CONTRADICTION_PAIRS
        )
        self.dead_code_patterns = parse_pattern_list(
            loaded.get("dead_code_patterns"), _FALLBACK_DEAD_CODE
        )
        self.self_negation_patterns = parse_pattern_list(
            loaded.get("self_negation_patterns"), _FALLBACK_SELF_NEGATION
        )

    def audit(self, target: AuditTarget) -> AgentResult:
        """論理的整合性を監査"""
        issues: List[AuditIssue] = []
        content = target.content

        # 正規表現パターンによる矛盾検出
        for pattern, code, message in self.logic_patterns:
            if code is None:
                continue
            for match in re.finditer(pattern, content, re.IGNORECASE | re.DOTALL):
                record_hit(code)
                issues.append(
                    AuditIssue(
                        agent=self.name,
                        code=code,
                        severity=AuditSeverity.HIGH,
                        message=message,
                        location=f"position {match.start()}",
                        suggestion="矛盾する記述のどちらかを修正",
                    )
                )

        # 対立概念ペアの共存チェック
        issues.extend(self._check_contradiction_pairs(content))

        # デッドコード (コード対象のみ、stripped_content 使用)
        if target.target_type == AuditTargetType.CODE:
            for pattern, code, message in self.dead_code_patterns:
                if code is None:
                    continue
                for match in re.finditer(pattern, target.stripped_content, re.MULTILINE):
                    record_hit(code)
                    issues.append(
                        AuditIssue(
                            agent=self.name,
                            code=code,
                            severity=AuditSeverity.MEDIUM,
                            message=message,
                            location=f"position {match.start()}",
                        )
                    )

        # 自己否定検出
        for pattern, code, message in self.self_negation_patterns:
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
            confidence=0.85,
        )

    def _check_contradiction_pairs(self, content: str) -> List[AuditIssue]:
        """対立概念ペアの共存を検出"""
        issues = []
        content_lower = content.lower()
        for term_a, term_b in self.contradiction_pairs:
            if term_a.lower() in content_lower and term_b.lower() in content_lower:
                record_hit("N06-010")
                issues.append(
                    AuditIssue(
                        agent=self.name,
                        code="N06-010",
                        severity=AuditSeverity.MEDIUM,
                        message=f"対立概念「{term_a}」と「{term_b}」が同一文書内に共存",
                        suggestion="意図的な対比でなければ統一せよ",
                    )
                )
        return issues

    def supports(self, target_type: AuditTargetType) -> bool:
        return True
