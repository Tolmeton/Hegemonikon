# PROOF: mekhane/periskope/tests/test_engine.py
# PURPOSE: periskope モジュールの engine に対するテスト
"""
Tests for Periskopē Engine (orchestrator).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from mekhane.periskope.engine import PeriskopeEngine, ResearchReport
from mekhane.periskope.models import (
    SearchResult,
    SearchSource,
    SynthesisResult,
    SynthModel,
    Citation,
    TaintLevel,
    DivergenceReport,
)
from mekhane.periskope.quality_metrics import QualityMetrics


# ── ResearchReport Tests ──

def test_report_markdown_empty():
    """Empty report should produce valid markdown."""
    report = ResearchReport(query="test", elapsed_seconds=1.5)
    md = report.markdown()
    assert "# Periskopē Research Report" in md
    assert "test" in md
    assert "1.5s" in md


def test_report_markdown_with_results():
    """Report with all phases should produce complete markdown."""
    report = ResearchReport(
        query="FEP",
        search_results=[
            SearchResult(source=SearchSource.GNOSIS, title="Paper A", content="..."),
            SearchResult(source=SearchSource.SEARXNG, title="Web B", content="..."),
        ],
        synthesis=[
            SynthesisResult(
                model=SynthModel.GEMINI_FLASH,
                content="The FEP is a fundamental principle.",
                confidence=0.85,
            ),
        ],
        citations=[
            Citation(
                claim="FEP is fundamental",
                source_url="https://a.com",
                taint_level=TaintLevel.SOURCE,
                similarity=0.92,
                verification_note="Verified: 92% match",
            ),
        ],
        divergence=DivergenceReport(
            models_compared=[SynthModel.GEMINI_FLASH],
            agreement_score=1.0,
            divergent_claims=[],
            consensus_claims=["Single model"],
        ),
        elapsed_seconds=3.2,
        source_counts={"gnosis": 1, "searxng": 1},
    )
    md = report.markdown()
    assert "## Sources" in md
    assert "## Synthesis" in md
    assert "## Citation Verification" in md
    assert "SOURCE" in md


# ── Engine Unit Tests ──

def test_engine_init():
    """Engine should initialize with default configuration."""
    engine = PeriskopeEngine()
    assert engine.max_results == 10
    assert engine.verify_citations is True


# ── Engine Integration Test (uses real APIs — skip by default) ──

@pytest.mark.skip(reason="Integration test: requires Gnosis/Sophia/Kairos services running")
@pytest.mark.asyncio
async def test_engine_research_internal_only():
    """Research with internal sources only should work without Docker."""
    engine = PeriskopeEngine(verify_citations=False)
    report = await engine.research(
        query="free energy principle",
        sources=["gnosis", "sophia"],
    )
    assert isinstance(report, ResearchReport)
    assert report.query == "free energy principle"
    assert report.elapsed_seconds > 0
    # Should have some results from internal knowledge
    assert isinstance(report.search_results, list)


@pytest.mark.skip(reason="Integration test: requires Gnosis/Sophia/Kairos services running")
@pytest.mark.asyncio
async def test_engine_research_full():
    """Full research pipeline (all sources + synthesis + verification)."""
    engine = PeriskopeEngine(
        max_results_per_source=3,
        verify_citations=True,
    )
    report = await engine.research(
        query="active inference framework",
        sources=["gnosis", "sophia", "kairos"],
    )
    assert isinstance(report, ResearchReport)
    md = report.markdown()
    assert len(md) > 100  # Should produce substantive output


@pytest.mark.asyncio
async def test_phi05_rejoins_parent_pipeline(monkeypatch):
    """Successful Φ0.5 decomposition should continue through the parent pipeline."""
    import mekhane.periskope.cognition.phi0_task_decompose as phi0_mod
    import mekhane.periskope.cognition.phi5_action_plan as phi5_mod
    from mekhane.periskope.cognition.phi0_task_decompose import SubTask

    engine = PeriskopeEngine(verify_citations=False)

    async def fake_decompose(query: str, max_subtasks: int = 3):
        if query == "parent compound query":
            return [
                SubTask(query="child one", focus="One", priority=1),
                SubTask(query="child two", focus="Two", priority=2),
            ]
        return []

    async def fake_subtask_synthesis(original_query: str, subtask_reports):
        assert original_query == "parent compound query"
        assert len(subtask_reports) == 2
        return "Unified parent synthesis"

    async def fake_expand(query, depth, expand_query, enabled, known_context=""):
        return [query], None, None

    async def fake_search(query, enabled, extra_queries=None):
        slug = query.replace(" ", "-")
        return (
            [SearchResult(
                source=SearchSource.GNOSIS,
                title=f"{query} title",
                url=f"https://example.com/{slug}",
                content=f"{query} content",
            )],
            {"gnosis": 1},
        )

    async def fake_filter(query, search_results, depth, llm_rerank=None):
        return search_results, list(search_results)

    async def fake_deep_read(query, search_results, depth):
        return search_results

    async def fake_iterative(query, search_results, source_counts, synthesis, enabled, depth,
                             progress_callback=None, interaction_callback=None, llm_rerank=None):
        return (
            search_results,
            source_counts,
            synthesis,
            DivergenceReport(
                models_compared=[s.model for s in synthesis],
                agreement_score=1.0,
                divergent_claims=[],
                consensus_claims=[f"{len(search_results)} results for {query}"],
            ),
        )

    async def fake_cite(synthesis, search_results):
        return [Citation(
            claim="merged claim",
            source_url=f"https://example.com/{len(search_results)}",
            taint_level=TaintLevel.SOURCE,
        )]

    def fake_quality(query, search_results, source_counts, pre_rerank_results, elapsed, diversity_weight=0.3):
        quality_calls.append((query, len(search_results), len(pre_rerank_results)))
        return QualityMetrics(
            ndcg_at_10=1.0,
            source_entropy=1.0,
            max_entropy=1.0,
            coverage_score=1.0,
            score_spread=1.0,
            coherence_score=1.0,
        )

    async def fake_belief_update(query, search_results, source_counts, synthesis, quality, adaptive_threshold):
        return None

    quality_calls = []
    monkeypatch.setattr(phi0_mod, "decompose_query", fake_decompose)
    monkeypatch.setattr(phi0_mod, "synthesize_subtask_results", fake_subtask_synthesis)
    monkeypatch.setattr(
        phi5_mod,
        "phi5_action_plan",
        lambda depth, multipass, source_count: SimpleNamespace(max_results_per_source=engine.max_results),
    )
    monkeypatch.setattr(engine, "_phase_cognitive_expand", fake_expand)
    monkeypatch.setattr(engine, "_phase_search", fake_search)
    monkeypatch.setattr(engine, "_phase_filter", fake_filter)
    monkeypatch.setattr(engine, "_phase_deep_read", fake_deep_read)
    monkeypatch.setattr(engine, "_phase_iterative_deepen", AsyncMock(side_effect=fake_iterative))
    monkeypatch.setattr(engine, "_phase_cite", AsyncMock(side_effect=fake_cite))
    monkeypatch.setattr(engine, "_phase_decision_frame", AsyncMock(return_value={"frame": "ok"}))
    monkeypatch.setattr(engine, "_compute_and_log_quality", fake_quality)
    monkeypatch.setattr(engine, "_phase_belief_update", AsyncMock(side_effect=fake_belief_update))
    monkeypatch.setattr(engine, "_log_phase_timing", lambda *args, **kwargs: None)
    monkeypatch.setattr(engine, "_min_results_threshold", lambda depth: 0)
    monkeypatch.setattr(
        engine.synthesizer,
        "synthesize",
        AsyncMock(side_effect=lambda query, search_results: [SynthesisResult(
            model=SynthModel.GEMINI_FLASH,
            content=f"synth {query}",
            confidence=0.9,
        )]),
    )
    monkeypatch.setattr(
        engine.synthesizer,
        "detect_divergence",
        lambda synthesis: DivergenceReport(
            models_compared=[s.model for s in synthesis],
            agreement_score=1.0,
            divergent_claims=[],
            consensus_claims=["child divergence"],
        ),
    )

    report = await engine.research(
        query="parent compound query",
        sources=["gnosis"],
        depth=3,
    )

    assert report.query == "parent compound query"
    assert len(report.search_results) == 2
    assert report.synthesis[0].content == "Unified parent synthesis"
    assert report.citations[0].source_url.endswith("/2")
    assert report.divergence.consensus_claims == ["2 results for parent compound query"]
    assert engine._phase_iterative_deepen.await_count == 3
    assert engine._phase_cite.await_count == 3
    assert len(quality_calls) == 3
    assert quality_calls[-1] == ("parent compound query", 2, 2)
