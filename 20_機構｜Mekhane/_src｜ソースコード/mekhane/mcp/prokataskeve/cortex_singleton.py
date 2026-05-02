from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/prokataskeve/cortex_singleton.py
"""
Shared CortexClient singleton for Prokataskeuē modules.

PURPOSE: Avoid creating a new CortexClient on every pre-processing call.
6 modules (intent_classifier, query_transformer, hypothesis_generator,
consistency_checker, predictor, diversify_query) all need Gemini Flash.
A shared singleton reduces initialization overhead and prevents the
"QueryExpander hang" caused by repeated auth chain setup.

FEP: Akribeia (A×Mi) — precise resource allocation at micro scale.
"""

import logging
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mekhane.ochema.cortex_client import CortexClient

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_client: CortexClient | None = None

# Default configuration for pre-processing LLM calls
_DEFAULT_MODEL = "gemini-3-flash-preview"
_DEFAULT_MAX_TOKENS = 512
_DEFAULT_TIMEOUT = 5.0


# PURPOSE: Get or create a shared CortexClient for Prokataskeuē
def get_cortex(
    model: str = _DEFAULT_MODEL,
    max_tokens: int = _DEFAULT_MAX_TOKENS,
    timeout: float = _DEFAULT_TIMEOUT,
) -> CortexClient | None:
    """Get or create a shared CortexClient with timeout guard.

    Returns None if CortexClient cannot be initialized (graceful degradation).
    Thread-safe via lock.

    Args:
        model: Gemini model name (default: gemini-3-flash-preview).
        max_tokens: Maximum output tokens.
        timeout: Default timeout for API calls.

    Returns:
        Shared CortexClient instance, or None on initialization failure.
    """
    global _client  # noqa: PLW0603
    if _client is not None:
        return _client

    with _lock:
        # Double-checked locking
        if _client is not None:
            return _client

        try:
            from mekhane.ochema.cortex_client import CortexClient as _CC

            try:
                from mekhane.ochema.account_router import get_account_for
                account = get_account_for("prokataskeve")
            except Exception:  # noqa: BLE001
                account = "default"

            _client = _CC(
                model=model,
                max_tokens=max_tokens,
                account=account,
            )
            logger.debug("CortexClient singleton initialized (model=%s, account=%s)", model, account)
            return _client

        except Exception as e:  # noqa: BLE001
            logger.warning("CortexClient singleton init failed: %s", e)
            return None


# PURPOSE: Reset singleton (for testing)
def reset_cortex() -> None:
    """Reset the shared CortexClient singleton. For testing only."""
    global _client  # noqa: PLW0603
    with _lock:
        _client = None
