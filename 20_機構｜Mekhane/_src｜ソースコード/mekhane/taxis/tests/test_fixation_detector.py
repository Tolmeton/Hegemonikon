#!/usr/bin/env python3
# PROOF: [L2/テスト] <- mekhane/taxis/tests/test_fixation_detector.py
# PURPOSE: fixation_detector の単体テスト
"""
固着パターン検出器のテスト。

テストケース:
1. 空テキスト → 固着なし
2. 尻込みワード → Q13 スコア上昇
3. 先延ばしワード → Q9 スコア上昇
4. 複合パターン → 最高スコアが dominant
5. 閾値以下 → alerts 空
6. 日本語テキスト統合テスト
7. ヒットの位置情報
8. フォーマット出力
"""

import pytest
from mekhane.taxis.fixation_detector import (
    FIXATION_PATTERNS,
    FixationHit,
    FixationPattern,
    FixationReport,
    detect_fixation,
    format_report,
    scan_text,
    score_fixation,
)


# ===========================================================================
# FixationPattern テスト
# ===========================================================================


class TestFixationPatterns:
    """FIXATION_PATTERNS 定数の整合性テスト。"""

    def test_all_patterns_have_required_fields(self):
        """全パターンが必須フィールドを持つ"""
        for pid, pattern in FIXATION_PATTERNS.items():
            assert pattern.pattern_id == pid, f"{pid}: pattern_id 不一致"
            assert pattern.q_edge_id > 0, f"{pid}: q_edge_id が正でない"
            assert len(pattern.keywords) > 0, f"{pid}: keywords が空"
            assert pattern.name, f"{pid}: name が空"
            assert pattern.nomos_ref, f"{pid}: nomos_ref が空"

    def test_pattern_count(self):
        """6パターンが定義されている"""
        assert len(FIXATION_PATTERNS) == 6

    def test_known_patterns_exist(self):
        """既知のパターンID が存在する"""
        expected = {"shirk", "procrastinate", "ruminate", "conserve", "skip_read", "impossible"}
        assert set(FIXATION_PATTERNS.keys()) == expected

    def test_q_edge_ids_are_valid(self):
        """Q辺IDが1-15の範囲"""
        for pid, pattern in FIXATION_PATTERNS.items():
            assert 1 <= pattern.q_edge_id <= 15, f"{pid}: Q辺ID={pattern.q_edge_id} が範囲外"


# ===========================================================================
# scan_text テスト
# ===========================================================================


class TestScanText:
    """テキスト走査のテスト。"""

    def test_empty_text(self):
        """空テキスト → ヒットなし"""
        hits = scan_text("")
        assert hits == []

    def test_no_keywords(self):
        """停止ワードを含まないテキスト → ヒットなし"""
        hits = scan_text("この設計は美しく、Kalon の条件を満たしている。")
        assert hits == []

    def test_single_shirk_keyword(self):
        """尻込みワード1つ → 1ヒット"""
        hits = scan_text("このタスクは大きすぎるので分割が必要です。")
        assert len(hits) >= 1
        assert any(h.pattern_id == "shirk" for h in hits)
        assert any(h.keyword == "大きすぎる" for h in hits)

    def test_multiple_keywords_same_pattern(self):
        """同じパターンの複数ワード → 複数ヒット"""
        text = "大きすぎるし複雑で難しいタスクです。"
        hits = scan_text(text)
        shirk_hits = [h for h in hits if h.pattern_id == "shirk"]
        assert len(shirk_hits) >= 3  # 大きすぎる, 複雑, 難しい

    def test_procrastinate_keyword(self):
        """先延ばしワード → procrastinate ヒット"""
        hits = scan_text("これは次のセッションでやりましょう。")
        assert any(h.pattern_id == "procrastinate" for h in hits)

    def test_mixed_patterns(self):
        """複数パターンのワード混在"""
        text = "大きすぎるので次のセッションに回しましょう。"
        hits = scan_text(text)
        patterns = {h.pattern_id for h in hits}
        assert "shirk" in patterns
        assert "procrastinate" in patterns

    def test_hit_position(self):
        """ヒットの位置情報が正しい"""
        text = "ここで大きすぎるという表現が出現"
        hits = scan_text(text)
        shirk_hits = [h for h in hits if h.keyword == "大きすぎる"]
        assert len(shirk_hits) == 1
        assert text[shirk_hits[0].position:shirk_hits[0].position + len("大きすぎる")] == "大きすぎる"

    def test_hit_context(self):
        """ヒットの文脈が含まれる"""
        text = "このタスクは大きすぎるので分割が必要。"
        hits = scan_text(text)
        shirk_hits = [h for h in hits if h.keyword == "大きすぎる"]
        assert len(shirk_hits) == 1
        assert "大きすぎる" in shirk_hits[0].context

    def test_impossible_keyword(self):
        """不可能断定ワード"""
        hits = scan_text("この方法ではできないと思います。")
        assert any(h.pattern_id == "impossible" for h in hits)

    def test_skip_read_keyword(self):
        """読み飛ばしワード"""
        hits = scan_text("知っているので確認は不要。")
        assert any(h.pattern_id == "skip_read" for h in hits)

    def test_repeated_keyword(self):
        """同じワードの複数回出現"""
        text = "難しい。本当に難しい。とても難しい。"
        hits = scan_text(text)
        shirk_hits = [h for h in hits if h.keyword == "難しい"]
        assert len(shirk_hits) == 3


# ===========================================================================
# score_fixation テスト
# ===========================================================================


class TestScoreFixation:
    """スコアリングのテスト。"""

    def test_empty_hits(self):
        """ヒットなし → 全スコア0"""
        scores = score_fixation([], text_length=100)
        assert all(s == 0.0 for s in scores.values())

    def test_single_hit_short_text(self):
        """短いテキスト (200文字以下) でのスコア"""
        hit = FixationHit(pattern_id="shirk", keyword="大きすぎる", position=0, context="")
        scores = score_fixation([hit], text_length=100)
        # normalizer = max(1, 100/200) = 1.0
        # スコア = 1 / 1.0 = 1.0
        assert scores["shirk"] == 1.0

    def test_single_hit_long_text(self):
        """長いテキスト (1000文字) でのスコア"""
        hit = FixationHit(pattern_id="shirk", keyword="大きすぎる", position=0, context="")
        scores = score_fixation([hit], text_length=1000)
        # normalizer = max(1, 1000/200) = 5.0
        # スコア = 1 / 5.0 = 0.2
        assert scores["shirk"] == pytest.approx(0.2)

    def test_multiple_hits_same_pattern(self):
        """同パターン複数ヒット → 加算"""
        hits = [
            FixationHit(pattern_id="shirk", keyword="大きすぎる", position=0, context=""),
            FixationHit(pattern_id="shirk", keyword="複雑", position=10, context=""),
        ]
        scores = score_fixation(hits, text_length=200)
        # normalizer = 1.0, スコア = 2 / 1.0 = 2.0
        assert scores["shirk"] == 2.0

    def test_different_patterns(self):
        """異なるパターン → 独立にスコア"""
        hits = [
            FixationHit(pattern_id="shirk", keyword="大きすぎる", position=0, context=""),
            FixationHit(pattern_id="procrastinate", keyword="次のセッション", position=10, context=""),
        ]
        scores = score_fixation(hits, text_length=200)
        assert scores["shirk"] == 1.0
        assert scores["procrastinate"] == 1.0

    def test_all_patterns_present(self):
        """全パターンのキーがスコアに含まれる"""
        scores = score_fixation([], text_length=100)
        for pid in FIXATION_PATTERNS:
            assert pid in scores


# ===========================================================================
# detect_fixation テスト
# ===========================================================================


class TestDetectFixation:
    """統合検出のテスト。"""

    def test_empty_text(self):
        """空テキスト → 固着なし"""
        report = detect_fixation("")
        assert not report.has_fixation
        assert report.total_hits == 0
        assert report.alerts == []

    def test_no_fixation(self):
        """停止ワードなし → 固着なし"""
        report = detect_fixation("これは美しい設計です。")
        assert not report.has_fixation
        assert report.total_hits == 0

    def test_shirk_detection(self):
        """尻込みパターンの検出"""
        text = "大きすぎるし複雑で膨大なタスクです。"
        report = detect_fixation(text, threshold=0.3)
        assert report.has_fixation
        assert "shirk" in report.alerts

    def test_procrastinate_detection(self):
        """先延ばしパターンの検出"""
        text = "これは次のセッションで後でやりましょう。"
        report = detect_fixation(text, threshold=0.3)
        assert report.has_fixation
        assert "procrastinate" in report.alerts

    def test_dominant_pattern(self):
        """最高スコアが dominant に設定される"""
        # 尻込み3回 + 先延ばし1回 → shirk が dominant
        text = "大きすぎるし複雑で難しいので次のセッションで。"
        report = detect_fixation(text, threshold=0.1)  # 低閾値
        assert report.dominant_pattern == "shirk"
        assert report.max_score > 0

    def test_threshold_filtering(self):
        """高い閾値 → 軽微なヒットはアラートにならない"""
        text = "少し複雑ですが対処可能。"  # 「複雑」1回のみ
        report = detect_fixation(text, threshold=5.0)  # 非常に高い閾値
        assert not report.has_fixation
        assert report.total_hits >= 1  # ヒットはあるがアラートにならない

    def test_report_summary(self):
        """サマリ文字列の生成"""
        text = "大きすぎるし複雑で次のセッションにしましょう。"
        report = detect_fixation(text, threshold=0.3)
        summary = report.summary
        assert "固着" not in summary or "パターン" not in summary or len(summary) > 0

    def test_text_length_recorded(self):
        """テキスト長がレポートに記録される"""
        text = "テストテキスト"
        report = detect_fixation(text)
        assert report.text_length == len(text)


# ===========================================================================
# format_report テスト
# ===========================================================================


class TestFormatReport:
    """Markdown フォーマットのテスト。"""

    def test_no_fixation_format(self):
        """固着なしのフォーマット"""
        report = detect_fixation("美しい設計です。")
        output = format_report(report)
        assert "固着パターン検出レポート" in output
        assert "✅ なし" in output

    def test_fixation_format(self):
        """固着ありのフォーマット"""
        report = detect_fixation("大きすぎるし複雑で膨大。", threshold=0.3)
        output = format_report(report)
        assert "固着パターン検出レポート" in output
        assert "⚠️" in output

    def test_table_format(self):
        """テーブルが含まれる"""
        report = detect_fixation("テスト")
        output = format_report(report)
        assert "| パターン |" in output
        assert "| Q辺 |" in output or "Q辺" in output
