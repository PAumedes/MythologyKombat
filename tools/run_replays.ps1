# Strict replay of every recording under tests\replays\local\ (T2.20).
# Usage: tools\run_replays.ps1 [-Exe build\MythologyKombat.exe] [-Session <dir>] [-Python <python.exe>]
# For each session dir (contains inputs.csv) it runs build\replay-diagnostics.py against a fresh private output dir
# under work\replay_out\<name>-<timestamp> (git-ignored) and prints PASS or FAIL per recording.
# PASS = the replay tool exited 0 AND printed "Replay verified". Anything else is FAIL (exit code and last log lines shown).
# The exe must be the same build that made the recording; the tool verifies build identity itself.
# Recordings, memory cards and replay output are git-ignored and must never be committed.
param(
  [string]$Exe = 'build\MythologyKombat.exe',
  [string]$Session = '',
  [string]$Python = ''
)
$root = Split-Path -Parent $PSScriptRoot
if (-not $Python) {
  $retro = "$env:USERPROFILE\retro-tools"
  if ($env:RETRO_TOOLS_DIR) { $retro = $env:RETRO_TOOLS_DIR }
  $Python = Join-Path $retro 'python\python.exe'
}
Set-Location $root
$disc = 'ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue'
if ($Session) { $dirs = @(Get-Item -LiteralPath $Session) }
else { $dirs = @(Get-ChildItem 'tests\replays\local' -Directory -ErrorAction SilentlyContinue | Where-Object { Test-Path (Join-Path $_.FullName 'inputs.csv') }) }
if ($dirs.Count -eq 0) { Write-Host 'no recordings found under tests\replays\local\'; exit 2 }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$fail = 0
foreach ($d in $dirs) {
  $out = Join-Path $root "work\replay_out\$($d.Name)-$stamp"
  New-Item -ItemType Directory -Force (Split-Path $out) | Out-Null
  $log = "$out.log"
  $sw = [Diagnostics.Stopwatch]::StartNew()
  & $Python build\replay-diagnostics.py $d.FullName --exe $Exe --disc $disc --game game.toml --output $out *> $log
  $code = $LASTEXITCODE
  $sw.Stop()
  $text = Get-Content $log -Raw
  if ($code -eq 0 -and $text -match 'Replay verified') { '{0}  PASS  ({1:n0} s)' -f $d.Name, $sw.Elapsed.TotalSeconds }
  else { $fail++; '{0}  FAIL  exit={1}' -f $d.Name, $code; (Get-Content $log -Tail 6) | ForEach-Object { "    $_" } }
}
exit ([int]($fail -gt 0))
