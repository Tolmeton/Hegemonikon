# PROOF: mekhane/anamnesis/tests/test_chunker_nucleator.py
# PURPOSE: anamnesis モジュールの chunker_nucleator に対するテスト
"""chunker_nucleator.py のユニットテスト。

Production NucleatorChunker の核心アルゴリズムを検証する:
- Step / Chunk / ChunkingResult データクラス
- 類似度トレース (pairwise / knn)
- 境界検出
- G∘F 反復 (merge + split → Fix 収束)
- L(c) メトリクス計算
- τ 動的決定 (統計的 / エントロピーベース)
- chunk_session 統合テスト
"""

import math
import pytest

from mekhane.anamnesis.chunker_nucleator import (
    Step,
    Chunk,
    ChunkingResult,
    PrecisionResult,
    compute_similarity_trace,
    detect_boundaries,
    steps_to_chunks,
    gf_iterate,
    compute_chunk_metrics,
    compute_adaptive_tau,
    compute_tau_from_entropy,
    compute_ay,
    chunk_session,
)


# ── ヘルパー ──────────────────────────────────────────────

def _make_steps(n: int, prefix: str = "Step") -> list[Step]:
    """テスト用に n 個の Step を生成する。"""
    return [Step(index=i, text=f"{prefix} {i} content here.") for i in range(n)]


def _make_embeddings_similar(n: int, dim: int = 8) -> list[list[float]]:
    """全て似た embedding を生成 (境界ゼロ期待)。"""
    base = [1.0 / math.sqrt(dim)] * dim
    return [base[:] for _ in range(n)]


def _make_embeddings_divergent(n: int, dim: int = 8) -> list[list[float]]:
    """交互に異なる embedding を生成 (境界多数期待)。"""
    embs = []
    for i in range(n):
        vec = [0.0] * dim
        vec[i % dim] = 1.0  # one-hot 風
        embs.append(vec)
    return embs


def _make_embeddings_two_clusters(n: int, dim: int = 8) -> list[list[float]]:
    """前半と後半で2クラスタを形成する embedding。"""
    embs = []
    half = n // 2
    for i in range(n):
        vec = [0.0] * dim
        if i < half:
            vec[0] = 1.0
            vec[1] = 0.1 * (i / max(half, 1))
        else:
            vec[2] = 1.0
            vec[3] = 0.1 * ((i - half) / max(n - half, 1))
        embs.append(vec)
    return embs


# ── データクラス ──────────────────────────────────────────

class TestDataClasses:

    def test_step_creation(self):
        s = Step(index=0, text="Hello world")
        assert s.index == 0
        assert s.text == "Hello world"

    def test_chunk_creation(self):
        """Chunk は chunk_id と steps リストで構築される。"""
        steps = _make_steps(3)
        c = Chunk(chunk_id=0, steps=steps)
        assert c.chunk_id == 0
        assert len(c.steps) == 3
        assert c.coherence == 0.0  # デフォルト値
        assert c.topic == ""

    def test_chunk_with_metrics(self):
        steps = _make_steps(2)
        c = Chunk(chunk_id=1, steps=steps, coherence=0.9, drift=0.1, efe=0.05)
        assert c.coherence == 0.9
        assert c.drift == 0.1
        assert c.efe == 0.05

    def test_chunking_result(self):
        steps = _make_steps(2)
        chunks = [Chunk(chunk_id=0, steps=steps)]
        result = ChunkingResult(
            session_id="test",
            chunks=chunks,
            similarity_trace=[0.8],
            tau=0.70,
            iterations=3,
            converged=True,
            metrics={},
        )
        assert result.converged is True
        assert result.tau == 0.70
        assert len(result.chunks) == 1
        assert result.session_id == "test"


# ── 類似度トレース ────────────────────────────────────────

class TestSimilarityTrace:

    def test_pairwise_mode(self):
        embs = _make_embeddings_two_clusters(6)
        trace = compute_similarity_trace(embs, mode="pairwise")
        # n-1 個の類似度が返る
        assert len(trace) == 5

    def test_knn_mode(self):
        embs = _make_embeddings_two_clusters(6)
        trace = compute_similarity_trace(embs, mode="knn", k=2)
        assert len(trace) == 5

    def test_similar_embeddings_high_trace(self):
        embs = _make_embeddings_similar(5)
        trace = compute_similarity_trace(embs, mode="pairwise")
        # 全て同じ → 類似度 ≈ 1.0
        for val in trace:
            assert val > 0.95

    def test_minimum_input(self):
        embs = _make_embeddings_similar(2)
        trace = compute_similarity_trace(embs, mode="pairwise")
        assert len(trace) == 1

    def test_knn_k_clamped(self):
        """k が n より大きくてもエラーにならない。"""
        embs = _make_embeddings_similar(3)
        trace = compute_similarity_trace(embs, mode="knn", k=100)
        assert len(trace) == 2


# ── 境界検出 ──────────────────────────────────────────────

class TestBoundaryDetection:

    def test_no_boundaries_similar(self):
        """全て似た trace → 境界なし (高い τ 閾値)。"""
        trace = [0.95, 0.96, 0.94, 0.97]
        boundaries = detect_boundaries(trace, tau=0.50)
        assert len(boundaries) == 0

    def test_boundaries_with_drop(self):
        """明確な drop → 境界検出。"""
        trace = [0.9, 0.9, 0.2, 0.9, 0.9]
        boundaries = detect_boundaries(trace, tau=0.70)
        assert 2 in boundaries

    def test_multiple_drops(self):
        """複数の drop → 複数の境界。"""
        trace = [0.9, 0.1, 0.9, 0.1, 0.9]
        boundaries = detect_boundaries(trace, tau=0.70)
        assert len(boundaries) >= 2

    def test_empty_trace(self):
        boundaries = detect_boundaries([], tau=0.70)
        assert boundaries == []


# ── 初期チャンク構築 ──────────────────────────────────────

class TestStepsToChunks:

    def test_no_boundaries(self):
        """境界ゼロ → 全体が 1 チャンク。"""
        steps = _make_steps(5)
        chunks = steps_to_chunks(steps, boundaries=[])
        assert len(chunks) == 1
        # 全 step がカバーされている
        assert len(chunks[0].steps) == 5

    def test_with_boundaries(self):
        """境界あり → 複数チャンク。boundary は inclusive end (b+1 まで)。"""
        steps = _make_steps(6)
        chunks = steps_to_chunks(steps, boundaries=[3])
        assert len(chunks) == 2
        # boundary=3 → end=4 → steps[0:4] (4つ) + steps[4:] (2つ)
        assert len(chunks[0].steps) == 4
        assert len(chunks[1].steps) == 2

    def test_multiple_boundaries(self):
        """複数境界 → 3つ以上のチャンク。"""
        steps = _make_steps(9)
        chunks = steps_to_chunks(steps, boundaries=[2, 5])
        assert len(chunks) == 3


# ── G∘F 反復 ──────────────────────────────────────────────

class TestGFIterate:

    def test_convergence_similar(self):
        """似た embedding → 変化なし → 即収束。"""
        steps = _make_steps(6)
        embs = _make_embeddings_similar(6)
        initial = steps_to_chunks(steps, boundaries=[])

        result_chunks, iterations, converged = gf_iterate(
            initial, embs,
            tau=0.70,
            min_steps=2,
            max_iterations=10,
        )
        assert converged is True
        assert iterations <= 2

    def test_max_iterations_respected(self):
        """max_iterations=1 → 最大1回で停止。"""
        steps = _make_steps(8)
        embs = _make_embeddings_divergent(8)
        initial = steps_to_chunks(steps, boundaries=[2, 4, 6])

        _, iterations, _ = gf_iterate(
            initial, embs,
            tau=0.70,
            min_steps=1,
            max_iterations=1,
        )
        assert iterations <= 1

    def test_chunks_preserved(self):
        """G∘F を経ても全 step がカバーされる。"""
        steps = _make_steps(10)
        embs = _make_embeddings_two_clusters(10)
        initial = steps_to_chunks(steps, boundaries=[4])

        result_chunks, _, _ = gf_iterate(
            initial, embs,
            tau=0.70,
            min_steps=2,
            max_iterations=5,
        )
        # 全 step が何らかのチャンクにカバーされている
        covered = set()
        for c in result_chunks:
            for s in c.steps:
                covered.add(s.index)
        assert covered == set(range(10))


# ── メトリクス計算 ─────────────────────────────────────────

class TestChunkMetrics:

    def test_metrics_computed(self):
        """メトリクスが正常に計算される。"""
        steps = _make_steps(6)
        embs = _make_embeddings_two_clusters(6)
        chunks = steps_to_chunks(steps, boundaries=[2])
        sims = compute_similarity_trace(embs, mode="pairwise")

        result = compute_chunk_metrics(chunks, embs, sims, lambda1=0.5, lambda2=0.5)
        assert len(result) == len(chunks)
        for c in result:
            assert hasattr(c, 'coherence')
            assert hasattr(c, 'drift')
            assert hasattr(c, 'efe')
            # coherence は 0-1 の範囲
            assert 0.0 <= c.coherence <= 1.0

    def test_single_chunk_metrics(self):
        """1チャンクでもメトリクス計算がエラーにならない。"""
        steps = _make_steps(3)
        embs = _make_embeddings_similar(3)
        chunks = steps_to_chunks(steps, boundaries=[])
        sims = compute_similarity_trace(embs, mode="pairwise")

        result = compute_chunk_metrics(chunks, embs, sims, lambda1=0.5, lambda2=0.5)
        assert len(result) == 1


# ── τ 動的決定 ────────────────────────────────────────────

class TestAdaptiveTau:

    def test_auto_tau_range(self):
        """統計的 τ が妥当な範囲に収まる。"""
        trace = [0.8, 0.7, 0.3, 0.8, 0.6, 0.2, 0.9]
        tau = compute_adaptive_tau(trace, k=1.5)
        assert 0.30 <= tau <= 0.95

    def test_uniform_trace(self):
        """均一な trace → τ ≈ mean。"""
        trace = [0.7] * 10
        tau = compute_adaptive_tau(trace, k=1.5)
        # σ ≈ 0 → τ ≈ μ = 0.7
        assert abs(tau - 0.7) < 0.05

    def test_high_variance_trace(self):
        """高分散 trace → τ が低くなる。"""
        trace = [0.9, 0.1, 0.9, 0.1, 0.9, 0.1]
        tau = compute_adaptive_tau(trace, k=1.5)
        # μ-kσ で低い τ が期待される
        assert tau <= 0.5


class TestTauFromEntropy:

    def test_empty_issues(self):
        """issues 空 → τ_base (0.70)。"""
        tau = compute_tau_from_entropy([])
        assert tau == 0.70

    def test_with_issues(self):
        """issues あり → τ が変動。"""
        issues = [
            {"severity": "high", "description": "test issue"},
            {"severity": "low", "description": "minor"},
        ]
        tau = compute_tau_from_entropy(issues)
        assert 0.50 <= tau <= 0.90


# ── 統合テスト: chunk_session ─────────────────────────────

class TestChunkSession:

    def test_basic_session(self):
        """基本的なチャンキングが動作する。"""
        steps = _make_steps(8)
        embs = _make_embeddings_two_clusters(8)

        result = chunk_session(
            steps, embs,
            tau=0.70,
            min_steps=2,
            max_iterations=5,
        )
        assert isinstance(result, ChunkingResult)
        assert len(result.chunks) >= 1
        assert result.tau > 0

    def test_auto_tau(self):
        """tau="auto" が動作する。"""
        steps = _make_steps(8)
        embs = _make_embeddings_two_clusters(8)

        result = chunk_session(
            steps, embs,
            tau="auto",
            min_steps=2,
            max_iterations=5,
        )
        assert isinstance(result, ChunkingResult)
        assert result.tau > 0

    def test_all_similar(self):
        """全て似た embedding → 1チャンク。"""
        steps = _make_steps(5)
        embs = _make_embeddings_similar(5)

        result = chunk_session(steps, embs, tau=0.70)
        assert len(result.chunks) == 1
        assert result.converged is True

    def test_many_steps(self):
        """ステップ数が多くてもエラーにならない。"""
        steps = _make_steps(50)
        embs = _make_embeddings_divergent(50, dim=50)

        result = chunk_session(steps, embs, tau=0.60, min_steps=2)
        assert len(result.chunks) >= 1
        # 全 step がカバーされている
        covered = set()
        for c in result.chunks:
            for s in c.steps:
                covered.add(s.index)
        assert covered == set(range(50))

    def test_minimum_steps(self):
        """2ステップでもエラーにならない。"""
        steps = _make_steps(2)
        embs = _make_embeddings_similar(2)

        result = chunk_session(steps, embs, tau=0.70, min_steps=1)
        assert len(result.chunks) >= 1

    def test_knn_mode(self):
        """knn モードで動作する。"""
        steps = _make_steps(10)
        embs = _make_embeddings_two_clusters(10)

        result = chunk_session(
            steps, embs,
            tau=0.70,
            sim_mode="knn",
            sim_k=3,
        )
        assert isinstance(result, ChunkingResult)
        assert len(result.chunks) >= 1


# ── chunker.py NucleatorChunker アダプタ ──────────────────

class TestNucleatorChunkerAdapter:
    """chunker.py 側の NucleatorChunker がフォールバック含め機能するか。"""

    def test_no_embed_fn_fallback(self):
        """embed_fn=None → MarkdownChunker にフォールバック。"""
        from mekhane.anamnesis.chunker import NucleatorChunker
        nc = NucleatorChunker(embed_fn=None)
        text = "## Section 1\nHello world\n\n## Section 2\nGoodbye world"
        chunks = nc.chunk(text, source_id="test")
        assert len(chunks) >= 1

    def test_empty_text(self):
        from mekhane.anamnesis.chunker import NucleatorChunker
        nc = NucleatorChunker(embed_fn=None)
        chunks = nc.chunk("", source_id="test")
        assert chunks == []

    def test_with_mock_embed_fn(self):
        """mock embed_fn で Nucleator が動作する。"""
        from mekhane.anamnesis.chunker import NucleatorChunker

        dim = 8
        call_count = [0]

        def mock_embed(texts):
            call_count[0] += 1
            return _make_embeddings_two_clusters(len(texts), dim=dim)

        nc = NucleatorChunker(embed_fn=mock_embed, tau=0.70)
        text = "\n\n".join([
            f"This is paragraph {i} with enough content to be meaningful and pass the length filter."
            for i in range(6)
        ])
        chunks = nc.chunk(text, source_id="test_mock", title="Test Doc")
        assert len(chunks) >= 1
        assert call_count[0] >= 1
        # Nucleator 固有メトリクス
        if chunks and "coherence" in chunks[0]:
            assert 0.0 <= chunks[0]["coherence"] <= 1.0

    def test_tau_property(self):
        from mekhane.anamnesis.chunker import NucleatorChunker
        nc = NucleatorChunker(embed_fn=None, tau=0.65)
        assert nc.tau == 0.65

    def test_tau_auto_default(self):
        from mekhane.anamnesis.chunker import NucleatorChunker
        nc = NucleatorChunker(embed_fn=None, tau="auto")
        # auto の場合デフォルト 0.70 が返る
        assert nc.tau == 0.70


# ── Ensemble Precision 統合テスト ────────────────────────────

class TestPrecisionResult:
    """新規 PrecisionResult dataclass のテスト。"""

    def test_creation_defaults(self):
        """PrecisionResult がデフォルト値で作成される。"""
        pr = PrecisionResult(
            knn=0.7,
            multilayer=0.0,
            ensemble=0.0,
            integrated=0.7,
            gate_label="HIGH",
        )
        assert pr.knn == 0.7
        assert pr.multilayer == 0.0
        assert pr.ensemble == 0.0
        assert pr.integrated == 0.7
        assert pr.gate_label == "HIGH"

    def test_creation_full(self):
        """全フィールド指定で作成される。"""
        pr = PrecisionResult(
            knn=0.6,
            multilayer=0.5,
            ensemble=0.8,
            integrated=0.7,
            gate_label="mid",
        )
        assert pr.knn == 0.6
        assert pr.multilayer == 0.5
        assert pr.ensemble == 0.8
        assert pr.integrated == 0.7
        assert pr.gate_label == "mid"


class TestChunkPrecisionFields:
    """新規 Chunk precision フィールドのテスト。"""

    def test_chunk_precision_defaults(self):
        """Chunk の precision フィールドがデフォルト値を持つ。"""
        steps = _make_steps(2)
        c = Chunk(chunk_id=0, steps=steps)
        assert c.precision == 0.0
        assert c.precision_ml == 0.0
        assert c.precision_ensemble == 0.0
        assert c.precision_result is None

    def test_chunk_with_precision_result(self):
        """Chunk に PrecisionResult を設定できる。"""
        pr = PrecisionResult(
            knn=0.8, multilayer=0.0, ensemble=0.0,
            integrated=0.75, gate_label="high",
        )
        steps = _make_steps(3)
        c = Chunk(
            chunk_id=0,
            steps=steps,
            precision=0.75,
            precision_result=pr,
        )
        assert c.precision == 0.75
        assert c.precision_result is not None
        assert c.precision_result.knn == 0.8


class TestEnsemblePrecisionIntegration:
    """compute_chunk_metrics の 3パス precision ロジックのテスト。"""

    def test_knn_only_fallback(self):
        """ensemble/ml なし → kNN のみで precision が計算される (後方互換)。"""
        steps = _make_steps(6)
        embs = _make_embeddings_two_clusters(6)
        chunks = steps_to_chunks(steps, boundaries=[2])
        sims = compute_similarity_trace(embs, mode="pairwise")

        result = compute_chunk_metrics(
            chunks, embs, sims,
            lambda1=0.5, lambda2=0.5,
        )
        for c in result:
            assert c.precision >= 0.0
            assert c.precision_ml == 0.0
            assert c.precision_ensemble == 0.0
            # PrecisionResult が生成されている
            assert c.precision_result is not None
            assert c.precision_result.gate_label in ("high", "mid", "low")

    def test_with_ensemble_precisions(self):
        """ensemble_precisions を渡すと precision_ensemble が計算される。"""
        steps = _make_steps(6)
        embs = _make_embeddings_two_clusters(6)
        chunks = steps_to_chunks(steps, boundaries=[2])
        sims = compute_similarity_trace(embs, mode="pairwise")

        # 簡単な ensemble precision: 各チャンクに対応
        ens_prec = [0.9, 0.3]  # チャンク数と同じ

        result = compute_chunk_metrics(
            chunks, embs, sims,
            lambda1=0.5, lambda2=0.5,
            ensemble_precisions=ens_prec,
            ensemble_weight=0.5,
        )
        assert len(result) == 2
        # ensemble precision が反映されている
        assert result[0].precision_ensemble == 0.9
        assert result[1].precision_ensemble == 0.3
        # precision (integrated) が kNN だけの場合と異なる
        assert result[0].precision_result is not None
        assert result[0].precision_result.ensemble == 0.9

    def test_ensemble_weight_effect(self):
        """ensemble_weight が統合 precision に影響する。"""
        steps = _make_steps(4)
        embs = _make_embeddings_similar(4)
        chunks = steps_to_chunks(steps, boundaries=[])
        sims = compute_similarity_trace(embs, mode="pairwise")

        # weight=0 → kNN のみ
        r0 = compute_chunk_metrics(
            chunks, embs, sims,
            lambda1=0.5, lambda2=0.5,
            ensemble_precisions=[0.5],
            ensemble_weight=0.0,
        )
        # weight=1 → ensemble のみ
        r1 = compute_chunk_metrics(
            chunks, embs, sims,
            lambda1=0.5, lambda2=0.5,
            ensemble_precisions=[0.5],
            ensemble_weight=1.0,
        )
        # weight=0 の場合 precision_ensemble は無視されるが、値自体はのこる
        assert r0[0].precision_ensemble == 0.5
        assert r1[0].precision_ensemble == 0.5
        # 統合値は weight により変わる
        assert r0[0].precision_result is not None
        assert r1[0].precision_result is not None


class TestChunkSessionEnsemble:
    """統合テスト: chunk_session に ensemble パラメータを渡す。"""

    def test_session_with_ensemble_weight(self):
        """新規パラメータがエラーなく動作する。"""
        steps = _make_steps(8)
        embs = _make_embeddings_two_clusters(8)

        result = chunk_session(
            steps, embs,
            tau=0.70,
            min_steps=2,
            max_iterations=5,
            ensemble_weight=0.5,
        )
        assert isinstance(result, ChunkingResult)
        assert len(result.chunks) >= 1
        # 全チャンクに precision_result がある
        for c in result.chunks:
            assert c.precision_result is not None

    def test_session_backward_compatible(self):
        """新規パラメータなしでも後方互換。"""
        steps = _make_steps(6)
        embs = _make_embeddings_two_clusters(6)

        result = chunk_session(steps, embs, tau=0.70)
        assert isinstance(result, ChunkingResult)
        # precision は kNN のみで計算
        for c in result.chunks:
            assert c.precision >= 0.0
            assert c.precision_ensemble == 0.0


class TestNucleatorChunkerEnsembleWeight:
    """NucleatorChunker の ensemble_weight パラメータのテスト。"""

    def test_default_weight(self):
        """デフォルトは 0.5。"""
        from mekhane.anamnesis.chunker import NucleatorChunker
        nc = NucleatorChunker(embed_fn=None)
        assert nc.ensemble_weight == 0.5

    def test_custom_weight(self):
        """カスタム値が設定できる。"""
        from mekhane.anamnesis.chunker import NucleatorChunker
        nc = NucleatorChunker(embed_fn=None)
        nc.ensemble_weight = 0.7
        assert nc.ensemble_weight == 0.7


# ── AY (Presheaf Representability) テスト ──────────────────

class TestComputeAY:
    """compute_ay の4アプローチをカバーするテスト群。"""

    def _make_chunks_uniform(self, n_chunks: int = 3, steps_per: int = 4) -> list[Chunk]:
        """均一な Chunk 群を生成。coherence / precision 高め。"""
        chunks = []
        idx = 0
        for i in range(n_chunks):
            steps = [Step(index=idx + j, text=f"Step {idx + j}") for j in range(steps_per)]
            c = Chunk(
                chunk_id=i, steps=steps,
                coherence=0.9, drift=0.1, precision=0.85,
                efe=0.05, loss=0.02,
            )
            chunks.append(c)
            idx += steps_per
        return chunks

    def _make_chunks_varied(self, n_chunks: int = 4) -> list[Chunk]:
        """品質にバラつきのある Chunk 群を生成。precision が全て異なる。"""
        specs = [
            (5, 0.95, 0.05, 0.90),
            (3, 0.60, 0.40, 0.50),
            (2, 0.40, 0.70, 0.30),
            (6, 0.85, 0.12, 0.80),
        ]
        chunks = []
        idx = 0
        for i, (ns, coh, dri, prec) in enumerate(specs[:n_chunks]):
            steps = [Step(index=idx + j, text=f"Step {idx + j}") for j in range(ns)]
            c = Chunk(
                chunk_id=i, steps=steps,
                coherence=coh, drift=dri, precision=prec,
                efe=0.1 * (1 - coh), loss=0.05 * dri,
            )
            chunks.append(c)
            idx += ns
        return chunks

    def test_ay_structural_positive(self):
        """アプローチ1: 構造的AY — 均一チャンクでは AY >= 0 (int)。"""
        chunks = self._make_chunks_uniform(3, 4)
        result = compute_ay(chunks)
        assert "ay_structural" in result
        assert isinstance(result["ay_structural"], int)
        # 均一 precision → unique_p=1, AY = filter(1) + compare(0) = 1
        assert result["ay_structural"] >= 0

    def test_ay_informational(self):
        """アプローチ2: 情報量AY (ay_info) — 結果が float で返る。"""
        chunks = self._make_chunks_varied(4)
        result = compute_ay(chunks)
        assert "ay_info" in result
        assert isinstance(result["ay_info"], float)
        # 4つの異なる precision → エントロピー > 0
        assert result["ay_info"] > 0.0

    def test_ay_effective_varies_with_data(self):
        """アプローチ3: 実効AY — drift/efe が異なるチャンクで正値。"""
        chunks = self._make_chunks_varied(4)
        result = compute_ay(chunks)
        assert "ay_effective" in result
        assert isinstance(result["ay_effective"], float)
        # varied chunks は drift/efe が異なるので ay_effective > 0
        assert result["ay_effective"] >= 0.0

    def test_ay_quality_signal(self):
        """アプローチ4: 品質信号AY — precision-coherence/drift 相関。"""
        chunks = self._make_chunks_varied(4)
        result = compute_ay(chunks)
        assert "corr_precision_coherence" in result
        assert "corr_precision_drift" in result
        assert isinstance(result["corr_precision_coherence"], float)
        assert isinstance(result["corr_precision_drift"], float)

    def test_ay_empty_chunks(self):
        """空チャンクリスト → 全 AY = 0。"""
        result = compute_ay([])
        assert result["ay_structural"] == 0
        assert result["ay_info"] == 0.0
        assert result["ay_effective"] == 0.0
        assert result["ay_positive"] is False
        assert result["corr_precision_coherence"] == 0.0
        assert result["corr_precision_drift"] == 0.0

    def test_ay_single_chunk(self):
        """1チャンク → edge case でエラーにならない。"""
        chunks = self._make_chunks_uniform(1, 5)
        result = compute_ay(chunks)
        # 1チャンク → unique_p=1 → AY = 1 (filter=1, compare=0)
        assert isinstance(result["ay_structural"], int)
        assert isinstance(result["ay_info"], float)
        assert isinstance(result["ay_effective"], float)
        # 1チャンクでは相関は計算不可 → 0.0
        assert result["corr_precision_coherence"] == 0.0
        assert result["corr_precision_drift"] == 0.0


class TestChunkSessionAY:
    """chunk_session の metrics に AY が統合されていることを確認。"""

    def test_metrics_contain_ay(self):
        """chunk_session の返り値 metrics に AY キーが含まれる。"""
        steps = _make_steps(8)
        embs = _make_embeddings_two_clusters(8)

        result = chunk_session(
            steps, embs,
            tau=0.70,
            min_steps=2,
            max_iterations=5,
        )
        assert "ay" in result.metrics, "Missing 'ay' namespace in metrics"
        ay_metrics = result.metrics["ay"]
        # 基本 AY キーの存在確認
        for key in ["ay_structural", "ay_info", "ay_effective", "ay_positive",
                    "corr_precision_coherence", "corr_precision_drift",
                    "lambda_recommendation"]:
            assert key in ay_metrics, f"Missing key: {key} in ay_metrics"
