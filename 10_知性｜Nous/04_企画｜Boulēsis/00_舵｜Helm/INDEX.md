# 📇 HGK OS ドキュメント MECE インデックス

> **作成**: 2026-03-08
> **最終更新**: 2026-04-17
> **目的**: HGK OS (認知OS) 関連文書の全景を MECE に整理し、ナビゲーションを提供する
> **分類軸**: `AMBITION.typos` の機能フレーム (F1-F10) × ドキュメント種別

---

## 分類構造

```
HGK OS ドキュメント
├── A. ビジョン・企画 (Why / What)
│   ├── A1. ビジョン本体
│   ├── A1.5. 変換規則 (Protocol)
│   └── A2. 実装仕様 (IMPL_SPEC)
├── B. 設計・技術 (How)
│   ├── B1. アーキテクチャ
│   └── B2. UI/UX
├── C. 運用・作業 (Do)
│   ├── C1. 作業指示書
│   └── C2. 外部分析
└── D. 記録・記憶 (Was)
    ├── D1. セッションログ
    ├── D2. 週次レビュー
    └── D3. 知識ベース
```

---

## A. ビジョン・企画 (Why / What)

> 「HGK OS とは何か」「なぜ作るのか」を定義する文書群

### A1. ビジョン本体

> `hgk_vision_v4.typos` と `AMBITION.typos` は **canonical ancestors**。
> 新規変換は protocol を通すが、これら自体は置換しない。

| # | ドキュメント | 概要 | AMBITION 対応 |
|:--|:-----------|:-----|:-------------|
| 1 | [AMBITION.typos](AMBITION.typos) | **HGK OS 野望要件定義書**。認知OS の全構想。F1-F10 の9+1機能定義 | 全体 |
| 2 | [hgk_vision_v4.typos](hgk_vision_v4.typos) | HGK 全体ビジョン。7層 × 14 項目の構想 packet 群 | 全体 |
| 3 | [PLUGIN_OS_V1.md](specs/PLUGIN_OS_V1.md) (3.9KB) | Plugin OS v1 設計。L1-L6 の6層アーキテクチャ | F10 |

### A1.5. 変換規則 (Protocol)

> `HGK_NATIVE_SPEC_PROTOCOL_v1.md` は **current canonical transform rule**。

| # | ドキュメント | 概要 |
|:--|:-----------|:-----|
| 4 | [HGK_NATIVE_SPEC_PROTOCOL_v1.md](HGK_NATIVE_SPEC_PROTOCOL_v1.md) | Vision Packet → State Packet → IMPL_SPEC → WORK_ORDER の正規変換 |
| 5 | [templates/](templates/) | VISION / STATE / IMPL_SPEC / WORK_ORDER の最小 template pack |

### A2. 実装仕様 (IMPL_SPEC)

| # | ドキュメント | 概要 | AMBITION 対応 |
|:--|:-----------|:-----|:-------------|
| 6 | [IMPL_SPEC_APP_AGENT.md](specs/IMPL_SPEC_APP_AGENT.md) (23KB) | App Agent 実装仕様。AI Agent 統合の中核 | F4, F6, F9 |
| 7 | [IMPL_SPEC_F1_PHANTAZEIN.md](specs/IMPL_SPEC_F1_PHANTAZEIN.md) (4.6KB) | マザーブレイン実装仕様。常時Boot機構 | F1 |
| 8 | [IMPL_SPEC_F2_SESSION_NOTE.md](specs/IMPL_SPEC_F2_SESSION_NOTE.md) (5.6KB) | セッション=ノート実装仕様 | F2 |
| 9 | [IMPL_SPEC_F5_VIRTUAL_FEED.md](specs/IMPL_SPEC_F5_VIRTUAL_FEED.md) (6.9KB) | 仮想Twitterフィード実装仕様 | F5 |
| 10 | [IMPL_SPEC_F7_3DKB.md](specs/IMPL_SPEC_F7_3DKB.md) (2.1KB) | 3D Knowledge Base 実装仕様 | F7 |

---

## B. 設計・技術 (How)

> 「どう作るか」の技術設計文書群

### B1. アーキテクチャ

| # | ドキュメント | 概要 | AMBITION 対応 |
|:--|:-----------|:-----|:-------------|
| 11 | [SERVER_ARCHITECTURE.md](specs/SERVER_ARCHITECTURE.md) (3.1KB) | サーバーアーキテクチャ設計 | F1, F6, F9 |
| 12 | [ARSENAL.md](ARSENAL.md) (3.7KB) | 技術スタック定義 | 基盤 |

### B2. UI/UX

| # | ドキュメント | 概要 | AMBITION 対応 |
|:--|:-----------|:-----|:-------------|
| 13 | [UI_REQUIREMENTS.md](specs/UI_REQUIREMENTS.md) (4.5KB) | UI 要件定義 | F3, F4, F8 |
| 14 | COWORK_INSTRUCTIONS.md *(→ Archive/ に移動)* | Cowork モード指示書 | F4, F8 |
| 15 | [clawx-design-reference.md](specs/clawx-design-reference.md) (1.4KB) | ClawX デザインリファレンス | F8 |

---

## C. 運用・作業 (Do)

> 「いま何をするか」の作業文書群

### C1. 作業指示書

| # | ドキュメント | 概要 |
|:--|:-----------|:-----|
| 16 | [HGK_APP_WORK_ORDERS.md](specs/HGK_APP_WORK_ORDERS.md) (12KB) | HGK App 開発の作業指示書 |
| 17 | [JULES_BATCH_PROMPTS.md](specs/JULES_BATCH_PROMPTS.md) (4.4KB) | Jules 並列コーディング用プロンプト |
| 18 | [DOCUMENT_GOVERNANCE.md](DOCUMENT_GOVERNANCE.md) | ドキュメント統治ルール |

### C2. 外部分析

| # | ドキュメント | 概要 |
|:--|:-----------|:-----|
| 19 | [OPENCLAW_ANALYSIS.md](../../04_随伴｜OssAdjoint/research/openclaw/OPENCLAW_ANALYSIS.md) (151KB) | OpenClaw ソースコード全分析 (転用計画用) |

---

## D. 記録・記憶 (Was)

> 「何があったか」の記録文書群。パス記法は `30_記憶｜Mneme/` 以降を表示。

### D1. セッションログ (HGK OS 議論を含む)

| # | セッション | パス | 内容 |
|:--|:----------|:-----|:-----|
| 17 | **conv_68** Reviewing HGK OS Vision | [01_記録/b_対話/conv/](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/b_対話｜sessions/conv/2026-02-26_conv_68_Reviewing%20HGK%20OS%20Vision.md) | AMBITION.typos `/dia+` 判定、VISION 拡張 |
| 18 | **conv_47** Reading HGK App Docs | [01_記録/b_対話/conv/](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/b_対話｜sessions/conv/2026-02-26_conv_47_Reading%20HGK%20App%20Docs.md) | F1-F9 精読 |
| 19 | **conv_43** Standalone LS Claude Test | [01_記録/b_対話/conv/](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/b_対話｜sessions/conv/2026-02-26_conv_43_Standalone%20LS%20Claude%20Test.md) | Cowork UI 実装、HGK OS 企画参照 |
| 20 | **conv_76** Refining Dev Environment | [01_記録/b_対話/conv/](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/b_対話｜sessions/conv/2026-02-26_conv_76_Refining%20Development%20Environment.md) | HGK OS UI 全面リデザイン、フライアウトルート遷移 |
| 21 | **conv_33** Synedrion UI | [01_記録/b_対話/conv/](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/b_対話｜sessions/conv/2026-02-28_conv_33_Synedrion%20UI%20Implementation.md) | Core 4 PJ 定義 (Hegemonikón = 認知OS) |
| 22 | **conv_28** FileMaker Workspace | [01_記録/b_対話/conv/](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/b_対話｜sessions/conv/2026-02-09_conv_28_FileMaker%20Workspace%20Setup.md) | HGK = OS = Constitution = Base Table |
| 23 | **conv_38** Dashboard Digest | [01_記録/b_対話/conv/](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/b_対話｜sessions/conv/2026-02-28_conv_38_Dashboard%20Digest%20Widget.md) | 「cognitive operating system」定義 |

### D2. 週次レビュー

| # | レビュー | 内容 |
|:--|:---------|:-----|
| 24 | [weekly_review_2026-02-20.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/e_レビュー｜reviews/weekly_review_2026-02-20.md) | HGK OS 構想+哲学 (3件)、AMBITION.typos 策定記録 |
| 25 | [weekly_review_2026-02-22.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/e_レビュー｜reviews/weekly_review_2026-02-22.md) | HGK OS UI 全面リデザイン記録 |

### D3. 知識ベース

| # | ドキュメント | 内容 |
|:--|:-----------|:-----|
| 26 | [自己分析テキスト(AI用).md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/03_素材｜Materials/a_受信｜incoming/AI用ナレッジベース/自己分析テキスト(AI用).md) | Creator の「認知OS」「行動原理」「AuDHD特性」定義 |
| 27 | [eat_20260219_periskope_deep_research...md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/03_素材｜Materials/b_処理済｜processed/eat_20260219_periskope_deep_research_system_architecture_how_t.md) | Deep Research: HGK OS アーキテクチャ調査 |

---

## AMBITION 機能 × ドキュメント クロスリファレンス

| 機能 | ビジョン (A) | 設計 (B) | 運用 (C) | 記録 (D) |
|:-----|:-----------|:---------|:---------|:---------|
| **F1** マザーブレイン | `AMBITION.typos`, `IMPL_SPEC_F1_PHANTAZEIN.md` | `SERVER_ARCHITECTURE.md` | — | `conv_47`, `conv_38` |
| **F2** セッション=ノート | `AMBITION.typos`, `IMPL_SPEC_F2_SESSION_NOTE.md` | — | — | `conv_47` |
| **F3** タブ・マルチタスク | `AMBITION.typos` | `UI_REQUIREMENTS.md` | — | — |
| **F4** AI指揮台+Cowork | `AMBITION.typos`, `hgk_vision_v4.typos`, `IMPL_SPEC_APP_AGENT.md` | `UI_REQUIREMENTS.md`, `COWORK_INSTRUCTIONS.md`, `clawx-design-reference.md` | `HGK_APP_WORK_ORDERS.md` | `conv_43`, `conv_76` |
| **F5** 仮想Feed | `AMBITION.typos`, `IMPL_SPEC_F5_VIRTUAL_FEED.md` | — | — | `eat_20260219_periskope_deep_research...md` |
| **F6** 認知コロニー ✅ | `AMBITION.typos`, `IMPL_SPEC_APP_AGENT.md` | `SERVER_ARCHITECTURE.md` | `HGK_APP_WORK_ORDERS.md` | `conv_33` |
| **F7** 3DKB | `AMBITION.typos`, `IMPL_SPEC_F7_3DKB.md` | — | — | — |
| **F8** Cowork UI | `AMBITION.typos` | `UI_REQUIREMENTS.md`, `COWORK_INSTRUCTIONS.md`, `clawx-design-reference.md` | `HGK_APP_WORK_ORDERS.md` | `conv_76`, `weekly_review_2026-02-20.md`, `weekly_review_2026-02-22.md` |
| **F9** 並列実行基盤 | `AMBITION.typos`, `IMPL_SPEC_APP_AGENT.md` | `SERVER_ARCHITECTURE.md` | `HGK_APP_WORK_ORDERS.md`, `JULES_BATCH_PROMPTS.md` | — |
| **F10** Plugin OS | `AMBITION.typos`, `hgk_vision_v4.typos`, `PLUGIN_OS_V1.md` | — | `OPENCLAW_ANALYSIS.md` | — |
| 基盤 (横断) | `HGK_NATIVE_SPEC_PROTOCOL_v1.md`, `templates/` | `ARSENAL.md` | `DOCUMENT_GOVERNANCE.md` | `conv_28`, `conv_38`, `自己分析テキスト(AI用).md`, `eat_20260219_periskope_deep_research...md` |

---

## 未カバー領域 (Gap 分析)

| AMBITION 機能 | IMPL_SPEC | Gap |
|:-------------|:----------|:----|
| F1 マザーブレイン | ✅ あり | — |
| F2 セッション=ノート | ✅ あり | — |
| F3 タブ・マルチタスク | ❌ なし | IMPL_SPEC_F3 未作成 |
| F4 AI指揮台+Cowork | ✅ APP_AGENT | — |
| F5 仮想Feed | ✅ あり | — |
| F6 認知コロニー | ✅ APP_AGENT | MVP 済 |
| F7 3DKB | ✅ あり | — |
| F8 Cowork UI | ❌ なし | IMPL_SPEC_F8 未作成 (UI_REQUIREMENTS がカバー?) |
| F9 並列実行基盤 | ❌ なし | IMPL_SPEC_F9 未作成 (APP_AGENT がカバー?) |
| F10 Plugin OS | ✅ あり | [IMPL_SPEC_F10](specs/IMPL_SPEC_F10_PLUGIN_OS.md) + [PLUGIN_OS_V1](specs/PLUGIN_OS_V1.md) |

---

## Protocol Note

- 新規 Medium+ change は `HGK_NATIVE_SPEC_PROTOCOL_v1.md` を通す
- `hgk_vision_v4.typos` と `AMBITION.typos` は canonical ancestors
- 既存 `IMPL_SPEC` 群は reader-facing artifact として維持し、一括改修はしない

---

*Index v1.2 — 2026-04-17 (protocol + template pack + `.typos` 正本表記に更新)*
