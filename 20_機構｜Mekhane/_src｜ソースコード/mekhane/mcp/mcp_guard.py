# PROOF: [L2/インフラ] <- mekhane/mcp/mcp_guard.py A0→MCP プロセスガード (DEPRECATED)
"""
[DEPRECATED] MCP Guard — ゾンビプロセス防止の自己防衛モジュール

WARNING: このモジュールは非推奨(Deprecated)です。
Antigravity IDE の MCP クライアントがプロセスライフサイクルを管理するため、
このモジュールが独自に行う kill 処理は IDE の動作と競合し、
接続エラー (Connection closed: EOF) を引き起こす原因となります。
新規の MCP サーバーでは、このモジュールを使用しないでください (`_base.run()` などを単独で呼ぶ構成にしてください)。

各 MCP サーバーが起動時に呼ぶ。同名サーバーの重複起動を構造的に不可能にする。

Design:
    1. PID ファイルで自プロセスを登録
    2. 起動時に古いプロセスを SIGTERM → SIGKILL
    3. /proc/{pid}/cmdline で誤 kill を防止
    4. atexit で PID ファイルを削除
    5. 全て try/except — ガード失敗 ≠ 起動失敗

Usage (DEPRECATED):
    if __name__ == "__main__":
        from mekhane.mcp.mcp_guard import guard
        guard("ochema")
        server.run()
"""
import atexit
import os
import signal
import time
import warnings
from pathlib import Path

# PID ファイルの保存先
PID_DIR = Path.home() / ".cache" / "hgk" / "mcp"

# SIGTERM 後に SIGKILL するまでの待機秒数
_KILL_WAIT = 2.0


# PURPOSE: [L2-auto] guard の関数定義
def guard(server_name: str) -> None:
    """[DEPRECATED] MCP サーバー起動ガード。
    
    WARNING: IDEプロセスマネージャーと競合するため非推奨。
    使用するとEOFエラーの原因になります。

    Args:
        server_name: サーバー識別名 (例: "ochema", "hermeneus")
    """
    warnings.warn(
        "mcp_guard.guard() is deprecated. It conflicts with IDE process management "
        "and causes EOF connection errors. Remove this from your server's __main__ block.",
        DeprecationWarning,
        stacklevel=2
    )
    try:
        _ensure_dir()
        # _kill_old_process(server_name)  # Temporarily disable to debug EOF issue
        _write_pid(server_name)
        _register_cleanup(server_name)
    except Exception:  # noqa: BLE001
        # ガード失敗 ≠ 起動失敗。従来通り起動を続行。
        pass


# PURPOSE: [L2-auto] _ensure_dir の関数定義
def _ensure_dir() -> None:
    """PID ディレクトリを作成。"""
    PID_DIR.mkdir(parents=True, exist_ok=True)


# PURPOSE: [L2-auto] _pid_file の関数定義
def _pid_file(server_name: str) -> Path:
    """PID ファイルのパスを返す。"""
    return PID_DIR / f"{server_name}.pid"


# PURPOSE: [L2-auto] _kill_old_process の関数定義
def _kill_old_process(server_name: str) -> None:
    """古い同名プロセスを安全に kill する。

    Safety:
        - PID ファイルの PID が実際に MCP サーバーか検証 (/proc/{pid}/cmdline)
        - 無関係なプロセスは kill しない
        - 自分自身は kill しない
    """
    pid_path = _pid_file(server_name)

    if not pid_path.exists():
        return

    try:
        old_pid = int(pid_path.read_text().strip())
    except (ValueError, OSError):
        # 壊れた PID ファイル → 削除して続行
        pid_path.unlink(missing_ok=True)
        return

    # 自分自身なら skip
    if old_pid == os.getpid():
        return

    # プロセスの生存確認 + MCP サーバーかどうか検証
    if not _is_mcp_process(old_pid, server_name):
        # PID は存在しないか、MCP サーバーではない → PID ファイルだけ削除
        pid_path.unlink(missing_ok=True)
        return

    # SIGTERM で丁寧に止める
    try:
        os.kill(old_pid, signal.SIGTERM)
    except ProcessLookupError:
        pid_path.unlink(missing_ok=True)
        return
    except PermissionError:
        # 他ユーザーのプロセス → 触らない
        return

    # 待機
    deadline = time.monotonic() + _KILL_WAIT
    while time.monotonic() < deadline:
        if not _process_alive(old_pid):
            break
        time.sleep(0.2)

    # まだ生きていたら SIGKILL
    if _process_alive(old_pid):
        try:
            os.kill(old_pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass

    pid_path.unlink(missing_ok=True)


# PURPOSE: [L2-auto] _is_mcp_process の関数定義
def _is_mcp_process(pid: int, server_name: str) -> bool:
    """PID が実際に MCP サーバーのプロセスかどうかを検証。

    /proc/{pid}/cmdline を読み、以下を両方満たす場合のみ True:
    - python を含む
    - server_name またはサーバーファイル名を含む

    これにより PID 再利用で無関係なプロセスを kill するリスクを排除。
    """
    try:
        cmdline_path = Path(f"/proc/{pid}/cmdline")
        if not cmdline_path.exists():
            return False
        cmdline = cmdline_path.read_bytes().decode("utf-8", errors="replace")
        # /proc/cmdline は \x00 区切り
        cmdline_lower = cmdline.lower().replace("\x00", " ")
        has_python = "python" in cmdline_lower
        has_server = (
            server_name in cmdline_lower
            or f"{server_name}_mcp" in cmdline_lower
            or f"{server_name}_server" in cmdline_lower
            or "mcp_server" in cmdline_lower
            or "hermeneus_mcp" in cmdline_lower
            or "hgk_gateway" in cmdline_lower
        )
        return has_python and has_server
    except (OSError, PermissionError):
        return False


# PURPOSE: [L2-auto] _process_alive の関数定義
def _process_alive(pid: int) -> bool:
    """プロセスが生存しているか確認。"""
    try:
        os.kill(pid, 0)  # signal 0 = 生存確認のみ
        return True
    except (ProcessLookupError, PermissionError):
        return False


# PURPOSE: [L2-auto] _write_pid の関数定義
def _write_pid(server_name: str) -> None:
    """自分の PID をファイルに書き込む。"""
    _pid_file(server_name).write_text(str(os.getpid()))


# PURPOSE: [L2-auto] _register_cleanup の関数定義
def _register_cleanup(server_name: str) -> None:
    """終了時に PID ファイルを削除する atexit ハンドラを登録。"""
    # PURPOSE: [L2-auto] _cleanup の関数定義
    def _cleanup():
        try:
            pid_path = _pid_file(server_name)
            if pid_path.exists():
                # 自分の PID の場合のみ削除 (他のプロセスが上書きしていたら触らない)
                stored_pid = int(pid_path.read_text().strip())
                if stored_pid == os.getpid():
                    pid_path.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass

    atexit.register(_cleanup)


# PURPOSE: [L2-auto] status の関数定義
def status() -> dict:
    """全 MCP サーバーの PID 状況を返す。診断用。"""
    result = {}
    if not PID_DIR.exists():
        return result

    for pid_file in PID_DIR.glob("*.pid"):
        name = pid_file.stem
        try:
            pid = int(pid_file.read_text().strip())
            alive = _process_alive(pid)
            is_mcp = _is_mcp_process(pid, name) if alive else False
            result[name] = {
                "pid": pid,
                "alive": alive,
                "is_mcp": is_mcp,
                "status": "✅ running" if (alive and is_mcp) else
                          "⚠️ stale" if not alive else
                          "🔴 wrong process",
            }
        except (ValueError, OSError):
            result[name] = {"pid": None, "status": "❌ corrupt"}

    return result
