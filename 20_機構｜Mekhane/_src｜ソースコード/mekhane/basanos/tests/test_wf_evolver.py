# PROOF: mekhane/basanos/tests/test_wf_evolver.py
# PURPOSE: basanos モジュールの wf_evolver に対するテスト
"""Tests for WFEvolver — WF 品質トラッキング + 進化エンジン。

TrendAnalyzer テストの構造に準拠。合成 WF データでテスト。
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from mekhane.basanos.wf_evolver import WFProfile, WFQualityScorer, WFTrendAnalyzer, WFMutator


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Fixtures — 合成 WF データ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PERFECT_WF = """\
---
description: Perfect workflow for testing
version: "1.0"
---
# Perfect Workflow

## Overview

This is a well-structured workflow with proper frontmatter,
headings, and content density.

## Steps

1. First step with details
2. Second step with details
3. Third step with details

## Output

The expected output format is:
- Item one
- Item two
- Item three

## Notes

Additional context and references for this workflow.
This section provides supporting information.
"""

MINIMAL_WF = """\
---
description: Minimal workflow
---
# Minimal

A minimal workflow.
"""

BROKEN_WF = """\
## Missing H1

No frontmatter here.

```python
unclosed code block
"""

EMPTY_WF = ""

STUB_WF = "TODO: implement this workflow"


@pytest.fixture
def perfect_wf_dir(tmp_path):
    """WF ディレクトリに perfect + minimal + broken を配置。"""
    wf_dir = tmp_path / "workflows"
    wf_dir.mkdir()

    (wf_dir / "perfect.md").write_text(PERFECT_WF, "utf-8")
    (wf_dir / "minimal.md").write_text(MINIMAL_WF, "utf-8")
    (wf_dir / "broken.md").write_text(BROKEN_WF, "utf-8")
    (wf_dir / "stub.md").write_text(STUB_WF, "utf-8")

    # Subdirectory
    sub = wf_dir / "sub"
    sub.mkdir()
    (sub / "nested.md").write_text(PERFECT_WF, "utf-8")

    return wf_dir


@pytest.fixture
def reviews_dir_with_data(tmp_path):
    """5日分の WF レビューデータを生成。"""
    reviews = tmp_path / "wf_reviews"
    reviews.mkdir()

    today = datetime.now()
    for i in range(5):
        date = (today - timedelta(days=4 - i)).strftime("%Y-%m-%d")
        scores = {
            "perfect.md": 0.9 + i * 0.01,  # Improving
            "minimal.md": 0.5,               # Stable low
            "broken.md": 0.3 - i * 0.02,    # Declining
        }
        review = {
            "timestamp": f"{date}T06:00:00",
            "wf_count": len(scores),
            "scores": scores,
            "mean_score": round(sum(scores.values()) / len(scores), 3),
            "weak_wfs": [k for k, v in scores.items() if v < 0.7],
        }
        (reviews / f"{date}.json").write_text(
            json.dumps(review, ensure_ascii=False, indent=2), "utf-8"
        )

    return reviews


@pytest.fixture
def scorer():
    return WFQualityScorer()


@pytest.fixture
def analyzer_with_data(tmp_path, reviews_dir_with_data, perfect_wf_dir):
    return WFTrendAnalyzer(
        wf_dir=perfect_wf_dir,
        reviews_dir=reviews_dir_with_data,
        days=14,
    )


@pytest.fixture
def empty_analyzer(tmp_path):
    return WFTrendAnalyzer(
        wf_dir=tmp_path / "no_wfs",
        reviews_dir=tmp_path / "no_reviews",
        days=14,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WFQualityScorer Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestQualityScorerBasics:
    def test_perfect_wf_high_score(self, scorer):
        score = scorer.score(PERFECT_WF)
        assert score >= 0.75, f"Perfect WF should score >= 0.75, got {score}"

    def test_minimal_wf_medium_score(self, scorer):
        score = scorer.score(MINIMAL_WF)
        assert 0.3 <= score <= 0.8, f"Minimal WF should score 0.3-0.8, got {score}"

    def test_broken_wf_low_score(self, scorer):
        score = scorer.score(BROKEN_WF)
        assert score < 0.6, f"Broken WF should score < 0.6, got {score}"

    def test_empty_wf_zero(self, scorer):
        assert scorer.score(EMPTY_WF) == 0.0

    def test_stub_wf_low(self, scorer):
        score = scorer.score(STUB_WF)
        assert score < 0.4, f"Stub WF should score < 0.4, got {score}"

    def test_score_range(self, scorer):
        """All scores should be in [0.0, 1.0]."""
        for content in [PERFECT_WF, MINIMAL_WF, BROKEN_WF, EMPTY_WF, STUB_WF]:
            score = scorer.score(content)
            assert 0.0 <= score <= 1.0, f"Score {score} out of range"


class TestQualityScorerDetail:
    def test_detail_keys(self, scorer):
        detail = scorer.score_detail(PERFECT_WF)
        assert set(detail.keys()) == {"frontmatter", "sections", "content_density", "formatting", "hash_consistency"}

    def test_perfect_frontmatter(self, scorer):
        """Perfect WF has good frontmatter."""
        detail = scorer.score_detail(PERFECT_WF)
        assert detail["frontmatter"] >= 0.8

    def test_broken_frontmatter(self, scorer):
        """Broken WF has no frontmatter."""
        detail = scorer.score_detail(BROKEN_WF)
        assert detail["frontmatter"] == 0.0

    def test_broken_formatting(self, scorer):
        """Broken WF has unclosed code block."""
        detail = scorer.score_detail(BROKEN_WF)
        assert detail["formatting"] < 0.5


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WFProfile Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestWFProfile:
    def test_empty_profile(self):
        p = WFProfile(path="test.md")
        assert p.quality == 0.0
        assert p.trend == 0.0
        assert not p.needs_evolution

    def test_quality_returns_latest(self):
        p = WFProfile(path="test.md", quality_scores=[0.5, 0.6, 0.8])
        assert p.quality == 0.8

    def test_trend_positive(self):
        """Improving scores → positive trend."""
        p = WFProfile(path="test.md", quality_scores=[0.3, 0.5, 0.7, 0.9])
        assert p.trend > 0

    def test_trend_negative(self):
        """Declining scores → negative trend."""
        p = WFProfile(path="test.md", quality_scores=[0.9, 0.7, 0.5, 0.3])
        assert p.trend < 0

    def test_trend_stable(self):
        """Same scores → trend ≈ 0."""
        p = WFProfile(path="test.md", quality_scores=[0.5, 0.5, 0.5])
        assert abs(p.trend) < 0.01

    def test_needs_evolution_low_quality(self):
        p = WFProfile(path="test.md", quality_scores=[0.4])
        assert p.needs_evolution

    def test_needs_evolution_declining(self):
        p = WFProfile(path="test.md", quality_scores=[0.9, 0.8, 0.7, 0.6])
        assert p.needs_evolution


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WFTrendAnalyzer Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestScanWorkflows:
    def test_scan_finds_all(self, perfect_wf_dir):
        analyzer = WFTrendAnalyzer(wf_dir=perfect_wf_dir, reviews_dir=perfect_wf_dir / "reviews")
        scores = analyzer.scan_workflows()
        assert len(scores) == 5  # perfect, minimal, broken, stub, sub/nested

    def test_scan_empty_dir(self, tmp_path):
        analyzer = WFTrendAnalyzer(wf_dir=tmp_path / "nope", reviews_dir=tmp_path / "reviews")
        scores = analyzer.scan_workflows()
        assert scores == {}

    def test_perfect_scores_high(self, perfect_wf_dir):
        analyzer = WFTrendAnalyzer(wf_dir=perfect_wf_dir, reviews_dir=perfect_wf_dir / "reviews")
        scores = analyzer.scan_workflows()
        assert scores["perfect.md"] >= 0.75


class TestLoadReviews:
    def test_load_all(self, analyzer_with_data):
        reviews = analyzer_with_data.load_reviews()
        assert len(reviews) == 5

    def test_empty(self, empty_analyzer):
        reviews = empty_analyzer.load_reviews()
        assert reviews == []


class TestWFProfiles:
    def test_profiles_count(self, analyzer_with_data):
        profiles = analyzer_with_data.wf_profiles()
        assert len(profiles) == 3  # perfect, minimal, broken

    def test_perfect_improving(self, analyzer_with_data):
        profiles = analyzer_with_data.wf_profiles()
        p = profiles["perfect.md"]
        assert p.trend > 0  # Scores increase over time

    def test_broken_declining(self, analyzer_with_data):
        profiles = analyzer_with_data.wf_profiles()
        p = profiles["broken.md"]
        assert p.trend < 0  # Scores decrease over time


class TestWeakWorkflows:
    def test_weak_detection(self, analyzer_with_data):
        weak = analyzer_with_data.weak_workflows(threshold=0.7)
        paths = [w.path for w in weak]
        assert "broken.md" in paths
        assert "minimal.md" in paths

    def test_weak_sorted_by_quality(self, analyzer_with_data):
        weak = analyzer_with_data.weak_workflows()
        if len(weak) >= 2:
            assert weak[0].quality <= weak[1].quality

    def test_empty_data(self, empty_analyzer):
        assert empty_analyzer.weak_workflows() == []


class TestSaveReview:
    def test_save_creates_file(self, tmp_path, perfect_wf_dir):
        reviews_dir = tmp_path / "reviews"
        analyzer = WFTrendAnalyzer(
            wf_dir=perfect_wf_dir,
            reviews_dir=reviews_dir,
        )
        path = analyzer.save_review()
        assert path.exists()
        data = json.loads(path.read_text())
        assert "scores" in data
        assert data["wf_count"] == 5

    def test_save_with_scores(self, tmp_path, perfect_wf_dir):
        reviews_dir = tmp_path / "reviews"
        analyzer = WFTrendAnalyzer(
            wf_dir=perfect_wf_dir,
            reviews_dir=reviews_dir,
        )
        scores = {"test.md": 0.85}
        path = analyzer.save_review(scores=scores)
        data = json.loads(path.read_text())
        assert data["scores"]["test.md"] == 0.85


class TestLogEvolution:
    def test_log_creates_file(self, tmp_path):
        log_file = tmp_path / "evo.jsonl"
        analyzer = WFTrendAnalyzer(
            wf_dir=tmp_path,
            reviews_dir=tmp_path,
        )
        analyzer.log_evolution(
            wf_path="test.md",
            original_score=0.5,
            mutated_score=0.7,
            mutation_type="restructure",
            kept=True,
            log_file=log_file,
        )

        assert log_file.exists()
        entry = json.loads(log_file.read_text().strip())
        assert entry["wf_path"] == "test.md"
        assert entry["delta"] == 0.2
        assert entry["kept"] is True


class TestSummary:
    def test_summary_with_data(self, analyzer_with_data):
        s = analyzer_with_data.summary()
        assert "WF Trend Analysis" in s
        assert "Weak" in s or "Mean" in s

    def test_summary_empty(self, empty_analyzer):
        s = empty_analyzer.summary()
        assert "No data" in s


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Phase B: WFMutator + Evolution Loop Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestWFMutator:
    def test_available_strategies(self):
        strategies = WFMutator.available_strategies()
        assert len(strategies) == 5
        assert "clarify" in strategies
        assert "restructure" in strategies
        assert "densify" in strategies
        assert "decompose" in strategies
        assert "strengthen" in strategies

    def test_build_prompt_contains_content(self):
        prompt = WFMutator.build_prompt(PERFECT_WF, "clarify")
        assert "元の WF" in prompt
        assert "Perfect Workflow" in prompt  # Content preserved
        assert "frontmatter" in prompt  # Instruction present

    def test_build_prompt_unknown_strategy(self):
        with pytest.raises(ValueError, match="Unknown strategy"):
            WFMutator.build_prompt(PERFECT_WF, "nonexistent")

    def test_build_prompt_all_strategies(self):
        """All strategies produce non-empty prompts."""
        for strategy in WFMutator.available_strategies():
            prompt = WFMutator.build_prompt(MINIMAL_WF, strategy)
            assert len(prompt) > 100


class TestEvolve:
    def test_evolve_generates_results(self, tmp_path):
        analyzer = WFTrendAnalyzer(
            wf_dir=tmp_path, reviews_dir=tmp_path / "reviews",
        )
        results = analyzer.evolve("test.md", PERFECT_WF)
        assert len(results) == 5  # 5 strategies
        for r in results:
            assert r["wf_path"] == "test.md"
            assert r["original_score"] > 0
            assert r["prompt"] is not None
            assert r["mutated_content"] is None  # Not yet filled
            assert r["kept"] is None

    def test_evolve_specific_strategies(self, tmp_path):
        analyzer = WFTrendAnalyzer(
            wf_dir=tmp_path, reviews_dir=tmp_path / "reviews",
        )
        results = analyzer.evolve("test.md", PERFECT_WF, mutation_types=["clarify"])
        assert len(results) == 1
        assert results[0]["mutation_type"] == "clarify"


class TestEvaluateMutation:
    def test_evaluate_keeps_improvement(self, tmp_path):
        analyzer = WFTrendAnalyzer(
            wf_dir=tmp_path, reviews_dir=tmp_path / "reviews",
        )
        log_file = tmp_path / "evo.jsonl"

        # Simulate: original is broken, mutation is perfect
        result = {
            "wf_path": "test.md",
            "mutation_type": "restructure",
            "original_score": 0.3,
            "prompt": "...",
            "mutated_content": None,
            "mutated_score": None,
            "kept": None,
        }
        evaluated = analyzer.evaluate_mutation(result, PERFECT_WF, log_file=log_file)

        assert evaluated["kept"] is True
        assert evaluated["mutated_score"] > 0.3
        assert log_file.exists()

    def test_evaluate_discards_regression(self, tmp_path):
        analyzer = WFTrendAnalyzer(
            wf_dir=tmp_path, reviews_dir=tmp_path / "reviews",
        )
        log_file = tmp_path / "evo.jsonl"

        result = {
            "wf_path": "test.md",
            "mutation_type": "densify",
            "original_score": 0.9,
            "prompt": "...",
            "mutated_content": None,
            "mutated_score": None,
            "kept": None,
        }
        # Mutation degrades to broken
        evaluated = analyzer.evaluate_mutation(result, BROKEN_WF, log_file=log_file)

        assert evaluated["kept"] is False
        assert evaluated["mutated_score"] < 0.9


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Phase C: evolve_runner Integration Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from unittest.mock import patch, MagicMock
from mekhane.basanos.evolve_runner import mutate_wf, evolve_one, run


class _FakeLLMResponse:
    """Mock LLMResponse for CortexClient.ask()."""
    def __init__(self, text: str):
        self.text = text


class TestMutateWF:
    """mutate_wf() — CortexClient をモックして変異を検証。"""

    @patch("mekhane.basanos.evolve_runner._get_cortex_client")
    def test_mutate_returns_text(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.ask.return_value = _FakeLLMResponse(PERFECT_WF)
        mock_get_client.return_value = mock_client

        result = mutate_wf(MINIMAL_WF, "clarify")
        assert result == PERFECT_WF
        mock_client.ask.assert_called_once()

    @patch("mekhane.basanos.evolve_runner._get_cortex_client")
    def test_mutate_passes_system_instruction(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.ask.return_value = _FakeLLMResponse("mutated")
        mock_get_client.return_value = mock_client

        mutate_wf(MINIMAL_WF, "restructure")

        call_kwargs = mock_client.ask.call_args
        assert "system_instruction" in call_kwargs.kwargs
        assert "Hegemonikón" in call_kwargs.kwargs["system_instruction"]


class TestEvolveOne:
    """evolve_one() — 単一 WF の進化ループをテスト。"""

    @patch("mekhane.basanos.evolve_runner.mutate_wf")
    def test_evolve_one_dry_run(self, mock_mutate, tmp_path):
        """Dry run: ファイルが変更されないことを確認。"""
        wf_dir = tmp_path / "wfs"
        wf_dir.mkdir()
        wf_file = wf_dir / "broken.md"
        wf_file.write_text(BROKEN_WF, "utf-8")
        original = wf_file.read_text()

        mock_mutate.return_value = PERFECT_WF

        analyzer = WFTrendAnalyzer(wf_dir=wf_dir, reviews_dir=tmp_path / "reviews")
        results = evolve_one(
            wf_path=wf_file,
            analyzer=analyzer,
            strategies=["clarify"],
            apply=False,
            log_file=tmp_path / "evo.jsonl",
        )

        assert len(results) == 1
        assert results[0]["kept"] is True
        assert wf_file.read_text() == original  # ファイル未変更

    @patch("mekhane.basanos.evolve_runner.mutate_wf")
    def test_evolve_one_apply_writes_file(self, mock_mutate, tmp_path):
        """Apply: best mutation が WF ファイルに書き込まれることを確認。"""
        wf_dir = tmp_path / "wfs"
        wf_dir.mkdir()
        wf_file = wf_dir / "broken.md"
        wf_file.write_text(BROKEN_WF, "utf-8")

        mock_mutate.return_value = PERFECT_WF

        analyzer = WFTrendAnalyzer(wf_dir=wf_dir, reviews_dir=tmp_path / "reviews")
        results = evolve_one(
            wf_path=wf_file,
            analyzer=analyzer,
            strategies=["clarify"],
            apply=True,
            log_file=tmp_path / "evo.jsonl",
        )

        assert results[0]["kept"] is True
        assert wf_file.read_text("utf-8") == PERFECT_WF  # ファイル更新
        assert (wf_dir / "broken.md.bak").exists()  # バックアップ作成

    @patch("mekhane.basanos.evolve_runner.mutate_wf")
    def test_evolve_one_discard_no_apply(self, mock_mutate, tmp_path):
        """既にスコアが高い WF → 変異は discard + apply しても変更なし。"""
        wf_dir = tmp_path / "wfs"
        wf_dir.mkdir()
        wf_file = wf_dir / "perfect.md"
        wf_file.write_text(PERFECT_WF, "utf-8")

        # 変異結果が broken = スコア劣化
        mock_mutate.return_value = BROKEN_WF

        analyzer = WFTrendAnalyzer(wf_dir=wf_dir, reviews_dir=tmp_path / "reviews")
        results = evolve_one(
            wf_path=wf_file,
            analyzer=analyzer,
            strategies=["clarify"],
            apply=True,  # apply でも discard なら書き込まない
            log_file=tmp_path / "evo.jsonl",
        )

        assert results[0]["kept"] is False
        assert wf_file.read_text("utf-8") == PERFECT_WF  # 変更なし


class TestRunOrchestrator:
    """run() — メインオーケストレーション。"""

    @patch("mekhane.basanos.evolve_runner.mutate_wf")
    def test_run_with_target(self, mock_mutate, perfect_wf_dir, tmp_path):
        """特定 WF をターゲットにした実行。"""
        mock_mutate.return_value = PERFECT_WF

        summary = run(
            wf_dir=perfect_wf_dir,
            target_wf="broken.md",
            strategies=["clarify"],
            apply=False,
        )

        assert summary["targets"] == 1
        assert summary["mutations_total"] == 1
        assert summary["applied"] is False

    @patch("mekhane.basanos.evolve_runner.mutate_wf")
    def test_run_top_n(self, mock_mutate, perfect_wf_dir, tmp_path):
        """弱い WF 上位 N 件の自動選定。"""
        mock_mutate.return_value = PERFECT_WF

        summary = run(
            wf_dir=perfect_wf_dir,
            top_n=2,
            strategies=["clarify"],
            apply=False,
        )

        assert summary["targets"] == 2
        assert summary["mutations_total"] == 2

    def test_run_nonexistent_target(self, tmp_path):
        """存在しない WF をターゲット → エラー。"""
        wf_dir = tmp_path / "wfs"
        wf_dir.mkdir()

        summary = run(
            wf_dir=wf_dir,
            target_wf="nonexistent.md",
            apply=False,
        )

        assert "error" in summary

