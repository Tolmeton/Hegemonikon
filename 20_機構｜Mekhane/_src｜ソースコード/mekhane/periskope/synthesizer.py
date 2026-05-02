from __future__ import annotations
# PROOF: mekhane/periskope/synthesizer.py
# PURPOSE: periskope モジュールの synthesizer
"""
Multi-model synthesizer for Periskopē.

Synthesizes search results using multiple LLMs in parallel:
- Gemini (via CortexClient.chat() — generateChat API)
- Claude (via CortexClient.chat() — generateChat API, LS 不要)

Detects divergence between models to identify uncertain claims.

Depth-level model routing:
  L1: Gemini Pro only
  L2: Gemini Pro + Claude Sonnet
  L3: Gemini Pro + Claude Opus
"""


import asyncio
import logging
import time

from mekhane.ochema.model_defaults import FLASH
from mekhane.periskope.models import (
    Citation,
    DivergenceReport,
    SearchResult,
    SynthesisResult,
    SynthModel,
    TaintLevel,
)

logger = logging.getLogger(__name__)

# ━━━ Týpos .prompt からプロンプトをロード ━━━
import pathlib as _pathlib

_PROMPT_DIR = _pathlib.Path(__file__).resolve().parent.parent / "ergasterion" / "typos" / "prompts"


def _load_prompt_file(name: str) -> str:
    """Týpos .prompt ファイルからプロンプトをコンパイルする。"""
    try:
        from mekhane.ergasterion.typos.typos import parse_file
        pf = parse_file(str(_PROMPT_DIR / name))
        return pf.compile(format="markdown")
    except Exception as e:  # noqa: BLE001
        logger.warning("Týpos prompt %s load failed: %s", name, e)
        return ""


_CACHED_SYNTH: str | None = None
_CACHED_INCR: str | None = None


def _get_synth_prompt() -> str:
    global _CACHED_SYNTH
    if _CACHED_SYNTH is None:
        loaded = _load_prompt_file("periskope_synthesizer.prompt")
        _CACHED_SYNTH = loaded if loaded else _FALLBACK_SYNTH_PROMPT
    return _CACHED_SYNTH


def _get_incr_synth_prompt() -> str:
    global _CACHED_INCR
    if _CACHED_INCR is None:
        loaded = _load_prompt_file("periskope_synth_incr.prompt")
        _CACHED_INCR = loaded if loaded else _FALLBACK_INCR_SYNTH_PROMPT
    return _CACHED_INCR


# フォールバック (Týpos ロード失敗時)
_FALLBACK_SYNTH_PROMPT = """You are a research synthesizer. Given the following search results
for the query "{query}", produce a comprehensive synthesis.

Requirements:
1. Synthesize the key findings across all sources
2. Cite specific sources using [Source N] notation
3. Note any contradictions between sources
4. Rate your confidence (0-100%) in the synthesis

Search Results:
{results_text}

Output your synthesis in EXACTLY this format:

## Key Findings
- [finding 1] [Source N]

## Source Analysis
- [Source N]: [brief assessment of source quality/relevance]

## Contradictions
- [contradiction description] (between [Source X] and [Source Y])

## Confidence: X%
"""

_FALLBACK_INCR_SYNTH_PROMPT = """You are a research synthesizer. You are updating an existing synthesis with NEW search results.
Query: "{query}"

Current Synthesis State:
{current_synthesis}

New Search Results:
{results_text}

Requirements:
1. UPDATE the Current Synthesis State by incorporating the New Search Results.
2. If new findings contradict existing ones, note the contradiction.
3. Keep all previous [Source N] citations and add new ones as appropriate.
4. Output EXACTLY the same markdown format as below.

Output format:
## Key Findings
- [finding] [Source N]

## Source Analysis
- [Source N]: [assessment]

## Contradictions
- [contradiction]

## Confidence: X%
"""

# Depth-level → model selection mapping
_DEPTH_MODELS: dict[int, list[SynthModel]] = {
    1: [SynthModel.GEMINI_PRO],
    2: [SynthModel.GEMINI_PRO, SynthModel.CLAUDE_SONNET],
    3: [SynthModel.GEMINI_PRO, SynthModel.CLAUDE_OPUS],
}


# PURPOSE: [L2-auto] models_for_depth の関数定義
def models_for_depth(depth: int) -> list[SynthModel]:
    """Return synthesis models for the given depth level (1-3)."""
    return _DEPTH_MODELS.get(depth, _DEPTH_MODELS[2])


# PURPOSE: [L2-auto] MultiModelSynthesizer のクラス定義
class MultiModelSynthesizer:
    """Synthesize search results using multiple LLMs.

    Uses CortexClient.chat() (generateChat API) for both Gemini and Claude.
    No Language Server dependency — all models accessed directly via Cortex.

    Depth-level routing:
        L1: Gemini Pro only (fast, single-model)
        L2: Gemini Pro + Claude Sonnet (standard dual-model)
        L3: Gemini Pro + Claude Opus (deep dual-model)
    """

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(
        self,
        synth_models: list[SynthModel] | None = None,
        gemini_model: str = "gemini-3.1-pro-preview",
        max_tokens: int = 4096,
        cortex=None,
    ) -> None:
        self.synth_models = synth_models or models_for_depth(2)
        self.gemini_model = gemini_model
        self.max_tokens = max_tokens
        self._cortex = cortex
        self._embedder = None  # BGE-M3 for divergence detection

    # PURPOSE: [L2-auto] _get_cortex の関数定義
    def _get_cortex(self):
        """Lazy-load CortexClient."""
        if self._cortex is None:
            from mekhane.ochema.cortex_client import CortexClient
            try:
                from mekhane.ochema.account_router import get_account_for
                account = get_account_for("periskope")
            except Exception:  # noqa: BLE001
                account = "default"
            self._cortex = CortexClient(
                model=self.gemini_model,
                max_tokens=self.max_tokens,
                account=account,
            )
        return self._cortex

    # PURPOSE: [L2-auto] synthesize の非同期処理定義
    async def synthesize(
        self,
        query: str,
        search_results: list[SearchResult],
        system_instruction: str | None = None,
        char_budget: int | None = None,
    ) -> list[SynthesisResult]:
        """Synthesize search results using configured models.

        Args:
            char_budget: Optional Kalon-driven character budget for _format_results.
                         When None, uses the default 150K limit.
        """
        if not search_results:
            logger.warning("No search results to synthesize")
            return []

        chunk_size = self._get_chunk_size()
        if len(search_results) <= chunk_size:
            # Standard single-pass synthesis
            results_text = self._format_results(search_results, char_budget=char_budget)
            prompt = _get_synth_prompt().format(query=query, results_text=results_text)
            
            tasks = []
            for model in self.synth_models:
                target_model = SynthModel.CLAUDE_SONNET if model == SynthModel.CLAUDE_LS else model
                tasks.append(self._synth_via_cortex(prompt, target_model, system_instruction))
        else:
            # Incremental synthesis
            tasks = []
            for model in self.synth_models:
                target_model = SynthModel.CLAUDE_SONNET if model == SynthModel.CLAUDE_LS else model
                tasks.append(self._incremental_synthesis(
                    query, search_results, target_model, chunk_size, system_instruction,
                    char_budget=char_budget,
                ))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        synth_results = []
        for r in results:
            if isinstance(r, SynthesisResult):
                synth_results.append(r)
            elif isinstance(r, Exception):
                logger.error("Synthesis failed: %s", r)

        return synth_results

    # PURPOSE: [L2-auto] _incremental_synthesis の非同期処理定義
    async def _incremental_synthesis(
        self,
        query: str,
        search_results: list[SearchResult],
        model: SynthModel,
        chunk_size: int,
        system_instruction: str | None,
        char_budget: int | None = None,
    ) -> SynthesisResult:
        """Process large result sets incrementally to avoid dilution and context limits."""
        logger.info("Starting incremental synthesis for %s with %d results", model, len(search_results))
        
        chunks = [search_results[i:i + chunk_size] for i in range(0, len(search_results), chunk_size)]
        
        # Base synthesis
        results_text = self._format_results(chunks[0], char_budget=char_budget)
        prompt = _get_synth_prompt().format(query=query, results_text=results_text)
        current_result = await self._synth_via_cortex(prompt, model, system_instruction)
        
        # Incremental updates with graceful degradation
        for i, chunk in enumerate(chunks[1:], 1):
            try:
                logger.info("Incremental synthesis %s: chunk %d/%d", model, i + 1, len(chunks))
                results_text = self._format_results(chunk)
                update_prompt = _get_incr_synth_prompt().format(
                    query=query,
                    current_synthesis=current_result.content,
                    results_text=results_text
                )
                current_result = await self._synth_via_cortex(update_prompt, model, system_instruction)
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "Incremental synthesis %s chunk %d/%d failed: %s — returning partial result",
                    model, i + 1, len(chunks), e,
                )
                break  # Return best result so far
            
        return current_result

    # PURPOSE: [L2-auto] _get_chunk_size の関数定義
    def _get_chunk_size(self) -> int:
        """Get synthesis chunk size from config."""
        try:
            from mekhane.periskope.config_loader import load_config
            cfg = load_config()
            return cfg.get('synthesis', {}).get('incremental_chunk_size', 15)
        except Exception:  # noqa: BLE001
            return 15

    # PURPOSE: [L2-auto] _synth_via_cortex の非同期処理定義
    async def _synth_via_cortex(
        self,
        prompt: str,
        model: SynthModel,
        system_instruction: str | None,
    ) -> SynthesisResult:
        """Synthesize via CortexClient.chat() (generateChat API).

        Works for both Gemini and Claude models — unified pathway.
        Falls back to gemini-3-flash-preview if 403 PERMISSION_DENIED.
        """
        cortex = self._get_cortex()

        # model.value is the model_config_id (e.g. "gemini-3.1-pro-preview", "claude-sonnet-4-6")
        model_id = model.value

        # Prepend system instruction to the prompt if provided
        # (generateChat doesn't have a separate system_instruction field)
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"System: {system_instruction}\n\n{prompt}"

        start = time.monotonic()

        # CortexClient.chat() is sync — run in thread pool
        _FALLBACK_MODEL = FLASH
        try:
            response = await asyncio.to_thread(
                cortex.chat,
                message=full_prompt,
                model=model_id,
                timeout=120.0,
            )
        except Exception as e:  # noqa: BLE001
            err_str = str(e)
            if ("403" in err_str or "PERMISSION_DENIED" in err_str) and model_id != _FALLBACK_MODEL:
                logger.warning(
                    "Synthesis (%s): 403 PERMISSION_DENIED, falling back to %s",
                    model_id, _FALLBACK_MODEL,
                )
                response = await asyncio.to_thread(
                    cortex.chat,
                    message=full_prompt,
                    model=_FALLBACK_MODEL,
                    timeout=120.0,
                )
                model_id = _FALLBACK_MODEL
            else:
                raise
        elapsed = time.monotonic() - start

        # Extract citations from the response
        citations = self._extract_citations(response.text)

        # Extract confidence from response text
        confidence = self._extract_confidence(response.text)

        logger.info(
            "Synthesis (%s): %d chars in %.1fs, confidence=%d%%",
            model_id, len(response.text), elapsed, int(confidence * 100),
        )

        return SynthesisResult(
            model=model,
            content=response.text,
            citations=citations,
            confidence=confidence,
            thinking=getattr(response, "thinking", "") or "",
            token_count=response.token_usage.get("total_tokens", 0)
            if isinstance(response.token_usage, dict)
            else 0,
        )

    # PURPOSE: [L2-auto] detect_divergence の関数定義
    def detect_divergence(
        self,
        results: list[SynthesisResult],
    ) -> DivergenceReport:
        """Detect divergence between multiple model outputs.

        Compares outputs from different models using two signals:
        1. Confidence spread (how much models disagree on certainty)
        2. Semantic similarity via BGE-M3 embeddings (how different the content is)

        Agreement score = 0.5 * (1 - confidence_spread) + 0.5 * semantic_similarity

        Args:
            results: List of synthesis results from different models.

        Returns:
            DivergenceReport with agreement analysis.
        """
        if len(results) < 2:
            return DivergenceReport(
                models_compared=[r.model for r in results],
                agreement_score=1.0,
                divergent_claims=[],
                consensus_claims=["Single model — no divergence detection possible"],
            )

        # Signal 1: Confidence spread
        confidences = [r.confidence for r in results]
        avg_confidence = sum(confidences) / len(confidences)
        confidence_spread = max(confidences) - min(confidences)
        confidence_agreement = max(0.0, 1.0 - confidence_spread)

        # Signal 2: Semantic similarity via BGE-M3
        semantic_similarity = self._compute_text_similarity(results)

        # Combined agreement score
        if semantic_similarity is not None:
            agreement = 0.5 * confidence_agreement + 0.5 * semantic_similarity
        else:
            agreement = confidence_agreement

        # Build divergence/consensus claims
        divergent_claims = []
        consensus_claims = [f"Average confidence: {avg_confidence:.2f}"]

        if confidence_spread > 0.2:
            divergent_claims.append(
                f"Confidence spread: {confidence_spread:.2f} "
                f"({', '.join(f'{r.model.value}={r.confidence:.0%}' for r in results)})"
            )
        if semantic_similarity is not None and semantic_similarity < 0.7:
            divergent_claims.append(
                f"Semantic divergence: {1.0 - semantic_similarity:.2f} "
                f"(content differs significantly between models)"
            )
        if semantic_similarity is not None and semantic_similarity >= 0.8:
            consensus_claims.append(
                f"Semantic agreement: {semantic_similarity:.2f}"
            )

        return DivergenceReport(
            models_compared=[r.model for r in results],
            agreement_score=agreement,
            divergent_claims=divergent_claims,
            consensus_claims=consensus_claims,
        )

    # PURPOSE: [L2-auto] _compute_text_similarity の関数定義
    def _compute_text_similarity(
        self, results: list[SynthesisResult],
    ) -> float | None:
        """Compute pairwise semantic similarity between synthesis texts.

        Uses VertexEmbedder (API) first, BGE-M3 (local) as fallback.
        Returns the minimum pairwise cosine similarity (worst-case divergence).
        """
        try:
            if self._embedder is None:
                from mekhane.periskope.embedder_factory import get_embedder
                self._embedder = get_embedder()

            # Batch embed (single API call for all texts)
            texts = [r.content[:2000] for r in results]
            vectors = self._embedder.embed_batch(texts)

            # Pairwise cosine similarity
            min_sim = 1.0
            for i in range(len(vectors)):
                for j in range(i + 1, len(vectors)):
                    dot = sum(a * b for a, b in zip(vectors[i], vectors[j]))
                    min_sim = min(min_sim, max(0.0, min(1.0, dot)))

            return min_sim
        except Exception as e:  # noqa: BLE001
            logger.debug("Semantic divergence unavailable: %s", e)
            return None

    # PURPOSE: [L2-auto] _format_results の関数定義
    def _format_results(
        self,
        results: list[SearchResult],
        char_budget: int | None = None,
    ) -> str:
        """Format search results for the synthesis prompt.
        
        Applies a total character budget to prevent context window overflow.
        When char_budget is provided (e.g., from Kalon-driven adaptive budgeting),
        it overrides the default 150K limit.
        """
        lines = []
        total_chars = 0
        max_total_chars = char_budget if char_budget is not None else 150_000
        
        for i, r in enumerate(results, 1):
            source_tag = f"[{r.source.value}]" if r.source else ""
            url_line = f"\n   URL: {r.url}" if r.url else ""
            content_text = (r.content or r.snippet or "")
            
            # Per-source budget: remaining budget / remaining sources
            remaining_sources = max(1, len(results) - i + 1)
            per_source_budget = min(40000, (max_total_chars - total_chars) // remaining_sources)
            if per_source_budget < 200:
                # Budget exhausted — add minimal entry
                lines.append(f"[Source {i}] {source_tag} {r.title}{url_line}\n   [truncated]")
                continue
                
            content_text = content_text[:per_source_budget]
            entry = (
                f"[Source {i}] {source_tag} {r.title}"
                f"{url_line}"
                f"\n   {content_text}"
            )
            total_chars += len(entry)
            lines.append(entry)
            
        return "\n\n".join(lines)

    # PURPOSE: [L2-auto] _extract_citations の関数定義
    def _extract_citations(self, text: str) -> list[Citation]:
        """Extract [Source N] citations from synthesis text."""
        import re

        citations = []
        # Find all [Source N] references
        refs = re.findall(r'\[Source\s+(\d+)\]', text)
        seen = set()
        for ref_num in refs:
            if ref_num not in seen:
                seen.add(ref_num)
                citations.append(Citation(
                    claim=f"Referenced as Source {ref_num}",
                    source_url="",
                    taint_level=TaintLevel.UNCHECKED,
                ))
        return citations

    # PURPOSE: [L2-auto] _extract_confidence の関数定義
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence percentage from synthesis text."""
        import re

        match = re.search(r'Confidence:\s*(\d+)%', text)
        if match:
            return min(1.0, int(match.group(1)) / 100.0)
        return 0.5  # Default moderate confidence
