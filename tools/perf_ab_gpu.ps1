# Runs the MX150 phase of the A/B with a per-app Windows GPU preference on the COPY exe only, and ALWAYS restores the registry.
# Original state recorded to work\perf_ab\gpu_pref_original.txt (key absent or prior value). Usage: perf_ab_gpu.ps1 [-Rounds 3]
param([int]$Rounds = 3)
$root = Split-Path -Parent $PSScriptRoot
$exe = (Get-ChildItem (Join-Path $root 'work\perf_ab\rel') -Directory | Select-Object -First 1).FullName + '\MythologyKombat.exe'
$key = 'HKCU:\Software\Microsoft\DirectX\UserGpuPreferences'
$keyExisted = Test-Path $key
$prior = if ($keyExisted) { (Get-ItemProperty $key -ErrorAction SilentlyContinue).$exe } else { $null }
"keyExisted=$keyExisted priorValueForExe=[$prior] exe=$exe" | Set-Content (Join-Path $root 'work\perf_ab\gpu_pref_original.txt')
try {
  if (-not $keyExisted) { New-Item -Path 'HKCU:\Software\Microsoft\DirectX' -Name 'UserGpuPreferences' -Force | Out-Null }
  Set-ItemProperty -Path $key -Name $exe -Value 'GpuPreference=2;'
  & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'perf_ab_matrix.ps1') -Gpu mx150 -Rounds $Rounds
} finally {
  if ($null -eq $prior) { Remove-ItemProperty -Path $key -Name $exe -ErrorAction SilentlyContinue } else { Set-ItemProperty -Path $key -Name $exe -Value $prior }
  if (-not $keyExisted) { $p = Get-Item $key -ErrorAction SilentlyContinue; if ($p -and $p.ValueCount -eq 0) { Remove-Item $key } }
  "RESTORED keyExists=$(Test-Path $key)"
}
