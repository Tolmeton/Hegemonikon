# PROOF: [L2/インフラ] <- mekhane/ochema/cortex_client.py A0→外部LLM接続→Cortex API 直叩きクライアント
# PURPOSE: Cortex API (cloudcode-pa v1internal) を LS 非経由で呼び出す Python クライアント
"""CortexClient — Gemini API direct access via cloudcode-pa v1internal.

Bypasses the Language Server to call Gemini models directly.
Returns the LLMResponse type for unified interface.

Reference: kernel/doxa/DX-010_ide_hack_cortex_direct_access.md
    - §J: Three-layer auth (OAuth + apiKey + dynamic projectId)
    - §K: AI Ultra Quota structure (Premium pool, 5h reset, 20% increments)

Usage:
    from mekhane.ochema import CortexClient

    client = CortexClient()
    response = client.ask("Hello")
    print(response.text)

    # Batch for CCL pipeline
    results = client.ask_batch([
        {"prompt": "Analyze...", "model": "gemini-3.1-pro-preview"},
        {"prompt": "Review...", "model": "gemini-3.1-pro-preview"},
    ])

    # Quota check
    quota = client.retrieve_quota()
"""

from __future__ import annotations
from typing import Any, Generator, Optional
import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Dict

from mekhane.ochema.types import LLMResponse
from mekhane.ochema.cortex_auth import CortexAuth, AUTH_LAYERS  # noqa: F401 — re-export
from mekhane.ochema.cortex_chat import CortexChat, ChatConversation  # noqa: F401 — re-export
from mekhane.ochema.cortex_tools import CortexTools  # noqa: F401 — re-export
from mekhane.ochema.model_defaults import (
    DEFAULT, MODEL_FALLBACK_CHAIN,
    CIRCUIT_BREAKER_TIMEOUT, CIRCUIT_BREAKER_TIMEOUT_STREAM,
)

logger = logging.getLogger(__name__)

# --- Constants ---

# Auth constants moved to cortex_auth.py
# Re-import for backward compatibility
from mekhane.ochema.cortex_auth import (
    _TOKEN_CACHE,
)  # noqa: F401
from mekhane.ochema.cortex_api import CortexAPI, _BASE_URL, THINKING_REDACTED_FIELD, THINKING_SIGNATURE_FIELD  # noqa: F401

# Defaults
DEFAULT_MODEL = DEFAULT
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 8192
MAX_RETRIES = 3
BACKOFF_BASE = 1.0  # seconds

# ─── Pre-flight Avoidance Cache ─────────────────────────────
# Tracks models that recently returned CAPACITY_EXHAUSTED.
# Key: model name, Value: monotonic timestamp when cooldown expires.
# Shared across all CortexClient instances within the same process.
_EXHAUSTED_CACHE: dict[str, float] = {}
_EXHAUSTED_COOLDOWN = 60.0  # seconds

def _is_model_exhausted(model: str) -> bool:
    """Check if a model is known to be capacity-exhausted (pre-flight)."""
    expires = _EXHAUSTED_CACHE.get(model)
    if expires is None:
        return False
    if time.monotonic() > expires:
        del _EXHAUSTED_CACHE[model]
        return False
    return True

def _mark_model_exhausted(model: str, cooldown: float = _EXHAUSTED_COOLDOWN) -> None:
    """Mark a model as capacity-exhausted for `cooldown` seconds."""
    _EXHAUSTED_CACHE[model] = time.monotonic() + cooldown
    logger.info(
        "Pre-flight: marked %s as exhausted for %.0fs",
        model, cooldown,
    )

# --- DX-010 §K: AI Ultra Quota Structure ---
# Premium pool resets every 5 hours; quotas are reported in 20% increments.
# Premium models (Claude, GPT-OSS) share a separate pool from Gemini.
QUOTA_RESET_INTERVAL_HOURS = 5
QUOTA_INCREMENT_PCT = 20
PREMIUM_MODEL_PREFIXES = ("claude", "gpt", "o1", "o3", "o4-mini")


# --- Exceptions ---


# PURPOSE: Cortex API 固有のエラーを他の例外と区別する
class CortexError(Exception):
    """Cortex API error."""

    pass


# PURPOSE: OAuth 認証の未完了を検出し、ユーザーに gemini-cli 認証を促す
class CortexAuthError(CortexError):
    """Authentication error — gemini-cli OAuth required."""

    pass


# PURPOSE: API レート制限や一時的エラーを区別し、リトライ戦略を適用する
class CortexAPIError(CortexError):
    """API call error with status code."""

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(self, message: str, status_code: int = 0, response_body: str = "", error_reason: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.error_reason = error_reason  # "CAPACITY_EXHAUSTED", "RATE_LIMIT", or ""

    # PURPOSE: [L2-auto] __str__ の関数定義
    def __str__(self) -> str:
        return f"{super().__str__()} (Body: {self.response_body})"


# --- Client ---


# PURPOSE: Cortex API (cloudcode-pa v1internal) を LS 非経由で呼び出し、
#   LLMResponse を返す統一インターフェースを提供する
# PURPOSE: [L2-auto] CortexClient のクラス定義
class CortexClient:
    """Cortex API direct client — bypasses Language Server.

    Provides the ask() → LLMResponse interface for Cortex API,
    enabling transparent model switching between LS-proxied and direct access.

    Key features:
        - Token caching (55 min TTL, shared with cortex.sh)
        - Auto project ID retrieval via loadCodeAssist
        - Retry with exponential backoff
        - Zero external dependencies (urllib.request only)
        - CCL pipeline support via ask_batch()
    """

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        account: str = "default",
        cooldown_manager: Optional[Any] = None,
    ):
        """Initialize with default generation parameters.

        Args:
            model: Default model (gemini-3-flash-preview, gemini-2.5-pro,
                   gemini-3.1-pro-preview, etc.)
            temperature: Default temperature (0.0-2.0)
            max_tokens: Default max output tokens
            account: TokenVault account name for multi-account support
            cooldown_manager: Optional shared CooldownManager instance
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        self._account = account
        self._auth = CortexAuth(account=account, cooldown_manager=cooldown_manager)
        self._api = CortexAPI(self._auth)
        self._chat = CortexChat(self._auth, self._api)
        self._tools = CortexTools(self._api)

    # Models that only work via generateChat (not generateContent/stream).
    # Dynamically populated: when generateContent returns 404 or ILLEGAL_MODEL_CONFIG,
    # the model is added here automatically (see ask() L256, ask_stream() L522).
    # NOTE: 2026-02-23 テストで gemini-3.1-pro-preview は generateContent 200 OK を確認。
    #   Google が後から対応を追加した。ハードコードは誤った制限を生むため空にする。
    _chat_only_cache: set[str] = set()

    # DX-010 v19.0 §N.10: Claude models via REST generateChat are FALSE POSITIVE.
    # cloudcode-pa echoes back "Claude Sonnet 4.6" in model field but actual
    # inference is Gemini fallback. Claude is ONLY reachable via LS ConnectRPC.
    _CLAUDE_PREFIXES = ("claude", "MODEL_PLACEHOLDER_M35", "MODEL_PLACEHOLDER_M26", "MODEL_CLAUDE")

    # Unset proxy env vars (mitmproxy remnant avoidance)
    for var in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy"):
            os.environ.pop(var, None)

    @property
    def vault(self) -> "TokenVault":
        """Get or create TokenVault instance (delegated to CortexAuth)."""
        return self._auth.vault

    @property
    def _current_account(self) -> str:
        """Currently active account (delegated to CortexAuth)."""
        return self._auth.account

    # --- Public API ---

    # PURPOSE: 統一シグネチャで LLM を呼び出し、
    #   呼び出し側が LS 経由か直叩きかを意識しない統一 IF を実現する
    # PURPOSE: [L2-auto] ask の関数定義
    def ask(
        self,
        message: str,
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        response_schema: Optional[Dict[str, Any]] = None,
        timeout: float = 120.0,
        response_model: Optional[Any] = None,
    ) -> LLMResponse:
        """Send a prompt and get a response.

        Args:
            message: The prompt text
            model: Model override (default: instance model)
            system_instruction: Optional system prompt
            temperature: Temperature override
            max_tokens: Max output tokens override
            thinking_budget: Thinking budget for extended thinking models
            timeout: Request timeout in seconds

        Returns:
            LLMResponse with text, model, token_usage fields populated

        Note:
            Models not yet available via generateContent (e.g. gemini-3.1-pro-preview)
            are automatically routed through generateChat instead.
        """
        model = model or self.model
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens or self.max_tokens

        # If response_model is provided, generate response_schema from Pydantic
        if response_model is not None and response_schema is None:
            try:
                # Pydantic v2
                response_schema = response_model.model_json_schema()
            except AttributeError:
                # Pydantic v1 fallback
                response_schema = response_model.schema()

        # Models only available via generateChat (not yet in generateContent)
        # Dynamically populated in self._chat_only_cache on 404 errors.
        if model in self._chat_only_cache:
            # Route directly through generateChat (DX-010 §A')
            logger.debug("Model %s: routing via generateChat (cached)", model)
            if temperature is not None:
                logger.debug("Model %s: ignoring temperature (not supported by generateChat)", model)
            return self.chat(
                message=message,
                model=model,
                system_instruction=system_instruction,
                timeout=timeout,
            )

        request_body = self._api._build_request(
            contents=[{"role": "user", "parts": [{"text": message}]}],
            model=model,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking_budget=thinking_budget,
            response_schema=response_schema,
        )

        # Circuit Breaker: absolute deadline across retries + fallbacks
        deadline = time.monotonic() + CIRCUIT_BREAKER_TIMEOUT

        # ─── Pre-flight Avoidance ─────────────────────────────
        # If this model is known-exhausted, skip HTTP entirely → jump to fallback
        if _is_model_exhausted(model):
            fallbacks = MODEL_FALLBACK_CHAIN.get(model, [])
            if fallbacks:
                fb_model = fallbacks[0]
                logger.info(
                    "Pre-flight: %s is exhausted, routing directly to %s",
                    model, fb_model,
                )
                remaining = deadline - time.monotonic()
                result = self.ask(
                    message=message,
                    model=fb_model,
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    thinking_budget=thinking_budget,
                    response_schema=response_schema,
                    timeout=min(timeout, remaining) if remaining > 0 else timeout,
                )
                result.fallback_from = model  # type: ignore[attr-defined]
                result.fallback_to = fb_model  # type: ignore[attr-defined]
                return result
            # No fallback available — proceed normally (model may have recovered)

        try:
            response = self._api._call_api(
                f"{_BASE_URL}:generateContent",
                request_body,
                timeout=timeout,
                _deadline=deadline,
            )
        except CortexAPIError as e:
            if e.status_code == 404:
                # Model not available via generateContent — fallback to generateChat
                logger.info(
                    "Model %s returned 404 on generateContent, "
                    "falling back to generateChat and caching as chat-only",
                    model,
                )
                self._chat_only_cache.add(model)
                if temperature is not None:
                    logger.debug("Model %s: ignoring temperature (not supported by generateChat)", model)
                return self.chat(
                    message=message,
                    model=model,
                    system_instruction=system_instruction,
                    timeout=timeout,
                )
            # MODEL_CAPACITY_EXHAUSTED: mark + try fallback models
            if e.status_code == 429 and getattr(e, 'error_reason', '') == 'CAPACITY_EXHAUSTED':
                _mark_model_exhausted(model)  # Pre-flight: remember for next call
                fallbacks = MODEL_FALLBACK_CHAIN.get(model, [])
                if fallbacks:
                    for fb_model in fallbacks:
                        # Circuit Breaker: check deadline before fallback attempt
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            logger.warning(
                                "Circuit breaker: deadline exceeded, skipping fallback to %s",
                                fb_model,
                            )
                            break
                        logger.warning(
                            "CAPACITY_EXHAUSTED on %s → trying fallback %s (%.1fs remaining)",
                            model, fb_model, remaining,
                        )
                        try:
                            result = self.ask(
                                message=message,
                                model=fb_model,
                                system_instruction=system_instruction,
                                temperature=temperature,
                                max_tokens=max_tokens,
                                thinking_budget=thinking_budget,
                                response_schema=response_schema,
                                timeout=min(timeout, remaining),
                            )
                            # Tag the response so caller knows fallback was used
                            result.fallback_from = model  # type: ignore[attr-defined]
                            result.fallback_to = fb_model  # type: ignore[attr-defined]
                            return result
                        except CortexAPIError:
                            continue  # try next in chain
                # All fallbacks failed or no chain defined
            raise

        return self._api._parse_response(response)

    # PURPOSE: CCL パイプラインや Specialist Reviews で複数プロンプトを
    #   順次処理し、一括で結果を返す
    # PURPOSE: [L2-auto] ask_batch の関数定義
    def ask_batch(
        self,
        tasks: list[dict[str, Any]],
        default_model: Optional[str] = None,
        default_system_instruction: Optional[str] = None,
        delay: float = 0.5,
    ) -> list[LLMResponse]:
        """Process multiple prompts sequentially.

        Args:
            tasks: List of dicts with 'prompt' (required) and optional
                   'model', 'system_instruction', 'temperature',
                   'max_tokens', 'thinking_budget'
            default_model: Default model for all tasks
            default_system_instruction: Default system instruction
            delay: Delay between requests (rate limit safety)

        Returns:
            List of LLMResponse, one per task
        """
        results: list[LLMResponse] = []
        model = default_model or self.model

        for i, task in enumerate(tasks):
            if i > 0 and delay > 0:
                time.sleep(delay)

            try:
                response = self.ask(
                    message=task["prompt"],
                    model=task.get("model", model),
                    system_instruction=task.get(
                        "system_instruction", default_system_instruction
                    ),
                    temperature=task.get("temperature"),
                    max_tokens=task.get("max_tokens"),
                    thinking_budget=task.get("thinking_budget"),
                )
                results.append(response)
            except CortexError as e:
                logger.error("Batch task %d/%d failed: %s", i + 1, len(tasks), e)
                results.append(
                    LLMResponse(
                        text=f"[ERROR] {e}",
                        model=task.get("model", model),
                    )
                )

        return results

    # PURPOSE: 非同期版の ask() — asyncio イベントループから呼び出し可能
    async def ask_async(
        self,
        message: str,
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        timeout: float = 120.0,
        response_model: Optional[Any] = None,
    ) -> LLMResponse:
        """Async version of ask() — runs sync code in thread pool.

        Thread-safe: each call runs in its own thread via ThreadPoolExecutor.

        Args:
            (same as ask())

        Returns:
            LLMResponse
        """
        import asyncio
        import concurrent.futures

        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return await loop.run_in_executor(
                pool,
                lambda: self.ask(
                    message=message,
                    model=model,
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    thinking_budget=thinking_budget,
                    timeout=timeout,
                    response_model=response_model,
                ),
            )

    # PURPOSE: 複数プロンプトを並行処理し、逐次版 ask_batch() 比で大幅高速化する
    async def ask_batch_async(
        self,
        tasks: list[dict[str, Any]],
        default_model: Optional[str] = None,
        default_system_instruction: Optional[str] = None,
        max_concurrency: int = 5,
    ) -> list[LLMResponse]:
        """Process multiple prompts concurrently.

        Uses asyncio.Semaphore for rate-limit-safe concurrency control.
        Default max_concurrency=5 keeps well within Cortex rate limits.

        Args:
            tasks: List of dicts with 'prompt' (required) and optional
                   'model', 'system_instruction', 'temperature',
                   'max_tokens', 'thinking_budget'
            default_model: Default model for all tasks
            default_system_instruction: Default system instruction
            max_concurrency: Max concurrent requests (default: 5)

        Returns:
            List of LLMResponse in same order as tasks
        """
        import asyncio

        model = default_model or self.model
        semaphore = asyncio.Semaphore(max_concurrency)

        # PURPOSE: [L2-auto] _run_one の非同期処理定義
        async def _run_one(task: dict[str, Any]) -> LLMResponse:
            async with semaphore:
                try:
                    return await self.ask_async(
                        message=task["prompt"],
                        model=task.get("model", model),
                        system_instruction=task.get(
                            "system_instruction", default_system_instruction
                        ),
                        temperature=task.get("temperature"),
                        max_tokens=task.get("max_tokens"),
                        thinking_budget=task.get("thinking_budget"),
                    )
                except CortexError as e:
                    logger.error("Async batch task failed: %s", e)
                    return LLMResponse(
                        text=f"[ERROR] {e}",
                        model=task.get("model", model),
                    )

        return list(await asyncio.gather(*[_run_one(t) for t in tasks]))

    # PURPOSE: ストリーミング応答を yield で返し、対話的 CLI やリアルタイム表示に対応する
    def ask_stream(
        self,
        message: str = "",
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        timeout: float = 120.0,
        contents: Optional[list[dict]] = None,
    ) -> Generator[str, None, None]:
        """Stream a response token by token.

        Yields text chunks as they arrive via SSE.
        Falls back to chat_stream for models not available via generateContent.

        Args:
            message: User message (used if contents is None)
            contents: Multi-turn history format (overrides message)
            ... (other same as ask())

        Yields:
            str: Text chunks from the response
        """
        model = model or self.model
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens or self.max_tokens

        # Models only available via generateChat — route to chat_stream
        if model in self._chat_only_cache:
            logger.debug("ask_stream: model %s routed via chat_stream (cached)", model)
            # chat_stream currently does not support raw contents well, just pass message for fallback
            yield from self.chat_stream(
                message=message or str(contents),
                model=model,
                timeout=timeout,
            )
            return

        final_contents = contents or [{"role": "user", "parts": [{"text": message}]}]

        request_body = self._api._build_request(
            contents=final_contents,
            model=model,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking_budget=thinking_budget,
        )

        # Circuit Breaker: absolute deadline across retries + fallbacks
        deadline = time.monotonic() + CIRCUIT_BREAKER_TIMEOUT_STREAM

        # ─── Pre-flight Avoidance ─────────────────────────────
        if _is_model_exhausted(model):
            fallbacks = MODEL_FALLBACK_CHAIN.get(model, [])
            if fallbacks:
                fb_model = fallbacks[0]
                logger.info(
                    "ask_stream Pre-flight: %s is exhausted, routing directly to %s",
                    model, fb_model,
                )
                fb_remaining = deadline - time.monotonic()
                yield from self.ask_stream(
                    message=message,
                    model=fb_model,
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    thinking_budget=thinking_budget,
                    timeout=min(timeout, fb_remaining) if fb_remaining > 0 else timeout,
                    contents=contents,
                )
                return
            # No fallbacks — proceed normally

        for attempt in range(2):
            # Circuit Breaker: check deadline before attempt
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CortexAPIError(
                    "ask_stream circuit breaker: total timeout exceeded",
                    status_code=0,
                    error_reason="CIRCUIT_BREAKER",
                )
            req_timeout = min(timeout, remaining)

            token = self._get_token()
            project = self._api._get_project(token)
            request_body["project"] = project
    
            url = f"{_BASE_URL}:streamGenerateContent?alt=sse"
            data = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
    
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
                with urllib.request.urlopen(req, timeout=req_timeout) as resp:
                    for line_bytes in resp:
                        line = line_bytes.decode("utf-8").strip()
                        if line.startswith("data: "):
                            try:
                                d = json.loads(line[6:])
                                # --- Energy Budget Tracking ---
                                usage: dict[str, Any] = d.get("usageMetadata") or {}
                                if usage:
                                    try:
                                        acct = getattr(self, "_current_account", getattr(self, "_account", "default"))
                                        p_tok = usage.get("promptTokenCount", 0)
                                        c_tok = usage.get("candidatesTokenCount", 0)
                                        self.vault.record_usage(acct, model, p_tok, c_tok)
                                    except Exception as e:  # noqa: BLE001
                                        logger.debug("Failed to record usage: %s", e)
                                # ------------------------------
                                candidates = (
                                    d.get("response", {}).get("candidates", [{}])
                                )
                                for candidate in candidates:
                                    parts = (
                                        candidate.get("content", {}).get("parts", [])
                                    )
                                    for part in parts:
                                        if part.get("thought"):
                                            # Thinking chunk — prefix for separation
                                            if "text" in part:
                                                yield f"__THINKING__:{part['text']}"
                                        elif "text" in part:
                                            yield part["text"]
                            except json.JSONDecodeError:
                                continue
                return
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                if e.code in (401, 403) and attempt == 0:
                    logger.warning("ask_stream: Token expired (401), clearing cache and retrying...")
                    self._auth._token = None
                    if _TOKEN_CACHE.exists():
                        _TOKEN_CACHE.unlink()
                    continue

                # 429 CAPACITY_EXHAUSTED: model fallback (same pattern as ask())
                if e.code == 429:
                    from mekhane.ochema.cortex_api import _extract_429_reason
                    reason = _extract_429_reason(err_body)
                    if reason == "CAPACITY_EXHAUSTED":
                        _mark_model_exhausted(model)  # Pre-flight: remember for next call
                        fallbacks = MODEL_FALLBACK_CHAIN.get(model, [])
                        for fb_model in fallbacks:
                            # Circuit Breaker: check deadline before fallback
                            fb_remaining = deadline - time.monotonic()
                            if fb_remaining <= 0:
                                logger.warning(
                                    "ask_stream circuit breaker: deadline exceeded, "
                                    "skipping fallback to %s", fb_model,
                                )
                                break
                            logger.warning(
                                "ask_stream: CAPACITY_EXHAUSTED on %s → trying fallback %s "
                                "(%.1fs remaining)",
                                model, fb_model, fb_remaining,
                            )
                            try:
                                yield from self.ask_stream(
                                    message=message,
                                    model=fb_model,
                                    system_instruction=system_instruction,
                                    temperature=temperature,
                                    max_tokens=max_tokens,
                                    thinking_budget=thinking_budget,
                                    timeout=min(timeout, fb_remaining),
                                    contents=contents,
                                )
                                return  # fallback succeeded
                            except (CortexAPIError, urllib.error.HTTPError):
                                continue  # try next in chain
                        # All fallbacks failed — raise original error
                    # RATE_LIMIT or all fallbacks failed — raise
                    raise CortexAPIError(
                        f"Stream failed: {e.code} {e.reason}",
                        status_code=e.code,
                        response_body=err_body,
                        error_reason=reason,
                    )

                if e.code == 404 or (e.code == 400 and "ILLEGAL_MODEL_CONFIG" in err_body):
                    # Model not available via streamGenerateContent — fallback
                    logger.info(
                        "ask_stream: model %s returned %d, falling back to chat_stream",
                        model,
                        e.code,
                    )
                    self._chat_only_cache.add(model)

                    # Convert contents back to message/history for chat_stream if needed
                    fallback_msg = message
                    fallback_hist = None
                    if not fallback_msg and contents:
                        # contents is like [{"role": "user", "parts": [{"text": "Hello"}]}, ...]
                        fallback_hist = []
                        for c in contents[:-1]:
                            author = 1 if c.get("role") == "user" else 2
                            text = "".join(p.get("text", "") for p in c.get("parts", []))
                            fallback_hist.append({"author": author, "content": text})
                        
                        last_c = contents[-1]
                        fallback_msg = "".join(p.get("text", "") for p in last_c.get("parts", []))

                    yield from self.chat_stream(
                        message=fallback_msg,
                        model=model,
                        system_instruction=system_instruction,
                        history=fallback_hist,
                        timeout=timeout,
                    )
                    return
                raise CortexAPIError(
                    f"Stream failed: {e.code} {e.reason}",
                    status_code=e.code,
                    response_body=err_body,
                )

    # PURPOSE: プロジェクト情報 (tier, プロジェクト ID) を取得し、
    #   接続確認と設定把握に使う
    # PURPOSE: [L2-auto] load_code_assist の関数定義
    def load_code_assist(self) -> dict:
        """Get loadCodeAssist info (project, tier, settings).

        Returns:
            dict with cloudaicompanionProject, currentTier, paidTier, etc.
        """
        token = self._get_token()
        return self._api._call_api(
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

    # PURPOSE: 全モデルの Quota 残量を取得し、モデルルーティング判断の入力とする
    def retrieve_quota(self) -> dict:
        """Get quota info for all model buckets.

        Returns:
            dict with model quotas (12 buckets expected)
        """
        token = self._get_token()
        project = self._api._get_project(token)
        resp = self._api._call_api(
            f"{_BASE_URL}:retrieveUserQuota",
            {"project": project},
            token_override=token,
        )
        
        # Lightweight quota monitoring (F5)
        # If gemini-3.1-pro-preview appears in quota buckets, generateContent likely supports it.
        try:
            buckets = resp.get("buckets", [])
            if "gemini-3.1-pro-preview" in str(buckets):
                if "gemini-3.1-pro-preview" in self._chat_only_cache:
                    self._chat_only_cache.remove("gemini-3.1-pro-preview")
                    logger.info("Auto-detected gemini-3.1-pro-preview in quota, removed from chat-only cache")
        except Exception as e:  # noqa: BLE001
            logger.debug("Failed to parse quota for chat-only cache cleanup: %s", e)

        return resp

    @staticmethod
    def parse_quota_buckets(raw_quota: dict) -> list[dict[str, Any]]:
        """Parse raw quota response into structured bucket list.

        Applies DX-010 §K knowledge:
        - Quotas come in QUOTA_INCREMENT_PCT (20%) increments
        - Premium models are identified by PREMIUM_MODEL_PREFIXES
        - Reset interval is QUOTA_RESET_INTERVAL_HOURS (5h)

        Returns:
            List of dicts with keys: model, remaining_pct, is_premium, pool
        """
        buckets = raw_quota.get("buckets", [])
        parsed: list[dict[str, Any]] = []
        for bucket in buckets:
            model_id = bucket.get("modelId", bucket.get("id", ""))
            remaining = bucket.get("remainingRequests", bucket.get("remaining", 0))
            is_premium = any(
                model_id.lower().startswith(p) for p in PREMIUM_MODEL_PREFIXES
            )
            parsed.append({
                "model": model_id,
                "remaining_pct": remaining,
                "is_premium": is_premium,
                "pool": "premium" if is_premium else "standard",
                "reset_hours": QUOTA_RESET_INTERVAL_HOURS,
                "increment_pct": QUOTA_INCREMENT_PCT,
            })
        return parsed

    def validate_auth_chain(self) -> dict[str, bool]:
        """Validate that all three authentication layers are available.

        DX-010 §J defines three required layers:
        1. OAuth token (Layer 1)
        2. API key (embedded in requests, Layer 2)
        3. Dynamic project ID (Layer 3)

        Returns:
            Dict mapping AUTH_LAYERS names to availability status.
            All three must be True for API calls to succeed.
        """
        status: dict[str, bool] = {layer: False for layer in AUTH_LAYERS}
        try:
            token = self._get_token()
            status["oauth_token"] = bool(token)
        except Exception:  # noqa: BLE001
            pass
        # API key is embedded in requests (always True if client is constructed)
        status["api_key"] = True
        try:
            if status["oauth_token"]:
                project = self._api._get_project(self._get_token())
                status["dynamic_project_id"] = bool(project)
        except Exception:  # noqa: BLE001
            pass
        return status

    # PURPOSE: [L2-auto] retrieve_all_quotas の関数定義
    def retrieve_all_quotas(self) -> dict[str, dict]:
        """Get quota for all TokenVault accounts in parallel.

        Returns:
            Dict mapping account_name -> quota response (or error string)
        """
        import concurrent.futures

        accounts = self.vault.list_accounts()
        results: dict[str, dict] = {}

        # PURPOSE: [L2-auto] _fetch_quota の関数定義
        def _fetch_quota(acct_name: str) -> tuple[str, dict]:
            try:
                client = CortexClient(account=acct_name)
                quota = client.retrieve_quota()
                return acct_name, quota
            except Exception as e:  # noqa: BLE001
                return acct_name, {"error": str(e)}

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            futures = {
                pool.submit(_fetch_quota, a["name"]): a["name"]
                for a in accounts
            }
            for future in concurrent.futures.as_completed(futures):
                name, quota = future.result()
                results[name] = quota

        return results

    # PURPOSE: API から利用可能なモデル一覧を動的に取得する (F6)
    def fetch_available_models(self) -> list[dict[str, Any]]:
        """Fetch available model configurations from the API.

        Calls the fetchAvailableModels endpoint to discover
        which models are currently available for this account.

        Returns:
            List of model config dicts with id, displayName, etc.
            Falls back to empty list on failure.
        """
        try:
            token = self._get_token()
            project = self._api._get_project(token)
            result = self._api._call_api(
                f"{_BASE_URL}:fetchAvailableModels",
                {"project": project},
                token_override=token,
            )
            # Extract models from response (structure TBD — API未確認)
            models = result.get("models", result.get("modelConfigs", []))
            if isinstance(models, list):
                return models
            return []
        except Exception as e:  # noqa: BLE001
            logger.warning("fetchAvailableModels failed: %s", e)
            return []

    # --- Private Methods (auth delegated to CortexAuth) ---

    def _set_token(self, new_token: str) -> None:
        """Set token (delegated to CortexAuth)."""
        self._auth.set_token(new_token)

    def _get_token(self) -> str:
        """Get access token (delegated to CortexAuth)."""
        return self._auth.get_token()

    # --- API communication methods moved to CortexAPI ---
    # --- Chat methods moved to CortexChat ---

    def _parse_chat_response(
        self,
        response: dict,
        request_model: str = "",
    ) -> LLMResponse:
        """Parse generateChat response (delegated to CortexChat)."""
        return self._chat._parse_chat_response(response, request_model)

    # --- generateChat API (DX-010 §A') ---

    # --- generateChat API (delegated to CortexChat) ---

    def chat(
        self,
        message: str,
        model: str = "",
        system_instruction: str | None = None,
        history: list[dict[str, Any]] | None = None,
        tier_id: str = "",
        include_thinking: bool = True,
        thinking_budget: Optional[int] = None,
        timeout: float = 120.0,
    ) -> LLMResponse:
        """generateChat API でチャット応答を取得 (delegated to CortexChat)."""
        return self._chat.chat(
            message=message,
            model=model,
            system_instruction=system_instruction,
            history=history,
            tier_id=tier_id,
            include_thinking=include_thinking,
            thinking_budget=thinking_budget,
            timeout=timeout,
        )

    def chat_stream(
        self,
        message: str,
        model: str = "",
        system_instruction: str | None = None,
        history: list[dict[str, Any]] | None = None,
        tier_id: str = "",
        include_thinking: bool = True,
        thinking_budget: Optional[int] = None,
        timeout: float = 120.0,
    ) -> Generator[str, None, None]:
        """streamGenerateChat API でストリーミングチャット (delegated to CortexChat)."""
        yield from self._chat.chat_stream(
            message=message,
            model=model,
            system_instruction=system_instruction,
            history=history,
            tier_id=tier_id,
            include_thinking=include_thinking,
            thinking_budget=thinking_budget,
            timeout=timeout,
        )

    def start_chat(
        self,
        model: str = "",
        tier_id: str = "",
        include_thinking: bool = True,
    ) -> "ChatConversation":
        """マルチターン generateChat 会話を開始する (delegated to CortexChat)."""
        return ChatConversation(
            chat=self._chat,
            model=model,
            tier_id=tier_id,
            include_thinking=include_thinking,
            account=self._account,
            default_model=self.model,
        )

    # PURPOSE: [L2-auto] __repr__ の関数定義
    def __repr__(self) -> str:
        return f"CortexClient(model={self.model!r}, project={self._api._project!r})"

    # PURPOSE: Function Calling でローカルファイルを操作するエージェントループ。
    def ask_with_tools(
        self,
        message: str,
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        tools: Optional[list[dict]] = None,
        max_iterations: int = 10,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        timeout: float = 120.0,
        on_event: Optional[Callable[[str, dict], None]] = None,
        on_gate: Optional[Callable[[str, dict], bool]] = None,
    ) -> LLMResponse:
        """Send a prompt with tool use support (delegated to CortexTools)."""
        return self._tools.ask_with_tools(
            message=message,
            model=model or self.model,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            system_instruction=system_instruction,
            tools=tools,
            max_iterations=max_iterations,
            thinking_budget=thinking_budget,
            timeout=timeout,
            on_event=on_event,
            on_gate=on_gate,
        )


# --- ChatConversation moved to cortex_chat.py ---



# --- Convenience Functions ---


# PURPOSE: ワンライナーで Gemini API を呼べるヘルパー関数。
#   スクリプトや n8n 統合などの簡易利用向け
# PURPOSE: [L2-auto] cortex_ask の関数定義
def cortex_ask(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system_instruction: Optional[str] = None,
    thinking_budget: Optional[int] = None,
) -> str:
    """One-liner convenience function.

    Args:
        prompt: The prompt text
        model: Model name
        system_instruction: Optional system prompt
        thinking_budget: Optional thinking budget

    Returns:
        Response text (string only)
    """
    client = CortexClient(model=model)
    response = client.ask(
        prompt,
        system_instruction=system_instruction,
        thinking_budget=thinking_budget,
    )
    return response.text


# --- CLI ---

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python cortex_client.py <prompt>")
        print("       python cortex_client.py --quota")
        print("       python cortex_client.py --info")
        sys.exit(1)

    arg = sys.argv[1]

    client = CortexClient()

    if arg == "--quota":
        import pprint

        pprint.pprint(client.retrieve_quota())
    elif arg == "--info":
        import pprint

        pprint.pprint(client.load_code_assist())
    else:
        prompt = " ".join(sys.argv[1:])
        resp = client.ask(prompt)
        print(resp.text)
        if resp.token_usage:
            print(
                f"\n---\n📊 {resp.token_usage.get('prompt_tokens', '?')} in → "
                f"{resp.token_usage.get('completion_tokens', '?')} out = "
                f"{resp.token_usage.get('total_tokens', '?')} total"
            )
            print(f"📍 model: {resp.model}")
