from __future__ import annotations
# PROOF: mekhane/periskope/searchers/semantic_scholar_searcher.py
# PURPOSE: periskope モジュールの semantic_scholar_searcher
"""
Semantic Scholar API client for Periskopē.

Provides free, unlimited access to academic paper search.
No API key required (but recommended for higher rate limits).
Rate limits: 1 RPS with key, shared 5000/5min without.

Uses curl subprocess instead of httpx to bypass Python DNS/TLS hangs.
Python's getaddrinfo() blocks the event loop on some networks (IPv6 AAAA
lookup timeout). curl uses the system resolver and handles this correctly.

API docs: https://api.semanticscholar.org/api-docs/
"""


import asyncio
import json
import logging
import os
import urllib.parse
from typing import Any

from mekhane.periskope.models import SearchResult, SearchSource

logger = logging.getLogger(__name__)

_S2_API_URL = "https://api.semanticscholar.org/graph/v1"
_S2_SEARCH_URL = f"{_S2_API_URL}/paper/search"

# Rate limit retry config
_MAX_RETRIES = 3
_INITIAL_BACKOFF = 2.0  # seconds


# PURPOSE: Semantic Scholar API client (curl-based)
class SemanticScholarSearcher:
    """Client for Semantic Scholar API.

    Free academic paper search with:
    - Semantic (meaning-based) paper search
    - Citation data, abstracts, author info
    - No API key required (but recommended)
    - Rate limit: 1 RPS (with key) / shared pool (without)
    - Auto-retry on 429 with exponential backoff (2s→4s→8s)
    - Uses curl subprocess to bypass Python DNS/TLS hangs

    Optional: S2_API_KEY environment variable for higher limits.
    """

    # PURPOSE: 初期化
    def __init__(self, timeout: float = 20.0) -> None:
        self._api_key = os.getenv("S2_API_KEY") or os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        self._timeout = timeout

    # PURPOSE: 利用可能性チェック
    @property
    def available(self) -> bool:
        """Always available (no key required, key is optional)."""
        return True

    # PURPOSE: curl subprocess で S2 API にアクセス (Python DNS ハング回避)
    async def _curl_fetch(
        self,
        url: str,
        headers: dict[str, str],
    ) -> tuple[int, dict | None]:
        """Fetch URL via curl subprocess.

        Returns (http_status_code, parsed_json_or_None).
        Forces IPv4 (-4) to avoid AAAA lookup timeout.
        """
        curl_headers = []
        for k, v in headers.items():
            curl_headers.extend(["-H", f"{k}: {v}"])

        cmd = [
            "curl", "-s", "-4",  # Force IPv4
            "--connect-timeout", "10",
            "--max-time", str(int(self._timeout)),
            "-w", "\n%{http_code}",
            *curl_headers,
            url,
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self._timeout + 5,
            )
            output = stdout.decode("utf-8", errors="replace")

            # Parse: body + last line = HTTP status code
            lines = output.rstrip().rsplit("\n", 1)
            if len(lines) == 2:
                body, status_str = lines
            else:
                body = output
                status_str = "0"

            status_code = int(status_str) if status_str.isdigit() else 0

            if status_code == 200 and body.strip():
                return status_code, json.loads(body)
            else:
                return status_code, None

        except asyncio.TimeoutError:
            logger.error("S2: curl timed out after %.0fs", self._timeout + 5)
            return 0, None
        except json.JSONDecodeError as e:
            logger.error("S2: JSON parse error: %s", e)
            return 200, None
        except Exception as e:  # noqa: BLE001
            logger.error("S2: curl failed: %s", e)
            return 0, None

    # PURPOSE: search の非同期処理定義
    async def search(
        self,
        query: str,
        max_results: int = 10,
        year_range: str | None = None,
        fields_of_study: list[str] | None = None,
        open_access_only: bool = False,
    ) -> list[SearchResult]:
        """Search academic papers via Semantic Scholar.

        Args:
            query: Search query.
            max_results: Maximum results (1-100).
            year_range: Year filter (e.g., '2023-2026', '2024-').
            fields_of_study: Filter by field (e.g., ['Computer Science']).
            open_access_only: Only return open access papers.

        Returns:
            List of SearchResult from Semantic Scholar.
        """
        headers: dict[str, str] = {}
        if self._api_key:
            headers["x-api-key"] = self._api_key

        params: dict[str, Any] = {
            "query": query,
            "limit": min(max_results, 100),
            "fields": "title,abstract,url,year,authors,citationCount,"
                      "externalIds,openAccessPdf,publicationDate,"
                      "journal,fieldsOfStudy",
        }
        if year_range:
            params["year"] = year_range
        if fields_of_study:
            params["fieldsOfStudy"] = ",".join(fields_of_study)
        if open_access_only:
            params["openAccessPdf"] = ""

        # Build URL with query string
        query_string = urllib.parse.urlencode(params)
        url = f"{_S2_SEARCH_URL}?{query_string}"

        # Retry with exponential backoff on 429
        data: dict | None = None
        for attempt in range(_MAX_RETRIES + 1):
            status, data = await self._curl_fetch(url, headers)

            if status == 200 and data is not None:
                break
            elif status == 429:
                backoff = _INITIAL_BACKOFF * (2 ** attempt)
                logger.warning(
                    "S2 rate limited (429), retry %d/%d in %.1fs",
                    attempt + 1, _MAX_RETRIES, backoff,
                )
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(backoff)
                    continue
                else:
                    logger.error(
                        "S2 rate limit exhausted after %d retries", _MAX_RETRIES,
                    )
                    return []
            else:
                logger.error("S2 search failed with status %d", status)
                return []

        if data is None:
            return []

        # Parse results
        results: list[SearchResult] = []
        papers = data.get("data", [])

        for i, paper in enumerate(papers[:max_results]):
            title = paper.get("title", "Untitled")
            abstract = paper.get("abstract", "")
            url_str = paper.get("url", "")

            # Build author string
            authors = paper.get("authors", [])
            author_str = ", ".join(
                a.get("name", "") for a in authors[:5]
            )
            if len(authors) > 5:
                author_str += f" et al. ({len(authors)} authors)"

            # Get external IDs
            ext_ids = paper.get("externalIds", {}) or {}
            doi = ext_ids.get("DOI")
            arxiv_id = ext_ids.get("ArXiv")

            # Open access PDF
            oa_pdf = paper.get("openAccessPdf")
            pdf_url = oa_pdf.get("url") if oa_pdf else None

            # Relevance: S2 returns in relevance order
            citation_count = paper.get("citationCount", 0) or 0
            # Combine position with citation impact
            position_score = 1.0 - (i / max(len(papers), 1)) * 0.5
            citation_boost = min(citation_count / 1000, 0.3)
            relevance = position_score + citation_boost

            content = abstract or ""
            if author_str:
                content = f"Authors: {author_str}\n\n{content}"

            result = SearchResult(
                source=SearchSource.SEMANTIC_SCHOLAR,
                title=title,
                url=url_str or None,
                content=content[:1000],
                snippet=_truncate(abstract or title, 200),
                relevance=relevance,
                timestamp=paper.get("publicationDate"),
                metadata={
                    "authors": author_str,
                    "citations": citation_count,
                    "year": paper.get("year"),
                    "doi": doi,
                    "arxiv_id": arxiv_id,
                    "pdf_url": pdf_url,
                    "journal": (paper.get("journal") or {}).get("name", ""),
                    "fields_of_study": paper.get("fieldsOfStudy", []),
                },
            )
            results.append(result)

        logger.info(
            "Semantic Scholar: %d results for %r", len(results), query,
        )
        return results


# PURPOSE: テキスト切り詰めユーティリティ
def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
