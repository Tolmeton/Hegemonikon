---
rom_id: rom_2026-02-25_micks_k_to_j_transfer
session_id: 6ec1e618-0bf4-4f01-a91d-4c2dc59890a7
created_at: 2026-02-25 15:54
rom_type: distilled
derivative: deep
reliability: High
topics: [MICKS, FM(J), FM(K), K→J移行, IMP_フィールド, インポートスクリプト, 腎生検]
exec_summary: |
  FM(K) の全142項目インポート実装が完了。次はこの知見を活用して FM(J) の
  インポートスクリプトを作成する。J と K の差異・共通点を構造化して記録。
---

# K→J 移行のための蒸留知識 {#overview}

> **[DECISION]** 顧客回答 Q2:「使用者はどちらも私です。J = K は同一範囲で取り込む」
> → J も K と同じ 141 項目を対象とする。

---

## 1. K で確立した実装パターン（J にそのまま適用可能） {#patterns}

### 1.1 アーキテクチャ

```
Excel → _TEMP_インポート テーブル (22列) → 変数抽出 (行移動+GetField) → フィールド設定 (新規腎台帳 / 腎生検2012.01～)
```

- **_TEMP_ テーブル**: 22列 (A,C,E,F,H,J,L,M,O,P,U,W,X,Z,AA,AB,AC,AD,AE,AF,AI,AJ)
- **変数抽出**: 行移動 → `$_変数名` に格納 → フィールド設定ステップで書き込み
- **Excel 構造**: 4日版テンプレートの「記入用紙」シートから直接インポート

### 1.2 フィールド分類

| 分類 | 意味 | K での数 |
|:-----|:-----|:--------:|
| EXISTS | FM に既存フィールドがある → そのまま使う | 22 |
| NEW (IMP_) | FM にフィールドがない → `IMP_` プレフィックスで新規作成 | ~119 |
| 不要 | リネームや統合で吸収 | 2 (フリガナ→リネーム, 生検番号→前回番号★) |

### 1.3 教訓（そのまま J に適用）

| # | 教訓 | 詳細 |
|:--|:-----|:-----|
| L1 | フィールド名に括弧禁止 | `()`, `[]`, `{}`, `/`, `:` は FM が計算式パーサーで誤認。`_` で代替 |
| L2 | CSV でフィールド作成しない | 記号が `_` に置換される。XML ペースト (`Mac-XMFD`) を使う |
| L3 | 顧客の専門名はラベルで維持 | フィールド名は FM 命名規則、TextObj ラベルは専門名のまま |
| L4 | 同名別物に注意 | IgG★(蛍光) ≠ IMP_IgG(血清)。C3★(蛍光) ≠ IMP_C3(血清) |
| L5 | リネームで済むなら新規作成しない | ふりがな→フリガナ, 前回番号→前回番号★ |
| L6 | v7 テンプレートを流用 | オフスクリーンウィンドウ方式 (白画面一瞬) がベスト |

---

## 2. J と K の差異（★最重要★） {#differences}

### 2.1 数値比較

| 指標 | FM(J) | FM(K) | 差異 |
|:-----|:-----:|:-----:|:-----|
| 対応表の J/K 既存フィールド | **23** | **16** | J の方が 7 個多い |
| ★付き既存フィールド（DDR 全体） | **73+** | 約 30 | J は病理所見フィールドが大量 |
| テーブル名 | 腎生検2012.01～ | 新規腎台帳 | **異なる** |
| フィールド総数 | 432 | 648 | K の方が多い（IMP_ 追加後） |

### 2.2 J にだけ存在するフィールド（対応表の J 既存 23 個）

> SOURCE: 案件01_腎生検Excel取込.md §4 + mapping_J_skeleton.yaml

**基本情報** (9): 光顕番号★, 前回番号★, 年齢★, 性別★, 施設名★, 生検日★, 生検日★コピー, 臨床診断★, 電顕番号★
**既往歴** (2): DM既往★, HT既往★ (+RPS分類(DM)★ は J 固有)
**現症** (4): 体重★, 身長★, 収縮期血圧★, 拡張期血圧★
**尿検査** (5): 尿潜血(定性)★, 尿潜血(沈査)★, 尿蛋白(g/day)★, 尿蛋白(g/gCr)★, 尿蛋白(定性)★
**血液検査** (7+): C3dp★, C3★, IgA★, IgG★, IgM★, SCr★, alb★, ISKDC Grade★, IgG subclass★
**病理** (多数): 診断1-4★, H-Grade★, 総糸球体★, 肥大糸球体★ など

> ⚠️ **J の「C3★」「IgA★」「IgG★」「IgM★」「Fibrinogen★」は蛍光抗体法の所見**。
> 対応表の赤字 #83-85,#89 (IgG/IgA/IgM/C3 mg/dL) は血清検査値であり**別物**。
> K と同様、IMP_IgG / IMP_IgA / IMP_IgM / IMP_C3 を新規作成する必要がある。

### 2.3 J と K で共通の 141 項目マッピング

> **[RULE]** 141 項目の Excel セル位置 (行/列) は J でも K でも同じ。
> 変わるのは FM 側のフィールド名と ID のみ。

→ **K の v7 スクリプトの「変数抽出」部分はそのまま流用可能**。
→ **「フィールド設定」部分を J のフィールド名/ID に差し替えればよい**。

---

## 3. J 作業の具体的手順（次セッションで実行） {#next_steps}

### Phase 1: J の DDR 解析

1. FM(J) の DDR XML (`filemaker (J)_fmp12.xml`) をパースして `structure/` に JSON 出力
2. J の★付きフィールド一覧(ID含む)を抽出
3. 対応表 141 項目 × J 既存フィールドの突合 → EXISTS / NEW_FIELD_NEEDED を分類

### Phase 2: J の IMP_ フィールド作成

1. K と同様の方法で `IMP_fields_J.xml` を生成 (Mac-XMFD 形式)
2. `fm_paste_fields.ps1` で FM(J) にペースト
3. Inspector で確認 → `field_id_map_J.json` を取得

### Phase 3: J の v7 スクリプト生成

1. K の `mapping_k_v2_全項目.md` をテンプレートとして `mapping_j_v1_全項目.md` を作成
2. EXISTS フィールドの ID を J の実 ID に差し替え
3. IMP_ フィールドの ID を Phase 2 で取得した ID に差し替え
4. `腎生検_J_v7.xml` を生成

### Phase 4: テスト

1. テストデータ (サンプルA/B/C.xlsx) でインポートテスト
2. IMP レイアウト (J 版) を作成して全フィールド検証

---

## 4. ファイルの所在 {#files}

| 役割 | パス |
|:-----|:-----|
| **案件マスタードキュメント** | `projects/micks/案件01_腎生検Excel取込.md` |
| **K 完成版マッピング** | `projects/micks/mapping_k_v2_全項目.md` |
| **J マッピング骨格** | `projects/micks/mapping_J_skeleton.yaml` (DDR 自動生成、excel_row/col 未設定) |
| **J 完成版マッピング** | `projects/micks/mapping_j_complete.yaml` (★要確認: 精度未検証) |
| **K v7 スクリプト** | `Sync: スクリプト｜Scripts/腎生検_K_v7.xml` |
| **K フィールドID** | `projects/micks/scripts/field_id_map.json` |
| **J DDR XML** | `案件01.../ファイル/filemaker (J)_fmp12.xml` |
| **K DDR XML** | `案件01.../ファイル/filemaker (K)_fmp12.xml` |
| **顧客確認事項** | `案件01.../ドキュメント｜Documents/質問事項_顧客確認_20260225.md` |
| **テストデータ** | `projects/micks/サンプルA.xlsx`, `サンプルB.xlsx`, `サンプルC.xlsx` |
| **K IMP レイアウト XML** | `案件01.../フィールド定義｜FieldDefs/TEMPインポート` |

> 共通ルート: `/home/makaron8426/Sync/oikos/20_作業場｜Workspace/A_仕事｜Work/a_ファイルメーカー｜FileMaker/01_MICKS/`

---

## 5. 注意事項 {#warnings}

> ⚠️ J のテーブル名は「**腎生検2012.01～**」であり、K の「新規腎台帳」とは異なる。スクリプト内のテーブル参照を必ず書き換えること。

> ⚠️ J の★付きフィールドには K にはない病理所見系（Oxford M/E/S/T/C, ISN/RPS分類, ISKDC Grade, H-Grade, 各種deposit, Foot process fusion 等）が大量にある。これらは対応表の 141 項目には含まれないが、既存構造を壊さないよう注意。

> ⚠️ `mapping_J_skeleton.yaml` の confidence は全て 0.5 (DDR 自動生成)。Inspector 実機確認が必要。

> ⚠️ J のフィールド名にも括弧 `()` が含まれている可能性がある (例: `尿潜血 (定性)★`)。K と同様にリネームが必要かどうか確認すること。

---

<!-- ROM_GUIDE
primary_use: FM(K)からFM(J)へのインポートスクリプト移植に必要な知識の完全な記録
retrieval_keywords: MICKS, FM(J), FM(K), K→J, 移行, IMP_, 腎生検, mapping, スクリプト, DDR
expiry: 2026-04-30
-->
