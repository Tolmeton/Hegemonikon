# Handoff: /dio Triage 完了 + F1 GCP IAM 修復

> **セッション**: 2026-02-25 21:30–22:25 JST
> **目的**: 前回 /dio トリアージで抽出された F1–F5 の未踏アイテムを完了させる
> **結果**: F1–F4 完了、F5 はスキップ（F1 解決により不要化）

---

## 📋 タスク結果

| F# | 内容 | 結果 | 備考 |
|:---|:-----|:-----|:-----|
| F1 | GCP IAM 権限修復 | ✅ 完了 | `roles/cloudaicompanion.user` 付与 + `CORTEX_PROJECT` 設定 |
| F2 | ドキュメントガバナンス | ✅ 作成済み | `hgk/docs/DOCUMENT_GOVERNANCE.md` — **commit 待ち** |
| F3 | CI ワークフロー | ✅ 作成済み | `hgk/.github/workflows/tests.yml` — **commit 待ち** |
| F4 | hgk-cli.sh | ✅ 動作確認済み | ポート 9698、7コマンド対応 |
| F5 | Cortex 依存脱却 | ⏭️ スキップ | F1 解決により緊急性消失、Creator 判断で見送り |

---

## 🔑 F1 詳細: GCP IAM 権限修復

### 問題

Cortex API の `generateContent` (= `ask_with_tools`) が全アカウントで 403 Permission Denied を返していた。

### 原因特定

1. `loadCodeAssist` API が動的プロジェクト ID (`driven-circlet-rgkmt`) を返す
2. この内部プロジェクトに対する `cloudaicompanion.companions.generateChat` 権限がなかった
3. `hraiki` アカウントのみ例外的に成功（サブスクリプションの違い）
4. `generateChat` API は別経路で認証されるため影響なし

### 解決策

1. **IAM 権限付与**: `project-d4c65f26-e7d2-44af-841` に対して Vault 内全6アカウントに `roles/cloudaicompanion.user` を付与

```bash
gcloud projects add-iam-policy-binding project-d4c65f26-e7d2-44af-841 \
  --member="user:{email}" --role="roles/cloudaicompanion.user"
```

1. **プロジェクト指定**: `.env` に `CORTEX_PROJECT=project-d4c65f26-e7d2-44af-841` を追加。`cortex_client.py` の `_get_project()` が `CORTEX_PROJECT` 環境変数を優先参照するため、動的プロジェクト解決をバイパス。

### 検証結果

`CORTEX_PROJECT` 設定後、`default`, `movement`, `Tolmeton` アカウントで `generateContent` 成功を確認（残り3アカウントは 429 レート制限のみで権限エラーなし）。

---

## 📂 変更ファイル

| ファイル | 変更内容 | リポジトリ | commit 状態 |
|:---------|:---------|:-----------|:------------|
| `scripts/hgk-cli.sh` | 新規作成 (ポート 9698, API パス修正済み) | hegemonikon | uncommitted |
| `hgk/.github/workflows/tests.yml` | 新規作成 (CI ワークフロー) | hgk | staged |
| `hgk/docs/DOCUMENT_GOVERNANCE.md` | 新規作成 (ガバナンスルール) | hgk | staged |
| `.env` | `CORTEX_PROJECT` 追加 | hegemonikon | uncommitted (.gitignore) |

---

## ⚡ API サーバー確認結果

| 項目 | 結果 |
|:-----|:-----|
| 実際のポート | **9698** (uvicorn `--port 9698` で起動、PID 654) |
| `DEFAULT_PORT` コード上 | 9696 (起動引数で上書き) |
| `/api/status` | ✅ 11項目 JSON (score: 0.636) |
| `/api/docs` | ✅ Swagger UI |
| `/api/gnosis/search` | ✅ 応答あり |

---

## 🎯 次回アクション

1. **hgk リポジトリの commit/push**:

   ```bash
   cd ~/oikos/hegemonikon/hgk
   git commit -m "ci: add GitHub Actions workflow + document governance"
   git push origin master
   ```

2. **hgk-cli.sh の commit**:

   ```bash
   cd ~/oikos/hegemonikon
   git add scripts/hgk-cli.sh
   git commit -m "feat: add hgk-cli.sh HTTP API helper script"
   ```

3. **Periskopē L2 ベンチマーク再実行**: F1 修正により `ask_with_tools` が復活したため、LLM rerank を含む L2 ベンチマークの再実行が可能に

---

## ⚠️ 未解決・注意事項

- **Jules MCP**: EOF エラーで接続不可。IDE/Cowork 側の問題。再起動で回復する可能性あり
- **Ochema MCP**: 同様に EOF。MCP サーバー全体の再起動が必要
- **ker(R)**: チャット履歴エクスポートは LS 不在のためスキップ

---

*Handoff generated: 2026-02-25T22:25 JST*
