"""
CCL Contract Compiler / Validator

明示 CCL invocation を strict contract として扱うための共通基盤。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json
import re

from hermeneus.src.ccl_ast import (
    Adjunction,
    ConvergenceLoop,
    ForLoop,
    Fusion,
    IfCondition,
    Integral,
    MacroRef,
    Morphism,
    OpType,
    Oscillation,
    Parallel,
    PartialDiff,
    Pipeline,
    PreVerb,
    Sequence,
    Summation,
    TaggedBlock,
    WhileLoop,
    Workflow,
)
from hermeneus.src.ccl_normalizer import normalize_ccl_input
from hermeneus.src.macros import get_macro_expansion, get_macro_metadata, get_macro_sources
from hermeneus.src.parser import CCLParser
from hermeneus.src.skill_registry import ExecutionContractDefinition, SkillRegistry
from mekhane.ccl.macro_expander import MacroExpander
from mekhane.ccl.macro_registry import MacroRegistry
from mekhane.ccl.sel_validator import SELValidator


DEFAULT_EXECUTION_CONTRACT = ExecutionContractDefinition(
    explicit_invocation="strict",
    implicit_trigger="flexible",
    fallback_behavior="declare_and_stop",
    default_depth="L2",
    macro_expansion="required",
    required_outputs=[],
)

OPERATOR_REQUIREMENTS: Dict[str, List[str]] = {
    "+": ["詳細な根拠提示", "複数の視点", "具体例"],
    "-": ["核心のみ", "説明省略可"],
    "^": ["前提の明示", "構造の説明"],
    "!": ["全派生の列挙", "各派生の実行"],
}

REQUIREMENT_PATTERNS: Dict[str, List[str]] = {
    "declared_derivative": ["派生選択", "derivative", "depth:"],
    "phase_0": ["phase 0", "p-0", "s-0", "prolegomena"],
    "phase_0_5": ["phase 0.5", "p-0.5", "s-0.5", "epistemic mapping"],
    "phase_1": ["phase 1", "p-1", "s-1"],
    "phase_2": ["phase 2", "p-2", "s-2"],
    "phase_3": ["phase 3", "p-3", "s-3"],
    "phase_4": ["phase 4", "p-4", "s-4"],
    "phase_5": ["phase 5", "p-5", "s-5"],
    "phase_6": ["phase 6", "p-6", "s-6"],
    "checkpoints": ["[checkpoint", "checkpoint"],
    "orthogonality_proof": ["orthogonality", "直交"],
    "t1_t3": ["t1", "t2", "t3"],
    "skqs": ["skqs"],
    "sgqs": ["sgqs"],
    "macro_trace": ["展開", "expanded", "@", "macro"],
    "expanded_ccl": ["expanded ccl", "展開:"],
    "child_workflows": ["/"],
    "convergence_trace": ["収束", "trace", "loop", "反復"],
}

OPTYPE_TO_SYMBOL = {
    OpType.DEEPEN: "+",
    OpType.CONDENSE: "-",
    OpType.ASCEND: "^",
    OpType.EXPAND: "!",
    OpType.QUERY: "?",
    OpType.INVERT: "\\",
    OpType.DIFF: "'",
}


@dataclass
class ContractObligation:
    id: str
    kind: str
    source: str
    requirement: str
    runtime_enforced: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "source": self.source,
            "requirement": self.requirement,
            "runtime_enforced": self.runtime_enforced,
            "metadata": dict(self.metadata),
        }


@dataclass
class CompiledCCLContract:
    requested_ccl: str
    normalized_ccl: str
    expanded_ccl: str
    invocation_mode: str
    strict: bool
    fallback_behavior: str
    default_depth: str
    macro_names: List[str] = field(default_factory=list)
    workflows: List[str] = field(default_factory=list)
    obligations: List[ContractObligation] = field(default_factory=list)
    source_paths: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requested_ccl": self.requested_ccl,
            "normalized_ccl": self.normalized_ccl,
            "expanded_ccl": self.expanded_ccl,
            "invocation_mode": self.invocation_mode,
            "strict": self.strict,
            "fallback_behavior": self.fallback_behavior,
            "default_depth": self.default_depth,
            "macro_names": list(self.macro_names),
            "workflows": list(self.workflows),
            "obligations": [ob.to_dict() for ob in self.obligations],
            "source_paths": dict(self.source_paths),
        }


@dataclass
class CCLContractValidationResult:
    contract: CompiledCCLContract
    is_compliant: bool
    met_requirements: List[str] = field(default_factory=list)
    unmet_requirements: List[str] = field(default_factory=list)
    blocking_reason: str = ""

    def blocked_payload(self) -> Dict[str, Any]:
        return {
            "status": "blocked",
            "error_type": "ccl_contract_blocked",
            "requested_ccl": self.contract.requested_ccl,
            "normalized_ccl": self.contract.normalized_ccl,
            "unmet_requirements": list(self.unmet_requirements),
            "blocking_reason": self.blocking_reason or "explicit CCL invocation contract was not satisfied",
            "safe_next_step": "不足要件を満たすか、Tolmetes が軽量化を明示許可するまで停止",
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_compliant": self.is_compliant,
            "met_requirements": list(self.met_requirements),
            "unmet_requirements": list(self.unmet_requirements),
            "blocking_reason": self.blocking_reason,
            "blocked_payload": self.blocked_payload() if not self.is_compliant else None,
        }


class CCLContractCompiler:
    """CCL 式から strict execution contract を構築する。"""

    def __init__(
        self,
        skill_registry: Optional[SkillRegistry] = None,
        sel_validator: Optional[SELValidator] = None,
    ):
        self.skill_registry = skill_registry or SkillRegistry()
        self.sel_validator = sel_validator or SELValidator()
        self.macro_metadata = get_macro_metadata()
        self.macro_sources = get_macro_sources()

    def compile(
        self,
        ccl: str,
        invocation_mode: str = "explicit",
    ) -> CompiledCCLContract:
        normalized = normalize_ccl_input(ccl)
        expanded, macro_names = self._expand_macros(normalized)
        ast = CCLParser().parse(self._sanitize_for_parser(expanded))

        obligations: List[ContractObligation] = []
        workflows: List[str] = []
        source_paths: Dict[str, str] = {}

        strict = invocation_mode == "explicit"
        fallback_behavior = DEFAULT_EXECUTION_CONTRACT.fallback_behavior
        default_depth = DEFAULT_EXECUTION_CONTRACT.default_depth

        for macro_name in macro_names:
            macro_contract = self._contract_from_dict(
                self.macro_metadata.get(macro_name, {}).get("execution_contract", {})
            )
            strict = strict or macro_contract.explicit_invocation == "strict"
            fallback_behavior = macro_contract.fallback_behavior or fallback_behavior
            default_depth = macro_contract.default_depth or default_depth
            source_paths[f"@{macro_name}"] = self.macro_sources.get(macro_name, "")
            obligations.extend(self._macro_obligations(macro_name, macro_contract))

        self._compile_node(
            node=ast,
            obligations=obligations,
            workflows=workflows,
            source_paths=source_paths,
        )

        return CompiledCCLContract(
            requested_ccl=ccl,
            normalized_ccl=normalized,
            expanded_ccl=expanded,
            invocation_mode=invocation_mode,
            strict=strict,
            fallback_behavior=fallback_behavior,
            default_depth=default_depth,
            macro_names=macro_names,
            workflows=workflows,
            obligations=obligations,
            source_paths=source_paths,
        )

    def _expand_macros(self, normalized_ccl: str) -> tuple[str, List[str]]:
        registry = MacroRegistry()
        expander = MacroExpander(registry)
        macro_names = [macro.name for macro in expander.list_macros_in_expr(normalized_ccl)]
        expanded, _, _ = expander.expand(normalized_ccl)
        for _ in range(3):
            nested, did_expand, _ = expander.expand(expanded)
            if not did_expand:
                break
            expanded = nested
        return expanded, macro_names

    def _sanitize_for_parser(self, ccl: str) -> str:
        """contract compile 用の軽量サニタイズ。

        parser がまだ受け付けない symbolic iteration (`×N`) を最小安全値に落とす。
        これは contract compile 専用であり、runtime の実行式は変更しない。
        """
        return re.sub(r"×[A-Za-z_][A-Za-z0-9_]*", "×1", ccl)

    def _compile_node(
        self,
        node: Any,
        obligations: List[ContractObligation],
        workflows: List[str],
        source_paths: Dict[str, str],
    ) -> List[ContractObligation]:
        if isinstance(node, Workflow):
            obligations.extend(self._workflow_obligations(node, workflows, source_paths))
            return obligations

        if isinstance(node, MacroRef):
            name = node.name
            source_paths[f"@{name}"] = self.macro_sources.get(name, "")
            obligations.append(
                ContractObligation(
                    id=f"macro:{name}:expansion",
                    kind="macro_expansion",
                    source=f"@{name}",
                    requirement="macro_expansion",
                    runtime_enforced=False,
                )
            )
            expansion = get_macro_expansion(name)
            if expansion:
                expanded_ast = CCLParser().parse(expansion)
                self._compile_node(expanded_ast, obligations, workflows, source_paths)
            return obligations

        if isinstance(node, Sequence):
            markers = self._child_markers(node.steps)
            obligations.append(
                ContractObligation(
                    id=f"sequence:{len(markers)}",
                    kind="ordered_children",
                    source="sequence",
                    requirement=" -> ".join(markers),
                    runtime_enforced=False,
                    metadata={"children": markers},
                )
            )
            for step in node.steps:
                self._compile_node(step, obligations, workflows, source_paths)
            return obligations

        if isinstance(node, Pipeline):
            markers = self._child_markers(node.steps)
            obligations.append(
                ContractObligation(
                    id=f"pipeline:{len(markers)}",
                    kind="ordered_children",
                    source="pipeline",
                    requirement=" &> ".join(markers),
                    runtime_enforced=False,
                    metadata={"children": markers},
                )
            )
            for step in node.steps:
                self._compile_node(step, obligations, workflows, source_paths)
            return obligations

        if isinstance(node, Parallel):
            markers = self._child_markers(node.branches)
            obligations.append(
                ContractObligation(
                    id=f"parallel:{len(markers)}",
                    kind="all_children",
                    source="parallel",
                    requirement=" && ".join(markers),
                    runtime_enforced=False,
                    metadata={"children": markers},
                )
            )
            for branch in node.branches:
                self._compile_node(branch, obligations, workflows, source_paths)
            return obligations

        if isinstance(node, Fusion):
            markers = self._child_markers([node.left, node.right])
            obligations.append(
                ContractObligation(
                    id=f"fusion:{':'.join(markers)}",
                    kind="all_children",
                    source="fusion",
                    requirement=" * ".join(markers),
                    runtime_enforced=False,
                    metadata={"children": markers},
                )
            )
            self._compile_node(node.left, obligations, workflows, source_paths)
            self._compile_node(node.right, obligations, workflows, source_paths)
            return obligations

        if isinstance(node, Oscillation):
            markers = self._child_markers([node.left, node.right])
            obligations.append(
                ContractObligation(
                    id=f"oscillation:{':'.join(markers)}",
                    kind="oscillation",
                    source="oscillation",
                    requirement=" ~ ".join(markers),
                    runtime_enforced=False,
                    metadata={"children": markers},
                )
            )
            self._compile_node(node.left, obligations, workflows, source_paths)
            self._compile_node(node.right, obligations, workflows, source_paths)
            return obligations

        if isinstance(node, Morphism):
            markers = self._child_markers([node.source, node.target])
            obligations.append(
                ContractObligation(
                    id=f"morphism:{node.direction}:{':'.join(markers)}",
                    kind="morphism",
                    source="morphism",
                    requirement=node.direction,
                    runtime_enforced=False,
                    metadata={"children": markers, "direction": node.direction},
                )
            )
            self._compile_node(node.source, obligations, workflows, source_paths)
            self._compile_node(node.target, obligations, workflows, source_paths)
            return obligations

        if isinstance(node, Adjunction):
            self._compile_node(node.left, obligations, workflows, source_paths)
            self._compile_node(node.right, obligations, workflows, source_paths)
            obligations.append(
                ContractObligation(
                    id="adjunction",
                    kind="adjunction",
                    source="adjunction",
                    requirement="adjunction",
                    runtime_enforced=False,
                )
            )
            return obligations

        if isinstance(node, ConvergenceLoop):
            self._compile_node(node.body, obligations, workflows, source_paths)
            obligations.append(
                ContractObligation(
                    id="convergence_loop",
                    kind="convergence_loop",
                    source="lim",
                    requirement="convergence_trace",
                    runtime_enforced=False,
                )
            )
            return obligations

        if isinstance(node, TaggedBlock):
            self._compile_node(node.body, obligations, workflows, source_paths)
            obligations.append(
                ContractObligation(
                    id=f"tagged:{node.tag}",
                    kind="tagged_block",
                    source=node.tag,
                    requirement=node.tag,
                    runtime_enforced=False,
                )
            )
            return obligations

        if isinstance(node, ForLoop):
            self._compile_node(node.body, obligations, workflows, source_paths)
            obligations.append(
                ContractObligation(
                    id="for_loop",
                    kind="for_loop",
                    source="F",
                    requirement="loop_container",
                    runtime_enforced=False,
                )
            )
            return obligations

        if isinstance(node, IfCondition):
            self._compile_node(node.then_branch, obligations, workflows, source_paths)
            if node.else_branch is not None:
                self._compile_node(node.else_branch, obligations, workflows, source_paths)
            obligations.append(
                ContractObligation(
                    id="if_condition",
                    kind="if_condition",
                    source="I",
                    requirement="conditional_branch",
                    runtime_enforced=False,
                )
            )
            return obligations

        if isinstance(node, WhileLoop):
            self._compile_node(node.body, obligations, workflows, source_paths)
            obligations.append(
                ContractObligation(
                    id="while_loop",
                    kind="while_loop",
                    source="W",
                    requirement="while_loop",
                    runtime_enforced=False,
                )
            )
            return obligations

        if isinstance(node, (PartialDiff, Integral, Summation)):
            body = getattr(node, "body", None)
            if body is not None:
                self._compile_node(body, obligations, workflows, source_paths)
            return obligations

        if isinstance(node, PreVerb):
            obligations.append(
                ContractObligation(
                    id=f"preverb:{node.id}",
                    kind="preverb",
                    source=node.id,
                    requirement=node.id,
                    runtime_enforced=False,
                )
            )
        return obligations

    def _workflow_obligations(
        self,
        node: Workflow,
        workflows: List[str],
        source_paths: Dict[str, str],
    ) -> List[ContractObligation]:
        obligations: List[ContractObligation] = []
        wf_id = node.id
        if wf_id not in workflows:
            workflows.append(wf_id)

        skill = self.skill_registry.get(wf_id)
        if skill and skill.source_path:
            source_paths[f"/{wf_id}"] = str(skill.source_path)

        contract = (
            skill.execution_contract if skill else DEFAULT_EXECUTION_CONTRACT
        )
        op_symbols = "".join(OPTYPE_TO_SYMBOL.get(op, "") for op in node.operators)
        depth = self._select_depth(op_symbols, contract.default_depth)

        for name in contract.required_outputs:
            obligations.append(
                ContractObligation(
                    id=f"workflow:{wf_id}:required:{name}",
                    kind="required_output",
                    source=f"/{wf_id}",
                    requirement=name,
                )
            )

        if skill:
            for phase in skill.get_execution_plan(depth=depth):
                obligations.append(
                    ContractObligation(
                        id=f"workflow:{wf_id}:phase:{phase.number}",
                        kind="phase",
                        source=f"/{wf_id}",
                        requirement=self._phase_requirement_name(phase.number),
                    )
                )
                if len(skill.phases) > 1 or "CHECKPOINT" in phase.raw_content.upper():
                    obligations.append(
                        ContractObligation(
                            id=f"workflow:{wf_id}:checkpoint:{phase.number}",
                            kind="checkpoint",
                            source=f"/{wf_id}",
                            requirement="checkpoints",
                        )
                    )
            for rule in skill.anti_skip_rules:
                obligations.append(
                    ContractObligation(
                        id=f"workflow:{wf_id}:anti_skip:{len(obligations)}",
                        kind="anti_skip",
                        source=f"/{wf_id}",
                        requirement=rule,
                        runtime_enforced=False,
                    )
                )

        operator_requirements = self._operator_requirements(skill, op_symbols)
        for req in operator_requirements:
            obligations.append(
                ContractObligation(
                    id=f"workflow:{wf_id}:operator:{req}",
                    kind="operator_requirement",
                    source=f"/{wf_id}",
                    requirement=req,
                )
            )
        return obligations

    def _operator_requirements(
        self,
        skill: Any,
        op_symbols: str,
    ) -> List[str]:
        requirements: List[str] = []
        if skill and isinstance(skill.raw_frontmatter.get("sel_enforcement"), dict):
            for op_symbol in op_symbols:
                data = skill.raw_frontmatter["sel_enforcement"].get(op_symbol, {})
                if isinstance(data, dict):
                    for item in data.get("minimum_requirements", []):
                        requirements.append(str(item))
        if not requirements:
            for op_symbol in op_symbols:
                requirements.extend(OPERATOR_REQUIREMENTS.get(op_symbol, []))
        return list(dict.fromkeys(requirements))

    def _macro_obligations(
        self, macro_name: str, contract: ExecutionContractDefinition
    ) -> List[ContractObligation]:
        obligations = [
            ContractObligation(
                id=f"macro:{macro_name}:expansion",
                kind="macro_expansion",
                source=f"@{macro_name}",
                requirement="macro_expansion",
                runtime_enforced=False,
            )
        ]
        for name in contract.required_outputs:
            obligations.append(
                ContractObligation(
                    id=f"macro:{macro_name}:required:{name}",
                    kind="macro_required_output",
                    source=f"@{macro_name}",
                    requirement=name,
                )
            )
        return obligations

    def _contract_from_dict(self, raw: Any) -> ExecutionContractDefinition:
        if not isinstance(raw, dict):
            return DEFAULT_EXECUTION_CONTRACT
        required_outputs = raw.get("required_outputs", [])
        if not isinstance(required_outputs, list):
            required_outputs = []
        return ExecutionContractDefinition(
            explicit_invocation=str(raw.get("explicit_invocation", "strict")),
            implicit_trigger=str(raw.get("implicit_trigger", "flexible")),
            fallback_behavior=str(raw.get("fallback_behavior", "declare_and_stop")),
            default_depth=str(raw.get("default_depth", "L2")),
            macro_expansion=str(raw.get("macro_expansion", "required")),
            required_outputs=[str(item) for item in required_outputs if str(item).strip()],
        )

    def _select_depth(self, op_symbols: str, fallback: str) -> str:
        if "+" in op_symbols:
            return "L3"
        if "-" in op_symbols:
            return "L1"
        return fallback or "L2"

    def _phase_requirement_name(self, number: Any) -> str:
        text = str(number).replace(".", "_")
        return f"phase_{text}"

    def _child_markers(self, children: Iterable[Any]) -> List[str]:
        markers = []
        for child in children:
            if isinstance(child, Workflow):
                markers.append(f"/{child.id}")
            elif isinstance(child, MacroRef):
                markers.append(f"@{child.name}")
            else:
                markers.append(type(child).__name__)
        return markers


class CCLContractValidator:
    """contract に対する lightweight fail-closed validator。"""

    def __init__(self, sel_validator: Optional[SELValidator] = None):
        self.sel_validator = sel_validator or SELValidator()

    def validate(
        self,
        contract: CompiledCCLContract,
        output: Any,
    ) -> CCLContractValidationResult:
        if contract.invocation_mode != "explicit" or not contract.strict:
            return CCLContractValidationResult(contract=contract, is_compliant=True)

        output_text = extract_text_payload(output)
        met: List[str] = []
        unmet: List[str] = []

        for obligation in contract.obligations:
            if not obligation.runtime_enforced:
                continue
            if self._check_obligation(obligation, output_text):
                met.append(obligation.requirement)
            else:
                unmet.append(obligation.requirement)

        return CCLContractValidationResult(
            contract=contract,
            is_compliant=len(unmet) == 0,
            met_requirements=met,
            unmet_requirements=unmet,
            blocking_reason="explicit CCL invocation requires full protocol conformance",
        )

    def _check_obligation(self, obligation: ContractObligation, output_text: str) -> bool:
        patterns = self._patterns_for_requirement(obligation.requirement)
        return any(
            self.sel_validator.check_requirement(pattern, output_text)
            for pattern in patterns
        )

    def _patterns_for_requirement(self, requirement: str) -> List[str]:
        normalized = requirement.strip().lower()
        if normalized in REQUIREMENT_PATTERNS:
            return REQUIREMENT_PATTERNS[normalized]
        if normalized.startswith("phase_"):
            return [normalized.replace("_", " "), normalized.replace("_", "-")]
        return [normalized, normalized.replace("_", " ")]


def compile_ccl_contract(ccl: str, invocation_mode: str = "explicit") -> CompiledCCLContract:
    return CCLContractCompiler().compile(ccl, invocation_mode=invocation_mode)


def validate_ccl_contract(
    contract: CompiledCCLContract,
    output: Any,
) -> CCLContractValidationResult:
    return CCLContractValidator().validate(contract, output)


def extract_text_payload(payload: Any) -> str:
    """任意オブジェクトから検証対象テキストを抽出する。"""
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload
    if isinstance(payload, (int, float, bool)):
        return str(payload)
    if isinstance(payload, dict):
        parts: List[str] = []
        for key in (
            "final_output",
            "output",
            "summary",
            "result",
            "message",
            "text",
            "status",
            "error",
        ):
            if key in payload:
                parts.append(extract_text_payload(payload[key]))
        if not parts:
            parts.append(json.dumps(payload, ensure_ascii=False))
        return "\n".join(part for part in parts if part)
    if isinstance(payload, (list, tuple, set)):
        return "\n".join(extract_text_payload(item) for item in payload)
    if hasattr(payload, "to_dict"):
        try:
            return extract_text_payload(payload.to_dict())
        except Exception:  # noqa: BLE001
            pass
    if hasattr(payload, "final_output"):
        return extract_text_payload(getattr(payload, "final_output"))
    return str(payload)
