# `.github/hooks`（GitHub Copilot 用）

このディレクトリは **GitHub Copilot CLI / Copilot エージェントが読む JSON フック**（`.github/hooks/*.json`）用です。

## このリポジトリでの方針

- **Claude Code のフック（マスター）:** `.claude/settings.json` で定義し、実行スクリプトは **`.claude/hooks/`** に置く。
- **Copilot 形式のフックが必要になったら** ここに JSON を追加する（[Copilot hooks のスキーマ](https://docs.github.com/copilot) に準拠）。

両者の形式は互換ではないため、**同一ロジックを共有したい場合は** スクリプトを `.claude/hooks/` に置き、Copilot 側のフックからそのスクリプトを呼ぶ、などの構成にすると保守しやすいです。
