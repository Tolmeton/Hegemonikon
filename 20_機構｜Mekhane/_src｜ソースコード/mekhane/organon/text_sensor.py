from __future__ import annotations

# PROOF: [L2/Organon] <- Text Sensor deterministic ingress
"""Minimal deterministic Text Sensor for Organon.

This sensor intentionally starts with explicit Poiesis markers such as `/noe`
or `/tek+`. Broader natural-language classification belongs to the future
lexicon/LLM layer, not this minimal common-surface bridge.
"""

from collections import Counter
import re

from mekhane.fep.mapping import POIESIS_VERBS

from .sensor_reading import SensorReading


_POIESIS_TOKEN_PATTERNS: dict[str, re.Pattern[str]] = {
    ccl_name: re.compile(rf"(?<![\w/])/{re.escape(ccl_name)}[+-]?(?![\w-])")
    for ccl_name in POIESIS_VERBS
}


def analyze_text_sensor(
    text: str,
    *,
    session_id: str = "unknown",
    timestamp: str | None = None,
) -> SensorReading:
    """Analyze assistant text and return a common SensorReading.

    The current implementation only treats explicit slash-verb tokens as direct
    evidence. This keeps Text Sensor separate from Being Sensor and avoids
    pretending that broad natural language has already been classified.
    """
    counts: Counter[str] = Counter()
    matched_tokens: list[str] = []

    for ccl_name, pattern in _POIESIS_TOKEN_PATTERNS.items():
        matches = pattern.findall(text)
        if not matches:
            continue
        counts[ccl_name] += len(matches)
        matched_tokens.extend(matches)

    total = sum(counts.values())
    vector = {
        ccl_name: count / total
        for ccl_name, count in sorted(counts.items())
    } if total else {}

    return SensorReading(
        timestamp=timestamp,
        session_id=session_id,
        sensor="text",
        confidence="direct",
        vector=vector,
        evidence={
            "text_length": len(text),
            "match_count": total,
            "counts_by_ccl": dict(counts),
            "matched_tokens": matched_tokens,
        },
    )
