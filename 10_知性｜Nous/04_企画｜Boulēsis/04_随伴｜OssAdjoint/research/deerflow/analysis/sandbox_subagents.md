# DeerFlow 精読レポート: sandbox/ + subagents/ + client.py

> 精読対象: ~2600行 (sandbox/ ~1050行, subagents/ ~660行, client.py 877行)
> 精読日: 2026-03-11

---

## 1. Sandbox (`src/sandbox/`)

### 1.1 アーキテクチャ (3層)

```
ABC 層:     sandbox.py (Sandbox) + sandbox_provider.py (SandboxProvider)
例外層:     exceptions.py (5階層の構造化例外)
ツール層:   tools.py (5つの LangChain Tool)
実装層:     local/ (LocalSandbox + LocalSandboxProvider + list_dir)
```

### 1.2 核心メカニズム

#### 仮想パス双方向変換 (LocalSandbox)

```python
# 正変換: 仮想パス → 実パス (LLM のコマンド → OS 実行)
_resolve_path("/mnt/skills/tool.py")  →  "/home/user/.deer-flow/skills/tool.py"

# 逆変換: 実パス → 仮想パス (OS 出力 → LLM への表示)
_reverse_resolve_path("/home/user/.deer-flow/skills/tool.py")  →  "/mnt/skills/tool.py"

# 出力内一括変換: コマンド出力全体のパスを逆変換
_reverse_resolve_paths_in_output(stdout)  →  仮想パスに置換された出力
```

- **longest prefix first** ソート: `/mnt/user-data/uploads` が `/mnt/user-data` より先にマッチ
- コマンド内パス変換: regex で `_resolve_paths_in_command()` を適用後に `subprocess.run`
- **LLM には常に仮想パス空間しか見えない** ← セキュリティ + 移植性

#### SandboxProvider (シングルトン管理)

- `resolve_class(config_string)` で設定駆動のクラス解決 (e.g., `"src.sandbox.local.LocalSandboxProvider"`)
- `acquire()` → シングルトン生成、`get()` → 取得、`release()` → noop (LocalSandbox は破棄しない)
- `_setup_path_mappings()`: config から skills の container_path → local_path を取得

#### 5ツール (tools.py)

| ツール | 機能 | 特記 |
|:-------|:-----|:-----|
| `bash_tool` | コマンド実行 | `ensure_sandbox_initialized()` + パス変換 |
| `ls_tool` | ディレクトリ列挙 | max_depth=2, IGNORE_PATTERNS (30+パターン) |
| `read_file_tool` | ファイル読込 | バイナリ判定、巨大ファイル警告 (100KB) |
| `write_file_tool` | ファイル書込 | append モード対応 |
| `str_replace_tool` | 部分置換 | 一意性検証 + diff 表示 |

- 共通パターン: `replace_virtual_path()` で仮想→実パス変換、`ensure_sandbox_initialized()` で lazy init
- `is_local_sandbox()`: Docker vs Local の判定で出力形式を切替え

#### 構造化例外 (exceptions.py)

```
SandboxError (基底)
├── SandboxNotFoundError
├── SandboxRuntimeError
├── CommandExecutionError (exit_code 保持)
└── FileOperationError
    ├── FileNotFoundError
    └── FilePermissionError
```

---

## 2. Subagents (`src/subagents/`)

### 2.1 アーキテクチャ

```
定義層:   config.py (SubagentConfig dataclass)
実行層:   executor.py (SubagentExecutor — 2段プール + ストリーミング)
登録層:   registry.py (BUILTIN_SUBAGENTS dict + config.yaml override)
組込み:   builtins/ (bash + general-purpose)
```

### 2.2 SubagentExecutor (492行 — 核心)

#### 2段 ThreadPool

```
scheduler_pool (3 workers)   →  タイムアウト付きで execution_pool を監視
execution_pool (3 workers)   →  実際のエージェント実行 (asyncio.run)
```

- **タイムアウトメカニズム**: `execution_future.result(timeout=config.timeout_seconds)` → `FuturesTimeoutError` → `cancel()`
- **3層呼出チェーン**: `execute_async()` → `_scheduler.submit(run_task)` → `_execution.submit(execute)` → `asyncio.run(_aexecute)`

#### AIMessage ストリーミング収集

```python
async for chunk in agent.astream(state, stream_mode="values"):
    # message_id ベースの重複排除
    if not is_duplicate:
        result.ai_messages.append(message_dict)
```

- 全 AIMessage を `ai_messages: list[dict]` に蓄積 → 親エージェントに構造化データで返却
- **content の型安全**: `str | list[block]` の両方に対応

#### 状態管理 (グローバル dict + lock)

```python
_background_tasks: dict[str, SubagentResult] = {}
_background_tasks_lock = threading.Lock()
```

- `cleanup_background_task()`: terminal state のみ削除 (race condition 防止)
- SubagentStatus: PENDING → RUNNING → COMPLETED / FAILED / TIMED_OUT

#### ツールフィルタリング

```python
_filter_tools(all_tools, allowed=["bash", "ls"], disallowed=["task", "ask_clarification"])
```

- `disallowed_tools` デフォルト: `["task"]` — **再帰的 subagent 呼出を防止**

#### モデル継承

- `model: "inherit"` → 親エージェントのモデルを使用
- subagent は `thinking_enabled=False` で生成

### 2.3 組込みサブエージェント

| 名前 | ツール | max_turns | 用途 |
|:-----|:-------|:----------|:-----|
| `bash` | sandbox のみ (5ツール) | 30 | コマンド実行の隔離 |
| `general-purpose` | 全ツール継承 | 50 | 汎用タスク委譲 |

共通:
- `disallowed_tools: ["task", "ask_clarification", "present_files"]` — 再帰防止 + 自律完了 (質問不可)
- system_prompt に `<working_directory>` で仮想パスを注入
- `<output_format>` で構造化出力を要求

---

## 3. DeerFlowClient (`src/client.py`, 877行)

### 3.1 設計意図

**LangGraph Server 不要の組み込みクライアント**。HTTP API と同一のインターフェースを Python 直接呼出で提供。

### 3.2 核心パターン

#### エージェント遅延再生成

```python
def _ensure_agent(self, config):
    key = (model_name, thinking_enabled, plan_mode, subagent_enabled)
    if self._agent is not None and self._agent_config_key == key:
        return  # キャッシュヒット
    self._agent = create_agent(...)  # 再生成
```

- config-key が変わらない限りエージェントを再利用
- `reset_agent()` で強制再生成

#### ストリーミング (SSE 互換)

```
values           — state snapshot (title, messages, artifacts)
messages-tuple   — per-message (AI / tool)
end              — 完了
```

- `seen_ids: set[str]` で重複排除
- `chat()` は `stream()` のラッパー (最後の AI text のみ返却)

#### セキュリティ

- **パストラバーサル防止**: `file_path.relative_to(uploads_dir.resolve())` → `PermissionError`
- **アトミック書込**: `tempfile.NamedTemporaryFile` → `Path.replace()`
- **スキル安全インストール**: ZIP 展開 → symlink 除去 → 100MB 制限 → パス走査 → frontmatter 検証

#### 管理 API (Gateway 同型)

| API | 機能 |
|:----|:-----|
| `list_models()` / `get_model()` | モデル一覧/詳細 |
| `list_skills()` / `get_skill()` / `update_skill()` / `install_skill()` | スキル CRUD |
| `get_memory()` / `get_memory_config()` / `reload_memory()` | メモリ管理 |
| `get_mcp_config()` / `update_mcp_config()` | MCP 設定 |
| `upload_files()` / `list_uploads()` / `delete_upload()` | ファイル操作 |
| `get_artifact()` | 成果物取得 |

---

## 4. HGK への随伴分析

### 新規発見 (D16-D20)

| # | 欠陥 | 深刻度 | 発見元 | HGK 実装先 |
|:--|:-----|:-------|:-------|:------------|
| D16 | **仮想パス双方向変換** | ★★ | LocalSandbox | Jules sandbox — LLM に一貫した仮想パス空間を提示 |
| D17 | **2段プール実行** | ★★★ | SubagentExecutor | Jules Pool — scheduler+executor 分離でタイムアウト管理 |
| D18 | **AIMessage 逐次収集** | ★★ | SubagentExecutor | Ochēma — subagent の中間出力を構造化データで返却 |
| D19 | **Embedded Client (dual interface)** | ★★ | DeerFlowClient | HGK API — HTTP と直接呼出の同型インターフェース |
| D20 | **スキル安全インストール** | ★ | DeerFlowClient | Skill Governance — ZIP 検証 + symlink 除去 |

### 随伴可能性の総括

| 領域 | 随伴可能性 | 根拠 |
|:-----|:----------|:-----|
| 仮想パス変換 | ◎ 完全 | regex + dict mapping。LangGraph 依存なし |
| 2段プール | ◎ 完全 | 標準 threading/concurrent.futures のみ |
| AIMessage 収集 | ○ 部分 | LangChain AIMessage 固有。HGK は独自メッセージ型 |
| Embedded Client | ◎ 完全 | パターンのみ。LangGraph 系は HGK MCP に置換 |
| スキルインストール | ○ 部分 | ZIP + frontmatter は Skill Governance が既に類似機能を持つ |

---

*精読完了: 2026-03-11*
