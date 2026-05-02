from __future__ import annotations
# PROOF: mekhane/periskope/phases/belief_update.py
# PURPOSE: Phase 4 — Φ7 Belief Update + Adaptive Depth Escalation
"""
Phase 4: Belief Update.

  Φ7: Belief update (H4 Doxa) — residual error, should_loop, seed queries
  Adaptive depth escalation: auto-escalate to L3 when quality insufficient

Extracted from engine.py:
  - _phase_belief_update (L2562-2589)
"""

import logging

from mekhane.periskope.models import SearchResult
from mekhane.periskope.cognition import (
    BeliefUpdate,
    phi1_coverage_gaps,
    phi7_belief_update,
)

logger = logging.getLogger(__name__)


async def phase_belief_update(
    query: str,
    search_results: list[SearchResult],
    source_counts: dict[str, int],
    synthesis: list,
    quality: object,
    adaptive_threshold: float,
) -> BeliefUpdate | None:
    """Φ7: Belief update (H4 Doxa).

    Analyzes synthesis quality and determines if additional research
    iteration is needed.

    Returns:
        BeliefUpdate with residual_error, should_loop, seed_queries,
        or None on failure.
    """
    try:
        gaps = phi1_coverage_gaps(query, search_results, source_counts)
        belief = await phi7_belief_update(
            query=query,
            overall_score=quality.overall_score,
            synthesis_texts=[s.content for s in synthesis] if synthesis else [],
            coverage_gaps=gaps,
            iteration=0,
            loop_threshold=adaptive_threshold,
        )
        logger.info(
            "Φ7: residual_error=%.2f, should_loop=%s, seeds=%d",
            belief.residual_error, belief.should_loop, len(belief.seed_queries),
        )
        return belief
    except Exception as e:  # noqa: BLE001
        logger.warning("Φ7 belief update failed: %s", e)
        return None
