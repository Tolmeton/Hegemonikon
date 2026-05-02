# PROOF: [L2/インフラ] <- mekhane/mneme/pareto_frontier.py A0→GEPA Pareto frontier 管理
from __future__ import annotations

from typing import Any, Mapping, MutableSequence, Sequence


def dominates(
    a: Mapping[str, float],
    b: Mapping[str, float],
    objectives: Sequence[str] | None = None,
    *,
    maximize: bool = True,
    eps: float = 1e-9,
) -> bool:
    """Return True iff ``a`` Pareto-dominates ``b`` on the given objectives.

    *maximize* True: higher is better. *maximize* False: lower is better (minimization).
    A missing objective value in either vector makes the pair incomparable → False.
    Strict improvement on at least one axis is required (ties on all axes → False).
    """
    keys = list(objectives) if objectives is not None else sorted(set(a) | set(b))
    if not keys:
        return False

    strictly_better = False
    for k in keys:
        if k not in a or k not in b:
            return False
        va, vb = float(a[k]), float(b[k])
        if maximize:
            if va + eps < vb:
                return False
            if va > vb + eps:
                strictly_better = True
        else:
            if va > vb + eps:
                return False
            if va + eps < vb:
                strictly_better = True
    return strictly_better


def update_frontier(
    frontier: MutableSequence[dict[str, Any]],
    candidate: dict[str, Any],
    objectives: Sequence[str] | None = None,
    *,
    score_key: str = "scores",
) -> list[dict[str, Any]]:
    """Insert *candidate* into *frontier* and drop any Pareto-dominated entries.

    Each item must be a mapping containing *score_key* → ``dict[str, float]`` of objective
    values. Other keys (``id``, ``decision_id``, …) are preserved verbatim.
    """
    pool: list[dict[str, Any]] = [*list(frontier), candidate]
    survivors: list[dict[str, Any]] = []

    for i, point in enumerate(pool):
        scores = point.get(score_key)
        if not isinstance(scores, Mapping):
            raise TypeError(f"each frontier item must have mapping[{score_key!r}]")

        dominated = False
        for j, other in enumerate(pool):
            if i == j:
                continue
            other_scores = other.get(score_key)
            if not isinstance(other_scores, Mapping):
                raise TypeError(f"each frontier item must have mapping[{score_key!r}]")
            if dominates(other_scores, scores, objectives):
                dominated = True
                break
        if not dominated:
            survivors.append(point)

    return survivors
