from __future__ import annotations
# PROOF: mekhane/periskope/cognition/phi0_task_decompose.py
# PURPOSE: periskope モジュールの phi0_task_decompose
"""
Φ0.5 Task Decomposition Agent — Compound query splitting.

Analyzes a research query to determine if it's compound (e.g., "Compare X and Y",
"Analyze A, B, and C"), and if so, decomposes it into independent sub-queries
that can be researched separately and then synthesized.

Enhancement v2.0: Perplexity Deep Research-inspired agent planning.
"""


import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SubTask:
    """A sub-research task decomposed from a compound query."""
    query: str
    focus: str  # What this subtask specifically investigates
    priority: int  # 1=highest, 3=lowest


async def decompose_query(
    query: str,
    max_subtasks: int = 3,
) -> list[SubTask]:
    """Φ0.5: Decompose a compound query into independent sub-tasks.

    Uses LLM to analyze whether the query contains multiple distinct
    research objectives that should be investigated independently.

    Simple queries (single topic, single question) return an empty list,
    indicating no decomposition is needed.

    Args:
        query: The research query to analyze.
        max_subtasks: Maximum number of sub-tasks to generate (default 3).

    Returns:
        List of SubTask objects, or empty list if query is simple.
    """
    from mekhane.periskope.cognition._llm import llm_ask

    prompt = (
        "You are a research planning agent. Analyze this query and determine "
        "if it contains MULTIPLE DISTINCT research objectives that should be "
        "investigated independently.\n\n"
        f"Query: {query}\n\n"
        "Rules:\n"
        "- If the query is SIMPLE (single topic, single question), respond: SIMPLE\n"
        "- If the query is COMPOUND (comparison, multi-aspect, multi-entity), "
        f"decompose into {max_subtasks} or fewer focused sub-queries.\n\n"
        "For compound queries, respond with one sub-query per line in this format:\n"
        "PRIORITY|FOCUS|QUERY\n"
        "where PRIORITY is 1-3 (1=most important), FOCUS is a 2-5 word label, "
        "and QUERY is the focused research question.\n\n"
        "Examples of compound queries:\n"
        "- 'Compare React and Vue for enterprise apps' → COMPOUND\n"
        "- 'Analyze the market, technology, and regulatory aspects of EVs' → COMPOUND\n"
        "- 'What is the free energy principle?' → SIMPLE\n\n"
        "Respond ONLY with SIMPLE or the decomposition lines."
    )

    text = await llm_ask(prompt, model="gemini-3.1-pro-preview", max_tokens=512)

    if not text or "SIMPLE" in text.strip().upper():
        logger.info("Φ0.5: Query is simple — no decomposition needed")
        return []

    subtasks = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or "|" not in line:
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        try:
            priority = int(parts[0].strip())
        except ValueError:
            priority = 2
        focus = parts[1].strip()
        sub_query = parts[2].strip()
        if sub_query:
            subtasks.append(SubTask(
                query=sub_query,
                focus=focus,
                priority=min(max(priority, 1), 3),
            ))

    subtasks = subtasks[:max_subtasks]
    subtasks.sort(key=lambda s: s.priority)

    if subtasks:
        logger.info(
            "Φ0.5: Decomposed into %d subtasks: %s",
            len(subtasks),
            [f"{s.focus}: {s.query[:50]}" for s in subtasks],
        )

    return subtasks


async def synthesize_subtask_results(
    original_query: str,
    subtask_reports: list[tuple[SubTask, object]],
) -> str:
    """Synthesize results from multiple sub-task research reports into a unified answer.

    Args:
        original_query: The original compound query.
        subtask_reports: List of (SubTask, ResearchReport) tuples.

    Returns:
        Unified synthesis text combining all sub-task findings.
    """
    from mekhane.periskope.cognition._llm import llm_ask

    # Build context from each subtask's synthesis
    context_parts = []
    for subtask, report in subtask_reports:
        synth_text = ""
        if hasattr(report, 'synthesis') and report.synthesis:
            synth_text = report.synthesis[0].content[:3000]
        context_parts.append(
            f"## Sub-research: {subtask.focus}\n"
            f"Query: {subtask.query}\n"
            f"Findings:\n{synth_text}\n"
        )

    context = "\n---\n".join(context_parts)

    prompt = (
        "You are a research synthesis expert. Combine the following sub-research "
        "findings into a unified, coherent answer to the original question.\n\n"
        f"Original question: {original_query}\n\n"
        f"Sub-research results:\n{context}\n\n"
        "Provide a comprehensive synthesis that:\n"
        "1. Addresses the original question directly\n"
        "2. Integrates findings across all sub-researches\n"
        "3. Highlights areas of agreement and disagreement\n"
        "4. Notes any gaps that remain\n"
    )

    text = await llm_ask(prompt, model="gemini-3.1-pro-preview", max_tokens=4096)
    return text or ""
