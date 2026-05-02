# PROOF: [L2/インフラ] <- mekhane/mcp/tests/test_depth_resolver.py
"""
Tests for depth_resolver — 3-path detection with priority order.

Plan reference: ccl-llm-api-hidden-popcorn.md (Phase 0 deliverable).
"""

import os
from typing import Any

import pytest

from mekhane.mcp.depth_resolver import (
    HarnessDepth,
    depth_from_ccl_modifier,
    resolve_depth,
)


# PURPOSE: Clear HGK_DEPTH env var around each test for isolation.
@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    monkeypatch.delenv("HGK_DEPTH", raising=False)


# =============================================================================
# Unit: depth_from_ccl_modifier
# =============================================================================


@pytest.mark.parametrize("expr,expected", [
    ("/noe+",   HarnessDepth.L3),
    ("/bou-",   HarnessDepth.L1),
    ("/noe",    HarnessDepth.L2),
    ("/dia--",  HarnessDepth.L0),
    ("/sop++",  HarnessDepth.L4),
    ("",        None),
    ("   ",     None),
])
def test_depth_from_ccl_modifier(expr: str, expected):
    assert depth_from_ccl_modifier(expr) == expected


def test_depth_from_ccl_modifier_non_string_returns_none():
    assert depth_from_ccl_modifier(None) is None  # type: ignore[arg-type]


# =============================================================================
# Integration: resolve_depth (3-path priority)
# =============================================================================


def test_resolve_depth_default_l2_when_no_signal():
    """No arguments, no env, no CCL -> L2 (regression-safe default)."""
    assert resolve_depth() == HarnessDepth.L2
    assert resolve_depth({}) == HarnessDepth.L2


def test_resolve_depth_explicit_argument_wins():
    """arguments['_depth'] = 'L0' -> L0 (highest priority)."""
    assert resolve_depth({"_depth": "L0"}) == HarnessDepth.L0
    assert resolve_depth({"_depth": "L3"}) == HarnessDepth.L3


def test_resolve_depth_explicit_lenient_parsing():
    """Accept 'l1', 'L1', '1' equivalently."""
    assert resolve_depth({"_depth": "l1"}) == HarnessDepth.L1
    assert resolve_depth({"_depth": "1"}) == HarnessDepth.L1


def test_resolve_depth_env_var_override(monkeypatch):
    """HGK_DEPTH=L3 with no argument -> L3."""
    monkeypatch.setenv("HGK_DEPTH", "L3")
    assert resolve_depth({}) == HarnessDepth.L3


def test_resolve_depth_explicit_arg_beats_env(monkeypatch):
    """arguments['_depth'] beats HGK_DEPTH (call-site override)."""
    monkeypatch.setenv("HGK_DEPTH", "L0")
    assert resolve_depth({"_depth": "L3"}) == HarnessDepth.L3


def test_resolve_depth_ccl_modifier():
    """arguments['ccl_expr'] with modifier -> derived depth."""
    assert resolve_depth({"ccl_expr": "/noe+"}) == HarnessDepth.L3
    assert resolve_depth({"ccl_expr": "/noe-"}) == HarnessDepth.L1
    assert resolve_depth({"ccl_expr": "/noe--"}) == HarnessDepth.L0


def test_resolve_depth_explicit_beats_ccl():
    """Path 1 (explicit) beats path 2 (CCL modifier)."""
    assert resolve_depth({"_depth": "L0", "ccl_expr": "/noe+"}) == HarnessDepth.L0


def test_resolve_depth_env_beats_ccl(monkeypatch):
    """Path 1b (env) beats path 2 (CCL modifier)."""
    monkeypatch.setenv("HGK_DEPTH", "L1")
    assert resolve_depth({"ccl_expr": "/noe+"}) == HarnessDepth.L1


def test_resolve_depth_ccl_beats_skill_frontmatter():
    """Path 2 (CCL modifier) beats path 3 (skill frontmatter)."""
    assert resolve_depth({
        "ccl_expr": "/noe+",
        "_skill_depth": "L1",
    }) == HarnessDepth.L3


def test_resolve_depth_skill_frontmatter_when_only_signal():
    """Path 3 only -> skill depth applies."""
    assert resolve_depth({"_skill_depth": "L1"}) == HarnessDepth.L1
    assert resolve_depth({"_skill_depth": "L3"}) == HarnessDepth.L3


def test_resolve_depth_invalid_explicit_falls_through():
    """Invalid _depth string falls through to next path (L2 default if alone)."""
    assert resolve_depth({"_depth": "garbage"}) == HarnessDepth.L2
    # Falls through to CCL path
    assert resolve_depth({
        "_depth": "garbage",
        "ccl_expr": "/noe+",
    }) == HarnessDepth.L3


def test_resolve_depth_handles_none_arguments():
    """None arguments must not crash."""
    assert resolve_depth(None) == HarnessDepth.L2


def test_resolve_depth_ignores_non_string_ccl_expr():
    """ccl_expr that is not a string is ignored gracefully."""
    assert resolve_depth({"ccl_expr": 12345}) == HarnessDepth.L2  # type: ignore[dict-item]
    assert resolve_depth({"ccl_expr": None}) == HarnessDepth.L2
