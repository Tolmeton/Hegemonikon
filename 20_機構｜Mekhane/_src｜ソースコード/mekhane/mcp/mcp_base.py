#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/mcp_base.py A0→全 MCP サーバーの共通基盤
"""
MCP Base Module — Hegemonikón MCP Server Common Infrastructure

All MCP servers share:
  - StdoutSuppressor: prevent stdout pollution during imports
  - log(): stderr-only logging with server name prefix
  - path setup: project root calculation
  - MCP SDK imports (Tool, TextContent, Server, stdio_server)
  - main() / run loop boilerplate

Usage:
    from mcp_base import MCPBase, StdoutSuppressor

    base = MCPBase("server_name", "1.0.0", "Description")
    server = base.server
    log = base.log

    @server.list_tools()
    async def list_tools(): ...

    @server.call_tool()
    async def call_tool(name, arguments): ...

    if __name__ == "__main__":
        base.run()
"""

import sys
import os
import io
import asyncio
from pathlib import Path


# =============================================================================
# B2a: 分散 Sekishō 自動監査 — モジュールレベル関数
# =============================================================================

_SEKISHO_AUTO_PROMPT = """あなたは Hegemonikón の行動パターン監査官（軽量モード）です。
以下のツール呼出ログから、Agent の行動パターンに異常がないか検査してください。

## L0: パターン検知 — 以下の3パターンを重点検査

1. **skip_bias (35%)**: view_file/参照なしで実装・回答していないか
   シグナル: 複数の write/edit 後に view_file がない
2. **laziness_deception (14%)**: 品質低下を環境のせいにしていないか
   シグナル: 短い応答が連続
3. **false_impossibility (13%)**: 未調査で「不可能」と断定していないか
   シグナル: 検索/参照ツールを使わずに回答

## L1: 行動異常 — ツール呼出パターンの異常

- θ12.1 違反兆候: CCL 式が含まれるのに hermeneus_run が呼ばれていない
- N-9 違反兆候: 新しいファイルへの書込みの前に view_file がない
- N-5 違反兆候: WF 実行中に検索ステップが省略されている

## MCP サーバー: {server_name}
## 直近のツール呼出: {tool_name}({tool_args_keys})

## セッションログ (最新10件):

{session_log}

## 判定

異常なし → 空文字 "" のみ返す（説明不要）
異常あり → 以下の形式で1行:
⚠️ [パターン名] 検出理由（1行）
"""


def _run_sekisho_auto_audit(
    server_name: str,
    tool_name: str,
    arguments: dict,
) -> str | None:
    """L0+L1 自動監査を Gemini Flash で実行。

    Returns:
        異常検出時: 警告テキスト
        正常時: None
    """
    try:
        from mekhane.agent_guard.prostasia import get_prostasia
        from mekhane.ochema.cortex_client import CortexClient

        prostasia = get_prostasia()
        session_log = prostasia.session_log

        # ログが少なすぎる場合はスキップ（起動直後）
        if len(session_log.get_log()) < 3:
            return None

        # 最新10件のログを取得
        recent_entries = session_log.get_log()[-10:]
        log_text = "\n".join(
            f"[{e['timestamp']}] {e['tool']}({e['args_keys']})"
            for e in recent_entries
        )

        prompt = _SEKISHO_AUTO_PROMPT.format(
            server_name=server_name,
            tool_name=tool_name,
            tool_args_keys=list(arguments.keys()),
            session_log=log_text,
        )

        client = CortexClient(
            model="gemini-3-flash-preview",
            max_tokens=256,
        )
        response = client.ask(
            message=prompt,
            system_instruction="行動パターン監査官。異常なしなら空文字のみ。異常ありなら1行で。",
            temperature=0.0,
            timeout=8.0,
        )

        text = (response.text if hasattr(response, 'text') else str(response)).strip()

        # 空 or 空白 → 正常
        if not text or text == '""' or text == "''":
            return None

        # 異常検出時のみ警告テキストを返す
        if "⚠️" in text or "警告" in text or "検出" in text:
            return f"\n\n---\n🔍 **Sekishō L0/L1 自動監査** ({server_name})\n{text}\n---"

        return None

    except Exception as e:  # noqa: BLE001
        print(f"[Sekishō] Auto-audit internal error: {e}", file=sys.stderr, flush=True)
        return None


# Platform-specific asyncio setup
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# =============================================================================
# run_sync — MCP EOF 防止の中核ユーティリティ
# =============================================================================

async def run_sync(fn, *args, timeout_sec: float = 120.0, **kwargs):
    """Run a synchronous/blocking function in a thread pool.

    This is THE standard way to call blocking operations from MCP tool handlers.
    Prevents blocking the asyncio event loop, which causes EOF disconnections.

    Features:
      - Runs fn(*args, **kwargs) via asyncio.to_thread (thread pool)
      - Timeout protection (default 120s)
      - Descriptive error on timeout (includes function name)

    Usage:
        from mekhane.mcp.mcp_base import run_sync

        # Instead of:  result = await asyncio.to_thread(svc.ask, msg)
        # Write:       result = await run_sync(svc.ask, msg)

        # With timeout: result = await run_sync(svc.ask, msg, timeout_sec=60)

    Args:
        fn: Synchronous callable to execute.
        *args: Positional arguments forwarded to fn.
        timeout_sec: Max seconds to wait (default 120). 0 = no timeout.
        **kwargs: Keyword arguments forwarded to fn.

    Returns:
        Whatever fn returns.

    Raises:
        TimeoutError: If fn doesn't complete within timeout_sec.
    """
    label = getattr(fn, '__qualname__', None) or getattr(fn, '__name__', repr(fn))
    coro = asyncio.to_thread(fn, *args, **kwargs)
    if timeout_sec > 0:
        try:
            return await asyncio.wait_for(coro, timeout=timeout_sec)
        except asyncio.TimeoutError:
            print(
                f"[mcp-base] run_sync TIMEOUT: {label} exceeded {timeout_sec}s",
                file=sys.stderr, flush=True,
            )
            raise TimeoutError(f"Sync call '{label}' timed out after {timeout_sec}s")
    return await coro

# Preserve original stdout before any redirection
_original_stdout = sys.stdout


# PURPOSE: [L2-auto] StdoutSuppressor のクラス定義
class StdoutSuppressor:
    """Suppress stdout during imports to prevent MCP protocol pollution.

    MCP uses stdio for JSON-RPC. Any stray print() call will corrupt
    the protocol stream. This context manager redirects stdout to
    a StringIO buffer during the suppressed block.
    """

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(self):
        self._null = io.StringIO()
        self._old_stdout = None

    # PURPOSE: [L2-auto] __enter__ の関数定義
    def __enter__(self):
        self._old_stdout = sys.stdout
        sys.stdout = self._null
        return self

    # PURPOSE: [L2-auto] __exit__ の関数定義
    def __exit__(self, *args):
        sys.stdout = self._old_stdout
        captured = self._null.getvalue()
        if captured.strip():
            print(
                f"[mcp-base] Suppressed stdout: {captured[:200]}...",
                file=sys.stderr,
                flush=True,
            )


# PURPOSE: [L2-auto] MCPBase のクラス定義
class MCPBase:
    """Common infrastructure for all Hegemonikón MCP servers.

    Handles:
      - Logging (stderr only)
      - Path setup (project root discovery)
      - Server initialization
      - Error-safe tool execution
      - Main run loop
    """

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(self, name: str, version: str, instructions: str):
        self.name = name
        self.version = version
        self._setup_paths()
        self._log(f"Starting {name} MCP Server v{version}...")

        # Load environment variables
        try:
            from mekhane.paths import ensure_env
            ensure_env()
            self._log("Loaded project .env")
        except ImportError:
            self._log("mekhane.paths not available, skipping .env load")

        # Import MCP SDK
        # NOTE: mekhane/mcp/ パッケージが site-packages の mcp パッケージ (MCP SDK) を
        #       シャドウイングする問題への対策。sys.path に .../mekhane が含まれると
        #       import mcp が mekhane/mcp/ を参照してしまうため、MCP SDK import 時のみ
        #       mekhane を含むパスを一時退避する。
        try:
            # mekhane を含むパスエントリを一時退避
            _saved_paths = []
            for _p in list(sys.path):
                if 'mekhane' in _p.lower() or 'mekhane' in str(_p):
                    _saved_paths.append(_p)
                    sys.path.remove(_p)

            try:
                from mcp.server import Server
                from mcp.server.stdio import stdio_server
                from mcp.types import Tool, TextContent
            finally:
                # sys.path を復元 (import の成否に関わらず)
                for _p in reversed(_saved_paths):
                    if _p not in sys.path:
                        sys.path.insert(0, _p)

            self._stdio_server = stdio_server
            self.Tool = Tool
            self.TextContent = TextContent
            self._log("MCP SDK imports OK")
        except Exception as e:  # noqa: BLE001
            import traceback
            self._log(f"MCP SDK import error: {e}")
            self._log(f"  sys.path = {sys.path[:8]}")
            self._log(f"  PYTHONPATH = {os.environ.get('PYTHONPATH', 'NOT SET')}")
            self._log(f"  traceback:\n{traceback.format_exc()}")
            sys.exit(1)

        self.server = Server(
            name=name,
            version=version,
            instructions=instructions,
        )
        self._background_tasks: list = []  # F3: registered background coroutines
        self._log("Server initialized")

    # PURPOSE: [L2-auto] _setup_paths の関数定義
    def _setup_paths(self):
        """Add project root and mekhane dir to sys.path."""
        # mekhane/mcp/mcp_base.py → mekhane/ → hegemonikon/
        self.mcp_dir = Path(__file__).parent
        self.mekhane_dir = self.mcp_dir.parent
        self.project_root = self.mekhane_dir.parent

        for p in [str(self.project_root), str(self.mekhane_dir)]:
            if p not in sys.path:
                sys.path.insert(0, p)

    # PURPOSE: [L2-auto] _log の関数定義
    def _log(self, msg: str):
        """Log to stderr with server name prefix."""
        print(f"[{self.name}] {msg}", file=sys.stderr, flush=True)

    # PURPOSE: [L2-auto] log の関数定義
    @property
    def log(self):
        """Provide log function for external use."""
        return self._log

    def register_background_task(self, coro_factory):
        """Register a coroutine factory to run as background task during _main().

        Args:
            coro_factory: An async function (no args) that runs as background task.
                          Will be cancelled when the server stops.
        """
        self._background_tasks.append(coro_factory)
        self._log(f"Background task registered: {coro_factory.__name__}")



    async def _heartbeat(self):
        """Background heartbeat — proves event loop is alive."""
        count = 0
        while True:
            await asyncio.sleep(30)
            count += 1
            self._log(f"heartbeat #{count} (event loop alive)")

    # PURPOSE: [L2-auto] _main の非同期処理定義
    async def _main(self):
        """MCP server main loop (stdio)."""
        # F4: Save original stdout for MCP protocol, then redirect
        # sys.stdout to stderr to prevent stray print() from corrupting
        # the MCP JSON-RPC stream.
        # CRITICAL: stdio_server() must receive the REAL stdout, not stderr.
        # MCP SDK v1.26.0 reads sys.stdout.buffer internally, so we must
        # pass the original stdout explicitly before redirecting.
        import anyio
        from io import TextIOWrapper
        real_stdout = anyio.wrap_file(
            TextIOWrapper(_original_stdout.buffer, encoding="utf-8")
        )
        real_stdin = anyio.wrap_file(
            TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
        )
        sys.stdout = sys.stderr
        self._log("Starting stdio server (stdout → stderr)...")

        try:
            async with self._stdio_server(
                stdin=real_stdin, stdout=real_stdout
            ) as streams:
                self._log("stdio connected")
                bg_tasks = [asyncio.create_task(self._heartbeat())]
                for factory in self._background_tasks:
                    bg_tasks.append(asyncio.create_task(factory()))
                try:
                    await self.server.run(
                        streams[0],
                        streams[1],
                        self.server.create_initialization_options(),
                    )
                finally:
                    for t in bg_tasks:
                        t.cancel()
                    await asyncio.gather(*bg_tasks, return_exceptions=True)
        except Exception as e:  # noqa: BLE001
            self._log(f"Server error: {e}")
            raise

    def run_http(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the MCP server over Streamable HTTP.

        Uses MCP SDK's StreamableHTTPSessionManager for proper ASGI integration.
        Routes /mcp directly via raw ASGI to avoid Starlette endpoint wrapper
        corrupting the connection (endpoint wrapper sends a second response).
        """
        from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
        from starlette.applications import Starlette
        from starlette.responses import Response
        import uvicorn
        from contextlib import asynccontextmanager

        session_manager = StreamableHTTPSessionManager(
            app=self.server,
            json_response=False,
        )

        @asynccontextmanager
        async def lifespan(app):
            self._log("Starting HTTP background tasks...")
            bg_tasks = [asyncio.create_task(self._heartbeat())]
            for factory in self._background_tasks:
                bg_tasks.append(asyncio.create_task(factory()))
            async with session_manager.run():
                try:
                    yield
                finally:
                    self._log("Cancelling HTTP background tasks...")
                    for t in bg_tasks:
                        t.cancel()
                    await asyncio.gather(*bg_tasks, return_exceptions=True)

        # Starlette app for lifespan management only (no routes)
        starlette_app = Starlette(lifespan=lifespan)

        # Raw ASGI app: route /mcp directly to session_manager
        async def app(scope, receive, send):
            if scope["type"] == "lifespan":
                await starlette_app(scope, receive, send)
            elif scope["type"] == "http" and scope["path"] == "/mcp":
                await session_manager.handle_request(scope, receive, send)
            else:
                response = Response("Not Found", status_code=404)
                await response(scope, receive, send)

        self._log(f"Starting Streamable HTTP on {host}:{port} (/mcp)")
        uvicorn.run(app, host=host, port=port, log_level="warning")

    # PURPOSE: [L2-auto] run の関数定義
    def run(self, transport: str | None = None, host: str = "0.0.0.0", port: int | None = None):
        """Run the MCP server (blocking)."""
        import argparse
        parser = argparse.ArgumentParser(description=f"{self.server.name} MCP Server", add_help=False)
        parser.add_argument("--transport", type=str, default="stdio",
                            choices=["stdio", "http", "streamable-http"])
        parser.add_argument("--port", type=int, default=8000)
        parser.add_argument("--host", type=str, default="0.0.0.0")
        args, _ = parser.parse_known_args()

        actual_transport = args.transport if transport is None else transport
        actual_port = args.port if port is None else port
        actual_host = args.host if host == "0.0.0.0" else host

        self._log(f"Running main... (transport={actual_transport})")
        try:
            if actual_transport in ("http", "streamable-http"):
                self.run_http(host=actual_host, port=actual_port)
            else:
                asyncio.run(self._main())
        except KeyboardInterrupt:
            self._log("Stopped by user")
        except Exception as e:  # noqa: BLE001
            self._log(f"Fatal error: {e}")
            sys.exit(1)

    # PURPOSE: Prostasia BC動的注入の環境強制フック
    def install_prostasia_hook(self):
        """Prostasia BC注入フックをインストール。

        MCP SDK v1.26+ 対応: request_handlers[CallToolRequest] を wrap する。
        Private API (_call_tool_handler) には依存しない。

        使い方: call_tool 定義後、run() 前に呼ぶ:
            base.install_prostasia_hook()
            base.run()
        """
        try:
            from mekhane.agent_guard.prostasia import inject_into_mcp_result
            from mcp.types import CallToolRequest

            original_handler = self.server.request_handlers.get(CallToolRequest)

            if original_handler is None:
                self._log("[Prostasia] No CallToolRequest handler registered, skipping hook")
                return

            async def _prostasia_hook(req: CallToolRequest):
                result = await original_handler(req)
                # CallToolResult の content を wrap する
                try:
                    if hasattr(result, 'content') and result.content is not None:
                        result.content = inject_into_mcp_result(
                            list(result.content),
                            req.params.name,
                            req.params.arguments or {},
                            self.TextContent,
                        )
                except Exception as e:  # noqa: BLE001
                    self._log(f"[Prostasia] Injection error (non-fatal): {e}")
                return result

            self.server.request_handlers[CallToolRequest] = _prostasia_hook
            self._log("[Prostasia] BC injection hook installed (SDK v1.26+)")

        except ImportError as e:
            self._log(f"[Prostasia] Not available: {e}")
        except Exception as e:  # noqa: BLE001
            self._log(f"[Prostasia] Hook install error: {e}")

    # PURPOSE: B2a 分散 Sekishō — Agent の意志をバイパスする自動 Gemini 監査
    def install_sekisho_hook(self):
        """分散 Sekishō 自動監査フックをインストール。

        MCP SDK v1.26+ 対応: request_handlers[CallToolRequest] を wrap する。
        Prostasia フックの後に chain する。
        全ツール呼出で Gemini Flash が自動監査を実行。

        L0: パターン検知 — skip_bias/laziness/false_impossibility のシグナル検出
        L1: 行動異常 — ツール呼出パターンの異常検出

        使い方: install_prostasia_hook() の後に呼ぶ:
            base.install_prostasia_hook()
            base.install_sekisho_hook()
            base.run()
        """
        try:
            from mcp.types import CallToolRequest

            original_handler = self.server.request_handlers.get(CallToolRequest)
            if original_handler is None:
                self._log("[Sekishō] No CallToolRequest handler, skipping")
                return

            server_name = self.name
            log_fn = self._log

            # Sekisho 除外ツール (自己監査の再帰防止)
            excluded = frozenset({
                "sekisho_audit", "sekisho_ping", "sekisho_history",
                "sekisho_gate",
            })

            async def _sekisho_hook(req: CallToolRequest):
                result = await original_handler(req)
                tool_name = req.params.name
                arguments = req.params.arguments or {}

                # Sekishō 自体は監査しない (再帰防止)
                if tool_name in excluded:
                    return result

                # 非同期で Gemini Flash 監査を実行
                try:
                    audit_result = await run_sync(
                        _run_sekisho_auto_audit,
                        server_name, tool_name, arguments,
                        timeout_sec=10.0,
                    )
                    if audit_result and hasattr(result, 'content') and result.content is not None:
                        from mcp.types import TextContent as TC
                        content_list = list(result.content)
                        content_list.append(TC(
                            type="text",
                            text=audit_result,
                        ))
                        result.content = content_list
                except Exception as e:  # noqa: BLE001
                    log_fn(f"[Sekishō] Auto-audit error (non-fatal): {e}")

                return result

            self.server.request_handlers[CallToolRequest] = _sekisho_hook
            self._log("[Sekishō] Auto-audit hook installed (SDK v1.26+, L0+L1)")

        except ImportError as e:
            self._log(f"[Sekishō] Not available: {e}")
        except Exception as e:  # noqa: BLE001
            self._log(f"[Sekishō] Hook install error: {e}")

    # PURPOSE: V-011 多層品質保証の自動適用 (IDE直叩きサーバー用)
    def install_quality_gate_hook(self):
        """品質ゲートの自動評価フックをインストール。

        MCP SDK v1.26+ 対応: request_handlers[CallToolRequest] を wrap する。
        Prostasia/Sekisho フックの後に chain する。
        ポリシーに従いツール呼び出しのリスクを判定し、L1/L2 ゲートを実行。

        使い方:
            base.install_prostasia_hook()
            base.install_sekisho_hook()
            base.install_quality_gate_hook()  # <- New
            base.run()
        """
        import os
        if os.getenv("HGK_QUALITY_GATE_ENABLED", "1") != "1":
            self._log("[QualityGate] Disabled via env HGK_QUALITY_GATE_ENABLED=0")
            return

        try:
            from mcp.types import CallToolRequest, TextContent
            from mekhane.mcp.quality_gate import execute_quality_gate, format_gate_result, update_gate_status

            original_handler = self.server.request_handlers.get(CallToolRequest)
            if original_handler is None:
                self._log("[QualityGate] No CallToolRequest handler, skipping")
                return

            log_fn = self._log

            async def _quality_gate_hook(req: CallToolRequest):
                result = await original_handler(req)
                tool_name = req.params.name
                arguments = req.params.arguments or {}

                # 実行結果（TextContent）をまとめる
                response_text = ""
                if hasattr(result, 'content') and result.content is not None:
                    for c in result.content:
                        if getattr(c, 'type', '') == 'text' and hasattr(c, 'text'):
                            response_text += c.text + "\n"

                # 非同期で品質ゲートを実行 (CortexClient が同期のため run_sync を使用)
                try:
                    gate_result = await run_sync(
                        execute_quality_gate,
                        tool_name, arguments, response_text, None
                    )
                    
                    if gate_result:
                        await run_sync(update_gate_status, gate_result)
                        formatted = format_gate_result(gate_result)
                        if formatted and hasattr(result, 'content') and result.content is not None:
                            content_list = list(result.content)
                            content_list.append(TextContent(
                                type="text",
                                text=formatted,
                            ))
                            result.content = content_list

                        # ステータス更新 (非同期実行をブロックしないようバックグラウンド等でやるべきか確認、現状は同期で一瞬なのでrun_sync内が望ましいが、関数外なので直接呼ぶか一旦同期実行)
                        # ステータス更新も同期的ファイルIOなのでrun_syncで呼ぶ方が安全
                except Exception as e:  # noqa: BLE001
                    log_fn(f"[QualityGate] Auto-gate error (non-fatal): {e}")

                return result

            self.server.request_handlers[CallToolRequest] = _quality_gate_hook
            self._log("[QualityGate] Auto-gate hook installed (SDK v1.26+, V-011)")

        except ImportError as e:
            self._log(f"[QualityGate] Not available: {e}")
        except Exception as e:  # noqa: BLE001
            self._log(f"[QualityGate] Hook install error: {e}")

    # PURPOSE: T-03 Tool Loop Guard の自動適用
    def install_tool_loop_guard_hook(self):
        """Tool Loop Guard フックをインストール。

        MCP SDK v1.26+ 対応: request_handlers[CallToolRequest] を wrap する。
        Prostasia/Sekisho/QualityGate フックの前に chain するのが望ましいが、どこでも可。
        無限ループを検知した場合は RuntimeError を投げて実行をブロックする。

        使い方:
            base.install_tool_loop_guard_hook()  # <- New
            ...
            base.run()
        """
        import os
        if os.getenv("HGK_TOOL_LOOP_GUARD_ENABLED", "1") != "1":
            self._log("[ToolLoopGuard] Disabled via env HGK_TOOL_LOOP_GUARD_ENABLED=0")
            return

        try:
            from mcp.types import CallToolRequest
            from mekhane.agent_guard.tool_loop import (
                detect_tool_call_loop,
                record_tool_call,
                record_tool_outcome,
            )
            import time

            original_handler = self.server.request_handlers.get(CallToolRequest)
            if original_handler is None:
                self._log("[ToolLoopGuard] No CallToolRequest handler, skipping")
                return

            log_fn = self._log
            history = []

            async def _tool_loop_hook(req: CallToolRequest):
                tool_name = req.params.name
                arguments = req.params.arguments or {}
                
                # Check for loop before execution
                res = detect_tool_call_loop(history, tool_name, arguments)
                if res.stuck:
                    if res.level == "critical":
                        log_fn(f"[ToolLoopGuard] BLOCKED: {res.message}")
                        raise RuntimeError(res.message)
                    else:
                        log_fn(f"[ToolLoopGuard] WARNING: {res.message}")

                # Record call
                record_tool_call(history, tool_name, arguments, time.time())
                
                try:
                    result = await original_handler(req)
                    
                    # Convert MCP result to dict for outcome hashing
                    res_dict = {"content": []}
                    if hasattr(result, 'content') and result.content is not None:
                         for c in result.content:
                             if getattr(c, 'type', '') == 'text' and hasattr(c, 'text'):
                                 res_dict["content"].append({"type": "text", "text": c.text})
                    
                    record_tool_outcome(history, tool_name, arguments, result=res_dict)
                    return result
                except Exception as e:  # noqa: BLE001
                    record_tool_outcome(history, tool_name, arguments, error=e)
                    raise

            self.server.request_handlers[CallToolRequest] = _tool_loop_hook
            self._log("[ToolLoopGuard] Hook installed (SDK v1.26+, T-03)")

        except ImportError as e:
            self._log(f"[ToolLoopGuard] Not available: {e}")
        except Exception as e:  # noqa: BLE001
            self._log(f"[ToolLoopGuard] Hook install error: {e}")

    # PURPOSE: θ12.2 環境強制 — sekisho_gate リマインダー + ハードブロック
    def install_sekisho_gate_reminder_hook(
        self,
        soft_threshold: int = 10,
        hard_threshold: int = 20,
    ):
        """Sekisho Gate リマインダーフック — L1 hooks 移行により no-op 化。

        L1 Stop hook (sekisho-async-audit.py) が毎応答で自動監査し、
        sekisho_status.json の consecutive_unaudited を 0 にリセットする。
        MCP 側のツール単位カウントは L1 存在下では冗長のため無効化。

        移行先: hooks/sekisho-async-audit.py (Stop hook)
                hooks/sekisho-gate-verify.sh (SessionStart hook)
        """
        self._log("[SekishoReminder] Superseded by L1 Stop hook (sekisho-async-audit.py) — no-op")

    # PURPOSE: 全フック一括インストール — ボイラープレート排除
    def install_all_hooks(self):
        """全フックを正しい順序で一括インストール。

        各サーバーで個別に install_*_hook() を呼ぶ代わりに、
        この1メソッドで全フックを統一的にインストールする。

        順序:
          1. prostasia (BC 動的注入)
          2. sekisho (分散自動監査)
          3. quality_gate (品質ゲート)
          4. tool_loop_guard (ツールループ検出)
          5. sekisho_gate_reminder (Gate リマインダー)

        使い方:
            base = MCPBase("server_name", "1.0.0", "Description")
            # ... @server.list_tools, @server.call_tool ...
            base.install_all_hooks()
            base.run()
        """
        self.install_prostasia_hook()
        self.install_sekisho_hook()
        self.install_quality_gate_hook()
        self.install_tool_loop_guard_hook()
        self.install_sekisho_gate_reminder_hook()


# ═══════════════════════════════════════════════════════════════
# PURPOSE: MCPBase 非継承サーバー向け Sekishō フック (hermeneus, jules 用)
# _call_tool_handler ラップ方式 — MCPBase の install_sekisho_hook /
# install_sekisho_gate_reminder_hook と同等のロジック
# ═══════════════════════════════════════════════════════════════

def _default_log(msg: str) -> None:
    """デフォルトのログ関数 (stderr)。"""
    print(f"[MCP] {msg}", file=sys.stderr, flush=True)


# PURPOSE: MCPBase 非継承サーバー向け Sekishō 自動監査フック
def install_sekisho_hook_for_server(
    server,
    server_name: str,
    log_fn=None,
):
    """MCPBase 非継承サーバー用 Sekishō 自動監査フック。

    server._call_tool_handler をラップし、全ツール呼出後に
    Gemini Flash による L0/L1 自動監査を実行する。

    使い方 (jules の Prostasia hook の後に chain):
        install_sekisho_hook_for_server(server, "jules", log)
    """
    log = log_fn or _default_log

    try:
        original_handler = server._call_tool_handler
        if original_handler is None:
            log("[Sekishō] No _call_tool_handler, skipping")
            return

        # Sekisho 除外ツール (自己監査の再帰防止)
        excluded = frozenset({
            "sekisho_audit", "sekisho_ping", "sekisho_history",
            "sekisho_gate",
        })

        async def _sekisho_hook(name, arguments):
            result = await original_handler(name, arguments or {})
            tool_name = name

            # Sekishō 自体は監査しない (再帰防止)
            if tool_name in excluded:
                return result

            # 非同期で Gemini Flash 監査を実行
            try:
                audit_result = await run_sync(
                    _run_sekisho_auto_audit,
                    server_name, tool_name, arguments or {},
                    timeout_sec=10.0,
                )
                if audit_result and isinstance(result, list):
                    from mcp.types import TextContent as TC
                    result.append(TC(type="text", text=audit_result))
            except Exception as e:  # noqa: BLE001
                log(f"[Sekishō] Auto-audit error (non-fatal): {e}")

            return result

        server._call_tool_handler = _sekisho_hook
        log(f"[Sekishō] Auto-audit hook installed for {server_name} (L0+L1)")

    except Exception as e:  # noqa: BLE001
        log(f"[Sekishō] Hook install error: {e}")


# PURPOSE: MCPBase 非継承サーバー向け Sekishō Gate リマインダーフック
def install_sekisho_gate_reminder_hook_for_server(
    server,
    server_name: str,
    log_fn=None,
    soft_threshold: int = 10,
    hard_threshold: int = 20,
):
    """Sekishō Gate リマインダーフック (非継承版) — L1 hooks 移行により no-op 化。

    L1 Stop hook (sekisho-async-audit.py) が毎応答で自動監査するため、
    MCP 側のツール単位カウントは不要。
    """
    log = log_fn or _default_log
    log("[SekishoReminder] Superseded by L1 Stop hook (sekisho-async-audit.py) — no-op")


# PURPOSE: MCPBase 非継承サーバー向け全フック一括インストール
def install_all_hooks_for_server(
    server,
    server_name: str,
    log_fn=None,
    soft_threshold: int = 10,
    hard_threshold: int = 20,
):
    """MCPBase 非継承サーバー用 全フック一括インストール。

    hermeneus/jules など独自 Server() を使うサーバー向け。
    利用可能なフック (sekisho + gate_reminder) を一括インストール。

    注: prostasia / quality_gate / tool_loop_guard は
    request_handlers パターン前提のため非継承サーバーでは未対応。

    使い方:
        from mekhane.mcp.mcp_base import install_all_hooks_for_server
        install_all_hooks_for_server(server, "hermeneus", log)
    """
    install_sekisho_hook_for_server(server, server_name, log_fn)
    install_sekisho_gate_reminder_hook_for_server(
        server, server_name, log_fn, soft_threshold, hard_threshold,
    )


# ═══════════════════════════════════════════════════════════════
# PURPOSE: MCPBase 非継承サーバー向け Streamable HTTP 起動ユーティリティ
# hermeneus, jules 等の独自サーバーがコピペなく HTTP モードを利用できる
# ═══════════════════════════════════════════════════════════════

def run_streamable_http(
    server,
    *,
    host: str = "0.0.0.0",
    port: int = 8000,
    log_fn=None,
    background_tasks=None,
):
    """MCPBase 非継承サーバー用 Streamable HTTP 起動関数。

    Uses MCP SDK's StreamableHTTPSessionManager for proper ASGI integration.

    Args:
        server: mcp.server.Server インスタンス
        host: バインドアドレス
        port: ポート番号
        log_fn: ログ関数 (省略時は print to stderr)
        background_tasks: サーバー起動時に開始するバックグラウンドタスクファクトリのリスト
    """
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.applications import Starlette
    from starlette.responses import Response
    import uvicorn
    from contextlib import asynccontextmanager
    import asyncio as _asyncio

    _log = log_fn or (lambda msg: print(f"[mcp-http] {msg}", file=__import__("sys").stderr, flush=True))

    session_manager = StreamableHTTPSessionManager(
        app=server,
        json_response=False,
    )

    @asynccontextmanager
    async def lifespan(app):
        _log("Starting HTTP background tasks...")
        _running_bg_tasks = []
        if background_tasks:
            for factory in background_tasks:
                _running_bg_tasks.append(_asyncio.create_task(factory()))
        async with session_manager.run():
            try:
                yield
            finally:
                _log("Shutting down...")
                if _running_bg_tasks:
                    for t in _running_bg_tasks:
                        t.cancel()
                    await _asyncio.gather(*_running_bg_tasks, return_exceptions=True)

    # Starlette app for lifespan management only (no routes)
    starlette_app = Starlette(lifespan=lifespan)

    # Raw ASGI app: route /mcp directly to session_manager
    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            await starlette_app(scope, receive, send)
        elif scope["type"] == "http" and scope["path"] == "/mcp":
            await session_manager.handle_request(scope, receive, send)
        else:
            response = Response("Not Found", status_code=404)
            await response(scope, receive, send)

    _log(f"Starting Streamable HTTP on {host}:{port} (/mcp)")
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    srv = uvicorn.Server(config)

    _asyncio.run(srv.serve())
