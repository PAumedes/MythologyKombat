# Visible-window perf A/B run on a COPY of the release exe (T3.7/T3.8). Never touches build\settings.toml.
# Usage: perf_ab.ps1 -Name I4_v0_r1 -Resolution 4k [-Ss 4] [-Aa $true] [-Vsync 0] [-Fullscreen 0] [-Seconds 80] [-ExeDir <dir>]
# ExeDir default: work\perf_ab\rel\ (an extracted copy of the release zip). The per-app GPU preference
# (HKCU DirectX UserGpuPreferences, keyed by the exe path) is NOT touched here; tools\perf_ab_gpu.ps1 does that.
# Writes work\perf_ab\results\<Name>\ : settings.toml used, meta.txt, stdout/stderr logs, session telemetry.csv + session.json.
param([Parameter(Mandatory)][string]$Name, [string]$Resolution = '4k', [int]$Ss = 4, [int]$Aa = 1, [int]$Vsync = 0,
      [int]$Fullscreen = 0, [int]$Seconds = 80, [string]$ExeDir = '')
$root = Split-Path -Parent $PSScriptRoot
if (-not $ExeDir) { $ExeDir = (Get-ChildItem (Join-Path $root 'work\perf_ab\rel') -Directory | Select-Object -First 1).FullName
  if (-not $ExeDir) { $ExeDir = Join-Path $root 'work\perf_ab\rel' } }
$exe = Join-Path $ExeDir 'MythologyKombat.exe'
if (-not (Test-Path $exe)) { throw "exe not found: $exe" }
$rd = Join-Path $root "work\perf_ab\results\$Name"; New-Item -ItemType Directory -Force $rd | Out-Null
# settings.toml: copy of the user's file with video keys replaced, [disc] and [memcard] removed (never point at the user's saves).
$lines = Get-Content (Join-Path $root 'build\settings.toml'); $out = New-Object System.Collections.Generic.List[string]; $skip = $false
foreach ($l in $lines) {
  if ($l -match '^\[(.+)\]') { $skip = ($Matches[1] -in 'disc','memcard') }
  if ($skip) { continue }
  if     ($l -match '^internal_resolution\s*=') { if ($Resolution -eq 'none') { continue }; $l = "internal_resolution = `"$Resolution`"" }
  elseif ($l -match '^supersampling\s*=')       { $l = "supersampling     = $Ss" }
  elseif ($l -match '^antialiasing\s*=')        { $l = "antialiasing      = $(if ($Aa) {'true'} else {'false'})" }
  elseif ($l -match '^fullscreen\s*=')          { $l = "fullscreen        = $Fullscreen" }
  $out.Add($l)
}
$out | Set-Content (Join-Path $ExeDir 'settings.toml') -Encoding utf8
Copy-Item (Join-Path $ExeDir 'settings.toml') (Join-Path $rd 'settings.toml')
$saves = Join-Path $root 'work\perf_ab\saves'; New-Item -ItemType Directory -Force $saves | Out-Null
$disc = Join-Path $root 'ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue'
$envs = [ordered]@{PSX_FPS_TELEMETRY='1'; PSX_RUNTIME_PERF_DIAG='1'; PSX_RUNTIME_PERF_DIAG_MS='1000'; PSX_VSYNC="$Vsync"}
$p = $null; $saved = @{}; foreach ($k in $envs.Keys) { $saved[$k] = [Environment]::GetEnvironmentVariable($k,'Process') }
$diagRoot = Join-Path $ExeDir 'saves\diagnostics'
$before = @(); if (Test-Path $diagRoot) { $before = @(Get-ChildItem $diagRoot -Directory | ForEach-Object Name) }
try {
  foreach ($k in $envs.Keys) { [Environment]::SetEnvironmentVariable($k, $envs[$k], 'Process') }
  $argv = @('--no-launcher','--disc',"`"$disc`"",'--game','game.toml','--memcard-dir',"`"$saves`"")
  $p = Start-Process -FilePath $exe -ArgumentList $argv -WorkingDirectory $ExeDir -PassThru `
        -RedirectStandardOutput (Join-Path $rd 'stdout.log') -RedirectStandardError (Join-Path $rd 'stderr.log')
  $meta = @("run=$Name start=$(Get-Date -Format o) pid=$($p.Id) seconds=$Seconds", "exe=$exe", "args=$($argv -join ' ')",
            "env=" + (($envs.Keys | ForEach-Object { "$_=$($envs[$_])" }) -join ' '),
            "res=$Resolution ss=$Ss aa=$Aa vsync_env=$Vsync fullscreen=$Fullscreen",
            "power_plan=$((& powercfg /getactivescheme | Out-String).Trim())",
            "gpu_pref_entry=" + ((Get-ItemProperty 'HKCU:\Software\Microsoft\DirectX\UserGpuPreferences' -ErrorAction SilentlyContinue).$exe))
  $meta | Set-Content (Join-Path $rd 'meta.txt')
  Start-Sleep -Seconds $Seconds
  if ($p.HasExited) { "EXITED EARLY code $($p.ExitCode)" } else { "will kill $($p.Id) in finally" }
  Start-Sleep 2
} finally { if ($p -and -not $p.HasExited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; "killed $($p.Id)"; Start-Sleep 2 }; foreach ($k in $saved.Keys) { [Environment]::SetEnvironmentVariable($k, $saved[$k], 'Process') } }
$new = @(Get-ChildItem $diagRoot -ErrorAction SilentlyContinue -Directory | Where-Object { $before -notcontains $_.Name } | Sort-Object LastWriteTime)
if ($new.Count -ne 1) { "WARNING: $($new.Count) new session dirs" }
if ($new.Count -ge 1) { $s = $new[-1]; Copy-Item (Join-Path $s.FullName '*') $rd -Exclude '*.mcd' -Force -ErrorAction SilentlyContinue; Add-Content (Join-Path $rd 'meta.txt') "session=$($s.FullName)" }
Get-Content (Join-Path $rd 'stdout.log') | Select-String -Pattern 'OpenGL context created|internal resolution|supersampl|vsync|sync-to-host|window' | Select-Object -First 8 | ForEach-Object { $_.Line }
Add-Content (Join-Path $rd "meta.txt") ((Select-String -Path (Join-Path $rd "stdout.log") -Pattern "OpenGL context created" | Select-Object -First 1).Line)
