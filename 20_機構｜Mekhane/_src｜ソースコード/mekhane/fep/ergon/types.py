from __future__ import annotations
# PROOF: [L2/Ergon型] <- mekhane/fep/ergon/types.py
"""
PROOF: [L2/Ergon型] このファイルは存在しなければならない

A0 → FEP の Markov blanket は μ/s/a/η の4状態を分離する
   → μ⇔a インターフェースには型安全性が必要
   → L 関手 (Plan→Task) と R 関手 (Result→Belief) の型を定義

Design: 09_能動｜Ergon/02_設計｜Design/04_l_functor_schema.md
        09_能動｜Ergon/02_設計｜Design/05_r_functor_schema.md

Q.E.D.
"""


from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


# ━━━ Enums ━━━


# PURPOSE: [L2-design] Markov blanket の透過度を3段階で制御
class SafetyClass(str, Enum):
    """Graduated permeability of the Markov blanket.

    Biological analogy:
      read_only    → ion channel (always open, passive diffusion)
      reversible   → gated channel (open/close, git rollback possible)
      irreversible → active transport (energy-consuming, N-04 θ4.1 required)
    """

    READ_ONLY = "read_only"
    REVERSIBLE = "reversible"
    IRREVERSIBLE = "irreversible"


# PURPOSE: [L2-design] N-10 SOURCE/TAINT 区別の型化
class SourceLabel(str, Enum):
    """Precision label for belief updates (N-10 compliance).

    SOURCE:     view_file, test result, deterministic execution
    TAINT:      LLM synthesis, memory, reasoning
    WEAK_INPUT: Creator verbal, Handoff, external papers
    """

    SOURCE = "SOURCE"
    TAINT = "TAINT"
    WEAK_INPUT = "WEAK_INPUT"


# PURPOSE: [L2-design] N-3 確信度ラベルの型化
class Confidence(str, Enum):
    """Confidence label for belief updates (N-3 compliance).

    Must be proportional to SourceLabel:
      SOURCE     → 確信 (90%+)
      TAINT      → 推定 (60-90%) upper bound
      WEAK_INPUT → 仮説 (<60%) upper bound
    """

    CERTAIN = "確信"    # 90%+
    ESTIMATED = "推定"  # 60-90%
    HYPOTHESIS = "仮説"  # <60%


# ━━━ L 関手の型 ━━━


# PURPOSE: [L2-design] L 関手の入力 — μ 側の対象
@dataclass
class Plan:
    """L functor input. Internal States (μ) object.

    What HGK intends to do — the cognitive plan before execution.
    """

    intent: str
    """What the agent intends to achieve. Natural language description."""

    context: str = ""
    """Relevant context for the plan. Should be /rom+ full-volume (θ12.1c)."""

    confidence_threshold: float = 0.6
    """Minimum confidence required for the plan to be actionable."""

    source_label: SourceLabel = SourceLabel.TAINT
    """Precision label of the plan's basis."""

    nomoi_refs: list[str] = field(default_factory=list)
    """Relevant Nomoi references (e.g., ['N-04', 'N-12'])."""

    depth: Literal["L0", "L1", "L2", "L3"] = "L2"
    """Depth level for execution."""


# PURPOSE: [L2-design] L 関手の出力 — a 側の対象
@dataclass
class Task:
    """L functor output. Active States (a) object.

    Concrete executable task derived from a Plan.
    """

    tool_name: str
    """MCP tool to invoke (e.g., 'hermeneus_run', 'ask_with_tools')."""

    parameters: dict = field(default_factory=dict)
    """Tool-specific parameters (JSON-serializable)."""

    safety_class: SafetyClass = SafetyClass.READ_ONLY
    """Graduated permeability level."""

    deterministic: bool = True
    """Whether the tool execution is deterministic (no LLM in the loop)."""

    plan_id: str = ""
    """Trace back to the originating Plan."""

    expected_side_effects: list[str] = field(default_factory=list)
    """Predicted side effects (e.g., ['file_create:*.md', 'api_call:gemini'])."""


# ━━━ R 関手の型 ━━━


# PURPOSE: [L2-design] R 関手の入力 — a 側の対象
@dataclass
class ExecutionResult:
    """R functor input. Active States (a) object.

    Raw result data generated after tool execution.
    """

    plan_id: str
    """Trace back to the originating Plan/Task."""

    tool_name: str
    """Executed tool name. Should match Task.tool_name."""

    raw_output: str | dict = ""
    """Raw tool output (JSON or text)."""

    exit_status: Literal["success", "failure", "partial", "timeout"] = "success"
    """Execution termination status."""

    actual_side_effects: list[str] = field(default_factory=list)
    """Actually occurred side effects. Compare with Task.expected_side_effects."""

    duration_ms: int = 0
    """Execution duration in milliseconds."""

    verification: dict | None = None
    """Multi-Agent Debate / Sekisho audit result if available.
    {verdict: 'PASS'|'BLOCK', confidence: float, reasoning: str}"""


# PURPOSE: [L2-design] R 関手の出力 — μ 側の対象
@dataclass
class ErgonBeliefUpdate:
    """R functor output. Internal States (μ) object.

    Distilled belief update for μ to absorb.

    Named ErgonBeliefUpdate (not BeliefUpdate) to distinguish from
    phi7_belief_update.BeliefUpdate which operates on the s→μ channel.
    See: 05_r_functor_schema.md §3.1 (Boundary Separation).
    """

    source_label: SourceLabel
    """Precision label (N-10 compliance)."""

    confidence: Confidence
    """Confidence label (N-3 compliance). Must be proportional to source_label."""

    belief_delta: Literal["new", "updated", "confirmed", "refuted"]
    """Type of belief change."""

    summary: str
    """Distilled belief content (1-3 sentences). The R functor's forgetting result."""

    plan_id: str = ""
    """Trace back to originating Plan/Task."""

    prediction_error: str | None = None
    """Diff between Plan.intent and ExecutionResult. None = prediction confirmed.
    Non-None feeds into N-06 (anomaly detection)."""

    next_action: str | None = None
    """Recommended next action with 'なぜ: {reason}' (N-7 θ7.2 compliance).
    None = self-contained result."""
