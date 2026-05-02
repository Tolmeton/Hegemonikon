# PROOF: [L2/FEP] <- mekhane/fep/tests/test_fisher_metric.py
# PURPOSE: Fisher ブロック対角化の検証テスト
"""
Tests for Fisher Metric Block Diagonalization.

Level A Step 2 の検証: POMDP 十分統計量から構成される
Fisher 情報行列が 7 つの独立ブロックに分解されること。
"""

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def analyzer():
    """FisherMetricAnalyzer インスタンスを生成。"""
    from mekhane.fep.fisher_metric import FisherMetricAnalyzer
    return FisherMetricAnalyzer()


@pytest.fixture
def fisher_matrix(analyzer):
    """デフォルトのブロック対角 Fisher 行列。"""
    return analyzer.build_fisher_matrix()


# ---------------------------------------------------------------------------
# Block Structure Tests
# ---------------------------------------------------------------------------

class TestBlockStructure:
    """ブロック構造の構成テスト。"""

    def test_has_seven_blocks(self, analyzer):
        """全 7 ブロック (6 修飾座標 + 1 Flow) が存在する。"""
        assert len(analyzer.all_blocks) == 7

    def test_has_six_parameter_blocks(self, analyzer):
        """6 つの修飾座標ブロックが存在する。"""
        assert len(analyzer.parameter_blocks) == 6

    def test_has_flow_block(self, analyzer):
        """Flow ブロックが存在する。"""
        assert analyzer.flow_block is not None
        assert analyzer.flow_block.name == "Block_Flow"

    def test_all_coordinates_covered(self, analyzer):
        """全 6 修飾座標がブロックとしてカバーされている。"""
        coords = {b.coordinate for b in analyzer.parameter_blocks}
        expected = {"Value", "Function", "Precision", "Scale", "Valence", "Temporality"}
        assert coords == expected

    def test_each_block_has_gamma_and_q(self, analyzer):
        """各ブロックに Γ と Q の演算子がペアで存在する。"""
        for block in analyzer.parameter_blocks:
            assert block.gamma_op.is_gradient, (
                f"{block.name}: gamma_op should be gradient"
            )
            assert block.q_op.is_solenoidal, (
                f"{block.name}: q_op should be solenoidal"
            )

    def test_gamma_q_same_coordinate(self, analyzer):
        """各ブロック内の Γ と Q が同じ座標に属する。"""
        for block in analyzer.parameter_blocks:
            assert block.gamma_op.coordinate == block.q_op.coordinate, (
                f"{block.name}: Γ={block.gamma_op.coordinate} vs Q={block.q_op.coordinate}"
            )


# ---------------------------------------------------------------------------
# Internal Adjunction Tests (Γ⊣Q → 1 DOF)
# ---------------------------------------------------------------------------

class TestInternalAdjunction:
    """各ブロック内の随伴性テスト: Γ⊣Q → 有効自由度 1。"""

    def test_each_block_dof_is_one(self, analyzer):
        """各ブロックの有効自由度が 1 である。"""
        for block in analyzer.all_blocks:
            assert block.effective_dof == 1, (
                f"{block.name}: expected DOF=1, got {block.effective_dof}"
            )


# ---------------------------------------------------------------------------
# Block Independence Tests (非対角項 = 0)
# ---------------------------------------------------------------------------

class TestBlockIndependence:
    """ブロック間の独立性テスト: Fisher 行列の非対角ブロックが 0。"""

    def test_off_diagonal_blocks_are_zero(self, fisher_matrix):
        """異なるブロック間の Fisher 情報 (交差項) が 0 である。

        Smithe Theorem 46:
        テンソル積モデルでは VFE が加法分解 →
        ∂²F/∂θ_i∂θ_j = 0 for i≠j where θ_i ∈ Block_i, θ_j ∈ Block_j
        """
        n_blocks = 7
        for i in range(n_blocks):
            for j in range(n_blocks):
                if i == j:
                    continue
                # ブロック i と ブロック j の交差領域
                row_start, row_end = i * 2, (i + 1) * 2
                col_start, col_end = j * 2, (j + 1) * 2
                cross_block = fisher_matrix[row_start:row_end, col_start:col_end]
                assert np.allclose(cross_block, 0.0), (
                    f"Block ({i},{j}) cross-term is not zero: {cross_block}"
                )


# ---------------------------------------------------------------------------
# Degrees of Freedom Tests (rank = 7)
# ---------------------------------------------------------------------------

class TestDegreesOfFreedom:
    """有効自由度テスト: rank(J) == 7。"""

    def test_effective_dof_is_seven(self, analyzer):
        """構造的な有効自由度の合計が 7 である。"""
        assert analyzer.calculate_effective_dof() == 7

    def test_fisher_matrix_rank_is_seven(self, analyzer):
        """Fisher 行列の数値的ランクが 7 である。

        14×14 行列 (7 ブロック × 2 成分) だが、
        各ブロック内の Γ⊣Q 随伴により 2→1 に縮約。
        実効ランク = 7。
        """
        result = analyzer.verify_rank()
        assert result.is_valid, (
            f"Expected rank 7, got {result.rank}. "
            f"Singular values: {result.singular_values}"
        )
        assert result.rank == 7
        assert result.expected_rank == 7

    def test_seven_large_singular_values(self, analyzer):
        """7 つの大きな特異値と 7 つのほぼ 0 の特異値が存在する。"""
        result = analyzer.verify_rank()
        assert result.n_large == 7, (
            f"Expected 7 large SVs, got {result.n_large}"
        )
        assert result.n_small == 7, (
            f"Expected 7 small SVs, got {result.n_small}"
        )

    def test_rank_with_varied_block_values(self, analyzer):
        """ブロックごとに異なる Fisher 情報量でもランクは 7。"""
        J = analyzer.build_fisher_matrix(block_values={
            "Value": 3.0,
            "Function": 1.5,
            "Precision": 2.0,
            "Scale": 0.8,
            "Valence": 4.0,
            "Temporality": 1.2,
            "Flow": 2.5,
        })
        result = analyzer.verify_rank(J)
        assert result.is_valid, (
            f"Rank should be 7 regardless of block values, got {result.rank}"
        )


# ---------------------------------------------------------------------------
# Block Diagonalization Verification
# ---------------------------------------------------------------------------

class TestBlockDiagonalization:
    """ブロック対角化の総合検証テスト。"""

    def test_check_passes(self, analyzer):
        """構造的検証が全項目 PASS する。"""
        result = analyzer.check_block_diagonalization()
        assert result.is_block_diagonal, (
            f"Block diagonalization check failed: {result.issues}"
        )
        assert result.n_blocks == 7
        assert result.effective_dof == 7
        assert result.issues == []

    def test_summary_contains_pass(self, analyzer):
        """サマリに PASS が含まれる。"""
        summary = analyzer.summary()
        assert "✅ PASS" in summary
        assert "❌ FAIL" not in summary


# ---------------------------------------------------------------------------
# POMDP Statistic Mapping Tests
# ---------------------------------------------------------------------------

class TestPOMDPMapping:
    """POMDP 統計量と HGK 座標の対応テスト。"""

    def test_all_six_statistics_mapped(self):
        """6 つの POMDP 統計量が全てマッピングされている。"""
        from mekhane.fep.fisher_metric import (
            POMDPStatistic,
            STATISTIC_COORDINATE_MAP,
        )
        assert len(STATISTIC_COORDINATE_MAP) == 6
        for stat in POMDPStatistic:
            assert stat in STATISTIC_COORDINATE_MAP, (
                f"Missing mapping for {stat}"
            )

    def test_mapping_is_bijective(self):
        """マッピングが全単射 (bijection) である。"""
        from mekhane.fep.fisher_metric import STATISTIC_COORDINATE_MAP
        coords = list(STATISTIC_COORDINATE_MAP.values())
        assert len(coords) == len(set(coords)), "Mapping is not injective"


# ---------------------------------------------------------------------------
# Step 2b-i: Product Decomposition Proof Tests
# ---------------------------------------------------------------------------

@pytest.fixture
def decomposition():
    """ProductDecompositionProof インスタンスを生成。"""
    from mekhane.fep.fisher_metric import ProductDecompositionProof
    return ProductDecompositionProof()


class TestProductDecomposition:
    """POMDP 直積分解の構造的証明テスト (Level A Step 2b-i)。

    検証対象: 6 つの POMDP 十分統計量が独立に推論可能であること
    (= 状態空間が直積分解される) を支持する証拠線の構造。
    """

    def test_has_six_evidence_lines(self, decomposition):
        """6 座標に対応する 6 つの証拠線が存在する。

        各修飾座標 (Value, Function, Precision, Scale, Valence, Temporality)
        の独立性を個別に裏付ける証拠が必要。
        """
        assert decomposition.n_total == 6

    def test_five_proven_one_computational(self, decomposition):
        """5 つが proven、1 つが computational。

        Valence (v = -dF/dt) の完全な独立性は
        交差項 Σ_i (∂F/∂θ_i)(dθ_i/dt) のため不完全。
        これを正直に'computational'と申告していることを検証。
        """
        result = decomposition.verify()
        assert result.n_proven == 5, f"Expected 5 proven, got {result.n_proven}"
        assert result.n_computational == 1, (
            f"Expected 1 computational, got {result.n_computational}"
        )
        assert result.n_conjectured == 0, (
            f"Expected 0 conjectured, got {result.n_conjectured}"
        )

    def test_overall_status_is_structurally_supported(self, decomposition):
        """総合判定が 'structurally_supported' (5/6 proven) である。

        'proven' (6/6 全て証明済み) ではないことを自覚的に示す。
        過大な主張を避ける N-3 (確信度を明示せよ) の実践。
        """
        result = decomposition.verify()
        assert result.overall_status == "structurally_supported"

    def test_valence_is_the_gap(self, decomposition):
        """唯一のギャップが Valence の独立性である。

        Valence = -dF/dt は VFE の時間微分であり、
        dF/dt = Σ_i (∂F/∂θ_i)(dθ_i/dt) と展開されるため
        他パラメータの変化率に構造的に依存する可能性がある。
        """
        result = decomposition.verify()
        assert len(result.gaps) == 1
        assert "Valence" in result.gaps[0]

    def test_each_evidence_has_source(self, decomposition):
        """全証拠線が学術的引用元 (arXiv ID 等) を持つ。

        N-9 (原典に当たれ) + N-10 (SOURCE/TAINT) の実践:
        証拠は traceable でなければならない。
        """
        for e in decomposition.evidence:
            assert len(e.source) > 0, f"{e.name}: source is empty"
            # arXiv ID, 論文著者名, 年号のいずれかを含むべき
            has_ref = any(
                marker in e.source
                for marker in ["arXiv", "2019", "2020", "2023", "2008", "2013", "2017"]
            )
            assert has_ref, f"{e.name}: source '{e.source}' lacks academic reference"

    def test_each_evidence_has_claim_and_detail(self, decomposition):
        """各証拠線に claim (主張) と detail (詳細) が記載されている。

        N-11 (読み手が行動できる形で出せ): 抽象1 + 具体3 の原則。
        claim が抽象、detail が具体。
        """
        for e in decomposition.evidence:
            assert len(e.claim) > 20, f"{e.name}: claim too short ({len(e.claim)} chars)"
            assert len(e.detail) > 30, f"{e.name}: detail too short ({len(e.detail)} chars)"

    def test_evidence_covers_all_coordinate_aspects(self, decomposition):
        """証拠線が 6 座標の独立性の根拠を網羅している。

        必要な根拠:
        - Value/Function/Precision: VFE の変分構造 (Friston 2019)
        - Scale: 階層的 Markov 性 (Friston 2008)
        - Valence: VFE 変化率 (Seth 2013)
        - Temporality: 一般化座標 (Friston 2017)
        """
        names = {e.name for e in decomposition.evidence}
        expected_keywords = [
            "VFE",           # Value/Function/Precision の根拠
            "Tensor",        # Smithe のテンソル積定理
            "Independent",   # Da Costa の独立推論
            "Hierarchical",  # Scale の階層性
            "Valence",       # Valence の変化率
            "Temporal",      # Temporality の一般化座標
        ]
        for kw in expected_keywords:
            found = any(kw in name for name in names)
            assert found, f"No evidence line covers '{kw}'"

    def test_summary_is_valid_markdown(self, decomposition):
        """サマリが有効な Markdown テーブルを含む。"""
        summary = decomposition.summary()
        assert "# Step 2b-i" in summary
        assert "| #" in summary  # テーブルヘッダ
        assert "✅" in summary   # proven マーカー
        assert "🟡" in summary   # computational マーカー
        assert "### 残存ギャップ" in summary  # ギャップセクション

    def test_has_gaps_property(self, decomposition):
        """has_gaps が True を返す (Valence ギャップが存在するため)。"""
        assert decomposition.has_gaps is True
        assert len(decomposition.gaps) == 1
        assert decomposition.gaps[0].status == "computational"

    def test_gaps_detail_mentions_cross_terms(self, decomposition):
        """ギャップの detail に交差項の問題が記載されている。

        Valence の独立性が不完全な理由 (dF/dt の交差項) が
        正直に記述されていることを検証。
        """
        gap = decomposition.gaps[0]
        assert "交差項" in gap.detail or "dF/dt" in gap.detail, (
            f"Gap detail should mention cross-terms: {gap.detail}"
        )


# ---------------------------------------------------------------------------
# Integration: __init__.py 経由のインポートテスト
# ---------------------------------------------------------------------------

class TestPublicAPI:
    """__init__.py 経由で公開 API が利用可能であることを検証。"""

    def test_fisher_analyzer_importable(self):
        """FisherMetricAnalyzer が mekhane.fep から直接インポート可能。"""
        from mekhane.fep import FisherMetricAnalyzer
        analyzer = FisherMetricAnalyzer()
        assert analyzer.calculate_effective_dof() == 7

    def test_product_decomposition_importable(self):
        """ProductDecompositionProof が mekhane.fep.fisher_metric からインポート可能。"""
        from mekhane.fep.fisher_metric import ProductDecompositionProof
        proof = ProductDecompositionProof()
        result = proof.verify()
        assert result.overall_status == "structurally_supported"

    def test_result_types_importable(self):
        """結果型が fisher_metric からインポート可能。"""
        from mekhane.fep.fisher_metric import (
            BlockDiagonalizationResult,
            RankVerificationResult,
            ProductDecompositionResult,
            DecompositionEvidence,
        )
        # 型がインポートできること自体が検証
        assert BlockDiagonalizationResult is not None
        assert RankVerificationResult is not None
        assert ProductDecompositionResult is not None
        assert DecompositionEvidence is not None
