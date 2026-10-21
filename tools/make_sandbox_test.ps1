<#
.SYNOPSIS
  Prepares the Windows Sandbox clean-machine test (T3.22, D30). Does NOT start the sandbox.

.DESCRIPTION
  Windows PowerShell 5.1, ASCII only. Creates, under <repo>\work\sandbox\ (git-ignored):
    in\     a COPY of the release zip, its checksums.txt, and sandbox_steps.ps1 (the welcome text and steps)
    out\    empty folder, the only writable mapping: the user drops screenshots and logs here
    mk-test.wsb   the Windows Sandbox config. Double-click it to start the test.

  The copy of the zip is verified against checksums.txt (SHA-256) before anything else is written.
  If the zip and the checksum line do not match, the script stops with exit code 1 and writes no .wsb.

  Sandbox settings and why:
    Networking Disable          the test is offline (the updater must say it cannot reach the server).
    VGpu Enable                 the game needs an OpenGL 3.3 context. RISK: the Sandbox vGPU is a
                                virtualised DirectX-based adapter. It may expose no usable OpenGL driver
                                (question 310). If the window does not open, retry with
                                --renderer software (steps are printed in the sandbox window).
                                With VGpu Disable the Sandbox uses a software WARP display and OpenGL 3.3
                                is even less likely, so Enable is the better first try.
    ClipboardRedirection Disable  nothing moves through the clipboard between host and sandbox.
    MemoryInMB 4096.
    AudioInput Disable          this is the microphone only. Audio OUTPUT has no setting in the schema:
                                it is redirected to the host by default. It may still be missing or
                                crackly in the sandbox. Say so in the report.
    All host folders are mapped ReadOnly=true except out\.
    The disc folder (<repo>\ps1_game) is mapped read-only and is never copied or modified.

.PARAMETER Zip  Release zip to test. Default: newest MythologyKombat-*-Windows-x64.zip under work\release\rc1-a.
#>
[CmdletBinding()]
param(
    [string]$Zip
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

function Fail([string]$m) { Write-Host ('ERROR: ' + $m) -ForegroundColor Red; exit 1 }

$Repo = Split-Path -Parent $PSScriptRoot
$Disc = Join-Path $Repo 'ps1_game'
$Sbx  = Join-Path $Repo 'work\sandbox'
$In   = Join-Path $Sbx 'in'
$Out  = Join-Path $Sbx 'out'
$Wsb  = Join-Path $Sbx 'mk-test.wsb'

if (-not $Zip) {
    $dir = Join-Path $Repo 'work\release\rc1-a'
    $cand = @()
    if (Test-Path -LiteralPath $dir) {
        $cand = @(Get-ChildItem -LiteralPath $dir -Filter 'MythologyKombat-*-Windows-x64.zip' -File | Sort-Object LastWriteTime -Descending)
    }
    if ($cand.Count -eq 0) { Fail ('no release zip found in ' + $dir + '. Pass -Zip <path>.') }
    $Zip = $cand[0].FullName
}
if (-not (Test-Path -LiteralPath $Zip -PathType Leaf)) { Fail ('zip not found: ' + $Zip) }
$Zip = (Resolve-Path -LiteralPath $Zip).Path
$ZipName = Split-Path -Leaf $Zip
$SrcSums = Join-Path (Split-Path -Parent $Zip) 'checksums.txt'
if (-not (Test-Path -LiteralPath $SrcSums -PathType Leaf)) { Fail ('checksums.txt not found next to the zip: ' + $SrcSums) }
if (-not (Test-Path -LiteralPath $Disc -PathType Container)) { Fail ('disc folder not found: ' + $Disc) }
if ($ZipName -ne 'MythologyKombat-0.1.0-Windows-x64.zip') {
    Write-Host ('NOTE: zip name is ' + $ZipName + '; the printed steps use this name.')
}

# expected hash from checksums.txt: line "<sha256>  <name>"
$expected = $null
foreach ($line in (Get-Content -LiteralPath $SrcSums)) {
    if ($line -match '^\s*([0-9A-Fa-f]{64})\s+\*?(.+?)\s*$' -and $Matches[2] -eq $ZipName) { $expected = $Matches[1].ToLower() }
}
if (-not $expected) { Fail ('checksums.txt has no line for ' + $ZipName) }

New-Item -ItemType Directory -Force -Path $In  | Out-Null
New-Item -ItemType Directory -Force -Path $Out | Out-Null
# remove stale zips/wsb from an earlier run so the old config cannot pair with a new zip
Get-ChildItem -LiteralPath $In -Filter '*.zip' -File -ErrorAction SilentlyContinue | Remove-Item -Force
if (Test-Path -LiteralPath $Wsb) { Remove-Item -LiteralPath $Wsb -Force }

$ZipCopy = Join-Path $In $ZipName
Copy-Item -LiteralPath $Zip -Destination $ZipCopy -Force
Copy-Item -LiteralPath $SrcSums -Destination (Join-Path $In 'checksums.txt') -Force

# verify the COPY against the COPIED checksums.txt
$actual = (Get-FileHash -LiteralPath $ZipCopy -Algorithm SHA256).Hash.ToLower()
if ($actual -ne $expected) {
    Remove-Item -LiteralPath $ZipCopy -Force
    Fail ('SHA-256 mismatch. checksums.txt: ' + $expected + ' copy: ' + $actual + '. Copy removed, no .wsb written.')
}
Write-Host ('SHA-256 ok: ' + $actual)

# ---- steps script that runs inside the sandbox (shown in a PowerShell window) ----
$steps = @'
# Mythology Kombat clean-machine test (Windows Sandbox). Read-only helper: it only prints text.
$ErrorActionPreference = 'Continue'
Set-Location "$env:USERPROFILE\Desktop"
Write-Host ''
Write-Host '=== MythologyKombat clean-machine test (Windows Sandbox, offline) ===' -ForegroundColor Cyan
Write-Host 'Folders on this Desktop:'
Write-Host '  in    (read-only) release zip + checksums.txt'
Write-Host '  disc  (read-only) your disc image (.cue/.bin)'
Write-Host '  out   (writable) drop screenshots and logs here; the host sees them in work\sandbox\out'
Write-Host 'Network is off and the clipboard is off. Audio output may be missing: report it.'
Write-Host 'Copy a command from below into this window one at a time. Note every message.' -ForegroundColor Yellow
Write-Host ''
Write-Host 'OPTIONAL FIRST (Mark of the Web). Real downloads carry it, a mapped folder does not:' -ForegroundColor Yellow
Write-Host '  New-Item -ItemType Directory -Force Desktop\zipcopy | Out-Null'
Write-Host '  Copy-Item Desktop\in\MythologyKombat-0.1.0-Windows-x64.zip Desktop\zipcopy\'
Write-Host '  Set-Content -Path Desktop\zipcopy\MythologyKombat-0.1.0-Windows-x64.zip -Stream Zone.Identifier -Value "[ZoneTransfer]","ZoneId=3"'
Write-Host '  Get-Content Desktop\zipcopy\MythologyKombat-0.1.0-Windows-x64.zip -Stream Zone.Identifier'
Write-Host '  (then use Desktop\zipcopy\... instead of Desktop\in\... in step a. NOTE: PowerShell Expand-Archive does'
Write-Host '   NOT copy the mark onto the extracted files. To get it on them, right-click the zip in File Explorer,'
Write-Host '   Extract All to Desktop\test, or after step a run:'
Write-Host '   Get-ChildItem Desktop\test -Recurse -File | ForEach-Object { Set-Content -Path $_.FullName -Stream Zone.Identifier -Value "[ZoneTransfer]","ZoneId=3" } )'
Write-Host ''
Write-Host 'a) Expand the zip:' -ForegroundColor Green
Write-Host '   Expand-Archive Desktop\in\MythologyKombat-0.1.0-Windows-x64.zip -DestinationPath Desktop\test'
Write-Host '   Get-ChildItem Desktop\test\MythologyKombat-0.1.0 | Select-Object Name, Length'
Write-Host 'b) Verify the checksum (compare with Desktop\in\checksums.txt):' -ForegroundColor Green
Write-Host '   Get-FileHash Desktop\in\MythologyKombat-0.1.0-Windows-x64.zip -Algorithm SHA256'
Write-Host '   Get-Content Desktop\in\checksums.txt'
Write-Host 'c) Start the game:' -ForegroundColor Green
Write-Host '   c1, straight to the game, no launcher:'
Write-Host '   & "Desktop\test\MythologyKombat-0.1.0\MythologyKombat.exe" --disc "Desktop\disc\Mortal Kombat Mythologies - Sub-Zero.cue" --no-launcher'
Write-Host '   If no window opens or it fails on OpenGL, try the software renderer and report both results:'
Write-Host '   & "Desktop\test\MythologyKombat-0.1.0\MythologyKombat.exe" --disc "Desktop\disc\Mortal Kombat Mythologies - Sub-Zero.cue" --no-launcher --renderer software'
Write-Host '   c2, the plain launcher (pick the .cue in Desktop\disc, check the verdict, press PLAY):'
Write-Host '   Start-Process "Desktop\test\MythologyKombat-0.1.0\MythologyKombat.exe"'
Write-Host '   Note: SmartScreen / Smart App Control text (verbatim), time from PLAY to title screen,'
Write-Host '   whether the title picture is right, and the Midway logo audio (broken or fine).'
Write-Host 'd) Updater, offline (expected: a message that the server cannot be reached; nothing is changed):' -ForegroundColor Green
Write-Host '   & "Desktop\test\MythologyKombat-0.1.0\update.cmd" -CheckOnly'
Write-Host 'e) Screenshots: Win+Shift+S has no clipboard here. Open the Snipping Tool, take the shot,'
Write-Host '   then File > Save as... and save into Desktop\out. Copy any log text into a file in Desktop\out too.'
Write-Host ''
Write-Host 'f) Check that no disc file ended up in the game folder (expected: no output):' -ForegroundColor Green
Write-Host '   Get-ChildItem Desktop\test -Recurse -Include *.bin,*.cue,*.iso,*.chd,*.mcd,*.ovr,*.str | Select-Object FullName'
Write-Host 'g) Windows version for the report:' -ForegroundColor Green
Write-Host '   (Get-CimInstance Win32_OperatingSystem).Caption'
Write-Host ''
'@
$StepsPath = Join-Path $In 'sandbox_steps.ps1'
[System.IO.File]::WriteAllText($StepsPath, ($steps -replace "`r?`n", "`r`n"), (New-Object System.Text.ASCIIEncoding))

# ---- the .wsb ----
function XmlEsc([string]$s) { return [System.Security.SecurityElement]::Escape($s) }
$d = 'C:\Users\WDAGUtilityAccount\Desktop'
$logon = 'powershell.exe -NoExit -NoProfile -ExecutionPolicy Bypass -File ' + $d + '\in\sandbox_steps.ps1'
$wsbText = @"
<Configuration>
  <VGpu>Enable</VGpu>
  <Networking>Disable</Networking>
  <ClipboardRedirection>Disable</ClipboardRedirection>
  <AudioInput>Disable</AudioInput>
  <VideoInput>Disable</VideoInput>
  <PrinterRedirection>Disable</PrinterRedirection>
  <ProtectedClient>Disable</ProtectedClient>
  <MemoryInMB>4096</MemoryInMB>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>$(XmlEsc $In)</HostFolder>
      <SandboxFolder>$d\in</SandboxFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
    <MappedFolder>
      <HostFolder>$(XmlEsc $Disc)</HostFolder>
      <SandboxFolder>$d\disc</SandboxFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
    <MappedFolder>
      <HostFolder>$(XmlEsc $Out)</HostFolder>
      <SandboxFolder>$d\out</SandboxFolder>
      <ReadOnly>false</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>$(XmlEsc $logon)</Command>
  </LogonCommand>
</Configuration>
"@
[System.IO.File]::WriteAllText($Wsb, $wsbText, (New-Object System.Text.ASCIIEncoding))

# ---- self-validation ----
$x = New-Object System.Xml.XmlDocument
$x.Load($Wsb)
foreach ($mf in $x.Configuration.MappedFolders.MappedFolder) {
    if (-not (Test-Path -LiteralPath $mf.HostFolder -PathType Container)) { Fail ('mapped host folder missing: ' + $mf.HostFolder) }
}
$ro = @($x.Configuration.MappedFolders.MappedFolder | Where-Object { $_.ReadOnly -eq 'true' }).Count
Write-Host ('wsb ok: ' + $Wsb + ' (' + $ro + ' read-only mappings, 1 writable: out)')
Write-Host ('Input: ' + $ZipCopy)
Write-Host 'Not started. Double-click mk-test.wsb to launch Windows Sandbox.'
exit 0
