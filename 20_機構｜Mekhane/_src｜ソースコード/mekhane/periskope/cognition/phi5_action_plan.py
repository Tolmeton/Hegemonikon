from __future__ import annotations
# PROOF: mekhane/periskope/cognition/phi5_action_plan.py
# PURPOSE: periskope モジュールの phi5_action_plan
"""
Φ5: 行動準備 (S2 Mekhanē) — Action preparation.

Design: Search Cognition Theory §2.2 (kernel/search_cognition.md)

Prepares the search execution by configuring parameters based on
the cognitive analysis from Φ1-Φ4. This module was extracted from
engine.py to align with VISION's 7-stage architecture (D5 gap fix).

Responsibilities:
  - Set max_results scaling based on depth
  - Configure timeout and concurrency parameters
  - Determine multipass strategy
"""


import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# PURPOSE: [L2-auto] ActionPlan のクラス定義
@dataclass
class ActionPlan:
    """Φ5: Search execution plan — parameters for Φ6."""

    max_results_per_source: int = 10
    """Max results to request from each source."""

    timeout_seconds: float = 30.0
    """Per-source timeout."""

    enable_multipass: bool = False
    """Whether to use W6 2-pass refinement search."""

    concurrency: int = 5
    """Max concurrent source queries."""

    reasoning: str = ""
    """Why these parameters were chosen."""


# PURPOSE: [L2-auto] phi5_action_plan の関数定義
def phi5_action_plan(
    depth: int = 2,
    multipass: bool = False,
    source_count: int = 1,
) -> ActionPlan:
    """Φ5: Prepare action plan for search execution.

    Configures search parameters based on depth level and flags.

    Args:
        depth: Research depth (1=Quick, 2=Standard, 3=Deep).
        multipass: Whether to enable 2-pass refinement.
        source_count: Number of active sources.

    Returns:
        ActionPlan with calibrated search parameters.
    """
    # Scale max_results by depth (VISION §2.1 Table)
    if depth >= 3:
        max_results = 20
        timeout = 45.0
    elif depth >= 2:
        max_results = 10
        timeout = 30.0
    else:
        max_results = 5
        timeout = 15.0

    # Concurrency scales with source count but capped
    concurrency = min(source_count * 2, 10)

    reasoning = (
        f"Depth L{depth}: max_results={max_results}, "
        f"timeout={timeout}s, multipass={multipass}, "
        f"concurrency={concurrency}"
    )

    plan = ActionPlan(
        max_results_per_source=max_results,
        timeout_seconds=timeout,
        enable_multipass=multipass,
        concurrency=concurrency,
        reasoning=reasoning,
    )

    logger.info("Φ5: %s", reasoning)
    return plan
