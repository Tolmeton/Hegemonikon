from __future__ import annotations
# PROOF: [L2/Ergon分類] <- mekhane/fep/ergon/classifier.py
"""
PROOF: [L2/Ergon分類] このファイルは存在しなければならない

A0 → MCP ツールは Markov blanket の異なる層で動作する
   → 安全性を型で保証するには分類テーブルが必要
   → 7境界ツールの safety_class デフォルトを定義

Design: 09_能動｜Ergon/02_設計｜Design/04_l_functor_schema.md §3-4
        09_能動｜Ergon/04_実装｜Impl/02_state_classification.md

Q.E.D.
"""


from dataclasses import dataclass, field
from typing import Literal

from .types import SafetyClass


# PURPOSE: [L2-design] ツール分類エントリの構造体
@dataclass
class ToolClassification:
    """Classification of an MCP tool in the Markov blanket.

    state: FEP state (μ=internal, s=sensory, a=active, η=external)
    default_safety: Default safety_class for this tool
    boundary: Whether this tool crosses the μ⇔a interface
    notes: Design rationale
    """

    tool_name: str
    state: Literal["μ", "s", "a", "η", "μ→a"]
    default_safety: SafetyClass
    boundary: bool = False
    deterministic_default: bool = True
    notes: str = ""


# PURPOSE: [L2-design] 7境界ツール + 主要ツールの分類テーブル
# Source: 02_state_classification.md + 04_l_functor_schema.md
BOUNDARY_TOOL_DEFAULTS: dict[str, ToolClassification] = {
    # ━━━ 7 Boundary tools (μ→a) ━━━
    "hermeneus_run": ToolClassification(
        tool_name="hermeneus_run",
        state="μ→a",
        default_safety=SafetyClass.REVERSIBLE,
        boundary=True,
        deterministic_default=False,
        notes="CCL execution. LLM in the loop. Output files are deletable.",
    ),
    "hermeneus_execute": ToolClassification(
        tool_name="hermeneus_execute",
        state="μ→a",
        default_safety=SafetyClass.REVERSIBLE,
        boundary=True,
        deterministic_default=False,
        notes="WF execution. Subset of hermeneus_run.",
    ),
    "ask_with_tools": ToolClassification(
        tool_name="ask_with_tools",
        state="μ→a",
        default_safety=SafetyClass.IRREVERSIBLE,
        boundary=True,
        deterministic_default=False,
        notes="⚠️ Gemini agent with file r/w. Highest risk boundary tool.",
    ),
    "context_rot_distill": ToolClassification(
        tool_name="context_rot_distill",
        state="μ→a",
        default_safety=SafetyClass.REVERSIBLE,
        boundary=True,
        deterministic_default=False,
        notes="ROM file creation. Deletable output.",
    ),
    "periskope_research": ToolClassification(
        tool_name="periskope_research",
        state="μ→a",
        default_safety=SafetyClass.READ_ONLY,
        boundary=True,
        deterministic_default=False,
        notes="Search + synthesis. No environment mutation.",
    ),
    "run_digestor": ToolClassification(
        tool_name="run_digestor",
        state="μ→a",
        default_safety=SafetyClass.REVERSIBLE,
        boundary=True,
        deterministic_default=False,
        notes="dry_run=True → READ_ONLY. Creates eat_*.md files.",
    ),
    "sekisho_gate": ToolClassification(
        tool_name="sekisho_gate",
        state="μ→a",
        default_safety=SafetyClass.REVERSIBLE,
        boundary=True,
        deterministic_default=False,
        notes="Gate token persistence. Status file update.",
    ),

    # ━━━ Pure internal (μ) — no boundary crossing ━━━
    "hermeneus_dispatch": ToolClassification(
        tool_name="hermeneus_dispatch",
        state="μ",
        default_safety=SafetyClass.READ_ONLY,
        boundary=False,
        deterministic_default=True,
        notes="CCL parsing only. No execution.",
    ),
    "mcp_mneme_search": ToolClassification(
        tool_name="mcp_mneme_search",
        state="s",
        default_safety=SafetyClass.READ_ONLY,
        boundary=False,
        deterministic_default=True,
        notes="Knowledge retrieval. Read-only.",
    ),
    "periskope_search": ToolClassification(
        tool_name="periskope_search",
        state="s",
        default_safety=SafetyClass.READ_ONLY,
        boundary=False,
        deterministic_default=False,
        notes="Lightweight search. No synthesis.",
    ),
}


# PURPOSE: [L2-design] ツール→SafetyClass 自動判定
def classify_tool(
    tool_name: str,
    *,
    override: SafetyClass | None = None,
    dry_run: bool = False,
) -> SafetyClass:
    """Classify a tool's safety_class.

    Priority:
      1. Explicit override (caller decides)
      2. dry_run → READ_ONLY (special case for run_digestor etc.)
      3. BOUNDARY_TOOL_DEFAULTS lookup
      4. Default: READ_ONLY (conservative fallback)

    Args:
        tool_name: MCP tool name (e.g., 'hermeneus_run')
        override: Explicit safety_class override
        dry_run: Whether the tool is in dry-run mode

    Returns:
        SafetyClass for the tool
    """
    if override is not None:
        return override

    if dry_run:
        return SafetyClass.READ_ONLY

    entry = BOUNDARY_TOOL_DEFAULTS.get(tool_name)
    if entry is not None:
        return entry.default_safety

    # Conservative fallback: unknown tools are read_only
    return SafetyClass.READ_ONLY


# PURPOSE: [L2-design] 境界ツールか否かの判定
def is_boundary_tool(tool_name: str) -> bool:
    """Check if a tool crosses the μ⇔a interface."""
    entry = BOUNDARY_TOOL_DEFAULTS.get(tool_name)
    return entry.boundary if entry is not None else False


# PURPOSE: [L2-design] N-04 θ4.5 ブラックリスト適合性チェック
def requires_confirmation(tool_name: str, safety: SafetyClass | None = None) -> bool:
    """Check if a tool invocation requires Creator confirmation (N-04 θ4.1).

    Returns True for:
      - IRREVERSIBLE safety_class
      - ask_with_tools (always, regardless of safety_class)
    """
    if safety is None:
        safety = classify_tool(tool_name)

    if safety == SafetyClass.IRREVERSIBLE:
        return True

    # ask_with_tools is always high-risk
    if tool_name == "ask_with_tools":
        return True

    return False
