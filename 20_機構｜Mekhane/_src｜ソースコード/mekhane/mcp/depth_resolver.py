from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/mcp/depth_resolver.py
"""
Depth Resolver — Harness depth detection from 3 input paths.

PURPOSE:
    Determine HarnessDepth (L0/L1/L2/L3) for a tool invocation, then hand off
    to harness_gate to choose the active harness profile.

    This module is the HGK-specific advisor in the Depth-driven Harness
    Selection design (plan: ccl-llm-api-hidden-popcorn.md, Phase 0).

DETECTION PRIORITY (high to low):
    1. Explicit override (`arguments["_depth"]` or env `HGK_DEPTH`)
    2. CCL modifier (`+`->L3 / no-mark->L2 / `-`->L1 / `--`->L0) parsed from
       arguments["ccl_expr"] (or any string field if `ccl_expr` is absent —
       see resolve_from_text)
    3. Skill frontmatter (`#depth: L2`) injected as `arguments["_skill_depth"]`
       by the skill loader (separate concern, parser extension TODO)
    4. Default fallback: HarnessDepth.L2 (current implicit default = regression
       safety)

NOTE on Depth enum reuse:
    Re-exports `prokataskeve.models.Depth` as the SoT. The same enum is used
    by prokataskeve.PreprocessPipeline at a different layer (text
    preprocessing complexity), but harness_gate consumes the same identifiers
    for harness profile lookup. They are semantically distinct uses of the
    same name space — kept intentionally aligned to avoid divergence.
"""

import os
from typing import Any

from mekhane.mcp.prokataskeve.models import Depth as HarnessDepth

# Re-export for downstream consumers (harness_gate, gateway_hooks).
__all__ = ["HarnessDepth", "resolve_depth", "depth_from_ccl_modifier"]

# CCL modifier -> HarnessDepth mapping.
# Source of truth: 10_知性｜Nous/01_制約｜Constraints/E_CCL｜CCL/operators.md §1.1
# Aligned with mekhane.ccl.output_schema.OperatorType (DEEPEN="+", CONDENSE="-").
_MODIFIER_TO_DEPTH: dict[str, HarnessDepth] = {
    "++": HarnessDepth.L4,   # double deepen (rare; reserved)
    "+":  HarnessDepth.L3,   # deepen
    "":   HarnessDepth.L2,   # default
    "-":  HarnessDepth.L1,   # condense
    "--": HarnessDepth.L0,   # bypass
}

# Env var override key (uppercase; HGK convention).
_ENV_KEY = "HGK_DEPTH"

# Argument keys recognised by 3-path detection.
_ARG_EXPLICIT = "_depth"             # path 1: explicit
_ARG_CCL_EXPR = "ccl_expr"           # path 2: CCL modifier source
_ARG_SKILL_DEPTH = "_skill_depth"    # path 3: skill frontmatter injected


# PURPOSE: Parse a CCL modifier suffix (+, -, ++, --) into a HarnessDepth.
def depth_from_ccl_modifier(ccl_expr: str) -> HarnessDepth | None:
    """Extract trailing CCL modifier and return its depth, or None.

    Examples:
        "/noe+"   -> HarnessDepth.L3
        "/noe-"   -> HarnessDepth.L1
        "/noe"    -> HarnessDepth.L2 (default; explicit no-mark)
        "/noe--"  -> HarnessDepth.L0
        ""        -> None (no expression)
    """
    if not ccl_expr or not isinstance(ccl_expr, str):
        return None

    expr = ccl_expr.strip()
    if not expr:
        return None

    # Match longest modifier first (++/-- before single + / -).
    for mod in ("++", "--", "+", "-"):
        if expr.endswith(mod):
            return _MODIFIER_TO_DEPTH[mod]

    # No modifier => explicit default depth.
    return _MODIFIER_TO_DEPTH[""]


# PURPOSE: Parse explicit depth string into HarnessDepth, lenient.
def _parse_explicit(value: str | None) -> HarnessDepth | None:
    """Accept "L0".."L4" (case-insensitive) or "0".."4". None on failure."""
    if value is None:
        return None
    s = str(value).strip().upper()
    if not s:
        return None
    if not s.startswith("L"):
        s = f"L{s}"
    try:
        return HarnessDepth(s)
    except ValueError:
        return None


# PURPOSE: Resolve harness depth via 3-path priority.
def resolve_depth(arguments: dict[str, Any] | None = None) -> HarnessDepth:
    """Resolve HarnessDepth for a tool call.

    Returns HarnessDepth.L2 (current implicit default) on failure of all paths.
    This default preserves regression safety: skills with no depth signal
    behave exactly as today.

    Args:
        arguments: tool call arguments (may be None, e.g. for bare gateway
                   probes).

    Resolution order:
        1. arguments["_depth"]   (explicit override at call site)
        2. env HGK_DEPTH         (process-wide override)
        3. arguments["ccl_expr"] (CCL modifier suffix)
        4. arguments["_skill_depth"] (skill frontmatter injected by loader)
        5. HarnessDepth.L2 (fallback)
    """
    args = arguments or {}

    # Path 1a: explicit argument
    explicit = _parse_explicit(args.get(_ARG_EXPLICIT))
    if explicit is not None:
        return explicit

    # Path 1b: env var (process-wide override; useful for L0 perf testing)
    env_explicit = _parse_explicit(os.environ.get(_ENV_KEY))
    if env_explicit is not None:
        return env_explicit

    # Path 2: CCL modifier
    ccl_expr = args.get(_ARG_CCL_EXPR)
    if isinstance(ccl_expr, str):
        from_modifier = depth_from_ccl_modifier(ccl_expr)
        if from_modifier is not None:
            return from_modifier

    # Path 3: skill frontmatter (injected by skill loader; not yet wired)
    skill_depth = _parse_explicit(args.get(_ARG_SKILL_DEPTH))
    if skill_depth is not None:
        return skill_depth

    # Fallback: current implicit default
    return HarnessDepth.L2
