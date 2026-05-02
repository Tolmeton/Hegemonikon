#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/ochema/ A0→HGK Gateway Tool Use
# PURPOSE: HGK Gateway ツールを Gemini Function Calling / Claude Tool Use で利用可能にする

"""
HGK Gateway Tool Definitions + Executor

ask_with_tools() から呼び出される HGK Gateway ツール群。
ファイル操作ツール (tools.py) と組み合わせることで、
LLM が HGK 全機能 + ローカルファイル操作を自律的に実行可能になる。

Integration:
    tools.py の execute_tool() からフォールスルーで呼ばれる。
    または ask_with_tools(tools=ALL_TOOL_DEFINITIONS) で直接指定。
"""
from __future__ import annotations
from typing import Any


import logging
import os
import time

logger = logging.getLogger(__name__)

# HGK tools with side effects — trigger WBC alert
HGK_SIDE_EFFECT_TOOLS = frozenset({"hgk_digest_run", "hgk_digest_mark", "hgk_idea_capture"})

# ─── Tool Definitions (Gemini Function Calling format) ───────────

HGK_TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "hgk_pks_search",
        "category": "knowledge",
        "description": (
            "Search the full HGK knowledge base (34K+ docs). "
            "Searches Gnōsis (papers), Kairos (conversations), "
            "Sophia (KI), and Chronos (timeline) simultaneously."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language search query"},
                "k": {"type": "integer", "description": "Max results (default: 10)"},
                "sources": {
                    "type": "string",
                    "description": "Comma-separated sources filter (gnosis,kairos,sophia,chronos). Empty = all",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "hgk_search",
        "category": "knowledge",
        "description": (
            "Search the HGK knowledge base (KI / Gnōsis / Sophia). "
            "Supports hybrid (vector+keyword), vector-only, or keyword-only modes."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results (default: 5)"},
                "mode": {
                    "type": "string",
                    "description": "Search mode: hybrid, vector, keyword (default: hybrid)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "hgk_ccl_execute",
        "category": "ccl",
        "description": (
            "Execute a CCL (Cognitive Control Language) expression. "
            "CCL is HGK's cognitive programming language. "
            "Examples: /noe+ (deep thinking), /dia+~*/noe (adversarial review)"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ccl": {"type": "string", "description": "CCL expression (e.g. /noe+, /dia+~*/noe)"},
                "context": {"type": "string", "description": "Execution context (analysis target, etc.)"},
            },
            "required": ["ccl"],
        },
    },
    {
        "name": "hgk_ccl_dispatch",
        "category": "ccl",
        "description": "Parse a CCL expression and return its structure without executing.",
        "parameters": {
            "type": "object",
            "properties": {
                "ccl": {"type": "string", "description": "CCL expression to parse"},
            },
            "required": ["ccl"],
        },
    },
    {
        "name": "hgk_status",
        "category": "system",
        "description": "Get HGK system overview: Handoff count, KI count, Doxa count, Ideas, latest Handoff, Digestor status.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "hgk_health",
        "category": "system",
        "description": "Get detailed HGK health report: Health Score, Heartbeat, WBC alerts.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "hgk_doxa_read",
        "category": "knowledge",
        "description": "Read the Doxa (belief store). Shows accumulated laws, lessons, and beliefs.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "hgk_handoff_read",
        "category": "session",
        "description": "Read the latest session handoff(s). Shows what was done previously and what to do next.",
        "parameters": {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "Number of handoffs to read (default: 1)"},
            },
        },
    },
    {
        "name": "hgk_idea_capture",
        "category": "knowledge",
        "description": "Save an idea memo. Automatically loaded on next /boot.",
        "parameters": {
            "type": "object",
            "properties": {
                "idea": {"type": "string", "description": "Idea content (max 10,000 chars)"},
                "tags": {"type": "string", "description": "Comma-separated tags (e.g. FEP, design, experiment)"},
            },
            "required": ["idea"],
        },
    },
    {
        "name": "hgk_notifications",
        "category": "system",
        "description": "Check unread notifications (INFO/HIGH/CRITICAL) from the HGK system.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of notifications to show (default: 10)"},
            },
        },
    },
    {
        "name": "hgk_paper_search",
        "category": "research",
        "description": "Search academic papers via Semantic Scholar.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (e.g. 'active inference free energy')"},
                "limit": {"type": "integer", "description": "Max results (1-20, default: 5)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "hgk_digest_check",
        "category": "digest",
        "description": "Check incoming/ for undigested files. Lists papers waiting for digestion.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "hgk_digest_list",
        "category": "digest",
        "description": "Evaluate paper candidates using Digestor selector (dry-run).",
        "parameters": {
            "type": "object",
            "properties": {
                "topics": {"type": "string", "description": "Target topics (comma-separated). Empty = all."},
                "max_candidates": {"type": "integer", "description": "Max candidates (1-20, default: 10)"},
            },
        },
    },
    {
        "name": "hgk_digest_run",
        "category": "digest",
        "description": "Run the Digestor pipeline. Default is dry_run. Set dry_run=false to generate .md files.",
        "parameters": {
            "type": "object",
            "properties": {
                "topics": {"type": "string", "description": "Target topics (comma-separated). Empty = all."},
                "max_papers": {"type": "integer", "description": "Max papers (1-50, default: 20)"},
                "dry_run": {"type": "boolean", "description": "true=report only, false=generate files (default: true)"},
            },
        },
    },
    {
        "name": "hgk_digest_topics",
        "category": "digest",
        "description": "List all configured digest topics from topics.yaml.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "hgk_digest_mark",
        "category": "digest",
        "description": "Move digested files from incoming/ to processed/.",
        "parameters": {
            "type": "object",
            "properties": {
                "filenames": {
                    "type": "string",
                    "description": "Filenames to move (comma-separated). Empty = all eat_*.md files.",
                },
            },
        },
    },
    {
        "name": "hgk_proactive_push",
        "category": "research",
        "description": (
            "Autophōnos proactive knowledge push. "
            "Surfaces relevant knowledge based on context/topics. "
            "Papers narrate themselves in first person."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topics": {"type": "string", "description": "Comma-separated topics. Empty = auto from Handoff."},
                "max_results": {"type": "integer", "description": "Max results (default: 5)"},
                "use_advocacy": {"type": "boolean", "description": "First-person narration mode (default: true)"},
            },
        },
    },
    {
        "name": "hgk_sop_generate",
        "category": "research",
        "description": "Generate a /sop research request template for Gemini Deep Research or Perplexity.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Research topic"},
                "decision": {"type": "string", "description": "What decision this research informs"},
                "hypothesis": {"type": "string", "description": "Prior hypothesis (if any)"},
            },
            "required": ["topic"],
        },
    },
    {
        "name": "hub_shadow_status",
        "category": "hub",
        "description": "Shadow Gemini の状態/切替。enabled パラメータで ON/OFF。省略時は現状を返す。",
        "parameters": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "description": "True=有効, False=無効。省略時は現状を返す"},
            },
        },
    },
    {
        "name": "hub_stats",
        "category": "hub",
        "description": "Hub 全体の統計: 呼出ログ、Shadow 結果、バックエンド状態、Gate 統計。",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "hub_recommend",
        "category": "hub",
        "description": "タスク記述から最適な MCP バックエンドとツールを推奨する (S-006 Stage 1)。",
        "parameters": {
            "type": "object",
            "properties": {
                "task_description": {"type": "string", "description": "実行したいタスクの説明"},
                "top_k": {"type": "integer", "description": "返す推奨件数 (デフォルト: 3)"},
            },
            "required": ["task_description"],
        },
    },
    {
        "name": "hub_execute",
        "category": "hub",
        "description": "指定したバックエンドのツールを Hub 経由で実行する (S-006 Stage 2)。hub_recommend で推奨を取得後、Claude が選択したツールを実行。",
        "parameters": {
            "type": "object",
            "properties": {
                "backend": {"type": "string", "description": "バックエンド名 (例: periskope, phantazein, ochema)"},
                "tool": {"type": "string", "description": "実行するツール名 (例: periskope_research, search)"},
                "arguments": {"type": "object", "description": "ツールに渡す引数 (JSON オブジェクト)"},
            },
            "required": ["backend", "tool"],
        },
    },
    {
        "name": "sekisho_audit",
        "category": "sekisho",
        "description": "Agent の最終応答を Gemini Pro で BC 監査する関所。PASS なら監査ログを返す (応答末尾に付記すること)。BLOCK なら応答を差し止め、修正指示を返す。最終応答前に必ず1回呼ぶこと。",
        "parameters": {
            "type": "object",
            "properties": {
                "draft_response": {"type": "string", "description": "Agent の応答ドラフト (全文)"},
                "reasoning": {"type": "string", "description": "Agent の思考過程 (推論・判断のテキスト)"},
                "depth": {"type": "string", "description": "現在の深度レベル", "enum": ["L0", "L1", "L2", "L3"]},
            },
            "required": ["draft_response", "reasoning"],
        },
    },
    {
        "name": "sekisho_gate",
        "category": "sekisho",
        "description": "応答の関所ゲート。Gemini Pro で監査し、PASS なら gate_token を発行。notify_user の前に呼ぶこと。gate_token は Status File に永続化され、次回セッションで検証される。BLOCK 時は修正指示を返す。",
        "parameters": {
            "type": "object",
            "properties": {
                "draft_response": {"type": "string", "description": "Agent の応答ドラフト (全文)"},
                "reasoning": {"type": "string", "description": "Agent の思考過程"},
                "depth": {"type": "string", "enum": ["L0", "L1", "L2", "L3"]},
            },
            "required": ["draft_response", "reasoning"],
        },
    },
    {
        "name": "sekisho_history",
        "category": "sekisho",
        "description": "過去の監査結果を表示する。",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "表示件数"},
            },
        },
    },
    {
        "name": "hub_gate",
        "category": "hub",
        "description": "Gate (Sekisho) 監査。Agent の応答ドラフトを BC 違反チェック。PASS なら gate_token 発行。",
        "parameters": {
            "type": "object",
            "properties": {
                "draft_response": {"type": "string", "description": "Agent の応答ドラフト (全文)"},
                "reasoning": {"type": "string", "description": "Agent の思考過程"},
                "depth": {"type": "string", "description": "深度レベル (L0-L3)", "enum": ["L0", "L1", "L2", "L3"]},
            },
            "required": ["draft_response", "reasoning"],
        },
    },
    {
        "name": "hgk_models",
        "category": "system",
        "description": "List available LLM models from Cortex API + LS.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "hgk_sessions",
        "category": "session",
        "description": "List IDE sessions (cascade sessions) or Handoff history.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "hgk_session_read",
        "category": "session",
        "description": "Read conversation content from an IDE session.",
        "parameters": {
            "type": "object",
            "properties": {
                "cascade_id": {"type": "string", "description": "Session cascade_id"},
                "max_turns": {"type": "integer", "description": "Max turns to return (default: 10)"},
                "full": {"type": "boolean", "description": "Full retrieval up to 30000 chars (default: false)"},
            },
            "required": ["cascade_id"],
        },
    },
    {
        "name": "hgk_pks_stats",
        "category": "knowledge",
        "description": "Show PKS knowledge base statistics: doc counts per index.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "hgk_pks_health",
        "category": "system",
        "description": "Run health check on all Autophōnos stack components.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "hgk_gateway_health",
        "category": "gateway",
        "description": "Run Gateway self-diagnostic: OAuth, tokens, registered clients, uptime.",
        "parameters": {"type": "object", "properties": {}},
    },
]




# ─── Fuzzy Match ──────────────────────────────────────────────────

from .utils import fuzzy_suggest as _hgk_fuzzy_suggest


# ─── Tool Execution Dispatcher ───────────────────────────────────


class _ToolProxy:
    """@mcp.tool() が返すプロキシ — 関数への参照を保持する。"""
    __slots__ = ("name", "fn")

    def __init__(self, name: str, fn):
        self.name = name
        self.fn = fn


class _ToolCollector:
    """FastMCP を模倣する軽量レジストリ。

    `mcp` パッケージがインストールされていない環境 (Ochema 等) でも
    `register_all(collector)` を呼ぶだけで gateway_tools 内の全関数を
    名前→関数のマッピングとして取得できる。

    @mcp.tool() デコレータの呼び出しをエミュレートする:
      @mcp.tool()          # → mcp.tool() が返す decorator を呼び出す
      def some_func(): ... # → decorator(some_func) が関数を登録し返す
    """

    def __init__(self):
        self._tools: dict[str, _ToolProxy] = {}

    def tool(self, *_args, **_kwargs):
        """FastMCP.tool() の互換。返す関数は元の関数をそのまま返す。"""
        def _decorator(fn):
            proxy = _ToolProxy(name=fn.__name__, fn=fn)
            self._tools[fn.__name__] = proxy
            return fn
        return _decorator

    def get_tool(self, name: str) -> _ToolProxy | None:
        return self._tools.get(name)

    def list_tools(self) -> list[_ToolProxy]:
        return list(self._tools.values())


_tool_cache: _ToolCollector | None = None


def _get_tool_registry() -> _ToolCollector:
    """FastMCP 非依存で全 gateway_tools 関数を収集する。"""
    global _tool_cache
    if _tool_cache is None:
        from mekhane.mcp.gateway_tools import register_all
        collector = _ToolCollector()
        register_all(collector)
        _tool_cache = collector
    return _tool_cache

# PURPOSE: [L2-auto] execute_hgk_tool の関数定義
def execute_hgk_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Execute an HGK Gateway tool dynamically via FastMCP registry.

    Lazy-imports gateway functions to avoid module-level side effects.
    All gateway functions return str (Markdown).

    Returns:
        dict with 'output' (str) or 'error' (str)
    """
    import inspect
    import asyncio
    
    # C-1: Ensure .env is loaded — gateway dies with sys.exit(1) if TOKEN missing
    if not os.environ.get("HGK_GATEWAY_TOKEN"):
        try:
            from mekhane.paths import ensure_env
            ensure_env()
        except ImportError:
            pass

    try:
        registry = _get_tool_registry()
    except Exception as e:  # Intentional Catch-All (Tool Registry Init)  # noqa: BLE001
        logger.error("Failed to initialize tool registry: %s", e)
        return {"error": f"Failed to initialize tool registry: {e}"}

    # ツールの存在確認
    tool = registry.get_tool(name)

    if not tool:
        # D-2: Fuzzy match for HGK tool typos
        known_tools = [t.name for t in registry.list_tools()]
        suggestion = _hgk_fuzzy_suggest(name, known_tools)
        hint = f" Did you mean '{suggestion}'?" if suggestion else ""
        return {"error": f"Unknown HGK tool: {name}.{hint}"}

    try:
        # C-3: Validate required args against tool definitions
        tool_def = next((t for t in HGK_TOOL_DEFINITIONS if t["name"] == name), None)
        if tool_def:
            required = tool_def.get("parameters", {}).get("required", [])
            missing = [r for r in required if r not in args]
            if missing:
                return {"error": f"Missing required args for {name}: {missing}"}

        start = time.monotonic()
        
        # Filter arbitrary args that the tool doesn't expect to avoid TypeError
        sig = inspect.signature(tool.fn)
        valid_args = {k: v for k, v in args.items() if k in sig.parameters}
        
        # Execute tool
        if inspect.iscoroutinefunction(tool.fn):
            result = asyncio.run(tool.fn(**valid_args))
        else:
            result = tool.fn(**valid_args)
            
        elapsed = time.monotonic() - start

        logger.info("HGK tool %s executed in %.2fs", name, elapsed)

        # W-4: WBC alert for side-effect tools
        if name in HGK_SIDE_EFFECT_TOOLS:
            try:
                from mekhane.mcp.sympatheia_server import wbc_alert
                wbc_alert(
                    details=f"HGK tool: {name}({args})",
                    severity="low",
                    files=[],
                    source="hgk-tools",
                )
            except Exception:  # Intentional Catch-All (Tool Logging)  # noqa: BLE001
                pass  # Non-fatal

        return {"output": result}
    except Exception as e:  # Intentional Catch-All (Tool Execution Boundary)  # noqa: BLE001
        logger.error("HGK tool %s failed: %s", name, e)
        return {"error": f"HGK tool {name} failed: {e}"}


# PURPOSE: [L2-auto] is_hgk_tool の関数定義
def is_hgk_tool(name: str) -> bool:
    """Check if a tool name is an HGK Gateway tool."""
    return name.startswith("hgk_") or name.startswith("hub_") or name.startswith("sekisho_")
