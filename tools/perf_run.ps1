# Diagnostic FMV perf run (Release exe, hidden window, cwd = build\).
# Usage: perf_run.ps1 -Name A [-Seconds 105] [-ExtraArgs @('--renderer','software')] [-Env @{PSX_VSYNC='0'}]
# NOTE: runs shorter than ~105 s truncate the FMV phase (it starts ~12 s in and lasts ~92 s wall with vsync on).
# Env vars are set per invocation and restored in finally{}; they never leak into the caller session.
# The exact args and env are written to work\perf\run_<Name>.meta.txt (the game log does not echo them).
# Meta also records effective video settings (settings.toml over game.toml), power plan, GPU/driver, window mode, exe SHA, framework pins (T3.6).
# Only the PID started here is killed.
param([string]$Name, [int]$Seconds = 105, [string[]]$ExtraArgs = @(), [hashtable]$Env = @{})
$root = Split-Path -Parent $PSScriptRoot
$out = Join-Path $root 'work\perf'; New-Item -ItemType Directory -Force $out | Out-Null
$all = [ordered]@{PSX_RUNTIME_PERF_DIAG='1'; PSX_RUNTIME_PERF_DIAG_MS='1000'; PSX_FPS_TELEMETRY='1'}
foreach ($k in $Env.Keys) { $all[$k] = $Env[$k] }
# ---- T3.6 measurement hygiene: record everything that changes the numbers ----
function Get-TomlSection([string]$path, [string]$section) {
  $h = [ordered]@{}
  if (-not (Test-Path $path)) { return $h }
  $in = $false
  foreach ($l in Get-Content $path) {
    $t = $l.Trim()
    if ($t -match '^\[(.+)\]\s*(#.*)?$') { $in = ($Matches[1] -eq $section); continue }
    if ($in -and $t -match '^([A-Za-z0-9_]+)\s*=\s*(.*?)\s*(#.*)?$') { $h[$Matches[1]] = $Matches[2].Trim('"') }
  }
  $h
}
function Get-PerfMeta([string]$root) {
  $gameV = Get-TomlSection (Join-Path $root 'build\game.toml') 'video'
  $setV  = Get-TomlSection (Join-Path $root 'build\settings.toml') 'video'
  $lines = New-Object System.Collections.Generic.List[string]
  foreach ($k in 'internal_resolution','supersampling','antialiasing','dynamic_resolution','vsync','fullscreen','window_width','renderer') {
    if ($setV.Contains($k)) { $v = $setV[$k]; $src = 'build\settings.toml' }
    elseif ($gameV.Contains($k)) { $v = $gameV[$k]; $src = 'build\game.toml' }
    else { $v = '(unset)'; $src = 'engine default' }
    $lines.Add("video.$k=$v (source: $src)")
  }
  if (-not (Test-Path (Join-Path $root 'build\settings.toml'))) { $lines.Add('video.note=build\settings.toml missing; build\game.toml only') }
  $lines.Add('window_mode=hidden window (--hidden-window); no visible swap chain, GPU present cost not measured')
  $plan = (& powercfg /getactivescheme | Out-String).Trim()
  $lines.Add("power_plan=$plan")
  foreach ($g in (Get-CimInstance Win32_VideoController | Sort-Object Name)) {
    $lines.Add("gpu=$($g.Name) driver=$($g.DriverVersion) driver_date=$($g.DriverDate.ToString('yyyy-MM-dd'))")
  }
  $exe = Join-Path $root 'build\MythologyKombat.exe'
  $lines.Add("exe_sha256=$((Get-FileHash $exe -Algorithm SHA256).Hash.ToLower())")
  foreach ($sub in 'psxrecomp','recomp-ui') {
    $d = Join-Path $root $sub
    $head = (& git -C $d rev-parse HEAD 2>$null | Out-String).Trim()
    # Dirty = tracked changes outside generated\ (the recompiler regenerates files there) ; the generated-only count is shown separately.
    $st = @(& git -C $d status --porcelain --untracked-files=no 2>$null)
    $gen = @($st | Where-Object { $_ -match '^\s*\S+\s+"?generated/' }).Count
    $other = $st.Count - $gen
    $lines.Add("pin.$sub=$head dirty_files=$other (plus $gen under generated/)")
  }
  $lines
}
$saved = @{}
foreach ($k in $all.Keys) { $saved[$k] = [Environment]::GetEnvironmentVariable($k, 'Process') }
$disc = Join-Path $root 'ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue'
$argv = @('--hidden-window','--no-launcher','--disc',"`"$disc`"",'--game','game.toml','--memcard-dir',(Join-Path $root 'work\perf_saves')) + $ExtraArgs
try {
  foreach ($k in $all.Keys) { [Environment]::SetEnvironmentVariable($k, $all[$k], 'Process') }
  $p = Start-Process -FilePath (Join-Path $root 'build\MythologyKombat.exe') -ArgumentList $argv -WorkingDirectory (Join-Path $root 'build') `
    -PassThru -RedirectStandardOutput (Join-Path $out "run_$Name.log") -RedirectStandardError (Join-Path $out "run_$Name.err.log")
  @("run=$Name start=$(Get-Date -Format o) pid=$($p.Id) seconds=$Seconds", "args=$($argv -join ' ')",
    ("env=" + (($all.Keys | ForEach-Object { "$_=$($all[$_])" }) -join ' '))) + @(Get-PerfMeta $root) | Set-Content (Join-Path $out "run_$Name.meta.txt")
  "started PID $($p.Id)"
  Start-Sleep -Seconds $Seconds
  if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force; "killed PID $($p.Id)" } else { "exited early code $($p.ExitCode)" }
  Start-Sleep 2
  if (Get-Process -Id $p.Id -ErrorAction SilentlyContinue) { "ORPHAN" } else { "no orphan" }
} finally {
  foreach ($k in $saved.Keys) { [Environment]::SetEnvironmentVariable($k, $saved[$k], 'Process') }
}
