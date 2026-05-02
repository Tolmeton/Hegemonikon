from __future__ import annotations
"""
Phantazein File Watcher — Always-On Boot の Phase 2。

watchdog を使ってファイルシステムの変更を監視し、
影響を受ける boot 軸のキャッシュをインクリメンタルに更新する。

MCP サーバー起動時に start_watcher() を呼ぶだけで常駐する。
stop_watcher() で安全に停止。

# PURPOSE: ファイル変更を検知して boot キャッシュを選択的に更新するデーモン
"""


import logging
import os
import threading
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger("phantazein.watcher")

# ── Syncthing 除外パターン ──
_IGNORE_PREFIXES = (".syncthing.", ".stversions", ".sync-conflict-")
_IGNORE_SUFFIXES = (".tmp", ".swp", ".swo", "~", ".part")


def _should_ignore(path: str) -> bool:
    """Syncthing の一時ファイル・バージョンを除外する。"""
    name = os.path.basename(path)
    if any(name.startswith(p) for p in _IGNORE_PREFIXES):
        return True
    if any(name.endswith(s) for s in _IGNORE_SUFFIXES):
        return True
    # .stversions/ ディレクトリ内のファイルも除外
    if "/.stversions/" in path or "\\.stversions\\" in path:
        return True
    return False


class _DebouncedHandler:
    """
    ファイル変更イベントをデバウンスし、軸単位でキャッシュ更新をトリガーする。

    連続するファイル変更 (Syncthing の atomic rename 等) を1秒間の quiet period で
    まとめて処理する。デバウンスは軸キー単位で行われるため、
    異なる軸の変更は独立してトリガーされる。
    """

    def __init__(self, dir_to_axes: dict[str, list[str]], debounce_sec: float = 1.0):
        self._dir_to_axes = dir_to_axes
        self._debounce_sec = debounce_sec
        self._pending: dict[str, float] = {}  # axis_key → last_event_time
        self._lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None

    def on_any_event(self, event) -> None:
        """watchdog イベントハンドラ。"""
        # ディレクトリイベント自体は無視 (ファイルイベントのみ)
        if getattr(event, "is_directory", False):
            return

        src_path = getattr(event, "src_path", "")
        if not src_path or _should_ignore(src_path):
            return

        # 変更パスから影響を受ける軸を特定
        affected_axes: set[str] = set()
        for watched_dir, axes in self._dir_to_axes.items():
            if src_path.startswith(watched_dir):
                affected_axes.update(axes)

        if not affected_axes:
            return

        now = time.time()
        with self._lock:
            for axis in affected_axes:
                self._pending[axis] = now

            # 既存タイマーをキャンセルして再設定 (デバウンス)
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce_sec, self._fire)
            self._timer.daemon = True
            self._timer.start()

    def _fire(self) -> None:
        """デバウンス期間経過後にキャッシュ更新をトリガーする。"""
        with self._lock:
            axes_to_update = list(self._pending.keys())
            self._pending.clear()
            self._timer = None

        if not axes_to_update:
            return

        logger.info(
            "Boot cache invalidation triggered: axes=%s",
            ", ".join(axes_to_update),
        )

        try:
            from mekhane.symploke.boot_integration import refresh_boot_cache
            result = refresh_boot_cache(axis_keys=axes_to_update)
            logger.info(
                "Boot cache refreshed: updated=%d/%d",
                result.get("updated", 0),
                result.get("requested", 0),
            )
        except Exception:  # noqa: BLE001
            logger.exception("Boot cache refresh failed")


# ── グローバル状態 ──
_observer = None
_observer_lock = threading.Lock()


def start_watcher() -> bool:
    """
    ファイル監視デーモンを開始する。

    MCP サーバー起動時に1回だけ呼ぶ。
    watchdog がインストールされていない場合は False を返す (致命的ではない)。

    Returns:
        True: 監視開始成功
        False: watchdog 未インストール or 既に起動済み
    """
    global _observer

    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        logger.warning(
            "watchdog not installed — boot cache watcher disabled. "
            "Install with: pip install watchdog"
        )
        return False

    with _observer_lock:
        if _observer is not None:
            logger.debug("Watcher already running")
            return False

        # 軸→ディレクトリマッピングを取得
        from mekhane.symploke.boot_integration import _dir_to_axes
        dir_axes_map = _dir_to_axes()

        # watchdog 用のアダプター (FileSystemEventHandler のサブクラス)
        debounced = _DebouncedHandler(dir_axes_map, debounce_sec=1.0)

        class _WatchdogAdapter(FileSystemEventHandler):
            def on_any_event(self, event):
                debounced.on_any_event(event)

        handler = _WatchdogAdapter()
        observer = Observer()
        observer.daemon = True

        # 各監視ディレクトリを登録
        scheduled = 0
        for watched_dir in dir_axes_map:
            dir_path = Path(watched_dir)
            if dir_path.exists() and dir_path.is_dir():
                observer.schedule(handler, str(dir_path), recursive=True)
                scheduled += 1
                logger.debug("Watching: %s", watched_dir)
            else:
                logger.debug("Skip non-existent dir: %s", watched_dir)

        if scheduled == 0:
            logger.warning("No directories to watch — watcher not started")
            return False

        observer.start()
        _observer = observer
        logger.info(
            "Boot cache watcher started: %d directories monitored",
            scheduled,
        )
        return True


def stop_watcher() -> None:
    """ファイル監視デーモンを安全に停止する。"""
    global _observer

    with _observer_lock:
        if _observer is None:
            return

        logger.info("Stopping boot cache watcher...")
        _observer.stop()
        _observer.join(timeout=5.0)
        _observer = None
        logger.info("Boot cache watcher stopped")


def watcher_status() -> dict:
    """監視デーモンの状態を返す (MCP 診断用)。"""
    with _observer_lock:
        if _observer is None:
            return {"running": False}

        return {
            "running": _observer.is_alive() if _observer else False,
            "daemon": True,
        }
