from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/prokataskeve/context_resolver.py
"""
ContextResolver — Reference resolution, context integration, past result recall.

Contains:
  - resolve_references (Hypomnēsis, I×Past) — L1
  - integrate_context (Synopsis, I×Ma) — L2
  - recall_past (Anatheōrēsis, A×Past) — L3
"""

import logging
import re
from typing import Any

from mekhane.mcp.prokataskeve.models import (
    ContextSummary,
    IntentClassification,
    PastResult,
)

logger = logging.getLogger(__name__)


# Reference words that need session-state resolution
_REFERENCE_PATTERNS = [
    (re.compile(r'さっきの|先ほどの|前の|上の'), "temporal_back"),
    (re.compile(r'これ|この|それ|その|あれ|あの'), "demonstrative"),
    (re.compile(r'同じ|同様の'), "identity"),
]


# =============================================================================
# L1: resolve_references (Hypomnēsis)
# =============================================================================


# PURPOSE: L1 参照解決 (Hypomnēsis, I×Past — 過去の信念状態にアクセスする)
def resolve_references(
    text: str,
    session_state: dict[str, Any] | None = None,
) -> dict[str, str]:
    """L1 Resolve anaphoric references in text.

    Maps references like "さっきの" to concrete IDs from session state.
    Returns a dict of {reference_text: resolved_id}.

    When session_state is None, only detects references without resolving.
    """
    resolved: dict[str, str] = {}

    for pattern, ref_type in _REFERENCE_PATTERNS:
        for m in pattern.finditer(text):
            ref_text = m.group()

            if session_state is None:
                resolved[ref_text] = f"[unresolved:{ref_type}]"
                continue

            if ref_type == "temporal_back":
                last_topic = session_state.get("last_topic", "")
                last_file = session_state.get("last_file", "")
                last_paper = session_state.get("last_paper", "")
                if last_paper:
                    resolved[ref_text] = last_paper
                elif last_file:
                    resolved[ref_text] = last_file
                elif last_topic:
                    resolved[ref_text] = last_topic
                else:
                    resolved[ref_text] = f"[unresolved:{ref_type}]"
            else:
                resolved[ref_text] = f"[unresolved:{ref_type}]"

    return resolved


# =============================================================================
# L2: integrate_context (Synopsis)
# =============================================================================


# PURPOSE: L2 文脈統合 (Synopsis, I×Ma — 巨視的に世界像を認識する)
async def integrate_context(
    text: str,
    session_state: dict[str, Any] | None = None,
    resolved_refs: dict[str, str] | None = None,
) -> ContextSummary:
    """L2 Integrate session context, resolved references, and memory state.

    Queries Mneme for related KIs and combines with session state
    to provide a holistic context picture for downstream processing.
    """
    summary = ContextSummary()

    if session_state:
        summary.session_topic = session_state.get("topic", "")
        summary.active_files = session_state.get("active_files", [])
        summary.recent_decisions = session_state.get("decisions", [])

    # Try Mneme search for related KIs
    try:
        from mekhane.mneme.search import search_all
        results = await search_all(query=text[:200], k=3, sources=["sophia"])
        summary.related_kis = [
            r.get("title", r.get("id", "unknown"))
            for r in (results if isinstance(results, list) else [])
        ]
    except Exception as e:  # noqa: BLE001
        logger.debug("Mneme search for context integration failed: %s", e)

    # Build summary text
    parts = []
    if summary.session_topic:
        parts.append(f"トピック: {summary.session_topic}")
    if summary.active_files:
        parts.append(f"作業中ファイル: {', '.join(summary.active_files[:3])}")
    if summary.related_kis:
        parts.append(f"関連KI: {', '.join(summary.related_kis[:3])}")
    if resolved_refs:
        resolved_items = [f"{k}→{v}" for k, v in resolved_refs.items()
                         if not v.startswith("[unresolved:")]
        if resolved_items:
            parts.append(f"解決済み参照: {', '.join(resolved_items)}")
    summary.summary_text = "; ".join(parts) if parts else ""

    return summary


# =============================================================================
# L3: recall_past (Anatheōrēsis)
# =============================================================================


# PURPOSE: L3 過去結果参照 (Anatheōrēsis, A×Past — 過去の行動結果を参照する)
async def recall_past(
    text: str,
    intent: IntentClassification,
) -> list[PastResult]:
    """L3 Search for past processing results for similar inputs.

    Queries Chronos (chat history) for similar past interactions
    and their outcomes.
    """
    try:
        from mekhane.mneme.search import search_all
        results = await search_all(query=text[:200], k=3, sources=["chronos"])
        past_results = []
        for r in (results if isinstance(results, list) else []):
            past_results.append(PastResult(
                query=r.get("query", ""),
                result_summary=r.get("content", r.get("summary", ""))[:200],
                source=f"chronos:{r.get('id', 'unknown')}",
                success=True,
                timestamp=r.get("timestamp", ""),
            ))
        return past_results
    except Exception as e:  # noqa: BLE001
        logger.debug("Past result recall failed: %s", e)
        return []
