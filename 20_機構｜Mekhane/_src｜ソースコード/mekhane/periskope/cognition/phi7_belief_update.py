from __future__ import annotations
# PROOF: mekhane/periskope/cognition/phi7_belief_update.py
# PURPOSE: periskope モジュールの phi7_belief_update
"""
Φ7: 信念更新 (H4 Doxa) — Belief update.

Design: Search Cognition Theory §2.2 (kernel/search_cognition.md)

After search + synthesis + verification, evaluates:
  1. Residual prediction error = 1 - overall_quality_score
  2. Whether to loop back to Φ1 (residual > θ)
  3. Seed queries for the next iteration

Loop structure (§2.3):
  Φ7 → Φ1 if residual_error > θ
  Precision increases each iteration (narrowing search space).

The final belief update (knowledge persistence) is the subject's
responsibility — Periskopē provides the data, not the decision.
"""


import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# PURPOSE: [L2-auto] BeliefUpdate のクラス定義
@dataclass
class BeliefUpdate:
    """Result of Φ7 belief update analysis."""

    residual_error: float = 0.0
    """1 - overall_score. High = search didn't fully answer the question."""

    should_loop: bool = False
    """Whether to go back to Φ1 for another search round."""

    seed_queries: list[str] = field(default_factory=list)
    """Queries to use in the next iteration (empty if no loop)."""

    coverage_gaps: list[str] = field(default_factory=list)
    """Identified coverage gaps from Φ1 post-search analysis."""

    iteration: int = 0
    """Current iteration number (0-based)."""

    confidence_trend: str = "stable"
    """Direction of confidence: 'improving', 'stable', 'declining'."""

    def to_channel(self) -> dict:
        """Adapt to BeliefChannelProtocol format (Ergon cross-channel).

        Enables cross-channel comparison between s→μ (Periskopē)
        and a→μ (Ergon) belief updates.

        Returns:
            Dict with prediction_residual, should_iterate, confidence_direction.
        """
        try:
            from mekhane.fep.ergon.protocols import phi7_to_channel
            return phi7_to_channel(self)
        except ImportError:
            # Graceful degradation: Ergon not installed
            return {
                "prediction_residual": self.residual_error,
                "should_iterate": self.should_loop,
                "confidence_direction": self.confidence_trend,
            }


# PURPOSE: [L2-auto] _llm_ask の共通モジュール参照
from mekhane.periskope.cognition._llm import llm_ask as _llm_ask

# PURPOSE: Týpos プロンプトローダー
from mekhane.periskope.prompts import load_prompt


# PURPOSE: [L2-auto] phi7_belief_update の非同期処理定義
async def phi7_belief_update(
    query: str,
    overall_score: float,
    synthesis_texts: list[str],
    coverage_gaps: list[str] | None = None,
    iteration: int = 0,
    max_iterations: int = 2,
    loop_threshold: float = 0.5,
) -> BeliefUpdate:
    """Φ7: Evaluate residual prediction error and decide whether to loop.

    After search + synthesis + verification, calculates:
    - Residual error = 1 - overall_score
    - Whether quality is below threshold (should_loop)
    - Seed queries for next iteration (if looping)

    Loop conditions:
    - residual_error > loop_threshold AND iteration < max_iterations
    - Not looping if quality is adequate or max iterations reached

    Args:
        query: Original research query.
        overall_score: Quality metrics overall score (0-1).
        synthesis_texts: Content from multi-model synthesis.
        coverage_gaps: Gaps identified by Φ1 post-search (phi1_coverage_gaps).
        iteration: Current iteration number (0-based).
        max_iterations: Maximum loop iterations allowed.
        loop_threshold: Residual error threshold for looping.

    Returns:
        BeliefUpdate with loop decision and seed queries.
    """
    residual = 1.0 - overall_score

    # VISION §2.3: Precision requirement increases each iteration
    # Lower threshold = stricter quality requirement
    # Fix: 0.15 was too steep, changed to 0.10 for smoother escalation.
    precision_step = 0.10
    dynamic_threshold = max(0.2, loop_threshold - (iteration * precision_step))
    should_loop = residual > dynamic_threshold and iteration < max_iterations

    update = BeliefUpdate(
        residual_error=residual,
        should_loop=should_loop,
        coverage_gaps=coverage_gaps or [],
        iteration=iteration,
    )

    if not should_loop:
        logger.info(
            "Φ7: Residual error %.2f (dynamic threshold %.2f), iteration %d/%d — no loop needed",
            residual, dynamic_threshold, iteration, max_iterations,
        )
        return update

    # Generate seed queries for next iteration
    gap_text = "\n".join(f"- {g}" for g in (coverage_gaps or []))
    combined = "\n".join(t[:500] for t in synthesis_texts[:2])

    template = load_prompt("phi7_belief_update.typos")
    if template:
        prompt = template.format(
            query=query,
            overall_score=f"{overall_score:.0%}",
            target_quality=f">{(1-loop_threshold):.0%}",
            iteration_info=f"{iteration + 1}/{max_iterations}",
            gap_text=gap_text if gap_text else "(none)",
            combined_synthesis=combined[:1000],
        )
    else:
        # Fallback: hardcoded prompt
        prompt = (
            "A research search has completed but quality is below threshold.\n\n"
            f"Original query: {query}\n"
            f"Quality score: {overall_score:.0%} (target: >{(1-loop_threshold):.0%})\n"
            f"Iteration: {iteration + 1}/{max_iterations}\n"
        )
        if gap_text:
            prompt += f"\nIdentified gaps:\n{gap_text}\n"
        prompt += (
            f"\nCurrent synthesis (truncated):\n{combined[:1000]}\n\n"
            "Generate 2-3 FOCUSED follow-up queries that would:\n"
            "1. Fill the identified gaps\n"
            "2. Improve answer quality\n"
            "3. Cover missing perspectives\n\n"
            "Return ONLY the queries, one per line. No numbering.\n"
            "Make each query more SPECIFIC than the original — narrower, deeper."
        )

    text = await _llm_ask(prompt, max_tokens=256)

    if text and "NONE" not in text.upper().strip():
        update.seed_queries = [
            line.strip()
            for line in text.strip().split("\n")
            if line.strip() and len(line.strip()) > 5
        ][:3]

    logger.info(
        "Φ7: Residual error %.2f > dynamic threshold %.2f — looping with %d seed queries",
        residual, dynamic_threshold, len(update.seed_queries),
    )

    return update
