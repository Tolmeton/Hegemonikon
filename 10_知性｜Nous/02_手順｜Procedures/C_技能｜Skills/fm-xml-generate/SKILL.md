---
name: FM XML Generate
description: >
  FileMaker スクリプト XML (fmxmlsnippet) の生成定型手順。
  mapping.yaml → FMXMLBuilder → 6ブロック XML の一貫したパイプライン。
  generate_v9.py の知見を汎用化し、次の案件にも適用可能にする。

triggers:
  - FM スクリプト XML を生成する必要があるとき
  - mapping.yaml が定義済みで、FM にペーストするスクリプトが必要なとき
  - "forge xml", "forge generate", "forge pipeline" コマンドの実行時
  - Excel → FM 取込スクリプトの作成・修正時

keywords:
  - fmxmlsnippet
  - FileMaker
  - スクリプト生成
  - XML
  - インポート
  - fm_paste

prerequisites:
  - mapping.yaml が作成済み（forge map コマンドまたは手動）
  - DDR XML を解析済み（forge analyze）
  - 対象の FM ファイル名・テーブル名・レイアウト名が判明している

related_skills:
  - fm-automation
  - code-protocols

lineage: "v1.0 — MICKS案件 generate_v9.py の知見を汎用 SKILL 化 (2026-03-05)"
version: "1.0.0"
---


````typos
#prompt fm-xml-generate
#syntax: v8.4
#depth: L2

<:role: FM XML Generate :>
<:goal: FileMaker スクリプト XML (fmxmlsnippet) の生成定型手順。 :>
````

# FM XML Generate — FileMaker スクリプト XML 生成

> **核心**: mapping.yaml → FM にペースト可能な完全な fmxmlsnippet XML をワンコマンドで生成する
> **道具**: `forge.engines.xml_generate.FMXMLBuilder` + `XMLScriptGenerator`
> **原則**: 退屈で確実な XML 生成。CDATA、要素順序、ダミーID の仕様を厳守する

---

## 1. XML 生成の鉄則 (MICKS 案件で検証済み)

### 1.1 CDATA の扱い

| ルール | 理由 |
|:-------|:-----|
| **Calculation 要素は CDATA で囲む** | FM 式に `<` `>` `&` が含まれる |
| **CDATA 内は XML エスケープしない** | `&` をそのまま書く |
| **Name 要素は CDATA 不要** | 変数名に特殊文字がなければ plain text |

### 1.2 要素の順序 (致命的)

| ステップ | 正しい順序 | 誤った順序の結果 |
|:---------|:-----------|:---------------|
| **Set Field** | `<Calculation>` → `<Field>` | FM が値を無視する |
| **Set Variable** | `<Value>` → `<Repetition>` → `<Name>` | FM が変数名を認識しない |
| **Go to Record** | `<NoInteract>` → `<RowPageLocation>` → `<Calculation>` | 移動先が空になる |

> **CRITICAL**: `Set Field` で `<Field>` を `<Calculation>` より先に書くと、
> FM は計算結果をフィールドに書き込まない。これは v7 で発覚した致命的な仕様。

### 1.3 ダミー ID

| 対象 | ID | 理由 |
|:-----|:--:|:-----|
| `<Field id="0">` or `<Field id="1">` | 0 or 1 | FM は table + name で解決する |
| `<Layout id="0">` | 0 | FM は name で解決する |
| `<Table id="0">` | 0 | FM は name で解決する |

---

## 2. 6ブロック構成 (FM インポートスクリプトの標準構造)

### 生成API

| メソッド | 用途 |
|:---------|:-----|
| `XMLScriptGenerator.generate_full_xml()` | 6ブロック全体を一括生成 (推奨) |
| `XMLScriptGenerator.generate_block4_xml()` | Block 4 (Extract) のみ生成（パッチ時） |
| `XMLScriptGenerator.generate_block5_xml()` | Block 5 (Set Field) のみ生成（パッチ時） |

```
Block 1: Init          — エラー処理ON, 強制終了OFF, 画面固定, $_元レイアウト保存
Block 2: ファイル選択   — ファイルダイアログ, キャンセル時終了
Block 3: TEMP clear    — _TEMP_インポートに切替, 全削除, Excel インポート
Block 4: Extract       — 各行のTEMPレコードから変数に値を取り出す
Block 5: Set Fields    — 実テーブルに新規レコード作成, 変数→フィールドに書込
Block 6: Cleanup       — TEMP削除, 元レイアウト復帰, 完了ダイアログ
```

### 各ブロックの FMXMLBuilder API 対応

| Block | メソッド群 |
|:------|:----------|
| 1 | `error_capture()`, `allow_user_abort()`, `refresh_window()`, `set_variable()` |
| 2 | `set_variable()`, `if_()`, `exit_script()`, `end_if()` |
| 3 | `go_to_layout()`, `show_all_records()`, `if_()`, `delete_found_records()`, `end_if()`, `import_records()` |
| 4 | `go_to_record()`, `set_variable()` / `set_variable_with_text()` |
| 5 | `go_to_layout()`, `new_record()`, `set_field()` / `set_field_clean()`, `commit_records()` |
| 6 | `go_to_layout()`, `show_all_records()`, `delete_found_records()`, `go_to_layout_by_calc()`, `show_dialog()`, `refresh_window()`, `error_capture()` |

---

## 3. TRANSFORMS 辞書 (宣言的データ変換)

mapping.yaml の `transform` フィールドから名前で参照。
`{var}` は実際の変数名に置換される。

| 名前 | FM 計算式 | 用途 |
|:-----|:---------|:-----|
| *(空 / passthrough)* | `{var}` | そのまま |
| `dot_clean` | `If(Left({var};1)="."; "0"&{var}; {var})` | `.34` → `0.34` |
| `bp_systolic` | `LeftWords(Substitute({var}; "/"; " "); 1)` | `130/82` → `130` |
| `bp_diastolic` | `RightWords(Substitute({var}; "/"; " "); 1)` | `130/82` → `82` |
| `as_number` | `GetAsNumber({var})` | テキスト→数値変換 |
| `as_text` | `GetAsText({var})` | 明示的テキスト化 |
| `trim` | `Trim({var})` | 前後空白除去 |
| `custom` | *(mapping.yaml の custom_calc を直接使用)* | 特殊変換 |

### 新しい transform の追加手順

1. `xml_generate.py` の `TRANSFORMS` 辞書に1行追加
2. mapping.yaml で `transform: "新しい名前"` を使用
3. テストで生成XML内の Calculation を目視確認

---

## 4. 実行チェックリスト

### 4.1 XML 生成前

- [ ] mapping.yaml が最新か確認 (`forge verify` でバリデーション)
- [ ] DDR 構造データが存在するか (`structure/` ディレクトリ)
- [ ] テーブルオカレンス名が mapping.yaml に記載されているか
- [ ] 入力レイアウト名が判明しているか

### 4.2 XML 生成時

- [ ] `forge xml <project>` または `XMLScriptGenerator.generate_full_xml()` を使用
- [ ] Block 2 のファイルダイアログは FM GUI で手動追加が必要（XML では完全再現不可）
- [ ] Import Records の TargetFields が mapping の temp_col と一致しているか
- [ ] Extract で GetAsText() を使用しているか (`use_get_as_text=True`)
- [ ] Set Field の transform が正しく適用されているか

### 4.3 XML 生成後

- [ ] `<fmxmlsnippet>` で始まり `</fmxmlsnippet>` で終わるか
- [ ] CDATA が正しく閉じているか (`]]>` の漏れがないか)
- [ ] step_count() が期待値と一致するか
- [ ] Windows 側に XML ファイルが同期されているか (Syncthing)
- [ ] `fm_paste.ps1` でペーストし、FM スクリプトエディタで表示されるか

---

## 5. よくある失敗とその対策

| 失敗 | 原因 | 対策 |
|:-----|:-----|:-----|
| Set Field で値が入らない | Calculation と Field の順序が逆 | 必ず `<Calculation>` → `<Field>` |
| Go to Record で移動しない | NoInteract / RowPageLocation が欠落 | `go_to_record()` メソッドに含まれている |
| インポートで列がずれる | TargetFields の DoNotImport/Import 指定ミス | mapping.yaml の temp_col を再確認 |
| TEMP に値が入っていない | Excel のシート名が「記入用紙」でない | FM のインポート設定でシートを再選択 |
| `.34` が `34` になる | FM がテキストを数値として解釈 | `GetAsText()` + `dot_clean` transform |
| ペースト後に FM がエラー | XML が well-formed でない | CDATA の閉じタグ確認 |

---

## 6. ワンコマンド実行 (将来の理想)

```bash
# mapping.yaml → 完全な XML → Windows 配置
forge pipeline micks --layout "カウント" --target K

# 内部動作:
# 1. mapping.yaml を読み込み
# 2. DDR 構造データと照合 (verify)
# 3. XMLScriptGenerator.generate_full_xml() で6ブロック XML 生成
# 4. output/ に保存
# 5. Syncthing で Windows 側に自動同期
```

---

*v1.0 — MICKS 案件の知見を汎用 SKILL 化 (2026-03-05)*
