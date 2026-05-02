# PROOF: [L2/インフラ] <- hgk/api/tests/test_tool_loop_guard.py
"""
Tool Loop Guard テスト — OpenClaw 移植の整合性検証。

検証対象:
  - 4層検知器 (generic_repeat, known_poll_no_progress, ping_pong, global_circuit_breaker)
  - hash_tool_outcome の精緻なフィールド選択
  - _extract_text_content, _format_error_for_hash, _is_known_poll_tool
  - _canonical_pair_key による warningKey 正規化
  - _is_soft_match (Entropy ベース進捗計測)
  - NON_DETERMINISTIC_TOOLS + result_serialized
"""

import pytest

from hgk.api.tool_loop_guard import (
    LoopDetectionConfig,
    NON_DETERMINISTIC_TOOLS,
    SOFT_MATCH_THRESHOLD,
    ToolLoopGuard,
    _canonical_pair_key,
    _extract_text_content,
    _format_error_for_hash,
    _is_known_poll_tool,
    _is_soft_match,
    hash_tool_call,
    hash_tool_outcome,
)


# =============================================================================
# Helper Functions
# =============================================================================


class TestExtractTextContent:
    def test_mcp_content_array(self):
        result = {"content": [
            {"type": "text", "text": "Hello"},
            {"type": "text", "text": "World"},
        ]}
        assert _extract_text_content(result) == "Hello\nWorld"

    def test_non_text_entries_filtered(self):
        result = {"content": [
            {"type": "text", "text": "Hello"},
            {"type": "image", "url": "..."},
            {"type": "text", "text": "World"},
        ]}
        assert _extract_text_content(result) == "Hello\nWorld"

    def test_empty_content(self):
        assert _extract_text_content({"content": []}) == ""

    def test_no_content_key(self):
        assert _extract_text_content({"output": "foo"}) == ""

    def test_not_dict(self):
        assert _extract_text_content("string") == ""
        assert _extract_text_content(None) == ""

    def test_whitespace_stripped(self):
        result = {"content": [{"type": "text", "text": "  hello  "}]}
        assert _extract_text_content(result) == "hello"


class TestFormatErrorForHash:
    def test_exception(self):
        err = ValueError("test error")
        assert _format_error_for_hash(err) == "test error"

    def test_exception_no_args(self):
        err = RuntimeError()
        assert _format_error_for_hash(err) == "RuntimeError"

    def test_string(self):
        assert _format_error_for_hash("error msg") == "error msg"

    def test_int(self):
        assert _format_error_for_hash(42) == "42"

    def test_dict(self):
        result = _format_error_for_hash({"code": 500})
        assert "500" in result


class TestIsKnownPollTool:
    def test_command_status(self):
        assert _is_known_poll_tool("command_status", {}) is True

    def test_read_terminal(self):
        assert _is_known_poll_tool("read_terminal", {}) is True

    def test_process_poll(self):
        assert _is_known_poll_tool("process", {"action": "poll"}) is True

    def test_process_log(self):
        assert _is_known_poll_tool("process", {"action": "log"}) is True

    def test_process_other(self):
        assert _is_known_poll_tool("process", {"action": "start"}) is False

    def test_regular_tool(self):
        assert _is_known_poll_tool("grep_search", {"query": "foo"}) is False

    def test_process_non_dict_params(self):
        assert _is_known_poll_tool("process", "not a dict") is False


class TestCanonicalPairKey:
    def test_order_independent(self):
        key_ab = _canonical_pair_key("aaa", "bbb")
        key_ba = _canonical_pair_key("bbb", "aaa")
        assert key_ab == key_ba

    def test_contains_separator(self):
        key = _canonical_pair_key("alpha", "beta")
        assert "|" in key


# =============================================================================
# Soft Matching (Entropy ベース進捗計測)
# =============================================================================


class TestIsSoftMatch:
    def test_identical_strings(self):
        assert _is_soft_match("hello world", "hello world") is True

    def test_both_none(self):
        assert _is_soft_match(None, None) is True

    def test_one_none(self):
        assert _is_soft_match("hello", None) is False
        assert _is_soft_match(None, "hello") is False

    def test_nearly_identical(self):
        """タイムスタンプだけ異なるテキスト — ソフトマッチすべき。"""
        a = '{"output": "Status: running", "timestamp": "2026-02-28T21:00:00"}'
        b = '{"output": "Status: running", "timestamp": "2026-02-28T21:00:05"}'
        assert _is_soft_match(a, b) is True

    def test_completely_different(self):
        a = "Hello World"
        b = "Completely different text that has nothing in common"
        assert _is_soft_match(a, b) is False

    def test_threshold_boundary(self):
        """5%超の変化 — ソフトマッチしないべき。"""
        base = "A" * 100
        changed = "B" * 6 + "A" * 94
        assert _is_soft_match(base, changed) is False


class TestNonDeterministicTools:
    def test_search_web_in_list(self):
        assert "search_web" in NON_DETERMINISTIC_TOOLS

    def test_read_url_content_in_list(self):
        assert "read_url_content" in NON_DETERMINISTIC_TOOLS

    def test_grep_not_in_list(self):
        assert "grep_search" not in NON_DETERMINISTIC_TOOLS


class TestSoftMatchStreak:
    def test_non_deterministic_tool_soft_match(self):
        """非決定的ツールのソフトマッチング — タイムスタンプのみ異なる結果でもストリーク。"""
        guard = ToolLoopGuard(LoopDetectionConfig(warning_threshold=3, history_size=30))
        for i in range(5):
            guard.record_call("search_web", {"query": "test"})
            guard.record_outcome(
                "search_web", {"query": "test"},
                result={"output": f"Result at 2026-02-28T21:00:0{i}", "data": "same content " * 20},
            )
        result = guard.detect("search_web", {"query": "test"})
        assert result.stuck is True

    def test_deterministic_tool_no_soft_match(self):
        """決定的ツール — ハッシュが異なれば進捗ありと判定。"""
        guard = ToolLoopGuard(LoopDetectionConfig(warning_threshold=3, history_size=30))
        for i in range(5):
            guard.record_call("grep_search", {"query": "test"})
            guard.record_outcome(
                "grep_search", {"query": "test"},
                result={"details": {"count": i},
                        "content": [{"type": "text", "text": f"Result {i}"}]},
            )
        result = guard.detect("grep_search", {"query": "test"})
        assert result.stuck is False

    def test_result_serialized_populated(self):
        """非決定的ツールでのみ result_serialized が保存される。"""
        guard = ToolLoopGuard()
        guard.record_call("search_web", {"q": "x"})
        guard.record_outcome("search_web", {"q": "x"}, result={"output": "hello"})
        assert guard.history[-1].result_serialized is not None

        guard.record_call("grep_search", {"q": "x"})
        guard.record_outcome("grep_search", {"q": "x"}, result={"output": "hello"})
        assert guard.history[-1].result_serialized is None


# =============================================================================
# Hash Functions
# =============================================================================


class TestHashToolCall:
    def test_deterministic(self):
        h1 = hash_tool_call("grep", {"query": "foo"})
        h2 = hash_tool_call("grep", {"query": "foo"})
        assert h1 == h2

    def test_different_params(self):
        h1 = hash_tool_call("grep", {"query": "foo"})
        h2 = hash_tool_call("grep", {"query": "bar"})
        assert h1 != h2

    def test_different_tools(self):
        h1 = hash_tool_call("grep", {"query": "foo"})
        h2 = hash_tool_call("find", {"query": "foo"})
        assert h1 != h2


class TestHashToolOutcome:
    def test_error_hashing(self):
        h = hash_tool_outcome("grep", {}, error=ValueError("boom"))
        assert h is not None
        assert h.startswith("error:")

    def test_none_result(self):
        assert hash_tool_outcome("grep", {}, result=None) is None

    def test_non_dict_result(self):
        h = hash_tool_outcome("grep", {}, result="simple string")
        assert h is not None

    def test_general_dict_uses_details_and_text(self):
        result = {
            "details": {"count": 5},
            "content": [{"type": "text", "text": "found"}],
        }
        h = hash_tool_outcome("grep", {"q": "x"}, result=result)
        assert h is not None

    def test_process_poll_selective_fields(self):
        result_a = {
            "details": {"status": "running", "exitCode": None, "exitSignal": None,
                        "aggregated": None, "extra_field": "ignore_me"},
            "content": [{"type": "text", "text": "output"}],
        }
        result_b = {
            "details": {"status": "running", "exitCode": None, "exitSignal": None,
                        "aggregated": None, "extra_field": "different_value"},
            "content": [{"type": "text", "text": "output"}],
        }
        params = {"action": "poll"}
        h_a = hash_tool_outcome("process", params, result=result_a)
        h_b = hash_tool_outcome("process", params, result=result_b)
        assert h_a == h_b

    def test_process_log_selective_fields(self):
        result = {
            "details": {"status": "done", "totalLines": 100, "totalChars": 5000,
                        "truncated": False, "exitCode": 0, "exitSignal": None},
            "content": [{"type": "text", "text": "log output"}],
        }
        h = hash_tool_outcome("process", {"action": "log"}, result=result)
        assert h is not None

    def test_command_status_uses_general_hash(self):
        result = {
            "details": {"status": "running"},
            "content": [{"type": "text", "text": "waiting"}],
        }
        h = hash_tool_outcome("command_status", {}, result=result)
        assert h is not None


# =============================================================================
# 4 Layer Detection
# =============================================================================


class TestGenericRepeat:
    def test_no_detection_below_threshold(self):
        guard = ToolLoopGuard()
        for _ in range(9):
            guard.record_call("grep", {"q": "foo"})
        result = guard.detect("grep", {"q": "foo"})
        assert result.stuck is False

    def test_warning_at_threshold(self):
        guard = ToolLoopGuard()
        for _ in range(10):
            guard.record_call("grep", {"q": "foo"})
        result = guard.detect("grep", {"q": "foo"})
        assert result.stuck is True
        assert result.level == "warning"
        assert result.detector == "generic_repeat"

    def test_poll_tool_excluded(self):
        guard = ToolLoopGuard()
        for _ in range(15):
            guard.record_call("command_status", {"id": "123"})
        result = guard.detect("command_status", {"id": "123"})
        assert result.detector != "generic_repeat"


class TestKnownPollNoProgress:
    def test_warning_at_threshold(self):
        guard = ToolLoopGuard()
        for _ in range(10):
            guard.record_call("command_status", {"id": "abc"})
            guard.record_outcome("command_status", {"id": "abc"},
                                 result={"details": {"status": "running"},
                                         "content": [{"type": "text", "text": "still running"}]})
        result = guard.detect("command_status", {"id": "abc"})
        assert result.stuck is True
        assert result.level == "warning"
        assert result.detector == "known_poll_no_progress"

    def test_no_warning_with_changing_result(self):
        guard = ToolLoopGuard()
        for i in range(10):
            guard.record_call("command_status", {"id": "abc"})
            guard.record_outcome("command_status", {"id": "abc"},
                                 result={"details": {"status": "running"},
                                         "content": [{"type": "text", "text": f"line {i}"}]})
        result = guard.detect("command_status", {"id": "abc"})
        assert result.stuck is False


class TestGlobalCircuitBreaker:
    def test_triggers_at_threshold(self):
        guard = ToolLoopGuard()
        for _ in range(30):
            guard.record_call("grep", {"q": "foo"})
            guard.record_outcome("grep", {"q": "foo"},
                                 result={"details": {},
                                         "content": [{"type": "text", "text": "same"}]})
        result = guard.detect("grep", {"q": "foo"})
        assert result.stuck is True
        assert result.level == "critical"
        assert result.detector == "global_circuit_breaker"


class TestPingPong:
    def test_warning_at_threshold(self):
        guard = ToolLoopGuard()
        for i in range(10):
            if i % 2 == 0:
                guard.record_call("grep", {"q": "foo"})
            else:
                guard.record_call("find", {"path": "bar"})
        result = guard.detect("grep", {"q": "foo"})
        assert result.stuck is True
        assert result.detector == "ping_pong"

    def test_canonical_warning_key(self):
        guard = ToolLoopGuard()
        for i in range(12):
            if i % 2 == 0:
                guard.record_call("grep", {"q": "foo"})
            else:
                guard.record_call("find", {"path": "bar"})
        result = guard.detect("grep", {"q": "foo"})
        assert result.stuck is True
        assert result.warning_key is not None
        assert "|" in result.warning_key


class TestDisabled:
    def test_disabled_returns_not_stuck(self):
        config = LoopDetectionConfig(enabled=False)
        guard = ToolLoopGuard(config=config)
        for _ in range(50):
            guard.record_call("grep", {"q": "foo"})
        result = guard.detect("grep", {"q": "foo"})
        assert result.stuck is False


class TestStats:
    def test_stats_output(self):
        guard = ToolLoopGuard()
        guard.record_call("grep", {"q": "foo"})
        guard.record_call("grep", {"q": "foo"})
        guard.record_call("find", {"path": "bar"})
        stats = guard.get_stats()
        assert stats["total_calls"] == 3
        assert stats["unique_patterns"] == 2
        assert stats["most_frequent"]["count"] == 2


class TestConfig:
    def test_threshold_auto_correction(self):
        config = LoopDetectionConfig(
            warning_threshold=20,
            critical_threshold=10,
            circuit_breaker_threshold=5,
        )
        assert config.critical_threshold == 21
        assert config.circuit_breaker_threshold == 22

    def test_design_decision_documented(self):
        config = LoopDetectionConfig()
        assert config.enabled is True
        assert "Design Decision" in LoopDetectionConfig.__doc__
