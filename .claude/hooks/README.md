# Claude Code hooks（リポジトリ側）

Sekisho / Pinakas 用の **Python フック本体** は **`%USERPROFILE%\.claude\hooks\`**（Linux/WSL: `~/.claude/hooks/`）に置いています。  
フック定義の正本は **`~/.claude/settings.canonical.json`**、実行時の反映先は **`~/.claude/settings.json`** です（`PreToolUse` / `PostToolUse` / `Stop` 等）。

## ログ

監査・パターン・Pinakas キューは **`~/.claude/hooks/logs/`** に出力されます。別パスにしたい場合は環境変数 **`CLAUDE_HOOK_LOG_DIR`** を設定してください。

## このリポジトリの `settings.json`

Hegemonikon リポジトリの **`.claude/settings.json`** には **プロジェクト用の `permissions` と `additionalDirectories` のみ** を残し、**`hooks` キーは持ちません**（全プロジェクト共通のユーザー設定に一本化）。
