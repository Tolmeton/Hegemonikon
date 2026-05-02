# IMPL_SPEC: F1 — マザーブレイン（常時 Boot 機構）

> **AMBITION 要件**: ダッシュボードを常時 Boot 機構にする。Push 型ナレーター。
> **ステータス**: 🟠 バックエンド実装済み / フロントエンド未接続

---

## 1. 概要

マザーブレインは HGK APP の常駐プロセスとして、セッション・ハンドオフ・KI を一元管理する。
既存 `boot_integration.py` (919行) が 13 軸の Boot コンテキスト統合 API を持っており、
**フロントエンドとの接続と Push 型 UI の実装が主タスク**。

## 2. 既存バックエンド（接続先）

| コンポーネント | パス | 主要 API |
|:-------------|:-----|:---------|
| Boot Integration | `mekhane/symploke/boot_integration.py` | `get_boot_context(mode, context)` |
| Boot Axes | `mekhane/symploke/boot_axes.py` | 12 軸ローダー (Handoff, KI, PKS 等) |
| API Route | `mekhane/api/routes/symploke.py` L166 | `GET /api/symploke/boot` |
| Template | `boot_integration.py` L587 | `generate_boot_template(result)` |
| Postcheck | `boot_integration.py` L728 | `postcheck_boot_report(path, mode)` |

## 3. API 仕様

### 既存 (稼働中)

| Method | Path | 説明 |
|:-------|:-----|:-----|
| GET | `/api/symploke/boot?mode=standard` | Boot コンテキスト取得 |

### 新規 (実装が必要)

| Method | Path | 説明 |
|:-------|:-----|:-----|
| GET | `/api/phantazein/status` | 常駐状態の取得 (boot 済みか、最終更新日時) |
| GET | `/api/phantazein/narrate/{section}` | セクション別の Push ナレーション取得 |
| POST | `/api/phantazein/refresh` | Boot コンテキストの再構築 |
| WS | `/ws/phantazein` | リアルタイム状態更新 (WebSocket) |

### `/api/phantazein/narrate/{section}` レスポンス例

```json
{
  "section": "handoff",
  "narration": "前回のセッション (2h前) では HGK APP の UI ブロッカーに取り組みました。...",
  "urgency": "medium",
  "action_suggestions": [
    {"label": "続きを実行", "ccl": "/ene+"},
    {"label": "進捗確認", "ccl": "/now"}
  ]
}
```

## 4. データモデル

```typescript
// 既存 boot_integration の返却を型付け
interface BootContext {
  handoffs: HandoffSummary[];
  sophia_kis: KISummary[];
  projects: ProjectStatus[];
  health: HealthScore;
  pks: PKSSummary;
  formatted: string;         // テンプレート済みテキスト
}

interface NarrationItem {
  section: string;           // 'handoff' | 'projects' | 'health' | 'pks' | ...
  narration: string;         // LLM 生成の語りかけテキスト
  urgency: 'low' | 'medium' | 'high' | 'critical';
  actionSuggestions: ActionCard[];
}

interface ActionCard {
  label: string;
  ccl: string;               // 実行可能な CCL 式
  icon?: string;
}
```

## 5. フロントエンド実装ステップ

### Phase 1: Boot 状態の可視化（既存 API 接続）

| Step | 内容 | ファイル |
|:-----|:-----|:---------|
| 1-1 | `client.ts` に `getBootContext()` メソッド追加 | `src/api/client.ts` |
| 1-2 | Dashboard の各カードを BootContext 型でリファクタ | `src/views/dashboard.ts` |
| 1-3 | 「最終 Boot 日時」バッジ表示 | `src/views/dashboard.ts` |

### Phase 2: Push 型ナレーション UI

| Step | 内容 | ファイル |
|:-----|:-----|:---------|
| 2-1 | Narration コンポーネント作成 (クリックで語りかけ) | `src/components/narration-card.ts` [NEW] |
| 2-2 | バックエンド `/api/phantazein/narrate` 実装 | `mekhane/api/routes/phantazein.py` [NEW] |
| 2-3 | Dashboard カードに Narration トリガー追加 | `src/views/dashboard.ts` |

### Phase 3: 常駐化 (WebSocket)

| Step | 内容 | ファイル |
|:-----|:-----|:---------|
| 3-1 | WebSocket エンドポイント追加 | `mekhane/api/routes/phantazein.py` |
| 3-2 | クライアント側 WS 接続管理 | `src/api/phantazein-ws.ts` [NEW] |
| 3-3 | リアルタイムステータスバー | `src/components/status-bar.ts` [NEW] |

## 6. テスト戦略

| テスト種別 | 内容 |
|:----------|:-----|
| 単体テスト | `test_boot_integration.py` を拡張 (narrate endpoint) |
| E2E | Dashboard 表示 → Narration クリック → アクション提案表示 |
| 非機能 | Boot コンテキスト取得 < 3秒 (13軸並列) |

## 7. 依存関係

- `mekhane/symploke/boot_integration.py` ← 13軸 Boot API (実装済み ✅)
- `mekhane/api/routes/symploke.py` ← Boot API ルート (実装済み ✅)
- Ochema Cortex API ← LLM ナレーション生成
- Kairos / Mneme / Sophia ← データソース (実装済み ✅)
