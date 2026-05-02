from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/prokataskeve/models.py V-001 データモデル
"""
Prokataskeuē Data Models — All dataclasses and enums for the pre-processing pipeline.

PURPOSE: Single source of truth for all data structures used across the 8 modules.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# =============================================================================
# Enums
# =============================================================================


# PURPOSE: Depth levels for pre-processing
class Depth(str, Enum):
    """Pre-processing depth levels, synchronized with main processing depth."""
    L0 = "L0"  # Rule-based only (3 functions, <50ms)
    L1 = "L1"  # + Gemini Flash (6 functions, <300ms)
    L2 = "L2"  # + Standard LLM (12 functions, <1s)
    L3 = "L3"  # + Heavy LLM (16 functions, <3s)
    L4 = "L4"  # + Speculative (18 functions, <5s)


# PURPOSE: Entity types detected by L0 Analysis
class EntityType(str, Enum):
    """Types of entities extracted from input text."""
    PATH = "path"
    URL = "url"
    NUMBER = "number"
    CODE_BLOCK = "code_block"
    QUOTED = "quoted"
    CCL = "ccl"
    LANGUAGE = "language"


# PURPOSE: Intent types classified by L1 Noēsis
class IntentType(str, Enum):
    """High-level intent classification."""
    SEARCH = "search"
    CODE = "code"
    DISCUSS = "discuss"
    DEBUG = "debug"
    REVIEW = "review"
    WORKFLOW = "workflow"
    UNKNOWN = "unknown"


# PURPOSE: Domain classification
class Domain(str, Enum):
    """Domain of the input."""
    ACADEMIC = "academic"
    ENGINEERING = "engineering"
    OPS = "ops"
    GENERAL = "general"


# =============================================================================
# L0 Data Models
# =============================================================================


@dataclass
class Entity:
    """An entity extracted from input text (L0 Analysis)."""
    type: EntityType
    value: str
    start: int
    end: int


@dataclass
class CertainSpan:
    """A span of text marked as SOURCE (L0 Katalēpsis)."""
    text: str
    source_type: str  # "quoted", "code_block", "number", "path", "blockquote"
    start: int
    end: int


# =============================================================================
# L1 Data Models
# =============================================================================


@dataclass
class IntentClassification:
    """Intent classification result (L1 Noēsis)."""
    intent: IntentType
    domain: Domain
    confidence: float = 0.0
    reasoning: str = ""


# =============================================================================
# L2 Data Models
# =============================================================================


@dataclass
class GoalExtraction:
    """Structured goal extracted from input (L2 Boulēsis)."""
    action: str           # e.g., "fix", "search", "create", "review"
    target: str           # e.g., "bug", "paper", "class", "code"
    constraints: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class TemplateMatch:
    """Result of template matching (L2 Synagōgē)."""
    template_id: str      # e.g., "ccl_execute", "paper_search", "code_review"
    template_name: str
    confidence: float = 0.0
    params: dict[str, str] = field(default_factory=dict)


@dataclass
class AmbiguitySpan:
    """A span of text flagged as ambiguous (L2 Epochē)."""
    text: str
    ambiguity_type: str   # "unresolved_ref", "vague_scope", "omitted_subject", "implicit_context"
    start: int
    end: int
    suggestion: str = ""  # How to resolve this ambiguity


@dataclass
class ContextSummary:
    """Integrated context from session state and memory (L2 Synopsis)."""
    session_topic: str = ""
    active_files: list[str] = field(default_factory=list)
    recent_decisions: list[str] = field(default_factory=list)
    related_kis: list[str] = field(default_factory=list)
    summary_text: str = ""


@dataclass
class FewShotExample:
    """A few-shot example from past successes (L2 Bebaiōsis)."""
    input_text: str
    output_text: str
    source: str = ""      # e.g., "kairos:handoff_2026-03-07", "sophia:ki_name"
    relevance: float = 0.0


@dataclass
class StructuredBlock:
    """MECE 構造化された1ブロック (L2 Skepsis×Synagōgē)."""
    block_id: str         # 例: "A-1", "B-2", "C-1"
    series: str           # "A" (タスク), "B" (アイデア), "C" (メタ)
    tone: str             # 例: "指示", "提案", "仮説 40%"
    content: str          # ブロック本文
    confidence: float = 0.5
    dependencies: list[str] = field(default_factory=list)  # 例: ["A-1"]
    suggested_wf: str = ""  # 例: "/ene", "/noe+"
    wf_rationale: str = ""  # WF 提案の根拠 (「〜が可能になる」)
    voice: str = ""       # 発話トーン保存 (インライン確信度マーカー含む)
    is_held: bool = False  # 留保フラグ
    priority: int = 0     # 実行優先順位 (1=最優先, 0=未設定)


@dataclass
class TraceEntry:
    """トレーサビリティ表の1行 — 原文の文 → 対応ブロックID."""
    original: str         # 原文のフレーズ
    block_id: str         # 対応するブロック ID (例: "A-1", "A-3 [条件]")


@dataclass
class StructureResult:
    """MECE 構造化の全体結果 (L2 Skepsis×Synagōgē)."""
    blocks: list[StructuredBlock] = field(default_factory=list)
    raw_output: str = ""   # LLM の生出力 (デバッグ用)
    is_fallback: bool = False  # フォールバック結果かどうか
    summary: str = ""      # 冒頭サマリ (例: "3タスク + 2構想")
    traceability: list[TraceEntry] = field(default_factory=list)  # 原文→ブロック逆引き


# =============================================================================
# L3 Data Models
# =============================================================================


@dataclass
class PastResult:
    """A past processing result for similar input (L3 Anatheōrēsis)."""
    query: str
    result_summary: str
    source: str = ""      # e.g., "chronos:session_id"
    success: bool = True
    timestamp: str = ""


@dataclass
class Contradiction:
    """A detected contradiction (L3 Elenchos)."""
    description: str
    span_a: str           # First contradicting element
    span_b: str           # Second contradicting element
    severity: str = "medium"  # "low", "medium", "high"


@dataclass
class FixSuggestion:
    """A suggested fix for ambiguity or contradiction (L3 Diorthōsis)."""
    issue_type: str       # "ambiguity" or "contradiction"
    original: str
    suggestion: str
    action: str = "ask"   # "ask" (clarification), "auto_fix", "warn"


# =============================================================================
# Complete Result
# =============================================================================


@dataclass
class PreprocessResult:
    """Complete result of the pre-processing pipeline."""
    # Input
    original_text: str
    depth: Depth

    # L0 outputs
    normalized_text: str = ""
    entities: list[Entity] = field(default_factory=list)
    certain_spans: list[CertainSpan] = field(default_factory=list)

    # L1 outputs
    intent: IntentClassification | None = None
    resolved_refs: dict[str, str] = field(default_factory=dict)
    rewritten_queries: list[str] = field(default_factory=list)

    # L2 outputs
    goal: GoalExtraction | None = None
    template_match: TemplateMatch | None = None
    diversified_queries: list[str] = field(default_factory=list)
    ambiguities: list[AmbiguitySpan] = field(default_factory=list)
    context_summary: ContextSummary | None = None
    few_shot_examples: list[FewShotExample] = field(default_factory=list)
    structure: StructureResult | None = None

    # L3 outputs
    past_results: list[PastResult] = field(default_factory=list)
    contradictions: list[Contradiction] = field(default_factory=list)
    fix_suggestions: list[FixSuggestion] = field(default_factory=list)
    hyde_query: str | None = None

    # L4 outputs
    predictions: list[str] = field(default_factory=list)
    prefetched: dict[str, Any] = field(default_factory=dict)

    # Metadata
    latency_ms: float = 0.0
    functions_executed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for MCP response."""
        result: dict[str, Any] = {
            "original_text": self.original_text,
            "normalized_text": self.normalized_text,
            "depth": self.depth.value,
            "latency_ms": float(f"{self.latency_ms:.1f}"),
            "functions_executed": self.functions_executed,
            "entities": [
                {"type": e.type.value, "value": e.value,
                 "start": e.start, "end": e.end}
                for e in self.entities
            ],
            "certain_spans": [
                {"text": cs.text, "source_type": cs.source_type,
                 "start": cs.start, "end": cs.end}
                for cs in self.certain_spans
            ],
        }
        if self.intent is not None:
            result["intent"] = {
                "intent": self.intent.intent.value,
                "domain": self.intent.domain.value,
                "confidence": self.intent.confidence,
                "reasoning": self.intent.reasoning,
            }
        if self.resolved_refs:
            result["resolved_refs"] = self.resolved_refs
        if self.rewritten_queries:
            result["rewritten_queries"] = self.rewritten_queries
        # L2
        if self.goal is not None:
            result["goal"] = {
                "action": self.goal.action, "target": self.goal.target,
                "constraints": self.goal.constraints, "confidence": self.goal.confidence,
            }
        if self.template_match is not None:
            result["template_match"] = {
                "template_id": self.template_match.template_id,
                "template_name": self.template_match.template_name,
                "confidence": self.template_match.confidence,
                "params": self.template_match.params,
            }
        if self.diversified_queries:
            result["diversified_queries"] = self.diversified_queries
        if self.ambiguities:
            result["ambiguities"] = [
                {"text": a.text, "type": a.ambiguity_type,
                 "start": a.start, "end": a.end, "suggestion": a.suggestion}
                for a in self.ambiguities
            ]
        if self.context_summary is not None:
            result["context_summary"] = {
                "session_topic": self.context_summary.session_topic,
                "active_files": self.context_summary.active_files,
                "recent_decisions": self.context_summary.recent_decisions,
                "related_kis": self.context_summary.related_kis,
                "summary_text": self.context_summary.summary_text,
            }
        if self.few_shot_examples:
            result["few_shot_examples"] = [
                {"input": ex.input_text, "output": ex.output_text,
                 "source": ex.source, "relevance": ex.relevance}
                for ex in self.few_shot_examples
            ]
        if self.structure is not None:
            result["structure"] = {
                "blocks": [
                    {"id": b.block_id, "series": b.series, "tone": b.tone,
                     "content": b.content, "confidence": b.confidence,
                     "dependencies": b.dependencies, "suggested_wf": b.suggested_wf,
                     "wf_rationale": b.wf_rationale, "voice": b.voice,
                     "is_held": b.is_held, "priority": b.priority}
                    for b in self.structure.blocks
                ],
                "is_fallback": self.structure.is_fallback,
                "summary": self.structure.summary,
                "traceability": [
                    {"original": t.original, "block_id": t.block_id}
                    for t in self.structure.traceability
                ],
            }
        # L3 (always include keys when depth >= L3)
        if self.depth.value >= Depth.L3.value:
            result["past_results"] = [
                {"query": pr.query, "summary": pr.result_summary,
                 "source": pr.source, "success": pr.success}
                for pr in self.past_results
            ]
            result["contradictions"] = [
                {"description": c.description, "span_a": c.span_a,
                 "span_b": c.span_b, "severity": c.severity}
                for c in self.contradictions
            ]
            result["fix_suggestions"] = [
                {"type": fs.issue_type, "original": fs.original,
                 "suggestion": fs.suggestion, "action": fs.action}
                for fs in self.fix_suggestions
            ]
            result["hyde_query"] = self.hyde_query
        else:
            # Include only if non-empty (sparse output for lower depths)
            if self.past_results:
                result["past_results"] = [
                    {"query": pr.query, "summary": pr.result_summary,
                     "source": pr.source, "success": pr.success}
                    for pr in self.past_results
                ]
            if self.contradictions:
                result["contradictions"] = [
                    {"description": c.description, "span_a": c.span_a,
                     "span_b": c.span_b, "severity": c.severity}
                    for c in self.contradictions
                ]
            if self.fix_suggestions:
                result["fix_suggestions"] = [
                    {"type": fs.issue_type, "original": fs.original,
                     "suggestion": fs.suggestion, "action": fs.action}
                    for fs in self.fix_suggestions
                ]
            if self.hyde_query:
                result["hyde_query"] = self.hyde_query
        # L4 (always include keys when depth >= L4)
        if self.depth.value >= Depth.L4.value:
            result["predictions"] = self.predictions
            result["prefetched"] = self.prefetched
        else:
            if self.predictions:
                result["predictions"] = self.predictions
            if self.prefetched:
                result["prefetched"] = self.prefetched
        return result
