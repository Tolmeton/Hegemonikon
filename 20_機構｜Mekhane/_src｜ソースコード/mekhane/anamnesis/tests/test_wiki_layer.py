# PROOF: mekhane/anamnesis/tests/test_wiki_layer.py
# PURPOSE: WikiLayer Phase α 実装の roundtrip / 検出ロジック / CLI smoke 検証
"""WikiLayer + WikiPage テスト — Phase α scaffold の動作保証。

Phase α は LLM 不要の決定論的経路のみを覆う:
- WikiPage の to_markdown / from_markdown roundtrip
- WikiLayer 検出ロジック (orphan / staleness / cross-ref-gap / NotImplementedError)
- crystallize_pages の in-memory 統合
- CLI subcommand smoke

外部 DB (phantazein.db) を汚染しないため、PhantazeinStore は session_id="test_wiki_layer"
で呼ばれることだけを mock で検証し、本物のストアには触れない。
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from pydantic import ValidationError

from mekhane.anamnesis import wiki_layer as wiki_layer_module
from mekhane.anamnesis.wiki_layer import (
    ContradictionReport,
    CrossRefGapReport,
    LintResult,
    MissingReport,
    OrphanReport,
    StalenessReport,
    WikiLayer,
)
from mekhane.anamnesis.wiki_schema import WikiPage


# ---------------------------------------------------------------------------
# A. wiki_schema roundtrip + validation
# ---------------------------------------------------------------------------


class TestWikiPageRoundtrip:
    """WikiPage の Markdown serialization が情報を保つことを確認する。"""

    def _make_page(self, **overrides) -> WikiPage:
        now = datetime(2026, 4, 17, 12, 0, 0, tzinfo=timezone.utc)
        defaults = dict(
            cluster_id="cluster_abc123",
            members=["chunk_1", "chunk_2", "chunk_3"],
            source_types=["session", "handoff"],
            representative_text="代表テキスト本文。改行や日本語を含む。",
            title="代表テキスト本文",
            created_at=now,
            last_updated=now,
            in_degree=2,
            out_degree=4,
            tags=["fep", "active-inference"],
        )
        defaults.update(overrides)
        return WikiPage(**defaults)

    def test_roundtrip_preserves_all_fields(self):
        page = self._make_page()
        text = page.to_markdown()
        restored = WikiPage.from_markdown(text)

        assert restored.cluster_id == page.cluster_id
        assert restored.members == page.members
        assert restored.source_types == page.source_types
        assert restored.representative_text == page.representative_text
        assert restored.title == page.title
        assert restored.created_at == page.created_at
        assert restored.last_updated == page.last_updated
        assert restored.in_degree == page.in_degree
        assert restored.out_degree == page.out_degree
        assert restored.tags == page.tags

    def test_roundtrip_empty_optional_fields(self):
        """tags / members / source_types の境界値 (空 list / 単一要素)。"""
        page = self._make_page(
            members=["chunk_only"],
            source_types=["session"],
            tags=[],
        )
        restored = WikiPage.from_markdown(page.to_markdown())
        assert restored.members == ["chunk_only"]
        assert restored.source_types == ["session"]
        assert restored.tags == []

    def test_from_markdown_missing_front_matter_raises(self):
        with pytest.raises(ValueError, match="missing YAML front matter"):
            WikiPage.from_markdown("plain markdown without front matter")

    def test_from_markdown_unterminated_front_matter_raises(self):
        bad = "---\ncluster_id: foo\n(no closing fence)\n"
        with pytest.raises(ValueError, match="unterminated"):
            WikiPage.from_markdown(bad)

    def test_pydantic_rejects_missing_required_field(self):
        """cluster_id を欠いた payload は ValidationError。"""
        with pytest.raises(ValidationError):
            WikiPage(
                # cluster_id を意図的に欠落
                members=["chunk_1"],
                source_types=["session"],
                representative_text="text",
                title="title",
                created_at=datetime.now(timezone.utc),
                last_updated=datetime.now(timezone.utc),
            )  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Helpers for WikiLayer tests
# ---------------------------------------------------------------------------


def _make_layer(
    tmp_path: Path,
    records: list[dict] | None = None,
    link_graph=None,
    min_knn_density: float = 0.3,
) -> WikiLayer:
    """フィクスチャ: tmp_path 配下に分離した wiki_root を持つ WikiLayer。"""
    field_mock = MagicMock()
    storage_mock = MagicMock()
    storage_mock.filter_to_pandas.return_value = pd.DataFrame(records or [])
    field_mock._get_storage.return_value = storage_mock
    layer = WikiLayer(
        phantasia_field=field_mock,
        wiki_root=tmp_path / "wiki",
        link_graph=link_graph,
        min_knn_density=min_knn_density,
    )
    return layer


def _write_page(layer: WikiLayer, page: WikiPage) -> Path:
    """layer.wiki_root 配下にページを書き出してパスを返す。"""
    page_path = layer._page_path(page)
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_text(page.to_markdown(), encoding="utf-8")
    return page_path


def _make_page(
    cluster_id: str,
    members: list[str],
    source_types: list[str] | None = None,
    representative_text: str = "rep text",
) -> WikiPage:
    now = datetime.now(timezone.utc)
    return WikiPage(
        cluster_id=cluster_id,
        members=members,
        source_types=source_types or ["session"],
        representative_text=representative_text,
        title=cluster_id,
        created_at=now,
        last_updated=now,
    )


# ---------------------------------------------------------------------------
# B. WikiLayer unit tests
# ---------------------------------------------------------------------------


class TestSelectRepresentative:
    """密度最大の chunk が代表として選ばれることを確認する。"""

    def test_selects_highest_density(self):
        cluster = [
            {"chunk_id": "a", "density": 0.2, "content": "A"},
            {"chunk_id": "b", "density": 0.9, "content": "B"},
            {"chunk_id": "c", "density": 0.5, "content": "C"},
        ]
        result = WikiLayer._select_representative(cluster)
        assert result["chunk_id"] == "b"

    def test_handles_missing_density(self):
        """density 欠落 chunk は 0.0 扱い → 他の最大が選ばれる。"""
        cluster = [
            {"chunk_id": "a", "content": "no density"},
            {"chunk_id": "b", "density": 0.4, "content": "B"},
        ]
        result = WikiLayer._select_representative(cluster)
        assert result["chunk_id"] == "b"


class TestDetectOrphan:
    """orphan: link_graph 注入時の in_degree=0、また低密度の検出。"""

    def test_in_degree_zero_with_link_graph(self, tmp_path: Path):
        link_graph = MagicMock()
        link_graph.nodes = {"cluster_X": MagicMock(in_links=[], out_links=[])}
        # density 高めにして low_knn_density 経路を切り、in_degree=0 だけで上がるか確認
        layer = _make_layer(
            tmp_path,
            records=[{"chunk_id": "m1", "parent_id": "p1", "density": 0.9}],
            link_graph=link_graph,
        )
        page = _make_page("cluster_X", ["m1"])
        _write_page(layer, page)

        reports = layer._detect_orphan()
        assert len(reports) == 1
        assert reports[0].cluster_id == "cluster_X"
        assert reports[0].reason == "in_degree=0"
        assert reports[0].in_degree == 0

    def test_low_knn_density_without_link_graph(self, tmp_path: Path):
        """link_graph 不在 + density < 0.3 → low_knn_density で検出される。"""
        layer = _make_layer(
            tmp_path,
            records=[{"chunk_id": "m1", "parent_id": "p1", "density": 0.1}],
            link_graph=None,
        )
        page = _make_page("cluster_lowdense", ["m1"])
        _write_page(layer, page)

        reports = layer._detect_orphan()
        assert len(reports) == 1
        assert reports[0].cluster_id == "cluster_lowdense"
        assert reports[0].reason == "low_knn_density"
        assert reports[0].knn_density == pytest.approx(0.1)

    def test_high_density_no_report(self, tmp_path: Path):
        """高密度 + link_graph なし → orphan 報告なし。"""
        layer = _make_layer(
            tmp_path,
            records=[{"chunk_id": "m1", "parent_id": "p1", "density": 0.9}],
            link_graph=None,
        )
        _write_page(layer, _make_page("cluster_dense", ["m1"]))
        assert layer._detect_orphan() == []


class TestLinkGraphIntegration:
    """LinkGraph の有無で orphan 判定が分岐することを確認する。"""

    def test_singleton_excluded_when_no_link_graph(self, tmp_path: Path, caplog: pytest.LogCaptureFixture):
        layer = _make_layer(
            tmp_path,
            records=[{"chunk_id": "m1", "parent_id": "p1", "vector": [1.0, 0.0, 0.0]}],
            link_graph=None,
        )
        _write_page(layer, _make_page("cluster_singleton", ["m1"]))

        with caplog.at_level("WARNING"):
            reports = layer._detect_orphan()

        assert reports == []
        assert "skipping orphan detection for 1 singleton clusters" in caplog.text

    def test_singleton_in_degree_zero_with_link_graph(self, tmp_path: Path):
        link_graph = MagicMock()
        link_graph.nodes = {"cluster_singleton": MagicMock(in_links=[], out_links=[])}
        layer = _make_layer(
            tmp_path,
            records=[{"chunk_id": "m1", "parent_id": "p1", "vector": [1.0, 0.0, 0.0]}],
            link_graph=link_graph,
        )
        _write_page(layer, _make_page("cluster_singleton", ["m1"]))

        reports = layer._detect_orphan()

        assert len(reports) == 1
        assert reports[0].reason == "in_degree=0"
        assert reports[0].in_degree == 0

    def test_min_knn_density_arg_overrides_default(self, tmp_path: Path):
        layer = _make_layer(
            tmp_path,
            records=[
                {"chunk_id": "m1", "parent_id": "p1", "density": 0.1},
                {"chunk_id": "m2", "parent_id": "p1", "density": 0.1},
            ],
            link_graph=None,
            min_knn_density=0.05,
        )
        _write_page(layer, _make_page("cluster_density_override", ["m1", "m2"]))

        assert layer.min_knn_density == pytest.approx(0.05)
        assert layer._detect_orphan() == []


class TestSnapshot:
    """FAISS backend の snapshot 読み取りを検証する。"""

    def _make_real_field(self, tmp_path: Path):
        from mekhane.anamnesis.phantasia_field import PhantasiaField

        db_path = tmp_path / "db"
        field = PhantasiaField(db_path=str(db_path), backend="faiss")
        storage = field._get_storage()
        storage.backend.create(
            [
                {
                    "chunk_id": "m1",
                    "primary_key": "m1",
                    "id": "m1",
                    "parent_id": "doc_1",
                    "source": "session",
                    "content": "snapshot test content",
                    "density": 0.2,
                    "vector": [1.0, 0.0, 0.0],
                }
            ]
        )
        return field

    def test_snapshot_created_and_cleaned(self, tmp_path: Path):
        field = self._make_real_field(tmp_path)
        layer = WikiLayer(field, tmp_path / "wiki")
        _write_page(layer, _make_page("cluster_snapshot", ["m1"]))

        seen_snapshot_dirs: list[Path] = []
        original_cleanup = layer._cleanup_snapshot

        def wrapped_cleanup(snapshot_dir: Path | None) -> None:
            if snapshot_dir is not None:
                seen_snapshot_dirs.append(snapshot_dir)
                assert snapshot_dir.exists()
            original_cleanup(snapshot_dir)

        with patch.object(layer, "_cleanup_snapshot", side_effect=wrapped_cleanup):
            layer.lint(["orphan"], dry_run=True)

        assert seen_snapshot_dirs
        assert all(not path.exists() for path in seen_snapshot_dirs)

    def test_snapshot_disabled_via_flag(self, tmp_path: Path):
        field = self._make_real_field(tmp_path)
        layer = WikiLayer(field, tmp_path / "wiki", use_snapshot=False)
        _write_page(layer, _make_page("cluster_snapshot_disabled", ["m1"]))

        temp_root = Path(wiki_layer_module.tempfile.gettempdir())
        before = {path.name for path in temp_root.glob("wiki_snapshot_*")}
        layer.lint(["orphan"], dry_run=True)
        after = {path.name for path in temp_root.glob("wiki_snapshot_*")}

        assert before == after

    def test_snapshot_retry_on_truncated_pickle(self, tmp_path: Path):
        field = self._make_real_field(tmp_path)
        layer = WikiLayer(field, tmp_path / "wiki")

        real_pickle_load = wiki_layer_module._pickle.load
        load_calls = {"count": 0}

        def flaky_pickle_load(handle):
            load_calls["count"] += 1
            if load_calls["count"] == 1:
                raise wiki_layer_module._pickle.UnpicklingError("truncated")
            return real_pickle_load(handle)

        with patch.object(wiki_layer_module._pickle, "load", side_effect=flaky_pickle_load):
            snapshot_dir = layer._create_snapshot()

        try:
            assert snapshot_dir is not None
            assert load_calls["count"] >= 2
            assert snapshot_dir.exists()
        finally:
            layer._cleanup_snapshot(snapshot_dir)


class TestFAISSClustering:
    """FAISS top-k clustering path と in-memory fallback を検証する。"""

    def _make_records(self, size: int = 50) -> list[dict]:
        half = size // 2
        records: list[dict] = []
        for i in range(half):
            records.append(
                {
                    "chunk_id": f"a{i}",
                    "parent_id": "doc_a",
                    "vector": [1.0, 0.0, 0.0],
                    "content": f"A{i}",
                }
            )
        for i in range(size - half):
            records.append(
                {
                    "chunk_id": f"b{i}",
                    "parent_id": "doc_b",
                    "vector": [0.0, 1.0, 0.0],
                    "content": f"B{i}",
                }
            )
        return records

    def _make_faiss_layer(self, tmp_path: Path) -> WikiLayer:
        from mekhane.anamnesis.backends.faiss_backend import FAISSBackend

        field_mock = MagicMock()
        storage_mock = MagicMock()
        storage_mock.backend = FAISSBackend(tmp_path / "cluster_db", table_name="cluster_test")
        field_mock._get_storage.return_value = storage_mock
        return WikiLayer(field_mock, tmp_path / "wiki")

    @staticmethod
    def _cluster_member_sets(clusters: list[list[dict]]) -> set[frozenset[str]]:
        return {
            frozenset(record["chunk_id"] for record in cluster)
            for cluster in clusters
        }

    def test_faiss_path_matches_inmemory_for_small_n(self, tmp_path: Path):
        records = self._make_records(size=50)
        faiss_layer = self._make_faiss_layer(tmp_path)
        memory_layer = _make_layer(tmp_path / "memory")

        baseline = memory_layer._cluster_records(records, k_neighbors=10, similarity_threshold=0.7)
        faiss_clusters = faiss_layer._cluster_records(records, k_neighbors=10, similarity_threshold=0.7)

        assert len(faiss_clusters) == len(baseline)
        assert self._cluster_member_sets(faiss_clusters) == self._cluster_member_sets(baseline)

    def test_faiss_path_skipped_when_faiss_unavailable(self, tmp_path: Path):
        import builtins

        records = self._make_records(size=50)
        layer = self._make_faiss_layer(tmp_path)
        original_import = builtins.__import__

        def failing_import(name, *args, **kwargs):
            if name == "faiss":
                raise ImportError("forced for test")
            return original_import(name, *args, **kwargs)

        with patch.object(layer, "_cluster_records_inmemory", wraps=layer._cluster_records_inmemory) as spy:
            with patch("builtins.__import__", side_effect=failing_import):
                clusters = layer._cluster_records(records, k_neighbors=10, similarity_threshold=0.7)

        assert spy.call_count == 1
        assert clusters

    def test_faiss_path_skipped_for_small_n(self, tmp_path: Path, caplog: pytest.LogCaptureFixture):
        records = self._make_records(size=10)
        layer = self._make_faiss_layer(tmp_path)

        with patch.object(layer, "_cluster_records_inmemory", wraps=layer._cluster_records_inmemory) as spy:
            with caplog.at_level("INFO"):
                clusters = layer._cluster_records(records, k_neighbors=5, similarity_threshold=0.7)

        assert spy.call_count == 1
        assert clusters
        assert "WikiLayer clustering: in-memory path (N=10, k=5)" in caplog.text


class TestDetectStaleness:
    """source mtime > wiki mtime のページを検出する。"""

    def test_source_newer_than_wiki(self, tmp_path: Path):
        # source ファイルを実存させる
        source_file = tmp_path / "source.md"
        source_file.write_text("source content", encoding="utf-8")

        layer = _make_layer(
            tmp_path,
            records=[{"chunk_id": "m1", "parent_id": str(source_file), "density": 0.5}],
        )
        page = _make_page("cluster_stale", ["m1"])
        page_path = _write_page(layer, page)

        # wiki page を意図的に古くする
        old_mtime = source_file.stat().st_mtime - 3600
        import os
        os.utime(page_path, (old_mtime, old_mtime))

        reports = layer._detect_staleness()
        assert len(reports) == 1
        assert reports[0].cluster_id == "cluster_stale"
        assert reports[0].source_path == str(source_file.resolve())
        assert reports[0].source_mtime > reports[0].wiki_mtime

    def test_no_report_when_wiki_is_newer(self, tmp_path: Path):
        source_file = tmp_path / "source2.md"
        source_file.write_text("src", encoding="utf-8")
        # source を意図的に古くする
        import os
        old_mtime = source_file.stat().st_mtime - 7200
        os.utime(source_file, (old_mtime, old_mtime))

        layer = _make_layer(
            tmp_path,
            records=[{"chunk_id": "m1", "parent_id": str(source_file), "density": 0.5}],
        )
        _write_page(layer, _make_page("cluster_fresh", ["m1"]))

        assert layer._detect_staleness() == []


class TestDetectCrossRefGap:
    """類似度高だが explicit edge なし → ギャップ検出。"""

    def test_detects_gap_between_similar_unlinked_pages(self, tmp_path: Path):
        # 2 nodes, neighbor link なし
        node_a = MagicMock(in_links=[], out_links=[])
        node_b = MagicMock(in_links=[], out_links=[])
        link_graph = MagicMock()
        link_graph.nodes = {"src_a": node_a, "src_b": node_b}

        # α-2.2: centroids are built from per-record `vector` (no embedder call).
        records = [
            {"chunk_id": "m1", "parent_id": "src_a", "density": 0.5, "vector": [1.0, 0.0]},
            {"chunk_id": "m2", "parent_id": "src_b", "density": 0.5, "vector": [1.0, 0.0]},
        ]
        layer = _make_layer(tmp_path, records=records, link_graph=link_graph)

        page_a = _make_page("cluster_A", ["m1"], representative_text="text A")
        page_b = _make_page("cluster_B", ["m2"], representative_text="text B")
        _write_page(layer, page_a)
        _write_page(layer, page_b)

        reports = layer._detect_cross_ref_gap(similarity_threshold=0.7)

        assert len(reports) == 1
        assert {reports[0].cluster_a, reports[0].cluster_b} == {"cluster_A", "cluster_B"}
        assert reports[0].cosine_similarity == pytest.approx(1.0)

    def test_skips_when_no_link_graph(self, tmp_path: Path):
        layer = _make_layer(tmp_path, link_graph=None)
        assert layer._detect_cross_ref_gap() == []

    def test_skips_when_explicit_edge_exists(self, tmp_path: Path):
        node_a = MagicMock(in_links=[], out_links=["src_b"])
        node_b = MagicMock(in_links=["src_a"], out_links=[])
        link_graph = MagicMock()
        link_graph.nodes = {"src_a": node_a, "src_b": node_b}

        records = [
            {"chunk_id": "m1", "parent_id": "src_a", "density": 0.5, "vector": [1.0, 0.0]},
            {"chunk_id": "m2", "parent_id": "src_b", "density": 0.5, "vector": [1.0, 0.0]},
        ]
        layer = _make_layer(tmp_path, records=records, link_graph=link_graph)
        _write_page(layer, _make_page("cluster_A", ["m1"], representative_text="t"))
        _write_page(layer, _make_page("cluster_B", ["m2"], representative_text="t"))

        reports = layer._detect_cross_ref_gap(similarity_threshold=0.7)

        assert reports == []

    def test_cross_ref_gap_faiss_backed_matches_pairwise(self, tmp_path: Path):
        """Phase α-2.1: FAISS-backed search must report the same pairs as
        pure Python cosine for a small deterministic fixture.

        Graph layout:
            A ── B   (explicit edge: should be suppressed)
            C       (no edge; near A & B: should appear)
            D       (dissimilar: below threshold)
        """
        # 4 source nodes. Only A↔B is explicitly linked.
        node_a = MagicMock(in_links=[], out_links=["src_b"])
        node_b = MagicMock(in_links=["src_a"], out_links=[])
        node_c = MagicMock(in_links=[], out_links=[])
        node_d = MagicMock(in_links=[], out_links=[])
        link_graph = MagicMock()
        link_graph.nodes = {
            "src_a": node_a,
            "src_b": node_b,
            "src_c": node_c,
            "src_d": node_d,
        }

        # Phase α-2.1+: centroid is built from stored member vectors, no embedder call.
        records = [
            {"chunk_id": "m_a", "parent_id": "src_a", "density": 0.5, "vector": [1.0, 0.0]},
            {"chunk_id": "m_b", "parent_id": "src_b", "density": 0.5, "vector": [1.0, 0.0]},
            {"chunk_id": "m_c", "parent_id": "src_c", "density": 0.5, "vector": [1.0, 0.0]},
            {"chunk_id": "m_d", "parent_id": "src_d", "density": 0.5, "vector": [0.0, 1.0]},
        ]
        layer = _make_layer(tmp_path, records=records, link_graph=link_graph)
        for cid, member in (
            ("cluster_A", "m_a"),
            ("cluster_B", "m_b"),
            ("cluster_C", "m_c"),
            ("cluster_D", "m_d"),
        ):
            _write_page(layer, _make_page(cid, [member], representative_text=cid))

        reports = layer._detect_cross_ref_gap(similarity_threshold=0.7)

        gap_pairs = {frozenset({r.cluster_a, r.cluster_b}) for r in reports}
        # A-B is explicit → suppressed. A-D / B-D / C-D are below threshold.
        # A-C and B-C are gaps (high similarity, no edge).
        assert gap_pairs == {
            frozenset({"cluster_A", "cluster_C"}),
            frozenset({"cluster_B", "cluster_C"}),
        }
        for r in reports:
            assert r.cosine_similarity == pytest.approx(1.0)


class TestDeferredDetectors:
    """Phase β に申し送られた検出器が NotImplementedError を上げることを確認。"""

    def test_contradiction_raises(self, tmp_path: Path):
        layer = _make_layer(tmp_path)
        with pytest.raises(NotImplementedError, match="Phase"):
            layer._detect_contradiction(llm_budget=0)

    def test_missing_raises(self, tmp_path: Path):
        layer = _make_layer(tmp_path)
        with pytest.raises(NotImplementedError, match="Phase"):
            layer._detect_missing()


class TestWriteToConsistencyLog:
    """log_consistency_issue が想定 args で呼ばれることを mock で確認。実 DB は触らない。"""

    def test_write_invokes_store_with_session_id(self, tmp_path: Path):
        layer = _make_layer(tmp_path)
        store_mock = MagicMock()
        layer._store = store_mock  # PhantazeinStore の lazy init を bypass

        result = LintResult(operations_run=["orphan"])
        result.orphans = [
            OrphanReport(
                cluster_id="cluster_X",
                reason="in_degree=0",
                in_degree=0,
                knn_density=0.5,
            )
        ]
        result.staleness = [
            StalenessReport(
                cluster_id="cluster_Y",
                source_path="/tmp/source.md",
                source_mtime=2.0,
                wiki_mtime=1.0,
            )
        ]

        layer._write_to_consistency_log(result)

        assert store_mock.log_consistency_issue.call_count == 2
        for call in store_mock.log_consistency_issue.call_args_list:
            kwargs = call.kwargs
            assert kwargs["session_id"] == "wiki_layer_lint"
            assert kwargs["issue"].startswith("[wiki/")
            assert kwargs["severity"] in {"low", "medium", "high"}
        assert result.consistency_log_inserts == 2


class TestLintValidation:
    """lint() の operation 名 validation を確認。"""

    def test_unknown_operation_raises(self, tmp_path: Path):
        layer = _make_layer(tmp_path)
        with pytest.raises(ValueError, match="Unknown wiki lint operations"):
            layer.lint(["xyz"])


class TestDryRun:
    """dry_run=True で consistency_log 書き込みが抑止されることを確認。"""

    def test_dry_run_skips_consistency_log_write(self, tmp_path: Path):
        layer = _make_layer(tmp_path)
        with patch.object(layer, "_write_to_consistency_log") as mock_write:
            result = layer.lint(operations=["orphan"], dry_run=True)
            mock_write.assert_not_called()
        assert result.dry_run is True
        assert result.consistency_log_inserts == 0

    def test_dry_run_default_false_still_writes(self, tmp_path: Path):
        layer = _make_layer(tmp_path)
        with patch.object(layer, "_write_to_consistency_log") as mock_write:
            result = layer.lint(operations=["orphan"])
            mock_write.assert_called_once_with(result)
        assert result.dry_run is False


# ---------------------------------------------------------------------------
# C. CLI smoke tests (subprocess; safe — read-only --help / invalid arg)
# ---------------------------------------------------------------------------


class TestCLI:
    """subprocess 経由で CLI の起動と arg parsing を確認。"""

    def _src_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "mekhane.anamnesis.wiki_layer", *args],
            cwd=self._src_root(),
            capture_output=True,
            text=True,
        )

    def test_crystallize_help_exits_zero(self):
        result = self._run("crystallize", "--help")
        assert result.returncode == 0
        assert "crystallize" in result.stdout.lower() or "options" in result.stdout.lower()

    def test_lint_help_exits_zero(self):
        result = self._run("lint", "--help")
        assert result.returncode == 0
        assert "operations" in result.stdout.lower()

    def test_invalid_subcommand_exits_nonzero(self):
        result = self._run("xyz")
        assert result.returncode != 0
        assert "invalid choice" in result.stderr.lower() or "error" in result.stderr.lower()


class TestCLIDryRun:
    """lint --help に dry-run flag が登録されていることを確認。"""

    def _src_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "mekhane.anamnesis.wiki_layer", *args],
            cwd=self._src_root(),
            capture_output=True,
            text=True,
        )

    def test_lint_help_shows_no_write_flag(self):
        result = self._run("lint", "--help")
        assert result.returncode == 0
        assert "--no-write" in result.stdout


# ---------------------------------------------------------------------------
# D. crystallize_pages 統合テスト (in-memory + tmp_path)
# ---------------------------------------------------------------------------


class TestCrystallizePagesIntegration:
    """mock PhantasiaField から chunk を取り、wiki page を tmp_path に書く。"""

    def _records_with_vectors(self) -> list[dict]:
        # 5 chunk: 3 つは似たベクトル (cluster A 候補), 2 つは別ベクトル (cluster B 候補)
        return [
            {
                "chunk_id": f"a{i}",
                "parent_id": "doc_a",
                "source": "session",
                "vector": [1.0, 0.0, 0.0],
                "density": 0.5 + 0.1 * i,
                "content": f"cluster A content {i}",
            }
            for i in range(3)
        ] + [
            {
                "chunk_id": f"b{i}",
                "parent_id": "doc_b",
                "source": "handoff",
                "vector": [0.0, 1.0, 0.0],
                "density": 0.4 + 0.1 * i,
                "content": f"cluster B content {i}",
            }
            for i in range(2)
        ]

    def test_crystallize_writes_pages_and_roundtrip(self, tmp_path: Path):
        layer = _make_layer(tmp_path, records=self._records_with_vectors())
        pages = layer.crystallize_pages(no_llm=True, k_neighbors=3)

        # 2 つの cluster が生成される (ベクトル直交なので分離される)
        assert len(pages) == 2

        # ファイルが想定形式で書かれているか
        written_files = sorted((tmp_path / "wiki").rglob("*.md"))
        assert len(written_files) == 2

        # 各ファイルを from_markdown で読み戻して内容一致を確認
        for written in written_files:
            text = written.read_text(encoding="utf-8")
            restored = WikiPage.from_markdown(text)
            # cluster_id は cluster_<hash> 形式
            assert restored.cluster_id.startswith("cluster_")
            # source_types に session/handoff のいずれかが含まれる
            assert restored.source_types
            assert restored.source_types[0] in {"session", "handoff"}
            assert restored.representative_text  # 非空

    def test_crystallize_returns_empty_when_no_records(self, tmp_path: Path):
        layer = _make_layer(tmp_path, records=[])
        pages = layer.crystallize_pages(no_llm=True)
        assert pages == []

    def test_crystallize_rejects_llm_path(self, tmp_path: Path):
        layer = _make_layer(tmp_path, records=self._records_with_vectors())
        with pytest.raises(NotImplementedError, match="Phase"):
            layer.crystallize_pages(no_llm=False)


class TestLinkGraphIntegration:
    def test_singleton_excluded_when_no_link_graph_no_stored_density(self, tmp_path):
        layer = _make_layer(
            tmp_path,
            records=[
                {"chunk_id": "m1", "parent_id": "p1", "vector": [1.0, 0.0, 0.0]},
            ],
            link_graph=None,
        )
        _write_page(layer, _make_page("cluster_singleton", ["m1"]))
        assert layer._detect_orphan() == []

    def test_singleton_flagged_with_explicit_low_stored_density(self, tmp_path):
        layer = _make_layer(
            tmp_path,
            records=[{"chunk_id": "m1", "parent_id": "p1", "density": 0.05}],
            link_graph=None,
        )
        _write_page(layer, _make_page("cluster_explicitlow", ["m1"]))
        reports = layer._detect_orphan()
        assert len(reports) == 1
        assert reports[0].reason == "low_knn_density"

    def test_singleton_with_link_graph_in_degree_zero(self, tmp_path):
        link_graph = MagicMock()
        link_graph.nodes = {"cluster_X": MagicMock(in_links=[], out_links=[])}
        layer = _make_layer(
            tmp_path,
            records=[{"chunk_id": "m1", "parent_id": "p1", "density": 0.9}],
            link_graph=link_graph,
        )
        _write_page(layer, _make_page("cluster_X", ["m1"]))
        reports = layer._detect_orphan()
        assert len(reports) == 1
        assert reports[0].reason == "in_degree=0"

    def test_min_knn_density_arg_overrides_default(self, tmp_path):
        layer = _make_layer(
            tmp_path,
            records=[
                {"chunk_id": "m1", "parent_id": "p1", "density": 0.2},
                {"chunk_id": "m2", "parent_id": "p1", "density": 0.2},
            ],
            link_graph=None,
        )
        _write_page(layer, _make_page("cluster_multi", ["m1", "m2"]))
        assert len(layer._detect_orphan()) == 1

        layer2 = _make_layer(
            tmp_path / "v2",
            records=[
                {"chunk_id": "m1", "parent_id": "p1", "density": 0.2},
                {"chunk_id": "m2", "parent_id": "p1", "density": 0.2},
            ],
            link_graph=None,
        )
        layer2.min_knn_density = 0.05
        _write_page(layer2, _make_page("cluster_multi", ["m1", "m2"]))
        assert layer2._detect_orphan() == []


class TestFAISSClustering:
    def _gen_records(self, n: int, dim: int = 8) -> list[dict]:
        import random

        random.seed(42)
        recs = []
        for i in range(n):
            if i % 2 == 0:
                v = [1.0 + random.uniform(-0.05, 0.05)] + [random.uniform(-0.02, 0.02)] * (dim - 1)
            else:
                v = [random.uniform(-0.02, 0.02), 1.0 + random.uniform(-0.05, 0.05)] + [0.0] * (dim - 2)
            recs.append({"chunk_id": f"r{i}", "parent_id": f"doc_{i}", "vector": v, "density": 0.5})
        return recs

    def test_faiss_path_matches_inmemory_for_50_vectors(self, tmp_path):
        layer = _make_layer(tmp_path, records=[])
        recs = self._gen_records(50)
        cl_faiss = layer._cluster_records(recs, k_neighbors=5, similarity_threshold=0.7)
        cl_mem = layer._cluster_records_inmemory(recs, k_neighbors=5, similarity_threshold=0.7)
        assert abs(len(cl_faiss) - len(cl_mem)) <= max(1, len(cl_mem) // 10)

    def test_small_n_uses_inmemory(self, tmp_path, caplog):
        layer = _make_layer(tmp_path, records=[])
        recs = self._gen_records(10)
        with caplog.at_level("INFO", logger="mekhane.anamnesis.wiki_layer"):
            layer._cluster_records(recs, k_neighbors=3)
        assert any("in-memory path" in r.message for r in caplog.records)

    def test_faiss_unavailable_fallback(self, tmp_path, monkeypatch):
        layer = _make_layer(tmp_path, records=[])
        recs = self._gen_records(40)
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "faiss":
                raise ImportError("simulated")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        clusters = layer._cluster_records(recs, k_neighbors=5)
        assert clusters


class TestSnapshot:
    def _make_field_with_real_faiss(self, tmp_path):
        from mekhane.anamnesis.backends.faiss_backend import FAISSBackend

        backend = FAISSBackend(tmp_path / "faiss_data", table_name="t")
        backend.create(
            [
                {"chunk_id": "a", "vector": [1.0, 0.0], "density": 0.5, "content": "x"},
                {"chunk_id": "b", "vector": [0.0, 1.0], "density": 0.5, "content": "y"},
            ]
        )
        field = MagicMock()
        storage = MagicMock()
        storage._backend = backend
        storage.backend = backend
        storage.filter_to_pandas.return_value = pd.DataFrame(backend.to_list())
        field._get_storage.return_value = storage
        return field, backend

    def test_snapshot_created_and_cleaned(self, tmp_path):
        field, _backend = self._make_field_with_real_faiss(tmp_path)
        layer = WikiLayer(field, tmp_path / "wiki", use_snapshot=True)
        snap = layer._create_snapshot()
        assert snap is not None and snap.exists()
        assert (snap / "t.faiss").exists()
        assert (snap / "t.meta.pkl").exists()
        layer._cleanup_snapshot(snap)
        assert not snap.exists()

    def test_snapshot_disabled_via_flag(self, tmp_path):
        field, _backend = self._make_field_with_real_faiss(tmp_path)
        layer = WikiLayer(field, tmp_path / "wiki", use_snapshot=False)
        assert layer._create_snapshot() is None

    def test_snapshot_retry_on_truncated_pickle(self, tmp_path, monkeypatch):
        field, _backend = self._make_field_with_real_faiss(tmp_path)
        layer = WikiLayer(field, tmp_path / "wiki", use_snapshot=True)
        import pickle as _pickle

        real_load = _pickle.load
        call_count = {"n": 0}

        def flaky_load(f, *a, **kw):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise _pickle.UnpicklingError("simulated")
            return real_load(f, *a, **kw)

        monkeypatch.setattr(wiki_layer_module._pickle, "load", flaky_load)
        snap = layer._create_snapshot()
        assert snap is not None
        layer._cleanup_snapshot(snap)


# ---------------------------------------------------------------------------
# E. FAISS-backed clustering (Fix 2)
# ---------------------------------------------------------------------------


class TestFAISSClustering:
    """`_cluster_records` の FAISS 経路 / fallback 経路を検証する。"""

    def _gen_records(self, n: int, dim: int = 8) -> list[dict]:
        import random
        random.seed(42)
        recs: list[dict] = []
        for i in range(n):
            # 2 つの直交クラスタ: 偶数 idx は [1,0,...]、奇数 idx は [0,1,0,...]
            if i % 2 == 0:
                vec = [1.0 + random.uniform(-0.05, 0.05)] + [random.uniform(-0.02, 0.02) for _ in range(dim - 1)]
            else:
                vec = [random.uniform(-0.02, 0.02), 1.0 + random.uniform(-0.05, 0.05)] + [0.0] * (dim - 2)
            recs.append({
                "chunk_id": f"r{i}",
                "parent_id": f"doc_{i}",
                "vector": vec,
                "density": 0.5,
            })
        return recs

    def test_faiss_path_matches_inmemory_for_50_vectors(self, tmp_path: Path):
        """N=50 で FAISS 経路と in-memory 経路のクラスタ数が ±10% で一致する。"""
        layer = _make_layer(tmp_path, records=[])
        recs = self._gen_records(50)
        cl_faiss = layer._cluster_records(recs, k_neighbors=5, similarity_threshold=0.7)
        cl_mem = layer._cluster_records_inmemory(recs, k_neighbors=5, similarity_threshold=0.7)
        # cluster 数の差は 10% 以内 (最低 1 件は許容)
        tolerance = max(1, len(cl_mem) // 10)
        assert abs(len(cl_faiss) - len(cl_mem)) <= tolerance

    def test_small_n_uses_inmemory(self, tmp_path: Path, caplog):
        """N<32 の場合は in-memory 経路がログに記録される。"""
        import logging
        layer = _make_layer(tmp_path, records=[])
        recs = self._gen_records(10)
        with caplog.at_level(logging.INFO, logger="mekhane.anamnesis.wiki_layer"):
            layer._cluster_records(recs, k_neighbors=3)
        assert any("in-memory path" in rec.message for rec in caplog.records)

    def test_faiss_unavailable_fallback(self, tmp_path: Path, monkeypatch):
        """faiss import 失敗時に in-memory 経路へ落ち、例外を投げない。"""
        layer = _make_layer(tmp_path, records=[])
        recs = self._gen_records(40)
        import builtins
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "faiss":
                raise ImportError("simulated faiss unavailable")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        clusters = layer._cluster_records(recs, k_neighbors=5)
        assert clusters  # 空でない
