# PROOF: mekhane/periskope/tests/test_schedule_override.py
# PURPOSE: periskope モジュールの schedule_override に対するテスト
"""
Periskope MCP Server Schedule Override Test

research / benchmark アクション時に MCP 経由で渡された
decay_type や alpha_schedule が PeriskopeEngine の設定に上書き適用されるかを検証する。
消去テスト: periskope_mcp_server.py を消すとこのテストが壊れる。
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from mekhane.mcp.periskope_mcp_server import handle_research, handle_benchmark


@pytest.mark.asyncio
async def test_handle_research_schedule_override():
    """handle_research 呼び出し時に schedule が上書きされるか"""
    with patch("mekhane.mcp.periskope_mcp_server.PeriskopeEngine") as MockEngine:
        engine_instance = MagicMock()
        engine_instance._config = {"iterative_deepening": {"decay_type": "linear", "alpha_schedule": "linear"}}
        engine_instance.research = AsyncMock()
        mock_report = MagicMock()
        mock_report.markdown.return_value = "report"
        mock_report.elapsed_seconds = 1.0
        mock_report.quality_metrics.summary.return_value = "mock_summary"
        del mock_report.reasoning_trace
        del mock_report.thinking_trace
        engine_instance.research.return_value = mock_report
        MockEngine.return_value = engine_instance

        # Override なし
        await handle_research({"query": "test", "sources": []})
        assert engine_instance._config["iterative_deepening"]["decay_type"] == "linear"

        # Override あり
        await handle_research({
            "query": "test",
            "sources": [],
            "decay_type": "logsnr",
            "alpha_schedule": "sigmoid"
        })
        assert engine_instance._config["iterative_deepening"]["decay_type"] == "logsnr"
        assert engine_instance._config["iterative_deepening"]["alpha_schedule"] == "sigmoid"


@pytest.mark.asyncio
async def test_handle_benchmark_schedule_override():
    """handle_benchmark 呼び出し時に schedule が上書きされるか"""
    with patch("mekhane.mcp.periskope_mcp_server.PeriskopeEngine") as MockEngine:
        engine_instance = MagicMock()
        engine_instance._config = {"iterative_deepening": {"decay_type": "linear", "alpha_schedule": "linear"}}
        engine_instance.run = AsyncMock(return_value={"ndcg": 0.9, "entropy": 0.8, "coverage": 0.7})
        MockEngine.return_value = engine_instance

        # Override あり
        await handle_benchmark({
            "queries": ["test"],
            "decay_type": "cosine",
            "alpha_schedule": "cosine"
        })
        assert engine_instance._config["iterative_deepening"]["decay_type"] == "cosine"
        assert engine_instance._config["iterative_deepening"]["alpha_schedule"] == "cosine"
