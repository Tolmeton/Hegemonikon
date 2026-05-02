"""
Periskopē searchers — pluggable search source adapters.

Each searcher implements the same async interface:
    async def search(query: str, max_results: int) -> list[SearchResult]
"""

from .searxng import SearXNGSearcher
from .brave_searcher import BraveSearcher
from .tavily_searcher import TavilySearcher
from .semantic_scholar_searcher import SemanticScholarSearcher
from .gemini_searcher import GeminiSearcher
from .vertex_search_searcher import VertexSearchSearcher
from .internal_searcher import GnosisSearcher, SophiaSearcher, KairosSearcher
from .llm_reranker import LLMReranker

__all__ = [
    "SearXNGSearcher",
    "BraveSearcher",
    "TavilySearcher",
    "SemanticScholarSearcher",
    "GeminiSearcher",
    "VertexSearchSearcher",
    "GnosisSearcher",
    "SophiaSearcher",
    "KairosSearcher",
    "LLMReranker",
]
