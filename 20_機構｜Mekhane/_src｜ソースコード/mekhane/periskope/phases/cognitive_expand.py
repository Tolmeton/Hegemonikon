from __future__ import annotations
# PROOF: mekhane/periskope/phases/cognitive_expand.py
# PURPOSE: Phase 0 — 認知拡張 (Φ0-Φ4 pre-search cognitive expansion)
"""
Phase 0: Cognitive Query Expansion.

Implements the pre-search cognitive expansion pipeline:
  Φ0:   Intent Decomposition (V1 base arrow)
  Φ0:   Query Plan (V2 lookahead chain)
  Φ0:   Source Adaptation (V3 source-specific transforms)
  Φ0:   Query Fortification (pre-gate structuring)
  Φ0.5: NL API Entity Extraction (KG disambiguation)
  Φ1:   Blind Spot Analysis + Counterfactual Queries
  Φ2:   Divergent Thinking
  Φ3:   Context Setting
  Φ4:   Pre-search Convergent Ranking

Extracted from engine.py L1110-1354 (_phase_cognitive_expand).
"""

import asyncio
import logging
from typing import TYPE_CHECKING

from mekhane.periskope.cognition import (
    IntentDecomposition,
    QueryPlan,
    SourceAdaptedQueries,
    phi0_intent_decompose,
    phi0_query_plan,
    phi0_source_adapt,
    phi1_blind_spot_analysis,
    phi1_counterfactual_queries,
    phi2_divergent_thinking,
    phi3_context_setting,
    phi4_pre_search_ranking,
)

if TYPE_CHECKING:
    from mekhane.periskope.query_expander import QueryExpander

logger = logging.getLogger(__name__)


async def phase_cognitive_expand(
    query: str,
    depth: int,
    expand_query: bool,
    enabled: set[str],
    known_context: str = "",
    *,
    # Injected dependencies (from PeriskopeEngine)
    nl_client: object | None = None,
    nl_call_count: int = 0,
    nl_max_calls: int = 10,
    nl_entity_cache: dict | None = None,
    cloud_nl_cfg: dict | None = None,
    query_expander: 'QueryExpander | None' = None,
    config: dict | None = None,
) -> tuple[
    list[str],
    object | None,
    object | None,
    IntentDecomposition | None,
    QueryPlan | None,
    int,  # updated nl_call_count
]:
    """Phase 0: Cognitive query expansion (Φ0-Φ4 pre-search).

    Returns:
        (expanded_queries, context_plan, source_adapted_queries,
         intent, query_plan, updated_nl_call_count)
    """
    if nl_entity_cache is None:
        nl_entity_cache = {}
    if cloud_nl_cfg is None:
        cloud_nl_cfg = {}
    if config is None:
        config = {}

    blind_spot_queries: list[str] = []
    counterfactual_queries: list[str] = []

    # D1: Φ1 blind-spot is always-on (VISION §2.1)
    # D2: Include past search history for differential blind-spot detection
    past_context = known_context or ""
    try:
        from mekhane.periskope.research_tracker import list_tracks
        tracks = list_tracks()
        past_queries: list[str] = []
        for t in tracks:
            past_queries.extend(h.get("query", "") for h in t.depth_history[-5:])
        if past_queries:
            past_context += "\nPrevious searches: " + "; ".join(past_queries[-10:])
    except Exception as e:  # noqa: BLE001
        logger.debug("Could not load research_tracker context for Φ1: %s", e)

    # NL API Entity Extraction (Φ0.5) — moved BEFORE Φ1 for KG disambiguation (F3)
    entity_queries: list[str] = []
    entities: list = []
    if nl_client and nl_call_count < nl_max_calls:
        try:
            max_entities = cloud_nl_cfg.get("max_entities", 10)
            salience_threshold = cloud_nl_cfg.get("salience_threshold", 0.3)
            high_salience_threshold = cloud_nl_cfg.get("high_salience_threshold", 0.5)
            entities = await asyncio.to_thread(
                nl_client.analyze_entities, query, "", max_entities
            )
            nl_call_count += 1
            nl_entity_cache[query] = entities

            for e in entities:
                if e.salience >= high_salience_threshold:
                    entity_queries.append(e.name)
                elif e.salience >= salience_threshold:
                    entity_queries.append(f"{query} {e.name}")

            if entity_queries:
                logger.info(
                    "Φ0.5 [NL API]: %d entity queries (high: %d, ctx: %d) from %d entities",
                    len(entity_queries),
                    sum(1 for e in entities if e.salience >= high_salience_threshold),
                    sum(1 for e in entities if salience_threshold <= e.salience < high_salience_threshold),
                    len(entities),
                )

            # F3: Inject KG metadata into blind-spot context for disambiguation
            kg_parts: list[str] = []
            for e in entities:
                if e.metadata:
                    wiki = e.metadata.get("wikipedia_url", "")
                    mid = e.metadata.get("mid", "")
                    kg_parts.append(f"{e.name} ({e.type}, wiki={wiki}, mid={mid})")
                elif e.salience >= salience_threshold:
                    kg_parts.append(f"{e.name} ({e.type}, salience={e.salience:.2f})")
            if kg_parts:
                past_context += "\nKG Entities: " + "; ".join(kg_parts)
                logger.info("F3: %d KG entities injected into Φ1 context", len(kg_parts))
        except Exception as e:  # noqa: BLE001
            logger.warning("NL API extraction failed: %s", e)

    # Φ0 Pre-gate: Query Structuring — depth >= 2 only
    if depth >= 2:
        try:
            from mekhane.periskope.cognition.phi0_query_fortifier import (
                fortify_query,
            )
            logger.info("Φ0 Pre-gate: Structuring query: %r", query[:80])
            fortified = await fortify_query(query, known_context or "")
            if fortified != query:
                logger.info("Φ0 Pre-gate: Query structured → %r", fortified[:120])
                query = fortified
        except Exception as e:  # noqa: BLE001
            logger.warning("Φ0 Pre-gate structuring skipped: %s", e)

    # Φ0: Intent Decomposition — V1 base arrow
    intent: IntentDecomposition | None = None
    if depth >= 2:
        try:
            intent = await phi0_intent_decompose(query, context=past_context)
            if intent and intent.core_concepts:
                past_context += "\n" + intent.to_context_string()
                logger.info(
                    "Φ0: Intent decomposed — %d concepts, evidence=%r",
                    len(intent.core_concepts),
                    intent.evidence_type[:50] if intent.evidence_type else "(none)",
                )
        except Exception as e:  # noqa: BLE001
            logger.warning("Φ0 intent decomposition failed: %s", e)

    # Φ0: Query Plan — V2 lookahead chain
    query_plan: QueryPlan | None = None
    if depth >= 2:
        try:
            intent_ctx = intent.to_context_string() if intent and intent.core_concepts else ""
            query_plan = await phi0_query_plan(
                query, context=past_context, intent_context=intent_ctx,
            )
            if query_plan and query_plan.step1_survey:
                logger.info(
                    "Φ0 QueryPlan: %d step1 + %d step2 + %d step3 queries",
                    len(query_plan.step1_survey),
                    len(query_plan.step2_analysis),
                    len(query_plan.step3_verification),
                )
        except Exception as e:  # noqa: BLE001
            logger.warning("Φ0 query planning failed: %s", e)

    # Φ1: Blind Spot Analysis
    try:
        blind_spot_queries = await phi1_blind_spot_analysis(query, context=past_context)
        if blind_spot_queries:
            logger.info("Φ1: %d blind-spot queries", len(blind_spot_queries))
    except Exception as e:  # noqa: BLE001
        logger.warning("Φ1 blind-spot failed: %s", e)

    # Φ1: Counterfactual Queries (depth >= 2)
    if depth >= 2:
        try:
            counterfactual_queries = await phi1_counterfactual_queries(query)
            if counterfactual_queries:
                logger.info("Φ1: %d counterfactual queries", len(counterfactual_queries))
        except Exception as e:  # noqa: BLE001
            logger.warning("Φ1 counterfactual failed: %s", e)

    # W3: Bilingual query expansion
    queries = [query]
    if expand_query and query_expander:
        try:
            queries = await query_expander.expand(query)
            if len(queries) > 1:
                logger.info("W3: Query expanded to %d variants", len(queries))
        except Exception as e:  # noqa: BLE001
            logger.warning("W3 expansion failed, using original: %s", e)

    # Merge Φ0 negation + Φ0 plan step1 + Φ1 queries
    negation_queries = []
    if intent and intent.negation_queries:
        negation_queries = intent.negation_queries
    plan_step1 = query_plan.step1_as_candidates() if query_plan else []
    all_phi01 = blind_spot_queries + counterfactual_queries + entity_queries + negation_queries + plan_step1
    if all_phi01:
        existing = {q.lower() for q in queries}
        for bq in all_phi01:
            if bq.lower() not in existing:
                queries.append(bq)
                existing.add(bq.lower())

    # Φ2: Divergent thinking
    if depth >= 2:
        try:
            divergent_candidates = await phi2_divergent_thinking(
                query,
                expanded_queries=queries[1:],
                max_candidates=8 if depth >= 3 else 5,
                depth=depth,
            )
            existing = {q.lower() for q in queries}
            for dc in divergent_candidates:
                if dc.lower() not in existing:
                    queries.append(dc)
                    existing.add(dc.lower())
            logger.info("Φ2: %d total candidates after divergent thinking", len(queries))
        except Exception as e:  # noqa: BLE001
            logger.warning("Φ2 divergent thinking failed: %s", e)

    # Φ3: Context setting
    context_plan = None
    if depth >= 2:
        try:
            context_plan = await phi3_context_setting(
                query,
                candidates=queries,
                available_sources=list(enabled),
                site_scoped_domains=config.get("site_scoped_domains", []),
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("Φ3 context setting failed: %s", e)

    # Φ4: Pre-search convergent ranking
    if depth >= 2 and len(queries) > 1:
        try:
            ranked_queries = await phi4_pre_search_ranking(
                query, queries, max_queries=5, known_context=known_context,
            )
            if ranked_queries:
                queries = [rq.query for rq in ranked_queries]
                logger.info(
                    "Φ4: Ranked %d candidates, top score=%.2f",
                    len(ranked_queries),
                    ranked_queries[0].score if ranked_queries else 0,
                )
        except Exception as e:  # noqa: BLE001
            logger.warning("Φ4 pre-search ranking failed: %s", e)

    # Φ0: Source Adaptation — V3 rule-based
    source_adapted: SourceAdaptedQueries | None = None
    if context_plan and depth >= 2:
        try:
            core_concepts = intent.core_concepts if intent else None
            source_adapted = phi0_source_adapt(
                query,
                query_type=context_plan.query_type,
                core_concepts=core_concepts,
                enabled_sources=enabled,
            )
            if source_adapted and source_adapted.has_adaptations():
                logger.info(
                    "Φ0 SourceAdapt: %d source-specific variants",
                    len(source_adapted.adapted),
                )
        except Exception as e:  # noqa: BLE001
            logger.warning("Φ0 source adaptation failed: %s", e)

    return queries, context_plan, source_adapted, intent, query_plan, nl_call_count


def build_site_scoped_queries(
    query: str,
    extra_queries: list[str],
    context_plan: object | None,
    enabled: set[str],
    config: dict | None = None,
) -> list[str]:
    """G4: Build site-scoped queries from Φ3 plan or config."""
    if config is None:
        config = {}
    if context_plan and hasattr(context_plan, 'site_scoped_queries') and context_plan.site_scoped_queries:
        for sq in context_plan.site_scoped_queries:
            if sq not in extra_queries:
                extra_queries.append(sq)
        logger.info("G4 (Φ3): %d site-scoped queries", len(context_plan.site_scoped_queries))
    else:
        site_scoped_domains = config.get("site_scoped_domains", [
            "qiita.com", "zenn.dev", "b.hatena.ne.jp",
        ])
        if site_scoped_domains and "searxng" in enabled:
            for domain in site_scoped_domains:
                site_query = f"{query} site:{domain}"
                if site_query not in extra_queries:
                    extra_queries.append(site_query)
            logger.info("G4: Added %d site-scoped queries", len(site_scoped_domains))
    return extra_queries


def min_results_threshold(depth: int, config: dict | None = None) -> int:
    """Depth-based minimum results threshold for fallback decisions."""
    if config is None:
        config = {}
    fallback_cfg = config.get("fallback", {})
    thresholds = fallback_cfg.get(
        "min_results_by_depth", {1: 1, 2: 3, 3: 5},
    )
    return thresholds.get(depth, thresholds.get(2, 3))
