# PROOF: mekhane/tests/test_organon_diagnostics.py
# PURPOSE: Sensor Triad Tool/Text diagnostics
"""Tests for mekhane.organon.diagnostics."""


def test_diagnose_tool_text_flags_pattern_3_for_text_only_s_claim():
    from mekhane.organon import SensorReading, diagnose_tool_text

    tool = SensorReading(
        timestamp=None,
        session_id="alpha",
        sensor="tool",
        confidence="direct",
        vector={},
        evidence={},
    )
    text = SensorReading(
        timestamp=None,
        session_id="alpha",
        sensor="text",
        confidence="direct",
        vector={"prs": 1.0},
        evidence={},
    )

    findings = diagnose_tool_text(tool, text)

    assert [(finding.rule, finding.pattern, finding.severity) for finding in findings] == [
        ("R2", "P3", "block"),
    ]
    assert findings[0].evidence["text_s_weight"] == 1.0
    assert findings[0].to_dict()["pattern"] == "P3"


def test_diagnose_tool_text_passes_when_tool_and_text_overlap():
    from mekhane.organon import SensorReading, diagnose_tool_text

    tool = SensorReading(
        timestamp=None,
        session_id="alpha",
        sensor="tool",
        confidence="direct",
        vector={"prs": 1.0},
        evidence={},
    )
    text = SensorReading(
        timestamp=None,
        session_id="alpha",
        sensor="text",
        confidence="direct",
        vector={"prs": 1.0},
        evidence={},
    )

    findings = diagnose_tool_text(tool, text)

    assert [(finding.rule, finding.pattern, finding.severity) for finding in findings] == [
        ("R1", "P1", "pass"),
    ]


def test_diagnose_tool_text_reports_pattern_8_for_unverbalized_tool_use():
    from mekhane.organon import SensorReading, diagnose_tool_text

    tool = SensorReading(
        timestamp=None,
        session_id="alpha",
        sensor="tool",
        confidence="direct",
        vector={"tek": 1.0},
        evidence={},
    )
    text = SensorReading(
        timestamp=None,
        session_id="alpha",
        sensor="text",
        confidence="direct",
        vector={},
        evidence={},
    )

    findings = diagnose_tool_text(tool, text)

    assert [(finding.rule, finding.pattern, finding.severity) for finding in findings] == [
        ("R4", "P8", "info"),
    ]
