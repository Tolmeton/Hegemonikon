```typos
#prompt cursor-hooks-reference
#syntax: v8
#depth: L2

<:role: Cursor IDE Hooks API リファレンス — HGK フック作成用設計ドキュメント。
  Cursor IDE と Claude Code の両方の Hooks 仕様を統合し、HGK プロジェクトで
  フックを実装する際の SOURCE ドキュメントとして機能する。:>

<:goal: HGK の Cursor 移行において、Hooks の設計・実装に必要な全情報を一元管理する :>

<:constraints:
  - フック設計は HGK の 12 Nomoi に対応させること
  - N-4 (不可逆前確認) → beforeShellExecution / preToolUse で環境強制
  - N-12 (正確な実行) → sessionStart でコンテキスト注入
  - 保存先: hooks/ (実装) / .cursor/hooks.json (Cursor設定)
/constraints:>

<:context:
  - [knowledge] ソース: Cursor Hooks ドキュメント + Claude Code Hooks リファレンス (2026-03-26 取得)
  - [file] hooks/hooks.json (既存スタブ — echo のみ)
/context:>
```

# Cursor Hooks 設計ドキュメント — HGK 統合リファレンス

> **目的**: HGK (Hegemonikon) の Cursor IDE 移行において、Hooks システムを活用した認知制約の環境強制を設計・実装するための SOURCE ドキュメント。

---

## 1. アーキテクチャ概要

### 1.1 設定ファイルの配置

| レベル | パス | スコープ | 優先度 |
|:---|:---|:---|:---|
| Enterprise | `C:\ProgramData\Cursor\hooks.json` | システム全体 | 最高 |
| Project | `<project>/.cursor/hooks.json` | プロジェクト固有 | 中 |
| User | `~/.cursor/hooks.json` | ユーザー全体 | 低 |

**HGK での方針**: Project レベル (`.cursor/hooks.json`) を使用し、リポジトリにコミット。

### 1.2 スクリプトの配置

```
<project-root>/
├── .cursor/
│   └── hooks.json          # Cursor IDE 用設定
├── hooks/
│   └── hooks.json          # Claude Code 用設定 (Claude Code Plugin 互換)
└── .cursor/hooks/           # フックスクリプト本体
    ├── session-init.sh      # sessionStart
    ├── n04-shell-guard.py   # beforeShellExecution (N-4)
    ├── n04-mcp-guard.py     # beforeMCPExecution (N-4)
    ├── audit.py             # 各種監査ログ
    └── format-on-edit.sh    # afterFileEdit フォーマッタ
```

### 1.3 フック実行タイプ

| タイプ | 説明 | 用途 |
|:---|:---|:---|
| `command` | シェルスクリプト実行。stdin=JSON, stdout=JSON | メイン (N-4, 監査等) |
| `prompt` | LLM に自然言語条件を評価させる | ポリシー判定 |
| `http` | HTTP POST でイベントを外部送信 | テレメトリ連携 (将来) |
| `agent` | サブエージェント生成で条件検証 (Claude Code のみ) | 高度な検証 (将来) |

---

## 2. フックイベント一覧

### 2.1 Cursor IDE Agent 用イベント

| イベント | タイミング | ブロック可能 | HGK 用途 |
|:---|:---|:---|:---|
| `sessionStart` | セッション開始時 | ❌ | コンテキスト注入 (Boot Context) |
| `sessionEnd` | セッション終了時 | ❌ | 監査ログ・セッション統計 |
| `preToolUse` | ツール実行前 (汎用) | ✅ | N-4 環境強制 (全ツール) |
| `postToolUse` | ツール実行成功後 | ❌ | 監査・コンテキスト注入 |
| `postToolUseFailure` | ツール失敗後 | ❌ | エラー追跡 |
| `subagentStart` | サブエージェント起動前 | ✅ | サブエージェント制御 |
| `subagentStop` | サブエージェント完了後 | ✅ | 自動フォローアップ |
| `beforeShellExecution` | シェルコマンド実行前 | ✅ | **N-4 コマンドブラックリスト** |
| `afterShellExecution` | シェルコマンド実行後 | ❌ | 監査ログ |
| `beforeMCPExecution` | MCP ツール実行前 | ✅ | **N-4 MCP ツール制御** |
| `afterMCPExecution` | MCP ツール実行後 | ❌ | 監査ログ |
| `beforeReadFile` | ファイル読み取り前 | ✅ | 機密ファイル保護 (θ4.7) |
| `afterFileEdit` | ファイル編集後 | ❌ | フォーマッタ実行 |
| `beforeSubmitPrompt` | プロンプト送信前 | ✅ | PII スキャン |
| `preCompact` | コンテキスト圧縮前 | ❌ | Context Rot 監視 |
| `stop` | エージェントループ終了時 | ✅ | 自動フォローアップ |
| `afterAgentResponse` | レスポンス完了後 | ❌ | 応答追跡 |
| `afterAgentThought` | Thinking 完了後 | ❌ | 推論追跡 |

### 2.2 Claude Code 拡張イベント

Claude Code Plugin (`hooks/hooks.json`) で追加利用可能:

| イベント | タイミング | ブロック可能 | HGK 用途 |
|:---|:---|:---|:---|
| `PreToolUse` | ツール実行前 | ✅ | N-4 + N-12 環境強制 |
| `PostToolUse` | ツール成功後 | ✅ (block) | 品質検証 |
| `PermissionRequest` | 権限ダイアログ表示時 | ✅ | 自動承認/拒否 |
| `Stop` | 応答完了時 | ✅ | 自動フォローアップ |
| `SubagentStop` | サブエージェント完了 | ✅ | フォローアップ注入 |
| `UserPromptSubmit` | プロンプト送信前 | ✅ (block) | 入力検証 |
| `Notification` | 通知送信時 | ❌ | 通知ログ |
| `FileChanged` | ファイル変更検知 | ❌ | ファイル監視 |
| `CwdChanged` | 作業ディレクトリ変更 | ❌ | 環境管理 |
| `PreCompact` / `PostCompact` | 圧縮前後 | ❌ | Context Rot 監視 |
| `InstructionsLoaded` | ルールファイルロード | ❌ | ルール読込み追跡 |

---

## 3. 入出力スキーマ

### 3.1 共通入力フィールド (全イベント)

```json
{
  "conversation_id": "string",
  "generation_id": "string",
  "model": "string",
  "hook_event_name": "string",
  "cursor_version": "string",
  "workspace_roots": ["<path>"],
  "user_email": "string | null",
  "transcript_path": "string | null"
}
```

### 3.2 終了コード

| コード | 意味 | 動作 |
|:---|:---|:---|
| `0` | 成功 | stdout の JSON 出力を処理 |
| `2` | ブロッキングエラー | アクション拒否 (stderr をエラーメッセージとして使用) |
| その他 | 非ブロッキングエラー | 実行続行 (フェイルオープン) |

### 3.3 主要な出力パターン

**beforeShellExecution / beforeMCPExecution (N-4 環境強制)**:
```json
{
  "permission": "allow | deny | ask",
  "user_message": "<ユーザー表示メッセージ>",
  "agent_message": "<エージェントへのフィードバック>"
}
```

**preToolUse (汎用ツール制御)**:
```json
{
  "permission": "allow | deny",
  "user_message": "<拒否時メッセージ>",
  "agent_message": "<エージェントへのメッセージ>",
  "updated_input": { "command": "<修正後コマンド>" }
}
```

**sessionStart (コンテキスト注入)**:
```json
{
  "env": { "<key>": "<value>" },
  "additional_context": "<コンテキストテキスト>"
}
```

**stop (自動フォローアップ)**:
```json
{
  "followup_message": "<次のユーザーメッセージとして自動送信>"
}
```

---

## 4. HGK Nomoi × Hooks マッピング

### 4.1 環境強制の設計方針

| Nomos | 強制方式 | フックイベント | 実装 |
|:---|:---|:---|:---|
| N-4 不可逆前確認 | `deny` + フィードバック | `beforeShellExecution` | ブラックリストマッチ |
| N-4 MCP 制御 | `deny` + フィードバック | `beforeMCPExecution` | レート制限チェック |
| N-4 機密保護 | `deny` | `beforeReadFile` | `.env` パスマッチ |
| N-12 CCL 環境強制 | コンテキスト注入 | `sessionStart` | Boot Context |
| N-12 ツール呼出強制 | 監査ログ | `postToolUse` | ツール使用カウント |
| 監査 (全般) | ログ記録 | 各 `after*` イベント | JSON ログ出力 |

### 4.2 N-4 シェルコマンドガード設計

```
beforeShellExecution
  ├─ matcher: "rm|del|rmdir|DROP|TRUNCATE|sudo|pkill|kill"
  ├─ 入力: { "command": "<コマンド>", "cwd": "<作業ディレクトリ>" }
  ├─ 判定:
  │   ├─ θ4.5 ブラックリストマッチ → deny + 理由
  │   ├─ .env/SACRED_TRUTH パス含む → deny + 理由
  │   └─ それ以外 → allow
  └─ 出力: { "permission": "deny", "agent_message": "[N-4] ..." }
```

### 4.3 sessionStart コンテキスト注入設計

```
sessionStart
  ├─ 環境変数の設定:
  │   ├─ HGK_PROJECT_ROOT=<ワークスペースルート>
  │   ├─ HGK_SESSION_ID=<セッションID>
  │   └─ HGK_NOMOI_ACTIVE=12
  ├─ additional_context の注入:
  │   ├─ 最新 Handoff の要約
  │   ├─ 未完了タスクリスト
  │   └─ Context Rot 状態
  └─ 出力: { "env": {...}, "additional_context": "..." }
```

---

## 5. 設定ファイルテンプレート

### 5.1 .cursor/hooks.json (Cursor IDE Project 用)

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [
      {
        "command": ".cursor/hooks/session-init.sh"
      }
    ],
    "beforeShellExecution": [
      {
        "command": "python3 .cursor/hooks/n04-shell-guard.py",
        "timeout": 10,
        "matcher": "rm|del|rmdir|DROP|TRUNCATE|sudo|pkill|kill|chmod"
      }
    ],
    "beforeMCPExecution": [
      {
        "command": "python3 .cursor/hooks/n04-mcp-guard.py",
        "timeout": 10,
        "failClosed": true
      }
    ],
    "beforeReadFile": [
      {
        "command": "python3 .cursor/hooks/n04-file-guard.py",
        "timeout": 5
      }
    ],
    "afterFileEdit": [
      {
        "command": ".cursor/hooks/audit.sh"
      }
    ],
    "afterShellExecution": [
      {
        "command": ".cursor/hooks/audit.sh"
      }
    ],
    "preCompact": [
      {
        "command": ".cursor/hooks/context-rot-monitor.sh"
      }
    ],
    "stop": [
      {
        "command": ".cursor/hooks/audit.sh"
      }
    ]
  }
}
```

### 5.2 hooks/hooks.json (Claude Code Plugin 用)

```json
{
  "description": "Hegemonikon cognitive constraint hooks",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.cursor/hooks/n04-shell-guard.py",
            "timeout": 10
          }
        ]
      },
      {
        "matcher": "mcp__.*",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.cursor/hooks/n04-mcp-guard.py",
            "timeout": 10
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.cursor/hooks/session-init.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash|Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.cursor/hooks/audit.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.cursor/hooks/audit.sh"
          }
        ]
      }
    ]
  }
}
```

---

## 6. 環境変数

### 6.1 Cursor 提供の環境変数

| 変数 | 説明 | 常時利用可能 |
|:---|:---|:---|
| `CURSOR_PROJECT_DIR` | ワークスペースルート | ✅ |
| `CURSOR_VERSION` | Cursor バージョン | ✅ |
| `CURSOR_USER_EMAIL` | ユーザーメール | ログイン時のみ |
| `CURSOR_TRANSCRIPT_PATH` | トランスクリプトパス | transcript 有効時 |
| `CLAUDE_PROJECT_DIR` | プロジェクトルート (Claude互換) | ✅ |

### 6.2 Claude Code 追加変数

| 変数 | 説明 |
|:---|:---|
| `CLAUDE_ENV_FILE` | 環境変数永続化ファイルパス (SessionStart のみ) |
| `CLAUDE_PLUGIN_ROOT` | プラグインインストールディレクトリ |
| `CLAUDE_PLUGIN_DATA` | プラグイン永続データディレクトリ |

---

## 7. Matcher パターンリファレンス

### 7.1 ツールマッチャー (preToolUse / postToolUse)

| パターン | 対象 |
|:---|:---|
| `Shell` | シェルコマンド |
| `Read` | ファイル読取 |
| `Write` | ファイル書込 |
| `Grep` | 検索 |
| `Delete` | 削除 |
| `Task` | サブエージェント |
| `MCP:<tool_name>` | 特定 MCP ツール |

### 7.2 Claude Code 拡張マッチャー

| パターン | 対象 |
|:---|:---|
| `Bash` | シェルコマンド |
| `Edit\|Write` | ファイル書込系 |
| `mcp__<server>__<tool>` | MCP ツール (正規表現対応) |
| `mcp__.*__write.*` | 全サーバーの write 系ツール |

### 7.3 コマンドマッチャー (beforeShellExecution)

コマンド文字列全体に対してマッチ。パイプ (`|`) で OR 結合。

```
"rm|del|rmdir|DROP|TRUNCATE|DELETE FROM|sudo|pkill|kill|chmod|git push --force"
```

---

## 8. 実装ロードマップ

### Phase 1: 基盤 (即時)
- [ ] `.cursor/hooks.json` 設定ファイル配置
- [ ] `n04-shell-guard.py` — θ4.5 ブラックリスト enforcement
- [ ] `session-init.sh` — 基本的なセッション初期化

### Phase 2: 監査 (短期)
- [ ] `audit.py` — 全イベント監査ログ (JSON 形式)
- [ ] `n04-file-guard.py` — .env / 機密ファイル保護
- [ ] `context-rot-monitor.sh` — preCompact でのトークン監視

### Phase 3: 高度な統合 (中期)
- [ ] `hooks/hooks.json` — Claude Code Plugin フック
- [ ] MCP ツールガード (`n04-mcp-guard.py`)
- [ ] sessionStart でのコンテキスト注入 (Handoff 自動ロード)
- [ ] stop フックでの自動フォローアップ

---

## 9. 注意事項

### 9.1 Cursor IDE と Claude Code の差異

| 項目 | Cursor IDE | Claude Code |
|:---|:---|:---|
| 設定形式 | `version` + フラットな hooks | ネストされた matcher + hooks 配列 |
| イベント名 | camelCase (`sessionStart`) | PascalCase (`SessionStart`) |
| ブロック | `permission: "deny"` | 終了コード 2 or `hookSpecificOutput` |
| フェイルオープン | デフォルト | `failClosed: true` で変更可 |
| プロンプトフック | ✅ (`type: "prompt"`) | ✅ |
| HTTP フック | ❌ | ✅ (`type: "http"`) |
| エージェントフック | ❌ | ✅ (`type: "agent"`) |

### 9.2 failClosed の推奨

セキュリティ重要なフック (`beforeMCPExecution`, `beforeReadFile`) では `failClosed: true` を設定し、フック障害時にもアクションをブロックすること。

### 9.3 `loop_limit` 設定

`stop` フックでの `followup_message` による自動ループはデフォルト上限 5 回。`loop_limit` で変更可能。`null` で無制限。

---

---

## 10. Claude Code 拡張: PreToolUse ツール別入力スキーマ

各ツールの `tool_input` 構造 (PreToolUse / PostToolUse で共通):

### Bash
| フィールド | 型 | 説明 |
|:---|:---|:---|
| `command` | string | 実行するシェルコマンド |
| `description` | string | コマンドの説明 (optional) |
| `timeout` | number | タイムアウト ms (optional) |
| `run_in_background` | boolean | バックグラウンド実行 (optional) |

### Write
| フィールド | 型 | 説明 |
|:---|:---|:---|
| `file_path` | string | 絶対パス |
| `content` | string | 書き込むコンテンツ |

### Edit
| フィールド | 型 | 説明 |
|:---|:---|:---|
| `file_path` | string | 絶対パス |
| `old_string` | string | 検索テキスト |
| `new_string` | string | 置換テキスト |
| `replace_all` | boolean | 全置換 (optional) |

### Read
| フィールド | 型 | 説明 |
|:---|:---|:---|
| `file_path` | string | 絶対パス |
| `offset` | number | 開始行番号 (optional) |
| `limit` | number | 読取行数 (optional) |

### Glob
| フィールド | 型 | 説明 |
|:---|:---|:---|
| `pattern` | string | グロブパターン (例: `**/*.ts`) |
| `path` | string | 検索ディレクトリ (optional) |

### Grep
| フィールド | 型 | 説明 |
|:---|:---|:---|
| `pattern` | string | 正規表現パターン |
| `path` | string | 検索パス (optional) |
| `glob` | string | ファイルフィルタ (optional) |
| `output_mode` | string | `content` / `files_with_matches` / `count` |
| `-i` | boolean | 大文字小文字無視 |
| `multiline` | boolean | 複数行マッチ |

### WebFetch
| フィールド | 型 | 説明 |
|:---|:---|:---|
| `url` | string | 取得 URL |
| `prompt` | string | コンテンツ処理プロンプト |

### WebSearch
| フィールド | 型 | 説明 |
|:---|:---|:---|
| `query` | string | 検索クエリ |
| `allowed_domains` | array | 許可ドメイン (optional) |
| `blocked_domains` | array | ブロックドメイン (optional) |

### Agent (サブエージェント)
| フィールド | 型 | 説明 |
|:---|:---|:---|
| `prompt` | string | エージェントのタスク |
| `description` | string | タスクの短い説明 |
| `subagent_type` | string | エージェントタイプ (`Explore`, `Plan` 等) |
| `model` | string | モデルオーバーライド (optional) |

---

## 11. PreToolUse 決定制御 (hookSpecificOutput)

Claude Code では `hookSpecificOutput` 内に決定を返す (トップレベル `decision` は非推奨):

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow | deny | ask",
    "permissionDecisionReason": "理由",
    "updatedInput": { "field_to_modify": "new value" },
    "additionalContext": "追加コンテキスト"
  }
}
```

| フィールド | 説明 |
|:---|:---|
| `permissionDecision` | `allow` (許可), `deny` (拒否), `ask` (ユーザー確認) |
| `permissionDecisionReason` | allow/ask: ユーザー表示。deny: Claudeに表示 |
| `updatedInput` | 実行前にツール入力を変更 |
| `additionalContext` | コンテキストに追加される文字列 |

---

## 12. PermissionRequest 決定制御

権限ダイアログをプログラムで許可/拒否:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow | deny",
      "updatedInput": { "command": "npm run lint" },
      "updatedPermissions": [{ "type": "addRules", "rules": [...], "behavior": "allow", "destination": "session" }],
      "message": "deny時のみ: Claudeへの説明",
      "interrupt": false
    }
  }
}
```

### updatedPermissions エントリの type

| type | 効果 |
|:---|:---|
| `addRules` | 権限ルール追加 |
| `replaceRules` | 指定 behavior の全ルール置換 |
| `removeRules` | ルール削除 |
| `setMode` | 権限モード変更 (`default`/`acceptEdits`/`dontAsk`/`bypassPermissions`/`plan`) |
| `addDirectories` | 作業ディレクトリ追加 |
| `removeDirectories` | 作業ディレクトリ削除 |

### destination

| 値 | 保存先 |
|:---|:---|
| `session` | メモリのみ (セッション終了で破棄) |
| `localSettings` | `.claude/settings.local.json` |
| `projectSettings` | `.claude/settings.json` |
| `userSettings` | `~/.claude/settings.json` |

---

## 13. 追加イベント詳細 (Claude Code 固有)

### InstructionsLoaded
ルールファイル (CLAUDE.md / `.claude/rules/*.md`) のロード時に発火。ブロック不可。

入力フィールド: `file_path`, `memory_type` (User/Project/Local/Managed), `load_reason` (session_start/nested_traversal/path_glob_match/include/compact), `globs`, `trigger_file_path`, `parent_file_path`

### Notification
通知送信時に発火。ブロック不可。

マッチャー値: `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog`

入力: `message`, `title`, `notification_type`

### StopFailure
API エラーによるターン終了時に発火。出力・終了コードは無視。

マッチャー値: `rate_limit`, `authentication_failed`, `billing_error`, `invalid_request`, `server_error`, `max_output_tokens`, `unknown`

### TeammateIdle (Agent Teams)
チームメイトがアイドル状態になる前に発火。exit 2 で作業続行を強制可能。

### TaskCompleted (Agent Teams)
タスク完了マーク時に発火。exit 2 で完了を阻止可能。

### ConfigChange
設定ファイル変更時に発火。`policy_settings` 以外はブロック可能。

マッチャー値: `user_settings`, `project_settings`, `local_settings`, `policy_settings`, `skills`

### CwdChanged
作業ディレクトリ変更時に発火。ブロック不可。`CLAUDE_ENV_FILE` にアクセス可能。

出力: `watchPaths` (FileChanged の監視対象を動的設定)

### FileChanged
監視ファイルの変更時に発火。ブロック不可。`CLAUDE_ENV_FILE` にアクセス可能。

マッチャー: ファイルのベース名 (例: `.envrc|.env`)

入力: `file_path`, `event` (change/add/unlink)

### WorktreeCreate / WorktreeRemove
ワークツリー作成/削除時に発火。Git 以外の VCS (SVN, Perforce等) に対応可能。

### PreCompact / PostCompact
コンパクション前後に発火。ブロック不可。

マッチャー: `manual`, `auto`

PostCompact 入力: `compact_summary` (生成されたサマリー)

### Elicitation / ElicitationResult
MCP サーバーのユーザー入力リクエスト時に発火。

出力 action: `accept`, `decline`, `cancel`

### SessionEnd
セッション終了時に発火。ブロック不可。デフォルトタイムアウト 1.5秒。

reason: `clear`, `resume`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other`

タイムアウト変更: `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` 環境変数

---

## 14. プロンプトベースのフック (`type: "prompt"`)

LLM を使用して条件を評価。カスタムスクリプト不要でポリシーを適用。

```json
{
  "type": "prompt",
  "prompt": "Evaluate if Claude should stop: $ARGUMENTS. Check if all tasks are complete.",
  "model": "haiku",
  "timeout": 30
}
```

- `$ARGUMENTS` はフック入力 JSON に自動置換
- LLM レスポンス: `{ "ok": true }` (許可) or `{ "ok": false, "reason": "..." }` (ブロック)
- 対応イベント: PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, Stop, SubagentStop, TaskCompleted, UserPromptSubmit

---

## 15. エージェントベースのフック (`type: "agent"`)

マルチターンツールアクセスを持つサブエージェントを生成して条件を検証。

```json
{
  "type": "agent",
  "prompt": "Verify that all unit tests pass. Run the test suite and check the results. $ARGUMENTS",
  "timeout": 120
}
```

- Read, Grep, Glob 等のツールを使用して調査可能
- 最大 50 ターン
- プロンプトフックと同じレスポンススキーマ
- 対応イベント: プロンプトベースと同一

---

## 16. 非同期フック (`async: true`)

長時間タスクをバックグラウンドで実行。Claude はブロックされずに作業を続行。

```json
{
  "type": "command",
  "command": "/path/to/run-tests.sh",
  "async": true,
  "timeout": 120
}
```

- `type: "command"` フックのみ対応
- ブロック/決定制御は不可 (アクションは既に進行済み)
- 出力の `systemMessage` / `additionalContext` は次の会話ターンで配信
- 同一フックの複数発火で重複排除なし

---

## 17. CLAUDE_ENV_FILE による環境変数永続化

SessionStart / CwdChanged / FileChanged フックで利用可能:

```bash
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=production' >> "$CLAUDE_ENV_FILE"
  echo 'export DEBUG_LOG=true' >> "$CLAUDE_ENV_FILE"
fi
```

書き込まれた変数はセッション中の後続の全 Bash コマンドで利用可能。

---

## 18. セキュリティベストプラクティス

- **入力のサニタイズ**: stdin の JSON データを盲目的に信頼しない
- **シェル変数の引用**: `"$VAR"` を使用 (`$VAR` ではなく)
- **パストラバーサル防止**: ファイルパスで `..` をチェック
- **絶対パスの使用**: スクリプトの完全なパスを指定、`"$CLAUDE_PROJECT_DIR"` を活用
- **機密ファイルのスキップ**: `.env`, `.git/`, 鍵ファイルを避ける
- **failClosed**: セキュリティ重要なフックには `failClosed: true` を設定

### フック実行権限
コマンドフックはシステムユーザーの**完全な権限**で実行される。ユーザーアカウントがアクセス可能な全ファイルを変更・削除・アクセス可能。

### デバッグ
`claude --debug` でフック実行の詳細確認 (マッチ、終了コード、出力)。

---

## 19. フックタイプ対応表 (全イベント)

### 全4タイプ対応 (command/http/prompt/agent)
PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, Stop, SubagentStop, TaskCompleted, UserPromptSubmit

### command のみ対応
SessionStart, SessionEnd, SubagentStart, Notification, StopFailure, TeammateIdle, ConfigChange, CwdChanged, FileChanged, InstructionsLoaded, PreCompact, PostCompact, Elicitation, ElicitationResult, WorktreeCreate, WorktreeRemove

---

*cursor-hooks-reference v2.0 — 2026-03-26 全量読取統合版 (Cursor Hooks + Claude Code Hooks)*
