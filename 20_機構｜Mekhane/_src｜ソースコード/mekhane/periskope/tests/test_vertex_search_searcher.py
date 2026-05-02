# PROOF: mekhane/periskope/tests/test_vertex_search_searcher.py
# PURPOSE: periskope モジュールの vertex_search_searcher に対するテスト
"""
Tests for VertexSearchSearcher (Discovery Engine API).

Tests both mock (offline) and live (online, requires gcloud ADC) scenarios.
Covers: single-engine, multi-engine, SA key auth, ADC fallback, gcloud fallback,
        result deduplication, backward compatibility.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from mekhane.periskope.models import SearchResult, SearchSource
from mekhane.periskope.searchers.vertex_search_searcher import (
    EngineConfig,
    VertexSearchSearcher,
    _truncate,
)


# ─── Fixtures ───────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clear_token_cache():
    """Clear class-level token cache between tests."""
    VertexSearchSearcher._token_cache.clear()
    yield
    VertexSearchSearcher._token_cache.clear()


@pytest.fixture
def searcher():
    """Single-engine searcher (legacy mode)."""
    return VertexSearchSearcher(
        project="951023173830",
        engine_id="hgk-search_1771900372482",
        location="global",
        timeout=10.0,
    )


@pytest.fixture
def multi_searcher():
    """Multi-engine searcher."""
    return VertexSearchSearcher(
        engines=[
            {
                "project": "111111111",
                "engine_id": "engine-a",
                "location": "global",
            },
            {
                "project": "222222222",
                "engine_id": "engine-b",
                "location": "global",
            },
        ],
        timeout=10.0,
    )


@pytest.fixture
def unconfigured_searcher():
    """Searcher without project/engine — should be unavailable."""
    with patch.dict(os.environ, {}, clear=True):
        return VertexSearchSearcher(project="", engine_id="")


# ─── EngineConfig Tests ────────────────────────────────────────


class TestEngineConfig:
    def test_available_with_both(self):
        ec = EngineConfig(project="123", engine_id="eng")
        assert ec.available is True

    def test_unavailable_without_engine(self):
        ec = EngineConfig(project="123", engine_id="")
        assert ec.available is False

    def test_label_auto_generated(self):
        ec = EngineConfig(project="123", engine_id="eng")
        assert ec.label == "123/eng"

    def test_label_custom(self):
        ec = EngineConfig(project="123", engine_id="eng", label="my-engine")
        assert ec.label == "my-engine"


# ─── Availability Tests ────────────────────────────────────────


class TestAvailability:
    def test_available_single_engine(self, searcher: VertexSearchSearcher):
        assert searcher.available is True

    def test_available_multi_engine(self, multi_searcher: VertexSearchSearcher):
        assert multi_searcher.available is True
        assert len(multi_searcher._engines) == 2

    def test_unavailable_without_config(
        self, unconfigured_searcher: VertexSearchSearcher
    ):
        assert unconfigured_searcher.available is False

    @pytest.mark.asyncio
    async def test_search_returns_empty_when_unavailable(
        self, unconfigured_searcher: VertexSearchSearcher
    ):
        results = await unconfigured_searcher.search("test query")
        assert results == []
        await unconfigured_searcher.close()

    def test_engines_from_list(self):
        """Multi-engine via engines= parameter."""
        s = VertexSearchSearcher(
            engines=[
                {"project": "p1", "engine_id": "e1"},
                {"project": "", "engine_id": ""},  # invalid — should be filtered
                {"project": "p2", "engine_id": "e2"},
            ]
        )
        assert s.available is True
        assert len(s._engines) == 2  # invalid one filtered out


# ─── Truncate Tests ────────────────────────────────────────────


class TestTruncate:
    def test_short_text_unchanged(self):
        assert _truncate("hello", 10) == "hello"

    def test_exact_length_unchanged(self):
        assert _truncate("12345", 5) == "12345"

    def test_long_text_truncated(self):
        result = _truncate("a" * 100, 20)
        assert len(result) == 20
        assert result.endswith("...")


# ─── Token Cache Tests ─────────────────────────────────────────


class TestTokenAuth:
    def test_sa_key_priority(self, searcher):
        """SA key is tried first."""
        searcher._engines[0].credentials_file = "/tmp/fake.json"
        with patch("os.path.isfile", return_value=True), \
             patch.object(VertexSearchSearcher, "_token_from_sa_key", return_value="sa-token") as mock_sa, \
             patch.object(VertexSearchSearcher, "_token_from_adc", return_value="adc-token") as mock_adc, \
             patch.object(VertexSearchSearcher, "_token_from_gcloud", return_value="gcloud-token") as mock_gcloud:
            token = searcher._get_access_token(searcher._engines[0])

        assert token == "sa-token"
        mock_adc.assert_not_called()
        mock_gcloud.assert_not_called()

    def test_gcloud_priority(self, searcher):
        """gcloud is prioritized over ADC."""
        with patch.object(VertexSearchSearcher, "_token_from_adc", return_value="adc-token") as mock_adc, \
             patch.object(VertexSearchSearcher, "_token_from_gcloud", return_value="gcloud-token"):
            token = searcher._get_access_token(searcher._engines[0])
        assert token == "gcloud-token"

    def test_adc_fallback(self, searcher):
        """Falls back to ADC when gcloud fails."""
        with patch.object(VertexSearchSearcher, "_token_from_adc", return_value="adc-token") as mock_adc, \
             patch.object(VertexSearchSearcher, "_token_from_gcloud", return_value=""):
            token = searcher._get_access_token(searcher._engines[0])
        assert token == "adc-token"

    def test_all_auth_fail(self, searcher):
        """All auth methods fail → empty token."""
        with patch.object(VertexSearchSearcher, "_token_from_adc", return_value=""), \
             patch.object(VertexSearchSearcher, "_token_from_gcloud", return_value=""):
            token = searcher._get_access_token(searcher._engines[0])
        assert token == ""

    def test_token_cached(self, searcher):
        """Token is cached (second call doesn't re-auth)."""
        with patch.object(VertexSearchSearcher, "_token_from_adc", return_value="cached-token") as mock_adc, \
             patch.object(VertexSearchSearcher, "_token_from_gcloud", return_value=""):
            t1 = searcher._get_access_token(searcher._engines[0])
            t2 = searcher._get_access_token(searcher._engines[0])

        assert t1 == t2 == "cached-token"
        assert mock_adc.call_count == 1  # Only one actual auth call


# ─── Result Parsing Tests ──────────────────────────────────────


class TestResultParsing:
    MOCK_API_RESPONSE = {
        "results": [
            {
                "document": {
                    "id": "doc-001",
                    "name": "projects/123/locations/global/collections/default_collection/dataStores/ds/branches/0/documents/doc-001",
                    "derivedStructData": {
                        "link": "https://example.com/page1",
                        "title": "Page One",
                        "snippets": [
                            {"snippet": "The <b>Model Context Protocol</b> enables..."}
                        ],
                    },
                }
            },
            {
                "document": {
                    "id": "doc-002",
                    "name": "projects/123/locations/global/dataStores/ds/documents/doc-002",
                    "derivedStructData": {
                        "link": "https://example.com/page2",
                        "title": "Page Two",
                        "snippets": [],
                    },
                }
            },
        ],
        "summary": {"summaryText": "Summary text..."},
    }

    @pytest.mark.asyncio
    async def test_parse_results(self, searcher: VertexSearchSearcher):
        with patch.object(searcher, "_get_access_token", return_value="tok"):
            mock_response = MagicMock()
            mock_response.json.return_value = self.MOCK_API_RESPONSE
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)

            with patch.object(searcher, "_get_client", return_value=mock_client):
                results = await searcher.search("test", max_results=5)

        assert len(results) == 2
        r0 = results[0]
        assert r0.source == SearchSource.VERTEX_SEARCH
        assert r0.title == "Page One"
        assert "Model Context Protocol" in r0.content
        assert "<b>" not in r0.content
        assert 0.0 <= r0.relevance <= 1.0
        assert r0.metadata["engine_id"] == "hgk-search_1771900372482"

        r1 = results[1]
        assert r1.content == ""
        await searcher.close()


# ─── Multi-Engine Deduplication Tests ──────────────────────────


class TestMultiEngineDedup:
    @pytest.mark.asyncio
    async def test_dedup_keeps_highest_relevance(
        self, multi_searcher: VertexSearchSearcher
    ):
        """Same URL from two engines → keep highest relevance."""

        async def mock_search_a(engine, query, max_results, site_search, data_store_filter):
            if engine.engine_id == "engine-a":
                return [
                    SearchResult(
                        source=SearchSource.VERTEX_SEARCH,
                        title="Shared Page",
                        url="https://shared.com/page",
                        content="...",
                        snippet="...",
                        relevance=0.8,
                        metadata={"engine_id": "engine-a"},
                    ),
                    SearchResult(
                        source=SearchSource.VERTEX_SEARCH,
                        title="Unique A",
                        url="https://unique-a.com",
                        content="...",
                        snippet="...",
                        relevance=0.6,
                        metadata={"engine_id": "engine-a"},
                    ),
                ]
            else:
                return [
                    SearchResult(
                        source=SearchSource.VERTEX_SEARCH,
                        title="Shared Page",
                        url="https://shared.com/page",
                        content="better snippet",
                        snippet="better snippet",
                        relevance=0.95,
                        metadata={"engine_id": "engine-b"},
                    ),
                    SearchResult(
                        source=SearchSource.VERTEX_SEARCH,
                        title="Unique B",
                        url="https://unique-b.com",
                        content="...",
                        snippet="...",
                        relevance=0.7,
                        metadata={"engine_id": "engine-b"},
                    ),
                ]

        with patch.object(
            multi_searcher, "_search_single_engine", side_effect=mock_search_a
        ):
            results = await multi_searcher.search("test", max_results=10)

        # 3 unique URLs (shared deduped to 1)
        assert len(results) == 3
        urls = {r.url for r in results}
        assert "https://shared.com/page" in urls
        assert "https://unique-a.com" in urls
        assert "https://unique-b.com" in urls

        # Shared page should have max relevance (0.95 from engine-b)
        shared = [r for r in results if r.url == "https://shared.com/page"][0]
        assert shared.relevance == 0.95
        assert shared.metadata["engine_id"] == "engine-b"

        # Results should be sorted by relevance descending
        relevances = [r.relevance for r in results]
        assert relevances == sorted(relevances, reverse=True)

        await multi_searcher.close()


# ─── Error Handling Tests ──────────────────────────────────────


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_no_token_returns_empty(self, searcher: VertexSearchSearcher):
        with patch.object(searcher, "_get_access_token", return_value=""):
            results = await searcher.search("test")
            assert results == []
        await searcher.close()

    @pytest.mark.asyncio
    async def test_http_429_returns_empty(self, searcher: VertexSearchSearcher):
        with patch.object(searcher, "_get_access_token", return_value="tok"):
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "429", request=MagicMock(), response=mock_response
            )
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)

            with patch.object(searcher, "_get_client", return_value=mock_client):
                results = await searcher.search("test")

            assert results == []
        await searcher.close()

    @pytest.mark.asyncio
    async def test_http_403_returns_empty(self, searcher: VertexSearchSearcher):
        with patch.object(searcher, "_get_access_token", return_value="tok"):
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "403", request=MagicMock(), response=mock_response
            )
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)

            with patch.object(searcher, "_get_client", return_value=mock_client):
                results = await searcher.search("test")

            assert results == []
        await searcher.close()

    @pytest.mark.asyncio
    async def test_multi_engine_partial_failure(
        self, multi_searcher: VertexSearchSearcher
    ):
        """One engine fails, other succeeds → partial results returned."""

        call_count = 0

        async def mock_search(engine, query, max_results, site_search, data_store_filter):
            nonlocal call_count
            call_count += 1
            if engine.engine_id == "engine-a":
                raise httpx.ConnectError("Connection refused")
            return [
                SearchResult(
                    source=SearchSource.VERTEX_SEARCH,
                    title="From B",
                    url="https://b.com",
                    content="...",
                    snippet="...",
                    relevance=0.9,
                    metadata={"engine_id": "engine-b"},
                )
            ]

        with patch.object(
            multi_searcher, "_search_single_engine", side_effect=mock_search
        ):
            results = await multi_searcher.search("test")

        assert len(results) == 1
        assert results[0].title == "From B"
        await multi_searcher.close()


# ─── Backward Compatibility Tests ──────────────────────────────


class TestBackwardCompat:
    def test_legacy_single_engine_init(self):
        """Old-style init with project/engine_id still works."""
        s = VertexSearchSearcher(
            project="old-project",
            engine_id="old-engine",
            location="us-central1",
        )
        assert s.available is True
        assert len(s._engines) == 1
        assert s._engines[0].project == "old-project"
        assert s._engines[0].location == "us-central1"

    def test_env_var_fallback(self):
        """Env vars work when no explicit config."""
        with patch.dict(
            os.environ,
            {
                "VERTEX_SEARCH_PROJECT": "env-project",
                "VERTEX_SEARCH_ENGINE": "env-engine",
                "VERTEX_SEARCH_CREDENTIALS_FILE": "/tmp/creds.json",
            },
        ):
            s = VertexSearchSearcher()
            assert s.available is True
            assert s._engines[0].project == "env-project"
            assert s._engines[0].credentials_file == "/tmp/creds.json"


# ─── Site Search Tests ─────────────────────────────────────────


class TestSiteSearch:
    @pytest.mark.asyncio
    async def test_site_search_appends_prefix(self, searcher: VertexSearchSearcher):
        captured_payload = {}

        async def capture_post(url, **kwargs):
            captured_payload.update(kwargs.get("json", {}))
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"results": []}
            mock_resp.raise_for_status = MagicMock()
            return mock_resp

        with patch.object(searcher, "_get_access_token", return_value="tok"):
            mock_client = AsyncMock()
            mock_client.post = capture_post
            with patch.object(searcher, "_get_client", return_value=mock_client):
                await searcher.search("active inference", site_search="arxiv.org")

        assert captured_payload["query"] == "site:arxiv.org active inference"
        await searcher.close()


# ─── Integration Test (requires gcloud ADC) ────────────────────


@pytest.mark.skipif(
    not os.getenv("VERTEX_SEARCH_PROJECT"),
    reason="VERTEX_SEARCH_PROJECT not set — skip live API test",
)
@pytest.mark.asyncio
async def test_live_search():
    """Live API test — requires ADC and configured data store."""
    searcher = VertexSearchSearcher()
    assert searcher.available

    results = await searcher.search("MCP server", max_results=3)
    assert len(results) > 0
    assert len(results) <= 3

    for r in results:
        assert r.source == SearchSource.VERTEX_SEARCH
        assert r.title
        assert r.url
        assert 0.0 <= r.relevance <= 1.0
        assert r.metadata.get("engine_id")

    await searcher.close()
