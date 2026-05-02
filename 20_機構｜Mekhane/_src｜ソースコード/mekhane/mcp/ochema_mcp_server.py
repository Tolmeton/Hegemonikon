# PROOF: [L2/インフラ] <- mekhane/mcp/ochema_mcp_server.py Ochēma MCP Server
#!/usr/bin/env python3
"""
Ochēma MCP Server — Antigravity Language Server Bridge

Send prompts to LLM (Claude/Gemini) via local Language Server.
Also provides status, model listing, and chat.

WARNING: ToS グレーゾーン。実験用途限定。公開禁止。
"""

import asyncio
import uuid

from mekhane.mcp.mcp_base import MCPBase, StdoutSuppressor, run_sync
from mcp.types import TextContent, Tool
from pathlib import Path

# Shadow Gemini (S-003: Claude × Gemini 分業)
from mekhane.mcp.shadow_gemini import get_shadow

_base = MCPBase(
    "ochema",
    "0.2.0",
    "Ochēma — Antigravity Language Server bridge. "
    "Send prompts to LLM (Claude/Gemini) via local Language Server. "
    "Also provides status, model listing, and chat.",
)
server = _base.server
log = _base.log

# OchemaService — unified LLM service (singleton)
# PURPOSE: get_service — OchemaService シングルトン取得
def get_service():
    """OchemaService をシングルトンで取得。"""
    with StdoutSuppressor():
        from mekhane.ochema.service import OchemaService
    svc = OchemaService.get()
    log(f"OchemaService: {svc}")
    return svc

# ============ Stateful Chat Conversations ============
_MAX_CONVERSATIONS = 10
_conversations: dict[str, object] = {}  # {conv_id: ChatConversation or _LSChatConversation}


class _LSChatConversation:
    """Claude (LS 経由) 用のステートフルチャット。

    LS の cascadeId でサーバーサイドに会話履歴を保持する。
    CortexClient.ChatConversation と同じ send/close インターフェース。
    """

    def __init__(self, model: str):
        self.model = model
        self.cascade_id = ""  # 初回 send 時に自動生成
        self.turn_count = 0

    def send(self, message: str) -> object:
        svc = get_service()
        response = svc.chat(
            message=message,
            model=self.model,
            cascade_id=self.cascade_id,
            timeout=120.0,
        )
        # cascadeId を保持して次回以降再利用
        if hasattr(response, 'cascade_id') and response.cascade_id:
            self.cascade_id = response.cascade_id
        self.turn_count += 1
        return response

    def close(self):
        self.cascade_id = ""
        self.turn_count = 0




# PURPOSE: [L2-auto] List available tools.

# PURPOSE: [L2-auto] list_tools の非同期処理定義
@server.list_tools()
async def list_tools():
    """List available tools — 統合版 v2 (17→5 ファサード)."""
    log("list_tools called (v2 consolidated)")
    return [
        # ============ 1. ask: LLM 呼出統合 ============
        Tool(
            name="ask",
            description=(
                "LLM にプロンプトを送信する統合ツール。mode で経路を選択。"
                "mode=ls: Antigravity Language Server 経由 (Claude/Gemini)。"
                "mode=cortex: Gemini Cortex API 直接呼出 (高速)。"
                "mode=chat: Gemini generateChat API (マルチターン、履歴手動)。"
                "mode=tools: Gemini + Tool Use (ファイル操作等の自律エージェント)。"
                "Example: ask(message='...', mode='cortex')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "LLM に送信するプロンプト",
                    },
                    "mode": {
                        "type": "string",
                        "description": (
                            "呼出経路。ls=Language Server (default), "
                            "cortex=Gemini直接, chat=generateChat, tools=Tool Use"
                        ),
                        "enum": ["ls", "cortex", "chat", "tools"],
                        "default": "ls",
                    },
                    "model": {
                        "type": "string",
                        "description": (
                            "モデル指定。mode=ls: MODEL_PLACEHOLDER_M35 (Sonnet, default), "
                            "MODEL_PLACEHOLDER_M26 (Opus). "
                            "mode=cortex/chat/tools: gemini-3-flash-preview (default), "
                            "gemini-3.1-pro-preview"
                        ),
                    },
                    "timeout": {
                        "type": "number",
                        "description": "最大待機秒数 (default: 120)",
                        "default": 120,
                    },
                    "account": {
                        "type": "string",
                        "description": "TokenVault account name (default: 'auto')",
                        "default": "auto",
                    },
                    "system_instruction": {
                        "type": "string",
                        "description": "システム指示 (mode=cortex/tools で有効)",
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "最大出力トークン数 (default: 65536)",
                        "default": 65536,
                    },
                    "cached_content": {
                        "type": "string",
                        "description": "Gemini Context Cache名 (mode=cortex で有効)",
                    },
                    "history": {
                        "type": "array",
                        "description": "会話履歴 (mode=chat で有効)。{author:1=user/2=model, content:string}",
                        "items": {
                            "type": "object",
                            "properties": {
                                "author": {"type": "number"},
                                "content": {"type": "string"},
                            },
                        },
                    },
                    "tier_id": {
                        "type": "string",
                        "description": "モデルルーティング tier (mode=chat で有効)",
                        "default": "",
                    },
                    "planner_params": {
                        "type": "object",
                        "description": "CascadePlannerConfig 注入 (mode=ls のみ)",
                    },
                    "thinking_budget": {
                        "type": "integer",
                        "description": "思考トークン予算 (mode=tools で有効。default: 32768)",
                        "default": 32768,
                    },
                    "max_iterations": {
                        "type": "integer",
                        "description": "ツール呼出最大ラウンド数 (mode=tools で有効。default: 10)",
                        "default": 10,
                    },
                },
                "required": ["message"],
            },
        ),
        # ============ 2. chat: ステートフル会話管理 ============
        Tool(
            name="chat",
            description=(
                "ステートフルなマルチターン会話を管理。"
                "action=start: 新規会話を開始し conversation_id を返す。"
                "action=send: 既存会話にメッセージを送信。"
                "action=close: 会話を終了しリソースを解放。"
                "Example: chat(action='start', model='claude-sonnet-4-6')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "操作: start/send/close",
                        "enum": ["start", "send", "close"],
                    },
                    "conversation_id": {
                        "type": "string",
                        "description": "会話 ID (action=send/close で必須)",
                    },
                    "message": {
                        "type": "string",
                        "description": "送信メッセージ (action=send で必須)",
                    },
                    "model": {
                        "type": "string",
                        "description": "モデル (action=start で使用。空=デフォルト)",
                        "default": "",
                    },
                    "tier_id": {
                        "type": "string",
                        "description": "モデル tier (action=start で使用)",
                        "default": "",
                    },
                    "account": {
                        "type": "string",
                        "description": "TokenVault account (default: 'auto')",
                        "default": "auto",
                    },
                },
                "required": ["action"],
            },
        ),
        # ============ 3. context: Context Rot 管理 ============
        Tool(
            name="context",
            description=(
                "セッションの Context Rot 管理。"
                "action=status: Context Rot 健全性と推奨事項を返す。"
                "action=distill: /rom+ ワークフローで ROM ファイルに蒸留。"
                "action=cache: Boot Context を Gemini Context Cache に保存。"
                "Example: context(action='status')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "操作: status/distill/cache",
                        "enum": ["status", "distill", "cache"],
                    },
                    "cascade_id": {
                        "type": "string",
                        "description": "セッション ID (action=status/distill で使用)",
                    },
                    "topic": {
                        "type": "string",
                        "description": "ROM トピック (action=distill で使用)",
                    },
                    "depth": {
                        "type": "string",
                        "description": "蒸留深度: L1/L2/L3 (action=distill。default: L3)",
                        "default": "L3",
                    },
                    "context": {
                        "type": "string",
                        "description": "蒸留対象テキスト (action=distill で明示的に指定する場合)",
                    },
                    "text": {
                        "type": "string",
                        "description": "キャッシュするテキスト (action=cache で必須)",
                    },
                    "system_instruction": {
                        "type": "string",
                        "description": "システム指示 (action=cache で使用)",
                    },
                    "ttl": {
                        "type": "integer",
                        "description": "キャッシュ TTL 秒数 (action=cache。default: 3600)",
                        "default": 3600,
                    },
                },
                "required": ["action"],
            },
        ),
        # ============ 4. info: 状態・管理照会 ============
        Tool(
            name="info",
            description=(
                "Ochēma の状態・管理情報を照会。"
                "action=ping: ヘルスチェック。"
                "action=status: Cortex API 接続状態。"
                "action=models: 利用可能モデル一覧。"
                "action=quota: Gemini API 残量 + チャットセッション情報。"
                "action=session: アクティブチャットセッション一覧。"
                "action=shadow: Shadow Gemini 状態確認・制御。"
                "Example: info(action='quota')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "照会種別: ping/status/models/quota/session/shadow",
                        "enum": ["ping", "status", "models", "quota", "session", "shadow"],
                    },
                    "account": {
                        "type": "string",
                        "description": "TokenVault account (action=quota で使用)",
                        "default": "default",
                    },
                    "conversation_id": {
                        "type": "string",
                        "description": "特定セッション ID (action=session で使用)",
                    },
                    "enabled": {
                        "type": "boolean",
                        "description": "Shadow Gemini ON/OFF (action=shadow で使用)",
                    },
                },
                "required": ["action"],
            },
        ),
        # ============ 5. plan_task: タスク分解 ============
        Tool(
            name="plan_task",
            description=(
                "コード変更リクエストを並列実行可能なサブタスクに分解。"
                "Jules 並列実行用の wave 構造を生成。"
                "Example: plan_task(prompt='Add auth + logging', repo='owner/repo')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "コード変更リクエスト",
                    },
                    "repo": {
                        "type": "string",
                        "description": "リポジトリ (owner/repo 形式)",
                    },
                    "branch": {
                        "type": "string",
                        "description": "開始ブランチ (default: main)",
                        "default": "main",
                    },
                    "max_subtasks": {
                        "type": "integer",
                        "description": "最大サブタスク数 (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["prompt", "repo"],
            },
        ),
    ]

# PURPOSE: [L2-auto] Handle tool calls.

# PURPOSE: [L2-auto] call_tool の非同期処理定義
@server.call_tool(validate_input=True)
async def call_tool(name: str, arguments: dict):
    """Handle tool calls with global timeout protection."""
    log(f"call_tool: {name} with {arguments}")

    # イベントループのデッドロックを防ぐグローバルタイムアウト
    if name in ("ask", "ask_cortex", "ask_with_tools"):
        timeout_sec = float(arguments.get("timeout", 150.0))
    elif name in ("ask_chat", "send_chat", "start_chat", "ochema_plan_task"):
        timeout_sec = 180.0
    elif name == "context_rot_distill":
        timeout_sec = 120.0  # LLM 分類 + 要約生成 + ファイル I/O
    elif name == "context_rot_status":
        timeout_sec = 30.0   # session_info 取得 + ROM 一覧
    else:
        timeout_sec = 15.0  # quota, status, models, ping, session_info etc.

    try:
        import asyncio
        async with asyncio.timeout(timeout_sec):
            return await _call_tool_inner(name, arguments)
    except asyncio.TimeoutError:
        log(f"Global timeout ({timeout_sec}s) exceeded for {name}")
        return [TextContent(type="text", text=f"Error: Tool '{name}' timed out after {timeout_sec}s. Protected event loop from deadlock.")]
    except Exception as e:  # noqa: BLE001
        log(f"Fatal error in call_tool ({name}): {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _call_tool_inner(name: str, arguments: dict):
    """Inner handler for tool calls.

    v2 統合: 新ファサード名 → 旧ツール名に変換して既存ロジックに委譲。
    旧ツール名での直接呼出も後方互換で動作する。
    """
    # ============ エイリアスレイヤー (v2 統合) ============
    # 新ファサード名を旧ツール名に変換
    if name == "ask":
        mode = arguments.get("mode", "ls")
        if mode == "cortex":
            name = "ask_cortex"
        elif mode == "chat":
            name = "ask_chat"
        elif mode == "tools":
            name = "ask_with_tools"
        # mode == "ls" → name = "ask" のまま (既存ロジック)
    elif name == "chat":
        action = arguments.get("action", "")
        if action == "start":
            name = "start_chat"
        elif action == "send":
            name = "send_chat"
        elif action == "close":
            name = "close_chat"
        else:
            return [TextContent(type="text", text=f"Error: chat action '{action}' is invalid. Use: start/send/close")]
    elif name == "context":
        action = arguments.get("action", "")
        if action == "status":
            name = "context_rot_status"
        elif action == "distill":
            name = "context_rot_distill"
        elif action == "cache":
            name = "cache_boot_context"
        else:
            return [TextContent(type="text", text=f"Error: context action '{action}' is invalid. Use: status/distill/cache")]
    elif name == "info":
        action = arguments.get("action", "")
        if action == "ping":
            name = "ping"
        elif action == "status":
            name = "status"
        elif action == "models":
            name = "models"
        elif action == "quota":
            name = "cortex_quota"
        elif action == "session":
            name = "session_info"
        elif action == "shadow":
            name = "shadow_status"
        else:
            return [TextContent(type="text", text=f"Error: info action '{action}' is invalid. Use: ping/status/models/quota/session/shadow")]
    elif name == "plan_task":
        name = "ochema_plan_task"

    # ============ 旧ツール名ディスパッチ (後方互換) ============
    if name == "ping":
        return [TextContent(type="text", text="pong")]

    if name == "ask":
        message = arguments.get("message", "")
        model = arguments.get("model", "MODEL_PLACEHOLDER_M35")
        timeout = arguments.get("timeout", 120)
        planner_params = arguments.get("planner_params", None)

        if not message:
            return [TextContent(type="text", text="Error: message is required")]

        try:
            svc = get_service()
            log(f"Sending to {model}: {message[:50]}...")

            response = await run_sync(svc.ask, message, model=model, timeout=timeout, planner_params=planner_params, force_provider="ls")

            output_lines = [
                "# Ochēma LLM Response\n",
                f"**Model**: {response.model}",
                f"**Cascade ID**: {response.cascade_id[:16]}...",
                "",
                "## Response\n",
                response.text,
            ]

            if response.thinking:
                output_lines.extend([
                    "",
                    "## Thinking\n",
                    response.thinking[:1000],
                ])

            if response.token_usage:
                output_lines.extend([
                    "",
                    "## Token Usage\n",
                    f"```json\n{response.token_usage}\n```",
                ])

            log(f"Response received: {len(response.text)} chars")
            return [TextContent(type="text", text="\n".join(output_lines))]

        except TimeoutError as e:
            log(f"Timeout: {e}")
            return [TextContent(type="text", text=f"Error: LLM response timed out ({timeout}s)")]
        except Exception as e:  # noqa: BLE001
            log(f"Ask error: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "ask_cortex":
        message = arguments.get("message", "")
        model = arguments.get("model", "gemini-3-flash-preview")
        system_instruction = arguments.get("system_instruction")
        max_tokens = int(arguments.get("max_tokens", 65536))
        timeout = float(arguments.get("timeout", 120))
        account = arguments.get("account", "auto")
        cached_content = arguments.get("cached_content", "")

        if not message:
            return [TextContent(type="text", text="Error: message is required")]

        # ★ Phase 3A: CAG Auto-Routing
        # cached_content 未指定 → アクティブ cache を自動検出して CAG ルートへ
        # opt-out: cached_content="none" で明示的に無効化
        if cached_content == "none":
            cached_content = ""  # opt-out: CAG 無効化
        elif not cached_content:
            try:
                from mekhane.ochema.cortex_cache import get_cache
                _ar_cache = get_cache()
                # 1. インメモリ状態を優先 (0ms, 同一プロセス内)
                _ar_health = _ar_cache.cache_health()
                if _ar_health.get("active") and _ar_health.get("ttl_remaining", 0) > 60:
                    cached_content = _ar_health["cache_name"]
                    log(f"CAG Auto-Routing (in-memory): {cached_content[:30]}")
                else:
                    # 2. API フォールバック: list_caches から hgk-boot-*/hgk-rom-* を検索
                    for _ar_ci in _ar_cache.list_caches():
                        if _ar_ci.display_name.startswith(("hgk-boot-", "hgk-rom-")):
                            cached_content = _ar_ci.name
                            log(f"CAG Auto-Routing (API): {cached_content[:30]}")
                            break
            except Exception as _ar_err:  # noqa: BLE001
                log(f"CAG Auto-Routing error (non-blocking): {_ar_err}")

        # CAG 透過ルート: cached_content が指定されていれば CortexCache 経由
        if cached_content:
            try:
                from mekhane.ochema.cortex_cache import get_cache
                ctx_cache = get_cache()
                log(f"CAG ask (cached={cached_content[:20]}): {message[:50]}...")
                result = await run_sync(
                    ctx_cache.ask,
                    message,
                    cache_name=cached_content,
                    max_tokens=max_tokens,
                )
                output_lines = [
                    "# Cortex Response (CAG — Context Cached)\n",
                    f"**Model**: {result['model']}",
                    f"**Cache**: `{cached_content[:30]}…`",
                ]
                if result.get("token_usage"):
                    usage = result["token_usage"]
                    output_lines.append(
                        f"**Tokens**: {usage.get('prompt_tokens', 0)} → "
                        f"{usage.get('completion_tokens', 0)} "
                        f"(cached: {usage.get('cached_tokens', 0)}, "
                        f"total: {usage.get('total_tokens', 0)})"
                    )
                output_lines.extend(["", "## Response\n", result["text"]])
                log(f"CAG response: {len(result['text'])} chars")

                # Passive Keep-Alive: TTL 残り < 15分 なら自動延長
                try:
                    extended = ctx_cache.maybe_extend_ttl()
                    if extended:
                        output_lines.append("\n**Keep-Alive**: TTL extended (1h)")
                except Exception as ka_err:  # noqa: BLE001
                    log(f"CAG keep-alive error (non-blocking): {ka_err}")

                # Shadow Gemini: CAG ルートでも記録 + ピギーバック
                try:
                    shadow = get_shadow()
                    shadow.record(
                        backend="ochema",
                        tool_name="ask_cortex",
                        summary=message,
                        result_preview=result["text"],
                        reasoning=f"CAG cached ({result.get('model', 'unknown')}). "
                                  f"Claude の質問: {message}",
                    )
                    shadow_result = await shadow.maybe_shadow()
                    if shadow_result:
                        output_lines.append(shadow.format_piggyback(shadow_result))
                except Exception as sg_err:  # noqa: BLE001
                    log(f"Shadow Gemini error (non-blocking): {sg_err}")

                return [TextContent(type="text", text="\n".join(output_lines))]
            except Exception as e:  # noqa: BLE001
                log(f"CAG ask error (falling back to direct): {e}")
                # フォールバック: 通常の Cortex API 経由

        try:
            svc = get_service()
            log(f"Asking {model} (account={account}): {message[:50]}...")

            response = await run_sync(
                svc.ask,
                message,
                model=model,
                system_instruction=system_instruction,
                max_tokens=max_tokens,
                timeout=timeout,
                account=account,
            )

            output_lines = [
                "# Cortex Response (Gemini Direct)\n",
                f"**Model**: {response.model}",
            ]

            if response.token_usage:
                usage = response.token_usage
                output_lines.append(
                    f"**Tokens**: {usage.get('prompt_tokens', 0)} → "
                    f"{usage.get('completion_tokens', 0)} "
                    f"(total: {usage.get('total_tokens', 0)})"
                )

            output_lines.extend(["", "## Response\n", response.text])

            # Shadow Gemini: 記録 + ピギーバック
            shadow = get_shadow()
            shadow.record(
                backend="ochema",
                tool_name="ask_cortex",
                summary=message,
                result_preview=response.text,
                reasoning=f"Gemini Direct ({response.model}). "
                          f"Claude の質問: {message}",
            )
            shadow_result = await shadow.maybe_shadow()
            if shadow_result:
                output_lines.append(shadow.format_piggyback(shadow_result))

            log(f"Cortex response: {len(response.text)} chars")
            return [TextContent(type="text", text="\n".join(output_lines))]

        except Exception as e:  # noqa: BLE001
            log(f"Cortex ask error: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "ask_chat":
        message = arguments.get("message", "")
        model = arguments.get("model", "")
        history = arguments.get("history", [])
        tier_id = arguments.get("tier_id", "")
        account = arguments.get("account", "auto")

        if not message:
            return [TextContent(type="text", text="Error: message is required")]

        try:
            svc = get_service()
            log(f"Chat: {message[:50]}... (model={model or 'default'}, account={account})")

            response = await run_sync(
                svc.chat,
                message=message,
                model=model,
                history=history,
                tier_id=tier_id,
                account=account,
            )

            output_lines = [
                "# Chat Response (generateChat)\n",
                f"**Model**: {response.model}",
                "",
                "## Response\n",
                response.text,
            ]

            # Shadow Gemini: 記録 + ピギーバック
            shadow = get_shadow()
            shadow.record(
                backend="ochema",
                tool_name="ask_chat",
                summary=message,
                result_preview=response.text,
                reasoning=f"Chat ({response.model}). Claude の質問: {message}",
            )
            shadow_result = await shadow.maybe_shadow()
            if shadow_result:
                output_lines.append(shadow.format_piggyback(shadow_result))

            log(f"Chat response: {len(response.text)} chars")
            return [TextContent(type="text", text="\n".join(output_lines))]

        except Exception as e:  # noqa: BLE001
            log(f"Chat error: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "start_chat":
        model = arguments.get("model", "")
        tier_id = arguments.get("tier_id", "")
        account = arguments.get("account", "auto")
        try:
            if len(_conversations) >= _MAX_CONVERSATIONS:
                oldest_id = next(iter(_conversations))
                _conversations[oldest_id].close()
                del _conversations[oldest_id]
                log(f"Evicted conversation {oldest_id}")

            svc = get_service()
            # Claude モデルの場合は LS 経由の cascadeId ベースチャット
            if svc._is_claude_model(model):
                conv = _LSChatConversation(model=model)
                conv_id = str(uuid.uuid4())[:8]
                _conversations[conv_id] = conv
                log(f"Started LS chat {conv_id} (Claude model={model})")
                return [TextContent(
                    type="text",
                    text=(
                        f"# Chat Started (Claude via LS)\n\n"
                        f"**Conversation ID**: `{conv_id}`\n"
                        f"**Model**: {model}\n"
                        f"**Backend**: LS ConnectRPC (cascadeId stateful)\n\n"
                        f"Use `send_chat` with this ID to send messages.\n"
                        f"Use `close_chat` to end the conversation."
                    ),
                )]
            else:
                # Gemini → Cortex generateChat
                conv = svc.start_chat(model=model, tier_id=tier_id, account=account)
                conv_id = str(uuid.uuid4())[:8]
                _conversations[conv_id] = conv
                log(f"Started conversation {conv_id} (model={model or 'default'}, total: {len(_conversations)})")
                return [TextContent(
                    type="text",
                    text=(
                        f"# Chat Started\n\n"
                        f"**Conversation ID**: `{conv_id}`\n"
                        f"Use `send_chat` with this ID to send messages.\n"
                        f"Use `close_chat` to end the conversation."
                    ),
                )]
        except Exception as e:  # noqa: BLE001
            log(f"Start chat error: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "send_chat":
        conv_id = arguments.get("conversation_id", "")
        message = arguments.get("message", "")

        if not conv_id or not message:
            return [TextContent(type="text", text="Error: conversation_id and message are required")]

        conv = _conversations.get(conv_id)
        if conv is None:
            return [TextContent(
                type="text",
                text=f"Error: conversation '{conv_id}' not found. Use start_chat first.",
            )]

        from mekhane.agent_guard.session_lock import SessionWriteLock
        from pathlib import Path

        lock_dir = Path.home() / ".config" / "ochema" / "locks"
        try:
            lock_dir.mkdir(parents=True, exist_ok=True)
        except Exception:  # noqa: BLE001
            pass

        lock_path = str(lock_dir / f"chat_{conv_id}")

        try:
            async with SessionWriteLock(lock_path):
                log(f"Send to {conv_id}: {message[:50]}... (turn {conv.turn_count + 1})")
                response = await run_sync(conv.send, message)

            output_lines = [
                "# Chat Response\n",
                f"**Conversation**: `{conv_id}` (turn {conv.turn_count})",
                f"**Model**: {response.model}",
                "",
                "## Response\n",
                response.text,
            ]

            log(f"Chat {conv_id} turn {conv.turn_count}: {len(response.text)} chars")
            return [TextContent(type="text", text="\n".join(output_lines))]

        except TimeoutError as e:
            log(f"Send chat lock timeout ({conv_id}): {e}")
            return [TextContent(type="text", text=f"Error: conversation '{conv_id}' is locked by another request. Please wait and try again.")]
        except Exception as e:  # noqa: BLE001
            log(f"Send chat error ({conv_id}): {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "close_chat":
        conv_id = arguments.get("conversation_id", "")

        if not conv_id:
            return [TextContent(type="text", text="Error: conversation_id is required")]

        conv = _conversations.pop(conv_id, None)
        if conv is None:
            return [TextContent(
                type="text",
                text=f"Error: conversation '{conv_id}' not found.",
            )]

        turns = conv.turn_count
        conv.close()
        log(f"Closed conversation {conv_id} ({turns} turns)")
        return [TextContent(
            type="text",
            text=f"Chat `{conv_id}` closed ({turns} turns completed).",
        )]

    elif name == "cortex_quota":
        try:
            account = arguments.get("account", "default")
            svc = get_service()
            quota_data = await run_sync(svc.quota, account=account)
            quota = quota_data.get("cortex", {})

            output_lines = ["# Gemini Quota\n"]
            output_lines.append("| Model | Remaining | Reset |")
            output_lines.append("|:------|----------:|:------|")
            for bucket in quota.get("buckets", []):
                model = bucket.get("modelId", "?")
                remaining = bucket.get("remainingFraction", 0)
                reset = bucket.get("resetTime", "?")[:16]
                output_lines.append(
                    f"| `{model}` | {remaining*100:.1f}% | {reset} |"
                )

            # Chat session info (F8)
            if _conversations:
                output_lines.append("")
                output_lines.append("## Active Chat Sessions")
                output_lines.append(f"**{len(_conversations)}/{_MAX_CONVERSATIONS}** sessions active")
                total_turns = 0
                for cid, conv in _conversations.items():
                    try:
                        turns = conv.turn_count  # type: ignore[union-attr]
                        total_turns += turns
                        output_lines.append(f"- `{cid[:8]}…`: {turns} turns")
                    except AttributeError:
                        output_lines.append(f"- `{cid[:8]}…`: (unknown)")
                output_lines.append(f"\n**Total turns**: {total_turns}")

            # Token health (F5)
            token_health = quota_data.get("token_health")
            if token_health and token_health.get("accounts"):
                output_lines.append("")
                output_lines.append("## Token Health")
                for acct_name, info in token_health["accounts"].items():
                    if info.get("cached"):
                        ttl = info.get("ttl_seconds", 0)
                        healthy = "✅" if info.get("healthy") else "⚠️"
                        output_lines.append(
                            f"- `{acct_name}`: {healthy} TTL={ttl}s"
                        )
                    else:
                        output_lines.append(
                            f"- `{acct_name}`: 🔘 not cached"
                        )

            log(f"Quota returned: {len(quota.get('buckets', []))} buckets")
            return [TextContent(type="text", text="\n".join(output_lines))]

        except Exception as e:  # noqa: BLE001
            log(f"Cortex quota error: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "status":
        try:
            svc = get_service()
            svc_status = await run_sync(svc.status)

            output_lines = ["# Ochēma Status\n"]
            output_lines.append(f"- **Cortex**: {'✓' if svc_status.get('cortex_available') else '✗'}")

            tc = svc_status.get("token_cache")
            if tc:
                output_lines.append(f"- **Token TTL**: {tc.get('remaining_human', 'N/A')}")

            log("Status returned")
            return [TextContent(type="text", text="\n".join(output_lines))]

        except Exception as e:  # noqa: BLE001
            log(f"Status error: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "models":
        try:
            svc = get_service()
            model_data = await run_sync(svc.models)

            output_lines = ["# Available Models\n"]
            models = model_data.get("models", {})
            output_lines.append("| Model | Display Name |")
            output_lines.append("|:------|:-------------|")
            for mid, display in models.items():
                output_lines.append(f"| `{mid}` | {display} |")

            output_lines.append(f"\n**Default**: `{model_data.get('default', 'N/A')}`")
            output_lines.append(f"**Cortex**: {'✓' if model_data.get('cortex_available') else '✗'}")

            log(f"Models listed: {len(models)}")
            return [TextContent(type="text", text="\n".join(output_lines))]

        except Exception as e:  # noqa: BLE001
            log(f"Models error: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "session_info":
        try:
            conv_id = arguments.get("conversation_id")

            if not _conversations:
                return [TextContent(type="text", text="活動中のチャットセッションはありません。start_chat で開始してください。")]

            if conv_id and conv_id in _conversations:
                conv = _conversations[conv_id]
                turns = getattr(conv, 'turn_count', 0)
                rot_level = (
                    "🔴 CRITICAL" if turns > 50
                    else "🟡 WARNING" if turns > 30
                    else "🟢 HEALTHY"
                )
                output_lines = [
                    "# Session Info\n",
                    f"- **ID**: `{conv_id}`",
                    f"- **Turns**: {turns}",
                    f"- **Context Rot**: {rot_level}",
                ]
            else:
                output_lines = [
                    f"# Chat Sessions ({len(_conversations)} active)\n",
                    "| ID | Turns | Rot Risk |",
                    "|:---|------:|:--------|",
                ]
                for cid, conv in _conversations.items():
                    turns = getattr(conv, 'turn_count', 0)
                    rot = (
                        "🔴" if turns > 50
                        else "🟡" if turns > 30
                        else "🟢"
                    )
                    output_lines.append(f"| `{cid}` | {turns} | {rot} |")

            log(f"Session info: {len(_conversations)} chats")
            return [TextContent(type="text", text="\n".join(output_lines))]

        except Exception as e:  # noqa: BLE001
            log(f"Session info error: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "ask_with_tools":
        message = arguments.get("message", "")
        model = arguments.get("model", "gemini-3.1-pro-preview")
        system_instruction = arguments.get("system_instruction")
        thinking_budget = arguments.get("thinking_budget", 32768)
        max_iterations = int(arguments.get("max_iterations", 10))
        max_tokens = int(arguments.get("max_tokens", 65536))
        timeout = float(arguments.get("timeout", 120))
        account = arguments.get("account", "default")

        if not message:
            return [TextContent(type="text", text="Error: message is required")]

        try:
            svc = get_service()
            log(f"Tool use: model={model} account={account}: {message[:50]}...")

            # Convert thinking_budget to int if provided
            tb = int(thinking_budget) if thinking_budget is not None else None

            response = await run_sync(
                svc.ask_with_tools,
                message=message,
                model=model,
                system_instruction=system_instruction,
                max_iterations=max_iterations,
                max_tokens=max_tokens,
                thinking_budget=tb,
                timeout=timeout,
                account=account,
            )

            output_lines = [
                "# Tool Use Response (AI + Local Tools)\n",
                f"**Model**: {response.model}",
            ]

            if response.token_usage:
                usage = response.token_usage
                output_lines.append(
                    f"**Tokens**: {usage.get('prompt_tokens', 0)} → "
                    f"{usage.get('completion_tokens', 0)} "
                    f"(total: {usage.get('total_tokens', 0)})"
                )

            output_lines.extend(["", "## Response\n", response.text])

            if response.thinking:
                output_lines.extend(["", "## Thinking\n", response.thinking[:1000]])

            # Shadow Gemini: 記録 + ピギーバック
            shadow = get_shadow()
            shadow.record(
                backend="ochema",
                tool_name="ask_with_tools",
                summary=message,
                result_preview=response.text,
                reasoning=f"Tool Use ({response.model}). Claude の質問: {message}",
            )
            shadow_result = await shadow.maybe_shadow()
            if shadow_result:
                output_lines.append(shadow.format_piggyback(shadow_result))

            log(f"Tool use response: {len(response.text)} chars")
            return [TextContent(type="text", text="\n".join(output_lines))]

        except Exception as e:  # noqa: BLE001
            detail = str(e)
            if hasattr(e, "response_body") and e.response_body:
                detail += f"\n\nAPI Response:\n{e.response_body[:1000]}"
            log(f"Tool use error: {detail}")
            return [TextContent(type="text", text=f"Error: {detail}")]

    # ============ Context Rot (V-003) ============
    elif name == "context_rot_status":
        try:
            from mekhane.mcp.context_rot import context_rot_status as _cr_status
            cascade_id = arguments.get("cascade_id", "")
            result = await _cr_status(cascade_id=cascade_id)
            import json
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        except Exception as e:  # noqa: BLE001
            log(f"context_rot_status error: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    elif name == "context_rot_distill":
        try:
            from mekhane.mcp.context_rot import context_rot_distill as _cr_distill
            result = await _cr_distill(
                cascade_id=arguments.get("cascade_id", ""),
                topic=arguments.get("topic", ""),
                depth=arguments.get("depth", "L3"),
                context=arguments.get("context", ""),
            )
            # ★ Phase 3B: ROM → CAG Bridge
            # ROM 蒸留成功時に CAG キャッシュも更新 (Auto-Routing で自動活用される)
            rom_text = result.get("context", "") or arguments.get("context", "")
            if rom_text and len(rom_text) > 500:
                try:
                    from mekhane.ochema.cortex_cache import get_cache
                    _rom_cache = get_cache()
                    _rom_topic = arguments.get("topic", "session")[:20]
                    _rom_ci = _rom_cache.create_cache(
                        contents=rom_text,
                        display_name=f"hgk-rom-{_rom_topic}",
                        ttl=3600,
                    )
                    if _rom_ci:
                        result["cag_cache"] = _rom_ci.name
                        log(f"ROM→CAG Bridge: {_rom_ci.name}")
                except Exception as _rom_err:  # noqa: BLE001
                    log(f"ROM→CAG error (non-blocking): {_rom_err}")
            import json
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        except Exception as e:  # noqa: BLE001
            log(f"context_rot_distill error: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # ============ Task Planner (Φ0.5-Code) ============
    elif name == "ochema_plan_task":
        return await _handle_plan_task(arguments)

    # ============ CAG: Context Caching (PoC) ============
    elif name == "cache_boot_context":
        text = arguments.get("text", "")
        system_instruction = arguments.get("system_instruction", "")
        ttl = int(arguments.get("ttl", 3600))

        if not text:
            return [TextContent(type="text", text="Error: text is required")]

        try:
            from mekhane.ochema.cortex_cache import get_cache
            ctx_cache = get_cache()

            if not ctx_cache.is_available:
                return [TextContent(type="text", text="Error: GEMINI_API_KEY が未設定。キャッシュ機能を利用するには環境変数に設定してください。")]

            log(f"Cache boot context: {len(text)} chars, ttl={ttl}")
            info = await run_sync(
                ctx_cache.get_or_create_boot_cache,
                text,
                system_instruction=system_instruction,
                ttl=ttl,
            )
            health = ctx_cache.cache_health()

            import json
            result = {
                "cache_name": info.name,
                "display_name": info.display_name,
                "token_count": info.token_count,
                "content_hash": info.content_hash,
                "model": info.model,
                "cache_health": health,
                "usage": f"ask_cortex の cached_content パラメータに '{info.name}' を指定して使用",
            }
            log(f"Cache created: {info.name} ({info.token_count} tokens)")
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        except Exception as e:  # noqa: BLE001
            log(f"Cache boot context error: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    # ============ Shadow Gemini (S-003) ============
    elif name == "shadow_status":
        try:
            shadow = get_shadow()
            enabled_arg = arguments.get("enabled")
            if enabled_arg is not None:
                shadow.enabled = bool(enabled_arg)
                log(f"Shadow Gemini {'enabled' if shadow.enabled else 'disabled'}")
            import json
            stats = shadow.stats()
            return [TextContent(type="text", text=json.dumps(stats, ensure_ascii=False, indent=2))]
        except Exception as e:  # noqa: BLE001
            log(f"Shadow status error: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ============ Task Planner Handler (Φ0.5-Code) ============

# PURPOSE: [L2-auto] _handle_plan_task の非同期処理定義
async def _handle_plan_task(arguments: dict) -> list[TextContent]:
    """Handle ochema_plan_task: decompose code change into parallel sub-tasks."""
    try:
        from mekhane.ochema.task_planner import (
            decompose_code_task,
            format_plan_summary,
            format_batch_tasks,
        )

        prompt = arguments.get("prompt", "")
        repo = arguments.get("repo", "")
        branch = arguments.get("branch", "main")
        max_subtasks = int(arguments.get("max_subtasks", 5))

        if not prompt or not repo:
            return [TextContent(type="text", text="Error: prompt and repo are required")]

        log(f"Plan task: {prompt[:80]}... (repo={repo})")

        plan = await decompose_code_task(
            prompt=prompt,
            repo=repo,
            branch=branch,
            max_subtasks=max_subtasks,
        )

        output_lines = [format_plan_summary(plan)]

        # Show Jules-ready batch format for each wave
        if plan.is_compound and plan.parallel_groups:
            output_lines.append("\n---\n### Jules Batch Format\n")
            for wave_idx in range(len(plan.parallel_groups)):
                batch = format_batch_tasks(plan, group_index=wave_idx)
                output_lines.append(f"**Wave {wave_idx + 1}** ({len(batch)} tasks):")
                output_lines.append(f"```json\n{batch}\n```\n")

        log(f"Plan complete: {len(plan.subtasks)} subtasks, {len(plan.parallel_groups)} waves")
        return [TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:  # noqa: BLE001
        log(f"Plan task error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]





# ============ F3: Token Warmup Background Task ============

async def _token_warmup():
    """Pre-refresh OAuth tokens before TTL expires.

    Runs every 45 minutes (TTL is 55 min), refreshing tokens for all
    TokenVault accounts in a worker thread to prevent blocking.
    This eliminates the "surprise token refresh" that was the trigger
    for asyncio event loop blocking → IDE EOF disconnect.
    """
    await asyncio.sleep(60)  # Initial delay: let server stabilize
    while True:
        try:
            svc = get_service()
            # Warm up tokens in background thread
            await run_sync(_do_token_warmup, svc)
        except Exception as e:  # noqa: BLE001
            log(f"Token warmup error (non-fatal): {e}")
        await asyncio.sleep(2700)  # 45 minutes

def _do_token_warmup(svc):
    """Synchronous token warmup — runs in worker thread."""
    try:
        from mekhane.ochema.token_vault import TokenVault
        vault = TokenVault()
        accounts = vault.list_accounts()
        refreshed = 0
        for acct in accounts:
            try:
                vault.get_token(acct["name"])
                refreshed += 1
            except Exception as e:  # noqa: BLE001
                log(f"Token warmup failed for {acct['name']}: {e}")
        log(f"Token warmup: {refreshed}/{len(accounts)} accounts refreshed")
    except Exception as e:  # noqa: BLE001
        log(f"Token warmup setup error: {e}")

_base.register_background_task(_token_warmup)




if __name__ == "__main__":
    _base.install_all_hooks()
    _base.run()
