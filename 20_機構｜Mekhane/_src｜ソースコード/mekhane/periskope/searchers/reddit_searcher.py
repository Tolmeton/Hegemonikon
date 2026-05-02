from __future__ import annotations
# PROOF: mekhane/periskope/searchers/reddit_searcher.py
# PURPOSE: periskope モジュールの reddit_searcher
"""
Reddit Search API client for Periskopē.

Uses Reddit's JSON endpoints (no OAuth needed for read-only search).
Developer discussions, real-world experiences, and community consensus.

API: https://www.reddit.com/search.json
Rate limit: ~60 requests/minute (unauthenticated).
"""


import logging
from typing import Any

import httpx

from mekhane.periskope.models import SearchResult, SearchSource

logger = logging.getLogger(__name__)

_REDDIT_SEARCH_URL = "https://www.reddit.com/search.json"


class RedditSearcher:
    """Client for Reddit search (JSON API, no auth required).

    Searches posts across all subreddits for developer discussions,
    real-world experiences, and community opinions.
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
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                headers={
                    # Reddit blocks default Python UA
                    "User-Agent": "Periskope/1.0 (HGK Deep Research Engine)",
                },
            )
        return self._client

    async def search(
        self,
        query: str,
        max_results: int = 10,
        sort: str = "relevance",
        time_filter: str = "all",
        subreddit: str = "",
    ) -> list[SearchResult]:
        """Search Reddit posts.

        Args:
            query: Search query string.
            max_results: Maximum results (1-100).
            sort: 'relevance', 'hot', 'top', 'new', 'comments'.
            time_filter: 'hour', 'day', 'week', 'month', 'year', 'all'.
            subreddit: Limit to specific subreddit (e.g., 'linux').

        Returns:
            List of SearchResult from Reddit.
        """
        if subreddit:
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            params: dict[str, Any] = {
                "q": query,
                "limit": min(max_results, 100),
                "sort": sort,
                "t": time_filter,
                "restrict_sr": "true",
            }
        else:
            url = _REDDIT_SEARCH_URL
            params = {
                "q": query,
                "limit": min(max_results, 100),
                "sort": sort,
                "t": time_filter,
            }

        try:
            client = await self._get_client()
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            # Reddit may return HTML (block page) instead of JSON
            content_type = resp.headers.get("content-type", "")
            if "json" not in content_type:
                logger.warning("Reddit returned non-JSON response: %s", content_type)
                return []
            data = resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Reddit rate limited — back off")
            else:
                logger.error("Reddit search HTTP error: %s", e.response.status_code)
            return []
        except Exception as e:  # noqa: BLE001
            logger.error("Reddit search failed: %s", e)
            return []

        children = data.get("data", {}).get("children", [])
        results: list[SearchResult] = []

        for i, child in enumerate(children[:max_results]):
            post = child.get("data", {})

            title = post.get("title", "")
            selftext = post.get("selftext", "")[:2000]
            permalink = post.get("permalink", "")
            post_url = f"https://www.reddit.com{permalink}" if permalink else ""

            subreddit_name = post.get("subreddit", "")
            score = post.get("score", 0)
            num_comments = post.get("num_comments", 0)
            upvote_ratio = post.get("upvote_ratio", 0.0)
            created_utc = post.get("created_utc", 0)

            snippet_parts = [f"r/{subreddit_name}"]
            snippet_parts.append(f"⬆{score}")
            snippet_parts.append(f"💬{num_comments}")
            snippet_parts.append(f"ratio:{upvote_ratio:.0%}")
            snippet = " | ".join(snippet_parts)

            relevance = 1.0 - (i / max(len(children), 1)) * 0.5

            from datetime import datetime, timezone
            timestamp = ""
            if created_utc:
                timestamp = datetime.fromtimestamp(
                    created_utc, tz=timezone.utc
                ).isoformat()

            result = SearchResult(
                source=SearchSource.REDDIT,
                title=title,
                url=post_url or None,
                content=selftext,
                snippet=_truncate(snippet, 200),
                relevance=relevance,
                timestamp=timestamp,
                metadata={
                    "subreddit": subreddit_name,
                    "score": score,
                    "num_comments": num_comments,
                    "upvote_ratio": upvote_ratio,
                    "is_self": post.get("is_self", False),
                },
            )
            results.append(result)

        logger.info("Reddit: %d results for %r", len(results), query)
        return results

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
