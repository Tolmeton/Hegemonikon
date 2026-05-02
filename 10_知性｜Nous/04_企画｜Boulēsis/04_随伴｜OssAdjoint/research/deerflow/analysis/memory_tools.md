# DeerFlow Memory + Tools 行為可能性棚卸

> **対象**: `backend/src/agents/memory/` (4ファイル) + `backend/src/tools/` (7ファイル)
> **精読**: 合計 ~1500行 全行読了
> **日付**: 2026-03-11

---

## I. Memory 層 (4ファイル ~900行)

### 全体アーキテクチャ

```
MemoryMiddleware (after_agent)
  → _filter_messages_for_memory()  ← tool msg/upload block 除去
  → MemoryUpdateQueue.add()        ← debounced batch 収集
    → threading.Timer(delay)       ← デバウンス実行
    → MemoryUpdater.process_batch()
      → _load_memory()             ← mtime-based cache
      → _update_memory()           ← LLM 要約
      → _apply_updates()           ← structural merge
      → _save_memory()             ← atomic write (.tmp → rename)
```

### 1. queue.py — デバウンス記憶更新キュー (196行)

#### 構造
- `MemoryUpdateQueue`: thread_id → (messages, callback) をバッチ管理
- **同一 thread_id は最新で上書き**: `self._pending[thread_id] = entry` — 古い会話を持たない
- `threading.Timer(delay)`: 既存タイマーをキャンセル→再セット (デバウンス)
- `self._semaphore = Semaphore(max_concurrent)`: 同時実行数制御 (デフォルト 3)

#### 悪魔の細部
- **`DEFAULT_DELAY = 15`秒**: 15秒の沈黙後に初めて処理 → 連続入力は batch 化
- **`MAX_PENDING = 100`**: 溢れたら FIFO で最古を drop (OOM 防止)
- **`shutdown()`**: タイマー全キャンセル → 全 pending を即座に flush
- **`_process_entry()`**: semaphore で排他 → callback 実行 → pending から削除
- `thread_id` ベースなので、異なる thread は並列処理可能

#### HGK 随伴
Context Rot protocol の「自動セーブ」。現在の /rom は手動。**debounced auto-save** で N≥30 の中間セーブを自動化すべき。semaphore パターンは MCP 並列制御にも転用可能。

---

### 2. updater.py — LLM 駆動の記憶更新器 (385行)

#### memory.json スキーマ
```json
{
  "user": {
    "workContext": "仕事の文脈",
    "personalContext": "個人的文脈",
    "topOfMind": "最近の関心事"
  },
  "history": {
    "recentMonths": "直近数ヶ月",
    "earlierContext": "それ以前",
    "longTermBackground": "長期的背景"
  },
  "facts": [
    {"content": "事実文", "confidence": 0.85}
  ]
}
```

#### 処理フロー
1. **`_load_memory()`**: ファイル → JSON。**mtime-based cache**: `Path.stat().st_mtime` で変更検知、外部編集にも対応
2. **`_update_memory()`**: 会話テキストを MEMORY_UPDATE_PROMPT に投入 → LLM が JSON patch を返す
3. **`_apply_updates()`**: JSON patch を適用:
   - `user.*` / `history.*`: 文字列を直接上書き
   - `facts.remove[]`: content 完全一致で削除
   - `facts.add[]`: confidence 付きで追加。**confidence < 0.5 は破棄**
   - **max_facts (デフォルト 50)**: 超過分は confidence 降順でトリム
4. **`_save_memory()`**: `.tmp` に書出 → `os.replace()` で atomic swap

#### 悪魔の細部
- **`_strip_upload_mentions_from_memory()`**: 記憶内の upload ファイル参照を除去する3箇所を走査 (context, history, facts)。正規表現 `<uploaded_files>...</uploaded_files>` ブロック除去 + facts からファイルパス言及を削除。**セッション一時データの長期記憶汚染を防ぐ**
- **token counting**: `tiktoken` で `gpt-4o` エンコーダを使用。context + conversation が `max_context_tokens (128000)` を超えたら会話を切り詰め
- **max_facts**: 50 件上限。超過時に低 confidence から drop → 自然にノイズが減衰

#### HGK 随伴
- **Fact confidence scoring** → Mneme の KI に confidence メタデータ追加
- **mtime cache** → Memory middleware が SessionState を外部ファイルで永続化する際に使用可能
- **upload 汚染防止** → /bye Handoff 生成時にセッション一時データ (MCP 一時出力等) を自動除去
- **atomic write** → HGK の全 write_to_file は現在 Overwrite 直書き。atomic pattern を Code Protocol に追加

---

### 3. prompt.py — 記憶管理プロンプト (274行)

#### MEMORY_UPDATE_PROMPT
- **目的**: 会話ログ + 既存記憶 → JSON patch 生成
- **構造**: `<current_memory>` + `<conversation>` → `<output>` (JSON)
- **重要な指示**: "Do NOT record file upload events", "Do NOT include mention of uploaded files in ANY section"
  → **3層防御**: middleware filter (1層) → prompt 指示 (2層) → `_strip_upload_mentions_from_memory()` (3層)

#### FACT_EXTRACTION_PROMPT
- **目的**: 会話から構造化 fact を抽出
- **出力**: `[{"content": "...", "confidence": 0.0-1.0}]`
- **confidence ガイド**: 0.9-1.0 (直接言及) / 0.7-0.8 (強く示唆) / 0.5-0.6 (推測)

#### format_conversation_for_memory()
- HumanMessage → `User: {content}`
- AIMessage → `Assistant: {content}` (tool_calls ありなら skip)
- ToolMessage → skip
- **upload block も除去**: `<uploaded_files>...</uploaded_files>` を正規表現で strip

#### HGK 随伴
- **3層防御パターン** → HGK の安全不変条件に応用。N-4 (破壊的操作) でも middleware + prompt + post-process の多層防御を設計すべき
- **confidence-scored facts** → Gnōsis の論文メタデータに confidence を追加 (現在は citation count のみ)

---

### 4. `__init__.py` — エクスポート定義 (45行)

- `MemoryFormat`, `MEMORY_SECTION_DESCRIPTIONS`: 記憶セクションの宣言的定義
- `memory_update_queue`: モジュールレベルのシングルトン
- `MemoryUpdater`: ファクトリ的エクスポート
- `MEMORY_UPDATE_PROMPT`, `FACT_EXTRACTION_PROMPT`: プロンプトテンプレート

---

## II. Tools 層 (7ファイル ~600行)

### 全体アーキテクチャ

```
get_available_tools()           ← ツール合成層
  ├ config.tools → resolve_variable()  ← YAML 設定駆動
  ├ BUILTIN_TOOLS                       ← present_files, ask_clarification
  ├ SUBAGENT_TOOLS (条件付き)           ← task (subagent_enabled=True のみ)
  ├ view_image_tool (条件付き)          ← model.supports_vision=True のみ
  └ MCP tools (条件付き)               ← ExtensionsConfig.from_file() → cache
```

### 5. tools.py — ツール合成層 (85行)

#### 設計パターン
- **4層合成**: config駆動 + builtin + 条件付き subagent + 条件付き vision + MCP cache
- **MCP 動的リロード**: `ExtensionsConfig.from_file()` で**ディスクから最新を毎回読む**。Gateway API (別プロセス) での変更を即座に反映
- **vision 条件分岐**: モデルの `supports_vision` 属性で view_image_tool の include/exclude

#### HGK 随伴
HGK のツールは Antigravity IDE の静的リストとして提供されている。**動的ツール合成** — MCP サーバーの追加/削除を再起動なしで反映する仕組み。Motherbrain の health check と連動可能。

---

### 6. ask_clarification_tool — プレースホルダーツール (56行)

#### clarification_type (5種)
| type | 意味 | HGK 対応 |
|:-----|:-----|:---------|
| `missing_info` | 必要情報の欠如 | N-5 (能動的に探せ) のトリガー |
| `ambiguous_requirement` | 曖昧な要件 | N-1 (実体を読め) + N-6 (違和感検知) |
| `approach_choice` | 複数アプローチの選択 | N-3 θ3.3 (代替案提示) |
| `risk_confirmation` | リスク操作の確認 | **N-4 (不可逆前に確認)** — 最も直接的 |
| `suggestion` | 提案の承認要求 | N-7 (主観を述べ次を提案) |

#### 悪魔の細部
- `return_direct=True`: LLM にツール結果を直接返さない (middleware が処理)
- `parse_docstring=True`: docstring から引数説明を自動抽出
- ツール本体は `return "Clarification request processed by middleware"` — **プレースホルダー**。実ロジックは ClarificationMiddleware

#### HGK 随伴 ★★★ D1 最重要
- **N-4 の環境強制化**: `risk_confirmation` タイプを θ4.1 確認フォーマットと統合
- **N-6 の構造化**: 違和感を `ambiguous_requirement` として型付き表出
- **実装案**: `notify_user` ツールに clarification_type パラメータを追加し、Sekisho が type ごとの応答品質を監査

---

### 7. task_tool — サブエージェント委任 (196行)

#### 構造
1. `get_subagent_config(subagent_type)`: 2種 (`general-purpose`, `bash`)
2. Skills セクションを親から継承: `config.system_prompt + skills_prompt`
3. **再帰防止**: `get_available_tools(subagent_enabled=False)` — task ツール自体を除外
4. `executor.execute_async(prompt)`: バックグラウンド実行開始
5. **5秒ポーリング**: `while True: sleep(5)` + `get_background_task_result()`
6. **stream_writer**: `task_started`, `task_running`, `task_completed/failed/timed_out` イベント
7. **polling timeout**: `(config.timeout_seconds + 60) // 5` 回でタイムアウト

#### 悪魔の細部
- **ToolRuntime 活用**: `runtime.state` から sandbox, thread_data を取得。`runtime.context` から thread_id。`runtime.config.metadata` から model_name, trace_id
- **trace_id 伝播**: 親 → 子エージェントへ分散トレーシング ID を引き継ぎ
- **ai_messages 差分送信**: `last_message_count` でインクリメンタルに新規メッセージのみ送信
- **cleanup_background_task()**: 完了/失敗後に必ずクリーンアップ (メモリリーク防止)

#### HGK 随伴 ★★
- **Jules Pool の改善**: 現在の `jules_create_task` → `jules_get_status` のポーリングと同等だが、**stream_writer によるリアルタイム進捗**が欠如
- **再帰防止パターン**: HGK の ochema_ask_with_tools で「自分自身を呼ぶ」ループの防止に転用
- **trace_id 伝播**: Hermeneus → Ochēma → Jules の呼出チェーンにトレーシングを追加

---

### 8. present_file_tool — ファイル提示 (101行)

#### 設計パターン
- **仮想パス契約**: `/mnt/user-data/outputs/*` のみ受付。それ以外は ValueError
- **パス正規化**: virtual path → actual path → `relative_to(outputs_dir)` → 再構成
- **reducer 統合**: `Command(update={"artifacts": normalized_paths})` — `merge_artifacts` reducer で重複排除

#### HGK 随伴
アーティファクト管理。現在の `brain/<conversation-id>/` は IDE 側で管理。**仮想パス契約** で Agent と IDE の間にファイル交換プロトコルを定義する発想。

---

### 9. view_image_tool — 画像読取 (95行)

#### 設計パターン
- 4段バリデーション: absolute path → exists → is_file → valid extension
- MIME 検知: `mimetypes.guess_type()` + fallback dict
- **reducer 統合**: `Command(update={"viewed_images": {path: {base64, mime_type}}})` — `merge_viewed_images` reducer

#### HGK 随伴
`view_file` のバイナリ版で既に HGK に存在するが、**reducer ベースの状態管理** が HGK にはない。画像を「見た」事実を状態として保持し、後続の判断に使う仕組み。

---

### 10. setup_agent_tool — 動的エージェント生成 (63行)

#### 設計パターン
- **ファイルベース**: `SOUL.md` (人格) + `config.yaml` (メタデータ) を `agent_dir/` に書出
- **runtime.context.agent_name**: ToolRuntime から動的にエージェント名を取得
- **即時フィードバック**: `Command(update={"created_agent_name": name})`
- **失敗時クリーンアップ**: `shutil.rmtree(agent_dir)` — 中途半端な状態を残さない

#### HGK 随伴 ★
Týpos からの動的 Skill 生成。`typos_generate` → `.typos` ファイル → Skills ディレクトリに自動配置の自動化。失敗時 rollback パターンは Code Protocol に追加すべき。

---

## III. 欠陥の最終更新 (全層統合)

| # | 欠陥 | 深刻度 | 発見元 | 具体的実装パターン |
|:--|:-----|:-------|:-------|:-----------------|
| D1 | **Clarification 型付きツール** | ★★★ | tool + middleware | 5カテゴリ型 × wrap_tool_call → N-4/N-6 の環境強制 |
| D2 | **DanglingToolCall 回収** | ★★ | middleware | wrap_model_call で synthetic ToolMessage 注入 |
| D3 | **State 型付き reducer** | ★★ | tool + state | Command(update={}) + merge reducers |
| D4 | **Soul (personality)** | ★ | tool | SOUL.md ファイルベースの動的生成 |
| D5 | **Memory 自動注入** | ★★★ | memory | debounced queue + filter + LLM 要約 + atomic write |
| D6 | **Bootstrap モード** | ★★ | agent | setup_agent で Agent が Agent を作る |
| D7 | **Context-loss detection** | ★★★ | middleware | state ∩ ¬messages → reminder injection |
| D8 | **セッション内dir管理** | ★★ | middleware | workspace/uploads/outputs 3分離 + lazy_init |
| **D9** | **Fact confidence scoring** | ★★ | memory | confidence 0.0-1.0 + 閾値 drop + max_facts トリム |
| **D10** | **Upload 汚染3層防御** | ★★ | memory + prompt | middleware filter → prompt 指示 → post-process strip |
| **D11** | **動的ツール合成** | ★ | tools.py | config + MCP cache + vision条件 + subagent条件の4層 |
| **D12** | **trace_id 伝播** | ★ | task_tool | parent → child への分散トレーシング ID 引き継ぎ |

---

## IV. 最も価値の高い3パターン (実装優先度)

### 1. Debounced Memory Auto-Save (D5 + D9 + D10)
**何**: セッション中の会話を自動的にフィルタ→バッチ→LLM要約→永続化
**なぜ**: Context Rot の根本対策。手動 /rom に依存しない
**HGK 実装先**: Ochēma context_rot_distill の自動トリガー化

### 2. Clarification Type System (D1)
**何**: 不確実性の種類を5カテゴリに型付けし、実行中断を環境強制
**なぜ**: N-4/N-6 の「意志的遵守」→「環境強制」への転換
**HGK 実装先**: notify_user に clarification_type パラメータ追加 + Sekisho 監査連携

### 3. Context-Loss Detection (D7)
**何**: state に存在するが context window から消えた情報を自動検知・再注入
**なぜ**: Context Rot の「情報消失」をプログラム的に検出する唯一の方法
**HGK 実装先**: Ochēma の context_rot_status に「消失情報リスト」を追加

---

*Phase 0 — Memory + Tools 精読完了。lead_agent + middleware + memory + tools で全4レポート完成。*
