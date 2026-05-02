from __future__ import annotations
# PROOF: [L2/Ergonプロトコル] <- mekhane/fep/ergon/protocols.py
"""
PROOF: [L2/Ergonプロトコル] このファイルは存在しなければならない

A0 → FEP の Markov blanket には2つの信念更新チャネルがある
     s→μ (Periskopē/phi7: 検索品質)
     a→μ (Ergon: ツール実行結果)
   → 共通プロトコルが両チャネルの統一的扱いを可能にする
   → protocols.py が共通インターフェースを定義

Design: 09_能動｜Ergon/02_設計｜Design/05_r_functor_schema.md §3.1

Q.E.D.
"""


from typing import Protocol, runtime_checkable


# PURPOSE: [L2-design] s→μ と a→μ の共通信念更新プロトコル
@runtime_checkable
class BeliefChannelProtocol(Protocol):
    """Common protocol for belief update channels in the Markov blanket.

    Two channels feed into Internal States (μ):
      - s→μ: Sensory channel (Periskopē phi7 — search quality)
      - a→μ: Active channel (Ergon — execution results)

    Both channels share:
      1. A measure of prediction error (residual between expected and actual)
      2. A loop/iterate decision (whether more cycles are needed)
      3. A confidence direction (improving, stable, declining)

    This protocol captures the minimal common interface.
    Implementors are NOT required to inherit — structural subtyping (duck typing) suffices.
    """

    @property
    def prediction_residual(self) -> float:
        """Prediction error magnitude.

        s→μ: 1 - overall_quality_score (phi7.residual_error)
        a→μ: presence/severity of prediction_error (Ergon)
        """
        ...

    @property
    def should_iterate(self) -> bool:
        """Whether the μ should request another cycle.

        s→μ: residual > threshold AND iteration < max (phi7.should_loop)
        a→μ: prediction_error is not None (Ergon — anomaly detected)
        """
        ...

    @property
    def confidence_direction(self) -> str:
        """Trend of confidence across iterations.

        Values: 'improving' | 'stable' | 'declining'

        s→μ: phi7.confidence_trend
        a→μ: derived from belief_delta (new/confirmed → improving, refuted → declining)
        """
        ...


# PURPOSE: [L2-design] ErgonBeliefUpdate に Protocol 準拠プロパティを追加するミックスイン
class ErgonBeliefChannelMixin:
    """Mixin to make ErgonBeliefUpdate conform to BeliefChannelProtocol.

    Usage:
        Instead of modifying ErgonBeliefUpdate directly (which would create
        a circular import), this mixin can be composed at runtime.

        Or, more practically: use the adapter functions below.
    """
    pass


# PURPOSE: [L2-design] ErgonBeliefUpdate → BeliefChannelProtocol アダプタ
def ergon_to_channel(belief_update) -> dict:
    """Adapt an ErgonBeliefUpdate to BeliefChannelProtocol-compatible dict.

    Args:
        belief_update: An ErgonBeliefUpdate instance.

    Returns:
        Dict with prediction_residual, should_iterate, confidence_direction.
    """
    # prediction_residual: binary (0.0 or 1.0) based on prediction_error presence
    has_error = belief_update.prediction_error is not None
    residual = 1.0 if has_error else 0.0

    # should_iterate: anomaly detected → needs investigation
    should_iterate = has_error

    # confidence_direction: derived from belief_delta
    delta_map = {
        "new": "improving",
        "confirmed": "stable",
        "updated": "improving",
        "refuted": "declining",
    }
    direction = delta_map.get(belief_update.belief_delta, "stable")

    return {
        "prediction_residual": residual,
        "should_iterate": should_iterate,
        "confidence_direction": direction,
    }


# PURPOSE: [L2-design] phi7.BeliefUpdate → BeliefChannelProtocol アダプタ
def phi7_to_channel(phi7_update) -> dict:
    """Adapt a phi7.BeliefUpdate to BeliefChannelProtocol-compatible dict.

    Args:
        phi7_update: A phi7_belief_update.BeliefUpdate instance.

    Returns:
        Dict with prediction_residual, should_iterate, confidence_direction.
    """
    return {
        "prediction_residual": phi7_update.residual_error,
        "should_iterate": phi7_update.should_loop,
        "confidence_direction": phi7_update.confidence_trend,
    }


# PURPOSE: [L2-design] 両チャネルの統合比較
def compare_channels(
    ergon_channel: dict,
    phi7_channel: dict,
) -> dict:
    """Compare two belief channels to detect cross-channel patterns.

    When both sensory AND active channels report high residual,
    the system may be in a fundamentally uncertain state (aleatoric).
    When only one reports high residual, the uncertainty is epistemic
    and can be resolved by the corresponding channel's iteration.

    Returns:
        Dict with combined assessment.
    """
    both_high = (
        ergon_channel["prediction_residual"] > 0.5
        and phi7_channel["prediction_residual"] > 0.5
    )

    return {
        "ergon_residual": ergon_channel["prediction_residual"],
        "phi7_residual": phi7_channel["prediction_residual"],
        "either_iterating": (
            ergon_channel["should_iterate"]
            or phi7_channel["should_iterate"]
        ),
        "uncertainty_type": "aleatoric" if both_high else "epistemic",
        "recommended_action": (
            "accept_uncertainty"
            if both_high
            else "iterate"
            if ergon_channel["should_iterate"] or phi7_channel["should_iterate"]
            else "commit"
        ),
    }
