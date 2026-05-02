from __future__ import annotations
# PROOF: [L2/Ergon関手] <- mekhane/fep/ergon/functors.py
"""
PROOF: [L2/Ergon関手] このファイルは存在しなければならない

A0 → L⊣R 随伴対の操作的ロジックが必要
   → source_label 決定規則 (§6) と忘却率計算
   → 三角恒等式の型レベル検証ユーティリティ

Design: 09_能動｜Ergon/02_設計｜Design/05_r_functor_schema.md §6
        09_能動｜Ergon/02_設計｜Design/06_boundary_contracts.md

Q.E.D.
"""


from .types import (
    SafetyClass,
    SourceLabel,
    Confidence,
    Task,
    ExecutionResult,
    ErgonBeliefUpdate,
)


# PURPOSE: [L2-design] R 関手の source_label 決定規則 (§6)
def source_label_rule(task: Task, result: ExecutionResult) -> tuple[SourceLabel, Confidence]:
    """Determine source_label and confidence for a BeliefUpdate.

    Rules (from 05_r_functor_schema.md §6):
      1. deterministic + success → SOURCE / 確信
      2. verification PASS → SOURCE / 確信
      3. read_only → TAINT / 推定
      4. default → TAINT / 推定

    The confidence is always proportional to source_label (N-3 × N-10).
    """
    # Rule 1: Deterministic success = highest precision
    if task.deterministic and result.exit_status == "success":
        return SourceLabel.SOURCE, Confidence.CERTAIN

    # Rule 2: Verified result = SOURCE promotion
    if result.verification and result.verification.get("verdict") == "PASS":
        return SourceLabel.SOURCE, Confidence.CERTAIN

    # Rule 3-4: LLM output is TAINT
    return SourceLabel.TAINT, Confidence.ESTIMATED


# PURPOSE: [L2-design] 忘却率の計算
def forgetting_rate(result: ExecutionResult, belief: ErgonBeliefUpdate) -> float:
    """Calculate the R functor's forgetting rate.

    Forgetting Rate = 1 - |BeliefUpdate| / |ExecutionResult|

    Approximation: uses string length as a proxy for information content.
    In practice, a more sophisticated measure (e.g., semantic similarity)
    would be appropriate.

    Returns:
        float in [0, 1]. Higher = more information forgotten.
        0.0 = no forgetting (raw output preserved)
        1.0 = complete forgetting (empty belief)
    """
    result_size = _info_size(result.raw_output)
    belief_size = len(belief.summary) + len(belief.prediction_error or "") + len(belief.next_action or "")

    if result_size == 0:
        return 0.0

    rate = 1.0 - (belief_size / result_size)
    return max(0.0, min(1.0, rate))


# PURPOSE: [L2-design] prediction error の生成
def compute_prediction_error(task: Task, result: ExecutionResult) -> str | None:
    """Compute prediction error between Plan/Task expectations and actual result.

    Returns None if no prediction error (expectations met).
    Returns a description string if expectations differ from reality.
    """
    errors = []

    # Side effect mismatch
    expected = set(task.expected_side_effects)
    actual = set(result.actual_side_effects)

    unexpected = actual - expected
    missing = expected - actual

    if unexpected:
        errors.append(f"Unexpected side effects: {', '.join(sorted(unexpected))}")
    if missing:
        errors.append(f"Expected but missing: {', '.join(sorted(missing))}")

    # Exit status mismatch
    if result.exit_status != "success":
        errors.append(f"Exit status: {result.exit_status}")

    return "; ".join(errors) if errors else None


# PURPOSE: [L2-design] 三角恒等式の型レベル検証
def triangle_identity_check(task: Task, re_task: Task) -> bool:
    """Check triangle identity 1 at type level.

    εL ∘ Lη = id_L

    Operationally: Plan → Task → Execute → Distill → Re-Plan → Re-Task
    should produce the same tool_name and safety_class.

    The parameters may differ (LLM's probabilistic variation is tolerated),
    but tool_name and safety_class must be invariant.
    """
    return (
        task.tool_name == re_task.tool_name
        and task.safety_class == re_task.safety_class
    )


# ━━━ Internal helpers ━━━


def _info_size(raw: str | dict) -> int:
    """Approximate information size of raw output."""
    if isinstance(raw, dict):
        import json
        return len(json.dumps(raw, ensure_ascii=False))
    return len(str(raw))
