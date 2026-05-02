# DeerFlow 随伴 (鹿流随伴) — VISION

> DeerFlow 2.0 (ByteDance) を HGK に随伴吸収する。
> 「設計パターンだけ」ではなく、実装の技術ごと食べる。
> 悪魔は細部に宿る。具体(実装)と抽象(設計)は相補的。

```typos
#prompt deerflow-adjoint-vision
#syntax: v8
#depth: L2

<:role: DeerFlow 2.0 → HGK 随伴吸収プロジェクト
  LangGraph ベースの super agent harness を HGK の座標系で再構成する。
  「フォーク」ではなく「消化」— 原形を留めないまで分解し、HGK の血肉にする。:>

<:goal: DeerFlow の実行インフラを HGK の認知制御と統合し、
  「正しく考える」(HGK) × 「正しく動く」(DeerFlow) の随伴対を完成させる :>

<:constraints:
  - 実装を読め — 設計パターンだけ抽出するな。コードの判断の集積が価値
  - 随伴不能は欠陥 — HGK が再現できない機能は HGK 体系の不完全性の証明
  - LangGraph 依存を HGK ネイティブに — 外部依存ではなく CCL/Hermēneus で再構成
  - 「しない」を「できない」にするな — SFBT 5項目を常に走査
:>

<:context:
  - [knowledge] upstream: https://github.com/bytedance/deer-flow
  - [knowledge] local clone: C:\Users\makar\Sync\oikos\deer-flow
  - [knowledge] DeerFlow = Deep Exploration and Efficient Research Flow
  - [knowledge] v2.0 は v1 とコード共有なしの完全再構築。MIT ライセンス

  - [knowledge] アーキテクチャ (4サービス):
    LangGraph Server (port 2024) — エージェントランタイム
    Gateway API (port 8001) — REST API
    Frontend (port 3000) — Next.js Web UI
    Nginx (port 2026) — 統合リバースプロキシ

  - [knowledge] 随伴対の構造:
    F: DeerFlow → HGK (持ち上げ = 実装パターンを HGK に再構成)
    G: HGK → DeerFlow (忘却 = HGK 固有性を落とすと DeerFlow の何に対応するか)
    η: Id → G∘F = 取り込んだ結果、元の DeerFlow とどれだけ一致するか
    ε: F∘G → Id = HGK の固有性を落として DeerFlow に写像し、再び持ち上げた結果
:>
```

---

## 6領域の随伴マップ

### Phase 0 — Middleware Chain `★★★`

| 項目 | 値 |
|:-----|:---|
| DeerFlow ソース | `src/agents/middlewares/` (10 middleware) |
| HGK 吸収先 | Hermēneus execution pipeline / Mekhane |
| 随伴の方向 | DeerFlow の宣言的 middleware → HGK の WF 実行に middleware 層を追加 |

**DeerFlow の 10 middleware** (厳密な実行順序):
```
ThreadData → Uploads → Sandbox → DanglingToolCall →
Summarization → TodoList → Title → Memory →
ViewImage → SubagentLimit → Clarification
```

**HGK への随伴**:
| DeerFlow Middleware | HGK 対応 | 状態 |
|:--------------------|:---------|:-----|
| ThreadData | CCL context | 既存 |
| Uploads | (なし) | **新規** |
| Sandbox | Synergeia sandbox | 拡張 |
| DanglingToolCall | (なし) | **新規** — ユーザー中断時の tool call 回収 |
| Summarization | Context Rot protocol | 拡張 — 自動要約をパイプラインに組込 |
| TodoList | /ccl-plan の todo | 拡張 |
| Title | (なし) | 軽微 |
| Memory | Mneme | 拡張 — 自動 fact extraction |
| ViewImage | (なし) | **新規** |
| SubagentLimit | Jules Pool | 既存 (より高性能) |
| Clarification | (なし) | **新規** — 不明点の自動検出と質問生成 |

---

### Phase 1 — Memory 自動抽出 `★★★`

| 項目 | 値 |
|:-----|:---|
| DeerFlow ソース | `src/agents/memory/` |
| HGK 吸収先 | Mnēmē (30_記憶) |
| 随伴の方向 | fact 自動抽出 + confidence scoring → Handoff/KI の自動生成 |

**DeerFlow の Memory** (精読済: ~900行):
- 3層構造: user (workContext/personalContext/topOfMind) + history (recent/earlier/longTerm) + facts[]
- Fact confidence 0.0-1.0。**threshold 0.5 以下は破棄**。max_facts = **50** (超過時 confidence 降順でトリム)
- Debounce **15秒** → threading.Timer + Semaphore(3) → atomic file I/O (.tmp → os.replace)
- mtime-based cache: 外部編集も検知
- **3層 upload 汚染防御**: middleware filter → prompt "Do NOT record" → `_strip_upload_mentions_from_memory()`

**HGK への再構成**:
- DeerFlow の flat facts → HGK の構造化 KI (Sophia) + confidence メタデータ
- confidence threshold → N-10 SOURCE/TAINT ラベルと連動
- Debounce → Context Rot protocol のチェックポイントと統合
- 3層防御 → N-4 安全不変条件にも応用 (middleware + prompt + post-process)

---

### Phase 2 — Sandbox + Subagents `★★★`

| 項目 | 値 |
|:-----|:---|
| DeerFlow ソース | `src/sandbox/` (~1050行) + `src/subagents/` (~660行) |
| HGK 吸収先 | Synergeia / Jules Pool / Ochēma |
| 随伴の方向 | 仮想パスシステム + 2段プール実行器 → Jules タスクの隔離実行環境 |

**Sandbox** (精読済):
- 3層: ABC (Sandbox/SandboxProvider) → 実装 (LocalSandbox/LocalSandboxProvider) → ツール (5つの LangChain Tool)
- **仮想パス双方向変換**: `_resolve_path` (仮想→実) / `_reverse_resolve_path` (実→仮想) / `_reverse_resolve_paths_in_output` (出力一括変換)
- longest prefix first ソート: `/mnt/user-data/uploads` > `/mnt/user-data`
- 5ツール: bash / ls (max_depth=2, 30+ ignore patterns) / read_file (100KB警告) / write_file / str_replace (一意性検証)
- 構造化例外: SandboxError → 5サブクラス (exit_code 保持など)
- shell 検出: zsh → bash → sh → PATH 上の sh (フォールバック付き)

**Subagents** (精読済):
- **2段 ThreadPool**: scheduler_pool (3) + execution_pool (3)
- `execute_async()` → scheduler → execution → `asyncio.run(_aexecute())` の4層チェーン
- **タイムアウト**: `execution_future.result(timeout=config.timeout_seconds)` → TIMED_OUT
- **AIMessage 逐次収集**: `astream()` で message_id ベース重複排除しながら蓄積
- **trace_id 伝播**: 親→子にトレースID伝搬
- **ツールフィルタ**: allowlist + denylist (デフォルト: `task` 除外=再帰防止)
- **モデル継承**: `model: "inherit"` → 親のモデルを使用 (thinking=False)
- 2つの組込み: `bash` (sandbox tools, 30 turns) / `general-purpose` (全ツール, 50 turns)

**HGK への再構成**:
- 仮想パス変換 → Jules sandbox の入出力パス隔離
- 2段プール → Jules Pool のタイムアウト管理改善
- AIMessage 収集 → Ochēma の中間出力構造化返却
- ツールフィルタ → Jules task の権限制御

---

### Phase 3 — IM チャネル `★★★`

| 項目 | 値 |
|:-----|:---|
| DeerFlow ソース | `src/channels/` (10ファイル ~2030行) |
| HGK 吸収先 | Organon (新モジュール) |
| 随伴の方向 | Telegram bot → HGK への入力チャネル。Desktop App を待たずに HGK と会話 |

**DeerFlow の Channels** (精読済):
- 3層構造: Foundation (base/store/types) → Orchestration (MessageBus/ChannelManager/Service) → Platform (Telegram/Slack/Feishu)
- **MessageBus**: async Queue (inbound) + callback list (outbound) の Pub/Sub ハブ
- **ChannelManager**: 3層セッション解決 (default→channel→user)、LangGraph Server 呼出、アーティファクト配信
- **ChannelStore**: `{channel}:{topic_id}` → `thread_id` の JSON 永続化 (atomic write)
- **コマンドシステム**: /new, /status, /models, /memory, /help の5コマンド
- **同時処理制限**: asyncio.Semaphore(5)

**HGK への再構成**:
- MessageBus → Motherbrain / Mekhane のイベント駆動層
- ChannelManager → Ochēma MCP を LangGraph Server の代替として使用
- ChannelStore → Mnēmē のセッション永続化と統合
- コマンド → CCL 式をコマンドとして解釈 (IM 上で /noe や /bou をトリガー)
- **完全随伴可能**: LangGraph 固有依存なし

---

### Phase 4 — Embedded Client `★★`

| 項目 | 値 |
|:-----|:---|
| DeerFlow ソース | `src/client.py` (877行) |
| HGK 吸収先 | HGK API (mekhane/api/) |
| 随伴の方向 | HTTP API と Python 直接呼出しの dual interface パターン |

**DeerFlowClient** (精読済):
- **遅延エージェント再生成**: config-key (model/thinking/plan/subagent) が変わらない限りキャッシュ
- **SSE 互換ストリーミング**: values / messages-tuple / end イベント
- **管理 API**: models, skills, memory, MCP config, uploads, artifacts の完全 CRUD
- **セキュリティ**: パストラバーサル防止 (`relative_to` + `resolve()`)、アトミック JSON 書込、ZIP スキル安全インストール (symlink除去/100MB制限)
- **`chat()`**: stream ラッパー (最後の AI text のみ)
- **ファイル変換**: PDF/PPT/Excel/Word → Markdown 自動変換

**HGK への再構成**:
- dual interface (HTTP + Python) → HGK API で同型パターンを採用
- config-key 遅延再生成 → Ochēma の session 管理に応用
- アトミック書込 → Mnēmē の JSON 永続化に横展開

---

### Phase 5 — Gateway 検証パターン `★`

| 項目 | 値 |
|:-----|:---|
| DeerFlow ソース | `src/tests/` |
| HGK 吸収先 | Peira |
| 随伴の方向 | Pydantic モデルで HTTP / embedded の同型性を CI 検証 |

---

## 特定された HGK 欠陥 (D1-D15)

| # | 欠陥 | 深刻度 | 発見元 | HGK 実装先 |
|:--|:-----|:-------|:-------|:----------|
| D1 | **Clarification 型付きツール** | ★★★ | tool + middleware | notify_user + Sekisho |
| D2 | **DanglingToolCall 回収** | ★★ | middleware | Ochēma MCP 回収 |
| D3 | **State 型付き reducer** | ★★ | tool + state | Hermēneus state |
| D4 | **Soul (personality)** | ★ | tool | Týpos SOUL 生成 |
| D5 | **Memory 自動注入** | ★★★ | memory | Ochēma context_rot_distill 自動化 |
| D6 | **Bootstrap モード** | ★★ | agent | Týpos + Skills 自動生成 |
| D7 | **Context-loss detection** | ★★★ | middleware | Ochēma context_rot_status 拡張 |
| D8 | **セッション内dir管理** | ★★ | middleware | brain/ ディレクトリ体系化 |
| D9 | **Fact confidence scoring** | ★★ | memory | Mneme KI + Gnōsis メタデータ |
| D10 | **Upload 汚染3層防御** | ★★ | memory + prompt | N-4 安全不変条件 |
| D11 | **動的ツール合成** | ★ | tools.py | Motherbrain health + MCP 連携 |
| D12 | **trace_id 伝播** | ★ | task_tool | Hermēneus → Ochēma → Jules チェーン |
| D13 | **IM ↔ Agent ブリッジ** | ★★★ | ChannelManager | Organon — Telegram/Slack で HGK と対話 |
| D14 | **async Pub/Sub バス** | ★★ | MessageBus | Motherbrain — イベント駆動アーキテクチャ |
| D15 | **セッション永続化 (topic→thread)** | ★★ | ChannelStore | Mnēmē — IM 会話とセッションの紐付け |
| D16 | **仮想パス双方向変換** | ★★ | LocalSandbox | Jules — LLM に一貫した仮想パス空間を提示 |
| D17 | **2段プール実行** | ★★★ | SubagentExecutor | Jules Pool — scheduler+executor 分離でタイムアウト管理 |
| D18 | **AIMessage 逐次収集** | ★★ | SubagentExecutor | Ochēma — subagent の中間出力を構造化で返却 |
| D19 | **Embedded Client (dual interface)** | ★★ | DeerFlowClient | HGK API — HTTP と直接呼出の同型インターフェース |
| D20 | **スキル安全インストール** | ★ | DeerFlowClient | Skill Governance — ZIP 検証 + symlink 除去 |

---

## Phase 優先度

| Phase | 領域 | 難易度 | 価値 | 依存 |
|:------|:-----|:-------|:-----|:-----|
| 0 | Middleware Chain | ★★★ | 最高 | なし |
| 1 | Memory 自動抽出 | ★★☆ | 高 | なし |
| 2 | Sandbox 仮想パス | ★★☆ | 中 | なし |
| 3 | IM チャネル | ★★☆ | 高 | Phase 0 |
| 4 | Embedded Client | ★☆☆ | 中 | Phase 0 |
| 5 | Gateway 検証 | ★☆☆ | 低 | Phase 4 |

**推奨**: Phase 0 → 1 → 3 → 2 → 4 → 5

---

## 精読ロードマップ

### 完了 ✅
1. ✅ `backend/src/agents/lead_agent/agent.py` (333行) → [analysis/lead_agent.md](analysis/lead_agent.md)
2. ✅ `backend/src/agents/lead_agent/thread_state.py` (56行)
3. ✅ `backend/src/agents/lead_agent/prompt.py` (410行)
4. ✅ `backend/src/agents/middlewares/*.py` (10本 ~1110行) → [analysis/middlewares.md](analysis/middlewares.md)
5. ✅ `backend/src/agents/memory/` (4ファイル ~900行) → [analysis/memory_tools.md](analysis/memory_tools.md)
6. ✅ `backend/src/tools/` (7ファイル ~600行) → [analysis/memory_tools.md](analysis/memory_tools.md)

7. ✅ `backend/src/channels/` (10ファイル ~2030行) → [analysis/channels.md](analysis/channels.md)

8. ✅ `backend/src/sandbox/` (~1050行) → [analysis/sandbox_subagents.md](analysis/sandbox_subagents.md)
9. ✅ `backend/src/client.py` (877行) → [analysis/sandbox_subagents.md](analysis/sandbox_subagents.md)
10. ✅ `backend/src/subagents/` (~660行) → [analysis/sandbox_subagents.md](analysis/sandbox_subagents.md)

### 残存未踏
11. `backend/src/config/` — 設定スキーマ (ツール合成の config 駆動部分)
12. `frontend/` — Next.js Web UI (Phase 3 IM 連携時)

---

*Created: 2026-03-11*
*Updated: 2026-03-11 (Phase 0+1+2+3+4 精読完了, D1-D20 特定)*
*Upstream: https://github.com/bytedance/deer-flow*
