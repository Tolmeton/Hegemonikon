# PROOF: [L2/インフラ] <- mekhane/mcp/mneme_server.py A0→MCP経由のアクセスが必要→phantazein query server が担う (旧 mneme)
#!/usr/bin/env python3
"""
Phantazein Query Server v1.1 (旧 Mneme MCP Server) - Hegemonikón Symplokē Integration

Unified knowledge search: Gnōsis papers + Sophia KI + Kairos handoffs + Chronos chat
Query interface to the Phantasia Field (unified meaning space).
"""

import asyncio
import traceback
from pathlib import Path
from mekhane.mcp.mcp_base import MCPBase, StdoutSuppressor

_base = MCPBase(
    name="phantazein",
    version="1.1.0",
    instructions="Phantazein: Hegemonikón unified knowledge server — query interface to the Phantasia Field (Gnōsis papers + Sophia KI + Kairos handoffs + Chronos chat)",
)
server = _base.server
log = _base.log
TextContent = _base.TextContent
Tool = _base.Tool

# Import Symplokē components
try:
    with StdoutSuppressor():
        from mekhane.symploke.search.engine import SearchEngine
        from mekhane.symploke.adapters.vector_store import VectorStore
        from mekhane.symploke.indices import (
            GnosisIndex,
            ChronosIndex,
            SophiaIndex,
            KairosIndex,
        )
        from mekhane.symploke.indices.gnosis_bridge import GnosisBridge
    log("Symplokē imports successful (VectorStore + LanceBridge mode)")
except Exception as e:  # noqa: BLE001
    log(f"Symplokē import error: {e}")
    SearchEngine = None
    GnosisBridge = None


# ============ Auto-rebuild helpers ============
# PURPOSE: sophia.pkl の差分更新 (manifest ベース)
def _auto_rebuild_sophia(indices_dir: 'Path', log):
    """sophia.pkl を差分更新 (incremental rebuild)。"""
    sophia_pkl = indices_dir / "sophia.pkl"
    try:
        from mekhane.symploke.sophia_ingest import incremental_rebuild_sophia
        stats = incremental_rebuild_sophia(str(sophia_pkl))
        log(f"sophia incremental: +{stats['added']} ~{stats['updated']} -{stats['deleted']} ={stats['unchanged']} (total {stats['total']})")
    except Exception as e:  # noqa: BLE001
        log(f"sophia auto-rebuild failed (non-fatal): {e}")


# PURPOSE: code.pkl / code_ccl.pkl の差分更新 (manifest ベース)
def _auto_rebuild_code(code_pkl: 'Path', code_ccl_pkl: 'Path', log):
    """code.pkl / code_ccl.pkl を差分更新 (incremental rebuild)。"""
    try:
        from mekhane.symploke.code_ingest import (
            incremental_rebuild_code,
            incremental_rebuild_code_ccl,
        )
        stats = incremental_rebuild_code(str(code_pkl))
        log(f"code incremental: +{stats['added']} ~{stats['updated']} -{stats['deleted']} ={stats['unchanged']} (total {stats['total']})")

        ccl_stats = incremental_rebuild_code_ccl(str(code_ccl_pkl))
        log(f"code_ccl incremental: +{ccl_stats['added']} ~{ccl_stats['updated']} -{ccl_stats['deleted']} ={ccl_stats['unchanged']} (total {ccl_stats['total']})")

    except Exception as e:  # noqa: BLE001
        log(f"code auto-rebuild failed (non-fatal): {e}")


# ============ Initialize SearchEngine ============
# PURPOSE: Lazy initialization of SearchEngine.
_engine = None
_vertex_embedder = None  # Shared VertexEmbedder instance
_rebuild_thread = None  # バックグラウンド再構築スレッド
_DOC_SEARCH_SOURCES = ("gnosis", "sophia", "hgk_core", "chronos", "kairos")
_CODE_SEARCH_SOURCES = ("code", "code_ccl")


def _normalize_sources_arg(sources: object) -> list[str] | None:
    """MCP arguments の sources を正規化する。"""
    if sources is None:
        return None
    if isinstance(sources, str):
        return [part.strip() for part in sources.split(",") if part.strip()]
    if isinstance(sources, (list, tuple, set)):
        return [str(part).strip() for part in sources if str(part).strip()]
    return None


# PURPOSE: stale なインデックスをバックグラウンドで差分更新する
def _background_rebuild(engine, embed_fn, embed_dim, indices_dir, code_pkl, code_ccl_pkl, log_fn):
    """バックグラウンドスレッドでインクリメンタル更新し、hot-swap する。

    既存インデックスで即座にサービスを開始した後、このスレッドが裏で
    差分更新を実行し、完了次第 engine.register() で差し替える。
    """
    import gc
    import time
    start = time.time()
    log_fn("🔄 Background incremental rebuild started")

    # --- Sophia ---
    try:
        from mekhane.symploke.sophia_ingest import incremental_rebuild_sophia
        sophia_pkl = indices_dir / "sophia.pkl"
        stats = incremental_rebuild_sophia(str(sophia_pkl))
        log_fn(f"sophia incremental: +{stats['added']} ~{stats['updated']} -{stats['deleted']} ={stats['unchanged']}")

        if stats['added'] or stats['updated'] or stats['deleted']:
            # hot-swap: 新しいインデックスをロードして差し替え
            from mekhane.symploke.adapters.vector_store import VectorStore as VS
            from mekhane.symploke.indices.sophia import SophiaIndex as SI
            adapter = VS()
            new_idx = SI(adapter, "sophia", dimension=embed_dim, embed_fn=embed_fn)
            new_idx.load(str(sophia_pkl))
            engine.register(new_idx)
            gc.collect()  # 旧インデックスの即時解放
            log_fn(f"🔄 sophia hot-swapped ({new_idx.count()} docs)")
    except Exception as e:  # noqa: BLE001
        log_fn(f"sophia background rebuild failed (non-fatal): {e}")

    # --- Code + Code CCL ---
    try:
        from mekhane.symploke.code_ingest import (
            incremental_rebuild_code,
            incremental_rebuild_code_ccl,
        )

        code_stats = incremental_rebuild_code(str(code_pkl))
        log_fn(f"code incremental: +{code_stats['added']} ~{code_stats['updated']} -{code_stats['deleted']} ={code_stats['unchanged']}")

        if code_stats['added'] or code_stats['updated'] or code_stats['deleted']:
            from mekhane.symploke.adapters.vector_store import VectorStore as VS
            from mekhane.symploke.indices.sophia import SophiaIndex as SI
            adapter = VS()
            new_idx = SI(adapter, "code", dimension=embed_dim, embed_fn=embed_fn)
            new_idx.load(str(code_pkl))
            engine.register(new_idx)
            gc.collect()
            log_fn(f"🔄 code hot-swapped ({new_idx.count()} docs)")

        ccl_stats = incremental_rebuild_code_ccl(str(code_ccl_pkl))
        log_fn(f"code_ccl incremental: +{ccl_stats['added']} ~{ccl_stats['updated']} -{ccl_stats['deleted']} ={ccl_stats['unchanged']}")

        if ccl_stats['added'] or ccl_stats['updated'] or ccl_stats['deleted']:
            from mekhane.symploke.adapters.vector_store import VectorStore as VS
            from mekhane.symploke.indices.sophia import SophiaIndex as SI
            adapter = VS()
            new_idx = SI(adapter, "code_ccl", dimension=embed_dim, embed_fn=embed_fn)
            new_idx.load(str(code_ccl_pkl))
            engine.register(new_idx)
            gc.collect()
            log_fn(f"🔄 code_ccl hot-swapped ({new_idx.count()} docs)")
    except Exception as e:  # noqa: BLE001
        log_fn(f"code background rebuild failed (non-fatal): {e}")

    elapsed = time.time() - start
    log_fn(f"🔄 Background incremental rebuild completed in {elapsed:.1f}s")


# PURPOSE: engine を取得する (Lazy Rebuild 版)
def get_engine():
    """Lazy initialization of SearchEngine.

    起動時: 既存 pkl を即ロード (stale でも OK) → 即座にサービス開始
    バックグラウンド: stale なインデックスを再構築 → 完了時に hot-swap
    """
    global _engine, _vertex_embedder, _rebuild_thread
    if _engine is None and SearchEngine is not None:
        log("Initializing SearchEngine...")
        _engine = SearchEngine()

        # --- インデックスパスの定義 ---
        from mekhane.paths import INDICES_DIR, CODE_INDEX, CODE_CCL_INDEX
        _real_indices = {
            "kairos": INDICES_DIR / "kairos.pkl",
            "sophia": INDICES_DIR / "sophia.pkl",
            "chronos": INDICES_DIR / "chronos.pkl",
            "code": CODE_INDEX,
            "code_ccl": CODE_CCL_INDEX,
        }

        # --- Seed data fallback ---
        seed_data = {}
        try:
            from mekhane.symploke.seed_data import (
                GNOSIS_SEED,
                CHRONOS_SEED,
                SOPHIA_SEED,
                KAIROS_SEED,
            )
            seed_data = {
                "gnosis": GNOSIS_SEED,
                "chronos": CHRONOS_SEED,
                "sophia": SOPHIA_SEED,
                "kairos": KAIROS_SEED,
            }
            log("Seed data loaded (fallback)")
        except ImportError:
            log("No seed data available")

        # --- VertexEmbedder for 3072d query embeddings (via embedder_factory) ---
        from mekhane.symploke.embedder_factory import get_embed_fn, get_dimension
        EMBED_DIM = get_dimension()

        try:
            embed_fn = get_embed_fn()
            log(f"embed_fn ready ({EMBED_DIM}d)")
        except Exception as e:  # noqa: BLE001
            log(f"embedder init failed completely: {e}, falling back to stub")
            embed_fn = None

        # --- Register gnosis: LanceBridge (27,432 papers) or seed fallback ---
        if GnosisBridge is not None:
            try:
                bridge = GnosisBridge()
                count = bridge.count()
                _engine.register(bridge)
                log(f"Loaded gnosis via LanceBridge ({count} docs)")
            except Exception as e:  # noqa: BLE001
                log(f"LanceBridge failed: {e}, falling back to seed")
                adapter = VectorStore()
                index = GnosisIndex(adapter, "gnosis", dimension=EMBED_DIM, embed_fn=embed_fn)
                index.initialize()
                if "gnosis" in seed_data:
                    index.ingest(seed_data["gnosis"])
                _engine.register(index)
        else:
            adapter = VectorStore()
            index = GnosisIndex(adapter, "gnosis", dimension=EMBED_DIM, embed_fn=embed_fn)
            index.initialize()
            if "gnosis" in seed_data:
                index.ingest(seed_data["gnosis"])
            _engine.register(index)
            log("Registered gnosis from seed")

        # --- 即座にロード: 既存 pkl を stale でも即ロード ---
        # 再構築が必要かどうかを追跡
        needs_rebuild = False

        for IndexClass, name in [
            (ChronosIndex, "chronos"),
            (SophiaIndex, "sophia"),
            (KairosIndex, "kairos"),
            (SophiaIndex, "code"),
            (SophiaIndex, "code_ccl"),
        ]:
            pkl_path = _real_indices.get(name)

            # FAISS 形式 (.faiss/.meta) または旧 pkl のいずれかが存在すればロード
            faiss_path = pkl_path.with_suffix('.faiss') if pkl_path else None
            has_index = (pkl_path and pkl_path.exists()) or (faiss_path and faiss_path.exists())
            if has_index:
                adapter = VectorStore()
                index = IndexClass(adapter, name, dimension=EMBED_DIM, embed_fn=embed_fn)
                try:
                    index.load(str(pkl_path))
                    count = index.count()
                    log(f"Loaded {name} from {pkl_path.name} ({count} docs)")
                except Exception as e:  # noqa: BLE001
                    # 破損 pkl (EOFError 等) を検出したら seed/empty から復旧する。
                    log(f"Failed to load {name} from {pkl_path.name}: {e}. Rebuilding from seed/empty.")
                    try:
                        pkl_path.unlink(missing_ok=True)
                    except Exception:  # noqa: BLE001
                        pass
                    adapter = VectorStore()
                    index = IndexClass(adapter, name, dimension=EMBED_DIM, embed_fn=embed_fn)
                    index.initialize()
                    if name in seed_data:
                        try:
                            count = index.ingest(seed_data[name])
                            log(f"Recovered {name} from seed ({count} docs)")
                        except Exception as e2:  # noqa: BLE001
                            log(f"Seed ingest for {name} failed (non-fatal, starting empty): {e2}")
                    else:
                        log(f"Recovered {name} (empty)")
                    needs_rebuild = True
            else:
                adapter = VectorStore()
                index = IndexClass(adapter, name, dimension=EMBED_DIM, embed_fn=embed_fn)
                index.initialize()
                if name in seed_data:
                    try:
                        count = index.ingest(seed_data[name])
                        log(f"Registered {name} from seed ({count} docs)")
                    except Exception as e:  # noqa: BLE001
                        log(f"Seed ingest for {name} failed (non-fatal, starting empty): {e}")
                else:
                    log(f"Registered {name} (empty)")
                needs_rebuild = True  # pkl なし → 再構築必要

            _engine.register(index)

        # --- Stale チェック & バックグラウンド再構築 ---
        if not needs_rebuild:
            # sophia の stale チェック
            try:
                from mekhane.symploke.sophia_ingest import DEFAULT_KNOWLEDGE_DIRS, GENERIC_DOCUMENT_DIRS
                sophia_pkl = _real_indices["sophia"]
                latest = 0.0
                for d in DEFAULT_KNOWLEDGE_DIRS:
                    if d.exists():
                        for f in d.rglob("*.md"):
                            try:
                                mt = f.stat().st_mtime
                                if mt > latest:
                                    latest = mt
                            except OSError:
                                pass
                for d_path, _ in GENERIC_DOCUMENT_DIRS:
                    if d_path.exists():
                        for f in d_path.rglob("*.md"):
                            try:
                                mt = f.stat().st_mtime
                                if mt > latest:
                                    latest = mt
                            except OSError:
                                pass
                if sophia_pkl.exists() and sophia_pkl.stat().st_mtime < latest:
                    needs_rebuild = True
            except Exception:  # noqa: BLE001
                pass

            # code の stale チェック
            if not needs_rebuild:
                try:
                    from mekhane.symploke.code_ingest import CODE_SCAN_DIRS
                    code_pkl_path = _real_indices["code"]
                    latest = 0.0
                    for d_path, _ in CODE_SCAN_DIRS:
                        if d_path.exists():
                            for f in d_path.rglob("*.py"):
                                try:
                                    mt = f.stat().st_mtime
                                    if mt > latest:
                                        latest = mt
                                except OSError:
                                    pass
                    if code_pkl_path.exists() and code_pkl_path.stat().st_mtime < latest:
                        needs_rebuild = True
                except Exception:  # noqa: BLE001
                    pass

        if needs_rebuild:
            import threading
            log("⚡ Stale indices detected — starting background rebuild")
            _rebuild_thread = threading.Thread(
                target=_background_rebuild,
                args=(
                    _engine, embed_fn, EMBED_DIM,
                    INDICES_DIR, CODE_INDEX, CODE_CCL_INDEX, log,
                ),
                daemon=True,
                name="phantazein-rebuild",
            )
            _rebuild_thread.start()
        else:
            log("All indices are up-to-date")

        log(f"SearchEngine ready (sources: {list(_real_indices.keys())})")

    return _engine

# PURPOSE: List available tools.

# ============ Tool definitions ============
# PURPOSE: [L2-auto] list_tools の非同期処理定義
@server.list_tools()
# PURPOSE: [L2-auto] List available tools.
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        # ========================================
        # ファサード 1: search — 統合検索
        # 旧ツール: search, search_papers, search_code を統合
        # ========================================
        Tool(
            name="search",
            description=(
                "統合知識検索。scope で検索対象を切替:\n"
                "- all: 文書インデックス横断検索 (gnosis/sophia/hgk_core/chronos/kairos)。code は含めない\n"
                "- papers: Gnōsis 論文DB 特化検索\n"
                "- code: コード検索 (text/structure/both/auto/similar)\n\n"
                "例: search(query='active inference', scope='papers')\n"
                "例: search(query='BBS proposal', scope='all', sources=['sophia'])\n"
                "例: search(query='error handling', scope='code', code_mode='structure')\n"
                "例: search(query='code_ingest.py::python_to_ccl', scope='code', code_mode='similar')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "検索クエリ"},
                    "scope": {
                        "type": "string",
                        "enum": ["all", "papers", "code"],
                        "description": "検索スコープ (default: all)",
                        "default": "all",
                    },
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "scope=all 時: 文書ソース絞込 (gnosis, chronos, sophia, hgk_core, kairos)。code は scope=code を使う",
                    },
                    "k": {
                        "type": "integer",
                        "description": "結果件数 (default: 10)",
                        "default": 10,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "scope=papers 時: 最大件数 (default: 5)",
                        "default": 5,
                    },
                    "code_mode": {
                        "type": "string",
                        "enum": ["auto", "text", "structure", "both", "similar", "r1"],
                        "description": "scope=code 時: 検索モード。similar=Code→Code 構造検索 (query に file::func 形式で指定)。r1=CCL完全一致検索 (同一構造の関数を検出)",
                        "default": "auto",
                    },
                },
                "required": ["query"],
            },
        ),
        # ========================================
        # ファサード 2: check — 検証・診断
        # 旧ツール: dendron_check, dendron_mece_check, dejavu_check, dejavu_history を統合
        # ========================================
        Tool(
            name="check",
            description=(
                "検証・診断ツール。action で機能を切替:\n"
                "- proof: Dendron PROOF 存在証明チェック\n"
                "- mece: ディレクトリ構造の MECE 診断\n"
                "- dejavu: テキストの重複チェック (NOVEL/SIMILAR/DUPLICATE)\n"
                "- dejavu_history: 過去のデジャブ検出ログ表示\n\n"
                "例: check(action='proof', path='/path/to/dir')\n"
                "例: check(action='dejavu', text='...')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["proof", "mece", "dejavu", "dejavu_history"],
                        "description": "実行する検証の種類",
                    },
                    "path": {"type": "string", "description": "action=proof/mece 時: 対象パス"},
                    "check_functions": {"type": "boolean", "description": "action=proof 時: 関数/クラス PURPOSE コメントチェック", "default": True},
                    "recursive": {"type": "boolean", "description": "action=proof 時: サブディレクトリ再帰", "default": False},
                    "embed": {"type": "boolean", "description": "action=mece 時: 意味的 MECE チェック", "default": False},
                    "me_threshold": {"type": "number", "description": "action=mece 時: ME 警告閾値", "default": 0.70},
                    "ce_min_children": {"type": "integer", "description": "action=mece 時: CE 最小子ディレクトリ数", "default": 3},
                    "text": {"type": "string", "description": "action=dejavu 時: 重複チェック対象テキスト"},
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "action=dejavu 時: ソース絞込",
                    },
                    "threshold": {"type": "number", "description": "action=dejavu 時: NOVEL 閾値", "default": 0.80},
                    "limit": {"type": "integer", "description": "action=dejavu_history 時: 表示件数", "default": 10},
                },
                "required": ["action"],
            },
        ),
        # ========================================
        # ファサード 3: graph — 知識グラフ
        # 旧ツール: backlinks, graph_stats, stats, sources を統合
        # ========================================
        Tool(
            name="graph",
            description=(
                "知識グラフ・統計ツール。action で機能を切替:\n"
                "- backlinks: KI のバックリンク/アウトリンク表示\n"
                "- stats: 知識グラフ統計 (ノード/エッジ/最多リンク)\n"
                "- index: インデックス文書数の統計\n"
                "- sources: 利用可能な知識ソース一覧\n\n"
                "例: graph(action='backlinks', ki_name='kalon')\n"
                "例: graph(action='stats')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["backlinks", "stats", "index", "sources"],
                        "description": "実行する操作の種類",
                    },
                    "ki_name": {"type": "string", "description": "action=backlinks 時: KI 名"},
                },
                "required": ["action"],
            },
        ),
        # ========================================
        # ファサード 4: convert — コード変換 (独立維持)
        # ========================================
        Tool(
            name="convert",
            description="Python コードを CCL 構造式に変換。構造的コード検索のパターン取得に使用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "変換対象の Python コード"},
                },
                "required": ["code"],
            },
        ),
        # ========================================
        # ファサード 5: recommend_model — モデル推薦 (独立維持)
        # ========================================
        Tool(
            name="recommend_model",
            description="タスクに最適な AI モデル (Claude/Gemini) を推薦。Krisis 優先度ルール (P1-P5) に基づく。",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_description": {"type": "string", "description": "分析対象のタスク説明"},
                },
                "required": ["task_description"],
            },
        ),
    ]
# PURPOSE: tool calls の安全な処理を保証する


# PURPOSE: 旧ツール名 (mneme_search 等) をファサード名へ正規化 — Hub / Antigravity / ドキュ互換
def _normalize_legacy_tool(name: str, arguments: dict | None) -> tuple[str, dict]:
    args = dict(arguments or {})
    if name == "mneme_search":
        return "search", args
    if name == "search_papers":
        args.setdefault("scope", "papers")
        return "search", args
    if name == "search_code":
        args.setdefault("scope", "code")
        return "search", args
    if name == "dejavu_check":
        args.setdefault("action", "dejavu")
        return "check", args
    if name == "dendron_check":
        args.setdefault("action", "proof")
        return "check", args
    if name == "dendron_mece_check":
        args.setdefault("action", "mece")
        return "check", args
    if name == "dejavu_history":
        args.setdefault("action", "dejavu_history")
        return "check", args
    if name in ("mneme_backlinks", "backlinks"):
        args.setdefault("action", "backlinks")
        return "graph", args
    if name in ("graph_stats", "mneme_stats"):
        args.setdefault("action", "stats")
        return "graph", args
    if name == "graph_index":
        args.setdefault("action", "index")
        return "graph", args
    if name == "mneme_sources":
        args.setdefault("action", "sources")
        return "graph", args
    if name in ("code_to_ccl", "python_to_ccl"):
        return "convert", args
    return name, args


# PURPOSE: [L2-auto] call_tool の非同期処理定義
@server.call_tool()
# PURPOSE: [L2-auto] Handle tool calls.
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    orig = name
    name, arguments = _normalize_legacy_tool(name, arguments)
    if orig != name:
        log(f"Legacy tool alias: {orig!r} → {name!r}")
    log(f"Tool call: {name} with args: {arguments}")

    try:
        if name == "search":
            return await _handle_search_facade(arguments)
        elif name == "check":
            return await _handle_check_facade(arguments)
        elif name == "graph":
            return await _handle_graph_facade(arguments)
        elif name == "convert":
            return await asyncio.to_thread(_handle_code_to_ccl, arguments)
        elif name == "recommend_model":
            return await _handle_recommend_model(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc()
        log(f"Tool error: {e}\n{tb}")
        return [TextContent(type="text", text=f"Error: {str(e)}\n\nTraceback:\n{tb}")]

async def _handle_search_facade(arguments: dict) -> list[TextContent]:
    scope = arguments.get("scope", "all")
    try:
        if scope == "all":
            sources = _normalize_sources_arg(arguments.get("sources"))
            code_sources = [source for source in sources or [] if source in _CODE_SEARCH_SOURCES]
            non_code_sources = [source for source in sources or [] if source not in _CODE_SEARCH_SOURCES]

            if code_sources and non_code_sources:
                return [
                    TextContent(
                        type="text",
                        text=(
                            "CODE_SEARCH_SEPARATED\n"
                            "- scope=all は文書検索専用です。code と文書ソースを同じランキング面で混ぜません。\n"
                            "- 文書検索: search(query=..., scope='all', sources=['sophia', 'hgk_core', ...])\n"
                            "- コード検索: search(query=..., scope='code', code_mode='text|structure|both|similar|r1')"
                        ),
                    )
                ]

            search_args = dict(arguments)
            if code_sources and not non_code_sources:
                search_args["scope"] = "code"
                search_args.setdefault("code_mode", "text")
                return await asyncio.to_thread(_handle_search_code, search_args)

            search_args["sources"] = sources or list(_DOC_SEARCH_SOURCES)
            return await asyncio.to_thread(_handle_search, search_args)
        elif scope == "papers":
            return await asyncio.to_thread(_handle_search_papers, arguments)
        elif scope == "code":
            return await asyncio.to_thread(_handle_search_code, arguments)
        else:
            return [TextContent(type="text", text=f"Unknown search scope: {scope}")]
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc()
        log(f"Search facade error (scope={scope}): {e}\n{tb}")
        return [TextContent(type="text", text=f"Search failed (scope={scope}): {str(e)}\n\nTraceback:\n{tb}")]

async def _handle_check_facade(arguments: dict) -> list[TextContent]:
    action = arguments.get("action")
    try:
        if action == "proof":
            return await _handle_dendron_check(arguments)
        elif action == "mece":
            return await _handle_dendron_mece_check(arguments)
        elif action == "dejavu":
            return await asyncio.to_thread(_handle_dejavu_check, arguments)
        elif action == "dejavu_history":
            return await _handle_dejavu_history(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown check action: {action}")]
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc()
        log(f"Check facade error (action={action}): {e}\n{tb}")
        return [TextContent(type="text", text=f"Check failed (action={action}): {str(e)}\n\nTraceback:\n{tb}")]

async def _handle_graph_facade(arguments: dict) -> list[TextContent]:
    action = arguments.get("action")
    try:
        if action == "backlinks":
            return await _handle_backlinks(arguments)
        elif action == "stats":
            return await _handle_graph_stats(arguments)
        elif action == "index":
            return await _handle_stats(arguments)
        elif action == "sources":
            return await _handle_sources(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown graph action: {action}")]
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc()
        log(f"Graph facade error (action={action}): {e}\n{tb}")
        return [TextContent(type="text", text=f"Graph failed (action={action}): {str(e)}\n\nTraceback:\n{tb}")]


# PURPOSE: [L2-auto] Handle search tool.
def _handle_search(arguments: dict) -> list[TextContent]:
    """Handle search tool."""
    query = arguments.get("query", "")
    sources = arguments.get("sources")
    k = arguments.get("k", 10)

    try:
        engine = get_engine()
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc()
        log(f"get_engine() failed: {e}\n{tb}")
        return [TextContent(type="text", text=f"SearchEngine init error: {str(e)}\n\nTraceback:\n{tb}")]

    if engine is None:
        return [TextContent(type="text", text="SearchEngine not available (stub mode)")]

    try:
        results = engine.search(query, sources=sources, k=k)
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc()
        log(f"engine.search() failed: {e}\n{tb}")
        return [TextContent(type="text", text=f"Search error: {str(e)}\n\nTraceback:\n{tb}")]

    # --- Phantasia Field (FAISS knowledge index) からの結果をマージ ---
    # gnosis_index_update.py で構築した 24k+ チャンクの統一インデックス
    knowledge_lines = []
    try:
        with StdoutSuppressor():
            from mekhane.anamnesis.index import GnosisIndex as FAISSIndex
            faiss_idx = FAISSIndex()
            if faiss_idx.table_exists():
                faiss_results = faiss_idx.search(query, k=min(k, 5))
                if faiss_results:
                    knowledge_lines.append(f"### 🌀 Phantasia Field — {len(faiss_results)} hits")
                    for i, r in enumerate(faiss_results, 1):
                        title = r.get("title", "Untitled")[:60]
                        source = r.get("source", "unknown")
                        dist = r.get("_distance", 0)
                        abstract = r.get("abstract", "")[:200]
                        knowledge_lines.append(f"{i}. **[{source}] {title}** (Score: {1-dist:.3f})")
                        if abstract:
                            knowledge_lines.append(f"   {abstract}...")
                    knowledge_lines.append("")
    except Exception as e:  # noqa: BLE001
        log(f"Phantasia Field search failed (non-fatal): {e}")

    if not results and not knowledge_lines:
        return [TextContent(type="text", text=f"No results for: {query}")]

    # ソース → 表示ラベルのマッピング
    _SOURCE_LABELS = {
        "gnosis": "🔬 Gnōsis (論文)",
        "sophia": "📖 Sophia (知識)",
        "chronos": "💬 Chronos (対話)",
        "kairos": "🔄 Kairos (引継)",
        "code": "💻 Code (コード)",
    }

    # sophia の doc_type → 表示ラベルのマッピング
    _DOC_TYPE_LABELS = {
        "kernel": "🔷 Kernel (公理・定理)",
        "horos": "📏 Hóros (制約)",
        "workflow": "⚙️ Workflow (手順)",
        "episteme": "📚 Epistēmē (知識)",
        "mekhane_doc": "🔧 Mekhane (機構)",
        "artifact": "📎 Artifact (成果物)",
        "boulesis": "📋 Boulēsis (企画)",
        "hyle": "🧱 Hylē (素材)",
        "rom": "💾 ROM (蒸留)",
        "session": "💬 Session (対話)",
        "review": "📝 Review (レビュー)",
        "ops_doc": "🛠️ Ops (運用)",
        "trace": "🔍 Trace (実行痕跡)",
        "belief": "🧭 Belief (信念)",
        "knowledge_item": "📖 KI (知識項目)",
        "brain_artifact": "🧠 Brain (IDE)",
    }

    # 全結果を source.value でグループ化
    from collections import defaultdict
    source_groups = defaultdict(list)
    for r in results:
        source_groups[r.source.value].append(r)

    # 各グループ内をスコア降順ソート
    for source_name in source_groups:
        source_groups[source_name].sort(key=lambda r: r.score, reverse=True)

    # グループ順序: グループ内最高スコアの降順
    sorted_groups = sorted(
        source_groups.items(),
        key=lambda x: x[1][0].score if x[1] else 0,
        reverse=True,
    )

    lines = [f"## Search Results for: {query}", f"Found {len(results)} results\n"]

    for source_name, items in sorted_groups:
        source_label = _SOURCE_LABELS.get(source_name, f"📄 {source_name}")
        hit_word = "hit" if len(items) == 1 else "hits"

        if source_name == "sophia":
            # sophia: doc_type サブグルーピング維持
            lines.append(f"### {source_label} — {len(items)} {hit_word}")
            facets = defaultdict(list)
            for r in items:
                doc_type = r.metadata.get("doc_type") or r.metadata.get("type", "unknown")
                facets[doc_type].append(r)

            sorted_facets = sorted(
                facets.items(),
                key=lambda x: x[1][0].score if x[1] else 0,
                reverse=True,
            )

            for doc_type, sub_items in sorted_facets:
                label = _DOC_TYPE_LABELS.get(doc_type, f"📄 {doc_type}")
                sub_hit = "hit" if len(sub_items) == 1 else "hits"
                lines.append(f"#### {label} — {len(sub_items)} {sub_hit}")
                for i, r in enumerate(sub_items, 1):
                    display_name = r.metadata.get("ki_name") or r.doc_id
                    content_preview = ""
                    if r.content:
                        content_preview = f" — {r.content[:120].strip()}..."
                    lines.append(f"{i}. **{display_name}** (Score: {r.score:.3f}){content_preview}")
                lines.append("")
        else:
            # gnosis/chronos/kairos/code: フラット表示 (スコア降順)
            lines.append(f"### {source_label} — {len(items)} {hit_word}")
            for i, r in enumerate(items, 1):
                display_name = r.metadata.get("ki_name") or r.doc_id
                content_preview = ""
                if r.content:
                    content_preview = f" — {r.content[:120].strip()}..."
                lines.append(f"{i}. **{display_name}** (Score: {r.score:.3f}){content_preview}")
            lines.append("")

    # Phantasia Field 結果を末尾に追加
    if knowledge_lines:
        lines.extend(knowledge_lines)

    return [TextContent(type="text", text="\n".join(lines))]


# PURPOSE: [L2-auto] Handle stats tool.
async def _handle_stats(arguments: dict) -> list[TextContent]:
    """Handle stats tool."""
    engine = get_engine()
    if engine is None:
        return [TextContent(type="text", text="SearchEngine not available (stub mode)")]

    stats = engine.stats()

    lines = ["## Mneme Statistics\n"]
    total = 0
    for source, count in stats.items():
        lines.append(f"- **{source}**: {count} documents")
        total += count
    lines.append(f"\n**Total**: {total} documents")

# PURPOSE: sources tool の安全な処理を保証する
    return [TextContent(type="text", text="\n".join(lines))]


# PURPOSE: [L2-auto] Handle sources tool.
async def _handle_sources(arguments: dict) -> list[TextContent]:
    """Handle sources tool."""
    engine = get_engine()
    if engine is None:
        sources = ["gnosis", "chronos", "sophia", "kairos"]
    else:
        sources = list(engine.registered_sources)

    lines = ["## Available Knowledge Sources\n"]
    descriptions = {
        "gnosis": "External knowledge (research papers, documentation)",
        "chronos": "Chat history (time-ordered conversations)",
        "sophia": "Knowledge items (distilled insights)",
        "kairos": "Session handoffs (context continuity)",
    }

    for source in sources:
        desc = descriptions.get(source, "Unknown source")
        lines.append(f"- **{source}**: {desc}")

    return [TextContent(type="text", text="\n".join(lines))]


# ============ Gnosis tools (from gnosis_mcp_server.py) ============

# PURPOSE: [L2-auto] Handle search_papers tool.
def _handle_search_papers(arguments: dict) -> list[TextContent]:
    """Search Gnosis papers via GnosisIndex."""
    query = arguments.get("query", "")
    limit = arguments.get("limit", 5)
    if not query:
        return [TextContent(type="text", text="Error: query is required")]
    try:
        with StdoutSuppressor():
            from mekhane.anamnesis.index import GnosisIndex
            index = GnosisIndex()
            results = index.search(query, k=limit)
        if not results:
            return [TextContent(type="text", text=f"No results found for: {query}")]
        lines = [f'# Gnōsis Search Results: "{query}"\n', f"Found {len(results)} results:\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"## [{i}] {r.get('title', 'Untitled')}")
            lines.append(f"- **Source**: {r.get('source', 'Unknown')}")
            lines.append(f"- **Citations**: {r.get('citations', 'N/A')}")
            authors = r.get('authors', 'Unknown')
            if isinstance(authors, str):
                authors = authors[:100]
            lines.append(f"- **Authors**: {authors}")
            abstract = r.get('abstract', '')
            if isinstance(abstract, str):
                abstract = abstract[:300]
            lines.append(f"- **Abstract**: {abstract}...")
            if r.get("url"):
                lines.append(f"- **URL**: {r.get('url')}")
            lines.append("")
        log(f"search_papers completed: {len(results)} results")
        return [TextContent(type="text", text="\n".join(lines))]
    except Exception as e:  # noqa: BLE001
        log(f"search_papers error: {e}")
        return [TextContent(type="text", text=f"Error searching papers: {str(e)}")]


# PURPOSE: [L2-auto] Handle recommend_model tool.
async def _handle_recommend_model(arguments: dict) -> list[TextContent]:
    """Recommend AI model based on Krisis priority rules."""
    task_desc = arguments.get("task_description", "").lower()
    if not task_desc:
        return [TextContent(type="text", text="Error: task_description is required")]
    log(f"Recommending model for: {task_desc[:50]}...")
    priority_rules = [
        ("P1", ["セキュリティ", "security", "監査", "audit", "コンプライアンス", "compliance", "品質保証", "quality"], "Claude"),
        ("P2", ["画像", "image", "ui", "ux", "図", "diagram", "可視化", "visualization", "デザイン", "design"], "Gemini"),
        ("P3", ["探索", "explore", "ブレスト", "brainstorm", "プロトタイプ", "prototype", "mvp", "試作"], "Gemini"),
        ("P4", ["高速", "fast", "バッチ", "batch", "初期調査", "triage", "トリアージ"], "Gemini Flash"),
    ]
    detected_keywords = []
    matched_priority = None
    recommended_model = "Claude"  # Default P5
    for priority, keywords, model in priority_rules:
        for kw in keywords:
            if kw in task_desc:
                detected_keywords.append(kw)
                if matched_priority is None:
                    matched_priority = priority
                    recommended_model = model
    if matched_priority is None:
        matched_priority = "P5"
    lines = [
        "# [Hegemonikon] T2 Krisis (Model Selection)\n",
        f"- **Task**: {arguments.get('task_description', '')}",
        f"- **Detected Keywords**: {', '.join(detected_keywords) if detected_keywords else '(none)'}",
        f"- **Priority**: {matched_priority}",
        f"- **Recommended Model**: {recommended_model}",
    ]
    return [TextContent(type="text", text="\n".join(lines))]


# ============ Sophia tools (from sophia_mcp_server.py) ============

# Index paths — paths.py が Single Source of Truth
try:
    from mekhane.paths import SOPHIA_INDEX, KAIROS_INDEX, KI_DIR
except ImportError:
    SOPHIA_INDEX = SOPHIA_INDEX
    KAIROS_INDEX = KAIROS_INDEX
    KI_DIR = Path.home() / ".gemini" / "antigravity" / "knowledge"
STEPS_ROOT = Path.home() / ".gemini" / "antigravity" / "brain"

# PURPOSE: [L2-auto] Handle backlinks tool.
async def _handle_backlinks(arguments: dict) -> list[TextContent]:
    """Get backlinks for a Knowledge Item."""
    ki_name = arguments.get("ki_name", "")
    if not ki_name:
        return [TextContent(type="text", text="Error: ki_name is required")]
    try:
        with StdoutSuppressor():
            from mekhane.symploke.sophia_backlinker import SophiaBacklinker
        log(f"Getting backlinks for: {ki_name}")
        backlinker = SophiaBacklinker()
        backlinker.build_graph()
        backlinks = backlinker.get_backlinks(ki_name)
        outlinks = backlinker.get_outlinks(ki_name)
        lines = [f"# Backlinks: {ki_name}\n"]
        if backlinks:
            lines.append(f"## ← Backlinks ({len(backlinks)})")
            for link in sorted(backlinks):
                lines.append(f"- {link}")
        else:
            lines.append("No backlinks found.")
        lines.append("")
        if outlinks:
            lines.append(f"## → Outlinks ({len(outlinks)})")
            for link in sorted(outlinks):
                lines.append(f"- {link}")
        return [TextContent(type="text", text="\n".join(lines))]
    except Exception as e:  # noqa: BLE001
        log(f"Backlinks error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# PURPOSE: [L2-auto] Handle graph_stats tool.
async def _handle_graph_stats(arguments: dict) -> list[TextContent]:
    """Get knowledge graph statistics."""
    try:
        with StdoutSuppressor():
            from mekhane.symploke.sophia_backlinker import SophiaBacklinker
        log("Getting graph stats...")
        backlinker = SophiaBacklinker()
        backlinker.build_graph()
        stats = backlinker.get_stats()
        lines = ["# Knowledge Graph Statistics\n"]
        lines.append(f"- **Nodes**: {stats['nodes']}")
        lines.append(f"- **Edges**: {stats['edges']}")
        lines.append(f"- **Isolated**: {stats['isolated']}")
        if stats["most_linked"]:
            lines.append("\n## Most Linked")
            for name, count in stats["most_linked"]:
                if count > 0:
                    lines.append(f"- **{name}**: {count} backlinks")
        return [TextContent(type="text", text="\n".join(lines))]
    except Exception as e:  # noqa: BLE001
        log(f"Graph stats error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ============ Dendron tools ============

# PURPOSE: [L2-auto] _handle_dendron_check の非同期処理定義
async def _handle_dendron_check(arguments: dict) -> list[TextContent]:
    """Run Dendron PROOF verification on a file or directory."""
    target = arguments.get("path", "")
    if not target:
        return [TextContent(type="text", text="Error: path is required")]

    check_functions = arguments.get("check_functions", True)
    recursive = arguments.get("recursive", False)

    try:
        with StdoutSuppressor():
            from mekhane.dendron.checker import DendronChecker

        target_path = Path(target)
        if not target_path.exists():
            return [TextContent(type="text", text=f"Error: path not found: {target}")]

        checker = DendronChecker(
            check_functions=check_functions,
            root=_base.project_root,
        )

        issues = []
        if target_path.is_file():
            result = checker.check_file_proof(target_path)
            if result.status.value not in ("ok", "exempt"):
                issues.append(f"- **{result.status.value}**: {target_path.name} — {result.reason or 'no reason'}")
            if check_functions:
                func_results = checker.check_functions_in_file(target_path)
                for fr in func_results:
                    if fr.status.value != "ok":
                        issues.append(f"- **{fr.status.value}**: `{fr.name}` in {target_path.name} — {fr.reason or ''}")
        elif target_path.is_dir():
            # Check directory PROOF.md
            dir_result = checker.check_dir_proof(target_path)
            if dir_result.status.value not in ("ok", "exempt"):
                issues.append(f"- **{dir_result.status.value}**: {target_path.name}/ — {dir_result.reason or ''}")

            # Check files in directory
            pattern = "**/*.py" if recursive else "*.py"
            for py_file in sorted(target_path.glob(pattern)):
                if py_file.name.startswith("__"):
                    continue
                result = checker.check_file_proof(py_file)
                if result.status.value not in ("ok", "exempt"):
                    rel = py_file.relative_to(target_path)
                    issues.append(f"- **{result.status.value}**: {rel} — {result.reason or ''}")

        if not issues:
            return [TextContent(type="text", text=f"✅ Dendron: all checks passed for `{target_path.name}`")]

        lines = [f"# 🌿 Dendron Check: {target_path.name}\n"]
        lines.append(f"**Issues found**: {len(issues)}\n")
        lines.extend(issues)
        return [TextContent(type="text", text="\n".join(lines))]

    except Exception as e:  # noqa: BLE001
        log(f"Dendron check error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# PURPOSE: ディレクトリ構造の MECE 診断を実行し、ME/CE issues を MCP 経由で返す
async def _handle_dendron_mece_check(arguments: dict) -> list[TextContent]:
    """Run MECE diagnosis on a directory structure."""
    target = arguments.get("path", "")
    if not target:
        return [TextContent(type="text", text="Error: path is required")]

    me_threshold = arguments.get("me_threshold", 0.70)
    me_error_threshold = arguments.get("me_error_threshold", 0.85)
    ce_min_children = arguments.get("ce_min_children", 3)

    try:
        with StdoutSuppressor():
            from mekhane.dendron.checker import DendronChecker

        target_path = Path(target)
        if not target_path.exists():
            return [TextContent(type="text", text=f"Error: path not found: {target}")]
        if not target_path.is_dir():
            return [TextContent(type="text", text=f"Error: path must be a directory: {target}")]

        # embedding 関数の設定
        embed_fn = None
        use_embed = arguments.get("embed", False)
        if use_embed:
            try:
                from mekhane.symploke.embedder_factory import get_embed_fn
                embed_fn = get_embed_fn()
            except Exception as e:  # noqa: BLE001
                log(f"Embedding init failed, falling back to text: {e}")

        checker = DendronChecker(root=_base.project_root)
        issues = checker.check_mece(
            target_path,
            embed_fn=embed_fn,
            me_threshold=me_threshold,
            me_error_threshold=me_error_threshold,
            ce_min_children=ce_min_children,
        )

        if not issues:
            return [TextContent(type="text", text=f"✅ MECE: no issues found for `{target_path.name}`")]

        # ME/CE を分離して報告
        me_issues = [i for i in issues if i.issue_type.startswith("me_")]
        ce_issues = [i for i in issues if i.issue_type.startswith("ce_")]
        errors = sum(1 for i in issues if i.severity == "error")
        warnings = sum(1 for i in issues if i.severity == "warning")

        lines = [f"# 🔍 Dendron MECE Check: {target_path.name}\n"]
        lines.append(f"**Total**: {len(issues)} issues ({errors} errors, {warnings} warnings)")
        lines.append(f"**ME**: {len(me_issues)} | **CE**: {len(ce_issues)}\n")

        if me_issues:
            lines.append("## ME (Mutual Exclusivity)\n")
            for issue in me_issues[:20]:  # 上限 20 件
                sev = "❌" if issue.severity == "error" else "⚠️"
                parent = issue.parent_path.name if issue.parent_path else "?"
                lines.append(f"{sev} [{parent}] {issue.suggestion}")
                if issue.paths:
                    for p in issue.paths:
                        lines.append(f"  - {p.name}")

        if ce_issues:
            lines.append("\n## CE (Collective Exhaustiveness)\n")
            for issue in ce_issues[:30]:  # 上限 30 件
                sev = "❌" if issue.severity == "error" else "⚠️"
                parent = issue.parent_path.name if issue.parent_path else "?"
                lines.append(f"{sev} [{parent}] {issue.suggestion}")
                if issue.paths:
                    for p in issue.paths[:5]:  # パス上限 5
                        lines.append(f"  - {p.name}")
                    if len(issue.paths) > 5:
                        lines.append(f"  - ... (+{len(issue.paths) - 5} more)")

        if len(issues) > 50:
            lines.append(f"\n(Showing top 50 of {len(issues)} issues)")

        return [TextContent(type="text", text="\n".join(lines))]

    except Exception as e:  # noqa: BLE001
        log(f"Dendron MECE check error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]



# ============ Déjà Vu Detector ============

# PURPOSE: デジャブ検出ログのパス
try:
    from mekhane.paths import STATE_LOGS
    _DEJAVU_LOG = STATE_LOGS / "dejavu_log.jsonl"
except ImportError:
    _DEJAVU_LOG = Path.home() / ".hegemonikon" / "dejavu_log.jsonl"

# PURPOSE: LLM 判定プロンプト — 類似候補を文脈込みで分析
_DEJAVU_LLM_PROMPT = """あなたは Hegemonikón の重複検出監査官です。
以下の「入力テキスト」と「類似候補」を比較し、判定してください。

## 入力テキスト
{input_text}

## 類似候補 (上位 {n} 件, コサイン類似度順)
{candidates}

## 判定基準
- DUPLICATE: 入力テキストが既存の成果物とほぼ同じ内容で、新たな価値を追加していない
- SIMILAR: 関連する既存成果物があるが、入力テキストは新しい視点・拡張・更新を含む
- NOVEL: 既存の成果物とは本質的に異なるトピック・アプローチ

## 出力形式 (JSON のみ、他のテキストは不要)
{{
  "verdict": "NOVEL" | "SIMILAR" | "DUPLICATE",
  "reason": "判定理由 (日本語, 1-2文)",
  "references": ["参照すべき既存成果物の doc_id (あれば)"]
}}
"""


# PURPOSE: ベクトル検索 + LLM 二段判定でデジャブを検出する
def _handle_dejavu_check(arguments: dict) -> list[TextContent]:
    """デジャブ検出: ベクトル検索 → 閾値フィルタ → LLM 判定。"""
    import json as _json
    from datetime import datetime, timezone

    text = arguments.get("text", "").strip()
    if not text:
        return [TextContent(type="text", text="Error: text is required")]

    sources = arguments.get("sources")
    threshold = arguments.get("threshold", 0.80)

    # ① SearchEngine でハイブリッド検索
    try:
        engine = get_engine()
    except Exception as e:  # noqa: BLE001
        return [TextContent(type="text", text=f"SearchEngine init error: {e}")]

    if engine is None:
        return [TextContent(type="text", text="SearchEngine not available (stub mode)")]

    try:
        results = engine.search(text, sources=sources, k=20)
    except Exception as e:  # noqa: BLE001
        return [TextContent(type="text", text=f"Search error: {e}")]

    # ② コサイン類似度でフィルタ
    # SearchEngine.search() の score は類似度 (高いほど類似)
    similar_hits = [r for r in results if r.score >= threshold]

    # ③ 閾値超え 0件 → NOVEL
    if not similar_hits:
        verdict = {
            "verdict": "NOVEL",
            "reason": f"類似候補なし (最高スコア: {results[0].score:.3f}, 閾値: {threshold})" if results else f"検索結果なし (閾値: {threshold})",
            "references": [],
            "top_scores": [round(r.score, 3) for r in results[:5]],
        }
        _dejavu_log_entry(text, verdict, similar_hits)
        return [TextContent(type="text", text=_format_dejavu_result(verdict))]

    # ④ LLM 判定 — CortexClient で Gemini に投げる
    candidates_text = ""
    for i, hit in enumerate(similar_hits[:5], 1):
        content_preview = (hit.content or "")[:300]
        candidates_text += f"\n### 候補 {i} (score={hit.score:.3f}, source={hit.source.value}, id={hit.doc_id})\n{content_preview}\n"

    prompt = _DEJAVU_LLM_PROMPT.format(
        input_text=text[:1000],
        n=min(len(similar_hits), 5),
        candidates=candidates_text,
    )

    try:
        from mekhane.ochema.cortex_client import CortexClient
        client = CortexClient(
            model="gemini-3-flash-preview",
            max_tokens=512,
        )
        response = client.ask(
            message=prompt,
            system_instruction="重複検出監査官。JSON のみ出力。",
            temperature=0.0,
            timeout=15.0,
        )
        # LLM 応答から JSON を抽出
        resp_text = response.text.strip()
        # 「```json ... ```」ブロックを除去
        if resp_text.startswith("```"):
            resp_text = resp_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        verdict = _json.loads(resp_text)
        # top_scores を付与
        verdict["top_scores"] = [round(r.score, 3) for r in similar_hits[:5]]
    except Exception as e:  # noqa: BLE001
        log(f"dejavu_check LLM error: {e}")
        # LLM 失敗時のフォールバック判定
        max_score = similar_hits[0].score if similar_hits else 0.0
        fallback_verdict = "DUPLICATE" if max_score >= 0.95 else "SIMILAR"
        verdict = {
            "verdict": fallback_verdict,
            "reason": f"LLM 判定失敗 ({e})。類似度ベースのフォールバック (max={max_score:.3f})",
            "references": [similar_hits[0].doc_id] if similar_hits else [],
            "top_scores": [round(r.score, 3) for r in similar_hits[:5]],
        }

    # ⑤ JSONL ログに記録
    _dejavu_log_entry(text, verdict, similar_hits)

    return [TextContent(type="text", text=_format_dejavu_result(verdict))]


# PURPOSE: デジャブ検出結果をフォーマットする
def _format_dejavu_result(verdict: dict) -> str:
    """デジャブ検出結果を人間可読な形式にフォーマット。"""
    v = verdict.get("verdict", "UNKNOWN")
    icons = {"NOVEL": "✅", "SIMILAR": "🔶", "DUPLICATE": "🔴"}
    icon = icons.get(v, "❓")

    lines = [
        f"# {icon} Déjà Vu Check: {v}\n",
        f"**理由**: {verdict.get('reason', 'N/A')}",
    ]

    refs = verdict.get("references", [])
    if refs:
        lines.append(f"\n**参照すべき既存成果物**: {', '.join(refs)}")

    scores = verdict.get("top_scores", [])
    if scores:
        lines.append(f"\n**類似度スコア (上位)**: {scores}")

    if v == "SIMILAR":
        lines.append("\n> [!TIP]")
        lines.append("> 既存の成果物を参照した上で、差分を明確にしてから進めてください。")
    elif v == "DUPLICATE":
        lines.append("\n> [!WARNING]")
        lines.append("> ⚠️ 車輪の再発明の可能性が高い。既存の成果物を再利用できないか検討してください。")

    return "\n".join(lines)


# PURPOSE: デジャブ検出結果を JSONL ログに記録する
def _dejavu_log_entry(text: str, verdict: dict, hits: list) -> None:
    """検査結果を JSONL ログに追記。"""
    import json as _json
    from datetime import datetime, timezone

    try:
        _DEJAVU_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_preview": text[:200],
            "verdict": verdict.get("verdict"),
            "reason": verdict.get("reason"),
            "references": verdict.get("references", []),
            "hit_count": len(hits),
            "top_scores": verdict.get("top_scores", []),
        }
        with open(_DEJAVU_LOG, "a", encoding="utf-8") as f:
            f.write(_json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:  # noqa: BLE001
        log(f"dejavu_log write error: {e}")


# PURPOSE: 過去のデジャブ検出ログを表示する
async def _handle_dejavu_history(arguments: dict) -> list[TextContent]:
    """過去の検査結果ログを表示。"""
    import json as _json

    limit = arguments.get("limit", 10)

    if not _DEJAVU_LOG.exists():
        return [TextContent(type="text", text="Déjà Vu 検査ログはまだありません。")]

    try:
        with open(_DEJAVU_LOG, "r", encoding="utf-8") as f:
            all_lines = f.readlines()

        recent = all_lines[-limit:] if len(all_lines) > limit else all_lines
        icons = {"NOVEL": "✅", "SIMILAR": "🔶", "DUPLICATE": "🔴"}

        lines = [f"# Déjà Vu History (最新 {len(recent)} 件)\n"]
        for raw in reversed(recent):
            try:
                entry = _json.loads(raw)
                v = entry.get("verdict", "?")
                icon = icons.get(v, "❓")
                ts = entry.get("timestamp", "?")[:19]
                preview = entry.get("input_preview", "")[:80]
                lines.append(f"{icon} **{v}** [{ts}] {preview}...")
                if entry.get("reason"):
                    lines.append(f"   理由: {entry['reason']}")
                lines.append("")
            except _json.JSONDecodeError:
                continue

        return [TextContent(type="text", text="\n".join(lines))]
    except Exception as e:  # noqa: BLE001
        return [TextContent(type="text", text=f"Error reading déjà vu log: {e}")]


# ============================================================
# search_code / code_to_ccl ハンドラ
# ============================================================

# PURPOSE: CCL 演算子がクエリに含まれるかを判定する
# ブラケット演算子 (F:[, I:[ 等) は確実に CCL。
# ">>" 単独は Python ビットシフト等と衝突するため、"[" との共起を要件とする。
_CCL_BRACKET_OPS = ["F:[", "I:[", "C:[", "V:[", "E:[", "R:["]


def _detect_ccl_query(query: str) -> bool:
    """クエリが CCL パターンかを判定。

    判定ルール:
    - ブラケット演算子 (F:[, I:[ 等) があれば → CCL 確定
    - ">>" があり、かつ "[" もあれば → CCL (例: "F:[each]{...} >> I:[ok]{...}")
    - ">>" のみ → CCL ではない (偽陽性防止)
    """
    if any(op in query for op in _CCL_BRACKET_OPS):
        return True
    if ">>" in query and "[" in query:
        return True
    return False


# PURPOSE: RRF マージキーの生成 (ファイルパス + 行番号)
def _result_key(r) -> str:
    """検索結果の一意キー。重複検出に使用。"""
    fp = r.metadata.get("file_path", "")
    ls = r.metadata.get("line_start", "")
    return f"{fp}:{ls}"


# PURPOSE: Reciprocal Rank Fusion で text + structure 結果を統合
def _rrf_merge(
    text_results: list,
    struct_results: list,
    k_param: int = 60,
) -> list[dict]:
    """RRF (Reciprocal Rank Fusion) で2つのランキングを統合する。

    公式: RRF_score(d) = Σ 1/(k + rank_i(d))
    k = 60 (Cormack et al. 2009 の標準定数)

    Args:
        text_results: テキスト検索結果 (IndexedResult のリスト)
        struct_results: 構造検索結果 (IndexedResult のリスト)
        k_param: RRF 定数 (デフォルト: 60)

    Returns:
        統合結果のリスト。各要素は dict:
        {
            "result": IndexedResult (代表結果),
            "rrf_score": float,
            "sources": set ("text", "structure"),
            "text_rank": int | None,
            "struct_rank": int | None,
            "text_score": float | None,   # 元のコサイン類似度
            "struct_score": float | None,  # 元の構造スコア
            "ccl_expr": str,               # CCL 式 (structure 側から取得)
        }
    """
    # キー → 統合情報 のマップ
    fused: dict[str, dict] = {}

    # テキスト検索結果を登録
    for rank, r in enumerate(text_results, 1):
        key = _result_key(r)
        if key not in fused:
            fused[key] = {
                "result": r,
                "rrf_score": 0.0,
                "sources": set(),
                "text_rank": None,
                "struct_rank": None,
                "text_score": None,
                "struct_score": None,
                "ccl_expr": "",
            }
        fused[key]["rrf_score"] += 1.0 / (k_param + rank)
        fused[key]["sources"].add("text")
        fused[key]["text_rank"] = rank
        fused[key]["text_score"] = r.score

    # 構造検索結果を登録
    for rank, r in enumerate(struct_results, 1):
        key = _result_key(r)
        if key not in fused:
            fused[key] = {
                "result": r,
                "rrf_score": 0.0,
                "sources": set(),
                "text_rank": None,
                "struct_rank": None,
                "text_score": None,
                "struct_score": None,
                "ccl_expr": "",
            }
        fused[key]["rrf_score"] += 1.0 / (k_param + rank)
        fused[key]["sources"].add("structure")
        fused[key]["struct_rank"] = rank
        fused[key]["struct_score"] = r.score
        # 構造側のメタデータから CCL 式を取得
        ccl = r.metadata.get("ccl_expr", "")
        if ccl:
            fused[key]["ccl_expr"] = ccl

    # RRF スコア降順でソート
    merged = sorted(fused.values(), key=lambda x: x["rrf_score"], reverse=True)
    return merged


# PURPOSE: both モード — RRF 統合ランキング
def _handle_search_code_both(engine, query: str, k: int) -> list[TextContent]:
    """text と structure を RRF (Reciprocal Rank Fusion) で統合ランキングする。"""
    try:
        text_results = engine.search(query, sources=["code"], k=k)
    except Exception:  # noqa: BLE001
        text_results = []

    try:
        struct_results = engine.search(query, sources=["code_ccl"], k=k)
    except Exception:  # noqa: BLE001
        struct_results = []

    if not text_results and not struct_results:
        return [TextContent(type="text", text=f"No results for: {query} (mode: both)")]

    # RRF マージ
    merged = _rrf_merge(text_results, struct_results)

    # 上位 k 件に絞る
    merged = merged[:k]

    # 統計
    n_text = len(text_results)
    n_struct = len(struct_results)
    n_both = sum(1 for m in merged if len(m["sources"]) == 2)

    lines = [
        "## Code Search Results — 🔀 RRF Fusion (Text + Structure)",
        f"Query: `{query}`",
        f"Text: {n_text} / Structure: {n_struct} / Fused: {len(merged)} / Both: {n_both}\n",
    ]

    for i, m in enumerate(merged, 1):
        r = m["result"]
        ki_name = r.metadata.get("ki_name", r.doc_id)
        file_path = r.metadata.get("file_path", "")
        line_start = r.metadata.get("line_start", "?")
        line_end = r.metadata.get("line_end", "?")
        rrf_score = m["rrf_score"]

        # 出典タグ
        sources = m["sources"]
        if sources == {"text", "structure"}:
            tag = "📝🔍"
        elif "text" in sources:
            tag = "📝"
        else:
            tag = "🔍"

        # スコア詳細
        score_parts = [f"RRF: {rrf_score:.4f}"]
        if m["text_rank"] is not None:
            score_parts.append(f"T#{m['text_rank']}={m['text_score']:.3f}")
        if m["struct_rank"] is not None:
            score_parts.append(f"S#{m['struct_rank']}={m['struct_score']:.3f}")
        score_detail = " | ".join(score_parts)

        lines.append(f"**{i}. {ki_name}** ({score_detail}) {tag}")
        if file_path:
            lines.append(f"  📁 `{file_path}` L{line_start}-{line_end}")
        if m["ccl_expr"]:
            lines.append(f"  🔷 CCL: `{m['ccl_expr'][:200]}`")
        if r.content:
            preview = r.content[:150].replace("\n", " ").strip()
            lines.append(f"  📝 {preview}")
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]


# PURPOSE: search_code ツールのハンドラ
def _handle_search_code(arguments: dict) -> list[TextContent]:
    """コード検索ツール。text/structure/both/auto/similar 5モード。"""
    query = arguments.get("query", "")
    mode = arguments.get("mode") or arguments.get("code_mode", "auto")
    k = arguments.get("k", 10)

    # similar モード: 49d CCL 特徴量による Code→Code 構造検索
    if mode == "similar":
        return _handle_search_code_similar(query, k)

    # r1 モード: CCL 文字列完全一致による同型関数検索
    if mode == "r1":
        return _handle_search_code_r1(query, k)

    try:
        engine = get_engine()
    except Exception as e:  # noqa: BLE001
        return [TextContent(type="text", text=f"SearchEngine init error: {e}")]

    if engine is None:
        return [TextContent(type="text", text="SearchEngine not available")]

    # auto モード: クエリから判定
    if mode == "auto":
        mode = "structure" if _detect_ccl_query(query) else "text"

    # both モード: text + structure を並列検索してファセット表示
    if mode == "both":
        return _handle_search_code_both(engine, query, k)

    # 検索先を決定
    if mode == "structure":
        sources = ["code_ccl"]
        mode_label = "🔍 Structure (CCL)"
    else:
        sources = ["code"]
        mode_label = "📝 Text"

    try:
        results = engine.search(query, sources=sources, k=k)
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc()
        return [TextContent(type="text", text=f"Code search error: {e}\n\nTraceback:\n{tb}")]

    if not results:
        return [TextContent(type="text", text=f"No results for: {query} (mode: {mode})")]

    lines = [
        f"## Code Search Results — {mode_label}",
        f"Query: `{query}`",
        "Score: query と code chunk embedding の cosine 類似度。論文内容や命題支持の強さではありません。",
        f"Found {len(results)} results\n",
    ]

    for i, r in enumerate(results, 1):
        ki_name = r.metadata.get("ki_name", r.doc_id)
        ccl_expr = r.metadata.get("ccl_expr", "")
        file_path = r.metadata.get("file_path", "")
        line_start = r.metadata.get("line_start", "?")
        line_end = r.metadata.get("line_end", "?")

        lines.append(f"### {i}. {ki_name} (Score: {r.score:.3f})")
        if file_path:
            lines.append(f"   📁 `{file_path}` L{line_start}-{line_end}")
        if ccl_expr:
            lines.append(f"   🔷 CCL: `{ccl_expr[:200]}`")
        if r.content:
            preview = r.content[:200].replace("\n", " ").strip()
            lines.append(f"   📝 {preview}")
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]


# PURPOSE: Code→Code 構造類似検索ハンドラ (43d CCL 特徴量)


# PURPOSE: R1 CCL 完全一致検索ハンドラ (車輪の再開発検出)
def _handle_search_code_r1(query: str, k: int = 10) -> list[TextContent]:
    """CCL 文字列完全一致で同一構造の関数を検索する。

    query: 関数名 (file.py::func_name) または CCL 式そのもの。
    CCLFeatureIndex のメタデータ (ccl_expr) を辞書検索。
    インデックスは phantazein サーバー (旧 mneme) が常駐管理しているため追加ロード不要。
    """
    try:
        from mekhane.symploke.ccl_feature_index import CCLFeatureIndex
        from mekhane.paths import CODE_CCL_FEATURES_INDEX
    except ImportError as e:
        return [TextContent(type="text", text=f"CCLFeatureIndex not available: {e}")]

    # インデックスのロード (similar ハンドラと同じパス)
    import os
    index_path = str(CODE_CCL_FEATURES_INDEX)
    if not os.path.exists(index_path):
        return [TextContent(type="text", text=f"CCL Features Index not found: {index_path}\ncode_ingest.py --both でインデックスを構築してください。")]

    idx = CCLFeatureIndex()
    try:
        idx.load(index_path)
    except Exception as e:  # noqa: BLE001
        return [TextContent(type="text", text=f"Index load error: {e}")]

    if idx.count == 0:
        return [TextContent(type="text", text="Code index is empty")]

    # query が file::func 形式なら、まず対象関数の CCL を取得
    target_ccl = query  # デフォルト: query 自体が CCL 式
    source_meta = None
    if "::" in query:
        file_part, func_part = query.split("::", 1)
        # インデックス内から該当関数を検索
        for i in range(idx.count):
            meta = idx._metadata[i]
            if (meta.get("function_name") == func_part and
                    file_part in meta.get("file_path", "")):
                target_ccl = meta.get("ccl_expr", "")
                source_meta = meta
                break
        if not target_ccl:
            return [TextContent(type="text", text=f"Function not found in index: {query}")]

    if not target_ccl or len(target_ccl) < 10:
        return [TextContent(type="text", text=f"CCL expression too short or empty: {target_ccl[:50]}")]

    # 完全一致検索: O(N) だがメモリ上の辞書なので高速
    matches = []
    for i in range(idx.count):
        meta = idx._metadata[i]
        if meta.get("ccl_expr") == target_ccl:
            # self-match を除外
            if source_meta and (meta.get("file_path") == source_meta.get("file_path") and
                                meta.get("function_name") == source_meta.get("function_name")):
                continue
            matches.append(meta)

    if not matches:
        return [TextContent(type="text", text=f"No R1 exact matches for CCL: `{target_ccl[:100]}`")]

    # k 件に制限
    matches = matches[:k]

    lines = [
        "## 🔴 R1 Exact Match (CCL 完全一致)",
        f"Query: `{query}`",
        f"CCL: `{target_ccl[:150]}`",
        f"Found {len(matches)} identical structures\n",
    ]

    for i, m in enumerate(matches, 1):
        func_name = m.get("function_name", "?")
        file_path = m.get("file_path", "?")
        line_start = m.get("line_start", "?")
        line_end = m.get("line_end", "?")
        lines.append(
            f"{i}. **{func_name}** — `{Path(file_path).name}` L{line_start}-{line_end}"
        )
        lines.append(f"   📁 `{file_path}`")

    lines.append(f"\n💡 これらは同一の CCL 構造を持つ関数です。共通化を検討してください。")

    return [TextContent(type="text", text="\n".join(lines))]

def _handle_search_code_similar(query: str, k: int = 10) -> list[TextContent]:
    """49d CCL 特徴量ベクトルで構造的に類似した関数を検索。

    query: "file_name.py::function_name" 形式の関数参照。
           ファイルをパースし、対象関数の 49d ベクトルを計算して検索。
    """
    try:
        from mekhane.symploke.ccl_feature_index import CCLFeatureIndex
        from mekhane.paths import CODE_CCL_FEATURES_INDEX
    except ImportError as e:
        return [TextContent(type="text", text=f"⚠️ CCL Feature Index モジュールが利用できません: {e}")]

    # インデックスの読み込み
    index_path = str(CODE_CCL_FEATURES_INDEX)
    import os
    if not os.path.exists(index_path):
        return [TextContent(type="text", text=f"⚠️ CCL Feature Index が見つかりません: {index_path}\ncode_ingest.py --both でインデックスを構築してください。")]

    try:
        idx = CCLFeatureIndex()
        idx.load(index_path)
    except Exception as e:  # noqa: BLE001
        return [TextContent(type="text", text=f"⚠️ CCL Feature Index 読み込みエラー: {e}")]

    # query を file_path::function_name に分解
    if "::" in query:
        parts = query.split("::", 1)
        file_ref = parts[0].strip()
        func_name = parts[1].strip()
    else:
        # :: なしの場合はクエリ全体を関数名として扱い、インデックス内を直接検索
        return _handle_search_code_similar_by_name(idx, query.strip(), k)

    # ファイルパスの解決 (相対パス → 絶対パスの推定)
    from mekhane.paths import HGK_ROOT
    import pathlib
    file_path = pathlib.Path(file_ref)
    if not file_path.is_absolute():
        # HGK_ROOT 以下で検索
        candidates = list(pathlib.Path(HGK_ROOT).rglob(file_ref))
        if candidates:
            file_path = candidates[0]
        else:
            return [TextContent(type="text", text=f"⚠️ ファイルが見つかりません: {file_ref}")]

    try:
        results = idx.find_similar_to(
            str(file_path), func_name, k=k + 1  # 自己を含むので +1
        )
    except Exception as e:  # noqa: BLE001
        return [TextContent(type="text", text=f"⚠️ 検索エラー: {e}")]

    # 自己を除外
    filtered = [
        r for r in results
        if not (r.function_name == func_name and str(file_path).endswith(r.file_path.split("/")[-1]))
    ][:k]

    if not filtered:
        return [TextContent(type="text", text=f"構造的に類似した関数が見つかりませんでした: {query}")]

    lines = [
        f"## Code→Code 構造検索結果 — 🔬 Similar",
        f"Query: `{query}` (49d CCL Feature Vector)",
        f"Found {len(filtered)} similar functions\n",
    ]

    for i, r in enumerate(filtered, 1):
        lines.append(f"### {i}. {r.function_name} (Similarity: {r.score:.3f})")
        if r.file_path:
            lines.append(f"   📁 `{r.file_path}` L{r.line_start}")
        if r.ccl_expr:
            lines.append(f"   🔷 CCL: `{r.ccl_expr[:200]}`")
        # メタデータ要約
        if r.metadata:
            code_type = r.metadata.get("code_type", "")
            if code_type:
                lines.append(f"   📋 Type: {code_type}")
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]


# PURPOSE: 関数名のみで構造類似検索 (:: なし入力のフォールバック)
def _handle_search_code_similar_by_name(
    idx, func_name: str, k: int = 10
) -> list[TextContent]:
    """インデックス内の関数名で検索し、そのベクトルで類似検索。"""
    from mcp.types import TextContent

    # インデックス内の _metadata リストから関数名を検索
    target_vec = None
    target_file = ""
    for i, meta in enumerate(idx._metadata):
        if meta.get("function_name") == func_name:
            target_vec = idx._vectors[i]
            target_file = meta.get("file_path", "")
            break

    if target_vec is None:
        return [TextContent(type="text", text=f"⚠️ インデックス内に関数 '{func_name}' が見つかりません。\nfile::func 形式で指定してください。")]

    # そのベクトルで検索 (自己除外付き)
    try:
        results = idx.search_similar(
            target_vec.tolist(),
            k=k + 1,
            exclude_self=True,
            self_file=target_file,
            self_func=func_name,
        )
    except Exception as e:  # noqa: BLE001
        return [TextContent(type="text", text=f"⚠️ 検索エラー: {e}")]

    filtered = results[:k]

    if not filtered:
        return [TextContent(type="text", text=f"構造的に類似した関数が見つかりませんでした: {func_name}")]

    lines = [
        f"## Code→Code 構造検索結果 — 🔬 Similar",
        f"Query: `{func_name}` (インデックス内ベクトル使用)",
        f"Found {len(filtered)} similar functions\n",
    ]

    for i, r in enumerate(filtered, 1):
        lines.append(f"### {i}. {r.function_name} (Similarity: {r.score:.3f})")
        if r.file_path:
            lines.append(f"   📁 `{r.file_path}` L{r.line_start}")
        if r.ccl_expr:
            lines.append(f"   🔷 CCL: `{r.ccl_expr[:200]}`")
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]


# PURPOSE: code_to_ccl ツールのハンドラ
def _handle_code_to_ccl(arguments: dict) -> list[TextContent]:
    """Python コードを CCL 構造式に変換。"""
    code = arguments.get("code", "")

    if not code.strip():
        return [TextContent(type="text", text="⚠️ 空のコードが渡されました")]

    try:
        from mekhane.symploke.code_ingest import code_snippet_to_ccl
        ccl_expr = code_snippet_to_ccl(code)
    except Exception as e:  # noqa: BLE001
        return [TextContent(type="text", text=f"CCL 変換エラー: {e}")]

    lines = [
        "## Python → CCL 変換結果",
        "",
        f"```ccl",
        ccl_expr,
        "```",
        "",
        "この CCL 式を `search_code` の `structure` モードで検索すると、同じ構造のコードが見つかります。",
    ]

    return [TextContent(type="text", text="\n".join(lines))]


if __name__ == "__main__":
    # Initialize engine before server starts
    get_engine()
    _base.install_all_hooks()
    _base.run()
