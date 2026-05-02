from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/prokataskeve/consistency_checker.py
"""
ConsistencyChecker — Contradiction detection and fix suggestion.

Contains:
  - detect_contradiction (Elenchos, I×-) — L3
  - suggest_fix (Diorthōsis, A×-) — L3
"""

import asyncio
import json
import logging

from mekhane.mcp.prokataskeve.models import (
    AmbiguitySpan,
    ContextSummary,
    Contradiction,
    FixSuggestion,
)

logger = logging.getLogger(__name__)


# =============================================================================
# L3: detect_contradiction (Elenchos)
# =============================================================================


_CONTRADICTION_PROMPT = (
    "Analyze the input text for internal contradictions or inconsistencies.\n"
    "Also check against the provided context for contradictions.\n\n"
    "Input: {input}\n"
    "Context: {context}\n\n"
    "If contradictions exist, reply as JSON array:\n"
    '[{{"description": "...", "span_a": "...", "span_b": "...", "severity": "low|medium|high"}}]\n'
    "If no contradictions, reply: []"
)


# PURPOSE: L3 矛盾検出 (Elenchos, I×- — 反証を通じて信念を弱める)
async def detect_contradiction(
    text: str,
    context: ContextSummary | None = None,
) -> list[Contradiction]:
    """L3 Detect contradictions within input and against known context.

    Uses LLM to identify:
      - Internal contradictions (within the input itself)
      - External contradictions (input vs session context/known facts)
    """
    try:
        from mekhane.mcp.prokataskeve.cortex_singleton import get_cortex
        client = get_cortex()
        if client is None:
            raise RuntimeError("CortexClient unavailable")

        ctx_text = context.summary_text if context else "なし"
        prompt = _CONTRADICTION_PROMPT.replace(
            "{input}", text[:500],
        ).replace(
            "{context}", ctx_text[:300],
        )

        response = await asyncio.to_thread(
            client.chat, message=prompt, model="gemini-3-flash-preview", timeout=5.0,
        )
        raw = response.text.strip().removeprefix("```json").removesuffix("```").strip()
        data = json.loads(raw)

        if isinstance(data, list):
            return [
                Contradiction(
                    description=str(item.get("description", "")),
                    span_a=str(item.get("span_a", "")),
                    span_b=str(item.get("span_b", "")),
                    severity=str(item.get("severity", "medium")),
                )
                for item in data
                if isinstance(item, dict)
            ]
    except Exception as e:  # noqa: BLE001
        logger.debug("Contradiction detection failed: %s", e)

    return []


# =============================================================================
# L3: suggest_fix (Diorthōsis)
# =============================================================================


# PURPOSE: L3 入力修正提案 (Diorthōsis, A×- — 誤りを修正する行動)
def suggest_fix(
    contradictions: list[Contradiction],
    ambiguities: list[AmbiguitySpan],
) -> list[FixSuggestion]:
    """L3 Generate fix suggestions for detected contradictions and ambiguities.

    Rule-based: converts detected issues into actionable suggestions.
    High-severity contradictions → "ask" (clarification request).
    Ambiguities → suggestion text from AmbiguitySpan.
    """
    suggestions: list[FixSuggestion] = []

    for contradiction in contradictions:
        if contradiction.severity == "high":
            suggestions.append(FixSuggestion(
                issue_type="contradiction",
                original=f"{contradiction.span_a} vs {contradiction.span_b}",
                suggestion=f"矛盾を検出: {contradiction.description}",
                action="ask",
            ))
        else:
            suggestions.append(FixSuggestion(
                issue_type="contradiction",
                original=f"{contradiction.span_a} vs {contradiction.span_b}",
                suggestion=f"軽微な矛盾: {contradiction.description}",
                action="warn",
            ))

    for ambiguity in ambiguities:
        suggestions.append(FixSuggestion(
            issue_type="ambiguity",
            original=ambiguity.text,
            suggestion=ambiguity.suggestion,
            action="ask" if ambiguity.ambiguity_type == "omitted_subject" else "warn",
        ))

    return suggestions
