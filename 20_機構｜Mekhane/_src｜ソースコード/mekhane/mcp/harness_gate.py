from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/mcp/harness_gate.py
"""
Harness Gate — Apply harness profile to runtime singletons.

CONTEXT:
    Phase 1 of Depth-driven Harness Selection
    (plan: ccl-llm-api-hidden-popcorn.md).

    The depth_resolver picks a HarnessDepth (L0..L4); this module
    looks up the matching harness profile from harness_map.yaml and
    applies it to the live Daimonion + HGKFastMCP gateway instances
    BEFORE the gateway dispatches to the inner tool body.

PUBLIC API:
    load_harness_map(path)           -> dict
    get_profile(depth, harness_map)  -> dict   (defaults merged)
    apply(daimonion, gateway, profile) -> None (mutates singletons)
    is_bypass(profile)               -> bool   (L0 fast path)

DESIGN:
    - Pure side-effect functions; no global state owned here.
    - Graceful degrade: any failure logs to stderr and returns a
      regression-safe default (current implicit L2 behavior).
    - HGK_HARNESS_GATE=disabled env var -> apply() becomes a no-op
      (fast rollback without code changes).
"""

import os
import sys
from pathlib import Path
from typing import Any

import yaml

from mekhane.mcp.depth_resolver import HarnessDepth

__all__ = [
    "load_harness_map",
    "get_profile",
    "apply",
    "is_bypass",
]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default YAML path: sibling of this module (kept in sync with harness_map.yaml).
_DEFAULT_MAP_PATH = Path(__file__).resolve().parent / "harness_map.yaml"

# Rollback env var. When "disabled" (case-insensitive), apply() is a no-op.
_DISABLE_ENV_KEY = "HGK_HARNESS_GATE"
_DISABLE_VALUE = "disabled"

# Profile keys recognized by the gate (must match harness_map.yaml).
_PROFILE_KEYS = (
    "alpha",
    "beta",
    "gamma",
    "periskope",
    "rom_persist",
    "subagent_allowed",
    "bypass_llm_only",
)

# Regression-safe fallback: behaves like current implicit L2 default
# for L2, and disables everything for the other depths if the YAML is
# unreadable. This is intentional: a YAML failure must not silently
# enable new gates.
_SAFE_DEFAULT_MAP: dict[str, Any] = {
    "version": 1,
    "defaults": {k: False for k in _PROFILE_KEYS},
    "profiles": {
        "L0": {"bypass_llm_only": True},
        "L1": {k: False for k in _PROFILE_KEYS},
        "L2": {
            "alpha": True,
            "beta": True,
            "gamma": True,
            "subagent_allowed": True,
        },
        "L3": {k: False for k in _PROFILE_KEYS},
        "L4": {k: False for k in _PROFILE_KEYS},
    },
}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


# PURPOSE: Load harness_map.yaml and validate the minimal schema.
def load_harness_map(path: Path | None = None) -> dict[str, Any]:
    """Load the harness map YAML.

    On any failure (missing file, parse error, schema mismatch),
    log to stderr and return a regression-safe default dict.
    """
    target = Path(path) if path is not None else _DEFAULT_MAP_PATH
    try:
        with open(target, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except Exception as e:  # noqa: BLE001
        print(
            f"[Gateway/HarnessGate] load_harness_map failed for {target}: {e}",
            file=sys.stderr,
            flush=True,
        )
        return _SAFE_DEFAULT_MAP

    if not isinstance(data, dict):
        print(
            f"[Gateway/HarnessGate] {target} root is not a mapping; using safe default",
            file=sys.stderr,
            flush=True,
        )
        return _SAFE_DEFAULT_MAP

    if data.get("version") != 1:
        print(
            f"[Gateway/HarnessGate] {target} unsupported version "
            f"({data.get('version')!r}); using safe default",
            file=sys.stderr,
            flush=True,
        )
        return _SAFE_DEFAULT_MAP

    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        print(
            f"[Gateway/HarnessGate] {target} missing 'profiles'; using safe default",
            file=sys.stderr,
            flush=True,
        )
        return _SAFE_DEFAULT_MAP

    return data


# ---------------------------------------------------------------------------
# Profile resolution
# ---------------------------------------------------------------------------


# PURPOSE: Merge defaults with the depth-specific overrides.
def get_profile(
    depth: HarnessDepth,
    harness_map: dict[str, Any],
) -> dict[str, Any]:
    """Return the effective profile for `depth`.

    Order:
        1. Start from `defaults` (or all-False if absent).
        2. Overlay `profiles[depth.value]` overrides.
        3. Ensure all 7 profile keys are present.

    Unknown depth -> log + L2-equivalent fallback.
    """
    base: dict[str, Any] = {k: False for k in _PROFILE_KEYS}
    defaults = harness_map.get("defaults") if isinstance(harness_map, dict) else None
    if isinstance(defaults, dict):
        for k in _PROFILE_KEYS:
            if k in defaults:
                base[k] = bool(defaults[k])

    profiles = (
        harness_map.get("profiles") if isinstance(harness_map, dict) else None
    ) or {}
    profile_key = depth.value if isinstance(depth, HarnessDepth) else str(depth)

    overrides = profiles.get(profile_key)
    if overrides is None:
        print(
            f"[Gateway/HarnessGate] no profile for depth={profile_key!r}; "
            f"using defaults only",
            file=sys.stderr,
            flush=True,
        )
        overrides = {}
    if not isinstance(overrides, dict):
        print(
            f"[Gateway/HarnessGate] profile {profile_key!r} is not a mapping; "
            f"ignoring",
            file=sys.stderr,
            flush=True,
        )
        overrides = {}

    for k in _PROFILE_KEYS:
        if k in overrides:
            base[k] = bool(overrides[k])

    return base


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


# PURPOSE: Apply a harness profile to live daimonion + gateway singletons.
def apply(
    daimonion: Any,
    gateway: Any,
    profile: dict[str, Any],
) -> None:
    """Mutate the daimonion and gateway in place to reflect `profile`.

    - daimonion._alpha_enabled / _beta_enabled (existing attrs)
    - gateway._gamma_required, ._periskope_required, ._rom_persist_required,
      ._bypass_llm_only (created on demand via setattr)

    Safe defaults: missing keys -> False. Any exception -> log + return.
    Honors HGK_HARNESS_GATE=disabled by no-op'ing.
    """
    if (os.environ.get(_DISABLE_ENV_KEY, "").strip().lower() == _DISABLE_VALUE):
        return

    if not isinstance(profile, dict):
        print(
            f"[Gateway/HarnessGate] apply: profile must be dict, got {type(profile)!r}",
            file=sys.stderr,
            flush=True,
        )
        return

    try:
        if daimonion is not None:
            # Prefer explicit setters when present; fall back to direct attr
            # so unit tests can use SimpleNamespace stubs.
            alpha_val = bool(profile.get("alpha", False))
            beta_val = bool(profile.get("beta", False))
            if hasattr(daimonion, "set_alpha") and callable(
                getattr(daimonion, "set_alpha")
            ):
                daimonion.set_alpha(alpha_val)
            else:
                setattr(daimonion, "_alpha_enabled", alpha_val)
            if hasattr(daimonion, "set_beta") and callable(
                getattr(daimonion, "set_beta")
            ):
                daimonion.set_beta(beta_val)
            else:
                setattr(daimonion, "_beta_enabled", beta_val)

        if gateway is not None:
            setattr(gateway, "_gamma_required", bool(profile.get("gamma", False)))
            setattr(
                gateway,
                "_periskope_required",
                bool(profile.get("periskope", False)),
            )
            setattr(
                gateway,
                "_rom_persist_required",
                bool(profile.get("rom_persist", False)),
            )
            setattr(
                gateway,
                "_bypass_llm_only",
                bool(profile.get("bypass_llm_only", False)),
            )
            setattr(
                gateway,
                "_subagent_allowed",
                bool(profile.get("subagent_allowed", False)),
            )
    except Exception as e:  # noqa: BLE001
        print(
            f"[Gateway/HarnessGate] apply error (non-fatal): {e}",
            file=sys.stderr,
            flush=True,
        )


# PURPOSE: Convenience predicate for the L0 bypass fast path.
def is_bypass(profile: dict[str, Any]) -> bool:
    """True iff profile explicitly requests bare-LLM bypass."""
    if not isinstance(profile, dict):
        return False
    return bool(profile.get("bypass_llm_only", False))
