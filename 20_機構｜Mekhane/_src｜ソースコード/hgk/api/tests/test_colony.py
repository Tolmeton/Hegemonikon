import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from hgk.api.colony import Colony, SubTask, WorkerType

@pytest.fixture
def mock_ochema_service():
    svc = MagicMock()
    # ask and chat are synchronous in service, asyncio.to_thread is used
    svc.chat = MagicMock()
    svc.ask = MagicMock()
    return svc

@pytest.mark.asyncio
async def test_colony_decompose_success(mock_ochema_service):
    # Setup mock response for COO chat
    mock_response = MagicMock()
    mock_response.text = '''```json
    {
      "analysis": "リクエストを分解します。",
      "subtasks": [
        {
          "id": "1",
          "description": "システム情報を取得",
          "worker_type": "engineer",
          "priority": 1,
          "depends_on": []
        }
      ]
    }
    ```'''
    mock_response.model = "mock-opus"
    mock_ochema_service.chat.return_value = mock_response

    colony = Colony(svc=mock_ochema_service)
    subtasks = await colony._decompose("システム情報を確認して")

    assert len(subtasks) == 1
    assert subtasks[0].id == "1"
    assert subtasks[0].worker_type == WorkerType.ENGINEER

@pytest.mark.asyncio
async def test_colony_fallback_to_gemini(mock_ochema_service):
    """Test that COO call falls back to Gemini if LS fails."""
    # Raise exception in primary LS call
    mock_ochema_service.chat.side_effect = Exception("LS is down")
    
    # Mock fallback success
    fallback_response = MagicMock()
    fallback_response.text = "```json\n{\"analysis\":\"fallback\",\"subtasks\":[]}\n```"
    fallback_response.model = "gemini-fallback"
    mock_ochema_service.ask.return_value = fallback_response

    colony = Colony(svc=mock_ochema_service)
    subtasks = await colony._decompose("フォールバックテスト")
    
    # Empty subtasks → auto-generated COO_DIRECT fallback task
    assert len(subtasks) == 1
    assert subtasks[0].worker_type == WorkerType.COO_DIRECT
    mock_ochema_service.chat.assert_called_once()
    mock_ochema_service.ask.assert_called_once()


# ─── Vertex AI Integration Tests ────────────────────────────────

@pytest.mark.asyncio
async def test_colony_vertex_coo_primary(mock_ochema_service):
    """When vertex_mode=True and VertexClaudeClient is available, COO uses Vertex first."""
    # Mock VertexClaudeClient
    mock_vc = MagicMock()
    mock_vc_response = MagicMock()
    mock_vc_response.text = '''```json
    {
      "analysis": "Vertex AI Claude COO analysis.",
      "subtasks": [
        {
          "id": "v1",
          "description": "Vertex AI 経由のタスク",
          "worker_type": "engineer",
          "priority": 1,
          "depends_on": []
        }
      ]
    }
    ```'''
    mock_vc_response.model = "claude-opus-4-6"
    mock_vc_response.account = "account-1"
    mock_vc_response.region = "us-east5"
    mock_vc_response.estimated_cost_usd = 0.05

    # ask_async is an async function
    async def _mock_ask_async(**kwargs):
        return mock_vc_response
    mock_vc.ask_async = AsyncMock(return_value=mock_vc_response)
    mock_vc.accounts = [MagicMock()]
    mock_vc.costs = MagicMock()
    mock_vc.costs.budget_usd = 600.0

    colony = Colony(svc=mock_ochema_service, vertex_mode=True)
    colony._vertex_claude = mock_vc  # Inject mock directly

    subtasks = await colony._decompose("Vertex AIテスト")

    # Vertex Claude should have been called
    mock_vc.ask_async.assert_called_once()
    # LS should NOT have been called (Vertex succeeded)
    mock_ochema_service.chat.assert_not_called()
    mock_ochema_service.ask.assert_not_called()

    assert len(subtasks) == 1
    assert subtasks[0].id == "v1"


@pytest.mark.asyncio
async def test_colony_vertex_fallback_to_ls(mock_ochema_service):
    """When Vertex Claude fails, COO falls back to LS Claude."""
    # Mock VertexClaudeClient that fails
    mock_vc = MagicMock()
    mock_vc.ask_async = AsyncMock(side_effect=Exception("Vertex quota exhausted"))
    mock_vc.accounts = [MagicMock()]
    mock_vc.costs = MagicMock()
    mock_vc.costs.budget_usd = 600.0

    # LS succeeds
    ls_response = MagicMock()
    ls_response.text = '''```json
    {
      "analysis": "LS Claude fallback.",
      "subtasks": [
        {
          "id": "ls1",
          "description": "LS 経由のフォールバック",
          "worker_type": "engineer",
          "priority": 1,
          "depends_on": []
        }
      ]
    }
    ```'''
    ls_response.model = "claude-opus-4-6"
    mock_ochema_service.chat.return_value = ls_response

    colony = Colony(svc=mock_ochema_service, vertex_mode=True)
    colony._vertex_claude = mock_vc

    subtasks = await colony._decompose("フォールバックテスト")

    # Vertex was tried and failed
    mock_vc.ask_async.assert_called_once()
    # LS was called as fallback
    mock_ochema_service.chat.assert_called_once()
    # Gemini was NOT called (LS succeeded)
    mock_ochema_service.ask.assert_not_called()

    assert len(subtasks) == 1
    assert subtasks[0].id == "ls1"


@pytest.mark.asyncio
async def test_colony_vertex_off_no_change(mock_ochema_service):
    """When vertex_mode=False, behavior is identical to original (no Vertex calls)."""
    ls_response = MagicMock()
    ls_response.text = '''```json
    {
      "analysis": "Original behavior.",
      "subtasks": [
        {
          "id": "orig1",
          "description": "既存挙動のテスト",
          "worker_type": "engineer",
          "priority": 1,
          "depends_on": []
        }
      ]
    }
    ```'''
    ls_response.model = "claude-opus-4-6"
    mock_ochema_service.chat.return_value = ls_response

    colony = Colony(svc=mock_ochema_service, vertex_mode=False)

    subtasks = await colony._decompose("既存挙動テスト")

    # LS should be called directly
    mock_ochema_service.chat.assert_called_once()
    # vertex_claude should not have been initialized
    assert colony._vertex_claude is None

    assert len(subtasks) == 1
    assert subtasks[0].id == "orig1"


@pytest.mark.asyncio
async def test_colony_vertex_engineer(mock_ochema_service):
    """When vertex_mode=True, Engineer uses CortexClient.ask_with_tools directly."""
    # Mock CortexClient.ask_with_tools
    mock_cortex_response = MagicMock()
    mock_cortex_response.text = "Engineer Vertex output"
    mock_cortex_response.model = "gemini-3-pro-preview"

    with patch("hgk.api.colony.asyncio.to_thread") as mock_to_thread:
        mock_to_thread.return_value = mock_cortex_response

        colony = Colony(svc=mock_ochema_service, vertex_mode=True)
        output, model = await colony._run_engineer("Build a module")

        # asyncio.to_thread should have been called with CortexClient.ask_with_tools
        mock_to_thread.assert_called_once()
        call_args = mock_to_thread.call_args
        # First positional arg is the callable (ask_with_tools method)
        callable_arg = call_args[0][0]
        assert "ask_with_tools" in str(callable_arg) or hasattr(callable_arg, '__name__')
        # Keyword args should include our prompt
        assert call_args[1].get("message") == "Build a module"
        assert call_args[1].get("max_iterations") == 10

    assert output == "Engineer Vertex output"
    assert model == "gemini-3-pro-preview"
    # OchemaService should NOT have been called
    mock_ochema_service.ask_with_tools.assert_not_called()


@pytest.mark.asyncio
async def test_colony_vertex_engineer_fallback(mock_ochema_service):
    """When Vertex Engineer fails, falls back to OchemaService path."""
    # Mock CortexClient to fail
    cortex_response = MagicMock()
    cortex_response.text = "OchemaService fallback output"
    cortex_response.model = "gemini-3-pro-preview"
    mock_ochema_service.ask_with_tools.return_value = cortex_response

    with patch("hgk.api.colony.asyncio.to_thread") as mock_to_thread:
        # First call (CortexClient path) fails, second call (OchemaService) succeeds
        mock_to_thread.side_effect = [
            Exception("CortexClient init failed"),  # Vertex path fails
            cortex_response,                          # OchemaService path succeeds
        ]

        colony = Colony(svc=mock_ochema_service, vertex_mode=True)
        output, model = await colony._run_engineer("Fallback test")

    assert output == "OchemaService fallback output"
    # to_thread called twice: once for CortexClient (failed), once for OchemaService
    assert mock_to_thread.call_count == 2

