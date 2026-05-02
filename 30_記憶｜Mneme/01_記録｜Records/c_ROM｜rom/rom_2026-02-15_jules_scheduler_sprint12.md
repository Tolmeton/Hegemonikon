---
rom_id: rom_2026-02-15_jules_scheduler_sprint12
session_id: a755c082-452d-407d-bf04-6e485389f782
created_at: "2026-02-15 17:00"
rom_type: rag_optimized
reliability: High
topics: [jules, scheduler, basanos, dashboard, sparkline, specialist-analyzer, api, trend, feedback]
exec_summary: |
  Jules×Basanos統合のSprint 1（基盤整備: ログ標準化・失敗通知・自動削除）と
  Sprint 2（可視化: Specialist分析・Trend API・SVGスパークライン）を完了。
  全テスト228 passed、TSビルド0 errors。Sprint 3-4（自律淘汰・自動生成）が残る。
search_extensions:
  synonyms: [Jules pipeline, daily cron, perspective ranking, success rate, trend chart]
  abbreviations: [API, SVG, CLI, TS, FeedbackStore]
  related_concepts: [basanos_feedback, specialist_mode, hybrid_mode, perspective_usefulness]
---

# Jules Scheduler Sprint 1-2 完了 {#sec_01_overview .sprint .scheduler}

> **[DECISION]** Sprint 方式（4段階: 基盤→可視化→自律淘汰→自律進化）で段階的実装を選択

## Sprint 1: 基盤整備 {#sec_02_sprint1 .infrastructure}

> **[DECISION]** ログ形式に新旧互換フォールバック戦略を採用。古いログも API が正しく解析

### NEW-1: ログ形式標準化 {#sec_02a_log_format}

> **[FACT]** `jules_daily_scheduler.py` (L664-673) にトップレベルキー追加:
> `total_tasks`, `total_started`, `total_failed`, `files_reviewed`, `dynamic`

> **[RULE]** API 側 (`routes/scheduler.py` L57-68) で旧フォーマット (result.metadata 内) と
> 新フォーマット (トップレベル) の両方を透過的に処理するフォールバックロジック

### F13: Cron 失敗通知 {#sec_02b_cron_notification}

> **[FACT]** `jules_cron.sh` (L69-76): EXIT_CODE != 0 時に Sympatheia API で CRITICAL 通知送信

### N4: ログ自動削除 {#sec_02c_log_cleanup}

> **[FACT]** `jules_cron.sh` (L47-49): 30日超の古いログを `find -mtime +30 -delete`

### テスト {#sec_02d_tests}

> **[FACT]** `test_scheduler_api.py`: 10テスト全pass
> カバー: no_data, 旧/新フォーマット, 成功率計算, status判定, limit, モード集計, 壊れログスキップ

---

## Sprint 2: 可視化 {#sec_03_sprint2 .visualization}

### F12: Specialist 効果分析 {#sec_03a_specialist_analyzer}

> **[DISCOVERY]** Perspective 有用率は 3軸で集計可能: perspective 個別 / domain 別 / axis 別

> **[FACT]** `specialist_analyzer.py`:
> - `rank_perspectives()`: 有用率降順ランキング（10回以上使用のみ）
> - `aggregate_by_domain()` / `aggregate_by_axis()`: 集計関数
> - `full_analysis()`: JSON 出力用。API から直接呼出し可能
> - CLI: `rank`, `domain`, `axis`, `json` コマンド

### API エンドポイント {#sec_03b_api_endpoints}

> **[FACT]** `/scheduler/trend` (GET, ?days=14):
> 日別成功率推移。計算式 = `(started - failed) / started × 100`
> レスポンス: `{ trend: [{date, success_rate, runs, started, failed}], days }`

> **[FACT]** `/scheduler/analysis` (GET):
> FeedbackStore からランキング + domain/axis 集計。
> レスポンス: `{ ranking, by_domain, by_axis, low_quality_ids, total_perspectives }`

### TypeScript 統合 {#sec_03c_typescript}

> **[DECISION]** SVG スパークラインで可視化（Canvas/外部ライブラリ不使用）

> **[FACT]** `client.ts` に 6 interfaces 追加:
> `SchedulerTrendPoint`, `SchedulerTrendResponse`,
> `PerspectiveRank`, `DomainAggregate`, `AxisAggregate`, `SchedulerAnalysisResponse`

> **[FACT]** `dashboard.ts`:
> - `renderSparkline()`: SVG パス描画 + 90% 閾値ライン（破線）
> - `renderSchedulerCard()` に trend データ表示を統合
> - Promise.all に `schedulerTrend(14)` 追加

---

## 検証結果 {#sec_04_verification .quality}

> **[FACT]** Python: 228 passed, 4 skipped (全テストスイート)
> **[FACT]** TypeScript: `tsc --noEmit` 0 errors

---

## 未実装 (Sprint 3-4) {#sec_05_remaining .roadmap}

> **[CONTEXT]** Sprint 3 (F14): Feedback に基づく Perspective 自動淘汰
> **[CONTEXT]** Sprint 4 (F15/F16): Specialist 自動生成 + 適応的曜日ローテーション

---

## 変更ファイル一覧 {#sec_06_files .reference}

| ファイル | 変更種別 | 概要 |
|:---------|:---------|:-----|
| `mekhane/symploke/jules_daily_scheduler.py` | MODIFY | トップレベルキー追加 |
| `mekhane/api/routes/scheduler.py` | MODIFY | trend/analysis エンドポイント + フォールバック |
| `mekhane/symploke/jules_cron.sh` | MODIFY | 失敗通知 + ログ削除 |
| `mekhane/symploke/specialist_analyzer.py` | NEW | Perspective 効果分析 CLI |
| `mekhane/symploke/tests/test_scheduler_api.py` | NEW | API 10テスト |
| `hgk/src/api/client.ts` | MODIFY | 6 interfaces + 2 API メソッド |
| `hgk/src/views/dashboard.ts` | MODIFY | sparkline + trend 取得 |

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "Jules schedulerの成功率は？"
  - "Specialist分析どうなってる？"
  - "ダッシュボードのトレンド表示の仕組みは？"
  - "Sprint 3-4 の残タスクは？"
  - "ログ形式の互換性はどう担保されてる？"
answer_strategy: "このROMはJulesスケジューラーの拡張実装の全体像。具体的な実装はファイル参照。認知判断は含まない。"
confidence_notes: "全て実装・検証済み。テスト + ビルド通過。Source: view_file + pytest + tsc"
related_roms: []
-->
