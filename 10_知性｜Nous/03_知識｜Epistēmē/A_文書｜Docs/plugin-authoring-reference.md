```typos
#prompt plugin-authoring-reference
#syntax: v8
#depth: L2

<:role: プラグイン制作リファレンス — Cursor IDE + Claude Code 統合ドキュメント
  2つの公式ドキュメントを MECE にマージした制作用知識基盤。:>

<:goal: HGK プラグイン制作に必要な全仕様を一元管理する :>

<:context:
  - [knowledge] 📍 観測: 2026-03-26 / SOURCE: cursor.com/docs/plugins + code.claude.com/docs
  - [knowledge] 元ファイル: cursor-plugin-reference.md.resolved (Cursor IDE) + Claude Code Plugin Reference (code.claude.com)
  - [knowledge] マージ方針: 共通部分を統合し、各プラットフォーム固有仕様を明示的にラベル付け
/context:>
```

---

# プラグイン制作リファレンス (Cursor IDE + Claude Code 統合)

> SOURCE: cursor.com/docs/plugins + code.claude.com/docs  
> 📅 情報鮮度: 2026-03-26 取得 / FRESH

---

## 1. プラグインとは

ルール・スキル・エージェント・コマンド・MCP サーバー・フック等を**配布可能なバンドル**にまとめたもの。

| 項目 | Cursor IDE | Claude Code |
|:-----|:-----------|:------------|
| CLI 対応 | 未対応 | `claude plugin install/uninstall/enable/disable/update` |
| Cloud Agents | MCP サーバーのみ | MCP + LSP サーバー |
| 配布方式 | Git リポジトリ → Marketplace 審査 | マーケットプレイス (Git リポジトリベース) |
| マニフェスト場所 | `.cursor-plugin/plugin.json` | `.claude-plugin/plugin.json` |
| コンポーネント | rules, skills, agents, commands, hooks, MCP | skills, agents, commands, hooks, MCP, **LSP**, **channels** |

---

## 2. ディレクトリ構造

### 2.1 Cursor IDE

```text
my-plugin/
├── .cursor-plugin/
│   └── plugin.json          # 必須: マニフェスト
├── rules/                   # .mdc ファイル
│   └── coding-standards.mdc
├── skills/                  # SKILL.md を含むサブディレクトリ
│   └── code-reviewer/
│       └── SKILL.md
├── agents/                  # カスタムエージェント .md
│   └── security-reviewer.md
├── commands/                # コマンド .md/.txt
│   └── deploy.md
├── hooks/
│   └── hooks.json
├── .mcp.json                # MCP サーバー定義
├── assets/
│   └── logo.svg
├── scripts/                 # フック・ユーティリティ
│   └── format-code.py
└── README.md
```

### 2.2 Claude Code

```text
enterprise-plugin/
├── .claude-plugin/           # メタデータディレクトリ（オプション）
│   └── plugin.json
├── commands/                 # デフォルトコマンド場所
│   ├── status.md
│   └── logs.md
├── agents/                   # Subagent マークダウンファイル
│   ├── security-reviewer.md
│   └── performance-tester.md
├── skills/                   # <name>/SKILL.md 構造
│   ├── code-reviewer/
│   │   └── SKILL.md
│   └── pdf-processor/
│       ├── SKILL.md
│       └── scripts/
├── hooks/
│   ├── hooks.json
│   └── security-hooks.json
├── settings.json             # プラグインデフォルト設定 [Claude Code 固有]
├── .mcp.json
├── .lsp.json                 # LSP サーバー設定 [Claude Code 固有]
├── scripts/
│   ├── security-scan.sh
│   └── format-code.py
├── LICENSE
└── CHANGELOG.md
```

> ⚠️ 共通: コンポーネントディレクトリは `.cursor-plugin/` / `.claude-plugin/` 内ではなく**プラグインルート**に配置。マニフェストのみメタデータディレクトリに配置。

---

## 3. マニフェスト (`plugin.json`)

### 3.1 必須フィールド（共通）

| フィールド | 型 | 制約 |
|:----------|:---|:-----|
| `name` | string | 小文字ケバブケース。英数字+ハイフン+ピリオド。先頭末尾は英数字 |

マニフェストはオプション。省略時はデフォルト場所からコンポーネントを自動検出し、ディレクトリ名から名前を導出。

### 3.2 メタデータフィールド（共通）

| フィールド | 型 | 説明 |
|:----------|:---|:-----|
| `description` | string | 簡潔な説明 |
| `version` | string | セマンティックバージョン (例: `1.0.0`) |
| `author` | object | `name` (必須), `email` (任意), `url` (任意) |
| `homepage` | string | ドキュメント URL |
| `repository` | string | ソースコード URL |
| `license` | string | 例: `MIT` |
| `keywords` | array | 検索用タグ |

### 3.3 コンポーネントパスフィールド（共通）

| フィールド | 型 | 説明 |
|:----------|:---|:-----|
| `commands` | string/array | コマンドファイル/ディレクトリ |
| `agents` | string/array | エージェントファイル |
| `skills` | string/array | スキルディレクトリ |
| `hooks` | string/object | フック設定 |
| `mcpServers` | string/object/array | MCP 設定 |

> ⚠️ **パス動作ルール**: カスタムパスはデフォルトディレクトリを**置き換えるのではなく補足**する。`commands/` が存在する場合、カスタムコマンドパスに加えてロードされる。全パスはプラグインルートに相対的で `./` で始まる必要がある。

### 3.3a 名前空間 [Claude Code]

`name` はコンポーネントの名前空間に使用。例: プラグイン名 `plugin-dev` のエージェント `agent-creator` は UI で `plugin-dev:agent-creator` として表示される。

### 3.4 Cursor IDE 固有フィールド

| フィールド | 型 | 説明 |
|:----------|:---|:-----|
| `logo` | string | 相対パス or 絶対 URL |
| `rules` | string/array | .mdc ルールファイルパス |

### 3.5 Claude Code 固有フィールド

| フィールド | 型 | 説明 |
|:----------|:---|:-----|
| `outputStyles` | string/array | 出力スタイルファイル/ディレクトリ |
| `lspServers` | string/object | LSP サーバー設定 |
| `userConfig` | object | ユーザー設定可能な値 (有効化時にプロンプト) |
| `channels` | array | メッセージ注入用チャネル宣言 |

---

## 4. コンポーネント形式

### 4.1 Rules [Cursor IDE 固有]

```yaml
---
description: ルールの概要
alwaysApply: true        # true=自動適用 / false=手動
globs: "**/*.ts"         # 対象ファイルパターン (任意)
---
ルール本文 (Markdown)
```

- 配置: `rules/` ディレクトリ、拡張子 `.mdc`
- **Always / Agent Decides / Manual** の3モード切り替え

### 4.2 Skills（共通）

```yaml
---
name: skill-name         # 小文字ケバブケース
description: 説明文
---
# スキル本文 (Markdown)
```

- 配置: `skills/{skill-name}/SKILL.md`
- チャットで `/skill-name` で手動呼び出し可能
- Skills は SKILL.md の横にサポートファイル (scripts/ 等) を含めることができる

### 4.3 Agents（共通 + Claude Code 拡張）

```yaml
---
name: agent-name
description: 説明文
model: sonnet              # [Claude Code 固有]
effort: medium             # [Claude Code 固有]
maxTurns: 20               # [Claude Code 固有]
disallowedTools: Write, Edit  # [Claude Code 固有]
---
# エージェント本文 (Markdown)
```

- 配置: `agents/` ディレクトリ
- **Claude Code 追加 frontmatter**: `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`, `isolation` (唯一有効値: `"worktree"`)
- **制限**: `hooks`, `mcpServers`, `permissionMode` はプラグインエージェントでは不可

### 4.4 Commands（共通）

```yaml
---
name: command-name
description: 説明文
---
# コマンド本文
```

- 配置: `commands/` ディレクトリ
- 拡張子: `.md`, `.mdc`, `.markdown`, `.txt`

### 4.5 Hooks

#### Cursor IDE イベント

| カテゴリ | イベント |
|:---------|:--------|
| Agent | `sessionStart`, `sessionEnd`, `preToolUse`, `postToolUse`, `beforeShellExecution`, `afterShellExecution`, `beforeMCPExecution`, `afterMCPExecution`, `beforeReadFile`, `afterFileEdit`, `beforeSubmitPrompt`, `preCompact`, `stop`, `afterAgentResponse`, `afterAgentThought` |
| Tab | `beforeTabFileRead`, `afterTabFileEdit` |

#### Claude Code イベント（より詳細）

| イベント | トリガータイミング |
|:--------|:------------------|
| `SessionStart` | セッション開始/再開時 |
| `UserPromptSubmit` | プロンプト送信時 (処理前) |
| `PreToolUse` | ツール実行前 (ブロック可能) |
| `PermissionRequest` | 権限ダイアログ表示時 |
| `PostToolUse` | ツール成功後 |
| `PostToolUseFailure` | ツール失敗後 |
| `Notification` | 通知送信時 |
| `SubagentStart` / `SubagentStop` | サブエージェント起動/終了 |
| `Stop` / `StopFailure` | 応答完了/API エラー |
| `TeammateIdle` | チームメイトがアイドル化直前 |
| `TaskCompleted` | タスク完了マーク時 |
| `InstructionsLoaded` | CLAUDE.md / rules ロード時 |
| `ConfigChange` | 設定ファイル変更時 |
| `CwdChanged` | 作業ディレクトリ変更時 |
| `FileChanged` | 監視ファイル変更時 (matcher 指定) |
| `WorktreeCreate` / `WorktreeRemove` | ワークツリー作成/削除時 |
| `PreCompact` / `PostCompact` | コンテキスト圧縮前後 |
| `Elicitation` / `ElicitationResult` | MCP ユーザー入力要求/応答 |
| `SessionEnd` | セッション終了時 |

#### Claude Code Hook タイプ

| タイプ | 説明 |
|:-------|:-----|
| `command` | シェルコマンド/スクリプト実行 |
| `http` | イベント JSON を URL へ POST |
| `prompt` | LLM でプロンプト評価 (`$ARGUMENTS` 使用) |
| `agent` | ツール付き agentic verifier 実行 |

### 4.6 MCP サーバー（共通）

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": { "KEY": "${ENV_VAR}" }
    }
  }
}
```

- ルートの `.mcp.json` は自動検出
- カスタムパス・インライン設定は `plugin.json` の `mcpServers` で指定

### 4.7 LSP サーバー [Claude Code 固有]

```json
// .lsp.json
{
  "go": {
    "command": "gopls",
    "args": ["serve"],
    "extensionToLanguage": { ".go": "go" }
  }
}
```

**必須**: `command`, `extensionToLanguage`

**オプション**: `args`, `transport` (`stdio`/`socket`), `env`, `initializationOptions`, `settings`, `workspaceFolder`, `startupTimeout`, `shutdownTimeout`, `restartOnCrash`, `maxRestarts`

> ⚠️ 言語サーバーバイナリは別途インストールが必要

**利用可能な LSP プラグイン (公式):**

| プラグイン | 言語サーバー | インストール |
|:----------|:-----------|:-----------|
| `pyright-lsp` | Pyright (Python) | `pip install pyright` or `npm install -g pyright` |
| `typescript-lsp` | TypeScript LS | `npm install -g typescript-language-server typescript` |
| `rust-lsp` | rust-analyzer | rust-analyzer 公式手順参照 |

### 4.8 ユーザー設定 [Claude Code 固有]

```json
{
  "userConfig": {
    "api_endpoint": { "description": "...", "sensitive": false },
    "api_token": { "description": "...", "sensitive": true }
  }
}
```

- `${user_config.KEY}` として MCP/LSP/hook/skill/agent 内で置換可能
- 環境変数 `CLAUDE_PLUGIN_OPTION_<KEY>` としてもエクスポート
- 機密値はシステムキーチェーンに保存 (約 2KB 制限)

### 4.9 チャネル [Claude Code 固有]

```json
{
  "channels": [{
    "server": "telegram",
    "userConfig": {
      "bot_token": { "description": "...", "sensitive": true },
      "owner_id": { "description": "...", "sensitive": false }
    }
  }]
}
```

- `server` は `mcpServers` のキーと一致が必要

---

## 5. コンポーネント自動検出（共通）

| コンポーネント | デフォルト配置 | 検出方法 |
|:-------------|:-------------|:--------|
| Skills | `skills/` | `SKILL.md` を含むサブディレクトリ |
| Rules | `rules/` | .md, .mdc, .markdown [Cursor 固有] |
| Agents | `agents/` | .md, .mdc, .markdown |
| Commands | `commands/` | .md, .mdc, .markdown, .txt |
| Hooks | `hooks/hooks.json` | イベント名解析 |
| MCP | `.mcp.json` | サーバーエントリ解析 |
| LSP | `.lsp.json` | サーバーエントリ解析 [Claude Code 固有] |
| Root Skill | ルートの `SKILL.md` | skills/ も manifest もない場合のみ |

---

## 6. 環境変数 [Claude Code 固有]

| 変数 | 説明 |
|:-----|:-----|
| `${CLAUDE_PLUGIN_ROOT}` | プラグインインストールディレクトリへの絶対パス (更新で変更される — ここに書き込んだファイルは更新後に保持されない) |
| `${CLAUDE_PLUGIN_DATA}` | 更新後も保持される永続ディレクトリ (`~/.claude/plugins/data/{id}/`) |

- skill/agent コンテンツ、hook コマンド、MCP/LSP 設定にインライン置換
- hook/MCP/LSP サブプロセスに環境変数としてエクスポート
- `${CLAUDE_PLUGIN_DATA}` は初回参照時に自動作成

### 6.1 永続データディレクトリ ID 規則

`{id}` は `a-z`, `A-Z`, `0-9`, `_`, `-` 以外の文字が `-` に置換。例: `formatter@my-marketplace` → `~/.claude/plugins/data/formatter-my-marketplace/`

アンインストール時、最後のスコープから削除すると `${CLAUDE_PLUGIN_DATA}` も自動削除。`--keep-data` で保持可能。

### 6.2 永続データ更新パターン (SessionStart hook)

プラグイン更新で依存関係マニフェストが変わった場合の再インストールパターン:

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "diff -q \"${CLAUDE_PLUGIN_ROOT}/package.json\" \"${CLAUDE_PLUGIN_DATA}/package.json\" >/dev/null 2>&1 || (cd \"${CLAUDE_PLUGIN_DATA}\" && cp \"${CLAUDE_PLUGIN_ROOT}/package.json\" . && npm install) || rm -f \"${CLAUDE_PLUGIN_DATA}/package.json\""
      }]
    }]
  }
}
```

- `diff` は保存コピー不足 or バンドルコピーとの差異でゼロ以外終了 → 初回実行 + 依存関係変更の両方をカバー
- `npm install` 失敗時、末尾の `rm` がコピーマニフェストを削除 → 次セッションで再試行

**バンドルスクリプトから永続 node_modules を参照する MCP 設定例:**

```json
{
  "mcpServers": {
    "routines": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/server.js"],
      "env": { "NODE_PATH": "${CLAUDE_PLUGIN_DATA}/node_modules" }
    }
  }
}
```

---

## 7. インストールスコープ [Claude Code 固有]

| スコープ | 設定ファイル | ユースケース |
|:--------|:-----------|:-----------|
| `user` | `~/.claude/settings.json` | 全プロジェクト共通 (デフォルト) |
| `project` | `.claude/settings.json` | チーム共有 (VCS 経由) |
| `local` | `.claude/settings.local.json` | プロジェクト固有 (gitignored) |
| `managed` | 管理設定 | 管理プラグイン (読み取り専用) |

---

## 8. プラグインキャッシングとパス制約 [Claude Code 固有]

- マーケットプレイスプラグインは `~/.claude/plugins/cache` にコピーされる
- **パストラバーサル制限**: プラグインルート外への `../` 参照はキャッシュにコピーされないため不可
- **外部依存関係**: シンボリックリンクで対処 (`ln -s /path/to/shared-utils ./shared-utils`)

---

## 9. マルチプラグインリポジトリ [Cursor IDE 固有]

### `marketplace.json` (リポジトリルート `.cursor-plugin/` 内)

```json
{
  "name": "marketplace-name",
  "owner": { "name": "Org", "email": "..." },
  "metadata": { "description": "..." },
  "plugins": [
    { "name": "plugin-a", "source": "plugin-a", "description": "..." },
    { "name": "plugin-b", "source": "plugin-b", "description": "..." }
  ]
}
```

---

## 10. ローカルテスト

### Cursor IDE

1. `~/.cursor/plugins/local/my-plugin/` にプラグインを配置
2. Cursor 再起動 or `Developer: Reload Window`
3. Windows シンボリックリンク: `mklink /D %USERPROFILE%\.cursor\plugins\local\my-plugin C:\path\to\plugin`

### Claude Code

- `claude --plugin-dir <path>` でセッション内利用
- `claude --debug` でプラグイン読み込み詳細を確認

---

## 11. CLI コマンド [Claude Code 固有]

| コマンド | 説明 | エイリアス |
|:--------|:-----|:---------|
| `claude plugin install <plugin> [-s scope]` | インストール | — |
| `claude plugin uninstall <plugin> [-s scope] [--keep-data]` | アンインストール | `remove`, `rm` |
| `claude plugin enable <plugin> [-s scope]` | 有効化 | — |
| `claude plugin disable <plugin> [-s scope]` | 無効化 | — |
| `claude plugin update <plugin> [-s scope]` | 更新 | — |

- `<plugin>`: プラグイン名 or `plugin-name@marketplace-name`
- `--scope`: `user` (デフォルト), `project`, `local`, `managed` (update のみ)

---

## 12. デバッグとトラブルシューティング

| 問題 | 原因 | 解決策 |
|:-----|:-----|:-------|
| プラグインが読み込まれない | 無効な `plugin.json` | `claude plugin validate` / `/plugin validate` で検証 |
| コマンドが表示されない | ディレクトリ構造が間違い | コンポーネントはルートレベルに配置 (.cursor-plugin/ 内ではない) |
| Hooks が発火しない | スクリプトが実行不可 | `chmod +x script.sh` + shebang 確認 (`#!/bin/bash`) |
| MCP サーバー失敗 | パスが絶対 | `${CLAUDE_PLUGIN_ROOT}` 変数を使用 |
| パスエラー | 絶対パス使用 | 全パスは相対・`./` 始まり |
| LSP 実行可能ファイル未発見 | バイナリ未インストール | 言語サーバーを別途インストール |
| Hook イベント名不一致 | 大文字小文字区別 | `PostToolUse` ✅ / `postToolUse` ❌ |

### 12.1 エラーメッセージ例 [Claude Code]

| エラー | 原因 |
|:-------|:-----|
| `Invalid JSON syntax: Unexpected token }` | コンマ欠落・余分コンマ・未クォート文字列 |
| `Plugin has an invalid manifest ... name: Required` | 必須フィールド不足 |
| `Plugin has a corrupt manifest ... JSON parse error` | JSON 構文エラー |
| `No commands found in plugin ... custom directory` | コマンドパスが存在するが有効ファイルなし |
| `Plugin directory not found at path` | marketplace.json の `source` パスが不正 |
| `conflicting manifests: both plugin.json and marketplace entry` | 重複コンポーネント定義 |

---

## 13. 配布とバージョン管理（共通）

**バージョン形式**: `MAJOR.MINOR.PATCH` (セマンティックバージョニング)

- **MAJOR**: 破壊的変更
- **MINOR**: 後方互換な新機能
- **PATCH**: 後方互換なバグ修正

> ⚠️ Claude Code: バージョンを更新せずにコードを変更した場合、キャッシングのため既存ユーザーに変更が反映されない。

---

## 14. 提出チェックリスト

- [ ] `plugin.json` マニフェストが有効
- [ ] `name` が一意・小文字ケバブケース
- [ ] `description` で目的が明確
- [ ] 全コンポーネントに適切な frontmatter
- [ ] ロゴがリポジトリ内 (相対パス)
- [ ] `README.md` に使い方と設定を記載
- [ ] パスは全て相対 (`..` や絶対パス禁止)
- [ ] ローカルテスト済み
- [ ] (Cursor マルチプラグイン) `marketplace.json` がルートにあり名前が一意
- [ ] (Cursor) 提出: https://cursor.com/marketplace/publish
- [ ] (Claude Code) `CHANGELOG.md` でバージョン履歴を文書化

---

## 15. MECE 差分サマリ

| カテゴリ | Cursor IDE 固有 | Claude Code 固有 | 共通 |
|:---------|:---------------|:-----------------|:-----|
| ルール | rules/ (.mdc, 3モード) | — | — |
| スキル | — | — | ✅ skills/{name}/SKILL.md |
| エージェント | 基本 frontmatter | 拡張 frontmatter (model, effort, maxTurns, isolation) | ✅ agents/ |
| コマンド | — | — | ✅ commands/ |
| フック | イベント名が camelCase | イベント名が PascalCase + http/prompt/agent タイプ | ✅ hooks.json |
| MCP | — | — | ✅ .mcp.json |
| LSP | — | .lsp.json | — |
| ユーザー設定 | — | userConfig + キーチェーン | — |
| チャネル | — | channels (メッセージ注入) | — |
| 環境変数 | — | CLAUDE_PLUGIN_ROOT/DATA | — |
| スコープ | — | user/project/local/managed | — |
| キャッシング | — | plugins/cache + シンボリックリンク | — |
| CLI | — | install/uninstall/enable/disable/update | — |
| マルチプラグイン | marketplace.json | — | — |
| ローカルテスト | ~/.cursor/plugins/local/ | --plugin-dir / --debug | — |
