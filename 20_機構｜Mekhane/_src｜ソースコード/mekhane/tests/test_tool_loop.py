# PROOF: mekhane/tests/test_tool_loop.py
# PURPOSE: T-03 Tool Loop Guard の re-export 検証 + canonical API テスト
"""
Re-export テスト: mekhane.agent_guard.tool_loop が
hgk.api.tool_loop_guard の全シンボルを正しく re-export していることを検証。
ロジックテストは全て hgk/api/tests/test_tool_loop_guard.py (54テスト) が担う。
"""
import pytest


# ═══════════════════════════════════════════════════════════════
# 1. Re-export 検証
# ═══════════════════════════════════════════════════════════════

def test_reexported_symbols():
    """旧 import パスから主要シンボルにアクセスできること"""
    from mekhane.agent_guard.tool_loop import (
        ToolLoopGuard,
        LoopDetectionConfig,
        ToolCallRecord,
        LoopDetectionResult,
        hash_tool_call,
        hash_tool_outcome,
        is_known_poll_tool_call,
    )
    assert ToolLoopGuard is not None
    assert LoopDetectionConfig is not None


def test_class_api_from_package():
    """パッケージレベルからクラスベース API にアクセスできること"""
    from mekhane.agent_guard import ToolLoopGuard, LoopDetectionConfig
    guard = ToolLoopGuard()
    assert guard is not None
    cfg = LoopDetectionConfig()
    assert cfg.enabled is True


def test_identity_with_canonical():
    """re-export されたオブジェクトが canonical と同一であること"""
    from mekhane.agent_guard.tool_loop import ToolLoopGuard as W
    from hgk.api.tool_loop_guard import ToolLoopGuard as C
    assert W is C


def test_constant_aliases():
    """旧定数名の互換エイリアスが機能すること"""
    from mekhane.agent_guard.tool_loop import (
        TOOL_CALL_HISTORY_SIZE,
        GLOBAL_CIRCUIT_BREAKER_THRESHOLD,
        HISTORY_SIZE,
        CIRCUIT_BREAKER_THRESHOLD,
    )
    assert TOOL_CALL_HISTORY_SIZE == HISTORY_SIZE
    assert GLOBAL_CIRCUIT_BREAKER_THRESHOLD == CIRCUIT_BREAKER_THRESHOLD


# ═══════════════════════════════════════════════════════════════
# 2. 最小限の smoke test (canonical のロジックが通ること)
# ═══════════════════════════════════════════════════════════════

def test_guard_detect_no_loop():
    """空の Guard がループなしと判定すること"""
    from mekhane.agent_guard import ToolLoopGuard
    guard = ToolLoopGuard()
    res = guard.detect("some_tool", {"arg": "val"})
    assert not res.stuck


def test_guard_detect_generic_repeat():
    """同一ツール+引数+結果の連続でループ検知すること"""
    from mekhane.agent_guard import ToolLoopGuard
    from mekhane.agent_guard.tool_loop import LoopDetectionConfig
    guard = ToolLoopGuard(LoopDetectionConfig(warning_threshold=3, history_size=30))
    for i in range(5):
        guard.record_call("search_web", {"query": "test"})
        guard.record_outcome(
            "search_web", {"query": "test"},
            result={"output": f"Result at T{i}", "data": "same content " * 20},
        )
    res = guard.detect("search_web", {"query": "test"})
    assert res.stuck


def test_hash_functions():
    """ハッシュ関数が一貫した値を返すこと"""
    from mekhane.agent_guard.tool_loop import hash_tool_call, hash_tool_outcome
    h1 = hash_tool_call("t", {"a": 1})
    h2 = hash_tool_call("t", {"a": 1})
    assert h1 == h2
    r1 = hash_tool_outcome("t", {"a": 1}, result={"content": [{"type": "text", "text": "ok"}]})
    r2 = hash_tool_outcome("t", {"a": 1}, result={"content": [{"type": "text", "text": "ok"}]})
    assert r1 == r2
