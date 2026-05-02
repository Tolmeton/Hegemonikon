# Handoff: FM Plugin Build → フィールド一括作成

> **Session**: 2026-02-20 13:56–15:25 JST
> **Conversation**: cb9f8eb2-9ab9-4741-b9e5-50a52a8c0855

---

## 成果

### ✅ 達成

1. **SQLBatch プラグインのビルド成功** — x64 Native Tools Command Prompt で `build.bat` → `SQLBatch.fmx64` 生成
2. **プラグインの FM Pro 読込成功** — プラグイン一覧に表示、`SQLBatch_Version` 動作確認
3. **SELECT SQL 実行成功** — `ExecuteFileSQLTextResult` で SELECT が動作
4. **125 フィールドの一括作成成功** — CSV インポート → 新規テーブルで解決

### ❌ 失敗

1. **DDL (ALTER TABLE / CREATE TABLE) は FM SDK の `ExecuteFileSQLTextResult` で非対応** — ERROR:12
2. **プラグイン開発に約1時間を浪費** — 事前調査で回避できた

---

## 技術的知見

### FM Plugin SDK v22 の SQL 制約

| SQL 種別 | ExecuteFileSQLTextResult | ODBC/JDBC |
|---------|:---:|:---:|
| SELECT | ✅ | ✅ |
| INSERT/UPDATE/DELETE | ✅ | ✅ |
| ALTER TABLE / CREATE TABLE | ❌ | ✅ |

### フィールド一括作成の正解手順

1. CSV (UTF-8 BOM) でフィールド名をヘッダ行、ダミーデータを2行目に配置
2. FM Pro → ファイル → レコードのインポート → ファイル
3. **ターゲット: 「新規テーブル」を選択**（既存テーブルにインポートすると誤マッピング）
4. 125 フィールドが自動作成される

### ビルド環境

- **x64 Native Tools Command Prompt for VS 2026** が必須
- Developer PowerShell (x86) ではリンクエラー
- `cd /d C:\Users\makar\Hegemonikon\SQLBatch` → `build.bat`
- SDK: `C:\Users\makar\Downloads\fm_plugin_sdk_22.0.1.68\`

---

## 未完了タスク

1. **腎生検スクリプト v2 のテスト** — スクリプトを確認したが実行未完了
   - `腎生検_K_v2.xml`: 22 項目を TEMP テーブルから抽出 → 新規腎台帳に書込み
   - `id="0"` のフィールド（★追加マーク付き）は FM 内で再マッピングが必要
2. **IMP_ フィールドのテーブル移動** — 新規テーブルに作成された 125 フィールドを「新規腎台帳」に統合する必要あり
3. **SQLBatch プラグインの今後** — SELECT/INSERT/UPDATE/DELETE は動作する。DDL 以外の用途で活用可能

---

## BC 違反

| BC | 内容 | 深刻度 |
|:---|:-----|:------|
| BC-16 | DDL 対応可否を事前調査せずにプラグイン開発に着手 | HIGH |
| BC-14 | 高リスク判断前の Thought Record 未実行 | HIGH |
| BC-6 | DDL 動作を未検証のまま確信度高く提案 | MEDIUM |

### 教訓
>
> **実装前に API の制約を調査せよ。`/sop` を先に実行せよ。**
> **「できるはず」は仮説であり、事実ではない。**

---

## ファイル

| ファイル | 場所 | 内容 |
|---------|------|------|
| `SQLBatch.cpp` | `~/Sync/SQLBatch/` | プラグインソース |
| `build.bat` | `~/Sync/SQLBatch/` | ビルドスクリプト |
| `SQLBatch.fmx64` | FM Extensions フォルダ | ビルド済みプラグイン |
| `IMP_fields_v3.csv` | `~/Sync/` | 125 フィールドの CSV |
| `腎生検_K_v2.xml` | `projects/micks/scripts/` | インポートスクリプト |

---

*Generated: 2026-02-20T15:25 JST*
