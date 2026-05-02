# PROOF: mekhane/agent_guard/session_lock.py
# PURPOSE: agent_guard モジュールの session_lock
"""
Session Write Lock (T-15)

セッションファイルへの排他書き込みロック。
OpenClaw の session-write-lock.ts を Python に移植。

Features:
- O_EXCL ベースのファイルロック
- PID tracking + stale 検出 (dead PID / too old)
- Re-entrant counting
- Watchdog (max hold enforcement)
- Signal handler cleanup
- async context manager
"""
import asyncio
import json
import os
import signal
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional

# Constants (OpenClaw defaults)
DEFAULT_STALE_MS = 30 * 60 * 1000  # 30 minutes
DEFAULT_MAX_HOLD_S = 5 * 60  # 5 minutes
DEFAULT_TIMEOUT_S = 10  # 10 seconds
DEFAULT_WATCHDOG_INTERVAL_S = 60  # 60 seconds
MAX_LOCK_HOLD_S = 2_147  # ~35 minutes (safe int range for timers)


@dataclass
class LockPayload:
    pid: Optional[int] = None
    created_at: Optional[str] = None


@dataclass
class LockInspection:
    lock_path: str
    pid: Optional[int] = None
    pid_alive: bool = False
    created_at: Optional[str] = None
    age_s: Optional[float] = None
    stale: bool = False
    stale_reasons: list = field(default_factory=list)
    removed: bool = False


@dataclass
class HeldLock:
    count: int = 1
    lock_path: str = ""
    acquired_at: float = 0.0
    max_hold_s: float = DEFAULT_MAX_HOLD_S


# Process-global state
_held_locks: Dict[str, HeldLock] = {}
_cleanup_registered: bool = False
_watchdog_task: Optional[asyncio.Task] = None


def _is_pid_alive(pid: int) -> bool:
    """PID が生きているか確認"""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _read_lock_payload(lock_path: str) -> Optional[LockPayload]:
    """ロックファイルのペイロードを読み取る"""
    try:
        with open(lock_path, "r") as f:
            data = json.load(f)
        payload = LockPayload()
        if isinstance(data.get("pid"), int):
            payload.pid = data["pid"]
        if isinstance(data.get("created_at"), str):
            payload.created_at = data["created_at"]
        return payload
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        return None


def _inspect_lock(payload: Optional[LockPayload], stale_s: float, now: float) -> LockInspection:
    """ロックファイルの状態を検査"""
    inspection = LockInspection(lock_path="")
    
    if payload:
        inspection.pid = payload.pid
        inspection.created_at = payload.created_at
    
    pid = inspection.pid
    inspection.pid_alive = _is_pid_alive(pid) if pid is not None else False
    
    stale_reasons = []
    
    if pid is None:
        stale_reasons.append("missing-pid")
    elif not inspection.pid_alive:
        stale_reasons.append("dead-pid")
    
    if inspection.created_at:
        try:
            from datetime import datetime, timezone
            created_dt = datetime.fromisoformat(inspection.created_at)
            age_s = now - created_dt.timestamp()
            inspection.age_s = max(0.0, age_s)
            if inspection.age_s > stale_s:
                stale_reasons.append("too-old")
        except (ValueError, TypeError):
            stale_reasons.append("invalid-created_at")
    else:
        stale_reasons.append("invalid-created_at")
    
    inspection.stale = len(stale_reasons) > 0
    inspection.stale_reasons = stale_reasons
    
    return inspection


def _should_reclaim(lock_path: str, inspection: LockInspection, stale_s: float) -> bool:
    """ロックを回収すべきか判定"""
    if not inspection.stale:
        return False
    
    # PID死亡 or too-old は即回収
    if any(r in ("dead-pid", "too-old") for r in inspection.stale_reasons):
        return True
    
    # missing-pid + invalid-created_at だけの場合、mtime で判定
    if all(r in ("missing-pid", "invalid-created_at") for r in inspection.stale_reasons):
        try:
            stat = os.stat(lock_path)
            age_s = time.time() - stat.st_mtime
            return age_s > stale_s
        except FileNotFoundError:
            return False
        except OSError:
            return True
    
    return True


def _release_lock_sync(session_file: str) -> bool:
    """ロックを同期的に解放 (exit handler 用)"""
    held = _held_locks.pop(session_file, None)
    if held is None:
        return False
    
    try:
        os.unlink(held.lock_path)
    except (FileNotFoundError, OSError):
        pass
    return True


def _release_all_locks_sync() -> None:
    """全ロックを同期的に解放"""
    for session_file in list(_held_locks.keys()):
        _release_lock_sync(session_file)


def _register_cleanup() -> None:
    global _cleanup_registered
    if _cleanup_registered:
        return
    _cleanup_registered = True
    
    import atexit
    atexit.register(_release_all_locks_sync)


async def _watchdog_loop(interval_s: float = DEFAULT_WATCHDOG_INTERVAL_S) -> None:
    """max hold 超過ロックを自動解放する watchdog"""
    while True:
        await asyncio.sleep(interval_s)
        now = time.time()
        for session_file in list(_held_locks.keys()):
            held = _held_locks.get(session_file)
            if held is None:
                continue
            held_for_s = now - held.acquired_at
            if held_for_s > held.max_hold_s:
                _release_lock_sync(session_file)


def _ensure_watchdog_started() -> None:
    global _watchdog_task
    if _watchdog_task is not None and not _watchdog_task.done():
        return
    
    try:
        loop = asyncio.get_running_loop()
        _watchdog_task = loop.create_task(_watchdog_loop())
    except RuntimeError:
        pass  # No running loop — will start on first acquire


async def acquire_session_write_lock(
    session_file: str,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    stale_s: float = DEFAULT_STALE_MS / 1000,
    max_hold_s: float = DEFAULT_MAX_HOLD_S,
    allow_reentrant: bool = True,
) -> "SessionWriteLock":
    """セッションファイルの排他ロックを取得"""
    _register_cleanup()
    _ensure_watchdog_started()
    
    session_file = os.path.realpath(session_file)
    session_dir = os.path.dirname(session_file)
    os.makedirs(session_dir, exist_ok=True)
    lock_path = f"{session_file}.lock"
    
    # Re-entrant check
    held = _held_locks.get(session_file)
    if allow_reentrant and held:
        held.count += 1
        return SessionWriteLock(session_file=session_file, held=held)
    
    started_at = time.time()
    attempt = 0
    
    while time.time() - started_at < timeout_s:
        attempt += 1
        
        try:
            # O_EXCL: アトミックに新規作成 (既存なら失敗)
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                from datetime import datetime, timezone
                created_at = datetime.now(timezone.utc).isoformat()
                payload = json.dumps({"pid": os.getpid(), "created_at": created_at}, indent=2)
                os.write(fd, payload.encode("utf-8"))
            finally:
                os.close(fd)
            
            new_held = HeldLock(
                count=1,
                lock_path=lock_path,
                acquired_at=time.time(),
                max_hold_s=max_hold_s,
            )
            _held_locks[session_file] = new_held
            return SessionWriteLock(session_file=session_file, held=new_held)
            
        except FileExistsError:
            # ロックが既に存在 → stale check
            existing_payload = _read_lock_payload(lock_path)
            inspection = _inspect_lock(existing_payload, stale_s, time.time())
            inspection.lock_path = lock_path
            
            if _should_reclaim(lock_path, inspection, stale_s):
                try:
                    os.unlink(lock_path)
                except (FileNotFoundError, OSError):
                    pass
                continue  # 次の試行
            
            # 待機
            delay = min(1.0, 0.05 * attempt)
            await asyncio.sleep(delay)

    # タイムアウト
    existing_payload = _read_lock_payload(lock_path)
    owner = f"pid={existing_payload.pid}" if existing_payload and existing_payload.pid else "unknown"
    raise TimeoutError(f"session file locked (timeout {timeout_s}s): {owner} {lock_path}")


class SessionWriteLock:
    """セッション排他ロック。async context manager として使用"""
    
    def __init__(self, session_file: str, held: HeldLock):
        self._session_file = session_file
        self._held = held
    
    @property
    def lock_path(self) -> str:
        return self._held.lock_path
    
    @property
    def session_file(self) -> str:
        return self._session_file
    
    async def release(self) -> bool:
        """ロックを解放"""
        held = _held_locks.get(self._session_file)
        if held is not self._held:
            return False
        
        self._held.count -= 1
        if self._held.count > 0:
            return False  # Re-entrant: まだ他の参照がある
        
        _held_locks.pop(self._session_file, None)
        try:
            os.unlink(self._held.lock_path)
        except (FileNotFoundError, OSError):
            pass
        return True
    
    async def __aenter__(self) -> "SessionWriteLock":
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.release()


@asynccontextmanager
async def session_write_lock(
    session_file: str,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    stale_s: float = DEFAULT_STALE_MS / 1000,
    max_hold_s: float = DEFAULT_MAX_HOLD_S,
) -> AsyncIterator[SessionWriteLock]:
    """Convenience context manager for session write lock"""
    lock = await acquire_session_write_lock(
        session_file=session_file,
        timeout_s=timeout_s,
        stale_s=stale_s,
        max_hold_s=max_hold_s,
    )
    try:
        yield lock
    finally:
        await lock.release()


def clean_stale_locks(
    sessions_dir: str,
    stale_s: float = DEFAULT_STALE_MS / 1000,
    remove: bool = True,
) -> list[LockInspection]:
    """stale ロックファイルを検査・削除"""
    results = []
    sessions_path = Path(sessions_dir)
    
    if not sessions_path.exists():
        return results
    
    for lock_file in sorted(sessions_path.glob("*.lock")):
        lock_path = str(lock_file)
        payload = _read_lock_payload(lock_path)
        inspection = _inspect_lock(payload, stale_s, time.time())
        inspection.lock_path = lock_path
        
        if inspection.stale and remove:
            try:
                os.unlink(lock_path)
                inspection.removed = True
            except (FileNotFoundError, OSError):
                pass
        
        results.append(inspection)
    
    return results


# テスト用エクスポート
__testing = {
    "release_all_locks_sync": _release_all_locks_sync,
    "held_locks": _held_locks,
    "is_pid_alive": _is_pid_alive,
}
