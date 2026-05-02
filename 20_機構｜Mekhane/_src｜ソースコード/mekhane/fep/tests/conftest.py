"""Global test fixtures for mekhane.fep tests.

Patches all embedding-related classes to prevent real API calls.
Targets:
  - mekhane.anamnesis.vertex_embedder.VertexEmbedder  (TheoremAttractor)
  - mekhane.anamnesis.index.Embedder                   (SeriesAttractor)
"""
import pytest
import numpy as np


class MockEmbedder:
    """Mock embedder producing semantically distinct deterministic embeddings.

    Each text gets a deterministic direction based on its hash.
    Embeddings are designed so that:
    - Different texts produce meaningfully different vectors
    - User input (via embed()) aligns with the first prototype direction
    - Temperature sharpening preserves separation above threshold (0.15)
    """

    _DIMENSION = 3072
    # Store prototype directions so embed() can align with them
    _prototype_directions: list[np.ndarray] = []

    def __init__(self, *args, **kwargs):
        self.model_name = kwargs.get("model_name", "mock")
        self._dimension = kwargs.get("dimension", self._DIMENSION)
        self._dimension_mismatch = False
        self._use_gpu = False
        self._is_onnx_fallback = False
        self._initialized = True
        self._embedder = self  # Embedder wraps itself

        try:
            from mekhane.paths import STATE_CACHE
            cache_file = STATE_CACHE / "theorem_proto.npz"
            cached = np.load(str(cache_file), allow_pickle=False)
            self.proto_matrix = cached["proto_matrix"]
        except Exception:
            self.proto_matrix = np.random.randn(24, self._DIMENSION).astype(np.float32)

    def _make_direction(self, seed: int) -> np.ndarray:
        """Create a unit vector from a deterministic seed."""
        rng = np.random.RandomState(abs(seed) % (2**31))
        vec = rng.randn(self._DIMENSION).astype(np.float32)
        return vec / np.linalg.norm(vec)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return semantically distinct vectors for each text.

        Records the first call's directions as 'prototype directions'
        so that embed() can produce vectors aligned with them.
        """
        results = []
        for t in texts:
            vec = self._make_direction(hash(t))
            results.append(vec)
        # Record prototype directions on first call (Series prototypes)
        if not MockEmbedder._prototype_directions:
            MockEmbedder._prototype_directions = [v.copy() for v in results]
        return [v.tolist() for v in results]

    def embed(self, text: str) -> list[float]:
        """Return a vector aligned with the first prototype direction.

        This ensures at least one Series always has high similarity,
        exceeding the threshold even after temperature sharpening.
        """
        if MockEmbedder._prototype_directions:
            # Align with first prototype + small perturbation for uniqueness
            base = MockEmbedder._prototype_directions[0]
            rng = np.random.RandomState(abs(hash(text)) % (2**31))
            noise = rng.randn(self._DIMENSION).astype(np.float32) * 0.02
            vec = base + noise
            return (vec / np.linalg.norm(vec)).tolist()
        else:
            # Fallback: pure random (should not happen in practice)
            return self._make_direction(hash(text)).tolist()


@pytest.fixture(autouse=True)
def patch_all_embedders(monkeypatch):
    """Patch both VertexEmbedder and Embedder to prevent real API calls."""
    import mekhane.anamnesis.vertex_embedder as ve_mod
    import mekhane.anamnesis.index as idx_mod

    # Clear class-level state from previous tests
    MockEmbedder._prototype_directions = []

    # Clear Embedder singleton cache so fresh mock instances are created
    idx_mod.Embedder._instances = {}

    # Patch VertexEmbedder (used by TheoremAttractor)
    monkeypatch.setattr(ve_mod, "VertexEmbedder", MockEmbedder)

    # Patch Embedder (used by SeriesAttractor)
    monkeypatch.setattr(idx_mod, "Embedder", MockEmbedder)

