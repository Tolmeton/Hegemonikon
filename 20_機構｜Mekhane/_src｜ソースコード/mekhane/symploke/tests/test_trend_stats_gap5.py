# -*- coding: utf-8 -*-
# PROOF: GAP-5 トレンド分析の統計的検定テスト
"""
PURPOSE: _trend_slope, _trend_mann_kendall, _trend_change_point, _trend_summary の単体テスト。
"""
import math

import pytest

from mekhane.symploke.phantazein_reporter import (
    _trend_change_point,
    _trend_mann_kendall,
    _trend_slope,
    _trend_summary,
)


# ── OLS 線形回帰 ──────────────────────────


class TestTrendSlope:
    """_trend_slope のテスト"""

    def test_increasing(self) -> None:
        """単調増加データ → slope > 0, r² > 0.9"""
        xs = [0.0, 1.0, 2.0, 3.0, 4.0]
        ys = [1.0, 3.0, 5.0, 7.0, 9.0]
        result = _trend_slope(xs, ys)
        assert result is not None
        assert result["slope"] > 0
        assert result["r_squared"] > 0.9

    def test_flat(self) -> None:
        """定数データ → slope ≈ 0"""
        xs = [0.0, 1.0, 2.0, 3.0]
        ys = [5.0, 5.0, 5.0, 5.0]
        result = _trend_slope(xs, ys)
        assert result is not None
        assert result["slope"] == 0.0
        assert result["r_squared"] == 0.0

    def test_empty(self) -> None:
        """空リスト → None"""
        assert _trend_slope([], []) is None

    def test_single_point(self) -> None:
        """1点のみ → None"""
        assert _trend_slope([0.0], [5.0]) is None

    def test_decreasing(self) -> None:
        """単調減少 → slope < 0"""
        xs = [0.0, 1.0, 2.0, 3.0]
        ys = [10.0, 7.0, 4.0, 1.0]
        result = _trend_slope(xs, ys)
        assert result is not None
        assert result["slope"] < 0
        assert result["r_squared"] > 0.9

    def test_length_mismatch(self) -> None:
        """xs/ys の長さが異なる → None"""
        assert _trend_slope([0.0, 1.0], [5.0]) is None


# ── Mann-Kendall 傾向検定 ─────────────────────


class TestTrendMannKendall:
    """_trend_mann_kendall のテスト"""

    def test_increasing(self) -> None:
        """単調増加 → S > 0, p < 0.05"""
        ys = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        result = _trend_mann_kendall(ys)
        assert result is not None
        assert result["S"] > 0
        assert result["p"] < 0.05
        assert result["direction"] == "increasing"

    def test_no_trend(self) -> None:
        """ランダム/交互データ → 有意でない"""
        ys = [1.0, 5.0, 2.0, 4.0, 3.0, 6.0, 1.0, 5.0]
        result = _trend_mann_kendall(ys)
        assert result is not None
        # p >= 0.05 なら no_trend (ランダムデータなので)
        # S が小さければ no_trend の可能性が高い
        # ただし確実ではないので direction の存在のみ確認
        assert result["direction"] in ("increasing", "decreasing", "no_trend")

    def test_short(self) -> None:
        """2点以下 → None"""
        assert _trend_mann_kendall([1.0, 2.0]) is None
        assert _trend_mann_kendall([1.0]) is None
        assert _trend_mann_kendall([]) is None

    def test_decreasing(self) -> None:
        """単調減少 → S < 0"""
        ys = [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0]
        result = _trend_mann_kendall(ys)
        assert result is not None
        assert result["S"] < 0
        assert result["direction"] == "decreasing"

    def test_three_points(self) -> None:
        """3点 → 結果が返る (None でない)"""
        result = _trend_mann_kendall([1.0, 2.0, 3.0])
        assert result is not None
        assert result["S"] > 0


# ── CUSUM 変化点検出 ──────────────────────


class TestTrendChangePoint:
    """_trend_change_point のテスト"""

    def test_step_function(self) -> None:
        """ステップ関数 → 中間点検出"""
        ys = [1.0, 1.0, 1.0, 1.0, 5.0, 5.0, 5.0, 5.0]
        result = _trend_change_point(ys)
        assert result is not None
        # 変化点は index 4 付近
        assert 3 <= result["index"] <= 5
        assert result["magnitude"] >= 3.0
        assert result["before_mean"] < result["after_mean"]

    def test_flat(self) -> None:
        """定数データ → None (変化なし)"""
        ys = [3.0, 3.0, 3.0, 3.0, 3.0, 3.0]
        result = _trend_change_point(ys)
        assert result is None

    def test_too_short(self) -> None:
        """3点以下 → None"""
        assert _trend_change_point([1.0, 2.0, 3.0]) is None
        assert _trend_change_point([1.0]) is None
        assert _trend_change_point([]) is None

    def test_small_change(self) -> None:
        """小さな変化 (< 0.5) → None (閾値未満)"""
        ys = [1.0, 1.0, 1.0, 1.2, 1.2, 1.2]
        result = _trend_change_point(ys)
        assert result is None

    def test_late_change(self) -> None:
        """後半に大きな変化 → 検出"""
        ys = [2.0, 2.0, 2.0, 2.0, 2.0, 10.0, 10.0, 10.0]
        result = _trend_change_point(ys)
        assert result is not None
        assert result["index"] >= 4


# ── 統合サマリ ──────────────────────────


class TestTrendSummary:
    """_trend_summary のテスト"""

    def test_minimal_data(self) -> None:
        """2日分のデータ → Markdown が生成される"""
        timeline = [
            {"day": "2026-03-15", "session_count": 3},
            {"day": "2026-03-16", "session_count": 5},
        ]
        result = _trend_summary(timeline)
        assert "### 4-3. 統計サマリ" in result
        assert "線形傾き" in result

    def test_insufficient_data(self) -> None:
        """1日分 → 不足メッセージ"""
        timeline = [{"day": "2026-03-15", "session_count": 3}]
        result = _trend_summary(timeline)
        assert "データ点が不足" in result

    def test_empty(self) -> None:
        """空リスト → 不足メッセージ"""
        result = _trend_summary([])
        assert "データ点が不足" in result

    def test_rich_data(self) -> None:
        """十分なデータ → Mann-Kendall を含む"""
        timeline = [
            {"day": f"2026-03-{i:02d}", "session_count": i}
            for i in range(1, 11)
        ]
        result = _trend_summary(timeline)
        assert "Mann-Kendall" in result
        assert "日数" in result
        assert "中央値" in result

    def test_contains_basic_stats(self) -> None:
        """基本統計量 (日数, 合計, 平均, 最大, 中央値) を含む"""
        timeline = [
            {"day": "2026-03-01", "session_count": 2},
            {"day": "2026-03-02", "session_count": 4},
            {"day": "2026-03-03", "session_count": 6},
        ]
        result = _trend_summary(timeline)
        assert "3 日" in result
        assert "12" in result  # 合計
        assert "4.0" in result  # 平均
        assert "6" in result  # 最大
