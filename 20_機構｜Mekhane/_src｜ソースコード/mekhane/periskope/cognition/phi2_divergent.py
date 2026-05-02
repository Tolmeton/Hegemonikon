from __future__ import annotations
# PROOF: mekhane/periskope/cognition/phi2_divergent.py
# PURPOSE: periskope モジュールの phi2_divergent
"""
Φ2: 拡散思考 (O3 Zētēsis) — Divergent thinking.

Design: Search Cognition Theory §2.2 (kernel/search_cognition.md)

Expands the query space by generating diverse query candidates:
  1. Synonym/paraphrase expansion
  2. Adjacent concept exploration
  3. Multi-perspective query generation (optimistic/critical/historical/practical)

The goal is to maximize Epistemic Value (ε) in EFE:
  G(π) = -ε (info gain) - π (pragmatic value)
  Φ2 maximizes ε by exploring the broadest possible query space.

Φ2 is "Exploration" in the Function axiom (Explore ↔ Exploit).
"""


import logging

logger = logging.getLogger(__name__)


# PURPOSE: [L2-auto] _llm_ask の共通モジュール参照
from mekhane.periskope.cognition._llm import llm_ask as _llm_ask

# PURPOSE: Týpos プロンプトローダー
from mekhane.periskope.prompts import load_prompt


# PURPOSE: [L2-auto] phi2_divergent_thinking の非同期処理定義
async def phi2_divergent_thinking(
    query: str,
    expanded_queries: list[str] | None = None,
    max_candidates: int = 5,
    depth: int = 2,
) -> list[str]:
    """Φ2: Divergent thinking — expand the query space.

    Generates diverse query candidates by exploring synonyms,
    adjacent concepts, and multiple perspectives. This is the
    "Exploration" phase — breadth over depth.

    Args:
        query: Original research query.
        expanded_queries: Already-expanded queries from W3 (QueryExpander).
            These are included in the output but not regenerated.
        max_candidates: Maximum total query candidates (including original).
            Default reduced from 8 to 5 to prevent irrelevant result dilution.
        depth: Research depth (2=Standard uses 3 categories, 3=Deep uses 5).

    Returns:
        List of query candidates (original + expanded + divergent).
        Deduplicated and capped at max_candidates.
    """
    # Start with what we have
    candidates: list[str] = [query]
    if expanded_queries:
        for eq in expanded_queries:
            if eq.lower() != query.lower():
                candidates.append(eq)

    # Generate divergent queries via LLM
    remaining = max_candidates - len(candidates)
    if remaining <= 0:
        return candidates[:max_candidates]

    # depth=2: core 3 categories, depth=3: all 5 categories
    if depth >= 3:
        categories = (
            "1. SYNONYMS: Rephrase using different terminology\n"
            "2. ADJACENT: Explore related but distinct concepts\n"
            "3. CRITICAL: Queries that would find counterarguments or limitations\n"
            "4. HISTORICAL: How has this topic evolved? Predecessor concepts?\n"
            "5. PRACTICAL: Real-world applications, implementations, case studies\n"
        )
    else:
        categories = (
            "1. SYNONYMS: Rephrase using different terminology\n"
            "2. ADJACENT: Explore related but distinct concepts\n"
            "3. CRITICAL: Queries that would find counterarguments or limitations\n"
        )

    template = load_prompt("phi2_divergent_thinking.typos")
    if template:
        prompt = template.format(query=query, remaining=remaining, categories=categories)
    else:
        # Fallback: hardcoded prompt
        prompt = (
            "You are a research query strategist. Given a research query, "
            "generate diverse alternative search queries that would uncover "
            "different aspects of the topic.\n\n"
            f"Original query: {query}\n\n"
            f"Generate queries in these categories:\n{categories}\n"
            "IMPORTANT: Only generate queries DIRECTLY relevant to the original "
            "research goal. Do NOT generate tangentially related queries.\n\n"
            f"Return {remaining} queries, one per line. No numbering, no labels.\n"
            "Each query should be a complete, standalone search query.\n"
            "Use the SAME LANGUAGE as the original query.\n"
            "Avoid duplicate concepts — each query should target a DIFFERENT facet."
        )

    text = await _llm_ask(prompt, max_tokens=512)

    if text:
        existing_lower = {c.lower() for c in candidates}
        for line in text.strip().split("\n"):
            line = line.strip()
            # Strip common numbering patterns
            if line and len(line) > 2:
                if line[0].isdigit() and line[1] in ".):":
                    line = line[2:].strip()
                elif line.startswith("- "):
                    line = line[2:].strip()

            if line and len(line) > 5 and line.lower() not in existing_lower:
                candidates.append(line)
                existing_lower.add(line.lower())

            if len(candidates) >= max_candidates:
                break

    logger.info(
        "Φ2: Generated %d query candidates from %r (original + %d divergent)",
        len(candidates), query, len(candidates) - 1,
    )

    return candidates[:max_candidates]
