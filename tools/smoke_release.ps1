<#
.SYNOPSIS
  Smoke test of a release zip (T3.19): unzip, windowed boot with your disc, screenshots, kill. Windows PowerShell 5.1.

.DESCRIPTION
  Extracts -Zip into an empty folder under work\, starts MythologyKombat.exe there with
  `--disc <cue> --no-launcher`, takes window screenshots at -At seconds, then kills the process and lists
  every file the game created next to the exe (so you can see what a first run writes). The disc is read
  only (passed as an argument; the folder is snapshotted before and after).
  Exit code 0 when the process stayed alive until the last sample, no psx_crash.txt appeared and the runtime's
  frame counter (psx_freeze_heartbeat.json beside the exe) strictly increases between samples. Screenshots are
  evidence for a human; they are black when the desktop is locked or asleep, so they do not decide the result.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\smoke_release.ps1 -Zip work\release\test\MythologyKombat-test-Windows-x64.zip -Disc "...\game.cue"
#>
param(
    [Parameter(Mandatory = $true)][string]$Zip,
    [Parameter(Mandatory = $true)][string]$Disc,
    [string]$At = '15,30,45,60',   # seconds after start at which to sample (comma separated)
    [string]$OutDir
)
$ErrorActionPreference = 'Stop'
$AtList = @($At -split '[,; ]+' | Where-Object { $_ } | ForEach-Object { [int]$_ })
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Zip = (Resolve-Path -LiteralPath $Zip).Path
$Disc = (Resolve-Path -LiteralPath $Disc).Path
if (-not $OutDir) { $OutDir = Join-Path (Split-Path $Zip -Parent) 'smoke' }
$OutDir = [IO.Path]::GetFullPath($OutDir)
$work = [IO.Path]::GetFullPath((Join-Path $RepoRoot 'work')) + '\'
if (-not ($OutDir + '\').StartsWith($work, [StringComparison]::OrdinalIgnoreCase)) { throw "OutDir must be under $work" }
if (Test-Path -LiteralPath $OutDir) { & cmd.exe /c "rd /s /q `"$OutDir`"" | Out-Null }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$discDir = Split-Path $Disc -Parent
function Snap { Get-ChildItem -LiteralPath $discDir -File | Sort-Object Name | ForEach-Object { "{0}|{1}|{2}" -f $_.Name, $_.Length, $_.LastWriteTimeUtc.Ticks } }
$discBefore = (@(Snap)) -join "`n"

Add-Type -AssemblyName System.IO.Compression.FileSystem
$sw = [Diagnostics.Stopwatch]::StartNew()
[IO.Compression.ZipFile]::ExtractToDirectory($Zip, $OutDir)
Write-Host ("unzip: {0:N1} s" -f $sw.Elapsed.TotalSeconds)
$top = @(Get-ChildItem -LiteralPath $OutDir -Directory)
$root = $OutDir
if ($top.Count -eq 1 -and -not (Test-Path -LiteralPath (Join-Path $OutDir 'MythologyKombat.exe'))) { $root = $top[0].FullName }
$exe = Join-Path $root 'MythologyKombat.exe'
if (-not (Test-Path -LiteralPath $exe)) { throw "no MythologyKombat.exe in the zip" }
$before = @{}
Get-ChildItem -LiteralPath $root -Recurse -File | ForEach-Object { $before[$_.FullName] = $true }
Write-Host ("exe: {0}" -f $exe)

Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class SmokeWin {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  [DllImport("user32.dll")] public static extern bool SetProcessDpiAwarenessContext(IntPtr v);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
}
'@
[void][SmokeWin]::SetProcessDpiAwarenessContext([IntPtr](-4))
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms

$p = Start-Process -FilePath $exe -ArgumentList @('--disc', ('"' + $Disc + '"'), '--no-launcher') -WorkingDirectory $root -PassThru
$t0 = Get-Date
$alive = $true; $shots = @(); $titles = @(); $fracs = @(); $frames = @()
try {
    foreach ($s in $AtList) {
        $wait = $s - ((Get-Date) - $t0).TotalSeconds
        if ($wait -gt 0) { Start-Sleep -Milliseconds ([int]($wait * 1000)) }
        if ($p.HasExited) { $alive = $false; Write-Host "process exited early, code $($p.ExitCode)"; break }
        $p.Refresh()
        [void][SmokeWin]::SetForegroundWindow($p.MainWindowHandle)
        Start-Sleep -Milliseconds 500
        $r = New-Object SmokeWin+RECT
        if ([SmokeWin]::GetWindowRect($p.MainWindowHandle, [ref]$r)) {
            $w = $r.R - $r.L; $h = $r.B - $r.T
            if ($w -gt 0 -and $h -gt 0) {
                $bmp = New-Object System.Drawing.Bitmap $w, $h
                $g = [System.Drawing.Graphics]::FromImage($bmp)
                $g.CopyFromScreen($r.L, $r.T, 0, 0, $bmp.Size)
                $f = Join-Path $OutDir ("shot_{0}s.png" -f $s)
                # objective "is something drawn" signal: share of non-black pixels in the client area (grid sample)
                $nb = 0; $tot = 0
                for ($yy = 48; $yy -lt ($h - 8); $yy += 12) { for ($xx = 8; $xx -lt ($w - 8); $xx += 12) {
                    $c = $bmp.GetPixel($xx, $yy); $tot++
                    if (($c.R + $c.G + $c.B) -gt 40) { $nb++ } } }
                $frac = if ($tot -gt 0) { $nb / $tot } else { 0 }
                $fracs += $frac
                $bmp.Save($f); $g.Dispose(); $bmp.Dispose()
                $shots += $f
                Write-Host ("  shot {0}s: {1}x{2}, non-black {3:P1}" -f $s, $w, $h, $frac)
            }
        }
        $titles += $p.MainWindowTitle
        $hb = Join-Path $root 'psx_freeze_heartbeat.json'
        $fc = -1
        if (Test-Path -LiteralPath $hb) {
            try { $m = [regex]::Match((Get-Content -LiteralPath $hb -Raw), '"frame_count"\s*:\s*(\d+)'); if ($m.Success) { $fc = [int64]$m.Groups[1].Value } } catch { }
        }
        $frames += $fc
        Write-Host ("  runtime frame counter (psx_freeze_heartbeat.json): {0}" -f $fc)
        Write-Host ("t={0}s alive, window title '{1}'" -f $s, $p.MainWindowTitle)
    }
} finally {
    if (-not $p.HasExited) { & taskkill.exe /F /T /PID $p.Id | Out-Null }
}
Start-Sleep -Milliseconds 800
Write-Host 'files created next to the exe by the first run:'
$new = Get-ChildItem -LiteralPath $root -Recurse -File | Where-Object { -not $before.ContainsKey($_.FullName) }
$new | ForEach-Object { Write-Host ("  {0}  ({1} bytes)" -f $_.FullName.Substring($root.Length + 1), $_.Length) }
$crash = @($new | Where-Object { $_.Name -eq 'psx_crash.txt' })
foreach ($s in $shots) { Write-Host "screenshot: $s" }
$discAfter = (@(Snap)) -join "`n"
Write-Host ("disc folder unchanged: {0}" -f ($discBefore -eq $discAfter))
if ($discBefore -ne $discAfter) { exit 1 }
$drawn = @($fracs | Where-Object { $_ -gt 0.02 }).Count -gt 0
$advancing = $false
$valid = @($frames | Where-Object { $_ -ge 0 })
if ($valid.Count -ge 2) { $advancing = $true; for ($i = 1; $i -lt $valid.Count; $i++) { if ($valid[$i] -le $valid[$i - 1]) { $advancing = $false } } }
Write-Host ('frame counter strictly increasing across samples: {0}' -f $advancing)
Write-Host ('picture drawn in at least one shot (informational; a locked or sleeping desktop captures black): {0}' -f $drawn)
if ($alive -and $crash.Count -eq 0 -and $advancing) { Write-Host 'SMOKE PASS (alive, no crash file, frames advancing)'; exit 0 }
Write-Host 'SMOKE FAIL'; exit 1
