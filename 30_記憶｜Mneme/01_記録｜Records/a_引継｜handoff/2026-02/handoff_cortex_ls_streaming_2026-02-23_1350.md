# Handoff: Cortex LS Streaming & Safety Constraints

## セッション概要

- **日時**: 2026-02-23 13:50
- **目的**:
  - LS ConnectRPC (gRPC-web) を用いたストリーミング (`StartChatClientRequestStream` 等) により Claude の thinking データを取得できるか検証する
  - `SendUserCascadeMessage` の正しいリクエスト構造を特定・送信する
- **結論**:
  - `StartChatClientRequestStream` はパネル制御専用であり、チャットや thinking は流れない。
  - `SendUserCascadeMessage` を IDE の LS に直接送信するのは極めて危険 (CascadeManager ロックによる全セッション停止リスク)。
  - Cortex REST API 直叩き (`generateChat` + `tier_id`) により、LS 非依存で Claude を呼び出せる事実を確定し DX-010 に追記 (v9.0)。

## 成果物

| ファイル | 状態 | 内容 |
|:--------|:-----|:-----|
| `kernel/doxa/DX-010_ide_hack_cortex_direct_access.md` | ✅ v9.0 | 安全制約の追加 (SendUserCascadeMessage 危険性) と、LS 非依存 Claude アクセスの確定事実記録 |
| `experiments/four_step_flow.py` | ✅ 作成 | 4-Step フローの gRPC-web 実装 (CascadeConfig のフォーマット判明) |
| `experiments/stream_listen.py` | ✅ 作成 | raw socket を用いた gRPC-web チャンクダウンローダ (timeout 回避版) |

## 重要な教訓・安全制約

### 🔴 安全制約: SendUserCascadeMessage
>
> **絶対厳守**: IDE の LS に `SendUserCascadeMessage` を直接送ってはならない。

- **理由**: CascadeManager シングルトンの排他ロックを取得するため、メタデータ欠損等でエラーパスに入るとロックが解放されず、IDE 上の全ての Cascade 機能 (チャット等) が長時間停止・ハングする。
- 過去の `/noe+` 分析 (2026-02-13) の予測が完全に裏付けられた。

### 📡 ストリーミングの限界 (gRPC-web)

- `StartChatClientRequestStream`: 接続成功 (200 OK)。しかし流れてくるのは `initialAck` 等の初期化・制御イベントのみ。チャットのテキストや `thinking` データは観測されなかった。
- `StreamCascadePanelReactiveUpdates`: HTTP/1.1 (gRPC-web) では応答なし。HTTP/2 の bidirectional streaming が必須と推定される。

### 🧠 Thinking データ取得の現在地

- LS 非依存の REST API (`generateChat`) 経由での Claude ルーティング自体は成功 (`tier_id` 指定により解決)。
- ただし、REST レスポンス内に `thinkingSummaries` が含まれているかはまだ最終確定していない (M35モデル等での検証が必要)。

## 次のアクション

1. (継続調査) `CortexClient.chat_stream()` を使用して、REST API 経由で Claude の Thinking データが抽出可能か (SSE 形式 / JSON Array 形式) を詳細に検証する。
2. 必要に応じて ochema MCP サーバーの `/ask_chat` 処理を改修し、Thinking データの出力に対応させる。
