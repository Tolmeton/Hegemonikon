# PROOF: [L2/インフラ] <- mekhane/fep/ergon/__init__.py
"""
PROOF: [L2/インフラ] このファイルは存在しなければならない

A0 → Ergon は FEP の Active States (a) を型付けする
   → Markov blanket の μ⇔a インターフェースに型安全性を提供
   → __init__.py がパッケージエントリポイントを担う

Q.E.D.

---

Ergon: Active States type system for the Markov blanket.

Provides:
- SafetyClass: Graduated permeability of the blanket (read_only/reversible/irreversible)
- Plan/Task: L functor types (Cog → Exec)
- ExecutionResult/BeliefUpdate: R functor types (Exec → Cog)
- classify_tool: Tool → SafetyClass classifier
"""

from .types import (
    SafetyClass,
    SourceLabel,
    Confidence,
    Plan,
    Task,
    ExecutionResult,
    ErgonBeliefUpdate,
)
from .classifier import classify_tool, BOUNDARY_TOOL_DEFAULTS
from .functors import source_label_rule, forgetting_rate
from .protocols import (
    BeliefChannelProtocol,
    ergon_to_channel,
    phi7_to_channel,
    compare_channels,
)

__all__ = [
    # Types
    "SafetyClass",
    "SourceLabel",
    "Confidence",
    "Plan",
    "Task",
    "ExecutionResult",
    "ErgonBeliefUpdate",
    # Classifier
    "classify_tool",
    "BOUNDARY_TOOL_DEFAULTS",
    # Functors
    "source_label_rule",
    "forgetting_rate",
    # Protocols
    "BeliefChannelProtocol",
    "ergon_to_channel",
    "phi7_to_channel",
    "compare_channels",
]
