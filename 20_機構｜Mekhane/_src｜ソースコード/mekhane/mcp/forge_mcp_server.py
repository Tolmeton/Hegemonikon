#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/forge_mcp_server.py A0→FM-Forge MCP サーバー
"""
FM-Forge MCP Server v1.0 — FileMaker 開発自動化

Forge CLI/API の機能を MCP ツールとして公開する。
Forge 本体は FM ワークスペース内に残し、sys.path 追加で import。

Tools: forge_ping, forge_status, forge_new, forge_analyze,
       forge_analyze_excel, forge_schema, forge_generate,
       forge_validate, forge_verify, forge_ddr_diff, forge_snippets
"""

import sys
from pathlib import Path

from mekhane.mcp.mcp_base import MCPBase, StdoutSuppressor, run_sync

# Initialize via shared infrastructure
_base = MCPBase(
    name="forge",
    version="1.0.0",
    instructions="FM-Forge: FileMaker 開発自動化 (DDR解析, Excel解析, XML生成, マッピング, スニペットDB)",
)
server = _base.server
log = _base.log
TextContent = _base.TextContent
Tool = _base.Tool


# =============================================================================
# Forge パス解決 — HGK 外部のコードを動的に import
# =============================================================================

_FORGE_PARENT = None
_forge_ready = False


def _ensure_forge_path():
    """Forge パッケージの親ディレクトリを sys.path に追加。"""
    global _FORGE_PARENT, _forge_ready
    if _forge_ready:
        return True

    # Forge の所在候補 (WSL パス)
    candidates = [
        Path.home() / "Sync/oikos/02_作業場｜Workspace/A_仕事｜Work/a_ファイルメーカー｜FileMaker/02_その他｜Other",
        # Syncthing 同期先のフォールバック
        Path("/home/makaron8426/Sync/oikos/02_作業場｜Workspace/A_仕事｜Work/a_ファイルメーカー｜FileMaker/02_その他｜Other"),
    ]

    for candidate in candidates:
        forge_dir = candidate / "forge"
        if forge_dir.exists() and (forge_dir / "__init__.py").exists():
            _FORGE_PARENT = candidate
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            _forge_ready = True
            log(f"Forge path resolved: {forge_dir}")
            return True

    log("❌ Forge パッケージが見つかりません")
    return False


def _get_forge_project():
    """Forge の ProjectConfig をインポート。"""
    if not _ensure_forge_path():
        return None
    try:
        with StdoutSuppressor():
            from forge.project import ProjectConfig
        return ProjectConfig
    except ImportError as e:
        log(f"Forge import error: {e}")
        return None


# =============================================================================
# Tool definitions
# =============================================================================

# PURPOSE: [L2-auto] list_tools の非同期処理定義
@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        Tool(
            name="forge_ping",
            description="FM-Forge ヘルスチェック。サーバーの生存確認。",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="forge_status",
            description="全 FM プロジェクトの状態一覧を取得。 Returns: プロジェクト名、DDR、Excel、最終更新日。",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="forge_new",
            description="新規 FM プロジェクトを初期化。project.yaml + 標準ディレクトリを生成。 Example: forge_new(name='sangyoi', display_name='産業医科大学')",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "プロジェクト ID (英数字)"},
                    "display_name": {"type": "string", "description": "表示名 (日本語可)"},
                    "ddr_path": {"type": "string", "description": "DDR XML ファイルパス (任意)"},
                    "excel_path": {"type": "string", "description": "Excel テンプレートパス (任意)"},
                    "fm_version": {"type": "string", "default": "unknown", "description": "FM バージョン"},
                    "description": {"type": "string", "default": "", "description": "プロジェクト説明"},
                },
                "required": ["name", "display_name"],
            },
        ),
        Tool(
            name="forge_analyze",
            description="DDR XML を解析して構造化データ (JSON) に変換。 Example: forge_analyze(project='sangyoi')",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "プロジェクト名"},
                    "verbose": {"type": "boolean", "default": False, "description": "詳細出力"},
                },
                "required": ["project"],
            },
        ),
        Tool(
            name="forge_analyze_excel",
            description="Excel テンプレートのシート構造・セル内容を解析。 Example: forge_analyze_excel(project='sangyoi')",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "プロジェクト名"},
                },
                "required": ["project"],
            },
        ),
        Tool(
            name="forge_schema",
            description="DDR 構造から mapping.yaml の雛形を自動生成。 Example: forge_schema(project='sangyoi', table='腎生検')",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "プロジェクト名"},
                    "table": {"type": "string", "description": "テーブル名 (省略時はテーブル一覧を返す)"},
                    "fm_file": {"type": "string", "description": "FM ファイル名 (J/K 等)"},
                    "table_occurrence": {"type": "string", "description": "テーブルオカレンス名"},
                },
                "required": ["project"],
            },
        ),
        Tool(
            name="forge_generate",
            description="mapping.yaml から FM スクリプト XML を生成。 Example: forge_generate(project='sangyoi')",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "プロジェクト名"},
                    "mapping": {"type": "string", "default": "mapping.yaml", "description": "マッピングファイル名"},
                    "block": {"type": "string", "description": "特定ブロックのみ生成"},
                },
                "required": ["project"],
            },
        ),
        Tool(
            name="forge_validate",
            description="mapping.yaml の構文検証。 Example: forge_validate(project='sangyoi')",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "プロジェクト名"},
                    "mapping": {"type": "string", "default": "mapping.yaml", "description": "マッピングファイル名"},
                },
                "required": ["project"],
            },
        ),
        Tool(
            name="forge_verify",
            description="mapping.yaml と DDR 構造の整合性検証。 Example: forge_verify(project='sangyoi')",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "プロジェクト名"},
                    "mapping": {"type": "string", "default": "mapping.yaml", "description": "マッピングファイル名"},
                },
                "required": ["project"],
            },
        ),
        Tool(
            name="forge_ddr_diff",
            description="2つの DDR XML を比較し、差分レポートを生成。 Example: forge_ddr_diff(before='old.xml', after='new.xml')",
            inputSchema={
                "type": "object",
                "properties": {
                    "before": {"type": "string", "description": "比較元 DDR XML パス"},
                    "after": {"type": "string", "description": "比較先 DDR XML パス"},
                    "table": {"type": "string", "description": "特定テーブルのみ比較"},
                },
                "required": ["before", "after"],
            },
        ),
        Tool(
            name="forge_snippets",
            description="FM スニペット DB の操作 (一覧/検索/追加/統計)。 Example: forge_snippets(action='list')",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "search", "stats", "add", "import-ddr", "export"],
                        "description": "操作種別",
                    },
                    "query": {"type": "string", "description": "検索クエリ (search 用)"},
                    "type": {"type": "string", "description": "フィルタ: スニペット種別 (list 用)"},
                    "tag": {"type": "string", "description": "フィルタ: タグ (list 用)"},
                    "limit": {"type": "integer", "default": 20, "description": "最大件数"},
                    "id": {"type": "integer", "description": "スニペット ID (export 用)"},
                    "file": {"type": "string", "description": "ファイルパス (add/import-ddr 用)"},
                },
                "required": ["action"],
            },
        ),
    ]


# =============================================================================
# Tool dispatch
# =============================================================================

# PURPOSE: [L2-auto] call_tool の非同期処理定義
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    log(f"Tool call: {name} with args: {arguments}")

    try:
        if name == "forge_ping":
            return await handle_ping()
        elif name == "forge_status":
            return await handle_status()
        elif name == "forge_new":
            return await handle_new(arguments)
        elif name == "forge_analyze":
            return await handle_analyze(arguments)
        elif name == "forge_analyze_excel":
            return await handle_analyze_excel(arguments)
        elif name == "forge_schema":
            return await handle_schema(arguments)
        elif name == "forge_generate":
            return await handle_generate(arguments)
        elif name == "forge_validate":
            return await handle_validate(arguments)
        elif name == "forge_verify":
            return await handle_verify(arguments)
        elif name == "forge_ddr_diff":
            return await handle_ddr_diff(arguments)
        elif name == "forge_snippets":
            return await handle_snippets(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:  # noqa: BLE001
        log(f"Tool error: {e}")
        import traceback
        tb = traceback.format_exc()
        return [TextContent(type="text", text=f"❌ Error in {name}: {e}\n\n{tb}")]


# =============================================================================
# Handlers
# =============================================================================

async def handle_ping():
    """ヘルスチェック。"""
    forge_ok = _ensure_forge_path()
    status = "✅ Forge パス解決済み" if forge_ok else "❌ Forge パス未解決"
    return [TextContent(type="text", text=f"pong — FM-Forge MCP v1.0\n{status}")]


async def handle_status():
    """全プロジェクト一覧。"""
    ProjectConfig = _get_forge_project()
    if ProjectConfig is None:
        return [TextContent(type="text", text="❌ Forge モジュールが利用できません")]

    projects = await run_sync(ProjectConfig.list_all)
    if not projects:
        return [TextContent(type="text", text="📭 プロジェクトがありません\n\n`forge_new` で新規作成してください。")]

    output = f"=== FM-Forge プロジェクト一覧 ({len(projects)} 件) ===\n\n"
    for name in projects:
        try:
            config = await run_sync(ProjectConfig.load, name)
            ddr_count = len(config.ddr_paths) if config.ddr_paths else 0
            excel_count = len(config.excel_templates) if config.excel_templates else 0
            output += f"📁 **{config.display_name}** (`{name}`)\n"
            output += f"   FM: {config.fm_version} | DDR: {ddr_count} | Excel: {excel_count}\n"
            if config.description:
                output += f"   {config.description}\n"
            output += "\n"
        except Exception as e:  # noqa: BLE001
            output += f"📁 `{name}` — ⚠️ 読み込みエラー: {e}\n\n"

    return [TextContent(type="text", text=output)]


async def handle_new(arguments: dict):
    """新規プロジェクト初期化。"""
    ProjectConfig = _get_forge_project()
    if ProjectConfig is None:
        return [TextContent(type="text", text="❌ Forge モジュールが利用できません")]

    name = arguments.get("name", "")
    display_name = arguments.get("display_name", "")
    if not name or not display_name:
        return [TextContent(type="text", text="❌ name と display_name は必須です")]

    config = ProjectConfig(
        name=name,
        display_name=display_name,
        ddr_paths=[arguments["ddr_path"]] if arguments.get("ddr_path") else [],
        excel_templates=[arguments["excel_path"]] if arguments.get("excel_path") else [],
        fm_version=arguments.get("fm_version", "unknown"),
        description=arguments.get("description", ""),
    )

    created = await run_sync(config.scaffold)

    output = f"✅ プロジェクト作成完了: **{display_name}** (`{name}`)\n\n"
    output += "生成されたファイル/ディレクトリ:\n"
    for p in created:
        output += f"  📄 {p.name}\n"
    output += f"\n設定ファイル: {config.config_path}\n"
    output += "\n次のステップ:\n"
    output += "1. DDR XML を `ddr/` に配置\n"
    output += "2. `forge_analyze` で構造解析\n"
    output += "3. `forge_schema` で mapping 雛形生成\n"

    return [TextContent(type="text", text=output)]


async def handle_analyze(arguments: dict):
    """DDR XML 解析。"""
    if not _ensure_forge_path():
        return [TextContent(type="text", text="❌ Forge モジュールが利用できません")]

    project_name = arguments.get("project", "")
    if not project_name:
        return [TextContent(type="text", text="❌ project は必須です")]

    def _run():
        from forge.project import ProjectConfig
        from forge.engines.analyze import DDRAnalyzer

        config = ProjectConfig.load(project_name)
        if not config.ddr_paths:
            return "⚠️ DDR XML が登録されていません。project.yaml に ddr_paths を追加してください。"

        results = []
        for ddr_path_str in config.ddr_paths:
            p = Path(ddr_path_str)
            if not p.exists():
                results.append(f"❌ ファイル未発見: {p}")
                continue

            analyzer = DDRAnalyzer(ddr_path_str)
            structure = analyzer.analyze()
            s = structure.summary

            # Save structure JSON
            output_dir = config.project_dir / "structure"
            output_dir.mkdir(parents=True, exist_ok=True)
            json_path = output_dir / f"{p.stem}_structure.json"
            structure.to_json(json_path)

            results.append(
                f"✅ {p.name}\n"
                f"   テーブル: {s.get('tables', '?')} | フィールド: {s.get('fields', '?')}\n"
                f"   TO: {s.get('table_occurrences', '?')} | リレーション: {s.get('relationships', '?')}\n"
                f"   => {json_path}\n"
            )

        return f"=== DDR 解析結果 ({project_name}) ===\n\n" + "\n".join(results)

    with StdoutSuppressor():
        result = await run_sync(_run, timeout_sec=60.0)
    return [TextContent(type="text", text=result)]


async def handle_analyze_excel(arguments: dict):
    """Excel テンプレート解析。"""
    if not _ensure_forge_path():
        return [TextContent(type="text", text="❌ Forge モジュールが利用できません")]

    project_name = arguments.get("project", "")
    if not project_name:
        return [TextContent(type="text", text="❌ project は必須です")]

    def _run():
        from forge.project import ProjectConfig
        from forge.engines.excel_analyze import ExcelAnalyzer

        config = ProjectConfig.load(project_name)
        if not config.excel_templates:
            return "⚠️ Excel テンプレートが登録されていません。project.yaml に excel_templates を追加してください。"

        results = []
        for excel_path_str in config.excel_templates:
            p = Path(excel_path_str)
            if not p.exists():
                results.append(f"❌ ファイル未発見: {p}")
                continue

            try:
                analyzer = ExcelAnalyzer(excel_path_str)
                dump = analyzer.dump_for_claude()
                results.append(f"✅ {p.name}\n{dump}\n")
            except Exception as e:  # noqa: BLE001
                results.append(f"❌ {p.name}: {e}")

        return f"=== Excel 解析結果 ({project_name}) ===\n\n" + "\n".join(results)

    with StdoutSuppressor():
        result = await run_sync(_run, timeout_sec=60.0)
    return [TextContent(type="text", text=result)]


async def handle_schema(arguments: dict):
    """mapping.yaml 雛形生成。"""
    if not _ensure_forge_path():
        return [TextContent(type="text", text="❌ Forge モジュールが利用できません")]

    project_name = arguments.get("project", "")
    if not project_name:
        return [TextContent(type="text", text="❌ project は必須です")]

    table = arguments.get("table")
    fm_file = arguments.get("fm_file")
    table_occurrence = arguments.get("table_occurrence")

    def _run():
        from forge.project import ProjectConfig
        from forge.engines.schema_forge import SchemaForge

        config = ProjectConfig.load(project_name)
        structure_dir = config.project_dir / "structure"
        json_files = list(structure_dir.glob("*_structure.json")) if structure_dir.exists() else []
        if not json_files:
            return "⚠️ 構造データがありません。先に `forge_analyze` を実行してください。"

        # Select structure file
        src = json_files[0]
        if fm_file:
            matched = [f for f in json_files if f"({fm_file})" in f.name.upper()]
            if matched:
                src = matched[0]

        sf = SchemaForge(src)
        tables = sf.list_tables()

        if not table:
            return f"=== テーブル一覧 ({project_name}) ===\n\n" + "\n".join(f"- {t}" for t in tables) + "\n\n`table` パラメータでテーブル名を指定してください。"

        if table not in tables:
            return f"❌ テーブル '{table}' が見つかりません。\n利用可能: {', '.join(tables)}"

        used_fm_file = fm_file or config.name
        out_name = f"mapping_{used_fm_file}_skeleton.yaml"
        out_path = config.project_dir / out_name

        result_path = sf.generate_skeleton(
            table_name=table,
            output_path=out_path,
            project_name=config.name,
            fm_file=used_fm_file,
            table_occurrence=table_occurrence or table,
        )

        return f"✅ mapping 雛形生成完了\n\n  テーブル: {table}\n  出力: {result_path}\n\n次のステップ: mapping ファイルを編集し、Excel列 ↔ FM フィールドの対応を記入してください。"

    with StdoutSuppressor():
        result = await run_sync(_run, timeout_sec=30.0)
    return [TextContent(type="text", text=result)]


async def handle_generate(arguments: dict):
    """FM スクリプト XML 生成。"""
    if not _ensure_forge_path():
        return [TextContent(type="text", text="❌ Forge モジュールが利用できません")]

    project_name = arguments.get("project", "")
    mapping_name = arguments.get("mapping", "mapping.yaml")
    block = arguments.get("block")

    if not project_name:
        return [TextContent(type="text", text="❌ project は必須です")]

    def _run():
        from forge.project import ProjectConfig
        from forge.engines.xml_generate import XMLGenerator
        from forge.engines.mapping import MappingDefinition

        config = ProjectConfig.load(project_name)
        mapping_path = config.project_dir / mapping_name
        if not mapping_path.exists():
            return f"❌ マッピングファイル未発見: {mapping_path}"

        defn = MappingDefinition.load(mapping_path)
        gen = XMLGenerator(defn)

        if block:
            blocks = [b for b in defn.blocks if b.name == block]
            if not blocks:
                available = [b.name for b in defn.blocks]
                return f"❌ ブロック '{block}' が見つかりません。\n利用可能: {', '.join(available)}"
            xml_str = gen.generate_block(blocks[0])
        else:
            xml_str = gen.generate_all()

        # Save to output directory
        output_dir = config.project_dir / "scripts"
        output_dir.mkdir(parents=True, exist_ok=True)
        suffix = f"_{block}" if block else ""
        output_path = output_dir / f"generated{suffix}.xml"
        output_path.write_text(xml_str, encoding="utf-8")

        line_count = xml_str.count("\n") + 1
        return (
            f"✅ FM スクリプト XML 生成完了\n\n"
            f"  出力: {output_path}\n"
            f"  行数: {line_count}\n"
            f"  ブロック: {block or '全体'}\n\n"
            f"次のステップ: `forge clip set {output_path}` で FM クリップボードに設定し、FM Pro で Ctrl+V"
        )

    with StdoutSuppressor():
        result = await run_sync(_run, timeout_sec=60.0)
    return [TextContent(type="text", text=result)]


async def handle_validate(arguments: dict):
    """mapping.yaml 構文検証。"""
    if not _ensure_forge_path():
        return [TextContent(type="text", text="❌ Forge モジュールが利用できません")]

    project_name = arguments.get("project", "")
    mapping_name = arguments.get("mapping", "mapping.yaml")

    if not project_name:
        return [TextContent(type="text", text="❌ project は必須です")]

    def _run():
        from forge.project import ProjectConfig
        from forge.engines.mapping import MappingDefinition

        config = ProjectConfig.load(project_name)
        mapping_path = config.project_dir / mapping_name
        if not mapping_path.exists():
            return f"❌ マッピングファイル未発見: {mapping_path}"

        try:
            defn = MappingDefinition.load(mapping_path)
            block_count = len(defn.blocks) if hasattr(defn, 'blocks') else 0
            return (
                f"✅ mapping.yaml 構文検証 OK\n\n"
                f"  ファイル: {mapping_path}\n"
                f"  プロジェクト: {defn.project_name}\n"
                f"  FM ファイル: {defn.fm_file}\n"
                f"  ブロック数: {block_count}\n"
            )
        except Exception as e:  # noqa: BLE001
            return f"❌ mapping.yaml 構文エラー\n\n{e}"

    with StdoutSuppressor():
        result = await run_sync(_run, timeout_sec=15.0)
    return [TextContent(type="text", text=result)]


async def handle_verify(arguments: dict):
    """DDR 整合性検証。"""
    if not _ensure_forge_path():
        return [TextContent(type="text", text="❌ Forge モジュールが利用できません")]

    project_name = arguments.get("project", "")
    mapping_name = arguments.get("mapping", "mapping.yaml")

    if not project_name:
        return [TextContent(type="text", text="❌ project は必須です")]

    def _run():
        from forge.project import ProjectConfig
        from forge.engines.analyze import DDRAnalyzer
        from forge.engines.verify import Verifier
        from forge.engines.mapping import MappingDefinition

        config = ProjectConfig.load(project_name)
        mapping_path = config.project_dir / mapping_name
        if not mapping_path.exists():
            return f"❌ マッピングファイル未発見: {mapping_path}"

        defn = MappingDefinition.load(mapping_path)

        # Load DDR structure
        structure = None
        if config.ddr_paths:
            fm_file = defn.fm_file.upper() if defn.fm_file else ""
            for ddr_path in config.ddr_paths:
                p = Path(ddr_path)
                if p.exists() and (not fm_file or f"({fm_file})" in p.name.upper()):
                    analyzer = DDRAnalyzer(ddr_path)
                    structure = analyzer.analyze()
                    break
            if structure is None:
                for ddr_path in config.ddr_paths:
                    if Path(ddr_path).exists():
                        analyzer = DDRAnalyzer(ddr_path)
                        structure = analyzer.analyze()
                        break

        # DDR JSON for coverage
        ddr_json = None
        structure_dir = config.project_dir / "structure"
        if structure_dir.exists():
            fm_file_upper = defn.fm_file.upper() if defn.fm_file else ""
            json_files = list(structure_dir.glob("*_structure.json"))
            matched = [f for f in json_files if fm_file_upper and f"({fm_file_upper})" in f.name.upper()]
            ddr_json = matched[0] if matched else (json_files[0] if json_files else None)

        v = Verifier(defn, structure, ddr_json_path=ddr_json)
        report = v.full_check()

        # Format report
        output = f"=== DDR 整合性検証 ({project_name}) ===\n\n"
        if isinstance(report, dict):
            for key, value in report.items():
                output += f"**{key}**: {value}\n"
        else:
            output += str(report)
        return output

    with StdoutSuppressor():
        result = await run_sync(_run, timeout_sec=60.0)
    return [TextContent(type="text", text=result)]


async def handle_ddr_diff(arguments: dict):
    """DDR 差分比較。"""
    if not _ensure_forge_path():
        return [TextContent(type="text", text="❌ Forge モジュールが利用できません")]

    before = arguments.get("before", "")
    after = arguments.get("after", "")
    table_filter = arguments.get("table")

    if not before or not after:
        return [TextContent(type="text", text="❌ before と after は必須です")]

    def _run():
        from forge.engines.ddr_diff import DDRDiff

        before_path = Path(before)
        after_path = Path(after)

        for p in [before_path, after_path]:
            if not p.exists():
                return f"❌ ファイル未発見: {p}"

        diff = DDRDiff.from_files(before_path, after_path)
        report = diff.compare(table_filter=table_filter)
        return report.summary()

    with StdoutSuppressor():
        result = await run_sync(_run, timeout_sec=30.0)
    return [TextContent(type="text", text=result)]


async def handle_snippets(arguments: dict):
    """スニペット DB 操作。"""
    if not _ensure_forge_path():
        return [TextContent(type="text", text="❌ Forge モジュールが利用できません")]

    action = arguments.get("action", "list")

    def _run():
        from forge.engines.snippet_db import SnippetDB

        db = SnippetDB()
        try:
            if action == "list":
                snippets = db.list(
                    type=arguments.get("type"),
                    tag=arguments.get("tag"),
                    limit=arguments.get("limit", 20),
                )
                if not snippets:
                    return "📭 スニペットがありません"
                output = f"📋 スニペット一覧 ({len(snippets)} 件)\n\n"
                for s in snippets:
                    tags_str = f" [{s.tags}]" if s.tags else ""
                    output += f"  #{s.id:4d}  {s.type:20s}  {s.name}{tags_str}\n"
                return output

            elif action == "search":
                query = arguments.get("query", "")
                if not query:
                    return "❌ query は必須です"
                results = db.search(query, limit=arguments.get("limit", 20))
                if not results:
                    return f"🔍 '{query}' に一致するスニペットはありません"
                output = f"🔍 '{query}' — {len(results)} 件\n\n"
                for s in results:
                    output += f"  #{s.id:4d}  {s.type:20s}  {s.name}\n"
                    if s.source:
                        output += f"         source: {s.source}\n"
                return output

            elif action == "stats":
                stats = db.stats()
                output = f"📊 スニペット DB 統計\n\n"
                output += f"   合計: {stats['total']} 件\n"
                output += f"   DB: {stats['db_path']}\n"
                if stats["by_type"]:
                    output += f"\n   種別:\n"
                    for t, c in stats["by_type"].items():
                        output += f"     {t}: {c}\n"
                return output

            elif action == "export":
                snippet_id = arguments.get("id")
                if snippet_id is None:
                    return "❌ id は必須です"
                xml = db.export_xml(snippet_id)
                if xml is None:
                    return f"❌ スニペット #{snippet_id} が見つかりません"
                return f"✅ スニペット #{snippet_id}\n\n```xml\n{xml}\n```"

            elif action == "add":
                file_path = arguments.get("file")
                if not file_path:
                    return "❌ file は必須です"
                p = Path(file_path)
                if not p.exists():
                    return f"❌ ファイル未発見: {p}"
                xml_text = p.read_text(encoding="utf-8")
                sid = db.import_fmxmlsnippet(xml_text, name="", source=p.name)
                s = db.get(sid)
                return f"✅ スニペット追加: #{sid} {s.name} ({s.type})"

            elif action == "import-ddr":
                file_path = arguments.get("file")
                if not file_path:
                    return "❌ file は必須です"
                p = Path(file_path)
                if not p.exists():
                    return f"❌ ファイル未発見: {p}"
                counts = db.import_from_ddr(p)
                return (
                    f"✅ DDR インポート完了: {p.name}\n"
                    f"   Custom Functions: {counts['custom_functions']}\n"
                    f"   Scripts: {counts['scripts']}\n"
                    f"   合計: {counts['total']}\n"
                )

            else:
                return f"❌ 不明なアクション: {action}\n利用可能: list, search, stats, add, import-ddr, export"

        finally:
            db.close()

    with StdoutSuppressor():
        result = await run_sync(_run, timeout_sec=30.0)
    return [TextContent(type="text", text=result)]


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    _base.install_all_hooks()
    _base.run()
