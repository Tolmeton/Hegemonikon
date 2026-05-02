from __future__ import annotations
# PROOF: mekhane/periskope/dialectic.py
# PURPOSE: periskope モジュールの dialectic
"""
Dialectic Engine — L2 Pipeline Phase Inversion for Periskopē (v2).

VISION §7: At pipeline granularity, clone Periskopē itself with
an inverted objective function and run Thesis ↔ Antithesis debate.
Both engines run in PARALLEL with full power, communicating dynamically
via a Shared Ephemeral Index.

    ┌─ Thesis Engine ──────┐                ┌── Anti Engine ────────┐
    │ research() FULL power│                │ research() FULL power │
    │ CoT iter 1 → publish │ ←── Shared ──→ │ CoT iter 1 → publish │
    │ ← read opponent ←    │    Channel     │ ← read opponent ←    │
    │ CoT iter 2 → publish │  (Ephemeral)   │ CoT iter 2 → publish │
    │ ...converge...       │    Index       │ ...converge...        │
    └──────────────────────┘                └───────────────────────┘
                             ↘     ↙
                       Dialectical Synthesis
"""


import asyncio
import logging
import time
from dataclasses import dataclass, field

from mekhane.periskope.cognition._llm import llm_ask as _llm_ask
from mekhane.periskope.cognition.ephemeral_index import EphemeralIndex
from mekhane.periskope.cognition.phase_inversion import invert_queries

logger = logging.getLogger(__name__)


# Anti-Periskopē system instruction — inverts synthesis objective
ANTI_SYSTEM_INSTRUCTION = (
    "You are conducting ADVERSARIAL research. Your goal is to find evidence "
    "that CONTRADICTS, REFUTES, or WEAKENS the provisional perspective. "
    "Do NOT confirm the initial premise — actively seek counter-evidence, "
    "alternative explanations, methodological flaws, and overlooked factors. "
    "Be rigorous and specific. Cite sources for every counter-claim."
)


@dataclass
class DialecticReport:
    """Result of a dialectical research process."""

    query: str
    synthesis_text: str = ""
    thesis_confidence: float = 0.0
    antithesis_confidence: float = 0.0
    final_confidence: float = 0.0
    elapsed_seconds: float = 0.0

    # Underlying reports (for citation/source access)
    thesis_search_results: list = field(default_factory=list)
    antithesis_search_results: list = field(default_factory=list)
    source_counts: dict = field(default_factory=dict)
    
    # Trace history (to retain visibility into iterations)
    thesis_trace: dict = field(default_factory=dict)
    antithesis_trace: dict = field(default_factory=dict)

    # Quality metrics (integrated from both engines)
    quality_metrics: object | None = None  # QualityMetrics or None
    thesis_quality: object | None = None
    antithesis_quality: object | None = None

    def markdown(self) -> str:
        """Format as markdown for final report."""
        lines = ["## Dialectical Analysis (Parallel Execute)\n"]
        
        lines.append(f"### Thesis (Confidence: {self.thesis_confidence:.0%})")
        lines.append("See trace for standalone thesis synthesis.")
        
        lines.append(f"\n### Antithesis (Confidence: {self.antithesis_confidence:.0%})")
        lines.append("See trace for standalone antithesis synthesis.")
        
        lines.append("\n### Dialectical Synthesis")
        lines.append(self.synthesis_text)
        lines.append(f"\n**Final Integrated Confidence:** {self.final_confidence:.0%}")

        # Quality metrics section
        if self.quality_metrics and hasattr(self.quality_metrics, 'markdown_section'):
            lines.append("")
            lines.append(self.quality_metrics.markdown_section())

        return "\n".join(lines)


class DialecticEngine:
    """L2 Pipeline Phase Inversion: run two PeriskopeEngines in parallel.

    Usage:
        engine = DialecticEngine()
        report = await engine.research("Is X true?", depth=2)
    """

    def __init__(
        self,
        synth_models: list | None = None,
        max_results_per_source: int = 10,
    ):
        """Initialize with two PeriskopeEngine instances and a shared index."""
        from mekhane.periskope.engine import PeriskopeEngine
        from mekhane.periskope.config_loader import load_config

        config = load_config()
        self._config = config
        self._dialectic_cfg = config.get("phase_inversion", {}).get("dialectic", {})
        
        # Shared Ephemeral Index for dynamic mutual interaction
        self.ephemeral_index = EphemeralIndex()

        # Engine definitions (symmetric, full power)
        # SearXNG URL(s) resolved from config.yaml automatically by PeriskopeEngine
        self.thesis_engine = PeriskopeEngine(
            synth_models=synth_models,
            max_results_per_source=max_results_per_source,
            shared_index=self.ephemeral_index,
            role="thesis",
            decay_type="linear",  # Gradual narrowing for constructive thesis
            alpha_schedule="linear",  # Steady structural focus
        )
        self.anti_engine = PeriskopeEngine(
            synth_models=synth_models,
            max_results_per_source=max_results_per_source,
            shared_index=self.ephemeral_index,
            role="antithesis",
            decay_type="logsnr",  # High diversity longer, finding edge cases
            alpha_schedule="sigmoid",  # Delayed convergence, maximizing critique
        )

    async def research(
        self,
        query: str,
        depth: int = 2,
        sources: list[str] | None = None,
        expand_query: bool = True,
        known_context: str = "",
        llm_rerank: bool | None = None,
        progress_callback=None,
    ) -> DialecticReport:
        """Execute parallel dialectical research."""
        start = time.monotonic()

        logger.info(
            "Dialectic research [v2 Parallel]: query=%r depth=L%d",
            query[:80], depth,
        )

        report = DialecticReport(query=query)
        self.ephemeral_index.clear()  # Reset index for this session

        # Pre-invert query for Antithesis
        try:
            anti_queries = await invert_queries(query, claims=[query])
            anti_query = anti_queries[0] if anti_queries else f"arguments against: {query}"
        except Exception as e:  # noqa: BLE001
            logger.warning("Query inversion failed, using fallback: %s", e)
            anti_query = f"arguments against: {query}"

        # Create execution tasks
        thesis_task = asyncio.create_task(
            self.thesis_engine.research(
                query=query,
                sources=sources,
                depth=depth,
                expand_query=expand_query,
                known_context=known_context,
                llm_rerank=llm_rerank,
                progress_callback=progress_callback,
            )
        )
        
        anti_task = asyncio.create_task(
            self.anti_engine.research(
                query=anti_query,
                sources=sources,
                depth=depth,
                expand_query=expand_query,
                known_context=known_context,
                llm_rerank=llm_rerank,
                system_instruction=ANTI_SYSTEM_INSTRUCTION,
                progress_callback=progress_callback,
            )
        )

        # Run both engines in parallel
        # Note: Dynamic interaction happens *inside* the engine.py CoT loop via self.ephemeral_index
        try:
            thesis_result, anti_result = await asyncio.gather(thesis_task, anti_task)
        except Exception as e:  # noqa: BLE001
            logger.error("Parallel dialectic execution failed: %s", e, exc_info=True)
            thesis_result, anti_result = None, None

        # Collect results
        if thesis_result:
            report.thesis_search_results = thesis_result.search_results
            for k, v in thesis_result.source_counts.items():
                report.source_counts[k] = report.source_counts.get(k, 0) + v
            if thesis_result.reasoning_trace:
                report.thesis_confidence = thesis_result.reasoning_trace.latest_confidence
            elif thesis_result.quality_metrics:
                # Fallback: use quality_metrics overall_score as confidence proxy
                report.thesis_confidence = thesis_result.quality_metrics.overall_score
            if thesis_result.quality_metrics:
                report.thesis_quality = thesis_result.quality_metrics
        
        if anti_result:
            report.antithesis_search_results = anti_result.search_results
            for k, v in anti_result.source_counts.items():
                report.source_counts[k] = report.source_counts.get(k, 0) + v
            if anti_result.reasoning_trace:
                report.antithesis_confidence = anti_result.reasoning_trace.latest_confidence
            elif anti_result.quality_metrics:
                report.antithesis_confidence = anti_result.quality_metrics.overall_score
            if anti_result.quality_metrics:
                report.antithesis_quality = anti_result.quality_metrics

        # Merge quality metrics (weighted average: thesis 0.6, anti 0.4)
        report.quality_metrics = self._merge_quality_metrics(
            report.thesis_quality, report.antithesis_quality, depth=depth,
        )

        # Final Summary Synthesis
        report.synthesis_text = await self._dialectical_synthesis(
            query, thesis_result, anti_result,
        )

        # Final Confidence — dynamic weighting consistent with _merge_quality_metrics
        t_c = report.thesis_confidence
        a_c = report.antithesis_confidence
        total_c = t_c + a_c
        if total_c > 0.01:
            t_w = t_c / total_c
            clamp_min = 0.1 if depth >= 3 else 0.3
            clamp_max = 0.9 if depth >= 3 else 0.7
            t_w = max(clamp_min, min(clamp_max, t_w))
        else:
            t_w = 0.5
        report.final_confidence = t_c * t_w + a_c * (1.0 - t_w)

        report.elapsed_seconds = time.monotonic() - start
        
        # Log stats
        idx_stats = self.ephemeral_index.stats()
        logger.info(
            "Dialectic complete [v2]: conf=%.0f%%, %.1fs. Index stats: %s",
            report.final_confidence * 100, report.elapsed_seconds, idx_stats,
        )

        return report

    async def _dialectical_synthesis(
        self, query: str, thesis_result, anti_result,
    ) -> str:
        """Synthesize parallel thesis and antithesis into a balanced final answer."""
        thesis_text = ""
        anti_text = ""
        if thesis_result and thesis_result.synthesis:
            thesis_text = thesis_result.synthesis[0].content[:2500]
        if anti_result and anti_result.synthesis:
            anti_text = anti_result.synthesis[0].content[:2500]

        if not thesis_text and not anti_text:
            return "(No synthesis available from either engine)"

        prompt = (
            "You are performing a dialectical synthesis of two independent parallel research efforts.\\n"
            "Integrate the Thesis (supporting evidence) and Antithesis "
            "(counter-evidence) into a balanced, nuanced final answer.\\n\\n"
            "Rules:\\n"
            "- Acknowledge BOTH supporting and counter-evidence\\n"
            "- Identify where the evidence is strong vs weak\\n"
            "- Note unresolved tensions or open questions\\n"
            "- Be specific about what we can and cannot conclude\\n\\n"
            f"## Research Question\\n{query}\\n\\n"
            f"## Thesis Perspective\\n{thesis_text}\\n\\n"
            f"## Antithesis Perspective\\n{anti_text}\\n\\n"
            "## Dialectical Synthesis\\n"
            "Write a balanced synthesis (500-1000 words):\\n"
        )

        synthesis = await _llm_ask(
            prompt, model="gemini-3.1-pro-preview", max_tokens=2048,
        )
        return synthesis or "(Synthesis generation failed)"

    @staticmethod
    def _merge_quality_metrics(thesis_qm, anti_qm, depth: int = 2):
        """Merge thesis/antithesis QualityMetrics via dynamic Precision weighting.

        Uses each engine's overall_score as a confidence proxy.
        Weight is clamped to [0.1, 0.9] for L3+, [0.3, 0.7] otherwise.
        Falls back to 0.5/0.5 if scores are negligible.
        """
        if thesis_qm is None and anti_qm is None:
            return None

        from mekhane.periskope.quality_metrics import QualityMetrics

        # Use only available metrics with proper weighting
        if thesis_qm is None:
            return anti_qm
        if anti_qm is None:
            return thesis_qm

        # Dynamic Precision weighting: use overall_score as confidence proxy
        t_conf = getattr(thesis_qm, 'overall_score', 0.5)
        a_conf = getattr(anti_qm, 'overall_score', 0.5)
        total = t_conf + a_conf
        if total < 0.01:
            t_w, a_w = 0.5, 0.5
        else:
            t_w = t_conf / total
            a_w = a_conf / total
            
        # Clamp to prevent one engine from completely dominating
        clamp_min = 0.1 if depth >= 3 else 0.3
        clamp_max = 0.9 if depth >= 3 else 0.7
        t_w = max(clamp_min, min(clamp_max, t_w))
        a_w = 1.0 - t_w

        return QualityMetrics(
            ndcg_at_10=thesis_qm.ndcg_at_10 * t_w + anti_qm.ndcg_at_10 * a_w,
            source_entropy=(
                thesis_qm.source_entropy * t_w + anti_qm.source_entropy * a_w
            ),
            max_entropy=max(thesis_qm.max_entropy, anti_qm.max_entropy),
            coverage_score=(
                thesis_qm.coverage_score * t_w + anti_qm.coverage_score * a_w
            ),
        )

