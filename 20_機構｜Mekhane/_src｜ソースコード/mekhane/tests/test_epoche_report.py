# PROOF: mekhane/tests/test_epoche_report.py
# PURPOSE: max_iterations 到達時の Epoche 構造化レポート
"""Tests for mekhane.ochema.epoche_report."""

import json

import pytest


def test_build_max_iterations_epoche_response_structure():
    from mekhane.ochema.epoche_report import build_max_iterations_epoche_response

    r = build_max_iterations_epoche_response(
        max_iterations=3,
        last_tool_calls=[{"name": "read_file", "args": {"path": "a.md"}}],
        total_usage={"total_tokens": 42},
        model="gemini-test",
    )
    data = json.loads(r.text)
    er = data["epoche_report"]
    assert er["reason"] == "max_iterations_reached"
    assert er["max_iterations"] == 3
    assert er["synthesis_status"] == "pending"
    assert len(er["last_executed_tool_calls"]) == 1
    assert er["last_executed_tool_calls"][0]["name"] == "read_file"
    assert "completed_tool_calls" not in er
    assert "unresolved_tool_calls" not in er
    assert r.model == "gemini-test"
    assert r.token_usage["total_tokens"] == 42
    assert r.pending_synthesis is not None
    assert r.pending_synthesis[0]["name"] == "read_file"


def test_build_max_iterations_preserves_tool_call_id():
    from mekhane.ochema.epoche_report import build_max_iterations_epoche_response

    r = build_max_iterations_epoche_response(
        max_iterations=1,
        last_tool_calls=[
            {"name": "read_file", "args": {"path": "x"}, "id": "call_abc123"},
        ],
        total_usage={},
        model="m",
    )
    data = json.loads(r.text)
    row = data["epoche_report"]["last_executed_tool_calls"][0]
    assert row["id"] == "call_abc123"
    assert r.pending_synthesis is not None
    assert r.pending_synthesis[0]["id"] == "call_abc123"


def test_build_max_iterations_epoche_empty_calls():
    from mekhane.ochema.epoche_report import build_max_iterations_epoche_response

    r = build_max_iterations_epoche_response(
        max_iterations=1,
        last_tool_calls=[],
        total_usage={},
        model="m",
    )
    data = json.loads(r.text)
    assert data["epoche_report"]["last_executed_tool_calls"] == []
    assert data["epoche_report"]["synthesis_status"] == "pending"
    assert r.pending_synthesis is None


def test_build_claude_variant():
    from mekhane.ochema.epoche_report import build_max_iterations_epoche_response_claude

    r = build_max_iterations_epoche_response_claude(
        max_iterations=2,
        last_tool_calls=[{"name": "grep", "args": {"pattern": "x"}}],
        model="claude-test",
    )
    assert r.token_usage == {}
    data = json.loads(r.text)
    assert "epoche_report" in data
    assert data["epoche_report"]["synthesis_status"] == "pending"


def test_cortex_tools_max_iterations_returns_epoche(monkeypatch):
    """ask_with_tools がループ上限で Epoche JSON を返す (API はモック)。"""
    monkeypatch.setattr(
        "mekhane.agent_guard.apotheke.retrieve_context",
        lambda *a, **k: [],
    )
    from mekhane.ochema.cortex_tools import CortexTools
    from mekhane.ochema.types import LLMResponse

    class _FakeAPI:
        def _build_request(self, **kwargs):
            return {}

        def _call_api(self, *a, **kw):
            return {}

        def _parse_response(self, raw):
            r = LLMResponse(
                model="m",
                token_usage={
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 1,
                },
            )
            r.function_calls = [{"name": "noop", "args": {}}]  # type: ignore[attr-defined]
            r.raw_model_parts = [{"functionCall": {"name": "noop", "args": {}}}]  # type: ignore[attr-defined]
            return r

        def ask(self, *a, **kw):
            return ""

    tools = CortexTools(_FakeAPI())  # type: ignore[arg-type]

    from mekhane.ochema import tools as ochema_tools_mod

    def _noop_execute(name, args):
        return {"output": "ok"}

    monkeypatch.setattr(ochema_tools_mod, "execute_tool", _noop_execute)

    noop_tool = {
        "name": "noop",
        "description": "no-op for test",
        "parameters": {"type": "object", "properties": {}},
    }
    r = tools.ask_with_tools(
        message="hi",
        model="gemini-2.0-flash",
        temperature=0.0,
        max_tokens=100,
        max_iterations=2,
        tools=[noop_tool],
    )
    body = json.loads(r.text)
    assert body["epoche_report"]["reason"] == "max_iterations_reached"
    assert body["epoche_report"]["synthesis_status"] == "pending"
    assert r.pending_synthesis
