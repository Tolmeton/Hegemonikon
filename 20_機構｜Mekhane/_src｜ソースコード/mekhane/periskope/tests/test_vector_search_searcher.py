# PROOF: mekhane/periskope/tests/test_vector_search_searcher.py
# PURPOSE: periskope モジュールの vector_search_searcher に対するテスト
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from mekhane.periskope.models import SearchResult, SearchSource
from mekhane.periskope.searchers.vector_search_searcher import VectorSearchSearcher

@pytest.fixture
def mock_embedder():
    embedder = MagicMock()
    # Mocking embed_query to return a dummy vector (3072 dims)
    embedder.embed_query = MagicMock(return_value=[0.1] * 3072)
    return embedder

@pytest.fixture
def default_config():
    return {
        "project": "test-project",
        "location": "us-central1",
        "index_endpoint_id": "test-endpoint",
        "deployed_index_id": "test-deployed-index"
    }

class MockMatch:
    def __init__(self, doc_id, distance):
        self.id = doc_id
        self.distance = distance

class MockNamespace:
    def __init__(self, name, allow_tokens):
        self.name = name
        self.allow_tokens = allow_tokens

@pytest.mark.asyncio
async def test_vector_search_disabled(mock_embedder, default_config):
    # Missing endpoint ID should disable it
    config = default_config.copy()
    config["index_endpoint_id"] = ""
    searcher = VectorSearchSearcher(**config, embedder=mock_embedder)
    
    assert searcher.enabled is False
    assert searcher.available is False
    results = await searcher.search("test query")
    assert results == []

@pytest.mark.asyncio
async def test_vector_search_success(mock_embedder, default_config):
    searcher = VectorSearchSearcher(**default_config, embedder=mock_embedder)
    assert searcher.enabled is True
    
    # Mock endpoint find_neighbors
    mock_endpoint = MagicMock()
    mock_endpoint.find_neighbors.return_value = [
        [MockMatch("doc1", 0.95), MockMatch("doc2", 0.85)]
    ]
    searcher._endpoint_cache = mock_endpoint  # Skip _get_endpoint / aiplatform.init
    
    # Disable hydration for unit test
    searcher._hydrate_results = lambda results: results
    
    results = await searcher.search("test query", max_results=2)
    
    assert len(results) == 2
    assert results[0].url == "vvs://doc1"
    assert results[0].relevance == 0.95
    assert results[0].source == SearchSource.VECTOR_SEARCH_ANN
    assert results[1].url == "vvs://doc2"
    assert results[1].relevance == 0.85

@pytest.mark.asyncio
async def test_vector_search_with_filter(mock_embedder, default_config):
    searcher = VectorSearchSearcher(**default_config, embedder=mock_embedder)
    
    mock_endpoint = MagicMock()
    mock_endpoint.find_neighbors.return_value = [
        [MockMatch("doc1", 0.95)]
    ]
    searcher._endpoint_cache = mock_endpoint
    searcher._hydrate_results = lambda results: results
    
    results = await searcher.search("test query", source_filter="arxiv")
    
    assert len(results) == 1
    # Verify find_neighbors was called with string_restricts
    call_kwargs = mock_endpoint.find_neighbors.call_args[1]
    assert len(call_kwargs["string_restricts"]) == 1
    assert call_kwargs["string_restricts"][0].name == "source"
    assert call_kwargs["string_restricts"][0].allow_tokens == ["arxiv"]

@pytest.mark.asyncio
async def test_vector_search_hydration(mock_embedder, default_config):
    """Test that _hydrate_results fills in skeletal results from Gnōsis."""
    searcher = VectorSearchSearcher(**default_config, embedder=mock_embedder)
    
    # Create skeletal results (as VVS would return)
    results = [
        SearchResult(
            url="vvs://paper123",
            title="[VVS] paper123",
            snippet="",
            relevance=0.95,
            source=SearchSource.VECTOR_SEARCH_ANN,
        ),
    ]
    
    # Mock Gnōsis table with pandas-like response
    mock_df = MagicMock()
    mock_row = {
        "primary_key": "paper123",
        "title": "Deep Learning for NLP",
        "abstract": "This paper explores deep learning approaches.",
        "content": "Full paper content here.",
        "url": "https://arxiv.org/abs/2301.00001",
        "source": "arxiv",
        "authors": "Smith et al.",
        "doi": "10.1234/test",
    }
    mock_df.iterrows.return_value = [(0, MagicMock(**{
        'get.side_effect': lambda k, d="": mock_row.get(k, d)
    }))]
    
    mock_table = MagicMock()
    mock_table.search.return_value.where.return_value.limit.return_value.to_pandas.return_value = mock_df
    searcher._lance_table = mock_table
    
    hydrated = searcher._hydrate_results(results)
    
    assert hydrated[0].title == "Deep Learning for NLP"
    assert hydrated[0].snippet.startswith("This paper explores")
    assert hydrated[0].url == "https://arxiv.org/abs/2301.00001"
    assert hydrated[0].metadata["vvs_doc_id"] == "paper123"
    assert hydrated[0].metadata["vvs_source"] == "arxiv"

@pytest.mark.asyncio
async def test_vector_search_hydration_graceful_fallback(mock_embedder, default_config):
    """When Gnōsis is unavailable, results stay skeletal (no crash)."""
    searcher = VectorSearchSearcher(**default_config, embedder=mock_embedder)
    
    results = [
        SearchResult(
            url="vvs://orphan_doc",
            title="[VVS] orphan_doc",
            snippet="",
            relevance=0.80,
            source=SearchSource.VECTOR_SEARCH_ANN,
        ),
    ]
    
    # _lance_table = None simulates unavailable Gnōsis
    searcher._lance_table = None
    
    hydrated = searcher._hydrate_results(results)
    
    # Should return original results unchanged
    assert hydrated[0].title == "[VVS] orphan_doc"
    assert hydrated[0].snippet == ""
