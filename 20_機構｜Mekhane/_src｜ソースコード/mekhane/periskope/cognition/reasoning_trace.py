from __future__ import annotations
# PROOF: mekhane/periskope/cognition/reasoning_trace.py
# PURPOSE: periskope モジュールの reasoning_trace
"""
Reasoning Trace — CoT Search Chain for Periskopē.

Each search iteration produces a ReasoningStep recording:
  - What was learned (Facts)
  - Contradictions found (Distortion check)
  - Remaining knowledge gaps (Counter)
  - Next queries to pursue (Alternative)
  - Confidence score (Score)

This structure mirrors N-2 Thought Record (F→D→C→A→S)
applied to search rather than internal reasoning.

Reference: arXiv:2506.18959 "From Web Search towards Agentic Deep Research"
"""


import json
import logging
import re
from dataclasses import dataclass, field

from mekhane.periskope.cognition._llm import llm_ask as _llm_ask

# PURPOSE: Týpos プロンプトローダー
from mekhane.periskope.prompts import load_prompt

logger = logging.getLogger(__name__)


# PURPOSE: [L2-auto] ReasoningStep のデータクラス定義
@dataclass
class ReasoningStep:
    """One iteration's reasoning record. N-2 Thought Record for search.

    F (Facts)       → learned: what we newly discovered
    D (Distortion)  → contradictions: inconsistencies found
    C (Counter)     → gaps: what remains unknown
    A (Alternative) → next_queries: derived follow-up queries
    S (Score)       → confidence + info_gain
    """

    iteration: int
    learned: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    next_queries: list[str] = field(default_factory=list)
    refutations: list[str] = field(default_factory=list)
    confidence: float = 0.0
    info_gain: float = 0.0
    new_results: int = 0

    def summary(self) -> str:
        """One-line summary for logging."""
        parts = [
            f"[iter {self.iteration}]",
            f"learned={len(self.learned)}",
            f"contradictions={len(self.contradictions)}",
            f"gaps={len(self.gaps)}",
            f"next={len(self.next_queries)}",
        ]
        if self.refutations:
            parts.append(f"refutations={len(self.refutations)}")
        parts.extend([
            f"conf={self.confidence:.0%}",
            f"gain={self.info_gain:.3f}",
        ])
        return " ".join(parts)


# PURPOSE: [L2-auto] ReasoningTrace のデータクラス定義
@dataclass
class ReasoningTrace:
    """Full reasoning chain across all search iterations."""

    query: str
    steps: list[ReasoningStep] = field(default_factory=list)

    @property
    def cumulative_knowledge(self) -> str:
        """Concatenate all learned facts across iterations."""
        sections = []
        for step in self.steps:
            if step.learned:
                sections.append(
                    f"### Iteration {step.iteration} "
                    f"(confidence: {step.confidence:.0%})\n"
                    + "\n".join(f"- {item}" for item in step.learned)
                )
            if step.contradictions:
                sections.append(
                    "**Contradictions found:**\n"
                    + "\n".join(f"- ⚠️ {item}" for item in step.contradictions)
                )
        return "\n\n".join(sections) if sections else "(No prior knowledge)"

    @property
    def open_questions(self) -> list[str]:
        """Return gaps from the most recent step."""
        if self.steps:
            return self.steps[-1].gaps
        return []

    @property
    def latest_confidence(self) -> float:
        """Return confidence from the most recent step."""
        if self.steps:
            return self.steps[-1].confidence
        return 0.0

    def to_dict(self) -> dict:
        """Serialize for logging / report inclusion."""
        return {
            "query": self.query,
            "total_iterations": len(self.steps),
            "final_confidence": self.latest_confidence,
            "steps": [
                {
                    "iteration": s.iteration,
                    "learned": s.learned,
                    "contradictions": s.contradictions,
                    "gaps": s.gaps,
                    "next_queries": s.next_queries,
                    "refutations": s.refutations,
                    "confidence": s.confidence,
                    "info_gain": s.info_gain,
                    "new_results": s.new_results,
                }
                for s in self.steps
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ReasoningTrace':
        """Deserialize from dict (JSON roundtrip)."""
        trace = cls(query=data.get("query", ""))
        for s_data in data.get("steps", []):
            step = ReasoningStep(
                iteration=s_data.get("iteration", 0),
                learned=s_data.get("learned", []),
                contradictions=s_data.get("contradictions", []),
                gaps=s_data.get("gaps", []),
                next_queries=s_data.get("next_queries", []),
                refutations=s_data.get("refutations", []),
                confidence=s_data.get("confidence", 0.0),
                info_gain=s_data.get("info_gain", 0.0),
                new_results=s_data.get("new_results", 0),
            )
            trace.steps.append(step)
        return trace

    def format_for_report(self) -> str:
        """Format trace as markdown for inclusion in the final report."""
        if not self.steps:
            return ""
        lines = ["## Reasoning Trace\n"]
        for step in self.steps:
            lines.append(f"### Iteration {step.iteration}")
            if step.learned:
                lines.append("**Learned:**")
                lines.extend(f"- {x}" for x in step.learned)
            if step.contradictions:
                lines.append("**Contradictions:**")
                lines.extend(f"- ⚠️ {x}" for x in step.contradictions)
            if step.refutations:
                lines.append("**Refutations (Phase Inversion):**")
                lines.extend(f"- 🔄 {x}" for x in step.refutations)
            if step.gaps:
                lines.append("**Open questions:**")
                lines.extend(f"- ❓ {x}" for x in step.gaps)
            lines.append(
                f"**Confidence:** {step.confidence:.0%} | "
                f"**Info gain:** {step.info_gain:.3f} | "
                f"**New results:** {step.new_results}"
            )
            lines.append("")
        return "\n".join(lines)


# PURPOSE: [L2-auto] analyze_iteration の非同期処理定義
async def analyze_iteration(
    query: str,
    trace: ReasoningTrace,
    current_synthesis: str,
    max_queries: int = 2,
) -> ReasoningStep:
    """Analyze current synthesis in context of prior reasoning chain.

    This is the core CoT-in-Search function: it takes the accumulated
    reasoning trace + current synthesis and produces a structured
    analysis of what was learned, what contradicts, what's missing,
    and what to search next.

    Args:
        query: Original research query.
        trace: Accumulated reasoning trace from prior iterations.
        current_synthesis: Current synthesis text (from latest round).
        max_queries: Maximum number of next queries to generate.

    Returns:
        ReasoningStep with structured analysis.
    """
    iteration = len(trace.steps) + 1

    # Build the CoT prompt
    prompt = _build_analysis_prompt(
        query, trace, current_synthesis, max_queries,
    )

    # Call LLM — use Pro for quality (runs every iteration)
    raw = await _llm_ask(prompt, model="gemini-3.1-pro-preview", max_tokens=512)

    if not raw:
        logger.warning("Reasoning analysis returned empty (iter %d)", iteration)
        return ReasoningStep(iteration=iteration)

    # Parse structured output
    step = _parse_analysis(raw, iteration)

    logger.info("Reasoning: %s", step.summary())

    return step


# PURPOSE: [L2-auto] _build_analysis_prompt の関数定義
def _build_analysis_prompt(
    query: str,
    trace: ReasoningTrace,
    current_synthesis: str,
    max_queries: int,
) -> str:
    """Build the structured analysis prompt for CoT-in-Search."""
    prior = trace.cumulative_knowledge

    template = load_prompt("reasoning_trace_analysis.typos")
    if template:
        return template.format(
            query=query,
            prior=prior,
            current_synthesis=current_synthesis[:3000],
            max_queries=max_queries,
        )

    # Fallback: hardcoded prompt
    return (
        "You are a research analyst performing iterative deep research.\n\n"
        f"## Research Goal\n{query}\n\n"
        f"## Prior Reasoning Chain\n{prior}\n\n"
        f"## Current Synthesis (latest search round)\n"
        f"{current_synthesis[:3000]}\n\n"
        "## Your Task\n"
        "Analyze the current synthesis IN CONTEXT of what was previously known.\n"
        "Produce a structured analysis:\n\n"
        "LEARNED:\n- (list new facts discovered in THIS round, not previously known)\n\n"
        "CONTRADICTIONS:\n- (list any contradictions between sources or with prior knowledge)\n"
        "(write NONE if no contradictions)\n\n"
        "GAPS:\n- (list remaining knowledge gaps that need investigation)\n"
        "(write NONE if research goal is fully answered)\n\n"
        f"NEXT:\n- (list up to {max_queries} search queries to fill the most important gaps)\n"
        "(write NONE if no gaps remain)\n\n"
        "CONFIDENCE: (single integer 0-100, your confidence that the research goal is answered)\n"
    )


# PURPOSE: [L2-auto] _parse_analysis の関数定義
def _parse_analysis(raw: str, iteration: int) -> ReasoningStep:
    """Parse LLM structured output into ReasoningStep."""
    step = ReasoningStep(iteration=iteration)

    logger.debug("Reasoning raw output (iter %d):\n%s", iteration, raw[:500])

    # Extract sections
    step.learned = _extract_section(raw, "LEARNED")
    step.contradictions = _extract_section(raw, "CONTRADICTIONS")
    step.gaps = _extract_section(raw, "GAPS")
    step.next_queries = _extract_section(raw, "NEXT")

    # Extract confidence — multiple formats:
    # CONFIDENCE: 75, CONFIDENCE: 75%, **CONFIDENCE:** 75, ## CONFIDENCE\n75%
    conf_match = re.search(
        r"CONFIDENCE(?:[\*:\s\n]*)(\d+)",
        raw, re.IGNORECASE,
    )
    if conf_match:
        step.confidence = int(conf_match.group(1)) / 100.0
    else:
        # Heuristic fallback: estimate from learned vs gaps ratio
        n_learned = len(step.learned)
        n_gaps = len(step.gaps)
        if n_learned + n_gaps > 0:
            step.confidence = n_learned / (n_learned + n_gaps)
        else:
            step.confidence = 0.5  # No signal → neutral
        logger.warning(
            "Confidence not found in LLM output (iter %d), "
            "estimated %.0f%% from learned=%d, gaps=%d",
            iteration, step.confidence * 100, n_learned, n_gaps,
        )

    return step


def _extract_section(text: str, header: str) -> list[str]:
    """Extract bullet points from a named section.

    Handles LLM output variations:
      - LEARNED:, **LEARNED:**, **LEARNED**:
      - ## LEARNED
      - Bullet points: - item, * item, 1. item
      - NONE / None / none
    """
    lines = text.split("\n")
    # Header format broadly: optional #/spaces, optional *, alphabetical word (3+ chars), optional :, optional *, optional :, optional spaces
    header_regex = re.compile(rf"^(?:\#{{1,3}}\s*)?\*{{0,2}}([A-Z]{{3,}}):?\*{{0,2}}:?\s*$", re.IGNORECASE)
    
    in_section = False
    section_lines = []
    
    for line in lines:
        match = header_regex.match(line.strip())
        if match:
            found_header = match.group(1).upper()
            if found_header == header.upper():
                in_section = True
                continue
            elif in_section:
                # We reached another valid header, stop collecting
                break
        
        if in_section:
            section_lines.append(line)
            
    section_text = "\n".join(section_lines).strip()
    if not section_text:
        return []

    # Check for NONE variants
    if re.match(r"^-?\s*none\.?\s*$", section_text, re.IGNORECASE):
        return []

    # Extract bullet points (-, *, numbered)
    items = []
    for line in section_text.split("\n"):
        line = line.strip()
        # Standard bullet: - item
        if line.startswith("- "):
            item = line[2:].strip()
        # Alternative bullet: * item
        elif line.startswith("* "):
            item = line[2:].strip()
        # Numbered: 1. item, 2. item
        elif re.match(r"^\d+\.\s+", line):
            item = re.sub(r"^\d+\.\s+", "", line).strip()
        else:
            continue

        if item and not re.match(r"^none\.?\s*$", item, re.IGNORECASE):
            items.append(item)

    return items
