# Ochema OpenAI 互換ブリッジ — 起動スクリプト

すべて `20_機構｜Mekhane\_src｜ソースコード` をカレントにする必要はなく、**この `scripts` から相対パスで Mekhane ルートを解決**します。

| スクリプト | 用途 |
|------------|------|
| `Resolve-MekhaneSrcRoot.ps1` | 内部用。`pyproject.toml` があるソースルートを返す。 |
| `Start-OchemaBridge.ps1` | ブリッジ起動。トークンは `%USERPROFILE%\.hgk_openai_compat_token.txt`（無ければ生成）。`-Background` で別ウィンドウ。 |
| `Start-OchemaQuickTunnel.ps1` | クイックトンネル（URL は起動のたびに変わる）。 |
| `Start-OchemaNamedTunnel.ps1` | `%USERPROFILE%\.cloudflared\config.yml` で名前付きトンネル（固定ホスト名）。 |
| `Register-NamedTunnel.ps1` | `cloudflared tunnel login` → `tunnel create` まで対話実行。続きは README_CURSOR_OPENAI.md。 |
| `Start-OchemaRemoteStack.ps1` | ブリッジをバックグラウンド起動後、クイックトンネルを開始。 |

**例（PowerShell）:**

```powershell
cd "…\mekhane\ochema\scripts"
.\Start-OchemaBridge.ps1 -Background
.\Start-OchemaQuickTunnel.ps1
```

Cursor の **API Key** は `Get-Content $env:USERPROFILE\.hgk_openai_compat_token.txt`。**Base URL** はトンネル表示 URL に `/v1` を付ける。
