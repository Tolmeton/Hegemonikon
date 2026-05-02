from __future__ import annotations
# PROOF: mekhane/periskope/searchers/github_searcher.py
# PURPOSE: periskope モジュールの github_searcher
"""
GitHub Search API client for Periskopē.

Searches GitHub Issues, Discussions, and Code to find recent
developer discussions, bug reports, and solutions. Complements
general web search with developer-community-specific results.

API docs: https://docs.github.com/en/rest/search/search
Rate limits: 10 req/min (unauthenticated), 30 req/min (authenticated)
"""


import logging
import os
from typing import Any

import httpx

from mekhane.periskope.models import SearchResult, SearchSource

logger = logging.getLogger(__name__)

_GITHUB_API_URL = "https://api.github.com/search"


# PURPOSE: [L2-auto] GitHubSearcher のクラス定義
class GitHubSearcher:
    """Client for GitHub Search API.

    Searches Issues, Discussions via GitHub REST API.
    Provides developer-community-specific results with:
    - Exact date filtering (updated, created)
    - State filtering (open/closed)
    - Sort by relevance, updated, created, reactions

    Optional: Set GITHUB_TOKEN env var for higher rate limits.
    """

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(self, timeout: float = 10.0) -> None:
        self._token = os.getenv("GITHUB_TOKEN", "")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    # PURPOSE: [L2-auto] available の関数定義
    @property
    def available(self) -> bool:
        """Always available (unauthenticated search works, just slower)."""
        return True

    # PURPOSE: [L2-auto] _get_client の非同期処理定義
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers: dict[str, str] = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                headers=headers,
            )
        return self._client

    # PURPOSE: [L2-auto] search の非同期処理定義
    async def search(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "issues",
        sort: str = "updated",
        order: str = "desc",
    ) -> list[SearchResult]:
        """Search GitHub Issues/Discussions.

        Args:
            query: Search query string.
            max_results: Maximum results (1-100, GitHub API limit).
            search_type: 'issues' (includes PRs), 'code', 'repositories'.
            sort: Sort field: 'updated', 'created', 'reactions', 'best-match'.
            order: 'desc' or 'asc'.

        Returns:
            List of SearchResult from GitHub.
        """
        params: dict[str, Any] = {
            "q": query,
            "per_page": min(max_results, 100),
            "sort": sort if sort != "best-match" else "",
            "order": order,
        }
        # Remove empty sort (GitHub default = best-match)
        if not params["sort"]:
            del params["sort"]

        endpoint = f"{_GITHUB_API_URL}/{search_type}"

        try:
            client = await self._get_client()
            resp = await client.get(endpoint, params=params)

            # Rate limit handling
            remaining = resp.headers.get("x-ratelimit-remaining", "?")
            logger.debug("GitHub API rate limit remaining: %s", remaining)

            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.warning(
                    "GitHub API rate limited. Set GITHUB_TOKEN env var for higher limits."
                )
            else:
                logger.error("GitHub search HTTP error: %s — %s", e.response.status_code, e)
            return []
        except Exception as e:  # noqa: BLE001
            logger.error("GitHub search failed: %s", e)
            return []

        items = data.get("items", [])
        total = data.get("total_count", 0)
        results: list[SearchResult] = []

        for i, item in enumerate(items[:max_results]):
            url = item.get("html_url", "")
            title = item.get("title", "")
            body = item.get("body", "") or ""

            # Build rich snippet from issue metadata
            state = item.get("state", "")
            labels = [lb.get("name", "") for lb in item.get("labels", [])]
            reactions = item.get("reactions", {}).get("total_count", 0)
            comments = item.get("comments", 0)
            updated = item.get("updated_at", "")
            created = item.get("created_at", "")
            repo_url = item.get("repository_url", "")
            repo_name = repo_url.split("/")[-2:] if "/" in repo_url else []

            snippet_parts = []
            if state:
                snippet_parts.append(f"[{state.upper()}]")
            if repo_name:
                snippet_parts.append("/".join(repo_name))
            if labels:
                snippet_parts.append(f"Labels: {', '.join(labels[:3])}")
            if reactions:
                snippet_parts.append(f"👍{reactions}")
            if comments:
                snippet_parts.append(f"💬{comments}")
            snippet = " | ".join(snippet_parts)

            # Content: title + truncated body
            content = body[:2000] if body else ""

            # Relevance: position-based scoring (1.0 → 0.5)
            relevance = 1.0 - (i / max(len(items), 1)) * 0.5

            result = SearchResult(
                source=SearchSource.GITHUB,
                title=title,
                url=url or None,
                content=content,
                snippet=_truncate(snippet, 200),
                relevance=relevance,
                timestamp=updated or created,
                metadata={
                    "state": state,
                    "labels": labels,
                    "reactions": reactions,
                    "comments": comments,
                    "repo": "/".join(repo_name) if repo_name else "",
                    "search_type": search_type,
                },
            )
            results.append(result)

        logger.info(
            "GitHub: %d/%d results for %r (type=%s, sort=%s)",
            len(results), total, query, search_type, sort,
        )
        return results

    # PURPOSE: [L2-auto] search_multi の非同期処理定義
    async def search_multi(
        self,
        query: str,
        max_results: int = 10,
        search_types: list[str] | None = None,
    ) -> list[SearchResult]:
        """Search across multiple GitHub search types.

        Merges results from issues and discussions (if configured).
        """
        types = search_types or ["issues"]
        all_results: list[SearchResult] = []
        per_type = max(max_results // len(types), 3)

        for st in types:
            results = await self.search(query, max_results=per_type, search_type=st)
            all_results.extend(results)

        # Deduplicate by URL
        seen: set[str] = set()
        deduped: list[SearchResult] = []
        for r in all_results:
            if r.url and r.url not in seen:
                seen.add(r.url)
                deduped.append(r)
            elif not r.url:
                deduped.append(r)

        return deduped[:max_results]

    # PURPOSE: [L2-auto] close の非同期処理定義
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# PURPOSE: [L2-auto] _truncate の関数定義
def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
