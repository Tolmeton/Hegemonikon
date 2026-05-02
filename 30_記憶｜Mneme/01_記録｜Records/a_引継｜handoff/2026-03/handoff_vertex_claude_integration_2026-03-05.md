# Handoff: Vertex AI Claude Opus 4.6 統合

## セッション概要

- **日時**: 2026-03-05 10:30 - 12:20
- **目的**: Vertex AI の Claude Opus 4.6 を HGK フレームワークに統合
- **結果**: 6垢マルチアカウント + OchemaService 統合完了。Quota 承認待ち (3/7 以降)

## 成果物

| ファイル | 状態 | 内容 |
|:--------|:-----|:-----|
| `mekhane/ochema/vertex_claude.py` | ✅ 全面改修 | 6垢ラウンドロビン + 4リージョンフェイルオーバー + CostTracker ($600/月) |
| `mekhane/ochema/service.py` | ✅ 統合 | VERTEX_CLAUDE_MODELS + _ask_vertex_claude + stream() NotImplementedError |
| `experiments/vertex_claude/setup_gcloud_accounts.sh` | ✅ 作成 | 6垢 gcloud auth 一括セットアップ |

## 技術的発見

### モデル名の特定

- **正解**: `claude-opus-4-6` (ハイフン区切り)
- **間違い**: `claude-opus-4@20250514` (Anthropic API 風の @ バージョン)
- **発見方法**: Creator のスクリーンショット (GCP Console Quota ページ)

### Quota の挙動

- Model Garden で有効化直後の初期 Quota = 0 tokens/min
- 引き上げ申請 → 自動拒否「48h 待て」→ 3/7 に再申請
- 429 = 認証成功・Quota 不足 vs 403 = 権限なし

### 6 垢認証

- gcloud configurations で各垢独立トークン管理
- `gcloud auth print-access-token --configuration=xxx` で垢個別トークン取得
- 全24エンドポイント (6垢 × 4リージョン) で 429 確認 = 認証成功

## Creator のコード改善 (学ぶべきポイント)

Creator がセッション中に service.py を直接修正した内容:

1. `_vertex_client` を `__init__` で明示初期化 (`hasattr` → `is None`)
2. `close()` にクリーンアップ追加
3. `stream()` に NotImplementedError 分岐
4. LS フォールバックを二重 try/except に強化
5. timeout パススルーを末端まで伝播

→ **教訓**: シングルトンの管理は `hasattr` ではなく明示的な `None` 初期化 + `is None` チェック。Creator はこのパターンを一貫して適用する。

## 次セッションで最初にやること

1. **3/7 10:52 以降**: 6 垢で Quota 再申請
   - 200K input TPM / 50K output TPM / 10 RPM
   - 申請理由: 前回と同じ英文 (既に用意済み)
2. **Quota 通過後**: `python -m mekhane.ochema.vertex_claude "test"` で rawPredict 成功確認
3. **HGK APP 統合**: Gateway/MCP から `opus-vertex` ルートで Claude Opus を呼ぶ実装

## 環境状態

| 項目 | 状態 |
|:-----|:-----|
| gcloud configurations | 6 垢設定完了 (全 token ✅) |
| Vertex AI Quota | 0 (全 6 垢、3/7 再申請) |
| vertex_claude.py | 6 垢 ラウンドロビン + 4 リージョン |
| OchemaService | opus-vertex ルート統合済み |
| CostTracker | $0 / $600 (未使用) |
