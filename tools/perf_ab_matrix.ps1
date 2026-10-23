# Runs the T3.7/T3.8 A/B matrix by calling perf_ab.ps1 (visible window, copy of the release exe). Rounds are interleaved
# (round 1 of every config, then round 2, ...) to spread thermal drift. Run names: <GPU>_<config>_r<round>.
# Usage: perf_ab_matrix.ps1 -Gpu intel|mx150 [-Rounds 3] [-Seconds 75] [-Only cfg1,cfg2]
param([Parameter(Mandatory)][string]$Gpu, [int]$Rounds = 3, [int]$Seconds = 75, [string[]]$Only = @())
$ab = Join-Path $PSScriptRoot 'perf_ab.ps1'
# name = @(Resolution, Ss, Aa, Vsync, Fullscreen)   Vsync env: 0 immediate, 1 vsync, -1 adaptive
$cfg = [ordered]@{
  'n1x_v0'   = @('native', 1, 0, 0, 0)
  'ss2_v0'   = @('none',   2, 0, 0, 0)
  '720p_v0'  = @('720p',   3, 1,  0, 0)
  '4k_v0'    = @('4k',     4, 1,  0, 0)
  'n1x_von'  = @('native', 1, 0, 1, 0)
  '4k_von'   = @('4k',     4, 1,  1, 0)
  '4k_vad'   = @('4k',     4, 1, -1, 0)
  '4k_v0_fs' = @('4k',     4, 1,  0, 1)
}
if ($Gpu -eq 'mx150') { $Only = @('n1x_v0','ss2_v0','4k_v0','4k_von') }
for ($r = 1; $r -le $Rounds; $r++) {
  foreach ($k in $cfg.Keys) {
    if ($Only.Count -and ($Only -notcontains $k)) { continue }
    $v = $cfg[$k]
    "== $Gpu $k round $r  $(Get-Date -Format T)"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $ab -Name "${Gpu}_${k}_r$r" -Resolution $v[0] -Ss $v[1] -Aa $v[2] -Vsync $v[3] -Fullscreen $v[4] -Seconds $Seconds | Select-Object -Last 3
  }
}
"MATRIX DONE $Gpu $(Get-Date -Format T)"
