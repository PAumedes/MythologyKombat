# run_psxrecomp.ps1 - run the upstream psxrecomp_cli.py with the project toolchain environment.
# Windows PowerShell 5.1 compatible. Forwards all arguments, exits with the CLI's exit code.
# Usage (from repo root):
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_psxrecomp.ps1 verify-disc --config game.toml --disc "ps1_game\<name>.cue"
#
# Env overrides: RETRO_TOOLS_DIR (default %USERPROFILE%\retro-tools),
#                PSXRECOMP_FORCE_PRIVATE_PY=1 (skip option (a), use the private Python copy; for testing).
#
# Python choice (decision D5): the upstream CLI must NOT run with -I.
#   (a) the embeddable <retro-tools>\python\python.exe as is (the CLI adds psxrecomp\tools to sys.path itself);
#   (b) a private copy at work\py-psxrecomp whose python312._pth lists the psxrecomp dirs.
# The retro-tools install is never modified.
$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$retro = "$env:USERPROFILE\retro-tools"
if ($env:RETRO_TOOLS_DIR) { $retro = $env:RETRO_TOOLS_DIR }
$cli = Join-Path $repo 'psxrecomp\psxrecomp_cli.py'
if (-not (Test-Path -LiteralPath $cli)) { Write-Error "missing $cli (psxrecomp submodule not initialised)"; exit 2 }

# --- toolchain environment ---
$tc = Join-Path $retro 'cmake-clang'
$env:PSXRECOMP_TOOLCHAIN_DIR = $tc
$prefix = @()
# Git's bin first so `bash` is Git's bash (not WSL/MSYS).
$gitBin = $null
$gitCmd = Get-Command git -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
$cands = @()
if ($gitCmd) { $cands += (Split-Path (Split-Path $gitCmd.Source -Parent) -Parent) }
foreach ($pf in @($env:ProgramFiles, ${env:ProgramFiles(x86)}, "$env:LOCALAPPDATA\Programs")) { if ($pf) { $cands += (Join-Path $pf 'Git') } }
foreach ($c in $cands) { if (Test-Path -LiteralPath (Join-Path $c 'bin\bash.exe')) { $gitBin = Join-Path $c 'bin'; break } }
if ($gitBin) { $prefix += $gitBin } else { Write-Host '[run_psxrecomp] note: Git bash.exe not found; PATH bash left as is' }
$prefix += (Join-Path $tc 'bin')
$env:PATH = ($prefix -join ';') + ';' + $env:PATH

# --- python selection ---
function Test-Cli([string]$py) {
    # Returns $true if `py psxrecomp_cli.py --help` exits 0 (no -I).
    try {
        $o = & $py $cli --help 2>&1
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

$chosen = $null
$why = ''
$embed = Join-Path $retro 'python\python.exe'
if ((-not $env:PSXRECOMP_FORCE_PRIVATE_PY) -and (Test-Path -LiteralPath $embed)) {
    if (Test-Cli $embed) { $chosen = $embed; $why = 'option (a): embeddable Python as is' }
}
if (-not $chosen) {
    $src = Join-Path $retro 'python'
    $priv = Join-Path $repo 'work\py-psxrecomp'
    $privPy = Join-Path $priv 'python.exe'
    if (-not (Test-Path -LiteralPath $privPy)) {
        if (-not (Test-Path -LiteralPath (Join-Path $src 'python.exe'))) { Write-Error "no embeddable Python at $src"; exit 3 }
        Write-Host "[run_psxrecomp] creating private Python copy at $priv"
        New-Item -ItemType Directory -Force -Path $priv | Out-Null
        Copy-Item -Path (Join-Path $src '*') -Destination $priv -Recurse -Force
        $pth = Get-ChildItem -LiteralPath $priv -Filter 'python*._pth' | Select-Object -First 1
        if (-not $pth) { Write-Error 'no ._pth in private copy'; exit 3 }
        $lines = @(Get-Content -LiteralPath $pth.FullName | Where-Object { $_ -notmatch '^\s*#\s*import site' -and $_ -ne 'import site' })
        $lines += (Join-Path $repo 'psxrecomp\tools')
        $lines += (Join-Path $repo 'psxrecomp\tools\new_project_layout')
        $lines += (Join-Path $repo 'psxrecomp')
        $lines += 'import site'
        Set-Content -LiteralPath $pth.FullName -Value $lines -Encoding ASCII
    }
    if (Test-Cli $privPy) { $chosen = $privPy; $why = 'option (b): private copy work\py-psxrecomp with extended ._pth' }
}
if (-not $chosen) {
    Write-Host '[run_psxrecomp] STOP: neither embeddable Python (a) nor private copy (b) can run psxrecomp_cli.py. A full Python install needs user approval.'
    exit 4
}
Write-Host "[run_psxrecomp] python: $chosen ($why)"
Write-Host "[run_psxrecomp] toolchain: $tc"

& $chosen $cli @args
exit $LASTEXITCODE
