#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/api/
# PURPOSE: FastAPI アプリケーション本体 — CORS, ルーター登録, uvicorn 起動
"""
Hegemonikón API Server

Tauri v2 デスクトップアプリのバックエンド。
既存の mekhane/* モジュールを REST API として公開する。

Usage:
    # TCP モード (開発・n8n 連携用)
    python -m mekhane.api.server
    python -m mekhane.api.server --port 9696

    # UDS モード (Tauri デスクトップアプリ用)
    python -m mekhane.api.server --uds /tmp/hgk.sock
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Load .env BEFORE importing gateway modules (HGK_GATEWAY_TOKEN required at module level)
from mekhane.paths import ensure_env, MEKHANE_SRC
ensure_env()
_PROJECT_ROOT = MEKHANE_SRC  # 後方互換: sys.path 用

# R4 fix: scripts/ パッケージが PYTHONPATH なしで import 可能になるよう
# プロジェクトルートを sys.path に追加
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mekhane.api import API_PREFIX, API_TITLE, DEFAULT_PORT, __version__


# PURPOSE: Embedder 事前ロード + Digestor Scheduler をバックグラウンドで起動
@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Startup: Embedder 事前ロード + Digestor Scheduler → Shutdown: cleanup."""
    import asyncio

    async def _preload_background():
        """Background task: Embedder をロードして app.state に格納."""
        try:
            def _preload():
                # Strategy: Vertex AI を直接試行 → BGE-M3 は最終フォールバック
                # _get_embedder() は Vertex 失敗時に BGE-M3 をロードして
                # 起動を ~60s 遅延させるので、ここでは直接制御する。
                try:
                    from mekhane.anamnesis.vertex_embedder import VertexEmbedder
                    from mekhane.anamnesis.constants import EMBED_MODEL, EMBED_DIM
                    embedder = VertexEmbedder(
                        model_name=EMBED_MODEL,
                        dimension=EMBED_DIM,
                    )
                    # Quick test to verify API access
                    _ = embedder.embed("ping")
                    logger.info(
                        "Embedder preloaded: VertexEmbedder (%s, dim=%d)",
                        EMBED_MODEL,
                        getattr(embedder, '_dimension', EMBED_DIM),
                    )
                    return embedder
                except Exception as ve:  # noqa: BLE001
                    logger.warning("Vertex AI unavailable (%s), falling back to local", ve)

                # Fallback: local BGE-M3 (heavy, ~20s load)
                from mekhane.anamnesis.index import Embedder
                embedder = Embedder(model_name="BAAI/bge-m3")
                logger.info(
                    "Embedder preloaded: %s (dim=%d) [fallback]",
                    embedder.model_name, getattr(embedder, '_dimension', -1),
                )
                return embedder

            embedder = await asyncio.wait_for(
                asyncio.to_thread(_preload), timeout=60.0
            )
            app.state.embedder = embedder
            dim = getattr(embedder, '_dimension', -1)
            model = getattr(embedder, 'model_name', 'unknown')
            logger.info(f"🧠 Embedder ({model}, {dim}d) warm cache ready")
        except asyncio.TimeoutError:
            logger.warning("Embedder preload timed out (60s) — will load on first search")
            app.state.embedder = None
        except Exception as exc:  # noqa: BLE001
            logger.warning("Embedder preload failed (non-fatal): %s", exc)
            app.state.embedder = None

    # --- Startup ---

    # 1. Embedder (fire-and-forget)
    app.state.embedder = None  # 初期値
    app.state._preload_task = asyncio.create_task(_preload_background())

    # 2. Digestor Scheduler (バックグラウンドループ — 独自の schedule ライブラリ)
    app.state._digestor_task = None
    try:
        from mekhane.ergasterion.digestor.scheduler import start_async_scheduler_loop
        app.state._digestor_task = asyncio.create_task(start_async_scheduler_loop())
        logger.info("📥 Digestor Scheduler started (API-integrated mode)")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Digestor Scheduler startup failed (non-fatal): %s", exc)

    # 3. SchedulerService (P-02: 統合バックグラウンドジョブ管理)
    #    gnosis_sync(6h) + health_check(1h) + temporal_summary(24h)
    app.state.scheduler = None
    try:
        from mekhane.pks.scheduler_service import create_default_scheduler
        scheduler = create_default_scheduler()
        await scheduler.start()
        app.state.scheduler = scheduler
        logger.info("📅 SchedulerService started (%d jobs)", len(scheduler._jobs))
    except Exception as exc:  # noqa: BLE001
        logger.warning("SchedulerService startup failed (non-fatal): %s", exc)

    # 4. MCP Gateway SessionManager — app.mount() はサブアプリの lifespan を呼ばないため、
    #    ここで手動的に session_manager.run() を起動する。
    #    _register_routers() で app.state._mcp_session_manager に保存済み。
    mcp_sm = getattr(app.state, '_mcp_session_manager', None)
    mcp_sm_cm = None
    if mcp_sm is not None:
        try:
            mcp_sm_cm = mcp_sm.run()
            await mcp_sm_cm.__aenter__()
            logger.info("🔌 MCP Gateway SessionManager started (task group initialized)")
        except Exception as exc:  # noqa: BLE001
            logger.warning("MCP SessionManager startup failed: %s", exc)
            mcp_sm_cm = None

    yield

    # --- MCP SessionManager 停止 ---
    if mcp_sm_cm is not None:
        try:
            await mcp_sm_cm.__aexit__(None, None, None)
            logger.info("MCP Gateway SessionManager stopped")
        except Exception as exc:  # noqa: BLE001
            logger.warning("MCP SessionManager shutdown failed: %s", exc)

    # --- Shutdown ---

    # SchedulerService 停止
    if app.state.scheduler:
        try:
            await app.state.scheduler.stop()
        except Exception as exc:  # noqa: BLE001
            logger.warning("SchedulerService stop failed: %s", exc)

    # その他のバックグラウンドタスク停止
    for task_name in ('_digestor_task', '_preload_task'):
        task = getattr(app.state, task_name, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            logger.info("Cancelled background task: %s", task_name)

# PURPOSE: デフォルト UDS パス
DEFAULT_UDS_PATH = "/tmp/hgk.sock"

# PURPOSE: ロギング設定
logger = logging.getLogger("hegemonikon.api")


# PURPOSE: FastAPI アプリケーション生成
def create_app() -> FastAPI:
    """FastAPI インスタンスを生成し、ルーターを登録する。"""
    app = FastAPI(
        title=API_TITLE,
        version=__version__,
        description="Hegemonikón mekhane モジュールの REST API",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=f"{API_PREFIX}/redoc",
        openapi_url=f"{API_PREFIX}/openapi.json",
        lifespan=_lifespan,
    )

    # CORS — TCP モード時のみ意味がある（UDS では不要だが害もない）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # R3 fix: app.state.start_time でサーバー起動時刻を正確に記録
    app.state.start_time = time.time()

    # ルートレベル /health — Funnel 経由の外部監視用 (軽量)
    # MCP Gateway が "/" にマウントされる前に FastAPI で捕捉する
    @app.get("/health")
    async def root_health():
        """外部監視用の軽量ヘルスチェック (Tailscale Funnel 経由)."""
        import os
        uptime = time.time() - app.state.start_time
        return {
            "status": "ok",
            "port": int(os.environ.get("HGK_API_PORT", 9696)),
            "uptime_seconds": round(uptime, 1),
        }

    # ルーター登録
    _register_routers(app)

    return app


# PURPOSE: 全ルーターを登録（Gnōsis は遅延ロードで安全に）
def _register_routers(app: FastAPI) -> None:
    """各ルートモジュールのルーターを登録する。"""
    from mekhane.api.routes.status import router as status_router
    from mekhane.api.routes.fep import router as fep_router
    from mekhane.api.routes.postcheck import router as postcheck_router
    from mekhane.api.routes.dendron import router as dendron_router
    from mekhane.api.routes.graph import router as graph_router
    from mekhane.api.routes.plugins import router as plugins_router

    app.include_router(status_router, prefix=API_PREFIX)
    app.include_router(fep_router, prefix=API_PREFIX)
    app.include_router(postcheck_router, prefix=API_PREFIX)
    app.include_router(dendron_router, prefix=API_PREFIX)
    app.include_router(graph_router, prefix=API_PREFIX)
    app.include_router(plugins_router, prefix=API_PREFIX)

    # Gnōsis — shape mismatch の可能性があるため遅延ロード
    try:
        from mekhane.api.routes.gnosis import router as gnosis_router
        app.include_router(gnosis_router, prefix=API_PREFIX)
        logger.info("Gnōsis router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gnōsis router skipped: %s", exc)

    # CCL — Hermēneus/Synergeia に依存するため遅延ロード
    try:
        from mekhane.api.routes.ccl import router as ccl_router
        app.include_router(ccl_router, prefix=API_PREFIX)
        logger.info("CCL router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("CCL router skipped: %s", exc)

    # Sympatheia — AttractorAdvisor (モデルロード) に依存するため遅延ロード
    try:
        from mekhane.api.routes.sympatheia import router as sympatheia_router
        app.include_router(sympatheia_router, prefix=API_PREFIX)
        logger.info("Sympatheia router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Sympatheia router skipped: %s", exc)

    # Cortex — Lite proxy for Gemini
    try:
        from mekhane.api.routes.cortex import router as cortex_router
        # Cortex router は API_PREFIX に既に /cortex が含まれている前提なので、prefix をどうするか確認
        # cortex.py で prefix="/api/cortex" としているので、ここでは prefix="" または削除
        app.include_router(cortex_router)
        logger.info("Cortex router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cortex router skipped: %s", exc)

    # PKS — 埋め込みモデルに依存するため遅延ロード
    try:
        from mekhane.api.routes.pks import router as pks_router
        app.include_router(pks_router, prefix=API_PREFIX)
        logger.info("PKS router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("PKS router skipped: %s", exc)

    # Gnōsis Narrator — PKSEngine + PKSNarrator に依存するため遅延ロード
    try:
        from mekhane.api.routes.gnosis_narrator import router as narrator_router
        app.include_router(narrator_router, prefix=API_PREFIX)
        logger.info("Gnōsis Narrator router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gnōsis Narrator router skipped: %s", exc)

    # Link Graph — ファイルシステム IO に依存するため遅延ロード
    try:
        from mekhane.api.routes.link_graph import router as link_graph_router
        app.include_router(link_graph_router, prefix=API_PREFIX)
        logger.info("Link Graph router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Link Graph router skipped: %s", exc)

    # Sophia KI — ファイルシステム CRUD
    try:
        from mekhane.api.routes.sophia import router as sophia_router
        app.include_router(sophia_router, prefix=API_PREFIX)
        logger.info("Sophia KI router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Sophia KI router skipped: %s", exc)

    # Symploke — 埋め込みモデル (ベクトル検索) に依存するため遅延ロード
    try:
        from mekhane.api.routes.symploke import router as symploke_router
        app.include_router(symploke_router, prefix=API_PREFIX)
        logger.info("Symploke router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Symploke router skipped: %s", exc)

    # Phantazein (F1) — 常時 Boot / ナレーション。遅延ロード。
    try:
        from mekhane.api.routes.phantazein import router as phantazein_router
        app.include_router(phantazein_router, prefix=API_PREFIX)
        logger.info("Phantazein router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Phantazein router skipped: %s", exc)

    # Synteleia — 6視点認知アンサンブル監査 (外部依存なし)
    try:
        from mekhane.api.routes.synteleia import router as synteleia_router
        app.include_router(synteleia_router, prefix=API_PREFIX)
        logger.info("Synteleia router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Synteleia router skipped: %s", exc)

    # Basanos — SweepEngine 多視点スキャン + ResponseCache
    try:
        from mekhane.api.routes.basanos import router as basanos_router
        app.include_router(basanos_router, prefix=API_PREFIX)
        logger.info("Basanos router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Basanos router skipped: %s", exc)

    # Timeline — セッション・タイムライン (ファイルシステム IO のみ)
    try:
        from mekhane.api.routes.timeline import router as timeline_router
        app.include_router(timeline_router, prefix=API_PREFIX)
        logger.info("Timeline router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Timeline router skipped: %s", exc)

    # Session Notes — F2 セッション＝ノート (SessionNotes に依存)
    try:
        from mekhane.api.routes.notes import router as notes_router
        app.include_router(notes_router, prefix=API_PREFIX)
        logger.info("Session Notes router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Session Notes router skipped: %s", exc)

    # Kalon — Fix(G∘F) 判定の記録と参照
    try:
        from mekhane.api.routes.kalon import router as kalon_router
        app.include_router(kalon_router, prefix=API_PREFIX)
        logger.info("Kalon router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Kalon router skipped: %s", exc)

    # MCP Gateway — PolicyEnforcer + DiscoveryEngine に依存するため遅延ロード
    try:
        from mekhane.api.routes.gateway import router as gateway_router
        app.include_router(gateway_router, prefix=API_PREFIX)
        logger.info("Gateway router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gateway router skipped: %s", exc)

    # HGK Dynamic — hgk_gateway 実関数への動的ルーティング (スタブ置換)
    try:
        from mekhane.api.routes.hgk import router as hgk_router
        app.include_router(hgk_router)
        logger.info("HGK dynamic router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("HGK dynamic router skipped: %s", exc)

    # Digestor — 候補レポート閲覧 (ファイルシステム IO のみ)
    try:
        from mekhane.api.routes.digestor import router as digestor_router
        app.include_router(digestor_router, prefix=API_PREFIX)
        logger.info("Digestor router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Digestor router skipped: %s", exc)

    # Chat — Gemini API SSE プロキシ (httpx に依存するため遅延ロード)
    try:
        from mekhane.api.routes.chat import router as chat_router
        app.include_router(chat_router, prefix=API_PREFIX)
        logger.info("Chat router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Chat router skipped: %s", exc)

    # Quota — agq-check.sh (subprocess) に依存するため遅延ロード
    try:
        from mekhane.api.routes.quota import router as quota_router
        app.include_router(quota_router, prefix=API_PREFIX)
        logger.info("Quota router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Quota router skipped: %s", exc)

    # Aristos — L2 Evolution Dashboard (ファイルシステム IO のみ)
    try:
        from mekhane.api.routes.aristos import router as aristos_router
        app.include_router(aristos_router, prefix=API_PREFIX)
        logger.info("Aristos router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Aristos router skipped: %s", exc)

    # Sentinel — Paper Sentinel レポート (ファイルシステム IO のみ)
    try:
        from mekhane.api.routes.sentinel import router as sentinel_router
        app.include_router(sentinel_router, prefix=API_PREFIX)
        logger.info("Sentinel router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Sentinel router skipped: %s", exc)

    # Epistemic — 認識論的地位レジストリ (YAML ファイル IO のみ)
    try:
        from mekhane.api.routes.epistemic import router as epistemic_router
        app.include_router(epistemic_router, prefix=API_PREFIX)
        logger.info("Epistemic router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Epistemic router skipped: %s", exc)

    # Scheduler — Jules Daily Scheduler ログ (ファイルシステム IO のみ)
    try:
        from mekhane.api.routes.scheduler import router as scheduler_router
        app.include_router(scheduler_router, prefix=API_PREFIX)
        logger.info("Scheduler router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Scheduler router skipped: %s", exc)

    # Periskopē — 研究エンジン API (非同期研究リクエスト・履歴参照)
    try:
        from mekhane.api.routes.periskope import router as periskope_router
        app.include_router(periskope_router, prefix=API_PREFIX)
        logger.info("Periskopē router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Periskopē router skipped: %s", exc)

    # Theorem — 定理使用頻度トラッキング (ファイルシステム IO のみ)
    try:
        from mekhane.api.routes.theorem import router as theorem_router
        app.include_router(theorem_router, prefix=API_PREFIX)
        logger.info("Theorem router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Theorem router skipped: %s", exc)

    # WAL — Intent-WAL ダッシュボードカード (ファイルシステム IO のみ)
    try:
        from mekhane.api.routes.wal import router as wal_router
        app.include_router(wal_router, prefix=API_PREFIX)
        logger.info("WAL router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("WAL router skipped: %s", exc)

    # DevTools — ファイル操作・ターミナル・Ochema AI (CortexClient に依存)
    try:
        from mekhane.api.routes.devtools import router as devtools_router
        app.include_router(devtools_router, prefix=API_PREFIX)
        logger.info("DevTools router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("DevTools router skipped: %s", exc)

    # ============================================================
    # serve.py 統合ルーター群 (旧 hgk.api.serve:app)
    # ============================================================

    # Cortex Ask — LLM 問い合わせプロキシ (ask, ask/stream)
    try:
        from mekhane.api.routes.cortex_ask import router as cortex_ask_router
        app.include_router(cortex_ask_router)
        logger.info("Cortex Ask router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cortex Ask router skipped: %s", exc)

    # Agent — LLM + HGK ツール自律呼出 (Safety Gate 付き)
    try:
        from mekhane.api.routes.agent import router as agent_router
        app.include_router(agent_router)
        logger.info("Agent router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Agent router skipped: %s", exc)

    # Colony — F6 マルチ AI 組織
    try:
        from mekhane.api.routes.colony_route import router as colony_router
        app.include_router(colony_router)
        logger.info("Colony router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Colony router skipped: %s", exc)

    # Jules — 非同期コーディングエージェント
    try:
        from mekhane.api.routes.jules import router as jules_router
        app.include_router(jules_router)
        logger.info("Jules router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Jules router skipped: %s", exc)

    # Files — ローカルファイル操作 API
    try:
        from mekhane.api.routes.files import router as files_router
        app.include_router(files_router)
        logger.info("Files router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Files router skipped: %s", exc)

    # IDE — ConnectRPC + Push SSE + Gateway Trace
    try:
        from mekhane.api.routes.ide import router as ide_router
        app.include_router(ide_router)
        logger.info("IDE router registered")
    except Exception as exc:  # noqa: BLE001
        logger.warning("IDE router skipped: %s", exc)

    # =========================================================================
    # MCP Gateway — FastMCP Streamable HTTP (OAuth 2.1) を同一プロセスにマウント
    # =========================================================================
    # PURPOSE: 旧 hgk-gateway.service (port 8765) を mekhane.api.server に統合。
    #          FastMCP.streamable_http_app() は Starlette アプリを返すため、
    #          FastAPI の app.mount() でサブアプリケーションとして共存できる。
    try:
        from mekhane.mcp.hgk_gateway import mcp as mcp_gateway
        mcp_starlette_app = mcp_gateway.streamable_http_app()
        # FastMCP internal routes expect exact matches for `/mcp`, `/oauth/*`, `/.well-known/*`.
        # By mounting at `/`, we preserve the standalone paths unchanged.
        app.mount("/", mcp_starlette_app)
        logger.info("MCP Gateway mounted at / (handles /mcp, /oauth/*, etc)")
        # SessionManager を app.state に保存 — _lifespan() で run() を呼ぶため
        # (FastAPI の app.mount() はサブアプリの lifespan を呼ばない)
        app.state._mcp_session_manager = mcp_gateway.session_manager
        # gateway_tools のツールを登録 (hgk_gateway 初期化完了後に遅延 import)
        from mekhane.mcp.gateway_tools import register_all
        register_all()
        logger.info("Gateway tools registered (58 tools, 9 domains)")
    except Exception as exc:  # noqa: BLE001
        logger.warning("MCP Gateway mount skipped: %s", exc)


# PURPOSE: アプリケーションインスタンス（uvicorn 用）
app = create_app()


# PURPOSE: 残留ソケットファイルの安全な削除
def _cleanup_stale_socket(uds_path: str) -> None:
    """前回のクラッシュで残ったソケットファイルを削除する。"""
    sock = Path(uds_path)
    if sock.exists():
        try:
            # ソケットファイルかどうか確認
            import stat
            if stat.S_ISSOCK(sock.stat().st_mode):
                sock.unlink()
                logger.info("Removed stale socket: %s", uds_path)
            else:
                logger.error("%s exists but is not a socket file", uds_path)
                sys.exit(1)
        except OSError as e:
            logger.error("Cannot remove %s: %s", uds_path, e)
            sys.exit(1)


# PURPOSE: CLI エントリポイント
def main() -> int:
    """サーバーを起動する。"""
    import uvicorn

    parser = argparse.ArgumentParser(description="Hegemonikón API Server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port (default: {DEFAULT_PORT})")
    parser.add_argument("--host", default="127.0.0.1", help="Host (default: 127.0.0.1)")
    parser.add_argument("--uds", type=str, default=None,
                        help=f"Unix Domain Socket path (default: None, use --uds for Tauri mode)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    if args.uds:
        # UDS モード — Tauri デスクトップアプリ用
        _cleanup_stale_socket(args.uds)
        logger.info("Starting Hegemonikón API on UDS: %s", args.uds)
        uvicorn.run(
            "mekhane.api.server:app",
            uds=args.uds,
            reload=args.reload,
            log_level="info",
        )
    else:
        # TCP モード — 開発・n8n 連携用
        logger.info("Starting Hegemonikón API on %s:%d", args.host, args.port)
        uvicorn.run(
            "mekhane.api.server:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
