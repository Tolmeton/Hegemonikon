# MECE Phase 1: Boulésis cleanup
# Move vision typos to Helm, remove empty/legacy dirs

$ErrorActionPreference = "Stop"
$base = "C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\10_知性｜Nous\04_企画｜Boulēsis"

Write-Host "=== Phase 1: Boulésis MECE cleanup ===" -ForegroundColor Cyan

# 1. Move hgk_vision_v4.typos to Helm
$src = Join-Path $base "C_ビジョン｜Vision\hgk_vision_v4.typos"
$dst = Join-Path $base "00_舵｜Helm\hgk_vision_v4.typos"
if (Test-Path $src) {
    Move-Item -Path $src -Destination $dst -Force
    Write-Host "[OK] Moved hgk_vision_v4.typos to Helm" -ForegroundColor Green
} else {
    Write-Host "[SKIP] hgk_vision_v4.typos already moved" -ForegroundColor Yellow
}

# 2. Remove empty legacy dirs (all confirmed empty)
$targets = @(
    "A_アゴラ｜Agora",
    "F_OSS随伴｜OssAdjoint",
    "D_自律提案｜Autophonos",
    "E_美論｜Kalon",
    "C_ビジョン｜Vision",
    "B_バイトボット｜Bytebot",
    "B_活用｜Praxis",
    "07_知覚｜Perception",
    "08_形式導出｜FormalDerivation"
)

foreach ($dir in $targets) {
    $path = Join-Path $base $dir
    if (Test-Path $path) {
        $fileCount = (Get-ChildItem $path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
        if ($fileCount -eq 0) {
            Remove-Item $path -Recurse -Force
            Write-Host "[OK] Removed: $dir (empty)" -ForegroundColor Green
        } else {
            Write-Host "[WARN] $dir has $fileCount files - skipping" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[SKIP] $dir not found" -ForegroundColor Yellow
    }
}

# 3. Show result
Write-Host ""
Write-Host "=== Result ===" -ForegroundColor Cyan
Get-ChildItem $base -Directory | ForEach-Object { Write-Host "  $($_.Name)" }
$count = (Get-ChildItem $base -Directory | Measure-Object).Count
Write-Host "Total: $count directories"
