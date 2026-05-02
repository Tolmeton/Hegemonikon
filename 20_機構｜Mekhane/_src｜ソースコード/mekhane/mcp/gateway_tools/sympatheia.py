# PROOF: mekhane/mcp/gateway_tools/sympatheia.py
# PURPOSE: mcp モジュールの sympatheia
"""Gateway tools: sympatheia domain."""
import time
import json
import os
from pathlib import Path
from datetime import datetime
from mekhane.symploke.handoff_files import list_handoff_files


def register_sympatheia_tools(mcp):
    """Register sympatheia domain tools (12 tools)."""
    from mekhane.mcp.gateway_tools._utils import _traced, _get_policy, _trace_tool_call, MNEME_DIR, PROJECT_ROOT, _GATEWAY_URL, _MNEME_DIR, HANDOFF_DIR

    # =============================================================================
    # Sympatheia: システム健全性
    # =============================================================================

    # PURPOSE: HGK システムの健全性チェック (Sympatheia 読取り)
    @mcp.tool()
    @_traced
    def hgk_health() -> str:
        """
        HGK システムの詳細な健全性レポートを表示する。
        Heartbeat, WBC アラート, Health スコアを確認。
        """
        lines = ["## 🩺 HGK Health Report\n"]

        # 1. Heartbeat
        hb_file = _MNEME_DIR / "heartbeat.json"
        if hb_file.exists():
            try:
                hb = json.loads(hb_file.read_text("utf-8"))
                beats = hb.get("totalBeats", 0)
                last = hb.get("lastBeat", "不明")
                lines.append(f"### 💓 Heartbeat\n- **総拍動数**: {beats}\n- **最終拍動**: {last}\n")
            except Exception:  # noqa: BLE001
                lines.append("### 💓 Heartbeat\n- ⚠️ 読取りエラー\n")
        else:
            lines.append("### 💓 Heartbeat\n- 未検出\n")

        # 2. WBC Alerts
        wbc_file = _MNEME_DIR / "wbc_state.json"
        if wbc_file.exists():
            try:
                wbc = json.loads(wbc_file.read_text("utf-8"))
                total = wbc.get("totalAlerts", 0)
                alerts = wbc.get("alerts", [])
                recent = alerts[-5:] if alerts else []

                lines.append(f"### 🛡️ WBC Alerts\n- **総アラート数**: {total}\n")
                if recent:
                    lines.append("**直近5件:**\n")
                    for a in reversed(recent):
                        sev = a.get("severity", "?")
                        ts = a.get("timestamp", "?")[:19]
                        details = a.get("details", "")[:80]
                        icon = "🔴" if sev == "high" else ("🟡" if sev == "medium" else "🟢")
                        lines.append(f"- {icon} [{sev}] {ts} — {details}")
                    lines.append("")
                else:
                    lines.append("- ✅ アラートなし\n")
            except Exception:  # noqa: BLE001
                lines.append("### 🛡️ WBC\n- ⚠️ 読取りエラー\n")
        else:
            lines.append("### 🛡️ WBC\n- 未検出\n")

        # 3. Health Metrics (latest entry)
        health_file = _MNEME_DIR / "health_metrics.jsonl"
        if health_file.exists():
            try:
                last_line = ""
                with open(health_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            last_line = line
                if last_line:
                    metric = json.loads(last_line)
                    score = metric.get("score", "?")
                    lines.append(f"### 📊 Health Score\n- **最新スコア**: {score}\n")
            except Exception:  # noqa: BLE001
                lines.append("### 📊 Health Score\n- ⚠️ 読取りエラー\n")

        # 4. Git Status
        git_file = _MNEME_DIR / "git_sentinel_state.json"
        if git_file.exists():
            try:
                git = json.loads(git_file.read_text("utf-8"))
                dirty = git.get("isDirty", False)
                modified = len(git.get("modifiedFiles", []))
                icon = "🟡" if dirty else "🟢"
                lines.append(f"### {icon} Git\n- **Dirty**: {dirty}\n- **変更ファイル**: {modified}\n")
            except Exception:  # noqa: BLE001
                pass

        return "\n".join(lines)
    # PURPOSE: 未読通知の確認 (Sympatheia notifications)
    @mcp.tool()
    @_traced
    def hgk_notifications(limit: int = 10) -> str:
        """
        未読通知を確認する。
        HGK システムからの通知 (INFO/HIGH/CRITICAL) を表示。

        Args:
            limit: 表示件数 (デフォルト: 10)
        """
        notif_file = _MNEME_DIR / "notifications.jsonl"
        if not notif_file.exists():
            return "## 🔔 通知\n\n📭 通知ファイルが見つかりません"

        try:
            notifications = []
            with open(notif_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            notifications.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass

            if not notifications:
                return "## 🔔 通知\n\n✅ 通知はありません"

            limit = max(1, min(50, limit))
            recent = notifications[-limit:]

            lines = [f"## 🔔 通知 ({len(recent)}/{len(notifications)} 件)\n"]

            for n in reversed(recent):
                level = n.get("level", n.get("notification_level", "INFO"))
                title = n.get("title", "無題")
                body = n.get("body", "")[:100]
                ts = n.get("timestamp", "?")[:19]

                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "INFO": "🔵"}.get(level, "⚪")
                lines.append(f"- {icon} **[{level}]** {title}")
                if body:
                    lines.append(f"  {body}")
                lines.append(f"  *{ts}*")
                lines.append("")

            return "\n".join(lines)
        except Exception as e:  # noqa: BLE001
            return f"❌ 通知読取りエラー: {e}"
    # PURPOSE: PKSEngine を遅延初期化
    def _get_pks_engine():
        """PKSEngine を遅延初期化"""
        global _pks_engine
        if _pks_engine is None:
            try:
                from mekhane.pks.pks_engine import PKSEngine
                _pks_engine = PKSEngine(
                    enable_questions=True,
                    enable_serendipity=True,
                    enable_feedback=True,
                    enable_advocacy=True,
                )
            except Exception as e:  # noqa: BLE001
                print(f"[Gateway] PKSEngine init error: {e}", file=sys.stderr)
        return _pks_engine
    # PURPOSE: Autophōnos 能動的知識プッシュ — トピックに基づく知識表面化
    @mcp.tool()
    @_traced
    def hgk_proactive_push(
        topics: str = "",
        max_results: int = 5,
        use_advocacy: bool = True,
    ) -> str:
        """
        論文が自ら語りかける — Autophōnos 能動的知識プッシュ。
        コンテキスト (トピック) に基づき、関連する知識を能動的に表面化する。
        use_advocacy=True で論文が一人称で語りかける (Autophōnos モード)。

        トピック未指定時は最新の Handoff から自動抽出する。

        Args:
            topics: カンマ区切りのトピック (例: "FEP,Active Inference,CCL")。
                    省略時は最新 Handoff から自動抽出。
            max_results: 最大結果数 (デフォルト: 5)
            use_advocacy: 一人称モード (デフォルト: True)
        """
        engine = _get_pks_engine()
        if engine is None:
            return "❌ PKSEngine を初期化できませんでした"

        topic_list = [t.strip() for t in topics.split(",") if t.strip()] if topics else []

        # トピック未指定時: 最新 Handoff から自動抽出
        if not topic_list:
            topic_list = _auto_extract_topics()

        if topic_list:
            engine.set_context(topics=topic_list)

        try:
            nuggets = engine.proactive_push(k=max_results)
            if not nuggets:
                ctx_info = ", ".join(topic_list[:5]) if topic_list else "(未設定)"
                return (
                    f"📭 現在のコンテキスト ({ctx_info}) に関連する"
                    " 知識は見つかりませんでした。\n\n"
                    "💡 別のトピックを試してみてください。"
                )
            return engine.format_push_report(nuggets, use_advocacy=use_advocacy)
        except Exception as e:  # noqa: BLE001
            return f"❌ プッシュエラー: {e}"
    # PURPOSE: 最新 Handoff からトピックを自動抽出
    def _auto_extract_topics() -> list[str]:
        """最新の Handoff ファイルからトピックを自動抽出"""
        if not HANDOFF_DIR.exists():
            return []

        handoffs = list_handoff_files(HANDOFF_DIR)
        if not handoffs:
            return []

        latest = handoffs[0]
        try:
            from mekhane.pks.pks_engine import AutoTopicExtractor

            extractor = AutoTopicExtractor()
            text = latest.read_text(encoding="utf-8", errors="replace")
            topics = extractor.extract(text, max_topics=8)
            if topics:
                print(f"[Autophōnos] Handoff '{latest.name}' から {len(topics)} トピック抽出")
            return topics
        except Exception as e:  # noqa: BLE001
            print(f"[Autophōnos] トピック自動抽出エラー: {e}", file=sys.stderr)
            return []
    def _get_sympatheia():
        """sympatheia.py の遅延ロード。"""
        global _sympatheia
        if _sympatheia is None:
            try:
                from mekhane.api.routes import sympatheia as _sym
                _sympatheia = _sym
            except ImportError as e:
                print(f"[Gateway] Sympatheia import error: {e}", file=sys.stderr)
        return _sympatheia
    @mcp.tool()
    @_traced
    def hgk_sympatheia_wbc(
        details: str,
        severity: str = "medium",
        source: str = "claude",
        files: str = "",
    ) -> str:
        """
        白血球 (WBC): ファイル変更や異常にスコアリングして脅威レベルを判定する。
        SACRED_TRUTH.md 変更時は threatScore=15。CRITICAL/HIGH ならエスカレーション。

        Args:
            details: 何が起きたかの説明
            severity: low, medium, high, critical
            source: アラート発生元 (e.g. WF-08, manual)
            files: 関連ファイルパス (カンマ区切り)
        """
        import asyncio
        sym = _get_sympatheia()
        if sym is None: return "❌ Sympatheia モジュールがロードできません"

        file_list = [f.strip() for f in files.split(",")] if files else []
        req = sym.WBCRequest(source=source, severity=severity, details=details, files=file_list)
        result = asyncio.run(sym.wbc_analyze(req))
        d = result.model_dump()

        lines = [
            "# 🩸 WBC 脅威分析結果\n",
            f"- **Threat Score**: {d.get('threatScore', 0)}/15",
            f"- **Level**: {d.get('level', 'UNKNOWN')}",
            f"- **Severity**: {d.get('severity', severity)}",
            f"- **Source**: {d.get('source', source)}",
            f"- **Should Escalate**: {'🚨 YES' if d.get('shouldEscalate') else 'No'}",
            f"- **Recent Alerts (1h)**: {d.get('recentAlertCount', 0)}",
            f"- **Details**: {d.get('details', details)}",
            f"- **Files**: {', '.join(d.get('files', [])) or 'N/A'}",
        ]
        return "\n".join(lines)
    @mcp.tool()
    @_traced
    def hgk_sympatheia_attractor(context: str) -> str:
        """
        定理推薦 (Attractor): 入力テキストから最適な Hegemonikón 定理とワークフローを推薦する。
        TF-IDF ベクトル類似度で 24 定理から選択。

        Args:
            context: 推薦対象のテキスト (ユーザー入力など)
        """
        import asyncio
        sym = _get_sympatheia()
        if sym is None: return "❌ Sympatheia モジュールがロードできません"

        req = sym.AttractorRequest(context=context)
        result = asyncio.run(sym.attractor_dispatch(req))
        d = result.model_dump()

        if d.get("recommendation"):
            r = d["recommendation"]
            lines = [
                "# ⚡ Attractor 定理推薦\n",
                f"- **Theorem**: {r.get('theorem')} ({r.get('name')})",
                f"- **Series**: {r.get('series')}",
                f"- **Command**: `{r.get('command')}`",
                f"- **Confidence**: {r.get('confidence', 0):.1%}",
                f"- **Auto-dispatch**: {'Yes' if d.get('autoDispatch') else 'No'}",
                f"\n> Input: {d.get('context', context)}",
            ]
        else:
            lines = [
                "# ⚡ Attractor 定理推薦\n",
                "引力圏外。定理レベルで収束しません。",
                f"\n> Input: {d.get('context', context)}",
            ]
        return "\n".join(lines)
    @mcp.tool()
    @_traced
    def hgk_sympatheia_digest() -> str:
        """
        記憶圧縮 (Digest): 全 Sympatheia state ファイルを集約して週次サマリを生成する。
        Heartbeat, FileMonitor, Git, WBC, Health, Sessions を統合。
        """
        import asyncio
        sym = _get_sympatheia()
        if sym is None: return "❌ Sympatheia モジュールがロードできません"

        req = sym.DigestRequest()
        result = asyncio.run(sym.weekly_digest(req))
        d = result.model_dump()
        hm = d.get('health', {})
        fm = d.get('fileMon', {})
        git = d.get('git', {})
        wbc = d.get('wbc', {})

        lines = [
            "# 📊 Weekly Digest\n",
            f"**Week ending**: {d.get('weekEnding')}\n",
            f"- **Heartbeat**: {d.get('heartbeat', {}).get('beats', 0)} beats",
            f"- **File Monitor**: {fm.get('scans', 0)} scans, {fm.get('changes', 0)} changes",
            f"- **Git**: branch={git.get('branch')}, dirty={git.get('dirty')}, {git.get('changes', 0)} changes",
            f"- **WBC**: {wbc.get('weekAlerts', 0)} alerts ({wbc.get('criticals', 0)} critical, {wbc.get('highs', 0)} high)",
            f"- **Health**: avg={hm.get('avg', 0)}, {hm.get('samples', 0)} samples",
            f"- **Sessions**: {d.get('sessions', 0)}",
        ]
        return "\n".join(lines)
    @mcp.tool()
    @_traced
    def hgk_sympatheia_feedback() -> str:
        """
        恒常性 (Feedback): 直近 3 日の Health スコアと WBC アラート頻度からシステム閾値を動的調整する。
        高スコア持続→感度向上、低スコア→感度低下、アラート過多→間隔延長。
        """
        import asyncio
        sym = _get_sympatheia()
        if sym is None: return "❌ Sympatheia モジュールがロードできません"

        req = sym.FeedbackRequest()
        result = asyncio.run(sym.feedback_loop(req))
        d = result.model_dump()
        m = d.get('metrics', {})
        th = d.get('thresholds', {})

        lines = [
            "# ⚖️ Feedback Loop\n",
            "## Metrics (3 days)",
            f"- **Avg Score**: {m.get('avg', 0)}",
            f"- **Trend**: {m.get('trend', 0):+.2f}",
            f"- **Samples**: {m.get('samples', 0)}",
            f"- **WBC Alerts**: {m.get('wbcAlerts', 0)}",
            "\n## Thresholds",
            f"- health_high: {th.get('health_high', 'N/A')}",
            f"- health_low: {th.get('health_low', 'N/A')}",
            f"- stale_minutes: {th.get('stale_minutes', 'N/A')}",
            f"\n**Adjusted**: {'⚙️ YES' if d.get('adjusted') else 'No'}",
        ]
        if d.get("adjustments"):
            lines.append("\n## Adjustments")
            for a in d["adjustments"]:
                lines.append(f"- {a}")
        return "\n".join(lines)
    # =============================================================================
    # Sympatheia: 検査・監査系 (Basanos, Peira, Violations)
    # =============================================================================

    @mcp.tool()
    @_traced
    def hgk_sympatheia_basanos_scan(path: str, max_issues: int = 50) -> str:
        """
        Basanos L0 スキャン: AST ベース静的解析で Python ファイルの品質問題を検出する。
        DailyReviewPipeline の L0 フェーズを手動実行。

        Args:
            path: スキャン対象パス (ファイルまたはディレクトリ)
            max_issues: 最大 issue 数
        """
        import asyncio
        import sys
        from pathlib import Path
        synergeia_path = Path.home() / "Sync" / "oikos" / "hegemonikon" / "synergeia"
        if str(synergeia_path) not in sys.path:
            sys.path.insert(0, str(synergeia_path))

        try:
            from basanos.auditor import AIAuditor
            auditor = AIAuditor()

            # Run async scan in an event loop
            async def _scan():
                await auditor.analyze_project(path)
                return auditor.generate_report("terminal")
            
            report = asyncio.run(_scan())
        
            # Limit lines if needed, since it's just raw text report
            lines = report.split("\n")
            if len(lines) > 200:
                report = "\n".join(lines[:200]) + "\n\n... (Truncated for output size)"
            
            return f"## ⚖️ Basanos Scan Report\n\n```text\n{report}\n```"
        except ImportError as e:
            return f"❌ Basanos 読込エラー: synergeia モジュールがパスにありません ({e})"
        except Exception as e:  # noqa: BLE001
            return f"❌ スキャンエラー: {e}"
    @mcp.tool()
    @_traced
    def hgk_sympatheia_peira_health() -> str:
        """
        Peira ヘルスチェック: 全サービスの死活と品質を一覧表示。
        Systemd, Docker, Handoff, Dendron, 定理活性度, Digest 鮮度を検証。
        """
        import subprocess
        try:
            peira_script = Path.home() / "Sync" / "oikos" / "hegemonikon" / "mekhane" / "peira" / "hgk_health.py"
            if not peira_script.exists():
                return "❌ hgk_health.py が見つかりません"
            
            result = subprocess.run(
                ["python", str(peira_script)],
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout or result.stderr
        
            # Color codes are stripped by terminal view, so return as is
            return f"## 🩺 Peira System Health\n\n```text\n{output}\n```"
        except Exception as e:  # noqa: BLE001
            return f"❌ Peira 実行エラー: {e}"
    @mcp.tool()
    @_traced
    def hgk_sympatheia_log_violation(
        feedback_type: str,
        description: str,
        corrective: str = "",
        pattern: str = "",
        severity: str = "medium",
        bc_ids: str = "",
        creator_words: str = "",
        context: str = "",
    ) -> str:
        """
        BC違反/フィードバック記録: Creator の叱責・承認・AI 自己検出を即時記録。

        Args:
            feedback_type: "reprimand"(叱責), "acknowledgment"(承認), "self_detected"(自己検出)
            description: 何が起きたか
            corrective: 取った是正行動
            pattern: パターンID (skip_bias, selective_omission 等)
            severity: low, medium, high, critical
            bc_ids: 違反した BC/Nomoi ID (カンマ区切り。例: "N-1, θ3.1")
            creator_words: Creator の原文 (叱責/承認の言葉)
            context: そのとき何をしていたか
        """
        import asyncio
        sym = _get_sympatheia()
        if sym is None: return "❌ Sympatheia モジュールがロードできません"

        bc_list = [b.strip() for b in bc_ids.split(",")] if bc_ids else []
    
        req = sym.ViolationLogRequest(
            feedback_type=feedback_type,
            description=description,
            corrective=corrective,
            pattern=pattern,
            severity=severity,
            bc_ids=bc_list,
            creator_words=creator_words,
            context=context
        )
        result = asyncio.run(sym.log_violation(req))
        d = result.model_dump()
        stats = d.get('stats', {})

        lines = [
             "## 📝 記録完了",
            f"- ID: `{d.get('id', 'N/A')}`",
            f"- Status: {d.get('status', 'N/A')}",
            "",
            "### 📊 セッション統計",
            f"- セッションログ数: {d.get('session_count', 0)}",
            f"- Reprimand (叱責): {stats.get('reprimand', 0)}",
            f"- Acknowledgment (承認): {stats.get('acknowledgment', 0)}",
            f"- Self-Detected (自己検出): {stats.get('self_detected', 0)}",
            f"- 最近のパターン: {', '.join(stats.get('patterns', []))}",
            "",
            "※ セッション終了時に /bye で handoff に統合されます。"
        ]
        return "\n".join(lines)
    @mcp.tool()
    @_traced
    def hgk_sympatheia_violation_dashboard(period: str = "all") -> str:
        """
        BC違反ダッシュボード: パターン別・BC別・深刻度別の統計を表示。
        叱責率と自己検出率を可視化する。

        Args:
            period: "today", "week", "month", "all"
        """
        import asyncio
        sym = _get_sympatheia()
        if sym is None: return "❌ Sympatheia モジュールがロードできません"

        req = sym.DashboardRequest(period=period)
        result = asyncio.run(sym.get_violation_dashboard(req))
        d = result.model_dump()

        lines = [
            f"## 🛡️ Violation & Feedback Dashboard ({period})",
            "",
            "### 📊 サマリー",
            f"- **Reprimand (叱責)**: {d.get('reprimand', 0)}",
            f"- **Acknowledgment (承認)**: {d.get('acknowledgment', 0)}",
            f"- **Self-Detected (自己検出)**: {d.get('self_detected', 0)}",
        ]
    
        total = d.get('reprimand', 0) + d.get('self_detected', 0)
        if total > 0:
            self_rate = (d.get('self_detected', 0) / total) * 100
            lines.append(f"- **自己検出率**: {self_rate:.1f}%")
        
        if d.get("severity"):
            lines.extend(["", "### 🔴 深刻度別", "```text"])
            for sev, count in d.get("severity", {}).items():
                lines.append(f"{sev:<10}: {count}")
            lines.append("```")
        
        if d.get("patterns"):
            lines.extend(["", "### 🧩 パターン別 (Top 5)", "```text"])
            for pat, count in list(d.get("patterns", {}).items())[:5]:
                lines.append(f"{pat:<20}: {count}")
            lines.append("```")

        if d.get("bc_ids"):
            lines.extend(["", "### 📜 BC違反別", "```text"])
            for bc, count in d.get("bc_ids", {}).items():
                lines.append(f"{bc:<10}: {count}")
            lines.append("```")

        return "\n".join(lines)
    @mcp.tool()
    @_traced
    def hgk_sympatheia_escalate(min_occurrences: int = 3, min_severity: str = "high") -> str:
        """
        BC違反の昇格候補検出: 深刻度や再発回数に基づき violations.md への昇格候補を提案。
        自動書込みはしない (LBYL)。

        Args:
            min_occurrences: 最低出現回数 (デフォルト: 3)
            min_severity: 最低深刻度 (デフォルト: high)
        """
        import asyncio
        sym = _get_sympatheia()
        if sym is None: return "❌ Sympatheia モジュールがロードできません"

        req = sym.EscalateRequest(min_occurrences=min_occurrences, min_severity=min_severity)
        result = asyncio.run(sym.get_escalation_candidates(req))
        d = result.model_dump()
        cands = d.get("candidates", [])

        if not cands:
            return "## 🛡️ 昇格候補なし\n条件を満たすパターンは見つかりませんでした。"

        lines = [
            f"## 🚨 violations.md 昇格候補 ({len(cands)} 件)",
            "> 以下のパターンは繰り返されているか、深刻度が高いため明文化を推奨します。",
            ""
        ]
    
        for c in cands:
            lines.extend([
                f"### パターン: `{c.get('pattern')}`",
                f"- **出現回数**: {c.get('count')}",
                f"- **最高深刻度**: {c.get('max_severity')}",
                f"- **関連 BC IDs**: {', '.join(c.get('bc_ids', []))}",
                "**Creator の言葉**:",
            ])
            for cw in c.get('creator_words', [])[:3]:
                lines.append(f"> \"{cw}\"")
            lines.extend([
                "",
                "**昇格用テンプレート**: `violations.md` に追記してください",
                "```markdown",
                "### V-XXX: [タイトル]",
                f"**日付**: {datetime.now().strftime('%Y-%m-%d')}",
                f"**BC違反**: {', '.join(c.get('bc_ids', []))}",
                f"**現象**: {c.get('pattern')} — [詳細説明]",
                "**対症療法**: [防止策]",
                "**根本原因**: 第零原則「意志より環境」の観点から考察",
                "```",
                "---"
            ])
        
        return "\n".join(lines)

    # =============================================================================
    # Q3: Fixation Detection (Q-series circulation stagnation)
    # =============================================================================

    # PURPOSE: テキスト表層の停止ワードから Q-series 固着パターンを検出する MCP ツール
    @mcp.tool()
    @_traced
    async def hgk_sympatheia_fixation(
        text: str = "",
        threshold: float = 0.3,
    ) -> str:
        """テキスト内の認知的固着パターンを Q-series 辺にマッピングして検出する。

        Hóros の停止ワード (「大きすぎる」「次のセッション」等) の出現頻度から
        固着スコアを算出。閾値超過で Sympatheia 通知を自動発行。

        Args:
            text: 分析対象のテキスト (空の場合は使い方を返す)
            threshold: 固着検出の閾値 (0.0-1.0, デフォルト 0.3)

        Returns:
            固着検出レポート (Markdown)
        """
        if not text.strip():
            return (
                "## 🔄 Q-series 固着検出ツール\n\n"
                "**使い方**: `text` にセッションテキストを渡してください。\n"
                "停止ワードの出現頻度から固着パターンを検出します。\n\n"
                "**対象パターン**:\n"
                "- T-6: 尻込み (「大きすぎる」「複雑」)\n"
                "- T-3: 先延ばし (「次のセッション」「後で」)\n"
                "- B20: 反芻 (「現実的でない」「膨大」)\n"
                "- T-4: 保守化 (「安全な方」「リスクを避け」)\n"
                "- B1: 読み飛ばし (「既に取得済み」「全文読みは」)\n"
                "- CD-1: 不可能断定 (「できない」「不可能」)\n"
            )

        from mekhane.sympatheia.core import fixation_analyze, FixationRequest
        from mekhane.taxis.fixation_detector import format_report, detect_fixation

        # 固着検出を実行
        report = detect_fixation(text, threshold=threshold)

        # Sympatheia 通知を発行 (閾値超過時)
        req = FixationRequest(text=text, threshold=threshold)
        response = await fixation_analyze(req)

        # レポートをフォーマット
        formatted = format_report(report)

        # 通知発行履歴を追記
        if response.has_fixation:
            formatted += f"\n\n📢 **Sympatheia 通知発行済み** (level: {'HIGH' if response.max_score > 0.7 else 'INFO'})"

        return formatted

    # =============================================================================
    # Q3-b: WF 使用パターン分析 (定理ログからの偏り検出)
    # =============================================================================

    # PURPOSE: 定理ログから WF 使用パターンの偏りを検出する MCP ツール
    @mcp.tool()
    @_traced
    async def hgk_sympatheia_wf_pattern(
        days: int = 7,
    ) -> str:
        """定理ログから WF 使用パターンの偏りを検出する。

        Explore/Exploit 比率、6族エントロピー、未使用定理を分析し、
        認知的偏りを可視化する。偏り検出時は Sympatheia 通知を自動発行。

        Args:
            days: 分析対象の日数 (0=全期間, デフォルト 7)

        Returns:
            WF パターン分析レポート (Markdown)
        """
        from mekhane.sympatheia.core import wf_pattern_analyze, WFPatternRequest
        from mekhane.taxis.wf_pattern_detector import detect_wf_pattern, format_wf_report

        # 検出を実行
        report = detect_wf_pattern(days=days)

        # Sympatheia 通知を発行 (偏り検出時)
        req = WFPatternRequest(days=days)
        response = await wf_pattern_analyze(req)

        # レポートをフォーマット
        formatted = format_wf_report(report)

        # 通知発行履歴を追記
        if response.has_imbalance:
            level = "HIGH" if len(response.alerts) >= 2 else "INFO"
            formatted += f"\n\n📢 **Sympatheia 通知発行済み** (level: {level})"

        return formatted

    @mcp.tool()
    @_traced
    async def hgk_sympatheia_cognitive_scan(
        text: str = "",
        days: int = 7,
        threshold: float = 0.5,
    ) -> str:
        """
        認知スキャン: テキスト固着 + WF 使用パターン偏りを統合分析し、複合スコア (0-1) を算出。
        閾値超過時に WBC 脅威アラートを自動発行。

        Args:
            text: 固着チェック対象テキスト (空文字なら固着チェックをスキップ)
            days: WF パターン分析期間 (デフォルト: 7日)
            threshold: WBC 発行閾値 (デフォルト: 0.5)
        """
        import asyncio
        sym = _get_sympatheia()
        if sym is None:
            return "❌ Sympatheia モジュールがロードできません"

        req = sym.CognitiveScanRequest(
            text=text,
            days=days,
            threshold=threshold,
        )
        result = asyncio.run(sym.cognitive_scan(req))
        d = result.model_dump()

        # スコアに応じた絵文字
        score = d.get("cognitive_score", 0)
        if score >= 0.7:
            emoji = "🚨"
            verdict = "HIGH — 認知的偏り検出"
        elif score >= 0.5:
            emoji = "⚠️"
            verdict = "MEDIUM — 注意が必要"
        else:
            emoji = "✅"
            verdict = "正常"

        lines = [
            f"# 🧠 認知スキャン結果 {emoji}\n",
            f"- **Cognitive Score**: {score:.3f} / 1.0",
            f"- **Verdict**: {verdict}",
            f"- **固着検出**: {'⚠️ あり' if d.get('fixation_detected') else '✅ なし'}"
            f" (ratio={d.get('fixation_ratio', 0):.2f})",
            f"- **WF 偏り**: {'⚠️ あり' if d.get('wf_imbalance_detected') else '✅ なし'}"
            f" (E/E={d.get('wf_ee_ratio', 0):.2f}, entropy={d.get('wf_entropy_ratio', 0):.2f})",
            f"- **WBC 発行**: {'🚨 発行済み (score={d.get(\"wbc_threat_score\", 0)})' if d.get('wbc_triggered') else '未発行'}",
        ]

        # 成分スコア
        components = d.get("components", {})
        if components:
            lines.append("\n## スコア成分")
            for k, v in components.items():
                bar = "█" * int(v * 20) + "░" * (20 - int(v * 20))
                lines.append(f"- **{k}**: {v:.3f} |{bar}|")

        # アラート一覧
        alerts = d.get("alerts", [])
        if alerts:
            lines.append("\n## アラート")
            for a in alerts:
                lines.append(f"- {a}")

        return "\n".join(lines)
