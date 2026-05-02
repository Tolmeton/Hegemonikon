# PROOF: [L2/テスト] <- mekhane/ochema/tests/test_cost_estimation.py
# PURPOSE: Cortex cost estimation と top-level cost_usd 契約の回帰テスト
from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

from mekhane.ochema.cortex_api import CortexAPI
from mekhane.ochema.service import OchemaService


def _make_api() -> CortexAPI:
    auth = MagicMock()
    auth._on_token_change = None
    return CortexAPI(auth)


class TestCortexCostEstimation:
    def test_parse_response_sets_cost_fields_when_litellm_available(self):
        api = _make_api()
        fake_litellm = ModuleType("litellm")
        fake_litellm.completion_cost = MagicMock(return_value=0.0123)
        response = {
            "response": {
                "modelVersion": "gemini-2.0-flash",
                "candidates": [{"content": {"parts": [{"text": "hello"}]}}],
                "usageMetadata": {
                    "promptTokenCount": 10,
                    "candidatesTokenCount": 5,
                    "totalTokenCount": 15,
                },
            }
        }

        with patch.dict(sys.modules, {"litellm": fake_litellm}):
            result = api._parse_response(response)

        assert result.text == "hello"
        assert result.cost_usd == 0.0123
        assert result.token_usage["estimated_cost_usd"] == 0.0123
        fake_litellm.completion_cost.assert_called_once_with(
            completion_response=None,
            model="gemini-2.0-flash",
            prompt_tokens=10,
            completion_tokens=5,
        )

    def test_parse_response_keeps_none_without_usage_metadata(self):
        api = _make_api()
        response = {
            "response": {
                "modelVersion": "gemini-2.0-flash",
                "candidates": [{"content": {"parts": [{"text": "hello"}]}}],
            }
        }

        result = api._parse_response(response)

        assert result.text == "hello"
        assert result.cost_usd is None
        assert result.token_usage == {}

    def test_parse_response_survives_litellm_import_failure(self):
        api = _make_api()
        response = {
            "response": {
                "modelVersion": "gemini-2.0-flash",
                "candidates": [{"content": {"parts": [{"text": "hello"}]}}],
                "usageMetadata": {
                    "promptTokenCount": 10,
                    "candidatesTokenCount": 5,
                    "totalTokenCount": 15,
                },
            }
        }

        with patch.dict(sys.modules, {"litellm": None}):
            result = api._parse_response(response)

        assert result.text == "hello"
        assert result.cost_usd is None
        assert "estimated_cost_usd" not in result.token_usage
        assert result.token_usage["total_tokens"] == 15

    def test_parse_response_survives_litellm_runtime_failure(self):
        api = _make_api()
        fake_litellm = ModuleType("litellm")
        fake_litellm.completion_cost = MagicMock(side_effect=RuntimeError("boom"))
        response = {
            "response": {
                "modelVersion": "gemini-2.0-flash",
                "candidates": [{"content": {"parts": [{"text": "hello"}]}}],
                "usageMetadata": {
                    "promptTokenCount": 10,
                    "candidatesTokenCount": 5,
                    "totalTokenCount": 15,
                },
            }
        }

        with patch.dict(sys.modules, {"litellm": fake_litellm}):
            result = api._parse_response(response)

        assert result.text == "hello"
        assert result.cost_usd is None
        assert "estimated_cost_usd" not in result.token_usage
        assert result.token_usage["total_tokens"] == 15


class TestVertexTopLevelCost:
    def test_vertex_path_sets_top_level_cost_usd(self):
        OchemaService.reset()
        svc = OchemaService.get()
        fake_resp = SimpleNamespace(
            text="vertex answer",
            provider="vertex",
            account="acct-a",
            region="us-central1",
            input_tokens=12,
            output_tokens=34,
            total_tokens=46,
            estimated_cost_usd=0.0456,
            stop_reason="end_turn",
            parsed=None,
        )

        with patch("mekhane.ochema.vertex_claude.VertexClaudeClient") as mock_vertex:
            mock_vertex.return_value.ask.return_value = fake_resp
            result = svc._ask_vertex_claude("hello")

        assert result.text == "vertex answer"
        assert result.cost_usd == 0.0456
        assert result.token_usage["estimated_cost_usd"] == 0.0456

        OchemaService.reset()
