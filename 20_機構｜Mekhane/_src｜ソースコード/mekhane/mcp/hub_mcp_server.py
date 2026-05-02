#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/hub_mcp_server.py A0→Hub MCP Proxy
"""
Hub MCP Router — 全射が通過する routing plane

Claude Code → local axis router (9720-9722) → local / remote MCP backends の透過プロキシ。

設計思想:
  - Antigravity は Hub に対して複数の「仮想サーバー」として接続する
  - 各仮想サーバーは /mcp/{backend_name} パスでルーティングされる
  - Hub は各バックエンドの list_tools/call_tool をそのまま転送する
  - 転送前後にパイプラインフック (ログ、Shadow、Gate) を挟む

Ph1: passthrough + ログ記録 ✓
Ph2: Shadow Gemini 自動反証 ✓
Ph3: Gate (Sekisho 統合) ✓
"""

import sys

# stdio transport 用: logging/import が stdout を汚す前にキャプチャ (mcp_base.py L192 と同一)
_original_stdout = sys.stdout

import os
import io
import json
import time
import asyncio
import logging
import argparse
import shutil
import subprocess as _subprocess
import socket as _socket
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime, timezone
from typing import Optional

# フルパス直起動でも `mekhane` を import できるよう source root を補う
_SOURCE_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_ROOT_STR = str(_SOURCE_ROOT)
if _SOURCE_ROOT_STR not in sys.path:
    sys.path.insert(0, _SOURCE_ROOT_STR)

from mekhane.mcp.hub_config import (
    AXIS_PORTS,
    AXIS_TO_GROUP,
    BACKENDS,
    DEFAULT_REMOTE_MCP_HOST,
    FEP_GROUPS,
    HUB_PORT,
    PIPELINE_CONFIG,
    axis_url,
    backend_runs_in_profile,
    backend_url,
    get_backend_axis,
    get_backends_by_fep_group,
    get_backends_for_axis,
    get_delegated_backends_for_axis,
    get_runnable_backends_for_axis,
    get_tool_scores,
)
from mekhane.mcp.hub.packet import build_return_packet, build_secretary_packet

# ログ設定: stderr のみ (stdout を汚染しないため)
logging.basicConfig(
    level=logging.INFO,
    format="[Axis] %(asctime)s %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("axis-router")


# PURPOSE: [L2-auto] ログ出力ヘルパー
def log(msg: str) -> None:
    """stderr にログ出力。"""
    print(f"[Axis] {msg}", file=sys.stderr, flush=True)


# =============================================================================
# バックエンド接続管理
# =============================================================================

class BackendConnection:
    """1つのバックエンド MCP サーバーへの接続を管理する。

    自動再接続: call_tool でセッションエラーが発生した場合、
    指数バックオフで再接続を試みる (最大60秒)。
    """

    # PURPOSE: [L2-auto] バックエンド接続の初期化
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self.tools: list[dict] = []
        self._connected = False
        self._reconnect_backoff: float = 1.0  # 再接続バックオフ (秒)
        self._last_reconnect_attempt: float = 0.0

    # PURPOSE: [L2-auto] バックエンドに接続しツールリストを取得
    async def connect(self) -> bool:
        """バックエンドに接続し、ツールリストを取得する。

        失敗時は contextmanager を確実にクリーンアップする。
        anyio cancel scope 跨ぎによる RuntimeError を防止。
        """
        try:
            from mcp.client.streamable_http import streamablehttp_client
            from mcp import ClientSession

            # NOTE:
            # streamablehttp_client を長寿命保持して別タスクから __aexit__ すると、
            # anyio cancel scope の task 不一致で RuntimeError になり得る。
            # 接続確認は短命セッションで完結させる。
            async with streamablehttp_client(self.url, timeout=30) as (
                read_stream,
                write_stream,
                _get_session_id,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.list_tools()

            self.tools = [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                }
                for tool in result.tools
            ]
            self._connected = True
            log(f"  ✓ {self.name}: {len(self.tools)} tools ({self.url})")
            return True

        except Exception as e:  # noqa: BLE001
            log(f"  ✗ {self.name}: {e}")
            self._connected = False
            return False

    # PURPOSE: [L2-auto] TCP プリフライト — ポートが listen しているか高速チェック
    def _tcp_preflight(self, timeout: float = 1.0) -> bool:
        """バックエンドのポートが listen 中か TCP レベルで確認する。

        MCP handshake より遥かに安価 (< 10ms vs > 500ms)。
        死んだバックエンドへの無駄な接続試行を回避する。
        """
        try:
            parsed = urlparse(self.url)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or 80
            with _socket.create_connection((host, port), timeout=timeout):
                return True
        except (OSError, ConnectionRefusedError):
            return False

    # PURPOSE: [L2-auto] ツール呼出をバックエンドに転送 (即座リトライ付き)
    async def call_tool(self, tool_name: str, arguments: dict, max_retries: int = 2) -> list[dict]:
        """ツール呼出をバックエンドに転送する。

        一過性エラー (接続断・Session terminated 等) 時は即座にリトライする。
        max_retries: 初回失敗後のリトライ回数 (デフォルト2、合計最大3回試行)。
        """
        # 未接続の場合、再接続を試みる
        if not self._connected:
            reconnected = await self._try_reconnect()
            if not reconnected:
                return [{"type": "text", "text": f"Error: Backend '{self.name}' is not connected"}]

        last_error: Exception | None = None
        for attempt in range(1 + max_retries):
            # TCP プリフライト: ポートが死んでいれば MCP handshake を試みない
            if not self._tcp_preflight(timeout=1.0):
                last_error = ConnectionRefusedError(f"{self.name} port not listening")
                log(f"  ⟳ {self.name}.{tool_name}: port unreachable (attempt {attempt + 1})")
                if attempt < max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                break

            try:
                from mcp.client.streamable_http import streamablehttp_client
                from mcp import ClientSession

                async with streamablehttp_client(self.url, timeout=60) as (
                    read_stream,
                    write_stream,
                    _get_session_id,
                ):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments)

                # 成功: バックオフをリセット
                self._reconnect_backoff = 1.0
                self._connected = True
                if attempt > 0:
                    log(f"  ✓ {self.name}.{tool_name}: recovered on attempt {attempt + 1}")
                # MCP SDK の result.content を dict のリストに変換
                return [
                    {"type": c.type, "text": getattr(c, "text", str(c))}
                    for c in result.content
                ]
            except Exception as e:  # noqa: BLE001
                last_error = e
                is_transient = self._is_transient_error(e)
                if attempt < max_retries and is_transient:
                    wait = 0.5 * (attempt + 1)  # 0.5s, 1.0s
                    log(f"  ⟳ {self.name}.{tool_name}: transient error, retry {attempt + 1}/{max_retries} in {wait:.1f}s — {e}")
                    await asyncio.sleep(wait)
                    continue
                # 最終試行 or 非一過性エラー → 終了
                break

        log(f"  ✗ {self.name}.{tool_name}: {last_error}")
        self._connected = False
        return [{"type": "text", "text": f"Error: {self.name}.{tool_name} failed: {last_error}"}]

    @staticmethod
    def _is_transient_error(e: Exception) -> bool:
        """一過性エラー (リトライで回復する可能性がある) かを判定する。"""
        msg = str(e).lower()
        transient_patterns = [
            "session terminated",
            "connection refused",
            "connection reset",
            "broken pipe",
            "timed out",
            "timeout",
            "503",
            "502",
            "connect call failed",
            "server disconnected",
        ]
        return any(p in msg for p in transient_patterns)

    # PURPOSE: [L2-auto] 自動再接続 (指数バックオフ, force オプション付き)
    async def _try_reconnect(self, force: bool = False) -> bool:
        """指数バックオフで再接続を試みる。最大30秒。

        force=True の場合、バックオフ期間を無視して即座に試行する。
        execute 等からの明示的な再接続要求で使用。
        """
        now = time.time()
        if not force and now - self._last_reconnect_attempt < self._reconnect_backoff:
            return False  # バックオフ期間中

        self._last_reconnect_attempt = now
        log(f"  🔄 Reconnecting to {self.name}... (backoff={self._reconnect_backoff:.0f}s)")

        # 既存セッションをクリーンアップ
        await self.disconnect()

        success = await self.connect()
        if success:
            self._reconnect_backoff = 1.0  # リセット
            log(f"  ✓ Reconnected to {self.name}")
        else:
            # 指数バックオフ (最大30秒; 60秒は長すぎた)
            self._reconnect_backoff = min(self._reconnect_backoff * 2, 30.0)
        return success

    # PURPOSE: [L2-auto] 接続クリーンアップ
    async def disconnect(self):
        """接続をクリーンアップする。"""
        # 短命セッション化により明示クリーンアップ対象はない。
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected


# =============================================================================
# Stdio MCP バックエンド接続 (codex mcp-server 等)
# =============================================================================

class StdioBackendConnection:
    """stdio ベースの MCP サーバー子プロセスへの接続を管理する。

    BackendConnection (HTTP) と同じインターフェースを提供し、
    Hub のパイプライン (recommend/execute/shadow/gate) から透過的に使用できる。

    使用例: codex mcp-server, gemini-mcp-tool 等
    """

    def __init__(self, name: str, command: list[str], env: dict[str, str] | None = None):
        self.name = name
        self.command = command
        self.env = env
        self.tools: list[dict] = []
        self._connected = False
        self._process: asyncio.subprocess.Process | None = None
        self._session = None
        self._read_stream = None
        self._write_stream = None
        self._cm_stack = None  # contextmanager stack for cleanup
        self._reconnect_backoff: float = 1.0
        self._last_reconnect_attempt: float = 0.0

    async def connect(self) -> bool:
        """子プロセスを起動し、stdio MCP クライアントで接続する。"""
        try:
            # コマンドの実行可能性を確認
            cmd_name = self.command[0]
            cmd_path = shutil.which(cmd_name)
            if not cmd_path:
                # ~/.local/bin も検索
                local_bin = Path.home() / ".local" / "bin" / cmd_name
                if local_bin.exists():
                    cmd_path = str(local_bin)
                else:
                    log(f"  ✗ {self.name}: command '{cmd_name}' not found in PATH")
                    self._connected = False
                    return False

            full_command = [cmd_path] + self.command[1:]

            from mcp.client.stdio import stdio_client, StdioServerParameters
            from mcp import ClientSession
            from contextlib import AsyncExitStack

            server_params = StdioServerParameters(
                command=full_command[0],
                args=full_command[1:],
                env={**os.environ, **(self.env or {})},
            )

            # AsyncExitStack で contextmanager のライフサイクルを管理
            self._cm_stack = AsyncExitStack()
            transport = await self._cm_stack.enter_async_context(
                stdio_client(server_params)
            )
            self._read_stream, self._write_stream = transport
            self._session = await self._cm_stack.enter_async_context(
                ClientSession(self._read_stream, self._write_stream)
            )
            await self._session.initialize()
            result = await self._session.list_tools()

            self.tools = [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                }
                for tool in result.tools
            ]
            self._connected = True
            log(f"  ✓ {self.name} (stdio): {len(self.tools)} tools — {' '.join(self.command)}")
            return True

        except Exception as e:  # noqa: BLE001
            log(f"  ✗ {self.name} (stdio): {e}")
            self._connected = False
            await self._cleanup()
            return False

    async def call_tool(self, tool_name: str, arguments: dict, max_retries: int = 1) -> list[dict]:
        """stdio MCP サーバーのツールを呼び出す。

        接続断時は再接続を試みてからリトライする。
        """
        if not self._connected or not self._session:
            reconnected = await self._try_reconnect()
            if not reconnected:
                return [{"type": "text", "text": f"Error: Stdio backend '{self.name}' is not connected"}]

        last_error: Exception | None = None
        for attempt in range(1 + max_retries):
            try:
                result = await self._session.call_tool(tool_name, arguments)
                if attempt > 0:
                    log(f"  ✓ {self.name}.{tool_name} (stdio): recovered on attempt {attempt + 1}")
                self._reconnect_backoff = 1.0
                return [
                    {"type": c.type, "text": getattr(c, "text", str(c))}
                    for c in result.content
                ]
            except Exception as e:  # noqa: BLE001
                last_error = e
                if attempt < max_retries:
                    log(f"  ⟳ {self.name}.{tool_name} (stdio): error, reconnecting... — {e}")
                    await self._cleanup()
                    reconnected = await self.connect()
                    if not reconnected:
                        break
                    continue
                break

        log(f"  ✗ {self.name}.{tool_name} (stdio): {last_error}")
        self._connected = False
        return [{"type": "text", "text": f"Error: {self.name}.{tool_name} failed: {last_error}"}]

    async def _try_reconnect(self, force: bool = False) -> bool:
        """指数バックオフで再接続を試みる。"""
        now = time.time()
        if not force and now - self._last_reconnect_attempt < self._reconnect_backoff:
            return False

        self._last_reconnect_attempt = now
        log(f"  🔄 Reconnecting stdio backend {self.name}... (backoff={self._reconnect_backoff:.0f}s)")

        await self._cleanup()
        success = await self.connect()
        if success:
            self._reconnect_backoff = 1.0
        else:
            self._reconnect_backoff = min(self._reconnect_backoff * 2, 30.0)
        return success

    async def _cleanup(self):
        """子プロセスとセッションをクリーンアップする。"""
        self._session = None
        self._read_stream = None
        self._write_stream = None
        if self._cm_stack:
            try:
                await self._cm_stack.aclose()
            except Exception:  # noqa: BLE001
                pass
            self._cm_stack = None

    async def disconnect(self):
        """接続とプロセスをシャットダウンする。"""
        await self._cleanup()
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected


# =============================================================================
# Hub MCP Proxy サーバー
# =============================================================================

class HubProxy:
    """
    Hub MCP Proxy — 全射が通過する routing plane。

    Antigravity の mcp.json で各サーバーが
      {"type": "http", "url": "http://127.0.0.1:9720/mcp"}
    と設定されている場合、Antigravity は各 name に対して個別に接続する。

    Hub は各パス (/mcp/{name}) への接続を受け取り、
    対応するバックエンドサーバーに転送する。

    パイプライン:
      Pre-hook  → ログ記録
      転送      → backend.call_tool()
      Post-hook → Shadow Gemini 反証 (自動) + Gate (Sekisho; 明示呼出 daimonion_judge のみ)
    """

    # PURPOSE: [L2-auto] Hub の初期化
    def __init__(
        self,
        axis: str | None = None,
        placement_profile: str = "local",
        remote_upstream_host: str | None = None,
    ):
        self.backends: dict[str, BackendConnection] = {}
        self._call_log: list[dict] = []
        self._start_time = time.time()
        self._shadow = None
        self._gate_count = 0
        self._gate_pass_count = 0
        self._gate_block_count = 0
        self.axis = axis if axis in AXIS_TO_GROUP else None
        self.placement_profile = placement_profile
        self.remote_upstream_host = remote_upstream_host or DEFAULT_REMOTE_MCP_HOST
        self._upstream_axis: BackendConnection | None = None
        self._helper_backend_names = self._resolve_helper_backend_names()
        self._direct_backend_names = self._resolve_direct_backend_names()
        self._delegated_backend_names = self._resolve_delegated_backend_names()
        self._exposed_backend_names = self._resolve_exposed_backend_names()

    @property
    def is_axis_router(self) -> bool:
        return self.axis is not None

    @property
    def primary_server_name(self) -> str:
        return self.axis or "hub"

    def route_names(self) -> list[str]:
        """このプロセスが公開する MCP サーバー名一覧。"""
        if not self.is_axis_router:
            return list(BACKENDS.keys()) + ["hub"] + list(AXIS_TO_GROUP.keys())

        names = [self.axis]
        for name in self._direct_backend_names:
            if name in self._exposed_backend_names and name not in names:
                names.append(name)
        return names

    def _resolve_helper_backend_names(self) -> list[str]:
        if self.placement_profile != "local":
            return []
        # secretary/recommend/gate は全 axis でローカル ochema/sekisho を内部利用する。
        return [
            name for name in ("ochema", "sekisho")
            if backend_runs_in_profile(name, "local")
        ]

    def _resolve_direct_backend_names(self) -> list[str]:
        if not self.is_axis_router:
            return list(BACKENDS.keys())

        names = list(get_runnable_backends_for_axis(self.axis, self.placement_profile))
        for helper in self._helper_backend_names:
            if helper not in names:
                names.append(helper)
        return names

    def _resolve_delegated_backend_names(self) -> list[str]:
        if not self.is_axis_router:
            return []
        return list(get_delegated_backends_for_axis(self.axis, self.placement_profile))

    def _resolve_exposed_backend_names(self) -> list[str]:
        if not self.is_axis_router:
            return list(BACKENDS.keys())
        return list(get_backends_for_axis(self.axis))

    def _backend_connected(self, name: str) -> bool:
        conn = self.backends.get(name)
        if conn is not None:
            return conn.is_connected
        if name in self._delegated_backend_names:
            return bool(self._upstream_axis and self._upstream_axis.is_connected)
        return False

    def _visible_backends(self, *, fep_group: str | None = None) -> list[str]:
        if self.is_axis_router:
            visible = list(self._exposed_backend_names)
        else:
            visible = list(BACKENDS.keys())

        if fep_group is None:
            return visible
        return [
            name for name in visible
            if BACKENDS.get(name, {}).get("fep_group") == fep_group
        ]

    def _upstream_backend_tools(self) -> list[dict]:
        if not self._upstream_axis or not self._upstream_axis.tools:
            return []
        return [
            tool for tool in self._upstream_axis.tools
            if tool.get("name") not in self.ROUTER_SELF_TOOLS
        ]

    # PURPOSE: [L2-auto] Daimonion (旧 Shadow Gemini) の遅延初期化
    def _get_shadow(self):
        """Daimonion インスタンスを遅延初期化して返す。後方互換: _get_shadow 名を維持。"""
        if self._shadow is None:
            try:
                from mekhane.mcp.daimonion import get_daimonion
                self._shadow = get_daimonion()
                log("Daimonion (δαιμόνιον) initialized")
            except Exception as e:  # noqa: BLE001
                log(f"Daimonion init failed: {e}")
        return self._shadow

    # PURPOSE: [L2-auto] 全バックエンドに接続 (リトライ付き)
    async def connect_all(self, max_retries: int = 3, retry_delay: float = 2.0) -> dict[str, bool]:
        """全バックエンドに接続する。

        未接続バックエンドも登録し、後から遅延接続可能にする。
        リトライ: 未接続バックエンドに対して max_retries 回まで再試行。
        """
        log("Connecting to backends...")
        results = {}

        # 直接接続するバックエンドのみ登録する。axis router では remote バックエンドは upstream 委譲。
        target_backend_names = self._direct_backend_names if self.is_axis_router else list(BACKENDS.keys())

        for name in target_backend_names:
            cfg = BACKENDS[name]
            # subprocess バックエンド (gemini-cli 等) は MCP 接続対象外
            if cfg.get("type") == "subprocess":
                results[name] = True  # subprocess は常に「利用可能」
                continue
            # stdio MCP バックエンド (codex mcp-server 等) は子プロセスとして起動
            if cfg.get("type") == "stdio_mcp":
                command = cfg.get("command", [])
                if name not in self.backends:
                    self.backends[name] = StdioBackendConnection(
                        name, command, env=cfg.get("env"),
                    )
                continue
            url = backend_url(name)
            if name not in self.backends:
                self.backends[name] = BackendConnection(name, url)

        if self.is_axis_router and self._delegated_backend_names:
            self._upstream_axis = BackendConnection(
                f"{self.axis}-upstream",
                axis_url(self.axis, host=self.remote_upstream_host),
            )

        # リトライループ
        for attempt in range(1, max_retries + 1):
            pending = [n for n, c in self.backends.items() if not c.is_connected]
            upstream_pending = bool(
                self._upstream_axis is not None and not self._upstream_axis.is_connected
            )
            if not pending and not upstream_pending:
                break

            if attempt > 1:
                delay = retry_delay * (attempt - 1)
                total_pending = len(pending) + (1 if upstream_pending else 0)
                log(f"  Retry {attempt}/{max_retries} ({total_pending} pending, waiting {delay:.0f}s)...")
                await asyncio.sleep(delay)

            for name in pending:
                conn = self.backends[name]
                success = await conn.connect()
                results[name] = success
            if upstream_pending and self._upstream_axis is not None:
                try:
                    results[f"{self.axis}-upstream"] = await asyncio.wait_for(
                        self._upstream_axis.connect(),
                        timeout=5.0,
                    )
                except asyncio.TimeoutError:
                    log(f"  ✗ {self.axis}-upstream: connect timed out")
                    self._upstream_axis._connected = False
                    results[f"{self.axis}-upstream"] = False

        # 結果集計
        for name in target_backend_names:
            if name not in results and name in self.backends:
                results[name] = self.backends[name].is_connected
        for name in self._delegated_backend_names:
            results[name] = bool(self._upstream_axis and self._upstream_axis.is_connected)

        connected = sum(1 for v in results.values() if v)
        total = len(results)
        log(f"Connected: {connected}/{total} backends")

        # Shadow の初期化 (接続後)
        if PIPELINE_CONFIG.get("shadow_enabled"):
            self._get_shadow()

        return results

    # PURPOSE: [L2-auto] 未接続バックエンドのバックグラウンド再接続
    async def reconnect_loop(self, interval: float = 5.0):
        """未接続バックエンドを定期的に再接続するバックグラウンドタスク。

        interval: 5s (旧: 30s)。バックエンドが systemd Restart=always (RestartSec=3-5s) で
        復帰するため、5s ポーリングなら最大 ~10s で回復する。
        """
        while True:
            await asyncio.sleep(interval)
            disconnected = [n for n, c in self.backends.items() if not c.is_connected]
            upstream_disconnected = bool(
                self._upstream_axis is not None and not self._upstream_axis.is_connected
            )
            if not disconnected and not upstream_disconnected:
                continue
            if disconnected:
                log(f"  🔄 Background reconnect: {len(disconnected)} backends ({', '.join(disconnected)})...")
            for name in disconnected:
                conn = self.backends[name]
                if isinstance(conn, StdioBackendConnection):
                    # stdio バックエンドは TCP preflight 不要 — 直接再接続を試みる
                    await conn.connect()
                elif hasattr(conn, '_tcp_preflight'):
                    # HTTP バックエンド: TCP プリフライトで port が開いている場合のみ MCP 接続を試行
                    if conn._tcp_preflight(timeout=1.0):
                        await conn.connect()
                    # else: まだ再起動中 → 次のループまでスキップ
            if upstream_disconnected and self._upstream_axis is not None:
                log(f"  🔄 Background reconnect: upstream axis {self.axis} ({self.remote_upstream_host})")
                if self._upstream_axis._tcp_preflight(timeout=1.0):
                    await self._upstream_axis.connect()

    # PURPOSE: [L2-auto] FEP 軸仮想サーバーの定義
    # 各軸が集約する axis-router ツール名。backend ツールは fep_group から自動収集。
    _FEP_AXIS_MAP: dict[str, str] = AXIS_TO_GROUP
    _FEP_AXIS_ROUTER_TOOLS: dict[str, list[str]] = {
        # S群: 知覚入口 + execute + secretary + boot_context + stats
        "aisthetikon": [
            "aisthetikon", "execute", "secretary",
            "boot_context", "axis_stats",
        ],
        # I群: 推論入口 + execute + secretary + recommend + daimonion
        "dianoetikon": [
            "dianoetikon", "execute", "secretary",
            "recommend", "daimonion_status", "daimonion_judge",
        ],
        # E群: 生産入口 + execute + secretary
        "poietikon": [
            "poietikon", "execute", "secretary",
        ],
    }

    # PURPOSE: [L2-auto] 特定バックエンドのツールリストを返却
    def list_tools_for(self, backend_name: str) -> list[dict]:
        """特定バックエンドのツールリストを返す。

        backend_name == "hub" の場合は Hub 固有ツールを返す。
        FEP 軸名 (aisthetikon/dianoetikon/poietikon) の場合は軸集約ツールを返す。
        """
        if backend_name == "hub":
            return self._router_tools()
        if backend_name in self._FEP_AXIS_MAP:
            if self.is_axis_router and backend_name != self.axis:
                return []
            return self._fep_axis_tools(backend_name)
        if self.is_axis_router and backend_name not in self._exposed_backend_names:
            return []
        conn = self.backends.get(backend_name)
        if not conn:
            return []
        return conn.tools

    # PURPOSE: [L2-auto] FEP 軸仮想サーバーのツール集約
    def _fep_axis_tools(self, axis_name: str) -> list[dict]:
        """FEP 軸に属する全バックエンドのツール + 軸固有 router ツールを返す。"""
        fep_group = self._FEP_AXIS_MAP[axis_name]
        tools: list[dict] = []
        seen_names: set[str] = set()

        def add_tool(tool: dict) -> None:
            name = tool.get("name", "")
            if not name or name in seen_names:
                return
            seen_names.add(name)
            tools.append(tool)

        if self.is_axis_router:
            if axis_name != self.axis:
                return []
            visible_backends = self._visible_backends(fep_group=fep_group)
            for name in visible_backends:
                conn = self.backends.get(name)
                if conn and conn.tools:
                    for tool in conn.tools:
                        add_tool(tool)
            for tool in self._upstream_backend_tools():
                add_tool(tool)
        else:
            for name, cfg in BACKENDS.items():
                if cfg.get("fep_group") != fep_group:
                    continue
                conn = self.backends.get(name)
                if conn and conn.tools:
                    for tool in conn.tools:
                        add_tool(tool)

        # 軸固有 router ツールを追加
        router_tool_names = set(self._FEP_AXIS_ROUTER_TOOLS.get(axis_name, []))
        for t in self._router_tools():
            if t["name"] in router_tool_names:
                add_tool(t)

        return tools

    # PURPOSE: [L2-auto] axis-router 固有ツールの定義
    def _router_tools(self) -> list[dict]:
        """axis-router 固有のツール定義を返す。"""
        return [
            {
                "name": "daimonion_status",
                "description": "Daimonion (δαιμόνιον) の状態/切替。enabled パラメータで α (反証) モードの ON/OFF。省略時は全モードの統計を返す。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "enabled": {
                            "type": "boolean",
                            "description": "True=有効, False=無効。省略時は現状を返す",
                        },
                    },
                },
            },
            {
                "name": "axis_stats",
                "description": "axis router の統計: 呼出ログ、Daimonion 結果、バックエンド状態、Gate 統計。",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "recommend",
                "description": "タスク記述から最適な MCP バックエンドとツールを推奨する (S-006 Stage 1)。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_description": {
                            "type": "string",
                            "description": "実行したいタスクの説明",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返す推奨件数 (デフォルト: 3)",
                            "default": 3,
                        },
                        "task_id": {"type": "string", "description": "タスクID (V-009パケット用, 省略可)"},
                        "decisions_log_path": {"type": "string", "description": "意思決定ログのパス (省略可)"},
                    },
                    "required": ["task_description"],
                },
            },
            {
                "name": "daimonion_judge",
                "description": "Daimonion γ (Akribeia) — 精密監査。Agent の応答ドラフトを BC 違反チェック。PASS なら gate_token 発行。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "draft_response": {
                            "type": "string",
                            "description": "Agent の応答ドラフト (全文)",
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Agent の思考過程",
                        },
                        "depth": {
                            "type": "string",
                            "description": "深度レベル (L0-L3)",
                            "default": "L2",
                            "enum": ["L0", "L1", "L2", "L3"],
                        },
                        "task_id": {"type": "string", "description": "タスクID (V-009パケット用, 省略可)"},
                        "decisions_log_path": {"type": "string", "description": "意思決定ログのパス (省略可)"},
                    },
                    "required": ["draft_response", "reasoning"],
                },
            },
            {
                "name": "execute",
                "description": "指定したバックエンドのツールを axis router 経由で実行する (S-006 Stage 2)。recommend で推奨を取得後、Claude が選択したツールを実行。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "backend": {
                            "type": "string",
                            "description": "バックエンド名 (例: periskope, mneme, ochema)",
                        },
                        "tool": {
                            "type": "string",
                            "description": "実行するツール名 (例: periskope_research, search)",
                        },
                        "arguments": {
                            "type": "object",
                            "description": "ツールに渡す引数 (JSON オブジェクト)",
                            "default": {},
                        },
                        "task_id": {"type": "string", "description": "タスクID (V-009パケット用, 省略可)"},
                        "decisions_log_path": {"type": "string", "description": "意思決定ログのパス (省略可)"},
                    },
                    "required": ["backend", "tool"],
                },
            },
            {
                "name": "boot_context",
                "description": "/boot 相当: GET /api/symploke/boot-context を優先し、不通時は get_boot_context をローカル同期実行。axes + formatted を含む JSON を返す。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mode": {
                            "type": "string",
                            "description": "fast | standard | detailed",
                            "enum": ["fast", "standard", "detailed"],
                            "default": "standard",
                        },
                        "context": {
                            "type": "string",
                            "description": "セッションコンテキスト (省略可)",
                        },
                        "timeout_sec": {
                            "type": "integer",
                            "description": "API 側 boot-context のタイムアウト秒 (10–300, 既定 90)",
                            "default": 90,
                        },
                        "task_id": {"type": "string", "description": "タスクID (V-009パケット用, 省略可)"},
                        "decisions_log_path": {"type": "string", "description": "意思決定ログのパス (省略可)"},
                    },
                },
            },
            # --- FEP 認知入口: 3能力 (τὸ -τικόν 系) ---
            {
                "name": "aisthetikon",
                "description": "Aisthetikon (τὸ αἰσθητικόν) — 知覚能力: 調べたいとき。periskope, phantazein, digestor, gws, opsis 等の知覚系バックエンドから最適ツールを推奨。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_description": {
                            "type": "string",
                            "description": "調べたい内容の説明",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返す推奨件数 (デフォルト: 3)",
                            "default": 3,
                        },
                        "task_id": {"type": "string", "description": "タスクID (省略可)"},
                        "decisions_log_path": {"type": "string", "description": "意思決定ログのパス (省略可)"},
                    },
                    "required": ["task_description"],
                },
            },
            {
                "name": "dianoetikon",
                "description": "Dianoetikon (τὸ διανοητικόν) — 推論能力: 処理を深めたいとき。ochema, hermeneus, sympatheia, sekisho, typos 等の推論系バックエンドから最適ツールを推奨。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_description": {
                            "type": "string",
                            "description": "深めたい処理の説明",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返す推奨件数 (デフォルト: 3)",
                            "default": 3,
                        },
                        "task_id": {"type": "string", "description": "タスクID (省略可)"},
                        "decisions_log_path": {"type": "string", "description": "意思決定ログのパス (省略可)"},
                    },
                    "required": ["task_description"],
                },
            },
            {
                "name": "poietikon",
                "description": "Poietikon (τὸ ποιητικόν) — 生産能力: 成果物を生成したいとき。jules, codex-mcp, cursor-agent 等の行為系バックエンドから最適ツールを推奨。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_description": {
                            "type": "string",
                            "description": "生成したい成果物の説明",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返す推奨件数 (デフォルト: 3)",
                            "default": 3,
                        },
                        "task_id": {"type": "string", "description": "タスクID (省略可)"},
                        "decisions_log_path": {"type": "string", "description": "意思決定ログのパス (省略可)"},
                    },
                    "required": ["task_description"],
                },
            },
            {
                "name": "secretary",
                "description": "統合秘書 (Vision B): タスクを分析→最適ツール選定→実行→反証→監査を一括実行し、判断材料パッケージを返す。ルーティング脳が計画、Daimonion α が反証、Daimonion γ が監査。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_description": {
                            "type": "string",
                            "description": "秘書に依頼したいタスクの詳細",
                        },
                        "max_steps": {
                            "type": "integer",
                            "description": "ルーティング計画の最大ステップ数 (デフォルト: 5)",
                            "default": 5,
                        },
                        "routing_model": {
                            "type": "string",
                            "description": "ルーティング脳のモデル (デフォルト: config値。claude-opus-4-6 でOpus切替)",
                        },
                        "skip_shadow": {
                            "type": "boolean",
                            "description": "反証生成をスキップする (デフォルト: false)",
                            "default": False,
                        },
                        "skip_gate": {
                            "type": "boolean",
                            "description": "Gate 監査をスキップする (デフォルト: false)",
                            "default": False,
                        },
                        "task_id": {"type": "string", "description": "タスクID (V-009パケット用, 省略可)"},
                        "decisions_log_path": {"type": "string", "description": "意思決定ログのパス (省略可)"},
                    },
                    "required": ["task_description"],
                },
            },
        ]

    # PURPOSE: [L2-auto] axis-router 固有ツールの実行
    async def _call_router_tool(self, tool_name: str, arguments: dict) -> list[dict]:
        """axis-router 固有ツールを実行する。"""
        if tool_name == "daimonion_status":
            return await self._handle_shadow_status(arguments)
        elif tool_name == "axis_stats":
            return await self._handle_axis_stats(arguments)
        elif tool_name == "recommend":
            return await self._handle_recommend(arguments)
        elif tool_name == "daimonion_judge":
            return await self._handle_gate(arguments)
        elif tool_name == "execute":
            return await self._handle_execute(arguments)
        elif tool_name == "boot_context":
            return await self._handle_boot_context(arguments)
        elif tool_name == "secretary":
            return await self._handle_secretary(arguments)
        # FEP 認知入口
        elif tool_name == "aisthetikon":
            return await self._handle_recommend(arguments, fep_group="S")
        elif tool_name == "dianoetikon":
            return await self._handle_recommend(arguments, fep_group="I")
        elif tool_name == "poietikon":
            return await self._handle_recommend(arguments, fep_group="E")
        else:
            return [{"type": "text", "text": f"Error: Unknown axis-router tool '{tool_name}'"}]

    # PURPOSE: [L2-auto] Shadow ステータスの取得/切替
    async def _handle_shadow_status(self, arguments: dict) -> list[dict]:
        """Shadow Gemini のステータス取得/切替。"""
        shadow = self._get_shadow()
        if shadow is None:
            return [{"type": "text", "text": json.dumps({"error": "Shadow not initialized"}, ensure_ascii=False)}]

        if "enabled" in arguments:
            shadow.enabled = arguments["enabled"]
            log(f"Shadow {'enabled' if shadow.enabled else 'disabled'} by daimonion_status")

        return [{"type": "text", "text": json.dumps(shadow.stats(), ensure_ascii=False, indent=2)}]

    # PURPOSE: [L2-auto] Hub 統計の取得
    async def _handle_axis_stats(self, arguments: dict) -> list[dict]:
        """Hub 全体の統計を返す。"""
        stats = self.stats()
        return [{"type": "text", "text": json.dumps(stats, ensure_ascii=False, indent=2)}]

    # PURPOSE: [L2-auto] ツール推奨エンジン (S-006 Stage 1)
    async def _handle_recommend(self, arguments: dict, fep_group: str | None = None) -> list[dict]:
        """タスク記述から最適なバックエンド+ツールを推奨する。

        優先: LLM (Gemini Flash via ochema) による意味的推奨。
        フォールバック: キーワードマッチ (ochema 不通時/パースエラー時)。

        fep_group: "S"|"I"|"E" で絞り込み (aisthetikon/dianoetikon/poietikon から呼ばれる)。
                   None の場合は全バックエンドが対象 (recommend)。
        """
        task_desc = arguments.get("task_description", "").strip()
        if not task_desc:
            return [{"type": "text", "text": "Error: task_description is required"}]

        top_k = min(max(arguments.get("top_k", 3), 1), 10)

        # LLM 推奨を試みる → 失敗時はキーワードマッチにフォールバック
        recommendations = await self._recommend_backend_llm(task_desc, top_k, fep_group=fep_group)
        if recommendations is not None:
            note = "[TAINT: LLM推論] Gemini Flash による意味的推奨。確認して使用してください。"
        else:
            recommendations = self._recommend_backend_keyword(task_desc, top_k, fep_group=fep_group)
            note = "[TAINT: ルールベース推論] キーワードマッチの結果 (LLM フォールバック)。"

        # FEP グループ情報を付与
        _FEP_TOOL_NAMES = {"S": "aisthetikon", "I": "dianoetikon", "E": "poietikon"}
        fep_label = FEP_GROUPS.get(fep_group, "") if fep_group else ""
        source_tool = _FEP_TOOL_NAMES.get(fep_group, "recommend") if fep_group else "recommend"

        result_body = {
            "task": task_desc,
            "recommendations": recommendations,
            "note": note,
        }
        if fep_group:
            result_body["fep_group"] = fep_group
            result_body["fep_label"] = fep_label

        packet_str = build_return_packet(
            backend=source_tool,
            status="success",
            result=result_body,
            task_id=arguments.get("task_id"),
            decisions_log_path=arguments.get("decisions_log_path")
        )
        return [{"type": "text", "text": packet_str}]

    # PURPOSE: [L2-auto] Boot コンテキスト (/boot 相当) — API 優先・ローカルフォールバック
    async def _handle_boot_context(self, arguments: dict) -> list[dict]:
        """GET /api/symploke/boot-context を優先し、失敗時は get_boot_context を同期実行。"""
        import urllib.request
        import urllib.parse

        mode = arguments.get("mode", "standard")
        if mode not in ("fast", "standard", "detailed"):
            mode = "standard"
        context = arguments.get("context")
        timeout_sec = int(arguments.get("timeout_sec", 90))
        timeout_sec = max(10, min(300, timeout_sec))

        api_base = os.environ.get("HGK_API_BASE", "http://127.0.0.1:9696").rstrip("/")

        def fetch_via_api() -> dict:
            params = [("mode", mode), ("timeout", str(timeout_sec))]
            if context is not None and str(context).strip():
                params.append(("context", str(context)))
            qs = urllib.parse.urlencode(params)
            url = f"{api_base}/api/symploke/boot-context?{qs}"
            req = urllib.request.Request(url)
            client_timeout = max(120.0, float(timeout_sec) + 30.0)
            with urllib.request.urlopen(req, timeout=client_timeout) as response:
                return json.loads(response.read().decode("utf-8"))

        def fetch_local() -> dict:
            from mekhane.symploke.boot_integration import get_boot_context
            return get_boot_context(mode=mode, context=context)

        try:
            data = await asyncio.to_thread(fetch_via_api)
            axes = data.get("axes") or {}
            summary = data.get("summary") or ""
            if not axes or summary.startswith("Timeout"):
                raise ValueError("empty axes or API timeout")
            if not axes.get("formatted"):
                raise ValueError("missing formatted in axes (API)")
            result_body = {
                "source": "api",
                "mode": data.get("mode", mode),
                "summary": summary,
                "axes": axes,
            }
        except Exception as e:  # noqa: BLE001
            log(f"boot_context API fallback: {e}")
            try:
                axes = await asyncio.to_thread(fetch_local)
                result_body = {
                    "source": "local",
                    "mode": mode,
                    "summary": "Boot context loaded via get_boot_context (local)",
                    "axes": axes,
                }
            except Exception as e2:  # noqa: BLE001
                err_text = build_return_packet(
                    backend="boot_context",
                    status="error",
                    result={"error": str(e2), "api_error": str(e)},
                    task_id=arguments.get("task_id"),
                    decisions_log_path=arguments.get("decisions_log_path"),
                )
                return [{"type": "text", "text": err_text}]

        packet_str = build_return_packet(
            backend="boot_context",
            status="success",
            result=result_body,
            task_id=arguments.get("task_id"),
            decisions_log_path=arguments.get("decisions_log_path"),
        )
        return [{"type": "text", "text": packet_str}]

    # axis router 自身のツール名集合 — 再帰呼出防止ガード (ゲーデル的自己言及防止)
    ROUTER_SELF_TOOLS = frozenset({
        "recommend", "execute",
        "daimonion_judge", "daimonion_status",
        "axis_stats",
        "secretary", "boot_context",
        "aisthetikon", "dianoetikon", "poietikon",
    })

    # PURPOSE: [L2-auto] バックエンド経由でツールを委託実行 (S-006 Stage 2)
    async def _handle_execute(self, arguments: dict) -> list[dict]:
        """指定されたバックエンドのツールを Hub 経由で実行する。

        設計思想 (代替案 B — /ele+ 反駁結果):
          recommend = 知る (どのツールを呼ぶべきか)
          execute = 行う (選択されたツールを実行する)
          引数構築は Claude の責務。Hub は実行のみ担う。
        """
        backend_name = arguments.get("backend", "").strip()
        tool_name = arguments.get("tool", "").strip()
        tool_args = arguments.get("arguments", {})
        available_backends = [
            name for name in self._visible_backends()
            if self._backend_connected(name)
        ]

        # エラー返却ヘルパー
        def error_packet(err_result: dict):
            return [{"type": "text", "text": build_return_packet(
                backend=backend_name or "execute",
                status="error",
                result=err_result,
                task_id=arguments.get("task_id"),
                decisions_log_path=arguments.get("decisions_log_path")
            )}]

        # バリデーション
        if not backend_name or not tool_name:
            return error_packet({"error": "backend と tool は必須パラメータです"})

        if self.is_axis_router:
            backend_axis = get_backend_axis(backend_name)
            if backend_axis and backend_axis != self.axis:
                return error_packet({
                    "error": f"バックエンド '{backend_name}' は axis '{self.axis}' の外です",
                    "available_backends": available_backends,
                })

        # 再帰ガード: axis router 自身のツールへの委託を禁止
        if tool_name in self.ROUTER_SELF_TOOLS:
            return error_packet({
                "error": f"自己言及禁止: axis router のツール '{tool_name}' は execute で実行できません",
                "reason": "axis router は自身の品質を自身では評価できない (ゲーデル的制約)",
                "suggestion": f"'{tool_name}' は直接呼んでください",
            })

        # gemini-cli 特殊パス: MCP ではなく subprocess で実行
        if backend_name == "gemini-cli":
            return await self._handle_gemini_cli(tool_name, tool_args, arguments)

        # CLI Agent 特殊パス: copilot / cursor-agent を subprocess で実行
        # (codex は codex-mcp へのフォールバック連携があるため別処理)
        if backend_name in ("copilot", "cursor-agent"):
            return await self._handle_cli_agent(backend_name, tool_name, tool_args, arguments)

        # codex subprocess: codex-mcp が接続済みならそちらにリダイレクト
        if backend_name == "codex":
            codex_mcp = self.backends.get("codex-mcp")
            if codex_mcp and codex_mcp.is_connected:
                # SOURCE: codex mcp-server v0.118.0 は "codex" と "codex-reply" の 2 ツール
                # cli_agent_ask → "codex" (セッション開始) にマッピング
                mcp_tool = "codex" if tool_name == "cli_agent_ask" else tool_name
                log(f"execute: redirecting codex → codex-mcp.{mcp_tool} (MCP mode)")
                arguments_copy = dict(arguments)
                arguments_copy["backend"] = "codex-mcp"
                arguments_copy["tool"] = mcp_tool
                return await self._handle_execute(arguments_copy)
            # codex-mcp が使えない場合は subprocess にフォールバック
            return await self._handle_cli_agent(backend_name, tool_name, tool_args, arguments)

        if backend_name in self._delegated_backend_names:
            if not self._upstream_axis:
                return error_packet({
                    "error": f"remote axis '{self.axis}' への upstream が未設定です",
                    "available_backends": available_backends,
                })
            if not self._upstream_axis.is_connected:
                log(f"execute: upstream axis {self.axis} not connected, attempting reconnect...")
                reconnected = await self._upstream_axis._try_reconnect(force=True)
                if not reconnected:
                    return error_packet({
                        "error": f"remote axis '{self.axis}' に接続されていません (再接続も失敗)",
                        "available_backends": available_backends,
                    })
            return await self._upstream_axis.call_tool("execute", arguments)

        # バックエンド接続チェック (未接続時は即座に再接続を試みる)
        conn = self.backends.get(backend_name)
        if not conn:
            return error_packet({
                "error": f"バックエンド '{backend_name}' は登録されていません",
                "available_backends": available_backends,
            })
        if not conn.is_connected:
            log(f"execute: {backend_name} not connected, attempting reconnect...")
            reconnected = await conn._try_reconnect(force=True)
            if not reconnected:
                return error_packet({
                    "error": f"バックエンド '{backend_name}' に接続されていません (再接続も失敗)",
                    "available_backends": available_backends,
                })

        # ツール存在チェック
        available_tools = [t["name"] for t in conn.tools]
        if tool_name not in available_tools:
            return error_packet({
                "error": f"ツール '{tool_name}' はバックエンド '{backend_name}' に存在しません",
                "available_tools": available_tools,
            })

        # 実行
        start = time.time()
        try:
            result = await conn.call_tool(tool_name, tool_args)
            elapsed = time.time() - start
            log(f"execute: {backend_name}.{tool_name} OK ({elapsed:.1f}s)")

            # 実行ログを記録
            self._call_log.append({
                "time": datetime.now(timezone.utc).isoformat(),
                "source": "execute",
                "backend": backend_name,
                "tool": tool_name,
                "elapsed_ms": round(elapsed * 1000),
                "success": True,
            })

            # 戻り値を V-009 パケットにカプセル化
            parsed_result = []
            for item in result:
                if item.get("type") == "text":
                    try:
                        parsed_result.append(json.loads(item.get("text", "")))
                    except json.JSONDecodeError:
                        parsed_result.append(item.get("text", ""))
                else:
                    parsed_result.append(item)
            
            if len(parsed_result) == 1:
                parsed_result = parsed_result[0]

            packet_str = build_return_packet(
                backend=backend_name,
                status="success",
                result=parsed_result,
                task_id=arguments.get("task_id"),
                elapsed_ms=round(elapsed * 1000),
                decisions_log_path=arguments.get("decisions_log_path")
            )
            return [{"type": "text", "text": packet_str}]

        except Exception as e:  # noqa: BLE001
            elapsed = time.time() - start
            log(f"execute: {backend_name}.{tool_name} FAILED ({elapsed:.1f}s): {e}")

            self._call_log.append({
                "time": datetime.now(timezone.utc).isoformat(),
                "source": "execute",
                "backend": backend_name,
                "tool": tool_name,
                "elapsed_ms": round(elapsed * 1000),
                "success": False,
                "error": str(e),
            })

            error_obj = {
                "error": f"実行失敗: {e}",
                "backend": backend_name,
                "tool": tool_name,
            }
            packet_str = build_return_packet(
                backend=backend_name,
                status="error",
                result=error_obj,
                task_id=arguments.get("task_id"),
                elapsed_ms=round(elapsed * 1000),
                decisions_log_path=arguments.get("decisions_log_path")
            )
            return [{"type": "text", "text": packet_str}]

    # PURPOSE: [L2-auto] gemini-cli バックエンド — subprocess 経由で gemini CLI を呼び出す
    GEMINI_CLI_TOOLS = {
        "gemini_ask": {
            "description": "Gemini CLI で単発プロンプトを実行する (無料, L0-L1)",
            "params": ["prompt", "model", "sandbox"],
        },
        "gemini_research": {
            "description": "Gemini CLI + MCP サーバーで調査を実行する (無料, L1)",
            "params": ["prompt", "model", "mcp_servers", "sandbox"],
        },
    }

    async def _handle_gemini_cli(
        self, tool_name: str, tool_args: dict, arguments: dict
    ) -> list[dict]:
        """gemini-cli バックエンドの実行ハンドラ。

        subprocess で `gemini` CLI を呼び出し、stdout を返す。
        MCP サーバーではないため BackendConnection を使わない。
        """
        # ツール存在チェック
        if tool_name not in self.GEMINI_CLI_TOOLS:
            return [{"type": "text", "text": build_return_packet(
                backend="gemini-cli",
                status="error",
                result={
                    "error": f"ツール '{tool_name}' は gemini-cli に存在しません",
                    "available_tools": list(self.GEMINI_CLI_TOOLS.keys()),
                },
                task_id=arguments.get("task_id"),
                decisions_log_path=arguments.get("decisions_log_path"),
            )}]

        # gemini CLI の存在確認 (wrapper 優先 — gcloud config 汚染遮断)
        _wrapper = os.path.expanduser("~/.local/bin/gemini-wrapper")
        if os.path.isfile(_wrapper) and os.access(_wrapper, os.X_OK):
            gemini_path = _wrapper
        else:
            gemini_path = shutil.which("gemini-wrapper") or shutil.which("gemini")
        if not gemini_path:
            return [{"type": "text", "text": build_return_packet(
                backend="gemini-cli",
                status="error",
                result={"error": "gemini CLI が PATH に見つかりません"},
                task_id=arguments.get("task_id"),
                decisions_log_path=arguments.get("decisions_log_path"),
            )}]

        prompt = tool_args.get("prompt", "").strip()
        if not prompt:
            return [{"type": "text", "text": build_return_packet(
                backend="gemini-cli",
                status="error",
                result={"error": "prompt は必須パラメータです"},
                task_id=arguments.get("task_id"),
                decisions_log_path=arguments.get("decisions_log_path"),
            )}]

        # コマンド構築
        cmd = [gemini_path, "-p", prompt]

        # モデル指定
        model = tool_args.get("model", "").strip()
        if model:
            cmd.extend(["-m", model])

        # sandbox (--yolo 相当 — 非インタラクティブ実行)
        sandbox = tool_args.get("sandbox", True)
        if sandbox:
            cmd.append("--sandbox")
        else:
            cmd.append("--yolo")

        # MCP サーバー指定 (gemini_research のみ)
        if tool_name == "gemini_research":
            mcp_servers = tool_args.get("mcp_servers", [])
            if isinstance(mcp_servers, list) and mcp_servers:
                cmd.extend(["--allowed-mcp-server-names", ",".join(mcp_servers)])

        # gcloud config 汚染遮断 (gemini-wrapper と同等の環境変数)
        env = {
            **os.environ,
            "CLOUDSDK_CONFIG": "/dev/null",
            "GOOGLE_CLOUD_PROJECT": "",
            "GOOGLE_CLOUD_PROJECT_ID": "",
            "GCLOUD_PROJECT": "",
        }

        # アカウント自動ローテーション (実行前に次のアカウントに切替)
        rotate_path = shutil.which("gemini-rotate")
        if rotate_path:
            try:
                await asyncio.to_thread(
                    _subprocess.run,
                    [rotate_path, "next"],
                    capture_output=True, text=True, timeout=5,
                    env=env,
                )
            except Exception:  # noqa: BLE001
                pass  # ローテーション失敗は無視 (現在のアカウントで続行)

        log(f"gemini-cli: {' '.join(cmd[:6])}...")
        start = time.time()
        cwd = str(_PROJECT_ROOT)
        max_429_retries = 5

        for attempt in range(max_429_retries + 1):
            try:
                result = await asyncio.to_thread(
                    _subprocess.run,
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5分タイムアウト
                    cwd=cwd,
                    env=env,
                )
                elapsed = time.time() - start

                stdout = result.stdout.strip()
                stderr = result.stderr.strip()

                if result.returncode != 0:
                    # 429 quota exhaustion → アカウントをローテーションしてリトライ
                    if "429" in stderr and attempt < max_429_retries and rotate_path:
                        log(f"gemini-cli: 429 detected, rotating account (attempt {attempt + 1}/{max_429_retries})")
                        try:
                            await asyncio.to_thread(
                                _subprocess.run,
                                [rotate_path, "next"],
                                capture_output=True, text=True, timeout=5,
                                env=env,
                            )
                        except Exception:  # noqa: BLE001
                            pass
                        continue

                    log(f"gemini-cli: FAILED (rc={result.returncode}, {elapsed:.1f}s)")
                    return [{"type": "text", "text": build_return_packet(
                        backend="gemini-cli",
                        status="error",
                        result={
                            "error": f"gemini CLI exited with code {result.returncode}",
                            "stderr": stderr[:2000] if stderr else None,
                            "stdout": stdout[:2000] if stdout else None,
                            "attempts": attempt + 1,
                        },
                        task_id=arguments.get("task_id"),
                        elapsed_ms=round(elapsed * 1000),
                        decisions_log_path=arguments.get("decisions_log_path"),
                    )}]

                log(f"gemini-cli: OK ({elapsed:.1f}s, {len(stdout)} chars)")

                self._call_log.append({
                    "time": datetime.now(timezone.utc).isoformat(),
                    "source": "execute",
                    "backend": "gemini-cli",
                    "tool": tool_name,
                    "elapsed_ms": round(elapsed * 1000),
                    "success": True,
                })

                return [{"type": "text", "text": build_return_packet(
                    backend="gemini-cli",
                    status="success",
                    result={
                        "output": stdout,
                        "tool": tool_name,
                        "model": model or "default",
                        "chars": len(stdout),
                        "attempts": attempt + 1,
                    },
                    task_id=arguments.get("task_id"),
                    elapsed_ms=round(elapsed * 1000),
                    decisions_log_path=arguments.get("decisions_log_path"),
                )}]

            except _subprocess.TimeoutExpired:
                elapsed = time.time() - start
                log(f"gemini-cli: TIMEOUT ({elapsed:.1f}s)")
                return [{"type": "text", "text": build_return_packet(
                    backend="gemini-cli",
                    status="error",
                    result={"error": "gemini CLI timed out (300s limit)"},
                    task_id=arguments.get("task_id"),
                    elapsed_ms=round(elapsed * 1000),
                    decisions_log_path=arguments.get("decisions_log_path"),
                )}]
            except Exception as e:  # noqa: BLE001
                elapsed = time.time() - start
                log(f"gemini-cli: ERROR ({elapsed:.1f}s): {e}")

                self._call_log.append({
                    "time": datetime.now(timezone.utc).isoformat(),
                    "source": "execute",
                    "backend": "gemini-cli",
                    "tool": tool_name,
                    "elapsed_ms": round(elapsed * 1000),
                    "success": False,
                    "error": str(e),
                })

                return [{"type": "text", "text": build_return_packet(
                    backend="gemini-cli",
                    status="error",
                    result={"error": str(e)},
                    task_id=arguments.get("task_id"),
                    elapsed_ms=round(elapsed * 1000),
                    decisions_log_path=arguments.get("decisions_log_path"),
                )}]

        # max_429_retries を使い切った場合 (全アカウント quota exhaustion)
        elapsed = time.time() - start
        log(f"gemini-cli: ALL ACCOUNTS EXHAUSTED ({elapsed:.1f}s, {max_429_retries} retries)")
        return [{"type": "text", "text": build_return_packet(
            backend="gemini-cli",
            status="error",
            result={
                "error": f"全アカウント quota exhaustion ({max_429_retries} retries)",
                "attempts": max_429_retries + 1,
            },
            task_id=arguments.get("task_id"),
            elapsed_ms=round(elapsed * 1000),
            decisions_log_path=arguments.get("decisions_log_path"),
        )}]

    # PURPOSE: [L2-auto] CLI Agent バックエンド — copilot / codex / cursor-agent を subprocess 経由で呼び出す
    CLI_AGENT_TOOLS = {
        "cli_agent_ask": {
            "description": "CLI Agent (copilot/codex/cursor-agent) で単発プロンプトを実行する",
            "params": ["prompt", "model"],
        },
    }

    async def _handle_cli_agent(
        self, backend_name: str, tool_name: str, tool_args: dict, arguments: dict
    ) -> list[dict]:
        """CLI Agent バックエンドの実行ハンドラ。

        cli_agent_bridge.run_cli_agent() を asyncio.to_thread() で呼び出す。
        """
        from mekhane.ochema.cli_agent_bridge import run_cli_agent

        prompt = tool_args.get("prompt", "").strip()
        if not prompt:
            return [{"type": "text", "text": build_return_packet(
                backend=backend_name,
                status="error",
                result={"error": "prompt は必須パラメータです"},
                task_id=arguments.get("task_id"),
                decisions_log_path=arguments.get("decisions_log_path"),
            )}]

        model = tool_args.get("model", "").strip() or None

        log(f"cli-agent ({backend_name}): prompt={prompt[:80]}... model={model}")
        start = time.time()

        try:
            result = await asyncio.to_thread(
                run_cli_agent,
                prompt,
                tool=backend_name,
                model=model,
                timeout=300,
            )
            elapsed = time.time() - start

            if result.get("status") != "ok":
                log(f"cli-agent ({backend_name}): FAILED ({elapsed:.1f}s)")
                return [{"type": "text", "text": build_return_packet(
                    backend=backend_name,
                    status="error",
                    result=result,
                    task_id=arguments.get("task_id"),
                    elapsed_ms=round(elapsed * 1000),
                    decisions_log_path=arguments.get("decisions_log_path"),
                )}]

            log(f"cli-agent ({backend_name}): OK ({elapsed:.1f}s, {result.get('chars', 0)} chars)")

            self._call_log.append({
                "time": datetime.now(timezone.utc).isoformat(),
                "source": "execute",
                "backend": backend_name,
                "tool": tool_name,
                "elapsed_ms": round(elapsed * 1000),
                "success": True,
            })

            return [{"type": "text", "text": build_return_packet(
                backend=backend_name,
                status="success",
                result=result,
                task_id=arguments.get("task_id"),
                elapsed_ms=round(elapsed * 1000),
                decisions_log_path=arguments.get("decisions_log_path"),
            )}]

        except Exception as e:  # noqa: BLE001
            elapsed = time.time() - start
            log(f"cli-agent ({backend_name}): ERROR ({elapsed:.1f}s): {e}")

            self._call_log.append({
                "time": datetime.now(timezone.utc).isoformat(),
                "source": "execute",
                "backend": backend_name,
                "tool": tool_name,
                "elapsed_ms": round(elapsed * 1000),
                "success": False,
                "error": str(e),
            })

            return [{"type": "text", "text": build_return_packet(
                backend=backend_name,
                status="error",
                result={"error": str(e)},
                task_id=arguments.get("task_id"),
                elapsed_ms=round(elapsed * 1000),
                decisions_log_path=arguments.get("decisions_log_path"),
            )}]

    # PURPOSE: [L2-auto] Vision B 統合秘書パイプライン
    async def _handle_secretary(self, arguments: dict) -> list[dict]:
        """Vision B: ルーティング脳 + 実行 + 反証 + 監査を一括実行し判断材料パッケージを返す。

        Phase A: Routing   — Gemini 3.1 Pro (or Claude Opus) で最適ツール計画を生成
        Phase B1: Execute  — 計画のステップを順次実行
        Phase B2: Shadow   — 反証を B1 と並列生成
        Phase C: Gate      — Sekisho で BC コンプライアンス監査
        Phase D: Package   — 全結果を判断材料パッケージに組立
        """
        import uuid as _uuid

        task_desc = arguments.get("task_description", "").strip()
        if not task_desc:
            return [{"type": "text", "text": "Error: task_description is required"}]

        task_id = arguments.get("task_id") or f"sec-{_uuid.uuid4().hex[:8]}"
        max_steps = arguments.get("max_steps", 5)
        routing_model = arguments.get("routing_model") or PIPELINE_CONFIG.get(
            "secretary_routing_model", "gemini-3.1-pro-preview"
        )
        skip_shadow = arguments.get("skip_shadow", False)
        skip_gate = arguments.get("skip_gate", False)
        decisions_log_path = arguments.get("decisions_log_path")

        overall_start = time.time()

        # ====== Phase A: ROUTING ======
        log(f"secretary[{task_id}] Phase A: routing ({routing_model})")
        routing_result = await self._secretary_route(task_desc, routing_model, max_steps)

        if routing_result is None:
            elapsed_ms = round((time.time() - overall_start) * 1000)
            packet = build_secretary_packet(
                task_id=task_id, task_description=task_desc,
                status="error", elapsed_ms=elapsed_ms,
                routing={"model": routing_model, "reasoning": "routing failed", "plan": [], "latency_ms": elapsed_ms},
                decisions_log_path=decisions_log_path,
            )
            return [{"type": "text", "text": packet}]

        plan = routing_result.get("plan", [])
        log(f"secretary[{task_id}] Phase A: {len(plan)} steps planned")

        # ====== Phase B: EXECUTION + SHADOW (parallel) ======
        shadow = self._get_shadow()
        exec_coro = self._secretary_execute(plan, task_id)

        if not skip_shadow and shadow and shadow.enabled:
            shadow_coro = shadow.shadow_for_secretary(task_desc, plan)
            log(f"secretary[{task_id}] Phase B: execute + shadow (parallel)")
            exec_results, shadow_result = await asyncio.gather(
                exec_coro, shadow_coro, return_exceptions=True,
            )
        else:
            log(f"secretary[{task_id}] Phase B: execute only")
            exec_results = await exec_coro
            shadow_result = None

        # asyncio.gather with return_exceptions=True: unpack
        if isinstance(exec_results, BaseException):
            log(f"secretary[{task_id}] execution error: {exec_results}")
            exec_results = []
        if isinstance(shadow_result, BaseException):
            log(f"secretary[{task_id}] shadow error (non-fatal): {shadow_result}")
            shadow_result = None

        # ====== Phase C: GATE ======
        gate_result = None
        if not skip_gate and PIPELINE_CONFIG.get("secretary_gate_always", True):
            log(f"secretary[{task_id}] Phase C: gate")
            gate_result = await self._secretary_gate(exec_results, task_desc)

        # ====== Phase D: PACKAGE ASSEMBLY ======
        elapsed_ms = round((time.time() - overall_start) * 1000)

        # status 判定
        success_count = sum(1 for r in exec_results if r.get("status") == "success")
        if success_count > 0:
            status = "success"
        elif plan:
            status = "partial"
        else:
            status = "error"

        # counter_evidence をシリアライズ可能な dict に変換
        ce_dict = None
        if shadow_result is not None:
            ce_dict = {
                "findings": [
                    {"category": f.category, "content": f.content, "severity": f.severity}
                    for f in shadow_result.findings
                ],
                "counterpoint": shadow_result.counterpoint,
                "confidence": shadow_result.confidence,
                "model": shadow_result.model,
                "latency_ms": shadow_result.latency_ms,
            }

        packet = build_secretary_packet(
            task_id=task_id,
            task_description=task_desc,
            status=status,
            elapsed_ms=elapsed_ms,
            routing=routing_result,
            results=exec_results,
            counter_evidence=ce_dict,
            gate=gate_result,
            decisions_log_path=decisions_log_path,
        )
        log(f"secretary[{task_id}] Phase D: {status} ({elapsed_ms}ms, {len(exec_results)} steps, shadow={'yes' if ce_dict else 'no'}, gate={gate_result.get('verdict', 'SKIP') if gate_result else 'SKIP'})")
        return [{"type": "text", "text": packet}]

    # PURPOSE: [L2-auto] Secretary Phase A: ルーティング脳
    async def _secretary_route(
        self, task_desc: str, model: str, max_steps: int
    ) -> Optional[dict]:
        """CortexClient で routing plan を生成する。失敗時は None。"""
        catalog_text = self._build_catalog_text()

        prompt = (
            "あなたは Hegemonikon Hub の Routing Brain です。\n"
            "タスク記述を分析し、最適な実行計画を JSON で返してください。\n\n"
            "## 制約\n"
            "- 利用可能なツールは下のカタログのみ\n"
            "- ✅ は接続済み、❌ は未接続。接続済みを強く優先\n"
            f"- ステップは1-{max_steps}個。不必要に多くしない\n"
            "- 各ステップの arguments は実際のツールスキーマに従う\n"
            "- ステップ間に依存関係がある場合は depends_on で明示\n\n"
            "## 出力形式 (JSON のみ、他のテキスト禁止)\n"
            '{\n'
            '  "reasoning": "タスク分析と計画の根拠 (2-3文)",\n'
            '  "plan": [\n'
            '    {\n'
            '      "step": 1,\n'
            '      "backend": "バックエンド名",\n'
            '      "tool": "ツール名",\n'
            '      "arguments": { ... },\n'
            '      "reason": "選択理由 (1行)",\n'
            '      "depends_on": []\n'
            '    }\n'
            '  ]\n'
            '}\n\n'
            f"## ツールカタログ\n{catalog_text}\n\n"
            f"## タスク\n{task_desc}"
        )

        t0 = time.time()
        try:
            # Ochema 経由で CortexClient を呼ぶ
            ochema_conn = self.backends.get("ochema")
            if not ochema_conn or not ochema_conn.is_connected:
                log("secretary route: ochema not connected")
                return None

            result = await ochema_conn.call_tool("ask_cortex", {
                "message": prompt,
                "model": model,
                "max_tokens": PIPELINE_CONFIG.get("secretary_routing_max_tokens", 4096),
                "cached_content": "none",  # CAG 自動ルーティングを無効化 (routing brain 専用)
            })

            response_text = ""
            if result and isinstance(result, list):
                for item in result:
                    if isinstance(item, dict) and "text" in item:
                        response_text = item["text"]
                        break

            if not response_text:
                log("secretary route: empty response")
                return None

            # ask_cortex は "## Response\n{content}" 形式でラップするため展開
            import re as _re
            if "## Response" in response_text:
                response_text = response_text.split("## Response", 1)[1].lstrip()
            log(f"secretary route: response_text[:200]={response_text[:200]!r}")

            # JSON 抽出
            json_match = _re.search(r'```json\s*\n?(.*?)\n?\s*```|(\{.*\})', response_text, _re.DOTALL)
            if not json_match:
                log(f"secretary route: no JSON found in response (full={response_text[:500]!r})")
                return None

            json_str = json_match.group(1) or json_match.group(2)
            data = json.loads(json_str)
            latency_ms = round((time.time() - t0) * 1000)

            return {
                "model": model,
                "reasoning": data.get("reasoning", ""),
                "plan": data.get("plan", [])[:max_steps],
                "latency_ms": latency_ms,
            }

        except Exception as e:  # noqa: BLE001
            log(f"secretary route failed: {e}")
            return None

    # PURPOSE: [L2-auto] Secretary Phase B1: 計画実行
    async def _secretary_execute(
        self, plan: list[dict], task_id: str
    ) -> list[dict]:
        """routing plan のステップを順次実行する。"""
        results = []
        for step in plan:
            backend_name = step.get("backend", "")
            tool_name = step.get("tool", "")
            arguments = step.get("arguments", {})
            step_num = step.get("step", len(results) + 1)

            t0 = time.time()
            try:
                result = await self.call_tool(backend_name, tool_name, arguments)
                elapsed_ms = round((time.time() - t0) * 1000)

                # MCP result を data に変換
                data = result
                if isinstance(result, list) and result:
                    text_parts = [r.get("text", "") for r in result if isinstance(r, dict)]
                    data = "\n".join(text_parts) if text_parts else result

                results.append({
                    "step": step_num, "backend": backend_name, "tool": tool_name,
                    "status": "success", "data": data, "elapsed_ms": elapsed_ms,
                })
                log(f"secretary exec step {step_num}: {backend_name}.{tool_name} OK ({elapsed_ms}ms)")

            except Exception as e:  # noqa: BLE001
                elapsed_ms = round((time.time() - t0) * 1000)
                results.append({
                    "step": step_num, "backend": backend_name, "tool": tool_name,
                    "status": "error", "data": {"error": str(e)}, "elapsed_ms": elapsed_ms,
                })
                log(f"secretary exec step {step_num}: {backend_name}.{tool_name} FAILED ({elapsed_ms}ms): {e}")

        return results

    # PURPOSE: [L2-auto] Secretary Phase C: Gate 監査
    async def _secretary_gate(
        self, exec_results: list[dict], task_desc: str
    ) -> Optional[dict]:
        """Sekisho で実行結果全体を BC 監査する。"""
        sekisho_conn = self.backends.get("sekisho")
        if not sekisho_conn or not sekisho_conn.is_connected:
            return {"verdict": "SKIP", "reason": "sekisho offline", "violations": [], "latency_ms": 0}

        # 実行結果をドラフトテキストに変換
        draft_parts = [f"## タスク\n{task_desc}\n"]
        for r in exec_results:
            data_str = r.get("data", "")
            if isinstance(data_str, dict):
                data_str = json.dumps(data_str, ensure_ascii=False)
            elif not isinstance(data_str, str):
                data_str = str(data_str)
            draft_parts.append(f"### Step {r.get('step', '?')}: {r.get('backend', '?')}.{r.get('tool', '?')}\n{data_str[:2000]}\n")

        draft_response = "\n".join(draft_parts)

        t0 = time.time()
        try:
            result = await sekisho_conn.call_tool("sekisho_gate", {
                "draft_response": draft_response,
                "reasoning": "secretary pipeline auto-gate",
                "depth": PIPELINE_CONFIG.get("secretary_gate_depth", "L1"),
            })
            latency_ms = round((time.time() - t0) * 1000)

            result_text = result[0].get("text", "") if result else ""
            # sekisho_gate はフォーマット済みテキストを返すため、
            # JSON パース → テキストパース の順でフォールバック
            import re as _re_gate
            gate_data: dict = {}
            try:
                json_m = _re_gate.search(r'\{.*\}', result_text, _re_gate.DOTALL)
                if json_m:
                    gate_data = json.loads(json_m.group())
            except (json.JSONDecodeError, ValueError):
                pass

            if gate_data.get("verdict"):
                verdict = gate_data["verdict"]
            elif "修正推奨" in result_text:
                # _format_result BLOCK: "**判定**: 修正推奨"
                verdict = "BLOCK"
            elif "gate_token=" in result_text or "SEKISHO GATE" in result_text:
                # _format_result PASS: "🪞 **SEKISHO GATE**" + gate_token
                verdict = "PASS"
            else:
                verdict = "UNKNOWN"

            # gate_token をテキストから抽出
            token = gate_data.get("gate_token", "")
            if not token:
                token_m = _re_gate.search(r'gate_token=`([^`]+)`', result_text)
                if token_m:
                    token = token_m.group(1)

            return {
                "verdict": verdict,
                "violations": gate_data.get("violations", []),
                "gate_token": token,
                "latency_ms": latency_ms,
            }

        except Exception as e:  # noqa: BLE001
            latency_ms = round((time.time() - t0) * 1000)
            log(f"secretary gate failed: {e}")
            return {"verdict": "SKIP", "reason": str(e), "violations": [], "latency_ms": latency_ms}

    # PURPOSE: [L2-auto] ツールカタログテキスト構築 (secretary + recommend 共用)
    def _build_catalog_text(self) -> str:
        """TOOL_CATALOG を接続状態付きテキストに変換。"""
        allowed_backends = set(self._visible_backends())
        lines = []
        for entry in self.TOOL_CATALOG:
            if entry["tool"] in self.ROUTER_SELF_TOOLS:
                continue
            if entry["backend"] not in allowed_backends:
                continue
            connected = (
                entry["backend"] in allowed_backends
                and self._backend_connected(entry["backend"])
            )
            status = "✅" if connected else "❌"
            lines.append(f"- {status} {entry['backend']}/{entry['tool']}: {entry['desc']}")
        return "\n".join(lines)

    # PURPOSE: [L2-auto] ツールカタログ — LLM 推奨のプロンプト素材
    TOOL_CATALOG: list[dict[str, str]] = [
        {"backend": "hermeneus", "tool": "hermeneus_run", "desc": "CCL/WF の解析・実行。CCL 式 (/noe, /bou 等) やワークフローを実行する"},
        {"backend": "hermeneus", "tool": "hermeneus_dispatch", "desc": "CCL 式の構文解析 (実行せず AST のみ返す)"},
        {"backend": "digestor",  "tool": "paper_search", "desc": "学術論文の検索。Semantic Scholar API 経由"},
        {"backend": "digestor",  "tool": "paper_details", "desc": "特定論文の詳細情報取得 (DOI/arXiv ID 指定)"},
        {"backend": "phantazein", "tool": "search", "desc": "統合知識検索 (scope=all/papers/code; 論文のみは scope=papers)。旧 mneme_search / search_papers はエイリアス"},
        {"backend": "phantazein", "tool": "check", "desc": "検証・診断 (action=proof/mece/dejavu/...)。旧 dejavu_check / dendron_check 等はエイリアス"},
        {"backend": "phantazein", "tool": "graph", "desc": "知識グラフ・統計 (action=backlinks/stats/index/sources)。旧 mneme_backlinks 等はエイリアス"},
        {"backend": "periskope", "tool": "periskope_research", "desc": "Deep Research — 多ソース並列検索→合成→引用検証→レポート。2-4分かかる"},
        {"backend": "periskope", "tool": "periskope_search", "desc": "軽量な多ソース並列検索 (合成なし)。10-15秒"},
        {"backend": "sympatheia","tool": "basanos_scan", "desc": "L0 静的解析 — Python ファイルの AST スキャン"},
        {"backend": "sympatheia","tool": "sympatheia_verify_on_edit", "desc": "ファイル変更後の関連テスト自動実行"},
        {"backend": "sekisho",   "tool": "sekisho_gate", "desc": "BC 違反チェック監査。応答ドラフトを検証"},
        {"backend": "ochema",    "tool": "ask_cortex", "desc": "Gemini への直接相談 (高速)"},
        {"backend": "ochema",    "tool": "ask_with_tools", "desc": "Gemini にツール使用を許可した相談 (ファイル読み書き可)"},
        {"backend": "phantazein-boot","tool": "phantazein_boot", "desc": "セッション開始コンテキスト生成"},
        {"backend": "phantazein-boot","tool": "phantazein_health", "desc": "全 MCP サーバーのヘルスチェック"},
        {"backend": "typos",     "tool": "typos_compile", "desc": "TYPOS v8 式のコンパイル (マークダウン出力)"},
        {"backend": "typos",     "tool": "typos_validate", "desc": "TYPOS v8 式の構文検証"},
        {"backend": "opsis",     "tool": "opsis_observe", "desc": "Web ページの DOM を Ref ID 付き a11y snapshot として取得。HGK 認知動詞アノテーション付き"},
        {"backend": "opsis",     "tool": "opsis_act", "desc": "Ref ID 指定で DOM 要素を操作 (click, fill, select 等)"},
        {"backend": "opsis",     "tool": "opsis_extract", "desc": "Web ページから構造化データを抽出 (テキスト/HTML/属性値/JS eval)"},
    ]

    # PURPOSE: [L2-auto] LLM ベースのバックエンド推奨 (ochema ask_cortex 経由)
    async def _recommend_backend_llm(
        self, task_desc: str, top_k: int, *, fep_group: str | None = None
    ) -> list[dict] | None:
        """Gemini Flash にタスク記述とツールカタログを渡し、推奨を返す。

        Args:
            fep_group: "S"|"I"|"E" で絞り込み。None なら全バックエンド。

        Returns:
            推奨リスト (成功時) / None (ochema 不通・パースエラー時)
        """
        # ochema バックエンドが接続されているか確認
        ochema_conn = self.backends.get("ochema")
        if not ochema_conn or not ochema_conn.is_connected:
            log("ochema 未接続 — LLM 推奨をスキップ")
            return None

        # FEP グループフィルタ: 対象バックエンド名の集合
        allowed_backends: set[str] | None = None
        if fep_group:
            allowed_backends = set(self._visible_backends(fep_group=fep_group))
        elif self.is_axis_router:
            allowed_backends = set(self._visible_backends())

        # ツールカタログからプロンプトを構築
        catalog_lines = []
        for entry in self.TOOL_CATALOG:
            # axis router 自身のツールを除外
            if entry["tool"] in self.ROUTER_SELF_TOOLS:
                continue
            # FEP グループフィルタ
            if allowed_backends is not None and entry["backend"] not in allowed_backends:
                continue
            connected = self._backend_connected(entry["backend"])
            status = "✅" if connected else "❌"
            catalog_lines.append(
                f"- {status} {entry['backend']}/{entry['tool']}: {entry['desc']}"
            )
        catalog_text = "\n".join(catalog_lines)

        if not catalog_lines:
            log(f"FEP グループ '{fep_group}' のカタログが空 — LLM 推奨をスキップ")
            return None

        prompt = (
            f"以下のツール一覧から、タスクに最適なツールを最大 {top_k} 件選んでください。\n"
            f"✅ は接続済み、❌ は未接続です。接続済みを優先してください。\n\n"
            f"## ツール一覧\n{catalog_text}\n\n"
            f"## タスク\n{task_desc}\n\n"
            f"## 出力形式\n"
            f"以下の JSON 配列のみを出力してください。説明文は不要です。\n"
            f'[{{"backend": "...", "tool": "...", "reason": "選んだ理由 (1行)"}}]'
        )

        try:
            result = await ochema_conn.call_tool("ask_cortex", {
                "message": prompt,
                "model": "gemini-3-flash-preview",
                "max_tokens": 1024,
            })

            # 応答テキストを取得
            response_text = ""
            if result and isinstance(result, list):
                for item in result:
                    if isinstance(item, dict) and "text" in item:
                        response_text = item["text"]
                        break

            if not response_text:
                log("ochema からの応答が空")
                return None

            # JSON 配列を抽出 (応答に余分なテキストがある可能性)
            import re as _re
            json_match = _re.search(r'\[.*\]', response_text, _re.DOTALL)
            if not json_match:
                log(f"LLM 応答から JSON を抽出できず: {response_text[:200]}")
                return None

            raw_recs = json.loads(json_match.group())
            if not isinstance(raw_recs, list):
                log("LLM 応答が配列でない")
                return None

            # 推奨を正規化して返す
            recommendations: list[dict] = []
            for rec in raw_recs[:top_k]:
                if not isinstance(rec, dict):
                    continue
                backend = rec.get("backend", "").strip()
                tool = rec.get("tool", "").strip()
                reason = rec.get("reason", "LLM 推奨").strip()
                if not backend or not tool:
                    continue
                # axis router 自身のツールが推奨されていたらスキップ
                if tool in self.ROUTER_SELF_TOOLS:
                    continue

                importance, complexity = get_tool_scores(tool)
                recommendations.append({
                    "backend": backend,
                    "tool": tool,
                    "reason": reason,
                    "match_score": importance,  # LLM 推奨では importance をスコアとして使用
                    "importance": importance,
                    "complexity": complexity,
                    "connected": self._backend_connected(backend),
                })

            if not recommendations:
                log("LLM 推奨結果が空 (全フィルタ後)")
                return None

            return recommendations

        except Exception as exc:  # noqa: BLE001
            log(f"LLM 推奨でエラー: {exc}")
            return None

    # PURPOSE: [L2-auto] バックエンド推奨ロジック (キーワードマッチ — フォールバック)
    @staticmethod
    def _is_cjk(text: str) -> bool:
        """テキストが CJK 文字を含むか判定する。"""
        import unicodedata
        return any(unicodedata.category(c).startswith(("Lo",)) for c in text)

    def _keyword_matches(self, keyword: str, task_lower: str) -> bool:
        """キーワードがタスク記述にマッチするか判定する。

        日本語 (CJK) キーワード: 部分文字列一致 (形態素分割不要)
        英語・記号キーワード: 単語境界 (\\b) 付き正規表現マッチ
        スラッシュ付き CCL: 先頭 / を含む完全な形でマッチ
        """
        import re
        if keyword.startswith("/"):
            # CCL 式 (/noe 等): 正確な前方一致 + 後続が英字でない
            return bool(re.search(re.escape(keyword) + r'(?![a-z])', task_lower))
        if self._is_cjk(keyword):
            # 日本語: 部分文字列一致
            return keyword in task_lower
        # 英語: 単語境界マッチ
        return bool(re.search(r'\b' + re.escape(keyword) + r'\b', task_lower))

    def _recommend_backend_keyword(self, task_desc: str, top_k: int, *, fep_group: str | None = None) -> list[dict]:
        """タスク記述からキーワードマッチでバックエンド+ツールを推奨する。

        Args:
            fep_group: "S"|"I"|"E" で絞り込み。None なら全バックエンド。
        """
        # キーワード → (バックエンド名, ツール名, 理由) のマッピング
        # 注意: 同バックエンドの複数エントリでキーワードは排他的にする (重複禁止)
        _KEYWORD_MAP = [
            # hermeneus: CCL / WF 関連
            (["ccl", "ワークフロー", "wf", "/noe", "/bou", "/zet", "/ene", "workflow"],
             "hermeneus", "hermeneus_run", "CCL/WF の解析・実行"),
            (["dispatch", "構文解析"],
             "hermeneus", "hermeneus_dispatch", "CCL 式の構文解析"),
            # digestor: 論文 / コンテンツ消化
            (["論文", "paper", "引用", "citation", "arxiv", "semantic"],
             "digestor", "paper_search", "学術論文の検索"),
            (["pdf", "消化", "digest", "読み込み"],
             "digestor", "digestor_analyze", "PDF/コンテンツの消化"),
            # phantazein: 知識検索 (旧 mneme)
            (["知識検索", "search", "ki", "gnosis", "sophia"],
             "phantazein", "search", "統合知識検索 (Gnōsis/Sophia)"),
            (["バックリンク", "backlink", "グラフ"],
             "phantazein", "graph", "知識グラフ (action=backlinks 等)"),
            (["デジャブ", "dejavu", "重複検出"],
             "phantazein", "check", "重複検出 (action=dejavu)"),
            (["dendron", "proof", "存在証明"],
             "phantazein", "check", "PROOF 検査 (action=proof)"),
            # periskope: 外部調査
            (["調査", "research", "deep research"],
             "periskope", "periskope_research", "Deep Research (多ソース検索+合成)"),
            (["外部検索"],
             "periskope", "periskope_search", "軽量外部検索"),
            # jules: コード PR
            (["pull request", "コードレビュー", "jules", "github", "コード生成"],
             "jules", "jules_create_task", "Jules を使ったコード PR 生成"),
            # sympatheia: コード品質
            (["テスト", "test", "basanos", "health"],
             "sympatheia", "basanos_scan", "L0 静的解析スキャン"),
            (["verify", "変更後テスト"],
             "sympatheia", "sympatheia_verify_on_edit", "編集後の関連テスト自動実行"),
            # sekisho: 監査
            (["監査", "audit", "sekisho", "関所"],
             "sekisho", "sekisho_gate", "BC 違反チェック監査"),
            # codex-mcp: Codex MCP — 実装・数学・形式化 (E群)
            (["codex", "openai", "gpt", "セカンドオピニオン", "実装", "数学", "latex",
              "証明", "形式化", "計算", "FrontierMath", "スクリプト自動化"],
             "codex-mcp", "codex", "Codex: 実装・数学形式化・スクリプト自動化 (GPT-5.4)"),
            # copilot: GitHub Copilot CLI — 1リクエスト高トークン (I群, リクエスト課金)
            (["copilot", "github copilot", "大コンテキスト", "高トークン",
              "全文解析", "大規模レビュー", "リクエスト制", "丸ごと読ませ"],
             "copilot", "cli_agent_ask", "Copilot: 1リクエスト高トークン (Pro+ リクエスト課金, GPT-5.4:xhigh/Opus:high)"),
            # cursor-agent: Cursor Agent CLI — コーディング特化 (E群)
            (["cursor", "cursor-agent", "composer"],
             "cursor-agent", "cli_agent_ask", "Cursor Agent: コーディング特化"),
            # gemini-cli: Gemini CLI — 最も積極的に使え (S群, クオータ余剰, 最安)
            (["gemini-cli", "gemini cli", "無料gemini", "サブエージェント調査",
              "バッチ", "大量解析", "ログ解析", "文献レビュー", "コスト重視", "1Mコンテキスト",
              "科学", "GPQA", "抽象推論", "パターン認識", "latex生成", "数式"],
             "gemini-cli", "gemini_ask", "Gemini CLI: 解析・数学・科学・素材生成 (MATH 95.1%, 最安, 1M ctx)"),
            (["gemini調査", "gemini研究", "gemini mcp", "ギャップ分析", "論点洗い出し",
              "セカンドオピニオン構造", "設計レビュー"],
             "gemini-cli", "gemini_research", "Gemini CLI: Deep Research + セカンドオピニオン"),
            # ochema: LLM / Gemini
            (["llm", "gemini", "cortex", "相談"],
             "ochema", "ask_cortex", "Gemini Cortex への相談"),
            (["デスクトップ", "at-spi", "gui操作"],
             "ochema", "ochema_run", "デスクトップ UI 操作"),
            # phantazein: コンテキスト
            (["boot", "コンテキスト", "context", "セッション開始"],
             "phantazein", "phantazein_boot", "セッション開始コンテキスト生成"),
            # typos: 構文
            (["typos", "compile", "コンパイル"],
             "typos", "typos_compile", "TYPOS v8 のコンパイル"),
            (["typos", "validate"],
             "typos", "typos_validate", "TYPOS v8 の検証"),
            # opsis: Web 視覚基盤
            (["web", "url", "ブラウザ", "dom", "スクレイピング", "scrape", "opsis", "snapshot", "webページ", "ウェブ"],
             "opsis", "opsis_observe", "Web ページの DOM snapshot 取得"),
            (["クリック", "click", "フォーム", "入力", "fill"],
             "opsis", "opsis_act", "DOM 要素の操作 (click, fill 等)"),
            (["抽出", "extract", "テキスト取得"],
             "opsis", "opsis_extract", "Web ページからデータ抽出"),
        ]

        # FEP グループフィルタ: 対象バックエンド名の集合
        allowed_backends: set[str] | None = None
        if fep_group:
            allowed_backends = set(self._visible_backends(fep_group=fep_group))
        elif self.is_axis_router:
            allowed_backends = set(self._visible_backends())

        task_lower = task_desc.lower()
        scored: list[tuple[float, dict]] = []

        for keywords, backend, tool, reason in _KEYWORD_MAP:
            # FEP グループフィルタ
            if allowed_backends is not None and backend not in allowed_backends:
                continue
            # キーワードマッチ数をスコアとして使用 (境界考慮)
            match_count = sum(
                1 for kw in keywords if self._keyword_matches(kw, task_lower)
            )
            if match_count == 0:
                continue

            importance, complexity = get_tool_scores(tool)
            # スコア = マッチ数 × importance
            score = match_count * importance

            scored.append((score, {
                "backend": backend,
                "tool": tool,
                "reason": reason,
                "match_score": round(score, 3),
                "importance": importance,
                "complexity": complexity,
                "connected": self._backend_connected(backend),
            }))

        # スコアの降順でソートし、重複バックエンドを除去しつつ top_k を取得
        scored.sort(key=lambda x: x[0], reverse=True)
        seen_tools: set[str] = set()
        results: list[dict] = []
        for _score, rec in scored:
            if rec["tool"] not in seen_tools:
                seen_tools.add(rec["tool"])
                results.append(rec)
                if len(results) >= top_k:
                    break

        if not results:
            # マッチなし → デフォルト推奨
            default_backend = "ochema"
            default_tool = "ask_cortex"
            default_reason = "キーワードマッチなし。汎用 Gemini 相談を推奨。"
            if allowed_backends is not None and default_backend not in allowed_backends:
                axis_defaults = {
                    "aisthetikon": ("phantazein", "search", "キーワードマッチなし。既存知識検索を推奨。"),
                    "dianoetikon": ("ochema", "ask_cortex", "キーワードマッチなし。汎用 Gemini 相談を推奨。"),
                    "poietikon": ("codex-mcp", "codex", "キーワードマッチなし。実装系の汎用エージェントを推奨。"),
                }
                default_backend, default_tool, default_reason = axis_defaults.get(
                    self.axis or "",
                    (default_backend, default_tool, default_reason),
                )

            results = [{
                "backend": default_backend,
                "tool": default_tool,
                "reason": default_reason,
                "match_score": 0.0,
                "importance": 0.5,
                "complexity": 0.5,
                "connected": self._backend_connected(default_backend),
            }]

        return results

    # PURPOSE: [L2-auto] Gate (Sekisho) 監査の実行
    async def _handle_gate(self, arguments: dict) -> list[dict]:
        """Gate 監査を Sekisho バックエンド経由で実行する。"""
        # Sekisho バックエンドが接続されているか確認
        sekisho_conn = self.backends.get("sekisho")
        if not sekisho_conn or not sekisho_conn.is_connected:
            err_obj = {
                "error": "Sekisho backend not connected",
                "verdict": "SKIP",
                "reason": "Gate unavailable — sekisho backend offline",
            }
            packet_str = build_return_packet(
                backend="daimonion_judge",
                status="error",
                result=err_obj,
                task_id=arguments.get("task_id"),
                decisions_log_path=arguments.get("decisions_log_path")
            )
            return [{"type": "text", "text": packet_str}]

        self._gate_count += 1

        try:
            # Sekisho の sekisho_gate ツールを呼ぶ
            start = time.time()
            result = await sekisho_conn.call_tool("sekisho_gate", {
                "draft_response": arguments.get("draft_response", ""),
                "reasoning": arguments.get("reasoning", ""),
                "depth": arguments.get("depth", "L2"),
            })
            elapsed = time.time() - start

            # 結果を解析して Gate 統計を更新
            result_text = result[0].get("text", "") if result else ""
            parsed_gate_data = result_text
            try:
                gate_data = json.loads(result_text)
                parsed_gate_data = gate_data
                verdict = gate_data.get("verdict", "UNKNOWN")
                if verdict == "PASS":
                    self._gate_pass_count += 1
                elif verdict == "BLOCK":
                    self._gate_block_count += 1
                log(f"Gate #{self._gate_count}: {verdict} ({elapsed:.1f}s)")
            except (json.JSONDecodeError, KeyError):
                log(f"Gate #{self._gate_count}: response parse error")

            packet_str = build_return_packet(
                backend="daimonion_judge",
                status="success",
                result=parsed_gate_data,
                task_id=arguments.get("task_id"),
                elapsed_ms=round(elapsed * 1000),
                decisions_log_path=arguments.get("decisions_log_path")
            )
            return [{"type": "text", "text": packet_str}]

        except Exception as e:  # noqa: BLE001
            log(f"Gate failed: {e}")
            error_obj = {
                "error": str(e),
                "verdict": "SKIP",
                "reason": f"Gate execution failed: {e}",
            }
            packet_str = build_return_packet(
                backend="daimonion_judge",
                status="error",
                result=error_obj,
                task_id=arguments.get("task_id"),
                decisions_log_path=arguments.get("decisions_log_path")
            )
            return [{"type": "text", "text": packet_str}]

    # PURPOSE: [L2-auto] Gate 自動適用 (importance 閾値フィルタリング)
    async def _auto_gate(
        self, backend_name: str, tool_name: str, result: list[dict],
    ) -> list[dict]:
        """importance が閾値以上のツール呼出結果に対して自動的に Gate 監査を発火する。

        Gate 結果は新規 TextContent ブロックとして result に追加される。
        sekisho バックエンド自身への呼出は再帰防止のためスキップする。
        """
        # 再帰防止: sekisho 自身への呼出はスキップ
        if backend_name == "sekisho":
            return result

        # importance 閾値チェック
        threshold = PIPELINE_CONFIG.get("gate_auto_importance_threshold", 0.7)
        importance, _complexity = get_tool_scores(tool_name)
        if importance < threshold:
            return result

        # Sekisho バックエンドの接続確認
        sekisho_conn = self.backends.get("sekisho")
        if not sekisho_conn or not sekisho_conn.is_connected:
            return result  # 静かにスキップ (利用不可時にエラーは出さない)

        # ツール結果テキストを draft_response として抽出
        draft_text = "\n".join(
            c.get("text", "") for c in result if c.get("type") == "text"
        )
        if not draft_text:
            return result

        # Gate 呼出 (非ブロッキング: 失敗時は result をそのまま返す)
        try:
            gate_result = await sekisho_conn.call_tool("sekisho_audit", {
                "draft_response": draft_text[:8000],  # 過大な入力を制限
                "reasoning": f"Auto-gate: {backend_name}.{tool_name} (importance={importance})",
                "depth": "L1",  # 自動適用は L1 (軽量) で十分
            })

            # Gate 統計を更新
            self._gate_count += 1
            gate_text = gate_result[0].get("text", "") if gate_result else ""
            try:
                gate_data = json.loads(gate_text)
                verdict = gate_data.get("verdict", "UNKNOWN")
                if verdict == "PASS":
                    self._gate_pass_count += 1
                elif verdict == "BLOCK":
                    self._gate_block_count += 1
                log(f"Auto-Gate #{self._gate_count}: {verdict} for {backend_name}.{tool_name}")
            except (json.JSONDecodeError, KeyError):
                log(f"Auto-Gate #{self._gate_count}: parse error")

            # Gate 結果を新規ブロックとして追加 (矛盾2 の教訓: 既存ブロックには触らない)
            gate_piggyback = f"\n---\n🏛️ Auto-Gate (L1): {gate_text[:2000]}"
            result.append({"type": "text", "text": gate_piggyback})

        except Exception as e:  # noqa: BLE001
            log(f"Auto-Gate failed for {backend_name}.{tool_name}: {e}")
            # 失敗時は静かにスキップ — 本来のツール結果を毀損しない

        return result

    # PURPOSE: [L2-auto] FEP 軸仮想サーバーのツール呼出ルーティング
    async def _call_fep_axis_tool(self, axis_name: str, tool_name: str, arguments: dict) -> list[dict]:
        """FEP 軸仮想サーバーのツール呼出。

        axis-router ツール → _call_router_tool に委譲。
        バックエンドツール → tool_name から所属バックエンドを逆引きし転送。
        """
        if self.is_axis_router and axis_name != self.axis:
            return [{"type": "text", "text": f"Error: Axis '{axis_name}' is not served by this router"}]

        # axis-router ツール判定
        if tool_name in self.ROUTER_SELF_TOOLS:
            return await self._call_router_tool(tool_name, arguments)

        # バックエンドツール: 軸内バックエンドから tool_name を逆引き
        fep_group = self._FEP_AXIS_MAP[axis_name]
        for name in self._visible_backends(fep_group=fep_group):
            conn = self.backends.get(name)
            if conn and any(t["name"] == tool_name for t in conn.tools):
                # 実バックエンド名で call_tool — パイプライン (shadow/gate) も適用される
                return await self.call_tool(name, tool_name, arguments)
        if self._upstream_axis and any(t["name"] == tool_name for t in self._upstream_backend_tools()):
            return await self._upstream_axis.call_tool(tool_name, arguments)

        return [{"type": "text", "text": f"Error: Tool '{tool_name}' not found in {axis_name} axis (fep_group={fep_group})"}]

    # PURPOSE: [L2-auto] ツール呼出をバックエンドに転送 (パイプライン付き)
    async def call_tool(self, backend_name: str, tool_name: str, arguments: dict) -> list[dict]:
        """ツール呼出をバックエンドに転送する。パイプラインフックを挟む。"""

        # 後方互換 route 用の router 固有ツール
        if backend_name == "hub":
            return await self._call_router_tool(tool_name, arguments)

        # FEP 軸仮想サーバー
        if backend_name in self._FEP_AXIS_MAP:
            if self.is_axis_router and backend_name != self.axis:
                return [{"type": "text", "text": f"Error: Axis '{backend_name}' is not served by this router"}]
            return await self._call_fep_axis_tool(backend_name, tool_name, arguments)

        if self.is_axis_router:
            backend_axis = get_backend_axis(backend_name)
            if backend_axis and backend_axis != self.axis and backend_name not in self._helper_backend_names:
                return [{"type": "text", "text": f"Error: Backend '{backend_name}' is outside axis '{self.axis}'"}]
            if backend_name in self._delegated_backend_names:
                if not self._upstream_axis:
                    return [{"type": "text", "text": f"Error: Upstream axis '{self.axis}' is not configured"}]
                if not self._upstream_axis.is_connected:
                    await self._upstream_axis._try_reconnect(force=True)
                    if not self._upstream_axis.is_connected:
                        return [{"type": "text", "text": f"Error: Remote axis '{self.axis}' is not connected"}]
                return await self._upstream_axis.call_tool(tool_name, arguments)

        conn = self.backends.get(backend_name)
        if not conn:
            return [{"type": "text", "text": f"Error: Backend '{backend_name}' not found or not connected"}]

        # 未接続の場合、強制再接続を試みる (パイプライン経由呼出でも回復)
        if not conn.is_connected:
            await conn._try_reconnect(force=True)
            if not conn.is_connected:
                return [{"type": "text", "text": f"Error: Backend '{backend_name}' is not connected (reconnect failed)"}]

        # --- Pre-hook: ログ記録 ---
        call_record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "backend": backend_name,
            "tool": tool_name,
            "args_keys": list(arguments.keys()),
        }

        if PIPELINE_CONFIG.get("log_enabled"):
            log(f"→ {backend_name}.{tool_name}({', '.join(arguments.keys())})")

        # --- 転送 ---
        start = time.time()
        result = await conn.call_tool(tool_name, arguments)
        elapsed = time.time() - start

        # --- Post-hook: ログ記録 ---
        call_record["elapsed_ms"] = round(elapsed * 1000)
        call_record["result_size"] = sum(len(c.get("text", "")) for c in result)
        self._call_log.append(call_record)

        # ログを直近 500 件に制限
        if len(self._call_log) > 500:
            self._call_log = self._call_log[-500:]

        if PIPELINE_CONFIG.get("log_enabled"):
            log(f"← {backend_name}.{tool_name} ({elapsed*1000:.0f}ms, {call_record['result_size']} chars)")

        # --- Post-hook: Shadow Gemini 反証 ---
        if PIPELINE_CONFIG.get("shadow_enabled"):
            # 矛盾5修正: Shadow 処理中は post-hook をスキップ (再帰防止)
            shadow = self._get_shadow()
            if shadow and not shadow.is_shadowing:
                result = await self._apply_shadow(backend_name, tool_name, arguments, result)

        # --- Post-hook: Gate (Sekisho) 自動監査 ---
        if PIPELINE_CONFIG.get("gate_enabled"):
            result = await self._auto_gate(backend_name, tool_name, result)

        return result

    # PURPOSE: [L2-auto] Shadow Gemini パイプライン
    async def _apply_shadow(
        self, backend_name: str, tool_name: str,
        arguments: dict, result: list[dict],
    ) -> list[dict]:
        """Shadow Gemini の post-hook を適用する。

        1. アクションを記録
        2. should_shadow() で判定
        3. True → Gemini で反証 → result に piggyback 追加
        """
        shadow = self._get_shadow()
        if shadow is None:
            return result

        # 引数の要約を生成
        summary = json.dumps(arguments, ensure_ascii=False, default=str)[:3000]
        # 結果のプレビュー
        result_text = "\n".join(c.get("text", "")[:2000] for c in result[:3])

        # 1. 記録
        shadow.record(
            backend=backend_name,
            tool_name=tool_name,
            summary=summary,
            result_preview=result_text,
        )

        # 2. 判定 + 3. 反証
        try:
            shadow_result = await shadow.maybe_shadow()
            if shadow_result:
                # result に piggyback テキストを新規ブロックとして追加
                # (矛盾2修正: 既存の text に += すると JSON レスポンスが壊れる)
                piggyback = shadow.format_piggyback(shadow_result)
                result.append({"type": "text", "text": piggyback})
                log(f"🔮 Shadow applied to {backend_name}.{tool_name}")
        except Exception as e:  # noqa: BLE001
            log(f"Shadow pipeline error (non-fatal): {e}")

        return result

    # PURPOSE: [L2-auto] axis-router 統計を返す
    def stats(self) -> dict:
        """axis-router の統計情報を返す。"""
        shadow_stats = {}
        shadow = self._get_shadow()
        if shadow:
            shadow_stats = shadow.stats()

        state_names = self._visible_backends() if self.is_axis_router else list(BACKENDS.keys())
        backend_states = {
            name: self._backend_connected(name)
            for name in state_names
        }
        connected_count = sum(1 for ok in backend_states.values() if ok)
        unhealthy_backends = sorted([
            name for name in state_names
            if not backend_states.get(name, False)
        ])
        recent_failures = [
            c for c in self._call_log
            if not c.get("success", False)
        ][-10:]

        routes = {
            "primary": "/mcp",
            "aliases": [f"/mcp/{name}" for name in self.route_names()],
        }
        if not self.is_axis_router:
            routes["legacy"] = "/mcp/hub"

        return {
            "uptime_seconds": round(time.time() - self._start_time),
            "router_mode": "axis_router" if self.is_axis_router else "legacy_aggregate",
            "axis": self.axis,
            "placement_profile": self.placement_profile,
            "backends_connected": connected_count,
            "backends_total": len(state_names),
            "backend_states": backend_states,
            "unhealthy_backends": unhealthy_backends,
            "total_calls": len(self._call_log),
            "recent_calls": self._call_log[-10:],
            "recent_failures": recent_failures,
            "routes": routes,
            "upstream": {
                "host": self.remote_upstream_host if self._delegated_backend_names else "",
                "connected": bool(self._upstream_axis and self._upstream_axis.is_connected),
                "delegated_backends": list(self._delegated_backend_names),
            },
            "pipeline": {
                "log": PIPELINE_CONFIG.get("log_enabled", False),
                "daimonion_alpha": PIPELINE_CONFIG.get("daimonion_alpha_enabled",
                                   PIPELINE_CONFIG.get("shadow_enabled", False)),
                "daimonion_beta": PIPELINE_CONFIG.get("daimonion_beta_enabled", False),
                "daimonion_gamma": PIPELINE_CONFIG.get("daimonion_gamma_enabled",
                                   PIPELINE_CONFIG.get("gate_enabled", False)),
                # 後方互換
                "shadow": PIPELINE_CONFIG.get("shadow_enabled", False),
                "gate": PIPELINE_CONFIG.get("gate_enabled", False),
            },
            "daimonion": shadow_stats,
            "shadow": shadow_stats,  # 後方互換
            "gate": {
                "total": self._gate_count,
                "pass": self._gate_pass_count,
                "block": self._gate_block_count,
            },
        }

    # PURPOSE: [L2-auto] 全バックエンドを切断
    async def disconnect_all(self):
        """全バックエンドを切断する。"""
        for conn in self.backends.values():
            await conn.disconnect()
        if self._upstream_axis is not None:
            await self._upstream_axis.disconnect()
        self.backends.clear()


# =============================================================================
# Raw ASGI アプリ — streamable-http サーバー
# =============================================================================

def create_axis_app(hub: HubProxy):
    """
    axis router の ASGI アプリを生成する。

    各バックエンドに対して /mcp/{name} パスで MCP サーバーを公開する。
    axis router モードでは hub route を公開しない。
    mcp_base.py L418-426 のパターンに従い、raw ASGI でルーティングする。
    StreamableHTTPSessionManager.handle_request(scope, receive, send) は raw ASGI。
    """
    from mcp.server import Server
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse, Response
    from mcp.types import Tool, TextContent
    from contextlib import asynccontextmanager

    # 各バックエンドに対する MCP Server + SessionManager を生成
    session_managers: dict[str, StreamableHTTPSessionManager] = {}

    all_names = hub.route_names()
    primary_name = hub.primary_server_name

    for backend_name in all_names:
        # クロージャで name をキャプチャ
        def _make_manager(name: str):
            server = Server(f"hgk-{name}")

            @server.list_tools()
            async def _list_tools():
                tools_data = hub.list_tools_for(name)
                return [
                    Tool(
                        name=t["name"],
                        description=t.get("description", ""),
                        inputSchema=t.get("inputSchema", {}),
                    )
                    for t in tools_data
                ]

            @server.call_tool()
            async def _call_tool(tool_name: str, arguments: dict | None):
                result = await hub.call_tool(name, tool_name, arguments or {})
                return [
                    TextContent(type=r.get("type", "text"), text=r.get("text", ""))
                    for r in result
                ]

            return StreamableHTTPSessionManager(
                app=server,
                json_response=True,
                stateless=True,
            )

        session_managers[backend_name] = _make_manager(backend_name)

    # lifespan: 全 session_manager の run() を管理
    @asynccontextmanager
    async def lifespan(app):
        log("Starting session managers...")
        # AsyncExitStack で全 session_manager.run() を管理
        from contextlib import AsyncExitStack
        async with AsyncExitStack() as stack:
            for name, sm in session_managers.items():
                await stack.enter_async_context(sm.run())
                log(f"  ✓ SessionManager [{name}] started")
            yield

    # Starlette app (lifespan 管理のみ)
    starlette_app = Starlette(lifespan=lifespan)

    # Raw ASGI ルーティング
    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            # lifespan は Starlette に委任
            await starlette_app(scope, receive, send)
            return

        if scope["type"] == "http":
            path = scope.get("path", "")

            # /health — ヘルスチェック
            if path == "/health":
                response = JSONResponse(hub.stats())
                await response(scope, receive, send)
                return

            # /mcp/{name} — 名前付き alias
            for name, sm in session_managers.items():
                prefix = f"/mcp/{name}"
                if path == prefix or path.startswith(prefix + "/"):
                    # パスを /mcp に書き換え (バックエンドは /mcp を期待する)
                    scope = dict(scope)
                    scope["path"] = "/mcp" + path[len(prefix):]
                    await sm.handle_request(scope, receive, send)
                    return

            # /mcp — このポートの primary server。
            # 未登録 alias (/mcp/hub 等) は primary に吸収せず 404 にする。
            if path == "/mcp":
                await session_managers[primary_name].handle_request(scope, receive, send)
                return

            # 404
            response = Response("Not Found", status_code=404)
            await response(scope, receive, send)
            return

        # その他のスコープタイプは無視
        response = Response("Not Found", status_code=404)
        await response(scope, receive, send)

    return app


# =============================================================================
# エントリーポイント
# =============================================================================

# PURPOSE: [L2-auto] Hub MCP Proxy のメインエントリーポイント
async def _run_hub(
    host: str,
    port: int,
    *,
    transport: str = "streamable-http",
    axis: str | None = None,
    placement_profile: str = "local",
    remote_upstream_host: str | None = None,
):
    """Hub を起動する。

    transport:
      streamable-http — uvicorn ASGI (従来モード)
      stdio           — stdin/stdout MCP (CC プロセス管理用)

    バックエンドが0個でも起動し、バックグラウンドで再接続を試みる。
    """
    hub = HubProxy(
        axis=axis,
        placement_profile=placement_profile,
        remote_upstream_host=remote_upstream_host,
    )

    # 全バックエンドに接続 (リトライ付き)
    results = await hub.connect_all(max_retries=3, retry_delay=2.0)
    connected_count = sum(1 for v in results.values() if v)

    if connected_count == 0:
        log("WARNING: No backends connected yet. Axis router will start and retry in background.")

    server_name = hub.primary_server_name
    if hub.is_axis_router:
        log(f"  Axis: {hub.axis} ({hub.placement_profile})")
        if hub._delegated_backend_names:
            log(f"  Upstream: {hub.remote_upstream_host} ({', '.join(hub._delegated_backend_names)})")
    connected_backends = [n for n in hub._visible_backends() if hub._backend_connected(n)]
    log(f"  Backends: {len(connected_backends)}/{len(hub._visible_backends())} connected")
    log(f"  Pipeline: log={PIPELINE_CONFIG['log_enabled']}, "
        f"shadow={PIPELINE_CONFIG.get('shadow_enabled', False)}, "
        f"gate={PIPELINE_CONFIG.get('gate_enabled', False)}")

    # ----- stdio トランスポート -----
    if transport == "stdio":
        await _run_axis_stdio(hub, server_name)
        return

    # ----- streamable-http トランスポート (従来モード) -----
    import uvicorn

    # ASGI アプリを生成
    app = create_axis_app(hub)

    log(f"HGK axis MCP router starting on {host}:{port}")
    log(f"  /mcp → {server_name}")
    for name in hub.route_names():
        log(f"  /mcp/{name}")

    # バックグラウンド再接続タスクを開始
    reconnect_task = asyncio.create_task(hub.reconnect_loop(interval=5.0))

    # Dual-stack ソケットを手動作成 (IPv4 + IPv6 両対応)
    # uvicorn は IPv6 ソケットで IPV6_V6ONLY=1 を設定するため、
    # 手動で IPV6_V6ONLY=0 にして dual-stack にする
    sock = _socket.socket(_socket.AF_INET6, _socket.SOCK_STREAM)
    sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
    sock.setsockopt(_socket.IPPROTO_IPV6, _socket.IPV6_V6ONLY, 0)
    # bind retry: 前プロセスの socket 解放を待つ (systemd restart 対策)
    import time as _time
    for _attempt in range(5):
        try:
            sock.bind(("::", port))
            break
        except OSError as e:
            if _attempt < 4:
                log(f"  bind retry {_attempt+1}/5: {e} — waiting 2s...")
                _time.sleep(2)
            else:
                raise
    sock.listen(2048)
    sock.set_inheritable(True)
    log(f"  Dual-stack socket: [::] + 0.0.0.0 on port {port}")

    # uvicorn の fd 経路は fromfd(..., AF_UNIX, ...) を通るため、
    # ここでは pre-bound socket を直接渡す。
    config = uvicorn.Config(
        app=app,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    try:
        await server.serve(sockets=[sock])
    finally:
        reconnect_task.cancel()
        try:
            await reconnect_task
        except asyncio.CancelledError:
            pass


# PURPOSE: [L2-auto] stdio トランスポートでの Hub 起動
async def _run_axis_stdio(hub: HubProxy, server_name: str):
    """stdio トランスポートで Hub を起動する。

    CC (Claude Code / Antigravity) がプロセスを自動管理する場合に使用。
    stdin/stdout で MCP JSON-RPC を送受信する。
    ログは stderr にルーティング済みなので stdout との干渉は発生しない。
    """
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent

    mcp_server = Server(f"hgk-{server_name}")

    @mcp_server.list_tools()
    async def _list_tools():
        tools_data = hub.list_tools_for(server_name)
        return [
            Tool(
                name=t["name"],
                description=t.get("description", ""),
                inputSchema=t.get("inputSchema", {}),
            )
            for t in tools_data
        ]

    @mcp_server.call_tool()
    async def _call_tool(tool_name: str, arguments: dict | None):
        result = await hub.call_tool(server_name, tool_name, arguments or {})
        return [
            TextContent(type=r.get("type", "text"), text=r.get("text", ""))
            for r in result
        ]

    log(f"HGK axis MCP router starting (stdio, server={server_name})")

    # バックグラウンド再接続タスクを開始
    reconnect_task = asyncio.create_task(hub.reconnect_loop(interval=5.0))

    try:
        async with stdio_server() as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )
    finally:
        reconnect_task.cancel()
        try:
            await reconnect_task
        except asyncio.CancelledError:
            pass


def main():
    parser = argparse.ArgumentParser(description="HGK axis MCP router")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=HUB_PORT)
    # run_mcp_service.sh 互換 + CC stdio 対応
    parser.add_argument("--transport", type=str, default="streamable-http",
                        choices=["streamable-http", "stdio"])
    parser.add_argument(
        "--axis",
        type=str,
        choices=sorted(AXIS_PORTS.keys()),
        help="起動する 3軸 router 名",
    )
    parser.add_argument(
        "--placement-profile",
        type=str,
        default=os.environ.get("HGK_MCP_PROFILE", "local"),
        choices=["local", "remote"],
        help="router が束ねる配置プロファイル",
    )
    parser.add_argument(
        "--remote-upstream-host",
        type=str,
        default=os.environ.get("HGK_REMOTE_MCP_HOST", DEFAULT_REMOTE_MCP_HOST),
        help="local profile で remote axis router を委譲する先ホスト",
    )
    args = parser.parse_args()

    asyncio.run(
        _run_hub(
            args.host,
            args.port,
            transport=args.transport,
            axis=args.axis,
            placement_profile=args.placement_profile,
            remote_upstream_host=args.remote_upstream_host,
        )
    )


if __name__ == "__main__":
    main()
