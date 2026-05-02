from __future__ import annotations
# PROOF: mekhane/periskope/phases/deep_read.py
# PURPOSE: Phase 1.8 — W7 Summary→Full-text selective crawl
"""
Phase 1.8: Deep Read.

W7: Summary→Full-text selective crawl pattern.
LLM analyzes snippets and decides which pages should be read in full.

Extracted from engine.py:
  - _phase_deep_read (L1445-1468)
  - _select_urls_for_deep_read (L2959-3061)
"""

import logging
import re
from typing import TYPE_CHECKING

from mekhane.periskope.models import SearchResult
from mekhane.periskope.page_fetcher import INTERNAL_SOURCES
from mekhane.periskope.prompts import load_prompt

if TYPE_CHECKING:
    from mekhane.periskope.page_fetcher import PageFetcher

logger = logging.getLogger(__name__)


async def _llm_ask(prompt: str, model: str = "gemini-3-flash-preview", max_tokens: int = 256) -> str:
    """Thin LLM wrapper (reused from engine.py top-level)."""
    from mekhane.ochema.cortex_client import CortexClient
    try:
        from mekhane.ochema.account_router import get_account_for
        account = get_account_for("periskope")
    except Exception:  # noqa: BLE001
        account = "default"
    client = CortexClient(max_tokens=max_tokens, account=account)
    return await client.generate(prompt, model=model)


async def select_urls_for_deep_read(
    query: str,
    search_results: list[SearchResult],
    depth: int = 2,
) -> list[str]:
    """W7: Select URLs that deserve full-text deep reading.

    Summary→Full-text pattern: LLM analyzes snippets
    and decides which pages should be read in full.

    Only external URLs with insufficient content are considered.
    Internal sources (Gnosis/Sophia/Kairos) already have full text.

    Returns:
        List of URLs to crawl (max 5 for L2, max 15 for L3).
    """
    max_deep_read = 5 if depth <= 2 else 15

    # Filter candidates: external sources with short content only
    candidates: list[tuple[int, SearchResult]] = []
    for i, r in enumerate(search_results):
        source_name = r.source.value if hasattr(r.source, "value") else str(r.source)
        if source_name in INTERNAL_SOURCES:
            continue
        if not r.url:
            continue
        if r.content and len(r.content) >= 1000:
            continue
        candidates.append((i, r))

    if not candidates:
        logger.info("W7: No URLs need deep reading (all have sufficient content)")
        return []

    # Build numbered list for LLM
    result_list = []
    for idx, (i, r) in enumerate(candidates[:30]):
        snippet = (r.snippet or r.content or "")[:150]
        result_list.append(
            f"[{idx + 1}] {r.title}\n"
            f"    URL: {r.url}\n"
            f"    Snippet: {snippet}"
        )

    template = load_prompt("w7_deep_read_selection.typos")
    if template:
        prompt = template.format(
            query=query,
            result_list="\n".join(result_list),
            max_deep_read=max_deep_read,
        )
    else:
        prompt = (
            "You are a research assistant deciding which web pages to read in full.\n\n"
            f"Research query: {query}\n\n"
            "Search results (summaries only):\n"
            + "\n".join(result_list)
            + "\n\n"
            f"Which pages should be read in full to best answer the query? "
            f"Select up to {max_deep_read} pages.\n\n"
            "Consider:\n"
            "- Pages likely to contain detailed analysis or original data\n"
            "- Pages from authoritative sources (academic, official docs)\n"
            "- Pages whose snippets suggest they cover key aspects of the query\n\n"
            "If the snippets already provide enough information, return NONE.\n\n"
            f"Return ONLY the numbers (comma-separated), e.g.: 1, 3, 5\n"
            "If no pages need deep reading: NONE"
        )

    try:
        text = await _llm_ask(prompt, max_tokens=128)

        if not text or "NONE" in text.upper().strip():
            logger.info("W7: LLM decided no deep reading needed")
            return []

        numbers = re.findall(r"\d+", text)
        selected_indices = [int(n) - 1 for n in numbers if n.isdigit()]

        urls = []
        for idx in selected_indices:
            if 0 <= idx < len(candidates):
                urls.append(candidates[idx][1].url)
            if len(urls) >= max_deep_read:
                break

        logger.info("W7: LLM selected %d URLs for deep reading", len(urls))
        return urls

    except Exception as e:  # noqa: BLE001
        logger.warning("W7: URL selection failed, falling back to top-N: %s", e)
        return [r.url for _, r in candidates[:max_deep_read] if r.url]


async def phase_deep_read(
    query: str,
    search_results: list[SearchResult],
    depth: int,
    *,
    page_fetcher: 'PageFetcher | None' = None,
) -> list[SearchResult]:
    """Phase 1.8: W7 Summary→Full-text selective crawl."""
    if page_fetcher is None:
        return search_results

    try:
        deep_read_urls = await select_urls_for_deep_read(
            query, search_results, depth=depth,
        )
        if deep_read_urls:
            logger.info("Phase 1.8: Deep-reading %d URLs", len(deep_read_urls))
            fetched = await page_fetcher.fetch_many(deep_read_urls)
            enriched = 0
            for r in search_results:
                if r.url and r.url in fetched:
                    r.content = fetched[r.url]
                    enriched += 1
            if enriched:
                logger.info("Phase 1.8: Enriched %d results", enriched)
    except Exception as e:  # noqa: BLE001
        logger.warning("Phase 1.8 (deep-read) failed: %s", e)
    return search_results
