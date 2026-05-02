from __future__ import annotations

# PROOF: [L2/Organon] <- session observe orchestration for Sensor Triad
"""Session-level observe entrypoint for Organon Sensor Triad."""

from dataclasses import dataclass
from pathlib import Path

from .diagnostics import DiagnosticFinding, diagnose_tool_text
from .sensor_reading import SensorReading
from .text_sensor import analyze_text_sensor
from .tool_sensor import read_tool_sensor_log
from .tool_sensor_adapter import aggregate_layer_alpha_seeds, project_tool_sensor


@dataclass(frozen=True, slots=True)
class SessionObservation:
    """Tool/Text observation result for one session turn or transcript chunk."""

    session_id: str
    tool_reading: SensorReading
    text_reading: SensorReading
    findings: list[DiagnosticFinding]

    def to_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "tool_reading": self.tool_reading.to_dict(),
            "text_reading": self.text_reading.to_dict(),
            "findings": [finding.to_dict() for finding in self.findings],
        }


def observe_session(
    assistant_text: str,
    *,
    session_id: str | None = None,
    timestamp: str | None = None,
    tool_log_path: str | Path | None = None,
    tool_log_dir: str | Path | None = None,
    strict: bool = False,
) -> SessionObservation:
    """Observe one session using Tool Sensor logs plus assistant text."""
    tool_seed_readings = read_tool_sensor_log(
        session_id,
        log_path=tool_log_path,
        log_dir=tool_log_dir,
        strict=strict,
    )
    layer_alpha_seeds = project_tool_sensor(tool_seed_readings)
    tool_reading = aggregate_layer_alpha_seeds(layer_alpha_seeds)

    resolved_session_id = session_id or tool_reading.session_id
    text_reading = analyze_text_sensor(
        assistant_text,
        session_id=resolved_session_id,
        timestamp=timestamp,
    )
    findings = diagnose_tool_text(tool_reading, text_reading)

    return SessionObservation(
        session_id=resolved_session_id,
        tool_reading=tool_reading,
        text_reading=text_reading,
        findings=findings,
    )
