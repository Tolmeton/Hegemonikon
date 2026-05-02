"""
Periskopē Cognition Module — Φ0-Φ7 cognitive flow.

Implements Search Cognition Theory (kernel/search_cognition.md):
  Φ0: Intent decomposition + Query planning + Source adaptation (V1-V3)
  Φ1: Blind-spot analysis (O1 Noēsis) — 無知のリマインド
  Φ2: Divergent thinking (O3 Zētēsis) — 拡散思考
  Φ3: Context setting (P1 Khōra) — 文脈配置
  Φ4: Convergent thinking (A2 Krisis) — 収束思考
  Φ5: Action preparation (S2 Mekhanē) — 行動準備 [engine.py inline]
  Φ6: Action (O4 Energeia) — 行動 [engine.py inline]
  Φ7: Belief update (H4 Doxa) — 信念更新

Design Principles (search_cognition.md §0):
  I. Cognitive Sovereignty — perception is the subject's core competence
  II. Support ≠ Replacement — Copilot, not Autopilot
  III. Spectrum — nudge, don't substitute
"""

from mekhane.periskope.cognition.phi0_intent_decompose import (
    phi0_intent_decompose,
    IntentDecomposition,
)
from mekhane.periskope.cognition.phi0_query_planner import (
    phi0_query_plan,
    QueryPlan,
)
from mekhane.periskope.cognition.phi0_source_adapter import (
    phi0_source_adapt,
    SourceAdaptedQueries,
)
from mekhane.periskope.cognition.phi1_blind_spot import (
    phi1_blind_spot_analysis,
    phi1_coverage_gaps,
    phi1_counterfactual_queries,
)
from mekhane.periskope.cognition.phi2_divergent import phi2_divergent_thinking
from mekhane.periskope.cognition.phi3_context import phi3_context_setting, ContextPlan
from mekhane.periskope.cognition.phi4_convergent import (
    phi4_pre_search_ranking,
    phi4_post_search_framing,
    RankedQuery,
    DecisionFrame,
)
from mekhane.periskope.cognition.phi7_belief_update import phi7_belief_update, BeliefUpdate
from mekhane.periskope.cognition.phi7_query_feedback import phi7_query_feedback, QueryFeedback

__all__ = [
    "phi0_intent_decompose",
    "IntentDecomposition",
    "phi0_query_plan",
    "QueryPlan",
    "phi0_source_adapt",
    "SourceAdaptedQueries",
    "phi1_blind_spot_analysis",
    "phi1_coverage_gaps",
    "phi1_counterfactual_queries",
    "phi2_divergent_thinking",
    "phi3_context_setting",
    "ContextPlan",
    "phi4_pre_search_ranking",
    "phi4_post_search_framing",
    "RankedQuery",
    "DecisionFrame",
    "phi7_belief_update",
    "BeliefUpdate",
    "phi7_query_feedback",
    "QueryFeedback",
]

