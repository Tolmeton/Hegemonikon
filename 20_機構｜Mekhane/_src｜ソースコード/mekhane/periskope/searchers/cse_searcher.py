from __future__ import annotations
# PROOF: mekhane/periskope/searchers/cse_searcher.py
# PURPOSE: periskope モジュールの cse_searcher
"""
Google Custom Search Engine (CSE) searcher for Periskopē.

Multi-account round-robin: 6 Google accounts with independent CSE instances.
Each account has 100 free queries/day. Round-robin distributes load across
accounts, giving effectively 600 queries/day at zero cost.

Architecture:
    config.yaml → google_cse.accounts[] → CseAccount(api_key, cx)
    CseSearcher._next_account() → round-robin selection
    CseSearcher.search() → Google Custom Search API v1 → SearchResult[]
"""


import asyncio
import itertools
import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

from mekhane.periskope.models import SearchResult, SearchSource

logger = logging.getLogger(__name__)

_CSE_API_URL = "https://www.googleapis.com/customsearch/v1"


@dataclass
class CseAccount:
    """A single Google CSE account with API key and cx."""
    name: str
    api_key: str
    cx: str
    specialist: str = ""  # e.g. "academic", "refutation", "jp_academic", "tech", "philosophy"
    lr: str = ""  # language restrict (e.g. "lang_ja", "lang_en")

    @property
    def available(self) -> bool:
        return bool(self.api_key and self.cx)


class CseSearcher:
    """Google Custom Search API client with multi-account round-robin.

    Loads account credentials from environment variables as defined in
    config.yaml google_cse.accounts[]. Rotates through available accounts
    to distribute API quota (100 queries/day per account).

    On 403/429 (quota exceeded), automatically falls through to the next
    account in the rotation.
    """

    def __init__(
        self,
        accounts_config: list[dict[str, str]] | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._accounts: list[CseAccount] = []

        if accounts_config:
            for acfg in accounts_config:
                api_key = os.getenv(acfg.get("api_key_env", ""), "")
                cx = os.getenv(acfg.get("cx_env", ""), "")
                account = CseAccount(
                    name=acfg.get("name", "unknown"),
                    api_key=api_key,
                    cx=cx,
                    specialist=acfg.get("specialist", ""),
                    lr=acfg.get("lr", ""),
                )
                if account.available:
                    self._accounts.append(account)
                else:
                    logger.warning(
                        "CSE account %r skipped: api_key=%s, cx=%s",
                        acfg.get("name"), bool(api_key), bool(cx),
                    )

        # Round-robin iterator over available accounts
        self._rotation = itertools.cycle(self._accounts) if self._accounts else None
        self._rotation_lock = asyncio.Lock()
        logger.info("CSE: %d accounts loaded", len(self._accounts))

    @property
    def available(self) -> bool:
        """At least one account is configured."""
        return len(self._accounts) > 0

    async def _next_account(self) -> CseAccount | None:
        """Get the next account in round-robin rotation (async-safe)."""
        if self._rotation is None:
            return None
        async with self._rotation_lock:
            return next(self._rotation)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def search(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[SearchResult]:
        """Search via Google Custom Search API with account rotation.

        On quota errors (403/429), tries the next account up to len(accounts)
        times before giving up.
        """
        if not self.available:
            logger.warning("No CSE accounts configured — skipping")
            return []

        max_attempts = len(self._accounts)

        for attempt in range(max_attempts):
            account = await self._next_account()
            if account is None:
                break

            try:
                results = await self._search_with_account(
                    account, query, max_results,
                )
                if results is not None:  # None = quota error, try next
                    return results
            except Exception as e:  # noqa: BLE001
                logger.error(
                    "CSE search failed (account=%s, attempt=%d): %s",
                    account.name, attempt + 1, e,
                )

        logger.warning("CSE: all %d accounts exhausted for query %r", max_attempts, query)
        return []

    async def _search_with_account(
        self,
        account: CseAccount,
        query: str,
        max_results: int,
    ) -> list[SearchResult] | None:
        """Execute search with a specific account. Returns None on quota error."""
        params: dict[str, Any] = {
            "key": account.api_key,
            "cx": account.cx,
            "q": query,
            "num": min(max_results, 10),  # CSE max is 10 per request
            # Search quality parameters
            "hl": "ja",       # UI language: Japanese
            "gl": "jp",       # Geolocation: Japan (boost local results)
        }
        # Per-account language restriction (e.g. rairai → lang_ja)
        if account.lr:
            params["lr"] = account.lr

        client = await self._get_client()
        try:
            resp = await client.get(_CSE_API_URL, params=params)
        except httpx.TimeoutException:
            logger.warning("CSE timeout for account %s", account.name)
            return None  # Treat as quota-like, try next

        if resp.status_code in (403, 429):
            logger.warning(
                "CSE quota exceeded for account %s (HTTP %d), rotating...",
                account.name, resp.status_code,
            )
            return None  # Signal to try next account

        if resp.status_code >= 400:
            logger.error(
                "CSE HTTP error for account %s: %d %s",
                account.name, resp.status_code, resp.text[:200],
            )
            return []  # Non-quota error, don't retry

        data = resp.json()

        items = data.get("items", [])
        results: list[SearchResult] = []

        for i, item in enumerate(items[:max_results]):
            url = item.get("link", "")
            title = item.get("title", "")
            snippet = item.get("snippet", "")

            # Relevance: position-based scoring (1.0 → 0.5)
            relevance = 1.0 - (i / max(len(items), 1)) * 0.5

            result = SearchResult(
                source=SearchSource.GOOGLE_CSE,
                title=title,
                url=url or None,
                content=snippet,
                snippet=_truncate(snippet, 200),
                relevance=relevance,
                metadata={
                    "cse_account": account.name,
                    "display_link": item.get("displayLink", ""),
                    "cache_id": item.get("cacheId"),
                },
            )
            results.append(result)

        logger.info(
            "CSE (%s): %d results for %r",
            account.name, len(results), query,
        )
        return results

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
