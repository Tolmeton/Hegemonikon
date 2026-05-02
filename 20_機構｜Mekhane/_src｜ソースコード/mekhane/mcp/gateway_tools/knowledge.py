# PROOF: mekhane/mcp/gateway_tools/knowledge.py
# PURPOSE: mcp モジュールの knowledge
"""Gateway tools: knowledge domain."""
import time
import json
import os
import sys
from pathlib import Path
from datetime import datetime


def register_knowledge_tools(mcp):
    """Register knowledge domain tools (12 tools)."""
    from mekhane.mcp.gateway_tools._utils import _traced, _get_policy, _trace_tool_call, MNEME_DIR, SESSIONS_DIR, HANDOFF_DIR, DOXA_DIR, SOP_OUTPUT_DIR, IDEA_DIR, PROJECT_ROOT, POLICY, _GATEWAY_URL, INCOMING_DIR, PROCESSED_DIR, _MNEME_DIR, _COWORK_DIR, _COWORK_ARCHIVE, _COWORK_MAX_ACTIVE

    # =============================================================================
    # P1: /sop 調査依頼書テンプレート生成
    # =============================================================================

    # PURPOSE: hgk_gateway の hgk sop generate 処理を実行する
    @mcp.tool()
    @_traced
    def hgk_sop_generate(
        topic: str,
        decision: str = "",
        hypothesis: str = "",
    ) -> str:
        """
        /sop 調査依頼書テンプレートを生成する。

        Gemini Deep Research や Perplexity にコピペして使う。
        Hegemonikón /sop ワークフローのモバイル版。

        Args:
            topic: 調査対象のテーマ (例: "FEP と Active Inference の最新動向")
            decision: この調査の結果、何を決定するか
            hypothesis: 事前仮説 (あれば)
        """
        now = datetime.now().strftime("%Y-%m-%d")

        template = f"""# 調査依頼書（深掘り版）

    > テーマ: {topic}
    > 生成日: {now}
    > 生成元: HGK /sop (出張版)

    ---

    ## 出力形式

    以下の4列テーブルで構造化して回答してください：

    | 項目 | 値 | 根拠（出典） | URL |
    |:-----|:---|:-----------|:----|

    ---

    ## タスク定義

    {topic}について、以下の論点を**網羅的かつ最新の情報**に基づいて調査してください。

    ## 時間制約

    - **過去6ヶ月の情報を優先**
    - 2025年以降の論文・記事を重視

    ## 決定事項

    {decision if decision else "（調査結果に基づいて決定する）"}

    ## 仮説

    {hypothesis if hypothesis else "（仮説なし — 探索的調査）"}

    ---

    ## 論点（必須項目）

    A. {topic}の現状
    - A1: 最新の定義・分類はどうなっているか？
    - A2: 主要な研究グループ・実装は？
    - A3: 2025年以降の重要な変化・ブレイクスルーは？

    B. 実践・応用
    - B1: 現時点で最も有効な手法・ツールは？
    - B2: 成功事例と失敗事例は？
    - B3: コスト・実装の現実的な制約は？

    C. 将来展望
    - C1: 今後6-12ヶ月で予想される変化は？
    - C2: リスクや注意すべき点は？

    ---

    > この調査依頼書は Hegemonikón /sop ワークフロー (出張版) で生成されました。
    > Gemini Deep Research または Perplexity にコピペして実行してください。
    """

        # Save to file
        SOP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        safe_topic = topic[:30].replace("/", "_").replace(" ", "_")
        output_path = SOP_OUTPUT_DIR / f"sop_{safe_topic}_{now}.md"
        output_path.write_text(template, encoding="utf-8")

        return f"## ✅ 調査依頼書を生成しました\n\n保存先: `{output_path}`\n\n---\n\n{template}"
    # =============================================================================
    # P1: KI / Gnōsis 検索
    # =============================================================================

    # PURPOSE: hgk_gateway の hgk search 処理を実行する (→ hgk_pks_search への薄いラッパー)
    @mcp.tool()
    @_traced
    def hgk_search(query: str, max_results: int = 5, mode: str = "hybrid") -> str:
        """
        HGK の知識ベース (KI / Gnōsis / Sophia) を検索する。
        内部的には hgk_pks_search に転送される (後方互換用ラッパー)。

        Args:
            query: 検索クエリ (例: "FEP 精度加重", "認知バイアス")
            max_results: 最大結果数
            mode: 検索モード (旧パラメータ、現在は無視)
        """
        return hgk_pks_search(query=query, k=max_results, sources="")
    # =============================================================================
    # P2: Doxa 読み取り
    # =============================================================================

    # PURPOSE: hgk_gateway の hgk doxa read 処理を実行する
    @mcp.tool()
    @_traced
    def hgk_doxa_read() -> str:
        """
        Doxa (信念ストア) の内容を一覧表示する。
        HGK で蓄積された法則・教訓・信念を参照する。
        """
        if not DOXA_DIR.exists():
            return "## ⚠️ Doxa ディレクトリが見つかりません"

        # Artifacts are stored as UUID subdirs with .metadata.json files
        meta_files = sorted(DOXA_DIR.glob("*/*.metadata.json"), reverse=True)
        if not meta_files:
            return "## 📭 Doxa は空です"

        lines = [f"## 💡 Doxa (成果物ストア) — {len(meta_files)} 件\n"]
        # Show most recent 20 entries to avoid overwhelming output
        for mf in meta_files[:20]:
            try:
                data = json.loads(mf.read_text(encoding="utf-8"))
                artifact_type = data.get("artifactType", "unknown").replace("ARTIFACT_TYPE_", "")
                summary = data.get("summary", "（要約なし）")
                updated = data.get("updatedAt", "?")[:10]
                lines.append(f"- **[{artifact_type}]** {summary[:120]} ({updated})")
            except Exception:  # noqa: BLE001
                lines.append(f"- ⚠️ {mf.parent.name}: 読み取りエラー")

        if len(meta_files) > 20:
            lines.append(f"\n... 他 {len(meta_files) - 20} 件")

        return "\n".join(lines)
    # =============================================================================
    # P3: Handoff 参照
    # =============================================================================

    # PURPOSE: hgk_gateway の hgk handoff read 処理を実行する
    @mcp.tool()
    @_traced
    def hgk_handoff_read(count: int = 1) -> str:
        """
        最新の Handoff (セッション引き継ぎ書) を読む。
        前回のセッションで何をしたか、次に何をすべきかを確認する。

        Args:
            count: 読む Handoff の数 (デフォルト: 1)
        """
        if not HANDOFF_DIR.exists():
            return "## ⚠️ Handoff ディレクトリが見つかりません"

        handoffs = sorted(HANDOFF_DIR.glob("**/handoff_*.md"), reverse=True)
        if not handoffs:
            return "## 📭 Handoff がありません"

        lines = [f"## 📋 最新 Handoff ({min(count, len(handoffs))}/{len(handoffs)} 件)\n"]

        for hf in handoffs[:count]:
            try:
                content = hf.read_text(encoding="utf-8")
                # First 50 lines
                summary = "\n".join(content.split("\n")[:50])
                lines.append(f"### {hf.stem}\n\n{summary}\n\n---")
            except Exception:  # noqa: BLE001
                lines.append(f"### {hf.stem}\n\n⚠️ 読み取りエラー")

        return "\n".join(lines)
    # =============================================================================
    # P3: アイデアメモ保存
    # =============================================================================

    # PURPOSE: hgk_gateway の hgk idea capture 処理を実行する
    @mcp.tool()
    def hgk_idea_capture(idea: str, tags: str = "") -> str:
        """
        アイデアメモを保存する。外出先での閃きを逃さない。
        次回 /boot で自動的に読み込まれる。

        Args:
            idea: アイデアの内容 (最大10,000文字)
            tags: タグ (カンマ区切り、例: "FEP, 設計, 実験")
        """
        # [C-3] Content size limit (policy-driven)
        _start = time.time()
        MAX_IDEA_SIZE = _get_policy("hgk_idea_capture", "max_input_size", 10_000)
        if len(idea) > MAX_IDEA_SIZE:
            _trace_tool_call("hgk_idea_capture", len(idea), (time.time() - _start) * 1000, False)
            return f"❌ エラー: アイデアが長すぎます ({len(idea)} 文字)。上限は {MAX_IDEA_SIZE} 文字です。"
        IDEA_DIR.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        filename = f"idea_{now.strftime('%Y%m%d_%H%M%S')}.md"
        filepath = IDEA_DIR / filename

        content = f"""# 💡 アイデアメモ

    > **日時**: {now.strftime('%Y-%m-%d %H:%M:%S')}
    > **タグ**: {tags if tags else '未分類'}
    > **ソース**: HGK 出張版 (モバイル)

    ---

    {idea}

    ---

    *Captured via HGK Gateway*
    """
        filepath.write_text(content, encoding="utf-8")
        _trace_tool_call("hgk_idea_capture", len(idea), (time.time() - _start) * 1000, True)

        return f"## ✅ アイデア保存完了\n\n保存先: `{filepath}`\nタグ: {tags if tags else '未分類'}\n\n次回 `/boot` で自動的に確認されます。"
    # =============================================================================
    # HGK Status (ヘルスチェック)
    # =============================================================================

    # PURPOSE: hgk_gateway の hgk status 処理を実行する
    @mcp.tool()
    @_traced
    def hgk_status() -> str:
        """
        HGK システムの概要ステータスを表示する。
        モバイルから現在の状態を確認する。
        """
        status_items = []

        # Handoff count
        handoff_count = len(list(HANDOFF_DIR.glob("**/handoff_*.md"))) if HANDOFF_DIR.exists() else 0
        status_items.append(f"📋 Handoff: {handoff_count} 件")

        # KI count
        ki_base = Path.home() / ".gemini" / "antigravity" / "knowledge"
        ki_count = len([d for d in ki_base.iterdir() if d.is_dir()]) if ki_base.exists() else 0
        status_items.append(f"📚 KI: {ki_count} 件")

        # Doxa (artifacts) count
        doxa_count = len(list(DOXA_DIR.glob("*/*.metadata.json"))) if DOXA_DIR.exists() else 0
        status_items.append(f"💡 Doxa: {doxa_count} 件")

        # Ideas count
        idea_count = len(list(IDEA_DIR.glob("*.md"))) if IDEA_DIR.exists() else 0
        status_items.append(f"🌟 Ideas: {idea_count} 件")

        # Latest handoff
        if HANDOFF_DIR.exists():
            handoffs = sorted(HANDOFF_DIR.glob("**/handoff_*.md"), reverse=True)
            if handoffs:
                status_items.append(f"📅 最新 Handoff: `{handoffs[0].name}`")

        # Digestor status
        incoming_count = len(list(INCOMING_DIR.glob("eat_*.md"))) if INCOMING_DIR.exists() else 0
        processed_count = len(list(PROCESSED_DIR.glob("eat_*.md"))) if PROCESSED_DIR.exists() else 0
        status_items.append(f"\n### Digestor")
        status_items.append(f"📥 incoming: {incoming_count} 件")
        status_items.append(f"📦 processed: {processed_count} 件")

        try:
            from mekhane.ergasterion.digestor.state import get_status_summary
            status_items.append(get_status_summary())
        except Exception:  # noqa: BLE001
            status_items.append("🔄 Digestor: 状態不明")

        # Scheduler PID check
        pid_file = Path.home() / ".hegemonikon" / "digestor" / "scheduler.pid"
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                os.kill(pid, 0)  # Check if process exists
                status_items.append("⚡ Scheduler: 稼働中")
            except (ProcessLookupError, ValueError):
                status_items.append("💤 Scheduler: 停止中 (PID stale)")
        else:
            status_items.append("💤 Scheduler: 停止中")

        return f"## 🏠 HGK ステータス\n\n" + "\n".join(status_items)
    # =============================================================================
    # PKS: Knowledge Stats & Health (Autophōnos)
    # =============================================================================

    # PURPOSE: PKS 知識基盤の統計を表示する MCP ツール
    @mcp.tool()
    @_traced
    def hgk_pks_stats() -> str:
        """
        PKS (Proactive Knowledge Surface) の知識基盤統計を表示する。
        Gnōsis, Kairos, Sophia の各インデックスのドキュメント数と
        Handoff/KI ファイル数を返す。
        """
        import io, contextlib
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "mekhane.pks.pks_cli", "stats"],
                capture_output=True, text=True,
                cwd=str(PROJECT_ROOT),
                env={**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
                timeout=30,
            )
        return result.stdout if result.returncode == 0 else f"❌ Error: {result.stderr[:200]}"
    # PURPOSE: PKS ヘルスチェックを実行する MCP ツール
    @mcp.tool()
    @_traced
    def hgk_pks_health() -> str:
        """
        Autophōnos 全スタック (9コンポーネント) のヘルスチェックを実行する。
        Gnōsis, Kairos, Sophia, Embedder, GnosisBridge, PKSEngine,
        TopicExtractor, SelfAdvocate, Chronos の各コンポーネントの OK/FAIL を返す。
        """
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "mekhane.pks.pks_cli", "health"],
            capture_output=True, text=True,
            cwd=str(PROJECT_ROOT),
            env={**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
            timeout=60,
        )
        return result.stdout if result.returncode == 0 else f"❌ Error: {result.stderr[:200]}"
    # PURPOSE: PKS 全インデックス横断検索 MCP ツール
    @mcp.tool()
    @_traced
    def hgk_pks_search(query: str, k: int = 10, sources: str = "") -> str:
        """
        全知識基盤 (34K+ docs) を横断検索する(後方互換用)。
        Gnōsis, Kairos, Sophia, Chronos, Handoff を検索。

        Args:
            query: 検索クエリ (自然言語)
            k: 取得件数 (デフォルト: 10)
            sources: 検索ソースのカンマ区切り (例: "gnosis,chronos")。空=全ソース
        """
        from mekhane.symploke.search.search_factory import get_search_engine
        try:
            src_list = [s.strip() for s in sources.split(",")] if sources else ["gnosis", "sophia", "kairos", "handoff", "chronos"]
            engine, init_errors = get_search_engine(src_list)
            res = engine.search(query=query, k=k, sources=src_list)
            if not res:
                return f"🔍 `{query}` に一致する結果はありませんでした。"

            out = [f"## 🔍 PKS 横断検索結果: `{query}`\n\n**{len(res)} 件**\n"]
            for r in res:
                source = r.source.value if hasattr(r.source, "value") else str(r.source)
                title = r.metadata.get("title", "無題")
                score = r.score
                snippet = r.content[:200]
                out.append(f"[{source}] **{title}** (score: {score:.3f})\n{snippet}...")
            if init_errors:
                out.append(f"\n> ⚠️ 初期化失敗ソース: {', '.join(init_errors)}")
            return "\n\n".join(out)
        except Exception as e:  # noqa: BLE001
            import sys
            print(f"hgk_pks_search error: {e}", file=sys.stderr)
            return f"## ❌ エラー\n\n`{e}`"
    # =============================================================================
    # F8: Gateway Self-Diagnosis
    # =============================================================================

    # PURPOSE: [L2-auto] hgk_gateway_health の関数定義
    @mcp.tool()
    @_traced
    def hgk_gateway_health() -> str:
        """
        Gateway の自己診断を実行する。
        OAuth 設定、トークン永続化、登録クライアント、稼働時間を確認。
        """
        from datetime import timezone
        checks = []

        # 1. OAuth issuer URL
        checks.append(f"🔗 **Issuer URL**: `{_GATEWAY_URL}`")
        is_localhost = "localhost" in _GATEWAY_URL or "127.0.0.1" in _GATEWAY_URL
        if is_localhost:
            checks.append("  ⚠️ issuer が localhost — モバイルからの OAuth は失敗します")
        else:
            checks.append("  ✅ 外部アクセス可能な URL")

        # 2. Token persistence
        state_file = _MNEME_DIR / "gateway_oauth.json"
        if state_file.exists():
            size = state_file.stat().st_size
            mtime = datetime.fromtimestamp(state_file.stat().st_mtime, tz=timezone.utc)
            checks.append(f"💾 **OAuth State**: `gateway_oauth.json` ({size}B, updated {mtime.strftime('%Y-%m-%d %H:%M')} UTC)")
        else:
            checks.append("💾 **OAuth State**: ファイルなし (初回接続待ち)")

        # 3. Registered clients & tokens (lazy import to avoid reverse dependency)
        try:
            from mekhane.mcp.hgk_gateway import _oauth_provider
            if _oauth_provider:
                n_clients = len(_oauth_provider._clients)
                n_refresh = len(_oauth_provider._refresh_tokens)
                n_codes = len(_oauth_provider._auth_codes)
                checks.append(f"👥 **Clients**: {n_clients} 登録済み, {n_refresh} refresh tokens, {n_codes} active auth codes")
            else:
                checks.append("👥 **OAuth**: 無効 (GATEWAY_TOKEN 未設定)")
        except ImportError:
            checks.append("👥 **OAuth**: インポート不可")

        # 4. Policy
        checks.append(f"📋 **Policy**: v{POLICY.get('version', '?')} ({len(POLICY.get('tools', {}))} tools)")

        # 5. WBC alerts
        try:
            wbc_data = json.loads((_MNEME_DIR / "wbc_state.json").read_text("utf-8"))
            n_alerts = len(wbc_data.get("alerts", []))
            total = wbc_data.get("totalAlerts", 0)
            checks.append(f"🛡️ **WBC**: {n_alerts} active alerts (cumulative: {total})")
        except Exception:  # noqa: BLE001
            checks.append("🛡️ **WBC**: 読み取り不可")

        return "## 🏥 HGK Gateway Health\n\n" + "\n".join(checks)
    def _cowork_ensure_dirs() -> None:
        """Cowork ディレクトリを確保する。"""
        _COWORK_DIR.mkdir(parents=True, exist_ok=True)
        _COWORK_ARCHIVE.mkdir(parents=True, exist_ok=True)
    def _cowork_rotate() -> None:
        """最新 N 件を残し、古いファイルを _archive/ に移動する。"""
        files = sorted(_COWORK_DIR.glob("cowork_*.md"), key=lambda p: p.name)
        overflow = len(files) - _COWORK_MAX_ACTIVE
        if overflow > 0:
            for f in files[:overflow]:
                dest = _COWORK_ARCHIVE / f.name
                f.rename(dest)
    @mcp.tool()
    @_traced
    def hgk_cowork_save(
        summary: str,
        tasks: str = "",
        next_actions: str = "",
    ) -> str:
        """
        Cowork セッション活動をファイルに保存する。
        セッション終了前や長時間作業中の定期保存に使う。
        Creator（AuDHD）が「何をしていたか」を忘れないための記憶補完。

        Args:
            summary: 今やっていたことの要約 (1-3行)
            tasks: 進行中のタスクリスト (改行区切り)
            next_actions: 次にやるべきこと (改行区切り)
        """
        if not summary or not summary.strip():
            return "❌ summary は必須です"

        _cowork_ensure_dirs()

        now = datetime.now()
        filename = f"cowork_{now.strftime('%Y-%m-%d_%H%M')}.md"
        filepath = _COWORK_DIR / filename

        # Build markdown content
        lines = [
            f"# Cowork Session — {now.strftime('%Y-%m-%d %H:%M')}",
            "",
            "## 📋 やっていたこと",
            "",
            summary.strip(),
            "",
        ]

        if tasks and tasks.strip():
            lines.extend([
                "## ✅ タスク一覧",
                "",
            ])
            for task in tasks.strip().split("\n"):
                task = task.strip()
                if task:
                    # Preserve existing checkbox format or add one
                    if task.startswith("- [") or task.startswith("- "):
                        lines.append(task)
                    else:
                        lines.append(f"- {task}")
            lines.append("")

        if next_actions and next_actions.strip():
            lines.extend([
                "## ⏭️ 次にやること",
                "",
            ])
            for action in next_actions.strip().split("\n"):
                action = action.strip()
                if action:
                    lines.append(f"- {action}")
            lines.append("")

        lines.extend([
            "---",
            f"*保存: {now.strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
        ])

        filepath.write_text("\n".join(lines), encoding="utf-8")

        # Rotate old files
        _cowork_rotate()

        active_count = len(list(_COWORK_DIR.glob("cowork_*.md")))

        return (
            f"## ✅ Cowork 活動を保存しました\n\n"
            f"- **ファイル**: `{filename}`\n"
            f"- **保存先**: `cowork/`\n"
            f"- **アクティブ件数**: {active_count}/{_COWORK_MAX_ACTIVE}\n\n"
            f"次回 Cowork を開始したら `hgk_cowork_resume` で復元できます。"
        )
    @mcp.tool()
    @_traced
    def hgk_cowork_resume(count: int = 3) -> str:
        """
        直近の Cowork セッション活動を読み出す。
        セッション開始時に呼んで、Creator に「前回何をしていたか」を伝える。

        Args:
            count: 読み出す件数 (デフォルト: 3, 最大: 5)
        """
        _cowork_ensure_dirs()

        files = sorted(_COWORK_DIR.glob("cowork_*.md"), key=lambda p: p.name, reverse=True)

        if not files:
            return (
                "## 📭 Cowork 活動記録なし\n\n"
                "まだ保存された Cowork セッション記録がありません。\n"
                "作業中に `hgk_cowork_save` で活動を保存できます。"
            )

        count = max(1, min(count, _COWORK_MAX_ACTIVE))
        target_files = files[:count]

        lines = [
            f"## 🔄 Cowork セッション復元 ({len(target_files)} 件)",
            "",
        ]

        for i, f in enumerate(target_files, 1):
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                # Show a compact version
                lines.append(f"### [{i}] {f.stem.replace('cowork_', '')}")
                lines.append("")

                # Extract key sections
                current_section = None
                for line in content.split("\n"):
                    if line.startswith("## 📋"):
                        current_section = "summary"
                    elif line.startswith("## ✅"):
                        current_section = "tasks"
                    elif line.startswith("## ⏭️"):
                        current_section = "next"
                    elif line.startswith("---"):
                        current_section = None
                    elif line.startswith("# "):
                        continue  # Skip title
                    elif current_section and line.strip():
                        if current_section == "summary":
                            lines.append(f"**📋 要約**: {line.strip()}")
                        elif current_section == "tasks":
                            lines.append(f"  {line.strip()}")
                        elif current_section == "next":
                            text = line.strip().lstrip("- ")
                            lines.append(f"  ⏭️ {text}")

                lines.append("")
            except Exception as e:  # noqa: BLE001
                lines.append(f"### [{i}] {f.name} — ⚠️ 読取りエラー: {e}")
                lines.append("")

        archive_count = len(list(_COWORK_ARCHIVE.glob("cowork_*.md")))
        if archive_count > 0:
            lines.append(f"📁 アーカイブ: {archive_count} 件")

        return "\n".join(lines)
