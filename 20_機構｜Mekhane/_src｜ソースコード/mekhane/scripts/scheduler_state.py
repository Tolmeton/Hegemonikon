from __future__ import annotations
# PROOF: [L2/状態管理] <- mekhane/scripts/scheduler_state.py O4→ジョブ状態永続化が必要→scheduler_state が担う
"""
Scheduler State Store — ClawX Cron Adjunction

JSON ファイルベースの状態永続化。crontab (ジョブ定義) と state.json (実行履歴) を
マージして SchedulerJob のリストを返す。

ClawX 対応: skill-config.ts の readConfig/writeConfig パターンを Python に翻訳。
  - ClawX: ~/.openclaw/openclaw.json
  - HGK:   ~/.hgk/scheduler_state.json
"""


import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from mekhane.scripts.scheduler_models import (
    CronJobState,
    DeliveryMode,
    SchedulerJob,
)

logger = logging.getLogger(__name__)

# PURPOSE: デフォルト状態ファイルパス
DEFAULT_STATE_PATH = Path.home() / ".hgk" / "scheduler_state.json"


# PURPOSE: ジョブ状態の永続化と crontab とのマージ
class SchedulerStateStore:
    """JSON file-based scheduler state store.

    ClawX pattern: skill-config.ts の readConfig/writeConfig を参考に、
    非同期 I/O ではなく同期ファイル I/O を使用 (Python CLI スクリプトのため)。
    """

    def __init__(self, state_path: Path | None = None):
        self.state_path = state_path or DEFAULT_STATE_PATH
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    # ── 読み書き ──────────────────────────────────────

    # PURPOSE: 状態ファイルの読み込み
    def _read_state(self) -> dict[str, Any]:
        """Read state from JSON file."""
        if not self.state_path.exists():
            return {"jobs": {}, "version": "1.0"}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read scheduler state: %s", exc)
            return {"jobs": {}, "version": "1.0"}

    # PURPOSE: 状態ファイルへの書き込み
    def _write_state(self, state: dict[str, Any]) -> None:
        """Write state to JSON file (atomic via temp + rename)."""
        tmp_path = self.state_path.with_suffix(".tmp")
        try:
            tmp_path.write_text(
                json.dumps(state, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            tmp_path.replace(self.state_path)
        except OSError as exc:
            logger.error("Failed to write scheduler state: %s", exc)
            raise

    # ── ジョブ状態操作 ──────────────────────────────────

    # PURPOSE: 実行完了を記録 — ClawX の transformCronJob の lastRun 更新に対応
    def update_job_state(
        self,
        job_id: str,
        success: bool,
        error: str | None = None,
        duration_sec: float | None = None,
    ) -> CronJobState:
        """Record a job execution result."""
        state = self._read_state()
        jobs = state.setdefault("jobs", {})
        job_state = CronJobState.from_dict(jobs.get(job_id, {}))
        job_state.record_run(success=success, error=error, duration_sec=duration_sec)
        jobs[job_id] = job_state.to_dict()
        self._write_state(state)
        return job_state

    # PURPOSE: 特定ジョブの状態を取得
    def get_job_state(self, job_id: str) -> CronJobState:
        """Get state for a specific job."""
        state = self._read_state()
        job_data = state.get("jobs", {}).get(job_id, {})
        return CronJobState.from_dict(job_data)

    # ── 全ジョブ一覧 (crontab マージ) ──────────────────

    # PURPOSE: 登録済みジョブ定義 — crontab 解析は行わず、既知のジョブを返す
    @staticmethod
    def get_known_jobs() -> list[SchedulerJob]:
        """Return well-known HGK scheduler jobs.

        crontab のパースは脆弱なため、既知のジョブを静的に定義する。
        将来: YAML 設定ファイルから読み込む。
        """
        return [
            SchedulerJob(
                id="swarm_daily",
                name="Swarm Daily (4AM JST)",
                schedule="0 19 * * *",  # 4:00 JST = 19:00 UTC
                command="python swarm_scheduler.py --run",
                delivery=DeliveryMode.STDOUT,
            ),
            SchedulerJob(
                id="digestor",
                name="Digestor Pipeline",
                schedule="0 */6 * * *",
                command="python -m mekhane.ergasterion.digestor.scheduler",
                delivery=DeliveryMode.STDOUT,
            ),
        ]

    # PURPOSE: 全ジョブ + 状態をマージして返す — ClawX の fetchSkills 3層マージに対応
    def get_all_jobs(self) -> list[SchedulerJob]:
        """Merge known jobs with persisted state.

        ClawX pattern: stores/skills.ts の fetchSkills() が
        Gateway + ClawHub + Config を 3 層マージするのに対応。
        HGK: known_jobs (定義) + state.json (実行履歴) を 2 層マージ。
        """
        jobs = self.get_known_jobs()
        state = self._read_state()
        state_jobs = state.get("jobs", {})

        for job in jobs:
            if job.id in state_jobs:
                job.state = CronJobState.from_dict(state_jobs[job.id])

        return jobs

    # PURPOSE: ジョブの enable/disable 切替
    def set_job_enabled(self, job_id: str, enabled: bool) -> None:
        """Toggle job enabled state."""
        state = self._read_state()
        jobs = state.setdefault("jobs", {})
        job_data = jobs.setdefault(job_id, {})
        job_data["enabled"] = enabled
        job_data["updated_at"] = datetime.now().isoformat()
        self._write_state(state)

    # ── 手動トリガー ──────────────────────────────────

    # PURPOSE: ジョブの手動実行 — ClawX の cron:trigger → cron.run {force} に対応
    def trigger_job(self, job_id: str) -> CronJobState:
        """Manually trigger a job and record the result.

        ClawX mapping: ipcMain.handle('cron:trigger') →
          gatewayManager.rpc('cron.run', { id, mode: 'force' })
        """
        jobs = {j.id: j for j in self.get_known_jobs()}
        if job_id not in jobs:
            raise ValueError(f"Unknown job: {job_id}")

        job = jobs[job_id]
        logger.info("Manually triggering job: %s (%s)", job.name, job.command)

        start = time.monotonic()
        try:
            result = subprocess.run(
                job.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour max
            )
            duration = time.monotonic() - start
            success = result.returncode == 0
            error = result.stderr.strip() if not success else None

            if success:
                logger.info("Job %s completed in %.1fs", job_id, duration)
            else:
                logger.error("Job %s failed (exit %d): %s",
                             job_id, result.returncode, error)

            return self.update_job_state(
                job_id=job_id,
                success=success,
                error=error,
                duration_sec=round(float(duration), 2),
            )
        except subprocess.TimeoutExpired:
            duration = time.monotonic() - start
            logger.error("Job %s timed out after %.1fs", job_id, duration)
            return self.update_job_state(
                job_id=job_id,
                success=False,
                error="Timeout after 1 hour",
                duration_sec=round(float(duration), 2),
            )
        except Exception as exc:  # noqa: BLE001
            duration = time.monotonic() - start
            logger.error("Job %s error: %s", job_id, exc)
            return self.update_job_state(
                job_id=job_id,
                success=False,
                error=str(exc),
                duration_sec=round(float(duration), 2),
            )
