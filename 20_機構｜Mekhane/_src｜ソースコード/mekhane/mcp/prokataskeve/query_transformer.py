from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/prokataskeve/query_transformer.py
"""
QueryTransformer — Query rewriting and diversification.

Contains:
  - rewrite_query (Tekhnē, A×Exploit) — L1
  - diversify_query (Skepsis, I×Explore) — L2
"""

import asyncio
import json
import logging
import re

from mekhane.mcp.prokataskeve.models import (
    Entity,
    IntentClassification,
    IntentType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# L1: rewrite_query (Tekhnē)
# =============================================================================


# PURPOSE: L1 クエリ書き換え (Tekhnē, A×Exploit — 既知解法で確実に成果を出す)
async def rewrite_query(
    text: str,
    intent: IntentClassification | None = None,
    entities: list[Entity] | None = None,
) -> list[str]:
    """L1 Rewrite query for optimal downstream processing.

    Uses the existing QueryExpander for bilingual expansion.
    Adds intent-based query sharpening.
    """
    queries = [text]

    # Try bilingual expansion via existing QueryExpander (singleton)
    try:
        from mekhane.periskope.query_expander import get_expander
        expander = get_expander()
        expanded_res = await expander.expand(text)
        if isinstance(expanded_res, list) and len(expanded_res) > 1:
            queries = [str(q) for q in expanded_res]
    except Exception as e:  # noqa: BLE001
        logger.debug("QueryExpander failed: %s", e)

    # Intent-based sharpening
    if intent and intent.intent == IntentType.SEARCH:
        cleaned = re.sub(
            r'(?:について|を|で|に|は|が|って|して|教えて|調べて|検索して)',
            ' ', text,
        ).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)
        if cleaned and cleaned != text and cleaned not in queries:
            queries.append(cleaned)

    return queries


# =============================================================================
# L2: diversify_query (Skepsis)
# =============================================================================


_DIVERSIFY_PROMPT = (
    "Given the original query and its rewrites, generate 2-3 semantically diverse "
    "alternative queries that explore different angles of the same topic.\n\n"
    "Strategies:\n"
    "  1. Abstraction: generalize the concept\n"
    "  2. Specification: narrow to a specific aspect\n"
    "  3. Synonym: rephrase with different terminology\n"
    "  4. Cross-domain: find analogies in other fields\n\n"
    "Original: {original}\n"
    "Existing rewrites: {rewrites}\n\n"
    "Reply as JSON array of strings: [\"query1\", \"query2\", ...]"
)


# PURPOSE: L2 クエリ多角化 (Skepsis, I×Explore — 多角的に再解釈する)
async def diversify_query(
    text: str,
    queries: list[str],
) -> list[str]:
    """L2 Diversify queries by exploring different semantic angles.

    Adds abstraction, specification, synonym, and cross-domain alternatives.
    """
    try:
        from mekhane.mcp.prokataskeve.cortex_singleton import get_cortex
        client = get_cortex()
        if client is None:
            raise RuntimeError("CortexClient unavailable")

        prompt = _DIVERSIFY_PROMPT.replace(
            "{original}", text[:300],
        ).replace(
            "{rewrites}", json.dumps(queries[:5], ensure_ascii=False),
        )
        response = await asyncio.to_thread(
            client.chat, message=prompt, model="gemini-3-flash-preview", timeout=5.0,
        )
        raw = response.text.strip().removeprefix("```json").removesuffix("```").strip()
        new_queries = json.loads(raw)
        if isinstance(new_queries, list):
            return queries + [str(q) for q in new_queries if str(q) not in queries]
    except Exception as e:  # noqa: BLE001
        logger.debug("Query diversification failed: %s", e)

    return queries
