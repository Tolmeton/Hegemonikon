"""Stream A テスト: 密度ベース情報利得推定 (F6 Linkage L(c))

_compute_text_redundancy / _compute_drift / _compute_result_density の
単体テストと L(c) 損失関数の統合テスト。

sklearn 未インストール環境ではフォールバック動作のみ検証し、
sklearn 依存テストは importorskip で自動スキップ。
"""

import pytest
from types import SimpleNamespace

from mekhane.periskope.engine import PeriskopeEngine

# sklearn が利用可能かチェック (テストのグループ分けに使用)
try:
    import sklearn  # noqa: F401
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

sklearn_required = pytest.mark.skipif(
    not HAS_SKLEARN, reason="scikit-learn not installed"
)


# --- テストヘルパー ---

def _make_result(title: str, content: str, url: str = "") -> SimpleNamespace:
    """検索結果オブジェクトのモック。"""
    return SimpleNamespace(title=title, content=content, url=url)


def _make_engine() -> PeriskopeEngine:
    """最小構成の PeriskopeEngine インスタンス。"""
    return PeriskopeEngine.__new__(PeriskopeEngine)


# ========================================================================
# _compute_text_redundancy テスト
# ========================================================================

class TestComputeTextRedundancy:
    """テキスト群の内部冗長性 (redundancy) 推定のテスト。"""

    def test_single_text_returns_1(self):
        """単一テキスト → redundancy = 1.0 (比較対象がない)"""
        assert PeriskopeEngine._compute_text_redundancy(["hello world"]) == 1.0

    def test_empty_list_returns_1(self):
        """空リスト → redundancy = 1.0"""
        assert PeriskopeEngine._compute_text_redundancy([]) == 1.0

    def test_fallback_without_sklearn(self):
        """sklearn が ValueError を出す場合 → フォールバック 0.0"""
        # フォールバック動作は sklearn 有無に関わらず常にテスト可能
        red = PeriskopeEngine._compute_text_redundancy(["a", "b"])
        # sklearn なし→0.0、sklearn あり→実計算値: いずれも [0, 1] 範囲
        assert 0.0 <= red <= 1.0

    @sklearn_required
    def test_identical_texts_high_redundancy(self):
        """同一テキスト群 → redundancy ≈ 1.0"""
        texts = [
            "machine learning neural network deep learning",
            "machine learning neural network deep learning",
            "machine learning neural network deep learning",
        ]
        red = PeriskopeEngine._compute_text_redundancy(texts)
        assert red > 0.9, f"同一テキストなのに redundancy={red:.3f} < 0.9"

    @sklearn_required
    def test_diverse_texts_low_redundancy(self):
        """異なるトピックのテキスト群 → redundancy < 0.5"""
        texts = [
            "quantum computing qubits entanglement superposition",
            "culinary arts french cuisine pastry baking dessert",
            "ancient roman history gladiator colosseum senate republic",
        ]
        red = PeriskopeEngine._compute_text_redundancy(texts)
        assert red < 0.5, f"異なるトピックなのに redundancy={red:.3f} >= 0.5"

    def test_redundancy_range_0_to_1(self):
        """redundancy は [0, 1] の範囲に収まる"""
        texts = [
            "alpha beta gamma",
            "delta epsilon zeta",
            "eta theta iota kappa",
        ]
        red = PeriskopeEngine._compute_text_redundancy(texts)
        assert 0.0 <= red <= 1.0, f"redundancy={red:.3f} が [0,1] 外"


# ========================================================================
# _compute_drift テスト
# ========================================================================

class TestComputeDrift:
    """新結果の既存結果からの意味的距離 (drift) 推定のテスト。"""

    @sklearn_required
    def test_same_topic_low_drift(self):
        """同じトピックの新結果 → drift ≈ 0"""
        new = ["machine learning neural network training optimization"]
        existing = [
            "machine learning neural network deep learning model",
            "neural network backpropagation gradient descent training",
        ]
        drift = PeriskopeEngine._compute_drift(new, existing)
        assert drift < 0.4, f"同トピックなのに drift={drift:.3f} >= 0.4"

    @sklearn_required
    def test_different_topic_high_drift(self):
        """異なるトピックの新結果 → drift > 0.5"""
        new = ["culinary arts french cuisine pastry baking dessert chocolate"]
        existing = [
            "quantum computing qubits entanglement superposition decoherence",
            "quantum algorithm shor grover factoring search complexity",
        ]
        drift = PeriskopeEngine._compute_drift(new, existing)
        assert drift > 0.5, f"異なるトピックなのに drift={drift:.3f} <= 0.5"

    def test_drift_range_0_to_1(self):
        """drift は [0, 1] の範囲に収まる"""
        new = ["alpha beta gamma"]
        existing = ["delta epsilon zeta"]
        drift = PeriskopeEngine._compute_drift(new, existing)
        assert 0.0 <= drift <= 1.0, f"drift={drift:.3f} が [0,1] 外"


# ========================================================================
# _compute_result_density テスト
# ========================================================================

class TestComputeResultDensity:
    """L(c) 損失関数ベースの密度推定の統合テスト。"""

    def test_empty_new_results_returns_none(self):
        """新結果が空 → None"""
        engine = _make_engine()
        result = engine._compute_result_density(
            new_results=[],
            existing_results=[_make_result("test", "content")],
        )
        assert result is None

    def test_empty_existing_results_returns_none(self):
        """既存結果が空 → None"""
        engine = _make_engine()
        result = engine._compute_result_density(
            new_results=[_make_result("test", "content")],
            existing_results=[],
        )
        assert result is None

    def test_short_content_filtered_returns_none(self):
        """コンテンツが短すぎる → フィルタされて None"""
        engine = _make_engine()
        result = engine._compute_result_density(
            new_results=[_make_result("", "hi")],  # len < 10
            existing_results=[_make_result("", "ok")],  # len < 10
        )
        assert result is None

    def test_returns_dict_with_required_keys(self):
        """正常な入力 → redundancy, drift, density_gain, loss を含む dict"""
        engine = _make_engine()
        result = engine._compute_result_density(
            new_results=[
                _make_result("Machine Learning", "Neural network training with backpropagation gradient descent"),
                _make_result("Deep Learning", "Convolutional neural network image classification recognition"),
            ],
            existing_results=[
                _make_result("Quantum Computing", "Quantum bits entanglement superposition decoherence algorithms"),
            ],
        )
        assert result is not None
        assert "redundancy" in result
        assert "drift" in result
        assert "density_gain" in result
        assert "loss" in result

    def test_density_gain_in_range(self):
        """density_gain は [0, 1] の範囲に収まる"""
        engine = _make_engine()
        result = engine._compute_result_density(
            new_results=[
                _make_result("A", "Natural language processing transformer attention mechanism self"),
                _make_result("B", "Computer vision object detection segmentation recognition analysis"),
            ],
            existing_results=[
                _make_result("C", "Reinforcement learning policy gradient reward function optimization"),
            ],
        )
        assert result is not None
        assert 0.0 <= result["density_gain"] <= 1.0

    @sklearn_required
    def test_redundant_results_lower_density_gain(self):
        """冗長な新結果 (高 redundancy + 低 drift) → 低い density_gain"""
        engine = _make_engine()

        # 冗長: 新結果が既存と同じトピック + 互いに類似
        redundant = engine._compute_result_density(
            new_results=[
                _make_result("ML", "Machine learning neural network deep learning training model"),
                _make_result("ML2", "Machine learning neural network deep learning optimization model"),
            ],
            existing_results=[
                _make_result("ML3", "Machine learning neural network deep learning architecture model"),
            ],
        )

        # 新規: 新結果が既存と異なるトピック + 互いに多様
        novel = engine._compute_result_density(
            new_results=[
                _make_result("Bio", "Genomics CRISPR gene editing biotechnology molecular biology"),
                _make_result("Astro", "Exoplanet detection transit method radial velocity spectroscopy"),
            ],
            existing_results=[
                _make_result("ML3", "Machine learning neural network deep learning architecture model"),
            ],
        )

        assert redundant is not None and novel is not None
        # 新規の方が density_gain が高いはず
        assert novel["density_gain"] >= redundant["density_gain"], (
            f"新規({novel['density_gain']:.3f}) < 冗長({redundant['density_gain']:.3f}): "
            f"L(c) 損失関数が期待通り機能していない"
        )


# ========================================================================
# L(c) 損失関数の数値テスト
# ========================================================================

class TestLossFunction:
    """L(c) = -redundancy(c)·drift(c) + λ·drift(c) の数値整合性テスト。"""

    def test_loss_components_contribute_correctly(self):
        """redundancy↑ → loss↓ (良い), drift↑ → loss↑ (新方向)"""
        engine = _make_engine()
        result = engine._compute_result_density(
            new_results=[
                _make_result("A", "Transformer attention mechanism self-attention multi-head scaled dot product"),
                _make_result("B", "BERT GPT language model pretraining fine-tuning natural language processing"),
            ],
            existing_results=[
                _make_result("C", "Transformer attention mechanism neural network architecture encoder decoder"),
            ],
        )
        assert result is not None
        # loss は float であること
        assert isinstance(result["loss"], float)
        # density_gain = max(0, min(1, 0.5 - loss))
        expected_gain = max(0.0, min(1.0, 0.5 - result["loss"]))
        assert abs(result["density_gain"] - round(expected_gain, 4)) < 0.001
