# PROOF: mekhane/tests/test_anchor.py
# PURPOSE: ObservationAnchor Wave 0.5 A5/A6 acceptance tests
"""Tests for mekhane.organon.anchor — ObservationAnchor and observe_anchor."""

import dataclasses
from unittest.mock import MagicMock


_PROFILE = {
    "alpha": True,
    "beta": True,
    "gamma": True,
    "periskope": False,
    "rom_persist": False,
    "subagent_allowed": False,
    "bypass_llm_only": False,
}


def _make_depth():
    from mekhane.mcp.depth_resolver import HarnessDepth
    return HarnessDepth.L2


def test_observe_anchor_returns_nine_fields():
    """A5: observe_anchor returns an ObservationAnchor with all 9 fields accessible."""
    from mekhane.organon import ObservationAnchor, observe_anchor
    from mekhane.mcp.depth_resolver import HarnessDepth

    depth = HarnessDepth.L2
    anchor = observe_anchor(
        invocation_id="inv-001",
        depth=depth,
        profile=dict(_PROFILE),
        session_id="sess-abc",
        timestamp="2026-05-02T00:00:00+00:00",
    )

    assert isinstance(anchor, ObservationAnchor)

    # All 9 fields accessible with correct types
    assert anchor.invocation_id == "inv-001"
    assert anchor.session_id == "sess-abc"
    assert anchor.depth == HarnessDepth.L2
    assert isinstance(anchor.profile, dict) or hasattr(anchor.profile, "__getitem__")
    assert anchor.delta_source == "posthoc_e_proxy"
    assert anchor.delta_scores_ref is None  # no provider given
    assert anchor.alerts_ref is None
    assert anchor.timestamp == "2026-05-02T00:00:00+00:00"
    assert anchor.confidence == "partial"

    # to_dict serialises correctly
    d = anchor.to_dict()
    assert d["depth"] == "L2"
    assert d["invocation_id"] == "inv-001"
    assert d["session_id"] == "sess-abc"
    assert d["delta_source"] == "posthoc_e_proxy"
    assert d["confidence"] == "partial"


def test_observe_anchor_does_not_compute_delta_immediately():
    """A6: delta_scores_provider is NOT called at anchor creation time.

    The provider must only be called when anchor.delta_scores_ref() is
    explicitly invoked by the caller.
    """
    from mekhane.organon import observe_anchor
    from mekhane.mcp.depth_resolver import HarnessDepth

    mock_provider = MagicMock(return_value={"an": 0.1, "ho": 0.2})

    anchor = observe_anchor(
        invocation_id="inv-002",
        depth=HarnessDepth.L3,
        profile=dict(_PROFILE),
        session_id="sess-lazy",
        timestamp="2026-05-02T01:00:00+00:00",
        delta_scores_provider=mock_provider,
    )

    # Provider must NOT have been called during observe_anchor()
    mock_provider.assert_not_called()

    # delta_scores_ref is a callable (not None)
    assert anchor.delta_scores_ref is not None
    assert callable(anchor.delta_scores_ref)

    # Only after explicit invocation does the provider run
    result = anchor.delta_scores_ref()
    mock_provider.assert_called_once_with("sess-lazy")
    assert result == {"an": 0.1, "ho": 0.2}


def test_observation_anchor_is_frozen():
    """ObservationAnchor is frozen=True: attribute reassignment raises FrozenInstanceError."""
    from mekhane.organon import observe_anchor
    from mekhane.mcp.depth_resolver import HarnessDepth

    anchor = observe_anchor(
        invocation_id="inv-003",
        depth=HarnessDepth.L1,
        profile=dict(_PROFILE),
        session_id="sess-frozen",
        timestamp="2026-05-02T02:00:00+00:00",
    )

    import pytest
    with pytest.raises(dataclasses.FrozenInstanceError):
        anchor.invocation_id = "x"  # type: ignore[misc]
