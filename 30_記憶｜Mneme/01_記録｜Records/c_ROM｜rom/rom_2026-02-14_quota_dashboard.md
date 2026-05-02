---
rom_id: rom_2026-02-14_quota_dashboard
session_id: c4086669-3f88-4c1d-a943-9570573dc11b
created_at: 2026-02-14 18:17
rom_type: rag_optimized
reliability: High
topics: [quota, dashboard, desktop-app, api, agq-check, context-rot, language-server]
exec_summary: |
  Language Server Quota 情報を Desktop App ダッシュボードに表示するカードを実装。
  Python API (/api/quota) + Frontend UI (renderQuotaCard) + CSS の 5 ファイル変更。
  LS 未起動時のグレースフルな エラーハンドリングも検証済み。
search_expansion:
  synonyms: [quota-card, agq, prompt-credits, flow-credits, tier-alert, turtle-mode]
  concepts: [BC-18, Context-Rot, polling, tiered-alert, progress-bar]
---

# Quota ダッシュボード実装 {#sec_01_quota_dashboard .desktop .api .frontend}

> **[DECISION]** Desktop App ダッシュボードに Quota カードを追加。Kalon カードの直下、Health Items の直上に配置。

> **[DECISION]** API ポートは `9696` (`mekhane.api.DEFAULT_PORT`)。Frontend の `API_BASE` は `http://127.0.0.1:9696`。

> **[DECISION]** エラーハンドリング: LS 未起動時は `overall_status: "unknown"` + `error` メッセージを返し、UI 側は赤文字で「Quota 情報取得不可」を表示。

## アーキテクチャ {#sec_02_architecture .data-flow}

> **[FACT]** データフロー: `agq-check.sh --json` → Python API (`/api/quota`) → Frontend (`api.quota()`) → `renderQuotaCard()`

```
agq-check.sh --json
  ↓ subprocess (asyncio.to_thread)
routes/quota.py (/api/quota)
  ↓ JSON response
client.ts api.quota()
  ↓ QuotaResponse
main.ts renderQuotaCard()
  ↓ HTML
Dashboard Card (⚡ Quota)
```

## 変更ファイル {#sec_03_files .implementation}

> **[FACT]** 5 ファイルを変更・新規作成

| ファイル | 種別 | 行数 | 内容 |
|:---------|:-----|:-----|:-----|
| `mekhane/api/routes/quota.py` | NEW | ~179 | Python API エンドポイント |
| `mekhane/api/server.py` | MOD | +8 | ルータ登録 (遅延ロード) |
| `hgk/src/api/client.ts` | MOD | +27 | 型定義 (QuotaModel/Credits/Response) + api.quota() |
| `hgk/src/main.ts` | MOD | +67 | renderQuotaCard() 関数 |
| `hgk/src/styles.css` | MOD | +110 | Quota カード CSS |

## UI 構成 {#sec_04_ui .design}

> **[RULE]** 4段階アラート: green (🟢 ≥75%) → yellow (🟡 ≥50%) → orange (🟠 ≥25%) → red (🔴 <25%)

```
┌─ ⚡ Quota ────────────── Max Plan ─┐
│ 🟢 Claude Sonnet 4        92%     │
│ █████████████████████░░░░  ↻ 13:00 │
│ 🟡 Claude Opus 4          38%     │
│ █████████░░░░░░░░░░░░░░░  ↻ 13:00 │
│───────────────────────────────────│
│ 💳 Prompt: 450/500  🌊 Flow: 180/200│
└───────────────────────────────────┘
```

> **[RULE]** orange/red 時はアラートバナーを表示: 「🟠 Quota 残量低下」or「🔴 Quota 残量危険 — Turtle Mode 推奨」

## 発見事項 {#sec_05_discoveries .debugging}

> **[DISCOVERY]** `agq-check.sh` は Language Server プロセスを `pgrep -f` で直接検索する。IDE 外部環境 (CLI/API サーバー単体起動) からはプロセスが検出できないため、常にエラーを返す。

> **[DISCOVERY]** API サーバーは既にバックグラウンドで port 9696 稼働中だった（Errno 98: Address already in use で発覚）。起動元を特定する必要がある場合は `ss -tlnp | grep 9696` で確認可能。

## Lint 注記 {#sec_06_lint .maintenance}

> **[CONTEXT]** `quota.py` の Pyre2 lint (fastapi/pydantic import 未解決、unexpected keyword argument) は全て IDE の venv パス問題。他の全ルートファイル (status.py, gnosis.py 等) にも同一パターンが存在。**機能影響なし**。

## ユーザー追加 diff {#sec_07_user_diff .context}

> **[CONTEXT]** ユーザーが手動で `renderDigestCard()` 関数を `main.ts` に追加 (Quota カード実装と同時)。消化候補表示カードで `/ccl-read` の消化結果を Dashboard に表示する機能。`DigestReport`, `DigestCandidate` 型を使用。

## 関連情報 {#sec_08_related}

- 関連 WF: `/ene+` (実装実行)
- 関連 BC: BC-18 (Context Rot), BC-6 (確信度明示)
- 関連 Script: `~/oikos/hegemonikon/scripts/agq-check.sh`
- 関連 Skill: Code Protocols
- 前回セッション: 設計ドキュメント作成 + Python API 実装

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "Quota ダッシュボードの実装方法"
  - "Desktop App に新しいカードを追加する方法"
  - "agq-check.sh の動作仕様"
  - "API エンドポイントの追加方法 (FastAPI + Tauri)"
  - "段階的アラートの閾値設計"
answer_strategy: "ファイル変更リスト (sec_03) を起点に、各コンポーネントの実装詳細を参照。UI デザインは sec_04、データフローは sec_02 を参照。"
confidence_notes: "ビルド検証 + curl + Desktop App 表示確認済み。LS 連携の正常パスは未検証 (LS プロセス不在のため)。"
related_roms: []
-->
