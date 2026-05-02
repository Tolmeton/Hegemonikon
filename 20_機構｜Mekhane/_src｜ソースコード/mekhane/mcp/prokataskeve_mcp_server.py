#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/prokataskeve_mcp_server.py A0→V-001 前処理 MCP サーバー
"""
Prokataskeuē MCP Server — Pre-processing Pipeline

Exposes the depth-aware pre-processing pipeline as an MCP tool.
Supports L0-L4 depth levels synchronized with main processing depth.

Tools:
  - prokataskeve_preprocess: Run the pre-processing pipeline
  - ping: Health check
"""

from mekhane.mcp.mcp_base import MCPBase

# Initialize via shared infrastructure
_base = MCPBase(
    name="prokataskeve",
    version="1.0.0",
    instructions=(
        "Prokataskeuē: 前処理パイプライン (V-001)。"
        "入力テキストを深度 (L0-L4) に応じて前処理し、"
        "正規化・エンティティ抽出・意図分類・参照解決などを実行。"
    ),
)
server = _base.server
log = _base.log
TextContent = _base.TextContent
Tool = _base.Tool

# Lazy imports
_pipeline = None


# PURPOSE: パイプラインの遅延初期化
def _get_pipeline():
    """Lazy-initialize PreprocessPipeline on first use."""
    global _pipeline
    if _pipeline is None:
        from mekhane.mcp.prokataskeve import PreprocessPipeline
        _pipeline = PreprocessPipeline()
        log("PreprocessPipeline initialized (lazy)")
    return _pipeline


# PURPOSE: ツール一覧の定義
@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        Tool(
            name="ping",
            description=(
                "Health check. Returns instantly to verify server is alive. "
                "Example: ping() Errors on invalid input or internal failure."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="prokataskeve_preprocess",
            description=(
                "入力テキストを前処理パイプラインで処理。深度に応じた機能を適用: "
                "L0 (正規化+エンティティ抽出+確定情報, <50ms), "
                "L1 (+ 意図分類+参照解決+クエリ書換え, <300ms), "
                "L2 (+ 目的抽出+テンプレートマッチ+多角化+曖昧性検出+文脈統合+Few-Shot, <1s), "
                "L3 (+ 矛盾検出+修正提案+HyDE+過去参照, <3s), "
                "L4 (+ 予測的先読み+プリフェッチ, <5s)。 "
                "Returns: preprocessed result with entities, intent, refs. "
                "Example: prokataskeve_preprocess(text='...', depth='L1') "
                "Errors if required params (text) are missing or invalid."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "前処理対象のテキスト",
                    },
                    "depth": {
                        "type": "string",
                        "default": "L1",
                        "description": "前処理深度 (L0, L1, L2, L3, L4)。デフォルト L1。",
                        "enum": ["L0", "L1", "L2", "L3", "L4"],
                    },
                    "session_state": {
                        "type": "object",
                        "description": (
                            "セッション状態 (任意)。参照解決用: "
                            "{last_topic, last_file, last_paper} など"
                        ),
                    },
                },
                "required": ["text"],
            },
        ),
    ]


# PURPOSE: ツール呼出しハンドラ
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    log(f"Tool call: {name} with args: {arguments}")

    try:
        if name == "ping":
            return [TextContent(type="text", text="pong — prokataskeve v1.0.0")]

        elif name == "prokataskeve_preprocess":
            return await handle_preprocess(arguments)

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:  # noqa: BLE001
        log(f"Tool error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# PURPOSE: 前処理パイプライン実行ハンドラ
async def handle_preprocess(arguments: dict):
    """Run the pre-processing pipeline."""
    import json
    import time

    text = arguments.get("text", "")
    if not text:
        return [TextContent(type="text", text="Error: text is required")]

    depth = arguments.get("depth", "L1")
    session_state = arguments.get("session_state")

    pipeline = _get_pipeline()

    t0 = time.monotonic()
    result = await pipeline.run(
        text=text,
        depth=depth,
        session_state=session_state,
    )
    total_ms = (time.monotonic() - t0) * 1000

    log(
        f"Preprocess done: depth={depth}, "
        f"functions={len(result.functions_executed)}, "
        f"latency={total_ms:.1f}ms"
    )

    # Format output
    data = result.to_dict()
    output = json.dumps(data, ensure_ascii=False, indent=2)

    return [TextContent(type="text", text=output)]


if __name__ == "__main__":
    _base.install_all_hooks()
    _base.run()
