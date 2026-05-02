from __future__ import annotations
# PROOF: mekhane/periskope/cognition/phi0_source_adapter.py
# PURPOSE: periskope モジュールの phi0_source_adapter
"""
Φ0 Source Adapter — V3 ソース適応 (Source-Adaptive Query Transformation).

Design: /noe+ Periskopē クエリ形成分析 (2026-02-28)
  V3: 「各検索ソースには得意分野がある。クエリをソースの特性に合わせて変形すべき」

PURPOSE: 同一の意図を持つクエリを、各検索ソースの特性に最適化された
形式に変形する。現行は全ソースに同一クエリを投げているが、
ソースごとにクエリの言い回しや構造を調整する。

Principle III (Spectrum): 変形は軽微な調整 (nudge)。
ソースの特性を活用するだけであり、意味を変えない。

Φ3 (phi3_context.py) の _SOURCE_MAP / query_type を活用して
ソース別の最適クエリを生成する。
"""


import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# Source-specific query transformation rules
# Each rule describes how to adapt a query for a specific source type.
_SOURCE_ADAPTATIONS: dict[str, dict] = {
    "semantic_scholar": {
        "style": "academic",
        "transforms": [
            "Use precise academic terminology",
            "Remove colloquial phrasing",
        ],
        "prefix": "",
        "suffix": "",
        "max_words": 12,
    },
    "gnosis": {
        "style": "academic",
        "transforms": ["Use key concepts and authors"],
        "prefix": "",
        "suffix": "",
        "max_words": 10,
    },
    "stackoverflow": {
        "style": "technical",
        "transforms": [
            "Frame as a specific technical problem",
            "Include error messages or technology names",
        ],
        "prefix": "",
        "suffix": "",
        "max_words": 15,
    },
    "github": {
        "style": "implementation",
        "transforms": [
            "Focus on library/tool names",
            "Use programming language names",
        ],
        "prefix": "",
        "suffix": "",
        "max_words": 10,
    },
    "reddit": {
        "style": "conversational",
        "transforms": [
            "Use colloquial phrasing",
            "Frame as a question or discussion",
        ],
        "prefix": "",
        "suffix": "",
        "max_words": 15,
    },
    "hackernews": {
        "style": "tech_news",
        "transforms": ["Focus on trends, launches, opinions"],
        "prefix": "",
        "suffix": "",
        "max_words": 12,
    },
}

# Query type → source adaptation style mapping
_QUERY_TYPE_ADAPTATIONS: dict[str, dict[str, str]] = {
    "academic": {
        "semantic_scholar": "{query}",  # Already academic
        "reddit": "ELI5 {query}",
        "github": "{core_concept} implementation",
        "stackoverflow": "{core_concept} algorithm",
    },
    "implementation": {
        "semantic_scholar": "{core_concept} algorithm method",
        "reddit": "best library for {query}",
        "github": "{core_concept} example code",
        "stackoverflow": "{query}",  # Already technical
    },
    "troubleshoot": {
        "semantic_scholar": "{core_concept} root cause analysis",
        "reddit": "anyone else having {query}",
        "github": "{query} issue",
        "stackoverflow": "{query}",  # Already problem-oriented
    },
    "news": {
        "semantic_scholar": "{core_concept} survey 2024 2025",
        "reddit": "{query} announcement",
        "hackernews": "{query}",  # Already news-oriented
    },
    "concept": {
        "semantic_scholar": "{core_concept} overview framework",
        "reddit": "what is {query} explained",
        "stackoverflow": "how does {query} work",
        "github": "{core_concept}",
    },
}


@dataclass
class SourceAdaptedQueries:
    """Φ0 output: Source-specific query variants.

    Maps source names to their adapted query strings.
    Only sources that benefit from adaptation are included;
    sources not listed should use the original query.
    """

    # source_name → adapted query
    adapted: dict[str, str] = field(default_factory=dict)

    # Original query (fallback)
    original: str = ""

    # Query type used for adaptation
    query_type: str = ""

    def get_query_for_source(self, source: str) -> str:
        """Get the best query for a specific source.

        Returns adapted query if available, original otherwise.
        """
        return self.adapted.get(source, self.original)

    def has_adaptations(self) -> bool:
        """Whether any source-specific adaptations were generated."""
        return len(self.adapted) > 0


def phi0_source_adapt(
    query: str,
    query_type: str = "concept",
    core_concepts: list[str] | None = None,
    enabled_sources: set[str] | None = None,
) -> SourceAdaptedQueries:
    """Φ0: Generate source-adapted query variants.

    Synchronous — no LLM call needed. Uses rule-based transformation
    from query_type + source characteristics.

    Args:
        query: Original research query.
        query_type: From Φ3 classification (academic/implementation/news/troubleshoot/concept).
        core_concepts: From V1 intent decomposition (used as {core_concept} in templates).
        enabled_sources: Limit adaptations to these sources.

    Returns:
        SourceAdaptedQueries with source-specific variants.
    """
    core_concept = core_concepts[0] if core_concepts else query.split()[0] if query else ""

    adaptations = _QUERY_TYPE_ADAPTATIONS.get(query_type, {})
    result = SourceAdaptedQueries(original=query, query_type=query_type)

    for source, template in adaptations.items():
        # Skip if source not enabled
        if enabled_sources and source not in enabled_sources:
            continue

        adapted = template.format(
            query=query,
            core_concept=core_concept,
        )

        # Only include if meaningfully different from original
        if adapted.lower().strip() != query.lower().strip():
            # Enforce max word limit from source config
            source_config = _SOURCE_ADAPTATIONS.get(source, {})
            max_words = source_config.get("max_words", 15)
            words = adapted.split()
            if len(words) > max_words:
                adapted = " ".join(words[:max_words])

            result.adapted[source] = adapted

    if result.adapted:
        logger.info(
            "Φ0 SourceAdapt: %d adaptations for query_type=%r — %s",
            len(result.adapted),
            query_type,
            ", ".join(f"{s}={q[:30]!r}" for s, q in result.adapted.items()),
        )

    return result
