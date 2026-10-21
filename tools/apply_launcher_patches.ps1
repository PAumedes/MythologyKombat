<#
.SYNOPSIS
  Build a patched, throwaway copy of the recomp-ui launcher (D19, T3.12).

.DESCRIPTION
  The recomp-ui submodule is never edited. This script:
    1. reads the commit the superproject pins for recomp-ui (git ls-tree HEAD),
    2. exports exactly that commit (git archive, no autocrlf) into -Dest,
    3. applies every patches\launcher\*.patch in name order with git apply.
  The result is a normal recomp-ui tree. Point the build at it:

      cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release `
            -DRECOMP_UI_ROOT=<Dest> ...

  PSXRecomp's runtime.cmake honours -DRECOMP_UI_ROOT (it only falls back to
  <repo>\recomp-ui when the variable is empty), so no CMake change is needed.
  `git -C recomp-ui status --short` stays empty.

  Use -Only to apply a subset (e.g. for before/after screenshots):
      -Only 0001,0003

  Prints the Dest path on the last line (so a caller can capture it).
#>
param(
    [string]$Dest = (Join-Path $PSScriptRoot '..\work\recomp-ui-patched'),
    [string[]]$Only = @(),
    [string]$PatchDir = (Join-Path $PSScriptRoot '..\patches\launcher')
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Dest = [System.IO.Path]::GetFullPath($Dest)
$PatchDir = [System.IO.Path]::GetFullPath($PatchDir)

# Only ever write below work\ : refuse anything else so a typo cannot clobber the repo.
$workDir = [System.IO.Path]::GetFullPath((Join-Path $root 'work')) + '\'
if (-not ($Dest + '\').StartsWith($workDir, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Dest must be under $workDir (got $Dest)"
}

$line = git -C $root ls-tree HEAD recomp-ui
if (-not $line) { throw 'recomp-ui is not in the superproject HEAD' }
$pin = ($line -split '\s+')[2]
Write-Host "recomp-ui pin: $pin"

if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
New-Item -ItemType Directory -Force $Dest | Out-Null

# Pipe archive -> tar. -c core.autocrlf=false keeps the stored LF bytes, which
# is what the patches are written against.
$tar = Join-Path $env:TEMP ("recomp-ui-{0}.tar" -f $pin.Substring(0, 8))
git -C (Join-Path $root 'recomp-ui') -c core.autocrlf=false archive --format=tar -o $tar $pin
if ($LASTEXITCODE -ne 0) { throw 'git archive failed' }
& (Join-Path $env:SystemRoot 'System32\tar.exe') -xf $tar -C $Dest
if ($LASTEXITCODE -ne 0) { throw 'tar extract failed' }
Remove-Item $tar

$patches = Get-ChildItem $PatchDir -Filter '*.patch' | Sort-Object Name
if ($Only.Count -gt 0) {
    $patches = $patches | Where-Object { $n = $_.Name; ($Only | Where-Object { $n -like "$_*" }).Count -gt 0 }
}
# Dest lives under work\ inside the superproject checkout. Without a ceiling,
# git finds that repo, treats Dest as a subdirectory of it, and silently skips
# every patch path ("src/...") that is not relative to the repo root.
$env:GIT_CEILING_DIRECTORIES = (Split-Path $Dest -Parent)
foreach ($p in $patches) {
    git -C $Dest -c core.autocrlf=false apply --whitespace=nowarn --check $p.FullName
    if ($LASTEXITCODE -ne 0) { throw "patch does not apply: $($p.Name)" }
    git -C $Dest -c core.autocrlf=false apply --whitespace=nowarn $p.FullName
    if ($LASTEXITCODE -ne 0) { throw "git apply failed: $($p.Name)" }
    # Prove it took: the reverse patch must now apply cleanly.
    git -C $Dest -c core.autocrlf=false apply --whitespace=nowarn --check --reverse $p.FullName
    if ($LASTEXITCODE -ne 0) { throw "patch reported success but changed nothing: $($p.Name)" }
    Write-Host "applied $($p.Name)"
}
Write-Host "patched copy: $Dest"
Write-Output $Dest
