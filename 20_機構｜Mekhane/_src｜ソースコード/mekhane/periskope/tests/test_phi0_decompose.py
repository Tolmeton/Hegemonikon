# PROOF: mekhane/periskope/tests/test_phi0_decompose.py
# PURPOSE: periskope モジュールの phi0_decompose に対するテスト
"""Tests for Φ0.5 Task Decomposition."""
import inspect
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mekhane.periskope.cognition.phi0_task_decompose import (
    SubTask,
    decompose_query,
    synthesize_subtask_results,
)


@pytest.mark.asyncio
@patch("mekhane.periskope.cognition._llm.llm_ask")
async def test_decompose_query_simple(mock_llm_ask):
    """Test that a simple query returns an empty list."""
    mock_llm_ask.return_value = "SIMPLE"
    
    subtasks = await decompose_query("What is active inference?")
    
    assert len(subtasks) == 0
    mock_llm_ask.assert_called_once()
    assert "What is active inference?" in mock_llm_ask.call_args[0][0]


@pytest.mark.asyncio
@patch("mekhane.periskope.cognition._llm.llm_ask")
async def test_decompose_query_compound(mock_llm_ask):
    """Test that a compound query is correctly decomposed, parsed, and sorted."""
    mock_response = (
        "2|Frontend|Compare React performance\n"
        "1|Backend|Compare Django and Express\n"
        "3|Deploy|Compare AWS and Vercel"
    )
    mock_llm_ask.return_value = mock_response

    subtasks = await decompose_query("Compare React vs Vue and Django vs Express")
    
    assert len(subtasks) == 3
    # Should be sorted by priority
    assert subtasks[0].priority == 1
    assert subtasks[0].focus == "Backend"
    assert subtasks[0].query == "Compare Django and Express"

    assert subtasks[1].priority == 2
    assert subtasks[1].focus == "Frontend"
    
    assert subtasks[2].priority == 3
    assert subtasks[2].focus == "Deploy"


@pytest.mark.asyncio
@patch("mekhane.periskope.cognition._llm.llm_ask")
async def test_decompose_malformed_output(mock_llm_ask):
    """Test graceful handling of malformed LLM output."""
    mock_llm_ask.return_value = "Not sure what to do here\nJust simple text"
    
    subtasks = await decompose_query("Some weird query")
    
    # Should safely return empty list because no format match
    assert len(subtasks) == 0


@pytest.mark.asyncio
@patch("mekhane.periskope.cognition._llm.llm_ask")
async def test_synthesize_subtask_results(mock_llm_ask):
    """Test subtask synthesis assembles context correctly."""
    mock_llm_ask.return_value = "Unified synthesis text."
    
    subtask1 = SubTask(query="Query 1", focus="Focus 1", priority=1)
    
    # Mock ResearchReport with synthesis
    report1 = MagicMock()
    synth_result = MagicMock()
    synth_result.content = "Findings for query 1"
    report1.synthesis = [synth_result]
    
    reports = [(subtask1, report1)]
    
    result = await synthesize_subtask_results("Original compound query", reports)
    
    assert result == "Unified synthesis text."
    mock_llm_ask.assert_called_once()
    prompt = mock_llm_ask.call_args[0][0]
    assert "Original compound query" in prompt
    assert "Focus 1" in prompt
    assert "Findings for query 1" in prompt
