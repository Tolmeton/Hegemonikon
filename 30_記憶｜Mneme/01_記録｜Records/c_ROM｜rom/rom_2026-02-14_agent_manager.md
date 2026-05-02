---
rom_id: rom_2026-02-14_agent_manager
session_id: 1f6dce94-ce82-4344-bba5-83666fbe29c3
created_at: 2026-02-14 17:04
rom_type: snapshot
---
# Agent Manager 実装 (HGK Desktop)

Gemini 3 Pro Preview で Agent Manager コンポーネントを新規実装。2カラムレイアウト (サイドバー + メインパネル)、セッション管理 (シングルトン)、CCL ワークフローのデモデータ3件。@vet で /dia+ 敵対的レビュー実施し、AbortController によるイベント管理修正を適用。@nous で「独自価値 = CCL可視化 + 実用価値の両立」を発見。

## 決定事項

- [DECISION] Agent Manager は hgk/src/views/agent-manager.ts に配置 (470行)
- [DECISION] AgentManager クラスはシングルトン + subscribe/unsubscribe パターン
- [DECISION] CSS は既存変数体系 (am- prefix) で styles.css に追記 (380行)
- [DECISION] ルーター統合: main.ts に 'agents' ルート追加、index.html に🤖ナビボタン
- [DECISION] イベント管理は AbortController + MutationObserver (/dia+ で修正)
- [DECISION] アーキテクチャは実データ駆動で判断 (YAGNI — @nous 振動結果)

## @nous 発見

- [DISCOVERY] 独自価値 = CCL 実行プロセスの可視化 (ログ内 /pro, /kho 表示)
- [DISCOVERY] 実用価値 (アーティファクト Open 等) との両立が必須
- [DISCOVERY] Gemini への委任自体は良いが、レビューの深度を上げるべき

## 次回アクション

- P0: Tauri IPC 接続 (Hermēneus 実行結果を Agent Manager に流す)
- P1: CCL AST インライン表示 + アーティファクト Open
- P2: アーキテクチャ設計レビュー (実データ後)
- PUSH: セッション終了時に git push (14 commits ahead)
