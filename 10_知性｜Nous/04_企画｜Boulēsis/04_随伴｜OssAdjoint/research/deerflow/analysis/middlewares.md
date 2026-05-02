# DeerFlow Middleware 10本 行為可能性棚卸

> **対象**: `backend/src/agents/middlewares/` (9ファイル) + `backend/src/sandbox/middleware.py`
> **精読**: 合計 ~1110行 全行読了
> **日付**: 2026-03-11

---

## 0. Middleware API の hook point 体系

LangChain の `AgentMiddleware` は **5 つの hook point** を提供:

| hook | タイミング | 引数 | 用途 |
|:-----|:----------|:-----|:-----|
| `before_agent` | Agent 起動前 | state, runtime | 環境セットアップ (dir作成, sandbox取得) |
| `before_model` | LLM 呼出前 | state, runtime | コンテキスト注入 (Todo reminder, 画像) |
| `after_model` | LLM 応答後 | state, runtime | 応答加工 (subagent truncate, title生成) |
| `after_agent` | Agent 完了後 | state, runtime | 後処理 (memory queue) |
| `wrap_model_call` | LLM 呼出ラッパー | request, handler | メッセージ修正 (dangling tool call) |
| `wrap_tool_call` | Tool 呼出ラッパー | request, handler | Tool 傍受 (clarification) |

→ **HGK の Dokimasia (修飾層) と同型**。ただし DeerFlow は 5 hook × 具体実装で、HGK は 60 パラメータの宣言的定義。

---

## 1. 全10本の設計パターン分析

### ① ThreadData [before_agent] — 91行
**何をする**: thread_id からワーキングディレクトリを3つ (workspace/uploads/outputs) 生成
**悪魔の細部**: `lazy_init=True` — パス計算だけ先にやり、実ディレクトリは on-demand
**HGK 随伴**: セッション固有のワーキングディレクトリ管理。現在 HGK は `/tmp` + `artifacts/` だが体系化されていない

### ② Uploads [before_agent] — 205行
**何をする**: メッセージの `additional_kwargs.files` から新規/歴史ファイルを分離し `<uploaded_files>` ブロックを HumanMessage に prepend
**悪魔の細部**:
- `Path(filename).name != filename` でパストラバーサル防止
- `uploads_dir / filename).is_file()` で存在確認 (削除済みファイルの参照防止)
- content が `list` の場合 (multimodal) にも対応
**HGK 随伴**: ファイルアップロードの構造化注入。HGK は `view_file` で直接読むが、**前セッションのファイル参照**の仕組みがない

### ③ DanglingToolCall [wrap_model_call] — 111行
**何をする**: ユーザー中断で orphan になった tool_call に synthetic ToolMessage (status="error") を注入
**悪魔の細部**:
- `wrap_model_call` を使う理由: `before_model` + `add_messages` reducer は末尾に追加してしまう → AIMessage の直後に挿入できない
- `request.override(messages=patched)` でリクエスト自体を差し替え
**HGK 随伴**: Context Rot 時の「未完了 MCP 呼出」の安全な回収。現在 HGK にはこの概念がない — **★★★ D2 確認**

### ④ Clarification [wrap_tool_call] — 174行
**何をする**: `ask_clarification` ツール呼出を傍受し、`Command(goto=END)` で実行を中断。ToolMessage にフォーマット済み質問を返す
**悪魔の細部**:
- 5カテゴリ × アイコン: ❓ missing_info / 🤔 ambiguous_requirement / 🔀 approach_choice / ⚠️ risk_confirmation / 💡 suggestion
- `_is_chinese()`: 中国語ユーザーの言語検出 (中国語で回答するため)
- `goto=END` は LangGraph の `__end__` ノード — グラフ実行を即座に停止
**HGK 随伴**: **★★★ D1 確認** — N-6 (違和感検知) の環境強制化。`notify_user` ツールの clarification 特化版

### ⑤ Memory [after_agent] — 150行
**何をする**: Agent 完了後に会話を filter → debounced queue に投入 → 非同期で LLM 要約
**悪魔の細部**:
- `_filter_messages_for_memory()` が最も重要 — tool messages、tool_calls 付き AI messages、upload blocks を除去
- upload-only ターン (ファイルだけ送った) は paired AI response ごと drop
- `skip_next_ai` フラグで human-AI ペアを一括スキップ
- **debouncing**: `queue.add()` は即座には処理せず、複数ターンを batch
**HGK 随伴**: **★★★ D5 確認** — /boot 以外での記憶自動注入。特に filter ロジックは Context Rot protocol に直接応用可能

### ⑥ SubagentLimit [after_model] — 76行
**何をする**: LLM が生成した `task` ツール呼出が上限 (2-4) を超えたら excess を silently truncate
**悪魔の細部**:
- `_clamp_subagent_limit()`: [2, 4] にクランプ。設定値が範囲外でも安全
- `model_copy(update=...)`: Pydantic v2 の shallow copy で AIMessage を差し替え
- `task` ツール名のみフィルタ — 他のツールは制限しない
**HGK 随伴**: Jules Pool に同等の安全弁。現在 jules_batch_execute は max_concurrent=30 だが、**LLM 側の出力を制限する**発想がない

### ⑦ Title [aafter_model] — 94行
**何をする**: 初回 human-AI 交換後に lightweight model でスレッドタイトルを自動生成
**悪魔の細部**:
- `thinking_enabled=False` で軽量モデルを使用 (推論トークン節約)
- `user_msg[:500]` + `assistant_msg[:500]`: 入力を切り詰めてコスト削減
- フォールバック: LLM 失敗時は `user_msg[:50] + "..."` で代替
**HGK 随伴**: Motherbrain のセッション管理に自動タイトル生成を追加

### ⑧ Todo [before_model, extends TodoListMiddleware] — 101行
**何をする**: SummarizationMiddleware でコンテキストが切り詰められた場合、Todo リストの write_todos 呼出がコンテキスト外に消えることを検知し、`<system_reminder>` を注入
**悪魔の細部**:
- `_todos_in_messages()`: write_todos の tool call がまだ visible かチェック
- `_reminder_in_messages()`: 二重注入防止
- **Context-loss detection**: state にはあるが messages にない = 要約で消えた
- `HumanMessage(name="todo_reminder")`: named メッセージで識別可能に
**HGK 随伴**: **★★★ Context Rot の構造的解決** — state と messages の乖離を検知する仕組み。HGK の Context Rot protocol に「state に存在するが context から消えた情報」の自動回復を追加すべき

### ⑨ ViewImage [before_model] — 222行
**何をする**: view_image ツール完了後、画像の base64 データを HumanMessage として注入し LLM が「見れる」ようにする
**悪魔の細部**:
- `_all_tools_completed()`: 全 tool call の完了を確認してから注入 (途中注入防止)
- `_should_inject_image_message()`: 二重注入防止チェック (文字列マッチ)
- multimodal content: `{"type": "image_url", "image_url": {"url": "data:...;base64,..."}}`
**HGK 随伴**: Ochēma の vision 対応強化。現在 HGK は `generate_image` で出力するが、**既存画像の LLM への注入**は未実装

### ⑩ Sandbox [before_agent] — 61行
**何をする**: Docker sandbox を thread ごとに1つ acquire し、state に sandbox_id を保存
**悪魔の細部**:
- ThreadData と同じ `lazy_init` パターン
- sandbox は release しない — thread の全寿命で再利用、shutdown で一括解放
- ThreadData が先に走る必要がある (依存関係)
**HGK 随伴**: Jules タスクの sandbox 管理。現在 Jules は Google 側で sandbox を管理するため直接の随伴対象ではないが、自前 sandbox を持つなら参考

---

## 2. Hook Point × Middleware マトリクス

```
                before_agent  before_model  after_model  after_agent  wrap_model_call  wrap_tool_call
ThreadData      ●
Uploads         ●
Sandbox         ●
DanglingToolCall                                                      ●
Todo                          ●
ViewImage                     ●
SubagentLimit                               ●
Title                                       ●
Memory                                                   ●
Clarification                                                                          ●
```

→ **5 hook point のうち 5 つすべてが使用されている**。DeerFlow は middleware API を完全活用。

---

## 3. 実行順序と依存関係

```
[before_agent 層]
  1. ThreadData  ← thread_id → paths
  2. Uploads     ← paths + messages → uploaded_files
  3. Sandbox     ← thread_id → sandbox_id (ThreadData に依存)

[wrap_model_call 層]
  4. DanglingToolCall ← messages → patched messages (独立)

[Summarization は LangChain 内蔵]

[before_model 層]
  5. Todo        ← state.todos + messages → reminder injection
  6. ViewImage   ← state.viewed_images → image injection

[LLM 呼出]

[after_model 層]
  7. SubagentLimit ← tool_calls → truncated tool_calls
  8. Title       ← messages → title (初回のみ)

[wrap_tool_call 層]
  9. Clarification ← tool_call → Command(goto=END)

[after_agent 層]
  10. Memory     ← filtered messages → queue
```

**設計原則**: 外側 (before_agent/after_agent) = 環境管理、内側 (before_model/after_model) = コンテキスト操作、wrap = 傍受

---

## 4. HGK 欠陥の更新 (lead_agent + middleware 統合)

| # | 欠陥 | 深刻度 | middleware の教え |
|:--|:-----|:-------|:----------------|
| D1 | **Clarification ツール化** | ★★★ | `wrap_tool_call` + `Command(goto=END)` で物理的に実行中断。N-6 の環境強制 |
| D2 | **DanglingToolCall 回収** | ★★ | `wrap_model_call` で位置正確な synthetic message 挿入。before_model では不十分 |
| D3 | **State 型付き reducer** | ★★ | `merge_artifacts`, `merge_viewed_images` の宣言的状態マージ |
| D4 | **Soul (personality)** | ★ | per-agent の性格定義 |
| D5 | **Memory 自動注入** | ★★★ | `after_agent` + debounced queue + **filter ロジック** (tool msg 除去, upload block 除去) |
| D6 | **Bootstrap モード** | ★★ | Agent が Agent を作る自己参照 |
| **D7** | **Context-loss detection** | ★★★ | **新規発見**: Todo middleware の「state にあるが messages にない = 消えた」検知。Context Rot の構造的解決策 |
| **D8** | **セッション内ディレクトリ管理** | ★★ | **新規発見**: workspace/uploads/outputs の3分離 + lazy_init |

---

*Phase 0 — lead_agent + middleware 精読完了。次: `memory/` + `tools/` (Phase 0 残り)*
