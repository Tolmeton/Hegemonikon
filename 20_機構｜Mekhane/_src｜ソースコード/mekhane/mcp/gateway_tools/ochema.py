# PROOF: mekhane/mcp/gateway_tools/ochema.py
# PURPOSE: mcp モジュールの ochema
"""Gateway tools: ochema domain."""
import time
from mekhane.ochema.model_defaults import FLASH
from mekhane.symploke.handoff_files import list_handoff_files


def register_ochema_tools(mcp):
    """Register ochema domain tools (9 tools)."""
    from mekhane.mcp.gateway_tools._utils import _traced, _get_policy, _trace_tool_call, _GATEWAY_URL, HANDOFF_DIR, _ask_timestamps, _ASK_RATE_LIMIT, _ASK_RATE_WINDOW, _chat_sessions, _MAX_CHAT_SESSIONS

    # PURPOSE: [L2-auto] レートリミットチェック。True = 許可、False = 拒否。


    # PURPOSE: [L2-auto] _check_rate_limit の関数定義
    def _check_rate_limit() -> bool:
        """レートリミットチェック。True = 許可、False = 拒否。"""
        now = time.time()
        _ask_timestamps[:] = [t for t in _ask_timestamps if now - t < _ASK_RATE_WINDOW]
        if len(_ask_timestamps) >= _ASK_RATE_LIMIT:
            return False
        _ask_timestamps.append(now)
        return True
    # PURPOSE: セッション一覧を取得する (IDE セッション or Handoff 履歴)
    @mcp.tool()
    @_traced
    def hgk_sessions() -> str:
        """
        セッション一覧を取得する。

        IDE (Language Server) が接続されている場合は IDE セッション (cascade) 一覧を返す。
        接続されていない場合は Mneme の Handoff 履歴にフォールバックする。
        """
        return _sessions_from_handoffs()
    # PURPOSE: [L2-auto] _sessions_from_handoffs の関数定義
    def _sessions_from_handoffs() -> str:
        """Mneme の Handoff ファイルからセッション履歴を構築する。"""
        if not HANDOFF_DIR.exists():
            return "📭 セッション情報がありません (IDE 未接続 + Handoff なし)"

        handoffs = list_handoff_files(HANDOFF_DIR)

        if not handoffs:
            return "📭 セッション情報がありません (IDE 未接続 + Handoff なし)"

        # 最新 10 件を表示
        handoffs = handoffs[:10]

        lines = [
            f"## 📋 セッション履歴 (Handoff — {len(handoffs)} 件)\n",
            "> ⚪ IDE 未接続のため Handoff ファイルから表示\n",
        ]

        for h in handoffs:
            try:
                content = h.read_text(encoding="utf-8", errors="replace")
                # タイトル行 (最初の # で始まる行) を抽出
                title = "(タイトル不明)"
                for line in content.split("\n"):
                    if line.startswith("# "):
                        title = line[2:].strip()[:60]
                        break

                from datetime import datetime, timezone
                mtime = datetime.fromtimestamp(h.stat().st_mtime, tz=timezone.utc)
                size_kb = h.stat().st_size / 1024

                lines.append(
                    f"- 📝 **{title}**\n"
                    f"  `{h.name}` | {size_kb:.1f}KB | {mtime.strftime('%m/%d %H:%M')} UTC"
                )
            except Exception:  # noqa: BLE001
                lines.append(f"- ⚠️ `{h.name}` (読取エラー)")

        return "\n".join(lines)
    # PURPOSE: IDE セッションの会話内容を読み取る
    @mcp.tool()
    @_traced
    def hgk_session_read(
        cascade_id: str,
        max_turns: int = 10,
        full: bool = False,
    ) -> str:
        """
        IDE セッションの会話内容を読み取る。

        user/assistant/tool の全ターンを時系列で返す。
        claude.ai ↔ IDE のセッション同期に使用する。

        Args:
            cascade_id: セッションの cascade_id (hgk_sessions で取得)
            max_turns: 返す最大ターン数 (デフォルト: 10)
            full: True → フル取得 (上限 30000 文字)
        """
        return "❌ hgk_session_read は廃止されました。Handoff ファイル (hgk_handoff_read) を参照してください。"
    # PURPOSE: LLM にメッセージを送り応答を取得する (Cortex API 経由)
    @mcp.tool()
    @_traced
    def hgk_ask(
        message: str,
        model: str = FLASH,
        timeout: int = 120,
    ) -> str:
        """
        LLM にメッセージを送り応答を取得する。

        Cortex API 経由で Claude/Gemini を直接呼び出す。

        Args:
            message: LLM に送るメッセージ (最大 5000 文字)
            model: 使用モデル (デフォルト: Gemini 2.0 Flash)
            timeout: タイムアウト秒数 (最大 300)
        """
        # [C-3] Input validation
        if not message or not message.strip():
            return "❌ メッセージが空です"
        if len(message) > 5000:
            return f"❌ メッセージが長すぎます ({len(message)} 文字、上限 5000)"
        timeout = max(10, min(300, timeout))

        # Rate limit
        if not _check_rate_limit():
            return "⚠️ レートリミット超過 (5 回/分)。少し待ってから再試行してください。"

        try:
            # OchemaService 経由 (Cortex 直接)
            from mekhane.ochema.service import OchemaService

            svc = OchemaService.get()
            response = svc.ask(message, model=model, timeout=float(timeout))

            result = f"## 🤖 LLM 応答\n\n**モデル**: `{response.model}`\n\n---\n\n{response.text}"

            if response.thinking:
                result += f"\n\n---\n\n<details><summary>💭 思考プロセス</summary>\n\n{response.thinking[:2000]}\n\n</details>"

            # W12 Token Explosion 対策
            if len(result) > 8000:
                result = result[:8000] + "\n\n... (出力が 8000 文字を超えたため切り詰めました)"

            return result
        except Exception as e:  # noqa: BLE001
            return f"❌ LLM エラー: {e}"
    # PURPOSE: 利用可能な LLM モデル一覧を取得する
    @mcp.tool()
    @_traced
    def hgk_models() -> str:
        """
        利用可能な LLM モデル一覧を取得する。
        Cortex API + LS の両方からモデル情報を統合して返す。
        IDE 未起動でも Cortex 経由のモデル一覧は取得可能。
        """
        try:
            from mekhane.ochema.service import OchemaService

            svc = OchemaService.get()
            info = svc.models()  # Cortex 統合

            all_models = info.get("models", {})
            if not all_models:
                return "📭 モデル情報を取得できませんでした"

            cortex_ok = info.get("cortex_available", False)

            lines = ["## 🤖 利用可能モデル\n"]
            lines.append(f"- **Cortex API**: {'✅' if cortex_ok else '❌'}\n")

            lines.append("| モデル | 表示名 |")
            lines.append("|:-------|:-------|")
            for model_id, display_name in sorted(all_models.items()):
                lines.append(f"| `{model_id}` | {display_name} |")

            return "\n".join(lines)
        except Exception as e:  # noqa: BLE001
            return f"❌ エラー: {e}"
    # PURPOSE: Cortex API の接続状況を確認する
    @mcp.tool()
    @_traced
    def hgk_ochema_status() -> str:
        """
        Cortex API の接続状況を確認する。
        """
        try:
            from mekhane.ochema.service import OchemaService

            svc = OchemaService.get()
            st = svc.status()

            cortex_ok = st.get("cortex_available", False)
            result = f"""## 🔌 Ochēma ステータス\n\n**Cortex API**: {'✅ 接続済み' if cortex_ok else '❌ 未接続'}"""

            tc = st.get("token_cache")
            if tc:
                result += f"\n**トークンキャッシュ**: {tc.get('remaining_human', 'N/A')}"

            return result
        except Exception as e:  # noqa: BLE001
            return f"❌ エラー: {e}"
    @mcp.tool()
    def hgk_ask_with_tools(
        message: str,
        model: str = "gemini-3.1-pro-preview",
        system_instruction: str = "",
        thinking_budget: int = 32768,
        max_iterations: int = 10,
        max_tokens: int = 65536,
        timeout: int = 120,
    ) -> str:
        """
        ツール付きで LLM にメッセージを送る (エージェントループ)。

        LLM がローカルファイルの読み書き、テキスト検索、ディレクトリ一覧、
        シェルコマンド実行を自律的に行い、結果を返す。
        コード分析・デバッグ・調査に最適。

        Args:
            message: LLM に送るメッセージ (最大 10000 文字)
            model: 使用モデル (デフォルト: gemini-3.1-pro-preview)
            system_instruction: システムプロンプト (省略可)
            thinking_budget: 思考トークン予算 (0-32768)
            max_iterations: 最大ツール呼び出しラウンド数 (デフォルト: 10)
            max_tokens: 最大出力トークン数 (デフォルト: 8192)
            timeout: API 呼び出しごとのタイムアウト秒数 (最大 300)
        """
        _start = time.time()

        if not message or not message.strip():
            _trace_tool_call("hgk_ask_with_tools", 0, (time.time() - _start) * 1000, False)
            return "❌ メッセージが空です"
        if len(message) > 10000:
            _trace_tool_call("hgk_ask_with_tools", len(message), (time.time() - _start) * 1000, False)
            return f"❌ メッセージが長すぎます ({len(message)} 文字、上限 10000)"

        if not _check_rate_limit():
            return "⚠️ レートリミット超過 (5 回/分)。少し待ってから再試行してください。"

        timeout = max(10, min(300, timeout))
        max_iterations = max(1, min(20, max_iterations))

        try:
            from mekhane.ochema.service import OchemaService

            svc = OchemaService.get()
            response = svc.ask_with_tools(
                message=message,
                model=model,
                system_instruction=system_instruction or None,
                max_iterations=max_iterations,
                max_tokens=max_tokens,
                thinking_budget=int(thinking_budget) if thinking_budget else None,
                timeout=float(timeout),
            )

            result = f"## 🔧 ツール付き LLM 応答\n\n**モデル**: `{response.model}`\n"

            if response.token_usage:
                usage = response.token_usage
                result += (
                    f"**トークン**: {usage.get('prompt_tokens', 0)} → "
                    f"{usage.get('completion_tokens', 0)} "
                    f"(合計: {usage.get('total_tokens', 0)})\n"
                )

            result += f"\n---\n\n{response.text}"

            if response.thinking:
                result += f"\n\n---\n\n<details><summary>💭 思考プロセス</summary>\n\n{response.thinking[:2000]}\n\n</details>"

            # W12 Token Explosion 対策
            if len(result) > 12000:
                result = result[:12000] + "\n\n... (出力が 12000 文字を超えたため切り詰めました)"

            _trace_tool_call("hgk_ask_with_tools", len(message), (time.time() - _start) * 1000, True)
            return result
        except Exception as e:  # noqa: BLE001
            _trace_tool_call("hgk_ask_with_tools", len(message), (time.time() - _start) * 1000, False)
            return f"❌ エラー: {e}"
    @mcp.tool()
    def hgk_chat_start(model: str = "") -> str:
        """
        ステートフルな多ターンチャットを開始する。
        返される会話 ID を hgk_chat_send で使う。

        Args:
            model: モデル設定 ID (省略時: サーバーデフォルト)
        """
        import uuid
        _start = time.time()

        try:
            # Evict oldest if full
            if len(_chat_sessions) >= _MAX_CHAT_SESSIONS:
                oldest_id = next(iter(_chat_sessions))
                old_conv = _chat_sessions.pop(oldest_id)
                if hasattr(old_conv, 'close'):
                    old_conv.close()

            from mekhane.ochema.service import OchemaService

            svc = OchemaService.get()
            conv = svc.start_chat(model=model)
            conv_id = str(uuid.uuid4())[:8]
            _chat_sessions[conv_id] = conv

            _trace_tool_call("hgk_chat_start", 0, (time.time() - _start) * 1000, True)
            return (
                f"## 💬 チャット開始\n\n"
                f"**会話 ID**: `{conv_id}`\n"
                f"**セッション数**: {len(_chat_sessions)}/{_MAX_CHAT_SESSIONS}\n\n"
                f"`hgk_chat_send` でメッセージを送信してください。\n"
                f"`hgk_chat_close` で終了できます。"
            )
        except Exception as e:  # noqa: BLE001
            _trace_tool_call("hgk_chat_start", 0, (time.time() - _start) * 1000, False)
            return f"❌ エラー: {e}"
    @mcp.tool()
    def hgk_chat_send(conversation_id: str, message: str) -> str:
        """
        既存のチャットにメッセージを送信する。

        Args:
            conversation_id: hgk_chat_start で返された会話 ID
            message: 送信するメッセージ
        """
        _start = time.time()

        if not conversation_id or not message:
            _trace_tool_call("hgk_chat_send", 0, (time.time() - _start) * 1000, False)
            return "❌ エラー: conversation_id と message は必須です"

        conv = _chat_sessions.get(conversation_id)
        if conv is None:
            _trace_tool_call("hgk_chat_send", 0, (time.time() - _start) * 1000, False)
            return f"❌ 会話 '{conversation_id}' が見つかりません。hgk_chat_start で開始してください。"

        if not _check_rate_limit():
            return "⚠️ レートリミット超過 (5 回/分)。少し待ってから再試行してください。"

        try:
            response = conv.send(message)
            turn_count = getattr(conv, 'turn_count', '?')

            result = (
                f"## 💬 チャット応答\n\n"
                f"**会話**: `{conversation_id}` (ターン {turn_count})\n"
                f"**モデル**: `{response.model}`\n\n"
                f"---\n\n{response.text}"
            )

            if len(result) > 8000:
                result = result[:8000] + "\n\n... (切り詰め)"

            _trace_tool_call("hgk_chat_send", len(message), (time.time() - _start) * 1000, True)
            return result
        except Exception as e:  # noqa: BLE001
            _trace_tool_call("hgk_chat_send", len(message), (time.time() - _start) * 1000, False)
            return f"❌ エラー: {e}"
    @mcp.tool()
    def hgk_chat_close(conversation_id: str) -> str:
        """
        チャットを終了し、リソースを解放する。

        Args:
            conversation_id: 終了する会話 ID
        """
        if not conversation_id:
            return "❌ エラー: conversation_id は必須です"

        conv = _chat_sessions.pop(conversation_id, None)
        if conv is None:
            return f"❌ 会話 '{conversation_id}' が見つかりません。"

        turns = getattr(conv, 'turn_count', 0)
        if hasattr(conv, 'close'):
            conv.close()

        return f"✅ チャット `{conversation_id}` を終了しました ({turns} ターン)。"
