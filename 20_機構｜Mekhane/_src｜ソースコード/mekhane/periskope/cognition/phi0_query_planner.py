from __future__ import annotations
# PROOF: mekhane/periskope/cognition/phi0_query_planner.py
# PURPOSE: periskope モジュールの phi0_query_planner
"""
Φ0 Query Planner — V2 先読み連鎖 (Lookahead Query Chaining).

Design: /noe+ Periskopē クエリ形成分析 (2026-02-28)
  V2: 「問いの連鎖 — 単一クエリではなく問いの系列が良いクエリの本質」

PURPOSE: 初期クエリの時点で検索の「3手先」を読み、
段階的に深化するクエリ計画を生成する。

CoT Search Chain (reasoning_trace.py) は検索結果を見てから
次のクエリを考えるが、V2 は検索前に計画を立てる点が異なる。
両者は補完的: V2 の計画が CoT の初期方向を設定する。

Principle II (Support ≠ Replacement): 計画はあくまでガイド。
実際の CoT ループが結果を見て修正する。
"""


import json
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

from mekhane.periskope.cognition._llm import llm_ask as _llm_ask

# PURPOSE: Týpos プロンプトローダー
from mekhane.periskope.prompts import load_prompt


@dataclass
class QueryPlan:
    """Φ0 output: Multi-step query plan for iterative deepening.

    Each step represents a search phase with a distinct purpose.
    The plan guides CoT Search Chain (reasoning_trace.py) by
    providing initial direction before any search results exist.
    """

    # Step 1: Overview/survey queries (broad, exploratory)
    step1_survey: list[str] = field(default_factory=list)

    # Step 2: Comparison/analysis queries (narrowing, comparative)
    step2_analysis: list[str] = field(default_factory=list)

    # Step 3: Verification/detail queries (precise, evidential)
    step3_verification: list[str] = field(default_factory=list)

    # Confidence in the plan
    confidence: float = 0.0

    # Brief reasoning for the plan structure
    reasoning: str = ""

    def all_queries(self) -> list[str]:
        """Return all planned queries in execution order."""
        return self.step1_survey + self.step2_analysis + self.step3_verification

    def step1_as_candidates(self) -> list[str]:
        """Return step 1 queries as immediate search candidates.

        Only step 1 is used for initial search. Steps 2-3 are stored
        in the QueryPlan and used by CoT Search Chain when it needs
        next-iteration queries (if the reasoning trace doesn't produce
        better alternatives from actual results).
        """
        return list(self.step1_survey)


_PLAN_PROMPT = """\
You are a research strategist planning a 3-step search investigation.

Research query: {query}
{context_section}
Plan a systematic search strategy with 3 phases:

1. SURVEY: 1-2 queries to understand the landscape — what approaches exist, who are the key authors, what frameworks are used
2. ANALYSIS: 1-2 queries to investigate specific aspects — compare approaches, examine mechanisms, probe limitations
3. VERIFICATION: 1-2 queries to verify claims, find counter-evidence, or discover alternatives

Return a JSON object:
{{
  "step1_survey": ["survey query 1", "survey query 2"],
  "step2_analysis": ["analysis query 1", "analysis query 2"],
  "step3_verification": ["verification query 1"],
  "reasoning": "one-line explanation of the strategy"
}}

Rules:
- Each query must be a natural-language question or investigation request (NOT a keyword list)
- Include context: what you already know, what specific aspect you're investigating, why
- Step 2 queries should assume step 1 has revealed the landscape
- Step 3 queries should challenge or verify what steps 1-2 would find
- Bad example: "linear probing LLM hidden states structural" (keyword soup)
- Good example: "What methods beyond linear probing have been used to extract structural information from LLM hidden states? I know about Hewitt & Manning (2019) structural probes."
- Return ONLY the JSON object"""


async def phi0_query_plan(
    query: str,
    context: str = "",
    intent_context: str = "",
) -> QueryPlan:
    """Φ0: Generate a 3-step query plan for iterative deepening.

    Runs after intent decomposition (V1) in the cognitive pipeline.
    Results guide the CoT Search Chain's initial direction.

    Args:
        query: Original research query.
        context: Optional context (e.g., from NL API, past searches).
        intent_context: Structured intent from phi0_intent_decompose.

    Returns:
        QueryPlan with 3-step search strategy.
        On failure, returns an empty QueryPlan (graceful degradation).
    """
    context_section = ""
    if intent_context:
        context_section = f"\nKnown context:\n{intent_context}\n"
    elif context:
        context_section = f"\nAdditional context:\n{context}\n"

    template = load_prompt("phi0_query_plan.typos")
    if template:
        prompt = template.format(query=query, context_section=context_section)
    else:
        prompt = _PLAN_PROMPT.format(query=query, context_section=context_section)

    text = await _llm_ask(
        prompt,
        model="gemini-3-flash-preview",
        max_tokens=512,
    )

    if not text:
        logger.warning("Φ0 query planner: empty response")
        return QueryPlan()

    try:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        data = json.loads(cleaned)

        result = QueryPlan(
            step1_survey=data.get("step1_survey", [])[:2],
            step2_analysis=data.get("step2_analysis", [])[:2],
            step3_verification=data.get("step3_verification", [])[:2],
            reasoning=data.get("reasoning", ""),
            confidence=0.75,
        )

        total = len(result.step1_survey) + len(result.step2_analysis) + len(result.step3_verification)
        logger.info(
            "Φ0 QueryPlan: %d queries across 3 steps — %s",
            total,
            result.reasoning[:80] if result.reasoning else "(no reasoning)",
        )

        return result

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning("Φ0 query planner: parse failed: %s", e)
        return QueryPlan()
