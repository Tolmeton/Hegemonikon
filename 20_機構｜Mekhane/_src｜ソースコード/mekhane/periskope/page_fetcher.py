from __future__ import annotations
# PROOF: mekhane/periskope/page_fetcher.py
# PURPOSE: periskope モジュールの page_fetcher
"""
Page Fetcher — 選択的全文クロール for Periskopē.

サマリ→本文パターン: 合成が「深読みすべき」と判断した URL のみ全文取得。
httpx でフェッチ → trafilatura で本文抽出。
JS 必須ページは PlaywrightSearcher にフォールバック。
"""


import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

# Internal sources — already have full content, no crawling needed
INTERNAL_SOURCES = {"gnosis", "sophia", "kairos"}

# Domains that block bots or are unreliable
BLOCKED_DOMAINS = {
    "linkedin.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
}


# PURPOSE: [L2-auto] PageFetcher のクラス定義
class PageFetcher:
    """Fetch and extract full text from web pages.

    Strategy:
      1. httpx GET → trafilatura extract (fast, lightweight)
      2. If httpx fails or JS required → PlaywrightSearcher fallback
    """

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(
        self,
        timeout: float = 10.0,
        max_content_length: int = 40_000,
        min_content_length: int = 500,
        playwright_fallback: bool = True,
    ) -> None:
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.min_content_length = min_content_length
        self.playwright_fallback = playwright_fallback
        self._playwright = None  # Lazy-init
        self._cache: dict[str, str | None] = {}  # URL → content cache

    # PURPOSE: [L2-auto] fetch_one の非同期処理定義
    async def fetch_one(self, url: str) -> str | None:
        """Fetch a single URL and extract text content.

        Returns:
            Extracted text content, or None on failure.
        """
        # Cache check — avoid re-fetching same URL in multi-pass
        if url in self._cache:
            logger.debug("Cache hit for %s", url[:60])
            return self._cache[url]

        # Skip blocked domains
        for domain in BLOCKED_DOMAINS:
            if domain in url:
                logger.debug("Skipping blocked domain: %s", url[:60])
                self._cache[url] = None
                return None

        # Try httpx + trafilatura first (fast path)
        text = await self._fetch_httpx(url)
        if text and len(text) >= self.min_content_length:
            result = text[:self.max_content_length]
            self._cache[url] = result
            return result

        # Skip Playwright fallback for obvious PDF URLs
        if url.lower().endswith(".pdf"):
            logger.debug("Skipping Playwright fallback for PDF URL: %s", url[:60])
            self._cache[url] = None
            return None

        # Fallback to Playwright for JS-rendered pages
        if self.playwright_fallback:
            text = await self._fetch_playwright(url)
            if text and len(text) >= self.min_content_length:
                result = text[:self.max_content_length]
                self._cache[url] = result
                return result

        self._cache[url] = None
        return None

    # PURPOSE: [L2-auto] fetch_many の非同期処理定義
    async def fetch_many(
        self,
        urls: list[str],
        concurrency: int = 5,
    ) -> dict[str, str]:
        """Fetch multiple URLs in parallel with concurrency limit.

        Args:
            urls: URLs to fetch.
            concurrency: Maximum concurrent fetches.

        Returns:
            Mapping of URL → extracted text (only successful fetches).
        """
        sem = asyncio.Semaphore(concurrency)

        # PURPOSE: [L2-auto] _limited_fetch の非同期処理定義
        async def _limited_fetch(url: str) -> tuple[str, str | None]:
            async with sem:
                text = await self.fetch_one(url)
                return url, text

        tasks = [_limited_fetch(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        fetched: dict[str, str] = {}
        for result in results:
            if isinstance(result, tuple):
                url, text = result
                if text:
                    fetched[url] = text
            elif isinstance(result, Exception):
                logger.debug("Fetch exception: %s", result)

        logger.info(
            "PageFetcher: %d/%d URLs fetched successfully",
            len(fetched), len(urls),
        )
        return fetched

    # PURPOSE: [L2-auto] _fetch_httpx の非同期処理定義
    async def _fetch_httpx(self, url: str) -> str | None:
        """Fast path: httpx GET + content-type routing.

        Supports HTML (trafilatura) and Document (markitdown) extraction.
        Includes 1 retry with alternative User-Agent on failure.
        """
        user_agents = [
            (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            (
                "Mozilla/5.0 (compatible; Periskope/1.0; "
                "+https://github.com/hegemonikon)"
            ),
        ]

        for attempt, ua in enumerate(user_agents):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    follow_redirects=True,
                    headers={"User-Agent": ua},
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()

                    content_type = response.headers.get("content-type", "")

                    # Document extraction
                    doc_extensions = (".pdf", ".docx", ".pptx", ".xlsx", ".csv")
                    is_doc = any(url.lower().endswith(ext) for ext in doc_extensions)
                    is_doc_ctype = "application/pdf" in content_type or "application/vnd.openxmlformats" in content_type
                    if is_doc_ctype or is_doc:
                        text = self._extract_document(response.content, url)
                        if text:
                            logger.debug(
                                "httpx+markitdown: %d chars from %s",
                                len(text), url[:60],
                            )
                        return text

                    # HTML extraction
                    if "text/html" not in content_type and "text/plain" not in content_type:
                        logger.debug("Unsupported content type: %s for %s", content_type, url[:60])
                        return None

                    html = response.text

                # Extract main text with trafilatura
                text = self._extract_text(html, url)
                if text:
                    logger.debug(
                        "httpx+trafilatura: %d chars from %s",
                        len(text), url[:60],
                    )
                return text

            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                logger.debug("HTTP %d for %s (attempt %d)", status, url[:60], attempt + 1)
                if status in (403, 429) and attempt < len(user_agents) - 1:
                    continue  # Retry with different User-Agent
                return None
            except (httpx.TimeoutException, httpx.ConnectError) as e:  # noqa: BLE001
                logger.debug("httpx %s for %s (attempt %d)", type(e).__name__, url[:60], attempt + 1)
                if attempt < len(user_agents) - 1:
                    continue  # Retry
                return None
            except Exception as e:  # noqa: BLE001
                logger.debug("httpx fetch failed for %s: %s", url[:60], e)
                return None

        return None

    # PURPOSE: [L2-auto] _extract_document の関数定義
    @staticmethod
    def _extract_document(doc_bytes: bytes, url: str) -> str | None:
        """Extract text from Document bytes using markitdown.

        Returns None if markitdown is not installed or extraction fails.
        """
        try:
            import io
            from markitdown import MarkItDown

            md = MarkItDown()
            # Let magika infer the file type from bytes
            res = md.convert(io.BytesIO(doc_bytes))
            text = res.text_content
            if text and text.strip():
                return text.strip()
            return None
        except ImportError:
            logger.debug("markitdown not installed — Document extraction unavailable")
            return None
        except Exception as e:  # noqa: BLE001
            logger.debug("Document extraction failed: %s", e)
            return None

    # PURPOSE: [L2-auto] _extract_text の関数定義
    @staticmethod
    def _extract_text(html: str, url: str = "") -> str | None:
        """Extract main text from HTML using trafilatura.

        Falls back to basic tag stripping if trafilatura is unavailable.
        """
        try:
            import trafilatura
            text = trafilatura.extract(
                html,
                url=url,
                include_comments=False,
                include_tables=True,
                include_formatting=True,  # Preserve heading structure (Markdown)
                favor_recall=True,
            )
            return text
        except ImportError:
            logger.warning(
                "trafilatura not installed — falling back to basic extraction. "
                "Install with: pip install trafilatura"
            )
            # Basic fallback: strip HTML tags
            import re
            text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
            text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text if len(text) > 100 else None
        except Exception as e:  # noqa: BLE001
            logger.debug("trafilatura extraction failed: %s", e)
            return None

    # PURPOSE: [L2-auto] _fetch_playwright の非同期処理定義
    async def _fetch_playwright(self, url: str) -> str | None:
        """Fallback: use Playwright for JS-rendered pages."""
        try:
            if self._playwright is None:
                from mekhane.periskope.searchers.playwright_searcher import PlaywrightSearcher
                self._playwright = PlaywrightSearcher(timeout=self.timeout)

            text = await self._playwright.fetch_page(url)
            if text:
                logger.debug(
                    "Playwright fallback: %d chars from %s",
                    len(text), url[:60],
                )
            return text
        except Exception as e:  # noqa: BLE001
            logger.debug("Playwright fallback failed for %s: %s", url[:60], e)
            return None
