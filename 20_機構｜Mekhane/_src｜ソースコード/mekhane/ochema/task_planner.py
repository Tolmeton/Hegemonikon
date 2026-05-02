# PROOF: mekhane/ochema/task_planner.py
# PURPOSE: ochema モジュールの task_planner
"""
Φ0.5-Code: Task Planner for Jules — Compound code change decomposition.

Horizontal expansion of Periskopē's Φ0.5 Task Decomposition pattern
to coding tasks. Analyzes a code change request and decomposes it into
independent sub-tasks that can be executed in parallel via Jules.

Architecture:
    Claude (analyze/decompose) → Jules (execute in parallel) → Claude (/vet review)

Design basis: @fathom analysis (2026-02-23) — Hybrid型 (LLM分割 + 依存検証)
"""


from __future__ import annotations
import logging
import time
from dataclasses import dataclass, field
from typing import Callable

from mekhane.periskope.models import ProgressEvent

# Same callback type as Periskopē engine — structural dependency
ProgressCallback = Callable[[ProgressEvent], None]

logger = logging.getLogger(__name__)


@dataclass
class CodeSubTask:
    """A sub-task decomposed from a compound code change request.

    Maps to Jules API: {prompt, repo, branch}.
    """
    prompt: str          # Focused instruction for Jules
    focus: str           # Short label (e.g., "API layer", "Tests")
    priority: int        # 1=highest, 3=lowest
    files: list[str] = field(default_factory=list)  # Expected files to touch
    depends_on: list[int] = field(default_factory=list)  # Indices of prerequisite tasks


@dataclass
class DecompositionPlan:
    """Result of decomposing a code change request."""
    original_prompt: str
    repo: str
    branch: str
    subtasks: list[CodeSubTask]
    is_compound: bool         # Whether decomposition was needed
    parallel_groups: list[list[int]] = field(default_factory=list)  # Groups of independent tasks
    reasoning: str = ""       # Why this decomposition was chosen


async def decompose_code_task(
    prompt: str,
    repo: str,
    branch: str = "main",
    max_subtasks: int = 5,
    progress_callback: ProgressCallback | None = None,
) -> DecompositionPlan:
    """Decompose a compound code change request into independent sub-tasks.

    Uses LLM to analyze whether the change request spans multiple independent
    components that can be safely parallelized via Jules batch_execute.

    Args:
        prompt: The code change request (e.g., "Add auth + logging + tests").
        repo: Repository in 'owner/repo' format.
        branch: Starting branch (default: main).
        max_subtasks: Maximum number of sub-tasks (default: 5).

    Returns:
        DecompositionPlan with subtasks and parallel execution groups.
    """
    from mekhane.periskope.cognition._llm import llm_ask

    start = time.monotonic()

    def _notify(phase: str, **detail):
        if progress_callback:
            try:
                progress_callback(ProgressEvent(
                    phase=phase,
                    detail=detail,
                    elapsed=round(time.monotonic() - start, 1),
                ))
            except (OSError, ValueError) as _e:
                logger.debug("Ignored exception: %s", _e)

    _notify("decompose_start", prompt=prompt[:80], repo=repo)

    analysis_prompt = (
        "You are a code change decomposition agent. Your job is to split a "
        "compound code change request into focused sub-tasks for parallel "
        "execution by independent AI coding agents.\n\n"
        f"Repository: {repo}\n"
        f"Branch: {branch}\n"
        f"Change request: {prompt}\n\n"
        "## Step 1: Classify\n"
        "Determine if this is SIMPLE or COMPOUND:\n"
        "- SIMPLE: Single concern, 1-2 files, one logical unit of work\n"
        "  Example: 'Fix the login button color' → SIMPLE\n"
        "- COMPOUND: Multiple concerns joined by 'and', 'plus', commas, or "
        "covering different layers (API, UI, tests, config, docs)\n"
        "  Example: 'Add auth middleware and logging' → COMPOUND (2 concerns)\n"
        "  Example: 'Refactor the database model' → SIMPLE (1 concern)\n\n"
        "If SIMPLE, respond with exactly: SIMPLE\n\n"
        "## Step 2: Decompose (only if COMPOUND)\n"
        f"Split into up to {max_subtasks} focused sub-tasks.\n"
        "Each sub-task should target ONE concern, with minimal file overlap.\n"
        "Tasks CAN have dependencies (e.g., tests depend on implementation).\n\n"
        "Output one line per sub-task in this exact format:\n"
        "PRIORITY|FOCUS|FILES|DEPENDS_ON|PROMPT\n\n"
        "Fields:\n"
        "- PRIORITY: 1 (critical), 2 (normal), 3 (low)\n"
        "- FOCUS: 2-5 word label for this concern\n"
        "- FILES: expected files to modify (comma-separated)\n"
        "- DEPENDS_ON: indices of prerequisite tasks (0-based), or NONE\n"
        "- PROMPT: Clear, focused instruction for ONE coding agent\n\n"
        "## Examples\n\n"
        "Input: 'Add JWT auth, structured logging, and tests for both'\n"
        "Output:\n"
        "1|JWT auth middleware|src/middleware/auth.py,src/config.py|NONE|"
        "Implement JWT authentication middleware with token validation and refresh\n"
        "1|Structured logging|src/utils/logger.py,src/config.py|NONE|"
        "Add structured JSON logging with request correlation IDs\n"
        "2|Auth tests|tests/test_auth.py|0|"
        "Write comprehensive unit tests for JWT auth middleware\n"
        "2|Logging tests|tests/test_logger.py|1|"
        "Write unit tests for structured logging including JSON format validation\n\n"
        "Input: 'Update the README'\n"
        "Output:\n"
        "SIMPLE\n\n"
        "Input: 'Add rate limiting to API endpoints and update docs'\n"
        "Output:\n"
        "1|Rate limiting|src/middleware/rate_limit.py,src/config.py|NONE|"
        "Implement token bucket rate limiting for all API endpoints\n"
        "2|API docs update|docs/api.md,README.md|0|"
        "Update API documentation to reflect new rate limiting headers and limits\n\n"
        "Respond with SIMPLE or the decomposition lines. Nothing else."
    )


    text = await llm_ask(analysis_prompt, model="gemini-3.1-pro-preview", max_tokens=1024)
    _notify("decompose_llm_done", response_len=len(text or ""))

    if not text or "SIMPLE" in text.strip().upper():
        logger.info("Φ0.5-Code: Task is simple — no decomposition needed")
        _notify("decompose_done", result="simple")
        return DecompositionPlan(
            original_prompt=prompt,
            repo=repo,
            branch=branch,
            subtasks=[],
            is_compound=False,
            reasoning="Single-component change, no decomposition needed.",
        )

    subtasks = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or "|" not in line:
            continue
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        try:
            priority = int(parts[0].strip())
        except ValueError:
            priority = 2

        focus = parts[1].strip()
        files = [f.strip() for f in parts[2].strip().split(",") if f.strip()]
        depends_raw = parts[3].strip()
        depends = []
        if depends_raw.upper() != "NONE" and depends_raw:
            for d in depends_raw.split(","):
                try:
                    depends.append(int(d.strip()))
                except ValueError:
                    pass
        sub_prompt = parts[4].strip()

        if sub_prompt:
            subtasks.append(CodeSubTask(
                prompt=sub_prompt,
                focus=focus,
                priority=min(max(priority, 1), 3),
                files=files,
                depends_on=depends,
            ))

    subtasks = subtasks[:max_subtasks]
    subtasks.sort(key=lambda s: s.priority)

    # Build parallel execution groups (topological ordering by dependencies)
    parallel_groups = _build_parallel_groups(subtasks)

    if subtasks:
        logger.info(
            "Φ0.5-Code: Decomposed into %d subtasks: %s",
            len(subtasks),
            [f"{s.focus}: {s.prompt[:50]}" for s in subtasks],
        )

    _notify("decompose_done", result="compound",
            subtask_count=len(subtasks), wave_count=len(parallel_groups))

    return DecompositionPlan(
        original_prompt=prompt,
        repo=repo,
        branch=branch,
        subtasks=subtasks,
        is_compound=True,
        parallel_groups=parallel_groups,
        reasoning=f"Decomposed into {len(subtasks)} independent sub-tasks "
                  f"in {len(parallel_groups)} execution waves.",
    )


def _build_parallel_groups(subtasks: list[CodeSubTask]) -> list[list[int]]:
    """Build parallel execution groups respecting dependencies.

    Tasks with no dependencies (or all dependencies satisfied) can run
    in parallel. Returns groups ordered by execution wave.

    Example: [{0, 2}, {1, 3}] means tasks 0&2 run first, then 1&3.
    """
    if not subtasks:
        return []

    n = len(subtasks)
    remaining = set(range(n))
    completed = set()
    groups = []

    while remaining:
        # Find tasks whose dependencies are all satisfied
        ready = [
            i for i in remaining
            if all(d in completed for d in subtasks[i].depends_on)
        ]
        if not ready:
            # Circular dependency or invalid reference — force remaining
            logger.warning("Φ0.5-Code: Circular dependency detected, forcing remaining tasks")
            groups.append(list(remaining))
            break
        groups.append(ready)
        completed.update(ready)
        remaining -= set(ready)

    return groups


def format_batch_tasks(
    plan: DecompositionPlan,
    group_index: int = 0,
) -> list[dict]:
    """Convert a parallel group into Jules batch_execute format.

    Args:
        plan: The decomposition plan.
        group_index: Which parallel group to execute (0-indexed).

    Returns:
        List of {prompt, repo, branch} dicts for jules_batch_execute.
    """
    if group_index >= len(plan.parallel_groups):
        return []

    group = plan.parallel_groups[group_index]
    tasks = []
    for idx in group:
        st = plan.subtasks[idx]
        # Enrich the prompt with file hints
        file_hint = ""
        if st.files:
            file_hint = f"\n\nExpected files to modify: {', '.join(st.files)}"
        tasks.append({
            "prompt": f"[{st.focus}] {st.prompt}{file_hint}",
            "repo": plan.repo,
            "branch": plan.branch,
        })
    return tasks


def format_plan_summary(plan: DecompositionPlan) -> str:
    """Format a human-readable summary of the decomposition plan."""
    if not plan.is_compound:
        return (
            f"📋 **Simple task** — no decomposition needed\n"
            f"→ Execute directly: `{plan.original_prompt[:80]}`"
        )

    lines = [
        f"📋 **Task Decomposition Plan** ({len(plan.subtasks)} sub-tasks, "
        f"{len(plan.parallel_groups)} execution waves)",
        f"📦 Repo: `{plan.repo}` (branch: `{plan.branch}`)",
        f"💬 Original: {plan.original_prompt[:100]}",
        "",
    ]

    for wave_idx, group in enumerate(plan.parallel_groups):
        lines.append(f"### Wave {wave_idx + 1} (parallel)")
        for idx in group:
            st = plan.subtasks[idx]
            deps = f" ← depends on [{', '.join(str(d) for d in st.depends_on)}]" if st.depends_on else ""
            files = f" ({', '.join(st.files)})" if st.files else ""
            lines.append(
                f"  {idx}. **[P{st.priority}] {st.focus}**{files}{deps}\n"
                f"     {st.prompt[:120]}"
            )
        lines.append("")

    lines.append(f"🧠 {plan.reasoning}")
    return "\n".join(lines)
