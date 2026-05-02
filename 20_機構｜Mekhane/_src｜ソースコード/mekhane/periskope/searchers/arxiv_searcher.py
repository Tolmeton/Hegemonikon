from __future__ import annotations
# PROOF: mekhane/periskope/searchers/arxiv_searcher.py
# PURPOSE: periskope モジュールの arxiv_searcher
"""
arXiv API client for Periskopē.

arXiv provides open access to scholarly articles in physics, mathematics,
computer science, and related fields. The API is free with no key required.

API docs: https://info.arxiv.org/help/api/index.html
"""


import logging
import re
from typing import Any
from xml.etree import ElementTree

import httpx

from mekhane.periskope.models import SearchResult, SearchSource

logger = logging.getLogger(__name__)

# arXiv API endpoint (Atom feed)
_ARXIV_API_URL = "https://export.arxiv.org/api/query"

# XML namespaces
_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


class ArxivSearcher:
    """Client for arXiv API.

    Provides access to scholarly preprints with:
    - Full text abstracts
    - Author and category metadata
    - No API key required
    - Rate limit: ~1 request per 3 seconds recommended

    No authentication required.
    """

    def __init__(self, timeout: float = 15.0) -> None:
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def available(self) -> bool:
        """arXiv API is always available (no key needed)."""
        return True

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                headers={"User-Agent": "Periskope/1.0 (HGK Deep Research)"},
            )
        return self._client

    async def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "descending",
    ) -> list[SearchResult]:
        """Search arXiv via the Atom API.

        Args:
            query: Search query (supports arXiv query syntax).
            max_results: Maximum results (1-100).
            sort_by: Sort criterion ('relevance', 'lastUpdatedDate', 'submittedDate').
            sort_order: Sort direction ('ascending', 'descending').

        Returns:
            List of SearchResult from arXiv.
        """
        # Build arXiv search query
        search_query = f"all:{query}"

        params: dict[str, Any] = {
            "search_query": search_query,
            "start": 0,
            "max_results": min(max_results, 100),
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        import urllib.parse
        import asyncio
        url = f"{_ARXIV_API_URL}?{urllib.parse.urlencode(params)}"
        try:
            cmd = ["curl", "-s", "-L", "-A", "Periskope/1.0 (HGK Deep Research)", url]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=min(self._timeout, 15.0))
            
            if proc.returncode != 0:
                logger.error("arXiv curl error (code %s): %s", proc.returncode, stderr.decode(errors="ignore"))
                return []
                
            xml_text = stdout.decode("utf-8", errors="ignore")
        except asyncio.TimeoutError:
            logger.error("arXiv search curl timeout")
            return []
        except Exception as e:  # noqa: BLE001
            logger.error("arXiv search curl execution error: %s", e)
            return []

        # Parse Atom XML
        return self._parse_atom(xml_text, max_results)

    def _parse_atom(self, xml_text: str, max_results: int) -> list[SearchResult]:
        """Parse arXiv Atom XML response into SearchResult list."""
        try:
            root = ElementTree.fromstring(xml_text)
        except ElementTree.ParseError as e:
            logger.error("arXiv XML parse error: %s", e)
            return []

        entries = root.findall("atom:entry", _NS)
        results: list[SearchResult] = []

        for i, entry in enumerate(entries[:max_results]):
            title = (entry.findtext("atom:title", "", _NS) or "").strip()
            title = re.sub(r"\s+", " ", title)  # Normalize whitespace

            summary = (entry.findtext("atom:summary", "", _NS) or "").strip()
            summary = re.sub(r"\s+", " ", summary)

            # Get the arXiv ID and construct URL
            entry_id = entry.findtext("atom:id", "", _NS) or ""
            # entry_id is like http://arxiv.org/abs/2301.12345v1
            arxiv_id = entry_id.split("/abs/")[-1] if "/abs/" in entry_id else ""

            # Get PDF link
            pdf_url = ""
            for link in entry.findall("atom:link", _NS):
                if link.get("title") == "pdf":
                    pdf_url = link.get("href", "")
                    break

            # Authors
            authors = []
            for author in entry.findall("atom:author", _NS):
                name = author.findtext("atom:name", "", _NS)
                if name:
                    authors.append(name)

            # Categories
            categories = []
            for cat in entry.findall("atom:category", _NS):
                term = cat.get("term", "")
                if term:
                    categories.append(term)

            # Published date
            published = entry.findtext("atom:published", "", _NS) or ""

            # Relevance: position-based scoring (1.0 → 0.5)
            relevance = 1.0 - (i / max(len(entries), 1)) * 0.5

            content = summary
            if authors:
                content = f"Authors: {', '.join(authors[:5])}\n\n{summary}"

            result = SearchResult(
                source=SearchSource.ARXIV,
                title=title,
                url=entry_id or None,
                content=content,
                snippet=_truncate(summary, 200),
                relevance=relevance,
                timestamp=published[:10] if published else None,
                metadata={
                    "arxiv_id": arxiv_id,
                    "pdf_url": pdf_url,
                    "authors": authors,
                    "categories": categories,
                },
            )
            results.append(result)

        logger.info("arXiv: %d results for query", len(results))
        return results

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
