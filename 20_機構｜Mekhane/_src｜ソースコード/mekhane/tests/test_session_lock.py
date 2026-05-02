# PROOF: mekhane/tests/test_session_lock.py
# PURPOSE: tests モジュールの session_lock に対するテスト
"""
AGENT GUARD モジュールのテスト — Session Write Lock (T-15)
"""
import asyncio
import json
import os
import time
from pathlib import Path

import pytest

from mekhane.agent_guard.session_lock import (
    LockInspection,
    SessionWriteLock,
    _held_locks,
    _inspect_lock,
    _is_pid_alive,
    _read_lock_payload,
    _release_all_locks_sync,
    acquire_session_write_lock,
    clean_stale_locks,
    session_write_lock,
    LockPayload,
)


@pytest.fixture(autouse=True)
def _clear_held_locks():
    """テスト間で held locks をクリア"""
    _held_locks.clear()
    yield
    _release_all_locks_sync()


@pytest.mark.asyncio
async def test_acquire_and_release(tmp_path: Path):
    session_file = str(tmp_path / "test_session.jsonl")
    lock = await acquire_session_write_lock(session_file, timeout_s=2)
    lock_path = lock.lock_path
    
    # ロックファイルが存在する
    assert os.path.exists(lock_path)
    
    # ペイロードにPIDが書かれている
    with open(lock_path) as f:
        data = json.load(f)
    assert data["pid"] == os.getpid()
    assert "created_at" in data
    
    # 解放
    released = await lock.release()
    assert released
    assert not os.path.exists(lock_path)


@pytest.mark.asyncio
async def test_reentrant_lock(tmp_path: Path):
    session_file = str(tmp_path / "reentrant.jsonl")
    
    lock1 = await acquire_session_write_lock(session_file, timeout_s=2)
    lock2 = await acquire_session_write_lock(session_file, timeout_s=2, allow_reentrant=True)
    
    # lock2 解放 → まだロックファイルは残る (count=1)
    released = await lock2.release()
    assert not released  # count > 0 → not fully released
    assert os.path.exists(lock1.lock_path)
    
    # lock1 解放 → 完全解放
    released = await lock1.release()
    assert released
    assert not os.path.exists(lock1.lock_path)


@pytest.mark.asyncio
async def test_stale_lock_recovery(tmp_path: Path):
    session_file = str(tmp_path / "stale.jsonl")
    lock_path = f"{os.path.realpath(session_file)}.lock"
    
    # 死んだPIDのロックファイルを手動作成
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    with open(lock_path, "w") as f:
        json.dump({"pid": 99999999, "created_at": "2020-01-01T00:00:00+00:00"}, f)
    
    # stale ロックを回収してロック取得
    lock = await acquire_session_write_lock(session_file, timeout_s=2)
    assert os.path.exists(lock.lock_path)
    await lock.release()


@pytest.mark.asyncio
async def test_timeout_on_active_lock(tmp_path: Path):
    session_file = str(tmp_path / "active.jsonl")
    lock_path = f"{os.path.realpath(session_file)}.lock"
    
    # 生きているPIDのロックファイルを作成
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    from datetime import datetime, timezone
    with open(lock_path, "w") as f:
        json.dump({"pid": os.getpid(), "created_at": datetime.now(timezone.utc).isoformat()}, f)
    
    # タイムアウトするはず
    with pytest.raises(TimeoutError, match="session file locked"):
        await acquire_session_write_lock(session_file, timeout_s=0.3, allow_reentrant=False)
    
    # クリーンアップ
    os.unlink(lock_path)


@pytest.mark.asyncio
async def test_context_manager(tmp_path: Path):
    session_file = str(tmp_path / "cm.jsonl")
    
    async with session_write_lock(session_file, timeout_s=2) as lock:
        assert os.path.exists(lock.lock_path)
    
    # context manager 終了後にロックファイルが消える
    assert not os.path.exists(lock.lock_path)


def test_clean_stale_locks(tmp_path: Path):
    # stale ロックファイルを2つ作成
    for name in ["session_a.jsonl.lock", "session_b.jsonl.lock"]:
        lock_path = tmp_path / name
        with open(lock_path, "w") as f:
            json.dump({"pid": 99999999, "created_at": "2020-01-01T00:00:00+00:00"}, f)
    
    results = clean_stale_locks(str(tmp_path), stale_s=1, remove=True)
    assert len(results) == 2
    assert all(r.stale for r in results)
    assert all(r.removed for r in results)
    
    # ファイルが消えている
    remaining = list(tmp_path.glob("*.lock"))
    assert len(remaining) == 0


def test_inspect_lock_alive_pid():
    from datetime import datetime, timezone
    # 現在時刻に近い created_at を使う
    now = time.time()
    recent_iso = datetime.fromtimestamp(now - 60, tz=timezone.utc).isoformat()
    payload = LockPayload(pid=os.getpid(), created_at=recent_iso)
    inspection = _inspect_lock(payload, stale_s=999999, now=now)
    assert inspection.pid == os.getpid()
    assert inspection.pid_alive
    assert not inspection.stale  # PID alive + not too old


def test_inspect_lock_dead_pid():
    payload = LockPayload(pid=99999999, created_at="2026-01-01T00:00:00+00:00")
    inspection = _inspect_lock(payload, stale_s=999999, now=time.time())
    assert not inspection.pid_alive
    assert inspection.stale
    assert "dead-pid" in inspection.stale_reasons
