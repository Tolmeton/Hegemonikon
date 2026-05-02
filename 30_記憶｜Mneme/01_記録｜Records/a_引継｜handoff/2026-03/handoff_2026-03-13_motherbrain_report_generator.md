# Handoff — Motherbrain Report Generator 実装

**日時**: 2026-03-13 16:43 JST
**Agent**: Claude (Antigravity)
**セッション**: 5fb1904f-aaea-4244-8fc7-df5b11564467

---

## S: 状況

Motherbrain に動的レポート生成機能を実装するセッション。Phase 1 (データ集約+テンプレート) + Phase 2 (LLM統合) の2段構成。

## B: 背景

- Creator が手動で BRAIN データの統合レポートを作成していた作業を自動化する需要
- Motherbrain の既存 SQLite DB + MCP サーバーを活用

## A: 評価

### 完了タスク
1. `motherbrain_store.py` に `get_report_data()` 追加 (L1067-1180)
2. `report_generator.py` 新規作成 (render_report + generate_and_save)
3. MCP ツール `motherbrain_report` 追加 (days, save, narrate, title パラメータ)
4. テスト 17/17 通過
5. MCP 経由でレポート生成成功 (39セッション・48アーティファクト)
6. LLM ナレーション: httpx→CortexClient 直接呼出に修正
7. save パス: Linux ハードコード→HGK_ROOT ベースに修正

### 残タスク
- [ ] MCP サーバー再起動後に `narrate=true` の動作確認
- [ ] MCP サーバー再起動後に `save=true` の動作確認

## R: 推奨

`motherbrain` MCP サーバーを再起動して `narrate=true` + `save=true` をテストする。

---

## 変更ファイル

| ファイル | 操作 |
|---|---|
| `mekhane/symploke/motherbrain_store.py` | MODIFY — get_report_data() 追加 |
| `mekhane/symploke/report_generator.py` | NEW — Markdown レンダラー |
| `mekhane/mcp/motherbrain_mcp_server.py` | MODIFY — MCP ツール + LLM ナレーション + save 修正 |
| `mekhane/tests/test_report_generator.py` | MODIFY — ide_sessions 直接INSERT, NOT NULL修正 |
