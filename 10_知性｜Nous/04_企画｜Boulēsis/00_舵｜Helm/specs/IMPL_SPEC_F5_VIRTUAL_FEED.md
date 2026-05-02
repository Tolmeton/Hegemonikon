# IMPL_SPEC: F5 — 仮想 Twitter フィード（プッシュ型情報共有）

> **AMBITION 要件**: 仮想インフルエンサーが私向けの最新情報をポスト。いいね学習 + コメント + フォローアップリサーチ。
> **ステータス**: 🟡 バックエンド萌芽あり (SelfAdvocate) / フロントエンド・API ルート未実装

---

## 1. 概要

論文や KI がプロアクティブに情報を提示する仮想 Twitter フィード。
**`SelfAdvocate` (242行) が論文一人称メッセージ生成の核を持っているが、
フィード生成ループ・いいね学習・フォローアップリサーチは未実装**。

## 2. 既存バックエンド（接続先）

| コンポーネント | パス | 主要 API | 状態 |
|:-------------|:-----|:---------|:-----|
| SelfAdvocate | `mekhane/pks/self_advocate.py` (242行) | `generate(nugget, context)`, `generate_batch()`, `format_report()` | ✅ コア実装済み |
| PKS Engine | `mekhane/pks/pks_engine.py` (L622) | SelfAdvocate を呼び出し | ✅ 統合済み |
| PKS CLI | `mekhane/pks/pks_cli.py` (L35, L238) | CLI 経由の SelfAdvocate | ✅ |
| Gnōsis | `mekhane/gnosis/` | 論文データソース | ✅ |
| Sophia KI | `mekhane/sophia/` | KI データソース | ✅ |
| Digestor | `mekhane/digestor/` | 論文消化パイプライン | ✅ |
| API ルート | **未公開** | フィード用 API なし | ❌ |

### SelfAdvocate の主要メソッド

| メソッド | 説明 |
|:---------|:-----|
| `generate(nugget, context)` | 単一論文 → 一人称メッセージ生成 |
| `generate_batch(nuggets, context)` | 複数論文の一括変換 |
| `format_report(advocacies)` | Markdown レポート生成 |
| `_generate_llm(nugget, context)` | Gemini で一人称メッセージ生成 |
| `_generate_template(nugget, context)` | テンプレートベースのフォールバック |

## 3. API 仕様 (新規)

| Method | Path | 説明 | バックエンド |
|:-------|:-----|:-----|:------------|
| GET | `/api/feed` | フィードアイテム一覧 (ページ付き) | FeedGenerator [NEW] |
| GET | `/api/feed/{id}` | フィードアイテム詳細 | 同上 |
| POST | `/api/feed/{id}/like` | いいね (学習データとして記録) | FeedPreference [NEW] |
| POST | `/api/feed/{id}/comment` | コメント追加 | FeedComment [NEW] |
| POST | `/api/feed/{id}/research` | フォローアップリサーチ発動 | Periskopē 連携 |
| GET | `/api/feed/preferences` | 学習済み好み設定 | FeedPreference |
| POST | `/api/feed/generate` | フィード手動生成トリガー | FeedGenerator |
| DELETE | `/api/feed/{id}/dismiss` | フィードアイテム非表示 | 同上 |

### `/api/feed` レスポンス例

```json
{
  "items": [
    {
      "id": "feed-20260226-001",
      "author": {
        "name": "Dr. Friston (FEP)",
        "avatar": "🧠",
        "persona": "fep_researcher"
      },
      "headline": "Active Inference の最新動向 — 2026年の3つの革新",
      "body": "私の自由エネルギー原理が、ついに実装レベルで...",
      "source": {"paperId": "arXiv:2602.xxxxx", "title": "..."},
      "relevanceScore": 0.87,
      "postedAt": "2026-02-26T10:00:00Z",
      "liked": false,
      "commentCount": 0
    }
  ],
  "total": 15,
  "page": 1
}
```

## 4. データモデル

```typescript
interface FeedItem {
  id: string;
  author: FeedAuthor;         // 仮想インフルエンサー
  headline: string;           // 3行要約
  body: string;               // 10-20行本文
  source: {paperId: string; title: string; url?: string};
  relevanceScore: number;     // SelfAdvocate 算出
  postedAt: string;
  liked: boolean;
  comments: FeedComment[];
}

interface FeedAuthor {
  name: string;               // "Dr. Friston" 等
  avatar: string;             // Emoji アイコン
  persona: string;            // システムプロンプト ID
}

interface FeedComment {
  id: string;
  text: string;
  createdAt: string;
}

interface FeedPreference {
  likedTopics: string[];       // いいねから学習
  dismissedPaperIds: string[];
  preferredPersonas: string[];
}
```

## 5. バックエンド新規実装

### FeedGenerator (新規)

```python
# mekhane/pks/feed_generator.py [NEW]
class FeedGenerator:
    """SelfAdvocate + Digestor + PKS → Twitter 風フィードを生成"""

    def __init__(self, self_advocate: SelfAdvocate):
        self.advocate = self_advocate

    def generate_daily(self, preferences: FeedPreference) -> list[FeedItem]:
        """日次フィード生成: 新着論文 + KI → SelfAdvocate → FeedItem"""
        # 1. Digestor から候補取得
        # 2. preferences でフィルタ + 優先度計算
        # 3. SelfAdvocate.generate_batch() で一人称変換
        # 4. FeedItem 形式に変換
        ...

    def generate_followup(self, feed_id: str) -> ResearchReport:
        """フォローアップリサーチ: Periskopē 連携"""
        ...
```

## 6. フロントエンド実装ステップ

### Phase 1: フィード UI (読み取り)

| Step | 内容 | ファイル |
|:-----|:-----|:---------|
| 1-1 | FeedGenerator + API ルーター作成 | `mekhane/pks/feed_generator.py` [NEW], `mekhane/api/routes/feed.py` [NEW] |
| 1-2 | Feed ビュー作成 (Twitter カード風) | `src/views/feed.ts` [NEW] |
| 1-3 | route-config.ts にルート追加 | `src/route-config.ts` |
| 1-4 | `client.ts` に feed API メソッド追加 | `src/api/client.ts` |

### Phase 2: インタラクション (いいね・コメント)

| Step | 内容 | ファイル |
|:-----|:-----|:---------|
| 2-1 | いいねボタン + 学習 API | `feed.ts`, `feed_generator.py` |
| 2-2 | コメント入力 UI | `src/components/feed-comment.ts` [NEW] |
| 2-3 | 好みプロファイル表示 | `src/views/settings.ts` 拡張 |

### Phase 3: フォローアップリサーチ

| Step | 内容 | ファイル |
|:-----|:-----|:---------|
| 3-1 | 「深掘り」ボタン → Periskopē research 連携 | `feed.ts` + `periskope_research` |
| 3-2 | リサーチ結果の inline 表示 | `src/components/research-result.ts` [NEW] |
| 3-3 | 消化候補への自動追加 (Digestor 連携) | `feed_generator.py` |

## 6. テスト戦略

| テスト種別 | 内容 |
|:----------|:-----|
| 単体テスト | `test_self_advocate.py` (既存 ✅) + `test_feed_generator.py` [NEW] |
| E2E | フィード表示 → いいね → フォローアップリサーチ → 結果表示 |
| 非機能 | フィード生成 < 10秒 / 20アイテム |

## 7. 依存関係

- `mekhane/pks/self_advocate.py` ← 論文一人称変換 (実装済み ✅)
- `mekhane/pks/pks_engine.py` ← PKS 統合 (実装済み ✅)
- `mekhane/digestor/` ← 消化パイプライン (実装済み ✅)
- Periskopē ← フォローアップリサーチ (MCP 実装済み ✅)
- Gnōsis / Sophia ← データソース (実装済み ✅)
