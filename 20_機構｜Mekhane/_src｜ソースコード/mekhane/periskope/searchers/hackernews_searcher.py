from __future__ import annotations
# PROOF: mekhane/periskope/searchers/hackernews_searcher.py
# PURPOSE: periskope モジュールの hackernews_searcher
"""
Hacker News Search API client for Periskopē.

Uses the Algolia-powered HN Search API for real-time access
to tech discussions, product launches, and industry news.

API docs: https://hn.algolia.com/api
No authentication required. No rate limit documented.
"""


import logging
from typing import Any

import httpx

from mekhane.periskope.models import SearchResult, SearchSource

logger = logging.getLogger(__name__)

_HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
_HN_SEARCH_DATE_URL = "https://hn.algolia.com/api/v1/search_by_date"


class HackerNewsSearcher:
    """Client for Hacker News (Algolia) Search API.

    Searches stories, comments, and Show HN posts.
    No authentication needed — completely free and open.
    """

    def __init__(self, timeout: float = 10.0) -> None:
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def available(self) -> bool:
        """Always available (no API key needed)."""
        return True

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by_date: bool = True,
        tags: str = "story",
    ) -> list[SearchResult]:
        """Search Hacker News via Algolia API.

        Args:
            query: Search query string.
            max_results: Maximum results (1-1000, but we cap at 50).
            sort_by_date: If True, sort by date (newest first).
                         If False, sort by relevance (Algolia ranking).
            tags: Filter by type: 'story', 'comment', 'ask_hn',
                  'show_hn', 'poll'. Can combine: '(story,show_hn)'.

        Returns:
            List of SearchResult from Hacker News.
        """
        url = _HN_SEARCH_DATE_URL if sort_by_date else _HN_SEARCH_URL
        params: dict[str, Any] = {
            "query": query,
            "hitsPerPage": min(max_results, 50),
            "tags": tags,
        }

        try:
            client = await self._get_client()
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.error("HN search HTTP error: %s", e.response.status_code)
            return []
        except Exception as e:  # noqa: BLE001
            logger.error("HN search failed: %s", e)
            return []

        hits = data.get("hits", [])
        results: list[SearchResult] = []

        for i, hit in enumerate(hits[:max_results]):
            title = hit.get("title", "") or hit.get("story_title", "")
            story_url = hit.get("url", "")
            hn_url = f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
            # Prefer original URL, fall back to HN discussion
            display_url = story_url or hn_url

            points = hit.get("points", 0) or 0
            num_comments = hit.get("num_comments", 0) or 0
            author = hit.get("author", "")
            created_at = hit.get("created_at", "")

            # Comment text or story text
            content = hit.get("comment_text", "") or hit.get("story_text", "") or ""
            # Strip HTML
            import re
            content = re.sub(r"<[^>]+>", "", content)[:2000]

            snippet_parts = []
            if points:
                snippet_parts.append(f"⬆{points}")
            if num_comments:
                snippet_parts.append(f"💬{num_comments}")
            if author:
                snippet_parts.append(f"by {author}")
            snippet = " | ".join(snippet_parts)

            relevance = 1.0 - (i / max(len(hits), 1)) * 0.5

            result = SearchResult(
                source=SearchSource.HACKERNEWS,
                title=title,
                url=display_url or None,
                content=content,
                snippet=_truncate(snippet, 200),
                relevance=relevance,
                timestamp=created_at,
                metadata={
                    "points": points,
                    "num_comments": num_comments,
                    "author": author,
                    "hn_url": hn_url,
                    "story_url": story_url,
                    "object_id": hit.get("objectID", ""),
                },
            )
            results.append(result)

        logger.info("HackerNews: %d results for %r", len(results), query)
        return results

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
