"""GAP-4: Handoff 品質スコアリング — ユニットテスト.

5軸のヘルパー関数 + 統合スコアリング関数 + _hq_grade をテスト。
C-1〜C-5 修正後の仕様に準拠。
"""
import datetime
import unittest

from mekhane.symploke.phantazein_reporter import (
    HQ_THRESHOLDS,
    HQ_WEIGHTS,
    _hq_grade,
    _score_handoff_density,
    _score_handoff_fresh,
    _score_handoff_link,
    _score_handoff_quality,
    _score_handoff_size,
    _score_handoff_struct,
)


# ── _hq_grade テスト ────────────────────────────────────────
class TestHqGrade(unittest.TestCase):
    """H(q) 値から品質段階を正しく返すか。"""

    def test_kalon(self):
        self.assertEqual(_hq_grade(0.75), "◎")
        self.assertEqual(_hq_grade(1.0), "◎")

    def test_ok(self):
        self.assertEqual(_hq_grade(0.50), "◯")
        self.assertEqual(_hq_grade(0.74), "◯")

    def test_improve(self):
        self.assertEqual(_hq_grade(0.30), "△")
        self.assertEqual(_hq_grade(0.49), "△")

    def test_bad(self):
        self.assertEqual(_hq_grade(0.0), "✗")
        self.assertEqual(_hq_grade(0.29), "✗")


# ── _score_handoff_struct テスト (C-1: SBAR 形式) ────────────
class TestScoreHandoffStruct(unittest.TestCase):
    """構造完全性スコアのテスト (SBAR 形式)。"""

    def test_empty_content(self):
        """空文字列は 0.0。"""
        self.assertEqual(_score_handoff_struct(""), 0.0)

    def test_all_sections_present_text(self):
        """全 SBAR セクションのテキストが存在 → 1.0。"""
        content = """\
# Handoff

## 状況
現在の状況説明

## 背景
背景情報

## 評価
評価結果

## 推奨
推奨事項
"""
        self.assertEqual(_score_handoff_struct(content), 1.0)

    def test_all_sections_present_emoji(self):
        """全 SBAR セクションの Emoji が存在 → 1.0。"""
        content = """\
📋 状況の説明
📊 背景データ
✅ 評価結果
📌 推奨アクション
"""
        self.assertEqual(_score_handoff_struct(content), 1.0)

    def test_partial_sections(self):
        """一部セクションのみ → 0.5。"""
        content = """\
## 状況
状況テスト

## 背景
背景テスト
"""
        self.assertEqual(_score_handoff_struct(content), 0.5)

    def test_no_sections(self):
        """セクションなし → 0.0。"""
        content = "ただの文章です。特にセクションはありません。"
        self.assertEqual(_score_handoff_struct(content), 0.0)

    def test_old_format_not_matched(self):
        """旧形式 (セッション目標/完了タスク等) は検出されない。"""
        content = """\
## セッション目標
目標テスト

## 完了タスク
タスクA
"""
        self.assertEqual(_score_handoff_struct(content), 0.0)


# ── _score_handoff_size テスト ───────────────────────────────
class TestScoreHandoffSize(unittest.TestCase):
    """サイズ適正スコアのテスト。"""

    def test_tiny(self):
        """500B 未満 → 0.0。"""
        self.assertEqual(_score_handoff_size(100), 0.0)

    def test_small(self):
        """500-2000B → 0.5。"""
        self.assertEqual(_score_handoff_size(1000), 0.5)

    def test_optimal(self):
        """2000-8000B → 1.0 (最適帯)。"""
        self.assertEqual(_score_handoff_size(3000), 1.0)
        self.assertEqual(_score_handoff_size(8000), 1.0)

    def test_large(self):
        """8001-15000B → 0.7。"""
        self.assertEqual(_score_handoff_size(12000), 0.7)

    def test_huge(self):
        """15000B 超 → 0.4。"""
        self.assertEqual(_score_handoff_size(20000), 0.4)

    def test_boundary_500(self):
        """境界値 500B → 0.5 (small 帯)。"""
        self.assertEqual(_score_handoff_size(500), 0.5)

    def test_boundary_2000(self):
        """境界値 2000B → 1.0 (optimal 帯)。"""
        self.assertEqual(_score_handoff_size(2000), 1.0)


# ── _score_handoff_link テスト ───────────────────────────────
class TestScoreHandoffLink(unittest.TestCase):
    """セッション紐づけスコアのテスト。"""

    def test_id_match(self):
        """session_id が既知セッションに一致 → 1.0。"""
        self.assertEqual(_score_handoff_link("abc", {"abc", "def"}), 1.0)

    def test_id_exists_no_match(self):
        """session_id はあるがセッションテーブルにない → 0.5。"""
        self.assertEqual(_score_handoff_link("xyz", {"abc", "def"}), 0.5)

    def test_no_id(self):
        """session_id なし → 0.0。"""
        self.assertEqual(_score_handoff_link(None, {"abc"}), 0.0)
        self.assertEqual(_score_handoff_link("", {"abc"}), 0.0)


# ── _score_handoff_fresh テスト (C-2: 日数ベース拡張) ────────
class TestScoreHandoffFresh(unittest.TestCase):
    """鮮度スコアのテスト (C-2: version + created_at ベース)。"""

    def test_version_only_no_date(self):
        """version あり + 日付なし → 0.8。"""
        self.assertEqual(_score_handoff_fresh("v4.3"), 0.8)

    def test_version_with_recent_date(self):
        """version あり + 今日作成 → 1.0。"""
        today = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.assertEqual(_score_handoff_fresh("v4.3", today), 1.0)

    def test_version_with_old_date(self):
        """version あり + 60日前 → 0.6。"""
        old = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=60)).isoformat()
        self.assertEqual(_score_handoff_fresh("v4.3", old), 0.6)

    def test_version_with_30day_date(self):
        """version あり + 15日前 → 0.8。"""
        mid = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=15)).isoformat()
        self.assertEqual(_score_handoff_fresh("v4.3", mid), 0.8)

    def test_no_version_no_date(self):
        """version なし + 日付なし → 0.3。"""
        self.assertEqual(_score_handoff_fresh(None), 0.3)
        self.assertEqual(_score_handoff_fresh(""), 0.3)

    def test_no_version_old_date(self):
        """version なし + 60日前 → 0.1。"""
        old = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=60)).isoformat()
        self.assertEqual(_score_handoff_fresh(None, old), 0.1)
        self.assertEqual(_score_handoff_fresh("", old), 0.1)


# ── _score_handoff_density テスト (C-3: 正規表現 + チェックリスト) ──
class TestScoreHandoffDensity(unittest.TestCase):
    """内容密度スコアのテスト (C-3: 番号リスト + チェックリスト対応)。"""

    def test_empty_content(self):
        """空文字列は 0.0。"""
        self.assertEqual(_score_handoff_density(""), 0.0)

    def test_dense_content(self):
        """箇条書き・テーブルが多い → 高スコア。"""
        content = """# Title
- item 1
- item 2
- item 3
| col1 | col2 |
| v1   | v2   |
"""
        score = _score_handoff_density(content)
        self.assertGreater(score, 0.5)

    def test_sparse_content(self):
        """テキストのみ → 低スコア。"""
        content = """長い散文です。
構造化されていません。
ただの文章が続きます。
特に何もありません。
なにもないです。
本当になにもない。
"""
        score = _score_handoff_density(content)
        self.assertLess(score, 0.5)

    def test_code_block(self):
        """コードブロック内の行は info_elements としてカウント。"""
        content = """# Code
```python
def foo():
    return 42
```
"""
        score = _score_handoff_density(content)
        self.assertGreater(score, 0.0)

    def test_capped_at_1(self):
        """密度は 1.0 を超えない。"""
        lines = ["- item " + str(i) for i in range(100)]
        content = "\n".join(lines)
        score = _score_handoff_density(content)
        self.assertLessEqual(score, 1.0)

    def test_ordered_list_double_digit(self):
        """10. 以上の番号付きリストも検出する (C-3 修正)。"""
        content = "\n".join([f"{i}. タスク{i}" for i in range(1, 15)])
        score = _score_handoff_density(content)
        # 14行中14行が info_elements → 高スコア
        self.assertGreater(score, 0.9)

    def test_checklist_detection(self):
        """チェックリスト (- [x], - [ ]) も info_elements として検出 (C-3 修正)。"""
        content = """\
- [x] 完了タスクA
- [ ] 未完了タスクB
- [x] 完了タスクC
散文行
散文行
"""
        score = _score_handoff_density(content)
        # 5行中3行が info_elements → 3/(5*0.5) = 1.0+
        self.assertGreater(score, 0.5)


# ── _score_handoff_quality 統合テスト (C-5: content_available) ──
class TestScoreHandoffQuality(unittest.TestCase):
    """統合品質スコアのテスト。"""

    def test_perfect_handoff(self):
        """全条件が最良 → 高スコア + ◎。"""
        today = datetime.datetime.now(datetime.timezone.utc).isoformat()
        handoff = {
            "session_id": "abc123",
            "handoff_version": "v4.3",
            "size_bytes": 4000,
            "created_at": today,
        }
        session_ids = {"abc123"}
        content = """\
## 状況
Goal

## 背景
- context A
- context B

## 評価
- assessment X

## 推奨
- next Y
"""
        result = _score_handoff_quality(handoff, session_ids, content)

        self.assertEqual(result["link"], 1.0)
        self.assertEqual(result["fresh"], 1.0)
        self.assertEqual(result["size"], 1.0)
        self.assertEqual(result["struct"], 1.0)
        self.assertGreater(result["density"], 0.0)
        self.assertGreaterEqual(result["total"], HQ_THRESHOLDS["kalon"])
        self.assertEqual(result["grade"], "◎")
        self.assertTrue(result["content_available"])

    def test_minimal_handoff(self):
        """最小限の Handoff → 低スコア。"""
        handoff = {
            "session_id": "",
            "handoff_version": "",
            "size_bytes": 100,
        }
        result = _score_handoff_quality(handoff, set(), None)

        self.assertEqual(result["link"], 0.0)
        self.assertEqual(result["fresh"], 0.3)  # C-2: version なし → 0.3
        self.assertEqual(result["size"], 0.0)
        # content=None → struct/density は中立 0.5
        self.assertEqual(result["struct"], 0.5)
        self.assertEqual(result["density"], 0.5)
        self.assertFalse(result["content_available"])  # C-5: content 不可
        self.assertIn(result["grade"], ("✗", "△"))

    def test_weight_sum_is_1(self):
        """重みの合計が 1.0 であること。"""
        total_weight = sum(HQ_WEIGHTS.values())
        self.assertAlmostEqual(total_weight, 1.0, places=10)

    def test_result_keys(self):
        """戻り値の dict に必要なキーが全てある (C-5: content_available 含む)。"""
        handoff = {"session_id": "", "handoff_version": "", "size_bytes": 1000}
        result = _score_handoff_quality(handoff, set())
        expected_keys = {
            "struct", "size", "link", "fresh", "density",
            "total", "grade", "content_available",
        }
        self.assertEqual(set(result.keys()), expected_keys)

    def test_none_safe(self):
        """handoff dict に None 値がある場合でもクラッシュしない。"""
        handoff = {
            "session_id": None,
            "handoff_version": None,
            "size_bytes": None,
        }
        result = _score_handoff_quality(handoff, set())
        self.assertIsInstance(result["total"], float)
        self.assertIn(result["grade"], ("◎", "◯", "△", "✗"))

    def test_content_available_true_when_provided(self):
        """content を渡した場合 content_available=True。"""
        handoff = {"session_id": "", "handoff_version": "", "size_bytes": 1000}
        result = _score_handoff_quality(handoff, set(), "some content")
        self.assertTrue(result["content_available"])

    def test_content_available_false_when_none(self):
        """content=None の場合 content_available=False。"""
        handoff = {"session_id": "", "handoff_version": "", "size_bytes": 1000}
        result = _score_handoff_quality(handoff, set(), None)
        self.assertFalse(result["content_available"])


if __name__ == "__main__":
    unittest.main()
