from __future__ import annotations
# PROOF: [L2/FEP] <- mekhane/fep/uml_sel_bridge.py
# PURPOSE: UML × SEL 統合検証ブリッジ
"""
PROOF: [L2/FEP] このファイルは存在しなければならない

A0 → UML (Phase 1) はヒューリスティック検査
   → SEL は YAML frontmatter ベースの要件検証
   → 両者を統合した検証が必要
   → uml_sel_bridge が担う

Q.E.D.

---

UML-SEL Bridge — メタ認知チェックとSEL要件の統合検証

Phase 2 の核心: UML 5段階の結果を SEL 検証に接続し、
WF 出力が「MP を経由した品質」を持つことを構造的に検証する。

Usage:
    from mekhane.fep.uml_sel_bridge import validate_with_uml

    result = validate_with_uml(
        workflow="noe", operator="+",
        output=response, context=user_input,
        confidence=75.0,
    )
    print(result.summary)
    print(f"SEL: {result.sel_result.score:.0%}")
    print(f"UML: {result.uml_report.summary}")
"""


from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

from mekhane.fep.metacognitive_layer import (
    run_full_uml,
    UMLReport,
)
from mekhane.ccl.sel_validator import (
    SELValidator,
    SELValidationResult,
)


# =============================================================================
# Data Classes
# =============================================================================


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: UML-SEL 統合検証の結果
class UMLSELResult:
    """UML-SEL 統合検証の結果"""

    workflow: str
    operator: str
    sel_result: SELValidationResult
    uml_report: UMLReport
    combined_score: float = 0.0  # 重み付き統合スコア
    sel_weight: float = 0.7  # SEL の重み
    uml_weight: float = 0.3  # UML の重み

    # PURPOSE: SEL 遵守 かつ UML 全通過
    @property
    def is_compliant(self) -> bool:
        """SEL 遵守 かつ UML 全通過"""
        return self.sel_result.is_compliant and self.uml_report.overall_pass

    # PURPOSE: summary の処理
    @property
    def summary(self) -> str:
        sel_pct = f"{self.sel_result.score:.0%}"
        uml_pct = f"{self.uml_report.pass_count}/{self.uml_report.total_count}"
        combined = f"{self.combined_score:.0%}"
        status = "✅" if self.is_compliant else "⚠️"
        amp = " 🔄AMP" if self.uml_report.feedback_loop_triggered else ""
        return (
            f"{status} {self.workflow}{self.operator}: "
            f"統合={combined} (SEL={sel_pct} UML={uml_pct}){amp}"
        )

    # PURPOSE: Multi-line detail report
    @property
    def details(self) -> str:
        """Multi-line detail report."""
        lines = [
            f"═ UML-SEL 統合レポート: {self.workflow}{self.operator} ═",
            f"",
            f"📊 統合スコア: {self.combined_score:.0%}",
            f"   SEL: {self.sel_result.score:.0%} (weight={self.sel_weight})",
            f"   UML: {self.uml_report.pass_count}/{self.uml_report.total_count} (weight={self.uml_weight})",
        ]

        if self.sel_result.missing_requirements:
            lines.append(f"")
            lines.append(f"⚠️ SEL 不足:")
            for req in self.sel_result.missing_requirements:
                lines.append(f"  - {req}")

        if self.sel_result.uml_missing:
            lines.append(f"")
            lines.append(f"⚠️ UML要件 不足:")
            for req in self.sel_result.uml_missing:
                lines.append(f"  - {req}")

        failed_uml = [
            c for c in self.uml_report.all_checks if not c.passed
        ]
        if failed_uml:
            lines.append(f"")
            lines.append(f"⚠️ UML Stage 不通過:")
            for c in failed_uml:
                lines.append(f"  - {c.stage_label}: {c.result}")

        if self.uml_report.feedback_loop_triggered:
            lines.append(f"")
            lines.append(
                f"🔄 AMP: {self.uml_report.feedback_loop_count} loops — "
                f"{self.uml_report.feedback_reason}"
            )

        return "\n".join(lines)


# =============================================================================
# Core Functions
# =============================================================================


# PURPOSE: SEL + UML 統合検証
def validate_with_uml(
    workflow: str,
    operator: str,
    output: str,
    context: str = "",
    confidence: float = 0.0,
    sel_weight: float = 0.7,
    uml_weight: float = 0.3,
    workflows_dir: Optional[Path] = None,
) -> UMLSELResult:
    """SEL + UML 統合検証を実行。

    1. SEL 要件をロード (uml_requirements 含む) して検証
    2. UML 5段階 + AMP フィードバック実行
    3. 重み付き統合スコアを算出

    Args:
        workflow: WF名 (e.g., "noe")
        operator: 演算子 (e.g., "+")
        output: WF の出力テキスト
        context: 入力コンテキスト
        confidence: 確信度 (0-100)
        sel_weight: SEL スコアの重み (default: 0.7)
        uml_weight: UML スコアの重み (default: 0.3)

    Returns:
        UMLSELResult with combined score and details
    """
    # 1. SEL validation
    validator = SELValidator(workflows_dir=workflows_dir)
    sel_result = validator.validate(workflow, operator, output)

    # 2. UML validation
    uml_report = run_full_uml(
        context=context,
        output=output,
        wf_name=workflow,
        confidence=confidence,
    )

    # 3. Combined score
    uml_pass_rate = (
        uml_report.pass_count / uml_report.total_count
        if uml_report.total_count > 0
        else 1.0
    )
    combined = sel_weight * sel_result.score + uml_weight * uml_pass_rate

    return UMLSELResult(
        workflow=workflow,
        operator=operator,
        sel_result=sel_result,
        uml_report=uml_report,
        combined_score=combined,
        sel_weight=sel_weight,
        uml_weight=uml_weight,
    )


# PURPOSE: 複数WF出力を一括統合検証
def validate_batch_with_uml(
    outputs: dict,
    contexts: Optional[dict] = None,
    confidence: float = 0.0,
) -> List[UMLSELResult]:
    """複数WF出力を一括統合検証。

    Args:
        outputs: {workflow: {operator: output_text}}
        contexts: {workflow: context_text} (optional)
        confidence: 確信度 (0-100)

    Returns:
        List of UMLSELResult
    """
    results = []
    for workflow, ops in outputs.items():
        ctx = (contexts or {}).get(workflow, "")
        for operator, output in ops.items():
            results.append(
                validate_with_uml(
                    workflow=workflow,
                    operator=operator,
                    output=output,
                    context=ctx,
                    confidence=confidence,
                )
            )
    return results
