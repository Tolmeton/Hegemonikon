from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/pks/scheduler_service.py
# PURPOSE: 定期バックグラウンドジョブの統合管理サービス (P-02)
"""
SchedulerService — 定期バックグラウンドジョブ統合管理

FastAPI lifespan に統合され、複数のバックグラウンドジョブを一元管理する。
APScheduler は不要 — 既存の asyncio パターンを統合する設計。

Architecture:
    server.py _lifespan
        → SchedulerService.start()
            → asyncio.create_task(job_loop) × N
        → SchedulerService.stop()

Jobs:
    - gnosis_sync (6h): SyncWatcher.run_once() → 変更検出 + temporal 記録
    - health_check (1h): Peira hgk_health.run_health_check()
    - temporal_summary (24h): TemporalReasoningService.generate_summary()
"""


import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

logger = logging.getLogger("hegemonikon.scheduler")


@dataclass
class JobDefinition:
    """ジョブの定義"""
    name: str
    func: Callable[[], Any]
    interval_seconds: float
    run_at_start: bool = True
    description: str = ""


@dataclass
class JobState:
    """ジョブの実行状態"""
    name: str
    interval_seconds: float
    description: str = ""
    run_count: int = 0
    last_run: Optional[str] = None
    last_duration_sec: float = 0.0
    last_error: Optional[str] = None
    next_run: Optional[str] = None
    is_running: bool = False


class SchedulerService:
    """定期バックグラウンドジョブの統合管理サービス

    使い方:
        scheduler = SchedulerService()
        scheduler.register("health", check_health, interval_seconds=3600)
        await scheduler.start()
        ...
        await scheduler.stop()
    """

    # PURPOSE: 初期化
    def __init__(self) -> None:
        self._jobs: dict[str, JobDefinition] = {}
        self._states: dict[str, JobState] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._running = False
        self._start_time: Optional[float] = None

    # PURPOSE: ジョブを登録する
    def register(
        self,
        name: str,
        func: Callable[[], Any],
        interval_seconds: float,
        run_at_start: bool = True,
        description: str = "",
    ) -> None:
        """ジョブを登録する。start() の前に呼ぶ。"""
        if self._running:
            logger.warning("スケジューラ実行中にジョブを追加: %s", name)

        self._jobs[name] = JobDefinition(
            name=name,
            func=func,
            interval_seconds=interval_seconds,
            run_at_start=run_at_start,
            description=description,
        )
        self._states[name] = JobState(
            name=name,
            interval_seconds=interval_seconds,
            description=description,
        )
        logger.info("ジョブ登録: %s (間隔: %ds, 起動時実行: %s)",
                     name, int(interval_seconds), run_at_start)

    # PURPOSE: 全ジョブの非同期ループを開始する
    async def start(self) -> None:
        """全ジョブの非同期ループを開始する。"""
        if self._running:
            logger.warning("スケジューラは既に実行中")
            return

        self._running = True
        self._start_time = time.monotonic()
        logger.info("SchedulerService 起動: %d ジョブ", len(self._jobs))

        for name, job in self._jobs.items():
            task = asyncio.create_task(
                self._job_loop(job),
                name=f"scheduler-{name}",
            )
            self._tasks[name] = task

    # PURPOSE: 全ジョブを停止する
    async def stop(self) -> None:
        """全ジョブを停止する。"""
        self._running = False
        for name, task in self._tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                logger.info("ジョブ停止: %s", name)
        self._tasks.clear()
        logger.info("SchedulerService 停止")

    # PURPOSE: 全ジョブの状態を取得する (MCP 公開用)
    def get_status(self) -> dict:
        """全ジョブの状態を辞書で返す。"""
        uptime = 0.0
        if self._start_time:
            uptime = time.monotonic() - self._start_time

        return {
            "running": self._running,
            "uptime_seconds": round(uptime, 1),
            "job_count": len(self._jobs),
            "jobs": {
                name: {
                    "interval_seconds": state.interval_seconds,
                    "description": state.description,
                    "run_count": state.run_count,
                    "last_run": state.last_run,
                    "last_duration_sec": state.last_duration_sec,
                    "last_error": state.last_error,
                    "next_run": state.next_run,
                    "is_running": state.is_running,
                }
                for name, state in self._states.items()
            },
        }

    # PURPOSE: 個別ジョブの非同期ループ
    async def _job_loop(self, job: JobDefinition) -> None:
        """個別ジョブの非同期ループ。失敗しても止まらない。"""
        state = self._states[job.name]

        # 起動時実行
        if job.run_at_start:
            await self._execute_job(job, state)

        # 定期ループ
        while self._running:
            # 次の実行時刻を計算
            next_dt = datetime.now()
            from datetime import timedelta
            next_dt = next_dt + timedelta(seconds=job.interval_seconds)
            state.next_run = next_dt.strftime("%Y-%m-%d %H:%M:%S")

            try:
                await asyncio.sleep(job.interval_seconds)
            except asyncio.CancelledError:
                break

            if not self._running:
                break

            await self._execute_job(job, state)

    # PURPOSE: ジョブを1回実行する (asyncio.to_thread でブロッキングを回避)
    async def _execute_job(self, job: JobDefinition, state: JobState) -> None:
        """ジョブを1回実行する。例外は記録するが伝搬しない。"""
        state.is_running = True
        start = time.monotonic()

        try:
            logger.info("ジョブ実行開始: %s", job.name)
            # ブロッキング関数は asyncio.to_thread でオフロード
            result = await asyncio.to_thread(job.func)
            elapsed = time.monotonic() - start

            state.run_count += 1
            state.last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            state.last_duration_sec = round(elapsed, 2)
            state.last_error = None

            logger.info("ジョブ完了: %s (%.1fs)", job.name, elapsed)
        except Exception as e:  # noqa: BLE001
            elapsed = time.monotonic() - start
            state.run_count += 1
            state.last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            state.last_duration_sec = round(elapsed, 2)
            state.last_error = str(e)

            logger.error("ジョブ失敗: %s — %s (%.1fs)", job.name, e, elapsed)
        finally:
            state.is_running = False


# ── ジョブ関数定義 ─────────────────────────────────────────


# PURPOSE: Gnōsis 変更検出ジョブ (SyncWatcher.run_once)
def job_gnosis_sync() -> dict:
    """SyncWatcher.run_once() で Gnōsis の変更を検出し temporal に記録。"""
    from pathlib import Path
    from mekhane.paths import GNOSIS_DIR

    # SyncWatcher 初期化 — state は ~/.hegemonikon/sync/ に保持
    state_dir = Path.home() / ".hegemonikon" / "sync"
    state_dir.mkdir(parents=True, exist_ok=True)

    try:
        from mekhane.pks.sync_watcher import SyncWatcher
        watcher = SyncWatcher(
            watch_dirs=[str(GNOSIS_DIR)],
            state_path=str(state_dir / "gnosis_sync_state.json"),
        )
        result = watcher.run_once()
        logger.info("gnosis_sync: %s", result)
        return result or {}
    except Exception as e:  # noqa: BLE001
        logger.warning("gnosis_sync: %s (非致死)", e)
        return {"error": str(e)}


# PURPOSE: Peira ヘルスチェックジョブ
def job_health_check() -> dict:
    """Peira hgk_health.run_health_check() を実行し結果を永続化。"""
    import json
    from pathlib import Path
    from dataclasses import asdict

    try:
        from mekhane.peira.hgk_health import run_health_check
        report = run_health_check()

        # JSON 永続化
        health_dir = Path.home() / ".hegemonikon" / "health"
        health_dir.mkdir(parents=True, exist_ok=True)
        out = health_dir / "latest.json"
        out.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2))

        logger.info("health_check: score=%.2f (%d items)",
                     report.score, len(report.items))
        return {"score": report.score, "items": len(report.items)}
    except Exception as e:  # noqa: BLE001
        logger.warning("health_check: %s (非致死)", e)
        return {"error": str(e)}


# PURPOSE: Temporal サマリージョブ
def job_temporal_summary() -> dict:
    """TemporalReasoningService.generate_summary() を実行。"""
    try:
        from pathlib import Path
        state_dir = Path.home() / ".hegemonikon" / "temporal"
        from mekhane.pks.temporal import TemporalReasoningService
        svc = TemporalReasoningService(state_dir=state_dir)
        summary = svc.generate_summary()
        logger.info("temporal_summary: %s", summary.get("total_entities", 0))
        return summary
    except Exception as e:  # noqa: BLE001
        logger.warning("temporal_summary: %s (非致死)", e)
        return {"error": str(e)}


# ── ファクトリ ─────────────────────────────────────────────


# PURPOSE: デフォルトの SchedulerService を生成する
def create_default_scheduler() -> SchedulerService:
    """デフォルトの3ジョブを登録した SchedulerService を返す。"""
    svc = SchedulerService()

    svc.register(
        name="gnosis_sync",
        func=job_gnosis_sync,
        interval_seconds=6 * 3600,  # 6時間
        run_at_start=True,
        description="Gnōsis 変更検出 + temporal 記録",
    )

    svc.register(
        name="health_check",
        func=job_health_check,
        interval_seconds=3600,  # 1時間
        run_at_start=True,
        description="Peira ヘルスチェック",
    )

    svc.register(
        name="temporal_summary",
        func=job_temporal_summary,
        interval_seconds=24 * 3600,  # 24時間
        run_at_start=False,
        description="Temporal サマリー生成",
    )

    return svc
