# PROOF: mekhane/tests/test_text_sensor.py
# PURPOSE: Organon Text Sensor emits the common SensorReading surface
"""Tests for mekhane.organon.text_sensor."""


def test_analyze_text_sensor_returns_common_reading_for_slash_verbs():
    from mekhane.organon import SensorReading, analyze_text_sensor

    reading = analyze_text_sensor(
        "Use /noe before /tek+. Then /noe again.",
        session_id="alpha",
        timestamp="2026-04-24T00:00:00Z",
    )

    assert isinstance(reading, SensorReading)
    assert reading.timestamp == "2026-04-24T00:00:00Z"
    assert reading.session_id == "alpha"
    assert reading.sensor == "text"
    assert reading.confidence == "direct"
    assert reading.vector == {"noe": 2 / 3, "tek": 1 / 3}
    assert reading.evidence["counts_by_ccl"] == {"noe": 2, "tek": 1}


def test_analyze_text_sensor_ignores_h_series_brackets():
    from mekhane.organon import analyze_text_sensor

    reading = analyze_text_sensor("The text names [th] and [ph], but no Poiesis slash verb.")

    assert reading.vector == {}
    assert reading.evidence["match_count"] == 0


def test_analyze_text_sensor_does_not_match_bare_words():
    from mekhane.organon import analyze_text_sensor

    reading = analyze_text_sensor("noe and tek are bare words here, not explicit commands.")

    assert reading.vector == {}
