# PROOF: [L2/インフラ] <- mekhane/ochema/cortex_api.py A0→外部LLM接続→Cortex API 通信基盤
# PURPOSE: Cortex API の低レベル HTTP 通信、リトライ、リクエスト構築、レスポンス解析を担う通信層。
"""CortexAPI — API communication layer for Cortex API.

Handles HTTP requests, retries with exponential backoff, rate limit handling,
request payload building, and response parsing.

DX-010: AI Ultra Quota handling & gRPC Thinking Stream metadata parsing.
"""
from __future__ import annotations
from typing import Any, Optional

import json
import logging
import os
import re
import time
import urllib.error
import urllib.request

from mekhane.ochema.types import LLMResponse
from mekhane.ochema.cortex_auth import CortexAuth, _TOKEN_CACHE

logger = logging.getLogger(__name__)

# --- API Constants ---
_BASE_URL = "https://cloudcode-pa.googleapis.com/v1internal"
MAX_RETRIES = 3
BACKOFF_BASE = 1.0  # seconds

# --- DX-010 §I: gRPC Thinking Stream ---
THINKING_REDACTED_FIELD = "thinkingRedacted"
THINKING_SIGNATURE_FIELD = "thinkingSignature"


# --- 429 Error Classification ---


def _extract_429_reason(body: str) -> str:
    """Extract the specific 429 reason from API response body.

    Returns:
        'CAPACITY_EXHAUSTED' if MODEL_CAPACITY_EXHAUSTED detected,
        'RATE_LIMIT' for RATE_LIMIT_EXCEEDED or other 429s,
        'UNKNOWN' if parsing fails.
    """
    try:
        data = json.loads(body)
        # Google API errors nest: {"error": {"details": [{"reason": "..."}]}}
        error = data.get("error", {})
        for detail in error.get("details", []):
            reason = detail.get("reason", "")
            if "CAPACITY" in reason.upper():
                return "CAPACITY_EXHAUSTED"
            if "RATE" in reason.upper() or "LIMIT" in reason.upper():
                return "RATE_LIMIT"
        # Also check top-level status field
        status = error.get("status", "")
        if "RESOURCE_EXHAUSTED" in status:
            # Disambiguate via message
            message = error.get("message", "")
            if "capacity" in message.lower() or "no capacity" in message.lower():
                return "CAPACITY_EXHAUSTED"
            return "RATE_LIMIT"
    except (json.JSONDecodeError, AttributeError):
        pass
    return "UNKNOWN"


class CortexAPI:
    """Low-level API communication layer for Cortex API."""

    def __init__(self, auth: CortexAuth):
        self._auth = auth
        self._project: Optional[str] = None
        # Register callback to invalidate project on token change
        self._auth._on_token_change = self._invalidate_project_cache

    def _invalidate_project_cache(self) -> None:
        """Invalidate project cache when token changes."""
        self._project = None

    def _get_project(self, token: str) -> str:
        """Get project ID via loadCodeAssist (cached)."""
        from mekhane.ochema.cortex_client import CortexError

        if self._project:
            return self._project

        # Check env override (but ignore legacy 'anthropic-ct5-web' which causes 403)
        env_project = os.environ.get("CORTEX_PROJECT")
        if env_project and env_project != "anthropic-ct5-web":
            self._project = env_project
            return self._project

        result = self._call_api(
            f"{_BASE_URL}:loadCodeAssist",
            {
                "metadata": {
                    "ideType": "IDE_UNSPECIFIED",
                    "platform": "PLATFORM_UNSPECIFIED",
                    "pluginType": "GEMINI",
                }
            },
            token_override=token,
        )

        project = result.get("cloudaicompanionProject")
        if not project:
            raise CortexError(
                f"loadCodeAssist がプロジェクト ID を返しませんでした: {result}"
            )

        self._project = project
        logger.info("Cortex project: %s", project)
        return self._project

    def _build_request(
        self,
        contents: list[dict],
        model: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 65536,
        thinking_budget: Optional[int] = None,
        tools: Optional[list[dict]] = None,
        response_schema: Optional[dict[str, Any]] = None,
    ) -> dict:
        """Build the generateContent/generateChat request payload."""
        # Ensure maxOutputTokens is strictly greater than thinkingBudget
        if thinking_budget is not None and thinking_budget >= max_tokens:
            max_tokens = thinking_budget + 4096

        request_inner: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        if response_schema:
            request_inner["generationConfig"]["responseMimeType"] = "application/json"
            request_inner["generationConfig"]["responseSchema"] = response_schema

        if system_instruction:
            request_inner["systemInstruction"] = {
                "role": "user",
                "parts": [{"text": system_instruction}],
            }

        if thinking_budget is not None:
            request_inner["generationConfig"]["thinkingConfig"] = {
                "thinkingBudget": thinking_budget
            }

        if tools:
            # Gemini API は name/description/parameters のみ受け付ける。
            # HGK 内部メタデータ (category 等) をストリップして INVALID_ARGUMENT を防ぐ。
            _ALLOWED_KEYS = {"name", "description", "parameters"}
            sanitized = [
                {k: v for k, v in t.items() if k in _ALLOWED_KEYS}
                for t in tools
            ]
            request_inner["tools"] = [{"functionDeclarations": sanitized}]

        logger.info("_build_request output payload: %s", request_inner)
        return {
            "model": model,
            "request": request_inner,
        }

    def _call_api(
        self,
        url: str,
        payload: dict,
        timeout: float = 120.0,
        token_override: Optional[str] = None,
        _deadline: Optional[float] = None,
    ) -> dict:
        """Make an API call with retry and error handling.

        Args:
            _deadline: Absolute monotonic deadline (set by caller for
                       circuit breaker). If None, no circuit breaker.
        """
        from mekhane.ochema.cortex_client import CortexAPIError, CortexError

        token = token_override or self._auth.get_token()

        # Inject project if not present and not a loadCodeAssist call
        if "project" not in payload and ":loadCodeAssist" not in url:
            payload["project"] = self._get_project(token)

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        last_error: Optional[Exception] = None
        for attempt in range(MAX_RETRIES):
            # --- Circuit Breaker: check deadline ---
            if _deadline is not None:
                remaining = _deadline - time.monotonic()
                if remaining <= 0:
                    logger.warning(
                        "Circuit breaker tripped: deadline exceeded after %d attempts",
                        attempt,
                    )
                    raise last_error or CortexError(
                        "Circuit breaker: total timeout exceeded"
                    )
                # Cap per-request timeout to remaining time
                timeout = min(timeout, remaining)

            if attempt > 0:
                sleep_time = BACKOFF_BASE * (2 ** (attempt - 1))
                # Don't sleep past the deadline
                if _deadline is not None:
                    remaining = _deadline - time.monotonic()
                    if remaining <= sleep_time:
                        logger.warning(
                            "Circuit breaker: would sleep %.1fs but only %.1fs remain",
                            sleep_time, remaining,
                        )
                        raise last_error or CortexError(
                            "Circuit breaker: total timeout exceeded"
                        )
                logger.info("Retry %d/%d after %.1fs", attempt + 1, MAX_RETRIES, sleep_time)
                time.sleep(sleep_time)

            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    result = json.loads(resp.read().decode("utf-8"))

                # Check for API-level errors in response body
                if "error" in result:
                    err = result["error"]
                    raise CortexAPIError(
                        f"API error: {json.dumps(err)}",
                        status_code=err.get("code", 0),
                        response_body=json.dumps(result),
                    )

                return result

            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                error_reason = _extract_429_reason(body) if e.code == 429 else ""
                last_error = CortexAPIError(
                    f"HTTP {e.code}: {e.reason}",
                    status_code=e.code,
                    response_body=body,
                    error_reason=error_reason,
                )
                # Don't retry auth errors
                if e.code in (401, 403):
                    # Token might be expired — clear cache and retry once
                    if attempt == 0:
                        self._auth._token = None
                        if _TOKEN_CACHE.exists():
                            _TOKEN_CACHE.unlink()
                        token = self._auth.get_token()
                        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                        continue
                    raise last_error
                # Don't retry 4xx (except 429)
                if 400 <= e.code < 500 and e.code != 429:
                    raise last_error
                # 429: smart backoff — respect API wait time + try account rotation
                if e.code == 429:
                    # Classify 429 reason for downstream CooldownManager decisions
                    _error_kind_str = "capacity" if error_reason == "CAPACITY_EXHAUSTED" else "rate_limit"
                    self._auth.vault.mark_rate_limited(
                        self._auth.account, cooldown=60, error_kind=_error_kind_str,
                    )

                    # CAPACITY_EXHAUSTED = server-level, not account-level.
                    # Account rotation won't help. Propagate to ask() for model fallback.
                    if error_reason == "CAPACITY_EXHAUSTED":
                        logger.warning(
                            "429 CAPACITY_EXHAUSTED on model (account=%s). "
                            "Propagating for model fallback.",
                            self._auth.account,
                        )
                        raise last_error

                    # RATE_LIMIT: account-level — try rotating to a different account
                    # Extract actual wait time from API response
                    wait_match = re.search(r"reset after (\d+)s", body)
                    if wait_match:
                        sleep_time = float(wait_match.group(1)) + 2  # buffer
                    else:
                        sleep_time = max(10, BACKOFF_BASE * (2 ** attempt))
                    # Try rotating to a different account
                    try:
                        alt_token, alt_acct = self._auth.vault.get_token_round_robin()
                        if alt_acct != self._auth.account:
                            self._auth._current_account = alt_acct
                            token = alt_token
                            # Clear project cache → loadCodeAssist with new token
                            self._project = None
                            # Re-resolve project for the new account
                            if ":loadCodeAssist" not in url:
                                payload["project"] = self._get_project(token)
                            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                            logger.info(
                                "429 RATE_LIMIT: rotated to account '%s' (skipping %s wait)",
                                alt_acct, f"{sleep_time:.0f}s"
                            )
                            continue  # retry immediately with new account
                    except (OSError, KeyError) as _e:
                        logger.debug("Ignored exception: %s", _e)
                        pass  # no alternate accounts, fall through to sleep
                    logger.info(
                        "429 RATE_LIMIT: waiting %.0fs before retry (account=%s)",
                        sleep_time, self._auth.account,
                    )
                    time.sleep(sleep_time)
                    continue
                logger.warning("API error (attempt %d): %s", attempt + 1, last_error)

            except urllib.error.URLError as e:
                last_error = CortexError(f"Network error: {e.reason}")
                logger.warning("Network error (attempt %d): %s", attempt + 1, e.reason)

        raise last_error or CortexError("All retries exhausted")

    def _parse_response(self, response: dict) -> LLMResponse:
        """Parse Cortex API response into LLMResponse.

        Handles text, thinking, and function call response formats.
        """
        r = response.get("response", response)

        text_parts: list[str] = []
        thinking_parts: list[str] = []
        function_calls: list[dict[str, Any]] = []
        model_version = r.get("modelVersion", "")

        thinking_redacted = False
        thinking_signature: str | None = None

        for candidate in r.get("candidates", []):
            # DX-010 §I: Detect server-enforced thinking redaction
            if candidate.get(THINKING_REDACTED_FIELD, False):
                thinking_redacted = True
                logger.debug(
                    "Thinking redacted by server (DX-010 §I: "
                    "raw_thinking unavailable, only encrypted signature)"
                )
            sig = candidate.get(THINKING_SIGNATURE_FIELD)
            if sig:
                thinking_signature = sig

            for part in candidate.get("content", {}).get("parts", []):
                if "text" in part:
                    # Thinking models put thought in a separate part with "thought": true
                    if part.get("thought"):
                        thinking_parts.append(part["text"])
                    else:
                        text_parts.append(part["text"])
                elif "functionCall" in part:
                    function_calls.append(part["functionCall"])

        usage = r.get("usageMetadata", {})
        token_usage = {}
        if usage:
            token_usage = {
                "prompt_tokens": usage.get("promptTokenCount", 0),
                "completion_tokens": usage.get("candidatesTokenCount", 0),
                "total_tokens": usage.get("totalTokenCount", 0),
            }

        result = LLMResponse(
            text="\n".join(text_parts),
            thinking="\n".join(thinking_parts),
            model=model_version,
            token_usage=token_usage,
        )
        # Attach function calls as extra attribute for agent loop
        result.function_calls = function_calls  # type: ignore[attr-defined]
        # DX-010 §I: Attach thinking redaction metadata
        result.thinking_redacted = thinking_redacted  # type: ignore[attr-defined]
        result.thinking_signature = thinking_signature  # type: ignore[attr-defined]
        # Preserve raw model parts for thought_signature (Gemini 3 requirement)
        raw_parts: list[dict[str, Any]] = []
        for candidate in r.get("candidates", []):
            raw_parts.extend(candidate.get("content", {}).get("parts", []))
        result.raw_model_parts = raw_parts  # type: ignore[attr-defined]
        return result
