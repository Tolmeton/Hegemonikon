from __future__ import annotations
# PROOF: mekhane/periskope/cognition/phi1_blind_spot.py
# PURPOSE: periskope モジュールの phi1_blind_spot
"""
Φ1: 無知のリマインド (O1 Noēsis) — Blind-spot analysis.

Design: Search Cognition Theory §2.2 (kernel/search_cognition.md)
Principle I: Cognitive Sovereignty — we PRESENT blind spots, never REPLACE perception.

Support capabilities:
  1. Blind-spot query generation (LLM-based)
  2. Coverage gap detection (post-search, Shannon Entropy analysis)
  3. Counterfactual queries ("What if X were not true?")

The subject (Creator + Claude) decides whether a blind spot matters.
Periskopē only nudges — "here's a gap you might want to look at."
"""


import logging
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mekhane.periskope.models import SearchResult

logger = logging.getLogger(__name__)


# PURPOSE: [L2-auto] _llm_ask の共通モジュール参照
from mekhane.periskope.cognition._llm import llm_ask as _llm_ask

# PURPOSE: Týpos プロンプトローダー
from mekhane.periskope.prompts import load_prompt


# PURPOSE: [L2-auto] phi1_blind_spot_analysis の非同期処理定義
async def phi1_blind_spot_analysis(
    query: str,
    context: str = "",
) -> list[str]:
    """Φ1: Blind-spot analysis — detect query blind spots.

    Analyzes the query for implicit assumptions, missing perspectives,
    and alternative framings. Returns supplementary queries that cover
    the identified blind spots.

    This runs automatically inside the pipeline (L2+).
    Claude mediates (二重 Copilot 構造) — Creator is not interrupted.

    Args:
        query: Original research query.
        context: Optional additional context.

    Returns:
        List of 1-3 supplementary queries targeting blind spots.
    """
    template = load_prompt("phi1_blind_spot_analysis.typos")
    if template:
        prompt = template.format(query=query, context=context or "")
    else:
        # Fallback: hardcoded prompt
        prompt = (
            "You are an epistemic auditor. Analyze this research query for blind spots.\n\n"
            f"Query: {query}\n"
        )
        if context:
            prompt += f"Context: {context}\n"
        prompt += (
            "\nIdentify:\n"
            "1. IMPLICIT ASSUMPTIONS: What does this query take for granted?\n"
            "2. MISSING PERSPECTIVES: What viewpoints or disciplines are absent?\n"
            "3. ALTERNATIVE FRAMINGS: How else could this question be asked?\n\n"
            "Generate 1-3 supplementary search queries that would cover these blind spots.\n"
            "Each query should target a DIFFERENT blind spot.\n\n"
            "Return ONLY the queries, one per line. No numbering, no explanation.\n"
            "If no significant blind spots: NONE"
        )

    text = await _llm_ask(prompt, model="gemini-3.1-pro-preview", max_tokens=256)

    if not text or "NONE" in text.upper().strip():
        logger.info("Φ1: No significant blind spots detected for %r", query)
        return []

    blind_spot_queries = [
        line.strip()
        for line in text.strip().split("\n")
        if line.strip() and len(line.strip()) > 5
    ]
    blind_spot_queries = blind_spot_queries[:3]

    if blind_spot_queries:
        logger.info(
            "Φ1: Detected %d blind spots for %r: %s",
            len(blind_spot_queries), query, blind_spot_queries,
        )

    return blind_spot_queries


# PURPOSE: [L2-auto] phi1_coverage_gaps の関数定義
def phi1_coverage_gaps(
    query: str,
    results: list[SearchResult],
    source_counts: dict[str, int],
) -> list[str]:
    """Φ1 post-search: Detect coverage gaps via Shannon Entropy analysis.

    After a search round completes, analyzes whether results are
    clustered in a narrow domain or spread across diverse sources.
    Low entropy = potential blind spot in coverage.

    This is a nudge, not a mandate. The subject decides whether to act.

    Args:
        query: Original research query.
        results: Search results from the completed round.
        source_counts: Source name → result count mapping.

    Returns:
        List of gap descriptions (empty if coverage is adequate).
    """
    gaps: list[str] = []

    # Shannon Entropy of source distribution
    total = sum(source_counts.values())
    if total == 0:
        gaps.append("No results found — consider broadening the query")
        return gaps

    active_sources = {k: v for k, v in source_counts.items() if v > 0}
    if len(active_sources) <= 1:
        only_source = next(iter(active_sources.keys()), "unknown")
        gaps.append(
            f"All results from single source '{only_source}' — "
            f"consider adding more search engines"
        )

    # Calculate entropy
    entropy = 0.0
    for count in active_sources.values():
        p = count / total
        entropy -= p * math.log2(p)

    max_entropy = math.log2(len(active_sources)) if len(active_sources) > 1 else 0
    normalized = entropy / max_entropy if max_entropy > 0 else 0

    if normalized < 0.5 and len(active_sources) > 1:
        dominant = max(active_sources, key=active_sources.get)  # type: ignore[arg-type]
        gaps.append(
            f"Source diversity low ({normalized:.0%}) — "
            f"'{dominant}' dominates with {active_sources[dominant]}/{total} results"
        )

    # Check for missing expected source types
    query_lower = query.lower()
    academic_kw = {"paper", "arxiv", "研究", "論文", "study", "journal"}
    if any(kw in query_lower for kw in academic_kw):
        if "semantic_scholar" not in active_sources and "gnosis" not in active_sources:
            gaps.append("Academic query but no academic sources returned results")

    if gaps:
        logger.info("Φ1 coverage: %d gaps detected: %s", len(gaps), gaps)

    return gaps


# PURPOSE: [L2-auto] phi1_counterfactual_queries の非同期処理定義
async def phi1_counterfactual_queries(
    query: str,
    max_queries: int = 2,
) -> list[str]:
    """Φ1: Generate counterfactual queries.

    "What if X were not true?" — challenges the core assumption of the query.
    These make the subject aware of implicit assumptions they may not have questioned.

    Args:
        query: Original research query.
        max_queries: Maximum counterfactual queries to generate.

    Returns:
        List of counterfactual queries.
    """
    template = load_prompt("phi1_counterfactual_queries.typos")
    if template:
        prompt = template.format(query=query, max_queries=max_queries)
    else:
        # Fallback: hardcoded prompt
        prompt = (
            "Given this research query, generate counterfactual questions that "
            "challenge its core assumptions.\n\n"
            f"Query: {query}\n\n"
            "For each assumption the query makes, ask: 'What if this assumption were wrong?'\n"
            "Convert each challenge into a concrete search query.\n\n"
            f"Return ONLY {max_queries} queries, one per line. No explanation.\n"
            "If the query has no challengeable assumptions: NONE"
        )

    text = await _llm_ask(prompt, model="gemini-3.1-pro-preview", max_tokens=128)

    if not text or "NONE" in text.upper().strip():
        return []

    queries = [
        line.strip()
        for line in text.strip().split("\n")
        if line.strip() and len(line.strip()) > 5
    ]
    return queries[:max_queries]
