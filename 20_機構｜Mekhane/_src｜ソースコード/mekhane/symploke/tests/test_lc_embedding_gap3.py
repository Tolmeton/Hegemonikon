# -*- coding: utf-8 -*-
"""GAP-3 テスト: L(c) embedding ベース Drift 計算。

テスト対象:
1. _compute_drift_embedding — 重心距離計算、フォールバック条件
2. _compute_lc_with_embedder — embedding 版 L(c) 計算
3. PhantazeinReporter のルーティング — embedder 有無でのパス分岐
"""
import math
import unittest
import warnings
from unittest.mock import MagicMock, patch

from mekhane.symploke.phantazein_reporter import (
    _compute_drift_approx,
    _compute_drift_embedding,
    _compute_efe,
    _compute_lc_approx,
    _compute_lc_with_embedder,
    _lc_grade,
    PhantazeinReporter,
)


def _make_embedder(vectors: list[list[float]], fail: bool = False):
    """テスト用の mock embedder を作成する。"""
    embedder = MagicMock()
    if fail:
        embedder.embed_batch.side_effect = RuntimeError("embed failed")
    else:
        embedder.embed_batch.return_value = vectors
    return embedder


class TestComputeDriftEmbedding(unittest.TestCase):
    """_compute_drift_embedding のユニットテスト。"""

    def test_valid_summaries_compute_drift(self):
        """有効な summary が十分あれば、各 summary の drift を返す。"""
        # 3つの似た summary (各30文字以上) → drift が小さい
        summaries = [
            "タスク管理のための実装計画書を作成して進捗を管理するものです。プロジェクトの品質を改善します。",
            "タスク管理の進捗トラッキングを行い、チームの生産性を向上させる。品質保証のための仕組みを構築。",
            "タスクリストの更新と管理を行います。継続的な改善のために定期的なレビューを実施しています。",
        ]
        # 似たベクトルを返す mock embedder
        vecs = [
            [0.9, 0.1, 0.0],
            [0.85, 0.15, 0.0],
            [0.88, 0.12, 0.0],
        ]
        embedder = _make_embedder(vecs)
        result = _compute_drift_embedding(summaries, embedder)

        self.assertEqual(len(result), 3)
        for d in result:
            self.assertGreaterEqual(d, 0.0)
            self.assertLessEqual(d, 1.0)
        # 似たベクトルなので drift は小さい
        self.assertLess(max(result), 0.1)

    def test_diverse_summaries_higher_drift(self):
        """異なる方向のベクトル → drift が大きい。"""
        summaries = [
            "タスク管理のための実装計画書を作成して進捗を管理するためのドキュメントを準備します。",
            "セキュリティ監査とリスク分析を実施して脆弱性を検出し修正方針を策定するレポートを作成。",
            "デザインパターンの美的評価基準を策定し、ユーザーインターフェースの品質を向上させます。",
            "パフォーマンス最適化のベンチマーク結果を分析して、システムのスループットを改善する計画です。",
        ]
        # 直交に近いベクトル
        vecs = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
        embedder = _make_embedder(vecs)
        result = _compute_drift_embedding(summaries, embedder)

        self.assertEqual(len(result), 4)
        # 直交なので drift は大きい
        self.assertGreater(min(result), 0.3)

    def test_insufficient_summaries_returns_empty(self):
        """有効な summary が min_summaries 未満なら空リストを返す。"""
        summaries = ["短", "短"]
        embedder = _make_embedder([[1, 0], [0, 1]])
        result = _compute_drift_embedding(summaries, embedder)

        self.assertEqual(result, [])

    def test_empty_summaries_marked_minus_one(self):
        """空の summary は -1.0 (フォールバック指示)。"""
        summaries = [
            "",
            "有効なサマリーテキストが入っている部分です。この部分は十分な長さを持っています。",
            "別の有効な summary テキスト内容です。こちらも十分な長さのテキストを含んでいます。",
            "三番目の有効な summary テキストです。品質評価に必要な情報を含むテキストです。",
        ]
        vecs = [
            [0.9, 0.1, 0.0],
            [0.85, 0.15, 0.0],
            [0.88, 0.12, 0.0],
        ]
        embedder = _make_embedder(vecs)
        result = _compute_drift_embedding(summaries, embedder)

        self.assertEqual(len(result), 4)
        self.assertEqual(result[0], -1.0)  # 空 summary → フォールバック
        for d in result[1:]:
            self.assertGreaterEqual(d, 0.0)

    def test_embed_failure_returns_empty(self):
        """embedding 失敗時は空リスト (全体フォールバック)。"""
        summaries = [
            "有効な summary テキストが入っている部分",
            "別の有効な summary テキスト内容",
            "三番目の有効な summary テキスト",
        ]
        embedder = _make_embedder([], fail=True)
        result = _compute_drift_embedding(summaries, embedder)

        self.assertEqual(result, [])


class TestComputeLcWithEmbedder(unittest.TestCase):
    """_compute_lc_with_embedder のユニットテスト。"""

    def test_embedding_drift_used(self):
        """embedding_drift >= 0 の場合、embedding 値が使われる。"""
        artifact = {
            "artifact_type": "implementation_plan",
            "mece_category": "A: 知識・分析",
            "summary": "有効な summary",
            "size_bytes": 1000,
        }
        result = _compute_lc_with_embedder(artifact, 1000, True, 0.1)

        self.assertEqual(result["drift"], 0.1)
        self.assertEqual(result["drift_source"], "embedding")
        self.assertIn("lc", result)
        self.assertIn("grade", result)

    def test_fallback_when_minus_one(self):
        """embedding_drift == -1.0 の場合、近似版にフォールバック。"""
        artifact = {
            "artifact_type": "other",
            "mece_category": "Z: その他",
            "summary": "",
            "size_bytes": 500,
        }
        result = _compute_lc_with_embedder(artifact, 1000, False, -1.0)

        self.assertEqual(result["drift_source"], "approx")
        self.assertGreater(result["drift"], 0.0)  # Z ペナルティ + summary 0

    def test_z_penalty_applied_with_embedding(self):
        """MECE Z ペナルティは embedding 版でも適用される。"""
        artifact_z = {
            "artifact_type": "other",
            "mece_category": "Z: その他",
            "summary": "有効な summary",
            "size_bytes": 1000,
        }
        artifact_a = {
            "artifact_type": "other",
            "mece_category": "A: 知識・分析",
            "summary": "有効な summary",
            "size_bytes": 1000,
        }
        result_z = _compute_lc_with_embedder(artifact_z, 1000, True, 0.1)
        result_a = _compute_lc_with_embedder(artifact_a, 1000, True, 0.1)

        # Z ペナルティ +0.1 が適用される
        self.assertAlmostEqual(result_z["drift"], 0.2)
        self.assertAlmostEqual(result_a["drift"], 0.1)

    def test_drift_source_in_result(self):
        """結果に drift_source キーが含まれる。"""
        artifact = {
            "artifact_type": "task",
            "mece_category": "A: 知識・分析",
            "summary": "summary",
            "size_bytes": 1000,
        }
        result_emb = _compute_lc_with_embedder(artifact, 1000, True, 0.05)
        result_fb = _compute_lc_with_embedder(artifact, 1000, True, -1.0)

        self.assertEqual(result_emb["drift_source"], "embedding")
        self.assertEqual(result_fb["drift_source"], "approx")

    def test_grade_boundaries(self):
        """grade が閾値に従って正しく設定される。"""
        artifact = {
            "artifact_type": "implementation_plan",
            "mece_category": "A: 知識・分析",
            "summary": "有効な summary テキスト",
            "size_bytes": 2000,
        }
        # drift=0, handoff=True → lc は低い (◎ 域)
        result = _compute_lc_with_embedder(artifact, 1000, True, 0.0)
        self.assertEqual(result["grade"], "◎")


class TestReporterRouting(unittest.TestCase):
    """PhantazeinReporter の embedder ルーティングテスト。"""

    def test_init_accepts_embedder(self):
        """__init__ が embedder パラメータを受け取る。"""
        mock_store = MagicMock()
        mock_embedder = MagicMock()
        reporter = PhantazeinReporter(store=mock_store, embedder=mock_embedder)

        self.assertIs(reporter._embedder, mock_embedder)

    def test_init_without_embedder(self):
        """embedder なしでも初期化できる。"""
        mock_store = MagicMock()
        reporter = PhantazeinReporter(store=mock_store)

        self.assertIsNone(reporter._embedder)


class TestBackwardCompatibility(unittest.TestCase):
    """既存の _compute_lc_approx との後方互換性テスト。"""

    def test_approx_still_works(self):
        """_compute_lc_approx が変更前と同じ結果を返す。"""
        artifact = {
            "artifact_type": "implementation_plan",
            "mece_category": "A: 知識・分析",
            "summary": "有効な summary テキスト",
            "size_bytes": 1000,
        }
        result = _compute_lc_approx(artifact, 1000, True)

        self.assertIn("drift", result)
        self.assertIn("efe", result)
        self.assertIn("lc", result)
        self.assertIn("grade", result)
        # drift_source は既存版には含まれない
        self.assertNotIn("drift_source", result)

    def test_embedding_version_same_efe_as_approx(self):
        """embedding 版と近似版で EFE が同じ値になる。"""
        artifact = {
            "artifact_type": "implementation_plan",
            "mece_category": "A: 知識・分析",
            "summary": "有効な summary テキスト",
            "size_bytes": 1500,
        }
        approx = _compute_lc_approx(artifact, 1000, True)
        emb = _compute_lc_with_embedder(artifact, 1000, True, 0.1)

        self.assertEqual(approx["efe"], emb["efe"])


class TestE3MockVerification(unittest.TestCase):
    """E-3 修正: mock embedder の呼出引数検証テスト。"""

    def test_embed_batch_called_with_correct_args(self):
        """embed_batch が正しい引数 (有効な summary のみ) で呼ばれる。"""
        summaries = [
            "",  # 空 → 除外される
            "タスク管理のための実装計画書を作成して進捗を管理するものです。プロジェクト品質改善。",
            "タスク管理の進捗トラッキングを行い、チームの生産性を向上させる。品質保証の仕組み。",
            "タスクリストの更新と管理を行います。継続的な改善のために定期的レビュー実施。",
        ]
        vecs = [
            [0.9, 0.1, 0.0],
            [0.85, 0.15, 0.0],
            [0.88, 0.12, 0.0],
        ]
        embedder = _make_embedder(vecs)
        _compute_drift_embedding(summaries, embedder)

        # embed_batch が1回だけ呼ばれたことの検証
        embedder.embed_batch.assert_called_once()
        # 呼出引数: 空 summary を除外した3つのみ
        called_args = embedder.embed_batch.call_args[0][0]
        self.assertEqual(len(called_args), 3)
        # 空 summary は除外されている
        for s in called_args:
            self.assertTrue(len(s) >= 30)


class TestE7TypeSafety(unittest.TestCase):
    """E-7 修正: embedder 型安全性テスト。"""

    def test_embedder_without_embed_batch_warns_and_disables(self):
        """embed_batch メソッドがないオブジェクトは警告して None 化する。"""
        mock_store = MagicMock()
        invalid_embedder = object()  # embed_batch がない

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            reporter = PhantazeinReporter(store=mock_store, embedder=invalid_embedder)

            self.assertIsNone(reporter._embedder)
            self.assertEqual(len(w), 1)
            self.assertIn("embed_batch", str(w[0].message))


class TestExtractedHelpers(unittest.TestCase):
    """E-1 修正: 抽出した共通関数のユニットテスト。"""

    def test_compute_drift_approx_median_match(self):
        """サイズが中央値と一致するとき、size_penalty は 0。"""
        artifact = {
            "size_bytes": 1000,
            "mece_category": "A: 知識・分析",
            "summary": "有効な summary テキスト (十分長い)",
        }
        drift = _compute_drift_approx(artifact, 1000)
        # log2(1.0) = 0 → size_penalty = 0, Z なし, summary あり → -0.05
        # drift = max(0.0, 0 + 0 + (-0.05)) = 0 (min clamp)
        self.assertAlmostEqual(drift, 0.0, places=2)

    def test_compute_drift_approx_z_penalty(self):
        """MECE Z カテゴリで Z ペナルティが加算される。"""
        artifact = {
            "size_bytes": 1000,
            "mece_category": "Z: その他",
            "summary": "有効な summary テキスト (十分長い)",
        }
        drift = _compute_drift_approx(artifact, 1000)
        self.assertGreaterEqual(drift, 0.15)  # z_penalty=0.2 + summary bonus=-0.05

    def test_compute_drift_approx_empty_summary(self):
        """summary 空でペナルティ加算。"""
        artifact = {
            "size_bytes": 1000,
            "mece_category": "A: 知識・分析",
            "summary": "",
        }
        drift = _compute_drift_approx(artifact, 1000)
        self.assertAlmostEqual(drift, 0.15, places=2)  # summary_penalty=0.15

    def test_compute_efe_plan_with_handoff(self):
        """implementation_plan + handoff → 高 EFE。"""
        artifact = {
            "artifact_type": "implementation_plan",
            "size_bytes": 2000,
        }
        efe = _compute_efe(artifact, 1000, session_has_handoff=True)
        # base=0.8 + size_bonus=0.1 + handoff=0.1 = 1.0 (min clamp)
        self.assertAlmostEqual(efe, 1.0, places=2)

    def test_compute_efe_other_no_handoff(self):
        """other タイプ + handoff なし → 低 EFE。"""
        artifact = {
            "artifact_type": "other",
            "size_bytes": 500,
        }
        efe = _compute_efe(artifact, 1000, session_has_handoff=False)
        # base=0.4, size_bonus=0 (500<1000), handoff=0 → 0.4
        self.assertAlmostEqual(efe, 0.4, places=2)

    def test_lc_grade_boundaries(self):
        """_lc_grade が閾値で正しい段階を返す。"""
        # LC_THRESHOLDS: kalon=0.2, ok=0.4, improve=0.6
        self.assertEqual(_lc_grade(0.1), "◎")   # <= 0.2
        self.assertEqual(_lc_grade(0.2), "◎")   # ちょうど kalon 境界
        self.assertEqual(_lc_grade(0.25), "◯")  # 0.2 < x <= 0.4
        self.assertEqual(_lc_grade(0.4), "◯")   # ちょうど ok 境界
        self.assertEqual(_lc_grade(0.5), "△")   # 0.4 < x <= 0.6
        self.assertEqual(_lc_grade(0.6), "△")   # ちょうど improve 境界
        self.assertEqual(_lc_grade(0.8), "✗")   # > 0.6

    def test_approx_and_embedder_efe_consistent(self):
        """approx 版と embedder 版の EFE が完全一致 (DRY 修正検証)。"""
        artifact = {
            "artifact_type": "walkthrough",
            "mece_category": "B: コード実装",
            "summary": "有効なサマリーテキスト",
            "size_bytes": 3000,
        }
        approx_result = _compute_lc_approx(artifact, 1000, True)
        embedder_result = _compute_lc_with_embedder(artifact, 1000, True, 0.1)

        # EFE は同じ共通関数 _compute_efe を使うので完全一致すべき
        self.assertEqual(approx_result["efe"], embedder_result["efe"])

    def test_drift_fallback_consistency(self):
        """embedder版のフォールバック drift が approx版と完全一致 (DRY 修正検証)。"""
        artifact = {
            "artifact_type": "other",
            "mece_category": "Z: その他",
            "summary": "",
            "size_bytes": 500,
        }
        approx_result = _compute_lc_approx(artifact, 1000, False)
        # フォールバック (embedding_drift=-1.0) → approx と同じ値であるべき
        embedder_result = _compute_lc_with_embedder(artifact, 1000, False, -1.0)

        self.assertEqual(approx_result["drift"], embedder_result["drift"])
        self.assertEqual(approx_result["efe"], embedder_result["efe"])
        self.assertEqual(approx_result["lc"], embedder_result["lc"])
        self.assertEqual(approx_result["grade"], embedder_result["grade"])


if __name__ == "__main__":
    unittest.main()

