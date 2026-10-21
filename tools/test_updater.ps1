<#
.SYNOPSIS
  Test harness for the standalone updater (T3.21). Windows PowerShell 5.1.

.DESCRIPTION
  Builds fake installs under work\updater_test from a real release folder (default work\release\test\MythologyKombat-test),
  serves fake releases from a local HTTP server (tests\updater_test_server.py on 127.0.0.1) and runs
  tools\updater\update.ps1 in test mode against it. No network, no disc, no ps1_game. Writes only under work\updater_test.

  Cases (UPDATER_DESIGN section 10): good update, bad checksum, truncated zip, hostile zips, downgrade/equal/odd tags,
  wrong-host redirects, game running, crash during swap (throw and hard kill) + recovery, -Rollback, preserved files,
  game.toml conffile rule, rate-limit fallback, repo mismatch, test-flag refusal outside test mode, unconfirmed/confirmed.

.PARAMETER SourceDir  A real release folder to build from (needs MythologyKombat.exe and release_info.json).
.PARAMETER Only       Optional case-name filter (substring).
#>
[CmdletBinding()]
param(
    [string]$SourceDir,
    [string]$Only = ''
)
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $SourceDir) { $SourceDir = Join-Path $RepoRoot 'work\release\test\MythologyKombat-test' }
if (-not (Test-Path -LiteralPath (Join-Path $SourceDir 'MythologyKombat.exe'))) { throw "no release folder at $SourceDir (run tools\release.ps1 or pass -SourceDir)" }
$W = Join-Path $RepoRoot 'work\updater_test'
$Updater = Join-Path $RepoRoot 'tools\updater'
$Repo = 'PAumedes/MythologyKombat'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Sha([string]$p) {
    $s = [Security.Cryptography.SHA256]::Create(); $f = [IO.File]::OpenRead($p)
    try { return (($s.ComputeHash($f) | ForEach-Object { $_.ToString('x2') }) -join '') } finally { $f.Dispose(); $s.Dispose() }
}
function ShaBytes([byte[]]$b) { $s = [Security.Cryptography.SHA256]::Create(); try { return (($s.ComputeHash($b) | ForEach-Object { $_.ToString('x2') }) -join '') } finally { $s.Dispose() } }
function Rmrf([string]$p) { if (Test-Path -LiteralPath $p) { & cmd.exe /c "rd /s /q `"$p`"" | Out-Null } }
function Copy-Tree([string]$from, [string]$to) {
    & robocopy.exe $from $to /E /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed $LASTEXITCODE" }
}
function Get-TreeHash([string]$dir, [switch]$All) {
    $base = (Resolve-Path -LiteralPath $dir).Path.TrimEnd('\')
    $lines = New-Object System.Collections.Generic.List[string]
    foreach ($f in Get-ChildItem -LiteralPath $base -Recurse -File -Force) {
        $rel = $f.FullName.Substring($base.Length + 1).Replace('\', '/')
        if ((-not $All -and $rel -like '.update/*') -or $rel -ieq '.write-test.tmp') { continue }
        $lines.Add(('{0}|{1}|{2}' -f $rel, $f.Length, (Sha $f.FullName)))
    }
    $lines.Sort([StringComparer]::Ordinal)
    return (ShaBytes ([Text.Encoding]::UTF8.GetBytes(($lines -join "`n"))))
}
function Get-FullState([string]$dir) {
    # every file (path, size, SHA-256, last-write ticks) AND every directory (so an empty .update folder shows up)
    $base = (Resolve-Path -LiteralPath $dir).Path.TrimEnd('\')
    $lines = New-Object System.Collections.Generic.List[string]
    foreach ($i in Get-ChildItem -LiteralPath $base -Recurse -Force) {
        $rel = $i.FullName.Substring($base.Length + 1).Replace('\', '/')
        if ($i.PSIsContainer) { $lines.Add("D|$rel") }
        else { $lines.Add(('F|{0}|{1}|{2}|{3}' -f $rel, $i.Length, (Sha $i.FullName), $i.LastWriteTimeUtc.Ticks)) }
    }
    $lines.Sort([StringComparer]::Ordinal)
    return (ShaBytes ([Text.Encoding]::UTF8.GetBytes(($lines -join "`n"))))
}
function Write-Utf8([string]$p, [string]$t) {
    $d = Split-Path $p -Parent; if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
    [IO.File]::WriteAllText($p, $t, (New-Object Text.UTF8Encoding($false)))
}
function Read-Json([string]$p) { return ([IO.File]::ReadAllText($p) | ConvertFrom-Json) }
function Set-ReleaseInfo([string]$dir, [string]$ver, [string]$repo) {
    $p = Join-Path $dir 'release_info.json'
    $j = Read-Json $p
    $j.version = $ver; $j.tag = "v$ver"
    if ($j.PSObject.Properties['repo']) { $j.repo = $repo } else { $j | Add-Member -NotePropertyName repo -NotePropertyValue $repo }
    $j.exe_sha256 = Sha (Join-Path $dir 'MythologyKombat.exe')
    $j.exe_size = (Get-Item -LiteralPath (Join-Path $dir 'MythologyKombat.exe')).Length
    Write-Utf8 $p (($j | ConvertTo-Json -Depth 6) + "`n")
}
function New-Manifest([string]$dir, [string]$ver) { & (Join-Path $PSScriptRoot 'new_release_manifest.ps1') -Dir $dir -Version $ver | Out-Null }

function New-ZipFromEntries([string]$zipPath, $entries, [bool]$fast = $true) {
    # entries: array of @{ name=...; bytes=... } or @{ name=...; file=... } or @{ name=...; zeros=<MB> }
    if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
    $fs = [IO.File]::Open($zipPath, [IO.FileMode]::Create, [IO.FileAccess]::Write)
    try {
        $za = New-Object IO.Compression.ZipArchive($fs, [IO.Compression.ZipArchiveMode]::Create)
        try {
            foreach ($e in $entries) {
                $lvl = [IO.Compression.CompressionLevel]::Fastest
                $en = $za.CreateEntry([string]$e.name, $lvl)
                $en.LastWriteTime = New-Object DateTimeOffset((Get-Date '2026-01-01').ToUniversalTime(), [TimeSpan]::Zero)
                $es = $en.Open()
                try {
                    if ($e.ContainsKey('file')) { $in = [IO.File]::OpenRead($e.file); try { $in.CopyTo($es) } finally { $in.Dispose() } }
                    elseif ($e.ContainsKey('zeros')) { $z = New-Object byte[] (1MB); for ($i = 0; $i -lt $e.zeros; $i++) { $es.Write($z, 0, $z.Length) } }
                    else { $b = [byte[]]$e.bytes; $es.Write($b, 0, $b.Length) }
                } finally { $es.Dispose() }
            }
        } finally { $za.Dispose() }
    } finally { $fs.Dispose() }
}
function New-ZipFromDir([string]$dir, [string]$top, [string]$zipPath) {
    $base = (Resolve-Path -LiteralPath $dir).Path.TrimEnd('\')
    $rels = New-Object System.Collections.Generic.List[string]
    foreach ($f in Get-ChildItem -LiteralPath $base -Recurse -File) { $rels.Add($f.FullName.Substring($base.Length + 1).Replace('\', '/')) }
    $rels.Sort([StringComparer]::Ordinal)
    New-ZipFromEntries $zipPath @($rels | ForEach-Object { @{ name = "$top/$_"; file = (Join-Path $base ($_.Replace('/', '\'))) } })
}

# ------------------------------------------------------------------ fixtures
$results = New-Object System.Collections.Generic.List[object]
$script:failed = 0
function Check([string]$case, [bool]$ok, [string]$what) {
    $results.Add(@{ case = $case; ok = $ok; what = $what })
    if ($ok) { Write-Host ("    ok    " + $what) } else { Write-Host ("    FAIL  " + $what); $script:failed++ }
}

Rmrf $W
New-Item -ItemType Directory -Force -Path $W | Out-Null
$Www = Join-Path $W 'www'; $Inst = Join-Path $W 'inst'; $Data = Join-Path $W 'data'; $Dl = Join-Path $W 'zips'
New-Item -ItemType Directory -Force -Path $Www, $Inst, $Dl | Out-Null

Write-Host 'Building the base (0.1.0) and the new (0.2.0) release trees from the real release folder...'
$Base = Join-Path $W 'base'
Copy-Tree $SourceDir $Base
Copy-Item (Join-Path $Updater 'update.ps1') $Base -Force
Copy-Item (Join-Path $Updater 'update.cmd') $Base -Force
Set-ReleaseInfo $Base '0.1.0' $Repo
New-Manifest $Base '0.1.0'

$NewDir = Join-Path $W 'new\MythologyKombat-0.2.0'
Copy-Tree $Base $NewDir
$exeNew = Join-Path $NewDir 'MythologyKombat.exe'
$fs = [IO.File]::Open($exeNew, [IO.FileMode]::Append); $fs.Write([byte[]](1, 2, 3, 4, 5, 6, 7, 8), 0, 8); $fs.Dispose()
Add-Content -LiteralPath (Join-Path $NewDir 'README_FIRST.txt') -Value 'v0.2.0 note' -Encoding ASCII
Add-Content -LiteralPath (Join-Path $NewDir 'game.toml') -Value '# new default in 0.2.0' -Encoding ASCII
Add-Content -LiteralPath (Join-Path $NewDir 'game_options.toml') -Value '# new option default in 0.2.0' -Encoding ASCII
$dropFile = Get-ChildItem -LiteralPath (Join-Path $NewDir 'licenses') -File | Select-Object -First 1
$DropRel = 'licenses/' + $dropFile.Name
Remove-Item -LiteralPath $dropFile.FullName
Write-Utf8 (Join-Path $NewDir 'assets\new_in_020.txt') "new file`n"
Set-ReleaseInfo $NewDir '0.2.0' $Repo
New-Manifest $NewDir '0.2.0'
$NewExeSha = Sha $exeNew
$OldExeSha = Sha (Join-Path $Base 'MythologyKombat.exe')
$GoodZipName = 'MythologyKombat-0.2.0-Windows-x64.zip'
$GoodZip = Join-Path $Dl $GoodZipName
New-ZipFromDir $NewDir 'MythologyKombat-0.2.0' $GoodZip
Write-Host ("  good zip: {0:N1} MB, drop file {1}" -f ((Get-Item $GoodZip).Length / 1MB), $DropRel)

# server
$l = New-Object Net.Sockets.TcpListener([Net.IPAddress]::Loopback, 0); $l.Start(); $Port = $l.LocalEndpoint.Port; $l.Stop()
$BaseUrl = "http://127.0.0.1:$Port"
$Py = Join-Path $env:USERPROFILE 'retro-tools\python\python.exe'
if (-not (Test-Path -LiteralPath $Py)) { $Py = (Get-Command python -CommandType Application | Select-Object -First 1).Source }
$srv = Start-Process -FilePath $Py -ArgumentList @('-I', (Join-Path $RepoRoot 'tests\updater_test_server.py'), '--root', $Www, '--port', $Port) -PassThru -WindowStyle Hidden
$up = $false
for ($i = 0; $i -lt 50 -and -not $up; $i++) {
    try { $c = New-Object Net.Sockets.TcpClient('127.0.0.1', $Port); $c.Close(); $up = $true } catch { Start-Sleep -Milliseconds 200 }
}
if (-not $up) { throw 'test server did not start' }
Write-Host "test server on $BaseUrl"
$ReqLog = Join-Path $W 'requests.log'

function Reset-Www { Rmrf $Www; New-Item -ItemType Directory -Force -Path $Www | Out-Null; if (Test-Path $ReqLog) { Remove-Item $ReqLog } }
function Publish-Release([string]$tag, [string]$zipPath, [string]$zipName, [string]$sumsText, [hashtable]$over = @{}) {
    # lays out the API JSON, the zip and checksums.txt on the server
    $dir = Join-Path $Www ("$Repo/releases/download/$tag".Replace('/', '\'))
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Copy-Item -LiteralPath $zipPath -Destination (Join-Path $dir $zipName) -Force
    Write-Utf8 (Join-Path $dir 'checksums.txt') $sumsText
    $dlBase = "$BaseUrl/$Repo/releases/download/$tag"
    $size = (Get-Item -LiteralPath $zipPath).Length
    if ($over.ContainsKey('size')) { $size = $over.size }
    $digest = 'sha256:' + (Sha $zipPath)
    if ($over.ContainsKey('digest')) { $digest = $over.digest }
    $rel = [ordered]@{
        tag_name = $tag; draft = $false; prerelease = $false; body = "Notes for $tag`nline two"
        assets = @(
            [ordered]@{ name = $zipName; size = $size; digest = $digest; browser_download_url = "$dlBase/$zipName" },
            [ordered]@{ name = 'checksums.txt'; size = 100; browser_download_url = "$dlBase/checksums.txt" })
    }
    foreach ($k in $over.Keys) { if (@('size', 'digest') -notcontains $k) { $rel[$k] = $over[$k] } }
    Write-Utf8 (Join-Path $Www ("repos\$Repo\releases\latest".Replace('/', '\'))) ($rel | ConvertTo-Json -Depth 5)
}
function Sums([string]$zipPath, [string]$zipName) { return ("{0}  {1}`n" -f (Sha $zipPath), $zipName) }
function Set-Route([string]$urlPath, [int]$status, [hashtable]$headers) {
    $p = Join-Path $Www ($urlPath.TrimStart('/').Replace('/', '\') + '.route.json')
    Write-Utf8 $p (@{ status = $status; headers = $headers; body = 'route' } | ConvertTo-Json -Depth 4)
}

$DataN = 0
function New-Install([string]$name) {
    $d = Join-Path $Inst $name
    Rmrf $d
    Copy-Tree $Base $d
    # files the player / runtime create (UPDATER_DESIGN 5, question 293)
    $rnd = New-Object byte[] 1024; (New-Object Random 7).NextBytes($rnd)
    New-Item -ItemType Directory -Force -Path (Join-Path $d 'saves'), (Join-Path $d 'mods\texture-packs'), (Join-Path $d 'cache\SLUS-00476') | Out-Null
    [IO.File]::WriteAllBytes((Join-Path $d 'saves\card1.mcd'), $rnd)
    Write-Utf8 (Join-Path $d 'settings.toml') "[video]`nscale = 3`n"
    Write-Utf8 (Join-Path $d 'input.ini') "pad1=keyboard`n"
    Write-Utf8 (Join-Path $d 'keybinds.ini') "a=Z`n"
    Write-Utf8 (Join-Path $d 'disc.cfg') "disc=Z:\fake\disc.cue`n"
    Write-Utf8 (Join-Path $d 'bios.cfg') "bios=Z:\fake\bios`n"
    Write-Utf8 (Join-Path $d 'launcher-window.ini') "x=10`n"
    Write-Utf8 (Join-Path $d 'mods\state.toml') "enabled=[]`n"
    [IO.File]::WriteAllBytes((Join-Path $d 'mods\texture-packs\t.png'), $rnd)
    [IO.File]::WriteAllBytes((Join-Path $d 'cache\SLUS-00476\x.bin'), $rnd)
    Write-Utf8 (Join-Path $d 'overlay_captures.json') "{}`n"
    return $d
}
$PlayerRels = @('saves\card1.mcd', 'settings.toml', 'input.ini', 'keybinds.ini', 'disc.cfg', 'bios.cfg', 'launcher-window.ini',
    'mods\state.toml', 'mods\texture-packs\t.png', 'cache\SLUS-00476\x.bin', 'overlay_captures.json')
function Get-PlayerHash([string]$d) { return (($PlayerRels | ForEach-Object { $_ + '=' + (Sha (Join-Path $d $_)) }) -join ';') }

function Invoke-Updater([string]$d, [string[]]$extra = @(), [bool]$testMode = $true, [bool]$yes = $true) {
    $dataDir = Join-Path $Data ('d' + ($script:DataN++))
    $a = @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $d 'update.ps1'))
    if ($testMode) { $a += @('-TestBaseUrl', $BaseUrl, '-TestDataDir', $dataDir) }
    if ($yes -and $testMode) { $a += '-Yes' }
    $a += $extra
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    $out = (& powershell.exe @a 2>&1 | Out-String)
    $code = $LASTEXITCODE
    $ErrorActionPreference = $old
    return @{ out = $out; code = $code; data = $dataDir }
}
function Want-Case([string]$name) { return ($Only -eq '' -or $name -like "*$Only*") }
function Show-Out($r) { ($r.out -split "`r?`n" | Where-Object { $_ } | ForEach-Object { '      | ' + $_ }) -join "`n" }

try {
    $goodSums = Sums $GoodZip $GoodZipName

    # ============================================================ 1 good update + preserved + self copy + rollback
    $case = '01 good update'
    if (Want-Case $case) {
        Write-Host "[$case]"
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
        $d = New-Install 'c01'
        $pre = Get-TreeHash $d; $prePlayer = Get-PlayerHash $d
        $r = Invoke-Updater $d @('-CheckOnly')
        Check $case ($r.code -eq 0 -and $r.out -match 'Newer version available: 0\.2\.0') 'CheckOnly finds 0.2.0 and changes nothing'
        Check $case ((Get-TreeHash $d) -eq $pre) 'tree identical after CheckOnly'
        $r = Invoke-Updater $d @('-DryRun')
        Check $case ($r.code -eq 0 -and $r.out -match 'Dry run' -and $r.out -match 'SHA-256 verified') 'DryRun verifies and stops'
        Check $case ((Get-TreeHash $d) -eq $pre -and -not (Test-Path (Join-Path $d '.update\stage-0.2.0'))) 'tree identical after DryRun, stage removed'
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 0 -and $r.out -match 'Updated to 0\.2\.0') ('update exit 0 and message' + $(if ($r.code -ne 0) { "`n" + (Show-Out $r) } else { '' }))
        Check $case ((Read-Json (Join-Path $d 'release_info.json')).version -eq '0.2.0') 'release_info.json says 0.2.0'
        Check $case ((Sha (Join-Path $d 'MythologyKombat.exe')) -eq $NewExeSha) 'installed exe is the new exe (hash)'
        $man = Read-Json (Join-Path $d 'manifest.json'); $bad = 0
        foreach ($f in $man.files) { $p = Join-Path $d ($f.path.Replace('/', '\')); if (-not (Test-Path -LiteralPath $p) -or (Sha $p) -ne $f.sha256) { $bad++ } }
        Check $case ($bad -eq 0) ("every file of the new manifest ({0}) is installed byte-exact" -f @($man.files).Count)
        Check $case (-not (Test-Path -LiteralPath (Join-Path $d $DropRel.Replace('/', '\')))) 'file dropped by 0.2.0 was removed'
        Check $case (Test-Path -LiteralPath (Join-Path $d 'assets\new_in_020.txt')) 'file added by 0.2.0 exists'
        Check $case ((Get-PlayerHash $d) -eq $prePlayer) 'saves, settings, input, disc.cfg, bios.cfg, mod state, texture packs, cache, captures byte-identical'
        Check $case ((Sha (Join-Path $d '.update\backup-0.1.0\MythologyKombat.exe')) -eq $OldExeSha) 'previous exe kept in .update\backup-0.1.0'
        Check $case ((Read-Json (Join-Path $d '.update\journal.json')).state -eq 'swapped-unconfirmed') 'journal state swapped-unconfirmed'
        Check $case (@(Get-Process -Name MythologyKombat -ErrorAction SilentlyContinue).Count -eq 0) 'the game was not started'
        Check $case ((Sha (Join-Path $r.data 'run\update.ps1')) -eq (Sha (Join-Path $Updater 'update.ps1'))) 'updater ran from its copy under the data dir'
        Check $case (-not (Test-Path (Join-Path $r.data 'dl-0.2.0')) -and -not (Test-Path (Join-Path $d '.update\stage-0.2.0'))) 'download and stage folders cleaned up'
        $r = Invoke-Updater $d @('-CheckOnly')
        Check $case ($r.code -eq 0 -and $r.out -match 'Up to date' -and $r.out -match 'has not been started') 'second run: up to date, warns the new build never ran'

        $case = '02 rollback'
        Write-Host "[$case]"
        $r = Invoke-Updater $d @('-Rollback')
        Check $case ($r.code -eq 0 -and $r.out -match 'Rolled back to 0\.1\.0') 'Rollback exits 0'
        Check $case ((Get-TreeHash $d) -eq $pre) 'tree byte-identical to before the update (incl. saves and settings)'
        $r = Invoke-Updater $d @('-Rollback')
        Check $case ($r.code -eq 1 -and $r.out -match 'nothing to roll back') 'a second Rollback is refused'
    }

    # ============================================================ confirmation after the game ran
    $case = '03 confirm after run'
    if (Want-Case $case) {
        Write-Host "[$case]"
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
        $d = New-Install 'c03'
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 0) 'update installed'
        (Get-Item (Join-Path $d 'input.ini')).LastWriteTimeUtc = [DateTime]::UtcNow.AddSeconds(5)   # the new build "ran" and wrote a runtime file
        $r = Invoke-Updater $d   # a normal run (already up to date) does the confirmation
        Check $case ($r.out -match 'has run since' -and -not (Test-Path (Join-Path $d '.update\backup-0.1.0'))) 'backup removed once the new build has run'
        $r = Invoke-Updater $d @('-Rollback')
        Check $case ($r.code -eq 1) 'Rollback is no longer possible'
    }

    # ============================================================ bad checksum
    $case = '04 bad checksum'
    if (Want-Case $case) {
        Write-Host "[$case]"
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName (("{0}  {1}`n" -f ('0' * 64), $GoodZipName))
        $d = New-Install 'c04'; $pre = Get-TreeHash $d
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'SHA-256 MISMATCH') 'refused with SHA-256 MISMATCH'
        Check $case ((Get-TreeHash $d) -eq $pre) 'install bit-identical'
        Check $case (-not (Test-Path (Join-Path $d '.update'))) 'nothing written to .update (no stage before verification)'
        Check $case (-not (Test-Path (Join-Path $r.data 'dl-0.2.0'))) 'download folder deleted'
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums @{ digest = ('sha256:' + ('c' * 64)) }
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'API digest') 'API digest different from the download: refused'
        Check $case ((Get-TreeHash $d) -eq $pre -and -not (Test-Path (Join-Path $d '.update'))) 'install bit-identical'
        # checksums.txt without a line for the zip, and with conflicting lines
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName ("{0}  other.zip`n" -f ('a' * 64))
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'no line for') 'checksums.txt without a line for the zip is refused'
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName (($goodSums) + ("{0}  {1}`n" -f ('b' * 64), $GoodZipName))
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'conflicting') 'conflicting checksum lines are refused'
        Check $case ((Get-TreeHash $d) -eq $pre) 'install still bit-identical'
    }

    # ============================================================ truncated zip
    $case = '05 truncated zip'
    if (Want-Case $case) {
        Write-Host "[$case]"
        $bytes = [IO.File]::ReadAllBytes($GoodZip)
        $tz = Join-Path $Dl 'trunc.zip'
        $cut = New-Object byte[] ($bytes.Length - 3000); [Array]::Copy($bytes, $cut, $cut.Length); [IO.File]::WriteAllBytes($tz, $cut)
        $d = New-Install 'c05'; $pre = Get-TreeHash $d
        # (a) the checksum matches the truncated file: the zip itself must be rejected
        Reset-Www; Publish-Release 'v0.2.0' $tz $GoodZipName (Sums $tz $GoodZipName)
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'cannot be read') 'truncated zip with a matching hash: unreadable zip refused'
        Check $case ((Get-TreeHash $d) -eq $pre) 'install bit-identical'
        # (b) the server delivers fewer bytes than the release declares / than checksums.txt covers
        Reset-Www; Publish-Release 'v0.2.0' $tz $GoodZipName $goodSums @{ size = (Get-Item $GoodZip).Length }
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'declares') 'short download (size mismatch) refused'
        Check $case ((Get-TreeHash $d) -eq $pre) 'install bit-identical'
    }

    # ============================================================ hostile zips
    $case = '06 hostile zips'
    if (Want-Case $case) {
        Write-Host "[$case]"
        $d = New-Install 'c06'; $pre = Get-TreeHash $d
        $top = 'MythologyKombat-0.2.0'
        $ok1 = @{ name = "$top/release_info.json"; bytes = [Text.Encoding]::ASCII.GetBytes('{}') }
        $many = @(); for ($i = 0; $i -lt 5100; $i++) { $many += @{ name = "$top/f$i.txt"; bytes = [byte[]]@(65) } }
        $hostile = [ordered]@{
            'dotdot'        = @{ ent = @($ok1, @{ name = "$top/../evil.txt"; bytes = [byte[]]@(1) }); re = 'dot segment' }
            'dotdot-deep'   = @{ ent = @($ok1, @{ name = "$top/a/../../evil.txt"; bytes = [byte[]]@(1) }); re = 'dot segment' }
            'absolute'      = @{ ent = @($ok1, @{ name = "/abs/evil.txt"; bytes = [byte[]]@(1) }); re = 'outside the top folder' }
            'drive'         = @{ ent = @($ok1, @{ name = "C:/x/evil.txt"; bytes = [byte[]]@(1) }); re = 'outside the top folder' }
            'drive-inside'  = @{ ent = @($ok1, @{ name = "$top/C:/evil.txt"; bytes = [byte[]]@(1) }); re = 'forbidden character' }
            'stream'        = @{ ent = @($ok1, @{ name = "$top/a.txt:stream"; bytes = [byte[]]@(1) }); re = 'forbidden character' }
            'backslash'     = @{ ent = @($ok1, @{ name = "$top/..\evil.txt"; bytes = [byte[]]@(1) }); re = 'backslash' }
            'reserved-CON'  = @{ ent = @($ok1, @{ name = "$top/CON"; bytes = [byte[]]@(1) }); re = 'reserved device name' }
            'reserved-nul'  = @{ ent = @($ok1, @{ name = "$top/assets/nul.txt"; bytes = [byte[]]@(1) }); re = 'reserved device name' }
            'trailing-dot'  = @{ ent = @($ok1, @{ name = "$top/evil."; bytes = [byte[]]@(1) }); re = 'ends with dot' }
            'wrong-top'     = @{ ent = @($ok1, @{ name = "Other-0.2.0/x.txt"; bytes = [byte[]]@(1) }); re = 'outside the top folder' }
            'duplicate'     = @{ ent = @($ok1, @{ name = "$top/a.txt"; bytes = [byte[]]@(1) }, @{ name = "$top/A.TXT"; bytes = [byte[]]@(2) }); re = 'duplicate zip entry' }
            'protected'     = @{ ent = @($ok1, @{ name = "$top/saves/card1.mcd"; bytes = [byte[]]@(1) }); re = 'protected player file' }
            'protected-set' = @{ ent = @($ok1, @{ name = "$top/settings.toml"; bytes = [byte[]]@(1) }); re = 'protected player file' }
            'alias-settings' = @{ ent = @($ok1, @{ name = "$top/SETTIN~1.TOM"; bytes = [byte[]]@(1) }); re = 'forbidden character' }
            'alias-game' = @{ ent = @($ok1, @{ name = "$top/GAME~1.TOM"; bytes = [byte[]]@(1) }); re = 'forbidden character' }
            'alias-keybinds' = @{ ent = @($ok1, @{ name = "$top/KEYBIN~1.INI"; bytes = [byte[]]@(1) }); re = 'forbidden character' }
            'alias-captures' = @{ ent = @($ok1, @{ name = "$top/OVERLA~1.JSO"; bytes = [byte[]]@(1) }); re = 'forbidden character' }
            'alias-mods-state' = @{ ent = @($ok1, @{ name = "$top/mods/STATE~1.TOM"; bytes = [byte[]]@(1) }); re = 'forbidden character' }
            'alias-dir' = @{ ent = @($ok1, @{ name = "$top/SAVES~1/x.mcd"; bytes = [byte[]]@(1) }); re = 'forbidden character' }
            'conin' = @{ ent = @($ok1, @{ name = "$top/CONIN$"; bytes = [byte[]]@(1) }); re = 'forbidden character' }
            'conout' = @{ ent = @($ok1, @{ name = "$top/CONOUT$"; bytes = [byte[]]@(1) }); re = 'forbidden character' }
            'clock' = @{ ent = @($ok1, @{ name = "$top/CLOCK$"; bytes = [byte[]]@(1) }); re = 'forbidden character' }
            'protected-space' = @{ ent = @($ok1, @{ name = "$top/settings.toml "; bytes = [byte[]]@(1) }); re = 'ends with dot or space' }
            'no-manifest'   = @{ ent = @($ok1); re = 'no manifest.json' }
            'too-many'      = @{ ent = $many; re = 'too many entries' }
            'oversize'      = @{ ent = @($ok1, @{ name = "$top/big.dat"; zeros = 205 }); re = 'too large' }
        }
        foreach ($k in $hostile.Keys) {
            $hz = Join-Path $Dl ("h-$k.zip")
            New-ZipFromEntries $hz $hostile[$k].ent
            Reset-Www; Publish-Release 'v0.2.0' $hz $GoodZipName (Sums $hz $GoodZipName)
            $r = Invoke-Updater $d
            $okc = ($r.code -eq 1 -and $r.out -match $hostile[$k].re)
            Check $case $okc ("zip '{0}' refused ({1})" -f $k, $hostile[$k].re)
            if (-not $okc) { Write-Host (Show-Out $r) }
            Remove-Item -LiteralPath $hz -Force
        }
        Check $case ((Get-TreeHash $d) -eq $pre) 'install bit-identical after all hostile zips'
        $evil = @(Get-ChildItem -LiteralPath $W -Recurse -Force -File -Filter 'evil*' -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike "$Dl*" })
        Check $case ($evil.Count -eq 0) 'no evil* file written anywhere under the test area'
        Check $case (-not (Test-Path (Join-Path $d '.update'))) 'no stage or journal left in the install'
        # a symlink entry
        $lnk = Join-Path $Dl 'h-link.zip'
        $fs = [IO.File]::Open($lnk, [IO.FileMode]::Create); $za = New-Object IO.Compression.ZipArchive($fs, [IO.Compression.ZipArchiveMode]::Create)
        $en = $za.CreateEntry("$top/link.txt"); $en.ExternalAttributes = (0xA1FF -shl 16)
        $es = $en.Open(); $es.WriteByte(65); $es.Dispose(); $za.Dispose(); $fs.Dispose()
        Reset-Www; Publish-Release 'v0.2.0' $lnk $GoodZipName (Sums $lnk $GoodZipName)
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'symbolic link') 'symlink entry refused'
        Remove-Item $lnk -Force
        # manifest mismatch: a valid-looking zip whose file differs from manifest.json
        $tamper = Join-Path $W 'tamper'; Rmrf $tamper; Copy-Tree $NewDir $tamper
        Add-Content -LiteralPath (Join-Path $tamper 'LICENSE') -Value 'tampered' -Encoding ASCII
        $tz = Join-Path $Dl 'tamper.zip'; New-ZipFromDir $tamper $top $tz
        Reset-Www; Publish-Release 'v0.2.0' $tz $GoodZipName (Sums $tz $GoodZipName)
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'differs from manifest') 'file not matching manifest.json refused'
        Check $case ((Get-TreeHash $d) -eq $pre) 'install bit-identical'
        Check $case (-not (Test-Path (Join-Path $d '.update\stage-0.2.0'))) 'stage removed after the refusal'
        Rmrf $tamper; Remove-Item $tz -Force
    }

    # ============================================================ downgrade, equal, odd tags
    $case = '07 downgrade and odd tags'
    if (Want-Case $case) {
        Write-Host "[$case]"
        $d = New-Install 'c07'; $pre = Get-TreeHash $d
        $tiny = Join-Path $Dl 'tiny.zip'; New-ZipFromEntries $tiny @(@{ name = 'x/y.txt'; bytes = [byte[]]@(1) })
        foreach ($t in @('v0.1.0', 'v0.0.9', 'v0.1.0')) {
            Reset-Www; Publish-Release $t $tiny "MythologyKombat-$($t.TrimStart('v'))-Windows-x64.zip" 'x'
            $r = Invoke-Updater $d
            Check $case ($r.code -eq 0 -and $r.out -match 'Up to date') "tag $t is not newer: up to date"
        }
        foreach ($t in @('0.3.0', 'v0.3.0-beta', 'v1.2', 'v0.3.0.1', 'vv0.3.0')) {
            Reset-Www; Publish-Release $t $tiny 'x.zip' 'x'
            $r = Invoke-Updater $d
            Check $case ($r.code -eq 1 -and $r.out -match 'is not vX\.Y\.Z') "tag '$t' refused"
        }
        $odds = @(@{ n = 'trailing newline'; t = "v0.3.0`n" }, @{ n = 'arabic-indic digit'; t = ('v0.3.' + [char]0x0663) }, @{ n = 'fullwidth digit'; t = ('v0.3.' + [char]0xFF10) }, @{ n = 'leading space'; t = ' v0.3.0' })
        foreach ($odd in $odds) {
            Reset-Www; Publish-Release 'v0.3.0' $tiny 'MythologyKombat-0.3.0-Windows-x64.zip' 'x' @{ tag_name = $odd.t }
            $r = Invoke-Updater $d
            Check $case ($r.code -eq 1 -and $r.out -match 'is not vX\.Y\.Z') ("tag with " + $odd.n + " refused")
        }
        Reset-Www; Publish-Release 'v0.3.0' $tiny 'x.zip' 'x' @{ prerelease = $true }
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'draft or prerelease') 'prerelease refused'
        Reset-Www; Publish-Release 'v0.3.0' $tiny 'MythologyKombat-0.3.0-Windows-x64.zip' 'x' @{ draft = $true }
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'draft or prerelease') 'draft refused'
        Check $case ((Get-TreeHash $d) -eq $pre) 'install bit-identical'
        $zipGets = @(if (Test-Path $ReqLog) { Get-Content $ReqLog | Where-Object { $_ -like 'GET*.zip *' } }).Count
        Check $case ($zipGets -eq 0) 'no zip was ever requested'
        # asset URL not matching the expected pattern
        Reset-Www; Publish-Release 'v0.3.0' $tiny 'MythologyKombat-0.3.0-Windows-x64.zip' 'x'
        $lj = Join-Path $Www ("repos\$Repo\releases\latest".Replace('/', '\'))
        $t = [IO.File]::ReadAllText($lj).Replace("$BaseUrl/$Repo/releases/download/v0.3.0/MythologyKombat", 'https://evil.example.org/MythologyKombat')
        [IO.File]::WriteAllText($lj, $t)
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'asset URLs do not match') 'asset URL pointing elsewhere refused'
    }

    # ============================================================ wrong-host redirects
    $case = '08 redirects'
    if (Want-Case $case) {
        Write-Host "[$case]"
        $d = New-Install 'c08'; $pre = Get-TreeHash $d
        $zp = "/$Repo/releases/download/v0.2.0/$GoodZipName"
        $cases = @(
            @{ n = 'other host (https)'; loc = 'https://evil.example.org/x.zip'; re = 'allow-list' },
            @{ n = 'http downgrade to github.com'; loc = 'http://github.com/x.zip'; re = 'non-https' },
            @{ n = 'lookalike host'; loc = 'https://github.com.evil.example.org/x.zip'; re = 'allow-list' },
            @{ n = 'lookalike suffix'; loc = 'https://evilgithubusercontent.com/x.zip'; re = 'allow-list' },
            @{ n = 'userinfo trick'; loc = 'https://github.com@evil.example.org/x.zip'; re = 'credentials' },
            @{ n = 'non-default port'; loc = 'https://github.com:8443/x.zip'; re = 'non-default port' },
            @{ n = 'file scheme'; loc = 'file:///C:/Windows/win.ini'; re = 'non-https' },
            @{ n = 'other repo on this server'; loc = "$BaseUrl/other/evilrepo/releases/download/v0.2.0/$GoodZipName"; re = 'refused path outside' },
            @{ n = 'other repo on github.com'; loc = "https://github.com/other/evilrepo/releases/download/v0.2.0/$GoodZipName"; re = 'refused path outside' },
            @{ n = 'same repo, other tag'; loc = "https://github.com/$Repo/releases/download/v9.9.9/$GoodZipName"; re = 'refused path outside' },
            @{ n = 'generic githubusercontent host'; loc = 'https://raw.githubusercontent.com/other/x/main/x.zip'; re = 'allow-list' },
            @{ n = 'api host for a download'; loc = 'https://api.github.com/repos/other/x/zipball'; re = 'allow-list' },
            @{ n = 'percent-encoded dot segments (server)'; loc = "$BaseUrl/$Repo/releases/download/v0.2.0/%2e%2e/%2e%2e/other/evilrepo/x.zip"; re = 'percent escape' },
            @{ n = 'percent-encoded dot segments (github.com)'; loc = "https://github.com/$Repo/releases/download/v0.2.0/%2E%2E/%2E%2E/other/evilrepo/x.zip"; re = 'percent escape' },
            @{ n = 'encoded slash'; loc = "https://github.com/$Repo/releases/download/v0.2.0%2f..%2f..%2fother/x.zip"; re = 'percent escape' },
            @{ n = 'redirect loop'; loc = "$BaseUrl$zp"; re = 'more than 5 redirects' }
        )
        foreach ($c in $cases) {
            Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
            Set-Route $zp 302 @{ Location = $c.loc }
            $r = Invoke-Updater $d
            Check $case ($r.code -eq 1 -and $r.out -match $c.re) ("zip redirect: " + $c.n + ' refused')
        }
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
        Set-Route "/$Repo/releases/download/v0.2.0/checksums.txt" 302 @{ Location = 'https://evil.example.org/checksums.txt' }
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'allow-list') 'checksums.txt redirect to another host refused'
        foreach ($loc in @("$BaseUrl/other/evilrepo/releases/download/v0.2.0/checksums.txt", 'https://github.com/other/evilrepo/releases/download/v0.2.0/checksums.txt', "$BaseUrl/$Repo/releases/download/v0.2.0/%2e%2e/%2e%2e/other/x/checksums.txt")) {
            Set-Route "/$Repo/releases/download/v0.2.0/checksums.txt" 302 @{ Location = $loc }
            $r = Invoke-Updater $d
            Check $case ($r.code -eq 1 -and $r.out -match 'refused path outside|percent escape') ("checksums.txt redirect to another repo refused: " + $loc.Substring(0, 30))
        }
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
        Set-Route "/repos/$Repo/releases/latest" 302 @{ Location = "$BaseUrl/repos/other/evilrepo/releases/latest" }
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'refused path outside|refused API path') 'API call redirected to another repo refused'
        Set-Route "/repos/$Repo/releases/latest" 302 @{ Location = "$BaseUrl/repos/$Repo/%2e%2e/%2e%2e/repos/other/evilrepo/releases/latest" }
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'percent escape') 'API redirect with %2e%2e refused'
        Set-Route "/repos/$Repo/releases/latest" 302 @{ Location = 'https://github.com/PAumedes/MythologyKombat/releases/latest' }
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'allow-list') 'API call redirected to github.com (not an API host) refused'
        Check $case ((Get-TreeHash $d) -eq $pre -and -not (Test-Path (Join-Path $d '.update'))) 'install bit-identical'
        # a legitimate same-server redirect chain (2 hops) works
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
        New-Item -ItemType Directory -Force -Path (Join-Path $Www 'cdn') | Out-Null
        Copy-Item $GoodZip (Join-Path $Www "cdn\$GoodZipName")
        $q1 = 'sp=r&sv=2018-11-09&sr=b&spr=https&se=2026-10-21T15%3A54%3A19Z&rscd=attachment%3B+filename%3DSECRETNAME.zip&rsct=application%2Foctet-stream&sig=SECRETSIG%2Bab%2Fcd%3D&jwt=SECRETJWT&response-content-disposition=attachment%3B%20filename%3DSECRETNAME.zip'
        Set-Route $zp 302 @{ Location = "$BaseUrl/cdn/a/${GoodZipName}?$q1" }
        Set-Route "/cdn/a/$GoodZipName" 302 @{ Location = "$BaseUrl/cdn/${GoodZipName}?$q1" }
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 0 -and $r.out -match 'Updated to') 'a 2-hop redirect with a signed, %-encoded query (%3A %3B %3D %2F %20 %2B) installs'
        Check $case ($r.out -notmatch 'SECRET|sig=|jwt=|%3D|sv=2018') 'the query string is not echoed anywhere in the output'
        $qlog = @(if (Test-Path $ReqLog) { Get-Content $ReqLog | Where-Object { $_ -like '*sig=SECRETSIG%2Bab%2Fcd%3D*' } }).Count
        Check $case ($qlog -ge 1) 'the query reached the server byte for byte (not re-encoded)'
        # refusals must not echo the query either
        $d2 = New-Install 'c08q'
        foreach ($qc in @(
                @{ n = 'other host with a signed query'; loc = 'https://evil.example.org/x.zip?sig=SECRETSIG%3D&jwt=SECRETJWT'; re = 'allow-list' },
                @{ n = 'http with a signed query'; loc = 'http://github.com/x.zip?sig=SECRETSIG%3D'; re = 'non-https' },
                @{ n = '%2e%2e path with a query'; loc = "$BaseUrl/$Repo/releases/download/v0.2.0/%2e%2e/%2e%2e/other/x.zip?sig=SECRETSIG%3D"; re = 'percent escape' },
                @{ n = '%2f path with a query (github.com)'; loc = "https://github.com/$Repo/releases/download/v0.2.0%2f..%2fx.zip?sig=SECRETSIG%3D"; re = 'percent escape' },
                @{ n = '%5c path'; loc = "$BaseUrl/$Repo/releases/download/v0.2.0/..%5cx.zip"; re = 'percent escape' },
                @{ n = 'other repo with a query'; loc = "https://github.com/other/evilrepo/releases/download/v0.2.0/x.zip?sig=SECRETSIG%3D"; re = 'refused path outside' })) {
            Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
            Set-Route $zp 302 @{ Location = $qc.loc }
            $r = Invoke-Updater $d2
            Check $case ($r.code -eq 1 -and $r.out -match $qc.re -and $r.out -notmatch 'SECRET') ("refused and query not echoed: " + $qc.n)
            Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
            Set-Route "/$Repo/releases/download/v0.2.0/checksums.txt" 302 @{ Location = $qc.loc }
            $r = Invoke-Updater $d2
            Check $case ($r.code -eq 1 -and $r.out -match $qc.re -and $r.out -notmatch 'SECRET') ("checksums.txt, refused and query not echoed: " + $qc.n)
        }
    }

    # ============================================================ game running
    $case = '09 game running'
    if (Want-Case $case) {
        Write-Host "[$case]"
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
        $d = New-Install 'c09'
        Copy-Item -LiteralPath (Join-Path $env:SystemRoot 'System32\PING.EXE') -Destination (Join-Path $d 'MythologyKombat.exe') -Force
        $pre = Get-TreeHash $d
        $gp = Start-Process -FilePath (Join-Path $d 'MythologyKombat.exe') -ArgumentList @('-n', '60', '127.0.0.1') -PassThru -WindowStyle Hidden
        try {
            Start-Sleep -Seconds 1
            $r = Invoke-Updater $d
            Check $case ($r.code -eq 1 -and $r.out -match 'is running') 'refused while the game exe runs from this folder'
            Check $case ((Get-TreeHash $d) -eq $pre -and -not (Test-Path (Join-Path $d '.update'))) 'nothing changed'
            $r = Invoke-Updater $d @('-Rollback')
            Check $case ($r.code -eq 1) '-Rollback also refused while running'
        } finally { Stop-Process -Id $gp.Id -Force -ErrorAction SilentlyContinue; Start-Sleep -Milliseconds 500 }
        $r = Invoke-Updater $d @('-CheckOnly')
        Check $case ($r.code -eq 0 -and $r.out -match 'Newer version') 'CheckOnly is allowed while it runs (no files touched)'
    }

    # ============================================================ crash during the swap
    $case = '10 crash during swap'
    if (Want-Case $case) {
        Write-Host "[$case]"
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
        $d = New-Install 'c10a'; $pre = Get-TreeHash $d; $prePlayer = Get-PlayerHash $d
        $r = Invoke-Updater $d @('-TestCrashAfter', '3', '-TestCrashMode', 'throw')
        Check $case ($r.code -eq 1 -and $r.out -match 'rolled back') 'failure mid-swap is rolled back automatically'
        Check $case ((Get-TreeHash $d) -eq $pre) 'install bit-identical after the automatic rollback'
        $d = New-Install 'c10b'; $pre = Get-TreeHash $d; $prePlayerB = Get-PlayerHash $d
        $r = Invoke-Updater $d @('-TestCrashAfter', '3', '-TestCrashMode', 'kill')
        Check $case ($r.code -eq 99) 'updater hard-killed mid-swap (exit 99)'
        Check $case ((Read-Json (Join-Path $d '.update\journal.json')).state -eq 'swapping') 'journal says swapping'
        Check $case ((Get-TreeHash $d) -ne $pre) 'install is in a half-updated state (precondition)'
        $r = Invoke-Updater $d @('-CheckOnly')
        Check $case ($r.code -eq 0 -and $r.out -match 'NOTE: an earlier update' -and (Get-TreeHash $d) -ne $pre) '-CheckOnly reports the interrupted update and moves nothing'
        $r = Invoke-Updater $d @('-Rollback')
        Check $case ($r.out -match 'interrupted' -and $r.out -match 'Restored') 'next run detects the interrupted update and restores'
        Check $case ((Get-TreeHash $d) -eq $pre) 'install bit-identical after recovery'
        Check $case ((Get-PlayerHash $d) -eq $prePlayerB -and (Read-Json (Join-Path $d '.update\journal.json')).state -eq 'rolled-back') 'journal says rolled-back'
        # after recovery a normal update works
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 0 -and $r.out -match 'Updated to 0\.2\.0') 'a normal update succeeds after recovery'
        Check $case ((Sha (Join-Path $d 'MythologyKombat.exe')) -eq $NewExeSha) 'new exe in place'
    }

    $case = '10b corrupt journal and failed rollback'
    if (Want-Case $case) {
        Write-Host "[$case]"
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
        $d = New-Install 'c10c'; $pre = Get-TreeHash $d
        $r = Invoke-Updater $d @('-TestCrashAfter', '3', '-TestCrashMode', 'kill')
        $jp = Join-Path $d '.update\journal.json'
        $half = Get-TreeHash $d
        $goodJournal = [IO.File]::ReadAllBytes($jp)
        Check $case ($r.code -eq 99 -and -not (Test-Path ($jp + '.tmp'))) 'killed mid-swap; no leftover journal.json.tmp'
        $jtext = [Text.Encoding]::UTF8.GetString($goodJournal)
        $variants = @(
            @{ n = 'truncated'; b = $goodJournal[0..([int]($goodJournal.Length / 2))] },
            @{ n = 'empty'; b = [byte[]]@() },
            @{ n = 'whitespace only'; b = [Text.Encoding]::ASCII.GetBytes("  `r`n") },
            @{ n = 'not json'; b = [Text.Encoding]::ASCII.GetBytes('garbage') },
            @{ n = 'plan with a protected file'; b = [Text.Encoding]::UTF8.GetBytes(($jtext -replace '"rel":\s+"README_FIRST.txt"', '"rel":  "settings.toml"')) },
            @{ n = 'negative timestamp'; b = [Text.Encoding]::UTF8.GetBytes(($jtext -replace '"swapped_ticks":\s+0', '"swapped_ticks":  -5')) },
            @{ n = 'text timestamp'; b = [Text.Encoding]::UTF8.GetBytes(($jtext -replace '"swapped_ticks":\s+0', '"swapped_ticks":  "soon"')) },
            @{ n = 'plan with ..'; b = [Text.Encoding]::UTF8.GetBytes(($jtext -replace '"rel":\s+"README_FIRST.txt"', '"rel":  "../evil.txt"')) })
        Check $case ($jtext -match '"rel":\s+"README_FIRST.txt"') 'precondition: journal lists README_FIRST.txt'
        foreach ($v in $variants) {
            [IO.File]::WriteAllBytes($jp, [byte[]]$v.b)
            $r = Invoke-Updater $d
            Check $case ($r.code -eq 1 -and $r.out -match 'journal\.json is corrupt') ("corrupt journal (" + $v.n + ") refused with recovery instructions")
            Check $case ((Get-TreeHash $d) -eq $half) ("install untouched (" + $v.n + ")")
            $r = Invoke-Updater $d @('-CheckOnly')
            Check $case ($r.code -eq 0 -and $r.out -match 'WARNING: journal\.json is corrupt' -and $r.out -match 'Newer version') ("-CheckOnly still works with a corrupt journal (" + $v.n + ")")
            $r = Invoke-Updater $d @('-Rollback')
            Check $case ($r.code -eq 1 -and $r.out -match 'journal\.json is corrupt') ("-Rollback refused with a corrupt journal (" + $v.n + ")")
        }
        Check $case (-not (Test-Path (Join-Path $W 'evil.txt')) -and -not (Test-Path (Join-Path $d '..\evil.txt'))) 'the tampered plan wrote nothing'
        [IO.File]::WriteAllBytes($jp, $goodJournal)
        $r = Invoke-Updater $d @('-Rollback')
        Check $case ($r.out -match 'Restored' -and (Get-TreeHash $d) -eq $pre) 'valid journal: recovery restores the install bit-identical'
        # backup file missing: rollback fails loudly with manual steps, keeps what is left, and is RETRIED once the cause is fixed
        $d = New-Install 'c10d'; $pre = Get-TreeHash $d
        $r = Invoke-Updater $d @('-TestCrashAfter', '3', '-TestCrashMode', 'kill')
        $bkf = Join-Path $d '.update\backup-0.1.0\README_FIRST.txt'
        $bkSaved = Join-Path $W 'README_FIRST.saved'; Copy-Item -LiteralPath $bkf -Destination $bkSaved -Force
        Remove-Item -LiteralPath $bkf -Force
        $r = Invoke-Updater $d @('-Rollback')
        Check $case ($r.code -eq 1 -and $r.out -match 'ROLLBACK INCOMPLETE' -and $r.out -match 'README_FIRST\.txt: the backup is missing') 'missing backup file: rollback reports failure for that file'
        Check $case ($r.out -match 'finish by hand' -and $r.out -match 'copy everything from' -and $r.out -match 'then delete the folder') 'manual recovery steps are printed'
        Check $case ((Test-Path (Join-Path $d '.update\backup-0.1.0')) -and (Read-Json (Join-Path $d '.update\journal.json')).state -eq 'rollback-failed') 'backup folder kept, journal says rollback-failed'
        $r = Invoke-Updater $d @('-Rollback')
        Check $case ($r.code -eq 1 -and $r.out -match 'Retrying' -and $r.out -match 'finish by hand') 'a second run retries, still fails, and prints the manual steps again (no dead end)'
        $r = Invoke-Updater $d @('-CheckOnly')
        Check $case ($r.code -eq 0 -and $r.out -match 'NOTE: an earlier update' -and (Read-Json (Join-Path $d '.update\journal.json')).state -eq 'rollback-failed') '-CheckOnly only reports it'
        Copy-Item -LiteralPath $bkSaved -Destination $bkf -Force   # fix the cause
        $r = Invoke-Updater $d @('-Rollback')
        Check $case ($r.out -match 'Retrying' -and $r.out -match 'Restored') 'after the cause is fixed the retry succeeds'
        Check $case ((Get-TreeHash $d) -eq $pre -and (Read-Json (Join-Path $d '.update\journal.json')).state -eq 'rolled-back' -and -not (Test-Path (Join-Path $d '.update\backup-0.1.0'))) 'install bit-identical, state cleared to rolled-back, backup removed'
        # the same retry through -Rollback
        $d = New-Install 'c10e'; $pre = Get-TreeHash $d
        $r = Invoke-Updater $d @('-TestCrashAfter', '3', '-TestCrashMode', 'kill')
        $bkf = Join-Path $d '.update\backup-0.1.0\README_FIRST.txt'; Copy-Item -LiteralPath $bkf -Destination $bkSaved -Force; Remove-Item -LiteralPath $bkf -Force
        $r = Invoke-Updater $d @('-Rollback')
        Check $case ($r.code -eq 1 -and $r.out -match 'ROLLBACK INCOMPLETE') '-Rollback on an interrupted update with a missing backup fails with the steps'
        Copy-Item -LiteralPath $bkSaved -Destination $bkf -Force
        $r = Invoke-Updater $d @('-Rollback')
        Check $case ($r.code -eq 0 -and $r.out -match 'Restored' -and (Get-TreeHash $d) -eq $pre) '-Rollback retries and succeeds after the fix'
        $r = Invoke-Updater $d @('-Rollback', '-CheckOnly')
        Check $case ($r.code -eq 1 -and $r.out -match 'cannot be combined') '-Rollback with -CheckOnly is refused'
    }

    $case = '10c check-only never modifies'
    if (Want-Case $case) {
        Write-Host "[$case]"
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
        $d = New-Install 'c10f'
        Copy-Item -LiteralPath (Join-Path $env:SystemRoot 'System32\PING.EXE') -Destination (Join-Path $d 'MythologyKombat.exe') -Force
        $r = Invoke-Updater $d @('-TestCrashAfter', '3', '-TestCrashMode', 'kill')
        Check $case ($r.code -eq 99) 'interrupted update prepared (hard kill)'
        $all = Get-TreeHash $d -All
        $gp = Start-Process -FilePath (Join-Path $d 'MythologyKombat.exe') -ArgumentList @('-n', '60', '127.0.0.1') -PassThru -WindowStyle Hidden
        try {
            Start-Sleep -Seconds 1
            $r = Invoke-Updater $d @('-CheckOnly')
            Check $case ($r.code -eq 0 -and $r.out -match 'NOTE: an earlier update' -and $r.out -match 'changes nothing') '-CheckOnly with the game running: reports, exit 0'
            Check $case ((Get-TreeHash $d -All) -eq $all) 'no file anywhere (install or .update) was moved or rewritten'
            $r = Invoke-Updater $d @('-DryRun')
            Check $case ($r.code -eq 1 -and $r.out -match 'is running') 'a normal run is refused while the game runs'
            Check $case ((Get-TreeHash $d -All) -eq $all) 'still nothing changed'
        } finally { Stop-Process -Id $gp.Id -Force -ErrorAction SilentlyContinue; Start-Sleep -Milliseconds 500 }
    }

    $case = '10d concurrent updaters'
    if (Want-Case $case) {
        Write-Host "[$case]"
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
        $d = New-Install 'c10g'; $pre = Get-TreeHash $d
        $dataA = Join-Path $Data 'holdA'
        $holdArgs = @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $d 'update.ps1'), '-TestBaseUrl', $BaseUrl, '-TestDataDir', $dataA, '-Yes', '-TestHoldSeconds', '25')
        $pa = Start-Process -FilePath 'powershell.exe' -ArgumentList $holdArgs -PassThru -WindowStyle Hidden
        try {
            Start-Sleep -Seconds 6
            $r = Invoke-Updater $d
            Check $case ($r.code -eq 1 -and $r.out -match 'another updater is already running') 'a second updater on the same folder is refused while the first holds the lock'
            Check $case ((Get-TreeHash $d) -eq $pre -and -not (Test-Path (Join-Path $d ".update"))) 'the refused instance changed nothing'
            $other = New-Install 'c10h'
            $r = Invoke-Updater $other @('-CheckOnly')
            Check $case ($r.code -eq 0 -and $r.out -match 'Newer version') 'an updater on a different folder is not blocked'
        } finally { Stop-Process -Id $pa.Id -Force -ErrorAction SilentlyContinue; Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.CommandLine -like '*holdA*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } }
        Start-Sleep -Seconds 1
        $r = Invoke-Updater $d @('-CheckOnly')
        Check $case ($r.code -eq 0 -and $r.out -match 'Newer version') 'after the holder is killed the lock is free again (abandoned mutex handled)'
    }

    $case = '10e read-only modes'
    if (Want-Case $case) {
        Write-Host "[$case]"
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
        # (a) swapped-unconfirmed journal, the new build "ran" (newer settings.toml)
        $d = New-Install 'c10i'
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 0) 'update installed (state swapped-unconfirmed)'
        (Get-Item (Join-Path $d 'settings.toml')).LastWriteTimeUtc = [DateTime]::UtcNow.AddSeconds(10)
        $st = Get-FullState $d
        $r = Invoke-Updater $d @('-CheckOnly')
        Check $case ($r.code -eq 0 -and $r.out -match 'will remove the old backup') '-CheckOnly: reports that the backup would be removed'
        Check $case ((Get-FullState $d) -eq $st) '-CheckOnly: every file, mtime and directory (incl. .update) unchanged'
        Check $case ((Test-Path (Join-Path $d '.update\backup-0.1.0')) -and (Read-Json (Join-Path $d '.update\journal.json')).state -eq 'swapped-unconfirmed') '-CheckOnly: backup kept, journal not rewritten'
        # a newer release (0.3.0) is announced, so -DryRun really downloads and stages
        $t3 = Join-Path $W 'new3\MythologyKombat-0.3.0'; Rmrf (Join-Path $W 'new3'); Copy-Tree $NewDir $t3
        Add-Content -LiteralPath (Join-Path $t3 'README_FIRST.txt') -Value 'v0.3.0 note' -Encoding ASCII
        Set-ReleaseInfo $t3 '0.3.0' $Repo; New-Manifest $t3 '0.3.0'
        $z3Name = 'MythologyKombat-0.3.0-Windows-x64.zip'; $z3 = Join-Path $Dl $z3Name
        New-ZipFromDir $t3 'MythologyKombat-0.3.0' $z3
        Reset-Www; Publish-Release 'v0.3.0' $z3 $z3Name (Sums $z3 $z3Name)
        $r = Invoke-Updater $d @('-DryRun')
        Check $case ($r.out -match 'will remove the old backup' -and $r.out -match 'SHA-256 verified' -and $r.out -notmatch 'removing the old backup') '-DryRun: downloads and stages 0.3.0 but does not confirm'
        Check $case ((Get-FullState $d) -eq $st) '-DryRun: everything unchanged (stage removed again)'
        # (b) a fresh install: no .update, no stray probe file, no empty folders left
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
        $d = New-Install 'c10j'; $st = Get-FullState $d
        $r = Invoke-Updater $d @('-CheckOnly')
        Check $case ($r.code -eq 0 -and (Get-FullState $d) -eq $st -and -not (Test-Path (Join-Path $d '.update'))) '-CheckOnly on a fresh install creates nothing (no .update, no probe file)'
        $r = Invoke-Updater $d @('-DryRun')
        Check $case ($r.code -eq 0 -and $r.out -match 'Dry run' -and (Get-FullState $d) -eq $st -and -not (Test-Path (Join-Path $d '.update'))) '-DryRun on a fresh install leaves no .update folder behind'
        # (c) interrupted update: DryRun reports, changes nothing
        $d = New-Install 'c10k'
        $r = Invoke-Updater $d @('-TestCrashAfter', '3', '-TestCrashMode', 'kill')
        $st = Get-FullState $d
        $r = Invoke-Updater $d @('-DryRun')
        Check $case ($r.code -eq 0 -and $r.out -match 'NOTE: an earlier update' -and $r.out -match 'changes nothing') '-DryRun with an interrupted journal: reports only'
        Check $case ((Get-FullState $d) -eq $st -and (Read-Json (Join-Path $d '.update\journal.json')).state -eq 'swapping') '-DryRun did not recover or rewrite the journal'
    }

    # ============================================================ conffile rule
    $case = '11 game.toml conffile rule'
    if (Want-Case $case) {
        Write-Host "[$case]"
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
        $d = New-Install 'c11'
        Add-Content -LiteralPath (Join-Path $d 'game.toml') -Value 'multitap_analog = true  # player/launcher edit' -Encoding ASCII
        $edited = Sha (Join-Path $d 'game.toml')
        $pre = Get-TreeHash $d
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 0 -and $r.out -match 'WARNING: game\.toml') 'update succeeds and warns about game.toml'
        Check $case ((Sha (Join-Path $d 'game.toml')) -eq $edited) "player's modified game.toml kept byte-identical"
        Check $case ((Sha (Join-Path $d 'game.toml.new')) -eq (Sha (Join-Path $NewDir 'game.toml'))) 'new game.toml saved as game.toml.new'
        Check $case ((Sha (Join-Path $d 'game_options.toml')) -eq (Sha (Join-Path $NewDir 'game_options.toml'))) 'unmodified game_options.toml replaced'
        $r = Invoke-Updater $d @('-Rollback')
        Check $case ($r.code -eq 0 -and (Get-TreeHash $d) -eq $pre) 'rollback restores everything and removes game.toml.new'
        # unmodified game.toml is replaced (covered by case 01); a second update after the .new exists replaces the .new
    }

    # ============================================================ rate limit fallback
    $case = '12 rate limit fallback'
    if (Want-Case $case) {
        Write-Host "[$case]"
        foreach ($status in @(403, 429)) {
            Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
            Set-Route "/repos/$Repo/releases/latest" $status @{ 'X-RateLimit-Remaining' = '0' }
            Set-Route "/$Repo/releases/latest/download/checksums.txt" 302 @{ Location = "$BaseUrl/$Repo/releases/download/v0.2.0/checksums.txt" }
            $d = New-Install "c12-$status"
            $r = Invoke-Updater $d
            Check $case ($r.code -eq 0 -and $r.out -match 'rate limit' -and $r.out -match 'Updated to 0\.2\.0') "API ${status}: fallback finds the tag and installs"
            Check $case ((Sha (Join-Path $d 'MythologyKombat.exe')) -eq $NewExeSha) 'new exe in place'
        }
        # fallback pointing at a non-version tag, or at another repo
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
        Set-Route "/repos/$Repo/releases/latest" 403 @{ 'X-RateLimit-Remaining' = '0' }
        Set-Route "/$Repo/releases/latest/download/checksums.txt" 302 @{ Location = "$BaseUrl/other/repo/releases/download/v9.9.9/checksums.txt" }
        $d = New-Install 'c12-x'; $pre = Get-TreeHash $d
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'did not name|refused path outside') 'fallback redirect naming another repo refused'
        Set-Route "/$Repo/releases/latest/download/checksums.txt" 302 @{ Location = 'https://evil.example.org/x' }
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'allow-list') 'fallback redirect to another host refused'
        # 500 and 404: friendly message, no stack trace
        Set-Route "/repos/$Repo/releases/latest" 500 @{}
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'HTTP 500' -and $r.out -notmatch 'at <ScriptBlock>') 'HTTP 500: friendly error, no stack trace'
        Check $case ((Get-TreeHash $d) -eq $pre) 'install bit-identical'
    }

    # ============================================================ repo / mode guards
    $case = '13 guards'
    if (Want-Case $case) {
        Write-Host "[$case]"
        Reset-Www; Publish-Release 'v0.2.0' $GoodZip $GoodZipName $goodSums
        $d = New-Install 'c13'; $pre = Get-TreeHash $d
        $ri = Join-Path $d 'release_info.json'
        $j = Read-Json $ri; $j.repo = 'someone/else'; Write-Utf8 $ri ($j | ConvertTo-Json -Depth 6)
        $pre2 = Get-TreeHash $d
        $r = Invoke-Updater $d
        Check $case ($r.code -eq 1 -and $r.out -match 'built for PAumedes/MythologyKombat') 'release_info.json repo different from the updater constant: refused'
        Check $case ((Get-TreeHash $d) -eq $pre2) 'install unchanged'
        $r = Invoke-Updater $d @('-Yes') $false
        Check $case ($r.code -eq 1 -and $r.out -match 'only in test mode') '-Yes without test mode refused'
        $r = Invoke-Updater $d @('-TestBaseUrl', 'http://example.com') $false
        Check $case ($r.code -eq 1 -and $r.out -match 'must be http://127\.0\.0\.1') '-TestBaseUrl with a remote host refused'
        $r = Invoke-Updater $d @('-TestBaseUrl', 'https://127.0.0.1:5000') $false
        Check $case ($r.code -eq 1) '-TestBaseUrl with https refused'
        $dd = New-Install 'c13c'; $preD = Get-TreeHash $dd; $r = Invoke-Updater $dd @('-TestFreeBytes', '1000')
        Check $case ($r.code -eq 1 -and $r.out -match 'not enough free disk space') 'low free disk space refused before anything is downloaded'
        Check $case ((Get-TreeHash $dd) -eq $preD) 'install unchanged'
        $e = Join-Path $W 'notgame'; New-Item -ItemType Directory -Force -Path $e | Out-Null
        Copy-Item (Join-Path $Updater 'update.ps1') $e
        $r = Invoke-Updater $e
        Check $case ($r.code -eq 1 -and $r.out -match 'not a MythologyKombat folder') 'a folder without the exe is refused'
        # cancelled prompt: answer n through stdin is not possible non-interactively -> prompt failure counts as no
        $r = Invoke-Updater (New-Install 'c13b') @() $true $false
        Check $case ($r.code -eq 0 -and $r.out -match 'Cancelled') 'without -Yes and without a typed answer nothing is installed'
    }
}
finally {
    if ($srv -and -not $srv.HasExited) { Stop-Process -Id $srv.Id -Force -ErrorAction SilentlyContinue }
}

Write-Host ''
$pass = @($results | Where-Object { $_.ok }).Count
Write-Host ("updater tests: {0} checks, {1} passed, {2} failed" -f $results.Count, $pass, $script:failed)
if ($script:failed -gt 0) { exit 1 }
exit 0
