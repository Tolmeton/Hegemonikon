# PROOF: [L2/テスト] <- mekhane/ochema/tests/test_model_fallback.py T-08 テスト
# PURPOSE: Model Fallback のユニットテスト
"""Tests for mekhane.ochema.model_fallback."""


from __future__ import annotations
import asyncio
import time
from unittest.mock import AsyncMock

import pytest

from mekhane.ochema.model_fallback import (
    AllCandidatesFailedError,
    ContextOverflowError,
    CooldownManager,
    ErrorKind,
    FallbackAttempt,
    ModelCandidate,
    build_candidate_chain,
    classify_error,
    run_with_model_fallback,
    run_with_model_fallback_sync,
)


# --- ModelCandidate ---


class TestModelCandidate:
    def test_key(self):
        c = ModelCandidate(provider="google", model="gemini-pro")
        assert c.key == "google/gemini-pro"

    def test_equality(self):
        a = ModelCandidate(provider="google", model="gemini-pro")
        b = ModelCandidate(provider="google", model="gemini-pro")
        assert a == b

    def test_frozen(self):
        c = ModelCandidate(provider="google", model="gemini-pro")
        with pytest.raises(AttributeError):
            c.provider = "openai"  # type: ignore[misc]


# --- build_candidate_chain ---


class TestBuildCandidateChain:
    def test_primary_only(self):
        p = ModelCandidate("google", "gemini-pro")
        chain = build_candidate_chain(p)
        assert chain == [p]

    def test_with_fallbacks(self):
        p = ModelCandidate("google", "gemini-pro")
        f1 = ModelCandidate("openai", "gpt-4o")
        f2 = ModelCandidate("anthropic", "claude-sonnet")
        chain = build_candidate_chain(p, fallbacks=[f1, f2])
        assert chain == [p, f1, f2]

    def test_dedup(self):
        p = ModelCandidate("google", "gemini-pro")
        f1 = ModelCandidate("google", "gemini-pro")  # duplicate
        f2 = ModelCandidate("openai", "gpt-4o")
        chain = build_candidate_chain(p, fallbacks=[f1, f2])
        assert chain == [p, f2]

    def test_config_default(self):
        p = ModelCandidate("google", "gemini-pro")
        d = ModelCandidate("openai", "gpt-4o")
        chain = build_candidate_chain(p, config_default=d)
        assert chain == [p, d]

    def test_config_default_same_as_primary(self):
        p = ModelCandidate("google", "gemini-pro")
        chain = build_candidate_chain(p, config_default=p)
        assert chain == [p]  # no duplicate


# --- CooldownManager ---


class TestCooldownManager:
    def test_no_cooldown(self):
        cm = CooldownManager()
        assert not cm.is_in_cooldown("google")

    def test_mark_and_check(self):
        cm = CooldownManager()
        cm.mark_cooldown("google", cooldown=60.0)
        assert cm.is_in_cooldown("google")

    def test_expiry(self):
        cm = CooldownManager()
        cm.mark_cooldown("google", cooldown=0.01)  # 10ms
        time.sleep(0.02)
        assert not cm.is_in_cooldown("google")

    def test_get_cooldown_expiry(self):
        cm = CooldownManager()
        assert cm.get_cooldown_expiry("google") is None
        cm.mark_cooldown("google", cooldown=60.0)
        expiry = cm.get_cooldown_expiry("google")
        assert expiry is not None
        assert expiry > time.monotonic()

    def test_error_kind_tracking(self):
        cm = CooldownManager()
        cm.mark_cooldown("google", error_kind=ErrorKind.AUTH)
        assert cm.get_cooldown_error_kind("google") == ErrorKind.AUTH

    def test_should_probe_primary_no_fallback(self):
        cm = CooldownManager()
        cm.mark_cooldown("google", cooldown=60.0)
        assert not cm.should_probe_primary(
            "google", is_primary=True, has_fallback=False
        )

    def test_should_probe_primary_throttle(self):
        cm = CooldownManager()
        cm.mark_cooldown("google", cooldown=60.0)
        cm.mark_probe("google")
        assert not cm.should_probe_primary(
            "google", is_primary=True, has_fallback=True
        )

    def test_resolve_cooldown_decision_persistent(self):
        cm = CooldownManager()
        cm.mark_cooldown("google", error_kind=ErrorKind.AUTH, cooldown=600.0)
        c = ModelCandidate("google", "gemini-pro")
        decision = cm.resolve_cooldown_decision(
            c, is_primary=True, has_fallback=True
        )
        assert decision.action == "skip"
        assert decision.error_kind == ErrorKind.AUTH

    def test_resolve_cooldown_decision_rate_limit_non_primary(self):
        cm = CooldownManager()
        cm.mark_cooldown("google", error_kind=ErrorKind.RATE_LIMIT, cooldown=60.0)
        c = ModelCandidate("google", "gemini-flash")
        decision = cm.resolve_cooldown_decision(
            c, is_primary=False, has_fallback=True
        )
        assert decision.action == "attempt"

    def test_clear(self):
        cm = CooldownManager()
        cm.mark_cooldown("google", cooldown=60.0)
        cm.mark_probe("google")
        cm.clear()
        assert not cm.is_in_cooldown("google")


# --- classify_error ---


class TestClassifyError:
    def test_context_overflow(self):
        assert classify_error(ContextOverflowError("too long")) == ErrorKind.CONTEXT_OVERFLOW

    def test_cancelled_error(self):
        assert classify_error(asyncio.CancelledError()) == ErrorKind.ABORT

    def test_status_429(self):
        err = Exception("rate limited")
        err.status = 429  # type: ignore[attr-defined]
        assert classify_error(err) == ErrorKind.RATE_LIMIT

    def test_status_401(self):
        err = Exception("unauthorized")
        err.status = 401  # type: ignore[attr-defined]
        assert classify_error(err) == ErrorKind.AUTH

    def test_status_402_billing(self):
        err = Exception("payment required")
        err.status = 402  # type: ignore[attr-defined]
        assert classify_error(err) == ErrorKind.BILLING

    def test_message_rate_limit(self):
        assert classify_error(Exception("Too Many Requests")) == ErrorKind.RATE_LIMIT

    def test_message_context_overflow(self):
        assert classify_error(Exception("context too long")) == ErrorKind.CONTEXT_OVERFLOW

    def test_timeout(self):
        assert classify_error(asyncio.TimeoutError()) == ErrorKind.TIMEOUT

    def test_unknown(self):
        assert classify_error(Exception("something weird")) == ErrorKind.UNKNOWN


# --- run_with_model_fallback ---


class TestRunWithModelFallback:
    @pytest.mark.asyncio
    async def test_primary_success(self):
        candidates = [ModelCandidate("google", "gemini-pro")]
        run = AsyncMock(return_value="ok")
        result = await run_with_model_fallback(candidates, run)
        assert result.result == "ok"
        assert result.provider == "google"
        assert result.model == "gemini-pro"
        assert len(result.attempts) == 0

    @pytest.mark.asyncio
    async def test_fallback_on_error(self):
        c1 = ModelCandidate("google", "gemini-pro")
        c2 = ModelCandidate("openai", "gpt-4o")

        call_count = [0]

        async def run(provider: str, model: str) -> str:
            call_count[0] += 1
            if provider == "google":
                err = Exception("service unavailable")
                err.status = 503  # type: ignore[attr-defined]
                raise err
            return "fallback_ok"

        result = await run_with_model_fallback([c1, c2], run)
        assert result.result == "fallback_ok"
        assert result.provider == "openai"
        assert len(result.attempts) == 1
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_context_overflow_no_fallback(self):
        c1 = ModelCandidate("google", "gemini-pro")
        c2 = ModelCandidate("openai", "gpt-4o")

        async def run(provider: str, model: str) -> str:
            raise ContextOverflowError("too long")

        with pytest.raises(ContextOverflowError):
            await run_with_model_fallback([c1, c2], run)

    @pytest.mark.asyncio
    async def test_abort_no_fallback(self):
        c1 = ModelCandidate("google", "gemini-pro")
        c2 = ModelCandidate("openai", "gpt-4o")

        async def run(provider: str, model: str) -> str:
            raise asyncio.CancelledError()

        with pytest.raises(asyncio.CancelledError):
            await run_with_model_fallback([c1, c2], run)

    @pytest.mark.asyncio
    async def test_all_candidates_fail(self):
        c1 = ModelCandidate("google", "gemini-pro")
        c2 = ModelCandidate("openai", "gpt-4o")

        async def run(provider: str, model: str) -> str:
            err = Exception("rate limited")
            err.status = 429  # type: ignore[attr-defined]
            raise err

        with pytest.raises(AllCandidatesFailedError) as exc_info:
            await run_with_model_fallback([c1, c2], run)
        assert len(exc_info.value.attempts) == 2

    @pytest.mark.asyncio
    async def test_cooldown_skip(self):
        cm = CooldownManager()
        cm.mark_cooldown("google", error_kind=ErrorKind.AUTH, cooldown=600.0)

        c1 = ModelCandidate("google", "gemini-pro")
        c2 = ModelCandidate("openai", "gpt-4o")

        run = AsyncMock(return_value="ok")
        result = await run_with_model_fallback(
            [c1, c2], run, cooldown_manager=cm
        )
        assert result.provider == "openai"
        assert len(result.attempts) == 1
        assert result.attempts[0].error_kind == ErrorKind.AUTH

    @pytest.mark.asyncio
    async def test_deadline_timeout(self):
        c1 = ModelCandidate("google", "gemini-pro")

        async def run(provider: str, model: str) -> str:
            await asyncio.sleep(10)
            return "ok"

        with pytest.raises(asyncio.TimeoutError):
            await run_with_model_fallback([c1], run, deadline=0.05)

    @pytest.mark.asyncio
    async def test_on_error_callback(self):
        c1 = ModelCandidate("google", "gemini-pro")
        c2 = ModelCandidate("openai", "gpt-4o")
        errors: list[FallbackAttempt] = []

        async def run(provider: str, model: str) -> str:
            if provider == "google":
                err = Exception("fail")
                err.status = 500  # type: ignore[attr-defined]
                raise err
            return "ok"

        async def on_err(attempt: FallbackAttempt) -> None:
            errors.append(attempt)

        result = await run_with_model_fallback(
            [c1, c2], run, on_error=on_err
        )
        assert result.result == "ok"
        assert len(errors) == 1

    @pytest.mark.asyncio
    async def test_no_candidates_raises(self):
        with pytest.raises(ValueError, match="No model candidates"):
            await run_with_model_fallback([], AsyncMock())

    @pytest.mark.asyncio
    async def test_rate_limit_marks_cooldown(self):
        cm = CooldownManager()
        c1 = ModelCandidate("google", "gemini-pro")
        c2 = ModelCandidate("openai", "gpt-4o")

        async def run(provider: str, model: str) -> str:
            if provider == "google":
                err = Exception("rate limited")
                err.status = 429  # type: ignore[attr-defined]
                raise err
            return "ok"

        await run_with_model_fallback([c1, c2], run, cooldown_manager=cm)
        assert cm.is_in_cooldown("google")

# --- run_with_model_fallback_sync ---


class TestRunWithModelFallbackSync:
    def test_success_first_candidate(self):
        candidates = [ModelCandidate("google", "gemini-pro")]
        
        def run(provider: str, model: str) -> str:
            return "ok"
            
        result = run_with_model_fallback_sync(candidates, run)
        assert result.result == "ok"
        assert result.provider == "google"
        assert result.model == "gemini-pro"
        assert len(result.attempts) == 0

    def test_fallback_on_error(self):
        c1 = ModelCandidate("google", "gemini-pro")
        c2 = ModelCandidate("openai", "gpt-4o")
        call_count = [0]

        def run(provider: str, model: str) -> str:
            call_count[0] += 1
            if provider == "google":
                err = Exception("service unavailable")
                err.status = 503  # type: ignore[attr-defined]
                raise err
            return "fallback_ok"

        result = run_with_model_fallback_sync([c1, c2], run)
        assert result.result == "fallback_ok"
        assert result.provider == "openai"
        assert len(result.attempts) == 1
        assert call_count[0] == 2

    def test_all_candidates_fail(self):
        c1 = ModelCandidate("google", "gemini-pro")
        c2 = ModelCandidate("openai", "gpt-4o")

        def run(provider: str, model: str) -> str:
            err = Exception("rate limited")
            err.status = 429  # type: ignore[attr-defined]
            raise err

        with pytest.raises(AllCandidatesFailedError) as exc_info:
            run_with_model_fallback_sync([c1, c2], run)
        assert len(exc_info.value.attempts) == 2

    def test_no_candidates_raises(self):
        with pytest.raises(ValueError, match="No model candidates"):
            run_with_model_fallback_sync([], lambda p, m: "ok")
