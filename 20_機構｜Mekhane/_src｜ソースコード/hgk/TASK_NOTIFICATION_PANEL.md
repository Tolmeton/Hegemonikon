# Task: 通知パネル UI 実装

> **担当**: Jules (Gemini Code Assist)
> **リポジトリ**: `Tolmeton/Hegemonikon`
> **関連ファイル**: `hgk/src/`

## 目的

Sympatheia 自律神経系からの通知を表示するパネルを HGK Desktop App に追加する。
バックエンド API（`GET /api/sympatheia/notifications`）は実装済み。

## API 仕様

### `GET /api/sympatheia/notifications`

| パラメータ | 型 | デフォルト | 説明 |
|:-----------|:---|:-----------|:-----|
| `limit` | int | 50 | 最大件数 (1-500) |
| `since` | string? | null | ISO8601 タイムスタンプフィルタ |
| `level` | string? | null | `INFO` / `HIGH` / `CRITICAL` |

**レスポンス** (配列、最新順):

```json
[
  {
    "id": "2a51782e",
    "timestamp": "2026-02-09T14:00:00+00:00",
    "source": "WF-09",
    "level": "CRITICAL",
    "title": "🚨 WBC: CRITICAL threat detected",
    "body": "Source: claude-test\nScore: 26/15\nFiles: SACRED_TRUTH.md",
    "data": { "threatScore": 26, "files": ["SACRED_TRUTH.md"] }
  }
]
```

## 実装手順

### 1. `client.ts` に API メソッド追加

```typescript
// --- Notification Types ---
export interface Notification {
    id: string;
    timestamp: string;
    source: string;
    level: 'INFO' | 'HIGH' | 'CRITICAL';
    title: string;
    body: string;
    data: Record<string, unknown>;
}

// api オブジェクトに追加:
notifications: (limit = 50, level?: string) =>
    apiFetch<Notification[]>(
        `/api/sympatheia/notifications?limit=${limit}${level ? `&level=${level}` : ''}`
    ),
```

### 2. `main.ts` にルート追加

```typescript
// routes に追加
'notifications': renderNotifications,

// index.html nav に追加
<button data-route="notifications">🔔 Notifications</button>
```

### 3. `renderNotifications()` ビュー関数

以下の要素を含むビューを実装:

1. **ヘッダー**: `<h1>🔔 Notifications</h1>` + リフレッシュボタン + levelフィルターセレクト
2. **通知カード一覧**: 各通知を `.card` で表示
   - level に応じた左ボーダー色:
     - `CRITICAL`: `var(--error-color)` (赤)
     - `HIGH`: `var(--warning-color)` (黄)
     - `INFO`: `var(--primary-color)` (青)
   - `.source` バッジ（例: `WF-09`）
   - `.title` (太字)
   - `.body` (プリフォーマット、`white-space: pre-line`)
   - `.timestamp` (相対時間表示: "3分前", "2時間前")
3. **空状態**: `通知はありません` メッセージ
4. **ポーリング**: 30秒間隔で自動更新（既存の `startPolling` を使用）

### 4. CSS 追加 (`styles.css`)

```css
/* Notification cards */
.notif-card {
  border-left: 3px solid var(--primary-color);
}

.notif-card.level-critical {
  border-left-color: var(--error-color);
}

.notif-card.level-high {
  border-left-color: var(--warning-color);
}

.notif-source {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 600;
  background: var(--border-color);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  margin-right: 0.5rem;
}

.notif-time {
  color: #8b949e;
  font-size: 0.8rem;
}

.notif-body {
  font-size: 0.85rem;
  white-space: pre-line;
  margin-top: 0.25rem;
  color: #8b949e;
}
```

## 既存パターンへの準拠

| 項目 | 既存パターン | 場所 |
|:-----|:-------------|:-----|
| API 呼び出し | `api.xxx()` | `client.ts` L41-77 |
| HTML エスケープ | `esc()` | `main.ts` L17-25 |
| ポーリング | `startPolling(fn, 30000)` | `main.ts` L36-39 |
| カードスタイル | `.card` | `styles.css` L81-92 |
| バッジ | `.poll-badge` | `styles.css` L110-117 |
| ビュー関数 | `async function renderXxx()` | `main.ts` の各セクション |

## 注意

- `api-types.ts` は OpenAPI 生成型。通知は手動型定義でOK（`Notification` interface）
- body 内の改行 `\n` を `pre-line` で表示
- 相対時間は `Intl.RelativeTimeFormat` または簡易実装で
- level フィルタは `<select class="input">` で実装
