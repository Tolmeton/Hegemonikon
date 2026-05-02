---
name: FM Project Init
description: >
  新規 FM 案件の初期化手順。forge new コマンドでディレクトリ構造を
  自動生成し、mapping.yaml の雛形を作成する。

triggers:
  - 新しい FM 案件を始めるとき
  - "forge new" コマンド実行時
  - 案件のディレクトリ構造を確認するとき

keywords:
  - 新規案件
  - プロジェクト作成
  - forge new
  - 初期化

prerequisites:
  - forge パッケージが利用可能であること
  - DDR XML または Excel テンプレートが手元にあること

related_skills:
  - fm-xml-generate
  - fm-excel-analyze

lineage: "v1.0 — MICKS案件の知見を汎用 SKILL 化 (2026-03-05)"
version: "1.0.0"
---


````typos
#prompt fm-project-init
#syntax: v8.4
#depth: L2

<:role: FM Project Init :>
<:goal: 新規 FM 案件の初期化手順。forge new コマンドでディレクトリ構造を :>
````

# FM Project Init — 新規案件の初期化

> **核心**: `forge new <name>` で案件の雛形を一発生成
> **道具**: `forge.project.ProjectConfig.scaffold()`

---

## 1. 案件開始チェックリスト

### 1.1 プロジェクト作成

```bash
python -m forge new "project_name" \
  --display "表示名" \
  --description "案件の説明" \
  --fm-version "17" \
  --ddr path/to/ddr.xml \
  --excel path/to/template.xlsx
```

生成される構造:

```
projects/<name>/
├── project.yaml       # 案件メタデータ
├── mapping.yaml       # マッピング雛形 (手順コメント付き)
├── ddr/               # DDR XML 保存先
├── excel/             # Excel テンプレート保存先
├── scripts/           # 生成スクリプト
├── patches/           # パッチ XML
├── output/            # 生成物出力先
└── docs/
    └── progress.md    # 進捗チェックリスト
```

### 1.2 次のステップ

- [ ] DDR XML を `ddr/` にコピー → `forge analyze <name>`
- [ ] Excel を `excel/` にコピー → `forge analyze-excel <name>`
- [ ] `dump_for_claude()` の出力を見ながら `mapping.yaml` を記入
- [ ] `forge generate <name>` で XML 生成
- [ ] FM にペーストして動作確認

---

## 2. mapping.yaml 記入ガイド

```yaml
mappings:
  - excel_label: "患者氏名"     # Excel のラベル
    fm_field: "患者氏名"        # FM のフィールド名
    excel_col: "E"              # Excel の値列
    temp_col: 2                 # TEMP テーブルの列番号
    transform: ""               # 変換 (bp_systolic, dot_clean 等)
    category: "基本情報"        # セクション名
```

---

## 3. よくある問題

| 問題 | 対策 |
|:-----|:-----|
| DDR XML がない | FM Pro → ファイル → データベースデザインレポート |
| Excel テンプレートが複数シート | `analyze(sheet=...)` でシート指定 |
| mapping.yaml の temp_col が不明 | Excel の列番号（A=1, B=2...）|
| scaffold が既存ファイルを上書き | scaffold() はべき等。既存ファイルは保持 |

---

*v1.0 — MICKS 案件の知見を汎用 SKILL 化 (2026-03-05)*
