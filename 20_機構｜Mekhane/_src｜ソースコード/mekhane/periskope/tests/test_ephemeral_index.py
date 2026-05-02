# PROOF: mekhane/periskope/tests/test_ephemeral_index.py
# PURPOSE: periskope モジュールの ephemeral_index に対するテスト
"""Tests for EphemeralIndex — Shared vector store for Phase Inversion."""

from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from mekhane.periskope.cognition.ephemeral_index import (
    EphemeralIndex,
    IndexEntry,
)


# --- IndexEntry tests ---

def test_index_entry_defaults():
    """IndexEntry has sane defaults."""
    e = IndexEntry(text="hello", source="thesis", entry_type="search_result")
    assert e.text == "hello"
    assert e.source == "thesis"
    assert e.metadata == {}
    assert e.timestamp > 0


# --- Mock embedder for unit tests ---

class MockEmbedder:
    """Deterministic mock embedder for testing."""

    def __init__(self, dim: int = 8):
        self.dim = dim
        self._call_count = 0

    def embed(self, text: str) -> list[float]:
        """Return a deterministic vector based on text hash."""
        np.random.seed(hash(text) % (2**31))
        vec = np.random.randn(self.dim).tolist()
        self._call_count += 1
        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


def _make_index(dim: int = 8) -> EphemeralIndex:
    """Create an EphemeralIndex with mock embedder."""
    idx = EphemeralIndex(dimension=dim)
    idx._embedder = MockEmbedder(dim=dim)
    return idx


# --- Publish tests ---

@pytest.mark.asyncio
async def test_publish_single():
    """Single publish adds entry."""
    idx = _make_index()
    await idx.publish("thesis", "search_result", "Einstein proved E=mc²")
    assert idx.stats()["total_entries"] == 1
    assert idx.stats()["by_source"]["thesis"] == 1


@pytest.mark.asyncio
async def test_publish_ignores_short():
    """Short texts are ignored."""
    idx = _make_index()
    await idx.publish("thesis", "search_result", "short")
    assert idx.stats()["total_entries"] == 0


@pytest.mark.asyncio
async def test_publish_batch():
    """Batch publish adds multiple entries."""
    idx = _make_index()
    texts = [
        "First important finding about quantum mechanics",
        "Second finding about relativity theory and spacetime",
        "Third finding about thermodynamics and entropy",
    ]
    count = await idx.publish_batch("antithesis", "synthesis", texts)
    assert count == 3
    assert idx.stats()["total_entries"] == 3
    assert idx.stats()["by_source"]["antithesis"] == 3


# --- Query tests ---

@pytest.mark.asyncio
async def test_query_excludes_own():
    """By default, query excludes own source's entries."""
    idx = _make_index()
    await idx.publish("thesis", "search_result", "Thesis found evidence for X being true and valid")
    await idx.publish("antithesis", "refutation", "Antithesis found evidence against X being false")

    # Thesis queries — should only see antithesis entries
    results = await idx.query("thesis", "evidence about X", top_k=5)
    assert len(results) == 1
    assert results[0][0].source == "antithesis"


@pytest.mark.asyncio
async def test_query_includes_own_when_requested():
    """Can include own entries."""
    idx = _make_index()
    await idx.publish("thesis", "search_result", "Thesis found evidence for X being true")
    await idx.publish("antithesis", "refutation", "Antithesis argues X is false")

    results = await idx.query("thesis", "evidence X", top_k=5, exclude_own=False)
    assert len(results) == 2


@pytest.mark.asyncio
async def test_query_filter_by_type():
    """Can filter by entry_type."""
    idx = _make_index()
    await idx.publish("antithesis", "search_result", "Search result about quantum physics")
    await idx.publish("antithesis", "refutation", "Refutation of classical hypothesis theory")

    results = await idx.query(
        "thesis", "quantum physics",
        entry_types=["refutation"],
    )
    assert len(results) == 1
    assert results[0][0].entry_type == "refutation"


@pytest.mark.asyncio
async def test_query_empty_index():
    """Empty index returns no results."""
    idx = _make_index()
    results = await idx.query("thesis", "anything here")
    assert results == []


@pytest.mark.asyncio
async def test_query_top_k():
    """Respects top_k limit."""
    idx = _make_index()
    for i in range(10):
        await idx.publish(
            "antithesis", "search_result",
            f"Finding number {i} about topic alpha beta gamma delta epsilon",
        )
    results = await idx.query("thesis", "topic alpha", top_k=3)
    assert len(results) <= 3


# --- Stats and clear ---

@pytest.mark.asyncio
async def test_clear():
    """Clear empties the index."""
    idx = _make_index()
    await idx.publish("thesis", "search_result", "some important finding about X")
    assert idx.stats()["total_entries"] == 1
    idx.clear()
    assert idx.stats()["total_entries"] == 0


@pytest.mark.asyncio
async def test_stats_by_type():
    """Stats tracks by entry type."""
    idx = _make_index()
    await idx.publish("thesis", "search_result", "Thesis search result about topic")
    await idx.publish("thesis", "synthesis", "Thesis synthesis summary of topic")
    await idx.publish("antithesis", "refutation", "Antithesis refutation of claims")

    stats = idx.stats()
    assert stats["by_type"]["search_result"] == 1
    assert stats["by_type"]["synthesis"] == 1
    assert stats["by_type"]["refutation"] == 1
