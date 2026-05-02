# DeerFlow Channels 精読レポート

> 📖 参照: `backend/src/channels/` 全10ファイル (~2030行)

---

## 1. アーキテクチャ概観

channels/ は **3層構造** で IM → Agent → IM のフルループを構成する:

```
┌─────────────────────────────────────────────────────┐
│  Layer 3: Platform Adapters                         │
│  ┌──────────┐ ┌─────────┐ ┌──────────┐             │
│  │ Telegram │ │  Slack  │ │  Feishu  │             │
│  │ 283行    │ │ 245行   │ │  379行   │             │
│  └────┬─────┘ └────┬────┘ └────┬─────┘             │
│       │            │           │                    │
│  Layer 2: Orchestration                             │
│  ┌────┴────────────┴───────────┴─────┐              │
│  │         MessageBus (Pub/Sub)      │ ← 237行     │
│  └───────────┬───────────────────────┘              │
│              │                                      │
│  ┌───────────┴───────────────────────┐              │
│  │      ChannelManager (Dispatch)    │ ← 339行     │
│  └───────────┬───────────────────────┘              │
│              │                                      │
│  ┌───────────┴───────────┐                          │
│  │   ChannelService      │ ← ライフサイクル管理     │
│  │   (start/stop)        │   127行                  │
│  └───────────────────────┘                          │
│                                                     │
│  Layer 1: Foundation                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ base.py  │ │ store.py │ │ types.py │            │
│  │ 抽象基底 │ │ JSON永続 │ │ メッセージ│            │
│  │  130行   │ │   91行   │ │   62行   │            │
│  └──────────┘ └──────────┘ └──────────┘            │
└─────────────────────────────────────────────────────┘
```

---

## 2. Layer 1 — 基盤

### types.py (62行)

- `InboundMessage`: channel → agent 方向。`topic_id` で IM スレッド → DeerFlow thread のマッピング
- `OutboundMessage`: agent → channel 方向。`is_final` フラグで完了 reaction 制御
- `ResolvedAttachment`: file path + size + mime_type + is_image。セキュリティ検証済みの添付ファイル
- `InboundMessageType`: CHAT / COMMAND の enum

### base.py (130行)

- `Channel` ABC: `start()`, `stop()`, `send()`, `send_file()` の抽象メソッド
- **共通実装**:
  - `_make_inbound()`: InboundMessage 生成のファクトリ関数
  - `_on_outbound()`: outbound callback の共通ルーティング (自分宛てメッセージだけ処理)

### store.py (91行)

- `ChannelStore`: `{channel}:{topic_id}` → `thread_id` の JSON 永続化
- **atomic write**: `.tmp` → `os.replace` (V-013 対策と同型)
- `threading.Lock` でスレッドセーフ
- `_load()` は起動時に1回 JSON 読み込み → インメモリ dict で運用

---

## 3. Layer 2 — オーケストレーション

### MessageBus (237行)

**非同期 Pub/Sub ハブ**。チャネルとディスパッチャーを疎結合にする。

```python
# インバウンド: キュー
self._inbound_queue: asyncio.Queue[InboundMessage]

# アウトバウンド: コールバック
self._outbound_callbacks: list[Callable[[OutboundMessage], Awaitable[None]]]
```

- `publish_inbound()`: キューに投入 (async)
- `subscribe_outbound()` / `unsubscribe_outbound()`: コールバック登録/解除
- `_publish_outbound()`: 全コールバックに fire-and-forget (`asyncio.create_task`)
- `start()` / `stop()`: ワーカータスクのライフサイクル管理

### ChannelManager (339行)

**核心のディスパッチャー**。InboundMessage を消費し、LangGraph Server へ中継する。

#### 3層セッション解決

```python
async def _resolve_session_config(channel: str, user_id: str) -> dict:
    # 優先度: user-specific > channel-specific > default
    # merge して返す
```

各レベルで以下を設定可能:
- `model`: LLM モデル名
- `assistant_id`: LangGraph assistant
- `context`: 追加コンテキスト文字列

#### コマンドハンドラ (5コマンド)

| コマンド | 処理 |
|:---------|:-----|
| `/new` | スレッド強制リセット (`ChannelStore.delete_mapping`) |
| `/status` | Gateway API `/api/status` へ HTTP |
| `/models` | Gateway API `/api/models` へ HTTP |
| `/memory` | Gateway API `/api/memory?thread_id=...` へ HTTP |
| `/help` | 静的ヘルプテキスト |

#### Agent 呼出フロー

```
InboundMessage
    ↓
_resolve_session_config()  ← 3層merge
    ↓
ChannelStore.get_thread_id()  ← topic_id → thread_id 解決
    ↓                            なければ threads.create()
LangGraph Client
    runs.wait(thread_id, input, config)
    ↓
_extract_response()  ← messages[-1] のテキスト抽出
    ↓
_extract_artifacts()  ← present_files tool call からパス解決
    ↓                    セキュリティ: outputs/ 外を拒否 + path traversal 防止
OutboundMessage(text, attachments)
    ↓
MessageBus.publish_outbound()
```

**同時処理制限**: `asyncio.Semaphore(max_concurrency=5)`

#### アーティファクト配信セキュリティ

```python
# 仮想パス → 実パス解決
real_path = thread_dir / "outputs" / virtual_path.name
# パストラバーサル防止
if not real_path.is_relative_to(outputs_dir):
    continue  # 無視
```

### ChannelService (127行)

- 設定ファイルから enabled channels を動的ロード
- `CHANNEL_MAP`: `{"telegram": TelegramChannel, "slack": SlackChannel, "feishu": FeishuChannel}`
- start/stop のライフサイクル管理

---

## 4. Layer 3 — プラットフォーム実装

### 3プラットフォーム共通パターン

| パターン | 実装 |
|:---------|:-----|
| **SDK スレッド分離** | 専用 `threading.Thread` + `asyncio.new_event_loop()` で SDK の polling を隔離 |
| **クロスループ通信** | `asyncio.run_coroutine_threadsafe(coro, main_loop)` でメインへ非同期投入 |
| **即時応答** | 「Working on it...」をメッセージ受信直後に返す (UX 改善) |
| **指数バックオフ** | `send()` で max 3回リトライ、delay = 2^attempt 秒 |
| **ユーザー ACL** | `allowed_users` リストによるホワイトリスト (空 = 全許可) |
| **ファイルサイズ制限** | プラットフォーム API の制限に合わせたバリデーション |
| **emoji reaction** | 処理状態を視覚的に表示 (受信/処理中/完了/失敗) |

### Telegram (283行)

- **接続方式**: Long-polling (`python-telegram-bot`)
- **topic_id 戦略**: reply chain → `reply_to_message.message_id` を topic_id として使用。新規メッセージ = 新 topic
- **ファイル制限**: 画像 10MB / ドキュメント 50MB
- **スレッド表現**: `reply_to_message_id` で返信チェイン
- **SDK 回避策**: `run_polling()` は `add_signal_handler()` を呼ぶためメインスレッドでしか使えない → 手動で `initialize()` + `start()` + `start_polling()` を分離

### Slack (245行)

- **接続方式**: Socket Mode (`slack-sdk`, WebSocket、公開 IP 不要)
- **topic_id 戦略**: `thread_ts` を直接使用 (スレッド内 = 共通 thread_ts、非スレッド = 自身の ts)
- **Markdown 変換**: `markdown_to_mrkdwn` で標準 Markdown → Slack mrkdwn フォーマット
- **UX 追加**: `reactions_add("eyes")` で受信確認、`"white_check_mark"` / `"x"` で成功/失敗
- **SDK 統合**: `SocketModeClient` の `socket_mode_request_listeners` にコールバック登録
- **コマンド認識**: `/` プレフィックスで InboundMessageType.COMMAND に分類

### Feishu (379行)

- **接続方式**: WebSocket (`lark-oapi` SDK)
- **topic_id 戦略**: `root_id` (Feishu の返信チェイン root) を使用。root_id なし = msg_id = 新 topic
- **メッセージ形式**: Interactive Card (JSON) + Markdown 埋め込み
- **ファイル送信**: 2段階 — upload (image_key/file_key 取得) → send (created message に埋め込み)
- **ファイル型分類**: 拡張子で xls/ppt/pdf/doc/stream に分岐
- **ファイル制限**: 画像 10MB / その他 30MB
- **SDK 回避策**: `lark_oapi.ws.client.loop` がモジュールレベルで event loop をキャッシュ → 専用スレッドの新ループで上書き (`_ws_client_mod.loop = loop`)
- **エラーハンドリング**: `_log_future_error()` で `run_coroutine_threadsafe` の future に done callback を付与 → 非同期エラーを確実に捕捉

---

## 5. HGK への随伴分析

### 高価値パターン (HGK に吸収すべき)

| # | パターン | DeerFlow 実装 | HGK 吸収先 | 随伴の方向 |
|:--|:---------|:-------------|:-----------|:-----------|
| P1 | **MessageBus (Pub/Sub)** | async Queue + callback | Motherbrain / Mekhane | 入出力の非同期疎結合。MCP とは別の軽量メッセージング |
| P2 | **3層セッション解決** | default→channel→user | Ochēma / Motherbrain | account の概念拡張。入力元に応じたコンテキスト注入 |
| P3 | **topic_id スレッド永続化** | ChannelStore JSON | Mnēmē / Kairos | 1会話 = 1 thread の概念。Handoff と連動可能 |
| P4 | **即時応答パターン** | 「Working on it...」 | Ochēma chat / Telegram bot | LLM 応答前のラテンシ改善。ユーザー体験の核心 |
| P5 | **コマンドシステム** | /new, /status 等 5つ | CCL 簡易インターフェース | IM 上で CCL/WF をトリガー |
| P6 | **アーティファクト配信** | present_files → attach | Organon 出力 | ファイルの IM 配信パイプライン |

### 新規欠陥

| # | 欠陥 | 深刻度 | 発見元 | HGK 実装先 |
|:--|:-----|:-------|:-------|:-----------|
| D13 | **IM ↔ Agent ブリッジ** | ★★★ | ChannelManager | Organon — Telegram/Slack/Discord で HGK と対話 |
| D14 | **async Pub/Sub バス** | ★★ | MessageBus | Motherbrain / Mekhane — イベント駆動アーキテクチャ |
| D15 | **セッション永続化 (topic→thread)** | ★★ | ChannelStore | Mnēmē — IM 会話とセッションの紐付け |

### 随伴不能の検証

| DeerFlow 機能 | HGK で再現可能か | 判定 |
|:-------------|:----------------|:-----|
| LangGraph Server 呼出 | **代替可能**: Ochēma MCP が同等の機能を提供 | ✅ 随伴可能 |
| MessageBus (async pub/sub) | **追加可能**: Python asyncio で実装。Motherbrain に統合 | ✅ 随伴可能 |
| ChannelStore (JSON 永続化) | **追加可能**: Mnēmē の JSON ストアと統合 | ✅ 随伴可能 |
| Telegram/Slack/Feishu アダプタ | **追加可能**: SDK は同じものを使える | ✅ 随伴可能 |
| 3層セッション解決 | **拡張可能**: Ochēma の account 概念を拡張 | ✅ 随伴可能 |
| コマンドシステム | **追加可能**: CCL 式をコマンドとして解釈 | ✅ 随伴可能 |
| アーティファクト配信 | **追加可能**: brain/ ディレクトリのファイルを IM に転送 | ✅ 随伴可能 |

**結論**: channels/ レイヤーは **完全に随伴可能**。LangGraph 固有の依存はない。

---

## 6. 実装品質の観察

### 良い実装

1. **SDK スレッド分離**: 各 SDK が独自の event loop を必要とする問題を正しく解決。特に Feishu の `_ws_client_mod.loop = loop` はエレガントなモンキーパッチ
2. **atomic write**: store.py の `.tmp` → `os.replace` パターンは一貫して使用
3. **run_coroutine_threadsafe + done callback**: Feishu の `_log_future_error()` は非同期エラーを確実に捕捉
4. **markdown_to_mrkdwn**: Slack のマークダウン変換を外部ライブラリで適切に処理
5. **graceful shutdown**: 各チャネルの `stop()` が SDK の shutdown sequence を正しく実行

### 懸念点

1. **ChannelManager の Gateway API 依存**: `/status` `/models` `/memory` コマンドは Gateway API に HTTP 問合せ。Gateway がダウンすると全コマンドが失敗
2. **store.py の単一ファイル**: 大量の topic 蓄積でパフォーマンス劣化のリスク。LRU や TTL がない
3. **`_last_bot_message` の非永続化**: Telegram の reply chain は再起動で消失
4. **max_concurrency=5 のハードコード**: 設定可能にすべき

---

*精読: 2026-03-11 | ファイル数 10 | 合計行数 ~2030*
