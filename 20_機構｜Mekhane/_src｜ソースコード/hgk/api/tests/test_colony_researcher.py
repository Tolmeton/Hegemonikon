"""Researcher Worker 結合テスト.

Colony の Researcher Worker が PeriskopeEngine.research() を正常に呼び出し、
結果を WorkerResult に統合できることを検証する。
"""
import asyncio
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

from hgk.api.colony import Colony, WorkerType, SubTask


@dataclass
class MockReport:
    executive_summary: str = "テスト要約"
    synthesis: str = "テスト統合"


@pytest.mark.asyncio
async def test_researcher_worker_produces_output():
    """Researcher Worker が PeriskopeEngine を呼び出し結果を返すことを検証."""
    mock_svc = MagicMock()
    colony = Colony(svc=mock_svc)

    with patch("mekhane.periskope.engine.PeriskopeEngine") as MockEngine:
        mock_engine_instance = MagicMock()
        mock_engine_instance.research.return_value = MockReport(
            executive_summary="FEP は自由エネルギー原理の略で..."
        )
        MockEngine.return_value = mock_engine_instance

        subtask = SubTask(
            id="t1",
            description="FEP について調査",
            worker_type=WorkerType.RESEARCHER,
            priority=1,
        )

        result = await colony._execute_worker(subtask, "")

        assert result.success is True
        assert result.worker_type == WorkerType.RESEARCHER
        assert "FEP" in result.output
        assert result.model == "periskope"
        print(f"✅ Researcher Worker 結合テスト成功: output={result.output[:50]}...")


@pytest.mark.asyncio
async def test_researcher_worker_failure_is_graceful():
    """Researcher Worker がエラー時に graceful に失敗することを検証."""
    mock_svc = MagicMock()
    colony = Colony(svc=mock_svc)

    with patch("mekhane.periskope.engine.PeriskopeEngine") as MockEngine:
        mock_engine_instance = MagicMock()
        mock_engine_instance.research.side_effect = RuntimeError("API unavailable")
        MockEngine.return_value = mock_engine_instance

        subtask = SubTask(
            id="t1",
            description="壊れた調査",
            worker_type=WorkerType.RESEARCHER,
            priority=1,
        )

        result = await colony._execute_worker(subtask, "")

        assert result.success is False
        assert "API unavailable" in result.error
        print(f"✅ Researcher Worker エラーハンドリングテスト成功: error={result.error}")
