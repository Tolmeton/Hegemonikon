# PROOF: mekhane/kube/tests/test_kube_agent.py
# PURPOSE: kube モジュールの kube_agent に対するテスト
"""
Kube Agent テスト: OODA ループの各フェーズを検証する。

Mock LLM + Mock Browser で、Agent の制御フローのみを検証。
消去テスト: このテストが存在する限り、agent.py を消すとテストが壊れる。
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import asdict

from mekhane.kubenous import (
    KubeAgent, Plan, SubGoal, Decision, WorkingMemory, AgentResult, _extract_json
)
from mekhane.kube.playwright_bridge import PageState, ActionResult


# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture
def mock_browser():
    browser = AsyncMock()
    browser.observe = AsyncMock(return_value=PageState(
        url="https://example.com",
        title="Example",
        snapshot="[role=main] Example Domain",
        interactive_count=3,
    ))
    browser.navigate = AsyncMock(return_value=ActionResult(success=True))
    browser.click = AsyncMock(return_value=ActionResult(success=True))
    browser.type_text = AsyncMock(return_value=ActionResult(success=True))
    browser.go_back = AsyncMock(return_value=ActionResult(success=True))
    browser.extract_text = AsyncMock(return_value=ActionResult(success=True, data="extracted"))
    browser.scroll_down = AsyncMock(return_value=ActionResult(success=True))
    browser.scroll_up = AsyncMock(return_value=ActionResult(success=True))
    browser.select_option = AsyncMock(return_value=ActionResult(success=True))
    browser.wait_for = AsyncMock(return_value=ActionResult(success=True))
    return browser


def make_plan_response(feasibility="possible", subgoals=None):
    """LLM plan 応答を生成する"""
    if subgoals is None:
        subgoals = [
            {"id": 1, "description": "example.com にアクセスする",
             "security_level": "read", "success_criteria": "ページが開く"},
        ]
    return json.dumps({
        "goal_understanding": "テスト目標",
        "feasibility": feasibility,
        "subgoals": subgoals,
        "requires_login": False,
        "requires_payment": False,
        "warnings": [],
    })


def make_decide_response(action="subgoal_complete", args=None, confidence=0.9):
    """LLM decide 応答を生成する"""
    return json.dumps({
        "thinking": "テスト思考",
        "action": action,
        "args": args or {"summary": "done"},
        "confidence": confidence,
        "security_level": "read",
        "confirm_required": False,
    })


# ── Plan tests ────────────────────────────────────────────────

class TestPlan:
    @pytest.mark.asyncio
    async def test_plan_parses_subgoals(self, mock_browser):
        llm_plan = AsyncMock(return_value=make_plan_response(subgoals=[
            {"id": 1, "description": "Step A", "security_level": "read",
             "success_criteria": "A done"},
            {"id": 2, "description": "Step B", "security_level": "write",
             "success_criteria": "B done", "depends_on": [1]},
        ]))
        llm_decide = AsyncMock()
        agent = KubeAgent(mock_browser, llm_plan, llm_decide)

        plan = await agent.plan("テスト目標")

        assert len(plan.subgoals) == 2
        assert plan.subgoals[0].description == "Step A"
        assert plan.subgoals[1].depends_on == [1]
        assert plan.feasibility == "possible"

    @pytest.mark.asyncio
    async def test_plan_impossible_goal(self, mock_browser):
        llm_plan = AsyncMock(return_value=make_plan_response(feasibility="impossible"))
        llm_decide = AsyncMock()
        agent = KubeAgent(mock_browser, llm_plan, llm_decide)

        result = await agent.execute("不可能な目標")

        assert result.status == "failed"
        assert "not feasible" in result.error


# ── Execute (OODA) tests ─────────────────────────────────────

class TestOODALoop:
    @pytest.mark.asyncio
    async def test_successful_execution(self, mock_browser):
        """Plan → Observe → Decide(complete) の正常系"""
        llm_plan = AsyncMock(return_value=make_plan_response())
        llm_decide = AsyncMock(return_value=make_decide_response("subgoal_complete"))
        agent = KubeAgent(mock_browser, llm_plan, llm_decide)

        result = await agent.execute("example.com を開く")

        assert result.status == "completed"
        assert result.steps_taken >= 1
        mock_browser.observe.assert_called()

    @pytest.mark.asyncio
    async def test_navigate_action(self, mock_browser):
        """Navigate アクション → subgoal_complete の流れ"""
        responses = [
            make_decide_response("navigate", {"url": "https://example.com"}),
            make_decide_response("subgoal_complete", {"summary": "done"}),
        ]
        llm_plan = AsyncMock(return_value=make_plan_response())
        llm_decide = AsyncMock(side_effect=responses)
        agent = KubeAgent(mock_browser, llm_plan, llm_decide)

        result = await agent.execute("example.com にアクセス")

        assert result.status == "completed"
        mock_browser.navigate.assert_awaited_once_with("https://example.com")

    @pytest.mark.asyncio
    async def test_security_escalation(self, mock_browser):
        """payment/auth レベルのサブゴールはエスカレーション"""
        llm_plan = AsyncMock(return_value=make_plan_response(subgoals=[
            {"id": 1, "description": "支払い処理",
             "security_level": "payment", "success_criteria": "支払い完了"},
        ]))
        llm_decide = AsyncMock()
        agent = KubeAgent(mock_browser, llm_plan, llm_decide)

        result = await agent.execute("何か購入する")

        assert result.status == "escalated"
        assert "payment" in result.escalation_question

    @pytest.mark.asyncio
    async def test_retry_on_parse_error(self, mock_browser):
        """JSON パースエラー時のリトライ"""
        responses = [
            "invalid json response",
            "still invalid",
            "nope",
            make_decide_response("subgoal_complete"),  # never reached — max_retries=2
        ]
        llm_plan = AsyncMock(return_value=make_plan_response())
        llm_decide = AsyncMock(side_effect=responses)
        agent = KubeAgent(mock_browser, llm_plan, llm_decide, max_steps=10)

        result = await agent.execute("テスト")

        assert result.status == "failed"  # max_retries exceeded

    @pytest.mark.asyncio
    async def test_action_failure_recovery(self, mock_browser):
        """アクション失敗 → リトライ → 成功"""
        mock_browser.click = AsyncMock(side_effect=[
            ActionResult(success=False, error="Element not found"),
            ActionResult(success=True),
        ])
        responses = [
            make_decide_response("click", {"selector": "#btn"}),
            make_decide_response("click", {"selector": "#btn"}),
            make_decide_response("subgoal_complete"),
        ]
        llm_plan = AsyncMock(return_value=make_plan_response())
        llm_decide = AsyncMock(side_effect=responses)
        agent = KubeAgent(mock_browser, llm_plan, llm_decide)

        result = await agent.execute("ボタンを押す")

        assert result.status == "completed"
        assert mock_browser.click.await_count == 2


# ── WorkingMemory tests ──────────────────────────────────────

class TestWorkingMemory:
    def test_add_and_retrieve_extractions(self):
        mem = WorkingMemory()
        mem.add_extraction("title", "Example Domain")
        mem.add_extraction("price", "100円")

        assert mem.extractions["title"] == "Example Domain"
        assert len(mem.extractions) == 2

    def test_action_history_fifo(self):
        mem = WorkingMemory(_max_actions=3)
        for i in range(5):
            mem.add_action(f"action_{i}", {}, True)

        assert len(mem.actions) == 3
        assert mem.actions[0]["action"] == "action_2"  # oldest kept

    def test_to_json_truncation(self):
        mem = WorkingMemory()
        # Add many large extractions
        for i in range(100):
            mem.add_extraction(f"key_{i}", "x" * 200)

        result = mem.to_json(max_tokens=500)
        assert len(result) <= 500 * 4 + 200  # rough bound


# ── _extract_json tests ──────────────────────────────────────

class TestExtractJson:
    def test_json_code_block(self):
        text = '```json\n{"action": "click"}\n```'
        assert _extract_json(text) == {"action": "click"}

    def test_bare_json(self):
        text = 'Here is the result: {"status": "ok"}'
        assert _extract_json(text) == {"status": "ok"}

    def test_no_json_raises(self):
        with pytest.raises(ValueError, match="No valid JSON"):
            _extract_json("no json here")
