#!/usr/bin/env python3
# PROOF: [L2/テスト] <- mekhane/taxis/tests/test_wf_pattern_detector.py
# PURPOSE: wf_pattern_detector のユニットテスト
"""
WF パターン検出器のテスト。

カバレッジ:
- THEOREM_MAP の整合性
- E/E 比計算
- 族エントロピー計算
- 日次推移計算
- 未使用定理検出
- 統合関数 detect_wf_pattern
- フォーマット関数
"""

import math
import pytest

from mekhane.taxis.wf_pattern_detector import (
    CHRONOS,
    DIASTASIS,
    EXPLOIT,
    EXPLORE,
    FAMILIES,
    KRISIS,
    METHODOS,
    OREXIS,
    TELOS,
    THEOREM_MAP,
    DailyStats,
    WFPatternReport,
    WFUsageRecord,
    analyze_ee_ratio,
    analyze_family_entropy,
    compute_daily_trend,
    detect_wf_pattern,
    find_unused_theorems,
    format_wf_report,
)


# ---------------------------------------------------------------------------
# テストデータ生成ヘルパー
# ---------------------------------------------------------------------------

def _make_record(tid: str, ts: float = 0.0, date: str = "2026-03-15") -> WFUsageRecord:
    """テスト用 WFUsageRecord を生成。"""
    info = THEOREM_MAP[tid]
    return WFUsageRecord(
        theorem_id=tid,
        timestamp=ts,
        family=info[0],
        ee_type=info[1],
        date=date,
    )


def _make_records(ids: list[str], date: str = "2026-03-15") -> list[WFUsageRecord]:
    """複数の定理IDからレコードリストを生成。"""
    return [_make_record(tid, ts=float(i), date=date) for i, tid in enumerate(ids)]


# ---------------------------------------------------------------------------
# THEOREM_MAP 整合性テスト
# ---------------------------------------------------------------------------

class TestTheoremMap:
    """THEOREM_MAP の整合性テスト。"""

    def test_has_24_theorems(self):
        """24定理が定義されているか"""
        assert len(THEOREM_MAP) == 24

    def test_all_families_covered(self):
        """6族全てが含まれるか"""
        families_in_map = {info[0] for info in THEOREM_MAP.values()}
        assert families_in_map == set(FAMILIES)

    def test_each_family_has_4(self):
        """各族に4定理あるか"""
        from collections import Counter
        family_counts = Counter(info[0] for info in THEOREM_MAP.values())
        for fam in FAMILIES:
            assert family_counts[fam] == 4, f"{fam} has {family_counts[fam]} theorems"

    def test_ee_types_valid(self):
        """E/E タイプが Explore/Exploit のいずれかか"""
        for tid, info in THEOREM_MAP.items():
            assert info[1] in (EXPLORE, EXPLOIT), f"{tid} has invalid ee_type: {info[1]}"

    def test_ee_balance_per_family(self):
        """各族に Explore/Exploit が最低1つずつあるか"""
        from collections import Counter
        for fam in FAMILIES:
            ee_types = [info[1] for info in THEOREM_MAP.values() if info[0] == fam]
            counter = Counter(ee_types)
            assert counter[EXPLORE] >= 1, f"{fam} has no Explore theorems"
            assert counter[EXPLOIT] >= 1, f"{fam} has no Exploit theorems"

    def test_theorem_ids_format(self):
        """定理 ID のフォーマットが正しいか"""
        for tid in THEOREM_MAP:
            assert len(tid) == 2, f"Invalid tid format: {tid}"
            assert tid[0] in "OHKADCM", f"Invalid prefix: {tid}"
            assert tid[1].isdigit(), f"Invalid suffix: {tid}"


# ---------------------------------------------------------------------------
# E/E 比テスト
# ---------------------------------------------------------------------------

class TestEERatio:
    """Explore/Exploit 比率計算のテスト。"""

    def test_empty_records(self):
        """空リスト → 0.5"""
        assert analyze_ee_ratio([]) == 0.5

    def test_all_explore(self):
        """全 Explore → 1.0"""
        records = _make_records(["O1", "O3", "H1", "H3"])
        assert analyze_ee_ratio(records) == 1.0

    def test_all_exploit(self):
        """全 Exploit → 0.0"""
        records = _make_records(["O2", "O4", "H2", "H4"])
        assert analyze_ee_ratio(records) == 0.0

    def test_balanced(self):
        """均等 → 0.5"""
        records = _make_records(["O1", "O2", "O3", "O4"])
        assert analyze_ee_ratio(records) == 0.5

    def test_weighted(self):
        """3:1 → 0.75"""
        records = _make_records(["O1", "O3", "H1", "O2"])
        assert analyze_ee_ratio(records) == 0.75


# ---------------------------------------------------------------------------
# エントロピーテスト
# ---------------------------------------------------------------------------

class TestFamilyEntropy:
    """族エントロピー計算のテスト。"""

    def test_empty_records(self):
        """空リスト → 0.0"""
        assert analyze_family_entropy([]) == 0.0

    def test_single_family(self):
        """1族のみ → 0.0"""
        records = _make_records(["O1", "O2", "O3", "O4"])
        assert analyze_family_entropy(records) == 0.0

    def test_two_families_equal(self):
        """2族均等 → 1.0"""
        records = _make_records(["O1", "O1", "H1", "H1"])
        assert abs(analyze_family_entropy(records) - 1.0) < 0.001

    def test_all_families_equal(self):
        """6族均等 → log2(6)"""
        records = _make_records(["O1", "H1", "K1", "A1", "D1", "C1"])
        expected = math.log2(6)
        assert abs(analyze_family_entropy(records) - expected) < 0.001

    def test_skewed(self):
        """偏った分布 → 低エントロピー"""
        # Telos 8件、他1件ずつ
        records = _make_records(["O1"]*8 + ["H1", "K1", "A1", "D1", "C1"])
        entropy = analyze_family_entropy(records)
        max_entropy = math.log2(6)
        assert entropy < max_entropy * 0.8  # 明確に低い


# ---------------------------------------------------------------------------
# 日次推移テスト
# ---------------------------------------------------------------------------

class TestDailyTrend:
    """日次推移計算のテスト。"""

    def test_empty(self):
        """空 → 空"""
        assert compute_daily_trend([]) == []

    def test_single_day(self):
        """1日分"""
        records = _make_records(["O1", "O2", "O3"], date="2026-03-15")
        trend = compute_daily_trend(records)
        assert len(trend) == 1
        assert trend[0].date == "2026-03-15"
        assert trend[0].explore == 2
        assert trend[0].exploit == 1

    def test_multi_day(self):
        """複数日"""
        r1 = _make_records(["O1", "O2"], date="2026-03-14")
        r2 = _make_records(["O3", "O4"], date="2026-03-15")
        trend = compute_daily_trend(r1 + r2)
        assert len(trend) == 2
        assert trend[0].date == "2026-03-14"
        assert trend[1].date == "2026-03-15"


# ---------------------------------------------------------------------------
# 未使用定理テスト
# ---------------------------------------------------------------------------

class TestUnusedTheorems:
    """未使用定理検出のテスト。"""

    def test_empty(self):
        """空 → 全24定理"""
        unused = find_unused_theorems([])
        assert len(unused) == 24

    def test_all_used(self):
        """全使用 → 空"""
        records = _make_records(list(THEOREM_MAP.keys()))
        unused = find_unused_theorems(records)
        assert unused == []

    def test_partial(self):
        """一部使用"""
        records = _make_records(["O1", "O2"])
        unused = find_unused_theorems(records)
        assert "O1" not in unused
        assert "O2" not in unused
        assert "O3" in unused
        assert len(unused) == 22


# ---------------------------------------------------------------------------
# 統合関数テスト
# ---------------------------------------------------------------------------

class TestDetectWFPattern:
    """detect_wf_pattern 統合テスト。"""

    def test_empty_records(self):
        """空入力"""
        report = detect_wf_pattern(records=[])
        assert report.total_records == 0
        assert report.ee_ratio == 0.5
        assert len(report.unused_theorems) == 24
        assert not report.has_imbalance

    def test_exploit_heavy(self):
        """Exploit 偏重 → アラート"""
        records = _make_records(["O2", "O4", "H2", "H4", "K1", "K3"] * 5)
        report = detect_wf_pattern(records=records, ee_threshold_low=0.25)
        assert report.ee_ratio == 0.0
        assert report.has_imbalance
        assert any("Exploit偏重" in a for a in report.alerts)

    def test_explore_heavy(self):
        """Explore 偏重 → アラート"""
        records = _make_records(["O1", "O3", "H1", "H3", "K2", "K4"] * 5)
        report = detect_wf_pattern(records=records, ee_threshold_high=0.75)
        assert report.ee_ratio == 1.0
        assert report.has_imbalance
        assert any("Explore偏重" in a for a in report.alerts)

    def test_balanced(self):
        """均衡 → アラートなし (E/E, 族エントロピーともに正常)"""
        all_ids = list(THEOREM_MAP.keys())
        records = _make_records(all_ids * 2)  # 各2回
        report = detect_wf_pattern(records=records)
        # E/E は 24定理中 Explore 12, Exploit 12 → 0.5
        assert 0.4 <= report.ee_ratio <= 0.6
        # 族は6族均等 → 高エントロピー
        assert report.entropy_ratio > 0.9
        # 未使用なし
        assert report.unused_theorems == []

    def test_family_deficit(self):
        """特定族の欠如 → アラート"""
        # Chronos 以外を大量に
        records = _make_records(["O1", "H1", "K1", "A1", "D1"] * 10)
        report = detect_wf_pattern(records=records)
        assert any("Chronos 欠如" in a for a in report.alerts)

    def test_top_theorem(self):
        """最頻定理が正しいか"""
        records = _make_records(["O1"] * 10 + ["O2"] * 3)
        report = detect_wf_pattern(records=records)
        assert report.top_theorem == "O1"
        assert report.top_count == 10


# ---------------------------------------------------------------------------
# フォーマットテスト
# ---------------------------------------------------------------------------

class TestFormatWFReport:
    """フォーマット関数のテスト。"""

    def test_format_empty(self):
        """空レポートのフォーマット"""
        report = detect_wf_pattern(records=[])
        md = format_wf_report(report)
        assert "📊" in md
        assert "✅ 均衡的" in md

    def test_format_with_alerts(self):
        """アラート付きレポートのフォーマット"""
        records = _make_records(["O2", "O4", "H2", "H4"] * 10)
        report = detect_wf_pattern(records=records)
        md = format_wf_report(report)
        assert "⚠️" in md
        assert "Exploit" in md or "族偏り" in md

    def test_format_has_table(self):
        """テーブルが含まれるか"""
        records = _make_records(list(THEOREM_MAP.keys()))
        report = detect_wf_pattern(records=records)
        md = format_wf_report(report)
        # 族テーブル
        assert "| Telos |" in md
        assert "| Chronos |" in md

    def test_format_daily_trend(self):
        """日次推移テーブルが含まれるか"""
        records = _make_records(["O1", "O2"], date="2026-03-15")
        report = detect_wf_pattern(records=records)
        md = format_wf_report(report)
        assert "日次 E/E 推移" in md
        assert "2026-03-15" in md


# ---------------------------------------------------------------------------
# DailyStats テスト
# ---------------------------------------------------------------------------

class TestDailyStats:
    """DailyStats のプロパティテスト。"""

    def test_empty(self):
        """データなし → 中立"""
        ds = DailyStats(date="2026-03-15")
        assert ds.total == 0
        assert ds.ee_ratio == 0.5

    def test_all_explore(self):
        ds = DailyStats(date="2026-03-15", explore=10, exploit=0)
        assert ds.ee_ratio == 1.0

    def test_mixed(self):
        ds = DailyStats(date="2026-03-15", explore=3, exploit=7)
        assert abs(ds.ee_ratio - 0.3) < 0.001


# ---------------------------------------------------------------------------
# WFPatternReport プロパティテスト
# ---------------------------------------------------------------------------

class TestWFPatternReport:
    """WFPatternReport のプロパティテスト。"""

    def test_entropy_ratio(self):
        """正規化エントロピーの計算"""
        report = WFPatternReport(
            window_days=7,
            total_records=100,
            ee_ratio=0.5,
            family_entropy=math.log2(6),
            max_entropy=math.log2(6),
            family_counts={},
            unused_theorems=[],
            daily_trend=[],
        )
        assert abs(report.entropy_ratio - 1.0) < 0.001

    def test_has_imbalance(self):
        """アラートなし → False"""
        report = WFPatternReport(
            window_days=7,
            total_records=0,
            ee_ratio=0.5,
            family_entropy=0,
            max_entropy=math.log2(6),
            family_counts={},
            unused_theorems=[],
            daily_trend=[],
            alerts=[],
        )
        assert not report.has_imbalance
