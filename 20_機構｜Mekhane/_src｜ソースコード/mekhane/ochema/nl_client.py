# PROOF: [L2/インフラ] <- mekhane/ochema/nl_client.py A0→Cloud NL API 接続
# PURPOSE: Cloud Natural Language API v2 REST クライアント
from __future__ import annotations
from typing import Any
"""NLClient — Google Cloud Natural Language API v2 client.

Provides entity extraction for Periskopē query expansion and reranking.
Uses gcloud CLI tokens for authentication (no SA key required).

Free tier: 5,000 units/month per account.

Usage:
    from mekhane.ochema.nl_client import NLClient

    client = NLClient()
    entities = client.analyze_entities("Free Energy Principle and active inference")
    for e in entities:
        print(f"{e.name} ({e.type}, salience={e.salience:.2f})")

API Reference:
    https://cloud.google.com/natural-language/docs/reference/rest/v2/documents/analyzeEntities
"""


import json
import logging
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_NL_API_URL = "https://language.googleapis.com/v2/documents:analyzeEntities"

# Token cache: (token_str, expiry_timestamp)
_token_cache: dict[str, tuple[str, float]] = {}
_TOKEN_TTL = 3300  # 55 minutes

# F1: Entity type → recommended search sources routing table
ENTITY_SOURCE_ROUTING: dict[str, list[str]] = {
    "PERSON": ["semantic_scholar", "vertex_search"],
    "ORGANIZATION": ["github", "vertex_search"],
    "WORK_OF_ART": ["semantic_scholar"],
    "EVENT": ["vertex_search", "brave"],
    "CONSUMER_GOOD": ["github", "vertex_search"],
    "LOCATION": ["vertex_search", "brave"],
    # OTHER, NUMBER, UNKNOWN → no routing bias (use all sources)
}


def suggest_sources(entities: list[Entity]) -> set[str]:
    """F1: Suggest additional search sources based on entity types.
    
    Returns a set of source names that should be enabled based on
    the dominant entity types in the query.
    """
    suggestions: set[str] = set()
    for e in entities:
        if e.salience >= 0.3 and e.type in ENTITY_SOURCE_ROUTING:
            suggestions.update(ENTITY_SOURCE_ROUTING[e.type])
    return suggestions


@dataclass
class Entity:
    """Extracted entity from Cloud NL API."""

    name: str
    type: str  # PERSON, LOCATION, ORGANIZATION, EVENT, WORK_OF_ART, etc.
    salience: float  # 0.0 - 1.0
    metadata: dict[str, str] = field(default_factory=dict)
    mentions: int = 1

    def __repr__(self) -> str:
        return f"Entity({self.name!r}, type={self.type}, salience={self.salience:.2f})"


class NLClient:
    """Cloud Natural Language API v2 client.

    Uses gcloud CLI token authentication (multi-account compatible).
    Caches tokens for 55 minutes to minimize subprocess calls.
    """

    def __init__(
        self,
        gcloud_account: str = "",
        project_id: str = "",
        timeout: float = 10.0,
    ) -> None:
        self._gcloud_account = gcloud_account
        self._project_id = project_id
        self._timeout = timeout

    def _get_token(self) -> str:
        """Get OAuth2 access token via gcloud CLI.

        Returns:
            Access token string, or empty string on failure.
        """
        cache_key = self._gcloud_account or "__default__"

        # Check cache
        if cache_key in _token_cache:
            token, expiry = _token_cache[cache_key]
            if time.time() < expiry:
                return token

        try:
            cmd = ["gcloud", "auth", "print-access-token"]
            if self._gcloud_account:
                cmd.append(f"--account={self._gcloud_account}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                logger.warning(
                    "NLClient: gcloud auth failed: %s",
                    result.stderr.strip(),
                )
                return ""
            token = result.stdout.strip()
            _token_cache[cache_key] = (token, time.time() + _TOKEN_TTL)
            return token
        except OSError as e:
            logger.warning("NLClient: token retrieval failed: %s", e)
            return ""

    def analyze_entities(
        self,
        text: str,
        language: str = "",
        max_entities: int = 10,
    ) -> list[Entity]:
        """Extract entities from text using Cloud NL API v2.

        Args:
            text: Input text (max 1,000,000 bytes for v2).
            language: Language hint (e.g. "en", "ja"). Empty = auto-detect.
            max_entities: Maximum entities to return (sorted by salience).

        Returns:
            List of Entity objects, sorted by salience descending.
        """
        token = self._get_token()
        if not token:
            logger.warning("NLClient: No token available — skipping entity analysis")
            return []

        # Truncate to stay within limits (v2 allows 1MB, we use 10K for safety)
        if len(text.encode("utf-8")) > 10_000:
            text = text[:5000]

        payload: dict[str, Any] = {
            "document": {
                "type": "PLAIN_TEXT",
                "content": text,
            },
            "encodingType": "UTF8",
        }
        if language:
            payload["document"]["languageCode"] = language

        headers: dict[str, str] = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        # Required for user credentials (gcloud tokens) — specifies quota project
        if self._project_id:
            headers["X-Goog-User-Project"] = self._project_id

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                _NL_API_URL,
                data=data,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8")[:200]
            except (OSError, UnicodeDecodeError) as _e:
                logger.debug("Ignored exception: %s", _e)
            logger.warning(
                "NLClient: API error %d: %s",
                e.code,
                body,
            )
            return []
        except OSError as e:
            logger.warning("NLClient: Request failed: %s", e)
            return []

        # Parse response
        entities: list[Entity] = []
        for item in result.get("entities", []):
            entity = Entity(
                name=item.get("name", ""),
                type=item.get("type", "UNKNOWN"),
                salience=item.get("salience", 0.0),
                metadata=item.get("metadata", {}),
                mentions=len(item.get("mentions", [])),
            )
            entities.append(entity)

        # Sort by salience descending, take top N
        entities.sort(key=lambda e: e.salience, reverse=True)
        entities = entities[:max_entities]

        if entities:
            logger.info(
                "NLClient: %d entities from %d chars (top: %s %.2f)",
                len(entities),
                len(text),
                entities[0].name,
                entities[0].salience,
            )

        return entities

    @property
    def available(self) -> bool:
        """Check if NL API is accessible (has valid token)."""
        return bool(self._get_token())
