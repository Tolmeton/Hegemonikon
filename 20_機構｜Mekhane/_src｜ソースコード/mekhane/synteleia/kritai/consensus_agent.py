# PROOF: [L3/品質] <- mekhane/synteleia/kritai/consensus_agent.py L3 マルチモデルコンセンサス監査
# PURPOSE: 複数 LLM の監査結果を比較し、一致率で確信度を計算する
"""
ConsensusAgent — Multi-Model Consensus Auditing

複数の LLM バックエンドに同一の監査プロンプトを投げ、
結果の一致率から確信度を計算する。

- 全モデルが同意 → 確信度 1.0
- 過半数が同意 → 確信度 0.6-0.8
- 不一致 → 確信度 0.3

Usage:
    agent = ConsensusAgent(backends=[backend1, backend2, backend3])
    result = agent.audit(target)
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ..base import (
    AgentResult,
    AuditAgent,
    AuditIssue,
    AuditSeverity,
    AuditTarget,
)

logger = logging.getLogger(__name__)


# PURPOSE: セマンティック監査の LLM バックエンドプロトコル
class LLMBackendProtocol:
    """LLMBackend のプロトコル (型チェック用)。"""

    # PURPOSE: [L2-auto] query の関数定義
    def query(self, prompt: str, context: str) -> str:
        raise NotImplementedError

    # PURPOSE: [L2-auto] is_available の関数定義
    def is_available(self) -> bool:
        raise NotImplementedError


# PURPOSE: コンセンサス監査エージェント
class ConsensusAgent(AuditAgent):
    """複数 LLM の監査結果を比較し、コンセンサスで確信度を算出。

    L3 層: CRITICAL/HIGH 検出時に自動発動される想定。
    """

    name = "ConsensusAgent"
    description = "L3 Multi-Model Consensus Auditing"

    # PURPOSE: 監査プロンプト (Týpos 経由でロード)
    _AUDIT_PROMPT_CACHE: str | None = None

    @classmethod
    def _get_audit_prompt(cls) -> str:
        """Týpos .prompt ファイルからコンセンサス監査プロンプトをロードする。"""
        if cls._AUDIT_PROMPT_CACHE is not None:
            return cls._AUDIT_PROMPT_CACHE
        try:
            from pathlib import Path
            from mekhane.ergasterion.typos.typos import parse_file
            prompt_path = Path(__file__).resolve().parent.parent.parent / "ergasterion" / "typos" / "prompts" / "synteleia_consensus.prompt"
            pf = parse_file(str(prompt_path))
            cls._AUDIT_PROMPT_CACHE = pf.compile(format="markdown")
            return cls._AUDIT_PROMPT_CACHE
        except Exception:  # noqa: BLE001
            cls._AUDIT_PROMPT_CACHE = cls._FALLBACK_AUDIT_PROMPT
            return cls._AUDIT_PROMPT_CACHE

    _FALLBACK_AUDIT_PROMPT = """あなたはコード監査の専門家です。以下のコードを監査し、問題点をJSON形式で報告してください。

## 出力形式
```json
{
  "issues": [
    {"code": "...", "message": "...", "severity": "critical|high|medium|low"}
  ],
  "summary": "...",
  "confidence": 0.0-1.0
}
```

## 監査対象"""

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(self, backends: Optional[List[Any]] = None):
        self._backends = backends or []

    # PURPOSE: [L2-auto] audit の関数定義
    def audit(self, target: AuditTarget) -> AgentResult:
        """複数バックエンドに監査を依頼し、コンセンサスを計算。"""
        if not self._backends:
            return AgentResult(
                agent_name=self.name,
                passed=True,
                confidence=0.0,
                metadata={"reason": "No backends available"},
            )

        available = [b for b in self._backends if b.is_available()]
        if not available:
            return AgentResult(
                agent_name=self.name,
                passed=True,
                confidence=0.0,
                metadata={"reason": "No backends reachable"},
            )

        # 各バックエンドに問い合わせ
        responses: List[Dict[str, Any]] = []
        for backend in available:
            try:
                raw = backend.query(self._get_audit_prompt(), target.content)
                parsed = json.loads(raw)
                responses.append(parsed)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Backend %s failed: %s", backend, exc)

        if not responses:
            return AgentResult(
                agent_name=self.name,
                passed=True,
                confidence=0.0,
                metadata={"reason": "All backends failed"},
            )

        # コンセンサス計算
        return self._compute_consensus(responses, target)

    # PURPOSE: [L2-auto] _compute_consensus の関数定義
    def _compute_consensus(
        self, responses: List[Dict[str, Any]], target: AuditTarget
    ) -> AgentResult:
        """応答間のコンセンサスを計算。"""
        # 各応答の issue コードを集計
        code_counts: Dict[str, int] = {}
        all_issues: List[AuditIssue] = []
        n = len(responses)

        for resp in responses:
            for issue in resp.get("issues", []):
                code = issue.get("code", "UNKNOWN")
                code_counts[code] = code_counts.get(code, 0) + 1

        # 過半数が検出した issue のみ採用
        majority_threshold = n / 2
        consensus_issues: List[AuditIssue] = []

        for resp in responses:
            for issue in resp.get("issues", []):
                code = issue.get("code", "UNKNOWN")
                if code_counts.get(code, 0) > majority_threshold:
                    severity_str = issue.get("severity", "low")
                    try:
                        severity = AuditSeverity(severity_str)
                    except ValueError:
                        severity = AuditSeverity.LOW

                    consensus_issues.append(
                        AuditIssue(
                            agent=self.name,
                            code=code,
                            severity=severity,
                            message=issue.get("message", ""),
                        )
                    )

        # 重複排除
        seen_codes = set()
        unique_issues = []
        for issue in consensus_issues:
            if issue.code not in seen_codes:
                seen_codes.add(issue.code)
                unique_issues.append(issue)

        # 確信度: 応答間の一致率
        if code_counts:
            agreement_rates = [count / n for count in code_counts.values()]
            confidence = sum(agreement_rates) / len(agreement_rates)
        else:
            confidence = 1.0  # 全員が問題なしと判断 → 高確信度

        has_critical = any(i.severity == AuditSeverity.CRITICAL for i in unique_issues)
        has_high = any(i.severity == AuditSeverity.HIGH for i in unique_issues)

        return AgentResult(
            agent_name=self.name,
            passed=not (has_critical or has_high),
            issues=unique_issues,
            confidence=confidence,
            metadata={
                "n_backends": n,
                "n_issues_total": sum(code_counts.values()),
                "consensus_codes": list(seen_codes),
            },
        )
