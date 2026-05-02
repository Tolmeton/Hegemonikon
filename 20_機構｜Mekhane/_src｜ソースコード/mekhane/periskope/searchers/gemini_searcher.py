from __future__ import annotations
# PROOF: mekhane/periskope/searchers/gemini_searcher.py
# PURPOSE: periskope モジュールの gemini_searcher
"""
Google Search via Gemini Grounding for Periskopē.

Uses Gemini API's Google Search Grounding (`googleSearch` tool)
to retrieve real-time web search results from Google's index.
No Custom Search Engine (CSE) needed — works with any Gemini API key.

This replaces the deprecated Custom Search JSON API approach
(closed to new customers as of 2024).

Requires: GOOGLE_API_KEY environment variable (Gemini API key).
"""


import logging
import os
from typing import Any

import httpx

from mekhane.periskope.models import SearchResult, SearchSource
from mekhane.ochema.model_defaults import FLASH

logger = logging.getLogger(__name__)

_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_DEFAULT_MODEL = FLASH


class GeminiSearcher:
    """Google Search via Gemini Grounding API.

    Leverages Gemini's built-in Google Search tool to retrieve
    grounded search results with real URLs from Google's index.

    Requires:
        GOOGLE_API_KEY: Gemini API key from Google Cloud Console
    """

    def __init__(
        self,
        timeout: float = 15.0,
        model: str = _DEFAULT_MODEL,
    ) -> None:
        self._api_key = os.getenv("GOOGLE_API_KEY", "")
        self._timeout = timeout
        self._model = model
        self._client: httpx.AsyncClient | None = None

    @property
    def available(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(self._api_key)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def search(
        self,
        query: str,
        max_results: int = 10,
        date_restrict: str = "",
        site_search: str = "",
    ) -> list[SearchResult]:
        """Search via Gemini Google Search Grounding.

        Args:
            query: Search query string.
            max_results: Maximum results to return.
            date_restrict: Not used (kept for API compatibility).
            site_search: Optional site restriction (added to query).

        Returns:
            List of SearchResult from Google Search Grounding.
        """
        if not self.available:
            logger.warning("GOOGLE_API_KEY not set — skipping Gemini Search")
            return []

        # Build search prompt that maximizes grounding chunk retrieval
        search_query = query
        if site_search:
            search_query = f"site:{site_search} {query}"

        prompt = (
            f"Search for: {search_query}\n"
            f"List the top {max_results} most relevant web pages with their URLs and brief descriptions."
        )

        url = _GEMINI_URL.format(model=self._model)
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"googleSearch": {}}],
        }

        try:
            client = await self._get_client()
            resp = await client.post(
                url,
                params={"key": self._api_key},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Gemini API quota exceeded")
            else:
                logger.error("Gemini Search Grounding HTTP error: %s", e.response.status_code)
            return []
        except Exception as e:  # noqa: BLE001
            logger.error("Gemini Search Grounding failed: %s", e)
            return []

        # Extract grounding chunks from response
        candidates = data.get("candidates", [])
        if not candidates:
            logger.warning("Gemini Search Grounding: no candidates in response")
            return []

        candidate = candidates[0]
        grounding = candidate.get("groundingMetadata", {})
        chunks = grounding.get("groundingChunks", [])

        # Also extract the generated text for snippet enrichment
        gen_text = ""
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        if parts:
            gen_text = parts[0].get("text", "")

        # Extract support details for better snippets
        supports = grounding.get("groundingSupports", [])
        support_map: dict[int, str] = {}
        for sup in supports:
            segment = sup.get("segment", {})
            text = segment.get("text", "")
            for idx in sup.get("groundingChunkIndices", []):
                if idx not in support_map or len(text) > len(support_map[idx]):
                    support_map[idx] = text

        results: list[SearchResult] = []
        for i, chunk in enumerate(chunks[:max_results]):
            web = chunk.get("web", {})
            uri = web.get("uri", "")
            title = web.get("title", "")

            # Use support text as snippet, fall back to title
            snippet = support_map.get(i, title)

            relevance = 1.0 - (i / max(len(chunks), 1)) * 0.5

            result = SearchResult(
                source=SearchSource.GEMINI_SEARCH,
                title=title,
                url=uri or None,
                content=snippet,
                snippet=_truncate(snippet, 200),
                relevance=relevance,
                metadata={
                    "grounding_model": self._model,
                    "chunk_index": i,
                },
            )
            results.append(result)

        logger.info(
            "Gemini Search Grounding: %d results for %r (via %s)",
            len(results), query, self._model,
        )
        return results

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
