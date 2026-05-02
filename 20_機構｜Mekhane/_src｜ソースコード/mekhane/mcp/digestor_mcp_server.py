# PROOF: [L2/インフラ] <- mekhane/mcp/digestor_mcp_server.py A0→MCP経由のアクセスが必要→digestor_mcp_server が担う
#!/usr/bin/env python3
"""
Digestor MCP Server v2.1 - Hegemonikón Knowledge Digestion Pipeline

Tools: list_candidates, run_digestor, get_topics, check_incoming,
       mark_processed, paper_search, paper_details, paper_citations
"""

from pathlib import Path
from mekhane.mcp.mcp_base import MCPBase, StdoutSuppressor
from mekhane.paths import INCOMING_DIR

# Initialize via shared infrastructure
_base = MCPBase(
    name="digestor",
    version="2.1.0",
    instructions="Digestor: Knowledge ingestion pipeline (Gnosis → /eat) + Semantic Scholar API (paper search/details/citations)",
)
server = _base.server
log = _base.log
TextContent = _base.TextContent
Tool = _base.Tool

# Lazy Digestor imports — deferred to first tool use to prevent startup blocking
_DigestorSelector = None
_DigestorPipeline = None


def _get_digestor_modules():
    """Lazy import DigestorSelector and DigestorPipeline on first use."""
    global _DigestorSelector, _DigestorPipeline
    if _DigestorSelector is None:
        try:
            with StdoutSuppressor():
                from mekhane.ergasterion.digestor.selector import DigestorSelector
                from mekhane.ergasterion.digestor.pipeline import DigestorPipeline
            _DigestorSelector = DigestorSelector
            _DigestorPipeline = DigestorPipeline
            log("Digestor imports successful (lazy)")
        except Exception as e:  # noqa: BLE001
            log(f"Digestor import error: {e}")
            log("Will run with stub mode")
    return _DigestorSelector, _DigestorPipeline
# PURPOSE: List available tools.


# PURPOSE: [L2-auto] list_tools の非同期処理定義
@server.list_tools()
# PURPOSE: [L2-auto] List available tools.
async def list_tools():
    """List available tools."""
    return [
        # ── pipeline: 消化パイプライン操作 (5機能統合) ──
        Tool(
            name="digestor_pipeline",
            description=(
                "消化パイプラインの操作。action で選択: "
                "candidates=消化候補リスト, run=パイプライン実行, "
                "topics=対象トピック一覧, incoming=未消化ファイル確認, "
                "processed=消化完了ファイル移動。"
                "Example: digestor_pipeline(action='candidates')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["candidates", "run", "topics", "incoming", "processed"],
                        "description": "操作: candidates(候補), run(実行), topics(トピック), incoming(未消化確認), processed(完了移動)",
                    },
                    # candidates / run 共通
                    "topics": {"type": "array", "items": {"type": "string"}, "description": "対象トピック（省略時は全トピック）"},
                    # candidates
                    "max_candidates": {"type": "integer", "default": 10, "description": "action=candidates 時: 最大候補数"},
                    # run
                    "dry_run": {"type": "boolean", "default": True, "description": "action=run 時: Dry run モード（レポート生成のみ）"},
                    "max_papers": {"type": "integer", "default": 50, "description": "action=run 時: 取得する最大論文数"},
                    # processed
                    "filenames": {"type": "array", "items": {"type": "string"}, "description": "action=processed 時: 移動するファイル名。省略時は全 eat_*.md を移動"},
                },
                "required": ["action"],
            },
        ),
        # ── paper: Semantic Scholar API + ping (4機能統合) ──
        Tool(
            name="digestor_paper",
            description=(
                "Semantic Scholar API + ヘルスチェック。action で選択: "
                "search=論文検索, details=論文詳細, citations=被引用論文, ping=死活確認。"
                "Example: digestor_paper(action='search', query='free energy principle')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["search", "details", "citations", "ping"],
                        "description": "操作: search(検索), details(詳細), citations(被引用), ping(死活)",
                    },
                    # search
                    "query": {"type": "string", "description": "action=search 時: 検索クエリ"},
                    # details / citations
                    "paper_id": {"type": "string", "description": "action=details/citations 時: S2 Paper ID, DOI, or arXiv ID"},
                    # search / citations 共通
                    "limit": {"type": "integer", "default": 10, "description": "action=search/citations 時: 最大件数"},
                },
                "required": ["action"],
            },
        ),
    ]
# PURPOSE: tool calls の安全な処理を保証する


# PURPOSE: [L2-auto] call_tool の非同期処理定義
@server.call_tool()
# PURPOSE: [L2-auto] Handle tool calls.
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    # ── エイリアス層: 旧ツール名 → 新ファサード名にマッピング ──
    _ALIAS = {
        "ping": ("digestor_paper", "ping"),
        "list_candidates": ("digestor_pipeline", "candidates"),
        "run_digestor": ("digestor_pipeline", "run"),
        "get_topics": ("digestor_pipeline", "topics"),
        "check_incoming": ("digestor_pipeline", "incoming"),
        "mark_processed": ("digestor_pipeline", "processed"),
        "paper_search": ("digestor_paper", "search"),
        "paper_details": ("digestor_paper", "details"),
        "paper_citations": ("digestor_paper", "citations"),
    }
    if name in _ALIAS:
        facade, action_val = _ALIAS[name]
        arguments.setdefault("action", action_val)
        name = facade

    try:
        # ── pipeline ファサード ──
        if name == "digestor_pipeline":
            action = arguments.get("action", "candidates")
            if action == "candidates":
                return await handle_list_candidates(arguments)
            elif action == "run":
                return await handle_run_digestor(arguments)
            elif action == "topics":
                return await handle_get_topics(arguments)
            elif action == "incoming":
                return await handle_check_incoming(arguments)
            elif action == "processed":
                return await handle_mark_processed(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown pipeline action: {action}")]
        # ── paper ファサード ──
        elif name == "digestor_paper":
            action = arguments.get("action", "ping")
            if action == "ping":
                return [TextContent(type="text", text="pong")]
            elif action in ("search", "details", "citations"):
                # handle_semantic_scholar は旧ツール名 (paper_search 等) を期待
                old_name = f"paper_{action}"
                return await handle_semantic_scholar(old_name, arguments)
            else:
                return [TextContent(type="text", text=f"Unknown paper action: {action}")]
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:  # noqa: BLE001
        log(f"Tool error: {e}")
# PURPOSE: 消化候補をリスト
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# PURPOSE: list candidates を処理する
async def handle_list_candidates(arguments: dict):
    """消化候補をリスト"""
    _, DigestorPipeline = _get_digestor_modules()
    if DigestorPipeline is None:
        return [TextContent(type="text", text="Digestor module not available")]

    topics = arguments.get("topics")
    max_candidates = arguments.get("max_candidates", 10)

    # pipeline.run() は print() で stdout に出力する → MCP stdio を汚染するため抑制
    with StdoutSuppressor():
        pipeline = DigestorPipeline()
        result = pipeline.run(topics=topics, max_candidates=max_candidates, dry_run=True)

    output = f"=== 消化候補リスト ===\n"
    output += f"総論文数: {result.total_papers}\n"
    output += f"選定候補: {result.candidates_selected}\n\n"

    for i, c in enumerate(result.candidates, 1):
        output += f"{i}. [{c.score:.2f}] {c.paper.title[:60]}...\n"
        output += f"   Topics: {', '.join(c.matched_topics)}\n"
        output += f"   Source: {c.paper.source}\n\n"

# PURPOSE: 消化パイプライン実行
    return [TextContent(type="text", text=output)]


# PURPOSE: run digestor を処理する
async def handle_run_digestor(arguments: dict):
    """消化パイプライン実行"""
    _, DigestorPipeline = _get_digestor_modules()
    if DigestorPipeline is None:
        return [TextContent(type="text", text="Digestor module not available")]

    topics = arguments.get("topics")
    dry_run = arguments.get("dry_run", True)
    max_papers = arguments.get("max_papers", 50)

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
            log(f"[PROGRESS] {event.summary()}")
        except Exception:  # noqa: BLE001
            pass

    _emit("pipeline_start", topics=topics, max_papers=max_papers, dry_run=dry_run)

    # pipeline.run() は print() で stdout に出力する → MCP stdio を汚染するため抑制
    with StdoutSuppressor():
        pipeline = DigestorPipeline()
        result = pipeline.run(
            topics=topics,
            max_papers=max_papers,
            dry_run=dry_run,
        )

    _emit("pipeline_done", total=result.total_papers, candidates=result.candidates_selected)

    output = f"=== Digestor パイプライン {'(Dry Run)' if dry_run else ''} ===\n"
    output += f"Timestamp: {result.timestamp}\n"
    output += f"Source: {result.source}\n"
    output += f"総論文数: {result.total_papers}\n"
    output += f"選定候補: {result.candidates_selected}\n\n"

    if result.candidates:
        output += "消化候補:\n"
        for i, c in enumerate(result.candidates, 1):
            output += f"  {i}. {c.paper.title[:50]}... (score: {c.score:.2f})\n"

    # F4: Falsification matching — check digested papers against epistemic_status.yaml
    _emit("falsification_start")
    try:
        from mekhane.dendron.falsification_matcher import check_falsification, format_alerts

        for c in (result.candidates or []):
            paper_text = f"{c.paper.title} {getattr(c.paper, 'abstract', '')}"
            alerts = check_falsification(paper_text, c.paper.title, threshold=0.4)
            if alerts:
                output += f"\n{format_alerts(alerts, c.paper.title)}\n"
        _emit("falsification_done")
    except Exception as e:  # noqa: BLE001
        log(f"Falsification check skipped: {e}")
        _emit("falsification_skipped", reason=str(e))

    # Append thinking trace
    if thinking_events:
        output += "\n---\n## 🧠 思考過程\n"
        for ev in thinking_events:
            output += f"- {ev}\n"

# PURPOSE: トピック一覧取得
    return [TextContent(type="text", text=output)]


# PURPOSE: get topics を処理する
async def handle_get_topics(arguments: dict):
    """トピック一覧取得"""
    DigestorSelector, _ = _get_digestor_modules()
    if DigestorSelector is None:
        return [TextContent(type="text", text="Digestor module not available")]

    # DigestorSelector の初期化でも stdout に出力される可能性があるため抑制
    with StdoutSuppressor():
        selector = DigestorSelector()
        topics = selector.get_topics()

    output = "=== 消化対象トピック ===\n\n"
    for t in topics:
        output += f"- **{t.get('id')}**: {t.get('description', '')}\n"
        output += f"  Query: {t.get('query', '')}\n"
        digest_to = t.get("digest_to", [])
        if digest_to:
            output += f"  消化先: {', '.join(digest_to)}\n"
        output += "\n"

# PURPOSE: Run the MCP server.
    return [TextContent(type="text", text=output)]


# PURPOSE: incoming/ の未消化ファイルを確認する
async def handle_check_incoming(arguments: dict):
    """incoming/ の未消化ファイルを確認"""
    incoming_dir = INCOMING_DIR

    if not incoming_dir.exists():
        return [TextContent(type="text", text="incoming/ ディレクトリが見つかりません")]

    files = sorted(incoming_dir.glob("eat_*.md"))
    if not files:
        return [TextContent(type="text", text="消化待ちの候補はありません (0 件)")]

    output = f"=== 消化待ち候補: {len(files)} 件 ===\n\n"

    for i, f in enumerate(files, 1):
        # YAML frontmatter からメタデータを抽出
        try:
            content = f.read_text(encoding="utf-8")
            title = "(タイトル不明)"
            score = ""
            topics = ""

            in_frontmatter = False
            for line in content.split("\n"):
                if line.strip() == "---":
                    if in_frontmatter:
                        break
                    in_frontmatter = True
                    continue
                if in_frontmatter:
                    if line.startswith("title:"):
                        title = line.split(":", 1)[1].strip().strip('"\'')
                    elif line.startswith("score:"):
                        score = line.split(":", 1)[1].strip()
                    elif line.startswith("topics:"):
                        topics = line.split(":", 1)[1].strip()

            output += f"{i}. {title}\n"
            if score:
                output += f"   Score: {score}\n"
            if topics:
                output += f"   Topics: {topics}\n"
            output += f"   File: {f.name}\n\n"
        except Exception as e:  # noqa: BLE001
            output += f"{i}. {f.name} (読取エラー: {e})\n\n"

    return [TextContent(type="text", text=output)]


# PURPOSE: 消化完了ファイルを processed/ に移動する
async def handle_mark_processed(arguments: dict):
    """消化完了ファイルを incoming/ → processed/ に移動"""
    _, DigestorPipeline = _get_digestor_modules()
    if DigestorPipeline is None:
        return [TextContent(type="text", text="Digestor module not available")]

    from mekhane.ergasterion.digestor.pipeline import mark_as_processed

    filenames = arguments.get("filenames")
    result = mark_as_processed(filenames=filenames)

    output = f"=== processed/ 移動結果 ===\n"
    output += f"移動成功: {result['count']} 件\n\n"

    for f in result["moved"]:
        output += f"  ✅ {f}\n"
    for e in result["errors"]:
        output += f"  ❌ {e['file']}: {e['error']}\n"

    return [TextContent(type="text", text=output)]


# === Semantic Scholar handlers ===

# PURPOSE: [L2-auto] handle_semantic_scholar の非同期処理定義
async def handle_semantic_scholar(name: str, arguments: dict):
    """Handle Semantic Scholar API tools."""
    try:
        with StdoutSuppressor():
            from mekhane.pks.semantic_scholar import SemanticScholarClient
            import os
            api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
            client = SemanticScholarClient(api_key=api_key)
    except Exception as e:  # noqa: BLE001
        return [TextContent(type="text", text=f"Error initializing S2 client: {e}")]

    if name == "paper_search":
        query = arguments.get("query", "")
        limit = arguments.get("limit", 10)
        if not query:
            return [TextContent(type="text", text="Error: query is required")]
        try:
            papers = client.search(query, limit=min(limit, 100))
            if not papers:
                return [TextContent(type="text", text=f"No results for: {query}")]
            lines = [f'# Semantic Scholar: "{query}"\n', f"Found {len(papers)} results:\n"]
            for i, p in enumerate(papers, 1):
                lines.append(f"## [{i}] {p.title}")
                lines.append(f"- **Year**: {p.year or 'N/A'}")
                lines.append(f"- **Citations**: {p.citation_count}")
                lines.append(f"- **Authors**: {', '.join(p.authors[:5])}")
                if p.abstract:
                    lines.append(f"- **Abstract**: {p.abstract[:300]}...")
                if p.url:
                    lines.append(f"- **URL**: {p.url}")
                if p.doi:
                    lines.append(f"- **DOI**: {p.doi}")
                lines.append("")
            return [TextContent(type="text", text="\n".join(lines))]
        except Exception as e:  # noqa: BLE001
            return [TextContent(type="text", text=f"Error: {e}")]

    elif name == "paper_details":
        paper_id = arguments.get("paper_id", "")
        if not paper_id:
            return [TextContent(type="text", text="Error: paper_id is required")]
        try:
            paper = client.get_paper(paper_id)
            if not paper:
                return [TextContent(type="text", text=f"Paper not found: {paper_id}")]
            lines = [
                f"# {paper.title}\n",
                f"- **Year**: {paper.year or 'N/A'}",
                f"- **Citations**: {paper.citation_count}",
                f"- **Authors**: {', '.join(paper.authors)}",
                f"- **DOI**: {paper.doi or 'N/A'}",
                f"- **arXiv**: {paper.arxiv_id or 'N/A'}",
                f"- **URL**: {paper.url or 'N/A'}",
            ]
            if paper.abstract:
                lines.append(f"\n## Abstract\n\n{paper.abstract}")
            return [TextContent(type="text", text="\n".join(lines))]
        except Exception as e:  # noqa: BLE001
            return [TextContent(type="text", text=f"Error: {e}")]

    elif name == "paper_citations":
        paper_id = arguments.get("paper_id", "")
        limit = arguments.get("limit", 10)
        if not paper_id:
            return [TextContent(type="text", text="Error: paper_id is required")]
        try:
            citations = client.get_citations(paper_id, limit=limit)
            if not citations:
                return [TextContent(type="text", text=f"No citations found for: {paper_id}")]
            lines = [f"# Citations for {paper_id}\n", f"Found {len(citations)} citing papers:\n"]
            for i, p in enumerate(citations, 1):
                lines.append(f"{i}. **{p.title}** ({p.year or '?'}) — {p.citation_count} citations")
            return [TextContent(type="text", text="\n".join(lines))]
        except Exception as e:  # noqa: BLE001
            return [TextContent(type="text", text=f"Error: {e}")]

    return [TextContent(type="text", text=f"Unknown S2 tool: {name}")]




if __name__ == "__main__":
    _base.install_all_hooks()
    _base.run()
