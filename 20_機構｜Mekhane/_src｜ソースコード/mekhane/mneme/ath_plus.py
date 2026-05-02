#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mneme/ath_plus.py A0→GEPA-informed /ath+ CLI
"""GEPA-informed retrospective CLI — load traces, score, diagnose, update Pareto frontier."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator

from .feedback_scorer import score_external, score_objective
from .pareto_frontier import update_frontier
from .reflective_diagnosis import diagnose
from .trace_point import FeedbackScore, TracePoint

OBJECTIVES = ("objective", "external")


def _default_data_dir() -> Path:
    env = os.environ.get("MNEME_TRACE_ROOT") or os.environ.get("MEKHANE_TRACE_ROOT")
    return Path(env) if env else Path.cwd() / "mneme_traces"


def _trace_path(data_dir: Path, session_id: str) -> Path:
    return data_dir / session_id / "trace_points.jsonl"


def _iter_trace_points(path: Path) -> Iterator[TracePoint]:
    if not path.is_file():
        raise FileNotFoundError(f"trace file not found: {path}")

    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield TracePoint.from_json(line)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                raise ValueError(f"invalid trace JSON at {path}:{lineno}") from e


def _load_frontier(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise TypeError(f"frontier file must contain a JSON array: {path}")
    return data


def _save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GEPA-informed /ath+ retrospective over session traces.")
    parser.add_argument("--session-id", required=True, help="Session directory name under data-dir.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Root directory holding <session-id>/trace_points.jsonl "
        "(default: $MNEME_TRACE_ROOT or ./mneme_traces).",
    )
    parser.add_argument(
        "--trace-file",
        type=Path,
        default=None,
        help="Override path to trace_points.jsonl (skips data-dir layout).",
    )
    parser.add_argument(
        "--skip-external",
        action="store_true",
        help="Skip Gemini external scoring; use objective-only vector (external=0).",
    )
    parser.add_argument("--gemini-timeout", type=int, default=300, help="Per-call Gemini timeout (seconds).")
    parser.add_argument(
        "--diagnosis-timeout",
        type=int,
        default=600,
        help="Timeout (seconds) for the aggregate diagnosis call.",
    )
    args = parser.parse_args(argv)

    data_dir = args.data_dir or _default_data_dir()
    trace_path = args.trace_file if args.trace_file else _trace_path(data_dir, args.session_id)
    session_dir = trace_path.parent

    try:
        traces = list(_iter_trace_points(trace_path))
    except (OSError, ValueError) as e:
        print(f"[ath+] {e}", file=sys.stderr)
        return 2

    decision_like = {"DECISION", "CORRECTION"}
    scored_traces = [t for t in traces if t.type in decision_like]

    feedback_scores: list[FeedbackScore] = []
    pareto_candidates: list[dict[str, Any]] = []

    for tp in scored_traces:
        oid = tp.id
        obj = float(score_objective(tp))
        if args.skip_external:
            ext = 0.0
            fb = FeedbackScore(decision_id=oid, score=ext, feedback_text="external scoring skipped")
        else:
            try:
                fb = score_external(oid, tp, timeout=args.gemini_timeout)
                ext = float(fb.score)
            except (OSError, RuntimeError, ValueError, FileNotFoundError) as e:
                print(f"[ath+] external score failed for {oid}: {e}", file=sys.stderr)
                ext = 0.0
                fb = FeedbackScore(
                    decision_id=oid,
                    score=ext,
                    feedback_text=f"[external scoring failed] {e}",
                )

        feedback_scores.append(fb)
        pareto_candidates.append(
            {
                "id": oid,
                "type": tp.type,
                "scores": {"objective": obj, "external": ext},
            }
        )

    frontier_path = session_dir / "pareto_frontier.json"
    frontier = _load_frontier(frontier_path)
    for cand in pareto_candidates:
        frontier = update_frontier(frontier, cand, OBJECTIVES)
    _save_json(frontier_path, frontier)

    scores_path = session_dir / "feedback_scores.jsonl"
    scores_path.parent.mkdir(parents=True, exist_ok=True)
    with scores_path.open("w", encoding="utf-8") as fh:
        for fs in feedback_scores:
            fh.write(json.dumps(asdict(fs), ensure_ascii=False) + "\n")

    diagnosis: dict[str, Any]
    if not scored_traces:
        diagnosis = {
            "summary": "No DECISION/CORRECTION traces to score; skipped Gemini diagnosis.",
            "root_causes": [],
            "counterfactuals": [],
            "lessons": [],
            "risks": [],
            "if_then_rules": [],
        }
    else:
        try:
            diagnosis = diagnose(scored_traces, feedback_scores, timeout=args.diagnosis_timeout)
        except (OSError, RuntimeError, ValueError, FileNotFoundError) as e:
            print(f"[ath+] diagnosis failed: {e}", file=sys.stderr)
            diagnosis = {
                "summary": f"diagnosis failed: {e}",
                "root_causes": [],
                "counterfactuals": [],
                "lessons": [],
                "risks": [],
                "if_then_rules": [],
            }

    _save_json(session_dir / "diagnosis.json", diagnosis)

    print(json.dumps({"session_dir": str(session_dir), "n_traces": len(traces), "n_scored": len(scored_traces)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
