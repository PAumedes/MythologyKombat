<#
.SYNOPSIS
  Local release builder (T3.19, D25): clean checkout -> game build from the user's disc -> allow-listed zip.

.DESCRIPTION
  Run by hand at release time on the PC that holds the disc. Not a pre-commit step. Windows PowerShell 5.1.

  1. Clones this repo (never the dirty working tree) at -Ref into work\release\<Version>\src with
     recursive submodules, and stops if the clone is dirty or the submodules differ from framework_pins.txt.
  2. Applies patches\launcher through the clone's own tools\apply_launcher_patches.ps1 (D19) and points the
     build at the patched copy (-DRECOMP_UI_ROOT).
  3. Runs, through the clone's tools\run_psxrecomp.ps1: verify-disc, generate, ensure-toolchain, rebuild
     (Release, no PGO unless -Pgo, -DPSX_PUBLIC_RELEASE=ON so playtest recording is off by default).
  4. Assembles the release folder from an ALLOW-LIST (never "copy the build dir and subtract").
  5. Runs tools\check_release_content.py on the folder and on the zip; any violation stops the script.
  6. Writes MythologyKombat-<Version>-Windows-x64.zip (deterministic: sorted entries, fixed timestamps)
     and checksums.txt (SHA-256), plus release_notes.md, under work\release\<Version>\.
  7. Nothing is uploaded. With -Draft the exact `gh release create ... --draft` command is printed and runs
     ONLY after you type UPLOAD at an interactive prompt (never in a non-interactive session).
     -Publish is not implemented in this task.

  The disc path is only ever passed to the CLI as an argument. It is not written to the repo, to
  release_info.json, to the notes or to the zip. The disc folder is never written to (the script
  snapshots its files before and after and fails if anything changed).

.PARAMETER Disc     Path to the .cue of your own disc image.
.PARAMETER Version  Release version, e.g. 0.1.0 (tag is v<Version> unless -Ref says otherwise). A dotted
                    version must equal the VERSION file at the commit; any other label (e.g. "test") skips that check.
.PARAMETER Ref      Tag or commit to build. Default: tag v<Version> (must exist).
.PARAMETER Pgo      Build with PGO (needs the disc and a window; off by default).
.PARAMETER Draft    After the build, print the draft-upload command; run it only after typing UPLOAD.
.PARAMETER Publish  Not implemented.
.PARAMETER Repo     owner/name passed to gh as --repo (optional).
.PARAMETER KeepDisc Keep the disc copy that generate makes inside the staging clone (deleted by default).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\release.ps1 -Version 0.1.0 -Disc "D:\discs\game.cue"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Disc,
    [Parameter(Mandatory = $true)][string]$Version,
    [string]$Ref,
    [switch]$Pgo,
    [switch]$Draft,
    [switch]$Publish,
    [string]$Repo,
    [switch]$KeepDisc
)
$ErrorActionPreference = 'Stop'

if ($Publish) { throw '-Publish is not implemented in T3.19. Use -Draft; publishing the draft is a separate, explicit step.' }

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Version = $Version.Trim().TrimStart('v')
if ($Version -notmatch '^[0-9A-Za-z][0-9A-Za-z._-]{0,40}$') { throw "Bad -Version '$Version'" }
$Tag = "v$Version"
$ProductName = 'MythologyKombat'
$ZipName = "$ProductName-$Version-Windows-x64.zip"

# Keep line endings out of the build: independent of the user's global git config (T3.26).
$env:GIT_CONFIG_COUNT = '1'
$env:GIT_CONFIG_KEY_0 = 'core.autocrlf'
$env:GIT_CONFIG_VALUE_0 = 'false'

# Reproducible helper exes (T3.26): the framework builds psxrecomp-bios.exe and psxrecomp-game.exe (shipped in
# overlay_toolchain\) in its own CMake build. CMake seeds CMAKE_EXE_LINKER_FLAGS from LDFLAGS on first configure, so
# this drops the PE link timestamp there too. The game exe gets the same flag from the top-level CMakeLists.txt.
$env:LDFLAGS = '-Wl,--no-insert-timestamp'

$Timings = New-Object System.Collections.Specialized.OrderedDictionary
function Measure-Step([string]$name, [scriptblock]$body) {
    Write-Host ''
    Write-Host ("=== {0}" -f $name)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & $body
    $sw.Stop()
    $Timings[$name] = $sw.Elapsed.TotalSeconds
    Write-Host ("--- {0}: {1:N1} s" -f $name, $sw.Elapsed.TotalSeconds)
}

function Git-Out {
    # git with output captured as text lines; throws on non-zero.
    $out = & git @args
    if ($LASTEXITCODE -ne 0) { throw ("git {0} failed (exit {1})" -f ($args -join ' '), $LASTEXITCODE) }
    return @($out | Where-Object { "$_" -ne '' })
}

function Quote-Arg([string]$a) { return '"' + ($a -replace '"', '\"') + '"' }

function Invoke-Logged {
    # Runs a program with stdout/stderr to log files, prints a heartbeat, returns the exit code.
    param([string]$Exe, [string[]]$ArgList, [string]$Log, [string]$WorkDir)
    $outLog = "$Log.out.txt"; $errLog = "$Log.err.txt"
    $argStr = ($ArgList | ForEach-Object { Quote-Arg $_ }) -join ' '
    Write-Host ("  > {0} {1}" -f (Split-Path $Exe -Leaf), $argStr)
    Write-Host ("  log: {0}" -f $outLog)
    $p = Start-Process -FilePath $Exe -ArgumentList $argStr -WorkingDirectory $WorkDir `
        -RedirectStandardOutput $outLog -RedirectStandardError $errLog -NoNewWindow -PassThru
    $null = $p.Handle   # keep the handle so ExitCode is readable (PS 5.1)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $next = 60
    while (-not $p.HasExited) {
        Start-Sleep -Seconds 2
        if ($sw.Elapsed.TotalSeconds -ge $next) {
            $sz = 0; if (Test-Path -LiteralPath $outLog) { $sz = (Get-Item -LiteralPath $outLog).Length }
            Write-Host ("  ... running {0:N0} s (log {1} bytes)" -f $sw.Elapsed.TotalSeconds, $sz)
            $next += 60
        }
    }
    $p.WaitForExit()
    return $p.ExitCode
}

function Show-Tail([string]$path, [int]$n = 25) {
    if (Test-Path -LiteralPath $path) { Get-Content -LiteralPath $path -Tail $n | ForEach-Object { Write-Host ("    | " + $_) } }
}

function Get-Sha256([string]$path) { return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }

function Write-TextLF([string]$path, [string]$text) {
    $dir = Split-Path $path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    [IO.File]::WriteAllText($path, ($text -replace "`r`n", "`n"), (New-Object Text.UTF8Encoding($false)))
}

# ---------------------------------------------------------------- preflight
$sumAll = [Diagnostics.Stopwatch]::StartNew()
Write-Host "release.ps1: version $Version, repo $RepoRoot"

if (-not (Test-Path -LiteralPath $Disc -PathType Leaf)) { throw "Disc not found: $Disc" }
if ([IO.Path]::GetExtension($Disc).ToLowerInvariant() -ne '.cue') { throw "-Disc must be the .cue file" }
$Disc = (Resolve-Path -LiteralPath $Disc).Path
$discDir = Split-Path $Disc -Parent
function Get-DiscSnapshot {
    Get-ChildItem -LiteralPath $discDir -File | Sort-Object Name | ForEach-Object { "{0}|{1}|{2}" -f $_.Name, $_.Length, $_.LastWriteTimeUtc.Ticks }
}
$discBefore = @(Get-DiscSnapshot)
$mainStatusBefore = @(Git-Out -C $RepoRoot status --porcelain)

# Pick a Python for the content check (never -I-less: the checker is stdlib only).
$retro = Join-Path $env:USERPROFILE 'retro-tools'
if ($env:RETRO_TOOLS_DIR) { $retro = $env:RETRO_TOOLS_DIR }
$Py = Join-Path $retro 'python\python.exe'
if (-not (Test-Path -LiteralPath $Py)) {
    $c = Get-Command python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($c) { $Py = $c.Source } else { throw "No Python found for the content check (looked for $Py)" }
}
$Checker = Join-Path $PSScriptRoot 'check_release_content.py'
if (-not (Test-Path -LiteralPath $Checker)) { throw "missing $Checker" }

# Resolve the ref to a commit.
$refName = $Ref
if (-not $refName) {
    & git -C $RepoRoot rev-parse --verify --quiet "refs/tags/$Tag" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Tag $Tag does not exist. Create it first, or pass -Ref <commit> for a test build." }
    $refName = $Tag
}
$Commit = (Git-Out -C $RepoRoot rev-parse --verify "$refName^{commit}" | Select-Object -First 1).Trim()
$CommitDate = (Git-Out -C $RepoRoot show -s --format=%cI $Commit | Select-Object -First 1).Trim()
$FixedTime = [DateTimeOffset]::Parse($CommitDate).UtcDateTime
$isTag = $false
& git -C $RepoRoot rev-parse --verify --quiet "refs/tags/$Tag^{commit}" | Out-Null
if ($LASTEXITCODE -eq 0) {
    $tagCommit = (Git-Out -C $RepoRoot rev-parse "refs/tags/$Tag^{commit}" | Select-Object -First 1).Trim()
    $isTag = ($tagCommit -eq $Commit)
    if (-not $isTag) { Write-Warning "Tag $Tag exists but points at $tagCommit, not the requested $Commit" }
}
Write-Host ("commit {0} ({1}); tag {2} {3}" -f $Commit, $CommitDate, $Tag, $(if ($isTag) { 'matches' } else { 'does not match (test build)' }))
if ($Draft -and -not $isTag) { throw "-Draft needs tag $Tag to exist and point at the built commit." }
if ($mainStatusBefore.Count -gt 0) {
    Write-Warning ("The working tree has {0} uncommitted change(s). They are NOT part of this release (only commit {1} is built)." -f $mainStatusBefore.Count, $Commit.Substring(0, 8))
}

# Staging layout (everything under work\release\<Version>\ ; refuse anything else).
$ReleaseRoot = [IO.Path]::GetFullPath((Join-Path $RepoRoot 'work\release'))
$R = [IO.Path]::GetFullPath((Join-Path $ReleaseRoot $Version))
if (-not ($R + '\').StartsWith($ReleaseRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "staging dir escapes work\release: $R" }
$Src = Join-Path $R 'src'
$Logs = Join-Path $R 'logs'
$Pkg = Join-Path $R "$ProductName-$Version"
$ZipPath = Join-Path $R $ZipName
$SumsPath = Join-Path $R 'checksums.txt'
$NotesPath = Join-Path $R 'release_notes.md'

if (Test-Path -LiteralPath $R) {
    Write-Host "removing previous staging dir $R"
    # git object files are read-only
    & cmd.exe /c "rd /s /q `"$R`"" | Out-Null
    if (Test-Path -LiteralPath $R) { throw "could not remove $R" }
}
New-Item -ItemType Directory -Force -Path $R, $Logs | Out-Null

# ---------------------------------------------------------------- 1. clean checkout
Measure-Step '1 clone' {
    & git clone --quiet --no-checkout $RepoRoot $Src
    if ($LASTEXITCODE -ne 0) { throw 'git clone failed' }
    & git -C $Src config core.autocrlf false
    & git -C $Src checkout --quiet --detach $Commit
    if ($LASTEXITCODE -ne 0) { throw "commit $Commit is not in the clone (not reachable from a branch or tag?)" }
    & git -C $Src -c protocol.file.allow=always submodule update --init --recursive --quiet
    if ($LASTEXITCODE -ne 0) { throw 'git submodule update failed (network needed for the submodules)' }

    $dirty = @(Git-Out -C $Src status --porcelain)
    $dirtySub = @(Git-Out -C $Src submodule foreach --quiet --recursive 'git status --porcelain')
    if ($dirty.Count -gt 0 -or $dirtySub.Count -gt 0) {
        $dirty + $dirtySub | ForEach-Object { Write-Host "  dirty: $_" }
        throw 'the fresh checkout is not clean'
    }
    $subStatus = (Git-Out -C $Src submodule status --recursive) -join "`n"
    if ($subStatus -match '(?m)^[+\-U]') { throw "submodules are not at their pinned commits:`n$subStatus" }
    $pins = Get-Content -LiteralPath (Join-Path $Src 'framework_pins.txt')
    foreach ($line in $pins) {
        if ($line -match '^(\S+)=\S+ \(([0-9a-f]{40})\)') {
            $pinName = $Matches[1]; $pinSha = $Matches[2]
            if (-not $subStatus.Contains($pinSha)) { throw "framework_pins.txt: $pinName $pinSha is not what the checkout has" }
        }
    }
    if (Test-Path -LiteralPath (Join-Path $Src 'generated')) { throw 'the fresh checkout already has generated\ (D24)' }
    Write-Host 'checkout is clean; submodules match framework_pins.txt'

    # Reproducible build id (T3.26, D27). The exe embeds `git describe --always --dirty --tags` of this
    # repo and of psxrecomp. Tags (a temp test tag, a later release tag) would change that string between
    # builds of one commit, so drop every tag in the staging clone and its submodules: describe then gives
    # the bare commit hash, fixed to 12 characters. The -Version label never enters the build id.
    & git -C $Src config core.abbrev 12
    & git -C $Src submodule foreach --quiet --recursive 'git config core.abbrev 12'
    foreach ($repoDir in @($Src) + @(Git-Out -C $Src submodule foreach --quiet --recursive 'echo $toplevel/$sm_path')) {
        foreach ($t in @(Git-Out -C $repoDir tag --list)) { & git -C $repoDir tag -d $t | Out-Null }
    }
}
$VerFile = (Get-Content -LiteralPath (Join-Path $Src 'VERSION') -Raw).Trim()
if ($Version -match '^\d+\.\d+\.\d+') {
    if ($VerFile -ne $Version) { throw "VERSION file at $Commit says '$VerFile' but -Version is '$Version'" }
}

# ---------------------------------------------------------------- 2. launcher patches
$PatchedUi = $null
Measure-Step '2 launcher patches' {
    $dest = Join-Path $Src 'work\recomp-ui-patched'
    $applyLog = Join-Path $Logs '02-apply-launcher-patches'
    $code = Invoke-Logged -Exe 'powershell.exe' -WorkDir $Src -Log $applyLog -ArgList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $Src 'tools\apply_launcher_patches.ps1'), '-Dest', $dest)
    if ($code -ne 0) { Show-Tail "$applyLog.err.txt"; Show-Tail "$applyLog.out.txt"; throw "apply_launcher_patches failed ($code)" }
    Get-Content -LiteralPath "$applyLog.out.txt" | Where-Object { $_ -match '^applied ' } | ForEach-Object { Write-Host "  $_" }
    if (-not (Test-Path -LiteralPath (Join-Path $dest 'recomp_ui.cmake'))) { throw 'patched recomp-ui tree is missing recomp_ui.cmake' }
    $script:PatchedUi = $dest
    # The pinned submodule itself must still be untouched.
    if (@(Git-Out -C (Join-Path $Src 'recomp-ui') status --porcelain).Count -gt 0) { throw 'recomp-ui submodule was modified' }
}
$PatchNames = @(Get-ChildItem -LiteralPath (Join-Path $Src 'patches\launcher') -Filter '*.patch' | Sort-Object Name | ForEach-Object { $_.Name })

# ---------------------------------------------------------------- 3. verify-disc, generate, ensure-toolchain, rebuild
$Run = Join-Path $Src 'tools\run_psxrecomp.ps1'
if (-not (Test-Path -LiteralPath $Run)) { throw "missing $Run" }
$Config = Join-Path $Src 'game.toml'
function Invoke-Cli([string]$name, [string[]]$cliArgs) {
    $log = Join-Path $Logs ('03-' + $name)
    $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $Run) + $cliArgs
    $code = Invoke-Logged -Exe 'powershell.exe' -ArgList $a -Log $log -WorkDir $Src
    if ($code -ne 0) {
        Show-Tail "$log.err.txt" 15; Show-Tail "$log.out.txt" 25
        throw ("{0} failed with exit code {1} (see {2}.out.txt)" -f $name, $code, $log)
    }
    return "$log.out.txt"
}

Measure-Step '3a verify-disc' {
    $null = Invoke-Cli 'verify-disc' @('verify-disc', '--config', $Config, '--project-root', $Src, '--disc', $Disc)
}
Measure-Step '3b generate' {
    $null = Invoke-Cli 'generate' @('generate', '--config', $Config, '--project-root', $Src, '--disc', $Disc)
    $marker = Join-Path $Src 'generated\SLUS_004.76_dispatch.c'
    if (-not (Test-Path -LiteralPath $marker)) { throw "generate did not write $marker" }
    $n = @(Get-ChildItem -LiteralPath (Join-Path $Src 'generated') -File).Count
    Write-Host "  generated\ has $n files (stay in the staging clone; never shipped)"
}
$TcOut = $null
Measure-Step '3c ensure-toolchain' {
    $script:TcOut = Invoke-Cli 'ensure-toolchain' @('ensure-toolchain', '--project-root', $Src)
}
$buildDir = Join-Path $Src 'build-release'
Measure-Step '3d rebuild' {
    $rb = @('rebuild', '--config', $Config, '--project-root', $Src, '--build-dir', $buildDir,
        '--target', 'psx-runtime', '--exe-basename', $ProductName,
        ('--cmake-extra=-DRECOMP_UI_ROOT=' + ($PatchedUi -replace '\\', '/')),
        '--cmake-extra=-DPSX_PUBLIC_RELEASE=ON',
        # Reproducible exe (T3.26): commit time for __DATE__/__TIME__, no PE timestamp, no path leakage.
        ('--cmake-extra=-DMK_SOURCE_DATE_EPOCH=' + ([DateTimeOffset]$FixedTime).ToUnixTimeSeconds()))
    if ($Pgo) { $rb += @('--force-pgo', '--disc', $Disc) } else { $rb += '--no-pgo' }
    $null = Invoke-Cli 'rebuild' $rb
}

# Toolchain version for the version file.
$TcVersion = 'unknown'; $TcInfo = $null
$tcBinLine = Get-Content -LiteralPath $TcOut | Where-Object { $_ -match 'Toolchain ready:\s*(.+)$' } | Select-Object -First 1
$tcCandidates = @()
if ($tcBinLine -match 'Toolchain ready:\s*(.+)$') { $tcCandidates += (Split-Path (Split-Path $Matches[1].Trim() -Parent) -Parent) }
$tcCandidates += (Join-Path $retro 'cmake-clang')
foreach ($t in $tcCandidates) {
    $j = Join-Path $t 'retcomm-toolchain.json'
    if (Test-Path -LiteralPath $j) { $TcInfo = Get-Content -LiteralPath $j -Raw | ConvertFrom-Json; $TcVersion = $TcInfo.version; break }
}
Write-Host "toolchain: $($TcInfo.id) $TcVersion"

# ---------------------------------------------------------------- 4. build guards
$Exe = Join-Path $buildDir "$ProductName.exe"
$marker = Join-Path $buildDir 'psxrecomp_exe_name-psx-runtime.txt'
if (Test-Path -LiteralPath $marker) {
    $pub = (Get-Content -LiteralPath $marker -Raw).Trim()
    if ($pub) { $Exe = Join-Path $buildDir "$pub.exe" }
}
if (-not (Test-Path -LiteralPath $Exe)) { throw "game exe not found: $Exe" }
$ExeName = Split-Path $Exe -Leaf
if ($ExeName -ne "$ProductName.exe") { throw "unexpected exe name $ExeName" }
$cache = Get-Content -LiteralPath (Join-Path $buildDir 'CMakeCache.txt')
if ($cache -match '^PSXRECOMP_FORCE_SETUP_HOST:BOOL=ON') { throw 'the build is a setup host, not a game (D24)' }
if (-not ($cache -match '^PSX_PUBLIC_RELEASE:BOOL=ON')) { throw 'PSX_PUBLIC_RELEASE is not ON in the build' }
$uiLine = $cache | Where-Object { $_ -match '^RECOMP_UI_ROOT:' } | Select-Object -First 1
if (-not $uiLine -or ($uiLine -replace '\\', '/') -notmatch [regex]::Escape(($PatchedUi -replace '\\', '/'))) { throw "the build did not use the patched recomp-ui ($uiLine)" }
if (-not (Select-String -LiteralPath (Join-Path $buildDir 'build.ninja') -Pattern 'PSX_HAS_GAME_DISPATCH' -Quiet)) { throw 'no PSX_HAS_GAME_DISPATCH in build.ninja: generated game C was not linked' }
$stamp = (Get-Content -LiteralPath (Join-Path $buildDir 'psx_game_version.txt') -Raw).Trim()
if ($stamp -ne $VerFile) { throw "binary version stamp '$stamp' differs from VERSION '$VerFile'" }
$diagManifest = Get-ChildItem -LiteralPath (Join-Path $buildDir 'mods\bundled\mythologykombat.diagnostics') -Recurse -Filter manifest.toml | Select-Object -First 1
if (-not $diagManifest) { throw 'diagnostics mod manifest not staged' }
if ((Select-String -LiteralPath $diagManifest.FullName -Pattern '^\s*default_enabled\s*=\s*true' -Quiet)) { throw 'diagnostics recording/osd default to ON in the staged mod (public release must default off)' }
$ExeHash = Get-Sha256 $Exe
$ExeSize = (Get-Item -LiteralPath $Exe).Length
Write-Host ("exe: {0} bytes, SHA-256 {1}" -f $ExeSize, $ExeHash)

# ---------------------------------------------------------------- 5. assemble (allow-list)
Measure-Step '5 assemble' {
    New-Item -ItemType Directory -Force -Path $Pkg | Out-Null
    function Put([string]$from, [string]$toRel) {
        if (-not (Test-Path -LiteralPath $from)) { throw "allow-listed item missing: $from" }
        $to = Join-Path $Pkg $toRel
        $d = Split-Path $to -Parent
        if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
        Copy-Item -LiteralPath $from -Destination $to -Force
    }
    function PutTree([string]$fromDir, [string]$toRel, [string[]]$ExcludeNames = @()) {
        if (-not (Test-Path -LiteralPath $fromDir -PathType Container)) { throw "allow-listed folder missing: $fromDir" }
        $base = (Resolve-Path -LiteralPath $fromDir).Path.TrimEnd('\')
        foreach ($f in Get-ChildItem -LiteralPath $base -Recurse -File) {
            if ($ExcludeNames -contains $f.Name) { continue }
            $rel = $f.FullName.Substring($base.Length + 1)
            Put $f.FullName (Join-Path $toRel $rel)
        }
    }
    # game exe and what sits beside it
    Put $Exe $ExeName
    Put (Join-Path $buildDir "$ProductName.execution.json") "$ProductName.execution.json"
    Put (Join-Path $buildDir 'psx_game_version.txt') 'psx_game_version.txt'
    foreach ($dll in Get-ChildItem -LiteralPath $buildDir -File -Filter '*.dll') { Put $dll.FullName $dll.Name }
    # launcher resources, OpenBIOS (the only BIOS), defaults
    PutTree (Join-Path $buildDir 'assets') 'assets'
    Put (Join-Path $buildDir 'bios\openbios.bin') 'bios\openbios.bin'
    Put (Join-Path $buildDir 'bios\OpenBIOS.LICENSE') 'bios\OpenBIOS.LICENSE'
    Put (Join-Path $buildDir 'game.toml') 'game.toml'
    Put (Join-Path $buildDir 'game_options.toml') 'game_options.toml'
    # preloaded mod packages (build output of mods\preloaded + framework builtins); no state.toml, no texture dumps
    PutTree (Join-Path $buildDir 'mods\bundled') 'mods\bundled'
    if (Test-Path -LiteralPath (Join-Path $buildDir 'mods\README.md')) { Put (Join-Path $buildDir 'mods\README.md') 'mods\README.md' }
    # overlay toolchain (runtime autocompiles overlays from the player's own disc); compiler.txt names a path on THIS machine
    PutTree (Join-Path $buildDir 'overlay_toolchain') 'overlay_toolchain' @('compiler.txt')
    # licences
    Put (Join-Path $Src 'LICENSE') 'LICENSE'
    Put (Join-Path $Src 'NOTICE') 'NOTICE'
    PutTree (Join-Path $Src 'psxrecomp\runtime\licenses') 'licenses'
    Put (Join-Path $Src 'psxrecomp\THIRD_PARTY_ATTRIBUTION.md') 'licenses\THIRD_PARTY_ATTRIBUTION.md'
    Put (Join-Path $Src 'psxrecomp\LICENSE') 'licenses\psxrecomp-LICENSE'
    Put (Join-Path $PatchedUi 'LICENSE') 'licenses\recomp-ui-LICENSE'
    Put (Join-Path $PatchedUi 'assets\common\fonts\NOTICE.md') 'assets\fonts\NOTICE.md'
    Put (Join-Path $PatchedUi 'assets\common\img\NOTICE.md') 'assets\img\NOTICE.md'

    # the defaults file must equal the committed one (generate/build must not have rewritten it)
    $committed = (& git -C $Src show "HEAD:game.toml") -join "`n"
    $shipped = ((Get-Content -LiteralPath (Join-Path $Pkg 'game.toml')) -join "`n")
    if ($committed.TrimEnd() -ne $shipped.TrimEnd()) { Write-Warning 'build-release\game.toml differs from the committed game.toml' }

    # version file
    # [string] casts: Get-Content decorates its output with PS* note properties that ConvertTo-Json would serialise
    # (that leaked local paths into release_info.json once; the content check now also catches JSON-escaped paths).
    $pinPsx = [string](Get-Content -LiteralPath (Join-Path $Src 'framework_pins.txt') | Where-Object { $_ -like 'psxrecomp=*' } | Select-Object -First 1)
    $pinUi = [string](Get-Content -LiteralPath (Join-Path $Src 'framework_pins.txt') | Where-Object { $_ -like 'recomp-ui=*' } | Select-Object -First 1)
    $info = [ordered]@{
        product            = $ProductName
        version            = $Version
        tag                = $Tag
        commit             = $Commit
        commit_date        = $CommitDate
        game_serial        = 'SLUS-00476'
        exe_name           = $ExeName
        exe_size           = $ExeSize
        exe_sha256         = $ExeHash
        toolchain_id       = [string]$TcInfo.id
        toolchain_version  = [string]$TcVersion
        toolchain_llvm     = $(if ($TcInfo -and $TcInfo.pins) { [string]$TcInfo.pins.llvm } else { '' })
        psxrecomp_pin      = $pinPsx
        recomp_ui_pin      = $pinUi
        launcher_patches   = @($PatchNames | ForEach-Object { [string]$_ })
        build              = [ordered]@{ configuration = 'Release'; pgo = [bool]$Pgo; public_release = $true }
    }
    Write-TextLF (Join-Path $Pkg 'release_info.json') ((($info | ConvertTo-Json -Depth 5)) + "`n")

    $readme = @"
$ProductName $Version (Windows x64)

An unofficial, non-commercial native Windows port of Mortal Kombat Mythologies:
Sub-Zero (PlayStation, NTSC-U, SLUS-00476), made with PSXRecomp.

YOU MUST SUPPLY YOUR OWN DISC IMAGE
This download does not include the game disc, a disc image, memory cards or a
retail BIOS. You need your own copy of the game, dumped to a .cue/.bin pair.
Only the NTSC-U release (SLUS-00476) is supported.

HOW TO USE
1. Extract the whole zip to a folder you can write to (not Program Files).
2. Run $ExeName.
3. In the launcher, pick your own disc image (the .cue file), then play.
4. Saves go to the saves folder and settings to a settings file next to the exe.

WHAT IS IN THIS ZIP
- ${ExeName}: the game program. It was produced by translating the game's program
  code taken from a disc image, so it is derived from the original game and may
  contain parts of its code and data. It needs your own disc image to run.
- assets, mods, overlay_toolchain, bios (OpenBIOS, an open-source BIOS
  replacement under the MIT licence), licenses: files the program needs.
- LICENSE, NOTICE, licenses\: the licence of this port (PolyForm Noncommercial
  1.0.0) and third-party notices.
- release_info.json: version, source commit, exe SHA-256, toolchain version.

NOT IN THIS ZIP: any disc image, memory card, save, recording, retail BIOS
or the generated source code.

CHECK THE DOWNLOAD
Compare the SHA-256 of the zip with checksums.txt on the release page.
The program is not code-signed, so Windows SmartScreen may warn about it.

This project is not affiliated with or endorsed by the rights holders of the
game. Names and trademarks belong to their owners. It is free and must stay free.
"@
    Write-TextLF (Join-Path $Pkg 'README_FIRST.txt') ($readme + "`n")

    # fixed timestamps (commit time) for a deterministic zip
    foreach ($f in Get-ChildItem -LiteralPath $Pkg -Recurse -File) { if ($f.IsReadOnly) { $f.IsReadOnly = $false }; $f.LastWriteTimeUtc = $FixedTime }
    $nFiles = @(Get-ChildItem -LiteralPath $Pkg -Recurse -File).Count
    $bytes = (Get-ChildItem -LiteralPath $Pkg -Recurse -File | Measure-Object Length -Sum).Sum
    Write-Host ("  staged {0} files, {1:N0} bytes in {2}" -f $nFiles, $bytes, $Pkg)
}

# ---------------------------------------------------------------- 6. content check (folder), zip, content check (zip)
$OpenBiosSha = Get-Sha256 (Join-Path $Src 'psxrecomp\bios\openbios.bin')
function Invoke-ContentCheck([string[]]$modeArgs, [string]$logName) {
    $log = Join-Path $Logs $logName
    $a = @('-I', $Checker) + $modeArgs + @('--generated-dir', (Join-Path $Src 'generated'), '--openbios-sha256', $OpenBiosSha)
    $code = Invoke-Logged -Exe $Py -ArgList $a -Log $log -WorkDir $RepoRoot
    Get-Content -LiteralPath "$log.out.txt" | ForEach-Object { Write-Host "    $_" }
    if ($code -ne 0) { throw "release content check FAILED ($code), see $log.out.txt" }
}
Measure-Step '6a content check (folder)' { Invoke-ContentCheck @('--dir', $Pkg, '--deep') '06-check-dir' }

Measure-Step '6b zip' {
    Add-Type -AssemblyName System.IO.Compression
    if (Test-Path -LiteralPath $ZipPath) { Remove-Item -LiteralPath $ZipPath -Force }
    $base = (Resolve-Path -LiteralPath $Pkg).Path.TrimEnd('\')
    $rels = New-Object System.Collections.Generic.List[string]
    foreach ($f in Get-ChildItem -LiteralPath $base -Recurse -File) { $rels.Add($f.FullName.Substring($base.Length + 1).Replace('\', '/')) }
    $arr = $rels.ToArray(); [Array]::Sort($arr, [StringComparer]::Ordinal)
    $fs = [IO.File]::Open($ZipPath, [IO.FileMode]::Create, [IO.FileAccess]::Write)
    try {
        $za = New-Object IO.Compression.ZipArchive($fs, [IO.Compression.ZipArchiveMode]::Create)
        try {
            foreach ($rel in $arr) {
                $entry = $za.CreateEntry("$ProductName-$Version/$rel", [IO.Compression.CompressionLevel]::Optimal)
                $entry.LastWriteTime = New-Object DateTimeOffset($FixedTime, [TimeSpan]::Zero)
                $es = $entry.Open()
                try {
                    $in = [IO.File]::OpenRead((Join-Path $base ($rel.Replace('/', '\'))))
                    try { $in.CopyTo($es) } finally { $in.Dispose() }
                } finally { $es.Dispose() }
            }
        } finally { $za.Dispose() }
    } finally { $fs.Dispose() }
    Write-Host ("  {0}: {1:N0} bytes, {2} entries" -f $ZipName, (Get-Item -LiteralPath $ZipPath).Length, $arr.Count)
}
Measure-Step '6c content check (zip)' { Invoke-ContentCheck @('--zip', $ZipPath) '06-check-zip' }

# ---------------------------------------------------------------- 7. checksums, notes
$ZipHash = Get-Sha256 $ZipPath
Write-TextLF $SumsPath ("{0}  {1}`n" -f $ZipHash, $ZipName)
# verify by recomputing from the file just written
$line = (Get-Content -LiteralPath $SumsPath | Select-Object -First 1)
if ($line -ne ("{0}  {1}" -f (Get-Sha256 $ZipPath), $ZipName)) { throw 'checksums.txt does not match the zip' }

$notes = @"
$ProductName $Version - unofficial Windows port of Mortal Kombat Mythologies: Sub-Zero (PS1, NTSC-U, SLUS-00476)

Download $ZipName, extract it, run $ExeName and pick your own disc image (.cue). You must supply your own disc image: it is not included.

This zip contains the game program built from a disc image on the maintainer's PC (so it is derived from the original game), the launcher, OpenBIOS, mods and licences. It contains no disc image, memory card, save, recording or retail BIOS.

SHA-256 of the zip: $ZipHash
Source commit: $Commit
Game exe SHA-256: $ExeHash
Toolchain: $($TcInfo.id) $TcVersion
The program is not code-signed; Windows SmartScreen may warn.
"@
Write-TextLF $NotesPath ($notes + "`n")

# ---------------------------------------------------------------- 8. disc + repo untouched, cleanup
if (-not $KeepDisc) {
    $discCopy = Join-Path $Src 'work\disc'
    if (Test-Path -LiteralPath $discCopy) { & cmd.exe /c "rd /s /q `"$discCopy`"" | Out-Null; Write-Host 'removed the disc copy from the staging clone' }
}
$discAfter = @(Get-DiscSnapshot)
$discSame = (($discBefore -join "`n") -eq ($discAfter -join "`n"))
$mainStatusAfter = @(Git-Out -C $RepoRoot status --porcelain)
$mainSame = (($mainStatusBefore -join "`n") -eq ($mainStatusAfter -join "`n"))
if (-not $discSame) { throw 'the disc folder changed during the run' }
if (-not $mainSame) {
    # The script only writes under work\ (git-ignored). A change here means someone edited the repo while it ran.
    Write-Warning 'git status of the main repo differs from the start of the run (this script writes only under work\):'
    Compare-Object $mainStatusBefore $mainStatusAfter | ForEach-Object { Write-Warning ("  {0} {1}" -f $_.SideIndicator, $_.InputObject) }
}

$sumAll.Stop()
Write-Host ''
Write-Host '================ RELEASE BUILT (nothing uploaded) ================'
Write-Host ("zip       : {0}" -f $ZipPath)
Write-Host ("zip size  : {0:N0} bytes" -f (Get-Item -LiteralPath $ZipPath).Length)
Write-Host ("zip sha256: {0}" -f $ZipHash)
Write-Host ("exe sha256: {0}  ({1:N0} bytes)" -f $ExeHash, $ExeSize)
Write-Host ("checksums : {0}" -f $SumsPath)
Write-Host ("notes     : {0}" -f $NotesPath)
Write-Host ("disc folder unchanged: {0}; main repo git status unchanged: {1}" -f $discSame, $mainSame)
foreach ($k in $Timings.Keys) { Write-Host ("  {0,-28} {1,8:N1} s" -f $k, $Timings[$k]) }
Write-Host ("  {0,-28} {1,8:N1} s" -f 'total', $sumAll.Elapsed.TotalSeconds)

# ---------------------------------------------------------------- 9. optional draft upload (typed confirmation only)
if ($Draft) {
    $ghArgs = @('release', 'create', $Tag, $ZipPath, $SumsPath, '--draft', '--title', "$ProductName $Version", '--notes-file', $NotesPath, '--target', $Commit)
    if ($Repo) { $ghArgs += @('--repo', $Repo) }
    $shown = 'gh ' + (($ghArgs | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join ' ')
    Write-Host ''
    Write-Host 'Draft upload command (creates a DRAFT release; publishing it is a separate explicit step):'
    Write-Host "  $shown"
    $nonInteractive = (-not [Environment]::UserInteractive) -or [Console]::IsInputRedirected -or
        ([Environment]::GetCommandLineArgs() -contains '-NonInteractive')
    if ($nonInteractive) {
        Write-Host 'Non-interactive session: NOT running it. Run the command yourself, or re-run this script from a normal PowerShell window.'
    } else {
        $answer = Read-Host 'Type UPLOAD (exactly, upper case) to run it now, anything else to skip'
        if ($answer -ceq 'UPLOAD') {
            & gh @ghArgs
            if ($LASTEXITCODE -ne 0) { throw "gh release create failed ($LASTEXITCODE)" }
        } else {
            Write-Host 'Skipped. Nothing was uploaded.'
        }
    }
}
