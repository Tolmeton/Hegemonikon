from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/prokataskeve/pattern_injector.py
"""
PatternInjector — Few-shot example injection.

Contains:
  - inject_few_shot (Bebaiōsis, I×+) — L2
"""

import logging

from mekhane.mcp.prokataskeve.models import (
    FewShotExample,
    IntentClassification,
    IntentType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# L2: inject_few_shot (Bebaiōsis)
# =============================================================================


# PURPOSE: L2 Few-Shot 注入 (Bebaiōsis, I×+ — 成功パターンで信念を強化する)
async def inject_few_shot(
    text: str,
    intent: IntentClassification,
) -> list[FewShotExample]:
    """L2 Inject few-shot examples from past successes.

    Searches Mneme (sophia/kairos) for similar past interactions
    and formats them as few-shot examples for downstream LLMs.
    """
    try:
        from mekhane.mneme.search import search_all

        # Map intent to search source
        source_map = {
            IntentType.SEARCH: ["sophia", "kairos"],
            IntentType.CODE: ["kairos"],
            IntentType.DEBUG: ["kairos"],
            IntentType.WORKFLOW: ["kairos"],
            IntentType.REVIEW: ["kairos"],
            IntentType.DISCUSS: ["sophia"],
        }
        sources = source_map.get(intent.intent, ["sophia", "kairos"])

        results = await search_all(query=text[:200], k=3, sources=sources)
        examples = []
        for r in (results if isinstance(results, list) else []):
            content = r.get("content", r.get("summary", ""))
            if not content:
                continue
            examples.append(FewShotExample(
                input_text=r.get("query", r.get("title", ""))[:200],
                output_text=content[:500],
                source=f"{r.get('source', 'unknown')}:{r.get('id', '')}",
                relevance=float(r.get("score", 0.0)),
            ))
        return examples
    except Exception as e:  # noqa: BLE001
        logger.debug("Few-shot injection failed: %s", e)
        return []
