# 90_保管庫｜Archive — EFE · 過去政策 (Q_{t-1})

> **FEP 演繹**: Archive は能動推論の「過去政策の記録庫」。
> もはや使われない古い行動政策 Q_{t-1} を保存する帯。

---

## 分類基準: EFE 変数 Q_{t-1} (過去の政策)

**唯一の問い: 「これはなぜ obsolete になったか？」**

### 番号付き帯 (旧 Nous/Mekhane/Mneme の保管)

| 帯 | 内容 |
|:---|:-----|
| `00_スクリプト｜Scripts` | 廃止された自動化スクリプト |
| `01_設計｜Designs` | 旧設計ドキュメント (kube 等) |
| `02_アセット｜Assets` | 旧アセット (壁紙、テンプレ等) |
| `03_テキストミラー｜TextMirror` | 旧テキストミラー |
| `03_企画_clawx_src` | 旧プロジェクト (ClawX) ソース |
| `05_出力｜Output` | 旧出力・実行結果・ベンチマーク |
| `06_スキル｜Skills` | 廃止されたスキル定義 |
| `07_ワークフロー｜Workflows` | 廃止されたワークフロー |

### 旧モジュール保管

| 帯 | 内容 |
|:---|:-----|
| `20_Mekhane_legacy` | 旧 Mekhane モジュール群 (Aristos, Bytebot, Synergeia, Pepsis) |
| `30_Mneme_Archive` | 旧 Mneme エクスポート (MECE 解析, 索引等) |
| `30_Records_legacy` | 旧 Records (artifacts, logs, patterns) |
| `80_Infrastructure` | 旧インフラ (kube, periskope 初期版) |

### アルファベット帯 (旧体系構造)

| 帯 | 内容 |
|:---|:-----|
| `A_旧規則｜ArchivedRules` | 旧 BC/規則 (CONSTITUTION, anti-timidity 等) |
| `B_旧技能｜SkillsArchive` | 旧スキルスキーマ |
| `C_旧手順｜WorkflowsArchive` | 旧 WF (boot_v3.9, bye_v3.3, ccl-* レガシー) |
| `D_旧公理構造｜AxiomsLegacy` | 旧公理体系 (axiom_hierarchy v2-3, doctrine v3.2) |

---

## 境界ケースの判定

| ケース | 判定 |
|:-------|:-----|
| 古い BC/規則 → どこへ？ | `A_旧規則` |
| 古い WF → どこへ？ | `C_旧手順` (実験失敗の WF は Peira→Archive) |
| 古いスキル → どこへ？ | `B_旧技能` or `06_スキル` |
| 古い公理構造 → どこへ？ | `D_旧公理構造` |
| 旧 Mekhane モジュール → どこへ？ | `20_Mekhane_legacy` |
| 復活の可能性があるもの | Archive に置くが README に「復活候補」と記載 |

---

*Archive EFE Classification v1.1 — 2026-03-13*
