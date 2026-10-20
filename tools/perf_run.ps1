# Diagnostic FMV perf run (Release exe, hidden window, cwd = build\).
# Usage: perf_run.ps1 -Name A [-Seconds 105] [-ExtraArgs @('--renderer','software')] [-Env @{PSX_VSYNC='0'}]
# NOTE: runs shorter than ~105 s truncate the FMV phase (it starts ~12 s in and lasts ~92 s wall with vsync on).
# Env vars are set per invocation and restored in finally{}; they never leak into the caller session.
# The exact args and env are written to work\perf\run_<Name>.meta.txt (the game log does not echo them).
# Only the PID started here is killed.
param([string]$Name, [int]$Seconds = 105, [string[]]$ExtraArgs = @(), [hashtable]$Env = @{})
$root = Split-Path -Parent $PSScriptRoot
$out = Join-Path $root 'work\perf'; New-Item -ItemType Directory -Force $out | Out-Null
$all = [ordered]@{PSX_RUNTIME_PERF_DIAG='1'; PSX_RUNTIME_PERF_DIAG_MS='1000'; PSX_FPS_TELEMETRY='1'}
foreach ($k in $Env.Keys) { $all[$k] = $Env[$k] }
$saved = @{}
foreach ($k in $all.Keys) { $saved[$k] = [Environment]::GetEnvironmentVariable($k, 'Process') }
$disc = Join-Path $root 'ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue'
$argv = @('--hidden-window','--no-launcher','--disc',"`"$disc`"",'--game','game.toml','--memcard-dir',(Join-Path $root 'work\perf_saves')) + $ExtraArgs
try {
  foreach ($k in $all.Keys) { [Environment]::SetEnvironmentVariable($k, $all[$k], 'Process') }
  $p = Start-Process -FilePath (Join-Path $root 'build\MythologyKombat.exe') -ArgumentList $argv -WorkingDirectory (Join-Path $root 'build') `
    -PassThru -RedirectStandardOutput (Join-Path $out "run_$Name.log") -RedirectStandardError (Join-Path $out "run_$Name.err.log")
  @("run=$Name start=$(Get-Date -Format o) pid=$($p.Id) seconds=$Seconds", "args=$($argv -join ' ')",
    ("env=" + (($all.Keys | ForEach-Object { "$_=$($all[$_])" }) -join ' '))) | Set-Content (Join-Path $out "run_$Name.meta.txt")
  "started PID $($p.Id)"
  Start-Sleep -Seconds $Seconds
  if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force; "killed PID $($p.Id)" } else { "exited early code $($p.ExitCode)" }
  Start-Sleep 2
  if (Get-Process -Id $p.Id -ErrorAction SilentlyContinue) { "ORPHAN" } else { "no orphan" }
} finally {
  foreach ($k in $saved.Keys) { [Environment]::SetEnvironmentVariable($k, $saved[$k], 'Process') }
}
