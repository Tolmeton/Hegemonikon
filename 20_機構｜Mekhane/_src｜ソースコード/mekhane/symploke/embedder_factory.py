#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/ A0→エンベディング統一が必要→embedder_factory が担う
"""
Symplokē Embedder Factory — embedder 一元管理

全 ingest / search モジュールはここからエンベダーと embed_fn を取得する。

環境変数 HGK_EMBEDDER で切替:
  - "vertex" (デフォルト): VertexEmbedder (API Key 方式, 3072d)
  - "codebert": CodeBertEmbedder (microsoft/codebert-base, 768d, GPU 対応)

Usage:
    from mekhane.symploke.embedder_factory import get_embed_fn, get_dimension, get_embedder
"""
import logging
import os
import threading

logger = logging.getLogger(__name__)

# PURPOSE: Shared state for singleton embedder
_embedder = None
_embedder_lock = threading.Lock()

# 環境変数で embedder を選択
EMBEDDER_TYPE = os.environ.get("HGK_EMBEDDER", "vertex").lower()


# PURPOSE: Get or create the shared embedder
def get_embedder():
    """Get or create the shared embedder (singleton, thread-safe).

    HGK_EMBEDDER 環境変数で切替:
      - "vertex": VertexEmbedder (API Key, gemini-embedding, 3072d)
      - "codebert": CodeBertEmbedder (microsoft/codebert-base, 768d)

    Returns:
        EmbedderMixin instance.
    Raises:
        RuntimeError: If initialization fails.
    """
    global _embedder

    if _embedder is not None:
        return _embedder

    with _embedder_lock:
        if _embedder is not None:
            return _embedder

        if EMBEDDER_TYPE == "codebert":
            _embedder = _create_codebert_embedder()
        else:
            _embedder = _create_vertex_embedder()

        return _embedder


def _create_vertex_embedder():
    """VertexEmbedder を作成。"""
    from mekhane.anamnesis.constants import EMBED_MODEL, EMBED_DIM
    try:
        from mekhane.anamnesis.vertex_embedder import VertexEmbedder
        emb = VertexEmbedder(
            model_name=EMBED_MODEL,
            dimension=EMBED_DIM,
        )
        logger.info(
            "Symplokē embedder: VertexEmbedder (%s, %dd, %d keys)",
            EMBED_MODEL, EMBED_DIM, len(emb._api_keys),
        )
        return emb
    except Exception as e:  # noqa: BLE001
        logger.error("VertexEmbedder initialization failed: %s", e)
        raise RuntimeError(f"VertexEmbedder init failed: {e}") from e


def _create_codebert_embedder():
    """CodeBertEmbedder を作成。"""
    try:
        from mekhane.anamnesis.codebert_embedder import CodeBertEmbedder
        emb = CodeBertEmbedder()
        logger.info(
            "Symplokē embedder: CodeBertEmbedder (%s, %dd)",
            emb._model_name, emb.dimension,
        )
        return emb
    except Exception as e:  # noqa: BLE001
        logger.error("CodeBertEmbedder initialization failed: %s", e)
        raise RuntimeError(f"CodeBertEmbedder init failed: {e}") from e


# PURPOSE: Create embed_fn for DomainIndex (text → np.ndarray)
def get_embed_fn():
    """Get embed_fn — embedder.embed.

    Returns:
        Callable[[str], np.ndarray]
    """
    return get_embedder().embed


# PURPOSE: Get embedding dimension
def get_dimension() -> int:
    """Return the embedding dimension."""
    if EMBEDDER_TYPE == "codebert":
        from mekhane.anamnesis.codebert_embedder import CODEBERT_DIM
        return CODEBERT_DIM
    else:
        from mekhane.anamnesis.constants import EMBED_DIM
        return EMBED_DIM
