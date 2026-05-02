# PROOF: [L3/テスト] <- mekhane/lethe/type_classifier.py synthetic Type 1/2/3 separability and recall reporting
"""Tests for the Lethe Type 1/2/3 classifier."""

from pathlib import Path
import sys

import numpy as np


sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


from mekhane.lethe.type_classifier import (
    FEATURE_NAMES,
    TypeClassifier,
    classify_trajectory,
    extract_features,
)


def test_extract_features_returns_12_dimensional_feature_dict():
    trajectory = _make_type_trajectory(1, 0)

    features = extract_features(trajectory)

    assert list(features) == FEATURE_NAMES
    assert len(features) == 12
    assert all(0.0 <= value <= 1.0 for value in features.values())


def test_type_classifier_fit_predict_reaches_synthetic_accuracy_floor():
    trajectories, labels = _build_synthetic_dataset()
    accuracies = {}

    for model_type in ("logistic", "random_forest", "mlp"):
        classifier = TypeClassifier(model_type=model_type, k_tail=5, random_state=11, max_iter=600)
        classifier.fit(trajectories, labels)
        predictions = classifier.predict(trajectories)
        accuracy = float(np.mean(predictions == labels))
        accuracies[model_type] = accuracy

        assert predictions.shape == labels.shape
        assert set(classifier.get_feature_importance()) == set(FEATURE_NAMES)

    assert max(accuracies.values()) >= 0.55

    report = classify_trajectory(trajectories[0], classifier=TypeClassifier(model_type="random_forest", k_tail=5, random_state=13).fit(trajectories, labels))
    assert report["predicted_type"] in {1, 2, 3}
    assert len(report["root_cause_features"]) >= 1


def test_get_per_type_recall_returns_three_type_dict():
    trajectories, labels = _build_synthetic_dataset()
    classifier = TypeClassifier(model_type="random_forest", k_tail=5, random_state=17)
    classifier.fit(trajectories, labels)

    recall = classifier.get_per_type_recall(trajectories, labels)

    assert set(recall) == {1, 2, 3}
    assert all(0.0 <= value <= 1.0 for value in recall.values())


def _build_synthetic_dataset() -> tuple[list[dict], np.ndarray]:
    trajectories: list[dict] = []
    labels: list[int] = []
    for label in (1, 2, 3):
        for seed in range(20):
            trajectories.append(_make_type_trajectory(label, seed))
            labels.append(label)
    return trajectories, np.asarray(labels)


def _make_type_trajectory(label: int, seed: int) -> dict:
    if label == 1:
        clue = f"needle_{seed}"
        return {
            "query": "find the useful clue and answer with it",
            "final_focus": f"the final clue is {clue}",
            "final_answer": f"use {clue} to open the archive",
            "summary": "archive notes, old debris, unresolved hints",
            "turns": [
                {"action": "scan_room", "observation": "dusty room", "tau": 0.20, "progress": 0.12},
                {"action": "read_index", "observation": "index fragments", "tau": 0.35, "progress": 0.22},
                {
                    "action": "inspect_recent_clue",
                    "clue": clue,
                    "observation": f"fresh clue says {clue}",
                    "tau": 0.62,
                    "progress": 0.55,
                    "clue_hit": True,
                },
                {
                    "action": "connect_clue",
                    "reasoning": f"{clue} directly matches the useful trail",
                    "tau": 0.82,
                    "progress": 0.74,
                },
                {
                    "action": "answer",
                    "hypothesis": f"{clue} is the useful clue",
                    "answer": f"use {clue} to open the archive",
                    "tau": 0.94,
                    "progress": 0.92,
                    "hypothesis_confidence": 0.84,
                    "action_relevance": 0.88,
                    "action_gain": 0.80,
                },
            ],
        }

    if label == 2:
        action = f"retry_pdf_loop_{seed % 3}"
        return {
            "query": "escape the dead-end search loop",
            "final_focus": "still trapped in the same document search",
            "summary": "same pdf opened again and again",
            "turns": [
                {"action": action, "observation": "same pdf page", "tau": 0.44, "progress": 0.10, "dead_end": True},
                {"action": action, "observation": "same pdf page", "tau": 0.30, "progress": 0.08, "dead_end": True},
                {"action": action, "observation": "same pdf page", "tau": 0.22, "progress": 0.05, "dead_end": True},
                {"action": action, "observation": "same pdf page", "tau": 0.14, "progress": 0.04, "dead_end": True},
                {
                    "action": action,
                    "observation": "same pdf page",
                    "tau": 0.08,
                    "progress": 0.03,
                    "dead_end": True,
                    "hypothesis_confidence": 0.34,
                    "action_relevance": 0.26,
                    "action_gain": 0.12,
                },
            ],
        }

    if label == 3:
        hypothesis = f"artifact_{seed}"
        return {
            "query": "identify the correct artifact and act on it",
            "final_focus": f"{hypothesis} is the correct artifact",
            "summary": f"correct artifact {hypothesis} identified but execution drifts",
            "counterfactual_gain_gap": 0.81,
            "turns": [
                {"action": "inspect_board", "observation": f"artifact marker {hypothesis}", "tau": 0.62, "progress": 0.26},
                {
                    "action": "state_hypothesis",
                    "hypothesis": f"{hypothesis} is correct",
                    "reasoning": f"{hypothesis} is clearly the correct artifact",
                    "tau": 0.69,
                    "progress": 0.28,
                },
                {"action": "adjust_sidebar", "observation": "UI sidebar moved", "tau": 0.68, "progress": 0.14},
                {"action": "sort_by_timestamp", "observation": "table resorted", "tau": 0.66, "progress": 0.12},
                {
                    "action": "open_unrelated_panel",
                    "hypothesis": f"{hypothesis} remains correct",
                    "reasoning": f"{hypothesis} is still the right artifact",
                    "tau": 0.64,
                    "progress": 0.10,
                    "hypothesis_confidence": 0.93,
                    "action_relevance": 0.15,
                    "action_gain": 0.08,
                    "candidate_action_gain": 0.89,
                },
            ],
        }

    raise ValueError(f"Unsupported synthetic type: {label}")
