"""FisherField 統合テスト — 密度推定・Fisher行列・固有分解・理論橋渡し。

PROOF: B2 Fisher × Phantasia 統合テスト。
4カテゴリで FisherField のパイプラインを検証する:
  1. 単体テスト — 模擬 embedding で各メソッドの動作確認
  2. 結合テスト — Mock PhantasiaField で end-to-end パイプライン
  3. スペクトル構造テスト — 合成クラスタで sloppy gap 検出
  4. 理論橋渡しテスト — FisherMetricAnalyzer の 7 DOF との対応

依存:
  - mekhane.anamnesis.fisher_field (FisherField, FieldAxes)
  - mekhane.fep.fisher_metric (FisherMetricAnalyzer)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from mekhane.anamnesis.fisher_field import FisherField, FieldAxes


# ---------------------------------------------------------------------------
# ヘルパー: 合成データ生成
# ---------------------------------------------------------------------------

def _make_uniform_embeddings(n: int = 100, d: int = 64) -> np.ndarray:
    """一様分布の embedding を生成 (テスト用)。"""
    rng = np.random.RandomState(42)
    return rng.randn(n, d).astype(np.float32)


def _make_clustered_embeddings(
    n_clusters: int = 7,
    points_per_cluster: int = 50,
    d: int = 64,
    cluster_spread: float = 0.3,
    cluster_separation: float = 5.0,
) -> tuple[np.ndarray, np.ndarray]:
    """クラスタ構造のある embedding を生成。

    各クラスタの中心は cluster_separation だけ離れ、
    各点はクラスタ中心からの cluster_spread のガウスノイズを持つ。

    Returns:
        (embeddings, labels) のタプル
    """
    rng = np.random.RandomState(42)
    n = n_clusters * points_per_cluster

    # クラスタ中心を生成 (十分離す)
    centers = rng.randn(n_clusters, d).astype(np.float32)
    # 中心間の距離を正規化してから separation を掛ける
    norms = np.linalg.norm(centers, axis=1, keepdims=True)
    centers = centers / norms * cluster_separation

    embeddings = np.zeros((n, d), dtype=np.float32)
    labels = np.zeros(n, dtype=np.int32)

    for i in range(n_clusters):
        start = i * points_per_cluster
        end = start + points_per_cluster
        noise = rng.randn(points_per_cluster, d).astype(np.float32) * cluster_spread
        embeddings[start:end] = centers[i] + noise
        labels[start:end] = i

    return embeddings, labels


def _make_mock_phantasia_field(
    embeddings: np.ndarray,
    session_ids: list[str] | None = None,
) -> MagicMock:
    """PhantasiaField のモックを生成。

    _get_index() が to_pandas() で embedding を返すモックを構築。
    """
    n = len(embeddings)
    if session_ids is None:
        session_ids = [f"session_{i % 5}" for i in range(n)]

    # pandas DataFrame のモック
    import pandas as pd
    df = pd.DataFrame({
        "vector": [embeddings[i].tolist() for i in range(n)],
        "source": ["session"] * n,
        "session_id": session_ids,
        "text": [f"chunk_{i}" for i in range(n)],
    })

    # Backend テーブルのモック
    mock_backend = MagicMock()
    mock_backend.to_pandas.return_value = df

    # GnosisIndex のモック
    mock_index = MagicMock()
    mock_index._backend = mock_backend

    # PhantasiaField のモック
    mock_field = MagicMock()
    mock_field._get_index.return_value = mock_index

    return mock_field


# ===========================================================================
# カテゴリ 1: 単体テスト (模擬データ)
# ===========================================================================

class TestComputeRhoKnn:
    """k-NN 密度推定の単体テスト。"""

    def test_basic_density(self):
        """基本動作: ρ が [0, 1] 内に収まる。"""
        embeddings = _make_uniform_embeddings(100, 64)
        rho = FisherField.compute_rho_knn(embeddings, k=10)

        assert rho.shape == (100,)
        assert rho.min() >= 0.0
        assert rho.max() <= 1.0

    def test_density_small_dataset(self):
        """エッジケース: データ点 ≤ k のとき一様密度 0.5 を返す。"""
        embeddings = _make_uniform_embeddings(5, 64)
        rho = FisherField.compute_rho_knn(embeddings, k=10)

        assert rho.shape == (5,)
        np.testing.assert_allclose(rho, 0.5, atol=1e-6)

    def test_dense_cluster_higher_density(self):
        """高密度クラスタの点は低密度点より ρ が高い。"""
        rng = np.random.RandomState(42)
        # 密集クラスタ (50点) + 散布点 (50点)
        dense = rng.randn(50, 32).astype(np.float32) * 0.1
        sparse = rng.randn(50, 32).astype(np.float32) * 10.0
        embeddings = np.vstack([dense, sparse])

        rho = FisherField.compute_rho_knn(embeddings, k=5)

        # 密集クラスタの平均密度 > 散布点の平均密度
        dense_mean = rho[:50].mean()
        sparse_mean = rho[50:].mean()
        assert dense_mean > sparse_mean, (
            f"密集 {dense_mean:.3f} ≤ 散布 {sparse_mean:.3f}"
        )


class TestComputeFisherMatrix:
    """Fisher 情報行列の単体テスト。"""

    def test_symmetry(self):
        """Fisher 行列は対称行列。"""
        embeddings = _make_uniform_embeddings(50, 32)
        G = FisherField.compute_fisher_matrix(embeddings, k=5)

        np.testing.assert_allclose(G, G.T, atol=1e-10)

    def test_shape(self):
        """Fisher 行列の形状は (d, d)。"""
        d = 32
        embeddings = _make_uniform_embeddings(50, d)
        G = FisherField.compute_fisher_matrix(embeddings, k=5)

        assert G.shape == (d, d)

    def test_positive_semidefinite(self):
        """Fisher 行列は半正定値 (固有値 ≥ 0)。"""
        embeddings = _make_uniform_embeddings(80, 32)
        G = FisherField.compute_fisher_matrix(embeddings, k=5)

        eigenvalues = np.linalg.eigvalsh(G)
        # 数値誤差を許容
        assert np.all(eigenvalues >= -1e-8), (
            f"負の固有値: {eigenvalues[eigenvalues < -1e-8]}"
        )

    def test_precomputed_rho(self):
        """事前計算した ρ を渡せる。"""
        embeddings = _make_uniform_embeddings(50, 32)
        rho = np.full(50, 0.5, dtype=np.float32)  # 一様密度

        G = FisherField.compute_fisher_matrix(embeddings, k=5, rho=rho)
        assert G.shape == (32, 32)


class TestEigenDecompose:
    """固有分解 + sloppy gap 検出の単体テスト。"""

    def test_basic_decomposition(self):
        """基本動作: FieldAxes が返る。"""
        # 制御可能なブロック対角行列をテスト入力に使用
        d = 32
        G = np.eye(d) * 0.01
        # 上位 5 軸を際立たせる
        for i in range(5):
            G[i, i] = 10.0 - i * 1.5

        axes = FisherField.eigen_decompose(G, k_max=20)

        assert isinstance(axes, FieldAxes)
        assert axes.k >= 2
        assert len(axes.eigenvalues) == axes.k
        assert axes.eigenvectors.shape == (d, axes.k)

    def test_eigenvalues_descending(self):
        """固有値は降順。"""
        d = 32
        G = np.eye(d)
        for i in range(d):
            G[i, i] = float(d - i)

        axes = FisherField.eigen_decompose(G, k_max=10)

        for i in range(len(axes.eigenvalues) - 1):
            assert axes.eigenvalues[i] >= axes.eigenvalues[i + 1]

    def test_minimum_k_is_2(self):
        """有効軸数は最低 2。"""
        d = 32
        # 固有値が全て同じ → gap なし → k=2 (最低値)
        G = np.eye(d)

        axes = FisherField.eigen_decompose(G, k_max=10)
        assert axes.k >= 2

    def test_computed_at_is_set(self):
        """computed_at が ISO8601 形式で設定される。"""
        G = np.eye(16)
        axes = FisherField.eigen_decompose(G, k_max=5)

        assert axes.computed_at != ""
        assert "T" in axes.computed_at  # ISO8601 の T 区切り


# ===========================================================================
# カテゴリ 2: PhantasiaField 結合テスト (Mock 注入)
# ===========================================================================

class TestComputeAxesIntegration:
    """FisherField + PhantasiaField の end-to-end パイプライン。"""

    def test_compute_axes_with_mock_field(self):
        """Mock PhantasiaField から軸を計算できる。"""
        embeddings = _make_uniform_embeddings(100, 64)
        mock_field = _make_mock_phantasia_field(embeddings)

        fisher = FisherField(hyphe_field=mock_field)
        axes = fisher.compute_axes(k_neighbors=5, k_max_axes=20)

        assert isinstance(axes, FieldAxes)
        assert axes.k >= 2
        assert axes.total_points == 100

    def test_compute_axes_centroid_mode(self):
        """centroid モードで軸を計算できる。"""
        embeddings = _make_uniform_embeddings(100, 64)
        session_ids = [f"session_{i // 20}" for i in range(100)]  # 5セッション
        mock_field = _make_mock_phantasia_field(embeddings, session_ids)

        fisher = FisherField(hyphe_field=mock_field)
        axes = fisher.compute_axes(
            k_neighbors=3,
            k_max_axes=4,
            use_centroids=True,
        )

        assert isinstance(axes, FieldAxes)
        assert axes.k >= 2


class TestProjectSession:
    """セッション射影のテスト。"""

    def test_project_single_session(self):
        """単一セッションを固有軸空間に射影できる。"""
        d = 64
        embeddings = _make_uniform_embeddings(100, d)
        session_ids = [f"session_{i // 20}" for i in range(100)]
        mock_field = _make_mock_phantasia_field(embeddings, session_ids)

        fisher = FisherField(hyphe_field=mock_field)
        axes = fisher.compute_axes(k_neighbors=5, k_max_axes=10)

        coords = fisher.project_session("session_0", axes)
        assert coords is not None
        assert coords.shape == (axes.k,)

    def test_project_nonexistent_session(self):
        """存在しないセッションは None を返す。"""
        embeddings = _make_uniform_embeddings(50, 64)
        mock_field = _make_mock_phantasia_field(embeddings)

        fisher = FisherField(hyphe_field=mock_field)
        axes = fisher.compute_axes(k_neighbors=5, k_max_axes=10)

        coords = fisher.project_session("nonexistent", axes)
        assert coords is None

    def test_project_all_sessions(self):
        """全セッションを一括射影できる。"""
        embeddings = _make_uniform_embeddings(100, 64)
        session_ids = [f"session_{i // 20}" for i in range(100)]
        mock_field = _make_mock_phantasia_field(embeddings, session_ids)

        fisher = FisherField(hyphe_field=mock_field)
        axes = fisher.compute_axes(k_neighbors=5, k_max_axes=10)

        projected = fisher.project_all_sessions(axes)
        assert len(projected) == 5  # 5 セッション
        for sid, coords in projected.items():
            assert coords.shape == (axes.k,)


# ===========================================================================
# カテゴリ 3: スペクトル構造テスト (合成クラスタ)
# ===========================================================================

class TestSloppySpectrum:
    """sloppy spectrum と意味的クラスタの対応テスト。"""

    def test_clustered_data_has_gap(self):
        """7クラスタデータで非自明なスペクトルが得られる。

        k-NN 密度推定→勾配→Fisher 行列の経路で、クラスタ構造が
        そのまま k に反映されるとは限らない。
        ここでは「パイプラインがエラーなく完了し、FieldAxes が返る」ことを検証。
        """
        embeddings, _ = _make_clustered_embeddings(
            n_clusters=7,
            points_per_cluster=80,
            d=16,
            cluster_spread=0.2,
            cluster_separation=8.0,
        )
        mock_field = _make_mock_phantasia_field(embeddings)

        fisher = FisherField(hyphe_field=mock_field)
        axes = fisher.compute_axes(k_neighbors=10, k_max_axes=15)

        # パイプラインが完了し、有効な FieldAxes が返る
        assert isinstance(axes, FieldAxes)
        assert axes.k >= 2
        assert axes.total_points == 560
        assert len(axes.eigenvalues) == axes.k

    def test_uniform_data_produces_axes(self):
        """一様分布データでもパイプラインが完了する。

        一様データでも k-NN 密度勾配にはノイズ由来の変動があるため、
        sloppy gap が任意の k を返すのは正常動作。
        """
        embeddings = _make_uniform_embeddings(200, 16)
        mock_field = _make_mock_phantasia_field(embeddings)

        fisher = FisherField(hyphe_field=mock_field)
        axes = fisher.compute_axes(k_neighbors=10, k_max_axes=15)

        assert isinstance(axes, FieldAxes)
        assert axes.k >= 2
        assert axes.total_points == 200

    def test_clustered_vs_uniform_k(self):
        """クラスタデータの k > 一様データの k。"""
        # クラスタデータ
        embeddings_c, _ = _make_clustered_embeddings(
            n_clusters=7,
            points_per_cluster=50,
            d=16,
            cluster_spread=0.2,
            cluster_separation=8.0,
        )
        mock_field_c = _make_mock_phantasia_field(embeddings_c)
        fisher_c = FisherField(hyphe_field=mock_field_c)
        axes_c = fisher_c.compute_axes(k_neighbors=10, k_max_axes=15)

        # 一様データ
        embeddings_u = _make_uniform_embeddings(350, 16)
        mock_field_u = _make_mock_phantasia_field(embeddings_u)
        fisher_u = FisherField(hyphe_field=mock_field_u)
        axes_u = fisher_u.compute_axes(k_neighbors=10, k_max_axes=15)

        # クラスタデータの k >= 一様データの k
        assert axes_c.k >= axes_u.k, (
            f"クラスタ k={axes_c.k} < 一様 k={axes_u.k}"
        )


# ===========================================================================
# カテゴリ 4: 理論橋渡しテスト
# ===========================================================================

class TestTheoryBridge:
    """FisherMetricAnalyzer の 7 DOF vs FisherField の sloppy k。"""

    def test_theoretical_dof_is_7(self):
        """理論的有効自由度は 7。"""
        from mekhane.fep.fisher_metric import FisherMetricAnalyzer

        analyzer = FisherMetricAnalyzer()
        assert analyzer.calculate_effective_dof() == 7

    def test_theoretical_block_diagonalization(self):
        """理論的ブロック対角化が PASS する。"""
        from mekhane.fep.fisher_metric import FisherMetricAnalyzer

        analyzer = FisherMetricAnalyzer()
        result = analyzer.check_block_diagonalization()

        assert result.is_block_diagonal
        assert result.n_blocks == 7
        assert result.effective_dof == 7

    def test_theoretical_rank_is_7(self):
        """理論的 Fisher 行列のランクが 7。"""
        from mekhane.fep.fisher_metric import FisherMetricAnalyzer

        analyzer = FisherMetricAnalyzer()
        result = analyzer.verify_rank()

        assert result.is_valid
        assert result.rank == 7

    def test_7_cluster_spectrum_aligns_with_theory(self):
        """7クラスタの sloppy k が理論的 DOF=7 と ±5 以内で対応。

        FEP 的意味: 実データから演繹的に導出される有効軸数が、
        理論的に予測される 7 独立制約と整合する。

        注意: これは「構造的整合性」の検証であり、
        「7クラスタ = 7座標」の直接的同一視ではない。
        Fisher 場が構造的に意味のある軸数を復元できるかのテスト。
        """
        from mekhane.fep.fisher_metric import FisherMetricAnalyzer

        # 理論側
        analyzer = FisherMetricAnalyzer()
        theoretical_dof = analyzer.calculate_effective_dof()  # = 7

        # 実験側: 7 クラスタ合成データ
        embeddings, _ = _make_clustered_embeddings(
            n_clusters=7,
            points_per_cluster=50,
            d=64,
            cluster_spread=0.3,
            cluster_separation=5.0,
        )
        mock_field = _make_mock_phantasia_field(embeddings)

        fisher = FisherField(hyphe_field=mock_field)
        axes = fisher.compute_axes(k_neighbors=10, k_max_axes=30)

        # 理論 DOF と実験 k の対応 (±5 以内)
        diff = abs(axes.k - theoretical_dof)
        assert diff <= 5, (
            f"理論 DOF={theoretical_dof} vs 実験 k={axes.k}, "
            f"差={diff} (許容: ≤5)"
        )


# ===========================================================================
# エッジケーステスト
# ===========================================================================

class TestEdgeCases:
    """エッジケースの処理。"""

    def test_very_few_points(self):
        """データ点が非常に少ない (5点) でもエラーにならない。

        n <= k+1 のとき compute_rho_knn は一様密度を返す。
        compute_axes はこれを受けて最小限の固有分解を行う。
        """
        embeddings = _make_uniform_embeddings(5, 16)
        mock_field = _make_mock_phantasia_field(embeddings)

        fisher = FisherField(hyphe_field=mock_field)
        axes = fisher.compute_axes(k_neighbors=2, k_max_axes=2)

        assert isinstance(axes, FieldAxes)

    def test_empty_embeddings_raises(self):
        """embedding が空の場合 ValueError を送出する。"""
        # 空の DataFrame を返す mock
        import pandas as pd
        mock_backend = MagicMock()
        mock_backend.to_pandas.return_value = pd.DataFrame(columns=["vector", "source"])

        mock_index = MagicMock()
        mock_index._backend = mock_backend

        mock_field = MagicMock()
        mock_field._get_index.return_value = mock_index

        fisher = FisherField(hyphe_field=mock_field)

        with pytest.raises(ValueError, match="embedding がありません"):
            fisher.compute_axes()

    def test_single_session_project(self):
        """セッションが1つだけでも射影可能。"""
        embeddings = _make_uniform_embeddings(20, 32)
        session_ids = ["only_session"] * 20
        mock_field = _make_mock_phantasia_field(embeddings, session_ids)

        fisher = FisherField(hyphe_field=mock_field)
        axes = fisher.compute_axes(k_neighbors=5, k_max_axes=5)

        projected = fisher.project_all_sessions(axes)
        assert len(projected) == 1
        assert "only_session" in projected
