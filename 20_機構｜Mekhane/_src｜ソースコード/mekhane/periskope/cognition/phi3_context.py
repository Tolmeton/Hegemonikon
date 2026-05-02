from __future__ import annotations
# PROOF: mekhane/periskope/cognition/phi3_context.py
# PURPOSE: periskope モジュールの phi3_context
"""
Φ3: 文脈配置 (P1 Khōra) — Context setting.

Design: Search Cognition Theory §2.2 (kernel/search_cognition.md)

Decides WHERE to search — the "場" (Khōra) for each query candidate.
Uses LLM-based semantic classification (with keyword fallback) to map
query types to optimal source combinations.

v2: LLM-based classification replaces pure keyword matching (D3 gap fix).
"""


import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_VALID_TYPES = {"academic", "implementation", "news", "concept", "troubleshoot"}


# PURPOSE: [L2-auto] _llm_ask の共通モジュール参照
from mekhane.periskope.cognition._llm import llm_ask as _llm_ask


# PURPOSE: [L2-auto] ContextPlan のクラス定義
@dataclass
class ContextPlan:
    """Plan for where to search — source recommendations per query."""

    queries_with_sources: list[tuple[str, list[str]]] = field(default_factory=list)
    """Each entry: (query, recommended_sources)."""

    site_scoped_queries: list[str] = field(default_factory=list)
    """Additional site-scoped queries (e.g., 'site:qiita.com ...')."""

    query_type: str = "concept"
    """Classified query type: academic, implementation, news, troubleshoot, concept."""

    reasoning: str = ""
    """Why these sources were selected."""


# PURPOSE: [L2-auto] _classify_query_keyword の関数定義
def _classify_query_keyword(query: str) -> str:
    """F12 fallback: Classify query type via keyword matching.

    Returns:
        "academic", "implementation", "news", or "concept".
    """
    q = query.lower()
    academic_kw = ["paper", "arxiv", "研究", "論文", "experiment", "study", "journal"]
    impl_kw = ["実装", "code", "how to", "作り方", "tutorial", "library", "方法"]
    news_kw = ["latest", "最新", "news", "ニュース", "announce", "release", "update"]
    trouble_kw = ["bug", "error", "fix", "debug", "traceback", "エラー", "バグ",
                  "crash", "exception", "failed", "broken", "issue", "問題"]

    if any(kw in q for kw in trouble_kw):
        return "troubleshoot"
    if any(kw in q for kw in news_kw):
        return "news"
    if any(kw in q for kw in academic_kw):
        return "academic"
    if any(kw in q for kw in impl_kw):
        return "implementation"
    return "concept"


# PURPOSE: Týpos プロンプトローダー (共通モジュール)
from mekhane.periskope.prompts import load_prompt


# PURPOSE: [L2-auto] _classify_query_llm の非同期処理定義
async def _classify_query_llm(query: str) -> str | None:
    """F12 primary: Classify query type via LLM semantic understanding.

    Returns:
        "academic", "implementation", "news", "concept", or None on failure.
    """
    template = load_prompt("phi3_classify_query.typos")
    if template:
        prompt = template.format(query=query)
    else:
        # Fallback
        prompt = (
            "Classify this search query into exactly ONE category.\n\n"
            f"Query: {query}\n\n"
            "Categories:\n"
            "- academic: research papers, scientific studies, theoretical work\n"
            "- implementation: code, tutorials, how-to guides, libraries\n"
            "- news: recent events, announcements, releases, updates\n"
            "- troubleshoot: bugs, errors, debugging, fixes, crashes\n"
            "- concept: general concepts, explanations, overviews\n\n"
            "Reply with ONLY the category name (one word). Nothing else."
        )
    text = await _llm_ask(prompt)
    if not text:
        return None
    result = text.strip().lower().split()[0] if text.strip() else None
    if result in _VALID_TYPES:
        return result
    logger.warning("Φ3 LLM returned invalid type %r, falling back to keyword", result)
    return None


# Source recommendations per query type
_SOURCE_MAP: dict[str, list[str]] = {
    "academic": ["gnosis", "semantic_scholar", "arxiv", "openalex", "searxng", "brave", "vertex_search", "gemini_search"],
    "implementation": ["searxng", "brave", "sophia", "github", "vertex_search", "gemini_search", "stackoverflow", "reddit", "hackernews"],
    "news": ["searxng", "brave", "tavily", "vertex_search", "gemini_search", "reddit", "hackernews"],
    "troubleshoot": ["stackoverflow", "github", "searxng", "reddit", "vertex_search", "gemini_search", "brave"],
    "concept": ["searxng", "brave", "tavily", "semantic_scholar", "arxiv", "openalex", "gnosis", "sophia", "kairos", "github", "vertex_search", "gemini_search", "stackoverflow"],
}

# Site-scoped domains for Japanese technical content (G4)
_SITE_SCOPED_DOMAINS: list[str] = [
    "qiita.com",
    "zenn.dev",
    "b.hatena.ne.jp",
]


# PURPOSE: [L2-auto] phi3_context_setting の非同期処理定義
async def phi3_context_setting(
    query: str,
    candidates: list[str],
    available_sources: list[str] | None = None,
    site_scoped_domains: list[str] | None = None,
) -> ContextPlan:
    """Φ3: Context setting — decide where to search.

    Uses LLM-based semantic classification with keyword fallback
    to map each query candidate to its optimal source set.
    Also generates site-scoped queries for niche platforms.

    Args:
        query: Original research query (for classification).
        candidates: Query candidates from Φ2 divergent thinking.
        available_sources: Limit to these sources (default: all).
        site_scoped_domains: Domains for site-scoped search (G4).

    Returns:
        ContextPlan with source recommendations per query.
    """
    # Primary: LLM classification. Fallback: keyword matching
    llm_type = await _classify_query_llm(query)
    if llm_type:
        query_type = llm_type
        classification_method = "llm"
    else:
        query_type = _classify_query_keyword(query)
        classification_method = "keyword"

    recommended = _SOURCE_MAP.get(query_type, _SOURCE_MAP["concept"])

    # Filter by available sources
    avail_set = set(available_sources) if available_sources else None
    if avail_set:
        recommended = [s for s in recommended if s in avail_set]

    # Map each candidate to sources (keyword fallback only — batch LLM is overkill)
    queries_with_sources: list[tuple[str, list[str]]] = []
    for candidate in candidates:
        cand_type = _classify_query_keyword(candidate)
        cand_sources = _SOURCE_MAP.get(cand_type, recommended)
        if avail_set:
            cand_sources = [s for s in cand_sources if s in avail_set]
        queries_with_sources.append((candidate, cand_sources or recommended))

    # Generate site-scoped queries (G4)
    domains = site_scoped_domains or _SITE_SCOPED_DOMAINS
    site_scoped: list[str] = []
    if query_type in ("implementation", "concept", "troubleshoot"):
        for domain in domains:
            # G4+: GitHub Issues/Discussions 狙い撃ち
            if domain == "github.com" and query_type == "implementation":
                site_scoped.append(f"site:github.com/issues {query}")
                site_scoped.append(f"site:github.com/discussions {query}")
            else:
                site_scoped.append(f"site:{domain} {query}")

    reasoning = (
        f"Query classified as '{query_type}' (via {classification_method}). "
        f"Primary sources: {', '.join(recommended)}. "
        f"{len(candidates)} candidates mapped. "
        f"{len(site_scoped)} site-scoped queries added."
    )

    plan = ContextPlan(
        queries_with_sources=queries_with_sources,
        site_scoped_queries=site_scoped,
        query_type=query_type,
        reasoning=reasoning,
    )

    logger.info("Φ3: %s", reasoning)
    return plan
