from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- hgk/api/ A0→F6 複数AI組織 (認知コロニー)
# PURPOSE: COO (Opus 4.6) がタスクを分解し、専門 Worker に委任するオーケストレーター
"""
Colony — F6 AI Organization (Cognitive Colony)

Architecture:
    Creator (CEO)
      └─ COO (Claude Opus 4.6 — 判断・分解・統合, 最大性能)
           ├─ Engineer (Gemini 3 Pro — HGK Tools で高速実行)
           ├─ Researcher (Periskopē — 調査・分析)
           └─ Intern Pool (Jules × N — 並列コーディング)

Flow:
    1. COO decomposes user message into SubTasks
    2. Independent SubTasks run in parallel on Workers
    3. Dependent SubTasks wait for prerequisites
    4. COO synthesizes all Worker results into final answer
"""


import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Feature flag: enable Vertex AI backend for Colony COO + Workers
# Set COLONY_USE_VERTEX=true to route through Vertex AI (GCP credits)
# Default: false (existing LS/Cortex behavior preserved)
COLONY_USE_VERTEX = os.environ.get("COLONY_USE_VERTEX", "").lower() in ("true", "1", "yes")


# ─── Data Types ──────────────────────────────────────────────────

class WorkerType(str, Enum):
    """Available worker types in the Colony."""
    ENGINEER = "engineer"       # Gemini 3 Pro + HGK Tools
    RESEARCHER = "researcher"   # Periskopē Deep Research
    JULES = "jules"             # Jules async coding
    CCL = "ccl"                 # Hermēneus CCL dispatch
    COO_DIRECT = "coo_direct"   # COO handles directly (simple tasks)


@dataclass
class SubTask:
    """A decomposed unit of work for a Worker."""
    id: str
    description: str
    worker_type: WorkerType
    priority: int = 1              # Higher = execute first
    depends_on: list[str] = field(default_factory=list)
    context: str = ""              # Additional context from COO


@dataclass
class WorkerResult:
    """Result from a Worker execution."""
    task_id: str
    worker_type: WorkerType
    output: str
    model: str = ""
    duration_ms: int = 0
    success: bool = True
    error: str = ""


@dataclass
class ColonyResult:
    """Final Colony execution result."""
    synthesis: str                 # COO's synthesized answer
    subtasks: list[SubTask] = field(default_factory=list)
    results: list[WorkerResult] = field(default_factory=list)
    coo_model: str = ""
    total_duration_ms: int = 0
    thinking: str = ""             # COO's thinking process


# ─── COO Configuration ──────────────────────────────────────────

# Opus 4.6 — Maximum performance, no compromise
COO_MODEL = "MODEL_PLACEHOLDER_M26"
COO_THINKING_BUDGET = 32768  # Maximum thinking depth
COO_TIER = "g1-ultra-tier"
COO_FALLBACK_MODEL = "gemini-3.1-pro-preview"  # When LS unavailable

# Engineer
ENGINEER_MODEL = "gemini-3-pro-preview"
ENGINEER_THINKING_BUDGET = 32768

# ─── Prompt Loading ─────────────────────────────────────────────

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str, fallback: str = "") -> str:
    """Load prompt from .prompt file. Falls back to inline string."""
    path = _PROMPTS_DIR / f"{name}.prompt"
    if path.exists():
        # Read raw content, skip YAML frontmatter
        text = path.read_text(encoding="utf-8")
        if text.startswith("---"):
            # Strip frontmatter between --- markers
            parts = text.split("---", 2)
            if len(parts) >= 3:
                text = parts[2].strip()
        return text
    logger.warning("Prompt file not found: %s, using fallback", path)
    return fallback


# System prompts (loaded from .prompt files)
COO_DECOMPOSE_PROMPT = _load_prompt("coo_decompose", fallback="""\
あなたは Hegemonikón の COO (最高執行責任者) である。Claude Opus 4.6 として最大の知性で判断せよ。

あなたの役割:
1. Creator のリクエストを分析し、最適なサブタスクに分解する
2. 各サブタスクを最適な Worker に割り当てる
3. 依存関係を正しく設定する

出力形式 (厳密に JSON で出力せよ):
```json
{
  "analysis": "リクエストの分析 (1-2文)",
  "subtasks": [
    {
      "id": "t1",
      "description": "タスクの具体的な説明",
      "worker_type": "engineer|researcher|jules|coo_direct",
      "priority": 1,
      "depends_on": [],
      "context": "Worker に伝える追加コンテキスト"
    }
  ]
}
```
""")

COO_SYNTHESIZE_PROMPT = _load_prompt("coo_synthesize", fallback="""\
あなたは Hegemonikón の COO (最高執行責任者) である。

Worker たちの実行結果を統合し、Creator への最終報告を作成せよ。

ルール:
- 全 Worker の結果を踏まえた統合的な回答を書け
- 矛盾がある場合は指摘せよ
- Creator が行動できるレベルの具体性で書け (N-11)
""")



# ─── Colony Orchestrator ─────────────────────────────────────────

class Colony:
    """F6 AI Organization — COO delegates to specialized Workers.

    Usage:
        colony = Colony()
        result = await colony.execute("hgk_tools.py をレビューして改善点をまとめて")

        # Vertex AI mode (GCP credits, 1M context for COO):
        colony = Colony(vertex_mode=True)
    """

    def __init__(
        self,
        on_event: Optional[Callable] = None,
        on_gate: Optional[Callable] = None,
        svc=None,
        vertex_mode: Optional[bool] = None,
    ):
        """Initialize Colony.

        Args:
            on_event: Callback for SSE events. Called with (event_type, data_dict).
            on_gate: Safety Gate callback. Called with (tool_name, args) -> bool.
                     If None, all tool calls are auto-approved.
            svc: Optional OchemaService instance (for testing).
            vertex_mode: Enable Vertex AI backend for COO. If None, reads
                         COLONY_USE_VERTEX env var. Default: False.
        """
        self.on_event = on_event or (lambda t, d: None)
        self.on_gate = on_gate
        self._svc = svc
        self._vertex_mode = vertex_mode if vertex_mode is not None else COLONY_USE_VERTEX
        self._vertex_claude = None  # Lazy-initialized

    @property
    def svc(self):
        """Lazy-load OchemaService to avoid import-time side effects."""
        if self._svc is None:
            from mekhane.ochema.service import OchemaService
            self._svc = OchemaService.get()
        return self._svc

    @property
    def vertex_claude(self):
        """Lazy-load VertexClaudeClient (only when vertex_mode=True)."""
        if self._vertex_claude is None and self._vertex_mode:
            try:
                from mekhane.ochema.vertex_claude import VertexClaudeClient
                self._vertex_claude = VertexClaudeClient()
                logger.info(
                    "Colony: VertexClaudeClient initialized (%d accounts, budget=$%.0f)",
                    len(self._vertex_claude.accounts),
                    self._vertex_claude.costs.budget_usd,
                )
            except Exception as e:  # noqa: BLE001
                logger.warning("Colony: VertexClaudeClient init failed: %s", e)
                self._vertex_mode = False  # Disable for this session
        return self._vertex_claude

    async def execute(self, message: str) -> ColonyResult:
        """Execute the Colony pipeline.

        Phase 1: COO decomposes message into SubTasks
        Phase 2: Workers execute SubTasks (parallel where possible)
        Phase 3: COO synthesizes Worker results
        """
        start = time.monotonic()

        # Phase 1: Decompose
        self.on_event("phase", {"phase": "decompose", "status": "starting"})
        subtasks = await self._decompose(message)
        self.on_event("decompose", {
            "subtasks": [
                {"id": st.id, "description": st.description,
                 "worker_type": st.worker_type.value, "priority": st.priority}
                for st in subtasks
            ]
        })

        # Phase 2: Dispatch workers
        self.on_event("phase", {"phase": "dispatch", "status": "starting"})
        results = await self._dispatch(subtasks)

        # Phase 3: Synthesize
        self.on_event("phase", {"phase": "synthesize", "status": "starting"})
        synthesis, thinking = await self._synthesize(message, subtasks, results)

        total_ms = int((time.monotonic() - start) * 1000)

        return ColonyResult(
            synthesis=synthesis,
            subtasks=subtasks,
            results=results,
            coo_model=COO_MODEL,
            total_duration_ms=total_ms,
            thinking=thinking,
        )

    async def _call_coo(self, prompt: str, system: str = "") -> "LLMResponse":
        """Call COO with 3-tier fallback:

        1. Vertex AI Claude (if vertex_mode=True) — 1M context, GCP credits
        2. LS Claude Opus (ConnectRPC) — 45K context, free
        3. Gemini 3 Pro (Cortex API) — fallback

        COO は常に最大性能で動作する。
        """
        from mekhane.ochema.types import LLMResponse

        full_msg = f"{system}\n\n{prompt}" if system else prompt

        # Tier 0: Vertex AI Claude (if enabled + client available)
        if self._vertex_mode and self.vertex_claude:
            try:
                vc_resp = await self.vertex_claude.ask_async(
                    message=full_msg,
                    system=system,
                    max_tokens=COO_THINKING_BUDGET,
                )
                logger.info(
                    "COO (vertex): Claude via Vertex AI, account=%s region=%s len=%d cost=$%.4f",
                    vc_resp.account, vc_resp.region, len(vc_resp.text), vc_resp.estimated_cost_usd,
                )
                return LLMResponse(
                    text=vc_resp.text,
                    model=vc_resp.model or "claude-opus-4-6",
                )
            except Exception as e:  # noqa: BLE001
                logger.warning("COO Vertex Claude failed: %s — trying LS", e)

        # Tier 1: Claude Opus via LS
        try:
            response = await asyncio.to_thread(
                self.svc.chat,
                message=full_msg,
                model=COO_MODEL,
                tier_id=COO_TIER,
                thinking_budget=COO_THINKING_BUDGET,
            )
            logger.info("COO (ls): Opus via LS, len=%d", len(response.text))
            return response
        except Exception as e:  # noqa: BLE001
            logger.warning("COO LS failed: %s — falling back to Gemini", e)

        # Tier 2: Gemini 3 Pro via Cortex
        response = await asyncio.to_thread(
            self.svc.ask,
            message=full_msg,
            model=COO_FALLBACK_MODEL,
            system_instruction=(
                "あなたは Hegemonikón COO の代理 (Gemini) として動作している。"
                "本来の COO は Claude Opus 4.6 だが、LS 不在のため代理実行。"
                "最大限の品質で回答せよ。"
            ),
            thinking_budget=COO_THINKING_BUDGET,
        )
        logger.info("COO (gemini-fallback): Gemini, len=%d", len(response.text))
        return response

    # ─── Phase 1: Decompose ─────────────────────────────────────

    async def _decompose(self, message: str) -> list[SubTask]:
        """COO analyzes the request and decomposes into SubTasks."""
        prompt = f"以下のリクエストを分析し、サブタスクに分解せよ:\n\n{message}"
        response = await self._call_coo(prompt, system=COO_DECOMPOSE_PROMPT)

        logger.info("COO decompose response model=%s len=%d",
                     response.model, len(response.text))

        return self._parse_subtasks(response.text)

    def _parse_subtasks(self, text: str) -> list[SubTask]:
        """Parse COO's JSON output into SubTask objects."""
        # Extract JSON from markdown code block if present
        json_text = text
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            json_text = text[start:end].strip()
        elif "```" in text:
            start = text.index("```") + 3
            end = text.index("```", start)
            json_text = text[start:end].strip()

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError:
            # Fallback: treat entire request as single coo_direct task
            logger.warning("Failed to parse COO decomposition, falling back to coo_direct")
            return [SubTask(
                id="t1",
                description=text[:500],
                worker_type=WorkerType.COO_DIRECT,
            )]

        subtasks = []
        for st_data in data.get("subtasks", []):
            try:
                worker = WorkerType(st_data.get("worker_type", "coo_direct"))
            except ValueError:
                worker = WorkerType.COO_DIRECT

            subtasks.append(SubTask(
                id=st_data.get("id", f"t{len(subtasks)+1}"),
                description=st_data.get("description", ""),
                worker_type=worker,
                priority=st_data.get("priority", 1),
                depends_on=st_data.get("depends_on", []),
                context=st_data.get("context", ""),
            ))

        if not subtasks:
            subtasks.append(SubTask(
                id="t1",
                description="(COO produced no subtasks — direct execution)",
                worker_type=WorkerType.COO_DIRECT,
            ))

        return subtasks

    # ─── Phase 2: Dispatch Workers ──────────────────────────────

    async def _dispatch(self, subtasks: list[SubTask]) -> list[WorkerResult]:
        """Execute SubTasks respecting dependencies. Parallel where possible."""
        completed: dict[str, WorkerResult] = {}
        pending = list(subtasks)
        results = []

        while pending:
            # Find tasks whose dependencies are all satisfied
            ready = [
                st for st in pending
                if all(dep in completed for dep in st.depends_on)
            ]

            if not ready:
                logger.error("Deadlock: no ready tasks but %d pending", len(pending))
                for st in pending:
                    results.append(WorkerResult(
                        task_id=st.id,
                        worker_type=st.worker_type,
                        output="",
                        success=False,
                        error="Dependency deadlock",
                    ))
                break

            # Execute ready tasks in parallel
            coros = []
            for st in ready:
                # Build context from dependent results
                dep_context = ""
                for dep_id in st.depends_on:
                    if dep_id in completed:
                        dep_context += f"\n\n--- Result from {dep_id} ---\n{completed[dep_id].output[:2000]}"

                coros.append(self._execute_worker(st, dep_context))

            batch_results = await asyncio.gather(*coros, return_exceptions=True)

            for st, result in zip(ready, batch_results):
                if isinstance(result, Exception):
                    wr = WorkerResult(
                        task_id=st.id,
                        worker_type=st.worker_type,
                        output="",
                        success=False,
                        error=str(result),
                    )
                else:
                    wr = result

                completed[st.id] = wr
                results.append(wr)
                pending.remove(st)

                self.on_event("worker_done", {
                    "task_id": wr.task_id,
                    "worker_type": wr.worker_type.value,
                    "success": wr.success,
                    "duration_ms": wr.duration_ms,
                    "output_preview": wr.output[:200] if wr.output else wr.error[:200],
                })

        return results

    async def _execute_worker(self, task: SubTask, dep_context: str) -> WorkerResult:
        """Execute a single SubTask on the appropriate Worker."""
        start = time.monotonic()
        self.on_event("worker_start", {
            "task_id": task.id,
            "worker_type": task.worker_type.value,
            "description": task.description[:100],
        })

        full_prompt = task.description
        if task.context:
            full_prompt += f"\n\nAdditional context: {task.context}"
        if dep_context:
            full_prompt += f"\n\nPrevious results:{dep_context}"

        try:
            if task.worker_type == WorkerType.ENGINEER:
                output, model = await self._run_engineer(full_prompt)
            elif task.worker_type == WorkerType.RESEARCHER:
                output, model = await self._run_researcher(full_prompt)
            elif task.worker_type == WorkerType.JULES:
                output, model = await self._run_jules(full_prompt)
            elif task.worker_type == WorkerType.CCL:
                output, model = await self._run_ccl(task.context or full_prompt)
            elif task.worker_type == WorkerType.COO_DIRECT:
                output, model = await self._run_coo_direct(full_prompt)
            else:
                raise ValueError(f"Unknown worker type: {task.worker_type}")

            duration_ms = int((time.monotonic() - start) * 1000)
            return WorkerResult(
                task_id=task.id,
                worker_type=task.worker_type,
                output=output,
                model=model,
                duration_ms=duration_ms,
                success=True,
            )
        except Exception as e:  # noqa: BLE001
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.error("Worker %s failed for task %s: %s",
                        task.worker_type.value, task.id, e)
            return WorkerResult(
                task_id=task.id,
                worker_type=task.worker_type,
                output="",
                duration_ms=duration_ms,
                success=False,
                error=str(e),
            )

    # ─── Worker Implementations ─────────────────────────────────

    async def _run_engineer(self, prompt: str) -> tuple[str, str]:
        """Engineer Worker — Gemini 3 Pro with HGK Tools.

        vertex_mode=True: CortexClient direct (GCP credits, higher throughput)
        vertex_mode=False: OchemaService via LS (free tier)
        """
        from mekhane.ochema.tools import TOOL_DEFINITIONS, HGK_SYSTEM_TEMPLATES
        from mekhane.ochema.hgk_tools import HGK_TOOL_DEFINITIONS

        all_tools = TOOL_DEFINITIONS + HGK_TOOL_DEFINITIONS
        system_instruction = HGK_SYSTEM_TEMPLATES.get("hgk_citizen", "")

        # Vertex Gemini path: CortexClient direct (bypasses LS)
        if self._vertex_mode:
            try:
                from mekhane.ochema.cortex_client import CortexClient
                client = CortexClient()
                response = await asyncio.to_thread(
                    client.ask_with_tools,
                    message=prompt,
                    model=ENGINEER_MODEL,
                    system_instruction=system_instruction,
                    tools=all_tools,
                    max_iterations=10,
                    thinking_budget=ENGINEER_THINKING_BUDGET,
                    on_gate=self.on_gate,
                )
                logger.info("Engineer (vertex): CortexClient direct, len=%d", len(response.text))
                return response.text, response.model or ENGINEER_MODEL
            except Exception as e:  # noqa: BLE001
                logger.warning("Engineer Vertex path failed: %s — using OchemaService", e)

        # Standard path: OchemaService (LS-proxied)
        kwargs: dict = dict(
            message=prompt,
            model=ENGINEER_MODEL,
            system_instruction=system_instruction,
            tools=all_tools,
            max_iterations=10,
            thinking_budget=ENGINEER_THINKING_BUDGET,
        )
        if self.on_gate:
            kwargs["on_gate"] = self.on_gate

        response = await asyncio.to_thread(
            self.svc.ask_with_tools,
            **kwargs,
        )
        return response.text, response.model or ENGINEER_MODEL

    async def _run_researcher(self, prompt: str) -> tuple[str, str]:
        """Researcher Worker — Periskopē Deep Research."""
        from mekhane.periskope.engine import PeriskopeEngine

        engine = PeriskopeEngine()
        report = await asyncio.to_thread(
            engine.research,
            query=prompt,
            depth=2,
            max_results=10,
        )
        output = report.executive_summary or report.synthesis or "(No results)"
        return output, "periskope"

    async def _run_jules(self, prompt: str) -> tuple[str, str]:
        """Jules Worker — Async coding tasks."""
        from hgk.api.jules_client import get_jules_client

        client = get_jules_client()
        if not client.available:
            return "(Jules API not available — no API keys configured)", "jules"

        # List available sources
        sources = await asyncio.to_thread(client.list_sources)
        if not sources:
            return "(Jules: no repositories available)", "jules"

        # Use first source as default
        source_id = sources[0].get("name", "")
        session = await asyncio.to_thread(
            client.create_session,
            prompt=prompt,
            source=source_id,
            title=f"Colony task {uuid.uuid4().hex[:6]}",
        )

        session_id = session.get("name", "").split("/")[-1] if session.get("name") else ""
        return (
            f"Jules session created: {session_id}\n"
            f"Source: {source_id}\n"
            f"Status: {session.get('state', 'unknown')}\n"
            f"Note: Jules tasks are async. Monitor via /api/jules/sessions/{session_id}"
        ), "jules"

    async def _run_ccl(self, ccl_expr: str) -> tuple[str, str]:
        """CCL Worker — Hermēneus CCL dispatch and execute.

        Parses and executes a CCL expression via the Hermēneus engine.
        Falls back to dispatch-only (AST + plan) if execution is not available.
        """
        try:
            from hermeneus.src.executor import execute_ccl
            result = await asyncio.to_thread(execute_ccl, ccl_expr)
            output = result.get("output", "") or str(result)
            return output, "hermeneus"
        except ImportError:
            logger.info("CCL execute unavailable, falling back to dispatch")
        except Exception as e:  # noqa: BLE001
            logger.warning("CCL execute failed: %s — falling back to dispatch", e)

        # Fallback: dispatch-only (parse + plan)
        try:
            from hermeneus.src.parser import parse as ccl_parse
            ast = ccl_parse(ccl_expr)
            return f"CCL AST:\n{ast}\n\nExpression: {ccl_expr}", "hermeneus"
        except Exception as e:  # noqa: BLE001
            return f"CCL dispatch failed: {e}\nExpression: {ccl_expr}", "hermeneus"

    async def _run_coo_direct(self, prompt: str) -> tuple[str, str]:
        """COO handles directly — for simple analysis/questions."""
        response = await self._call_coo(prompt)
        return response.text, response.model or COO_MODEL

    # ─── Phase 3: Synthesize ────────────────────────────────────

    async def _synthesize(
        self, original_message: str,
        subtasks: list[SubTask],
        results: list[WorkerResult],
    ) -> tuple[str, str]:
        """COO synthesizes Worker results into final answer.

        Returns:
            (synthesis_text, thinking_text)
        """
        # If only one coo_direct task, return it directly (no need to re-synthesize)
        if (
            len(results) == 1
            and results[0].worker_type == WorkerType.COO_DIRECT
            and results[0].success
        ):
            return results[0].output, ""

        # Build worker results summary for COO
        results_summary = []
        for st, wr in zip(subtasks, results):
            status = "✅ 成功" if wr.success else f"❌ 失敗: {wr.error}"
            results_summary.append(
                f"### SubTask: {st.id} ({wr.worker_type.value})\n"
                f"**説明**: {st.description}\n"
                f"**状態**: {status} ({wr.duration_ms}ms, model: {wr.model})\n"
                f"**出力**:\n{wr.output[:3000] if wr.output else '(empty)'}\n"
            )

        synthesis_prompt = (
            f"{COO_SYNTHESIZE_PROMPT}\n\n"
            f"## 元のリクエスト\n{original_message}\n\n"
            f"## Worker 結果\n\n{'---'.join(results_summary)}"
        )

        response = await self._call_coo(synthesis_prompt, system=COO_SYNTHESIZE_PROMPT)

        thinking = getattr(response, "thinking", "") or ""
        return response.text, thinking
