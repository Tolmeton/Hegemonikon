from __future__ import annotations
# PROOF: mekhane/periskope/cognition/phase_inversion.py
# PURPOSE: periskope モジュールの phase_inversion
"""
Phase Inversion — Multi-scale refutation for Periskopē.

VISION §7: Phase Inversion = inverting the objective function.
Normal:  f(query) = argmax P(evidence | supports query)
Inverted: f̄(query) = argmax P(evidence | refutes query)

This module implements L0 (query inversion) and L1 (step inversion).
L2 (pipeline inversion / DialecticEngine) is in dialectic.py.
L3 (session inversion / /vet) is existing.

Scale Axiom: the same operation repeats fractally at every layer.
"""


import logging
import re
from dataclasses import dataclass, field

from mekhane.periskope.cognition._llm import llm_ask as _llm_ask

# PURPOSE: Týpos プロンプトローダー
from mekhane.periskope.prompts import load_prompt

logger = logging.getLogger(__name__)


@dataclass
class AdvocatusChallenge:
    """Result of a phase inversion challenge (L1 step inversion).

    The Advocatus Diaboli challenges the current synthesis by:
    1. Identifying refutable claims (refutation_points)
    2. Generating search queries to find counter-evidence (counter_queries)
    3. Adjusting confidence downward if warranted (challenged_confidence)
    """

    refutation_points: list[str] = field(default_factory=list)
    counter_queries: list[str] = field(default_factory=list)
    challenged_confidence: float = 0.0

    def summary(self) -> str:
        """One-line summary for logging."""
        return (
            f"[advocatus] "
            f"refutations={len(self.refutation_points)} "
            f"counter_queries={len(self.counter_queries)} "
            f"challenged_conf={self.challenged_confidence:.0%}"
        )


async def advocatus_challenge(
    query: str,
    synthesis_text: str,
    current_confidence: float,
    max_refutations: int = 3,
    max_counter_queries: int = 2,
    model: str = "gemini-3-flash-preview",
) -> AdvocatusChallenge:
    """L1 Step Inversion: challenge the current synthesis.

    Called within each CoT iteration to actively seek refutation
    of the provisional answer. This is N-2 Column C (Counter)
    externalized at the search pipeline level.

    Args:
        query: Original research query.
        synthesis_text: Current synthesis text to challenge.
        current_confidence: Current confidence (0.0-1.0).
        max_refutations: Maximum refutation points to generate.
        max_counter_queries: Maximum counter-evidence queries.
        model: LLM model for challenge generation.

    Returns:
        AdvocatusChallenge with refutation points and counter queries.
    """
    prompt = _build_challenge_prompt(
        query, synthesis_text, current_confidence,
        max_refutations, max_counter_queries,
    )

    raw = await _llm_ask(prompt, model=model, max_tokens=512)

    if not raw:
        logger.warning("Advocatus challenge returned empty")
        return AdvocatusChallenge(challenged_confidence=current_confidence)

    challenge = _parse_challenge(raw, current_confidence)
    logger.info("Phase Inversion L1: %s", challenge.summary())

    return challenge


def _build_challenge_prompt(
    query: str,
    synthesis_text: str,
    current_confidence: float,
    max_refutations: int,
    max_counter_queries: int,
) -> str:
    """Build the adversarial challenge prompt."""
    template = load_prompt("phase_inversion_challenge.typos")
    if template:
        return template.format(
            query=query,
            synthesis_text=synthesis_text[:3000],
            current_confidence=f"{current_confidence:.0%}",
            max_refutations=max_refutations,
            max_counter_queries=max_counter_queries,
        )

    # Fallback: hardcoded prompt
    return (
        "You are the Advocatus Diaboli — a rigorous devil's advocate.\n"
        "Your role is to find weaknesses, counter-evidence, and refutable claims\n"
        "in the following research synthesis.\n\n"
        "IMPORTANT: You are NOT trying to be negative for its own sake.\n"
        "You are seeking TRUTH by stress-testing the provisional answer.\n"
        "If the answer is actually solid, say so — but try hard to find flaws first.\n\n"
        f"## Research Question\n{query}\n\n"
        f"## Current Synthesis (confidence: {current_confidence:.0%})\n"
        f"{synthesis_text[:3000]}\n\n"
        "## Your Task\n"
        "Analyze this synthesis and identify its weaknesses.\n\n"
        f"REFUTATIONS:\n"
        f"- (list up to {max_refutations} specific claims that could be wrong, "
        f"unsupported, or missing nuance)\n"
        f"(write NONE if the synthesis is solid)\n\n"
        f"COUNTER_QUERIES:\n"
        f"- (list up to {max_counter_queries} search queries that would find "
        f"evidence AGAINST the synthesis's conclusions)\n"
        f"(write NONE if no counter-evidence is likely)\n\n"
        "CHALLENGED_CONFIDENCE: (integer 0-100, your assessment of how confident "
        "we SHOULD be given the weaknesses you found. "
        f"Current confidence is {int(current_confidence * 100)}%)\n"
    )


def _parse_challenge(raw: str, fallback_confidence: float) -> AdvocatusChallenge:
    """Parse LLM output into AdvocatusChallenge."""
    challenge = AdvocatusChallenge()

    challenge.refutation_points = _extract_items(raw, "REFUTATIONS")
    challenge.counter_queries = _extract_items(raw, "COUNTER_QUERIES")

    # Extract challenged confidence
    conf_match = re.search(
        r"CHALLENGED_CONFIDENCE[:\s*]*(\d+)",
        raw, re.IGNORECASE,
    )
    if conf_match:
        challenge.challenged_confidence = int(conf_match.group(1)) / 100.0
    else:
        challenge.challenged_confidence = fallback_confidence

    return challenge


def _extract_items(text: str, header: str) -> list[str]:
    """Extract bullet points from a named section (shared with reasoning_trace)."""
    lines = text.split("\n")
    header_upper = header.upper()
    in_section = False
    items = []

    for line in lines:
        stripped = line.strip()
        # Detect section headers: REFUTATIONS:, **REFUTATIONS**, ## REFUTATIONS
        cleaned = re.sub(r"[#*:\s]", "", stripped).upper()
        if cleaned == header_upper:
            in_section = True
            continue
        # Detect OTHER section headers (stop collecting)
        if in_section and re.match(r"^(?:#{1,3}\s*)?[*]{0,2}[A-Z_]{3,}[*]{0,2}:?\s*$", stripped):
            break

        if in_section:
            # Extract bullet items
            if stripped.startswith("- "):
                item = stripped[2:].strip()
            elif stripped.startswith("* "):
                item = stripped[2:].strip()
            elif re.match(r"^\d+\.\s+", stripped):
                item = re.sub(r"^\d+\.\s+", "", stripped).strip()
            else:
                continue

            if item and not re.match(r"^none\.?\s*$", item, re.IGNORECASE):
                items.append(item)

    return items


# --- L0: Query Inversion ---

async def invert_queries(
    query: str,
    claims: list[str],
    max_queries: int = 2,
    model: str = "gemini-3-flash-preview",
) -> list[str]:
    """L0 Query Inversion: generate queries that seek to refute specific claims.

    Enhanced version of phi1_counterfactual — instead of generic
    "what if the opposite were true?", this targets specific claims
    extracted from the synthesis.

    Args:
        query: Original research query.
        claims: Specific claims to target for refutation.
        max_queries: Maximum number of inverted queries.
        model: LLM model.

    Returns:
        List of search queries designed to find counter-evidence.
    """
    if not claims:
        return []

    claims_text = "\n".join(f"- {c}" for c in claims[:5])

    template = load_prompt("phase_inversion_queries.typos")
    if template:
        prompt = template.format(
            query=query,
            claims_text=claims_text,
            max_queries=max_queries,
        )
    else:
        # Fallback: hardcoded prompt
        prompt = (
            "Generate search queries that would find evidence AGAINST "
            "the following claims. The queries should be specific and searchable.\n\n"
            f"## Original Question\n{query}\n\n"
            f"## Claims to Refute\n{claims_text}\n\n"
            f"Generate up to {max_queries} search queries, one per line.\n"
            "Format: one query per line, no bullets or numbering.\n"
        )

    raw = await _llm_ask(prompt, model=model, max_tokens=256)

    if not raw:
        return []

    queries = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        # Remove numbering/bullets
        line = re.sub(r"^[\d\.\-\*\)]+\s*", "", line).strip()
        if line and len(line) > 10:
            queries.append(line)
        if len(queries) >= max_queries:
            break

    return queries
