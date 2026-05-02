# PROOF: [L2/インフラ] <- hermeneus/src/mcp_server.py Hermēneus MCP Server
"""
Hermēneus MCP Server — AI 自己統合

MCP (Model Context Protocol) を通じて Antigravity IDE から
Hermēneus を呼び出し可能にする。

Usage:
    python -m hermeneus.src.mcp_server

Origin: 2026-01-31 CCL Execution Guarantee Architecture
"""

import asyncio
import contextvars
import json
import sys
import time as _time_mod
from pathlib import Path
from typing import Any, Dict, List, Sequence

from mekhane.symploke.handoff_files import list_handoff_files

# =============================================================================
# Universal Progress Reporter (stderr JSON)
# =============================================================================
# PURPOSE: 長時間処理の進捗を stderr に push。全 MCP ツール共通インフラ。
# stderr は MCP プロトコル外なので通信を阻害しない。
# IDE のサーバーログに表示され、「動いているか」が一目でわかる。
# contextvars でリクエストスコープのタイマーを管理し、並行安全性を担保。

import logging as _logging
_progress_logger = _logging.getLogger("hermeneus.progress")
_progress_start_var: contextvars.ContextVar[float] = contextvars.ContextVar(
    "_progress_start", default=0.0
)


def _progress_reset() -> None:
    """progress タイマーをリセット。各 MCP ツールのエントリーポイントで呼ぶ。"""
    _progress_start_var.set(_time_mod.monotonic())


def _progress(phase: str, detail: str = "", step: int = 0, total: int = 0) -> None:
    """長時間処理の進捗を stderr に JSON push.

    Args:
        phase: 現在のフェーズ名 (例: "context_enrich", "llm_call")
        detail: 詳細情報 (例: "/{wf_id} → Gemini API...")
        step: 現在のステップ番号 (0 = 不使用)
        total: 全ステップ数 (0 = 不使用)
    """
    start = _progress_start_var.get()
    if start == 0.0:
        start = _time_mod.monotonic()
        _progress_start_var.set(start)
    elapsed = round(_time_mod.monotonic() - start, 1)
    msg: dict[str, str | int | float] = {
        "event": "progress",
        "phase": phase,
        "detail": detail,
        "elapsed": elapsed,
    }
    if step > 0:
        msg["step"] = step
    if total > 0:
        msg["total"] = total
    print(json.dumps(msg, ensure_ascii=False), file=sys.stderr, flush=True)

# EOF prevention: run blocking calls in thread pool
async def run_sync(fn, *args, timeout_sec: float = 120.0, **kwargs):
    """Run sync function in thread pool. See mekhane.mcp.mcp_base.run_sync."""
    label = getattr(fn, '__qualname__', None) or getattr(fn, '__name__', repr(fn))
    coro = asyncio.to_thread(fn, *args, **kwargs)
    if timeout_sec > 0:
        try:
            return await asyncio.wait_for(coro, timeout=timeout_sec)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Sync call '{label}' timed out after {timeout_sec}s")
    return await coro


def _json_text_response(payload: Dict[str, Any]) -> Sequence["TextContent"]:
    """Render a JSON payload as an MCP text response."""
    blocked_json = json.dumps(payload, ensure_ascii=False, indent=2)
    return [TextContent(type="text", text=f"```json\n{blocked_json}\n```")]


def _prepare_zero_trust_explicit(
    ccl: str,
    invocation_mode: str,
):
    """Build Zero-Trust preflight for explicit invocation only."""
    if invocation_mode != "explicit":
        return None, None, None

    from mekhane.ccl.executor import (
        ZeroTrustCCLExecutor,
        build_zero_trust_blocked_payload,
    )

    executor = ZeroTrustCCLExecutor()
    context, validation = executor.preflight(ccl)
    if validation is None:
        return executor, context, None
    return (
        executor,
        context,
        build_zero_trust_blocked_payload(ccl, context, validation),
    )


def _zero_trust_validation_payload(validation: Any, context: Any) -> Dict[str, Any]:
    """Serialize Zero-Trust validation with contract trace."""
    payload = validation.to_dict() if validation is not None else {}
    if context is not None:
        payload["contract_trace"] = context.contract_trace
    return payload


def _append_zero_trust_trace(text: str, validation: Any, context: Any) -> str:
    """Append Zero-Trust validation trace for multi-workflow executions."""
    if context is None or getattr(context, "workflow_count", 0) < 2:
        return text
    trace_payload = _zero_trust_validation_payload(validation, context)
    trace_json = json.dumps(trace_payload, ensure_ascii=False, indent=2)
    return text + f"\n---\n### Zero-Trust Trace\n```json\n{trace_json}\n```"

# MCP SDK import (optional)
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        CallToolResult,
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Server = None
    Tool = Any
    TextContent = Any
    CallToolResult = Any


# =============================================================================
# P4: θ12.1 Pending Dispatch Tracker (WBC Integration)
# =============================================================================

import time as _time_module

# PURPOSE: dispatch のみ呼ばれて execute/run が来なかったパターンを検出する
_pending_dispatches: dict[str, float] = {}  # {ccl: timestamp}
_PENDING_TIMEOUT_SEC = 300  # 5分以内に execute/run が来なければ疑わしい


def _normalize_pending_key(ccl: str) -> str:
    """record/clear で使う CCL キーを正規化する。
    
    strip + 先頭の `/` を `@` に変換し、
    dispatch と execute/run でキーが一致することを保証する。
    """
    key = ccl.strip()
    if key.startswith("/"):
        key = "@" + key[1:]
    return key


def _record_pending_dispatch(ccl: str) -> None:
    """dispatch 呼び出しを記録する。"""
    _pending_dispatches[_normalize_pending_key(ccl)] = _time_module.time()


def _clear_pending_dispatch(ccl: str) -> None:
    """execute/run 呼び出し時にペンディングを消す。"""
    _pending_dispatches.pop(_normalize_pending_key(ccl), None)


def _log_wbc_theta12_1_alert(ccl: str, elapsed_sec: float) -> None:
    """θ12.1 違反疑いを wbc_state.json に書き込み、notifications.jsonl にも通知する。"""
    import json
    from datetime import datetime, timezone
    mneme_dir = Path(__file__).parent.parent.parent/ "30_記憶｜Mneme"
    wbc_file = mneme_dir / "wbc_state.json"
    notif_file = mneme_dir / "notifications.jsonl"
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        mneme_dir.mkdir(parents=True, exist_ok=True)
        if wbc_file.exists():
            state = json.loads(wbc_file.read_text("utf-8"))
        else:
            state = {"alerts": [], "totalAlerts": 0}
        alert = {
            "timestamp": now_iso,
            "source": "hermeneus_theta12_1_watchdog",
            "severity": "high",
            "eventType": "theta12_1_dispatch_without_execute",
            "details": f"dispatch('{ccl}') was called {elapsed_sec:.0f}s ago without execute/run. Possible θ12.1 violation.",
            "threatScore": 8,
        }
        state["alerts"].append(alert)
        state["totalAlerts"] = state.get("totalAlerts", 0) + 1
        state["alerts"] = state["alerts"][-100:]
        wbc_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        
        # A5.2/§3.2: Sympatheia 通知にも CRITICAL を送信
        # SOURCE: パプくん A5.2 — ToolCritic のフィードバックパイプライン
        notification = {
            "id": f"theta12_1-{int(_time_module.time())}",
            "timestamp": now_iso,
            "level": "CRITICAL",
            "source": "hermeneus_theta12_1_watchdog",
            "title": f"θ12.1 違反疑い: dispatch('{ccl}') → execute/run 未呼出",
            "body": f"dispatch('{ccl}') が {elapsed_sec:.0f}秒前に呼ばれたが、execute/run が呼ばれていない。手書き偽装の可能性。",
            "dismissed": False,
        }
        with open(notif_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(notification, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass  # WBC/notification logging should never crash the main flow


# PURPOSE: 残存ペンディングをチェックし、古いものを WBC アラート化する
def check_pending_dispatches() -> list[dict]:
    """残存ペンディングをチェックし、古いものを WBC アラート化する。

    /boot や peira_health から呼ばれることを想定。
    Returns: list of {ccl, elapsed_sec} for detected violations.
    """
    now = _time_module.time()
    violations = []
    expired_keys = []
    for ccl, ts in _pending_dispatches.items():
        elapsed = now - ts
        if elapsed > _PENDING_TIMEOUT_SEC:
            _log_wbc_theta12_1_alert(ccl, elapsed)
            violations.append({"ccl": ccl, "elapsed_sec": round(elapsed, 1)})
            expired_keys.append(ccl)
    for k in expired_keys:
        _pending_dispatches.pop(k, None)
    return violations


# =============================================================================
# MCP Server Implementation
# =============================================================================

if MCP_AVAILABLE:
    server = Server("hermeneus")
    
    # PURPOSE: 利用可能なツール一覧を返す
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """利用可能なツール一覧を返す (統合ファサード: 8→3)"""
        return [
            # ━━━ 1. hermeneus_run: θ12.1 主力 — 独立維持 ━━━
            Tool(
                name="hermeneus_run",
                description=(
                    "Parse AND Execute Cognitive Control Language (CCL) expressions. "
                    "This is the PRIMARY tool for CCL execution. It atomically combines dispatch+execute, "
                    "returning both the parsing AST with the final execution result. "
                    "USE THIS TOOL for normal CCL execution to comply with θ12.1. "
                    "Returns: execution result with status and output. "
                    "Example: hermeneus_run(ccl='...') "
                    "Errors if required params (ccl) are missing or invalid."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ccl": {
                            "type": "string",
                            "description": "CCL 式 (例: /noe+, /bou+ >> /ene+)"
                        },
                        "context": {
                            "type": "string",
                            "description": "実行コンテキスト — /rom+ 的な全量を渡すこと。"
                                           "先行分析の原文・仮説・根拠・Creator の発言・違反歴など、"
                                           "自分が持つ関連コンテキストを最低限の下処理のみで全量含める。"
                                           "要約や圧縮は禁止。短すぎるコンテキストは品質低下の主因。",
                            "default": ""
                        },
                        "verify": {
                            "type": "boolean",
                            "description": "Multi-Agent Debate で検証するか",
                            "default": True
                        },
                        "audit": {
                            "type": "boolean",
                            "description": "監査記録を残すか",
                            "default": True
                        },
                        "model": {
                            "type": "string",
                            "description": "使用するモデル (auto, gemini-3.1-pro-preview, claude-opus-4-20250514, vertex/claude-sonnet-4.5 等)",
                            "default": "auto"
                        },
                        "use_llm": {
                            "type": "boolean",
                            "description": "LLMStepHandler を使用して実際の LLM を呼び出すか。False の場合は CognitiveStepHandler によるシミュレーション実行となる。",
                            "default": True
                        },
                        "account": {
                            "type": "string",
                            "description": "Token Vault のアカウント名 (default, movement, Tolmeton 等)",
                            "default": "default"
                        },
                        "cascade_id": {
                            "type": "string",
                            "description": "LS の cascade_id。指定時はそのセッションのトーク履歴を context に自動追加する。"
                                           "並列セッション環境では明示指定が必要。",
                            "default": ""
                        },
                        "invocation_mode": {
                            "type": "string",
                            "description": "contract enforcement mode: explicit|implicit|internal",
                            "default": "explicit"
                        }
                    },
                    "required": ["ccl"]
                }
            ),
            # ━━━ 2. hermeneus_analyze: dispatch + execute + compile を統合 ━━━
            Tool(
                name="hermeneus_analyze",
                description=(
                    "CCL の解析・実行・コンパイルを統一的に行うファサード。"
                    "action パラメータで操作を選択: "
                    "dispatch=CCL パース(AST), execute=CCL 実行(LLM), compile=LMQL コンパイル。"
                    "Returns: action に応じた結果。"
                    "Errors if required params (ccl) are missing or invalid."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["dispatch", "execute", "compile"],
                            "description": "操作種別: dispatch(パース), execute(実行), compile(コンパイル)",
                            "default": "dispatch"
                        },
                        "ccl": {
                            "type": "string",
                            "description": "CCL 式 (例: /noe+, /bou+ >> /ene+)"
                        },
                        "context": {
                            "type": "string",
                            "description": "実行コンテキスト (execute 時に使用)",
                            "default": ""
                        },
                        "verify": {
                            "type": "boolean",
                            "description": "Multi-Agent Debate で検証するか (execute 時)",
                            "default": True
                        },
                        "audit": {
                            "type": "boolean",
                            "description": "監査記録を残すか (execute 時)",
                            "default": True
                        },
                        "model": {
                            "type": "string",
                            "description": "使用するモデル (execute/compile 時)",
                            "default": "auto"
                        },
                        "use_llm": {
                            "type": "boolean",
                            "description": "LLM を呼び出すか (execute 時)",
                            "default": True
                        },
                        "account": {
                            "type": "string",
                            "description": "Token Vault アカウント (execute 時)",
                            "default": "default"
                        },
                        "cascade_id": {
                            "type": "string",
                            "description": "LS の cascade_id (execute 時)",
                            "default": ""
                        },
                        "invocation_mode": {
                            "type": "string",
                            "description": "contract enforcement mode: explicit|implicit|internal",
                            "default": "explicit"
                        }
                    },
                    "required": ["ccl"]
                }
            ),
            # ━━━ 3. hermeneus_admin: workflows + audit + export + ping ━━━
            Tool(
                name="hermeneus_admin",
                description=(
                    "Hermēneus の管理操作ファサード。"
                    "action パラメータで操作を選択: "
                    "workflows=WF一覧, audit=監査レポート, export=セッション履歴エクスポート, ping=ヘルスチェック。"
                    "Returns: action に応じた結果。"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["workflows", "audit", "export", "ping"],
                            "description": "操作種別: workflows(WF一覧), audit(監査), export(セッション履歴), ping(ヘルスチェック)"
                        },
                        "period": {
                            "type": "string",
                            "description": "監査期間 (audit 時: today, last_24h, last_7_days, last_30_days, all)",
                            "default": "last_7_days"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "監査最大件数 (audit 時)",
                            "default": 10
                        },
                        "session_name": {
                            "type": "string",
                            "description": "セッション名 (export 時、省略可)",
                            "default": ""
                        }
                    },
                    "required": ["action"]
                }
            ),
        ]
    
    # PURPOSE: ツールを実行
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """ツールを実行 (統合ファサード: 8→3)"""
        # ━━━ エイリアスレイヤー: 旧ツール名 → 新ファサード ━━━
        _ALIASES = {
            "hermeneus_execute":        ("hermeneus_analyze", {"action": "execute"}),
            "hermeneus_compile":        ("hermeneus_analyze", {"action": "compile"}),
            "hermeneus_dispatch":       ("hermeneus_analyze", {"action": "dispatch"}),
            "hermeneus_audit":          ("hermeneus_admin",   {"action": "audit"}),
            "hermeneus_list_workflows": ("hermeneus_admin",   {"action": "workflows"}),
            "hermeneus_export_session": ("hermeneus_admin",   {"action": "export"}),
            "hermeneus_ping":           ("hermeneus_admin",   {"action": "ping"}),
        }
        if name in _ALIASES:
            new_name, defaults = _ALIASES[name]
            arguments = {**defaults, **arguments}
            name = new_name

        try:
            if name == "hermeneus_run":
                result = await _handle_run(arguments)
            elif name == "hermeneus_analyze":
                action = arguments.get("action", "dispatch")
                if action == "dispatch":
                    result = await _handle_dispatch(arguments)
                elif action == "execute":
                    result = await _handle_execute(arguments)
                elif action == "compile":
                    result = await _handle_compile(arguments)
                else:
                    result = [TextContent(type="text", text=f"Unknown analyze action: {action}")]
            elif name == "hermeneus_admin":
                action = arguments.get("action")
                if action == "ping":
                    return [TextContent(type="text", text="pong")]
                elif action == "audit":
                    result = await _handle_audit(arguments)
                elif action == "workflows":
                    result = await _handle_list_workflows(arguments)
                elif action == "export":
                    result = await _handle_export_session(arguments)
                else:
                    result = [TextContent(type="text", text=f"Unknown admin action: {action}")]
            else:
                result = [TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]
        except Exception as e:  # noqa: BLE001
            result = [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]

        # V-011 品質ゲート (環境強制)
        import os
        if os.getenv("HGK_QUALITY_GATE_ENABLED", "1") == "1":
            try:
                from mekhane.mcp.quality_gate import (
                    execute_quality_gate, format_gate_result, update_gate_status
                )
                response_text = "\n".join(
                    c.text for c in result if hasattr(c, "text")
                )
                gate_result = await run_sync(
                    execute_quality_gate,
                    name, arguments, response_text, None,
                )
                if gate_result:
                    await run_sync(update_gate_status, gate_result)
                    formatted = format_gate_result(gate_result)
                    if formatted:
                        result = list(result) + [
                            TextContent(type="text", text=formatted)
                        ]
            except Exception as qg_err:  # noqa: BLE001
                print(
                    f"[hermeneus] QualityGate error (non-fatal): {qg_err}",
                    file=sys.stderr, flush=True,
                )

        return result


# PURPOSE: hermeneus_execute の処理
async def _handle_execute(args: Dict[str, Any]) -> Sequence[TextContent]:
    """hermeneus_execute の処理"""
    ccl = args["ccl"]
    # P4: execute 呼び出し時にペンディングをクリア
    _clear_pending_dispatch(ccl)
    # D2: 入力層で正規化 — 下流は @xxx しか見ない (v3.2)
    from hermeneus.src.ccl_normalizer import normalize_ccl_input
    ccl = normalize_ccl_input(ccl)
    context = args.get("context", "")
    invocation_mode = args.get("invocation_mode", "explicit")
    contract = None
    contract_compile_error: Exception | None = None
    try:
        from hermeneus.src.ccl_contracts import compile_ccl_contract
        contract = compile_ccl_contract(ccl, invocation_mode=invocation_mode)
    except Exception as exc:  # noqa: BLE001
        contract_compile_error = exc
        contract = None
    if contract is None and invocation_mode == "explicit":
        blocked_payload = {
            "status": "blocked",
            "error_type": "ccl_contract_blocked",
            "requested_ccl": ccl,
            "normalized_ccl": ccl,
            "unmet_requirements": ["contract_compile"],
            "blocking_reason": f"CCL contract compile failed: {contract_compile_error}",
            "safe_next_step": "CCL contract compile が通るまで実行を停止",
        }
        return _json_text_response(blocked_payload)
    zero_trust_executor, zero_trust_context, zero_trust_block = (
        _prepare_zero_trust_explicit(ccl, invocation_mode)
    )
    if zero_trust_block is not None:
        return _json_text_response(zero_trust_block)
    verify = args.get("verify", True)
    audit = args.get("audit", True)
    model = args.get("model", "auto")
    use_llm = args.get("use_llm", True)
    account = args.get("account", "default")

    # ProgressEvent for phase tracking
    import time as _time
    _start = _time.monotonic()
    thinking_events: list[str] = []

    def _emit(phase: str, **detail):
        try:
            from mekhane.periskope.models import ProgressEvent
            event = ProgressEvent(
                phase=phase, detail=detail,
                elapsed=round(_time.monotonic() - _start, 1),
            )
            thinking_events.append(event.summary())
        except Exception:  # noqa: BLE001
            pass

    _emit("ccl_parse", ccl=ccl, model=model, use_llm=use_llm)
    
    # /ax 特殊ルーティング: AxPipeline に委譲
    ccl_stripped = ccl.strip().lstrip("/")
    if ccl_stripped in ("ax", "ax+", "ax-"):
        return await _handle_ax_pipeline(args)
    
    if use_llm:
        # Phase 1: LLMStepHandler を用いた MacroExecutor 実行
        from .macro_executor import MacroExecutor, LLMStepHandler
        import functools
        
        handler = LLMStepHandler(model=model, account=account)

        # v9.0: EventBus 構築 + サブスクライバ登録
        from .event_bus import CognitionEventBus
        event_bus = CognitionEventBus(enabled=True)
        try:
            from .subscribers import create_all_subscribers
            for sub in create_all_subscribers():
                event_bus.subscribe_all(sub)
        except Exception as _e:  # noqa: BLE001
            logger.debug("Subscriber registration failed: %s", _e)

        executor = MacroExecutor(step_handler=handler.handle, environment=event_bus)
        
        _emit("llm_execute_start", model=model, account=account)

        # MacroExecutor executes synchronously (CortexClient is synchronous)
        # ccl that does not start with @ or / is treated as a macro if it's alphanumeric, but MacroExecutor handles parsing
        loop = asyncio.get_running_loop()
        exec_func = functools.partial(executor.execute, ccl, context=context)
        
        # run_in_executor to avoid blocking the MCP server's event loop
        result = await loop.run_in_executor(None, exec_func)
        
        _emit("llm_execute_done", success=result.success)
        
        status = "✅ 成功" if result.success else "❌ 失敗"
        
        # 出力テキストが大きすぎないように制限
        output_snippet = result.final_output.strip()
        if len(output_snippet) > 4000:
            output_snippet = output_snippet[:4000] + "\n\n... (以下省略) ..."
        if not output_snippet:
            output_snippet = "(出力なし)"

        text = f"""## Hermēneus マクロ実行結果

**CCL**: `{ccl}`
**ステータス**: {status}
**モデル**: `{model}`
**アカウント**: `{account}`

---

{result.summary()}

---
### 最終出力
{output_snippet}
"""
        # Append structured output
        if hasattr(result, "structured_output") and result.structured_output:
            import json as _json
            try:
                struct_json = _json.dumps(result.structured_output, ensure_ascii=False, indent=2)
                text += f"\n---\n### 構造化メタデータ (Structured Output)\n```json\n{struct_json}\n```\n"
                
                # 下流消費者接続: structured_output を jsonl ログに永続化
                from pathlib import Path
                log_dir = Path.home() / ".hermeneus" / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                log_file = log_dir / "structured_outputs.jsonl"
                with open(log_file, "a", encoding="utf-8") as f:
                    log_entry = {
                        "timestamp": datetime.now().isoformat() if 'datetime' in globals() else __import__('datetime').datetime.now().isoformat(),
                        "ccl": ccl,
                        "model": model,
                        "account": account,
                        "structured_output": result.structured_output
                    }
                    f.write(_json.dumps(log_entry, ensure_ascii=False) + "\n")
            except Exception as e:  # noqa: BLE001
                logger.debug("Failed to record structured output: %s", e)

        # Append thinking trace
        if thinking_events:
            text += "\n---\n## 🧠 思考過程\n"
            for ev in thinking_events:
                text += f"- {ev}\n"

        # Krisis 随伴統合: メトリクス付加
        text = _append_krisis_adjunction(text, ccl, output_snippet, context)

        zero_trust_validation = None
        if zero_trust_executor is not None and zero_trust_context is not None:
            zero_trust_validation = zero_trust_executor.validate(
                result.final_output,
                zero_trust_context,
            )

        if contract is not None:
            try:
                from hermeneus.src.ccl_contracts import validate_ccl_contract
                validation_payload = (
                    result.to_dict()
                    if hasattr(result, "to_dict")
                    else {
                        "final_output": result.final_output,
                        "summary": result.summary(),
                        "structured_output": getattr(result, "structured_output", {}),
                    }
                )
                validation = validate_ccl_contract(contract, validation_payload)
                if not validation.is_compliant and invocation_mode == "explicit":
                    blocked_payload = validation.blocked_payload()
                    if zero_trust_validation is not None and zero_trust_context is not None:
                        blocked_payload["zero_trust"] = _zero_trust_validation_payload(
                            zero_trust_validation,
                            zero_trust_context,
                        )
                    return _json_text_response(blocked_payload)
            except Exception:  # noqa: BLE001
                pass

        if (
            zero_trust_validation is not None
            and not zero_trust_validation.valid
            and invocation_mode == "explicit"
        ):
            from mekhane.ccl.executor import build_zero_trust_blocked_payload

            return _json_text_response(
                build_zero_trust_blocked_payload(
                    ccl,
                    zero_trust_context,
                    zero_trust_validation,
                )
            )

        text = _append_zero_trust_trace(
            text,
            zero_trust_validation,
            zero_trust_context,
        )

        return [TextContent(type="text", text=text)]
    # use_llm=False: MacroExecutor + CognitiveStepHandler (テンプレート応答)
    # NOTE: 旧実装は WorkflowExecutor (LMQL パイプライン) に委譲していたが、
    #       LMQL subprocess 起動で [Errno 2] が発生するため、
    #       MacroExecutor + CognitiveStepHandler に統一した。
    from .macro_executor import MacroExecutor, CognitiveStepHandler
    import functools

    handler = CognitiveStepHandler.handle

    # v9.0: EventBus 構築 + サブスクライバ登録
    from .event_bus import CognitionEventBus
    event_bus = CognitionEventBus(enabled=True)
    try:
        from .subscribers import create_all_subscribers
        for sub in create_all_subscribers():
            event_bus.subscribe_all(sub)
    except Exception as _e:  # noqa: BLE001
        logger.debug("Subscriber registration failed: %s", _e)

    executor = MacroExecutor(step_handler=handler, environment=event_bus)

    _emit("wf_execute_start", ccl=ccl, verify=verify)

    loop = asyncio.get_running_loop()
    exec_func = functools.partial(executor.execute, ccl, context=context)
    result = await loop.run_in_executor(None, exec_func)

    _emit("wf_execute_done", success=result.success, confidence="N/A (CognitiveStepHandler)")

    status = "✅ 成功" if result.success else "❌ 失敗"

    output_snippet = result.final_output.strip()
    if len(output_snippet) > 4000:
        output_snippet = output_snippet[:4000] + "\n\n... (以下省略) ..."
    if not output_snippet:
        output_snippet = "(出力なし)"

    text = f"""## Hermēneus シミュレーション実行結果

**CCL**: `{ccl}`
**ステータス**: {status}
**モデル**: `CognitiveStepHandler (テンプレート)`

---

{result.summary()}

---
### 最終出力
{output_snippet}
"""
    # Append structured output
    if hasattr(result, "structured_output") and result.structured_output:
        import json as _json
        try:
            struct_json = _json.dumps(result.structured_output, ensure_ascii=False, indent=2)
            text += f"\n---\n### 構造化メタデータ (Structured Output)\n```json\n{struct_json}\n```\n"
        except Exception:  # noqa: BLE001
            pass

    # Append thinking trace
    if thinking_events:
        text += "\n---\n## 🧠 思考過程\n"
        for ev in thinking_events:
            text += f"- {ev}\n"

    # Krisis 随伴統合: メトリクス付加
    text = _append_krisis_adjunction(text, ccl, output_snippet, context)

    zero_trust_validation = None
    if zero_trust_executor is not None and zero_trust_context is not None:
        zero_trust_validation = zero_trust_executor.validate(
            result.final_output,
            zero_trust_context,
        )

    if contract is not None:
        try:
            from hermeneus.src.ccl_contracts import validate_ccl_contract
            validation_payload = (
                result.to_dict()
                if hasattr(result, "to_dict")
                else {
                    "final_output": result.final_output,
                    "summary": result.summary(),
                    "structured_output": getattr(result, "structured_output", {}),
                }
            )
            validation = validate_ccl_contract(contract, validation_payload)
            if not validation.is_compliant and invocation_mode == "explicit":
                blocked_payload = validation.blocked_payload()
                if zero_trust_validation is not None and zero_trust_context is not None:
                    blocked_payload["zero_trust"] = _zero_trust_validation_payload(
                        zero_trust_validation,
                        zero_trust_context,
                    )
                return _json_text_response(blocked_payload)
        except Exception:  # noqa: BLE001
            pass

    if (
        zero_trust_validation is not None
        and not zero_trust_validation.valid
        and invocation_mode == "explicit"
    ):
        from mekhane.ccl.executor import build_zero_trust_blocked_payload

        return _json_text_response(
            build_zero_trust_blocked_payload(
                ccl,
                zero_trust_context,
                zero_trust_validation,
            )
        )

    text = _append_zero_trust_trace(
        text,
        zero_trust_validation,
        zero_trust_context,
    )

    return [TextContent(type="text", text=text)]

# PURPOSE: Krisis 随伴統合ヘルパー — WF 実行結果に随伴メトリクスを付加
def _append_krisis_adjunction(text: str, ccl: str, wf_output: str, context: str = "") -> str:
    """Append Krisis adjunction metrics to execute result text.

    Extracts WF id from CCL, checks if it's a Krisis WF,
    and if so, appends drift detection + adjunction metrics + dual proposal.
    """
    try:
        from mekhane.fep.krisis_adjunction_builder import (
            compute_adjunction_from_execution,
            detect_drift,
            propose_dual_wf,
        )
    except ImportError:
        return text

    # Extract WF id from CCL (e.g. "/kat+" → "kat", "@kat" → "kat")
    wf_id = ccl.strip().lstrip("/@").rstrip("+-~*")
    if not wf_id:
        return text

    sections = []

    # 1. Pre-execution drift detection
    drift = detect_drift(wf_id, context)
    if drift:
        sections.append(f"\n---\n## ⚠️ Drift Detection\n{drift['warning']}\n> {drift.get('fep', '')}")

    # 2. Post-execution adjunction metrics
    adj_result = compute_adjunction_from_execution(wf_id, wf_output)
    if adj_result:
        sections.append(f"\n---\n{adj_result['section']}")
        # 永続化: メトリクスを JSONL に保存
        try:
            from mekhane.fep.krisis_metrics_store import save_metrics
            adj = adj_result.get("adjunction")
            if adj:
                save_metrics(
                    wf_id=wf_id,
                    pair_name=adj_result.get("pair_name", ""),
                    eta=adj.eta_quality,
                    epsilon=adj.epsilon_precision,
                    drift_type=drift.get("drift_type") if drift else None,
                    context_summary=context[:100] if context else "",
                )
        except Exception:  # noqa: BLE001
            pass  # 永続化失敗は実行を止めない

    # 3. Morphism proposal (dual + I→A transition)
    proposal = propose_dual_wf(wf_id)
    if proposal:
        sections.append(f"\n---\n{proposal}")

    if sections:
        text += "\n".join(sections)

    return text


# PURPOSE: /ax パイプライン専用ハンドラ
async def _handle_ax_pipeline(args: Dict[str, Any]) -> Sequence[TextContent]:
    """/ax パイプライン専用ハンドラ
    
    AxPipeline を起動し、4フェーズの完全実行を行う:
    Phase 1: 6 Peras (T/M/K/D/O/C) を L3 で順次実行
    Phase 2: 6 Limits の統合・対比分析  
    Phase 3: X-series 15エッジの張力分析
    Phase 4: 最終統合レポート生成
    """
    from .ax_pipeline import AxPipeline
    
    context = args.get("context", "")
    model = args.get("model", "auto")
    verify = args.get("verify", True)
    audit = args.get("audit", True)
    
    pipeline = AxPipeline(model=model, verify=verify, audit=audit)
    result = await pipeline.run(context=context, model=model)
    
    # Format output
    status = "✅ 成功" if result.success else "❌ 失敗"
    
    text = f"""## 📐 /ax — Peras の Peras 実行結果

**ステータス**: {status}
**モデル**: `{model}`
**実行時間**: {result.total_duration_ms:.0f}ms

### Phase 1: 6 Series 個別評価
"""
    
    for pr in result.peras_results:
        s = "✅" if pr.success else "❌"
        text += f"- {s} **{pr.series_name}** (`/{pr.series_id}+`): conf={pr.confidence:.0%}, {pr.duration_ms:.0f}ms\n"
    
    if result.synthesis:
        text += f"\n### Phase 2: 統合分析\n{result.synthesis[:1000]}\n"
    
    if result.edge_tensions:
        text += "\n### Phase 3: X-series 張力 (Top 5)\n"
        sorted_t = sorted(result.edge_tensions, key=lambda e: e.tension_score, reverse=True)[:5]
        for et in sorted_t:
            type_match = "✓" if et.tension_type == et.expected_type else "≠"
            text += f"- ⚡ **{et.edge[0]}—{et.edge[1]}** [{et.tension_type}{type_match}]: {et.tension_level} ({et.tension_score:.2f}) — {et.description}\n"
    
    if result.report:
        text += f"\n### Phase 4: 最終レポート\n\n{result.report}\n"
    
    return [TextContent(type="text", text=text)]


# PURPOSE: hermeneus_compile の処理
async def _handle_compile(args: Dict[str, Any]) -> Sequence[TextContent]:
    """hermeneus_compile の処理"""
    from . import compile_ccl
    from .dispatch import dispatch
    
    ccl = args["ccl"]
    model = args.get("model", "openai/gpt-4o")
    
    lmql_code = await run_sync(compile_ccl, ccl, model=model)
    
    # v4.1 修飾子の解決プレビューを追加
    dispatch_res = await run_sync(dispatch, ccl)
    modifier_info = ""
    if "【修飾子 (Dokimasia パラメータ)】" in dispatch_res.get("plan_template", ""):
        lines = dispatch_res["plan_template"].split("\n")
        in_mod = False
        mod_lines = []
        for line in lines:
            if line.startswith("【修飾子 (Dokimasia パラメータ)】"):
                in_mod = True
                mod_lines.append(line)
            elif in_mod and line.startswith("【"):
                break
            elif in_mod:
                mod_lines.append(line)
        modifier_info = "\n" + "\n".join(mod_lines).strip() + "\n"
    
    text = f"""## Hermēneus コンパイル結果

**CCL**: `{ccl}`
**モデル**: `{model}`
{modifier_info}
```lmql
{lmql_code}
```
"""
    return [TextContent(type="text", text=text)]


# PURPOSE: hermeneus_audit の処理
async def _handle_audit(args: Dict[str, Any]) -> Sequence[TextContent]:
    """hermeneus_audit の処理"""
    from .audit import get_audit_report
    
    period = args.get("period", "last_7_days")
    limit = args.get("limit", 10)
    
    report = await run_sync(get_audit_report, period=period)
    
    # Structured Insights: 品質トレンドを付加
    insights_text = ""
    try:
        from .structured_insights import get_insights
        period_days = {"today": 1, "last_24h": 1, "last_7_days": 7, "last_30_days": 30, "all": 365}
        days = period_days.get(period, 7)
        insights_text = "\n\n---\n\n" + get_insights(days=days)
    except Exception:  # noqa: BLE001
        pass  # Insights の失敗は audit レポートを止めない
    
    return [TextContent(type="text", text=f"## 監査レポート\n\n{report}{insights_text}")]


# PURPOSE: hermeneus_list_workflows の処理
async def _handle_list_workflows(args: Dict[str, Any]) -> Sequence[TextContent]:
    """hermeneus_list_workflows の処理"""
    from .registry import list_workflows, get_workflow
    
    names = await run_sync(list_workflows)
    
    lines = ["## 利用可能なワークフロー\n"]
    
    for name in names[:20]:  # 最大20件
        wf = await run_sync(get_workflow, name)
        if wf:
            lines.append(f"- **/{name}**: {wf.description}")
        else:
            lines.append(f"- **/{name}**")
    
    if len(names) > 20:
        lines.append(f"\n... 他 {len(names) - 20} 件")
    
    return [TextContent(type="text", text="\n".join(lines))]


# PURPOSE: hermeneus_export_session の処理 — セッション記録・Handoff 補助
async def _handle_export_session(args: Dict[str, Any]) -> Sequence[TextContent]:
    """hermeneus_export_session の処理 — セッション記録・Handoff 補助"""
    from datetime import datetime
    
    session_name = args.get("session_name", "")
    if not session_name:
        session_name = f"Session_{datetime.now().strftime('%Y%m%d_%H%M')}"
    
    hegemonikon_dir = Path(__file__).parent.parent.parent
    handoff_dir = hegemonikon_dir/ "30_記憶｜Mneme" / "01_記録｜Records" / "a_引継｜handoff"
    
    def _get_handoff_summary():
        handoffs = list_handoff_files(handoff_dir)
        if not handoffs:
            return None, 0, ""
        latest = handoffs[0]
        try:
            content = latest.read_text(encoding="utf-8")
            summary_lines = content.split("\n")[:30]
            return latest.name, len(handoffs), "\n".join(summary_lines)
        except Exception:  # noqa: BLE001
            return latest.name, len(handoffs), "(読み取りエラー)"

    latest_name, hf_count, summary = await run_sync(_get_handoff_summary)
    
    if latest_name:
        text = f"""## ✅ セッション記録確認

**セッション名**: `{session_name}`
**最新 Handoff**: `{latest_name}`
**Handoff 数**: {hf_count} 件

### 最新 Handoff サマリー
```
{summary}
```

> 💡 チャットエクスポートは IDE ネイティブ機能を使用してください。
"""
    else:
        text = f"""## ⚠️ Handoff 未検出

**セッション名**: `{session_name}`
**Handoff ディレクトリ**: `{handoff_dir}`

Handoff ファイルが見つかりません。`/bye` でセッションを終了すると自動生成されます。
"""
    
    return [TextContent(type="text", text=text)]


# PURPOSE: hermeneus_dispatch の処理 — CCL パース + AST 表示 + 実行計画テンプレート
async def _handle_dispatch(args: Dict[str, Any]) -> Sequence[TextContent]:
    """hermeneus_dispatch の処理 — CCL パース + AST 表示 + 実行計画テンプレート"""
    from .dispatch import dispatch
    
    ccl = args["ccl"]
    invocation_mode = args.get("invocation_mode", "explicit")
    # P4: dispatch 呼び出しをペンディング記録 (execute/run が来るべき)
    _record_pending_dispatch(ccl)
    result = await run_sync(dispatch, ccl, invocation_mode=invocation_mode)
    
    if not result["success"]:
        text = f"""## ❌ CCL パースエラー

**CCL**: `{ccl}`
**エラー**: {result['error']}

パーサー拡張が必要か、式の修正が必要です。"""
    else:
        text = f"""## ✅ CCL ディスパッチ結果

**CCL**: `{ccl}`

### AST 構造
```
{result['tree']}
```

### 関連ワークフロー
{', '.join(f'`{wf}`' for wf in result['workflows'])}

### 実行計画テンプレート
{result['plan_template']}"""
    
    # A5.2/§3.1: ToolCritic 的 tool-required 判定
    # SOURCE: パプくん §3.1 — tool-required classifier の導入提言
    # HGK翻訳: dispatch 出力の末尾に強制指示を追加し、テキスト手書き偽装を環境的に阻止
    if result.get("success"):
        tool_required = (
            "\n\n━━━ 🔒 Tool-Required 判定 ━━━\n"
            "この CCL 式は MCP ツール実行が【必須】です。\n"
            "テキスト応答で結果を手書きすることは θ12.1 違反 (BRD-B11) です。\n"
            f"次に呼ぶべきツール: hermeneus_run(ccl=\"{ccl}\")\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        text += tool_required
    
    return [TextContent(type="text", text=text)]


# PURPOSE: LLM による構造化下処理 (Phase 2.1: ele+ 改善)
_LLM_PREPROCESS_SYSTEM = """セッション履歴から冗長部分だけを削り、事実を全保持した構造化テキストを生成せよ。

## 消してよいもの（冗長）
- 挨拶・相槌（「了解しました」「はい」「ありがとうございます」等）
- 同じ内容の繰り返し・言い換え
- 「以下の通り」「次に」等のフィラー
- 作業の途中経過の逐次報告（結果だけ残す）

## 絶対消すな（事実）
- cascade_id の具体値
- ファイルの絶対パス
- 関数名・クラス名・変数名
- 行番号・バージョン番号・数値
- tool名（view_file, replace_file_content 等）とその入出力
- 決定事項・設定値・エラーメッセージ
- ユーザーの指示原文

## 出力形式
- 📋 **概要**: 何をしているか (1行)
- 🎯 **決定**: 確定事項 (箇条書き)
- ❓ **未決**: 未解決の問い (なければ省略)
- 🔧 **技術**: ファイルパス, 関数名, 設定値, cascade_id等 (そのまま列挙)
- 🛠️ **操作**: tool名→入力→出力 (各1行)
- 💬 **直近**: 最後2-3ターンの要点 (各1行)"""

_LLM_PREPROCESS_MODEL = "gemini-3-flash-preview"


async def _llm_preprocess_context(raw_text: str) -> str:
    """構造化テキストを LLM に通して情報ロスなしで整理する。

    CortexClient.ask_async() (gemini-3-flash) を使用。
    品質検証: (1) 必須セクションの存在, (2) キーワード保持率。
    失敗時は元テキストをそのまま返す (二重 fallback)。

    Args:
        raw_text: 構造化テキスト (session_read の出力をテキスト化したもの)

    Returns:
        LLM で整理されたテキスト (失敗時は raw_text)
    """
    # 短すぎるテキストは LLM に通す意味がない
    if len(raw_text) < 500:
        return raw_text

    try:
        from mekhane.ochema.cortex_client import CortexClient
        client = CortexClient(model=_LLM_PREPROCESS_MODEL)
        response = await asyncio.wait_for(
            client.ask_async(
                message=f"以下のセッション履歴を構造化してください:\n\n{raw_text}",
                system_instruction=_LLM_PREPROCESS_SYSTEM,
                max_tokens=4096,
                temperature=0.0,  # 確定的出力 — 情報ロス最小化
            ),
            timeout=20.0,  # Cortex API タイムアウト — イベントループ保護
        )
        if not response.text:
            return raw_text

        # 内容ベース品質検証
        result = response.text
        if not _validate_llm_output(raw_text, result):
            return raw_text
        return result
    except Exception:  # noqa: BLE001
        # Cortex 接続失敗 — 元テキストで続行
        return raw_text


# PURPOSE: LLM 出力の品質を内容ベースで検証する
_REQUIRED_SECTIONS = ["概要", "決定", "技術"]

def _validate_llm_output(raw_input: str, llm_output: str) -> bool:
    """LLM 圧縮出力の品質を内容ベースで検証する。

    検証項目:
    1. 圧縮されているか (出力 < 入力)
    2. 短すぎないか (100文字以上)
    3. 必須セクション (概要, 決定, 技術) の存在

    Args:
        raw_input: 元の構造化テキスト
        llm_output: LLM が生成した圧縮出力

    Returns:
        True = 品質OK, False = fallback すべき
    """
    # 1. 圧縮チェック: 出力が入力より長い → 圧縮失敗
    if len(llm_output) >= len(raw_input):
        return False
        
    # 2. 過剰圧縮・崩壊チェック: 100文字未満なら何かおかしい
    if len(llm_output) < 100:
        return False

    # 3. 必須セクションの存在チェック
    missing_sections = [s for s in _REQUIRED_SECTIONS if s not in llm_output]
    if len(missing_sections) >= 2:
        return False

    return True


# PURPOSE: LS セッション履歴から context を自動収集する (Phase 2: 環境強制)
async def _auto_gather_context(existing_context: str, cascade_id: str = "") -> str:
    """LS Cascade API 経由でセッションのトーク履歴を取得し、構造化テキストとして返す。

    AntigravityClient.session_read() を使って conversation を取得し、
    構造化下処理を適用: user/assistant は全文保持、tool は名前+引数概要+結果概要。

    Args:
        existing_context: 既存のコンテキスト (空でない場合は先頭に配置)
        cascade_id: LS の cascade_id (省略時は最新セッションを使用)

    Returns:
        enriched context string (失敗時は existing_context をそのまま返す)
    """
    try:
        from mekhane.ochema.antigravity_client import AntigravityClient
        client = AntigravityClient()

        # cascade_id 未指定時は最新セッションを取得
        if not cascade_id:
            info = client.session_info()
            sessions = info.get("sessions", [])
            if not sessions:
                return existing_context
            # 最新セッションの cascade_id を使用
            cascade_id = sessions[0].get("cascade_id", "")
            if not cascade_id:
                return existing_context

        # セッション履歴を取得 (max_turns=15, full=False: 各ターン 2000 文字上限)
        result = client.session_read(cascade_id, max_turns=15, full=False)
        if "error" in result:
            return existing_context

        conversation = result.get("conversation", [])
        if not conversation:
            return existing_context

        # 構造化下処理: 情報ロスなしでテキスト化
        lines: list[str] = []
        lines.append("## LS セッション履歴 (自動注入)")
        lines.append(f"cascade_id: {cascade_id}")
        lines.append(f"total_steps: {result.get('total_steps', '?')}")
        lines.append("")

        for turn in conversation:
            role = turn.get("role", "unknown")
            if role == "user":
                content = turn.get("content", "")
                truncated = " [truncated]" if turn.get("truncated") else ""
                lines.append(f"### User{truncated}")
                lines.append(content)
                lines.append("")
            elif role == "assistant":
                content = turn.get("content", "")
                model = turn.get("model", "")
                truncated = " [truncated]" if turn.get("truncated") else ""
                model_tag = f" ({model})" if model else ""
                lines.append(f"### Assistant{model_tag}{truncated}")
                lines.append(content)
                lines.append("")
            elif role == "tool":
                tool_name = turn.get("tool", "unknown")
                status = turn.get("status", "")
                # ele+ 改善: tool の引数/出力概要も含める
                tool_input = turn.get("input", "")
                tool_output = turn.get("output", "")
                tool_line = f"- 🔧 `{tool_name}` [{status}]"
                if tool_input:
                    # 引数は最大 200 文字で概要化
                    input_summary = tool_input[:200] + ("..." if len(str(tool_input)) > 200 else "")
                    tool_line += f"\n  - 入力: `{input_summary}`"
                if tool_output:
                    # 出力は最大 300 文字で概要化
                    output_summary = str(tool_output)[:300] + ("..." if len(str(tool_output)) > 300 else "")
                    tool_line += f"\n  - 出力: `{output_summary}`"
                lines.append(tool_line)

        session_text = "\n".join(lines)

        # LLM 構造化下処理 (Phase 2.1): 情報ロスなしで整理
        try:
            session_text = await asyncio.wait_for(
                _llm_preprocess_context(session_text),
                timeout=30.0,  # LLM 前処理タイムアウト
            )
        except asyncio.TimeoutError:
            pass  # タイムアウト時は raw session_text を維持

        # 既存コンテキストと結合
        if existing_context:
            return f"{existing_context}\n\n---\n\n{session_text}"
        return session_text

    except Exception:  # noqa: BLE001
        # LS 接続失敗 — MCP は IDE 内プロセスなので LS 未接続は異常状態
        # (ele+ 改善: fallback 発動 = 異常と明記)
        return existing_context


# PURPOSE: WF frontmatter の output_routing から保存先指示セクションを生成 (環境強制)
def _build_routing_section(metadata: dict, wf_id: str) -> str:
    """WF frontmatter の output_routing から保存先指示セクションを生成。

    Agent が保存先を推測せず、WF 定義に従うよう環境強制する。
    output_routing が未定義、または type が none/ephemeral の場合は空文字列を返す。
    """
    routing = metadata.get("output_routing")
    if not routing or not isinstance(routing, dict):
        return ""

    rtype = routing.get("type", "none")
    if rtype in ("none", "ephemeral"):
        return ""

    path = routing.get("path", "")
    naming = routing.get("naming", "")
    desc = routing.get("description", "")

    lines = [
        "\n### 📁 Output Routing (環境強制)",
        f"\n**保存タイプ**: `{rtype}`",
    ]
    if path:
        lines.append(f"**保存先**: `{path}`")
    if naming:
        lines.append(f"**命名規則**: `{naming}`")
    if desc:
        lines.append(f"**説明**: {desc}")
    lines.append(
        "\n> ⚠️ この保存先は WF frontmatter で定義されています。"
        " 成果物を上記パスに保存してください。\n"
    )
    return "\n".join(lines)


# PURPOSE: hermeneus_run の処理 — dispatch + execute をアトミックに実行
async def _handle_run(args: Dict[str, Any]) -> Sequence[TextContent]:
    """hermeneus_run の処理 — dispatch + execute を連続実行し結合結果を返す
    θ12.1 (CCL Execute Obligation) を環境的に強制するための主ツール。

    Single WF Compile-Only Mode:
      WF が1つだけの場合、LLM 実行をスキップして compile 結果のみ返す。
      Claude が WF 定義を view_file で読んで手動実行する (品質向上 + quota 節約)。
      マルチ WF (マクロ/シーケンス) は従来通り全自動実行。
    """
    ccl = args["ccl"]
    # P4: run 呼び出し時にペンディングをクリア (dispatch が内部で再記録するが即消す)
    _clear_pending_dispatch(ccl)
    verify = args.get("verify", True)
    audit = args.get("audit", True)
    model = args.get("model", "auto")
    use_llm = args.get("use_llm", True)
    account = args.get("account", "default")
    context = args.get("context", "")
    cascade_id = args.get("cascade_id", "")
    invocation_mode = args.get("invocation_mode", "explicit")
    enforce_contract = False
    try:
        from hermeneus.src.ccl_contracts import compile_ccl_contract
        _run_contract = compile_ccl_contract(ccl, invocation_mode=invocation_mode)
        enforce_contract = _run_contract.strict and invocation_mode == "explicit"
    except Exception as exc:  # noqa: BLE001
        if invocation_mode == "explicit":
            blocked_payload = {
                "status": "blocked",
                "error_type": "ccl_contract_blocked",
                "requested_ccl": ccl,
                "normalized_ccl": ccl,
                "unmet_requirements": ["contract_compile"],
                "blocking_reason": f"CCL contract compile failed: {exc}",
                "safe_next_step": "CCL contract compile が通るまで実行を停止",
            }
            blocked_json = json.dumps(blocked_payload, ensure_ascii=False, indent=2)
            return [TextContent(type="text", text=f"```json\n{blocked_json}\n```")]
        enforce_contract = False

    # θ12.1c Phase 2: コンテキスト自動豊富化 (環境強制)
    _CONTEXT_MIN_LENGTH = 200
    _context_warning = ""
    _AUTO_GATHER_TIMEOUT = 15.0  # 秒 — Cortex API 障害時のデッドロック防止
    _progress_reset()
    _progress("run_start", f"CCL: {ccl}")

    # ── 非同期コンテキスト取得タスク (パイプライニング用) ──
    async def _enrich_context_task(ctx_text: str) -> str:
        """コンテキスト自動豊富化を非同期タスクとして実行。
        dispatch と並列実行するためのラッパー。
        引数で context を受け取り、enriched な結果を返す (純粋関数的)。
        """
        if len(ctx_text) >= _CONTEXT_MIN_LENGTH:
            return ctx_text
        _progress("context_enrich", "LS セッション履歴を取得中...")
        try:
            enriched = await asyncio.wait_for(
                _auto_gather_context(ctx_text, cascade_id),
                timeout=_AUTO_GATHER_TIMEOUT,
            )
        except asyncio.TimeoutError:
            import logging
            logging.getLogger(__name__).warning(
                "_auto_gather_context timed out after %.0fs (Cortex API 障害の可能性)",
                _AUTO_GATHER_TIMEOUT,
            )
            _progress("context_enrich", "タイムアウト — 元コンテキストを維持")
            return ctx_text  # タイムアウト時は元のコンテキストを維持
        if enriched != ctx_text:
            _progress("context_enrich", f"完了 ({len(enriched)}文字)")
            return enriched
        elif ctx_text and 0 < len(ctx_text) < _CONTEXT_MIN_LENGTH:
            _progress("context_enrich", "失敗 — コンテキスト不足")
        return ctx_text

    # ── Auto-Search Hook for Compile-Only (N-5 (θ5.3) 環境強制) ──
    async def _search_gnosis(search_query: str) -> str:
        """Gnōsis 内部検索 (並列実行用サブタスク)"""
        try:
            from mekhane.anamnesis.index import GnosisIndex
            idx = GnosisIndex()
            gnosis_hits = idx.search(search_query, k=3)
            if gnosis_hits:
                lines = ["**Gnōsis (内部知識)**:"]
                for i, hit in enumerate(gnosis_hits, 1):
                    title = getattr(hit, "title", str(hit))[:120]
                    lines.append(f"  {i}. {title}")
                return "\n".join(lines)
        except Exception:  # noqa: BLE001
            return "**Gnōsis**: 利用不可 (faiss-cpu 未インストール等)"
        return ""

    async def _search_periskope(search_query: str) -> str:
        """Periskopē 外部検索 (並列実行用サブタスク)"""
        try:
            from mekhane.periskope.searchers.searxng import SearXNGSearcher
            searcher = SearXNGSearcher()
            periskope_hits = await searcher.search(search_query, max_results=3)
            if periskope_hits:
                lines = ["**Periskopē (外部知識)**:"]
                for i, hit in enumerate(periskope_hits, 1):
                    title = getattr(hit, "title", str(hit))[:120]
                    url = getattr(hit, "url", "")
                    lines.append(f"  {i}. {title}")
                    if url:
                        lines.append(f"     {url}")
                return "\n".join(lines)
        except Exception:  # noqa: BLE001
            return "**Periskopē**: 利用不可"
        return ""

    async def _search_semantic_scholar(search_query: str) -> str:
        """Semantic Scholar 論文検索 (並列実行用サブタスク)"""
        try:
            from mekhane.periskope.searchers.semantic_scholar_searcher import (
                SemanticScholarSearcher,
            )
            ss = SemanticScholarSearcher()
            ss_results = await ss.search(search_query, max_results=3)
            if ss_results:
                lines = ["**Semantic Scholar (学術論文)**:"]
                for hit in ss_results:
                    title = getattr(hit, "title", str(hit))[:120]
                    lines.append(f"  - {title}")
                return "\n".join(lines)
        except Exception:  # noqa: BLE001
            pass  # 学術検索は optional
        return ""

    async def _auto_search_for_compile_only(
        ccl_expr: str, search_context: str, wf_id: str,
        search_budget: int = -1, gnosis_search: bool = True,
    ) -> str:
        """Compile-Only パスで + 修飾子付き CCL の場合に検索を自動実行。

        PURPOSE: WF markdown に「省略禁止」と書くだけでは意志依存（第零原則違反）。
        コードレベルで検索を自動注入し、結果を Claude への返却テキストに含める。
        /noe+ Q3 分析 (2026-03-02) の結論 "A + C" の C に相当。

        3検索系統を asyncio.gather で並列実行 (パイプライニング最適化)。

        Precision-Aware Routing (Activity 3) 連携:
          search_budget: 検索回数 (0=スキップ, 1=Gnōsis のみ, 3=全系統)。
                         -1 の場合は従来動作 (+ 修飾子ベース)
          gnosis_search: False なら Gnōsis 検索を除外
        """
        # search_budget=0 なら precision routing が検索不要と判断 → スキップ
        if search_budget == 0:
            return ""

        # + 修飾子がなければスキップ (search_budget 未指定時の従来動作)
        if search_budget < 0 and "+" not in ccl_expr:
            return ""

        search_query = search_context[:200].replace("\n", " ").strip() if search_context else wf_id
        if not search_query:
            return ""

        # 検索系統を search_budget / gnosis_search で制御
        tasks = []
        task_labels = []
        if gnosis_search and search_budget != 1:  # budget=1 は Gnōsis のみの意味ではない
            tasks.append(_search_gnosis(search_query))
            task_labels.append("gnosis")
        elif gnosis_search:
            tasks.append(_search_gnosis(search_query))
            task_labels.append("gnosis")

        if search_budget >= 3 or search_budget < 0:  # 全系統 or 従来動作
            tasks.append(_search_periskope(search_query))
            task_labels.append("periskope")
            tasks.append(_search_semantic_scholar(search_query))
            task_labels.append("s2")
        elif search_budget >= 1 and not gnosis_search:
            # gnosis 除外だが budget >= 1 → Periskopē のみ
            tasks.append(_search_periskope(search_query))
            task_labels.append("periskope")

        if not tasks:
            return ""

        # 並列実行 (CPU out-of-order 実行のアナロジー)
        results = await asyncio.gather(*tasks)

        results_parts = [r for r in results if r]
        if not results_parts:
            return ""

        # 検索ソース情報
        budget_info = f" (budget={search_budget})" if search_budget >= 0 else ""
        return (
            f"\n### 🔍 自動検索結果 (N-5 (θ5.3) 環境強制{budget_info})\n\n"
            + "\n\n".join(results_parts)
            + "\n\n> この検索は `+` 修飾子に基づき自動実行されました。"
            "\n> 検索結果を WF 実行のコンテキストとして活用してください。\n"
        )

    # ── パイプライニング: context_enrich と dispatch を並列実行 ──
    # CPU パイプライン最適化のアナロジー:
    #   - context_enrich は I/O バウンド (LS API 呼び出し)
    #   - dispatch は CPU バウンド (CCL パース) → run_sync で thread pool
    #   - 依存関係なし → 並列実行可能
    if use_llm:
        _progress("pipeline", "context_enrich + dispatch を並列実行中...")
        from .dispatch import dispatch as _dispatch_fn

        enriched_context, dispatch_result = await asyncio.gather(
            _enrich_context_task(context),
            run_sync(_dispatch_fn, ccl),
        )

        # コンテキスト結果を反映
        if enriched_context != context:
            _context_warning = (
                "\n📡 **Context Auto-Enriched**: "
                f"LS セッション履歴を自動注入しました (元: {len(context)}文字 → {len(enriched_context)}文字)。\n"
            )
            context = enriched_context
        elif context and 0 < len(context) < _CONTEXT_MIN_LENGTH:
            _context_warning = (
                "\n🚨 **Context Enrichment Failed (異常)**: "
                f"コンテキストが {len(context)} 文字と短い (推奨: {_CONTEXT_MIN_LENGTH}+)。"
                "\nLS セッション履歴の自動取得にも失敗しました。"
                "\n⚠️ MCP は IDE 内プロセスのため、LS 未接続は異常状態です。\n"
            )

        _clear_pending_dispatch(ccl)  # dispatch が再記録するのでクリア
        _progress("pipeline", "完了")

        workflows = dispatch_result.get("workflows", [])
        tree = dispatch_result.get("tree", "")
        # 複合 AST ノードが存在する場合は compile-only にしない
        # (例: /bou+ >> /ene+ は workflows=['/bou'] だが ConvergenceLoop)
        _COMPOUND_NODES = ("Oscillation", "ConvergenceLoop", "Sequence", "Group", "MacroRef")
        is_compound = any(node in tree for node in _COMPOUND_NODES)
        if dispatch_result.get("success") and len(workflows) == 1 and not is_compound and not enforce_contract:
            wf_id = workflows[0]
            # WF 定義ファイルのパスを解決 (プリフェッチ — dispatch 直後に実行)
            wf_path = ""
            try:
                from .registry import get_workflow
                wf_def = await run_sync(get_workflow, wf_id)
                if wf_def and hasattr(wf_def, "source_path"):
                    wf_path = str(wf_def.source_path)
                elif wf_def and hasattr(wf_def, "path"):
                    wf_path = str(wf_def.path)
            except Exception:  # noqa: BLE001
                pass

            # mode / derivative 情報を抽出
            plan = dispatch_result.get("plan_template", "")
            # compile-only モードでは dispatch の "execute を呼べ" 警告は矛盾する → 除去
            import re
            plan = re.sub(r'⚠️⚠️⚠️.*?→ これで進めてよいですか？', '', plan, flags=re.DOTALL)
            plan = re.sub(r'━━━ 🔒 Tool-Required.*$', '', plan, flags=re.DOTALL)

            # Context 全文セクション — 切り詰めない (θ12.1c)
            context_section = ""
            if context:
                context_section = f"\n### 📄 実行コンテキスト\n\n{context}\n"

            # ── N-5 (θ5.3) 環境強制: + 修飾子付きなら検索自動注入 ──
            # Precision-Aware Routing Consumer: search_budget / gnosis_search を消費
            _search_budget = -1  # デフォルト: 従来動作 (+ 修飾子ベース)
            _gnosis_search = True
            _precision_info = ""
            try:
                from hermeneus.src.precision_router import (
                    compute_context_precision, route_execution,
                )
                # dispatch 後に遅延計算 (dispatch 並列化を維持するため)
                if context and len(context) >= 100:
                    _p_ml = compute_context_precision(context)
                    # dispatch_result から ccl_depth を取得
                    _ccl_depth = dispatch_result.get("depth_level", 2)
                    # P1 fix: PrecisionResult.diff を渡す (route_execution は float を期待)
                    _strategy = route_execution(_p_ml.diff, _ccl_depth)
                    _search_budget = _strategy.search_budget
                    _gnosis_search = _strategy.gnosis_search
                    _precision_info = (
                        f"\n📊 **Precision Routing**: "
                        f"precision_ml={_p_ml.diff:.3f}, "
                        f"strategy={_strategy.reasoning}, "
                        f"search_budget={_search_budget}, "
                        f"gnosis_search={_gnosis_search}\n"
                    )
            except ImportError as _ie:
                _precision_info = f"\n⚠️ Precision Router: ImportError — {_ie}\n"
            except Exception as _pe:  # noqa: BLE001
                import traceback
                _precision_info = f"\n⚠️ Precision Router Error: {_pe}\n```\n{traceback.format_exc()}\n```\n"

            search_section = ""
            if "+" in ccl or _search_budget > 0:
                _progress("auto_search", f"Gnōsis + Periskopē + S2 検索中... (WF: {wf_id})")
            try:
                search_section = await _auto_search_for_compile_only(
                    ccl, context or "", wf_id,
                    search_budget=_search_budget,
                    gnosis_search=_gnosis_search,
                )
                if search_section:
                    _progress("auto_search", "完了")
            except Exception as _search_err:  # noqa: BLE001
                import traceback
                search_section = (
                    f"\n### ⚠️ 自動検索エラー\n"
                    f"```\n{traceback.format_exc()}\n```\n"
                )
                _progress("auto_search", "エラー")

            # WF 内容を直接埋め込み (view_file 省略のため — Tier 1 改善)
            wf_content_embed = ""
            # Output Routing (θ-routing 環境強制)
            routing_section = ""
            _wf_metadata: dict = {}
            try:
                if wf_def and hasattr(wf_def, "raw_content") and wf_def.raw_content:
                    wf_content_embed = wf_def.raw_content
                if wf_def and hasattr(wf_def, "metadata") and wf_def.metadata:
                    _wf_metadata = wf_def.metadata

                # フォールバック: registry が WF を見つけられない場合、
                # .agents/workflows/ から直接 frontmatter を読み取る
                if not _wf_metadata or not wf_content_embed:
                    _wf_name = wf_id.strip("/").split("/")[-1]  # /eat → eat
                    _agents_wf = Path(__file__).resolve().parents[4] / ".agents" / "workflows" / f"{_wf_name}.md"
                    if _agents_wf.exists():
                        _raw = _agents_wf.read_text(encoding="utf-8")
                        if not wf_content_embed:
                            wf_content_embed = _raw
                        if not wf_path:
                            wf_path = str(_agents_wf)
                        # frontmatter パース
                        if not _wf_metadata:
                            import re as _re
                            _fm = _re.match(r"^---\s*\n(.*?)\n---\s*\n", _raw, _re.DOTALL)
                            if _fm:
                                import yaml as _yaml
                                _wf_metadata = _yaml.safe_load(_fm.group(1)) or {}

                if _wf_metadata:
                    routing_section = _build_routing_section(_wf_metadata, wf_id)
            except Exception:  # noqa: BLE001
                pass

            wf_section = ""
            if wf_content_embed:
                wf_section = f"\n### 📋 WF 定義 (全文 — 必読)\n\n{wf_content_embed}\n"
            else:
                wf_section = f"\n### 📋 WF 定義\n\n⚠️ WF 内容取得失敗。view_file で読込: `{wf_path}`\n"

            # ── Phase 分解実行指示の自動注入 (品質強制) ──
            # PURPOSE: WF 全文を渡すだけでは Claude が echo (パラフレーズ) で終わる。
            #          Phase ごとの独立プロンプトと品質強制ルール (anti-echo, ツール呼出義務,
            #          CHECKPOINT 出力義務) を環境強制として注入する。
            #          既存の PhaseDefinition.to_prompt() と get_execution_plan() を活用。
            phase_instructions_section = ""
            try:
                from .skill_registry import get_default_skill_registry
                _skill_reg = get_default_skill_registry()
                _wf_name = wf_id.strip("/").split("/")[-1]  # /noe → noe
                # CCL 修飾子から深度を推定
                _depth = "L3" if "+" in ccl else "L1" if "-" in ccl else "L2"
                _phase_instructions = _skill_reg.build_phase_instructions(
                    skill_id=_wf_name,
                    depth=_depth,
                    context=context or "",
                )
                if _phase_instructions:
                    phase_instructions_section = f"\n{_phase_instructions}\n"
            except Exception:  # noqa: BLE001
                pass  # Phase 分解失敗時は従来の WF 全文のみで続行

            # ── Phase-U 認知制御の自動注入 (環境強制) ──
            # PURPOSE: SKILL.md の Phase-U 定義を Compile-Only 出力に注入し、
            #          各 Phase で適用すべき認知操作 (Purge/Build/Audit) を環境強制する。
            #          Phase-U は「人間が読む知識」ではなく「LLM が従う指示」として機能する。
            phase_u_section = ""
            try:
                if not _skill_reg:
                    from .skill_registry import get_default_skill_registry
                    _skill_reg = get_default_skill_registry()
                phase_u_section = _skill_reg.extract_phase_u(_wf_name)
            except Exception:  # noqa: BLE001
                pass  # Phase-U 取得失敗はパイプラインをブロックしない


            text = f"""## 🔧 Compile-Only Mode — 単一 WF 直接実行

**CCL**: `{ccl}`
**WF**: `{wf_id}` | **パス**: `{wf_path}`
**モード**: compile-only (Claude 直接実行)
{_precision_info}{_context_warning}
### AST 構造
```
{tree}
```

### 実行計画
{plan}

---
{phase_instructions_section}{wf_section}
{phase_u_section}{context_section}{search_section}{routing_section}
> 💡 単一 WF のため Claude が直接実行します。
> **Phase 分解指示がある場合**: 指示に従い Phase ごとに逐次実行し CHECKPOINT を出力すること。
> **WF 全文**: 必ず全文を読み、Phase 分解指示と照合して漏れがないか確認すること。
"""
            # ── tape 自動記録 (環境強制: Compile-Only パスの tape バイパスを修正) ──
            # PURPOSE: executor._record_tape() は Multi WF パスのみ。Compile-Only は
            #          ここを通るため tape に記録されず、WF 実行データが欠損していた。
            #          Te 遷移 U 字仮説検証 + Q-series 分析の計測バイアス解消。
            try:
                from mekhane.ccl.tape import TapeWriter
                _tape = TapeWriter()
                _tape.log(
                    wf=ccl,
                    step="COMPILE_ONLY",
                    success=True,
                    source="compile_only",
                    workflow_name=wf_id,
                    session_id=cascade_id or "",
                )
                _tape.log(
                    wf=ccl,
                    step="COMPLETE",
                    success=True,
                    source="compile_only",
                    workflow_name=wf_id,
                    session_id=cascade_id or "",
                    model="claude_direct",
                )
            except Exception:  # noqa: BLE001
                pass  # tape 記録失敗はパイプラインをブロックしない

            return [TextContent(type="text", text=text)]

    # ── use_llm=False の場合: ここでコンテキストを取得 (上で並列化されていない) ──
    if not use_llm and len(context) < _CONTEXT_MIN_LENGTH:
        enriched_context = await _enrich_context_task(context)
        if enriched_context != context:
            _context_warning = (
                "\n📡 **Context Auto-Enriched**: "
                f"LS セッション履歴を自動注入しました (元: {len(context)}文字 → {len(enriched_context)}文字)。\n"
            )
            context = enriched_context
        elif context and 0 < len(context) < _CONTEXT_MIN_LENGTH:
            _context_warning = (
                "\n🚨 **Context Enrichment Failed (異常)**: "
                f"コンテキストが {len(context)} 文字と短い (推奨: {_CONTEXT_MIN_LENGTH}+)。"
                "\nLS セッション履歴の自動取得にも失敗しました。"
                "\n⚠️ MCP は IDE 内プロセスのため、LS 未接続は異常状態です。\n"
            )

    # ── Multi WF / use_llm=False: 従来通りフル実行 ──
    # 1. パース (dispatch) を実行
    _progress("multi_dispatch", f"マルチ WF パース中: {ccl}")
    dispatch_content = await _handle_dispatch({"ccl": ccl, "invocation_mode": invocation_mode})
    dispatch_text = dispatch_content[0].text
    # P4: _handle_dispatch が再記録するので、ここでもクリア
    _clear_pending_dispatch(ccl)
    _progress("multi_dispatch", "完了")

    if "❌ CCL パースエラー" in dispatch_text:
        _progress("multi_dispatch", "パースエラー — 中断")
        return [TextContent(type="text", text=dispatch_text)]

    # 2. 実行 (execute) を実行
    _progress("multi_execute", f"MacroExecutor 起動中 (model={model})")
    exec_args = {
        "ccl": ccl,
        "context": context,
        "verify": verify,
        "audit": audit,
        "model": model,
        "use_llm": use_llm,
        "account": account,
        "invocation_mode": invocation_mode,
    }
    execute_content = await _handle_execute(exec_args)
    execute_text = execute_content[0].text
    _progress("multi_execute", "完了")

    # 3. 結合して返す (A2.3 think 的中間確認付き)
    # SOURCE: パプくん A2.3 — Anthropic think ツール研究 (τ-Bench pass^1 0.37→0.57, 54% 改善)
    # HGK翻訳: hermeneus_run 自体が「実行+省察」のアトミック単位として機能する
    think_section = (
        "\n\n━━━ 🧠 材料→批評 義務 (θ12.1b) ━━━\n"
        "⚠️ この出力は「材料」であって「カンペ」ではない (BRD-B18)。\n"
        "以下を Creator に報告する前に必ず実行せよ:\n"
        "\n"
        "1. 【エラー調査】エラーがあれば推測ではなく調査せよ (quota確認, runtime.py確認等)\n"
        "2. 【独立批評】Gemini出力に対する自分の評価・補足・反論を明記せよ (N-7)\n"
        "3. 【SOURCE分離】何がGemini出力で何が自分の分析かを区別せよ\n"
        "4. 【情報保存】要約時に情報量を落とすな。落とすなら何を落としたか明記せよ\n"
        "\n"
        "❌ 禁止: 出力をそのままテーブルに圧縮して転送する「劣化伝達」\n"
        "✅ 義務: 材料を咀嚼し、自分の判断を加えた上で Creator に報告する\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    combined_text = (
        f"{_context_warning}{dispatch_text}\n\n---\n\n{execute_text}{think_section}"
    )
    
    return [TextContent(type="text", text=combined_text)]


# =============================================================================
# Fallback (MCP なしの場合)
# =============================================================================

# PURPOSE: [L2-auto] MCP SDK がない場合のフォールバック
class FallbackServer:
    """MCP SDK がない場合のフォールバック"""
    
    # PURPOSE: CCL を実行
    async def execute(self, ccl: str, context: str = "") -> Dict[str, Any]:
        """CCL を実行"""
        from .executor import run_workflow
        
        result = await run_workflow(ccl=ccl, context=context)
        return result.to_dict()
    
    # PURPOSE: CCL をコンパイル
    async def compile(self, ccl: str, model: str = "openai/gpt-4o") -> str:
        """CCL をコンパイル"""
        from . import compile_ccl
        return compile_ccl(ccl, model=model)


# =============================================================================
# Entry Point
# =============================================================================

# PURPOSE: MCP サーバーを起動
async def main():
    """MCP サーバーを起動"""
    # F4: Save original stdout for MCP protocol before redirecting.
    # CRITICAL: stdio_server() must receive the REAL stdout, not stderr.
    # MCP SDK v1.26.0 reads sys.stdout.buffer internally.
    import anyio
    from io import TextIOWrapper
    _original_stdout = sys.stdout
    real_stdout = anyio.wrap_file(
        TextIOWrapper(_original_stdout.buffer, encoding="utf-8")
    )
    real_stdin = anyio.wrap_file(
        TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    )
    sys.stdout = sys.stderr

    if not MCP_AVAILABLE:
        print("MCP SDK not available. Install with: pip install mcp", file=sys.stderr)
        print("Running in fallback mode...", file=sys.stderr)
        
        # Simple REPL for testing
        fallback = FallbackServer()
        while True:
            try:
                line = input("hermeneus> ")
                if line.startswith("/"):
                    result = await fallback.execute(line)
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                elif line == "quit":
                    break
            except EOFError:
                break
        return
    
    async def _heartbeat():
        """Background heartbeat — proves event loop is alive."""
        count = 0
        while True:
            await asyncio.sleep(30)
            count += 1
            print(f"[hermeneus] heartbeat #{count} (event loop alive)", file=sys.stderr, flush=True)
            # P4: 定期的に pending dispatch トラッカーを検証し WBC にアラート化
            try:
                violations = check_pending_dispatches()
                for v in violations:
                    print(f"[hermeneus] 🚨 θ12.1 WBC Alert: dispatch({v['ccl']}) pending for {v['elapsed_sec']}s", file=sys.stderr, flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"[hermeneus] Failed to check pending dispatches: {e}", file=sys.stderr, flush=True)

    # Sekishō Gate hooks (非 MCPBase パターン — _call_tool_handler ラップ)
    try:
        from mekhane.mcp.mcp_base import install_all_hooks_for_server
        _log = lambda msg: print(f"[hermeneus] {msg}", file=sys.stderr, flush=True)
        install_all_hooks_for_server(server, "hermeneus", _log)
    except Exception as e:  # noqa: BLE001
        print(f"[hermeneus] Sekishō hooks not available: {e}", file=sys.stderr, flush=True)

    # MCP サーバーを起動
    async with stdio_server(stdin=real_stdin, stdout=real_stdout) as (read_stream, write_stream):
        print("[hermeneus] stdio connected", file=sys.stderr, flush=True)
        hb_task = asyncio.create_task(_heartbeat())
        try:
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
        finally:
            hb_task.cancel()
            try:
                await hb_task
            except asyncio.CancelledError:
                pass


# PURPOSE: Streamable HTTP モードの main 関数
def main_http(port: int = 9703):
    """MCP サーバーを Streamable HTTP で起動"""
    from mekhane.mcp.mcp_base import run_streamable_http
    
    async def _heartbeat_http():
        count = 0
        while True:
            await asyncio.sleep(30)
            count += 1
            print(f"[hermeneus] heartbeat #{count} (event loop alive)", file=sys.stderr, flush=True)
            try:
                violations = check_pending_dispatches()
                for v in violations:
                    print(f"[hermeneus] 🚨 θ12.1 WBC Alert: dispatch({v['ccl']}) pending for {v['elapsed_sec']}s", file=sys.stderr, flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"[hermeneus] Failed to check pending dispatches: {e}", file=sys.stderr, flush=True)

    def _log(msg):
        print(f"[hermeneus] {msg}", file=sys.stderr, flush=True)

    run_streamable_http(server, port=port, log_fn=_log, background_tasks=[_heartbeat_http])


# PURPOSE: エントリーポイント
def run_server():
    """エントリーポイント — CLI 引数で transport を切替"""
    import argparse
    parser = argparse.ArgumentParser(description="Hermēneus MCP Server", add_help=False)
    parser.add_argument("--transport", type=str, default="stdio",
                        choices=["stdio", "http", "streamable-http"])
    parser.add_argument("--port", type=int, default=9703)
    args, _ = parser.parse_known_args()

    if args.transport in ("http", "streamable-http"):
        main_http(port=args.port)
    else:
        asyncio.run(main())


if __name__ == "__main__":
    run_server()
