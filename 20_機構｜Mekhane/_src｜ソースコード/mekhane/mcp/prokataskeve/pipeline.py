from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/prokataskeve/pipeline.py
"""
PreprocessPipeline — Depth-aware composition of all 18 functions.

PURPOSE: Compose the 8 modules into a single pipeline that executes
functions based on the requested depth level (L0-L4).

Depth  Functions  Latency   Method
─────  ─────────  ────────  ──────────────────────
L0     3          <50ms     Rule-based only
L1     6          <300ms    + Gemini Flash
L2     12         <1s       + Standard LLM + Mneme
L3     16         <3s       + Heavy LLM + consistency check
L4     18         <5s       + Speculative execution
"""

import asyncio
import logging
import time
from typing import Any

from mekhane.mcp.prokataskeve.models import Depth, PreprocessResult

logger = logging.getLogger(__name__)


# PURPOSE: PreprocessPipeline — depth-aware composition of 8 modules
class PreprocessPipeline:
    """Depth-aware pre-processing pipeline.

    Applies functions based on the depth level:
      L0: normalize + extract_entities + extract_certain
      L1: + classify_intent + resolve_references + rewrite_query
      L2: + extract_goal + match_template + diversify_query
          + detect_ambiguity + integrate_context + inject_few_shot
      L3: + recall_past + detect_contradiction + suggest_fix + generate_hyde
      L4: + predict_next + prefetch
    """

    # PURPOSE: Execute the pipeline at the given depth
    async def run(
        self,
        text: str,
        depth: str | Depth = Depth.L1,
        session_state: dict[str, Any] | None = None,
    ) -> PreprocessResult:
        """Run the pre-processing pipeline.

        Args:
            text: Raw input text.
            depth: Processing depth (L0-L4).
            session_state: Optional session context for reference resolution.

        Returns:
            PreprocessResult with all extracted information.
        """
        if isinstance(depth, str):
            try:
                depth = Depth(depth)
            except ValueError:
                depth = Depth.L1

        t0 = time.monotonic()
        result = PreprocessResult(original_text=text, depth=depth)

        # =================================================================
        # L0: Rule-based (<50ms)
        # =================================================================
        from mekhane.mcp.prokataskeve.input_analyzer import (
            extract_certain,
            extract_entities,
            normalize,
        )

        result.normalized_text = normalize(text)
        result.functions_executed.append("normalize")

        result.entities = extract_entities(result.normalized_text)
        result.functions_executed.append("extract_entities")

        result.certain_spans = extract_certain(result.normalized_text, result.entities)
        result.functions_executed.append("extract_certain")

        if depth == Depth.L0:
            result.latency_ms = (time.monotonic() - t0) * 1000
            return result

        # =================================================================
        # L1: + LLM (<300ms)
        # =================================================================
        from mekhane.mcp.prokataskeve.context_resolver import resolve_references
        from mekhane.mcp.prokataskeve.intent_classifier import classify_intent
        from mekhane.mcp.prokataskeve.query_transformer import rewrite_query

        result.intent = await classify_intent(result.normalized_text, result.entities)
        result.functions_executed.append("classify_intent")

        result.resolved_refs = resolve_references(
            result.normalized_text, session_state,
        )
        result.functions_executed.append("resolve_references")

        result.rewritten_queries = await rewrite_query(
            result.normalized_text, result.intent, result.entities,
        )
        result.functions_executed.append("rewrite_query")

        if depth == Depth.L1:
            result.latency_ms = (time.monotonic() - t0) * 1000
            return result

        # =================================================================
        # L2: + Standard LLM + Mneme (<1s)
        # Independent functions run in parallel via asyncio.gather
        # =================================================================
        from mekhane.mcp.prokataskeve.context_resolver import integrate_context
        from mekhane.mcp.prokataskeve.input_analyzer import detect_ambiguity
        from mekhane.mcp.prokataskeve.intent_classifier import (
            extract_goal,
            match_template,
        )
        from mekhane.mcp.prokataskeve.pattern_injector import inject_few_shot
        from mekhane.mcp.prokataskeve.query_transformer import diversify_query
        from mekhane.mcp.prokataskeve.structurizer import structurize

        # Sync functions first
        result.template_match = match_template(result.normalized_text, result.intent)
        result.functions_executed.append("match_template")

        result.ambiguities = detect_ambiguity(
            result.normalized_text, result.entities, result.resolved_refs,
        )
        result.functions_executed.append("detect_ambiguity")

        # Async functions in parallel (structurize を追加)
        goal_task = extract_goal(result.normalized_text, result.intent)
        diversify_task = diversify_query(result.normalized_text, result.rewritten_queries)
        context_task = integrate_context(
            result.normalized_text, session_state, result.resolved_refs,
        )
        few_shot_task = inject_few_shot(result.normalized_text, result.intent)
        structure_task = structurize(
            result.normalized_text, result.intent, result.entities,
        )

        (
            result.goal,
            result.diversified_queries,
            result.context_summary,
            result.few_shot_examples,
            result.structure,
        ) = await asyncio.gather(
            goal_task, diversify_task, context_task, few_shot_task,
            structure_task,
        )
        result.functions_executed.extend([
            "extract_goal", "diversify_query", "integrate_context",
            "inject_few_shot", "structurize",
        ])

        if depth == Depth.L2:
            result.latency_ms = (time.monotonic() - t0) * 1000
            return result

        # =================================================================
        # L3: + Heavy LLM + consistency check (<3s)
        # =================================================================
        from mekhane.mcp.prokataskeve.consistency_checker import (
            detect_contradiction,
            suggest_fix,
        )
        from mekhane.mcp.prokataskeve.context_resolver import recall_past
        from mekhane.mcp.prokataskeve.hypothesis_generator import generate_hyde

        # Async in parallel
        recall_task = recall_past(result.normalized_text, result.intent)
        contradiction_task = detect_contradiction(
            result.normalized_text, result.context_summary,
        )
        hyde_task = generate_hyde(result.normalized_text, result.intent)

        (
            result.past_results,
            result.contradictions,
            result.hyde_query,
        ) = await asyncio.gather(recall_task, contradiction_task, hyde_task)
        result.functions_executed.extend([
            "recall_past", "detect_contradiction", "generate_hyde",
        ])

        # suggest_fix depends on contradictions + ambiguities (sync)
        result.fix_suggestions = suggest_fix(
            result.contradictions, result.ambiguities,
        )
        result.functions_executed.append("suggest_fix")

        if depth == Depth.L3:
            result.latency_ms = (time.monotonic() - t0) * 1000
            return result

        # =================================================================
        # L4: + Speculative execution (<5s)
        # =================================================================
        from mekhane.mcp.prokataskeve.predictor import predict_next, prefetch

        result.predictions = await predict_next(
            result.normalized_text, result.intent, result.context_summary,
        )
        result.functions_executed.append("predict_next")

        result.prefetched = await prefetch(result.predictions)
        result.functions_executed.append("prefetch")

        result.latency_ms = (time.monotonic() - t0) * 1000
        return result
