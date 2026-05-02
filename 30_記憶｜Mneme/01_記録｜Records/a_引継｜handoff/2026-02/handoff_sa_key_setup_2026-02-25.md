# Handoff: SA Key Setup for Vertex Search — 3アカウント完了

## セッション概要

- **日時**: 2026-02-25 13:00 - 21:25
- **目的**: Vertex AI Search の SA 鍵認証を3アカウント分設定する
- **結果**: 全3アカウントで org ポリシー無効化 → SA 作成 → 鍵配置 → config.yaml 更新完了。テスト 26 passed。

## 成果物

| ファイル | 状態 | 内容 |
|:--------|:-----|:-----|
| `mekhane/periskope/config.yaml` | ✅ 更新 | 3エンジンの `credentials_file` を絶対パスで設定 |
| `.secrets/makaron8426-vertex-search.json` | ✅ 配置 | SA: `vertex-search-sa@project-f2526536...` |
| `.secrets/Tolmeton-vertex-search.json` | ✅ 配置 | SA: `vertex-search-sa@project-f2526536...` |
| `.secrets/movement8426-vertex-search.json` | ✅ 配置 | SA: `vertex-search-sa-periskope@project-d4c65f26...` (専用SA) |
| `.gitignore` | ✅ 更新 | `.secrets/` 追加 |
| `mekhane/periskope/searchers/vertex_search_searcher.py` | ✅ 更新 (前セッション) | 5つの修正 (認証優先度、quota tracking、ログ、劣化サマリー、token cache) |

## 重要な知見

### 1. 組織ポリシー無効化の手順

GCP で SA 鍵作成がブロックされている場合:

1. **IAM > ロール付与**: アカウントに「Organization Policy Administrator」を組織レベルで付与
2. **IAM > 組織のポリシー > `iam.disableServiceAccountKeyCreation`**: 親のポリシーをオーバーライド → オフ
3. SA 鍵 → キーを追加 → JSON

### 2. クロスプロジェクト問題 — 実は不在

`/ops_/dio*%/lys` で movement8426 のエンジンが別プロジェクトにあると指摘したが、**config の `project: "1003263550004"` はプロジェクト番号** (数字) であり、**プロジェクト ID は `project-d4c65f26-e7d2-44af-841`** — makaron8426 と同一プロジェクトだった。ただし専用 SA を分離したことで責務の分離は達成。

### 3. 認証優先順位

```
SA key (credentials_file) → gcloud CLI (gcloud_account) → ADC (fallback)
```

SA 鍵が存在しない場合は gcloud_account にフォールバック。token cache はクラス変数で共有。

### 4. Playwright ダウンロードファイルの消失

`/tmp/playwright-artifacts-*` は一時ディレクトリで、セッション間で消える。ダウンロード成功後は即座に永続ストレージにコピーすること。

## 組織ポリシー状況

| 組織 | org ID | ポリシー | SA 数 |
|:-----|:-------|:--------|:------|
| makaron8426-org | 673438422024 | ✅ 未適用 | 1 (vertex-search-sa) |
| Tolmeton-org | 511012843486 | ✅ 未適用 | 1 (vertex-search-sa) |
| movement8426-org | 569953010828 | ✅ 未適用 | 2 (vertex-search-sa + vertex-search-sa-periskope) |

## 残タスク

| タスク | 優先度 | 説明 |
|:------|:-------|:-----|
| SA 認証の実検証 | HIGH | テストが本当に SA 鍵経由で認証されているか未確認。意図的に鍵を無効化してフォールバック動作を検証すべき |
| スキップテストの調査 | LOW | 26 passed, 1 skipped — 何がスキップされているか未調査 |
| IAM 最小権限レビュー | MEDIUM | 各 SA に付与されたロールの過不足確認 |
| movement8426 の SA ロール付与 | MEDIUM | `vertex-search-sa-periskope` へのロール付与がブラウザ操作で失敗した可能性あり。要確認 |
| 組織ポリシー再有効化検討 | LOW | セキュリティ観点で、SA 鍵作成完了後にポリシーを再有効化すべきか |

## 法則化

> **Playwright のダウンロードファイルは揮発する**: `/tmp/playwright-artifacts-*` に保存されるが、セッション間で消失する。成功確認後は即座に永続ストレージに `cp` すること。
>
> **GCP プロジェクト番号 ≠ プロジェクト ID**: config.yaml で `project: "1003263550004"` と `project-d4c65f26-e7d2-44af-841` は同一プロジェクト。混同注意。

---

*Handoff v7.5 — SA Key Setup 2026-02-25*
