# run_overlay_coverage.ps1 - T2.17 launcher for tools\overlay_coverage.py (Windows PowerShell 5.1).
# Usage (from anywhere):  powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_overlay_coverage.ps1 [-- script options]
# Examples:  ...run_overlay_coverage.ps1 -BootRoute      (auto-skips the intro and starts New Game)
#            ...run_overlay_coverage.ps1 --help
# Env: RETRO_TOOLS_DIR (default %USERPROFILE%\retro-tools). Python is run with -I.
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$retro = "$env:USERPROFILE\retro-tools"
if ($env:RETRO_TOOLS_DIR) { $retro = $env:RETRO_TOOLS_DIR }
$py = Join-Path $retro 'python\python.exe'
if (-not (Test-Path -LiteralPath $py)) { Write-Error "python not found: $py"; exit 2 }
$extra = @()
foreach ($x in $args) { if ($x -eq '-BootRoute') { $extra += '--boot-route' } else { $extra += [string]$x } }
Set-Location $repo
& $py -I (Join-Path $repo 'tools\overlay_coverage.py') @extra
exit $LASTEXITCODE
