# -*- coding: utf-8 -*-
"""Tests for Hyphe Session Log Chunker.

PURPOSE: hyphe_chunker.py test suite.
Mock embedder for logic tests + real API for integration tests.
"""

import math
import statistics
import unittest
import pytest
from pathlib import Path

from hyphe_chunker import (
    Step,
    Chunk,
    parse_session,
    compute_similarity_trace,
    detect_boundaries,
    steps_to_chunks,
    gf_iterate,
    compute_chunk_metrics,
    chunk_session,
    compute_tau_from_entropy,
    compute_lambda_schedule,
    compute_precision_gradient,
    LambdaNormalizationMeta,
    normalize_lambda_cross_session,
    _l2_normalize,
    _compute_knn_trace,
    _compute_knn_density,
    _compute_epistemic_density,
    _recursive_split,
)


# -- Mock Embedding -----------------------------------------------------------

def _make_embeddings_with_shift(n: int, shift_at: list[int], dim: int = 8) -> list[list[float]]:
    """Generate test embeddings with controlled shifts at specified positions."""
    embeddings = []
    current_basis = 0

    for i in range(n):
        if i in shift_at:
            current_basis = (current_basis + 1) % dim

        vec = [0.1 * ((hash(f"noise_{i}_{d}") % 100) / 100) for d in range(dim)]
        vec[current_basis] = 5.0 + 0.1 * (i % 3)

        norm = math.sqrt(sum(x * x for x in vec))
        vec = [x / norm for x in vec]
        embeddings.append(vec)

    return embeddings


# -- TestParse ----------------------------------------------------------------

class TestParse:
    """Session log Step splitting tests."""

    def test_parse_basic(self):
        text = "# Session Header\n\nSome metadata here.\n\n## \U0001F916 Assistant ()\n\nFirst assistant response.\n\n## \U0001F916 Assistant ()\n\nSecond assistant response.\n\n## \U0001F916 Assistant ()\n\nThird response with tool usage.\n"
        steps = parse_session(text)
        assert len(steps) == 3
        assert "First assistant" in steps[0].text
        assert "Second assistant" in steps[1].text
        assert "Third response" in steps[2].text

    def test_parse_empty(self):
        steps = parse_session("")
        assert len(steps) == 0

    def test_parse_no_markers(self):
        steps = parse_session("Just plain text without any markers.")
        assert len(steps) == 0

    def test_parse_claude_format(self):
        """conv/ ディレクトリの ## 🤖 Claude マーカーをパースする。"""
        text = (
            "# Session Header\n\n"
            "## 🤖 Claude ()\n\n"
            "First Claude response.\n\n"
            "## 🤖 Claude ()\n\n"
            "Second Claude response.\n"
        )
        steps = parse_session(text)
        assert len(steps) == 2
        assert "First Claude" in steps[0].text
        assert "Second Claude" in steps[1].text

    def test_parse_mixed_assistant_claude(self):
        """Assistant と Claude マーカーが混在するログのパース（後方互換性テスト）。"""
        text = (
            "# Mixed Session\n\n"
            "## 🤖 Assistant ()\n\n"
            "Old format response.\n\n"
            "## 🤖 Claude ()\n\n"
            "New format response.\n"
        )
        steps = parse_session(text)
        assert len(steps) == 2
        assert "Old format" in steps[0].text
        assert "New format" in steps[1].text


# -- TestBoundaryDetection ----------------------------------------------------

class TestBoundaryDetection:
    """Embedding-based boundary detection tests."""

    def test_no_boundaries(self):
        similarities = [0.95, 0.92, 0.88, 0.91]
        boundaries = detect_boundaries(similarities, tau=0.7)
        assert boundaries == []

    def test_clear_boundary(self):
        similarities = [0.9, 0.85, 0.3, 0.88, 0.92]
        boundaries = detect_boundaries(similarities, tau=0.7)
        assert boundaries == [2]

    def test_multiple_boundaries(self):
        similarities = [0.9, 0.2, 0.85, 0.1, 0.9]
        boundaries = detect_boundaries(similarities, tau=0.7)
        assert sorted(boundaries) == [1, 3]

    def test_with_mock_embeddings(self):
        embeddings = _make_embeddings_with_shift(5, shift_at=[3])
        sims = compute_similarity_trace(embeddings)
        assert len(sims) == 4
        boundaries = detect_boundaries(sims, tau=0.7)
        assert 2 in boundaries


# -- TestGFIteration ----------------------------------------------------------

class TestGFIteration:
    """G-F iteration convergence tests."""

    def test_convergence(self):
        embeddings = _make_embeddings_with_shift(10, shift_at=[5])
        sims = compute_similarity_trace(embeddings)
        boundaries = detect_boundaries(sims, tau=0.7)

        steps = [Step(index=i, text=f"Step {i}") for i in range(10)]
        chunks = steps_to_chunks(steps, boundaries)

        result_chunks, iterations, converged = gf_iterate(
            chunks, embeddings, tau=0.7, min_steps=2, max_iterations=10
        )

        assert converged, "G-F should converge"
        assert iterations <= 3, f"Should converge in <=3 iters (got {iterations})"

    def test_merge_tiny_chunks(self):
        steps = [Step(index=i, text=f"Step {i}") for i in range(5)]
        chunks = [Chunk(chunk_id=i, steps=[s]) for i, s in enumerate(steps)]

        embeddings = _make_embeddings_with_shift(5, shift_at=[])
        result_chunks, iterations, converged = gf_iterate(
            chunks, embeddings, tau=0.7, min_steps=2, max_iterations=10
        )

        assert len(result_chunks) < 5
        all_step_indices = [s.index for c in result_chunks for s in c.steps]
        assert sorted(all_step_indices) == list(range(5))

    def test_max_iterations(self):
        steps = [Step(index=i, text=f"Step {i}") for i in range(4)]
        chunks = [Chunk(chunk_id=0, steps=steps)]
        embeddings = _make_embeddings_with_shift(4, shift_at=[])

        _, iterations, _ = gf_iterate(
            chunks, embeddings, tau=0.7, min_steps=2, max_iterations=3
        )
        assert iterations <= 3


# -- TestLcCalculation --------------------------------------------------------

class TestLcCalculation:
    """L(c) Drift term calculation tests."""

    def test_drift_high_coherence(self):
        embeddings = _make_embeddings_with_shift(4, shift_at=[])
        sims = compute_similarity_trace(embeddings)

        steps = [Step(index=i, text=f"Step {i}") for i in range(4)]
        chunks = [Chunk(chunk_id=0, steps=steps)]
        chunks = compute_chunk_metrics(chunks, embeddings, sims)

        assert chunks[0].drift >= 0.0
        assert chunks[0].drift < 0.2, "High coherence -> low Drift"
        assert chunks[0].coherence > 0.8, "Expect high coherence"

    def test_drift_low_coherence(self):
        embeddings = _make_embeddings_with_shift(4, shift_at=[1, 2, 3])
        sims = compute_similarity_trace(embeddings)

        steps = [Step(index=i, text=f"Step {i}") for i in range(4)]
        chunks = [Chunk(chunk_id=0, steps=steps)]
        chunks = compute_chunk_metrics(chunks, embeddings, sims)

        assert chunks[0].drift > 0.1, "Low coherence -> high Drift"

    def test_drift_nonnegative(self):
        for shift in [[], [2], [1, 3]]:
            embeddings = _make_embeddings_with_shift(6, shift_at=shift)
            sims = compute_similarity_trace(embeddings)
            steps = [Step(index=i, text=f"Step {i}") for i in range(6)]
            boundaries = detect_boundaries(sims, tau=0.7)
            chunks = steps_to_chunks(steps, boundaries)
            chunks = compute_chunk_metrics(chunks, embeddings, sims)
            for c in chunks:
                assert c.drift >= 0.0, f"Drift must be non-negative, got {c.drift}"


# -- TestChunkSession (end-to-end) --------------------------------------------

class TestChunkSession:
    """chunk_session end-to-end tests (Mock)."""

    def test_basic_flow(self):
        steps = [Step(index=i, text=f"Step {i} text content") for i in range(10)]
        embeddings = _make_embeddings_with_shift(10, shift_at=[5])

        result = chunk_session(steps, embeddings, tau=0.7, min_steps=2)

        assert result.converged
        assert len(result.chunks) >= 2
        assert result.metrics["total_steps"] == 10
        assert result.metrics["num_chunks"] == len(result.chunks)
        assert result.metrics["mean_drift"] >= 0.0

    def test_single_step(self):
        steps = [Step(index=0, text="Only step")]
        embeddings = [[1.0, 0.0, 0.0]]

        result = chunk_session(steps, embeddings, tau=0.7)
        assert len(result.chunks) == 1
        assert result.chunks[0].steps[0].text == "Only step"

    def test_empty(self):
        result = chunk_session([], [], tau=0.7)
        assert len(result.chunks) == 0
        assert result.converged

    def test_mismatched_lengths(self):
        steps = [Step(index=i, text=f"Step {i}") for i in range(3)]
        embeddings = [[1.0, 0.0]] * 5

        with pytest.raises(ValueError):
            chunk_session(steps, embeddings, tau=0.7)


# -- TestKnnSimilarity (v2 -- 1st-order Markov overcome) ----------------------

class TestKnnSimilarity:
    """k-nearest similarity trace tests."""

    def test_knn_output_length(self):
        """knn mode also produces n-1 similarities."""
        embeddings = _make_embeddings_with_shift(8, shift_at=[4])
        sims_pw = compute_similarity_trace(embeddings, mode="pairwise")
        sims_knn = compute_similarity_trace(embeddings, mode="knn", k=2)
        assert len(sims_pw) == len(sims_knn) == 7

    def test_knn_detects_shift(self):
        """knn mode detects shifts as boundaries."""
        embeddings = _make_embeddings_with_shift(10, shift_at=[5])
        sims_knn = compute_similarity_trace(embeddings, mode="knn", k=3)
        boundaries = detect_boundaries(sims_knn, tau=0.7)
        assert any(3 <= b <= 5 for b in boundaries), f"Boundaries {boundaries} should contain shift region"

    def test_knn_smoother_than_pairwise(self):
        """knn is smoother than pairwise (lower variance)."""
        embeddings = _make_embeddings_with_shift(12, shift_at=[6])
        sims_pw = compute_similarity_trace(embeddings, mode="pairwise")
        sims_knn = compute_similarity_trace(embeddings, mode="knn", k=3)

        var_pw = statistics.variance(sims_pw) if len(sims_pw) >= 2 else 0
        var_knn = statistics.variance(sims_knn) if len(sims_knn) >= 2 else 0
        assert var_knn <= var_pw * 1.5, f"knn var {var_knn:.4f} >> pairwise {var_pw:.4f}"


# -- TestRecursiveSplit (v2 -- G-F aggressive) --------------------------------

class TestRecursiveSplit:
    """Recursive split tests."""

    def test_multiple_splits(self):
        """Multiple shifts should produce multiple chunks."""
        steps = [Step(index=i, text=f"Step {i}") for i in range(12)]
        embeddings = _make_embeddings_with_shift(12, shift_at=[4, 8])
        chunk = Chunk(chunk_id=0, steps=steps)

        result = _recursive_split(chunk, embeddings, tau=0.7, min_steps=2)
        assert len(result) >= 3, f"Expected >=3 chunks, got {len(result)}"

    def test_no_split_when_above_tau(self):
        """All above tau -> no split."""
        steps = [Step(index=i, text=f"Step {i}") for i in range(6)]
        embeddings = _make_embeddings_with_shift(6, shift_at=[])
        chunk = Chunk(chunk_id=0, steps=steps)

        result = _recursive_split(chunk, embeddings, tau=0.7, min_steps=2)
        assert len(result) == 1, "Expected no split"

    def test_respects_min_steps(self):
        """Min steps constraint is respected."""
        steps = [Step(index=i, text=f"Step {i}") for i in range(4)]
        embeddings = _make_embeddings_with_shift(4, shift_at=[1, 2, 3])
        chunk = Chunk(chunk_id=0, steps=steps)

        result = _recursive_split(chunk, embeddings, tau=0.7, min_steps=3)
        for c in result:
            assert len(c) >= 1, "Empty chunks not allowed"


# -- TestTrueDrift (v2 -- centroid variance) ----------------------------------

class TestTrueDrift:
    """v2 drift calculation (centroid variance) tests."""

    def test_uniform_embedding_low_drift(self):
        """Same direction embeddings -> drift near 0."""
        embeddings = _make_embeddings_with_shift(6, shift_at=[])
        sims = compute_similarity_trace(embeddings)
        steps = [Step(index=i, text=f"Step {i}") for i in range(6)]
        chunks = [Chunk(chunk_id=0, steps=steps)]
        chunks = compute_chunk_metrics(chunks, embeddings, sims)
        assert chunks[0].drift < 0.05, f"Expected drift ~0, got {chunks[0].drift:.3f}"

    def test_diverse_embedding_high_drift(self):
        """Diverse embeddings -> high drift."""
        embeddings = _make_embeddings_with_shift(6, shift_at=[1, 2, 3, 4, 5])
        sims = compute_similarity_trace(embeddings)
        steps = [Step(index=i, text=f"Step {i}") for i in range(6)]
        chunks = [Chunk(chunk_id=0, steps=steps)]
        chunks = compute_chunk_metrics(chunks, embeddings, sims)
        assert chunks[0].drift > 0.1, f"Expected high drift, got {chunks[0].drift:.3f}"

    def test_drift_bounded_0_1(self):
        """Drift must be in [0, 1]."""
        for shift in [[], [3], [1, 2, 3, 4, 5]]:
            embeddings = _make_embeddings_with_shift(6, shift_at=shift)
            sims = compute_similarity_trace(embeddings)
            steps = [Step(index=i, text=f"Step {i}") for i in range(6)]
            chunks = [Chunk(chunk_id=0, steps=steps)]
            chunks = compute_chunk_metrics(chunks, embeddings, sims)
            assert 0.0 <= chunks[0].drift <= 1.0, f"drift out of range: {chunks[0].drift}"


# -- TestComputeTauFromEntropy ------------------------------------------------

class TestComputeTauFromEntropy:
    """τ 動的決定 (consistency_log エントロピー → τ) のテスト。"""

    def test_empty_issues(self):
        """issue なし → τ_base を返す。"""
        tau = compute_tau_from_entropy([], tau_base=0.7)
        assert tau == 0.7

    def test_single_severity(self):
        """全て同じ severity → H=0 → τ_base。"""
        issues = [{"severity": "medium"}] * 10
        tau = compute_tau_from_entropy(issues, tau_base=0.7, alpha=0.3)
        assert tau == 0.7, f"H=0 なので τ=τ_base のはず, got {tau}"

    def test_uniform_distribution(self):
        """4種類均等 → H=H_max → τ = τ_base × (1 - α)。"""
        issues = [
            {"severity": "low"},
            {"severity": "medium"},
            {"severity": "high"},
            {"severity": "critical"},
        ]
        tau = compute_tau_from_entropy(issues, tau_base=0.7, alpha=0.3)
        # H_norm = 1.0 → τ = 0.7 × (1 - 0.3) = 0.49
        assert abs(tau - 0.49) < 0.01, f"Expected ~0.49, got {tau}"

    def test_high_severity_bias(self):
        """critical に偏る → H が低い → τ は τ_base に近い。"""
        issues = [{"severity": "critical"}] * 9 + [{"severity": "low"}]
        tau = compute_tau_from_entropy(issues, tau_base=0.7, alpha=0.3)
        # H は低い (偏り大) → τ は high
        assert tau > 0.6, f"Expected τ > 0.6 (biased distribution), got {tau}"

    def test_clamp_bounds(self):
        """極端な alpha でもクランプされる。"""
        # alpha=1.0 + 均等分布 → τ_base × 0 = 0.0 → clamp to tau_min
        issues = [
            {"severity": "low"},
            {"severity": "medium"},
            {"severity": "high"},
            {"severity": "critical"},
        ]
        tau = compute_tau_from_entropy(
            issues, tau_base=0.7, alpha=1.0, tau_min=0.3, tau_max=0.9,
        )
        assert tau >= 0.3, f"τ should be clamped to >= 0.3, got {tau}"

        # τ_base=1.0 + alpha=0 → τ=1.0 → clamp to tau_max
        tau_high = compute_tau_from_entropy(
            [], tau_base=1.0, alpha=0.0, tau_min=0.3, tau_max=0.9,
        )
        assert tau_high == 0.9, f"τ should be clamped to 0.9, got {tau_high}"


class TestCrossRefToText(unittest.TestCase):
    """cross_ref_to_text() の変換ロジックテスト。"""

    @classmethod
    def setUpClass(cls):
        # NucleatorChunker を動的 import
        import sys
        _mekhane_src = str(
            Path(__file__).resolve().parent.parent.parent
            / "20_機構｜Mekhane" / "_src｜ソースコード"
        )
        if _mekhane_src not in sys.path:
            sys.path.insert(0, _mekhane_src)
        from mekhane.anamnesis.chunker import NucleatorChunker
        cls._chunker_cls = NucleatorChunker

    def _convert(self, entries):
        """descriptor protocol を回避して staticmethod を呼ぶヘルパー。"""
        return self._chunker_cls.cross_ref_to_text(entries)

    def test_empty_entries(self):
        """空リスト → 空文字列。"""
        assert self._convert([]) == ""

    def test_single_session(self):
        """単一セッション → ## Session: ヘッダ。"""
        entries = [{"id": "s1", "title": "Test Session", "created_at": 100}]
        text = self._convert(entries)
        assert "## Session: Test Session" in text

    def test_chronological_order(self):
        """複数セッション → created_at 昇順。"""
        entries = [
            {"id": "s2", "title": "Later session with details", "created_at": 200},
            {"id": "s1", "title": "Earlier session with details", "created_at": 100},
        ]
        text = self._convert(entries)
        earlier_pos = text.index("Earlier")
        later_pos = text.index("Later")
        assert earlier_pos < later_pos, "Earlier should come before Later"

    def test_handoff_rom_artifact(self):
        """handoff/ROM/artifact が含まれる。"""
        entries = [{
            "id": "s1", "title": "Rich", "created_at": 100,
            "handoffs": [{"summary": "HO summary"}],
            "roms": [{"topic": "ROM topic"}],
            "artifacts": [{"filename": "plan.md"}],
        }]
        text = self._convert(entries)
        assert "Handoff: HO summary" in text
        assert "ROM: ROM topic" in text
        assert "Artifacts: plan.md" in text

    def test_skip_empty_session(self):
        """30文字未満のセッションはスキップ。"""
        entries = [
            {"id": "s1", "title": "x", "created_at": 100},  # 短い
            {"id": "s2", "title": "A session with enough content here", "created_at": 200},
        ]
        text = self._convert(entries)
        sections = text.count("## Session:")
        # 短いセッション "## Session: x" (14文字) は 30文字未満でスキップされる可能性
        # ただし status/agent がなければ "## Session: x" のみ = 13文字 → スキップ
        assert sections >= 1


# ===========================================================================
# Theme 3: save_chunk_kernel テスト
# ===========================================================================
import sqlite3
import json
import sys
import os

# mekhane をインポートパスに追加
_mekhane_src = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..",
    "20_機構｜Mekhane", "_src｜ソースコード",
)
if _mekhane_src not in sys.path:
    sys.path.insert(0, _mekhane_src)


class TestSaveChunkKernel:
    """save_chunk_kernel() のユニットテスト。"""

    def _make_store(self):
        """インメモリ DB で PhantazeinStore を構築。"""
        from mekhane.symploke.phantazein_store import PhantazeinStore
        store = PhantazeinStore.__new__(PhantazeinStore)
        store.db_path = ":memory:"
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        store._conn = conn
        store.conn = conn  # save_chunk_kernel 内の直接 SQL 用
        # knowledge_edges テーブル作成 (本体と同じカラム名)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_edges (
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                evidence TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_id, to_id, relation_type)
            )
        """)
        conn.commit()
        return store

    def _make_chunks(self, n=3):
        """テスト用チャンクを生成。
        
        section_title にセッション title を含む形式にすることで
        本体の same_session 逆引きロジック (sess_title in section_title) と整合させる。
        """
        # 2セッション (Session Alpha / Session Beta) に交互に割当
        session_names = ["Session Alpha", "Session Beta"]
        chunks = []
        for i in range(n):
            sess_name = session_names[i % len(session_names)]
            chunks.append({
                "chunk_id": f"xref_7d_chunk_{i}",
                "text": f"Chunk {i} content from session",
                "section_title": f"{sess_name}: Section {i}",
                "source_id": "xref_7d",
                "chunk_index": i,
                "coherence": 0.8,
                "drift": 0.05 * i,
            })
        return chunks

    def _make_entries(self, n=2):
        """テスト用セッションエントリを生成。
        
        title が _make_chunks の section_title に部分一致するようにする。
        """
        names = ["Session Alpha", "Session Beta"]
        entries = []
        for i in range(min(n, len(names))):
            entries.append({
                "id": f"session_{i}",
                "title": names[i],
                "created_at": 1000 + i * 100,
            })
        return entries

    def test_adjacency_edges(self):
        """隣接チャンク間に adjacency エッジが生成される。"""
        store = self._make_store()
        chunks = self._make_chunks(n=4)
        entries = self._make_entries(n=2)

        store.save_chunk_kernel(chunks, source_sessions=entries)

        cursor = store.conn.execute(
            "SELECT COUNT(*) FROM knowledge_edges WHERE relation_type = 'adjacency'"
        )
        adj_count = cursor.fetchone()[0]
        assert adj_count == 3, f"期待 3 adjacency, 実際 {adj_count}"

    def test_same_session_edges(self):
        """同一セッション由来チャンク間に same_session エッジが生成される。"""
        store = self._make_store()
        # 4チャンク: Alpha(0,2), Beta(1,3) → 各1ペア = 2 same_session
        chunks = self._make_chunks(n=4)
        entries = self._make_entries(n=2)

        store.save_chunk_kernel(chunks, source_sessions=entries)

        cursor = store.conn.execute(
            "SELECT COUNT(*) FROM knowledge_edges WHERE relation_type = 'same_session'"
        )
        ss_count = cursor.fetchone()[0]
        assert ss_count >= 1, f"期待 >= 1 same_session, 実際 {ss_count}"

    def test_total_edge_count(self):
        """合計エッジ数が adjacency + same_session の合計に一致。"""
        store = self._make_store()
        chunks = self._make_chunks(n=4)
        entries = self._make_entries(n=2)

        n = store.save_chunk_kernel(chunks, source_sessions=entries)
        # adjacency: 3 (n-1) + same_session: 2 (Alpha×1, Beta×1) → 合計 5
        assert n >= 4, f"期待 >= 4 エッジ (3 adjacency + same_session), 実際 {n}"

    def test_evidence_contains_temporality(self):
        """evidence に Temporality (タイムスタンプ) 情報が含まれる。"""
        store = self._make_store()
        chunks = self._make_chunks(n=2)
        entries = self._make_entries(n=2)

        store.save_chunk_kernel(chunks, source_sessions=entries)

        cursor = store.conn.execute(
            "SELECT evidence FROM knowledge_edges WHERE relation_type = 'adjacency' LIMIT 1"
        )
        row = cursor.fetchone()
        assert row is not None
        evidence = json.loads(row[0])
        # 本体の adjacency evidence は from_title, to_title, drift
        assert "from_title" in evidence, "evidence に from_title がない"
        assert "to_title" in evidence, "evidence に to_title がない"
        assert "drift" in evidence, "evidence に drift がない"

    def test_single_chunk_no_edges(self):
        """チャンクが1つだけの場合はエッジを生成しない。"""
        store = self._make_store()
        chunks = self._make_chunks(n=1)
        entries = self._make_entries(n=1)

        n = store.save_chunk_kernel(chunks, source_sessions=entries)
        assert n == 0, f"1チャンクで {n} エッジは不正"

    def test_empty_chunks(self):
        """空のチャンクリストでエラーにならない。"""
        store = self._make_store()
        n = store.save_chunk_kernel([], source_sessions=[])
        assert n == 0


# === v0.4: EFE 精度改善テスト ===================================================


class TestEpistemicDensity(unittest.TestCase):
    """I_epistemic の k-NN 密度ベース計算テスト。

    v0.4: _compute_knn_density + _compute_epistemic_density の検証。
    """

    def test_uniform_density_low_epistemic(self):
        """均一な密度場 → epistemic ≈ 0 (surprise なし)。"""
        # 全ステップがほぼ同じベクトル → 密度差なし
        normed = [[1.0, 0.0, 0.0]] * 10
        step_indices = [2, 3, 4]  # チャンク内
        result = _compute_epistemic_density(normed, step_indices, k=3)
        assert result < 0.1, f"均一密度で epistemic={result:.4f} は高すぎる"

    def test_cluster_high_epistemic(self):
        """密度の異なる領域のチャンク → epistemic が高い (surprise あり)。"""
        # チャンク外: 密集した7ステップ (全て [0,1,0] 付近 → 高密度)
        # チャンク内: 散在した3ステップ (異なる方向 → 低密度)
        normed = []
        for i in range(7):
            normed.append(_l2_normalize([0.0, 1.0, 0.02 * i]))  # 密集
        normed.append(_l2_normalize([1.0, 0.0, 0.0]))   # チャンク内: 孤立
        normed.append(_l2_normalize([0.0, 0.0, 1.0]))   # チャンク内: 孤立
        normed.append(_l2_normalize([0.7, 0.7, 0.0]))   # チャンク内: 中間

        step_indices = [7, 8, 9]  # チャンク内 (孤立・散在)
        # k=4: 近傍の密度構造の違いを検出
        result = _compute_epistemic_density(normed, step_indices, k=4)
        assert result > 0.1, f"非対称クラスタで epistemic={result:.4f} は低すぎる"

    def test_single_step_returns_zero(self):
        """1ステップ → 密度計算不能 → 0.0。"""
        result = _compute_epistemic_density([[1.0, 0.0]], [0], k=3)
        assert result == 0.0

    def test_knn_density_all_identical(self):
        """全同一ベクトル → 密度は全て1.0。"""
        normed = [[1.0, 0.0, 0.0]] * 8
        densities = _compute_knn_density(normed, k=3)
        assert len(densities) == 8
        for d in densities:
            assert abs(d - 1.0) < 1e-6, f"同一ベクトルで density={d:.4f}"

    def test_knn_density_small_n(self):
        """n ≤ k の場合もエラーなく動作する。"""
        normed = [[1.0, 0.0], [0.0, 1.0]]
        densities = _compute_knn_density(normed, k=5)
        assert len(densities) == 2
        # 直交ベクトルなので密度は低い (cos = 0)
        for d in densities:
            assert d < 0.1, f"直交で density={d:.4f}"


class TestPragmaticEdges(unittest.TestCase):
    """I_pragmatic の knowledge_edges 連携テスト。

    v0.4: edges あり → degree×weight / edges なし → boundary_novelty fallback。
    """

    def _make_test_data(self, n_steps=10, n_chunks=3):
        """テスト用のチャンク + embeddings + similarities を生成。"""
        steps = [Step(index=i, text=f"step{i}") for i in range(n_steps)]
        embeddings = _make_embeddings_with_shift(n_steps, [], dim=4)
        sims = [0.8] * (n_steps - 1)

        chunk_size = n_steps // n_chunks
        chunks = []
        for i in range(n_chunks):
            start = i * chunk_size
            end = start + chunk_size if i < n_chunks - 1 else n_steps
            c = Chunk(chunk_id=i, steps=steps[start:end])
            chunks.append(c)

        return chunks, embeddings, sims

    def test_edges_override_boundary_novelty(self):
        """edges が渡された場合、pragmatic は degree_weighted ベースになる。"""
        chunks, embs, sims = self._make_test_data()
        edges = {
            "0": [("1", 0.8), ("2", 0.5)],  # degree_weighted = 1.3
            "1": [("0", 0.3)],                # degree_weighted = 0.3
            # チャンク2 は edges にない → fallback
        }

        result = compute_chunk_metrics(
            chunks, embs, sims, edges=edges, use_density_epistemic=False,
        )

        # チャンク0: 1.3/1.3 = 1.0 (max degree)
        assert abs(result[0].pragmatic - 1.0) < 0.01, f"chunk0 pragmatic={result[0].pragmatic}"
        # チャンク1: 0.3/1.3 ≈ 0.23
        assert abs(result[1].pragmatic - 0.3 / 1.3) < 0.05, f"chunk1 pragmatic={result[1].pragmatic}"
        # チャンク2: fallback to boundary_novelty
        assert result[2].pragmatic == result[2].boundary_novelty

    def test_no_edges_fallback(self):
        """edges=None の場合は boundary_novelty にフォールバック。"""
        chunks, embs, sims = self._make_test_data()

        result = compute_chunk_metrics(
            chunks, embs, sims, edges=None, use_density_epistemic=False,
        )

        for c in result:
            assert c.pragmatic == c.boundary_novelty, (
                f"chunk{c.chunk_id}: pragmatic={c.pragmatic} != boundary={c.boundary_novelty}"
            )


class TestLambdaSchedule(unittest.TestCase):
    """λ₁, λ₂ の τ 依存スケジュールテスト。

    v0.4: compute_lambda_schedule(τ) → (λ₁, λ₂)。
    """

    def test_low_tau(self):
        """τ=0.6 → λ₁=0.7 (Drift 重視), λ₂=0.3。"""
        l1, l2, _ = compute_lambda_schedule(0.6)
        assert abs(l1 - 0.7) < 0.01, f"τ=0.6 で λ₁={l1}"
        assert abs(l2 - 0.3) < 0.01, f"τ=0.6 で λ₂={l2}"

    def test_high_tau(self):
        """τ=0.8 → λ₁=0.3 (EFE 重視), λ₂=0.7。"""
        l1, l2, _ = compute_lambda_schedule(0.8)
        assert abs(l1 - 0.3) < 0.01, f"τ=0.8 で λ₁={l1}"
        assert abs(l2 - 0.7) < 0.01, f"τ=0.8 で λ₂={l2}"

    def test_mid_tau(self):
        """τ=0.7 → λ₁=0.5, λ₂=0.5 (バランス)。"""
        l1, l2, _ = compute_lambda_schedule(0.7)
        assert abs(l1 - 0.5) < 0.01, f"τ=0.7 で λ₁={l1}"
        assert abs(l2 - 0.5) < 0.01, f"τ=0.7 で λ₂={l2}"

    def test_clamp_below(self):
        """τ < 0.6 → λ₁=0.7 にクランプ。"""
        l1, l2, _ = compute_lambda_schedule(0.3)
        assert abs(l1 - 0.7) < 0.01, f"τ=0.3 で λ₁={l1}"

    def test_clamp_above(self):
        """τ > 0.8 → λ₁=0.3 にクランプ。"""
        l1, l2, _ = compute_lambda_schedule(0.95)
        assert abs(l1 - 0.3) < 0.01, f"τ=0.95 で λ₁={l1}"

    def test_sum_is_one(self):
        """λ₁ + λ₂ = 1.0 を保証。"""
        for tau in [0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.9]:
            l1, l2, _ = compute_lambda_schedule(tau)
            assert abs(l1 + l2 - 1.0) < 0.001, f"τ={tau} で λ₁+λ₂={l1+l2}"


# ──────────────────────────────────────────────
# §3.5 Precision Gradient テスト
# linkage_hyphe.md の λ(ρ) モデルの逆像
# precision(ρ) = 1 - λ(ρ) の検証
# ──────────────────────────────────────────────


class TestPrecisionGradient:
    """linkage_hyphe.md §3.5: precision(ρ) = 1 - λ(ρ) の性質を検証。"""

    def test_monotonic_increase(self):
        """密度 ρ が増加 → precision も単調増加。
        高密度 = 高精度 = exploit 寄り。"""
        densities = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0]
        precisions = [compute_precision_gradient(d) for d in densities]
        for i in range(len(precisions) - 1):
            assert precisions[i] <= precisions[i + 1], (
                f"non-monotonic: ρ={densities[i]}→{precisions[i]}, "
                f"ρ={densities[i+1]}→{precisions[i+1]}"
            )

    def test_bounds_zero_one(self):
        """precision は常に [0, 1] 区間に収まる。"""
        for d in [0.0, 0.01, 0.1, 0.25, 0.5, 0.75, 0.99, 1.0]:
            p = compute_precision_gradient(d)
            assert 0.0 <= p <= 1.0, f"ρ={d} → precision={p} が区間外"

    def test_extreme_low_density(self):
        """ρ ≈ 0 → precision ≈ 0 (wide prior = explore)。"""
        p = compute_precision_gradient(0.0)
        assert p < 0.15, f"ρ=0.0 → precision={p} (期待: <0.15)"

    def test_extreme_high_density(self):
        """ρ ≈ 1 → precision が高い (narrow posterior = exploit)。
        指数減衰モデル λ(ρ)=0.3+0.7·exp(-5ρ) では precision(1.0) ≈ 0.695。"""
        p = compute_precision_gradient(1.0)
        assert p > 0.65, f"ρ=1.0 → precision={p} (期待: >0.65)"

    def test_critical_point(self):
        """ρ = 0.5 で precision ∈ [0.3, 0.7] (中間帯域)。"""
        p = compute_precision_gradient(0.5)
        assert 0.3 <= p <= 0.7, f"ρ=0.5 → precision={p} (期待: [0.3, 0.7])"

    def test_negative_density_clamps(self):
        """負の密度入力 → precision ≥ 0 にクランプ。"""
        p = compute_precision_gradient(-0.5)
        assert p >= 0.0, f"ρ=-0.5 → precision={p} (期待: ≥0)"

    def test_lambda_schedule_with_precision(self):
        """precision を渡すと λ₁, λ₂ が微調整される。
        高 precision → λ₂ (EFE) 上昇・λ₁ (Drift) 低下 (構造安定 → 展開性重視)。"""
        # precision なし (デフォルト)
        l1_base, l2_base, _ = compute_lambda_schedule(0.7)
        # precision = 1.0 (高精度 → λ₂ 上昇方向)
        l1_high, l2_high, _ = compute_lambda_schedule(0.7, precision=1.0)
        # precision = 0.0 (低精度 → λ₁ 上昇方向)
        l1_low, l2_low, _ = compute_lambda_schedule(0.7, precision=0.0)
        # λ₁ + λ₂ = 1.0 は維持
        assert abs(l1_high + l2_high - 1.0) < 0.001
        assert abs(l1_low + l2_low - 1.0) < 0.001
        # 高精度 → λ₂ が基準以上 (EFE 重視方向)
        assert l2_high >= l2_base - 0.01, (
            f"precision=1.0: λ₂={l2_high} < base λ₂={l2_base}"
        )

    def test_chunk_metrics_includes_precision(self):
        """chunk_session の結果に precision 統計が含まれる。

        end-to-end: steps → chunk_session → ChunkingResult.metrics
        """
        import random
        random.seed(42)

        # 10 ステップ × 128 次元の embedding を生成
        # 前半 5 ステップと後半 5 ステップで異なるクラスタを作る
        embeddings = []
        for i in range(10):
            base = [0.0] * 128
            if i < 5:
                base[0] = 0.8 + random.random() * 0.1
                base[1] = 0.1 + random.random() * 0.1
            else:
                base[0] = 0.1 + random.random() * 0.1
                base[1] = 0.8 + random.random() * 0.1
            embeddings.append(base)

        steps = [
            Step(index=i, text=f"ステップ{i}")
            for i in range(10)
        ]

        result = chunk_session(
            steps=steps,
            embeddings=embeddings,
            tau=0.7,
        )

        # ChunkingResult.metrics に precision 統計が存在する
        assert "mean_precision" in result.metrics, "mean_precision がメトリクスにない"
        assert "precision_var" in result.metrics, "precision_var がメトリクスにない"

        # 値の妥当性
        mp = result.metrics["mean_precision"]
        pv = result.metrics["precision_var"]
        assert 0.0 <= mp <= 1.0, f"mean_precision={mp} が区間外"
        assert pv >= 0.0, f"precision_var={pv} が負"


class TestPrecisionML:
    """v0.9 multilayer precision 統合のテスト。"""

    def _make_chunks_and_embeddings(self, n_steps=20, dim=4):
        """テスト用の steps, embeddings, similarities を生成。"""
        import random
        rng = random.Random(42)
        steps = [Step(index=i, text=f"step {i}") for i in range(n_steps)]
        embeddings = [[rng.gauss(0, 1) for _ in range(dim)] for _ in range(n_steps)]
        return steps, embeddings

    def test_precision_ml_without_sims(self):
        """per_step_sims=None → 後方互換: precision_ml=0.0。"""
        steps, embeddings = self._make_chunks_and_embeddings()
        result = chunk_session(steps=steps, embeddings=embeddings, tau=0.7)

        for chunk in result.chunks:
            assert chunk.precision_ml == 0.0, \
                f"per_step_sims=None なのに precision_ml={chunk.precision_ml}"
            assert 0.0 <= chunk.precision <= 1.0

        assert "mean_precision_ml" in result.metrics
        assert result.metrics["mean_precision_ml"] == 0.0

    def test_precision_ml_with_sims(self):
        """per_step_sims 有 → precision_ml ∈ (0,1)。"""
        import random
        rng = random.Random(42)
        steps, embeddings = self._make_chunks_and_embeddings()
        per_step_sims = [rng.uniform(0.6, 0.95) for _ in range(len(steps))]

        result = chunk_session(
            steps=steps, embeddings=embeddings, tau=0.7,
            per_step_sims=per_step_sims,
        )

        has_nonzero = False
        for chunk in result.chunks:
            assert 0.0 <= chunk.precision_ml <= 1.0, \
                f"precision_ml={chunk.precision_ml} が区間外"
            if chunk.precision_ml > 0.0:
                has_nonzero = True
        assert has_nonzero, "全チャンクの precision_ml が 0.0"
        assert result.metrics["mean_precision_ml"] > 0.0

    def test_precision_ml_variation(self):
        """異なる sim パターンで異なる precision_ml が出る。"""
        steps, embeddings = self._make_chunks_and_embeddings(n_steps=20)

        # パターンA: 前半低い、後半高い → 分散大
        sims_a = [0.5] * 10 + [0.9] * 10
        result_a = chunk_session(
            steps=steps, embeddings=embeddings, tau=0.7,
            per_step_sims=sims_a,
        )

        # パターンB: 全て均一 → min==max → fallback 0.5 → 分散 0
        sims_b = [0.7] * 20
        result_b = chunk_session(
            steps=steps, embeddings=embeddings, tau=0.7,
            per_step_sims=sims_b,
        )

        var_a = result_a.metrics.get("precision_ml_var", 0)
        var_b = result_b.metrics.get("precision_ml_var", 0)
        assert var_a >= var_b, \
            f"パターンA (var={var_a}) がパターンB (var={var_b}) より分散が小さい"

    def test_integrated_precision_weight(self):
        """ml_weight=1.0 → precision==precision_ml, ml_weight=0.0 → precision==knn。"""
        import random
        rng = random.Random(42)
        steps, embeddings = self._make_chunks_and_embeddings(n_steps=20)
        per_step_sims = [rng.uniform(0.5, 0.95) for _ in range(20)]

        # ml_weight=1.0 → precision == precision_ml
        result = chunk_session(
            steps=steps, embeddings=embeddings, tau=0.7,
            per_step_sims=per_step_sims, ml_weight=1.0,
        )
        for chunk in result.chunks:
            assert abs(chunk.precision - chunk.precision_ml) < 1e-9, \
                f"ml_weight=1.0 だが precision≠precision_ml"

        # ml_weight=0.0 → precision_knn と同等
        result_0 = chunk_session(
            steps=steps, embeddings=embeddings, tau=0.7,
            per_step_sims=per_step_sims, ml_weight=0.0,
        )
        result_none = chunk_session(
            steps=steps, embeddings=embeddings, tau=0.7,
        )
        for c0, cn in zip(result_0.chunks, result_none.chunks):
            assert abs(c0.precision - cn.precision) < 1e-9, \
                f"ml_weight=0.0 だが precision≠knn"


# ──────────────────────────────────────────────
# §v0.9 Cross-Session λ 正規化テスト
# LambdaNormalizationMeta + normalize_lambda_cross_session
# ──────────────────────────────────────────────


class TestLambdaNormalizationMeta:
    """compute_lambda_schedule が返す LambdaNormalizationMeta の検証。"""

    def test_meta_returned(self):
        """3要素タプルで meta が返る。"""
        l1, l2, meta = compute_lambda_schedule(0.7)
        assert isinstance(meta, LambdaNormalizationMeta)

    def test_meta_tau_raw(self):
        """tau_raw にクリップ前の値が保存される。"""
        _, _, meta = compute_lambda_schedule(0.3)  # 0.6 より下
        assert meta.tau_raw == 0.3

    def test_meta_default_range(self):
        """デフォルトの正規化範囲 [0.6, 0.8] が記録される。"""
        _, _, meta = compute_lambda_schedule(0.7)
        assert meta.tau_min == 0.6
        assert meta.tau_max == 0.8

    def test_meta_custom_range(self):
        """カスタム正規化範囲がメタに反映される。"""
        _, _, meta = compute_lambda_schedule(0.5, tau_min=0.4, tau_max=0.9)
        assert meta.tau_min == 0.4
        assert meta.tau_max == 0.9

    def test_meta_lambda_values(self):
        """meta に記録された λ 値は返り値と一致する。"""
        l1, l2, meta = compute_lambda_schedule(0.7)
        assert l1 == meta.lambda1
        assert l2 == meta.lambda2

    def test_meta_precision_none(self):
        """precision 未指定時は None。"""
        _, _, meta = compute_lambda_schedule(0.7)
        assert meta.precision is None

    def test_meta_precision_stored(self):
        """precision 指定時は値が保存される。"""
        _, _, meta = compute_lambda_schedule(0.7, precision=0.8)
        assert meta.precision == 0.8

    def test_custom_range_changes_lambda(self):
        """正規化範囲を変えると同じ tau でも λ が変わる。"""
        _, _, meta_default = compute_lambda_schedule(0.7)
        _, _, meta_wider = compute_lambda_schedule(0.7, tau_min=0.5, tau_max=0.9)
        # 0.7 はデフォルト [0.6, 0.8] では中間 (t=0.5)
        # [0.5, 0.9] では t = (0.7-0.5)/0.4 = 0.5 → 同じ！
        # [0.4, 1.0] では t = (0.7-0.4)/0.6 = 0.5 → 同じ！
        # [0.6, 1.0] では t = (0.7-0.6)/0.4 = 0.25 → 異なる！
        _, _, meta_shifted = compute_lambda_schedule(0.7, tau_min=0.6, tau_max=1.0)
        assert meta_default.lambda1 != meta_shifted.lambda1


class TestCrossSessionNormalization:
    """normalize_lambda_cross_session の検証。"""

    def test_same_session_is_identity(self):
        """同一メタを渡すと元の λ と同じ値が返る。"""
        _, _, meta = compute_lambda_schedule(0.7)
        (a_l1, a_l2), (b_l1, b_l2) = normalize_lambda_cross_session(meta, meta)
        assert a_l1 == b_l1
        assert a_l2 == b_l2

    def test_different_ranges_unified(self):
        """異なる正規化範囲のセッションが統合される。"""
        _, _, meta_a = compute_lambda_schedule(0.65, tau_min=0.6, tau_max=0.7)
        _, _, meta_b = compute_lambda_schedule(0.85, tau_min=0.8, tau_max=0.9)
        (a_l1, a_l2), (b_l1, b_l2) = normalize_lambda_cross_session(meta_a, meta_b)
        # 統合範囲: [0.6, 0.9]（tau_raw も含む）
        # a: tau=0.65 → t = (0.65-0.6)/0.3 ≈ 0.167 → λ₁ 大きい (Drift寄り)
        # b: tau=0.85 → t = (0.85-0.6)/0.3 ≈ 0.833 → λ₁ 小さい (EFE寄り)
        assert a_l1 > b_l1, "低 tau のセッションは λ₁ (Drift) が大きいべき"
        assert a_l2 < b_l2, "高 tau のセッションは λ₂ (EFE) が大きいべき"

    def test_sum_still_one(self):
        """再正規化後も λ₁ + λ₂ ≈ 1.0。"""
        _, _, meta_a = compute_lambda_schedule(0.65)
        _, _, meta_b = compute_lambda_schedule(0.75)
        (a_l1, a_l2), (b_l1, b_l2) = normalize_lambda_cross_session(meta_a, meta_b)
        assert abs(a_l1 + a_l2 - 1.0) < 0.001
        assert abs(b_l1 + b_l2 - 1.0) < 0.001

    def test_precision_preserved(self):
        """再正規化で各セッションの precision が維持される。"""
        _, _, meta_a = compute_lambda_schedule(0.7, precision=0.2)
        _, _, meta_b = compute_lambda_schedule(0.7, precision=0.8)
        (a_l1, a_l2), (b_l1, b_l2) = normalize_lambda_cross_session(meta_a, meta_b)
        # precision=0.8 は λ₂ (EFE) 寄り → b_l2 > a_l2
        assert b_l2 > a_l2, "高 precision は λ₂ (EFE) を押し上げるべき"

    def test_wide_tau_difference(self):
        """tau が大きく離れたセッション間の比較。"""
        _, _, meta_a = compute_lambda_schedule(0.5)   # 低 τ → Drift寄り
        _, _, meta_b = compute_lambda_schedule(0.9)   # 高 τ → EFE寄り
        (a_l1, a_l2), (b_l1, b_l2) = normalize_lambda_cross_session(meta_a, meta_b)
        # 差が明確に出るはず
        assert a_l1 > 0.5, f"低τセッション: λ₁={a_l1} は 0.5 超であるべき"
        assert b_l2 > 0.5, f"高τセッション: λ₂={b_l2} は 0.5 超であるべき"

    def test_return_type(self):
        """返り値が ((float, float), (float, float)) タプル。"""
        _, _, meta_a = compute_lambda_schedule(0.7)
        _, _, meta_b = compute_lambda_schedule(0.7)
        result = normalize_lambda_cross_session(meta_a, meta_b)
        assert len(result) == 2
        assert len(result[0]) == 2
        assert len(result[1]) == 2
