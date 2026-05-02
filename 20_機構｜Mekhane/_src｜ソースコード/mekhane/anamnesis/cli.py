# noqa: AI-ALL
# PROOF: [L2/インフラ] <- mekhane/anamnesis/
"""
PROOF: [L2/インフラ] このファイルは存在しなければならない

P3 → 記憶の永続化が必要
   → 永続化の操作インタフェースが必要
   → cli.py が担う

Q.E.D.

---

Gnōsis CLI - コマンドラインインタフェース

Usage:
    python -m mekhane.anamnesis.cli collect --source arxiv --query "transformer" --limit 10
    python mekhane/anamnesis/cli.py search "attention mechanism"
    python mekhane/anamnesis/cli.py stats
"""

import argparse
import sys
from pathlib import Path
import json
from datetime import datetime, timedelta

# Add Hegemonikon root to path for imports (mekhane package)
_THIS_DIR = Path(__file__).parent
_HEGEMONIKON_ROOT = (
    _THIS_DIR.parent.parent
)  # mekhane/anamnesis -> mekhane -> Hegemonikon
if str(_HEGEMONIKON_ROOT) not in sys.path:
    sys.path.insert(0, str(_HEGEMONIKON_ROOT))

from mekhane.paths import GNOSIS_DATA_DIR, HANDOFF_DIR, SESSIONS_DIR
from mekhane.symploke.handoff_files import list_handoff_files

# Configuration
DATA_DIR = GNOSIS_DATA_DIR
STATE_FILE = DATA_DIR / "state.json"


# PURPOSE: GnosisIndex 用 --backend をサブコマンドに付与
def _add_backend_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--backend",
        "-B",
        choices=("faiss", "numpy"),
        default="faiss",
        help="Vector store backend: faiss (default) or numpy if faiss is unavailable",
    )


# PURPOSE: argparse args から GnosisIndex を構築
def _gnosis_index(args):
    from mekhane.anamnesis.index import GnosisIndex

    return GnosisIndex(backend=getattr(args, "backend", "faiss"))


# PURPOSE: Update last collected timestamp.
def update_state():
    """Update last collected timestamp."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        state = {}
        if STATE_FILE.exists():
            try:
                state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                pass  # TODO: Add proper error handling # noqa: AI-ALL

        state["last_collected_at"] = datetime.now().isoformat()
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        print(f"[Warning] Failed to update state: {e}")


# PURPOSE: Check if collection is needed based on threshold days.
def cmd_check_freshness(args):
    """
    Check if collection is needed based on threshold days.
    Output JSON: {"status": "fresh"|"stale"|"missing", "days_elapsed": int|null}
    """
    threshold = timedelta(days=args.threshold)
    result = {"status": "missing", "days_elapsed": None}

    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            last_str = state.get("last_collected_at")
            if last_str:
                last_time = datetime.fromisoformat(last_str)
                elapsed = datetime.now() - last_time
                days = elapsed.days

                if elapsed > threshold:
                    result = {"status": "stale", "days_elapsed": days}
                else:
                    result = {"status": "fresh", "days_elapsed": days}
        except Exception:  # noqa: BLE001
            result = {"status": "error", "days_elapsed": None}

    print(json.dumps(result))
    # Return 0 if fresh, 1 if stale/missing (to allow simple shell checks) # noqa: AI-ALL
    return 0 if result["status"] == "fresh" else 1


# PURPOSE: 論文収集
def cmd_collect(args):
    """論文収集"""
    from mekhane.anamnesis.collectors.arxiv import ArxivCollector
    from mekhane.anamnesis.collectors.semantic_scholar import SemanticScholarCollector
    from mekhane.anamnesis.collectors.openalex import OpenAlexCollector

    collectors = {
        "arxiv": ArxivCollector,
        "semantic_scholar": SemanticScholarCollector,
        "s2": SemanticScholarCollector,
        "openalex": OpenAlexCollector,
        "oa": OpenAlexCollector,
    }

    source = args.source.lower()
    if source not in collectors:
        print(f"Unknown source: {args.source}")
        print(f"Available: {', '.join(collectors.keys())}")
        return 1

    print(f"[Collect] Source: {source}, Query: {args.query}, Limit: {args.limit}")

    try:
        collector = collectors[source]()
        papers = collector.search(args.query, max_results=args.limit)
        print(f"[Collect] Found {len(papers)} papers")

        if papers and not args.dry_run:
            index = _gnosis_index(args)
            added = index.add_papers(papers)
            print(f"[Collect] Added {added} to index")
            update_state()  # Update timestamp
        elif args.dry_run:
            print("[Collect] Dry run - not adding to index")
            for p in papers[:5]:
                print(f"  - {p.title[:60]}...")

        return 0
    except Exception as e:  # noqa: BLE001
        print(f"[Error] {e}")
        return 1


# PURPOSE: 全ソースから収集
def cmd_collect_all(args):  # noqa: AI-ALL
    """全ソースから収集"""
    from mekhane.anamnesis.collectors.arxiv import ArxivCollector
    from mekhane.anamnesis.collectors.semantic_scholar import SemanticScholarCollector
    from mekhane.anamnesis.collectors.openalex import OpenAlexCollector

    collectors = [
        ("arxiv", ArxivCollector()),
        ("semantic_scholar", SemanticScholarCollector()),
        ("openalex", OpenAlexCollector()),
    ]

    print(f"[CollectAll] Query: {args.query}, Limit per source: {args.limit}")

    all_papers = []
    for name, collector in collectors:
        try:
            print(f"  Collecting from {name}...")
            papers = collector.search(args.query, max_results=args.limit)
            print(f"    Found {len(papers)} papers")
            all_papers.extend(papers)
        except Exception as e:  # noqa: BLE001
            print(f"    Error: {e}")

    if all_papers and not args.dry_run:
        index = _gnosis_index(args)
        added = index.add_papers(all_papers, dedupe=True)
        print(f"[CollectAll] Added {added} unique papers to index")
        update_state()  # Update timestamp

    return 0


# PURPOSE: 論文検索 (ハイブリッド・拡充対応)
def cmd_search(args):
    """Semantic search with optional hybrid mode and query expansion."""
    source_filter = getattr(args, "source", None)
    hybrid = getattr(args, "hybrid", False)
    expand = getattr(args, "expand", False)
    
    queries = [args.query]
    if expand:
        import asyncio
        from mekhane.periskope.query_expander import QueryExpander
        print("[Search] Expanding query via Cortex API...")
        expander = QueryExpander(timeout=10.0)
        expanded = asyncio.run(expander.expand(args.query))
        if expanded:
            queries = expanded
        print(f"[Search] Effective queries: {queries}")

    filter_msg = f" (source={source_filter})" if source_filter else ""
    hybrid_msg = " [hybrid]" if hybrid else ""
    print(f"[Search] Initial Query: {args.query}{filter_msg}{hybrid_msg}")

    index = _gnosis_index(args)
    
    all_results = []
    seen_pks = set()
    
    for q in queries:
        results = index.search(
            q, k=args.limit,
            source_filter=source_filter, hybrid=hybrid,
        )
        for r in results:
            pk = r.get("primary_key")
            if pk and pk not in seen_pks:
                seen_pks.add(pk)
                all_results.append(r)
                
    # Re-sort combined results
    if hybrid:
        all_results.sort(key=lambda x: x.get("_rrf_score", 0.0), reverse=True)
    else:
        # Lower distance is better
        all_results.sort(key=lambda x: x.get("_distance", 999.0))
        
    final_results = all_results[:args.limit]

    if not final_results:
        print("No results found")
        return 0

    print(f"\nFound {len(final_results)} results (from {len(all_results)} total candidates):\n")
    print("-" * 70)

    for i, r in enumerate(final_results, 1):
        rrf = r.get('_rrf_score')
        score_str = f" | RRF={rrf:.4f}" if rrf else ""
        print(f"\n[{i}] {r.get('title', 'Untitled')[:70]}")
        print(f"    Source: {r.get('source')} | Citations: {r.get('citations', 'N/A')}{score_str}")
        print(f"    Authors: {r.get('authors', '')[:60]}...")
        print(f"    Abstract: {r.get('abstract', '')[:150]}...")
        if r.get("url"):
            print(f"    URL: {r.get('url')}")

    print("\n" + "-" * 70)
    return 0


# PURPOSE: インデックス統計
def cmd_stats(args):
    """インデックス統計"""
    index = _gnosis_index(args)
    stats = index.stats()

    print("\n[Gnōsis Index Statistics]")
    print("=" * 40)
    print(f"Total Papers: {stats['total']}")
    print(f"With DOI: {stats.get('unique_dois', 0)}")
    print(f"With arXiv ID: {stats.get('unique_arxiv', 0)}")
    print("\nBy Source:")
    for source, count in stats.get("sources", {}).items():
        print(f"  {source}: {count}")

    # Show freshness
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            print(f"Last Collected: {state.get('last_collected_at', 'Unknown')}")
        except Exception:  # noqa: BLE001
            pass  # TODO: Add proper error handling # noqa: AI-ALL

    print("=" * 40)

    return 0


# PURPOSE: PKS 能動的プッシュ
def cmd_proactive(args):
    """PKS 能動的プッシュ"""
    from mekhane.pks.pks_engine import PKSEngine
    from mekhane.pks.narrator import PKSNarrator
    from mekhane.pks.matrix_view import PKSMatrixView

    # コンテキスト設定
    topics = [t.strip() for t in args.context.split(",")] if args.context else []

    if not topics:
        print("[PKS] --context を指定してください (例: --context 'FEP,CCL')")
        return 1

    engine = PKSEngine(threshold=args.threshold, max_push=args.limit)
    engine.set_context(topics=topics)

    print(f"[PKS] Context: {topics}")
    print(f"[PKS] Threshold: {args.threshold}, Max: {args.limit}")
    print()

    nuggets = engine.proactive_push(k=args.limit * 4)

    if not nuggets:
        print("📭 プッシュ対象の知識はありません。")
        return 0

    # Push Report
    print(engine.format_push_report(nuggets))

    # Narrator (--narrate)
    if args.narrate:
        narrator = PKSNarrator()
        narratives = narrator.narrate_batch(nuggets[:3])
        print()
        print(narrator.format_report(narratives))

    # Matrix View (--matrix)
    if args.matrix:
        matrix = PKSMatrixView()
        print()
        print(matrix.generate(nuggets))

    return 0


# PURPOSE: Link Engine — ファイル間リレーション解析
def cmd_links(args):
    """Link Engine — ファイル間リレーション解析"""
    from mekhane.pks.links.link_engine import LinkEngine

    target_dir = Path(args.directory).resolve()
    if not target_dir.exists():
        print(f"[Links] Directory not found: {target_dir}")
        return 1

    engine = LinkEngine(target_dir)
    idx = engine.build_index()

    if args.backlinks:
        # 特定ファイルの backlinks
        links = engine.get_backlinks(args.backlinks)
        print(f"\n[Backlinks for '{args.backlinks}'] {len(links)} found:\n")
        for link in links:
            print(f"  ← {link.source}:{link.line_number}  context: {link.context[:60]}")
        return 0

    if args.orphans:
        orphans = engine.get_orphans()
        print(f"\n[Orphans] {len(orphans)} files with no incoming links:\n")
        for o in orphans:
            print(f"  • {o}")
        return 0

    if args.graph == "json":
        print(engine.export_graph_json())
        return 0

    if args.graph == "mermaid":
        print(engine.export_graph_mermaid())
        return 0

    # Default: summary
    print(engine.summary_markdown())
    return 0


# PURPOSE: CLI エントリポイント — 知識基盤の直接実行
def main():
    parser = argparse.ArgumentParser(
        description="Gnōsis - Knowledge Foundation CLI",
        prog="gnosis",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # collect
    p_collect = subparsers.add_parser("collect", help="Collect papers from a source")
    p_collect.add_argument(
        "--source", "-s", required=True, help="Source: arxiv, s2, openalex"
    )
    p_collect.add_argument("--query", "-q", required=True, help="Search query")
    p_collect.add_argument("--limit", "-l", type=int, default=10, help="Max results")
    p_collect.add_argument("--dry-run", action="store_true", help="Don't add to index")
    _add_backend_arg(p_collect)
    p_collect.set_defaults(func=cmd_collect)

    # collect-all
    p_all = subparsers.add_parser("collect-all", help="Collect from all sources")
    p_all.add_argument("--query", "-q", required=True, help="Search query")
    p_all.add_argument(
        "--limit", "-l", type=int, default=10, help="Max results per source"
    )
    p_all.add_argument("--dry-run", action="store_true", help="Don't add to index")
    _add_backend_arg(p_all)
    p_all.set_defaults(func=cmd_collect_all)

    # search
    p_search = subparsers.add_parser("search", help="Search indexed papers")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--limit", "-l", type=int, default=10, help="Max results")
    p_search.add_argument(
        "--source", "-s", default=None,
        help="Filter by source (arxiv, session, handoff, etc.)"
    )
    p_search.add_argument(
        "--hybrid", "-H", action="store_true", default=False,
        help="Enable hybrid search (Vector + Full-Text)"
    )
    p_search.add_argument(
        "--expand", "-E", action="store_true", default=False,
        help="Expand query via Gemini translation (requires Cortex API)"
    )
    _add_backend_arg(p_search)
    p_search.set_defaults(func=cmd_search)

    # bench (Search Quality Benchmark)
    def cmd_bench(args):
        """Search quality benchmark using golden set."""
        from mekhane.anamnesis.search_metrics import evaluate, format_report, compare_modes
        golden = args.golden
        if args.compare:
            print(compare_modes(golden, backend=args.backend))
        else:
            result = evaluate(golden, hybrid=args.hybrid, backend=args.backend)
            print(format_report(result))
        return 0

    p_bench = subparsers.add_parser("bench", help="Search quality benchmark")
    p_bench.add_argument(
        "--golden", "-g",
        default=str(Path(__file__).parent / "golden_set.yaml"),
        help="Path to golden set YAML",
    )
    p_bench.add_argument(
        "--hybrid", "-H", action="store_true",
        help="Use hybrid search mode",
    )
    p_bench.add_argument(
        "--compare", "-C", action="store_true",
        help="Compare vector vs hybrid modes",
    )
    _add_backend_arg(p_bench)
    p_bench.set_defaults(func=cmd_bench)

    # stats
    p_stats = subparsers.add_parser("stats", help="Show index statistics")
    _add_backend_arg(p_stats)
    p_stats.set_defaults(func=cmd_stats)

    # build-fts (FTS インデックス構築)
    def cmd_build_fts(args):
        """Build Full-Text Search index for hybrid search."""
        index = _gnosis_index(args)
        fields = args.fields.split(",") if args.fields else None
        success = index.build_fts_index(fields=fields)
        return 0 if success else 1

    p_fts = subparsers.add_parser("build-fts", help="Build FTS index for hybrid search")
    p_fts.add_argument(
        "--fields", "-f", default=None,
        help="Comma-separated fields to index (default: title,abstract)"
    )
    _add_backend_arg(p_fts)
    p_fts.set_defaults(func=cmd_build_fts)

    # reindex (ソース単位の再インデックス)
    def cmd_reindex(args):
        """Drop and re-index a specific source with chunking support."""
        source = args.source
        valid_sources = ["handoff", "rom", "session", "conversation", "export", "step"]
        if source not in valid_sources:
            print(f"[Reindex] Unknown source: {source}")
            print(f"  Valid: {', '.join(valid_sources)}")
            return 1

        index = _gnosis_index(args)

        # Step 1: Drop existing records
        if not args.no_drop:
            dropped = index.drop_source(source)
            print(f"[Reindex] Dropped {dropped} old '{source}' records")

        # Step 2: Re-index based on source type
        if source == "handoff":
            from mekhane.anamnesis.session_indexer import index_handoffs
            return index_handoffs(args.directory)
        elif source == "rom":
            from mekhane.anamnesis.session_indexer import index_roms
            return index_roms(args.directory)
        elif source == "export":
            from mekhane.anamnesis.session_indexer import index_exports
            return index_exports(args.directory)
        elif source == "step":
            from mekhane.anamnesis.session_indexer import index_steps
            return index_steps(args.directory)
        else:
            print(f"[Reindex] Source '{source}' requires manual re-indexing via its specific command")
            return 0

    p_reindex = subparsers.add_parser("reindex", help="Drop and re-index a source (with chunking)")
    p_reindex.add_argument("source", help="Source to reindex: handoff, rom, export, step")
    p_reindex.add_argument(
        "--directory", "-d", default=None,
        help="Custom directory for source files"
    )
    p_reindex.add_argument(
        "--no-drop", action="store_true",
        help="Skip dropping old records (append only)"
    )
    _add_backend_arg(p_reindex)
    p_reindex.set_defaults(func=cmd_reindex)

    # migrate-dim (768d/1024d -> 3072d migration)
    def cmd_migrate_dim(args):
        """Migrate Gnōsis index from 768d/1024d to 3072d format."""
        import sys
        import subprocess
        script_path = _HEGEMONIKON_ROOT / "scripts" / "reindex_gnosis.py"
        idx_args = [sys.executable, str(script_path)]
        if args.dry_run:
            idx_args.append("--dry-run")
        if args.batch_size:
            idx_args.extend(["--batch-size", str(args.batch_size)])
        # Execute the script out-of-process to avoid deep import conflicts
        print(f"[CLI] Running: {' '.join(idx_args)}")
        return subprocess.call(idx_args)

    p_migrate = subparsers.add_parser("migrate-dim", help="Migrate index vectors to 3072d")
    p_migrate.add_argument("--dry-run", action="store_true", help="Print stats and skip migration")
    p_migrate.add_argument("--batch-size", type=int, default=32, help="Embedding batch size (default: 32)")
    p_migrate.set_defaults(func=cmd_migrate_dim)

    # check-freshness
    p_check = subparsers.add_parser(
        "check-freshness", help="Check collection freshness"
    )
    p_check.add_argument(
        "--threshold", "-t", type=int, default=7, help="Threshold days (default: 7)"
    )
    p_check.set_defaults(func=cmd_check_freshness)

    # logs (Antigravity Output Panel Logs)
    from mekhane.anamnesis.antigravity_logs import cmd_logs

    p_logs = subparsers.add_parser("logs", help="Antigravity Output Panel logs")
    p_logs.add_argument(
        "--session", "-s", help="Session ID (timestamp, e.g. 20260125T145530)"
    )
    p_logs.add_argument(
        "--list", "-L", action="store_true", help="List available sessions"
    )
    p_logs.add_argument("--errors", "-e", action="store_true", help="Show errors only")
    p_logs.add_argument(
        "--models", "-m", action="store_true", help="Show detected models only"
    )
    p_logs.add_argument(
        "--tokens", "-t", action="store_true", help="Show token usage only"
    )
    p_logs.add_argument("--limit", "-l", type=int, default=10, help="Max items to show")
    p_logs.set_defaults(func=cmd_logs)

    # proactive (PKS Push)
    p_proactive = subparsers.add_parser(
        "proactive", help="PKS proactive knowledge push"
    )
    p_proactive.add_argument(
        "--context", "-c", required=True, help="Topics (comma-separated)"
    )
    p_proactive.add_argument(
        "--threshold", "-T", type=float, default=0.5, help="Relevance threshold"
    )
    p_proactive.add_argument(
        "--limit", "-l", type=int, default=5, help="Max push count"
    )
    p_proactive.add_argument(
        "--narrate", "-n", action="store_true", help="Include Narrator dialogue"
    )
    p_proactive.add_argument(
        "--matrix", "-m", action="store_true", help="Include Matrix comparison table"
    )
    p_proactive.set_defaults(func=cmd_proactive)

    # links (Link Engine)
    p_links = subparsers.add_parser("links", help="File link analysis")
    p_links.add_argument(
        "directory", nargs="?", default=".", help="Target directory (default: cwd)"
    )
    p_links.add_argument(
        "--backlinks", "-b", help="Show backlinks for a specific file/stem"
    )
    p_links.add_argument(
        "--orphans", "-o", action="store_true", help="Show orphan files"
    )
    p_links.add_argument(
        "--graph", "-g", choices=["json", "mermaid"], help="Export graph format"
    )
    p_links.set_defaults(func=cmd_links)

    # chat (Gnōsis Chat — RAG 対話)
    from mekhane.anamnesis.gnosis_chat import cmd_chat

    p_chat = subparsers.add_parser(
        "chat", help="Interactive RAG chat with knowledge base"
    )
    p_chat.add_argument(
        "question", nargs="?", default=None,
        help="Question to ask (omit for interactive mode)"
    )
    p_chat.add_argument(
        "--top-k", "-k", type=int, default=5,
        help="Number of documents to retrieve (default: 5)"
    )
    p_chat.add_argument(
        "--max-tokens", "-m", type=int, default=512,
        help="Max tokens to generate (default: 512)"
    )
    p_chat.add_argument(
        "--index", "-i", action="store_true",
        help="Index all knowledge files before chatting"
    )
    p_chat.add_argument(
        "--steering", "-s", default="hegemonikon",
        choices=["hegemonikon", "neutral", "academic"],
        help="Steering profile (default: hegemonikon)"
    )
    _add_backend_arg(p_chat)
    p_chat.set_defaults(func=cmd_chat)

    # session-index (Session History Vector Search)
    # PURPOSE: [L2-auto] セッション履歴をインデックス
    def cmd_session_index(args):
        """セッション履歴をインデックス"""
        from mekhane.anamnesis.session_indexer import index_from_api, index_from_json
        if args.json_path:
            return index_from_json(args.json_path)
        return index_from_api()

    p_session = subparsers.add_parser(
        "session-index", help="Index session history into GnosisIndex"
    )
    p_session.add_argument(
        "json_path", nargs="?", default=None,
        help="Path to trajectories_raw.json (omit to fetch from API)"
    )
    p_session.set_defaults(func=cmd_session_index)

    # handoff-index (Handoff VSearch)
    # PURPOSE: [L2-auto] Handoff ファイルをインデックス
    def cmd_handoff_index(args):
        """Handoff ファイルをインデックス"""
        from mekhane.anamnesis.session_indexer import index_handoffs
        return index_handoffs(args.handoff_dir)

    p_handoff = subparsers.add_parser(
        "handoff-index", help="Index handoff_*.md files into GnosisIndex"
    )
    p_handoff.add_argument(
        "--handoff-dir", default=None,
        help="Custom handoff directory (default: ~/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff)"
    )
    p_handoff.set_defaults(func=cmd_handoff_index)

    # rom-index (ROM VSearch)
    # PURPOSE: [L2-auto] ROM ファイルをインデックス
    def cmd_rom_index(args):
        """ROM ファイルをインデックス"""
        from mekhane.anamnesis.session_indexer import index_roms
        return index_roms(args.rom_dir)

    p_rom = subparsers.add_parser(
        "rom-index", help="Index rom_*.md files into GnosisIndex"
    )
    p_rom.add_argument(
        "--rom-dir", default=None,
        help="Custom ROM directory (default: ~/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom)"
    )
    p_rom.set_defaults(func=cmd_rom_index)

    # wal-index (Intent-WAL VSearch)
    # PURPOSE: [L2-auto] WAL ファイルをインデックス
    def cmd_wal_index(args):
        """Intent-WAL ファイルをインデックス"""
        from mekhane.anamnesis.session_indexer import index_wals
        return index_wals(args.wal_dir)

    p_wal = subparsers.add_parser(
        "wal-index", help="Index intent_wal_*.yaml files into GnosisIndex"
    )
    p_wal.add_argument(
        "--wal-dir", default=None,
        help="Custom WAL directory (default: ~/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff)"
    )
    p_wal.set_defaults(func=cmd_wal_index)

    # conversation-index (Full Conversation Content VSearch)
    # PURPOSE: [L2-auto] 全セッション会話をインデックス
    def cmd_conversation_index(args):
        """全セッション会話をインデックス"""
        from mekhane.anamnesis.session_indexer import index_conversations
        return index_conversations(args.max_sessions)

    p_conv = subparsers.add_parser(
        "conversation-index", help="Index full conversation content from LS API"
    )
    p_conv.add_argument(
        "--max-sessions", type=int, default=100,
        help="Max sessions to index (default: 100)"
    )
    p_conv.set_defaults(func=cmd_conversation_index)

    # session-dash (Session Quality Dashboard)
    # PURPOSE: [L2-auto] セッション品質ダッシュボード
    def cmd_session_dash(args):
        """Session quality dashboard: index stats + handoff compression + recurrence rate."""
        import numpy as np

        print("=" * 60)
        print(" 🧠 HEGEMONIKÓN SESSION QUALITY DASHBOARD")
        print("=" * 60)

        # --- インデックス統計 ---
        index = _gnosis_index(args)
        try:
            df_export = index.filter_to_pandas("source = 'export'")
            total_chunks = len(df_export)

            session_vectors = {}
            for _, row in df_export.iterrows():
                url = row.get("url", "")
                if not url:
                    continue
                if url not in session_vectors:
                    session_vectors[url] = []
                session_vectors[url].append(np.array(row["vector"]))

            session_rep = {u: np.mean(v, axis=0) for u, v in session_vectors.items()}
            total_sessions = len(session_rep)

            # Recurrence count (>0.95 cosine)
            urls = list(session_rep.keys())
            recurrences = 0
            for i in range(len(urls)):
                for j in range(i + 1, len(urls)):
                    v1, v2 = session_rep[urls[i]], session_rep[urls[j]]
                    dot = np.dot(v1, v2)
                    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
                    if norm > 0 and (dot / norm) > 0.95:
                        recurrences += 1
                        break
        except Exception:  # noqa: BLE001
            total_chunks, total_sessions, recurrences = 0, 0, 0

        print(f"\n[ GnosisIndex Vector Store ]")
        print(f"  Indexed Sessions : {total_sessions}")
        print(f"  Semantic Chunks  : {total_chunks:,}")
        if total_sessions > 0:
            print(f"  Recurrence Rate  : {recurrences / total_sessions:.1%} ({recurrences} highly similar sessions)")

        # --- Handoff compression ---
        sessions_dir = SESSIONS_DIR
        handoff_dir = HANDOFF_DIR
        export_files = list(sessions_dir.glob("*_conv_*.md"))
        handoff_files = list_handoff_files(handoff_dir)

        c_export = len(export_files)
        c_handoff = len(handoff_files)
        avg_export = sum(f.stat().st_size for f in export_files) / c_export if c_export else 0
        avg_handoff = sum(f.stat().st_size for f in handoff_files) / c_handoff if c_handoff else 0
        ratio = avg_handoff / avg_export if avg_export > 0 else 0

        print(f"\n[ Handoff Compression ]")
        print(f"  Full Sessions    : {c_export} files")
        print(f"  Handoffs Saved   : {c_handoff} files")
        print(f"  Avg Session Size : {avg_export / 1024:.1f} KB")
        print(f"  Avg Handoff Size : {avg_handoff / 1024:.1f} KB")
        if ratio > 0:
            print(f"  Compression Ratio: {ratio:.2%} ({int(1 / ratio)}x Reduction)")

        print(f"\n[ Diagnostic Summary ]")
        if ratio > 0 and ratio < 0.05:
            print("  🟢 Handoff Quality: EXCELLENT (High Compression)")
        elif ratio > 0:
            print("  🟡 Handoff Quality: WARNING (Low Compression)")

        if total_sessions > 0 and recurrences / total_sessions < 0.1:
            print("  🟢 Recurrence Rate: HEALTHY")
        elif total_sessions > 0:
            print("  🟡 Recurrence Rate: WARNING (Consider extracting patterns to KB)")

        print("=" * 60)
        return 0

    p_dash = subparsers.add_parser(
        "session-dash", help="Session quality dashboard (stats + compression + recurrence)"
    )
    _add_backend_arg(p_dash)
    p_dash.set_defaults(func=cmd_session_dash)

    # recurrence (Recurrent Session Detection)
    # PURPOSE: [L2-auto] 再発セッション検出
    def cmd_recurrence(args):
        """Detect highly similar sessions (potential recurrence patterns)."""
        import numpy as np

        threshold = args.threshold

        index = _gnosis_index(args)
        df = index.filter_to_pandas("source = 'export'")

        session_vectors = {}
        session_titles = {}
        for _, row in df.iterrows():
            url = row.get("url", "")
            title = row.get("title", "Untitled")
            if not url:
                continue
            if url not in session_vectors:
                session_vectors[url] = []
                session_titles[url] = title.split(" (")[0]
            session_vectors[url].append(np.array(row["vector"]))

        session_rep = {u: np.mean(v, axis=0) for u, v in session_vectors.items()}
        urls = list(session_rep.keys())

        similarities = []
        for i in range(len(urls)):
            for j in range(i + 1, len(urls)):
                u1, u2 = urls[i], urls[j]
                v1, v2 = session_rep[u1], session_rep[u2]
                dot = np.dot(v1, v2)
                norm = np.linalg.norm(v1) * np.linalg.norm(v2)
                sim = dot / norm if norm > 0 else 0
                if sim > threshold:
                    similarities.append((sim, u1, u2, session_titles[u1], session_titles[u2]))

        similarities.sort(key=lambda x: x[0], reverse=True)

        if not similarities:
            print(f"No recurrent sessions found above threshold {threshold:.2f}")
            return 0

        print(f"\n=== Recurrent Sessions (Similarity > {threshold:.2f}) ===\n")
        for sim, u1, u2, t1, t2 in similarities[: args.limit]:
            print(f"Similarity: {sim:.3f}")
            print(f"  A: {t1} ({u1})")
            print(f"  B: {t2} ({u2})")
            print("-" * 40)

        print(f"\nTotal: {len(similarities)} pairs above threshold")
        return 0

    p_recurrence = subparsers.add_parser(
        "recurrence", help="Detect highly similar (recurrent) sessions"
    )
    p_recurrence.add_argument(
        "--threshold", "-t", type=float, default=0.95,
        help="Cosine similarity threshold (default: 0.95)"
    )
    p_recurrence.add_argument(
        "--limit", "-l", type=int, default=20,
        help="Max pairs to show (default: 20)"
    )
    _add_backend_arg(p_recurrence)
    p_recurrence.set_defaults(func=cmd_recurrence)

    # retrieve (LLM 不使用 — 検索結果のみ返す)
    from mekhane.anamnesis.gnosis_chat import cmd_retrieve

    p_retrieve = subparsers.add_parser(
        "retrieve", help="Retrieve context only (no LLM generation)"
    )
    p_retrieve.add_argument(
        "query", help="Search query"
    )
    p_retrieve.add_argument(
        "--top-k", "-k", type=int, default=5,
        help="Number of documents to retrieve (default: 5)"
    )
    _add_backend_arg(p_retrieve)
    p_retrieve.set_defaults(func=cmd_retrieve)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
