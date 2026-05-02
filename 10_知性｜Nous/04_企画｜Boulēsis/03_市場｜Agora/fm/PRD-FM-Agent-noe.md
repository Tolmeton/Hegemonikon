# /noe.prd — FM-Agent Problem Statement

> 実行日: 2026-03-09
> WF: `/noe.prd` (Phase 1-3)
> 接続先: → `/bou.prd`

---

## Phase 1 (η): 問題の構造化

### 誰が困っているか

- **Creator (エンジニア)**: FileMaker の GUI 操作を手作業で行っている。スクリプト貼付け、フィールド配置確認、レイアウト検証など。
- **社長の会社 (FM 受託開発)**: 大学病院向け FileMaker 案件で、Excel → FM マッピング、スクリプト配備、テスト実行を属人的に行っている。
- **社長**: Creator が作業した結果を顧客 (大学病院) に説明する立場。作業の品質・進捗の可視化が不足。

### 何に困っているか

- FileMaker Pro は **API / CLI を持たない** (唯一の操作インターフェースは GUI)
- XML でスクリプトを生成しても、**貼付は手作業** (クリップボード → FM Inspector)
- レイアウト検証、ポータルフィルタ確認、フィールド配置照合は **目視に依存**
- テスト自動化ができない → **リグレッション検出が困難**

### なぜ困っているか (根本原因 vs 症状)

| 症状 | 根本原因 |
|:-----|:---------|
| XML 貼付が手作業 | FM Pro に CLI/API がない (プラットフォーム制約) |
| レイアウト変更の検証漏れ | GUI 状態の自動取得手段がない |
| 手順書が属人的 | 操作手順が暗黙知のまま |
| テスト自動化できない | FileMaker のアサーション機構が存在しない |

---

## Phase 2 (μ): 問題の精錬

### Problem Statement

> **FileMaker Pro で受託開発を行うエンジニア** は、
> **FM Pro が GUI 以外の操作インターフェースを持たない** という制約において、
> **スクリプト配備・レイアウト検証・テスト実行の全工程が手作業に依存している** という課題に直面している。

### Background (問題の歴史・経緯)

- FileMaker Pro は 1987 年から続くレガシープラットフォーム。API は近年 Data API (REST) が追加されたが、**GUI 操作の自動化 API は存在しない**
- Claris (Apple 子会社) は開発環境の近代化を優先していない
- HGK プロジェクトでは Forge エンジン (XML 生成) で「生成」は自動化済みだが、「配備」「検証」は手動のまま
- 2026-01 に AT-SPI (Linux アクセシビリティ) による自動化を検討 → Wine 上の FM は AT-SPI 非対応 → Bytebot (VLM ベース) パスに方向転換
- 2026-03 に Windows VM の自動構築を着手 (unattended install)

### Context (現在の変化要因)

- **VLM の成熟**: Bytebot (vision-language model) による GUI 操作が実用段階に
- **Desktop Agent の潮流**: Claude Computer Use, Anthropic Desktop Agent 等が登場
- **案件の拡大**: 大学病院の案件が複数テーブル・複数レイアウトに拡大 → 手作業の限界
- **Windows VM**: QEMU/KVM + unattended install で FM Pro の実行環境が自動構築可能に

### 問題の境界

| 含むもの | 含まないもの |
|:---------|:-------------|
| FM Pro の GUI 操作自動化 | FM Data API (REST) — 既に別途対応 |
| スクリプト XML の自動貼付 | FM のスクリプト生成 — Forge が担当 |
| レイアウト検証の自動化 | FM のデータベース設計 — 手動のまま |
| テスト自動化 (アサーション) | FM ユーザー教育 — スコープ外 |
| Windows VM 上での FM 操作 | macOS 対応 — 将来構想 |

---

## Phase 3 (T(X)): 接続テスト

**「この問題記述で目的を定義できるか？」**

→ ✅ 定義可能。Problem Statement から以下の目的が自然に導出される:
1. FM Pro の GUI 操作を自動化するエージェントの構築
2. スクリプト配備・検証・テストの End-to-End 自動化
3. 手作業の属人性を排除し、再現可能なワークフローに転換

| 項目 | 内容 |
|:-----|:-----|
| Problem Statement | FileMaker Pro で受託開発を行うエンジニアは、FM Pro が GUI 以外の操作インターフェースを持たないという制約において、スクリプト配備・レイアウト検証・テスト実行の全工程が手作業に依存しているという課題に直面している |
| Background | FM Pro は API/CLI を持たないレガシープラットフォーム。Forge で生成は自動化済みだが配備・検証は手動。AT-SPI 不可→Bytebot VLM パスに方向転換 |
| Context | VLM 成熟 + Desktop Agent 潮流 + 案件拡大 + Windows VM 自動構築が変化要因 |
| 問題の境界 | 含む: GUI 自動化/XML 貼付/レイアウト検証/テスト自動化。含まない: Data API/スクリプト生成/DB 設計/ユーザー教育 |
| 接続先 | → `/bou.prd` (目的定義) |
