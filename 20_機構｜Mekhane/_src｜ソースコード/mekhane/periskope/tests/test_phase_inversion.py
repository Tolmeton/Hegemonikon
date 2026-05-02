# PROOF: mekhane/periskope/tests/test_phase_inversion.py
# PURPOSE: periskope モジュールの phase_inversion に対するテスト
"""Tests for Phase Inversion (VISION §7)."""

from __future__ import annotations

import pytest

from mekhane.periskope.cognition.phase_inversion import (
    AdvocatusChallenge,
    _extract_items,
    _parse_challenge,
)
from mekhane.periskope.cognition.reasoning_trace import (
    ReasoningStep,
    ReasoningTrace,
)


# --- AdvocatusChallenge dataclass ---

def test_advocatus_challenge_defaults():
    """AdvocatusChallenge has sane defaults."""
    c = AdvocatusChallenge()
    assert c.refutation_points == []
    assert c.counter_queries == []
    assert c.challenged_confidence == 0.0


def test_advocatus_challenge_summary():
    """Summary format is correct."""
    c = AdvocatusChallenge(
        refutation_points=["point1", "point2"],
        counter_queries=["q1"],
        challenged_confidence=0.65,
    )
    s = c.summary()
    assert "refutations=2" in s
    assert "counter_queries=1" in s
    assert "65%" in s


# --- Parser tests ---

def test_extract_items_basic():
    """Extract bullet items from a section."""
    text = (
        "REFUTATIONS:\n"
        "- First claim is weak\n"
        "- Second claim lacks evidence\n"
        "COUNTER_QUERIES:\n"
        "- search for X\n"
    )
    items = _extract_items(text, "REFUTATIONS")
    assert len(items) == 2
    assert items[0] == "First claim is weak"


def test_extract_items_none():
    """NONE returns empty list."""
    text = "REFUTATIONS:\n- NONE\nCOUNTER_QUERIES:\n- query\n"
    items = _extract_items(text, "REFUTATIONS")
    assert items == []


def test_extract_items_markdown_headers():
    """Handle markdown-style headers."""
    text = (
        "## REFUTATIONS\n"
        "- Point A\n"
        "- Point B\n"
        "## COUNTER_QUERIES\n"
        "- Query 1\n"
    )
    items = _extract_items(text, "REFUTATIONS")
    assert len(items) == 2


def test_parse_challenge_full():
    """Full parse with all sections."""
    raw = (
        "REFUTATIONS:\n"
        "- The study sample size is too small\n"
        "- Confounding variables not controlled\n"
        "COUNTER_QUERIES:\n"
        "- meta-analysis contradicting small sample studies\n"
        "CHALLENGED_CONFIDENCE: 45\n"
    )
    c = _parse_challenge(raw, fallback_confidence=0.7)
    assert len(c.refutation_points) == 2
    assert len(c.counter_queries) == 1
    assert c.challenged_confidence == 0.45


def test_parse_challenge_no_confidence():
    """Fallback confidence when not present."""
    raw = "REFUTATIONS:\n- Point\nCOUNTER_QUERIES:\n- NONE\n"
    c = _parse_challenge(raw, fallback_confidence=0.8)
    assert c.challenged_confidence == 0.8


# --- ReasoningStep with refutations ---

def test_reasoning_step_refutations_field():
    """ReasoningStep has refutations field."""
    step = ReasoningStep(
        iteration=1,
        learned=["fact1"],
        refutations=["refutation1", "refutation2"],
        confidence=0.7,
    )
    assert len(step.refutations) == 2
    assert "refutations=2" in step.summary()


def test_reasoning_step_no_refutations_in_summary():
    """Summary omits refutations when empty."""
    step = ReasoningStep(iteration=1, confidence=0.5)
    assert "refutations" not in step.summary()


def test_reasoning_trace_serialization_with_refutations():
    """ReasoningTrace roundtrip preserves refutations."""
    trace = ReasoningTrace(query="test")
    step = ReasoningStep(
        iteration=1,
        learned=["fact1"],
        refutations=["ref1"],
        confidence=0.7,
    )
    trace.steps.append(step)

    data = trace.to_dict()
    assert data["steps"][0]["refutations"] == ["ref1"]

    restored = ReasoningTrace.from_dict(data)
    assert restored.steps[0].refutations == ["ref1"]


def test_reasoning_trace_format_report_includes_refutations():
    """format_for_report includes refutations section."""
    trace = ReasoningTrace(query="test")
    step = ReasoningStep(
        iteration=1,
        refutations=["claim X is unsupported"],
        confidence=0.6,
    )
    trace.steps.append(step)

    report = trace.format_for_report()
    assert "Refutations" in report
    assert "claim X is unsupported" in report


# --- Config validation ---

def test_config_has_phase_inversion():
    """config.yaml includes phase_inversion section."""
    from mekhane.periskope.config_loader import load_config
    config = load_config()
    assert "phase_inversion" in config
    pi = config["phase_inversion"]
    assert pi.get("enabled") is True
    assert "l1" in pi
    assert "dialectic" in pi
    assert pi["dialectic"]["rounds"][2] == 3  # L2 = 3 rounds


# --- DialecticEngine basic ---

def test_dialectic_report_markdown():
    """DialecticReport.markdown() produces valid output (v2 parallel)."""
    from mekhane.periskope.dialectic import DialecticReport

    report = DialecticReport(
        query="Is X true?",
        synthesis_text="The evidence is mixed...",
        thesis_confidence=0.7,
        antithesis_confidence=0.4,
        final_confidence=0.58,
    )
    md = report.markdown()
    assert "Thesis" in md
    assert "Antithesis" in md
    assert "Synthesis" in md
    assert "70%" in md
    assert "40%" in md
