# PROOF: [L2/インフラ] <- mekhane/ergasterion/typos/typos.py S2→プロンプト言語が必要→typos が担う
#!/usr/bin/env python3
"""
typos Parser
==================

Parse .typos files into structured data.

Usage:
    python typos.py parse <file>       # Parse and output JSON
    python typos.py validate <file>    # Validate syntax
    python typos.py expand <file>      # Expand to natural language prompt

Requirements:
    Python 3.10+
"""

import re
import json
import sys
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Any

try:
    import yaml as _yaml  # type: ignore
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

# Model archetype YAML path
_ARCHETYPE_PATH = (
    Path(__file__).parent.parent
    / "tekhne" / "references" / "typos-templates" / "model_archetypes.yaml"
)
_ARCHETYPE_CACHE: Any = None


# TYPOS v7.0: 24 description act directives (7 bases × 4 poles - Endpoint)
# Why (Reason), How (Resolution), How-much (Salience), Where (Context),
# Which (Order), When (Modality) — each with source/target × 2 poles = 4 acts
V7_DIRECTIVES = frozenset([
    # Why (Endpoint × Reason)
    "@context",   # src×arché: background
    "@intent",    # src×telos: intent
    "@rationale", # tgt×arché: rationale
    "@goal",      # tgt×telos: goal  (also legacy)
    # How (Endpoint × Resolution)
    "@detail",    # src×precise: detail
    "@summary",   # src×compressed: summary
    "@spec",      # tgt×precise: specification
    "@outline",   # tgt×compressed: outline
    # How-much (Endpoint × Salience)
    "@focus",     # src×focused: focus
    "@scope",     # src×diffuse: scope
    "@highlight", # tgt×focused: highlight
    "@breadth",   # tgt×diffuse: breadth
    # Where (Endpoint × Context)
    "@case",      # src×local: case/example
    "@principle", # src×global: principle
    "@step",      # tgt×local: step
    "@policy",    # tgt×global: policy
    # Which (Endpoint × Order)
    "@data",      # src×object: data
    "@schema",    # src×meta: schema
    "@content",   # tgt×object: content
    "@format",    # tgt×meta: format  (also legacy)
    # When (Endpoint × Modality)
    "@fact",      # src×actual: fact
    "@assume",    # src×possible: assumption
    "@assert",    # tgt×actual: assertion
    "@option",    # tgt×possible: option
])

# V7 directives that overlap with legacy fields (handled by legacy parsers first)
# @context → v7.1+: freed as v7.0 description act (Why族 Reason×arché×source)
#            Use @include for data injection (compiler instruction)
# @goal → parsed as text (legacy), also in V7_DIRECTIVES
# @format → parsed as text (legacy), also in V7_DIRECTIVES
V7_LEGACY_OVERLAP = frozenset(["@goal", "@format"])

# v7.1+: Depth Level System — which bases are active at each depth
# Maps depth level to the set of directive families available
# L0: Endpoint only (legacy: @role, @goal, @constraints, @format, @examples, @tools)
# L1: + Reason (Why), Resolution (How)
# L2: + Salience (How-much), Context (Where)
# L3: + Order (Which), Modality (When) — all 7 bases active
DEPTH_ACTIVE_DIRECTIVES: dict[str, frozenset[str]] = {
    "L0": frozenset(),  # No v7.0 directives — legacy only
    "L1": frozenset([
        # Why (Reason)
        "@context", "@intent", "@rationale", "@goal",
        # How (Resolution)
        "@detail", "@summary", "@spec", "@outline",
    ]),
    "L2": frozenset([
        # L1 directives +
        "@context", "@intent", "@rationale", "@goal",
        "@detail", "@summary", "@spec", "@outline",
        # How-much (Salience)
        "@focus", "@scope", "@highlight", "@breadth",
        # Where (Context)
        "@case", "@principle", "@step", "@policy",
    ]),
    "L3": V7_DIRECTIVES,  # All 24 directives active
}

# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: A single block in a typos file.
class PromptBlock:
    """A single block in a typos file."""

    block_type: str
    content: str | list | dict


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: A single rubric dimension for evaluation.
class RubricDimension:
    """A single rubric dimension for evaluation."""

    name: str
    description: str
    scale: str  # "1-5", "1-10", "binary", "percent"
    criteria: dict[str, str] = field(default_factory=dict)


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: Rubric block for self-evaluation.
class Rubric:
    """Rubric block for self-evaluation."""

    dimensions: list[RubricDimension] = field(default_factory=list)
    output_format: Optional[str] = None
    output_key: Optional[str] = None


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: Conditional block (@if/@else).
class Condition:
    """Conditional block (@if/@else)."""

    variable: str
    operator: str  # "==", "!=", ">", "<", ">=", "<="
    value: str
    if_content: dict = field(default_factory=dict)
    else_content: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "variable": self.variable,
            "operator": self.operator,
            "value": self.value,
            "if_content": self.if_content,
            "else_content": self.else_content,
        }


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: Activation metadata for glob/rule integration.
class Activation:
    """Activation metadata for glob/rule integration."""

    mode: str = "manual"  # "always_on", "manual", "glob", "model_decision"
    pattern: Optional[str] = None
    priority: int = 1
    rules: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "pattern": self.pattern,
            "priority": self.priority,
            "rules": self.rules,
        }


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: A single context resource reference.
class ContextItem:
    """A single context resource reference."""

    ref_type: str  # "file", "dir", "conv", "mcp", "ki"
    path: str
    priority: str = "MEDIUM"  # "HIGH", "MEDIUM", "LOW"
    section: Optional[str] = None
    filter: Optional[str] = None
    depth: Optional[int] = None
    tool_chain: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        d: dict[str, Any] = {"ref_type": self.ref_type, "path": self.path, "priority": self.priority}
        if self.section:
            d["section"] = self.section
        if self.filter:
            d["filter"] = self.filter
        if self.depth is not None:
            d["depth"] = self.depth
        if self.tool_chain:
            d["tool_chain"] = self.tool_chain
        return d


# v2.1 additions
# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: Reusable template fragment for composition.
class Mixin:
    """Reusable template fragment for composition."""

    name: str
    activation: Optional[Activation] = None
    blocks: dict[str, Any] = field(default_factory=dict)
    conditions: list[Condition] = field(default_factory=list)
    family_scope: dict[str, list[str]] = field(default_factory=dict)
    block_meta: dict[str, str] = field(default_factory=dict)
    block_relations: list[tuple[list[str], str, list[str]]] = field(default_factory=list)

    def to_v8(self, context: dict | None = None) -> str:
        """Convert Mixin AST to Týpos v8 format."""
        prompt = Prompt(
            name=self.name,
            activation=self.activation,
            blocks=dict(self.blocks),
            conditions=list(self.conditions),
        )
        return prompt.to_v8(context, is_mixin=True)# PURPOSE: Error when circular reference is detected in extends/mixin chain.
class CircularReferenceError(Exception):
    """Error when circular reference is detected in extends/mixin chain."""

    # PURPOSE: CircularReferenceError の初期化 — Error when referenced prompt/mixin is not found.
    def __init__(self, chain: list[str]):
        self.chain = chain
        super().__init__(f"Circular reference: {' → '.join(chain)}")

# PURPOSE: Error when referenced prompt/mixin is not found.

# PURPOSE: [L2-auto] ReferenceError のクラス定義
class ReferenceError(Exception):
    """Error when referenced prompt/mixin is not found."""

    # PURPOSE: ReferenceError の初期化 — Parsed typos document.
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Reference not found: {name}")

# PURPOSE: Parsed typos document.

# PURPOSE: [L2-auto] Prompt のクラス定義
@dataclass
class Prompt:
    """Parsed typos document."""

    name: str
    # v2 additions
    conditions: list[Condition] = field(default_factory=list)
    activation: Optional[Activation] = None
    # v2.1 additions (extends/mixin)
    extends: Optional[str] = None
    mixins: list[str] = field(default_factory=list)
    _resolved: bool = field(default=False, repr=False)
    # v7.0 additions — TYPOS 24 description acts
    blocks: dict[str, Any] = field(default_factory=dict)
    # v7.1 additions — Depth Level ("調号")
    depth: Optional[str] = None  # "L0", "L1", "L2", "L3" or None (= no restriction)
    # v7.1 additions — Layered architecture
    # L1: Family scope — maps family name to list of directives in that scope
    family_scope: dict[str, list[str]] = field(default_factory=dict)
    # L3: Block metadata — maps "directive.key" to value
    block_meta: dict[str, str] = field(default_factory=dict)
    # L4: Block relations — list of relation tuples (sources, operator, targets)
    block_relations: list[tuple[list[str], str, list[str]]] = field(default_factory=list)
    # v8.0 additions — syntax version and target
    syntax_version: str = "hybrid"  # "v7", "v8", or "hybrid"
    target: str = "markdown"  # "typos", "xml", "markdown", or "auto"



    # PURPOSE: Convert to dictionary.
    def to_dict(self) -> dict[str, Any]:
        """Convert Prompt AST to dictionary."""
        d: dict[str, Any] = {"name": self.name}
        if self.conditions:
            d["conditions"] = [c.to_dict() for c in self.conditions]
        if self.activation:
            d["activation"] = self.activation.to_dict()
        if self.extends:
            d["extends"] = self.extends
        if self.mixins:
            d["mixins"] = self.mixins
        if self.blocks:
            serialized_blocks = {}
            for k, v in self.blocks.items():
                if isinstance(v, list) and v and hasattr(v[0], 'to_dict'):
                    serialized_blocks[k] = [i.to_dict() for i in v]
                elif hasattr(v, 'to_dict'):
                    serialized_blocks[k] = v.to_dict()
                else:
                    serialized_blocks[k] = v
            d["blocks"] = serialized_blocks
        if self.depth:
            d["depth"] = self.depth
        if self.family_scope:
            d["family_scope"] = self.family_scope
        if self.block_meta:
            d["block_meta"] = self.block_meta
        if self.block_relations:
            d["block_relations"] = self.block_relations
        if self.syntax_version != "hybrid":
            d["syntax_version"] = self.syntax_version
        if self.target != "markdown":
            d["target"] = self.target

        return d

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_xml(self, context: dict | None = None) -> str:
        """Convert Prompt AST to XML tag format."""
        context = context or {}
        parts: list[str] = [f"<!-- prompt: {self.name} -->"]

        if self.conditions:
            for cond in self.conditions:
                if self._evaluate_condition(cond, context):
                    raw = cond.if_content.get("raw", "")
                else:
                    raw = cond.else_content.get("raw", "")
                if raw:
                    parts.append(f"<conditional>\n  {raw.strip()}\n</conditional>")

        if self.blocks:
            for directive, content in self.blocks.items():
                tag = directive.lstrip("@")
                if isinstance(content, list):
                    if content and isinstance(content[0], dict):
                        ex_parts = []
                        for ex in content:
                            ex_parts.append(f"  <example>")
                            if "input" in ex: ex_parts.append(f"    <input>{ex['input']}</input>")
                            if "output" in ex: ex_parts.append(f"    <output>{ex['output']}</output>")
                            ex_parts.append(f"  </example>")
                        parts.append(f"<{tag}s>\n" + "\n".join(ex_parts) + f"\n</{tag}s>")
                    elif content and hasattr(content[0], "ref_type"): 
                        ctx_items = []
                        for item in content:
                            item_content = self._resolve_context_item(item)
                            ctx_items.append(f'  <item type="{item.ref_type}" path="{item.path}">{item_content or ""}</item>')
                        parts.append(f"<{tag}>\n" + "\n".join(ctx_items) + f"\n</{tag}>")
                    else:
                        c_items = "\n".join(f"  <item>{c}</item>" for c in content)
                        parts.append(f"<{tag}s>\n{c_items}\n</{tag}s>")
                elif isinstance(content, dict):
                    t_items = "\n".join(f'  <item name="{name}">{desc}</item>' for name, desc in content.items())
                    parts.append(f"<{tag}s>\n{t_items}\n</{tag}s>")
                elif hasattr(content, "dimensions"): 
                    rub_parts = []
                    for dim in content.dimensions:
                        rub_parts.append(f'  <dimension name="{dim.name}" scale="{dim.scale}">')
                        rub_parts.append(f"    <description>{dim.description}</description>")
                        if dim.criteria:
                            for score, desc in dim.criteria.items():
                                rub_parts.append(f'    <criterion score="{score}">{desc}</criterion>')
                        rub_parts.append("  </dimension>")
                    parts.append(f"<{tag}>\n" + "\n".join(rub_parts) + f"\n</{tag}>")
                else:
                    parts.append(f"<{tag}>\n  {str(content).strip()}\n</{tag}>")

        return "\n\n".join(parts)


    def to_v8(self, context: dict | None = None, is_mixin: bool = False) -> str:
        """Convert Prompt AST to Týpos v8 format."""
        context = context or {}
        parts: list[str] = []

        header_type = "#mixin" if is_mixin else "#prompt"
        parts.append(f"{header_type} {self.name}")
        parts.append("#syntax: v8")

        if self.conditions:
            for cond in self.conditions:
                if self._evaluate_condition(cond, context):
                    raw = cond.if_content.get("raw", "")
                else:
                    raw = cond.else_content.get("raw", "")
                if raw:
                    parts.append(f"\n<:conditional:\n  {raw.strip()}\n:>")

        if self.blocks:
            for directive, content in self.blocks.items():
                tag = directive.lstrip("@")
                if isinstance(content, list):
                    if content and isinstance(content[0], dict):
                        parts.append(f"\n<:{tag}s:")
                        for ex in content:
                            parts.append("  <:example:")
                            if "input" in ex: parts.append(f"    <:input:\n      {ex['input']}\n    :>")
                            if "output" in ex: parts.append(f"    <:output:\n      {ex['output']}\n    :>")
                            parts.append("  :>")
                        parts.append(":>")
                    elif content and hasattr(content[0], "ref_type"): 
                        ctx_lines = []
                        for item in content:
                            ctx_lines.append(f"  - [{item.ref_type}] {item.path} (priority: {item.priority})")
                        parts.append(f"\n<:{tag}:\n" + "\n".join(ctx_lines) + "\n:>")
                    else:
                        c_lines = "\n".join(f"  - {c}" for c in content)
                        parts.append(f"\n<:{tag}:\n{c_lines}\n:>")
                elif isinstance(content, dict):
                    t_lines = "\n".join(f"  - {name}: {desc}" for name, desc in content.items())
                    parts.append(f"\n<:{tag}:\n{t_lines}\n:>")
                elif hasattr(content, "dimensions"): 
                    rub_lines = []
                    for dim in content.dimensions:
                        rub_lines.append(f"  - {dim.name}:")
                        rub_lines.append(f"      description: {dim.description}")
                        rub_lines.append(f"      scale: {dim.scale}")
                        if dim.criteria:
                            rub_lines.append("      criteria:")
                            for score, desc in dim.criteria.items():
                                rub_lines.append(f"        {score}: {desc}")
                    parts.append(f"\n<:{tag}:\n" + "\n".join(rub_lines) + "\n:>")
                else:
                    stripped = str(content).strip()
                    if "\n" not in stripped and len(stripped) < 80:
                        parts.append(f"\n<:{tag}: {stripped} :>")
                    else:
                        parts.append(f"\n<:{tag}:\n  {stripped}\n:>")

        return "\n".join(parts)

    def expand(self) -> str:
        """Expand to natural language prompt."""
        parts = []

        if self.blocks:
            for directive, content in self.blocks.items():
                label = directive.lstrip('@').replace('_', ' ').title()
                if isinstance(content, list):
                    if content and isinstance(content[0], dict):
                        parts.append(f"\n\n{label}:")
                        for ex in content:
                            parts.append(f"- Input: {ex.get('input', '')}")
                            parts.append(f"  Output: {ex.get('output', '')}")
                    elif content and hasattr(content[0], "ref_type"):
                        parts.append(f"\n\n{label}:")
                        for item in content:
                            parts.append(f"- [{item.ref_type}] {item.path} (priority: {item.priority})")
                    else:
                        parts.append(f"\n\n{label}:")
                        for c in content:
                            parts.append(f"- {c}")
                elif isinstance(content, dict):
                    parts.append(f"\n\n{label}:")
                    for name, desc in content.items():
                        parts.append(f"- {name}: {desc}")
                elif hasattr(content, "dimensions"):
                    parts.append(f"\n\n{label}:")
                    for dim in content.dimensions:
                        parts.append(f"- {dim.name}: {dim.description} (scale: {dim.scale})")
                        if dim.criteria:
                            for score, desc in dim.criteria.items():
                                parts.append(f"    {score}: {desc}")
                else:
                    parts.append(f"\n\n{label}:\n{str(content).strip()}")

        if self.conditions:
            parts.append("\n\nConditional Rules:")
            for cond in self.conditions:
                parts.append(f"- When {cond.variable} {cond.operator} {cond.value}:")
                if cond.if_content.get("raw"):
                    parts.append(f"    {cond.if_content['raw'][:100]}...")

        return "\n".join(parts).strip()

    def _format_block_markdown(self, label: str, content: Any, inline_title: bool = False, extra_meta: str = "") -> list[str]:
        """Helper to format a dynamic block value as markdown sections."""
        out = []
        if isinstance(content, list):
            if content and isinstance(content[0], dict):
                out.append(f"\n### {label}{extra_meta}")
                for i, ex in enumerate(content, 1):
                    out.append(f"**Example {i}**")
                    if ex.get("input"): out.append(f"**Input**: {ex['input']}")
                    if ex.get("output"): out.append(f"**Output**: {ex['output']}")
            elif content and hasattr(content[0], "ref_type"):
                out.append(f"\n### {label}{extra_meta}")
                for item in content:
                    content_item = self._resolve_context_item(item)
                    out.append(f"\n#### [{item.ref_type}] {item.path}\n*Priority: {item.priority}*")
                    if content_item: out.append(f"```\n{content_item}\n```")
            else:
                out.append(f"\n### {label}{extra_meta}")
                for c in content: out.append(f"- {c}")
        elif isinstance(content, dict):
            out.append(f"\n### {label}{extra_meta}")
            for name, desc in content.items():
                out.append(f"- **{name}**: {desc}")
        elif hasattr(content, "dimensions"):
            out.append(f"\n### {label}{extra_meta}")
            for dim in content.dimensions:
                out.append(f"- **{dim.name}**: {dim.description} (scale: {dim.scale})")
                if dim.criteria:
                    for score, desc in dim.criteria.items():
                        out.append(f"    - {score}: {desc}")
        else:
            if inline_title:
                out.append(f"**{label}{extra_meta}**: {str(content).strip()}")
            else:
                out.append(f"\n## {label}{extra_meta}\n{str(content).strip()}")
        return out

    def compile(self, context: Optional[dict] = None, format: Optional[str] = None,
                quality: bool = False, model: Optional[str] = None) -> str:
        """
        Compile AST to system prompt string.

        Args:
            context: Variables for @if evaluation (e.g., {"env": "prod"})
            format: Output format ("markdown", "xml", "plain")
            quality: If True, append quality score block at the end
            model: Target model family ("gemini", "claude", "openai", or None)
                   When set, applies model-specific archetype optimizations.

        Returns:
            Compiled system prompt string
        """
        context = context or {}
        if model:
            context["model"] = model
            
        # Determine target format
        # Hierarchy: format param > Prompt.target field
        actual_format = format if format else self.target

        if actual_format == "xml" or (actual_format == "auto" and model and "claude" in model.lower()):
            return self.to_xml(context)
        elif actual_format == "typos" or actual_format == "auto":
            return self.to_v8(context)

        # "markdown" formatting logic (fallback to existing v7 generation)
        sections = []

        # Header
        sections.append(f"# {self.name}")

        # v7.0/v7.1: Description act blocks
        if self.blocks:
            if self.family_scope:
                # v7.1 View Mode: Group by family scope
                rendered_directives = set()
                for family, directives in self.family_scope.items():
                    family_label = family.title()
                    sections.append(f"\n## {family_label}")
                    for directive in directives:
                        if directive in self.blocks:
                            label = directive.lstrip('@').replace('_', ' ').title()
                            content = self.blocks[directive]
                            # Integrate L3 metadata inline
                            meta_parts = []
                            for mk, mv in self.block_meta.items():
                                d_name = directive.lstrip('@')
                                if mk.startswith(d_name + "."):
                                    key = mk[len(d_name) + 1:]
                                    meta_parts.append(f"{key}: {mv}")
                            meta_str = f" [{', '.join(meta_parts)}]" if meta_parts else ""
                            # Check L4 relations
                            rel_str = ""
                            for sources, op, targets in self.block_relations:
                                d_name = directive.lstrip('@')
                                if d_name in sources:
                                    rel_str = f" → {', '.join(targets)}"
                            
                            extra_meta = f"{meta_str}{rel_str}"
                            # Render block
                            sections.extend(self._format_block_markdown(label, content, inline_title=True, extra_meta=extra_meta))
                            rendered_directives.add(directive)
                # Render any blocks not in a family scope
                for directive, content in self.blocks.items():
                    if directive not in rendered_directives:
                        label = directive.lstrip('@').replace('_', ' ').title()
                        sections.extend(self._format_block_markdown(label, content))
            else:
                # v7.0 flat mode (backward compatible)
                for directive, content in self.blocks.items():
                    label = directive.lstrip('@').replace('_', ' ').title()
                    sections.extend(self._format_block_markdown(label, content))

        # Conditions (v2 - evaluated)
        if self.conditions:
            for cond in self.conditions:
                if self._evaluate_condition(cond, context):
                    # Use if_content
                    if cond.if_content.get("raw"):
                        sections.append(
                            f"\n## Conditional (when {cond.variable}={cond.value})"
                        )
                        sections.append(cond.if_content["raw"])
                else:
                    # Use else_content
                    if cond.else_content.get("raw"):
                        sections.append(f"\n## Conditional (else)")
                        sections.append(cond.else_content["raw"])

        # Quality score (opt-in)
        if quality:
            score_info = self.quality_score()
            if score_info:
                sections.append(f"\n<!-- Quality: {score_info['total']}/100 -->")

        result = "\n".join(sections)

        # Apply model-specific archetype post-processing
        if model:
            result = self._apply_archetype(result, model)

        return result

    # PURPOSE: Calculate prompt quality score.
    def quality_score(self) -> Optional[dict]:
        """Calculate prompt quality score using prompt_quality_scorer.

        Lazy-imports the scorer to avoid circular dependencies.

        Returns:
            dict with 'total', 'grade', 'dimensions' or None if scorer unavailable
        """
        try:
            from mekhane.ergasterion.tekhne.prompt_quality_scorer import score_prompt_text
            report = score_prompt_text(self.expand(), name=self.name)
            return {
                "total": report.total,
                "grade": report.grade,
                "structure": report.structure.normalized,
                "safety": report.safety.normalized,
                "completeness": report.completeness.normalized,
                "archetype_fit": report.archetype_fit.normalized,
            }
        except ImportError:
            return None
        except Exception:  # noqa: BLE001
            return None

    # PURPOSE: Check depth level compliance for v7.0 directives.
    def depth_warnings(self) -> list[str]:
        """Check if v7.0 directives are within the active depth level.

        Returns list of warning messages for directives used outside
        their active depth level. Empty list = no violations.
        """
        depth = self.depth
        if not depth or not self.blocks:
            return []

        active = DEPTH_ACTIVE_DIRECTIVES.get(depth, V7_DIRECTIVES)
        warnings = []
        for directive in self.blocks:
            if directive not in active:
                # Find what depth level this directive becomes active
                needed = "L3"
                for level in ["L1", "L2", "L3"]:
                    if directive in DEPTH_ACTIVE_DIRECTIVES[level]:
                        needed = level
                        break
                warnings.append(
                    f"⚠️ {directive} requires depth {needed}, "
                    f"but @depth is {depth}"
                )
        return warnings

    # PURPOSE: Async compile AST to system prompt string.
    async def compile_async(
        self, context: Optional[dict[str, Any]] = None, mcp_handler=None, format: str = "markdown"
    ) -> str:
        """
        Async compile AST to system prompt string.

        Args:
            context: Variables for @if evaluation
            mcp_handler: Async callback for MCP resolution
            format: Output format
        """
        context = context or {}
        sections = []

        # Header
        sections.append(f"# {self.name}")

        # v7.0/v7.1: Description act blocks
        if self.blocks:
            rendered_directives = set()
            if self.family_scope:
                for family, directives in self.family_scope.items():
                    family_label = family.title()
                    sections.append(f"\n## {family_label}")
                    for directive in directives:
                        if directive in self.blocks:
                            content = self.blocks[directive]
                            label = directive.lstrip('@').replace('_', ' ').title()
                            
                            meta_parts = []
                            for mk, mv in self.block_meta.items():
                                d_name = directive.lstrip('@')
                                if mk.startswith(d_name + "."):
                                    key = mk[len(d_name) + 1:]
                                    meta_parts.append(f"{key}: {mv}")
                            meta_str = f" [{', '.join(meta_parts)}]" if meta_parts else ""
                            rel_str = ""
                            for sources, op, targets in self.block_relations:
                                d_name = directive.lstrip('@')
                                if d_name in sources:
                                    rel_str = f" → {', '.join(targets)}"
                            extra_meta = f"{meta_str}{rel_str}"

                            # Handle async context resolution
                            if isinstance(content, list) and content and hasattr(content[0], "ref_type"):
                                sections.append(f"\n### {label}{extra_meta}")
                                for item in content:
                                    if item.ref_type == "mcp":
                                        content_item = await self._resolve_context_item_async(item, mcp_handler)
                                    else:
                                        content_item = self._resolve_context_item(item)
                                    sections.append(f"\n#### [{item.ref_type}] {item.path}\n*Priority: {item.priority}*")
                                    if content_item:
                                        sections.append(f"```\n{content_item}\n```")
                                    else:
                                        sections.append("<!-- Resource not available -->")
                            else:
                                sections.extend(self._format_block_markdown(label, content, inline_title=True, extra_meta=extra_meta))
                            rendered_directives.add(directive)
            
            # Render blocks not yet rendered
            for directive, content in self.blocks.items():
                if directive not in rendered_directives:
                    label = directive.lstrip('@').replace('_', ' ').title()
                    if isinstance(content, list) and content and hasattr(content[0], "ref_type"):
                        sections.append(f"\n## {label}")
                        for item in content:
                            if item.ref_type == "mcp":
                                content_item = await self._resolve_context_item_async(item, mcp_handler)
                            else:
                                content_item = self._resolve_context_item(item)
                            sections.append(f"\n### [{item.ref_type}] {item.path}\n*Priority: {item.priority}*")
                            if content_item:
                                sections.append(f"```\n{content_item}\n```")
                            else:
                                sections.append("<!-- Resource not available -->")
                    else:
                        sections.extend(self._format_block_markdown(label, content))

        # Conditions (v2 - evaluated)
        if self.conditions:
            for cond in self.conditions:
                if self._evaluate_condition(cond, context):
                    if cond.if_content.get("raw"):
                        sections.append(
                            f"\n## Conditional (when {cond.variable}={cond.value})"
                        )
                        sections.append(cond.if_content["raw"])
                else:
                    if cond.else_content.get("raw"):
                        sections.append(f"\n## Conditional (else)")
                        sections.append(cond.else_content["raw"])

        return "\n".join(sections)

    # PURPOSE: Resolve a context item asynchronously.
    async def _resolve_context_item_async(
        self, item: "ContextItem", mcp_handler
    ) -> Optional[str]:
        """Resolve a context item asynchronously."""
        if item.ref_type == "mcp":
            if not mcp_handler:
                return f"Error: No MCP handler provided for {item.path}"

            try:
                # Parse path: "server.tool" or "server.tool(args)"
                # But here path is already "gnosis" (server) if tool_chain is set?
                # Parser sets tool_chain="mcp:gnosis.tool('search')"

                target = item.tool_chain if item.tool_chain else item.path

                # Extract server, tool, args from target string
                # Expected format: "mcp:server.tool('args')" or "server.tool"

                # Clean up prefix
                if target.startswith("mcp:"):
                    target = target[4:]

                server_name = target.split(".")[0]

                # Check for .tool("args") pattern
                tool_match = re.search(r'\.tool\((["\']?)(.+?)\1\)', target)
                if tool_match:
                    tool_name = tool_match.group(2)
                    # We might need to parse args more complexly later
                    args = (
                        {}
                    )  # Arguments usually passed via .with() or similar in Týpos v2 spec?
                    # The spec says: mcp:gnosis.tool("search")
                    # So tool name is passed as argument to .tool()?
                    # Or is it mcp:gnosis.search?

                    # Based on parser:
                    # if ref_type == "mcp" and ".tool(" in path:
                    #    tool_chain = path

                    # So we have "gnosis.tool('search')"
                    return await mcp_handler(server_name, tool_name, {})
                else:
                    return f"Error resolving MCP URI: {target}"

            except Exception as e:  # noqa: BLE001
                return f"MCP Error: {e}"

        return self._resolve_context_item(item)

    # PURPOSE: Evaluate a condition against the context.
    def _evaluate_condition(self, cond: "Condition", context: dict) -> bool:
        """Evaluate a condition against the context."""
        var_value = context.get(cond.variable)
        if var_value is None:
            return False

        if cond.operator == "==":
            return str(var_value) == str(cond.value)
        elif cond.operator == "!=":
            return str(var_value) != str(cond.value)
        elif cond.operator == ">":
            return float(var_value) > float(cond.value)
        elif cond.operator == "<":
            return float(var_value) < float(cond.value)
        elif cond.operator == ">=":
            return float(var_value) >= float(cond.value)
        elif cond.operator == "<=":
            return float(var_value) <= float(cond.value)

        return False

    # PURPOSE: Load model archetype definitions from YAML.
    @staticmethod
    def _load_archetype(model_family: str) -> dict | None:
        """Load model archetype definitions from YAML.

        Returns archetype dict for the given model family, or None.
        """
        global _ARCHETYPE_CACHE
        if _ARCHETYPE_CACHE is None:
            if not _YAML_AVAILABLE:
                return None
            if not _ARCHETYPE_PATH.exists():
                return None
            try:
                _ARCHETYPE_CACHE = _yaml.safe_load(
                    _ARCHETYPE_PATH.read_text(encoding="utf-8")
                )
            except Exception:  # noqa: BLE001
                return None

        archetypes = (_ARCHETYPE_CACHE or {}).get("archetypes", {})
        return archetypes.get(model_family)

    # PURPOSE: Detect model family from a model name string.
    @staticmethod
    def _detect_model(model_name: str) -> str | None:
        """Detect model family from a model name string.

        Args:
            model_name: Model identifier (e.g. "gemini-3-flash-preview", "claude-opus-4-20250514")

        Returns:
            Model family key ("gemini", "claude", "openai") or None.
        """
        global _ARCHETYPE_CACHE
        if _ARCHETYPE_CACHE is None:
            if not _YAML_AVAILABLE or not _ARCHETYPE_PATH.exists():
                return None
            try:
                _ARCHETYPE_CACHE = _yaml.safe_load(
                    _ARCHETYPE_PATH.read_text(encoding="utf-8")
                )
            except Exception:  # noqa: BLE001
                return None

        detection = (_ARCHETYPE_CACHE or {}).get("detection", {})
        lower = model_name.lower()
        for family, keywords in detection.items():
            for kw in keywords:
                if kw in lower:
                    return family
        return None

    # PURPOSE: Apply model-specific archetype post-processing.
    def _apply_archetype(self, compiled: str, model: str) -> str:
        """Apply model-specific archetype optimizations to compiled output.

        Args:
            compiled: The compiled prompt string.
            model: Model family key ("gemini", "claude", "openai").
                   If not a known family, attempts auto-detection.

        Returns:
            Post-processed prompt string.
        """
        # Auto-detect if needed
        arch = self._load_archetype(model)
        if arch is None:
            detected = self._detect_model(model)
            if detected:
                arch = self._load_archetype(detected)
        if arch is None:
            return compiled  # No archetype found, return as-is

        result = compiled
        role_fmt = arch.get("role_format", "prose")
        constraint_style = arch.get("constraint_style", "")
        instruction_fmt = arch.get("instruction_format", "")
        xml_tags = arch.get("xml_tags", {})

        # 1. Role format: wrap in XML tags for xml-style models
        if role_fmt == "xml" and xml_tags.get("role"):
            tag = xml_tags["role"]
            result = re.sub(
                r"(## Role\n)(.*?)(?=\n## |\Z)",
                lambda m: f"## Role\n<{tag}>\n{m.group(2).strip()}\n</{tag}>",
                result,
                flags=re.DOTALL,
            )

        # 2. Constraint style transformations
        if constraint_style == "contract":
            # Claude contract-style: convert "- X" to "- MUST: X" / "- MUST NOT: X"
            result = self._apply_contract_constraints(result)
        elif constraint_style == "explicit":
            # OpenAI explicit-style: number constraints and add enforcement note
            result = self._apply_explicit_constraints(result)

        # 3. Instruction format: wrap constraints section in XML tags
        if instruction_fmt == "xml" and xml_tags.get("instructions"):
            tag = xml_tags["instructions"]
            result = re.sub(
                r"(## Constraints\n)(.*?)(?=\n## |\Z)",
                lambda m: f"## Constraints\n<{tag}>\n{m.group(2).strip()}\n</{tag}>",
                result,
                flags=re.DOTALL,
            )

        # 4. Instruction format: JSON schema hint for openai-style
        if instruction_fmt == "json":
            result = self._apply_json_format_hint(result)

        # 5. Thinking hint: append if present
        hint = arch.get("thinking_hint")
        if hint:
            result += f"\n\n<!-- Thinking hint: {hint} -->"

        # 6. Structure: task_input_output テンプレート (Gemini 3 最適化)
        # KI: Gemini 3 は <task>/<output> タグで入出力境界を明確化すると精度向上
        structure = arch.get("structure", "sections")
        if structure == "task_input_output" and xml_tags:
            task_tag = xml_tags.get("task", "task")
            output_tag = xml_tags.get("output", "output")

            # Steps セクションを <task> でラップ
            result = re.sub(
                r"(## (?:Steps|Procedure|手順)\n)(.*?)(?=\n## |\Z)",
                lambda m: (
                    f"## Steps\n<{task_tag}>\n"
                    f"{m.group(2).strip()}\n"
                    f"</{task_tag}>"
                ),
                result,
                flags=re.DOTALL,
            )

            # Output Format セクションを <output> でラップ
            result = re.sub(
                r"(## (?:Output Format|出力形式|Format)\n)(.*?)(?=\n## |\Z)",
                lambda m: (
                    f"## Output Format\n<{output_tag}>\n"
                    f"{m.group(2).strip()}\n"
                    f"</{output_tag}>"
                ),
                result,
                flags=re.DOTALL,
            )

        return result

    # PURPOSE: Convert constraints to contract-style (MUST/MUST NOT) for Claude.
    @staticmethod
    def _apply_contract_constraints(compiled: str) -> str:
        """Convert constraint list items to contract obligations.

        Detects negation patterns and converts to MUST NOT, otherwise MUST.
        """

        def _to_contract(match: re.Match) -> str:
            line = match.group(1).strip()
            # Detect negation patterns
            negation_patterns = [
                "not ", "never ", "don't ", "do not ", "avoid ",
                "禁止", "しない", "してはいけない", "するな",
            ]
            is_negative = any(p in line.lower() for p in negation_patterns)
            prefix = "MUST NOT" if is_negative else "MUST"
            return f"- **{prefix}**: {line}"

        return re.sub(
            r"^- (.+)$",
            _to_contract,
            compiled,
            flags=re.MULTILINE,
        )

    # PURPOSE: Convert constraints to explicit numbered format for OpenAI.
    @staticmethod
    def _apply_explicit_constraints(compiled: str) -> str:
        """Number constraint items and add enforcement note."""

        def _replace_constraints_section(match: re.Match) -> str:
            header = match.group(1)
            body = match.group(2)
            lines = [l for l in body.strip().split("\n") if l.strip().startswith("- ")]
            numbered = []
            for i, line in enumerate(lines, 1):
                content = line.lstrip("- ").strip()
                numbered.append(f"{i}. {content}")
            numbered.append("")
            numbered.append("> ⚠️ Strictly follow ALL constraints above. "
                           "Violations will be flagged.")
            return header + "\n".join(numbered)

        return re.sub(
            r"(## Constraints\n)(.*?)(?=\n## |\Z)",
            _replace_constraints_section,
            compiled,
            flags=re.DOTALL,
        )

    # PURPOSE: Add JSON format hint for OpenAI-style prompts.
    @staticmethod
    def _apply_json_format_hint(compiled: str) -> str:
        """Add JSON format guidance note after Output Format section, or at end."""
        json_hint = ("\n## Response Format\n"
                     "Respond in valid JSON. Follow any provided JSON schema exactly.\n"
                     "Do not include markdown code fences around the JSON output.")
        # Insert after Output Format if it exists, otherwise append
        if "## Output Format" in compiled:
            compiled = compiled.replace(
                "## Output Format",
                "## Output Format\n> Note: Output must be valid JSON.",
                1,
            )
            return compiled
        else:
            return compiled + json_hint

    # PURPOSE: Resolve a context item to its content string.
    def _resolve_context_item(self, item: "ContextItem") -> Optional[str]:
        """Resolve a context item to its content string."""

        if item.ref_type == "file":
            # Read actual file
            path = Path(item.path)
            if path.exists():
                try:
                    content = path.read_text(encoding="utf-8")
                    # Truncate if too long (based on priority)
                    max_lines = {"HIGH": 200, "MEDIUM": 100, "LOW": 50}.get(
                        item.priority, 100
                    )
                    lines = content.split("\n")
                    if len(lines) > max_lines:
                        content = (
                            "\n".join(lines[:max_lines])
                            + f"\n... ({len(lines) - max_lines} more lines)"
                        )
                    return content
                except Exception as e:  # noqa: BLE001
                    return f"Error reading file: {e}"
            else:
                return f"File not found: {item.path}"

        elif item.ref_type == "dir":
            # List files in directory
            path = Path(item.path)
            if path.exists() and path.is_dir():
                try:
                    pattern = item.filter or "*"
                    max_depth = item.depth or 1

                    # Use glob to find files
                    if max_depth == 1:
                        files = list(path.glob(pattern))
                    else:
                        files = list(path.glob(f"**/{pattern}"))

                    # Limit results
                    files = files[:20]
                    return "\n".join(str(f.relative_to(path)) for f in files)
                except Exception as e:  # noqa: BLE001
                    return f"Error listing directory: {e}"
            else:
                return f"Directory not found: {item.path}"

        elif item.ref_type == "conv":
            # Placeholder for conversation reference
            return f"[Conversation: {item.path}]"

        elif item.ref_type == "mcp":
            # Placeholder for MCP server reference
            return f"[MCP Server: {item.path}]"
# PURPOSE: Result of parsing a typos file with multiple definitions.

        elif item.ref_type == "ki":
            # Placeholder for Knowledge Item
            return f"[Knowledge Item: {item.path}]"

        return None


# v2.1 additions
# PURPOSE: Result of parsing a typos file with multiple definitions
@dataclass
class ParseResult:
    """Result of parsing a typos file with multiple definitions."""

    prompts: dict[str, Prompt] = field(default_factory=dict)  # name -> Prompt
    mixins: dict[str, Mixin] = field(default_factory=dict)  # name -> Mixin

    # PURPOSE: Get a prompt by name.
    def get_prompt(self, name: str) -> Optional[Prompt]:
        """Get a prompt by name."""
# PURPOSE: Error during parsing.
        return self.prompts.get(name)

    # PURPOSE: Get a mixin by name.
    def get_mixin(self, name: str) -> Optional[Mixin]:
        """Get a mixin by name."""
        return self.mixins.get(name)

    # PURPOSE: Get a prompt or mixin by name.
# PURPOSE: Parser for typos files.
    def get(self, name: str) -> Optional[Prompt | Mixin]:
        """Get a prompt or mixin by name."""
        return self.prompts.get(name) or self.mixins.get(name)


# PURPOSE: Error during parsing
class ParseError(Exception):
    """Error during parsing."""

    # PURPOSE: ParseError の初期化 — Parser for typos files.
    def __init__(self, message: str, line: int = 0):
        self.line = line
        super().__init__(f"Line {line}: {message}" if line else message)


# PURPOSE: Parser for typos files
class PromptLangParser:
    """Parser for typos files."""

    # Regex patterns
    HEADER_PATTERN = re.compile(r"^#prompt\s+([a-zA-Z_][a-zA-Z0-9_-]*)$")
    SYNTAX_PATTERN = re.compile(r"^#syntax:\s*(v7|v8|hybrid)$")  # v8.0
    TARGET_PATTERN = re.compile(r"^#target:\s*(typos|xml|markdown|auto)$")  # v8.0
    DEPTH_PATTERN = re.compile(r"^#depth:\s*(L[0-3])$")  # v7.1 / v8.0
    MIXIN_HEADER_PATTERN = re.compile(r"^#mixin\s+([a-zA-Z_][a-zA-Z0-9_-]*)$")  # v2.1
    BLOCK_PATTERN = re.compile(r"^(@\w+):$")
    LIST_ITEM_PATTERN = re.compile(r"^  - (.+)$")
    TOOL_ITEM_PATTERN = re.compile(r"^  - ([a-z_][a-z0-9_-]*): (.+)$")
    EXAMPLE_INPUT_PATTERN = re.compile(r"^  - input: (.+)$")
    EXAMPLE_OUTPUT_PATTERN = re.compile(r"^  +output: (.+)$")  # Allow flexible indent
    FENCED_START_PATTERN = re.compile(r"^  ```(\w*)$")
    FENCED_END_PATTERN = re.compile(r"^  ```\s*$")  # Allow trailing whitespace
    INDENTED_LINE_PATTERN = re.compile(r"^  (.+)$")
    # v2.1 patterns for extends/mixin
    EXTENDS_INLINE_PATTERN = re.compile(r"^@extends:\s*(.+)$")
    MIXIN_REF_PATTERN = re.compile(r"^@mixin:\s*\[([^\]]+)\]$")
    # v8.0 patterns — <:directive: ... :>
    V8_INLINE_PATTERN = re.compile(r"^<:(\w+):\s*(.*?)\s*:>$")  # single-line
    V8_BLOCK_OPEN_PATTERN = re.compile(r"^<:(\w+):$")  # multi-line open
    V8_BLOCK_CLOSE_PATTERN = re.compile(r"^:>$")  # multi-line close
    V8_NAMED_CLOSE_PATTERN = re.compile(r"^/(\w+):>$")  # named close: /name:>
    V8_IF_PATTERN = re.compile(r"^<:if\s+(.+):$")  # <:if condition:

    # PURPOSE: PromptLangParser の初期化 — Parse the content and return a Prompt object.
    def __init__(self, content: str):
        self.content = content
        self.lines = content.split("\n")
        self.pos = 0
        self.prompt: Prompt = Prompt(name="unnamed")
        self._current_family: Optional[str] = None
        self._layer_mode: str = "directives"

    # PURPOSE: Parse the content and return a Prompt object.
    def parse(self) -> Prompt:
        """Parse the content and return a Prompt object."""
        self._skip_empty_lines()
        self._parse_header()

        # v8.0: Branch on syntax version — use AST pipeline
        if self.prompt.syntax_version == "v8":
            try:
                from mekhane.ergasterion.typos.v8_tokenizer import V8Tokenizer
                from mekhane.ergasterion.typos.v8_compiler import V8Compiler
            except ImportError:
                from .v8_tokenizer import V8Tokenizer  # type: ignore
                from .v8_compiler import V8Compiler  # type: ignore
            doc = V8Tokenizer(self.content).tokenize()
            return V8Compiler(doc, self.prompt).compile()

        # v8.0 hybrid: detect <: in content for auto-hybrid
        is_hybrid = self.prompt.syntax_version == "hybrid"
        if not is_hybrid:
            # Auto-detect: if any line starts with <: it's hybrid
            for i in range(self.pos, len(self.lines)):
                if self.lines[i].strip().startswith("<:"):
                    is_hybrid = True
                    self.prompt.syntax_version = "hybrid"
                    break

        # v7.1: Track current family scope and layer mode
        self._current_family: Optional[str] = None
        self._layer_mode: str = "directives"  # "directives" | "meta_relations"

        while self.pos < len(self.lines):
            self._skip_empty_lines()
            if self.pos >= len(self.lines):
                break

            line = self._current_line()

            # v7.1: Layer boundary (---) switches to meta/relations mode
            if line.strip() == "---":
                self._layer_mode = "meta_relations"
                self.pos += 1
                continue

            # v7.1: Family scope (## Family)
            if line.startswith("## ") and self._layer_mode == "directives":
                family = line[3:].strip().lower()
                self._current_family = family
                if family not in self.prompt.family_scope:
                    self.prompt.family_scope[family] = []
                self.pos += 1
                continue

            # v7.1: Meta/relations mode parsing
            if self._layer_mode == "meta_relations":
                self._parse_meta_or_relation(line)
                self.pos += 1
                continue

            # v8.0 hybrid: try v8 block before v7
            if is_hybrid and self._try_parse_v8_block():
                continue

            # Normal directive parsing
            self._parse_block()

        return self.prompt

    # PURPOSE: [L2-auto] _parse_meta_or_relation の関数定義
    def _parse_meta_or_relation(self, line: str):
        """Parse a line in meta/relations mode (after ---)."""
        line = line.strip()
        if not line:
            return

        # L4: Relation — pattern: "a -> b" or "a, b -> c"
        if " -> " in line:
            parts = line.split(" -> ", 1)
            sources = [s.strip() for s in parts[0].split(",")]
            targets = [t.strip() for t in parts[1].split(",")]
            self.prompt.block_relations.append((sources, "->", targets))
            return

        # L3: Metadata — pattern: "directive.key: value"
        if "." in line and ":" in line:
            dot_pos = line.index(".")
            colon_pos = line.index(":", dot_pos)
            meta_key = line[:colon_pos].strip()
            meta_value = line[colon_pos + 1:].strip()
            self.prompt.block_meta[meta_key] = meta_value
            return

    # PURPOSE: Skip empty lines and comments.
    def _skip_empty_lines(self):
        """Skip empty lines and comments."""
        while self.pos < len(self.lines):
            line = self.lines[self.pos].rstrip()
            if line and not line.startswith("//"):
                break
            self.pos += 1

    # PURPOSE: Get current line.
    def _current_line(self) -> str:
        """Get current line."""
        if self.pos < len(self.lines):
            return self.lines[self.pos].rstrip()
        return ""

    # PURPOSE: Parse #prompt header.
    def _parse_header(self):
        """Parse #prompt header and optional #syntax: v8."""
        line = self._current_line()
        match = self.HEADER_PATTERN.match(line)
        if not match:
            raise ParseError(f"Expected '#prompt <name>', got: {line}", self.pos + 1)

        self.prompt = Prompt(name=match.group(1))
        self.pos += 1

        # v8.0: Check for optional #syntax, #depth, #target headers
        while self.pos < len(self.lines):
            self._skip_empty_lines()
            if self.pos >= len(self.lines):
                break
            
            line = self._current_line()
            
            syntax_match = self.SYNTAX_PATTERN.match(line)
            if syntax_match:
                self.prompt.syntax_version = syntax_match.group(1)
                self.pos += 1
                continue

            depth_match = self.DEPTH_PATTERN.match(line)
            if depth_match:
                self.prompt.depth = depth_match.group(1)
                self.pos += 1
                continue
                
            target_match = self.TARGET_PATTERN.match(line)
            if target_match:
                self.prompt.target = target_match.group(1)
                self.pos += 1
                continue
                
            # If line is not empty and not a header, stop header parsing
            if line and not line.startswith("//"):
                break

    # PURPOSE: Parse v8 syntax (<:directive: ... :>).
    def _parse_v8(self) -> Prompt:
        """Parse v8 syntax with <:directive: ... :> blocks.

        v8 uses explicit open/close delimiters:
        - Single-line: <:directive: content :>
        - Multi-line:  <:directive:\n  content\n:>
        - Nested:      <:if cond:\n  <:directive: ... :>\n:>
        """
        while self.pos < len(self.lines):
            self._skip_empty_lines()
            if self.pos >= len(self.lines):
                break

            line = self._current_line()

            # Try single-line match: <:directive: content :>
            inline_match = self.V8_INLINE_PATTERN.match(line)
            if inline_match:
                directive = inline_match.group(1)
                content = inline_match.group(2).strip()
                self._assign_v8_directive(directive, content)
                self.pos += 1
                continue

            # Try <:if condition: (must be before generic block open)
            if_match = self.V8_IF_PATTERN.match(line)
            if if_match:
                self.pos += 1
                content = self._collect_v8_block_content()
                self._parse_v8_condition_block(line, content)
                continue

            # Try multi-line block open: <:directive:
            block_match = self.V8_BLOCK_OPEN_PATTERN.match(line)
            if block_match:
                directive = block_match.group(1)
                self.pos += 1
                content = self._collect_v8_block_content(directive)
                # Special handling for 'if' blocks
                if directive == "if":
                    self._parse_v8_condition_block(
                        block_match.group(0), content
                    )
                else:
                    self._assign_v8_directive(directive, content)
                continue

            # Skip unknown lines or text content belonging to parent
            self.pos += 1

        return self.prompt

    # PURPOSE: Try to parse a v8 block at current position (for hybrid mode).
    def _try_parse_v8_block(self) -> bool:
        """Try to parse a v8 block at current position.

        Returns True if a v8 block was parsed, False otherwise.
        Used in hybrid mode to handle v8 blocks mixed with v7 directives.
        """
        line = self._current_line()

        # Try single-line match: <:directive: content :>
        inline_match = self.V8_INLINE_PATTERN.match(line)
        if inline_match:
            directive = inline_match.group(1)
            content = inline_match.group(2).strip()
            self._assign_v8_directive(directive, content)
            self.pos += 1
            return True

        # Try multi-line block open: <:directive:
        block_match = self.V8_BLOCK_OPEN_PATTERN.match(line)
        if block_match:
            directive = block_match.group(1)
            self.pos += 1
            content = self._collect_v8_block_content(directive)
            if directive == "if":
                self._parse_v8_condition_block(
                    block_match.group(0), content
                )
            else:
                self._assign_v8_directive(directive, content)
            return True

        return False

    # PURPOSE: Collect content lines until matching :> is found.
    def _collect_v8_block_content(self, block_name: str = "") -> str:
        """Collect content lines until matching :> or /name:> is found.

        Handles nested <: :> blocks by tracking depth.
        Supports named close tags: /name:> for explicit matching.
        RFC v0.4: Ignores `<:` and `:>` inside markdown code blocks (```).

        Args:
            block_name: The directive name for named close tag matching.
        """
        lines: list[str] = []
        depth = 1
        in_code_block = False

        while self.pos < len(self.lines):
            line = self._current_line()
            stripped = line.strip()

            # RFC v0.4: Toggle code block protection
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                lines.append(line)
                self.pos += 1
                continue

            # If inside a code block, ignore all v8 markers
            if in_code_block:
                lines.append(line)
                self.pos += 1
                continue

            # Check for nested block open
            if self.V8_BLOCK_OPEN_PATTERN.match(stripped) or self.V8_IF_PATTERN.match(stripped):
                depth += 1
                lines.append(line)
                self.pos += 1
                continue

            # Check for named block close: /name:>
            named_close = self.V8_NAMED_CLOSE_PATTERN.match(stripped)
            if named_close:
                close_name = named_close.group(1)
                # RFC v0.4: if name matches exactly, close regardless of depth
                if close_name == block_name:
                    self.pos += 1
                    break
                else:
                    # Mismatched named close — treat as decrement if we are at depth > 1
                    # (it might be closing an inner block we just passed over)
                    depth -= 1
                    if depth == 0:
                        # Should not normally happen if names match, but safely break
                        self.pos += 1
                        break
                    lines.append(line)
                    self.pos += 1
                    continue

            # Check for anonymous block close: :>
            if stripped == ":>":
                depth -= 1
                if depth == 0:
                    self.pos += 1  # consume the :>
                    break
                else:
                    lines.append(line)
                    self.pos += 1
                    continue

            # Check for inline close on a content line (nested single-line)
            # Example: <:input: code :> inside <:example:
            if self.V8_INLINE_PATTERN.match(stripped):
                lines.append(line)
                self.pos += 1
                continue

            lines.append(line)
            self.pos += 1

        return "\n".join(lines)

    # PURPOSE: Assign a v8 directive value to the appropriate Prompt field.
    def _assign_v8_directive(self, directive: str, content: str):
        """Map v8 directive name to Prompt block and assign content."""
        if directive == "role":
            self.prompt.blocks["@role"] = content.strip()
        elif directive == "goal":
            self.prompt.blocks["@goal"] = content.strip()
        elif directive == "constraints":
            # Parse list items (lines starting with "- " or "  - ")
            items = []
            for line in content.split("\n"):
                stripped = line.strip()
                if stripped.startswith("- "):
                    items.append(stripped[2:])
            if items:
                self.prompt.blocks["@constraints"] = items
            elif content.strip():
                # Single constraint as text
                self.prompt.blocks["@constraints"] = [content.strip()]
        elif directive == "format":
            self.prompt.blocks["@format"] = content.strip()
        elif directive == "rubric":
            self.prompt.blocks["@rubric"] = self._parse_v8_rubric(content)
        elif directive == "examples":
            self.prompt.blocks["@examples"] = self._parse_v8_examples(content)
        elif directive == "tools":
            self.prompt.blocks["@tools"] = self._parse_v8_key_value(content)
        elif directive == "resources":
            self.prompt.blocks["@resources"] = self._parse_v8_key_value(content)
        elif directive == "context":
            # Store as text block for now
            self.prompt.blocks["@context"] = content.strip()
        elif directive == "conditional":
            # Raw conditional content (from v7 conversion artifacts)
            self.prompt.blocks["@conditional"] = content.strip()
        else:
            # Generic block — store with @ prefix for consistency
            self.prompt.blocks[f"@{directive}"] = content.strip()

    # PURPOSE: Parse v8 key-value pairs (for tools/resources).
    def _parse_v8_key_value(self, content: str) -> dict[str, str]:
        """Parse v8 key-value list content (for tools, resources).

        Expected format:
          - key_name: value text
          - another_key: another value
        """
        items: dict[str, str] = {}
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("- "):
                pair = stripped[2:]
                if ": " in pair:
                    key, value = pair.split(": ", 1)
                    items[key.strip()] = value.strip()
        return items

    # PURPOSE: Parse v8 rubric content into a Rubric object.
    def _parse_v8_rubric(self, content: str) -> Rubric:
        """Parse v8 rubric content into a Rubric object.

        Expected format:
          - dimension_name:
              description: ...
              scale: 1-5
              criteria:
                5: description
                3: description
        """
        rubric = Rubric()
        current_dim_name: Optional[str] = None
        current_dim: Optional[RubricDimension] = None

        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue

            # Top-level dimension: "- name:" or "name:"
            if stripped.startswith("- ") and stripped.endswith(":"):
                # Save previous dimension
                if current_dim:
                    rubric.dimensions.append(current_dim)
                current_dim_name = stripped[2:-1].strip()
                current_dim = RubricDimension(name=current_dim_name, description="", scale="")
                continue

            if current_dim:
                if stripped.startswith("description:"):
                    current_dim.description = stripped[12:].strip()
                elif stripped.startswith("scale:"):
                    current_dim.scale = stripped[6:].strip()
                elif stripped.startswith("criteria:"):
                    continue  # Just a header
                elif ":" in stripped:
                    # Criterion line: "5: description"
                    parts = stripped.split(":", 1)
                    try:
                        score = int(parts[0].strip())
                        desc = parts[1].strip()
                        current_dim.criteria[score] = desc
                    except (ValueError, IndexError):
                        pass

        # Don't forget the last dimension
        if current_dim:
            rubric.dimensions.append(current_dim)

        return rubric

    # PURPOSE: Parse v8 examples content.
    def _parse_v8_examples(self, content: str) -> list[dict]:
        """Parse v8 examples content into list of dicts.
        
        Supports both:
        1. Flat list:
           - input: ...
             output: ...
             
        2. Nested blocks (RFC v0.4):
           <:example:
             <:input: ... :>
             <:output: ... :>
           :>
        """
        examples: list[dict] = []
        
        # Check if using nested v8 syntax
        if "<:example:" in content:
            # Simple recursive extraction for known fixed structures
            ex_blocks = re.findall(r"<:example:(.*?)(?:/example:>|:>\s*(?=<:example:|:>\s*$))", content + "\n:>", re.DOTALL)
            for block in ex_blocks:
                current = {}
                
                # Extract `<:input:` ... `:>`
                inp_match = re.search(r"<:input:(.*?):>", block, re.DOTALL)
                if inp_match:
                    current["input"] = inp_match.group(1).strip()
                    
                # Extract `<:output:` ... `:>`
                out_match = re.search(r"<:output:(.*?):>", block, re.DOTALL)
                if out_match:
                    current["output"] = out_match.group(1).strip()
                    
                if current:
                    examples.append(current)
            
            return examples
            
        # Fallback to older flat list syntax
        current: dict = {}
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("- input:"):
                if current:
                    examples.append(current)
                current = {"input": stripped[8:].strip()}
            elif stripped.startswith("output:"):
                current["output"] = stripped[7:].strip()
            elif stripped.startswith("- output:"):
                current["output"] = stripped[9:].strip()

        if current:
            examples.append(current)

        return examples

        return examples

    # PURPOSE: Parse v8 condition block (<:if cond: ... :>).
    def _parse_v8_condition_block(self, header_line: str, content: str):
        """Parse a v8 <:if condition: ... :> block.

        Extracts condition from header and parses nested v8 blocks
        in content as conditional directives.
        """
        # Extract condition from "<:if env == "prod":"
        cond_text = header_line.strip()
        if cond_text.startswith("<:if ") and cond_text.endswith(":"):
            cond_text = cond_text[4:-1].strip()
        elif cond_text.startswith("if "):
            cond_text = cond_text[3:].strip().rstrip(":")

        # Parse condition expression (var op value)
        cond_match = re.match(
            r'(\w+)\s*(==|!=|>=|<=|>|<)\s*["\']?([^"\']+?)["\']?\s*$',
            cond_text
        )

        if cond_match:
            condition = Condition(
                variable=cond_match.group(1),
                operator=cond_match.group(2),
                value=cond_match.group(3),
                if_content={"raw": content.strip()},
                else_content={},
            )
            self.prompt.conditions.append(condition)

    # PURPOSE: Parse a block (@role, @goal, etc.).
    def _parse_block(self):
        """Parse a block (@role, @goal, etc.)."""
        line = self._current_line()

        # Special handling for @if (doesn't match standard pattern)
        if line.startswith("@if "):
            condition = self._parse_condition_block()
            if condition:
                self.prompt.conditions.append(condition)
            return

        # v2.1: Check for inline @extends: name
        extends_match = self.EXTENDS_INLINE_PATTERN.match(line)
        if extends_match:
            self.prompt.extends = extends_match.group(1).strip()
            self.pos += 1
            return

        # v2.1: Check for inline @mixin: [name1, name2]
        mixin_match = self.MIXIN_REF_PATTERN.match(line)
        if mixin_match:
            mixins_str = mixin_match.group(1)
            self.prompt.mixins = [m.strip() for m in mixins_str.split(",")]
            self.pos += 1
            return

        match = self.BLOCK_PATTERN.match(line)
        if not match:
            # Skip unknown lines
            self.pos += 1
            return

        block_type = match.group(1)
        self.pos += 1

        # v7.1: Register ALL directives under current family scope
        if hasattr(self, '_current_family') and self._current_family:
            if self._current_family in self.prompt.family_scope:
                self.prompt.family_scope[self._current_family].append(block_type)

        # v7.1+: @depth — "key signature" for active bases
        if block_type == "@depth":
            depth_val = self._parse_text_content().strip().upper()
            if depth_val in DEPTH_ACTIVE_DIRECTIVES:
                self.prompt.depth = depth_val
            return

        if block_type == "@role":
            self.prompt.blocks["@role"] = self._parse_text_content()
        elif block_type == "@goal":
            self.prompt.blocks["@goal"] = self._parse_text_content()
        elif block_type == "@constraints":
            self.prompt.blocks["@constraints"] = self._parse_list_content()
        elif block_type == "@format":
            self.prompt.blocks["@format"] = self._parse_format_content()
        elif block_type == "@examples":
            self.prompt.blocks["@examples"] = self._parse_example_content()
        elif block_type == "@tools":
            self.prompt.blocks["@tools"] = self._parse_tool_content()
        elif block_type == "@resources":
            self.prompt.blocks["@resources"] = self._parse_tool_content()  # Same format
        # v2 additions
        elif block_type == "@rubric":
            self.prompt.blocks["@rubric"] = self._parse_rubric_content()
        elif block_type == "@activation":
            self.prompt.activation = self._parse_activation_content()
        elif block_type == "@if":
            # Re-parse with condition
            self.pos -= 1  # Go back to @if line
            condition = self._parse_condition_block()
            if condition:
                self.prompt.conditions.append(condition)
        # v7.1+: @include — compiler instruction for data injection
        # (replaces legacy @context file:/dir:/conv:/mcp:/ki:)
        elif block_type == "@include":
            self.prompt.blocks["@context"] = self._parse_context_content()
        # v7.1+: @context with ContextItem format → backward compat alias for @include
        elif block_type == "@context":
            # Peek ahead: if next line looks like ContextItem ("  - type:"),
            # parse as @include (backward compat). Otherwise, parse as v7.0 text block.
            next_line = self.lines[self.pos].rstrip() if self.pos < len(self.lines) else ""
            if re.match(r'^  - (file|dir|conv|mcp|ki):', next_line):
                self.prompt.blocks["@context"] = self._parse_context_content()
            else:
                self.prompt.blocks[block_type] = self._parse_text_content()
        # v7.0: TYPOS 24 description acts — generic text blocks
        elif block_type in V7_DIRECTIVES:
            self.prompt.blocks[block_type] = self._parse_text_content()

    # PURPOSE: Parse indented text content.
    def _parse_text_content(self) -> str:
        """Parse indented text content."""
        lines = []
        while self.pos < len(self.lines):
            line = self._current_line()
            match = self.INDENTED_LINE_PATTERN.match(line)
            if match:
                lines.append(match.group(1))
                self.pos += 1
            elif line == "" or line.startswith("@") or line.startswith("#"):
                break
            else:
                self.pos += 1
                break
        return "\n".join(lines)

    # PURPOSE: Parse list items.
    def _parse_list_content(self) -> list[str]:
        """Parse list items."""
        items = []
        while self.pos < len(self.lines):
            line = self._current_line()
            match = self.LIST_ITEM_PATTERN.match(line)
            if match:
                items.append(match.group(1))
                self.pos += 1
            elif line == "":
                self.pos += 1
            elif line.startswith("@") or line.startswith("#"):
                break
            else:
                break
        return items

    # PURPOSE: Parse format content (may include fenced code block).
    def _parse_format_content(self) -> str:
        """Parse format content (may include fenced code block)."""
        lines = []
        in_fenced = False

        while self.pos < len(self.lines):
            line = self.lines[self.pos].rstrip()  # Use raw line, stripped

            # Check for fenced block start (only if not already in fenced)
            if not in_fenced and line.startswith("  ```"):
                in_fenced = True
                lines.append(line[2:])  # Remove 2-space indent
                self.pos += 1
                continue

            # Check for fenced block end
            if in_fenced:
                if line.strip() == "```" or line == "  ```":
                    lines.append("```")
                    self.pos += 1
                    break  # Exit after fenced block ends
                else:
                    # Inside fenced block, keep content
                    if line.startswith("  "):
                        lines.append(line[2:])
                    else:
                        lines.append(line)
                    self.pos += 1
                    continue

            # Regular indented content (not in fenced block)
            if line.startswith("  ") and not line.startswith("  -"):
                lines.append(line[2:])
                self.pos += 1
            elif line == "":
                self.pos += 1
            elif line.startswith("@") or line.startswith("#"):
                break
            else:
                break

        return "\n".join(lines)

    # PURPOSE: Parse example items.
    def _parse_example_content(self) -> list[dict]:
        """Parse example items."""
        examples = []
        current = {}

        while self.pos < len(self.lines):
            line = self._current_line()

            input_match = self.EXAMPLE_INPUT_PATTERN.match(line)
            output_match = self.EXAMPLE_OUTPUT_PATTERN.match(line)

            if input_match:
                if current:
                    examples.append(current)
                current = {"input": input_match.group(1)}
                self.pos += 1
            elif output_match:
                current["output"] = output_match.group(1)
                self.pos += 1
            elif line == "":
                self.pos += 1
            elif line.startswith("@") or line.startswith("#"):
                break
            else:
                break

        if current:
            examples.append(current)

        return examples

    # PURPOSE: Parse tool/resource items.
    def _parse_tool_content(self) -> dict[str, str]:
        """Parse tool/resource items."""
        items = {}
        while self.pos < len(self.lines):
            line = self._current_line()
            match = self.TOOL_ITEM_PATTERN.match(line)
            if match:
                items[match.group(1)] = match.group(2)
                self.pos += 1
            elif line == "":
                self.pos += 1
            elif line.startswith("@") or line.startswith("#"):
                break
            else:
                break
        return items

    # PURPOSE: Parse @context block content.
    def _parse_context_content(self) -> list[ContextItem]:
        """Parse @context block content."""
        items = []

        while self.pos < len(self.lines):
            line = self._current_line()

            # Check for context item: "  - type:"path" [options]"
            # Patterns: file:"path", dir:"path", conv:"title", mcp:server, ki:"name"
            item_match = re.match(
                r'^  - (file|dir|conv|mcp|ki):(["\']?)([^"\']+)\2(.*)$', line
            )
            if item_match:
                ref_type = item_match.group(1)
                path = item_match.group(3)
                options_str = item_match.group(4).strip()

                # Parse options [priority=HIGH, section="..."]
                priority = "MEDIUM"
                section = None
                filter_opt = None
                depth = None
                tool_chain = None

                if options_str:
                    # Parse filter options (filter="*.ts", depth=2)
                    filter_match = re.search(
                        r'\(filter=["\']?([^"\']+)["\']?', options_str
                    )
                    if filter_match:
                        filter_opt = filter_match.group(1)
                    depth_match = re.search(r"depth=(\d+)", options_str)
                    if depth_match:
                        depth = int(depth_match.group(1))

                    # Parse bracket options [priority=HIGH]
                    if "[" in options_str:
                        bracket_content = re.search(r"\[([^\]]+)\]", options_str)
                        if bracket_content:
                            opts = bracket_content.group(1)
                            priority_match = re.search(
                                r"priority=(HIGH|MEDIUM|LOW)", opts
                            )
                            if priority_match:
                                priority = priority_match.group(1)
                            section_match = re.search(
                                r'section=["\']?([^"\']+)["\']?', opts
                            )
                            if section_match:
                                section = section_match.group(1)

                    # Parse MCP tool chain
                    if ref_type == "mcp" and ".tool(" in path:
                        tool_chain = path
                        path = path.split(".")[0]

                items.append(
                    ContextItem(
                        ref_type=ref_type,
                        path=path,
                        priority=priority,
                        section=section,
                        filter=filter_opt,
                        depth=depth,
                        tool_chain=tool_chain,
                    )
                )
                self.pos += 1
            elif line == "":
                self.pos += 1
            elif line.startswith("@") or line.startswith("#"):
                break
            else:
                break

        return items

    # PURPOSE: Parse @rubric block content.
    def _parse_rubric_content(self) -> Rubric:
        """Parse @rubric block content."""
        rubric = Rubric()
        current_dimension = None

        while self.pos < len(self.lines):
            line = self._current_line()

            # Check for dimension header: "  - dimension_name:"
            dim_match = re.match(r"^  - ([a-z_][a-z0-9_-]*):$", line)
            if dim_match:
                if current_dimension:
                    rubric.dimensions.append(current_dimension)
                current_dimension = RubricDimension(
                    name=dim_match.group(1), description="", scale="1-5"
                )
                self.pos += 1
                continue

            # Check for dimension properties (6-space indent)
            if current_dimension and line.startswith("      "):
                prop_line = line.strip()
                if prop_line.startswith("description:"):
                    current_dimension.description = prop_line[12:].strip().strip("\"'")
                elif prop_line.startswith("scale:"):
                    current_dimension.scale = prop_line[6:].strip()
                elif prop_line.startswith("criteria:"):
                    # Parse criteria block
                    self.pos += 1
                    while self.pos < len(self.lines):
                        crit_line = self._current_line()
                        crit_match = re.match(r"^        (\d+): (.+)$", crit_line)
                        if crit_match:
                            current_dimension.criteria[crit_match.group(1)] = (
                                crit_match.group(2).strip("\"'")
                            )
                            self.pos += 1
                        elif crit_line.startswith("        "):
                            self.pos += 1
                        else:
                            break
                    continue
                self.pos += 1
                continue

            # Check for output spec: "  output:"
            if line == "  output:":
                self.pos += 1
                while self.pos < len(self.lines):
                    out_line = self._current_line()
                    if out_line.startswith("    format:"):
                        rubric.output_format = out_line[11:].strip().strip("\"'")
                    elif out_line.startswith("    key:"):
                        rubric.output_key = out_line[8:].strip().strip("\"'")
                    elif out_line.startswith("    "):
                        pass
                    else:
                        break
                    self.pos += 1
                continue

            # End conditions
            if line == "":
                self.pos += 1
            elif line.startswith("@") or line.startswith("#"):
                break
            else:
                break

        if current_dimension:
            rubric.dimensions.append(current_dimension)

        return rubric

    # PURPOSE: Parse @activation block content.
    def _parse_activation_content(self) -> Activation:
        """Parse @activation block content."""
        activation = Activation()

        while self.pos < len(self.lines):
            line = self._current_line()

            # Parse key: value pairs with 2-space indent
            if line.startswith("  ") and ":" in line:
                stripped = line[2:].strip()
                if stripped.startswith("mode:"):
                    activation.mode = stripped[5:].strip().strip("\"'")
                elif stripped.startswith("pattern:"):
                    activation.pattern = stripped[8:].strip().strip("\"'")
                elif stripped.startswith("priority:"):
                    try:
                        activation.priority = int(stripped[9:].strip())
                    except ValueError:
                        activation.priority = 1
                elif stripped.startswith("rules:"):
                    # Parse rules list: [rule1, rule2]
                    rules_str = stripped[6:].strip()
                    if rules_str.startswith("[") and rules_str.endswith("]"):
                        rules_str = rules_str[1:-1]
                        activation.rules = [
                            r.strip().strip("\"'")
                            for r in rules_str.split(",")
                            if r.strip()
                        ]
                self.pos += 1
            elif line == "":
                self.pos += 1
            elif line.startswith("@") or line.startswith("#"):
                break
            else:
                break

        return activation

    # PURPOSE: Parse @if/@else/@endif block.
    def _parse_condition_block(self) -> Optional[Condition]:
        """Parse @if/@else/@endif block."""
        line = self._current_line()

        # Parse @if condition:
        if_match = re.match(
            r'^@if\s+(\w+)\s*(==|!=|>|<|>=|<=)\s*["\']?([^"\']+)["\']?\s*:$', line
        )
        if not if_match:
            self.pos += 1
            return None

        condition = Condition(
            variable=if_match.group(1),
            operator=if_match.group(2),
            value=if_match.group(3),
        )
        self.pos += 1

        # Collect if_content until @else or @endif
        if_lines = []
        while self.pos < len(self.lines):
            line = self._current_line()
            if line == "@else:":
                self.pos += 1
                break
            elif line == "@endif":
                self.pos += 1
                return condition
            elif line.startswith("  "):
# PURPOSE: Parse a .prompt file.
                if_lines.append(line[2:])
                self.pos += 1
            elif line == "":
                self.pos += 1
            else:
                break

        condition.if_content = {"raw": "\n".join(if_lines)}

        # Collect else_content until @endif
        else_lines = []
        while self.pos < len(self.lines):
# PURPOSE: Parse content with multiple prompts and mixins.
            line = self._current_line()
            if line == "@endif":
                self.pos += 1
                break
            elif line.startswith("  "):
                else_lines.append(line[2:])
                self.pos += 1
            elif line == "":
                self.pos += 1
            else:
                break

        condition.else_content = {"raw": "\n".join(else_lines)}

        return condition


# PURPOSE: Markdown ファイルから ```typos ブロックを抽出して結合する
def _extract_typos_from_markdown(content: str) -> str:
    """Markdown ファイル内の ```typos コードブロックを抽出して結合する。

    対応フォーマット:
        - YAML フロントマター (---) はスキップ
        - ```typos で始まるブロックの中身を抽出
        - 複数ブロックがある場合は\n\nで結合

    Returns:
        結合された Typos ソースコード

    Raises:
        ValueError: ```typos ブロックが見つからない場合
    """
    blocks: list[str] = []
    lines = content.split("\n")
    i = 0
    in_block = False
    current_block: list[str] = []

    while i < len(lines):
        line = lines[i].rstrip()

        if not in_block and line.startswith("```typos"):
            in_block = True
            current_block = []
            i += 1
            continue

        if in_block:
            if line == "```":
                blocks.append("\n".join(current_block))
                in_block = False
                current_block = []
            else:
                current_block.append(line)
            i += 1
            continue

        i += 1

    if not blocks:
        raise ValueError("No ```typos blocks found in Markdown file")

    return "\n\n".join(blocks)


# PURPOSE: Parse a .prompt/.typos/.md file
def parse_file(filepath: str) -> Prompt:
    """Parse a .typos file, or extract and parse ```typos blocks from .md."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    content = path.read_text(encoding="utf-8")

    # Markdown: extract ```typos blocks first
    if path.suffix == ".md":
        content = _extract_typos_from_markdown(content)

    # Multi-prompt support: try parse_all, return first prompt
    result = parse_all(content)
    if result.prompts:
        first_name = next(iter(result.prompts))
        prompt = result.prompts[first_name]
        # Resolve extends/mixins if needed
        if prompt.extends or prompt.mixins:
            prompt = resolve(prompt, result)
        return prompt

    # Fallback: single prompt
    parser = PromptLangParser(content)
    return parser.parse()


# v2.1 additions: parse_all and resolve functions
# PURPOSE: Parse content with multiple prompts and mixins
def parse_all(content: str) -> ParseResult:
    """
    Parse content with multiple prompts and mixins.

    Supports:
        #prompt name
        #mixin name

    Returns:
        ParseResult with all prompts and mixins
    """
    result = ParseResult()
    lines = content.split("\n")
    pos = 0

    while pos < len(lines):
        line = lines[pos].rstrip()

        # Skip empty lines and comments
        if not line or line.startswith("//"):
            pos += 1
            continue

        # Check for #mixin header
        mixin_match = PromptLangParser.MIXIN_HEADER_PATTERN.match(line)
        if mixin_match:
            name = mixin_match.group(1)
            # Extract mixin content until next # header
            mixin_lines = [line]
            pos += 1
            while pos < len(lines):
                next_line = lines[pos].rstrip()
                if next_line.startswith("#prompt") or next_line.startswith("#mixin"):
                    break
                mixin_lines.append(next_line)
                pos += 1

            # Parse as prompt and convert to Mixin
            mixin_content = "\n".join(mixin_lines).replace("#mixin", "#prompt", 1)
            parser = PromptLangParser(mixin_content)
            prompt = parser.parse()
            mixin = Mixin(
                name=name,
                activation=prompt.activation,
                blocks=dict(prompt.blocks),
                conditions=list(prompt.conditions),
            )
            result.mixins[name] = mixin
            continue

        # Check for #prompt header
        prompt_match = PromptLangParser.HEADER_PATTERN.match(line)
        if prompt_match:
            name = prompt_match.group(1)
            # Extract prompt content until next # header
            prompt_lines = [line]
            pos += 1
            while pos < len(lines):
                next_line = lines[pos].rstrip()
                if next_line.startswith("#prompt") or next_line.startswith("#mixin"):
                    break
                prompt_lines.append(next_line)
                pos += 1

            prompt_content = "\n".join(prompt_lines)
            parser = PromptLangParser(prompt_content)
            prompt = parser.parse()
            result.prompts[name] = prompt
            continue

        pos += 1

    return result


# PURPOSE: [L2-auto] _merge の関数定義
def _merge(parent: Prompt | Mixin, child: Prompt) -> Prompt:
    """
    Merge parent into child. Child takes precedence for scalar fields.

    Rules:
        - str fields: child overrides
        - list fields: concatenate (parent + child)
        - dict fields: merge (child overrides)
        - complex fields (rubric, activation): child overrides
    """
    # Merge blocks
    merged_blocks = dict(parent.blocks)
    for k, v in child.blocks.items():
        if k in merged_blocks:
            if isinstance(v, list) and isinstance(merged_blocks[k], list):
                merged_blocks[k] = merged_blocks[k] + v
            elif isinstance(v, dict) and isinstance(merged_blocks[k], dict):
                merged_blocks[k] = {**merged_blocks[k], **v}
            else:
                merged_blocks[k] = v
        else:
            merged_blocks[k] = v

    return Prompt(
        name=child.name,
        conditions=parent.conditions + child.conditions,
        activation=child.activation or parent.activation,
        extends=None,  # resolved
        mixins=[],  # resolved
        _resolved=True,
        blocks=merged_blocks,
        depth=child.depth or getattr(parent, "depth", None),
        family_scope={**parent.family_scope, **child.family_scope},
        block_meta={**parent.block_meta, **child.block_meta},
        block_relations=parent.block_relations + child.block_relations,
        syntax_version=child.syntax_version,
        target=child.target,
    )


# PURPOSE: Internal resolver with cycle detection.
def resolve(prompt: Prompt, registry: ParseResult) -> Prompt:
    """
    Resolve extends and mixins for a prompt.

    Resolution order:
        1. Mixins (left to right)
        2. Extends (recursive, depth-first)
        3. Self

    Args:
        prompt: The prompt to resolve
        registry: ParseResult containing all prompts and mixins

    Returns:
        Resolved Prompt with _resolved=True

    Raises:
        CircularReferenceError: If circular reference is detected
        ReferenceError: If referenced prompt/mixin is not found
    """
    if prompt._resolved:
        return prompt

    visited: set[str] = {prompt.name}
    chain: list[str] = [prompt.name]

    return _resolve_with_chain(prompt, registry, visited, chain)


# PURPOSE: [L2-auto] _resolve_with_chain の関数定義
def _resolve_with_chain(
    prompt: Prompt, registry: ParseResult, visited: set[str], chain: list[str]
) -> Prompt:
    """Internal resolver with cycle detection."""
    result = prompt

    # 1. Apply mixins (left to right)
    for mixin_name in prompt.mixins:
# PURPOSE: Validate a .prompt file.
        mixin = registry.get_mixin(mixin_name)
        if not mixin:
            raise ReferenceError(mixin_name)
        result = _merge(mixin, result)

    # 2. Apply extends (recursive)
    if prompt.extends:
        parent_name = prompt.extends

        if parent_name in visited:
            raise CircularReferenceError(chain + [parent_name])

        parent = registry.get_prompt(parent_name) or registry.get_mixin(parent_name)
        if not parent:
            raise ReferenceError(parent_name)

        visited.add(parent_name)
        chain.append(parent_name)

        # Recursively resolve parent if it's a Prompt
        if isinstance(parent, Prompt) and (parent.extends or parent.mixins):
# PURPOSE: CLI エントリポイント — 自動化基盤の直接実行
            parent = _resolve_with_chain(parent, registry, visited, chain)

        result = _merge(parent, result)

    result._resolved = True
    return result


# PURPOSE: Validate typos file against AST rules.
def validate_file(filepath: str) -> tuple[bool, str]:
    """Validate typos file against AST rules."""
    try:
        path = Path(filepath)
        if not path.exists():
            return False, f"File not found: {filepath}"

        content = path.read_text(encoding="utf-8")

        # Markdown: extract ```typos blocks
        if path.suffix == ".md":
            content = _extract_typos_from_markdown(content)

        # Check for v8 syntax
        warnings = []
        if "#syntax: v8" not in content:
            warnings.append("⚠️ DeprecationWarning: This file uses v7 syntax. Please migrate to v8 using 'python typos.py migrate'.")

        prompt = parse_file(filepath)
        
        # Check required fields
        errors = []
        if not prompt.blocks.get("@role"):
            errors.append("Missing required block: @role")
        if not prompt.blocks.get("@goal"):
            errors.append("Missing required block: @goal")

        if errors:
            return False, "\n".join(errors)

        # Validate constraints count
        if len(prompt.blocks.get("@constraints", [])) < 1:
            return False, "Validation failed: Must have at least 1 constraint"

        # Output warnings if any
        if warnings:
            return True, "\n".join(warnings) + "\nValidation passed."
            
        return True, "Validation passed."
    except Exception as e:  # noqa: BLE001
        return False, f"Validation error: {e}"


# PURPOSE: main の処理
def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return

    command = sys.argv[1].lower()
    filepath = sys.argv[2]

    if command == "parse":
        try:
            prompt = parse_file(filepath)
            print(prompt.to_json())
        except Exception as e:  # noqa: BLE001
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "validate":
        valid, message = validate_file(filepath)
        print(message)
        sys.exit(0 if valid else 1)

    elif command == "expand":
        try:
            prompt = parse_file(filepath)
            print(prompt.expand())
        except Exception as e:  # noqa: BLE001
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "compile":
        try:
            prompt = parse_file(filepath)
            # Parse context from --context "key=value,key2=value2"
            context = {}
            for arg in sys.argv[3:]:
                if arg.startswith("--context="):
                    pairs = arg[10:].split(",")
                    for pair in pairs:
                        if "=" in pair:
                            k, v = pair.split("=", 1)
                            context[k.strip()] = v.strip()
            print(prompt.compile(context=context))
        except Exception as e:  # noqa: BLE001
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "migrate":
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if '#syntax: v8' in content:
                print(f"Already v8 syntax: {filepath}")
                sys.exit(0)
                
            result = parse_all(content)
            
            parts = []
            for name, p in result.mixins.items():
                parts.append(p.to_v8())
            for name, p in result.prompts.items():
                parts.append(p.to_v8(is_mixin=False))
                
            new_content = '\n\n'.join(parts) + '\n'
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            print(f"Successfully migrated to v8: {filepath}")
        except Exception as e:  # noqa: BLE001
            print(f"Error migrating file: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
