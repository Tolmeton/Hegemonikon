# PROOF: mekhane/tests/test_tool_sensor_reader.py
# PURPOSE: Organon Tool Sensor reader normalizes PostToolUse 48-seed logs
"""Tests for mekhane.organon.tool_sensor."""

import os
from pathlib import Path
import textwrap


def test_project_tool_seed_maps_scale_micro_to_prs():
    from mekhane.organon.tool_sensor import ToolSeedReading
    from mekhane.organon.tool_sensor_adapter import project_tool_seed

    reading = ToolSeedReading(
        timestamp="2026-04-23T00:00:00Z",
        session_id="alpha",
        sensor="tool",
        source_event="PostToolUse",
        output_type="48-seed",
        tool="Read",
        quadrant="S",
        axis_hints={"scale": "micro"},
        confidence="direct",
        requires_semantic_fallback=False,
        evidence={"tool_name": "Read"},
    )

    projected = project_tool_seed(reading)

    assert projected is not None
    assert projected.coordinate == "Scale"
    assert projected.ccl_name == "prs"
    assert projected.helmholtz_component == "Γ"


def test_project_tool_seed_maps_action_exploit_to_tek():
    from mekhane.organon.tool_sensor import ToolSeedReading
    from mekhane.organon.tool_sensor_adapter import project_tool_seed

    reading = ToolSeedReading(
        timestamp="2026-04-23T00:00:00Z",
        session_id="alpha",
        sensor="tool",
        source_event="PostToolUse",
        output_type="48-seed",
        tool="Write",
        quadrant="A",
        axis_hints={"function": "exploit"},
        confidence="direct",
        requires_semantic_fallback=False,
        evidence={"tool_name": "Write"},
    )

    projected = project_tool_seed(reading)

    assert projected is not None
    assert projected.coordinate == "Function"
    assert projected.ccl_name == "tek"
    assert projected.weight_map == {"tek": 1.0}


def test_project_tool_seed_returns_none_when_axis_hints_too_coarse():
    from mekhane.organon.tool_sensor import ToolSeedReading
    from mekhane.organon.tool_sensor_adapter import project_tool_seed

    reading = ToolSeedReading(
        timestamp="2026-04-23T00:00:00Z",
        session_id="alpha",
        sensor="tool",
        source_event="PostToolUse",
        output_type="48-seed",
        tool="Task",
        quadrant="A",
        axis_hints={},
        confidence="direct",
        requires_semantic_fallback=True,
        evidence={"tool_name": "Task"},
    )

    assert project_tool_seed(reading) is None


def test_aggregate_layer_alpha_seeds_builds_normalized_sparse_vector():
    from mekhane.organon.tool_sensor import ToolSeedReading
    from mekhane.organon.sensor_reading import SensorReading
    from mekhane.organon.tool_sensor_adapter import (
        aggregate_layer_alpha_seeds,
        project_tool_seed,
    )

    readings = [
        ToolSeedReading(
            timestamp="2026-04-23T00:00:00Z",
            session_id="alpha",
            sensor="tool",
            source_event="PostToolUse",
            output_type="48-seed",
            tool="Read",
            quadrant="S",
            axis_hints={"scale": "micro"},
            confidence="direct",
            requires_semantic_fallback=False,
            evidence={"tool_name": "Read"},
        ),
        ToolSeedReading(
            timestamp="2026-04-23T00:00:01Z",
            session_id="alpha",
            sensor="tool",
            source_event="PostToolUse",
            output_type="48-seed",
            tool="Read",
            quadrant="S",
            axis_hints={"scale": "micro"},
            confidence="direct",
            requires_semantic_fallback=False,
            evidence={"tool_name": "Read"},
        ),
        ToolSeedReading(
            timestamp="2026-04-23T00:00:02Z",
            session_id="alpha",
            sensor="tool",
            source_event="PostToolUse",
            output_type="48-seed",
            tool="Write",
            quadrant="A",
            axis_hints={"function": "exploit"},
            confidence="direct",
            requires_semantic_fallback=False,
            evidence={"tool_name": "Write"},
        ),
    ]

    seeds = [project_tool_seed(reading) for reading in readings]
    aggregate = aggregate_layer_alpha_seeds([seed for seed in seeds if seed is not None])

    assert aggregate.session_id == "alpha"
    assert isinstance(aggregate, SensorReading)
    assert aggregate.sensor == "tool"
    assert aggregate.timestamp == "2026-04-23T00:00:02Z"
    assert aggregate.vector == {"prs": 2 / 3, "tek": 1 / 3}
    assert aggregate.evidence["counts_by_ccl"] == {"prs": 2, "tek": 1}
    assert aggregate.evidence["counts_by_quadrant"] == {"S": 2, "A": 1}
    assert aggregate.to_dict()["sensor"] == "tool"


def test_read_tool_sensor_log_parses_48_seed_lines(tmp_path: Path):
    from mekhane.organon.tool_sensor import read_tool_sensor_log

    log_path = tmp_path / "tool_sensor_alpha.jsonl"
    log_path.write_text(
        textwrap.dedent(
            """
            {"timestamp":"2026-04-23T00:00:00Z","session_id":"alpha","sensor":"tool","source_event":"PostToolUse","output_type":"48-seed","tool":"Read","quadrant":"S","axis_hints":{"scale":"micro"},"confidence":"direct","requires_semantic_fallback":false,"evidence":{"tool_name":"Read"}}
            {"timestamp":"2026-04-23T00:00:01Z","session_id":"alpha","sensor":"tool","source_event":"PostToolUse","output_type":"48-seed","tool":"Write","quadrant":"A","axis_hints":{"scale":"micro"},"confidence":"direct","requires_semantic_fallback":false,"evidence":{"tool_name":"Write"}}
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    readings = read_tool_sensor_log(log_path=log_path)

    assert len(readings) == 2
    assert readings[0].tool == "Read"
    assert readings[0].quadrant == "S"
    assert readings[1].tool == "Write"
    assert readings[1].quadrant == "A"


def test_read_tool_sensor_log_skips_non_seed_lines_when_not_strict(tmp_path: Path):
    from mekhane.organon.tool_sensor import read_tool_sensor_log

    log_path = tmp_path / "tool_sensor_alpha.jsonl"
    log_path.write_text(
        textwrap.dedent(
            """
            not-json
            {"timestamp":"2026-04-23T00:00:00Z","session_id":"alpha","sensor":"tool","source_event":"PostToolUse","output_type":"gate-only","tool":"Read","quadrant":"S","axis_hints":{},"confidence":"direct","requires_semantic_fallback":false,"evidence":{}}
            {"timestamp":"2026-04-23T00:00:01Z","session_id":"alpha","sensor":"tool","source_event":"PostToolUse","output_type":"48-seed","tool":"Task","quadrant":"A","axis_hints":{"function":"explore"},"confidence":"direct","requires_semantic_fallback":true,"evidence":{"tool_name":"Task"}}
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    readings = read_tool_sensor_log(log_path=log_path)

    assert len(readings) == 1
    assert readings[0].tool == "Task"
    assert readings[0].requires_semantic_fallback is True


def test_tool_sensor_log_path_picks_latest_file(tmp_path: Path):
    from mekhane.organon.tool_sensor import tool_sensor_log_path

    old_path = tmp_path / "tool_sensor_old.jsonl"
    new_path = tmp_path / "tool_sensor_new.jsonl"
    old_path.write_text("", encoding="utf-8")
    new_path.write_text("", encoding="utf-8")
    os.utime(old_path, (1, 1))
    os.utime(new_path, (2, 2))

    latest = tool_sensor_log_path(log_dir=tmp_path)

    assert latest == new_path


def test_summarize_tool_sensor_counts_quadrants_and_fallbacks(tmp_path: Path):
    from mekhane.organon.tool_sensor import read_tool_sensor_log, summarize_tool_sensor

    log_path = tmp_path / "tool_sensor_alpha.jsonl"
    log_path.write_text(
        textwrap.dedent(
            """
            {"timestamp":"2026-04-23T00:00:00Z","session_id":"alpha","sensor":"tool","source_event":"PostToolUse","output_type":"48-seed","tool":"Read","quadrant":"S","axis_hints":{"scale":"micro"},"confidence":"direct","requires_semantic_fallback":false,"evidence":{"tool_name":"Read"}}
            {"timestamp":"2026-04-23T00:00:01Z","session_id":"alpha","sensor":"tool","source_event":"PostToolUse","output_type":"48-seed","tool":"Task","quadrant":"A","axis_hints":{"function":"explore"},"confidence":"direct","requires_semantic_fallback":true,"evidence":{"tool_name":"Task"}}
            {"timestamp":"2026-04-23T00:00:02Z","session_id":"alpha","sensor":"tool","source_event":"PostToolUse","output_type":"48-seed","tool":"Write","quadrant":"A","axis_hints":{"scale":"micro"},"confidence":"direct","requires_semantic_fallback":false,"evidence":{"tool_name":"Write"}}
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    snapshot = summarize_tool_sensor(read_tool_sensor_log(log_path=log_path))

    assert snapshot.session_id == "alpha"
    assert snapshot.reading_count == 3
    assert snapshot.counts_by_quadrant == {"S": 1, "A": 2}
    assert snapshot.counts_by_tool == {"Read": 1, "Task": 1, "Write": 1}
    assert snapshot.semantic_fallback_count == 1
    assert snapshot.latest_timestamp == "2026-04-23T00:00:02Z"
