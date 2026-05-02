# PROOF: mekhane/periskope/tests/test_cognition.py
# PURPOSE: periskope モジュールの cognition に対するテスト
from mekhane.periskope.models import SearchResult, SearchSource
from mekhane.periskope.cognition.phi1_blind_spot import phi1_coverage_gaps
from mekhane.periskope.cognition.phi3_context import phi3_context_setting, _classify_query_keyword
from mekhane.periskope.cognition.phi4_convergent import RankedQuery, DecisionFrame
from mekhane.periskope.cognition.phi7_belief_update import BeliefUpdate
from mekhane.periskope.quality_metrics import _ndcg
import pytest
from unittest.mock import AsyncMock, patch


def test_classify_query():
    assert _classify_query_keyword("free energy principle 論文") == "academic"
    assert _classify_query_keyword("how to build python server") == "implementation"
    assert _classify_query_keyword("latest AI news") == "news"
    assert _classify_query_keyword("what is consciousness") == "concept"


@pytest.mark.asyncio
async def test_phi3_context_setting():
    query = "active inference build code"
    candidates = [query, "active inference tutorial code"]
    with patch(
        "mekhane.periskope.cognition.phi3_context._llm_ask",
        new_callable=AsyncMock,
        return_value="implementation",
    ):
        plan = await phi3_context_setting(
            query=query,
            candidates=candidates,
            available_sources=["searxng", "brave", "tavily"],
            site_scoped_domains=["qiita.com", "zenn.dev"]
        )
    
    assert plan.query_type == "implementation"
    assert len(plan.queries_with_sources) == 2
    # Implementation adds site-scoped queries
    assert len(plan.site_scoped_queries) == 2
    assert "site:qiita.com" in plan.site_scoped_queries[0]


def test_phi1_coverage_gaps():
    # Empty results
    gaps1 = phi1_coverage_gaps("test", [], {})
    assert "No results found" in gaps1[0]

    # Single source
    gaps2 = phi1_coverage_gaps("test", [], {"searxng": 10})
    assert any("single source" in g for g in gaps2)

    # Academic but no academic sources
    gaps3 = phi1_coverage_gaps("test paper", [], {"searxng": 10, "brave": 5})
    assert any("no academic sources" in g for g in gaps3)


def test_quality_metrics_ndcg_fix():
    pre = [
        SearchResult(source=SearchSource.SEARXNG, title="low", relevance=0.3),
        SearchResult(source=SearchSource.BRAVE, title="high", relevance=0.9),
        SearchResult(source=SearchSource.TAVILY, title="mid", relevance=0.6),
    ]
    post = sorted(pre, key=lambda x: x.relevance, reverse=True)
    
    score_self = _ndcg(post, k=3, source_count=3)
    score_compare = _ndcg(post, k=3, pre_rerank_results=pre, source_count=3)
    
    assert score_self == 1.0  # self-comparison with multiple sources → 1.0
    assert score_compare < 1.0  # before rerank order was suboptimal
    assert score_compare > 0.5  # shouldn't be zero


def test_cognition_dataclasses():
    rq = RankedQuery(query="test", score=0.9, category="divergent")
    assert rq.score == 0.9

    df = DecisionFrame(key_findings=["fact A"], confidence=0.8)
    assert len(df.key_findings) == 1

    bu = BeliefUpdate(residual_error=0.4, should_loop=True, iteration=1)
    assert bu.should_loop is True
