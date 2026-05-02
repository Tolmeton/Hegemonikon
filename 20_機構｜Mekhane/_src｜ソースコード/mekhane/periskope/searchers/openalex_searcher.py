from __future__ import annotations
# PROOF: mekhane/periskope/searchers/openalex_searcher.py
# PURPOSE: periskope モジュールの openalex_searcher
"""
OpenAlex API client for Periskopē.

OpenAlex is a free, open catalog of the world's scholarly works, authors,
institutions, and more. 100,000 requests/day free tier.

API docs: https://docs.openalex.org/
"""


import logging
import os
from typing import Any

import httpx

from mekhane.periskope.models import SearchResult, SearchSource

logger = logging.getLogger(__name__)

# OpenAlex API endpoint
_OPENALEX_API_URL = "https://api.openalex.org/works"


class OpenAlexSearcher:
    """Client for OpenAlex API.

    Provides access to scholarly metadata with:
    - 250M+ works indexed
    - Free tier: 100,000 requests/day
    - CC0 licensed data
    - Polite pool: include email for higher rate limits

    Optional: Set OPENALEX_EMAIL env var for polite pool access.
    """

    def __init__(self, timeout: float = 15.0) -> None:
        self._timeout = timeout
        self._email = os.getenv("OPENALEX_EMAIL", "")
        self._client: httpx.AsyncClient | None = None

    @property
    def available(self) -> bool:
        """OpenAlex API is always available (no key needed)."""
        return True

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {"User-Agent": "Periskope/1.0 (HGK Deep Research)"}
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                headers=headers,
            )
        return self._client

    async def search(
        self,
        query: str,
        max_results: int = 10,
        sort: str = "relevance_score:desc",
    ) -> list[SearchResult]:
        """Search OpenAlex for scholarly works.

        Args:
            query: Search query string.
            max_results: Maximum results (1-200).
            sort: Sort criterion (default: relevance_score:desc).

        Returns:
            List of SearchResult from OpenAlex.
        """
        params: dict[str, Any] = {
            "search": query,
            "per_page": min(max_results, 200),
            "sort": sort,
        }

        # Polite pool: include email for higher rate limits
        if self._email:
            params["mailto"] = self._email

        try:
            client = await self._get_client()
            resp = await client.get(_OPENALEX_API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.error("OpenAlex search HTTP error: %s — %s", e.response.status_code, e)
            return []
        except Exception as e:  # noqa: BLE001
            logger.error("OpenAlex search failed: %s", e)
            return []

        # Parse results
        works = data.get("results", [])
        results: list[SearchResult] = []

        for i, work in enumerate(works[:max_results]):
            title = work.get("title", "") or ""
            doi = work.get("doi", "")
            openalex_id = work.get("id", "")

            # Build URL: prefer DOI, fallback to OpenAlex URL
            url = doi if doi else openalex_id

            # Abstract (inverted index → full text)
            abstract = self._reconstruct_abstract(
                work.get("abstract_inverted_index")
            )

            # Authors
            authors = []
            for authorship in work.get("authorships", [])[:10]:
                author = authorship.get("author", {})
                name = author.get("display_name", "")
                if name:
                    authors.append(name)

            # Publication date and year
            pub_date = work.get("publication_date", "")
            pub_year = work.get("publication_year", "")

            # Venue / source
            primary_location = work.get("primary_location", {}) or {}
            source_info = primary_location.get("source", {}) or {}
            venue = source_info.get("display_name", "")

            # Citation count
            cited_by = work.get("cited_by_count", 0)

            # Open access
            oa = work.get("open_access", {}) or {}
            is_oa = oa.get("is_oa", False)
            oa_url = oa.get("oa_url", "")

            # Relevance: position-based scoring (1.0 → 0.5)
            relevance = 1.0 - (i / max(len(works), 1)) * 0.5

            # Build content
            content_parts = []
            if authors:
                content_parts.append(f"Authors: {', '.join(authors[:5])}")
            if venue:
                content_parts.append(f"Venue: {venue}")
            if pub_year:
                content_parts.append(f"Year: {pub_year}")
            if cited_by:
                content_parts.append(f"Citations: {cited_by}")
            if abstract:
                content_parts.append(f"\n{abstract}")

            content = "\n".join(content_parts)
            snippet = _truncate(abstract or title, 200)

            result = SearchResult(
                source=SearchSource.OPENALEX,
                title=title,
                url=url or None,
                content=content,
                snippet=snippet,
                relevance=relevance,
                timestamp=pub_date[:10] if pub_date else None,
                metadata={
                    "openalex_id": openalex_id,
                    "doi": doi,
                    "cited_by_count": cited_by,
                    "is_oa": is_oa,
                    "oa_url": oa_url,
                    "authors": authors,
                    "venue": venue,
                },
            )
            results.append(result)

        logger.info("OpenAlex: %d results for %r", len(results), query)
        return results

    @staticmethod
    def _reconstruct_abstract(inverted_index: dict | None) -> str:
        """Reconstruct abstract text from OpenAlex inverted index format.

        OpenAlex stores abstracts as {word: [positions]} for compression.
        We reconstruct the original text by placing words at their positions.
        """
        if not inverted_index:
            return ""

        # Build position → word mapping
        word_positions: list[tuple[int, str]] = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))

        # Sort by position and join
        word_positions.sort(key=lambda x: x[0])
        return " ".join(word for _, word in word_positions)

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
