---
description: WF スケジュール仕様 — frontmatter の schedule メタデータ
version: "1.0"
origin: "@chew 消化 B2 — Devin Scheduled Devins からの射"
---

# WF Schedule Specification v1.0

> **目的**: ワークフローの定期実行スケジュールを frontmatter で宣言する
> **射の種類**: 部分射 (Devin Scheduled Devins → HGK WF 体系)
> **起源**: chew_report.md.resolved の /eat 消化 — 優先度 B2

---

## 仕様

WF の frontmatter に `schedule` キーを追加可能。n8n や cron との連携を想定。

### frontmatter 構文

```yaml
---
description: 日次レビューワークフロー
schedule:
  enabled: true           # スケジュール有効化
  cron: "0 9 * * *"       # cron 式 (毎日 9:00)
  timezone: "Asia/Tokyo"  # タイムゾーン (IANA)
  trigger: "n8n"          # 実行トリガー (n8n | cron | manual)
  last_run: ""            # 最終実行日時 (ISO 8601)
  next_run: ""            # 次回実行予定 (自動計算)
---
```

### フィールド定義

| フィールド | 型 | 必須 | デフォルト | 説明 |
|:----------|:---|:-----|:----------|:-----|
| `enabled` | bool | ✅ | `false` | スケジュールの有効/無効 |
| `cron` | string | ✅ | — | cron 式 (5フィールド standard cron) |
| `timezone` | string | ❌ | `"Asia/Tokyo"` | IANA タイムゾーン |
| `trigger` | string | ❌ | `"manual"` | `n8n` \| `cron` \| `manual` |
| `last_run` | string | ❌ | `""` | ISO 8601 形式の最終実行日時 |
| `next_run` | string | ❌ | `""` | ISO 8601 形式の次回実行予定 |

### 使用例

```yaml
---
description: Gnōsis 論文の定期消化
schedule:
  enabled: true
  cron: "0 6 * * 1"      # 毎週月曜 6:00
  timezone: "Asia/Tokyo"
  trigger: "n8n"
---
```

### 対応 WF 候補

| WF | スケジュール案 | 理由 |
|:---|:-------------|:-----|
| `/boot` | 不要 | セッション開始時のみ |
| Digestor `/eat` | `0 6 * * 1` (週次) | 論文の定期消化 |
| Basanos scan | `0 0 * * *` (日次) | コード品質の継続監視 |
| Gnōsis 更新 | `0 3 * * 0` (週次) | 知識ベースの定期更新 |

---

## 実装ロードマップ

1. **Phase 1** (現在): frontmatter に `schedule` キーの仕様を定義 ← **ここ**
2. **Phase 2**: `expander.py` が `schedule` を認識してメタデータとして保存
3. **Phase 3**: n8n webhook → `hermeneus_run` の連携パイプライン

---

*v1.0 — @chew 消化 B2 (2026-03-01)*
