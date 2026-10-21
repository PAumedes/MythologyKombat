<#
.SYNOPSIS
  D24 assertions for the CI setup-host build (T3.17). No disc, no secrets.

.DESCRIPTION
  Fails (exit 1) unless the setup-host build came from a clean checkout:
    1. <Root>\generated does not exist and nothing under generated/ is tracked
    2. <Root>\ps1_game does not exist
    3. the configure log does not say "linking generated game C"
    4. neither build.ninja nor .ninja_log mentions generated/overlays_static
       or the retail generated game C (SLUS_004.76_full / _dispatch)
    5. the exe exists (when -Exe is given)
  Logs may be UTF-8 or UTF-16 (Get-Content detects the BOM).
  Output is one PASS/FAIL line per check.

  Also usable locally as a negative control: pointing -Root at a dev tree that
  has generated\ must fail checks 1 and 4.
#>
param(
    [string]$Root = (Join-Path $PSScriptRoot '..'),
    [Parameter(Mandatory)][string]$BuildDir,
    [Parameter(Mandatory)][string]$ConfigureLog,
    [string]$Exe = ''
)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path $Root).Path
$fail = 0
function Check([string]$name, [bool]$ok, [string]$detail = '') {
    if ($ok) { Write-Host "PASS $name" }
    else { Write-Host "FAIL $name $detail"; $script:fail++ }
}

Check 'no generated\ directory in checkout' (-not (Test-Path (Join-Path $Root 'generated'))) "($Root\generated exists)"
Check 'no ps1_game\ directory in checkout' (-not (Test-Path (Join-Path $Root 'ps1_game'))) "($Root\ps1_game exists)"
if (Test-Path (Join-Path $Root '.git')) {
    $tracked = @(git -C $Root ls-files -- generated)
    Check 'no tracked files under generated/' ($tracked.Count -eq 0) "($($tracked.Count) tracked)"
}

$log = Get-Content -Raw $ConfigureLog
Check 'configure log is non-empty' ($log.Length -gt 0)
Check 'configure log lacks "linking generated game C"' ($log -notmatch 'linking generated game C')

$pat = 'generated[\\/]+overlays_static|SLUS_004\.76_(full|dispatch)'
foreach ($f in 'build.ninja', '.ninja_log') {
    $p = Join-Path $BuildDir $f
    if (Test-Path $p) {
        $hits = @(Select-String -Path $p -Pattern $pat -AllMatches | Select-Object -First 3)
        $detail = ''
        if ($hits.Count -gt 0) {
            $l = $hits[0].Line
            $detail = "($($hits.Count)+ hit(s), first: $($l.Substring(0, [Math]::Min(120, $l.Length))))"
        }
        Check "$f has no generated game C or overlays_static" ($hits.Count -eq 0) $detail
    } elseif ($f -eq 'build.ninja') {
        Check 'build.ninja exists' $false "($p)"
    }
}
if ($Exe) { Check 'exe exists' (Test-Path $Exe) "($Exe)" }

if ($fail) { Write-Host "$fail check(s) failed"; exit 1 }
Write-Host 'all checks passed'
exit 0
