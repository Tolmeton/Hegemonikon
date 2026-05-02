from __future__ import annotations
# PROOF: mekhane/mcp/kube_mcp_server.py
# PURPOSE: mcp モジュールのサーバー実装 (kube_mcp_server)
"""
Kyvernetes MCP Server — 目標指向ブラウザ自動化。

Periskopē と同層の MCP サーバーとして、Claude に
kube_execute / kube_plan / kube_observe の3ツールを提供する。
"""


import asyncio
import json
import logging
import time
from pathlib import Path

log = logging.getLogger(__name__)

# Prompt templates (loaded at startup)
_PROMPT_DIR = Path(__file__).parent.parent / "kube" / "prompts"


def _load_prompt(name: str) -> str:
    """prompts/ ディレクトリから .prompt ファイルを読み込む"""
    path = _PROMPT_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    log.warning("Prompt file not found: %s", path)
    return ""


# ── MCP Tool Definitions ────────────────────────────────────

KUBE_TOOLS = [
    {
        "name": "kube_plan",
        "description": (
            "目標をサブゴールに分解して計画を返す (実行しない)。"
            "Planner プロンプトの dry-run。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "達成したい目標 (例: 'Google で FEP を検索して上位5件を集めて')",
                },
            },
            "required": ["goal"],
        },
    },
    {
        "name": "kube_execute",
        "description": (
            "ブラウザ上で自然言語の目標を自律的に達成する。"
            "内部で OODA ループを回し、完了時に結果を返す。"
            "payment/auth レベルのサブゴールは escalated を返す。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "達成したい目標",
                },
                "max_steps": {
                    "type": "integer",
                    "default": 30,
                    "description": "最大ステップ数",
                },
                "timeout": {
                    "type": "integer",
                    "default": 120,
                    "description": "タイムアウト秒",
                },
                "headless": {
                    "type": "boolean",
                    "default": True,
                    "description": "ヘッドレスモード (False でブラウザ表示)",
                },
            },
            "required": ["goal"],
        },
    },
    {
        "name": "kube_observe",
        "description": (
            "現在のブラウザの状態を構造化して返す。"
            "デバッグやユーザー確認用。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


# ── Tool Handlers ────────────────────────────────────────────

async def handle_kube_tool(name: str, arguments: dict, llm_callable=None) -> str:
    """
    MCP ツール呼び出しのハンドラ。

    llm_callable: async (prompt: str) -> str
        LLM を呼び出す関数。MCP サーバーのセットアップ時に注入する。
        None の場合は plan/execute は使えない (observe のみ)。
    """
    if name == "kube_plan":
        return await _handle_plan(arguments, llm_callable)
    elif name == "kube_execute":
        return await _handle_execute(arguments, llm_callable)
    elif name == "kube_observe":
        return await _handle_observe(arguments)
    else:
        return json.dumps({"error": f"Unknown tool: {name}"})


async def _handle_plan(arguments: dict, llm_callable) -> str:
    """kube_plan: タスク分解 (dry-run)"""
    from mekhane.kubenous import KubeAgent
    from mekhane.kube.playwright_bridge import PlaywrightBridge

    goal = arguments.get("goal", "")
    if not goal:
        return json.dumps({"error": "goal is required"})

    if not llm_callable:
        return json.dumps({"error": "LLM not configured"})

    plan_prompt = _load_prompt("plan.prompt")

    async def llm_plan(g: str) -> str:
        return await llm_callable(f"{plan_prompt}\n\n## ユーザーの目標\n{g}")

    # Plan は Playwright 不要
    bridge = PlaywrightBridge()
    agent = KubeAgent(browser=bridge, llm_plan=llm_plan, llm_decide=llm_callable)
    plan = await agent.plan(goal)

    return json.dumps({
        "goal_understanding": plan.goal_understanding,
        "feasibility": plan.feasibility,
        "subgoals": [
            {
                "id": sg.id,
                "description": sg.description,
                "security_level": sg.security_level,
                "success_criteria": sg.success_criteria,
            }
            for sg in plan.subgoals
        ],
        "requires_login": plan.requires_login,
        "requires_payment": plan.requires_payment,
        "warnings": plan.warnings,
    }, ensure_ascii=False, indent=2)


async def _handle_execute(arguments: dict, llm_callable) -> str:
    """kube_execute: 目標を自律実行"""
    from mekhane.kubenous import KubeAgent
    from mekhane.kube.playwright_bridge import PlaywrightBridge

    goal = arguments.get("goal", "")
    max_steps = arguments.get("max_steps", 30)
    timeout = arguments.get("timeout", 120)
    headless = arguments.get("headless", True)

    if not goal:
        return json.dumps({"error": "goal is required"})
    if not llm_callable:
        return json.dumps({"error": "LLM not configured"})

    plan_prompt = _load_prompt("plan.prompt")
    decide_prompt = _load_prompt("decide.prompt")

    async def llm_plan(g: str) -> str:
        return await llm_callable(f"{plan_prompt}\n\n## ユーザーの目標\n{g}")

    async def llm_decide(context: str) -> str:
        return await llm_callable(f"{decide_prompt}\n\n{context}")

    bridge = PlaywrightBridge()
    try:
        await bridge.launch(headless=headless)

        agent = KubeAgent(
            browser=bridge,
            llm_plan=llm_plan,
            llm_decide=llm_decide,
            max_steps=max_steps,
            timeout=timeout,
        )
        result = await agent.execute(goal)

        return json.dumps({
            "status": result.status,
            "result": result.result,
            "steps_taken": result.steps_taken,
            "elapsed_seconds": round(result.elapsed_seconds, 1),
            "escalation_question": result.escalation_question,
            "error": result.error,
        }, ensure_ascii=False, indent=2)

    finally:
        await bridge.close()


# ── Global state for observe ──

_active_bridge: PlaywrightBridge | None = None


async def _handle_observe(arguments: dict) -> str:
    """kube_observe: 現在のブラウザ状態を返す"""
    if not _active_bridge:
        return json.dumps({
            "error": "No active browser session. Use kube_execute first.",
        })

    state = await _active_bridge.observe()
    return json.dumps({
        "url": state.url,
        "title": state.title,
        "interactive_count": state.interactive_count,
        "snapshot_preview": state.snapshot[:2000],
    }, ensure_ascii=False, indent=2)
