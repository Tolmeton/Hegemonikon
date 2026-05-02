# PROOF: mekhane/periskope/tests/test_llm_rerank.py
# PURPOSE: periskope モジュールの llm_rerank に対するテスト
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from mekhane.periskope.models import SearchResult, SearchSource
from mekhane.periskope.searchers.llm_reranker import LLMReranker

@pytest.fixture
def mock_search_results():
    return [
        SearchResult(source=SearchSource.SEARXNG, url="url1", title="Title 1", snippet="Snippet 1", relevance=0.0),
        SearchResult(source=SearchSource.SEARXNG, url="url2", title="Title 2", snippet="Snippet 2", relevance=0.0),
        SearchResult(source=SearchSource.SEARXNG, url="url3", title="Title 3", snippet="Snippet 3", relevance=0.0),
    ]

@pytest.fixture
def default_config():
    return {
        "llm_rerank": {
            "enabled": True,
            "flash_model": "gemini-3-flash-preview",
            "pro_model": "gemini-3.1-pro-preview",
            "batch_size_by_depth": {1: 30, 2: 15, 3: 5},
            "top_k": 2,
            "top_n": 1,
            "fallback_on_error": True,
            "cohere": {
                "enabled": True,
                "model": "rerank-v3.5",
                "top_n": 1,
            }
        }
    }

class MockResponse:
    def __init__(self, text):
        self.text = text

@pytest.mark.asyncio
async def test_llm_reranker_disabled(mock_search_results):
    reranker = LLMReranker({})
    assert reranker.enabled is False
    res = await reranker.rerank("query", mock_search_results)
    assert res == mock_search_results

@pytest.mark.asyncio
@patch("mekhane.periskope.searchers.llm_reranker.LLMReranker._get_cortex")
@patch("asyncio.to_thread")
async def test_llm_reranker_stage_1_only(mock_to_thread, mock_get_cortex, mock_search_results, default_config):
    reranker = LLMReranker(default_config)
    
    # Mock Cortex response
    mock_to_thread.return_value = MockResponse(
        '[{"id": 0, "r": 0.1, "sp": 0.1, "au": 0.1}, {"id": 1, "r": 0.9, "sp": 0.9, "au": 0.9}, {"id": 2, "r": 0.5, "sp": 0.5, "au": 0.5}]'
    )
    
    res = await reranker.rerank("test query", mock_search_results, depth=1)
    
    assert len(res) == 1
    assert res[0].title == "Title 2"
    assert res[0].relevance == 0.9

@pytest.mark.asyncio
@patch("mekhane.periskope.searchers.llm_reranker.LLMReranker._get_cortex")
@patch("asyncio.to_thread")
async def test_llm_reranker_stage_1_and_2(mock_to_thread, mock_get_cortex, mock_search_results, default_config):
    # AP-2: 偶然テストが通ることを防ぐため、Stage 2 に渡される top_k の順番と ID の対応を明示検証する
    default_config["llm_rerank"]["top_n"] = 2 # top_n を増やして 2位のスコアもアサートできるようにする
    reranker = LLMReranker(default_config)
    
    # Stage 1: [0]=0.2, [1]=0.8, [2]=0.5 -> ソート後: [1]=0.8, [2]=0.5, [0]=0.2
    # top_k=2 により、Stage 2 に渡されるのは [Title 2, Title 3] のリスト
    response1 = MockResponse('[{"id": 0, "r": 0.2, "sp": 0.2, "au": 0.2}, {"id": 1, "r": 0.8, "sp": 0.8, "au": 0.8}, {"id": 2, "r": 0.5, "sp": 0.5, "au": 0.5}]')
    
    # Stage 2: 渡されたリストの [0] つまり Title 2 を 0.4 に下落させ、[1] つまり Title 3 を 0.95 に上げる
    response2 = MockResponse('[{"id": 0, "r": 0.4, "sp": 0.4, "au": 0.4}, {"id": 1, "r": 0.95, "sp": 0.95, "au": 0.95}]')
    mock_to_thread.side_effect = [response1, response2]
    
    res = await reranker.rerank("test query", mock_search_results, depth=2)
    
    assert len(res) == 2
    # 1位は Stage 2 で 0.95 に上がった Title 3
    assert res[0].title == "Title 3"
    assert res[0].relevance == 0.95
    # 2位は Stage 2 で 0.4 に落ちた Title 2
    assert res[1].title == "Title 2"
    assert res[1].relevance == 0.4
    
@pytest.mark.asyncio
@patch("mekhane.periskope.searchers.llm_reranker.LLMReranker._get_cortex")
@patch("asyncio.to_thread")
async def test_llm_reranker_json_parsing(mock_to_thread, mock_get_cortex, mock_search_results, default_config):
    reranker = LLMReranker(default_config)
    
    # Missing IDs, markdown json block parsing
    mock_to_thread.return_value = MockResponse(
        '```json\n[{"id": 1, "r": 0.99, "sp": 0.99, "au": 0.99}]\n```'
    )
    
    res = await reranker.rerank("test query", mock_search_results, depth=1)
    
    assert len(res) == 1
    assert res[0].title == "Title 2"
    assert res[0].relevance == 0.99

@pytest.mark.asyncio
@patch("mekhane.periskope.searchers.llm_reranker.LLMReranker._get_cortex")
@patch("asyncio.to_thread")
async def test_invalid_json_graceful_fallback(mock_to_thread, mock_get_cortex, mock_search_results, default_config):
    """AP-1: LLMが不正なJSON（プレーンテキストのみなど）を返した場合のフォールバック動作を検証。"""
    reranker = LLMReranker(default_config)
    
    mock_to_thread.return_value = MockResponse(
        "I'm sorry, I can't score these results for you."
    )
    
    res = await reranker.rerank("test query", mock_search_results, depth=1)
    
    # 全部失敗した場合、元の結果がそのまま返り top_n = 1 で切り詰められる
    assert len(res) == 1
    assert res[0].relevance == 0.0

@pytest.mark.asyncio
@patch("mekhane.periskope.searchers.llm_reranker.LLMReranker._get_cortex")
@patch("asyncio.to_thread")
async def test_truncated_json_fallback(mock_to_thread, mock_get_cortex, mock_search_results, default_config):
    """AP-1: LLMが途中で切れたJSONを返した場合のフォールバック動作を検証。"""
    reranker = LLMReranker(default_config)
    
    mock_to_thread.return_value = MockResponse(
        '[{"id": 0, "r": 0.8, "sp": 0.8, "au": 0.8}, {"id": 1, "r": 0.5, "sp": 0.5, "au": 0.5' # 途中で切れている
    )
    
    res = await reranker.rerank("test query", mock_search_results, depth=1)
    
    # 完全にフォールバックし、元の結果がそのまま返り top_n = 1 で切り詰められる
    assert len(res) == 1
    assert res[0].relevance == 0.0

@pytest.mark.asyncio
@patch("mekhane.periskope.searchers.llm_reranker.LLMReranker._get_cohere")
@patch("mekhane.periskope.searchers.llm_reranker.LLMReranker._bulk_score")
@patch("asyncio.to_thread")
async def test_llm_reranker_cohere_fallback(mock_to_thread, mock_bulk_score, mock_get_cohere, mock_search_results, default_config):
    reranker = LLMReranker(default_config)
    
    # Force LLM stage to fail entirely
    mock_bulk_score.side_effect = Exception("Cortex API error")
    
    class MockCohereResponse:
        class Result:
            def __init__(self, index, relevance_score):
                self.index = index
                self.relevance_score = relevance_score
        def __init__(self):
            self.results = [self.Result(2, 0.98), self.Result(0, 0.4)]
    
    # For _cohere_rerank which uses to_thread
    mock_to_thread.return_value = MockCohereResponse()
    
    res = await reranker.rerank("test query", mock_search_results, depth=1)
    
    assert len(res) == 3
    assert res[0].title == "Title 3"
    assert res[0].relevance == 0.98


# ━━━ D2: 5-Dimension Score Parsing Tests ━━━

@pytest.mark.asyncio
@patch("mekhane.periskope.searchers.llm_reranker.LLMReranker._get_cortex")
@patch("asyncio.to_thread")
async def test_5dim_score_parsing(mock_to_thread, mock_get_cortex, mock_search_results, default_config):
    """5次元スコア (r, sp, au, fr, co) + 合成 score が正しくパースされること。"""
    reranker = LLMReranker(default_config)

    # LLM returns 5-dimensional rubric scores + weighted composite
    mock_to_thread.return_value = MockResponse(
        '[{"id": 0, "r": 0.9, "sp": 0.8, "au": 0.7, "fr": 0.6, "co": 0.8},'
        ' {"id": 1, "r": 0.2, "sp": 0.1, "au": 0.3, "fr": 0.1, "co": 0.2},'
        ' {"id": 2, "r": 0.5, "sp": 0.4, "au": 0.6, "fr": 0.3, "co": 0.5}]'
    )

    res = await reranker.rerank("test query", mock_search_results, depth=1)

    assert len(res) == 1
    assert res[0].title == "Title 1"
    assert res[0].relevance == 0.83
    # 5-dimensional scores should be preserved in metadata
    assert "llm_scores" in res[0].metadata
    assert res[0].metadata["llm_scores"] == {"r": 0.9, "sp": 0.8, "au": 0.7}


@pytest.mark.asyncio
@patch("mekhane.periskope.searchers.llm_reranker.LLMReranker._get_cortex")
@patch("asyncio.to_thread")
async def test_score_clamping(mock_to_thread, mock_get_cortex, mock_search_results, default_config):
    """score が 0.0-1.0 にクランプされること。"""
    reranker = LLMReranker(default_config)

    mock_to_thread.return_value = MockResponse(
        '[{"id": 0, "r": 1.5, "sp": 1.5, "au": 1.5}, {"id": 1, "r": -0.3, "sp": -0.3, "au": -0.3}, {"id": 2, "r": 0.7, "sp": 0.7, "au": 0.7}]'
    )

    res = await reranker.rerank("test query", mock_search_results, depth=1)

    assert len(res) == 1
    # id=0 (score=1.5 → clamped to 1.0) should be highest
    assert res[0].title == "Title 1"
    assert res[0].relevance == 1.0


def test_depth_timeout_mapping(default_config):
    """depth → timeout マッピングが正しいこと。"""
    reranker = LLMReranker(default_config)
    assert reranker.timeout_by_depth[1] == 30.0
    assert reranker.timeout_by_depth[2] == 60.0
    assert reranker.timeout_by_depth[3] is None


def test_cortex_injection(default_config):
    """cortex DI が正しく動作すること。"""
    mock_cortex = MagicMock()
    reranker = LLMReranker(default_config, cortex=mock_cortex)
    assert reranker._cortex is mock_cortex
    assert reranker._get_cortex() is mock_cortex
