# PROOF: mekhane/tests/test_agent_guard.py
# PURPOSE: tests モジュールの agent_guard に対するテスト
"""
AGENT GUARD モジュールのテスト — Context Window Guard
"""

from mekhane.agent_guard import (
    ContextWindowGuardResult,
    ContextWindowInfo,
    resolve_context_window,
    evaluate_guard,
)


def test_resolve_context_window_model():
    info = resolve_context_window(
        provider="google",
        model_id="gemini-1.5-pro",
        model_context_window=200_000,
        default_tokens=128_000,
    )
    assert info.tokens == 200_000
    assert info.source == "model"


def test_resolve_context_window_config():
    info = resolve_context_window(
        provider="google",
        model_id="gemini-1.5-pro",
        model_context_window=200_000,
        default_tokens=128_000,
        config={"capabilities": {"max_tokens": 100_000}}
    )
    assert info.tokens == 100_000
    assert info.source == "config"


def test_resolve_context_window_agent_cap():
    info = resolve_context_window(
        provider="google",
        model_id="gemini-1.5-pro",
        model_context_window=200_000,
        default_tokens=128_000,
        config={"agent_cap": 64_000}
    )
    assert info.tokens == 64_000
    assert info.source == "agent_cap"


def test_evaluate_guard_blocks_and_warns():
    # 1. Healthy: 64k
    info = ContextWindowInfo(tokens=64_000, source="model")
    res = evaluate_guard(info, warn_below_tokens=32_000, hard_min_tokens=16_000)
    assert not res.should_warn
    assert not res.should_block

    # 2. Warn: 20k
    info = ContextWindowInfo(tokens=20_000, source="model")
    res = evaluate_guard(info, warn_below_tokens=32_000, hard_min_tokens=16_000)
    assert res.should_warn
    assert not res.should_block

    # 3. Block: 8k
    info = ContextWindowInfo(tokens=8_000, source="model")
    res = evaluate_guard(info, warn_below_tokens=32_000, hard_min_tokens=16_000)
    assert res.should_warn
    assert res.should_block


def test_resolve_from_model():
    from mekhane.agent_guard.context_window import resolve_from_model
    # Known model
    info = resolve_from_model("gemini-3-flash-preview")
    assert info.tokens == 1_000_000
    assert info.source == "model"

    # Unknown model → default 128k
    info = resolve_from_model("unknown-model-xyz")
    assert info.tokens == 128_000


def test_resolve_from_model_runtime_config_agent_cap():
    from mekhane.agent_guard.context_window import resolve_from_model

    info = resolve_from_model(
        "gemini-3-flash-preview",
        runtime_config={"agent_cap": 64_000},
    )
    assert info.tokens == 64_000
    assert info.source == "agent_cap"


def test_resolve_from_model_runtime_config_capabilities():
    from mekhane.agent_guard.context_window import resolve_from_model

    info = resolve_from_model(
        "gemini-3-flash-preview",
        runtime_config={"capabilities": {"max_tokens": 100_000}},
    )
    assert info.tokens == 100_000
    assert info.source == "config"


def test_evaluate_guard_ratio():
    from mekhane.agent_guard.context_window import evaluate_guard_ratio
    # 100k tokens with reference 1M → ratio = 10%
    # warn at 25% (250k), block at 12.5% (125k)
    info = ContextWindowInfo(tokens=100_000, source="model")
    res = evaluate_guard_ratio(info, reference_tokens=1_000_000)
    assert res.should_warn   # 100k < 250k
    assert res.should_block  # 100k < 125k

    # 200k tokens → above block (125k) but below warn (250k)
    info = ContextWindowInfo(tokens=200_000, source="model")
    res = evaluate_guard_ratio(info, reference_tokens=1_000_000)
    assert res.should_warn   # 200k < 250k
    assert not res.should_block  # 200k > 125k

    # 300k tokens → healthy
    info = ContextWindowInfo(tokens=300_000, source="model")
    res = evaluate_guard_ratio(info, reference_tokens=1_000_000)
    assert not res.should_warn
    assert not res.should_block
