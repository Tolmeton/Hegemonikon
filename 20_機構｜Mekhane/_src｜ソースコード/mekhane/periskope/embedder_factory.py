from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/periskope/embedder_factory.py A0→埋め込みベクトル生成が必要→embedder_factory が担う
"""
Periskopē Embedder Factory — Single Source of Truth for embedder instances.

Consolidates embedder initialization across engine.py, citation_agent.py
and synthesizer.py into a single shared factory with lazy initialization.

Priority:
    1. VertexEmbedder (gemini-embedding-001) — API, no CPU overhead
    2. BGE-M3 (local) — ~20s CPU load, used as fallback

Thread-safe singleton: once initialized, the same embedder instance
is shared across all Periskopē modules.
"""


import logging
import threading

from mekhane.anamnesis.embedder_mixin import EmbedderMixin

logger = logging.getLogger(__name__)

_embedder: EmbedderMixin | None = None
_embedder_lock = threading.Lock()
_embedder_failed = False


def get_embedder(
    dimension: int | None = None,
    vertex_model: str | None = None,
    credentials_file: str = "",
) -> EmbedderMixin:
    """Get or create the shared Periskopē embedder.

    Thread-safe lazy initialization with Vertex → BGE-M3 fallback.

    Args:
        dimension: Embedding dimension for Vertex (default: constants.EMBED_DIM).
        vertex_model: Vertex embedding model name (default: constants.EMBED_MODEL).
        credentials_file: Path to SA key JSON. If set, uses SA key auth
            instead of gcloud ADC. Eliminates dependency on active account.

    Returns:
        Embedder instance (VertexEmbedder or BGE-M3 Embedder).
        Supports `.embed(text) -> list[float]` and `.embed_batch(texts) -> list[list[float]]`.
    """
    global _embedder, _embedder_failed

    if _embedder is not None:
        return _embedder

    with _embedder_lock:
        # Double-check after acquiring lock
        if _embedder is not None:
            return _embedder

        if _embedder_failed:
            raise RuntimeError("Embedder initialization previously failed")

        # 1. Try Vertex AI (fast API-based embedding)
        try:
            from mekhane.anamnesis.constants import EMBED_MODEL, EMBED_DIM
            if vertex_model is None:
                vertex_model = EMBED_MODEL
            if dimension is None:
                dimension = EMBED_DIM
            from mekhane.anamnesis.vertex_embedder import VertexEmbedder
            _embedder = VertexEmbedder(
                model_name=vertex_model,
                dimension=dimension,
                credentials_file=credentials_file,
            )
            logger.info(
                "Periskopē embedder: VertexEmbedder (%s, %dd)",
                vertex_model, dimension,
            )
            return _embedder
        except Exception as e:  # noqa: BLE001
            logger.info("Vertex AI unavailable (%s), falling back to BGE-M3", e)

        # 2. Fallback to local BGE-M3
        try:
            from mekhane.anamnesis.index import Embedder
            _embedder = Embedder()
            logger.info("Periskopē embedder: BGE-M3 (local CPU)")
            return _embedder
        except Exception as e:  # noqa: BLE001
            logger.error("BGE-M3 initialization failed: %s", e)
            _embedder_failed = True
            raise


def reset_embedder():
    """Reset the shared embedder (for testing / hot-reload)."""
    global _embedder, _embedder_failed
    with _embedder_lock:
        _embedder = None
        _embedder_failed = False
