# PROOF: mekhane/periskope/tests/test_llm_rerank_integration.py
# PURPOSE: periskope モジュールの llm_rerank_integration に対するテスト
import pytest
from unittest.mock import MagicMock, AsyncMock
from mekhane.periskope.models import SearchResult, SearchSource

@pytest.fixture
def mock_search_results():
    return [
        SearchResult(source=SearchSource.SEARXNG, url="url1", title="Title 1", snippet="Snippet 1", relevance=0.0),
        SearchResult(source=SearchSource.SEARXNG, url="url2", title="Title 2", snippet="Snippet 2", relevance=0.0),
    ]

class TestLLMRerankIntegration:
    """AP-4: PeriskopeEngine 経由の LLM Reranker 統合テスト"""
    
    def _make_engine_with_mock_reranker(self):
        from mekhane.periskope.engine import PeriskopeEngine
        # Bypass __init__ to avoid full initialization of other components
        engine = PeriskopeEngine.__new__(PeriskopeEngine)
        
        # Setup mock llm_reranker
        engine.llm_reranker = MagicMock()
        engine.llm_reranker.enabled = True
        engine.llm_reranker.rerank = AsyncMock()
        
        # Setup other minimally required properties
        engine._embedder = MagicMock()
        engine._search_cache = {}
        engine._config = {}
        engine.nl_client = None
        engine.cloud_nl_cfg = {}
        
        return engine
        
    @pytest.mark.asyncio
    async def test_llm_rerank_results_calls_reranker(self, mock_search_results):
        """override_enabled=True の場合、LLMReranker.rerank が呼ばれること (AP-4)"""
        engine = self._make_engine_with_mock_reranker()
        
        # mock rerank return
        expected_results = mock_search_results[::-1]  # reverse to show change
        engine.llm_reranker.rerank.return_value = expected_results
        
        res = await engine._llm_rerank_results("query", mock_search_results, depth=2, override_enabled=True)
        
        # Check that it called the mock
        engine.llm_reranker.rerank.assert_awaited_once_with("query", mock_search_results, 2)
        assert res == expected_results
        
    @pytest.mark.asyncio
    async def test_llm_rerank_results_skips_when_disabled(self, mock_search_results):
        """override_enabled=False の場合、LLMReranker はスキップされること (AP-4)"""
        engine = self._make_engine_with_mock_reranker()
        engine.llm_reranker.enabled = True  # Base config is true
        
        res = await engine._llm_rerank_results("query", mock_search_results, depth=2, override_enabled=False)
        
        # The mock should NOT have been called
        engine.llm_reranker.rerank.assert_not_called()
        # Original results should be returned
        assert res == mock_search_results

    @pytest.mark.asyncio
    async def test_llm_rerank_results_follows_base_config_when_none(self, mock_search_results):
        """override_enabled=None の場合、Base config の enabled に従うこと (AP-4)"""
        engine = self._make_engine_with_mock_reranker()
        
        # 1. Base config is False -> Should NOT call
        engine.llm_reranker.enabled = False
        res = await engine._llm_rerank_results("query", mock_search_results, depth=2, override_enabled=None)
        engine.llm_reranker.rerank.assert_not_called()
        assert res == mock_search_results
        
        # 2. Base config is True -> Should call
        engine.llm_reranker.enabled = True
        engine.llm_reranker.rerank.return_value = []
        res2 = await engine._llm_rerank_results("query", mock_search_results, depth=2, override_enabled=None)
        engine.llm_reranker.rerank.assert_awaited_once_with("query", mock_search_results, 2)
