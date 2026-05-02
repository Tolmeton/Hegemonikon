# PROOF: mekhane/mcp/gateway_tools/periskope.py
# PURPOSE: mcp モジュールの periskope
"""Gateway tools: periskope domain."""
import time
import json


def register_periskope_tools(mcp):
    """Register periskope domain tools (6 tools)."""
    from mekhane.mcp.gateway_tools._utils import _traced, _get_policy, _trace_tool_call, _GATEWAY_URL

    # =============================================================================
    # Periskopē: Deep Research Engine
    # =============================================================================

    @mcp.tool()
    def hgk_research(
        query: str,
        depth: int = 2,
        sources: str = "",
        max_results: int = 10,
        expand_query: bool = True,
        known_context: str = "",
    ) -> str:
        """
        Periskopē Deep Research を実行する。
        多ソース並列検索 → 多モデル合成 → 引用検証 → レポート生成。
        2-4分かかる場合がある。

        Args:
            query: 調査クエリ (例: "Free Energy Principle と active inference の関係")
            depth: 調査深度 (1=Quick, 2=Standard, 3=Deep)
            sources: 使用ソース (カンマ区切り、空=全ソース)。選択肢: searxng, brave, tavily, semantic_scholar, gnosis, sophia, kairos
            max_results: ソースあたり最大結果数
            expand_query: バイリンガルクエリ展開 (デフォルト: True)
            known_context: 既に知っていることの文脈
        """
        import asyncio
        _start = time.time()

        if not query or not query.strip():
            _trace_tool_call("hgk_research", 0, (time.time() - _start) * 1000, False)
            return "❌ クエリが空です"

        try:
            from mekhane.periskope.engine import PeriskopeEngine

            source_list = [s.strip() for s in sources.split(",") if s.strip()] if sources else None
            depth = max(1, min(3, depth))

            engine = PeriskopeEngine(
                max_results_per_source=max_results,
                verify_citations=True,
            )
            report = asyncio.get_event_loop().run_until_complete(
                engine.research(
                    query=query,
                    sources=source_list,
                    depth=depth,
                    expand_query=expand_query,
                    known_context=known_context,
                )
            )

            md = report.markdown()

            # Auto-log to tracker
            try:
                from mekhane.periskope.research_tracker import log_research_run
                overall_score = report.quality_metrics.overall_score if report.quality_metrics else None
                log_research_run(theme=query[:60], query=query, depth=depth, score=overall_score)
            except Exception:  # noqa: BLE001
                pass

            # Token Explosion 対策
            if len(md) > 15000:
                md = md[:15000] + "\n\n... (出力が 15000 文字を超えたため切り詰めました)"

            _trace_tool_call("hgk_research", len(query), (time.time() - _start) * 1000, True)
            return md
        except Exception as e:  # noqa: BLE001
            _trace_tool_call("hgk_research", len(query), (time.time() - _start) * 1000, False)
            return f"❌ エラー: {e}"
    @mcp.tool()
    def hgk_research_search(
        query: str,
        sources: str = "",
        max_results: int = 10,
        expand_query: bool = True,
    ) -> str:
        """
        軽量検索のみ実行 (合成・引用検証なし)。高速 (10-15秒)。

        Args:
            query: 検索クエリ
            sources: 使用ソース (カンマ区切り、空=全ソース)
            max_results: ソースあたり最大結果数
            expand_query: バイリンガルクエリ展開
        """
        import asyncio
        _start = time.time()

        if not query or not query.strip():
            _trace_tool_call("hgk_research_search", 0, (time.time() - _start) * 1000, False)
            return "❌ クエリが空です"

        try:
            from mekhane.periskope.engine import PeriskopeEngine

            source_list = [s.strip() for s in sources.split(",") if s.strip()] if sources else None

            engine = PeriskopeEngine(
                max_results_per_source=max_results,
                verify_citations=False,
            )
            report = asyncio.get_event_loop().run_until_complete(
                engine.research(
                    query=query,
                    sources=source_list,
                    depth=1,
                    expand_query=expand_query,
                )
            )

            lines = [
                f"## 🔍 Periskopē 検索結果",
                f"",
                f"> **Query**: {query}",
                f"> **Time**: {report.elapsed_seconds:.1f}s",
                f"> **Results**: {len(report.search_results)} from {len(report.source_counts)} sources",
                f"",
            ]

            # Source breakdown
            lines.append("| Engine | Results |")
            lines.append("|:-------|--------:|")
            for source, count in sorted(report.source_counts.items()):
                lines.append(f"| {source} | {count} |")
            lines.append("")

            # Top results
            for i, r in enumerate(report.search_results[:20], 1):
                lines.append(f"### [{i}] {r.title}")
                if r.url:
                    lines.append(f"- **URL**: {r.url}")
                lines.append(f"- **Source**: {r.source.value}")
                snippet = r.snippet or (r.content[:200] if r.content else "")
                if snippet:
                    lines.append(f"- {snippet}")
                lines.append("")

            # Quick synthesis if available
            if report.synthesis:
                lines.append("## Quick Synthesis")
                for s in report.synthesis:
                    lines.append(f"\n{s.content}\n")

            result = "\n".join(lines)
            if len(result) > 10000:
                result = result[:10000] + "\n\n... (切り詰め)"

            _trace_tool_call("hgk_research_search", len(query), (time.time() - _start) * 1000, True)
            return result
        except Exception as e:  # noqa: BLE001
            _trace_tool_call("hgk_research_search", len(query), (time.time() - _start) * 1000, False)
            return f"❌ エラー: {e}"
    @mcp.tool()
    def hgk_research_sources(query: str) -> str:
        """
        クエリに最適な検索ソースを推薦する。

        Args:
            query: 分類対象のクエリ
        """
        _start = time.time()

        if not query:
            return "❌ クエリが空です"

        try:
            from mekhane.periskope.engine import PeriskopeEngine

            qtype = PeriskopeEngine._classify_query(query)
            recommended = PeriskopeEngine.select_sources(query)

            all_sources = {
                "searxng": "SearXNG (メタ検索)",
                "brave": "Brave Search",
                "tavily": "Tavily (AI向け検索)",
                "semantic_scholar": "Semantic Scholar (学術論文)",
                "gnosis": "Gnōsis (HGK 内部知識)",
                "sophia": "Sophia (KI)",
                "kairos": "Kairos (文脈知識)",
            }

            lines = [
                f"## 📡 ソース推薦",
                f"",
                f"**Query**: {query}",
                f"**分類**: {qtype}",
                f"",
                "| ソース | 説明 | 推薦 |",
                "|:-------|:-----|:----:|",
            ]
            for s, desc in all_sources.items():
                marker = "✅" if s in recommended else "—"
                lines.append(f"| {s} | {desc} | {marker} |")

            _trace_tool_call("hgk_research_sources", len(query), (time.time() - _start) * 1000, True)
            return "\n".join(lines)
        except Exception as e:  # noqa: BLE001
            _trace_tool_call("hgk_research_sources", len(query), (time.time() - _start) * 1000, False)
            return f"❌ エラー: {e}"
    @mcp.tool()
    @_traced
    def hgk_periskope_track(
        theme: str = "",
        action: str = "list",
        topics: str = "",
        completed: str = "",
        in_progress: str = "",
        next_actions: str = "",
        query: str = "",
        depth: int = 2,
        score: float | None = None,
    ) -> str:
        """
        調査テーマの進捗を管理。/sop.track
    
        Args:
            theme: 調査テーマ名
            action: 操作: list/create/update/status/log
            topics: カンマ区切りの論点リスト (create/update用)
            completed: カンマ区切りの完了論点 (update用)
            in_progress: カンマ区切りの進行中論点 (update用)
            next_actions: カンマ区切りの次のアクション (update用)
            query: 検索クエリ (log用)
            depth: 調査深度 (log用)
            score: 品質スコア (log用)
        """
        import asyncio
        from mekhane.periskope.research_tracker import (
            create_track, update_progress, log_research_run,
            load_track, list_tracks, format_status,
        )
    
        def _parse_list(s: str) -> list[str]:
            return [x.strip() for x in s.split(",") if x.strip()] if s else []

        if action == "list":
            tracks = list_tracks()
            if not tracks:
                return "調査テーマはまだありません。"
            lines = ["# 調査テーマ一覧", ""]
            lines.append("| テーマ | 進捗 | 更新日 |")
            lines.append("|:------|-----:|:------|")
            for t in tracks:
                lines.append(f"| {t.theme} | {t.progress_percent}% | {t.updated} |")
            return "\n".join(lines)

        if action == "create":
            if not theme: return "❌ Error: theme is required"
            topic = create_track(theme, _parse_list(topics))
            return format_status(topic)

        if action == "update":
            if not theme: return "❌ Error: theme is required"
            topic = update_progress(
                theme,
                completed=_parse_list(completed),
                in_progress=_parse_list(in_progress),
                pending=_parse_list(topics),
                next_actions=_parse_list(next_actions),
            )
            return format_status(topic)

        if action == "log":
            if not theme: return "❌ Error: theme is required"
            topic = log_research_run(
                theme,
                query=query,
                depth=depth,
                score=score,
            )
            return format_status(topic)

        if action == "status":
            if not theme: return "❌ Error: theme is required"
            topic = load_track(theme)
            if not topic:
                return f"テーマ '{theme}' が見つかりません。"
            return format_status(topic)

        return f"Unknown action: {action}"
    @mcp.tool()
    @_traced
    def hgk_periskope_metrics(limit: int = 10) -> str:
        """
        過去の調査結果から品質メトリクスの中央値やトレンド、詳細を照会する。
        """
        from mekhane.periskope.research_tracker import list_tracks
    
        tracks = list_tracks()
        if not tracks:
            return "No research tracks found."
    
        runs = []
        for t in tracks:
            for h in getattr(t, "depth_history", []):
                if h.get("score") is not None:
                    runs.append({
                        "theme": t.theme,
                        "date": h.get("date") or "",
                        "score": h["score"],
                    })
    
        # Sort by date (descending)
        runs.sort(key=lambda x: x["date"], reverse=True)
        recent = runs[:limit]

        if not recent:
            return "No scores recorded in recent tracks."
    
        avg_score = sum(r["score"] for r in recent) / len(recent)
    
        lines = [f"# Periskopē Quality Metrics (Last {len(recent)} runs)", ""]
        lines.append(f"- **Average Overall Score**: {avg_score:.2f}")
        lines.append("")
        lines.append("| Date | Theme | Score |")
        lines.append("|:---|:---|---:|")
        for r in recent:
            date_str = r["date"].split(" ")[0] if r["date"] else "Unknown"
            lines.append(f"| {date_str} | {r['theme'][:40]}... | {r['score']:.2f} |")
    
        return "\n".join(lines)
    @mcp.tool()
    @_traced
    def hgk_periskope_benchmark(
        queries: str,
        depth: int = 1,
        sources: str = "",
        decay_type: str = "",
        alpha_schedule: str = "",
        llm_rerank: bool = None,
    ) -> str:
        """
        指定した複数のクエリで検索を実行し、品質スコア(NDCG, Entropy, Coverage)を比較・ベンチマークする。
    
        Args:
            queries: ベンチマーク対象のクエリリスト (カンマ区切り)
            depth: 調査深度 (1=Quick, 2=Standard)
            sources: 使用ソース (カンマ区切り、空=デフォルトの高速ソース)
            decay_type: β schedule
            alpha_schedule: α schedule
            llm_rerank: LLM リランキングの on/off
        """
        import asyncio
        from mekhane.periskope.engine import PeriskopeEngine
    
        q_list = [q.strip() for q in queries.split(",") if q.strip()]
        if not q_list:
            return "❌ Error: queries list is required"
        
        engine = PeriskopeEngine(verify_citations=False)
        default_sources = engine._config.get("benchmark_default_sources", ["searxng", "brave", "tavily"])
    
        src_list = [s.strip() for s in sources.split(",") if s.strip()] if sources else default_sources
    
        lines = ["# Periskopē Benchmark Results", ""]
        lines.append(f"> **Depth**: L{depth}")
        lines.append(f"> **Queries**: {len(q_list)}")
        lines.append(f"> **Sources**: {', '.join(src_list)}")
        if decay_type:
            lines.append(f"> **β schedule**: {decay_type}")
        if alpha_schedule:
            lines.append(f"> **α schedule**: {alpha_schedule}")
        lines.append("")
        lines.append("| Query | Results | Srcs | NDCG | Entropy | Cov. | **Score** | Time |")
        lines.append("|:---|---:|---:|---:|---:|---:|---:|---:|")

        # Override schedule config if specified via MCP
        _apply_schedule_override(engine, decay_type, alpha_schedule, prefix="Benchmark ")

        async def run_benchmark():
            from mekhane.mcp.mcp_base import StdoutSuppressor
        
            for q in q_list:
                print(f"Benchmark running query: {q!r}", file=sys.stderr)
                try:
                    with StdoutSuppressor():
                        report = await engine.research(
                            query=q,
                            sources=src_list,
                            depth=depth, 
                            expand_query=False, 
                            auto_digest=False,
                            llm_rerank=llm_rerank,
                        )
                
                    m = report.quality_metrics
                    t = report.elapsed_seconds
                    results_cnt = len(report.search_results)
                    src_cnt = len(report.source_counts)
                
                    if m:
                        lines.append(
                            f"| {q[:30]} | {results_cnt} | {src_cnt} | "
                            f"{m:benchmark} | {t:.1f}s |"
                        )
                    else:
                        lines.append(
                            f"| {q[:30]} | {results_cnt} | {src_cnt} | - | - | - | - | {t:.1f}s |"
                        )
                except Exception as e:  # noqa: BLE001
                    lines.append(f"| {q[:30]} | ERROR | - | - | - | - | - | - |")
                    print(f"Benchmark error for '{q}': {e}", file=sys.stderr)
                
        asyncio.run(run_benchmark())
                    
        return "\n".join(lines)
