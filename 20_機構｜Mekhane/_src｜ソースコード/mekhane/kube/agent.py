from __future__ import annotations
# PROOF: mekhane/kube/agent.py
# PURPOSE: kube モジュールの agent
"""
Kyvernetes Agent — OODA ループエンジン。

Observe → Orient → Decide → Act の認知サイクルを回し、
自然言語の目標をブラウザ操作で達成する。
"""


import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable, Awaitable

from mekhane.kube.playwright_bridge import PlaywrightBridge, PageState, ActionResult

log = logging.getLogger(__name__)

# ── Data Structures ──────────────────────────────────────────

@dataclass
class SubGoal:
    id: int
    description: str
    security_level: str  # read | write | payment | auth
    success_criteria: str
    failure_fallback: Optional[str] = None
    depends_on: list[int] = field(default_factory=list)


@dataclass
class Plan:
    goal_understanding: str
    feasibility: str  # possible | partial | impossible
    subgoals: list[SubGoal]
    requires_login: bool = False
    requires_payment: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass
class Decision:
    thinking: str
    action: str
    args: dict
    confidence: float
    security_level: str
    confirm_required: bool = False
    extractions: Optional[dict] = None


@dataclass
class WorkingMemory:
    """タスク実行中のデータキャッシュ"""
    extractions: dict = field(default_factory=dict)
    actions: list[dict] = field(default_factory=list)
    _max_actions: int = 50

    def add_extraction(self, key: str, value: str):
        self.extractions[key] = value

    def add_action(self, action: str, args: dict, success: bool):
        self.actions.append({"action": action, "args": args, "success": success})
        if len(self.actions) > self._max_actions:
            self.actions = self.actions[-self._max_actions:]

    def recent_actions(self, n: int = 5) -> list[dict]:
        return self.actions[-n:]

    def to_json(self, max_tokens: int = 2000) -> str:
        """LLM プロンプトに注入する JSON 文字列 (サイズ制限付き)"""
        data = {"extractions": self.extractions, "recent_actions": self.recent_actions()}
        text = json.dumps(data, ensure_ascii=False, indent=2)
        if len(text) > max_tokens * 4:  # rough token estimate
            # FIFO: 古い extraction を捨てる
            keys = list(self.extractions.keys())
            while len(text) > max_tokens * 4 and keys:
                del self.extractions[keys.pop(0)]
                data["extractions"] = self.extractions
                text = json.dumps(data, ensure_ascii=False, indent=2)
        return text


@dataclass
class AgentResult:
    status: str          # completed | failed | escalated
    result: dict         # ワーキングメモリの最終状態
    steps_taken: int
    elapsed_seconds: float
    escalation_question: Optional[str] = None
    error: Optional[str] = None


# ── LLM Client Protocol ─────────────────────────────────────

# agent.py は LLM の呼び出し方を知らない。
# MCP サーバー側が LLM クライアントを注入する。
LLMCallable = Callable[[str], Awaitable[str]]


# ── Agent ────────────────────────────────────────────────────

class KubeAgent:
    """
    Kyvernetes: OODA ループベースのブラウザ自動化エージェント。

    LLM と Playwright の具体的な呼び出しは外部から注入される。
    このクラスのはループ制御とエラーリカバリの責務のみ。
    """

    def __init__(
        self,
        browser: PlaywrightBridge,
        llm_plan: LLMCallable,    # plan.prompt を使ってタスク分解する関数
        llm_decide: LLMCallable,  # decide.prompt を使って次アクションを決める関数
        max_steps: int = 30,
        timeout: float = 120.0,
    ):
        self.browser = browser
        self.llm_plan = llm_plan
        self.llm_decide = llm_decide
        self.max_steps = max_steps
        self.timeout = timeout

    async def plan(self, goal: str) -> Plan:
        """目標をサブゴールに分解する (dry-run: 実行しない)"""
        response = await self.llm_plan(goal)
        data = _extract_json(response)
        return Plan(
            goal_understanding=data.get("goal_understanding", goal),
            feasibility=data.get("feasibility", "possible"),
            subgoals=[
                SubGoal(
                    id=sg["id"],
                    description=sg["description"],
                    security_level=sg.get("security_level", "read"),
                    success_criteria=sg.get("success_criteria", ""),
                    failure_fallback=sg.get("failure_fallback"),
                    depends_on=sg.get("depends_on", []),
                )
                for sg in data.get("subgoals", [])
            ],
            requires_login=data.get("requires_login", False),
            requires_payment=data.get("requires_payment", False),
            warnings=data.get("warnings", []),
        )

    async def execute(self, goal: str) -> AgentResult:
        """目標を自律的に達成する (OODA ループ)"""
        start = time.monotonic()
        total_steps = 0
        memory = WorkingMemory()

        # Phase 1: Plan
        plan = await self.plan(goal)

        if plan.feasibility == "impossible":
            return AgentResult(
                status="failed",
                result=memory.extractions,
                steps_taken=0,
                elapsed_seconds=time.monotonic() - start,
                error=f"Goal is not feasible: {plan.goal_understanding}",
            )

        # Phase 2: Execute subgoals
        for subgoal in plan.subgoals:
            # Security check
            if subgoal.security_level in ("payment", "auth"):
                return AgentResult(
                    status="escalated",
                    result=memory.extractions,
                    steps_taken=total_steps,
                    elapsed_seconds=time.monotonic() - start,
                    escalation_question=(
                        f"サブゴール '{subgoal.description}' は "
                        f"{subgoal.security_level} レベルの操作が必要です。"
                        f"続行しますか？"
                    ),
                )

            result, steps = await self._execute_subgoal(
                subgoal, memory, start
            )
            total_steps += steps

            if result == "failed":
                return AgentResult(
                    status="failed",
                    result=memory.extractions,
                    steps_taken=total_steps,
                    elapsed_seconds=time.monotonic() - start,
                    error=f"Subgoal failed: {subgoal.description}",
                )

        return AgentResult(
            status="completed",
            result=memory.extractions,
            steps_taken=total_steps,
            elapsed_seconds=time.monotonic() - start,
        )

    async def _execute_subgoal(
        self, subgoal: SubGoal, memory: WorkingMemory, start_time: float
    ) -> tuple[str, int]:
        """1つのサブゴールに対する OODA ループ"""
        retry_count = 0
        max_retries = 2

        for step in range(self.max_steps):
            # Timeout check
            elapsed = time.monotonic() - start_time
            if elapsed > self.timeout:
                log.warning("Timeout after %.1fs", elapsed)
                return "failed", step + 1

            # ── Observe ──
            state = await self.browser.observe()

            # ── Orient + Decide (LLM) ──
            prompt_input = self._build_decide_input(subgoal, state, memory)
            raw_response = await self.llm_decide(prompt_input)

            try:
                decision = self._parse_decision(raw_response)
            except (json.JSONDecodeError, ValueError) as e:
                log.error("Failed to parse decision: %s", e)
                retry_count += 1
                if retry_count > max_retries:
                    return "failed", step + 1
                continue

            # ── Subgoal termination ──
            if decision.action == "subgoal_complete":
                log.info("Subgoal complete: %s", decision.args.get("summary", ""))
                return "completed", step + 1

            if decision.action == "subgoal_fail":
                log.warning("Subgoal failed: %s", decision.args.get("reason", ""))
                return "failed", step + 1

            if decision.action == "escalate":
                log.info("Escalating to user: %s", decision.args.get("question", ""))
                return "escalated", step + 1

            # ── Security gate ──
            if decision.confirm_required:
                log.info("Security gate: confirm_required for %s", decision.action)
                return "escalated", step + 1

            # ── Act ──
            action_result = await self._execute_action(decision)
            memory.add_action(decision.action, decision.args, action_result.success)

            if decision.extractions:
                for k, v in decision.extractions.items():
                    memory.add_extraction(k, v)

            # ── Error Recovery ──
            if not action_result.success:
                retry_count += 1
                log.warning(
                    "Action failed (retry %d/%d): %s",
                    retry_count, max_retries, action_result.error,
                )
                if retry_count > max_retries:
                    return "failed", step + 1
            else:
                retry_count = 0

        return "failed", self.max_steps

    async def _execute_action(self, decision: Decision) -> ActionResult:
        """Deciderの出力をPlaywrightBridge操作に変換して実行"""
        action = decision.action
        args = decision.args

        dispatch = {
            "navigate": lambda: self.browser.navigate(args.get("url", "")),
            "click": lambda: self.browser.click(args.get("selector", args.get("ref", ""))),
            "type": lambda: self.browser.type_text(
                args.get("selector", args.get("ref", "")),
                args.get("text", ""),
                args.get("submit", False),
            ),
            "select": lambda: self.browser.select_option(
                args.get("selector", args.get("ref", "")),
                args.get("value", ""),
            ),
            "scroll_down": lambda: self.browser.scroll_down(),
            "scroll_up": lambda: self.browser.scroll_up(),
            "go_back": lambda: self.browser.go_back(),
            "extract": lambda: self.browser.extract_text(
                args.get("selector", args.get("ref", ""))
            ),
            "wait": lambda: self.browser.wait_for(
                args.get("text", ""), args.get("seconds", 5.0)
            ),
        }

        handler = dispatch.get(action)
        if not handler:
            return ActionResult(success=False, error=f"Unknown action: {action}")

        return await handler()

    def _build_decide_input(
        self, subgoal: SubGoal, state: PageState, memory: WorkingMemory
    ) -> str:
        """Decider LLM への入力を構築する"""
        return (
            f"current_subgoal: \"{subgoal.description}\"\n"
            f"subgoal_success_criteria: \"{subgoal.success_criteria}\"\n"
            f"page_url: \"{state.url}\"\n"
            f"page_title: \"{state.title}\"\n"
            f"\n## Accessibility Snapshot\n```\n{state.snapshot}\n```\n"
            f"\n## Working Memory\n{memory.to_json()}\n"
            f"\n## Recent Actions\n{json.dumps(memory.recent_actions(), ensure_ascii=False)}\n"
        )

    @staticmethod
    def _parse_decision(raw: str) -> Decision:
        data = _extract_json(raw)
        return Decision(
            thinking=data.get("thinking", ""),
            action=data.get("action", ""),
            args=data.get("args", {}),
            confidence=data.get("confidence", 0.5),
            security_level=data.get("security_level", "read"),
            confirm_required=data.get("confirm_required", False),
            extractions=data.get("extractions"),
        )


# ── Utilities ────────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """LLM 応答から JSON を抽出する (test_prompt_parse.py と同じロジック)"""
    text = text.strip()

    # ```json ブロック
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end != -1:
            return json.loads(text[start:end].strip())

    # ``` ブロック
    if "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end != -1:
            candidate = text[start:end].strip()
            if candidate.startswith("{"):
                return json.loads(candidate)

    # 裸の JSON
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError as e:
            import logging
            logging.getLogger(__name__).error(f"JSONDecodeError: {e}\\nRaw LLM text:\\n{text}")
            raise

    raise ValueError("No valid JSON found in LLM response")
