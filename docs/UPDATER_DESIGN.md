# Updater design (T3.21 research)

Status: research and proposal only, written 2026-10-21. Nothing here is decided or built. Decision goes to a new entry in `docs\DECISIONS.md` (question 284). `recomp-ui\` and `psxrecomp\` are not edited.

Evidence tags: **[V]** verified (read or measured in this session, source given), **[I]** inferred from verified facts, **[H]** hypothesis or not tested.
Web sources were read with `gh api repos/<r>/contents/...` (raw file text) and `curl` on `api.github.com` metadata and on the 4-line `checksums.txt` only. No release binary was downloaded.

## 1. Summary

1. Neither reference project has what T3.21 asks for. Hell's Gate has a built-in check, but the update step downloads and runs an installer exe, with no checksum. For its portable zip it only opens the release page. Shaolin Monks Recomp has no updater for the game at all; its "Check for updates" button is for mods. [V] sections 2 and 3.
2. recomp-ui and the codegen host have no game or launcher updater. The only update code is the toolchain-pack check in `psxrecomp_codegen_host.c`, and it is Windows-only and tied to the setup wizard (which our release zip does not use). [V] section 4.
3. Our zip is already shaped for an in-place update: one top folder, `release_info.json`, `checksums.txt` in `sha256sum` format, and all player data lives beside the exe. [V] section 5. Two gaps: no per-file manifest in the zip, and the launcher may write into a shipped file (`game.toml`).
4. Recommendation: a small standalone PowerShell updater shipped in the zip (`update.cmd` + `update.ps1`), not an ImGui patch. The launcher gets at most a later 30-line patch that starts it. Effort about 3 days against about 6 to 8 for a built-in C updater. Section 7.

## 2. Hell's Gate Recomp (florinp93/hells-gate-recomp)

Sources: `launcher/README.md`, `launcher/DantesInferno.Shared/GitHubUpdater.cs`, `launcher/DantesInfernoLauncher/MainWindow.xaml.cs`, `launcher/installer.iss`, `launcher/package-release.ps1`, release metadata from `gh api repos/florinp93/hells-gate-recomp/releases`. All [V] unless tagged.

| Question | What it does |
|---|---|
| Stack | C# WPF launcher (.NET Framework 4.0) plus an Inno Setup installer. The launcher is a separate exe from the game (`dantes_inferno.exe`). README "Projects". |
| API | `GET https://api.github.com/repos/florinp93/hells-gate-recomp/releases` (the list, not `/latest`). It takes element 0. `GitHubUpdater.cs` line 151 (URL), lines 170 to 180 (first element). This includes prereleases. Every listed release so far has `prerelease=false`, so it works for them. |
| Auth | Optional `token` parameter, sent as `Authorization: token ...` (`GitHubUpdater.cs` lines 162 to 168). The launcher calls `CheckLatest()` with no token (`MainWindow.xaml.cs` lines 50 and 953). |
| TLS | Sets `SecurityProtocol = 3072` (TLS 1.2) in a static constructor (`GitHubUpdater.cs` line 157). Needed on .NET Framework 4.0. |
| When | On launcher start, in a background task, silently on error (`MainWindow.xaml.cs` lines 45 to 86). Also a "Check for Updates" button (line 947). If newer, a Yes/No message box offers "download and install". |
| Version compare | Own `SemanticVersion`: strips `v`, splits `+meta` and `-prerelease`, up to 4 numeric parts, release > prerelease, numeric then ordinal prerelease compare (`GitHubUpdater.cs` lines 32 to 125). Update if `release.Version > localVersion` (`MainWindow.xaml.cs` line 57). Local version is `version.txt` next to the launcher (`version.txt` holds `0.8.4-beta`). |
| Which asset | Exact name `DantesInfernoInstaller.exe` (`MainWindow.xaml.cs` lines 941 to 945). |
| Checksum | **None.** No hash in `GitHubUpdater.cs`, `MainWindow.xaml.cs` or `package-release.ps1` (grep for sha/checksum/hash found nothing relevant). The release assets are only the portable zip and the installer exe (`gh api .../releases`), so no `checksums.txt` exists. |
| Download | `WebClient.DownloadFile(asset.BrowserDownloadUrl, %TEMP%\DantesInfernoUpdate\<asset name>)` (`GitHubUpdater.cs` lines 202 to 225; `MainWindow.xaml.cs` line 1032). The asset URL is used as given. There is no host or scheme check. The asset name goes into `Path.Combine` unchecked [I: a hostile name with path parts could write elsewhere; low risk since the repo owner controls it]. |
| Replace | Does not replace anything itself. After a "Launch Installer" confirm it runs the downloaded installer (`Process.Start`, `UseShellExecute`) and calls `Application.Current.Shutdown()` (`MainWindow.xaml.cs` lines 1075 to 1095). The installer (Inno Setup, `PrivilegesRequired=admin`, `installer.iss` line 25) writes over the install folder. This also solves the "running exe is locked" problem: the launcher exits first. |
| What is kept | Inno copies only the files it lists; `[InstallDelete]` removes two named leftovers; `[UninstallDelete]` (uninstall only) removes `game`, `logs`, `dantes_inferno.toml`, `version.txt` (`installer.iss` lines 101 to 110). Release notes say an install over an existing one keeps saves and settings (launcher README of 2026-10-20, section 1 of `LAUNCHER_DESIGN.md`). |
| Portable zip | No in-app update. If `unins000.exe` is absent, the launcher shows "download the new portable zip from the release page and extract it over this folder (your saves and settings are kept)" and opens the release page (`MainWindow.xaml.cs` lines 996 to 1006). `package-release.ps1` line 113 says `portable.txt` keeps saves next to the game. |
| Rollback | None. |

What to take: GitHub-releases polling at launcher start, a prompt rather than a silent install, and the manual-extract fallback for zips. What not to take: running a downloaded exe with no hash check, the unvalidated asset URL, and `/releases` index 0.

## 3. Shaolin Monks Recomp (OAleex/ShaolinMonksRecomp)

Sources: `README.md`, `UPSTREAM.md`, `docs/TROUBLESHOOTING.md`, `tools/package_release.py`, `src/mods/http.cpp`, `src/mods/catalog.cpp`, `src/mods/manager.cpp`, release metadata. All [V].

| Question | Finding |
|---|---|
| Game self-update | **None.** A grep of every `src/**/*.cpp|h|inl` and `tools/*.py` for `api.github`, `releases/latest`, `self-update` found no game updater. The only "Check for updates" is `launcher.cpp` lines 418 and 805, which calls `mods->Refresh()` (mod catalog). The README says "It checks for mod updates when it opens" (README, Mods section). |
| How a player updates the game | By hand: README "Getting started" says download the latest release package, extract, start the exe. Settings, logs, cache, mods and saves are kept in separate "Data" and "Saves" folders that the player can move (README "User files"), so extracting a new zip does not touch them. |
| Release assets | `0.2.0`: `ShaolinMonksRecomp-0.2.0-Windows-x64.zip`, `...Linux-x64.tar.gz`, `checksums.txt`. `0.1.0`: zip only (`gh api .../releases`). Tags are bare `0.2.0`, not `v0.2.0`. |
| checksums.txt | `sha256sum` format, two spaces, written by `tools/package_release.py` `checksum()` lines 23 to 27 (`<hex>  <file name>`). I fetched it: two lines, `5a977a1c...  ShaolinMonksRecomp-0.2.0-Windows-x64.zip` and the Linux one. It is for the player to compare by hand; no code verifies it. |
| Version rule | `package_release.py` line 42: `^\d+\.\d+\.\d+(-[A-Za-z0-9.]+)?$`. |
| Mod update safety (the part worth copying) | `http.cpp` line 62: only `https://` URLs. WinHTTP redirect policy `DISALLOW_HTTPS_TO_HTTP` (lines 74 to 75). `catalog.cpp` line 101: the download URL must start with `https://github.com/OAleex/ShaolinMonksRecompKrypt/releases/download/`, and size must be non-zero and at most 2 GiB. `manager.cpp` lines 90, 129 and 139: SHA-256 checked for every file before use and again after install. Mod `path` values are checked for uniqueness (`catalog.cpp` line 118) [V]; the code that rejects `..` was not read [U]. |
| Own SHA-256 and HTTP code | `src/mods/sha256.cpp`, `src/mods/http.cpp` (WinHTTP on Windows). `UPSTREAM.md` says release packages do not include libcurl. |

What to take: the URL allow-list prefix, the size cap, hash-before-use, and keeping player data outside the replaced folder. Note the second point of difference: they split data from the install folder, we keep data beside the exe (section 5), so we need the preserve list.

## 4. What recomp-ui and psxrecomp already provide

Grep over `recomp-ui\` (not `.md`) and `psxrecomp\` sources for `RETCOMM_TOOLCHAIN_SKIP_UPDATE`, `api.github.com`, `releases/latest`, `self-update`, `checksums.txt`, `RETCOMM_DATA_HOME`. [V] for what matched; a negative result is "not found", not proof.

| Finding | Where |
|---|---|
| Toolchain-pack update check: `GET https://api.github.com/repos/<k_tc_repo>/releases/latest` via `curl.exe -fsSL --connect-timeout 5 --max-time 15 -A psxrecomp-codegen -H "Accept: application/vnd.github+json"`, with a fallback that follows the `github.com/<repo>/releases/latest` redirect and reads `url_effective`. Result is parsed with `parse_github_release_tag` and compared to the local pack. | `psxrecomp\host\psxrecomp_codegen_host.c` lines 3491 to 3578 |
| `host_toolchain_update_available` returns 0 when `RETCOMM_TOOLCHAIN_SKIP_UPDATE` is set (not empty, not `0`), on non-Windows, or offline. It is a toolchain-pack check only. | same file, lines 3579 to 3600 |
| It is exposed to the launcher through the `toolchain_update_available` callback (`recomp_launcher.h` line 2100), shown as a prompt on the setup-wizard page 0 with an "Update or Skip" choice (`launcher_model.c` lines 1054 to 1090, 3610 to 3634; `launcher_imgui.cpp` line 13179, `launcher_model_skip_toolchain_update` at 13311). | recomp-ui |
| `RETCOMM_DATA_HOME` selects the `retcomm` data root for the **toolchain cache** only (`psxrecomp_codegen_host.c` line 633; `tools\toolchain_pack.py` lines 9 and 238 to 241). No game or save path uses it (grep of `runtime\src` and `recomp-ui\src` found no other hit). | psxrecomp |
| Game state paths are anchored on the exe directory, never the working directory: `exe_dir_from_argv` ("the SINGLE anchor for every runtime file (game.toml, disc, BIOS, settings.toml, caches, memcards, sidecar .cfg)", `runtime\src\main.cpp` lines 3015 to 3030). | psxrecomp |
| Result for our release build: there is no hook for a game updater. The setup-wizard callbacks exist only when `PSX_SETUP_WIZARD` is on (`LAUNCHER_DESIGN.md` section 3), and the release exe is the bundled game, not the setup host. Question 252 is now answered: not found, search covered the keywords above. Question 284: no upstream updater to adopt. | |
| Reusable idea, not reusable code: the curl-based GitHub query shows that shelling out to `curl.exe` is accepted in this code base. Windows 10 1803 and later ship `curl.exe` and `tar.exe`; Windows 11 is our stated platform. [V] for the host code, [I] for the Windows claim from general knowledge. | |

## 5. What our release zip needs for an in-place update

Sources: `tools\release.ps1` lines 326 to 432, `docs\SETUP.md` "Local release script (T3.19)", `work\release\test\` (the `test` run), `build\` (a dev build folder with runtime files), `game.toml`, question 293. [V] unless tagged.

Zip layout: top folder `MythologyKombat-<version>\` containing `MythologyKombat.exe`, `MythologyKombat.execution.json`, `psx_game_version.txt`, `release_info.json`, `README_FIRST.txt`, `game.toml`, `game_options.toml`, `LICENSE`, `NOTICE`, `assets\`, `bios\openbios.bin`, `mods\bundled\`, `licenses\`, `overlay_toolchain\`, `*.dll`. Zip name `MythologyKombat-<version>-Windows-x64.zip`; `checksums.txt` has one line `<sha256>  <zip name>` (`release.ps1` lines 484 to 489; `work\release\test\checksums.txt`).

Version sources: `release_info.json` holds `version` and `tag` (`v<version>`), `commit`, `exe_sha256` (`release.ps1` lines 380 to 399). `psx_game_version.txt` holds the `VERSION` file (`0.1.0`), not the release label: in the `test` run `release_info.json` says `test` and `psx_game_version.txt` says `0.1.0`. So the updater must read `release_info.json` for the local version. For real releases the two agree because `release.ps1` requires a dotted version to equal `VERSION` (SETUP.md, `-Version`).

Files that appear at run time next to the exe (dev build folder `build\` listing, SETUP.md "Known limits", question 293):

| Path | Keep on update |
|---|---|
| `saves\` (memcards, `memcard_dir = "saves"` in `game.toml` line 39; also `saves\diagnostics`, `saves\netplay`) | yes, never touch |
| `settings.toml`, `input.ini`, `keybinds.ini` | yes |
| `disc.cfg`, `bios.cfg` (remembered disc and BIOS path, `main.cpp` lines 3522 and 3602) | yes. T3.21 text says "keep the disc path": this is it. |
| `launcher-window.ini` | yes |
| `mods\state.toml`, `mods\texture-packs\` | yes |
| `cache\` (per-serial cache, `cache\SLUS-00476`), `overlay_captures.json` and `.d\`, `psx_execution\`, `psx_freeze_*.json`, `psx_last_run_report.json`, `diagnostics-location.txt`, `replay-diagnostics.py`, `work\` | yes (not shipped, so untouched). Whether `cache\` content becomes stale after an exe change is not known [H]. Question to add. |
| `game.toml` | **special.** It is shipped, and the launcher has written into it in the past: `multitap_analog = true` appeared in the repo `game.toml` (questions 260 and 279, commit `6cfe55c`). In a release folder the launcher probably writes the same file [H, not tested]. A blind overwrite could drop a player's choice; a blind keep could keep stale defaults. |
| `game_options.toml` | shipped; whether the launcher writes it is not known [H]. Treat like `game.toml`. |

Gaps in the zip for an updater (changes to T3.19, small):

1. **A per-file manifest** (`manifest.json` or `MANIFEST.sha256`: relative path, size, SHA-256 of every file in the allow-listed folder). Without it the updater cannot tell which installed files came from the old release (to remove files that the new release dropped) or whether a shipped file such as `game.toml` was edited by the player. `release_info.json` today has only `exe_sha256`.
2. `update.cmd` and `update.ps1` in the allow-list, and `check_release_content.py` updated to accept them.
3. Optionally `release_info.json` gets `min_updater_version` or `update_channel`, no more.
4. The repo and tag pattern must be known: `-Repo owner/name` is optional in `release.ps1`, and this repo has no `git remote` in the status I saw (`git remote -v` printed nothing). The owner/repo for the updater is an open item (section 10).

## 6. Constraints for our updater

From the task, D19, D25 and the rules:

- No secrets. GitHub API unauthenticated limit is 60 requests per hour per IP: measured, `X-RateLimit-Limit: 60` from `https://api.github.com/repos/OAleex/ShaolinMonksRecomp/releases/latest`. [V]
- Downloads over https only; final host must be GitHub's. Measured redirect chain for `https://github.com/OAleex/ShaolinMonksRecomp/releases/latest/download/checksums.txt`: 302 to `https://github.com/OAleex/ShaolinMonksRecomp/releases/download/0.2.0/checksums.txt`, then to `https://release-assets.githubusercontent.com/...` (HTTP 200, 2 redirects). So the allow-list must include `github.com` and `*.githubusercontent.com`. [V]
- SHA-256 from `checksums.txt` of the same release.
- Nothing downloaded runs without a user click.
- Rollback; saves, settings and mod state survive; the disc is never downloaded.
- A running `MythologyKombat.exe` is locked against overwrite and delete. Windows allows a rename of a running exe on the same volume [I, general Windows behaviour, not tested here]; do not rely on it. The updater refuses while the exe runs from that folder.
- The updater cannot live only inside the folder it swaps. Copy it to a temp location and run from there.
- Patches to `recomp-ui` are `patches\launcher\*.patch` against the pinned commit `7c635c6b` (D19, `tools\apply_launcher_patches.ps1`). recomp-ui has no HTTP client of its own that I found; a launcher-side check would have to shell out or use WinHTTP.
- Platform: Windows 11 only; no Linux for now.

## 7. Options

| | A. Built-in updater (ImGui patch, C) | B. Standalone PowerShell updater in the zip | C. Standalone small exe (C++/C#) |
|---|---|---|---|
| UI | Button and prompt in the launcher | Console window or a minimal WinForms/`Out-GridView`-free text prompt; launcher button later | Own window or console |
| HTTP, JSON, zip, SHA-256 | Write in C: WinHTTP, JSON parse, zip extract (miniz is not in recomp-ui, Shaolin Monks added their own), SHA-256 | Built in: `Invoke-RestMethod`/`HttpWebRequest`, `System.IO.Compression.ZipFile`, `Get-FileHash` (PowerShell 5.1) | Same as A or use a runtime |
| Swap the running exe | Needs a helper process anyway, so a script or exe still has to exist | The script is the helper | Same |
| Maintenance | Patch against a pinned submodule; rebase on each recomp-ui bump; GL/ImGui rebuild to test | One file, testable without rebuilding the game | New build target, CI job, maybe signing |
| New attack surface | Parsing JSON and zips in C inside the game process | Script is readable and auditable | Native parsing again |
| SmartScreen / policy | None new (same exe) | `.cmd`/`.ps1` extracted from a downloaded zip carry Mark of the Web. Run with `powershell -NoProfile -ExecutionPolicy Bypass -File` from the `.cmd` to avoid `RemoteSigned` blocks. Constrained Language Mode or AppLocker on a locked-down PC could still block it [H] | Unsigned exe can be blocked by Smart App Control (question 255) |
| Effort [H] | 6 to 8 days | **about 3 days** | 4 to 5 days |

**Recommendation: B**, with a launcher button as an optional later step.

Why:
1. The swap needs a separate process in every option (the running exe is locked), so the helper is unavoidable. B is only the helper, nothing else.
2. PowerShell 5.1 already has everything: TLS 1.2 HTTP (set `[Net.ServicePointManager]::SecurityProtocol` as Hell's Gate does), JSON, zip reading entry by entry, SHA-256. No new C code in the game process, no change to the pinned submodule, nothing to rebuild or relink. A relink changes the exe hash (`LAUNCHER_DESIGN.md` 6.2), so avoiding it is a real saving.
3. `tools\release.ps1` and `tools\smoke_release.ps1` are already PowerShell 5.1; the test style matches.
4. If the user later wants the in-launcher button, that is a patch of roughly 30 lines (`ShellExecute` of `update.cmd`, then exit) [H], independent of the updater logic.

Cost of B: a console window; trust in a script a PC policy may block; the updater itself is updated only by the next run (state this in the README).

## 8. Minimal viable design (option B)

### 8.1 Shape

- `update.cmd` (one line): `powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0update.ps1" %*`. Double-click to run. No admin rights.
- `update.ps1`: the logic. Copies itself to `%LOCALAPPDATA%\MythologyKombat\update\run\update.ps1` and re-runs from there with `-InstallDir <original folder>`, so it never runs from the folder it swaps.
- Optional later: launcher button runs `update.cmd`. Optional check on launcher open is a separate, later feature (needs C in the game; skip).

### 8.2 Constants hard-coded in the script

`Repo = "<owner>/<repo>"` (set by T3.21 when the user fixes the repo, section 10), the three allowed hosts, the zip name pattern `^MythologyKombat-(\d+\.\d+\.\d+)-Windows-x64\.zip$`, the preserve list (section 8.5), size caps. A downloaded file never decides any of these.

### 8.3 Flow

1. Read the local version from `<InstallDir>\release_info.json`. If missing or non-numeric (the `test` label), treat as `0.0.0` and say so.
2. Refuse if `MythologyKombat.exe` is running from `InstallDir` (`Get-Process` path match). Offer to wait up to 30 s.
3. Check: `GET https://api.github.com/repos/<Repo>/releases/latest` with `User-Agent` and `Accept: application/vnd.github+json`. `/latest` excludes drafts and prereleases [I, GitHub behaviour; consistent with the toolchain check in `psxrecomp_codegen_host.c` line 3500]. Read `tag_name`, `assets[].name`, `assets[].size`, `assets[].browser_download_url`, `body` (shown as release notes, as text only). Cache the answer for the session; do not poll. If the API returns 403 or 429 (rate limit), fall back to `HEAD https://github.com/<Repo>/releases/latest/download/checksums.txt` without redirect following and read the tag from the `Location` header (the first hop contains `/releases/download/<tag>/`, measured above). No token anywhere.
4. Compare: parse `tag_name` with `^v?(\d+)\.(\d+)\.(\d+)$` (reject anything else, including prerelease tags). Update only if the remote version is strictly greater than the local one. Equal or lower: print "up to date" and stop. A `-Force` is not provided.
5. Show the version, the release notes text and the download size; ask `Download and install? [y/N]`. Nothing else runs without that answer.
6. Pick the assets by exact name: `MythologyKombat-<remote>-Windows-x64.zip` and `checksums.txt`. Require that both `browser_download_url` values start with `https://github.com/<Repo>/releases/download/<tag>/`. Require zip `size` at most 300 MB (today about 27 MB, `SETUP.md` test run).
7. Download both to a new empty folder `%LOCALAPPDATA%\MythologyKombat\update\dl-<remote>\` with redirects followed by hand: each hop must be `https`, host `github.com` or `*.githubusercontent.com`, at most 5 hops. Cap bytes read at the declared size plus 1 KiB. Delete the folder on any failure.
8. Verify: parse `checksums.txt` lines with `^([0-9a-f]{64})  (\S.*)$`; find the line whose name equals the zip name exactly; compare with `Get-FileHash -Algorithm SHA256` of the zip (case-insensitive hex compare). No line, a duplicate line with a different hash, or a mismatch: delete the download, print the error, replace nothing.
9. Validate the zip without extracting to the install folder (section 8.4), then extract into `%LOCALAPPDATA%\MythologyKombat\update\stage-<remote>\` entry by entry. Check each extracted file against `manifest.json` from the zip (path, size, SHA-256). Reject if the zip has a file not in the manifest or the reverse.
10. Swap (section 8.6) and write the backup and journal.
11. Print "Updated to <remote>. Start the game from the folder as usual." and wait for a keypress. It does not start the game automatically (no auto-run). A "start now?" prompt is allowed because it needs a click [H: still counts as a user click; the user can say no].
12. Dry run: `-CheckOnly` stops after step 4; `-DryRun` stops after step 9.

### 8.4 Zip validation (zip-slip and friends)

Use `[System.IO.Compression.ZipFile]::OpenRead` and walk `Entries`. Do not use `Expand-Archive` (PowerShell 5.1 has had path and backslash problems [H]). For each entry:

- Name must start with `MythologyKombat-<remote>/` (forward slash in zip names; also reject `\`). The top folder must equal the version from the file name. Strip that prefix to get the relative path.
- Reject if the relative path is empty after trimming, contains `..` as a segment, starts with `/` or `\`, contains `:` (drive letters and NTFS alternate data streams), a control character, a trailing dot or space in any segment, or a Windows reserved device name (`CON`, `NUL`, `COM1`, ...) in any segment.
- Compute the destination with `[IO.Path]::GetFullPath(Join-Path $stage $rel)` and require it to start with `$stage + '\'` (ordinal, case-insensitive). The check is made on the real path string, not on the entry name.
- Reject entries whose external attributes mark a symlink (zip stores them as a small file; extraction as a plain file is harmless, but reject to be safe), and refuse to extract through an existing reparse point (check the stage folder is freshly created and empty).
- Count at most 5,000 entries (today 421) and a total uncompressed size at most 400 MB (today about 89 MB), and each entry's declared length at most 200 MB (the exe is about 52 MB). Compare `Length` with the manifest. Stop reading an entry at its declared length (zip bomb).
- Reject case-insensitive duplicates.
- Reject paths in the preserve list (section 8.5): a release must never ship `saves\...`, `settings.toml`, `input.ini`, `keybinds.ini`, `disc.cfg`, `bios.cfg`, `launcher-window.ini`, `mods\state.toml`. The content check in `check_release_content.py` should assert this at build time too.

### 8.5 What is preserved

Hard-coded in the updater, matching the table in section 5:

- Never read, move or delete: `saves\`, `settings.toml`, `input.ini`, `keybinds.ini`, `disc.cfg`, `bios.cfg`, `launcher-window.ini`, `mods\state.toml`, `mods\texture-packs\`, `cache\`, `overlay_captures.json`, `overlay_captures.json.d\`, `psx_execution\`, `psx_freeze_*`, `psx_last_run_report.json`, `diagnostics-location.txt`, `replay-diagnostics.py`, `work\`, `.update\`.
- Never download or touch a disc, BIOS dump or memory card.
- Files not named in the old manifest and not in the new one are not touched. The updater deletes only files that the old `manifest.json` lists and the new one drops, and only if the on-disk SHA-256 still equals the old manifest value (a modified file is kept and reported).
- Shipped files that the player may have changed (`game.toml`, `game_options.toml`): compare the on-disk hash with the old manifest hash. Equal means unmodified, so replace it. Different means the player or the launcher changed it, so keep the player's copy, write the new one as `game.toml.new`, and print a warning. **This rule exists because question 260/279 shows the launcher can write into `game.toml`; confirm in the first real test (section 9, test 7).**
- Everything else in the new manifest replaces the old file.

The old manifest is read from the installed folder (`manifest.json`). The first release that has an updater has no older manifest for the first update; so the first release must ship `manifest.json` from the start (T3.19 change), or the first update falls back to "replace every shipped path, keep the preserve list, delete nothing".

### 8.6 Swap and rollback

Order, all on the same volume as `InstallDir` (stage and backup live in `<InstallDir>\.update\` and not in `%LOCALAPPDATA%`, so renames stay on one volume and are cheap; the `.update\` folder is in the preserve list and the download/stage step happens in `%LOCALAPPDATA%` first, then the verified stage is moved to `.update\stage` in one folder move) [H on volume layout; if the folder move crosses volumes the script copies instead].

1. Write `.update\journal.json` with `from`, `to`, and the planned file list. State `staged`.
2. For each file in the plan: move the old file to `.update\backup-<from>\<rel>` (same-volume move, no copy), then move the staged file into place. Write each step to the journal. State `swapping`.
3. If any step fails (locked file, access denied, AV): restore every moved file from the backup in reverse order, write state `rolled-back`, report the failing path, and leave the old version running. Retry a locked file 3 times with 1 s waits first.
4. After all files are in place, verify the installed exe SHA-256 equals `exe_sha256` in the new `release_info.json` and equals the manifest. State `swapped-unconfirmed`. Mismatch triggers rollback.
5. Keep `backup-<from>` and keep `journal.json`. The new build is considered to have started once when `psx_last_run_report.json` (or `release_info`-adjacent marker) is newer than the journal time [H: which file the runtime writes at start was not traced; verify]. At the next updater run, if the state is `swapped-unconfirmed` and the game has started, mark it `confirmed` and delete the older backup. If the game has not started, the updater offers `update.cmd -Rollback`, which restores from `backup-<from>`.
6. At most one backup is kept (about 89 MB).
7. After a crash of the updater itself (power loss), the next run reads `journal.json` and finishes the rollback automatically before doing anything else.

### 8.7 Safety analysis

| Threat | Control |
|---|---|
| Zip-slip, absolute paths, `..`, ADS, reserved names | Section 8.4. Destination checked as a full path under the stage folder. Top folder name must equal the expected version. |
| Zip bomb | Entry count, per-entry and total size caps; read stops at declared length; manifest sizes must match. |
| Tampered or truncated download | SHA-256 from `checksums.txt` of the same release, exact name match, checked before extraction; each file checked against `manifest.json` after extraction and the exe after install. Limit: `checksums.txt` comes from the same GitHub release, so this protects against corruption, truncation and CDN mix-ups, **not** against a compromised repo or release. Real authenticity needs a signature: an Ed25519 or minisign signature over `checksums.txt`, with the **public** key compiled into `update.ps1` and the private key kept on the user's PC and used by `release.ps1`. That adds no secret to the repo. Not in the MVP; list as a follow-up (question). |
| Downgrade or replay of an old release | Strictly-newer rule; tag regex with no prerelease; `/releases/latest` returns only the newest non-prerelease. An attacker who controls the release can still point `latest` at an older tag; the strict compare then says "up to date". |
| Redirect to a non-GitHub host | Manual redirect following; every hop must be `https` and host `github.com` or `*.githubusercontent.com`; at most 5 hops. Scheme downgrade is refused (Shaolin Monks does only `DISALLOW_HTTPS_TO_HTTP`; we are stricter). The asset URL must also start with `https://github.com/<Repo>/releases/download/<tag>/` (the pattern in Shaolin Monks `catalog.cpp` line 101). |
| Hostile release metadata | Asset names matched exactly, never used as paths; release notes printed as plain text; version from a strict regex; sizes capped. |
| Running downloaded code | Never. The updater only copies files. It does not run the new exe, `update.ps1` or anything in the zip. The new `update.ps1` takes effect at the next click. Optional "start the game" prompt needs a typed yes. |
| Repo or host override | Constants in the script; no environment variable or config file changes them. Tests use `-TestBaseUrl http://127.0.0.1:<port>` which is accepted only if the host is `127.0.0.1`, `[::1]` or `localhost`; it also disables nothing else (hash checks still run). |
| Partial update leaves a broken install | Journal and per-file move with backup; automatic rollback on any failure; exe hash check after the swap. |
| Concurrent runs, game running | Single-instance mutex; refuse if the exe runs from that folder. |
| Privacy | Sends only GitHub's normal request (IP, user agent `MythologyKombat-updater/<ver>`). No telemetry. Say so in the README. |
| Rate limit (60 per hour per IP) | One request per manual run, session cache, fallback to the redirect header. Many players behind one NAT could still hit it; the fallback covers it. |
| Install in a protected folder | Refuse with a message if `InstallDir` is not writable; README says "not Program Files". |
| Update only the user's own legal copy | The updater never touches the disc path (`disc.cfg`, `settings.toml`). |

### 8.8 Effort (agent time, guesses [H])

| Piece | Time |
|---|---|
| `release.ps1`: write `manifest.json`, add `update.cmd`/`update.ps1` to the allow-list, update `check_release_content.py` and its tests | 0.5 day |
| `update.ps1`: check, compare, download with redirect checks, verify, zip validation, stage | 1 day |
| Swap, journal, rollback, preserve rules | 0.75 day |
| Pester-free tests under `tests\` driven by a local `python -m http.server`-style test server (the four acceptance cases, plus the hostile-zip cases) | 0.75 day |
| Docs (`SETUP.md`, README section, DECISIONS entry) | 0.25 day |
| Total | about 3 days. Add about 1 day for an optional launcher "Update" patch. |

## 9. Test plan (maps to the T3.21 acceptance)

Use a throwaway install folder under `work\` and a local test server on `127.0.0.1` serving fake `releases/latest` JSON, a zip, and `checksums.txt`. Never the real disc.

1. Newer version found and installed (acceptance 1).
2. Equal and older versions are refused.
3. `checksums.txt` hash wrong: nothing replaced, folder bit-identical to before (acceptance 2).
4. Saves, `settings.toml`, `input.ini`, `keybinds.ini`, `disc.cfg`, `mods\state.toml` survive byte-identical (acceptance 3).
5. Previous build stays in `.update\backup-<from>` until confirmed; `-Rollback` restores it (acceptance 4).
6. Hostile zips: `..\evil.txt`, `/abs`, `C:\x`, `a:stream`, `CON`, wrong top folder, duplicate names, 10,000 entries, oversize entry. All refused, nothing written outside stage.
7. A modified `game.toml` is kept and `game.toml.new` written. Also run the real launcher once on an unzipped release, change a launcher setting, and check which shipped file changes (settles the `game.toml` and `game_options.toml` question).
8. Redirect to `http://` or to a non-GitHub host (test server returns 302): refused.
9. Exe locked (game running): updater stops, nothing changed.
10. Kill the updater mid-swap: next run completes the rollback.
11. Offline and 403/429: friendly message, fallback path tested, no stack trace.

## 10. Open items to add to `docs\OPEN_QUESTIONS.md`

1. Which GitHub `owner/repo` hosts the releases? This repo has no remote in the session's status. The updater needs the constant.
2. Does the launcher write into `game.toml` or `game_options.toml` in a release folder? (Test 7.) Decides keep-or-merge.
3. Is `cache\SLUS-00476` valid across exe versions, or must the updater clear it? Not traced.
4. Which file does the runtime write when it starts (to detect "the new build has run once")? `psx_last_run_report.json` is a candidate; not traced.
5. Sign `checksums.txt` with a public-key signature in a later step? User decision (cheap, no certificate).
6. Should the first public release ship `manifest.json` and `update.cmd` from day one? Recommended yes, otherwise the first update has no old manifest.
7. Does the `.cmd`/`.ps1` pair run on the user's clean machine (MOTW, execution policy)? Add to the T3.22 checklist.
8. `release_info.json` `version` is `test` for test builds while `psx_game_version.txt` says `0.1.0` (observed). The updater uses `release_info.json`; keep that rule.

## 11. Decision text proposed for `docs\DECISIONS.md` (D27, not written)

Updater mechanism: a standalone PowerShell updater (`update.cmd`, `update.ps1`) shipped in the release zip. Reason: neither Hell's Gate (runs an unchecked installer, no portable-zip update) nor Shaolin Monks (manual extract) nor recomp-ui/psxrecomp (toolchain check only) offers a reusable game updater; a running exe needs a helper process anyway; PowerShell 5.1 has all needed primitives; no change to the pinned submodule. Controls: GitHub-only https with host allow-list, SHA-256 from the release's `checksums.txt`, strict-newer compare, zip entry validation, preserve list, one backup with journaled rollback, no auto-run. A launcher button is an optional later patch.

## Sources

Web (read 2026-10-21 with `gh api` or `curl`):
- https://github.com/florinp93/hells-gate-recomp : `launcher/README.md`, `launcher/DantesInferno.Shared/GitHubUpdater.cs`, `launcher/DantesInfernoLauncher/MainWindow.xaml.cs`, `launcher/DantesInfernoLauncher/version.txt`, `launcher/installer.iss`, `launcher/package-release.ps1`, `/releases` metadata.
- https://github.com/OAleex/ShaolinMonksRecomp : `README.md`, `UPSTREAM.md`, `docs/TROUBLESHOOTING.md`, `tools/package_release.py`, `src/launcher.cpp`, `src/mods/http.cpp`, `src/mods/catalog.cpp`, `src/mods/manager.cpp`, `/releases` metadata, `releases/latest/download/checksums.txt` (4 lines, fetched), response headers of `https://api.github.com/repos/OAleex/ShaolinMonksRecomp/releases/latest`.

Local: `docs\TASKS.md` (T3.21), `docs\DECISIONS.md` (D25, D26), `docs\LAUNCHER_DESIGN.md` (sections 1, 3, 4), `docs\SETUP.md` (T3.19), `docs\OPEN_QUESTIONS.md` (252, 259, 260, 279, 284, 293), `tools\release.ps1`, `psxrecomp\host\psxrecomp_codegen_host.c`, `psxrecomp\runtime\src\main.cpp`, `psxrecomp\tools\toolchain_pack.py`, `recomp-ui\src\recomp_launcher.h`, `recomp-ui\src\common\launcher_model.c`, `recomp-ui\src\common\backends\imgui\launcher_imgui.cpp`, `game.toml`, `build\` listing, `work\release\test\`.
