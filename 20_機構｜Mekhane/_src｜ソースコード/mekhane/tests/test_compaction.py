# PROOF: mekhane/tests/test_compaction.py
# PURPOSE: tests モジュールの compaction に対するテスト
"""Tests for mekhane.agent_guard.compaction."""

import pytest

from mekhane.agent_guard.compaction import (
    chunk_by_max_tokens,
    DEFAULT_SUMMARY_FALLBACK,
    estimate_history_tokens,
    estimate_tokens,
    needs_compaction,
    SAFETY_MARGIN,
    split_by_token_share,
    summarize_history,
)


# --- Fixtures ---


def _make_history(n: int, content_len: int = 100) -> list[dict]:
    """Generate a test history with n messages."""
    history = []
    for i in range(n):
        role = 1 if i % 2 == 0 else 2  # alternate user/model
        history.append({
            "author": role,
            "content": f"Message {i}: " + "x" * content_len,
        })
    return history


# --- estimate_tokens ---


class TestEstimateTokens:
    def test_empty_string(self):
        assert estimate_tokens("") == 0

    def test_short_string(self):
        # "hello" = 5 chars -> 5/4 = 1
        assert estimate_tokens("hello") == 1

    def test_longer_string(self):
        text = "a" * 400
        assert estimate_tokens(text) == 100  # 400/4

    def test_minimum_one(self):
        assert estimate_tokens("ab") == 1  # 2/4 rounds to 0, but min is 1


# --- estimate_history_tokens ---


class TestEstimateHistoryTokens:
    def test_empty_history(self):
        assert estimate_history_tokens([]) == 0

    def test_single_message(self):
        history = [{"author": 1, "content": "a" * 400}]
        assert estimate_history_tokens(history) == 100

    def test_multiple_messages(self):
        history = _make_history(4, content_len=100)
        # Each message: "Message N: " (11 chars) + 100 "x" = 111 chars -> 27 tokens
        total = estimate_history_tokens(history)
        assert total > 0
        assert total == sum(
            estimate_tokens(m["content"]) for m in history
        )

    def test_missing_content_key(self):
        history = [{"author": 1}, {"author": 2, "content": "hello"}]
        assert estimate_history_tokens(history) == estimate_tokens("hello")


# --- split_by_token_share ---


class TestSplitByTokenShare:
    def test_empty(self):
        assert split_by_token_share([]) == []

    def test_single_part(self):
        history = _make_history(2)
        result = split_by_token_share(history, parts=1)
        assert len(result) == 1
        assert result[0] == history

    def test_two_parts(self):
        history = _make_history(10, content_len=100)
        result = split_by_token_share(history, parts=2)
        assert len(result) == 2
        total_msgs = sum(len(chunk) for chunk in result)
        assert total_msgs == 10

    def test_parts_greater_than_messages(self):
        history = _make_history(3)
        result = split_by_token_share(history, parts=10)
        # parts is clamped to message count
        assert len(result) <= 3
        total_msgs = sum(len(chunk) for chunk in result)
        assert total_msgs == 3


# --- chunk_by_max_tokens ---


class TestChunkByMaxTokens:
    def test_empty(self):
        assert chunk_by_max_tokens([], 1000) == []

    def test_all_fit(self):
        history = _make_history(3, content_len=10)
        result = chunk_by_max_tokens(history, max_tokens=10000)
        assert len(result) == 1

    def test_splits_when_exceeding(self):
        # Each message ~27 tokens. 10 messages ~270 tokens.
        # max_tokens=100, effective_max = 100/1.2 = 83
        history = _make_history(10, content_len=100)
        result = chunk_by_max_tokens(history, max_tokens=100)
        assert len(result) > 1
        total_msgs = sum(len(chunk) for chunk in result)
        assert total_msgs == 10


# --- needs_compaction ---


class TestNeedsCompaction:
    def test_within_budget(self):
        history = _make_history(2, content_len=10)
        assert needs_compaction(history, context_window=100_000) is False

    def test_exceeds_budget(self):
        # 100 messages * ~27 tokens = ~2700 tokens
        # context_window=100, max_share=0.5 -> budget=50
        history = _make_history(100, content_len=100)
        assert needs_compaction(history, context_window=100) is True


# --- summarize_history ---


class TestSummarizeHistory:
    def test_empty_history(self):
        result = summarize_history([], ask_fn=lambda p, m: "unused")
        assert result == DEFAULT_SUMMARY_FALLBACK

    def test_with_previous_summary(self):
        result = summarize_history(
            [],
            ask_fn=lambda p, m: "unused",
            previous_summary="Previous context"
        )
        assert result == "Previous context"

    def test_calls_ask_fn(self):
        history = _make_history(3, content_len=50)
        called_with: list[str] = []

        def mock_ask(prompt: str, model: str) -> str:
            called_with.append(prompt)
            return "Summary result"

        result = summarize_history(history, ask_fn=mock_ask)
        assert result == "Summary result"
        assert len(called_with) == 1
        assert "[User]:" in called_with[0]

    def test_ask_fn_failure_returns_fallback(self):
        history = _make_history(2, content_len=10)

        def failing_ask(prompt: str, model: str) -> str:
            raise RuntimeError("API error")

        result = summarize_history(history, ask_fn=failing_ask)
        assert result == DEFAULT_SUMMARY_FALLBACK

    def test_long_content_truncated(self):
        history = [{"author": 1, "content": "y" * 5000}]
        called_with: list[str] = []

        def mock_ask(prompt: str, model: str) -> str:
            called_with.append(prompt)
            return "ok"

        summarize_history(history, ask_fn=mock_ask)
        # Content should be truncated to ~2000 chars + "[...truncated...]"
        assert "[...truncated...]" in called_with[0]


