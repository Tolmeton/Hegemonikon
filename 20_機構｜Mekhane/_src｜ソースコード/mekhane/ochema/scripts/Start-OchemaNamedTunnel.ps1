<#
.SYNOPSIS
  名前付き Cloudflare トンネルを config.yml で起動する (固定ホスト名用)。

.PARAMETER ConfigPath
  既定: %USERPROFILE%\.cloudflared\config.yml
#>
param(
    [string] $ConfigPath = "$env:USERPROFILE\.cloudflared\config.yml"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $ConfigPath)) {
    throw "Missing $ConfigPath. Copy cloudflared_config.example.yml from mekhane/ochema/, run Register-NamedTunnel.ps1, fill tunnel UUID and credentials path. See README_CURSOR_OPENAI.md."
}

$cf = Get-Command cloudflared.exe -ErrorAction SilentlyContinue
if (-not $cf) {
    throw "cloudflared.exe not found on PATH."
}

Write-Host "Running: cloudflared tunnel --config $ConfigPath run"
& cloudflared.exe tunnel --config $ConfigPath run
