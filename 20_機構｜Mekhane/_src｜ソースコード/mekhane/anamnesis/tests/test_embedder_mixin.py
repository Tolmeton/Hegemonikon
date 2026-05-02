# PROOF: mekhane/anamnesis/tests/test_embedder_mixin.py
# PURPOSE: anamnesis モジュールの embedder_mixin に対するテスト
"""Tests for EmbedderMixin — exhaustive verification of all shared methods.

Coverage:
  - TestDelegation: NotImplementedError, embed() delegation, embed() edge cases
  - TestNormalization: L2 normalization guarantee (R2 safety net)
  - TestSimilarityBatch: empty, single, identical, multiple
  - TestSimilarity: empty inputs, identical, different
  - TestNovelty: identical, empty, different
  - TestPairwiseNovelty: empty, single, identical, labels, multiple
"""

import pytest
import math
import numpy as np
from mekhane.anamnesis.embedder_mixin import EmbedderMixin, _l2_normalize


class MockEmbedder(EmbedderMixin):
    """Embedder with deterministic L2-normalised embed_batch for testing."""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return normalised vectors based on text hash for reproducibility."""
        vectors = []
        for text in texts:
            h = hash(text)
            raw = [float((h >> (i * 8)) & 0xFF) for i in range(8)]
            norm = math.sqrt(sum(x * x for x in raw)) or 1.0
            vectors.append([x / norm for x in raw])
        return vectors


class NonNormalizingEmbedder(EmbedderMixin):
    """Embedder that returns NON-normalised vectors (simulates Vertex AI
    with reduced output_dimensionality). R2 safety test."""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            h = hash(text)
            # Deliberately NON-normalised: raw magnitudes vary wildly
            vectors.append([float((h >> (i * 8)) & 0xFF) + 10.0 for i in range(8)])
        return vectors


class BareEmbedder(EmbedderMixin):
    """Embedder that does NOT override embed_batch — tests NotImplementedError."""
    pass


@pytest.fixture
def embedder():
    return MockEmbedder()


@pytest.fixture
def non_norm_embedder():
    return NonNormalizingEmbedder()


# ── Delegation & Edge Cases (R1, R5) ──────────────────────────────────

class TestDelegation:
    def test_not_implemented(self):
        """BareEmbedder MUST raise NotImplementedError."""
        bare = BareEmbedder()
        with pytest.raises(NotImplementedError, match="BareEmbedder"):
            bare.embed_batch(["test"])

    def test_embed_delegates_to_embed_batch(self, embedder):
        """embed(text) MUST return exactly embed_batch([text])[0]."""
        vec_single = embedder.embed("hello world")
        vec_batch = embedder.embed_batch(["hello world"])[0]
        # embed() は np.ndarray を返すため、list に変換して比較
        assert list(vec_single) == vec_batch

    def test_embed_returns_ndarray_of_float(self, embedder):
        """embed() は np.ndarray (float32) を返す。"""
        vec = embedder.embed("single text")
        assert isinstance(vec, np.ndarray)
        assert len(vec) == 8
        assert vec.dtype == np.float32

    def test_embed_empty_string(self, embedder):
        """Empty string should not crash — embed_batch handles it."""
        vec = embedder.embed("")
        assert isinstance(vec, np.ndarray)
        assert len(vec) == 8

    def test_embed_long_text(self, embedder):
        """Very long text should not crash."""
        vec = embedder.embed("x" * 10000)
        assert isinstance(vec, np.ndarray)
        assert len(vec) == 8


# ── L2 Normalization Guarantee (R2) ───────────────────────────────────

class TestNormalization:
    def test_l2_normalize_helper(self):
        """_l2_normalize should produce unit vector."""
        raw = [3.0, 4.0]
        normed = _l2_normalize(raw)
        norm = math.sqrt(sum(x * x for x in normed))
        assert norm == pytest.approx(1.0, abs=1e-10)

    def test_l2_normalize_zero_vector(self):
        """Zero vector should pass through unchanged."""
        zero = [0.0, 0.0, 0.0]
        assert _l2_normalize(zero) == zero

    def test_similarity_with_non_normalized_vectors(self, non_norm_embedder):
        """R2: similarity_batch MUST produce valid [0,1] scores even
        when embed_batch returns non-normalised vectors."""
        scores = non_norm_embedder.similarity_batch("hello", ["world"])
        assert len(scores) == 1
        assert 0.0 <= scores[0] <= 1.0

    def test_identical_similarity_non_normalized(self, non_norm_embedder):
        """R2: identical text MUST give similarity ≈ 1.0
        even with non-normalised vectors."""
        scores = non_norm_embedder.similarity_batch("same", ["same"])
        assert scores[0] == pytest.approx(1.0, abs=0.001)

    def test_novelty_with_non_normalized_vectors(self, non_norm_embedder):
        """R2: novelty MUST return valid [0,1] with non-normalised vectors."""
        n = non_norm_embedder.novelty("hello", "world")
        assert 0.0 <= n <= 1.0

    def test_pairwise_with_non_normalized_vectors(self, non_norm_embedder):
        """R2: pairwise_novelty MUST work with non-normalised vectors."""
        result = non_norm_embedder.pairwise_novelty(["a", "b"])
        assert ("0", "1") in result
        assert 0.0 <= result[("0", "1")] <= 1.0


# ── SimilarityBatch ───────────────────────────────────────────────────

class TestSimilarityBatch:
    def test_empty_docs(self, embedder):
        assert embedder.similarity_batch("query", []) == []

    def test_single_doc(self, embedder):
        scores = embedder.similarity_batch("hello", ["world"])
        assert len(scores) == 1
        assert 0.0 <= scores[0] <= 1.0

    def test_identical_text(self, embedder):
        scores = embedder.similarity_batch("same text", ["same text"])
        assert scores[0] == pytest.approx(1.0, abs=0.001)

    def test_multiple_docs(self, embedder):
        scores = embedder.similarity_batch("q", ["a", "b", "c"])
        assert len(scores) == 3
        assert all(0.0 <= s <= 1.0 for s in scores)


# ── Similarity ────────────────────────────────────────────────────────

class TestSimilarity:
    def test_empty_text_a(self, embedder):
        assert embedder.similarity("", "world") == 0.0

    def test_empty_text_b(self, embedder):
        assert embedder.similarity("hello", "") == 0.0

    def test_both_empty(self, embedder):
        assert embedder.similarity("", "") == 0.0

    def test_identical(self, embedder):
        assert embedder.similarity("same", "same") == pytest.approx(1.0, abs=0.001)

    def test_different(self, embedder):
        s = embedder.similarity("hello", "world")
        assert 0.0 <= s <= 1.0


# ── Novelty ───────────────────────────────────────────────────────────

class TestNovelty:
    def test_identical(self, embedder):
        assert embedder.novelty("same", "same") == pytest.approx(0.0, abs=0.001)

    def test_empty_text_a(self, embedder):
        assert embedder.novelty("", "world") == 1.0

    def test_empty_text_b(self, embedder):
        assert embedder.novelty("hello", "") == 1.0

    def test_both_empty(self, embedder):
        assert embedder.novelty("", "") == 1.0

    def test_different(self, embedder):
        n = embedder.novelty("hello", "world")
        assert 0.0 <= n <= 1.0

    def test_symmetry(self, embedder):
        """novelty(a,b) should equal novelty(b,a)."""
        n1 = embedder.novelty("alpha", "beta")
        n2 = embedder.novelty("beta", "alpha")
        assert n1 == pytest.approx(n2, abs=0.001)


# ── PairwiseNovelty ───────────────────────────────────────────────────

class TestPairwiseNovelty:
    def test_empty(self, embedder):
        assert embedder.pairwise_novelty([]) == {}

    def test_single(self, embedder):
        assert embedder.pairwise_novelty(["only"]) == {}

    def test_two_identical(self, embedder):
        result = embedder.pairwise_novelty(["same", "same"])
        assert ("0", "1") in result
        assert result[("0", "1")] == pytest.approx(0.0, abs=0.001)

    def test_custom_labels(self, embedder):
        result = embedder.pairwise_novelty(["a", "b"], labels=["x", "y"])
        assert ("x", "y") in result

    def test_three_texts(self, embedder):
        result = embedder.pairwise_novelty(["a", "b", "c"])
        assert len(result) == 3  # C(3,2) = 3 pairs
        for v in result.values():
            assert 0.0 <= v <= 1.0

    def test_symmetry(self, embedder):
        """pairwise_novelty should be symmetric: novelty(a,b) == novelty(b,a)."""
        result = embedder.pairwise_novelty(["alpha", "beta"])
        # Only (0,1) exists by convention, but the score should be same
        # as novelty("alpha", "beta")
        n = embedder.novelty("alpha", "beta")
        assert result[("0", "1")] == pytest.approx(n, abs=0.01)
