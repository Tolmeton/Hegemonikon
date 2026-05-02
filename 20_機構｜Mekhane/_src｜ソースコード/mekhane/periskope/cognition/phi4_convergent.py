from __future__ import annotations
# PROOF: mekhane/periskope/cognition/phi4_convergent.py
# PURPOSE: periskope モジュールの phi4_convergent
"""
Φ4: 収束思考 (A2 Krisis) — Convergent thinking.

Design: Search Cognition Theory §2.2 (kernel/search_cognition.md)

Two roles:
  1. PRE-SEARCH: Rank query candidates by EFE approximation (ε + π)
     → Select the best queries to actually search
  2. POST-SEARCH: Frame synthesis results into actionable decisions
     → Existing _phi4_convergent_framing, relocated here

Φ4 is "Exploitation" in the Function axiom (Explore ↔ Exploit).
After Φ2 (Explore) expands the space, Φ4 contracts it to the highest-value queries.

IMPORTANT: Φ4 RANKS, it does not FILTER. All candidates flow to search,
but top-ranked candidates get priority. We never kill Φ2's divergent output.
"""


import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# PURPOSE: [L2-auto] RankedQuery のクラス定義
@dataclass
class RankedQuery:
    """A query candidate with EFE-approximate scoring."""

    query: str
    score: float  # 0.0-1.0, higher = more promising
    category: str = ""  # "original", "blind_spot", "divergent", "translation"
    reason: str = ""


# PURPOSE: [L2-auto] DecisionFrame のクラス定義
@dataclass
class DecisionFrame:
    """Φ4 post-search: Structured decision framework from synthesis."""

    key_findings: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    decision_options: list[str] = field(default_factory=list)
    confidence: float = 0.0


# PURPOSE: [L2-auto] _llm_ask の共通モジュール参照
from mekhane.periskope.cognition._llm import llm_ask as _llm_ask

# PURPOSE: Týpos プロンプトローダー
from mekhane.periskope.prompts import load_prompt


# PURPOSE: [L2-auto] phi4_pre_search_ranking の非同期処理定義
async def phi4_pre_search_ranking(
    original_query: str,
    candidates: list[str],
    max_queries: int = 5,
    known_context: str = "",
) -> list[RankedQuery]:
    """Φ4 pre-search: Rank query candidates by information value.

    Uses EFE approximation:
      score ≈ ε (epistemic novelty) + π (pragmatic relevance)

    The LLM estimates how much NEW information each query would yield
    and how relevant it is to the original research goal.

    G3 mitigation (search_cognition.md §7.1): When known_context is provided,
    the LLM estimates novelty relative to what the researcher already knows,
    not what the LLM considers novel. This improves ε estimation accuracy.

    Args:
        original_query: The original research query (goal anchor).
        candidates: All query candidates from Φ1 + Φ2.
        max_queries: How many top queries to highlight (all are returned).
        known_context: What the researcher already knows about this topic.
            Used to improve NOVELTY scoring by distinguishing 'novel to researcher'
            from 'novel to LLM'.

    Returns:
        All candidates as RankedQuery, sorted by score descending.
        The top max_queries are the recommended search queries.
    """
    if len(candidates) <= 1:
        return [RankedQuery(query=candidates[0], score=1.0, category="original")]

    # Build numbered candidate list
    numbered = "\n".join(f"[{i+1}] {c}" for i, c in enumerate(candidates))

    # G3: Include known context for better novelty estimation
    context_block = ""
    if known_context:
        # Load max length from config (default 2000)
        try:
            from mekhane.periskope.config_loader import load_config
            max_ctx_len = load_config().get("known_context_max_length", 2000)
        except Exception:  # noqa: BLE001
            max_ctx_len = 2000
        ctx = known_context[:max_ctx_len]
        context_block = (
            f"\nThe researcher already knows:\n{ctx}\n\n"
            "IMPORTANT: NOVELTY should measure what is NEW TO THE RESEARCHER, "
            "not what is new to you. If the researcher already knows something, "
            "queries about it have LOW novelty.\n"
        )

    template = load_prompt("phi4_pre_search_ranking.typos")
    if template:
        prompt = template.format(
            original_query=original_query,
            numbered_candidates=numbered,
            context_block=context_block,
        )
    else:
        # Fallback: hardcoded prompt
        prompt = (
            "You are a research strategist estimating the information value of search queries.\n\n"
            f"Research goal: {original_query}\n"
            f"{context_block}\n"
            f"Query candidates:\n{numbered}\n\n"
            "For each candidate, estimate:\n"
            "- NOVELTY (0-10): How much NEW information would this query reveal?\n"
            "- RELEVANCE (0-10): How directly does this serve the research goal?\n\n"
            "Return ONE LINE per candidate in format: [number] novelty relevance\n"
            "Example: [1] 7 9\n"
            "No explanation, just numbers."
        )

    text = await _llm_ask(prompt, max_tokens=256)

    ranked: list[RankedQuery] = []
    scores_parsed = False

    if text:
        import re
        for line in text.strip().split("\n"):
            match = re.match(r"\[?(\d+)\]?\s+(\d+)\s+(\d+)", line.strip())
            if match:
                idx = int(match.group(1)) - 1
                novelty = min(int(match.group(2)), 10)
                relevance = min(int(match.group(3)), 10)
                if 0 <= idx < len(candidates):
                    # D4: Dynamic ε/π weighting (G5 mitigation)
                    # When known_context is substantial, emphasize novelty (ε)
                    # to discover NEW information beyond what's already known
                    # Fix: replaced magic number 100 char length with 10 word count proxy
                    is_context_rich = bool(known_context) and len(str(known_context).split()) >= 10
                    if is_context_rich:
                        w_novelty, w_relevance = 0.6, 0.4
                    else:
                        w_novelty, w_relevance = 0.5, 0.5
                    score = (w_novelty * novelty + w_relevance * relevance) / 10.0
                    category = "original" if idx == 0 else "divergent"
                    ranked.append(RankedQuery(
                        query=candidates[idx],
                        score=score,
                        category=category,
                        reason=f"ε={novelty}/10 (w={w_novelty}), π={relevance}/10 (w={w_relevance})",
                    ))
                    scores_parsed = True

    # Fallback: if LLM scoring failed, use position-based defaults
    if not scores_parsed:
        logger.warning("Φ4: LLM scoring failed, using position-based fallback")
        for i, c in enumerate(candidates):
            score = max(0.1, 1.0 - (i * 0.1))
            ranked.append(RankedQuery(
                query=c,
                score=score,
                category="original" if i == 0 else "divergent",
            ))

    # Sort by score descending
    ranked.sort(key=lambda r: r.score, reverse=True)

    # Filter out low-scoring candidates to prevent NDCG degradation
    # Original query is always kept regardless of score
    MIN_SCORE = 0.3
    filtered = [r for r in ranked if r.score >= MIN_SCORE or r.category == "original"]
    if len(filtered) < len(ranked):
        dropped = len(ranked) - len(filtered)
        logger.info("Φ4 pre-search: Dropped %d candidates below threshold %.1f", dropped, MIN_SCORE)
        ranked = filtered

    logger.info(
        "Φ4 pre-search: Ranked %d candidates. Top %d: %s",
        len(ranked),
        min(max_queries, len(ranked)),
        [(r.query[:40], f"{r.score:.2f}") for r in ranked[:max_queries]],
    )

    return ranked


# PURPOSE: [L2-auto] phi4_post_search_framing の非同期処理定義
async def phi4_post_search_framing(
    query: str,
    synthesis_texts: list[str],
) -> DecisionFrame:
    """Φ4 post-search: Frame synthesis into actionable decisions.

    Relocated from engine._phi4_convergent_framing().
    Produces key findings, open questions, and decision options.

    Args:
        query: Original research query.
        synthesis_texts: Content from multi-model synthesis.

    Returns:
        DecisionFrame with structured findings.
    """
    combined = "\n\n---\n\n".join(synthesis_texts[:3])

    template = load_prompt("phi4_post_search_framing.typos")
    if template:
        prompt = template.format(query=query, combined_synthesis=combined[:3000])
    else:
        # Fallback: hardcoded prompt
        prompt = (
            "You are a research analyst creating a decision framework.\n\n"
            f"Research query: {query}\n\n"
            f"Synthesis:\n{combined[:3000]}\n\n"
            "Extract:\n"
            "KEY FINDINGS: (3-5 bullet points of established facts)\n"
            "OPEN QUESTIONS: (2-3 unresolved questions)\n"
            "DECISION OPTIONS: (2-3 actionable next steps)\n"
            "CONFIDENCE: (0-100%)\n\n"
            "Use this exact format with labels."
        )

    text = await _llm_ask(prompt, model="gemini-3.1-pro-preview", max_tokens=512)

    frame = DecisionFrame()

    if not text:
        return frame

    import re

    # Parse sections
    current_section: str | None = None
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        upper = line.upper()
        if "KEY FINDING" in upper:
            current_section = "findings"
            continue
        elif "OPEN QUESTION" in upper:
            current_section = "questions"
            continue
        elif "DECISION OPTION" in upper or "NEXT STEP" in upper:
            current_section = "options"
            continue
        elif "CONFIDENCE" in upper:
            match = re.search(r"(\d+)", line)
            if match:
                frame.confidence = min(int(match.group(1)), 100) / 100.0
            continue

        # Clean bullet points
        if line.startswith(("- ", "• ", "* ")):
            line = line[2:].strip()
        elif line[0].isdigit() and len(line) > 2 and line[1] in ".):":
            line = line[2:].strip()

        if line and current_section == "findings":
            frame.key_findings.append(line)
        elif line and current_section == "questions":
            frame.open_questions.append(line)
        elif line and current_section == "options":
            frame.decision_options.append(line)

    logger.info(
        "Φ4 post-search: %d findings, %d questions, confidence=%.0f%%",
        len(frame.key_findings), len(frame.open_questions), frame.confidence * 100,
    )

    return frame
