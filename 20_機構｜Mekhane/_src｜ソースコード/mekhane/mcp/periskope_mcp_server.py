# PROOF: [L2/インフラ] <- mekhane/mcp/periskope_mcp_server.py Periskopē Deep Research を MCP ツールとして公開
#!/usr/bin/env python3
"""
Periskopē MCP Server v1.0 — Deep Research Engine via MCP

Tools:
  - periskope_research: Full deep research pipeline (search + synthesis + verification)
  - periskope_search: Multi-source parallel search only (lightweight)
  - periskope_sources: Recommend optimal sources for a query
"""

from mekhane.mcp.mcp_base import MCPBase, StdoutSuppressor

# Initialize via shared infrastructure
_base = MCPBase(
    name="periskope",
    version="1.0.0",
    instructions=(
        "Periskopē: Deep Research Engine. "
        "Multi-source search (Google CSE, StackOverflow, Reddit, HackerNews, Github, SearXNG, Brave, Tavily, Semantic Scholar, Gnosis, Sophia, Kairos) "
        "+ multi-model synthesis (Gemini/Claude) + citation verification (N-10 TAINT). "
        "Use periskope_search for quick searches, periskope_research for full deep research."
    ),
)
server = _base.server
log = _base.log
TextContent = _base.TextContent
Tool = _base.Tool

# Import Periskopē modules
PeriskopeEngine = None
try:
    with StdoutSuppressor():
        from mekhane.periskope.engine import PeriskopeEngine as _PE
    PeriskopeEngine = _PE
    log("Periskopē engine import successful")
except Exception as e:  # noqa: BLE001
    log(f"Periskopē import error: {e}")
    log("Will run with stub mode")

def _apply_schedule_override(engine, decay_type: str, alpha_schedule: str, prefix: str = ""):
    """Override schedule config if specified via MCP."""
    if decay_type or alpha_schedule:
        iter_cfg = engine._config.get("iterative_deepening", {})
        if decay_type:
            iter_cfg["decay_type"] = decay_type
        if alpha_schedule:
            iter_cfg["alpha_schedule"] = alpha_schedule
        engine._config["iterative_deepening"] = iter_cfg
        log_prefix = prefix + "s" if prefix else "S"
        log(f"{log_prefix}chedule override: decay_type={decay_type!r}, alpha_schedule={alpha_schedule!r}")


# PURPOSE: [L2-auto] list_tools の非同期処理定義
@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        # ── research: 独立維持 (主力ツール) ──
        Tool(
            name="periskope_research",
            description=(
                "フル Deep Research パイプラインを実行。"
                "多ソース並列検索 → 多モデル合成 → 引用検証 → レポート生成。"
                "2-4分かかる場合がある (Deep Research は本来時間がかかるもの)。 Returns: list of matching results with relevance scores. Example: periskope_research(query='...') Errors if required params (query) are missing or invalid."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "調査依頼プロンプト（キーワード羅列は禁止）。外部AIへの調査依頼書として自然文で書くこと。"
                            "必須要素: (1) 背景: なぜこの調査が必要か、何の到達点にいるか "
                            "(2) 具体的な問い: 何を知りたいか（番号付きで複数可） "
                            "(3) 既知情報: 既に知っていること、検証したい仮説（重複排除用） "
                            "(4) 期待する証拠: 論文/実装/ベンチマーク/理論等 "
                            "(5) 制約: 前提にしないこと、不要な方向。"
                            "例: 'LLMのシステムプロンプトにおいて認知制約の密度と行為可能性は"
                            "どのような関係にあるか調査したい。具体的には: (1) WHATのみの簡潔な制約 vs "
                            "WHAT+HOW+WHYをパッケージした制約はどちらが行動変容に効くか？ "
                            "(2) WHYを含めると未知文脈への汎化は改善するか？ "
                            "先行研究: Liu et al. (2023) lost in the middle は既知。"
                            "実装・実験寄りの情報を優先してほしい。'"
                        ),
                    },
                    "research_brief": {
                        "type": "object",
                        "description": (
                            "構造化された調査依頼書。query の代わりに使用可能（推奨）。"
                            "各フィールドを埋めることで高品質な検索が保証される。"
                        ),
                        "properties": {
                            "background": {
                                "type": "string",
                                "description": "背景・動機: なぜこの調査が必要か、何の到達点にいるか",
                            },
                            "questions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "具体的な問い（番号付き）: 何を知りたいか",
                            },
                            "known_info": {
                                "type": "string",
                                "description": "既知情報: 既に知っていること、検証したい仮説（重複排除用）",
                            },
                            "evidence_type": {
                                "type": "string",
                                "description": "期待する証拠: 論文/実装/ベンチマーク/理論等",
                            },
                            "constraints": {
                                "type": "string",
                                "description": "制約: 前提にしないこと、不要な方向",
                            },
                        },
                    },
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Sources to use (omit for all sources). "
                            "Options: searxng, brave, tavily, semantic_scholar, gnosis, sophia, kairos, github, gemini_search, vertex_search, vector_search_ann, stackoverflow, reddit, hackernews"
                        ),
                    },
                    "depth": {
                        "type": "integer",
                        "default": 2,
                        "description": "Research depth. 1=L1 Quick, 2=L2 Standard, 3=L3 Deep",
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 10,
                        "description": "Max results per source",
                    },
                    "auto_digest": {
                        "type": "boolean",
                        "default": False,
                        "description": "True to auto-write to /eat incoming",
                    },
                    "multipass": {
                        "type": "boolean",
                        "default": False,
                        "description": "True for W6 two-pass refinement search",
                    },
                    "expand_query": {
                        "type": "boolean",
                        "default": True,
                        "description": "True for W3 bilingual query expansion",
                    },
                    "known_context": {
                        "type": "string",
                        "default": "",
                        "description": "Known context for information value evaluation",
                    },
                    "decay_type": {
                        "type": "string",
                        "default": "",
                        "description": (
                            "Beta schedule: exploration width decay. "
                            "Empty=config default. Options: linear, exponential, cosine, logsnr"
                        ),
                    },
                    "alpha_schedule": {
                        "type": "string",
                        "default": "",
                        "description": (
                            "Alpha schedule: explore/exploit balance (independent of beta). "
                            "Empty=config default. Options: linear, cosine, sigmoid"
                        ),
                    },
                    "dialectic": {
                        "type": "boolean",
                        "default": False,
                        "description": "True for parallel Thesis/Anti execution (DialecticEngine v2)",
                    },
                    "llm_rerank": {
                        "type": "boolean",
                        "description": "LLM reranking on/off. When omitted, follows config",
                    },
                },
                "required": ["query"],
            },
        ),
        # ── search: search + sources 統合ファサード ──
        Tool(
            name="periskope_search",
            description=(
                "軽量検索ファサード。mode で操作を選択: "
                "search=多ソース並列検索のみ実行 (合成・引用検証なし、10-15秒), "
                "sources=クエリに最適な検索ソースを推薦 (F12 分類)。"
                "Example: periskope_search(query='...', mode='search')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["search", "sources"],
                        "default": "search",
                        "description": "操作: search(並列検索), sources(ソース推薦)",
                    },
                    "query": {
                        "type": "string",
                        "description": (
                            "検索プロンプト（キーワード羅列は禁止）。何を探しているか、なぜ必要か、"
                            "既知の情報は何かを自然文で含める。"
                            "例: 'Hewitt & Manning (2019) の structural probes 論文の後続研究で、"
                            "linear probe の selectivity 問題を解決した手法を探している。"
                            "Pimentel et al. の control task approach は既知。それ以外の手法を知りたい。'"
                        ),
                    },
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "mode=search 時: Sources to use (omit for all)",
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 10,
                        "description": "mode=search 時: Max results per source",
                    },
                    "expand_query": {
                        "type": "boolean",
                        "default": True,
                        "description": "mode=search 時: W3 bilingual query expansion",
                    },
                    "research_brief": {
                        "description": (
                            "構造化された調査依頼書。query の代わりに使用可能（推奨）。"
                            "各フィールドを埋めることで高品質な検索が保証される。"
                        ),
                        "type": "object",
                        "properties": {
                            "background": {
                                "type": "string",
                                "description": "背景・動機: なぜこの調査が必要か、何の到達点にいるか",
                            },
                            "questions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "具体的な問い（番号付き）: 何を知りたいか",
                            },
                            "known_info": {
                                "type": "string",
                                "description": "既知情報: 既に知っていること、検証したい仮説（重複排除用）",
                            },
                            "evidence_type": {
                                "type": "string",
                                "description": "期待する証拠: 論文/実装/ベンチマーク/理論等",
                            },
                            "constraints": {
                                "type": "string",
                                "description": "制約: 前提にしないこと、不要な方向",
                            },
                        },
                    },
                },
                "required": ["query"],
            },
        ),
        # ── track: 独立維持 (既にアクション分岐あり) ──
        Tool(
            name="periskope_track",
            description=(
                "調査テーマの進捗を管理。action: list(一覧), create(新規), "
                "update(進捗更新), status(テーマ状況), log(調査実行記録)。 Returns: updated tracking state. Example: periskope_track(action='...') Errors on invalid input or internal failure."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "create", "update", "status", "log"],
                        "default": "list",
                        "description": "Action: list/create/update/status/log",
                    },
                    "theme": {"type": "string", "description": "Research theme name"},
                    "topics": {"type": "array", "items": {"type": "string"}, "description": "Topics list (for create/update)"},
                    "completed": {"type": "array", "items": {"type": "string"}, "description": "Completed topics (for update)"},
                    "in_progress": {"type": "array", "items": {"type": "string"}, "description": "In-progress topics (for update)"},
                    "next_actions": {"type": "array", "items": {"type": "string"}, "description": "Next actions (for update)"},
                    "query": {"type": "string", "description": "Search query (for log)"},
                    "depth": {"type": "integer", "description": "Research depth (for log)"},
                    "score": {"type": "number", "description": "Quality score (for log)"},
                },
            },
        ),
        # ── admin: benchmark + metrics + ping 統合ファサード ──
        Tool(
            name="periskope_admin",
            description=(
                "管理・診断ツール。action で操作を選択: "
                "ping=ヘルスチェック, metrics=品質メトリクス照会, "
                "benchmark=複数クエリのベンチマーク実行。"
                "Example: periskope_admin(action='ping')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["ping", "metrics", "benchmark"],
                        "description": "操作: ping(死活), metrics(品質), benchmark(ベンチマーク)",
                    },
                    # metrics 用
                    "limit": {"type": "integer", "default": 10, "description": "action=metrics 時: 取得件数"},
                    # benchmark 用
                    "queries": {"type": "array", "items": {"type": "string"}, "description": "action=benchmark 時: クエリリスト"},
                    "depth": {"type": "integer", "default": 1, "description": "action=benchmark 時: Research depth"},
                    "llm_rerank": {"type": "boolean", "description": "action=benchmark 時: LLM reranking on/off"},
                },
                "required": ["action"],
            },
        ),
    ]


# PURPOSE: [L2-auto] call_tool の非同期処理定義
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    log(f"Tool call: {name} with args: {arguments}")

    # ── エイリアス層: 旧ツール名 → 新ファサード名にマッピング ──
    _ALIAS = {
        "periskope_sources": ("periskope_search", "sources"),
        "periskope_metrics": ("periskope_admin", "metrics"),
        "periskope_benchmark": ("periskope_admin", "benchmark"),
        "periskope_ping": ("periskope_admin", "ping"),
    }
    if name in _ALIAS:
        facade, mode_val = _ALIAS[name]
        key = "mode" if facade == "periskope_search" else "action"
        arguments.setdefault(key, mode_val)
        name = facade

    try:
        # ── 独立ツール ──
        if name == "periskope_research":
            return await handle_research(arguments)
        elif name == "periskope_track":
            return await handle_track(arguments)
        # ── search ファサード (search + sources) ──
        elif name == "periskope_search":
            mode = arguments.get("mode", "search")
            if mode == "sources":
                return await handle_sources(arguments)
            else:
                return await handle_search(arguments)
        # ── admin ファサード (ping + metrics + benchmark) ──
        elif name == "periskope_admin":
            action = arguments.get("action", "ping")
            if action == "ping":
                return [TextContent(type="text", text="pong")]
            elif action == "metrics":
                return await handle_metrics(arguments)
            elif action == "benchmark":
                return await handle_benchmark(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown admin action: {action}")]
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:  # noqa: BLE001
        log(f"Tool error: {e}")
        import traceback
        log(traceback.format_exc())
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# PURPOSE: [L2-auto] handle_research の非同期処理定義
async def handle_research(arguments: dict):
    """Full deep research pipeline."""
    if PeriskopeEngine is None:
        return [TextContent(type="text", text="Periskopē engine not available")]

    query = arguments.get("query", "")

    # --- Φ0 Research Brief → Query 統合 ---
    # research_brief (構造化フィールド) があれば query に統合する
    research_brief = arguments.get("research_brief")
    has_brief = False
    if research_brief and isinstance(research_brief, dict):
        brief_parts = []
        bg = research_brief.get("background", "")
        if bg:
            brief_parts.append(f"背景: {bg}")
        questions = research_brief.get("questions", [])
        if questions:
            q_text = " ".join(f"({i+1}) {q}" for i, q in enumerate(questions))
            brief_parts.append(f"問い: {q_text}")
        known = research_brief.get("known_info", "")
        if known:
            brief_parts.append(f"既知: {known}")
        ev = research_brief.get("evidence_type", "")
        if ev:
            brief_parts.append(f"期待する証拠: {ev}")
        cons = research_brief.get("constraints", "")
        if cons:
            brief_parts.append(f"制約: {cons}")
        if brief_parts:
            structured_query = " ".join(brief_parts)
            if query:
                query = f"{query}\n{structured_query}"
            else:
                query = structured_query
            arguments["query"] = query
            has_brief = True
            log(f"📋 Research brief → query: {query[:150]!r}")
    # --- /Φ0 Research Brief → Query 統合 ---

    if not query:
        return [TextContent(type="text", text="Error: query or research_brief is required")]

    # --- Φ0.1 全クエリ構造化: research_brief なし → LLM で調査依頼書に構造化 ---
    if not has_brief:
        try:
            from mekhane.periskope.cognition.phi0_query_fortifier import fortify_query
            known_context = arguments.get("known_context", "")
            log(f"🔧 Structuring query: {query[:80]!r}")
            fortified = await fortify_query(query, known_context)
            if fortified != query:
                log(f"✅ Query structured → {fortified[:120]!r}")
                query = fortified
                arguments["query"] = query
        except Exception as e:  # noqa: BLE001
            log(f"Query structuring skipped: {e}")
    # --- /Φ0.1 全クエリ構造化 ---

    sources = arguments.get("sources")
    depth = arguments.get("depth", 2)
    max_results = arguments.get("max_results", 10)
    auto_digest = arguments.get("auto_digest", False)
    multipass = arguments.get("multipass", False)
    expand_query = arguments.get("expand_query", True)
    known_context = arguments.get("known_context", "")
    decay_type = arguments.get("decay_type", "")
    alpha_schedule = arguments.get("alpha_schedule", "")
    llm_rerank = arguments.get("llm_rerank", None)

    log(f"Research: query={query!r}, depth=L{depth}, sources={sources}")

    dialectic = arguments.get("dialectic", None)

    # Auto-activate dialectic for deep research (L3+)
    # FEP: deeper exploration demands adversarial verification
    if dialectic is None:
        dialectic = depth >= 3
        if dialectic:
            log(f"Auto-activating dialectic for depth=L{depth}")
    

    # Collect thinking trace events throughout execution
    thinking_events: list[dict] = []

    def progress_cb(event):
        """ProgressCallback — receives ProgressEvent from engine."""
        entry = {"t": event.elapsed, "phase": event.phase, **event.detail}
        if event.label:
            entry["label"] = event.label
        if event.phase_type:
            entry["type"] = event.phase_type
        thinking_events.append(entry)
        log(f"[PROGRESS] {event.summary()}")

    with StdoutSuppressor():
        if dialectic:
            # v2 DialecticEngine: parallel Thesis/Anti with EphemeralIndex
            from mekhane.periskope.dialectic import DialecticEngine
            log("Using DialecticEngine (v2 parallel)")
            engine = DialecticEngine(
                max_results_per_source=max_results,
            )
            report = await engine.research(
                query=query,
                sources=sources,
                depth=depth,
                expand_query=expand_query,
                known_context=known_context,
                llm_rerank=llm_rerank,
                progress_callback=progress_cb,
            )
            md = report.markdown()
            quality_info = ""
            overall_score = None
            if report.quality_metrics and hasattr(report.quality_metrics, 'summary'):
                quality_info = f", {report.quality_metrics.summary()}"
                overall_score = report.quality_metrics.overall_score
        else:
            # Standard PeriskopeEngine
            engine = PeriskopeEngine(
                max_results_per_source=max_results,
                verify_citations=True,
            )
            _apply_schedule_override(engine, decay_type, alpha_schedule)

            report = await engine.research(
                query=query,
                sources=sources,
                depth=depth,
                auto_digest=auto_digest,
                multipass=multipass,
                expand_query=expand_query,
                known_context=known_context,
                llm_rerank=llm_rerank,
                progress_callback=progress_cb,
            )

            md = report.markdown()
            quality_info = ""
            overall_score = None
            if report.quality_metrics:
                quality_info = f", {report.quality_metrics.summary()}"
                overall_score = report.quality_metrics.overall_score

    log(
        f"Research complete: {len(getattr(report, 'search_results', getattr(report, 'thesis_search_results', [])))} results, "
        f"{report.elapsed_seconds:.1f}s{quality_info}"
    )
    if hasattr(report, 'reasoning_trace') and report.reasoning_trace and report.reasoning_trace.steps:
        trace = report.reasoning_trace
        log(
            f"CoT trace: {len(trace.steps)} iterations, "
            f"confidence={trace.latest_confidence:.0%}"
        )

    # G7: Auto-log to /sop.track
    try:
        from mekhane.periskope.research_tracker import log_research_run
        log_research_run(
            theme=query[:60],
            query=query,
            depth=depth,
            score=overall_score,
        )
    except Exception as e:  # noqa: BLE001
        log(f"Track auto-log failed (non-fatal): {e}")

    # Generate thinking process artifact (appended to report)
    if thinking_events:
        thinking_md = _format_thinking_trace(thinking_events, report)
        md += "\n\n" + thinking_md

    return [TextContent(type="text", text=md)]


def _format_thinking_trace(events: list[dict], report) -> str:
    """Format accumulated thinking events into a structured artifact section."""
    lines = [
        "---",
        "",
        "## 🧠 思考過程 (Thinking Process)",
        "",
        "> 検索エンジンが辿った認知フロー — 各Phase の判断と発見を時系列で記録",
        "",
    ]

    # Phase timeline
    lines.append("### フェーズ推移")
    lines.append("")
    lines.append("| 経過(秒) | フェーズ | 詳細 |")
    lines.append("|--------:|:--------|:-----|")

    for ev in events:
        t = ev.get("t", 0)
        # label (人間可読) があればそれを使い、なければ phase (イベントID) にフォールバック
        display_phase = ev.get("label", ev.get("phase", "?"))

        # Format detail — strip internal keys
        detail_parts = []
        for k, v in ev.items():
            if k in ("t", "phase", "label"):
                continue
            if v is None:
                continue
            if isinstance(v, list) and len(v) > 3:
                detail_parts.append(f"{k}={len(v)} items")
            elif isinstance(v, dict) and len(v) > 3:
                detail_parts.append(f"{k}={len(v)} entries")
            else:
                detail_parts.append(f"{k}={v}")
        detail_str = ", ".join(detail_parts) if detail_parts else "—"

        lines.append(f"| {t:.1f} | {display_phase} | {detail_str} |")

    lines.append("")

    # Reasoning trace summary (if CoT was used)
    if hasattr(report, 'reasoning_trace') and report.reasoning_trace and report.reasoning_trace.steps:
        trace = report.reasoning_trace
        lines.append("### CoT 推論チェーン")
        lines.append("")
        for step in trace.steps:
            lines.append(f"#### 反復 {step.iteration} (確信度: {step.confidence:.0%})")
            if step.learned:
                lines.append("**学習:**")
                for item in step.learned[:5]:
                    lines.append(f"- {item}")
            if step.contradictions:
                lines.append("**矛盾検出:**")
                for item in step.contradictions[:3]:
                    lines.append(f"- ⚠️ {item}")
            if step.gaps:
                lines.append("**未解決:**")
                for item in step.gaps[:3]:
                    lines.append(f"- ❓ {item}")
            if step.next_queries:
                lines.append("**次の検索:**")
                for q in step.next_queries:
                    lines.append(f"- 🔍 `{q}`")
            lines.append(f"- 情報ゲイン: {step.info_gain:.3f} | 新規結果: +{step.new_results}")
            lines.append("")

    return "\n".join(lines)


# PURPOSE: [L2-auto] handle_search の非同期処理定義
async def handle_search(arguments: dict):
    """Search only (no synthesis/verification)."""
    if PeriskopeEngine is None:
        return [TextContent(type="text", text="Periskopē engine not available")]

    query = arguments.get("query", "")

    # --- Φ0 Research Brief → Query 統合 (periskope_research と同じロジック) ---
    research_brief = arguments.get("research_brief")
    has_brief = False
    if research_brief and isinstance(research_brief, dict):
        brief_parts = []
        bg = research_brief.get("background", "")
        if bg:
            brief_parts.append(f"背景: {bg}")
        questions = research_brief.get("questions", [])
        if questions:
            q_text = " ".join(f"({i+1}) {q}" for i, q in enumerate(questions))
            brief_parts.append(f"問い: {q_text}")
        known = research_brief.get("known_info", "")
        if known:
            brief_parts.append(f"既知: {known}")
        ev = research_brief.get("evidence_type", "")
        if ev:
            brief_parts.append(f"期待する証拠: {ev}")
        cons = research_brief.get("constraints", "")
        if cons:
            brief_parts.append(f"制約: {cons}")
        if brief_parts:
            structured_query = " ".join(brief_parts)
            if query:
                query = f"{query}\n{structured_query}"
            else:
                query = structured_query
            arguments["query"] = query
            has_brief = True
            log(f"📋 Search brief → query: {query[:150]!r}")
    # --- /Φ0 Research Brief → Query 統合 ---

    if not query:
        return [TextContent(type="text", text="Error: query or research_brief is required")]

    # --- Φ0.1 全クエリ構造化: research_brief なし → LLM で調査依頼書に構造化 ---
    if not has_brief:
        try:
            from mekhane.periskope.cognition.phi0_query_fortifier import fortify_query
            log(f"🔧 Structuring search query: {query[:80]!r}")
            fortified = await fortify_query(query)
            if fortified != query:
                log(f"✅ Search query structured → {fortified[:120]!r}")
                query = fortified
                arguments["query"] = query
        except Exception as e:  # noqa: BLE001
            log(f"Query structuring skipped: {e}")
    # --- /Φ0.1 全クエリ構造化 ---

    sources = arguments.get("sources")
    max_results = arguments.get("max_results", 10)
    expand_query = arguments.get("expand_query", True)

    log(f"Search: query={query!r}, sources={sources}")

    with StdoutSuppressor():
        engine = PeriskopeEngine(
            max_results_per_source=max_results,
            verify_citations=False,  # Search only — skip verification
        )
        report = await engine.research(
            query=query,
            sources=sources,
            depth=1,  # L1 — search only, Gemini Flash synthesis
            expand_query=expand_query,
        )

    # Format search results without full synthesis
    lines = [
        f"# Periskopē Search Results",
        f"",
        f"> **Query**: {query}",
        f"> **Time**: {report.elapsed_seconds:.1f}s",
        f"> **Results**: {len(report.search_results)} from {len(report.source_counts)} sources",
        f"",
    ]

    # Source breakdown
    lines.append("## Sources")
    lines.append("")
    lines.append("| Engine | Results |")
    lines.append("|:-------|--------:|")
    for source, count in sorted(report.source_counts.items()):
        lines.append(f"| {source} | {count} |")
    lines.append("")

    # Top results
    lines.append("## Results")
    lines.append("")
    for i, r in enumerate(report.search_results[:30], 1):
        lines.append(f"### [{i}] {r.title}")
        if r.url:
            lines.append(f"- **URL**: {r.url}")
        lines.append(f"- **Source**: {r.source.value}")
        lines.append(f"- **Relevance**: {r.relevance:.2f}")
        snippet = r.snippet or (r.content[:200] if r.content else "")
        if snippet:
            lines.append(f"- **Snippet**: {snippet}")
        lines.append("")

    # Include synthesis if available (L1 = Gemini Flash only)
    if report.synthesis:
        lines.append("## Quick Synthesis")
        lines.append("")
        for s in report.synthesis:
            lines.append(f"### {s.model.value} (Confidence: {s.confidence:.0%})")
            lines.append("")
            lines.append(s.content)
            lines.append("")

    log(f"Search complete: {len(report.search_results)} results, {report.elapsed_seconds:.1f}s")
    return [TextContent(type="text", text="\n".join(lines))]


# PURPOSE: [L2-auto] handle_sources の非同期処理定義
async def handle_sources(arguments: dict):
    """Recommend optimal sources for a query."""
    if PeriskopeEngine is None:
        return [TextContent(type="text", text="Periskopē engine not available")]

    query = arguments.get("query", "")
    if not query:
        return [TextContent(type="text", text="Error: query is required")]

    # F12: Query classification and source recommendation
    qtype = PeriskopeEngine._classify_query(query)
    recommended = PeriskopeEngine.select_sources(query)

    all_sources = {
        "searxng": "SearXNG (メタ検索エンジン — Google, Brave, DuckDuckGo 等を集約)",
        "brave": "Brave Search (プライバシー重視、2,000回/月無料)",
        "tavily": "Tavily (AI向け検索API、1,000回/月無料)",
        "semantic_scholar": "Semantic Scholar (学術論文、無制限)",
        "arxiv": "arXiv (プレプリント全文、APIキー不要)",
        "openalex": "OpenAlex (OA学術メタデータ、100K req/day無料)",
        "github": "GitHub (コード、Issue、PR検索)",
        "gemini_search": "Gemini Search Grounding (Gemini APIのGoogle検索ツール、LLM介在)",
        "google_cse": "Google CSE (Gemini Grounding 互換エイリアス)",
        "vertex_search": "Vertex AI Search (Discovery Engine、純粋なGoogle検索API)",
        "vector_search_ann": "Vertex AI Vector Search (ANN、HGK内部知識ベース高速検索)",
        "stackoverflow": "Stack Overflow (エラー解決、実装方法)",
        "reddit": "Reddit (コミュニティ、最新トレンド)",
        "hackernews": "Hacker News (最新技術ニュース)",
        "gnosis": "Gnōsis (HGK 内部知識ベース)",
        "sophia": "Sophia (HGK Sophia 知識)",
        "kairos": "Kairos (HGK 文脈知識)",
    }

    lines = [
        f"# Periskopē Source Recommendation",
        f"",
        f"> **Query**: {query}",
        f"> **Classification**: {qtype}",
        f"",
        f"## Recommended Sources",
        f"",
    ]
    for s in recommended:
        desc = all_sources.get(s, s)
        lines.append(f"- ✅ **{s}**: {desc}")
    lines.append("")

    lines.append("## All Available Sources")
    lines.append("")
    for s, desc in all_sources.items():
        marker = "✅" if s in recommended else "⬜"
        lines.append(f"- {marker} **{s}**: {desc}")

    return [TextContent(type="text", text="\n".join(lines))]


# PURPOSE: [L2-auto] handle_track の非同期処理定義
async def handle_track(arguments: dict):
    """Research tracking — /sop.track."""
    from mekhane.periskope.research_tracker import (
        create_track, update_progress, log_research_run,
        load_track, list_tracks, format_status,
    )

    action = arguments.get("action", "list")
    theme = arguments.get("theme", "")

    if action == "list":
        tracks = list_tracks()
        if not tracks:
            return [TextContent(type="text", text="調査テーマはまだありません。")]
        lines = ["# 調査テーマ一覧", ""]
        lines.append("| テーマ | 進捗 | 更新日 |")
        lines.append("|:------|-----:|:------|")
        for t in tracks:
            lines.append(f"| {t.theme} | {t.progress_percent}% | {t.updated} |")
        return [TextContent(type="text", text="\n".join(lines))]

    if action == "create":
        if not theme:
            return [TextContent(type="text", text="Error: theme is required")]
        topics = arguments.get("topics", [])
        topic = create_track(theme, topics)
        return [TextContent(type="text", text=format_status(topic))]

    if action == "update":
        if not theme:
            return [TextContent(type="text", text="Error: theme is required")]
        topic = update_progress(
            theme,
            completed=arguments.get("completed"),
            in_progress=arguments.get("in_progress"),
            pending=arguments.get("topics"),
            next_actions=arguments.get("next_actions"),
        )
        return [TextContent(type="text", text=format_status(topic))]

    if action == "log":
        if not theme:
            return [TextContent(type="text", text="Error: theme is required")]
        topic = log_research_run(
            theme,
            query=arguments.get("query", ""),
            depth=arguments.get("depth", 2),
            score=arguments.get("score"),
        )
        return [TextContent(type="text", text=format_status(topic))]

    if action == "status":
        if not theme:
            return [TextContent(type="text", text="Error: theme is required")]
        topic = load_track(theme)
        if not topic:
            return [TextContent(type="text", text=f"テーマ '{theme}' が見つかりません。")]
        return [TextContent(type="text", text=format_status(topic))]

    return [TextContent(type="text", text=f"Unknown action: {action}")]


# PURPOSE: [L2-auto] handle_metrics の非同期処理定義
async def handle_metrics(arguments: dict):
    """品質メトリクスのトレンド照会。"""
    from mekhane.periskope.research_tracker import list_tracks
    limit = int(arguments.get("limit", 10))
    tracks = list_tracks()
    if not tracks:
        return [TextContent(type="text", text="No research tracks found.")]
    
    runs = []
    for t in tracks:
        for h in getattr(t, "depth_history", []):
            if h.get("score") is not None:
                runs.append({
                    "theme": t.theme,
                    "date": h.get("date", "Unknown"),
                    "score": h["score"],
                })
    
    # Sort by date (descending)
    runs.sort(key=lambda x: x["date"], reverse=True)
    recent = runs[:limit]

    if not recent:
        return [TextContent(type="text", text="No scores recorded in recent tracks.")]
    
    avg_score = sum(r["score"] for r in recent) / len(recent)
    
    lines = [f"# Periskopē Quality Metrics (Last {len(recent)} runs)", ""]
    lines.append(f"- **Average Overall Score**: {avg_score:.2f}")
    lines.append("")
    lines.append("| Date | Theme | Score |")
    lines.append("|:---|:---|---:|")
    for r in recent:
        date_str = r["date"].split(" ")[0] if r["date"] else "Unknown"
        lines.append(f"| {date_str} | {r['theme'][:40]}... | {r['score']:.2f} |")
    
    return [TextContent(type="text", text="\n".join(lines))]


# PURPOSE: [L2-auto] handle_benchmark の非同期処理定義
async def handle_benchmark(arguments: dict):
    """複数クエリのベンチマーク実行とメトリクス比較。"""
    if PeriskopeEngine is None:
        return [TextContent(type="text", text="Periskopē engine not available")]

    queries = arguments.get("queries", [])
    if not queries:
        return [TextContent(type="text", text="Error: queries list is required")]

    depth = arguments.get("depth", 1)
    
    # Depth に応じた max_results_per_source (デフォルト10は少なすぎる)
    depth_max_results = {1: 15, 2: 30, 3: 50}
    max_results = depth_max_results.get(depth, 15)
    engine = PeriskopeEngine(
        max_results_per_source=max_results,
        verify_citations=False,
    )
    default_sources = engine._config.get("benchmark_default_sources", ["searxng", "brave", "tavily"])
    
    # Default to fast, reliable sources to avoid timeout with all 14 sources
    sources = arguments.get("sources", default_sources)
    decay_type = arguments.get("decay_type", "")
    alpha_schedule = arguments.get("alpha_schedule", "")
    llm_rerank = arguments.get("llm_rerank", None)
    
    lines = ["# Periskopē Benchmark Results", ""]
    lines.append(f"> **Depth**: L{depth}")
    lines.append(f"> **Queries**: {len(queries)}")
    lines.append(f"> **Sources**: {', '.join(sources)}")
    if decay_type:
        lines.append(f"> **β schedule**: {decay_type}")
    if alpha_schedule:
        lines.append(f"> **α schedule**: {alpha_schedule}")
    lines.append("")
    lines.append("| Query | Results | Srcs | NDCG | Entropy | Cov. | **Score** | Time |")
    lines.append("|:---|---:|---:|---:|---:|---:|---:|---:|")

    # Override schedule config if specified via MCP
    _apply_schedule_override(engine, decay_type, alpha_schedule, prefix="Benchmark ")

    for q in queries:
        log(f"Benchmark running query: {q!r}")
        try:
            with StdoutSuppressor():
                report = await engine.research(
                    query=q,
                    sources=sources,
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
            log(f"Benchmark error for '{q}': {e}")
            import traceback
            log(traceback.format_exc())

    return [TextContent(type="text", text="\n".join(lines))]




if __name__ == "__main__":
    _base.install_all_hooks()
    _base.run()
