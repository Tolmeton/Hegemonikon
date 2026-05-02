# PROOF: [L2/インフラ] <- mekhane/ochema/model_fallback.py T-08→Model Fallback with Cooldown/Probe
# PURPOSE: Model Fallback — OpenClaw model-fallback.ts (571L) pattern transfer to HGK
"""Model Fallback with Cooldown/Probe Strategy.

Ported from OpenClaw src/agents/model-fallback.ts (571 lines).
Provides resilient model routing with:
- Candidate chain (dedup + ordering)
- Cooldown/Probe strategy (30s throttle, 2min margin)
- Error classification (persistent vs transient)
- Async fallback loop with deadline
"""


from __future__ import annotations
import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Awaitable, Callable, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


# --- Error Classification ---


# PURPOSE: Classify errors into categories that determine fallback behavior
class ErrorKind(Enum):
    """Error classification for fallback decisions."""

    RATE_LIMIT = "rate_limit"  # 429 — transient, try sibling models
    AUTH = "auth"  # 401/403 — persistent, skip provider
    AUTH_PERMANENT = "auth_permanent"  # billing/quota — permanent skip
    BILLING = "billing"  # payment required — permanent skip
    CONTEXT_OVERFLOW = "context_overflow"  # token limit — don't fallback
    ABORT = "abort"  # user cancelled — don't fallback
    TIMEOUT = "timeout"  # request timeout — transient
    UNKNOWN = "unknown"  # unclassified — continue if candidates remain


PERSISTENT_ERRORS = frozenset(
    {ErrorKind.AUTH, ErrorKind.AUTH_PERMANENT, ErrorKind.BILLING}
)


# PURPOSE: Custom exceptions for fallback error handling
class FallbackError(Exception):
    """Base class for fallback-related errors."""

    pass


class AllCandidatesFailedError(FallbackError):
    """All model candidates exhausted."""

    def __init__(self, attempts: list[FallbackAttempt], message: str = ""):
        self.attempts = attempts
        super().__init__(
            message
            or f"All models failed ({len(attempts)}): "
            + " | ".join(str(a) for a in attempts)
        )


class ContextOverflowError(FallbackError):
    """Context window exceeded — do NOT fallback to a smaller model."""

    pass


# --- Data Classes ---


@dataclass(frozen=True)
class ModelCandidate:
    """A provider/model pair to attempt."""

    provider: str
    model: str

    @property
    def key(self) -> str:
        return f"{self.provider}/{self.model}"


@dataclass
class FallbackAttempt:
    """Record of a single fallback attempt."""

    provider: str
    model: str
    error: str
    error_kind: ErrorKind = ErrorKind.UNKNOWN
    status: int | None = None

    def __str__(self) -> str:
        suffix = f" ({self.error_kind.value})" if self.error_kind != ErrorKind.UNKNOWN else ""
        return f"{self.provider}/{self.model}: {self.error}{suffix}"


@dataclass
class FallbackResult(Generic[T]):
    """Result of a successful fallback execution."""

    result: T
    provider: str
    model: str
    attempts: list[FallbackAttempt] = field(default_factory=list)


# --- Cooldown Manager ---


# PURPOSE: Manage cooldown state and probe decisions per provider
class CooldownManager:
    """Manages cooldown state and probe decisions for model providers.

    Ported from OpenClaw's probe throttle logic:
    - MIN_PROBE_INTERVAL: 30 seconds between probes per provider
    - PROBE_MARGIN: 120 seconds before cooldown expiry, start probing
    """

    MIN_PROBE_INTERVAL: float = 30.0  # seconds
    PROBE_MARGIN: float = 120.0  # seconds — start probing 2min before expiry
    DEFAULT_COOLDOWN: float = 60.0  # seconds

    def __init__(self) -> None:
        self._last_probe: dict[str, float] = {}
        self._cooldowns: dict[str, _CooldownEntry] = {}

    def mark_cooldown(
        self,
        provider: str,
        error_kind: ErrorKind = ErrorKind.RATE_LIMIT,
        cooldown: float | None = None,
    ) -> None:
        """Mark a provider as in cooldown."""
        cd = cooldown if cooldown is not None else self.DEFAULT_COOLDOWN
        self._cooldowns[provider] = _CooldownEntry(
            expires_at=time.monotonic() + cd,
            error_kind=error_kind,
        )
        logger.debug(
            "Cooldown: %s marked %s for %.0fs",
            provider,
            error_kind.value,
            cd,
        )

    def is_in_cooldown(self, provider: str) -> bool:
        """Check if provider is currently in cooldown."""
        entry = self._cooldowns.get(provider)
        if entry is None:
            return False
        if time.monotonic() >= entry.expires_at:
            del self._cooldowns[provider]
            return False
        return True

    def get_time_since_last_probe(self, provider: str) -> float:
        """Get seconds since the last probe for a provider."""
        last_probe = self._last_probe.get(provider, 0.0)
        return time.monotonic() - last_probe

    def get_cooldown_expiry(self, provider: str) -> float | None:
        """Get cooldown expiry time (monotonic), or None if not in cooldown."""
        entry = self._cooldowns.get(provider)
        if entry is None:
            return None
        now = time.monotonic()
        if now >= entry.expires_at:
            del self._cooldowns[provider]
            return None
        return entry.expires_at

    def get_cooldown_error_kind(self, provider: str) -> ErrorKind | None:
        """Get the error kind that caused the cooldown."""
        entry = self._cooldowns.get(provider)
        return entry.error_kind if entry else None

    def should_probe_primary(
        self,
        provider: str,
        *,
        is_primary: bool,
        has_fallback: bool,
    ) -> bool:
        """Determine whether to probe a cooldown-ed primary provider.

        Probe conditions (all must be true):
        1. This is the primary candidate
        2. Fallback candidates exist (otherwise always attempt)
        3. Enough time has passed since last probe (30s throttle)
        4. Cooldown is about to expire (within 2min margin) or already expired
        """
        if not is_primary or not has_fallback:
            return False

        now = time.monotonic()

        # Throttle check
        last = self._last_probe.get(provider, 0.0)
        if now - last < self.MIN_PROBE_INTERVAL:
            return False

        # Margin check
        expiry = self.get_cooldown_expiry(provider)
        if expiry is None:
            return True  # cooldown expired, always probe
        return now >= expiry - self.PROBE_MARGIN

    def should_probe_account(self, provider: str) -> bool:
        """Determine whether to probe a cooldown-ed account (account-level round-robin).

        Account-level probe is more conservative than model-level:
        - Only probes when cooldown has < 30s remaining (vs 120s for model-level)
        - Skips persistent errors (AUTH, AUTH_PERMANENT, BILLING)
        - Enforces MIN_PROBE_INTERVAL throttle

        Returns True if the account should be probed, False otherwise.
        """
        error_kind = self.get_cooldown_error_kind(provider)
        if error_kind in PERSISTENT_ERRORS:
            return False

        expiry = self.get_cooldown_expiry(provider)
        if expiry is None:
            return False  # Not in cooldown — no need to probe

        remaining = expiry - time.monotonic()
        if remaining >= self.MIN_PROBE_INTERVAL:
            return False  # Too much cooldown remaining

        # Throttle check
        if self.get_time_since_last_probe(provider) < self.MIN_PROBE_INTERVAL:
            return False

        return True

    def mark_probe(self, provider: str) -> None:
        """Record that a probe was attempted."""
        self._last_probe[provider] = time.monotonic()

    def resolve_cooldown_decision(
        self,
        candidate: ModelCandidate,
        *,
        is_primary: bool,
        has_fallback: bool,
    ) -> CooldownDecision:
        """Decide whether to skip or attempt a cooldown-ed candidate.

        Logic (ported from OpenClaw resolveCooldownDecision):
        - Persistent error (auth/billing) → always skip
        - Primary + probe allowed → attempt with probe mark
        - Non-primary + rate_limit → attempt (model-scoped recovery)
        - Otherwise → skip
        """
        error_kind = self.get_cooldown_error_kind(candidate.provider)
        if error_kind is None:
            return CooldownDecision(action="attempt", error_kind=ErrorKind.UNKNOWN)

        if error_kind in PERSISTENT_ERRORS:
            return CooldownDecision(
                action="skip",
                error_kind=error_kind,
                reason=f"Provider {candidate.provider} has {error_kind.value} issue",
            )

        should_probe = self.should_probe_primary(
            candidate.provider,
            is_primary=is_primary,
            has_fallback=has_fallback,
        )

        if is_primary and should_probe:
            return CooldownDecision(
                action="attempt", error_kind=error_kind, mark_probe=True
            )

        if not is_primary and error_kind == ErrorKind.RATE_LIMIT:
            return CooldownDecision(action="attempt", error_kind=error_kind)

        return CooldownDecision(
            action="skip",
            error_kind=error_kind,
            reason=f"Provider {candidate.provider} in cooldown (all profiles unavailable)",
        )

    def clear(self) -> None:
        """Reset all state."""
        self._cooldowns.clear()
        self._last_probe.clear()


@dataclass
class _CooldownEntry:
    expires_at: float
    error_kind: ErrorKind


@dataclass
class CooldownDecision:
    action: str  # "attempt" or "skip"
    error_kind: ErrorKind = ErrorKind.UNKNOWN
    reason: str = ""
    mark_probe: bool = False


# --- Error Classification Functions ---


# PURPOSE: Classify exceptions into ErrorKind for fallback decisions
def classify_error(err: BaseException) -> ErrorKind:
    """Classify an exception into an ErrorKind.

    Override this for custom error classification in your LLM client.
    """
    if isinstance(err, ContextOverflowError):
        return ErrorKind.CONTEXT_OVERFLOW

    if isinstance(err, (asyncio.CancelledError, KeyboardInterrupt)):
        return ErrorKind.ABORT

    msg = str(err).lower()
    status = getattr(err, "status", None) or getattr(err, "status_code", None)

    # Status-based classification
    if status == 429:
        return ErrorKind.RATE_LIMIT
    if status in (401, 403):
        if "billing" in msg or "payment" in msg or "quota" in msg:
            return ErrorKind.BILLING
        return ErrorKind.AUTH
    if status == 402:
        return ErrorKind.BILLING

    # Message-based fallback
    if "rate limit" in msg or "too many requests" in msg:
        return ErrorKind.RATE_LIMIT
    if "context" in msg and ("overflow" in msg or "too long" in msg or "exceed" in msg):
        return ErrorKind.CONTEXT_OVERFLOW
    if "timeout" in msg or isinstance(err, asyncio.TimeoutError):
        return ErrorKind.TIMEOUT
    if "unauthorized" in msg or "forbidden" in msg:
        return ErrorKind.AUTH
    if "billing" in msg or "payment" in msg:
        return ErrorKind.BILLING

    return ErrorKind.UNKNOWN


# --- Candidate Chain Builder ---


# PURPOSE: Build deduplicated candidate list from config
def build_candidate_chain(
    primary: ModelCandidate,
    fallbacks: list[ModelCandidate] | None = None,
    config_default: ModelCandidate | None = None,
) -> list[ModelCandidate]:
    """Build a deduplicated, ordered candidate chain.

    Order: primary → explicit fallbacks → config default
    Dedup: uses dict.fromkeys for order-preserving uniqueness.
    """
    candidates: list[ModelCandidate] = [primary]
    if fallbacks:
        candidates.extend(fallbacks)
    if config_default and config_default != primary:
        candidates.append(config_default)
    # Deduplicate preserving order
    seen: set[str] = set()
    result: list[ModelCandidate] = []
    for c in candidates:
        if c.key not in seen:
            seen.add(c.key)
            result.append(c)
    return result


# --- Main Fallback Loop ---


# PURPOSE: Execute an async operation with model fallback
async def run_with_model_fallback(
    candidates: list[ModelCandidate],
    run: Callable[[str, str], Awaitable[T]],
    *,
    cooldown_manager: CooldownManager | None = None,
    on_error: Callable[[FallbackAttempt], Awaitable[None] | None] | None = None,
    deadline: float | None = None,
    classify: Callable[[BaseException], ErrorKind] = classify_error,
) -> FallbackResult[T]:
    """Run an async operation with automatic model fallback.

    Ported from OpenClaw runWithModelFallback (L379-511).

    Args:
        candidates: Ordered list of models to try.
        run: Async function(provider, model) → T.
        cooldown_manager: Optional cooldown state manager.
        on_error: Optional callback for each failed attempt.
        deadline: Optional total timeout in seconds for the entire loop.
        classify: Error classification function.

    Returns:
        FallbackResult with the successful result and metadata.

    Raises:
        AllCandidatesFailedError: All candidates exhausted.
        ContextOverflowError: Context window exceeded (no fallback).
        asyncio.CancelledError: Operation cancelled.
    """
    if not candidates:
        raise ValueError("No model candidates provided")

    cm = cooldown_manager or CooldownManager()
    attempts: list[FallbackAttempt] = []
    last_error: BaseException | None = None
    has_fallback = len(candidates) > 1

    async def _run_loop() -> FallbackResult[T]:
        nonlocal last_error
        for i, candidate in enumerate(candidates):
            is_primary = i == 0

            # --- Cooldown check ---
            if cm.is_in_cooldown(candidate.provider):
                decision = cm.resolve_cooldown_decision(
                    candidate, is_primary=is_primary, has_fallback=has_fallback
                )
                if decision.action == "skip":
                    attempts.append(
                        FallbackAttempt(
                            provider=candidate.provider,
                            model=candidate.model,
                            error=decision.reason,
                            error_kind=decision.error_kind,
                        )
                    )
                    logger.debug("Skipping %s: %s", candidate.key, decision.reason)
                    continue
                if decision.mark_probe:
                    cm.mark_probe(candidate.provider)
                    logger.debug("Probing cooldown-ed primary: %s", candidate.key)

            # --- Attempt execution ---
            try:
                result = await run(candidate.provider, candidate.model)
                return FallbackResult(
                    result=result,
                    provider=candidate.provider,
                    model=candidate.model,
                    attempts=attempts,
                )
            except BaseException as err:
                kind = classify(err)

                # Context overflow — never fallback to smaller model
                if kind == ErrorKind.CONTEXT_OVERFLOW:
                    raise

                # User abort — always propagate
                if kind == ErrorKind.ABORT:
                    raise

                last_error = err
                attempt = FallbackAttempt(
                    provider=candidate.provider,
                    model=candidate.model,
                    error=str(err),
                    error_kind=kind,
                    status=getattr(err, "status", None)
                    or getattr(err, "status_code", None),
                )
                attempts.append(attempt)

                # Mark cooldown for rate limits and auth errors
                if kind in (ErrorKind.RATE_LIMIT, *PERSISTENT_ERRORS):
                    cm.mark_cooldown(candidate.provider, error_kind=kind)

                # Unknown error on last candidate — propagate original
                if kind == ErrorKind.UNKNOWN and i == len(candidates) - 1:
                    raise

                if on_error:
                    cb_result = on_error(attempt)
                    if asyncio.iscoroutine(cb_result):
                        await cb_result

                logger.warning(
                    "Fallback attempt %d/%d failed: %s (%s)",
                    i + 1,
                    len(candidates),
                    candidate.key,
                    kind.value,
                )

        # All candidates exhausted
        raise AllCandidatesFailedError(attempts)

    if deadline is not None and deadline > 0:
        async with asyncio.timeout(deadline):
            return await _run_loop()
    else:
        return await _run_loop()


# PURPOSE: Synchronous version of run_with_model_fallback for sync callers (e.g. OchemaService.ask)
def run_with_model_fallback_sync(
    candidates: list[ModelCandidate],
    run: Callable[[str, str], T],
    *,
    cooldown_manager: CooldownManager | None = None,
    on_error: Callable[[FallbackAttempt], None] | None = None,
    deadline: float | None = None,
    classify: Callable[[BaseException], ErrorKind] = classify_error,
) -> FallbackResult[T]:
    """Run a synchronous operation with automatic model fallback.

    Synchronous mirror of run_with_model_fallback for use in sync contexts
    (e.g. OchemaService.ask). Same logic, no async/await.

    Args:
        candidates: Ordered list of models to try.
        run: Sync function(provider, model) → T.
        cooldown_manager: Optional cooldown state manager.
        on_error: Optional callback for each failed attempt.
        deadline: Optional absolute monotonic deadline for the entire loop.
        classify: Error classification function.

    Returns:
        FallbackResult with the successful result and metadata.

    Raises:
        AllCandidatesFailedError: All candidates exhausted.
        ContextOverflowError: Context window exceeded (no fallback).
        TimeoutError: Deadline exceeded.
    """
    if not candidates:
        raise ValueError("No model candidates provided")

    cm = cooldown_manager or CooldownManager()
    attempts: list[FallbackAttempt] = []
    has_fallback = len(candidates) > 1

    for i, candidate in enumerate(candidates):
        # --- Deadline check ---
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError(
                f"Model fallback deadline exceeded after {len(attempts)} attempts"
            )

        is_primary = i == 0

        # --- Cooldown check ---
        if cm.is_in_cooldown(candidate.provider):
            decision = cm.resolve_cooldown_decision(
                candidate, is_primary=is_primary, has_fallback=has_fallback
            )
            if decision.action == "skip":
                attempts.append(
                    FallbackAttempt(
                        provider=candidate.provider,
                        model=candidate.model,
                        error=decision.reason,
                        error_kind=decision.error_kind,
                    )
                )
                logger.debug("Skipping %s: %s", candidate.key, decision.reason)
                continue
            if decision.mark_probe:
                cm.mark_probe(candidate.provider)
                logger.debug("Probing cooldown-ed primary: %s", candidate.key)

        # --- Attempt execution ---
        try:
            result = run(candidate.provider, candidate.model)
            return FallbackResult(
                result=result,
                provider=candidate.provider,
                model=candidate.model,
                attempts=attempts,
            )
        except BaseException as err:
            kind = classify(err)

            # Context overflow — never fallback to smaller model
            if kind == ErrorKind.CONTEXT_OVERFLOW:
                raise

            # User abort — always propagate
            if kind == ErrorKind.ABORT:
                raise

            attempt = FallbackAttempt(
                provider=candidate.provider,
                model=candidate.model,
                error=str(err),
                error_kind=kind,
                status=getattr(err, "status", None)
                or getattr(err, "status_code", None),
            )
            attempts.append(attempt)

            # Mark cooldown for rate limits and auth errors
            if kind in (ErrorKind.RATE_LIMIT, *PERSISTENT_ERRORS):
                cm.mark_cooldown(candidate.provider, error_kind=kind)

            # Unknown error on last candidate — propagate original
            if kind == ErrorKind.UNKNOWN and i == len(candidates) - 1:
                raise

            if on_error:
                on_error(attempt)

            logger.warning(
                "Fallback attempt %d/%d failed: %s (%s)",
                i + 1,
                len(candidates),
                candidate.key,
                kind.value,
            )

    # All candidates exhausted
    raise AllCandidatesFailedError(attempts)
