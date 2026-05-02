"""ABPP (Anchor-Based Precision Profiling) v5 のテスト。

precision_router.py の ABPPResult / ABPPCalculator / compute_abpp をテストする。
API 呼出はすべてモックで代替し、オフラインで実行可能。
"""

import json
import math
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

# テスト対象のインポート
from hermeneus.src.precision_router import (
    ABPPResult,
    ABPPCalculator,
    compute_abpp,
    _cosine_similarity,
)


# === テスト用定数 ===

# 768d の模擬 embedding (先頭のみ有意、残りゼロ)
def _mock_embedding(values: list[float], dim: int = 768) -> list[float]:
    """短い値リストを 768d に拡張する。"""
    result = list(values) + [0.0] * (dim - len(values))
    return result


# 「高精度」寄りの embedding: simple アンカーに近い
EMBED_HIGH_PREC = _mock_embedding([0.9, 0.1, 0.0, 0.0, 0.0])
# 「低精度」寄りの embedding: complex アンカーに近い
EMBED_LOW_PREC = _mock_embedding([0.1, 0.9, 0.0, 0.0, 0.0])
# 中間の embedding
EMBED_MID_PREC = _mock_embedding([0.5, 0.5, 0.0, 0.0, 0.0])

# モック用アンカー embedding
MOCK_ANCHORS = {
    "tech_precise": _mock_embedding([0.95, 0.05, 0.0, 0.0, 0.0]),
    "tech_vague": _mock_embedding([0.05, 0.95, 0.0, 0.0, 0.0]),
    "proc_precise": _mock_embedding([0.9, 0.1, 0.0, 0.0, 0.0]),
    "proc_vague": _mock_embedding([0.1, 0.9, 0.0, 0.0, 0.0]),
    "concept_precise": _mock_embedding([0.85, 0.15, 0.0, 0.0, 0.0]),
    "concept_vague": _mock_embedding([0.15, 0.85, 0.0, 0.0, 0.0]),
    "judge_precise": _mock_embedding([0.88, 0.12, 0.0, 0.0, 0.0]),
    "judge_vague": _mock_embedding([0.12, 0.88, 0.0, 0.0, 0.0]),
    "simple": _mock_embedding([0.92, 0.08, 0.0, 0.0, 0.0]),
    "complex": _mock_embedding([0.08, 0.92, 0.0, 0.0, 0.0]),
}


class TestABPPResult(unittest.TestCase):
    """ABPPResult データクラスのテスト。"""

    def test_creation(self):
        """正常に生成できること。"""
        r = ABPPResult(
            electrophoresis=0.7,
            chromatography=0.8,
            ief_score=0.6,
            ief_pattern="+++-",
            ensemble=0.72,
            axis_scores={"tech": 0.9, "proc": 0.7, "concept": 0.5, "judge": 0.6},
            api_calls=11,
        )
        self.assertAlmostEqual(r.electrophoresis, 0.7)
        self.assertAlmostEqual(r.ensemble, 0.72)
        self.assertEqual(r.ief_pattern, "+++-")
        self.assertEqual(r.api_calls, 11)

    def test_frozen(self):
        """frozen=True で変更不可であること。"""
        r = ABPPResult(
            electrophoresis=0.5, chromatography=0.5, ief_score=0.5,
            ief_pattern="++--", ensemble=0.5,
            axis_scores={}, api_calls=1,
        )
        with self.assertRaises(AttributeError):
            r.ensemble = 0.9  # type: ignore


class TestABPPCalculator(unittest.TestCase):
    """ABPPCalculator の各手法テスト。"""

    def setUp(self):
        """テスト用の calculator を準備 (アンカーをモック注入)。"""
        self.calc = ABPPCalculator()
        # アンカーを直接注入 (API 呼出を回避)
        self.calc._anchors = MOCK_ANCHORS
        self.calc._anchors_loaded = True

    def test_electrophoresis_high_precision(self):
        """高精度テキスト → 高い electrophoresis スコア。"""
        score = self.calc._electrophoresis(EMBED_HIGH_PREC)
        # 高精度は precise アンカー群に近い → 重心からの偏差もそれなり
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_chromatography_separation(self):
        """高精度 → 高いクロマトスコア、低精度 → 低いクロマトスコア。"""
        score_high = self.calc._chromatography(EMBED_HIGH_PREC)
        score_low = self.calc._chromatography(EMBED_LOW_PREC)
        # 高精度は simple に近い → 正の差分 → 高スコア
        # 低精度は complex に近い → 負の差分 → 低スコア
        self.assertGreater(score_high, score_low,
                           f"高精度 ({score_high:.4f}) > 低精度 ({score_low:.4f}) であるべき")

    def test_ief_pattern_high(self):
        """高精度テキスト → IEF パターンが "+" 多数。"""
        score, pattern, _axis = self.calc._ief(EMBED_HIGH_PREC)
        # 高精度は全軸の precise 側に近い → パターンは "++++" に近い
        plus_count = pattern.count("+")
        self.assertGreaterEqual(plus_count, 3,
                                f"高精度なら + が 3個以上。実際: {pattern}")

    def test_ief_pattern_low(self):
        """低精度テキスト → IEF パターンが "-" 多数。"""
        score, pattern, _axis = self.calc._ief(EMBED_LOW_PREC)
        minus_count = pattern.count("-")
        self.assertGreaterEqual(minus_count, 3,
                                f"低精度なら - が 3個以上。実際: {pattern}")

    def test_ensemble_weights(self):
        """アンサンブル重み (E=0.2, C=0.3, I=0.5) の正しい加重平均。"""
        result = self.calc._compute_ensemble(
            electro=0.6, chrom=0.8, ief=0.5
        )
        expected = 0.2 * 0.6 + 0.3 * 0.8 + 0.5 * 0.5
        self.assertAlmostEqual(result, expected, places=6,
                               msg=f"加重平均が一致しない: {result} != {expected}")

    def test_compute_full(self):
        """compute() が ABPPResult を返すこと (モック embedding)。"""
        # _get_embedding をモックしてテキストから embedding を返す
        self.calc._get_embedding = MagicMock(return_value=EMBED_HIGH_PREC)
        result = self.calc.compute("テストテキスト" * 10, depth=2)
        self.assertIsInstance(result, ABPPResult)
        self.assertGreaterEqual(result.ensemble, 0.0)
        self.assertLessEqual(result.ensemble, 1.0)
        self.assertEqual(len(result.ief_pattern), 4)
        self.assertIn("tech", result.axis_scores)
        self.assertIn("proc", result.axis_scores)
        self.assertIn("concept", result.axis_scores)
        self.assertIn("judge", result.axis_scores)

    def test_depth_controls_methods(self):
        """depth=0 はクロマト単体、depth=1 はクロマト+IEF、depth=2 は全3手法。"""
        self.calc._get_embedding = MagicMock(return_value=EMBED_MID_PREC)

        r0 = self.calc.compute("テスト" * 20, depth=0)
        r1 = self.calc.compute("テスト" * 20, depth=1)
        r2 = self.calc.compute("テスト" * 20, depth=2)

        # depth=0: electrophoresis は 0.0 (未計算)
        self.assertAlmostEqual(r0.electrophoresis, 0.0,
                               msg="depth=0 では electrophoresis=0.0")
        # depth=1: electrophoresis は 0.0、IEF は計算済み
        self.assertAlmostEqual(r1.electrophoresis, 0.0,
                               msg="depth=1 では electrophoresis=0.0")
        self.assertNotAlmostEqual(r1.ief_score, 0.0,
                                  msg="depth=1 では IEF は計算済み")
        # depth=2: 全て計算済み
        self.assertNotAlmostEqual(r2.electrophoresis, 0.0,
                                  msg="depth=2 では electrophoresis も計算済み")


class TestComputeABPPFallback(unittest.TestCase):
    """API 非対応環境での graceful fallback テスト。"""

    @patch("hermeneus.src.precision_router._get_embed_client", return_value=None)
    def test_no_api_key_returns_fallback(self, mock_client):
        """API キーなし → ensemble=0.5 の fallback。"""
        # singleton をリセット
        import hermeneus.src.precision_router as pr
        old_calc = pr._abpp_calculator
        pr._abpp_calculator = None
        try:
            result = compute_abpp("テスト" * 20)
            self.assertIsInstance(result, ABPPResult)
            self.assertAlmostEqual(result.ensemble, 0.5,
                                   msg="API なし時は ensemble=0.5")
            self.assertEqual(result.ief_pattern, "????",
                             msg="API なし時は ief_pattern='????'")
            self.assertEqual(result.api_calls, 0)
        finally:
            pr._abpp_calculator = old_calc


if __name__ == "__main__":
    unittest.main()
