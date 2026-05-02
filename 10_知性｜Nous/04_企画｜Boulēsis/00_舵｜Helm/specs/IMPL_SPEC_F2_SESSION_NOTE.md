# IMPL_SPEC: F2 — セッション＝ノート（動的ナレッジ）

> **AMBITION 要件**: Obsidian 風ディレクトリ階層 + 自動分類 + リンク構造 + MemX 統合
> **ステータス**: 🟠 バックエンド実装済み / フロントエンド未接続 / API ルート未公開
> **Connected State Packet**: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/projects/PJ-20260417-001_v003-session-context/00_control/project_index.yaml` + `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/projects/PJ-20260417-001_v003-session-context/00_control/decisions.md`

---

## 0. State Packet 接続

本 spec は、`V-003` exemplar の `next_transform` として使う reader-facing IMPL_SPEC である。  
State Packet 側で固定した `purpose / assumptions / acceptance seed` を、ここでは
`概要 / 既存バックエンド / API 仕様 / フロントエンド実装ステップ / テスト戦略` に展開する。

---

## 1. 概要

セッションを動的なナレッジノートとして永続化する。
**バックエンドは `session_notes.py` (1399行) で MECE 分類・ベクトル検索・リンク構造・LLM 分類・
merge_similar・resume_context まで全メソッドが実装済み**。
主タスクは **API ルートの公開** と **フロントエンド UI の実装**。

## 2. 既存バックエンド（接続先）

| コンポーネント | パス | 主要 API |
|:-------------|:-----|:---------|
| SessionStore | `mekhane/ochema/session_store.py` (225行) | `create_session()`, `add_turn()`, `search()`, `get_history()` |
| SessionNotes | `mekhane/ochema/session_notes.py` (1399行) | `digest()`, `embed()`, `link()`, `get_relevant_chunks()`, `classify_with_llm()`, `merge_similar()`, `resume_context()`, `list_notes()`, `trace_to_source()`, `get_backlinks()`, `digest_all()` |
| Session Indexer | `mekhane/anamnesis/session_indexer.py` | セッションインデックス |
| API ルート | **未公開** | `/api/sessions/notes` 等は未実装 |

### SessionNotes の AMBITION 直接対応メソッド

| AMBITION 要件 | メソッド | 状態 |
|:-------------|:---------|:-----|
| 自動分類（ノート化） | `classify_with_llm()` | ✅ 実装済み |
| 各 PJ ディレクトリに保存・仕訳 | `digest()` | ✅ 実装済み |
| 似たテーマのメモを統合 | `merge_similar(synthesize=True)` | ✅ 実装済み |
| リンク構造 | `link()`, `get_backlinks()` | ✅ 実装済み |
| セッションの続きを行える | `resume_context()` | ✅ 実装済み |
| 関連情報を取得 | `get_relevant_chunks()` | ✅ 実装済み |

## 3. API 仕様 (新規)

| Method | Path | 説明 | バックエンド |
|:-------|:-----|:-----|:------------|
| GET | `/api/notes` | ノート一覧 (PJ フィルタ付) | `SessionNotes.list_notes()` |
| GET | `/api/notes/{session_id}` | ノート詳細 + チャンク | `SessionNotes.digest()` 結果参照 |
| POST | `/api/notes/{session_id}/digest` | セッションを消化→ノート化 | `SessionNotes.digest()` |
| POST | `/api/notes/digest-all` | 全未処理を一括消化 | `SessionNotes.digest_all()` |
| GET | `/api/notes/{session_id}/links` | リンク一覧 | `SessionNotes.link()` + `get_backlinks()` |
| GET | `/api/notes/search?q=...` | ベクトル類似検索 | `SessionNotes.get_relevant_chunks()` |
| POST | `/api/notes/{session_id}/classify` | LLM 分類実行 | `SessionNotes.classify_with_llm()` |
| GET | `/api/notes/merge?project=...` | 類似チャンク統合候補 | `SessionNotes.merge_similar()` |
| GET | `/api/notes/{session_id}/resume` | セッション再開用コンテキスト | `SessionNotes.resume_context()` |

## 4. データモデル

```typescript
interface SessionNote {
  sessionId: string;
  project: string;
  date: string;
  title: string;
  topics: string[];
  tags: string[];
  chunks: NoteChunk[];
}

interface NoteChunk {
  path: string;
  content: string;
  turnRange: [number, number];
  metadata: Record<string, unknown>;
}

interface NoteLink {
  source: string;            // チャンクパス
  target: string;
  distance: number;          // L2 距離
}

interface NoteTree {
  projects: {
    name: string;
    notes: SessionNote[];
    children: NoteTree[];    // サブプロジェクト
  }[];
}
```

## 5. フロントエンド実装ステップ

### Phase 1: API ルート公開 (バックエンド)

| Step | 内容 | ファイル |
|:-----|:-----|:---------|
| 1-1 | FastAPI ルーター作成 | `mekhane/api/routes/notes.py` [NEW] |
| 1-2 | SessionNotes を FastAPI に接続 | 同上 |
| 1-3 | `client.ts` に notes API メソッド追加 | `src/api/client.ts` |

### Phase 2: ディレクトリツリー UI

| Step | 内容 | ファイル |
|:-----|:-----|:---------|
| 2-1 | ツリーコンポーネント (開閉式) 作成 | `src/components/note-tree.ts` [NEW] |
| 2-2 | 左パネルに統合 (Cowork 準拠) | `src/views/cowork.ts` or `chat.ts` |
| 2-3 | ノート詳細ビュー (マークダウン表示) | `src/components/note-viewer.ts` [NEW] |

### Phase 3: リンク・検索 UI

| Step | 内容 | ファイル |
|:-----|:-----|:---------|
| 3-1 | バックリンクパネル (Obsidian 風) | `src/components/backlinks.ts` [NEW] |
| 3-2 | ベクトル検索の検索ビュー統合 | `src/views/search.ts` 拡張 |
| 3-3 | 類似マージ UI | `src/components/merge-panel.ts` [NEW] |

### Phase 4: セッション再開

| Step | 内容 | ファイル |
|:-----|:-----|:---------|
| 4-1 | ノートから「続きを開始」ボタン | `note-viewer.ts` |
| 4-2 | `resume_context()` → Chat 入力自動注入 | `src/views/chat.ts` |

## 6. テスト戦略

| テスト種別 | 内容 |
|:----------|:-----|
| 単体テスト | `test_session_notes.py` (既存 ✅) を API ルートテストに拡張 |
| E2E | ノート一覧表示 → クリック → 詳細表示 → バックリンク表示 |
| 非機能 | digest_all < 30秒 / 100セッション、ベクトル検索 < 1秒 |

## 7. 依存関係

- `mekhane/ochema/session_notes.py` ← 全メソッド実装済み ✅
- `mekhane/ochema/session_store.py` ← SQLite 永続化 ✅
- LanceDB ← ベクトル検索 (session_notes 内で使用)
- Cortex API ← LLM 分類 (classify_with_llm)
