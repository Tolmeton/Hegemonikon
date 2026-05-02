<#
.SYNOPSIS
  ブリッジをバックグラウンド起動し、その後クイックトンネルを張る (開発用ワンショット)。

.PARAMETER SkipBridge
  既にブリッジが動いているときに指定。
#>
param(
    [switch] $SkipBridge
)

$ErrorActionPreference = "Stop"
$bridge = Join-Path $PSScriptRoot "Start-OchemaBridge.ps1"
$tunnel = Join-Path $PSScriptRoot "Start-OchemaQuickTunnel.ps1"

if (-not $SkipBridge) {
    Write-Host "Starting bridge in new window..."
    & $bridge -Background
    Start-Sleep -Seconds 3
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:8765/health" -UseBasicParsing -TimeoutSec 5
        Write-Host "Health OK:" $r.Content
    } catch {
        Write-Warning "Bridge health check failed; start tunnel anyway after confirming port 8765."
    }
}

Write-Host "Starting quick tunnel (Ctrl+C to stop)..."
& $tunnel
