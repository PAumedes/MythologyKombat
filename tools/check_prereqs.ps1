# check_prereqs.ps1 - report which build/RE prerequisites are present. Installs nothing, needs no admin.
# Windows PowerShell 5.1 compatible. Always exits 0.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File tools\check_prereqs.ps1
$ErrorActionPreference = 'Continue'
$script:missing = 0

function Get-VersionFromText([string]$text) {
    if ($text -match '(\d+)\.(\d+)(?:\.(\d+))?') {
        $p = if ($matches[3]) { [int]$matches[3] } else { 0 }
        return New-Object System.Version ([int]$matches[1]), ([int]$matches[2]), $p
    }
    return $null
}

# Run an exe with args, merging stderr, returning text. Never throws.
function Invoke-Capture([string]$exe, [string]$argLine) {
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $exe
        $psi.Arguments = $argLine
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $p = [System.Diagnostics.Process]::Start($psi)
        $out = $p.StandardOutput.ReadToEnd() + "`n" + $p.StandardError.ReadToEnd()
        if (-not $p.WaitForExit(15000)) { try { $p.Kill() } catch {} }
        return $out
    } catch { return '' }
}

function Find-Exe([string]$name) {
    $c = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($c) { return $c.Source }
    return $null
}

function Write-Result([string]$tool, [string]$status, [string]$detail) {
    if ($status -ne 'present') { $script:missing++ }
    $line = '{0,-15} {1,-9} {2}' -f $tool, $status.ToUpper(), $detail
    $color = 'Green'
    if ($status -eq 'missing') { $color = 'Red' } elseif ($status -eq 'too old') { $color = 'Yellow' }
    Write-Host $line -ForegroundColor $color
}

# Generic check: find exe, run version args, compare to minimum.
function Test-Tool([string]$label, [string[]]$names, [string]$verArgs, [string]$minText, [string[]]$extraPaths) {
    $exe = $null
    foreach ($n in $names) { $exe = Find-Exe $n; if ($exe) { break } }
    if (-not $exe -and $extraPaths) {
        foreach ($pat in $extraPaths) {
            $hit = Get-ChildItem -Path $pat -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($hit) { $exe = $hit.FullName; break }
        }
    }
    if (-not $exe) { Write-Result $label 'missing' ('not found' + $(if ($minText) { " (need $minText)" } else { '' })); return }
    $text = Invoke-Capture $exe $verArgs
    $ver = Get-VersionFromText $text
    if (-not $ver) { Write-Result $label 'missing' "found at $exe but no usable version output (Store alias stub?)"; return }
    if ($minText) {
        $min = Get-VersionFromText $minText
        if ($ver -lt $min) { Write-Result $label 'too old' "$ver at $exe (need $minText)"; return }
    }
    Write-Result $label 'present' "$ver at $exe"
}

$pf   = $env:ProgramFiles
$pf86 = ${env:ProgramFiles(x86)}
$home_ = $env:USERPROFILE
$lad  = $env:LOCALAPPDATA

Write-Host 'MythologyKombat prerequisite check (read-only, installs nothing)'
Write-Host '----------------------------------------------------------------'

# Git
Test-Tool 'Git' @('git') '--version' '' @("$pf\Git\cmd\git.exe")

# Python 3.10+ (skip WindowsApps Store stubs; fall back to py launcher)
$pyExe = $null
foreach ($c in @(Get-Command python -CommandType Application -ErrorAction SilentlyContinue)) {
    if ($c.Source -notlike '*\WindowsApps\*') { $pyExe = $c.Source; break }
}
if ($pyExe) {
    $t = Invoke-Capture $pyExe '--version'; $v = Get-VersionFromText $t
    if ($t -match 'Python\s+3' -and $v) {
        if ($v -lt (New-Object System.Version 3,10,0)) { Write-Result 'Python' 'too old' "$v at $pyExe (need 3.10+)" }
        else { Write-Result 'Python' 'present' "$v at $pyExe" }
    } else { Write-Result 'Python' 'missing' "$pyExe did not report Python 3 (need 3.10+)" }
} else {
    $pyl = Find-Exe 'py'
    $done = $false
    if ($pyl) {
        $t = Invoke-Capture $pyl '-3 --version'; $v = Get-VersionFromText $t
        if ($t -match 'Python\s+3' -and $v) {
            $done = $true
            if ($v -lt (New-Object System.Version 3,10,0)) { Write-Result 'Python' 'too old' "$v via py launcher (need 3.10+)" }
            else { Write-Result 'Python' 'present' "$v via py launcher ($pyl)" }
        }
    }
    if (-not $done) { Write-Result 'Python' 'missing' 'not found (need 3.10+)' }
}

# CMake 3.20+
$vsCmake = @("$pf\CMake\bin\cmake.exe")
foreach ($r in @($pf, $pf86)) { if ($r) { $vsCmake += "$r\Microsoft Visual Studio\*\*\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" } }
Test-Tool 'CMake' @('cmake') '--version' '3.20' $vsCmake

# Ninja (also look inside Visual Studio's bundled CMake)
$vsNinja = @()
foreach ($r in @($pf, $pf86)) { if ($r) { $vsNinja += "$r\Microsoft Visual Studio\*\*\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe" } }
Test-Tool 'Ninja' @('ninja') '--version' '' $vsNinja

# C/C++ compiler: clang, cl (PATH or via vswhere), gcc
$cc = $null
$ccx = Find-Exe 'clang'
if (-not $ccx) { $ccx = Find-Exe 'clang-cl' }
if (-not $ccx -and (Test-Path "$pf\LLVM\bin\clang.exe")) { $ccx = "$pf\LLVM\bin\clang.exe" }
if ($ccx) {
    $v = Get-VersionFromText (Invoke-Capture $ccx '--version')
    $cc = "clang $v at $ccx"
}
if (-not $cc) {
    $clx = Find-Exe 'cl'
    if (-not $clx) {
        $vsw = $null
        if ($pf86 -and (Test-Path "$pf86\Microsoft Visual Studio\Installer\vswhere.exe")) { $vsw = "$pf86\Microsoft Visual Studio\Installer\vswhere.exe" }
        if ($vsw) {
            $inst = (Invoke-Capture $vsw '-latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath').Trim()
            if ($inst -and (Test-Path $inst)) {
                $hit = Get-ChildItem -Path "$inst\VC\Tools\MSVC\*\bin\Hostx64\x64\cl.exe" -ErrorAction SilentlyContinue | Sort-Object FullName | Select-Object -Last 1
                if ($hit) { $clx = $hit.FullName }
            }
        }
        if (-not $clx) {
            foreach ($r in @($pf, $pf86)) {
                if (-not $r) { continue }
                $hit = Get-ChildItem -Path "$r\Microsoft Visual Studio\*\*\VC\Tools\MSVC\*\bin\Hostx64\x64\cl.exe" -ErrorAction SilentlyContinue | Sort-Object FullName | Select-Object -Last 1
                if ($hit) { $clx = $hit.FullName; break }
            }
        }
    }
    if ($clx) {
        $v = Get-VersionFromText (Invoke-Capture $clx '')
        $note = ''
        if (-not (Find-Exe 'cl')) { $note = ' (not on PATH; use a Developer prompt)' }
        $cc = "MSVC cl $v at $clx$note"
    }
}
if (-not $cc) {
    $gx = Find-Exe 'gcc'
    if ($gx) { $v = Get-VersionFromText (Invoke-Capture $gx '--version'); $cc = "gcc $v at $gx" }
}
if ($cc) { Write-Result 'C/C++ compiler' 'present' $cc } else { Write-Result 'C/C++ compiler' 'missing' 'no clang, MSVC cl or gcc found' }

# Java 21+ (java -version prints to stderr, handled by Invoke-Capture)
$jexe = Find-Exe 'java'
if (-not $jexe -and $env:JAVA_HOME -and (Test-Path "$env:JAVA_HOME\bin\java.exe")) { $jexe = "$env:JAVA_HOME\bin\java.exe" }
if (-not $jexe) {
    foreach ($pat in @("$pf\Java\*\bin\java.exe", "$pf\Eclipse Adoptium\*\bin\java.exe", "$pf\Microsoft\jdk-*\bin\java.exe", "$pf\Amazon Corretto\*\bin\java.exe", "$pf\Zulu\*\bin\java.exe")) {
        $hit = Get-ChildItem -Path $pat -ErrorAction SilentlyContinue | Sort-Object FullName | Select-Object -Last 1
        if ($hit) { $jexe = $hit.FullName; break }
    }
}
if (-not $jexe) { Write-Result 'Java' 'missing' 'not found (need 21+ for Ghidra)' }
else {
    $t = Invoke-Capture $jexe '-version'
    $v = $null
    if ($t -match 'version "(\d+)(?:\.(\d+))?(?:\.(\d+))?') {
        $mi = 0; if ($matches[2]) { $mi = [int]$matches[2] }
        $v = New-Object System.Version ([int]$matches[1]), $mi
    }
    if (-not $v) { Write-Result 'Java' 'missing' "$jexe gave no version output" }
    elseif ($v.Major -lt 21) { Write-Result 'Java' 'too old' "$v at $jexe (need 21+)" }
    else { Write-Result 'Java' 'present' "$v at $jexe" }
}

# Ghidra: GHIDRA_INSTALL_DIR then common locations, looking for ghidraRun.bat
$gh = $null
$cands = @()
if ($env:GHIDRA_INSTALL_DIR) { $cands += $env:GHIDRA_INSTALL_DIR }
$cands += @('C:\ghidra*', 'C:\tools\ghidra*', "$home_\ghidra*", "$home_\tools\ghidra*", "$home_\Downloads\ghidra*", "$home_\Downloads\*\ghidra*", "$pf\ghidra*", "$pf86\ghidra*", "$lad\ghidra*", "$lad\Programs\ghidra*", "$home_\scoop\apps\ghidra\current*", 'C:\ProgramData\chocolatey\lib\ghidra\tools\ghidra*')
foreach ($pat in $cands) {
    foreach ($d in @(Get-ChildItem -Path $pat -Directory -ErrorAction SilentlyContinue)) {
        $run = $null
        if (Test-Path "$($d.FullName)\ghidraRun.bat") { $run = $d.FullName }
        else {
            $sub = Get-ChildItem -Path "$($d.FullName)\ghidra_*" -Directory -ErrorAction SilentlyContinue | Where-Object { Test-Path "$($_.FullName)\ghidraRun.bat" } | Select-Object -First 1
            if ($sub) { $run = $sub.FullName }
        }
        if ($run) { $gh = $run; break }
    }
    if ($gh) { break }
    if ((Test-Path $pat -PathType Container) -and (Test-Path "$pat\ghidraRun.bat")) { $gh = $pat; break }
}
if ($gh) {
    $ver = ''
    $props = "$gh\Ghidra\application.properties"
    if (Test-Path $props) {
        $m = Select-String -Path $props -Pattern '^application\.version=(.+)$' -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($m) { $ver = $m.Matches[0].Groups[1].Value.Trim() }
    }
    if (-not $ver) { $ver = '(version unknown)' }
    Write-Result 'Ghidra' 'present' "$ver at $gh"
} else { Write-Result 'Ghidra' 'missing' 'ghidraRun.bat not found (checked GHIDRA_INSTALL_DIR and common dirs)' }

# Node.js 22+
Test-Tool 'Node.js' @('node') '--version' '22.0' @("$pf\nodejs\node.exe")

# Reference emulator: DuckStation or PCSX-Redux
$emu = $null
foreach ($n in @('duckstation-qt-x64-ReleaseLTCG', 'duckstation-nogui-x64-ReleaseLTCG', 'duckstation', 'pcsx-redux')) {
    $e = Find-Exe $n
    if ($e) { $emu = $e; break }
}
if (-not $emu) {
    $dirs = @("$pf", "$pf86", "$lad", "$lad\Programs", "$home_\Downloads", "$home_\Desktop", "$home_\scoop\apps", 'C:\', 'C:\Emulators', 'C:\emu', 'C:\tools', "$home_\Documents", "$home_\source")
    foreach ($d in $dirs) {
        if (-not $d -or -not (Test-Path $d)) { continue }
        foreach ($glob in @('duckstation*', 'pcsx-redux*', 'PCSX-Redux*')) {
            foreach ($sub in @(Get-ChildItem -Path $d -Filter $glob -Directory -ErrorAction SilentlyContinue)) {
                $hit = Get-ChildItem -Path $sub.FullName -Filter '*.exe' -Recurse -Depth 2 -ErrorAction SilentlyContinue |
                    Where-Object { $_.Name -match '^(duckstation.*|pcsx-redux.*)\.exe$' -and $_.Name -notmatch 'unins' } | Select-Object -First 1
                if ($hit) { $emu = $hit.FullName; break }
            }
            if ($emu) { break }
            $hit = Get-ChildItem -Path $d -Filter "$glob.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($hit) { $emu = $hit.FullName; break }
        }
        if ($emu) { break }
    }
}
if ($emu) {
    $kind = 'emulator'
    if ($emu -match 'duckstation') { $kind = 'DuckStation' } elseif ($emu -match 'pcsx') { $kind = 'PCSX-Redux' }
    $fv = (Get-Item $emu -ErrorAction SilentlyContinue).VersionInfo.ProductVersion
    if (-not $fv) { $fv = '(version unknown)' }
    Write-Result 'Emulator' 'present' "$kind $fv at $emu"
} else { Write-Result 'Emulator' 'missing' 'no DuckStation or PCSX-Redux found' }

Write-Host '----------------------------------------------------------------'
if ($script:missing -eq 0) { Write-Host 'All prerequisites satisfied.' }
else { Write-Host "$($script:missing) prerequisite(s) missing or too old. Nothing was installed." }
exit 0
