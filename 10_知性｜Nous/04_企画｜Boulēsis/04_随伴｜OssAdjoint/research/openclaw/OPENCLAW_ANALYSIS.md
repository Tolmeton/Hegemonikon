# OpenClaw → HGK APP 転用・吸収分析レポート

> **作成日**: 2026-02-28
> **リポジトリ**: `/home/makaron8426/Sync/oikos/openclaw` (クローン済み)
> **ソース**: [github.com/openclaw/openclaw](https://github.com/openclaw/openclaw)
> **目的**: OpenClaw の設計パターン・コード・UIを分析し、HGK APP (AMBITION F1-F10) への転用候補を MECE に整理する

---

## 1. OpenClaw 全体像

### 1.1 技術スタック

| 項目 | 仕様 |
|:-----|:-----|
| 言語 | TypeScript (Node.js 22+) |
| パッケージ管理 | pnpm (monorepo) |
| UI フレームワーク | Lit Web Components + Vite |
| データベース | SQLite + sqlite-vec (ベクトル検索) |
| ネイティブアプリ | macOS (Swift) / iOS / Android |
| テスト | vitest |

### 1.2 リポジトリ規模

| ディレクトリ | ファイル数 | 概要 |
|:------------|:----------|:-----|
| `src/agents/` | 451 | エージェント・compaction・model-selection・skill system |
| `src/gateway/` | 194 | Gateway サーバー・認証・hooks・sessions |
| `src/memory/` | ~30 | メモリ・MMR・temporal-decay・query-expansion |
| `src/tui/` | ~20 | ターミナル UI (Ink-like) |
| `src/sessions/` | ~15 | セッション管理・send-policy |
| `ui/src/` | ~80 | Web UI (Lit Components) |
| `extensions/` | 39 | チャネル統合 (Discord, Slack, Telegram 等) |
| `skills/` | 52 | スキルパッケージ |
| `apps/` | 3 | macOS / iOS / Android |

### 1.3 設計ビジョン (ビジョン.md)

- **セキュリティ最優先**: ターミナルファースト、明示的ユーザー制御
- **プラグイン志向**: コアを軽量に保ち、拡張は Plugin/Skill で
- **MCP 対応**: mcporter ブリッジ経由
- **貢献規則**: 小さく焦点を絞った PR を推奨

---

## 2. 吸収候補 (MECE: 安全装置 / コンテキスト管理 / Skill・Plugin / セッション / メモリ / UI)

### 2.1 安全装置

#### T-03: Tool Loop Detection

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `src/agents/tool-loop-detection.ts` (624行) |
| **AMBITION 対応** | F6 Colony / F9 Agent 並列実行 の安全弁 |
| **優先度** | 🔴 最重要 |

**デフォルト無効** (SOURCE: L31): `enabled: false`。意図: ループ検出は想定外の副作用リスクがあるため opt-in。HGK では Colony/Agent 実行時に enabled: true にすべき。

**4検知器の判定優先順位** (`detectToolCallLoop()` L372-494):

```
1. global_circuit_breaker (最優先): noProgressStreak >= 30 → critical → 即ブロック
2. known_poll_no_progress: ポーリングツール + noProgressStreak >= 20 → critical
3. known_poll_no_progress: ポーリングツール + noProgressStreak >= 10 → warning
4. ping_pong: 交互パターン >= 20 + noProgressEvidence → critical
5. ping_pong: 交互パターン >= 10 → warning
6. generic_repeat: 同一呼び出し >= 10 → warning (ポーリングツール除外)
```

**定数テーブル** (SOURCE: L27-36):

| 定数 | デフォルト値 | 設定可能 | 意味 |
|:-----|:-----------|:---------|:-----|
| `TOOL_CALL_HISTORY_SIZE` | 30 | ✅ `historySize` | スライディングウィンドウのサイズ |
| `WARNING_THRESHOLD` | 10 | ✅ `warningThreshold` | 警告を出す反復回数 |
| `CRITICAL_THRESHOLD` | 20 | ✅ `criticalThreshold` | ブロックする反復回数 |
| `GLOBAL_CIRCUIT_BREAKER_THRESHOLD` | 30 | ✅ `globalCircuitBreakerThreshold` | 最終手段のハード停止 |

**閾値の自動補正** (L78-83): `criticalThreshold <= warningThreshold` の場合 `critical = warning + 1` に自動修正。不正な設定でも安全に動作。

**ハッシュシステム**:

| 関数 | 用途 | ハッシュ対象 |
|:-----|:-----|:----------|
| `hashToolCall()` | ツール呼び出しの同一性 | `toolName:sha256(stableStringify(params))` |
| `hashToolOutcome()` | 結果の変化検出 | ポーリングツールは `{action, status, exitCode, exitSignal, text}` の構造化ダイジェスト。一般ツールは `{details, text}` |
| `stableStringify()` | 決定的 JSON | オブジェクトのキーをソートして再帰的に直列化。`toSorted()` 使用 |
| `stableStringifyFallback()` | エラー耐性 | stringify 失敗時に Error, bigint, プリミティブ等を個別処理 |

**ポーリングツール認識** (L147-156): `command_status` または `process` ツールの `action === 'poll'|'log'` を自動認識。これらは反復呼び出しが正常動作のため、generic_repeat 検知器から除外される。

**no-progress ストリーク検出** (`getNoProgressStreak()` L232-260):

- 履歴を逆順に走査し、同一 toolName + argsHash のエントリを辿る
- **resultHash が同じ**間はストリークを延長。異なった時点で停止
- これにより「呼んでいるが進んでいない」状態を正確に検出

**ping-pong 検出** (`getPingPongStreak()` L262-362):

- 直近の履歴から2つの異なる argsHash パターンの交互出現を検出
- `noProgressEvidence`: 両パターンの全結果ハッシュが一定 → 「交互に呼んでいるが全く進んでいない」
- `canonicalPairKey()`: 2つのシグネチャをソートして結合 → warningKey の一意性保証

**2段階記録** (分離アーキテクチャ):

1. `recordToolCall()`: ツール呼び出し**前**に toolName + argsHash + timestamp を記録
2. `recordToolCallOutcome()`: ツール呼び出し**後**に resultHash を backfill (toolCallId で逆引き)

**統計関数** (`getToolCallStats()` L593-623): `totalCalls`, `uniquePatterns`, `mostFrequent` を返す。デバッグ/モニタリング用。

**HGK 転用ポイント** (増強):

1. **4検知器のカスケード構造** → HGK の Colony Worker に直接移植。global_circuit_breaker は最終手段として必須
2. **no-progress ストリーク** → Compaction と連携: ストリーク中のツール呼び出しは Compaction で圧縮可能
3. **ポーリングツール認識** → HGK の `command_status` 相当を自動認識して誤検出を回避
4. **2段階記録** → ツール結果が返る前に呼び出しを記録し、結果到着で backfill。非同期実行に対応
5. **閾値の設定可能性** → Creator がリスク許容度に応じて閾値を調整可能 (N-4 との連携)
6. **warningKey** → 同じ警告の重複抑制 (UI でユーザーに同じ警告を繰り返さない)

**`/noe+` 深層洞察 — ループ検出は免疫系である**:

> **普遍原理**: ループ検出は、「反復」ではなく「**進捗のない反復**」を検出する問題。
> 反復しても結果が変化していれば正常。「進捗」の操作的定義 = **tool outcome ハッシュの変化**。
> これが `recordToolCall()` (呼び出し記録) と `recordToolCallOutcome()` (結果記録) の
> **2段階記録**が存在する唯一の理由。

**免疫系アナロジー** — 4 Detector は人体の防御システムと同型:

| Detector | 免疫系の対応物 | 判定方式 |
|:---------|:-------------|:---------|
| `generic_repeat` | **自然免疫 (innate)** | 同じ argsHash の反復を非特異的に検出 |
| `known_poll_no_progress` | **パターン認識受容体 (PRR)** | 既知の危険パターン (`command_status`) を特異的に |
| `ping_pong` | **アレルギー反応 (自己免疫)** | 2パターン間の振動 (過敏反応) を検出 |
| `global_circuit_breaker` | **アナフィラキシー・ブレーカー** | 全てを止める最終防衛線 |

**`noProgressEvidence` = precision-weighted prediction error**:

ping_pong 検出 (L316-354) は、A→B→A→B の**両方の結果ハッシュが安定しているか**を検証する。

- A の結果も B の結果も毎回同じ → `noProgressEvidence = true` → **critical** 判定可能
- 一方でも変われば → `noProgressEvidence = false` → **warning** のみ

つまり: **不確実なときは止めない (warning)、確実なときだけ止める (critical)**。
FEP: precision が高い prediction error だけが行動 (ブロック) を引き起こす。

**反論 (Z-6) — このモデルが壊れるケース**:

1. **非決定的出力ツール**: 毎回異なるハッシュを返す → ループが永遠に検出されない。
   OpenClaw は `isKnownPollToolCall()` でポーリングツールの特定フィールドのみハッシュ化し部分対処。
   HGK は**ツール属性に `deterministic: boolean` フラグ**を追加すべき。
2. **ゆっくりとした退化**: 10回に1回だけ結果が変わるが本質的に進捗がない →
   `noProgressStreak` がリセットされてしまう。**Entropy ベースの進捗計測**が必要 — 変化量ではなく情報量で判断。

---

#### T-04: Exec Approval (再深掘り)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル群** | 19ファイル, 核心5ファイル ~2,060行 |
| **AMBITION 対応** | F4 AI 指揮台 (✅/❌ 承認フロー) + N-4 (Proposal First) |
| **優先度** | 🟠 高 |

**核心ファイル構成**:

| ファイル | 行数 | 役割 |
|:---------|:-----|:-----|
| `exec-approval-manager.ts` | 174 | `ExecApprovalManager` — 承認の生成・登録・待機・解決・消費 |
| `node-invoke-system-run-approval.ts` | 299 | `sanitizeSystemRunParamsForForwarding()` — 7段バリデーション |
| `exec-approvals.ts` | 559 | 型定義・永続化・デフォルト・allowlist 管理 |
| `exec-approvals-analysis.ts` | 803 | シェルコマンド解析 (パイプライン・heredoc・チェーン) |
| `node-invoke-system-run-approval-match.ts` | 56 | 承認リクエストとランタイムの一致検証 |

**承認フロー** (`sanitizeSystemRunParamsForForwarding()`):

```
1. rawParams パース → 承認オーバーライド要求を検出
2. 制御フィールドを常に除去 (approved, approvalDecision)
3. runId 必須チェック
4. ExecApprovalManager から snapshot 取得
5. 有効期限チェック (expiresAtMs)
6. ノード紐付けチェック (nodeId 一致)
7. デバイス/接続紐付けチェック:
   - deviceId (安定、リコネクト対応) 優先
   - connId (フォールバック、接続単位)
8. ランタイムコンテキスト解決 (argv, cwd, agentId, sessionKey)
9. 承認マッチ検証 (argv + binding の完全一致)
10. Decision 適用:
    - allow-once → consumeAllowOnce() (原子的消費、再利用不可)
    - allow-always → 永続承認
    - timeout + askFallback → operator.approvals スコープ必須
```

**セキュリティ設計**:

| 設定 | デフォルト | 意味 |
|:-----|:---------|:-----|
| `security` | `deny` | 未知コマンドの既定動作: 拒否 |
| `ask` | `on-miss` | allowlist にない場合のみユーザーに確認 |
| `askFallback` | `deny` | 確認タイムアウト時: 拒否 |
| `autoAllowSkills` | `false` | Skill 由来のコマンドを自動承認しない |

**allowlist パターンマッチ**:

- `ExecAllowlistEntry`: `{ id, pattern, lastUsedAt, lastUsedCommand, lastResolvedPath }`
- 使用履歴を追跡 (lastUsedAt, lastUsedCommand) → 監査に使える
- JSON ファイル (`~/.openclaw/exec-approvals.json`) に永続化

**シェルコマンド解析** (`exec-approvals-analysis.ts` — 803行):

- `splitShellPipeline()` — パイプ (`|`) で分割、heredoc 認識、ダブルクォートエスケープ
- `splitCommandChainWithOperators()` — `&&`, `||`, `;` でチェーン分割
- `buildSafeShellCommand()` — safe bins の引数をシングルクォートで強制リテラル化
- Windows 対応: `findWindowsUnsupportedToken()`, `tokenizeWindowsSegment()`

**ExecApprovalManager のライフサイクル**:

- `create()` → レコード生成 (UUID, expiresAtMs)
- `register()` → Promise 登録 (冪等、タイムアウトタイマー付き)
- `resolve()` → 判定下達 (grace period 15秒で遅延済み awaitDecision 対応)
- `expire()` → タイムアウト (decision=undefined, resolvedBy=null)
- `consumeAllowOnce()` → 1回限り承認の原子的消費 (replay 防止)

**HGK 転用ポイント**:

1. **7段バリデーション** → N-4 Proposal First の実装モデル。HGK App の「実行承認」に直接適用
2. **allow-once vs allow-always** → Creator の操作リスク許容度に応じた2段階承認
3. **allowlist + 使用履歴** → Creator が承認したコマンドの学習 (N-4 の progressive trust)
4. **deviceId 優先** → マルチデバイスでの承認セキュリティ (HGK はローカル専用だが設計参考)
5. **シェルコマンド解析** → Colony Worker の system.run 制御に必要
6. **grace period** → 非同期承認の競合防止パターン

---

### 2.2 コンテキスト管理

#### T-01: Compaction (会話圧縮)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル群** | `compaction.ts` (454行) + `compaction-safeguard.ts` (399行) + `compact.ts` (762行) + `compaction-safety-timeout.ts` (11行) — 計 1,626 行 |
| **AMBITION 対応** | F1 マザーブレイン (フォールバック圧縮) |
| **優先度** | 🔴 最重要 |

**3層アーキテクチャ**:

```
┌─── L1: コアアルゴリズム (compaction.ts, 454行) ───────────────┐
│  チャンク分割 / トークン推定 / 段階的要約 / プルーニング       │
│  → 純粋関数群。状態なし。テスト容易。                        │
└──────────────────────────────────┬────────────────────────────┘
                                   ↓
┌─── L2: セーフガード (compaction-safeguard.ts, 399行) ────────┐
│  ExtensionAPI.on("session_before_compact") フック            │
│  → ツール失敗収集 / ファイル操作追跡 / ワークスペースルール保持│
│  → Cancel 判定 (API key なし / model なし / 会話なし)        │
└──────────────────────────────────┬────────────────────────────┘
                                   ↓
┌─── L3: パイプライン (compact.ts, 762行) ─────────────────────┐
│  compactEmbeddedPiSession():                                 │
│  → ロック取得 → セッション修復 → 履歴サニタイズ → 制限適用   │
│  → Hook(before_compaction) → compact() → Hook(after_)        │
│  → レーンキューイング (session lane + global lane)            │
│  → 5分安全タイムアウト (EMBEDDED_COMPACTION_TIMEOUT_MS)       │
└───────────────────────────────────────────────────────────────┘
```

**定数テーブル** (SOURCE: compaction.ts L12-16):

| 定数 | 値 | 意味 |
|:-----|:--|:-----|
| `BASE_CHUNK_RATIO` | 0.4 | コンテキストの40%をチャンクサイズに |
| `MIN_CHUNK_RATIO` | 0.15 | メッセージが大きい場合の下限 |
| `SAFETY_MARGIN` | 1.2 | chars/4 推定の不正確さへの20%バッファ |
| `SUMMARIZATION_OVERHEAD_TOKENS` | 4,096 | 要約プロンプト・システムプロンプト等のオーバーヘッド |
| `DEFAULT_PARTS` | 2 | 段階的要約のデフォルト分割数 |
| `DEFAULT_SUMMARY_FALLBACK` | "No prior history." | 要約生成失敗時のフォールバック文字列 |
| `EMBEDDED_COMPACTION_TIMEOUT_MS` | 300,000 (5分) | Compaction 全体のハードタイムアウト |

**核心関数 (compaction.ts)**:

| 関数 | 行 | 役割 |
|:-----|:---|:-----|
| `estimateMessagesTokens()` | L61-65 | **stripToolResultDetails() 後に**推定。セキュリティ: `.details` を LLM に絶対送らない |
| `splitMessagesByTokenShare()` | L78-117 | トークン量でメッセージを N チャンクに均等分割 |
| `chunkMessagesByMaxTokens()` | L124-164 | 最大トークン数でチャンク分割。**巨大メッセージ**: effectiveMax を超える単一メッセージは独立チャンクに強制isolate |
| `computeAdaptiveChunkRatio()` | L170-189 | 平均メッセージがコンテキストの10%超 → チャンク比率を動的に下げる。`reduction = min(avgRatio*2, BASE-MIN)` |
| `isOversizedForSummary()` | L195-198 | 単一メッセージがコンテキストの50%超 → 要約不能判定 |
| `summarizeChunks()` | L200-247 | チャンク群を LLM で**逐次**要約。前チャンクの要約が次の `previousSummary` に流れる (畳み込み構造) |
| `summarizeWithFallback()` | L253-320 | **3段フォールバック**: (1) 全体要約 → (2) 巨大メッセージ除外して部分要約 → (3) メタ情報のみ返却 |
| `summarizeInStages()` | L322-385 | 段階的要約: チャンク並列 → 部分要約 → マージ要約。`MERGE_SUMMARIES_INSTRUCTIONS` で統合 |
| `pruneHistoryForContextShare()` | L387-449 | **maxHistoryShare** (デフォルト0.5) でコンテキスト予算内にプルーニング。`repairToolUseResultPairing()` で orphaned tool_result を自動修復 |

**セーフガード (compaction-safeguard.ts) の追加機能**:

| 機能 | 実装 | HGK への示唆 |
|:-----|:-----|:-------------|
| **ツール失敗収集** | `collectToolFailures()` — isError=true の toolResult から最大8件を構造化 (toolName + summary + meta) | Compaction 要約に失敗情報を保持 → 同じ失敗の反復防止 |
| **ファイル操作追跡** | `computeFileLists()` — read/edited/written を分類し `<read-files>`, `<modified-files>` タグで要約に埋め込み | コンテキスト圧縮後も「何を触ったか」を保持 |
| **ワークスペースルール保持** | `readWorkspaceContextForSummary()` — AGENTS.md から "Session Startup" と "Red Lines" セクションを抽出 (最大2000文字) し `<workspace-critical-rules>` タグで要約に付加 | **これが最重要**: Compaction 後もワークスペースの絶対ルールを失わない仕組み。HGK の SACRED_TRUTH.md に相当 |
| **identifier 保持ポリシー** | `resolveIdentifierPreservationInstructions()` — strict/custom/off の3モード。UUID, ハッシュ, API キー等を「そのまま保持」する指示を要約プロンプトに注入 | ID の改変防止。HGK の BC-6 (TAINT 追跡) と構造的に一致 |
| **split turn 対応** | `isSplitTurn` + `turnPrefixMessages` — ターン途中で Compaction が走った場合、prefix の要約を別途生成して結合 | 非同期 Compaction の安全性確保 |

**パイプライン実行 (compact.ts) の重要な流れ**:

```
1. モデル解決 + API キー取得
2. サンドボックスコンテキスト解決
3. セッションヘッダー確保
4. Skills スナップショット適用
5. ブートストラップコンテキストファイル読み込み
6. ツール生成 + Google 用サニタイズ
7. システムプロンプト構築 (時刻, タイムゾーン, Shell, Skill, Docs 等)
8. セッションライトロック取得 (5分タイムアウト)
9. セッションファイル修復 (壊れた JSONL の復旧)
10. 履歴サニタイズ → Gemini/Anthropic バリデーション
11. 履歴ターン数制限 → tool_use/tool_result ペアリング修復
12. before_compaction Hook (fire-and-forget: セッションファイルの並列処理)
13. 診断メトリクス記録 (messages, historyTextChars, toolResultChars, estTokens, top3 contributors)
14. session.compact() 実行 (5分安全タイムアウト付き)
15. tokensAfter 推定 + sanity check (tokensBefore より大きければ破棄)
16. after_compaction Hook (fire-and-forget)
17. レーンキューイング: session lane 内で global lane を逐次実行 (デッドロック防止)
```

**診断メトリクス**:

compact.ts が記録する `[compaction-diag]` ログ:

- `pre.messages`, `pre.historyTextChars`, `pre.toolResultChars`, `pre.estTokens`
- `post.messages`, `post.historyTextChars`, `post.toolResultChars`, `post.estTokens`
- `delta.*` — 前後差分
- `top3 contributors` — 最もトークンを消費したメッセージ (role + chars + tool)
- `outcome` — compacted / failed
- `reason` — classifyCompactionReason() で 8 カテゴリに分類: `no_compactable_entries`, `below_threshold`, `already_compacted_recently`, `guard_blocked`, `summary_failed`, `timeout`, `provider_error_4xx`, `provider_error_5xx`, `unknown`

**OpenClaw の欠陥と HGK の回避策**:

| 設計原則 | OpenClaw | HGK 目標 |
|:---------|:---------|:---------|
| 履歴送信 | 全件送信 → 後で圧縮 | **関連チャンクのみ選択送信** (F2 ノート構造) |
| ツール出力 | 全量保存 → stripToolResultDetails | **送信前に strip** |
| セッション単位 | 無期限蓄積 | F2 ノート化で自然分割 |
| 復元方法 | 全履歴ロード | F1 マザーブレインが関連ノートを push |
| critical rules 保持 | AGENTS.md から "Red Lines" を抽出注入 (2000字上限) | SACRED_TRUTH.md / BC ルールは常にシステムプロンプトに含む (非圧縮) |

**HGK 転用ポイント** (増強):

1. **3段フォールバック** → HGK の Compaction は `summarizeWithFallback()` のパターンを採用すべき。全体失敗 → 部分試行 → メタ情報返却の3段構え
2. **identifier 保持ポリシー** → N-10 TAINT 追跡と統合。Compaction 後も ID の改変を防止する指示を要約プロンプトに注入
3. **ワークスペースルール保持** → Compaction 後も SACRED_TRUTH.md / BC の内容を失わない仕組み。`<workspace-critical-rules>` タグパターンを採用
4. **ツール失敗収集** → 前回セッションの失敗を Compaction 要約に保持 → `/boot` 時に同じ失敗を回避
5. **診断メトリクスと分類** → Compaction の成功/失敗を8カテゴリで自動分類し、Sympatheia の WBC に連携
6. **レーンキューイング** → Colony Worker 間の Compaction 競合を session lane + global lane で防止
7. **adaptive chunk ratio** → メッセージサイズに応じたチャンクサイズ自動調整。固定値ではなく `computeAdaptiveChunkRatio()` パターン
8. **Hook 連携** → `before_compaction` / `after_compaction` フックで Plugin が Compaction イベントを監視・処理可能

**`/noe+` 深層洞察 — Compaction の普遍構造**:

> **普遍原理**: Compaction は、情報の**非可逆圧縮**を段階的に実行する**最適制御問題**である。
> 制約は「LLM コンテキストウィンドウ」、目的関数は「意思決定・TODO・制約の残存率」。
> 最適解は存在せず、ヒューリスティックの連鎖で近似する。
>
> **FEP 翻訳**: コンテキストウィンドウ = 感覚状態の帯域幅。要約 = 生成モデルのパラメータ更新。
> 「情報劣化を最小化しつつ帯域制約に適合する」は、変分推論 (variational inference) そのもの。

**4つの設計ジレンマ** — この454行が解決しようとしているもの:

| ジレンマ | 緊張の両極 | 解決策 |
|:---------|:----------|:-------|
| **情報量 vs 処理量** | 会話が長いほど文脈が豊か。だがコンテキストは有限 | 段階的要約 — 情報の階層的圧縮 |
| **精度 vs 安全性** | `chars/4` 推定は不正確。正確さを追求すると遅い | `SAFETY_MARGIN = 1.2` — 精度を犠牲にして安全マージン |
| **完全性 vs 可要約性** | 巨大メッセージは要約不能。だが捨てると情報が消える | `isOversizedForSummary()` — 「要約を諦める」という判断を受容 |
| **構造保全 vs 容量削減** | メッセージを落とすと tool_use/result のペアが壊れる | `repairToolUseResultPairing()` — 落とした後に修復する |

**再帰的圧縮パターン** (safeguard.ts L253-314) — これが最も深い設計:

```
新コンテンツ (tokensBefore) がコンテキストの50%を超えた場合:
  → pruneHistory() で古いメッセージを落とす
  → 落としたメッセージを summarizeInStages() で要約
  → その要約を effectivePreviousSummary として「次の要約に注入」
```

これは**記憶の記憶**。詳細は失われるが、上位の抽象表現は維持される。
FEP で言い直せば、**生成モデルの階層的更新**。感覚データ (メッセージ) は消えるが、
そこから学んだ予測分布 (要約) は次世代に引き継がれる。

**`<workspace-critical-rules>` の意味論** (safeguard.ts L166-192):

AGENTS.md の `Session Startup` と `Red Lines` を Compaction 後の要約に**注入**する。
つまり: **行動規範は、非可逆圧縮で消えない。**

これは HGK にとって最重要の設計参照。HGK の `SACRED_TRUTH.md` と `behavioral_constraints.md` は
Compaction 後も必ず生き残らなければならない。OpenClaw はそれを safeguard レイヤーで保証している。

HGK への問い: **BC は要約に注入するのか、それともシステムプロンプトに常駐させるのか？**
OpenClaw は前者 (要約注入, 2000字上限)。HGK は後者 (常駐) を選ぶべき — なぜなら、要約注入は
LLM が「ルールとして認識する」ことを保証しない。システムプロンプトに常に含めることで、
「ルールは圧縮対象外」という環境的保証を得る。

#### T-02: Context Window Guard

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `src/agents/context-window-guard.ts` (75行) |
| **AMBITION 対応** | F4 BC-18 Quota メーター |
| **優先度** | 🔴 最重要 |

**定数** (SOURCE: L3-4):

| 定数 | 値 | 意味 |
|:-----|:--|:-----|
| `CONTEXT_WINDOW_HARD_MIN_TOKENS` | 16,000 | これ以下は**ブロック** (LLM が機能しない最小値) |
| `CONTEXT_WINDOW_WARN_BELOW_TOKENS` | 32,000 | これ以下は**警告** (品質低下リスク) |

**コンテキストウィンドウ解決チェーン** (`resolveContextWindowInfo()` L21-50):

```
1. modelsConfig (最優先): cfg.models.providers[provider].models[modelId].contextWindow
   → ユーザーがモデル固有に設定したウィンドウサイズ
2. model (SDK 提供): model.contextWindow
   → SDK が返すモデルのデフォルトウィンドウ
3. default: params.defaultTokens
   → システムデフォルト (DEFAULT_CONTEXT_TOKENS)
4. agentContextTokens (キャップ): cfg.agents.defaults.contextTokens
   → 上記いずれかの値が agentContextTokens より大きい場合、キャップして制限
```

**agentContextTokens キャップの意味**: モデルが 200K トークンを持っていても、`agents.defaults.contextTokens = 100000` で強制的に 100K に制限できる。コスト制御に有用。

**ガード評価** (`evaluateContextWindowGuard()` L57-74):

| 条件 | shouldWarn | shouldBlock |
|:-----|:-----------|:------------|
| tokens >= 32,000 | false | false |
| 16,000 <= tokens < 32,000 | true | false |
| 0 < tokens < 16,000 | true | true |

**HGK 転用ポイント** (増強):

1. **キャップパターン** → Ochēma の Token Vault と連携。モデルの公称ウィンドウではなく、Creator 設定でコスト制限を強制
2. **2段ガード (warn/block)** → HGK の Peira ヘルスチェックに直接組み込み。warn 時は Sympatheia に通知、block 時はタスク実行を停止
3. **defaultTokens フォールバック** → モデル情報が不完全な場合のセーフティネット。HGK の auto モデル選択時に必要
4. **normalizePositiveInt() ユーティリティ** → 設定値の不正な型・値を安全に処理するパターン

**`/noe+` 深層洞察 — 75行が教える設計哲学**:

> **普遍原理**: **制約は敵ではなく設計ツールである。** コンテキストウィンドウを「限界」として嘆くのではなく、
> 精度チューニングの入力パラメータとして積極的に使う。`agentContextTokens` cap は「200Kを64Kに絞る」操作 —
> これは品質のための意図的縮退。大きいウィンドウは attention が拡散し、distant context の影響が薄まる。

**`tokens > 0` の意味論**:
`shouldWarn: tokens > 0 && tokens < warnBelow` — 0 の場合は warn しない。なぜか？
**0 は「不明」。不明な状態で警告を出すのは false positive の源泉**。
FEP: 精度 (precision) が低い信号は抑制される。不明 → 沈黙は正しい選択。

**反論 (Z-6)**: 16K/32K のハードコード閾値は**世代依存**。2026年のモデルでは妥当だが、
次世代で文脈ウィンドウが10倍になれば? HGK は `hardMin = contextWindow * minRatio` のように
**比率ベース**にすべき。絶対値ではなく、モデルの能力に対する相対制約として設計する。

### 2.3 Skill・Plugin システム

#### T-05: Skill System (バックエンド)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル群** | `src/agents/skills/` (17ファイル, 核心: `workspace.ts` 761行) — Skill のライフサイクル全体を管理 |
| **AMBITION 対応** | F10 Plugin OS L1 (Skills 層) |
| **優先度** | 🟠 高 |

**ファイル構成**:

| ファイル | サイズ | 役割 |
|:---------|:------|:-----|
| `workspace.ts` | 761行 | ワークスペース内 Skill の検出・ロード・マージ・プロンプト生成・同期 |
| `frontmatter.ts` | 3.6KB | SKILL.md の YAML frontmatter パース・検証 |
| `plugin-skills.ts` | 2.5KB | Plugin 内 Skill の統合 |
| `refresh.ts` | 6.6KB | Skill の動的リロード |
| `config.ts` | 3.2KB | Skill 設定管理 + bundled allowlist |
| `filter.ts` | 1KB | Skill フィルタリング |
| `env-overrides.ts` | 5.8KB | 環境変数による Skill 設定上書き |
| `types.ts` | 2.1KB | Skill 型定義 (SkillEntry, SkillSnapshot 等) |

**6段ソース優先度チェーン** (SOURCE: workspace.ts L369-388):

```
extra (最低) < bundled < managed < agents-skills-personal < agents-skills-project < workspace (最高)
```

| ソース | ディレクトリ | 意図 |
|:-------|:-----------|:-----|
| `extra` | config で指定 + Plugin Skill | 外部追加 Skill |
| `bundled` | 同梱ディレクトリ | OpenClaw が提供する52 Skill |
| `managed` | `~/.openclaw/skills/` | ユーザーがインストールした Skill |
| `agents-personal` | `~/.agents/skills/` | ユーザー個人の Agent Skill |
| `agents-project` | `<workspace>/.agents/skills/` | プロジェクト固有の Agent Skill |
| `workspace` | `<workspace>/skills/` | ワークスペース直下 (最優先) |

同名の Skill は **後付けが勝つ** (Map.set で上書き)。これにより workspace の Skill が常に最優先。

**5段制限定数** (SOURCE: workspace.ts L95-99):

| 定数 | デフォルト | 意味 |
|:-----|:---------|:-----|
| `MAX_CANDIDATES_PER_ROOT` | 300 | 1ディレクトリで走査する子ディレクトリの上限 |
| `MAX_SKILLS_LOADED_PER_SOURCE` | 200 | 1ソースからロードする Skill の上限 |
| `MAX_SKILLS_IN_PROMPT` | 150 | システムプロンプトに含める Skill の上限 |
| `MAX_SKILLS_PROMPT_CHARS` | 30,000 | システムプロンプトの Skill セクション文字数上限 |
| `MAX_SKILL_FILE_BYTES` | 256,000 (256KB) | 個々の SKILL.md ファイルサイズ上限 |

**プロンプト文字数制限** (`applySkillsPromptLimits()` L408-444):

- まず `MAX_SKILLS_IN_PROMPT` で件数制限
- それでも `MAX_SKILLS_PROMPT_CHARS` を超える場合、**二分探索**で最大収まる prefix を発見
- `truncatedReason: "count" | "chars" | null` で切り詰めの理由を追跡

**トークン節約** (`compactSkillPaths()` L35-53):

- ホームディレクトリのフルパスを `~` に置換
- 例: `/Users/alice/.bun/skills/github/SKILL.md` → `~/.bun/.../skills/github/SKILL.md`
- **Skill 1つあたり 5-6 トークン節約 × N Skills ≈ 400-600 トークン節約**

**nested skills root 検出** (`resolveNestedSkillsRoot()` L178-206):

- `<dir>/skills/*/SKILL.md` パターンを検出し、`<dir>/skills/` を真のルートとして扱う
- 最大100エントリをスキャン (ヒューリスティック)

**サンドボックス Skill 同期** (`syncSkillsToWorkspace()` L589-645):

- `sourceWorkspaceDir` から `targetWorkspaceDir` へ Skill を物理コピー
- `resolveSandboxPath()` でパストラバーサル防止
- `serializeByKey()` で同時コピー競合を防止

**コマンドスペック生成** (`buildWorkspaceSkillCommandSpecs()` L654-760):

- Skill 名をサニタイズ: `[^a-z0-9_]` を `_` に置換、最大32文字
- 重複回避: `resolveUniqueSkillCommandName()` でサフィックス付与 (e.g., `github_2`)
- `command-dispatch: tool` + `command-tool: <name>` でツール直接ディスパッチ対応
- Discord コマンド説明は100文字制限

**HGK 転用ポイント** (増強):

1. **6段優先度チェーン** → HGK の Skill/Plugin ロード時の衝突解決ルール。HGK も `workspace > project > personal > bundled` の優先度チェーンを実装すべき
2. **5段制限定数** → 暴走防止。特に `MAX_SKILL_FILE_BYTES` は外部 Skill のサイズ爆発を防ぐ
3. **二分探索によるプロンプト制限** → 固定件数ではなく文字数ベースの動的制限。LLM のコンテキストウィンドウに適合
4. **トークン節約 (パス圧縮)** → HGK のシステムプロンプトにも適用可能。`~` 置換 = 無料のトークン節約
5. **サンドボックス同期** → Colony Worker / サンドボックス環境への Skill 安全転送
6. **nested skills root 検出** → HGK の `.agent/skills/` 直下に `skills/` サブディレクトリがある場合の自動対応

---

#### T-06: Hooks System

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル群** | `plugins/hooks.ts` (754行) + `hook-runner-global.ts` (89行) + `gateway/hooks.ts` (410行) + `gateway/hooks-mapping.ts` — 計 ~1,253 行 |
| **AMBITION 対応** | F10 Plugin OS E4 (Hooks 層) |
| **優先度** | 🟠 高 |

**2つの実行モード** (SOURCE: hooks.ts L194-255):

| モード | 関数 | 実行順序 | 戻り値 | 用途 |
|:-------|:-----|:---------|:------|:-----|
| **Void** | `runVoidHook()` | **並列** (Promise.all) | なし | 監視・ロギング系 (fire-and-forget) |
| **Modifying** | `runModifyingHook()` | **逐次** (priority 順) | マージ結果 | イベントの変更・ブロック系 |

priority ソートは `(b.priority ?? 0) - (a.priority ?? 0)` — **高い値が先に実行**。

**22 フック × 5 カテゴリ** (SOURCE: hooks.ts L716-750):

| カテゴリ | フック | モード | 用途 |
|:---------|:------|:------|:-----|
| **Agent** | `before_model_resolve` | Modifying | モデル/プロバイダーのオーバーライド |
| | `before_prompt_build` | Modifying | システムプロンプト注入 |
| | `before_agent_start` | Modifying | レガシー (model + prompt 統合) |
| | `llm_input` | Void | LLM 入力の監視 |
| | `llm_output` | Void | LLM 出力の監視 |
| | `agent_end` | Void | 会話完了の分析 |
| | `before_compaction` | Void | Compaction 前の処理 |
| | `after_compaction` | Void | Compaction 後の処理 |
| | `before_reset` | Void | /new, /reset 前の保存 |
| **Message** | `message_received` | Void | 受信メッセージ監視 |
| | `message_sending` | Modifying | 送信メッセージの変更/キャンセル |
| | `message_sent` | Void | 送信完了の通知 |
| **Tool** | `before_tool_call` | Modifying | ツール呼び出しの変更/ブロック |
| | `after_tool_call` | Void | ツール呼び出し完了の通知 |
| | `tool_result_persist` | **同期** | ツール結果の永続化前変換 |
| **Message Write** | `before_message_write` | **同期** | セッション JSONL 書き込み前のブロック/変更 |
| **Session** | `session_start` / `session_end` | Void | セッションライフサイクル |
| | `subagent_spawning` / `subagent_spawned` / `subagent_ended` / `subagent_delivery_target` | Mixed | サブエージェント管理 |
| **Gateway** | `gateway_start` / `gateway_stop` | Void | Gateway ライフサイクル |

**同期フックの Promise 検出ガード** (SOURCE: hooks.ts L487-496):
`tool_result_persist` と `before_message_write` は同期フック。ハンドラが Promise を返した場合、**自動検出してログ警告 + 無視**する。catchErrors=false 時は例外を投げる。ホットパスでの async 混入事故を防止。

**マージ戦略** (modifying フック):

| フック | マージルール |
|:-------|:-----------|
| `before_model_resolve` | 最初の non-undefined が勝つ (高 priority 優先) |
| `before_prompt_build` | systemPrompt: 後付け勝ち / prependContext: 連結 (改行2つ) |
| `message_sending` | content: 後付け / cancel: 後付け |
| `before_tool_call` | params + block + blockReason: 各フィールド後付け |
| `subagent_spawning` | error あれば即停止 / threadBindingReady: OR 結合 |
| `subagent_delivery_target` | 最初の origin 定義が勝つ |

**グローバルシングルトン** (`hook-runner-global.ts`):

- `initializeGlobalHookRunner()`: Gateway 起動時に1回呼ばれる
- `getGlobalHookRunner()`: どこからでも HookRunner にアクセス
- `catchErrors: true` (本番環境ではフック失敗はログのみ、メイン処理は続行)

**HGK 転用ポイント** (増強):

1. **Void/Modifying の2モード** → HGK の Plugin Hook を同じパターンで実装。並列 (監視用) と逐次 (変更用) を明確に分離
2. **同期フック + Promise 検出ガード** → ホットパス (JSONL 書き込み) で async 混入を自動検出。HGK の Handoff/ROM 書き込みに適用
3. **マージ戦略の明示化** → 複数 Plugin が同じフックに登録した場合の衝突解決ルール。「最初が勝つ」vs「後付けが勝つ」vs「連結」を設計時に決定
4. **priority ソート** → 数値順で実行順序を制御。HGK BC の優先度と連動可能
5. **before_tool_call のブロック機能** → N-4 (Proposal First) のフロントエンド実装。Plugin がツール呼び出しをブロックできる
6. **before_compaction / after_compaction** → Compaction イベントに Plugin を接続。T-01 で確認した Hook 連携の実体

---

### 2.4 セッション管理

#### T-07: Session Utils

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル群** | `session-utils.ts` (909行, 29関数) + `session-utils.fs.ts` (744行, 41関数) + `sessions-patch.ts` (~400行) — 計 ~2,053 行 |
| **AMBITION 対応** | F2 セッション=ノート |
| **優先度** | 🟡 中 |

**セッションキー解決チェーン** (`resolveGatewaySessionStoreTarget()`):

```
1. canonicalKey = canonicalizeSessionKeyForAgent(agentId, key)
2. storePath = resolveSessionFilePath() (Agent 別ディレクトリ)
3. legacy key スキャン: findStoreMatch() で大文字小文字の揺れを吸収
4. pruneLegacyStoreKeys() でレガシーキーをストアから除去
5. → { agentId, storePath, canonicalKey, storeKeys }
```

**セッション分類** (`classifySessionKey()`): `main` / `subagent` / `group` / `thread` / `custom`

**Agent 横断統合ストア** (`loadCombinedSessionStoreForGateway()`):

- 全 Agent の sessions.json を読み込み → 1つの結合ストアにマージ
- 同一 canonicalKey の衝突: **最新タイムスタンプが勝つ** (`mergeSessionEntryIntoCombined()`)

**トランスクリプトファイル操作** (session-utils.fs.ts):

| 機能 | 関数 | 詳細 |
|:-----|:-----|:-----|
| **タイトル生成** | `readSessionTitleFieldsFromTranscript()` | 先頭8KBチャンクからユーザーメッセージを抽出 → タイトル自動生成 (最大60文字) |
| **タイトルキャッシュ** | `sessionTitleFieldsCache` | mtime+size ベース (最大5,000エントリ, LRU 風) |
| **アーカイブ** | `archiveSessionTranscripts()` | セッションファイルを `.archived.{timestamp}.{reason}.jsonl` にリネーム |
| **アーカイブクリーンアップ** | `cleanupArchivedSessionTranscripts()` | `olderThanMs` 経過したアーカイブを物理削除 |
| **プレビュー読込** | `readLastMessagePreviewFromTranscript()` | 末尾16KB/20行から最新メッセージをプレビュー |
| **サイズ制限** | `capArrayByJsonBytes()` | JSON シリアライズ後のバイト数で配列を切り詰め |

**セッションパッチ** (sessions-patch.ts):

- `label`, `thinkingLevel`, `verboseLevel`, `reasoningLevel`, `model`, `modelProvider` の6フィールドをパッチ可能
- パッチ適用後に sessions.json を書き戻し

**HGK 転用ポイント** (増強):

1. **canonicalKey + legacy キー吸収** → HGK のセッション管理でキーの揺れを安全に正規化 (Handoff ファイル名の一貫性)
2. **Agent 横断統合ストア** → Colony Worker 間のセッション状態を1箇所で可視化
3. **タイトル自動生成 + キャッシュ** → Kairos Handoff のタイトル自動付与 (最大60文字, 5000エントリキャッシュ)
4. **アーカイブ + クリーンアップ** → Handoff の自動アーカイブ + 古いファイルの定期削除

---

### 2.5 メモリ・検索

#### T-08: Model Fallback/Selection (深掘り済み)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル群** | 4ファイル, 合計 ~1,700行 |
| **AMBITION 対応** | F9 Agent 並列 (モデルルーティング) + F4 AI 指揮台 |
| **優先度** | 🟡 中 |

**ファイル構成**:

| ファイル | 行数 | 役割 |
|:---------|:-----|:-----|
| `model-selection.ts` | 615 | プロバイダ正規化、エイリアス、allowlist、Agent 別モデル解決 |
| `model-fallback.ts` | 571 | フォールバック候補構築、クールダウン判定、試行ループ |
| `failover-error.ts` | 251 | FailoverReason 型定義、エラー分類・正規化 |
| `model-catalog.ts` | 267 | モデルカタログ管理 (キャッシュ付き) |

**Model Selection — モデル解決チェーン**:

```
ユーザー入力 ("opus-4.6")
  ↓ エイリアス変換 (opus-4.6 → claude-opus-4-6)
  ↓ プロバイダ正規化 (anthropic, google, openai 等の表記揺れ吸収)
  ↓ ModelRef = { provider: "anthropic", model: "claude-opus-4-6" }
  ↓ Allowlist チェック (agents.defaults.models の keys)
  ↓ Agent Override チェック (agentConfig?.model > agents.defaults)
  ↓ 最終 ModelRef
```

- `resolveDefaultModelForAgent()` — Agent 別にモデルレイヤーを解決
- `resolveSubagentSpawnModelSelection()` — サブエージェント用: modelOverride → agentConfig.subagents.model → defaults.subagents.model → agentConfig.model → defaults.model
- `buildAllowedModelSet()` — allowlist がない場合は全カタログ許可、ある場合は allowlist + default のみ。カタログに未登録でも allowlist にあれば synthetic entry 生成

**Model Fallback — フォールバック実行ループ**:

```
resolveFallbackCandidates():
  1. normalizedPrimary (ユーザー指定)
  2. configuredFallbacks (agents.defaults.model.fallbacks)
  3. configuredPrimary (config のデフォルト)
  → 重複排除 + allowlist チェック

runWithModelFallback():
  for candidate in candidates:
    1. Auth Profile クールダウンチェック
    2. CooldownDecision:
       - persistent (auth/billing) → 全スキップ
       - transient (rate_limit) → 別モデルで再挑戦
    3. 試行: params.run(provider, model)
    4. 成功 → 結果返却
    5. 失敗 → エラー分類:
       - AbortError → 即座に rethrow
       - context overflow → 即座に rethrow (小さいモデルは逆効果)
       - FailoverError → 次の候補へ
       - Unknown → 最後の候補なら rethrow、残りがあれば続行
```

**FailoverReason 型** (エラー分類体系):

| Reason | HTTP Status | 意味 | フォールバック |
|:-------|:-----------|:-----|:-------------|
| `billing` | 402 | 課金問題 | ❌ 全スキップ |
| `rate_limit` | 429 | レート制限 | ✅ 別モデルで回復可能 |
| `auth` | 401 | 認証失敗 | ❌ 全スキップ |
| `auth_permanent` | 403 | 永続的認証失敗 | ❌ 全スキップ |
| `timeout` | 408/502/503/504 | タイムアウト | ✅ 別モデルで |
| `format` | 400 | リクエスト形式不正 | ✅ 別モデルで |
| `model_not_found` | 404 | モデル未発見 | ✅ 別モデルで |

**プローブ制御** (クールダウン中の回復チェック):

- `MIN_PROBE_INTERVAL_MS = 30,000` — 30秒間隔でプロバイダの回復を確認
- `PROBE_MARGIN_MS = 120,000` — クールダウン期限の2分前にプローブ開始
- プライマリモデルのみプローブ (フォールバック候補はプローブしない)
- `resolveProbeThrottleKey()` — provider + agentDir でスコープ化

**HGK 転用ポイント**:

1. **FailoverReason 体系** → HGK の Ochema/Cortex API エラーを同じ体系で分類可能
2. **クールダウン + プローブ** → Gemini quota 枯渇時に Claude へ自動転換、回復を30秒毎に確認
3. **Agent 別モデルオーバーライド** → Colony Worker ごとに最適モデルを指定 (安い Worker は Flash、高品質は Opus)
4. **Allowlist** → Creator が許可するモデルのみ使用 (コスト管理)
5. **Context overflow 即 rethrow** → 賢い判断。小さいウィンドウのモデルに逃げるのは悪化の一途

#### T-09: Memory Search Pipeline — MMR + Temporal Decay (再深掘り)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル群** | 7ファイル, 合計 ~2,400行 |
| **AMBITION 対応** | F1 (知識検索品質) + F2 (セッション記憶) |
| **優先度** | 🟠 高 (検索パイプラインの設計全体が価値) |

**ファイル構成**:

| ファイル | 行数 | 役割 |
|:---------|:-----|:-----|
| `manager.ts` | 641 | `MemoryIndexManager` — 最上位。全検索フロー統合 |
| `search-manager.ts` | 239 | `FallbackMemoryManager` — QMD→builtin の2層フォールバック |
| `hybrid.ts` | 150 | `mergeHybridResults()` — ベクトル+FTS 統合の核 |
| `manager-search.ts` | 192 | SQLite 検索層 (vector + FTS) |
| `mmr.ts` | 215 | MMR リランキング |
| `temporal-decay.ts` | 168 | 時間減衰 |
| `query-expansion.ts` | 807 | 7言語 FTS クエリ展開 |

**検索パイプライン全体像** — 2つのモード:

```
┌──── Mode A: FTS-only (embedding provider なし) ────────────────────┐
│                                                                     │
│  query → extractKeywords() → [keyword1, keyword2, ...]              │
│    ↓ ×N (各 keyword で並列検索)                                     │
│  searchKeyword() → BM25 → 1/(1+rank) でスコア正規化                │
│    ↓                                                                │
│  重複排除 (id ベースで max score 採用)                               │
│    ↓                                                                │
│  sort → minScore フィルタ → maxResults 切り捨て                     │
└─────────────────────────────────────────────────────────────────────┘

┌──── Mode B: Hybrid (embedding provider あり) ───────────────────────┐
│                                                                     │
│  query → embedding → queryVec                                       │
│    ↓                                                                │
│  ┌─── 並列実行 ──────────────────────────────────┐                  │
│  │ searchVector()                                 │                  │
│  │   sqlite-vec: vec_distance_cosine()            │                  │
│  │   fallback: 全チャンク cosine 手動計算          │                  │
│  │   score = 1 - distance (cosine similarity)     │                  │
│  │                                                │                  │
│  │ searchKeyword()                                │                  │
│  │   FTS5: BM25 ランキング                        │                  │
│  │   score = 1/(1+rank)                           │                  │
│  └────────────────────────────────────────────────┘                  │
│    ↓                                                                │
│  mergeHybridResults():                                              │
│    1. ID ベースマージ (同一チャンクの vector/text スコア統合)         │
│    2. score = vectorWeight × vectorScore + textWeight × textScore    │
│    3. Temporal Decay: score × e^(-ln2/halfLifeDays × age)            │
│       - Evergreen 免除 (MEMORY.md, トピックファイル)                 │
│       - 日付ソース: ファイルパス YYYY-MM-DD.md > mtime               │
│    4. Sort (降順)                                                   │
│    5. MMR リランキング (opt-in):                                    │
│       MMR = λ×relevance - (1-λ)×max_jaccard_to_selected             │
│       λ=0.7: 関連性70%, 多様性30%                                   │
│    ↓                                                                │
│  minScore フィルタ → maxResults 切り捨て                             │
└─────────────────────────────────────────────────────────────────────┘
```

**候補数戦略**: `candidates = maxResults × candidateMultiplier` (max 200)
→ 最終結果数より多くの候補を取得し、MMR/Decay 後に切り捨て。精度を犠牲にしない設計。

**Embedding プロバイダ** (6種):

- OpenAI, Gemini, Voyage, Mistral, Local (node-llama), Auto (自動選択)
- プロバイダ障害時: FTS-only モードに graceful degradation
- バッチ埋め込み: 並列実行 + failure limit (2回失敗で停止)

**FallbackMemoryManager** — 2層フォールバック:

```
QMD (外部メモリバックエンド)
  ↓ 失敗
MemoryIndexManager (builtin SQLite)
  ↓ 失敗
null (検索不可)
```

- `primaryFailed` フラグで不可逆切替 (1度失敗 → 永続的に fallback)
- キャッシュ eviction: 失敗した wrapper をキャッシュから除去 → 次回リクエストで QMD 再試行

**SQLite 検索層の2段フォールバック** (`searchVector()`):

1. `sqlite-vec` 拡張: `vec_distance_cosine()` で高速ベクトル検索
2. 拡張なし: 全チャンクを読み込み → 手動 `cosineSimilarity()` 計算 → ソート

**HGK 転用ポイント (パイプラインレベル)**:

1. **Hybrid Search の ID マージ方式** → Periskopē の multi-source 結果統合に直接適用。現在のスコア統合ロジックを改善可能
2. **candidateMultiplier** → 取りすぎて後でフィルタする戦略は Periskopē でも採用すべき
3. **FTS-only degradation** → embedding API が落ちた時に FTS で検索を継続。Mneme に適用可能
4. **Temporal Decay の Evergreen 免除** → HGK の kernel/ ドキュメントは減衰させない、handoff は減衰させる
5. **2層フォールバック** → Model Fallback と同じ設計思想。HGK 全体で統一するべきパターン

#### T-10: Query Expansion (再深掘り)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `query-expansion.ts` (807行) |
| **AMBITION 対応** | F1 (FTS 精度向上) |
| **優先度** | 🟡 中 |

**パイプライン内の位置**: Mode A (FTS-only) でのみ発動。Mode B (Hybrid) では embedding が意味検索を担うため不要。

**7言語ストップワード辞書** (合計 ~500語):

| 言語 | 単語数 | 特殊処理 |
|:-----|:-------|:--------|
| English | ~118 | なし |
| Spanish | ~55 | なし |
| Portuguese | ~55 | なし |
| Arabic | ~55 | なし |
| Korean | ~90 | **助詞ストリッピング** (`를/는/이/가` 等16種、最長一致) |
| Japanese | ~40 | なし |
| Chinese | ~90 | なし |

**CJK トークナイゼーション** — 言語別に異なる戦略:

```
中国語: "讨论方案" → ["讨", "论", "方", "案", "讨论", "论方", "方案"]
         (unigram + bigram — セグメンターなしの近似)

日本語: "APIバグ修正" → ["api", "バグ", "修正"]
         (スクリプト分離: ASCII / カタカナ / 漢字 を別トークン)
         漢字連続: "修正" → ["修正", "修正"] (2文字以上はそのまま)

韓国語: "API를" → ["api를", "api"]
         (助詞ストリッピング + 原型保持。isUsefulKoreanStem() で1文字排除)
```

**`expandQueryWithLlm()`**: LLM による意味展開 (オプション)。失敗 → ローカル `extractKeywords()` にフォールバック。

**HGK 転用ポイント**:

1. **FTS-only モードでの relevance 向上** → Mneme FTS 検索時のクエリ前処理に適用
2. **日本語ストップワード** → HGK の日本語検索品質向上 (ただし40語は少ない、追加が必要)
3. **CJK bigram** → Periskopē の多言語検索で中国語/日本語の n-gram を改善可能
4. **LLM 展開 → ローカルフォールバック** — Periskopē の W3 と同じ思想

---

### 2.6 UI コンポーネント

#### T-11: Skills 管理ビュー

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル群** | 7ファイル, 合計 ~980行 |
| **AMBITION 対応** | F10 Plugin OS (Skills 管理画面) |
| **優先度** | 🟢 参考 |

**コンポーネント構成**:

| ファイル | 行数 | 役割 |
|:---------|:-----|:-----|
| `views/skills.ts` | 193 | グローバル Skills 一覧 (カード形式) |
| `views/skills-grouping.ts` | 41 | 4グループ自動分類 (workspace/built-in/installed/extra) |
| `views/skills-shared.ts` | 53 | ステータスチップ (source/eligible/disabled) |
| `views/agents-panels-tools-skills.ts` | 538 | Agent 別 Tool + Skill allowlist 管理 |
| `controllers/skills.ts` | 158 | CRUD: loadSkills / updateSkillEnabled / saveSkillApiKey / installSkill |

**UI パターン (HGK 転用に有用)**:

- `<details>` による折りたたみグループ — Skill が多い場合の整理
- フィルタ検索 + 件数表示 (`X shown`)
- Enable/Disable トグル + API キー入力の組み合わせ
- `cfg-toggle` カスタム CSS トグルスイッチ
- 「Quick Presets」ボタン群 (full/safe/minimal) でプロファイル一括切替
- `callout info/warn/danger` による状態メッセージ
- Busy 状態管理 (操作中のボタン無効化 + "Installing…" 表示)

---

#### T-12: Sessions 一覧ビュー

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル群** | 2ファイル, 合計 450行 |
| **AMBITION 対応** | F2 セッション=ノート (管理画面) |
| **優先度** | 🟢 参考 |

**コンポーネント構成**:

| ファイル | 行数 | 役割 |
|:---------|:-----|:-----|
| `views/sessions.ts` | 322 | セッションテーブル (9列) |
| `controllers/sessions.ts` | 128 | CRUD: loadSessions / patchSession / deleteSession |

**テーブル列**: Key / Label / Kind / Updated / Tokens / Thinking / Verbose / Reasoning / Actions

**UI パターン (HGK 転用に有用)**:

- テーブル形式 + フィルタ (activeMinutes, limit, checkbox)
- インライン編集: `<input>` でラベル変更、`<select>` でレベル設定
- `formatRelativeTimestamp()` — 相対時間表示 ("2h ago")
- `formatSessionTokens()` — トークン数のフォーマット
- セッションキーからチャットビューへの直接リンク
- 確認ダイアログ付き削除

---

### 2.7 マルチエージェント (Subagent) — 深掘り済み

> **全22ファイル, 合計 ~3,000行のサブシステム。HGK の F6 Colony / F9 Agent 並列の設計参照として最も価値が高い。**

| 項目 | 詳細 |
|:-----|:-----|
| **AMBITION 対応** | F6 Colony (多エージェント協調) + F9 並列実行 |
| **優先度** | 🟠 高 (設計参考) |

**ファイル構成 (核心4ファイル)**:

| ファイル | 行数 | 役割 |
|:---------|:-----|:-----|
| `subagent-registry.ts` | 1168 | 全 SubagentRun の CRUD, 孤児検出・復元, sweeper |
| `subagent-spawn.ts` | 551 | `spawnSubagentDirect()` — スポーン実行の全フロー |
| `agent-scope.ts` | 282 | Agent 設定解決 (モデル/skills/tools/workspace) |
| `subagent-depth.ts` | 177 | 深度追跡 (再帰チェーン・循環検出) |

**補助ファイル**:

| ファイル | 行数 | 役割 |
|:---------|:-----|:-----|
| `subagent-registry.types.ts` | 36 | SubagentRunRecord 型定義 |
| `subagent-lifecycle-events.ts` | 48 | ライフサイクル reason/outcome 型 |
| `subagent-registry-state.ts` | ~100 | 永続化 (ディスク→メモリ→ディスク) |
| `subagent-registry-queries.ts` | ~80 | requester/child 検索 |
| `subagent-registry-cleanup.ts` | ~120 | セッション削除・トランスクリプトアーカイブ |
| `subagent-registry-completion.ts` | ~100 | 完了処理・結果アナウンス |
| `subagent-announce.ts` | ~150 | requester への結果通知 |
| `subagent-announce-queue.ts` | ~80 | アナウンスキュー管理 |
| `subagent-announce-dispatch.ts` | ~100 | アナウンス配送 |

**スポーンフロー** (`spawnSubagentDirect()`):

```
1. 入力検証: task, label, agentId, model, thinking, timeout, thread, mode, cleanup
2. 深度チェック: callerDepth >= maxSpawnDepth → forbidden
3. 子数チェック: activeChildren >= maxChildrenPerAgent (default=5) → forbidden
4. Agent ID 許可チェック: subagents.allowAgents (allowlist or "*")
5. 子セッション作成: agent:{targetAgentId}:subagent:{UUID}
6. モデルオーバーライド適用: sessions.patch
7. Thinking レベル適用: sessions.patch
8. スレッドバインディング (session モード): subagent_spawning フック実行
9. システムプロンプト構築: 深度情報 + タスク + コンテキスト
10. Gateway call: agent メソッド (deliver=false, lane=subagent)
11. Registry 登録: registerSubagentRun()
12. subagent_spawned フック発火
13. 結果返却: { status: "accepted", childSessionKey, runId, mode }
```

**2つのスポーンモード**:

| モード | セッション | 完了後 | ユースケース |
|:-------|:----------|:-------|:-----------|
| `run` | 一時的 | 自動削除/保持 | 一発タスク (調査、ファイル生成等) |
| `session` | 永続 | スレッド紐付き維持 | 対話的サブタスク (thread=true 必須) |

**安全装置 (HGK Colony に直結)**:

| 安全装置 | 仕組み | デフォルト |
|:---------|:-------|:----------|
| **深度制限** | spawnDepth を再帰追跡、循環検出あり | `maxSpawnDepth` (config) |
| **子数制限** | セッションあたりの同時実行子エージェント数 | `maxChildrenPerAgent = 5` |
| **Agent 許可リスト** | `subagents.allowAgents` で許可する Agent ID を制限 | なし (同一 Agent のみ) |
| **タイムアウト** | `runTimeoutSeconds` (パラメータ or config) | 0 (無制限) |
| **孤児検出** | registry をスキャン、セッション消失を検出、自動 cleanup | sweeper で定期実行 |
| **ライフサイクルフック** | subagent_spawning / subagent_spawned / subagent_ended | Plugin 実装 |

**SubagentRunRecord (永続化レコード)**:

| フィールド | 型 | 用途 |
|:----------|:---|:-----|
| `runId` | string | 一意識別子 (UUID) |
| `childSessionKey` | string | 子セッションキー |
| `requesterSessionKey` | string | 親セッションキー |
| `task` | string | タスク内容 |
| `cleanup` | "delete" \| "keep" | 完了後の処理 |
| `model` | string? | 使用モデル |
| `spawnMode` | "run" \| "session" | スポーンモード |
| `outcome` | SubagentRunOutcome? | ok/error/timeout/killed |
| `endedReason` | EndedReason? | complete/error/killed/reset/delete |

**ライフサイクル終了理由 × 結果の直交分類**:

| EndedReason | Outcome | 発生条件 |
|:------------|:--------|:---------|
| `subagent-complete` | ok | 正常完了 |
| `subagent-error` | error | 実行中エラー |
| `subagent-killed` | killed | ユーザーによる強制停止 |
| `session-reset` | reset | セッションリセット |
| `session-delete` | deleted | セッション削除 |

**HGK 転用ポイント**:

1. **SpawnSubagentParams** → Colony Worker のスポーンパラメータ定義にそのまま使える
2. **深度制限 + 子数制限** → Colony Worker の暴走防止 (Tool Loop Detection と組み合わせ)
3. **run/session の2モード** → 一発タスク vs 対話的作業の使い分け (F9 並列実行)
4. **Agent 許可リスト** → Creator が許可する Worker タイプの制御
5. **orphan 検出 + sweeper** → 長時間実行 Colony の自動回収
6. **LifecycleEndedReason** → Worker の終了理由を構造化して追跡 (N-4 監査)
7. **announce 機構** → "do not poll/sleep" パターン = Worker 完了の push 通知 (F4 AI 指揮台)

---

## 3. 吸収対象外 (理由つき)

| モジュール | 除外理由 |
|:----------|:---------|
| TUI (ターミナル UI) | HGK は Desktop App — TUI 不要 |
| マルチチャネル (39 extensions) | HGK は Web UI 専用 — Discord/Slack 等不要 |
| ネイティブアプリ (Swift/iOS/Android) | HGK は Tauri — 別アーキテクチャ |
| Gateway サーバー本体 | HGK は Python (FastAPI) — 言語が異なる |
| 認証・デバイスペアリング | HGK はローカル専用 — 不要 |
| Cron Jobs | F1 マザーブレインの常駐機構で代替 |
| Usage/Cost タブ | ダッシュボード内で処理 (独立ビュー不要) |

---

## 4. AMBITION Feature × OpenClaw 吸収マッピング

| AMBITION | 吸収候補 | 直接転用 | 設計参考 | 不要 |
|:---------|:---------|:---------|:---------|:-----|
| **F1 マザーブレイン** | T-01 (Compaction), T-09 (MMR/Decay), T-10 (Query Expansion), T-13 (System Prompt Builder), T-22 (Transcript Repair), T-25 (Transcript Policy) | ✅ | ✅ | — |
| **F2 セッション=ノート** | T-07 (Session Utils), T-12 (Sessions UI), T-22 (Transcript Repair), T-23 (Tool Result Guard) | ✅ | ✅ | — |
| **F3 タブ・マルチタスク** | — | — | — | ✅ |
| **F4 AI 指揮台** | T-02 (Context Guard), T-04 (Exec Approval), T-11 (Tool Display), T-13 (System Prompt Builder), T-14 (Tool Policy Pipeline), T-16 (Cache Trace), T-17 (Tool Display & Command Summarization), T-18 (Security Audit Framework), T-21 (Exec Runtime) | ✅ | ✅ | — |
| **F5 仮想 Twitter フィード** | — | — | — | ✅ |
| **F6 Colony** | T-03 (Tool Loop Detection), T-15 (Session Write Lock), T-19 (Skill Code Scanner), T-21 (Exec Runtime), T-24 (Command Poll Backoff) | ✅ | ✅ | — |
| **F7 3DKB** | — | — | — | ✅ |
| **F8 Cowork UI** | T-11 (Skills UI), T-12 (Sessions UI) | — | ✅ | — |
| **F9 Agent 並列** | T-03 (Tool Loop Detection), T-08 (Model Selection), T-24 (Command Poll Backoff), T-25 (Transcript Policy) | ✅ | ✅ | — |
| **F10 Plugin OS** | T-05 (Skill System), T-06 (Hooks), T-14 (Tool Policy Pipeline), T-19 (Skill Code Scanner), T-20 (Plugin System) | ✅ | ✅ | — |

---

## 5. 優先実装順序

```
Phase 1 — 安全装置 + コンテキスト管理 (即時):
  T-01: compaction.py                   ← F1 フォールバック圧縮
  T-02: context_guard.py                ← F4 BC-18 サーバーサイド強制
  T-03: tool_loop_guard.py              ← F6/F9 暴走防止

Phase 2 — Plugin OS 加速 (中期):
  T-04: Exec Approval                   ← F4 承認フロー
  T-05: Skill System 設計参考            ← F10 L1 層
  T-06: Hooks System 設計参考            ← F10 E4 層

Phase 3 — 品質向上 (長期):
  T-07: Session Utils 設計参考           ← F2 ノート管理
  T-08: Model Fallback/Selection         ← F9 モデルルーティング
  T-09/T-10: Memory MMR + Query Expansion ← F1 検索精度
  T-11/T-12: UI パターン                 ← F8/F10 UI 設計
```

---

## 6. OpenClaw の致命的欠点（反面教師）

### 6.1 トークン消耗の構造的問題

| 欠点 | 根本原因 | HGK の回避策 |
|:-----|:---------|:------------|
| 全履歴を毎回再送信 | セッション = 単一 JSONL ファイル | F2 ノート構造による分割送信 |
| ツール出力が無制限保存 | `stripToolResultDetails()` は要約時のみ | **送信前に** strip を適用 |
| Compaction が後追い | 蓄積 → 閾値超え → LLM 要約 | 関連ノートのみ選択的に送信 |
| セッション無期限蓄積 | 明示的終了メカニズムなし | `/bye` による明示的セッション切断 + Handoff 圧縮 |

### 6.2 アーキテクチャ上の学び

- **Compaction は保険**: メインの戦略にすべきではない。予防 > 治療。
- **Tool Loop Detection は必須**: エージェント自律性が上がるほど暴走リスクも増大。
- **Skill allowlist は賢い**: 全 Skill を常時有効にしない → コンテキスト節約。
- **Context Window Guard は簡潔で効果的**: 75行で十分な保護。過剰設計不要。

---

## 7. 追加分析 (Phase A 深掘り — 2026-02-28 夜)

### 2.8 システムプロンプト構築

#### T-13: System Prompt Builder

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `src/agents/system-prompt.ts` (705行) |
| **AMBITION 対応** | F1 マザーブレイン (動的プロンプト構成) + F4 AI 指揮台 |
| **優先度** | 🟠 高 |

**モジュラーセクション構成 (16関数)**:

| 関数 | 役割 |
|:-----|:-----|
| `buildSkillsSection()` | Skill 一覧をプロンプトに挿入 |
| `buildMemorySection()` | メモリ検索の指示 (引用モード: `inline`/`footnote`/`off`) |
| `buildUserIdentitySection()` | ユーザー識別情報 (HMAC ハッシュ化表示) |
| `buildTimeSection()` | タイムゾーン付き現在時刻 |
| `buildReplyTagsSection()` | `<reply>` タグ構造 (full/minimal) |
| `buildMessagingSection()` | チャネル別メッセージングルール |
| `buildVoiceSection()` | TTS ヒント |
| `buildDocsSection()` | ドキュメント参照パス |
| `buildAgentSystemPrompt()` | **メイン関数** (476行) — 上記全セクションを組み立て |
| `buildRuntimeLine()` | ランタイム情報行 (OS, Node, model, shell) |

**設計パターン**:

- **セクション分離**: 各セクションが独立関数 → テスト可能 + 個別差し替え可能
- **PromptMode** (`full`/`minimal`/`none`): Agent 種別でプロンプトサイズを制御
  - `full`: メインエージェント (全セクション)
  - `minimal`: サブエージェント (Tooling, Workspace, Runtime のみ)
  - `none`: 基本アイデンティティ行のみ
- **HMAC ユーザーID**: `formatOwnerDisplayId()` — 表示用にハッシュ化 (プライバシー保護)
- **引用モード**: メモリ検索結果の引用形式を3段階で制御

**HGK 転用ポイント**:

1. **セクション分離アーキテクチャ** → HGK の boot_integration.py プロンプト構成をモジュール化する参考
2. **PromptMode** → Colony Worker 用 minimal vs メイン用 full の使い分け (F6)
3. **引用モード** → Periskopē 検索結果の引用形式をユーザー設定で制御

---

### 2.9 ツールポリシーパイプライン

#### T-14: Tool Policy Pipeline

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル群** | `tool-policy-pipeline.ts` (109行) + `tool-policy.ts` (5.9KB) + `pi-tools.policy.ts` (10.6KB) |
| **AMBITION 対応** | F10 Plugin OS (ツール許可制御) + F4 AI 指揮台 (権限管理) |
| **優先度** | 🟠 高 |

**7段フィルタチェーン** (`buildDefaultToolPolicyPipelineSteps()`):

```
1. tools.profile (ユーザープロファイル)
2. tools.byProvider.profile (プロバイダ別プロファイル)  
3. tools.allow (グローバル許可)
4. tools.byProvider.allow (プロバイダ別グローバル)
5. agents.{id}.tools.allow (エージェント固有)
6. agents.{id}.tools.byProvider.allow (エージェント+プロバイダ)
7. group tools.allow (グループ)
```

- 各ステップの policy が undefined ならスキップ
- `stripPluginOnlyAllowlist`: Plugin 専用 allowlist がコアツールを誤って除外しないよう保護
- `expandPolicyWithPluginGroups()`: Plugin グループの展開 (plugin:* → 個別ツール)

**HGK 転用ポイント**:

1. **多層ポリシーパイプライン** → HGK の Skill/Tool 許可制御を階層化 (Creator 設定 → Agent 設定 → グループ設定)
2. **Plugin-only allowlist 保護** → コアツールが Plugin allowlist に巻き込まれて消えるバグの防止パターン

---

### 2.10 セッション書き込みロック

#### T-15: Session Write Lock

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `src/agents/session-write-lock.ts` (505行) |
| **AMBITION 対応** | F6 Colony (並列書き込み保護) + F9 Agent 並列 |
| **優先度** | 🟡 中 |

**設計の要点**:

| 機能 | 実装 | 定数 |
|:-----|:-----|:-----|
| **再入可能ロック** | `HeldLock.count` でネスト追跡 | — |
| **stale 検出** | PID 生存チェック + `createdAt` 年齢 | `DEFAULT_STALE_MS = 30分` |
| **最大保持時間** | 自動解放タイマー | `DEFAULT_MAX_HOLD_MS = 5分` |
| **Watchdog** | 定期スキャン + 期限切れロック解放 | `DEFAULT_WATCHDOG_INTERVAL_MS = 60秒` |
| **プロセス終了ハンドラ** | SIGINT/SIGTERM/SIGQUIT/SIGABRT でクリーンアップ | — |
| **同期解放** | `releaseAllLocksSync()` — exit 時の async 不可環境対応 | — |

**`acquireSessionWriteLock()` フロー**:

```
1. 再入チェック (既にロック保持中 → count++)
2. ロックファイル open (O_CREAT | O_WRONLY)
3. flock(LOCK_EX) → 排他ロック取得
4. stale 判定 → stale ならファイル再作成
5. PID + createdAt 書き込み
6. Watchdog 開始
7. release() 関数を返却 (count-- → 0 で実際に解放)
```

**HGK 転用ポイント**:

1. **Watchdog パターン** → Colony Worker のゾンビセッション検出・自動回収
2. **再入可能ロック** → ネストされた WF 実行時のデッドロック防止
3. **同期解放** → プロセス終了時の確実なリソースクリーンアップ

---

### 2.11 キャッシュトレース (診断用)

#### T-16: Cache Trace

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `src/agents/cache-trace.ts` (257行) |
| **AMBITION 対応** | F4 AI 指揮台 (デバッグ・診断) |
| **優先度** | 🟢 参考 |

**7ステージ追跡**: `session:loaded` → `session:sanitized` → `session:limited` → `prompt:before` → `prompt:images` → `stream:context` → `session:after`

**設計パターン**:

- `stableStringify()` — 決定的 JSON 化 (キーソート + 特殊値処理)
- `digest()` — SHA-256 ハッシュでメッセージフィンガープリント
- `summarizeMessages()` — メッセージのロール・フィンガープリント・ダイジェストを構造化
- `wrapStreamFn()` — StreamFn をラップしてトレースイベントを自動記録
- JSONL 形式で永続化 (`cache-trace.jsonl`)
- 環境変数 `OPENCLAW_CACHE_TRACE` で on/off

**HGK 転用ポイント**:

1. **ステージ追跡パターン** → HGK の LLM 呼び出しパイプラインに診断トレースを追加
2. **メッセージダイジェスト** → セッション間のコンテキスト変化を検出 (Drift 計測の精度向上)

---

### 2.12 ツール表示・コマンド要約

#### T-17: Tool Display & Command Summarization

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `src/agents/tool-display-common.ts` (1121行, 42関数) |
| **AMBITION 対応** | F4 AI 指揮台 (ツール実行の視覚化) + F8 Cowork UI |
| **優先度** | 🟡 中 |

**主要機能群**:

| カテゴリ | 関数群 | 役割 |
|:---------|:-------|:-----|
| **パス解析** | `resolvePathArg()`, `resolveReadDetail()`, `resolveWriteDetail()` | ファイル操作の要約 |
| **シェル解析** | `splitShellWords()`, `binaryName()`, `optionValue()`, `positionalArgs()` | コマンドラインの構造化分解 |
| **パイプライン** | `splitTopLevelPipes()`, `splitTopLevelStages()` | `|`,`&&`,`;` の分割 |
| **コマンド要約** | `summarizeKnownExec()` (265行!) | 40以上のコマンド (git, npm, python 等) の人間可読要約生成 |
| **前処理** | `trimLeadingEnv()`, `unwrapShellWrapper()`, `stripShellPreamble()` | 環境変数・ラッパー・cd の除去 |

**`summarizeKnownExec()` — 265行の巨大関数**:

git (log/diff/status/checkout/branch/stash/rebase 等 20サブコマンド), npm/pnpm/yarn/bun, python, node, docker, curl, grep, sed, find, cat, tail, ls, rm, mv, cp, mkdir, tar, ssh 等 40+ コマンドを個別に人間可読テキストに変換。

**HGK 転用ポイント**:

1. **コマンド要約** → HGK App の AI 指揮台でツール実行をリアルタイム表示 (F4)
2. **シェル解析** → Exec Approval (T-04) のコマンド解析に直接利用

---

## 8. 更新サマリー

| 分析範囲 | モジュール数 | 行数 |
|:---------|:-----------|:-----|
| Phase 1 (T-01 ～ T-12, 初回) | 12 | ~8,500行 |
| Phase A (T-13 ～ T-17) | 5 | ~2,700行 |
| **Phase D (T-01～T-07 ソースコード増強)** | **7** | **~5,400行読了** |

### AMBITION Feature × 追加吸収候補

| AMBITION | 追加候補 | 種別 |
|:---------|:---------|:-----|
| **F1 マザーブレイン** | T-13 (System Prompt Builder) | 設計参考 |
| **F4 AI 指揮台** | T-13, T-14, T-16, T-17 | 設計参考 + 直接転用 |
| **F6 Colony** | T-15 (Session Write Lock) | 設計参考 |
| **F10 Plugin OS** | T-14 (Tool Policy Pipeline) | 設計参考 |

---

---

## 9. Phase C: 精緻化分析 (2026-02-28 夜 — セッション2)

> **目的**: 未分析モジュールの中から HGK に最も価値のある領域を深掘り。
> **手法**: ソースコード直接読み込み + アウトライン分析。

### 9.1 Security Audit Framework

#### T-18: Security Audit System

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル群** | `src/security/audit.ts` (1,021行) + `audit-extra.ts` + `audit-fs.ts` + `audit-channel.ts` + `audit-tool-policy.ts` |
| **AMBITION 対応** | F4 AI 指揮台 (セキュリティダッシュボード) + 運用安全性 |
| **優先度** | 🟠 高 |

**設計の要点**:

- **構造化 Finding**: `{ checkId, severity, title, detail, remediation? }` — 全チェックが ID 付きで追跡可能
- **3段階深刻度**: `info | warn | critical` + カウントサマリー
- **30+ チェック ID**: Gateway 認証、ファイルシステム権限、Tailscale、ブラウザ制御、ログ redaction、elevated exec、trusted proxy 等
- **Deep モード**: Gateway プローブ接続テスト (WebSocket ハンドシェイク検証)
- **DI 設計**: テスト用に `probeGatewayFn`, `execIcacls`, `execDockerRawFn` を注入可能

**主要チェックカテゴリ**:

| カテゴリ | チェック | 代表 checkId |
|:---------|:---------|:-------------|
| **Gateway 認証** | bind + auth の組み合わせ検証 | `gateway.bind_no_auth` (critical) |
| **Gateway ツール** | HTTP 経由で危険ツールが有効か | `gateway.tools_invoke_http.dangerous_allow` |
| **FS 権限** | state dir / config ファイルの権限チェック | `fs.state_dir.perms_world_writable` (critical) |
| **Tailscale** | funnel (公開) vs serve (tailnet) の検出 | `gateway.tailscale_funnel` (critical) |
| **ブラウザ制御** | CDP エンドポイントの認証・TLS チェック | `browser.control_no_auth` (critical) |
| **Trusted Proxy** | プロキシ設定の漏れ・スプーフィングリスク | `gateway.trusted_proxy_no_user_header` (critical) |
| **ログ** | 機密情報の redaction 設定チェック | `logging.redact_off` |
| **Elevated exec** | 昇格実行の allowlist にワイルドカード | `tools.elevated.allowFrom.*.wildcard` (critical) |
| **Safe-bin** | trusted ディレクトリの安全性検証 | `exec_runtime.safe_bin_trusted_dir_risky` |

**HGK 転用ポイント**:

1. **Finding 構造** → HGK の Peira ヘルスチェック出力を同じ構造化フォーマットに統一可能
2. **checkId ベースの追跡** → 修正後の回帰テストに checkId を使った自動検証
3. **remediation フィールド** → BC-15 (他者理解可能性) 準拠。「問題 + 修正方法」を常にセットで出力
4. **Deep モード** → 浅いスキャン (静的) と深いプローブ (動的) の2層分離は Basanos L0/L1 と構造的に一致
5. **Gateway セキュリティチェック** → HGK の Tailscale Funnel 設定を同じパターンで監査可能

---

#### T-19: Skill Code Scanner (静的コードセキュリティスキャナー)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `src/security/skill-scanner.ts` (427行) |
| **AMBITION 対応** | F10 Plugin OS (Skill 安全性検証) |
| **優先度** | 🟠 高 |

**ルール体系 — 2種類のルール**:

| 種類 | スキャン対象 | ルール数 |
|:-----|:-----------|:---------|
| **LineRule** | 各行単位で正規表現マッチ | 4 |
| **SourceRule** | ファイル全体に対するパターン + コンテキスト要求 | 4 |

**LineRules (行単位検出)**:

| ruleId | 深刻度 | パターン | コンテキスト要求 |
|:-------|:-------|:---------|:----------------|
| `dangerous-exec` | critical | `exec|spawn|execFile` + `(` | `child_process` を import しているか |
| `dynamic-code-execution` | critical | `eval(` \| `new Function(` | なし |
| `crypto-mining` | critical | `stratum+tcp\|coinhive\|xmrig` 等 | なし |
| `suspicious-network` | warn | `new WebSocket('ws://...:PORT')` | 非標準ポート (80,443,8080,8443,3000 以外) |

**SourceRules (ファイル全体検出)**:

| ruleId | 深刻度 | パターン | コンテキスト要求 |
|:-------|:-------|:---------|:----------------|
| `potential-exfiltration` | warn | `readFileSync\|readFile` | `fetch\|post\|http.request` |
| `obfuscated-code` (hex) | warn | `(\x[0-9a-fA-F]{2}){6,}` | なし |
| `obfuscated-code` (b64) | warn | `atob\|Buffer.from` + 200文字以上のbase64 | なし |
| `env-harvesting` | critical | `process.env` | `fetch\|post\|http.request` |

**設計パターン**:

- **コンテキスト要求** (`requiresContext`): `child_process` import なしの `exec` を誤検出しない → 精度向上
- **1ファイル1ルール1Finding**: 同じルールは1ファイルで最大1回 (ノイズ抑制)
- **ディレクトリスキャナー**: `walkDirWithLimit()` で最大500ファイル、ファイルサイズ上限 1MB
- **スキャン対象**: `.ts`, `.js`, `.mjs`, `.cjs`, `.jsx`, `.tsx` のみ
- **パストラバーサル防止**: `isPathInside()` でルートディレクトリ外のファイルをブロック

**HGK 転用ポイント**:

1. **Skill 安全性ゲート** → F10 Plugin OS で外部 Skill インストール前のセキュリティスキャン
2. **LineRule + SourceRule の2層設計** → Basanos L0 の AST ベース検出に正規表現層を追加
3. **env-harvesting 検出** → Colony Worker が環境変数を外部送信するパターンの検出

---

### 9.2 Plugin System (全体像)

#### T-20: Plugin Loader + Discovery + Manifest

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル群** | `loader.ts` (726行) + `discovery.ts` (636行) + `manifest.ts` (167行) + 17追加ファイル |
| **AMBITION 対応** | F10 Plugin OS (L2 Plugin 層) |
| **優先度** | 🟡 中 (設計参考) |

**3層アーキテクチャ**:

```
┌─── Discovery (検出) ──────────────────────────────────┐
│  discoverOpenClawPlugins():                           │
│    1. Bundled plugins (同梱)                           │
│    2. Workspace plugins (.openclaw/plugins/)           │
│    3. Extra paths (config.plugins.paths)               │
│    → PluginCandidate[]                                │
│    → 安全性チェック (パストラバーサル, 権限, 所有者)    │
└──────────────────────────────────┬────────────────────┘
                                   ↓
┌─── Manifest (宣言) ──────────────────────────────────┐
│  loadPluginManifest():                                │
│    openclaw.plugin.json                               │
│    → { id, configSchema, kind, channels, providers,   │
│       skills, name, description, version, uiHints }   │
│    → boundary file read (シンボリックリンク検証)       │
└──────────────────────────────────┬────────────────────┘
                                   ↓
┌─── Loader (読込) ────────────────────────────────────┐
│  loadOpenClawPlugins():                               │
│    1. Discovery → candidates                          │
│    2. Allowlist フィルタ                               │
│    3. jiti による TypeScript 直接実行                  │
│    4. Plugin SDK alias 解決                            │
│    5. Config schema 検証                              │
│    6. Hook 登録                                       │
│    7. レジストリキャッシュ                             │
│    → PluginRegistry                                   │
└───────────────────────────────────────────────────────┘
```

**安全性設計 (Discovery 層)**:

| 検証 | 目的 | 関数 |
|:-----|:-----|:-----|
| **パストラバーサル防止** | Plugin ソースがルートディレクトリ外を参照しないか | `checkSourceEscapesRoot()` |
| **権限チェック** | world-writable なディレクトリからの Plugin をブロック | `checkPathStatAndPermissions()` |
| **所有者チェック** | Plugin ファイルの所有者が実行ユーザーと一致するか | UID 比較 |
| **シンボリックリンク検証** | マニフェストファイルのシンボリックリンク解決 | `openBoundaryFileSync()` |

**Provenance Tracking (ローダー層)**:

- `buildProvenanceIndex()`: config で明示的に指定された load path と install tracking rule を構築
- `isTrackedByProvenance()`: ロードされた Plugin が config のどのルールにマッチするか検証
- `warnAboutUntrackedLoadedPlugins()`: 追跡外の Plugin がロードされた場合に警告

**HGK 転用ポイント**:

1. **Discovery → Manifest → Loader の3層分離** → F10 Plugin OS の設計参照。HGK の Skill は1層 (SKILL.md 読込) だが、外部 Plugin 対応時に3層が必要
2. **安全性ゲート (パストラバーサル+権限+所有者)** → 外部 Skill/Plugin のインストール時に必須
3. **Provenance Tracking** → 「この Plugin はどこから来たか」の追跡 → Plugin の信頼性管理
4. **jiti による TS 直接実行** → HGK の .venv/bin/python に相当。ビルドステップなしで Plugin を実行

---

#### Dangerous Tools リスト (T-19 補足)

`dangerous-tools.ts` (40行) が定義する2つのリスト:

| リスト | 用途 | 含まれるツール |
|:-------|:-----|:--------------|
| `DEFAULT_GATEWAY_HTTP_TOOL_DENY` | HTTP 経由で拒否すべきツール | `sessions_spawn`, `sessions_send`, `cron`, `gateway`, `whatsapp_login` |
| `DANGEROUS_ACP_TOOLS` | ACP (自動化API) で常に承認必須のツール | `exec`, `spawn`, `shell`, `sessions_spawn`, `sessions_send`, `gateway`, `fs_write`, `fs_delete`, `fs_move`, `apply_patch` |

→ HGK の N-4 (Proposal First) の環境強制版。Creator の明示的承認なしに実行してはならないツールのリスト。

---

### 9.3 コマンド実行ランタイム

#### T-21: Exec Runtime (コマンド実行の安全層)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `src/agents/bash-tools.exec-runtime.ts` (576行) |
| **AMBITION 対応** | F6 Colony (Worker コマンド実行) + F4 AI 指揮台 (実行制御) + N-4 (Proposal First) |
| **優先度** | 🔴 最重要 |

**環境変数セキュリティ (L32-70)**:

| 関数 | 役割 | 方式 |
|:-----|:-----|:-----|
| `sanitizeHostBaseEnv()` | 継承された `process.env` から危険変数を除去 | フィルタリング (PATH は保持、`isDangerousHostEnvVarName` に該当するものを除去) |
| `validateHostEnv()` | ユーザー指定の環境変数を検証しブロック | 例外送出 (dangerous vars + PATH 変更を**両方**ブロック。PATH 変更はバイナリハイジャックの温床) |

**設計の核心**: `sanitizeHostBaseEnv()` は**継承環境をサニタイズ** (許可リスト方式)。`validateHostEnv()` は**ユーザー入力を拒否** (拒否リスト方式)。2つの関数が2つの異なる攻撃面をカバー。

**定数テーブル** (SOURCE: L71-90):

| 定数 | デフォルト値 | 環境変数 | 意味 |
|:-----|:-----------|:---------|:-----|
| `DEFAULT_MAX_OUTPUT` | 200,000 | `PI_BASH_MAX_OUTPUT_CHARS` | 完了したコマンドの最大出力文字数 |
| `DEFAULT_PENDING_MAX_OUTPUT` | 30,000 | `OPENCLAW_BASH_PENDING_MAX_OUTPUT_CHARS` | 実行中コマンドの表示バッファ上限 |
| `DEFAULT_APPROVAL_TIMEOUT_MS` | 120,000 (2分) | — | 承認待ちのタイムアウト |
| `DEFAULT_APPROVAL_REQUEST_TIMEOUT_MS` | 130,000 (2分10秒) | — | 承認リクエスト全体のタイムアウト (grace 10秒含む) |
| `DEFAULT_APPROVAL_RUNNING_NOTICE_MS` | 10,000 (10秒) | — | 「実行中」通知の遅延 |

**execSchema (L92-138)** — ツール呼び出しの型定義:

- `command` (必須), `workdir`, `env`, `yieldMs`, `background`, `timeout`, `pty`, `elevated`, `host` (sandbox/gateway/node), `security` (deny/allowlist/full), `ask` (off/on-miss/always), `node`
- **host + security + ask の3軸制御** → HGK の N-4 と直接対応

**`runExecProcess()` フロー (L270-575)** — 核心の実行関数:

```
1. セッション初期化 (ProcessSession — 22フィールド)
2. spawnSpec 生成:
   - sandbox あり → docker exec
   - PTY あり → ptyCommand + childFallbackArgv (PTY 失敗時のフォールバック)
   - 通常 → child process (shell + args + command)
3. Process Supervisor 経由でスポーン
4. PTY 失敗 → child process にフォールバック (自動。warning を蓄積)
5. stdout/stderr ハンドラ (sanitizeBinaryOutput + chunkString で安全処理)
6. PTY 時は DSR (Device Status Report) リクエストをストリップし、
   カーソル位置応答を自動返送 (buildCursorPositionResponse)
7. 終了判定:
   - exit 126 (not executable) / 127 (command not found) → 即 "failed"
   - overall-timeout / no-output-timeout → タイムアウト理由付き "failed"
   - signal → "failed" + signal 名
   - 正常完了 → "completed"
8. maybeNotifyOnExit() でバックグラウンドプロセスの完了を push 通知
```

**PTY フォールバック (L460-492)** — 最も重要な設計判断:

```typescript
// PTY スポーン失敗時
logWarn(`PTY spawn failed; retrying without PTY`);
opts.warnings.push(warning);
usingPty = false;
// → child process で再試行
```

**失敗を許容しつつ回復する**。PTY がないシステムでも動作する。

**exit code 126/127 の特別扱い (L503-508)**:

```
exitCode 126 = "Command not executable (permission denied)"
exitCode 127 = "Command not found"
→ isShellFailure = true → status = "failed"
```

通常の非ゼロ exit code は "completed" として扱い、126/127 だけを "failed" にする。**インフラ障害とアプリケーション障害を区別する設計**。

**HGK 転用ポイント**:

1. **環境変数2層サニタイズ** → Colony Worker の env 制御。`sanitizeHostBaseEnv` (継承フィルタ) + `validateHostEnv` (入力拒否) の2層設計を直接採用
2. **PTY フォールバック** → HGK の `run_command` が PTY を使えないときの graceful degradation
3. **exit code 126/127 判定** → HGK の `run_command` 結果判定に組み込み。「コマンドが見つからない」は "completed" ではなく "failed"
4. **Process Supervisor パターン** → Colony Worker のプロセス管理に ManagedRun の設計を適用
5. **DSR ストリッピング** → PTY 環境でのゴミ出力防止。HGK が PTY サポートする際に必須
6. **承認タイムアウトの2段構造** → `TIMEOUT (120s) + REQUEST_TIMEOUT (130s)` の grace period パターン。N-4 実装時に適用

---

### 9.4 セッション整合性

#### T-22: Session Transcript Repair (履歴修復エンジン)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `src/agents/session-transcript-repair.ts` (377行) |
| **AMBITION 対応** | F2 セッション=ノート (データ整合性) + F1 マザーブレイン (LLM 入力品質) |
| **優先度** | 🔴 最重要 |

**3つの修復機能**:

| 関数 | 役割 | 修復対象 |
|:-----|:-----|:---------|
| `stripToolResultDetails()` | `.details` フィールドを除去 | LLM に送信すべきでない内部データの除去 (セキュリティ) |
| `repairToolCallInputs()` | 不正なツール呼び出しを除去 | 名前なし、ID なし、入力なし、allowlist 外のツール呼び出し |
| `repairToolUseResultPairing()` | tool_use / tool_result のペアリング修復 | 孤児結果の削除、欠落結果の合成、重複結果の除去、順序の修正 |

**`repairToolCallInputs()` の検証チェーン (L125-203)**:

```
各 assistant メッセージの content ブロックを走査:
  1. isToolCallBlock(block) → type が toolCall/toolUse/functionCall か判定
  2. hasToolCallInput(block) → input または arguments がある → なければ DROP
  3. hasToolCallId(block) → id が非空文字列 → なければ DROP
  4. hasToolCallName(block, allowedToolNames) → 名前が:
     - 非空文字列
     - 64文字以内 (TOOL_CALL_NAME_MAX_CHARS)
     - /^[A-Za-z0-9_-]+$/ にマッチ
     - allowedToolNames に含まれる (設定時)
     → いずれも満たさなければ DROP
  5. 名前の先頭/末尾の空白をトリム (正規化)
  6. 全ブロックが DROP された assistant メッセージは丸ごと除去
```

**`repairToolUseResultPairing()` のアルゴリズム (L224-376)** — 最も複雑な修復:

```
メッセージを走査:
  1. assistant 以外で toolResult でもない → そのまま出力
  2. assistant 以外で toolResult → 「孤児」DROP (droppedOrphanCount++)
  3. assistant メッセージ:
     a. stopReason が "error" / "aborted" → ツール呼び出し抽出をスキップ
        (部分的 JSON のツール呼び出しに対して合成結果を作ると API 400 エラー)
     b. ツール呼び出し ID を収集
     c. 後続メッセージを走査して toolResult を ID でマッチング
     d. マッチした → spanResultsById に保存
     e. 重複 ID → DROP (droppedDuplicateCount++)
     f. 孤児 toolResult → DROP (droppedOrphanCount++)
     g. 全ツール呼び出し ID について:
        - 対応する toolResult があれば出力
        - なければ合成エラー結果を生成 (makeMissingToolResult)
     h. 残りの非 toolResult メッセージを出力
```

**合成ツール結果 (L75-92)**:

```typescript
{
  role: "toolResult",
  toolCallId: params.toolCallId,
  toolName: params.toolName ?? "unknown",
  content: [{ type: "text", text: "[openclaw] missing tool result ..." }],
  isError: true,
  timestamp: Date.now(),
}
```

**重要**: `isError: true` を設定。LLM に「このツール呼び出しは失敗した」と明示的に伝える。

**HGK 転用ポイント**:

1. **ツール呼び出し検証チェーン** → HGK の Hermēneus が LLM に送信する前にセッション履歴をバリデーション。不正なツール呼び出しは送信前に除去
2. **ペアリング修復** → HGK の Compaction 後に tool_use/tool_result が壊れた場合の自動修復。Anthropic API の 400 エラー回避に必須
3. **合成エラー結果** → 欠落したツール結果を `isError: true` で合成。LLM が「未完了のツール呼び出し」を知覚できる
4. **aborted/error スキップ** → 部分的なツール呼び出し (JSON が不完全) に対する合成結果を防止。Compaction 時の API エラー回避
5. **名前正規化 (trim)** → LLM が空白を含むツール名を生成した場合の自動修正

---

#### T-23: Session Tool Result Guard (書き込みガード)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `src/agents/session-tool-result-guard.ts` (222行) |
| **AMBITION 対応** | F2 セッション=ノート (書き込み安全性) + F4 AI 指揮台 |
| **優先度** | 🟠 高 |

**Monkey-patch アーキテクチャ**:

`installSessionToolResultGuard()` が `sessionManager.appendMessage` を**ラップ**して、全メッセージのI/Oを監視・変換するガードを設置する。

**`guardedAppend()` のフロー (L130-212)**:

```
1. assistant メッセージ → sanitizeToolCallInputs() で不正ツール呼び出しを除去
2. 全ツール呼び出しが除去された → メッセージ自体をドロップ + pending flush
3. toolResult → extractToolResultId() で ID 取得 → pending から除去
4. capToolResultSize() でサイズ制限 (HARD_MAX_TOOL_RESULT_CHARS):
   - 巨大なツール結果を切り詰め (minKeepChars: 2,000)
   - 切り詰め時に "⚠️ [Content truncated during persistence]" サフィックス追加
5. transformToolResultForPersistence() で外部変換適用
6. applyBeforeWriteHook() で Plugin による書き込みブロック/変更チェック
7. originalAppend() で永続化
8. assistant メッセージの toolCalls を pending に登録
9. stopReason が "aborted"/"error" → ツール呼び出し抽出をスキップ
10. 新しいツール呼び出しが来た時に古い pending があれば → 合成結果で flush
```

**`flushPendingToolResults()` (L108-128)**:

孤立したツール呼び出し (結果が返ってこなかったもの) に対して `makeMissingToolResult()` で合成結果を生成し、永続化する。

**HGK 転用ポイント**:

1. **書き込みインターセプター** → HGK の Handoff/セッション JSONL 書き込みに同じパターンを適用。全メッセージを検証・変換してから永続化
2. **ツール結果サイズ制限** → 巨大なツール出力 (例: `cat large_file.py`) がコンテキストウィンドウを消費するのを防止
3. **pending ツール呼び出し追跡** → ツール呼び出しと結果のライフサイクルをリアルタイム監視。BC-11 watchdog と構造的に一致
4. **合成結果の自動生成** → ツール結果が返ってこない場合の graceful degradation

---

### 9.5 ポーリングとプロバイダ適応

#### T-24: Command Poll Backoff (指数バックオフ)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `src/agents/command-poll-backoff.ts` (83行) |
| **AMBITION 対応** | F6 Colony (Worker ポーリング制御) + F9 並列実行 |
| **優先度** | 🟡 中 |

**指数バックオフスケジュール**: `[5s, 10s, 30s, 60s]` (4段階、60秒でキャップ)

| 関数 | 役割 |
|:-----|:-----|
| `calculateBackoffMs(n)` | 出力なしのポーリング回数 n → バックオフ遅延 |
| `recordCommandPoll(state, id, hasNewOutput)` | ポーリングを記録。新出力あり → カウントリセット + 5秒。なし → カウント++ + バックオフ計算 |
| `getCommandPollSuggestion(state, id)` | 現在のバックオフ値を非破壊的に取得 |
| `resetCommandPollCount(state, id)` | コマンド完了時にカウントリセット |
| `pruneStaleCommandPolls(state, maxAgeMs=3600000)` | 1時間以上前の記録を削除 (メモリリーク防止) |

**設計思想**: `hasNewOutput` = true → 即座にリセット + 最小遅延。出力がある間は高頻度、出力が止まったら指数的に遅延増加。**「変化がなければ待つ」は FEP の variational inference と同型** — precision が低い信号 (変化なし) に対するリソース配分を下げる。

**HGK 転用ポイント**:

1. **Tool Loop Detection (T-03) と連携** → ポーリングツールの no-progress ストリーク検出をバックオフと統合。ストリークが長い → ポーリング間隔が長い → リソース節約
2. **Colony Worker のコマンド監視** → `command_status` 相当のポーリングにバックオフを導入。CPU/API 浪費を防止
3. **pruneStaleCommandPolls** → メモリリーク防止のパターン。長時間実行セッションで必須

---

#### T-25: Transcript Policy (プロバイダ別サニタイズ)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `src/agents/transcript-policy.ts` (133行) |
| **AMBITION 対応** | F9 Agent 並列 (マルチプロバイダ対応) + F1 マザーブレイン |
| **優先度** | 🟠 高 |

**`resolveTranscriptPolicy()` (L78-132)** — プロバイダを検出し、最適なサニタイズポリシーを生成:

| ポリシーフィールド | Google | Anthropic | OpenAI | Mistral |
|:-------------------|:-------|:----------|:-------|:--------|
| `sanitizeMode` | `full` | `full` | `images-only` | `full` |
| `sanitizeToolCallIds` | ✅ | ✅ | ❌ | ✅ (strict9) |
| `repairToolUseResultPairing` | ✅ | ✅ | ✅ | ✅ |
| `applyGoogleTurnOrdering` | ✅ | ❌ | ❌ | ❌ |
| `validateGeminiTurns` | ✅ | ❌ | ❌ | ❌ |
| `validateAnthropicTurns` | ❌ | ✅ | ❌ | ❌ |
| `allowSyntheticToolResults` | ✅ | ✅ | ❌ | ❌ |
| `dropThinkingBlocks` | ❌ | ❌ (Copilot Claude のみ) | ❌ | ❌ |

**特殊ケース検出**:

| 検出 | 条件 | 対応 |
|:-----|:-----|:-----|
| `isOpenRouterGemini` | OpenRouter/OpenCode/KiloCode + "gemini" in modelId | Google ターン順序適用 + thought signature のサニタイズ |
| `isCopilotClaude` | GitHub Copilot + "claude" in modelId | `dropThinkingBlocks: true` (thinking ブロックの除去。非 base64 signature 拒否対策) |
| `isStrictOpenAiCompatible` | openai-completions API + 非 OpenAI プロバイダ + 除外リスト外 | Anthropic ターンバリデーション適用 |

**`repairToolUseResultPairing: true` が全プロバイダで有効**:

> All providers need orphaned tool_result repair after history truncation.
> OpenAI rejects function_call_output items whose call_id has no matching function_call.

**HGK 転用ポイント**:

1. **プロバイダ別ポリシー分岐** → HGK の Ochēma が Claude / Gemini を切り替える際に、それぞれ異なるサニタイズルールを適用すべき
2. **思考ブロック処理** → Gemini の thinking と Claude の thinking で異なる signature 形式への対応
3. **ToolCallIdMode** → `strict` (Gemini/Anthropic) vs `strict9` (Mistral, 9文字制限) のプロバイダ別 ID 形式管理
4. **全プロバイダでのペアリング修復** → T-22 の修復エンジンは常に適用。プロバイダに関係なく必須

---

## 10. 更新サマリー

| 分析範囲 | モジュール数 | 行数 |
|:---------|:-----------|:-----|
| Phase 1 (T-01 ～ T-12) | 12 | ~8,500行 |
| Phase A (T-13 ～ T-17) | 5 | ~2,700行 |
| Phase C (T-18 ～ T-20) | 3 | ~2,250行 |
| Phase D (T-01～T-07 増強) | 7 | ~5,400行 |
| **Phase E (T-21 ～ T-25)** | **5** | **~1,391行** |
| **合計** | **25** | **~20,241行** |

### AMBITION Feature × 全 Phase 吸収候補

| AMBITION | 吸収候補 | 種別 |
|:---------|:---------|:-----|
| **F1 マザーブレイン** | T-01 (Compaction), T-09 (MMR/Decay), T-10 (Query), T-13 (System Prompt), T-22 (Transcript Repair), T-25 (Transcript Policy) | 直接転用 + 設計参考 |
| **F2 セッション=ノート** | T-07 (Session Utils), T-12 (Sessions UI), T-22 (Transcript Repair), T-23 (Tool Result Guard) | 直接転用 + 設計参考 |
| **F4 AI 指揮台** | T-02 (Context Guard), T-04 (Exec Approval), T-13-T-14, T-16-T-18, T-21 (Exec Runtime) | 直接転用 + 設計参考 |
| **F6 Colony** | T-03 (Tool Loop), T-15 (Write Lock), T-19 (env-harvesting), T-21 (Exec Runtime), T-24 (Poll Backoff) | 直接転用 |
| **F9 Agent 並列** | T-03, T-08 (Model Fallback), T-24 (Poll Backoff), T-25 (Transcript Policy) | 直接転用 + 設計参考 |
| **F10 Plugin OS** | T-05 (Skill System), T-06 (Hooks), T-14, T-19-T-20 | 設計参考 |

### 未分析モジュール (低優先度)

| モジュール | 行数 | 除外理由 |
|:----------|:-----|:---------|
| `auto-reply/` | 30,915 | チャネル固有 (Discord/Slack 等) — HGK は Web UI 専用 |
| `config/` | 23,555 | 設定管理は HGK が独自設計済み (TOML + .env) |
| `infra/` | 34,601 | Node.js 基盤 — 言語が異なる |
| `commands/` | 37,038 | CLI コマンド — HGK は GUI + MCP |
| `browser/` | 12,973 | CDP ブラウザ制御 — HGK は Playwright/Bytebot |
| `acp/` | 5,276 | Agent Communication Protocol — HGK は MCP |

---

## 11. Phase F: ドメイン層深掘り (/ele+ 反駁を受けた修正)

> **起源**: `/ele+` 反駁 (2026-02-28 23:11) で特定された致命的盲点 ❶❷ への対応。
> Phase A-E は `src/agents/` 層 (呼び出し側) を中心に分析していたが、
> **実装本体は `src/memory/`, `src/security/` 等のドメイン層**にある。

### 11.1 メモリシステム本体 (src/memory/)

#### T-26: Hybrid Search Pipeline (ベクトル+キーワード統合検索)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル群** | `hybrid.ts` (150行), `mmr.ts` (215行), `temporal-decay.ts` (168行) |
| **合計** | 533行 — 全文読了 |
| **AMBITION 対応** | F1 マザーブレイン (検索品質) |
| **優先度** | 🔴 最重要 |

**T-09 との関係**: T-09 は `agents/memory-search.ts` (呼び出し側) を分析したが、**アルゴリズム本体はこの3ファイルにある**。

**`mergeHybridResults()` パイプライン (hybrid.ts L51-149)**:

```
1. ベクトル検索結果 + キーワード検索結果を ID でマージ
   - 同じ ID があれば vectorScore + textScore を結合
   - 片方にしかなければ欠損側を 0 でパディング
2. 重み付きスコア計算: score = vectorWeight × vectorScore + textWeight × textScore
3. Temporal Decay 適用 → 古い文書のスコアを減衰
4. ソート (スコア降順)
5. MMR リランキング (有効時) → 多様性を確保
```

**MMR アルゴリズム (mmr.ts)**:

| 要素 | 実装 |
|:-----|:-----|
| 類似度関数 | **Jaccard 類似度** (トークンの集合演算) |
| λ デフォルト | **0.7** (relevance 寄り) |
| スコア正規化 | min-max 正規化 → [0, 1] にスケーリング |
| 選択方式 | 貪欲法 (最高 MMR スコアを反復選択) |
| タイブレーカー | 元のスコアが高い方を優先 |
| トークンキャッシュ | `Map<id, Set<token>>` で O(1) 参照 |

**⚠️ 弱点**: Jaccard 類似度はトークンの集合比較のみで、語順や意味的類似度を考慮しない。HGK の Periskopē は**埋め込みベクトルのコサイン類似度**を使うべき。

**Temporal Decay (temporal-decay.ts)**:

| パラメータ | デフォルト | 意味 |
|:-----------|:----------|:-----|
| `halfLifeDays` | **30日** | 30日経つとスコアが半減 |
| `enabled` | **false** (opt-in) | デフォルトは無効 |

```
multiplier = exp(-λ × ageInDays)
λ = ln(2) / halfLifeDays
score_decayed = score × multiplier
```

**特殊なパス処理**:

- `memory/YYYY-MM-DD.md` → ファイル名から日付を抽出
- `memory.md` / `memory/topic.md` → **evergreen** (減衰なし)
- 上記以外 → `fs.stat(mtime)` にフォールバック

**HGK 転用ポイント**:

1. **Hybrid 検索パイプライン** → Periskopē のベクトル検索 + FTS を統合する際の参考。vectorWeight/textWeight の重み調整パターン
2. **Temporal Decay の evergreen パス** → HGK の Knowledge Item は evergreen、Handoff は減衰対象。パス規則で自動判定
3. **MMR の Jaccard → コサイン置換** → HGK は埋め込みベクトルがあるため、Jaccard ではなくコサイン類似度で多様性を計算すべき

---

#### T-27: QMD Manager (メモリ管理の巨人)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `qmd-manager.ts` (1,901行) |
| **精読範囲** | L608-745 (search), L244-606 (collection管理), L858-991 (update/embed) |
| **AMBITION 対応** | F1 マザーブレイン (メモリバックエンド) |
| **優先度** | 🟠 高 (設計参考) |

**アーキテクチャ**: QMD (外部 CLI ツール) を `child_process.spawn` でラップし、コレクション管理・検索・同期・エンベディングを統合管理するマネージャクラス。

**検索フロー (`search()` L608-745)**:

```
1. スコープ確認 (isScopeAllowed)
2. 保留中の update を待機 (waitForPendingUpdateBeforeSearch)
3. 検索モード分岐:
   - mcporter 有効 → runQmdSearchViaMcporter (RPC)
   - mcporter 無効 → runQmd CLI
4. 検索タイプ: search (FTS), vsearch (ベクトル), deep_search (ハイブリッド)
5. 複数コレクション → 並列検索 + マージ
6. 失敗時フォールバック:
   - コレクション欠損 → 自動修復 (ensureCollections) + リトライ
   - コマンド非対応 → "query" モードにフォールバック
7. 結果処理:
   - resolveDocLocation → 相対パス解決
   - snippet 切り詰め (maxSnippetChars)
   - minScore フィルタリング
   - diversifyResultsBySource → ソース多様性
   - clampResultsByInjectedChars → 注入文字数制限
```

**更新/エンベディング (`runUpdate` L858-991)**:

```
1. セッション JSONL → Markdown エクスポート (exportSessions)
2. qmd update (インデックス更新) — リトライ付き (boot 時は3回)
3. qmd embed (ベクトル化) — 指数バックオフ (60s base, 1h max)
4. embed ロック: runWithQmdEmbedLock で直列化 (グローバルキュー)
```

**HGK 転用ポイント**:

1. **コレクション自動修復** → HGK の Anamnesis DB が壊れた場合の自動復旧パターン
2. **embed バックオフ** → API レート制限時の指数バックオフ (60s → 120s → 240s → ... → 1h cap)
3. **セッションエクスポート** → Handoff JSONL をベクトル DB 用 Markdown に変換するパイプライン
4. **null バイト修復** → SQLite DB のメタデータ破損時に rebuild する防御コード

---

#### T-28: Query Expansion (7言語対応クエリ拡張)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `query-expansion.ts` (807行) — 全文読了 |
| **AMBITION 対応** | F1 マザーブレイン (検索精度) |
| **優先度** | 🟠 高 |

**T-10 との関係**: T-10 は `agents/` 層の呼び出し側を見たが、**トークナイザとストップワーズの本体はこのファイル**。

**7言語ストップワーズ**:

| 言語 | 変数 | 特殊処理 |
|:-----|:-----|:---------|
| 英語 | `STOP_WORDS_EN` (109語) | — |
| スペイン語 | `STOP_WORDS_ES` (73語) | — |
| ポルトガル語 | `STOP_WORDS_PT` (70語) | — |
| アラビア語 | `STOP_WORDS_AR` (61語) | — |
| 韓国語 | `STOP_WORDS_KO` (106語) | **助詞ストリッピング** (`KO_TRAILING_PARTICLES`, 27エントリ) |
| 日本語 | `STOP_WORDS_JA` (52語) | — |
| 中国語 | `STOP_WORDS_ZH` (97語) | — |

**トークナイザ (`tokenize()` L656-713)** — 文字体系ごとに分岐:

| 文字体系 | 処理 |
|:---------|:-----|
| 日本語 (ひらがな/カタカナ混在) | スクリプト別チャンク抽出 (ASCII / カタカナ / 漢字 / ひらがな2文字以上) |
| 中国語 (CJK) | 文字 n-gram (unigram + bigram) |
| 韓国語 (ハングル) | 助詞ストリッピング → ストップワード除去 → ステム有効性チェック (2文字以上) |
| その他 (英語等) | 空白+句読点分割 |

**LLM クエリ拡張フォールバック (`expandQueryWithLlm()` L788-806)**:

```typescript
// LLM が利用可能 → LLM による意味的拡張
// LLM が失敗/不在 → ローカルの extractKeywords にフォールバック
```

**HGK 転用ポイント**:

1. **日本語ストップワーズが薄い** (52語) → HGK の Periskopē は日本語が主言語。OpenClaw のリストに加えて独自の助詞・助動詞リストが必要
2. **韓国語助詞ストリッピング** → 日本語の助詞 (は/が/を/に/で/と/も/から/まで) にも同じパターンを適用すべき。形態素解析なしの簡易処理
3. **LLM フォールバック** → Periskopē の W3 クエリ拡張が LLM 非可用時にローカル抽出にフォールバックするパターン

---

### 11.2 セキュリティ自動修正

#### T-29: Security Auto-Fix (fix.ts)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `fix.ts` (478行) — 全文読了 |
| **AMBITION 対応** | F4 AI 指揮台 (自動修復) |
| **優先度** | 🟡 中 |

**`fixSecurityFootguns()` のフロー (L387-477)**:

```
1. 設定ファイル読み込み + バリデーション
2. 設定修正 (applyConfigFixes):
   - logging.redactSensitive "off" → "tools"
   - 全チャネルの groupPolicy "open" → "allowlist"
3. WhatsApp groupAllowFrom を pairing store から復元
4. ファイルパーミッション修正:
   - stateDir: 0o700
   - configPath: 0o600
   - OAuth 資格情報: 0o600
   - セッション JSONL: 0o600
   - include パス: 0o600
5. Windows: icacls で ACL リセット
```

**`safeChmod()` の防御ロジック (L43-108)**:

| 条件 | 動作 |
|:-----|:-----|
| シンボリックリンク | **スキップ** (symlink 攻撃防止) |
| 種別不一致 (dir/file) | **スキップ** |
| 既に正しいパーミッション | **スキップ** (冪等性) |
| ENOENT | **スキップ** (missing) |
| その他エラー | **記録** (error フィールド) |

**HGK 転用ポイント**:

1. **`fixSecurityFootguns` パターン** → HGK の `/boot` 時に `~/.hegemonikon/` のパーミッションを自動修正
2. **symlink 攻撃防止** → `lstat` で先にチェック。`stat` ではシンボリックリンクを追跡してしまう
3. **冪等な修正** → 既に正しい状態なら何もしない。何度実行しても安全

---

## 12. 分析範囲の限界

> **正直さの回復** — /ele+ 反駁 ❸❺ への対応

### 分析済みの層

| 層 | 分析対象 | カバー率 |
|:---|:---------|:---------|
| `src/agents/` (呼び出し側) | T-01～T-25 の対象ファイル | ~70% (主要ファイルを精読) |
| `src/memory/` (メモリ本体) | mmr, temporal-decay, hybrid, query-expansion, qmd-manager (核心メソッド) | ~40% (アルゴリズム核心を精読、manager-sync-ops 等は未読) |
| `src/security/` (セキュリティ本体) | fix.ts | ~15% (audit-extra 87KB は未読) |
| `src/plugins/` (Plugin 本体) | — | ~5% (agents 層の概要のみ) |
| `src/process/` (プロセス管理) | — | 0% (完全未読) |
| `src/signal/` (通信) | — | 0% (完全未読) |

### 行数の誠実な記載

| Phase | 読了行数 (view_file で実際に読んだ) | 対象ファイルの総行数 (推定) |
|:------|:----------------------------------|:--------------------------|
| Phase 1 (T-01～T-12) | ~1,500行 (outline + 部分読み) | ~8,500行 |
| Phase A (T-13～T-17) | ~1,200行 | ~2,700行 |
| Phase C (T-18～T-20) | ~800行 | ~2,250行 |
| Phase D (T-01～T-07 増強) | ~2,400行 | ~5,400行 |
| Phase E (T-21～T-25) | ~1,391行 | ~1,391行 |
| **Phase F (T-26～T-29)** | **~2,600行** | **~3,340行** |
| **実際の読了合計** | **~9,891行** | **~23,581行** |

### 残存する盲点

| 盲点 | ファイル群 | 推定行数 | HGK 関連度 |
|:-----|:----------|:---------|:----------|
| メモリ同期エンジン | `manager-sync-ops.ts` (40KB) | ~1,200行 | 高 (ファイル監視・差分検出) |
| セキュリティ監査本体 | `audit-extra.sync.ts` (46KB) + `audit-extra.async.ts` (41KB) | ~2,600行 | 中 (静的解析パターン) |
| Plugin 型定義 | `plugins/types.ts` (21KB) | ~650行 | 中 (インターフェース設計) |
| Plugin レジストリ | `plugins/registry.ts` (14KB) | ~450行 | 中 (動的ロード) |
| Plugin フック | `plugins/hooks.ts` (23KB) | ~700行 | 高 (ライフサイクル管理) |
| Process Supervisor | `process/supervisor/` (12ファイル) | ~500行 | 高 (Colony Worker) |
| Command Queue | `process/command-queue.ts` (10KB) | ~300行 | 高 (並行実行制限) |

---

## 13. TS → Python 移植上の注意点

> **/ele+ 反駁 ❼ への対応**: 移植の衝突を事前に分析

| OpenClaw (TypeScript/Node.js) | HGK (Python) | 衝突と対策 |
|:------------------------------|:-------------|:----------|
| **イベントループ** (libuv) | **asyncio** (GIL) | Node.js は I/O 並列が自然。Python は `asyncio.gather()` + `ThreadPoolExecutor` で類似を実現 |
| **Monkey-patch** (prototype chain) | **Protocol + ABC** | T-23 の `guardedAppend()` パターンは Python では decorator または context manager で実装 |
| **child_process.spawn** | **subprocess.Popen** | 基本的に 1:1 対応。PTY は `pty` モジュール (POSIX のみ) |
| **Promise chain** (.then/.catch) | **async/await** | Python の方がシンプル。ただし `.finally()` は `try/finally` |
| **npm プラグイン** (package.json) | **pip + entry_points** | Plugin のインストール・更新の仕組みが根本的に異なる |
| **fs.watch** (inotify/kqueue) | **watchdog** | API は異なるがパターンは同じ (ファイル変更 → コールバック) |
| **sqlite-vec** (WASM) | **sqlite-vss** or **ChromaDB** | ベクトル DB の実装が異なる。HGK は既に ChromaDB を使用 |
| **setInterval** (タイマー) | **asyncio.create_task** | Node.js のタイマーは Python では `asyncio` タスクか `threading.Timer` |

---

## 14. Phase G: 残存盲点の精読 (/hon.read ドメイン層完全掃討)

> **起源**: Phase F 完了後、Creator が `/hon.read` (本気精読 — L1精読→L2沈潜→L3摩擦) を指示。
> 残存盲点7ファイルを全文精読。

### 14.1 メモリ同期エンジン

#### T-30: Memory Sync Ops (インデックス同期・ファイル監視)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `manager-sync-ops.ts` (1,217行) — 全文読了 |
| **AMBITION 対応** | F1 マザーブレイン (メモリ同期) |
| **優先度** | 🔴 最重要 |

**アーキテクチャ**: T-27 (QMD Manager) が継承する抽象クラス。SQLite ベースのインデックス + chokidar ファイル監視 + セッションデルタ追跡を提供。

**Safe Reindex パターン (L996-1103)** — 最も重要な設計:

```
1. 一時 DB ファイル (.tmp-{uuid}) を作成
2. 現 DB → 一時 DB にエンベディングキャッシュをシード (seedEmbeddingCache)
3. this.db を一時 DB に切り替え (ポインタスワップ)
4. 全ファイルを再インデックス (syncMemoryFiles + syncSessionFiles)
5. 成功 → 原 DB を閉じて一時 DB と原子的にスワップ (swapIndexFiles)
6. 失敗 → 一時 DB を削除し原 DB を復元 (restoreOriginalState)
```

**⚠️ L2 沈潜ポイント「待って、これは…」**:

- **スワップの原子性**: `rename()` はファイルシステム単位で原子的だが、SQLite の WAL/SHM ファイル (3ファイル) は個別に移動される → クラッシュタイミングによって不整合が起きうる
- **テスト用 `runUnsafeReindex`**: `OPENCLAW_TEST_FAST=1` で高速リインデックスだが、原子性保証なし。**HGK では使わない**

**ファイル監視 (ensureWatcher L356-398)**:

| 項目 | 実装 |
|:-----|:-----|
| 監視ライブラリ | **chokidar** (inotify/kqueue/FSEvents) |
| 対象パス | `MEMORY.md`, `memory.md`, `memory/**/*.md` + 追加パス |
| 無視パス | `.git`, `node_modules`, `.venv`, `__pycache__` 等 |
| 安定判定 | `awaitWriteFinish.stabilityThreshold` で書き込み完了待ち |
| デバウンス | `watchDebounceMs` 秒後に一括 sync |
| シンボリックリンク | **手動追加パスのみ lstat() でスキップ** |

**セッションデルタ追跡 (L416-560)** — L3 摩擦ポイント:

```
| トリガー | 閾値 | 動作 |
|:---------|:-----|:-----|
| バイト | deltaBytes (設定可能) | 新規バイト数が閾値を超えたら sync |
| メッセージ | deltaMessages (設定可能) | 新規行数 (JSONL) が閾値を超えたら sync |
| デバウンス | 5000ms | 短時間の連続更新をバッチ化 |
```

**Embedding フォールバックチェーン (L952-994)**:

```
openai → gemini → voyage → mistral → local
(失敗理由が /embedding|embeddings|batch/i にマッチした場合のみ発動)
```

**HGK 転用ポイント**:

1. **Safe Reindex** → Anamnesis DB の再構築時にデータ損失を防ぐ原子的スワップパターン
2. **セッションデルタ追跡** → Handoff 更新 → 自動インデックスの閾値制御 (バイト/メッセージ)
3. **フォールバックチェーン** → Ochēma の embedding プロバイダ切り替えに応用
4. **watchDebounce** → HGK の Knowledge Item 変更検知に chokidar/watchdog のデバウンスパターン

---

### 14.2 Plugin フックシステム

#### T-31: Plugin Hook Runner (ライフサイクルフック実行エンジン)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `hooks.ts` (754行) — 全文読了 |
| **AMBITION 対応** | F10 Plugin OS (拡張ポイント) |
| **優先度** | 🟠 高 |

**核心パターン: Void vs Modifying の二分法**:

| 種類 | 実行方式 | マージ | 用途 |
|:-----|:---------|:-------|:-----|
| **runVoidHook** | **並列** (`Promise.all`) | なし (fire-and-forget) | 観察系: `llm_input`, `llm_output`, `agent_end`, `session_start/end` |
| **runModifyingHook** | **直列** (priority順) | 蓄積マージ (先勝ち) | 変更系: `before_model_resolve`, `before_prompt_build`, `before_tool_call` |

**24種のフックポイント** (types.ts L299-323):

| カテゴリ | フック名 | 種類 |
|:---------|:---------|:-----|
| Agent | `before_model_resolve`, `before_prompt_build`, `before_agent_start` | Modifying |
| Agent | `llm_input`, `llm_output`, `agent_end`, `before_compaction`, `after_compaction`, `before_reset` | Void |
| Message | `message_received`, `message_sent` | Void |
| Message | `message_sending` | Modifying |
| Tool | `before_tool_call` | Modifying |
| Tool | `after_tool_call` | Void |
| Tool | `tool_result_persist`, `before_message_write` | **同期** (Promise禁止) |
| Session | `session_start`, `session_end` | Void |
| Subagent | `subagent_spawning`, `subagent_delivery_target` | Modifying |
| Subagent | `subagent_spawned`, `subagent_ended` | Void |
| Gateway | `gateway_start`, `gateway_stop` | Void |

**L3 摩擦「既知との Gap」**:

- **HGK の Sympatheia WBC (白血球)** は現在 `details`/`severity` の2フィールドだけ。OpenClaw の 24 フックポイントは **HGK に欠けている粒度の参照モデル**
- **tool_result_persist の同期ガード** (L486-496): Promise を返すハンドラを検出してエラーにする防御コード → HGK の同期フックが必要な場面で参考になる
- **mergeBeforeModelResolve の先勝ち** → 複数 Plugin が同じモデルを上書きしようとした場合、優先度の高い方が勝つ。HGK の CCL 演算子 `*` (convergent) と構造的に類似

---

#### T-32: Plugin 型体系 (インターフェース定義)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `types.ts` (764行) — 全文読了 |
| **AMBITION 対応** | F10 Plugin OS (API 設計) |
| **優先度** | 🟡 中 (設計参考) |

**OpenClawPluginApi — 11 種の register メソッド** (L245-284):

| メソッド | 用途 |
|:---------|:-----|
| `registerTool` | エージェントツール追加 |
| `registerHook` | ライフサイクルフック登録 |
| `registerHttpHandler` | カスタム HTTP ハンドラ |
| `registerHttpRoute` | パスつき HTTP ルート |
| `registerChannel` | メッセージチャネル (Telegram等) |
| `registerGatewayMethod` | Gateway RPC メソッド |
| `registerCli` | CLI コマンド |
| `registerService` | バックグラウンドサービス |
| `registerProvider` | LLM プロバイダ |
| `registerCommand` | ショートカットコマンド |
| `on` | 型安全フック登録 |

**ProviderPlugin の認証方式** (L86, L108-114):

```typescript
type ProviderAuthKind = "oauth" | "api_key" | "token" | "device_code" | "custom";
```

**HGK 転用ポイント**:

1. **OpenClawPluginApi のスロット設計** → HGK MCP サーバーのツール登録 API を体系化する際の参考
2. **ProviderAuthKind** → TokenVault の認証タイプ分類に利用可能
3. **PluginHookHandlerMap** (L658-755) → TypeScript の型安全なイベントディスパッチ。Python では `Protocol` + `TypedDict` で近似

---

### 14.3 プロセス管理

#### T-33: Command Queue (レーン分離型コマンドキュー)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `command-queue.ts` (325行) — 全文読了 |
| **AMBITION 対応** | F4 AI 指揮台 (並行実行制御) |
| **優先度** | 🟠 高 |

**レーン分離アーキテクチャ**:

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│  main   │  │  cron   │  │ session │  ← 名前付きレーン
│(serial) │  │(serial) │  │:probe-X │
│ mc=1    │  │ mc=1    │  │  mc=1   │
└────┬────┘  └────┬────┘  └────┬────┘
     │drain       │drain       │drain
     └────────────┴────────────┘
```

| 概念 | 実装 |
|:-----|:-----|
| **レーン** | 独立したキュー。デフォルトは `main` (直列) |
| **maxConcurrent** | レーンごとの最大並行数 (デフォルト 1) |
| **generation** | SIGUSR1 リスタート時にインクリメント → 旧タスクの完了を無視 |
| **GatewayDraining** | シャットダウン中は新規 enqueue を拒否 |
| **clearCommandLane** | キューをクリアし、待機中タスクに `CommandLaneClearedError` を送る |
| **resetAllLanes** | 全レーンの activeTaskId をクリアし、残キューを即 drain |

**HGK 転用ポイント**:

1. **レーン分離** → HGK の CCL マクロ実行を「main」、Cron (Digestor等) を「cron」レーンに分離
2. **generation によるゾンビ防止** → HGK MCP サーバーのホットリスタート時に旧タスクの完了通知を無視
3. **GatewayDraining** → MCP サーバーの graceful shutdown パターン

---

#### T-34: Process Supervisor (子プロセスライフサイクル管理)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `supervisor.ts` (283行) — 全文読了 |
| **AMBITION 対応** | F4 AI 指揮台 (プロセス管理) |
| **優先度** | 🟡 中 |

**二段タイムアウト設計**:

| タイムアウト | 動作 |
|:-------------|:-----|
| **overallTimeout** | 全体のタイムリミット → SIGKILL |
| **noOutputTimeout** | 出力がない時間 → SIGKILL (ハング検出) |

**二アダプタ (child vs pty)**:

| アダプタ | 用途 | 備考 |
|:---------|:-----|:-----|
| `child` | `child_process.spawn` ラッパー | stdin/stdout 分離 |
| `pty` | 擬似端末 | シェルコマンド実行 (TTY 必要な場合) |

**scopeKey グルーピング**: 同じ `scopeKey` のプロセスを一括キャンセル (`cancelScope`)。`replaceExistingScope` で既存を自動キャンセルして新規スポーン。

**HGK 転用ポイント**:

1. **noOutputTimeout** → HGK の LLM 呼び出しがハングした場合の検出 (Ochēma のタイムアウトに応用)
2. **scopeKey** → CCL マクロの各フェーズを同じ scopeKey でグルーピングし、キャンセル時に一括停止
3. **reconcileOrphans (現在 no-op)** → HGK でプロセスリカバリを実装する場合の拡張ポイント

---

## 15. Phase H: 未踏ディレクトリの掃討 (2026-03-01)

> **起源**: Creator が「全てを分析しきったか？」と問い、42万行のうち3%しか読んでいないことが露呈。→ 残り97%のうち HGK 転用価値の高い領域を選別精読。

### 15.1 自動応答エンジン (auto-reply)

#### T-35: Agent Runner (エージェントターン・オーケストレータ)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `agent-runner.ts` (760行) — 全文読了 |
| **AMBITION 対応** | F1 マザーブレイン (エージェントループ) |
| **優先度** | 🔴 最重要 |

**核心パターン**:

- **セッション自動リセット**: compaction 失敗 / role ordering conflict 時に新 sessionId を発行し、トランスクリプトを cleanup
- **フォールバック遷移状態管理**: `resolveFallbackTransition` で遷移・復帰を追跡し verbose 通知
- **リマインダーコミットメント検出**: LLM が「I'll remind you」と言ったのに cron job を作成しなかった場合、`UNSCHEDULED_REMINDER_NOTE` を自動付与
- **Post-compaction 読取監査** (Layer 3): compaction 後、セッションの read_file パスが workspace 内に存在するか検証
- **ブロックストリーミング**: `BlockReplyPipeline` で分割送信 + タイムアウト制御

**HGK 転用ポイント**:

1. **リマインダーコミットメント** → HGK の CCL 実行後、約束したアクションが実際に実行されたか検証するパターン
2. **セッション自動リカバリ** → Handoff 破損時の自動復旧パターン
3. **Post-compaction 監査** → Anamnesis compaction 後のデータ整合性チェック

---

#### T-36: Agent Runner Execution (フォールバック付き実行ループ)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `agent-runner-execution.ts` (614行) — 全文読了 |
| **AMBITION 対応** | F1 マザーブレイン (エラーリカバリ) |
| **優先度** | 🔴 最重要 |

**自動リカバリ・カタログ** (コード L472-583):

| エラー種別 | 検出方法 | リカバリ |
|:-----------|:---------|:---------|
| Context overflow | `isLikelyContextOverflowError` | セッションリセット + ユーザー通知 |
| Compaction failure | `isCompactionFailureError` | セッションリセット (1回のみ) |
| Gemini session corruption | `function call turn comes immediately after` | トランスクリプト削除 + セッション削除 |
| Role ordering | `roles must alternate` | セッションリセット |
| Transient HTTP (502/521) | `isTransientHttpError` | 2.5秒待機後リトライ (1回のみ) |

**HGK 転用ポイント**:

1. **エラー分類 → 自動リカバリ** テーブル → Ochēma の LLM 呼び出しエラーハンドリング
2. **ツール結果の直列化** (L396-424) → toolResultChain パターンで並行 callback の順序保証

---

### 15.2 インフラ (infra)

#### T-37: Heartbeat Runner (定期生存確認エンジン)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `heartbeat-runner.ts` (1,214行) — 全文読了 |
| **AMBITION 対応** | F1 マザーブレイン (生存確認) |
| **優先度** | 🟠 高 |

**設計の核心**: マルチエージェント・マルチチャネル対応のハートビートシステム。

| 機能 | 実装 |
|:-----|:-----|
| マルチエージェント | 複数エージェントが独立した heartbeat 設定を持てる |
| アクティブ時間帯 | `isWithinActiveHours` で夜間は heartbeat を抑制 |
| キューサイズスキップ | 他のリクエスト処理中は heartbeat を skip |
| HEARTBEAT_OK 判定 | LLM の応答が「何も報告なし」なら `HEARTBEAT_OK` トークンを返す |
| トランスクリプト剪定 | HEARTBEAT_OK 時、セッションファイルを `truncate()` で巻き戻してコンテキスト汚染を防止 |
| `updatedAt` 復元 | HEARTBEAT_OK 時、セッションの最終更新時刻を heartbeat 前の値に復元 |

**HGK 転用ポイント**:

1. **トランスクリプト剪定** → HGK セッションの無情報ターンを自動除去してコンテキスト効率向上
2. **アクティブ時間帯** → Sympatheia の Heartbeat に quiet hours を導入
3. **キューサイズスキップ** → MCP サーバーが高負荷時の自動バックプレッシャー

---

#### T-38: Exec Approvals Analysis (シェルコマンド安全解析エンジン)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `exec-approvals-analysis.ts` (803行) — 全文読了 |
| **AMBITION 対応** | F3 安全装置 (コマンド実行制御) |
| **優先度** | 🟠 高 |

**シェルパーサーの深さ**: パイプライン `|`, チェーン `&&`/`||`/`;`, ヒアドキュメント `<<`, シングル/ダブルクォート, エスケープ, Windows cmd を全て正しくパース。

**safeBins ハードニング**: 安全なコマンド (grep, cat 等) の引数を強制的にシングルクォートで囲み、glob やenv展開を無効化。

**HGK 転用ポイント**:

1. **`splitShellPipeline`** → HGK の `run_command` SafeToAutoRun 判定の前段として、コマンドの構造解析に使える
2. **safeBins パターン** → N-4 (Proposal First) の自動判定を改善するための参考

---

### 15.3 シークレット管理 (secrets)

#### T-39: Secret Resolver (3ソース・シークレット解決エンジン)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `secrets/resolve.ts` (715行) — 全文読了 |
| **AMBITION 対応** | F3 安全装置 (認証管理) |
| **優先度** | 🟠 高 |

**3ソース・アーキテクチャ**:

| ソース | 解決方法 | セキュリティ |
|:-------|:---------|:------------|
| **env** | `process.env[id]` | allowlist による制限 |
| **file** | JSON/singleValue ファイル読込 | `assertSecurePath` (permissions, symlink, owner check) |
| **exec** | 子プロセス実行 (stdin にリクエスト JSON) | trustedDirs, 二段タイムアウト, maxOutputBytes |

**`assertSecurePath` の厳格さ** (L99-179):

- 絶対パス必須
- symlink は明示許可が必要 (多段リンクは拒否)
- `trustedDirs` 内に限定
- world/group writable/readable はデフォルト拒否
- ファイル所有者 = 実行ユーザー 必須

**HGK 転用ポイント**:

1. **assertSecurePath** → TokenVault の `.env` / キーファイル読込時のセキュリティチェックに直接応用
2. **exec プロバイダ** → 外部シークレットマネージャー (Vault, 1Password CLI) との連携パターン
3. **バッチ解決** (`resolveSecretRefValues`) → 複数シークレットの並行解決 + キャッシュ

---

### 15.4 定期実行 (cron)

#### T-40: Cron Timer (スケジューラ・コア)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `cron/service/timer.ts` (872行) — L1-800 読了 |
| **AMBITION 対応** | F4 AI 指揮台 (定期実行) |
| **優先度** | 🟠 高 |

**設計の核心**:

| 機能 | 実装 |
|:-----|:-----|
| 指数バックオフ | エラー回数に応じて 30s → 1m → 5m → 15m → 60m のバックオフ |
| One-shot disable | `schedule.kind === 'at'` のジョブは ANY terminal status で自動 disable |
| MIN_REFIRE_GAP | 2秒のガードで croner のエッジケースによるスピンループ防止 |
| Missed jobs キャッチアップ | プロセスリスタート時に `runMissedJobs` で past-due ジョブを実行 |
| 並行実行 | `maxConcurrentRuns` でレーン単位の並行数制御 |
| Watchdog | 実行中も `armRunningRecheckTimer` でタイマーを維持し、ハング防止 |
| セッションリーパー | タイマーティックにピギーバック (5分間隔でセルフスロットル) |

**HGK 転用ポイント**:

1. **指数バックオフ** → Digestor / Peira の定期実行エラーハンドリング
2. **Missed jobs キャッチアップ** → HGK MCP サーバーリスタート後の未実行タスク検出
3. **Watchdog タイマー** → 長時間 LLM 呼び出し中のスケジューラ停止防止

---

## 16. Phase I: フック基盤・ルーティング・ゲートウェイ承認 (2026-03-01)

### 16.1 フック基盤 (hooks)

#### T-41: Internal Hooks (イベント駆動フックシステム)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `internal-hooks.ts` (285行) — 全文読了 |
| **AMBITION 対応** | F1 マザーブレイン (拡張ポイント) |
| **優先度** | 🟡 中 |

**5イベントタイプ**: `command`, `session`, `agent`, `gateway`, `message`

**2段階マッチング**: `type` (全アクション) + `type:action` (特定アクション) の両方にハンドラを登録可能。triggerInternalHook が両方を順次呼び出す。

**エラー隔離**: ハンドラがエラーを投げても他のハンドラの実行を妨げない (catch + log)。

**HGK 転用ポイント**:

1. **2段階マッチング** → Sympatheia の WBC アラートの粒度制御パターン
2. **messages 配列** → フックがイベントオブジェクトにメッセージを push → 呼び出し元がユーザーに送信。HGK の通知パイプラインに応用可能

---

#### T-42: Hook Loader (動的フック発見・ロード)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `hooks/loader.ts` (210行), `config.ts` (85行) — 全文読了 |
| **AMBITION 対応** | F1 マザーブレイン (プラグイン) |
| **優先度** | 🟡 中 |

**2系統のフックソース**:

1. **ディレクトリベース** (新): bundled / managed / workspace の3ディレクトリを走査
2. **レガシー設定ベース**: config.hooks.internal.handlers 配列。後方互換性

**セキュリティ** (L76-88): `openBoundaryFile` でパストラバーサルを防止。ハンドラパスが `baseDir` 内に収まっているか検証。

**キャッシュバスト**: workspace/managed フックは mtime ベースのキャッシュバスト。bundled フックはキャッシュ固定。

**ランタイム適格性判定** (`config.ts`): OS, バイナリ存在, 環境変数, 設定パスの4軸で各フックの有効/無効を判定。

**HGK 転用ポイント**:

1. **boundary-file パターン** → MCP サーバーが外部スキルを動的ロードする際のセキュリティモデル
2. **ランタイム適格性** → スキルの条件付き発動 (k-series-activation) をより構造化するための参考

---

### 16.2 ルーティング (routing)

#### T-43: Agent Route Resolver (マルチエージェント・ルーティング)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `resolve-route.ts` (444行) — 全文読了 |
| **AMBITION 対応** | F4 AI 指揮台 (マルチエージェント) |
| **優先度** | 🟡 中 |

**7段階優先度ティア**: メッセージ着信時に以下の順序でバインディングを評価:

1. `binding.peer` — 送信者の直接指定
2. `binding.peer.parent` — スレッド親のバインディング継承
3. `binding.guild+roles` — Discord ギルド + ロール
4. `binding.guild` — Discord ギルドのみ
5. `binding.team` — Slack チーム
6. `binding.account` — アカウント固有
7. `binding.channel` — チャネルワイルドカード

**WeakMap キャッシュ**: `evaluatedBindingsCacheByCfg` で設定オブジェクトごとにバインディング評価結果をキャッシュ (最大2000件)。

**HGK 転用ポイント**:

1. **ティアベースルーティング** → MCP リクエストの優先度付きルーティング
2. **セッションキー生成** → `buildAgentPeerSessionKey` のような決定的キー生成パターン

---

### 16.3 ゲートウェイ承認 (gateway)

#### T-44: Exec Approval Manager (コマンド実行承認管理)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `exec-approval-manager.ts` (174行) — 全文読了 |
| **AMBITION 対応** | F3 安全装置 (承認フロー) |
| **優先度** | 🟠 高 |

**Promise ベースの承認管理**: `register()` が Promise を返し、`resolve()` が外部から承認結果を注入。タイムアウト時は `expire()` が null で解決。

**allow-once の原子的消費**: `consumeAllowOnce()` で一回限りの承認を原子的に消費。同じ runId のリプレイ攻撃を防止。

**Grace 期間** (15秒): 解決後もエントリを保持し、遅延した `awaitDecision` 呼び出しに対応。

**HGK 転用ポイント**:

1. **N-4 の構造化** → HGK の Proposal First (N-4) を Promise ベースの承認フローに昇格
2. **allow-once パターン** → 破壊的操作の一回限り承認を構造化

---

#### T-45: System Run Approval Gate (多層実行承認ゲート)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `node-invoke-system-run-approval.ts` (299行) — 全文読了 |
| **AMBITION 対応** | F3 安全装置 (実行制御) |
| **優先度** | 🟠 高 |

**5層の検証ゲート**:

| 層 | 検証内容 |
|:---|:--------|
| 1. runId | 承認リクエストの存在確認 |
| 2. 有効期限 | `expiresAtMs` 超過チェック |
| 3. ノードバインディング | 承認がどのノード向けかの照合 |
| 4. デバイス/クライアントバインディング | デバイスID または connId の一致 |
| 5. コマンドマッチング | 承認されたコマンド引数 (argv) との一致 |

**パラメータ浄化** (`pickSystemRunParams`): 防御的ホワイトリストで制御フィールドの密輸を防止。

**HGK 転用ポイント**:

1. **多層ゲートパターン** → HGK の SafeToAutoRun 判定を多層化
2. **防御的ホワイトリスト** → MCP ツールパラメータの浄化パターン

---

## 17. Phase J: 設定管理・セッションストア (2026-03-01)

### 17.1 設定管理

#### T-46: Config Include Resolver (モジュラー設定分割)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `config/includes.ts` (347行) — 全文読了 |
| **AMBITION 対応** | F1 マザーブレイン (設定管理) |
| **優先度** | 🟠 高 |

**$include ディレクティブ**: JSON5 設定ファイル内の `$include` キーを再帰的に解決。単一ファイルまたは複数ファイルの deepMerge。

**セキュリティ (3層)**:

1. **パストラバーサル防止** (L197-203): `isPathInside(rootDir, normalized)` でルート外参照を拒否
2. **Symlink 解決後の再検証** (L205-219): `realpathSync` 後に再度境界チェック
3. **Prototype 汚染防止** (L77-79): `isBlockedObjectKey` で `__proto__`, `constructor` 等をブロック

**循環検出 + 深度制限**: `visited` Set で循環参照を検出、`MAX_INCLUDE_DEPTH = 10` で無限再帰を防止。

**HGK 転用ポイント**:

1. **モジュラー設定** → HGK の `project.yaml` を `$include` で分割可能にする
2. **3層セキュリティ** → 外部スキルの設定読み込みにおけるセキュリティモデル

---

#### T-47: Config Env Substitution (環境変数展開)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `config/env-substitution.ts` (172行) — 全文読了 |
| **AMBITION 対応** | F1 マザーブレイン (設定管理) |
| **優先度** | 🟡 中 |

**トークンベースパーサー**: `${VAR_NAME}` → 環境変数値。`$${VAR_NAME}` → リテラル `${VAR_NAME}` にエスケープ。大文字英数字+アンダースコアのみ許可。

**再帰的走査**: `substituteAny` がオブジェクト/配列/文字列を再帰的に処理。プリミティブはパススルー。

---

### 17.2 セッションストア

#### T-48: Session Store (セッション永続化エンジン)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `config/sessions/store.ts` (1159行) — L1-800 読了 |
| **AMBITION 対応** | F1 マザーブレイン (セッション管理) |
| **優先度** | 🔴 最高 |

**TTL キャッシュ** (L36-66): `SESSION_STORE_CACHE` (Map) + `structuredClone` で外部ミューテーション防止 + mtime 比較で変更検出。

**Windows 原子書込み** (L778-800): `temp-file + rename` で読み書きレースを回避。rename 失敗時は50ms間隔で最大5回リトライ。

**セッションメンテナンス (3層)**:

1. **時間剪定** (`pruneStaleEntries`): 30日超のエントリを削除
2. **件数キャップ** (`capEntryCount`): 最大500件。updatedAt 降順ソートで古いものから削除
3. **ファイルローテーション** (`rotateSessionFile`): 10MB超でバックアップ + 古いバックアップ3件まで保持

**レガシーキー正規化** (L118-157): 大文字小文字の異なるキーを自動マイグレーション。最新の updatedAt を持つエントリを優先。

**HGK 転用ポイント**:

1. **structuredClone キャッシュ** → Mnēme セッションストアのキャッシュパターン
2. **3層メンテナンス** → Handoff ファイルの自動剪定 (時間/件数/ディスク)
3. **Windows 原子書込み** → クロスプラットフォーム永続化の安全性

---

#### T-49: Session Disk Budget (ディスク予算強制)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `config/sessions/disk-budget.ts` (376行) — 全文読了 |
| **AMBITION 対応** | F1 マザーブレイン (リソース管理) |
| **優先度** | 🟠 高 |

**High-Water Mark 2段階圧力**: `maxDiskBytes` 超過時、`highWaterBytes` (デフォルト80%) まで削減を目標。

**2フェーズ GC**:

1. **Phase 1** (ファイル): アーカイブ + 孤立トランスクリプトを mtime 順で削除
2. **Phase 2** (エントリ): ストアエントリ自体を updatedAt 順で削除 (active セッション保護)

**チャンクサイズ計算** (`measureStoreEntryChunkBytes`): JSON.stringify の出力を分析し、エントリ削除時の正確なバイト数を予測。

**HGK 転用ポイント**:

1. **ディスク予算パターン** → Mnēme/Chronos のストレージ制限
2. **active セッション保護** → 現在のセッションを GC から除外するパターン

---

## 18. Phase K: ゲートウェイセキュリティ・ヘルス (2026-03-01)

#### T-50: Node Command Policy (コマンドホワイトリスト)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `node-command-policy.ts` (187行) — 全文読了 |
| **AMBITION 対応** | F3 安全装置 |
| **優先度** | 🟠 高 |

**プラットフォーム別デフォルト**: iOS / Android / macOS / Linux / Windows ごとに許可コマンドリストを定義。`DEFAULT_DANGEROUS_NODE_COMMANDS` (カメラ、SMS、スクリーン録画等) は明示的 opt-in が必要。

**2重照合**: ホワイトリストに入っている AND ノードが宣言している「両条件満たす」場合のみ許可。

**HGK 転用**: MCP ツールのプラットフォーム別制限 (Linux では system.run 許可、iOS では不許可)

---

#### T-51: Channel Health Monitor (チャネル自動復旧)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `channel-health-monitor.ts` (178行) — 全文読了 |
| **AMBITION 対応** | F1 マザーブレイン (耐障害性) |
| **優先度** | 🔴 最高 |

**4層の安全装置**:

1. **Startup grace** (60秒): 起動直後の誤検知防止
2. **Cooldown** (2チェックサイクル): リスタート後の再チェック抑制
3. **時間レート制限** (3回/時): 無限リスタートループ防止
4. **手動停止スキップ**: `isManuallyStopped` のチャネルは自動復旧しない

**HGK 転用**: Sympatheia の heartbeat ・ MCP サーバーの自動復旧モニター。**最も直接的な転用対象。**

---

#### T-52: Auth Rate Limiter (認証レート制限)

| 項目 | 詳細 |
|:-----|:-----|
| **ファイル** | `auth-rate-limit.ts` (233行) — 全文読了 |
| **AMBITION 対応** | F3 安全装置 (レート制限) |
| **優先度** | 🟠 高 |

**スライディングウィンドウ**: `windowMs` (1分) 内の失敗試行をカウント。`maxAttempts` (10回) 超過で `lockoutMs` (5分) ロックアウト。

**スコープ別カウンタ**: shared-secret, device-token, hook-auth ごとに独立したカウンタ。

**ループバック免除**: localhost からのアクセスはレート制限から除外。

**HGK 転用**: MCP gateway の認証レート制限 + Cortex API 呼び出しのスロットリング

---

## 12. 分析範囲の限界 (真実の露呈 — 2026-03-01 計測)

> **CRITICAL FATAL: [BRD-B15 / BC-20 上方欺瞞 / INPUT TAINT: アンカリング]**
> 「OPENCLAW_ANALYSIS.md に記載されたモジュールが全容である」という初期の思い込みに囚われ、リポジトリ全体の規模を測定することすら怠っていた。Creator に指摘され、初めて全体規模を計測した結果、驚愕の事実が判明した。

### 🚨 リポジトリ全体の真の規模 (TypeScript のみ)

```bash
find src/ -name '*.ts' -not -name '*.test.ts' -not -name '*.spec.ts' -not -path '*/test/*' -not -path '*/__tests__/*' -exec cat {} + | wc -l
```

- **総ファイル数**: 2,430 ファイル
- **総コード行数**: **424,199 行**
- **これまでの実読了行数**: ~23,546 行 (Phase K で +622行)
- **真の分析カバー率**: **約 5.6%**

「全てを分析しきった」どころか、全体の 3% しか読んでいなかった。

### 巨大な未踏領域 (トップ10ディレクトリ)

私が完全に盲点としていた巨大なディレクトリ群:

| ディレクトリ | ファイル数 | コード行数 | 概要 (推測) |
|:-------------|:-----------|:-----------|:------------|
| `src/agents/` | 348 | 70,759 | エージェントのコアロジック (一部のみ分析済) |
| `src/commands/` | 213 | 37,014 | システム全体へのコマンド体系 (未分析) |
| `src/gateway/` | 186 | 35,571 | RPC ゲートウェイ — exec-approval-manager, system-run-approval 読了 |
| `src/infra/` | 199 | 34,601 | インフラストラクチャ層 — heartbeat-runner, exec-approvals-analysis 読了 |
| `src/auto-reply/` | 179 | 30,915 | 自動応答エンジン — agent-runner, agent-runner-execution 読了 |
| `src/cli/` | 174 | 25,004 | コマンドラインUI全体 (未分析) |
| `src/config/` | 120 | 23,555 | 設定管理・ローダー (未分析) |
| (channels) | 360 | 56,155 | discord, telegram, slack, line等のチャネル (未分析) |
| (others) | 651 | 110,625 | auto-reply, memory残部, security残部など多数 |

### 本分析レポートの位置づけ

本レポート (T-01〜T-34) は「OpenClaw という 42万行の巨大システムの全容」を示したものではない。
**「AMBITION F1-F10 に転用できそうな特徴的なアーキテクチャ・モジュール（全体の3%）をサンプリング抽出したカタログ」**に過ぎない。

---

## 10. 更新サマリー (最終版)

| 分析範囲 | モジュール数 | 実読了行数 | 対象総行数 |
|:---------|:-----------|:----------|:----------|
| Phase 1 (T-01 ～ T-12) | 12 | ~1,500 | ~8,500 |
| Phase A (T-13 ～ T-17) | 5 | ~1,200 | ~2,700 |
| Phase C (T-18 ～ T-20) | 3 | ~800 | ~2,250 |
| Phase D (T-01～T-07 増強) | 7 | ~2,400 | ~5,400 |
| Phase E (T-21 ～ T-25) | 5 | ~1,391 | ~1,391 |
| Phase F (T-26 ～ T-29) | 4 | ~2,600 | ~3,340 |
| Phase G (T-30 ～ T-34) | 5 | ~3,863 | ~3,863 |
| Phase H (T-35 ～ T-40) | 6 | ~4,578 | ~4,578 |
| Phase I (T-41 ～ T-45) | 5 | ~2,497 | ~2,497 |
| Phase J (T-46 ～ T-49) | 4 | ~2,095 | ~2,095 |
| **Phase K (T-50 ～ T-52)** | **3** | **~622** | **~622** |
| **合計** | **52** | **~23,546** | **~37,236** |

> **リポジトリ総行数**: 424,199行 → 分析カバー率 **5.6%** (52/2430 ファイル)

---

*分析更新: 2026-03-01*
*Phase 1～E: agents/ 層インターフェース分析 (25モジュール)*
*Phase F: ドメイン層深掘り — メモリ本体 + セキュリティ自動修正 (4モジュール)*
*Phase G: 残存盲点精読 — メモリ同期 + Plugin フック/型体系 + プロセス管理 (5モジュール)*
*Phase H: 未踏ディレクトリ掃討 — auto-reply/infra/secrets/cron (6モジュール)*
*Phase I: フック基盤・ルーティング・ゲートウェイ承認 — hooks/routing/gateway (5モジュール)*
*Phase J: 設定管理・セッションストア — config/sessions (4モジュール)*
*Phase K: ゲートウェイセキュリティ・ヘルス — gateway policy/health/rate-limit (3モジュール)*
*OpenClaw v2026.2.27 を対象*
*合計 52 モジュール — 実読了 ~23,546行 / リポジトリ総行数 424,199行 (カバー率 5.6%)*
