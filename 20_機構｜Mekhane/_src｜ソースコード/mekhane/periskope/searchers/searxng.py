from __future__ import annotations
# PROOF: mekhane/periskope/searchers/searxng.py
# PURPOSE: periskope モジュールの searxng
"""
SearXNG search client for Periskopē.

Connects to a self-hosted SearXNG instance to aggregate results
from 70+ search engines (Google, Bing, DuckDuckGo, Brave, etc.).
"""


import asyncio
import logging
import re
import time
from urllib.parse import urlencode, urlparse

import httpx

from mekhane.periskope.models import SearchResult, SearchSource

logger = logging.getLogger(__name__)

# Default SearXNG categories
CATEGORY_GENERAL = "general"
CATEGORY_SCIENCE = "science"
CATEGORY_NEWS = "news"
CATEGORY_IT = "it"

# PURPOSE: [L2-auto] SearXNGSearcher のクラス定義
class SearXNGSearcher:
    """Client for SearXNG meta-search engine cluster.

    SearXNG aggregates 70+ search engines into a single API.
    Results are returned in JSON format with relevance scoring.
    Supports round-robin across multiple SearXNG instances.

    Domain blacklist is injected via config.yaml (domain_blocklist key).
    """

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(
        self,
        base_url: str | list[str] = "http://localhost:8888",
        timeout: float = 180.0,
        default_lang: str = "ja-JP",
        min_score: float = 0.0,
        domain_blacklist: set[str] | None = None,
        category_engines: dict[str, list[str]] | None = None,
    ) -> None:
        # Support single URL (str) or multiple URLs (list) for round-robin
        if isinstance(base_url, str):
            self._urls = [base_url.rstrip("/")]
        else:
            self._urls = [u.rstrip("/") for u in base_url]
        self._url_index = 0
        self.timeout = timeout
        self.default_lang = default_lang
        self.min_score = min_score
        self.domain_blacklist = domain_blacklist or set()
        self._client: httpx.AsyncClient | None = None
        # Category-specific engine lists injected from config.yaml
        self.category_engines = category_engines or {}
        # Circuit breaker: track dead URLs with TTL-based resurrection
        self._dead_urls: dict[str, float] = {}  # url → monotonic death_time
        self._DEAD_TTL = 300.0  # 5 min resurrection window

    @property
    def base_url(self) -> str:
        """Round-robin with circuit breaker: skip dead URLs."""
        now = time.monotonic()
        # Resurrect expired dead URLs
        self._dead_urls = {
            u: t for u, t in self._dead_urls.items()
            if now - t < self._DEAD_TTL
        }
        alive = [u for u in self._urls if u not in self._dead_urls]
        if not alive:
            # All dead — force retry on all (last resort)
            alive = self._urls
            self._dead_urls.clear()
            logger.warning("SearXNG circuit breaker: all URLs dead, resetting")
        url = alive[self._url_index % len(alive)]
        self._url_index += 1
        return url

    def mark_dead(self, url: str) -> None:
        """Mark a URL as dead after connection/request failure."""
        self._dead_urls[url] = time.monotonic()
        logger.warning(
            "SearXNG circuit breaker: marked %s as dead (TTL=%ds)",
            url, int(self._DEAD_TTL),
        )

    # PURPOSE: [L2-auto] _get_client の非同期処理定義
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    # PURPOSE: [L2-auto] close の非同期処理定義
    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # PURPOSE: [L2-auto] search の非同期処理定義
    async def search(
        self,
        query: str,
        categories: list[str] | None = None,
        max_results: int = 20,
        language: str | None = None,
        time_range: str | None = None,
        engines: list[str] | None = None,
    ) -> list[SearchResult]:
        """Execute a search against SearXNG.

        Args:
            query: Search query string.
            categories: SearXNG categories (general, science, news, it).
            max_results: Maximum number of results to return.
            language: Language code (default: ja-JP).
            time_range: Time filter (day, week, month, year).
            engines: Specific engines to use (google, bing, etc.).

        Returns:
            List of SearchResult objects.
        """
        # Preprocess query
        processed_query = self._preprocess_query(query)

        params: dict[str, str] = {
            "q": processed_query,
            "format": "json",
            "language": language or self.default_lang,
        }

        if categories:
            params["categories"] = ",".join(categories)
        if time_range:
            params["time_range"] = time_range
        if engines:
            params["engines"] = ",".join(engines)

        url = f"{self.base_url}/search?{urlencode(params)}"

        try:
            client = await self._get_client()
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            logger.error("SearXNG search failed: %s", e)
            # Circuit breaker: mark the failed base URL as dead
            failed_base = url.split("/search")[0] if "/search" in url else ""
            if failed_base:
                self.mark_dead(failed_base)
            return []
        except Exception as e:  # noqa: BLE001
            logger.error("Unexpected error during SearXNG search: %s", e)
            return []

        results = []
        raw_results = data.get("results", [])

        for i, item in enumerate(raw_results[:max_results * 2]):  # over-fetch for filtering
            url_str = item.get("url", "")

            # Filter blacklisted domains
            if self._is_blacklisted(url_str):
                logger.debug("Filtered blacklisted URL: %s", url_str)
                continue

            relevance = _calculate_relevance(i, len(raw_results))

            # Filter low-score results
            if relevance < self.min_score:
                continue

            result = SearchResult(
                source=SearchSource.SEARXNG,
                title=item.get("title", ""),
                url=url_str or None,
                content=item.get("content", ""),
                snippet=_truncate(item.get("content", ""), 200),
                relevance=relevance,
                timestamp=item.get("publishedDate"),
                metadata={
                    "engine": item.get("engine", ""),
                    "engines": item.get("engines", []),
                    "category": item.get("category", ""),
                    "score": item.get("score", 0.0),
                },
            )
            results.append(result)

            if len(results) >= max_results:
                break

        logger.info(
            "SearXNG: %d results for %r (from %d total, %d filtered)",
            len(results),
            query,
            data.get("number_of_results", 0),
            len(raw_results) - len(results),
        )

        return results

    # PURPOSE: [L2-auto] search_academic の非同期処理定義
    async def search_academic(
        self, query: str, max_results: int = 20, time_range: str | None = None, engines: list[str] | None = None
    ) -> list[SearchResult]:
        """W2: Search specifically for academic papers and science articles."""
        return await self.search(
            query,
            categories=["science"],
            max_results=max_results,
            time_range=time_range,
            engines=engines,
        )

    async def search_news(
        self, query: str, max_results: int = 20, time_range: str | None = "day", engines: list[str] | None = None
    ) -> list[SearchResult]:
        """W3: Search specifically for recent news articles."""
        return await self.search(
            query,
            categories=["news"],
            max_results=max_results,
            time_range=time_range,
            engines=engines,
        )

    # PURPOSE: [L2-auto] health_check の非同期処理定義
    async def health_check(self) -> bool:
        """Check if SearXNG is reachable."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/search?q=ping&format=json")
            return response.status_code == 200
        except Exception:  # noqa: BLE001
            return False

    # PURPOSE: [L2-auto] search_multi_category の非同期処理定義
    async def search_multi_category(
        self,
        query: str,
        max_results: int = 20,
        weights: dict[str, float] | None = None,
        extra_queries: list[str] | None = None,
    ) -> list[SearchResult]:
        """W1: Search across 4 categories × multiple queries in parallel.

        Runs general, science, it, and news searches concurrently.
        If extra_queries is provided (e.g. translated queries from QueryExpander),
        each category is searched with all queries for better recall.

        Args:
            query: Primary search query.
            max_results: Total max results across all categories.
            weights: Category weights for result allocation.
            extra_queries: Additional queries (translations, synonyms).

        Returns:
            Merged and deduplicated results.
        """
        w = weights or {"general": 0.4, "science": 0.2, "it": 0.2, "news": 0.2}
        n_general = max(3, int(max_results * w.get("general", 0.4)))
        n_science = max(3, int(max_results * w.get("science", 0.2)))
        n_it = max(3, int(max_results * w.get("it", 0.2)))
        n_news = max(3, int(max_results * w.get("news", 0.2)))

        # All queries to search (primary + extras)
        all_queries = [query] + (extra_queries or [])

        # Engine lists from config.yaml (via category_engines) or defaults
        engines_general = self.category_engines.get("general") or None
        engines_it = self.category_engines.get("it") or None
        engines_news = self.category_engines.get("news") or None
        engines_science = self.category_engines.get("science") or None

        tasks = []
        task_labels = []
        for q in all_queries:
            q_label = q[:30] + "…" if len(q) > 30 else q
            tasks.append(self.search(q, categories=["general"], max_results=n_general, engines=engines_general))
            task_labels.append(f"general/{q_label}")
            tasks.append(self.search_academic(q, max_results=n_science, engines=engines_science))
            task_labels.append(f"science/{q_label}")
            tasks.append(self.search(q, categories=["it"], max_results=n_it, engines=engines_it))
            task_labels.append(f"it/{q_label}")
            tasks.append(self.search_news(q, max_results=n_news, time_range="month", engines=engines_news))
            task_labels.append(f"news/{q_label}")

        all_results: list[SearchResult] = []
        category_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Circuit breaker multi-category safety check
        if all(isinstance(r, Exception) for r in category_results):
            now = time.monotonic()
            alive_count = sum(1 for u in self._urls if now - self._dead_urls.get(u, 0) >= self._DEAD_TTL)
            if alive_count == 0:
                logger.error("SearXNG multi-category: All URLs died during concurrent execution. Bailing out early.")
                return []

        for label, result in zip(task_labels, category_results):
            if isinstance(result, list):
                all_results.extend(result)
                logger.debug("  SearXNG [%s]: %d results", label, len(result))
            elif isinstance(result, Exception):
                logger.warning("  SearXNG [%s]: FAILED — %s", label, result)

        # Deduplicate by URL
        seen: set[str] = set()
        deduped: list[SearchResult] = []
        for r in all_results:
            key = (r.url or "").lower().rstrip("/")
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            deduped.append(r)

        # Sort by relevance and trim
        deduped.sort(key=lambda r: r.relevance, reverse=True)
        result_list = deduped[:max_results]

        logger.info(
            "SearXNG multi-category: %d results (from %d raw, %d deduped, %d queries)",
            len(result_list), len(all_results), len(all_results) - len(deduped),
            len(all_queries),
        )
        return result_list

    # PURPOSE: [L2-auto] _preprocess_query の関数定義
    def _preprocess_query(self, query: str) -> str:
        """Preprocess search query for better results.

        - Strips excessive whitespace
        - Removes common noise words for academic queries
        """
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        return query

    # PURPOSE: [L2-auto] _is_blacklisted の関数定義
    def _is_blacklisted(self, url: str) -> bool:
        """Check if URL domain is in the blacklist."""
        if not url:
            return False
        try:
            domain = urlparse(url).hostname or ""
            return domain in self.domain_blacklist
        except Exception:  # noqa: BLE001
            return False


# PURPOSE: [L2-auto] _calculate_relevance の関数定義
def _calculate_relevance(index: int, total: int) -> float:
    """Calculate relevance score based on position (0-indexed)."""
    if total == 0:
        return 0.0
    return max(0.0, 1.0 - (index / max(total, 1)))


# PURPOSE: [L2-auto] _truncate の関数定義
def _truncate(text: str, max_len: int) -> str:
    """Truncate text to max_len characters."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."

