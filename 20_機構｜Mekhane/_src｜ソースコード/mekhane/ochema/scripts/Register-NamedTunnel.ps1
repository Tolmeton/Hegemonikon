<#
.SYNOPSIS
  Cloudflare 名前付きトンネルを対話的に作成する前準備として login と create を順に実行する。
  固定 DNS は Zero Trust ダッシュボードまたは cloudflared tunnel route dns で別途設定。

.PARAMETER TunnelName
  既定: hgk-ochema
#>
param(
    [string] $TunnelName = "hgk-ochema"
)

$ErrorActionPreference = "Stop"
$cf = Get-Command cloudflared.exe -ErrorAction SilentlyContinue
if (-not $cf) {
    throw "cloudflared.exe not found on PATH."
}

$cfDir = "$env:USERPROFILE\.cloudflared"
if (-not (Test-Path $cfDir)) {
    New-Item -ItemType Directory -Path $cfDir -Force | Out-Null
}

Write-Host "Step 1/2: Browser will open for Cloudflare login..."
& cloudflared.exe tunnel login

Write-Host "Step 2/2: Creating tunnel named '$TunnelName'..."
& cloudflared.exe tunnel create $TunnelName

Write-Host ""
Write-Host "Next: copy mekhane/ochema/cloudflared_config.example.yml to $cfDir\config.yml"
Write-Host "Fill tunnel: UUID from above, credentials-file path to the new .json under $cfDir"
Write-Host "Set ingress hostname to your zone on Cloudflare, service: http://127.0.0.1:8765"
Write-Host "Then in Zero Trust -> Tunnels -> Public Hostname, or: cloudflared tunnel route dns $TunnelName <hostname>"
Write-Host "Run: .\Start-OchemaNamedTunnel.ps1"
