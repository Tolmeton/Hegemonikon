<#
.SYNOPSIS
  OpenAI 互換ブリッジ (mekhane.ochema.openai_compat_server) を起動する。

.PARAMETER TokenPath
  Bearer 用トークンを1行で保存したファイル。無い場合は新規生成して保存する。

.PARAMETER AllowRemote
  cloudflared 等の非ループバック接続を許可 (既定: $true)

.PARAMETER Port
  既定 8765

.PARAMETER Background
  別ウィンドウで起動する。
#>
param(
    [string] $TokenPath = "$env:USERPROFILE\.hgk_openai_compat_token.txt",
    [switch] $AllowRemote = $true,
    [int] $Port = 8765,
    [switch] $Background
)

$ErrorActionPreference = "Stop"
$srcRoot = & (Join-Path $PSScriptRoot "Resolve-MekhaneSrcRoot.ps1")

if (-not (Test-Path $TokenPath)) {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $token = -join ($bytes | ForEach-Object { '{0:x2}' -f $_ })
    $token | Set-Content -Path $TokenPath -Encoding utf8
    Write-Host "Created token file: $TokenPath"
} else {
    Write-Host "Using existing token file: $TokenPath"
}

$tokenValue = (Get-Content $TokenPath -Raw).Trim()

if ($Background) {
    $runner = Join-Path $env:TEMP "ochema_bridge_run_$(Get-Random).ps1"
    $allow = if ($AllowRemote) { "`$env:HGK_OPENAI_COMPAT_ALLOW_REMOTE = '1'" } else { "" }
    @"
`$env:HGK_OPENAI_COMPAT_TOKEN = '$tokenValue'
$allow
`$env:HGK_OPENAI_COMPAT_PORT = '$Port'
Set-Location -LiteralPath '$srcRoot'
python -m mekhane.ochema.openai_compat_server
"@ | Set-Content -Path $runner -Encoding UTF8
    Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $runner
    Write-Host "Bridge started in new window."
    Write-Host "API Key (paste into Cursor): see $TokenPath"
    Write-Host "Base URL (local): http://127.0.0.1:$Port/v1"
} else {
    $env:HGK_OPENAI_COMPAT_TOKEN = $tokenValue
    if ($AllowRemote) { $env:HGK_OPENAI_COMPAT_ALLOW_REMOTE = "1" }
    $env:HGK_OPENAI_COMPAT_PORT = "$Port"
    Set-Location -LiteralPath $srcRoot
    & python -m mekhane.ochema.openai_compat_server
}
