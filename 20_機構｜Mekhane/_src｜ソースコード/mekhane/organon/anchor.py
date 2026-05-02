# PROOF: [L2/Organon] <- mekhane/organon/anchor.py
"""Invocation-local ObservationAnchor — Wave 0.5 §5.2 adapter.

PURPOSE:
    Provide `ObservationAnchor` (frozen dataclass, 9 fields) and
    `observe_anchor()` factory function as required by Organon Wave 0.5
    acceptance criteria A5 and A6.

    This module is the adapter that bridges a single tool invocation
    (depth + profile) to Daimonion delta post-hoc scoring, without triggering
    `compute_delta_scores()` synchronously at anchor creation time.

    Symbol distinction:
        `observe_anchor`    — this file, invocation-local anchor
        `observe_session`   — mekhane/organon/observe.py, session-aggregate
                              Sensor Triad orchestrator

    The two are not merged: they are distinct in granularity (invocation
    vs. session-aggregate) and in design lineage (organon_kernel_contract.md
    §5.2 vs. sensor_triad_formal.md §3-4).

DESIGN INVARIANTS:
    - `ObservationAnchor` is frozen (immutable after creation).
    - `delta_scores_ref` is a lazy callable — it must NOT be called at
      anchor creation time (Wave 0.5 A6 acceptance).
    - `daimonion_delta.compute_delta_scores` is wired through
      `delta_scores_provider` as a Callable[[str], Any], ensuring the
      import of daimonion_delta is deferred to call time.
    - `alerts_ref` is reserved for future use; v0.1 always produces None.

REFERENCES:
    - organon_kernel_contract.md §5, §6 (ObservationAnchor 9 fields, sequence)
    - wave_0_5_acceptance_audit.md §1.1, §4 case I
    - mekhane/mcp/depth_resolver.py (HarnessDepth import source)
    - mekhane/mcp/harness_gate.py (_PROFILE_KEYS 7 keys)
    - mekhane/sympatheia/daimonion_delta.py (compute_delta_scores; lazy only)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Callable, Mapping

from mekhane.mcp.depth_resolver import HarnessDepth

__all__ = ["ObservationAnchor", "observe_anchor"]

# 7 keys from harness_gate._PROFILE_KEYS (source: mekhane/mcp/harness_gate.py:57-65)
_PROFILE_KEYS: frozenset[str] = frozenset({
    "alpha",
    "beta",
    "gamma",
    "periskope",
    "rom_persist",
    "subagent_allowed",
    "bypass_llm_only",
})


@dataclass(frozen=True, slots=True)
class ObservationAnchor:
    """Immutable anchor recording one tool invocation for Daimonion delta post-hoc.

    Fields match Wave 0.5 organon_kernel_contract.md §5.2 exactly:

        invocation_id   — identifies the single tool call
        session_id      — key consumed by compute_delta_scores(session_id)
        depth           — HarnessDepth resolved from CCL modifier / _depth
        profile         — read-only MappingProxyType with 7 harness_gate keys
        delta_source    — provenance tag; default "posthoc_e_proxy"
        delta_scores_ref — lazy Callable[[], Any] | None; call to trigger delta
        alerts_ref      — lazy Callable[[], Any] | None; v0.1 always None
        timestamp       — ISO 8601 UTC string of anchor creation
        confidence      — completeness marker; v0.1 default "partial"

    `profile` is stored as MappingProxyType to prevent external mutation
    after construction (frozen=True prevents reassignment but not dict mutation).
    """

    invocation_id: str
    session_id: str
    depth: HarnessDepth
    profile: Mapping[str, Any]
    delta_source: str = "posthoc_e_proxy"
    delta_scores_ref: Callable[[], Any] | None = None
    alerts_ref: Callable[[], Any] | None = None
    timestamp: str = ""
    confidence: str = "partial"

    def to_dict(self) -> dict[str, Any]:
        """Serialise anchor to a plain dict.

        Callable fields are reduced to their repr strings (not invoked).
        HarnessDepth is serialised via .name to produce e.g. "L2".
        """
        return {
            "invocation_id": self.invocation_id,
            "session_id": self.session_id,
            "depth": self.depth.name,
            "profile": dict(self.profile),
            "delta_source": self.delta_source,
            "delta_scores_ref": repr(self.delta_scores_ref),
            "alerts_ref": repr(self.alerts_ref),
            "timestamp": self.timestamp,
            "confidence": self.confidence,
        }


def observe_anchor(
    invocation_id: str,
    depth: HarnessDepth,
    profile: dict[str, Any],
    session_id: str,
    *,
    timestamp: str | None = None,
    delta_scores_provider: Callable[[str], Any] | None = None,
) -> ObservationAnchor:
    """Create an ObservationAnchor for one tool invocation.

    Args:
        invocation_id: Caller-supplied identifier for the invocation.
        depth:         HarnessDepth resolved from the invocation arguments.
        profile:       HarnessProfile dict (7 keys from harness_gate).
                       Extra keys are silently included; missing keys from
                       _PROFILE_KEYS raise ValueError.
        session_id:    Session key passed to Daimonion delta scoring later.
        timestamp:     ISO 8601 string; if None, defaults to UTC now.
        delta_scores_provider:
            Optional Callable[[str], Any] — typically
            `daimonion_delta.compute_delta_scores`.  When given, it is
            **lazily** wrapped as `lambda: provider(session_id)` and stored
            in `delta_scores_ref`.  The provider is NOT called here
            (Wave 0.5 A6 acceptance: anchor must not require delta computation
            at creation time).

    Returns:
        A frozen ObservationAnchor with `alerts_ref=None` (v0.1).

    Raises:
        TypeError:  if `depth` is not a HarnessDepth instance.
        ValueError: if `profile` is missing any of the 7 required keys.
    """
    if not isinstance(depth, HarnessDepth):
        raise TypeError(f"depth must be HarnessDepth, got {type(depth)!r}")

    missing = _PROFILE_KEYS - set(profile)
    if missing:
        raise ValueError(f"profile missing required keys: {sorted(missing)}")

    resolved_ts = timestamp if timestamp is not None else datetime.now(timezone.utc).isoformat()

    # Freeze profile to prevent external mutation after anchor construction.
    frozen_profile: Mapping[str, Any] = MappingProxyType(dict(profile))

    lazy_ref: Callable[[], Any] | None
    if delta_scores_provider is not None:
        # Capture session_id by value to avoid closure-cell mutation.
        # E731: use def instead of lambda assignment.
        _sid = session_id
        _provider = delta_scores_provider

        def _make_lazy(_p: Callable[[str], Any], _s: str) -> Callable[[], Any]:
            def _lazy() -> Any:
                return _p(_s)
            return _lazy

        lazy_ref = _make_lazy(_provider, _sid)
    else:
        lazy_ref = None

    return ObservationAnchor(
        invocation_id=invocation_id,
        session_id=session_id,
        depth=depth,
        profile=frozen_profile,
        delta_source="posthoc_e_proxy",
        delta_scores_ref=lazy_ref,
        alerts_ref=None,
        timestamp=resolved_ts,
        confidence="partial",
    )
