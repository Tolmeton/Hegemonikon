# PROOF: mekhane/periskope/tests/test_searcher_resilience.py
# PURPOSE: periskope モジュールの searcher_resilience に対するテスト
"""Tests for new searcher resilience and Phi-3 troubleshoot routing.

B: Rate limit resilience — each searcher gracefully handles 429/errors.
C: New searcher mock tests — available property, basic search contract.
A: Phi-3 troubleshoot routing — bug/error queries → SO/GitHub/Reddit.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mekhane.periskope.models import SearchResult, SearchSource


# --- C: Searcher availability tests ---


def test_stackoverflow_always_available():
    from mekhane.periskope.searchers.stackoverflow_searcher import StackOverflowSearcher
    s = StackOverflowSearcher()
    assert s.available is True


def test_reddit_always_available():
    from mekhane.periskope.searchers.reddit_searcher import RedditSearcher
    s = RedditSearcher()
    assert s.available is True


def test_hackernews_always_available():
    from mekhane.periskope.searchers.hackernews_searcher import HackerNewsSearcher
    s = HackerNewsSearcher()
    assert s.available is True


def test_gemini_search_unavailable_without_key():
    from mekhane.periskope.searchers.gemini_searcher import GeminiSearcher
    with patch.dict("os.environ", {}, clear=True):
        s = GeminiSearcher()
        # Without GOOGLE_API_KEY, Gemini Grounding searcher should be unavailable
        assert s._api_key == ""
        assert s.available is False


# --- B: Rate limit resilience tests ---


@pytest.mark.asyncio
async def test_stackoverflow_handles_429():
    """SO searcher returns [] on HTTP 429."""
    from mekhane.periskope.searchers.stackoverflow_searcher import StackOverflowSearcher
    import httpx

    s = StackOverflowSearcher()
    mock_response = MagicMock()
    mock_response.status_code = 502
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(
        side_effect=httpx.HTTPStatusError("throttled", request=MagicMock(), response=mock_response),
    )
    mock_client.is_closed = False
    s._client = mock_client

    results = await s.search("test query")
    assert results == []


@pytest.mark.asyncio
async def test_reddit_handles_429():
    """Reddit searcher returns [] on HTTP 429."""
    from mekhane.periskope.searchers.reddit_searcher import RedditSearcher
    import httpx

    s = RedditSearcher()
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(
        side_effect=httpx.HTTPStatusError("rate limited", request=MagicMock(), response=mock_response),
    )
    mock_client.is_closed = False
    s._client = mock_client

    results = await s.search("test query")
    assert results == []


@pytest.mark.asyncio
async def test_hackernews_handles_error():
    """HN searcher returns [] on network error."""
    from mekhane.periskope.searchers.hackernews_searcher import HackerNewsSearcher
    import httpx

    s = HackerNewsSearcher()
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
    mock_client.is_closed = False
    s._client = mock_client

    results = await s.search("test query")
    assert results == []


@pytest.mark.asyncio
async def test_gemini_search_handles_quota_exceeded():
    """Gemini Search Grounding returns [] on 429 quota exceeded."""
    from mekhane.periskope.searchers.gemini_searcher import GeminiSearcher
    import httpx

    s = GeminiSearcher()
    s._api_key = "fake-key"
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(
        side_effect=httpx.HTTPStatusError("quota", request=MagicMock(), response=mock_response),
    )
    mock_client.is_closed = False
    s._client = mock_client

    results = await s.search("test query")
    assert results == []


# --- B: Phase search resilience (one source fails, others succeed) ---


@pytest.mark.asyncio
async def test_phase_search_resilient_to_single_failure():
    """_phase_search continues when one source raises an exception."""
    from mekhane.periskope.engine import PeriskopeEngine

    engine = PeriskopeEngine()

    # Mock one source to fail, one to succeed
    engine.searxng.search = AsyncMock(
        return_value=[SearchResult(source=SearchSource.SEARXNG, title="Good result")],
    )
    engine.brave.search = AsyncMock(side_effect=Exception("Brave is down"))

    results, counts = await engine._phase_search(
        "test query", enabled={"searxng", "brave"},
    )

    # SearXNG results should still be present
    assert len(results) >= 1
    assert counts.get("searxng", 0) >= 1
    assert counts.get("brave", 0) == 0


# --- A: Phi-3 troubleshoot routing tests ---


def test_classify_troubleshoot_keyword():
    """Bug/error keywords should classify as troubleshoot."""
    from mekhane.periskope.cognition.phi3_context import _classify_query_keyword

    assert _classify_query_keyword("fix asyncio CancelledError in Python") == "troubleshoot"
    assert _classify_query_keyword("how to debug segfault") == "troubleshoot"
    assert _classify_query_keyword("traceback TypeError") == "troubleshoot"
    assert _classify_query_keyword("Python エラー解決") == "troubleshoot"
    assert _classify_query_keyword("バグ修正方法") == "troubleshoot"


def test_troubleshoot_routes_to_stackoverflow():
    """Troubleshoot category should include stackoverflow and github."""
    from mekhane.periskope.cognition.phi3_context import _SOURCE_MAP

    troubleshoot_sources = _SOURCE_MAP["troubleshoot"]
    assert "stackoverflow" in troubleshoot_sources
    assert "github" in troubleshoot_sources
    assert "reddit" in troubleshoot_sources


def test_classify_non_troubleshoot():
    """Non-bug queries should NOT classified as troubleshoot."""
    from mekhane.periskope.cognition.phi3_context import _classify_query_keyword

    assert _classify_query_keyword("free energy principle overview") == "concept"
    assert _classify_query_keyword("latest Python release") == "news"
    assert _classify_query_keyword("arxiv paper on transformers") == "academic"
