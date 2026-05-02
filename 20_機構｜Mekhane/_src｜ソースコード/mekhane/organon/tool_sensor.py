from __future__ import annotations

# PROOF: [L2/Organon] <- tool sensor ingress for PostToolUse 48-seed logs
"""Reader for Organon Tool Sensor seed logs.

This module reads the `tool_sensor_<session_id>.jsonl` files emitted by the
Claude Code `PostToolUse` hook and normalizes them into a small runtime-facing
API. The reader is intentionally thin: it trusts the hook as the ingress layer
and only performs schema checks plus coarse aggregation.
"""

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ToolSeedReading:
    """Normalized Tool Sensor reading derived from a hook JSONL line."""

    timestamp: str
    session_id: str
    sensor: str
    source_event: str
    output_type: str
    tool: str
    quadrant: str
    axis_hints: dict[str, str]
    confidence: str
    requires_semantic_fallback: bool
    evidence: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ToolSeedReading":
        """Build a reading from one JSON object.

        Raises:
            KeyError: required fields are missing
            TypeError: field types are structurally invalid
            ValueError: output type is not a 48-seed record
        """
        output_type = str(payload["output_type"])
        if output_type != "48-seed":
            raise ValueError(f"unsupported output_type: {output_type}")

        axis_hints = payload.get("axis_hints", {}) or {}
        if not isinstance(axis_hints, dict):
            raise TypeError("axis_hints must be a dict")

        evidence = payload.get("evidence", {}) or {}
        if not isinstance(evidence, dict):
            raise TypeError("evidence must be a dict")

        return cls(
            timestamp=str(payload["timestamp"]),
            session_id=str(payload["session_id"]),
            sensor=str(payload["sensor"]),
            source_event=str(payload["source_event"]),
            output_type=output_type,
            tool=str(payload["tool"]),
            quadrant=str(payload["quadrant"]),
            axis_hints={str(k): str(v) for k, v in axis_hints.items()},
            confidence=str(payload["confidence"]),
            requires_semantic_fallback=bool(payload.get("requires_semantic_fallback", False)),
            evidence=evidence,
        )


@dataclass(frozen=True, slots=True)
class ToolSensorSnapshot:
    """Small aggregate view of a session's Tool Sensor ingress."""

    session_id: str
    reading_count: int
    counts_by_quadrant: dict[str, int]
    counts_by_tool: dict[str, int]
    semantic_fallback_count: int
    latest_timestamp: str | None


def default_tool_sensor_log_dir() -> Path:
    """Return the hook log directory used by Tool Sensor."""
    override = os.environ.get("CLAUDE_HOOK_LOG_DIR", "").strip()
    if override:
        return Path(override)
    return Path.home() / ".claude" / "hooks" / "logs"


def tool_sensor_log_path(
    session_id: str | None = None,
    *,
    log_dir: str | Path | None = None,
) -> Path:
    """Resolve a tool sensor log path.

    If `session_id` is omitted, the most recently modified tool sensor log in
    the directory is returned.
    """
    base_dir = Path(log_dir) if log_dir is not None else default_tool_sensor_log_dir()
    if session_id:
        return base_dir / f"tool_sensor_{session_id}.jsonl"

    candidates = sorted(
        base_dir.glob("tool_sensor_*.jsonl"),
        key=lambda path: (path.stat().st_mtime, path.name),
    )
    if not candidates:
        raise FileNotFoundError(f"no tool sensor logs found in {base_dir}")
    return candidates[-1]


def read_tool_sensor_log(
    session_id: str | None = None,
    *,
    log_path: str | Path | None = None,
    log_dir: str | Path | None = None,
    strict: bool = False,
) -> list[ToolSeedReading]:
    """Read one Tool Sensor JSONL file and return normalized readings.

    Non-JSON and non-48-seed lines are ignored by default so the reader can
    survive mixed or partially written logs. Set `strict=True` to surface the
    first malformed line as an exception.
    """
    resolved_path = Path(log_path) if log_path is not None else tool_sensor_log_path(session_id, log_dir=log_dir)
    readings: list[ToolSeedReading] = []
    with resolved_path.open(encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
                reading = ToolSeedReading.from_dict(payload)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                if strict:
                    raise
                continue
            readings.append(reading)
    return readings


def summarize_tool_sensor(readings: list[ToolSeedReading]) -> ToolSensorSnapshot:
    """Aggregate raw readings into a session-level ingress snapshot."""
    if not readings:
        return ToolSensorSnapshot(
            session_id="unknown",
            reading_count=0,
            counts_by_quadrant={},
            counts_by_tool={},
            semantic_fallback_count=0,
            latest_timestamp=None,
        )

    counts_by_quadrant: dict[str, int] = {}
    counts_by_tool: dict[str, int] = {}
    semantic_fallback_count = 0

    for reading in readings:
        counts_by_quadrant[reading.quadrant] = counts_by_quadrant.get(reading.quadrant, 0) + 1
        counts_by_tool[reading.tool] = counts_by_tool.get(reading.tool, 0) + 1
        if reading.requires_semantic_fallback:
            semantic_fallback_count += 1

    latest_timestamp = max(reading.timestamp for reading in readings)

    return ToolSensorSnapshot(
        session_id=readings[0].session_id,
        reading_count=len(readings),
        counts_by_quadrant=counts_by_quadrant,
        counts_by_tool=counts_by_tool,
        semantic_fallback_count=semantic_fallback_count,
        latest_timestamp=latest_timestamp,
    )
