from __future__ import annotations

# PROOF: [L2/Organon] <- common SensorReading surface for Sensor Triad
"""Common SensorReading surface for Organon sensors."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SensorReading:
    """Common sparse-vector reading emitted by Tool/Text/Being sensors."""

    timestamp: str | None
    session_id: str
    sensor: str
    confidence: str
    vector: dict[str, float]
    evidence: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "sensor": self.sensor,
            "confidence": self.confidence,
            "vector": dict(self.vector),
            "evidence": dict(self.evidence),
        }
