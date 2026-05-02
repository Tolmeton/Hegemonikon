# PROOF: [L2/インフラ] <- mekhane/synteleia/kritai/__init__.py Kritai 審査層パッケージ
"""
Kritai (κριταί) — 審査層 [非推奨]

⚠️ このパッケージは非推奨。mekhane.synteleia.nomoi を使用してください。
旧エージェント → 12法 (Nomoi) エージェントへのマッピング:
  PerigrapheAgent  → N04SafetyAgent (S-I × P4)
  KairosAgent      → N08ToolAgent (S-II × P4)
  OperatorAgent    → N12ExecutionAgent (S-III × P4)
  LogicAgent       → N06AnomalyAgent (S-II × P2)
  CompletenessAgent → N11ActionableAgent (S-III × P3)
  SemanticAgent    → L2 追加層として維持
"""

import warnings as _warnings

_warnings.warn(
    "mekhane.synteleia.kritai は非推奨です。"
    " mekhane.synteleia.nomoi を使用してください。"
    " 詳細: synteleia_design.md §後方互換性",
    DeprecationWarning,
    stacklevel=2,
)

from .perigraphe_agent import PerigrapheAgent
from .kairos_agent import KairosAgent
from .operator_agent import OperatorAgent
from .logic_agent import LogicAgent
from .completeness_agent import CompletenessAgent
from .semantic_agent import SemanticAgent

__all__ = [
    "PerigrapheAgent",
    "KairosAgent",
    "OperatorAgent",
    "LogicAgent",
    "CompletenessAgent",
    "SemanticAgent",
]
