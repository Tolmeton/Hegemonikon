# PROOF: [L1/基盤] <- mekhane/synteleia/nomoi/__init__.py 12法エージェント群
# PURPOSE: 12 Nomoi エージェントを一元的にエクスポートする
"""
Nomoi Agents — 12法ベースの監査エージェント群

3原理 × 4位相 = 12 エージェント:

  S-I  Tapeinophrosyne × {Aisthēsis, Dianoia, Ekphrasis, Praxis}
    = N01EntityAgent, N02UncertaintyAgent, N03ConfidenceAgent, N04IrreversibleAgent

  S-II  Autonomia × {Aisthēsis, Dianoia, Ekphrasis, Praxis}
    = N05ExplorationAgent, N06AnomalyAgent, N07ExpressionAgent, N08ToolUseAgent

  S-III Akribeia × {Aisthēsis, Dianoia, Ekphrasis, Praxis}
    = N09SourceAgent, N10TaintAgent, N11ActionableAgent, N12PrecisionAgent
"""

from .n01_entity import N01EntityAgent
from .n02_uncertainty import N02UncertaintyAgent
from .n03_confidence import N03ConfidenceAgent
from .n04_irreversible import N04IrreversibleAgent
from .n05_exploration import N05ExplorationAgent
from .n06_anomaly import N06AnomalyAgent
from .n07_expression import N07ExpressionAgent
from .n08_tooluse import N08ToolUseAgent
from .n09_source import N09SourceAgent
from .n10_taint import N10TaintAgent
from .n11_actionable import N11ActionableAgent
from .n12_precision import N12PrecisionAgent

# 原理ごとのグループ
S1_AGENTS = [N01EntityAgent, N02UncertaintyAgent, N03ConfidenceAgent, N04IrreversibleAgent]
S2_AGENTS = [N05ExplorationAgent, N06AnomalyAgent, N07ExpressionAgent, N08ToolUseAgent]
S3_AGENTS = [N09SourceAgent, N10TaintAgent, N11ActionableAgent, N12PrecisionAgent]

# 位相ごとのグループ
P1_AGENTS = [N01EntityAgent, N05ExplorationAgent, N09SourceAgent]  # Aisthēsis
P2_AGENTS = [N02UncertaintyAgent, N06AnomalyAgent, N10TaintAgent]  # Dianoia
P3_AGENTS = [N03ConfidenceAgent, N07ExpressionAgent, N11ActionableAgent]  # Ekphrasis
P4_AGENTS = [N04IrreversibleAgent, N08ToolUseAgent, N12PrecisionAgent]  # Praxis

ALL_AGENTS = S1_AGENTS + S2_AGENTS + S3_AGENTS

__all__ = [
    "N01EntityAgent", "N02UncertaintyAgent", "N03ConfidenceAgent", "N04IrreversibleAgent",
    "N05ExplorationAgent", "N06AnomalyAgent", "N07ExpressionAgent", "N08ToolUseAgent",
    "N09SourceAgent", "N10TaintAgent", "N11ActionableAgent", "N12PrecisionAgent",
    "S1_AGENTS", "S2_AGENTS", "S3_AGENTS",
    "P1_AGENTS", "P2_AGENTS", "P3_AGENTS", "P4_AGENTS",
    "ALL_AGENTS",
]
