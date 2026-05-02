# /bou.prd — FM-Agent Objective + OKR

> 実行日: 2026-03-09
> WF: `/bou.prd` (Objective + SMART OKR + 戦略整合)
> 入力元: ← `/noe.prd` (PRD-FM-Agent-noe.md)
> 接続先: → `/zet.prd`

---

## Objective

> **FM-Agent** (VLM ベース GUI 自動化エージェント) によって、
> FileMaker Pro のスクリプト配備・レイアウト検証・テスト実行を
> **End-to-End で自動化** し、手作業への依存を構造的に排除する。

## Key Results (SMART OKR)

| # | Key Result | Specific | Measurable | Time-bound |
|:--|:-----------|:---------|:-----------|:-----------|
| KR1 | XML スクリプトの自動貼付 | Forge 生成 XML をクリップボード経由で FM に自動配備 | 成功率 ≥ 90% (10回中9回) | 2026-04-30 |
| KR2 | レイアウト検証の自動化 | VLM がスクリーンショットからフィールド配置を検出し、DDR と照合 | 検出精度 ≥ 85% | 2026-05-31 |
| KR3 | テストシナリオの自動実行 | ポータルフィルタ・検索条件・ソートの E2E テスト | 自動化対象 ≥ 5 シナリオ | 2026-05-31 |

## Achievable (リソース制約)

| リソース | 状態 |
|:---------|:-----|
| Windows VM (QEMU/KVM) | 自動構築スクリプト作成済。unattended install 対応 |
| Bytebot VLM | 検証済み (AT-SPI 不可→VLM パス確定) |
| FM Pro ライセンス | あり (社長の会社) |
| Creator の工数 | 本業 (FM 受託) と並行。週 5-10h 程度 |

## Relevant (Problem Statement との整合)

| noe.prd の課題 | bou.prd の対応 |
|:---------------|:---------------|
| FM Pro に CLI/API がない | → VLM で GUI を API 化する (KR1) |
| レイアウト変更の検証漏れ | → VLM + DDR 照合で自動検知 (KR2) |
| テスト自動化できない | → E2E テストシナリオ自動実行 (KR3) |
| 手順書が属人的 | → 自動化ワークフローとして形式化 (全KR共通) |

## 非目的 (含まないもの)

- FM Data API (REST) の改善 — 既に別途対応
- FM のスクリプト生成ロジック — Forge が担当
- FM のデータベース設計の自動化 — 手動のまま (スコープ外)
- macOS 対応 — 将来構想 (Phase 2 以降)

## 戦略整合チェック

| 上位目標 | FM-Agent の貢献 |
|:---------|:----------------|
| HGK Ergon (能動状態) | FM-Agent は HGK の「外界に作用する手足」の具体的実装 |
| 社長の会社の生産性 | FM 受託案件の配備・検証・テスト工数を 50%+ 削減 |
| Creator の独立性 | FM 操作の属人性排除 → Creator なしでも案件を進められる基盤 |

| 項目 | 内容 |
|:-----|:-----|
| Objective | FM-Agent (VLM ベース GUI 自動化) で FM Pro の配備・検証・テストを End-to-End 自動化 |
| Key Result 1 | XML スクリプト自動貼付 成功率 ≥ 90% (2026-04-30) |
| Key Result 2 | レイアウト検証 VLM 検出精度 ≥ 85% (2026-05-31) |
| Key Result 3 | E2E テスト自動化 ≥ 5 シナリオ (2026-05-31) |
| 非目的 | Data API / スクリプト生成 / DB 設計 / macOS |
| 戦略整合 | HGK Ergon + 社長の会社の生産性 + Creator の独立性 |
| 接続先 | → `/zet.prd` (市場探索) |
