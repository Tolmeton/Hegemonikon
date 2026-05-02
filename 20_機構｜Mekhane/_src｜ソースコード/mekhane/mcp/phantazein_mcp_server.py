#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/phantazein_mcp_server.py
# PURPOSE: F1 Phantazein MCP Server — 常時 Boot 機構の MCP プロキシ層 + V-012 運用監視
"""
Phantazein MCP Server v1.2 — Hegemonikon Always-On Boot Mechanism

FastAPI 上で稼働している Phantazein 常駐プロセスに HTTP でリクエストを委譲する
Thin Proxy 層。MCPBase パターンで prostasia/sekisho フックを装着。

Tools:
  - phantazein_ping: ヘルスチェック
  - phantazein_boot: セッション開始 + Boot Context 取得
  - phantazein_snapshot: PJ 進捗スナップショット記録
  - phantazein_consistency: 不整合チェック (Gemini Flash 経由)
  - phantazein_status: 現在の Phantazein サービス状態
  - phantazein_health: MCP サーバー死活監視 (V-012)
  - phantazein_quota: Token 消費監視 (V-012)

Resources:
  - phantazein://status: Boot Cache の現在状態

Architecture:
  MCP Server (この薄いプロキシ, stdio)
    ↓ HTTP (localhost:9696)
  FastAPI phantazein.py (常時稼働サービス)
    ↓ read/write
  SQLite phantazein.db (永続状態)
"""

import sys
import os
import json
from pathlib import Path
from mekhane.mcp.mcp_base import MCPBase, StdoutSuppressor, run_sync

with StdoutSuppressor():
    import httpx

_base = MCPBase(
    name="phantazein",
    version="1.2.0",
    instructions=(
        "Phantazein API integration. Provides always-on Boot Context, "
        "project progress snapshots, consistency checks, "
        "MCP health monitoring (V-012), and quota tracking."
    ),
)
server = _base.server
log = _base.log
TextContent = _base.TextContent
Tool = _base.Tool

from mcp.types import Resource

# ── Config ──────────────────────────────────────────────────

MB_API_BASE = os.getenv("HGK_MB_API", "http://127.0.0.1:9696/api/phantazein")

# MCP サーバー定義 (V-012 死活監視対象)
MCP_SERVERS = [
    {"name": "ochema",     "port": 9701},
    {"name": "sympatheia", "port": 9702},
    {"name": "hermeneus",  "port": 9703},
    {"name": "phantazein", "port": 9704},
    {"name": "sekisho",    "port": 9705},
    {"name": "periskope",  "port": 9706},
    {"name": "digestor",   "port": 9707},
    {"name": "jules",      "port": 9708},
    {"name": "typos",      "port": 9709},
    {"name": "phantazein-boot","port": 9710},
]


# ── HTTP helpers ────────────────────────────────────────────


# PURPOSE: FastAPI に GET リクエストを送って結果を返す (同期)
def _http_get(path: str, timeout: float = 10.0) -> dict:
    try:
        with httpx.Client(timeout=timeout) as client:
            res = client.get(f"{MB_API_BASE}{path}")
            res.raise_for_status()
            return res.json()
    except Exception as e:  # noqa: BLE001
        log(f"HTTP GET {path} error: {e}")
        return {"error": str(e)}


# PURPOSE: FastAPI に POST リクエストを送って結果を返す (同期)
def _http_post(path: str, payload: dict, timeout: float = 30.0) -> dict:
    try:
        with httpx.Client(timeout=timeout) as client:
            res = client.post(f"{MB_API_BASE}{path}", json=payload)
            res.raise_for_status()
            return res.json()
    except Exception as e:  # noqa: BLE001
        log(f"HTTP POST {path} error: {e}")
        return {"error": str(e)}


# ============ Resources ============


# PURPOSE: phantazein の MCP リソース一覧を返す
@server.list_resources()
async def list_resources():
    return [
        Resource(
            uri="phantazein://status",
            name="Phantazein System Status",
            description="Returns current status of the Phantazein system, including recent sessions and projects.",
            mimeType="application/json",
        ),
    ]


# PURPOSE: phantazein リソースの内容を返す
@server.read_resource()
async def read_resource(uri: str):
    uri_str = str(uri)
    log(f"read_resource: {uri_str}")
    if uri_str == "phantazein://status":
        data = await run_sync(_http_get, "/status")
        return json.dumps(data, ensure_ascii=False, indent=2)
    return f'{{"error": "Unknown resource: {uri_str}"}}'


# ============ Tools ============


# PURPOSE: phantazein の MCP ツール一覧を返す
@server.list_tools()
async def list_tools():
    log("list_tools called")
    return [
        # ── boot: 独立維持 (最重要ツール) ──
        Tool(
            name="phantazein_boot",
            description=(
                "Start or register a session and get the latest Boot Context configuration. "
                "Required to get the 16 axes without running expensive scripts. "
                "Example: phantazein_boot(agent='claude', mode='fast')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent": {"type": "string", "description": "Agent name (e.g. 'claude', 'gemini')", "default": "claude"},
                    "mode": {"type": "string", "description": "Boot mode: 'fast', 'standard', or 'detailed'", "default": "fast"},
                    "context": {"type": "string", "description": "Optional: Session context"},
                },
            },
        ),
        # ── check: health/consistency/orphans/cache 診断ファサード ──
        Tool(
            name="phantazein_check",
            description=(
                "診断・検証ツール。scope でスコープを選択: "
                "health=MCP サーバー死活監視 (V-012), "
                "consistency=Handoff 不整合チェック (LLM), "
                "orphans=孤立アーティファクト検出, "
                "cache=Boot Context キャッシュ診断。"
                "Example: phantazein_check(scope='health')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "scope": {
                        "type": "string",
                        "enum": ["health", "consistency", "orphans", "cache"],
                        "description": "診断スコープ: health(死活), consistency(不整合), orphans(孤立), cache(キャッシュ)",
                    },
                    "server_filter": {"type": "string", "description": "scope=health 時: 特定サーバーのみチェック"},
                    "proposed_action": {"type": "string", "description": "scope=consistency 時: 検証対象の予定作業"},
                    "session_id": {"type": "string", "description": "scope=consistency 時: セッション ID"},
                    "min_size_bytes": {"type": "integer", "default": 1000, "description": "scope=orphans 時: 最小ファイルサイズ"},
                },
                "required": ["scope"],
            },
        ),
        # ── session: sessions/sync/classify/report/snapshot 管理ファサード ──
        Tool(
            name="phantazein_session",
            description=(
                "セッション・アーティファクト管理。action で操作を選択: "
                "list=セッション一覧, sync=DB同期, classify=F2分類, "
                "report=分析レポート生成, snapshot=PJ進捗記録。"
                "Example: phantazein_session(action='list', days=7)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "sync", "classify", "report", "snapshot"],
                        "description": "操作: list(一覧), sync(同期), classify(分類), report(レポート), snapshot(スナップ)",
                    },
                    # list 用
                    "limit": {"type": "integer", "default": 20, "description": "action=list 時: 最大件数"},
                    "status": {"type": "string", "description": "action=list 時: ステータスフィルタ"},
                    "days": {"type": "integer", "description": "action=list/report 時: 対象日数"},
                    "session_id": {"type": "string", "description": "action=list/classify 時: 特定セッション ID"},
                    # sync 用
                    "mode": {"type": "string", "enum": ["full", "incremental"], "default": "incremental", "description": "action=sync 時: 同期モード"},
                    # classify 用
                    "axes_id": {"type": "integer", "description": "action=classify 時: FieldAxes ID"},
                    "cluster_label": {"type": "string", "description": "action=classify 時: クラスターラベルフィルタ"},
                    "summary_only": {"type": "boolean", "default": False, "description": "action=classify 時: サマリーのみ"},
                    # report 用
                    "output_path": {"type": "string", "default": "", "description": "action=report 時: 出力ファイルパス"},
                    "compact": {"type": "boolean", "default": False, "description": "action=report 時: コンパクトモード"},
                    # snapshot 用
                    "project_id": {"type": "string", "description": "action=snapshot 時: プロジェクト ID"},
                    "phase": {"type": "string", "description": "action=snapshot 時: フェーズ"},
                    "snapshot_status": {"type": "string", "enum": ["green", "yellow", "red", "blocked"], "description": "action=snapshot 時: ステータス"},
                    "notes": {"type": "string", "description": "action=snapshot 時: メモ"},
                },
                "required": ["action"],
            },
        ),
        # ── info: ping/status/quota 情報ファサード ──
        Tool(
            name="phantazein_info",
            description=(
                "Phantazein の状態・管理情報を照会。action で操作を選択: "
                "ping=ヘルスチェック, status=サービス状態, quota=LLM API 残量。"
                "Example: phantazein_info(action='ping')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["ping", "status", "quota"],
                        "description": "操作: ping(死活), status(状態), quota(API残量)",
                    },
                    "account": {"type": "string", "default": "default", "description": "action=quota 時: TokenVault アカウント"},
                },
                "required": ["action"],
            },
        ),
    ]


# PURPOSE: MCP ツール呼び出しを処理する
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    log(f"call_tool: {name}")

    # ── エイリアス層: 旧ツール名 → 新ファサードにリダイレクト ──
    _ALIASES = {
        # check ファサード
        "phantazein_ping":         ("phantazein_info",    {"action": "ping"}),
        "phantazein_health":       ("phantazein_check",   {"scope": "health"}),
        "phantazein_consistency":  ("phantazein_check",   {"scope": "consistency"}),
        "phantazein_orphans":      ("phantazein_check",   {"scope": "orphans"}),
        "phantazein_cache_status": ("phantazein_check",   {"scope": "cache"}),
        # session ファサード
        "phantazein_sessions":     ("phantazein_session", {"action": "list"}),
        "phantazein_sync":         ("phantazein_session", {"action": "sync"}),
        "phantazein_classify":     ("phantazein_session", {"action": "classify"}),
        "phantazein_report":       ("phantazein_session", {"action": "report"}),
        "phantazein_snapshot":     ("phantazein_session", {"action": "snapshot"}),
        # info ファサード
        "phantazein_status":       ("phantazein_info",    {"action": "status"}),
        "phantazein_quota":        ("phantazein_info",    {"action": "quota"}),
    }
    if name in _ALIASES:
        new_name, defaults = _ALIASES[name]
        arguments = {**defaults, **arguments}
        name = new_name
        log(f"  alias → {name} ({arguments})")

    # ── info ファサード: ping/status/quota ──
    if name == "phantazein_info":
        action = arguments.get("action", "ping")
        if action == "ping":
            return [TextContent(type="text", text="pong (phantazein v1.2)")]
        elif action == "status":
            name = "phantazein_status"
        elif action == "quota":
            name = "phantazein_quota"

    # ── check ファサード → 旧ツール名に展開 ──
    if name == "phantazein_check":
        scope = arguments.get("scope", "health")
        _CHECK_MAP = {
            "health": "phantazein_health",
            "consistency": "phantazein_consistency",
            "orphans": "phantazein_orphans",
            "cache": "phantazein_cache_status",
        }
        name = _CHECK_MAP.get(scope, "phantazein_health")

    # ── session ファサード → 旧ツール名に展開 ──
    if name == "phantazein_session":
        action = arguments.get("action", "list")
        _SESSION_MAP = {
            "list": "phantazein_sessions",
            "sync": "phantazein_sync",
            "classify": "phantazein_classify",
            "report": "phantazein_report",
            "snapshot": "phantazein_snapshot",
        }
        name = _SESSION_MAP.get(action, "phantazein_sessions")
        # snapshot の status パラメータ名を復元
        if action == "snapshot" and "snapshot_status" in arguments:
            arguments["status"] = arguments.pop("snapshot_status")

    # ── boot ────────────────────────────────────────────
    elif name == "phantazein_boot":
        mode = arguments.get("mode", "fast")
        context_arg = arguments.get("context", "") or None

        # Direct call to get_boot_context (no FastAPI dependency)
        def _sync_boot():
            from mekhane.symploke.boot_integration import get_boot_context
            return get_boot_context(mode=mode, context=context_arg)

        try:
            result = await run_sync(_sync_boot, timeout_sec=120.0)
        except Exception as e:  # noqa: BLE001
            return [TextContent(type="text", text=f"Boot failed: {e}")]

        # Extract the consolidated formatted output
        top_level_formatted = result.get("formatted", "")
        if top_level_formatted:
            output = top_level_formatted
        else:
            # Fallback: concatenate per-axis formatted fields
            parts = []
            for k, v in result.items():
                if k == "formatted":
                    continue
                if isinstance(v, dict):
                    fmt = v.get("formatted", "")
                    if fmt:
                        parts.append(fmt)
                elif isinstance(v, str) and v:
                    parts.append(f"[{k}] {v}")
            output = "\n\n".join(parts) if parts else "Boot context empty."

        # ── CAG Fallback キャッシュ作成 (mode != "fast") ──────────
        # プライマリ: Agent が /boot WF Phase 6.3 で cache_boot_context() を呼ぶ
        # フォールバック: Agent が Phase 6.3 を省略した場合のために、ここでも作成する
        # get_or_create_boot_cache の冪等性により、二重作成しても API コスト以外の実害なし
        cag_hint = ""
        if mode != "fast":
            try:
                from mekhane.ochema.cortex_cache import get_cache
                ctx_cache = get_cache()
                if ctx_cache.is_available:
                    ttl = 7200 if mode == "detailed" else 3600
                    # get_or_create_boot_cache は冪等 — 同一ハッシュならスキップ
                    # 注: phantazein は ochema とは別プロセスのため、
                    # CortexCache のインメモリ短絡は無効。list_caches API で冪等性を保証
                    info = await run_sync(
                        ctx_cache.get_or_create_boot_cache,
                        output,
                        system_instruction="あなたは Hegemonikón (HGK) 体系の専門家です。Boot Context に基づいて質問に回答してください。",
                        ttl=ttl,
                        timeout_sec=30.0,  # boot の 120s 予算のうち CAG に 30s を割当
                    )
                    cag_hint = (
                        f"\n\n---\n🔑 **CAG Boot Cache**: `{info.name}`\n"
                        f"- tokens: {info.token_count}, TTL: {ttl // 3600}h\n"
                        f"- 使用: `ask_cortex(cached_content='{info.name}')`"
                    )
                    log(f"CAG auto-cache: {info.name} ({info.token_count} tokens, ttl={ttl}s)")
            except Exception as e:  # noqa: BLE001
                # CAG 失敗は boot をブロックしない
                log(f"CAG auto-cache skipped: {e}")

        return [TextContent(type="text", text=output + cag_hint)]

    # ── snapshot ────────────────────────────────────────
    elif name == "phantazein_snapshot":
        def _sync_snapshot():
            from mekhane.symploke.phantazein_store import get_store
            store = get_store()
            store.add_project_snapshot(
                project_id=arguments.get("project_id"),
                phase=arguments.get("phase"),
                status=arguments.get("status"),
                notes=arguments.get("notes", ""),
                session_id=arguments.get("session_id", ""),
            )
            return {"success": True, "project_id": arguments.get("project_id")}

        try:
            result = await run_sync(_sync_snapshot, timeout_sec=10.0)
            return [TextContent(type="text", text=f"Snapshot recorded: {result.get('project_id')}")]
        except Exception as e:  # noqa: BLE001
            return [TextContent(type="text", text=f"Snapshot failed: {e}")]

    # ── consistency ─────────────────────────────────────
    elif name == "phantazein_consistency":
        proposed_action = arguments.get("proposed_action", "")
        session_id = arguments.get("session_id", "")

        def _sync_consistency():
            """Gather handoff context for the consistency prompt."""
            from mekhane.symploke.boot_integration import get_boot_context
            ctx = get_boot_context(mode="fast")
            handoff_text = "No handoff data."
            if "handoffs" in ctx:
                hf = ctx["handoffs"]
                handoff_text = hf.get("formatted", "") if isinstance(hf, dict) else ""
            return handoff_text

        try:
            handoff_text = await run_sync(_sync_consistency, timeout_sec=60.0)
        except Exception as e:  # noqa: BLE001
            return [TextContent(type="text", text=f"Consistency check failed (boot): {e}")]

        prompt = f"""あなたは Hegemonikon の行動パターン監査官（Consistency Checker）です。
以下の直近のHandoff（引き継ぎ事項）と、Agent がこれから行おうとしている「予定作業」を比較し、
作業の重複、方向性の矛盾、または見落としがないか検査してください。

[直近の Handoffs]
{handoff_text[:8000]}

[予定作業]
{proposed_action}

[出力形式 (厳密なJSONのみ)]
{{
  "has_issues": true/false,
  "issues": [
    {{"severity": "high/medium/low", "issue": "問題の簡潔な説明", "details": "詳細"}}
  ],
  "narration": "AIへ向けた1-2文のPush型メッセージ"
}}"""

        def _sync_llm_check():
            from mekhane.ochema.service import OchemaService
            from mekhane.ochema.model_defaults import FLASH
            svc = OchemaService.get()
            result = svc.ask(message=prompt, model=FLASH,
                            system_instruction="You must respond in valid JSON format only.")
            text = result.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())

        try:
            data = await run_sync(_sync_llm_check, timeout_sec=60.0)
        except Exception as e:  # noqa: BLE001
            return [TextContent(type="text", text=f"Consistency check failed (LLM): {e}")]

        # Log issues to store
        try:
            def _sync_log_issues():
                from mekhane.symploke.phantazein_store import get_store
                store = get_store()
                for iss in data.get("issues", []):
                    store.log_consistency_issue(
                        session_id=session_id,
                        issue=iss.get("issue", "Unknown"),
                        severity=iss.get("severity", "medium"),
                        details=iss.get("details", ""),
                    )
            await run_sync(_sync_log_issues, timeout_sec=10.0)
        except Exception:  # noqa: BLE001
            pass  # Logging failure should not block the response

        output = f"Consistency Check: {data.get('narration', '')}\n\n"
        if data.get("has_issues"):
            output += "⚠️ ISSUES DETECTED:\n"
            for iss in data.get("issues", []):
                output += f"- [{iss.get('severity', 'medium')}] {iss.get('issue')}: {iss.get('details')}\n"
        else:
            output += "✅ No inconsistencies detected."
        return [TextContent(type="text", text=output)]

    # ── status ──────────────────────────────────────────
    elif name == "phantazein_status":
        def _sync_status():
            from mekhane.symploke.phantazein_store import get_store
            store = get_store()
            return store.get_stats()

        try:
            data = await run_sync(_sync_status, timeout_sec=10.0)
            return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]
        except Exception as e:  # noqa: BLE001
            return [TextContent(type="text", text=f"Status failed: {e}")]

    # ── health (V-012) ─────────────────────────────────
    elif name == "phantazein_health":
        server_filter = arguments.get("server_filter", "")

        def _sync_health():
            # 対象サーバーを決定
            targets = MCP_SERVERS
            if server_filter:
                targets = [s for s in MCP_SERVERS if s["name"] == server_filter]
                if not targets:
                    return {"error": f"Unknown server: {server_filter}"}

            # HTTP レベルチェック実行 (TCP + HTTP 二段判定)
            results = [_check_server(s["name"], s["port"]) for s in targets]

            # DB に永続化
            from mekhane.symploke.phantazein_store import get_store
            store = get_store()
            store.log_health_batch(results)

            # サマリー構築
            up = sum(1 for r in results if r["status"] == "up")
            degraded = sum(1 for r in results if r["status"] == "degraded")
            down = len(results) - up - degraded
            parts = [f"{up} UP"]
            if degraded:
                parts.append(f"{degraded} DEGRADED")
            parts.append(f"{down} DOWN")
            return {
                "summary": " / ".join(parts),
                "servers": results,
                "health_summary": store.get_health_summary(),
            }

        try:
            data = await run_sync(_sync_health, timeout_sec=30.0)
            if "error" in data:
                return [TextContent(type="text", text=f"Health check error: {data['error']}")]

            # フォーマット出力
            lines = [f"🏥 MCP Health: {data['summary']}", ""]
            for s in data.get("servers", []):
                if s["status"] == "up":
                    icon = "🟢"
                elif s["status"] == "degraded":
                    icon = "🟡"
                else:
                    icon = "🔴"
                latency = f" ({s['latency_ms']}ms)" if s.get("latency_ms") else ""
                err = f" — {s['error']}" if s.get("error") else ""
                lines.append(f"{icon} {s['server_name']:12s} :{s['port']}{latency}{err}")

            # 24h 障害統計
            failures = data.get("health_summary", {}).get("failures_24h", {})
            if failures:
                lines.append("")
                lines.append("⚠️ 24h failures:")
                for name_k, count in failures.items():
                    lines.append(f"  {name_k}: {count} failures")

            return [TextContent(type="text", text="\n".join(lines))]
        except Exception as e:  # noqa: BLE001
            return [TextContent(type="text", text=f"Health check failed: {e}")]

    # ── quota (V-012) ──────────────────────────────────
    elif name == "phantazein_quota":
        account = arguments.get("account", "default")

        def _sync_quota():
            from mekhane.ochema.cortex import CortexClient
            client = CortexClient(account=account)
            return client.get_quota()

        try:
            data = await run_sync(_sync_quota, timeout_sec=15.0)
            # フォーマット出力
            lines = ["📊 LLM Quota Status", ""]
            if isinstance(data, dict):
                for model, info in data.items():
                    if isinstance(info, dict):
                        remaining = info.get("remaining", "?")
                        limit = info.get("limit", "?")
                        pct = info.get("pct", 0)
                        icon = "🟢" if pct > 50 else ("🟡" if pct > 20 else "🔴")
                        lines.append(f"{icon} {model}: {remaining}/{limit} ({pct:.0f}%)")
                    else:
                        lines.append(f"  {model}: {info}")
            else:
                lines.append(str(data))
            return [TextContent(type="text", text="\n".join(lines))]
        except Exception as e:  # noqa: BLE001
            return [TextContent(type="text", text=f"Quota check failed: {e}")]

    # ── sync (S1) ──────────────────────────────────
    elif name == "phantazein_sync":
        mode = arguments.get("mode", "incremental")

        def _sync_exec():
            from mekhane.symploke.phantazein_indexer import full_sync, incremental_sync
            if mode == "full":
                return full_sync()
            else:
                return incremental_sync()

        try:
            data = await run_sync(_sync_exec, timeout_sec=120.0)
            lines = [f"🔄 Sync completed ({mode})", ""]
            lines.append(f"  Sessions: {data.get('sessions', 0)}")
            lines.append(f"  Artifacts: {data.get('total_artifacts', 0)}")
            lines.append(f"  Handoffs: {data.get('handoffs', 0)}")
            lines.append(f"  ROMs: {data.get('roms', 0)}")
            lines.append(f"  Duration: {data.get('duration_sec', 0)}s")
            return [TextContent(type="text", text="\n".join(lines))]
        except Exception as e:  # noqa: BLE001
            return [TextContent(type="text", text=f"Sync failed: {e}")]

    # ── sessions (S1) ───────────────────────────────
    elif name == "phantazein_sessions":
        session_id = arguments.get("session_id", "")

        def _sync_sessions():
            from mekhane.symploke.phantazein_store import get_store
            store = get_store()
            if session_id:
                return {"type": "detail", "data": store.get_session_with_artifacts(session_id)}
            return {
                "type": "list",
                "data": store.get_ide_sessions(
                    limit=arguments.get("limit", 20),
                    status=arguments.get("status"),
                    days=arguments.get("days"),
                ),
            }

        try:
            result = await run_sync(_sync_sessions, timeout_sec=10.0)
            if result["type"] == "detail":
                d = result["data"]
                if not d:
                    return [TextContent(type="text", text=f"Session not found: {session_id}")]
                lines = [f"📁 Session: {d.get('title', d['id'])}"]
                lines.append(f"  Created: {d.get('created_at', '')}")
                lines.append(f"  Artifacts: {d.get('artifact_count', 0)}")
                for a in d.get("artifacts", []):
                    std = "⭐" if a.get("is_standard") else "📝"
                    lines.append(f"  {std} {a['filename']} ({a.get('size_bytes', 0)}B) — {a.get('summary', '')[:60]}")
                return [TextContent(type="text", text="\n".join(lines))]
            else:
                sessions = result["data"]
                lines = [f"📁 IDE Sessions ({len(sessions)} results)", ""]
                for s in sessions:
                    lines.append(f"  {s['id'][:8]}.. | {s.get('title', '(no title)')[:40]} | {s.get('artifact_count', 0)} arts")
                return [TextContent(type="text", text="\n".join(lines))]
        except Exception as e:  # noqa: BLE001
            return [TextContent(type="text", text=f"Sessions query failed: {e}")]

    # ── orphans (S1) ────────────────────────────────
    elif name == "phantazein_orphans":
        min_size = arguments.get("min_size_bytes", 1000)

        def _sync_orphans():
            from mekhane.symploke.phantazein_store import get_store
            store = get_store()
            return store.get_orphan_artifacts(min_size_bytes=min_size)

        try:
            orphans = await run_sync(_sync_orphans, timeout_sec=10.0)
            if not orphans:
                return [TextContent(type="text", text="✅ No orphan artifacts detected.")]
            lines = [f"⚠️ Orphan Artifacts ({len(orphans)} found, min {min_size}B)", ""]
            for o in orphans:
                lines.append(
                    f"  📝 {o['filename']} ({o['size_bytes']:,}B) "
                    f"| Session: {o.get('session_title', o['session_id'][:8])} "
                    f"| {o.get('summary', '')[:50]}"
                )
            return [TextContent(type="text", text="\n".join(lines))]
        except Exception as e:  # noqa: BLE001
            return [TextContent(type="text", text=f"Orphan detection failed: {e}")]

    # ── report (S1) ─────────────────────────────────────
    elif name == "phantazein_report":
        days = arguments.get("days", 30)
        output_path = arguments.get("output_path", "")
        compact = arguments.get("compact", False)

        def _sync_report():
            from mekhane.symploke.phantazein_reporter import generate_report
            return generate_report(days=days, output_path=output_path, compact=compact)

        try:
            report = await run_sync(_sync_report, timeout_sec=30.0)
            # compact モードはサイズが小さいのでトランケーション不要
            max_len = 30000 if compact else 10000
            if len(report) > max_len:
                truncated = report[:max_len - 2000]
                truncated += f"\n\n... (省略: 全{len(report):,}文字)"
                if output_path:
                    truncated += f"\n\n📄 ファイルに保存済み: {output_path}"
                return [TextContent(type="text", text=truncated)]
            return [TextContent(type="text", text=report)]
        except Exception as e:  # noqa: BLE001
            return [TextContent(type="text", text=f"Report generation failed: {e}")]

    # ── classify (P6/F2) ────────────────────────────────
    elif name == "phantazein_classify":
        axes_id = arguments.get("axes_id")
        session_id = arguments.get("session_id", "")
        cluster_label = arguments.get("cluster_label", "")
        summary_only = arguments.get("summary_only", False)

        def _sync_classify():
            from mekhane.symploke.phantazein_store import get_store
            store = get_store()

            current_axes_id = axes_id
            if current_axes_id is None:
                latest = store.get_latest_field_axes()
                if latest:
                    current_axes_id = latest["id"]

            if current_axes_id is None:
                return {"error": "No FieldAxes found in database. Run field_classifier first."}

            if summary_only:
                return {
                    "type": "summary",
                    "axes_id": current_axes_id,
                    "data": store.get_classification_summary(current_axes_id)
                }
            
            if session_id:
                return {
                    "type": "single",
                    "axes_id": current_axes_id,
                    "data": store.get_session_classification(session_id, current_axes_id)
                }
            
            return {
                "type": "list",
                "axes_id": current_axes_id,
                "data": store.get_all_classifications(current_axes_id, cluster_label)
            }

        try:
            res = await run_sync(_sync_classify, timeout_sec=10.0)
            if "error" in res:
                return [TextContent(type="text", text=f"Classification failed: {res['error']}")]
            
            lines = [f"📊 Classification Results (Axes ID: {res['axes_id']})", ""]
            if res["type"] == "summary":
                for s in res["data"]:
                    lines.append(f"  - {s['cluster_label']}: {s['count']} sessions (avg confidence: {s['avg_confidence']:.2f})")
            elif res["type"] == "single":
                d = res["data"]
                if not d:
                    lines.append(f"  Session {session_id} not found in classification results.")
                else:
                    lines.append(f"  Session: {d['session_id']}")
                    lines.append(f"  Cluster: {d['cluster_label']} (confidence: {d['confidence']:.2f})")
                    lines.append(f"  Tags: {d['tags_json']}")
            else:
                data = res["data"]
                lines.append(f"  Total {len(data)} sessions categorized.")
                for d in data[:50]:
                    lines.append(f"  - [{d['cluster_label']:^15s}] {d['session_id'][:8]} | conf: {d['confidence']:.2f} | tags: {d.get('tags_json', '[]')}")
                if len(data) > 50:
                    lines.append("  ... (truncated)")

            return [TextContent(type="text", text="\n".join(lines))]
        except Exception as e:  # noqa: BLE001
            return [TextContent(type="text", text=f"Classification query failed: {e}")]

    # ── cache_status ── Always-On Boot 診断 ──────────────
    elif name == "phantazein_cache_status":
        def _sync_cache_status():
            from mekhane.symploke.phantazein_store import get_store
            from mekhane.symploke.phantazein_watcher import watcher_status
            store = get_store()
            cache_info = store.get_boot_cache_status()
            watcher_info = watcher_status()
            return {
                "cache": cache_info,
                "watcher": watcher_info,
            }

        try:
            result = await run_sync(_sync_cache_status, timeout_sec=10.0)
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False, default=str))]
        except Exception as e:  # noqa: BLE001
            return [TextContent(type="text", text=f"Cache status failed: {e}")]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]



# ── V-012 Health Check Logic ─────────────────────────────


# PURPOSE: TCP + HTTP 二段チェックで MCP サーバーの死活を判定する
# 3段判定: up (HTTP応答あり) / degraded (TCP OK, HTTP NG) / down (TCP NG)
def _check_server(name: str, port: int, tcp_timeout: float = 2.0, http_timeout: float = 3.0) -> dict:
    """TCP + HTTP 二段チェック。socat だけ活きている偽陽性を検出する。"""
    import socket
    import time as _time

    start = _time.monotonic()

    # Phase 1: TCP 接続チェック
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(tcp_timeout)
        sock.connect(("127.0.0.1", port))
        sock.close()
    except Exception as e:  # noqa: BLE001
        elapsed = (_time.monotonic() - start) * 1000
        return {
            "server_name": name,
            "port": port,
            "status": "down",
            "latency_ms": round(elapsed, 1),
            "error": f"TCP: {e}",
        }

    # Phase 2: HTTP レベルチェック — MCP エンドポイントに POST
    # initialize リクエストを送り、レスポンスが返るかで判定
    try:
        with httpx.Client(timeout=http_timeout) as client:
            res = client.post(
                f"http://127.0.0.1:{port}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": "health-check",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {},
                        "clientInfo": {"name": "phantazein-health", "version": "1.0"},
                    },
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            )
            elapsed = (_time.monotonic() - start) * 1000
            # 任意のレスポンス (200, 4xx でも) = プロセスは生きている
            # 接続拒否/タイムアウトのみが「プロセスなし」を示す
            return {
                "server_name": name,
                "port": port,
                "status": "up",
                "latency_ms": round(elapsed, 1),
                "error": "",
            }
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.RemoteProtocolError) as e:
        # TCP は通ったが HTTP は失敗 = socat は活きてるがプロセスが死んでいる
        # RemoteProtocolError: socat が TCP を受けて即切断する (バックエンド不在)
        elapsed = (_time.monotonic() - start) * 1000
        return {
            "server_name": name,
            "port": port,
            "status": "degraded",
            "latency_ms": round(elapsed, 1),
            "error": f"TCP OK but HTTP failed: {e}",
        }
    except httpx.ReadTimeout as e:
        # ReadTimeout: TCP + HTTP ハンドシェイクは成功したがレスポンスが遅い
        # プロセスは生きているが応答が遅い → up (ただし error 付き)
        elapsed = (_time.monotonic() - start) * 1000
        return {
            "server_name": name,
            "port": port,
            "status": "up",
            "latency_ms": round(elapsed, 1),
            "error": f"HTTP slow response: {e}",
        }
    except Exception as e:  # noqa: BLE001
        # その他の例外 (ReadError, WriteError 等)
        # TCP が通った後のエラー → プロセスの存在は不確実だが down ではない
        elapsed = (_time.monotonic() - start) * 1000
        return {
            "server_name": name,
            "port": port,
            "status": "degraded",
            "latency_ms": round(elapsed, 1),
            "error": f"HTTP error (uncertain): {e}",
        }


# ── Main ────────────────────────────────────────────────────

if __name__ == "__main__":
    # Always-On Boot: ファイル監視デーモンを起動
    try:
        from mekhane.symploke.phantazein_watcher import start_watcher
        if start_watcher():
            log("Boot cache watcher started")
        else:
            log("Boot cache watcher not started (watchdog missing or no dirs)")
    except Exception as e:  # noqa: BLE001
        log(f"Boot cache watcher failed to start: {e}")

    _base.install_all_hooks()
    _base.run()
