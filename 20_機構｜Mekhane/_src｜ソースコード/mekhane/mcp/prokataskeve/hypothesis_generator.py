from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/prokataskeve/hypothesis_generator.py
"""
HypothesisGenerator — HyDE (Hypothetical Document Embeddings).

Contains:
  - generate_hyde (Zētēsis, A×E) — L3
"""

import asyncio
import logging

from mekhane.mcp.prokataskeve.models import IntentClassification, IntentType

logger = logging.getLogger(__name__)


# =============================================================================
# L3: generate_hyde (Zētēsis)
# =============================================================================


_HYDE_PROMPT = (
    "Generate a hypothetical answer passage for the following query. "
    "This passage will be used as a search query to find relevant documents. "
    "Write a 2-3 sentence passage that a relevant document might contain.\n\n"
    "Query: {query}\n\n"
    "Hypothetical answer passage:"
)


# PURPOSE: L3 HyDE 仮説生成 (Zētēsis, A×E — 認識のために能動的に探求する)
async def generate_hyde(
    text: str,
    intent: IntentClassification,
) -> str | None:
    """L3 Generate a hypothetical document for search augmentation.

    Only activates for SEARCH intent. Creates a hypothetical answer
    that can be used as a dense retrieval query (HyDE technique).
    """
    # Only for search intent
    if intent.intent != IntentType.SEARCH:
        return None

    try:
        from mekhane.mcp.prokataskeve.cortex_singleton import get_cortex
        client = get_cortex()
        if client is None:
            raise RuntimeError("CortexClient unavailable")

        prompt = _HYDE_PROMPT.replace("{query}", text[:300])
        response = await asyncio.to_thread(
            client.chat, message=prompt, model="gemini-3-flash-preview", timeout=5.0,
        )
        hyde_text = response.text.strip()
        return hyde_text if len(hyde_text) > 20 else None
    except Exception as e:  # noqa: BLE001
        logger.debug("HyDE generation failed: %s", e)
        return None
