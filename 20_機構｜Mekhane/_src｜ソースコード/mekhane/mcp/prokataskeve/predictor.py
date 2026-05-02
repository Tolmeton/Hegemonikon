from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/prokataskeve/predictor.py
"""
Predictor — Predictive prefetching (speculative execution).

Contains:
  - predict_next (Promētheia, I×Future) — L4
  - prefetch (Proparaskeuē, A×Future) — L4
"""

import asyncio
import json
import logging
import os
from typing import Any

from mekhane.mcp.prokataskeve.models import (
    ContextSummary,
    IntentClassification,
)

logger = logging.getLogger(__name__)


# =============================================================================
# L4: predict_next (Promētheia)
# =============================================================================


_PREDICT_PROMPT = (
    "Based on the user's current input and context, predict 2-3 things "
    "the user is likely to need next. These predictions will be used to "
    "pre-fetch information.\n\n"
    "Current input: {input}\n"
    "Context: {context}\n"
    "Intent: {intent}\n\n"
    "Reply as JSON array of strings describing predicted next needs:\n"
    '["predicted_need_1", "predicted_need_2", ...]'
)


# PURPOSE: L4 予測的先読み (Promētheia, I×Future — 未来の信念状態を予測する)
async def predict_next(
    text: str,
    intent: IntentClassification,
    context: ContextSummary | None = None,
) -> list[str]:
    """L4 Predict what the user will need next.

    Uses LLM to anticipate follow-up queries or information needs.
    Speculative — predictions may miss. Cost is managed by enabling
    only at L4 depth.
    """
    try:
        from mekhane.mcp.prokataskeve.cortex_singleton import get_cortex
        client = get_cortex()
        if client is None:
            raise RuntimeError("CortexClient unavailable")

        ctx_text = context.summary_text if context else "なし"
        prompt = _PREDICT_PROMPT.replace(
            "{input}", text[:300],
        ).replace(
            "{context}", ctx_text[:200],
        ).replace(
            "{intent}", intent.intent.value,
        )

        response = await asyncio.to_thread(
            client.chat, message=prompt, model="gemini-3-flash-preview", timeout=5.0,
        )
        raw = response.text.strip().removeprefix("```json").removesuffix("```").strip()
        predictions = json.loads(raw)
        if isinstance(predictions, list):
            return [str(p) for p in predictions[:3]]
    except Exception as e:  # noqa: BLE001
        logger.debug("Prediction failed: %s", e)

    return []


# =============================================================================
# L4: prefetch (Proparaskeuē)
# =============================================================================


# PURPOSE: L4 先制プリフェッチ (Proparaskeuē, A×Future — 未来に向けて能動的に準備する)
async def prefetch(
    predictions: list[str],
) -> dict[str, Any]:
    """L4 Pre-fetch predicted information in parallel.

    For each prediction, attempt to:
      - Search Mneme for relevant KIs
      - Check file existence (if prediction mentions a path)
      - Warm up relevant caches

    Results are stored as a dict keyed by prediction text.
    """
    if not predictions:
        return {}

    results: dict[str, Any] = {}

    async def _fetch_one(prediction: str) -> tuple[str, Any]:
        try:
            # Check if prediction mentions a file path
            if prediction.startswith("/") or os.sep in prediction:
                exists = os.path.exists(prediction)
                return prediction, {"type": "file_check", "exists": exists}

            # Default: search Mneme
            from mekhane.mneme.search import search_all
            search_results = await search_all(query=prediction, k=2, sources=["sophia"])
            if isinstance(search_results, list) and search_results:
                return prediction, {
                    "type": "knowledge",
                    "count": len(search_results),
                    "titles": [r.get("title", "")[:50] for r in search_results],
                }
            return prediction, {"type": "no_hit"}
        except Exception as e:  # noqa: BLE001
            return prediction, {"type": "error", "detail": str(e)[:100]}

    # Parallel execution
    tasks = [_fetch_one(p) for p in predictions[:3]]
    for key, value in await asyncio.gather(*tasks):
        results[key] = value

    return results
