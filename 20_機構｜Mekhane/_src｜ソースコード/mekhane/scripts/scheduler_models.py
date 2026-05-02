from __future__ import annotations
# PROOF: [L2/データモデル] <- mekhane/scripts/scheduler_models.py O4→スケジューラジョブの型定義が必要→scheduler_models が担う
"""
Scheduler Data Models — ClawX Cron Adjunction

CronJobState + SchedulerJob: ClawX の CronJob/CronSchedule/CronJobLastRun を
HGK の Python 文脈に翻訳したデータモデル。

ClawX 対応マップ:
  CronJobState    ← CronJobLastRun + CronJob.nextRun
  SchedulerJob    ← CronJob + GatewayCronJob
  DeliveryMode    ← GatewayCronJob.delivery.mode
"""


from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any


# PURPOSE: 結果配信先 — ClawX の delivery.mode に対応
class DeliveryMode(str, Enum):
    """Job result delivery target."""
    STDOUT = "stdout"       # ログ出力のみ (デフォルト)
    N8N = "n8n"             # n8n webhook 経由
    HGK_APP = "hgk-app"    # hgk-app GUI 経由 (将来)


# PURPOSE: ジョブ実行状態 — ClawX の CronJobLastRun + state に対応
@dataclass
class CronJobState:
    """Runtime state of a scheduled job.

    ClawX mapping:
      last_run       ← GatewayCronJob.state.lastRunAtMs
      last_success   ← GatewayCronJob.state.lastStatus == 'ok'
      last_error     ← GatewayCronJob.state.lastError
      last_duration  ← GatewayCronJob.state.lastDurationMs (秒に変換)
      next_run       ← GatewayCronJob.state.nextRunAtMs
    """
    last_run: str | None = None           # ISO 8601
    last_success: bool = True
    last_error: str | None = None
    last_duration_sec: float | None = None
    next_run: str | None = None           # ISO 8601

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CronJobState:
        """Deserialize from dict."""
        return cls(
            last_run=data.get("last_run"),
            last_success=data.get("last_success", True),
            last_error=data.get("last_error"),
            last_duration_sec=data.get("last_duration_sec"),
            next_run=data.get("next_run"),
        )

    def record_run(self, success: bool, error: str | None = None,
                   duration_sec: float | None = None) -> None:
        """Record a completed run."""
        self.last_run = datetime.now().isoformat()
        self.last_success = success
        self.last_error = error
        self.last_duration_sec = duration_sec


# PURPOSE: スケジューラジョブ定義 — ClawX の CronJob + GatewayCronJob に対応
@dataclass
class SchedulerJob:
    """A scheduled job definition with runtime state.

    ClawX mapping:
      id         ← CronJob.id
      name       ← CronJob.name
      schedule   ← CronSchedule (cron 式のみ, at/every は未対応)
      command    ← GatewayCronJob.payload (HGK では直接コマンド)
      enabled    ← CronJob.enabled
      delivery   ← GatewayCronJob.delivery.mode
      state      ← GatewayCronJob.state (→ CronJobState)
      created_at ← CronJob.createdAt
      updated_at ← CronJob.updatedAt
    """
    id: str
    name: str
    schedule: str                               # cron 式 (e.g. "0 19 * * *")
    command: str                                # 実行コマンド
    enabled: bool = True
    delivery: DeliveryMode = DeliveryMode.STDOUT
    state: CronJobState = field(default_factory=CronJobState)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON/API response."""
        return {
            "id": self.id,
            "name": self.name,
            "schedule": self.schedule,
            "command": self.command,
            "enabled": self.enabled,
            "delivery": self.delivery.value,
            "state": self.state.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SchedulerJob:
        """Deserialize from dict."""
        state_data = data.get("state", {})
        return cls(
            id=data["id"],
            name=data["name"],
            schedule=data["schedule"],
            command=data["command"],
            enabled=data.get("enabled", True),
            delivery=DeliveryMode(data.get("delivery", "stdout")),
            state=CronJobState.from_dict(state_data) if state_data else CronJobState(),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )
