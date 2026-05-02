# Jules バッチ投入用プロンプト集
> **作成日**: 2026-02-25
> **用途**: Jules API 復旧後にコピペで投入 or IDE Claude から `hgk_jules_create_task` で使用
> **リポジトリ**: Tolmeton/Hegemonikon

---

## Task 1: WO-00b — Files パネル パス制限修正

**ブランチ**: `fix/files-panel-path`

```
Chat View の右パネル (Files タブ) に以下のエラーが赤文字で表示される:

Access denied: /home/makaron8426/Sync/oikos/01_ヘゲモニコン | Hegemonikon
is outside /home/makaron8426/oikos

ファイルパスが Sync/ 下のシンボリックリンクまたは旧パスを参照しており、
バックエンドの allowed_directories チェックに引っかかっている。

実装指示:
1. hgk/src/views/chat.ts 内の Files パネル初期化コードを特定
   (おそらく /api/files/list を呼んでいる箇所)
2. リクエストで送信しているパスの出所を追跡
3. バックエンド側修正 (推奨):
   mekhane/api/routes/ 内のファイル操作ルートで
   os.path.realpath() を適用してシンボリックリンクを解決してから
   allowed_directories チェックを行うように修正

検証: Chat View の Files タブが Access denied ではなくファイル一覧を表示すること
```

---

## Task 2: WO-02 — chat.ts の client.ts 統合

**ブランチ**: `fix/chat-client-integration`

```
hgk/src/views/chat.ts が生 fetch() で約9箇所 API を呼んでおり、
hgk/src/api/client.ts の型安全性・エラーハンドリングを迂回している。

実装指示:
1. chat.ts 内の全 fetch() 呼び出しを検索・特定 (約9箇所)
2. client.ts に SSE 対応関数を追加:
   - askStream(params) — 通常の SSE ストリーミング応答
   - askAgentStream(params) — Agent モードの SSE ストリーミング
   - askAgentApprove(sessionId, approve) — 安全ゲート承認/却下
   - chatModels() — 利用可能モデル一覧取得
3. SSE は ReadableStream を返す特殊パターン。apiStream() ヘルパーを新設:
   async function apiStream(path: string, body?: object): Promise<ReadableStream> {
     const res = await fetch(`${BASE_URL}${path}`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: body ? JSON.stringify(body) : undefined,
     });
     if (!res.ok) throw new ApiError(res.status, await res.text());
     return res.body!;
   }
4. chat.ts の各 fetch() を client.ts の関数呼び出しに置換
5. 型定義追加: AgentSSEEvent, ApprovalRequest, ChatModel

注意:
- Tauri 環境では直接 fetch で OK
- SSE パーサー (readSSEStream 等) は chat.ts に残してよい
- client.ts の既存パターン (apiGet, apiPost 等) を踏襲

検証:
- chat.ts 内に生の fetch() が残っていないこと
- npm run build でコンパイルエラーなし
```

---

## Task 3: WO-05 — Diff-review コンポーネント分離

**ブランチ**: `refactor/diff-review-component`

```
hgk/src/views/chat.ts (1300+ 行) に Diff レンダリングと承認 UI が
ハードコードされており、他のビューから再利用できない。

実装指示:
1. chat.ts から以下の関数を特定:
   - renderDiffHtml() (L456-472 付近) — unified diff → HTML テーブル
   - showApprovalUI() (L474-515 付近) — ツール実行の承認/却下ダイアログ

2. 新規ファイル作成:
   hgk/src/components/diff-review.ts:
     export function renderDiff(oldText: string, newText: string, filePath?: string): HTMLElement

   hgk/src/components/approval-gate.ts:
     export interface ApprovalRequest {
       toolName: string;
       args: Record<string, unknown>;
       diff?: { old: string; new: string; path: string };
     }
     export function showApprovalDialog(request: ApprovalRequest): Promise<boolean>

3. hgk/src/components/ ディレクトリが存在しなければ作成
4. chat.ts の元の関数を新コンポーネントの import に置換
5. CSS は hgk/src/components/css/diff-review.css に分離

検証:
- npm run build でコンパイルエラーなし
- Chat View で Agent モードの承認 UI が従来通り表示されること
```

---

## 投入コマンド例

```python
# IDE Claude or MCP から:
hgk_jules_create_task(
    prompt="<上記 Task 1 の内容>",
    repo="Tolmeton/Hegemonikon",
    branch="fix/files-panel-path"
)
```
