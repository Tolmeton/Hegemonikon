from __future__ import annotations
# PROOF: mekhane/periskope/query_expander.py
# PURPOSE: periskope モジュールの query_expander
"""
Query expander for Periskopē.

W3: Expands queries by translating between Japanese and English,
enabling parallel bilingual search for broader result coverage.
Uses Cortex API (Gemini) for lightweight translation.
"""


import asyncio
import logging
import threading

logger = logging.getLogger(__name__)

# CJK Unicode ranges for Japanese detection
_CJK_RANGES = (
    ('\u3040', '\u309f'),  # Hiragana
    ('\u30a0', '\u30ff'),  # Katakana
    ('\u4e00', '\u9fff'),  # CJK Unified Ideographs
    ('\u3400', '\u4dbf'),  # CJK Extension A
)


# PURPOSE: [L2-auto] _is_japanese の関数定義
def _is_japanese(text: str) -> bool:
    """Detect if text contains Japanese characters."""
    for char in text:
        for start, end in _CJK_RANGES:
            if start <= char <= end:
                return True
    return False


# PURPOSE: [L2-auto] QueryExpander のクラス定義
class QueryExpander:
    """Expand search queries via translation and synonym generation.

    Uses CortexClient.chat() (Gemini Flash) for fast, cost-effective translation.
    Consistent with synthesizer.py — all LLM calls go through CortexClient.
    """

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(
        self,
        model: str = "gemini-3-flash-preview",
        timeout: float = 15.0,
    ) -> None:
        self.model = model
        self.timeout = timeout
        self._cortex = None

    # PURPOSE: [L2-auto] _get_cortex の関数定義
    def _get_cortex(self):
        """Lazy-load CortexClient with timeout guard."""
        if self._cortex is None:
            try:
                from mekhane.ochema.cortex_client import CortexClient
                try:
                    from mekhane.ochema.account_router import get_account_for
                    account = get_account_for("periskope")
                except Exception:  # noqa: BLE001
                    account = "default"
                self._cortex = CortexClient(
                    model=self.model,
                    max_tokens=256,
                    account=account,
                )
            except Exception as e:  # noqa: BLE001
                logger.warning("CortexClient init failed in QueryExpander: %s", e)
                self._cortex = None
        return self._cortex

    # PURPOSE: [L2-auto] expand の非同期処理定義
    async def expand(self, query: str) -> list[str]:
        """Expand query via bilingual translation.

        Args:
            query: Original search query.

        Returns:
            List of queries (original + translated).
            If translation fails, returns only the original.
        """
        queries = [query]

        try:
            if _is_japanese(query):
                targets = [("ja", "en"), ("ja", "zh")]
            else:
                targets = [("en", "ja"), ("en", "zh")]

            # Parallel translation for lower latency
            tasks = [self._translate(query, src, tgt) for src, tgt in targets]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning("Translation failed: %s", result)
                    continue
                if result and result.strip() != query.strip():
                    # D8: Translation quality guard — reject abnormal length ratios
                    ratio = len(result.strip()) / max(len(query), 1)
                    if ratio > 3.0 or ratio < 0.33:
                        logger.warning(
                            "Translation rejected (length ratio %.1f): %r → %r",
                            ratio, query, result.strip(),
                        )
                        continue
                    # F2: Round-trip verification — translate back and check overlap
                    src, tgt = targets[i]
                    try:
                        round_trip = await self._translate(result.strip(), tgt, src)
                        if round_trip:
                            # Simple word overlap check (language-agnostic)
                            orig_words = set(query.lower().split())
                            rt_words = set(round_trip.lower().split())
                            if orig_words and rt_words:
                                overlap = len(orig_words & rt_words) / max(len(orig_words), 1)
                                if overlap < 0.2:
                                    logger.warning(
                                        "Translation rejected (round-trip overlap %.0f%%): %r → %r → %r",
                                        overlap * 100, query, result.strip(), round_trip,
                                    )
                                    continue
                    except Exception:  # noqa: BLE001
                        pass  # Round-trip is best-effort; proceed if it fails
                    queries.append(result.strip())

            if len(queries) > 1:
                logger.info("Query expanded: %r → %r", query, queries[1:])
        except Exception as e:  # noqa: BLE001
            logger.warning("Query expansion failed: %s", e)

        return queries

    # PURPOSE: [L2-auto] _translate の非同期処理定義
    async def _translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> str | None:
        """Translate text using CortexClient.chat() (Gemini Flash).

        Args:
            text: Text to translate.
            source_lang: Source language code (ja, en).
            target_lang: Target language code (ja, en).

        Returns:
            Translated text, or None on failure.
        """
        lang_names = {"ja": "Japanese", "en": "English", "zh": "Chinese"}
        prompt = (
            f"Translate the following {lang_names[source_lang]} search query "
            f"to {lang_names[target_lang]}. "
            f"Return ONLY the translated text, nothing else.\n\n"
            f"{text}"
        )

        try:
            cortex = self._get_cortex()
            # CortexClient.chat() is sync — run in thread pool (same as synthesizer.py)
            response = await asyncio.to_thread(
                cortex.chat,
                message=prompt,
                model=self.model,
                timeout=self.timeout,
            )
            result = response.text
            return result.strip() if result else None

        except Exception as e:  # noqa: BLE001
            logger.debug("Translation via Cortex failed: %s", e)
            return None


# =============================================================================
# Module-level singleton
# =============================================================================

_lock = threading.Lock()
_SHARED_EXPANDER: QueryExpander | None = None


def get_expander(
    model: str = "gemini-3-flash-preview",
    timeout: float = 15.0,
) -> QueryExpander:
    """Get or create a shared QueryExpander singleton.

    Thread-safe. Reuses the same instance across calls to avoid
    repeated CortexClient initialization overhead.
    """
    global _SHARED_EXPANDER  # noqa: PLW0603
    if _SHARED_EXPANDER is not None:
        return _SHARED_EXPANDER

    with _lock:
        if _SHARED_EXPANDER is not None:
            return _SHARED_EXPANDER
        _SHARED_EXPANDER = QueryExpander(model=model, timeout=timeout)
        return _SHARED_EXPANDER
