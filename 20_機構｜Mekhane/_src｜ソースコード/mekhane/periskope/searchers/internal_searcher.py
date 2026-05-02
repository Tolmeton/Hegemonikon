from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/periskope/searchers/internal_searcher.py A0→内部知識検索が必要→internal_searcher が担う
"""
Internal knowledge searcher for Periskopē — Symplokē adapter.

Thin async wrapper around Symplokē's DomainIndex (Single Source of Truth).
Uses asyncio.to_thread() to run sync DomainIndex.search() in a thread pool,
enabling parallel execution alongside external async searchers.

Architecture:
    Symplokē DomainIndex (sync, canonical)
        ↓ asyncio.to_thread()
    GnosisSearcher / SophiaSearcher / KairosSearcher (async, adapter)
        ↓ asyncio.gather() in PeriskopeEngine._phase_search()
    Parallel with SearXNG, Brave, Tavily, etc.
"""


import asyncio
import logging
from typing import TYPE_CHECKING

from mekhane.periskope.models import SearchResult, SearchSource

if TYPE_CHECKING:
    from mekhane.symploke.indices.base import IndexedResult

logger = logging.getLogger(__name__)


# ── Shared conversion ──

# SourceType.value → SearchSource mapping
_SOURCE_MAP = {
    "gnosis": SearchSource.GNOSIS,
    "sophia": SearchSource.SOPHIA,
    "kairos": SearchSource.KAIROS,
    "chronos": SearchSource.KAIROS,   # Chronos maps to Kairos in Periskopē
    "handoff": SearchSource.KAIROS,   # Handoff maps to Kairos in Periskopē
}


def _to_search_result(r: IndexedResult, fallback_source: SearchSource) -> SearchResult:
    """Convert Symplokē IndexedResult to Periskopē SearchResult."""
    source = _SOURCE_MAP.get(r.source.value, fallback_source)
    meta = r.metadata or {}

    return SearchResult(
        source=source,
        title=meta.get("title", r.doc_id),
        url=meta.get("url") or meta.get("file_path"),
        content=r.content[:1000] if r.content else "",
        snippet=_truncate(r.content, 200) if r.content else "",
        relevance=r.score,
        timestamp=meta.get("published_date") or meta.get("timestamp"),
        metadata=meta,
    )


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


# ── Symplokē engine singleton ──

_symploke_engines: dict[frozenset, object] = {}


def _get_symploke_engine(sources: list[str]):
    """Get or create a Symplokē SearchEngine for the given sources."""
    key = frozenset(sources)
    if key not in _symploke_engines:
        from mekhane.symploke.search.search_factory import get_search_engine
        engine, errors = get_search_engine(sources)
        if errors:
            logger.warning("Symplokē init errors for %s: %s", sources, errors)
        _symploke_engines[key] = engine
    return _symploke_engines[key]


# ── Async searchers (thin adapters) ──

class GnosisSearcher:
    """Search Gnōsis academic paper index via Symplokē DomainIndex.

    Delegates to Symplokē's GnosisIndex (Vertex/BGE-M3 embeddings).
    Runs in a thread pool for async compatibility.
    """

    async def search(
        self,
        query: str,
        max_results: int = 10,
        source_filter: str | None = None,
    ) -> list[SearchResult]:
        try:
            engine = _get_symploke_engine(["gnosis"])
            results = await asyncio.to_thread(
                engine.search, query, ["gnosis"], max_results,
            )
            out = [_to_search_result(r, SearchSource.GNOSIS) for r in results]
            logger.info("Gnōsis (symplokē): %d results for %r", len(out), query)
            return out
        except (Exception, asyncio.CancelledError) as e:  # noqa: BLE001
            logger.error("Gnōsis search failed: %s", e)
            return []


class SophiaSearcher:
    """Search Sophia Knowledge Items via Symplokē DomainIndex."""

    async def search(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[SearchResult]:
        try:
            engine = _get_symploke_engine(["sophia"])
            results = await asyncio.to_thread(
                engine.search, query, ["sophia"], max_results,
            )
            out = [_to_search_result(r, SearchSource.SOPHIA) for r in results]
            logger.info("Sophia (symplokē): %d results for %r", len(out), query)
            return out
        except (Exception, asyncio.CancelledError) as e:  # noqa: BLE001
            logger.error("Sophia search failed: %s", e)
            return []


class KairosSearcher:
    """Search Kairos session handoffs and ROM via Symplokē DomainIndex."""

    async def search(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[SearchResult]:
        try:
            engine = _get_symploke_engine(["kairos", "handoff"])
            results = await asyncio.to_thread(
                engine.search, query, ["kairos", "handoff"], max_results,
            )
            out = [_to_search_result(r, SearchSource.KAIROS) for r in results]
            logger.info("Kairos (symplokē): %d results for %r", len(out), query)
            return out
        except (Exception, asyncio.CancelledError) as e:  # noqa: BLE001
            logger.error("Kairos search failed: %s", e)
            return []
