from __future__ import annotations
# PROOF: mekhane/periskope/searchers/vertex_search_searcher.py
# PURPOSE: periskope モジュールの vertex_search_searcher
"""
Vertex AI Search (Discovery Engine API) client for Periskopē.

Uses the Discovery Engine API to search custom data stores
containing internal knowledge, academic sites, and niche domains.
Returns direct URLs (not redirect URLs like Gemini Grounding).

Supports:
    - Multiple GCP accounts / engines (parallel query)
    - Service Account JSON key authentication (google-auth)
    - Application Default Credentials (ADC) fallback
    - gcloud CLI fallback (subprocess)

Configuration (config.yaml):
    # Multi-engine (recommended):
    vertex_search:
      enabled: true
      engines:
        - project: "123456789"
          engine_id: "my-engine"
          credentials_file: "/path/to/sa-key.json"
        - project: "987654321"
          engine_id: "my-engine-2"
          credentials_file: "/path/to/sa-key-2.json"

    # Legacy single-engine (backward compatible):
    vertex_search:
      enabled: true
      project: "123456789"
      engine_id: "my-engine"

Environment variable overrides:
    VERTEX_SEARCH_PROJECT, VERTEX_SEARCH_ENGINE, VERTEX_SEARCH_LOCATION
    VERTEX_SEARCH_CREDENTIALS_FILE
"""


import asyncio
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import Any

import httpx

from mekhane.periskope.models import SearchResult, SearchSource

logger = logging.getLogger(__name__)

_DISCOVERY_ENGINE_BASE = (
    "https://discoveryengine.googleapis.com/v1/projects/{project}"
    "/locations/{location}/collections/default_collection"
    "/engines/{engine}/servingConfigs/default_search:search"
)


@dataclass
class EngineConfig:
    """Configuration for a single Discovery Engine instance."""

    project: str = ""
    engine_id: str = ""
    location: str = "global"
    credentials_file: str = ""
    gcloud_account: str = ""  # e.g. "Tolmetes@hegemonikon.org"
    label: str = ""  # human-readable label for logging

    @property
    def available(self) -> bool:
        return bool(self.project and self.engine_id)

    def __post_init__(self):
        if not self.label:
            self.label = f"{self.project}/{self.engine_id}"


class VertexSearchSearcher:
    """Discovery Engine API client for Vertex AI Search.

    Searches custom data stores containing internal knowledge,
    academic papers, and niche domain content. Returns direct URLs
    with relevance scores.

    Supports multiple engines (across GCP accounts) with parallel
    query execution and result deduplication.

    Auth priority per engine:
        1. SA key JSON file (credentials_file)
        2. gcloud CLI with --account= (gcloud_account)
        3. Application Default Credentials (ADC) — last resort,
           may hang on non-GCE environments
    """

    # Class-level token cache: shared across instances to avoid
    # redundant gcloud subprocess calls within the same process.
    _token_cache: dict[str, tuple[str, float]] = {}

    def __init__(
        self,
        project: str = "",
        engine_id: str = "",
        location: str = "global",
        credentials_file: str = "",
        timeout: float = 15.0,
        engines: list[dict[str, str]] | None = None,
    ) -> None:
        self._timeout = timeout
        self._clients: dict[str, httpx.AsyncClient] = {}

        # Build engine configs
        self._engines: list[EngineConfig] = []

        if engines:
            # Multi-engine mode (from config.yaml engines list)
            for eng in engines:
                self._engines.append(
                    EngineConfig(
                        project=eng.get("project", ""),
                        engine_id=eng.get("engine_id", ""),
                        location=eng.get("location", "global"),
                        credentials_file=eng.get(
                            "credentials_file",
                            os.getenv("VERTEX_SEARCH_CREDENTIALS_FILE", ""),
                        ),
                        gcloud_account=eng.get("gcloud_account", ""),
                    )
                )
        else:
            # Single-engine mode (legacy / env vars)
            self._engines.append(
                EngineConfig(
                    project=project
                    or os.getenv("VERTEX_SEARCH_PROJECT", ""),
                    engine_id=engine_id
                    or os.getenv("VERTEX_SEARCH_ENGINE", ""),
                    location=location
                    or os.getenv("VERTEX_SEARCH_LOCATION", "global"),
                    credentials_file=credentials_file
                    or os.getenv("VERTEX_SEARCH_CREDENTIALS_FILE", ""),
                )
            )

        # Filter to available engines only
        self._engines = [e for e in self._engines if e.available]

    @property
    def available(self) -> bool:
        """Check if at least one engine is configured."""
        return len(self._engines) > 0

    def _get_access_token(self, engine: EngineConfig) -> str:
        """Get OAuth2 access token for a specific engine.

        Priority:
            1. SA key JSON file (credentials_file)
            2. gcloud CLI with --account= (gcloud_account)
            3. ADC fallback (last resort — may hang on non-GCE)
        """
        import time

        cache_key = engine.label

        # Return cached token if still valid (refresh 60s before expiry)
        if cache_key in self._token_cache:
            token, expiry = self._token_cache[cache_key]
            if time.time() < expiry - 60:
                return token

        token = ""

        # 1. Try SA key file
        creds_file = engine.credentials_file
        if creds_file and os.path.isfile(creds_file):
            token = self._token_from_sa_key(creds_file)
            if token:
                self._token_cache[cache_key] = (token, time.time() + 3300)
                return token

        # 2. Try gcloud CLI (fast on local dev machines)
        token = self._token_from_gcloud(engine.gcloud_account)
        if token:
            self._token_cache[cache_key] = (token, time.time() + 3300)
            return token

        # 3. Fallback to ADC (may hang on non-GCE environments)
        token = self._token_from_adc()
        if token:
            self._token_cache[cache_key] = (token, time.time() + 3300)
            return token

        logger.error("No access token available for %s", engine.label)
        return ""

    @staticmethod
    def _token_from_sa_key(creds_file: str) -> str:
        """Get token from Service Account JSON key file.

        Uses PyJWT + httpx instead of google.auth to avoid hangs
        caused by google.auth.transport.requests.Request().
        """
        try:
            import json as _json
            import time as _time

            import jwt as _jwt

            with open(creds_file) as f:
                sa = _json.load(f)

            now = int(_time.time())
            payload = {
                "iss": sa["client_email"],
                "sub": sa["client_email"],
                "aud": "https://oauth2.googleapis.com/token",
                "iat": now,
                "exp": now + 3600,
                "scope": "https://www.googleapis.com/auth/cloud-platform",
            }
            assertion = _jwt.encode(payload, sa["private_key"], algorithm="RS256")

            # Synchronous httpx call (this runs in a sync context)
            resp = httpx.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": assertion,
                },
                timeout=10.0,
            )
            if resp.status_code == 200:
                return resp.json().get("access_token", "")
            logger.warning(
                "SA key token exchange failed (%s): %s %s",
                creds_file, resp.status_code, resp.text[:200],
            )
            return ""
        except Exception as e:  # noqa: BLE001
            logger.warning("SA key auth failed (%s): %s", creds_file, e)
            return ""

    @staticmethod
    def _token_from_adc() -> str:
        """Get token from Application Default Credentials."""
        try:
            import google.auth
            from google.auth.transport.requests import Request

            credentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            credentials.refresh(Request())
            return credentials.token or ""
        except Exception as e:  # noqa: BLE001
            logger.debug("ADC auth failed: %s", e)
            return ""

    @staticmethod
    def _token_from_gcloud(account: str = "") -> str:
        """Get token from gcloud CLI.

        Args:
            account: Optional Google account email.
                     If set, uses --account=EMAIL to get an
                     account-specific token (multi-account support
                     without SA keys).
        """
        try:
            cmd = ["gcloud", "auth", "print-access-token"]
            if account:
                cmd.append(f"--account={account}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                logger.debug("gcloud auth failed: %s", result.stderr.strip())
                return ""
            return result.stdout.strip()
        except Exception as e:  # noqa: BLE001
            logger.debug("gcloud CLI failed: %s", e)
            return ""

    async def _get_client(self, label: str) -> httpx.AsyncClient:
        if label not in self._clients or self._clients[label].is_closed:
            self._clients[label] = httpx.AsyncClient(timeout=self._timeout)
        return self._clients[label]

    async def _search_single_engine(
        self,
        engine: EngineConfig,
        query: str,
        max_results: int,
        site_search: str,
        data_store_filter: str,
    ) -> list[SearchResult]:
        """Execute search against a single engine."""
        token = self._get_access_token(engine)
        if not token:
            logger.warning("No token for %s — skipping", engine.label)
            return []

        search_query = query
        if site_search:
            search_query = f"site:{site_search} {query}"

        url = _DISCOVERY_ENGINE_BASE.format(
            project=engine.project,
            location=engine.location,
            engine=engine.engine_id,
        )

        payload: dict[str, Any] = {
            "query": search_query,
            "pageSize": min(max_results, 25),
            "queryExpansionSpec": {"condition": "AUTO"},
            "spellCorrectionSpec": {"mode": "AUTO"},
            "contentSearchSpec": {
                "snippetSpec": {"returnSnippet": True},
                "summarySpec": {
                    "summaryResultCount": min(max_results, 5),
                    "includeCitations": True,
                },
            },
        }

        if data_store_filter:
            payload["filter"] = data_store_filter

        try:
            client = await self._get_client(engine.label)
            headers = {"Authorization": f"Bearer {token}"}
            # Quota project header: required when using user account
            # tokens to attribute API usage to the correct project.
            if engine.gcloud_account:
                headers["x-goog-user-project"] = engine.project
            resp = await client.post(
                url,
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(
                    "Vertex Search quota exceeded (%s)", engine.label
                )
            elif e.response.status_code == 403:
                logger.error(
                    "Vertex Search permission denied (%s) — check IAM",
                    engine.label,
                )
            else:
                logger.error(
                    "Vertex Search HTTP error %s (%s): %s",
                    e.response.status_code,
                    engine.label,
                    e.response.text[:200],
                )
            return []
        except Exception as e:  # noqa: BLE001
            logger.error("Vertex Search failed (%s): %s", engine.label, e)
            return []

        # Parse results
        results_data = data.get("results", [])
        results: list[SearchResult] = []

        for i, item in enumerate(results_data[:max_results]):
            doc = item.get("document", {})
            derived = doc.get("derivedStructData", {})

            url_str = derived.get("link", "")
            title = derived.get("title", "")

            # Extract snippet from snippets array
            snippets = derived.get("snippets", [])
            snippet = ""
            if snippets:
                snippet = snippets[0].get("snippet", "")
                # Clean HTML tags from snippet
                snippet = re.sub(r"<[^>]+>", "", snippet)

            relevance = 1.0 - (i / max(len(results_data), 1)) * 0.5

            result = SearchResult(
                source=SearchSource.VERTEX_SEARCH,
                title=title,
                url=url_str or None,
                content=snippet,
                snippet=_truncate(snippet, 200),
                relevance=relevance,
                metadata={
                    "engine_id": engine.engine_id,
                    "engine_label": engine.label,
                    "doc_id": doc.get("id", ""),
                    "data_store": doc.get("name", "").split("/")[-3]
                    if "/" in doc.get("name", "")
                    else "",
                },
            )
            results.append(result)

        # Log summary if available
        summary = data.get("summary", {})
        summary_text = summary.get("summaryText", "")
        if summary_text:
            logger.info(
                "Vertex Search summary (%s): %s",
                engine.label,
                _truncate(summary_text, 100),
            )

        logger.info(
            "Vertex Search: %d results for %r (engine=%s)",
            len(results),
            query,
            engine.label,
        )
        return results

    async def search(
        self,
        query: str,
        max_results: int = 10,
        data_store_filter: str = "",
        date_restrict: str = "",
        site_search: str = "",
    ) -> list[SearchResult]:
        """Search via Discovery Engine API across all configured engines.

        Args:
            query: Search query string.
            max_results: Maximum results to return (total, after dedup).
            data_store_filter: Optional filter for specific data store.
            date_restrict: Not used (kept for API compatibility).
            site_search: Optional site restriction (added to query).

        Returns:
            List of SearchResult, deduplicated by URL, sorted by relevance.
        """
        if not self.available:
            logger.warning(
                "No Vertex Search engines configured — skipping"
            )
            return []

        if len(self._engines) == 1:
            # Single engine — direct call, no gather overhead
            return await self._search_single_engine(
                self._engines[0],
                query,
                max_results,
                site_search,
                data_store_filter,
            )

        # Multi-engine — parallel query
        tasks = [
            self._search_single_engine(
                engine, query, max_results, site_search, data_store_filter
            )
            for engine in self._engines
        ]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten and handle errors — track degradation
        combined: list[SearchResult] = []
        failed_engines: list[str] = []
        for engine, result in zip(self._engines, all_results):
            if isinstance(result, Exception):
                logger.warning(
                    "Vertex Search engine %s failed: %s",
                    engine.label, result,
                )
                failed_engines.append(engine.label)
                continue
            combined.extend(result)

        # Degradation summary
        total = len(self._engines)
        ok = total - len(failed_engines)
        if failed_engines:
            logger.warning(
                "Vertex Search degraded: %d/%d engines OK (failed: %s)",
                ok, total, ", ".join(failed_engines),
            )

        # Deduplicate by URL — keep highest relevance (max)
        seen: dict[str, SearchResult] = {}
        for r in combined:
            url_key = r.url or r.title  # fallback to title if no URL
            if url_key in seen:
                if r.relevance > seen[url_key].relevance:
                    seen[url_key] = r
            else:
                seen[url_key] = r

        # Sort by relevance descending, take top N
        deduped = sorted(seen.values(), key=lambda r: r.relevance, reverse=True)
        return deduped[:max_results]

    async def close(self) -> None:
        for client in self._clients.values():
            if not client.is_closed:
                await client.aclose()
        self._clients.clear()


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
