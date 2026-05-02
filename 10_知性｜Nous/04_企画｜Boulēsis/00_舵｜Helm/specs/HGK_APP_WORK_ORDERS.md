# HGK APP — Gap 埋め作業依頼書 v3.0
> **作成日**: 2026-02-23 → **更新日**: 2026-03-21
> **作成者**: Cowork Claude (外部レビュー + コードレベル検証 + Playwright UI 実測)
> **たたき台**: IDE Claude の /hon- L1-L3 レビュー
> **目的**: Jules / Gemini / IDE Claude への実装依頼を構造化

---

## v3.0 変更点 (2026-03-21)

| 変更 | 内容 |
|:-----|:-----|
| **解決** | WO-00: Chat cw-layout 全画面遮蔽 → ✅ ブラウザ検証で遮蔽なしを確認 |
| **解決** | WO-01: Agent 2エンドポイント → ✅ `agent.py` に完全実装済み (`/api/ask/agent/stream` L88 + `/api/ask/agent/approve` L204) |
| **追加** | WO-07: `node_modules/.bin/vite` が0バイト空ファイル → ✅ symlink 修復済み |
| **追加** | WO-08: Assistant Pane で 429 エラーが生 JSON 表示 |
| **追加** | WO-09: Chat ビュー状態保持不完全 (ビュー切替で会話リセット) |

<details><summary>v2.0 変更点</summary>

| 変更 | 内容 |
|:-----|:-----|
| **追加** | WO-00: Chat cw-layout が全ビューを遮蔽 (BLOCKER) |
| **追加** | WO-00b: Files パネル パス制限エラー |
| **削除** | 旧 WO-06: F6 Colony バックエンド → ✅ colony.py 535行で MVP 実装済み |
| **縮小** | WO-01: colony/stream は実装済み → agent/stream + approve のみ |
| **新発見** | 全9ビューが Chat View と同一画面 → ナビゲーション自体は動作するがCSSレイアウト崩壊 |

</details>

---

## Gap 一覧 (致命度順)

| ID | 致命度 | Gap | 依頼先 | 状態 |
|:---|:-------|:----|:-------|:-----|
| ~~G-BLK~~ | ~~BLOCKER~~ | ~~Chat cw-layout が全ビューを視覚的に遮蔽~~ | — | ✅ 解決済み (v3.0) |
| ~~G0~~ | ~~CRITICAL~~ | ~~Agent 2エンドポイント欠落~~ | — | ✅ 解決済み (v3.0) |
| G1 | HIGH | E2E テスト不足 | Jules ×3並列 | 未着手 |
| G2 | HIGH | chat.ts の client.ts 迂回 (9箇所 raw fetch) | Jules | 未着手 |
| G-FP | MEDIUM | Files パネル パス制限エラー | Jules | 未着手 |
| G4 | MEDIUM | UI U1-U6 残り + 文書同期 | Jules + Gemini | 未着手 |
| G5 | MEDIUM | Diff-review コンポーネント分離 | Jules | 未着手 |
| G6 | LOW | F1/F2/F5/F7 の IMPL_SPEC 作成 | Gemini | 未着手 |
| **G7** | ~~HIGH~~ | ~~`node_modules/.bin/vite` 0バイト空ファイル~~ | — | ✅ 修復済み (v3.0) |
| **G8** | MEDIUM | Assistant Pane で 429 エラーが生 JSON 表示 | IDE Claude | 未着手 |
| **G9** | MEDIUM | Chat ビュー状態保持不完全 (ビュー切替で会話リセット) | IDE Claude | 未着手 |

---

## WO-00: Chat cw-layout 全画面遮蔽の修正 [G-BLK — BLOCKER]

### 問題 (Playwright 実測で確認)

**全9ビューのスクリーンショットが同一の Chat View を表示。**

根本原因の推論チェーン:

1. `#app` は CSS Grid: `grid-template-columns: 48px 180px 1fr`
2. `main#view-content` は Grid の3列目 (`1fr`) — **CSS 定義なし** (overflow も position も未設定)
3. Chat View (DEFAULT_ROUTE) が `#view-content` 内に `.cw-layout { height: 100vh }` を描画
4. `.cw-layout` は自身の3カラム flex レイアウト (sidebar + main + panel) を持ち、**親コンテナを無視して viewport 全体を占有**
5. navigate() で他ビューに遷移すると `app.innerHTML = skeletonHTML()` → renderer() が実行される
6. **しかし**: E2E テストの `button:has-text("Dashboard")` が実際のタブボタンを正しくマッチしていない可能性、あるいは Chat の textarea auto-focus がクリックを奪っている

**確信度: 85%** — バックエンド未起動のため navigate() の実動作を完全には確認できていない。cw-layout の `100vh` 問題は CSS で確定。

### 依頼先: IDE Claude
**理由**: レイアウトの設計判断 (Chat を全画面にするか、Grid 内に収めるか) はアーキテクチャ判断。

### 実装指示

```
ファイル: src/styles.css, src/views/css/cowork.css

Option A (推奨): Chat を Grid 内に収める
  1. #view-content に CSS 追加:
     main#view-content {
       overflow: hidden;
       position: relative;
       min-height: 0;  /* flex/grid 子要素の縮小を許可 */
     }
  2. .cw-layout の height を 100vh → 100% に変更
  3. 他の 100vh ビュー (devtools, graph3d, orchestrator) も同様に修正

Option B: Chat を全画面モードとして icon-rail/tab-nav を上に重ねる
  1. .cw-layout に position: absolute; inset: 0; z-index: 1 を追加
  2. #icon-rail, #tab-nav に z-index: 10 を設定
  → Chat は全画面のままだが、ナビゲーションは常にアクセス可能
```

### 検証基準
- Playwright で dashboard 遷移 → スクリーンショットが Chat View と異なること
- 全23ビューで icon-rail + tab-nav が常に表示されること
- Chat View の cw-layout が #view-content 内に正しく収まること

---

## WO-00b: Files パネル パス制限修正 [G-FP — MEDIUM]

### 問題
右パネルの Files タブに赤文字で表示:
```
Access denied: /home/makaron8426/Sync/oikos/01_ヘゲモニコン | Hegemonikon
is outside /home/makaron8426/oikos
```

ファイルパスが Sync/ 下のシンボリックリンクまたは旧パスを参照しており、
バックエンドの `allowed_directories` チェックに引っかかっている。

### 依頼先: Jules

```
リポジトリ: Tolmeton/Hegemonikon
ブランチ: fix/files-panel-path

1. chat.ts 内の Files パネル初期化コードを特定
   (おそらく /api/files/list を呼んでいる箇所)
2. リクエストで送信しているパスの出所を追跡
   - ハードコード? localStorage? Tauri API?
3. 修正:
   - パスを /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon に正規化
   - または symlink 解決 (realpath) をバックエンド側で実施
```

---

## WO-01: Agent エンドポイント実装 [G0 — CRITICAL]

### 問題
chat.ts が呼んでいるエンドポイントのうち2つがサーバー側に未確認:
- `POST /api/ask/agent/stream` (Agent SSE ストリーミング)
- `POST /api/ask/agent/approve` (安全ゲート承認)

**注**: colony/stream は colony.py (535行) で ✅ MVP 実装済み。

### 依頼先: IDE Claude
**理由**: ask_with_tools のジェネレータ化、SSE イベント設計、安全ゲートのステートマシンはアーキテクチャ判断を伴う。

### 実装指示

```
ファイル: mekhane/api/routes/ に新規ルーター作成 (agent.py)

1. POST /api/ask/agent/stream
   - CortexClient.ask_with_tools() をジェネレータ版にリファクタ
   - SSE イベント型: thinking, tool_call, tool_result, chunk, done, error
   - hgk_tools.py の HGK_TOOL_DEFINITIONS + TOOL_DEFINITIONS を結合
   - asyncio.to_thread() で同期関数をラップ

2. POST /api/ask/agent/approve
   - Agent ループの一時停止 → 再開メカニズム
   - asyncio.Event or Queue でフロント ↔ バック同期
   - HIGH_RISK_TOOLS 判定: write_file, run_command, git_push
   - approve=true → ツール実行続行、approve=false → ループ中断
```

### 検証基準
- `curl -N -X POST localhost:9698/api/ask/agent/stream` で SSE イベントが流れる
- Chat View でエージェントモードON → 質問 → ツール実行がリアルタイム表示
- write_file 呼び出し時に承認UIが表示され、承認なしでは実行されない

---

## WO-02: chat.ts の client.ts 統合 [G2 — HIGH]

### 問題
chat.ts が生 `fetch()` で9箇所 API を呼んでおり、client.ts の型安全性・エラーハンドリング・Tauri IPC 対応を迂回。

### 依頼先: Jules

```
リポジトリ: Tolmeton/Hegemonikon
ブランチ: fix/chat-client-integration

1. chat.ts 内の全 fetch() を特定 (約9箇所)
2. client.ts に SSE 対応関数を追加:
   - askStream(), askAgentStream()
   - askAgentApprove(), chatModels()
3. chat.ts の fetch() を client.ts 呼び出しに置換
4. 型定義追加: AgentSSEEvent, ApprovalRequest

注意: SSE は ReadableStream を返す特殊パターン。
      apiStream() ヘルパーを新設。Tauri 環境は直接 fetch で可。
```

---

## WO-03: E2E テスト拡充 [G1 — HIGH]

### 依頼先: Jules ×3 並列

### タスク A: ビュー別スモークテスト
```
ブランチ: test/view-smoke-tests
ファイル: hgk/e2e/views.spec.ts
対象: dashboard, chat, devtools, search, gnosis, digestor
内容: ページ遷移 → DOM 要素確認 → API モック → エラーフォールバック

重要: WO-00 完了後に実施。現在は全ビューが Chat を表示するため。
```

### タスク B: Agent モード E2E (WO-01 完了後)
```
ブランチ: test/agent-e2e
ファイル: hgk/e2e/agent.spec.ts
内容: Agent ON → SSE 受信 → ツール表示 → 承認UI → 承認/却下
WO-01 未完了時は Playwright route でモック
```

### タスク C: SSE ストリーミング E2E
```
ブランチ: test/sse-e2e
ファイル: hgk/e2e/sse.spec.ts
内容: chunk逐次表示、thinking表示、エラー表示、接続断再接続
```

---

## WO-04: UI 文書同期 + スライドアウト改善 [G4 — MEDIUM]

### Gemini タスク: UI_REQUIREMENTS.md v2.0
```
U1-U6 の各項目を現在のコード (icon-rail.ts, tab-nav.ts,
slide-panel.ts, chat.ts) と突き合わせ、実装状態を更新。
SSE (U5) は「✅ 実装済み」、Diff (U6) は「⚠️ chat.ts 内にハードコード」に。
```

### Jules タスク: U3 スライドアウト改善
```
ブランチ: feat/slide-panel-hover
slide-panel.ts に OPPO PAD 風の振る舞いを実装:
- 右端に薄い線 (1px, opacity: 0.3) 常時表示
- ホバーで opacity: 0.7 トランジション
- クリックでスライドイン (320px)
- パネル外クリックでスライドアウト
```

---

## WO-05: Diff-review コンポーネント分離 [G5 — MEDIUM]

### 依頼先: Jules

```
ブランチ: refactor/diff-review-component

1. chat.ts の renderDiffHtml() → components/diff-review.ts に抽出
2. chat.ts の showApprovalUI() → components/approval-gate.ts に抽出
3. 公開 API:
   - renderDiff(old, new, filePath): HTMLElement
   - showApprovalDialog(request): Promise<boolean>
4. chat.ts, devtools.ts, orchestrator.ts から import 可能に
```

---

## WO-06: F1/F2/F5/F7 IMPL_SPEC ドラフト [G6 — LOW]

### 依頼先: Gemini

```
AMBITION.md の F1, F2, F5, F7 について IMPL_SPEC ドラフトを作成。
IMPL_SPEC_APP_AGENT.md と同じフォーマット:
- 現状分析、Layer 1-3 API 設計、Phase 分割、リスク

出力:
- IMPL_SPEC_MOTHERBRAIN.md (F1)
- IMPL_SPEC_SESSION_NOTE.md (F2)
- IMPL_SPEC_VIRTUAL_FEED.md (F5)
- IMPL_SPEC_3DKB.md (F7)

精度 60% で十分。Creator レビュー前提。
```

---

## 実行順序 (v2.0 — 依存関係反映)

```
Phase 0 — 即時 (BLOCKER 解消):
  WO-00 (IDE Claude)        ← 最優先。全ビューが遮蔽されている
  WO-00b (Jules)            ← 並列可能。Files パネル修正

Phase 1 — Week 1:
  WO-01 (IDE Claude)        ← WO-00 完了後。Agent 機能のブロッカー
  WO-02 (Jules)             ← 並列可能
  WO-04 Gemini 部分          ← 文書更新のみ、並列可能

Phase 2 — Week 2:
  WO-03 A (Jules)           ← WO-00 完了後 (ビューが見えないとテスト不能)
  WO-03 B/C (Jules ×2)     ← WO-01 完了後
  WO-05 (Jules)             ← 並列可能
  WO-04 Jules 部分           ← UI 改善

Phase 3 — Week 3:
  WO-06 (Gemini)            ← いつでも開始可能
```

### 依存関係グラフ
```
WO-00 ─┬─→ WO-03 A (ビューが見えてからテスト)
        └─→ WO-01 ─┬─→ WO-03 B (Agent E2E)
                    └─→ WO-03 C (SSE E2E)

WO-02 ───→ (独立、いつでも)
WO-04 ───→ (独立、いつでも)
WO-05 ───→ (独立、いつでも)
WO-06 ───→ (独立、いつでも)
WO-00b ──→ (独立、いつでも)
```

---

## 付録: Playwright 実測結果 (2026-02-25)

### スクリーンショット一覧
全9ビュー (`/tmp/hgk_final_*.png`) が同一の Chat View を表示。

### 共通観察
- **Icon Rail**: η, K, Δ, ε, Ω の5グループが左端に表示
- **Chat View**: 左サイドバー (Chats, New Chat), 中央 (何をお手伝いしましょう？), 右パネル (Files/Terminal/AI)
- **右パネル Files**: "Access denied" エラー表示
- **モデル選択**: Gemini 3.1 Pro がデフォルト表示、Claude Op... も選択可能
- **モードトグル**: +, P, E, V ボタン + ⚙️ 設定
- **テーマ**: ダークモード (☀️ トグル表示)
- **Backend**: port 9698 未起動のため API 依存ビューはスケルトンローダー表示

### 確認不能だった項目
- Dashboard, Search, DevTools 等の実際のレンダリング (CSS 遮蔽のため)
- SSE ストリーミングの動作 (バックエンド未起動)
- Agent モード・Colony モードの動作

---

*Generated: 2026-02-25 by Cowork Claude — v2.0 (Playwright UI 実測反映)*
