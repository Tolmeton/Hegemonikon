# PROOF: mekhane/periskope/tests/test_fallback_controller.py
# PURPOSE: フォールバック機構の単体テスト (3段階段階的緩和)
"""
Tests for fallback_controller.py — Phase 1.9 Progressive Relaxation.

テスト対象:
  - Stage 1: 閾値緩和 (threshold relaxation)
  - Stage 2: ソース展開 (source expansion)
  - Stage 3: 隣接ドメイン (adjacent domain)
  - execute_fallback: 段階的累積とearly return
  - Adaptive Depth 抑制フラグとの連携
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from mekhane.periskope.fallback_controller import (
    FallbackResult,
    _has_enough,
    _min_results_for_depth,
    _stage1_threshold_relaxation,
    _stage2_source_expansion,
    _stage3_adjacent_domain,
    execute_fallback,
)
from mekhane.periskope.models import SearchResult, SearchSource


# ── ヘルパー ──

def _make_result(
    relevance: float = 0.5,
    source: SearchSource = SearchSource.SEARXNG,
    title: str = "Test",
) -> SearchResult:
    """テスト用 SearchResult を生成する。"""
    return SearchResult(
        source=source,
        title=title,
        relevance=relevance,
        metadata={},
    )


def _default_config(**overrides) -> dict:
    """テスト用のデフォルト設定を生成する。"""
    cfg = {
        "fallback": {
            "enabled": True,
            "max_stages": 3,
            "min_results_by_depth": {1: 1, 2: 3, 3: 5},
            "relaxed_relevance_threshold": 0.15,
            "academic_sources": ["semantic_scholar", "gnosis", "gemini_search"],
            "adjacent_domain": {
                "max_concepts": 3,
                "model": "gemini-3-flash-preview",
            },
        },
    }
    cfg["fallback"].update(overrides)
    return cfg


def _run(coro):
    """async テスト用ヘルパー (pytest-asyncio 不要)。"""
    return asyncio.get_event_loop().run_until_complete(coro)


# ── _min_results_for_depth / _has_enough ──

class TestMinResultsForDepth:
    """depth 別の最小結果数閾値テスト。"""

    def test_depth_1(self):
        assert _min_results_for_depth(1, _default_config()) == 1

    def test_depth_2(self):
        assert _min_results_for_depth(2, _default_config()) == 3

    def test_depth_3(self):
        assert _min_results_for_depth(3, _default_config()) == 5

    def test_unknown_depth_falls_back_to_depth_2(self):
        """未定義の depth → depth=2 のデフォルト値を使用。"""
        assert _min_results_for_depth(99, _default_config()) == 3

    def test_custom_config(self):
        """設定でカスタム閾値を指定可能。"""
        cfg = _default_config(min_results_by_depth={1: 2, 2: 5, 3: 10})
        assert _min_results_for_depth(2, cfg) == 5


class TestHasEnough:
    """結果が十分かの判定テスト。"""

    def test_enough_for_depth_2(self):
        results = [_make_result() for _ in range(3)]
        assert _has_enough(results, 2, _default_config()) is True

    def test_not_enough_for_depth_2(self):
        results = [_make_result() for _ in range(2)]
        assert _has_enough(results, 2, _default_config()) is False

    def test_empty_results(self):
        assert _has_enough([], 1, _default_config()) is False


# ── Stage 1: 閾値緩和 ──

class TestStage1ThresholdRelaxation:
    """閾値緩和テスト (pre_rerank_results を緩い閾値で再フィルタ)。"""

    def test_recovers_results_above_relaxed_threshold(self):
        """relevance >= 0.15 の結果が復活する。"""
        initial = [
            _make_result(relevance=0.20, title="Above"),
            _make_result(relevance=0.10, title="Below"),
            _make_result(relevance=0.30, title="Well Above"),
        ]
        recovered = _run(_stage1_threshold_relaxation(initial, _default_config()))
        assert len(recovered) == 2
        titles = {r.title for r in recovered}
        assert "Above" in titles
        assert "Well Above" in titles
        assert "Below" not in titles

    def test_adds_fallback_stage_metadata(self):
        """復活した結果に fallback_stage メタデータが付与される。"""
        initial = [_make_result(relevance=0.20)]
        recovered = _run(_stage1_threshold_relaxation(initial, _default_config()))
        assert recovered[0].metadata["fallback_stage"] == "threshold_relaxation"

    def test_empty_when_all_below_threshold(self):
        """全ての結果が緩和閾値以下 → 空リスト。"""
        initial = [_make_result(relevance=0.05), _make_result(relevance=0.10)]
        recovered = _run(_stage1_threshold_relaxation(initial, _default_config()))
        assert len(recovered) == 0

    def test_custom_relaxed_threshold(self):
        """カスタム緩和閾値を使用可能。"""
        initial = [_make_result(relevance=0.25)]
        cfg = _default_config(relaxed_relevance_threshold=0.30)
        recovered = _run(_stage1_threshold_relaxation(initial, cfg))
        # 0.25 < 0.30 なので復活しない
        assert len(recovered) == 0


# ── Stage 2: ソース展開 ──

class TestStage2SourceExpansion:
    """ソース展開テスト (差集合で未検索ソースのみ追加)。"""

    def test_searches_only_new_sources(self):
        """already_searched に含まれないソースのみ検索する。"""
        engine = MagicMock()
        new_results = [_make_result(source=SearchSource.SEMANTIC_SCHOLAR, title="New")]
        engine._phase_search = AsyncMock(
            return_value=(new_results, {"semantic_scholar": 1}),
        )

        already = {"searxng", "brave"}
        results, counts = _run(_stage2_source_expansion(
            engine, "test query", already, _default_config(),
        ))

        # _phase_search に渡されたソースが差集合になっていること
        call_args = engine._phase_search.call_args
        called_sources = call_args[0][1]
        assert "searxng" not in called_sources
        assert "brave" not in called_sources
        assert len(results) == 1
        assert results[0].metadata["fallback_stage"] == "source_expansion"

    def test_no_new_sources_returns_empty(self):
        """全てのソースが検索済み → 空リスト。"""
        engine = MagicMock()
        already = {"semantic_scholar", "gnosis", "gemini_search"}
        results, counts = _run(_stage2_source_expansion(
            engine, "test query", already, _default_config(),
        ))
        assert results == []
        assert counts == {}
        # _phase_search は呼ばれないこと
        engine._phase_search.assert_not_called()


# ── Stage 3: 隣接ドメイン ──

class TestStage3AdjacentDomain:
    """隣接ドメイン展開テスト (LLM 概念生成 + 個別検索)。"""

    def test_generates_concepts_and_searches(self):
        """LLM で概念を生成し、各概念を検索する。"""
        engine = MagicMock()
        engine.cortex = MagicMock()
        engine.cortex.generate = AsyncMock(
            return_value="Markov category theory\nBayesian inference geometry\nCategorical probability",
        )
        engine._phase_search = AsyncMock(
            return_value=(
                [_make_result(title="Adjacent Result")],
                {"searxng": 1},
            ),
        )

        results, counts, concepts = _run(_stage3_adjacent_domain(
            engine, "FEP category theory", {"searxng"}, _default_config(),
        ))

        assert len(concepts) == 3
        # 各概念ごとに _phase_search が呼ばれる
        assert engine._phase_search.call_count == 3
        # メタデータに adjacent_domain と adjacent_concept が付与される
        for r in results:
            assert r.metadata["fallback_stage"] == "adjacent_domain"
            assert "adjacent_concept" in r.metadata

    def test_no_cortex_returns_empty(self):
        """LLM クライアントが存在しない → 空リスト。"""
        engine = MagicMock(spec=[])  # cortex 属性なし
        results, counts, concepts = _run(_stage3_adjacent_domain(
            engine, "test", {"searxng"}, _default_config(),
        ))
        assert results == []
        assert concepts == []


# ── execute_fallback (統合テスト) ──

class TestExecuteFallback:
    """段階的フォールバック統合テスト。"""

    def test_disabled_returns_empty(self):
        """fallback.enabled=false → 空の FallbackResult。"""
        engine = MagicMock()
        cfg = _default_config(enabled=False)
        result = _run(execute_fallback(
            engine, "query", [], set(), depth=2, config=cfg,
        ))
        assert result.search_results == []
        assert result.stages_executed == []

    def test_stage1_sufficient_stops_early(self):
        """Stage 1 で十分な結果 → Stage 2/3 はスキップ。"""
        engine = MagicMock()
        # 3件以上復活すれば depth=2 で十分
        initial = [_make_result(relevance=0.20) for _ in range(5)]
        result = _run(execute_fallback(
            engine, "query", initial, set(), depth=2,
            config=_default_config(),
        ))
        assert "threshold_relaxation" in result.stages_executed
        assert "source_expansion" not in result.stages_executed
        assert len(result.search_results) >= 3

    def test_stages_accumulate(self):
        """Stage 1 不足 → Stage 2 が実行される。"""
        engine = MagicMock()
        engine._phase_search = AsyncMock(
            return_value=(
                [_make_result(title=f"S2-{i}") for i in range(5)],
                {"semantic_scholar": 5},
            ),
        )
        # Stage 1: 1件しか復活しない → 不足
        initial = [_make_result(relevance=0.20)]
        result = _run(execute_fallback(
            engine, "query", initial,
            enabled_sources={"searxng"},
            depth=2,
            config=_default_config(),
        ))
        assert "threshold_relaxation" in result.stages_executed
        assert "source_expansion" in result.stages_executed

    def test_max_stages_limits_execution(self):
        """max_stages=1 なら Stage 2/3 は実行しない。"""
        engine = MagicMock()
        initial = [_make_result(relevance=0.05)]  # 復活しない
        cfg = _default_config(max_stages=1)
        result = _run(execute_fallback(
            engine, "query", initial, set(), depth=2, config=cfg,
        ))
        assert "threshold_relaxation" in result.stages_executed
        assert "source_expansion" not in result.stages_executed
        assert "adjacent_domain" not in result.stages_executed

    def test_progress_callback_invoked(self):
        """progress_callback が各ステージで呼ばれる。"""
        engine = MagicMock()
        callback = MagicMock()
        initial = [_make_result(relevance=0.20) for _ in range(5)]
        _run(execute_fallback(
            engine, "query", initial, set(), depth=2,
            config=_default_config(),
            progress_callback=callback,
        ))
        # stage1_start + stage1_done (少なくとも2回)
        assert callback.call_count >= 2
        phases = [c.args[0].phase for c in callback.call_args_list]
        assert "fallback_stage1_start" in phases
        assert "fallback_stage1_done" in phases
