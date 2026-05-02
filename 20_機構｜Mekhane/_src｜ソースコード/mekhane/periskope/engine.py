from __future__ import annotations
# PROOF: mekhane/periskope/engine.py
# PURPOSE: periskope モジュールのエンジン実装 (engine)
"""
Periskopē Deep Research Engine — Orchestrator.

VISION: ../VISION.md (設計思想: 問い駆動、Active Inference、7段階認知フロー)
Theory: ../../kernel/search_cognition.md (FEP 定式化、圏論的構造)

Enhancement v2.0:
  - Progress Streaming: progress_callback for real-time phase notifications
  - AI-to-AI Interactive Research: interaction_callback for mid-research guidance
  - Task Decomposition: Φ0.5 automatic subtask splitting for compound queries

Coordinates the full deep research pipeline:
  Phase 0: Cognitive query expansion (Φ1-Φ4)
  Phase 1: Parallel multi-source search (Φ5-Φ6)
  Phase 2: Multi-model synthesis (Cortex/LS)
  Phase 2.5: CoT Search Chain — iterative deepening (Φ7 loop)
  Phase 3: Citation verification (N-10 TAINT)
  Phase 3.5: Φ4 convergent framing + quality metrics
  Phase 4: Report generation + Φ7 Next Questions

Usage:
    engine = PeriskopeEngine()
    report = await engine.research("Free Energy Principle")
    print(report.markdown())
"""


import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from mekhane.paths import INCOMING_DIR
from mekhane.periskope.models import (
    Citation,
    DivergenceReport,
    SearchResult,
    SynthesisResult,
    SynthModel,
    TaintLevel,
)
from mekhane.periskope.quality_metrics import QualityMetrics, compute_quality_metrics, log_metrics
from mekhane.periskope.searchers.searxng import SearXNGSearcher
from mekhane.periskope.searchers.llm_reranker import LLMReranker

from mekhane.periskope.searchers.brave_searcher import BraveSearcher
from mekhane.periskope.searchers.tavily_searcher import TavilySearcher
from mekhane.periskope.searchers.cse_searcher import CseSearcher
from mekhane.periskope.searchers.semantic_scholar_searcher import SemanticScholarSearcher
from mekhane.periskope.searchers.arxiv_searcher import ArxivSearcher
from mekhane.periskope.searchers.openalex_searcher import OpenAlexSearcher
from mekhane.periskope.searchers.github_searcher import GitHubSearcher
from mekhane.periskope.searchers.gemini_searcher import GeminiSearcher
from mekhane.periskope.searchers.stackoverflow_searcher import StackOverflowSearcher
from mekhane.periskope.searchers.reddit_searcher import RedditSearcher
from mekhane.periskope.searchers.hackernews_searcher import HackerNewsSearcher
from mekhane.periskope.searchers.vertex_search_searcher import VertexSearchSearcher
from mekhane.periskope.searchers.internal_searcher import (
    GnosisSearcher,
    SophiaSearcher,
    KairosSearcher,
)
from mekhane.periskope.synthesizer import MultiModelSynthesizer
from mekhane.periskope.citation_agent import CitationAgent
from mekhane.periskope.kalon_detector import KalonDetector, compute_data_budget
from mekhane.periskope.query_expander import QueryExpander
from mekhane.periskope.page_fetcher import PageFetcher, INTERNAL_SOURCES
from mekhane.periskope.cognition import (
    phi0_intent_decompose,
    IntentDecomposition,
    phi0_query_plan,
    QueryPlan,
    phi0_source_adapt,
    SourceAdaptedQueries,
    phi1_blind_spot_analysis,
    phi1_coverage_gaps,
    phi1_counterfactual_queries,
    phi2_divergent_thinking,
    phi3_context_setting,
    phi4_pre_search_ranking,
    phi4_post_search_framing,
    phi7_belief_update,
    BeliefUpdate,
    phi7_query_feedback,
    QueryFeedback,
)
from mekhane.periskope.cognition.reasoning_trace import (
    ReasoningTrace,
    analyze_iteration,
)

logger = logging.getLogger(__name__)

# PURPOSE: Týpos プロンプトローダー
from mekhane.periskope.prompts import load_prompt


# PURPOSE: [L2-auto] _llm_ask の非同期処理定義
async def _llm_ask(prompt: str, model: str = "gemini-3-flash-preview", max_tokens: int = 256) -> str:
    """Lightweight LLM call via OchemaService for internal pipeline steps.

    Used by W6 (refinement queries) and W7 (URL selection).
    Falls back to empty string on failure.
    """
    try:
        from mekhane.ochema.service import OchemaService
        svc = OchemaService.get()
        response = await svc.ask_async(
            prompt, model=model, max_tokens=max_tokens, timeout=15.0,
        )
        return response.text
    except Exception as e:  # noqa: BLE001
        logger.warning("_llm_ask failed: %s", e)
        return ""


# PURPOSE: [L2-auto] _phi1_blind_spot_analysis の非同期処理定義
async def _phi1_blind_spot_analysis(
    query: str,
    context: str = "",
) -> list[str]:
    """Φ1: 無知のリマインド — Query blind spot analysis.

    Analyzes the query for implicit assumptions, missing perspectives,
    and alternative framings. Returns supplementary queries that cover
    the identified blind spots.

    This runs automatically inside the pipeline (always-on).
    The mediating agent (Claude) answers on behalf of the user.

    Design: Search Cognition Theory §2.1 (kernel/search_cognition.md)
    """
    template = load_prompt("phi1_blind_spot_analysis.typos")
    if template:
        prompt = template.format(
            query=query,
            context=context if context else "(none)",
        )
    else:
        # Fallback: hardcoded prompt
        prompt = (
            "You are an epistemic auditor. Analyze this research query for blind spots.\n\n"
            f"Query: {query}\n"
        )
        if context:
            prompt += f"Context: {context}\n"
        prompt += (
            "\nIdentify:\n"
            "1. IMPLICIT ASSUMPTIONS: What does this query take for granted?\n"
            "2. MISSING PERSPECTIVES: What viewpoints or disciplines are absent?\n"
            "3. ALTERNATIVE FRAMINGS: How else could this question be asked?\n\n"
            "Generate 1-3 supplementary search queries that would cover these blind spots.\n"
            "Each query should target a DIFFERENT blind spot.\n\n"
            "Return ONLY the queries, one per line. No numbering, no explanation.\n"
            "If no significant blind spots: NONE"
        )

    text = await _llm_ask(prompt, model="gemini-3-flash-preview", max_tokens=256)

    if not text or "NONE" in text.upper().strip():
        logger.info("Φ1: No significant blind spots detected for %r", query)
        return []

    blind_spot_queries = [
        line.strip()
        for line in text.strip().split("\n")
        if line.strip() and len(line.strip()) > 5
    ]
    blind_spot_queries = blind_spot_queries[:3]  # Cap at 3

    if blind_spot_queries:
        logger.info(
            "Φ1: Detected %d blind spots for %r: %s",
            len(blind_spot_queries), query, blind_spot_queries,
        )

    return blind_spot_queries


# PURPOSE: [L2-auto] DecisionFrame のクラス定義
@dataclass
class DecisionFrame:
    """Φ4: 収束思考 — Structured decision support frame.

    Transforms synthesis (What is known) into judgment support (What to decide).
    The subject (Creator + Claude) makes the final judgment.
    """

    key_findings: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    decision_options: list[str] = field(default_factory=list)
    confidence: float = 0.0
    blind_spots_addressed: int = 0


# PURPOSE: [L2-auto] _phi4_convergent_framing の非同期処理定義
async def _phi4_convergent_framing(
    query: str,
    synthesis_text: str,
) -> DecisionFrame:
    """Φ4: 収束思考 — Structure synthesis into decision support.

    Transforms "what we found" into "what to decide".
    The subject (Creator + Claude) retains judgment authority.

    Design: Search Cognition Theory §2.1 (kernel/search_cognition.md)
    """
    template = load_prompt("phi4_post_search_framing.typos")
    if template:
        prompt = template.format(
            query=query,
            synthesis_text=synthesis_text[:50000],
        )
    else:
        # Fallback: hardcoded prompt
        prompt = (
            "You are a decision support analyst. Given a research synthesis, "
            "structure it for human judgment.\n\n"
            f"Research query: {query}\n\n"
            f"Synthesis:\n{synthesis_text[:50000]}\n\n"
            "Provide EXACTLY this structure (use these exact headers):\n\n"
            "KEY FINDINGS:\n- (3-5 most important findings)\n\n"
            "OPEN QUESTIONS:\n- (2-4 questions that remain unanswered)\n\n"
            "DECISION OPTIONS:\n- (2-3 actionable options the reader could take)\n\n"
            "CONFIDENCE: (0-100, how well does the evidence support a conclusion?)\n"
        )

    text = await _llm_ask(prompt, model="gemini-3-flash-preview", max_tokens=512)

    frame = DecisionFrame()
    if not text:
        return frame

    current_section = ""
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        upper = line.upper()
        if "KEY FINDINGS" in upper:
            current_section = "findings"
            continue
        elif "OPEN QUESTIONS" in upper:
            current_section = "questions"
            continue
        elif "DECISION OPTIONS" in upper:
            current_section = "options"
            continue
        elif "CONFIDENCE" in upper:
            import re
            # Match "CONFIDENCE: 80" or "**Confidence**: 80%"
            confidence_match = re.search(r"CONFIDENCE.*?(\d+)", upper)
            if confidence_match:
                frame.confidence = min(int(confidence_match.group(1)), 100) / 100.0
            continue

        # Strip bullet markers
        if line.startswith(("- ", "* ", "• ")):
            line = line[2:].strip()
        elif len(line) > 2 and line[0].isdigit() and line[1] in ".):":
            line = line[2:].strip()

        if current_section == "findings" and line:
            frame.key_findings.append(line)
        elif current_section == "questions" and line:
            frame.open_questions.append(line)
        elif current_section == "options" and line:
            frame.decision_options.append(line)

    logger.info(
        "Φ4: DecisionFrame generated (%d findings, %d questions, %d options, %.0f%% confidence)",
        len(frame.key_findings), len(frame.open_questions),
        len(frame.decision_options), frame.confidence * 100,
    )
    return frame


# PURPOSE: [L2-auto] ResearchReport のクラス定義
@dataclass
class ResearchReport:
    """Complete research report from Periskopē."""

    query: str
    search_results: list[SearchResult] = field(default_factory=list)
    synthesis: list[SynthesisResult] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    divergence: DivergenceReport | None = None
    decision_frame: DecisionFrame | None = None
    elapsed_seconds: float = 0.0
    source_counts: dict[str, int] = field(default_factory=dict)
    quality_metrics: QualityMetrics | None = None
    reasoning_trace: ReasoningTrace | None = None
    belief_update: BeliefUpdate | None = None
    planning_ratio: float | None = None  # VISION: Phase 0 / total elapsed

    # PURPOSE: [L2-auto] markdown の関数定義
    def markdown(self) -> str:
        """Generate a structured Markdown report."""
        lines = [
            f"# Periskopē Research Report",
            f"",
            f"> **Query**: {self.query}",
            f"> **Time**: {self.elapsed_seconds:.1f}s",
            f"> **Sources**: {len(self.search_results)} results from {len(self.source_counts)} engines",
            f"",
            f"## Table of Contents",
            f"- [Synthesis](#synthesis)",
            f"- [Sources](#sources)",
        ]
        if self.divergence and len(self.divergence.models_compared) > 1:
            lines.append("- [Divergence Analysis](#divergence-analysis)")
        if self.decision_frame:
            lines.append("- [Φ4 Decision Frame](#4-decision-frame)")
        if self.citations:
            lines.append("- [Citation Verification](#citation-verification)")
        if self.quality_metrics:
            lines.append("- [Quality Metrics](#quality-metrics)")
        lines.append("")

        # Source breakdown
        lines.append("## Sources")
        lines.append("")
        lines.append("| Engine | Results |")
        lines.append("|:-------|--------:|")
        for source, count in sorted(self.source_counts.items()):
            lines.append(f"| {source} | {count} |")
        lines.append("")

        # Synthesis
        if self.synthesis:
            lines.append("## Synthesis")
            lines.append("")
            for s in self.synthesis:
                lines.append(f"### {s.model.value} (Confidence: {s.confidence:.0%})")
                lines.append("")
                lines.append(s.content)
                lines.append("")

        # Divergence
        if self.divergence and len(self.divergence.models_compared) > 1:
            lines.append("## Divergence Analysis")
            lines.append("")
            lines.append(f"- Agreement Score: {self.divergence.agreement_score:.2f}")
            if self.divergence.consensus_claims:
                lines.append(f"- Consensus: {'; '.join(self.divergence.consensus_claims)}")
            if self.divergence.divergent_claims:
                lines.append(f"- ⚠️ Divergence: {'; '.join(self.divergence.divergent_claims)}")
            lines.append("")

        # Decision Frame (Φ4)
        if self.decision_frame:
            df = self.decision_frame
            lines.append("## Φ4 Decision Frame")
            lines.append("")
            if df.key_findings:
                lines.append("### Key Findings")
                for f in df.key_findings:
                    lines.append(f"- {f}")
                lines.append("")
            if df.open_questions:
                lines.append("### Open Questions")
                for q in df.open_questions:
                    lines.append(f"- ❓ {q}")
                lines.append("")
            if df.decision_options:
                lines.append("### Decision Options")
                for o in df.decision_options:
                    lines.append(f"- ➡️ {o}")
                lines.append("")
            lines.append(f"**Confidence**: {df.confidence:.0%}")
            lines.append("")

        # Citations
        if self.citations:
            verified = [c for c in self.citations if c.taint_level != TaintLevel.UNCHECKED]
            if verified:
                lines.append("## Citation Verification")
                lines.append("")
                lines.append("| Claim | Level | Score | Note |")
                lines.append("|:------|:------|------:|:-----|")
                for c in verified[:20]:  # Limit display
                    claim_short = c.claim[:60] + "..." if len(c.claim) > 60 else c.claim
                    score = f"{c.similarity:.0%}" if c.similarity is not None else "—"
                    lines.append(
                        f"| {claim_short} | {c.taint_level.value} | {score} | {c.verification_note or ''} |"
                    )
                lines.append("")

        # Quality Metrics
        if self.quality_metrics:
            lines.append(self.quality_metrics.markdown_section())

        if self.reasoning_trace:
            lines.append("")
            lines.append(self.reasoning_trace.format_for_report())

        # Φ7: Next Questions — VISION §5 「問いを育てる」
        next_qs = []
        if self.reasoning_trace and self.reasoning_trace.steps:
            last_step = self.reasoning_trace.steps[-1]
            next_qs = getattr(last_step, 'next_queries', [])
        if self.belief_update and hasattr(self.belief_update, 'next_queries'):
            for q in self.belief_update.next_queries:
                if q not in next_qs:
                    next_qs.append(q)
        if next_qs:
            lines.append("")
            lines.append("## Φ7 Next Questions")
            lines.append("")
            lines.append("> 次の探索で問うべき問い (VISION: 問いを育てる)")
            lines.append("")
            for i, q in enumerate(next_qs, 1):
                lines.append(f"{i}. {q}")
            lines.append("")

        return "\n".join(lines)

    # PURPOSE: [L2-auto] to_json の関数定義
    def to_json(self) -> str:
        """Serialize report to JSON string for AI-to-AI communication."""
        import json
        from dataclasses import asdict
        from enum import Enum
        
        class EnumEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Enum):
                    return obj.value
                return super().default(obj)
                
        data = asdict(self)
        return json.dumps(data, cls=EnumEncoder, ensure_ascii=False, indent=2)

    # PURPOSE: [L2-auto] to_typos の関数定義
    def to_typos(self) -> str:
        """Export report in TYPOS syntax (not yet implemented).
        
        This will translate the structured JSON output into TYPOS directives
        (e.g., @node, @claim) for advanced Hegemonikón data management.
        """
        raise NotImplementedError("TYPOS export will be supported in v7.1")

    # PURPOSE: [L2-auto] from_json の関数定義
    @classmethod
    def from_json(cls, json_str: str) -> "ResearchReport":
        """Deserialize report from JSON string."""
        import json
        from mekhane.periskope.models import SearchSource, SynthModel, SearchResult, SynthesisResult, Citation, TaintLevel, DivergenceReport
        from mekhane.periskope.quality_metrics import QualityMetrics
        data = json.loads(json_str)
        
        search_results = data.pop('search_results', [])
        data['search_results'] = [
            SearchResult(**{**r, 'source': SearchSource(r['source'])}) 
            for r in search_results
        ]
        
        synth_results = data.pop('synthesis', [])
        data['synthesis'] = []
        for sr in synth_results:
            citations_data = sr.pop('citations', [])
            citations = [Citation(**{**c, 'taint_level': TaintLevel(c['taint_level'])}) for c in citations_data]
            data['synthesis'].append(SynthesisResult(**{
                **sr, 'model': SynthModel(sr['model']), 'citations': citations
            }))
            
        div_data = data.pop('divergence', None)
        if div_data:
            div_data['models_compared'] = [SynthModel(m) for m in div_data.get('models_compared', [])]
            data['divergence'] = DivergenceReport(**div_data)
            
        citations_data = data.pop('citations', [])
        data['citations'] = [Citation(**{**c, 'taint_level': TaintLevel(c['taint_level'])}) for c in citations_data]

        # Restore DecisionFrame
        df_data = data.pop('decision_frame', None)
        if df_data:
            data['decision_frame'] = DecisionFrame(**df_data)

        # Restore QualityMetrics
        qm_data = data.pop('quality_metrics', None)
        if qm_data:
            data['quality_metrics'] = QualityMetrics(**qm_data)

        # Restore ReasoningTrace (Enhancement ④)
        rt_data = data.pop('reasoning_trace', None)
        if rt_data:
            from mekhane.periskope.cognition.reasoning_trace import ReasoningTrace
            data['reasoning_trace'] = ReasoningTrace.from_dict(rt_data)

        # Restore BeliefUpdate (passthrough — simple dict ok)
        bu_data = data.pop('belief_update', None)
        if bu_data:
            data['belief_update'] = bu_data

        return cls(**data)


# PURPOSE: [L2-auto] PeriskopeEngine のクラス定義
class PeriskopeEngine:
    """Orchestrate the full Periskopē deep research pipeline.

    Configurable searchers and synthesis models allow flexible
    composition for different research needs:

    - Quick: SearXNG only + Gemini Flash
    - Standard: SearXNG + Brave + Tavily + Gnōsis + Gemini Flash
    - Deep: All searchers + multi-model + citation verification
    """

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(
        self,
        searxng_url: str | list[str] | None = None,
        synth_models: list[SynthModel] | None = None,
        max_results_per_source: int = 10,
        verify_citations: bool = True,
        shared_index: 'EphemeralIndex | None' = None,
        role: str = "standalone",
        decay_type: str | None = None,
        alpha_schedule: str | None = None,
    ) -> None:
        # Load .env for API keys (Google CSE, GitHub, etc.)
        try:
            from mekhane.paths import ensure_env
            ensure_env()
        except ImportError:
            pass  # mekhane.paths not available — rely on system env vars

        # P8: Load config from yaml
        self._config = self._load_config()
        
        self.decay_type_override = decay_type
        self.alpha_schedule_override = alpha_schedule

        self.max_results = max_results_per_source
        # Depth-adaptive max_results: config.yaml defaults.max_results_by_depth
        self._max_results_by_depth = self._config.get("defaults", {}).get(
            "max_results_by_depth", {1: 15, 2: 30, 3: 50}
        )
        self.verify_citations = verify_citations

        # Searchers — domain blocklist from config.yaml
        searxng_blocklist = set(self._config.get("domain_blocklist", []))
        searxng_cfg = self._config.get("searxng", {})
        # Resolve SearXNG URL(s): explicit arg > config searxng_urls > config searxng_url > default
        resolved_url: str | list[str] = searxng_url or self._config.get(
            "searxng_urls", self._config.get("searxng_url", "http://localhost:8888")
        )
        self.searxng = SearXNGSearcher(
            base_url=resolved_url,
            domain_blacklist=searxng_blocklist,
            category_engines=searxng_cfg.get("engines"),
        )

        self.brave = BraveSearcher()
        self.tavily = TavilySearcher()
        # Google CSE multi-account
        cse_config = self._config.get("google_cse", {})
        if cse_config.get("enabled", False):
            self.google_cse = CseSearcher(
                accounts_config=cse_config.get("accounts"),
            )
        else:
            self.google_cse = CseSearcher()  # No accounts = not available
        self.semantic_scholar = SemanticScholarSearcher()
        self.arxiv = ArxivSearcher()
        self.openalex = OpenAlexSearcher()
        self.github = GitHubSearcher()
        self.gemini_search = GeminiSearcher()
        self.stackoverflow = StackOverflowSearcher()
        self.reddit = RedditSearcher()
        self.hackernews = HackerNewsSearcher()
        vs_config = self._config.get("vertex_search", {})
        # Support both legacy (project/engine_id at top) and new (engines list)
        engines_list = vs_config.get("engines", None)
        if engines_list is None and vs_config.get("project"):
            # Legacy single-engine config — wrap in list for backward compat
            engines_list = None  # Let VertexSearchSearcher handle it
            self.vertex_search = VertexSearchSearcher(
                project=vs_config.get("project", ""),
                engine_id=vs_config.get("engine_id", ""),
                location=vs_config.get("location", "global"),
                credentials_file=vs_config.get("credentials_file", ""),
            )
        else:
            # Multi-engine config
            self.vertex_search = VertexSearchSearcher(
                engines=engines_list or [],
            )
        # W1: Vertex AI Vector Search (Matching Engine / ANN)
        from mekhane.periskope.searchers.vector_search_searcher import VectorSearchSearcher as VVSSearcher
        vvs_cfg = self._config.get("vector_search_ann", {})
        self.vector_search_ann = VVSSearcher(
            project=vvs_cfg.get("project", ""),
            location=vvs_cfg.get("location", "us-central1"),
            index_endpoint_id=vvs_cfg.get("index_endpoint_id", ""),
            deployed_index_id=vvs_cfg.get("deployed_index_id", "periskope_deployed_idx"),
            embedder=None,  # Injected lazily during search via _init_embedder
            credentials_file=vvs_cfg.get("credentials_file", ""),
        )

        self.gnosis = GnosisSearcher()
        self.sophia = SophiaSearcher()
        self.kairos = KairosSearcher()

        # Shared CortexClient (single instance for synthesizer + reranker)
        self._shared_cortex = None  # Lazy-initialized

        # Synthesizer — depth-level model routing from config
        gemini_model = self._config.get("synthesis", {}).get(
            "gemini_model", "gemini-3.1-pro-preview",
        )
        self.synthesizer = MultiModelSynthesizer(
            synth_models=synth_models,  # None = use depth routing
            gemini_model=gemini_model,
            cortex=self._get_shared_cortex(),
        )

        # Citation Agent
        self.citation_agent = CitationAgent()
        self.url_auditor = None  # Layer D: lazy-initialized

        # Query Expander (W3)
        expansion_model = self._config.get("expansion_model", "gemini-3-flash-preview")
        self.query_expander = QueryExpander(model=expansion_model)

        # Page Fetcher (W7: selective deep-read crawling)
        crawl_config = self._config.get("crawling", {})
        self.page_fetcher = PageFetcher(
            timeout=crawl_config.get("timeout", 10.0),
            max_content_length=crawl_config.get("max_content_length", 40_000),
            min_content_length=crawl_config.get("min_content_length", 500),
            playwright_fallback=crawl_config.get("playwright_fallback", True),
        )

        # Embedder cache (P1: avoid re-loading embedder per rerank call)
        self._embedder = None  # Lazy-initialized

        # LLM Reranker (Stage 1 Flash + Stage 2 Pro cascade)
        # AP-3: 初期化順序依存を防ぐため cortex の DI はせず llm_reranker 内部の lazy load に任せる
        self.llm_reranker = LLMReranker(self._config)

        # Cloud NL API Client
        self.cloud_nl_cfg = self._config.get("cloud_nl", {})
        self.nl_client = None
        self._nl_entity_cache: dict = {}  # query → list[Entity]
        self._nl_call_count: int = 0  # P1: API call counter for cost control
        self._nl_max_calls: int = self.cloud_nl_cfg.get("max_calls_per_research", 10)
        if self.cloud_nl_cfg.get("enabled", False):
            try:
                from mekhane.ochema.nl_client import NLClient
                accounts = self.cloud_nl_cfg.get("accounts", [])
                if accounts:
                    # P4: Deterministic round-robin based on object id
                    acct_idx = id(self) % len(accounts)
                    acct = accounts[acct_idx]
                    self.nl_client = NLClient(
                        gcloud_account=acct.get("gcloud_account", ""),
                        project_id=acct.get("project_id", "")
                    )
                    logger.info("Cloud NL API enabled (account[%d]: %s)", acct_idx, acct.get("gcloud_account", ""))
            except Exception as e:  # noqa: BLE001
                logger.warning("Failed to initialize NLClient: %s", e)

        # Search result cache (P4: avoid duplicate queries in multi-pass)
        self._search_cache: dict[str, tuple[list[SearchResult], dict[str, int]]] = {}

        # Phase Inversion: shared index for dialectic inter-engine communication
        self._shared_index = shared_index  # EphemeralIndex or None
        self._role = role  # "thesis" | "antithesis" | "standalone"
        # LS-pattern context buffer (depth set lazily at research time)
        self._dialectic_buffer: 'DialecticContextBuffer | None' = None

        self._reasoning_trace: 'ReasoningTrace' | None = None

    def _init_embedder(self):
        """Lazy-initialize embedder via shared factory (Single Source of Truth).

        Priority: VertexEmbedder (API, SA key) → Local fallback.
        SA key from config.yaml eliminates gcloud active account dependency.
        See embedder_factory.py for initialization logic.
        """
        if self._embedder is not None:
            return

        from mekhane.periskope.embedder_factory import get_embedder
        # Pass credentials_file from vector_search_ann config
        vvs_cfg = self._config.get("vector_search_ann", {})
        creds = vvs_cfg.get("credentials_file", "")
        self._embedder = get_embedder(credentials_file=creds)

    def _get_shared_cortex(self):
        """Lazy-initialize shared CortexClient (single instance for reranker + synthesizer)."""
        if self._shared_cortex is None:
            from mekhane.ochema.cortex_client import CortexClient
            try:
                from mekhane.ochema.account_router import get_account_for
                account = get_account_for("periskope")
            except Exception:  # noqa: BLE001
                account = "default"
            self._shared_cortex = CortexClient(max_tokens=65536, account=account)
        return self._shared_cortex

    # PURPOSE: [L2-auto] _load_config の関数定義
    @staticmethod
    def _load_config() -> dict:
        """P8: Load config.yaml — delegates to config_loader (H6)."""
        from mekhane.periskope.config_loader import load_config
        return load_config()

    def _clone_for_subtask(self) -> 'PeriskopeEngine':
        """Create a lightweight clone of the engine for parallel subtask execution.
        
        Shares stateless search clients and caches to prevent connection leaks
        and 429 rate limits, while maintaining isolated state for the subtask.
        """
        # Create a new engine instance to avoid state corruption during parallel execution
        sub_engine = type(self)(
            synth_models=self.synthesizer.synth_models,
            max_results_per_source=self.max_results,
            verify_citations=self.verify_citations,
            shared_index=self._shared_index,
            role=self._role,
            decay_type=self.decay_type_override,
            alpha_schedule=self.alpha_schedule_override,
        )
        # Inherit searchers (prevent 429 and connection leaks)
        sub_engine.searxng = self.searxng
        sub_engine.brave = self.brave
        sub_engine.tavily = self.tavily
        sub_engine.semantic_scholar = self.semantic_scholar
        sub_engine.gnosis = self.gnosis
        sub_engine.sophia = self.sophia
        sub_engine.kairos = self.kairos
        sub_engine.arxiv = self.arxiv
        sub_engine.openalex = self.openalex
        sub_engine.github = self.github
        sub_engine.gemini_search = self.gemini_search
        sub_engine.vertex_search = self.vertex_search
        sub_engine.stackoverflow = self.stackoverflow
        sub_engine.reddit = self.reddit
        sub_engine.hackernews = self.hackernews
        sub_engine.google_cse = self.google_cse
        sub_engine.vector_search_ann = self.vector_search_ann
        
        # Inherit core components and caches
        sub_engine.page_fetcher = self.page_fetcher
        sub_engine.llm_reranker = self.llm_reranker
        sub_engine.citation_agent = self.citation_agent
        sub_engine.synthesizer = self.synthesizer
        sub_engine.query_expander = self.query_expander
        sub_engine._embedder = self._embedder
        sub_engine._search_cache = self._search_cache

        sub_engine._shared_cortex = getattr(self, '_shared_cortex', None)
        sub_engine.nl_client = getattr(self, 'nl_client', None)
        sub_engine._in_subtask = True
        return sub_engine


    # PURPOSE: [L2-auto] research の非同期処理定義
    async def research(
        self,
        query: str,
        sources: list[str] | None = None,
        auto_digest: bool = False,
        digest_depth: str = "quick",
        expand_query: bool = True,
        multipass: bool = False,
        depth: int = 2,
        diversity_weight: float = 0.3,
        known_context: str = "",
        system_instruction: str | None = None,
        llm_rerank: bool | None = None,
        progress_callback: 'ProgressCallback | None' = None,
        interaction_callback: 'Callable[[object], str | None] | None' = None,
    ) -> ResearchReport:
        """Execute the full research pipeline.

        Args:
            query: Research query.
            sources: List of source names to use. If None, uses all.
                Valid: "searxng", "brave", "tavily", "semantic_scholar",
                    "gnosis", "sophia", "kairos"
            auto_digest: If True, write results to Digestor incoming/ as eat_*.md.
            digest_depth: Digest template depth — "quick" (/eat-), "standard" (/eat), "deep" (/eat+).
            expand_query: If True, expand query via bilingual translation (W3).
            multipass: If True, perform 2-pass search for deeper coverage (W6).
            depth: HGK depth level (1=L1 Quick, 2=L2 Standard, 3=L3 Deep).
                Controls model selection for synthesis.
            diversity_weight: Balance between precision and diversity (0.0-1.0).
                0.0 = precision-focused (NDCG dominates overall score).
                1.0 = diversity-focused (Entropy dominates overall score).
                Default 0.3 balances NDCG 52%, Entropy 18%, Coverage 30%.
            known_context: What the researcher already knows about the topic.
                Passed to Φ4 (pre-search ranking) to improve EFE epistemic novelty scoring.
            progress_callback: Optional callback for real-time progress notifications.
                Called as progress_callback(phase_name, detail_dict) at each Phase boundary.
                Enables Perplexity-style "Thinking UI" transparency.
            interaction_callback: Optional callback for AI-to-AI interactive research.
                Called at each CoT iteration with the ReasoningStep. Returns optional
                guidance string to inject into the next iteration, or None to continue.

        Returns:
            ResearchReport with all phases completed.
        """
        start = time.monotonic()

        # Helper for progress notifications (no-op if callback is None)
        def _notify(phase: str, label: str | None = None, **detail):
            if progress_callback:
                try:
                    from mekhane.periskope.models import ProgressEvent
                    event = ProgressEvent(
                        phase=phase,
                        label=label,
                        detail=detail,
                        elapsed=round(time.monotonic() - start, 1),
                    )
                    progress_callback(event)
                except Exception:  # noqa: BLE001
                    pass  # Never let callback errors break the pipeline
        enabled = set(sources or [
            "searxng", "brave", "tavily", "semantic_scholar",
            "arxiv", "openalex", "github",
            "gemini_search", "vertex_search",
            "stackoverflow", "reddit", "hackernews",
            "gnosis", "sophia", "kairos",
            "vector_search_ann",
        ])

        # Φ0.5: Task Decomposition — split compound queries into sub-tasks
        if depth >= 3 and not getattr(self, "_in_subtask", False):
            try:
                from mekhane.periskope.cognition.phi0_task_decompose import (
                    decompose_query, synthesize_subtask_results,
                )
                _notify("phi_0_5_start", label="Task Decomposition", query=query)
                subtasks = await decompose_query(query, max_subtasks=3)
                if subtasks:
                    _notify("phi_0_5_decomposed", subtasks=[
                        {"focus": s.focus, "query": s.query[:80]} for s in subtasks
                    ])
                    logger.info(
                        "Φ0.5: Compound query decomposed into %d subtasks", len(subtasks),
                    )
                    # Execute sub-researches in parallel
                    self._in_subtask = True
                    try:
                        async def run_subtask(i, st):
                            _notify("subtask_start", index=i + 1, total=len(subtasks),
                                    focus=st.focus, query=st.query[:80])
                            # Wrap callback to prefix subtask phases
                            sub_cb = None
                            if progress_callback:
                                subtask_idx = i + 1
                                def _make_sub_cb(idx):
                                    def _sub_cb(event):
                                        event.phase = f"subtask[{idx}]/{event.phase}"
                                        progress_callback(event)
                                    return _sub_cb
                                sub_cb = _make_sub_cb(subtask_idx)
                            
                            # Create a new engine instance to avoid state corruption during parallel execution
                            sub_engine = self._clone_for_subtask()
                            
                            sub_report = await sub_engine.research(
                                query=st.query,
                                sources=list(enabled),
                                depth=max(1, depth - 1),
                                expand_query=expand_query,
                                known_context=known_context,
                                llm_rerank=llm_rerank,
                                progress_callback=sub_cb,
                            )
                            _notify("subtask_done", index=i + 1, results=len(sub_report.search_results))
                            return st, sub_report

                        subtask_reports = await asyncio.gather(
                            *[run_subtask(i, st) for i, st in enumerate(subtasks)]
                        )
                    finally:
                        self._in_subtask = False

                    # Synthesize all subtask results
                    if subtask_reports:
                        _notify("subtask_synthesis_start", count=len(subtask_reports))
                        unified_text = await synthesize_subtask_results(
                            query, subtask_reports,
                        )
                        # Use the last subtask's report as base, override synthesis
                        base_report = subtask_reports[-1][1]
                        # Merge all search results
                        all_results = []
                        all_counts: dict[str, int] = {}
                        for _, r in subtask_reports:
                            all_results.extend(r.search_results)
                            for k, v in r.source_counts.items():
                                all_counts[k] = all_counts.get(k, 0) + v

                        from mekhane.periskope.models import SynthModel, SynthesisResult
                        elapsed = time.monotonic() - start
                        return ResearchReport(
                            query=query,
                            search_results=all_results,
                            synthesis=[SynthesisResult(
                                model=SynthModel.GEMINI_PRO,
                                content=unified_text,
                                confidence=0.8,
                            )],
                            citations=base_report.citations,
                            divergence=base_report.divergence,
                            decision_frame=base_report.decision_frame,
                            elapsed_seconds=elapsed,
                            source_counts=all_counts,
                            quality_metrics=base_report.quality_metrics,
                            reasoning_trace=base_report.reasoning_trace,
                        )
            except ImportError:
                logger.debug("Φ0.5: task_decomposer not available, skipping")
            except Exception as e:  # noqa: BLE001
                logger.warning("Φ0.5: Task decomposition failed, continuing with single query: %s", e)

        # F1: Φ5 Action Plan — centralized search parameter configuration
        from mekhane.periskope.cognition.phi5_action_plan import phi5_action_plan
        action_plan = phi5_action_plan(
            depth=depth, multipass=multipass, source_count=len(enabled),
        )
        original_max = self.max_results
        self.max_results = max(self.max_results, action_plan.max_results_per_source)


        # Phase 0: Cognitive query expansion (Φ1-Φ4)
        _notify("phase_0_start", label="Cognitive Expansion", query=query, depth=depth)
        queries, context_plan, source_adapted = await self._phase_cognitive_expand(
            query, depth, expand_query, enabled, known_context=known_context,
        )
        phase0_elapsed = time.monotonic() - start
        _notify("phase_0_done", label="Cognitive Expansion", queries=len(queries), elapsed=round(phase0_elapsed, 1))

        # Phase 1: Parallel search (Φ6)
        # F1: Entity-based source routing — expand enabled sources
        if self.nl_client and self._nl_entity_cache.get(query):
            try:
                from mekhane.ochema.nl_client import suggest_sources
                suggested = suggest_sources(self._nl_entity_cache[query])
                # P2: Only add sources that have available searchers
                available_sources = {s for s in suggested if hasattr(self, s.replace('-', '_')) 
                                     and getattr(getattr(self, s.replace('-', '_'), None), 'available', False)}
                new_sources = available_sources - enabled
                if new_sources:
                    enabled = enabled | new_sources
                    logger.info("F1: Entity-routed sources added: %s", sorted(new_sources))
            except Exception as e:  # noqa: BLE001
                logger.debug("F1: Source routing failed: %s", e)

        _notify("phase_1_start", label="Parallel Search", sources=sorted(enabled), query_count=len(queries))
        extra_queries = queries[1:] if len(queries) > 1 else []
        extra_queries = self._build_site_scoped_queries(
            query, extra_queries, context_plan, enabled,
        )
        search_results, source_counts = await self._phase_search(
            query, enabled, extra_queries=extra_queries or None,
        )
        _notify("phase_1_done", label="Parallel Search", results=len(search_results), sources=dict(source_counts))

        # Phase 1.5-1.75: Filter pipeline
        _notify("phase_1_5_start", label="Filter & Rerank", input_count=len(search_results))
        search_results, pre_rerank_results = await self._phase_filter(
            query, search_results, depth, llm_rerank=llm_rerank,
        )
        _notify("phase_1_5_done", label="Filter & Rerank", filtered_count=len(search_results))

        # Phase 1.9: Fallback (信号不足時の段階的緩和)
        if len(search_results) < self._min_results_threshold(depth):
            from mekhane.periskope.fallback_controller import execute_fallback
            _notify("phase_1_9_start", label="Fallback Recovery",
                    results=len(search_results))
            fallback = await execute_fallback(
                engine=self, query=query,
                initial_results=pre_rerank_results,
                enabled_sources=enabled, depth=depth,
                config=self._config,
                progress_callback=progress_callback,
            )
            if fallback.search_results:
                # フォールバック結果を既存結果にマージ
                search_results = list(search_results) + fallback.search_results
                for src, cnt in fallback.source_counts.items():
                    source_counts[src] = source_counts.get(src, 0) + cnt
                # マージ後に Dedup/Rerank を再適用
                # (Stage 2/3 は _phase_search の生データなので品質パイプラインが未通過)
                search_results, _ = await self._phase_filter(
                    query, search_results, depth, llm_rerank=llm_rerank,
                )
                logger.info(
                    "Fallback post-filter: %d results after dedup/rerank",
                    len(search_results),
                )
                # W-1: フォールバック実行済みフラグ (Adaptive Depth 抑制)
                self._fallback_executed = True
            _notify("phase_1_9_done", label="Fallback Recovery",
                    results=len(search_results),
                    stages=fallback.stages_executed)

            if not search_results:
                logger.warning("Fallback exhausted — no results for %r", query)
                return ResearchReport(
                    query=query,
                    elapsed_seconds=time.monotonic() - start,
                    source_counts=source_counts,
                )

        # Phase 1.8: Deep-read (W7)
        if depth >= 2:
            _notify("phase_1_8_start", label="Deep Read", candidates=len(search_results))
            search_results = await self._phase_deep_read(
                query, search_results, depth,
            )
            _notify("phase_1_8_done", label="Deep Read", enriched=len([r for r in search_results if r.content and len(r.content) > 500]))

        # Phase 2: Multi-model synthesis
        from mekhane.periskope.synthesizer import models_for_depth
        if not self.synthesizer.synth_models:
            self.synthesizer.synth_models = models_for_depth(depth)
        model_names = [m.value for m in self.synthesizer.synth_models]
        _notify("phase_2_start", label="Multi-model Synthesis", models=model_names, results=len(search_results))
        logger.info(
            "Phase 2: Multi-model synthesis (%d results, depth=L%d, models=%s)",
            len(search_results), depth, model_names,
        )
        synthesis = await self.synthesizer.synthesize(query, search_results)
        divergence = self.synthesizer.detect_divergence(synthesis)
        _notify("phase_2_done", label="Multi-model Synthesis", synthesis_count=len(synthesis))

        # Phase 2.5: CoT Search Chain (iterative deepening)
        # depth>=2 enables reasoning trace; iterations controlled by config
        # Gate: search_results is sufficient — synthesis may fail on first pass
        # but CoT iterations will re-synthesize with accumulated results.
        if depth >= 2 and search_results:
            if not synthesis:
                logger.warning(
                    "Phase 2.5: synthesis empty but search_results=%d — "
                    "proceeding with CoT (will re-synthesize in-loop)",
                    len(search_results),
                )
                # Bootstrap minimal synthesis from search results so CoT can reason
                synthesis = await self.synthesizer.synthesize(query, search_results[:10])
            _notify("phase_2_5_start", label="CoT Search Chain", depth=depth)
            search_results, source_counts, synthesis, divergence = (
                await self._phase_iterative_deepen(
                    query, search_results, source_counts, synthesis,
                    enabled, depth,
                    progress_callback=progress_callback,
                    interaction_callback=interaction_callback,
                    llm_rerank=llm_rerank,
                )
            )
            _notify("phase_2_5_done", label="CoT Search Chain", total_results=len(search_results))

        # Phase 3: Citation verification
        _notify("phase_3_start", label="Citation Verification")
        citations = await self._phase_cite(
            synthesis, search_results,
        )
        _notify("phase_3_done", label="Citation Verification", citations=len(citations))

        elapsed = time.monotonic() - start
        logger.info("Research complete in %.1fs", elapsed)

        # VISION §1: 計画8割 — Phase 0 比率計測
        planning_ratio = phase0_elapsed / elapsed if elapsed > 0 else 0.0
        logger.info(
            "VISION Planning Ratio: %.1f%% (Phase 0: %.1fs / Total: %.1fs)",
            planning_ratio * 100, phase0_elapsed, elapsed,
        )
        self._log_phase_timing(query, depth, phase0_elapsed, elapsed)

        # Phase 3.5: Φ4 convergent framing + quality metrics
        _notify("phase_3_5_start", label="Decision Frame & Quality")
        decision_frame = await self._phase_decision_frame(
            query, synthesis, depth,
        )
        quality = self._compute_and_log_quality(
            query, search_results, source_counts,
            pre_rerank_results, elapsed,
            diversity_weight=diversity_weight,
        )
        _notify("phase_3_5_done", label="Decision Frame & Quality", quality_score=round(quality.overall_score, 2) if quality else None)

        # Φ7: Belief update + G2: Adaptive Depth
        adaptive_threshold = self._config.get("adaptive_depth_threshold", 0.5)
        belief_update = None
        if depth >= 2 and quality is not None:
            belief_update = await self._phase_belief_update(
                query, search_results, source_counts,
                synthesis, quality, adaptive_threshold,
            )

        if (
            quality is not None
            and quality.overall_score < adaptive_threshold
            and depth < 3
            and not getattr(self, "_adaptive_retry", False)
            and not getattr(self, "_fallback_executed", False)
        ):
            new_depth = depth + 1
            logger.info(
                "Adaptive Depth: quality %.0f%% < %.0f%% threshold, "
                "escalating L%d → L%d",
                quality.overall_score * 100,
                adaptive_threshold * 100,
                depth, new_depth,
            )
            self.max_results = original_max
            self._adaptive_retry = True
            try:
                return await self.research(
                    query=query, sources=list(enabled),
                    auto_digest=auto_digest, digest_depth=digest_depth,
                    expand_query=expand_query, multipass=multipass,
                    depth=new_depth, known_context=known_context,
                    llm_rerank=llm_rerank,
                    progress_callback=progress_callback,
                    interaction_callback=interaction_callback,
                )
            finally:
                self._adaptive_retry = False

        report = ResearchReport(
            query=query,
            search_results=search_results,
            synthesis=synthesis,
            citations=citations,
            divergence=divergence,
            decision_frame=decision_frame,
            elapsed_seconds=elapsed,
            source_counts=source_counts,
            quality_metrics=quality,
            reasoning_trace=self._reasoning_trace,
            belief_update=belief_update,
            planning_ratio=planning_ratio,
        )

        _notify("research_complete", elapsed=round(elapsed, 1), results=len(search_results),
                synthesis_count=len(synthesis), quality=round(quality.overall_score, 2) if quality else None)

        # Phase 4: Φ7 Doxa — Knowledge persistence via /eat pipeline (VISION §2.2)
        if auto_digest and synthesis:
            logger.info("Φ7 Doxa: Auto-digest → incoming/ (depth=%s)", digest_depth)
            digest_path = self._phase_digest(report, depth=digest_depth)
            if digest_path:
                logger.info("  Φ7 → /eat: %s", digest_path)

        return report

    # ── Phase sub-methods ──────────────────────────────────────

    # PURPOSE: [L2-auto] _phase_cognitive_expand の非同期処理定義
    async def _phase_cognitive_expand(
        self,
        query: str,
        depth: int,
        expand_query: bool,
        enabled: set[str],
        known_context: str = "",
    ) -> tuple[list[str], object | None, object | None]:
        """Phase 0: Cognitive query expansion (Φ0-Φ4 pre-search).

        Returns:
            (expanded_queries, context_plan, source_adapted_queries)
        """
        blind_spot_queries: list[str] = []
        counterfactual_queries: list[str] = []
        # D1: Φ1 blind-spot is always-on (VISION §2.1)
        # D2: Include past search history for differential blind-spot detection
        past_context = known_context or ""
        try:
            from mekhane.periskope.research_tracker import list_tracks
            tracks = list_tracks()
            past_queries: list[str] = []
            for t in tracks:
                past_queries.extend(h.get("query", "") for h in t.depth_history[-5:])
            if past_queries:
                past_context += "\nPrevious searches: " + "; ".join(past_queries[-10:])
        except Exception as e:  # noqa: BLE001
            # D2 Fix: Avoid silent failure. Log at debug level if tracker fails.
            logger.debug("Could not load research_tracker context for Φ1: %s", e)

        # NL API Entity Extraction (Φ0.5) — moved BEFORE Φ1 for KG disambiguation (F3)
        entity_queries: list[str] = []
        entities: list = []
        if self.nl_client and self._nl_call_count < self._nl_max_calls:
            try:
                max_entities = self.cloud_nl_cfg.get("max_entities", 10)
                salience_threshold = self.cloud_nl_cfg.get("salience_threshold", 0.3)
                high_salience_threshold = self.cloud_nl_cfg.get("high_salience_threshold", 0.5)
                entities = await asyncio.to_thread(
                    self.nl_client.analyze_entities, query, "", max_entities
                )
                self._nl_call_count += 1
                self._nl_entity_cache[query] = entities

                for e in entities:
                    if e.salience >= high_salience_threshold:
                        # F2: High salience → independent query (worth searching alone)
                        entity_queries.append(e.name)
                    elif e.salience >= salience_threshold:
                        # F2: Medium salience → contextual query (combine with original)
                        entity_queries.append(f"{query} {e.name}")

                if entity_queries:
                    logger.info(
                        "Φ0.5 [NL API]: %d entity queries (high: %d, ctx: %d) from %d entities",
                        len(entity_queries),
                        sum(1 for e in entities if e.salience >= high_salience_threshold),
                        sum(1 for e in entities if salience_threshold <= e.salience < high_salience_threshold),
                        len(entities),
                    )

                # F3: Inject KG metadata into blind-spot context for disambiguation
                kg_parts: list[str] = []
                for e in entities:
                    if e.metadata:
                        wiki = e.metadata.get("wikipedia_url", "")
                        mid = e.metadata.get("mid", "")
                        kg_parts.append(f"{e.name} ({e.type}, wiki={wiki}, mid={mid})")
                    elif e.salience >= salience_threshold:
                        kg_parts.append(f"{e.name} ({e.type}, salience={e.salience:.2f})")
                if kg_parts:
                    past_context += "\nKG Entities: " + "; ".join(kg_parts)
                    logger.info("F3: %d KG entities injected into Φ1 context", len(kg_parts))
            except Exception as e:  # noqa: BLE001
                logger.warning("NL API extraction failed: %s", e)

        # Φ0: Intent Decomposition — V1 基底射 (2026-02-28 /noe+ 導出)
        # Decomposes query into core concepts, evidence type, assumptions,
        # perspectives, and negation queries. Results enrich all downstream Φ phases.

        # Φ0 Pre-gate: Query Structuring — 全クエリを調査依頼書形式に構造化
        # MCP 層の構造化との二重防御。engine 層は depth >= 2 のみ。
        if depth >= 2:
            try:
                from mekhane.periskope.cognition.phi0_query_fortifier import (
                    fortify_query,
                )
                logger.info("Φ0 Pre-gate: Structuring query: %r", query[:80])
                fortified = await fortify_query(query, known_context or "")
                if fortified != query:
                    logger.info("Φ0 Pre-gate: Query structured → %r", fortified[:120])
                    query = fortified
            except Exception as e:  # noqa: BLE001
                logger.warning("Φ0 Pre-gate structuring skipped: %s", e)

        intent: IntentDecomposition | None = None
        if depth >= 2:
            try:
                intent = await phi0_intent_decompose(query, context=past_context)
                if intent and intent.core_concepts:
                    # Inject structured intent into Φ1 context
                    past_context += "\n" + intent.to_context_string()
                    logger.info(
                        "Φ0: Intent decomposed — %d concepts, evidence=%r",
                        len(intent.core_concepts),
                        intent.evidence_type[:50] if intent.evidence_type else "(none)",
                    )
            except Exception as e:  # noqa: BLE001
                logger.warning("Φ0 intent decomposition failed: %s", e)

        # Store V1 result for V5 CoT feedback (phi7_query_feedback)
        self._intent = intent

        # Φ0: Query Plan — V2 先読み連鎖 (2026-02-28 /noe+ 導出)
        # Plans 3-step search strategy (survey → analysis → verification)
        # Step 1 queries are added as immediate candidates.
        # Steps 2-3 are stored for CoT Chain's initial direction.
        query_plan: QueryPlan | None = None
        if depth >= 2:
            try:
                intent_ctx = intent.to_context_string() if intent and intent.core_concepts else ""
                query_plan = await phi0_query_plan(
                    query, context=past_context, intent_context=intent_ctx,
                )
                if query_plan and query_plan.step1_survey:
                    logger.info(
                        "Φ0 QueryPlan: %d step1 + %d step2 + %d step3 queries",
                        len(query_plan.step1_survey),
                        len(query_plan.step2_analysis),
                        len(query_plan.step3_verification),
                    )
            except Exception as e:  # noqa: BLE001
                logger.warning("Φ0 query planning failed: %s", e)

        # Store V2 result for V5 CoT feedback (phi7_query_feedback)
        self._query_plan = query_plan

        try:
            blind_spot_queries = await phi1_blind_spot_analysis(query, context=past_context)
            if blind_spot_queries:
                logger.info("Φ1: %d blind-spot queries", len(blind_spot_queries))
        except Exception as e:  # noqa: BLE001
            logger.warning("Φ1 blind-spot failed: %s", e)

        if depth >= 2:
            try:
                counterfactual_queries = await phi1_counterfactual_queries(query)
                if counterfactual_queries:
                    logger.info("Φ1: %d counterfactual queries", len(counterfactual_queries))
            except Exception as e:  # noqa: BLE001
                logger.warning("Φ1 counterfactual failed: %s", e)

        # W3: Bilingual query expansion
        queries = [query]

        if expand_query:
            try:
                queries = await self.query_expander.expand(query)
                if len(queries) > 1:
                    logger.info("W3: Query expanded to %d variants", len(queries))
            except Exception as e:  # noqa: BLE001
                logger.warning("W3 expansion failed, using original: %s", e)

        # Merge Φ0 negation queries + Φ0 plan step1 + Φ1 queries
        negation_queries = []
        if intent and intent.negation_queries:
            negation_queries = intent.negation_queries
        plan_step1 = query_plan.step1_as_candidates() if query_plan else []
        all_phi01 = blind_spot_queries + counterfactual_queries + entity_queries + negation_queries + plan_step1
        if all_phi01:
            existing = {q.lower() for q in queries}
            for bq in all_phi01:
                if bq.lower() not in existing:
                    queries.append(bq)
                    existing.add(bq.lower())

        # Φ2: Divergent thinking
        if depth >= 2:
            try:
                divergent_candidates = await phi2_divergent_thinking(
                    query,
                    expanded_queries=queries[1:],
                    max_candidates=8 if depth >= 3 else 5,
                    depth=depth,
                )
                existing = {q.lower() for q in queries}
                for dc in divergent_candidates:
                    if dc.lower() not in existing:
                        queries.append(dc)
                        existing.add(dc.lower())
                logger.info("Φ2: %d total candidates after divergent thinking", len(queries))
            except Exception as e:  # noqa: BLE001
                logger.warning("Φ2 divergent thinking failed: %s", e)

        # Φ3: Context setting
        context_plan = None
        if depth >= 2:
            try:
                context_plan = await phi3_context_setting(
                    query,
                    candidates=queries,
                    available_sources=list(enabled),
                    site_scoped_domains=self._config.get("site_scoped_domains", []),
                )
            except Exception as e:  # noqa: BLE001
                logger.warning("Φ3 context setting failed: %s", e)

        # Φ4: Pre-search convergent ranking
        if depth >= 2 and len(queries) > 1:
            try:
                ranked_queries = await phi4_pre_search_ranking(
                    query, queries, max_queries=5, known_context=known_context,
                )
                if ranked_queries:
                    queries = [rq.query for rq in ranked_queries]
                    logger.info(
                        "Φ4: Ranked %d candidates, top score=%.2f",
                        len(ranked_queries),
                        ranked_queries[0].score if ranked_queries else 0,
                    )
            except Exception as e:  # noqa: BLE001
                logger.warning("Φ4 pre-search ranking failed: %s", e)

        # Φ0: Source Adaptation — V3 ソース適応 (2026-02-28 /noe+ 導出)
        # Transforms queries for each source's characteristics.
        # Uses Φ3 query_type + V1 core_concepts. Rule-based, no LLM call.
        source_adapted: SourceAdaptedQueries | None = None
        if context_plan and depth >= 2:
            try:
                core_concepts = intent.core_concepts if intent else None
                source_adapted = phi0_source_adapt(
                    query,
                    query_type=context_plan.query_type,
                    core_concepts=core_concepts,
                    enabled_sources=enabled,
                )
                if source_adapted and source_adapted.has_adaptations():
                    logger.info(
                        "Φ0 SourceAdapt: %d source-specific variants",
                        len(source_adapted.adapted),
                    )
            except Exception as e:  # noqa: BLE001
                logger.warning("Φ0 source adaptation failed: %s", e)

        return queries, context_plan, source_adapted

    # PURPOSE: [L2-auto] _build_site_scoped_queries の関数定義
    def _build_site_scoped_queries(
        self,
        query: str,
        extra_queries: list[str],
        context_plan: object | None,
        enabled: set[str],
    ) -> list[str]:
        """G4: Build site-scoped queries from Φ3 plan or config."""
        if context_plan and hasattr(context_plan, 'site_scoped_queries') and context_plan.site_scoped_queries:
            for sq in context_plan.site_scoped_queries:
                if sq not in extra_queries:
                    extra_queries.append(sq)
            logger.info("G4 (Φ3): %d site-scoped queries", len(context_plan.site_scoped_queries))
        else:
            site_scoped_domains = self._config.get("site_scoped_domains", [
                "qiita.com", "zenn.dev", "b.hatena.ne.jp",
            ])
            if site_scoped_domains and "searxng" in enabled:
                for domain in site_scoped_domains:
                    site_query = f"{query} site:{domain}"
                    if site_query not in extra_queries:
                        extra_queries.append(site_query)
                logger.info("G4: Added %d site-scoped queries", len(site_scoped_domains))
        return extra_queries

    # PURPOSE: [L2-auto] _min_results_threshold の関数定義
    def _min_results_threshold(self, depth: int) -> int:
        """Depth 別の最小結果数閾値。フォールバック判定に使用。"""
        fallback_cfg = self._config.get("fallback", {})
        thresholds = fallback_cfg.get(
            "min_results_by_depth", {1: 1, 2: 3, 3: 5},
        )
        return thresholds.get(depth, thresholds.get(2, 3))

    # PURPOSE: [L2-auto] _phase_filter の非同期処理定義
    async def _phase_filter(
        self,
        query: str,
        search_results: list[SearchResult],
        depth: int,
        llm_rerank: bool | None = None,
    ) -> tuple[list[SearchResult], list[SearchResult]]:
        """Phase 1.5-1.75: Dedup → Rerank → Quality filter.

        Returns:
            (filtered_results, pre_rerank_results)
        """
        # Phase 1.5: Dedup
        if search_results:
            before = len(search_results)
            search_results = self._deduplicate_results(search_results)
            if len(search_results) < before:
                logger.info("  Dedup: %d → %d results", before, len(search_results))

        # Phase 1.7: Semantic reranking (W4) + LLM Cascade
        pre_rerank_results = list(search_results) if search_results else []
        if search_results:
            search_results = self._rerank_results(query, search_results)
            search_results = await self._llm_rerank_results(
                query, search_results, depth=depth, override_enabled=llm_rerank
            )

        # Phase 1.75: Quality filter
        if search_results:
            blocklist = set(self._config.get("domain_blocklist", []))
            if blocklist:
                before = len(search_results)
                search_results = [
                    r for r in search_results
                    if not r.url or not any(
                        domain in (r.url or "").lower()
                        for domain in blocklist
                    )
                ]
                blocked = before - len(search_results)
                if blocked:
                    logger.info("Phase 1.75a: Blocked %d blocklisted", blocked)

            min_relevance = self._config.get("relevance_threshold", 0.25)
            before = len(search_results)
            search_results = [r for r in search_results if r.relevance >= min_relevance]
            filtered = before - len(search_results)
            if filtered:
                logger.info("Phase 1.75b: Filtered %d low-relevance (threshold=%.2f)", filtered, min_relevance)

        return search_results, pre_rerank_results

    # PURPOSE: [L2-auto] _phase_deep_read の非同期処理定義
    async def _phase_deep_read(
        self,
        query: str,
        search_results: list[SearchResult],
        depth: int,
    ) -> list[SearchResult]:
        """Phase 1.8: W7 Summary→Full-text selective crawl."""
        try:
            deep_read_urls = await self._select_urls_for_deep_read(
                query, search_results, depth=depth,
            )
            if deep_read_urls:
                logger.info("Phase 1.8: Deep-reading %d URLs", len(deep_read_urls))
                fetched = await self.page_fetcher.fetch_many(deep_read_urls)
                enriched = 0
                for r in search_results:
                    if r.url and r.url in fetched:
                        r.content = fetched[r.url]
                        enriched += 1
                if enriched:
                    logger.info("Phase 1.8: Enriched %d results", enriched)
        except Exception as e:  # noqa: BLE001
            logger.warning("Phase 1.8 (deep-read) failed: %s", e)
        return search_results

    # PURPOSE: [L2-auto] _phase_iterative_deepen の非同期処理定義
    async def _phase_iterative_deepen(
        self,
        query: str,
        search_results: list[SearchResult],
        source_counts: dict[str, int],
        synthesis: list,
        enabled: set[str],
        depth: int,
        progress_callback: 'ProgressCallback | None' = None,
        interaction_callback: 'Callable[[object], str | None] | None' = None,
        llm_rerank: bool | None = None,
    ) -> tuple[list[SearchResult], dict[str, int], list, object | None]:
        """Phase 2.5: CoT Search Chain — iterative deepening with reasoning trace.

        Each iteration builds on accumulated knowledge (CoT-in-Search):
          1. Analyze current synthesis + prior reasoning trace (LLM)
          2. Extract learned facts, contradictions, gaps, next queries
          3. Execute targeted searches from reasoning-derived queries
          4. Merge & rerank results
          5. Re-synthesize
          6. Measure information gain (Embedding novelty)
          7. Update reasoning trace
          8. Stop if gain < threshold OR confidence > threshold

        Config keys (config.yaml → iterative_deepening):
          max_iterations: {depth: max_rounds}
          saturation_threshold: float (0.0–1.0)
          queries_per_iteration: int
          log_gain_curve: bool

        Returns:
            (search_results, source_counts, synthesis, divergence)
        """
        # Load config
        iter_config = self._config.get("iterative_deepening", {})
        max_iter_map = iter_config.get("max_iterations", {1: 1, 2: 3, 3: 5})
        max_iterations = max_iter_map.get(depth, max_iter_map.get(2, 3))
        # Minimum guaranteed iterations before early-stop checks
        min_iter_map = iter_config.get("min_iterations", {1: 1, 2: 2, 3: 3})
        min_iterations = min_iter_map.get(depth, min_iter_map.get(2, 2))
        saturation_threshold = iter_config.get("saturation_threshold", 0.02)
        queries_per_iter = iter_config.get("queries_per_iteration", 2)
        log_gain = iter_config.get("log_gain_curve", True)

        # Apply depth-adaptive max_results
        depth_max = self._max_results_by_depth.get(depth)
        if depth_max:
            self.max_results = depth_max
            logger.info("Depth-adaptive max_results: L%d → %d", depth, depth_max)

        divergence = self.synthesizer.detect_divergence(synthesis)
        gain_history: list[dict] = []  # For sweet-spot experimentation
        cumulative_gain = 0.0  # For relative gain saturation check

        if max_iterations <= 0:
            return search_results, source_counts, synthesis, divergence

        logger.info(
            "Phase 2.5: CoT Search Chain (max=%d, threshold=%.2f, depth=L%d)",
            max_iterations, saturation_threshold, depth,
        )

        # Initialize reasoning trace — the CoT chain for search
        trace = ReasoningTrace(query=query)

        # Snapshot synthesis text for information gain comparison
        prev_synth_text = "\n".join(s.content[:2000] for s in synthesis[:2]) if synthesis else ""

        # F5: Entity novelty initialization
        prev_entities: list = []
        if self.nl_client and prev_synth_text:
            try:
                prev_entities = await asyncio.to_thread(self.nl_client.analyze_entities, prev_synth_text[:5000], "", 15)
            except Exception as e:  # noqa: BLE001
                logger.debug("F5 initial entity extraction failed: %s", e)

        # Initialize KalonDetector (Good-Turing saturation)
        # depth=1 → L1, depth=2 → L2, depth=3 → L3
        kalon_level = f"L{min(3, depth)}"
        kalon_detector = KalonDetector(level=kalon_level)

        # T4: Denoising scheduler parameters
        iter_config = self._config.get("iterative_deepening", {})
        
        initial_diversity = iter_config.get("initial_diversity_weight", 0.3)
        decay_type = self.decay_type_override or iter_config.get("decay_type", "linear")
        alpha_schedule = self.alpha_schedule_override or iter_config.get("alpha_schedule", "cosine")  # independent of decay_type
        initial_max_results = self.max_results  # e.g., 10
        final_max_results = max(3, initial_max_results // 3)  # e.g., 3

        try:
            for iteration in range(max_iterations):
                # T4: Denoising schedule — reduce entropy as iterations progress
                # t ∈ [0, 1]: progress ratio through iterations
                t = iteration / max(1, max_iterations - 1)
                
                if decay_type == "cosine":
                    # Cosine schedule (Nichol & Dhariwal 2021, DDPM improved)
                    # decay = 0.5 * (1 + cos(π * t)): slow start, fast mid, slow end
                    import math
                    decay_factor = 0.5 * (1.0 + math.cos(math.pi * t))
                    iter_diversity = initial_diversity * decay_factor
                    iter_max_results = max(
                        final_max_results,
                        int(final_max_results + (initial_max_results - final_max_results) * decay_factor),
                    )
                elif decay_type == "logsnr":
                    # logSNR-focused schedule (Hang et al. ICCV 2025)
                    # Laplace decay centered at t=0.5 (logSNR=0 critical point)
                    # Concentrates resources where signal ≈ noise
                    import math
                    b = 0.3  # temperature: smaller = sharper focus on t=0.5
                    decay_factor = math.exp(-abs(2.0 * t - 1.0) / b)
                    iter_diversity = initial_diversity * decay_factor
                    iter_max_results = max(
                        final_max_results,
                        int(final_max_results + (initial_max_results - final_max_results) * decay_factor),
                    )
                elif decay_type == "exponential":
                    # Exponential decay: e^(-k * t) where k=3.0 (reaches ~5% at t=1)
                    import math
                    decay_factor = math.exp(-3.0 * t)
                    iter_diversity = initial_diversity * decay_factor
                    iter_max_results = max(
                        final_max_results,
                        int(final_max_results + (initial_max_results - final_max_results) * decay_factor),
                    )
                else:
                    # Linear decay (default)
                    iter_diversity = initial_diversity * (1.0 - t)
                    iter_max_results = max(
                        final_max_results,
                        int(initial_max_results - (initial_max_results - final_max_results) * t),
                    )
                if iteration > 0:
                    logger.info(
                        "Phase 2.5 [denoise]: t=%.2f, diversity=%.2f, max_results=%d",
                        t, iter_diversity, iter_max_results,
                    )

                # Progress notification per iteration
                if progress_callback:
                    try:
                        from mekhane.periskope.models import ProgressEvent
                        progress_callback(ProgressEvent(
                            phase="cot_iteration_start",
                            detail={
                                "iteration": iteration + 1,
                                "max_iterations": max_iterations,
                                "t": round(t, 2),
                            },
                        ))
                    except Exception:  # noqa: BLE001
                        pass

                # Step 1: CoT reasoning — analyze synthesis with accumulated trace
                current_synth = "\n".join(
                    s.content[:2000] for s in synthesis[:2]
                ) if synthesis else ""

                reasoning_step = await analyze_iteration(
                    query=query,
                    trace=trace,
                    current_synthesis=current_synth,
                    max_queries=queries_per_iter,
                )

                # Step 1.5: Compute objective info_gain (text-diff based)
                # Resolves depth=2 QPP quality asymmetry with depth=3
                _cot_info_gain = self._assess_information_gain(
                    prev_synth_text, current_synth,
                )
                self._last_info_gain = _cot_info_gain
                reasoning_step.info_gain = _cot_info_gain
                prev_synth_text = current_synth

                # Use reasoning-derived queries (CoT), enhanced by V5 feedback
                refinement_queries = reasoning_step.next_queries

                # V5: Feedback-enhanced refinement — merge V1 intent + V2 plan
                try:
                    # Get query_plan from Phase 0 (stored on self if available)
                    _plan = getattr(self, '_query_plan', None)
                    _intent = getattr(self, '_intent', None)
                    # Get coverage gaps from current iteration
                    _gaps = []
                    if search_results:
                        src_counts: dict[str, int] = {}
                        for r in search_results:
                            src = getattr(r, 'source', 'unknown')
                            src_counts[src] = src_counts.get(src, 0) + 1
                        _gaps = phi1_coverage_gaps(query, search_results, src_counts)

                    # Get previous iteration's info_gain for QPP gating
                    _prev_gain = getattr(self, '_last_info_gain', None)

                    feedback = phi7_query_feedback(
                        iteration=iteration + 1,
                        reasoning_next_queries=refinement_queries,
                        plan_step2=_plan.step2_analysis if _plan else None,
                        plan_step3=_plan.step3_verification if _plan else None,
                        unchecked_assumptions=_intent.implicit_assumptions if _intent else None,
                        coverage_gaps=_gaps,
                        search_perspectives=_intent.search_perspectives if _intent else None,
                        max_queries=queries_per_iter,
                        info_gain=_prev_gain,
                        saturation_threshold=saturation_threshold,
                    )
                    if feedback.queries:
                        refinement_queries = feedback.queries
                except Exception as e:  # noqa: BLE001
                    logger.debug("V5 feedback enhancement skipped: %s", e)

                if not refinement_queries:
                    # Fallback: try legacy gap detection
                    refinement_queries = await self._generate_refinement_queries(
                        query, synthesis, search_results,
                    )

                if not refinement_queries:
                    # min_iterations guard: don't stop before minimum
                    if iteration + 1 < min_iterations:
                        logger.info(
                            "Phase 2.5 [iter %d/%d]: No gaps but below min_iterations (%d) → continuing",
                            iteration + 1, max_iterations, min_iterations,
                        )
                        # Generate broader queries to push exploration
                        refinement_queries = [f"{query} recent advances", f"{query} challenges limitations"]
                    else:
                        logger.info(
                            "Phase 2.5 [iter %d/%d]: No gaps found → converged",
                            iteration + 1, max_iterations,
                        )
                        reasoning_step.info_gain = 0.0
                        trace.steps.append(reasoning_step)
                        gain_history.append({
                            "iteration": iteration + 1,
                            "info_gain": 0.0,
                            "new_results": 0,
                            "reason": "no_gaps",
                            "confidence": reasoning_step.confidence,
                            "v5_strategy": getattr(locals().get('feedback'), 'strategy', None),
                        })
                        break

                # Cap queries per iteration
                refinement_queries = refinement_queries[:queries_per_iter]

                logger.info(
                    "Phase 2.5 [iter %d/%d]: %d sub-queries: %s",
                    iteration + 1, max_iterations,
                    len(refinement_queries),
                    refinement_queries,
                )

                # Step 2: Execute additional searches (T4: narrowing max_results)
                new_result_count = 0
                # Temporarily adjust max_results for denoising
                original_max_results = self.max_results
                self.max_results = iter_max_results
                
                search_tasks = [self._phase_search(rq, enabled) for rq in refinement_queries]
                rq_results = await asyncio.gather(*search_tasks, return_exceptions=True)
                
                for idx, res in enumerate(rq_results):
                    if isinstance(res, Exception):
                        logger.warning("Phase 2.5 parallel search failed for %r: %s", refinement_queries[idx], res)
                        continue
                    extra_results, extra_counts = res
                    if extra_results:
                        extra_results = self._deduplicate_results(
                            search_results + extra_results,
                        )
                        existing_urls = {(r.url or "").lower() for r in search_results}
                        new_results = [
                            r for r in extra_results
                            if (r.url or "").lower() not in existing_urls
                        ]
                        search_results.extend(new_results)
                        new_result_count += len(new_results)
                        for k, v in extra_counts.items():
                            source_counts[k] = source_counts.get(k, 0) + v
                # Restore max_results
                self.max_results = original_max_results

                # Update KalonDetector with URL frequencies
                all_urls = [r.url for r in search_results if r.url]
                # Approximation of new URLs from this iteration
                new_urls = all_urls[-new_result_count:] if new_result_count > 0 else []
                # Record query intent. If multiple queries, join them as a pseudo-query for tracking
                kalon_query = " | ".join(refinement_queries)
                kalon_detector.update(iteration + 1, kalon_query, new_urls, all_urls)

                # Step 3: Rerank merged results
                if new_result_count > 0:
                    search_results = self._rerank_results(query, search_results)
                    search_results = await self._llm_rerank_results(
                        query, search_results, depth=depth, override_enabled=llm_rerank
                    )

                # Step 4: Deep-read new high-ranking results
                if depth >= 2 and new_result_count > 0:
                    search_results = await self._phase_deep_read(
                        query, search_results, depth,
                    )

                # Step 5: Re-synthesize with accumulated results
                # Adaptive Token Budgeting: use Kalon P(new) to set char budget
                _char_budget = compute_data_budget(kalon_detector.state)
                logger.debug(
                    "Adaptive budget: %d chars (P(new)=%.3f)",
                    _char_budget, kalon_detector.state.p_new,
                )
                synthesis = await self.synthesizer.synthesize(
                    query, search_results, char_budget=_char_budget,
                )
                divergence = self.synthesizer.detect_divergence(synthesis)

                # Step 5.3: Phase Inversion L1 — Advocatus Diaboli challenge
                # VISION §7: same operation (phase inversion) at step granularity
                pi_cfg = self._config.get("phase_inversion", {})
                l1_cfg = pi_cfg.get("l1", {})
                pi_enabled = pi_cfg.get("enabled", False)
                pi_min_depth = l1_cfg.get("min_depth", 1)

                if pi_enabled and depth >= pi_min_depth and synthesis:
                    try:
                        from mekhane.periskope.cognition.phase_inversion import (
                            advocatus_challenge,
                        )
                        current_synth_for_pi = "\n".join(
                            s.content[:2000] for s in synthesis[:2]
                        )
                        challenge = await advocatus_challenge(
                            query=query,
                            synthesis_text=current_synth_for_pi,
                            current_confidence=reasoning_step.confidence,
                            max_refutations=l1_cfg.get("max_refutations", 3),
                            max_counter_queries=l1_cfg.get("max_counter_queries", 2),
                            model=l1_cfg.get("model", "gemini-3-flash-preview"),
                        )
                        logger.info(
                            "Phase 2.5 [L1 phase inversion]: %s",
                            challenge.summary(),
                        )

                        # Record refutations in reasoning trace
                        reasoning_step.refutations = challenge.refutation_points

                        # Step 5.4: Execute counter-evidence searches
                        if challenge.counter_queries:
                            original_max_pi = self.max_results
                            self.max_results = max(3, iter_max_results)
                            for cq in challenge.counter_queries:
                                counter_results, counter_counts = (
                                    await self._phase_search(cq, enabled)
                                )
                                if counter_results:
                                    existing_urls = {
                                        (r.url or "").lower()
                                        for r in search_results
                                    }
                                    new_counter = [
                                        r for r in counter_results
                                        if (r.url or "").lower() not in existing_urls
                                    ]
                                    search_results.extend(new_counter)
                                    new_result_count += len(new_counter)
                                    for k, v in counter_counts.items():
                                        source_counts[k] = (
                                            source_counts.get(k, 0) + v
                                        )
                            self.max_results = original_max_pi

                            # Step 5.5a: Re-synthesize with counter-evidence
                            if new_result_count > 0:
                                _pi_char_budget = compute_data_budget(kalon_detector.state)
                                synthesis = await self.synthesizer.synthesize(
                                    query, search_results, char_budget=_pi_char_budget,
                                    system_instruction="Phase Inversion: Re-synthesize incorporating the counter-evidence.",
                                )
                                divergence = self.synthesizer.detect_divergence(
                                    synthesis,
                                )
                                logger.info(
                                    "Phase 2.5 [L1 re-synthesis]: "
                                    "integrated %d counter-evidence results",
                                    new_result_count,
                                )

                    except ImportError:
                        logger.debug("Phase inversion module not available")
                    except Exception as e:  # noqa: BLE001
                        logger.warning(
                            "Phase 2.5 [L1 phase inversion] failed: %s", e,
                        )

                # Step 5.5b: Contradiction-driven query injection (legacy, L3 only)
                # Uses contradictions already detected by analyze_iteration
                # (reasoning_trace.py L232-251) — no extra LLM call needed
                if (depth >= 3
                    and reasoning_step.contradictions
                    and 0.2 < t < 0.8):
                    contradiction_queries = [
                        f"resolve contradiction: {c[:200]}"
                        for c in reasoning_step.contradictions[:2]
                    ]
                    logger.info(
                        "Phase 2.5 [contradiction]: %d queries from %d contradictions",
                        len(contradiction_queries),
                        len(reasoning_step.contradictions),
                    )
                    fix_tasks = [self._phase_search(cq, enabled) for cq in contradiction_queries]
                    fix_res_list = await asyncio.gather(*fix_tasks, return_exceptions=True)
                    
                    for idx, res in enumerate(fix_res_list):
                        if isinstance(res, Exception):
                            logger.warning("Phase 2.5 contradiction search failed for %r: %s", contradiction_queries[idx], res)
                            continue
                        fix_results, fix_counts = res
                        if fix_results:
                            existing_urls = {
                                (r.url or "").lower() for r in search_results
                            }
                            new_fixes = [
                                r for r in fix_results
                                if (r.url or "").lower() not in existing_urls
                            ]
                            search_results.extend(new_fixes)
                            for k, v in fix_counts.items():
                                source_counts[k] = source_counts.get(k, 0) + v

                # Step 5.6: Shared Index — publish this iteration's findings
                # VISION §7 v2: dynamic mutual interaction via EphemeralIndex
                if self._shared_index is not None and self._role != "standalone":
                    try:
                        # Publish synthesis
                        synth_text = "\n".join(
                            s.content[:2000] for s in synthesis[:2]
                        ) if synthesis else ""
                        if synth_text:
                            await self._shared_index.publish(
                                source=self._role,
                                entry_type="synthesis",
                                text=synth_text,
                                metadata={
                                    "iteration": iteration + 1,
                                    "confidence": reasoning_step.confidence,
                                },
                            )
                        # Publish refutations
                        if reasoning_step.refutations:
                            for ref in reasoning_step.refutations[:3]:
                                await self._shared_index.publish(
                                    source=self._role,
                                    entry_type="refutation",
                                    text=ref,
                                )
                        logger.debug(
                            "Phase 2.5 [shared index publish]: %s iter %d",
                            self._role, iteration + 1,
                        )
                    except Exception as e:  # noqa: BLE001
                        logger.debug("Shared index publish failed: %s", e)

                # Step 5.7: Shared Index — query opponent's discoveries
                # LS-pattern: DialecticContextBuffer with depth-aware budget + LLM compression
                if self._shared_index is not None and self._role != "standalone":
                    try:
                        # Lazy-init context buffer with current depth
                        if self._dialectic_buffer is None:
                            from mekhane.periskope.cognition.context_compressor import DialecticContextBuffer
                            self._dialectic_buffer = DialecticContextBuffer(depth=depth)

                        opponent_query = query if not synthesis else (
                            "\n".join(s.content[:500] for s in synthesis[:1])
                        )
                        opponent_findings = await self._shared_index.query(
                            requesting_source=self._role,
                            query_text=opponent_query,
                            top_k=3,
                            exclude_own=True,
                        )
                        if opponent_findings:
                            # Append each finding to the context buffer
                            for entry, _score in opponent_findings:
                                self._dialectic_buffer.append(
                                    iteration=iteration + 1,
                                    source=entry.source,
                                    text=f"[{entry.entry_type}]: {entry.text[:500]}",
                                )

                            # Compress old entries if over budget (LS checkpoint pattern)
                            await self._dialectic_buffer.compress_if_needed()

                            logger.info(
                                "Phase 2.5 [shared index query]: %s got %d findings. Buffer: %s",
                                self._role, len(opponent_findings),
                                self._dialectic_buffer.stats(),
                            )
                    except Exception as e:  # noqa: BLE001
                        logger.debug("Shared index query failed: %s", e)

                # Step 6: Determine information gain (FEP: predictive error reduction)
                # Evaluate the *change* in synthesis content across iterations
                curr_synth_text = "\n".join(
                    s.content[:2000] for s in synthesis[:2]
                ) if synthesis else ""
                
                info_gain = self._assess_information_gain(
                    prev_synth_text, curr_synth_text,
                )
                
                # F5: Entity Novelty Score (P1: cost-guarded)
                if self.nl_client and curr_synth_text and self._nl_call_count < self._nl_max_calls:
                    try:
                        curr_entities = await asyncio.to_thread(
                            self.nl_client.analyze_entities, curr_synth_text[:5000], "", 15
                        )
                        self._nl_call_count += 1
                        entity_gain = self._entity_novelty(prev_entities, curr_entities)
                        if len(curr_entities) > 0:
                            logger.info(
                                "F5: Entity novelty=%.3f (prev: %d, curr: %d entities, calls: %d/%d)",
                                entity_gain, len(prev_entities), len(curr_entities),
                                self._nl_call_count, self._nl_max_calls,
                            )
                            # Blend embedding information gain and entity novelty
                            info_gain = (info_gain + entity_gain) / 2.0
                        prev_entities = curr_entities
                    except Exception as e:  # noqa: BLE001
                        logger.debug("F5 entity extraction failed: %s", e)

                # F6: Linkage L(c) 密度ベース情報利得 (linkage_hyphe.md §4)
                # 検索結果レベルの coherence/drift を info_gain に統合
                density_metrics = None
                try:
                    # 反復深化内で新たに追加された結果 = search_results の末尾 new_result_count 件
                    iter_results = search_results[-new_result_count:] if new_result_count > 0 else []
                    # #1修正: existing から new を除外して自己類似度バイアスを排除
                    existing_only = search_results[:-new_result_count] if new_result_count > 0 else search_results
                    density_metrics = self._compute_result_density(
                        new_results=iter_results,
                        existing_results=existing_only,
                    )
                    if density_metrics and density_metrics.get("density_gain") is not None:
                        density_gain = density_metrics["density_gain"]
                        # info_gain と density_gain の重み付きブレンド
                        info_gain = 0.7 * info_gain + 0.3 * density_gain
                        logger.info(
                            "F6: density_gain=%.3f (redundancy=%.3f, drift=%.3f) → blended info_gain=%.3f",
                            density_gain,
                            density_metrics.get("redundancy", 0),
                            density_metrics.get("drift", 0),
                            info_gain,
                        )
                except Exception as e:  # noqa: BLE001
                    logger.debug("F6 density calculation skipped: %s", e)

                # G∘F 収束追跡: density から drift/redundancy を KalonDetector に渡す
                _gf_drift = density_metrics.get("drift", 0.0) if density_metrics else 0.0
                _gf_redundancy = density_metrics.get("redundancy", 0.0) if density_metrics else 0.0
                kalon_detector.update_gf(drift=_gf_drift, redundancy=_gf_redundancy)

                # FEP: π↓ → sensory-driven (gain), π↑ → prediction-driven (relevance) score
                # (diffusion_cognition.md §4/§5.1: precision-weighted score)
                # FEP: π↓ → sensory-driven (gain), π↑ → prediction-driven (relevance)
                self._init_embedder()
                query_relevance = 0.0
                try:
                    if curr_synth_text and self._embedder is not None:
                        query_relevance = self._embedder.similarity(
                            query[:500], curr_synth_text[:2000],
                        )
                except Exception as e:  # noqa: BLE001
                    logger.debug("Score function relevance calculation failed: %s", e)
                # α schedule: explore/exploit balance (independent of β decay)
                # (diffusion_cognition.md §5.1: nonlinear schedule)
                import math
                alpha_min, alpha_max = 0.3, 0.7
                if alpha_schedule == "sigmoid":
                    # Asymmetric sigmoid: flat low → steep mid → flat high
                    # Wide range for aggressive explore/exploit separation
                    alpha_min, alpha_max = 0.15, 0.85
                    alpha = alpha_min + (alpha_max - alpha_min) / (1.0 + math.exp(-8.0 * (t - 0.5)))
                elif alpha_schedule == "linear":
                    alpha = alpha_min + (alpha_max - alpha_min) * t
                else:
                    # Cosine ramp (default): symmetric, slow start/end
                    alpha = alpha_min + (alpha_max - alpha_min) * (1.0 - math.cos(math.pi * t)) / 2.0
                conf = reasoning_step.confidence  # precision proxy
                denoising_score = alpha * query_relevance * conf + (1 - alpha) * info_gain

                # Step 7: Update reasoning trace
                reasoning_step.info_gain = info_gain
                self._last_info_gain = info_gain  # V5 QPP gating
                reasoning_step.new_results = new_result_count

                # Deduplicate learned facts using novelty against prior knowledge
                if reasoning_step.learned and trace.steps and self._embedder:
                    prior = trace.cumulative_knowledge
                    if prior and prior != "(No prior knowledge)":
                        deduped = []
                        for fact in reasoning_step.learned:
                            n = self._embedder.novelty(fact, prior[:2000])
                            if n > 0.15:  # Genuinely new information
                                deduped.append(fact)
                            else:
                                logger.debug(
                                    "Filtered duplicate learned: %.50s (novelty=%.3f)",
                                    fact, n,
                                )
                        # Keep at least 1 item to avoid empty learned
                        reasoning_step.learned = deduped if deduped else reasoning_step.learned[:1]

                trace.steps.append(reasoning_step)

                gain_entry = {
                    "iteration": iteration + 1,
                    "info_gain": round(info_gain, 4),
                    "query_relevance": round(query_relevance, 4),
                    "denoising_score": round(denoising_score, 4),
                    "alpha": round(alpha, 2),
                    "new_results": new_result_count,
                    "total_results": len(search_results),
                    "queries": refinement_queries,
                    "learned": len(reasoning_step.learned),
                    "contradictions": len(reasoning_step.contradictions),
                    "gaps": len(reasoning_step.gaps),
                    # F6: Linkage 密度メトリクス
                    "density": density_metrics,
                    "confidence": reasoning_step.confidence,
                    # T4: Denoising schedule state
                    "diversity_weight": round(iter_diversity, 3),
                    "max_results_per_source": iter_max_results,
                    # V5: QPP strategy selection
                    "v5_strategy": getattr(locals().get('feedback'), 'strategy', None),
                }

                # Relative gain: normalize info_gain by cumulative knowledge
                cumulative_gain += info_gain
                relative_gain = info_gain / max(cumulative_gain, 0.001)
                gain_entry["relative_gain"] = round(relative_gain, 4)

                gain_history.append(gain_entry)

                logger.info(
                    "Phase 2.5 [iter %d/%d]: +%d results, gain=%.3f, "
                    "relevance=%.3f, score=%.3f (α=%.2f), "
                    "learned=%d, gaps=%d, conf=%.0f%%, total=%d",
                    iteration + 1, max_iterations,
                    new_result_count, info_gain,
                    query_relevance, denoising_score, alpha,
                    len(reasoning_step.learned),
                    len(reasoning_step.gaps),
                    reasoning_step.confidence * 100,
                    len(search_results),
                )

                # Enhancement ⑤: AI-to-AI interactive research
                # Allow the calling LLM (Claude) to inject guidance into the next iteration
                if interaction_callback:
                    try:
                        guidance = interaction_callback(reasoning_step)
                        if guidance:
                            # Inject guidance as additional context for next iteration
                            trace.external_guidance = guidance
                            logger.info("Phase 2.5: Received external guidance (%d chars)", len(guidance))
                    except Exception as e:  # noqa: BLE001
                        logger.debug("Interaction callback failed: %s", e)

                # Progress notification per iteration completion
                if progress_callback:
                    try:
                        from mekhane.periskope.models import ProgressEvent
                        progress_callback(ProgressEvent(
                            phase="cot_iteration_done",
                            detail={
                                "iteration": iteration + 1,
                                "info_gain": round(info_gain, 4),
                                "confidence": round(reasoning_step.confidence, 2),
                                "new_results": new_result_count,
                                "queries": refinement_queries,
                            },
                        ))
                    except Exception:  # noqa: BLE001
                        pass

                # Step 8: Convergence check (info gain OR high confidence OR kalon)
                is_kalon, kalon_metrics = kalon_detector.is_kalon()
                # `kalon_metrics` を現在のイテレーションの記録として残す
                gain_entry["kalon_metrics"] = kalon_metrics
                if is_kalon:
                    logger.info(
                        "Phase 2.5: Kalon saturation reached (P(new)=%.4f < %.4f) → stopping",
                        kalon_metrics["p_new"], kalon_metrics["threshold"],
                    )
                    logger.info("\n" + kalon_detector.report())
                    gain_entry["reason"] = "kalon"
                    break

                # min_iterations guard: don't early-stop before minimum
                if iteration + 1 < min_iterations:
                    logger.info(
                        "Phase 2.5 [iter %d/%d]: Below min_iterations (%d) → skipping convergence check",
                        iteration + 1, max_iterations, min_iterations,
                    )
                elif info_gain < saturation_threshold:
                    logger.info(
                        "Phase 2.5: Information gain %.3f < threshold %.3f → saturated",
                        info_gain, saturation_threshold,
                    )
                    gain_entry["reason"] = "saturated"
                    logger.info("\n" + kalon_detector.report())
                    break
                elif reasoning_step.confidence >= 0.95:
                    logger.info(
                        "Phase 2.5: Confidence %.0f%% >= 95%% → high-confidence stop",
                        reasoning_step.confidence * 100,
                    )
                    gain_entry["reason"] = "high_confidence"
                    logger.info("\n" + kalon_detector.report())
                    break

                prev_synth_text = curr_synth_text

        except Exception as e:  # noqa: BLE001
            logger.warning("CoT Search Chain failed at iter %d: %s",
                           len(gain_history) + 1, e)

        # Log gain curve + reasoning trace
        if log_gain and gain_history:
            self._log_gain_curve(query, depth, gain_history)

        # Store trace on engine for report inclusion
        self._reasoning_trace = trace
        if trace.steps:
            logger.info(
                "Phase 2.5: CoT chain complete — %d iterations, "
                "final confidence=%.0f%%",
                len(trace.steps),
                trace.latest_confidence * 100,
            )

        return search_results, source_counts, synthesis, divergence

    # PURPOSE: [L2-auto] F5 エンティティ新奇性の評価
    @staticmethod
    def _entity_identity(entity) -> str:
        """Return a stable identity key for an entity.
        
        Priority: KG MID > normalized name. This prevents overcounting
        entities with variant spellings (e.g. 'Karl Friston' vs 'K. Friston')
        when they share the same Knowledge Graph MID.
        """
        mid = getattr(entity, 'metadata', {}).get('mid', '') if hasattr(entity, 'metadata') and entity.metadata else ''
        if mid:
            return f"mid:{mid}"
        # Normalize: lowercase + collapse whitespace
        import re
        return re.sub(r'\s+', ' ', entity.name.lower().strip())

    def _entity_novelty(self, prev_entities: list, curr_entities: list) -> float:
        """F5: Measure entity novelty between iterations.
        
        Uses MID-based identity when available, falling back to normalized names.
        Calculates the proportion of distinct new entities in the current synthesis.
        """
        if not curr_entities:
            return 0.0
        prev_ids = {self._entity_identity(e) for e in prev_entities}
        curr_ids = {self._entity_identity(e) for e in curr_entities}
        if not curr_ids:
            return 0.0
        new_entities = curr_ids - prev_ids
        return len(new_entities) / len(curr_ids)

    # PURPOSE: [L2-auto] _assess_information_gain の関数定義
    def _assess_information_gain(
        self,
        prev_text: str,
        curr_text: str,
    ) -> float:
        """Measure information gain between two synthesis texts.

        Uses Embeddings to compute 1 - cosine_similarity as a
        novelty metric. High gain = significant new information found.
        Low gain = synthesis is saturated.

        Returns:
            Float in [0.0, 1.0]. 0.0 = identical, 1.0 = completely different.
        """
        if not prev_text or not curr_text:
            return 1.0  # No prior text = maximum gain

        try:
            if self._embedder is None:
                self._init_embedder()

            # Delegate to Embedder.novelty (distance/information gain)
            return self._embedder.novelty(prev_text[:2000], curr_text[:2000])

        except Exception as e:  # noqa: BLE001
            logger.debug("Embedder unavailable for info gain: %s — using TF-IDF fallback", e)
            # TF-IDF fallback: measure word-level novelty
            try:
                import re as _re
                prev_words = set(_re.findall(r'\w{3,}', prev_text[:2000].lower()))
                curr_words = set(_re.findall(r'\w{3,}', curr_text[:2000].lower()))
                if not prev_words or not curr_words:
                    return 0.5
                new_words = curr_words - prev_words
                novelty = len(new_words) / max(1, len(curr_words))
                return max(0.0, min(1.0, novelty))
            except Exception:  # noqa: BLE001
                return 0.5  # Conservative default

    # PURPOSE: F6 Linkage L(c) — 検索結果の密度ベース情報利得を計算
    def _compute_result_density(
        self,
        new_results: list,
        existing_results: list,
    ) -> dict | None:
        """密度ベース情報利得: density_gain = (1 - redundancy) * drift。

        検索結果レベルで redundancy (内部冗長性) と drift (既存結果からの距離)
        を Embedder で計算し、新規性・多様性の複合指標を返す。

        #1修正: existing_results は new_results を含まない (呼出側で分離)
        #2修正: url_novelty 廃止 → drift を直接使用
        #3修正: coherence → redundancy にリネーム (quality_metrics 側と区別)
        #7修正: loss 式の符号反転バグ修正 — 旧式 -redundancy*drift は
               冗長結果を低 loss (=高利得) と誤評価していた。
               density_gain = (1-redundancy)*drift に直接化

        Returns:
            dict with keys: redundancy, drift, density_gain.
            None if calculation is not possible.
        """
        if not new_results or not existing_results:
            return None

        new_texts = [
            f"{getattr(r, 'title', '')} {getattr(r, 'content', '') or ''}"
            for r in new_results
        ]
        existing_texts = [
            f"{getattr(r, 'title', '')} {getattr(r, 'content', '') or ''}"
            for r in existing_results[:50]  # 計算コスト制限
        ]

        # 空テキストをフィルタ
        new_texts = [t for t in new_texts if len(t.strip()) > 10]
        existing_texts = [t for t in existing_texts if len(t.strip()) > 10]

        if not new_texts or not existing_texts:
            return None

        redundancy = self._compute_text_redundancy(new_texts)
        drift = self._compute_drift(new_texts, existing_texts)

        # density_gain = (1 - redundancy) * drift
        # 多様 (低 redundancy) × 新方向 (高 drift) = 高い情報利得
        # 冗長 (高 redundancy) × 重複 (低 drift) = 低い情報利得
        density_gain = max(0.0, min(1.0, (1.0 - redundancy) * drift))

        return {
            "redundancy": round(redundancy, 4),
            "drift": round(drift, 4),
            "density_gain": round(density_gain, 4),
        }

    # PURPOSE: F6 ヘルパー — テキスト群の内部冗長性を Embedder 類似度で推定
    def _compute_text_redundancy(self, texts: list[str]) -> float:
        """テキスト群の内部冗長性 (redundancy) を推定。

        高い redundancy = 新結果が互いに類似 = 冗長。
        低い redundancy = 新結果が多様 = 新しい方向性。

        #3修正: coherence → redundancy にリネーム
        (quality_metrics の coherence は「一貫性 = 高い = 良い」で意味が逆)
        #4修正: フォールバック 0.5 → 0.0 に統一
        #5修正: TF-IDF の言語非依存化 (char_wb n-gram) → さらに Embedder による多言語意味計算へ深化
        #6修正: n=1 時のゼロ除算回避で 1.0 (最大冗長) ではなく 0.0 (最大多様) を返す (バグ修正)
        """
        if len(texts) < 2:
            return 0.0

        try:
            if self._embedder is None:
                self._init_embedder()
            
            novelties = self._embedder.pairwise_novelty(texts)
            if not novelties:
                return 0.0
            
            avg_novelty = sum(novelties.values()) / len(novelties)
            return float(1.0 - avg_novelty)
        except Exception as e:  # noqa: BLE001
            logger.warning("Embedder unavailable for redundancy computation: %s", e)
            return 0.0

    # PURPOSE: F6 ヘルパー — 新結果の既存結果からの意味的距離を推定
    def _compute_drift(self, new_texts: list[str], existing_texts: list[str]) -> float:
        """新結果の既存結果からの意味的距離 (drift) を推定。

        高い drift = 新しい方向への探索。
        低い drift = 既存知識の重複。

        #4修正: フォールバック 0.5 → 0.0 に統一
        #5修正: TF-IDF から Embedder による多言語意味計算へ深化
        """
        if not new_texts or not existing_texts:
            return 1.0
            
        try:
            if self._embedder is None:
                self._init_embedder()
                
            import numpy as np
            from mekhane.anamnesis.embedder_mixin import _l2_normalize_matrix
            
            # Embed all once
            all_texts = existing_texts + new_texts
            matrix = np.array(self._embedder.embed_batch(all_texts), dtype=np.float64)
            normalized = _l2_normalize_matrix(matrix)
            
            existing_vecs = normalized[:len(existing_texts)]
            new_vecs = normalized[len(existing_texts):]
            
            # Calculate similarities: (M, D) @ (D, N) -> (M, N)
            sim_matrix = new_vecs @ existing_vecs.T
            sim_matrix = np.clip(sim_matrix, 0.0, 1.0)
            
            max_sims = sim_matrix.max(axis=1)
            return float(1.0 - max_sims.mean())
        except Exception as e:  # noqa: BLE001
            logger.warning("Embedder unavailable for drift computation: %s", e)
            return 0.0
        except ValueError:
            return 0.0

    # PURPOSE: [L2-auto] _log_gain_curve の関数定義
    def _log_gain_curve(
        self,
        query: str,
        depth: int,
        gain_history: list[dict],
    ) -> None:
        """Log information gain curve to metrics.jsonl for sweet-spot analysis."""
        import json
        from pathlib import Path

        metrics_path = Path(__file__).parent / "metrics.jsonl"
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "type": "iterative_deepening",
            "query": query,
            "depth": depth,
            "iterations": len(gain_history),
            "gain_curve": gain_history,
            "total_gain": sum(g.get("info_gain", 0) for g in gain_history),
            "converged": gain_history[-1].get("reason", "max_iterations") != "max_iterations"
            if gain_history else False,
        }
        try:
            with open(metrics_path, "a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:  # noqa: BLE001
            logger.debug("Failed to log gain curve: %s", e)

    # PURPOSE: VISION §1 計画8割 — Phase 0 比率を metrics.jsonl に記録
    def _log_phase_timing(
        self,
        query: str,
        depth: int,
        phase0_elapsed: float,
        total_elapsed: float,
    ) -> None:
        """Log Phase 0 planning ratio to metrics.jsonl (VISION: 計画8割)."""
        import json
        from pathlib import Path

        metrics_path = Path(__file__).parent / "metrics.jsonl"
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "type": "phase_timing",
            "query": query,
            "depth": depth,
            "phase0_seconds": round(phase0_elapsed, 2),
            "total_seconds": round(total_elapsed, 2),
            "planning_ratio": round(phase0_elapsed / total_elapsed, 3)
            if total_elapsed > 0 else 0.0,
        }
        try:
            with open(metrics_path, "a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:  # noqa: BLE001
            logger.debug("Failed to log phase timing: %s", e)

    # PURPOSE: [L2-auto] _phase_multipass の非同期処理定義 (Legacy compat wrapper)
    async def _phase_multipass(
        self,
        query: str,
        search_results: list[SearchResult],
        source_counts: dict[str, int],
        synthesis: list,
        enabled: set[str],
        depth: int,
    ) -> tuple[list[SearchResult], dict[str, int], list, object | None]:
        """Phase 2.5: Legacy wrapper — delegates to _phase_iterative_deepen."""
        return await self._phase_iterative_deepen(
            query, search_results, source_counts, synthesis, enabled, depth,
            llm_rerank=None,
        )

    # PURPOSE: [L2-auto] _phase_cite の非同期処理定義
    async def _phase_cite(
        self,
        synthesis: list,
        search_results: list[SearchResult],
    ) -> list:
        """Phase 3: Citation verification (Layers B/C/E + D)."""
        citations = []
        if self.verify_citations and synthesis:
            logger.info("Phase 3: Citation verification")
            for synth_result in synthesis:
                extracted = self.citation_agent.extract_claims_from_synthesis(
                    synth_result.content, search_results,
                )
                source_contents = {}
                for sr in search_results:
                    if sr.url and sr.content:
                        source_contents[sr.url] = sr.content
                    # Layer E: Also index source_urls
                    for su in getattr(sr, 'source_urls', []) or []:
                        if su and sr.content and su not in source_contents:
                            source_contents[su] = sr.content
                verified = await self.citation_agent.verify_citations(
                    extracted, source_contents, verify_depth=2,
                )

                # Layer D: URL Auditor (Gemini 3 Flash) for remaining TAINT
                taint_count = sum(1 for c in verified if c.taint_level == TaintLevel.TAINT)
                if taint_count > 0:
                    try:
                        if self.url_auditor is None:
                            from mekhane.periskope.url_auditor import URLAuditor
                            self.url_auditor = URLAuditor()
                        verified = await self.url_auditor.audit_citations(
                            verified, source_contents,
                        )
                    except Exception as e:  # noqa: BLE001
                        logger.debug("Layer D URLAuditor failed: %s", e)

                citations.extend(verified)
        return citations

    # PURPOSE: [L2-auto] _phase_decision_frame の非同期処理定義
    async def _phase_decision_frame(
        self,
        query: str,
        synthesis: list,
        depth: int,
    ) -> DecisionFrame | None:
        """Phase 3.5: Φ4 convergent framing."""
        if depth < 2 or not synthesis:
            return None
        try:
            synth_texts = [s.content for s in synthesis]
            return await phi4_post_search_framing(query, synth_texts)
        except Exception as e:  # noqa: BLE001
            logger.warning("Φ4 post-search framing failed: %s", e)
            return None

    # PURPOSE: [L2-auto] _compute_and_log_quality の関数定義
    def _compute_and_log_quality(
        self,
        query: str,
        search_results: list[SearchResult],
        source_counts: dict[str, int],
        pre_rerank_results: list[SearchResult],
        elapsed: float,
        diversity_weight: float = 0.3,
    ) -> object | None:
        """Compute quality metrics and log to JSONL."""
        try:
            quality = compute_quality_metrics(
                query=query,
                results=search_results,
                source_counts=source_counts,
                pre_rerank_results=pre_rerank_results,
                diversity_weight=diversity_weight,
            )
            logger.info("Quality: %s", quality.summary())
            log_metrics(query, quality, source_counts, elapsed=elapsed)
            return quality
        except Exception as e:  # noqa: BLE001
            logger.warning("Quality metrics failed: %s", e)
            return None

    # PURPOSE: [L2-auto] _phase_belief_update の非同期処理定義
    async def _phase_belief_update(
        self,
        query: str,
        search_results: list[SearchResult],
        source_counts: dict[str, int],
        synthesis: list,
        quality: object,
        adaptive_threshold: float,
    ) -> BeliefUpdate | None:
        """Φ7: Belief update (H4 Doxa)."""
        try:
            gaps = phi1_coverage_gaps(query, search_results, source_counts)
            belief = await phi7_belief_update(
                query=query,
                overall_score=quality.overall_score,
                synthesis_texts=[s.content for s in synthesis] if synthesis else [],
                coverage_gaps=gaps,
                iteration=0,
                loop_threshold=adaptive_threshold,
            )
            logger.info(
                "Φ7: residual_error=%.2f, should_loop=%s, seeds=%d",
                belief.residual_error, belief.should_loop, len(belief.seed_queries),
            )
            return belief
        except Exception as e:  # noqa: BLE001
            logger.warning("Φ7 belief update failed: %s", e)
            return None

    # PURPOSE: [L2-auto] _phase_search の非同期処理定義
    async def _phase_search(
        self,
        query: str,
        enabled: set[str],
        extra_queries: list[str] | None = None,
    ) -> tuple[list[SearchResult], dict[str, int]]:
        """Phase 1: Execute parallel searches.

        Args:
            query: Primary search query.
            enabled: Set of enabled source names.
            extra_queries: Additional queries (translations) for SearXNG.
        """
        # P4: Cache key based on query + sources
        cache_key = f"{query}||{'|'.join(sorted(enabled))}"
        if cache_key in self._search_cache:
            cached_results, cached_counts = self._search_cache[cache_key]
            logger.info("P4: Cache hit for %r (%d results)", query, len(cached_results))
            return cached_results, cached_counts

        tasks = {}

        if "searxng" in enabled:
            searxng_weights = self._config.get("searxng", {}).get("weights")
            tasks["searxng"] = self.searxng.search_multi_category(
                query, max_results=self.max_results, weights=searxng_weights,
                extra_queries=extra_queries,
            )

        if "brave" in enabled and self.brave.available:
            tasks["brave"] = self.brave.search(query, max_results=self.max_results)
        if "tavily" in enabled and self.tavily.available:
            tasks["tavily"] = self.tavily.search(query, max_results=self.max_results)
        if "semantic_scholar" in enabled:
            # S2 API works best with short keyword queries (< 200 chars)
            # Strip explanatory text after colons and truncate
            s2_query = query.split(":")[0].strip() if ":" in query else query
            s2_query = s2_query[:200]
            tasks["semantic_scholar"] = self.semantic_scholar.search(
                s2_query, max_results=self.max_results,
            )
        if "gnosis" in enabled:
            tasks["gnosis"] = self.gnosis.search(query, max_results=self.max_results)
        if "sophia" in enabled:
            tasks["sophia"] = self.sophia.search(query, max_results=self.max_results)
        if "kairos" in enabled:
            tasks["kairos"] = self.kairos.search(query, max_results=self.max_results)
        if "arxiv" in enabled:
            tasks["arxiv"] = self.arxiv.search(query, max_results=self.max_results)
        if "openalex" in enabled:
            tasks["openalex"] = self.openalex.search(query, max_results=self.max_results)
        if "github" in enabled and self.github.available:
            github_config = self._config.get("github", {})
            tasks["github"] = self.github.search_multi(
                query,
                max_results=self.max_results,
                search_types=github_config.get("search_types", ["issues", "discussions"])
            )

        if "gemini_search" in enabled and self.gemini_search.available:
            tasks["gemini_search"] = self.gemini_search.search(
                query, max_results=self.max_results,
            )
        if "vertex_search" in enabled and self.vertex_search.available:
            tasks["vertex_search"] = self.vertex_search.search(
                query, max_results=self.max_results,
            )
        if "stackoverflow" in enabled and self.stackoverflow.available:
            tasks["stackoverflow"] = self.stackoverflow.search(
                query, max_results=self.max_results,
            )
        if "reddit" in enabled and self.reddit.available:
            tasks["reddit"] = self.reddit.search(
                query, max_results=self.max_results,
            )
        if "hackernews" in enabled and self.hackernews.available:
            tasks["hackernews"] = self.hackernews.search(
                query, max_results=self.max_results,
            )
        if "google_cse" in enabled and self.google_cse.available:
            tasks["google_cse"] = self.google_cse.search(
                query, max_results=self.max_results,
            )

        # W1: Vertex AI Vector Search (ANN) — internal knowledge
        if "vector_search_ann" in enabled and self.vector_search_ann.enabled:
            # Lazy-inject embedder on first use
            if self.vector_search_ann.embedder is None:
                self._init_embedder()
                self.vector_search_ann.embedder = self._embedder
            tasks["vector_search_ann"] = self.vector_search_ann.search(
                query, max_results=self.max_results,
            )

        all_results: list[SearchResult] = []
        source_counts: dict[str, int] = {}

        if not tasks:
            return all_results, source_counts

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        for name, result in zip(tasks.keys(), results):
            if isinstance(result, list):
                if result:
                    # P-2 Correction Plan 案B: SourceごとのMin-Max正規化
                    # これによりS2の異常高スコア(1.0+)による他ソース駆逐を防ぎ、多様性を確保する
                    import os
                    if not os.environ.get("DISABLE_NORMALIZATION"):
                        scores = [r.relevance for r in result]
                        max_score = max(scores)
                        min_score = min(scores)
                        range_score = max_score - min_score
                        if range_score > 0:
                            for r in result:
                                r.relevance = (r.relevance - min_score) / range_score
                        else:
                            for r in result:
                                r.relevance = 1.0 if r.relevance > 0 else 0.0

                all_results.extend(result)
                source_counts[name] = len(result)
                logger.info("  %s: %d results", name, len(result))
            elif isinstance(result, BaseException):
                logger.error("  %s: FAILED — %s", name, result)
                source_counts[name] = 0

        # Sort by relevance (descending)
        all_results.sort(key=lambda r: r.relevance, reverse=True)

        # P4: Cache the results
        self._search_cache[cache_key] = (all_results, source_counts)

        return all_results, source_counts

    # PURPOSE: [L2-auto] _normalize_url の関数定義
    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize URL for deduplication."""
        url = url.lower().strip()
        # Remove trailing slash
        url = url.rstrip("/")
        # Remove common tracking params
        if "?" in url:
            base, _ = url.split("?", 1)
            return base
        return url

    # PURPOSE: [L2-auto] _deduplicate_results の関数定義
    def _deduplicate_results(
        self, results: list[SearchResult],
    ) -> list[SearchResult]:
        """F11: Cross-source deduplication by URL normalization."""
        seen: set[str] = set()
        deduped: list[SearchResult] = []

        for r in results:
            key = self._normalize_url(r.url) if r.url else f"title:{r.title}"
            if key not in seen:
                seen.add(key)
                deduped.append(r)

        return deduped

    # PURPOSE: [L2-auto] _llm_rerank_results の非同期処理定義
    async def _llm_rerank_results(
        self, query: str, results: list[SearchResult], depth: int = 2,
        override_enabled: bool | None = None
    ) -> list[SearchResult]:
        """Apply LLM cascade reranking to search results.

        Depth-based policy:
          - Depth 1 (Quick): OFF — speed priority, search engine order is sufficient
          - Depth 2+ (Standard/Deep): ON — quality priority, cross-source ranking needed

        override_enabled takes precedence over depth-based policy.
        """
        if override_enabled is not None:
            is_enabled = override_enabled
        elif depth >= 2:
            is_enabled = self.llm_reranker.enabled  # config 設定に従う (Depth 2+)
        else:
            is_enabled = False  # Depth 1: 速度優先で OFF
            logger.debug("W8: LLM reranking skipped (Depth %d < 2)", depth)

        if not is_enabled:
            return results

        logger.info("W8: Starting LLM cascade reranking for %d results (depth=%d)", len(results), depth)
        return await self.llm_reranker.rerank(query, results, depth)

    # PURPOSE: [L2-auto] _rerank_results の関数定義
    def _rerank_results(
        self,
        query: str,
        results: list[SearchResult],
        max_rerank: int | None = None,
    ) -> list[SearchResult]:
        """W4: Rerank results using Vertex Embeddings semantic similarity.

        Delegates similarity computation to Embedder.similarity_batch()
        for single-pass inference. Results beyond max_rerank keep original scores.
        Config: config.yaml → rerank.max_results, rerank.enabled
        """
        if not results:
            return results

        # Read config (with safe defaults)
        rerank_config = self._config.get("rerank", {})
        if not rerank_config.get("enabled", True):
            return results
        if max_rerank is None:
            max_rerank = rerank_config.get("max_results", 30)

        try:
            if self._embedder is None:
                self._init_embedder()
                logger.info("W4: Embedder initialized for reranking")

            # Split: rerank top N, keep rest with original scores
            to_rerank = results[:max_rerank]
            remainder = results[max_rerank:]

            # Delegate similarity to Embedder (single responsibility)
            texts = [f"{r.title} {r.snippet or r.content[:500] if r.content else ''}"
                     for r in to_rerank]
            scores = self._embedder.similarity_batch(query, texts)

            for r, score in zip(to_rerank, scores):
                r.relevance = score

            # F4: NL API Type-Aware Rerank Boost
            if self.nl_client and self.cloud_nl_cfg.get("enabled", False):
                try:
                    import re as _re
                    boost_weight = self.cloud_nl_cfg.get("rerank_boost", 0.1)
                    salience_threshold = self.cloud_nl_cfg.get("salience_threshold", 0.3)
                    
                    query_entities = self._nl_entity_cache.get(query)
                    if query_entities is None:
                        max_entities = self.cloud_nl_cfg.get("max_entities", 10)
                        query_entities = self.nl_client.analyze_entities(query, max_entities=max_entities)
                        self._nl_entity_cache[query] = query_entities
                    
                    salient = [e for e in query_entities if e.salience >= salience_threshold]
                    
                    if salient:
                        # Pre-compile patterns for word-boundary matching
                        patterns = []
                        for e in salient:
                            try:
                                pat = _re.compile(r'\b' + _re.escape(e.name) + r'\b', _re.IGNORECASE)
                                patterns.append((e, pat))
                            except _re.error:
                                pass
                        
                        boosted = 0
                        for r in to_rerank:
                            text_body = ((r.snippet or "") + " " + (r.content or "")).lower()
                            score_delta = 0.0
                            for e, pat in patterns:
                                # F4: Type-specific matching weight
                                if e.type == "PERSON" and getattr(r, 'source', '') == 'semantic_scholar':
                                    # Author name in title = high relevance signal
                                    if pat.search(r.title or ""):
                                        score_delta += e.salience * boost_weight * 2.0
                                        continue
                                if pat.search(text_body):
                                    score_delta += e.salience * boost_weight
                            
                            if score_delta > 0:
                                r.relevance = min(1.0, r.relevance + score_delta)
                                boosted += 1
                        
                        if boosted:
                            logger.info("F4: Boosted %d/%d results via NL entities", boosted, len(to_rerank))
                except Exception as e:  # noqa: BLE001
                    logger.warning("NL API rerank boost failed: %s", e)

            to_rerank.sort(key=lambda r: r.relevance, reverse=True)
            merged = to_rerank + remainder
            logger.info(
                "W4: Reranked %d/%d results via Embeddings (batch)",
                len(to_rerank), len(results),
            )

        except Exception as e:  # noqa: BLE001
            logger.warning("W4: Reranking unavailable, keeping original order: %s", e)
            merged = results

        return merged

    # PURPOSE: [L2-auto] _generate_refinement_queries の非同期処理定義
    async def _generate_refinement_queries(
        self,
        original_query: str,
        synthesis: list[SynthesisResult],
        results: list[SearchResult],
    ) -> list[str]:
        """W6: Generate refinement queries for multi-pass search.

        Analyzes first-pass synthesis to identify gaps and produces
        targeted follow-up queries for deeper coverage.

        Returns:
            List of 1-3 refinement queries, or empty if unnecessary.
        """
        # Build context from synthesis + source coverage
        synth_summary = "\n".join(
            s.content[:500] for s in synthesis[:2]
        )
        source_list = ", ".join(
            set(r.source.value for r in results[:20])
        )
        coverage_terms = set()
        for r in results[:20]:
            for word in (r.title + " " + r.snippet).lower().split():
                if len(word) > 3:
                    coverage_terms.add(word)

        template = load_prompt("w6_refinement_query.typos")
        if template:
            prompt = template.format(
                original_query=original_query,
                synth_summary=synth_summary,
                source_list=source_list,
            )
        else:
            # Fallback: hardcoded prompt
            prompt = (
                "You are a research gap analyst. Your job is to find SPECIFIC missing information.\n\n"
                f"## Original Query\n{original_query}\n\n"
                f"## Current Synthesis\n{synth_summary}\n\n"
                f"## Sources Used\n{source_list}\n\n"
                "## Task: Generate targeted follow-up queries\n\n"
                "Analyze the synthesis for these gap types:\n"
                "1. **Evidence gaps**: Claims without citations or data\n"
                "2. **Perspective gaps**: Missing viewpoints (e.g., no criticism, no alternatives)\n"
                "3. **Specificity gaps**: Vague statements that need concrete examples or numbers\n"
                "4. **Temporal gaps**: Outdated information or missing recent developments\n"
                "5. **Scope gaps**: Adjacent topics that would deepen understanding\n\n"
                "For each gap found, generate ONE search query that:\n"
                "- Targets a SPECIFIC fact, person, paper, or statistic\n"
                "- Uses keywords likely to appear in authoritative sources\n"
                "- Is in the same language as the original query\n\n"
                "Return 2-3 queries, one per line. No numbering or explanation.\n"
                "If synthesis is comprehensive with no gaps: NONE"
            )

        try:
            text = await _llm_ask(prompt, max_tokens=256)

            if not text or "NONE" in text.upper().strip():
                return []

            queries = [
                line.strip()
                for line in text.strip().split("\n")
                if line.strip() and len(line.strip()) > 5
            ]
            return queries[:3]  # Cap at 3

        except Exception as e:  # noqa: BLE001
            logger.warning("W6: Refinement query generation failed: %s", e)
            return []

    # PURPOSE: [L2-auto] _select_urls_for_deep_read の非同期処理定義
    async def _select_urls_for_deep_read(
        self,
        query: str,
        search_results: list[SearchResult],
        depth: int = 2,
    ) -> list[str]:
        """W7: Select URLs that deserve full-text deep reading.

        Summary→Full-text pattern: LLM analyzes snippets
        and decides which pages should be read in full.

        Only external URLs with insufficient content are considered.
        Internal sources (Gnosis/Sophia/Kairos) already have full text.

        Returns:
            List of URLs to crawl (max 5 for L2, max 15 for L3).
        """
        max_deep_read = 5 if depth <= 2 else 15

        # Filter candidates: external sources with short content only
        candidates: list[tuple[int, SearchResult]] = []
        for i, r in enumerate(search_results):
            source_name = r.source.value if hasattr(r.source, "value") else str(r.source)
            if source_name in INTERNAL_SOURCES:
                continue  # Already has full content
            if not r.url:
                continue
            if r.content and len(r.content) >= 1000:
                continue  # Already has substantial content
            candidates.append((i, r))

        if not candidates:
            logger.info("W7: No URLs need deep reading (all have sufficient content)")
            return []

        # Build numbered list for LLM
        result_list = []
        for idx, (i, r) in enumerate(candidates[:30]):  # Max 30 candidates
            snippet = (r.snippet or r.content or "")[:150]
            result_list.append(
                f"[{idx + 1}] {r.title}\n"
                f"    URL: {r.url}\n"
                f"    Snippet: {snippet}"
            )

        template = load_prompt("w7_deep_read_selection.typos")
        if template:
            prompt = template.format(
                query=query,
                result_list="\n".join(result_list),
                max_deep_read=max_deep_read,
            )
        else:
            # Fallback: hardcoded prompt
            prompt = (
                "You are a research assistant deciding which web pages to read in full.\n\n"
                f"Research query: {query}\n\n"
                "Search results (summaries only):\n"
                + "\n".join(result_list)
                + "\n\n"
                f"Which pages should be read in full to best answer the query? "
                f"Select up to {max_deep_read} pages.\n\n"
                "Consider:\n"
                "- Pages likely to contain detailed analysis or original data\n"
                "- Pages from authoritative sources (academic, official docs)\n"
                "- Pages whose snippets suggest they cover key aspects of the query\n\n"
                "If the snippets already provide enough information, return NONE.\n\n"
                f"Return ONLY the numbers (comma-separated), e.g.: 1, 3, 5\n"
                "If no pages need deep reading: NONE"
            )

        try:
            text = await _llm_ask(prompt, max_tokens=128)

            if not text or "NONE" in text.upper().strip():
                logger.info("W7: LLM decided no deep reading needed")
                return []

            # Parse selected numbers
            import re
            numbers = re.findall(r"\d+", text)
            selected_indices = [int(n) - 1 for n in numbers if n.isdigit()]

            urls = []
            for idx in selected_indices:
                if 0 <= idx < len(candidates):
                    urls.append(candidates[idx][1].url)
                if len(urls) >= max_deep_read:
                    break

            logger.info(
                "W7: LLM selected %d URLs for deep reading",
                len(urls),
            )
            return urls

        except Exception as e:  # noqa: BLE001
            logger.warning("W7: URL selection failed, falling back to top-N: %s", e)
            # Fallback: top N external URLs by relevance
            return [
                r.url for _, r in candidates[:max_deep_read]
                if r.url
            ]

    # PURPOSE: [L2-auto] _classify_query の関数定義
    @staticmethod
    def _classify_query(query: str) -> str:
        """F12: Classify query type for adaptive source selection.

        Delegates to Φ3 context setting's keyword classifier.

        Returns:
            "academic", "implementation", "news", "troubleshoot", or "concept".
        """
        from mekhane.periskope.cognition.phi3_context import _classify_query_keyword
        return _classify_query_keyword(query)

    # PURPOSE: [L2-auto] select_sources の関数定義
    @classmethod
    def select_sources(cls, query: str) -> list[str]:
        """F12: Suggest optimal sources based on query classification.

        Delegates to Φ3 context setting's SOURCE_MAP.
        """
        from mekhane.periskope.cognition.phi3_context import _SOURCE_MAP
        qtype = cls._classify_query(query)
        return _SOURCE_MAP.get(qtype, _SOURCE_MAP["concept"])



    # PURPOSE: [L2-auto] _phase_digest の関数定義
    def _phase_digest(self, report: ResearchReport, depth: str = "quick") -> Path | None:
        """Phase 4: Write research results to Digestor incoming.

        Creates an eat_*.md file in ~/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/03_素材｜Materials/a_受信｜incoming/
        compatible with the /eat workflow (F⊣G adjunction).

        Args:
            report: Completed research report.
            depth: Template depth — "quick" (/eat-), "standard" (/eat), "deep" (/eat+).

        Returns:
            Path to the created file, or None on failure.
        """
        try:
            incoming_dir = INCOMING_DIR
            incoming_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d")
            safe_query = "".join(
                ch if ch.isalnum() or ch in "-_ " else ""
                for ch in report.query[:40]
            ).strip().replace(" ", "_")
            filename = f"eat_{timestamp}_periskope_{safe_query}.md"
            filepath = incoming_dir / filename

            if filepath.exists():
                logger.info("Digest file already exists: %s", filename)
                return filepath

            # Build synthesis content
            synth_content = ""
            confidence = 0.0
            for s in report.synthesis:
                synth_content += s.content + "\n\n"
                confidence = max(confidence, s.confidence)

            # Citation summary
            citation_lines = []
            for c in report.citations:
                score = f"{c.similarity:.0%}" if c.similarity is not None else "—"
                citation_lines.append(
                    f"| {c.claim[:50]}... | {c.taint_level.value} | {score} |"
                )
            citation_table = ""
            if citation_lines:
                citation_table = (
                    "| Claim | Level | Score |\n"
                    "|:------|:------|------:|\n"
                    + "\n".join(citation_lines[:10])
                )

            # Decision Frame (Φ4)
            decision_frame_md = ""
            if report.decision_frame:
                df = report.decision_frame
                decision_frame_md = "## Φ4 Decision Frame\n\n"
                if df.key_findings:
                    decision_frame_md += "### Key Findings\n"
                    decision_frame_md += "\n".join(f"- {f}" for f in df.key_findings)
                    decision_frame_md += "\n\n"
                if df.open_questions:
                    decision_frame_md += "### Open Questions\n"
                    decision_frame_md += "\n".join(f"- ❓ {q}" for q in df.open_questions)
                    decision_frame_md += "\n\n"
                if df.decision_options:
                    decision_frame_md += "### Decision Options\n"
                    decision_frame_md += "\n".join(f"- ➡️ {o}" for o in df.decision_options)
                    decision_frame_md += "\n\n"
                decision_frame_md += f"**Confidence**: {df.confidence:.0%}\n\n"

            # Source count
            sources_str = ", ".join(
                f"{k}: {v}" for k, v in report.source_counts.items()
            )

            # Depth-dependent sections
            if depth == "deep":
                phase_template = self._deep_template()
            elif depth == "standard":
                phase_template = self._standard_template()
            else:
                phase_template = self._quick_template()

            content = f"""---
title: "Periskopē: {report.query[:60]}"
source: periskope
url: N/A
score: {confidence:.2f}
matched_topics: [periskope_research]
digest_to: []
generated: {timestamp}
depth: {depth}
---

# /eat 候補: Periskopē Research — {report.query[:60]}

> **Confidence**: {confidence:.0%} | **Sources**: {sources_str}
> **Elapsed**: {report.elapsed_seconds:.1f}s | **Results**: {len(report.search_results)}
> **Depth**: {depth} | **Auto-generated by Periskopē → /eat auto-digest**

## Synthesis

{synth_content.strip()}

## Citation Verification

{citation_table or '(no citations verified)'}

{decision_frame_md}

{phase_template}

---

*Auto-generated by Periskopē auto-digest ({timestamp}, depth={depth})*
*消化するには: `/eat` で読み込み、上記のテンプレートに従って統合*
"""
            filepath.write_text(content, encoding="utf-8")
            return filepath

        except Exception as e:  # noqa: BLE001
            logger.error("Auto-digest failed: %s", e)
            return None

    # PURPOSE: [L2-auto] _quick_template の関数定義
    @staticmethod
    def _quick_template() -> str:
        """Quick /eat- template — minimal Phase 0."""
        return """## Phase 0: 圏の特定

| 項目 | 内容 |
|:-----|:-----|
| 圏 Ext | <!-- 外部構造 --> |
| 圏 Int | <!-- 内部構造 --> |
| F (取込) | <!-- Ext → Int --> |
| G (忘却) | <!-- Int → Ext --> |"""

    # PURPOSE: [L2-auto] _standard_template の関数定義
    @staticmethod
    def _standard_template() -> str:
        """Standard /eat template — Phase 0 + /fit checklist."""
        return """## Phase 0: 圏の特定 (テンプレート)

| 項目 | 内容 |
|:-----|:-----|
| 圏 Ext (外部構造) | <!-- Periskopē が収集した研究知見 --> |
| 圏 Int (内部構造) | <!-- HGK 内の対応する圏 --> |
| 関手 F (取込) | <!-- Ext → Int へのマッピング --> |
| 関手 G (忘却) | <!-- Int → Ext への写像 --> |
| η (情報保存) | <!-- 取り込んで忘却→元情報をどの程度復元できるか --> |
| ε (構造保存) | <!-- 忘却して取込→HGK構造がどの程度維持されるか --> |

## /fit チェックリスト

- [ ] η 検証: 研究知見が HGK 内で再現可能
- [ ] ε 検証: HGK 既存構造との整合性確認
- [ ] Drift 測定: 1-ε の許容範囲内"""

    # PURPOSE: [L2-auto] _deep_template の関数定義
    @staticmethod
    def _deep_template() -> str:
        """Deep /eat+ template — full 7-phase digestion."""
        return """## Phase 0: 圏の特定

| 項目 | 内容 |
|:-----|:-----|
| 圏 Ext (外部構造) | <!-- Periskopē が収集した研究知見 --> |
| 圏 Int (内部構造) | <!-- HGK 内の対応する圏 --> |
| 関手 F (取込) | <!-- Ext → Int へのマッピング --> |
| 関手 G (忘却) | <!-- Int → Ext への写像 --> |
| η (情報保存) | <!-- 取り込んで忘却→元情報をどの程度復元できるか --> |
| ε (構造保存) | <!-- 忘却して取込→HGK構造がどの程度維持されるか --> |

## Phase 1: 構造抽出

> 主要概念・メカニズム・依存関係を構造化抽出する。

- [ ] 主要概念の列挙
- [ ] 依存関係グラフ (概念間)
- [ ] HGK 既存概念との対応付け

## Phase 2: 変換設計 (F: Ext → Int)

> 外部知見を HGK 内部構造にマッピングする具体設計。

- [ ] T1: 既知の再発見 (Rediscovery)
- [ ] T2: 既知の拡張 (Extension)
- [ ] T3: 新規概念 (Novel)
- [ ] T4: 不要/矛盾 (Reject)

## Phase 3: 忘却設計 (G: Int → Ext)

> HGK 構造から外部に投影したとき何が失われるかを分析。

- [ ] 忘却される情報の特定
- [ ] 許容できる情報損失の判定
- [ ] 情報保存の対策

## Phase 4: 統合検証

- [ ] η 検証: F→G→F = id (情報保存)
- [ ] ε 検証: G→F→G = id (構造保存)
- [ ] Drift 測定: 1-ε の許容範囲内
- [ ] 構造整合性確認

## Phase 5: 行動提案

- [ ] 実装すべき変更のリスト
- [ ] 優先順位付け
- [ ] 見積もり

## Phase 6: 反芻

- [ ] 消化プロセスの振り返り
- [ ] 信念更新 (/dox)
- [ ] 知識永続化 (/epi)"""

