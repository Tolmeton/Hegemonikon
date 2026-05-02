# PROOF: [L2/インフラ] <- mekhane/ccl/guardrails/validators.py
# Phase 2: CCL 出力検証

"""
CCL Output Validator - 出力検証モジュール

目的:
- 演算子別必須セクションの存在確認
- 最小長の検証
- 違反時のリジェクト + 再生成指示
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set
import re


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: 検証エラー
class ValidationError:
    """検証エラー"""

    operator: str
    error_type: str
    message: str
    suggestion: str
    workflow: Optional[str] = None
    phase: Optional[str] = None
    gate_type: Optional[str] = None


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: 検証結果
class ValidationResult:
    """検証結果"""

    valid: bool
    errors: List[ValidationError]
    warnings: List[str]
    blocked: bool = False
    contract_failures: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize validation result for API/MCP responses."""
        return {
            "valid": self.valid,
            "blocked": self.blocked,
            "warnings": list(self.warnings),
            "contract_failures": list(self.contract_failures),
            "errors": [asdict(error) for error in self.errors],
        }

    # PURPOSE: validators の regeneration instruction 処理を実行する
    @property
    # PURPOSE: 再生成用の指示を生成
    def regeneration_instruction(self) -> str:
        """再生成用の指示を生成"""
        if self.valid:
            return ""

        heading = (
            "## 🛑 CCL CONTRACT BLOCKED\n"
            if self.blocked
            else "## ❌ 検証失敗 — 再生成が必要\n"
        )
        lines = [heading]
        lines.append("以下の問題を修正して再生成してください:\n")

        for i, err in enumerate(self.errors, 1):
            lines.append(f"### {i}. {err.error_type}")
            lines.append(f"- **演算子**: `{err.operator}`")
            if err.workflow:
                lines.append(f"- **Workflow**: `{err.workflow}`")
            if err.phase:
                lines.append(f"- **Phase**: `{err.phase}`")
            if err.gate_type:
                lines.append(f"- **Gate**: `{err.gate_type}`")
            lines.append(f"- **問題**: {err.message}")
            lines.append(f"- **修正**: {err.suggestion}\n")

        if self.contract_failures:
            lines.append("## Contract Failures")
            for failure in self.contract_failures:
                lines.append(f"- {failure}")
            lines.append("")

        return "\n".join(lines)


# 演算子と必須セクションのマッピング
OPERATOR_REQUIRED_SECTIONS: Dict[str, List[str]] = {
    "!": ["## 全派生", "派生リスト", "同時実行"],
    "~": ["## 振動", "↔", "←", "→"],
    "*": ["## 融合", "統合結果"],
    "^": ["## メタ", "メタ分析", "メタ視点"],
    "+": ["## 詳細", "詳細展開"],
}

# 演算子ごとの最小出力行数
OPERATOR_MIN_LINES: Dict[str, int] = {
    "!": 20,  # 全派生は長くなるはず
    "~": 15,  # 振動は両方向必要
    "*": 10,
    "^": 10,
    "+": 15,
}

INTERACTIVE_WAIT_MARKERS = [
    "creator の反応を待つ",
    "creatorの反応を待つ",
    "反応待ち",
    "入力待ち",
    "ここで止まる",
    "ここで停止",
    "wait",
]

RESPONSIBILITY_MIXING_HINTS = [
    "/ene",
    "実行計画",
    "次アクション",
    "保存テスト",
    "実保存",
]

# PURPOSE: CCL 出力検証器

# PURPOSE: [L2-auto] CCLOutputValidator のクラス定義
class CCLOutputValidator:
    """CCL 出力検証器"""

    # PURPOSE: CCL 式から演算子を抽出
    def parse_operators(self, ccl_expr: str) -> Set[str]:
        """CCL 式から演算子を抽出"""
        operators = set()
        for char in ccl_expr:
            if char in OPERATOR_REQUIRED_SECTIONS:
                operators.add(char)
        return operators

    def _contains_marker(self, output: str, marker: str) -> bool:
        """Case-insensitive substring match."""
        return marker.lower() in output.lower()

    def _update_workflow_trace(
        self,
        contract_trace: Optional[Dict[str, Any]],
        workflow_name: str,
        *,
        phase_status: Optional[str] = None,
        gate_status: Optional[str] = None,
        validation_status: Optional[str] = None,
    ) -> None:
        """Update a workflow entry inside contract trace."""
        if not contract_trace:
            return

        for item in contract_trace.get("workflows", []):
            if item.get("name") != workflow_name:
                continue
            if phase_status is not None:
                item["phase_status"] = phase_status
            if gate_status is not None:
                item["gate_status"] = gate_status
            if validation_status is not None:
                item["validation_status"] = validation_status
            return

    # PURPOSE: 必須セクションの存在確認
    def check_required_sections(
        self, output: str, operators: Set[str]
    ) -> List[ValidationError]:
        """必須セクションの存在確認"""
        errors = []

        for op in operators:
            if op not in OPERATOR_REQUIRED_SECTIONS:
                continue

            required = OPERATOR_REQUIRED_SECTIONS[op]
            found = False

            for keyword in required:
                if keyword.lower() in output.lower():
                    found = True
                    break

            if not found:
                errors.append(
                    ValidationError(
                        operator=op,
                        error_type="必須セクション欠落",
                        message=f"演算子 `{op}` に必要なセクションがありません",
                        suggestion=f"以下のいずれかを出力に含めてください: {', '.join(required)}",
                    )
                )

        return errors

    # PURPOSE: 振動演算子の両方向確認
    def check_oscillation_bidirectional(self, output: str) -> List[ValidationError]:
        """振動演算子の両方向確認"""
        errors = []

        # 振動の両方向を示すパターン
        has_forward = bool(re.search(r"→|方向[12AB]|←.*→|A.*B", output))
        has_backward = bool(re.search(r"←|方向[12AB]|→.*←|B.*A", output))

        if "振動" in output and not (has_forward and has_backward):
            errors.append(
                ValidationError(
                    operator="~",
                    error_type="振動の一方向のみ",
                    message="振動演算子は両方向の分析が必要です",
                    suggestion="「A ↔ B」のように両方向を明示してください",
                )
            )

        return errors

    # PURPOSE: 最小長の確認
    def check_minimum_length(
        self, output: str, operators: Set[str]
    ) -> List[ValidationError]:
        """最小長の確認"""
        errors = []
        lines = output.strip().split("\n")

        for op in operators:
            if op in OPERATOR_MIN_LINES:
                min_lines = OPERATOR_MIN_LINES[op]
                if len(lines) < min_lines:
                    errors.append(
                        ValidationError(
                            operator=op,
                            error_type="出力が短すぎる",
                            message=f"演算子 `{op}` を使用した出力は最低 {min_lines} 行必要ですが、{len(lines)} 行しかありません",
                            suggestion="より詳細な出力を生成してください",
                        )
                    )

        return errors

    # PURPOSE: 演算子理解の証拠確認
    def check_operator_understanding(
        self, output: str, operators: Set[str]
    ) -> List[ValidationError]:
        """演算子理解の証拠確認"""
        errors = []

        if not operators:
            return errors

        # 理解確認セクションの存在
        has_understanding = "理解" in output or "確認" in output or "A:" in output

        if not has_understanding:
            errors.append(
                ValidationError(
                    operator="*",  # 汎用
                    error_type="理解証明欠落",
                    message="演算子理解の証明がありません",
                    suggestion="「## 理解確認」セクションで各演算子の意味を説明してください",
                )
            )

        return errors

    def check_workflow_contracts(
        self,
        output: str,
        manifest: Optional[Dict[str, Any]],
        contract_trace: Optional[Dict[str, Any]] = None,
    ) -> List[ValidationError]:
        """Validate workflow-level contract requirements for multi-skill CCL."""
        if not manifest:
            return []

        workflows = manifest.get("workflows", [])
        if len(workflows) < 2:
            return []

        errors: List[ValidationError] = []
        has_wait_marker = any(
            self._contains_marker(output, marker) for marker in INTERACTIVE_WAIT_MARKERS
        )

        for workflow in workflows:
            workflow_name = workflow["name"]
            self._update_workflow_trace(
                contract_trace,
                workflow_name,
                phase_status="completed",
                gate_status="not_required"
                if not workflow.get("interactive_gate")
                else "satisfied",
                validation_status="passed",
            )

            native_phase_markers = workflow.get("native_phase_markers", [])
            if native_phase_markers and not any(
                self._contains_marker(output, marker) for marker in native_phase_markers
            ):
                errors.append(
                    ValidationError(
                        operator="ccl",
                        error_type="native phase marker 欠落",
                        message=(
                            f"`{workflow_name}` の native phase marker が出力に見当たりません"
                        ),
                        suggestion=(
                            "phase 見出しを prose に畳まず、workflow の native structure を保持してください"
                        ),
                        workflow=workflow_name,
                        phase="native",
                    )
                )

            if workflow.get("interactive_gate") and has_wait_marker:
                self._update_workflow_trace(
                    contract_trace,
                    workflow_name,
                    gate_status="pending_creator",
                    validation_status="passed",
                )
                continue

            missing_outputs = [
                item
                for item in workflow.get("required_outputs", [])
                if not self._contains_marker(output, item)
            ]
            if missing_outputs:
                errors.append(
                    ValidationError(
                        operator="ccl",
                        error_type="required_outputs 欠落",
                        message=(
                            f"`{workflow_name}` に必要な出力要素が不足しています: "
                            f"{', '.join(missing_outputs)}"
                        ),
                        suggestion=(
                            "required_outputs を native 形式のまま出力し、省略要約に置換しないでください"
                        ),
                        workflow=workflow_name,
                        phase="output",
                    )
                )

        interactive_index = next(
            (
                index
                for index, workflow in enumerate(workflows)
                if workflow.get("interactive_gate")
            ),
            None,
        )
        if interactive_index is None or interactive_index >= len(workflows) - 1:
            return errors

        interactive_workflow = workflows[interactive_index]
        downstream = workflows[interactive_index + 1 :]
        downstream_names = [workflow["name"] for workflow in downstream]
        mentions_downstream = any(
            self._contains_marker(output, name) for name in downstream_names
        ) or any(
            self._contains_marker(output, hint) for hint in RESPONSIBILITY_MIXING_HINTS
        )

        if has_wait_marker:
            for workflow in downstream:
                self._update_workflow_trace(
                    contract_trace,
                    workflow["name"],
                    phase_status="pending",
                    validation_status="pending",
                )
            return errors

        if mentions_downstream:
            errors.append(
                ValidationError(
                    operator="ccl",
                    error_type="interactive gate violation",
                    message=(
                        f"`{interactive_workflow['name']}` は Creator の反応待ちが必要なのに、"
                        " 後続 workflow まで完了扱いしています"
                    ),
                    suggestion=(
                        "interactive gate で停止し、Creator の入力を得るまでは後続 workflow を進めないでください"
                    ),
                    workflow=interactive_workflow["name"],
                    phase="interactive",
                    gate_type="creator_response",
                )
            )
            self._update_workflow_trace(
                contract_trace,
                interactive_workflow["name"],
                phase_status="blocked",
                gate_status="violated",
                validation_status="failed",
            )

            first_downstream = downstream[0]["name"]
            errors.append(
                ValidationError(
                    operator="ccl",
                    error_type="責務混入",
                    message=(
                        f"`{interactive_workflow['name']}` の出力に `{first_downstream}` の責務が混入しています"
                    ),
                    suggestion=(
                        "前段 workflow の責務と後段 workflow の責務を分離し、後段は gate 通過後にのみ実行してください"
                    ),
                    workflow=first_downstream,
                    phase="handoff",
                )
            )
            self._update_workflow_trace(
                contract_trace,
                first_downstream,
                phase_status="invalid",
                validation_status="failed",
            )

        return errors

    # PURPOSE: 出力を検証
    def validate(
        self,
        output: str,
        ccl_expr: str,
        manifest: Optional[Dict[str, Any]] = None,
        contract_trace: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """出力を検証"""
        operators = self.parse_operators(ccl_expr)
        errors = []
        warnings = []

        # 各種チェック
        errors.extend(self.check_required_sections(output, operators))
        errors.extend(
            self.check_oscillation_bidirectional(output) if "~" in operators else []
        )
        errors.extend(self.check_minimum_length(output, operators))
        errors.extend(self.check_operator_understanding(output, operators))
        workflow_errors = self.check_workflow_contracts(
            output, manifest, contract_trace=contract_trace
        )
        errors.extend(workflow_errors)

        # 警告（エラーではないがベストプラクティス違反）
        if len(output) < 500:
            warnings.append("⚠️ 出力が500文字未満です。省略していませんか？")

        if "自己監査" not in output and "self-audit" not in output.lower():
            warnings.append("⚠️ 自己監査セクションがありません")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            blocked=any(error.gate_type for error in errors),
            contract_failures=[error.message for error in workflow_errors],
        )


# テスト用
if __name__ == "__main__":
    validator = CCLOutputValidator()

    # 不完全な出力をテスト
    bad_output = """
    分析結果です。
    終わり。
    """

    result = validator.validate(bad_output, "/noe!~/u+")
    print(f"Valid: {result.valid}")
    print(f"Errors: {len(result.errors)}")
    for err in result.errors:
        print(f"  - {err.error_type}: {err.message}")
    print(result.regeneration_instruction)
