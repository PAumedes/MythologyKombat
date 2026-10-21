# Launcher and distribution design (research)

Status: research and proposal only, written 2026-10-20. Nothing here is decided. Nothing was built, run or pushed.

Update 2026-10-21: superseded by D25 for the distribution choice. The release is a prebuilt game zip, built on the user's PC from the user's disc (`tools\release.ps1`, or an optional self-hosted runner). CI builds the launcher and tools only. Section 2 (options A and C) and section 4 (updater) no longer decide the release route. Section 0 and the excluded options in section 2 still hold. D18's setup-host kit is the fallback and developer path. Section 5 CI rows for the `kit` and `release` jobs are replaced by T3.17 to T3.26.

Evidence tags: **[V]** verified (read in this session; source given), **[U]** unverified (not stated by the source, or inferred), **[H]** hypothesis.
Local sources are paths under `<REPO_ROOT>`. Web pages were read through a fetch tool that summarises the page, so wording is paraphrased; open the URL before quoting.

## 0. The constraint that shapes everything

`CLAUDE.md` (hard rules) and decision D8 (`docs/DECISIONS.md`): generated game C, game binaries and disc contents are never committed or distributed. Only derived address/name/size/hash data is allowed (`seeds/ghidra_funcs.txt`, `game.toml`, `catalog_identity.json`, `.recomp.json`, `aot/overlays.json`, `symbols.toml`).

Consequence: a compiled `MythologyKombat.exe` that has the game C linked in is a game-derived binary. It is excluded, whether it comes from a repo, a release, a CDN or a per-user "cache" that we host. Only things that are built on the user's own machine from the user's own disc stay inside the rule.

## 1. How other projects distribute (comparison)

The user named "Dante's Inferno" and "Shaolin Monks". Searching found these (they are Xbox 360 and Xbox projects, not PS1/PS2, and not the same toolchain as PSXRecomp):

- Dante's Inferno: `florinp93/hells-gate-recomp` (Xbox 360, ReXGlue SDK). Other forks exist (`VaGNaroK/dantes-inferno-linux`). [V] search results.
- Shaolin Monks: `OAleex/ShaolinMonksRecomp` (Xbox). A separate PS2 effort `OGmidway/mksm-recomp` is "not a playable release yet" per the search summary. [V] search results; the PS2 project was not opened.

| Question | Hell's Gate (Dante's Inferno, X360) | ShaolinMonksRecomp (Xbox) | Zelda64Recomp (N64) | PSXRecomp bundled titles (upstream) | Us (target) |
|---|---|---|---|---|---|
| What the user downloads | `DantesInfernoInstaller.exe` (19,643,986 bytes) or `DantesInferno-0.8.4-beta-portable.zip` (31,672,911 bytes). [V] https://api.github.com/repos/florinp93/hells-gate-recomp/releases | `ShaolinMonksRecomp-0.2.0-Windows-x64.zip` (9,620,122 bytes) plus Linux tar.gz and `checksums.txt`. [V] https://api.github.com/repos/OAleex/ShaolinMonksRecomp/releases | Prebuilt binaries from Releases. [V] https://github.com/Zelda64Recomp/Zelda64Recomp | One zip per platform, "the compiled game". [V] `psxrecomp\docs\ci\BUNDLED_RELEASES.md` | A launcher (see section 3) |
| What the launcher does with the disc | Installer asks for the ISO and extracts it into `<install>\game` with `extract-xiso.exe`, unless `game\default.xex` exists. [V] https://raw.githubusercontent.com/florinp93/hells-gate-recomp/main/launcher/README.md | Launcher is pointed at an ISO, XISO, ZIP, folder or `default.xbe`. Runtime reads ISO/XISO directly; ZIP contents are imported once. [V] https://github.com/OAleex/ShaolinMonksRecomp | User picks the US ROM in the main menu; project loads assets from it. ROMs not in .z64 are converted. [V] https://github.com/Zelda64Recomp/Zelda64Recomp | Player picks the disc on first run; it is verified and read at run time. [V] `BUNDLED_RELEASES.md` "What players do" | verify-disc, then generate and compile locally |
| Is code compiled on the user's machine? | README says the game is translated ahead of time and the build-from-source path needs the user's own `default.xex` and runs `dantes_inferno_codegen`. Release docs do not say whether the shipped `dantes_inferno.exe` has game code in it. The launcher README says the game binary ships inside the installer. [V] for both quotes; the conclusion "game code is shipped precompiled in the installer" is [U] (not stated, only implied) | Not stated. Release zip is small (9.6 MB). [U] whether recompiled game code is inside it | `BUILDING.md`: the builder places the ROM, runs `N64Recomp` and `RSPRecomp` to generate C, then builds. [V] https://raw.githubusercontent.com/Zelda64Recomp/Zelda64Recomp/dev/BUILDING.md . README says releases "do not contain game assets". Whether the release exe contains recompiled code, and where CI gets the ROM, was not stated. [U] | No. Game C is committed in the title repo and CI compiles it; nothing is generated on the player's machine. [V] `BUNDLED_RELEASES.md` | Yes (option A, section 2) |
| Updates | Launcher checks GitHub Releases when it opens, compares the newest tag with local `version.txt`, downloads that release's `DantesInfernoInstaller.exe` and runs it. Installer over an existing install keeps saves and settings. No checksum check is mentioned. [V] launcher README and release notes (https://github.com/florinp93/hells-gate-recomp/releases) | Launcher reads a mod catalog and checks mod updates at start. How the game/launcher itself updates is not described. [V] README; [U] for the rest. Releases carry `checksums.txt`. [V] | Not described. [U] | Raw zip extract over the old one; settings and saves live beside the exe. [V] `BUNDLED_RELEASES.md` | Section 4 |
| Licensing statements | Unofficial fan project, not affiliated with EA, Visceral or Microsoft; "contains no game code or assets". The page states no software licence. [V] https://github.com/florinp93/hells-gate-recomp | Code GPL-2.0-or-later; licence does not cover the game; user must supply their own USA/Europe copy; not affiliated with the owners of Mortal Kombat or Xbox. [V] https://github.com/OAleex/ShaolinMonksRecomp | GPL-3.0; "does not contain game assets"; original game required. [V] https://github.com/Zelda64Recomp/Zelda64Recomp | PolyForm Noncommercial 1.0.0 for psxrecomp; MIT for recomp-ui, OpenBIOS. Retail BIOS and discs not distributed; OpenBIOS is. [V] https://github.com/mstan/psxrecomp and `psxrecomp\LICENSE`, `recomp-ui\README.md` | "Stays free" (CLAUDE.md); a repo licence is still undecided (`docs/PUBLISHING_AUDIT.md` blocker 2) |
| Launcher build | C# solution plus Inno Setup `installer.iss`. [V] launcher README | In-tree launcher (Dear ImGui is a dependency). [V] README | In-game menu. [V] | recomp-ui (Dear ImGui, C++) linked into the game exe. [V] `recomp-ui\README.md` | recomp-ui wizard (already in our exe) |
| Self-compile on user machine | Not stated. [U] | Not stated. [U] | Only in the "build it yourself" path. [V] | Only in the retired "setup host" model. [V] `BUNDLED_RELEASES.md` | Yes |
| Retro Launcher (RetroPortingToolKit) | n/a | n/a | n/a | Catalogue, install, update hub. Titles "self-compile on the end user's machine"; first install about 5 to 10 minutes; shared toolchain; stores only the disc path, never a copy. [V] https://github.com/RetroPortingToolKit/Retro-Launcher . Releases: AppImage, Windows installer and portable zip, DMGs, APK; MIT. [V] same page. | Possible catalog entry later (section 3, option D) |

Takeaways:

1. None of the pages read says "the ISO is turned into code on your machine, then compiled". Hell's Gate extracts files; Zelda64Recomp's documented generate step is a developer build step. So "generate then compile on the user's PC" is closest to Retro Launcher's self-compile model and PSXRecomp's retired setup-host model, not to the three projects the user cited. [V] for what each page says; the reading of their intent is [H].
2. Whether Hell's Gate, Shaolin Monks and Zelda64Recomp ship recompiled game code inside their release binaries is **not established** by what was read. If they do, they have taken a legal position that D8 forbids for us. Do not copy their release shape without the owner's decision. [U]
3. Upstream PSXRecomp moved on purpose from setup host to bundled (2026-09-30) because first-run depended on a toolchain download and every generate/build failure landed on the player. [V] `BUNDLED_RELEASES.md` first paragraphs. We would be choosing the model upstream retired, so its failure modes are the known cost.

## 2. Options for this port

Everything in "Excluded" would distribute game-derived code or binaries. Everything in "Allowed" builds game-derived output only on the user's own machine.

### Excluded (distributes game-derived content, so it breaks D8 / CLAUDE.md)

| Option | Why excluded |
|---|---|
| X1. Upstream bundled release: commit `generated/`, CI links it, ship the compiled game zip | Generated C committed; exe contains the translated game. `psxrecomp\docs\GAME_PROJECT_SETUP.md` bundled flow; `scripts/package_release.sh` in this repo is exactly that packager and must not be wired into CI. [V] |
| X2. CI generates from a disc stored in CI secrets or a self-hosted runner, then publishes the exe | Output is the same game-derived exe, and the disc would sit on a server. |
| X3. A "prebuilt cache" we host and the launcher downloads (object files, `libgame.a`, `overlays_static.c`, shard cache, `build-release` tree) | These are compiled/translated game code. A per-user cache **built locally and kept on that PC** is fine; a shared cache is not. |
| X4. Binary patches or deltas of the compiled game for updates | Derived from game-derived binaries. |
| X5. Shipping `overlay_cache` shards produced from a disc | Upstream already refuses this in CI because the cache is compiled from the disc. [V] `BUNDLED_RELEASES.md` "Overlays" |

### Allowed

| Option | What we ship | What runs on the user's PC | Notes |
|---|---|---|---|
| A. Setup-host kit (recommended baseline) | A zip: setup-host exe (`-DPSXRECOMP_FORCE_SETUP_HOST=ON`, no game C, recomp-ui wizard on), the `psxrecomp/` tree the CLI needs (CLI, tools, emitters sources or binaries, OpenBIOS profiles), our derived data (`game.toml`, `seeds/`, `aot/overlays.json`, `symbols.toml`), licences | Wizard: pick disc, `verify-disc`, `generate`, `ensure-toolchain`, `rebuild`; then relaunch the built exe in `build-release\` | Matches what `psxrecomp_codegen_host.c` already implements (`prepare_disc_label = "Generate & rebuild…"`, `setup_needs_toolchain`, `ensure_toolchain_with_progress`, lines about 4815 to 4895). [V] Upstream calls it "a developer convenience - not what CI ships". [V] `LOCAL_CODEGEN_SDK.md`. `package_setup_host.sh` is marked RETIRED and still exists. [V] |
| B. Source-only repo | Nothing prebuilt; README says clone, install the pinned toolchain, run `tools\run_psxrecomp.ps1` | All of it | Cheapest; worst player experience. `docs/PUBLISHING_AUDIT.md` option B. |
| C. Own thin launcher driving the same CLI | A small separate exe (Hell's Gate style: installer plus launcher) that calls `psxrecomp_cli.py` JSONL (`--json-progress`) and shows progress | Same as A | Only worthwhile if the recomp-ui wizard proves too rough (section 6). `--json-progress` event types: `phase`, `disc`, `log`, `result`, `error`. [V] `LOCAL_CODEGEN_SDK.md` |
| D. Retro Launcher catalog entry | Release zip (option A kit) listed in Retro | Retro installs, self-compiles and updates | Possible later; Retro's handling of setup-host kits not verified. [U] |
| E. Optimisation of A: ship framework-only prebuilt objects/libs so the user compiles only the generated C | Pre-compiled runtime/host libraries (no game code) | Compile only `generated/*.c` | Not supported by upstream CMake that I read; feasibility [H]. Saves time but adds a second build recipe to maintain. Only framework code would be prebuilt, so it respects D8. |

Details that decide how painful option A is:

- Player prerequisites: Python 3 (CLI), the clang/CMake/Ninja pack from `RetroPorting-Toolchains` (downloaded by the wizard to `%LOCALAPPDATA%\retcomm\toolchains\cmake-clang-v1\`), internet on first run, disk for the build tree. [V] `LOCAL_CODEGEN_SDK.md` "Where this sits now". The wizard defaults to `/releases/latest` of the toolchain repo and prompts when newer; `RETCOMM_TOOLCHAIN_SKIP_UPDATE=1` disables the check. [V] same file and `psxrecomp_codegen_host.c` lines 2944 and 3490 to 3580. For reproducibility we want a pinned version (v1.0.14 is what `docs/SETUP.md` line 77 uses). Whether the wizard can be pinned to a tag without editing the submodule is **not verified**; `RETCOMM_TOOLCHAIN_MIN_VERSION` only sets a floor. [V] for the floor; [U] for pinning.
- Python: local setup uses a Python 3.12.10 embeddable zip (`docs/SETUP.md` lines 81 and 96). Upstream's `overlay_toolchain/` bundles a "pinned relocatable Python", but only in bundled zips. [V] `BUNDLED_RELEASES.md`. We could ship an embeddable Python in the kit (PSF licence) so the player does not install Python; not tested here. [H]
- Time: Retro says 5 to 10 minutes for self-compile in general. [V] Retro Launcher page. Our measured build time is not recorded in the docs I read; measure it. [U]
- Windows 11 Smart App Control blocks unsigned executables with no "run anyway". A locally compiled exe carries no signature at all; this is a known cost of option A. [V] `psxrecomp\docs\ci\README.md` "Windows code signing". Unknown whether the user's machine has it on. We can sign only the kit exe we ship, not the exe the player builds. [V]
- The updated product lives in `build-release\`, and the zip-root exe forwards to it (`PSXRECOMP_NO_FORWARD=1` opts out). [V] `LOCAL_CODEGEN_SDK.md`.

## 3. Launcher shape

Recommended: use the recomp-ui wizard that is already in our exe (option A), and treat a separate launcher (C) as a fallback.

What recomp-ui + the codegen host already do: [V] unless noted.

- `recomp-ui` is a native Dear ImGui launcher over SDL3 (SDL2 fallback) and OpenGL, linked into the game exe; `recomp_launcher_run_window()` returns LAUNCH, QUIT or UNAVAILABLE. It is not a web or Electron UI. (`recomp-ui\README.md`, `launcher_imgui.cpp` line 3 and lines 14662 to 14666.)
- It has a disc picker (native dialog via tinyfiledialogs; built-in picker fallback), a verdict block (Serial, Region, ISO header, SBI) from the host `disc_verify` callback, PLAY, Settings, Mods. (`launcher_imgui.cpp` `draw_verdict_block` 2100, `draw_game_panel` 2188.)
- With `PSX_SETUP_WIZARD=ON`, `gi->setup_wizard_supported = 1` and the host sets: Generate & rebuild button, progress callbacks, toolchain readiness/ensure/update-available/repair callbacks, PGO option (`psxrecomp_codegen_host.c` 4765 to 4890). `needs_setup` is set when generated sources are missing. Our `CMakeLists.txt` already has `ENABLE_SETUP_WIZARD`.
- The CLI contract it wraps: `verify-disc`, `generate`, `ensure-toolchain`, `rebuild`, `pgo-train`; exit codes 0/1/2/3 (3 = disc verification failure). (`LOCAL_CODEGEN_SDK.md`)
- Updates of the toolchain pack: yes (prompt Update or Skip). Updates of the game/launcher itself: **no** mechanism in recomp-ui or the codegen host that I found; upstream expects a raw zip extract or Retro. A grep of `recomp-ui\src` for an updater was not exhaustive. [U]
- recomp-ui has no CI of its own (`recomp-ui\.github` absent). [V] The standalone `recomp-ui-launcher` is a self-test harness, not an end-user app. [V] `recomp-ui\CMakeLists.txt`, `docs/PUBLISHING_AUDIT.md` item 4.
- Not verified: that a clean second Windows machine with only a disc completes the whole wizard flow. `docs/PUBLISHING_AUDIT.md` section 6 says nobody has done it. This is the acceptance test for any of the options. [U]

Gap list for "like Dante's Inferno": installer UI, auto-update of the kit, a single "Install" progress page covering download toolchain + generate + compile, signed kit. Of these, only the auto-update is missing in code; the rest exist in some form in the wizard.

## 4. Update mechanism

Proposal (GitHub Releases + versioned data):

1. Release asset = the **kit zip** (option A) plus `checksums.txt` (SHA-256) per release, like Shaolin Monks does. [V] for the asset pattern. Hell's Gate's updater mentions no checksum; we should verify one. [V] absence is from a summary; [U] strictly.
2. Kit version `X.Y.Z` in `VERSION`/`psx_game_version.txt` style. The kit contains: pinned `psxrecomp` + `recomp-ui` gitlinks content, `game.toml`, `seeds\`, `aot\overlays.json`, `symbols.toml`, wizard exe.
3. "Data version" stamp: hash of (`seeds`, `game.toml` codegen sections, `aot/overlays.json`, framework SHA, emitter fingerprint). Written by Generate next to the build (the framework already writes `.psxrecomp_last_generate`, which our `.gitignore` lists). On start, if the stamp differs from the kit's data version, the wizard shows "Regenerate and rebuild (about N minutes)". [H] about reuse of that stamp; the file exists, its comparison semantics were not read.
4. Launcher update check: `GET https://api.github.com/repos/<owner>/<repo>/releases/latest`, compare tag with local version, download kit zip, verify hash, extract over the install dir keeping `build-release\`, `saves\`, `settings.toml`, `bios\`. Same shape as Hell's Gate's updater. The host already has a curl-based GitHub query for the toolchain (`psxrecomp_codegen_host.c` 3490 to 3580); that code could be reused or copied for our repo. [V] for the existing code; the reuse is [H]. Upstream edits are not wanted (CLAUDE.md "upstream first"), so this probably lives in `codegen_setup.c` or a launcher-side helper. [H]
5. Saves and settings are preserved because they live beside the exe. [V] `BUNDLED_RELEASES.md`.
6. Never in an update: any file derived from the disc. The kit has none, so the update contains none.
7. Rollback: keep the previous kit directory until the new build succeeds. [H]

## 5. CI (GitHub Actions)

There is no `.github` directory in this repo yet. Add `.github/workflows/`. The `.gitignore` blocks `*.exe`, `*.zip`, `*.dll`, `/dist/`, `/build-*/`. That is fine as long as artifacts are uploaded with `actions/upload-artifact` and `softprops/action-gh-release` from the runner and **never git-added**. Do not use `git add -f`. A "no game data in the tree" guard (below) should run on every PR.

Evidence for the jobs: [V] `psxrecomp\.github\workflows\cli-release.yml` (windows-latest + MSYS2 MinGW64 + `python tools/build_cli.py release`), `psxrecomp\docs\ci\templates\game-release.yml` (windows-2022, MSYS2 for the game, `fetch-toolchain` action for emitters, SDL3 prefetch to avoid HTTP/2 REFUSED_STREAM, emitter cache keyed on the psxrecomp SHA). Nothing in upstream CI uses clang on `windows-latest` directly; it uses the llvm-mingw from the cmake-clang pack. [V] `docs/PUBLISHING_AUDIT.md` section 5.

| Job | Runner | Steps | Artifact | Notes |
|---|---|---|---|---|
| `guard` | ubuntu-latest | checkout (no submodules needed); script `tools\check_no_game_data.py`: fail if `git ls-files` contains `generated/`, `ps1_game/`, `work/`, `*.bin`, `*.cue`, `*.iso`, `*.exe`, `*.zip`, `overlay_captures.json`, or a file with the `PS-X EXE` magic | none | Script does not exist yet. Cheapest, most important. |
| `emitters-test` | windows-latest | checkout `submodules: recursive`; install toolchain; build `recompiler/`; `ctest` | none | `ctest` runs 38 tests in under 5 seconds with no disc. [V] `psxrecomp\docs\BUILDING.md` per `docs/PUBLISHING_AUDIT.md` item 6 (not run by me). |
| `setup-host` | windows-latest | restore toolchain; configure with `-DPSXRECOMP_FORCE_SETUP_HOST=ON -DPSX_SETUP_WIZARD=ON`; build `psx-runtime` target; assert the configure log does not say "linking generated game C" | `MythologyKombat-setup.exe` (workflow artifact only) | Never built in this repo yet: `docs/PUBLISHING_AUDIT.md` marks it [H]. Must also confirm that no `generated/` directory exists on the runner (it is ignored, so a fresh clone has none). |
| `kit` | windows-latest | stage kit zip from an allow-list (setup exe, `psxrecomp/` filtered, `game.toml`, `seeds/`, `aot/`, `symbols.toml`, licences); run a content check that rejects `.c` files from `generated/`, `.bin`, `.cue`; compute SHA-256 | `MythologyKombat-<ver>-kit-windows-x64.zip`, `checksums.txt` | Do not call `scripts/package_release.sh` (bundled packager). Do not call retired `package_setup_host.sh` unmodified; it filters trees, but it was not read in full. [U] |
| `release` | ubuntu-latest, `needs: [guard, emitters-test, setup-host, kit]` | on tag `v*` or manual dispatch: download artifacts, tag, `softprops/action-gh-release@v2` with `fail_on_unmatched_files` | GitHub Release assets | Template shows the pattern. [V] `game-release.yml` last job. `permissions: contents: write`. |

Toolchain choice in CI: MSYS2 MinGW64 is what upstream uses to build game exes, and the clang pack (llvm-mingw, `cmake-clang-v1-windows-x64.zip`, v1.0.14) is what the **player** will get from the wizard and what we use locally (`docs/SETUP.md`). Use the clang pack in the `setup-host` job so CI tests the same compiler the player uses (CI downloads `https://github.com/RetroPortingToolKit/RetroPorting-Toolchains/releases/download/v1.0.14/cmake-clang-v1-windows-x64.zip`; the `releases/download/<tag>/` URL form is the standard GitHub form, and the `releases/latest/download/` form is what the host uses, [V] host.c line 2944; the exact asset name for v1.0.14 is from `docs/SETUP.md` line 92, [V]). Optionally add an MSYS2 leg later for parity with upstream. The upstream `fetch-toolchain` composite action downloads latest, not a pinned version. [V] `docs/PUBLISHING_AUDIT.md` item 7. Cache the toolchain by tag. SDL3 may need the upstream prefetch trick. [V] template.

Code signing: the template signs only if secrets exist (`WINDOWS_SIGN_PFX_BASE64`, `WINDOWS_SIGN_PFX_PASSWORD`). We could sign the kit exe. Needs a certificate: **USER** purchase and decision. [V] for the mechanism.

Limits: CI can never run Generate or the wizard end to end, because it has no disc. It can only prove that the kit builds and contains no game data. The end-to-end proof is manual on a clean machine (task T3.x below).

## 6. Launcher UX/UI issues

Reported by the user (treat as facts), then mapped to source. Everything in "likely cause" is a **hypothesis from reading the source**; none was reproduced in a screenshot in this session. Since T3.11 (2026-10-20), section 6.1 records what the user's screenshots show.

Platform: the UI is **native Dear ImGui** (C++), SDL3 or SDL2, OpenGL 3.3 (GLES2 on Android), drawn with the `LauncherTheme` token table. It is not web, not Electron and has no CSS. [V] `launcher_imgui.cpp` lines 3 and 14662 to 14666; `recomp-ui\README.md`. There is a headless script mode for screenshots: `LNG_SCRIPT="wait:40;view:settings;shot:out.png;quit"` in the standalone harness, and `LNG_VARIANT=psx`. [V] `recomp-ui\README.md` "Build & self-test". To reproduce in our exe, run `build\MythologyKombat.exe` with the launcher, or use the built-in browser pane / the OS screenshot; whether `LNG_SCRIPT` works inside the game exe was not checked. [U] Default window is 1100 by 880 logical pixels, resizable, size remembered in `launcher-window.ini`. [V] README. Layout scales with `px()` (DPI factor); I did not read its definition. [U]

| # | User report | Likely source (file:line, in `recomp-ui\src\common\backends\imgui\launcher_imgui.cpp` unless noted) | Likely cause [H] | Upstream-fixable by a small patch? |
|---|---|---|---|---|
| 1 | Scrolling on the main section | `begin_panel` 1755 to 1768 (comment 1759 to 1763: a fill-height card "must SCROLL when the window is too short"); `draw_game_panel` 2188 to 2231 (card height = `g_game_visible_h` minus a hard-coded `reserve` of 198 px, +120 for the disc verdict block, +62 multi-disc, +110 if a BIOS is required, etc., art capped at 368 px and dropped under 96 px); `g_game_visible_h` set at 3571 | The reserve list is a manual estimate; with the PSX verdict block plus the filename wrap and a "Browse" button, content exceeds the card at 1100x880 or on a scaled display, so ImGui shows a scrollbar | Small patch: enlarge `reserve` constants or measure content height instead (two-pass `GetCursorPosY`). Moderate risk: the same code serves other consoles. Needs a screenshot to confirm which branch fires. |
| 2 | Big calendar icon where a disc or game icon is expected | `hero_boxart_centered` 1991 to 2038: when `g_boxart` has no texture it draws a **hand-made SNES cartridge placeholder** (rounded body, three "ridges" on top, a recessed label window). Our `CMakeLists.txt` line 46 has `LAUNCHER_BOXART` commented out, so no `boxart.tga` is staged and `launcher_assets\img` does not exist (checked: `build\assets\img` has no `boxart*.tga`). Texture load: 14672 to 14674. A PSX `disc.tga` asset exists in `recomp-ui\assets\consoles\psx\img\disc.tga` but a grep of `recomp-ui\src` and the cmake files found no use of `disc.tga` | The cartridge with top ridges reads as a calendar (binder rings); this is the "no box art" fallback, not an emoji | Two options: (a) **ours, no upstream change**: provide a boxart TGA through `LAUNCHER_BOXART` (art we have the right to use; the scaffold's libretro boxart fetch, `fetch_boxart.py`, takes it from a third party, so ownership/licence is a **USER** decision); (b) upstream patch: draw a disc glyph when the profile is PSX (use `disc.tga` or a vector disc). Small patch (about 30 lines) if upstream accepts it. |
| 3 | Filename cropped | `draw_game_panel` meta table 2267 to 2278: `kv_row("File", m->rom_file, ...)`; `kv_row` 1787 to 1798 uses `ImGui::TextUnformatted(v)` (no wrap, no ellipsis) in a stretch column after a 76 px key column; `m->rom_file` is the basename, set in `launcher_model.c:1599` | Long names like `Mortal Kombat Mythologies - Sub-Zero.cue` exceed the column; ImGui clips at the cell edge | Small patch: `TextWrapped`, or middle-ellipsis + tooltip with the full name. Low risk. |
| 4 | Analog/D-pad control without proper bottom padding | `pad_mode_selector` 3114 to 3166 (buttons 28 px high; only a 6 px `Dummy` after it at 3442); caller 3440 to 3443; the card contains pad art, selector, `##src` combo (3445), Configure row (3459) | The Analog/D-Pad row is two buttons, not a textbox, and the next control (source combo) follows at 6 px spacing. In a fixed-height controller card the last row can sit at the card edge. Which element the user means is not certain. | Small patch: raise the `Dummy` or add bottom padding in the card (`WindowPadding` is `spacing_lg`, set at 1538). Low risk, but confirm with a screenshot which element. |
| 5a | Settings: Window size has no dropdown | `4065 to 4071`: `Window size` is a **button that cycles** through `kWindowWidths` (`launcher_model_cycle_window_size`, `launcher_model.c:1977`); only the `else` branch (`row_window_scale`, 1960) uses a combo (`settings_combo_row` 1926). The label is generated width x height from the aspect index (`launcher_model.c:1984`) | By design: the Renderer row's comment (4085 to 4088) says a list is better than a cycle for several entries, but the Window size row was never converted | Small patch: replace the button with a `BeginCombo` over `kWindowWidths` (list is in `launcher_model.c`; length `kWindowWidthCount`). Needs exposing a count/label-at accessor like `launcher_model_renderer_label_at`. About 25 lines. |
| 5b | Renderer: the OpenGL option text does not fit | `4089 to 4118`; control width `SETTINGS_CTRL_W 150.0f` (line 1896) shared by every row; upstream comment 4102 to 4107 says the closed combo shows "OpenGL (exper" for the long label and adds a hover tooltip | The renderer labels come from the host (`kOvlRenderers` / renderer table in `psxrecomp\runtime\src\main.cpp` near 16948, other label source not traced). A 150 px column (scaled by `px()`) is too narrow at the user's DPI/font | Small patch: widen the column for this row, or `CalcTextSize` of the longest label, or truncate the selected label with an ellipsis in the combo. Alternatively our host passes shorter labels (our side, no upstream change). The popup width already sizes to the longest entry (upstream comment). |
| 5c | Some textboxes have weird internal padding | `FramePadding = (spacing_md, spacing_sm)` at 1539; several widgets override with `PushStyleVar(FramePadding, (14, 8))` at 4706 and 4719; steppers use fixed `bh = 30, bw = 32, fw = 58` (1822 to 1826); buttons fixed 28/30/34 px heights (3152, 4067, 2299); combos use the default frame padding with fixed widths | Mixed fixed pixel heights and frame paddings across controls, so text boxes, steppers and combos do not share a height or inner padding | Unknown which textboxes. Probable fix is a shared helper that sets `FramePadding` once per row. Needs the screenshot; do not patch blind. |

### 6.1 Observed in screenshots (T3.11, 2026-10-20)

Source: the user's five images in `work\screens\` (agent-viewed, not run live). Display: DPI 120 (`AppliedDPI`, which is 125 percent) on a 1920x1080 screen, so about 1536x864 logical pixels are usable. The report does not say which screenshot shows each detail, so the file column lists the set the detail appears in.

| Shot | File |
|---|---|
| Main page | `shot_230017.png` |
| Main page scrolled | `shot_230036.png` |
| Settings top | `shot_230049.png` |
| Settings scrolled | `shot_230059.png` |
| Mods/Features page | `shot_230113.png` |

| # | Status | What the images show | Files |
|---|---|---|---|
| 1 | Seen | The main page scrolls. The scrolled view is shown. Cause not traced. | `shot_230017.png`, `shot_230036.png` |
| 2 | Seen | A calendar-like glyph sits in a blue tile where the game or disc icon should be. This matches the fallback in row 2 (no box art texture). Code path not traced. | `shot_230017.png`, `shot_230036.png` |
| 3 | Seen | The File row reads `Mortal Kombat Mythologies - Sub-Zero.c`, cut at the right edge. The `.cue` ending is not visible. | Main page shots |
| 4 | Partly seen | The Analog/D-Pad toggle sits close above the Keyboard row. The spacing is above the Keyboard row, not at the bottom of the card. The user may mean either. The bottom-padding cause is not confirmed. | Main page shots |
| 5a | Seen | Window size is one button labelled `1920 x 1440`, not a dropdown. | `shot_230049.png`, `shot_230059.png` |
| 5b | Seen | The closed Renderer combo shows `OpenGL (Recor`, cut short. The dropdown-open view was not captured. | `shot_230049.png`, `shot_230059.png` |
| 5c | Not confirmed | Dynamic resolution, Perspective textures and Scanlines checkboxes start at different x positions from the rest of the control column. The `Raw` screen-model button is wider than its neighbours. This may be the misaligned control column behind 5c. The user did not say that this is the item meant. | `shot_230049.png`, `shot_230059.png` |

Also seen in the images, not in the five reports [H on cause]:

- Window clipping: **refuted (T3.12).** The earlier clipping hypothesis was wrong. The user's screenshot method was not DPI aware. The image was a 1536 by 864 crop of a 1920 by 1080 screen at 125 percent. With a DPI-aware capture the launcher fits the work area. The launcher window size comes from `launcher-window.ini`, not from `video.window_width`. The DPI-aware capture tool is `tools\launcher_window_probe.ps1` (see `docs/SETUP.md`, T3.12).
- The Settings VSync combo shows `Off`, but `build\settings.toml` says `immediate` (user report, file not read in this step). Question 259.
- The launcher wrote `multitap_analog = true` into the repo `game.toml` at line 52, directly above `[netplay]` at line 53, after the netplay comment at lines 50 to 51 (agent read). Question 260. The `game.toml` change is in the `git status` at the start of T3.11 (`M game.toml`).

Also seen while reading (not reported by the user) [H]:

- The Settings combo columns are fixed at 150 px and non-responsive, so every long label will clip; the Renderer comment shows upstream knows (4102).
- The disc selector and the `Browse For Disc` label use the profile's `rom_noun`; for PSX with a `.cue` the user may think the `.bin` is needed. Wording only; not verified.
- `draw_verdict_block` shows `SBI File: N/A` for ordinary discs (2160 to 2164). Probably noise to a player. [H]
- On a failed disc check the message depends on `launcher_model` verdict text; I did not trace how a mismatching dump (hash differs from `game.toml`) is explained. [U]

How to reproduce screenshots: run the launcher at the default 1100x880 and at the user's actual display scale; set the same Windows scaling; capture with the Windows screenshot tool. For repeatable images use recomp-ui's `LNG_SCRIPT` in the standalone harness (`LNG_VARIANT=psx`), which exercises the same code but with fabricated game info, so it may not show our no-boxart or long-filename cases unless `LNG_BOX` and a long ROM name are supplied (`proto_main.c:576` mentions `LNG_BOX`). [V] `recomp-ui\README.md`; the details of `proto_main.c` were not read.

All of the above need the user's confirmation with a screenshot before any patch. Patches to `recomp-ui` would be to a submodule we pin: upstream-first means contribute or carry a patch file in `patches/`, not edit the submodule in place. [V] `CLAUDE.md` ("Upstream first"; `patches/` is for hooks and enhancements).

### 6.2 Patch outcomes (T3.12, 2026-10-20)

The fixes are patch files under `patches\launcher\` (D19). They apply to the pinned recomp-ui commit `7c635c6b`. The `recomp-ui\` submodule is not edited. The apply and build steps are in `docs/SETUP.md` (T3.12).

Evidence: agent-measured in this session, with DPI-aware captures. Before images are `work\screens\base_*.png`. After images are `work\screens\after2_*.png`. The user has not checked these fixes.

| # | Item (section 6.1) | Patch | Outcome (agent-measured) | Upstream candidate |
|---|--------------------|-------|--------------------------|--------------------|
| 1 | Scroll on the main section | `0001-dashboard-fit-right-column.patch` | The right column overrun is absorbed by 14 units of memory-card padding. Then the controller picture shrinks. At 1920 by 1080 at 125 percent, the pad art is about 30 logical units. | Yes |
| 2 | Calendar-like glyph in the game tile | `0002-game-card-disc-glyph.patch` | A neutral disc glyph is drawn with `ImDrawList`. It uses no copyrighted art. This is route (b) in `docs/TASKS.md` (T3.13), which makes the box-art route superseded. The user was told and did not object. The user has not explicitly confirmed it. | Yes |
| 3 | File name cropped | `0003-game-card-wrap-file-name.patch` | The file name wraps. | Yes |
| 4 | Analog/D-Pad bottom padding | `0004-player-card-selector-padding.patch` | The gap goes from 6 to 12 units. This was not verified as the user's complaint. The user must judge it. | Low value |
| 5a | Window size is a button, not a dropdown | `0005-settings-window-size-combo.patch` | Window size is a dropdown. | Yes |
| 5b | Renderer text does not fit | `0006-settings-control-column-width.patch` | The control column width is scoped to the DISPLAY card. | Yes |
| 5c | Misaligned controls | `0007-settings-align-checkboxes-and-screen-model.patch` | The checkboxes and the screen-model button align with the control column. This answers the 5c question in `docs/OPEN_QUESTIONS.md` (243). | Yes |

Window clipping is refuted. See section 6.1.

Not done, and why:

- The blank band in popups comes from upstream theme padding. It is out of scope and not fixed.
- The left-card reserve in `draw_game_panel` is not replaced. No overflow was found there.
- Not tested: multitap, a narrow layout, non-PSX consoles and a real mouse session.

Upstream: patches 0001, 0002, 0003, 0005, 0006 and 0007 are candidates. Patch 0004 is low value. Whether to send any upstream is the user's call (section 8, item 6).

A relink with these patches changes the exe SHA-256. Any user recording (T3.3) must come after the final relink.

## 7. Effort estimate and proposed tasks

Rough effort (agent time unless marked USER; my guesses, not measured): [H]

| Piece | Estimate |
|---|---|
| Guard script + `ci.yml` (guard, emitters-test) | 0.5 day |
| Setup-host build in CI + prove no game C is linked | 0.5 to 1 day (never built here) |
| Kit packager (allow-list) + content check + checksums | 1 day |
| Release job | 0.5 day |
| Clean-machine end-to-end test of the wizard | 0.5 day plus USER time; likely to find bugs: 1 to 3 days |
| Updater (check, download, verify, replace, data-version prompt) | 2 to 3 days |
| Embedded Python in the kit | 0.5 to 1 day |
| UX fixes 1 to 5 (after screenshots) | 1 to 2 days, mostly patches carried in `patches/` or sent upstream |
| Docs/README/licence/legal wording | 0.5 day plus USER decisions |

Proposed tasks (numbering follows the existing Phase 3 plan in `docs/TASKS.md`, which I did not edit; T3.1 and T3.2 are done, so start at T3.6, to be adjusted to the actual file):

| Id | Task | Who | Notes |
|---|---|---|---|
| T3.6 | USER decision: release model (A kit, B source-only, C own launcher) and the legal wording; confirm derived-data scope (PUBLISHING_AUDIT blocker 4) | USER | Blocks everything below. |
| T3.7 | `tools\check_no_game_data.py` + `.github/workflows/ci.yml` (guard, emitters-test) | implementer | No disc needed. |
| T3.8 | Build setup-host exe locally (`FORCE_SETUP_HOST=ON`), then in CI | implementer | Document the first run of the wizard on this machine. |
| T3.9 | USER: clean-machine / VM test with only a disc (the audit's acceptance test) | USER (agent writes the checklist) | Needs a second Windows machine or VM. |
| T3.10 | Kit packager and `kit` job; checksums | implementer + reviewer | Reject any generated C, disc or exe built from generated C. |
| T3.11 | Release workflow (tag `v*`), with pinned toolchain v1.0.14 | implementer | No git add of artifacts. |
| T3.12 | USER: screenshots for the UX list in section 6 (default window and the user's scale) | USER | Turns hypotheses into facts. |
| T3.13 | Launcher patches (window size combo, renderer width, filename wrap, boxart/disc glyph, padding) as `patches/*.patch` or upstream PRs | implementer | USER decides upstream PR vs local patch. |
| T3.14 | Update check + data-version prompt | implementer | Design in section 4. |
| T3.15 | USER: choose boxart / icon source and licence; optional code-signing certificate | USER | Third-party art needs rights; signing costs money. |
| T3.16 | Optional: embedded Python, pinned toolchain without network, offline kit variant | implementer | Reduces first-run failures. |

USER-only steps: T3.6, T3.9, T3.12, T3.15; also creating the public GitHub repo and enabling Actions (the PUBLISHING_AUDIT blockers: licence file, history/identity cleanup) are user decisions and are not in this document's scope.

## 8. Open decisions (for the user)

1. Release model: kit with local generate and compile (A), source-only (B), or own launcher (C)? A is the only one with a "download and click" feel that also respects D8.
2. Is the 5 to 10+ minute first-run compile (plus a toolchain download and Python) acceptable? Upstream retired this model for exactly that reason.
3. Do you accept an unsigned locally built exe (Smart App Control may block it), and do you want to buy a signing certificate for the kit exe?
4. Box art / icon: which image may we ship, and under what licence?
5. Pin the toolchain at v1.0.14 in the wizard? Pinning may need a small patch to the submodule or a `codegen_setup.c` override; floor-only is supported today.
6. Upstream PRs or local patches for recomp-ui fixes?
7. Whether a differently built copy (shared prebuilt framework objects, option E) is worth the second build recipe.
8. Legal wording on the repo and release pages (the other projects use "no game code or assets"; for us the kit really has none, so a stronger statement is possible).
9. Whether to re-check the claims marked [U] about Hell's Gate, Shaolin Monks and Zelda64Recomp (do their release binaries embed recompiled game code?) before we cite them as precedent. They are not needed for our design.

## Sources

Web (fetched 2026-10-20): https://github.com/florinp93/hells-gate-recomp , https://github.com/florinp93/hells-gate-recomp/releases , https://raw.githubusercontent.com/florinp93/hells-gate-recomp/main/README.md , https://raw.githubusercontent.com/florinp93/hells-gate-recomp/main/launcher/README.md , https://api.github.com/repos/florinp93/hells-gate-recomp/releases , https://github.com/OAleex/ShaolinMonksRecomp , https://github.com/OAleex/ShaolinMonksRecomp/releases , https://api.github.com/repos/OAleex/ShaolinMonksRecomp/releases , https://github.com/Zelda64Recomp/Zelda64Recomp , https://raw.githubusercontent.com/Zelda64Recomp/Zelda64Recomp/dev/BUILDING.md , https://github.com/RetroPortingToolKit/Retro-Launcher , https://github.com/mstan/psxrecomp , https://github.com/rexglue/rexglue-sdk (page did not say whether generated code is shipped or user-generated).

Not found: any Dante's Inferno or Shaolin Monks recomp for PS1/PS2 that uses PSXRecomp; the two cited projects are Xbox 360 / Xbox. A project repo `BUILDING.md` for Shaolin Monks returned 404 at the path I tried.

Local: `psxrecomp\docs\GAME_PROJECT_SETUP.md`, `psxrecomp\docs\LOCAL_CODEGEN_SDK.md`, `psxrecomp\docs\ci\README.md`, `psxrecomp\docs\ci\BUNDLED_RELEASES.md`, `psxrecomp\docs\ci\templates\game-release.yml`, `psxrecomp\.github\workflows\cli-release.yml`, `psxrecomp\tools\package_setup_host.sh`, `psxrecomp\host\psxrecomp_codegen_host.c`, `recomp-ui\README.md`, `recomp-ui\src\common\backends\imgui\launcher_imgui.cpp`, `recomp-ui\src\common\launcher_model.c`, `docs\PUBLISHING_AUDIT.md`, `docs\DECISIONS.md` (D8), `CMakeLists.txt`, `.gitignore`.
