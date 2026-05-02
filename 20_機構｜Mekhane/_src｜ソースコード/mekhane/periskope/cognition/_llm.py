from __future__ import annotations
# PROOF: mekhane/periskope/cognition/_llm.py
# PURPOSE: periskope モジュールの _llm
"""
Shared LLM helper for Periskopē cognitive phases (Φ1-Φ7).

All Φ modules use this centralized function instead of duplicating
the OchemaService interaction pattern.

Account rotation: Uses account_router to distribute requests across
multiple Cortex API accounts via round-robin, preventing 429 rate limits.
"""


import logging
from mekhane.ochema.model_defaults import FLASH

logger = logging.getLogger(__name__)


async def llm_ask(
    prompt: str,
    model: str = "gemini-3.1-pro-preview",
    max_tokens: int = 256,
    timeout: float = 120.0,
    pipeline: str = "periskope",
) -> str:
    """Lightweight LLM call via OchemaService with account rotation.

    Shared across all Φ modules. Centralizes error handling,
    model configuration, and account rotation for rate-limit resilience.

    If the primary model returns 403 PERMISSION_DENIED (e.g. non-default
    account lacks Pro access), automatically falls back to gemini-3-flash-preview.

    Args:
        prompt: The prompt to send.
        model: Model identifier (default: gemini-3.1-pro-preview).
        max_tokens: Maximum output tokens.
        timeout: Request timeout in seconds (default: 120).
        pipeline: Pipeline name for account routing (default: periskope).

    Returns:
        Response text, or empty string on failure.
    """
    _FALLBACK_MODEL = FLASH

    try:
        from mekhane.ochema.account_router import get_account_for
        from mekhane.ochema.service import OchemaService

        account = get_account_for(pipeline)
        svc = OchemaService.get()
        logger.debug("Φ llm_ask: model=%s, account=%s", model, account)

        try:
            response = await svc.ask_async(
                prompt, model=model, max_tokens=max_tokens,
                timeout=timeout, account=account,
            )
            return response.text
        except Exception as primary_err:  # noqa: BLE001
            err_str = str(primary_err)
            # 403 PERMISSION_DENIED → fallback to Flash model
            if ("403" in err_str or "PERMISSION_DENIED" in err_str) and model != _FALLBACK_MODEL:
                logger.warning(
                    "Φ llm_ask: %s returned 403 for account=%s, "
                    "falling back to %s",
                    model, account, _FALLBACK_MODEL,
                )
                response = await svc.ask_async(
                    prompt, model=_FALLBACK_MODEL, max_tokens=max_tokens,
                    timeout=timeout, account=account,
                )
                return response.text
            raise  # re-raise if not a 403 or already on fallback
    except Exception as e:  # noqa: BLE001
        logger.warning("Φ llm_ask failed (model=%s): %s", model, e)
        return ""

