# PROOF: mekhane/mcp/gateway_tools/jules.py
# PURPOSE: mcp モジュールの jules
"""Gateway tools: jules domain."""
import time
import os
import json


def register_jules_tools(mcp):
    """Register jules domain tools (4 tools)."""
    from mekhane.mcp.gateway_tools._utils import _traced, _get_policy, _trace_tool_call, _GATEWAY_URL

    def _jules_init_pool() -> None:
        """Load Jules API keys from environment (JULES_API_KEY_01 to JULES_API_KEY_18)."""
        global _jules_api_key_pool, _jules_dashboard
        for i in range(1, 19):
            key_name = f"JULES_API_KEY_{i:02d}"
            key = os.environ.get(key_name)
            if key:
                _jules_api_key_pool.append((i, key))
        print(f"[hgk-gateway] Jules API Key Pool: {len(_jules_api_key_pool)} keys loaded", file=sys.stderr)
        try:
            synergeia_path = str(PROJECT_ROOT / "synergeia")
            if synergeia_path not in sys.path:
                sys.path.insert(0, synergeia_path)
            from jules_dashboard import JulesDashboard
            _jules_dashboard = JulesDashboard()
        except ImportError:
            pass
    def _jules_get_key() -> tuple:
        """Get next Jules API key (load-balanced or round-robin)."""
        global _jules_api_key_index, _jules_dashboard
        if not _jules_api_key_pool:
            _jules_init_pool()
        if not _jules_api_key_pool:
            return None, 0
        if _jules_dashboard:
            try:
                _, best_idx = _jules_dashboard.get_best_account()
                for idx, key in _jules_api_key_pool:
                    if idx == best_idx:
                        return key, idx
            except Exception:  # noqa: BLE001
                pass
        idx, key = _jules_api_key_pool[_jules_api_key_index % len(_jules_api_key_pool)]
        _jules_api_key_index += 1
        return key, idx
    def _jules_record(key_index: int, session_id: str) -> None:
        """Record Jules usage to dashboard."""
        if _jules_dashboard:
            try:
                _jules_dashboard.record_usage(key_index, session_id)
            except Exception:  # noqa: BLE001
                pass
    @mcp.tool()
    def hgk_jules_create_task(
        prompt: str,
        repo: str,
        branch: str = "main",
    ) -> str:
        """
        Jules にコード生成タスクを送信する。
        コードの実装・修正・テスト生成などを Jules に委譲する。

        Args:
            prompt: タスクの説明 (例: "utils.py のバグを修正して")
            repo: リポジトリ (owner/repo 形式、例: "Tolmeton/Hegemonikon")
            branch: ブランチ名 (デフォルト: main)
        """
        import asyncio
        _start = time.time()

        if not prompt or not repo:
            _trace_tool_call("hgk_jules_create_task", 0, (time.time() - _start) * 1000, False)
            return "❌ エラー: prompt と repo は必須です"

        api_key, key_index = _jules_get_key()
        if not api_key:
            _trace_tool_call("hgk_jules_create_task", len(prompt), (time.time() - _start) * 1000, False)
            return "❌ エラー: JULES_API_KEY_XX 環境変数が設定されていません"

        try:
            from mekhane.symploke.jules_client import JulesClient

            client = JulesClient(api_key)
            source = f"sources/github/{repo}"
            session = asyncio.get_event_loop().run_until_complete(
                client.create_session(prompt, source, branch)
            )
            _jules_record(key_index, session.id)
            _trace_tool_call("hgk_jules_create_task", len(prompt), (time.time() - _start) * 1000, True)

            return (
                f"## ✅ Jules タスク作成完了\n\n"
                f"- **Session ID**: `{session.id}`\n"
                f"- **State**: {session.state.value}\n"
                f"- **Repository**: {repo}\n"
                f"- **Branch**: {branch}\n"
                f"- **Account**: Key #{key_index} (auto-balanced)\n\n"
                f"`hgk_jules_get_status` で進捗を確認してください。"
            )
        except Exception as e:  # noqa: BLE001
            _trace_tool_call("hgk_jules_create_task", len(prompt), (time.time() - _start) * 1000, False)
            return f"❌ エラー: {e}"
    @mcp.tool()
    def hgk_jules_get_status(session_id: str) -> str:
        """
        Jules セッションの進捗を確認する。

        Args:
            session_id: hgk_jules_create_task で返された Session ID
        """
        import asyncio
        _start = time.time()

        if not session_id:
            _trace_tool_call("hgk_jules_get_status", 0, (time.time() - _start) * 1000, False)
            return "❌ エラー: session_id は必須です"

        api_key, _ = _jules_get_key()
        if not api_key:
            _trace_tool_call("hgk_jules_get_status", 0, (time.time() - _start) * 1000, False)
            return "❌ エラー: JULES_API_KEY_XX 環境変数が設定されていません"

        try:
            from mekhane.symploke.jules_client import JulesClient

            client = JulesClient(api_key)
            session = asyncio.get_event_loop().run_until_complete(
                client.get_session(session_id)
            )
            emoji = {"planning": "📝", "implementing": "🔨", "testing": "🧪", "completed": "✅", "failed": "❌"}
            _trace_tool_call("hgk_jules_get_status", 0, (time.time() - _start) * 1000, True)

            output = (
                f"## Jules セッション状態\n\n"
                f"- **Session ID**: `{session.id}`\n"
                f"- **State**: {emoji.get(session.state.value, '❓')} {session.state.value}\n"
            )
            if session.pull_request_url:
                output += f"- **Pull Request**: {session.pull_request_url}\n"
            if session.error:
                output += f"- **Error**: {session.error}\n"
            return output
        except Exception as e:  # noqa: BLE001
            _trace_tool_call("hgk_jules_get_status", 0, (time.time() - _start) * 1000, False)
            return f"❌ エラー: {e}"
    @mcp.tool()
    def hgk_jules_list_repos() -> str:
        """
        Jules に接続されているリポジトリ一覧を表示する。
        """
        return (
            "## Jules リポジトリ\n\n"
            "リポジトリ一覧の自動取得は未実装です。\n"
            "`owner/repo` 形式で指定してください (例: `Tolmeton/Hegemonikon`)。"
        )
    @mcp.tool()
    def hgk_jules_batch_execute(
        tasks: str,
        max_concurrent: int = 30,
    ) -> str:
        """
        複数の Jules タスクを並列実行する。

        Args:
            tasks: JSON 形式のタスクリスト。各タスクは {"prompt": "...", "repo": "owner/repo"} 形式。
            max_concurrent: 最大並行数 (デフォルト: 30、最大: 60)
        """
        import asyncio
        _start = time.time()

        try:
            task_list = json.loads(tasks) if isinstance(tasks, str) else tasks
        except json.JSONDecodeError as e:
            _trace_tool_call("hgk_jules_batch_execute", len(str(tasks)), (time.time() - _start) * 1000, False)
            return f"❌ JSON パースエラー: {e}"

        if not task_list:
            _trace_tool_call("hgk_jules_batch_execute", 0, (time.time() - _start) * 1000, False)
            return "❌ エラー: タスクリストが空です"

        max_concurrent = min(max_concurrent, 60)

        api_key, _ = _jules_get_key()
        if not api_key:
            _trace_tool_call("hgk_jules_batch_execute", 0, (time.time() - _start) * 1000, False)
            return "❌ エラー: JULES_API_KEY_XX 環境変数が設定されていません"

        try:
            from mekhane.symploke.jules_client import JulesClient, SessionState

            client = JulesClient(api_key)
            formatted = [
                {"prompt": t["prompt"], "source": f"sources/github/{t['repo']}", "branch": t.get("branch", "main")}
                for t in task_list
            ]
            results = asyncio.get_event_loop().run_until_complete(
                client.batch_execute(formatted, max_concurrent)
            )

            completed = sum(1 for r in results if r.state == SessionState.COMPLETED)
            failed = sum(1 for r in results if r.state == SessionState.FAILED)

            lines = [
                f"## Jules バッチ結果\n",
                f"**合計**: {len(results)} タスク",
                f"- ✅ 完了: {completed}",
                f"- ❌ 失敗: {failed}\n",
            ]
            for i, r in enumerate(results, 1):
                emoji = "✅" if r.state == SessionState.COMPLETED else "❌"
                lines.append(f"### [{i}] {emoji} {r.prompt[:50]}...")
                if r.pull_request_url:
                    lines.append(f"- PR: {r.pull_request_url}")
                if r.error:
                    lines.append(f"- Error: {r.error}")
                lines.append("")

            _trace_tool_call("hgk_jules_batch_execute", len(str(tasks)), (time.time() - _start) * 1000, True)
            return "\n".join(lines)
        except Exception as e:  # noqa: BLE001
            _trace_tool_call("hgk_jules_batch_execute", len(str(tasks)), (time.time() - _start) * 1000, False)
            return f"❌ エラー: {e}"
