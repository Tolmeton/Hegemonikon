# noqa: AI-ALL
# PROOF: [L2/テスト] <- mekhane/tests/
"""
PROOF: [L2/テスト] このファイルは存在しなければならない

A0 (FEP) → temporal.py の正しさは予測誤差最小化のための前提
→ テストが正しさを保証する

# PURPOSE: pks/temporal.py のユニットテスト
"""

import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from mekhane.pks.temporal import (
    AnomalyResult,
    AnomalyType,
    ChangeEvent,
    ExponentialDecay,
    MentionStats,
    Observation,
    TemporalReasoningService,
    TrendDirection,
    TrendResult,
)


# --- ExponentialDecay ---


class TestExponentialDecay:
    """ExponentialDecay の数学的正確性テスト"""

    # PURPOSE: 経過0日は減衰なし (score=1.0)
    def test_decay_zero_days(self):
        d = ExponentialDecay(half_life_days=7.0)
        assert d.decay(0) == 1.0

    # PURPOSE: 半減期で score ≈ 0.5
    def test_decay_half_life(self):
        d = ExponentialDecay(half_life_days=7.0)
        assert abs(d.decay(7.0) - 0.5) < 0.001

    # PURPOSE: 半減期の2倍で score ≈ 0.25
    def test_decay_double_half_life(self):
        d = ExponentialDecay(half_life_days=7.0)
        assert abs(d.decay(14.0) - 0.25) < 0.001

    # PURPOSE: 負の日数は 1.0 を返す
    def test_decay_negative_days(self):
        d = ExponentialDecay(half_life_days=7.0)
        assert d.decay(-5) == 1.0

    # PURPOSE: 大きな日数はほぼ 0
    def test_decay_large_days(self):
        d = ExponentialDecay(half_life_days=7.0)
        assert d.decay(100) < 0.001

    # PURPOSE: half_life_days <= 0 は ValueError
    def test_invalid_half_life(self):
        with pytest.raises(ValueError):
            ExponentialDecay(half_life_days=0)
        with pytest.raises(ValueError):
            ExponentialDecay(half_life_days=-1)

    # PURPOSE: タイムスタンプからのスコア計算
    def test_score_from_timestamp(self):
        d = ExponentialDecay(half_life_days=7.0)
        now = datetime(2026, 3, 14, 12, 0, 0)
        one_week_ago = (now - timedelta(days=7)).isoformat()
        score = d.score_from_timestamp(one_week_ago, now=now)
        assert abs(score - 0.5) < 0.001

    # PURPOSE: 不正なタイムスタンプは 0.0
    def test_score_from_invalid_timestamp(self):
        d = ExponentialDecay(half_life_days=7.0)
        assert d.score_from_timestamp("invalid") == 0.0


# --- Observation ---


class TestObservation:
    """Observation のシリアライズテスト"""

    # PURPOSE: dict 変換のラウンドトリップ
    def test_roundtrip(self):
        obs = Observation(
            entity_id="paper_001",
            field_name="citations",
            value="42",
            timestamp="2026-03-14T12:00:00",
        )
        d = obs.to_dict()
        restored = Observation.from_dict(d)
        assert restored.entity_id == obs.entity_id
        assert restored.field_name == obs.field_name
        assert restored.value == obs.value
        assert restored.timestamp == obs.timestamp


# --- TemporalReasoningService ---


@pytest.fixture
def tmp_state_dir():
    """テスト用一時ディレクトリ"""
    d = tempfile.mkdtemp(prefix="test_temporal_")
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


class TestChangeDetection:
    """変更検出テスト"""

    # PURPOSE: 値が変化したエンティティを検出
    def test_detect_value_change(self, tmp_state_dir):
        svc = TemporalReasoningService(tmp_state_dir)

        svc.record_observation("p1", "citations", "10", "2026-03-01T00:00:00")
        svc.record_observation("p1", "citations", "25", "2026-03-14T00:00:00")

        changes = svc.get_changes_since("2026-03-07T00:00:00")
        assert len(changes) == 1
        assert changes[0].entity_id == "p1"
        assert changes[0].old_value == "10"
        assert changes[0].new_value == "25"

    # PURPOSE: 新規エンティティ (before なし) の検出
    def test_detect_new_entity(self, tmp_state_dir):
        svc = TemporalReasoningService(tmp_state_dir)

        svc.record_observation("p2", "status", "active", "2026-03-14T00:00:00")

        changes = svc.get_changes_since("2026-03-07T00:00:00")
        assert len(changes) == 1
        assert changes[0].old_value == ""
        assert changes[0].new_value == "active"

    # PURPOSE: 値が変化していない場合は検出なし
    def test_no_change_when_same_value(self, tmp_state_dir):
        svc = TemporalReasoningService(tmp_state_dir)

        svc.record_observation("p3", "status", "active", "2026-03-01T00:00:00")
        svc.record_observation("p3", "status", "active", "2026-03-14T00:00:00")

        changes = svc.get_changes_since("2026-03-07T00:00:00")
        assert len(changes) == 0

    # PURPOSE: 複数エンティティの変更を検出
    def test_multiple_entities(self, tmp_state_dir):
        svc = TemporalReasoningService(tmp_state_dir)

        svc.record_observation("p1", "citations", "10", "2026-03-01T00:00:00")
        svc.record_observation("p1", "citations", "20", "2026-03-14T00:00:00")
        svc.record_observation("p2", "status", "draft", "2026-03-01T00:00:00")
        svc.record_observation("p2", "status", "published", "2026-03-14T00:00:00")

        changes = svc.get_changes_since("2026-03-07T00:00:00")
        assert len(changes) == 2


class TestTrendAnalysis:
    """トレンド分析テスト"""

    # PURPOSE: 増加パターンは RISING
    def test_rising_trend(self, tmp_state_dir):
        svc = TemporalReasoningService(tmp_state_dir)
        now = datetime.now()

        # 前期: 1回/日 × 3日
        for i in range(3):
            day = now - timedelta(days=10 + i)
            svc.record_observation("concept_fep", "mention", "x", day.isoformat())

        # 現期: 5回/日 × 3日
        for i in range(3):
            day = now - timedelta(days=i + 1)
            for _ in range(5):
                svc.record_observation("concept_fep", "mention", "x", day.isoformat())

        trends = svc.analyze_trends(period_days=7)
        fep_trends = [t for t in trends if t.entity_id == "concept_fep"]
        assert len(fep_trends) == 1
        assert fep_trends[0].direction == TrendDirection.RISING
        assert fep_trends[0].change_ratio > 0.2

    # PURPOSE: 減少パターンは FALLING
    def test_falling_trend(self, tmp_state_dir):
        svc = TemporalReasoningService(tmp_state_dir)
        now = datetime.now()

        # 前期: 5回/日 × 3日
        for i in range(3):
            day = now - timedelta(days=10 + i)
            for _ in range(5):
                svc.record_observation("topic_old", "mention", "x", day.isoformat())

        # 現期: 1回/日 × 1日
        day = now - timedelta(days=1)
        svc.record_observation("topic_old", "mention", "x", day.isoformat())

        trends = svc.analyze_trends(period_days=7)
        old_trends = [t for t in trends if t.entity_id == "topic_old"]
        assert len(old_trends) == 1
        assert old_trends[0].direction == TrendDirection.FALLING

    # PURPOSE: 変化なしは STABLE
    def test_stable_trend(self, tmp_state_dir):
        svc = TemporalReasoningService(tmp_state_dir)
        now = datetime.now()

        # 前期・現期とも 2回/日
        for i in range(14):
            day = now - timedelta(days=i + 1)
            for _ in range(2):
                svc.record_observation("topic_stable", "mention", "x", day.isoformat())

        trends = svc.analyze_trends(period_days=7)
        stable = [t for t in trends if t.entity_id == "topic_stable"]
        assert len(stable) == 1
        assert stable[0].direction == TrendDirection.STABLE


class TestAnomalyDetection:
    """異常検出テスト"""

    # PURPOSE: 長期未観測は SILENCE
    def test_silence_detection(self, tmp_state_dir):
        svc = TemporalReasoningService(tmp_state_dir)
        # 20日前に最後の観測
        old_time = (datetime.now() - timedelta(days=20)).isoformat()
        svc.record_observation("forgotten", "mention", "x", old_time)

        anomalies = svc.detect_anomalies(silence_days=14)
        silence = [a for a in anomalies if a.anomaly_type == AnomalyType.SILENCE]
        assert len(silence) == 1
        assert silence[0].entity_id == "forgotten"
        assert silence[0].score >= 20.0

    # PURPOSE: 最近の観測は SILENCE にならない
    def test_no_silence_for_recent(self, tmp_state_dir):
        svc = TemporalReasoningService(tmp_state_dir)
        svc.record_observation("active", "mention", "x")

        anomalies = svc.detect_anomalies(silence_days=14)
        silence = [a for a in anomalies if a.anomaly_type == AnomalyType.SILENCE]
        assert len(silence) == 0


class TestMentionStats:
    """言及統計テスト"""

    # PURPOSE: 言及回数の変化率計算
    def test_mention_change_ratio(self, tmp_state_dir):
        svc = TemporalReasoningService(tmp_state_dir)
        now = datetime.now()

        # 前期: 5回
        for i in range(5):
            day = now - timedelta(days=10)
            svc.record_observation("paper_x", "cite", "y", day.isoformat())

        # 現期: 10回
        for i in range(10):
            day = now - timedelta(days=3)
            svc.record_observation("paper_x", "cite", "y", day.isoformat())

        mentions = svc.get_mention_changes(period_days=7)
        px = [m for m in mentions if m.entity_id == "paper_x"]
        assert len(px) == 1
        assert px[0].current_count == 10
        assert px[0].previous_count == 5
        assert px[0].change_ratio == 1.0  # (10-5)/5 = 1.0


class TestDecayedScores:
    """減衰スコア一括取得テスト"""

    # PURPOSE: 最近の観測はスコアが高い
    def test_recent_high_score(self, tmp_state_dir):
        svc = TemporalReasoningService(tmp_state_dir)
        svc.record_observation("recent", "x", "y")

        scores = svc.get_decayed_scores(["recent"])
        assert scores["recent"] > 0.9

    # PURPOSE: 古い観測はスコアが低い
    def test_old_low_score(self, tmp_state_dir):
        svc = TemporalReasoningService(tmp_state_dir)
        old = (datetime.now() - timedelta(days=30)).isoformat()
        svc.record_observation("ancient", "x", "y", old)

        scores = svc.get_decayed_scores(["ancient"])
        assert scores["ancient"] < 0.1

    # PURPOSE: 存在しないエンティティはスコア 0.0
    def test_unknown_entity(self, tmp_state_dir):
        svc = TemporalReasoningService(tmp_state_dir)
        scores = svc.get_decayed_scores(["nonexistent"])
        assert scores["nonexistent"] == 0.0


class TestGenerateSummary:
    """サマリ生成テスト"""

    # PURPOSE: 空の状態でもエラーにならない
    def test_empty_summary(self, tmp_state_dir):
        svc = TemporalReasoningService(tmp_state_dir)
        summary = svc.generate_summary()
        assert "時間的推論レポート" in summary
        assert "変化なし" in summary
