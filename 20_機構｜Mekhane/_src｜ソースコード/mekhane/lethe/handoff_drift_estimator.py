# PROOF: [L2/インフラ] <- lethe/handoff_drift_estimator.py Brief 1 Task 2 — slot-front χ 推定
"""Estimate handoff drift on boot⊣bye logs without external model APIs."""

from __future__ import annotations

from collections.abc import Sequence
import argparse
import csv
import json
from pathlib import Path
import re
from typing import Any

import numpy as np

try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover - optional dependency
    plt = None

__all__ = [
    "estimate_drift",
    "export_drift_artifacts",
    "judge_similarity",
    "load_handoff_pairs",
]

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")
_EPSILON = 1e-9


def load_handoff_pairs(source: str | Path | Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Load handoff pairs from JSONL, JSON, or an in-memory list of dicts."""

    if isinstance(source, Sequence) and not isinstance(source, (str, bytes, Path)):
        if not all(isinstance(item, dict) for item in source):
            raise TypeError("handoff_pairs must be a sequence of dict objects")
        return [dict(item) for item in source]

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix == ".jsonl":
        pairs: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            pairs.append(json.loads(stripped))
        return pairs

    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        if not all(isinstance(item, dict) for item in payload):
            raise TypeError("JSON payload must be a list of dict objects")
        return payload
    if isinstance(payload, dict):
        pairs = payload.get("handoff_pairs")
        if isinstance(pairs, list) and all(isinstance(item, dict) for item in pairs):
            return pairs
    raise TypeError("Unsupported handoff pair source")


def judge_similarity(reference: str, observed: str) -> float:
    """Simple placeholder judge using token-overlap cosine similarity."""

    left = _tokenize(reference)
    right = _tokenize(observed)
    if not left or not right:
        ref = reference.strip().lower()
        obs = observed.strip().lower()
        if ref and obs and (ref in obs or obs in ref):
            return 1.0
        return 0.0

    vocab = sorted(set(left) | set(right))
    left_counts = np.array([left.count(token) for token in vocab], dtype=float)
    right_counts = np.array([right.count(token) for token in vocab], dtype=float)
    denom = float(np.linalg.norm(left_counts) * np.linalg.norm(right_counts))
    cosine = 0.0 if denom <= _EPSILON else float(np.dot(left_counts, right_counts) / denom)
    overlap = len(set(left) & set(right)) / max(len(set(left) | set(right)), 1)
    ref = reference.lower()
    obs = observed.lower()
    if ref in obs or obs in ref:
        overlap = max(overlap, 0.75)
    return float(np.clip(0.5 * cosine + 0.5 * overlap, 0.0, 1.0))


def estimate_drift(
    handoff_pairs: list[dict],
    mode: str = "slot",
    p: float = 0.5,
    kappa_c: float = 0.5,
    epsilon: float = 0.2,
) -> dict:
    """Estimate χ from handoff pairs using slot-front primary and coverage fallback."""

    if not handoff_pairs:
        return {
            "mode_requested": mode,
            "pair_results": [],
            "summary": {
                "pair_count": 0,
                "mean_chi_characteristic": 0.0,
                "std_chi_characteristic": 0.0,
                "chi_characteristic_quantiles": {"p50": 0.0, "p90": 0.0},
                "max_turn_chi": 0.0,
                "mode_usage": {"slot": 0, "coverage": 0},
                "regime": "no-data",
            },
            "turn_rows": [],
        }

    if mode not in {"slot", "coverage", "auto"}:
        raise ValueError("mode must be one of: slot, coverage, auto")

    pair_results: list[dict[str, Any]] = []
    turn_rows: list[dict[str, Any]] = []
    chi_characteristics: list[float] = []
    chi_turns: list[float] = []
    mode_usage = {"slot": 0, "coverage": 0}

    for index, raw_pair in enumerate(handoff_pairs):
        pair = _normalize_pair(raw_pair, index)
        support_scores, margin_scores = _resolve_score_matrices(pair)
        pair_result = _estimate_pair(
            pair=pair,
            support_scores=support_scores,
            margin_scores=margin_scores,
            requested_mode=mode,
            p=p,
            kappa_c=kappa_c,
            epsilon=epsilon,
        )
        pair_results.append(pair_result)
        mode_usage[pair_result["mode_used"]] += 1
        chi_characteristics.append(float(pair_result["chi_characteristic"]))
        chi_turns.extend(pair_result["chi_turn"])
        turn_rows.extend(pair_result["turn_rows"])

    characteristic_array = np.array(chi_characteristics, dtype=float)
    turn_array = np.array(chi_turns, dtype=float)
    mean_characteristic = float(np.mean(characteristic_array)) if characteristic_array.size else 0.0
    summary = {
        "pair_count": len(pair_results),
        "mean_chi_characteristic": mean_characteristic,
        "std_chi_characteristic": float(np.std(characteristic_array)) if characteristic_array.size else 0.0,
        "chi_characteristic_quantiles": {
            "p50": _quantile_or_zero(characteristic_array, 0.5),
            "p90": _quantile_or_zero(characteristic_array, 0.9),
        },
        "max_turn_chi": float(np.max(turn_array)) if turn_array.size else 0.0,
        "mode_usage": mode_usage,
        "pairs_with_chi_above_one": sum(item["chi_characteristic"] > 1.0 for item in pair_results),
        "regime": "drift-dominant" if mean_characteristic > 1.0 else "carrier-recovery",
    }
    return {
        "mode_requested": mode,
        "parameters": {"p": p, "kappa_c": kappa_c, "epsilon": epsilon},
        "pair_results": pair_results,
        "summary": summary,
        "turn_rows": turn_rows,
    }


def export_drift_artifacts(result: dict, output_dir: str | Path) -> dict[str, str | None]:
    """Write CSV, JSON, and PNG artifacts for a drift estimate result."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    csv_path = output_path / "handoff_drift_results.csv"
    json_path = output_path / "handoff_drift_summary.json"
    png_path = output_path / "chi_distribution.png"

    rows = result.get("turn_rows", [])
    csv_columns = [
        "pair_id",
        "turn_index",
        "mode_used",
        "carrier_front",
        "null_front",
        "coverage",
        "mass",
        "v_carrier",
        "v_null",
        "chi",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column) for column in csv_columns})

    json_payload = {
        "mode_requested": result.get("mode_requested"),
        "parameters": result.get("parameters", {}),
        "summary": result.get("summary", {}),
        "pair_results": [
            {
                key: value
                for key, value in pair_result.items()
                if key != "turn_rows"
            }
            for pair_result in result.get("pair_results", [])
        ],
    }
    json_path.write_text(json.dumps(json_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    written_png: str | None = None
    if plt is not None:
        distribution = [
            float(pair_result["chi_characteristic"])
            for pair_result in result.get("pair_results", [])
        ]
        if len(distribution) < 2:
            distribution = [float(row["chi"]) for row in rows]
        if distribution:
            fig, axis = plt.subplots(figsize=(6, 4))
            axis.hist(distribution, bins=min(20, max(len(distribution), 5)), color="#355C7D", alpha=0.85)
            axis.set_title("Handoff Drift χ Distribution")
            axis.set_xlabel("χ")
            axis.set_ylabel("count")
            axis.axvline(1.0, color="#C06C84", linestyle="--", linewidth=1.5)
            fig.tight_layout()
            fig.savefig(png_path)
            plt.close(fig)
            written_png = str(png_path)

    return {
        "csv": str(csv_path),
        "json": str(json_path),
        "png": written_png,
    }


def _estimate_pair(
    pair: dict[str, Any],
    support_scores: np.ndarray,
    margin_scores: np.ndarray,
    requested_mode: str,
    p: float,
    kappa_c: float,
    epsilon: float,
) -> dict[str, Any]:
    carrier_fronts = _carrier_fronts(support_scores, kappa_c)
    null_fronts = _null_fronts(margin_scores, epsilon)
    coverage = np.mean(support_scores >= kappa_c, axis=1)
    mass = np.mean(margin_scores <= epsilon, axis=1)

    mode_used = _select_mode(
        requested_mode=requested_mode,
        carrier_fronts=carrier_fronts,
        null_fronts=null_fronts,
        pair=pair,
    )

    if mode_used == "slot":
        carrier_velocity = _front_velocity(carrier_fronts)
        null_velocity = _front_velocity(null_fronts)
    else:
        carrier_velocity = _positive_velocity(coverage)
        null_velocity = _positive_velocity(mass)

    chi_turn = _chi_series(null_velocity, carrier_velocity)
    characteristic_v_carrier = _quantile_or_zero(carrier_velocity[1:], p)
    characteristic_v_null = _quantile_or_zero(null_velocity[1:], p)
    chi_characteristic = float(characteristic_v_null / max(characteristic_v_carrier, _EPSILON))
    first_above_one = next((idx for idx, value in enumerate(chi_turn, start=1) if value > 1.0), None)

    turn_rows = []
    for turn_index in range(len(pair["post_turn_texts"])):
        turn_rows.append(
            {
                "pair_id": pair["pair_id"],
                "turn_index": turn_index + 1,
                "mode_used": mode_used,
                "carrier_front": _maybe_number(carrier_fronts[turn_index]),
                "null_front": _maybe_number(null_fronts[turn_index]),
                "coverage": float(coverage[turn_index]),
                "mass": float(mass[turn_index]),
                "v_carrier": float(carrier_velocity[turn_index]),
                "v_null": float(null_velocity[turn_index]),
                "chi": float(chi_turn[turn_index]),
            }
        )

    return {
        "pair_id": pair["pair_id"],
        "mode_used": mode_used,
        "unit_count": len(pair["atomic_units"]),
        "turn_count": len(pair["post_turn_texts"]),
        "atomic_units": pair["atomic_units"],
        "carrier_front": [_maybe_number(item) for item in carrier_fronts],
        "null_front": [_maybe_number(item) for item in null_fronts],
        "coverage": [float(item) for item in coverage],
        "mass": [float(item) for item in mass],
        "v_carrier": [float(item) for item in carrier_velocity],
        "v_null": [float(item) for item in null_velocity],
        "chi_turn": [float(item) for item in chi_turn],
        "chi_characteristic": chi_characteristic,
        "median_chi_turn": _quantile_or_zero(np.array(chi_turn[1:], dtype=float), 0.5),
        "max_chi_turn": float(np.max(chi_turn[1:])) if len(chi_turn) > 1 else float(np.max(chi_turn)),
        "first_chi_above_one_turn": first_above_one,
        "characteristic_v_carrier": characteristic_v_carrier,
        "characteristic_v_null": characteristic_v_null,
        "turn_rows": turn_rows,
    }


def _normalize_pair(raw_pair: dict[str, Any], index: int) -> dict[str, Any]:
    pre_turns = raw_pair.get("pre_handoff_turns") or raw_pair.get("pre_turns") or raw_pair.get("pre") or []
    post_turns = raw_pair.get("post_handoff_turns") or raw_pair.get("post_turns") or raw_pair.get("post") or []
    if not isinstance(pre_turns, Sequence) or isinstance(pre_turns, (str, bytes)):
        raise TypeError("pre_handoff_turns must be a sequence")
    if not isinstance(post_turns, Sequence) or isinstance(post_turns, (str, bytes)):
        raise TypeError("post_handoff_turns must be a sequence")

    pre_turn_texts = [_coerce_turn_text(turn) for turn in pre_turns]
    post_turn_texts = [_coerce_turn_text(turn) for turn in post_turns]
    atomic_units = raw_pair.get("atomic_units") or _extract_atomic_units(pre_turn_texts)
    if not atomic_units:
        atomic_units = ["empty handoff"]

    return {
        "pair_id": str(raw_pair.get("pair_id") or raw_pair.get("id") or f"handoff-{index:03d}"),
        "pre_turn_texts": pre_turn_texts,
        "post_turn_texts": post_turn_texts,
        "atomic_units": [str(unit) for unit in atomic_units],
        "distractors": raw_pair.get("distractors"),
        "support_scores": raw_pair.get("support_scores"),
        "margin_scores": raw_pair.get("margin_scores"),
        "force_fallback": bool(raw_pair.get("force_fallback", False)),
    }


def _resolve_score_matrices(pair: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    unit_count = len(pair["atomic_units"])
    turn_count = len(pair["post_turn_texts"])
    support_scores = pair.get("support_scores")
    margin_scores = pair.get("margin_scores")

    if support_scores is None:
        support_matrix = _support_matrix(pair["atomic_units"], pair["post_turn_texts"])
    else:
        support_matrix = _coerce_matrix(support_scores, turn_count, unit_count, "support_scores")

    if margin_scores is None:
        distractors = _resolve_distractors(pair["atomic_units"], pair.get("distractors"))
        margin_matrix = _margin_matrix(
            pair["atomic_units"],
            distractors,
            pair["post_turn_texts"],
            support_matrix,
        )
    else:
        margin_matrix = _coerce_matrix(margin_scores, turn_count, unit_count, "margin_scores")

    return support_matrix, margin_matrix


def _support_matrix(atomic_units: Sequence[str], post_turn_texts: Sequence[str]) -> np.ndarray:
    matrix = np.zeros((len(post_turn_texts), len(atomic_units)), dtype=float)
    for turn_index, turn_text in enumerate(post_turn_texts):
        for unit_index, atomic_unit in enumerate(atomic_units):
            matrix[turn_index, unit_index] = judge_similarity(atomic_unit, turn_text)
    return matrix


def _margin_matrix(
    atomic_units: Sequence[str],
    distractors: Sequence[list[str]],
    post_turn_texts: Sequence[str],
    support_matrix: np.ndarray,
) -> np.ndarray:
    matrix = np.zeros_like(support_matrix, dtype=float)
    for turn_index, turn_text in enumerate(post_turn_texts):
        for unit_index, atomic_unit in enumerate(atomic_units):
            positive = float(support_matrix[turn_index, unit_index])
            negative = max((judge_similarity(distractor, turn_text) for distractor in distractors[unit_index]), default=0.0)
            matrix[turn_index, unit_index] = float(np.clip(positive - negative, -1.0, 1.0))
    return matrix


def _resolve_distractors(atomic_units: Sequence[str], raw_distractors: Any) -> list[list[str]]:
    if isinstance(raw_distractors, dict):
        resolved = []
        for index, atomic_unit in enumerate(atomic_units):
            entry = raw_distractors.get(atomic_unit)
            if entry is None:
                entry = raw_distractors.get(str(index))
            resolved.append(_coerce_distractor_list(entry, atomic_units, index))
        return resolved

    if isinstance(raw_distractors, Sequence) and not isinstance(raw_distractors, (str, bytes)):
        if len(raw_distractors) == len(atomic_units):
            return [
                _coerce_distractor_list(entry, atomic_units, index)
                for index, entry in enumerate(raw_distractors)
            ]

    return [_default_distractors(atomic_units, index) for index in range(len(atomic_units))]


def _coerce_distractor_list(entry: Any, atomic_units: Sequence[str], index: int) -> list[str]:
    if entry is None:
        return _default_distractors(atomic_units, index)
    if isinstance(entry, str):
        return [entry]
    if isinstance(entry, Sequence) and not isinstance(entry, (str, bytes)):
        values = [str(item) for item in entry if str(item).strip()]
        return values or _default_distractors(atomic_units, index)
    return _default_distractors(atomic_units, index)


def _default_distractors(atomic_units: Sequence[str], index: int) -> list[str]:
    if len(atomic_units) == 1:
        return [f"{atomic_units[0]} absent"]
    neighbor = atomic_units[(index + 1) % len(atomic_units)]
    return [neighbor]


def _coerce_matrix(raw_matrix: Any, turns: int, units: int, name: str) -> np.ndarray:
    matrix = np.asarray(raw_matrix, dtype=float)
    if matrix.shape != (turns, units):
        raise ValueError(f"{name} must have shape {(turns, units)}, got {matrix.shape}")
    return matrix


def _carrier_fronts(support_scores: np.ndarray, kappa_c: float) -> np.ndarray:
    fronts = np.full(support_scores.shape[0], np.nan, dtype=float)
    for turn_index in range(support_scores.shape[0]):
        indices = np.flatnonzero(support_scores[turn_index] >= kappa_c)
        if indices.size:
            fronts[turn_index] = float(indices[-1])
    return fronts


def _null_fronts(margin_scores: np.ndarray, epsilon: float) -> np.ndarray:
    fronts = np.full(margin_scores.shape[0], np.nan, dtype=float)
    for turn_index in range(margin_scores.shape[0]):
        indices = np.flatnonzero(margin_scores[turn_index] <= epsilon)
        if indices.size:
            fronts[turn_index] = float(indices[-1])
    return fronts


def _front_velocity(fronts: np.ndarray) -> np.ndarray:
    velocities = np.zeros(fronts.shape[0], dtype=float)
    for index in range(1, fronts.shape[0]):
        previous = fronts[index - 1]
        current = fronts[index]
        if np.isfinite(previous) and np.isfinite(current):
            velocities[index] = abs(float(current - previous))
    return velocities


def _positive_velocity(series: np.ndarray) -> np.ndarray:
    velocities = np.zeros(series.shape[0], dtype=float)
    for index in range(1, series.shape[0]):
        velocities[index] = max(float(series[index] - series[index - 1]), 0.0)
    return velocities


def _chi_series(null_velocity: np.ndarray, carrier_velocity: np.ndarray) -> np.ndarray:
    denominator = np.maximum(carrier_velocity, _EPSILON)
    return np.divide(null_velocity, denominator)


def _select_mode(
    requested_mode: str,
    carrier_fronts: np.ndarray,
    null_fronts: np.ndarray,
    pair: dict[str, Any],
) -> str:
    if requested_mode == "coverage":
        return "coverage"
    if pair.get("force_fallback"):
        return "coverage"
    if requested_mode == "slot" and _slot_alignment_reliable(carrier_fronts, null_fronts):
        return "slot"
    if requested_mode == "auto" and _slot_alignment_reliable(carrier_fronts, null_fronts):
        return "slot"
    return "coverage"


def _slot_alignment_reliable(carrier_fronts: np.ndarray, null_fronts: np.ndarray) -> bool:
    carrier_steps = np.diff(np.where(np.isfinite(carrier_fronts), carrier_fronts, np.nan))
    null_steps = np.diff(np.where(np.isfinite(null_fronts), null_fronts, np.nan))
    finite_carrier = carrier_steps[np.isfinite(carrier_steps)]
    finite_null = null_steps[np.isfinite(null_steps)]
    if finite_carrier.size < 2 or finite_null.size < 2:
        return False
    return bool(np.any(np.abs(finite_carrier) > 0.0) and np.any(np.abs(finite_null) > 0.0))


def _extract_atomic_units(pre_turn_texts: Sequence[str]) -> list[str]:
    joined = " ".join(text.strip() for text in pre_turn_texts if text.strip())
    if not joined:
        return []
    sentences = [piece.strip() for piece in _SENTENCE_RE.split(joined) if piece.strip()]
    deduped: list[str] = []
    seen: set[str] = set()
    for sentence in sentences:
        if sentence not in seen:
            seen.add(sentence)
            deduped.append(sentence)
    return deduped


def _coerce_turn_text(turn: Any) -> str:
    if isinstance(turn, str):
        return turn
    if isinstance(turn, dict):
        if "text" in turn and isinstance(turn["text"], str):
            return turn["text"]
        if "content" in turn:
            return _coerce_content(turn["content"])
        pieces = []
        for key in ("assistant", "response", "message", "retrieval", "memory", "summary"):
            if key in turn:
                piece = _coerce_content(turn[key])
                if piece:
                    pieces.append(piece)
        if pieces:
            return " ".join(pieces)
        return json.dumps(turn, ensure_ascii=False, sort_keys=True)
    if isinstance(turn, Sequence) and not isinstance(turn, (bytes, bytearray)):
        return " ".join(_coerce_turn_text(item) for item in turn)
    return str(turn)


def _coerce_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        if "text" in content and isinstance(content["text"], str):
            return content["text"]
        return " ".join(_coerce_content(value) for value in content.values())
    if isinstance(content, Sequence) and not isinstance(content, (str, bytes, bytearray)):
        return " ".join(_coerce_content(item) for item in content)
    return str(content)


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _quantile_or_zero(values: np.ndarray, q: float) -> float:
    if values.size == 0:
        return 0.0
    return float(np.quantile(values, q))


def _maybe_number(value: float) -> float | None:
    if np.isfinite(value):
        return float(value)
    return None


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Estimate handoff drift from JSONL pairs.")
    parser.add_argument("source", help="Path to JSON or JSONL handoff pair input")
    parser.add_argument("--output-dir", default=".", help="Directory for CSV/JSON/PNG outputs")
    parser.add_argument("--mode", default="slot", choices=["slot", "coverage", "auto"])
    parser.add_argument("--p", type=float, default=0.5)
    parser.add_argument("--kappa-c", type=float, default=0.5)
    parser.add_argument("--epsilon", type=float, default=0.2)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_argument_parser()
    args = parser.parse_args(argv)
    pairs = load_handoff_pairs(args.source)
    result = estimate_drift(
        pairs,
        mode=args.mode,
        p=args.p,
        kappa_c=args.kappa_c,
        epsilon=args.epsilon,
    )
    artifacts = export_drift_artifacts(result, args.output_dir)
    payload = {
        "artifacts": artifacts,
        "summary": result["summary"],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
