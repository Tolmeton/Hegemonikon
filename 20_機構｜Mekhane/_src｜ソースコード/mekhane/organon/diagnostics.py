from __future__ import annotations

# PROOF: [L2/Organon] <- Sensor Triad diagnostic comparison
"""Diagnostics over common SensorReading values."""

from dataclasses import dataclass

from mekhane.fep.mapping import POIESIS_VERBS

from .sensor_reading import SensorReading


@dataclass(frozen=True, slots=True)
class DiagnosticFinding:
    """One Sensor Triad diagnostic result."""

    rule: str
    pattern: str
    severity: str
    message: str
    evidence: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": self.rule,
            "pattern": self.pattern,
            "severity": self.severity,
            "message": self.message,
            "evidence": dict(self.evidence),
        }


def _sum_flow_weight(reading: SensorReading, flow_pole: str) -> float:
    total = 0.0
    for ccl_name, weight in reading.vector.items():
        verb = POIESIS_VERBS.get(ccl_name)
        if verb is not None and verb.flow_pole == flow_pole:
            total += weight
    return total


def _support(reading: SensorReading, *, threshold: float) -> set[str]:
    return {
        ccl_name
        for ccl_name, weight in reading.vector.items()
        if weight >= threshold
    }


def diagnose_tool_text(
    tool_reading: SensorReading,
    text_reading: SensorReading,
    *,
    support_threshold: float = 0.05,
    text_s_threshold: float = 0.5,
    tool_s_threshold: float = 0.1,
) -> list[DiagnosticFinding]:
    """Compare Tool and Text sensor readings.

    This is the first diagnostic bridge for the Sensor Triad. It covers the
    Tool/Text-only rules from the design matrix and leaves Being-related
    Pattern 6/7 to a later comparator.
    """
    tool_support = _support(tool_reading, threshold=support_threshold)
    text_support = _support(text_reading, threshold=support_threshold)
    overlap = sorted(tool_support & text_support)
    tool_s_weight = _sum_flow_weight(tool_reading, "S")
    text_s_weight = _sum_flow_weight(text_reading, "S")
    findings: list[DiagnosticFinding] = []

    evidence = {
        "tool_sensor": tool_reading.sensor,
        "text_sensor": text_reading.sensor,
        "tool_support": sorted(tool_support),
        "text_support": sorted(text_support),
        "overlap": overlap,
        "tool_s_weight": tool_s_weight,
        "text_s_weight": text_s_weight,
    }

    if text_s_weight > text_s_threshold and tool_s_weight < tool_s_threshold:
        findings.append(
            DiagnosticFinding(
                rule="R2",
                pattern="P3",
                severity="block",
                message="Text Sensor claims S-quadrant perception without matching Tool Sensor evidence.",
                evidence=evidence,
            )
        )

    if overlap:
        findings.append(
            DiagnosticFinding(
                rule="R1",
                pattern="P1",
                severity="pass",
                message="Tool and Text sensors share doing-side support.",
                evidence=evidence,
            )
        )

    if tool_s_weight >= support_threshold and text_s_weight < support_threshold:
        findings.append(
            DiagnosticFinding(
                rule="R4",
                pattern="P2",
                severity="info",
                message="Tool Sensor has S-quadrant evidence that Text Sensor did not verbalize.",
                evidence=evidence,
            )
        )

    if tool_support and not text_support:
        findings.append(
            DiagnosticFinding(
                rule="R4",
                pattern="P8",
                severity="info",
                message="Tool Sensor fired but Text Sensor has no matching semantic support.",
                evidence=evidence,
            )
        )

    if not tool_support and not text_support:
        findings.append(
            DiagnosticFinding(
                rule="R0",
                pattern="P4",
                severity="pass",
                message="Neither Tool nor Text sensor fired above threshold.",
                evidence=evidence,
            )
        )

    return findings
