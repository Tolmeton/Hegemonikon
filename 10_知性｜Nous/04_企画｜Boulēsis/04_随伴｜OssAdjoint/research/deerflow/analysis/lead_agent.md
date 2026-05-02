# DeerFlow lead_agent 行為可能性棚卸

> **対象**: `backend/src/agents/lead_agent/` (agent.py + prompt.py + thread_state.py)
> **精読**: 合計 ~800行 全行読了
> **日付**: 2026-03-11

---

## 1. アーキテクチャの実体

```
make_lead_agent(config: RunnableConfig)
    ↓
    モデル解決: requested → agent_config → default (3段フォールバック)
    ↓
    _build_middlewares(): 条件付き middleware chain 構築
    ↓
    create_agent(model, tools, middleware, system_prompt, state_schema)
    ↓
    LangGraph StateGraph (内部生成 — DeerFlow は直接触らない)
```

**核心**: DeerFlow は `langchain.agents.create_agent()` を呼ぶだけ。
StateGraph の構築は LangChain 内部に委譲している。
→ HGK が随伴すべきは **LangChain の create_agent** ではなく、**DeerFlow がその上に載せた4層**:

| 層 | 内容 | HGK 随伴 |
|:---|:-----|:---------|
| **State 拡張** | ThreadState (7 追加フィールド) | CCL context の型定義 |
| **Middleware chain** | 条件付き 10+1 middleware | Hermēneus / Dokimasia |
| **Prompt 構造** | XML タグ 9セクション | .typos / WF 定義 |
| **Agent 構成** | bootstrap + default 2パス | /boot + 通常セッション |

---

## 2. ThreadState — 状態空間の設計

```python
class ThreadState(AgentState):
    sandbox: SandboxState | None         # sandbox_id
    thread_data: ThreadDataState | None  # workspace/uploads/outputs パス
    title: str | None                    # 自動生成タイトル
    artifacts: list[str]                 # 成果物パス (重複排除 reducer)
    todos: list | None                   # TodoList
    uploaded_files: list[dict] | None    # アップロードファイル
    viewed_images: dict[str, ViewedImageData]  # 画像キャッシュ (clear 可能)
```

### 行為可能性

| # | 発見 | HGK への吸収 |
|:--|:-----|:------------|
| A1 | **Annotated 型 + reducer パターン** — `merge_artifacts`, `merge_viewed_images` で状態マージを宣言的に定義 | CCL context に reducer 概念を導入。現在 context は flat str → 型付き dict + reducer に進化可能 |
| A2 | **viewed_images の clear 機構** — `new == {}` で全クリア。middleware が処理後に画像を消す | HGK の context にも「処理済みマーク」を付ける機構が欲しい |
| A3 | **SandboxState の分離** — sandbox 情報を state の一部として持つ | Jules タスクの sandbox_id を CCL context に保持する設計 |
| A4 | **ThreadDataState の3パス構造** — workspace / uploads / outputs を明示分離 | HGK API に統一的なパス管理層を追加 |

---

## 3. Middleware Chain — 宣言的パイプライン

### 構築ロジック (`_build_middlewares`)

```
[常時] ThreadData → Uploads → Sandbox → DanglingToolCall
[条件] Summarization (config.enabled)
[条件] TodoList (is_plan_mode)
[常時] Title
[常時] Memory
[条件] ViewImage (model.supports_vision)
[条件] SubagentLimit (subagent_enabled)
[常時] Clarification (常に最後)
```

### 行為可能性

| # | 発見 | HGK への吸収 |
|:--|:-----|:------------|
| B1 | **条件付き middleware** — 4つが config/mode に応じて on/off | Hermēneus に深度 (L0-L3) に応じた middleware on/off を実装 |
| B2 | **順序の厳密な理由** — コメントに「なぜこの順序か」が明記 (L199-207) | WF 実行パイプラインに順序制約とその理由を文書化する規約 |
| B3 | **DanglingToolCall** — ユーザー中断時の orphan tool call を回収 | HGK にはない概念。Context Rot 時の未完了操作の回収に応用 |
| B4 | **Clarification は常に最後** — 全処理後に「曖昧さ検出」 | N-6 (違和感検知) を middleware として WF 実行後に自動挿入 |
| B5 | **Summarization の trigger/keep 設計** — いつ要約するか / 何を残すかを config で制御 | Context Rot protocol に `trigger` (発動条件) と `keep` (保持条件) を追加 |
| B6 | **SubagentLimit の silently discard** — 超過分を黙って捨てる | Jules Pool に同等の安全弁を実装 (現在は30上限だがエラーで返す) |

---

## 4. Prompt 構造 — XML タグ 9セクション

```xml
<role>           → エージェントの自己認識
<soul>           → SOUL.md (personality) の動的注入
<memory>         → 永続記憶 facts の system prompt 注入
<thinking_style> → 思考プロセスの制約
<clarification_system> → 曖昧さ検出と質問生成 (5カテゴリ)
<skill_system>   → Skills の progressive loading 指示
<subagent_system> → Sub-agent delegation ルール
<working_directory> → ファイルパスの仮想化
<response_style> → 出力スタイル制約
<citations>      → 引用形式
<critical_reminders> → 忘却防止リマインダー
```

### 行為可能性

| # | 発見 | HGK への吸収 |
|:--|:-----|:------------|
| C1 | **Soul (SOUL.md)** — agent personality を外部ファイルで定義し動的注入 | HGK の `.agents/rules/` が同等機能を持つが、**per-agent personality** の概念がない。Custom Agent ごとに BC のサブセットを選択する設計 |
| C2 | **Clarification 5カテゴリ** — missing_info / ambiguous_requirement / approach_choice / risk_confirmation / suggestion | N-1, N-3, N-4, N-6 に対応するが、**ツール化** (ask_clarification) されている点が異なる。HGK でも Clarification を MCP tool 化する価値あり |
| C3 | **Memory の system prompt 注入** — `<memory>` タグとして最大 N tokens を注入 | HGK は Handoff を手動で読むが、**自動注入** は /boot でのみ。全セッションで memory を自動注入する設計 |
| C4 | **Progressive Loading** — Skills を最初は名前だけ渡し、必要時に read_file で読む | HGK の Skills と同じ設計。ただし DeerFlow は container path を使い、sandbox 内のパスに変換する点が実装的に洗練 |
| C5 | **Subagent batch 制御** — N (=max_concurrent) を prompt に埋め込み、LLM に「数えさせる」 | Jules Pool のタスク分割に同等のガイダンスを CCL マクロのプロンプトに注入 |
| C6 | **Bootstrap モード** — 最小プロンプトで Custom Agent を作成するモード | HGK に /agent-create 的な WF を追加。Agent 自身が Agent を作る自己参照 |

---

## 5. 判断の集積 (悪魔の細部)

| 行 | 判断 | なぜそうしたか (推定) | HGK への示唆 |
|:---|:-----|:---------------------|:------------|
| L30-39 | 3段フォールバック (request → agent → default) | ユーザー指定 > agent 設定 > グローバルデフォルト。安全側に倒す | Ochēma のモデル選択にも同パターンを |
| L46-47 | Summarization.enabled = config | 全セッションで要約するのではなく opt-in | Context Rot は opt-out (常時) にすべき |
| L199 | ThreadData **must be before** Sandbox | sandbox_id の生成に thread_id が必要 | 依存関係を明示的にコメントする規約 |
| L241 | ViewImage は **vision 対応モデルのみ** | 非対応モデルに画像を渡しても無駄 | Ochēma のモデル capabilities に合わせた middleware 選択 |
| L250 | Clarification は **always last** | 全処理後に残った曖昧さだけを質問 | 早すぎる質問は情報不足。処理後の質問がより精密 |
| L268 | is_bootstrap frag | Custom Agent 作成時は最小プロンプト | /boot の Focus Mode と同じ設計動機 |
| L313-323 | bootstrap → setup_agent ツール追加 | Agent が Agent を定義するための特殊ツール | 自己参照的な Agent 構成 |

---

## 6. HGK 体系の不完全性として露呈した欠陥

| # | DeerFlow にあって HGK にないもの | 深刻度 |
|:--|:-------------------------------|:-------|
| D1 | **Clarification ツール** — 曖昧さを構造的に検出しツールとして質問する | ★★★ (N-6 の機械化) |
| D2 | **DanglingToolCall 回収** — 中断時の未完了操作の安全な処理 | ★★ |
| D3 | **State の型付き reducer** — 状態マージの宣言的定義 | ★★ |
| D4 | **Soul (per-agent personality)** — Agent ごとの性格定義 | ★ (Custom Agent で必要) |
| D5 | **Memory の自動注入** — 全セッションで永続記憶を system prompt に注入 | ★★★ (/boot 以外でも常時) |
| D6 | **Bootstrap モード** — Agent が Agent を作る自己参照機構 | ★★ |

---

*Phase 0 — lead_agent 精読完了。次: middlewares/ の10ファイル精読 (Phase 0 の本丸)*
