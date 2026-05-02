<#
.SYNOPSIS
  ローカルの OpenAI 互換ブリッジ (既定 http://127.0.0.1:8765) へ Cloudflare クイックトンネルを張る。
  起動のたび URL が変わる (固定 URL には名前付きトンネルが必要)。

.PARAMETER Origin
  既定 http://127.0.0.1:8765
#>
param(
    [string] $Origin = "http://127.0.0.1:8765"
)

$ErrorActionPreference = "Stop"
$cf = Get-Command cloudflared.exe -ErrorAction SilentlyContinue
if (-not $cf) {
    throw "cloudflared.exe not found on PATH. Install: winget install Cloudflare.cloudflared"
}

Write-Host "Starting quick tunnel -> $Origin (URL changes each run)"
Write-Host "Ensure the bridge is running (Start-OchemaBridge.ps1 -Background)."
& cloudflared.exe tunnel --url $Origin
