# PROOF: [L3/テスト] <- mekhane/symploke/tests/test_search_factory.py 検索エンジンファクトリの振る舞い検証
"""
Tests for mekhane.symploke.search.search_factory.
Verifies caching (singleton behavior per source set), invalid source handling,
and graceful error handling during domain index initialization (G1/G5 validation).
"""

import pytest
from unittest.mock import patch, MagicMock
from mekhane.symploke.search.search_factory import get_search_engine, clear_cache

@pytest.fixture(autouse=True)
def run_around_tests():
    # Setup: clear cache before each test
    clear_cache()
    yield
    # Teardown: clear cache after each test
    clear_cache()

def test_get_search_engine_caching():
    """Test that requesting the same sources returns the cached SearchEngine instance."""
    sources = ["gnosis", "sophia"]
    
    engine1, errors1 = get_search_engine(sources)
    engine2, errors2 = get_search_engine(sources)
    
    assert engine1 is engine2, "Repeated calls with same sources should return the same instance"
    assert errors1 == []
    assert errors2 == []
    assert len(engine1._indices) == 2, "Should have registered two indices"

def test_get_search_engine_unordered_sources_cache():
    """Test that order of sources doesn't matter for caching (frozenset key)."""
    engine1, _ = get_search_engine(["sophia", "kairos"])
    engine2, _ = get_search_engine(["kairos", "sophia"])
    
    assert engine1 is engine2, "Different order of same sources should hit the cache"

def test_get_search_engine_invalid_source_skipped():
    """Test that invalid source names are silently skipped without erroring."""
    sources = ["gnosis", "invalid_source_123"]
    engine, errors = get_search_engine(sources)
    
    # Invalid sources are just ignored (not added to errors, as they don't fail initialization)
    assert errors == []
    # Only gnosis should be registered
    assert len(engine._indices) == 1
    assert "gnosis" in engine._indices

@patch("mekhane.symploke.indices.sophia.SophiaIndex.initialize")
def test_get_search_engine_initialization_error_handled(mock_sophia_init):
    """Test that if an index fails to initialize, it is caught and reported in errors."""
    # Force initialize() to raise an exception for Sophia
    mock_sophia_init.side_effect = Exception("Simulated DB connection failure")
    
    sources = ["gnosis", "sophia"]
    engine, errors = get_search_engine(sources)
    
    # Sophia should be in errors
    assert "sophia" in errors
    
    # Gnosis should still be successfully registered
    assert "gnosis" in engine._indices
    assert "sophia" not in engine._indices
    assert len(engine._indices) == 1
