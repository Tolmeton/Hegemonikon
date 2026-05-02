from __future__ import annotations
# PROOF: mekhane/periskope/phases/verification.py
# PURPOSE: Phase 3-3.5 — Citation verification, Decision Frame, Quality metrics
"""
Phase 3-3.5: Verification and Quality Assessment.

  Phase 3: Citation verification (Layers B/C/D/E)
  Phase 3.5: Φ4 Convergent Framing + Quality Metrics

Extracted from engine.py:
  - _phase_cite (L2477-2516)
  - _phase_decision_frame (L2519-2533)
  - _compute_and_log_quality (L2536-2559)
"""

import logging
from typing import TYPE_CHECKING

from mekhane.periskope.models import SearchResult, TaintLevel
from mekhane.periskope.quality_metrics import compute_quality_metrics, log_metrics
from mekhane.periskope.cognition import phi4_post_search_framing

if TYPE_CHECKING:
    from mekhane.periskope.citation_agent import CitationAgent

logger = logging.getLogger(__name__)


async def phase_cite(
    synthesis: list,
    search_results: list[SearchResult],
    *,
    verify_citations: bool = True,
    citation_agent: 'CitationAgent | None' = None,
    url_auditor: object | None = None,
) -> tuple[list, object | None]:
    """Phase 3: Citation verification (Layers B/C/E + D).

    Returns:
        (citations, updated_url_auditor)
    """
    citations = []
    if not verify_citations or not synthesis or citation_agent is None:
        return citations, url_auditor

    logger.info("Phase 3: Citation verification")
    for synth_result in synthesis:
        extracted = citation_agent.extract_claims_from_synthesis(
            synth_result.content, search_results,
        )
        source_contents = {}
        for sr in search_results:
            if sr.url and sr.content:
                source_contents[sr.url] = sr.content
            for su in getattr(sr, 'source_urls', []) or []:
                if su and sr.content and su not in source_contents:
                    source_contents[su] = sr.content
        verified = await citation_agent.verify_citations(
            extracted, source_contents, verify_depth=2,
        )

        # Layer D: URL Auditor (Gemini 3 Flash)
        taint_count = sum(1 for c in verified if c.taint_level == TaintLevel.TAINT)
        if taint_count > 0:
            try:
                if url_auditor is None:
                    from mekhane.periskope.url_auditor import URLAuditor
                    url_auditor = URLAuditor()
                verified = await url_auditor.audit_citations(
                    verified, source_contents,
                )
            except Exception as e:  # noqa: BLE001
                logger.debug("Layer D URLAuditor failed: %s", e)

        citations.extend(verified)
    return citations, url_auditor


async def phase_decision_frame(
    query: str,
    synthesis: list,
    depth: int,
) -> object | None:
    """Phase 3.5: Φ4 convergent framing."""
    if depth < 2 or not synthesis:
        return None
    try:
        synth_texts = [s.content for s in synthesis]
        return await phi4_post_search_framing(query, synth_texts)
    except Exception as e:  # noqa: BLE001
        logger.warning("Φ4 post-search framing failed: %s", e)
        return None


def compute_and_log_quality(
    query: str,
    search_results: list[SearchResult],
    source_counts: dict[str, int],
    pre_rerank_results: list[SearchResult],
    elapsed: float,
    diversity_weight: float = 0.3,
) -> object | None:
    """Compute quality metrics and log to JSONL."""
    try:
        quality = compute_quality_metrics(
            query=query,
            results=search_results,
            source_counts=source_counts,
            pre_rerank_results=pre_rerank_results,
            diversity_weight=diversity_weight,
        )
        logger.info("Quality: %s", quality.summary())
        log_metrics(query, quality, source_counts, elapsed=elapsed)
        return quality
    except Exception as e:  # noqa: BLE001
        logger.warning("Quality metrics failed: %s", e)
        return None
