# PROOF: [L2/インフラ] <- lethe/type_classifier.py Brief 2 Task 2 — Type 1/2/3 state classifier
"""Type 1/2/3 state classifier utilities without external model APIs."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import math
import re
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import recall_score
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

__all__ = [
    "FEATURE_NAMES",
    "TypeClassifier",
    "classify_trajectory",
    "extract_features",
]

FEATURE_NAMES = [
    "recent_clue_hit",
    "recent_clue_reuse",
    "tau_tail_slope",
    "summary_loss_risk",
    "action_repeat_ratio",
    "dead_end_tail_retention",
    "loop_closure_score",
    "tau_collapse_score",
    "hypothesis_confidence",
    "action_relevance",
    "hyp_act_gap",
    "counterfactual_gain_gap",
]

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
_EPSILON = 1e-9
_ALLOWED_K_TAIL = {3, 5}
_EMBEDDING_MODEL_NAME = "hash-bow-v1"


@dataclass(frozen=True)
class FeatureConfig:
    """Configuration for feature extraction."""

    k_tail: int = 5
    embedding_dim: int = 32
    root_cause_top_n: int = 4

    def __post_init__(self) -> None:
        if self.k_tail not in _ALLOWED_K_TAIL:
            raise ValueError(f"k_tail must be one of {_ALLOWED_K_TAIL}")
        if self.embedding_dim <= 0:
            raise ValueError("embedding_dim must be positive")
        if self.root_cause_top_n <= 0:
            raise ValueError("root_cause_top_n must be positive")


@dataclass(frozen=True)
class _FeatureBundle:
    features: dict[str, float]
    missing_mask: dict[str, float]
    metadata: dict[str, Any]


def extract_features(trajectory: dict) -> dict[str, float]:
    """Return the normalized 12-dimensional feature vector for a trajectory."""

    config = _config_from_trajectory(trajectory)
    return _extract_feature_bundle(trajectory, config).features


class TypeClassifier:
    """Trainable classifier wrapper for Type 1/2/3 state prediction."""

    def __init__(
        self,
        model_type: str = "logistic",
        *,
        k_tail: int = 5,
        random_state: int = 7,
        max_iter: int = 400,
        hidden_layer_sizes: tuple[int, ...] = (16, 8),
        confidence_threshold: float | None = None,
        abstain_label: Any = 0,
    ) -> None:
        self.config = FeatureConfig(k_tail=k_tail)
        self.model_type = model_type
        self.random_state = random_state
        self.max_iter = max_iter
        self.hidden_layer_sizes = hidden_layer_sizes
        self.confidence_threshold = confidence_threshold
        self.abstain_label = abstain_label
        self.estimator = self._build_estimator()
        self.classes_: np.ndarray | None = None
        self._is_fitted = False

    def fit(self, X: Any, y: Sequence[Any]) -> "TypeClassifier":
        matrix = self._coerce_matrix(X)
        labels = np.asarray(list(y))
        if matrix.shape[0] != labels.shape[0]:
            raise ValueError("X and y must contain the same number of samples")
        self.estimator.fit(matrix, labels)
        self.classes_ = np.asarray(self.estimator.classes_)
        self._is_fitted = True
        return self

    def predict(self, X: Any) -> np.ndarray:
        probabilities = self.predict_proba(X)
        class_index = np.argmax(probabilities, axis=1)
        predictions = np.asarray(self.classes_)[class_index]
        if self.confidence_threshold is None:
            return predictions
        confidence = np.max(probabilities, axis=1)
        masked = predictions.astype(object)
        masked[confidence < self.confidence_threshold] = self.abstain_label
        return masked

    def predict_proba(self, X: Any) -> np.ndarray:
        self._require_fitted()
        matrix = self._coerce_matrix(X)
        return self.estimator.predict_proba(matrix)

    def get_per_type_recall(self, X: Any, y: Sequence[Any]) -> dict[Any, float]:
        labels = np.asarray(list(y))
        predictions = self.predict(X)
        active_labels = np.asarray(self.classes_)
        scores = recall_score(
            labels,
            predictions,
            labels=active_labels,
            average=None,
            zero_division=0,
        )
        return {label: float(score) for label, score in zip(active_labels, scores)}

    def get_feature_importance(self) -> dict[str, float]:
        self._require_fitted()
        combined = self._combined_importance_vector()
        total = float(np.sum(combined))
        if total <= _EPSILON:
            return {name: 1.0 / len(FEATURE_NAMES) for name in FEATURE_NAMES}
        return {
            name: float(combined[index] / total)
            for index, name in enumerate(FEATURE_NAMES)
        }

    def _build_estimator(self) -> Any:
        model_type = self.model_type.lower()
        if model_type == "logistic":
            return Pipeline(
                [
                    ("scale", StandardScaler()),
                    (
                        "clf",
                        LogisticRegression(
                            class_weight="balanced",
                            max_iter=self.max_iter,
                            random_state=self.random_state,
                        ),
                    ),
                ]
            )
        if model_type == "random_forest":
            return RandomForestClassifier(
                class_weight="balanced",
                n_estimators=240,
                min_samples_leaf=1,
                random_state=self.random_state,
            )
        if model_type == "mlp":
            return Pipeline(
                [
                    ("scale", StandardScaler()),
                    (
                        "clf",
                        MLPClassifier(
                            hidden_layer_sizes=self.hidden_layer_sizes,
                            activation="relu",
                            alpha=1e-3,
                            learning_rate_init=0.01,
                            max_iter=self.max_iter,
                            random_state=self.random_state,
                        ),
                    ),
                ]
            )
        raise ValueError("model_type must be one of: logistic, random_forest, mlp")

    def _coerce_matrix(self, X: Any) -> np.ndarray:
        if isinstance(X, np.ndarray):
            array = np.asarray(X, dtype=float)
            if array.ndim == 1:
                array = array.reshape(1, -1)
            return self._coerce_numeric_matrix(array)

        if isinstance(X, Mapping):
            bundles = [self._bundle_from_mapping(X)]
        elif isinstance(X, Sequence) and not isinstance(X, (str, bytes)):
            bundles = [self._bundle_from_mapping(item) for item in X]
        else:
            raise TypeError("X must be an ndarray, a mapping, or a sequence of mappings")

        vectors = [self._bundle_to_vector(bundle) for bundle in bundles]
        return np.vstack(vectors)

    def _coerce_numeric_matrix(self, matrix: np.ndarray) -> np.ndarray:
        feature_count = len(FEATURE_NAMES)
        if matrix.shape[1] == feature_count:
            missing_mask = np.zeros_like(matrix)
            return np.concatenate([matrix, missing_mask], axis=1)
        if matrix.shape[1] == feature_count * 2:
            return matrix
        raise ValueError(
            f"Expected {feature_count} features or {feature_count * 2} features+mask columns"
        )

    def _bundle_from_mapping(self, item: Any) -> _FeatureBundle:
        if not isinstance(item, Mapping):
            raise TypeError("Each sample must be a mapping when not using ndarray input")
        if _looks_like_trajectory(item):
            merged = dict(item)
            merged.setdefault("k_tail", self.config.k_tail)
            return _extract_feature_bundle(merged, self.config)
        features = {
            name: _clip01(item.get(name, 0.5))
            for name in FEATURE_NAMES
        }
        raw_mask = item.get("missing_mask", {})
        missing_mask = {
            name: _clip01(raw_mask.get(name, 0.0 if name in item else 1.0))
            for name in FEATURE_NAMES
        }
        return _FeatureBundle(
            features=features,
            missing_mask=missing_mask,
            metadata={"source": "feature_dict", "embedding_model": _EMBEDDING_MODEL_NAME},
        )

    def _bundle_to_vector(self, bundle: _FeatureBundle) -> np.ndarray:
        values = [bundle.features[name] for name in FEATURE_NAMES]
        missing = [bundle.missing_mask[name] for name in FEATURE_NAMES]
        return np.asarray(values + missing, dtype=float)

    def _combined_importance_vector(self) -> np.ndarray:
        feature_count = len(FEATURE_NAMES)
        estimator = self.estimator.named_steps["clf"] if isinstance(self.estimator, Pipeline) else self.estimator
        if hasattr(estimator, "feature_importances_"):
            raw = np.asarray(estimator.feature_importances_, dtype=float)
        elif hasattr(estimator, "coef_"):
            raw = np.mean(np.abs(np.asarray(estimator.coef_, dtype=float)), axis=0)
        elif hasattr(estimator, "coefs_"):
            raw = np.mean(np.abs(np.asarray(estimator.coefs_[0], dtype=float)), axis=1)
        else:
            raw = np.ones(feature_count * 2, dtype=float)

        if raw.shape[0] < feature_count * 2:
            padded = np.zeros(feature_count * 2, dtype=float)
            padded[: raw.shape[0]] = raw
            raw = padded

        return raw[:feature_count] + raw[feature_count : feature_count * 2]

    def _require_fitted(self) -> None:
        if not self._is_fitted or self.classes_ is None:
            raise RuntimeError("TypeClassifier must be fitted before inference")


def classify_trajectory(trajectory: dict, classifier: TypeClassifier) -> dict[str, Any]:
    """Classify one trajectory and return probabilities plus root-cause features."""

    classifier._require_fitted()
    bundle = _extract_feature_bundle(trajectory, classifier.config)
    vector = classifier._bundle_to_vector(bundle).reshape(1, -1)
    probabilities = classifier.estimator.predict_proba(vector)[0]
    classes = list(classifier.classes_)
    probability_map = {
        label: float(probability)
        for label, probability in zip(classes, probabilities)
    }
    predicted = classes[int(np.argmax(probabilities))]
    if classifier.confidence_threshold is not None and max(probabilities) < classifier.confidence_threshold:
        predicted = classifier.abstain_label

    importance_map = classifier.get_feature_importance()
    ranked = []
    for name in FEATURE_NAMES:
        centered_value = abs(bundle.features[name] - 0.5)
        score = importance_map[name] * centered_value
        if bundle.missing_mask[name] > 0.5:
            score += importance_map[name] * 0.25
            signal = "missing"
        else:
            signal = "high" if bundle.features[name] >= 0.5 else "low"
        ranked.append(
            {
                "feature": name,
                "value": float(bundle.features[name]),
                "importance": float(importance_map[name]),
                "signal": signal,
                "score": float(score),
            }
        )
    ranked.sort(key=lambda item: item["score"], reverse=True)

    return {
        "predicted_type": predicted,
        "probabilities": probability_map,
        "features": dict(bundle.features),
        "missing_mask": dict(bundle.missing_mask),
        "root_cause_features": ranked[: classifier.config.root_cause_top_n],
        "metadata": dict(bundle.metadata),
    }


def _extract_feature_bundle(trajectory: Mapping[str, Any], config: FeatureConfig) -> _FeatureBundle:
    turns = _get_turns(trajectory)
    tail = turns[-config.k_tail :] if turns else []
    prior_turns = turns[: max(len(turns) - len(tail), 0)]

    final_focus_text = _join_text(
        trajectory.get("final_focus"),
        trajectory.get("focus"),
        trajectory.get("final_hypothesis"),
        _last_value(turns, "hypothesis"),
        _last_value(turns, "focus"),
    )
    final_answer_text = _join_text(
        trajectory.get("final_answer"),
        trajectory.get("answer"),
        _last_value(turns, "answer"),
        _last_value(turns, "response"),
    )
    query_text = _join_text(trajectory.get("query"), trajectory.get("task"))
    target_text = _join_text(query_text, final_focus_text, final_answer_text)
    target_embedding = _embed_text(target_text or query_text or final_focus_text, config.embedding_dim)

    tail_clue_text = " ".join(_extract_clue_text(turn) for turn in tail).strip()
    tail_clue_tokens = _tokenize(tail_clue_text)
    recent_window_text = " ".join(
        _join_text(turn.get("reasoning"), turn.get("answer"), turn.get("response"))
        for turn in tail[-2:]
    ).strip()

    recent_clue_hit = _feature_recent_clue_hit(tail, target_text)
    recent_clue_reuse = _feature_recent_clue_reuse(tail_clue_tokens, recent_window_text, final_answer_text, final_focus_text)
    tau_values = _compute_tau_values(turns, target_embedding, config.embedding_dim)
    tau_raw_slope = _mean_diff(tau_values[-config.k_tail :])
    tau_tail_slope = _clip01(0.5 + 0.5 * tau_raw_slope)

    summary_loss_risk = _feature_summary_loss_risk(
        trajectory,
        recent_clue_hit,
        tail_clue_tokens,
        prior_turns,
    )

    action_repeat_ratio = _feature_action_repeat_ratio(tail)
    progress_values = _progress_values(tail)
    mean_progress = float(np.mean(progress_values)) if progress_values else 0.0
    dead_end_tail_retention = _feature_dead_end_tail_retention(tail, action_repeat_ratio, mean_progress)
    loop_closure_score = _feature_loop_closure_score(turns, mean_progress, config.embedding_dim)
    tau_collapse_score = _clip01((1.0 - _mean_or_default(tau_values[-config.k_tail :], 0.5)) * 0.7 + max(0.0, -tau_raw_slope) * 0.3)

    hypothesis_confidence, hypothesis_missing = _feature_hypothesis_confidence(
        trajectory,
        turns,
        query_text,
        tail_clue_text,
        config.embedding_dim,
    )
    action_relevance, action_missing = _feature_action_relevance(
        trajectory,
        turns,
        target_text or final_focus_text or query_text,
        config.embedding_dim,
    )
    hyp_act_gap = _feature_gap(hypothesis_confidence, action_relevance)
    counterfactual_gain_gap, counterfactual_missing = _feature_counterfactual_gap(trajectory, turns)

    features = {
        "recent_clue_hit": recent_clue_hit,
        "recent_clue_reuse": recent_clue_reuse,
        "tau_tail_slope": tau_tail_slope,
        "summary_loss_risk": summary_loss_risk,
        "action_repeat_ratio": action_repeat_ratio,
        "dead_end_tail_retention": dead_end_tail_retention,
        "loop_closure_score": loop_closure_score,
        "tau_collapse_score": tau_collapse_score,
        "hypothesis_confidence": hypothesis_confidence,
        "action_relevance": action_relevance,
        "hyp_act_gap": hyp_act_gap,
        "counterfactual_gain_gap": counterfactual_gain_gap,
    }
    missing_mask = {
        "recent_clue_hit": 0.0,
        "recent_clue_reuse": 0.0,
        "tau_tail_slope": 0.0,
        "summary_loss_risk": 0.0,
        "action_repeat_ratio": 0.0,
        "dead_end_tail_retention": 0.0,
        "loop_closure_score": 0.0,
        "tau_collapse_score": 0.0,
        "hypothesis_confidence": float(hypothesis_missing),
        "action_relevance": float(action_missing),
        "hyp_act_gap": float(hypothesis_missing or action_missing),
        "counterfactual_gain_gap": float(counterfactual_missing),
    }

    metadata = {
        "embedding_model": _EMBEDDING_MODEL_NAME,
        "k_tail": config.k_tail,
        "tail_size": len(tail),
        "missing_features": [name for name, flag in missing_mask.items() if flag > 0.5],
    }
    return _FeatureBundle(features=features, missing_mask=missing_mask, metadata=metadata)


def _feature_recent_clue_hit(tail: list[dict[str, Any]], target_text: str) -> float:
    explicit = _explicit_number_from_items(tail, ("recent_clue_hit", "clue_hit"))
    if explicit is not None:
        return 1.0 if explicit >= 0.5 else 0.0
    target_tokens = set(_tokenize(target_text))
    if not target_tokens:
        return 0.0
    for turn in tail:
        clue_tokens = set(_tokenize(_extract_clue_text(turn)))
        if clue_tokens and clue_tokens & target_tokens:
            return 1.0
    return 0.0


def _feature_recent_clue_reuse(
    clue_tokens: list[str],
    recent_window_text: str,
    final_answer_text: str,
    final_focus_text: str,
) -> float:
    if not clue_tokens:
        return 0.0
    denominator = max(len(set(clue_tokens)), 1)
    reused_tokens = set(_tokenize(_join_text(recent_window_text, final_answer_text, final_focus_text)))
    if not reused_tokens:
        return 0.0
    return _clip01(len(set(clue_tokens) & reused_tokens) / denominator)


def _feature_summary_loss_risk(
    trajectory: Mapping[str, Any],
    recent_clue_hit: float,
    clue_tokens: list[str],
    prior_turns: list[dict[str, Any]],
) -> float:
    explicit = _extract_number(trajectory, ("summary_loss_risk",))
    if explicit is not None:
        return _clip01(explicit)
    if recent_clue_hit < 0.5 or not clue_tokens:
        return 0.0
    summary_text = _join_text(trajectory.get("summary"), trajectory.get("summary_text"))
    prior_text = " ".join(_turn_state_text(turn) for turn in prior_turns)
    summary_overlap = _token_overlap_ratio(clue_tokens, _tokenize(summary_text))
    prior_overlap = _token_overlap_ratio(clue_tokens, _tokenize(prior_text))
    return _clip01((1.0 - summary_overlap) * 0.65 + (1.0 - prior_overlap) * 0.35)


def _feature_action_repeat_ratio(tail: list[dict[str, Any]]) -> float:
    explicit = _explicit_number_from_items(tail, ("action_repeat_ratio",))
    if explicit is not None:
        return _clip01(explicit)
    actions = [_normalize_action(turn) for turn in tail if _normalize_action(turn)]
    if not actions:
        return 0.0
    counts = Counter(actions)
    return _clip01(max(counts.values()) / max(len(tail), 1))


def _feature_dead_end_tail_retention(
    tail: list[dict[str, Any]],
    action_repeat_ratio: float,
    mean_progress: float,
) -> float:
    explicit = _explicit_number_from_items(tail, ("dead_end_tail_retention", "dead_end"))
    if explicit is not None:
        return 1.0 if explicit >= 0.5 else 0.0
    has_repeat_loop = action_repeat_ratio >= 0.6
    return 1.0 if has_repeat_loop and mean_progress <= 0.25 else 0.0


def _feature_loop_closure_score(
    turns: list[dict[str, Any]],
    mean_progress: float,
    embedding_dim: int,
) -> float:
    explicit = _explicit_number_from_items(turns, ("loop_closure_score",))
    if explicit is not None:
        return _clip01(explicit)
    if len(turns) < 2:
        return 0.0
    state_embeddings = [
        _embed_text(_turn_state_text(turn), embedding_dim)
        for turn in turns
    ]
    last_state = state_embeddings[-1]
    similarities = [_cosine(last_state, previous) for previous in state_embeddings[:-1]]
    if not similarities:
        return 0.0
    stagnation = _clip01(1.0 - mean_progress)
    return _clip01(max(similarities) * stagnation)


def _feature_hypothesis_confidence(
    trajectory: Mapping[str, Any],
    turns: list[dict[str, Any]],
    query_text: str,
    clue_text: str,
    embedding_dim: int,
) -> tuple[float, bool]:
    explicit = _extract_number(trajectory, ("hypothesis_confidence", "q_hyp"))
    if explicit is None:
        explicit = _explicit_number_from_items(turns, ("hypothesis_confidence", "q_hyp"))
    if explicit is not None:
        return _clip01(explicit), False

    logits = _last_logits(turns, ("hypothesis_logits", "logits"))
    if logits is not None:
        return _clip01(_max_softmax_probability(logits)), False

    hypothesis_text = _join_text(
        trajectory.get("final_hypothesis"),
        trajectory.get("final_focus"),
        _last_value(turns, "hypothesis"),
        _last_value(turns, "focus"),
    )
    support_text = _join_text(query_text, clue_text)
    if hypothesis_text and support_text:
        confidence = _cosine(_embed_text(hypothesis_text, embedding_dim), _embed_text(support_text, embedding_dim))
        return _clip01(confidence), False
    return 0.5, True


def _feature_action_relevance(
    trajectory: Mapping[str, Any],
    turns: list[dict[str, Any]],
    target_text: str,
    embedding_dim: int,
) -> tuple[float, bool]:
    explicit = _extract_number(trajectory, ("action_relevance", "q_act"))
    if explicit is None:
        explicit = _explicit_number_from_items(turns, ("action_relevance", "q_act"))
    if explicit is not None:
        return _clip01(explicit), False

    logits = _last_logits(turns, ("action_logits",))
    if logits is not None:
        return _clip01(_max_softmax_probability(logits)), False

    action_text = _join_text(
        trajectory.get("action"),
        _last_value(turns, "action"),
        _last_value(turns, "tool"),
    )
    if action_text and target_text:
        relevance = _cosine(_embed_text(action_text, embedding_dim), _embed_text(target_text, embedding_dim))
        return _clip01(relevance), False
    return 0.5, True


def _feature_gap(hypothesis_confidence: float, action_relevance: float) -> float:
    return _clip01(0.5 + 0.5 * (hypothesis_confidence - action_relevance))


def _feature_counterfactual_gap(
    trajectory: Mapping[str, Any],
    turns: list[dict[str, Any]],
) -> tuple[float, bool]:
    explicit = _extract_number(trajectory, ("counterfactual_gain_gap",))
    if explicit is None:
        explicit = _explicit_number_from_items(turns, ("counterfactual_gain_gap",))
    if explicit is not None:
        return _clip01(explicit), False

    counterfactual_gain = _extract_number(trajectory, ("counterfactual_gain", "candidate_action_gain"))
    if counterfactual_gain is None:
        counterfactual_gain = _explicit_number_from_items(turns, ("counterfactual_gain", "candidate_action_gain"))
    actual_gain = _extract_number(trajectory, ("actual_gain", "action_gain"))
    if actual_gain is None:
        actual_gain = _explicit_number_from_items(turns, ("actual_gain", "action_gain"))

    if counterfactual_gain is None or actual_gain is None:
        return 0.5, True
    return _clip01(counterfactual_gain - actual_gain), False


def _compute_tau_values(
    turns: list[dict[str, Any]],
    target_embedding: np.ndarray,
    embedding_dim: int,
) -> list[float]:
    tau_values: list[float] = []
    for turn in turns:
        explicit = _extract_number(turn, ("tau", "tau_value"))
        if explicit is not None:
            tau_values.append(_clip01(explicit))
            continue
        state_text = _turn_state_text(turn)
        if not state_text:
            tau_values.append(0.5)
            continue
        tau_values.append(_clip01(_cosine(_embed_text(state_text, embedding_dim), target_embedding)))
    return tau_values


def _config_from_trajectory(trajectory: Mapping[str, Any]) -> FeatureConfig:
    config = trajectory.get("config", {})
    k_tail = trajectory.get("k_tail", config.get("k_tail", 5))
    return FeatureConfig(k_tail=int(k_tail))


def _get_turns(trajectory: Mapping[str, Any]) -> list[dict[str, Any]]:
    for key in ("turns", "trajectory", "history"):
        value = trajectory.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            turns = [dict(item) for item in value if isinstance(item, Mapping)]
            return turns
    return []


def _looks_like_trajectory(item: Mapping[str, Any]) -> bool:
    return any(key in item for key in ("turns", "trajectory", "history", "query", "task"))


def _extract_clue_text(turn: Mapping[str, Any]) -> str:
    return _join_text(turn.get("clue"), turn.get("observation"), turn.get("context"))


def _turn_state_text(turn: Mapping[str, Any]) -> str:
    return _join_text(
        turn.get("hypothesis"),
        turn.get("focus"),
        turn.get("action"),
        turn.get("tool"),
        turn.get("observation"),
        turn.get("context"),
        turn.get("reasoning"),
        turn.get("response"),
        turn.get("answer"),
        turn.get("clue"),
    )


def _normalize_action(turn: Mapping[str, Any]) -> str:
    action = _join_text(turn.get("action"), turn.get("tool"), turn.get("tool_call"))
    if not action:
        return ""
    return " ".join(_tokenize(action))


def _progress_values(turns: list[dict[str, Any]]) -> list[float]:
    values = []
    for turn in turns:
        explicit = _extract_number(turn, ("progress", "progress_score", "novelty"))
        if explicit is not None:
            values.append(_clip01(explicit))
            continue
        state_text = _turn_state_text(turn)
        values.append(_clip01(min(len(set(_tokenize(state_text))) / 12.0, 1.0)))
    return values


def _last_value(turns: list[dict[str, Any]], key: str) -> Any:
    for turn in reversed(turns):
        if key in turn:
            return turn.get(key)
    return None


def _last_logits(turns: list[dict[str, Any]], keys: Sequence[str]) -> Sequence[float] | None:
    for turn in reversed(turns):
        for key in keys:
            value = turn.get(key)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                return value
    return None


def _explicit_number_from_items(items: Sequence[Mapping[str, Any]], keys: Sequence[str]) -> float | None:
    for item in reversed(items):
        value = _extract_number(item, keys)
        if value is not None:
            return value
    return None


def _extract_number(mapping: Mapping[str, Any], keys: Sequence[str]) -> float | None:
    for key in keys:
        value = mapping.get(key)
        if value is None:
            continue
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        if isinstance(value, (int, float, np.floating, np.integer)):
            return float(value)
    return None


def _join_text(*parts: Any) -> str:
    chunks: list[str] = []
    for part in parts:
        if part is None:
            continue
        if isinstance(part, str):
            if part.strip():
                chunks.append(part.strip())
            continue
        if isinstance(part, Mapping):
            chunks.append(_join_text(*part.values()))
            continue
        if isinstance(part, Sequence) and not isinstance(part, (str, bytes)):
            chunks.append(_join_text(*part))
            continue
        chunks.append(str(part))
    return " ".join(chunk for chunk in chunks if chunk).strip()


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text or "")]


def _token_overlap_ratio(left: Sequence[str], right: Sequence[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set:
        return 0.0
    return len(left_set & right_set) / len(left_set)


def _embed_text(text: str, embedding_dim: int) -> np.ndarray:
    tokens = _tokenize(text)
    if not tokens:
        return np.zeros(embedding_dim, dtype=float)
    vector = np.zeros(embedding_dim, dtype=float)
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        slot = int.from_bytes(digest[:4], "big") % embedding_dim
        sign = -1.0 if (digest[4] % 2) else 1.0
        vector[slot] += sign
    norm = float(np.linalg.norm(vector))
    return vector if norm <= _EPSILON else vector / norm


def _cosine(left: np.ndarray, right: np.ndarray) -> float:
    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    if left_norm <= _EPSILON or right_norm <= _EPSILON:
        return 0.0
    return _clip01(float(np.dot(left, right) / (left_norm * right_norm)))


def _mean_diff(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    return float(np.mean(np.diff(np.asarray(values, dtype=float))))


def _mean_or_default(values: Sequence[float], default: float) -> float:
    if not values:
        return default
    return float(np.mean(np.asarray(values, dtype=float)))


def _max_softmax_probability(logits: Sequence[float]) -> float:
    array = np.asarray(logits, dtype=float)
    shifted = array - np.max(array)
    exp = np.exp(shifted)
    probs = exp / max(float(np.sum(exp)), _EPSILON)
    return float(np.max(probs))


def _clip01(value: float) -> float:
    if math.isnan(value):
        return 0.5
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)
