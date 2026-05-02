from __future__ import annotations
# PROOF: mekhane/periskope/cognition/phi0_intent_decompose.py
# PURPOSE: periskope モジュールの phi0_intent_decompose
"""
Φ0: 意図分解 (Intent Decomposition) — クエリ形成の基底射。

Design: /noe+ Periskopē クエリ形成分析 (2026-02-28)
  V1: 「良いクエリ = 意図分解 + 時間的展開 + ソース適応 + 深度制御 + フィードバック」
  意図分解は他の全射の基盤。

PURPOSE: ユーザーの自然言語クエリを構造化された意図に分解し、
後段の Φ1-Φ4 がより精密に動作するための基盤情報を提供する。

Principle I (Cognitive Sovereignty): 分解結果は「提案」であり、
ユーザーの意図を置き換えるものではない。
"""


import json
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

from mekhane.periskope.cognition._llm import llm_ask as _llm_ask

# PURPOSE: Týpos プロンプトローダー
from mekhane.periskope.prompts import load_prompt


@dataclass
class IntentDecomposition:
    """Φ0 output: Structured intent decomposition of a search query.

    Each field guides downstream cognitive phases:
      - core_concepts → Φ1 blind spot analysis uses these to check coverage
      - evidence_type → Φ3 context setting uses this for source selection
      - implicit_assumptions → Φ1 counterfactual query generation
      - search_perspectives → Φ2 divergent thinking seeds
      - negation_queries → Φ4 pre-search ranking diversity
    """

    # Core concepts extracted from the query (nouns, entities, relationships)
    core_concepts: list[str] = field(default_factory=list)

    # What kind of evidence/information the user is seeking
    evidence_type: str = ""

    # Assumptions the query implicitly makes
    implicit_assumptions: list[str] = field(default_factory=list)

    # Different perspectives/angles from which to search
    search_perspectives: list[str] = field(default_factory=list)

    # Queries that would find counter-evidence or alternative viewpoints
    negation_queries: list[str] = field(default_factory=list)

    # Confidence in the decomposition (0.0-1.0)
    confidence: float = 0.0

    def to_context_string(self) -> str:
        """Format decomposition as context string for downstream Φ phases.

        This is injected into Φ1 blind-spot analysis context to improve
        the quality of blind spot detection.
        """
        parts: list[str] = []
        if self.core_concepts:
            parts.append(f"Core concepts: {', '.join(self.core_concepts)}")
        if self.evidence_type:
            parts.append(f"Evidence sought: {self.evidence_type}")
        if self.implicit_assumptions:
            parts.append(f"Assumptions: {'; '.join(self.implicit_assumptions)}")
        if self.search_perspectives:
            parts.append(f"Perspectives: {'; '.join(self.search_perspectives)}")
        return "\n".join(parts)


_DECOMPOSE_PROMPT = """\
You are an intent decomposition engine for a deep research system.
Given a search query, extract its structured intent.

Query: {query}

Return a JSON object with these fields:
{{
  "core_concepts": ["concept1", "concept2", ...],
  "evidence_type": "what kind of evidence the user wants (e.g., empirical studies, tutorials, comparisons, theoretical frameworks, implementations)",
  "implicit_assumptions": ["assumption1", "assumption2", ...],
  "search_perspectives": ["perspective1", "perspective2", ...],
  "negation_queries": ["counter-query1", "counter-query2"]
}}

Rules:
- core_concepts: Extract 2-5 key nouns/entities/relationships. Be specific.
- evidence_type: ONE phrase describing the kind of information sought.
- implicit_assumptions: 1-3 things the query takes for granted.
- search_perspectives: 2-4 different angles to search from.
- negation_queries: 1-2 queries that would find counter-arguments or alternatives.

Return ONLY the JSON object, no explanation."""


async def phi0_intent_decompose(
    query: str,
    context: str = "",
) -> IntentDecomposition:
    """Φ0: Decompose query intent into structured components.

    Runs before Φ1 in the cognitive pipeline. Results are injected
    into Φ1's context to improve blind-spot detection quality.

    Args:
        query: Original research query.
        context: Optional additional context (e.g., from NL API entities).

    Returns:
        IntentDecomposition with structured intent components.
        On failure, returns an empty IntentDecomposition (graceful degradation).
    """
    template = load_prompt("phi0_intent_decompose.typos")
    if template:
        prompt = template.format(query=query)
    else:
        prompt = _DECOMPOSE_PROMPT.format(query=query)
    if context:
        prompt += f"\n\nAdditional context:\n{context}"

    text = await _llm_ask(
        prompt,
        model="gemini-3-flash-preview",  # Fast model — this is pre-processing
        max_tokens=512,
    )

    if not text:
        logger.warning("Φ0: Intent decomposition returned empty response")
        return IntentDecomposition()

    try:
        # Strip markdown code fences if present
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first and last lines (```json and ```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        data = json.loads(cleaned)

        result = IntentDecomposition(
            core_concepts=data.get("core_concepts", [])[:5],
            evidence_type=data.get("evidence_type", ""),
            implicit_assumptions=data.get("implicit_assumptions", [])[:3],
            search_perspectives=data.get("search_perspectives", [])[:4],
            negation_queries=data.get("negation_queries", [])[:2],
            confidence=0.8,  # LLM-based decomposition
        )

        logger.info(
            "Φ0: Intent decomposed — %d concepts, evidence=%r, %d assumptions, %d perspectives",
            len(result.core_concepts),
            result.evidence_type[:50],
            len(result.implicit_assumptions),
            len(result.search_perspectives),
        )

        return result

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning("Φ0: Failed to parse intent decomposition: %s", e)
        return IntentDecomposition()
