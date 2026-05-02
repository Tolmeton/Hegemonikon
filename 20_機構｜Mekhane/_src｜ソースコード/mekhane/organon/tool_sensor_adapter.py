from __future__ import annotations

# PROOF: [L2/Organon] <- Tool Sensor 48-seed → Layer α adapter
"""Adapter from Tool Sensor seed readings to Layer α candidate inputs."""

from dataclasses import dataclass

from mekhane.fep.basis import HelmholtzComponent, get_operator
from mekhane.fep.mapping import map_to_verb

from .sensor_reading import SensorReading
from .tool_sensor import ToolSeedReading


_AXIS_TO_COORDINATE: dict[str, str] = {
    "function": "Function",
    "precision": "Precision",
    "scale": "Scale",
    "valence": "Valence",
    "temporality": "Temporality",
    "value": "Value",
}

_POLARITY_TO_COMPONENT: dict[str, dict[str, HelmholtzComponent]] = {
    "function": {
        "explore": HelmholtzComponent.SOLENOIDAL,
        "exploit": HelmholtzComponent.GRADIENT,
    },
    "precision": {
        "uncertain": HelmholtzComponent.SOLENOIDAL,
        "certain": HelmholtzComponent.GRADIENT,
    },
    "scale": {
        "macro": HelmholtzComponent.SOLENOIDAL,
        "micro": HelmholtzComponent.GRADIENT,
    },
    "valence": {
        "negative": HelmholtzComponent.SOLENOIDAL,
        "-": HelmholtzComponent.SOLENOIDAL,
        "positive": HelmholtzComponent.GRADIENT,
        "+": HelmholtzComponent.GRADIENT,
    },
    "temporality": {
        "past": HelmholtzComponent.SOLENOIDAL,
        "future": HelmholtzComponent.GRADIENT,
    },
    "value": {
        "epistemic": HelmholtzComponent.SOLENOIDAL,
        "recognition": HelmholtzComponent.SOLENOIDAL,
        "pragmatic": HelmholtzComponent.GRADIENT,
        "practical": HelmholtzComponent.GRADIENT,
    },
}


@dataclass(frozen=True, slots=True)
class LayerAlphaSeed:
    """Minimal Layer α candidate derived from one 48-seed reading."""

    timestamp: str
    session_id: str
    tool: str
    quadrant: str
    coordinate: str
    axis_name: str
    axis_value: str
    ccl_name: str
    greek_name: str
    helmholtz_component: str
    requires_semantic_fallback: bool
    weight_map: dict[str, float]


LayerAlphaSensorReading = SensorReading


def _first_supported_axis(axis_hints: dict[str, str]) -> tuple[str, str] | None:
    for axis_name in ("value", "function", "precision", "scale", "valence", "temporality"):
        axis_value = axis_hints.get(axis_name)
        if axis_value:
            return axis_name, axis_value
    return None


def project_tool_seed(reading: ToolSeedReading) -> LayerAlphaSeed | None:
    """Project one Tool Sensor reading into a Layer α candidate verb.

    Returns None when the seed is too coarse to select a unique coordinate/component
    pair and should therefore stay in semantic fallback.
    """
    axis = _first_supported_axis(reading.axis_hints)
    if axis is None:
        return None

    axis_name, axis_value = axis
    component = _POLARITY_TO_COMPONENT.get(axis_name, {}).get(axis_value.lower())
    if component is None:
        return None

    coordinate = _AXIS_TO_COORDINATE[axis_name]
    operator = get_operator(coordinate, component)
    if operator is None:
        return None

    verb = map_to_verb(operator, reading.quadrant)
    if verb is None:
        return None

    return LayerAlphaSeed(
        timestamp=reading.timestamp,
        session_id=reading.session_id,
        tool=reading.tool,
        quadrant=reading.quadrant,
        coordinate=coordinate,
        axis_name=axis_name,
        axis_value=axis_value,
        ccl_name=verb.ccl_name,
        greek_name=verb.greek_name,
        helmholtz_component=operator.component.value,
        requires_semantic_fallback=reading.requires_semantic_fallback,
        weight_map={verb.ccl_name: 1.0},
    )


def project_tool_sensor(readings: list[ToolSeedReading]) -> list[LayerAlphaSeed]:
    """Project all directly mappable Tool Sensor readings to Layer α seeds."""
    projected: list[LayerAlphaSeed] = []
    for reading in readings:
        seed = project_tool_seed(reading)
        if seed is not None:
            projected.append(seed)
    return projected


def aggregate_layer_alpha_seeds(seeds: list[LayerAlphaSeed]) -> SensorReading:
    """Aggregate Layer α seeds into one sparse session vector.

    The vector is frequency-normalized across candidate verbs so it can serve as
    a thin Tool Sensor contribution to the common SensorReading surface.
    """
    if not seeds:
        return SensorReading(
            timestamp=None,
            session_id="unknown",
            sensor="tool",
            confidence="direct",
            vector={},
            evidence={
                "seed_count": 0,
                "counts_by_ccl": {},
                "counts_by_quadrant": {},
                "semantic_fallback_count": 0,
            },
        )

    counts_by_ccl: dict[str, int] = {}
    counts_by_quadrant: dict[str, int] = {}
    semantic_fallback_count = 0

    for seed in seeds:
        counts_by_ccl[seed.ccl_name] = counts_by_ccl.get(seed.ccl_name, 0) + 1
        counts_by_quadrant[seed.quadrant] = counts_by_quadrant.get(seed.quadrant, 0) + 1
        if seed.requires_semantic_fallback:
            semantic_fallback_count += 1

    total = sum(counts_by_ccl.values())
    vector = {
        ccl_name: count / total
        for ccl_name, count in sorted(counts_by_ccl.items())
    }

    latest_timestamp = max(seed.timestamp for seed in seeds)

    return SensorReading(
        timestamp=latest_timestamp,
        session_id=seeds[0].session_id,
        sensor="tool",
        confidence="direct",
        vector=vector,
        evidence={
            "seed_count": len(seeds),
            "counts_by_ccl": counts_by_ccl,
            "counts_by_quadrant": counts_by_quadrant,
            "semantic_fallback_count": semantic_fallback_count,
        },
    )
