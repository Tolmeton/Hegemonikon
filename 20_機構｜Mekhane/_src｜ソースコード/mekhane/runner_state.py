# PROOF: [L2/インフラ] <- mekhane/runner_state.py A0→状態マシンenum標準化
# PURPOSE: Hermēneus/Phantazein の WF 実行状態を統一するステートマシン定義。
#          MiroFish simulation_runner.py L30-50 の RunnerStatus enum をHGK用に再構成。
#          Mimēsis 随伴 D5: 状態マシン enum 標準化。
"""WF 実行状態の統一 enum。

MiroFish の RunnerStatus (IDLE→STARTING→RUNNING→STOPPING→COMPLETED→FAILED→PAUSED)
を HGK の WF 実行ライフサイクルに適合させた。

使用箇所:
- Hermēneus WF executor: ステップの実行状態
- Phantazein session state: セッション全体の状態
- Poiema incremental writer: レポート生成の進捗状態
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class RunnerState(Enum):
    """WF/タスク実行の状態遷移 enum。

    状態遷移図:
        IDLE → STARTING → RUNNING → COMPLETED
                           ↓
                         PAUSED → RUNNING (再開)
                           ↓
                         STOPPING → COMPLETED | FAILED
                           ↓
                         FAILED

    MiroFish 由来 (simulation_runner.py L30-50) を HGK 用にリファクタ。
    """
    # 初期状態
    IDLE = auto()

    # 実行準備中 (リソース確保, 検証)
    STARTING = auto()

    # 実行中
    RUNNING = auto()

    # 一時停止 (Creator の介入待ち等)
    PAUSED = auto()

    # 停止処理中 (クリーンアップ)
    STOPPING = auto()

    # 正常完了
    COMPLETED = auto()

    # 異常終了
    FAILED = auto()

    # キャンセル (Creator による中断)
    CANCELLED = auto()

    @property
    def is_terminal(self) -> bool:
        """終端状態 (COMPLETED, FAILED, CANCELLED) かどうか。"""
        return self in (RunnerState.COMPLETED, RunnerState.FAILED, RunnerState.CANCELLED)

    @property
    def is_active(self) -> bool:
        """実行中の状態 (STARTING, RUNNING, PAUSED, STOPPING) かどうか。"""
        return self in (
            RunnerState.STARTING,
            RunnerState.RUNNING,
            RunnerState.PAUSED,
            RunnerState.STOPPING,
        )


@dataclass
class Progress:
    """タスク進捗のリアルタイム追跡。

    MiroFish の progress.json パターン (report_agent.py L2199-2226) を
    dataclass として構造化。

    使用例:
        progress = Progress(total_steps=5, current_step=2, message="セクション生成中")
        print(progress.percent)  # 40.0
    """
    total_steps: int = 0
    current_step: int = 0
    message: str = ""
    status: str = "pending"  # pending / running / completed / failed
    current_section: str = ""
    completed_sections: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def percent(self) -> float:
        """進捗率 (0.0-100.0)。"""
        if self.total_steps <= 0:
            return 0.0
        return min(100.0, (self.current_step / self.total_steps) * 100)

    def advance(self, message: str = "", section: str = "") -> None:
        """1ステップ進める。"""
        self.current_step = min(self.current_step + 1, self.total_steps)
        self.updated_at = datetime.now(timezone.utc)
        # 初回 advance で running に自動遷移
        if self.status == "pending":
            self.status = "running"
        # 全ステップ完了で completed に自動遷移
        if self.current_step >= self.total_steps:
            self.status = "completed"
        if message:
            self.message = message
        if section:
            if self.current_section and self.current_section not in self.completed_sections:
                self.completed_sections.append(self.current_section)
            self.current_section = section

    def fail(self, message: str = "") -> None:
        """タスクを失敗状態に遷移する。"""
        self.status = "failed"
        self.updated_at = datetime.now(timezone.utc)
        if message:
            self.message = message

    def to_dict(self) -> dict[str, Any]:
        """JSON シリアル化可能な辞書を返す。"""
        return {
            "status": self.status,
            "progress": self.percent,
            "message": self.message,
            "current_section": self.current_section,
            "completed_sections": self.completed_sections,
            "total_steps": self.total_steps,
            "current_step": self.current_step,
            "started_at": self.started_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
