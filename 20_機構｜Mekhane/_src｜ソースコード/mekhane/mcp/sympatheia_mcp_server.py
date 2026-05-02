#!/usr/bin/env python3
# PROOF: [L2/Sympatheia] <- mekhane/mcp/
"""
Sympatheia MCP Server v1.1 — Hegemonikón Autonomic Nervous System

Tools: wbc, attractor, digest, feedback, notifications, status
Resources: heartbeat, wbc, config, notifications, digest, attractor
"""

import asyncio
import sys
import os
from pathlib import Path
from mekhane.mcp.mcp_base import MCPBase, StdoutSuppressor, run_sync

_base = MCPBase(
    name="sympatheia",
    version="1.1.0",
    instructions=(
        "Sympatheia 自律神経系。脅威分析(WBC)、定理推薦(Attractor)、"
        "記憶圧縮(Digest)、恒常性(Feedback)、ルーティング(Route)を提供。"
    ),
)
server = _base.server
log = _base.log
TextContent = _base.TextContent
Tool = _base.Tool

# Also need Resource for this server
from mcp.types import Resource

import json as _json

# Lazy Sympatheia import
_sympatheia = None


# PURPOSE: [L2-auto] _get_sympatheia の関数定義
def _get_sympatheia():
    """‪sympatheia.py のヘルパー関数群を安全にインポート。"""
    global _sympatheia
    if _sympatheia is None:
        try:
            with StdoutSuppressor():
                from mekhane.sympatheia import core as sympatheia
            _sympatheia = sympatheia
            log("Sympatheia module loaded")
        except Exception as e:  # noqa: BLE001
            log(f"Sympatheia import error: {e}")
    return _sympatheia


# ============ Resources ============
try:
    from mekhane.paths import MNEME_DIR, STATE_CACHE, STATE_LOGS, STATE_VIOLATIONS
except ImportError:
    _MNEME_STATE = Path(os.getenv("HGK_MNEME", str(MNEME_DIR))) / "05_状態｜State"
    STATE_VIOLATIONS = _MNEME_STATE / "A_違反｜Violations"
    STATE_CACHE = _MNEME_STATE / "B_キャッシュ｜Cache"
    STATE_LOGS = _MNEME_STATE / "C_ログ｜Logs"

# Resource URI -> (L2 path, filename, description)
_RESOURCES = {
    "sympatheia://heartbeat": (STATE_LOGS, "heartbeat.json", "Heartbeat state — beats, healthy, lastBeat"),
    "sympatheia://wbc": (STATE_VIOLATIONS, "wbc_state.json", "WBC state — alerts, totalAlerts, lastEscalation"),
    "sympatheia://config": (STATE_CACHE, "sympatheia_config.json", "Sympatheia config — thresholds, sensitivity"),
    "sympatheia://notifications": (STATE_LOGS, "notifications.jsonl", "Notification log — 最新 20 件"),
    "sympatheia://digest": (STATE_LOGS, "weekly_digest.json", "Weekly digest — 最新の週次集約"),
    "sympatheia://attractor": (STATE_LOGS, "attractor_dispatch.json", "Attractor dispatch history"),
    "sympatheia://audit": (STATE_LOGS, "sympatheia_audit.jsonl", "MCP Audit Log — ツール呼び出し履歴"),
}


# PURPOSE: sympatheia_mcp_server の list resources 処理を実行する
@server.list_resources()
async def list_resources():
    """公開リソース一覧。"""
    resources = []
    for uri, (base_dir, filename, desc) in _RESOURCES.items():
        resources.append(Resource(
            uri=uri,
            name=filename,
            description=desc,
            mimeType="application/json",
        ))
    return resources


# PURPOSE: sympatheia_mcp_server の read resource 処理を実行する
@server.read_resource()
async def read_resource(uri: str):
    """リソース読み取り。"""
    log(f"read_resource: {uri}")
    uri_str = str(uri)
    if uri_str not in _RESOURCES:
        return f"Unknown resource: {uri_str}"
    base_dir, filename, _ = _RESOURCES[uri_str]
    fpath = base_dir / filename
    try:
        raw = fpath.read_text("utf-8")
        if filename.endswith(".jsonl"):
            # JSONL: 最新 20 行を JSON array に変換
            lines = [l.strip() for l in raw.strip().split("\n") if l.strip()][-20:]
            lines.reverse()
            return "[" + ",".join(lines) + "]"
        return raw
    except FileNotFoundError:
        return f"{{}}"
    except Exception as e:  # noqa: BLE001
        return f"Error reading {filename}: {e}"


# ============ Tools ============

# PURPOSE: sympatheia_mcp_server の list tools 処理を実行する
@server.list_tools()
async def list_tools():
    """利用可能なツール一覧（3ファサード統合）。"""
    return [
        # === ファサード 1: 監視・健全性系 ===
        Tool(
            name="sympatheia_monitor",
            description=(
                "監視・健全性ツール。action で操作を選択: "
                "wbc=脅威分析, attractor=定理推薦, feedback=閾値調整, peira_health=サービス健全性, ping=死活確認。"
                "Example: sympatheia_monitor(action='wbc', details='...') "
                "Example: sympatheia_monitor(action='attractor', context='...') "
                "Example: sympatheia_monitor(action='ping')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "操作: wbc(脅威分析), attractor(定理推薦), feedback(閾値調整), peira_health(健全性), ping(死活)",
                        "enum": ["wbc", "attractor", "feedback", "peira_health", "ping"],
                    },
                    # wbc 用
                    "source": {"type": "string", "description": "action=wbc 時: Alert source (e.g. WF-08, manual)", "default": "claude"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"], "default": "medium"},
                    "details": {"type": "string", "description": "action=wbc 時: Description of what happened"},
                    "files": {"type": "array", "items": {"type": "string"}, "description": "action=wbc 時: Related file paths", "default": []},
                    # attractor 用
                    "context": {"type": "string", "description": "action=attractor 時: Input text to recommend theorems for"},
                },
                "required": ["action"],
            },
        ),
        # === ファサード 2: BC 違反系 ===
        Tool(
            name="sympatheia_violations",
            description=(
                "BC 違反の記録・分析ツール。action で操作を選択: "
                "log=違反記録, dashboard=統計ダッシュボード, escalate=エスカレーション候補検出。"
                "Example: sympatheia_violations(action='log', feedback_type='reprimand', description='...') "
                "Example: sympatheia_violations(action='dashboard', period='week') "
                "Example: sympatheia_violations(action='escalate')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "操作: log(違反記録), dashboard(統計), escalate(エスカレーション)",
                        "enum": ["log", "dashboard", "escalate"],
                    },
                    # log 用
                    "feedback_type": {
                        "type": "string",
                        "enum": ["reprimand", "acknowledgment", "self_detected"],
                        "description": "action=log 時: Type: reprimand, acknowledgment, or self_detected",
                    },
                    "bc_ids": {
                        "type": "array", "items": {"type": "string"},
                        "description": "action=log 時: Violated BC/Nomoi IDs (e.g. ['N-1', 'θ3.1'])",
                        "default": [],
                    },
                    "pattern": {
                        "type": "string",
                        "description": "action=log 時: Pattern ID (e.g. skip_bias, selective_omission)",
                        "default": "",
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "default": "medium",
                    },
                    "description": {"type": "string", "description": "action=log 時: What happened"},
                    "context": {"type": "string", "description": "action=log 時: What you were doing at the time", "default": ""},
                    "creator_words": {"type": "string", "description": "action=log 時: Creator's original words", "default": ""},
                    "corrective": {"type": "string", "description": "action=log 時: Corrective action taken", "default": ""},
                    # dashboard 用
                    "period": {
                        "type": "string",
                        "enum": ["today", "week", "month", "all"],
                        "default": "all",
                        "description": "action=dashboard 時: Aggregation period",
                    },
                    # escalate 用
                    "min_severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "default": "high",
                        "description": "action=escalate 時: Minimum severity level",
                    },
                    "min_occurrences": {
                        "type": "integer",
                        "default": 2,
                        "description": "action=escalate 時: Minimum occurrence count",
                    },
                },
                "required": ["action"],
            },
        ),
        # === ファサード 3: 運用・検証系 ===
        Tool(
            name="sympatheia_ops",
            description=(
                "運用・検証ツール。action で操作を選択: "
                "status=全体状態, digest=週次サマリー, notifications=通知管理, "
                "basanos_scan=L0静的解析, verify_on_edit=変更後テスト実行。"
                "Example: sympatheia_ops(action='status') "
                "Example: sympatheia_ops(action='basanos_scan', path='/path/to/file.py') "
                "Example: sympatheia_ops(action='verify_on_edit', changed_files=['/path/to/file.py'])"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "操作: status(全体状態), digest(週次サマリー), notifications(通知管理), basanos_scan(L0静的解析), verify_on_edit(変更後テスト)",
                        "enum": ["status", "digest", "notifications", "basanos_scan", "verify_on_edit"],
                    },
                    # notifications 用
                    "notification_action": {"type": "string", "enum": ["list", "send", "dismiss", "purge"], "default": "list",
                                            "description": "action=notifications 時: 通知操作"},
                    "limit": {"type": "integer", "description": "action=notifications 時: Max items to return", "default": 10},
                    "level": {"type": "string", "description": "action=notifications 時: Filter: INFO|HIGH|CRITICAL"},
                    "notification_source": {"type": "string", "description": "action=notifications 時: Notification source", "default": "claude"},
                    "title": {"type": "string", "description": "action=notifications 時: Notification title"},
                    "body": {"type": "string", "description": "action=notifications 時: Notification body"},
                    "notification_level": {"type": "string", "enum": ["INFO", "HIGH", "CRITICAL"], "default": "INFO"},
                    "id": {"type": "string", "description": "action=notifications 時: Notification ID (for dismiss)"},
                    "include_dismissed": {"type": "boolean", "description": "action=notifications 時: Include dismissed", "default": False},
                    # basanos_scan 用
                    "path": {"type": "string", "description": "action=basanos_scan 時: Absolute path to file or directory"},
                    "max_issues": {"type": "integer", "description": "action=basanos_scan 時: Maximum number of issues", "default": 20},
                    # verify_on_edit 用
                    "changed_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "action=verify_on_edit 時: 変更したファイルの絶対パス",
                    },
                    "include_basanos": {
                        "type": "boolean",
                        "default": True,
                        "description": "action=verify_on_edit 時: L0 静的解析も実行するか",
                    },
                    "max_tests": {
                        "type": "integer",
                        "default": 100,
                        "description": "action=verify_on_edit 時: 実行するテストの上限",
                    },
                },
                "required": ["action"],
            },
        ),
    ]


# PURPOSE: [L2-auto] _log_audit_event の関数定義 (W5 MCPShield プロキシ)
def _log_audit_event(tool_name: str, arguments: dict, status: str = "success", error: str | None = None):
    try:
        from datetime import datetime
        import time
        audit_file = STATE_LOGS / "sympatheia_audit.jsonl"
        safe_args = {}
        for k, v in arguments.items():
            if isinstance(v, str) and len(v) > 1000:
                safe_args[k] = v[:1000] + "...[truncated]"
            else:
                safe_args[k] = v
        entry = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "args": safe_args,
            "status": status
        }
        if error is not None:
            entry["error"] = error
        with open(audit_file, "a", encoding="utf-8") as f:
            f.write(_json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:  # noqa: BLE001
        log(f"Audit log error: {e}")


# PURPOSE: sympatheia_mcp_server の call tool 処理を実行する (MCPShield プロキシ)
@server.call_tool(validate_input=True)
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """ツール実行 (監査プロキシ)。"""
    log(f"call_tool: {name}")
    try:
        result = await _call_tool_impl(name, arguments)
        is_error = False
        error_msg = None
        if result and type(result) is list and len(result) > 0:
            first = result[0]
            if isinstance(first, TextContent) and first.text and first.text.startswith("Error:"):
                is_error = True
                error_msg = first.text
        
        _log_audit_event(
            tool_name=name,
            arguments=arguments,
            status="error" if is_error else "success",
            error=error_msg
        )

        # Prostasia: BC全文注入 + Sekisho監査用ログ蓄積
        if not is_error and result:
            try:
                from mekhane.agent_guard.prostasia import get_prostasia
                prostasia = get_prostasia()
                # レスポンステキストにBC全文を注入
                for i, item in enumerate(result):
                    if isinstance(item, TextContent) and item.text:
                        injected = prostasia.inject_into_response(
                            tool_name=name,
                            arguments=arguments,
                            response_text=item.text,
                        )
                        result[i] = TextContent(type="text", text=injected)
                        break  # 最初のTextContentにのみ注入
            except Exception as e:  # noqa: BLE001
                log(f"Prostasia injection error (non-fatal): {e}")

        return result
    except Exception as e:  # noqa: BLE001
        _log_audit_event(tool_name=name, arguments=arguments, status="error", error=str(e))
        log(f"Error in {name}: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return [TextContent(type="text", text=f"Error: {e}")]


async def _call_tool_impl(name: str, arguments: dict):
    # ── ファサードルーティング (3 facades) ──
    action = arguments.get("action", "")

    # sympatheia_ops: ping は Sympatheia モジュール不要
    if name == "sympatheia_ops" and action == "ping":
        return [TextContent(type="text", text="pong")]

    sym = _get_sympatheia()
    if sym is None:
        return [TextContent(type="text", text="Error: Sympatheia module not available")]

    try:
        # ═══════ sympatheia_monitor ═══════
        if name == "sympatheia_monitor":
            if action == "wbc":
                req = sym.WBCRequest(
                    source=arguments.get("source", "claude"),
                    severity=arguments.get("severity", "medium"),
                    details=arguments.get("details", ""),
                    files=arguments.get("files", []),
                )
                result = await sym.wbc_analyze(req)
                d = result.model_dump()

                lines = [
                    "# 🩸 WBC 脅威分析結果\n",
                    f"- **Threat Score**: {d['threatScore']}/15",
                    f"- **Level**: {d['level']}",
                    f"- **Severity**: {d['severity']}",
                    f"- **Source**: {d['source']}",
                    f"- **Should Escalate**: {'🚨 YES' if d['shouldEscalate'] else 'No'}",
                    f"- **Recent Alerts (1h)**: {d['recentAlertCount']}",
                    f"- **Details**: {d['details']}",
                    f"- **Files**: {', '.join(d['files']) or 'N/A'}",
                ]
                return [TextContent(type="text", text="\n".join(lines))]

            elif action == "attractor":
                context = arguments.get("context", "")
                req = sym.AttractorRequest(context=context)
                result = await sym.attractor_dispatch(req)
                d = result.model_dump()

                if d["recommendation"]:
                    r = d["recommendation"]
                    lines = [
                        "# ⚡ Attractor 定理推薦\n",
                        f"- **Theorem**: {r['theorem']} ({r['name']})",
                        f"- **Series**: {r['series']}",
                        f"- **Command**: `{r['command']}`",
                        f"- **Confidence**: {r['confidence']:.1%}",
                        f"- **Auto-dispatch**: {'Yes' if d['autoDispatch'] else 'No'}",
                        f"\n> Input: {d['context']}",
                    ]
                else:
                    lines = [
                        "# ⚡ Attractor 定理推薦\n",
                        "引力圏外。定理レベルで収束しません。",
                        f"\n> Input: {d['context']}",
                    ]
                return [TextContent(type="text", text="\n".join(lines))]

            elif action == "status":
                # 全 state ファイルサマリ
                mneme = sym.MNEME
                status = {}

                hb = sym._read_json(mneme / "heartbeat.json")
                status["heartbeat"] = f"beats={hb.get('beats', '?')}, healthy={hb.get('healthy', '?')}"

                wbc = sym._read_json(mneme / "wbc_state.json", {"alerts": [], "totalAlerts": 0})
                status["wbc"] = f"totalAlerts={wbc.get('totalAlerts', 0)}, active={len(wbc.get('alerts', []))}"

                git = sym._read_json(mneme / "git_sentinel.json")
                status["git"] = f"dirty={git.get('dirty', '?')}, branch={git.get('branch', '?')}"

                fm = sym._read_json(mneme / "file_monitor_state.json")
                status["fileMon"] = f"scans={fm.get('scanCount', 0)}, changes={fm.get('changeCount', 0)}"

                att = sym._read_json(mneme / "attractor_dispatch.json", {"totalDispatches": 0})
                status["attractor"] = f"totalDispatches={att.get('totalDispatches', 0)}"

                cfg = sym._load_config()
                th = cfg.get("thresholds", {})
                status["config"] = f"health_high={th.get('health_high')}, stale={th.get('stale_minutes')}min"

                wd = sym._read_json(mneme / "weekly_digest.json")
                status["digest"] = f"weekEnding={wd.get('weekEnding', 'N/A')}"

                try:
                    notif_raw = (mneme / "notifications.jsonl").read_text("utf-8").strip().split("\n")
                    crits = [l for l in notif_raw if '"CRITICAL"' in l]
                    status["notifications"] = f"total={len(notif_raw)}, critical={len(crits)}"
                except Exception:  # noqa: BLE001
                    status["notifications"] = "no data"

                lines = ["# 🧬 Sympatheia Status\n"]
                for k, v in status.items():
                    lines.append(f"- **{k}**: {v}")

                return [TextContent(type="text", text="\n".join(lines))]

            elif action == "feedback":
                req = sym.FeedbackRequest()
                result = await sym.feedback_loop(req)
                d = result.model_dump()

                lines = [
                    "# ⚖️ Feedback Loop\n",
                    "## Metrics (3 days)",
                    f"- **Avg Score**: {d['metrics'].get('avg', 0)}",
                    f"- **Trend**: {d['metrics'].get('trend', 0):+.2f}",
                    f"- **Samples**: {d['metrics'].get('samples', 0)}",
                    f"- **WBC Alerts**: {d['metrics'].get('wbcAlerts', 0)}",
                    "\n## Thresholds",
                    f"- health_high: {d['thresholds'].get('health_high', 'N/A')}",
                    f"- health_low: {d['thresholds'].get('health_low', 'N/A')}",
                    f"- stale_minutes: {d['thresholds'].get('stale_minutes', 'N/A')}",
                    f"\n**Adjusted**: {'⚙️ YES' if d['adjusted'] else 'No'}",
                ]
                if d["adjustments"]:
                    lines.append("\n## Adjustments")
                    for a in d["adjustments"]:
                        lines.append(f"- {a}")
                return [TextContent(type="text", text="\n".join(lines))]

            elif action == "peira_health":
                return await _handle_peira_health()

            elif action == "ping":
                return [
                    TextContent(
                        type="text",
                        text="✅ sympatheia_monitor ping OK — Sympatheia MCP は応答しています (Cursor からの疎通確認用)。",
                    )
                ]

            else:
                return [TextContent(type="text", text=f"Unknown sympatheia_monitor action: {action}")]

        # ═══════ sympatheia_violations ═══════
        elif name == "sympatheia_violations":
            if action == "log":
                return await _handle_log_violation(arguments)

            elif action == "dashboard":
                return await _handle_violation_dashboard(arguments)

            elif action == "escalate":
                return await _handle_escalate(arguments)

            else:
                return [TextContent(type="text", text=f"Unknown sympatheia_violations action: {action}")]

        # ═══════ sympatheia_ops ═══════
        elif name == "sympatheia_ops":
            if action == "basanos_scan":
                return await _handle_basanos_scan(arguments)

            elif action == "verify_on_edit":
                return await _handle_verify_on_edit(arguments)

            elif action == "digest":
                req = sym.DigestRequest()
                result = await sym.weekly_digest(req)
                d = result.model_dump()

                lines = [
                    "# 📊 Weekly Digest\n",
                    f"**Week ending**: {d['weekEnding']}\n",
                    f"- **Heartbeat**: {d['heartbeat'].get('beats', 0)} beats",
                    f"- **File Monitor**: {d['fileMon'].get('scans', 0)} scans, {d['fileMon'].get('changes', 0)} changes",
                    f"- **Git**: branch={d['git'].get('branch')}, dirty={d['git'].get('dirty')}, {d['git'].get('changes', 0)} changes",
                    f"- **WBC**: {d['wbc'].get('weekAlerts', 0)} alerts ({d['wbc'].get('criticals', 0)} critical, {d['wbc'].get('highs', 0)} high)",
                    f"- **Health**: avg={d['health'].get('avg', 0)}, {d['health'].get('samples', 0)} samples",
                    f"- **Sessions**: {d['sessions']}",
                ]
                return [TextContent(type="text", text="\n".join(lines))]

            elif action == "notifications":
                notif_action = arguments.get("notification_action", "list")
                if notif_action == "send":
                    notif_id = sym._send_notification(
                        source=arguments.get("source", "claude"),
                        level=arguments.get("notification_level", "INFO"),
                        title=arguments.get("title", ""),
                        body=arguments.get("body", ""),
                        data={},
                    )
                    return [TextContent(type="text", text=f"✅ Notification sent: id={notif_id}")]
                elif notif_action == "dismiss":
                    notif_id = arguments.get("id", "")
                    if not notif_id:
                        return [TextContent(type="text", text="Error: id is required for dismiss action")]
                    found = sym._dismiss_notification(notif_id)
                    if found:
                        return [TextContent(type="text", text=f"✅ Notification dismissed: id={notif_id}")]
                    else:
                        return [TextContent(type="text", text=f"❌ Notification not found: id={notif_id}")]
                elif notif_action == "purge":
                    result = sym._purge_notifications()
                    return [TextContent(type="text", text=f"🗑️ Purge complete: {result['purged']} removed, {result['remaining']} remaining")]
                else:
                    # list — 共通ヘルパーに委譲
                    limit = arguments.get("limit", 10)
                    level_filter = arguments.get("level")
                    include_dismissed = arguments.get("include_dismissed", False)
                    results = sym._list_notifications_raw(
                        limit=limit,
                        level=level_filter,
                        include_dismissed=include_dismissed,
                    )
                    if not results:
                        return [TextContent(type="text", text="📭 通知なし")]
                    lines = [f"# 🔔 通知一覧 ({len(results)} 件)\n"]
                    for r in results:
                        emoji = "🚨" if r.get("level") == "CRITICAL" else "⚠️" if r.get("level") == "HIGH" else "ℹ️"
                        lines.append(f"{emoji} **[{r.get('source')}]** {r.get('title')}")
                        lines.append(f"  {r.get('body', '')[:100]}")
                        lines.append(f"  _{r.get('timestamp', '')}_ | level={r.get('level')}")
                        lines.append("")
                    return [TextContent(type="text", text="\n".join(lines))]

            else:
                return [TextContent(type="text", text=f"Unknown sympatheia_ops action: {action}")]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:  # noqa: BLE001
        raise e  # Let the proxy handle and log the exception




# ============ Basanos/Peira handlers ============

# PURPOSE: [L2-auto] _handle_basanos_scan の非同期処理定義
async def _handle_basanos_scan(arguments: dict) -> list[TextContent]:
    """Basanos L0 scan via AIAuditor."""
    target = arguments.get("path", "")
    max_issues = arguments.get("max_issues", 20)
    if not target:
        return [TextContent(type="text", text="Error: path is required")]

    try:
        with StdoutSuppressor():
            from mekhane.basanos.ai_auditor import AIAuditor

        target_path = Path(target)
        if not target_path.exists():
            return [TextContent(type="text", text=f"Error: path not found: {target}")]

        auditor = AIAuditor(strict=False)

        def _scan():
            issues = []
            if target_path.is_file():
                result = auditor.audit_file(target_path)
                issues.extend(result.issues)
            else:
                for py_file in sorted(target_path.glob("**/*.py")):
                    if py_file.name.startswith("__"):
                        continue
                    try:
                        result = auditor.audit_file(py_file)
                        issues.extend(result.issues)
                    except Exception:  # noqa: BLE001
                        pass
            return issues

        all_issues = await run_sync(_scan)

        if not all_issues:
            return [TextContent(type="text", text=f"✅ Basanos: no issues in `{target_path.name}`")]

        lines = [f"# 🔍 Basanos Scan: {target_path.name}\n"]
        lines.append(f"**Issues**: {len(all_issues)} (showing max {max_issues})\n")
        for issue in all_issues[:max_issues]:
            lines.append(f"- **{issue.severity.value}** [{issue.code}] L{issue.line}: {issue.message}")

        return [TextContent(type="text", text="\n".join(lines))]
    except Exception as e:  # noqa: BLE001
        log(f"Basanos scan error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# PURPOSE: [L2-auto] _handle_peira_health の非同期処理定義
async def _handle_peira_health() -> list[TextContent]:
    """Peira health check."""
    try:
        with StdoutSuppressor():
            from mekhane.peira.hgk_health import run_health_check, format_terminal

        report = await run_sync(run_health_check)
        text = format_terminal(report)
        return [TextContent(type="text", text=text)]
    except Exception as e:  # noqa: BLE001
        log(f"Peira health error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ============ BC Violation Logger handlers ============

# PURPOSE: [L2-auto] _handle_log_violation の非同期処理定義
async def _handle_log_violation(arguments: dict) -> list[TextContent]:
    """BC違反/フィードバックを記録。"""
    try:
        from mekhane.sympatheia.violation_logger import (
            FeedbackEntry, log_entry, read_all_entries,
            format_session_summary, compute_stats,
        )
        from datetime import datetime

        entry = FeedbackEntry(
            timestamp=datetime.now().isoformat(),
            feedback_type=arguments.get("feedback_type", "self_detected"),
            bc_ids=arguments.get("bc_ids", []),
            pattern=arguments.get("pattern", ""),
            severity=arguments.get("severity", "medium"),
            description=arguments.get("description", ""),
            context=arguments.get("context", ""),
            creator_words=arguments.get("creator_words", ""),
            corrective=arguments.get("corrective", ""),
        )

        path = log_entry(entry)

        # セッション統計
        all_entries = read_all_entries()
        stats = compute_stats(all_entries)
        summary = format_session_summary(all_entries)

        TYPE_ICONS = {"reprimand": "⚡", "acknowledgment": "✨", "self_detected": "🔍"}
        icon = TYPE_ICONS.get(entry.feedback_type, "")

        lines = [
            f"# {icon} フィードバック記録完了\n",
            f"- **種別**: {entry.feedback_type}",
            f"- **BC**: {', '.join(entry.bc_ids) or 'N/A'}",
            f"- **パターン**: {entry.pattern or 'N/A'}",
            f"- **深刻度**: {entry.severity}",
            f"- **説明**: {entry.description}",
        ]
        if entry.creator_words:
            lines.append(f"- **Creator の言葉**: \"{entry.creator_words}\"")
        lines.append(f"\n{summary}")
        lines.append(f"\n📁 ログ: `{path}`")

        return [TextContent(type="text", text="\n".join(lines))]
    except Exception as e:  # noqa: BLE001
        log(f"Log violation error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# PURPOSE: [L2-auto] _handle_violation_dashboard の非同期処理定義
async def _handle_violation_dashboard(arguments: dict) -> list[TextContent]:
    """BC違反ダッシュボードを表示。"""
    try:
        from mekhane.sympatheia.violation_logger import (
            read_all_entries, format_dashboard,
        )

        period = arguments.get("period", "all")
        entries = read_all_entries()

        if not entries:
            return [TextContent(type="text", text="✅ フィードバック記録なし — まだログがありません")]

        dashboard = format_dashboard(entries, period=period)
        return [TextContent(type="text", text=dashboard)]
    except Exception as e:  # noqa: BLE001
        log(f"Violation dashboard error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# PURPOSE: [L2-auto] _handle_escalate の非同期処理定義
async def _handle_escalate(arguments: dict) -> list[TextContent]:
    """violations.md への昇格候補を表示。"""
    try:
        from mekhane.sympatheia.violation_logger import (
            read_all_entries, suggest_escalation,
        )

        min_severity = arguments.get("min_severity", "high")
        min_occurrences = arguments.get("min_occurrences", 2)
        entries = read_all_entries()

        if not entries:
            return [TextContent(type="text", text="✅ フィードバック記録なし")]

        candidates = suggest_escalation(
            entries, min_severity=min_severity, min_occurrences=min_occurrences,
        )

        if not candidates:
            return [TextContent(type="text", text="✅ 昇格候補なし — 条件に合致するパターンがありません")]

        lines = [f"# 📋 昇格候補: {len(candidates)} 件\n"]
        for c in candidates:
            lines.append(f"## {c['pattern']} ({c['reason']}, {c['count']}件)\n")
            lines.append(f"```yaml\n{c['template']}```\n")

        return [TextContent(type="text", text="\n".join(lines))]
    except Exception as e:  # noqa: BLE001
        log(f"Escalate error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ============ Verify-on-Edit handler ============

# PURPOSE: [L2] Verify-on-Edit ハンドラ — 変更ファイルの関連テストを発見・実行
async def _handle_verify_on_edit(arguments: dict) -> list[TextContent]:
    """Verify-on-Edit: 変更ファイルの関連テストを発見・実行する。"""
    changed_files = arguments.get("changed_files", [])
    if not changed_files:
        return [TextContent(type="text", text="Error: changed_files is required")]

    include_basanos = arguments.get("include_basanos", True)
    max_tests = arguments.get("max_tests", 100)

    try:
        with StdoutSuppressor():
            from mekhane.basanos.verify_on_edit import verify_on_edit

        def _run():
            return verify_on_edit(
                changed_files=changed_files,
                include_basanos=include_basanos,
                max_tests=max_tests,
            )

        result = await run_sync(_run)

        # 結果をフォーマット
        verdict = result.get("verdict", "UNKNOWN")
        verdict_icons = {
            "PASS": "✅", "FAIL": "❌", "SKIP": "⚠️",
            "NO_TESTS": "📭", "UNKNOWN": "❓",
        }
        icon = verdict_icons.get(verdict, "❓")

        lines = [f"# {icon} Verify-on-Edit: {verdict}\n"]

        # 変更ファイル
        lines.append(f"**Changed**: {len(changed_files)} files")
        for f in changed_files[:5]:
            lines.append(f"  - `{Path(f).name}`")

        # Basanos 結果
        basanos = result.get("basanos")
        if basanos and basanos.get("issues", 0) > 0:
            lines.append(f"\n**L0 Basanos**: {basanos['issues']} issues")
            for issue in basanos.get("details", [])[:5]:
                lines.append(
                    f"  - **{issue.get('severity', '?')}** [{issue.get('code', '?')}] "
                    f"L{issue.get('line', '?')}: {issue.get('message', '')}"
                )
        elif basanos:
            lines.append("\n**L0 Basanos**: ✅ clean")

        # テスト発見
        discovery = result.get("test_discovery")
        if discovery:
            lines.append(f"\n**Test Discovery**: {discovery['found']} tests found")
            for tf in discovery.get("test_files", [])[:5]:
                lines.append(f"  - `{Path(tf).name}`")

        # collect-only
        collection = result.get("collection")
        if collection:
            if collection.get("skipped_reason"):
                lines.append(f"\n**Collection**: ⚠️ {collection['skipped_reason']}")
            else:
                lines.append(f"\n**Collection**: {collection.get('count', 0)} test items")

        # 実行結果
        execution = result.get("execution")
        if execution:
            lines.append(
                f"\n**Execution**: {execution.get('total', 0)} tests — "
                f"{execution.get('total', 0) - execution.get('failed', 0) - execution.get('errors', 0)} passed, "
                f"{execution.get('failed', 0)} failed, "
                f"{execution.get('errors', 0)} errors"
            )
            if execution.get("output") and verdict == "FAIL":
                # 失敗時のみ出力を含める (末尾500文字)
                out = execution["output"][-500:]
                lines.append(f"\n```\n{out}\n```")

        # Lēthē Hint (軽量 — 重い検索は mneme に委譲)
        hint = result.get("lethe_hint")
        if hint and hint.get("count", 0) > 0:
            lines.append(f"\n**🔍 Lēthē**: {hint['count']} functions in changed files")
            lines.append(f"  💡 `mneme search scope=code code_mode=similar` で構造類似チェック推奨")
            for f in hint.get("functions", [])[:5]:
                lines.append(f"  - `{f['name']}` ({f['file']}:{f['line']})")

        return [TextContent(type="text", text="\n".join(lines))]

    except Exception as e:  # noqa: BLE001
        log(f"Verify-on-edit error: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


if __name__ == "__main__":
    _base.install_all_hooks()
    _base.run()

