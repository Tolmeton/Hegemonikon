# PROOF: [L1/定理] <- mekhane/synteleia/nomoi/n04_irreversible.py N-04 不可逆前に確認せよ
# PURPOSE: スコープ逸脱とセキュリティ脆弱性を検出 (S-I × Praxis)
"""
N-04 Irreversible Agent — 不可逆前に確認せよ

旧 PerigrapheAgent (スコープ逸脱) + OperatorAgent SEC系 (セキュリティ) を統合。
不可逆操作の事前検出。
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
from ..pattern_loader import (
    load_patterns,
    parse_pattern_list,
    parse_pattern_list_with_severity,
    record_hit,
)

_PATTERNS_YAML = Path(__file__).parent / "patterns.yaml"

_FALLBACK_SCOPE = [
    (r"ついでに|ところで|while we.re at it", "N04-001", "スコープ逸脱の兆候"),
    (r"ちなみに|余談(ですが|だけど)", "N04-002", "本題からの逸脱"),
    (r"せっかくだから|ここまで来た(ら|ので)", "N04-003", "サンクコスト的拡張"),
    (r"もう一つ|あと一点", "N04-004", "追加要求の連鎖"),
]

_FALLBACK_SECURITY = [
    (r"\beval\s*\(", "N04-010", "eval() は任意コード実行の危険", "critical"),
    (r"\bexec\s*\(", "N04-011", "exec() は任意コード実行の危険", "critical"),
    (r"\bos\.system\s*\(", "N04-012", "os.system() はシェルインジェクションの危険", "critical"),
    (r"\bsubprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True", "N04-013",
     "shell=True はインジェクションリスク", "high"),
    (r"\bpickle\.loads?\s*\(", "N04-014", "pickle は任意コード実行の危険", "high"),
    (r"\byaml\.(?:load|unsafe_load)\s*\(", "N04-015",
     "yaml.load() は yaml.safe_load() を使用せよ", "high"),
    (r'(?:password|secret|api_key)\s*=\s*["\x27][^"\x27]+["\x27]', "N04-016",
     "機密情報のハードコード", "critical"),
    (r"\b__import__\s*\(", "N04-017", "__import__() は動的インポートのリスク", "high"),
]


# PURPOSE: N-04 不可逆前確認エージェント
class N04IrreversibleAgent(AuditAgent):
    """N-04 不可逆前に確認せよ — スコープ逸脱 + セキュリティ"""

    name = "N04IrreversibleAgent"
    description = "N-4 不可逆前確認: スコープ逸脱とセキュリティ脆弱性を検出"
    stoicheion = "S-I"
    phase = "P4"  # Praxis
    nomos = "N-04"

    def __init__(self):
        loaded = load_patterns(_PATTERNS_YAML, "n04_irreversible")
        self.scope_patterns = parse_pattern_list(
            loaded.get("scope_patterns"), _FALLBACK_SCOPE
        )
        self.security_patterns = parse_pattern_list_with_severity(
            loaded.get("security_patterns"), _FALLBACK_SECURITY
        )

    def audit(self, target: AuditTarget) -> AgentResult:
        """不可逆操作の兆候を監査"""
        issues: List[AuditIssue] = []
        content = target.content

        # スコープ逸脱 (テキスト対象)
        if target.target_type != AuditTargetType.CODE:
            issues.extend(self._check_scope(content))

        # セキュリティ脆弱性 (コード対象、stripped_content を使用)
        if target.target_type == AuditTargetType.CODE:
            issues.extend(self._check_security(target.stripped_content))

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

    def _check_scope(self, content: str) -> List[AuditIssue]:
        """スコープ逸脱を検出"""
        issues = []
        for pattern, code, message in self.scope_patterns:
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
                        suggestion="スコープ確認: 本来の目的に関係あるか？",
                    )
                )
        return issues

    def _check_security(self, content: str) -> List[AuditIssue]:
        """セキュリティ脆弱性を検出"""
        issues = []
        for pattern, code, message, severity in self.security_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                record_hit(code)
                sev = getattr(AuditSeverity, severity.upper(), AuditSeverity.HIGH)
                issues.append(
                    AuditIssue(
                        agent=self.name,
                        code=code,
                        severity=sev,
                        message=message,
                        location=f"position {match.start()}",
                        suggestion="安全な代替手段を使用してください",
                    )
                )
        return issues

    def supports(self, target_type: AuditTargetType) -> bool:
        return True
