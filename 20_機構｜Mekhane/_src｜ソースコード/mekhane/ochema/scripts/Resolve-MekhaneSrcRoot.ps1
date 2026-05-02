# Returns the Mekhane Python source root (directory containing `mekhane` package and pyproject.toml).
# Scripts live in mekhane/ochema/scripts → three levels up.
$scriptsDir = $PSScriptRoot
$ochemaDir = Split-Path $scriptsDir -Parent
$mekhaneDir = Split-Path $ochemaDir -Parent
$srcRoot = Split-Path $mekhaneDir -Parent
if (-not (Test-Path (Join-Path $srcRoot "mekhane"))) {
    throw "Could not resolve Mekhane src root from $scriptsDir"
}
$srcRoot
