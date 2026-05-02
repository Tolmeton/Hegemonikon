# Handoff: Cortex API OAuth 復旧 + Syncthing 同期修復

**日付**: 2026-03-28
**作業者**: Claude Code (Opus 4.6)
**状態**: 完了 (残課題あり)

---

## 概要

Gemini Cortex API が全アカウントで 429 RESOURCE_EXHAUSTED → 調査の結果、認証トークンの不整合が原因と判明。Syncthing 同期障害も同時に修復。

## 障害の連鎖

```
Syncthing: .git/objects/pack (3.3GB) が帯域を占有
  → cortex_api.py が GALLERIA に同期されていなかった
  → ochema が不完全なコードで動作
  → Cortex API 呼び出しが全て失敗 (429)
```

## 実施した修正

### 1. Syncthing 同期修復
- **原因**: `.git/objects/pack/*.pack` (3.3GB) が同期キューをブロック
- **修正**: `.stignore` に git packfile 除外ルールを追加 (両デバイス)
  ```
  .git/objects/pack/*.pack
  .git/objects/pack/*.idx
  .git/objects/pack/*.rev
  ```
- **結果**: needFiles: 7,021 → 0

### 2. cortex_api.py 手動転送
- Syncthing 修復前の応急処置として SCP で GALLERIA に手動コピー

### 3. OAuth トークン修復 (movement / rairaixoxoxo)
- **発見**: 100.80.253.2 からコピーしたトークンが gcloud OAuth app (`32555940559`) 由来
- **問題**: `cloudcode-pa.googleapis.com` は gemini-cli app (`1071006060591`) 専用。gcloud app では 403 SERVICE_DISABLED
- **修正**: `vault_setup.py` の OAuth フローを手動再現し、gemini-cli client_id/secret で両アカウントを再認証
  - OAuth URL 生成 (v2/auth + redirect_uri=http://localhost)
  - Creator がブラウザで認証 → authorization code を取得
  - code → token 交換を GALLERIA 上で実行
  - `~/.config/ochema/tokens/{movement,rairaixoxoxo}.json` に保存
  - TokenVault に登録

### 4. account_router.py の一時修正と復元
- 壊れた2アカウントを一時除外 → 修復後に元の6アカウント構成に復元

## 最終状態

| アカウント | client_id | 状態 |
|:-----------|:----------|:-----|
| default | (Antigravity IDE管理) | 未検証 (IDE専用) |
| Tolmeton | 1071006060591 (gemini-cli) | OK |
| hraiki | 1071006060591 (gemini-cli) | OK |
| makaron | 1071006060591 (gemini-cli) | OK |
| nous | 1071006060591 (gemini-cli) | OK |
| movement | 1071006060591 (gemini-cli) | OK (再認証済) |
| rairaixoxoxo | 1071006060591 (gemini-cli) | OK (再認証済) |

Hub MCP → ochema → Gemini 3 Flash: 応答確認済み (7.5秒)

## 学んだこと

1. **cloudcode-pa は OAuth app-gated**: gemini-cli app のみアクセス可能。gcloud, 他の OAuth app では 403
2. **OOB リダイレクト廃止済み**: `urn:ietf:wg:oauth:2.0:oob` は 400 invalid_request。`http://localhost` リダイレクト方式を使う
3. **再認証手順**: `python -m mekhane.ochema.scripts.vault_setup add <name>` (ブラウザ必要)
4. **Syncthing + git packfile**: 巨大な pack ファイルが全体の同期をブロックする。`.stignore` で除外必須

## 残課題

### P1: Quota 分離の構造的欠如
- 全6アカウントが同一 OAuth client_id → 同一 quota bucket (推定)
- account_router のパイプライン分離は「アカウント」を分けているが「quota」は分けていない
- per-user vs per-app quota の実測が必要

### P2: 100.80.253.2 のトークン管理
- root 権限でアクセス不能 (`/root/.config/ochema/tokens/`)
- gcloud 版トークンが残存 (使用不可)

### P3: Google API 制約の強化傾向
- OOB 廃止、app-gating の強化。自前 OAuth app or 公式 API キーへの移行検討

## 関連ファイル

- `20_機構｜Mekhane/_src｜ソースコード/mekhane/ochema/account_router.py` — パイプライン別アカウント割当
- `20_機構｜Mekhane/_src｜ソースコード/mekhane/ochema/scripts/vault_setup.py` — OAuth 認証 CLI
- `20_機構｜Mekhane/_src｜ソースコード/mekhane/ochema/token_vault.py` — マルチアカウントトークン管理
- `20_機構｜Mekhane/_src｜ソースコード/mekhane/ochema/cortex_api.py` — Cortex API HTTP 層
- `.stignore` — Syncthing 除外ルール (git packfile 追加)
