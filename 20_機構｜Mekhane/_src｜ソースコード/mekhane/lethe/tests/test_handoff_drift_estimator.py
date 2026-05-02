# PROOF: [L3/テスト] <- mekhane/lethe/handoff_drift_estimator.py synthetic χ calibration and trajectory ordering
"""
Tests for the handoff drift estimator.
"""

from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


from mekhane.lethe.handoff_drift_estimator import estimate_drift


def test_estimate_drift_recovers_known_half_chi():
    synthetic_pairs = [
        _make_synthetic_pair(f"pair-{index}", carrier_step=2, null_step=1)
        for index in range(100)
    ]

    result = estimate_drift(synthetic_pairs, mode="slot", p=0.5, kappa_c=0.5, epsilon=0.2)

    assert result["summary"]["mean_chi_characteristic"] == pytest.approx(0.5, abs=0.1)


def test_type1_recovery_has_lower_chi_than_type2_dead_end_loop():
    result = estimate_drift(
        [
            _make_synthetic_pair("type1-clue-recovery", carrier_step=3, null_step=1),
            _make_synthetic_pair("type2-dead-end-loop", carrier_step=1, null_step=2),
        ],
        mode="slot",
        p=0.5,
        kappa_c=0.5,
        epsilon=0.2,
    )

    pairs = {item["pair_id"]: item for item in result["pair_results"]}

    assert pairs["type1-clue-recovery"]["chi_characteristic"] < pairs["type2-dead-end-loop"]["chi_characteristic"]


def _make_synthetic_pair(pair_id: str, carrier_step: int, null_step: int, units: int = 14, turns: int = 6) -> dict:
    atomic_units = [f"memory unit {index}" for index in range(units)]
    support_scores = []
    margin_scores = []
    carrier_front = -1
    null_front = -1

    for _ in range(turns):
        carrier_front = min(units - 1, carrier_front + carrier_step)
        null_front = min(units - 1, null_front + null_step)

        support_row = [0.9 if index <= carrier_front else 0.05 for index in range(units)]
        margin_row = [0.0 if index <= null_front else 0.85 for index in range(units)]
        support_scores.append(support_row)
        margin_scores.append(margin_row)

    return {
        "pair_id": pair_id,
        "pre_handoff_turns": atomic_units,
        "post_handoff_turns": [f"turn {index}" for index in range(turns)],
        "atomic_units": atomic_units,
        "support_scores": support_scores,
        "margin_scores": margin_scores,
    }
