<#
.SYNOPSIS
  Launch a launcher build, report its real window rectangle versus the primary
  display, and save a DPI-aware screen capture (T3.12, issue 6).

.DESCRIPTION
  The earlier user screenshots were cropped to 1536x864, which is a 1920x1080
  screen seen by a process that is NOT DPI aware at 125%. This probe marks
  itself per-monitor DPI aware first, so the numbers are real pixels.

  Run from any directory:
    powershell -ExecutionPolicy Bypass -File tools\launcher_window_probe.ps1 `
        -Exe work\build-launcher-test\MythologyKombat.exe -Out work\screens\probe.png
#>
param(
    [Parameter(Mandatory)][string]$Exe,
    [Parameter(Mandatory)][string]$Out,
    [int]$DelaySeconds = 10,
    [string]$Disc = ''
)
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Drawing;
public static class W {
  [DllImport("user32.dll")] public static extern bool SetProcessDpiAwarenessContext(IntPtr v);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern int GetSystemMetrics(int i);
  [DllImport("user32.dll")] public static extern uint GetDpiForWindow(IntPtr h);
  [DllImport("dwmapi.dll")] public static extern int DwmGetWindowAttribute(IntPtr h, int a, out RECT r, int s);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
'@ -ReferencedAssemblies System.Drawing
[void][W]::SetProcessDpiAwarenessContext([IntPtr](-4))   # PER_MONITOR_AWARE_V2
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms

$exeFull = (Resolve-Path $Exe).Path
$args = @()
if ($Disc) { $args += @('--disc', $Disc) }
$p = Start-Process -FilePath $exeFull -ArgumentList $args -WorkingDirectory (Split-Path $exeFull) -PassThru
try {
    Start-Sleep -Seconds $DelaySeconds
    $p.Refresh()
    $h = $p.MainWindowHandle
    if ($h -eq [IntPtr]::Zero) { throw 'no main window (launcher not shown?)' }
    [void][W]::SetForegroundWindow($h)
    Start-Sleep -Milliseconds 800
    $r = New-Object W+RECT
    [void][W]::GetWindowRect($h, [ref]$r)
    $ext = New-Object W+RECT
    [void][W]::DwmGetWindowAttribute($h, 9, [ref]$ext, 16)   # DWMWA_EXTENDED_FRAME_BOUNDS
    $screenW = [W]::GetSystemMetrics(0); $screenH = [W]::GetSystemMetrics(1)
    $wa = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
    "window title    : $($p.MainWindowTitle)"
    "window dpi      : $([W]::GetDpiForWindow($h))"
    "screen (px)     : ${screenW}x${screenH}"
    "work area (px)  : $($wa.X),$($wa.Y) $($wa.Width)x$($wa.Height)"
    "GetWindowRect   : $($r.L),$($r.T) -> $($r.R),$($r.B)  ($($r.R-$r.L)x$($r.B-$r.T))"
    "visible frame   : $($ext.L),$($ext.T) -> $($ext.R),$($ext.B)  ($($ext.R-$ext.L)x$($ext.B-$ext.T))"
    $inside = ($ext.L -ge $wa.X - 1) -and ($ext.T -ge $wa.Y - 1) -and ($ext.R -le $wa.X + $wa.Width + 1) -and ($ext.B -le $wa.Y + $wa.Height + 1)
    "inside work area: $inside"
    $bmp = New-Object System.Drawing.Bitmap $screenW, $screenH
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen(0, 0, 0, 0, $bmp.Size)
    $dir = Split-Path ([System.IO.Path]::GetFullPath($Out))
    New-Item -ItemType Directory -Force $dir | Out-Null
    $bmp.Save([System.IO.Path]::GetFullPath($Out), [System.Drawing.Imaging.ImageFormat]::Png)
    "saved           : $Out ($screenW x $screenH real pixels)"
} finally {
    if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }
}
