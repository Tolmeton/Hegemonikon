# PROOF: [L1/テスト] <- mekhane/mcp/tests/test_harness_gate.py
"""
Tests for harness_gate — Phase 1 of Depth-driven Harness Selection.

Plan reference: ccl-llm-api-hidden-popcorn.md.

Verifies:
    - YAML loads & validates the live harness_map.yaml.
    - L2 profile is byte-identical to the current default (regression).
    - L0 yields bypass + alpha/beta off.
    - L3 yields periskope + rom_persist on.
    - L1 Phase 1 override keeps gamma+beta on (legacy compat).
    - HGK_HARNESS_GATE=disabled makes apply() a no-op.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from mekhane.mcp.depth_resolver import HarnessDepth
from mekhane.mcp.harness_gate import (
    apply,
    get_profile,
    is_bypass,
    load_harness_map,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def _clear_disable_env(monkeypatch):
    """Ensure HGK_HARNESS_GATE is unset for every test by default."""
    monkeypatch.delenv("HGK_HARNESS_GATE", raising=False)


@pytest.fixture
def harness_map():
    """The live harness_map.yaml loaded once per test that needs it."""
    return load_harness_map()


def _make_daimonion_stub() -> SimpleNamespace:
    """Mirror the attrs harness_gate writes to / reads from."""
    return SimpleNamespace(_alpha_enabled=True, _beta_enabled=True)


def _make_gateway_stub() -> SimpleNamespace:
    """Bare gateway stub; apply() must create the new attrs on demand."""
    return SimpleNamespace()


# =============================================================================
# load_harness_map
# =============================================================================


def test_load_harness_map_valid(harness_map):
    """Default path loads OK and version == 1."""
    assert isinstance(harness_map, dict)
    assert harness_map.get("version") == 1
    assert "profiles" in harness_map
    assert "L0" in harness_map["profiles"]
    assert "L2" in harness_map["profiles"]
    assert "L3" in harness_map["profiles"]


def test_load_harness_map_missing_file_returns_safe_default(tmp_path):
    """Nonexistent path -> safe-default dict (no exception)."""
    bogus = tmp_path / "no_such_file.yaml"
    data = load_harness_map(bogus)
    assert data.get("version") == 1
    # Safe default L2 must keep regression behavior on.
    assert data["profiles"]["L2"]["alpha"] is True
    assert data["profiles"]["L2"]["gamma"] is True


def test_load_harness_map_bad_version_returns_safe_default(tmp_path):
    """Wrong version -> safe-default fallback."""
    bad = tmp_path / "bad.yaml"
    bad.write_text("version: 99\nprofiles: {}\n", encoding="utf-8")
    data = load_harness_map(bad)
    # Safe default's L2 includes alpha=True; the bad file's empty profiles
    # would have produced an L2 with everything False if accepted.
    assert data["profiles"]["L2"]["alpha"] is True


# =============================================================================
# get_profile
# =============================================================================


def test_get_profile_l2_legacy_compat(harness_map):
    """L2 = current implicit default. Regression guarantee."""
    p = get_profile(HarnessDepth.L2, harness_map)
    assert p["alpha"] is True
    assert p["beta"] is True
    assert p["gamma"] is True
    assert p["subagent_allowed"] is True
    assert p["bypass_llm_only"] is False
    # All 7 keys must be present.
    for key in (
        "alpha",
        "beta",
        "gamma",
        "periskope",
        "rom_persist",
        "subagent_allowed",
        "bypass_llm_only",
    ):
        assert key in p, f"missing key {key} from resolved L2 profile"


def test_get_profile_l0_bypass(harness_map):
    """L0 turns bypass_llm_only on; alpha/beta/gamma stay off."""
    p = get_profile(HarnessDepth.L0, harness_map)
    assert p["bypass_llm_only"] is True
    assert p["alpha"] is False
    assert p["beta"] is False
    assert p["gamma"] is False


def test_get_profile_l3_periskope_and_rom_persist(harness_map):
    """L3 enables full Daimonion + Periskope + ROM persistence."""
    p = get_profile(HarnessDepth.L3, harness_map)
    assert p["alpha"] is True
    assert p["beta"] is True
    assert p["gamma"] is True
    assert p["periskope"] is True
    assert p["rom_persist"] is True
    assert p["subagent_allowed"] is True


def test_get_profile_l1_phase1_legacy(harness_map):
    """Phase 1 override: L1 keeps gamma=True and beta=True for legacy safety."""
    p = get_profile(HarnessDepth.L1, harness_map)
    assert p["alpha"] is True
    assert p["beta"] is True   # Phase 3 will flip to False.
    assert p["gamma"] is True  # Phase 3 will flip to False.


def test_get_profile_unknown_depth_falls_back_to_defaults():
    """Depth without an explicit profile entry returns defaults only."""
    fake_map = {
        "version": 1,
        "defaults": {"alpha": False, "gamma": False, "bypass_llm_only": False},
        "profiles": {"L2": {"alpha": True, "gamma": True}},
    }
    p = get_profile(HarnessDepth.L4, fake_map)
    # Defaults only -> all False.
    assert p["alpha"] is False
    assert p["gamma"] is False
    assert p["bypass_llm_only"] is False


# =============================================================================
# apply
# =============================================================================


def test_apply_l0_sets_bypass(harness_map):
    """L0 profile sets bypass_llm_only and disables alpha/beta."""
    daimonion = _make_daimonion_stub()
    gateway = _make_gateway_stub()
    profile = get_profile(HarnessDepth.L0, harness_map)
    apply(daimonion, gateway, profile)
    assert daimonion._alpha_enabled is False
    assert daimonion._beta_enabled is False
    assert gateway._bypass_llm_only is True
    assert gateway._gamma_required is False
    assert gateway._periskope_required is False


def test_apply_l3_sets_periskope_and_rom_persist(harness_map):
    """L3 profile sets periskope_required and rom_persist_required."""
    daimonion = _make_daimonion_stub()
    gateway = _make_gateway_stub()
    profile = get_profile(HarnessDepth.L3, harness_map)
    apply(daimonion, gateway, profile)
    assert daimonion._alpha_enabled is True
    assert daimonion._beta_enabled is True
    assert gateway._gamma_required is True
    assert gateway._periskope_required is True
    assert gateway._rom_persist_required is True
    assert gateway._bypass_llm_only is False


def test_apply_l2_byte_identical_regression(harness_map):
    """L2 must reproduce current default behavior exactly."""
    daimonion = _make_daimonion_stub()
    gateway = _make_gateway_stub()
    profile = get_profile(HarnessDepth.L2, harness_map)
    apply(daimonion, gateway, profile)
    assert daimonion._alpha_enabled is True
    assert daimonion._beta_enabled is True
    assert gateway._gamma_required is True
    assert gateway._periskope_required is False
    assert gateway._rom_persist_required is False
    assert gateway._bypass_llm_only is False
    assert gateway._subagent_allowed is True


def test_apply_l1_phase1_legacy(harness_map):
    """L1 Phase 1 override: gamma=True (legacy compat), beta=True."""
    daimonion = _make_daimonion_stub()
    gateway = _make_gateway_stub()
    profile = get_profile(HarnessDepth.L1, harness_map)
    apply(daimonion, gateway, profile)
    assert daimonion._alpha_enabled is True
    assert daimonion._beta_enabled is True   # Phase 3 will set False.
    assert gateway._gamma_required is True   # Phase 3 will set False.


def test_apply_uses_setters_when_present(harness_map):
    """If daimonion exposes set_alpha/set_beta, apply() must use them."""
    calls: dict[str, bool] = {}

    class _DaimonionWithSetters:
        def __init__(self):
            self._alpha_enabled = False
            self._beta_enabled = False

        def set_alpha(self, value: bool) -> None:
            calls["alpha"] = bool(value)
            self._alpha_enabled = bool(value)

        def set_beta(self, value: bool) -> None:
            calls["beta"] = bool(value)
            self._beta_enabled = bool(value)

    daimonion = _DaimonionWithSetters()
    gateway = _make_gateway_stub()
    profile = get_profile(HarnessDepth.L3, harness_map)
    apply(daimonion, gateway, profile)
    assert calls == {"alpha": True, "beta": True}


def test_disabled_env_makes_apply_noop(monkeypatch, harness_map):
    """HGK_HARNESS_GATE=disabled -> apply() leaves stubs untouched."""
    monkeypatch.setenv("HGK_HARNESS_GATE", "disabled")
    daimonion = _make_daimonion_stub()
    gateway = _make_gateway_stub()
    # Pre-state: alpha=True, beta=True; no gateway flags set.
    profile = get_profile(HarnessDepth.L0, harness_map)  # L0 normally flips to bypass
    apply(daimonion, gateway, profile)
    # No mutation expected.
    assert daimonion._alpha_enabled is True
    assert daimonion._beta_enabled is True
    assert not hasattr(gateway, "_bypass_llm_only")
    assert not hasattr(gateway, "_gamma_required")


def test_apply_handles_none_daimonion(harness_map):
    """apply(None, gateway, profile) must not crash."""
    gateway = _make_gateway_stub()
    profile = get_profile(HarnessDepth.L0, harness_map)
    apply(None, gateway, profile)
    assert gateway._bypass_llm_only is True


def test_apply_handles_none_gateway(harness_map):
    """apply(daimonion, None, profile) must not crash."""
    daimonion = _make_daimonion_stub()
    profile = get_profile(HarnessDepth.L0, harness_map)
    apply(daimonion, None, profile)
    assert daimonion._alpha_enabled is False


# =============================================================================
# is_bypass
# =============================================================================


def test_is_bypass_true_for_l0(harness_map):
    assert is_bypass(get_profile(HarnessDepth.L0, harness_map)) is True


def test_is_bypass_false_for_l2(harness_map):
    assert is_bypass(get_profile(HarnessDepth.L2, harness_map)) is False


def test_is_bypass_handles_non_dict():
    assert is_bypass(None) is False  # type: ignore[arg-type]
    assert is_bypass("nope") is False  # type: ignore[arg-type]
