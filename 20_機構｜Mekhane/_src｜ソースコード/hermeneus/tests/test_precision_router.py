"""precision_router (Anchor Cosine Similarity v3) テスト。"""

import json
import math
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hermeneus.src.precision_router import (
    EXPLOIT_THRESHOLD,
    EXPLORE_THRESHOLD,
    ExecutionStrategy,
    PrecisionResult,
    _cosine_similarity,
    _load_anchors,
    compute_context_precision,
    route_execution,
)


# ============================================================
# ExecutionStrategy の基本テスト
# ============================================================

class TestExecutionStrategy:
    """ExecutionStrategy dataclass のテスト。"""

    def test_creation(self):
        """正常な生成を確認。"""
        s = ExecutionStrategy(
            depth_level=2,
            search_budget=1,
            gnosis_search=True,
            precision_ml=0.05,
            confidence_threshold=0.65,
            reasoning="balanced (diff=0.0500)",
        )
        assert s.depth_level == 2
        assert s.precision_ml == 0.05

    def test_frozen(self):
        """frozen=True で変更不可を確認。"""
        s = ExecutionStrategy(
            depth_level=1,
            search_budget=0,
            gnosis_search=False,
            precision_ml=0.1,
            confidence_threshold=0.8,
            reasoning="exploit",
        )
        with pytest.raises(AttributeError):
            s.depth_level = 3  # type: ignore


# ============================================================
# route_execution の戦略判定テスト
# ============================================================

class TestRouteExecution:
    """route_execution() の判定ロジックテスト。"""

    def test_high_diff_exploit(self):
        """diff ≥ 0.02 → exploit。"""
        s = route_execution(0.10, ccl_depth=2)
        assert s.depth_level == 2
        assert s.search_budget == 0
        assert s.gnosis_search is False
        assert "exploit" in s.reasoning

    def test_negative_diff_explore(self):
        """diff < -0.02 → explore。"""
        s = route_execution(-0.10, ccl_depth=2)
        assert s.depth_level == 2
        assert s.search_budget == 3
        assert s.gnosis_search is True
        assert "explore" in s.reasoning

    def test_near_zero_balanced(self):
        """-0.02 ≤ diff < 0.02 → balanced。"""
        s = route_execution(0.0, ccl_depth=2)
        assert s.depth_level == 2
        assert s.search_budget == 1
        assert "balanced" in s.reasoning

    def test_ccl_plus_preserves_depth(self):
        """CCL + (depth=3) は exploit でも L3 を維持。"""
        s = route_execution(0.15, ccl_depth=3)
        assert s.depth_level == 3  # max(3, 1) = 3

    def test_ccl_minus_with_explore(self):
        """CCL - (depth=1) でも explore なら L2 に引き上げ。"""
        s = route_execution(-0.10, ccl_depth=1)
        assert s.depth_level == 2  # max(1, 2) = 2

    def test_exploit_at_boundary(self):
        """ちょうど exploit_threshold の場合。"""
        s = route_execution(EXPLOIT_THRESHOLD, ccl_depth=2)
        assert "exploit" in s.reasoning

    def test_explore_below_boundary(self):
        """explore_threshold ぎりぎり下。"""
        s = route_execution(EXPLORE_THRESHOLD - 0.001, ccl_depth=2)
        assert "explore" in s.reasoning

    def test_custom_thresholds(self):
        """カスタム閾値が機能するか。"""
        s = route_execution(
            0.05, ccl_depth=2,
            exploit_threshold=0.10,
            explore_threshold=-0.10,
        )
        assert "balanced" in s.reasoning


# ============================================================
# _cosine_similarity の単体テスト
# ============================================================

class TestCosineSimilarity:
    """_cosine_similarity のテスト。"""

    def test_identical_vectors(self):
        """同一ベクトルの cos sim は 1.0。"""
        v = [1.0, 2.0, 3.0, 4.0]
        assert abs(_cosine_similarity(v, v) - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        """直交ベクトルの cos sim は 0.0。"""
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        assert abs(_cosine_similarity(a, b) - 0.0) < 1e-6

    def test_opposite_vectors(self):
        """反対ベクトルの cos sim は -1.0。"""
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert abs(_cosine_similarity(a, b) - (-1.0)) < 1e-6

    def test_zero_vector(self):
        """ゼロベクトルの cos sim は 0.0。"""
        a = [0.0, 0.0, 0.0]
        b = [1.0, 2.0, 3.0]
        assert _cosine_similarity(a, b) == 0.0

    def test_different_lengths(self):
        """異なる長さのベクトルは短い方に合わせる。"""
        a = [1.0, 2.0, 3.0]
        b = [1.0, 2.0]
        result = _cosine_similarity(a, b)
        # 先頭2要素のみで計算
        expected_dot = 1.0 + 4.0
        expected_na = math.sqrt(1.0 + 4.0)
        expected_nb = math.sqrt(1.0 + 4.0)
        assert abs(result - expected_dot / (expected_na * expected_nb)) < 1e-6


# ============================================================
# dispatch 統合テスト
# ============================================================

class TestDispatchPrecisionIntegration:
    """dispatch() との統合テスト。"""

    def test_dispatch_without_context(self):
        """context なしの dispatch は precision routing をスキップ。"""
        from hermeneus.src.dispatch import dispatch
        result = dispatch("/noe+")
        assert result is not None

    def test_dispatch_with_short_context(self):
        """短い context は API を呼ばず中立を返す。"""
        result = compute_context_precision("短い")
        assert isinstance(result, PrecisionResult)
        assert result.diff == 0.0

    def test_dispatch_with_context_no_api_key(self):
        """API Key なし環境でエラーなく中立を返す。"""
        import hermeneus.src.precision_router as pr
        # singleton リセット
        old_client = pr._embed_client
        old_attempted = pr._embed_client_attempted
        pr._embed_client = None
        pr._embed_client_attempted = False
        try:
            with patch.dict("os.environ", {}, clear=True):
                result = compute_context_precision("テスト" * 50)
            assert isinstance(result, PrecisionResult)
            assert result.diff == 0.0
        finally:
            pr._embed_client = old_client
            pr._embed_client_attempted = old_attempted

    def test_dispatch_context_parameter_backward_compatible(self):
        """dispatch の context パラメータは後方互換。"""
        from hermeneus.src.dispatch import dispatch
        result = dispatch("/noe+", context="テスト" * 50)
        assert result is not None

    def test_dispatch_signature_accepts_context(self):
        """dispatch() が context キーワード引数を受け付ける。"""
        import inspect
        from hermeneus.src.dispatch import dispatch
        sig = inspect.signature(dispatch)
        assert "context" in sig.parameters


# ============================================================
# compute_context_precision のモックテスト
# ============================================================

class TestComputeContextPrecision:
    """compute_context_precision() のテスト。"""

    def test_short_text_returns_neutral(self):
        """短いテキストは中立 PrecisionResult を返す。"""
        result = compute_context_precision("短い")
        assert isinstance(result, PrecisionResult)
        assert result.diff == 0.0

    def test_no_api_key_returns_neutral(self):
        """API Key なしで 0.0 を返す。"""
        import hermeneus.src.precision_router as pr
        old_client = pr._embed_client
        old_attempted = pr._embed_client_attempted
        pr._embed_client = None
        pr._embed_client_attempted = False
        try:
            with patch.dict("os.environ", {}, clear=True):
                result = compute_context_precision("テスト " * 50)
            assert isinstance(result, PrecisionResult)
            assert result.diff == 0.0
        finally:
            pr._embed_client = old_client
            pr._embed_client_attempted = old_attempted

    def test_with_mock_api_simple_text(self):
        """モック API: 単純テキスト → 正の diff。"""
        import sys
        import hermeneus.src.precision_router as pr

        # アンカーを手動設定 (3次元の簡易版)
        pr._anchor_simple = [1.0, 0.0, 0.0]
        pr._anchor_complex = [0.0, 0.0, 1.0]

        # 単純テキストに近い embedding をモック
        mock_embedding = MagicMock()
        mock_embedding.values = [0.9, 0.1, 0.1]  # simple に近い

        mock_result = MagicMock()
        mock_result.embeddings = [mock_embedding]

        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = mock_result

        old_client = pr._embed_client
        old_attempted = pr._embed_client_attempted
        pr._embed_client = mock_client
        pr._embed_client_attempted = True

        # google.genai.types をモック注入 (未インストール環境対応)
        mock_types = MagicMock()
        modules_to_inject = {
            "google": MagicMock(),
            "google.genai": MagicMock(),
            "google.genai.types": mock_types,
        }
        # 既にインストール済みの場合は上書きしない
        inject = {k: v for k, v in modules_to_inject.items() if k not in sys.modules}

        try:
            sys.modules.update(inject)
            result = compute_context_precision("テスト " * 100)
            # cos(input, simple) > cos(input, complex) → 正の diff
            assert isinstance(result, PrecisionResult)
            assert result.diff > 0.0
        finally:
            for k in inject:
                sys.modules.pop(k, None)
            pr._embed_client = old_client
            pr._embed_client_attempted = old_attempted
            pr._anchor_simple = None
            pr._anchor_complex = None

    def test_with_mock_api_complex_text(self):
        """モック API: 複雑テキスト → 負の diff。"""
        import sys
        import hermeneus.src.precision_router as pr

        pr._anchor_simple = [1.0, 0.0, 0.0]
        pr._anchor_complex = [0.0, 0.0, 1.0]

        mock_embedding = MagicMock()
        mock_embedding.values = [0.1, 0.1, 0.9]  # complex に近い

        mock_result = MagicMock()
        mock_result.embeddings = [mock_embedding]

        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = mock_result

        old_client = pr._embed_client
        old_attempted = pr._embed_client_attempted
        pr._embed_client = mock_client
        pr._embed_client_attempted = True

        # google.genai.types をモック注入 (未インストール環境対応)
        mock_types = MagicMock()
        modules_to_inject = {
            "google": MagicMock(),
            "google.genai": MagicMock(),
            "google.genai.types": mock_types,
        }
        inject = {k: v for k, v in modules_to_inject.items() if k not in sys.modules}

        try:
            sys.modules.update(inject)
            result = compute_context_precision("テスト " * 100)
            # cos(input, simple) < cos(input, complex) → 負の diff
            assert isinstance(result, PrecisionResult)
            assert result.diff < 0.0
        finally:
            for k in inject:
                sys.modules.pop(k, None)
            pr._embed_client = old_client
            pr._embed_client_attempted = old_attempted
            pr._anchor_simple = None
            pr._anchor_complex = None

    def test_with_mock_api_empty_result(self):
        """モック API: 空の embedding → 0.0。"""
        import hermeneus.src.precision_router as pr

        pr._anchor_simple = [1.0, 0.0, 0.0]
        pr._anchor_complex = [0.0, 0.0, 1.0]

        mock_result = MagicMock()
        mock_result.embeddings = []  # 空

        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = mock_result

        old_client = pr._embed_client
        old_attempted = pr._embed_client_attempted
        pr._embed_client = mock_client
        pr._embed_client_attempted = True

        try:
            result = compute_context_precision("テスト " * 100)
            assert isinstance(result, PrecisionResult)
            assert result.diff == 0.0
        finally:
            pr._embed_client = old_client
            pr._embed_client_attempted = old_attempted
            pr._anchor_simple = None
            pr._anchor_complex = None
