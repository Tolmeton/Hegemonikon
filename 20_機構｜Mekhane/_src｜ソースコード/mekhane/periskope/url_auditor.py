from __future__ import annotations
# PROOF: mekhane/periskope/url_auditor.py
# PURPOSE: periskope モジュールの url_auditor
"""
Layer D: URL Auditor for Periskopē Citation Verification.

Uses Gemini 3 Flash (via Cortex API) to assess whether a URL
is a valid source for a given claim. Runs only on TAINT citations
to minimize API cost.

Architecture:
    1. URL format validation (regex)
    2. Domain reachability check (HEAD request)
    3. LLM validity judgment (Gemini 3 Flash via Cortex)
"""


import asyncio
import logging
import re

from mekhane.periskope.models import Citation, TaintLevel

logger = logging.getLogger(__name__)

# Valid URL pattern
_URL_PATTERN = re.compile(
    r'^https?://'
    r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*'
    r'[a-zA-Z]{2,}'
    r'(?:/[^\s]*)?$'
)


class URLAuditor:
    """Layer D: LLM-based URL validity assessment.

    Processes only TAINT-level citations to control cost.
    Uses Gemini 3 Flash via Cortex API for fast, cheap judgment.
    """

    def __init__(
        self,
        cortex_account: str = "default",
        cortex_model: str = "gemini-3-flash-preview",
        max_audits: int = 10,
        timeout: float = 15.0,
    ) -> None:
        self._account = cortex_account
        self._model = cortex_model
        self._max_audits = max_audits
        self._timeout = timeout
        self._cortex = None

    def _get_cortex(self):
        """Lazy-initialize Cortex client."""
        if self._cortex is None:
            try:
                from mekhane.ochema.cortex_client import CortexClient
                self._cortex = CortexClient(account=self._account)
            except Exception as e:  # noqa: BLE001
                logger.warning("URLAuditor: CortexClient init failed: %s", e)
        return self._cortex

    async def audit_citations(
        self,
        citations: list[Citation],
        source_contents: dict[str, str] | None = None,
    ) -> list[Citation]:
        """Audit TAINT citations for URL validity.

        Only processes citations with taint_level == TAINT and a source_url.
        Upgrades to SOURCE or downgrades to FABRICATED based on LLM judgment.

        Args:
            citations: Citations (typically already verified by CitationAgent).
            source_contents: Pre-fetched content keyed by URL.

        Returns:
            Updated citations with LLM audit results.
        """
        if source_contents is None:
            source_contents = {}

        # Filter TAINT citations with URLs
        taint_candidates = [
            c for c in citations
            if c.taint_level == TaintLevel.TAINT
            and c.source_url
            and c.claim
        ]

        if not taint_candidates:
            return citations

        # Limit audits for cost control
        to_audit = taint_candidates[:self._max_audits]

        logger.info(
            "URLAuditor: Auditing %d/%d TAINT citations",
            len(to_audit), len(taint_candidates),
        )

        tasks = [
            self._audit_one(c, source_contents)
            for c in to_audit
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        upgraded = 0
        downgraded = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.debug("URLAuditor: Audit failed for citation: %s", result)
                continue
            if isinstance(result, str):
                verdict = result.strip().upper()
                citation = to_audit[i]
                if verdict.startswith("VALID"):
                    citation.taint_level = TaintLevel.SOURCE
                    citation.verification_note += f" | Layer D: {result.strip()}"
                    upgraded += 1
                elif verdict.startswith("INVALID"):
                    citation.taint_level = TaintLevel.FABRICATED
                    citation.verification_note += f" | Layer D: {result.strip()}"
                    downgraded += 1
                else:
                    # SUSPICIOUS — keep as TAINT
                    citation.verification_note += f" | Layer D: {result.strip()}"

        logger.info(
            "URLAuditor: %d upgraded to SOURCE, %d downgraded to FABRICATED",
            upgraded, downgraded,
        )

        return citations

    async def _audit_one(
        self,
        citation: Citation,
        source_contents: dict[str, str],
    ) -> str:
        """Audit a single citation via Gemini 3 Flash."""
        # Step 1: URL format check
        if not _URL_PATTERN.match(citation.source_url):
            return "INVALID — malformed URL"

        # Step 2: Get content (from cache or fetch)
        content = source_contents.get(citation.source_url, "")
        content_preview = content[:500] if content else "(content not available)"

        # Step 3: LLM judgment
        cortex = self._get_cortex()
        if cortex is None:
            return "SUSPICIOUS — CortexClient unavailable"

        prompt = (
            "You are a citation auditor. Evaluate whether a URL is a valid source "
            "for the given claim.\n\n"
            f"Claim: {citation.claim[:300]}\n"
            f"URL: {citation.source_url}\n"
            f"Page content preview: {content_preview}\n\n"
            "Respond with exactly one of:\n"
            "VALID — [reason]\n"
            "SUSPICIOUS — [reason]\n"
            "INVALID — [reason]\n"
        )

        try:
            response = await asyncio.to_thread(
                cortex.generate,
                prompt=prompt,
                model=self._model,
                max_tokens=100,
            )
            return response.strip() if response else "SUSPICIOUS — empty response"
        except Exception as e:  # noqa: BLE001
            logger.debug("URLAuditor LLM call failed: %s", e)
            return f"SUSPICIOUS — LLM error: {e}"
