---
name: FM Excel Analyze
description: >
  Excel テンプレートの構造化解析。openpyxl で読み取り、Claude が
  mapping.yaml を効率的に作成するための構造ダンプを出力する。
  「機械が読み取り、Claude が解釈する」

triggers:
  - Excel テンプレートを解析する必要があるとき
  - mapping.yaml を新規作成するとき
  - "forge analyze-excel" コマンド実行時

keywords:
  - Excel
  - xlsx
  - マッピング
  - テンプレート解析

prerequisites:
  - openpyxl がインストールされていること
  - Excel ファイル (.xlsx) が手元にあること

related_skills:
  - fm-xml-generate

lineage: "v1.0 — MICKS案件の知見を汎用 SKILL 化 (2026-03-05)"
version: "1.0.0"
---


````typos
#prompt fm-excel-analyze
#syntax: v8.4
#depth: L2

<:role: FM Excel Analyze :>
<:goal: Excel テンプレートの構造化解析。openpyxl で読み取り、Claude が :>
````

# FM Excel Analyze — Excel テンプレート構造解析

> **核心**: 「機械が読み取り、Claude が解釈する」
> **道具**: `forge.engines.excel_analyze.ExcelAnalyzer`
> **原則**: 完全自動マッピングは不可能。Claude の解析を高速化する

---

## 1. 解析手順チェックリスト

### 1.1 Excel 構造の取得

```python
from forge.engines.excel_analyze import ExcelAnalyzer
from pathlib import Path

a = ExcelAnalyzer()
template = a.analyze(Path("template.xlsx"), sheet="記入用紙")
print(a.dump_for_claude(template))
print(a.dump_mapping_hints(template))
```

- [ ] `dump_for_claude()` でセクション構造を確認
- [ ] `dump_mapping_hints()` でラベル→値列ペアを確認
- [ ] シート名が正しいか確認（データ用シートと入力用シートが別の場合あり）

### 1.2 DDR フィールド一覧との照合

```python
from forge.engines.analyze import FMStructure
from forge.engines.mapping import MappingEngine

# DDR XML をパースして構造を取得
structure = FMStructure(filename="ddr.xml", tables=[], relationships=[])
# NOTE: FMStructure は analyze.py の解析結果として生成される。
# 直接 from_xml() メソッドは存在しない。analyze_ddr() を使用すること。
```

- [ ] DDR のテーブル・フィールド一覧を取得
- [ ] Excel ラベルと FM フィールド名を照合
- [ ] ★付きフィールドは手動入力項目

### 1.3 mapping.yaml ドラフト作成

- [ ] mapping hints の「→ 列」を temp_col として使用
- [ ] セクションを category として使用
- [ ] 確信度が低い項目に `confidence < 1.0` を設定
- [ ] `transform` が必要な項目を特定（血圧 → bp_systolic/bp_diastolic 等）

---

## 2. Excel テンプレートの典型パターン

| パターン | 説明 | 例 |
| :------- | :--- | :- |
| ラベル-値ペア | 左に結合ラベル、右端+1列が入力欄 | `[A]施設名 → [E]` |
| 3列構造 | 検査値が A列/P列/AE列 の3グループ | 血液検査の行 |
| 結合見出し | セクション名は A列 結合セルで表現 | `[A1:D1]腎生検...` |
| チェックボックス | (−)/(+) の選択はセル値ではなくフォント色等で表現 | 既往歴 |

---

## 3. よくある落とし穴

| 問題 | 原因 | 対策 |
| :--- | :--- | :--- |
| ラベルと値のずれ | 結合セルの右端が不正確 | dump_mapping_hints の出力を目視確認 |
| セクション過多 | 個別検査項目もセクション扱い | _detect_sections のキーワードを調整 |
| 空シート | data_only=True で数式結果が None | data_only=False で再試行 |
| 結合セルの値消失 | 結合範囲の先頭セルのみに値がある | openpyxl の仕様。先頭セルを参照 |

---

*v1.0 — MICKS 案件の知見を汎用 SKILL 化 (2026-03-05)*
