# PROOF: mekhane/periskope/tests/test_resilience_hardening.py
# PURPOSE: periskope モジュールの resilience_hardening に対するテスト
"""Tests for 3 crack countermeasures (Dialectic Resilience Hardening).

Tests:
  1. SearXNG Circuit Breaker (mark_dead, TTL resurrection, all-dead reset)
  2. Conflict-Aware Compression Prompt (⚔️ CONFLICT marker in prompt)
  3. Dynamic Precision Merge (confidence-weighted, clamp [0.3, 0.7])
"""

import inspect
import time
from unittest.mock import MagicMock

import pytest


# ═══════════════════════════════════════════════════════════════
# 1. SearXNG Circuit Breaker
# ═══════════════════════════════════════════════════════════════


class TestSearXNGCircuitBreaker:
    """Circuit breaker: dead URL tracking with TTL resurrection."""

    def _make_searcher(self, urls=None):
        from mekhane.periskope.searchers.searxng import SearXNGSearcher
        return SearXNGSearcher(base_url=urls or ["http://a:8888", "http://b:8888", "http://c:8888"])

    def test_mark_dead_skips_url(self):
        """Dead URL should be skipped in round-robin."""
        s = self._make_searcher()
        s.mark_dead("http://a:8888")
        urls = [s.base_url for _ in range(6)]
        assert "http://a:8888" not in urls
        assert "http://b:8888" in urls
        assert "http://c:8888" in urls

    def test_ttl_resurrection(self):
        """Dead URL should resurrect after TTL expires."""
        s = self._make_searcher()
        s._DEAD_TTL = 0.1
        s.mark_dead("http://a:8888")
        assert "http://a:8888" not in [s.base_url for _ in range(6)]
        time.sleep(0.15)
        urls = [s.base_url for _ in range(9)]
        assert "http://a:8888" in urls

    def test_all_dead_resets(self):
        """When all URLs are dead, circuit breaker resets and retries all."""
        s = self._make_searcher()
        s.mark_dead("http://a:8888")
        s.mark_dead("http://b:8888")
        s.mark_dead("http://c:8888")
        url = s.base_url
        assert url in ["http://a:8888", "http://b:8888", "http://c:8888"]
        assert len(s._dead_urls) == 0

    def test_single_url_never_fully_dead(self):
        """Single-URL cluster: marking it dead still allows retry."""
        s = self._make_searcher(["http://solo:8888"])
        s.mark_dead("http://solo:8888")
        assert s.base_url == "http://solo:8888"

    def test_mark_dead_called_on_http_error(self):
        """search() failure should trigger mark_dead."""
        s = self._make_searcher(["http://fail:8888"])
        assert hasattr(s, 'mark_dead')
        assert hasattr(s, '_dead_urls')


# ═══════════════════════════════════════════════════════════════
# 2. Conflict-Aware Compression Prompt
# ═══════════════════════════════════════════════════════════════


class TestConflictAwarePrompt:
    """Compression prompt should extract and protect conflict points."""

    def test_prompt_contains_conflict_instruction(self):
        """_llm_compress prompt should include conflict extraction rules."""
        from mekhane.periskope.cognition.context_compressor import DialecticContextBuffer

        buf = DialecticContextBuffer(depth=2)
        source = inspect.getsource(buf._llm_compress)
        assert "CONFLICT" in source

    def test_prompt_contains_conflict_section(self):
        """Prompt should instruct LLM to create a Conflicts section."""
        from mekhane.periskope.cognition.context_compressor import DialecticContextBuffer

        buf = DialecticContextBuffer(depth=2)
        source = inspect.getsource(buf._llm_compress)
        assert "SEPARATELY LIST all points of conflict" in source
        assert "## Conflicts" in source


# ═══════════════════════════════════════════════════════════════
# 3. Dynamic Precision Merge
# ═══════════════════════════════════════════════════════════════


class TestDynamicPrecisionMerge:
    """Quality metrics merge should use dynamic confidence weighting."""

    def _make_qm(self, ndcg=0.7, entropy=2.0, max_ent=3.0, coverage=0.8, overall=0.5):
        """Create a mock QualityMetrics with overall_score."""
        qm = MagicMock()
        qm.ndcg_at_10 = ndcg
        qm.source_entropy = entropy
        qm.max_entropy = max_ent
        qm.coverage_score = coverage
        qm.overall_score = overall
        return qm

    def _merge(self, thesis, anti, depth=2):
        """Call _merge_quality_metrics with real QualityMetrics."""
        from mekhane.periskope.dialectic import DialecticEngine
        return DialecticEngine._merge_quality_metrics(thesis, anti, depth=depth)

    def test_equal_confidence_gives_equal_weight(self):
        """Equal overall_score -> 0.5/0.5 split."""
        thesis = self._make_qm(ndcg=1.0, overall=0.6)
        anti = self._make_qm(ndcg=0.0, overall=0.6)
        result = self._merge(thesis, anti)
        assert abs(result.ndcg_at_10 - 0.5) < 0.01

    def test_higher_thesis_confidence_shifts_weight(self):
        """Higher thesis score -> thesis-biased weight (clamped at 0.7)."""
        thesis = self._make_qm(ndcg=1.0, overall=0.9)
        anti = self._make_qm(ndcg=0.0, overall=0.1)
        result = self._merge(thesis, anti)
        assert abs(result.ndcg_at_10 - 0.7) < 0.01

    def test_higher_anti_confidence_shifts_weight(self):
        """Higher anti score -> anti-biased weight (thesis clamped at 0.3)."""
        thesis = self._make_qm(ndcg=1.0, overall=0.1)
        anti = self._make_qm(ndcg=0.0, overall=0.9)
        result = self._merge(thesis, anti)
        assert abs(result.ndcg_at_10 - 0.3) < 0.01

    def test_zero_confidence_fallback(self):
        """Zero total confidence -> 0.5/0.5 fallback."""
        thesis = self._make_qm(ndcg=1.0, overall=0.0)
        anti = self._make_qm(ndcg=0.0, overall=0.0)
        result = self._merge(thesis, anti)
        assert abs(result.ndcg_at_10 - 0.5) < 0.01

    def test_none_thesis_returns_anti(self):
        """None thesis -> returns anti metrics directly."""
        anti = self._make_qm()
        result = self._merge(None, anti)
        assert result is anti

    def test_none_anti_returns_thesis(self):
        """None anti -> returns thesis metrics directly."""
        thesis = self._make_qm()
        result = self._merge(thesis, None)
        assert result is thesis

    def test_both_none_returns_none(self):
        """Both None -> returns None."""
        assert self._merge(None, None) is None

    def test_clamp_range_standard_depth(self):
        """Weight should always stay in [0.3, 0.7] for depth < 3."""
        thesis = self._make_qm(ndcg=1.0, overall=1.0)
        anti = self._make_qm(ndcg=0.0, overall=0.0001)
        result = self._merge(thesis, anti, depth=2)
        assert abs(result.ndcg_at_10 - 0.7) < 0.01

    def test_clamp_range_l3_depth(self):
        """Weight should expand to [0.1, 0.9] for depth >= 3."""
        thesis = self._make_qm(ndcg=1.0, overall=1.0)
        anti = self._make_qm(ndcg=0.0, overall=0.0001)
        result = self._merge(thesis, anti, depth=3)
        assert abs(result.ndcg_at_10 - 0.9) < 0.01

        thesis2 = self._make_qm(ndcg=1.0, overall=0.0001)
        anti2 = self._make_qm(ndcg=0.0, overall=1.0)
        result2 = self._merge(thesis2, anti2, depth=4)
        assert abs(result2.ndcg_at_10 - 0.1) < 0.01
