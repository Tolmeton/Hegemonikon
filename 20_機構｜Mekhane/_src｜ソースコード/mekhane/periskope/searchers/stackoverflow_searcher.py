from __future__ import annotations
# PROOF: mekhane/periskope/searchers/stackoverflow_searcher.py
# PURPOSE: periskope モジュールの stackoverflow_searcher
"""
Stack Overflow Search API client for Periskopē.

Stack Exchange API provides direct access to questions, answers,
and comments — the richest developer Q&A database.

API docs: https://api.stackexchange.com/docs/search
Quota: 300 requests/day (unauthenticated), 10000/day (with key).
"""


import logging
import os
from typing import Any

import httpx

from mekhane.periskope.models import SearchResult, SearchSource

logger = logging.getLogger(__name__)

_SO_API_URL = "https://api.stackexchange.com/2.3/search/advanced"


class StackOverflowSearcher:
    """Client for Stack Overflow (Stack Exchange) API.

    Searches questions with answers, tags, and vote counts.
    Optional: Set STACKEXCHANGE_KEY env var for higher quota.
    """

    def __init__(self, timeout: float = 10.0) -> None:
        self._key = os.getenv("STACKEXCHANGE_KEY", "")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def available(self) -> bool:
        """Always available (unauthenticated works with lower quota)."""
        return True

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def search(
        self,
        query: str,
        max_results: int = 10,
        sort: str = "relevance",
        accepted: bool | None = None,
        tagged: str = "",
    ) -> list[SearchResult]:
        """Search Stack Overflow questions.

        Args:
            query: Search query string.
            max_results: Maximum results (1-100).
            sort: 'relevance', 'activity', 'votes', 'creation'.
            accepted: If True, only questions with accepted answers.
            tagged: Semicolon-separated tags (e.g., 'python;linux').

        Returns:
            List of SearchResult from Stack Overflow.
        """
        params: dict[str, Any] = {
            "q": query,
            "pagesize": min(max_results, 100),
            "order": "desc",
            "sort": sort,
            "site": "stackoverflow",
            "filter": "withbody",  # Include body text
        }
        if self._key:
            params["key"] = self._key
        if accepted is not None:
            params["accepted"] = str(accepted).lower()
        if tagged:
            params["tagged"] = tagged

        try:
            client = await self._get_client()
            resp = await client.get(_SO_API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 502:
                logger.warning("Stack Overflow API throttled")
            else:
                logger.error("SO search HTTP error: %s", e.response.status_code)
            return []
        except Exception as e:  # noqa: BLE001
            logger.error("SO search failed: %s", e)
            return []

        # Check quota
        quota_remaining = data.get("quota_remaining", "?")
        logger.debug("SO API quota remaining: %s", quota_remaining)

        items = data.get("items", [])
        results: list[SearchResult] = []

        for i, item in enumerate(items[:max_results]):
            url = item.get("link", "")
            title = item.get("title", "")
            body = item.get("body", "")
            # Strip HTML tags from body (simple approach)
            import re
            body_text = re.sub(r"<[^>]+>", "", body)[:2000]

            tags = item.get("tags", [])
            score = item.get("score", 0)
            answers = item.get("answer_count", 0)
            is_answered = item.get("is_answered", False)
            views = item.get("view_count", 0)
            created = item.get("creation_date", 0)
            last_activity = item.get("last_activity_date", 0)

            snippet_parts = []
            if is_answered:
                snippet_parts.append("✅ Answered")
            snippet_parts.append(f"⬆{score}")
            snippet_parts.append(f"💬{answers}")
            snippet_parts.append(f"👁{views}")
            if tags:
                snippet_parts.append(f"Tags: {', '.join(tags[:4])}")
            snippet = " | ".join(snippet_parts)

            # Relevance: combine position + score + answered
            relevance = 1.0 - (i / max(len(items), 1)) * 0.3
            if is_answered:
                relevance = min(relevance + 0.1, 1.0)

            from datetime import datetime, timezone
            timestamp = ""
            if last_activity:
                timestamp = datetime.fromtimestamp(
                    last_activity, tz=timezone.utc
                ).isoformat()

            result = SearchResult(
                source=SearchSource.STACKOVERFLOW,
                title=title,
                url=url or None,
                content=body_text,
                snippet=_truncate(snippet, 200),
                relevance=relevance,
                timestamp=timestamp,
                metadata={
                    "score": score,
                    "answer_count": answers,
                    "is_answered": is_answered,
                    "view_count": views,
                    "tags": tags,
                },
            )
            results.append(result)

        logger.info("StackOverflow: %d results for %r", len(results), query)
        return results

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
