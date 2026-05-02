#!/usr/bin/env python3
from __future__ import annotations

"""リモート LS pool を SSH トンネル経由でローカルへ登録する。

Local Ochema bridge は ~/.gemini/antigravity/ls_daemon.json を読む。
このスクリプトは remote host 上の ls_daemon.json を読み、各 LS ポートに対して
localhost への SSH local-forward を張り、source='remote' のエントリとして
ローカルの ls_daemon.json に同期する。

主用途:
  - one-shot 登録: python -m mekhane.ochema.remote_ls_register --host 100.83.204.102
  - 常駐監視:      python -m mekhane.ochema.remote_ls_register --host 100.83.204.102 --watch
  - 後始末:        python -m mekhane.ochema.remote_ls_register --cleanup
"""

import argparse
import fcntl
import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DAEMON_INFO_PATH = Path(os.environ.get(
    "LS_DAEMON_INFO_PATH",
    str(Path.home() / ".gemini/antigravity/ls_daemon.json"),
))
REMOTE_LS_DAEMON_PATH = "$HOME/.gemini/antigravity/ls_daemon.json"
TUNNEL_STATE_DIR = Path("/tmp/hgk-ls-tunnels")
TUNNEL_STATE_FILE = TUNNEL_STATE_DIR / "tunnel_pids.json"
LOCAL_PORT_BASE = 51000


def _read_remote_ls_info(host: str, user: str = "makaron8426") -> list[dict[str, Any]]:
    remote_path = REMOTE_LS_DAEMON_PATH
    target = f"{user}@{host}" if "@" not in host else host
    cmd = [
        "ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=accept-new",
        target, f"cat {remote_path}",
    ]
    logger.info("リモート LS 情報取得: %s", " ".join(cmd))

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired:
        logger.error("SSH タイムアウト: %s", host)
        return []

    if result.returncode != 0:
        logger.error("SSH エラー (rc=%d): %s", result.returncode, result.stderr.strip())
        return []

    content = result.stdout.strip()
    if not content:
        logger.warning("リモート ls_daemon.json が空: %s", host)
        return []

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.error("JSON パースエラー: %s", exc)
        return []

    if isinstance(data, dict):
        data = [data]
    return [entry for entry in data if isinstance(entry, dict)]


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _listener_pid(local_port: int) -> int:
    try:
        result = subprocess.run(
            ["lsof", "-ti", f"TCP:{local_port}", "-sTCP:LISTEN"],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0
    if result.returncode != 0 or not result.stdout.strip():
        return 0
    try:
        return int(result.stdout.strip().splitlines()[0])
    except (ValueError, IndexError):
        return 0


def _port_listening(local_port: int, pid: int = 0) -> bool:
    listen_pid = _listener_pid(local_port)
    if listen_pid <= 0:
        return False
    return pid <= 0 or listen_pid == pid


def _kill_pid(pid: int) -> None:
    if pid <= 0:
        return
    try:
        os.kill(pid, signal.SIGTERM)
        logger.info("トンネル停止: PID=%d", pid)
    except ProcessLookupError:
        logger.info("既に停止済み: PID=%d", pid)
    except PermissionError:
        logger.warning("権限不足: PID=%d", pid)


def _setup_ssh_tunnel(host: str, remote_port: int, local_port: int, user: str = "makaron8426") -> int | None:
    target = f"{user}@{host}" if "@" not in host else host
    cmd = [
        "ssh", "-N", "-f",
        "-o", "ConnectTimeout=5",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "ExitOnForwardFailure=yes",
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=3",
        "-L", f"{local_port}:127.0.0.1:{remote_port}",
        target,
    ]
    logger.info("SSH トンネル設定: localhost:%d -> %s:%d", local_port, host, remote_port)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired:
        logger.error("SSH トンネルタイムアウト: port %d", remote_port)
        return None

    if result.returncode != 0:
        logger.error("SSH トンネル失敗 (rc=%d): %s", result.returncode, result.stderr.strip())
        return None

    for _ in range(10):
        pid = _listener_pid(local_port)
        if pid > 0:
            logger.info("SSH トンネル PID=%d (localhost:%d)", pid, local_port)
            return pid
        time.sleep(0.2)

    if _port_listening(local_port):
        logger.warning("SSH トンネル起動確認 (PID 不明): localhost:%d", local_port)
        return -1
    logger.warning("SSH トンネル起動確認できず: localhost:%d", local_port)
    return None


def _load_tunnel_state() -> dict[int, dict[str, Any]]:
    if not TUNNEL_STATE_FILE.exists():
        return {}
    try:
        raw = json.loads(TUNNEL_STATE_FILE.read_text())
    except json.JSONDecodeError:
        logger.error("トンネル state ファイルのパースエラー")
        return {}

    state: dict[int, dict[str, Any]] = {}
    for local_port_str, value in raw.items():
        try:
            local_port = int(local_port_str)
        except ValueError:
            continue
        if isinstance(value, int):
            state[local_port] = {"pid": value}
        elif isinstance(value, dict):
            state[local_port] = value
    return state


def _save_tunnel_state(state: dict[int, dict[str, Any]]) -> None:
    TUNNEL_STATE_DIR.mkdir(parents=True, exist_ok=True)
    serializable = {str(port): value for port, value in state.items()}
    with open(TUNNEL_STATE_FILE, "w") as handle:
        json.dump(serializable, handle, indent=2)
    logger.info("トンネル state 保存: %s", TUNNEL_STATE_FILE)


def _merge_write_remote(entries: list[dict[str, Any]]) -> int:
    if not entries:
        logger.warning("登録するリモートエントリなし")
        return 0

    DAEMON_INFO_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DAEMON_INFO_PATH, "a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            handle.seek(0)
            content = handle.read().strip()
            existing: list[dict[str, Any]] = []
            if content:
                try:
                    existing = json.loads(content)
                    if isinstance(existing, dict):
                        existing = [existing]
                except json.JSONDecodeError:
                    existing = []

            merged = [entry for entry in existing if entry.get("source") != "remote"] + entries
            handle.seek(0)
            handle.truncate()
            json.dump(merged, handle, indent=2)
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    logger.info("リモート LS 登録: %d エントリ", len(entries))
    return len(entries)


def _cleanup_remote_entries() -> None:
    if not DAEMON_INFO_PATH.exists():
        return
    try:
        with open(DAEMON_INFO_PATH, "r+") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                content = handle.read().strip()
                data = json.loads(content) if content else []
                if isinstance(data, dict):
                    data = [data]
                data = [entry for entry in data if entry.get("source") != "remote"]
                handle.seek(0)
                handle.truncate()
                json.dump(data, handle, indent=2)
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        logger.info("remote エントリを ls_daemon.json から削除")
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("ls_daemon.json クリーンアップ失敗: %s", exc)


def _cleanup_tunnels() -> None:
    state = _load_tunnel_state()
    for entry in state.values():
        _kill_pid(int(entry.get("pid", 0)))
    _cleanup_remote_entries()
    TUNNEL_STATE_FILE.unlink(missing_ok=True)
    logger.info("クリーンアップ完了: %d トンネル停止", len(state))


def _sync_tunnels(host: str, user: str, local_port_base: int) -> bool:
    remote_entries = _read_remote_ls_info(host, user)
    if not remote_entries:
        return False

    logger.info("取得: %d エントリ", len(remote_entries))
    existing_state = _load_tunnel_state()
    desired_state: dict[int, dict[str, Any]] = {}
    local_entries: list[dict[str, Any]] = []

    for index, remote_entry in enumerate(remote_entries):
        remote_port = int(remote_entry.get("port", 0) or 0)
        if remote_port <= 0:
            continue

        local_port = local_port_base + index
        prior_state = existing_state.get(local_port, {})
        prior_pid = int(prior_state.get("pid", 0) or 0)
        prior_remote_port = int(prior_state.get("remote_port", 0) or 0)

        tunnel_pid = 0
        if prior_remote_port == remote_port and _pid_alive(prior_pid) and _port_listening(local_port, prior_pid):
            tunnel_pid = prior_pid
        else:
            _kill_pid(prior_pid)
            tunnel_pid = _setup_ssh_tunnel(host, remote_port, local_port, user)
            if tunnel_pid is None:
                logger.warning("トンネル設定失敗 (remote port %d)。スキップ。", remote_port)
                continue

        desired_state[local_port] = {
            "pid": tunnel_pid,
            "remote_host": host,
            "remote_port": remote_port,
            "user": user,
            "updated_at": time.time(),
        }
        local_entries.append({
            "pid": tunnel_pid,
            "tunnel_pid": tunnel_pid,
            "remote_pid": int(remote_entry.get("pid", 0) or 0),
            "port": local_port,
            "host": "127.0.0.1",
            "csrf": remote_entry.get("csrf", ""),
            "workspace": remote_entry.get("workspace", ""),
            "is_https": remote_entry.get("is_https", False),
            "source": "remote",
            "updated_at": time.time(),
            "remote_host": host,
            "remote_port": remote_port,
        })

    for local_port, entry in existing_state.items():
        if local_port not in desired_state:
            _kill_pid(int(entry.get("pid", 0) or 0))

    if not local_entries:
        logger.error("有効なトンネルなし。")
        return False

    _save_tunnel_state(desired_state)
    _merge_write_remote(local_entries)

    for entry in local_entries:
        logger.info(
            "  localhost:%d -> %s:%d (workspace=%s pid=%s)",
            entry["port"], entry["remote_host"], entry["remote_port"],
            entry.get("workspace"), entry.get("pid"),
        )
    return True


def _watch(host: str, user: str, local_port_base: int, refresh_sec: int) -> int:
    running = True

    def _stop(signum, _frame):
        nonlocal running
        logger.info("Received signal %s", signum)
        running = False

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    while running:
        ok = _sync_tunnels(host, user, local_port_base)
        if not ok:
            logger.warning("リモート LS 同期失敗。%ds 後に再試行。", refresh_sec)
        stop_at = time.time() + refresh_sec
        while running and time.time() < stop_at:
            time.sleep(1)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="リモート LS を SSH トンネル経由でローカルに登録")
    parser.add_argument("--host", default=os.environ.get("HGK_REMOTE_LS_HOST", "hgk"))
    parser.add_argument("--user", default=os.environ.get("HGK_REMOTE_LS_USER", "makaron8426"))
    parser.add_argument("--cleanup", action="store_true", help="SSH トンネルを停止し remote エントリを削除")
    parser.add_argument("--watch", action="store_true", help="常駐監視モード")
    parser.add_argument("--refresh-sec", type=int, default=int(os.environ.get("HGK_REMOTE_LS_REFRESH_SEC", "30")))
    parser.add_argument("--local-port-base", type=int, default=LOCAL_PORT_BASE)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if args.cleanup:
        _cleanup_tunnels()
        return

    if args.watch:
        raise SystemExit(_watch(args.host, args.user, args.local_port_base, args.refresh_sec))

    ok = _sync_tunnels(args.host, args.user, args.local_port_base)
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
