<#
.SYNOPSIS
  MythologyKombat standalone updater (T3.21, D27). Windows PowerShell 5.1, ASCII only.

.DESCRIPTION
  Run by hand (update.cmd). Checks the newest GitHub release of the constant repo below, and only if it is
  strictly newer: downloads the zip and checksums.txt (https, github hosts only, redirects checked hop by hop),
  verifies SHA-256, validates every zip entry, stages, then swaps files with a journal and a backup.
  It never runs anything from the zip and never starts the game. Saves and settings are never touched.

  -CheckOnly   stop after the version check.
  -DryRun      stop after download, verify and staging. Like -CheckOnly it never moves, deletes or rewrites any
               install file or journal (it only reports an interrupted update or an old backup it would handle);
               its stage folder is removed again and an empty .update folder it created is removed.
  -Rollback    restore the previous version from .update\backup-<old>.
  -InstallDir  the game folder (default: the folder of this script). The script copies itself to
               %LOCALAPPDATA%\MythologyKombat\update\run and runs from there, so it never runs from the folder it swaps.
  Test mode (-TestBaseUrl http://127.0.0.1:PORT, localhost only) is for tools\test_updater.ps1: it replaces the
  GitHub URLs with the local server and enables -Yes, -TestDataDir and the -TestCrash* hooks. Every check still runs.
#>
[CmdletBinding()]
param(
    [string]$InstallDir,
    [switch]$CheckOnly,
    [switch]$DryRun,
    [switch]$Rollback,
    [string]$TestBaseUrl,
    [string]$TestDataDir,
    [switch]$Yes,
    [int]$TestCrashAfter = -1,
    [string]$TestCrashMode = 'throw',
    [long]$TestFreeBytes = -1,
    [int]$TestHoldSeconds = 0
)
$ErrorActionPreference = 'Stop'

# ----------------------------------------------------------------------------- constants (never read from a download)
$ReleaseRepo = 'PAumedes/MythologyKombat'
$UpdaterId = 'MythologyKombat-updater/1'
$ProductName = 'MythologyKombat'
$ExeName = 'MythologyKombat.exe'
$GitHubHost = 'github.com'
$ApiHost = 'api.github.com'
$AssetHosts = @('release-assets.githubusercontent.com', 'objects.githubusercontent.com')
$MaxHops = 5
$MaxZipBytes = 300MB
$MaxEntries = 5000
$MaxTotalBytes = 400MB
$MaxEntryBytes = 200MB
$MaxTextBytes = 4MB
$ConfFiles = @('game.toml', 'game_options.toml')
$PreserveRegex = @(
    '^saves(/|$)', '^settings\.toml$', '^input\.ini$', '^keybinds\.ini$', '^disc\.cfg$', '^bios\.cfg$',
    '^launcher-window\.ini$', '^mods/state\.toml$', '^mods/texture-packs(/|$)', '^cache(/|$)',
    '^overlay_captures\.json', '^psx_execution(/|$)', '^psx_freeze_', '^psx_last_run_report\.json$',
    '^psx_crash\.txt$', '^diagnostics-location\.txt$', '^replay-diagnostics\.py$', '^work(/|$)', '^\.update(/|$)')
$RunMarkers = @('psx_last_run_report.json', 'settings.toml', 'input.ini', 'keybinds.ini', 'overlay_captures.json')

function Stop-Update([string]$msg) { throw ('UPDATER:' + $msg) }
function Say([string]$m) { Write-Host $m }

$TestMode = $false
$GitHubBase = 'https://github.com'
$ApiBase = 'https://api.github.com'
if ($TestBaseUrl) {
    $u = $null
    if (-not [Uri]::TryCreate($TestBaseUrl, [UriKind]::Absolute, [ref]$u) -or $u.Scheme -ne 'http' -or
        @('127.0.0.1', 'localhost', '[::1]') -notcontains $u.Host -or $u.AbsolutePath -ne '/' -or $u.Query -or $u.UserInfo) {
        Write-Host 'ERROR: -TestBaseUrl must be http://127.0.0.1:PORT, http://localhost:PORT or http://[::1]:PORT'
        exit 1
    }
    $TestMode = $true
    $GitHubBase = $u.GetLeftPart([UriPartial]::Authority)
    $ApiBase = $GitHubBase
}
if (-not $TestMode -and ($Yes -or $TestDataDir -or $TestCrashAfter -ge 0 -or $TestFreeBytes -ge 0 -or $TestHoldSeconds -gt 0)) {
    Write-Host 'ERROR: -Yes, -TestDataDir and -TestCrash* exist only in test mode.'
    exit 1
}

# ----------------------------------------------------------------------------- self copy (never run from the swapped folder)
if (-not $InstallDir) { $InstallDir = $PSScriptRoot }
try { $InstallDir = [IO.Path]::GetFullPath($InstallDir).TrimEnd('\') } catch { Write-Host 'ERROR: bad -InstallDir'; exit 1 }

if ($TestDataDir) { $DataDir = [IO.Path]::GetFullPath($TestDataDir) }
else { $DataDir = Join-Path $env:LOCALAPPDATA 'MythologyKombat\update' }

if ($PSScriptRoot -and ($PSScriptRoot.TrimEnd('\') -ieq $InstallDir)) {
    try {
        $runDir = Join-Path $DataDir 'run'
        [void][IO.Directory]::CreateDirectory($runDir)
        $copy = Join-Path $runDir 'update.ps1'
        [IO.File]::Copy((Join-Path $PSScriptRoot 'update.ps1'), $copy, $true)
    } catch {
        Write-Host ('ERROR: cannot copy the updater to ' + $DataDir + ': ' + $_.Exception.Message)
        exit 1
    }
    $argList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $copy, '-InstallDir', $InstallDir)
    if ([Environment]::GetCommandLineArgs() -contains '-NonInteractive') { $argList = @('-NonInteractive') + $argList }
    foreach ($k in $PSBoundParameters.Keys) {
        if ($k -eq 'InstallDir') { continue }
        $v = $PSBoundParameters[$k]
        if ($v -is [System.Management.Automation.SwitchParameter]) { if ($v.IsPresent) { $argList += ('-' + $k) } }
        else { $argList += ('-' + $k); $argList += [string]$v }
    }
    & powershell.exe @argList
    exit $LASTEXITCODE
}

# ----------------------------------------------------------------------------- helpers
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
try { [Net.ServicePointManager]::SecurityProtocol = (3072 -bor 12288) } catch { [Net.ServicePointManager]::SecurityProtocol = 3072 }

function Get-FileSha256([string]$path) {
    $sha = [Security.Cryptography.SHA256]::Create()
    $fs = [IO.File]::Open($path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    try { $h = $sha.ComputeHash($fs) } finally { $fs.Dispose(); $sha.Dispose() }
    return (($h | ForEach-Object { $_.ToString('x2') }) -join '')
}

function Write-TextFile([string]$path, [string]$text) {
    $d = [IO.Path]::GetDirectoryName($path)
    if (-not [IO.Directory]::Exists($d)) { [void][IO.Directory]::CreateDirectory($d) }
    [IO.File]::WriteAllText($path, $text, (New-Object Text.UTF8Encoding($false)))
}

function Remove-Tree([string]$path) {
    if ([IO.Directory]::Exists($path)) {
        try { [IO.Directory]::Delete($path, $true) } catch { & cmd.exe /c ('rd /s /q "' + $path + '"') | Out-Null }
    }
}

function Move-FileRetry([string]$from, [string]$to) {
    $d = [IO.Path]::GetDirectoryName($to)
    if (-not [IO.Directory]::Exists($d)) { [void][IO.Directory]::CreateDirectory($d) }
    for ($i = 1; $i -le 3; $i++) {
        try { [IO.File]::Move($from, $to); return } catch { if ($i -eq 3) { throw }; Start-Sleep -Seconds 1 }
    }
}

function Get-SafeText([string]$s, [int]$max) {
    if (-not $s) { return '' }
    $s = $s -replace '[^\x20-\x7e\r\n]', '?'
    if ($s.Length -gt $max) { $s = $s.Substring(0, $max) + ' [...]' }
    return $s
}

function Test-Preserved([string]$rel) {
    # normalise: lower case, no trailing dots/spaces per segment (Windows ignores them)
    $l = (($rel.ToLowerInvariant().Split('/') | ForEach-Object { $_.TrimEnd('. ') }) -join '/')
    foreach ($re in $PreserveRegex) { if ($l -match $re) { return $true } }
    return $false
}

function Get-RelPathError([string]$rel) {
    if ([string]::IsNullOrEmpty($rel)) { return 'empty path' }
    if ($rel.Length -gt 200) { return 'path too long' }
    if ($rel.IndexOf('\') -ge 0) { return 'backslash in path' }
    if ($rel.StartsWith('/')) { return 'absolute path' }
    if ($rel -match '[^\x20-\x7e]') { return 'control or non-ASCII character' }
    if ($rel.IndexOfAny([char[]]':*?"<>|') -ge 0) { return 'forbidden character (: * ? " < > |)' }
    # '~' blocks 8.3 short-name aliases (SETTIN~1.TOM would resolve to the player's settings.toml); '$' blocks CONIN$ and friends
    if ($rel.IndexOfAny([char[]]'~$') -ge 0) { return 'forbidden character (~ or $)' }
    foreach ($seg in $rel.Split('/')) {
        if ($seg.Length -eq 0) { return 'empty path segment' }
        if ($seg -eq '.' -or $seg -eq '..') { return 'dot segment' }
        if ($seg.EndsWith('.') -or $seg.EndsWith(' ')) { return 'segment ends with dot or space' }
        $b = $seg.Split('.')[0].Trim().ToUpperInvariant()
        if ($b -match '^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$') { return 'reserved device name' }
    }
    return $null
}

# ---- URL policy and manual redirects
function Get-UrlForLog([string]$s) {
    # never print a query string or fragment: signed CDN URLs carry credentials there
    if (-not $s) { return '' }
    $i = $s.IndexOfAny([char[]]'?#')
    if ($i -ge 0) { return $s.Substring(0, $i) + '?[query hidden]' }
    return $s
}

function Assert-NoPercent([string]$s) {
    # Percent escapes in the PATH (%2e%2e, %2f, %5c) are not normalised by every layer, and none of our paths needs one.
    # The query string (signed CDN URLs: %3A %3B %3D %2F %20) is not inspected here and is never printed.
    if (-not $s) { return }
    $i = $s.IndexOfAny([char[]]'?#')
    $pathPart = $s; if ($i -ge 0) { $pathPart = $s.Substring(0, $i) }
    if ($pathPart.IndexOf('%') -ge 0) { Stop-Update ('refused URL with a percent escape in its path: ' + (Get-SafeText $pathPart 120)) }
}

function Assert-UrlAllowed([string]$url, [string]$kind, [string]$prefix) {
    Assert-NoPercent $url
    # kind 'api': only api.github.com under /repos/<repo>/ (or /repositories/).
    # kind 'download': github.com under $prefix (/<repo>/releases/download/<tag>/), then the two GitHub asset hosts.
    $u = $null
    if (-not [Uri]::TryCreate($url, [UriKind]::Absolute, [ref]$u)) { Stop-Update ('bad URL refused: ' + (Get-SafeText (Get-UrlForLog $url) 120)) }
    if ($u.UserInfo) { Stop-Update 'URL with credentials refused' }
    $path = $u.AbsolutePath
    if ($TestMode) {
        $b = [Uri]$GitHubBase
        if ($u.Scheme -eq 'http' -and $u.Host -eq $b.Host -and $u.Port -eq $b.Port) {
            if ($path.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { return $u }
            if ($kind -eq 'download' -and $path.StartsWith('/cdn/', [StringComparison]::Ordinal)) { return $u }   # stands in for the asset CDN
            Stop-Update ('refused path outside ' + $prefix + ': ' + (Get-SafeText $path 100))
        }
    }
    if ($u.Scheme -ne 'https') { Stop-Update ('refused non-https URL: ' + (Get-SafeText (Get-UrlForLog $url) 120)) }
    if ($u.Port -ne 443) { Stop-Update 'refused URL with a non-default port' }
    $h = $u.Host.ToLowerInvariant()
    if ($kind -eq 'api' -and $h -eq $ApiHost) {
        if ($path.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase) -or $path.StartsWith('/repositories/', [StringComparison]::Ordinal)) { return $u }
        Stop-Update ('refused API path outside ' + $prefix + ': ' + (Get-SafeText $path 100))
    }
    if ($kind -eq 'download' -and $h -eq $GitHubHost) {
        if ($path.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { return $u }
        Stop-Update ('refused path outside ' + $prefix + ': ' + (Get-SafeText $path 100))
    }
    if ($kind -eq 'download' -and ($AssetHosts -contains $h)) { return $u }
    Stop-Update ('refused host not on the allow-list: ' + (Get-SafeText $h 80))
}

function Send-Request([string]$url, [string]$method, [string]$outFile, [long]$maxBytes) {
    $req = [Net.HttpWebRequest]::Create($url)
    $req.Method = $method
    $req.AllowAutoRedirect = $false
    $req.UserAgent = $UpdaterId
    $req.Accept = 'application/vnd.github+json, application/octet-stream, */*'
    $req.Timeout = 30000
    $req.ReadWriteTimeout = 30000
    $resp = $null
    try { $resp = $req.GetResponse() }
    catch [Net.WebException] {
        $resp = $_.Exception.Response
        if (-not $resp) { Stop-Update ('network error: ' + $_.Exception.Message) }
    }
    try {
        $r = @{ Status = [int]$resp.StatusCode; Location = $resp.Headers['Location']; RateRemaining = $resp.Headers['X-RateLimit-Remaining']; Text = $null; Bytes = 0L }
        $isRedirect = @(301, 302, 303, 307, 308) -contains $r.Status
        if ($method -eq 'GET' -and -not $isRedirect -and $r.Status -eq 200) {
            $cl = $resp.ContentLength
            if ($cl -gt $maxBytes) { Stop-Update ('response larger than the allowed ' + $maxBytes + ' bytes') }
            $in = $resp.GetResponseStream()
            try {
                if ($outFile) { $out = [IO.File]::Open($outFile, [IO.FileMode]::Create, [IO.FileAccess]::Write) } else { $out = New-Object IO.MemoryStream }
                try {
                    $buf = New-Object byte[] 65536
                    while (($n = $in.Read($buf, 0, $buf.Length)) -gt 0) {
                        $r.Bytes += $n
                        if ($r.Bytes -gt $maxBytes) { Stop-Update ('download exceeded the allowed ' + $maxBytes + ' bytes') }
                        $out.Write($buf, 0, $n)
                    }
                    if (-not $outFile) { $r.Text = [Text.Encoding]::UTF8.GetString($out.ToArray()) }
                } finally { $out.Dispose() }
            } finally { $in.Dispose() }
        }
        return $r
    } finally { $resp.Close() }
}

function Get-Following([string]$url, [string]$outFile, [long]$maxBytes, [string]$kind, [string]$prefix) {
    $cur = $url
    for ($hop = 0; $hop -le $MaxHops; $hop++) {
        [void](Assert-UrlAllowed $cur $kind $prefix)
        $r = Send-Request $cur 'GET' $outFile $maxBytes
        if (@(301, 302, 303, 307, 308) -contains $r.Status) {
            if (-not $r.Location) { Stop-Update 'redirect without Location' }
            Assert-NoPercent $r.Location
            if ($hop -ge $MaxHops) { Stop-Update ('more than ' + $MaxHops + ' redirects') }
            if ($r.Location -match '^https?://') { $cur = [string]$r.Location }   # keep a signed query byte for byte
            else { $cur = (New-Object Uri((New-Object Uri($cur)), $r.Location)).OriginalString }
            continue
        }
        $r.FinalUrl = $cur
        return $r
    }
    Stop-Update 'redirect limit'
}

# ---- manifest
function Read-Manifest([string]$json, [string]$what) {
    try { $m = $json | ConvertFrom-Json } catch { Stop-Update ($what + ' is not valid JSON') }
    if ($m.manifest_version -ne 1) { Stop-Update ($what + ': unsupported manifest_version') }
    $map = New-Object 'System.Collections.Generic.Dictionary[string,object]'
    $lower = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($f in @($m.files)) {
        $p = [string]$f.path
        $e = Get-RelPathError $p
        if ($e) { Stop-Update ($what + ': bad path "' + (Get-SafeText $p 80) + '": ' + $e) }
        if ($p -ieq 'manifest.json') { Stop-Update ($what + ': manifest lists itself') }
        if (-not $lower.Add($p.ToLowerInvariant())) { Stop-Update ($what + ': duplicate path ' + (Get-SafeText $p 80)) }
        if (-not ($f.size -is [int] -or $f.size -is [long]) -or $f.size -lt 0) { Stop-Update ($what + ': bad size for ' + (Get-SafeText $p 80)) }
        if (([string]$f.sha256) -notmatch '^[0-9a-f]{64}\z') { Stop-Update ($what + ': bad sha256 for ' + (Get-SafeText $p 80)) }
        $map[$p] = [pscustomobject]@{ Path = $p; Size = [long]$f.size; Sha = [string]$f.sha256 }
    }
    return @{ Version = [string]$m.version; Map = $map }
}

# ---- journal / swap / rollback
$UpdDir = Join-Path $InstallDir '.update'
$JournalPath = Join-Path $UpdDir 'journal.json'

function Read-Journal([bool]$tolerant = $false) {
    if (-not [IO.File]::Exists($JournalPath)) { return $null }
    $why = $null; $j = $null
    try {
        $txt = [IO.File]::ReadAllText($JournalPath)
        if ([string]::IsNullOrWhiteSpace($txt)) { $why = 'it is empty' }
        else {
            $j = $txt | ConvertFrom-Json
            if (-not $j -or -not $j.state -or -not $j.backup -or -not $j.stage -or $null -eq $j.plan) { $why = 'it is incomplete' }
            elseif (([string]$j.backup) -notmatch '^backup-[A-Za-z0-9._-]{1,60}\z' -or ([string]$j.stage) -notmatch '^stage-[0-9.]{1,40}\z') { $why = 'its folder names are not valid' }
            elseif (-not (($j.swapped_ticks -is [int] -or $j.swapped_ticks -is [long]) -and $j.swapped_ticks -ge 0 -and $j.swapped_ticks -le [DateTime]::MaxValue.Ticks)) { $why = 'its timestamp is invalid' }
            else {
                foreach ($it in @($j.plan)) {
                    if ((Get-RelPathError ([string]$it.rel)) -or @('replace', 'add', 'delete') -notcontains [string]$it.op -or (Test-Preserved ([string]$it.rel))) { $why = 'its plan contains an invalid entry'; break }
                    if ($it.op -ne 'delete' -and (Get-RelPathError ([string]$it.src))) { $why = 'its plan contains an invalid entry'; break }
                }
            }
        }
    } catch { $why = 'it is not valid JSON (' + ($_.Exception.Message -replace '^UPDATER:', '') + ')' }
    if ($why) {
        $msg = 'journal.json is corrupt: ' + $why + '. The updater will not touch the install until this is resolved. The folder ' + $UpdDir + ' may hold a backup-* folder with your previous files. If the game starts and works, delete the .update folder and run the updater again; if not, copy the files from .update\backup-* over the install folder by hand (keep the folder structure; or re-extract the release zip of your version over it), then delete the .update folder.'
        if ($tolerant) { Say ('WARNING: ' + $msg + ' (continuing because this run changes nothing)'); return $null }
        Stop-Update $msg
    }
    return $j
}
function Write-Journal($j) {
    $tmp = $JournalPath + '.tmp'
    Write-TextFile $tmp ($j | ConvertTo-Json -Depth 6)
    if ([IO.File]::Exists($JournalPath)) { [IO.File]::Replace($tmp, $JournalPath, $JournalPath + '.bak'); [IO.File]::Delete($JournalPath + '.bak') } else { [IO.File]::Move($tmp, $JournalPath) }
}

function Invoke-Rollback($j, [string]$finalState) {
    $backup = Join-Path $UpdDir $j.backup
    $stage = Join-Path $UpdDir $j.stage
    $j.state = 'rolling-back'; Write-Journal $j
    $errors = @()
    $plan = @($j.plan)
    for ($i = $plan.Count - 1; $i -ge 0; $i--) {
        $it = $plan[$i]
        $dest = Join-Path $InstallDir ($it.rel -replace '/', '\')
        $bk = Join-Path $backup ($it.rel -replace '/', '\')
        try {
            if ($it.op -eq 'replace') {
                if ([IO.File]::Exists($bk)) {
                    if ([IO.File]::Exists($dest)) { [IO.File]::Delete($dest) }
                    Move-FileRetry $bk $dest
                } elseif (-not [IO.File]::Exists($dest)) {
                    $errors += ($it.rel + ': the file is missing and its backup is missing')
                } else {
                    # no backup: fine only if the file is still the old one (the swap never reached it)
                    $cur = Get-FileSha256 $dest
                    if ($it.old_sha -and $cur -ne [string]$it.old_sha) { $errors += ($it.rel + ': the backup is missing and the installed file is not the old version') }
                }
            } elseif ($it.op -eq 'add') {
                $src = Join-Path $stage ($it.src -replace '/', '\')
                if ([IO.File]::Exists($dest) -and -not [IO.File]::Exists($src)) {
                    if ($it.new_sha -and (Get-FileSha256 $dest) -ne [string]$it.new_sha) { Say ('Note: ' + $it.rel + ' was changed after the update; left in place.') }
                    else { [IO.File]::Delete($dest) }
                }
            } elseif ($it.op -eq 'delete') {
                if ([IO.File]::Exists($bk) -and -not [IO.File]::Exists($dest)) { Move-FileRetry $bk $dest }
                elseif (-not [IO.File]::Exists($bk) -and -not [IO.File]::Exists($dest)) { $errors += ($it.rel + ': the file is missing and its backup is missing') }
            }
        } catch { $errors += ($it.rel + ': ' + ($_.Exception.Message -replace '^UPDATER:', '')) }
    }
    if ($errors.Count -gt 0) {
        $j.state = 'rollback-failed'; Write-Journal $j
        Say 'ROLLBACK INCOMPLETE. These files could not be restored:'
        $errors | ForEach-Object { Say ('  ' + $_) }
        Say ''
        Say 'Fix the cause (close the game; put a missing file back into the backup folder) and run the updater again: it retries the rollback.'
        Say ('If it keeps failing, finish by hand: close the game, copy everything from ' + $backup + ' over the install folder (' + $InstallDir + ') keeping the folder structure and answering yes to overwrite, then delete the folder ' + $UpdDir + '. For a file whose backup is missing, re-extract that file from the release zip of version ' + (Get-SafeText ([string]$j.from) 40) + '. Saves and settings are never touched by the updater.')
        Stop-Update 'rollback incomplete (see the steps above)'
    }
    Remove-Tree $stage
    Remove-Tree $backup
    $j.state = $finalState; Write-Journal $j
}

function Invoke-Plan($j, $stageDir, [string]$expectExeSha) {
    $backup = Join-Path $UpdDir $j.backup
    $count = 0
    foreach ($it in @($j.plan)) {
        $dest = Join-Path $InstallDir ($it.rel -replace '/', '\')
        $bk = Join-Path $backup ($it.rel -replace '/', '\')
        if ($it.op -eq 'replace') {
            Move-FileRetry $dest $bk
            Move-FileRetry (Join-Path $stageDir ($it.src -replace '/', '\')) $dest
        } elseif ($it.op -eq 'add') {
            Move-FileRetry (Join-Path $stageDir ($it.src -replace '/', '\')) $dest
        } elseif ($it.op -eq 'delete') {
            Move-FileRetry $dest $bk
        }
        $count++
        if ($TestCrashAfter -ge 0 -and $count -ge $TestCrashAfter) {
            if ($TestCrashMode -eq 'kill') { [Environment]::Exit(99) }
            throw 'test crash hook'
        }
    }
    $exe = Join-Path $InstallDir $ExeName
    if (-not [IO.File]::Exists($exe)) { throw 'exe missing after the swap' }
    if ($expectExeSha -and ((Get-FileSha256 $exe) -ne $expectExeSha)) { throw 'exe SHA-256 after the swap differs from the manifest' }
}

function Assert-FreeSpace([string]$path, [long]$need, [string]$what) {
    $free = -1L
    if ($TestFreeBytes -ge 0) { $free = $TestFreeBytes }
    else { try { $free = ([IO.DriveInfo]::new([IO.Path]::GetPathRoot([IO.Path]::GetFullPath($path)))).AvailableFreeSpace } catch { return } }
    if ($free -lt $need) { Stop-Update ('not enough free disk space for ' + $what + ': need about {0:N0} MB, {1:N0} MB free on that drive. Free some space and run the updater again. Nothing was changed.' -f ($need / 1MB), ($free / 1MB)) }
}

function Test-GameRunning {
    $exe = Join-Path $InstallDir $ExeName
    foreach ($p in @(Get-Process -Name ([IO.Path]::GetFileNameWithoutExtension($ExeName)) -ErrorAction SilentlyContinue)) {
        $path = $null
        try { $path = $p.MainModule.FileName } catch { }
        if (-not $path) { return $true }   # cannot tell: be safe
        if ($path -ieq $exe) { return $true }
    }
    if ([IO.File]::Exists($exe)) {
        try { $fs = [IO.File]::Open($exe, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None); $fs.Dispose() } catch { return $true }
    }
    return $false
}

# ----------------------------------------------------------------------------- main
$mutex = $null
try {
    # one updater per install folder, across all sessions (Global\), so two instances can never swap at once
    $lockSha = [Security.Cryptography.SHA256]::Create()
    $lockId = (($lockSha.ComputeHash([Text.Encoding]::UTF8.GetBytes($InstallDir.ToLowerInvariant())) | Select-Object -First 8 | ForEach-Object { $_.ToString('x2') }) -join '')
    $lockSha.Dispose()
    try { $mutex = New-Object Threading.Mutex($false, ('Global\MythologyKombatUpdater-' + $lockId)) }
    catch { Write-Host 'Warning: the machine-wide lock could not be created; using a per-session lock instead.'; $mutex = New-Object Threading.Mutex($false, ('Local\MythologyKombatUpdater-' + $lockId)) }
    $got = $false
    try { $got = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $got = $true }   # a killed updater: the journal handles its state
    if (-not $got) { $mutex.Dispose(); $mutex = $null; Stop-Update 'another updater is already running for this folder. Wait for it to finish.' }
    if ($TestHoldSeconds -gt 0) { Say 'test hold'; Start-Sleep -Seconds $TestHoldSeconds }

    Say ('MythologyKombat updater (repo ' + $ReleaseRepo + ')')
    if ($ReleaseRepo -notmatch '^[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9._-]{1,100}\z') { Stop-Update 'the repo constant in update.ps1 is not owner/name' }
    $Repo = $ReleaseRepo

    $ReadOnly = ($CheckOnly -or $DryRun)
    $updExisted = [IO.Directory]::Exists($UpdDir)
    if ($Rollback -and ($CheckOnly -or $DryRun)) { Stop-Update '-Rollback cannot be combined with -CheckOnly or -DryRun' }

    # install folder sanity
    $infoPath = Join-Path $InstallDir 'release_info.json'
    if (-not [IO.File]::Exists((Join-Path $InstallDir $ExeName)) -or -not [IO.File]::Exists($infoPath)) {
        Stop-Update ('not a MythologyKombat folder (need ' + $ExeName + ' and release_info.json): ' + $InstallDir)
    }
    try { $info = [IO.File]::ReadAllText($infoPath) | ConvertFrom-Json } catch { Stop-Update 'release_info.json is not valid JSON' }
    if ($info.repo -and ([string]$info.repo) -ne $Repo) { Stop-Update ('release_info.json says repo "' + (Get-SafeText ([string]$info.repo) 60) + '" but this updater is built for ' + $Repo) }
    $localRaw = [string]$info.version
    if ($localRaw -match '^([0-9]{1,6})\.([0-9]{1,6})\.([0-9]{1,6})\z') { $localVer = [Version]$localRaw }
    else { $localVer = [Version]'0.0.0'; Say ('Installed version label "' + (Get-SafeText $localRaw 30) + '" is not X.Y.Z; treating it as 0.0.0.') }
    $localLabel = ($localRaw -replace '[^A-Za-z0-9._-]', '_'); if ($localLabel.Length -gt 40) { $localLabel = $localLabel.Substring(0, 40) }; if (-not $localLabel) { $localLabel = 'unknown' }
    Say ('Installed version: ' + $localRaw)

    if (-not $CheckOnly) { try {
        $probe = Join-Path $InstallDir '.write-test.tmp'
        [IO.File]::WriteAllText($probe, 'x'); [IO.File]::Delete($probe)
    } catch { Stop-Update 'the install folder is not writable (do not install under Program Files)' } }

    if (-not $CheckOnly -and (Test-GameRunning)) { Stop-Update 'MythologyKombat is running (or its exe is locked). Close the game and run the updater again. Nothing was changed.' }

    # crash recovery first (never in a read-only run: -CheckOnly must not move any file)
    $journal = Read-Journal $ReadOnly
    $recovered = $false
    if ($journal -and (@('swapping', 'rolling-back', 'rollback-failed') -contains [string]$journal.state)) {
        if ($ReadOnly) {
            Say ('NOTE: an earlier update (' + (Get-SafeText ([string]$journal.from) 40) + ' -> ' + (Get-SafeText ([string]$journal.to) 40) + ') was interrupted or its rollback failed (state ' + (Get-SafeText ([string]$journal.state) 20) + '). This run changes nothing. Close the game and run update.cmd normally (without -CheckOnly or -DryRun) to restore the previous version.')
            if ($DryRun) { exit 0 }   # staging would overwrite the interrupted update's stage folder
        } else {
            if ([string]$journal.state -eq 'rollback-failed') { Say 'An earlier rollback was incomplete. Retrying it...' }
            else { Say 'A previous update was interrupted. Restoring the previous version first...' }
            Invoke-Rollback $journal 'rolled-back'
            $recovered = $true
            Say 'Restored.'
            $info = [IO.File]::ReadAllText($infoPath) | ConvertFrom-Json
            $localRaw = [string]$info.version
            if ($localRaw -match '^([0-9]{1,6})\.([0-9]{1,6})\.([0-9]{1,6})\z') { $localVer = [Version]$localRaw } else { $localVer = [Version]'0.0.0' }
            $localLabel = ($localRaw -replace '[^A-Za-z0-9._-]', '_'); if ($localLabel.Length -gt 40) { $localLabel = $localLabel.Substring(0, 40) }; if (-not $localLabel) { $localLabel = 'unknown' }
        }
    }

    # ---- -Rollback
    if ($Rollback -and $recovered) { Say 'The previous version is restored; nothing more to roll back.'; exit 0 }
    if ($Rollback) {
        if (-not $journal -or -not (@('swapped-unconfirmed', 'confirmed') -contains [string]$journal.state) -or -not [IO.Directory]::Exists((Join-Path $UpdDir $journal.backup))) {
            Stop-Update 'nothing to roll back (no kept previous version)'
        }
        Say ('This restores version ' + (Get-SafeText ([string]$journal.from) 40) + ' (replacing ' + (Get-SafeText ([string]$journal.to) 40) + ').')
        if (-not $Yes) {
            $a = $null; try { $a = Read-Host 'Roll back now? [y/N]' } catch { }
            if ($a -notmatch '^(y|yes)$') { Say 'Cancelled. Nothing changed.'; exit 0 }
        }
        Invoke-Rollback $journal 'rolled-back-manual'
        Say ('Rolled back to ' + (Get-SafeText ([string]$journal.from) 40) + '.')
        exit 0
    }

    # confirm an earlier update once the game has run since the swap
    if ($journal -and [string]$journal.state -eq 'swapped-unconfirmed') {
        $since = [DateTime]::new([long]$journal.swapped_ticks, [DateTimeKind]::Utc)
        $ran = $false
        foreach ($m in $RunMarkers) {
            $f = Join-Path $InstallDir $m
            if ([IO.File]::Exists($f) -and ([IO.File]::GetLastWriteTimeUtc($f) -gt $since)) { $ran = $true; break }
        }
        if ($ran -and $ReadOnly) {
            Say ('Note: version ' + (Get-SafeText ([string]$journal.to) 40) + ' has run since the last update; a normal run will remove the old backup. This run changes nothing.')
        } elseif ($ran) {
            Say ('Version ' + (Get-SafeText ([string]$journal.to) 40) + ' has run since the last update; removing the old backup.')
            Remove-Tree (Join-Path $UpdDir $journal.backup)
            $journal.state = 'confirmed'; Write-Journal $journal
        } else {
            Say ('Note: version ' + (Get-SafeText ([string]$journal.to) 40) + ' has not been started since the last update. Run update.cmd -Rollback to go back to ' + (Get-SafeText ([string]$journal.from) 40) + '.')
        }
    }

    # ---- check
    Say 'Checking for a newer release...'
    $tag = $null; $notes = ''; $declaredSize = 0L; $zipDigest = $null
    $api = Get-Following ($ApiBase + '/repos/' + $Repo + '/releases/latest') $null 2MB 'api' ('/repos/' + $Repo + '/')
    if ($api.Status -eq 200) {
        try { $rel = $api.Text | ConvertFrom-Json } catch { Stop-Update 'GitHub answered with something that is not JSON' }
        if ($rel.draft -eq $true -or $rel.prerelease -eq $true) { Stop-Update 'the latest release is a draft or prerelease; refused' }
        $tag = [string]$rel.tag_name
        $notes = Get-SafeText ([string]$rel.body) 2000
        $apiRelease = $rel
    } elseif ($api.Status -eq 403 -or $api.Status -eq 429) {
        Say 'GitHub API rate limit reached; using the release redirect instead (no release notes, no size).'
        [void](Assert-UrlAllowed ($GitHubBase + '/' + $Repo + '/releases/latest/download/checksums.txt') 'download' ('/' + $Repo + '/releases/'))
        $fb = Send-Request ($GitHubBase + '/' + $Repo + '/releases/latest/download/checksums.txt') 'HEAD' $null 0
        if (-not (@(301, 302, 303, 307, 308) -contains $fb.Status) -or -not $fb.Location) { Stop-Update ('fallback failed (HTTP ' + $fb.Status + ')') }
        Assert-NoPercent $fb.Location
        $lu = New-Object Uri((New-Object Uri($GitHubBase)), $fb.Location)
        [void](Assert-UrlAllowed $lu.AbsoluteUri 'download' ('/' + $Repo + '/releases/download/'))
        $mm = [regex]::Match($lu.AbsolutePath, '^/' + [regex]::Escape($Repo) + '/releases/download/(v[0-9]{1,6}\.[0-9]{1,6}\.[0-9]{1,6})/checksums\.txt\z', 'IgnoreCase')
        if (-not $mm.Success) { Stop-Update 'fallback redirect did not name a vX.Y.Z release of this repo' }
        $tag = $mm.Groups[1].Value
        $apiRelease = $null
    } elseif ($api.Status -eq 404) {
        Stop-Update ('no published release found for ' + $Repo + ' (HTTP 404)')
    } else {
        Stop-Update ('GitHub answered HTTP ' + $api.Status + '; try again later')
    }
    $tm = [regex]::Match($tag, '^v([0-9]{1,6})\.([0-9]{1,6})\.([0-9]{1,6})\z')
    if (-not $tm.Success) { Stop-Update ('release tag "' + (Get-SafeText $tag 40) + '" is not vX.Y.Z; refused') }
    $remoteStr = $tm.Groups[1].Value + '.' + $tm.Groups[2].Value + '.' + $tm.Groups[3].Value
    $remoteVer = [Version]$remoteStr
    if ($remoteVer -le $localVer) { Say ('Up to date (latest is ' + $tag + ', installed is ' + $localRaw + '). Nothing to do.'); exit 0 }
    Say ('Newer version available: ' + $remoteStr + ' (installed: ' + $localRaw + ')')
    if ($CheckOnly) { exit 0 }

    $zipName = $ProductName + '-' + $remoteStr + '-Windows-x64.zip'
    $dlPrefix = '/' + $Repo + '/releases/download/' + $tag + '/'
    $dlBase = $GitHubBase + $dlPrefix
    if ($apiRelease) {
        $zipAsset = @($apiRelease.assets | Where-Object { $_.name -ceq $zipName })
        $sumAsset = @($apiRelease.assets | Where-Object { $_.name -ceq 'checksums.txt' })
        if ($zipAsset.Count -ne 1 -or $sumAsset.Count -ne 1) { Stop-Update ('the release must have exactly one ' + $zipName + ' and one checksums.txt') }
        if ([string]$zipAsset[0].browser_download_url -cne ($dlBase + $zipName) -or [string]$sumAsset[0].browser_download_url -cne ($dlBase + 'checksums.txt')) {
            Stop-Update 'asset URLs do not match https://github.com/<repo>/releases/download/<tag>/<name>; refused'
        }
        $declaredSize = [long]$zipAsset[0].size
        $zipDigest = $null
        if ([string]$zipAsset[0].digest -match '^sha256:([0-9a-fA-F]{64})\z') { $zipDigest = $Matches[1].ToLowerInvariant() }
        elseif ($zipAsset[0].digest) { Say 'Note: the release API digest is not a sha256 value; ignored.' }
        if ($declaredSize -le 0 -or $declaredSize -gt $MaxZipBytes) { Stop-Update ('zip size ' + $declaredSize + ' is outside the allowed range') }
    }
    if ($notes) { Say ''; Say 'Release notes:'; Say $notes; Say '' }
    if ($declaredSize) { Say ('Download size: {0:N1} MB' -f ($declaredSize / 1MB)) }

    if ($Yes) { $ok = $true }
    else {
        $a = $null; try { $a = Read-Host 'Download and install? [y/N]' } catch { }
        $ok = ($a -match '^(y|yes)$')
    }
    if (-not $ok) { Say 'Cancelled. Nothing changed.'; exit 0 }

    # ---- download (fresh folder, every hop checked)
    $dl = Join-Path $DataDir ('dl-' + $remoteStr)
    Remove-Tree $dl
    [void][IO.Directory]::CreateDirectory($dl)
    $zipPath = Join-Path $dl $zipName
    $sumPath = Join-Path $dl 'checksums.txt'
    $stageName = 'stage-' + $remoteStr
    $stage = Join-Path $UpdDir $stageName
    $keepStage = $false
    try {
        $capZip = $MaxZipBytes; if ($declaredSize) { $capZip = $declaredSize + 1024 }
        Assert-FreeSpace $DataDir ($capZip + 64MB) 'the download'
        Say 'Downloading checksums.txt...'
        $r1 = Get-Following ($dlBase + 'checksums.txt') $sumPath 65536 'download' $dlPrefix
        if ($r1.Status -ne 200) { Stop-Update ('checksums.txt download failed (HTTP ' + $r1.Status + ')') }
        Say 'Downloading the zip...'
        $r2 = Get-Following ($dlBase + $zipName) $zipPath $capZip 'download' $dlPrefix
        if ($r2.Status -ne 200) { Stop-Update ('zip download failed (HTTP ' + $r2.Status + ')') }
        if ($declaredSize -and $r2.Bytes -ne $declaredSize) { Stop-Update ('downloaded ' + $r2.Bytes + ' bytes but the release declares ' + $declaredSize) }

        # ---- SHA-256 before anything is opened as a zip
        $want = @()
        foreach ($line in [IO.File]::ReadAllLines($sumPath)) {
            $m = [regex]::Match($line, '^([0-9a-fA-F]{64}) [ *](.+?)\s*$')
            if ($m.Success -and $m.Groups[2].Value -ceq $zipName) { $want += $m.Groups[1].Value.ToLowerInvariant() }
        }
        if ($want.Count -eq 0) { Stop-Update ('checksums.txt has no line for ' + $zipName) }
        if (@($want | Select-Object -Unique).Count -ne 1) { Stop-Update 'checksums.txt has conflicting lines for the zip' }
        # one open handle (FileShare.Read) for hash and extraction: the file cannot be swapped in between
        $zfs = [IO.File]::Open($zipPath, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
        $zipOpened = $false
        try {
            $shaz = [Security.Cryptography.SHA256]::Create()
            $have = (($shaz.ComputeHash($zfs) | ForEach-Object { $_.ToString('x2') }) -join ''); $shaz.Dispose()
            if ($have -ne $want[0]) { Stop-Update ('SHA-256 MISMATCH: the download is not the published file (expected ' + $want[0] + ', got ' + $have + '). Nothing was replaced.') }
            if ($zipDigest -and $zipDigest -ne $have) { Stop-Update ('SHA-256 MISMATCH: the release API digest (' + $zipDigest + ') differs from the download. Nothing was replaced.') }
            Say ('SHA-256 verified: ' + $have + $(if ($zipDigest) { ' (also matches the GitHub API digest)' } else { '' }))

            # ---- validate every zip entry, then extract entry by entry into the stage
            $top = $ProductName + '-' + $remoteStr + '/'
            [void]$zfs.Seek(0, [IO.SeekOrigin]::Begin)
            try { $za = New-Object IO.Compression.ZipArchive($zfs, [IO.Compression.ZipArchiveMode]::Read) } catch { Stop-Update ('the zip cannot be read: ' + $_.Exception.Message) }
            $zipOpened = $true
        try {
            $entries = @($za.Entries)
            if ($entries.Count -gt $MaxEntries) { Stop-Update ('zip has too many entries (' + $entries.Count + ')') }
            $seen = New-Object 'System.Collections.Generic.HashSet[string]'
            $zmap = New-Object 'System.Collections.Generic.Dictionary[string,object]'
            $total = 0L
            foreach ($e in $entries) {
                $name = $e.FullName
                if (-not $name.StartsWith($top, [StringComparison]::Ordinal)) { Stop-Update ('zip entry outside the top folder ' + $top + ': ' + (Get-SafeText $name 80)) }
                $rel = $name.Substring($top.Length)
                if ($rel.Length -eq 0) { continue }
                if ($rel.EndsWith('/')) {
                    $de = Get-RelPathError $rel.TrimEnd('/'); if ($de) { Stop-Update ('bad zip directory entry ' + (Get-SafeText $name 80) + ': ' + $de) }
                    continue
                }
                $pe = Get-RelPathError $rel
                if ($pe) { Stop-Update ('bad zip entry "' + (Get-SafeText $name 80) + '": ' + $pe) }
                if ((($e.ExternalAttributes -shr 16) -band 0xF000) -eq 0xA000) { Stop-Update ('symbolic link in zip: ' + (Get-SafeText $name 80)) }
                if (-not $seen.Add($rel.ToLowerInvariant())) { Stop-Update ('duplicate zip entry: ' + (Get-SafeText $name 80)) }
                if (Test-Preserved $rel) { Stop-Update ('the zip contains a protected player file: ' + (Get-SafeText $rel 80)) }
                if ($e.Length -gt $MaxEntryBytes) { Stop-Update ('zip entry too large: ' + (Get-SafeText $name 80)) }
                $total += $e.Length
                if ($total -gt $MaxTotalBytes) { Stop-Update 'zip total size too large' }
                $zmap[$rel] = $e
            }
            Assert-FreeSpace $InstallDir ($total + 64MB) 'the staged files'
            if (-not $zmap.ContainsKey('manifest.json')) { Stop-Update 'the zip has no manifest.json' }
            if ($zmap['manifest.json'].Length -gt $MaxTextBytes) { Stop-Update 'manifest.json too large' }
            $sr = New-Object IO.StreamReader($zmap['manifest.json'].Open(), [Text.Encoding]::UTF8)
            try { $manJson = $sr.ReadToEnd() } finally { $sr.Dispose() }
            $newMan = Read-Manifest $manJson 'new manifest.json'
            if ($newMan.Version -ne $remoteStr) { Stop-Update ('manifest.json is for version "' + (Get-SafeText $newMan.Version 30) + '", not ' + $remoteStr) }
            foreach ($k in $newMan.Map.Keys) { if (-not $zmap.ContainsKey($k)) { Stop-Update ('manifest lists a file the zip lacks: ' + (Get-SafeText $k 80)) }; if (Test-Preserved $k) { Stop-Update ('manifest lists a protected player file: ' + (Get-SafeText $k 80)) } }
            foreach ($k in $zmap.Keys) { if ($k -ne 'manifest.json' -and -not $newMan.Map.ContainsKey($k)) { Stop-Update ('the zip has a file the manifest does not list: ' + (Get-SafeText $k 80)) } }
            if (-not $newMan.Map.ContainsKey($ExeName)) { Stop-Update ('manifest has no ' + $ExeName) }
            Say ('Zip validated: ' + $zmap.Count + ' files.')

            # extract
            Remove-Tree $stage
            [void][IO.Directory]::CreateDirectory($stage)
            $keepStage = $true
            $stageFull = [IO.Path]::GetFullPath($stage).TrimEnd('\') + '\'
            $sha = [Security.Cryptography.SHA256]::Create()
            $buf = New-Object byte[] 65536
            foreach ($rel in @($zmap.Keys | Sort-Object)) {
                $e = $zmap[$rel]
                $dest = [IO.Path]::GetFullPath((Join-Path $stage ($rel -replace '/', '\')))
                if (-not $dest.StartsWith($stageFull, [StringComparison]::OrdinalIgnoreCase)) { Stop-Update ('entry escapes the stage folder: ' + (Get-SafeText $rel 80)) }
                $dd = [IO.Path]::GetDirectoryName($dest); if (-not [IO.Directory]::Exists($dd)) { [void][IO.Directory]::CreateDirectory($dd) }
                $in = $e.Open(); $out = [IO.File]::Open($dest, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
                $sha.Initialize(); $cnt = 0L
                try {
                    while (($n = $in.Read($buf, 0, $buf.Length)) -gt 0) {
                        $cnt += $n
                        if ($cnt -gt $e.Length) { Stop-Update ('zip entry is longer than declared: ' + (Get-SafeText $rel 80)) }
                        [void]$sha.TransformBlock($buf, 0, $n, $null, 0)
                        $out.Write($buf, 0, $n)
                    }
                    [void]$sha.TransformFinalBlock($buf, 0, 0)
                } finally { $in.Dispose(); $out.Dispose() }
                if ($cnt -ne $e.Length) { Stop-Update ('zip entry shorter than declared: ' + (Get-SafeText $rel 80)) }
                if ($rel -ne 'manifest.json') {
                    $ent = $newMan.Map[$rel]
                    $hex = (($sha.Hash | ForEach-Object { $_.ToString('x2') }) -join '')
                    if ($ent.Size -ne $cnt -or $ent.Sha -ne $hex) { Stop-Update ('file differs from manifest.json: ' + (Get-SafeText $rel 80)) }
                }
            }
            $sha.Dispose()
        } finally { $za.Dispose() }
        } finally { if (-not $zipOpened) { $zfs.Dispose() } }

        # staged release_info checks
        $sInfoPath = Join-Path $stage 'release_info.json'
        if (-not [IO.File]::Exists($sInfoPath)) { Stop-Update 'the release has no release_info.json' }
        $sInfo = [IO.File]::ReadAllText($sInfoPath) | ConvertFrom-Json
        if ([string]$sInfo.version -ne $remoteStr) { Stop-Update 'release_info.json version differs from the release tag' }
        if ([string]$sInfo.repo -ne $Repo) { Stop-Update ('release_info.json repo is "' + (Get-SafeText ([string]$sInfo.repo) 60) + '", expected ' + $Repo + '; refused (an update must keep the update source)') }
        $newExeSha = $newMan.Map[$ExeName].Sha
        if ($sInfo.exe_sha256 -and ([string]$sInfo.exe_sha256) -ne $newExeSha) { Stop-Update 'release_info.json exe_sha256 differs from the manifest' }

        # ---- plan
        $oldMan = $null
        $oldManPath = Join-Path $InstallDir 'manifest.json'
        if ([IO.File]::Exists($oldManPath)) {
            try { $oldMan = Read-Manifest ([IO.File]::ReadAllText($oldManPath)) 'installed manifest.json' } catch { Say ('Warning: installed manifest.json is not usable (' + ($_.Exception.Message -replace '^UPDATER:', '') + '); no files will be deleted.') }
        } else { Say 'Note: the installed version has no manifest.json; no files will be deleted and game.toml is kept unless identical.' }

        $plan = New-Object System.Collections.ArrayList
        $kept = @(); $unchanged = 0
        $relList = New-Object System.Collections.Generic.List[string]
        foreach ($k in $newMan.Map.Keys) { $relList.Add($k) }
        $relList.Sort([StringComparer]::Ordinal)
        $late = @($ExeName, 'release_info.json')
        $ordered = @($relList | Where-Object { $late -cnotcontains $_ }) + @($relList | Where-Object { $late -ccontains $_ })
        foreach ($rel in $ordered) {
            $ent = $newMan.Map[$rel]
            $dest = Join-Path $InstallDir ($rel -replace '/', '\')
            $exists = [IO.File]::Exists($dest)
            if ($ConfFiles -contains $rel) {
                if (-not $exists) { [void]$plan.Add(@{ rel = $rel; op = 'add'; src = $rel; new_sha = $ent.Sha }); continue }
                $disk = Get-FileSha256 $dest
                if ($disk -eq $ent.Sha) { $unchanged++; continue }
                if ($oldMan -and $oldMan.Map.ContainsKey($rel) -and $oldMan.Map[$rel].Sha -eq $disk) { [void]$plan.Add(@{ rel = $rel; op = 'replace'; src = $rel; old_sha = $disk; new_sha = $ent.Sha }); continue }
                $kept += $rel
                $newRel = $rel + '.new'
                $op = 'add'; if ([IO.File]::Exists((Join-Path $InstallDir $newRel))) { $op = 'replace' }
                $oldNew = $null; if ($op -eq 'replace') { $oldNew = Get-FileSha256 (Join-Path $InstallDir ($newRel.Replace('/', [string][char]92))) }
                [void]$plan.Add(@{ rel = $newRel; op = $op; src = $rel; old_sha = $oldNew; new_sha = $ent.Sha })
                continue
            }
            if (-not $exists) { [void]$plan.Add(@{ rel = $rel; op = 'add'; src = $rel; new_sha = $ent.Sha }); continue }
            $diskSha = Get-FileSha256 $dest
            if ($diskSha -eq $ent.Sha) { $unchanged++; continue }
            [void]$plan.Add(@{ rel = $rel; op = 'replace'; src = $rel; old_sha = $diskSha; new_sha = $ent.Sha })
        }
        $manOp = 'add'; if ([IO.File]::Exists($oldManPath)) { $manOp = 'replace' }
        $manSha = Get-FileSha256 (Join-Path $stage 'manifest.json'); $oldManSha = $null
        if ($manOp -eq 'replace') { $oldManSha = Get-FileSha256 $oldManPath }
        [void]$plan.Add(@{ rel = 'manifest.json'; op = $manOp; src = 'manifest.json'; old_sha = $oldManSha; new_sha = $manSha })
        $dropped = @()
        if ($oldMan) {
            foreach ($rel in @($oldMan.Map.Keys | Sort-Object)) {
                if ($newMan.Map.ContainsKey($rel) -or (Test-Preserved $rel)) { continue }
                $dest = Join-Path $InstallDir ($rel -replace '/', '\')
                if (-not [IO.File]::Exists($dest)) { continue }
                if ((Get-FileSha256 $dest) -eq $oldMan.Map[$rel].Sha) { [void]$plan.Add(@{ rel = $rel; op = 'delete'; src = $null; old_sha = $oldMan.Map[$rel].Sha }) }
                else { $dropped += $rel }
            }
        }
        $nRep = @($plan | Where-Object { $_.op -eq 'replace' }).Count
        $nAdd = @($plan | Where-Object { $_.op -eq 'add' }).Count
        $nDel = @($plan | Where-Object { $_.op -eq 'delete' }).Count
        Say ('Plan: replace {0}, add {1}, delete {2}, unchanged {3}.' -f $nRep, $nAdd, $nDel, $unchanged)
        foreach ($k in $kept) { Say ('WARNING: ' + $k + ' differs from the shipped one; your copy is kept and the new one is saved as ' + $k + '.new') }
        foreach ($k in $dropped) { Say ('Note: ' + $k + ' was removed from the release but you changed it; left in place.') }

        if ($DryRun) { Say 'Dry run: stopping before the swap. Nothing in the install changed.'; Remove-Tree $stage; $keepStage = $false; if (-not $updExisted -and [IO.Directory]::Exists($UpdDir) -and @(Get-ChildItem -LiteralPath $UpdDir -Force).Count -eq 0) { [IO.Directory]::Delete($UpdDir) }; exit 0 }

        # ---- swap (journaled; moves only)
        foreach ($d in @(Get-ChildItem -LiteralPath $UpdDir -Directory -Filter 'backup-*' -ErrorAction SilentlyContinue)) { Remove-Tree $d.FullName }
        if (Test-GameRunning) { Stop-Update 'MythologyKombat started while the update was being prepared. Close it and run the updater again. Nothing was changed.' }
        $backupName = 'backup-' + $localLabel
        $j = [ordered]@{
            state = 'swapping'; from = $localRaw; to = $remoteStr; backup = $backupName; stage = $stageName
            started_ticks = [DateTime]::UtcNow.Ticks; swapped_ticks = 0
            plan = @($plan | ForEach-Object { [ordered]@{ rel = $_.rel; op = $_.op; src = $_.src; old_sha = $_.old_sha; new_sha = $_.new_sha } })
        }
        $jo = [pscustomobject]$j
        Write-Journal $jo
        Say 'Installing...'
        try {
            Invoke-Plan $jo $stage $newExeSha
        } catch {
            $why = $_.Exception.Message
            Say ('Update failed: ' + $why)
            Say 'Restoring the previous version...'
            $jr = Read-Journal
            Invoke-Rollback $jr 'rolled-back'
            $keepStage = $false
            Stop-Update ('update failed and was rolled back (' + $why + ')')
        }
        $jo.state = 'swapped-unconfirmed'; $jo.swapped_ticks = [DateTime]::UtcNow.Ticks
        Write-Journal $jo
        Remove-Tree $stage; $keepStage = $false
        Say ''
        Say ('Updated to ' + $remoteStr + '. The previous version is kept in .update\' + $backupName + ' until the new one has run once.')
        Say 'Start the game from this folder as usual. To undo: update.cmd -Rollback'
        exit 0
    } finally {
        Remove-Tree $dl
        if ($keepStage) { Remove-Tree $stage }
    }
} catch {
    $msg = $_.Exception.Message
    if ($msg.StartsWith('UPDATER:')) { Write-Host ('ERROR: ' + $msg.Substring(8)) }
    else { Write-Host ('ERROR: unexpected: ' + $msg) }
    exit 1
} finally {
    if ($mutex) { try { $mutex.ReleaseMutex() } catch { }; $mutex.Dispose() }
}
