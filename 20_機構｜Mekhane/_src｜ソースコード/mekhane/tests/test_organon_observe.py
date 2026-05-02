# PROOF: mekhane/tests/test_organon_observe.py
# PURPOSE: observe_session wires Tool/Text sensors to diagnostics
"""Tests for mekhane.organon.observe."""

from pathlib import Path
import textwrap


def test_observe_session_returns_pass_when_tool_and_text_overlap(tmp_path: Path):
    from mekhane.organon import SessionObservation, observe_session

    log_path = tmp_path / "tool_sensor_alpha.jsonl"
    log_path.write_text(
        textwrap.dedent(
            """
            {"timestamp":"2026-04-24T00:00:00Z","session_id":"alpha","sensor":"tool","source_event":"PostToolUse","output_type":"48-seed","tool":"Read","quadrant":"S","axis_hints":{"scale":"micro"},"confidence":"direct","requires_semantic_fallback":false,"evidence":{"tool_name":"Read"}}
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    observation = observe_session(
        "I used /prs to inspect the local source.",
        session_id="alpha",
        tool_log_path=log_path,
        timestamp="2026-04-24T00:00:01Z",
    )

    assert isinstance(observation, SessionObservation)
    assert observation.session_id == "alpha"
    assert observation.tool_reading.vector == {"prs": 1.0}
    assert observation.text_reading.vector == {"prs": 1.0}
    assert [(finding.rule, finding.pattern) for finding in observation.findings] == [
        ("R1", "P1"),
    ]
    assert observation.to_dict()["session_id"] == "alpha"


def test_observe_session_flags_text_only_s_claim(tmp_path: Path):
    from mekhane.organon import observe_session

    log_path = tmp_path / "tool_sensor_alpha.jsonl"
    log_path.write_text("", encoding="utf-8")

    observation = observe_session(
        "I claim /prs without a tool seed.",
        session_id="alpha",
        tool_log_path=log_path,
    )

    assert observation.tool_reading.vector == {}
    assert observation.text_reading.vector == {"prs": 1.0}
    assert [(finding.rule, finding.pattern, finding.severity) for finding in observation.findings] == [
        ("R2", "P3", "block"),
    ]
