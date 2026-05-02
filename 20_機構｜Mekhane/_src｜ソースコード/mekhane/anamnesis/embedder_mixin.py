from __future__ import annotations
# PROOF: mekhane/anamnesis/embedder_mixin.py
# PURPOSE: anamnesis モジュールの embedder_mixin
"""EmbedderMixin — shared embedding operations for all Embedder backends.

Any class that implements `embed_batch(texts: list[str]) -> list[list[float]]`
can inherit this mixin to get `embed`, `similarity`, `similarity_batch`,
`novelty`, and `pairwise_novelty` for free.

Used by:
  - Embedder (BGE-M3, CPU/GPU local)
  - VertexEmbedder (Vertex AI API, 3072d)

Design invariant:
  embed_batch() is the sole primitive. ALL other methods are derived from it.
  Subclasses MUST NOT override derived methods to call external APIs directly.

L2 normalization:
  similarity_batch() and pairwise_novelty() use dot product as cosine similarity.
  This is only correct for L2-normalised vectors. To guarantee correctness across
  ALL backends (including Vertex AI with reduced output_dimensionality, which
  returns non-normalised vectors), we normalise in the derived methods.
"""


import logging
import math

import numpy as np

logger = logging.getLogger(__name__)


def _l2_normalize(vec: list[float]) -> list[float]:
    """L2-normalise a vector. Returns zero vector if norm is zero.

    後方互換のため残す。内部の新コードは _l2_normalize_matrix() を使用。
    """
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return vec
    return [x / norm for x in vec]


def _l2_normalize_matrix(matrix: np.ndarray) -> np.ndarray:
    """行ごとに L2 正規化。ゼロベクトルはそのまま返す。"""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    # ゼロ除算回避: ゼロノルムの行は 1.0 に置換
    norms = np.where(norms == 0.0, 1.0, norms)
    return matrix / norms


class EmbedderMixin:
    """Mixin providing embedding operations on top of embed_batch().

    Subclasses MUST implement:
        embed_batch(self, texts: list[str]) -> list[list[float]]

    All other methods (embed, similarity, similarity_batch, novelty,
    pairwise_novelty) are derived from embed_batch and MUST NOT be
    independently overridden with external API calls.

    内積・正規化は numpy 行列演算で一括実行 (for-loop より 10-100× 高速)。
    """

    # -- primitive -----------------------------------------------------------

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embed texts. Subclasses MUST override this."""
        raise NotImplementedError(
            f"{type(self).__name__} must implement embed_batch()"
        )

    def embed(self, text: str) -> np.ndarray:
        """Embed a single text. Returns np.ndarray (float32).

        Delegates to embed_batch() and converts to ndarray.
        Subclasses MAY override for efficiency (e.g. single-item API call),
        but MUST return the same vector as np.array(embed_batch([text])[0]).
        """
        return np.array(self.embed_batch([text])[0], dtype=np.float32)

    # -- derived operations --------------------------------------------------

    def similarity(self, text_a: str, text_b: str) -> float:
        """Cosine similarity between two texts.

        Returns:
            Score in [0.0, 1.0].
        """
        if not text_a or not text_b:
            return 0.0
        scores = self.similarity_batch(text_a, [text_b])
        return scores[0] if scores else 0.0

    def similarity_batch(
        self, query: str, documents: list[str],
    ) -> list[float]:
        """Cosine similarity between *query* and each document.

        Single embed_batch() call for query + all docs.
        numpy 行列演算で一括正規化 + 一括内積。

        Returns:
            List of similarity scores in [0.0, 1.0].
        """
        if not documents:
            return []
        all_texts = [query] + documents
        # numpy 一括変換 + 一括正規化
        matrix = np.array(self.embed_batch(all_texts), dtype=np.float64)
        normalized = _l2_normalize_matrix(matrix)
        query_vec = normalized[0]  # (D,)
        doc_vecs = normalized[1:]  # (N, D)
        # 一括内積: (N, D) @ (D,) → (N,)
        scores = doc_vecs @ query_vec
        # クランプして list に変換
        return np.clip(scores, 0.0, 1.0).tolist()

    def novelty(self, text_a: str, text_b: str) -> float:
        """Novelty (distance) between two texts.

        Returns:
            1.0 - cosine_similarity  (0.0 = identical, 1.0 = orthogonal).
        """
        if not text_a or not text_b:
            return 1.0
        scores = self.similarity_batch(text_a, [text_b])
        return 1.0 - scores[0] if scores else 1.0

    def pairwise_novelty(
        self, texts: list[str], labels: list[str] | None = None,
    ) -> dict[tuple[str, str], float]:
        """Novelty for all pairs of texts.

        Single embed_batch call, then numpy 一括正規化, then
        行列積で全ペアの類似度を一括計算。

        Returns:
            Dict mapping (label_i, label_j) → novelty score.
        """
        if len(texts) < 2:
            return {}

        if labels is None:
            labels = [str(i) for i in range(len(texts))]

        # numpy 一括変換 + 一括正規化
        matrix = np.array(self.embed_batch(texts), dtype=np.float64)
        normalized = _l2_normalize_matrix(matrix)
        # 全ペア類似度: (N, D) @ (D, N) → (N, N)
        sim_matrix = normalized @ normalized.T
        sim_matrix = np.clip(sim_matrix, 0.0, 1.0)

        # 上三角から結果を抽出
        result: dict[tuple[str, str], float] = {}
        n = len(texts)
        rows, cols = np.triu_indices(n, k=1)
        for r, c in zip(rows, cols):
            result[(labels[r], labels[c])] = round(1.0 - float(sim_matrix[r, c]), 3)
        return result
