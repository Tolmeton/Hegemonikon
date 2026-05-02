# HGK APP Agent 実装仕様書
>
> Generated: 2026-02-22 by Cowork Claude (対話インターフェース)
> Target: IDE Claude / Gemini (Cortex API 経由の実装者)
> Version: v1.0

---

## 目的

HGK APP を「Antigravity IDE と同等の自律的 AI エージェント環境」にする。
APP 内の LLM が Gateway ツール群を自律的に呼び出し、HGK の開発自体を APP から行えるようにする。

---

## 現状分析

### 既に存在するもの

- `mekhane/ochema/cortex_client.py` — `ask_with_tools()` がエージェントループ実装済み
- `mekhane/ochema/tools.py` — 7ツール定義 + `execute_tool()` ディスパッチャ + Claude text-based tool use パーサー
- `hgk/api/serve.py` — `/api/ask`, `/api/ask/stream` (LLM プロキシ)
- `hgk/src/views/chat.ts` — SSE ストリーミング対応チャット UI
- `hgk/src/api/client.ts` — Tauri IPC / Browser fetch 二重パス

### 不足しているもの

- Gateway ツール群 (PKS, Digestor, CCL 等) の HTTP API エンドポイント
- Gateway ツール群の Tool Definitions (Gemini Function Calling 形式)
- `/api/ask/agent` エンドポイント (ask_with_tools の HTTP 版)
- Chat UI のエージェントモード (ツール実行の可視化)
- Frontend からの個別 Gateway API 呼び出し

---

## Layer 1: serve.py API 拡張

### 1.1 Gateway ツールの直接 import

`hgk_gateway.py` は MCP デコレータ (`@mcp.tool()`) 付きだが、
関数本体は純粋な Python。MCP を経由せず、関数を直接呼べる。

**方針**: Gateway 関数を import し、FastAPI エンドポイントとして公開する。

```python
# serve.py に追加
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Gateway 関数の直接 import
from mekhane.mcp.hgk_gateway import (
    hgk_search,
    hgk_pks_search,
    hgk_pks_stats,
    hgk_pks_health,
    hgk_ccl_dispatch,
    hgk_ccl_execute,
    hgk_doxa_read,
    hgk_handoff_read,
    hgk_idea_capture,
    hgk_status,
    hgk_health,
    hgk_notifications,
    hgk_sessions,
    hgk_session_read,
    hgk_paper_search,
    hgk_digest_check,
    hgk_digest_list,
    hgk_digest_run,
    hgk_digest_topics,
    hgk_digest_mark,
    hgk_proactive_push,
    hgk_models,
    hgk_sop_generate,
    hgk_gateway_health,
)
```

### 1.2 エンドポイント設計

すべて `/api/hgk/*` 名前空間に配置。

| Endpoint | Method | Gateway 関数 | パラメータ |
|:---------|:-------|:-------------|:-----------|
| `/api/hgk/search` | POST | `hgk_search` | `{query, max_results?, mode?}` |
| `/api/hgk/pks/search` | POST | `hgk_pks_search` | `{query, k?, sources?}` |
| `/api/hgk/pks/stats` | GET | `hgk_pks_stats` | — |
| `/api/hgk/pks/health` | GET | `hgk_pks_health` | — |
| `/api/hgk/ccl/dispatch` | POST | `hgk_ccl_dispatch` | `{ccl}` |
| `/api/hgk/ccl/execute` | POST | `hgk_ccl_execute` | `{ccl, context?}` |
| `/api/hgk/doxa` | GET | `hgk_doxa_read` | — |
| `/api/hgk/handoff` | GET | `hgk_handoff_read` | `?count=1` |
| `/api/hgk/idea` | POST | `hgk_idea_capture` | `{idea, tags?}` |
| `/api/hgk/status` | GET | `hgk_status` | — |
| `/api/hgk/health` | GET | `hgk_health` | — |
| `/api/hgk/notifications` | GET | `hgk_notifications` | `?limit=10` |
| `/api/hgk/sessions` | GET | `hgk_sessions` | — |
| `/api/hgk/sessions/{cascade_id}` | GET | `hgk_session_read` | `?max_turns=10&full=false` |
| `/api/hgk/papers/search` | POST | `hgk_paper_search` | `{query, limit?}` |
| `/api/hgk/digest/check` | GET | `hgk_digest_check` | — |
| `/api/hgk/digest/list` | POST | `hgk_digest_list` | `{topics?, max_candidates?}` |
| `/api/hgk/digest/run` | POST | `hgk_digest_run` | `{topics?, max_papers?, dry_run?}` |
| `/api/hgk/digest/topics` | GET | `hgk_digest_topics` | — |
| `/api/hgk/digest/mark` | POST | `hgk_digest_mark` | `{filenames?}` |
| `/api/hgk/proactive` | POST | `hgk_proactive_push` | `{topics?, max_results?, use_advocacy?}` |
| `/api/hgk/models` | GET | `hgk_models` | — |
| `/api/hgk/sop` | POST | `hgk_sop_generate` | `{topic, decision?, hypothesis?}` |
| `/api/hgk/gateway/health` | GET | `hgk_gateway_health` | — |

### 1.3 実装パターン

Gateway 関数は全て `str` を返す (Markdown 形式)。
FastAPI ラッパーは JSON に変換して返す。

```python
@app.get("/api/hgk/status")
async def api_hgk_status():
    """HGK システムステータス"""
    try:
        result = hgk_status()
        return {"result": result}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/hgk/search")
async def api_hgk_search(request: Request):
    """知識ベース検索"""
    body = await request.json()
    try:
        result = hgk_search(
            query=body["query"],
            max_results=body.get("max_results", 5),
            mode=body.get("mode", "hybrid"),
        )
        return {"result": result}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
```

### 1.4 注意事項

- Gateway 関数は同期関数なので `asyncio.to_thread()` でラップすること
  (PKS検索などは重いため、イベントループをブロックしない)
- `_traced` デコレータは MCP コンテキスト外でも動くか要検証
  → 動かない場合、生の関数を取得する方法を検討
- port は **9698** を正式とする。serve.py の `__main__` と docstring を修正

---

## Layer 2: Frontend 統合

### 2.1 client.ts 拡張

`src/api/client.ts` に Gateway API 呼び出し関数を追加。

```typescript
// --- HGK Gateway API ---

export async function hgkStatus(): Promise<{result: string}> {
    return apiFetch('/api/hgk/status');
}

export async function hgkSearch(query: string, maxResults = 5, mode = 'hybrid'): Promise<{result: string}> {
    return apiFetch('/api/hgk/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, max_results: maxResults, mode }),
    });
}

export async function hgkPksSearch(query: string, k = 10, sources = ''): Promise<{result: string}> {
    return apiFetch('/api/hgk/pks/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, k, sources }),
    });
}

// ... 同パターンで全エンドポイント
```

### 2.2 既存 View の接続

- **Dashboard** (`dashboard.ts`): `hgkStatus()`, `hgkHealth()` でリアルデータ表示
- **Search** (`search.ts`): `hgkPksSearch()` で PKS 横断検索
- **Gnōsis** (`gnosis.ts`): `hgkSearch()` で論文検索
- **Digestor** (`digestor.ts`): `hgkDigestCheck/List/Run/Mark/Topics()`
- **PKS** (`pks.ts`): `hgkPksStats()`, `hgkPksHealth()`
- **Notifications** (`notifications.ts`): `hgkNotifications()`

---

## Layer 3: Agent Tool Use エンドポイント

### 3.1 HGK ツール定義の追加

`mekhane/ochema/tools.py` の `TOOL_DEFINITIONS` に Gateway ツールを追加。
**または** 新ファイル `mekhane/ochema/hgk_tools.py` を作成。

```python
HGK_TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "hgk_pks_search",
        "description": (
            "Search the full HGK knowledge base (38K+ docs). "
            "Searches Gnōsis (papers), Kairos (conversations), "
            "Sophia (KI), and Chronos (timeline) simultaneously."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language search query"},
                "k": {"type": "integer", "description": "Max results (default: 10)"},
                "sources": {"type": "string", "description": "Comma-separated sources filter (gnosis,kairos,sophia,chronos). Empty = all"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "hgk_ccl_execute",
        "description": (
            "Execute a CCL (Cognitive Control Language) expression. "
            "CCL is HGK's cognitive programming language. "
            "Examples: /noe+ (deep thinking), /dia+~*/noe (adversarial review)"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ccl": {"type": "string", "description": "CCL expression (e.g. /noe+, /dia+~*/noe)"},
                "context": {"type": "string", "description": "Execution context (analysis target, etc.)"},
            },
            "required": ["ccl"],
        },
    },
    {
        "name": "hgk_search",
        "description": (
            "Search the HGK knowledge base (KI / Gnōsis / Sophia). "
            "Supports hybrid (vector+keyword), vector-only, or keyword-only modes."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results (default: 5)"},
                "mode": {"type": "string", "description": "Search mode: hybrid, vector, keyword (default: hybrid)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "hgk_handoff_read",
        "description": "Read the latest session handoff(s). Shows what was done in previous sessions and what to do next.",
        "parameters": {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "Number of handoffs to read (default: 1)"},
            },
        },
    },
    {
        "name": "hgk_doxa_read",
        "description": "Read the Doxa (belief store). Shows accumulated laws, lessons, and beliefs from HGK sessions.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "hgk_idea_capture",
        "description": "Save an idea memo. Automatically loaded on next /boot.",
        "parameters": {
            "type": "object",
            "properties": {
                "idea": {"type": "string", "description": "Idea content (max 10,000 chars)"},
                "tags": {"type": "string", "description": "Comma-separated tags (e.g. FEP, design, experiment)"},
            },
            "required": ["idea"],
        },
    },
    {
        "name": "hgk_status",
        "description": "Get HGK system overview status. Shows health score, heartbeat, WBC alerts, git state.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "hgk_paper_search",
        "description": "Search academic papers via Semantic Scholar.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (e.g. 'active inference free energy')"},
                "limit": {"type": "integer", "description": "Max results (1-20, default: 5)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "hgk_digest_run",
        "description": "Run the Digestor pipeline. Default is dry_run (report only). Set dry_run=false to generate .md files.",
        "parameters": {
            "type": "object",
            "properties": {
                "topics": {"type": "string", "description": "Target topics (comma-separated). Empty = all topics."},
                "max_papers": {"type": "integer", "description": "Max papers to fetch (1-50, default: 20)"},
                "dry_run": {"type": "boolean", "description": "true=report only, false=generate files (default: true)"},
            },
        },
    },
    {
        "name": "hgk_proactive_push",
        "description": (
            "Autophōnos proactive knowledge push. Papers speak for themselves. "
            "Surfaces relevant knowledge based on context/topics."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topics": {"type": "string", "description": "Comma-separated topics. Empty = auto-extract from latest Handoff."},
                "max_results": {"type": "integer", "description": "Max results (default: 5)"},
                "use_advocacy": {"type": "boolean", "description": "First-person mode where papers narrate themselves (default: true)"},
            },
        },
    },
    {
        "name": "hgk_sop_generate",
        "description": "Generate a research request template (/sop). For Gemini Deep Research or Perplexity.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Research topic"},
                "decision": {"type": "string", "description": "What decision this research informs"},
                "hypothesis": {"type": "string", "description": "Prior hypothesis (if any)"},
            },
            "required": ["topic"],
        },
    },
]

# 既存の TOOL_DEFINITIONS と結合
ALL_TOOL_DEFINITIONS = TOOL_DEFINITIONS + HGK_TOOL_DEFINITIONS
```

### 3.2 HGK ツールの execute_tool 拡張

```python
# tools.py の execute_tool に追加 (または hgk_tools.py に新設)
def execute_hgk_tool(name: str, args: dict) -> dict:
    """Execute an HGK Gateway tool."""
    from mekhane.mcp.hgk_gateway import (
        hgk_search, hgk_pks_search, hgk_ccl_execute, hgk_ccl_dispatch,
        hgk_doxa_read, hgk_handoff_read, hgk_idea_capture, hgk_status,
        hgk_paper_search, hgk_digest_run, hgk_proactive_push, hgk_sop_generate,
    )

    hgk_dispatch = {
        "hgk_pks_search": lambda a: hgk_pks_search(a["query"], a.get("k", 10), a.get("sources", "")),
        "hgk_ccl_execute": lambda a: hgk_ccl_execute(a["ccl"], a.get("context", "")),
        "hgk_search": lambda a: hgk_search(a["query"], a.get("max_results", 5), a.get("mode", "hybrid")),
        "hgk_handoff_read": lambda a: hgk_handoff_read(a.get("count", 1)),
        "hgk_doxa_read": lambda a: hgk_doxa_read(),
        "hgk_idea_capture": lambda a: hgk_idea_capture(a["idea"], a.get("tags", "")),
        "hgk_status": lambda a: hgk_status(),
        "hgk_paper_search": lambda a: hgk_paper_search(a["query"], a.get("limit", 5)),
        "hgk_digest_run": lambda a: hgk_digest_run(a.get("topics", ""), a.get("max_papers", 20), a.get("dry_run", True)),
        "hgk_proactive_push": lambda a: hgk_proactive_push(a.get("topics", ""), a.get("max_results", 5), a.get("use_advocacy", True)),
        "hgk_sop_generate": lambda a: hgk_sop_generate(a["topic"], a.get("decision", ""), a.get("hypothesis", "")),
    }

    if name not in hgk_dispatch:
        return {"error": f"Unknown HGK tool: {name}"}

    try:
        result = hgk_dispatch[name](args)
        return {"output": result}
    except Exception as e:
        return {"error": str(e)}
```

### 3.3 `/api/ask/agent` エンドポイント

```python
@app.post("/api/ask/agent")
async def ask_agent(request: Request):
    """Agent mode — LLM with autonomous HGK tool access.

    Uses CortexClient.ask_with_tools() with HGK + file tools.
    Returns final response after all tool calls are resolved.
    """
    body = await request.json()
    message = body.get("message", "")
    model = body.get("model", "gemini-2.5-flash")
    system_instruction = body.get("system_instruction")
    thinking_budget = body.get("thinking_budget")
    max_iterations = body.get("max_iterations", 10)

    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    try:
        client = _get_client()

        # Merge file tools + HGK tools
        from mekhane.ochema.tools import TOOL_DEFINITIONS
        from mekhane.ochema.hgk_tools import HGK_TOOL_DEFINITIONS  # 新設ファイル
        all_tools = TOOL_DEFINITIONS + HGK_TOOL_DEFINITIONS

        result = await asyncio.to_thread(
            client.ask_with_tools,
            message=message,
            model=model,
            system_instruction=system_instruction or HGK_SYSTEM_TEMPLATES["hgk_citizen"],
            tools=all_tools,
            max_iterations=max_iterations,
            thinking_budget=thinking_budget,
        )
        return {
            "text": result.text,
            "model": result.model,
            "token_usage": result.token_usage,
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
```

### 3.4 `/api/ask/agent/stream` (SSE ストリーミング版)

エージェントループの各ステップを SSE で配信する。
各イベントの type:

- `thinking` — LLM の思考中
- `tool_call` — ツール呼び出し `{name, args}`
- `tool_result` — ツール実行結果 `{name, output}`
- `chunk` — 最終回答のテキストチャンク
- `done` — 完了

これにより Chat UI でツール実行をリアルタイム表示できる。

**実装方針**: `ask_with_tools()` をリファクタリングしてジェネレータ版を作るか、
コールバック版を作って SSE に橋渡しする。

---

## 実装順序

### Phase 1 (最優先 — 1日)

1. `serve.py` の port 修正 (9696 → 9698)
2. Gateway 関数の直接 import テスト (MCP デコレータの影響確認)
3. `/api/hgk/*` GET エンドポイント追加 (status, health, doxa, pks/stats)
4. 動作確認 (curl で叩いて確認)

### Phase 2 (2-3日)

1. 残りの POST エンドポイント追加
2. `client.ts` に全 Gateway API 関数追加
3. Dashboard / Search / PKS View をリアルデータ接続

### Phase 3 (3-5日)

1. `hgk_tools.py` 作成 (HGK_TOOL_DEFINITIONS + execute_hgk_tool)
2. `/api/ask/agent` エンドポイント実装
3. Chat View にエージェントモード切替 UI 追加

### Phase 4 (5-7日) — Agent + Streaming

1. `/api/ask/agent/stream` (SSE ストリーミング版)
2. Chat UI でツール実行可視化 (tool_call / tool_result の表示)
3. ファイル操作ツール (read_file, write_file) の統合テスト

### Phase 5 (7-10日) — 承認フロー + 安全ゲート (AMBITION F4 核心)

1. **安全ゲート (N-4 API 版)**: `write_file`, `run_command` 等の破壊的ツール呼び出し時に
    エージェントループを一時停止し、Creator に承認を求める仕組み。
    実装: `ask_with_tools` のループ内で HIGH_RISK_TOOLS 判定 → SSE で `approval_required`
    イベントを送信 → Frontend が承認/却下 UI を表示 → `/api/ask/agent/approve` で再開
2. **Diff レビュー View**: `write_file` の実行前に変更内容を diff 形式で表示。
    UI: GitHub PR 風の変更前/後表示 + ✅承認 / ❌却下ボタン。
    新 View `src/views/diff-review.ts` または Chat View 内のインライン diff パネル。
3. **結果表示パネル**: ターミナル出力の読取専用ログビュー (AMBITION L103, L109)
4. APP 自身のコード修正テスト (self-modification PoC) — 承認フロー経由

### Phase 6 (将来) — 拡張パス

1. **Push 型通知**: ✅ SSE による能動的語りかけ (F1 マザーブレイン)
    実装済: serve.py に `/api/push/stream` (SSE) エンドポイントを追加。
    Dashboard 接続時に `hgk_proactive_push` を自動実行し、結果を Push している。
2. **F6 複数 AI 組織**: ✅ **MVP 実装済み** (2026-02-23)
    `hgk/api/colony.py` — Colony オーケストレーター (535行)
    COO (Claude Opus 4.6 via LS, Gemini 3.1 Pro fallback) がタスクを分解し、
    Engineer (Gemini + HGK Tools), Researcher (Periskopē), Jules に委任。
    エンドポイント: `/api/ask/colony`, `/api/ask/colony/stream` (SSE)
    フロントエンド: `chat.ts` に 🏛️ Colony モードトグル追加。
3. **F2/F5/F7**: セッション=ノート、仮想Twitter、3DKB。
    Layer 1 の `/api/hgk/*` 名前空間は拡張可能な設計のため、
    これらの機能は新エンドポイント追加で対応可能。

---

## 検証基準

### Phase 1 完了条件

- `curl http://localhost:9698/api/hgk/status` が JSON を返す
- `curl http://localhost:9698/api/hgk/doxa` が Doxa 内容を返す

### Phase 3 完了条件

- Chat View から「HGK の現在のヘルススコアを教えて」と聞くと、
  LLM が `hgk_health` を自律的に呼び出し、結果を解釈して回答する

### Phase 5 完了条件 (= MVP 達成)

- Chat View から「dashboard.ts の行数を確認して」と聞くと、
  LLM が `read_file` を呼び出してファイルを読み、行数を回答する
- Chat View から「dashboard.ts に○○機能を追加して」と指示すると、
  LLM が `read_file` → 分析 → diff 表示 → **Creator が ✅承認** → `write_file` で適用
- 破壊的操作 (`write_file`) で承認なしに実行されないことを確認

---

## リスク・未解決事項

1. **~~`@_traced` デコレータ~~**: ✅ 実機検証済み。MCP 外でも正常動作。
   `.env` を `source` してから import すれば全関数が使える。

2. **`HGK_GATEWAY_TOKEN` (致命的)**: Gateway モジュールはモジュールレベルで
   `HGK_GATEWAY_TOKEN` を検証し、未設定なら `sys.exit(1)` する。
   **serve.py は起動前に `.env` をロードする必要がある**。
   対策: `serve.py` の先頭で `dotenv.load_dotenv()` を呼ぶか、
   uvicorn 起動スクリプトで `set -a && source .env && set +a` する。

3. **PKS Engine**: ✅ 実機検証済み。別プロセスから正常に検索可能 (8秒/3件)。
   LanceDB の読み取り並行性は問題なし。

4. **メモリ**: PKS Engine + CortexClient + Gateway 初期化で
   serve.py のメモリ消費が増加する。監視が必要。

5. **Claude Tool Use**: `ask_with_tools()` は Gemini Function Calling 前提。
   Claude の場合は `tools.py` の text-based パーサーを使う必要あり。
   → `chat_stream()` 経由で既に分岐している。統合テスト必要。

6. **Gateway の副作用**: OAuth state ファイルの読み込みが import 時に走る
   (「✅ Loaded OAuth state: 5 clients, 2 refresh tokens」)。
   serve.py からの利用では OAuth は不要なので、将来的に分離を検討。

---

## 実装状態 (2026-02-23 確認)

> この表は仕様ではなく、コードレベルで確認した事実の記録。

| Phase | 状態 | 確認根拠 |
|:------|:-----|:---------|
| **Phase 1** (Gateway import + GET) | ✅ 実装済み | `serve.py` に 28 エンドポイント。port 9698 |
| **Phase 2** (POST + client.ts) | ✅ 実装済み | `/api/hgk/*` 5 エンドポイント、`client.ts` 拡張済み |
| **Phase 3** (hgk_tools + /ask/agent) | ✅ 実装済み | `hgk_tools.py` 16KB 存在、`/api/ask/agent` L273 |
| **Phase 4** (Agent + SSE stream) | ✅ 実装済み | `/api/ask/agent/stream` L330、`chat.ts` Agent モード |
| **Phase 5** (承認フロー) | ✅ 実装済み | `/api/ask/agent/approve` L469、chat.ts Safety Gate |
| **Phase 6** (Push/F6/拡張) | ✅ 実装済み | `/api/push/stream` L494 + F6 Colony (`colony.py` 535行, `/api/ask/colony` + `/stream`) |
