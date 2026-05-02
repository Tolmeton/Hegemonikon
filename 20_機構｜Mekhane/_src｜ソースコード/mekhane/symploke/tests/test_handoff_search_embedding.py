# PROOF: [L2/インフラ] <- handoff_search 回帰 — VectorStore.encode 廃止後も検索ベクトルが取得できる
"""Handoff / 会話検索の埋め込み経路: embedder_factory 必須（model_name なし encode は禁止）。"""
import time

import numpy as np
from unittest.mock import MagicMock, patch


def test_query_embedding_vector_uses_embedder_factory():
    """_query_embedding_vector が embedder_factory を経由し 1d ベクトルを返す。"""
    from mekhane.symploke import handoff_search as hs

    with patch("mekhane.symploke.embedder_factory.get_embed_fn") as ge:
        ge.return_value = lambda q: np.arange(8, dtype=np.float32)
        hs._QUERY_EMBED_CACHE.clear()
        v = hs._query_embedding_vector("test query")
        assert v.shape == (8,)
        assert v.dtype == np.float32
        ge.assert_called_once()


def test_query_embedding_vector_flattens_2d():
    """埋め込みが (1, d) のとき 1d に潰す。"""
    from mekhane.symploke import handoff_search as hs

    with patch("mekhane.symploke.embedder_factory.get_embed_fn") as ge:
        ge.return_value = lambda q: np.ones((1, 4), dtype=np.float32)
        hs._QUERY_EMBED_CACHE.clear()
        v = hs._query_embedding_vector("x")
        assert v.shape == (4,)


def test_query_embedding_vector_cache_hits_same_query():
    """同一クエリでは get_embed_fn を再呼び出ししない。"""
    from mekhane.symploke import handoff_search as hs

    with patch("mekhane.symploke.embedder_factory.get_embed_fn") as ge:
        ge.return_value = lambda q: np.arange(6, dtype=np.float32)
        hs._QUERY_EMBED_CACHE.clear()
        a = hs._query_embedding_vector("cached-q")
        b = hs._query_embedding_vector("cached-q")
        assert np.array_equal(a, b)
        ge.assert_called_once()


def test_vector_search_with_embed_timeout_returns_empty_on_slow_embed():
    """埋め込みが遅いときタイムアウトで [] を返す。"""
    from mekhane.symploke import handoff_search as hs

    adapter = MagicMock()

    def slow_embed(_q):
        time.sleep(1.0)
        return np.zeros(4, dtype=np.float32)

    with patch.object(hs, "_query_embedding_vector", side_effect=slow_embed):
        out = hs._vector_search_with_embed_timeout(
            adapter, "q", k=3, timeout_sec=0.08
        )
    assert out == []
    adapter.search.assert_not_called()
