from __future__ import annotations
# PROOF: mekhane/periskope/phases/filter.py
# PURPOSE: Phase 1.5-1.75 — 重複除去、リランク、品質フィルタ
"""
Phase 1.5-1.75: Dedup → Rerank → Quality Filter.

Extracted from engine.py:
  - _phase_filter (L1392-1442)
  - _deduplicate_results (L2741-2754)
  - _normalize_url (L2729-2738)
  - _rerank_results (L2784-2882)
  - _llm_rerank_results (L2757-2781)
"""

import logging
import re as _re
from typing import TYPE_CHECKING

from mekhane.periskope.models import SearchResult

if TYPE_CHECKING:
    from mekhane.periskope.searchers.llm_reranker import LLMReranker

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """Normalize URL for deduplication."""
    url = url.lower().strip().rstrip("/")
    if "?" in url:
        base, _ = url.split("?", 1)
        return base
    return url


def deduplicate_results(results: list[SearchResult]) -> list[SearchResult]:
    """F11: Cross-source deduplication by URL normalization."""
    seen: set[str] = set()
    deduped: list[SearchResult] = []
    for r in results:
        key = normalize_url(r.url) if r.url else f"title:{r.title}"
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return deduped


async def rerank_results_embedding(
    query: str,
    results: list[SearchResult],
    *,
    embedder: object | None = None,
    init_embedder: 'callable | None' = None,
    nl_client: object | None = None,
    nl_entity_cache: dict | None = None,
    cloud_nl_cfg: dict | None = None,
    config: dict | None = None,
    max_rerank: int | None = None,
) -> list[SearchResult]:
    """W4: Rerank results using embedding semantic similarity.

    Delegates similarity computation to Embedder.similarity_batch().
    Config: config.yaml → rerank.max_results, rerank.enabled
    """
    if not results:
        return results
    if config is None:
        config = {}
    if cloud_nl_cfg is None:
        cloud_nl_cfg = {}
    if nl_entity_cache is None:
        nl_entity_cache = {}

    rerank_config = config.get("rerank", {})
    if not rerank_config.get("enabled", True):
        return results
    if max_rerank is None:
        max_rerank = rerank_config.get("max_results", 30)

    try:
        if embedder is None and init_embedder:
            init_embedder()
            # Caller must re-pass embedder after init; this is a signal
            logger.warning("W4: Embedder was None, init requested")
            return results

        to_rerank = results[:max_rerank]
        remainder = results[max_rerank:]

        texts = [
            f"{r.title} {r.snippet or r.content[:500] if r.content else ''}"
            for r in to_rerank
        ]
        scores = embedder.similarity_batch(query, texts)

        for r, score in zip(to_rerank, scores):
            r.relevance = score

        # F4: NL API Type-Aware Rerank Boost
        if nl_client and cloud_nl_cfg.get("enabled", False):
            try:
                boost_weight = cloud_nl_cfg.get("rerank_boost", 0.1)
                salience_threshold = cloud_nl_cfg.get("salience_threshold", 0.3)

                query_entities = nl_entity_cache.get(query)
                if query_entities is None:
                    max_entities = cloud_nl_cfg.get("max_entities", 10)
                    query_entities = nl_client.analyze_entities(
                        query, max_entities=max_entities,
                    )
                    nl_entity_cache[query] = query_entities

                salient = [e for e in query_entities if e.salience >= salience_threshold]

                if salient:
                    patterns = []
                    for e in salient:
                        try:
                            pat = _re.compile(
                                r'\b' + _re.escape(e.name) + r'\b', _re.IGNORECASE,
                            )
                            patterns.append((e, pat))
                        except _re.error:
                            pass

                    boosted = 0
                    for r in to_rerank:
                        text_body = ((r.snippet or "") + " " + (r.content or "")).lower()
                        score_delta = 0.0
                        for e, pat in patterns:
                            if (
                                e.type == "PERSON"
                                and getattr(r, 'source', '') == 'semantic_scholar'
                            ):
                                if pat.search(r.title or ""):
                                    score_delta += e.salience * boost_weight * 2.0
                                    continue
                            if pat.search(text_body):
                                score_delta += e.salience * boost_weight

                        if score_delta > 0:
                            r.relevance = min(1.0, r.relevance + score_delta)
                            boosted += 1

                    if boosted:
                        logger.info(
                            "F4: Boosted %d/%d results via NL entities",
                            boosted, len(to_rerank),
                        )
            except Exception as e:  # noqa: BLE001
                logger.warning("NL API rerank boost failed: %s", e)

        to_rerank.sort(key=lambda r: r.relevance, reverse=True)
        merged = to_rerank + remainder
        logger.info(
            "W4: Reranked %d/%d results via Embeddings (batch)",
            len(to_rerank), len(results),
        )

    except Exception as e:  # noqa: BLE001
        logger.warning("W4: Reranking unavailable, keeping original order: %s", e)
        merged = results

    return merged


async def llm_rerank_results(
    query: str,
    results: list[SearchResult],
    depth: int = 2,
    *,
    override_enabled: bool | None = None,
    llm_reranker: 'LLMReranker | None' = None,
) -> list[SearchResult]:
    """W8: Apply LLM cascade reranking.

    Depth-based policy:
      - Depth 1 (Quick): OFF
      - Depth 2+ (Standard/Deep): ON
    """
    if llm_reranker is None:
        return results

    if override_enabled is not None:
        is_enabled = override_enabled
    elif depth >= 2:
        is_enabled = llm_reranker.enabled
    else:
        is_enabled = False
        logger.debug("W8: LLM reranking skipped (Depth %d < 2)", depth)

    if not is_enabled:
        return results

    logger.info(
        "W8: Starting LLM cascade reranking for %d results (depth=%d)",
        len(results), depth,
    )
    return await llm_reranker.rerank(query, results, depth)


async def phase_filter(
    query: str,
    search_results: list[SearchResult],
    depth: int,
    *,
    llm_rerank: bool | None = None,
    embedder: object | None = None,
    init_embedder: 'callable | None' = None,
    llm_reranker: 'LLMReranker | None' = None,
    nl_client: object | None = None,
    nl_entity_cache: dict | None = None,
    cloud_nl_cfg: dict | None = None,
    config: dict | None = None,
) -> tuple[list[SearchResult], list[SearchResult]]:
    """Phase 1.5-1.75: Dedup → Rerank → Quality filter.

    Returns:
        (filtered_results, pre_rerank_results)
    """
    if config is None:
        config = {}

    # Phase 1.5: Dedup
    if search_results:
        before = len(search_results)
        search_results = deduplicate_results(search_results)
        if len(search_results) < before:
            logger.info("  Dedup: %d → %d results", before, len(search_results))

    # Phase 1.7: Semantic reranking (W4) + LLM Cascade
    pre_rerank_results = list(search_results) if search_results else []
    if search_results:
        search_results = await rerank_results_embedding(
            query, search_results,
            embedder=embedder,
            init_embedder=init_embedder,
            nl_client=nl_client,
            nl_entity_cache=nl_entity_cache,
            cloud_nl_cfg=cloud_nl_cfg,
            config=config,
        )
        search_results = await llm_rerank_results(
            query, search_results, depth=depth,
            override_enabled=llm_rerank,
            llm_reranker=llm_reranker,
        )

    # Phase 1.75: Quality filter
    if search_results:
        blocklist = set(config.get("domain_blocklist", []))
        if blocklist:
            before = len(search_results)
            search_results = [
                r for r in search_results
                if not r.url or not any(
                    domain in (r.url or "").lower()
                    for domain in blocklist
                )
            ]
            blocked = before - len(search_results)
            if blocked:
                logger.info("Phase 1.75a: Blocked %d blocklisted", blocked)

        min_relevance = config.get("relevance_threshold", 0.25)
        before = len(search_results)
        search_results = [r for r in search_results if r.relevance >= min_relevance]
        filtered = before - len(search_results)
        if filtered:
            logger.info(
                "Phase 1.75b: Filtered %d low-relevance (threshold=%.2f)",
                filtered, min_relevance,
            )

    return search_results, pre_rerank_results
