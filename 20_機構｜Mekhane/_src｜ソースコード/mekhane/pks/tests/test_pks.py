# PROOF: mekhane/pks/tests/test_pks.py
# PURPOSE: pks モジュールの pks に対するテスト
# PURPOSE: PKS v2 全モジュールの pytest テスト
"""
PKS v2 テストスイート

対象:
- pks_engine: KnowledgeNugget, SessionContext, ContextTracker,
              RelevanceDetector, SerendipityScorer, PushController
- narrator: PKSNarrator, Narrative, NarrativeSegment
- matrix_view: PKSMatrixView, PKSBacklinks
- sync_watcher: SyncWatcher, FileChange
- links: LinkEngine, CitationGraph
"""

from pathlib import Path

import pytest

from mekhane.pks.pks_engine import (
    ContextTracker,
    KnowledgeNugget,
    PushController,
    RelevanceDetector,
    SerendipityScorer,
    SessionContext,
)
from mekhane.pks.narrator import PKSNarrator
from mekhane.pks.matrix_view import PKSBacklinks, PKSMatrixView
from mekhane.pks.sync_watcher import SyncWatcher
from mekhane.pks.links.link_engine import WIKILINK_PATTERN
from mekhane.pks.links.citation_graph import Citation, CitationGraph, CitationType


# =============================================================================
# Fixtures
# =============================================================================


# PURPOSE: 標準テスト用 KnowledgeNugget
@pytest.fixture
def sample_nugget():
    """標準テスト用 KnowledgeNugget"""
    return KnowledgeNugget(
        title="Active Inference and FEP",
        abstract="This paper explores active inference under the free energy principle.",
        source="arxiv",
        relevance_score=0.85,
        url="https://arxiv.org/abs/2401.00001",
        authors="Friston et al.",
        push_reason="FEP トピックに関連",
    )


# PURPOSE: low_score_nugget の処理
@pytest.fixture
def low_score_nugget():
    """Verify low score nugget behavior."""
    return KnowledgeNugget(
        title="Cooking Recipes",
        abstract="A guide to making pasta.",
        source="blog",
        relevance_score=0.3,
        push_reason="低関連",
    )


# PURPOSE: multi_nuggets の処理
@pytest.fixture
def multi_nuggets(sample_nugget, low_score_nugget):
    """Verify multi nuggets behavior."""
    return [
        sample_nugget,
        low_score_nugget,
        KnowledgeNugget(
            title="Stoic Philosophy",
            abstract="Marcus Aurelius on self-governance.",
            source="semantic_scholar",
            relevance_score=0.72,
            push_reason="哲学的基盤",
        ),
    ]


# PURPOSE: テスト用一時ディレクトリ
@pytest.fixture
def tmp_state_dir(tmp_path):
    """テスト用一時ディレクトリ"""
    return tmp_path / "pks_state"


# =============================================================================
# KnowledgeNugget
# =============================================================================


# PURPOSE: Test knowledge nugget の実装
class TestKnowledgeNugget:
    # PURPOSE: to_markdown_contains_title をテストする
    """Test suite for knowledge nugget."""
    # PURPOSE: Verify to markdown contains title behaves correctly
    def test_to_markdown_contains_title(self, sample_nugget):
        """Verify to markdown contains title behavior."""
        md = sample_nugget.to_markdown()
        assert "Active Inference and FEP" in md

    # PURPOSE: to_markdown_contains_abstract をテストする
    def test_to_markdown_contains_abstract(self, sample_nugget):
        """Verify to markdown contains abstract behavior."""
        md = sample_nugget.to_markdown()
        assert "active inference" in md.lower()

    # PURPOSE: to_markdown_contains_source をテストする
    def test_to_markdown_contains_source(self, sample_nugget):
        """Verify to markdown contains source behavior."""
        md = sample_nugget.to_markdown()
        assert "arxiv" in md

    # PURPOSE: to_markdown_contains_url をテストする
    def test_to_markdown_contains_url(self, sample_nugget):
        """Verify to markdown contains url behavior."""
        md = sample_nugget.to_markdown()
        assert "https://arxiv.org" in md

    # PURPOSE: to_markdown_without_url をテストする
    def test_to_markdown_without_url(self, low_score_nugget):
        """Verify to markdown without url behavior."""
        md = low_score_nugget.to_markdown()
        assert "Cooking" in md


# =============================================================================
# SessionContext
# =============================================================================


# PURPOSE: Test session context の実装
class TestSessionContext:
    # PURPOSE: to_embedding_text_includes_topics をテストする
    """Test suite for session context."""
    # PURPOSE: Verify to embedding text includes topics behaves correctly
    def test_to_embedding_text_includes_topics(self):
        """Verify to embedding text includes topics behavior."""
        ctx = SessionContext(topics=["FEP", "CCL"])
        text = ctx.to_embedding_text()
        assert "FEP" in text
        assert "CCL" in text

    # PURPOSE: to_embedding_text_includes_queries をテストする
    def test_to_embedding_text_includes_queries(self):
        """Verify to embedding text includes queries behavior."""
        ctx = SessionContext(recent_queries=["active inference implementation"])
        text = ctx.to_embedding_text()
        assert "active inference" in text

    # PURPOSE: to_embedding_text_includes_workflows をテストする
    def test_to_embedding_text_includes_workflows(self):
        """Verify to embedding text includes workflows behavior."""
        ctx = SessionContext(active_workflows=["/boot", "/dia"])
        text = ctx.to_embedding_text()
        assert "/boot" in text

    # PURPOSE: empty_context_returns_text をテストする
    def test_empty_context_returns_text(self):
        """Verify empty context returns text behavior."""
        ctx = SessionContext()
        text = ctx.to_embedding_text()
        assert isinstance(text, str)


# =============================================================================
# ContextTracker
# =============================================================================


# PURPOSE: Test context tracker の実装
class TestContextTracker:
    # PURPOSE: update_topics をテストする
    """Test suite for context tracker."""
    # PURPOSE: Verify update topics behaves correctly
    def test_update_topics(self):
        """Verify update topics behavior."""
        tracker = ContextTracker()
        tracker.update_topics(["FEP", "Attractor"])
        assert "FEP" in tracker.context.topics

    # PURPOSE: add_query_appends をテストする
    def test_add_query_appends(self):
        """Verify add query appends behavior."""
        tracker = ContextTracker()
        tracker.add_query("test query")
        tracker.add_query("another query")
        assert "test query" in tracker.context.recent_queries
        assert "another query" in tracker.context.recent_queries

    # PURPOSE: add_query_deduplicates をテストする
    def test_add_query_deduplicates(self):
        """Verify add query deduplicates behavior."""
        tracker = ContextTracker()
        tracker.add_query("test query")
        tracker.add_query("test query")
        assert tracker.context.recent_queries.count("test query") == 1

    # PURPOSE: set_workflows をテストする
    def test_set_workflows(self):
        """Verify set workflows behavior."""
        tracker = ContextTracker()
        tracker.set_workflows(["/boot", "/dia"])
        assert "/boot" in tracker.context.active_workflows

    # PURPOSE: load_from_handoff_nonexistent_file をテストする
    def test_load_from_handoff_nonexistent_file(self):
        """Verify load from handoff nonexistent file behavior."""
        tracker = ContextTracker()
        tracker.load_from_handoff(Path("/nonexistent/handoff.md"))
        # Should not raise — graceful degradation
        assert tracker.context.handoff_keywords == [] or isinstance(
            tracker.context.handoff_keywords, list
        )


# =============================================================================
# RelevanceDetector
# =============================================================================


# PURPOSE: Test relevance detector の実装
class TestRelevanceDetector:
    # PURPOSE: high_relevance_passes_threshold をテストする
    """Test suite for relevance detector."""
    # PURPOSE: Verify high relevance passes threshold behaves correctly
    def test_high_relevance_passes_threshold(self):
        """Verify high relevance passes threshold behavior."""
        detector = RelevanceDetector(threshold=0.5)
        results = [
            {
                "title": "FEP Paper",
                "abstract": "Active inference.",
                "source": "arxiv",
                "_distance": 0.3,
                "url": "#",
                "authors": "A",
            },
        ]
        ctx = SessionContext(topics=["FEP"])
        nuggets = detector.score(ctx, results)
        assert len(nuggets) >= 1
        assert nuggets[0].title == "FEP Paper"

    # PURPOSE: low_relevance_filtered をテストする
    def test_low_relevance_filtered(self):
        """Verify low relevance filtered behavior."""
        detector = RelevanceDetector(threshold=0.9)
        results = [
            {
                "title": "Irrelevant",
                "abstract": "Cooking.",
                "source": "blog",
                "_distance": 1.5,
                "url": "#",
                "authors": "B",
            },
        ]
        ctx = SessionContext(topics=["FEP"])
        nuggets = detector.score(ctx, results)
        assert len(nuggets) == 0

    # PURPOSE: empty_results をテストする
    def test_empty_results(self):
        """Verify empty results behavior."""
        detector = RelevanceDetector()
        ctx = SessionContext(topics=["FEP"])
        nuggets = detector.score(ctx, [])
        assert nuggets == []

    # PURPOSE: push_reason_generated をテストする
    def test_push_reason_generated(self):
        """Verify push reason generated behavior."""
        detector = RelevanceDetector(threshold=0.3)
        results = [
            {
                "title": "FEP",
                "abstract": "AI",
                "source": "arxiv",
                "_distance": 0.2,
                "url": "#",
                "authors": "A",
            },
        ]
        ctx = SessionContext(topics=["FEP"])
        nuggets = detector.score(ctx, results)
        assert len(nuggets) >= 1
        assert nuggets[0].push_reason != ""

    # PURPOSE: BGE-large の実測距離範囲 (0.7-0.8) でスコアリングするテスト
    def test_bge_large_distance_range_passes_default_threshold(self):
        """BGE-large の典型的な距離 0.764 で閾値 0.50 を通過すること"""
        detector = RelevanceDetector()  # default threshold=0.50
        results = [
            {
                "title": "Active Inference Paper",
                "abstract": "FEP and active inference framework.",
                "source": "arxiv",
                "_distance": 0.764,  # 実測値
                "url": "#",
                "authors": "Friston",
            },
            {
                "title": "Somewhat Related",
                "abstract": "Another paper.",
                "source": "session",
                "_distance": 0.787,  # 実測値
                "url": "#",
                "authors": "B",
            },
        ]
        ctx = SessionContext(topics=["Active Inference"])
        nuggets = detector.score(ctx, results)
        # 0.764 → score=0.618, 0.787 → score=0.607: 両方 >= 0.50
        assert len(nuggets) == 2
        assert nuggets[0].relevance_score > 0.60

    # PURPOSE: 旧閾値 0.65 では BGE-large 距離がフィルタされるテスト
    def test_bge_large_distance_fails_old_threshold(self):
        """旧閾値 0.65 では BGE-large の典型距離がフィルタされる"""
        detector = RelevanceDetector(threshold=0.65)
        results = [
            {
                "title": "Paper A",
                "abstract": "Something.",
                "source": "arxiv",
                "_distance": 0.764,
                "url": "#",
                "authors": "A",
            },
        ]
        ctx = SessionContext(topics=["test"])
        nuggets = detector.score(ctx, results)
        # 0.764 → score=0.618 < 0.65 → フィルタされる
        assert len(nuggets) == 0


# =============================================================================
# AutoTopicExtractor v2.1
# =============================================================================


# PURPOSE: Test auto topic extractor v2.1 の実装
class TestAutoTopicExtractorV21:
    # PURPOSE: ドメイン概念の抽出テスト
    """Test suite for auto topic extractor v21."""
    # PURPOSE: Verify domain concepts extracted behaves correctly
    def test_domain_concepts_extracted(self):
        """Verify domain concepts extracted behavior."""
        from mekhane.pks.pks_engine import AutoTopicExtractor
        extractor = AutoTopicExtractor()
        text = """---
primary_task: "PKS修正"
---
## Situation
FEP に基づく Active Inference の実装を進めている。
CCL パーサーの修正が完了した。
"""
        topics = extractor.extract(text)
        topic_lower = [t.lower() for t in topics]
        assert any("fep" in t for t in topic_lower)
        assert any("active inference" in t for t in topic_lower)
        assert any("ccl" in t for t in topic_lower)

    # PURPOSE: 教訓セクションの抽出テスト
    def test_lesson_extraction(self):
        """Verify lesson extraction behavior."""
        from mekhane.pks.pks_engine import AutoTopicExtractor
        extractor = AutoTopicExtractor()
        text = """
- 教訓: 閾値をモデルに合わせて調整する必要がある
- 学び: BGE-large のスコア分布は BGE-small と異なる
"""
        topics = extractor.extract(text)
        assert any("閾値" in t for t in topics)

    # PURPOSE: max_topics 制限テスト
    def test_max_topics_limit(self):
        """Verify max topics limit behavior."""
        from mekhane.pks.pks_engine import AutoTopicExtractor
        extractor = AutoTopicExtractor()
        # 大量のコンテンツを生成
        lines = [f"- [x] Task {i} completed ✓" for i in range(30)]
        text = "\n".join(lines)
        topics = extractor.extract(text, max_topics=5)
        assert len(topics) <= 5


# =============================================================================
# SerendipityScorer
# =============================================================================


# PURPOSE: Test serendipity scorer の実装
class TestSerendipityScorer:
    # PURPOSE: sweet_spot_high_score をテストする
    """Test suite for serendipity scorer."""
    # PURPOSE: Verify sweet spot high score behaves correctly
    def test_sweet_spot_high_score(self):
        """Verify sweet spot high score behavior."""
        scorer = SerendipityScorer()
        # At sweet_spot distance, score should be high
        score = scorer.score(relevance=0.8, distance=0.45)
        assert score > 0.5

    # PURPOSE: very_close_lower_serendipity をテストする
    def test_very_close_lower_serendipity(self):
        """Verify very close lower serendipity behavior."""
        scorer = SerendipityScorer()
        # Very close = obvious, low serendipity
        score_close = scorer.score(relevance=0.8, distance=0.1)
        score_sweet = scorer.score(relevance=0.8, distance=0.45)
        assert score_sweet > score_close

    # PURPOSE: very_far_lower_serendipity をテストする
    def test_very_far_lower_serendipity(self):
        """Verify very far lower serendipity behavior."""
        scorer = SerendipityScorer()
        # Very far = irrelevant
        score_far = scorer.score(relevance=0.8, distance=0.9)
        score_sweet = scorer.score(relevance=0.8, distance=0.45)
        assert score_sweet >= score_far

    # PURPOSE: zero_relevance_zero_serendipity をテストする
    def test_zero_relevance_zero_serendipity(self):
        """Verify zero relevance zero serendipity behavior."""
        scorer = SerendipityScorer()
        score = scorer.score(relevance=0.0, distance=0.45)
        assert score == 0.0

    # PURPOSE: enrich_adds_scores をテストする
    def test_enrich_adds_scores(self, multi_nuggets):
        """Verify enrich adds scores behavior."""
        scorer = SerendipityScorer()
        distances = [0.3, 0.8, 0.45]
        scorer.enrich(multi_nuggets, distances)
        for nugget in multi_nuggets:
            assert nugget.serendipity_score >= 0.0


# =============================================================================
# PushController
# =============================================================================


# PURPOSE: Test push controller の実装
class TestPushController:
    # PURPOSE: max_push_limit をテストする
    """Test suite for push controller."""
    # PURPOSE: Verify max push limit behaves correctly
    def test_max_push_limit(self, multi_nuggets):
        """Verify max push limit behavior."""
        controller = PushController(max_push=1)
        filtered = controller.filter_pushable(multi_nuggets)
        assert len(filtered) <= 1

    # PURPOSE: record_and_cooldown をテストする
    def test_record_and_cooldown(self, sample_nugget):
        """Verify record and cooldown behavior."""
        controller = PushController(cooldown_hours=24.0)
        controller.record_push([sample_nugget])
        # Same nugget should be filtered by cooldown
        filtered = controller.filter_pushable([sample_nugget])
        assert len(filtered) == 0

    # PURPOSE: save_and_load_history をテストする
    def test_save_and_load_history(self, sample_nugget, tmp_path):
        """Verify save and load history behavior."""
        controller = PushController()
        controller.record_push([sample_nugget])
        history_path = tmp_path / "history.json"
        controller.save_history(history_path)
        assert history_path.exists()

        controller2 = PushController()
        controller2.load_history(history_path)
        filtered = controller2.filter_pushable([sample_nugget])
        assert len(filtered) == 0


# =============================================================================
# Narrator
# =============================================================================


# PURPOSE: Test narrator の実装
class TestNarrator:
    # PURPOSE: narrate_produces_3_segments をテストする
    """Test suite for narrator."""
    # PURPOSE: Verify narrate produces 5 segments behaves correctly
    def test_narrate_produces_5_segments(self, sample_nugget):
        """Verify narrate produces 5 segments behavior."""
        narrator = PKSNarrator()
        narrative = narrator.narrate(sample_nugget)
        assert len(narrative.segments) == 5

    # PURPOSE: segment_speakers をテストする
    def test_segment_speakers(self, sample_nugget):
        """Verify segment speakers behavior."""
        narrator = PKSNarrator()
        narrative = narrator.narrate(sample_nugget)
        speakers = [s.speaker for s in narrative.segments]
        assert speakers == ["Advocate", "Critic", "Advocate", "Critic", "Advocate"]

    # PURPOSE: narrative_to_markdown をテストする
    def test_narrative_to_markdown(self, sample_nugget):
        """Verify narrative to markdown behavior."""
        narrator = PKSNarrator()
        narrative = narrator.narrate(sample_nugget)
        md = narrative.to_markdown()
        assert "🟢 Advocate" in md
        assert "🔴 Critic" in md

    # PURPOSE: narrate_batch をテストする
    def test_narrate_batch(self, multi_nuggets):
        """Verify narrate batch behavior."""
        narrator = PKSNarrator()
        narratives = narrator.narrate_batch(multi_nuggets)
        assert len(narratives) == len(multi_nuggets)

    # PURPOSE: format_report_empty をテストする
    def test_format_report_empty(self):
        """Verify format report empty behavior."""
        narrator = PKSNarrator()
        report = narrator.format_report([])
        assert "なし" in report

    # PURPOSE: format_report_nonempty をテストする
    def test_format_report_nonempty(self, sample_nugget):
        """Verify format report nonempty behavior."""
        narrator = PKSNarrator()
        narrative = narrator.narrate(sample_nugget)
        report = narrator.format_report([narrative])
        assert "Narrative Report" in report

    # PURPOSE: critic_mentions_preprint_for_arxiv をテストする
    def test_critic_mentions_preprint_for_arxiv(self, sample_nugget):
        """Verify critic mentions preprint for arxiv behavior."""
        narrator = PKSNarrator()
        narrative = narrator.narrate(sample_nugget)
        critic_text = narrative.segments[1].content
        assert "査読" in critic_text  # arxiv source → preprint warning

    # PURPOSE: critic_relevance_warning_low_score をテストする
    def test_critic_relevance_warning_low_score(self, low_score_nugget):
        """Verify critic relevance warning low score behavior."""
        narrator = PKSNarrator()
        narrative = narrator.narrate(low_score_nugget)
        critic_text = narrative.segments[1].content
        assert "0.30" in critic_text or "確定的" in critic_text


# =============================================================================
# MatrixView
# =============================================================================


# PURPOSE: Test matrix view の実装
class TestMatrixView:
    # PURPOSE: generate_empty をテストする
    """Test suite for matrix view."""
    # PURPOSE: Verify generate empty behaves correctly
    def test_generate_empty(self):
        """Verify generate empty behavior."""
        matrix = PKSMatrixView()
        result = matrix.generate([])
        assert "なし" in result

    # PURPOSE: generate_table をテストする
    def test_generate_table(self, multi_nuggets):
        """Verify generate table behavior."""
        matrix = PKSMatrixView()
        table = matrix.generate(multi_nuggets)
        assert "Title" in table
        assert "Source" in table
        assert "Score" in table
        assert "Active Inference" in table

    # PURPOSE: pipe_escape をテストする
    def test_pipe_escape(self):
        """Verify pipe escape behavior."""
        nugget = KnowledgeNugget(
            title="Title|with|pipes",
            abstract="Abstract",
            source="test",
            relevance_score=0.5,
        )
        matrix = PKSMatrixView()
        table = matrix.generate([nugget])
        # Pipes should be escaped
        assert "\\|" in table


# PURPOSE: Test backlinks の実装
class TestBacklinks:
    # PURPOSE: empty_nuggets をテストする
    """Test suite for backlinks."""
    # PURPOSE: Verify empty nuggets behaves correctly
    def test_empty_nuggets(self):
        """Verify empty nuggets behavior."""
        bl = PKSBacklinks()
        result = bl.generate("FEP", [])
        assert "なし" in result or "ありません" in result

    # PURPOSE: backlinks_report をテストする
    def test_backlinks_report(self, multi_nuggets):
        """Verify backlinks report behavior."""
        bl = PKSBacklinks()
        result = bl.generate("FEP", multi_nuggets)
        assert "バックリンク" in result
        assert "FEP" in result
        assert "█" in result  # Score bar

    # PURPOSE: max_links_limit をテストする
    def test_max_links_limit(self, multi_nuggets):
        """Verify max links limit behavior."""
        bl = PKSBacklinks()
        result = bl.generate("FEP", multi_nuggets, max_links=1)
        # Should only show 1 entry in the detail table
        lines = [l for l in result.split("\n") if l.startswith("|") and "知識" not in l and "---" not in l]
        assert len(lines) <= 1


# =============================================================================
# SyncWatcher
# =============================================================================


# PURPOSE: Test sync watcher の実装
class TestSyncWatcher:
    # PURPOSE: detect_new_files をテストする
    """Test suite for sync watcher."""
    # PURPOSE: Verify detect new files behaves correctly
    def test_detect_new_files(self, tmp_path):
        """Verify detect new files behavior."""
        watch_dir = tmp_path / "watch"
        watch_dir.mkdir()
        (watch_dir / "test.md").write_text("# Test", encoding="utf-8")

        state_dir = tmp_path / "state"
        watcher = SyncWatcher(
            watch_dirs=[watch_dir],
            state_dir=state_dir,
        )
        changes = watcher.detect_changes()
        assert len(changes) == 1
        assert changes[0].change_type == "added"

    # PURPOSE: detect_modified_files をテストする
    def test_detect_modified_files(self, tmp_path):
        """Verify detect modified files behavior."""
        watch_dir = tmp_path / "watch"
        watch_dir.mkdir()
        f = watch_dir / "test.md"
        f.write_text("# Original", encoding="utf-8")

        state_dir = tmp_path / "state"
        watcher = SyncWatcher(watch_dirs=[watch_dir], state_dir=state_dir)
        watcher.run_once()  # Record state

        f.write_text("# Modified!", encoding="utf-8")
        changes = watcher.detect_changes()
        assert any(c.change_type == "modified" for c in changes)

    # PURPOSE: detect_deleted_files をテストする
    def test_detect_deleted_files(self, tmp_path):
        """Verify detect deleted files behavior."""
        watch_dir = tmp_path / "watch"
        watch_dir.mkdir()
        f = watch_dir / "test.md"
        f.write_text("# Delete me", encoding="utf-8")

        state_dir = tmp_path / "state"
        watcher = SyncWatcher(watch_dirs=[watch_dir], state_dir=state_dir)
        watcher.run_once()

        f.unlink()
        changes = watcher.detect_changes()
        assert any(c.change_type == "deleted" for c in changes)

    # PURPOSE: no_changes をテストする
    def test_no_changes(self, tmp_path):
        """Verify no changes behavior."""
        watch_dir = tmp_path / "watch"
        watch_dir.mkdir()
        (watch_dir / "stable.md").write_text("stable", encoding="utf-8")

        state_dir = tmp_path / "state"
        watcher = SyncWatcher(watch_dirs=[watch_dir], state_dir=state_dir)
        watcher.run_once()
        changes = watcher.detect_changes()
        assert len(changes) == 0

    # PURPOSE: extension_filter をテストする
    def test_extension_filter(self, tmp_path):
        """Verify extension filter behavior."""
        watch_dir = tmp_path / "watch"
        watch_dir.mkdir()
        (watch_dir / "test.txt").write_text("not md", encoding="utf-8")

        watcher = SyncWatcher(
            watch_dirs=[watch_dir],
            extensions=(".md",),
            state_dir=tmp_path / "state",
        )
        changes = watcher.detect_changes()
        assert len(changes) == 0  # .txt is not tracked


# =============================================================================
# Links
# =============================================================================


# PURPOSE: Test wikilinks の実装
class TestWikilinks:
    # PURPOSE: basic_wikilink をテストする
    """Test suite for wikilinks."""
    # PURPOSE: Verify basic wikilink behaves correctly
    def test_basic_wikilink(self):
        """Verify basic wikilink behavior."""
        matches = WIKILINK_PATTERN.findall("See [[target]] for details")
        assert len(matches) >= 1

    # PURPOSE: aliased_wikilink をテストする
    def test_aliased_wikilink(self):
        """Verify aliased wikilink behavior."""
        matches = WIKILINK_PATTERN.findall("See [[target|display text]]")
        assert len(matches) >= 1

    # PURPOSE: multiple_wikilinks をテストする
    def test_multiple_wikilinks(self):
        """Verify multiple wikilinks behavior."""
        matches = WIKILINK_PATTERN.findall("[[a]] and [[b]] and [[c]]")
        assert len(matches) == 3


# PURPOSE: Test citation graph の実装
class TestCitationGraph:
    # PURPOSE: add_and_query をテストする
    """Test suite for citation graph."""
    # PURPOSE: Verify add and query behaves correctly
    def test_add_and_query(self):
        """Verify add and query behavior."""
        graph = CitationGraph()
        graph.add_citation(Citation("paper_a", "paper_b", CitationType.SUPPORTS))
        stats = graph.get_stats("paper_b")
        assert stats.supporting_count == 1

    # PURPOSE: multiple_citations をテストする
    def test_multiple_citations(self):
        """Verify multiple citations behavior."""
        graph = CitationGraph()
        graph.add_citation(Citation("a", "b", CitationType.SUPPORTS))
        graph.add_citation(Citation("c", "b", CitationType.CONTRASTS))
        stats = graph.get_stats("b")
        assert stats.supporting_count == 1

    # PURPOSE: unknown_paper_returns_none をテストする
    def test_unknown_paper_returns_none(self):
        """Verify unknown paper returns none behavior."""
        graph = CitationGraph()
        stats = graph.get_stats("nonexistent")
        assert stats is None
