# PROOF: [L2/インフラ] <- mekhane/ccl/executor.py
# CCL Zero-Trust Executor - 統合エントリポイント

"""
Zero-Trust CCL Executor

5段階の強制機構を統合:
- Phase 0: 仕様強制注入
- Phase 1: 出力構造強制 (Pydantic)
- Phase 2: 出力検証
- Phase 3: 論理監査 (Multi-Agent) - 将来実装
- Phase 4: 失敗パターン学習
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .macro_expander import MacroExpander
from .spec_injector import SpecInjector
from .workflow_signature import EnforcementLevel, SignatureRegistry
from .guardrails.validators import CCLOutputValidator, ValidationError, ValidationResult
from .learning.failure_db import get_failure_db


@dataclass
class ExecutionContext:
    """CCL 実行コンテキスト"""

    ccl_expr: str
    injected_prompt: str
    warnings: List[str]
    raw_expr: str = ""
    expanded_expr: str = ""
    workflow_count: int = 0
    enforcement_level: EnforcementLevel = EnforcementLevel.SINGLE
    execution_manifest: Dict[str, Any] = field(default_factory=dict)
    contract_trace: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """CCL 実行結果"""

    success: bool
    output: str
    validation: ValidationResult
    context: ExecutionContext
    blocked_reason: Optional[str] = None
    contract_trace: Dict[str, Any] = field(default_factory=dict)


class ZeroTrustCCLExecutor:
    """Zero-Trust CCL 実行エンジン"""

    def __init__(self):
        self.injector = SpecInjector()
        self.validator = CCLOutputValidator()
        self.failure_db = get_failure_db()
        self.expander = MacroExpander()
        self.signature_registry = SignatureRegistry()

    def _build_blocked_message(
        self,
        *,
        ccl_expr: str,
        unmet_requirements: List[str],
        blocking_reason: str,
        safe_next_step: str,
    ) -> str:
        """Return a standardized CCL CONTRACT BLOCKED message."""
        lines = [
            "CCL CONTRACT BLOCKED",
            f"- requested_skill: `{ccl_expr}`",
            "- requested_depth_or_derivative: preflight",
            f"- unmet_requirements: {', '.join(unmet_requirements)}",
            f"- blocking_reason: {blocking_reason}",
            f"- safe_next_step: {safe_next_step}",
        ]
        return "\n".join(lines)

    def _find_unresolved_macros(self, expanded_expr: str) -> List[str]:
        """Find remaining unresolved macro references after expansion."""
        unresolved = []
        for match in self.expander.MACRO_PATTERN.finditer(expanded_expr):
            name = match.group(1)
            if not name.isdigit():
                unresolved.append(f"@{name}{match.group(2) or ''}")
        return unresolved

    def _build_execution_manifest(self, ccl_expr: str) -> Dict[str, Any]:
        """Build preflight execution manifest for explicit CCL invocation."""
        expanded_expr, macro_expanded, derivative = self.expander.expand(ccl_expr)
        unresolved_macros = self._find_unresolved_macros(expanded_expr)
        if unresolved_macros:
            return {
                "blocked": True,
                "blocking_reason": "macro expansion failed",
                "safe_next_step": "未解決 macro を展開可能な形に直すか、macro を使わず explicit CCL にしてください",
                "unmet_requirements": [
                    "macro_expansion",
                    f"unresolved_macros={', '.join(unresolved_macros)}",
                ],
            }

        invocations = self.signature_registry.extract_invocations(expanded_expr)
        if not invocations:
            return {
                "blocked": True,
                "blocking_reason": "workflow extraction failed",
                "safe_next_step": "少なくとも 1 つの workflow invocation を含む explicit CCL を指定してください",
                "unmet_requirements": ["expanded_workflow_count"],
            }

        workflows = []
        for invocation in invocations:
            signature = self.signature_registry.get(invocation.workflow)
            workflows.append(
                {
                    "name": invocation.workflow,
                    "derivative": invocation.derivative,
                    "required_outputs": list(signature.required_outputs)
                    if signature
                    else [],
                    "required_gates": list(signature.required_gates)
                    if signature
                    else [],
                    "interactive_gate": bool(signature and signature.interactive_gate),
                    "native_phase_markers": list(signature.native_phase_markers)
                    if signature
                    else [],
                    "macro_expanded": macro_expanded,
                    "known_signature": signature is not None,
                }
            )

        workflow_count = len(workflows)
        enforcement_level = EnforcementLevel.from_workflow_count(workflow_count)
        return {
            "blocked": False,
            "raw_expr": ccl_expr,
            "expanded_expr": expanded_expr,
            "workflow_count": workflow_count,
            "workflow_list": [workflow["name"] for workflow in workflows],
            "macro_expanded": macro_expanded,
            "derivative": derivative,
            "enforcement_level": enforcement_level.value,
            "workflows": workflows,
        }

    def _build_contract_trace(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Create a shared contract trace structure."""
        trace = {
            "expanded_expr": manifest.get("expanded_expr", ""),
            "workflow_count": manifest.get("workflow_count", 0),
            "enforcement_level": manifest.get("enforcement_level", "SINGLE"),
            "workflows": [
                {
                    "name": workflow["name"],
                    "phase_status": "pending",
                    "gate_status": "pending"
                    if workflow.get("interactive_gate")
                    else "not_required",
                    "validation_status": "pending",
                }
                for workflow in manifest.get("workflows", [])
            ],
        }
        if manifest.get("enforcement_level") == EnforcementLevel.COMPLEX.value:
            trace["stages"] = {
                "plan": "completed",
                "execution": "pending",
                "verification": "pending",
            }
        return trace

    def _blocked_validation(
        self,
        ccl_expr: str,
        manifest: Dict[str, Any],
        contract_trace: Dict[str, Any],
    ) -> ValidationResult:
        """Create a blocked validation result."""
        blocking_reason = manifest.get("blocking_reason", "preflight blocked")
        unmet_requirements = manifest.get("unmet_requirements", ["execution_manifest"])
        safe_next_step = manifest.get(
            "safe_next_step",
            "manifest を組み立てられる explicit CCL に直してください",
        )
        error = ValidationError(
            operator="ccl",
            error_type="CCL CONTRACT BLOCKED",
            message=blocking_reason,
            suggestion=safe_next_step,
            phase="plan",
        )
        if "stages" in contract_trace:
            contract_trace["stages"]["plan"] = "blocked"
        return ValidationResult(
            valid=False,
            errors=[error],
            warnings=[],
            blocked=True,
            contract_failures=[
                f"unmet_requirements={', '.join(unmet_requirements)}",
                blocking_reason,
            ],
        )

    def prepare(self, ccl_expr: str) -> ExecutionContext:
        """Phase 0: 実行準備 + preflight manifest."""
        manifest = self._build_execution_manifest(ccl_expr)
        contract_trace = self._build_contract_trace(manifest)

        if manifest.get("blocked"):
            blocked_prompt = self._build_blocked_message(
                ccl_expr=ccl_expr,
                unmet_requirements=manifest.get("unmet_requirements", []),
                blocking_reason=manifest.get("blocking_reason", "preflight blocked"),
                safe_next_step=manifest.get("safe_next_step", "explicit CCL を修正してください"),
            )
            return ExecutionContext(
                ccl_expr=ccl_expr,
                injected_prompt=blocked_prompt,
                warnings=[manifest.get("blocking_reason", "preflight blocked")],
                raw_expr=ccl_expr,
                expanded_expr=manifest.get("expanded_expr", ccl_expr),
                workflow_count=manifest.get("workflow_count", 0),
                enforcement_level=EnforcementLevel.SINGLE,
                execution_manifest=manifest,
                contract_trace=contract_trace,
            )

        injected_prompt = self.injector.inject(manifest["expanded_expr"])
        warnings_records = self.failure_db.get_warnings(manifest["expanded_expr"])
        warnings_text = self.failure_db.format_warnings(warnings_records)
        if warnings_text:
            injected_prompt = warnings_text + "\n" + injected_prompt

        return ExecutionContext(
            ccl_expr=ccl_expr,
            injected_prompt=injected_prompt,
            warnings=[w.message for w in warnings_records],
            raw_expr=ccl_expr,
            expanded_expr=manifest["expanded_expr"],
            workflow_count=manifest["workflow_count"],
            enforcement_level=EnforcementLevel(manifest["enforcement_level"]),
            execution_manifest=manifest,
            contract_trace=contract_trace,
        )

    def validate(self, output: str, context: ExecutionContext) -> ValidationResult:
        """Phase 2: 出力検証."""
        return self.validator.validate(
            output,
            context.expanded_expr or context.ccl_expr,
            manifest=context.execution_manifest,
            contract_trace=context.contract_trace,
        )

    def preflight(
        self, ccl_expr: str
    ) -> tuple[ExecutionContext, Optional[ValidationResult]]:
        """Run preflight only and return blocked validation when applicable."""
        context = self.prepare(ccl_expr)
        if not context.execution_manifest.get("blocked"):
            return context, None
        return (
            context,
            self._blocked_validation(
                ccl_expr,
                context.execution_manifest,
                context.contract_trace,
            ),
        )

    def record_result(
        self, context: ExecutionContext, validation: ValidationResult, output: str
    ) -> None:
        """Phase 4: 結果を記録."""
        if validation.blocked:
            return

        expr = context.expanded_expr or context.ccl_expr
        if validation.valid:
            self.failure_db.record_success(ccl_expr=expr, output_summary=output[:200])
            return

        for error in validation.errors:
            self.failure_db.record_failure(
                ccl_expr=expr,
                operator=error.operator,
                failure_type=error.error_type,
                cause=error.message,
            )

    def execute(
        self, ccl_expr: str, output: str, record: bool = True
    ) -> ExecutionResult:
        """CCL 実行フロー全体."""
        context = self.prepare(ccl_expr)
        manifest = context.execution_manifest

        if manifest.get("blocked"):
            validation = self._blocked_validation(
                ccl_expr, manifest, context.contract_trace
            )
            return ExecutionResult(
                success=False,
                output=context.injected_prompt,
                validation=validation,
                context=context,
                blocked_reason=manifest.get("blocking_reason"),
                contract_trace=context.contract_trace,
            )

        if "stages" in context.contract_trace:
            context.contract_trace["stages"]["execution"] = "completed"

        validation = self.validate(output, context)

        if "stages" in context.contract_trace:
            context.contract_trace["stages"]["verification"] = (
                "completed" if validation.valid else "invalid"
            )

        if record:
            self.record_result(context, validation, output)

        return ExecutionResult(
            success=validation.valid and not validation.blocked,
            output=output,
            validation=validation,
            context=context,
            blocked_reason=manifest.get("blocking_reason") if validation.blocked else None,
            contract_trace=context.contract_trace,
        )

    def get_regeneration_prompt(self, result: ExecutionResult) -> str:
        """再生成用のプロンプトを取得."""
        if result.success:
            return ""

        return f"""
{result.validation.regeneration_instruction}

---

## 元の CCL 式

`{result.context.ccl_expr}`

---

## 再生成してください
# PURPOSE: CCL 式から LLM に渡すプロンプトを生成

上記の問題を修正した出力を生成してください。
"""


def create_ccl_prompt(ccl_expr: str) -> str:
    """CCL 式から LLM に渡すプロンプトを生成."""
    executor = ZeroTrustCCLExecutor()
    context = executor.prepare(ccl_expr)
    return context.injected_prompt


def validate_ccl_output(ccl_expr: str, output: str) -> ValidationResult:
    """CCL 出力を検証."""
    executor = ZeroTrustCCLExecutor()
    context = executor.prepare(ccl_expr)
    if context.execution_manifest.get("blocked"):
        return executor._blocked_validation(
            ccl_expr, context.execution_manifest, context.contract_trace
        )
    return executor.validate(output, context)


def build_zero_trust_blocked_payload(
    ccl_expr: str,
    context: ExecutionContext,
    validation: ValidationResult,
) -> Dict[str, Any]:
    """Build a fail-closed payload for Zero-Trust pre/postflight violations."""
    manifest = context.execution_manifest
    first_error = validation.errors[0] if validation.errors else None
    unmet_requirements = manifest.get("unmet_requirements") or validation.contract_failures
    if not unmet_requirements:
        unmet_requirements = [
            error.error_type for error in validation.errors
        ] or ["zero_trust_validation"]
    blocking_reason = manifest.get("blocking_reason") or (
        first_error.message if first_error else "zero-trust validation failed"
    )
    safe_next_step = manifest.get("safe_next_step") or (
        first_error.suggestion
        if first_error
        else "native structure と interactive gate を満たすまで再生成してください"
    )
    return {
        "status": "blocked",
        "error_type": "ccl_contract_blocked",
        "requested_ccl": ccl_expr,
        "normalized_ccl": context.expanded_expr or ccl_expr,
        "unmet_requirements": unmet_requirements,
        "blocking_reason": blocking_reason,
        "safe_next_step": safe_next_step,
        "validation": validation.to_dict(),
        "contract_trace": context.contract_trace,
    }


if __name__ == "__main__":
    executor = ZeroTrustCCLExecutor()

    print("=" * 60)
    print("Phase 0: プロンプト生成")
    print("=" * 60)
    context = executor.prepare("/noe!~/u+")
    print(context.injected_prompt)

    print("\n" + "=" * 60)
    print("Phase 2: 出力検証 (不完全な出力)")
    print("=" * 60)
    bad_output = "分析結果です。終わり。"
    result = executor.execute("/noe!~/u+", bad_output, record=False)
    print(f"Success: {result.success}")
    print(f"Errors: {len(result.validation.errors)}")
    print(result.validation.regeneration_instruction)
