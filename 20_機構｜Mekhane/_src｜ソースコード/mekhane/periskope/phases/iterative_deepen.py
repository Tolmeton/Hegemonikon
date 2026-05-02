from __future__ import annotations
# PROOF: mekhane/periskope/phases/iterative_deepen.py
# PURPOSE: Phase 2.5 — CoT Search Chain (iterative deepening with reasoning trace)
"""
Phase 2.5: CoT Search Chain — Iterative Deepening.

The largest and most complex phase, implementing:
  - Diffusion-inspired denoising schedule (linear/cosine/exponential/logSNR)
  - α schedule for explore↔exploit balance
  - Reasoning trace with accumulated knowledge (CoT-in-Search)
  - Kalon saturation detection (Good-Turing)
  - V5 QPP feedback-enhanced query refinement
  - Phase Inversion L1 (Advocatus Diaboli)
  - F5 Entity novelty scoring
  - F6 Linkage density-based information gain
  - Shared Index for dialectic search

This module contains helper functions extracted from the iterative deepening
logic. The main loop remains in engine.py but delegates to these functions
for specific computations.

Extracted from engine.py L1475-2204 + utility methods L2206-2430.
"""

import json
import logging
import math
import re
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# ─── Denoising Schedule ────────────────────────────────────────────

def compute_decay_factor(t: float, decay_type: str) -> float:
    """Compute β decay factor at progress ratio t ∈ [0, 1].

    Supports: linear, cosine, exponential, logsnr.
    """
    if decay_type == "cosine":
        return 0.5 * (1.0 + math.cos(math.pi * t))
    elif decay_type == "logsnr":
        b = 0.3
        return math.exp(-abs(2.0 * t - 1.0) / b)
    elif decay_type == "exponential":
        return math.exp(-3.0 * t)
    else:
        # Linear (default)
        return 1.0 - t


def compute_denoising_params(
    t: float,
    decay_type: str,
    initial_diversity: float,
    initial_max_results: int,
    final_max_results: int,
) -> tuple[float, int]:
    """Compute denoising schedule params for iteration at progress t.

    Returns:
        (iter_diversity, iter_max_results)
    """
    decay_factor = compute_decay_factor(t, decay_type)
    iter_diversity = initial_diversity * decay_factor
    iter_max_results = max(
        final_max_results,
        int(final_max_results + (initial_max_results - final_max_results) * decay_factor),
    )
    return iter_diversity, iter_max_results


# ─── α Schedule ────────────────────────────────────────────────────

def compute_alpha(t: float, alpha_schedule: str) -> float:
    """Compute α (explore↔exploit balance) at progress t.

    Higher α = more exploit (relevance-focused)
    Lower α = more explore (gain-focused)
    """
    if alpha_schedule == "sigmoid":
        alpha_min, alpha_max = 0.15, 0.85
        return alpha_min + (alpha_max - alpha_min) / (1.0 + math.exp(-8.0 * (t - 0.5)))
    elif alpha_schedule == "linear":
        alpha_min, alpha_max = 0.3, 0.7
        return alpha_min + (alpha_max - alpha_min) * t
    else:
        # Cosine ramp (default)
        alpha_min, alpha_max = 0.3, 0.7
        return alpha_min + (alpha_max - alpha_min) * (1.0 - math.cos(math.pi * t)) / 2.0


def compute_denoising_score(
    alpha: float,
    query_relevance: float,
    confidence: float,
    info_gain: float,
) -> float:
    """FEP precision-weighted score: blend relevance × confidence with info_gain."""
    return alpha * query_relevance * confidence + (1 - alpha) * info_gain


# ─── Information Gain ──────────────────────────────────────────────

def assess_information_gain_tfidf(
    prev_text: str,
    curr_text: str,
) -> float:
    """TF-IDF fallback for information gain when embedder is unavailable."""
    if not prev_text or not curr_text:
        return 1.0
    try:
        prev_words = set(re.findall(r'\w{3,}', prev_text[:2000].lower()))
        curr_words = set(re.findall(r'\w{3,}', curr_text[:2000].lower()))
        if not prev_words or not curr_words:
            return 0.5
        new_words = curr_words - prev_words
        novelty = len(new_words) / max(1, len(curr_words))
        return max(0.0, min(1.0, novelty))
    except Exception:  # noqa: BLE001
        return 0.5


# ─── Entity Novelty (F5) ──────────────────────────────────────────

def entity_identity(entity: object) -> str:
    """Return a stable identity key for an NL API entity.

    Priority: KG MID > normalized name. Prevents overcounting
    entities with variant spellings sharing the same KG MID.
    """
    mid = ''
    if hasattr(entity, 'metadata') and entity.metadata:
        mid = getattr(entity.metadata, 'get', lambda *a: '')('mid', '') if isinstance(entity.metadata, dict) else ''
        if not mid and hasattr(entity.metadata, 'mid'):
            mid = entity.metadata.mid or ''
    if mid:
        return f"mid:{mid}"
    return re.sub(r'\s+', ' ', entity.name.lower().strip())


def entity_novelty(prev_entities: list, curr_entities: list) -> float:
    """F5: Measure entity novelty between iterations.

    Calculates the proportion of distinct new entities in the current synthesis.
    """
    if not curr_entities:
        return 0.0
    prev_ids = {entity_identity(e) for e in prev_entities}
    curr_ids = {entity_identity(e) for e in curr_entities}
    if not curr_ids:
        return 0.0
    new_entities = curr_ids - prev_ids
    return len(new_entities) / len(curr_ids)


# ─── Gain Curve Logging ───────────────────────────────────────────

def log_gain_curve(
    query: str,
    depth: int,
    gain_history: list[dict],
    metrics_dir: Path | None = None,
) -> None:
    """Log information gain curve to metrics.jsonl for sweet-spot analysis."""
    if metrics_dir is None:
        metrics_dir = Path(__file__).parent.parent
    metrics_path = metrics_dir / "metrics.jsonl"
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


def log_phase_timing(
    query: str,
    depth: int,
    phase0_elapsed: float,
    total_elapsed: float,
    metrics_dir: Path | None = None,
) -> None:
    """Log Phase 0 planning ratio to metrics.jsonl (VISION: 計画8割)."""
    if metrics_dir is None:
        metrics_dir = Path(__file__).parent.parent
    metrics_path = metrics_dir / "metrics.jsonl"
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
