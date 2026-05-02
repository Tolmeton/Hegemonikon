#!/usr/bin/env python3
# PROOF: [L2/テスト] <- mekhane/scripts/tests/
# PURPOSE: Scheduler State (ClawX Cron Adjunction) のユニットテスト
"""
Scheduler State tests — ClawX Cron Adjunction

scheduler_models.py + scheduler_state.py の検証:
- データモデルの serialization roundtrip
- 状態永続化 (write + read)
- trigger 後の state 更新
- 全ジョブマージ (known_jobs + state.json)
"""

import json
from pathlib import Path

import pytest

from mekhane.scripts.scheduler_models import (
    CronJobState,
    DeliveryMode,
    SchedulerJob,
)
from mekhane.scripts.scheduler_state import SchedulerStateStore


# ── CronJobState テスト ──────────────────────────────

class TestCronJobState:
    """CronJobState の serialization と record_run のテスト。"""

    def test_default_state(self):
        """デフォルト状態 → 全フィールドが None/True。"""
        state = CronJobState()
        assert state.last_run is None
        assert state.last_success is True
        assert state.last_error is None
        assert state.last_duration_sec is None

    def test_roundtrip(self):
        """to_dict → from_dict で情報が保存される。"""
        state = CronJobState(
            last_run="2026-03-07T22:00:00",
            last_success=False,
            last_error="connection timeout",
            last_duration_sec=45.2,
            next_run="2026-03-08T04:00:00",
        )
        d = state.to_dict()
        restored = CronJobState.from_dict(d)
        assert restored.last_run == state.last_run
        assert restored.last_success == state.last_success
        assert restored.last_error == state.last_error
        assert restored.last_duration_sec == state.last_duration_sec
        assert restored.next_run == state.next_run

    def test_record_run(self):
        """record_run で last_run/success/error/duration が更新される。"""
        state = CronJobState()
        state.record_run(success=False, error="oops", duration_sec=1.5)
        assert state.last_run is not None
        assert state.last_success is False
        assert state.last_error == "oops"
        assert state.last_duration_sec == 1.5


# ── SchedulerJob テスト ──────────────────────────────

class TestSchedulerJob:
    """SchedulerJob の serialization テスト。"""

    def test_roundtrip(self):
        """to_dict → from_dict で情報が保存される。"""
        job = SchedulerJob(
            id="test_job",
            name="Test Job",
            schedule="0 4 * * *",
            command="echo hello",
            enabled=True,
            delivery=DeliveryMode.N8N,
        )
        d = job.to_dict()
        restored = SchedulerJob.from_dict(d)
        assert restored.id == job.id
        assert restored.name == job.name
        assert restored.schedule == job.schedule
        assert restored.delivery == DeliveryMode.N8N

    def test_delivery_mode_enum(self):
        """DeliveryMode enum が正しくシリアライズされる。"""
        for mode in DeliveryMode:
            job = SchedulerJob(
                id="x", name="x", schedule="*", command="x",
                delivery=mode,
            )
            d = job.to_dict()
            assert d["delivery"] == mode.value
            restored = SchedulerJob.from_dict(d)
            assert restored.delivery == mode


# ── SchedulerStateStore テスト ──────────────────────────

class TestSchedulerStateStore:
    """SchedulerStateStore の永続化とマージのテスト。"""

    def test_state_roundtrip(self, tmp_path: Path):
        """状態の書き込み+読み込みが正しい。"""
        store = SchedulerStateStore(state_path=tmp_path / "state.json")
        result = store.update_job_state(
            job_id="test",
            success=True,
            duration_sec=2.5,
        )
        assert result.last_success is True
        assert result.last_duration_sec == 2.5

        # 別のインスタンスから読み直し
        store2 = SchedulerStateStore(state_path=tmp_path / "state.json")
        state = store2.get_job_state("test")
        assert state.last_success is True
        assert state.last_duration_sec == 2.5

    def test_get_all_jobs_merges_state(self, tmp_path: Path):
        """known_jobs と state.json がマージされる。"""
        store = SchedulerStateStore(state_path=tmp_path / "state.json")

        # swarm_daily の状態を記録
        store.update_job_state("swarm_daily", success=True, duration_sec=120.0)

        # 全ジョブ取得
        jobs = store.get_all_jobs()
        assert len(jobs) >= 2  # swarm_daily + digestor

        swarm = next(j for j in jobs if j.id == "swarm_daily")
        assert swarm.state.last_success is True
        assert swarm.state.last_duration_sec == 120.0

    def test_set_job_enabled(self, tmp_path: Path):
        """enable/disable の永続化。"""
        store = SchedulerStateStore(state_path=tmp_path / "state.json")
        store.set_job_enabled("swarm_daily", False)

        # ファイルから直接読んで確認
        data = json.loads((tmp_path / "state.json").read_text())
        assert data["jobs"]["swarm_daily"]["enabled"] is False

    def test_trigger_unknown_job(self, tmp_path: Path):
        """存在しないジョブの trigger → ValueError。"""
        store = SchedulerStateStore(state_path=tmp_path / "state.json")
        with pytest.raises(ValueError, match="Unknown job"):
            store.trigger_job("nonexistent")

    def test_trigger_job_records_state(self, tmp_path: Path):
        """trigger後に state が更新される (echo は即成功する)。"""
        # カスタムの known_jobs を使ってテスト
        store = SchedulerStateStore(state_path=tmp_path / "state.json")

        # 一時的に known_jobs を上書き
        original = SchedulerStateStore.get_known_jobs
        SchedulerStateStore.get_known_jobs = staticmethod(lambda: [
            SchedulerJob(
                id="echo_test",
                name="Echo Test",
                schedule="* * * * *",
                command="echo hello",
            ),
        ])

        try:
            result = store.trigger_job("echo_test")
            assert result.last_success is True
            assert result.last_duration_sec is not None
            assert result.last_duration_sec < 5.0  # echo should be fast
        finally:
            SchedulerStateStore.get_known_jobs = original
