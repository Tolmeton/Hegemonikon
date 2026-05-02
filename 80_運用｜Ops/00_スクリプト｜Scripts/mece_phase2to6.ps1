<# MECE Phase 2-6: All remaining phases in one script #>
$ErrorActionPreference = "Continue"

function Resolve-HGK($pattern) { return (Get-Item $pattern).FullName }

$root = Resolve-HGK 'C:\Users\makar\Sync\oikos\01_*'
$nous = Resolve-HGK "$root\10_*"
$mekhane = Resolve-HGK "$root\20_*"
$mneme = Resolve-HGK "$root\30_*"
$organon = Resolve-HGK "$root\40_*"
$peira = Resolve-HGK "$root\60_*"
$ops = Resolve-HGK "$root\80_*"
$archive = Resolve-HGK "$root\90_*"

Write-Host "Root: $root" -ForegroundColor DarkGray

# ============================================================
Write-Host "`n=== PHASE 2: 10_Nous ===" -ForegroundColor Cyan
# ============================================================

# 2a. Delete empty C_Horos
$horos = Join-Path $nous '01_制約｜Constraints\C_ホロス｜Horos'
if (Test-Path $horos) {
    $fc = (Get-ChildItem $horos -Recurse -File -EA SilentlyContinue | Measure).Count
    if ($fc -eq 0) { Remove-Item $horos -Recurse -Force; Write-Host "[OK] Removed C_Horos (empty)" -ForegroundColor Green }
    else { Write-Host "[WARN] C_Horos has $fc files" -ForegroundColor Yellow }
} else { Write-Host "[SKIP] C_Horos gone" -ForegroundColor DarkGray }

# 2b. Create 09_Archeia
$archeia = Join-Path $nous '09_保管｜Archeia'
if (-not (Test-Path $archeia)) {
    New-Item $archeia -ItemType Directory -Force | Out-Null
    Write-Host "[OK] Created 09_Archeia" -ForegroundColor Green
} else { Write-Host "[SKIP] 09_Archeia exists" -ForegroundColor DarkGray }

# 2c. Delete empty projects in Boulésis
$proj = Join-Path $nous '04_企画｜Boulēsis\projects'
if (Test-Path $proj) {
    $fc = (Get-ChildItem $proj -Recurse -File -EA SilentlyContinue | Measure).Count
    if ($fc -eq 0) { Remove-Item $proj -Recurse -Force; Write-Host "[OK] Removed projects (empty)" -ForegroundColor Green }
    else { Write-Host "[WARN] projects has $fc files" -ForegroundColor Yellow }
} else { Write-Host "[SKIP] projects gone" -ForegroundColor DarkGray }

# ============================================================
Write-Host "`n=== PHASE 3: 20_Mekhane ===" -ForegroundColor Cyan
# ============================================================

# 3a. Move old dirs to Archive
$mekhaneArchive = Join-Path $archive '20_Mekhane_legacy'
if (-not (Test-Path $mekhaneArchive)) { New-Item $mekhaneArchive -ItemType Directory -Force | Out-Null }

$oldMekDirs = @('00_最適化｜Aristos', '01_エージェント｜Bytebot', '02_協調｜Synergeia', '03_消化｜Pepsis', 'Bytebot', 'A_docs')
foreach ($d in $oldMekDirs) {
    $src = Join-Path $mekhane $d
    if (Test-Path $src) {
        $dst = Join-Path $mekhaneArchive $d
        Move-Item $src $dst -Force
        Write-Host "[OK] Archived: $d" -ForegroundColor Green
    } else { Write-Host "[SKIP] $d gone" -ForegroundColor DarkGray }
}

# 3b. Move Assets to 90_Archive
$assets = Join-Path $mekhane '04_アセット｜Assets'
if (Test-Path $assets) {
    $dst = Join-Path $archive '04_Mekhane_Assets'
    Move-Item $assets $dst -Force
    Write-Host "[OK] Assets -> Archive" -ForegroundColor Green
}

# 3c. Move README_organon.md to 40
$orgReadme = Join-Path $mekhane 'README_organon.md'
if (Test-Path $orgReadme) {
    Move-Item $orgReadme (Join-Path $organon 'README_organon.md') -Force
    Write-Host "[OK] README_organon.md -> 40_Organon" -ForegroundColor Green
}

# 3d. Create 1:1 module doc directories
$moduleDocs = @(
    '00_概要｜Overview',
    '01_MCP｜MCP',
    '02_車体｜Ochema',
    '03_解釈｜Hermeneus',
    '04_共感｜Sympatheia',
    '05_樹｜Dendron',
    '06_観察｜Periskope',
    '07_試金石｜Basanos',
    '08_最適化｜Aristos',
    '09_編組｜Symploke',
    '10_想起｜Anamnesis',
    '11_完遂｜Synteleia',
    '12_制作｜Poiema',
    '13_FEP｜FEP',
    '14_分類｜Taxis'
)
foreach ($d in $moduleDocs) {
    $p = Join-Path $mekhane $d
    if (-not (Test-Path $p)) {
        New-Item $p -ItemType Directory -Force | Out-Null
        Write-Host "[OK] Created doc dir: $d" -ForegroundColor Green
    } else { Write-Host "[SKIP] $d exists" -ForegroundColor DarkGray }
}

# ============================================================
Write-Host "`n=== PHASE 4: 30_Mneme ===" -ForegroundColor Cyan
# ============================================================

# 4a. Delete empty 02_Archive
$emptyArc = Join-Path $mneme '02_アーカイブ｜Archive'
if (Test-Path $emptyArc) {
    $fc = (Get-ChildItem $emptyArc -Recurse -File -EA SilentlyContinue | Measure).Count
    if ($fc -eq 0) { Remove-Item $emptyArc -Recurse -Force; Write-Host "[OK] Removed 02_Archive (empty)" -ForegroundColor Green }
    else { Write-Host "[WARN] 02_Archive has $fc files" -ForegroundColor Yellow }
}

# 4b. Move 06_Archive content to 90
$arc06 = Join-Path $mneme '06_アーカイブ｜Archive'
if (Test-Path $arc06) {
    $dst = Join-Path $archive '30_Mneme_Archive'
    if (-not (Test-Path $dst)) { New-Item $dst -ItemType Directory -Force | Out-Null }
    Get-ChildItem $arc06 | Move-Item -Destination $dst -Force
    Remove-Item $arc06 -Recurse -Force
    Write-Host "[OK] 06_Archive -> 90_Archive, removed" -ForegroundColor Green
}

# 4c. Records: merge ROM duplicates into c_ROM|rom
$records = Join-Path $mneme '01_記録｜Records'
$romTarget = Join-Path $records 'c_ROM｜rom'

$romOld1 = Join-Path $records 'c_ROM_rom'
if (Test-Path $romOld1) {
    Get-ChildItem $romOld1 -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($romOld1.Length + 1)
        $dstFile = Join-Path $romTarget $rel
        $dstDir = Split-Path $dstFile -Parent
        if (-not (Test-Path $dstDir)) { New-Item $dstDir -ItemType Directory -Force | Out-Null }
        if (-not (Test-Path $dstFile)) { Move-Item $_.FullName $dstFile -Force }
    }
    Remove-Item $romOld1 -Recurse -Force
    Write-Host "[OK] c_ROM_rom merged into c_ROM|rom" -ForegroundColor Green
}

$romOld2 = Join-Path $records 'c_蒸留_rom'
if (Test-Path $romOld2) {
    Get-ChildItem $romOld2 -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($romOld2.Length + 1)
        $dstFile = Join-Path $romTarget $rel
        $dstDir = Split-Path $dstFile -Parent
        if (-not (Test-Path $dstDir)) { New-Item $dstDir -ItemType Directory -Force | Out-Null }
        if (-not (Test-Path $dstFile)) { Move-Item $_.FullName $dstFile -Force }
    }
    Remove-Item $romOld2 -Recurse -Force
    Write-Host "[OK] c_蒸留_rom merged into c_ROM|rom" -ForegroundColor Green
}

# 4d. Records: merge output duplicates into d_成果|artifacts
$outTarget = Join-Path $records 'd_成果｜artifacts'

$outOld1 = Join-Path $records 'd_出力_outputs'
if (Test-Path $outOld1) {
    Get-ChildItem $outOld1 -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($outOld1.Length + 1)
        $dstFile = Join-Path $outTarget $rel
        $dstDir = Split-Path $dstFile -Parent
        if (-not (Test-Path $dstDir)) { New-Item $dstDir -ItemType Directory -Force | Out-Null }
        if (-not (Test-Path $dstFile)) { Move-Item $_.FullName $dstFile -Force }
    }
    Remove-Item $outOld1 -Recurse -Force
    Write-Host "[OK] d_出力_outputs merged into d_成果|artifacts" -ForegroundColor Green
}

$outOld2 = Join-Path $records 'e_出力｜outputs'
if (Test-Path $outOld2) {
    Get-ChildItem $outOld2 -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($outOld2.Length + 1)
        $dstFile = Join-Path $outTarget $rel
        $dstDir = Split-Path $dstFile -Parent
        if (-not (Test-Path $dstDir)) { New-Item $dstDir -ItemType Directory -Force | Out-Null }
        if (-not (Test-Path $dstFile)) { Move-Item $_.FullName $dstFile -Force }
    }
    Remove-Item $outOld2 -Recurse -Force
    Write-Host "[OK] e_出力|outputs merged into d_成果|artifacts" -ForegroundColor Green
}

# 4e. Move z_legacy to Archive
$legacy = Join-Path $records 'z_旧構造_legacy'
if (Test-Path $legacy) {
    $fc = (Get-ChildItem $legacy -Recurse -File -EA SilentlyContinue | Measure).Count
    if ($fc -eq 0) { Remove-Item $legacy -Recurse -Force; Write-Host "[OK] z_legacy removed (empty)" -ForegroundColor Green }
    else {
        $dst = Join-Path $archive '30_Records_legacy'
        Move-Item $legacy $dst -Force
        Write-Host "[OK] z_legacy -> Archive ($fc files)" -ForegroundColor Green
    }
}

# ============================================================
Write-Host "`n=== PHASE 5: 40 rename + 50 create ===" -ForegroundColor Cyan
# ============================================================

# 5a. Rename 40_応用 -> 40_作品｜Poiema
$newOrganon = Join-Path $root '40_作品｜Poiema'
if ((Test-Path $organon) -and -not (Test-Path $newOrganon)) {
    Rename-Item $organon '40_作品｜Poiema'
    Write-Host "[OK] 40 renamed to 40_作品|Poiema" -ForegroundColor Green
    $organon = $newOrganon
} else { Write-Host "[SKIP] 40 rename" -ForegroundColor DarkGray }

# 5b. Create 50_外部｜External
$external = Join-Path $root '50_外部｜External'
if (-not (Test-Path $external)) {
    New-Item $external -ItemType Directory -Force | Out-Null
    Write-Host "[OK] Created 50_外部|External" -ForegroundColor Green
}

# 5c. Move Bytebot and openclaw from 40 to 50
$poiema = Join-Path $root '40_作品｜Poiema'
foreach ($ext in @('Bytebot', 'openclaw')) {
    $src = Join-Path $poiema $ext
    if (Test-Path $src) {
        $dst = Join-Path $external $ext
        Move-Item $src $dst -Force
        Write-Host "[OK] $ext -> 50_External" -ForegroundColor Green
    }
}

# ============================================================
Write-Host "`n=== PHASE 6: 60/80/90 cleanup ===" -ForegroundColor Cyan
# ============================================================

# 6a. perception_poc duplicate check in 60_Peira
$poc1 = Join-Path $peira 'perception_poc'
$poc2 = Join-Path $peira '04_知覚PoC｜PerceptionPoc'
if ((Test-Path $poc1) -and (Test-Path $poc2)) {
    $fc = (Get-ChildItem $poc1 -Recurse -File -EA SilentlyContinue | Measure).Count
    if ($fc -eq 0) { Remove-Item $poc1 -Recurse -Force; Write-Host "[OK] perception_poc removed (empty)" -ForegroundColor Green }
    else { Write-Host "[INFO] perception_poc has $fc files - manual review needed" -ForegroundColor Yellow }
}

# 6b. Infrastructure in 80_Ops -> rename to standard
$infra = Join-Path $ops 'Infrastructure'
if (Test-Path $infra) {
    $fc = (Get-ChildItem $infra -Recurse -File -EA SilentlyContinue | Measure).Count
    if ($fc -eq 0) { Remove-Item $infra -Recurse -Force; Write-Host "[OK] Infrastructure removed (empty)" -ForegroundColor Green }
    else {
        $dst = Join-Path $archive '80_Infrastructure'
        Move-Item $infra $dst -Force
        Write-Host "[OK] Infrastructure -> Archive ($fc files)" -ForegroundColor Green
    }
}

# ============================================================
Write-Host "`n=== FINAL: Summary ===" -ForegroundColor Cyan
# ============================================================
Write-Host "`nTop-level:"
Get-ChildItem $root -Directory | Where-Object { $_.Name -notmatch '^\.' } | ForEach-Object { Write-Host "  $($_.Name)" }

Write-Host "`n20_Mekhane:"
Get-ChildItem (Join-Path $root '20_*') -Directory | ForEach-Object { Write-Host "  $($_.Name)" }

Write-Host "`n30_Mneme Records:"
Get-ChildItem (Join-Path $root '30_*\01_記録｜Records') -Directory -EA SilentlyContinue | ForEach-Object { Write-Host "  $($_.Name)" }

Write-Host "`nDone!" -ForegroundColor Green
