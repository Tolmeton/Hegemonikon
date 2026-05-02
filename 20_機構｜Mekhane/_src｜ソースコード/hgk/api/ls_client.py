"""
IDE ConnectRPC Client — LS 自動検出 + キャッシュ付き ConnectRPC 呼び出し

HGK Gateway の一部として IDE (Language Server) の内部情報にアクセスする。
ls_daemon.json (Non-Standalone LS) を優先し、見つからなければ /proc+ss (IDE LS) にフォールバック。
"""
import os
import subprocess
import re
import json
import time
import urllib.request
from pathlib import Path
from typing import Any

# --- 定数 ---
DAEMON_INFO_PATH = Path.home() / ".gemini/antigravity/ls_daemon.json"

# --- キャッシュ (PID が変わるまで有効) ---
_cache: dict[str, Any] = {}
_cache_ts: float = 0.0
_CACHE_TTL = 30.0  # 30秒間キャッシュ


def _detect_ls_params() -> dict[str, Any]:
    """LS の ConnectRPC 接続パラメータを /proc + ss から検出する"""
    # 1. PID の取得
    r = subprocess.run(
        ['pgrep', '-f', 'language_server_linux.*workspace_id'],
        capture_output=True, text=True
    )
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError("LS process not found")
    pid = r.stdout.strip().split('\n')[0]

    # 2. CSRF トークンの取得
    with open(f'/proc/{pid}/cmdline', 'r') as f:
        cmdline = f.read().replace('\0', '\n')
    m_csrf = re.search(r'--csrf_token[=\n]([^\n]+)', cmdline)
    if not m_csrf:
        raise RuntimeError("CSRF token not found in cmdline")
    csrf = m_csrf.group(1).strip()

    # 3. ConnectRPC ポート (fd=10) の取得
    ss = subprocess.run(
        ['ss', '-tlnp'], capture_output=True, text=True
    ).stdout
    m_port = re.search(rf':(\d+).*pid={pid},fd=10', ss)
    if not m_port:
        raise RuntimeError("ConnectRPC port (fd=10) not found")
    port = int(m_port.group(1))

    return {'pid': pid, 'port': port, 'csrf': csrf, 'base_url': f'http://127.0.0.1:{port}'}


def _load_daemon_info() -> dict[str, Any] | None:
    """ls_daemon.json から接続情報を読み込む (Non-Standalone LS 用)

    ls_daemon.py が書き出す JSON (リスト or 辞書) を読み、
    最初の生存 PID を持つエントリを返す。
    """
    if not DAEMON_INFO_PATH.exists():
        return None
    try:
        data = json.loads(DAEMON_INFO_PATH.read_text())
        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            pid = entry.get("pid", 0)
            if not pid:
                continue
            try:
                os.kill(pid, 0)  # 生存確認
            except (OSError, ValueError):
                continue
            port = entry.get("port", 0)
            return {
                'pid': str(pid),
                'port': port,
                'csrf': entry.get('csrf', ''),
                'base_url': f"http://127.0.0.1:{port}",
                'source': 'daemon',
            }
    except Exception:  # noqa: BLE001
        pass
    return None


def _get_params() -> dict[str, Any]:
    """キャッシュ付きで LS パラメータを取得

    優先順位:
    1. ls_daemon.json (Non-Standalone LS)
    2. /proc + ss (IDE LS)
    """
    global _cache, _cache_ts
    now = time.monotonic()
    if _cache and (now - _cache_ts) < _CACHE_TTL:
        # PID が変わっていないか軽量チェック
        try:
            os.kill(int(_cache['pid']), 0)
            return _cache
        except (OSError, ValueError):
            pass  # プロセスが消えた — 再検出
    # 1. ls_daemon.json (Non-Standalone LS) を優先
    daemon = _load_daemon_info()
    if daemon:
        _cache = daemon
        _cache_ts = now
        return _cache
    # 2. フォールバック: /proc + ss (IDE LS)
    _cache = _detect_ls_params()
    _cache_ts = now
    return _cache


def call_ls(method: str, data: dict | None = None, timeout: int = 5) -> dict[str, Any]:
    """ConnectRPC unary メソッドを呼び出す"""
    params = _get_params()
    url = f"{params['base_url']}/exa.language_server_pb.LanguageServerService/{method}"

    payload = json.dumps(data or {}).encode('utf-8')
    req = urllib.request.Request(
        url, data=payload,
        headers={
            'Content-Type': 'application/json',
            'x-codeium-csrf-token': params['csrf'],
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode('utf-8')
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        raise RuntimeError(f"IDE API error {e.code}: {body}")
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"IDE network error: {e}")


def get_ide_status() -> dict[str, Any]:
    """IDE 接続ステータスを取得"""
    try:
        params = _get_params()
        return {
            "status": "connected",
            "pid": params["pid"],
            "port": params["port"],
            "source": params.get("source", "ide"),
        }
    except RuntimeError as e:
        return {"status": "disconnected", "error": str(e)}
