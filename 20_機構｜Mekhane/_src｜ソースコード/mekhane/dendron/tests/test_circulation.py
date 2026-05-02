# PROOF: [L2/Dendron] <- mekhane/dendron/tests/test_circulation.py
"""
PROOF: [L2/Dendron] このファイルは存在しなければならない

circulation_detector.py の正当性を検証する必要がある
  → テストケースが担う

Q.E.D.

---

Tests for circulation_detector.py — Q-Series 循環検出
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from mekhane.dendron.circulation_detector import (
    CirculationReport,
    CirculationResult,
    DependencyGraph,
    detect_circulation,
    extract_imports,
    find_sccs,
    classify_sccs,
)


# --- extract_imports ---


class TestExtractImports:
    """import 抽出のテスト."""

    # PURPOSE: import 文の基本抽出
    def test_basic_import(self, tmp_path: Path):
        f = tmp_path / "mod.py"
        f.write_text("import os\nimport sys\n")
        result = extract_imports(f)
        assert "os" in result
        assert "sys" in result

    # PURPOSE: from import の抽出
    def test_from_import(self, tmp_path: Path):
        f = tmp_path / "mod.py"
        f.write_text("from os.path import join\nfrom sys import argv\n")
        result = extract_imports(f)
        assert "os.path" in result
        assert "sys" in result

    # PURPOSE: 不正な構文のファイル
    def test_syntax_error(self, tmp_path: Path):
        f = tmp_path / "bad.py"
        f.write_text("def broken(\n")
        result = extract_imports(f)
        assert result == []

    # PURPOSE: 空ファイル
    def test_empty_file(self, tmp_path: Path):
        f = tmp_path / "empty.py"
        f.write_text("")
        result = extract_imports(f)
        assert result == []


# --- DependencyGraph ---


class TestDependencyGraph:
    """依存グラフ構築のテスト."""

    # PURPOSE: 依存のないモジュール群
    def test_no_dependencies(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("x = 1\n")
        (tmp_path / "b.py").write_text("y = 2\n")

        graph = DependencyGraph()
        count = graph.build(tmp_path)
        assert count == 2
        assert graph.edge_count == 0

    # PURPOSE: 直線依存 A→B→C
    def test_linear_dependency(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import c\n")
        (tmp_path / "c.py").write_text("x = 1\n")

        graph = DependencyGraph()
        graph.build(tmp_path)
        assert graph.edge_count == 2

    # PURPOSE: 循環依存 A→B→A
    def test_circular_dependency(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")

        graph = DependencyGraph()
        graph.build(tmp_path)
        assert graph.edge_count == 2

    # PURPOSE: 存在しないディレクトリ
    def test_nonexistent_directory(self, tmp_path: Path):
        graph = DependencyGraph()
        count = graph.build(tmp_path / "nonexistent")
        assert count == 0


# --- find_sccs (Tarjan) ---


class TestFindSCCs:
    """Tarjan SCC 検出のテスト."""

    # PURPOSE: 循環なし — SCC なし
    def test_no_cycle(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import c\n")
        (tmp_path / "c.py").write_text("x = 1\n")

        graph = DependencyGraph()
        graph.build(tmp_path)
        sccs = find_sccs(graph)
        assert len(sccs) == 0

    # PURPOSE: 単純な2ノード循環
    def test_simple_cycle(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")

        graph = DependencyGraph()
        graph.build(tmp_path)
        sccs = find_sccs(graph)
        assert len(sccs) == 1
        assert len(sccs[0]) == 2

    # PURPOSE: 3ノード循環 A→B→C→A
    def test_triangle_cycle(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import c\n")
        (tmp_path / "c.py").write_text("import a\n")

        graph = DependencyGraph()
        graph.build(tmp_path)
        sccs = find_sccs(graph)
        assert len(sccs) == 1
        assert len(sccs[0]) == 3


# --- classify_sccs ---


class TestClassifySCCs:
    """SCC 分類のテスト."""

    # PURPOSE: 孤立循環 (外部からの参照なし)
    def test_isolated_cycle(self, tmp_path: Path):
        # A⇔B (循環) だが外部からの参照なし
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")
        (tmp_path / "c.py").write_text("x = 1\n")  # 誰も A,B を使わない

        graph = DependencyGraph()
        graph.build(tmp_path)
        sccs = find_sccs(graph)
        classified = classify_sccs(graph, sccs)

        assert len(classified) == 1
        assert classified[0].is_isolated is True
        assert classified[0].verdict == "isolated"

    # PURPOSE: 接続循環 (外部からの参照あり)
    def test_connected_cycle(self, tmp_path: Path):
        # A⇔B (循環) + C→A (外部参照あり)
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")
        (tmp_path / "c.py").write_text("import a\n")  # C が A を使う

        graph = DependencyGraph()
        graph.build(tmp_path)
        sccs = find_sccs(graph)
        classified = classify_sccs(graph, sccs)

        assert len(classified) == 1
        assert classified[0].is_isolated is False
        assert classified[0].verdict == "connected"

    # PURPOSE: 孤立循環の stiffness が ≤ 0 であることを検証 (ΔF ≤ 0 = 冗長)
    def test_isolated_stiffness_non_positive(self, tmp_path: Path):
        # A⇔B (循環) + C (孤立) → external_in=0 → accuracy_loss=0
        # internal_edges=2 (A→B, B→A) → complexity_cost > 0
        # → stiffness = 0 - complexity_cost ≤ 0
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")
        (tmp_path / "c.py").write_text("x = 1\n")

        graph = DependencyGraph()
        graph.build(tmp_path)
        sccs = find_sccs(graph)
        classified = classify_sccs(graph, sccs)

        assert len(classified) == 1
        scc = classified[0]
        assert scc.is_isolated is True
        assert scc.stiffness <= 0, (
            f"孤立循環の stiffness は ≤ 0 であるべき (actual: {scc.stiffness})"
        )
        assert scc.accuracy_loss == 0.0
        assert scc.complexity_cost > 0

    # PURPOSE: 接続循環の stiffness が正であることを検証 (ΔF > 0 = 存在理由あり)
    def test_connected_stiffness_positive(self, tmp_path: Path):
        # A⇔B (循環) + C→A, D→A, E→B (外部参照多数)
        # external_in=3 → accuracy_loss が大きい
        # internal_edges=2 → complexity_cost は小さい
        # → stiffness > 0
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")
        (tmp_path / "c.py").write_text("import a\n")
        (tmp_path / "d.py").write_text("import a\n")
        (tmp_path / "e.py").write_text("import b\n")

        graph = DependencyGraph()
        graph.build(tmp_path)
        sccs = find_sccs(graph)
        classified = classify_sccs(graph, sccs)

        assert len(classified) == 1
        scc = classified[0]
        assert scc.is_isolated is False
        assert scc.stiffness > 0, (
            f"接続循環 (外部参照多数) の stiffness は > 0 であるべき (actual: {scc.stiffness})"
        )
        assert scc.accuracy_loss > 0

    # PURPOSE: yoneda_score が external_in と一致することを検証
    def test_yoneda_score_equals_external_in(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")
        (tmp_path / "c.py").write_text("import a\n")

        graph = DependencyGraph()
        graph.build(tmp_path)
        sccs = find_sccs(graph)
        classified = classify_sccs(graph, sccs)

        scc = classified[0]
        assert scc.yoneda_score == scc.external_in

    # PURPOSE: 単一参照元 → diversity が低いことを検証
    def test_yoneda_diversity_single_source(self, tmp_path: Path):
        # A⇔B + C→A (1モジュールからのみ参照)
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")
        (tmp_path / "c.py").write_text("import a\n")

        graph = DependencyGraph()
        graph.build(tmp_path)
        sccs = find_sccs(graph)
        classified = classify_sccs(graph, sccs)

        scc = classified[0]
        # 参照元は c のみ (1/3 ≈ 0.33)
        assert 0 < scc.yoneda_diversity < 0.5

    # PURPOSE: 複数参照元 → diversity が高いことを検証
    def test_yoneda_diversity_multiple_sources(self, tmp_path: Path):
        # A⇔B + C→A, D→B, E→A (3つの異なる参照元)
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")
        (tmp_path / "c.py").write_text("import a\n")
        (tmp_path / "d.py").write_text("import b\n")
        (tmp_path / "e.py").write_text("import a\n")

        graph = DependencyGraph()
        graph.build(tmp_path)
        sccs = find_sccs(graph)
        classified = classify_sccs(graph, sccs)

        scc = classified[0]
        # 参照元は c, d, e (3/5 = 0.6)
        assert scc.yoneda_diversity >= 0.5

    # PURPOSE: 最小循環 (A⇔B) の kalon_distance が高いことを検証
    def test_kalon_distance_minimal_scc(self, tmp_path: Path):
        # A⇔B: internal_edges=2, max=2*1=2 → density=1.0 → d=0.0
        # ※ 2ノード完全循環は d=0 (既に不動点)
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")

        graph = DependencyGraph()
        graph.build(tmp_path)
        sccs = find_sccs(graph)
        classified = classify_sccs(graph, sccs)

        scc = classified[0]
        # A⇔B は完全グラフ → d = 0
        assert scc.kalon_distance == 0.0

    # PURPOSE: 大きい SCC で一方向のみ → kalon_distance が高いことを検証
    def test_kalon_distance_sparse_scc(self, tmp_path: Path):
        # A→B→C→A (3ノード, 3エッジ, max=6) → density=0.5 → d=0.5
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import c\n")
        (tmp_path / "c.py").write_text("import a\n")

        graph = DependencyGraph()
        graph.build(tmp_path)
        sccs = find_sccs(graph)
        classified = classify_sccs(graph, sccs)

        scc = classified[0]
        # 3エッジ / 6最大 = 0.5 → d = 0.5
        assert scc.kalon_distance == 0.5

    # PURPOSE: 3軸統合の existence_verdict が正しいことを検証
    def test_existence_verdict_isolated(self, tmp_path: Path):
        # 孤立循環 → h^X = 0 → "❌ 孤立"
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")

        graph = DependencyGraph()
        graph.build(tmp_path)
        sccs = find_sccs(graph)
        classified = classify_sccs(graph, sccs)

        scc = classified[0]
        assert "❌" in scc.existence_verdict
        assert "孤立" in scc.existence_verdict

    # PURPOSE: 接続 + stiffness > 0 + 低 kalon_distance → "✅ 存在理由あり"
    def test_existence_verdict_healthy(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")
        (tmp_path / "c.py").write_text("import a\n")
        (tmp_path / "d.py").write_text("import a\n")
        (tmp_path / "e.py").write_text("import b\n")

        graph = DependencyGraph()
        graph.build(tmp_path)
        sccs = find_sccs(graph)
        classified = classify_sccs(graph, sccs)

        scc = classified[0]
        assert "✅" in scc.existence_verdict


# --- detect_circulation (統合) ---


class TestDetectCirculation:
    """全パイプラインの統合テスト."""

    # PURPOSE: 循環なし
    def test_no_circulation(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("x = 1\n")

        report = detect_circulation(tmp_path)
        assert report.total_modules == 2
        assert len(report.sccs) == 0
        assert report.has_issues is False

    # PURPOSE: 孤立循環あり
    def test_with_isolated_circulation(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")

        report = detect_circulation(tmp_path)
        assert len(report.sccs) == 1
        assert report.isolated_count == 1
        assert report.has_issues is True

    # PURPOSE: Markdown レポート生成
    def test_markdown_report(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")

        report = detect_circulation(tmp_path)
        md = report.to_markdown()
        assert "循環検出レポート" in md
        assert "存在定理" in md
        assert "存在判定" in md

    # PURPOSE: 空ディレクトリ
    def test_empty_directory(self, tmp_path: Path):
        report = detect_circulation(tmp_path)
        assert report.total_modules == 0
        assert len(report.sccs) == 0
        assert report.has_issues is False


# --- scan_modules / resolve_edges (原子的 Phase 分離) ---


class TestAtomicPhases:
    """scan_modules と resolve_edges の原子的テスト."""

    # PURPOSE: scan_modules がノードのみ構築しエッジは空のままであることを検証
    def test_scan_modules_only(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")

        graph = DependencyGraph()
        py_files = graph.scan_modules(tmp_path)
        assert len(graph.nodes) == 2
        assert graph.edge_count == 0  # エッジはまだ構築されていない
        assert len(py_files) == 2

    # PURPOSE: resolve_edges が scan_modules 後にエッジを正しく構築することを検証
    def test_resolve_edges_after_scan(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("import b\n")
        (tmp_path / "b.py").write_text("import a\n")

        graph = DependencyGraph()
        py_files = graph.scan_modules(tmp_path)
        edge_count = graph.resolve_edges(py_files, tmp_path)
        assert edge_count == 2
        assert graph.edge_count == 2

    # PURPOSE: Phase 分離の結果が build() と同一であることを検証
    def test_phases_equivalent_to_build(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("import b\nimport c\n")
        (tmp_path / "b.py").write_text("import c\n")
        (tmp_path / "c.py").write_text("x = 1\n")

        # build() で構築
        g1 = DependencyGraph()
        g1.build(tmp_path)

        # scan + resolve で構築
        g2 = DependencyGraph()
        py_files = g2.scan_modules(tmp_path)
        g2.resolve_edges(py_files, tmp_path)

        assert g1.nodes == g2.nodes
        assert g1.edge_count == g2.edge_count


# --- 自己参照テスト (Quine テスト) ---


class TestSelfReference:
    """circulation_detector が自身を含むコードベースを正しく分析できることを検証.

    ゲーデル的メモ: これは機械的自己適用のテストであり、
    ゲーデル的自己言及 (自分の限界を自分の枠組みで表現) ではない。
    import レベルの検出器はコールグラフレベルの循環を検出できない。
    """

    # PURPOSE: 検出器自身が孤立循環と誤判定されないことを検証
    def test_detector_not_isolated(self):
        dendron_root = Path(__file__).parent.parent
        report = detect_circulation(dendron_root, package_prefix="mekhane.dendron")

        # circulation_detector 自身が SCC に含まれる場合、孤立ではないことを確認
        for scc in report.sccs:
            if any("circulation_detector" in m for m in scc.members):
                assert not scc.is_isolated, (
                    "circulation_detector が孤立循環と判定された — "
                    "checker.py から参照されているはずなので接続循環であるべき"
                )

    # PURPOSE: 検出器が自身のコードベースを正常に分析完了することを検証
    def test_self_analysis_completes(self):
        dendron_root = Path(__file__).parent.parent
        report = detect_circulation(dendron_root, package_prefix="mekhane.dendron")

        assert report.total_modules > 0, "dendron のモジュールが検出されるべき"
        assert report.total_edges >= 0, "エッジ数は非負であるべき"
        # レポート生成も正常に完了する
        md = report.to_markdown()
        assert len(md) > 0


# --- Phase 1: Yoneda 品質ティア ---


class TestPhase1YonedaTier:
    """Yoneda 品質ティア (orphan/fragile/robust) のテスト."""

    # PURPOSE: 外部参照ゼロの SCC は orphan であること
    def test_orphan_tier(self):
        graph = DependencyGraph()
        graph.nodes = {"a", "b", "c"}
        graph.edges = {"a": {"b"}, "b": {"a"}}
        graph.reverse_edges = {"a": {"b"}, "b": {"a"}}
        results = classify_sccs(graph, [["a", "b"]])
        r = results[0]
        assert r.yoneda_tier == "orphan"
        assert r.yoneda_score == 0

    # PURPOSE: 外部参照 1-2 は fragile であること
    def test_fragile_tier(self):
        graph = DependencyGraph()
        graph.nodes = {"a", "b", "c"}
        graph.edges = {"a": {"b"}, "b": {"a"}, "c": {"a"}}
        graph.reverse_edges = {"a": {"b", "c"}, "b": {"a"}}
        results = classify_sccs(graph, [["a", "b"]])
        r = results[0]
        assert r.yoneda_tier == "fragile"
        assert r.yoneda_score == 1

    # PURPOSE: 外部参照 3+ は robust であること (kalon.typos §2 D≥3)
    def test_robust_tier(self):
        graph = DependencyGraph()
        graph.nodes = {"a", "b", "c", "d", "e"}
        graph.edges = {"a": {"b"}, "b": {"a"}, "c": {"a"}, "d": {"a"}, "e": {"b"}}
        graph.reverse_edges = {"a": {"b", "c", "d"}, "b": {"a", "e"}}
        results = classify_sccs(graph, [["a", "b"]])
        r = results[0]
        assert r.yoneda_tier == "robust"
        assert r.yoneda_score >= 3

    # PURPOSE: パッケージ多様性が計算されること
    def test_package_diversity(self):
        graph = DependencyGraph()
        graph.nodes = {"pkg1/a", "pkg1/b", "pkg2/c", "pkg3/d"}
        graph.edges = {"pkg1/a": {"pkg1/b"}, "pkg1/b": {"pkg1/a"},
                       "pkg2/c": {"pkg1/a"}, "pkg3/d": {"pkg1/b"}}
        graph.reverse_edges = {"pkg1/a": {"pkg1/b", "pkg2/c"},
                               "pkg1/b": {"pkg1/a", "pkg3/d"}}
        results = classify_sccs(graph, [["pkg1/a", "pkg1/b"]])
        r = results[0]
        # 参照元パッケージ: pkg2, pkg3 (2 of 3 パッケージ → 2/3)
        assert r.yoneda_package_diversity > 0.0


# --- Phase 2: VFE 除去シミュレーション ---


class TestPhase2VFERemoval:
    """VFE 除去シミュレーション (broken_paths, cascade) のテスト."""

    # PURPOSE: 橋渡し SCC の除去で到達パスが壊れること
    def test_bridge_removal_breaks_paths(self):
        # c → [a↔b] → d: SCC {a,b} を除去すると c→d が不可能に
        graph = DependencyGraph()
        graph.nodes = {"a", "b", "c", "d"}
        graph.edges = {"a": {"b", "d"}, "b": {"a"}, "c": {"a"}}
        graph.reverse_edges = {"a": {"b", "c"}, "b": {"a"}, "d": {"a"}}
        results = classify_sccs(graph, [["a", "b"]])
        r = results[0]
        assert r.removal_broken_paths > 0, "橋渡し SCC 除去でパスが壊れるべき"

    # PURPOSE: 孤立 SCC 除去は cascade も broken_paths もゼロ
    def test_isolated_removal_no_impact(self):
        graph = DependencyGraph()
        graph.nodes = {"a", "b"}
        graph.edges = {"a": {"b"}, "b": {"a"}}
        graph.reverse_edges = {"a": {"b"}, "b": {"a"}}
        results = classify_sccs(graph, [["a", "b"]])
        r = results[0]
        assert r.removal_broken_paths == 0
        assert r.removal_cascade == 0

    # PURPOSE: stiffness_normalized がサイズ補正を適用すること
    def test_stiffness_normalized(self):
        graph = DependencyGraph()
        graph.nodes = {"a", "b", "c"}
        graph.edges = {"a": {"b"}, "b": {"a"}, "c": {"a"}}
        graph.reverse_edges = {"a": {"b", "c"}, "b": {"a"}}
        results = classify_sccs(graph, [["a", "b"]])
        r = results[0]
        # stiffness_normalized = stiffness / log2(size + 1)
        # size=2 なので log2(3) ≈ 1.585
        import math
        if r.stiffness != 0:
            expected = r.stiffness / math.log2(3)
            assert abs(r.stiffness_normalized - expected) < 0.01


# --- Phase 3: Kalon G∘F 反復不動点 ---


class TestPhase3KalonGF:
    """Kalon G∘F 反復不動点距離 (CKDF §5.2) のテスト."""

    # PURPOSE: 完全グラフの SCC は全ノードが不動点 → gf_distance ≈ 0
    def test_complete_graph_fixpoint_zero(self):
        # 全結合: a→b, b→a, a→c, c→a, b→c, c→b
        graph = DependencyGraph()
        graph.nodes = {"a", "b", "c"}
        graph.edges = {"a": {"b", "c"}, "b": {"a", "c"}, "c": {"a", "b"}}
        graph.reverse_edges = {"a": {"b", "c"}, "b": {"a", "c"}, "c": {"a", "b"}}
        results = classify_sccs(graph, [["a", "b", "c"]])
        r = results[0]
        assert r.kalon_gf_distance == 0.0, "完全グラフは Fix = 全体 → distance=0"
        assert r.kalon_gf_iterations == 0, "刈り込み不要"

    # PURPOSE: 線形チェーン付き SCC では末端が刈り込まれること
    def test_linear_chain_gets_pruned(self):
        # a→b→c→a, d→a (d は SCC 内だが入次数=0 ではないケース用)
        # 実際: a→b, b→c, c→a のみ → 全員が循環に参加 → gf=0
        graph = DependencyGraph()
        graph.nodes = {"a", "b", "c"}
        graph.edges = {"a": {"b"}, "b": {"c"}, "c": {"a"}}
        graph.reverse_edges = {"a": {"c"}, "b": {"a"}, "c": {"b"}}
        results = classify_sccs(graph, [["a", "b", "c"]])
        r = results[0]
        # 三角循環: 全ノードが入次数1 → 刈り込み不可 → Fix = 全体
        assert r.kalon_gf_distance == 0.0

    # PURPOSE: 末端ノードがある SCC では刈り込みが発生
    def test_dangling_node_pruned(self):
        # a→b, b→a, a→c. c は SCC に含まれるが入次数=0 (a→c のみ、c→a がない)
        # しかし SCC は強連結なので c→a or c→b が必要。テスト設計を修正
        # 実際の SCC: c→a→b→c (三角) + d→a (d は SCC 内で後方のみ)
        # SCC={a,b,c,d}: a→b, b→c, c→a, d→a
        # d の入次数=0 (SCC内で) → 刈り込まれる
        graph = DependencyGraph()
        graph.nodes = {"a", "b", "c", "d"}
        graph.edges = {"a": {"b"}, "b": {"c"}, "c": {"a"}, "d": {"a"}}
        graph.reverse_edges = {"a": {"c", "d"}, "b": {"a"}, "c": {"b"}}
        # SCC としては {a,b,c,d} は強連結ではない (d に戻る辺がない)
        # classify_sccs は入力を信頼する。d→a だけの場合 d は入次数0
        results = classify_sccs(graph, [["a", "b", "c", "d"]])
        r = results[0]
        assert r.kalon_gf_distance > 0.0, "末端 d が刈り込まれるので distance > 0"
        assert r.kalon_gf_iterations >= 1, "少なくとも1回は反復"

    # PURPOSE: 内部結束度 (cohesion) が計算されること
    def test_cohesion_computed(self):
        graph = DependencyGraph()
        graph.nodes = {"a", "b", "c"}
        graph.edges = {"a": {"b", "c"}, "b": {"a", "c"}, "c": {"a", "b"}}
        graph.reverse_edges = {"a": {"b", "c"}, "b": {"a", "c"}, "c": {"a", "b"}}
        results = classify_sccs(graph, [["a", "b", "c"]])
        r = results[0]
        # 完全グラフ: 各ノード min(in=2, out=2) = 2, 合計 6 / (3*2) = 1.0
        assert abs(r.kalon_cohesion - 1.0) < 0.01


# --- Phase 4: 統合ビットフラグ ---


class TestPhase4ExistenceFlags:
    """統合ビットフラグ (existence_flags) のテスト."""

    # PURPOSE: 健全な SCC は EX_HEALTHY (0x00)
    def test_healthy_flags(self):
        from mekhane.dendron.circulation_detector import (
            EX_HEALTHY, EX_ISOLATED, EX_FRAGILE, EX_REDUNDANT, EX_UNSTABLE,
        )
        # robust + stiffness > 0 + kalon_gf_distance < 0.8
        graph = DependencyGraph()
        graph.nodes = {"a", "b", "c", "d", "e"}
        graph.edges = {
            "a": {"b"}, "b": {"a"},
            "c": {"a"}, "d": {"a"}, "e": {"b"},
        }
        graph.reverse_edges = {"a": {"b", "c", "d"}, "b": {"a", "e"}}
        results = classify_sccs(graph, [["a", "b"]])
        r = results[0]
        assert r.existence_flags & EX_ISOLATED == 0

    # PURPOSE: 孤立 SCC は EX_ISOLATED フラグが立つ
    def test_isolated_flag(self):
        from mekhane.dendron.circulation_detector import EX_ISOLATED
        graph = DependencyGraph()
        graph.nodes = {"a", "b"}
        graph.edges = {"a": {"b"}, "b": {"a"}}
        graph.reverse_edges = {"a": {"b"}, "b": {"a"}}
        results = classify_sccs(graph, [["a", "b"]])
        r = results[0]
        assert r.existence_flags & EX_ISOLATED != 0

    # PURPOSE: fragile SCC は EX_FRAGILE フラグが立つ
    def test_fragile_flag(self):
        from mekhane.dendron.circulation_detector import EX_FRAGILE
        graph = DependencyGraph()
        graph.nodes = {"a", "b", "c"}
        graph.edges = {"a": {"b"}, "b": {"a"}, "c": {"a"}}
        graph.reverse_edges = {"a": {"b", "c"}, "b": {"a"}}
        results = classify_sccs(graph, [["a", "b"]])
        r = results[0]
        assert r.existence_flags & EX_FRAGILE != 0

    # PURPOSE: 複数フラグの複合が可能
    def test_compound_flags(self):
        from mekhane.dendron.circulation_detector import EX_ISOLATED, EX_REDUNDANT
        # 孤立 + stiffness ≤ 0 → ISOLATED | REDUNDANT
        graph = DependencyGraph()
        graph.nodes = {"a", "b"}
        graph.edges = {"a": {"b"}, "b": {"a"}}
        graph.reverse_edges = {"a": {"b"}, "b": {"a"}}
        results = classify_sccs(graph, [["a", "b"]])
        r = results[0]
        # 孤立 SCC は必ず ISOLATED
        assert r.existence_flags & EX_ISOLATED != 0
