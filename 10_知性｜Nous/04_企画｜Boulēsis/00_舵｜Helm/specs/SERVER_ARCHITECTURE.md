# サーバーアーキテクチャ — 2サーバー体制

> 作成日: 2026-02-26
> 最終更新: 2026-02-26

---

## 概要

HGK システムは 2 つの独立した FastAPI サーバーで構成される。
それぞれ異なる責務とポートを持ち、同一ホストで並行稼働する。

---

## サーバー一覧

| サーバー | モジュール | ポート | 起動コマンド |
|:---------|:-----------|:-------|:------------|
| **Mekhane API** | `mekhane.api.server:app` | 9698 (デフォルト 9696) | `PYTHONPATH=. .venv/bin/uvicorn mekhane.api.server:app --port 9698` |
| **HGK Desktop API** | `hgk.api.serve:app` | 9699 | `PYTHONPATH=. .venv/bin/uvicorn hgk.api.serve:app --port 9699` |

---

## Mekhane API (`mekhane/api/server.py`) — ポート 9698

**目的**: Tauri v2 デスクトップアプリのバックエンド + MCP Gateway の REST 化

26 ルーターを遅延ロードで登録:

| カテゴリ | ルーター | 依存 |
|:---------|:---------|:-----|
| 基盤 | status, fep, postcheck, dendron, graph | なし |
| 検索 | gnosis, pks, symploke, sophia, link_graph | 埋め込みモデル |
| AI | cortex, chat, gnosis_narrator | CortexClient, httpx |
| 監視 | basanos, synteleia, sentinel, quota | SweepEngine 等 |
| 記録 | timeline, kalon, theorem, wal, epistemic | ファイル IO |
| 統合 | gateway, hgk, digestor, scheduler | MCP Gateway |
| 開発 | devtools, aristos | CortexClient |
| 研究 | periskope | Periskopē Engine |

**特徴**:

- UDS (Unix Domain Socket) モード対応 (`--uds /tmp/hgk.sock`)
- Embedder の事前ロード (warm cache)
- 各ルーターが import 失敗しても起動継続 (遅延ロード + warning)

---

## HGK Desktop API (`hgk/api/serve.py`) — ポート 9699

**目的**: アシスタントパネル (チャット UI) の直接バックエンド

| 機能 | エンドポイント | 説明 |
|:-----|:---------------|:-----|
| LLM 対話 | `/api/ask`, `/api/ask/stream` | Gemini/Claude プロキシ (SSE) |
| Agent | `/api/ask/agent`, `/api/ask/agent/stream` | ask_with_tools + Safety Gate |
| Colony | `/api/ask/colony`, `/api/ask/colony/stream` | F6 マルチ AI 組織 |
| Jules | `/api/jules/*` (7 エンドポイント) | Jules セッション管理 |
| Push | `/api/push/stream` | Autophōnos プロアクティブ通知 |
| Gateway | `/api/hgk/*` (24 エンドポイント) | HGK Gateway 関数の直接公開 |

**特徴**:

- CortexClient のシングルトン管理
- Safety Gate (Phase 5): 破壊的ツール実行の承認フロー
- `.env` の自動ロード (`HGK_GATEWAY_TOKEN` が必要)

---

## 使い分け

| 用途 | 使うサーバー | ポート |
|:-----|:-------------|:-------|
| チャット UI (ask/agent/colony) | **Desktop API** | 9699 |
| hgk-cli.sh (CLI ツール) | **Desktop API** | 9699 |
| Tauri アプリのフロントエンド | **Mekhane API** | 9698 |
| MCP Gateway 経由の操作 | **Mekhane API** | 9698 |
| n8n/自動化連携 | **Mekhane API** | 9698 |

---

## 変更履歴

| 日付 | 変更 |
|:-----|:-----|
| 2026-02-26 | 初版作成 — 2サーバー体制の明文化 |
