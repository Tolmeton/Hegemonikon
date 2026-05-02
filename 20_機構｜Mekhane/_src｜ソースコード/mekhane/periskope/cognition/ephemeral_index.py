from __future__ import annotations
# PROOF: mekhane/periskope/cognition/ephemeral_index.py
# PURPOSE: periskope モジュールの ephemeral_index
"""
Ephemeral Index — Shared in-memory vector store for Phase Inversion.

VISION §7: Both Thesis and Anti engines publish their intermediate
findings (search results, synthesis snippets, reasoning steps) to a
shared vector index. Each engine can then discover the opponent's
findings via semantic similarity, enabling dynamic mutual interaction.

```
Thesis CoT iter → [embed] → Ephemeral Index ← [embed] ← Anti CoT iter
       ↑                          ↓                          ↑
       └──── vector search ───────┘──── vector search ───────┘
```

Design:
    - Thread-safe (asyncio + threading lock for embedder calls)
    - In-memory numpy cosine similarity (no FAISS dependency)
    - Vertex Embedder (gemini-embedding-001, 3072d) via embedder_factory
    - TTL-based expiry for session-scoped indices
    - Publish/subscribe pattern for CoT step integration
"""


import logging
import time
import threading
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class IndexEntry:
    """A single entry in the ephemeral index."""

    text: str
    source: str        # "thesis" or "antithesis"
    entry_type: str    # "search_result" | "synthesis" | "reasoning_step" | "refutation"
    metadata: dict = field(default_factory=dict)
    embedding: np.ndarray | None = None
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.monotonic()


class EphemeralIndex:
    """In-memory vector index for inter-engine knowledge sharing.

    Thread-safe, session-scoped. Both engines publish their findings
    here; each can query the other's discoveries via cosine similarity.

    Usage:
        index = EphemeralIndex()
        await index.publish("thesis", "search_result", "Einstein proved E=mc²")
        results = await index.query("antithesis", "energy mass equivalence", top_k=3)
    """

    def __init__(self, dimension: int = 3072):
        self._entries: list[IndexEntry] = []
        self._embeddings: np.ndarray | None = None  # (N, D) matrix
        self._dimension = dimension
        self._lock = threading.Lock()
        self._embedder = None
        self._dirty = True  # True when _embeddings needs rebuild

    def _get_embedder(self):
        """Lazy-load embedder via factory (Vertex AI primary)."""
        if self._embedder is None:
            from mekhane.periskope.embedder_factory import get_embedder
            self._embedder = get_embedder(dimension=self._dimension)
        return self._embedder

    async def publish(
        self,
        source: str,
        entry_type: str,
        text: str,
        metadata: dict | None = None,
    ) -> None:
        """Add an entry to the index (async-safe).

        Args:
            source: "thesis" or "antithesis"
            entry_type: "search_result" | "synthesis" | "reasoning_step" | "refutation"
            text: Text content to index.
            metadata: Optional metadata (e.g., URL, confidence).
        """
        if not text or len(text.strip()) < 10:
            return

        # Truncate very long texts for embedding efficiency
        embed_text = text[:2000]

        try:
            embedder = self._get_embedder()
            vec = embedder.embed(embed_text)
            embedding = np.array(vec, dtype=np.float32)
        except Exception as e:  # noqa: BLE001
            logger.warning("EphemeralIndex embed failed: %s", e)
            embedding = None

        entry = IndexEntry(
            text=text,
            source=source,
            entry_type=entry_type,
            metadata=metadata or {},
            embedding=embedding,
        )

        with self._lock:
            self._entries.append(entry)
            self._dirty = True

        logger.debug(
            "EphemeralIndex: published %s/%s (%d chars)",
            source, entry_type, len(text),
        )

    async def publish_batch(
        self,
        source: str,
        entry_type: str,
        texts: list[str],
        metadata_list: list[dict] | None = None,
    ) -> int:
        """Batch publish multiple entries (single embed_batch call).

        Returns:
            Number of entries successfully added.
        """
        if not texts:
            return 0

        # Filter and truncate
        valid = []
        for i, t in enumerate(texts):
            if t and len(t.strip()) >= 10:
                valid.append((i, t[:2000]))

        if not valid:
            return 0

        try:
            embedder = self._get_embedder()
            embed_texts = [t for _, t in valid]
            vecs = embedder.embed_batch(embed_texts)
        except Exception as e:  # noqa: BLE001
            logger.warning("EphemeralIndex embed_batch failed: %s", e)
            return 0

        metas = metadata_list or [{}] * len(texts)
        count = 0

        with self._lock:
            for (orig_idx, _), vec in zip(valid, vecs):
                entry = IndexEntry(
                    text=texts[orig_idx],
                    source=source,
                    entry_type=entry_type,
                    metadata=metas[orig_idx] if orig_idx < len(metas) else {},
                    embedding=np.array(vec, dtype=np.float32),
                )
                self._entries.append(entry)
                count += 1
            self._dirty = True

        logger.debug(
            "EphemeralIndex: batch published %d/%d %s/%s entries",
            count, len(texts), source, entry_type,
        )
        return count

    def _rebuild_matrix(self) -> None:
        """Rebuild the (N, D) embedding matrix from entries."""
        with self._lock:
            if not self._dirty:
                return
            valid = [e for e in self._entries if e.embedding is not None]
            if valid:
                self._embeddings = np.stack([e.embedding for e in valid])
                # L2 normalize for cosine similarity via dot product
                norms = np.linalg.norm(self._embeddings, axis=1, keepdims=True)
                norms = np.maximum(norms, 1e-10)
                self._embeddings = self._embeddings / norms
            else:
                self._embeddings = None
            self._dirty = False

    async def query(
        self,
        requesting_source: str,
        query_text: str,
        top_k: int = 5,
        exclude_own: bool = True,
        entry_types: list[str] | None = None,
    ) -> list[tuple[IndexEntry, float]]:
        """Query the index for semantically similar entries.

        Args:
            requesting_source: Who is asking ("thesis" or "antithesis").
            query_text: Query text to find similar entries for.
            top_k: Maximum number of results.
            exclude_own: If True, exclude entries from the same source
                         (default behavior for dynamic interaction).
            entry_types: Filter by entry type (e.g., ["refutation"]).

        Returns:
            List of (entry, similarity_score) tuples, sorted by similarity.
        """
        if not query_text:
            return []

        self._rebuild_matrix()

        if self._embeddings is None or len(self._embeddings) == 0:
            return []

        # Embed query
        try:
            embedder = self._get_embedder()
            q_vec = embedder.embed(query_text[:2000])
            q_norm = np.linalg.norm(q_vec)
            if q_norm > 1e-10:
                q_vec = q_vec / q_norm
        except Exception as e:  # noqa: BLE001
            logger.warning("EphemeralIndex query embed failed: %s", e)
            return []

        # Cosine similarity via dot product (vectors are L2-normalized)
        with self._lock:
            valid_entries = [e for e in self._entries if e.embedding is not None]

        if not valid_entries:
            return []

        similarities = self._embeddings @ q_vec  # (N,)

        # Filter and rank
        results = []
        for i, (entry, sim) in enumerate(zip(valid_entries, similarities)):
            # Exclude own entries if requested
            if exclude_own and entry.source == requesting_source:
                continue
            # Filter by entry type
            if entry_types and entry.entry_type not in entry_types:
                continue
            results.append((entry, float(sim)))

        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def stats(self) -> dict:
        """Return index statistics."""
        with self._lock:
            total = len(self._entries)
            by_source = {}
            by_type = {}
            for e in self._entries:
                by_source[e.source] = by_source.get(e.source, 0) + 1
                by_type[e.entry_type] = by_type.get(e.entry_type, 0) + 1
            embedded = sum(1 for e in self._entries if e.embedding is not None)

        return {
            "total_entries": total,
            "embedded": embedded,
            "by_source": by_source,
            "by_type": by_type,
        }

    def clear(self) -> None:
        """Clear all entries (session reset)."""
        with self._lock:
            self._entries.clear()
            self._embeddings = None
            self._dirty = True
