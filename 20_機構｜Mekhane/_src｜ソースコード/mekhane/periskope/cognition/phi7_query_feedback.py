from __future__ import annotations
# PROOF: mekhane/periskope/cognition/phi7_query_feedback.py
# PURPOSE: periskope モジュールの phi7_query_feedback
"""
Φ7 Query Feedback — V5 フィードバック強化 (Iterative Query Refinement).

Design: /noe+ Periskopē クエリ形成分析 (2026-02-28)
  V5: 「検索結果を見てクエリを書き換えるフィードバック」

PURPOSE: CoT Search Chain の各イテレーションで、
V1 (意図分解) と V2 (クエリ計画) の結果を活用して
reasoning_trace の next_queries を強化する。

現行の弱点:
  - analyze_iteration が生成する next_queries は
    元のクエリと合成テキストのみから導出される
  - V1 の implicit_assumptions や V2 の step2/step3 が
    CoT ループに反映されていない
  - coverage gap 検出 (phi1_coverage_gaps) の結果が
    次のイテレーションのクエリ生成に使われていない

V5 の改善:
  - V2 の step2/step3 をイテレーション番号に応じて注入
  - V1 の未確認前提をクエリ候補に変換
  - coverage gap をクエリ化
"""


import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class QueryFeedback:
    """Φ7 output: Enhanced refinement queries from feedback analysis.

    Combines multiple signals to produce better next-iteration queries:
      - reasoning_trace gaps (from analyze_iteration)
      - V2 planned queries (step2/step3)
      - V1 unchecked assumptions
      - Coverage gaps (Φ1 post-search)
    """

    # Final merged queries for the next iteration
    queries: list[str] = field(default_factory=list)

    # Source attribution for each query
    sources: dict[str, str] = field(default_factory=dict)

    # Whether plan queries were injected
    plan_injected: bool = False

    # Selected strategy name (narrowing/verification/assumption_check)
    strategy: str = ""

    # Coverage gaps that informed query generation
    gap_queries: list[str] = field(default_factory=list)


def phi7_query_feedback(
    iteration: int,
    reasoning_next_queries: list[str],
    plan_step2: list[str] | None = None,
    plan_step3: list[str] | None = None,
    unchecked_assumptions: list[str] | None = None,
    coverage_gaps: list[str] | None = None,
    search_perspectives: list[str] | None = None,
    max_queries: int = 3,
    info_gain: float | None = None,
    saturation_threshold: float = 0.035,
    qpp_high_multiplier: float = 3.0,
) -> QueryFeedback:
    """Φ7: Enhance refinement queries with multi-signal feedback.

    Synchronous — no LLM call. Merges and prioritizes queries from
    multiple sources based on information gain (QPP gating).

    Strategy by info_gain (adaptive — QPP-based):
      - info_gain is None (first iter / unmeasured): step2 injection (narrowing)
      - info_gain > threshold * 3 (high gain): step2 injection (narrowing)
      - threshold < info_gain <= threshold * 3 (medium): step3 injection (verification)
      - info_gain <= threshold (low / saturated): assumptions + gaps injection

    Fallback: When info_gain is None AND iteration > 1, uses legacy
    iteration-based strategy for backward compatibility.

    Academic basis:
      - QPP for Agentic RAG (arXiv:2507.10411)
      - Iter-RetGen (Shao et al., 2023): T=2 sweet spot
      - IRAGKR: retrieval gating by quality signal

    Args:
        iteration: Current CoT iteration (1-indexed).
        reasoning_next_queries: From analyze_iteration's ReasoningStep.
        plan_step2: V2 analysis queries (from QueryPlan).
        plan_step3: V2 verification queries (from QueryPlan).
        unchecked_assumptions: V1 assumptions not yet verified.
        coverage_gaps: From phi1_coverage_gaps post-search.
        search_perspectives: V1 perspectives not yet searched.
        max_queries: Maximum queries to return.
        info_gain: Previous iteration's information gain (0.0-1.0).
            None = first iteration or not measured (triggers fallback).
        saturation_threshold: Below this, info_gain is considered saturated.
            Default 0.035 matches engine.py's saturation_threshold.

    Returns:
        QueryFeedback with enhanced, merged queries.
    """
    feedback = QueryFeedback()
    candidates: list[tuple[str, str, float]] = []  # (query, source, priority)

    # Priority 1: Reasoning-derived queries (highest — LLM analyzed gaps)
    for q in (reasoning_next_queries or []):
        candidates.append((q, "reasoning_trace", 1.0))

    # Priority 2: QPP-based adaptive strategy selection
    strategy = _select_strategy(
        iteration, info_gain, saturation_threshold, qpp_high_multiplier,
    )
    feedback.strategy = strategy

    if strategy == "narrowing" and plan_step2:
        for q in plan_step2:
            candidates.append((q, "plan_step2", 0.8))
        feedback.plan_injected = True
    elif strategy == "verification" and plan_step3:
        for q in plan_step3:
            candidates.append((q, "plan_step3", 0.8))
        feedback.plan_injected = True
    elif strategy == "assumption_check":
        # Saturated on main line: inject unchecked assumptions as queries
        if unchecked_assumptions:
            for assumption in unchecked_assumptions[:2]:
                q = f"evidence for or against: {assumption}"
                candidates.append((q, "v1_assumption", 0.7))
        # Also inject unused perspectives
        if search_perspectives:
            for perspective in search_perspectives[:1]:
                q = f"{perspective} perspective on"
                candidates.append((q, "v1_perspective", 0.6))

    # Priority 3: Coverage gap queries
    if coverage_gaps:
        for gap in coverage_gaps:
            # Convert gap description to search query
            q = _gap_to_query(gap)
            if q:
                candidates.append((q, "coverage_gap", 0.5))
                feedback.gap_queries.append(q)

    # Deduplicate and sort by priority
    seen: set[str] = set()
    sorted_candidates = sorted(candidates, key=lambda x: -x[2])

    for query, source, _priority in sorted_candidates:
        q_lower = query.lower().strip()
        if q_lower not in seen and len(q_lower) > 5:
            seen.add(q_lower)
            feedback.queries.append(query)
            feedback.sources[query] = source
            if len(feedback.queries) >= max_queries:
                break

    if feedback.queries:
        source_summary = ", ".join(
            f"{s}={sum(1 for v in feedback.sources.values() if v == s)}"
            for s in dict.fromkeys(feedback.sources.values())
        )
        logger.info(
            "Φ7 Feedback [iter %d, strategy=%s]: %d queries (%s)%s",
            iteration,
            strategy,
            len(feedback.queries),
            source_summary,
            " +plan" if feedback.plan_injected else "",
        )

    return feedback


def _select_strategy(
    iteration: int,
    info_gain: float | None,
    saturation_threshold: float,
    qpp_high_multiplier: float = 3.0,
) -> str:
    """Select V5 injection strategy based on QPP info_gain signal.

    Returns one of: 'narrowing', 'verification', 'assumption_check'.
    """
    if info_gain is not None:
        # QPP-based adaptive selection
        high_threshold = saturation_threshold * qpp_high_multiplier
        if info_gain > high_threshold:
            return "narrowing"
        elif info_gain > saturation_threshold:
            return "verification"
        else:
            return "assumption_check"

    # Fallback: legacy iteration-based strategy (backward compat)
    if iteration <= 1:
        return "narrowing"
    elif iteration == 2:
        return "verification"
    else:
        return "assumption_check"


def _gap_to_query(gap_description: str) -> str:
    """Convert a coverage gap description to a search query.

    Handles common gap patterns from phi1_coverage_gaps:
      - "All results from single source 'X'" → broader search
      - "Source diversity low (N%)" → diversity-focused search
      - "Academic query but no academic sources" → academic search
    """
    gap_lower = gap_description.lower()

    if "single source" in gap_lower:
        return ""  # Can't fix this with a query change
    if "academic" in gap_lower and "no academic" in gap_lower:
        return "peer-reviewed study"
    if "diversity low" in gap_lower:
        return ""  # Source diversity is a source selection problem
    if "broadening" in gap_lower:
        return ""  # Already suggested by gap

    # Generic: use the gap description as context
    return ""
