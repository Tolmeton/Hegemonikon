# Gemini CLI 向け入口

**正本:** [`.claude/CLAUDE.md`](.claude/CLAUDE.md)

プロジェクトのルール・フック・エージェント構成は **`.claude/`** がマスターです。  
Gemini CLI 固有の設定は **`.gemini/`** にあります。

- `.gemini/settings.json` — プロジェクト設定
- `.gemini/GEMINI.md` — プロジェクト固有コンテキスト指示
- `~/.gemini/GEMINI.md` — ユーザーレベル指示 (Doctrine v4.3)
- `~/.gemini/mcp_config.json` — MCP サーバー定義
